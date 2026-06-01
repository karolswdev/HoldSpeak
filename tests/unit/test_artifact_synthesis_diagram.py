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


def test_decisions_artifact_embeds_decisions_and_questions() -> None:
    # HS-27-03: decision_capture output → a decisions/open-questions body + keys.
    runs = [
        _run(
            "decision_capture",
            {
                "summary": "1 decision(s); 1 open question(s).",
                "confidence_hint": 1.0,
                "active_intents": ["delivery"],
                "decisions": [{"decision": "Adopt the API gateway", "rationale": "Central auth"}],
                "open_questions": ["Who owns the migration?"],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "decisions"

    body = artifact.body_markdown
    assert "**Decisions**" in body
    assert "- Adopt the API gateway — Central auth" in body
    assert "**Open questions**" in body
    assert "- Who owns the migration?" in body
    assert artifact.structured_json["decisions"][0]["decision"] == "Adopt the API gateway"
    assert artifact.structured_json["open_questions"] == ["Who owns the migration?"]


def test_requirements_artifact_embeds_grouped_body() -> None:
    # HS-27-04: requirements_extractor output → a grouped body + structured key.
    runs = [
        _run(
            "requirements_extractor",
            {
                "summary": "3 requirement(s) (2 functional, 1 non-functional).",
                "confidence_hint": 1.0,
                "active_intents": ["product"],
                "requirements": [
                    {"text": "Users can export reports as PDF", "type": "functional"},
                    {"text": "Page loads within 200ms", "type": "non_functional"},
                    {"text": "Support SSO login", "type": "functional"},
                ],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "requirements"

    body = artifact.body_markdown
    assert "**Functional**" in body
    assert "- Users can export reports as PDF" in body
    assert "- Support SSO login" in body
    assert "**Non-functional**" in body
    assert "- Page loads within 200ms" in body
    # Functional group renders before the non-functional group.
    assert body.index("**Functional**") < body.index("**Non-functional**")
    assert "```mermaid" not in body
    assert artifact.structured_json["requirements"][0]["text"] == "Users can export reports as PDF"


def test_adr_artifact_embeds_records_body() -> None:
    # HS-28-02: adr_drafter output → an ADR body + structured key.
    runs = [
        _run(
            "adr_drafter",
            {
                "summary": "1 ADR(s); 1 accepted.",
                "confidence_hint": 1.0,
                "active_intents": ["architecture"],
                "adrs": [
                    {
                        "title": "Use Postgres for billing",
                        "status": "accepted",
                        "context": "Need transactional integrity",
                        "decision": "Adopt Postgres over DynamoDB",
                        "consequences": "Run a managed Postgres",
                    }
                ],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "adr"

    body = artifact.body_markdown
    assert "**Use Postgres for billing** — _accepted_" in body
    assert "- Context: Need transactional integrity" in body
    assert "- Decision: Adopt Postgres over DynamoDB" in body
    assert "- Consequences: Run a managed Postgres" in body
    assert "```mermaid" not in body
    assert artifact.structured_json["adrs"][0]["status"] == "accepted"


def test_milestone_artifact_embeds_plan_body() -> None:
    # HS-28-03: milestone_planner output → a milestone-plan body + structured key.
    runs = [
        _run(
            "milestone_planner",
            {
                "summary": "1 milestone(s); 1 with a target date.",
                "confidence_hint": 1.0,
                "active_intents": ["delivery"],
                "milestones": [
                    {
                        "name": "Beta launch",
                        "target": "Q3",
                        "deliverables": ["Auth", "Billing"],
                        "dependencies": ["API freeze"],
                    }
                ],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "milestone_plan"

    body = artifact.body_markdown
    assert "**Beta launch** — Q3" in body
    assert "- Deliverables: Auth, Billing" in body
    assert "- Dependencies: API freeze" in body
    assert "```mermaid" not in body
    assert artifact.structured_json["milestones"][0]["name"] == "Beta launch"


def test_risk_register_artifact_embeds_table_body() -> None:
    # HS-28-04: risk_heatmap output → a risk-register table body + structured key.
    runs = [
        _run(
            "risk_heatmap",
            {
                "summary": "1 risk(s); 1 high-impact.",
                "confidence_hint": 1.0,
                "active_intents": ["incident"],
                "risks": [
                    {
                        "risk": "Migration could lose data",
                        "impact": "high",
                        "likelihood": "low",
                        "mitigation": "Dry-run + backup",
                        "owner": "Maria",
                    }
                ],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "risk_register"

    body = artifact.body_markdown
    assert "| Risk | Impact | Likelihood | Mitigation | Owner |" in body
    assert "| Migration could lose data | high | low | Dry-run + backup | Maria |" in body
    assert "```mermaid" not in body
    assert artifact.structured_json["risks"][0]["impact"] == "high"


def test_dependency_map_artifact_embeds_edge_body() -> None:
    # HS-29-01: dependency_mapper output → an edge-list body + structured key.
    runs = [
        _run(
            "dependency_mapper",
            {
                "summary": "1 dependency edge(s) mapped.",
                "confidence_hint": 1.0,
                "active_intents": ["delivery"],
                "dependencies": [{"from": "Billing", "to": "API freeze", "note": "contract locked"}],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    artifact = artifacts[0]
    assert artifact.artifact_type == "dependency_map"
    assert "- Billing → API freeze — contract locked" in artifact.body_markdown
    assert artifact.structured_json["dependencies"][0]["to"] == "API freeze"


def test_scope_review_artifact_embeds_grouped_body() -> None:
    # HS-29-01: scope_guard output → a grouped scope body + structured key.
    runs = [
        _run(
            "scope_guard",
            {
                "summary": "2 scope finding(s); 1 flagged as scope creep.",
                "confidence_hint": 1.0,
                "active_intents": ["product"],
                "findings": [
                    {"item": "PDF export", "verdict": "in_scope", "rationale": "agreed"},
                    {"item": "Live chat", "verdict": "scope_creep", "rationale": "new ask"},
                ],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    artifact = artifacts[0]
    assert artifact.artifact_type == "scope_review"
    body = artifact.body_markdown
    assert "**In scope**" in body
    assert "- PDF export — agreed" in body
    assert "**Scope creep**" in body
    assert "- Live chat — new ask" in body
    assert artifact.structured_json["findings"][1]["verdict"] == "scope_creep"


def test_customer_signals_artifact_embeds_list_body() -> None:
    # HS-29-01: customer_signal_extractor output → a signals body + structured key.
    runs = [
        _run(
            "customer_signal_extractor",
            {
                "summary": "1 customer signal(s) (1 pain).",
                "confidence_hint": 1.0,
                "active_intents": ["product"],
                "signals": [{"signal": "Dashboard too slow", "type": "pain", "quote": "it crawls"}],
            },
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    artifact = artifacts[0]
    assert artifact.artifact_type == "customer_signals"
    assert '- _pain_: Dashboard too slow — "it crawls"' in artifact.body_markdown
    assert artifact.structured_json["signals"][0]["type"] == "pain"


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
