import hashlib
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests

import etl.acquire_official as acquire_module
import etl.raw_store as raw_store_module
from etl.extract import (
    DEFAULT_RESOURCE_ID,
    DataGovInAgmarknetAdapter,
    DataGovInConfig,
    PreflightResult,
    SourceAccessError,
    run_preflight,
)
from etl.raw_store import write_raw_response


class Response:
    def __init__(self, payload=None, *, body=None, content_type="application/json", status_code=200, json_error=None):
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.content = body if body is not None else json.dumps(payload).encode("utf-8")
        self.payload = payload
        self.json_error = json_error

    def raise_for_status(self):
        if self.status_code >= 400:
            error_response = requests.Response()
            error_response.status_code = self.status_code
            raise requests.HTTPError("error", response=error_response)

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class Session:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, endpoint, *, params=None, timeout=None, allow_redirects=True):
        self.calls.append({"endpoint": endpoint, "params": params, "timeout": timeout, "allow_redirects": allow_redirects})
        if self.error:
            raise self.error
        return self.response


def config(api_key="fixture-value"):
    return DataGovInConfig(api_key=api_key, timeout_seconds=4)


class AcquisitionWorkflowTests(unittest.TestCase):
    def test_dns_failure_stops_before_https_and_makes_no_retry(self):
        session = Session(Response({"records": []}))
        result = run_preflight(config(), session=session, resolver=lambda *args, **kwargs: (_ for _ in ()).throw(OSError("resolver failed")))
        self.assertEqual(result.dns_status, "dns_failure")
        self.assertEqual(result.https_status, "not_attempted")
        self.assertEqual(session.calls, [])

    def test_connection_refusal_and_timeout_are_distinguished(self):
        refusal = run_preflight(config(), session=Session(error=requests.ConnectionError("Connection refused")), resolver=lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 443))])
        timeout = run_preflight(config(), session=Session(error=requests.Timeout("timed out")), resolver=lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 443))])
        self.assertEqual(refusal.https_status, "connection_refused")
        self.assertEqual(timeout.https_status, "timeout")

    def test_missing_api_key_is_rejected_without_request(self):
        with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": ""}, clear=False):
            with self.assertRaises(SourceAccessError):
                DataGovInConfig.from_environment()

    def test_validated_request_is_bounded_and_not_retried(self):
        response = Response({"resource_id": DEFAULT_RESOURCE_ID, "records": [{"State": "Karnataka"}]})
        session = Session(response)
        result = DataGovInAgmarknetAdapter(config(), session=session).fetch_validated_response(limit=2, offset=3, filters={"State": "Karnataka"})
        self.assertEqual(len(result.records), 1)
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(session.calls[0]["params"]["limit"], 2)
        self.assertEqual(session.calls[0]["params"]["offset"], 3)
        self.assertEqual(session.calls[0]["params"]["filters[State]"], "Karnataka")
        self.assertNotIn("api-key", result.request_parameters)
        self.assertFalse(session.calls[0]["allow_redirects"])

    def test_failed_validated_request_makes_exactly_one_attempt(self):
        session = Session(Response({"error": "temporary"}, status_code=503))
        with self.assertRaisesRegex(SourceAccessError, "HTTP status 503"):
            DataGovInAgmarknetAdapter(config(), session=session).fetch_validated_response()
        self.assertEqual(len(session.calls), 1)

    def test_legacy_request_explicitly_disables_redirects(self):
        session = Session(Response({"records": []}))
        DataGovInAgmarknetAdapter(config(), session=session).fetch_records(limit=1)
        self.assertFalse(session.calls[0]["allow_redirects"])

    def test_html_response_is_rejected(self):
        response = Response(body=b"<html>access denied</html>", content_type="text/html")
        with self.assertRaisesRegex(SourceAccessError, "not JSON"):
            DataGovInAgmarknetAdapter(config(), session=Session(response)).fetch_validated_response()

    def test_authenticated_errors_do_not_expose_api_key(self):
        response = Response({"error": "unauthorized"}, status_code=401)
        with self.assertRaises(SourceAccessError) as context:
            DataGovInAgmarknetAdapter(config(), session=Session(response)).fetch_validated_response()
        self.assertNotIn("fixture-value", str(context.exception))
        self.assertIn("HTTP status 401", str(context.exception))

    def test_malformed_json_is_rejected(self):
        response = Response(body=b"not-json", json_error=ValueError("bad json"))
        with self.assertRaisesRegex(SourceAccessError, "malformed JSON"):
            DataGovInAgmarknetAdapter(config(), session=Session(response)).fetch_validated_response()

    def test_incorrect_identity_and_invalid_shape_are_rejected(self):
        wrong_identity = Response({"resource_id": "other-resource", "records": []})
        with self.assertRaisesRegex(SourceAccessError, "identity"):
            DataGovInAgmarknetAdapter(config(), session=Session(wrong_identity)).fetch_validated_response()
        invalid_shape = Response({"resource_id": DEFAULT_RESOURCE_ID, "records": "not-a-list"})
        with self.assertRaisesRegex(SourceAccessError, "records array"):
            DataGovInAgmarknetAdapter(config(), session=Session(invalid_shape)).fetch_validated_response()

    def test_raw_response_preserves_bytes_checksum_and_metadata_without_overwrite(self):
        body = b'{"records":[{"State":"Karnataka"}]}'
        with tempfile.TemporaryDirectory() as directory:
            path, metadata_path = write_raw_response(
                body,
                source_id="TEST_SOURCE",
                output_dir=directory,
                metadata={"source_url": "https://api.data.gov.in/resource", "resource_id": DEFAULT_RESOURCE_ID, "http_status": 200, "content_type": "application/json", "record_count": 1},
            )
            saved = path.read_bytes()
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(saved, body)
            self.assertEqual(metadata["downloaded_bytes"], len(body))
            self.assertEqual(metadata["sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(metadata["record_count"], 1)
            second_path, _ = write_raw_response(body, source_id="TEST_SOURCE", output_dir=directory, metadata={})
            self.assertNotEqual(path, second_path)

    def test_existing_body_and_sidecar_destinations_are_not_overwritten(self):
        fixed_time = __import__("datetime").datetime(2026, 10, 9, 14, 0, tzinfo=__import__("datetime").timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(raw_store_module, "datetime") as clock:
            clock.now.return_value = fixed_time
            first_body, first_metadata = write_raw_response(b"first", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            first_body.write_bytes(b"preserve-body")
            first_metadata.write_text("preserve-metadata", encoding="utf-8")
            second_body, second_metadata = write_raw_response(b"second", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            self.assertNotEqual(first_body, second_body)
            self.assertEqual(first_body.read_bytes(), b"preserve-body")
            self.assertEqual(first_metadata.read_text(encoding="utf-8"), "preserve-metadata")
            self.assertEqual(second_body.read_bytes(), b"second")
            self.assertTrue(second_metadata.exists())

    def test_existing_metadata_sidecar_destination_is_not_overwritten(self):
        fixed_time = __import__("datetime").datetime(2026, 10, 9, 14, 1, tzinfo=__import__("datetime").timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(raw_store_module, "datetime") as clock:
            clock.now.return_value = fixed_time
            existing_metadata = Path(directory) / "TEST_SOURCE_20261009T140100Z.metadata.json"
            existing_metadata.write_text("existing", encoding="utf-8")
            body, metadata = write_raw_response(b"new", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            self.assertNotEqual(metadata, existing_metadata)
            self.assertEqual(existing_metadata.read_text(encoding="utf-8"), "existing")
            self.assertEqual(body.read_bytes(), b"new")

    def test_body_write_failure_leaves_no_published_artifact(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(raw_store_module, "_write_temp_bytes", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                write_raw_response(b"body", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            self.assertEqual(list(Path(directory).glob("TEST_SOURCE*")), [])

    def test_metadata_publication_failure_leaves_orphan_and_later_run_uses_new_name(self):
        fixed_time = __import__("datetime").datetime(2026, 10, 9, 14, 2, tzinfo=__import__("datetime").timezone.utc)
        original_publish = raw_store_module._publish_without_overwrite
        calls = {"count": 0}

        def fail_on_metadata(source, destination):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("metadata publication failure")
            return original_publish(source, destination)

        with tempfile.TemporaryDirectory() as directory, patch.object(raw_store_module, "datetime") as clock:
            clock.now.return_value = fixed_time
            with patch.object(raw_store_module, "_publish_without_overwrite", side_effect=fail_on_metadata):
                with self.assertRaises(OSError):
                    write_raw_response(b"orphan", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            orphan = Path(directory) / "TEST_SOURCE_20261009T140200Z.json"
            self.assertEqual(orphan.read_bytes(), b"orphan")
            self.assertFalse(orphan.with_name(orphan.name.replace(".json", ".metadata.json")).exists())
            recovered_body, recovered_metadata = write_raw_response(b"complete", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            self.assertNotEqual(recovered_body, orphan)
            self.assertTrue(recovered_metadata.exists())
            self.assertEqual(orphan.read_bytes(), b"orphan")

    def test_replaced_lock_is_not_removed_by_original_writer(self):
        fixed_time = __import__("datetime").datetime(2026, 10, 9, 14, 3, tzinfo=__import__("datetime").timezone.utc)
        original_publish = raw_store_module._publish_without_overwrite
        calls = {"count": 0}

        def replace_lock_after_body(source, destination):
            calls["count"] += 1
            result = original_publish(source, destination)
            if calls["count"] == 1:
                lock = Path(directory) / ".TEST_SOURCE_20261009T140300Z.lock"
                lock.unlink()
                lock.write_text("replacement-owner", encoding="ascii")
            return result

        with tempfile.TemporaryDirectory() as directory, patch.object(raw_store_module, "datetime") as clock:
            clock.now.return_value = fixed_time
            with patch.object(raw_store_module, "_publish_without_overwrite", side_effect=replace_lock_after_body):
                write_raw_response(b"body", source_id="TEST_SOURCE", output_dir=directory, metadata={})
            replacement = Path(directory) / ".TEST_SOURCE_20261009T140300Z.lock"
            self.assertTrue(replacement.exists())
            self.assertEqual(replacement.read_text(encoding="ascii"), "replacement-owner")

    def test_sensitive_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "sensitive"):
                write_raw_response(b"body", source_id="TEST_SOURCE", output_dir=directory, metadata={"authorization": "Bearer hidden"})

    def test_request_exception_chain_and_cli_output_exclude_secret(self):
        secret = "dummy-secret-value"
        error = requests.ConnectionError(f"https://api.data.gov.in/resource?api-key={secret}")
        with self.assertRaises(SourceAccessError) as context:
            DataGovInAgmarknetAdapter(config(), session=Session(error=error)).fetch_validated_response()
        surfaced = context.exception
        self.assertNotIn(secret, str(surfaced))
        self.assertIsNone(surfaced.__cause__)
        self.assertIsNone(surfaced.__context__)

        with patch.object(acquire_module.DataGovInConfig, "from_environment", return_value=config()), \
             patch.object(acquire_module, "run_preflight", return_value=PreflightResult("api.data.gov.in", "success", "success", 200)), \
             patch.object(acquire_module.DataGovInAgmarknetAdapter, "fetch_validated_response", side_effect=surfaced), \
             patch("sys.argv", ["acquire_official", "--acquire"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = acquire_module.main()
        self.assertEqual(exit_code, 2)
        self.assertNotIn(secret, output.getvalue())

    def test_acquisition_module_has_no_database_import(self):
        source = Path(__file__).parents[1].joinpath("acquire_official.py").read_text(encoding="utf-8")
        self.assertNotIn("backend", source)
        self.assertNotIn("etl.load", source)


if __name__ == "__main__":
    unittest.main()
