"""Benchmark runner — compares ops for MULTIPLE roll numbers at scale."""
from __future__ import annotations

import argparse
import json
import random
import sys

from search_algorithms import batch_compare, generate_students


def make_targets(records, num_queries: int, hit_ratio: float = 0.8, seed: int = 7):
    rng = random.Random(seed)
    rolls = [s.roll_no for s in records]
    targets = []
    for _ in range(num_queries):
        if rng.random() < hit_ratio:
            targets.append(rng.choice(rolls))       # existing roll no
        else:
            targets.append("99MVZZZ9999")  # valid format, missing roll no
    return targets


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark student search algorithms")
    ap.add_argument("--sizes", nargs="+", type=int, default=[1000, 5000, 10000])
    ap.add_argument("--queries", type=int, default=100)
    ap.add_argument("--json-out", type=str, default="")
    args = ap.parse_args()

    all_results = []
    for n in args.sizes:
        records = generate_students(n, seed=42)
        targets = make_targets(records, args.queries)
        res = batch_compare(records, targets)
        all_results.append(res)
        L, B, H = res["linear"], res["binary"], res["hash"]
        print(f"\nDataset n={n:>6,} | queries q={args.queries}")
        print(f"  Linear  O(n)      : total_ops={L['total_ops']:>8,}  avg={L['avg_ops']:>8}  time={L['time_us']:>10,.1f} us")
        print(f"  Binary  O(log n)  : total_ops={B['total_ops']:>8,}  avg={B['avg_ops']:>8}  time={B['time_us']:>10,.1f} us")
        print(f"  Hash    O(1) avg  : total_ops={H['total_ops']:>8,}  avg={H['avg_ops']:>8}  time={H['time_us']:>10,.1f} us")
        print(f"  => Hash is ~{L['total_ops']/max(H['total_ops'],1):,.0f}x fewer ops than Linear, "
              f"~{B['total_ops']/max(H['total_ops'],1):,.0f}x fewer than Binary.")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved JSON -> {args.json_out}")


if __name__ == "__main__":
    sys.exit(main())
