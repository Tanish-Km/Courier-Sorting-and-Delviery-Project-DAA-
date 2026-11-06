"""
Parcel prioritization and sorting algorithms for the Mini-Courier Planner.
Implements MergeSort, QuickSort, and multi-criteria prioritization logic.
"""

from typing import List, Callable, Any, Tuple, Dict
import time
import random
from .models import Parcel


def mergesort(items: List[Any], key: Callable[[Any], Any] = lambda x: x, reverse: bool = False) -> List[Any]:
    """
    Stable Divide-and-Conquer Merge Sort implementation.
    
    Time Complexity:
        Best Case: O(N log N)
        Average Case: O(N log N)
        Worst Case: O(N log N)
    Space Complexity:
        O(N) auxiliary space
        
    Stability: Guaranteed (preserves order of items with identical keys).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = mergesort(items[:mid], key=key, reverse=reverse)
    right = mergesort(items[mid:], key=key, reverse=reverse)

    return _merge(left, right, key, reverse)


def _merge(left: List[Any], right: List[Any], key: Callable[[Any], Any], reverse: bool) -> List[Any]:
    merged = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        left_key = key(left[i])
        right_key = key(right[j])

        # If not reverse: left <= right; if reverse: left >= right
        # Use <= to maintain stability (elements from left take precedence)
        condition = (left_key >= right_key) if reverse else (left_key <= right_key)

        if condition:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    if i < len(left):
        merged.extend(left[i:])
    if j < len(right):
        merged.extend(right[j:])

    return merged


def quicksort(items: List[Any], key: Callable[[Any], Any] = lambda x: x, reverse: bool = False) -> List[Any]:
    """
    QuickSort implementation featuring Median-of-Three pivot selection and
    3-way Dutch National Flag partitioning for efficient handling of duplicate keys.
    
    Time Complexity:
        Best Case: O(N log N)
        Average Case: O(N log N)
        Worst Case: O(N^2) (mitigated by median-of-three pivot selection)
    Space Complexity:
        O(log N) auxiliary stack frames
    """
    arr = list(items)
    _quicksort_helper(arr, 0, len(arr) - 1, key, reverse)
    return arr


def _quicksort_helper(arr: List[Any], low: int, high: int, key: Callable[[Any], Any], reverse: bool) -> None:
    if low < high:
        # 3-way partition
        lt, gt = _partition_3way(arr, low, high, key, reverse)
        _quicksort_helper(arr, low, lt - 1, key, reverse)
        _quicksort_helper(arr, gt + 1, high, key, reverse)


def _partition_3way(arr: List[Any], low: int, high: int, key: Callable[[Any], Any], reverse: bool) -> Tuple[int, int]:
    # Median-of-three pivot selection to prevent worst-case degradation
    mid = (low + high) // 2
    candidates = [(key(arr[low]), low), (key(arr[mid]), mid), (key(arr[high]), high)]
    candidates.sort(key=lambda c: c[0])
    pivot_idx = candidates[1][1]
    arr[low], arr[pivot_idx] = arr[pivot_idx], arr[low]

    pivot_val = key(arr[low])
    lt = low
    gt = high
    i = low + 1

    while i <= gt:
        item_val = key(arr[i])
        if reverse:
            # Reverse: higher values first
            if item_val > pivot_val:
                arr[lt], arr[i] = arr[i], arr[lt]
                lt += 1
                i += 1
            elif item_val < pivot_val:
                arr[i], arr[gt] = arr[gt], arr[i]
                gt -= 1
            else:
                i += 1
        else:
            # Ascending: lower values first
            if item_val < pivot_val:
                arr[lt], arr[i] = arr[i], arr[lt]
                lt += 1
                i += 1
            elif item_val > pivot_val:
                arr[i], arr[gt] = arr[gt], arr[i]
                gt -= 1
            else:
                i += 1

    return lt, gt


def prioritize_parcels(
    parcels: List[Parcel],
    strategy: str = "deadline_priority",
    algorithm: str = "mergesort"
) -> List[Parcel]:
    """
    Sorts and prioritizes parcels based on delivery requirements.
    
    Strategies:
      - 'deadline_priority': Earliest deadline first, then highest priority, then lightest weight.
      - 'priority_only': Highest priority first (5 down to 1), then deadline.
      - 'value_density': Highest value-to-weight ratio (v/w) first (greedy heuristic).
    
    Algorithms:
      - 'mergesort': Guaranteed O(N log N) stable sort (Recommended for fairness and predictability).
      - 'quicksort': Fast in-place partitioning with median-of-three.
      - 'timsort': Python standard library Timsort.
    """
    if strategy == "deadline_priority":
        # Multi-key comparator:
        # primary: deadline ascending
        # secondary: priority descending (negated)
        # tertiary: weight ascending
        key_fn = lambda p: (p.deadline, -p.priority, p.weight)
        reverse = False
    elif strategy == "priority_only":
        key_fn = lambda p: (-p.priority, p.deadline, p.weight)
        reverse = False
    elif strategy == "value_density":
        key_fn = lambda p: -(p.value / max(1, p.weight))
        reverse = False
    else:
        raise ValueError(f"Unknown prioritization strategy: {strategy}")

    if algorithm == "mergesort":
        return mergesort(parcels, key=key_fn, reverse=reverse)
    elif algorithm == "quicksort":
        return quicksort(parcels, key=key_fn, reverse=reverse)
    elif algorithm == "timsort":
        return sorted(parcels, key=key_fn, reverse=reverse)
    else:
        raise ValueError(f"Unknown sorting algorithm: {algorithm}")


def compare_sorting_algorithms(test_parcels: List[Parcel], trials: int = 5) -> Dict[str, Any]:
    """
    Compares MergeSort, QuickSort, and Python Timsort execution performance.
    """
    results = {}
    key_fn = lambda p: (p.deadline, -p.priority, p.weight)

    # 1. MergeSort
    t0 = time.perf_counter()
    for _ in range(trials):
        sorted_merge = mergesort(test_parcels, key=key_fn)
    merge_time = (time.perf_counter() - t0) / trials

    # 2. QuickSort
    t0 = time.perf_counter()
    for _ in range(trials):
        sorted_quick = quicksort(test_parcels, key=key_fn)
    quick_time = (time.perf_counter() - t0) / trials

    # 3. Timsort (built-in)
    t0 = time.perf_counter()
    for _ in range(trials):
        sorted_tim = sorted(test_parcels, key=key_fn)
    tim_time = (time.perf_counter() - t0) / trials

    results["mergesort_time_ms"] = merge_time * 1000
    results["quicksort_time_ms"] = quick_time * 1000
    results["timsort_time_ms"] = tim_time * 1000
    results["count"] = len(test_parcels)

    # Verify equivalence of sorting outputs
    results["merge_equals_tim"] = [p.parcel_id for p in sorted_merge] == [p.parcel_id for p in sorted_tim]
    results["quick_keys_match_tim"] = [key_fn(p) for p in sorted_quick] == [key_fn(p) for p in sorted_tim]

    return results
