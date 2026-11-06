"""
Publication-quality visualization module for the Mini-Courier Planner using PyCairo.
Generates system architecture diagrams, DP decision heatmaps, road network route maps,
and scalability benchmark charts.
"""

from typing import List, Dict, Tuple, Any, Optional
import cairo
import math
from .models import Parcel, PackingResult, RouteResult
from .graph import Graph


def draw_system_architecture(output_path: str, width: int = 1200, height: int = 700) -> None:
    """
    Renders a high-resolution architectural workflow diagram detailing all five phases.
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # 1. Background
    ctx.set_source_rgb(0.96, 0.97, 0.99)
    ctx.paint()

    # Title Banner
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.1, 0.15, 0.25)
    ctx.move_to(50, 55)
    ctx.show_text("Mini-Courier Planner: Algorithmic Architecture & System Pipeline")

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(14)
    ctx.set_source_rgb(0.35, 0.42, 0.52)
    ctx.move_to(50, 85)
    ctx.show_text("Integrated Pipeline: Multi-Criteria Sorting -> 0/1 Knapsack DP -> Dijkstra Metric -> 2-Opt TSP Routing")

    # Phase boxes definition
    phases = [
        {
            "phase": "Phase 1: Design & Models",
            "algo": "Entities & Problem Setup",
            "details": ["• Parcel: ID, w, v, deadline", "• DeliveryPoint: (x, y)", "• Graph: Adjacency List", "• Feasibility Constraints"],
            "color": (0.22, 0.53, 0.85),
            "x": 60, "y": 140, "w": 195, "h": 460
        },
        {
            "phase": "Phase 2A: Prioritization",
            "algo": "MergeSort / QuickSort",
            "details": ["• Key: (Deadline, -Priority)", "• O(N log N) Stable Sort", "• Median-of-3 QuickSort", "• Urgency ordering"],
            "color": (0.16, 0.65, 0.53),
            "x": 285, "y": 140, "w": 195, "h": 460
        },
        {
            "phase": "Phase 2B: Box Filling",
            "algo": "0/1 Knapsack DP",
            "details": ["• DP[i][w] Tabulation", "• Vehicle Payload Limit W", "• Maximize sum(Value)", "• Backtracking Selection"],
            "color": (0.85, 0.45, 0.15),
            "x": 510, "y": 140, "w": 195, "h": 460
        },
        {
            "phase": "Phase 3A: Shortest Path",
            "algo": "Dijkstra's Algorithm",
            "details": ["• Min-Heap Priority Queue", "• All-Pairs Metric on stops", "• Predecessor pointers", "• O((V+E) log V)"],
            "color": (0.55, 0.28, 0.80),
            "x": 735, "y": 140, "w": 195, "h": 460
        },
        {
            "phase": "Phase 3B: Route Maker",
            "algo": "TSP Nearest-Neighbor + 2-Opt",
            "details": ["• Greedy Tour Generation", "• 2-Opt Edge-Cross Removal", "• Depot -> Stops -> Depot", "• Detailed road expansion"],
            "color": (0.82, 0.22, 0.35),
            "x": 960, "y": 140, "w": 195, "h": 460
        },
    ]

    for p in phases:
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        r, g, b = p["color"]

        # Card shadow
        ctx.set_source_rgba(0.0, 0.0, 0.0, 0.06)
        ctx.rectangle(x + 4, y + 4, w, h)
        ctx.fill()

        # Card background
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.rectangle(x, y, w, h)
        ctx.fill()

        # Top banner
        ctx.set_source_rgb(r, g, b)
        ctx.rectangle(x, y, w, 65)
        ctx.fill()

        # Card Border
        ctx.set_line_width(1.5)
        ctx.set_source_rgb(r, g, b)
        ctx.rectangle(x, y, w, h)
        ctx.stroke()

        # Phase title
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(12)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(x + 12, y + 25)
        ctx.show_text(p["phase"])

        # Algorithm name
        ctx.set_font_size(11)
        ctx.move_to(x + 12, y + 48)
        ctx.show_text(p["algo"])

        # Card body items
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(12)
        ctx.set_source_rgb(0.2, 0.25, 0.3)

        curr_y = y + 105
        for item in p["details"]:
            ctx.move_to(x + 15, curr_y)
            ctx.show_text(item)
            curr_y += 32

    # Draw connection arrows between cards
    ctx.set_line_width(3.0)
    ctx.set_source_rgb(0.4, 0.45, 0.55)
    for i in range(len(phases) - 1):
        x1 = phases[i]["x"] + phases[i]["w"]
        x2 = phases[i + 1]["x"]
        arrow_y = 370

        ctx.move_to(x1 + 4, arrow_y)
        ctx.line_to(x2 - 4, arrow_y)
        ctx.stroke()

        # Arrowhead
        ctx.move_to(x2 - 4, arrow_y)
        ctx.line_to(x2 - 12, arrow_y - 6)
        ctx.line_to(x2 - 12, arrow_y + 6)
        ctx.close_path()
        ctx.fill()

    # Footer note
    ctx.select_font_face("Sans", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(12)
    ctx.set_source_rgb(0.4, 0.45, 0.5)
    ctx.move_to(50, 650)
    ctx.show_text("Capstone Project: Algorithmic paradigms validated across sorting stability, optimal knapsack DP, and TSP approximation.")

    surface.write_to_png(output_path)


def draw_dp_matrix_heatmap(
    dp_table: List[List[int]],
    parcels: List[Parcel],
    capacity: int,
    output_path: str,
    max_w: int = 16,
    max_items: int = 10
) -> None:
    """
    Renders a clear tabular heatmap of the 0/1 Knapsack dynamic programming matrix.
    """
    rows = min(len(parcels) + 1, max_items + 1)
    cols = min(capacity + 1, max_w + 1)

    cell_w = 46
    cell_h = 34
    margin_left = 220
    margin_top = 110
    width = margin_left + cols * cell_w + 50
    height = margin_top + rows * cell_h + 80

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Background
    ctx.set_source_rgb(0.98, 0.98, 0.99)
    ctx.paint()

    # Title
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(20)
    ctx.set_source_rgb(0.12, 0.16, 0.24)
    ctx.move_to(40, 45)
    ctx.show_text("Phase 2: 0/1 Knapsack Dynamic Programming Table DP[i][w]")

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(13)
    ctx.set_source_rgb(0.4, 0.45, 0.55)
    ctx.move_to(40, 72)
    ctx.show_text(f"Optimal Value Formulation: Capacity W={capacity} kg | Showing first {rows-1} items & {cols-1} weight steps")

    # Backtracking path set
    w_curr = cols - 1
    optimal_path_cells = set()
    for i in range(rows - 1, 0, -1):
        optimal_path_cells.add((i, w_curr))
        if dp_table[i][w_curr] != dp_table[i - 1][w_curr]:
            w_curr -= parcels[i - 1].weight
            if w_curr < 0:
                break
    optimal_path_cells.add((0, max(0, w_curr)))

    max_val = max(1, max(max(row[:cols]) for row in dp_table[:rows]))

    # Draw Column Headers (Weights)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(11)
    for c in range(cols):
        cx = margin_left + c * cell_w
        cy = margin_top - 12
        ctx.set_source_rgb(0.2, 0.25, 0.35)
        ctx.move_to(cx + cell_w / 2 - 8, cy)
        ctx.show_text(f"{c}")

    ctx.move_to(margin_left - 70, margin_top - 12)
    ctx.show_text("Weight (w) ->")

    # Draw Table
    for r in range(rows):
        cy = margin_top + r * cell_h

        # Row label
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if r > 0 else cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(11)
        ctx.set_source_rgb(0.15, 0.2, 0.3)
        if r == 0:
            label = "0: Base (None)"
        else:
            p = parcels[r - 1]
            label = f"{p.parcel_id} (w={p.weight}, v={p.value})"

        ctx.move_to(30, cy + cell_h / 2 + 4)
        ctx.show_text(label)

        for c in range(cols):
            cx = margin_left + c * cell_w
            val = dp_table[r][c]
            norm = val / max_val

            # Heatmap background color
            if (r, c) in optimal_path_cells and val > 0:
                ctx.set_source_rgb(0.85, 0.95, 0.85)  # Highlighted optimal cell
            else:
                # Soft blue gradient
                ctx.set_source_rgb(1.0 - norm * 0.3, 1.0 - norm * 0.2, 1.0)
            ctx.rectangle(cx, cy, cell_w - 2, cell_h - 2)
            ctx.fill()

            # Border
            if (r, c) in optimal_path_cells and val > 0:
                ctx.set_line_width(2.0)
                ctx.set_source_rgb(0.15, 0.65, 0.25)
            else:
                ctx.set_line_width(0.7)
                ctx.set_source_rgb(0.78, 0.82, 0.88)
            ctx.rectangle(cx, cy, cell_w - 2, cell_h - 2)
            ctx.stroke()

            # Cell text
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if (r, c) in optimal_path_cells else cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(11)
            ctx.set_source_rgb(0.1, 0.15, 0.2)
            text = str(val)
            ext = ctx.text_extents(text)
            ctx.move_to(cx + (cell_w - ext.width) / 2 - 1, cy + (cell_h + ext.height) / 2 - 1)
            ctx.show_text(text)

    # Legend
    legend_y = height - 40
    ctx.set_source_rgb(0.85, 0.95, 0.85)
    ctx.rectangle(margin_left, legend_y, 22, 16)
    ctx.fill()
    ctx.set_line_width(1.5)
    ctx.set_source_rgb(0.15, 0.65, 0.25)
    ctx.rectangle(margin_left, legend_y, 22, 16)
    ctx.stroke()

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(11)
    ctx.set_source_rgb(0.25, 0.3, 0.38)
    ctx.move_to(margin_left + 30, legend_y + 13)
    ctx.show_text("Optimal Knapsack Backtracked Decisions (Optimal Selection Path)")

    surface.write_to_png(output_path)


def draw_route_map(
    graph: Graph,
    route_result: RouteResult,
    output_path: str,
    width: int = 1000,
    height: int = 800
) -> None:
    """
    Renders a spatial 2D road map depicting vertices, road network links,
    and the optimized TSP delivery tour with sequential stop badges.
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Background
    ctx.set_source_rgb(0.97, 0.98, 0.99)
    ctx.paint()

    # Determine coordinate bounds
    all_nodes = [graph.nodes[n] for n in graph.get_nodes() if n in graph.nodes]
    if not all_nodes:
        return

    min_x = min(n.x for n in all_nodes)
    max_x = max(n.x for n in all_nodes)
    min_y = min(n.y for n in all_nodes)
    max_y = max(n.y for n in all_nodes)

    pad = 80
    span_x = max(1.0, max_x - min_x)
    span_y = max(1.0, max_y - min_y)

    def to_screen(gx: float, gy: float) -> Tuple[float, float]:
        sx = pad + ((gx - min_x) / span_x) * (width - 2 * pad)
        sy = height - pad - ((gy - min_y) / span_y) * (height - 2 * pad - 80)
        return sx, sy

    # Title
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22)
    ctx.set_source_rgb(0.12, 0.16, 0.25)
    ctx.move_to(50, 45)
    ctx.show_text("Phase 3: Road Network & 2-Opt Optimized TSP Delivery Route")

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(13)
    ctx.set_source_rgb(0.4, 0.45, 0.55)
    ctx.move_to(50, 72)
    ctx.show_text(f"Total Circuit Distance: {route_result.total_distance:.2f} km | Stops: {' -> '.join(route_result.ordered_stops)}")

    # 1. Draw all road network edges (background)
    ctx.set_line_width(1.5)
    ctx.set_source_rgba(0.75, 0.8, 0.88, 0.7)
    for edge in graph.get_edges():
        if edge.source in graph.nodes and edge.target in graph.nodes:
            u_pt = graph.nodes[edge.source]
            v_pt = graph.nodes[edge.target]
            ux, uy = to_screen(u_pt.x, u_pt.y)
            vx, vy = to_screen(v_pt.x, v_pt.y)
            ctx.move_to(ux, uy)
            ctx.line_to(vx, vy)
            ctx.stroke()

    # 2. Draw Active Detailed Route
    detailed = route_result.detailed_path
    if len(detailed) >= 2:
        ctx.set_line_width(4.0)
        ctx.set_source_rgba(0.18, 0.55, 0.95, 0.85)
        for i in range(len(detailed) - 1):
            u_name, v_name = detailed[i], detailed[i + 1]
            if u_name in graph.nodes and v_name in graph.nodes:
                ux, uy = to_screen(graph.nodes[u_name].x, graph.nodes[u_name].y)
                vx, vy = to_screen(graph.nodes[v_name].x, graph.nodes[v_name].y)
                ctx.move_to(ux, uy)
                ctx.line_to(vx, vy)
                ctx.stroke()

                # Direction Arrow halfway
                mx, my = (ux + vx) / 2.0, (uy + vy) / 2.0
                angle = math.atan2(vy - uy, vx - ux)
                arrow_len = 12.0
                ctx.move_to(mx, my)
                ctx.line_to(mx - arrow_len * math.cos(angle - 0.4), my - arrow_len * math.sin(angle - 0.4))
                ctx.line_to(mx - arrow_len * math.cos(angle + 0.4), my - arrow_len * math.sin(angle + 0.4))
                ctx.close_path()
                ctx.fill()

    # 3. Draw Nodes
    selected_stops_set = set(route_result.ordered_stops)

    for nid in graph.get_nodes():
        node = graph.nodes[nid]
        sx, sy = to_screen(node.x, node.y)

        if node.is_depot:
            # Depot: Gold star / large badge
            ctx.set_source_rgb(0.95, 0.65, 0.1)
            ctx.arc(sx, sy, 18, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_line_width(2.5)
            ctx.set_source_rgb(0.65, 0.4, 0.05)
            ctx.arc(sx, sy, 18, 0, 2 * math.pi)
            ctx.stroke()

            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(10)
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.move_to(sx - 16, sy + 3)
            ctx.show_text("DEPOT")

        elif nid in selected_stops_set:
            # Selected customer stop
            ctx.set_source_rgb(0.12, 0.72, 0.52)
            ctx.arc(sx, sy, 14, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_line_width(2.0)
            ctx.set_source_rgb(0.08, 0.45, 0.32)
            ctx.arc(sx, sy, 14, 0, 2 * math.pi)
            ctx.stroke()

            # Stop order badge
            stop_indices = [idx for idx, stop in enumerate(route_result.ordered_stops) if stop == nid]
            idx_str = str(stop_indices[0]) if stop_indices else ""
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(11)
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ext = ctx.text_extents(idx_str)
            ctx.move_to(sx - ext.width / 2, sy + ext.height / 2)
            ctx.show_text(idx_str)

            # Node label
            ctx.set_font_size(12)
            ctx.set_source_rgb(0.1, 0.15, 0.25)
            ctx.move_to(sx + 18, sy + 4)
            ctx.show_text(nid)

        else:
            # Transit / non-selected graph node
            ctx.set_source_rgb(0.8, 0.84, 0.9)
            ctx.arc(sx, sy, 6, 0, 2 * math.pi)
            ctx.fill()

    # Legend at bottom
    ly = height - 35
    # Depot
    ctx.set_source_rgb(0.95, 0.65, 0.1)
    ctx.arc(60, ly, 8, 0, 2 * math.pi)
    ctx.fill()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(12)
    ctx.set_source_rgb(0.2, 0.25, 0.35)
    ctx.move_to(76, ly + 4)
    ctx.show_text("Central Distribution Depot (Start / Finish)")

    # Delivery Stops
    ctx.set_source_rgb(0.12, 0.72, 0.52)
    ctx.arc(380, ly, 8, 0, 2 * math.pi)
    ctx.fill()
    ctx.move_to(396, ly + 4)
    ctx.show_text("Customer Delivery Stop (Numbered in Tour Order)")

    # Road Network
    ctx.set_line_width(3.0)
    ctx.set_source_rgb(0.18, 0.55, 0.95)
    ctx.move_to(730, ly)
    ctx.line_to(770, ly)
    ctx.stroke()
    ctx.move_to(780, ly + 4)
    ctx.show_text("Optimized Delivery Path")

    surface.write_to_png(output_path)


def draw_benchmark_charts(benchmark_data: Dict[str, Any], output_path: str, width: int = 1100, height: int = 650) -> None:
    """
    Renders multi-line scalability curves showing runtime vs problem scale for all algorithms.
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Background
    ctx.set_source_rgb(0.98, 0.99, 1.0)
    ctx.paint()

    # Title
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(0.12, 0.16, 0.26)
    ctx.move_to(60, 50)
    ctx.show_text("Phase 4: Algorithmic Runtime Performance & Scalability Analysis")

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(13)
    ctx.set_source_rgb(0.4, 0.45, 0.55)
    ctx.move_to(60, 78)
    ctx.show_text("Empirical execution time (ms) recorded across varying parcel counts and graph vertex dimensions.")

    # Plot area
    px = 100
    py = 130
    pw = 920
    ph = 430

    # White plot background
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.rectangle(px, py, pw, ph)
    ctx.fill()
    ctx.set_line_width(1.2)
    ctx.set_source_rgb(0.8, 0.85, 0.9)
    ctx.rectangle(px, py, pw, ph)
    ctx.stroke()

    sizes = benchmark_data["sizes"]
    n_pts = len(sizes)
    if n_pts < 2:
        return

    # Find max time across all series for Y-axis scale
    all_times = (
        benchmark_data.get("total_pipeline_times", []) +
        benchmark_data.get("knapsack_times", []) +
        benchmark_data.get("dijkstra_allpairs_times", []) +
        benchmark_data.get("tsp_times", []) +
        benchmark_data.get("mergesort_times", []) +
        benchmark_data.get("quicksort_times", [])
    )
    max_time = max(max(all_times, default=0.1), 0.1) * 1.15

    # Draw horizontal gridlines
    num_grid = 6
    ctx.set_line_width(0.7)
    for g in range(num_grid + 1):
        gy = py + ph - (g / num_grid) * ph
        val = (g / num_grid) * max_time
        ctx.set_source_rgba(0.85, 0.88, 0.92, 0.8)
        ctx.move_to(px, gy)
        ctx.line_to(px + pw, gy)
        ctx.stroke()

        # Y-axis label
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(11)
        ctx.set_source_rgb(0.4, 0.45, 0.5)
        lbl = f"{val:.1f} ms"
        ctx.move_to(px - 58, gy + 4)
        ctx.show_text(lbl)

    # X-axis step
    x_coords = [px + (i / (n_pts - 1)) * pw for i in range(n_pts)]

    # Draw X-axis labels
    for i, size_label in enumerate(sizes):
        cx = x_coords[i]
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(11)
        ctx.set_source_rgb(0.2, 0.25, 0.35)
        ext = ctx.text_extents(size_label)
        ctx.move_to(cx - ext.width / 2, py + ph + 24)
        ctx.show_text(size_label)

    # Series definitions
    series = [
        {"name": "Total Pipeline", "data": benchmark_data["total_pipeline_times"], "color": (0.85, 0.2, 0.3), "width": 3.0},
        {"name": "Knapsack 0/1 DP", "data": benchmark_data["knapsack_times"], "color": (0.9, 0.5, 0.1), "width": 2.2},
        {"name": "Dijkstra All-Pairs", "data": benchmark_data["dijkstra_allpairs_times"], "color": (0.55, 0.25, 0.85), "width": 2.2},
        {"name": "MergeSort", "data": benchmark_data["mergesort_times"], "color": (0.15, 0.65, 0.4), "width": 1.8},
        {"name": "TSP 2-Opt", "data": benchmark_data["tsp_times"], "color": (0.15, 0.5, 0.9), "width": 1.8},
    ]

    for s in series:
        r, g, b = s["color"]
        ctx.set_line_width(s["width"])
        ctx.set_source_rgb(r, g, b)

        pts = []
        for i, val in enumerate(s["data"]):
            cx = x_coords[i]
            cy = py + ph - (val / max_time) * ph
            pts.append((cx, cy))

        ctx.move_to(pts[0][0], pts[0][1])
        for pt in pts[1:]:
            ctx.line_to(pt[0], pt[1])
        ctx.stroke()

        # Data point markers
        for cx, cy in pts:
            ctx.arc(cx, cy, 4, 0, 2 * math.pi)
            ctx.fill()

    # Legend at bottom
    leg_x = px + 40
    leg_y = py + ph + 55
    for s in series:
        r, g, b = s["color"]
        ctx.set_line_width(s["width"])
        ctx.set_source_rgb(r, g, b)
        ctx.move_to(leg_x, leg_y)
        ctx.line_to(leg_x + 25, leg_y)
        ctx.stroke()
        ctx.arc(leg_x + 12.5, leg_y, 4, 0, 2 * math.pi)
        ctx.fill()

        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(11)
        ctx.set_source_rgb(0.2, 0.25, 0.35)
        ctx.move_to(leg_x + 32, leg_y + 4)
        ctx.show_text(s["name"])

        leg_x += 165

    surface.write_to_png(output_path)


def draw_console_showcase(
    summary_text: str,
    output_path: str,
    width: int = 1000,
    height: int = 700
) -> None:
    """
    Renders a clean terminal-themed screenshot card presenting the execution output.
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Outer background
    ctx.set_source_rgb(0.92, 0.94, 0.96)
    ctx.paint()

    # Terminal window
    tx = 40
    ty = 40
    tw = width - 80
    th = height - 80

    # Shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.12)
    ctx.rectangle(tx + 5, ty + 5, tw, th)
    ctx.fill()

    # Terminal Body
    ctx.set_source_rgb(0.1, 0.12, 0.16)
    ctx.rectangle(tx, ty, tw, th)
    ctx.fill()

    # Terminal Header Bar
    ctx.set_source_rgb(0.16, 0.18, 0.24)
    ctx.rectangle(tx, ty, tw, 36)
    ctx.fill()

    # Mac/Linux-style window buttons
    colors = [(0.95, 0.36, 0.35), (0.95, 0.73, 0.24), (0.33, 0.77, 0.42)]
    for i, col in enumerate(colors):
        ctx.set_source_rgb(*col)
        ctx.arc(tx + 22 + i * 20, ty + 18, 6, 0, 2 * math.pi)
        ctx.fill()

    # Terminal Window Title
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(12)
    ctx.set_source_rgb(0.7, 0.75, 0.85)
    ctx.move_to(tx + tw / 2 - 120, ty + 22)
    ctx.show_text("bash: python -m src.planner --demo (Console Trace)")

    # Output lines
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(12)
    ctx.set_source_rgb(0.85, 0.9, 0.95)

    curr_y = ty + 68
    for line in summary_text.strip().split("\n"):
        if curr_y > ty + th - 25:
            break
        if line.startswith("===") or line.startswith("---"):
            ctx.set_source_rgb(0.4, 0.55, 0.75)
        elif "SUCCESS" in line or "OPTIMAL" in line or "COMPLETED" in line:
            ctx.set_source_rgb(0.3, 0.85, 0.45)
        elif "Phase" in line:
            ctx.set_source_rgb(0.95, 0.75, 0.3)
        else:
            ctx.set_source_rgb(0.85, 0.9, 0.95)

        ctx.move_to(tx + 25, curr_y)
        ctx.show_text(line)
        curr_y += 20

    surface.write_to_png(output_path)
