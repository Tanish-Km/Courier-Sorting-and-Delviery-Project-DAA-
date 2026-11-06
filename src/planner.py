"""
Integrated Mini-Courier Planner Orchestrator.
Combines sorting, 0/1 knapsack dynamic programming, Dijkstra's shortest path,
and Nearest-Neighbor TSP approximation into an end-to-end delivery management engine.
"""

from typing import List, Dict, Any, Optional
import time
from .models import Parcel, CourierPlanResult
from .sorting import prioritize_parcels
from .knapsack import knapsack_01_dp
from .graph import Graph, compute_distance_matrix, dijkstra
from .routing import tsp_nearest_neighbor, two_opt_optimize, build_full_delivery_route


class MiniCourierPlanner:
    """
    Main controller for the intelligent courier planning pipeline.
    """

    def __init__(
        self,
        sort_strategy: str = "deadline_priority",
        sort_algorithm: str = "mergesort",
        use_two_opt: bool = True
    ):
        self.sort_strategy = sort_strategy
        self.sort_algorithm = sort_algorithm
        self.use_two_opt = use_two_opt

    def plan(
        self,
        parcels: List[Parcel],
        graph: Graph,
        vehicle_capacity: int,
        depot_node: str = "Depot"
    ) -> CourierPlanResult:
        """
        Executes the complete courier planning workflow.
        
        Phases:
          1. Validation & Input Structuring (Validates depot, capacities, and network reachability)
          2. Parcel Prioritization (Sorting) & Knapsack Box-Filling (DP)
          3. Shortest Path Metric Construction (Dijkstra) & Route Optimization (TSP)
          4. Performance Logging & Result Assembly
        """
        t_total_start = time.perf_counter()
        runtime_breakdown: Dict[str, float] = {}

        # --- Phase 1: Input Validation & Graph Topology Verification ---
        if vehicle_capacity < 0:
            raise ValueError(f"Vehicle capacity cannot be negative: {vehicle_capacity}")

        if depot_node not in graph.adjacency:
            raise ValueError(f"Depot node '{depot_node}' not found in road network graph.")

        # Verify all candidate parcel destinations exist in graph and are reachable from depot
        depot_distances, _ = dijkstra(graph, depot_node)
        for p in parcels:
            if p.destination not in graph.adjacency:
                raise ValueError(
                    f"Destination node '{p.destination}' for parcel '{p.parcel_id}' does not exist in road network graph."
                )
            if depot_distances.get(p.destination, float("inf")) == float("inf"):
                raise ValueError(
                    f"Destination node '{p.destination}' for parcel '{p.parcel_id}' is unreachable from depot '{depot_node}'."
                )

        # --- Phase 2A: Sorting & Prioritization ---
        t0 = time.perf_counter()
        prioritized = prioritize_parcels(
            parcels,
            strategy=self.sort_strategy,
            algorithm=self.sort_algorithm
        )
        runtime_breakdown["sorting_ms"] = (time.perf_counter() - t0) * 1000.0

        # --- Phase 2B: 0/1 Knapsack Dynamic Programming ---
        t0 = time.perf_counter()
        packing_result = knapsack_01_dp(prioritized, capacity=vehicle_capacity)
        runtime_breakdown["knapsack_dp_ms"] = (time.perf_counter() - t0) * 1000.0

        # Collect target delivery nodes for packed parcels
        destinations = list({p.destination for p in packing_result.selected_parcels})
        # Ensure all destinations exist in graph
        for dest in destinations:
            if dest not in graph.adjacency:
                raise ValueError(f"Destination node '{dest}' does not exist in road network graph.")

        # Include depot in metric subgraph
        all_stops = [depot_node] + [d for d in destinations if d != depot_node]

        # --- Phase 3A: Dijkstra's Algorithm ---
        t0 = time.perf_counter()
        dist_matrix, path_matrix = compute_distance_matrix(graph, all_stops)
        runtime_breakdown["dijkstra_ms"] = (time.perf_counter() - t0) * 1000.0

        # --- Phase 3B: Nearest-Neighbor TSP + 2-Opt ---
        t0 = time.perf_counter()
        initial_tour = tsp_nearest_neighbor(depot_node, destinations, dist_matrix)
        
        if self.use_two_opt and len(initial_tour) > 3:
            optimized_tour = two_opt_optimize(initial_tour, dist_matrix)
        else:
            optimized_tour = initial_tour
            
        route_result = build_full_delivery_route(optimized_tour, dist_matrix, path_matrix)
        runtime_breakdown["tsp_routing_ms"] = (time.perf_counter() - t0) * 1000.0

        total_runtime_ms = (time.perf_counter() - t_total_start) * 1000.0

        return CourierPlanResult(
            initial_parcel_count=len(parcels),
            prioritized_parcels=prioritized,
            packing_result=packing_result,
            route_result=route_result,
            total_runtime_ms=total_runtime_ms,
            runtime_breakdown_ms=runtime_breakdown,
        )
