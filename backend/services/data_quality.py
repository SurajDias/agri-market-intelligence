"""Deterministic data-quality and evidence-readiness orchestration.

This module reads the existing ingestion foundation. It never fills dates,
changes observations, invents source trust, or uses the system clock unless a
caller explicitly supplies ``reference_datetime``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Commodity, DataQualityRun, DataSource, IngestionRun, Market, MarketPrice
from backend.schemas.data_quality import DataQualitySummaryResponse


QUALITY_WEIGHTS = {"completeness": Decimal("25"), "validity": Decimal("20"), "uniqueness": Decimal("15"), "freshness": Decimal("15"), "provenance": Decimal("15"), "consistency": Decimal("10")}
QUALITY_THRESHOLDS = {"excellent": Decimal("90"), "good": Decimal("75"), "acceptable": Decimal("60"), "poor": Decimal("40")}
FRESHNESS_THRESHOLDS_DAYS = {"fresh": 2, "recent": 7, "stale": 30}
MIN_FORECAST_OBSERVATIONS = 30
MIN_COVERAGE_PERCENT = Decimal("80")
MIN_VALIDITY_PERCENT = Decimal("95")


def _percent(numerator: int | Decimal, denominator: int | Decimal) -> Decimal:
    if not denominator:
        return Decimal("0")
    return (Decimal(numerator) * Decimal("100") / Decimal(denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _date_list(start: date | None, end: date | None) -> list[date]:
    if start is None or end is None or start > end:
        return []
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _classify(score: Decimal) -> str:
    for label, threshold in QUALITY_THRESHOLDS.items():
        if score >= threshold:
            return label
    return "unusable"


def _freshness(age: int | None) -> tuple[str, Decimal]:
    if age is None:
        return "unavailable", Decimal("0")
    if age < 0:
        return "future_reference", Decimal("0")
    if age <= 2:
        return "fresh", Decimal("100")
    if age <= 7:
        return "recent", Decimal("75")
    if age <= 30:
        return "stale", Decimal("40")
    return "very_stale", Decimal("0")


def _as_datetime(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _json_reasons(quality: DataQualityRun | None, run: IngestionRun) -> Counter[str]:
    reasons: Counter[str] = Counter()
    metrics = quality.metrics if quality and isinstance(quality.metrics, dict) else {}
    raw = metrics.get("rejection_reasons", {})
    if isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, int):
                reasons[str(key)] += value
    if not reasons and run.error_message:
        try:
            parsed = json.loads(run.error_message)
            if isinstance(parsed, dict):
                reasons.update({str(k): int(v) for k, v in parsed.items()})
        except (TypeError, ValueError):
            pass
    return reasons


def _issue(code: str, severity: str, count: int, message: str) -> dict:
    return {"code": code, "severity": severity, "affected_records": count, "message": message}


def build_data_quality_summary(
    db: Session,
    *,
    commodity_id: str | None = None,
    market_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    reference_datetime: datetime,
) -> DataQualitySummaryResponse:
    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must not be after end_date")

    statement = select(MarketPrice).order_by(MarketPrice.arrival_date, MarketPrice.commodity_id, MarketPrice.market_id, MarketPrice.id)
    if commodity_id:
        statement = statement.where(MarketPrice.commodity_id == commodity_id)
    if market_id:
        statement = statement.where(MarketPrice.market_id == market_id)
    if start_date:
        statement = statement.where(MarketPrice.arrival_date >= start_date)
    if end_date:
        statement = statement.where(MarketPrice.arrival_date <= end_date)
    rows = db.scalars(statement).all()
    ref = _as_datetime(reference_datetime)
    commodity_records = db.scalars(select(Commodity)).all()
    market_records = db.scalars(select(Market)).all()
    commodity_ids = {item.id for item in commodity_records}
    market_ids = {item.id for item in market_records}
    observed_dates = sorted({row.arrival_date for row in rows})
    effective_start = start_date or (observed_dates[0] if observed_dates else None)
    effective_end = end_date or (observed_dates[-1] if observed_dates else None)
    expected = _date_list(effective_start, effective_end)
    missing = sorted(set(expected) - set(observed_dates))
    total = len(rows)

    invalid_price = sum(1 for row in rows if any(value is not None and Decimal(str(value)) < 0 for value in (row.min_price_inr_per_kg, row.max_price_inr_per_kg, row.modal_price_inr_per_kg)))
    invalid_range = sum(1 for row in rows if row.min_price_inr_per_kg is not None and row.max_price_inr_per_kg is not None and (row.min_price_inr_per_kg > row.modal_price_inr_per_kg or row.modal_price_inr_per_kg > row.max_price_inr_per_kg or row.min_price_inr_per_kg > row.max_price_inr_per_kg))
    invalid_date = sum(1 for row in rows if not isinstance(row.arrival_date, date) or row.arrival_date > ref.date())
    invalid_unit = sum(1 for row in rows if row.source_price_unit not in {"INR/kg", "INR/quintal"})
    invalid_arrivals = sum(1 for row in rows if row.arrivals_tonnes is not None and Decimal(str(row.arrivals_tonnes)) < 0)
    invalid_records = sum(1 for row in rows if (any(value is not None and Decimal(str(value)) < 0 for value in (row.min_price_inr_per_kg, row.max_price_inr_per_kg, row.modal_price_inr_per_kg)) or (row.min_price_inr_per_kg is not None and row.max_price_inr_per_kg is not None and (row.min_price_inr_per_kg > row.modal_price_inr_per_kg or row.modal_price_inr_per_kg > row.max_price_inr_per_kg or row.min_price_inr_per_kg > row.max_price_inr_per_kg)) or row.source_price_unit not in {"INR/kg", "INR/quintal"} or (row.arrivals_tonnes is not None and Decimal(str(row.arrivals_tonnes)) < 0)))

    source_seen: set[tuple[str, str]] = set()
    logical_seen: set[tuple[Any, ...]] = set()
    duplicate_source = 0
    duplicate_logical = 0
    for row in rows:
        source_key = (row.source_id, row.source_record_id)
        logical_key = (row.commodity_id, row.market_id, row.arrival_date, row.source_variety or "", row.source_grade or "")
        if source_key in source_seen:
            duplicate_source += 1
        else:
            source_seen.add(source_key)
        if logical_key in logical_seen:
            duplicate_logical += 1
        else:
            logical_seen.add(logical_key)
    duplicate_count = duplicate_source + duplicate_logical

    provenance_fields = ("source_id", "source_record_id", "source_price_unit", "modal_price_inr_per_quintal", "modal_price_inr_per_kg", "ingestion_run_id")
    provenance_complete = sum(1 for row in rows if all(getattr(row, field, None) is not None for field in provenance_fields) and getattr(getattr(row, "source", None), "url", None))
    freshness_age = (ref.date() - max(observed_dates)).days if observed_dates else None
    freshness_label, freshness_pct = _freshness(freshness_age)
    completeness_pct = _percent(len(observed_dates), len(expected)) if expected else Decimal("0")
    valid_pct = _percent(total - invalid_records, total)
    uniqueness_pct = _percent(total - duplicate_count, total)
    provenance_pct = _percent(provenance_complete, total)
    unknown_reference = sum(1 for row in rows if row.commodity_id not in commodity_ids or row.market_id not in market_ids)
    consistency_failures = invalid_range + invalid_unit + invalid_arrivals + invalid_date + unknown_reference
    consistency_pct = _percent(total - min(total, consistency_failures), total)
    component_values = {"completeness": completeness_pct, "validity": valid_pct, "uniqueness": uniqueness_pct, "freshness": freshness_pct, "provenance": provenance_pct, "consistency": consistency_pct}
    score = sum((component_values[name] * weight / Decimal("100") for name, weight in QUALITY_WEIGHTS.items()), Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    classification = _classify(score)

    valid_rows = total - invalid_records - duplicate_count
    coverage_for_gate = completeness_pct
    forecast_ready = total >= MIN_FORECAST_OBSERVATIONS and coverage_for_gate >= MIN_COVERAGE_PERCENT and valid_pct >= MIN_VALIDITY_PERCENT and duplicate_count == 0 and invalid_records == 0
    market_count = len({row.market_id for row in rows})
    recommendation_ready = forecast_ready and freshness_age is not None and freshness_age <= 7 and market_count >= 2
    zero_price = sum(1 for row in rows if row.modal_price_inr_per_kg is not None and Decimal(str(row.modal_price_inr_per_kg)) == 0)
    extreme_price_change = 0
    by_series: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for row in rows:
        by_series[(row.commodity_id, row.market_id)].append(row)
    for series in by_series.values():
        ordered = sorted(series, key=lambda item: (item.arrival_date, item.id))
        for previous, current in zip(ordered, ordered[1:]):
            previous_price = Decimal(str(previous.modal_price_inr_per_kg)) if previous.modal_price_inr_per_kg is not None else None
            current_price = Decimal(str(current.modal_price_inr_per_kg)) if current.modal_price_inr_per_kg is not None else None
            if previous_price and current_price is not None and abs(current_price - previous_price) / previous_price >= Decimal("1"):
                extreme_price_change += 1
    arrivals = sorted(Decimal(str(row.arrivals_tonnes)) for row in rows if row.arrivals_tonnes is not None and Decimal(str(row.arrivals_tonnes)) >= 0)
    median_arrivals = arrivals[len(arrivals) // 2] if arrivals else Decimal("0")
    unusually_high_arrivals = sum(1 for row in rows if median_arrivals > 0 and row.arrivals_tonnes is not None and Decimal(str(row.arrivals_tonnes)) > median_arrivals * Decimal("10"))
    readiness = "recommendation_ready" if recommendation_ready else "forecast_ready" if forecast_ready else "evidence_limited" if valid_rows > 0 else "insufficient_data"

    critical: list[dict] = []
    warnings: list[dict] = []
    info: list[dict] = []
    if not rows:
        critical.append(_issue("no_observations", "critical", 0, "No market-price records match the selected filters."))
    if invalid_records:
        critical.append(_issue("invalid_records", "critical", invalid_records, "Persisted observations contain invalid price, unit, date, or arrival values."))
    if unknown_reference:
        critical.append(_issue("unknown_reference", "critical", unknown_reference, "Observations reference a commodity or market absent from the reference tables."))
    if invalid_range:
        warnings.append(_issue("unusual_min_modal_max_relationship", "warning", invalid_range, "Min/modal/max price ordering is inconsistent."))
    if zero_price:
        warnings.append(_issue("suspicious_zero_price", "warning", zero_price, "Zero modal prices are present and require source review."))
    if extreme_price_change:
        warnings.append(_issue("extreme_price_change", "warning", extreme_price_change, "A consecutive same-series modal price changed by at least 100%."))
    if unusually_high_arrivals:
        warnings.append(_issue("unusually_high_arrivals", "warning", unusually_high_arrivals, "Arrivals exceed ten times the deterministic series median."))
    if missing:
        warnings.append(_issue("missing_dates", "warning", len(missing), f"{len(missing)} expected calendar date(s) are not observed."))
    if duplicate_count:
        warnings.append(_issue("duplicate_observations", "warning", duplicate_count, "Duplicate source or logical observations are present."))
    if freshness_age is not None and freshness_age > 7:
        warnings.append(_issue("stale_data", "warning", total, f"The latest observation is {freshness_age} day(s) old."))
    if total and total < MIN_FORECAST_OBSERVATIONS:
        warnings.append(_issue("sparse_history", "warning", total, f"Only {total} usable observation(s) are available; forecasting requires {MIN_FORECAST_OBSERVATIONS}."))
    if invalid_records == 0 and total:
        info.append(_issue("valid_observations", "info", total, "No deterministic invalid-value checks failed."))
    limitations: list[str] = []
    if not rows: limitations.append("no_historical_data")
    if missing: limitations.append("missing_calendar_dates")
    if duplicate_count: limitations.append("duplicate_observations")
    if unknown_reference: limitations.append("unknown_reference")
    if zero_price: limitations.append("suspicious_zero_price")
    if extreme_price_change: limitations.append("extreme_price_change")
    if unusually_high_arrivals: limitations.append("unusually_high_arrivals")
    if provenance_complete < total: limitations.append("incomplete_provenance")
    if freshness_age is None or freshness_age > 7: limitations.append("stale_or_unavailable_latest_observation")
    if total < MIN_FORECAST_OBSERVATIONS: limitations.append("insufficient_forecast_history")
    if recommendation_ready is False and total and market_count < 2: limitations.append("insufficient_market_comparison")

    matrix: list[dict] = []
    grouped: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for row in rows: grouped[(row.commodity_id, row.market_id)].append(row)
    commodities = {item.id: item.name for item in commodity_records}
    markets = {item.id: item.name for item in market_records}
    for (cid, mid), group in sorted(grouped.items()):
        dates = sorted({item.arrival_date for item in group})
        matrix_start, matrix_end = start_date or dates[0], end_date or dates[-1]
        matrix_expected = _date_list(matrix_start, matrix_end)
        matrix_missing = sorted(set(matrix_expected) - set(dates))
        matrix.append({"commodity_id": cid, "commodity": commodities.get(cid), "market_id": mid, "market": markets.get(mid), "first_observation": dates[0], "last_observation": dates[-1], "observation_count": len(group), "expected_dates": len(matrix_expected), "observed_dates": len(dates), "coverage_percent": _percent(len(dates), len(matrix_expected)), "missing_dates": matrix_missing, "latest_price_date": dates[-1]})

    latest_run = _latest_ingestion(db, {row.ingestion_run_id for row in rows if row.ingestion_run_id is not None})
    ingestion = {"latest_run": _ingestion_summary(db, latest_run) if latest_run else None, "runs_considered": len({row.ingestion_run_id for row in rows if row.ingestion_run_id is not None})}
    return DataQualitySummaryResponse.model_validate({
        "overall": {"score": score, "classification": classification, "readiness": readiness, "generated_at": ref, "reference_datetime": ref},
        "dimensions": {name: {"score": (component_values[name] * QUALITY_WEIGHTS[name] / Decimal("100")).quantize(Decimal("0.01")), "maximum": QUALITY_WEIGHTS[name], "details": {"raw_percent": component_values[name]}} for name in QUALITY_WEIGHTS},
        "coverage": {"start_date": effective_start, "end_date": effective_end, "expected_dates": len(expected), "observed_dates": len(observed_dates), "missing_dates": missing, "coverage_percent": completeness_pct},
        "records": {"total": total, "valid": valid_rows, "invalid": invalid_records, "duplicates": duplicate_count, "duplicate_source_records": duplicate_source, "duplicate_logical_observations": duplicate_logical, "missing_price": sum(1 for row in rows if row.modal_price_inr_per_kg is None), "missing_arrivals": sum(1 for row in rows if row.arrivals_tonnes is None), "rejected": (latest_run.records_rejected if latest_run else 0)},
        "provenance": {"complete": provenance_complete, "incomplete": total - provenance_complete, "coverage_percent": provenance_pct},
        "ingestion": ingestion,
        "coverage_matrix": matrix,
        "issues": {"critical": critical, "warnings": warnings, "informational": info},
        "limitations": list(dict.fromkeys(limitations)),
    })


def _latest_ingestion(db: Session, ids: set[int]) -> IngestionRun | None:
    if not ids:
        return None
    return db.scalar(select(IngestionRun).where(IngestionRun.id.in_(ids)).order_by(IngestionRun.completed_at.desc(), IngestionRun.id.desc()).limit(1))


def _ingestion_summary(db: Session, run: IngestionRun) -> dict:
    quality = db.scalar(select(DataQualityRun).where(DataQualityRun.ingestion_run_id == run.id).order_by(DataQualityRun.created_at.desc()).limit(1))
    reasons = _json_reasons(quality, run)
    source = run.source
    return {"ingestion_run_id": run.id, "source": source.name if source else None, "resource": source.url if source else None, "source_type": source.source_type if source else None, "started_at": run.started_at, "completed_at": run.completed_at, "status": run.status, "records_seen": run.records_read, "records_accepted": run.records_loaded, "records_rejected": run.records_rejected, "rejection_count_by_reason": dict(sorted(reasons.items())), "duplicate_count": run.duplicates, "snapshot_reference": source.url if source else None}
