# Data Quality, Provenance & Evidence Readiness

The Stage 4.8 engine is a read-only orchestration layer over the existing
ingestion foundation. It measures persisted `market_prices`, joins source and
run metadata, and exposes deterministic quality/readiness evidence. It does
not correct, fill, delete, or synthesize observations.

```text
data.gov.in adapter / other source
              |
       etl.transform + etl.load
              |
  market_prices  data_sources  ingestion_runs
       |               |              |
       +---------------+--------------+
                       |
             services.data_quality
                       |
     /api/data-quality/summary (typed contract)
```

## Scope and filters

`GET /api/data-quality/summary` accepts optional `commodity_id`, `market_id`,
`start_date`, and `end_date`. `reference_datetime` is required. A reversed
date range returns HTTP 422. If no date range is supplied, the observed minimum
and maximum dates define the coverage interval; no dates are generated as
observations.

## Quality score

The score is a readiness score, not forecast accuracy, confidence, probability,
or source trust. Each dimension is independently returned with its raw
percentage and weighted contribution:

| Dimension | Weight | Formula |
| --- | ---: | --- |
| completeness | 25 | observed distinct dates / expected calendar dates × 100 |
| validity | 20 | non-invalid persisted rows / total rows × 100 |
| uniqueness | 15 | rows minus duplicate counts / total rows × 100 |
| freshness | 15 | 100 for age 0–2 days, 75 for 3–7, 40 for 8–30, 0 for >30 or unavailable |
| provenance | 15 | complete provenance rows / total rows × 100 |
| consistency | 10 | rows without deterministic consistency failures / total rows × 100 |

`score = Σ(raw_dimension_percentage × weight / 100)`, rounded to two decimal
places and bounded to 0–100. Empty data scores 0. Invalid rows include
negative prices, invalid min/modal/max relationships, unsupported units, and
negative arrivals. Consistency failures include those checks plus future/invalid
dates. The distinction is intentional: a value can affect both validity and
consistency when appropriate.

Quality classification thresholds are exact: `excellent >= 90`,
`good >= 75`, `acceptable >= 60`, `poor >= 40`, and `unusable < 40`.

## Readiness gates

Readiness is separate from the score:

* `insufficient_data`: zero persisted rows after filtering, or no valid rows.
* `forecast_ready`: at least 30 rows, at least 80% calendar coverage, at least
  95% valid rows, zero duplicate counts, and zero invalid rows.
* `recommendation_ready`: all forecast gates, latest observation age at most 7
  days, and at least two distinct markets for comparison.
* `evidence_limited`: usable rows exist but one or more gates fail.

Recommendation readiness takes precedence over forecast readiness. A sparse,
stale, duplicate, or incomplete dataset therefore cannot be labelled ready by
score alone.

## Dimensions and checks

Completeness reports expected dates, observed dates, missing dates, coverage,
missing modal-price count, and missing arrivals count. Validity checks persisted
negative values, invalid price relationships, unsupported units, invalid/future
dates, and negative arrivals. Malformed numeric values are rejected earlier by
`etl.transform`; because canonical persisted numeric columns cannot contain
them, the summary does not pretend to rediscover them.

Source duplicates use `(source_id, source_record_id)`. Logical duplicates use
`(commodity_id, market_id, arrival_date, source_variety, source_grade)`, so
variety/grade distinctions are retained. Counts are factual flags only; rows
are never removed by the summary.

Freshness is `reference_datetime.date() - latest_observation_date`. Negative
ages are classified as `future_reference`; the API never silently substitutes
the system clock.

## Provenance and source identity

A price row is provenance-complete only when it has source identity with a
non-empty source URL/resource, source record ID, source unit, raw/canonical
modal price values, and ingestion run ID. The API
returns complete, incomplete, and coverage percentage. Source identity is
reported from `data_sources` (name, URL/resource, source type); no numerical
trust score is invented. Missing source metadata is represented as `null` and
becomes the `incomplete_provenance` limitation.

## Ingestion aggregation and issues

The latest run associated with selected rows is reported from
`ingestion_runs`. It includes run ID, source/resource, times, status, records
seen/accepted/rejected, duplicate count, and rejection reasons. Reasons are
read from the existing `data_quality_runs.metrics.rejection_reasons`, falling
back to the loader's persisted `error_message` JSON. No reason is emitted if
it is not present in those records.

Issues are structured as `{code, severity, affected_records, message}` with
`critical`, `warning`, and `info` buckets. Current deterministic codes include
`no_observations`, `invalid_records`, `missing_dates`,
`duplicate_observations`, `stale_data`, `sparse_history`, and
`valid_observations`, plus `extreme_price_change`,
`unusual_min_modal_max_relationship`, `suspicious_zero_price`, and
`unusually_high_arrivals`. An extreme change is an absolute consecutive
same-series modal-price change of at least 100%; unusually high arrivals are
greater than ten times the deterministic median of non-negative arrivals.
ETL rejection codes remain source/transform facts, such
as `missing_commodity`, `invalid_date`, `future_date`, `malformed_price`,
`negative_price`, `invalid_price_range`, `duplicate`,
`commodity_reference_not_found_or_ambiguous`, and
`market_reference_not_found_or_ambiguous`.

The coverage matrix is grouped by commodity and market and returns first/last
date, observation count, expected/observed dates, missing dates, coverage, and
latest price date. No ML anomaly detector is used. Deterministic anomaly-style
signals are represented only by the documented checks and flags above; this
stage does not silently alter flagged observations.

## Empty database and limitations

With zero `market_prices`, the response contains zero observations and
coverage, score 0, classification `unusable`, readiness `insufficient_data`,
and the `no_historical_data` limitation. It contains no fabricated freshness,
ingestion, source, or quality metrics. This service does not manufacture
provider trust, infer forecast accuracy, or replace the distinct Stage 4.5/4.7
evidence and confidence concepts.

## Response shape

The response contains `overall`, six inspectable `dimensions`, `coverage`,
`records`, `provenance`, `ingestion`, `coverage_matrix`, structured `issues`,
and `limitations`. `overall.reference_datetime` and `overall.generated_at`
both identify the caller-supplied deterministic reference; they are not used
to claim an external ingestion timestamp.
