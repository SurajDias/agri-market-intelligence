import unittest
from decimal import Decimal
from types import SimpleNamespace

from pydantic import ValidationError

from backend.api.routes.transport import calculate_transport
from backend.engine.transport_cost import calculate_transport_cost
from backend.schemas.transport import TransportCostRequest


class FakeSession:
    def __init__(self, markets):
        self.markets = markets

    def get(self, _model, market_id):
        return self.markets.get(market_id)


class TransportCostTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession({"origin": SimpleNamespace(), "destination": SimpleNamespace()})

    def request(self, **overrides):
        values = {
            "origin_market_id": "origin",
            "destination_market_id": "destination",
            "quantity_kg": Decimal("1000"),
            "distance_km": Decimal("50"),
            "transport_rate_per_km_per_kg": Decimal("0.05"),
        }
        values.update(overrides)
        return TransportCostRequest(**values)

    def test_normal_calculation(self):
        result = calculate_transport_cost(
            "origin", "destination", Decimal("1000"), Decimal("50"), Decimal("0.05")
        )
        self.assertEqual(result["transport_cost"], Decimal("2500.00"))

    def test_zero_distance_and_zero_rate(self):
        self.assertEqual(
            calculate_transport_cost("a", "b", Decimal("10"), Decimal("0"), Decimal("2"))["transport_cost"],
            Decimal("0.00"),
        )
        self.assertEqual(
            calculate_transport_cost("a", "b", Decimal("10"), Decimal("2"), Decimal("0"))["transport_cost"],
            Decimal("0.00"),
        )

    def test_decimal_calculation(self):
        result = calculate_transport_cost(
            "a", "b", Decimal("12.5"), Decimal("2.4"), Decimal("0.15")
        )
        self.assertEqual(result["transport_cost"], Decimal("4.50"))

    def test_negative_inputs_are_rejected(self):
        for field, value in (
            ("quantity_kg", Decimal("-1")),
            ("distance_km", Decimal("-1")),
            ("transport_rate_per_km_per_kg", Decimal("-1")),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    self.request(**{field: value})

    def test_response_structure_and_units(self):
        response = calculate_transport(self.request(), self.db)
        self.assertEqual(response["origin"], "origin")
        self.assertEqual(response["destination"], "destination")
        self.assertEqual(response["quantity_kg"], Decimal("1000"))
        self.assertEqual(response["distance_km"], Decimal("50"))
        self.assertEqual(response["transport_rate_per_km_per_kg"], Decimal("0.05"))
        self.assertEqual(response["transport_cost"], Decimal("2500.00"))
        self.assertEqual(response["currency"], "INR")

    def test_unknown_origin_market(self):
        with self.assertRaisesRegex(Exception, "Origin market not found"):
            calculate_transport(self.request(), FakeSession({"destination": SimpleNamespace()}))

    def test_unknown_destination_market(self):
        with self.assertRaisesRegex(Exception, "Destination market not found"):
            calculate_transport(self.request(), FakeSession({"origin": SimpleNamespace()}))


if __name__ == "__main__":
    unittest.main()
