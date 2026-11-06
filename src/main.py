"""
Command Line Interface and Main Executable for Mini-Courier Planner.
"""

import os
import sys
import argparse
import csv
import json
from typing import List, Dict, Any

from src.models import Parcel, CourierPlanResult
from src.sorting import prioritize_parcels, compare_sorting_algorithms
from src.knapsack import knapsack_01_dp, format_dp_table_text
from src.graph import Graph, compute_distance_matrix, dijkstra
from src.routing import tsp_nearest_neighbor, two_opt_optimize, build_full_delivery_route
from src.planner import MiniCourierPlanner
from src.benchmark import generate_synthetic_graph, generate_synthetic_parcels, run_scalability_benchmarks
from src.visualization import (
    draw_system_architecture,
    draw_dp_matrix_heatmap,
    draw_route_map,
    draw_benchmark_charts,
    draw_console_showcase,
)


def load_parcels_csv(file_path: str) -> List[Parcel]:
    """Loads parcel records from a CSV file."""
    parcels = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parcels.append(Parcel(
                parcel_id=row["parcel_id"].strip(),
                destination=row["destination"].strip(),
                weight=int(row["weight"]),
                priority=int(row.get("priority", 1)),
                deadline=float(row.get("deadline", 24.0)),
                value=int(row["value"]) if "value" in row and row["value"].strip() else 0,
                customer_name=row.get("customer_name", "").strip(),
            ))
    return parcels


def save_parcels_csv(parcels: List[Parcel], file_path: str) -> None:
    """Saves parcels to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["parcel_id", "destination", "weight", "priority", "deadline", "value", "customer_name"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in parcels:
            writer.writerow(p.to_dict())


def generate_default_datasets(datasets_dir: str = "datasets") -> None:
    """Generates standard small, medium, and large test datasets."""
    os.makedirs(datasets_dir, exist_ok=True)

    # 1. Small Network (8 nodes) & Small Parcels (10 items)
    small_graph = generate_synthetic_graph(num_nodes=8, seed=42)
    small_graph.save_json(os.path.join(datasets_dir, "small_graph.json"))
    small_parcels = [
        Parcel("P101", "C1", weight=5, priority=4, deadline=2.0, value=75, customer_name="Alice (Tech Corp)"),
        Parcel("P102", "C2", weight=12, priority=5, deadline=1.5, value=95, customer_name="Dr. Banner (Hospital)"),
        Parcel("P103", "C3", weight=8, priority=3, deadline=4.0, value=55, customer_name="Charlie (Cafe Central)"),
        Parcel("P104", "C4", weight=15, priority=2, deadline=8.0, value=40, customer_name="David (Home Decor)"),
        Parcel("P105", "C5", weight=6, priority=5, deadline=1.0, value=98, customer_name="Emergency Clinic"),
        Parcel("P106", "C6", weight=10, priority=4, deadline=3.0, value=70, customer_name="Frank (Law Chambers)"),
        Parcel("P107", "C7", weight=4, priority=2, deadline=6.0, value=35, customer_name="Grace (Book Store)"),
        Parcel("P108", "C2", weight=7, priority=3, deadline=5.0, value=52, customer_name="City Labs"),
        Parcel("P109", "C3", weight=14, priority=1, deadline=12.0, value=25, customer_name="Hardware Depot"),
        Parcel("P110", "C5", weight=9, priority=4, deadline=2.5, value=72, customer_name="Ortho Care"),
    ]
    save_parcels_csv(small_parcels, os.path.join(datasets_dir, "small_parcels.csv"))

    # 2. Medium Network (25 nodes) & Medium Parcels (50 items)
    med_graph = generate_synthetic_graph(num_nodes=25, seed=123)
    med_graph.save_json(os.path.join(datasets_dir, "medium_graph.json"))
    med_parcels = generate_synthetic_parcels(50, med_graph.get_nodes(), seed=456)
    save_parcels_csv(med_parcels, os.path.join(datasets_dir, "medium_parcels.csv"))

    # 3. Large Network (60 nodes) & Large Parcels (200 items)
    large_graph = generate_synthetic_graph(num_nodes=60, seed=789)
    large_graph.save_json(os.path.join(datasets_dir, "large_graph.json"))
    large_parcels = generate_synthetic_parcels(200, large_graph.get_nodes(), seed=999)
    save_parcels_csv(large_parcels, os.path.join(datasets_dir, "large_parcels.csv"))


def run_pipeline_demo(vehicle_capacity: int = 40, output_dir: str = "images") -> str:
    """
    Executes a comprehensive demonstration of all 5 capstone phases,
    printing clear outputs and generating diagrams.
    """
    os.makedirs(output_dir, exist_ok=True)
    generate_default_datasets()

    graph = Graph.load_json("datasets/small_graph.json")
    parcels = load_parcels_csv("datasets/small_parcels.csv")

    lines = []
    lines.append("================================================================================")
    lines.append("                     MINI-COURIER PLANNER EXECUTION PIPELINE                    ")
    lines.append("================================================================================")
    lines.append(f"Loaded {len(parcels)} parcels and road network with {len(graph.get_nodes())} nodes.")
    lines.append(f"Vehicle Payload Weight Capacity: {vehicle_capacity} kg")
    lines.append("")

    # --- Phase 1: Problem Design ---
    lines.append("--- [PHASE 1: PROBLEM DESIGN & ATTRIBUTES] ---")
    lines.append("Parcel attributes: parcel_id, destination, weight (kg), priority (1-5), deadline (hrs), value")
    lines.append(f"Depot vertex: Depot | Total Customer Delivery Locations: {len(graph.get_nodes()) - 1}")
    lines.append("")

    # --- Phase 2A: Sorting ---
    lines.append("--- [PHASE 2A: PACKAGE PRIORITIZATION (SORTING)] ---")
    prioritized = prioritize_parcels(parcels, strategy="deadline_priority", algorithm="mergesort")
    lines.append(f"{'Rank':<5} {'ID':<6} {'Dest':<6} {'Weight':<8} {'Priority':<9} {'Deadline':<10} {'Value':<6}")
    lines.append("-" * 55)
    for idx, p in enumerate(prioritized, 1):
        lines.append(f"{idx:<5} {p.parcel_id:<6} {p.destination:<6} {p.weight:<8} {p.priority:<9} {p.deadline:<10.1f} {p.value:<6}")
    lines.append("")

    # --- Phase 2B: 0/1 Knapsack DP ---
    lines.append("--- [PHASE 2B: OPTIMAL BOX FILLING (0/1 KNAPSACK DP)] ---")
    packing = knapsack_01_dp(prioritized, capacity=vehicle_capacity)
    lines.append(f"Optimal Cumulative Delivery Value: {packing.total_value} points")
    lines.append(f"Total Packed Weight: {packing.total_weight} / {vehicle_capacity} kg ({packing.capacity_utilization:.1f}% capacity utilization)")
    lines.append(f"Selected Parcels ({len(packing.selected_parcels)}): {', '.join(p.parcel_id for p in packing.selected_parcels)}")
    lines.append(f"Rejected Parcels ({len(packing.rejected_parcels)}): {', '.join(p.parcel_id for p in packing.rejected_parcels)}")
    lines.append("")
    lines.append("Dynamic Programming Table Truncated View DP[i][w]:")
    dp_view = format_dp_table_text(packing.dp_table, prioritized, vehicle_capacity, max_w=12, max_items=6)
    lines.append(dp_view)
    lines.append("")

    # --- Phase 3: Route Maker & Shortest Path ---
    lines.append("--- [PHASE 3: ROUTE MAKER & GRAPH PROCESSING] ---")
    destinations = list({p.destination for p in packing.selected_parcels})
    all_stops = ["Depot"] + [d for d in destinations if d != "Depot"]
    dist_mat, path_mat = compute_distance_matrix(graph, all_stops)

    raw_tour = tsp_nearest_neighbor("Depot", destinations, dist_mat)
    optimized_tour = two_opt_optimize(raw_tour, dist_mat)
    route = build_full_delivery_route(optimized_tour, dist_mat, path_mat)

    lines.append(f"Delivery Stop Sequence: {' -> '.join(route.ordered_stops)}")
    lines.append(f"Total Route Distance: {route.total_distance:.2f} km")
    lines.append(f"Turn-by-turn Roadway Path: {' -> '.join(route.detailed_path)}")
    lines.append("Segment Breakdown:")
    for u, v, d in route.segment_distances:
        lines.append(f"  * {u} -> {v}: {d:.2f} km")
    lines.append("")

    # --- Phase 4: Benchmarks ---
    lines.append("--- [PHASE 4: PERFORMANCE BENCHMARKING & OPTIMIZATION] ---")
    benchmarks = run_scalability_benchmarks()
    lines.append(f"{'Scale':<18} {'MergeSort':<12} {'QuickSort':<12} {'Knapsack DP':<14} {'Dijkstra':<12} {'TSP 2-Opt':<12} {'Total Pipeline'}")
    lines.append("-" * 95)
    for i in range(len(benchmarks["sizes"])):
        lines.append(
            f"{benchmarks['sizes'][i]:<18} "
            f"{benchmarks['mergesort_times'][i]:<12.3f} "
            f"{benchmarks['quicksort_times'][i]:<12.3f} "
            f"{benchmarks['knapsack_times'][i]:<14.3f} "
            f"{benchmarks['dijkstra_allpairs_times'][i]:<12.3f} "
            f"{benchmarks['tsp_times'][i]:<12.3f} "
            f"{benchmarks['total_pipeline_times'][i]:.3f} ms"
        )
    lines.append("")

    # --- Phase 5: Deliverables & Visualization Generation ---
    lines.append("--- [PHASE 5: GENERATING VISUAL EVIDENCE & DIAGRAMS] ---")
    draw_system_architecture(os.path.join(output_dir, "system_architecture.png"))
    lines.append(f"  [+] Saved: {output_dir}/system_architecture.png")

    draw_dp_matrix_heatmap(packing.dp_table, prioritized, vehicle_capacity, os.path.join(output_dir, "knapsack_dp_matrix.png"))
    lines.append(f"  [+] Saved: {output_dir}/knapsack_dp_matrix.png")

    draw_route_map(graph, route, os.path.join(output_dir, "delivery_route_visualization.png"))
    lines.append(f"  [+] Saved: {output_dir}/delivery_route_visualization.png")

    draw_benchmark_charts(benchmarks, os.path.join(output_dir, "runtime_comparison.png"))
    lines.append(f"  [+] Saved: {output_dir}/runtime_comparison.png")

    summary_text = "\n".join(lines)
    draw_console_showcase(summary_text, os.path.join(output_dir, "console_output_demo.png"))
    lines.append(f"  [+] Saved: {output_dir}/console_output_demo.png")
    lines.append("================================================================================")
    lines.append("                     PIPELINE EXECUTION COMPLETED SUCCESSFULLY                  ")
    lines.append("================================================================================")

    full_output = "\n".join(lines)
    return full_output


def main():
    parser = argparse.ArgumentParser(description="Mini-Courier Planner Capstone CLI")
    parser.add_argument("--demo", action="store_true", help="Run full demonstration pipeline and generate figures")
    parser.add_argument("--capacity", type=int, default=40, help="Vehicle payload capacity in kg (default: 40)")
    parser.add_argument("--parcels", type=str, default="datasets/small_parcels.csv", help="Path to parcels CSV")
    parser.add_argument("--graph", type=str, default="datasets/small_graph.json", help="Path to road network graph JSON")
    args = parser.parse_args()

    if args.demo or not os.path.exists(args.parcels):
        output = run_pipeline_demo(vehicle_capacity=args.capacity)
        print(output)
    else:
        graph = Graph.load_json(args.graph)
        parcels = load_parcels_csv(args.parcels)
        planner = MiniCourierPlanner()
        result = planner.plan(parcels, graph, vehicle_capacity=args.capacity)
        print(f"Mini-Courier Planner executed in {result.total_runtime_ms:.2f} ms")
        print(f"Packed {len(result.packing_result.selected_parcels)} parcels, Total Value: {result.packing_result.total_value}")
        print(f"Delivery Route: {' -> '.join(result.route_result.ordered_stops)} ({result.route_result.total_distance:.2f} km)")


if __name__ == "__main__":
    main()
