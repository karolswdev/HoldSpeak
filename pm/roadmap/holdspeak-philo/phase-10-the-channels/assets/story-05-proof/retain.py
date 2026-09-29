#!/usr/bin/env python3
"""PHILO-10-05: the evidence copier -- keep every claimed run, keyed by case x width x run.

Phase 9's lesson (Codex Astra r1 on #688, finding 1): a copier keyed by the
batch let each run overwrite the last (1 of 28 kept). Here every row of the
rig's runs.tsv names its OWN run directory (`<case>--<width>/<run id>`); the
copier:

* refuses a destination label that already exists (a label is written once;
  never a silent `rm -rf` of an earlier capture);
* refuses two rows that name one run directory, a row whose directory is not
  `<case>--<width>/<run id>` of THAT row, and a run directory that exists;
* checks each observation.json names the row's case, width and verdict, all
  BEFORE anything is written (a refusal leaves no partial label);
* counts rows = directories = observations, or refuses.

Usage: retain.py <source label dir> <destination label dir> [--obs-only]
Exit 0 when every row is kept; 1 (with the reason) otherwise.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


class Refused(Exception):
    pass


def rows(src: Path) -> list[list[str]]:
    lines = (src / "runs.tsv").read_text().splitlines()
    if not lines or lines[0].split("\t")[:8] != ["file", "case", "width", "verdict", "seconds", "load1", "reading", "run_dir"]:
        raise Refused(f"{src}/runs.tsv has no rig header")
    return [line.split("\t") for line in lines[1:] if line.strip()]


def retain(src: Path, dest: Path, obs_only: bool = False) -> int:
    if dest.exists():
        raise Refused(f"{dest} already exists: a label is written once (choose a new label)")
    table = rows(src)
    if not table:
        raise Refused(f"{src}/runs.tsv holds no run")
    seen: set[str] = set()
    for row in table:
        _file, case, width, _verdict, *_rest, run_dir = row
        key = run_dir.split("/")[0] if "/" in run_dir else ""
        if key != f"{case}--{width}" or run_dir.count("/") != 1:
            raise Refused(f"row {case} {width}: run_dir {run_dir!r} is not <case>--<width>/<run id>")
        if run_dir in seen:
            raise Refused(f"two rows name one run directory {run_dir!r}")
        seen.add(run_dir)
        obs = json.loads((src / run_dir / "observation.json").read_text())
        # rig_run.py writes `error` when the run printed no VERDICT line (the hub
        # died at boot); its observation then says `not_run`. Only that pair maps.
        same = obs.get("verdict") == _verdict or (_verdict == "error" and obs.get("verdict") == "not_run")
        if obs.get("case_id") != case or not same:
            raise Refused(f"{run_dir}: observation says {obs.get('case_id')} {obs.get('verdict')}, the row {case} {_verdict}")
        if width != "op" and obs.get("viewport") != int(width):
            raise Refused(f"{run_dir}: observation viewport {obs.get('viewport')}, the row {width}")
    dest.mkdir(parents=True)
    shutil.copy2(src / "runs.tsv", dest / "runs.tsv")
    for row in table:
        _file, case, width, verdict, *_rest, run_dir = row
        into = dest / run_dir
        if into.exists():
            raise Refused(f"{into} already exists: refusing to mix two runs")
        into.mkdir(parents=True)
        if obs_only:
            shutil.copy2(src / run_dir / "observation.json", into / "observation.json")
        else:
            shutil.copytree(src / run_dir, into, dirs_exist_ok=True)
    kept = sorted(f"{p.parent.name}/{p.name}" for p in dest.glob("*/*") if p.is_dir())
    observations = list(dest.glob("*/*/observation.json"))
    if kept != sorted(seen) or len(observations) != len(table):
        raise Refused(f"retention mismatch: {len(table)} rows, {len(kept)} directories, {len(observations)} observations")
    print(f"retained: {len(table)} rows, {len(kept)} run directories, {len(observations)} observations -> {dest}")
    return len(table)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 1
    try:
        retain(Path(args[0]), Path(args[1]), obs_only="--obs-only" in argv)
    except Refused as exc:
        print(f"RETENTION REFUSED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
