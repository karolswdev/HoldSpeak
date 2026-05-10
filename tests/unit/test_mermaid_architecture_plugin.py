"""Unit tests for `MermaidArchitecturePlugin` (HS-16-01).

The LLM is injected via the `intel_call` constructor argument, so these
tests do not load any real local model or call any cloud endpoint.
"""

from __future__ import annotations

import pytest

from holdspeak.intel import MeetingIntelError
from holdspeak.plugins.builtin import (
    DeterministicPlugin,
    MermaidArchitecturePlugin,
    register_builtin_plugins,
)
from holdspeak.plugins.builtin.mermaid_architecture import _extract_mermaid_block
from holdspeak.plugins.host import PluginHost


_GOOD_FLOWCHART_RESPONSE = (
    "Frontend talks to API which fans out to Auth, Inventory, and Postgres.\n"
    "```mermaid\n"
    "flowchart TD\n"
    "  Frontend --> API\n"
    "  API --> Auth\n"
    "  API --> Inventory\n"
    "  API --> DB[(Postgres)]\n"
    "```\n"
)


_GOOD_SEQUENCE_RESPONSE = (
    "Client requests a token and the auth service issues one.\n"
    "```mermaid\n"
    "sequenceDiagram\n"
    "  participant C as Client\n"
    "  participant A as Auth\n"
    "  C->>A: request token\n"
    "  A-->>C: signed JWT\n"
    "```\n"
)


def test_run_success_path_returns_full_shape() -> None:
    plugin = MermaidArchitecturePlugin(
        intel_call=lambda messages: _GOOD_FLOWCHART_RESPONSE
    )

    out = plugin.run(
        {
            "transcript": (
                "We're putting an API in front of Auth, Inventory, and the database, "
                "and the frontend talks only to the API."
            ),
            "active_intents": ["architecture"],
            "tags": ["api", "auth"],
        }
    )

    assert set(out.keys()) == {
        "summary",
        "mermaid",
        "diagram_kind",
        "confidence_hint",
        "active_intents",
    }
    assert out["confidence_hint"] == 1.0
    assert out["diagram_kind"] == "flowchart"
    assert out["active_intents"] == ["architecture"]
    assert out["summary"].startswith("Frontend talks to API")
    # The `mermaid` value is the inner block body (no fences) per HS-16-01.
    assert "Frontend --> API" in out["mermaid"]
    assert not out["mermaid"].startswith("```")


def test_run_recognises_sequence_diagram() -> None:
    plugin = MermaidArchitecturePlugin(
        intel_call=lambda messages: _GOOD_SEQUENCE_RESPONSE
    )

    out = plugin.run({"transcript": "client asks auth for a token"})

    assert out["diagram_kind"] == "sequenceDiagram"
    assert out["confidence_hint"] == 1.0
    assert "participant" in out["mermaid"]
    assert "C->>A:" in out["mermaid"]


def test_run_no_fenced_block_returns_failure_shape() -> None:
    plugin = MermaidArchitecturePlugin(
        intel_call=lambda messages: "Sorry, I can't produce a diagram for this."
    )

    out = plugin.run(
        {"transcript": "hello world", "active_intents": ["architecture"]}
    )

    assert "mermaid" not in out
    assert out["confidence_hint"] == 0.0
    assert out["active_intents"] == ["architecture"]


def test_run_provider_raises_returns_failure_shape() -> None:
    def _raise(_messages: list[dict[str, str]]) -> str:
        raise MeetingIntelError("LLM exploded")

    plugin = MermaidArchitecturePlugin(intel_call=_raise)

    out = plugin.run({"transcript": "hello", "active_intents": ["architecture"]})

    assert "mermaid" not in out
    assert out["confidence_hint"] == 0.0
    assert "LLM exploded" in out["summary"]


def test_run_empty_transcript_returns_failure_shape_without_calling_llm() -> None:
    calls: list[list[dict[str, str]]] = []

    def _record(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return _GOOD_FLOWCHART_RESPONSE

    plugin = MermaidArchitecturePlugin(intel_call=_record)
    out = plugin.run({"transcript": "   ", "active_intents": []})

    assert "mermaid" not in out
    assert out["confidence_hint"] == 0.0
    assert calls == []  # never reached the LLM


def test_plugin_attributes_match_contract() -> None:
    plugin = MermaidArchitecturePlugin()
    assert plugin.id == "mermaid_architecture"
    assert plugin.version == "0.1.0"
    assert plugin.kind == "artifact_generator"
    assert plugin.execution_mode == "deferred"
    assert plugin.required_capabilities == ["llm"]


def test_register_builtin_plugins_uses_real_class() -> None:
    host = PluginHost()
    registered = register_builtin_plugins(host)

    assert "mermaid_architecture" in registered
    plugin = host.get_plugin("mermaid_architecture")
    assert plugin is not None
    assert isinstance(plugin, MermaidArchitecturePlugin)
    assert not isinstance(plugin, DeterministicPlugin)

    # Sibling stubs are still DeterministicPlugin (unchanged for HS-16-01).
    sibling = host.get_plugin("requirements_extractor")
    assert isinstance(sibling, DeterministicPlugin)


@pytest.mark.parametrize(
    "raw, expected_kind",
    [
        (
            "```mermaid\nflowchart TD\n  A --> B\n```",
            "flowchart",
        ),
        (
            "```mermaid\ngraph LR\n  A --> B\n  B --> C\n```",
            "graph",
        ),
        (
            "```mermaid\nsequenceDiagram\n  participant A\n  participant B\n  A->>B: hi\n```",
            "sequenceDiagram",
        ),
        (
            "```mermaid\nstateDiagram-v2\n  [*] --> Idle\n  Idle --> Running\n```",
            "stateDiagram",
        ),
    ],
)
def test_extract_mermaid_block_recognises_known_kinds(
    raw: str, expected_kind: str
) -> None:
    parsed = _extract_mermaid_block(raw)
    assert parsed is not None, f"failed to parse: {raw!r}"
    body, kind = parsed
    assert kind == expected_kind
    assert body  # non-empty body


@pytest.mark.parametrize(
    "raw",
    [
        # No fence at all.
        "flowchart TD\n  A --> B",
        # Fence but unknown kind on first line.
        "```mermaid\nfoobarchart TD\n  A --> B\n```",
        # Recognised kind but no edges → fails minimum-structure bar.
        "```mermaid\nflowchart TD\n  A\n```",
        # sequenceDiagram with a participant but no message.
        "```mermaid\nsequenceDiagram\n  participant A\n```",
        # Empty fenced block.
        "```mermaid\n\n```",
    ],
)
def test_extract_mermaid_block_rejects_invalid_input(raw: str) -> None:
    assert _extract_mermaid_block(raw) is None
