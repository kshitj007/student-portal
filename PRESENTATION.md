# Infosys Presentation Script (6–8 min)

## 1. Problem (30s)
"University holds thousands of records keyed by composite roll numbers — `25MVCSD0327`: batch 25, college MV, branch CSD, serial 0327. During exams the system must answer one question thousands of times: *does this roll number exist?* Twist: the serial repeats across branches, so only the **full string is unique**."

## 2. Portal tour (90s)
- **Login** (`admin@univ.edu / admin123`) — staff-only JWT portal; every data call carries a Bearer token.
- **Dashboard** — totals, branch bars, batch donut, recently added, and the live 100-query ops snapshot.
- **Students** — search full roll, then serial `0001`: one query, rows from *every branch and batch* (serials run 0001, 0002, … per batch+branch). Add form suggests the next roll automatically; same serial in a new branch is accepted, duplicate full roll rejected (409).

## 3. Search Lab — the core task (2–3 min) ⭐
- **Full roll**: `22MVCIV0010` → Linear ~1,100 ops, Binary ~10, Hash **1**. Missing `99MVZZZ9999` → Linear scans *everything*, Hash still **1**.
- **Serial only**: `0010` → 3 branches, 2,000-op full scan. *"A partial key cannot use the index — this is why we validate the format at entry."*
- **Multi-query**: 50 queries → Linear ~51k · Binary ~500 · Hash **50**. "Hash needs **~1,000× fewer operations**."
- Crank to 500 queries → linear explodes, hash stays at 500.

## 4. Trade-offs (45s)
| | Preprocessing | Memory | Exact query | Partial (serial) |
|---|---|---|---|---|
| Linear | none | O(1) | O(n) | O(n) |
| Binary | sort O(n log n) | O(1) | O(log n) | degrades |
| Hash | index O(n) | O(n) | **O(1) ★** | can't serve — scan |

## 5. Closing line (15s)
> "Make the full composite roll the key: build the hash index once, answer every exact query in one operation — and force full-format entry, because a bare serial always costs a scan. That is the system we are proposing."

## Backup Q&A
- *"Why not always hash?"* — extra memory + index rebuild on writes; worth it for read-heavy exam workloads.
- *"Same serial in two branches?"* — legal by design; uniqueness is on the full string (DB primary key), demo it live.
- *"Stack?"* — Python stdlib only (SQLite + hand-rolled JWT, zero pip installs); React + Router dashboard with JWT in localStorage and protected routes.
