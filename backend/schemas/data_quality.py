from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


Severity = Literal["critical", "warning", "info"]
QualityClassification = Literal["excellent", "good", "acceptable", "poor", "unusable"]
Readiness = Literal["forecast_ready", "recommendation_ready", "evidence_limited", "insufficient_data"]


class QualityDimension(BaseModel):
    score: Decimal
    maximum: Decimal
    details: dict


class QualityIssue(BaseModel):
    code: str
    severity: Severity
    affected_records: int
    message: str


class CoverageEntry(BaseModel):
    commodity_id: str
    commodity: str | None = None
    market_id: str
    market: str | None = None
    first_observation: date | None
    last_observation: date | None
    observation_count: int
    expected_dates: int
    observed_dates: int
    coverage_percent: Decimal | None
    missing_dates: list[date]
    latest_price_date: date | None


class IngestionSummary(BaseModel):
    ingestion_run_id: int
    source: str | None
    resource: str | None
    source_type: str | None
    started_at: datetime
    completed_at: datetime | None
    status: str
    records_seen: int
    records_accepted: int
    records_rejected: int
    rejection_count_by_reason: dict[str, int]
    duplicate_count: int
    snapshot_reference: str | None = None


class ProvenanceSummary(BaseModel):
    complete: int
    incomplete: int
    coverage_percent: Decimal


class DataQualitySummaryResponse(BaseModel):
    overall: dict
    dimensions: dict[str, QualityDimension]
    coverage: dict
    records: dict
    provenance: ProvenanceSummary
    ingestion: dict
    coverage_matrix: list[CoverageEntry]
    issues: dict[str, list[QualityIssue]]
    limitations: list[str]

