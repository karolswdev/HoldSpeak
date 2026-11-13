"""HS-S55: the project-update source policy has one home.

``holdspeak/services/project_update_policy.py`` owns the policy both entry
paths share. Three identities keep their rule, one test group each:

1. a trusted HTTP run: the project is the run's own binding, never a model's
   argument, and it needs no durable credential;
2. a durable CLI run: the project is the CONDUCTOR launch credential's;
3. the private-source scope (P2): a linked 1:1 meeting and its descendants are
   withheld, an owner-filed descendant is kept, People notes are withheld, and
   a source read that fails gives nothing wider.

The end-to-end proof of both paths through the real hub is
``tests/integration/test_desk_project_room.py::
test_project_update_run_credential_scopes_native_mcp_reads_and_draft_write``.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak import principals
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import engine_tool_loop, project_update_policy as policy
from holdspeak.services.conductor_launch import RUN_IDENTITY_PREFIX

ROOT = Path(__file__).resolve().parents[2] / "holdspeak"


class FakeService:
    """The ProjectUpdateService surface the call gate reads."""

    def __init__(self, eligible: set[str], private: set[str]) -> None:
        self.eligible, self.private = eligible, private

    def project_update_meeting_ids(self, principal: Any, project_id: str):
        return set(self.private), set(self.eligible)


@pytest.fixture
def sources(monkeypatch):
    service = FakeService({"m-ok"}, {"m-1on1"})
    excluded = {"meeting:m-1on1", "action:a-private"}
    monkeypatch.setattr(policy, "update_source_service", lambda principal, project_id: (service, set(excluded)))
    return service


def _run(run_id: str = "http-run") -> Principal:
    return Principal(PrincipalKind.AGENT, f"{RUN_IDENTITY_PREFIX}{run_id}")


# ── 1. the trusted HTTP run binding ───────────────────────────────────

def test_an_http_run_has_no_cli_scope_and_binds_its_own_project(sources, monkeypatch) -> None:
    monkeypatch.setattr(principals.agent_credentials, "launch_credential", lambda identity: None)
    principal = _run()
    # No durable credential: the CLI rule does not engage.
    assert policy.project_update_scope(principal) == ""
    # The binding (the item's output target) is the project; a missing
    # argument is filled, a conflicting model-supplied one is refused.
    args, _excluded, refusal = policy.prepare_project_update_call(principal, "project.get", {}, "p1")
    assert refusal is None and args["project_id"] == "p1"
    _args, _excluded, refusal = policy.prepare_project_update_call(
        principal, "project.get", {"project_id": "p2"}, "p1")
    assert refusal == "project update reads are scoped to its project"
    args, _excluded, refusal = policy.prepare_project_update_call(principal, "memory.page", {}, "p1")
    assert refusal is None and args == {"project_id": "p1", "scope": "project"}
    _args, _excluded, refusal = policy.prepare_project_update_call(
        principal, "meeting.get", {"meeting_id": "m-1on1"}, "p1")
    assert refusal == "meeting is outside project update sources"


def test_the_http_loop_reads_the_policy_and_fails_closed(monkeypatch) -> None:
    # The loop's palette is the update's tools, and a source read that breaks
    # is a refusal, never an unfiltered call.
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
    from holdspeak.services import run_trace

    selected = policy.update_tools(resolve_palette(CONDUCTOR))
    assert "project.update_draft" in selected and selected <= policy.SAFE_TOOLS
    assert not any(name.startswith("people.") for name in selected)

    def broken(*_args: Any, **_kwargs: Any):
        raise RuntimeError("source read failed")

    monkeypatch.setattr(engine_tool_loop, "prepare_project_update_call", broken)
    monkeypatch.setattr(run_trace, "record_call", lambda *args, **kwargs: None)
    answer = engine_tool_loop.call_tool(
        "http-run", "trace", "meeting.get", {"meeting_id": "m-ok"}, 1,
        allow_project_update=True, project_id="p1",
    )
    assert json.loads(answer) == {"error": "{\"error\": \"project update sources are unavailable\"}"}


# ── 2. the durable CLI credential ─────────────────────────────────────

def test_a_cli_run_takes_its_project_from_the_durable_credential(monkeypatch) -> None:
    credentials = {
        f"{RUN_IDENTITY_PREFIX}bound": SimpleNamespace(palette_name="CONDUCTOR", project_id=" p1 "),
        f"{RUN_IDENTITY_PREFIX}plain": SimpleNamespace(palette_name="CONDUCTOR", project_id=None),
        f"{RUN_IDENTITY_PREFIX}ask": SimpleNamespace(palette_name="ASK", project_id="p1"),
    }
    monkeypatch.setattr(principals.agent_credentials, "launch_credential", credentials.get)
    palette = frozenset({"meeting.get", "project.get", "people.relationship.list", "channel.prepare"})

    bound = _run("bound")
    assert policy.project_update_scope(bound) == "p1"
    assert policy.project_update_palette(bound, palette) == {"meeting.get", "project.get", "project.update_draft"}
    assert policy.project_update_palette(bound, None) == policy.SAFE_TOOLS
    # An ordinary launch credential, an ASK credential, a non-run agent and
    # the owner keep the palette they had.
    for principal in (_run("plain"), _run("ask"), Principal(PrincipalKind.AGENT, "agent:codex"),
                      Principal(PrincipalKind.OWNER, "owner")):
        assert policy.project_update_scope(principal) == ""
        assert policy.project_update_palette(principal, palette) is palette


def test_the_update_gate_adds_only_the_draft_writer() -> None:
    gate = policy.allow_update_draft(lambda name, arguments: name == "meeting.get")
    assert gate("project.update_draft", {}) and gate("meeting.get", {})
    assert not gate("channel.send", {})


def test_both_entry_paths_import_the_one_policy() -> None:
    def imports(path: Path) -> set[str]:
        found = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.rsplit(".", 1)[-1])
        return found

    assert "project_update_policy" in imports(ROOT / "services" / "engine_tool_loop.py")
    assert "project_update_policy" in imports(ROOT / "mcp" / "server.py")
    # One direction: the policy reads neither adapter.
    assert not {"engine_tool_loop", "server"} & imports(ROOT / "services" / "project_update_policy.py")


# ── 3. the private-source scope (P2) ──────────────────────────────────

class FakeProjects:
    def __init__(self, *, meetings_fail: bool = False) -> None:
        self.meetings_fail = meetings_fail

    def list_meetings(self, principal, project_id, limit=500, offset=0):
        if self.meetings_fail:
            raise RuntimeError("meetings not read")
        return [{"id": "m-ok", "title": "Cutover sync"}, {"id": "m-1on1", "title": "1:1 with Mira"}][offset:]

    def list_resources(self, principal, project_id):
        return [
            {"resource_ref": "action:a-filed"},          # owner-filed from the 1:1: kept
            {"resource_ref": "people_note:pn-1"},        # People material: withheld
            {"resource_ref": "note:n-people"},           # a note tagged people: withheld
            {"resource_ref": "note:n-plain"},            # an ordinary note: kept
            {"resource_ref": "github:org/repo"},
        ]

    def list_action_items(self, principal, project_id):
        return [{"id": "a-private", "meeting_id": "m-1on1"}, {"id": "a-filed", "meeting_id": "m-1on1"},
                {"id": "a-ok", "meeting_id": "m-ok"}]

    def list_artifacts(self, principal, project_id):
        return [{"id": "art-private", "meeting_id": "m-1on1"}]


class FakeDb:
    meetings = SimpleNamespace(get_meeting=lambda meeting_id: None)
    notes = SimpleNamespace(get=lambda note_id: SimpleNamespace(
        title="Notes", tags=["people"] if note_id == "n-people" else ["plan"]))

    def _connection(self):
        raise RuntimeError("no decision sources here")


def test_p2_withholds_the_private_meeting_and_its_unfiled_descendants() -> None:
    excluded = policy.excluded_refs(FakeDb(), FakeProjects(), None, None, "p1")
    assert {"meeting:m-1on1", "transcript:m-1on1", "action:a-private", "action_item:a-private",
            "artifact:art-private", "people_note:pn-1", "note:n-people", "notes:n-people"} <= excluded
    # The owner-filed descendant, the ordinary meeting and note stay readable.
    assert not {"action:a-filed", "action_item:a-filed", "meeting:m-ok", "action:a-ok",
                "note:n-plain"} & excluded

    refs = policy.grounding_refs(FakeDb(), FakeProjects(), None, None, "p1")
    assert "meeting:m-ok" in refs and "action:a-filed" in refs and "note:n-plain" in refs
    assert not {"meeting:m-1on1", "people_note:pn-1", "note:n-people"} & set(refs)


def test_p2_people_names_make_a_two_person_meeting_private() -> None:
    class Db(FakeDb):
        meetings = SimpleNamespace(get_meeting=lambda meeting_id: SimpleNamespace(
            title="Cutover sync", segments=[SimpleNamespace(speaker="Me"), SimpleNamespace(speaker="Mira")])
            if meeting_id == "m-ok" else None)

    private, eligible = policy.meeting_ids(Db(), FakeProjects(), lambda principal: ["Mira"], None, "p1")
    assert private == {"m-ok", "m-1on1"} and eligible == set()


def test_p2_fails_closed_when_the_meetings_are_not_read() -> None:
    private, eligible = policy.meeting_ids(FakeDb(), FakeProjects(meetings_fail=True), None, None, "p1")
    assert private == set() and eligible == set()
    refs = policy.grounding_refs(FakeDb(), FakeProjects(meetings_fail=True), None, None, "p1")
    assert not any(ref.startswith("meeting:") for ref in refs)


def test_p2_cuts_a_private_row_from_a_tool_answer() -> None:
    payload = {"hits": [{"ref": "meeting:m-1on1", "snippet": "PRIVATE"}, {"ref": "meeting:m-ok", "snippet": "ok"}],
               "meeting": {"id": "m-1on1", "title": "1:1 with Mira", "body": "PRIVATE"}}
    response = {"result": {"content": [{"type": "text", "text": json.dumps(payload)}]}}
    cut = policy.filter_response(response, {"meeting:m-1on1"}, "memory.search")
    text = cut["result"]["content"][0]["text"]
    assert "PRIVATE" not in text and "meeting:m-ok" in text
    assert json.loads(text)["meeting"] is None


def test_the_service_names_delegate_to_the_policy(monkeypatch) -> None:
    from holdspeak.services.project_update_service import ProjectUpdateService

    calls: list[str] = []
    for name in ("meeting_ids", "excluded_refs", "grounding_refs"):
        monkeypatch.setattr(policy, name, lambda *args, _n=name: calls.append(_n) or args)
    service = ProjectUpdateService.__new__(ProjectUpdateService)
    service._db, service._project_service, service._people_names = "db", "projects", None
    assert service.project_update_meeting_ids("me", "p1") == ("db", "projects", None, "me", "p1")
    service.project_update_excluded_refs("me", "p1")
    service.project_update_grounding_refs("me", "p1")
    assert calls == ["meeting_ids", "excluded_refs", "grounding_refs"]
