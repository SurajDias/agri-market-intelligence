import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from pydantic import ValidationError

from backend.engine.evidence import assess_evidence
from backend.schemas.evidence import EvidenceAssessmentRequest


def row(day, price):
    return SimpleNamespace(
        id=day.isoformat(),
        commodity_id="tomato",
        market_id="mandya",
        arrival_date=day,
        modal_price_inr_per_kg=price,
        min_price_inr_per_kg=price,
        max_price_inr_per_kg=price,
        arrivals_tonnes=1,
        source_id="government",
        source_record_id=day.isoformat(),
    )


class EvidenceTests(unittest.TestCase):
    def request(self, **overrides):
        values = {
            "commodity_id": "tomato",
            "market_id": "mandya",
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 1, 10),
            "reference_datetime": datetime(2026, 1, 11, tzinfo=timezone.utc),
        }
        values.update(overrides)
        return EvidenceAssessmentRequest(**values)

    def test_no_historical_data_is_insufficient(self):
        result = assess_evidence(self.request(), [])
        self.assertEqual(result.confidence_classification, "insufficient_evidence")
        self.assertEqual(result.evidence_quality_score, Decimal("0"))
        self.assertIn("no_historical_observations", result.critical_gates)
        self.assertIsNone(result.last_observation_date)

    def test_short_history_is_gated(self):
        result = assess_evidence(self.request(), [row(date(2026, 1, 10), 20)])
        self.assertEqual(result.confidence_classification, "insufficient_evidence")
        self.assertIn("insufficient_history", result.critical_gates)

    def test_strong_coverage_has_higher_score(self):
        observations = [row(date(2026, 1, day), 20 + day % 3) for day in range(1, 31)]
        result = assess_evidence(
            self.request(
                end_date=date(2026, 1, 30),
                reference_datetime=datetime(2026, 1, 31, tzinfo=timezone.utc),
            ),
            observations,
        )
        self.assertGreaterEqual(result.evidence_quality_score, Decimal("65"))
        self.assertIn("strong_historical_coverage", [reason.code for reason in result.evidence_reasons])

    def test_stale_and_recent_freshness(self):
        stale = assess_evidence(
            self.request(reference_datetime=datetime(2026, 3, 1, tzinfo=timezone.utc)),
            [row(date(2026, 1, 10), 20), row(date(2026, 1, 10), 21)],
        )
        self.assertEqual(stale.freshness_age_days, 50)
        self.assertIn("stale_market_data", stale.limitations)
        recent = assess_evidence(
            self.request(reference_datetime=datetime(2026, 1, 11, tzinfo=timezone.utc)),
            [row(date(2026, 1, 9), 20), row(date(2026, 1, 10), 21)],
        )
        self.assertEqual(recent.freshness_age_days, 1)
        self.assertIn("recent_observation", [reason.code for reason in recent.evidence_reasons])

    def test_missing_dates_reduce_coverage(self):
        result = assess_evidence(
            self.request(), [row(date(2026, 1, 1), 20), row(date(2026, 1, 10), 21)]
        )
        self.assertEqual(result.missing_date_count, 8)
        self.assertLess(result.calendar_coverage_percent, Decimal("50"))
        self.assertIn("insufficient_calendar_coverage", result.critical_gates)
        self.assertIn("missing_dates", [reason.code for reason in result.evidence_reasons])

    def test_forecast_good_and_poor_error(self):
        observations = [row(date(2026, 1, day), 20) for day in range(1, 11)]
        good = assess_evidence(self.request(forecast_evaluation={
            "strategy_name": "naive_last_value", "horizon": 1, "evaluated": True,
            "mae": 1, "rmse": 1.5, "mape": 5, "evaluation_observation_count": 8,
        }), observations)
        poor = assess_evidence(self.request(forecast_evaluation={
            "strategy_name": "naive_last_value", "horizon": 1, "evaluated": True,
            "mae": 10, "rmse": 12, "mape": 40, "evaluation_observation_count": 8,
        }), observations)
        self.assertTrue(good.forecast_evidence_available)
        self.assertGreater(good.evidence_quality_score, poor.evidence_quality_score)
        self.assertIn("low_forecast_error", [reason.code for reason in good.evidence_reasons])
        self.assertIn("high_forecast_error", [reason.code for reason in poor.evidence_reasons])

    def test_forecast_not_evaluated_is_explicit_limitation(self):
        result = assess_evidence(self.request(), [row(date(2026, 1, 1), 20), row(date(2026, 1, 10), 21)])
        self.assertFalse(result.forecast_evidence_available)
        self.assertIn("forecast_not_evaluated", result.limitations)
        self.assertEqual(result.provenance["forecast_metrics"], "unavailable")

    def test_high_opportunity_context_does_not_create_confidence(self):
        result = assess_evidence(self.request(decision_context={
            "expected_net_value": 100000, "opportunity_score": 99,
        }), [row(date(2026, 1, 10), 20)])
        self.assertEqual(result.confidence_classification, "insufficient_evidence")
        self.assertEqual(result.decision_trace["economic_calculation"]["opportunity_score"], Decimal("99"))

    def test_assumptions_provenance_and_limitations(self):
        result = assess_evidence(self.request(decision_context={
            "quantity_kg": 100, "expected_selling_price_per_kg": 20,
            "transport_cost": 100, "estimated_spoilage_kg": 5,
            "expected_net_value": -50, "shelf_life_status": "near_expiry",
            "assumption_flags": ["price_assumption", "distance_assumption", "transport_rate_assumption", "spoilage_assumption"],
        }), [row(date(2026, 1, 10), 20), row(date(2026, 1, 9), 19)])
        self.assertEqual(result.provenance["economic_context"], "supplied_by_caller")
        self.assertIn("price_assumption", result.limitations)
        self.assertIn("near_expiry_product", result.limitations)
        self.assertIn("negative_expected_net_value", result.limitations)

    def test_trace_is_deterministic(self):
        request = self.request()
        observations = [row(date(2026, 1, 9), 19), row(date(2026, 1, 10), 20)]
        first = assess_evidence(request, observations)
        second = assess_evidence(request, observations)
        self.assertEqual(first.model_dump(), second.model_dump())

    def test_reference_datetime_and_invalid_inputs(self):
        with self.assertRaises(ValueError):
            assess_evidence(self.request(reference_datetime=datetime(2025, 1, 1)), [row(date(2026, 1, 10), 20), row(date(2026, 1, 9), 19)])
        with self.assertRaises(ValidationError):
            self.request(start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            self.request(forecast_evaluation={"evaluated": True, "evaluation_observation_count": 0})


if __name__ == "__main__":
    unittest.main()
