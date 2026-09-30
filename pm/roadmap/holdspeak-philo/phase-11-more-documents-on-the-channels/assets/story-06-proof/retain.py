#!/usr/bin/env python3
"""PHILO-11-06: retain every serial walk without overwriting a run.

Usage::

    retain.py <source label dir> <destination label dir> [--obs-only]

The source table is checked against every observation before a destination is
created.  A destination is written once, through a temporary sibling and an
atomic rename; a duplicate row, path escape, mismatched case/width/verdict,
incomplete observation or provenance mismatch refuses the whole retention.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


HEADER = [
    "file", "case", "width", "verdict", "seconds", "load1", "reading", "run_dir",
    "exit_code", "source_revision", "source_dirty",
]
KNOWN_VERDICTS = {"pass", "fail", "blocked", "not_run", "not_applicable"}


class Refused(Exception):
    pass


def rows(src: Path) -> list[list[str]]:
    try:
        lines = (src / "runs.tsv").read_text().splitlines()
    except OSError as exc:
        raise Refused(f"{src}/runs.tsv is unreadable: {exc}") from exc
    if not lines or lines[0].split("\t")[: len(HEADER)] != HEADER:
        raise Refused(f"{src}/runs.tsv has no PHILO-11-06 rig header")
    result = [line.split("\t") for line in lines[1:] if line.strip()]
    if not result:
        raise Refused(f"{src}/runs.tsv holds no run")
    return result


def _relative_run(src: Path, value: str, case: str, width: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 2:
        raise Refused(f"row {case} {width}: run_dir {value!r} is not <case>--<width>/<run id>")
    if path.parts[0] != f"{case}--{width}":
        raise Refused(f"row {case} {width}: run_dir {value!r} names another case or width")
    resolved = (src / path).resolve()
    try:
        resolved.relative_to(src.resolve())
    except ValueError as exc:
        raise Refused(f"row {case} {width}: run_dir escapes source") from exc
    if not resolved.is_dir() or resolved.is_symlink():
        raise Refused(f"{value}: run directory is missing or symlinked")
    return resolved


def _observation(src: Path, row: list[str]) -> tuple[dict, Path]:
    if len(row) < len(HEADER):
        raise Refused(f"runs.tsv row has {len(row)} fields, expected {len(HEADER)}: {row!r}")
    _file, case, width, verdict, _seconds, _load, _reading, run_dir, _exit, revision, dirty = row[:11]
    if verdict not in KNOWN_VERDICTS:
        raise Refused(f"{run_dir}: unknown verdict {verdict!r}")
    run_path = _relative_run(src, run_dir, case, width)
    observation_path = run_path / "observation.json"
    if not observation_path.is_file() or observation_path.is_symlink():
        raise Refused(f"{run_dir}: observation.json is missing or symlinked")
    try:
        observation = json.loads(observation_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Refused(f"{run_dir}: observation.json is unreadable: {exc}") from exc
    if observation.get("case_id") != case:
        raise Refused(f"{run_dir}: observation case {observation.get('case_id')!r}, row {case!r}")
    if observation.get("brain") != "astra":
        raise Refused(f"{run_dir}: observation brain {observation.get('brain')!r}, expected 'astra'")
    if width == "op":
        if observation.get("viewport") != 1440:
            raise Refused(f"{run_dir}: operation viewport is {observation.get('viewport')!r}")
    elif observation.get("viewport") != int(width):
        raise Refused(f"{run_dir}: observation viewport {observation.get('viewport')!r}, row {width}")
    if observation.get("verdict") != verdict:
        raise Refused(f"{run_dir}: observation verdict {observation.get('verdict')!r}, row {verdict!r}")
    if not observation.get("complete"):
        raise Refused(f"{run_dir}: observation is incomplete")
    provenance = observation.get("provenance")
    if not isinstance(provenance, dict):
        raise Refused(f"{run_dir}: observation has no provenance")
    if str(provenance.get("revision")) != revision:
        raise Refused(f"{run_dir}: source revision differs between row and observation")
    if str(bool(provenance.get("dirty"))).lower() != dirty:
        raise Refused(f"{run_dir}: source dirty flag differs between row and observation")
    if verdict == "not_applicable":
        return observation, run_path
    db_path = provenance.get("db_path")
    hub_home = (provenance.get("hub") or {}).get("home")
    if not isinstance(db_path, str) or not isinstance(hub_home, str):
        raise Refused(f"{run_dir}: provenance has no hub HOME and db path")
    try:
        Path(db_path).resolve().relative_to(Path(hub_home).resolve())
    except ValueError as exc:
        raise Refused(f"{run_dir}: db path escapes the hub HOME") from exc
    return observation, run_path


def retain(src: Path, dest: Path, *, obs_only: bool = False) -> int:
    src = src.resolve()
    dest = dest.resolve()
    if dest.exists():
        raise Refused(f"{dest} already exists: a label is written once")
    table = rows(src)
    seen: set[str] = set()
    checked: list[tuple[list[str], Path]] = []
    for row in table:
        if len(row) < len(HEADER):
            raise Refused(f"runs.tsv row has {len(row)} fields, expected {len(HEADER)}: {row!r}")
        run_dir = row[7]
        if run_dir in seen:
            raise Refused(f"two rows name one run directory {run_dir!r}")
        seen.add(run_dir)
        _observation_record, path = _observation(src, row)
        checked.append((row, path))
    # Validate the source directory shape before copying.  A stray nested run
    # is evidence that the conductor and table diverged, so retain refuses it.
    on_disk = {
        f"{parent.name}/{child.name}"
        for parent in src.iterdir() if parent.is_dir() and parent.name != "__pycache__"
        for child in parent.iterdir() if child.is_dir()
    }
    if on_disk != seen:
        raise Refused(f"retention mismatch: table names {len(seen)} runs, disk has {len(on_disk)}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_name = tempfile.mkdtemp(prefix=f".{dest.name}.", dir=str(dest.parent))
    temp = Path(temp_name)
    try:
        shutil.copy2(src / "runs.tsv", temp / "runs.tsv")
        for row, path in checked:
            into = temp / row[7]
            into.parent.mkdir(parents=True, exist_ok=True)
            if obs_only:
                into.mkdir()
                shutil.copy2(path / "observation.json", into / "observation.json")
                if (path / "rig.log").exists():
                    shutil.copy2(path / "rig.log", into / "rig.log")
            else:
                shutil.copytree(path, into)
        copied = {
            f"{parent.name}/{child.name}"
            for parent in temp.iterdir() if parent.is_dir()
            for child in parent.iterdir() if child.is_dir()
        }
        observations = list(temp.glob("*/*/observation.json"))
        if copied != seen or len(observations) != len(table):
            raise Refused(
                f"retention mismatch after copy: {len(table)} rows, "
                f"{len(copied)} run directories, {len(observations)} observations"
            )
        os.replace(temp, dest)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    print(f"retained: {len(table)} rows, {len(seen)} run directories, "
          f"{len(table)} observations -> {dest}")
    return len(table)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    obs_only = "--obs-only" in args
    args = [arg for arg in args if arg != "--obs-only"]
    if len(args) != 2:
        print(__doc__)
        return 1
    try:
        retain(Path(args[0]), Path(args[1]), obs_only=obs_only)
    except Refused as exc:
        print(f"RETENTION REFUSED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
