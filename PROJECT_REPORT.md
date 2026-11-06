# Capstone Project Technical Report: Mini-Courier Planner
**Mapped Course Outcomes:** CO1, CO2, CO3, CO4, CO5 (Bloom's Taxonomy: L5 - Evaluate)  
**Total Marks:** 100  
**Project Title:** Mini-Courier Planner: An Algorithmic Dispatch and Route Optimization System  
**Submission Tag:** `v1.0-final-submission`  

---

## 1. Executive Summary & Problem Statement

### 1.1 Problem Statement
Modern logistics and courier networks face the simultaneous challenges of tight delivery deadlines, constrained vehicular payload capacities, volatile road distances, and increasing operational fuel costs. Given a batch of incoming parcels—each defined by a destination customer node, integer weight, priority level, and delivery deadline window—and a road network graph containing a centralized distribution depot and customer delivery addresses, the objective is to design, implement, and evaluate an automated **Mini-Courier Planner** prototype.

The solution must seamlessly synthesize four fundamental algorithmic paradigms:
1. **Divide-and-Conquer Sorting**: To prioritize and rank parcels fairly based on delivery urgency and business priority.
2. **Dynamic Programming (0/1 Knapsack)**: To determine the exact subset of parcels that maximizes cumulative delivery value without exceeding vehicle payload weight capacity.
3. **Graph Algorithms (Dijkstra's Shortest Path)**: To compute physical road network shortest-path distances and reconstruct turn-by-turn routes across intersections.
4. **Approximation Techniques (TSP Nearest-Neighbor with 2-Opt Local Search)**: To solve the NP-hard Travelling Salesperson Problem on the metric graph, producing a minimal-distance delivery tour starting and ending at the depot.

---

## 2. Phase 1: Courier Problem Design and Planning (20 Marks)

### 2.1 System Architecture & Algorithmic Workflow
The Mini-Courier Planner follows a strictly decoupled, modular pipeline where each phase consumes the validated output of the preceding phase:

```
+-----------------------------------------------------------------------------+
|                            PHASE 1: PROBLEM DESIGN                          |
|  - Define Parcel Entities: {ID, Weight, Priority, Deadline, Value, Dest}    |
|  - Define Road Network Graph: G = (V, E, c) with Euclidean/Road Distances   |
|  - Specify Vehicle Constraints: Payload Capacity W_max kg, Central Depot     |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                     PHASE 2A: PARCEL PRIORITIZATION (SORT)                  |
|  - Algorithm: Stable MergeSort vs Median-of-3 QuickSort                     |
|  - Multi-Key Criteria: (Deadline ASC, Priority DESC, Weight ASC)            |
|  - Output: Ranked parcel queue prioritizing urgent customer commitments     |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                     PHASE 2B: OPTIMAL BOX FILLING (KNAPSACK DP)             |
|  - Paradigm: 0/1 Knapsack Dynamic Programming with 2D Tabulation            |
|  - Objective: Maximize sum(Value) subject to sum(Weight) <= W_max           |
|  - Output: Optimal selected parcel set & rejected parcels + DP Matrix       |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                     PHASE 3A: GRAPH PROCESSING (DIJKSTRA)                   |
|  - Algorithm: Binary Min-Heap Priority Queue Dijkstra                       |
|  - Compute All-Pairs Metric Distance Matrix for {Depot} U {Selected Dests}  |
|  - Reconstruct Turn-by-Turn Predecessor Pointers                            |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                     PHASE 3B: ROUTE MAKER (TSP APPROXIMATION)               |
|  - Algorithm: Greedy Nearest-Neighbor Tour Construction                     |
|  - Local Search: 2-Opt Edge-Crossing Elimination Heuristic                  |
|  - Output: Ordered delivery stops, total circuit distance, turn-by-turn map |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                     PHASE 4: BENCHMARKING & EMPIRICAL COMPLEXITY            |
|  - Profile runtimes across N = [10, 50, 100, 200, 400] and |V| = [8..75]    |
|  - Theoretical vs Empirical Big-O analysis & optimization suggestions       |
+-----------------------------------------------------------------------------+
```

### 2.2 Entity Modeling & Data Structures
- **`Parcel`**: Dataclass holding `parcel_id` (str), `destination` (str), `weight` (int, kg), `priority` (int, 1-5), `deadline` (float, hours), and computed `value` (int).  
  *Value Formula:*
  $$v_i = \text{priority}_i \times 15 + \max(0, \lfloor (12 - \min(d_i, 12)) \times 2 \rfloor)$$
  This guarantees that emergency items (priority 5, deadline 1 hour) carry peak objective importance.
- **`DeliveryPoint`**: Geographical vertex with Cartesian coordinates $(x, y)$, name, and `is_depot` flag.
- **`RoadEdge`**: Bidirectional or directed roadway segment with real-valued distance/time weight $c(u, v) > 0$.
- **`Graph`**: Adjacency list representation `Dict[str, List[Tuple[str, float]]]`, allowing $O(1)$ vertex lookup and $O(\text{deg}(u))$ edge traversal.

---

## 3. Phase 2: Package Prioritization and Box Filling (20 Marks)

### 3.1 Package Prioritization (Sorting)
Delivery fairness requires that parcels with immediate deadlines be served first. However, when deadlines match, higher priority parcels take precedence; if both match, lighter packages break ties to preserve vehicle capacity.

We implemented and analyzed two classical sorting algorithms:
1. **MergeSort**:
   - Time Complexity: $O(N \log N)$ across Best, Average, and Worst cases.
   - Auxiliary Space: $O(N)$.
   - **Stability**: Formally guaranteed ($\le$ merge predicate preserves initial submission sequence for parcels with identical keys).
2. **QuickSort**:
   - Time Complexity: $O(N \log N)$ average, mitigated against $O(N^2)$ worst-case using **Median-of-Three** pivot selection.
   - Auxiliary Space: $O(\log N)$ recursive call stack.
   - 3-Way Partitioning (Dutch National Flag) ensures efficient processing when many parcels have identical priority values.

*Justification:* **MergeSort** was chosen as the primary production sorting algorithm because algorithmic stability is crucial for customer service level agreements (FIFO within equal priority tiers).

### 3.2 Optimal Box Filling (0/1 Knapsack Dynamic Programming)
Vehicles have a hard payload weight limit $W$ (e.g. 40 kg). Fractional knapsack (greedy by $v_i / w_i$) is invalid because physical packages cannot be cleaved. The problem is NP-complete. We solve it via Dynamic Programming:

**Mathematical Recurrence:**
$$DP[i][w] = \begin{cases} DP[i-1][w] & \text{if } w_i > w \\ \max(DP[i-1][w], DP[i-1][w - w_i] + v_i) & \text{if } w_i \le w \end{cases}$$
Base cases: $DP[0][w] = 0$ for all $w \in [0, W]$, $DP[i][0] = 0$ for all $i \in [0, n]$.

**Item Reconstruction (Backtracking):**
```python
w_curr = W
selected = []
for i in range(n, 0, -1):
    if DP[i][w_curr] != DP[i-1][w_curr]:
        selected.append(parcels[i-1])
        w_curr -= parcels[i-1].weight
```

**Experimental Demonstration (Capacity $W = 40$ kg):**
- Candidate Parcels: 10 items (Total weight: 89 kg)
- Selected by DP: `['P105', 'P102', 'P101', 'P110', 'P103']` (5 parcels)
- Cumulative Packed Weight: **40 kg / 40 kg (100.0% vehicle capacity utilization)**
- Total Objective Value: **395 points**
- Rejected Parcels: `['P106', 'P108', 'P107', 'P104', 'P109']` (queued for subsequent dispatch)

---

## 4. Phase 3: Route Maker and Graph Processing (20 Marks)

### 4.1 Shortest Path Calculation (Dijkstra's Algorithm)
Road networks rarely possess straight-line connections between all customer pairs. To construct a metric space for TSP, we compute all-pairs shortest paths among $\\{\text{Depot}\\} \cup \\{\text{selected destinations}\\}$:
- Implementation: Min-Heap (`heapq`) based Dijkstra.
- Time Complexity: $O((|V| + |E|) \log |V|)$ per source.
- Predecessors table stores the predecessor pointer `predecessor[v] = u` enabling full reconstruction of intermediate waypoint navigation.

### 4.2 Overall Delivery Route (Nearest-Neighbor TSP + 2-Opt Local Search)
With the metric distance matrix $D[u][v]$ computed:
1. **Greedy Nearest-Neighbor Heuristic**:
   - Start at `Depot`.
   - Iteratively select $v^* = \arg\min_{v \in U} D[u][v]$ where $U$ is the set of unvisited stops.
   - Return to `Depot` once $U = \emptyset$.
   - Time Complexity: $O(K^2)$ where $K$ is the number of delivery locations.
2. **2-Opt Local Search Optimization**:
   - Inspects pairs of non-adjacent edges $(i, i+1)$ and $(j, j+1)$.
   - If reversing segment $i+1 \dots j$ reduces total tour mileage ($D[i][j] + D[i+1][j+1] < D[i][i+1] + D[j][j+1]$), the sub-tour is reversed.
   - Eliminates self-intersecting loops and crossings, producing a 2-optimal circuit.

**Demonstration Route Outcome:**
- Ordered Delivery Tour: `Depot -> C3 -> C2 -> C5 -> C1 -> Depot`
- Total Mileage: **170.78 km**
- Leg Breakdown:
  - `Depot -> C3`: 26.56 km
  - `C3 -> C2`: 58.23 km
  - `C2 -> C5`: 21.86 km
  - `C5 -> C1`: 19.58 km
  - `C1 -> Depot`: 44.55 km

---

## 5. Phase 4: Performance Testing and Optimization (20 Marks)

### 5.1 Empirical Runtime Measurements
We conducted comprehensive scalability benchmarks across five escalating problem dimensions. Each trial recorded the component-level execution time in milliseconds:

| Dataset Scale | Parcel Count ($N$) | Road Nodes ($|V|$) | MergeSort (ms) | QuickSort (ms) | Knapsack DP (ms) | Dijkstra All-Pairs (ms) | Fast 2-Opt TSP (ms) | Total Pipeline (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Small** | 10 | 8 | 0.032 | 0.033 | 0.163 | 0.287 | 0.116 | **0.598 ms** |
| **Medium** | 50 | 20 | 0.159 | 0.124 | 2.283 | 1.838 | 1.272 | **5.552 ms** |
| **Large** | 100 | 35 | 0.342 | 0.268 | 12.639 | 5.464 | 2.570 | **21.016 ms** |
| **Very Large** | 200 | 50 | 0.719 | 0.552 | 42.906 | 14.170 | 14.997 | **72.792 ms** |
| **Stress** | 400 | 75 | 1.636 | 1.576 | 178.848 | 32.256 | 40.832 | **253.572 ms** |

### 5.2 Computational Complexity Analysis
1. **Sorting ($O(N \log N)$)**: Scales logarithmically; both MergeSort and QuickSort execute in under 2 ms even for 400 parcels.
2. **0/1 Knapsack DP ($O(N \cdot W)$)**: Exhibits predictable pseudo-polynomial scaling. When $N=400$ and $W=1800$, table tabulation evaluates $7.2 \times 10^5$ cells in 178.85 ms.
3. **Dijkstra ($O(K \cdot (|V| + |E|) \log |V|)$)**: Scales smoothly with graph size due to the $O(\log |V|)$ efficiency of the binary min-heap.
4. **Fast 2-Opt TSP ($O(I \cdot K^2)$)**: With $O(1)$ symmetric delta evaluation, local search runtime dropped from over 900 ms down to 40 ms at scale, preventing routing from bottlenecking the pipeline.

### 5.3 Optimization Strategies for Production Environments
- **$O(1)$ Symmetric Delta 2-Opt Evaluation**: Rather than reconstructing candidate tours and recalculating full tour lengths $O(K)$ inside the $O(K^2)$ inner loop (which degraded performance to $O(I \cdot K^3)$), we evaluate the delta $\Delta = (d(u_{i-1}, v_j) + d(u_i, v_{j+1})) - (d(u_{i-1}, u_i) + d(v_j, v_{j+1}))$ in $O(1)$ time for symmetric road metrics.
- **Space-Optimized 1D Knapsack DP**: In `src/knapsack.py`, we implemented `knapsack_01_space_optimized` which compresses memory consumption from $O(N \cdot W)$ to $O(W)$ by updating a 1D array from right to left ($W \to w_i$).
- **Bounding 2-Opt Moves (k-d Tree Pruning)**: Rather than evaluating all $O(K^2)$ edge pairs during 2-Opt local search, candidate swaps can be restricted to the $k$ nearest neighbors of each node, reducing search time to $O(k \cdot K)$.
- **A* Search with Euclidean Landmark Heuristics**: For continent-scale graphs ($|V| > 10^5$), goal-directed A* routing bypasses irrelevant nodes and achieves up to a $50\times$ speedup over standard Dijkstra.

---

## 6. Phase 5: Deliverables, Artifacts, and Demonstration (20 Marks)

### 6.1 Generated Visual Artifacts (Available in `images/`)
1. **`images/system_architecture.png`**: High-resolution workflow flowchart detailing entity schemas, algorithmic transitions, and data pipelines across all 5 phases.
2. **`images/knapsack_dp_matrix.png`**: Color-coded decision table visualization of $DP[i][w]$ showing cell value progression and the highlighted optimal backtracking path.
3. **`images/delivery_route_visualization.png`**: 2D cartesian road map featuring the distribution depot, customer locations, background street network, and the directed 2-Opt delivery tour with numbered stop badges.
4. **`images/runtime_comparison.png`**: Multi-line performance benchmark curves depicting empirical runtimes vs input scale across all algorithms.
5. **`images/console_output_demo.png`**: Terminal showcase card illustrating execution outputs.

### 6.2 Test Suite Verification Record
All 39 unit and integration test cases pass cleanly under Python's `unittest` framework:
- `tests/test_sorting.py` (8 tests): Verifies MergeSort and QuickSort correctness, stability, reverse ordering, edge cases (empty, single element, duplicates), and multi-key parcel prioritization.
- `tests/test_knapsack.py` (10 tests): Validates 0/1 Knapsack DP optimality, zero capacity, negative capacity rejection, negative weight rejection, invalid priority/deadline boundaries, 1D space optimization, and table formatting.
- `tests/test_graph.py` (8 tests): Validates graph creation, non-negative edge weight enforcement, Dijkstra shortest distances, predecessor path reconstruction, disconnected graphs (empty path verification), same-node paths, and serialization.
- `tests/test_routing.py` (6 tests): Validates Nearest-Neighbor tour cycle, 2-Opt crossover elimination, tour length calculation, empty/depot-only routes, and roadway waypoint expansion.
- `tests/test_planner.py` (7 tests): Validates end-to-end integration, unreachable destination detection, non-existent destination rejection, negative capacity rejection, empty parcel handling, zero capacity dispatching, and runtime breakdown profiling.

---

## 7. Conclusion & Future Scope

### 7.1 Conclusion
The **Mini-Courier Planner** successfully achieves all learning outcomes (CO1 through CO5):
- Synthesized multiple core algorithmic paradigms (sorting, dynamic programming, priority queues, local search).
- Engineered a robust, modular Python codebase accompanied by rigorous unit tests and benchmark datasets.
- Demonstrated exact mathematical optimality in cargo loading (100% capacity utilization, 395 value points) and approximate optimality in delivery routing (170.78 km).

### 7.2 Future Scope
1. **Multi-Vehicle Fleet Routing (CVRP)**: Extending the single-vehicle knapsack and TSP to Capacitated Vehicle Routing with multiple couriers using Clark-Wright Savings or Genetic Algorithms.
2. **Time Windows (VRPTW)**: Incorporating strict arrival time intervals at customer addresses and penalty costs for late arrivals.
3. **Dynamic Real-Time Re-routing**: Integrating live traffic API streams to update road edge weights dynamically via incremental shortest-path algorithms (D* Lite).

---
*End of Technical Report — Tagged as `v1.0-final-submission`.*
