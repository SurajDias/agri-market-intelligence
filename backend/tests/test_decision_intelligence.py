import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from pydantic import ValidationError

from backend.engine.decision_intelligence import analyze_decision_intelligence
from backend.schemas.decision_intelligence import DecisionIntelligenceRequest


def row(day, price):
    return SimpleNamespace(
        id=day.isoformat(), commodity_id="tomato", market_id="market",
        arrival_date=day, modal_price_inr_per_kg=price,
        min_price_inr_per_kg=price, max_price_inr_per_kg=price,
        arrivals_tonnes=1, source_id="government", source_record_id=day.isoformat(),
    )


def candidate(market_id, price="25", distance="10", rate="0.1", spoilage="0"):
    return {
        "market_id": market_id,
        "expected_selling_price_per_kg": price,
        "distance_km": distance,
        "transport_rate_per_km_per_kg": rate,
        "estimated_spoilage_kg": spoilage,
        "shelf_life_status": "viable",
    }


class DecisionIntelligenceTests(unittest.TestCase):
    def request(self, candidates=None, **overrides):
        values = {
            "commodity_id": "tomato", "origin_market_id": "origin", "quantity_kg": Decimal("100"),
            "start_date": date(2026, 1, 1), "end_date": date(2026, 1, 10),
            "reference_datetime": datetime(2026, 1, 11, tzinfo=timezone.utc),
            "candidates": [candidate("a"), candidate("b", price="20")] if candidates is None else candidates,
        }
        values.update(overrides)
        return DecisionIntelligenceRequest(**values)

    def observations(self, market_id, count=10):
        return [SimpleNamespace(
            id=f"{market_id}-{day}", commodity_id="tomato", market_id=market_id,
            arrival_date=date(2026, 1, day), modal_price_inr_per_kg=20 + day % 2,
            min_price_inr_per_kg=20 + day % 2, max_price_inr_per_kg=20 + day % 2,
            arrivals_tonnes=1, source_id="government", source_record_id=str(day),
        ) for day in range(1, count + 1)]

    def test_positive_economic_recommendation_and_unified_candidate(self):
        result = analyze_decision_intelligence(
            self.request(), {"a": self.observations("a"), "b": self.observations("b")}, {"a": "A", "b": "B"}
        )
        self.assertEqual(result.final_decision.recommended_market, "a")
        self.assertEqual(result.final_decision.economic_recommendation, "strong_opportunity")
        self.assertEqual(result.ranking, ["a", "b"])
        self.assertEqual(result.candidates[0].market_name, "A")
        self.assertIsNotNone(result.candidates[0].evidence_quality_score)

    def test_no_candidates_and_all_negative(self):
        empty = analyze_decision_intelligence(self.request([]), {})
        self.assertEqual(empty.final_decision.decision_status, "no_opportunity")
        loss = analyze_decision_intelligence(self.request([candidate("loss", price="1", distance="100", rate="1")]), {"loss": []})
        self.assertEqual(loss.final_decision.decision_status, "economically_unfavorable")
        self.assertIsNone(loss.final_decision.recommended_market)

    def test_strong_economics_with_weak_evidence_is_insufficient(self):
        result = analyze_decision_intelligence(self.request(), {"a": [], "b": []})
        self.assertEqual(result.final_decision.recommended_market, "a")
        self.assertEqual(result.final_decision.decision_status, "insufficient_evidence")
        self.assertIn("no_historical_observations", result.data_quality_summary.critical_data_issues)

    def test_forecast_evidence_is_integrated(self):
        request = self.request(forecast_evaluation={
            "strategy_name": "naive_last_value", "horizon": 1, "evaluated": True,
            "mae": 1, "rmse": 1, "mape": 5, "evaluation_observation_count": 8,
        })
        result = analyze_decision_intelligence(request, {"a": self.observations("a"), "b": self.observations("b")})
        self.assertTrue(result.candidates[0].forecast_evidence_available)
        self.assertEqual(result.candidates[0].forecast_strategy, "naive_last_value")
        self.assertIn("forecast_evaluated", result.final_decision.decision_reasons)

    def test_missing_dates_and_assumptions_are_visible(self):
        result = analyze_decision_intelligence(
            self.request(), {"a": self.observations("a", 2), "b": []}
        )
        candidate_result = next(item for item in result.candidates if item.market_id == "a")
        self.assertGreater(candidate_result.missing_date_count, 0)
        self.assertIn("caller_supplied_price", result.assumptions)
        self.assertIn("forecast_not_evaluated", candidate_result.limitations)

    def test_sensitivity_and_robustness_are_integrated(self):
        result = analyze_decision_intelligence(
            self.request(
                scenario={"target_market_id": "a", "price_change_percent": "-30"},
                sensitivity={"target_market_id": "a", "price_values": ["15", "25"]},
            ),
            {"a": self.observations("a"), "b": self.observations("b")},
        )
        self.assertEqual(result.candidates[0].sensitivity_summary["price"]["recommendation_change_at"], Decimal("25"))
        self.assertIn(result.final_decision.robustness_classification, {"highly_robust", "robust", "sensitive", "highly_sensitive"})
        self.assertIn("sensitivity_analysis", result.decision_trace)

    def test_confidence_does_not_change_economic_ranking(self):
        result = analyze_decision_intelligence(
            self.request(reference_datetime=datetime(2026, 1, 31, tzinfo=timezone.utc)),
            {"a": self.observations("a", 30), "b": []},
        )
        self.assertEqual(result.final_decision.recommended_market, "a")
        self.assertEqual(result.ranking[0], "a")
        self.assertEqual(next(item for item in result.candidates if item.market_id == "b").confidence_classification, "insufficient_evidence")

    def test_trace_and_provenance_are_deterministic(self):
        request = self.request()
        observations = {"a": self.observations("a"), "b": self.observations("b")}
        first = analyze_decision_intelligence(request, observations)
        second = analyze_decision_intelligence(request, observations)
        self.assertEqual(first.decision_trace, second.decision_trace)
        self.assertEqual(first.candidates[0].provenance["observation_count"], "measured_from_database")
        self.assertEqual(first.provenance["economic_inputs"], "supplied_by_caller")

    def test_invalid_request_dates_and_duplicates(self):
        with self.assertRaises(ValidationError):
            self.request(start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            self.request([candidate("a"), candidate("a", price="20")])
        with self.assertRaises(ValidationError):
            self.request([candidate("a", spoilage="101")])


if __name__ == "__main__":
    unittest.main()
