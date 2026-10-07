"""Safe onboarding for an explicitly verified AGMARKNET export.

This module is intentionally conservative: local files are untrusted until the
caller supplies the exact official resource identity and explicitly confirms
verification. Dry-run paths never open a database write transaction.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy.orm import Session

from backend.core.db import SessionLocal
from backend.models import Commodity, Market
from etl.load import load_records
from etl.raw_store import write_raw_snapshot
from etl.transform import NormalizedPriceRecord, TransformReport, normalize_text, transform_records


OFFICIAL_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
OFFICIAL_PROVIDER = "Ministry of Agriculture and Farmers Welfare / Directorate of Marketing and Inspection"
OFFICIAL_DATASET = "Current Daily Price of Various Commodities from Various Markets (Mandi)"
OFFICIAL_SOURCE_URL = "https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi"
OFFICIAL_URL_PREFIXES = ("https://www.data.gov.in/", "https://api.data.gov.in/")


class ImportSafetyError(ValueError):
    """Raised when a candidate cannot pass the explicit verification gate."""


@dataclass(frozen=True)
class OfficialSourceMetadata:
    provider: str
    dataset: str
    resource_id: str
    source_url: str
    retrieval_timestamp: datetime
    verified: bool = False

    def validate(self) -> None:
        if not self.verified:
            raise ImportSafetyError("source_status=unverified; explicit verification is required")
        if self.resource_id != OFFICIAL_RESOURCE_ID:
            raise ImportSafetyError("resource_id does not match the official AGMARKNET resource")
        if self.provider != OFFICIAL_PROVIDER:
            raise ImportSafetyError("provider identity does not exactly match the declared official provider")
        if self.dataset != OFFICIAL_DATASET:
            raise ImportSafetyError("dataset identity does not exactly match the declared official dataset")
        if not self.source_url.startswith(OFFICIAL_URL_PREFIXES):
            raise ImportSafetyError("source_url is not an official data.gov.in resource/API URL")
        if self.retrieval_timestamp.tzinfo is None:
            raise ImportSafetyError("retrieval_timestamp must include a timezone")


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = payload["records"]
    else:
        raise ImportSafetyError("JSON file must contain a list or an object with a records array")
    if any(not isinstance(item, dict) for item in records):
        raise ImportSafetyError("candidate contains a non-object record")
    return records


def read_candidate_file(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read a candidate for inspection only; this function never writes data."""
    candidate = Path(path)
    if not candidate.is_file():
        raise ImportSafetyError(f"candidate file does not exist: {candidate}")
    suffix = candidate.suffix.casefold()
    if suffix == ".csv":
        with candidate.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ImportSafetyError("CSV has no header row")
            records = [dict(row) for row in reader]
            columns = list(reader.fieldnames)
    elif suffix == ".json":
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        records = _records_from_payload(payload)
        columns = sorted({str(key) for row in records for key in row})
    else:
        raise ImportSafetyError("only CSV and JSON candidates are supported; XLSX/ZIP require explicit adapter work")
    return records, {
        "path": str(candidate),
        "file_type": suffix.lstrip("."),
        "size_bytes": candidate.stat().st_size,
        "columns": columns,
        "row_count": len(records),
        "source_status": "unverified",
    }


def inspect_candidate(path: str | Path) -> dict[str, Any]:
    records, metadata = read_candidate_file(path)
    date_values = list(row_values(records, "arrival_date", "arrival date", "date"))
    commodities = sorted({str(value).strip() for value in row_values(records, "commodity", "commodity_name") if value not in (None, "")})
    markets = sorted({str(value).strip() for value in row_values(records, "market", "market_name", "mandi") if value not in (None, "")})
    metadata.update({
        "date_values_detected": sorted({str(value) for value in date_values if value not in (None, "")}),
        "commodity_values": commodities,
        "market_values": markets,
        "price_fields": sorted({key for key in metadata["columns"] if "price" in normalize_text(key)}),
        "unit_fields": sorted({key for key in metadata["columns"] if "unit" in normalize_text(key)}),
        "provenance_fields": sorted({key for key in metadata["columns"] if any(token in normalize_text(key) for token in ("source", "resource", "record", "url"))}),
        "official_identity_link": False,
    })
    return metadata


def row_values(records: list[dict[str, Any]], *keys: str) -> Iterable[Any]:
    aliases = {normalize_text(key).replace(" ", "_") for key in keys}
    for record in records:
        for key, value in record.items():
            if normalize_text(key).replace(" ", "_") in aliases:
                yield value
                break


def row_keys(records: list[dict[str, Any]], *keys: str) -> Iterable[dict[str, Any]]:
    aliases = {normalize_text(key).replace(" ", "_") for key in keys}
    for record in records:
        yield {key: value for key, value in record.items() if normalize_text(key).replace(" ", "_") in aliases}


def _reference_rejections(session: Session, records: list[NormalizedPriceRecord]) -> tuple[list[NormalizedPriceRecord], dict[str, int]]:
    accepted: list[NormalizedPriceRecord] = []
    reasons: dict[str, int] = {}
    for record in records:
        commodities = session.query(Commodity).filter(Commodity.normalized_name == record.commodity_normalized_name, Commodity.is_active.is_(True)).all()
        markets = session.query(Market).filter(Market.normalized_name == record.market_normalized_name, Market.state == record.state, Market.district == record.district, Market.is_active.is_(True)).all()
        reason = None
        if len(commodities) != 1:
            reason = "commodity_reference_not_found_or_ambiguous"
        elif len(markets) != 1:
            reason = "market_reference_not_found_or_ambiguous"
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
        else:
            accepted.append(record)
    return accepted, reasons


def dry_run_candidate(session: Session, path: str | Path, source: OfficialSourceMetadata, *, today: date | None = None) -> dict[str, Any]:
    source.validate()
    records, file_metadata = read_candidate_file(path)
    normalized, report = transform_records(records, source_id=source.resource_id, today=today)
    matched, reference_rejections = _reference_rejections(session, normalized)
    rejection_reasons = dict(report.rejection_reasons)
    for key, value in reference_rejections.items():
        rejection_reasons[key] = rejection_reasons.get(key, 0) + value
    return {
        "source_status": "verified",
        "file": file_metadata,
        "records_seen": report.records_read,
        "accepted_candidates": len(matched),
        "rejected_records": report.records_rejected + sum(reference_rejections.values()),
        "duplicate_candidates": report.duplicate_records,
        "unmatched_commodities": reference_rejections.get("commodity_reference_not_found_or_ambiguous", 0),
        "unmatched_markets": reference_rejections.get("market_reference_not_found_or_ambiguous", 0),
        "invalid_prices": report.invalid_price + report.invalid_range,
        "invalid_dates": report.invalid_date + report.future_date,
        "unsupported_units": report.missing_price_unit,
        "expected_insertion_count": len(matched),
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "source": asdict(source),
    }


def import_verified_file(session: Session, path: str | Path, source: OfficialSourceMetadata, *, today: date | None = None, raw_output_dir: str | None = None) -> dict[str, Any]:
    """Import only after a successful explicit verification and dry run."""
    source.validate()
    records, _ = read_candidate_file(path)
    normalized, report = transform_records(records, source_id=source.resource_id, today=today)
    raw_path = write_raw_snapshot(records, source_id=source.resource_id, output_dir=raw_output_dir, metadata=asdict(source))
    result = load_records(session, normalized, report, source_id=source.resource_id, source_name=source.dataset, source_url=source.source_url)
    result["raw_snapshot"] = str(raw_path)
    result["source_status"] = "verified"
    return result


def _metadata_from_args(args: argparse.Namespace) -> OfficialSourceMetadata:
    return OfficialSourceMetadata(
        provider=args.provider,
        dataset=args.dataset,
        resource_id=args.resource_id,
        source_url=args.source_url,
        retrieval_timestamp=datetime.fromisoformat(args.retrieval_timestamp),
        verified=args.confirm_official,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect, dry-run, or explicitly import a verified AGMARKNET file")
    parser.add_argument("path")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--import", dest="do_import", action="store_true")
    parser.add_argument("--confirm-official", action="store_true")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--retrieval-timestamp", required=True)
    parser.add_argument("--today", type=date.fromisoformat)
    parser.add_argument("--raw-output-dir")
    args = parser.parse_args()
    if not (args.inspect or args.dry_run or args.do_import):
        parser.error("choose --inspect, --dry-run, or --import")
    if args.inspect:
        print(json.dumps(inspect_candidate(args.path), indent=2, default=str))
        return
    source = _metadata_from_args(args)
    if args.dry_run:
        if SessionLocal is None:
            raise SystemExit("DATABASE_URL is not configured; dry-run reference matching requires PostgreSQL")
        with SessionLocal() as session:
            print(json.dumps(dry_run_candidate(session, args.path, source, today=args.today), indent=2, default=str))
        return
    if not args.confirm_official:
        raise SystemExit("refusing import: pass --confirm-official with exact official metadata")
    if SessionLocal is None:
        raise SystemExit("DATABASE_URL is not configured; cannot import")
    with SessionLocal() as session:
        print(json.dumps(import_verified_file(session, args.path, source, today=args.today, raw_output_dir=args.raw_output_dir), indent=2, default=str))


if __name__ == "__main__":
    main()
