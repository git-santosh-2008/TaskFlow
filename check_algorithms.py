"""
Section 2, Task 7 — Automated checks for the sorting/search engine.

Lives at the repo root (per the suggested repository structure) but
imports the real engine from backend/algorithms.py — the exact same
functions that power GET /tasks?sort=... and GET /tasks/search.

Plain if/else checks (no assert/pytest/unittest), one PASS/FAIL line
printed per case.

Run with (from the repo root):  python3 check_algorithms.py
"""

import os
import sys

# Make backend/algorithms.py importable from the repo root without
# turning backend/ into a package or duplicating the algorithm code.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from algorithms import (
    insertion_sort,
    binary_search,
    linear_search,
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
)


def check(case_name, result, expected):
    if result == expected:
        print(f"PASS: {case_name}")
    else:
        print(f"FAIL: {case_name} — expected {expected}, got {result}")


def run_checks():
    # 1. insertion_sort on an empty list leaves it empty, completes without error.
    empty_list = []
    insertion_sort(empty_list, "value")
    check("insertion_sort: empty list stays empty", empty_list, [])

    # 2. insertion_sort on a single-element list leaves it unchanged.
    single = [{"value": 42}]
    insertion_sort(single, "value")
    check("insertion_sort: single-element list unchanged", single, [{"value": 42}])

    # 3. binary_search finds a value at the first, last, and middle index.
    sorted_records = [{"value": v} for v in [10, 20, 30, 40, 50]]
    check("binary_search: finds value at first index",
          binary_search(sorted_records, 10, "value"), 0)
    check("binary_search: finds value at last index",
          binary_search(sorted_records, 50, "value"), 4)
    check("binary_search: finds value at middle index",
          binary_search(sorted_records, 30, "value"), 2)

    # 4. binary_search returns the not-found result when target is absent.
    check("binary_search: returns None when target is absent",
          binary_search(sorted_records, 999, "value"), None)

    # 5. insertion_sort_count sorts correctly AND returns an int > 0.
    hand_checkable = [{"value": 3}, {"value": 1}, {"value": 2}]
    count_result = insertion_sort_count(hand_checkable, "value")
    check("insertion_sort_count: sorts the list correctly",
          hand_checkable, [{"value": 1}, {"value": 2}, {"value": 3}])
    check("insertion_sort_count: return value is a plain int",
          type(count_result) == int, True)
    check("insertion_sort_count: comparison count > 0 for multi-element list",
          count_result > 0, True)

    # 6. binary_search_count on a sorted list, value present at a known index.
    sorted_for_count = [{"value": v} for v in [5, 15, 25, 35, 45]]
    bsc_result = binary_search_count(sorted_for_count, 25, "value")
    check("binary_search_count: index matches expected position",
          bsc_result["index"], 2)
    check("binary_search_count: comparison_count is an int > 0",
          type(bsc_result["comparison_count"]) == int and bsc_result["comparison_count"] > 0, True)

    # 7. linear_search_count for an absent value.
    unsorted_for_count = [{"value": v} for v in [7, 3, 9, 1]]
    lsc_result = linear_search_count(unsorted_for_count, 999, "value")
    check("linear_search_count: index is None when absent",
          lsc_result["index"], None)
    check("linear_search_count: comparison_count equals list length",
          lsc_result["comparison_count"], len(unsorted_for_count))


if __name__ == "__main__":
    run_checks()