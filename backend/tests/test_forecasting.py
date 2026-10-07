import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from backend.api.routes.baseline_forecasts import get_baseline_forecast
from backend.services.forecasting import (
    baseline_forecast,
    build_naive_last_value_forecast,
    compare_strategies,
    evaluate_metrics,
    evaluate_history,
    NaiveLastValueStrategy,
    prepare_history,
    walk_forward_evaluate,
)


def row(day: date, price):
    return SimpleNamespace(
        id=day.isoformat(),
        arrival_date=day,
        modal_price_inr_per_kg=price,
    )


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeSession:
    def __init__(self, rows=None, commodity=True, market=True):
        self.rows = rows or []
        self.commodity = commodity
        self.market = market

    def get(self, model, identifier):
        return SimpleNamespace() if (identifier == "tomato" and self.commodity) or (identifier == "mandya" and self.market) else None

    def scalars(self, statement):
        return ScalarResult(self.rows)


class ForecastingTests(unittest.TestCase):
    def test_prepare_history_sorts_ignores_invalid_values_and_reports_gaps(self):
        prepared = prepare_history(
            [row(date(2026, 1, 3), 12), row(date(2026, 1, 1), 10), row(date(2026, 1, 2), None)]
        )
        self.assertEqual([item.observation_date for item in prepared.observations], [date(2026, 1, 1), date(2026, 1, 3)])
        self.assertEqual(prepared.invalid_price_count, 1)
        self.assertEqual(prepared.missing_dates, [date(2026, 1, 2)])

    def test_no_data_returns_structured_empty_forecast(self):
        result = build_naive_last_value_forecast(prepare_history([]), "tomato", "mandya")
        self.assertEqual(result["status"], "no_data")
        self.assertEqual(result["forecast"], [])
        self.assertIsNone(result["confidence"])

    def test_insufficient_history_returns_no_forecast(self):
        prepared = prepare_history([row(date(2026, 1, 1), 10)])
        result = build_naive_last_value_forecast(prepared, "tomato", "mandya")
        self.assertEqual(result["status"], "insufficient_history")
        self.assertEqual(result["historical_observation_count"], 1)
        self.assertEqual(result["forecast"], [])

    def test_naive_baseline_default_seven_day_horizon(self):
        prepared = prepare_history([row(date(2026, 1, 1), 10), row(date(2026, 1, 3), 12)])
        result = build_naive_last_value_forecast(prepared, "tomato", "mandya")
        self.assertEqual(result["status"], "sufficient_history")
        self.assertEqual(len(result["forecast"]), 7)
        self.assertEqual(result["forecast"][0]["forecast_date"], date(2026, 1, 4))
        self.assertTrue(all(point["predicted_price_per_kg"] == 12 for point in result["forecast"]))
        self.assertEqual(result["model"], "naive_last_value")

    def test_naive_baseline_custom_horizon(self):
        prepared = prepare_history([row(date(2026, 1, 1), 10), row(date(2026, 1, 2), 11)])
        result = build_naive_last_value_forecast(prepared, "tomato", "mandya", horizon=3)
        self.assertEqual(len(result["forecast"]), 3)

    def test_evaluation_metrics(self):
        result = evaluate_metrics([10, 20], [12, 17])
        self.assertEqual(result["observation_count"], 2)
        self.assertEqual(result["mae"], 2.5)
        self.assertAlmostEqual(result["rmse"], (6.5) ** 0.5)
        self.assertAlmostEqual(result["mape"], 17.5)

    def test_mape_ignores_zero_actual_values_safely(self):
        result = evaluate_metrics([0, 10], [5, 12])
        self.assertEqual(result["mape"], 20)
        self.assertIsNone(evaluate_metrics([0], [5])["mape"])

    def test_walk_forward_uses_prior_values_only(self):
        result = walk_forward_evaluate([10, 12, 15, 14], min_history=2)
        self.assertEqual(result["status"], "sufficient_data")
        self.assertEqual(result["evaluation_count"], 2)
        self.assertEqual(result["metrics"]["mae"], 2.0)

    def test_walk_forward_insufficient_data(self):
        result = walk_forward_evaluate([10, 12], min_history=2)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["evaluation_count"], 0)
        self.assertIsNone(result["metrics"]["mae"])

    def test_baseline_strategy_uses_common_interface(self):
        result = NaiveLastValueStrategy().forecast([10, 12], 3)
        self.assertEqual(result.model_name, "naive_last_value")
        self.assertEqual(result.status, "sufficient_history")
        self.assertEqual(result.values, [12.0, 12.0, 12.0])

    def test_horizon_aware_evaluation_supports_one_three_and_seven_days(self):
        values = list(range(1, 13))
        for horizon, expected_count in ((1, 10), (3, 8), (7, 4)):
            result = walk_forward_evaluate(values, horizon=horizon)
            self.assertEqual(result["status"], "sufficient_data")
            self.assertEqual(result["evaluation_count"], expected_count)
            self.assertEqual(result["metrics"]["evaluated_prediction_count"], expected_count)

    def test_walk_forward_horizon_uses_only_prior_observations(self):
        result = walk_forward_evaluate([10, 20, 30, 40, 50], horizon=3, min_history=2)
        self.assertEqual(result["evaluation_count"], 1)
        self.assertEqual(result["metrics"]["mae"], 30.0)

    def test_comparison_selects_best_strategy(self):
        result = compare_strategies([10, 12, 15, 14], horizon=1)
        self.assertEqual(result["best_strategy"], "naive_last_value")
        self.assertEqual(list(result["strategies"]), ["naive_last_value"])

    def test_comparison_has_no_best_strategy_when_data_is_insufficient(self):
        result = compare_strategies([10, 12], horizon=7)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIsNone(result["best_strategy"])

    def test_evaluation_reports_requested_date_gaps_without_filling_them(self):
        prepared = prepare_history(
            [row(date(2026, 1, 1), 10), row(date(2026, 1, 3), 12), row(date(2026, 1, 4), 13)]
        )
        result = evaluate_history(
            prepared, "tomato", "mandya", date(2026, 1, 1), date(2026, 1, 4), 1
        )
        self.assertEqual(result["missing_dates"], [date(2026, 1, 2)])
        self.assertEqual(result["evaluated_prediction_count"], 1)

    def test_baseline_reuses_historical_query(self):
        session = FakeSession([row(date(2026, 1, 1), 10), row(date(2026, 1, 2), 11)])
        result = baseline_forecast(session, "tomato", "mandya", horizon=2)
        self.assertEqual(result["status"], "sufficient_history")
        self.assertEqual(len(result["forecast"]), 2)

    def test_baseline_route_returns_no_data_without_fabricating(self):
        result = get_baseline_forecast(
            commodity_id="tomato",
            market_id="mandya",
            db=FakeSession([]),
        )
        self.assertEqual(result["status"], "no_data")
        self.assertEqual(result["forecast"], [])

    def test_baseline_route_rejects_invalid_horizon(self):
        with self.assertRaises(HTTPException) as context:
            get_baseline_forecast(
                commodity_id="tomato",
                market_id="mandya",
                horizon=0,
                db=FakeSession([]),
            )
        self.assertEqual(context.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
