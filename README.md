# Student Portal — JWT Auth · Dashboard · Search Comparison
> A university holds thousands of student records keyed by **composite roll numbers**
> (`25MVCSD0327` = batch 25 + college MV + branch CSD + serial 0327). During exams the
> system must answer, thousands of times: *does this roll number exist, and what is the
> student's info?* This portal does that, and **proves** which search strategy survives
> exam-day load.
>
> Python (stdlib only — no pip installs) · React (Vite + Router) · SQLite · JWT

## 1. Roll format

```
25 MV CSD 0327
│  │  │   └── serial — repeats across branches (CSD and ECE can both hold 0327)
│  │  └────── branch code: CSD, CSE, CSA, ECE, EEE, MEC, CIV
│  └───────── college prefix (MV)
└──────────── admission batch (22–25)
```

Only the **full string is unique** (DB primary key). Serials run **sequentially per
batch+branch** (`25MVCSD0001, 0002, …`, restarting at 0001 for every branch), so the
same serial naturally exists across branches. The add form auto-suggests the next
roll via `GET /api/next-roll?batch=&branch=`. Consequences, all demonstrated live
in the portal:
- Full roll → hash index answers in **O(1)**.
- Serial alone (`0327`) → the index can't serve a partial key: full **O(n) scan**, one row per branch.

## 2. Run it

```bash
# Terminal 1 — Python API (seeds 3,000 students + demo user on first run)
cd student-search-system/backend
python3 app.py --port 5001

# Terminal 2 — React portal
cd student-search-system/frontend
npm install
npm run dev        # -> http://localhost:5173
```

Login with the seeded demo account: **`admin@univ.edu / admin123`** (or sign up a new staff account).

## 3. What is inside

| Page | Route | What it does |
|---|---|---|
| Login / Signup | `/login` | Staff auth, JWT (HS256, 12h) stored in localStorage, protected routes |
| Dashboard | `/` | Total students, avg CGPA, **branch bars**, **batch donut**, live **100-query ops snapshot** (Linear vs Binary vs Hash), recently added |
| Students | `/students` | Search by full roll / serial / name, filter by branch, paginate, **view one record with its per-algorithm ops**, **add new student** (bad format → 400, duplicate full roll → 409, same serial in another branch is fine) |
| Search Lab | `/search` | Core task screen: single lookup ops (full vs serial) + **multi-query comparison** (10–500 queries, log-scale chart, speedup verdict) |

## 4. Backend API (all `/api/*`, `Authorization: Bearer <jwt>` except health + auth)

```
GET  /api/health
POST /api/auth/signup  {name, email, password}
POST /api/auth/login   {email, password} -> {token, user}
GET  /api/me
GET  /api/stats            -> totals, by_branch, by_batch, avg_cgpa, latest, ops_snapshot
GET  /api/students?query=&branch=&limit=&offset=   (query = full roll | serial | name)
GET  /api/students/<roll> -> record + parsed parts + {linear, binary, hash} ops
POST /api/students  {roll_no, name, branch?, cgpa}
POST /api/search    {target}   -> full roll (3-way ops) or 4-digit serial (scan)
POST /api/benchmark {num_queries}
```

Files: `search_algorithms.py` (format parsing + op-counted searches) · `db.py` (SQLite) · `auth.py` (PBKDF2 + JWT) · `app.py` (router) · `benchmark.py` (CLI, no server needed: `python3 benchmark.py --sizes 1000 5000 10000 --queries 100`)

## 5. The answer (say this on stage)

> Index the full composite key once O(n) and every exact query is O(1) — ~2,800× fewer operations than scanning at n=5,000. But a partial key (serial only) can't use the index and falls back to a full scan, returning one row per branch. So: validate the format at entry, store the composite as the key, and the exam-day lookup stays flat.
