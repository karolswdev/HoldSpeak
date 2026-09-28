"""PHILO-9-06 catalogue gap 1: an owner-only operation says so.

Found by the closing use (Codex, cold context): the agent's
``project.mark_update_delivered`` was refused ``project_delegation_required``
and Codex told the owner "this agent lacks project delegation", although no
grant can ever admit it (the owner's bound is run, stop, publish). An
operation outside ``PROJECT_GRANT_OPERATIONS`` is refused to an agent
``owner_principal_required`` (the code story 07 uses for grant and revoke);
only the grantable bound says ``project_delegation_required``. One receipt per
refusal, unchanged. A real Settings-issued PROJECT credential, over ``/api/mcp``
and over HTTP, without and with a LIVE grant.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo9_project_grant import _call, _grant, _op, _refused_with_receipt, hub  # noqa: E402,F401
from test_philo9_steward_admission import _agent, _project, _published, _tool  # noqa: E402

OWNER_REQUIRED = "owner_principal_required"


def _owner_only(agent: Any, pid: str, published: str) -> dict[str, tuple[Any, Any]]:
    return {
        "project.mark_update_delivered": (
            lambda: _tool(agent, "project.mark_update_delivered", {"update_id": published, "delivered_to": "Priya"}),
            lambda: agent.post(f"/api/updates/{published}/delivered", json={"delivered_to": "Priya"})),
        "project.archive": (
            lambda: _tool(agent, "project.archive", {"project_id": pid}),
            lambda: agent.delete(f"/api/projects/{pid}")),
        "project.configure_steward": (
            lambda: _tool(agent, "project.configure_steward", {"project_id": pid, "unattended_enabled": True}),
            lambda: agent.put(f"/api/projects/{pid}/steward/policy", json={"unattended_enabled": True})),
    }


@pytest.mark.parametrize("phase", ["no_grant", "live_grant"])
def test_an_owner_only_operation_is_refused_owner_principal_required(hub: Any, phase: str) -> None:  # noqa: F811
    pid = _project(hub)
    published = _published(hub, pid)
    agent = _agent(hub)
    if phase == "live_grant":
        _grant(hub, pid)
    for name, (mcp, http) in _owner_only(agent, pid, published).items():
        is_error, body = mcp()
        assert is_error, (phase, name, body)
        _refused_with_receipt(hub, body, name, OWNER_REQUIRED)
        resp = http()
        assert resp.status_code == 403, (phase, name, resp.text)
        answer = resp.json()
        assert OWNER_REQUIRED in {answer.get("code"), answer.get("error")}, (phase, name, answer)
        assert _op(hub, answer["operation_id"])["outcome"] == OWNER_REQUIRED, (phase, name, answer)


def test_the_grantable_bound_still_says_project_delegation_required(hub: Any) -> None:  # noqa: F811
    pid = _project(hub)
    agent = _agent(hub)
    for transport in ("mcp", "http"):
        refused, body = _call(agent, transport, "project.run_steward", {"pid": pid})
        assert refused
        _refused_with_receipt(hub, body, "project.run_steward", "project_delegation_required")


def test_no_owner_only_descriptor_names_a_delegation_code() -> None:
    from holdspeak.kernel import project as rooms
    from holdspeak.operations import DESCRIPTORS

    by_name = {d.name: d for d in DESCRIPTORS}
    admitted = rooms.ROOM_ADMITTED | rooms.STEWARD_AND_CONNECTORS_ADMITTED
    checked = 0
    for name in sorted(admitted - rooms.PROJECT_GRANT_OPERATIONS):
        if name not in by_name:
            continue
        checked += 1
        assert "project_delegation_required" not in by_name[name].refusals, name
    for name in sorted(rooms.PROJECT_GRANT_OPERATIONS):
        assert "project_delegation_required" in " ".join(by_name[name].refusals), name
    assert checked >= 20


