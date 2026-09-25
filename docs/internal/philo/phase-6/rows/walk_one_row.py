"""Run one actual atlas case and retain its observer rows before rig cleanup.

The graph rig still owns setup, trigger, observation and teardown. This
read-only sidecar counts the actual SQLiteObserver rows; it does not retry
the missing read or change the rig's observation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import hashlib
from pathlib import Path
import sqlite3
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--case", required=True)
    parser.add_argument("--viewport", type=int, choices=(1440, 393), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root))
    # A reused venv's editable install may point at the built lane. The hub
    # child must import the archive under test, not that installed checkout.
    os.environ["PYTHONPATH"] = str(root)
    spec = importlib.util.spec_from_file_location("philo6_row_rig", root / "scripts/graph_walk.py")
    rig = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = rig
    spec.loader.exec_module(rig)
    original_stop = rig.Hub.stop
    retained = {}

    def stop_with_rows(hub):
        if hub.db_path:
            hub._verify_paths()
            db_path = Path(hub.db_path).resolve()
            assert db_path.is_relative_to(hub.home.resolve())
            with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM pipeline_events WHERE error IS NOT NULL "
                    "AND (args_summary LIKE ? OR error LIKE ?) ORDER BY id",
                    ("%philo504-deliberately-absent%", "%philo504-deliberately-absent%"),
                ).fetchall()
            retained.update(db_path=str(db_path), home=str(hub.home),
                            rows=[dict(row) for row in rows], count=len(rows))
        original_stop(hub)

    rig.Hub.stop = stop_with_rows
    record = rig.run_case(
        root / "docs/internal/philo/graph/atlas-phase3.json", args.case,
        brain="astra", viewport=args.viewport, out=args.out.resolve(), engine="none",
        build=False, headless=args.case.endswith(".op"),
    )
    retained.update(case=args.case, viewport=args.viewport,
                    source_root=str(root),
                    route_sha256=hashlib.sha256((root / "holdspeak/web/routes/decisions.py").read_bytes()).hexdigest(),
                    source=record.get("provenance"), rig_verdict=record.get("verdict"),
                    one_cause_one_row=retained.get("count") == 1)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "observer-rows.json").write_text(json.dumps(retained, indent=2) + "\n")
    print(rig.report(record))
    print(json.dumps(retained, indent=2))
    ok = record.get("verdict") == "pass" and retained["one_cause_one_row"]
    print(f"ONE CAUSE ONE ROW: {'PASS' if ok else 'FAIL'} ({retained.get('count')} failure rows; expected 1)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
