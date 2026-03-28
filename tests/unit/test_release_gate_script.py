"""Tests for release gate checklist script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "release_gate.py"


def test_release_gate_passes_when_all_items_checked(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text(
        "- [x] Item A\n"
        "- [X] Item B\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_script_path()), "--checklist", str(checklist)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RELEASE GATE PASSED" in result.stdout


def test_release_gate_fails_when_items_unchecked(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text(
        "- [x] Item A\n"
        "- [ ] Item B\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_script_path()), "--checklist", str(checklist)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "RELEASE GATE FAILED" in result.stdout
    assert "Item B" in result.stdout
