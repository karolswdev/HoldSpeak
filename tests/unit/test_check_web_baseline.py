"""The web baseline checker with an EMPTY baseline (2026-10-03: all four
inherited failures healed, so ``tests/web-inherited-baseline.txt`` holds no
entry). The real script runs as a process on a vitest results file."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check_web_baseline.py"
TRACKED_BASELINE = REPO / "tests" / "web-inherited-baseline.txt"


def _results(tmp_path: Path, *, failed: bool) -> Path:
    """A vitest ``--reporter=json`` result with one passing test and, when
    asked, one failing test."""
    assertions = [{"status": "passed", "ancestorTitles": ["suite"], "title": "passes"}]
    if failed:
        assertions.append({"status": "failed", "ancestorTitles": ["suite"], "title": "fails"})
    path = tmp_path / "results.json"
    path.write_text(json.dumps({
        "numPassedTests": 1,
        "numFailedTests": 1 if failed else 0,
        "numPendingTests": 0,
        "numTodoTests": 0,
        "testResults": [{
            "name": str(REPO / "web" / "src" / "example.test.ts"),
            "assertionResults": assertions,
        }],
    }))
    return path


def _check(results: Path, baseline: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(results), "--baseline", str(baseline)],
        capture_output=True, text=True,
    )


def test_the_tracked_baseline_holds_no_entry() -> None:
    entries = [
        line for line in TRACKED_BASELINE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert entries == []


def test_an_empty_baseline_and_a_passing_run_exit_0(tmp_path: Path) -> None:
    done = _check(_results(tmp_path, failed=False), TRACKED_BASELINE)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "zero branch-new" in done.stdout


def test_an_empty_baseline_and_one_failing_test_exit_1(tmp_path: Path) -> None:
    done = _check(_results(tmp_path, failed=True), TRACKED_BASELINE)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "BRANCH-NEW: src/example.test.ts > suite > fails" in done.stdout
    assert "VERDICT: BRANCH-NEW FAILURES: 1" in done.stdout


def test_a_missing_baseline_file_is_still_an_error(tmp_path: Path) -> None:
    done = _check(_results(tmp_path, failed=False), tmp_path / "no-such-file.txt")
    assert done.returncode == 2
    assert "missing" in done.stderr
