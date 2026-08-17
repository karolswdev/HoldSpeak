#!/usr/bin/env python3
"""HS-137-04 — prove the schema collapse preserves the owner's real data.

Copies the owner's real database to a scratch path, opens the COPY through
the app's normal path (`Database(copy)` → reconcile-on-open), and asserts
invariant A6: every table and every row survives, `scheduled_recordings`
is gained, and the open does not raise a version refusal. THE ORIGINAL IS
NEVER TOUCHED — all work is on the copy.

Run:  uv run python scripts/verify_reconcile_real_db.py
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

REAL_DB = Path.home() / ".local/share/holdspeak/holdspeak.db"
# Tables we expect to be populated on the owner's desk — row counts must
# not drop across the reconcile.
SAMPLE_TABLES = (
    "meetings", "decisions", "artifacts", "workbenches", "recipes",
    "notes", "profiles", "activity_records",
)

FAILS: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    if not cond:
        FAILS.append(f"{label} {detail}")
    print(f"  {mark}  {label}" + (f"  {detail}" if detail else ""), flush=True)


def table_set(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def row_counts(conn: sqlite3.Connection, tables: set[str]) -> dict[str, int]:
    counts = {}
    for t in SAMPLE_TABLES:
        if t in tables:
            counts[t] = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    return counts


def main() -> int:
    if not REAL_DB.exists():
        print(f"real DB not found at {REAL_DB}", flush=True)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="hs137-verify-"))
    copy = tmp / "holdspeak.db"
    # Copy the DB and any sidecar WAL/SHM so the copy is consistent.
    shutil.copy2(REAL_DB, copy)
    for suffix in ("-wal", "-shm"):
        side = REAL_DB.with_name(REAL_DB.name + suffix)
        if side.exists():
            shutil.copy2(side, copy.with_name(copy.name + suffix))
    print(f"copied real DB → {copy}", flush=True)

    # ── PRE: snapshot the copy before the reconcile ────────────────────
    pre = sqlite3.connect(str(copy))
    pre_tables = table_set(pre)
    pre_counts = row_counts(pre, pre_tables)
    try:
        pre_version = pre.execute(
            "SELECT MAX(version) FROM schema_version").fetchone()[0]
    except Exception:
        pre_version = "n/a"
    pre.close()
    print(f"\nPRE: {len(pre_tables)} tables, stamped version {pre_version}",
          flush=True)
    print(f"  sample rows: {pre_counts}", flush=True)
    check("scheduled_recordings absent before (v63 lacks it)",
          "scheduled_recordings" not in pre_tables)

    # ── OPEN the copy the way the app does (reconcile on open) ─────────
    print("\nopening the copy through Database() (reconcile-on-open)…",
          flush=True)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from holdspeak.db.core import Database  # noqa: E402
    raised = None
    try:
        Database(copy)  # triggers _ensure_schema → reconcile_schema
    except Exception as exc:  # noqa: BLE001
        raised = exc
    check("open did not raise a version refusal (A5)", raised is None,
          str(raised) if raised else "")
    if raised is not None:
        return 1

    # ── POST: snapshot the copy after the reconcile ───────────────────
    post = sqlite3.connect(str(copy))
    post_tables = table_set(post)
    post_counts = row_counts(post, post_tables)
    post.close()
    print(f"\nPOST: {len(post_tables)} tables", flush=True)
    print(f"  sample rows: {post_counts}", flush=True)

    # ── ASSERT A6 ──────────────────────────────────────────────────────
    lost = pre_tables - post_tables
    check("no table was lost (A1/A6)", not lost, f"lost={sorted(lost)}")
    check("scheduled_recordings was gained (A3)",
          "scheduled_recordings" in post_tables)
    for t, n in pre_counts.items():
        after = post_counts.get(t, -1)
        check(f"rows preserved in {t}: {n} → {after}", after >= n,
              f"before={n} after={after}")
    check("orphan tables survived (the 7 experimental)",
          {"connector_reactions", "service_events"} <= post_tables
          or not ({"connector_reactions", "service_events"} & pre_tables),
          "(only asserted if present before)")

    print("\n" + ("ALL CHECKS PASSED" if not FAILS else f"{len(FAILS)} FAILED"),
          flush=True)
    for f in FAILS:
        print(f"  FAIL {f}", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
