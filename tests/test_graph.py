"""
Unit tests for Graph modeling and Dijkstra's Shortest Path algorithm.
"""

import unittest
from src.graph import Graph, dijkstra, reconstruct_path, compute_distance_matrix


class TestGraph(unittest.TestCase):

    def setUp(self):
        # Setup a sample graph:
        # Depot --(5)-- A --(3)-- B
        #   |            |        |
        #  (10)         (2)      (4)
        #   |            |        |
        #   v            v        v
        #   C   --(1)--> D --(2)-> E
        self.g = Graph(directed=False)
        self.g.add_node("Depot", is_depot=True)
        self.g.add_node("A")
        self.g.add_node("B")
        self.g.add_node("C")
        self.g.add_node("D")
        self.g.add_node("E")

        self.g.add_edge("Depot", "A", 5.0)
        self.g.add_edge("A", "B", 3.0)
        self.g.add_edge("Depot", "C", 10.0)
        self.g.add_edge("A", "D", 2.0)
        self.g.add_edge("B", "E", 4.0)
        self.g.add_edge("C", "D", 1.0)
        self.g.add_edge("D", "E", 2.0)

    def test_dijkstra_shortest_paths(self):
        distances, predecessors = dijkstra(self.g, "Depot")

        self.assertEqual(distances["Depot"], 0.0)
        self.assertEqual(distances["A"], 5.0)
        self.assertEqual(distances["B"], 8.0)
        # Depot -> A (5) -> D (2) -> C (1) = 8.0 < direct 10.0
        self.assertEqual(distances["D"], 7.0)
        self.assertEqual(distances["C"], 8.0)
        # Depot -> A (5) -> D (2) -> E (2) = 9.0
        self.assertEqual(distances["E"], 9.0)

    def test_reconstruct_path(self):
        _, predecessors = dijkstra(self.g, "Depot")
        path_to_e = reconstruct_path(predecessors, "E")
        self.assertEqual(path_to_e, ["Depot", "A", "D", "E"])

        path_to_c = reconstruct_path(predecessors, "C")
        self.assertEqual(path_to_c, ["Depot", "A", "D", "C"])

    def test_compute_distance_matrix(self):
        targets = ["Depot", "B", "E"]
        dist_mat, path_mat = compute_distance_matrix(self.g, targets)

        self.assertEqual(dist_mat[("Depot", "B")], 8.0)
        self.assertEqual(dist_mat[("Depot", "E")], 9.0)
        self.assertEqual(dist_mat[("B", "E")], 4.0)
        self.assertEqual(path_mat[("Depot", "E")], ["Depot", "A", "D", "E"])

    def test_dijkstra_disconnected_node(self):
        self.g.add_node("Isolated")
        distances, predecessors = dijkstra(self.g, "Depot")
        self.assertEqual(distances["Isolated"], float("inf"))
        # Unreachable node must return an empty path, NOT a phantom ['Isolated']
        self.assertEqual(reconstruct_path(predecessors, "Isolated"), [])
        self.assertEqual(reconstruct_path(predecessors, "Isolated", source="Depot"), [])

    def test_negative_edge_weight_raises(self):
        g = Graph()
        with self.assertRaises(ValueError):
            g.add_edge("A", "B", -1.0)

    def test_dijkstra_nonexistent_source_raises(self):
        with self.assertRaises(ValueError):
            dijkstra(self.g, "NonExistent")

    def test_reconstruct_path_same_node(self):
        _, predecessors = dijkstra(self.g, "Depot")
        self.assertEqual(reconstruct_path(predecessors, "Depot", source="Depot"), ["Depot"])

    def test_graph_serialization(self):
        d = self.g.to_dict()
        g2 = Graph.from_dict(d)
        self.assertEqual(set(self.g.get_nodes()), set(g2.get_nodes()))
        self.assertEqual(len(self.g.get_edges()), len(g2.get_edges()))


if __name__ == "__main__":
    unittest.main()
