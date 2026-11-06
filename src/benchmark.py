"""
Performance benchmarking and scalability analysis suite for the Mini-Courier Planner.
Evaluates algorithmic complexity across multiple input sizes.
"""

from typing import List, Dict, Any, Tuple
import time
import random
from .models import Parcel
from .graph import Graph, dijkstra, compute_distance_matrix
from .sorting import mergesort, quicksort, compare_sorting_algorithms
from .knapsack import knapsack_01_dp, knapsack_01_space_optimized
from .routing import tsp_nearest_neighbor, two_opt_optimize
from .planner import MiniCourierPlanner


def generate_synthetic_graph(num_nodes: int, grid_size: float = 100.0, seed: int = 42) -> Graph:
    """
    Generates a realistic connected planar road network graph with coordinates.
    """
    rng = random.Random(seed)
    g = Graph(directed=False)

    # 1. Place depot at center
    g.add_node("Depot", name="Central Distribution Depot", x=grid_size / 2.0, y=grid_size / 2.0, is_depot=True)

    # 2. Place customer nodes
    for i in range(1, num_nodes):
        node_id = f"C{i}"
        x = round(rng.uniform(5.0, grid_size - 5.0), 2)
        y = round(rng.uniform(5.0, grid_size - 5.0), 2)
        g.add_node(node_id, name=f"Customer Location {i}", x=x, y=y)

    nodes = g.get_nodes()

    # 3. Connect nodes with k-nearest neighbors to ensure realistic road topology
    coords = {nid: (g.nodes[nid].x, g.nodes[nid].y) for nid in nodes}

    for u in nodes:
        distances = []
        for v in nodes:
            if u != v:
                dx = coords[u][0] - coords[v][0]
                dy = coords[u][1] - coords[v][1]
                dist = round((dx * dx + dy * dy) ** 0.5, 2)
                distances.append((dist, v))
        distances.sort(key=lambda item: item[0])

        # Connect to 3 to 4 nearest neighbors
        k = rng.randint(3, min(5, len(nodes) - 1))
        for dist, v in distances[:k]:
            g.add_edge(u, v, dist)

    return g


def generate_synthetic_parcels(
    count: int,
    available_destinations: List[str],
    seed: int = 42
) -> List[Parcel]:
    """Generates synthetic parcel datasets with realistic weight, priority, and deadline distributions."""
    rng = random.Random(seed)
    parcels = []
    customer_dests = [d for d in available_destinations if d != "Depot"]

    for i in range(1, count + 1):
        pid = f"P{1000 + i}"
        dest = rng.choice(customer_dests)
        weight = rng.randint(1, 15)  # 1 to 15 kg
        priority = rng.choices([1, 2, 3, 4, 5], weights=[0.25, 0.30, 0.25, 0.15, 0.05])[0]
        deadline = round(rng.choice([1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 24.0]), 1)
        urgency_bonus = max(0, int(round((12.0 - min(deadline, 12.0)) * 2)))
        val = priority * 15 + urgency_bonus

        parcels.append(Parcel(
            parcel_id=pid,
            destination=dest,
            weight=weight,
            priority=priority,
            deadline=deadline,
            value=val,
            customer_name=f"Customer {dest}"
        ))

    return parcels


def run_scalability_benchmarks(
    sizes: List[Tuple[int, int]] = None
) -> Dict[str, Any]:
    """
    Executes benchmark suites across specified (parcel_count, graph_nodes) scales.
    Default sizes: (10, 8), (50, 25), (100, 40), (250, 60), (500, 80).
    """
    if sizes is None:
        sizes = [(10, 8), (50, 20), (100, 35), (200, 50), (400, 75)]

    benchmark_data = {
        "sizes": [],
        "mergesort_times": [],
        "quicksort_times": [],
        "timsort_times": [],
        "knapsack_times": [],
        "dijkstra_allpairs_times": [],
        "tsp_times": [],
        "total_pipeline_times": [],
    }

    planner = MiniCourierPlanner()

    for n_parcels, n_nodes in sizes:
        graph = generate_synthetic_graph(num_nodes=n_nodes, seed=100 + n_nodes)
        parcels = generate_synthetic_parcels(count=n_parcels, available_destinations=graph.get_nodes(), seed=200 + n_parcels)
        capacity = max(20, int(n_parcels * 4.5))

        # Benchmark sorting
        sort_res = compare_sorting_algorithms(parcels, trials=3)

        # Benchmark Knapsack
        t0 = time.perf_counter()
        pack_res = knapsack_01_dp(parcels, capacity=capacity)
        knapsack_ms = (time.perf_counter() - t0) * 1000.0

        # Benchmark Dijkstra & TSP on packed subset
        destinations = list({p.destination for p in pack_res.selected_parcels})
        stops = ["Depot"] + [d for d in destinations if d != "Depot"]

        t0 = time.perf_counter()
        dist_mat, path_mat = compute_distance_matrix(graph, stops)
        dijkstra_ms = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        tour = tsp_nearest_neighbor("Depot", destinations, dist_mat)
        tour_opt = two_opt_optimize(tour, dist_mat)
        tsp_ms = (time.perf_counter() - t0) * 1000.0

        total_ms = sort_res["mergesort_time_ms"] + knapsack_ms + dijkstra_ms + tsp_ms

        benchmark_data["sizes"].append(f"N={n_parcels}, |V|={n_nodes}")
        benchmark_data["mergesort_times"].append(round(sort_res["mergesort_time_ms"], 3))
        benchmark_data["quicksort_times"].append(round(sort_res["quicksort_time_ms"], 3))
        benchmark_data["timsort_times"].append(round(sort_res["timsort_time_ms"], 3))
        benchmark_data["knapsack_times"].append(round(knapsack_ms, 3))
        benchmark_data["dijkstra_allpairs_times"].append(round(dijkstra_ms, 3))
        benchmark_data["tsp_times"].append(round(tsp_ms, 3))
        benchmark_data["total_pipeline_times"].append(round(total_ms, 3))

    return benchmark_data
