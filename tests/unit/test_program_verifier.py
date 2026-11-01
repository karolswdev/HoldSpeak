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


# ── PG-REQ §5: the requirement form ─────────────────────────────────

from holdspeak.services.program_verifier import verify_requirement_log, verify_requirement_text  # noqa: E402


def _req_log(body: str, *, exit_code: int = 0, clean: bool = True, footer: bool = True) -> str:
    return ("program-check: commit 0123abcd\n" + ("program-check: tree clean\n" if clean else "program-check: tree dirty (1 files)\n")
            + "program-check: command uv run pytest -q tests/unit/test_x.py\n" + body
            + (f"program-check: exit {exit_code}\n" if footer else ""))


def test_a_requirement_log_is_met_on_the_engines_exit_and_no_red_line() -> None:
    result = verify_requirement_text(_req_log("....\n12 passed in 0.4s\n"))
    assert result["met"] and result["line"] == "12 passed in 0.4s" and result["commit"] == "0123abcd"
    assert verify_requirement_text(_req_log("12 passed\n"), expect=r"\b12 passed\b")["met"]


def test_a_requirement_log_is_not_met_without_its_receipt() -> None:
    assert verify_requirement_text(_req_log("12 passed\n", exit_code=1))["reasons"] == ["the command ended with exit 1"]
    assert "the log has no exit line of the engine" in verify_requirement_text(_req_log("12 passed\n", footer=False))["reasons"]
    red = verify_requirement_text(_req_log("FAILED tests/unit/test_x.py::t\n1 failed, 11 passed\n"))
    assert not red["met"] and any(reason.startswith("a line is red") for reason in red["reasons"])
    assert not verify_requirement_text(_req_log("12 passed\n", clean=False))["met"]
    assert verify_requirement_text(_req_log("11 passed\n"), expect=r"\b12 passed\b")["reasons"] == [r"no line matches \b12 passed\b"]


def test_no_requirement_log_is_never_met(tmp_path) -> None:
    assert verify_requirement_log(None)["reasons"] == ["the command wrote no log"]
    assert verify_requirement_log(str(tmp_path / "nope.log"))["reasons"] == ["the log is not there"]
    (tmp_path / "empty.log").write_text("")
    assert not verify_requirement_log(str(tmp_path / "empty.log"))["met"]


# ── PG-LANG LANG11: the Measure form ─────────────────────────────────

import pytest  # noqa: E402

from holdspeak.services.program_requirements import parse_bound  # noqa: E402
from holdspeak.services.program_verifier import verify_measure_log, verify_measure_text  # noqa: E402


def _measure_log(*lines: str, exit_code: int = 0, clean: bool = True) -> str:
    return ("program-check: commit 0123abcd\n" + ("program-check: tree clean\n" if clean else "program-check: tree dirty (1 files)\n")
            + "program-check: command sh bench.sh\n" + "".join(f"{line}\n" for line in lines)
            + f"program-check: exit {exit_code}\n")


@pytest.mark.parametrize("bound, lines, met, said", [
    ("total under 2 s", ["total 1.4 s"], True, "Measured 1.4 s, under 2 s"),
    ("total < 2 s", ["total 1400 ms"], True, "Measured 1.4 s, under 2 s"),
    ("files at most 3", ["files changed: 3"], True, "Measured 3, at most 3"),
    ("errors equal to 0", ["errors 0"], True, "Measured 0, equal to 0"),
    ("p95 < 100 ms", ["p95 120 ms", "p95 84 ms"], True, "Measured 84 ms, under 100 ms"),  # the last line wins
    ("p95 < 100 ms", ["p95 84 ms", "p95 120 ms"], False, "Measured 120 ms, not under 100 ms"),
    ("rows at least 10", ["rows 9"], False, "Measured 9, not at least 10"),
])
def test_a_measure_reads_the_last_value_and_compares_it_with_its_bound(bound, lines, met, said) -> None:
    result = verify_measure_text(_measure_log(*lines), parse_bound(bound))
    assert (result["met"], result["line"]) == (met, said), result


def test_a_measure_that_did_not_run_says_why_in_words(tmp_path) -> None:
    spec = parse_bound("total < 2 s")
    assert verify_measure_text(_measure_log("total 1 s", exit_code=127), spec)["line"] == \
        "Not measured: the command ended with exit 127"
    assert verify_measure_text(_measure_log("nothing"), spec)["line"] == "Not measured: the command printed no total number"
    assert verify_measure_text(_measure_log("total 1 kb"), spec)["line"] == \
        "Not measured: the command printed kb, which is not s"
    assert verify_measure_log(None, spec)["line"] == "Not measured: the command did not run"
    assert verify_measure_log(str(tmp_path / "gone.log"), spec)["met"] is False
