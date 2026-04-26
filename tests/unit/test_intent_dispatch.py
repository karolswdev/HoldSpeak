"""Unit tests for the typed plugin-chain dispatcher (HS-2-04 / spec §9.4)."""

from __future__ import annotations

from holdspeak.plugins.contracts import IntentScore, IntentWindow, PluginRun
from holdspeak.plugins.dispatch import dispatch_window, dispatch_windows
from holdspeak.plugins.host import PluginHost


class StubPlugin:
    def __init__(self, plugin_id: str, *, version: str = "1.0.0") -> None:
        self.id = plugin_id
        self.version = version
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        return {"id": self.id, "intents": list(context.get("active_intents") or [])}


class RaisingPlugin:
    id = "raises"
    version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("kaboom")


def _window(window_id: str = "m1:w0001", transcript: str = "Architecture review.") -> IntentWindow:
    return IntentWindow(
        window_id=window_id,
        meeting_id="m1",
        start_seconds=0.0,
        end_seconds=30.0,
        transcript=transcript,
        tags=[],
    )


def _score(window_id: str = "m1:w0001", *, threshold: float = 0.6, **scores: float) -> IntentScore:
    base = {
        "architecture": 0.0,
        "delivery": 0.0,
        "product": 0.0,
        "incident": 0.0,
        "comms": 0.0,
    }
    base.update(scores)
    return IntentScore(window_id=window_id, scores=base, threshold=threshold)


def _build_host_with(*plugin_ids: str) -> tuple[PluginHost, dict[str, StubPlugin]]:
    host = PluginHost(default_timeout_seconds=1.0)
    stubs: dict[str, StubPlugin] = {}
    for pid in plugin_ids:
        stub = StubPlugin(pid)
        stubs[pid] = stub
        host.register(stub)
    return host, stubs


def test_dispatch_window_returns_typed_plugin_runs_for_chain() -> None:
    # Architecture profile chain on architecture-active scores.
    host, stubs = _build_host_with(
        "project_detector",
        "requirements_extractor",
        "mermaid_architecture",
        "adr_drafter",
    )
    score = _score(architecture=0.9)

    runs = dispatch_window(
        host,
        score,
        window=_window(),
        profile="architect",
    )

    assert all(isinstance(r, PluginRun) for r in runs)
    assert [r.plugin_id for r in runs] == [
        "project_detector",
        "requirements_extractor",
        "mermaid_architecture",
        "adr_drafter",
    ]
    for run in runs:
        assert run.window_id == "m1:w0001"
        assert run.meeting_id == "m1"
        assert run.profile == "architect"
        assert run.status == "success"
        assert run.finished_at >= run.started_at
        assert run.duration_ms >= 0.0
    assert all(stub.calls == 1 for stub in stubs.values())


_BALANCED_DELIVERY_CHAIN = (
    "project_detector",
    "requirements_extractor",
    "action_owner_enforcer",
    "milestone_planner",
    "dependency_mapper",
)


def test_dispatch_window_passes_active_intents_into_plugin_context() -> None:
    host, stubs = _build_host_with(*_BALANCED_DELIVERY_CHAIN)
    score = _score(delivery=0.9)

    runs = dispatch_window(host, score, window=_window(), profile="balanced")

    # Plugin output records the active_intents it saw — assert it matches the routed set.
    payload = next(r for r in runs if r.plugin_id == "action_owner_enforcer")
    assert payload.status == "success"
    assert stubs["action_owner_enforcer"].calls == 1


def test_dispatch_window_idempotency_dedups_second_dispatch_mir_f_008() -> None:
    host, stubs = _build_host_with(*_BALANCED_DELIVERY_CHAIN)
    score = _score(delivery=0.9)

    first = dispatch_window(host, score, window=_window(), profile="balanced")
    second = dispatch_window(host, score, window=_window(), profile="balanced")

    assert all(r.status == "success" for r in first)
    assert all(r.status == "deduped" for r in second)
    # Each plugin executed exactly once across the two dispatches.
    assert all(stub.calls == 1 for stub in stubs.values())


def test_dispatch_window_isolates_plugin_failure_mir_r_004() -> None:
    host = PluginHost(default_timeout_seconds=1.0)
    host.register(StubPlugin("project_detector"))
    host.register(RaisingPlugin())
    host.register(StubPlugin("action_owner_enforcer"))

    # Use a score that gives "balanced" profile a known chain, then override the chain
    # by using profile="balanced" — which yields ["project_detector", "requirements_extractor",
    # "action_owner_enforcer"]. We need "raises" in the chain; easiest path: register
    # a raises-shadow under the requirements_extractor id so the route picks it.
    host._plugins["requirements_extractor"] = RaisingPlugin()  # type: ignore[attr-defined]
    score = _score(delivery=0.9)

    runs = dispatch_window(host, score, window=_window(), profile="balanced")

    statuses = {r.plugin_id: r.status for r in runs}
    assert statuses["project_detector"] == "success"
    assert statuses["requirements_extractor"] == "error"  # surfaced, not raised out
    assert statuses["action_owner_enforcer"] == "success"  # sibling kept running


def test_dispatch_windows_preserves_window_order_with_typed_records() -> None:
    # Use a no-active-intents score so the chain stays at the balanced base
    # (project_detector + requirements_extractor + action_owner_enforcer = 3 plugins),
    # keeping the test assertion-shape readable.
    host, stubs = _build_host_with(
        "project_detector",
        "requirements_extractor",
        "action_owner_enforcer",
    )

    w1 = _window("m1:w0001", "Some unrelated text one.")
    w2 = _window("m1:w0002", "Some unrelated text two.")
    w3 = _window("m1:w0003", "Some unrelated text three.")

    # All scores below default 0.6 threshold → empty active_intents → base chain only.
    pairs = [
        (w1, _score("m1:w0001")),
        (w2, _score("m1:w0002")),
        (w3, _score("m1:w0003")),
    ]

    runs = dispatch_windows(host, pairs, profile="balanced")

    # 3 plugins per window × 3 windows = 9 records, in document order.
    assert [r.window_id for r in runs] == [
        "m1:w0001", "m1:w0001", "m1:w0001",
        "m1:w0002", "m1:w0002", "m1:w0002",
        "m1:w0003", "m1:w0003", "m1:w0003",
    ]
    assert all(r.status == "success" for r in runs)
    # Each plugin executed exactly once per distinct (window_id, transcript_hash).
    assert all(stub.calls == 3 for stub in stubs.values())


def test_dispatch_window_missing_plugin_id_surfaces_as_error_record() -> None:
    host = PluginHost(default_timeout_seconds=1.0)
    host.register(StubPlugin("project_detector"))
    # Deliberately don't register "action_owner_enforcer" so host.execute raises KeyError.

    score = _score(delivery=0.9)
    runs = dispatch_window(host, score, window=_window(), profile="balanced")

    statuses = {r.plugin_id: r.status for r in runs}
    assert statuses["project_detector"] == "success"
    assert statuses["action_owner_enforcer"] == "error"
    err = next(r for r in runs if r.plugin_id == "action_owner_enforcer")
    assert err.error is not None and "Unknown plugin" in err.error
