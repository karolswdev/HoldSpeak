#!/usr/bin/env python3
"""Run the eight Phase 108 machine closeout beats in one session."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import NamedTuple

_REPO = Path(__file__).resolve().parents[1]


class Beat(NamedTuple):
    label: str
    commands: tuple[tuple[str, ...], ...]
    environment: tuple[tuple[str, str], ...] = ()


BEATS = (
    Beat(
        "B1 warrant forgery/replay/payload/focus confinement",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "tests/unit/test_privileged_desktop_executor.py",
                "tests/unit/test_typer.py",
            ),
        ),
    ),
    Beat(
        "B2 real desktop act through the spawned executor",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "python",
                "scripts/phase108_desktop_metal.py",
            ),
        ),
    ),
    Beat(
        "B3 terminal text and keys universally enter process.input",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "tests/unit/test_process_input_kernel.py",
                "tests/unit/test_web_routes_coders_steer.py",
            ),
        ),
    ),
    Beat(
        "B4 CLI reads require an authenticated principal before subprocess",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "tests/unit/test_activity_github.py",
                "tests/unit/test_activity_jira.py",
                "tests/unit/test_pipeline_runner.py",
                "tests/unit/test_web_routes_missioncontrol.py",
            ),
        ),
    ),
    Beat(
        "B5 generic claim and execution liveness terminalize",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "tests/unit/test_kernel_broker.py",
            ),
        ),
    ),
    Beat(
        "B6 live browser bus is mandatory and unskipped",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "tests/e2e/test_live_bus.py",
            ),
        ),
        (("HOLDSPEAK_REQUIRE_LIVE_BUS", "1"),),
    ),
    Beat(
        "B7 empty register, confinement fence, CI and docs agree",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "tests/unit/test_kernel_effect_fence.py",
                "tests/unit/test_live_bus_ci_gate.py",
                "tests/unit/test_doc_drift_guard.py",
            ),
        ),
    ),
    Beat(
        "B8 complete Python and web sweeps",
        (
            (
                "uv",
                "run",
                "--extra",
                "test",
                "pytest",
                "-q",
                "--ignore=tests/e2e/test_metal.py",
            ),
            ("npm", "--prefix", "web", "run", "check"),
        ),
    ),
)


def _run(command: tuple[str, ...], environment: tuple[tuple[str, str], ...]) -> bool:
    print("COMMAND", " ".join(command), flush=True)
    env = os.environ.copy()
    env.update(environment)
    completed = subprocess.run(
        command,
        cwd=_REPO,
        env=env,
        check=False,
        text=True,
    )
    return completed.returncode == 0


def main() -> int:
    passed = 0
    for label, commands, environment in BEATS:
        print(f"\n=== {label} ===", flush=True)
        ok = all(_run(command, environment) for command in commands)
        print(("PASS" if ok else "FAIL"), label, flush=True)
        passed += int(ok)
    print(f"\n{passed}/{len(BEATS)} machine beats passed", flush=True)
    return 0 if passed == len(BEATS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
