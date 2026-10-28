"""Programs §5: the gate's verifier reads the LOG, never the exit code.

Six log shapes: green, a red section, a section twice, no verdict line, no
log, a dirty tree. The green log is what ``tests/fixtures/
fake_program_check.sh`` prints under the engine's own header and footer
(the same shape ``scripts/quick_check.sh`` prints).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from holdspeak.services.program_verifier import verify_log, verify_text

FAKE = Path(__file__).resolve().parents[1] / "fixtures" / "fake_program_check.sh"


def _log(env: dict[str, str] | None = None, *, clean: bool = True) -> str:
    out = subprocess.run(["sh", str(FAKE)], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", **(env or {})})
    return (
        "program-check: commit 0123abcd\n"
        + ("program-check: tree clean\n" if clean else "program-check: tree dirty (2 files)\n")
        + f"program-check: command sh {FAKE}\n" + out.stdout + f"program-check: exit {out.returncode}\n"
    )


def test_green() -> None:
    result = verify_text(_log())
    assert result["green"] and result["reasons"] == []
    assert [(row["name"], row["state"]) for row in result["sections"]] == [
        ("build", "green"), ("vitest", "green"), ("pytest", "green"), ("sweep", "green"), ("canon", "green"),
        ("repo", "green"),
    ]
    assert result["commit"] == "0123abcd" and result["clean"] is True and result["exit"] == 0


def test_a_red_section() -> None:
    result = verify_text(_log({"FAKE_CHECK_RED": "1"}))
    assert not result["green"]
    assert "the section pytest is red" in result["reasons"]
    assert "the check's verdict is RED" in result["reasons"]


def test_a_section_twice() -> None:
    text = _log().replace("== repo guards\n", "== repo guards\n   1 passed\n== repo guards\n", 1)
    result = verify_text(text)
    assert "the section repo is in the log twice" in result["reasons"]
    assert not result["green"]


def test_no_verdict_line() -> None:
    text = _log().replace("QUICK CHECK GREEN: merge; the main watcher runs the whole suite.\n", "")
    result = verify_text(text)
    assert result["reasons"] == ["the log does not end with the check's verdict line"]


def test_no_log(tmp_path) -> None:
    assert verify_log(None)["reasons"] == ["the check wrote no log"]
    assert verify_log(str(tmp_path / "gone.log"))["reasons"] == ["the check log is not there"]
    nothing = tmp_path / "empty.log"
    nothing.write_text(
        "program-check: commit 1\nprogram-check: tree clean\nprogram-check: command x\nprogram-check: exit 1\n")
    result = verify_log(str(nothing))
    assert not result["green"]
    assert "the section build is not in the log" in result["reasons"]


def test_a_dirty_tree() -> None:
    result = verify_text(_log(clean=False))
    assert result["reasons"] == ["the worktree had changes that were not committed when the check started"]


def test_a_section_without_a_result_line_and_no_commit() -> None:
    text = _log().replace("   build ok\n", "").replace("program-check: commit 0123abcd\n", "")
    result = verify_text(text)
    assert "the section build has no result line" in result["reasons"]
    assert "the log names no commit" in result["reasons"]
