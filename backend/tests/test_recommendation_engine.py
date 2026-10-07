import unittest
from decimal import Decimal
from types import SimpleNamespace

from pydantic import ValidationError

from backend.api.routes.recommendations import analyze_market_recommendations
from backend.engine.recommendation import analyze_recommendation
from backend.schemas.recommendation import RecommendationRequest


class FakeSession:
    def __init__(self, commodities=None, markets=None):
        self.commodities = commodities or {}
        self.markets = markets or {}

    def get(self, model, identifier):
        if model.__name__ == "Commodity":
            return self.commodities.get(identifier)
        return self.markets.get(identifier)


def candidate(market_id, price, distance=10, rate="1", spoilage="0", status="viable"):
    return {
        "market_id": market_id,
        "expected_selling_price_per_kg": price,
        "distance_km": distance,
        "transport_rate_per_km_per_kg": rate,
        "estimated_spoilage_kg": spoilage,
        "shelf_life_status": status,
    }


class RecommendationEngineTests(unittest.TestCase):
    def request(self, candidates, **overrides):
        values = {
            "commodity_id": "tomato",
            "origin_market_id": "origin",
            "quantity_kg": Decimal("100"),
            "origin_expected_selling_price_per_kg": Decimal("20"),
            "candidates": candidates,
        }
        values.update(overrides)
        return RecommendationRequest(**values)

    def test_highest_net_value_wins_over_highest_price(self):
        request = self.request([
            candidate("high-price", 35, distance=100, rate="4"),
            candidate("best-net", 30, distance=10, rate="1"),
        ])
        result = analyze_recommendation(request, {"high-price": "High Price", "best-net": "Best Net"})
        self.assertEqual(result.recommended_market_id, "best-net")
        self.assertEqual([item.market_id for item in result.ranked_candidates], ["best-net", "high-price"])
        self.assertEqual(result.ranked_candidates[0].price_advantage_vs_origin, Decimal("10"))

    def test_deterministic_tie_breaking(self):
        request = self.request([candidate("market-b", 20), candidate("market-a", 20)])
        result = analyze_recommendation(request)
        self.assertEqual([item.market_id for item in result.ranked_candidates], ["market-a", "market-b"])

    def test_single_candidate_gets_full_relative_score(self):
        result = analyze_recommendation(self.request([candidate("only", 25)]))
        self.assertEqual(result.recommended_market_id, "only")
        self.assertEqual(result.ranked_candidates[0].opportunity_score, Decimal("100"))
        self.assertEqual(result.recommendation_label, "strong_opportunity")

    def test_opportunity_score_accounts_for_cost_and_spoilage(self):
        request = self.request([
            candidate("clean", 30, distance=10, rate="1", spoilage="0"),
            candidate("burdened", 30, distance=100, rate="1", spoilage="50", status="near_expiry"),
        ])
        result = analyze_recommendation(request)
        self.assertGreater(result.ranked_candidates[0].opportunity_score, result.ranked_candidates[1].opportunity_score)
        self.assertIn("near_expiry", result.ranked_candidates[1].assumption_flags)

    def test_explanation_and_assumption_flags(self):
        request = self.request([candidate("market", 25, distance=1, rate="1", spoilage="10", status="expired")])
        result = analyze_recommendation(request)
        item = result.ranked_candidates[0]
        self.assertIn("price_assumption", item.assumption_flags)
        self.assertIn("distance_assumption", item.assumption_flags)
        self.assertIn("transport_rate_assumption", item.assumption_flags)
        self.assertIn("spoilage_assumption", item.assumption_flags)
        self.assertIn("expired", item.assumption_flags)
        self.assertIn("Highest expected net value", item.primary_reason)
        self.assertEqual(item.explanation.primary_reason, item.primary_reason)

    def test_all_negative_net_values_do_not_recommend(self):
        result = analyze_recommendation(self.request([candidate("loss", 1, distance=100, rate="1")]))
        self.assertIsNone(result.recommended_market_id)
        self.assertEqual(result.recommendation_label, "avoid")
        self.assertIn("No candidate produces a positive", result.primary_reason)
        self.assertIn("negative expected net value", result.ranked_candidates[0].negative_factors)

    def test_empty_candidates_return_no_opportunity(self):
        result = analyze_recommendation(self.request([]))
        self.assertEqual(result.recommendation_label, "no_opportunity")
        self.assertIsNone(result.recommended_market_id)
        self.assertEqual(result.ranked_candidates, [])

    def test_validation_rejects_duplicate_and_invalid_candidate_values(self):
        with self.assertRaises(ValidationError):
            self.request([candidate("same", 20), candidate("same", 21)])
        for field, value in (
            ("quantity_kg", Decimal("0")),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    self.request([candidate("market", 20)], **{field: value})
        for field, value in (
            ("expected_selling_price_per_kg", "-1"),
            ("distance_km", "-1"),
            ("transport_rate_per_km_per_kg", "-1"),
            ("estimated_spoilage_kg", "-1"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    invalid_candidate = candidate("market", 20)
                    invalid_candidate[field] = value
                    self.request([invalid_candidate])
        with self.assertRaises(ValidationError):
            self.request([candidate("market", 20, spoilage="101")])

    def test_market_validation_rejects_unknown_references(self):
        request = self.request([candidate("missing", 20)])
        db = FakeSession(commodities={"tomato": SimpleNamespace()}, markets={"origin": SimpleNamespace()})
        with self.assertRaisesRegex(Exception, "Candidate market not found"):
            analyze_market_recommendations(request, db)

    def test_route_resolves_market_names(self):
        request = self.request([candidate("market", 20)])
        db = FakeSession(
            commodities={"tomato": SimpleNamespace()},
            markets={"origin": SimpleNamespace(name="Origin"), "market": SimpleNamespace(name="Destination")},
        )
        result = analyze_market_recommendations(request, db)
        self.assertEqual(result.recommended_market_name, "Destination")


if __name__ == "__main__":
    unittest.main()
