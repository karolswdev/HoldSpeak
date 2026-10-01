#!/usr/bin/env python3
"""PHILO-11-06: walk atlas cases one at a time and read each result.

The Phase 10 runner used a thread pool.  That is useful for throughput, but
it makes a failed hub and a retained observation hard to associate with the
case that produced it.  This runner is deliberately a small serial conductor:
one ``graph_walk.py run`` process owns one hub, one fresh HOME and one
``case x width x run`` directory.  It reads and validates that run's
``observation.json`` (including provenance) before starting the next case.

Usage::

    rig_run.py <label> [--case ID ...] [--root DIR]
        [--source-revision REV] [--source-dirty true|false]
        [--out .tmp/philo11-06] atlas-phase11.json ...

Face cases run at their declared widths (normally 1440 and 393).  Operation
cases run once with ``--headless``.  The process exits 1 when any case is not
``pass``; it exits 2 when the retention shape or provenance is invalid.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[6]
ROOT = REPO
KNOWN_VERDICTS = {"pass", "fail", "blocked", "not_run", "not_applicable"}
RUNS_HEADER = [
    "file", "case", "width", "verdict", "seconds", "load1", "reading", "run_dir",
    "exit_code", "source_revision", "source_dirty",
]


class HarnessError(RuntimeError):
    """A retention or provenance error, rather than a product verdict."""


@dataclass(frozen=True)
class PlannedRun:
    atlas: str
    case: str
    width: int
    headless: bool
    replayed: bool = False

    @property
    def width_label(self) -> str:
        return "op" if self.headless else str(self.width)

    @property
    def label(self) -> str:
        return f"{self.case}--{self.width_label}"


def _atlas_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def plan(files: Iterable[str], only: set[str] | None = None) -> list[PlannedRun]:
    """Expand atlas cases in file order, never parallelizing or reordering."""
    selected = only or set()
    runs: list[PlannedRun] = []
    for filename in files:
        atlas_path = _atlas_path(filename)
        atlas = json.loads(atlas_path.read_text())
        for case in atlas.get("cases", []):
            case_id = str(case["id"])
            if selected and case_id not in selected:
                continue
            widths = case.get("viewports") or []
            replayed = any(step.get("kind") == "boundary" and step.get("substitute") == "engine_reply"
                           for step in case.get("setup", []) if isinstance(step, dict))
            if widths:
                runs.extend(PlannedRun(filename, case_id, int(width), False, replayed) for width in widths)
            else:
                runs.append(PlannedRun(filename, case_id, 1440, True, replayed))
    return runs


def _safe_relative(path: str, *, base: Path) -> Path:
    """Resolve a run path and reject traversal or symlink escapes."""
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise HarnessError(f"run_dir is not relative: {path!r}")
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise HarnessError(f"run_dir escapes the label: {path!r}") from exc
    return resolved


def _run_dirs(label_dir: Path) -> list[Path]:
    return sorted(path for path in label_dir.iterdir() if path.is_dir()) if label_dir.exists() else []


def _observation_for(label_dir: Path, row: list[str], *, expected_revision: str | None,
                     expected_dirty: bool | None, brain: str) -> tuple[dict[str, Any], str]:
    if len(row) < len(RUNS_HEADER):
        raise HarnessError(f"runs.tsv row has {len(row)} fields, expected {len(RUNS_HEADER)}: {row!r}")
    _file, case_id, width, verdict, _seconds, _load, _reading, run_dir, exit_code, revision, dirty = row[:11]
    expected_parent = f"{case_id}--{width}"
    run_path = _safe_relative(run_dir, base=label_dir)
    parts = Path(run_dir).parts
    if len(parts) != 2 or parts[0] != expected_parent:
        raise HarnessError(
            f"row {case_id} {width}: run_dir {run_dir!r} is not "
            "<case>--<width>/<run id>"
        )
    if not run_path.is_dir() or run_path.is_symlink():
        raise HarnessError(f"{run_dir}: run directory is missing or symlinked")
    observation_path = run_path / "observation.json"
    if not observation_path.is_file() or observation_path.is_symlink():
        raise HarnessError(f"{run_dir}: observation.json is missing or symlinked")
    try:
        observation = json.loads(observation_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"{run_dir}: observation.json is unreadable: {exc}") from exc
    if observation.get("case_id") != case_id:
        raise HarnessError(f"{run_dir}: observation case {observation.get('case_id')!r}, row {case_id!r}")
    if observation.get("brain") != brain:
        raise HarnessError(f"{run_dir}: observation brain {observation.get('brain')!r}, expected {brain!r}")
    if width == "op":
        if observation.get("viewport") != 1440:
            raise HarnessError(f"{run_dir}: operation observation viewport {observation.get('viewport')!r}")
    elif observation.get("viewport") != int(width):
        raise HarnessError(f"{run_dir}: observation viewport {observation.get('viewport')!r}, row {width}")
    if observation.get("verdict") != verdict or verdict not in KNOWN_VERDICTS:
        raise HarnessError(
            f"{run_dir}: observation verdict {observation.get('verdict')!r}, row {verdict!r}"
        )
    if not observation.get("complete"):
        raise HarnessError(f"{run_dir}: observation is incomplete")
    provenance = observation.get("provenance")
    if not isinstance(provenance, dict):
        raise HarnessError(f"{run_dir}: observation has no provenance object")
    actual_revision = str(provenance.get("revision"))
    actual_dirty = bool(provenance.get("dirty"))
    if revision != actual_revision or dirty != str(actual_dirty).lower():
        raise HarnessError(
            f"{run_dir}: runs.tsv provenance {revision!r}/{dirty!r}, "
            f"observation {actual_revision!r}/{actual_dirty!r}"
        )
    if expected_revision is not None and actual_revision != expected_revision:
        raise HarnessError(f"{run_dir}: source revision {actual_revision!r}, expected {expected_revision!r}")
    if expected_dirty is not None and actual_dirty is not expected_dirty:
        raise HarnessError(f"{run_dir}: source dirty={actual_dirty}, expected {expected_dirty}")
    # A declared not-applicable case is recorded before a hub is booted, so
    # its truthful skeleton has no DB path or hub HOME.  Every attempted case
    # still needs both fields below; accepting a missing hub for ``not_run``
    # would turn a boot crash into an apparent result.
    if observation.get("verdict") == "not_applicable":
        return observation, run_dir
    db_path = provenance.get("db_path")
    home = (provenance.get("hub") or {}).get("home")
    if not isinstance(db_path, str) or not isinstance(home, str):
        raise HarnessError(f"{run_dir}: provenance has no hub HOME and db path")
    try:
        Path(db_path).resolve().relative_to(Path(home).resolve())
    except ValueError as exc:
        raise HarnessError(f"{run_dir}: db path {db_path!r} escapes hub HOME {home!r}") from exc
    return observation, run_dir


def _reading(observation: dict[str, Any], output: str) -> str:
    def one_line(value: Any) -> str:
        # A predicate often includes a pretty-printed selector/rect.  The
        # table is TSV: embedded newlines would turn one run into several
        # physical rows and corrupt retention.
        return " ".join(str(value).split())[:300]

    notes = [str(note) for note in observation.get("notes", []) if note]
    if notes:
        return one_line(notes[-1])
    for section in ("terminal_outcome", "initial_feedback"):
        value = observation.get(section) or {}
        if isinstance(value, dict) and value.get("reading"):
            return one_line(value["reading"])
    return one_line(output.strip().splitlines()[-1] if output.strip() else "")


def one(run: PlannedRun, label_dir: Path, *, brain: str, expected_revision: str | None,
        expected_dirty: bool | None, python_bin: Path) -> list[str]:
    """Run exactly one case, then read its observation before returning."""
    run_root = label_dir / run.label
    if run_root.exists():
        if any(run_root.iterdir()):
            raise HarnessError(f"{run_root} already holds a run: refusing to mix captures")
        run_root.rmdir()
    run_root.mkdir(parents=True)
    run_home = Path(tempfile.mkdtemp(prefix="philo11-walk-home-"))
    env = dict(os.environ)
    env["HOME"] = str(run_home)
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / "Library/Caches/ms-playwright"))
    # The child is invoked by an absolute script path, so Python puts
    # ``scripts/`` (rather than the product root) on sys.path.  Always prepend
    # the selected product root, including the normal checkout, or the hub
    # dies before it can write a truthful observation.
    env["PYTHONPATH"] = f"{ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(os.pathsep)
    if expected_revision is not None:
        env["HOLDSPEAK_SOURCE_REVISION"] = expected_revision
    if expected_dirty is not None:
        env["HOLDSPEAK_SOURCE_DIRTY"] = str(expected_dirty).lower()
    atlas_arg = run.atlas if Path(run.atlas).is_absolute() else run.atlas
    command = [
        str(python_bin), str(ROOT / "scripts/graph_walk.py"), "run",
        "--atlas", atlas_arg, "--case", run.case, "--brain", brain,
        "--viewport", str(run.width), "--no-build", "--out", str(run_root),
        "--engine", "replayed" if run.replayed else "none",
    ]
    if run.headless:
        command.append("--headless")
    started = time.monotonic()
    try:
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        output = process.stdout + process.stderr
        run_dirs = _run_dirs(run_root)
        if len(run_dirs) != 1:
            raise HarnessError(f"{run.label}: expected one graph-walk run directory, got {len(run_dirs)}")
        observation_path = run_dirs[0] / "observation.json"
        if not observation_path.is_file():
            raise HarnessError(f"{run.label}: graph-walk produced no observation.json")
        observation = json.loads(observation_path.read_text())
        (run_dirs[0] / "rig.log").write_text(output)
        # Validate now, before the conductor starts the next hub.
        _, run_dir = _observation_for(
            label_dir, [Path(run.atlas).name, run.case, run.width_label,
                        str(observation.get("verdict")), "0", "0", "", f"{run.label}/{run_dirs[0].name}",
                        str(process.returncode), str((observation.get("provenance") or {}).get("revision")),
                        str(bool((observation.get("provenance") or {}).get("dirty"))).lower()],
            expected_revision=expected_revision, expected_dirty=expected_dirty, brain=brain,
        )
        revision = str(observation["provenance"]["revision"])
        dirty = str(bool(observation["provenance"]["dirty"])).lower()
        reading = _reading(observation, output)
        return [Path(run.atlas).name, run.case, run.width_label, str(observation["verdict"]),
                str(round(time.monotonic() - started, 3)), f"{os.getloadavg()[0]:.2f}", reading,
                run_dir, str(process.returncode), revision, dirty]
    except (OSError, json.JSONDecodeError, HarnessError) as exc:
        # Keep the process output in the run-specific directory so a malformed
        # or missing observation is a visible harness failure, never a pass.
        (run_root / "rig.log").write_text(output if "output" in locals() else repr(exc))
        raise
    finally:
        shutil.rmtree(run_home, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--out", default=".tmp/philo11-06")
    parser.add_argument("--root", default=None)
    parser.add_argument("--brain", default="astra", choices=("astra", "muaddib"))
    parser.add_argument("--python", dest="python_bin", default=sys.executable)
    parser.add_argument("--source-revision")
    parser.add_argument("--source-dirty", choices=("true", "false"), default=None)
    args = parser.parse_args(argv)
    global ROOT
    if args.root:
        ROOT = Path(args.root).resolve()
        if not args.source_revision:
            raise SystemExit("--root is an archive/product root; --source-revision is required")
    expected_dirty = None if args.source_dirty is None else args.source_dirty == "true"
    python_bin = Path(args.python_bin).absolute()
    if not python_bin.is_file():
        raise SystemExit(f"Python executable not found: {python_bin}")
    probe = subprocess.run(
        [str(python_bin), "-c", (
            "import sys; raise SystemExit(sys.prefix == sys.base_prefix "
            "or sys.version_info[:2] != (3, 13))"
        )],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        raise SystemExit(f"Python executable is not the repository's isolated Python 3.13 toolchain: {python_bin}")
    label_dir = (REPO / args.out / args.label).resolve()
    if label_dir.exists():
        raise SystemExit(f"{label_dir} already exists: choose a new label")
    label_dir.mkdir(parents=True)
    runs = plan(args.files, set(args.case))
    print(f"{len(runs)} runs, strictly sequential; out {label_dir}", flush=True)
    rows: list[list[str]] = []
    errors: list[str] = []
    (label_dir / "runs.tsv").write_text("\t".join(RUNS_HEADER) + "\n")
    for index, run in enumerate(runs, start=1):
        print(f"[{index}/{len(runs)}] {run.case} {run.width_label}: starting", flush=True)
        try:
            row = one(run, label_dir, brain=args.brain,
                      expected_revision=args.source_revision, expected_dirty=expected_dirty,
                      python_bin=python_bin)
        except (HarnessError, OSError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            print(f"HARNESS ERROR: {exc}", flush=True)
            # A missing or mismatched observation invalidates the association
            # between this case and the next one.  Stop and leave the partial
            # table plus the failing run directory for diagnosis.
            break
        rows.append(row)
        (label_dir / "runs.tsv").write_text(
            "\n".join("\t".join(item) for item in [RUNS_HEADER, *rows]) + "\n"
        )
        print("\t".join(row), flush=True)
    actual_dirs = {f"{parent.name}/{child.name}" for parent in label_dir.iterdir() if parent.is_dir()
                   for child in parent.iterdir() if child.is_dir()}
    named_dirs = {row[7] for row in rows}
    if errors or named_dirs != actual_dirs or len(rows) != len(runs):
        print(f"RETENTION ERROR: {len(rows)}/{len(runs)} rows; errors={len(errors)}", flush=True)
        return 2
    passed = sum(row[3] == "pass" for row in rows)
    print(f"TOTAL {len(rows)} runs: {passed} pass, {len(rows) - passed} not pass", flush=True)
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
