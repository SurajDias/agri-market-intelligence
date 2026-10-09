"""Load normalized price records into the Stage 1 PostgreSQL schema."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import Commodity, DataQualityRun, DataSource, IngestionRun, Market, MarketPrice
from etl.data_quality import build_quality_metrics
from etl.transform import NormalizedPriceRecord, TransformReport


def _missing_count(report: TransformReport) -> int:
    return report.missing_commodity + report.missing_market + report.missing_date + report.missing_price


def _get_or_create_source(session: Session, source_id: str, source_name: str, source_url: str, source_type: str = "government_api") -> DataSource:
    source = session.get(DataSource, source_id)
    if source is None:
        source = DataSource(id=source_id, name=source_name, url=source_url, source_type=source_type, is_active=True)
        session.add(source)
        session.flush()
    return source


def load_records(
    session: Session,
    records: Iterable[NormalizedPriceRecord],
    report: TransformReport,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
) -> dict[str, int | float | dict[str, int]]:
    """Idempotently load records matching existing reference data.

    Commodities and markets are never created by the loader. Unmatched or
    ambiguous reference records are rejected and included in the run metrics.
    """
    now = datetime.now(timezone.utc)
    source = _get_or_create_source(session, source_id, source_name, source_url)
    ingestion_run = IngestionRun(
        source_id=source.id,
        started_at=now,
        status="RUNNING",
        records_read=report.records_read,
    )
    session.add(ingestion_run)
    session.flush()

    loaded = 0
    loader_rejected = 0
    duplicate_records = report.duplicate_records
    rejection_reasons: Counter[str] = Counter(report.rejection_reasons)

    try:
        for record in records:
            commodities = session.scalars(
                select(Commodity).where(
                    Commodity.normalized_name == record.commodity_normalized_name,
                    Commodity.is_active.is_(True),
                )
            ).all()
            markets = session.scalars(
                select(Market).where(
                    Market.normalized_name == record.market_normalized_name,
                    func.lower(Market.state) == record.state,
                    func.lower(Market.district) == record.district,
                    Market.is_active.is_(True),
                )
            ).all()
            if len(commodities) != 1:
                loader_rejected += 1
                rejection_reasons["commodity_reference_not_found_or_ambiguous"] += 1
                continue
            if len(markets) != 1:
                loader_rejected += 1
                rejection_reasons["market_reference_not_found_or_ambiguous"] += 1
                continue

            commodity = commodities[0]
            market = markets[0]
            existing = session.scalar(
                select(MarketPrice).where(
                    MarketPrice.commodity_id == commodity.id,
                    MarketPrice.market_id == market.id,
                    MarketPrice.arrival_date == record.arrival_date,
                    MarketPrice.source_id == source.id,
                    MarketPrice.source_record_id == record.source_record_id,
                )
            )
            if existing is not None:
                duplicate_records += 1
                rejection_reasons["duplicate_existing"] += 1
                continue

            session.add(
                MarketPrice(
                    commodity_id=commodity.id,
                    market_id=market.id,
                    ingestion_run_id=ingestion_run.id,
                    arrival_date=record.arrival_date,
                    source_arrival_date=record.source_arrival_date,
                    source_state=record.source_state,
                    source_district=record.source_district,
                    source_market_name=record.source_market_name,
                    source_commodity_name=record.source_commodity_name,
                    source_variety=record.source_variety,
                    source_grade=record.source_grade,
                    source_price_unit=record.source_price_unit,
                    min_price_inr_per_quintal=record.min_price_inr_per_quintal,
                    max_price_inr_per_quintal=record.max_price_inr_per_quintal,
                    modal_price_inr_per_quintal=record.modal_price_inr_per_quintal,
                    min_price_inr_per_kg=record.min_price_inr_per_kg,
                    max_price_inr_per_kg=record.max_price_inr_per_kg,
                    modal_price_inr_per_kg=record.modal_price_inr_per_kg,
                    arrivals_tonnes=record.arrivals_tonnes,
                    source_id=source.id,
                    source_record_id=record.source_record_id,
                    ingested_at=now,
                    created_at=now,
                )
            )
            loaded += 1

        rejected = report.records_rejected + loader_rejected
        metrics = build_quality_metrics(report, records_loaded=loaded, reference_rejections=loader_rejected)
        metrics["duplicate_records"] = duplicate_records
        metrics["rejection_reasons"] = dict(rejection_reasons)
        quality_score = (loaded / report.records_read * 100) if report.records_read else 0.0
        ingestion_run.completed_at = datetime.now(timezone.utc)
        ingestion_run.status = "SUCCESS"
        ingestion_run.records_loaded = loaded
        ingestion_run.records_rejected = rejected
        ingestion_run.missing_values = _missing_count(report)
        ingestion_run.duplicates = duplicate_records
        ingestion_run.error_message = json.dumps(dict(rejection_reasons), sort_keys=True) if rejection_reasons else None
        session.add(
            DataQualityRun(
                ingestion_run_id=ingestion_run.id,
                overall_score=quality_score,
                missing_values=_missing_count(report),
                duplicate_records=duplicate_records,
                invalid_records=report.invalid_price + report.invalid_range + report.invalid_date + report.future_date,
                metrics=metrics,
                created_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
        return {"records_read": report.records_read, "records_loaded": loaded, "records_rejected": rejected, "duplicate_records": duplicate_records, "quality_score": quality_score, "metrics": metrics}
    except Exception:
        session.rollback()
        raise
