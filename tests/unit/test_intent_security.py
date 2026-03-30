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
    id = "external-actuator"
    version = "1.0.0"
    kind = "actuator"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        return {"executed": bool(context)}


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


def test_actuator_plugins_are_disabled_by_default() -> None:
    host = PluginHost(default_timeout_seconds=0.1, enabled_capabilities={"actuation"})
    host.register(_ActuatorPlugin())

    blocked = host.execute(
        "external-actuator",
        context={"target": "ticket"},
        meeting_id="m-sec",
        window_id="w-act",
        transcript_hash="h-act",
    )
    assert blocked.status == "blocked"
    assert blocked.error is not None
    assert "disabled by default" in blocked.error.lower()

    allowed_host = PluginHost(
        default_timeout_seconds=0.1,
        enabled_capabilities={"actuation"},
        allow_actuators=True,
    )
    allowed_host.register(_ActuatorPlugin())
    allowed = allowed_host.execute(
        "external-actuator",
        context={"target": "ticket"},
        meeting_id="m-sec",
        window_id="w-act",
        transcript_hash="h-act",
    )
    assert allowed.status == "success"
