"""
Unit tests for 0/1 Knapsack Dynamic Programming solver.
"""

import unittest
from src.models import Parcel
from src.knapsack import knapsack_01_dp, knapsack_01_space_optimized, format_dp_table_text


class TestKnapsack(unittest.TestCase):

    def test_knapsack_standard_optimal(self):
        # Classic textbook 0/1 knapsack instance:
        # Items: (weight, value) = (2, 3), (3, 4), (4, 5), (5, 8)
        # Capacity = 5 -> Best: (2, 3) + (3, 4) = weight 5, value 7; or (5, 8) = weight 5, value 8 -> Optimal: value 8
        parcels = [
            Parcel("P1", "C1", weight=2, value=3),
            Parcel("P2", "C2", weight=3, value=4),
            Parcel("P3", "C3", weight=4, value=5),
            Parcel("P4", "C4", weight=5, value=8),
        ]
        result = knapsack_01_dp(parcels, capacity=5)
        self.assertEqual(result.total_value, 8)
        self.assertEqual(result.total_weight, 5)
        self.assertEqual(len(result.selected_parcels), 1)
        self.assertEqual(result.selected_parcels[0].parcel_id, "P4")

    def test_knapsack_multiple_items_selected(self):
        parcels = [
            Parcel("P1", "C1", weight=10, value=60),
            Parcel("P2", "C2", weight=20, value=100),
            Parcel("P3", "C3", weight=30, value=120),
        ]
        # Capacity 50 -> Can take P2 (20, 100) + P3 (30, 120) = weight 50, value 220
        result = knapsack_01_dp(parcels, capacity=50)
        self.assertEqual(result.total_value, 220)
        self.assertEqual(result.total_weight, 50)
        selected_ids = {p.parcel_id for p in result.selected_parcels}
        self.assertEqual(selected_ids, {"P2", "P3"})

    def test_knapsack_zero_capacity(self):
        parcels = [
            Parcel("P1", "C1", weight=5, value=10),
            Parcel("P2", "C2", weight=10, value=20),
        ]
        result = knapsack_01_dp(parcels, capacity=0)
        self.assertEqual(result.total_value, 0)
        self.assertEqual(result.total_weight, 0)
        self.assertEqual(len(result.selected_parcels), 0)
        self.assertEqual(len(result.rejected_parcels), 2)

    def test_knapsack_all_fit(self):
        parcels = [
            Parcel("P1", "C1", weight=2, value=10),
            Parcel("P2", "C2", weight=3, value=15),
        ]
        result = knapsack_01_dp(parcels, capacity=10)
        self.assertEqual(result.total_value, 25)
        self.assertEqual(result.total_weight, 5)
        self.assertEqual(len(result.selected_parcels), 2)
        self.assertEqual(len(result.rejected_parcels), 0)

    def test_knapsack_space_optimized_equivalence(self):
        parcels = [
            Parcel("P1", "C1", weight=3, value=12),
            Parcel("P2", "C2", weight=4, value=15),
            Parcel("P3", "C3", weight=6, value=25),
            Parcel("P4", "C4", weight=5, value=20),
        ]
        res_dp = knapsack_01_dp(parcels, capacity=10)
        val_opt, selected_opt = knapsack_01_space_optimized(parcels, capacity=10)

        self.assertEqual(res_dp.total_value, val_opt)
        self.assertEqual(sum(p.value for p in selected_opt), res_dp.total_value)

    def test_knapsack_negative_capacity_raises(self):
        parcels = [Parcel("P1", "C1", weight=2, value=10)]
        with self.assertRaises(ValueError):
            knapsack_01_dp(parcels, capacity=-5)
        with self.assertRaises(ValueError):
            knapsack_01_space_optimized(parcels, capacity=-5)

    def test_parcel_negative_weight_raises(self):
        with self.assertRaises(ValueError):
            Parcel("P1", "C1", weight=-2, value=10)

    def test_parcel_invalid_priority_raises(self):
        with self.assertRaises(ValueError):
            Parcel("P1", "C1", weight=2, priority=0)
        with self.assertRaises(ValueError):
            Parcel("P1", "C1", weight=2, priority=6)

    def test_parcel_invalid_deadline_raises(self):
        with self.assertRaises(ValueError):
            Parcel("P1", "C1", weight=2, deadline=0.0)

    def test_format_dp_table_text(self):
        parcels = [Parcel("P1", "C1", weight=2, value=10)]
        res = knapsack_01_dp(parcels, capacity=3)
        formatted = format_dp_table_text(res.dp_table, parcels, capacity=3)
        self.assertIn("P1", formatted)
        self.assertIn("None", formatted)


if __name__ == "__main__":
    unittest.main()
