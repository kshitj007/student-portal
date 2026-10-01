"""SQLite storage for the student portal (stdlib only).

Rolls are composite strings: 25MVCSD0327 = batch 25 + college MV +
branch CSD + serial 0327. The serial repeats across branches — only the
FULL string is unique (PRIMARY KEY).
"""
from __future__ import annotations

import os
import sqlite3
import time

DB_PATH = os.environ.get("STUDENT_DB", os.path.join(os.path.dirname(__file__), "students.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            pw_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    # Migrate from the old integer-roll schema if present (dev data reset).
    cols = [r[1] for r in cur.execute("PRAGMA table_info(students)").fetchall()]
    if cols and "roll" not in cols:
        cur.execute("DROP TABLE students")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            batch INTEGER NOT NULL,
            college TEXT NOT NULL,
            serial TEXT NOT NULL,
            cgpa REAL NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_students_serial ON students(serial)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_students_branch ON students(branch)")
    conn.commit()
    conn.close()


def count_students() -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    conn.close()
    return n


def seed_students(records) -> int:
    """Insert generated records (ignores duplicates). Returns rows present after."""
    conn = get_conn()
    now = time.time()
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR IGNORE INTO students (roll, name, branch, batch, college, serial, cgpa, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        [(s.roll_no, s.name, s.branch, s.batch, s.college, s.serial, s.cgpa, now) for s in records],
    )
    conn.commit()
    n = cur.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    conn.close()
    return n


def ensure_demo_user() -> None:
    """Create admin@univ.edu / admin123 on first run so the demo works offline."""
    from auth import hash_password  # local import to avoid cycle at module load
    conn = get_conn()
    exists = conn.execute("SELECT id FROM users WHERE email=?", ("admin@univ.edu",)).fetchone()
    if not exists:
        pw_hash, salt = hash_password("admin123")
        conn.execute(
            "INSERT INTO users (name, email, pw_hash, salt, created_at) VALUES (?,?,?,?,?)",
            ("Demo Admin", "admin@univ.edu", pw_hash, salt, time.time()),
        )
        conn.commit()
    conn.close()


def student_to_dict(row) -> dict:
    return {
        "roll_no": row["roll"],
        "name": row["name"],
        "branch": row["branch"],
        "batch": row["batch"],
        "college": row["college"],
        "serial": row["serial"],
        "cgpa": row["cgpa"],
    }
