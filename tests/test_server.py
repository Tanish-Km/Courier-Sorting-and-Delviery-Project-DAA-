"""
Comprehensive integration tests for the Mini-Courier Planner Web Server & REST API.
Verifies all REST API endpoints, static file serving, and edge case handling.
"""

import unittest
import threading
import time
import json
import urllib.request
import urllib.error
import socket
from typing import Dict, Any

from src.server import create_server, ensure_datasets
from src.models import Parcel
from src.graph import Graph


def find_free_port() -> int:
    """Finds an unused TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_datasets()
        cls.port = find_free_port()
        cls.host = "127.0.0.1"
        cls.base_url = f"http://{cls.host}:{cls.port}"

        cls.server = create_server(host=cls.host, port=cls.port)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

        # Wait briefly for server startup
        time.sleep(0.15)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2.0)

    def _get(self, path: str) -> tuple[int, Any, dict]:
        """Performs a GET request and returns (status_code, parsed_body_or_text, headers)."""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                code = resp.getcode()
                content_type = resp.headers.get("Content-Type", "")
                data = resp.read()
                if "application/json" in content_type:
                    return code, json.loads(data.decode("utf-8")), dict(resp.headers)
                return code, data.decode("utf-8", errors="replace"), dict(resp.headers)
        except urllib.error.HTTPError as e:
            try:
                content_type = e.headers.get("Content-Type", "")
                data = e.read()
                if "application/json" in content_type:
                    return e.code, json.loads(data.decode("utf-8")), dict(e.headers)
                return e.code, data.decode("utf-8", errors="replace"), dict(e.headers)
            finally:
                e.close()

    def _post(self, path: str, payload: Dict[str, Any]) -> tuple[int, Any, dict]:
        """Performs a POST request with JSON payload."""
        url = f"{self.base_url}{path}"
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                code = resp.getcode()
                content_type = resp.headers.get("Content-Type", "")
                data = resp.read()
                if "application/json" in content_type:
                    return code, json.loads(data.decode("utf-8")), dict(resp.headers)
                return code, data.decode("utf-8", errors="replace"), dict(resp.headers)
        except urllib.error.HTTPError as e:
            try:
                content_type = e.headers.get("Content-Type", "")
                data = e.read()
                if "application/json" in content_type:
                    return e.code, json.loads(data.decode("utf-8")), dict(e.headers)
                return e.code, data.decode("utf-8", errors="replace"), dict(e.headers)
            finally:
                e.close()

    # -------------------------------------------------------------------------
    # REST API Verification
    # -------------------------------------------------------------------------
    def test_health_check(self):
        code, body, _ = self._get("/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("service"), "Mini-Courier Planner")
        self.assertIn("version", body)

    def test_get_datasets_catalog(self):
        code, body, _ = self._get("/api/datasets")
        self.assertEqual(code, 200)
        datasets = body.get("datasets", [])
        self.assertGreaterEqual(len(datasets), 3)
        ids = [d["id"] for d in datasets]
        self.assertIn("small", ids)
        self.assertIn("medium", ids)
        self.assertIn("large", ids)

    def test_get_single_dataset(self):
        code, body, _ = self._get("/api/datasets/small")
        self.assertEqual(code, 200)
        self.assertEqual(body.get("id"), "small")
        self.assertIn("graph", body)
        self.assertIn("parcels", body)
        self.assertGreaterEqual(len(body["parcels"]), 5)
        self.assertEqual(body.get("recommended_capacity"), 40)

    def test_get_invalid_dataset_returns_404(self):
        code, body, _ = self._get("/api/datasets/non_existent_dataset_123")
        self.assertEqual(code, 404)
        self.assertEqual(body.get("status"), "error")

    def test_post_plan_standard(self):
        # Fetch small dataset
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": data["parcels"],
            "vehicle_capacity": 40,
            "sort_strategy": "deadline_priority",
            "sort_algorithm": "mergesort",
            "use_two_opt": True,
            "depot_node": "Depot",
            "speed_kmh": 40.0,
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)

        # Packing assertions
        pack = res["packing_result"]
        self.assertLessEqual(pack["total_weight"], 40)
        self.assertGreater(pack["total_value"], 0)
        self.assertGreater(len(pack["selected_parcels"]), 0)
        self.assertIn("dp_table", pack)
        self.assertIn("backtrack_path", pack)
        self.assertGreater(len(pack["backtrack_path"]), 0)

        # Route assertions
        route = res["route_result"]
        stops = route["ordered_stops"]
        self.assertEqual(stops[0], "Depot")
        self.assertEqual(stops[-1], "Depot")
        self.assertGreater(route["total_distance"], 0.0)
        self.assertGreater(len(route["detailed_path"]), 0)
        self.assertIn("itinerary", route)
        self.assertGreater(len(route["itinerary"]), 0)

        # Benchmark comparisons
        bench = res["benchmarks"]
        self.assertIn("knapsack", bench)
        self.assertIn("tsp", bench)
        self.assertGreaterEqual(bench["knapsack"]["dp_value"], bench["knapsack"]["greedy_value"])

    def test_post_plan_zero_capacity_edge_case(self):
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": data["parcels"],
            "vehicle_capacity": 0,
            "depot_node": "Depot",
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)
        pack = res["packing_result"]
        self.assertEqual(pack["total_weight"], 0)
        self.assertEqual(pack["total_value"], 0)
        self.assertEqual(len(pack["selected_parcels"]), 0)
        self.assertEqual(len(pack["rejected_parcels"]), len(data["parcels"]))
        self.assertEqual(res["route_result"]["ordered_stops"], ["Depot", "Depot"])

    def test_post_plan_enormous_capacity_edge_case(self):
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": data["parcels"],
            "vehicle_capacity": 500,
            "depot_node": "Depot",
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)
        pack = res["packing_result"]
        # All parcels should be selected
        self.assertEqual(len(pack["selected_parcels"]), len(data["parcels"]))
        self.assertEqual(len(pack["rejected_parcels"]), 0)

    def test_post_plan_empty_parcels_edge_case(self):
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": [],
            "vehicle_capacity": 40,
            "depot_node": "Depot",
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)
        self.assertEqual(res["initial_parcel_count"], 0)
        self.assertEqual(res["packing_result"]["total_weight"], 0)
        self.assertEqual(res["route_result"]["ordered_stops"], ["Depot", "Depot"])

    def test_post_plan_unreachable_node_returns_400(self):
        # Graph with disconnected node
        g = Graph(directed=False)
        g.add_node("Depot", is_depot=True, x=0, y=0)
        g.add_node("C1", x=10, y=0)
        g.add_node("Island", x=100, y=100) # no edge to Island
        g.add_edge("Depot", "C1", 10.0)

        payload = {
            "graph": g.to_dict(),
            "parcels": [
                {"parcel_id": "P1", "destination": "Island", "weight": 5, "priority": 3, "deadline": 4.0, "value": 50}
            ],
            "vehicle_capacity": 20,
            "depot_node": "Depot"
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 400)
        self.assertIn("unreachable", res.get("error", "").lower())

    def test_post_plan_sorting_strategies_and_algorithms(self):
        _, data, _ = self._get("/api/datasets/small")
        strategies = ["deadline_priority", "priority_only", "value_density"]
        algorithms = ["mergesort", "quicksort", "timsort"]

        for strat in strategies:
            for algo in algorithms:
                payload = {
                    "graph": data["graph"],
                    "parcels": data["parcels"],
                    "vehicle_capacity": 30,
                    "sort_strategy": strat,
                    "sort_algorithm": algo,
                }
                code, res, _ = self._post("/api/plan", payload)
                self.assertEqual(code, 200, f"Failed for strat={strat}, algo={algo}")
                self.assertIn("packing_result", res)

    def test_post_plan_large_capacity_returns_full_table(self):
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": data["parcels"],
            "vehicle_capacity": 150,
            "depot_node": "Depot",
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)
        pack = res["packing_result"]
        # dp_table should have 151 columns (0 to 150)
        self.assertEqual(len(pack["dp_table"][0]), 151)
        self.assertGreater(len(pack["backtrack_path"]), 0)
        # Verify optimal cell matches
        optimal_val = pack["dp_table"][-1][150]
        self.assertEqual(pack["total_value"], optimal_val)

    def test_post_plan_custom_graph_and_parcels(self):
        custom_graph = {
            "directed": False,
            "nodes": [
                {"node_id": "Depot", "name": "Hub", "x": 0.0, "y": 0.0, "is_depot": True},
                {"node_id": "StoreA", "name": "Store Alpha", "x": 10.0, "y": 0.0, "is_depot": False},
                {"node_id": "StoreB", "name": "Store Beta", "x": 10.0, "y": 10.0, "is_depot": False},
            ],
            "edges": [
                {"source": "Depot", "target": "StoreA", "weight": 10.0},
                {"source": "StoreA", "target": "StoreB", "weight": 10.0},
                {"source": "StoreB", "target": "Depot", "weight": 14.14},
            ]
        }
        custom_parcels = [
            {"parcel_id": "CUSTOM1", "destination": "StoreA", "weight": 5, "priority": 5, "deadline": 2.0, "value": 100},
            {"parcel_id": "CUSTOM2", "destination": "StoreB", "weight": 10, "priority": 3, "deadline": 4.0, "value": 60},
        ]
        payload = {
            "graph": custom_graph,
            "parcels": custom_parcels,
            "vehicle_capacity": 12,
            "depot_node": "Depot"
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)
        pack = res["packing_result"]
        self.assertEqual(pack["total_weight"], 5) # Selected CUSTOM1 (weight 5, val 100)
        self.assertEqual(pack["total_value"], 100)
        self.assertEqual(len(pack["selected_parcels"]), 1)
        self.assertEqual(pack["selected_parcels"][0]["parcel_id"], "CUSTOM1")

        route = res["route_result"]
        self.assertIn("StoreA", route["ordered_stops"])
        self.assertEqual(route["ordered_stops"][0], "Depot")
        self.assertEqual(route["ordered_stops"][-1], "Depot")

    def test_post_plan_negative_capacity_returns_400(self):
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": data["parcels"],
            "vehicle_capacity": -5,
            "depot_node": "Depot",
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 400)
        self.assertIn("negative", res.get("error", "").lower())

    def test_post_plan_itinerary_structure(self):
        _, data, _ = self._get("/api/datasets/small")
        payload = {
            "graph": data["graph"],
            "parcels": data["parcels"],
            "vehicle_capacity": 40,
            "depot_node": "Depot",
            "speed_kmh": 60.0
        }
        code, res, _ = self._post("/api/plan", payload)
        self.assertEqual(code, 200)
        itinerary = res["route_result"]["itinerary"]
        self.assertIsInstance(itinerary, list)
        self.assertGreater(len(itinerary), 0)
        # Check first stop is Depot at 0 km
        first = itinerary[0]
        self.assertEqual(first["node_id"], "Depot")
        self.assertEqual(first["cumulative_distance_km"], 0.0)
        self.assertEqual(first["eta_minutes"], 0.0)
        self.assertTrue(first["is_depot"])
        # Check fields in each stop
        for stop in itinerary:
            self.assertIn("node_id", stop)
            self.assertIn("leg_distance_km", stop)
            self.assertIn("cumulative_distance_km", stop)
            self.assertIn("eta_minutes", stop)
            self.assertIn("parcels_dropped", stop)

    def test_post_benchmark(self):
        code, body, _ = self._post("/api/benchmark", {})
        self.assertEqual(code, 200)
        self.assertIn("sorting", body)
        s = body["sorting"]
        self.assertIn("mergesort_time_ms", s)
        self.assertIn("quicksort_time_ms", s)
        self.assertIn("timsort_time_ms", s)

    # -------------------------------------------------------------------------
    # Static Assets Verification
    # -------------------------------------------------------------------------
    def test_serve_index_html(self):
        code, text, headers = self._get("/")
        self.assertEqual(code, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn("Mini-Courier Planner", text)
        self.assertIn("id=\"app\"", text)

    def test_serve_styles_css(self):
        code, text, headers = self._get("/styles.css")
        self.assertEqual(code, 200)
        self.assertIn("text/css", headers.get("Content-Type", ""))
        self.assertIn("--bg-primary", text)

    def test_serve_app_js(self):
        code, text, headers = self._get("/app.js")
        self.assertEqual(code, 200)
        self.assertTrue("javascript" in headers.get("Content-Type", "") or "text/plain" in headers.get("Content-Type", ""))
        self.assertIn("runOptimization", text)

    def test_serve_nonexistent_file(self):
        code, text, _ = self._get("/non_existent_file.xyz")
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
