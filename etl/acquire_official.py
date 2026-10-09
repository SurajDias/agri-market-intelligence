"""Operator-triggered, read-only acquisition of the official mandi API sample."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json

from etl.extract import (
    DataGovInAgmarknetAdapter,
    DataGovInConfig,
    SourceAccessError,
    run_preflight,
)
from etl.raw_store import write_raw_response


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight or acquire a bounded official data.gov.in JSON sample")
    parser.add_argument("--preflight", action="store_true", help="check official DNS/HTTPS availability without an API key")
    parser.add_argument("--acquire", action="store_true", help="acquire up to five validated JSON records")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    if not (args.preflight or args.acquire):
        parser.error("choose --preflight or --acquire")
    if not 1 <= args.limit <= 5:
        parser.error("--limit must be between 1 and 5")

    try:
        config = DataGovInConfig.from_environment(require_api_key=False)
        preflight = run_preflight(config)
        result: dict[str, object] = {"source_availability": asdict(preflight), "database_writes": 0}
        if args.preflight and not args.acquire:
            print(json.dumps(result, indent=2))
            return 0 if preflight.available else 2
        if not preflight.available:
            result.update({"acquisition": "not_attempted", "reason": "source unavailable; no retry made"})
            print(json.dumps(result, indent=2))
            return 2
        if not config.api_key:
            result.update({"acquisition": "not_attempted", "reason": "DATA_GOV_IN_API_KEY is not configured"})
            print(json.dumps(result, indent=2))
            return 2

        acquisition = DataGovInAgmarknetAdapter(config).fetch_validated_response(limit=args.limit, offset=args.offset)
        body_path, metadata_path = write_raw_response(
            acquisition.raw_bytes,
            source_id=DataGovInAgmarknetAdapter.source_id,
            output_dir=args.output_dir,
            metadata={
                "source_url": acquisition.source_url,
                "resource_id": acquisition.resource_id,
                "request_parameters": acquisition.request_parameters,
                "http_status": acquisition.http_status,
                "content_type": acquisition.content_type,
                "retrieval_timestamp": acquisition.retrieved_at.isoformat(),
                "record_count": len(acquisition.records),
            },
        )
        result.update({
            "acquisition": "success",
            "artifact_path": str(body_path),
            "metadata_path": str(metadata_path),
            "sha256": hashlib.sha256(acquisition.raw_bytes).hexdigest(),
            "record_count": len(acquisition.records),
            "schema_unit_status": "raw response only; schema and units require review",
        })
        print(json.dumps(result, indent=2))
        return 0
    except (SourceAccessError, OSError, ValueError) as exc:
        print(json.dumps({"acquisition": "failed", "reason": str(exc), "database_writes": 0}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
