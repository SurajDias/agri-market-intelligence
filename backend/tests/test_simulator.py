import unittest
from decimal import Decimal
from types import SimpleNamespace

from pydantic import ValidationError

from backend.api.routes.simulator import analyze_simulation
from backend.engine.simulator import simulate
from backend.schemas.simulator import SimulatorRequest


def candidate(market_id, price="25", distance="10", rate="0.1", spoilage="0"):
    return {
        "market_id": market_id,
        "expected_selling_price_per_kg": price,
        "distance_km": distance,
        "transport_rate_per_km_per_kg": rate,
        "estimated_spoilage_kg": spoilage,
        "shelf_life_status": "viable",
    }


class FakeSession:
    def __init__(self, markets=None, commodities=None):
        self.markets = markets or {}
        self.commodities = commodities or {}

    def get(self, model, identifier):
        return (self.commodities if model.__name__ == "Commodity" else self.markets).get(identifier)


class SimulatorTests(unittest.TestCase):
    def request(self, candidates=None, **overrides):
        values = {
            "commodity_id": "tomato",
            "origin_market_id": "origin",
            "quantity_kg": Decimal("100"),
            "candidates": [candidate("a"), candidate("b", price="20")] if candidates is None else candidates,
        }
        values.update(overrides)
        return SimulatorRequest(**values)

    def test_no_change_reproduces_baseline(self):
        result = simulate(self.request())
        scenario = result.scenarios[0]
        self.assertEqual(scenario.baseline_recommended_market, "a")
        self.assertEqual(scenario.scenario_recommended_market, "a")
        self.assertFalse(scenario.recommendation_changed)
        self.assertEqual(scenario.candidates[0].absolute_changes["expected_net_value"], Decimal("0.00"))

    def test_price_decrease_changes_net_and_recommendation(self):
        result = simulate(self.request(scenario={"target_market_id": "a", "price_change_percent": "-30"}))
        scenario = result.scenarios[0]
        self.assertEqual(scenario.scenario_recommended_market, "b")
        self.assertTrue(scenario.recommendation_changed)
        a = next(item for item in scenario.candidates if item.market_id == "a")
        self.assertEqual(a.scenario.expected_selling_price_per_kg, Decimal("17.50"))
        self.assertLess(a.scenario.expected_net_value, a.baseline.expected_net_value)

    def test_distance_rate_and_spoilage_changes_recalculate(self):
        result = simulate(self.request(scenario={
            "transport_rate_change_percent": "20",
            "distance_change_percent": "10",
            "spoilage_change_percent": "25",
        }))
        item = result.scenarios[0].candidates[0]
        self.assertEqual(item.scenario.transport_rate_per_km_per_kg, Decimal("0.12"))
        self.assertEqual(item.scenario.distance_km, Decimal("11.0"))
        self.assertEqual(item.scenario.estimated_spoilage_kg, Decimal("0"))
        self.assertLess(item.scenario.expected_net_value, item.baseline.expected_net_value)

    def test_break_even_thresholds_are_analytical(self):
        result = simulate(self.request())
        analysis = result.scenarios[0].break_even_analysis
        thresholds = analysis["comparisons"][0]["thresholds"]
        self.assertEqual(thresholds["minimum_price_for_best_market"], Decimal("20"))
        self.assertEqual(thresholds["maximum_transport_cost_for_best_market"], Decimal("600.00"))
        self.assertEqual(thresholds["maximum_distance_km_for_best_market"], Decimal("60"))
        self.assertEqual(thresholds["maximum_spoilage_kg_for_best_market"], Decimal("20"))

    def test_sensitivity_transition_is_deterministic(self):
        result = simulate(self.request(
            [candidate("a", spoilage="20"), candidate("b", price="20")],
            sensitivity={"target_market_id": "a", "price_values": ["15", "25"]},
        ))
        sensitivity = result.sensitivity["price"]
        self.assertEqual([entry["recommended_market"] for entry in sensitivity["values"]], ["b", "a"])
        self.assertEqual(sensitivity["recommendation_change_at"], Decimal("25"))

    def test_scenario_grid_and_limit(self):
        result = simulate(self.request(scenario_grid={
            "price_change_percent": ["0", "-10"],
            "transport_rate_change_percent": ["0", "10"],
        }))
        self.assertEqual(len(result.scenarios), 4)
        with self.assertRaises(ValueError):
            simulate(self.request(scenario_grid={"price_change_percent": [str(value) for value in range(11)], "transport_rate_change_percent": [str(value) for value in range(10)]}))

    def test_robustness_and_explanations(self):
        result = simulate(self.request(scenario={"price_change_percent": "-1"}))
        self.assertIn(result.robustness_analysis["classification"], {"highly_robust", "robust", "sensitive", "highly_sensitive"})
        self.assertIn("recommendation_preserved", result.scenarios[0].explanations)
        self.assertIn("price_is_primary_driver", result.scenarios[0].explanations)
        self.assertIn("changed_variables", result.scenarios[0].trace)

    def test_baseline_is_not_mutated(self):
        request = self.request()
        original = request.candidates[0].expected_selling_price_per_kg
        simulate(request, {})
        self.assertEqual(request.candidates[0].expected_selling_price_per_kg, original)

    def test_empty_and_all_negative_cases(self):
        empty = simulate(self.request([]))
        self.assertIsNone(empty.baseline_recommended_market)
        loss = simulate(self.request([candidate("loss", price="1", distance="100", rate="1")]))
        self.assertIsNone(loss.baseline_recommended_market)
        self.assertEqual(loss.scenarios[0].robustness_analysis["classification"], "indeterminate")

    def test_validation_rejects_conflicts_and_invalid_values(self):
        with self.assertRaises(ValidationError):
            self.request(scenario={"price_change_percent": "10", "expected_selling_price_per_kg": "20"})
        with self.assertRaises(ValidationError):
            self.request([candidate("a", spoilage="101")])
        with self.assertRaises(ValidationError):
            self.request(scenario={"price_change_percent": "-101"})
        with self.assertRaises(ValidationError):
            self.request([candidate("a"), candidate("a", price="20")])

    def test_route_validates_market_references(self):
        request = self.request([candidate("missing")])
        db = FakeSession(markets={"origin": SimpleNamespace(name="Origin")}, commodities={"tomato": SimpleNamespace()})
        with self.assertRaisesRegex(Exception, "Candidate market not found"):
            analyze_simulation(request, db)

    def test_trace_contains_baseline_scenario_and_deltas(self):
        result = simulate(self.request(scenario={"distance_change_percent": "15"}))
        trace = result.scenarios[0].trace
        self.assertIn("baseline_inputs", trace)
        self.assertIn("scenario_inputs", trace)
        self.assertIn("ranking_before", trace)
        self.assertIn("ranking_after", trace)
        self.assertIn("expected_net_value", result.scenarios[0].candidates[0].percentage_changes)


if __name__ == "__main__":
    unittest.main()
