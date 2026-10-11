"""The populated-project seed from the parked HS-158 Room glass (the test diet,
2026-10-11): a verbatim copy, so live browser tests (the desk sweep) keep it
after `tests/e2e/_parked/test_hs158_room_glass.py` was parked."""

from __future__ import annotations

from typing import Any

from .glass_infra import _api

TOKEN = "hs158-room-glass"


def _seed_populated_project(page: Any) -> str:
    """Create a realistic Senior-Architect project through the real API.

    Returns the project id. Creates:
    - 2 milestones (one reached, one planned)
    - 2 risks (one critical open, one medium mitigated)
    - 1 dependency at_risk
    - 1 signal active
    - 1 workstream active

    Room fields (purpose, outcome_text, lifecycle, posture) are written
    via the DB layer because no HTTP PATCH route exposes them.
    """
    created = _api(page, "POST", "/api/projects", {
        "name": "Payments Platform Rewrite",
        "description": "Migrate from legacy payment gateway to modern event-driven architecture.",
        "command_id": "hs158-glass-create",
    }, token=TOKEN)
    project = created["project"]
    project_id = project["id"]

    # Write room fields directly via DB (no HTTP route exists).
    from holdspeak.db import get_database
    db = get_database()
    db.projects.update_project_room_fields(
        project_id,
        purpose="Replace the monolithic payment gateway with an event-driven platform that supports real-time settlement and multi-currency clearing.",
        outcome_text="All production payment traffic routes through the new platform with zero-downtime cutover by Q1.",
        lifecycle="active",
        posture="on_track",
        posture_reason="Sprint 4 velocity stable; PCI audit passed.",
    )

    # Items through the real API.
    items: list[dict[str, Any]] = [
        {
            "item_type": "milestone",
            "title": "PCI-DSS audit passed",
            "summary": "External auditor confirmed compliance for the new gateway.",
            "lifecycle": "reached",
            "due_at": "2026-07-15",
        },
        {
            "item_type": "milestone",
            "title": "Production cutover",
            "summary": "Route all live traffic through the new event-driven pipeline.",
            "lifecycle": "planned",
            "severity": "high",
            "due_at": "2026-10-01",
        },
        {
            "item_type": "risk",
            "title": "Settlement latency under load",
            "summary": "P99 settlement exceeds 800ms at projected Black Friday volume.",
            "lifecycle": "open",
            "severity": "critical",
            "due_at": "2026-09-15",
            "details": {"likelihood": "high", "impact": "critical", "mitigation": "Horizontal scaling spike test scheduled."},
        },
        {
            "item_type": "risk",
            "title": "Legacy API deprecation timeline",
            "summary": "Stripe v2 sunset pushed back; dual-write window extended.",
            "lifecycle": "mitigated",
            "severity": "medium",
            "details": {"likelihood": "low", "impact": "medium", "mitigation": "Dual-write window extended through Q1."},
        },
        {
            "item_type": "dependency",
            "title": "Compliance team sign-off",
            "summary": "Legal review of multi-currency clearing rules pending.",
            "lifecycle": "at_risk",
            "severity": "high",
            "due_at": "2026-09-01",
            "details": {"direction": "upstream", "counterpart_ref": "team:compliance"},
        },
        {
            "item_type": "signal",
            "title": "Partner bank integration interest",
            "summary": "Two partner banks expressed interest in direct settlement API.",
            "lifecycle": "active",
            "details": {"metric": "partner_interest_count", "latest_value": 2},
        },
        {
            "item_type": "workstream",
            "title": "Event sourcing migration",
            "summary": "Move transaction log from RDBMS to event store.",
            "lifecycle": "active",
        },
    ]
    # Each item creation bumps the project revision; skip expected_revision
    # to avoid tracking it across the chain (legacy behavior: API-006).
    for item_payload in items:
        _api(page, "POST", f"/api/projects/{project_id}/items", {
            **{k: v for k, v in item_payload.items() if v is not None},
        }, token=TOKEN)

    return project_id


