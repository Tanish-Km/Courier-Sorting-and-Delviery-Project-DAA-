"""
Travelling Salesperson Problem (TSP) solvers and route builders:
Nearest-Neighbor heuristic, 2-Opt local search improvement, and full path expansion.
"""

from typing import List, Dict, Tuple, Optional
import time
from .models import RouteResult


def tsp_nearest_neighbor(
    start_node: str,
    delivery_nodes: List[str],
    dist_matrix: Dict[Tuple[str, str], float]
) -> List[str]:
    """
    Constructs an approximate TSP tour using the Greedy Nearest-Neighbor heuristic.
    
    The courier begins at start_node (Depot), visits all unique delivery stops,
    and returns to start_node.
    
    Algorithm:
      1. Initialize tour with start_node.
      2. Maintain unvisited set U = set(delivery_nodes).
      3. At current node u, find v in U that minimizes dist_matrix[(u, v)].
      4. Append v to tour, remove v from U, set u = v.
      5. Once U is empty, return to start_node.
      
    Complexity:
      Time Complexity:  O(K^2) where K is number of delivery locations.
      Space Complexity: O(K)
      Approximation Ratio: O(log K) for metric TSP.
    """
    if not delivery_nodes:
        return [start_node, start_node]

    # Ensure unique stops excluding the start node
    unvisited = set(node for node in delivery_nodes if node != start_node)
    tour = [start_node]
    current = start_node

    while unvisited:
        nearest = None
        min_dist = float("inf")
        for candidate in unvisited:
            d = dist_matrix.get((current, candidate), float("inf"))
            if d < min_dist:
                min_dist = d
                nearest = candidate

        if nearest is None:
            # Graph disconnected or unreachable
            break

        tour.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    # Close the cycle back to start_node
    tour.append(start_node)
    return tour


def calculate_tour_length(tour: List[str], dist_matrix: Dict[Tuple[str, str], float]) -> float:
    """Computes total cumulative distance of a given tour."""
    total = 0.0
    for i in range(len(tour) - 1):
        u, v = tour[i], tour[i + 1]
        dist = dist_matrix.get((u, v), float("inf"))
        total += dist
    return total


def two_opt_optimize(
    tour: List[str],
    dist_matrix: Dict[Tuple[str, str], float],
    max_iterations: int = 500
) -> List[str]:
    """
    Optimizes a TSP tour using the 2-Opt local search heuristic.
    Iteratively swaps edge pairs (i-1, i) and (j, j+1) whenever reversing the
    sub-route tour[i : j+1] reduces total distance, eliminating route crossings.
    
    Employs O(1) symmetric delta evaluation when the distance metric is symmetric,
    yielding orders-of-magnitude acceleration on planar road networks.
    
    Complexity: O(iterations * K^2)
    """
    if len(tour) <= 3:
        return list(tour)

    best_tour = list(tour)
    best_distance = calculate_tour_length(best_tour, dist_matrix)
    n = len(tour) - 1  # Excluding the duplicate closing depot stop

    # Check symmetry across unique stops in the tour
    unique_stops = list(dict.fromkeys(tour))
    is_symmetric = all(
        abs(dist_matrix.get((u, v), float("inf")) - dist_matrix.get((v, u), float("inf"))) < 1e-5
        for u in unique_stops
        for v in unique_stops
    )

    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        for i in range(1, n - 1):
            u_prev = best_tour[i - 1]
            u_curr = best_tour[i]
            d_u = dist_matrix.get((u_prev, u_curr), float("inf"))

            for j in range(i + 1, n):
                v_curr = best_tour[j]
                v_next = best_tour[j + 1]
                d_v = dist_matrix.get((v_curr, v_next), float("inf"))

                d_new_u = dist_matrix.get((u_prev, v_curr), float("inf"))
                d_new_v = dist_matrix.get((u_curr, v_next), float("inf"))

                if is_symmetric:
                    delta = (d_new_u + d_new_v) - (d_u + d_v)
                else:
                    cand_tour = best_tour[:i] + best_tour[i:j + 1][::-1] + best_tour[j + 1:]
                    delta = calculate_tour_length(cand_tour, dist_matrix) - best_distance

                if delta < -1e-6:
                    best_tour = best_tour[:i] + best_tour[i:j + 1][::-1] + best_tour[j + 1:]
                    best_distance += delta
                    improved = True
                    break
            if improved:
                break

    return best_tour


def build_full_delivery_route(
    tour: List[str],
    dist_matrix: Dict[Tuple[str, str], float],
    path_matrix: Dict[Tuple[str, str], List[str]]
) -> RouteResult:
    """
    Expands the high-level TSP sequence into turn-by-turn road network paths,
    computes segment distances, and packages results into RouteResult.
    """
    start_time = time.perf_counter()

    if len(tour) <= 2 and len(set(tour)) <= 1:
        return RouteResult(
            ordered_stops=list(tour),
            total_distance=0.0,
            detailed_path=list(tour),
            segment_distances=[(tour[0], tour[-1], 0.0)] if len(tour) == 2 else [],
            runtime_ms=(time.perf_counter() - start_time) * 1000.0,
        )

    detailed_path: List[str] = []
    segment_distances: List[Tuple[str, str, float]] = []
    total_distance = 0.0

    for i in range(len(tour) - 1):
        u, v = tour[i], tour[i + 1]
        dist = dist_matrix.get((u, v), 0.0)
        segment_distances.append((u, v, dist))
        total_distance += dist

        sub_path = path_matrix.get((u, v), [u, v])
        if not detailed_path:
            detailed_path.extend(sub_path if sub_path else [u, v])
        else:
            # Skip the starting node of the sub-path since it matches the previous end node
            if len(sub_path) > 1:
                detailed_path.extend(sub_path[1:])
            elif u == v:
                detailed_path.append(v)

    runtime_ms = (time.perf_counter() - start_time) * 1000.0

    return RouteResult(
        ordered_stops=tour,
        total_distance=round(total_distance, 2),
        detailed_path=detailed_path,
        segment_distances=segment_distances,
        runtime_ms=runtime_ms,
    )
