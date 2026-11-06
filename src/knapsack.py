"""
0/1 Knapsack Dynamic Programming solver for optimal parcel box-filling and vehicle loading.
"""

from typing import List, Tuple, Dict, Any
import time
from .models import Parcel, PackingResult


def knapsack_01_dp(parcels: List[Parcel], capacity: int) -> PackingResult:
    """
    Solves the 0/1 Knapsack problem using Dynamic Programming with full table tabulation.
    
    Mathematical Formulation:
      Let DP[i][w] represent the maximum total delivery value achievable using a
      subset of the first i parcels with total cumulative weight at most w kg.
      
      Recurrence:
        DP[i][w] = DP[i-1][w]                                    if w_i > w
        DP[i][w] = max(DP[i-1][w], DP[i-1][w - w_i] + v_i)        if w_i <= w
        
      Base Cases:
        DP[0][w] = 0 for all w in [0, capacity]
        DP[i][0] = 0 for all i in [0, n]
        
    Complexity:
      Time Complexity:  O(N * W) pseudo-polynomial
      Space Complexity: O(N * W) auxiliary matrix
      
    Args:
        parcels: Candidate list of parcels.
        capacity: Maximum payload weight capacity of the delivery vehicle.
        
    Returns:
        PackingResult containing selected parcels, rejected parcels, total weight,
        total value, the complete DP matrix, and runtime in milliseconds.
    """
    if capacity < 0:
        raise ValueError(f"Vehicle capacity cannot be negative: {capacity}")

    start_time = time.perf_counter()
    n = len(parcels)
    W = int(capacity)

    for p in parcels:
        if p.weight < 0:
            raise ValueError(f"Parcel weight cannot be negative: {p.weight}")

    # Allocate (N + 1) x (W + 1) table initialized to 0
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    # Dynamic Programming Tabulation
    for i in range(1, n + 1):
        p = parcels[i - 1]
        w_i = p.weight
        v_i = p.value

        for w in range(W + 1):
            if w_i <= w:
                include_val = dp[i - 1][w - w_i] + v_i
                exclude_val = dp[i - 1][w]
                dp[i][w] = include_val if include_val > exclude_val else exclude_val
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtracking to reconstruct the exact set of selected items
    selected_indices = []
    w_curr = W
    for i in range(n, 0, -1):
        if dp[i][w_curr] != dp[i - 1][w_curr]:
            # Parcel i-1 was included in the optimal knapsack
            selected_indices.append(i - 1)
            w_curr -= parcels[i - 1].weight

    selected_indices.reverse()
    selected_set = set(selected_indices)

    selected_parcels = [parcels[i] for i in selected_indices]
    rejected_parcels = [parcels[i] for i in range(n) if i not in selected_set]

    total_weight = sum(p.weight for p in selected_parcels)
    total_value = dp[n][W]
    runtime_ms = (time.perf_counter() - start_time) * 1000.0

    return PackingResult(
        selected_parcels=selected_parcels,
        rejected_parcels=rejected_parcels,
        total_weight=total_weight,
        total_value=total_value,
        capacity=capacity,
        dp_table=dp,
        runtime_ms=runtime_ms,
    )


def knapsack_01_space_optimized(parcels: List[Parcel], capacity: int) -> Tuple[int, List[Parcel]]:
    """
    Space-optimized 0/1 Knapsack DP utilizing a single 1D array of size (W + 1).
    Demonstrates O(W) auxiliary space optimization for Phase 4 performance enhancements.
    
    Note: To reconstruct items in 1D DP, bitmasks or boolean inclusion arrays are required.
    Here we maintain bitsets for tracking.
    """
    if capacity < 0:
        raise ValueError(f"Vehicle capacity cannot be negative: {capacity}")

    n = len(parcels)
    W = int(capacity)
    dp = [0] * (W + 1)
    # Bitmask tracking for reconstruction: pick_mask[w] has bit i set if parcel i was added
    picks = [0] * (W + 1)

    for i, p in enumerate(parcels):
        w_i = p.weight
        v_i = p.value
        # Iterate backwards from W down to w_i to preserve 0/1 condition
        for w in range(W, w_i - 1, -1):
            if dp[w - w_i] + v_i > dp[w]:
                dp[w] = dp[w - w_i] + v_i
                picks[w] = picks[w - w_i] | (1 << i)

    best_val = dp[W]
    best_mask = picks[W]
    selected = [parcels[i] for i in range(n) if (best_mask & (1 << i))]

    return best_val, selected


def format_dp_table_text(
    dp_table: List[List[int]],
    parcels: List[Parcel],
    capacity: int,
    max_w: int = 15,
    max_items: int = 10
) -> str:
    """
    Formats the 2D DP table into an ASCII grid suitable for console reports and markdown.
    Truncates gracefully if matrix dimensions exceed display limits.
    """
    rows = min(len(parcels) + 1, max_items + 1)
    cols = min(capacity + 1, max_w + 1)

    lines = []
    # Header row: Capacity columns 0 .. cols-1
    header = f"{'Item (w, v)':<18} | " + " ".join(f"{w:>4}" for w in range(cols))
    if cols <= capacity:
        header += " ..."
    lines.append(header)
    lines.append("-" * len(header))

    # Base row (0 items)
    base_line = f"{'0 (None)':<18} | " + " ".join(f"{dp_table[0][w]:>4}" for w in range(cols))
    if cols <= capacity:
        base_line += " ..."
    lines.append(base_line)

    for i in range(1, rows):
        p = parcels[i - 1]
        label = f"{p.parcel_id} (w={p.weight}, v={p.value})"
        row_str = f"{label:<18} | " + " ".join(f"{dp_table[i][w]:>4}" for w in range(cols))
        if cols <= capacity:
            row_str += " ..."
        lines.append(row_str)

    if rows <= len(parcels):
        lines.append(f"... [{len(parcels) - rows + 1} more items omitted from visual preview] ...")

    return "\n".join(lines)
