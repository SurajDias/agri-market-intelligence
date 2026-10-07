import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace

from backend.services.data_quality import build_data_quality_summary


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeSession:
    def __init__(self, prices, commodities=(), markets=(), runs=(), qualities=()):
        self.queues = [prices, commodities, markets, runs, qualities]

    def scalars(self, _statement):
        return ScalarResult(self.queues.pop(0))

    def scalar(self, _statement):
        values = self.queues.pop(0)
        return values[0] if values else None


def price(day, *, cid="tomato", mid="mandya", source_record_id=None, variety="Local", grade="FAQ", modal=10, minimum=9, maximum=11, unit="INR/kg", arrivals=2, ingestion_run_id=1, row_id=1):
    return SimpleNamespace(
        id=row_id, commodity_id=cid, market_id=mid, arrival_date=day,
        source_variety=variety, source_grade=grade, source_id="gov", source_record_id=source_record_id or f"{cid}-{mid}-{day}",
        source_price_unit=unit, min_price_inr_per_kg=minimum, max_price_inr_per_kg=maximum, modal_price_inr_per_kg=modal,
        min_price_inr_per_quintal=minimum * 100, max_price_inr_per_quintal=maximum * 100, modal_price_inr_per_quintal=modal * 100,
        arrivals_tonnes=arrivals, ingestion_run_id=ingestion_run_id,
        source=SimpleNamespace(name="Government source", url="https://example.invalid/resource"),
    )


REFERENCE = datetime(2026, 10, 7, tzinfo=timezone.utc)


class DataQualityServiceTests(unittest.TestCase):
    def build(self, rows, **kwargs):
        return build_data_quality_summary(
            FakeSession(rows, [SimpleNamespace(id="tomato", name="Tomato")], [SimpleNamespace(id="mandya", name="Mandya"), SimpleNamespace(id="kolar", name="Kolar")]),
            reference_datetime=REFERENCE, **kwargs,
        )

    def test_empty_database_is_explicitly_unusable(self):
        result = self.build([])
        self.assertEqual(result.overall["score"], 0)
        self.assertEqual(result.overall["classification"], "unusable")
        self.assertEqual(result.overall["readiness"], "insufficient_data")
        self.assertEqual(result.records["total"], 0)
        self.assertIn("no_historical_data", result.limitations)
        self.assertIsNone(result.ingestion["latest_run"])

    def test_perfect_rows_are_deterministic_and_have_inspectable_components(self):
        rows = [price(date(2026, 10, day), row_id=day) for day in range(1, 8)]
        first = self.build(rows, start_date=date(2026, 10, 1), end_date=date(2026, 10, 7))
        second = self.build(rows, start_date=date(2026, 10, 1), end_date=date(2026, 10, 7))
        self.assertEqual(first.model_dump(), second.model_dump())
        self.assertEqual(first.dimensions["completeness"].maximum, 25)
        self.assertEqual(first.coverage["coverage_percent"], 100)
        self.assertEqual(first.provenance.coverage_percent, 100)

    def test_missing_dates_invalid_values_and_duplicates_are_not_hidden(self):
        rows = [price(date(2026, 10, 1), row_id=1), price(date(2026, 10, 3), source_record_id="same", row_id=2), price(date(2026, 10, 3), source_record_id="same", row_id=3, minimum=-1)]
        result = self.build(rows, start_date=date(2026, 10, 1), end_date=date(2026, 10, 4))
        self.assertEqual(result.coverage["missing_dates"], [date(2026, 10, 2), date(2026, 10, 4)])
        self.assertGreaterEqual(result.records["duplicates"], 2)
        self.assertEqual(result.records["invalid"], 1)
        self.assertIn("missing_calendar_dates", result.limitations)

    def test_freshness_uses_explicit_reference_datetime(self):
        result = self.build([price(date(2026, 9, 1))])
        self.assertEqual(result.dimensions["freshness"].details["raw_percent"], 0)
        self.assertTrue(any(issue.code == "stale_data" for issue in result.issues["warnings"]))

    def test_extreme_price_change_is_a_deterministic_flag(self):
        result = self.build([price(date(2026, 10, 1), modal=10, row_id=1), price(date(2026, 10, 2), modal=25, row_id=2)])
        self.assertTrue(any(issue.code == "extreme_price_change" for issue in result.issues["warnings"]))

    def test_invalid_date_range_is_rejected(self):
        with self.assertRaises(ValueError):
            self.build([], start_date=date(2026, 10, 2), end_date=date(2026, 10, 1))

    def test_ingestion_reasons_are_only_read_from_persisted_run_data(self):
        run = SimpleNamespace(id=4, source=SimpleNamespace(name="Gov", url="resource-1", source_type="api"), started_at=REFERENCE, completed_at=REFERENCE, status="SUCCESS", records_read=3, records_loaded=2, records_rejected=1, duplicates=1, error_message=None)
        quality = SimpleNamespace(metrics={"rejection_reasons": {"invalid_date": 1}}, created_at=REFERENCE)
        session = FakeSession([price(date(2026, 10, 6))], [SimpleNamespace(id="tomato", name="Tomato")], [SimpleNamespace(id="mandya", name="Mandya")], [run], [quality])
        result = build_data_quality_summary(session, reference_datetime=REFERENCE)
        self.assertEqual(result.ingestion["latest_run"]["rejection_count_by_reason"], {"invalid_date": 1})


if __name__ == "__main__":
    unittest.main()
