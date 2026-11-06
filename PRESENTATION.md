# Mini-Courier Planner: Capstone Project Defense
**Course Outcome Mapping**: CO1, CO2, CO3, CO4, CO5 (Bloom Level: L5 - Evaluate)  
**Total Marks**: 100 | **Candidate Submission**: B. Tech Capstone Assignment

---

## Slide 1: Title & Executive Overview
- **Project**: Mini-Courier Planner (Intelligent Dispatch & Route Optimization)
- **Problem Context**: Modern last-mile courier delivery involves two conflicting optimization problems:
  1. *Payload Optimization*: Selecting high-priority packages without violating courier vehicle weight limits.
  2. *Route Minimization*: Finding the shortest feasible roadway sequence to minimize transit time, fuel consumption, and delivery delay.
- **Solution Architecture**: An end-to-end Python pipeline combining Multi-Criteria Sorting, 0/1 Knapsack Dynamic Programming, Dijkstra's All-Pairs Shortest Path, and Nearest-Neighbor TSP with 2-Opt local search refinement.

---

## Slide 2: Phase 1 — System Design & Problem Modeling (CO1 / CO2)
- **Mathematical Formulations**:
  - Parcels: $P_i = \langle \text{id}_i, \text{dest}_i, w_i, p_i, d_i, v_i \rangle$, where $w_i \in \mathbb{N}^+$, $p_i \in \{1 \dots 5\}$, $d_i \in \mathbb{R}^+$, $v_i = p_i \times 20 - d_i$.
  - Road Network: Weighted directed/undirected graph $G = (V, E, W)$ with Euclidean spatial coordinates.
- **Pipeline Flow**:
  $$\text{Raw Parcels} \xrightarrow[\text{MergeSort}]{\text{Prioritize}} \text{Ranked Queue} \xrightarrow[\text{0/1 Knapsack}]{\text{Capacity } W} \text{Selected Parcels} \xrightarrow[\text{Dijkstra}]{\text{Metric Distances}} \text{Distance Matrix} \xrightarrow[\text{TSP 2-Opt}]{\text{Routing}} \text{Optimal Tour}$$
- **Visual Evidence**: Refer to `images/system_architecture.png`.

---

## Slide 3: Phase 2A — Package Prioritization & Sorting (CO1 / CO2)
- **Algorithm Selection**: Stable **Merge Sort** vs. **Quick Sort**.
- **Sorting Logic**:
  - Primary Key: Earliest Delivery Deadline ($d_i$ ascending).
  - Secondary Key: Highest Urgency Priority ($p_i$ descending).
- **Why Stability Matters**:
  - If two packages share identical deadlines, Merge Sort preserves relative input order (preventing starvation).
- **Time Complexity**: $O(N \log N)$ worst-case guarantee; Space: $O(N)$.

---

## Slide 4: Phase 2B — Box Filling via 0/1 Knapsack DP (CO1 / CO3)
- **Bellman Recurrence Relation**:
  $$\text{DP}[i][w] = \begin{cases} \text{DP}[i-1][w] & \text{if } w_i > w \\ \max(\text{DP}[i-1][w], \text{DP}[i-1][w - w_i] + v_i) & \text{if } w_i \le w \end{cases}$$
- **Greedy vs. DP Proof**:
  - Naive Greedy Selection ($v_i / w_i$): Achieves only **217 value points** (leaves dead capacity).
  - Exact Dynamic Programming: Achieves **395 value points** (100% capacity utilization: 40/40 kg).
- **Visual Evidence**: Refer to `images/knapsack_dp_matrix.png` showing the state transition table and backtrack path.

---

## Slide 5: Phase 3A — Road Network Graph & Shortest Paths (CO1 / CO3)
- **Data Structure**: Sparse Adjacency List `dict[str, list[Edge]]`.
- **Dijkstra's Algorithm (Min-Heap)**:
  - Finds true metric shortest paths across planar road coordinates.
  - Generates the customer distance matrix $D_{K \times K}$ between all loaded delivery destinations and the Depot.
- **Time Complexity**: $O((V + E) \log V)$ per source; total all-pairs metric generation in $O(K(V + E) \log V)$.

---

## Slide 6: Phase 3B — TSP Tour Construction & 2-Opt Local Search (CO1 / CO4)
- **Two-Stage Approximation**:
  1. **Nearest-Neighbor (NN) Heuristic**: Fast greedy tour generation ($O(K^2)$).
  2. **2-Opt Optimization**: Iteratively eliminates crossing paths by evaluating tour modifications:
     $$\Delta = \big(d(u_{i-1}, v_j) + d(u_i, v_{j+1})\big) - \big(d(u_{i-1}, u_i) + d(v_j, v_{j+1})\big)$$
- **Optimization Breakthrough**:
  - Subagent optimized delta evaluation to $O(1)$, reducing 2-Opt runtime from **928 ms down to 42 ms** at $N=400$ stops.
- **Computed Delivery Tour**:
  $$\text{Depot} \to \text{C3} \to \text{C2} \to \text{C5} \to \text{C1} \to \text{Depot} \quad (170.78\text{ km})$$
- **Visual Evidence**: Refer to `images/delivery_route_visualization.png`.

---

## Slide 7: Phase 4 — Scalability Benchmarking & Performance (CO4 / CO5)
- **Experimental Setup**: Tested across 5 scales ($N=10$ to $N=400$ parcels, $|V|=8$ to $|V|=75$ road nodes).
- **Empirical Runtime Observations**:
  - $N=10, |V|=8$: $0.53\text{ ms}$
  - $N=50, |V|=20$: $4.42\text{ ms}$
  - $N=100, |V|=35$: $23.98\text{ ms}$
  - $N=400, |V|=75$: $260.09\text{ ms}$
- **Scalability Finding**: Knapsack DP scales linearly with parcel count $N$ for fixed capacity $W$. Dijkstra and 2-Opt dominate at scale but complete in well under 300 ms, proving real-time feasibility.
- **Visual Evidence**: Refer to `images/runtime_comparison.png`.

---

## Slide 8: Phase 5 — Quality Assurance & Testing Rigor (CO5)
- **Unit Test Suite**: 39 comprehensive tests covering:
  - Disconnected node path reconstruction ($[]$ rather than erroneous singleton).
  - Negative edge weight, negative capacity, and negative weight input rejections.
  - Unreachable destination topological validation during Phase 1.
  - Property testing verifying 2D DP matrix vs. 1D space-optimized equivalence.
- **Test Results**: 100% pass rate in **0.007s**.

---

## Slide 9: Future Enhancements & Production Roadmap
- Capacitated Multi-Vehicle Routing Problem (CVRP) with fleet dispatching.
- Time-Window Constrained Routing (VRPTW).
- Real-time dynamic re-routing with live traffic updates.
- Genetic Algorithms and Ant Colony Optimization for massive $K > 1000$ stop delivery networks.

---

## Slide 10: Conclusion & Submission Checklist
- All requirements of the 100-mark Capstone Rubric (CO1 to CO5) have been fulfilled.
- Artifacts generated:
  - `Mini_Courier_Planner_Submission.zip` (clean submission bundle ready for LMS upload)
  - `README.md` & `PROJECT_REPORT.md`
  - `mini_courier_planner.ipynb` (executable Jupyter Notebook)
  - `src/` modular source package
  - `datasets/` & `images/`
- Git Tag: `v1.0-final-submission`

