"""
Student Record Searching System — core logic.

Roll format: YY + COLLEGE(2) + BRANCH(3) + SERIAL(4), e.g. 25MVCSD0327
  25   = admission batch (year)
  MV   = college prefix
  CSD  = branch code (Computer Science - Data)
  0327 = serial — NOT unique across branches: CSD and ECE can both have 0327.
         Uniqueness holds on the FULL composite string only.

Compares three strategies for the same task:
  1. Linear Search   — O(n) per query, no preprocessing, works on unsorted data
  2. Binary Search   — O(log n) per query, needs sorted data
  3. Hash Search     — O(1) average per query, needs a dict index (roll -> record)

Each search returns (record_or_None, operations) so the number of
comparisons / hash probes can be compared fairly for MULTIPLE queries.
"""
from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


ROLL_RE = re.compile(r"^(\d{2})([A-Z]{2})([A-Z]{3})(\d{4})$")

BRANCH_NAMES = {
    "CSD": "Computer Science (Data)",
    "CSE": "Computer Science",
    "CSA": "Computer Science (AI)",
    "ECE": "Electronics & Communication",
    "EEE": "Electrical & Electronics",
    "MEC": "Mechanical",
    "CIV": "Civil",
}
BRANCHES = sorted(BRANCH_NAMES)
COLLEGE = "MV"
BATCHES = [22, 23, 24, 25]


def parse_roll(roll: str) -> Optional[dict]:
    """Split '25MVCSD0327' into parts. Returns None if the format is invalid."""
    m = ROLL_RE.match((roll or "").strip().upper())
    if not m:
        return None
    batch, college, branch, serial = m.groups()
    return {"batch": int(batch), "college": college, "branch": branch, "serial": serial}


def make_roll(batch: int, college: str, branch: str, serial: int) -> str:
    return f"{batch:02d}{college}{branch}{serial:04d}"


@dataclass
class Student:
    roll_no: str   # full composite, e.g. 25MVCSD0327 (unique)
    name: str
    branch: str    # 3-letter code, e.g. CSD
    batch: int     # admission year, e.g. 25
    college: str   # e.g. MV
    serial: str    # 4-digit, e.g. 0327 (repeats across branches)
    cgpa: float

    def to_dict(self) -> dict:
        return asdict(self)


FIRST = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Krishna",
         "Meera", "Nikhil", "Priya", "Rahul", "Riya", "Rohan", "Sanya",
         "Sneha", "Vikram", "Aditya", "Pooja", "Karan", "Neha"]
LAST = ["Sharma", "Verma", "Patel", "Reddy", "Gupta", "Mehta", "Iyer",
        "Nair", "Singh", "Khan", "Das", "Kulkarni", "Joshi", "Agarwal"]


def generate_students(n: int, seed: int = 42) -> List[Student]:
    """Generate n records with SEQUENTIAL serials per (batch, branch).

    First CSD student of batch 25 -> 25MVCSD0001, next -> 25MVCSD0002, ...
    Every branch restarts at 0001, so the same serial (e.g. 0007) exists under
    several branch codes — like real university data. Uniqueness holds on the
    full composite string only.
    """
    rng = random.Random(seed)
    combos = [(b, br) for b in BATCHES for br in BRANCHES]
    per, extra = divmod(n, len(combos))
    students = []
    for i, (batch, branch) in enumerate(combos):
        for serial in range(1, per + (1 if i < extra else 0) + 1):
            students.append(Student(
                roll_no=make_roll(batch, COLLEGE, branch, serial),
                name=f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                branch=branch,
                batch=batch,
                college=COLLEGE,
                serial=f"{serial:04d}",
                cgpa=round(rng.uniform(6.0, 10.0), 2),
            ))
    rng.shuffle(students)  # simulate unsorted DB dump
    return students


def next_serial(existing: List[int]) -> int:
    """Next sequential serial after the ones already taken (1-based)."""
    return (max(existing) if existing else 0) + 1


# ---------------------------------------------------------------- search fns

def linear_search(records: List[Student], target: str) -> Tuple[Optional[Student], int]:
    """Scan one by one. ops = number of roll comparisons."""
    ops = 0
    for s in records:
        ops += 1
        if s.roll_no == target:
            return s, ops
    return None, ops


def binary_search(sorted_records: List[Student], target: str) -> Tuple[Optional[Student], int]:
    """Binary search on roll-sorted list. ops = number of comparisons."""
    lo, hi = 0, len(sorted_records) - 1
    ops = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        ops += 1
        mid_roll = sorted_records[mid].roll_no
        if mid_roll == target:
            return sorted_records[mid], ops
        elif mid_roll < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return None, ops


def build_index(records: List[Student]) -> Dict[str, Student]:
    """Preprocessing for hash search: one-time O(n) index build."""
    return {s.roll_no: s for s in records}


def hash_search(index: Dict[str, Student], target: str) -> Tuple[Optional[Student], int]:
    """
    Dict lookup. Counted as 1 operation (one hash + probe on average).
    This is the correct system choice for 'does this roll number exist?' queries.
    """
    rec = index.get(target)
    return rec, 1


def serial_scan(records: List[Student], serial: str) -> Tuple[List[Student], int]:
    """Find every branch holding this serial. Must scan all n — the index
    only helps full composite keys. ops is always len(records)."""
    found = [s for s in records if s.serial == serial]
    return found, len(records)


# ------------------------------------------------------- multi-query compare

def batch_compare(
    records: List[Student],
    targets: List[str],
) -> dict:
    """
    Search for MULTIPLE roll numbers with each algorithm.
    Returns total ops + total time per algorithm so the comparison is exact.
    """
    sorted_records = sorted(records, key=lambda s: s.roll_no)
    index = build_index(records)

    def run(fn_name: str) -> dict:
        per_query_ops: List[int] = []
        found = 0
        t0 = time.perf_counter()
        for t in targets:
            if fn_name == "linear":
                rec, ops = linear_search(records, t)
            elif fn_name == "binary":
                rec, ops = binary_search(sorted_records, t)
            else:
                rec, ops = hash_search(index, t)
            per_query_ops.append(ops)
            if rec is not None:
                found += 1
        dt_us = (time.perf_counter() - t0) * 1e6
        return {
            "total_ops": sum(per_query_ops),
            "avg_ops": round(sum(per_query_ops) / max(len(per_query_ops), 1), 2),
            "per_query_ops": per_query_ops,
            "found": found,
            "time_us": round(dt_us, 2),
        }

    linear = run("linear")
    binary = run("binary")
    hashed = run("hash")

    return {
        "dataset_size": len(records),
        "num_queries": len(targets),
        "linear": {"algorithm": "Linear Search", "complexity": "O(n)", **linear},
        "binary": {"algorithm": "Binary Search", "complexity": "O(log n)", **binary},
        "hash": {"algorithm": "Hash Search (Dict Index)", "complexity": "O(1) avg", **hashed},
    }


if __name__ == "__main__":
    recs = generate_students(1000)
    rolls = [s.roll_no for s in recs]
    sample_targets = rolls[:5] + ["99MVZZZ9999"]  # 5 hits + 1 miss
    import json
    print(json.dumps(batch_compare(recs, sample_targets), indent=2))
