"""Raw peek unit tests (HS-111-11) — `coder_steering.peek_pane(raw=True)`.

The raw variant is the SAME read path with the stripping stage removed:
ANSI passthrough, the same hash gate, a raised (but still hard) byte
cap, and the pane geometry garnish. Stripped stays the default — the
first test pins that a raw-era module still answers the old call shape
byte-for-byte.
"""

from __future__ import annotations

import subprocess
from typing import Any

from holdspeak import coder_steering

COLORED = (
    "\x1b[32mPASS\x1b[0m tests/unit\n"
    "\x1b[1;31mFAIL\x1b[0m tests/e2e\n"
    "plain tail line"
)


def _completed(stdout: str = "", returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess(
        args=["tmux"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _capture_runner(stdout: str, *, geometry: str | None = "80 24 5 3"):
    """A runner that answers capture-pane with `stdout` and
    display-message with `geometry` (None = tmux refuses)."""

    def run(argv: list[str], cwd: Any = None):
        if argv[1] == "capture-pane":
            return _completed(stdout)
        if argv[1] == "display-message":
            if geometry is None:
                return _completed("", returncode=1, stderr="no such pane")
            return _completed(geometry + "\n")
        raise AssertionError(f"unexpected tmux verb: {argv}")

    return run


def test_stripped_stays_the_default() -> None:
    result = coder_steering.peek_pane("%1", runner=_capture_runner(COLORED))
    assert result["status"] == "live"
    assert result["lines"] == ["PASS tests/unit", "FAIL tests/e2e", "plain tail line"]
    assert "raw" not in result
    assert "pane" not in result


def test_raw_is_ansi_passthrough() -> None:
    result = coder_steering.peek_pane(
        "%1", runner=_capture_runner(COLORED), raw=True
    )
    assert result["status"] == "live"
    assert result["raw"] == COLORED
    assert "\x1b[32m" in result["raw"]
    assert "lines" not in result


def test_raw_carries_the_pane_geometry() -> None:
    result = coder_steering.peek_pane(
        "%1", runner=_capture_runner(COLORED), raw=True
    )
    assert result["pane"] == {
        "width": 80,
        "height": 24,
        "cursor_x": 5,
        "cursor_y": 3,
    }


def test_raw_geometry_failure_is_a_garnish_not_a_refusal() -> None:
    result = coder_steering.peek_pane(
        "%1", runner=_capture_runner(COLORED, geometry=None), raw=True
    )
    assert result["status"] == "live"
    assert "pane" not in result


def test_raw_hash_gate_parity() -> None:
    first = coder_steering.peek_pane(
        "%1", runner=_capture_runner(COLORED), raw=True
    )
    second = coder_steering.peek_pane(
        "%1", runner=_capture_runner(COLORED), last_hash=first["hash"], raw=True
    )
    assert second == {"status": "not_modified", "hash": first["hash"]}


def test_raw_and_stripped_hash_their_own_content() -> None:
    """A stripped hash never gates a raw peek: the digests differ, so a
    consumer flipping modes resyncs honestly instead of going blind."""
    stripped = coder_steering.peek_pane("%1", runner=_capture_runner(COLORED))
    raw = coder_steering.peek_pane(
        "%1", runner=_capture_runner(COLORED), last_hash=stripped["hash"], raw=True
    )
    assert raw["status"] == "live"
    assert raw["hash"] != stripped["hash"]


def test_raw_byte_cap_is_raised_and_keeps_the_tail() -> None:
    big = "\n".join(f"\x1b[33mline {i:07d}\x1b[0m" for i in range(20_000))
    assert len(big.encode()) > coder_steering.PEEK_RAW_MAX_BYTES
    result = coder_steering.peek_pane("%1", runner=_capture_runner(big), raw=True)
    encoded = result["raw"].encode("utf-8")
    assert len(encoded) <= coder_steering.PEEK_RAW_MAX_BYTES
    assert len(encoded) > coder_steering.PEEK_MAX_BYTES  # the raise is real
    assert result["raw"].endswith("line 0019999\x1b[0m")  # tail kept
    assert result["raw"].startswith("\x1b")  # cut lands on a line boundary


def test_raw_line_cap_still_clamps_the_capture() -> None:
    seen: dict[str, Any] = {}

    def run(argv: list[str], cwd: Any = None):
        if argv[1] == "capture-pane":
            seen["start"] = argv[argv.index("-S") + 1]
            return _completed("x")
        return _completed("80 24 0 0")

    coder_steering.peek_pane("%1", lines=9_999, runner=run, raw=True)
    assert seen["start"] == f"-{coder_steering.PEEK_MAX_LINES}"


def test_raw_pane_gone_is_the_same_typed_absence() -> None:
    def run(argv: list[str], cwd: Any = None):
        return _completed("", returncode=1, stderr="can't find pane %1")

    result = coder_steering.peek_pane("%1", runner=run, raw=True)
    assert result == {"status": "pane_gone", "detail": "can't find pane %1"}
