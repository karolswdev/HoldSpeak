"""HS-94-06 — immutable targets and the shared terminal stream.

Contract §7 proven against an injectable tmux: one node capture per
pane fans out to N subscribers; deltas are sequenced and ANSI-honest;
a slow client falls off the bounded ring into ``resync_required`` with
a REAL fresh snapshot (never fabricated bytes); absences are typed;
and a recycled pane moves the target generation so old handles refuse.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.delivery.terminal import (
    TerminalCapture,
    TerminalStreamService,
    TerminalTargetRegistry,
    normalize_pane_ref,
)


class FakeTmux:
    """A pane universe: mutable refs over canonical %N panes, plus
    real-shaped display-message / capture-pane answers."""

    def __init__(self) -> None:
        self.panes: dict[str, str] = {}
        self.refs: dict[str, str] = {}
        self.capture_calls = 0

    def __call__(self, argv, cwd=None):
        target = argv[argv.index("-t") + 1]
        pane = self._resolve(target)
        if argv[1] == "display-message":
            if pane is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pane")
            return SimpleNamespace(returncode=0, stdout=pane + "\n", stderr="")
        if argv[1] == "capture-pane":
            self.capture_calls += 1
            if pane is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pane")
            return SimpleNamespace(
                returncode=0, stdout=self.panes[pane] + "\n", stderr=""
            )
        raise AssertionError(f"unexpected tmux verb: {argv}")

    def _resolve(self, target: str):
        if target.startswith("%"):
            return target if target in self.panes else None
        pane = self.refs.get(target)
        return pane if pane in self.panes else None


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


@pytest.fixture
def tmux() -> FakeTmux:
    fake = FakeTmux()
    fake.panes["%5"] = "line-one\nline-two"
    fake.refs["hs:0.0"] = "%5"
    return fake


@pytest.fixture
def clock() -> Clock:
    return Clock()


def _service(tmux, clock, **kw) -> TerminalStreamService:
    registry = TerminalTargetRegistry(runner=tmux)
    return TerminalStreamService(registry, runner=tmux, clock=clock, **kw)


def _target(service: TerminalStreamService, ref: str = "hs:0.0") -> dict:
    issued = service.targets.issue(ref)
    assert issued["status"] == "issued"
    return issued


# ── targets ──────────────────────────────────────────────────────────


def test_normalize_pane_ref_compat_forms() -> None:
    assert normalize_pane_ref("pane:%7") == "%7"
    assert normalize_pane_ref("%7") == "%7"
    assert normalize_pane_ref(" hs:0.0 ") == "hs:0.0"


def test_issue_pins_the_canonical_pane_and_reissue_is_stable(tmux) -> None:
    registry = TerminalTargetRegistry(runner=tmux)
    first = registry.issue("pane:%5")
    assert first["status"] == "issued"
    assert first["pane_id"] == "%5"
    assert first["target_id"].startswith("term_")
    assert first["target_generation"].startswith("gen_")
    again = registry.issue("pane:%5")
    assert again["target_id"] == first["target_id"]
    assert again["target_generation"] == first["target_generation"]


def test_unprovable_pane_gets_no_target(tmux) -> None:
    registry = TerminalTargetRegistry(runner=tmux)
    assert registry.issue("pane:%404")["status"] == "pane_gone"
    assert registry.issue("")["status"] == "pane_gone"


def test_recycled_pane_moves_the_generation_and_old_handles_refuse(tmux) -> None:
    registry = TerminalTargetRegistry(runner=tmux)
    issued = registry.issue("hs:0.0")
    ok = registry.verify(issued["target_id"], issued["target_generation"])
    assert ok["status"] == "ok" and ok["pane_id"] == "%5"

    # The pane dies; the mutable address is reused by a NEW pane.
    del tmux.panes["%5"]
    tmux.panes["%9"] = "the impostor"
    tmux.refs["hs:0.0"] = "%9"

    refused = registry.verify(issued["target_id"], issued["target_generation"])
    assert refused["status"] == "generation_mismatch"
    assert refused["current_generation"] != issued["target_generation"]

    # A deliberate re-issue reaches the successor under the NEW generation.
    fresh = registry.issue("hs:0.0")
    assert fresh["target_id"] == issued["target_id"]
    assert fresh["target_generation"] == refused["current_generation"]
    assert fresh["pane_id"] == "%9"
    assert registry.verify(fresh["target_id"], fresh["target_generation"])["status"] == "ok"


def test_dead_pure_pane_ref_is_target_gone(tmux) -> None:
    registry = TerminalTargetRegistry(runner=tmux)
    issued = registry.issue("pane:%5")
    del tmux.panes["%5"]
    gone = registry.verify(issued["target_id"], issued["target_generation"])
    assert gone["status"] == "target_gone"


def test_unknown_target_id_is_target_gone(tmux) -> None:
    registry = TerminalTargetRegistry(runner=tmux)
    assert registry.verify("term_nope", "gen_nope")["status"] == "target_gone"


# ── the shared capture / fan-out ─────────────────────────────────────


def test_two_subscribers_share_one_capture_and_see_ordered_output(
    tmux, clock
) -> None:
    service = _service(tmux, clock)
    target = _target(service)

    a = service.read(target["target_id"], target["target_generation"])
    assert a["status"] == "snapshot"
    assert a["sequence"] == 1
    assert "line-one" in a["content"]

    # Subscriber B within the throttle window: NO second tmux capture.
    calls_after_a = tmux.capture_calls
    b = service.read(target["target_id"], target["target_generation"])
    assert b["status"] == "snapshot" and b["sequence"] == 1
    assert tmux.capture_calls == calls_after_a

    # Output moves; both subscribers resume and see the SAME ordered delta.
    tmux.panes["%5"] += "\nline-three"
    clock.advance(1.0)
    da = service.read(
        target["target_id"], target["target_generation"], resume_sequence=1
    )
    db = service.read(
        target["target_id"], target["target_generation"], resume_sequence=1
    )
    assert da["status"] == "deltas" and db["status"] == "deltas"
    assert [d["sequence"] for d in da["deltas"]] == [2]
    assert da["deltas"] == db["deltas"]
    assert "line-three" in da["deltas"][0]["data"]

    # One capture object served both (one pane, one stream).
    metrics = service.capture_metrics()
    assert list(metrics) == ["%5"]


def test_resume_at_current_sequence_is_not_modified(tmux, clock) -> None:
    service = _service(tmux, clock)
    target = _target(service)
    snap = service.read(target["target_id"], target["target_generation"])
    out = service.read(
        target["target_id"],
        target["target_generation"],
        resume_sequence=snap["sequence"],
    )
    assert out == {
        "status": "not_modified",
        "sequence": snap["sequence"],
        "target_id": target["target_id"],
        "target_generation": target["target_generation"],
    }


def test_hash_gated_snapshot_fallback(tmux, clock) -> None:
    service = _service(tmux, clock)
    target = _target(service)
    snap = service.read(target["target_id"], target["target_generation"])
    out = service.read(
        target["target_id"], target["target_generation"], last_hash=snap["hash"]
    )
    assert out["status"] == "not_modified"


def test_slow_client_past_the_ring_resyncs_with_real_bytes_only(
    tmux, clock
) -> None:
    service = _service(tmux, clock, ring_max_deltas=3)
    target = _target(service)
    fast = service.read(target["target_id"], target["target_generation"])
    assert fast["sequence"] == 1

    for i in range(6):
        tmux.panes["%5"] += f"\nburst-{i}"
        clock.advance(1.0)
        service.read(target["target_id"], target["target_generation"], resume_sequence=None)

    # The slow client resumes from 1 — evicted. It gets resync_required
    # plus a snapshot whose content is EXACTLY the pane's real content.
    out = service.read(
        target["target_id"], target["target_generation"], resume_sequence=1
    )
    assert out["status"] == "resync_required"
    assert out["content"] == tmux.panes["%5"]
    assert "deltas" not in out
    assert out["sequence"] == 7  # 1 snapshot + 6 real changes

    metrics = service.capture_metrics()["%5"]
    assert metrics["entries"] <= 3
    assert metrics["floor_sequence"] == 5  # ring kept only the newest 3


def test_resume_ahead_of_the_stream_resyncs(tmux, clock) -> None:
    service = _service(tmux, clock)
    target = _target(service)
    service.read(target["target_id"], target["target_generation"])
    out = service.read(
        target["target_id"], target["target_generation"], resume_sequence=99
    )
    assert out["status"] == "resync_required"


def test_ansi_bytes_pass_through_untouched(tmux, clock) -> None:
    ansi = "\x1b[1;31mERROR\x1b[0m plain \x1b[7mreverse\x1b[27m"
    tmux.panes["%5"] = ansi
    service = _service(tmux, clock)
    target = _target(service)
    snap = service.read(target["target_id"], target["target_generation"])
    assert snap["content"] == ansi
    assert snap["ansi"] is True

    tmux.panes["%5"] += "\n\x1b[32mgreen\x1b[0m"
    clock.advance(1.0)
    out = service.read(
        target["target_id"], target["target_generation"], resume_sequence=1
    )
    assert out["status"] == "deltas"
    assert out["deltas"][0]["data"] == "\n\x1b[32mgreen\x1b[0m"


def test_screen_redraw_is_a_typed_full_delta_never_fabricated(tmux, clock) -> None:
    service = _service(tmux, clock)
    target = _target(service)
    service.read(target["target_id"], target["target_generation"])
    tmux.panes["%5"] = "totally\nredrawn\nscreen"
    clock.advance(1.0)
    out = service.read(
        target["target_id"], target["target_generation"], resume_sequence=1
    )
    assert out["status"] == "deltas"
    (delta,) = out["deltas"]
    assert delta["kind"] == "screen"
    assert delta["data"] == "totally\nredrawn\nscreen"


def test_typed_absences_flow_through_the_subscription(tmux, clock) -> None:
    service = _service(tmux, clock)
    target = _target(service)
    # generation mismatch
    del tmux.panes["%5"]
    tmux.panes["%9"] = "new tenant"
    tmux.refs["hs:0.0"] = "%9"
    out = service.read(target["target_id"], target["target_generation"])
    assert out["status"] == "generation_mismatch"
    # target gone (pure pane target whose pane died)
    issued = service.targets.issue("pane:%9")
    del tmux.panes["%9"]
    gone = service.read(issued["target_id"], issued["target_generation"])
    assert gone["status"] == "target_gone"


def test_transient_tmux_failure_is_stream_unavailable(clock) -> None:
    def broken(argv, cwd=None):
        raise OSError("tmux exploded")

    healthy = FakeTmux()
    healthy.panes["%5"] = "x"
    registry = TerminalTargetRegistry(runner=healthy)
    issued = registry.issue("pane:%5")
    # The node's tmux goes away mid-flight: typed, never a fabricated stream.
    registry._runner = broken
    service = TerminalStreamService(registry, runner=broken, clock=clock)
    out = service.read(issued["target_id"], issued["target_generation"])
    assert out["status"] == "stream_unavailable"


def test_capture_ring_respects_the_byte_ceiling(tmux, clock) -> None:
    capture = TerminalCapture(
        "%5", runner=tmux, clock=clock, ring_max_bytes=64, min_poll_interval=0.0
    )
    capture.poll()
    for i in range(10):
        tmux.panes["%5"] += "\n" + ("x" * 30) + str(i)
        capture.poll()
    metrics = capture.ring_metrics()
    assert metrics["bytes"] <= 64 + 32  # at most one entry over before evict
    assert metrics["entries"] <= 2
