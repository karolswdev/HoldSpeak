#!/usr/bin/env python3
"""PHILO-9-05: run every case of the named atlas files through the rig.

Each face case runs at each width it declares (1440, 393); a case with no
viewports (an operation case) runs once, headless. Every run is its own
`scripts/graph_walk.py run` process: its own hub, its own mkdtemp HOME, its
own port, `--engine none`, `--no-build` (the caller builds the bundle first).

Usage: rig_run.py <label> [--jobs N] [--case ID ...] [--root DIR] <atlas.json> ...
--root runs the product of an export (git archive) at DIR: cwd and PYTHONPATH
are DIR, whose web bundle the caller built; the caller copies this branch's
rig (scripts/graph_walk.py) and the named atlas files in (red_main.sh).
Writes <out>/<label>/runs.tsv: file, case, width, verdict, seconds, load1,
the rig's reading (first 300 chars). Exit 1 when any run is not `pass`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]


ROOT = REPO


def plan(files: list[str], only: set[str]) -> list[tuple[str, str, int, bool]]:
    runs = []
    for f in files:
        atlas = json.loads((ROOT / f).read_text())
        for case in atlas["cases"]:
            if only and case["id"] not in only:
                continue
            widths = case.get("viewports") or []
            if widths:
                runs += [(f, case["id"], w, False) for w in widths]
            else:
                runs.append((f, case["id"], 1440, True))
    return runs


def one(run: tuple[str, str, int, bool], out: Path) -> list[str]:
    f, cid, width, headless = run
    env = dict(os.environ)
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / "Library/Caches/ms-playwright"))
    if ROOT != REPO:
        env["PYTHONPATH"] = str(ROOT)
    cmd = [str(REPO / ".venv/bin/python"), "scripts/graph_walk.py", "run", "--atlas", f, "--case", cid,
           "--brain", "muaddib", "--viewport", str(width), "--no-build", "--out", str(out)]
    if headless:
        cmd.append("--headless")
    load = os.getloadavg()[0]
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    secs = round(time.monotonic() - started)
    text = proc.stdout + proc.stderr
    verdict = next((line.split()[1] for line in text.splitlines() if line.startswith("VERDICT:")), "error")
    notes = [line[6:] for line in text.splitlines() if line.startswith("NOTE: predicate") or line.startswith("NOTE: BLOCKED")
             or "BLOCKED" in line[:20]]
    reading = (notes[-1] if notes else text.strip().splitlines()[-1] if text.strip() else "").replace("\t", " ")[:300]
    return [Path(f).name, cid, "op" if headless else str(width), verdict, str(secs), f"{load:.2f}", reading]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--out", default=".tmp/s05")
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    global ROOT
    if args.root:
        ROOT = Path(args.root).resolve()
    out = REPO / args.out / args.label
    out.mkdir(parents=True, exist_ok=True)
    runs = plan(args.files, set(args.case))
    print(f"{len(runs)} runs, {args.jobs} at a time; out {out}", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(lambda r: one(r, out), runs):
            rows.append(row)
            print("\t".join(row), flush=True)
    header = ["file", "case", "width", "verdict", "seconds", "load1", "reading"]
    (out / "runs.tsv").write_text("\n".join("\t".join(r) for r in [header, *rows]) + "\n")
    passed = sum(r[3] == "pass" for r in rows)
    print(f"TOTAL {len(rows)} runs: {passed} pass, {len(rows) - passed} not pass")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
