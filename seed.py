"""
Section 2, Task 5 — Benchmark seeding script.

Lives at the repo root (per the suggested repository structure) but
imports the real engine from backend/algorithms.py — the exact same
counting functions that power GET /tasks?sort=... and GET /tasks/search
internally.

Generates synthetic task data (same title/priority/due_date fields the
real /tasks endpoints operate on) at three sizes — 10, 500, 3000 — per
the assignment's allowance ("if seeding 3,000 real rows locally is
impractical, generate synthetic in-memory task dictionaries... at the
same three sizes instead"). Prints and saves the raw comparison counts.

Run with (from the repo root):  python3 seed.py
"""

import os
import sys
import random
import string
import copy

# Make backend/algorithms.py importable from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from algorithms import insertion_sort_count, binary_search_count, linear_search_count

SIZES = [10, 500, 3000]
PRIORITIES = ["low", "medium", "high"]
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}

RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.txt")


def make_synthetic_tasks(n: int) -> list:
    """
    Generates n synthetic task dicts with the same fields the real
    /tasks endpoints operate on: title, priority, due_date.
    Titles are zero-padded + random-suffixed so every title is unique
    (search-by-title needs an unambiguous target).
    """
    random.seed(42)  # reproducible counts across runs
    tasks = []
    for i in range(n):
        suffix = "".join(random.choices(string.ascii_lowercase, k=5))
        tasks.append({
            "id": i + 1,
            "title": f"task-{i:06d}-{suffix}",
            "priority": random.choice(PRIORITIES),
            "due_date": f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        })
    return tasks


def run_benchmark():
    lines = []
    lines.append("Section 2 - Task 5 benchmark results")
    lines.append("(counts produced by the exact functions behind /tasks?sort= and /tasks/search)")
    lines.append("=" * 78)

    for n in SIZES:
        base_tasks = make_synthetic_tasks(n)

        # --- insertion_sort_count: sort the full task list by priority rank
        #     (mirrors what GET /tasks?sort=priority does) ---
        sort_input = copy.deepcopy(base_tasks)
        for t in sort_input:
            t["_rank"] = PRIORITY_RANK[t["priority"]]
        sort_comparisons = insertion_sort_count(sort_input, "_rank")

        # --- build the {"id","title"} index used by GET /tasks/search,
        #     then sort a copy of it by title (needed before binary search) ---
        index = [{"id": t["id"], "title": t["title"]} for t in base_tasks]
        sorted_index = copy.deepcopy(index)
        index_sort_comparisons = insertion_sort_count(sorted_index, "title")

        # search for a title that exists (the middle element after sorting)
        # and one that doesn't, on both algorithms
        target_present = sorted_index[len(sorted_index) // 2]["title"]
        target_absent = "this-title-does-not-exist"

        binary_present = binary_search_count(sorted_index, target_present, "title")
        binary_absent = binary_search_count(sorted_index, target_absent, "title")

        linear_present = linear_search_count(index, target_present, "title")
        linear_absent = linear_search_count(index, target_absent, "title")

        lines.append(f"\n--- n = {n} tasks ---")
        lines.append(f"insertion_sort_count  (sort tasks by priority):      {sort_comparisons:>10,} comparisons")
        lines.append(f"insertion_sort_count  (sort search index by title):  {index_sort_comparisons:>10,} comparisons")
        lines.append(f"binary_search_count   (title present, mid element):  {binary_present['comparison_count']:>10,} comparisons  (index={binary_present['index']})")
        lines.append(f"binary_search_count   (title absent):                {binary_absent['comparison_count']:>10,} comparisons  (index={binary_absent['index']})")
        lines.append(f"linear_search_count   (title present, mid element):  {linear_present['comparison_count']:>10,} comparisons  (index={linear_present['index']})")
        lines.append(f"linear_search_count   (title absent):                {linear_absent['comparison_count']:>10,} comparisons  (index={linear_absent['index']})")

    output = "\n".join(lines)
    print(output)

    with open(RESULTS_FILE, "w") as f:
        f.write(output + "\n")

    print(f"\nRaw results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    run_benchmark()

    