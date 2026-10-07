"""Normalize and validate government mandi price records.

The transformer is deliberately source-agnostic. Adapters provide raw
dictionaries; this module maps common AGMARKNET/data.gov.in field spellings
into the canonical internal representation used by the loader.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
import hashlib
import json
import re
from typing import Any, Iterable


_MISSING = {"", "na", "n/a", "nan", "null", "none", "-", "not available"}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def _field_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize_text(value))


def _get(record: dict[str, Any], *aliases: str) -> Any:
    by_key = {_field_key(key): value for key, value in record.items()}
    for alias in aliases:
        value = by_key.get(_field_key(alias))
        if value is not None and normalize_text(value) not in _MISSING:
            return value
    return None


def parse_number(value: Any) -> float | None:
    if value is None or normalize_text(value) in _MISSING:
        return None
    cleaned = str(value).replace(",", "").strip()
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def _is_present(value: Any) -> bool:
    return value is not None and normalize_text(value) not in _MISSING


def parse_date(value: Any) -> date | None:
    """Accept ISO and unambiguous day-first government date formats only."""
    if value is None or normalize_text(value) in _MISSING:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _source_record_id(record: dict[str, Any], identity: tuple[Any, ...]) -> str:
    value = _get(record, "id", "record_id", "source_record_id", "_id")
    if value is not None:
        return str(value).strip()
    payload = json.dumps(identity, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NormalizedPriceRecord:
    source_id: str
    source_record_id: str
    source_arrival_date: str
    source_state: str
    source_district: str
    source_market_name: str
    source_commodity_name: str
    source_variety: str | None
    source_grade: str | None
    source_price_unit: str
    arrival_date: date
    state: str
    district: str
    market_name: str
    market_normalized_name: str
    commodity_name: str
    commodity_normalized_name: str
    min_price_inr_per_quintal: float | None
    max_price_inr_per_quintal: float | None
    modal_price_inr_per_quintal: float
    min_price_inr_per_kg: float | None
    max_price_inr_per_kg: float | None
    modal_price_inr_per_kg: float
    arrivals_tonnes: float | None


@dataclass
class TransformReport:
    records_read: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    duplicate_records: int = 0
    missing_commodity: int = 0
    missing_market: int = 0
    missing_date: int = 0
    missing_price: int = 0
    missing_price_unit: int = 0
    invalid_price: int = 0
    invalid_range: int = 0
    invalid_date: int = 0
    future_date: int = 0
    rejection_reasons: Counter[str] = field(default_factory=Counter)


def _price_unit(value: Any, default: str | None) -> str:
    raw_value = value if value is not None and normalize_text(value) not in _MISSING else default
    normalized = normalize_text(raw_value).replace("₹", "inr")
    if not normalized:
        return ""
    if normalized in {"inr/kg", "rs/kg", "rs./kg", "rs per kg", "rupees per kg", "inr per kg"}:
        return "INR/kg"
    if normalized in {
        "inr/quintal", "rs/quintal", "rs./quintal", "rs/qtl", "rs/q", "inr/qtl", "inr/q",
        "rs per quintal", "rupees per quintal", "inr per quintal",
    }:
        return "INR/quintal"
    return ""


def _to_per_kg(value: float | None, unit: str) -> float | None:
    if value is None:
        return None
    return value if unit == "INR/kg" else value / 100.0


def transform_records(
    records: Iterable[dict[str, Any]],
    *,
    source_id: str,
    default_price_unit: str | None = None,
    today: date | None = None,
) -> tuple[list[NormalizedPriceRecord], TransformReport]:
    """Return valid, de-duplicated records and a detailed deterministic report."""
    report = TransformReport()
    accepted: list[NormalizedPriceRecord] = []
    seen: set[tuple[str, str]] = set()
    today = today or date.today()

    for record in records:
        report.records_read += 1
        raw_commodity = _get(record, "commodity", "commodity_name")
        raw_market = _get(record, "market", "market_name", "mandi")
        raw_state = _get(record, "state")
        raw_district = _get(record, "district")
        raw_date = _get(record, "arrival_date", "arrival date", "date")
        raw_variety = _get(record, "variety")
        raw_grade = _get(record, "grade")
        parsed_date = parse_date(raw_date)
        identity = (
            normalize_text(raw_commodity), normalize_text(raw_market), normalize_text(raw_state),
            normalize_text(raw_district), parsed_date, normalize_text(raw_variety), normalize_text(raw_grade),
        )
        record_id = _source_record_id(record, identity)
        dedupe_key = (source_id, record_id)
        if dedupe_key in seen:
            report.duplicate_records += 1
            report.rejection_reasons["duplicate"] += 1
            continue
        seen.add(dedupe_key)

        reason: str | None = None
        if not raw_commodity:
            report.missing_commodity += 1
            reason = "missing_commodity"
        elif not raw_market or not raw_state or not raw_district:
            report.missing_market += 1
            reason = "missing_market_location"
        elif parsed_date is None:
            report.missing_date += int(raw_date is None)
            report.invalid_date += int(raw_date is not None)
            reason = "missing_date" if raw_date is None else "invalid_date"
        elif parsed_date > today:
            report.future_date += 1
            reason = "future_date"

        unit = _price_unit(_get(record, "unit", "price_unit"), default_price_unit)
        minimum = parse_number(_get(record, "min_price", "min price", "min_price_inr_per_quintal", "min_x0020_price"))
        maximum = parse_number(_get(record, "max_price", "max price", "max_price_inr_per_quintal", "max_x0020_price"))
        modal = parse_number(_get(record, "modal_price", "modal price", "modal_price_inr_per_quintal", "modal_x0020_price"))
        raw_minimum = _get(record, "min_price", "min price", "min_price_inr_per_quintal", "min_x0020_price")
        raw_maximum = _get(record, "max_price", "max price", "max_price_inr_per_quintal", "max_x0020_price")
        raw_modal = _get(record, "modal_price", "modal price", "modal_price_inr_per_quintal", "modal_x0020_price")
        malformed_price = any(
            _is_present(raw_value) and parsed_value is None
            for raw_value, parsed_value in (
                (raw_minimum, minimum),
                (raw_maximum, maximum),
                (raw_modal, modal),
            )
        )
        if malformed_price:
            report.invalid_price += 1
            reason = reason or "malformed_price"
        elif modal is None:
            report.missing_price += 1
            reason = reason or "missing_modal_price"
        elif unit not in {"INR/kg", "INR/quintal"}:
            report.missing_price_unit += 1
            report.invalid_price += 1
            reason = reason or "missing_or_unsupported_price_unit"
        elif any(value is not None and value < 0 for value in (minimum, maximum, modal)):
            report.invalid_price += 1
            reason = reason or "negative_price"
        elif (minimum is not None and minimum > modal) or (maximum is not None and maximum < modal) or (minimum is not None and maximum is not None and minimum > maximum):
            report.invalid_range += 1
            reason = reason or "invalid_price_range"

        if reason:
            report.records_rejected += 1
            report.rejection_reasons[reason] += 1
            continue

        report.records_accepted += 1
        accepted.append(
            NormalizedPriceRecord(
                source_id=source_id,
                source_record_id=record_id,
                source_arrival_date=str(raw_date),
                source_state=str(raw_state).strip(),
                source_district=str(raw_district).strip(),
                source_market_name=str(raw_market).strip(),
                source_commodity_name=str(raw_commodity).strip(),
                source_variety=str(raw_variety).strip() if raw_variety is not None else None,
                source_grade=str(raw_grade).strip() if raw_grade is not None else None,
                source_price_unit=unit,
                arrival_date=parsed_date,
                state=normalize_text(raw_state),
                district=normalize_text(raw_district),
                market_name=str(raw_market).strip(),
                market_normalized_name=normalize_text(raw_market),
                commodity_name=str(raw_commodity).strip(),
                commodity_normalized_name=normalize_text(raw_commodity),
                min_price_inr_per_quintal=minimum if unit == "INR/quintal" else (minimum * 100 if minimum is not None else None),
                max_price_inr_per_quintal=maximum if unit == "INR/quintal" else (maximum * 100 if maximum is not None else None),
                modal_price_inr_per_quintal=modal if unit == "INR/quintal" else modal * 100,
                min_price_inr_per_kg=_to_per_kg(minimum, unit),
                max_price_inr_per_kg=_to_per_kg(maximum, unit),
                modal_price_inr_per_kg=_to_per_kg(modal, unit),
                arrivals_tonnes=parse_number(_get(record, "arrivals", "arrival", "arrival_quantity", "arrivals_tonnes")),
            )
        )

    return accepted, report
