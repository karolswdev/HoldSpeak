"""HS-35-03 — per-project plugin enable/disable at dispatch.

A disabled plugin id is dropped from the *executed* set and recorded as a
`skipped` run (distinct from `blocked`/`error`); the *built* chain is
unchanged. Default (no disabled list) is byte-identical to today.
"""

from __future__ import annotations

import pytest

from holdspeak.config import MeetingConfig
from holdspeak.plugins.contracts import PLUGIN_RUN_STATUSES, IntentScore, IntentWindow
from holdspeak.plugins.dispatch import (
    dispatch_window,
    normalize_disabled_plugins,
    partition_chain,
)
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.router import build_plugin_chain


class StubPlugin:
    def __init__(self, plugin_id: str, *, version: str = "1.0.0") -> None:
        self.id = plugin_id
        self.version = version
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        return {"id": self.id}


def _window() -> IntentWindow:
    return IntentWindow(
        window_id="m1:w0001",
        meeting_id="m1",
        start_seconds=0.0,
        end_seconds=30.0,
        transcript="Architecture review.",
        tags=[],
    )


def _score(*, threshold: float = 0.6, **scores: float) -> IntentScore:
    base = {k: 0.0 for k in ("architecture", "delivery", "product", "incident", "comms")}
    base.update(scores)
    return IntentScore(window_id="m1:w0001", scores=base, threshold=threshold)


def _build_host_with(*plugin_ids: str) -> tuple[PluginHost, dict[str, StubPlugin]]:
    host = PluginHost(default_timeout_seconds=1.0)
    stubs: dict[str, StubPlugin] = {}
    for pid in plugin_ids:
        stub = StubPlugin(pid)
        stubs[pid] = stub
        host.register(stub)
    return host, stubs


# ─────────────────────── Pure routing-layer helpers ───────────────────


def test_skipped_is_a_known_status() -> None:
    assert "skipped" in PLUGIN_RUN_STATUSES


def test_normalize_disabled_plugins_cleans_and_dedupes() -> None:
    assert normalize_disabled_plugins([" adr_drafter ", "adr_drafter", "", None]) == {
        "adr_drafter"
    }
    assert normalize_disabled_plugins(None) == set()


def test_partition_chain_preserves_order_and_no_ops_unknown() -> None:
    chain = ["project_detector", "requirements_extractor", "mermaid_architecture", "adr_drafter"]
    executed, skipped = partition_chain(chain, ["mermaid_architecture", "not_in_chain"])
    assert executed == ["project_detector", "requirements_extractor", "adr_drafter"]
    assert skipped == ["mermaid_architecture"]


def test_partition_chain_empty_disabled_is_identity() -> None:
    chain = ["a", "b", "c"]
    executed, skipped = partition_chain(chain, None)
    assert executed == chain
    assert skipped == []


# ─────────────────────── Dispatch-gate behavior ───────────────────────


def test_disabled_plugin_is_skipped_not_executed() -> None:
    host, stubs = _build_host_with(
        "project_detector", "requirements_extractor", "mermaid_architecture", "adr_drafter"
    )
    runs = dispatch_window(
        host,
        _score(architecture=0.9),
        window=_window(),
        profile="architect",
        disabled_plugins=["mermaid_architecture"],
    )

    # The built chain is unchanged: a run exists for every chain member.
    assert [r.plugin_id for r in runs] == [
        "project_detector",
        "requirements_extractor",
        "mermaid_architecture",
        "adr_drafter",
    ]
    by_id = {r.plugin_id: r for r in runs}
    assert by_id["mermaid_architecture"].status == "skipped"
    assert by_id["mermaid_architecture"].duration_ms == 0.0
    assert by_id["mermaid_architecture"].output is None
    # The disabled plugin was never invoked; its siblings ran.
    assert stubs["mermaid_architecture"].calls == 0
    assert stubs["requirements_extractor"].calls == 1
    assert by_id["adr_drafter"].status == "success"


def test_skipped_run_carries_real_plugin_version() -> None:
    host, _ = _build_host_with("project_detector", "requirements_extractor")
    runs = dispatch_window(
        host,
        _score(architecture=0.9),
        window=_window(),
        profile="architect",
        disabled_plugins=["requirements_extractor"],
    )
    skipped = next(r for r in runs if r.plugin_id == "requirements_extractor")
    assert skipped.status == "skipped"
    assert skipped.plugin_version == "1.0.0"


def test_unknown_disabled_id_is_a_no_op() -> None:
    host, stubs = _build_host_with(
        "project_detector", "requirements_extractor", "mermaid_architecture", "adr_drafter"
    )
    runs = dispatch_window(
        host,
        _score(architecture=0.9),
        window=_window(),
        profile="architect",
        disabled_plugins=["does_not_exist"],
    )
    assert all(r.status == "success" for r in runs)
    assert stubs["requirements_extractor"].calls == 1


def test_default_no_disabled_is_byte_identical() -> None:
    """No disabled list ⇒ the executed set equals the built chain, all run."""
    host, stubs = _build_host_with("project_detector", "requirements_extractor", "action_owner_enforcer", "decision_capture")
    runs = dispatch_window(host, _score(), window=_window(), profile="balanced")
    built = build_plugin_chain("balanced", [])
    assert [r.plugin_id for r in runs] == built
    assert all(r.status == "success" for r in runs)
    assert all(s.calls == 1 for s in stubs.values())


# ─────────────────────────── Config knob ──────────────────────────────


def test_config_disabled_plugins_default_empty() -> None:
    assert MeetingConfig().disabled_plugins == []


def test_config_disabled_plugins_normalized() -> None:
    cfg = MeetingConfig(disabled_plugins=[" adr_drafter ", "adr_drafter", "", "scope_guard"])
    assert cfg.disabled_plugins == ["adr_drafter", "scope_guard"]


def test_config_disabled_plugins_rejects_non_list() -> None:
    with pytest.raises(ValueError, match="disabled_plugins"):
        MeetingConfig(disabled_plugins="adr_drafter")  # type: ignore[arg-type]


def test_config_disabled_plugins_rejects_non_string_members() -> None:
    with pytest.raises(ValueError, match="disabled_plugins"):
        MeetingConfig(disabled_plugins=["ok", 123])  # type: ignore[list-item]
