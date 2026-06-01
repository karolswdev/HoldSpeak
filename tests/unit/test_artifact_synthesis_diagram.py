"""HS-16-03: diagram-aware artifact body for mermaid_architecture.

A "diagram" artifact embeds the plugin's fenced Mermaid block in its
body_markdown (+ a structured_json["mermaid"] key); every other artifact type
keeps its legacy body byte-for-byte.
"""

from __future__ import annotations

from types import SimpleNamespace

from holdspeak.plugins.synthesis import synthesize_meeting_artifacts

_MERMAID = "flowchart TD\n    API[API Gateway] --> Auth[Auth Service]\n    API --> Billing[Billing Service]"


def _run(plugin_id, output, *, run_id=1, meeting_id="m-1", window_id="m-1:w0001"):
    return SimpleNamespace(
        id=run_id,
        meeting_id=meeting_id,
        window_id=window_id,
        plugin_id=plugin_id,
        plugin_version="0.1.0",
        status="success",
        output=output,
        created_at="2026-06-01T12:00:00",
    )


def test_diagram_artifact_embeds_single_fenced_mermaid_block() -> None:
    runs = [
        _run(
            "mermaid_architecture",
            {
                "summary": "Gateway fronts three services.",
                "confidence_hint": 1.0,
                "active_intents": ["architecture"],
                "mermaid": _MERMAID,
            },
        )
    ]

    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "diagram"

    body = artifact.body_markdown
    assert body.count("```mermaid") == 1
    assert body.count("```") == 2  # exactly one fenced block (open + close)
    assert _MERMAID in body
    # Block sits between the summary and the source footer.
    assert body.index("Gateway fronts") < body.index("```mermaid") < body.index("- Source windows:")
    assert artifact.structured_json["mermaid"] == _MERMAID


def test_diagram_artifact_without_mermaid_uses_legacy_body() -> None:
    # Parse-failure shape from HS-16-01: no "mermaid" key.
    runs = [
        _run(
            "mermaid_architecture",
            {
                "summary": "mermaid_architecture: response did not contain a parseable Mermaid block.",
                "confidence_hint": 0.0,
                "active_intents": ["architecture"],
            },
        )
    ]

    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert "```mermaid" not in artifact.body_markdown
    assert "mermaid" not in artifact.structured_json


def test_action_items_artifact_embeds_checklist_body() -> None:
    # HS-27-01: action_owner_enforcer output → a checklist body + structured key.
    runs = [
        _run(
            "action_owner_enforcer",
            {
                "summary": "2 action item(s); 1 missing an owner or due date.",
                "confidence_hint": 1.0,
                "active_intents": ["delivery"],
                "action_items": [
                    {"task": "Draft OAuth flow", "owner": "Karol", "due": "Friday", "gap": None},
                    {"task": "Book venue", "owner": None, "due": None, "gap": "missing_both"},
                ],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "action_items"

    body = artifact.body_markdown
    assert "- [ ] Draft OAuth flow — owner: Karol · due: Friday" in body
    assert "- [ ] Book venue — owner: — · due: —  ⚠️ missing both" in body
    assert "```mermaid" not in body
    assert artifact.structured_json["action_items"][1]["gap"] == "missing_both"


def test_non_diagram_artifact_body_is_byte_for_byte_legacy() -> None:
    # A non-diagram plugin run: even if (pathologically) it carried a "mermaid"
    # key, the body must match the exact legacy template.
    output = {
        "summary": "Define API contract and acceptance criteria.",
        "confidence_hint": 0.82,
        "active_intents": ["architecture", "delivery"],
        "mermaid": _MERMAID,
    }
    artifacts = synthesize_meeting_artifacts(
        meeting_id="m-1",
        plugin_runs=[_run("requirements_extractor", output, run_id=101)],
    )
    assert len(artifacts) == 1
    artifact = artifacts[0]

    expected = (
        "### Requirements Extractor\n\n"
        "Define API contract and acceptance criteria.\n\n"
        "- Source windows: m-1:w0001\n"
        "- Source plugin runs: 101"
    )
    assert artifact.body_markdown == expected
    assert "```mermaid" not in artifact.body_markdown
    assert "mermaid" not in artifact.structured_json
