#!/usr/bin/env python3
"""
Launcher script for the Mini-Courier Planner Interactive Web Frontend.
Starts the embedded high-performance Python server and opens the dashboard in your default browser.
"""

import sys
import os
import socket
import argparse
import webbrowser
import threading
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import create_server, ensure_datasets


def find_available_port(host: str, start_port: int, max_attempts: int = 20) -> int:
    """Finds an available TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    return start_port


def print_banner(host: str, port: int):
    url = f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}"
    banner = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   MINI-COURIER PLANNER WEB DASHBOARD                          ║
║            Intelligent Multi-Criteria Parcel Dispatch & TSP Routing           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  ▶ Local Web UI:         {url}
  ▶ REST API Base:        {url}/api/health
  ▶ Datasets Catalog:     {url}/api/datasets
  ▶ Optimizer Endpoint:   {url}/api/plan

  Interactive Features Available in Dashboard:
  -----------------------------------------------------------------------------
  [✓] Live Vehicle Payload Slider with Real-time 0/1 Knapsack DP Solve
  [✓] Interactive Dynamic Programming Matrix with Backtracking Cell Trace
  [✓] Road Network Canvas with Animated Courier Van Delivery Simulation
  [✓] Multi-Criteria Sorting Benchmark (MergeSort vs QuickSort vs Timsort)
  [✓] 2-Opt vs Nearest-Neighbor TSP Route Optimization & Savings Analysis
  [✓] Custom Parcel Management & Turn-by-Turn Delivery Manifest Export

  Press CTRL+C in this terminal anytime to stop the server.
═════════════════════════════════════════════════════════════════════════════════
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(description="Mini-Courier Planner Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Initial port to bind (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    ensure_datasets()
    port = find_available_port(args.host, args.port)
    server = create_server(host=args.host, port=port)
    print_banner(args.host, port)

    url = f"http://{'localhost' if args.host in ('0.0.0.0', '127.0.0.1') else args.host}:{port}"
    if not args.no_browser:
        def open_browser():
            time.sleep(0.7)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MiniCourier] Server stopped by user. Goodbye!")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
