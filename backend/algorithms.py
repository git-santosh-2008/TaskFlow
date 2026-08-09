"""
Section 2 — Hand-rolled sorting & search algorithms.

These are the ONLY sorting/search functions used by the GET /tasks?sort=...
and GET /tasks/search endpoints in routers/tasks.py — never Python's
built-in sorted() / list.sort(), and never a hand-computed substitute.

Not-found convention (documented, as the assignment allows either):
binary_search / linear_search / *_count return None (not -1) when no
matching record exists. None was chosen over -1 because it can never be
confused with a real index (index 0 is falsy but "found", -1 could
collide with negative-index slicing bugs elsewhere) and it reads clearly
in `if position is None:` checks.
"""

from typing import List, Dict, Any, Optional


# =========================================================
# Task 1 — insertion_sort
# =========================================================
def insertion_sort(records: List[Dict[str, Any]], key: str) -> None:
    """
    Sorts `records` in place, ascending, by record[key].

    Standard insertion sort: starting from the second element (index 1),
    compare it against the already-sorted elements before it, shifting
    each larger one right by one slot, until the correct position for
    the current element is found.

    Mutates `records` directly. Returns nothing.
    """
    for i in range(1, len(records)):
        current = records[i]
        current_value = current[key]
        j = i - 1
        while j >= 0 and records[j][key] > current_value:
            records[j + 1] = records[j]
            j -= 1
        records[j + 1] = current


# =========================================================
# Task 2 — binary_search
# =========================================================
def binary_search(sorted_records: List[Dict[str, Any]], target_value: Any, key: str) -> Optional[int]:
    """
    Standard binary search over a list already sorted ascending by
    record[key] (as produced by insertion_sort). Returns the index of a
    record whose record[key] == target_value, or None if absent.
    """
    low = 0
    high = len(sorted_records) - 1

    while low <= high:
        mid = (low + high) // 2
        mid_value = sorted_records[mid][key]

        if mid_value == target_value:
            return mid
        elif mid_value < target_value:
            low = mid + 1
        else:
            high = mid - 1

    return None


# =========================================================
# Task 3 — linear_search
# =========================================================
def linear_search(records: List[Dict[str, Any]], target_value: Any, key: str) -> Optional[int]:
    """
    Baseline linear scan, in order. Returns the index of the first record
    whose record[key] == target_value, or None if absent.
    """
    for i, record in enumerate(records):
        if record[key] == target_value:
            return i
    return None


# =========================================================
# Task 5 — comparison-counting wrapper functions
# (reimplement the same logic as Tasks 1-3, without changing their
# signatures/return contracts — used only by the benchmark script)
# =========================================================
def insertion_sort_count(records: List[Dict[str, Any]], key: str) -> int:
    """
    Sorts `records` in place exactly as insertion_sort does, counting
    every comparison made against an already-placed element. Returns
    only that count (a plain int).
    """
    comparisons = 0
    for i in range(1, len(records)):
        current = records[i]
        current_value = current[key]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if records[j][key] > current_value:
                records[j + 1] = records[j]
                j -= 1
            else:
                break
        records[j + 1] = current
    return comparisons


def binary_search_count(sorted_records: List[Dict[str, Any]], target_value: Any, key: str) -> Dict[str, Any]:
    """
    Same logic as binary_search, counting every comparison made against
    target_value. Returns {"index": ..., "comparison_count": ...}.
    """
    low = 0
    high = len(sorted_records) - 1
    comparisons = 0

    while low <= high:
        mid = (low + high) // 2
        mid_value = sorted_records[mid][key]
        comparisons += 1

        if mid_value == target_value:
            return {"index": mid, "comparison_count": comparisons}
        elif mid_value < target_value:
            low = mid + 1
        else:
            high = mid - 1

    return {"index": None, "comparison_count": comparisons}


def linear_search_count(records: List[Dict[str, Any]], target_value: Any, key: str) -> Dict[str, Any]:
    """
    Same logic as linear_search, counting every comparison made.
    Returns {"index": ..., "comparison_count": ...}.
    """
    comparisons = 0
    for i, record in enumerate(records):
        comparisons += 1
        if record[key] == target_value:
            return {"index": i, "comparison_count": comparisons}
    return {"index": None, "comparison_count": comparisons}


    