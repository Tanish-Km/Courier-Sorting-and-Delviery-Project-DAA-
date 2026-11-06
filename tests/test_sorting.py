"""
Unit tests for sorting algorithms and parcel prioritization.
"""

import unittest
from src.models import Parcel
from src.sorting import mergesort, quicksort, prioritize_parcels, compare_sorting_algorithms


class TestSorting(unittest.TestCase):

    def test_mergesort_basic(self):
        arr = [5, 2, 8, 1, 9, 3, 7, 4, 6]
        sorted_arr = mergesort(arr)
        self.assertEqual(sorted_arr, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_mergesort_reverse(self):
        arr = [5, 2, 8, 1, 9]
        sorted_arr = mergesort(arr, reverse=True)
        self.assertEqual(sorted_arr, [9, 8, 5, 2, 1])

    def test_mergesort_empty_and_single(self):
        self.assertEqual(mergesort([]), [])
        self.assertEqual(mergesort([42]), [42])

    def test_mergesort_stability(self):
        # Pairs of (key, original_order)
        items = [(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd'), (2, 'e')]
        sorted_items = mergesort(items, key=lambda x: x[0])
        # Elements with key 1 should preserve ('b', 'd')
        # Elements with key 2 should preserve ('a', 'c', 'e')
        self.assertEqual(sorted_items, [(1, 'b'), (1, 'd'), (2, 'a'), (2, 'c'), (2, 'e')])

    def test_quicksort_basic(self):
        arr = [64, 34, 25, 12, 22, 11, 90]
        sorted_arr = quicksort(arr)
        self.assertEqual(sorted_arr, sorted(arr))

    def test_quicksort_duplicates(self):
        arr = [3, 1, 2, 3, 3, 1, 2, 1, 3]
        sorted_arr = quicksort(arr)
        self.assertEqual(sorted_arr, [1, 1, 1, 2, 2, 3, 3, 3, 3])

    def test_prioritize_parcels_deadline_priority(self):
        p1 = Parcel("P1", "C1", weight=5, priority=3, deadline=4.0)
        p2 = Parcel("P2", "C2", weight=10, priority=5, deadline=1.0)
        p3 = Parcel("P3", "C3", weight=2, priority=4, deadline=2.0)
        p4 = Parcel("P4", "C4", weight=8, priority=2, deadline=2.0)

        parcels = [p1, p2, p3, p4]
        sorted_parcels = prioritize_parcels(parcels, strategy="deadline_priority", algorithm="mergesort")

        # P2 has earliest deadline (1.0)
        self.assertEqual(sorted_parcels[0].parcel_id, "P2")
        # Next deadline is 2.0: P3 (priority 4) vs P4 (priority 2) -> P3 wins
        self.assertEqual(sorted_parcels[1].parcel_id, "P3")
        self.assertEqual(sorted_parcels[2].parcel_id, "P4")
        # P1 has deadline 4.0
        self.assertEqual(sorted_parcels[3].parcel_id, "P1")

    def test_compare_sorting_algorithms(self):
        parcels = [
            Parcel(f"P{i}", f"C{i%5}", weight=(i*3)%10 + 1, priority=(i%5)+1, deadline=float((i*7)%20 + 1))
            for i in range(30)
        ]
        res = compare_sorting_algorithms(parcels, trials=2)
        self.assertTrue(res["merge_equals_tim"])
        self.assertTrue(res["quick_keys_match_tim"])
        self.assertEqual(res["count"], 30)


if __name__ == "__main__":
    unittest.main()
