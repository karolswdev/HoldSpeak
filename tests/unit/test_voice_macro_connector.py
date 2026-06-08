"""HS-52-03: local action connectors for voice command macros.

Drives the connectors with injected fakes (no real subprocess, no real typing) and
pins the safety property: an egress connector is bounded by a per-macro manifest to
exactly its configured command, so a different command is refused before any side
effect, and execution is blocked entirely when the actuator capability is off.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.config import VoiceMacroAction
from holdspeak.plugins.actuator_executor import ActuatorExecutor, ActuatorPolicyError
from holdspeak.plugins.gated_connector import ConnectorOperationRefused
from holdspeak.plugins.voice_macro_connector import (
    build_voice_macro_connector,
    voice_macro_argv,
)


def _proposal(kind: str, payload: str) -> SimpleNamespace:
    return SimpleNamespace(
        status="approved",
        plugin_id="voice_macro",
        target="voice_macro",
        action="run",
        preview="",
        payload={"kind": kind, "payload": payload},
        reversible=False,
        required_capabilities=(),
    )


def _ok_runner(captured: dict):
    def _run(argv, **kwargs):
        captured["argv"] = list(argv)
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="done\n", stderr="")

    return _run


def test_argv_per_kind_macos_and_linux() -> None:
    open_url = VoiceMacroAction("open_url", "https://x")
    launch = VoiceMacroAction("launch_app", "Terminal")
    shell = VoiceMacroAction("shell", "git push")
    assert voice_macro_argv(open_url, platform="darwin") == ("open", "https://x")
    assert voice_macro_argv(open_url, platform="linux") == ("xdg-open", "https://x")
    assert voice_macro_argv(launch, platform="darwin") == ("open", "-a", "Terminal")
    assert voice_macro_argv(launch, platform="linux") == ("Terminal",)
    assert voice_macro_argv(shell, platform="darwin") == ("sh", "-c", "git push")
    assert voice_macro_argv(VoiceMacroAction("type_text", "hi")) is None


@pytest.mark.parametrize(
    "kind,payload,expected_argv",
    [
        ("open_url", "https://example.com", ["open", "https://example.com"]),
        ("launch_app", "Terminal", ["open", "-a", "Terminal"]),
        ("shell", "echo hi", ["sh", "-c", "echo hi"]),
    ],
)
def test_egress_connector_runs_bounded_argv(kind, payload, expected_argv) -> None:
    captured: dict = {}
    action = VoiceMacroAction(kind, payload)
    connector = build_voice_macro_connector(
        action, runner=_ok_runner(captured), platform="darwin"
    )
    result = connector(_proposal(kind, payload))
    assert captured["argv"] == expected_argv
    assert result["returncode"] == 0
    assert result["argv"] == expected_argv


def test_connector_refuses_a_different_command_than_configured() -> None:
    """The bounded blast radius: a connector built for one command refuses a
    proposal carrying a different command (a mishearing fires the wrong macro, never
    a new command)."""
    captured: dict = {}
    configured = VoiceMacroAction("shell", "echo hi")
    connector = build_voice_macro_connector(
        configured, runner=_ok_runner(captured), platform="darwin"
    )
    # A proposal whose payload is a DIFFERENT shell command.
    with pytest.raises(ConnectorOperationRefused):
        connector(_proposal("shell", "rm -rf /"))
    assert "argv" not in captured  # refused before the runner is ever reached


def test_nonzero_exit_raises_to_fail_the_proposal() -> None:
    def _bad_runner(argv, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    action = VoiceMacroAction("shell", "false")
    connector = build_voice_macro_connector(action, runner=_bad_runner, platform="darwin")
    with pytest.raises(RuntimeError, match="exited 1"):
        connector(_proposal("shell", "false"))


def test_type_text_connector_types_via_injected_writer() -> None:
    typed: list[str] = []
    action = VoiceMacroAction("type_text", "## Standup")
    connector = build_voice_macro_connector(action, type_writer=typed.append)
    result = connector(_proposal("type_text", "## Standup"))
    assert typed == ["## Standup"]
    assert result == {"action": "type_text", "typed": "## Standup"}


def test_capability_off_blocks_execution_before_the_connector() -> None:
    """With `allow_actuators` off, the executor refuses before the connector runs."""
    captured: dict = {}
    action = VoiceMacroAction("shell", "echo hi")
    connector = build_voice_macro_connector(
        action, runner=_ok_runner(captured), platform="darwin"
    )
    proposal = _proposal("shell", "echo hi")

    class _FakeActuators:
        def get_proposal(self, _pid):
            return proposal

        def transition_proposal(self, *_a, **_k):  # pragma: no cover - not reached
            raise AssertionError("must not transition when policy refuses")

    fake_db = SimpleNamespace(actuators=_FakeActuators())
    executor = ActuatorExecutor(fake_db, connector=connector, allow_actuators=False)
    with pytest.raises(ActuatorPolicyError):
        executor.execute("pid")
    assert "argv" not in captured  # the connector never ran
