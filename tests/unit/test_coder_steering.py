"""coder_steering peek tests (HS-87-01).

Everything runs against a fake runner — no tmux, no subprocess. The
peek's typed statuses, the content-hash gate, ANSI stripping, and the
caps are pinned here; the live capture against a real pane is the
story's integration evidence.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

from holdspeak import coder_steering
from holdspeak.coder_steering import (
    PEEK_MAX_BYTES,
    awaiting_snapshot,
    awaiting_transitions,
    content_hash,
    peek_pane,
    resolve_pane_target,
    strip_ansi,
)


def _completed(stdout: str = "", returncode: int = 0, stderr: str = ""):
    return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)


def _runner_returning(result):
    calls: list[list[str]] = []

    def run(argv, cwd=None):
        calls.append(argv)
        return result

    run.calls = calls
    return run


# --- peek_pane -----------------------------------------------------------


def test_peek_live_returns_lines_and_hash() -> None:
    run = _runner_returning(_completed("one\ntwo\nthree\n"))
    result = peek_pane("%5", runner=run)
    assert result["status"] == "live"
    assert result["lines"] == ["one", "two", "three"]
    assert result["hash"] == content_hash("one\ntwo\nthree")


def test_peek_invokes_capture_pane_with_the_pinned_flags() -> None:
    run = _runner_returning(_completed("x"))
    peek_pane("%5", lines=50, runner=run)
    assert run.calls == [
        ["tmux", "capture-pane", "-p", "-e", "-t", "%5", "-S", "-50"]
    ]


def test_peek_hash_gate_answers_not_modified_without_a_body() -> None:
    run = _runner_returning(_completed("same\ncontent"))
    first = peek_pane("%5", runner=run)
    second = peek_pane("%5", last_hash=first["hash"], runner=run)
    assert second == {"status": "not_modified", "hash": first["hash"]}
    assert "lines" not in second


def test_peek_changed_content_reopens_the_gate() -> None:
    first = peek_pane("%5", runner=_runner_returning(_completed("before")))
    second = peek_pane(
        "%5", last_hash=first["hash"], runner=_runner_returning(_completed("after"))
    )
    assert second["status"] == "live"
    assert second["lines"] == ["after"]


def test_peek_strips_ansi_and_osc_sequences() -> None:
    raw = "\x1b[31mred\x1b[0m and \x1b]0;title\x07plain\x1b[?25l"
    run = _runner_returning(_completed(raw))
    result = peek_pane("%5", runner=run)
    assert result["lines"] == ["red and plain"]


def test_peek_caps_the_body_and_keeps_the_tail() -> None:
    body = "\n".join(f"line-{i:07d}" for i in range(12_000))
    assert len(body.encode()) > PEEK_MAX_BYTES
    result = peek_pane("%5", runner=_runner_returning(_completed(body)))
    joined = "\n".join(result["lines"])
    assert len(joined.encode()) <= PEEK_MAX_BYTES
    assert result["lines"][-1] == "line-0011999"  # the newest survives
    assert result["lines"][0].startswith("line-")  # no half line at the head


def test_peek_dead_pane_is_pane_gone_not_an_exception() -> None:
    run = _runner_returning(_completed(returncode=1, stderr="can't find pane %5"))
    result = peek_pane("%5", runner=run)
    assert result == {"status": "pane_gone", "detail": "can't find pane %5"}


def test_peek_timeout_is_a_typed_error() -> None:
    def run(argv, cwd=None):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=5)

    result = peek_pane("%5", runner=run)
    assert result["status"] == "error"


def test_peek_without_tmux_is_tmux_absent(monkeypatch) -> None:
    monkeypatch.setattr(coder_steering.shutil, "which", lambda _name: None)
    assert peek_pane("%5") == {"status": "tmux_absent"}


def test_peek_clamps_the_lines_argument() -> None:
    run = _runner_returning(_completed("x"))
    peek_pane("%5", lines=99_999, runner=run)
    assert run.calls[0][-1] == f"-{coder_steering.PEEK_MAX_LINES}"


# --- strip_ansi / resolve_pane_target ------------------------------------


def test_strip_ansi_handles_st_terminated_osc() -> None:
    assert strip_ansi("a\x1b]8;;http://x\x1b\\b") == "ab"


def _session(**kw):
    base = {
        "agent": "claude",
        "session_id": "abc",
        "awaiting_response": False,
        "tmux_pane": None,
        "tmux_session": None,
        "tmux_window": None,
        "tmux_pane_index": None,
    }
    base.update(kw)
    return SimpleNamespace(**base)


def test_resolve_pane_target_prefers_the_unique_pane_id() -> None:
    s = _session(tmux_pane="%7", tmux_session="hs", tmux_window="1", tmux_pane_index="0")
    assert resolve_pane_target(s) == "%7"


def test_resolve_pane_target_composes_the_address_fallback() -> None:
    s = _session(tmux_session="hs", tmux_window="1", tmux_pane_index="0")
    assert resolve_pane_target(s) == "hs:1.0"


def test_resolve_pane_target_none_when_the_record_never_saw_tmux() -> None:
    assert resolve_pane_target(_session()) is None


# --- the watcher's pure half ----------------------------------------------


def test_awaiting_snapshot_keys_sessions_the_board_way() -> None:
    sessions = [
        _session(agent="claude", session_id="a", awaiting_response=True),
        _session(agent="codex", session_id="b", awaiting_response=False),
    ]
    assert awaiting_snapshot(sessions) == {"claude:a": True, "codex:b": False}


def test_awaiting_transitions_report_flips_both_ways() -> None:
    previous = {"claude:a": False, "codex:b": True}
    current = {"claude:a": True, "codex:b": False}
    assert sorted(awaiting_transitions(previous, current)) == [
        "claude:a",
        "codex:b",
    ]


def test_awaiting_transitions_new_session_counts_only_when_awaiting() -> None:
    assert awaiting_transitions({}, {"claude:new": False}) == []
    assert awaiting_transitions({}, {"claude:new": True}) == ["claude:new"]


def test_awaiting_transitions_pruned_session_is_not_a_transition() -> None:
    assert awaiting_transitions({"claude:gone": True}, {}) == []


def test_awaiting_transitions_steady_state_is_silent() -> None:
    snap = {"claude:a": True, "codex:b": False}
    assert awaiting_transitions(snap, dict(snap)) == []
