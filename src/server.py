"""
Web API Server and Static Asset Handler for Mini-Courier Planner.
Uses Python's standard library http.server for a zero-external-dependency,
instant-startup REST backend and responsive web frontend server.
"""

import os
import sys
import json
import time
import mimetypes
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Any, Optional

from src.models import Parcel, DeliveryPoint, RoadEdge, CourierPlanResult
from src.graph import Graph, compute_distance_matrix, dijkstra
from src.knapsack import knapsack_01_dp
from src.sorting import prioritize_parcels, compare_sorting_algorithms
from src.routing import tsp_nearest_neighbor, two_opt_optimize, build_full_delivery_route, calculate_tour_length
from src.planner import MiniCourierPlanner
from src.main import load_parcels_csv, generate_default_datasets

# Determine root directories
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(PROJECT_DIR, "web")
DATASETS_DIR = os.path.join(PROJECT_DIR, "datasets")


def greedy_knapsack(parcels: List[Parcel], capacity: int) -> Dict[str, Any]:
    """
    Greedy heuristic Knapsack solver (by value-to-weight ratio).
    Used for algorithmic benchmark comparison against optimal 0/1 DP.
    """
    sorted_p = sorted(
        parcels,
        key=lambda p: (p.value / max(1, p.weight), p.priority),
        reverse=True
    )
    selected = []
    current_w = 0
    total_val = 0
    for p in sorted_p:
        if current_w + p.weight <= capacity:
            selected.append(p)
            current_w += p.weight
            total_val += p.value

    return {
        "selected_parcels": [p.to_dict() for p in selected],
        "total_weight": current_w,
        "total_value": total_val,
        "count": len(selected),
    }


def extract_dp_backtracking_path(
    dp: List[List[int]],
    parcels: List[Parcel],
    capacity: int
) -> List[Dict[str, Any]]:
    """
    Traces the optimal 0/1 knapsack decision path backwards from DP[n][W] to DP[0][0].
    Enables step-by-step matrix visualizer and cell inspection.
    """
    n = len(parcels)
    W = capacity
    w_curr = W
    steps = []

    for i in range(n, 0, -1):
        p = parcels[i - 1]
        curr_val = dp[i][w_curr]
        prev_val = dp[i - 1][w_curr]
        picked = (curr_val != prev_val)

        steps.append({
            "item_index": i - 1,
            "row": i,
            "col": w_curr,
            "parcel_id": p.parcel_id,
            "weight": p.weight,
            "value": p.value,
            "picked": picked,
            "cell_value": curr_val,
            "prev_cell_value": prev_val,
        })

        if picked:
            w_curr -= p.weight

    steps.append({
        "item_index": -1,
        "row": 0,
        "col": w_curr,
        "parcel_id": "Base",
        "weight": 0,
        "value": 0,
        "picked": False,
        "cell_value": dp[0][w_curr] if dp and dp[0] else 0,
        "prev_cell_value": 0,
    })

    return steps


def build_detailed_itinerary(
    ordered_stops: List[str],
    segment_distances: List[tuple],
    selected_parcels: List[Parcel],
    graph: Graph,
    speed_kmh: float = 40.0,
    stop_service_minutes: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Constructs an itinerary timeline including timestamps, ETAs, and package drop-offs.
    """
    itinerary = []
    cum_distance = 0.0
    cum_time_min = 0.0

    # Map destination to list of parcels
    dest_parcels: Dict[str, List[Parcel]] = {}
    for p in selected_parcels:
        dest_parcels.setdefault(p.destination, []).append(p)

    for idx, stop_id in enumerate(ordered_stops):
        leg_dist = 0.0
        if idx > 0 and idx - 1 < len(segment_distances):
            _, _, leg_dist = segment_distances[idx - 1]
            cum_distance += leg_dist
            transit_time = (leg_dist / max(1.0, speed_kmh)) * 60.0
            cum_time_min += transit_time

        node_info = graph.nodes.get(stop_id)
        node_name = node_info.name if node_info else stop_id
        is_depot = node_info.is_depot if node_info else (stop_id == "Depot")

        parcels_dropped = [p.to_dict() for p in dest_parcels.get(stop_id, [])] if not is_depot else []

        itinerary.append({
            "stop_number": idx,
            "node_id": stop_id,
            "node_name": node_name,
            "is_depot": is_depot,
            "x": node_info.x if node_info else 0.0,
            "y": node_info.y if node_info else 0.0,
            "leg_distance_km": round(leg_dist, 2),
            "cumulative_distance_km": round(cum_distance, 2),
            "eta_minutes": round(cum_time_min, 1),
            "parcels_dropped": parcels_dropped,
            "parcels_count": len(parcels_dropped),
        })

        if not is_depot and idx < len(ordered_stops) - 1:
            cum_time_min += stop_service_minutes

    return itinerary


class CourierPlannerRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler serving both the REST API and the Frontend Single-Page App.
    """

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _send_json(self, status_code: int, data: Any):
        """Sends a JSON response with proper headers."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status_code: int, message: str):
        """Sends a structured error JSON."""
        self._send_json(status_code, {"error": message, "status": "error"})

    def do_GET(self):
        """Handles HTTP GET requests for API and static web files."""
        parsed = urlparse(self.path)
        path = parsed.path

        # --- REST API Endpoints ---
        if path == "/api/health":
            self._send_json(200, {
                "status": "ok",
                "service": "Mini-Courier Planner",
                "version": "1.0.0",
                "timestamp": time.time(),
            })
            return

        if path == "/api/datasets":
            self.handle_get_datasets()
            return

        if path.startswith("/api/datasets/"):
            dataset_name = path[len("/api/datasets/"):]
            self.handle_get_single_dataset(dataset_name)
            return

        # --- Static File Serving ---
        self.handle_serve_static(path)

    def do_POST(self):
        """Handles HTTP POST requests for optimization planning and benchmarking."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read JSON request payload
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            try:
                raw_data = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(raw_data)
            except Exception as e:
                self._send_error_json(400, f"Malformed JSON request: {str(e)}")
                return
        else:
            payload = {}

        if path == "/api/plan":
            self.handle_post_plan(payload)
            return

        if path == "/api/benchmark":
            self.handle_post_benchmark(payload)
            return

        self._send_error_json(404, f"API endpoint '{path}' not found.")

    def handle_get_datasets(self):
        """Returns catalog of pre-generated datasets."""
        ensure_datasets()
        datasets = [
            {
                "id": "small",
                "name": "Small Urban Network (8 nodes, 10 parcels)",
                "node_count": 8,
                "parcel_count": 10,
                "recommended_capacity": 40,
                "graph_file": "small_graph.json",
                "parcels_file": "small_parcels.csv",
                "description": "Ideal for pedagogical walkthrough, full DP table inspection, and rapid testing."
            },
            {
                "id": "medium",
                "name": "Medium Suburban District (25 nodes, 50 parcels)",
                "node_count": 25,
                "parcel_count": 50,
                "recommended_capacity": 100,
                "graph_file": "medium_graph.json",
                "parcels_file": "medium_parcels.csv",
                "description": "Realistic district route with multiple clusters and high capacity demands."
            },
            {
                "id": "large",
                "name": "Large Metropolitan Hub (60 nodes, 200 parcels)",
                "node_count": 60,
                "parcel_count": 200,
                "recommended_capacity": 250,
                "graph_file": "large_graph.json",
                "parcels_file": "large_parcels.csv",
                "description": "High-density stress test demonstrating scalability and asymptotic performance."
            }
        ]
        self._send_json(200, {"datasets": datasets})

    def handle_get_single_dataset(self, name: str):
        """Loads and returns graph and parcel data for a given dataset ID."""
        ensure_datasets()
        name = name.lower()
        graph_path = os.path.join(DATASETS_DIR, f"{name}_graph.json")
        parcels_path = os.path.join(DATASETS_DIR, f"{name}_parcels.csv")

        if not os.path.exists(graph_path) or not os.path.exists(parcels_path):
            self._send_error_json(404, f"Dataset '{name}' not found.")
            return

        try:
            graph = Graph.load_json(graph_path)
            parcels = load_parcels_csv(parcels_path)
            rec_cap = 40 if name == "small" else (100 if name == "medium" else 250)

            self._send_json(200, {
                "id": name,
                "graph": graph.to_dict(),
                "parcels": [p.to_dict() for p in parcels],
                "recommended_capacity": rec_cap,
            })
        except Exception as e:
            self._send_error_json(500, f"Error loading dataset '{name}': {str(e)}")

    def handle_post_plan(self, payload: Dict[str, Any]):
        """
        Executes full MiniCourierPlanner on client-provided or preset dataset.
        Computes 0/1 Knapsack DP, TSP routing, detailed itineraries, and benchmarks.
        """
        try:
            # 1. Parse Graph
            if "graph" in payload and payload["graph"]:
                graph = Graph.from_dict(payload["graph"])
            elif "dataset" in payload:
                ds_path = os.path.join(DATASETS_DIR, f"{payload['dataset']}_graph.json")
                graph = Graph.load_json(ds_path)
            else:
                ds_path = os.path.join(DATASETS_DIR, "small_graph.json")
                graph = Graph.load_json(ds_path)

            # 2. Parse Parcels
            parcels_data = payload.get("parcels", [])
            parcels: List[Parcel] = []
            for item in parcels_data:
                parcels.append(Parcel(
                    parcel_id=str(item.get("parcel_id", "")).strip(),
                    destination=str(item.get("destination", "")).strip(),
                    weight=int(item.get("weight", 1)),
                    priority=int(item.get("priority", 1)),
                    deadline=float(item.get("deadline", 24.0)),
                    value=int(item["value"]) if "value" in item and item["value"] not in (None, "") else 0,
                    customer_name=str(item.get("customer_name", "")).strip(),
                ))

            # 3. Parameters
            vehicle_capacity = int(payload.get("vehicle_capacity", 40))
            sort_strategy = str(payload.get("sort_strategy", "deadline_priority"))
            sort_algorithm = str(payload.get("sort_algorithm", "mergesort"))
            use_two_opt = bool(payload.get("use_two_opt", True))
            depot_node = str(payload.get("depot_node", "Depot"))
            speed_kmh = float(payload.get("speed_kmh", 40.0))

            # 4. Execute MiniCourierPlanner
            planner = MiniCourierPlanner(
                sort_strategy=sort_strategy,
                sort_algorithm=sort_algorithm,
                use_two_opt=use_two_opt
            )

            plan_result: CourierPlanResult = planner.plan(
                parcels=parcels,
                graph=graph,
                vehicle_capacity=vehicle_capacity,
                depot_node=depot_node
            )

            # 5. Extract DP Backtracking Path
            backtrack_path = extract_dp_backtracking_path(
                dp=plan_result.packing_result.dp_table,
                parcels=plan_result.prioritized_parcels,
                capacity=vehicle_capacity
            )

            # 6. Build Detailed Turn-by-Turn Itinerary
            itinerary = build_detailed_itinerary(
                ordered_stops=plan_result.route_result.ordered_stops,
                segment_distances=plan_result.route_result.segment_distances,
                selected_parcels=plan_result.packing_result.selected_parcels,
                graph=graph,
                speed_kmh=speed_kmh
            )

            # 7. Algorithmic Benchmarks & Comparative Metrics
            greedy_res = greedy_knapsack(parcels, vehicle_capacity)
            dp_val = plan_result.packing_result.total_value
            greedy_val = greedy_res["total_value"]
            opt_gap = round(((dp_val - greedy_val) / max(1, dp_val)) * 100.0, 1) if dp_val > greedy_val else 0.0

            # Compare TSP Nearest-Neighbor alone vs 2-Opt
            destinations = list({p.destination for p in plan_result.packing_result.selected_parcels})
            all_stops = [depot_node] + [d for d in destinations if d != depot_node]
            dist_mat, _ = compute_distance_matrix(graph, all_stops)
            raw_tour = tsp_nearest_neighbor(depot_node, destinations, dist_mat)
            raw_tour_dist = round(calculate_tour_length(raw_tour, dist_mat), 2)
            opt_tour_dist = plan_result.route_result.total_distance
            dist_saved = round(max(0.0, raw_tour_dist - opt_tour_dist), 2)
            route_reduction_pct = round((dist_saved / max(0.001, raw_tour_dist)) * 100.0, 1) if raw_tour_dist > 0 else 0.0

            # Package full JSON response
            response = {
                "initial_parcel_count": plan_result.initial_parcel_count,
                "prioritized_parcels": [p.to_dict() for p in plan_result.prioritized_parcels],
                "packing_result": {
                    "selected_parcels": [p.to_dict() for p in plan_result.packing_result.selected_parcels],
                    "rejected_parcels": [p.to_dict() for p in plan_result.packing_result.rejected_parcels],
                    "total_weight": plan_result.packing_result.total_weight,
                    "total_value": plan_result.packing_result.total_value,
                    "capacity": plan_result.packing_result.capacity,
                    "capacity_utilization": round(plan_result.packing_result.capacity_utilization, 2),
                    "dp_table": plan_result.packing_result.dp_table,
                    "backtrack_path": backtrack_path,
                    "runtime_ms": round(plan_result.packing_result.runtime_ms, 3),
                },
                "route_result": {
                    "ordered_stops": plan_result.route_result.ordered_stops,
                    "total_distance": plan_result.route_result.total_distance,
                    "detailed_path": plan_result.route_result.detailed_path,
                    "segment_distances": [
                        {"source": u, "target": v, "distance": d}
                        for u, v, d in plan_result.route_result.segment_distances
                    ],
                    "itinerary": itinerary,
                    "runtime_ms": round(plan_result.route_result.runtime_ms, 3),
                },
                "benchmarks": {
                    "knapsack": {
                        "dp_value": dp_val,
                        "greedy_value": greedy_val,
                        "optimality_gap_percent": opt_gap,
                        "dp_weight": plan_result.packing_result.total_weight,
                        "greedy_weight": greedy_res["total_weight"],
                    },
                    "tsp": {
                        "raw_tour": raw_tour,
                        "raw_distance": raw_tour_dist,
                        "optimized_distance": opt_tour_dist,
                        "distance_saved_km": dist_saved,
                        "reduction_percent": route_reduction_pct,
                        "two_opt_enabled": use_two_opt,
                    },
                },
                "total_runtime_ms": round(plan_result.total_runtime_ms, 3),
                "runtime_breakdown_ms": {
                    k: round(v, 3) for k, v in plan_result.runtime_breakdown_ms.items()
                },
            }

            self._send_json(200, response)

        except Exception as e:
            self._send_error_json(400, str(e))

    def handle_post_benchmark(self, payload: Dict[str, Any]):
        """Runs comparative algorithm benchmarks."""
        try:
            parcels_data = payload.get("parcels", [])
            parcels = []
            for item in parcels_data:
                parcels.append(Parcel(
                    parcel_id=str(item.get("parcel_id", "")),
                    destination=str(item.get("destination", "C1")),
                    weight=int(item.get("weight", 1)),
                    priority=int(item.get("priority", 1)),
                    deadline=float(item.get("deadline", 24.0)),
                    value=int(item.get("value", 10)),
                ))

            if not parcels:
                # Load default small parcels for benchmark
                ensure_datasets()
                parcels = load_parcels_csv(os.path.join(DATASETS_DIR, "small_parcels.csv"))

            sort_comp = compare_sorting_algorithms(parcels, trials=10)
            self._send_json(200, {
                "sorting": sort_comp,
                "parcel_count": len(parcels),
            })
        except Exception as e:
            self._send_error_json(500, f"Benchmark execution error: {str(e)}")

    def handle_serve_static(self, path: str):
        """Serves HTML, CSS, JavaScript, and images from the web/ directory."""
        if path in ("", "/"):
            path = "/index.html"

        # Sanitize path to prevent directory traversal
        clean_path = os.path.normpath(path.lstrip("/"))
        file_path = os.path.join(WEB_DIR, clean_path)

        # Allow serving generated images as well
        if clean_path.startswith("images/"):
            file_path = os.path.join(PROJECT_DIR, clean_path)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            if file_path.endswith(".js"):
                mime_type = "application/javascript"
            elif file_path.endswith(".css"):
                mime_type = "text/css"
            elif file_path.endswith(".svg"):
                mime_type = "image/svg+xml"
            else:
                mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type or "json" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"500 Internal Server Error: {str(e)}".encode("utf-8"))

    def log_message(self, format, *args):
        """Clean console logging format."""
        # Suppress normal successful static asset spam, log API calls
        if args and len(args) > 0 and "/api/" in str(args[0]):
            sys.stdout.write(f"[MiniCourier-API] {self.address_string()} - {format % args}\n")
            sys.stdout.flush()


def ensure_datasets():
    """Ensures test datasets exist."""
    os.makedirs(DATASETS_DIR, exist_ok=True)
    small_path = os.path.join(DATASETS_DIR, "small_graph.json")
    if not os.path.exists(small_path):
        generate_default_datasets(DATASETS_DIR)


def create_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Creates a ThreadingHTTPServer instance for concurrent client handling."""
    ensure_datasets()
    server = ThreadingHTTPServer((host, port), CourierPlannerRequestHandler)
    return server


def run_server(host: str = "127.0.0.1", port: int = 8080):
    """Starts the HTTP server on the designated host and port."""
    server = create_server(host, port)
    print(f" Mini-Courier Planner Server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Server shutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port)
