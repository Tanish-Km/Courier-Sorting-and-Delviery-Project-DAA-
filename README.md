# Mini-Courier Planner 🚚📦

> **Capstone Assignment: Mini-Courier Planner (B. Tech)**  
> **Course Outcomes Mapped:** CO1, CO2, CO3, CO4, CO5 (Bloom's Taxonomy: L5 - Evaluate)  
> **Total Marks:** 100  
> **Release Tag:** `v1.0-final-submission`

---

## 📖 Overview

The **Mini-Courier Planner** is an intelligent automated logistics prototype that models, optimizes, and simulates courier package prioritization, vehicle loading, and delivery routing. Given a collection of candidate parcels and a physical road network of a city, the system combines four foundational algorithmic paradigms:

1. **Parcel Prioritization & Sorting (Phase 2A)**: Multi-criteria sorting using **MergeSort** (guaranteed $O(N \log N)$ and stable) and **QuickSort** (with median-of-three pivot selection).
2. **Optimal Box Filling (Phase 2B)**: Solves the **0/1 Knapsack Problem** via **Dynamic Programming** to maximize cumulative delivered parcel value under vehicle payload capacity limits.
3. **Road Network Shortest Paths (Phase 3A)**: Uses **Dijkstra's Algorithm** with a binary min-heap priority queue to determine true shortest-path distances and turn-by-turn road waypoints.
4. **Delivery Route Optimization (Phase 3B)**: Solves the **Travelling Salesperson Problem (TSP)** using a **Greedy Nearest-Neighbor heuristic** paired with **2-Opt local search optimization** to eliminate route crossovers.
5. **Scalability & Performance Benchmarking (Phase 4)**: Empirical runtime profiling and Big-O computational complexity analysis across varying input sizes.

---

## 🗂️ Project Repository Structure

```
.
├── README.md                      # Project overview, installation, usage, and design
├── PROJECT_REPORT.md              # Comprehensive 100-mark Capstone Technical Project Report
├── mini_courier_planner.ipynb     # Complete interactive Jupyter Notebook implementation
├── requirements.txt               # Project Python package dependencies
├── .gitignore                     # Git ignore rules for virtualenvs, caches, and checkpoints
├── run_demo.py                    # One-command demonstration executable
├── run_web.py                     # Interactive Web Dashboard launcher
├── web/                           # Modern responsive Single-Page Application (SPA)
│   ├── index.html                 # Semantic HTML5 layout with dark/light themes
│   ├── styles.css                 # Logistics dashboard styling, glassmorphism, responsive grid
│   └── app.js                     # State management, Canvas route renderer, animated van, DP inspector
├── src/                           # Modular Python source package
│   ├── __init__.py                # Package initialization and exports
│   ├── models.py                  # Parcel, DeliveryPoint, RoadEdge, and Result data models
│   ├── sorting.py                 # MergeSort, QuickSort, and multi-key parcel prioritization
│   ├── knapsack.py                # 0/1 Knapsack DP solver, backtracking, and 1D space optimization
│   ├── graph.py                   # Adjacency list Graph representation and Dijkstra's algorithm
│   ├── routing.py                 # Nearest-Neighbor TSP heuristic and 2-Opt local search
│   ├── planner.py                 # Integrated MiniCourierPlanner pipeline orchestrator
│   ├── benchmark.py               # Scalability benchmarking suite across problem dimensions
│   ├── visualization.py           # Publication-quality PyCairo visualization rendering
│   ├── server.py                  # REST API & static web server (zero external dependencies)
│   └── main.py                    # Command-line interface (CLI) for running simulations
├── datasets/                      # Benchmark datasets for parcel batches and road networks
│   ├── small_parcels.csv          # 10 parcels for demonstration and manual validation
│   ├── small_graph.json           # 8-node connected city road network
│   ├── medium_parcels.csv         # 50 parcels
│   ├── medium_graph.json          # 25-node road network
│   ├── large_parcels.csv          # 200 parcels
│   └── large_graph.json           # 60-node road network
├── images/                        # Generated diagrams, charts, and execution cards
│   ├── system_architecture.png    # System architecture and algorithmic pipeline flowchart
│   ├── knapsack_dp_matrix.png     # Heatmap visualization of the 0/1 Knapsack DP decision matrix
│   ├── delivery_route_visualization.png # 2D road map depicting vertices and 2-Opt delivery tour
│   ├── runtime_comparison.png     # Scalability curves comparing algorithm runtimes vs scale
│   └── console_output_demo.png    # Terminal execution trace demonstration card
└── tests/                         # Comprehensive automated test suite
    ├── __init__.py
    ├── test_sorting.py            # Unit tests for MergeSort, QuickSort, and priority keys
    ├── test_knapsack.py           # Unit tests for 0/1 Knapsack DP optimality and edge cases
    ├── test_graph.py              # Unit tests for Graph modeling and Dijkstra's shortest paths
    ├── test_routing.py            # Unit tests for TSP tour validity, 2-Opt, and route expansion
    ├── test_planner.py            # End-to-end integration tests for MiniCourierPlanner
    └── test_server.py             # Integration tests for REST API endpoints and static assets
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository_url>
cd "Clg Projects"
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Execution & Usage

### 1. Run Complete Demonstration (One Command)
Runs the end-to-end pipeline on sample datasets, logs execution metrics, and exports all visual diagrams to `images/`:
```bash
python run_demo.py
```
*or via the CLI:*
```bash
python -m src.main --demo --capacity 40
```

### 2. Launch Interactive Web Dashboard (GUI)
Starts the embedded high-performance Python web server and opens the modern responsive dashboard in your browser:
```bash
python run_web.py
```
*Options:*
- `--port 8080`: Custom TCP port (auto-detects next available port if busy).
- `--host 0.0.0.0`: Bind to all interfaces for LAN/remote access.
- `--no-browser`: Start server without opening browser automatically.

**Dashboard Features:**
- **Dynamic Vehicle Payload Slider**: Adjust capacity in real time (5 to 150+ kg) with instant 0/1 Knapsack DP recomputation.
- **Interactive DP Matrix Inspector**: Tabular $DP[i][w]$ visualizer with dynamic column windowing for large capacities, glowing optimal backtracking path overlay, and step-by-step recurrence breakdown.
- **Road Network Canvas**: Pan/zoom vector map with node inspector and animated courier delivery van simulation along the 2-Opt route.
- **Dispatch Manifest & Itinerary**: Filterable selected/rejected package table and turn-by-turn ETA delivery timeline.
- **Custom Dataset & Import Suite**: Add custom parcels, generate random batches, and import custom parcels via CSV or road networks via JSON.
- **Live Algorithm Benchmarks**: Compare DP vs Greedy heuristic optimality gap, 2-Opt vs Nearest-Neighbor mileage savings, and MergeSort vs QuickSort sorting trials.
- **Export Options**: One-click download of dispatch manifests in JSON and CSV, driver delivery itinerary CSV, vector SVG route maps, and print-ready reports.

### 3. Run Interactive Jupyter Notebook
Launch the notebook containing complete mathematical formulations, code blocks, output traces, and embedded visualizations:
```bash
jupyter notebook mini_courier_planner.ipynb
```

### 4. Run Automated Test Suite
Execute all 58 unit and integration test cases covering the entire algorithm stack and web server API:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 5. Git Submission & Final Tagging
To push and tag your final submission repository commit:
```bash
git add .
git commit -m "Complete Mini-Courier Planner Capstone Implementation"
git tag -a v1.0-final-submission -m "v1.0-final-submission release"
git push origin master --tags
```

---

## 📊 Summary of Results & Algorithmic Benchmarks

### Demonstration Output (Vehicle Capacity $W = 40$ kg)
- **Candidate Parcels**: 10 parcels (total weight: 89 kg)
- **Prioritization**: Ranked by `(Deadline ASC, Priority DESC, Weight ASC)` using stable MergeSort.
- **Knapsack DP Box-Filling**:
  - Selected 5 parcels: `P105, P102, P101, P110, P103`
  - Total packed weight: **40 kg / 40 kg (100.0% capacity utilization)**
  - Total delivery value: **395 points**
- **Dijkstra & Fast 2-Opt TSP Route**:
  - Stops: `Depot -> C3 -> C2 -> C5 -> C1 -> Depot`
  - Total circuit distance: **170.78 km**
  - Execution runtime: **0.598 ms**

### Scalability Benchmarking Table
| Dataset Scale | Parcels ($N$) | Nodes ($|V|$) | MergeSort | QuickSort | Knapsack DP | Dijkstra | Fast 2-Opt TSP | Total Pipeline |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Small** | 10 | 8 | 0.032 ms | 0.033 ms | 0.163 ms | 0.287 ms | 0.116 ms | **0.598 ms** |
| **Medium** | 50 | 20 | 0.159 ms | 0.124 ms | 2.283 ms | 1.838 ms | 1.272 ms | **5.552 ms** |
| **Large** | 100 | 35 | 0.342 ms | 0.268 ms | 12.639 ms | 5.464 ms | 2.570 ms | **21.016 ms** |
| **Very Large** | 200 | 50 | 0.719 ms | 0.552 ms | 42.906 ms | 14.170 ms | 14.997 ms | **72.792 ms** |
| **Stress** | 400 | 75 | 1.636 ms | 1.576 ms | 178.848 ms | 32.256 ms | 40.832 ms | **253.572 ms** |

---

## 🖼️ Visualizations & Diagrams

All diagrams are automatically generated and saved to the `images/` folder:
- **`images/system_architecture.png`**: High-resolution architecture flowchart of all 5 phases.
- **`images/knapsack_dp_matrix.png`**: Tabular heatmap of the 0/1 Knapsack decision table.
- **`images/delivery_route_visualization.png`**: 2D cartesian road map and 2-Opt delivery tour.
- **`images/runtime_comparison.png`**: Multi-line performance benchmark curves.
- **`images/console_output_demo.png`**: Terminal showcase card illustrating execution outputs.

---

## 👥 Authors & Academic Context
- **Project**: Mini-Courier Planner Capstone Assignment
- **Degree**: B. Tech in Computer Science & Engineering
- **Evaluation Criteria**: Problem design, parcel prioritization, knapsack box-filling, Dijkstra shortest paths, TSP nearest-neighbor approximation, runtime benchmarking, documentation quality, and originality.
