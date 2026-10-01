"""
Student Portal API — stdlib only (no pip install needed).

Roll format: 25MVCSD0327 = batch 25 + college MV + branch CSD + serial 0327.
Serials repeat across branches — only the FULL string is unique.

  python3 app.py --port 5001 --seed 3000

Public:
  GET  /api/health
  POST /api/auth/signup   {name, email, password} -> {token, user}
  POST /api/auth/login    {email, password}       -> {token, user}

Protected (Authorization: Bearer <jwt>):
  GET  /api/me
  GET  /api/stats                          -> totals + distributions + ops snapshot
  GET  /api/students?query=&branch=&limit=50&offset=0
  GET  /api/students/<roll>                -> record + parts + per-algorithm ops
  POST /api/students  {roll_no,name,branch?,cgpa}
  POST /api/search    {target}              -> full roll (3-way ops) or serial (scan)
  POST /api/benchmark {num_queries}
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote

import db
from auth import create_token, hash_password, verify_password, verify_token
from search_algorithms import (
    BRANCH_NAMES,
    Student,
    batch_compare,
    binary_search,
    build_index,
    generate_students,
    hash_search,
    linear_search,
    parse_roll,
    serial_scan,
)

VALID_BRANCHES = sorted(BRANCH_NAMES)
SERIAL_RE = re.compile(r"^\d{4}$")


def all_records() -> list[Student]:
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT roll, name, branch, batch, college, serial, cgpa FROM students ORDER BY rowid").fetchall()
    conn.close()
    return [Student(r["roll"], r["name"], r["branch"], r["batch"],
                    r["college"], r["serial"], r["cgpa"]) for r in rows]


def missing_roll() -> str:
    """A valid-format roll guaranteed absent from seeded data."""
    return "99MVZZZ9999"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    # -- helpers ---------------------------------------------------------
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = 0
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode() or "{}")
        except Exception:
            return {}

    def _auth_user(self):
        authz = self.headers.get("Authorization", "")
        if not authz.startswith("Bearer "):
            return None
        payload = verify_token(authz[7:])
        if not payload:
            return None
        conn = db.get_conn()
        row = conn.execute("SELECT id, name, email FROM users WHERE id=?", (payload["sub"],)).fetchone()
        conn.close()
        return dict(row) if row else None

    def _require_auth(self):
        user = self._auth_user()
        if not user:
            self._json({"error": "unauthorized — login first"}, 401)
        return user

    # -- GET -------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            return self._json({"ok": True, "service": "student-portal-api"})

        if path == "/api/me":
            user = self._require_auth()
            return self._json({"user": user}) if user else None

        if path == "/api/stats":
            if not self._require_auth():
                return None
            conn = db.get_conn()
            total = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
            by_branch = {r["branch"]: r["c"] for r in
                         conn.execute("SELECT branch, COUNT(*) c FROM students GROUP BY branch")}
            by_batch = {str(r["batch"]): r["c"] for r in
                        conn.execute("SELECT batch, COUNT(*) c FROM students GROUP BY batch")}
            avg = conn.execute("SELECT AVG(cgpa) a FROM students").fetchone()["a"] or 0
            latest = [db.student_to_dict(r) for r in
                      conn.execute("SELECT * FROM students ORDER BY created_at DESC LIMIT 5")]
            conn.close()
            records = all_records()
            rolls = [s.roll_no for s in records]
            rng = random.Random(7)
            targets = [rng.choice(rolls) if rng.random() < 0.8
                       else missing_roll() for _ in range(min(100, max(len(rolls), 1)))] if rolls else []
            ops = batch_compare(records, targets) if records else None
            return self._json({
                "total_students": total,
                "by_branch": by_branch,
                "branch_names": BRANCH_NAMES,
                "by_batch": by_batch,
                "avg_cgpa": round(avg, 2),
                "latest": latest,
                "ops_snapshot": ({k: {"total_ops": ops[k]["total_ops"], "avg_ops": ops[k]["avg_ops"]}
                                  for k in ("linear", "binary", "hash")} if ops else None),
            })

        if path == "/api/students":
            if not self._require_auth():
                return None
            qs = parse_qs(parsed.query)
            q = (qs.get("query", [""])[0] or "").strip().upper()
            branch = (qs.get("branch", [""])[0] or "").strip().upper()
            try:
                limit = max(1, min(int(qs.get("limit", ["50"])[0]), 200))
                offset = max(0, int(qs.get("offset", ["0"])[0]))
            except ValueError:
                return self._json({"error": "bad pagination"}, 400)
            conn = db.get_conn()
            where, params = [], []
            if q:
                if parse_roll(q):
                    where.append("roll = ?")
                    params.append(q)
                elif SERIAL_RE.match(q):
                    where.append("serial = ?")  # same serial, every branch
                    params.append(q)
                else:
                    where.append("name LIKE ?")
                    params.append(f"%{q}%")
            if branch:
                where.append("branch = ?")
                params.append(branch)
            clause = f"WHERE {' AND '.join(where)}" if where else ""
            total = conn.execute(f"SELECT COUNT(*) c FROM students {clause}", params).fetchone()["c"]
            rows = conn.execute(
                f"SELECT * FROM students {clause} ORDER BY roll LIMIT ? OFFSET ?",
                (*params, limit, offset)).fetchall()
            conn.close()
            return self._json({"total": total, "limit": limit, "offset": offset,
                               "students": [db.student_to_dict(r) for r in rows]})

        if path == "/api/next-roll":
            if not self._require_auth():
                return None
            qs = parse_qs(parsed.query)
            try:
                batch = int((qs.get("batch", ["25"])[0] or "25"))
            except ValueError:
                return self._json({"error": "batch must be a number, e.g. 25"}, 400)
            branch = (qs.get("branch", ["CSD"])[0] or "").strip().upper()
            if branch not in VALID_BRANCHES:
                return self._json({"error": f"unknown branch (one of {VALID_BRANCHES})"}, 400)
            conn = db.get_conn()
            row = conn.execute(
                "SELECT MAX(CAST(serial AS INTEGER)) m FROM students WHERE batch=? AND branch=?",
                (batch, branch)).fetchone()
            conn.close()
            nxt = (row["m"] or 0) + 1
            if nxt > 9999:
                return self._json({"error": "serials exhausted for this batch+branch"}, 400)
            from search_algorithms import COLLEGE, make_roll
            return self._json({"batch": batch, "branch": branch,
                               "next_serial": f"{nxt:04d}",
                               "roll": make_roll(batch, COLLEGE, branch, nxt)})

        if path.startswith("/api/students/"):
            if not self._require_auth():
                return None
            roll = unquote(path.rsplit("/", 1)[-1]).strip().upper()
            parts = parse_roll(roll)
            if not parts:
                return self._json({"error": "invalid roll — use format 25MVCSD0327"}, 400)
            records = all_records()
            idx = build_index(records)
            rec_h, ops_h = hash_search(idx, roll)
            if rec_h is None:
                return self._json({"error": f"roll {roll} not found"}, 404)
            _, ops_l = linear_search(records, roll)
            _, ops_b = binary_search(sorted(records, key=lambda s: s.roll_no), roll)
            d = rec_h.to_dict()
            d["ops"] = {"linear": ops_l, "binary": ops_b, "hash": ops_h}
            return self._json(d)

        return self._json({"error": "not found"}, 404)

    # -- POST ------------------------------------------------------------
    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()

        if path == "/api/auth/signup":
            name, email, pw = (body.get("name", "") or "").strip(), \
                (body.get("email", "") or "").strip().lower(), body.get("password", "") or ""
            if len(name) < 2 or "@" not in email or len(pw) < 6:
                return self._json({"error": "name (2+), valid email, password (6+) required"}, 400)
            pw_hash, salt = hash_password(pw)
            conn = db.get_conn()
            try:
                cur = conn.execute(
                    "INSERT INTO users (name, email, pw_hash, salt, created_at) VALUES (?,?,?,?,?)",
                    (name, email, pw_hash, salt, time.time()))
                conn.commit()
                uid = cur.lastrowid
            except Exception:
                conn.close()
                return self._json({"error": "email already registered"}, 409)
            conn.close()
            return self._json({"token": create_token(uid, email),
                               "user": {"id": uid, "name": name, "email": email}})

        if path == "/api/auth/login":
            email, pw = (body.get("email", "") or "").strip().lower(), body.get("password", "") or ""
            conn = db.get_conn()
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            conn.close()
            if not row or not verify_password(pw, row["pw_hash"], row["salt"]):
                return self._json({"error": "invalid email or password"}, 401)
            user = {"id": row["id"], "name": row["name"], "email": row["email"]}
            return self._json({"token": create_token(user["id"], user["email"]), "user": user})

        # ---- everything below needs auth ----
        user = self._require_auth()
        if not user:
            return None

        if path == "/api/students":
            roll = (str(body.get("roll_no", "")) or "").strip().upper()
            parts = parse_roll(roll)
            name = (body.get("name", "") or "").strip()
            branch = (body.get("branch", "") or "").strip().upper()
            try:
                cgpa = float(body.get("cgpa", 0))
            except (TypeError, ValueError):
                return self._json({"error": "cgpa must be a number"}, 400)
            if not parts:
                return self._json({"error": "roll_no must look like 25MVCSD0327 (YY + college + branch + 4-digit serial)"}, 400)
            if parts["branch"] not in VALID_BRANCHES:
                return self._json({"error": f"unknown branch code (one of {VALID_BRANCHES})"}, 400)
            if branch and branch != parts["branch"]:
                return self._json({"error": f"branch {branch} does not match roll ({parts['branch']})"}, 400)
            if len(name) < 2 or not (0 <= cgpa <= 10):
                return self._json({"error": "name (2+) and cgpa 0-10 required"}, 400)
            conn = db.get_conn()
            try:
                conn.execute(
                    "INSERT INTO students (roll, name, branch, batch, college, serial, cgpa, created_at)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (roll, name, parts["branch"], parts["batch"],
                     parts["college"], parts["serial"], cgpa, time.time()))
                conn.commit()
            except Exception:
                conn.close()
                return self._json({"error": f"roll {roll} already exists"}, 409)
            conn.close()
            return self._json({"ok": True, "student": {"roll_no": roll, "name": name,
                                                       "branch": parts["branch"], "batch": parts["batch"],
                                                       "serial": parts["serial"], "cgpa": cgpa}}, 201)

        if path == "/api/search":
            target = (str(body.get("target", "")) or "").strip().upper()
            if not target:
                return self._json({"error": "target is required, e.g. 25MVCSD0327 or serial 0327"}, 400)
            records = all_records()
            if SERIAL_RE.match(target):
                # Partial key: the index cannot serve it — full scan, every branch.
                matches, ops = serial_scan(records, target)
                return self._json({"target": target, "mode": "serial", "dataset_size": len(records),
                                   "found": [m.to_dict() for m in matches],
                                   "linear": {"ops": ops, "found": len(matches) > 0},
                                   "binary": {"ops": None, "found": None},
                                   "hash": {"ops": None, "found": None},
                                   "note": "Serial-only search scans all records — use the full roll for O(1) lookup."})
            if not parse_roll(target):
                return self._json({"error": "use a full roll (25MVCSD0327) or a 4-digit serial (0327)"}, 400)
            idx = build_index(records)
            rec_l, ops_l = linear_search(records, target)
            rec_b, ops_b = binary_search(sorted(records, key=lambda s: s.roll_no), target)
            rec_h, ops_h = hash_search(idx, target)
            found = rec_h or rec_b or rec_l
            return self._json({"target": target, "mode": "full", "dataset_size": len(records),
                               "found": found.to_dict() if found else None,
                               "linear": {"ops": ops_l, "found": rec_l is not None},
                               "binary": {"ops": ops_b, "found": rec_b is not None},
                               "hash": {"ops": ops_h, "found": rec_h is not None}})

        if path == "/api/benchmark":
            try:
                q = max(1, min(int(body.get("num_queries", 100) or 100), 2000))
            except (TypeError, ValueError):
                return self._json({"error": "num_queries must be a number"}, 400)
            records = all_records()
            if not records:
                return self._json({"error": "no students yet"}, 400)
            rolls = [s.roll_no for s in records]
            rng = random.Random(7)
            targets = [rng.choice(rolls) if rng.random() < 0.8 else missing_roll() for _ in range(q)]
            return self._json(batch_compare(records, targets))

        return self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--seed", type=int, default=3000, help="seed rows if DB empty")
    args = ap.parse_args()
    db.init_db()
    db.ensure_demo_user()
    if db.count_students() == 0:
        n = db.seed_students(generate_students(args.seed, seed=42))
        print(f"Seeded {n} students")
    srv = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Student Portal API at http://localhost:{args.port}  (demo: admin@univ.edu / admin123)")
    srv.serve_forever()
