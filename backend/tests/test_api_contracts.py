"""Dependency-light contract smoke tests.

Full HTTP/database tests should run with PostgreSQL and an HTTP test client.
These tests verify that the application imports and registers Stage 1 routes.
"""

import unittest
from datetime import date
from unittest.mock import patch
from types import SimpleNamespace

from backend.main import app
from backend.api.routes.markets import list_commodities, list_market_prices, list_markets
from backend.schemas.commodity import CommodityResponse
from backend.schemas.market import MarketResponse


class ApiContractTests(unittest.TestCase):
    def test_health_route_is_registered(self):
        self.assertIn("/api/health", app.openapi()["paths"])

    def test_reference_routes_are_registered(self):
        paths = set(app.openapi()["paths"])
        self.assertIn("/api/markets", paths)
        self.assertIn("/api/markets/{market_id}", paths)
        self.assertIn("/api/commodities", paths)
        self.assertIn("/api/markets/{market_id}/prices", paths)
        self.assertIn("/api/forecasts/evaluate", paths)
        self.assertIn("/api/transport/calculate", paths)
        self.assertIn("/api/shelf-life/estimate", paths)
        self.assertIn("/api/decision/calculate", paths)
        self.assertIn("/api/recommendations/analyze", paths)
        self.assertIn("/api/evidence/assess", paths)
        self.assertIn("/api/simulator/analyze", paths)
        self.assertIn("/api/decision-intelligence/analyze", paths)

    def test_response_models_expose_frontend_fields(self):
        self.assertIn("shelfLifeDays", CommodityResponse.model_fields)
        self.assertIn("type", MarketResponse.model_fields)

    def test_health_reports_database_failure_as_503(self):
        from backend.main import health_check

        with patch("backend.main.check_database_connection", return_value=False):
            response = health_check()
        self.assertEqual(response.status_code, 503)

    def test_market_route_returns_database_records(self):
        class Result:
            def all(self):
                return ["market-record"]

        class FakeSession:
            def scalars(self, _statement):
                return Result()

        self.assertEqual(list_markets(db=FakeSession()), ["market-record"])

    def test_commodity_route_returns_database_records(self):
        class Result:
            def all(self):
                return ["commodity-record"]

        class FakeSession:
            def scalars(self, _statement):
                return Result()

        self.assertEqual(list_commodities(db=FakeSession()), ["commodity-record"])

    def test_price_route_returns_empty_result_for_valid_market_without_prices(self):
        class Result:
            def all(self):
                return []

        class FakeSession:
            def get(self, _model, _market_id):
                return SimpleNamespace()

            def scalars(self, _statement):
                return Result()

        self.assertEqual(
            list_market_prices(
                market_id="mandya",
                commodity_id="tomato",
                start_date=date(2026, 10, 1),
                end_date=date(2026, 10, 5),
                db=FakeSession(),
            ),
            [],
        )

    def test_price_route_rejects_unknown_market(self):
        class FakeSession:
            def get(self, _model, _market_id):
                return None

        with self.assertRaises(Exception) as context:
            list_market_prices(market_id="missing", db=FakeSession())
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
