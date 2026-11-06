"""
End-to-end integration tests for MiniCourierPlanner.
"""

import unittest
from src.models import Parcel
from src.graph import Graph
from src.planner import MiniCourierPlanner


class TestPlanner(unittest.TestCase):

    def setUp(self):
        self.graph = Graph(directed=False)
        self.graph.add_node("Depot", is_depot=True, x=0, y=0)
        self.graph.add_node("C1", x=10, y=0)
        self.graph.add_node("C2", x=10, y=10)
        self.graph.add_node("C3", x=0, y=10)

        self.graph.add_edge("Depot", "C1", 10.0)
        self.graph.add_edge("C1", "C2", 10.0)
        self.graph.add_edge("C2", "C3", 10.0)
        self.graph.add_edge("C3", "Depot", 10.0)

        self.parcels = [
            Parcel("P1", "C1", weight=5, priority=5, deadline=1.0, value=100),
            Parcel("P2", "C2", weight=10, priority=4, deadline=2.0, value=80),
            Parcel("P3", "C3", weight=15, priority=3, deadline=3.0, value=60),
            Parcel("P4", "C1", weight=20, priority=1, deadline=10.0, value=20),
        ]

    def test_end_to_end_planner_execution(self):
        planner = MiniCourierPlanner()
        # Capacity 20 -> optimal picks P1 (5, 100) + P2 (10, 80) = weight 15, value 180
        result = planner.plan(self.parcels, self.graph, vehicle_capacity=20)

        self.assertEqual(result.initial_parcel_count, 4)
        self.assertEqual(result.packing_result.total_weight, 15)
        self.assertEqual(result.packing_result.total_value, 180)
        self.assertEqual(len(result.packing_result.selected_parcels), 2)

        # Route should visit Depot, C1, C2, and back to Depot
        stops = result.route_result.ordered_stops
        self.assertEqual(stops[0], "Depot")
        self.assertEqual(stops[-1], "Depot")
        self.assertEqual(set(stops[1:-1]), {"C1", "C2"})

        # Check runtime breakdown contains all expected phases
        self.assertIn("sorting_ms", result.runtime_breakdown_ms)
        self.assertIn("knapsack_dp_ms", result.runtime_breakdown_ms)
        self.assertIn("dijkstra_ms", result.runtime_breakdown_ms)
        self.assertIn("tsp_routing_ms", result.runtime_breakdown_ms)

    def test_missing_depot_raises(self):
        planner = MiniCourierPlanner()
        with self.assertRaises(ValueError):
            planner.plan(self.parcels, self.graph, vehicle_capacity=20, depot_node="NonExistentDepot")

    def test_unreachable_destination_raises(self):
        planner = MiniCourierPlanner()
        self.graph.add_node("Isolated")
        unreachable_parcels = [Parcel("P_iso", "Isolated", weight=5, priority=5, value=100)]
        with self.assertRaises(ValueError) as ctx:
            planner.plan(unreachable_parcels, self.graph, vehicle_capacity=20)
        self.assertIn("unreachable", str(ctx.exception).lower())

    def test_nonexistent_destination_raises(self):
        planner = MiniCourierPlanner()
        bad_parcels = [Parcel("P_bad", "GhostCity", weight=5, priority=5, value=100)]
        with self.assertRaises(ValueError) as ctx:
            planner.plan(bad_parcels, self.graph, vehicle_capacity=20)
        self.assertIn("does not exist", str(ctx.exception).lower())

    def test_negative_capacity_raises(self):
        planner = MiniCourierPlanner()
        with self.assertRaises(ValueError):
            planner.plan(self.parcels, self.graph, vehicle_capacity=-10)

    def test_empty_parcels_plan(self):
        planner = MiniCourierPlanner()
        result = planner.plan([], self.graph, vehicle_capacity=20)
        self.assertEqual(result.initial_parcel_count, 0)
        self.assertEqual(len(result.packing_result.selected_parcels), 0)
        self.assertEqual(result.route_result.ordered_stops, ["Depot", "Depot"])
        self.assertEqual(result.route_result.detailed_path, ["Depot", "Depot"])
        self.assertEqual(result.route_result.total_distance, 0.0)

    def test_zero_capacity_plan(self):
        planner = MiniCourierPlanner()
        result = planner.plan(self.parcels, self.graph, vehicle_capacity=0)
        self.assertEqual(len(result.packing_result.selected_parcels), 0)
        self.assertEqual(result.route_result.ordered_stops, ["Depot", "Depot"])
        self.assertEqual(result.route_result.total_distance, 0.0)


if __name__ == "__main__":
    unittest.main()
