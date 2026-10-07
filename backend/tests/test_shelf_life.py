import unittest
from decimal import Decimal

from pydantic import ValidationError

from backend.api.routes.shelf_life import estimate_shelf_life_route
from backend.engine.shelf_life import estimate_shelf_life
from backend.schemas.shelf_life import ShelfLifeEstimateRequest


class ShelfLifeTests(unittest.TestCase):
    def estimate(self, **overrides):
        values = {
            "quantity_kg": Decimal("1000"),
            "remaining_shelf_life_days": Decimal("5"),
            "transit_time_days": Decimal("2"),
            "baseline_spoilage_rate_per_day": Decimal("0.03"),
        }
        values.update(overrides)
        return estimate_shelf_life(**values)

    def test_normal_viable_case(self):
        result = self.estimate()
        self.assertEqual(result["shelf_life_status"], "viable")
        self.assertEqual(result["remaining_shelf_life_after_transit_days"], Decimal("3"))
        self.assertEqual(result["estimated_spoilage_fraction"], Decimal("0.06"))
        self.assertEqual(result["estimated_spoilage_kg"], Decimal("60.00"))
        self.assertEqual(result["estimated_remaining_quantity_kg"], Decimal("940.00"))

    def test_near_expiry_case(self):
        self.assertEqual(
            self.estimate(remaining_shelf_life_days=Decimal("3"), transit_time_days=Decimal("2"))["shelf_life_status"],
            "near_expiry",
        )

    def test_expired_case(self):
        result = self.estimate(remaining_shelf_life_days=Decimal("1"), transit_time_days=Decimal("2"))
        self.assertEqual(result["shelf_life_status"], "expired")
        self.assertEqual(result["remaining_shelf_life_after_transit_days"], Decimal("-1"))

    def test_zero_transit_and_zero_rate(self):
        result = self.estimate(transit_time_days=Decimal("0"), baseline_spoilage_rate_per_day=Decimal("0"))
        self.assertEqual(result["estimated_spoilage_fraction"], Decimal("0"))
        self.assertEqual(result["estimated_spoilage_kg"], Decimal("0"))
        self.assertEqual(result["estimated_remaining_quantity_kg"], Decimal("1000"))

    def test_maximum_spoilage_rate_is_capped(self):
        result = self.estimate(
            transit_time_days=Decimal("2"), baseline_spoilage_rate_per_day=Decimal("1")
        )
        self.assertEqual(result["estimated_spoilage_fraction"], Decimal("1"))
        self.assertEqual(result["estimated_remaining_quantity_kg"], Decimal("0"))

    def test_fractional_quantity_and_transit(self):
        result = self.estimate(
            quantity_kg=Decimal("12.5"),
            remaining_shelf_life_days=Decimal("2.5"),
            transit_time_days=Decimal("0.5"),
            baseline_spoilage_rate_per_day=Decimal("0.2"),
        )
        self.assertEqual(result["estimated_spoilage_fraction"], Decimal("0.10"))
        self.assertEqual(result["estimated_spoilage_kg"], Decimal("1.250"))
        self.assertEqual(result["estimated_remaining_quantity_kg"], Decimal("11.250"))

    def test_invalid_inputs_are_rejected(self):
        valid = {
            "quantity_kg": Decimal("1"),
            "remaining_shelf_life_days": Decimal("1"),
            "transit_time_days": Decimal("1"),
            "baseline_spoilage_rate_per_day": Decimal("0.1"),
        }
        for field, value in (
            ("quantity_kg", Decimal("-1")),
            ("remaining_shelf_life_days", Decimal("-1")),
            ("transit_time_days", Decimal("-1")),
            ("baseline_spoilage_rate_per_day", Decimal("-0.1")),
            ("baseline_spoilage_rate_per_day", Decimal("1.1")),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValidationError):
                    ShelfLifeEstimateRequest(**{**valid, field: value})

    def test_response_structure_and_assumption_note(self):
        result = estimate_shelf_life_route(ShelfLifeEstimateRequest(
            quantity_kg=1000,
            remaining_shelf_life_days=5,
            transit_time_days=2,
            baseline_spoilage_rate_per_day="0.03",
        ))
        self.assertEqual(set(result), {
            "quantity_kg", "remaining_shelf_life_days", "transit_time_days",
            "remaining_shelf_life_after_transit_days", "baseline_spoilage_rate_per_day",
            "estimated_spoilage_fraction", "estimated_spoilage_kg",
            "estimated_remaining_quantity_kg", "shelf_life_status", "assumption_note",
        })
        self.assertIn("assumption-based", result["assumption_note"])


if __name__ == "__main__":
    unittest.main()
