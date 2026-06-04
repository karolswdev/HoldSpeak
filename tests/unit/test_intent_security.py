from __future__ import annotations

from holdspeak.plugins.host import PluginHost


class _CapabilityPlugin:
    id = "needs-network"
    version = "1.0.0"
    required_capabilities = ["network"]

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        return {"ok": True}


class _ActuatorPlugin:
    """An actuator PROPOSES a side effect; it never performs one.

    HS-37-01: `run()` builds an `ActuatorProposal` from context and returns
    it — reaching out is the guarded executor's job (HS-37-04), never run()'s.
    """

    id = "external-actuator"
    version = "1.0.0"
    kind = "actuator"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        return {
            "target": "github",
            "action": "create_issue",
            "preview": "Open a follow-up issue for the unowned action item",
            "payload": {"repo": "acme/app", "title": "Follow up", "had_context": bool(context)},
            "reversible": True,
        }


class _MisbehavingActuator:
    """An actuator whose run() returns a non-proposal — the host rejects it."""

    id = "bad_actuator"
    version = "1.0.0"
    kind = "actuator"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        return {"executed": True}  # not an ActuatorProposal


class _GatedActuator:
    """An actuator that opts in via the `actuator` capability."""

    id = "gated_actuator"
    version = "1.0.0"
    kind = "actuator"
    required_capabilities = ["actuator"]

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        return {
            "target": "webhook",
            "action": "post",
            "preview": "POST the stakeholder update to the configured webhook",
            "payload": {"url": "https://example.test/hook"},
        }


def test_capability_mismatch_blocks_plugin_execution() -> None:
    host = PluginHost(default_timeout_seconds=0.1, enabled_capabilities={"filesystem"})
    host.register(_CapabilityPlugin())

    result = host.execute(
        "needs-network",
        context={},
        meeting_id="m-sec",
        window_id="w-cap",
        transcript_hash="h-cap",
    )

    assert result.status == "blocked"
    assert result.error is not None
    assert "Missing capabilities: network" in result.error
    metrics = host.get_metrics()
    assert metrics["blocked"] == 1
    assert metrics["runs_total"] == 1


def test_actuator_runs_produce_a_proposal_not_a_side_effect() -> None:
    # HS-37-01: an actuator runs to PROPOSE — status `proposed`, the proposal
    # on `output`, and the host performs NO side effect. The execution-gating
    # flag (`allow_actuators`) is irrelevant to proposing.
    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_ActuatorPlugin())

    result = host.execute(
        "external-actuator",
        context={"target": "ticket"},
        meeting_id="m-sec",
        window_id="w-act",
        transcript_hash="h-act",
    )

    assert result.status == "proposed"
    assert result.output is not None
    assert result.output["target"] == "github"
    assert result.output["action"] == "create_issue"
    assert result.output["preview"]
    assert result.output["reversible"] is True
    # The proposal carries the exact machine payload — the parity source of
    # truth the guarded executor (HS-37-04) checks before acting.
    assert result.output["payload"]["repo"] == "acme/app"

    metrics = host.get_metrics()
    assert metrics["proposed"] == 1
    assert metrics["runs_total"] == 1


def test_malformed_actuator_proposal_is_an_error_not_a_side_effect() -> None:
    # HS-37-01: a run() that doesn't return a proposal is the actuator's fault
    # → a normal `error`, never a silent side effect.
    host = PluginHost(default_timeout_seconds=0.1)
    host.register(_MisbehavingActuator())

    result = host.execute(
        "bad_actuator",
        context={},
        meeting_id="m-sec",
        window_id="w-bad",
        transcript_hash="h-bad",
    )

    assert result.status == "error"
    assert result.error is not None
    assert "actuator proposal" in result.error.lower()
    assert result.output is None


def test_actuator_capability_is_off_by_default() -> None:
    # HS-37-01: an actuator that opts in via the `actuator` capability is
    # capability-blocked until an operator enables it — the default-safe state.
    blocked_host = PluginHost(default_timeout_seconds=0.1)
    blocked_host.register(_GatedActuator())
    blocked = blocked_host.execute(
        "gated_actuator",
        context={},
        meeting_id="m-sec",
        window_id="w-gate",
        transcript_hash="h-gate",
    )
    assert blocked.status == "blocked"
    assert blocked.error is not None
    assert "actuator" in blocked.error.lower()

    enabled_host = PluginHost(
        default_timeout_seconds=0.1, enabled_capabilities={"actuator"}
    )
    enabled_host.register(_GatedActuator())
    enabled = enabled_host.execute(
        "gated_actuator",
        context={},
        meeting_id="m-sec",
        window_id="w-gate",
        transcript_hash="h-gate",
    )
    assert enabled.status == "proposed"
    assert enabled.output["target"] == "webhook"
