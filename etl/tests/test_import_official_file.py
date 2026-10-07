import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from etl.import_official_file import (
    OFFICIAL_DATASET,
    OFFICIAL_PROVIDER,
    OFFICIAL_RESOURCE_ID,
    OFFICIAL_SOURCE_URL,
    ImportSafetyError,
    OfficialSourceMetadata,
    dry_run_candidate,
    inspect_candidate,
    read_candidate_file,
)


SOURCE = OfficialSourceMetadata(
    provider=OFFICIAL_PROVIDER,
    dataset=OFFICIAL_DATASET,
    resource_id=OFFICIAL_RESOURCE_ID,
    source_url=OFFICIAL_SOURCE_URL,
    retrieval_timestamp=datetime(2026, 10, 7, tzinfo=timezone.utc),
    verified=True,
)


class Query:
    def __init__(self, values):
        self.values = values

    def filter(self, *args):
        return self

    def all(self):
        return self.values


class ReferenceSession:
    def __init__(self, commodities=None, markets=None):
        self.commodities = commodities or []
        self.markets = markets or []

    def query(self, model):
        return Query(self.commodities if model.__name__ == "Commodity" else self.markets)


def write_csv(content):
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return Path(handle.name)


class OfficialFileImportTests(unittest.TestCase):
    def test_unverified_metadata_is_rejected(self):
        unverified = SOURCE.__class__(**{**SOURCE.__dict__, "verified": False})
        with self.assertRaises(ImportSafetyError):
            unverified.validate()

    def test_inspection_reports_actual_headers_without_importing(self):
        path = write_csv("State,District,Market,Commodity,Arrival_Date,Min Price,Max Price,Modal Price,Unit\nKarnataka,Mandya,Mandya,Tomato,05/10/2026,1000,1400,1200,Rs./Quintal\n")
        result = inspect_candidate(path)
        self.assertEqual(result["row_count"], 1)
        self.assertIn("Modal Price", result["columns"])
        self.assertEqual(result["source_status"], "unverified")
        self.assertFalse(result["official_identity_link"])

    def test_dry_run_requires_explicit_source_and_does_not_write(self):
        path = write_csv("State,District,Market,Commodity,Arrival_Date,Min Price,Max Price,Modal Price,Unit\nKarnataka,Mandya,Mandya,Tomato,05/10/2026,1000,1400,1200,Rs./Quintal\n")
        session = ReferenceSession([SimpleNamespace(normalized_name="tomato", is_active=True)], [SimpleNamespace(normalized_name="mandya", state="karnataka", district="mandya", is_active=True)])
        result = dry_run_candidate(session, path, SOURCE, today=datetime(2026, 10, 7, tzinfo=timezone.utc).date())
        self.assertEqual(result["records_seen"], 1)
        self.assertEqual(result["accepted_candidates"], 1)
        self.assertEqual(result["expected_insertion_count"], 1)

    def test_missing_unit_is_rejected_by_existing_transformer(self):
        path = write_csv("State,District,Market,Commodity,Arrival_Date,Min Price,Max Price,Modal Price\nKarnataka,Mandya,Mandya,Tomato,05/10/2026,1000,1400,1200\n")
        session = ReferenceSession([SimpleNamespace(normalized_name="tomato", is_active=True)], [SimpleNamespace(normalized_name="mandya", state="karnataka", district="mandya", is_active=True)])
        result = dry_run_candidate(session, path, SOURCE, today=datetime(2026, 10, 7, tzinfo=timezone.utc).date())
        self.assertEqual(result["accepted_candidates"], 0)
        self.assertGreater(result["unsupported_units"], 0)

    def test_malformed_json_is_rejected(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        handle.write('{"not_records": []}')
        handle.close()
        with self.assertRaises(ImportSafetyError):
            read_candidate_file(handle.name)


if __name__ == "__main__":
    unittest.main()
