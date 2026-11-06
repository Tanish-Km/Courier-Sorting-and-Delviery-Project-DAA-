"""
Unit tests for TSP Nearest-Neighbor heuristic, 2-Opt local search, and route expansion.
"""

import unittest
from src.routing import (
    tsp_nearest_neighbor,
    two_opt_optimize,
    calculate_tour_length,
    build_full_delivery_route,
)


class TestRouting(unittest.TestCase):

    def setUp(self):
        # Distance matrix for a 4-node square: Depot (0,0), A (0,10), B (10,10), C (10,0)
        # Distances:
        # Depot-A: 10, A-B: 10, B-C: 10, C-Depot: 10
        # Diagonals: Depot-B: 14.14, A-C: 14.14
        self.dist_matrix = {
            ("Depot", "Depot"): 0.0,
            ("Depot", "A"): 10.0, ("A", "Depot"): 10.0,
            ("Depot", "B"): 14.14, ("B", "Depot"): 14.14,
            ("Depot", "C"): 10.0, ("C", "Depot"): 10.0,
            ("A", "A"): 0.0,
            ("A", "B"): 10.0, ("B", "A"): 10.0,
            ("A", "C"): 14.14, ("C", "A"): 14.14,
            ("B", "B"): 0.0,
            ("B", "C"): 10.0, ("C", "B"): 10.0,
            ("C", "C"): 0.0,
        }
        self.path_matrix = {
            (u, v): [u, v] for u in ["Depot", "A", "B", "C"] for v in ["Depot", "A", "B", "C"]
        }

    def test_tsp_nearest_neighbor_tour_structure(self):
        stops = ["A", "B", "C"]
        tour = tsp_nearest_neighbor("Depot", stops, self.dist_matrix)

        # Starts and ends at Depot
        self.assertEqual(tour[0], "Depot")
        self.assertEqual(tour[-1], "Depot")
        # Visits all 3 stops
        self.assertEqual(set(tour[1:-1]), {"A", "B", "C"})
        self.assertEqual(len(tour), 5)

    def test_calculate_tour_length(self):
        # Perimeter tour: Depot -> A -> B -> C -> Depot = 10 + 10 + 10 + 10 = 40.0
        perimeter_tour = ["Depot", "A", "B", "C", "Depot"]
        length = calculate_tour_length(perimeter_tour, self.dist_matrix)
        self.assertAlmostEqual(length, 40.0, places=1)

        # Crossing tour: Depot -> B -> A -> C -> Depot = 14.14 + 10 + 14.14 + 10 = 48.28
        crossing_tour = ["Depot", "B", "A", "C", "Depot"]
        length_crossing = calculate_tour_length(crossing_tour, self.dist_matrix)
        self.assertGreater(length_crossing, length)

    def test_two_opt_removes_crossing(self):
        crossing_tour = ["Depot", "B", "A", "C", "Depot"]
        optimized = two_opt_optimize(crossing_tour, self.dist_matrix)
        opt_len = calculate_tour_length(optimized, self.dist_matrix)
        orig_len = calculate_tour_length(crossing_tour, self.dist_matrix)
        self.assertLess(opt_len, orig_len)

    def test_empty_destinations(self):
        tour = tsp_nearest_neighbor("Depot", [], self.dist_matrix)
        self.assertEqual(tour, ["Depot", "Depot"])

    def test_build_full_delivery_route(self):
        tour = ["Depot", "A", "B", "Depot"]
        route = build_full_delivery_route(tour, self.dist_matrix, self.path_matrix)
        self.assertEqual(route.ordered_stops, tour)
        self.assertEqual(route.detailed_path, ["Depot", "A", "B", "Depot"])
        self.assertAlmostEqual(route.total_distance, 34.14, places=1)

    def test_build_full_delivery_route_depot_only(self):
        tour = ["Depot", "Depot"]
        route = build_full_delivery_route(tour, self.dist_matrix, self.path_matrix)
        self.assertEqual(route.ordered_stops, ["Depot", "Depot"])
        self.assertEqual(route.detailed_path, ["Depot", "Depot"])
        self.assertEqual(route.total_distance, 0.0)


if __name__ == "__main__":
    unittest.main()
