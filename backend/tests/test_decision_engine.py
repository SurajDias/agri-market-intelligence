import unittest
from decimal import Decimal

from pydantic import ValidationError

from backend.api.routes.decision import calculate_decision_value
from backend.engine.decision_engine import calculate_expected_net_value
from backend.schemas.decision import DecisionValueRequest


class DecisionEngineTests(unittest.TestCase):
    def calculate(self, **overrides):
        values = {
            "quantity_kg": Decimal("1000"),
            "expected_selling_price_per_kg": Decimal("25"),
            "transport_cost": Decimal("1200"),
            "estimated_spoilage_kg": Decimal("50"),
            "shelf_life_status": "viable",
        }
        values.update(overrides)
        return calculate_expected_net_value(**values)

    def test_normal_positive_net_value_case(self):
        result = self.calculate()
        self.assertEqual(result["saleable_quantity_kg"], Decimal("950"))
        self.assertEqual(result["gross_revenue"], Decimal("23750.00"))
        self.assertEqual(result["estimated_spoilage_loss_inr"], Decimal("1250.00"))
        self.assertEqual(result["expected_net_value"], Decimal("22550.00"))

    def test_negative_net_value_is_preserved(self):
        result = self.calculate(transport_cost=Decimal("25000"))
        self.assertEqual(result["expected_net_value"], Decimal("-1250.00"))

    def test_zero_transport_and_zero_spoilage(self):
        result = self.calculate(transport_cost=Decimal("0"), estimated_spoilage_kg=Decimal("0"))
        self.assertEqual(result["saleable_quantity_kg"], Decimal("1000"))
        self.assertEqual(result["estimated_spoilage_loss_inr"], Decimal("0.00"))
        self.assertEqual(result["expected_net_value"], Decimal("25000.00"))

    def test_full_spoilage(self):
        result = self.calculate(estimated_spoilage_kg=Decimal("1000"))
        self.assertEqual(result["saleable_quantity_kg"], Decimal("0"))
        self.assertEqual(result["gross_revenue"], Decimal("0.00"))
        self.assertEqual(result["expected_net_value"], Decimal("-1200.00"))
        self.assertEqual(result["spoilage_percentage"], Decimal("100"))

    def test_zero_expected_price(self):
        result = self.calculate(expected_selling_price_per_kg=Decimal("0"))
        self.assertEqual(result["gross_revenue"], Decimal("0.00"))
        self.assertEqual(result["estimated_spoilage_loss_inr"], Decimal("0.00"))
        self.assertEqual(result["expected_net_value"], Decimal("-1200.00"))

    def test_decimal_calculation_and_per_original_kg(self):
        result = self.calculate(
            quantity_kg=Decimal("12.5"),
            expected_selling_price_per_kg=Decimal("10.25"),
            transport_cost=Decimal("3.10"),
            estimated_spoilage_kg=Decimal("1.25"),
        )
        self.assertEqual(result["saleable_quantity_kg"], Decimal("11.25"))
        self.assertEqual(result["gross_revenue"], Decimal("115.31"))
        self.assertEqual(result["estimated_spoilage_loss_inr"], Decimal("12.81"))
        self.assertEqual(result["expected_net_value"], Decimal("112.21"))
        self.assertEqual(result["net_value_per_original_kg"], Decimal("8.98"))
        self.assertEqual(result["spoilage_percentage"], Decimal("10.00"))

    def test_invalid_inputs_are_rejected(self):
        valid = {
            "quantity_kg": Decimal("1"),
            "expected_selling_price_per_kg": Decimal("1"),
            "transport_cost": Decimal("1"),
            "estimated_spoilage_kg": Decimal("0"),
        }
        for field, value in (
            ("quantity_kg", Decimal("-1")),
            ("expected_selling_price_per_kg", Decimal("-1")),
            ("transport_cost", Decimal("-1")),
            ("estimated_spoilage_kg", Decimal("-1")),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    DecisionValueRequest(**{**valid, field: value})

        with self.assertRaises(ValidationError):
            DecisionValueRequest(**{**valid, "estimated_spoilage_kg": Decimal("2")})

    def test_response_structure_and_explanation(self):
        result = calculate_decision_value(DecisionValueRequest(
            quantity_kg=1000,
            expected_selling_price_per_kg=25,
            transport_cost=1200,
            estimated_spoilage_kg=50,
            shelf_life_status="near_expiry",
        ))
        self.assertEqual(result["shelf_life_status"], "near_expiry")
        self.assertEqual(result["explanation"]["original_quantity_kg"], Decimal("1000"))
        self.assertEqual(result["explanation"]["spoilage_quantity_kg"], Decimal("50"))
        self.assertIn("Expected Price × Saleable Quantity", result["explanation"]["formula"])


if __name__ == "__main__":
    unittest.main()
