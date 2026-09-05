"""Security-scoped MCP coverage for the encrypted People capability."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import resources, server
from holdspeak.mcp.families import people as people_family
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService


OWNER = Principal(PrincipalKind.OWNER, "people-mcp-owner")


@pytest.fixture
def people_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    service = PeopleService(store)
    monkeypatch.setattr(people_family, "build_people_service", lambda: service)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    monkeypatch.delenv(people_family.ACCESS_ENV, raising=False)
    return service


def _call(name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, Any]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def test_people_mcp_default_is_write_and_readiness_does_not_open_store_when_off(
    people_service: PeopleService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HS-139-08: the default is now "write" (owner ruling: ledger-not-gate).
    The invariants that still hold:
    - Readiness never opens the store when access is off.
    - Leader-private material is never serialized.
    - Explicit env can still set off/read.
    """
    # Verify the default is "write" (no env var set).
    assert people_family.access_mode() == "write"

    # Explicit env override to "off" — the store must NOT be composed.
    monkeypatch.setenv(people_family.ACCESS_ENV, "off")
    monkeypatch.setattr(
        people_family,
        "build_people_service",
        lambda: pytest.fail("disabled readiness must not compose the encrypted store"),
    )

    failed, readiness = _call("people.readiness")
    assert failed is False
    assert readiness == {
        "access": "disabled",
        "disclosure": "shared_intent_only",
        "reason_code": "people_mcp_access_disabled",
        "store": "not_opened",
    }

    failed, error = _call("people.relationship.list")
    assert failed is True
    assert error == {"error": "people_mcp_access_disabled"}

    # Explicit env override to "read" — reads work, writes refused.
    monkeypatch.setenv(people_family.ACCESS_ENV, "read")
    assert people_family.access_mode() == "read"


def test_people_mcp_read_projection_omits_every_leader_private_field(
    people_service: PeopleService, monkeypatch: pytest.MonkeyPatch
) -> None:
    relationship = people_service.create_relationship(OWNER, {
        "display_name": "Shared Relationship",
        "role_context": "Platform",
    })
    private_session = people_service.create_one_on_one(OWNER, relationship["id"], {
        "agenda": "PRIVATE SESSION SENTINEL",
        "private_prep": "PRIVATE PREP SENTINEL",
        "visibility": "leader_private",
    })
    people_service.add_agenda_item(OWNER, private_session["id"], {
        "body": "PRIVATE AGENDA SENTINEL",
        "visibility": "leader_private",
    })
    shared_session = people_service.create_one_on_one(OWNER, relationship["id"], {
        "agenda": "Shared session",
        "visibility": "shared_intent",
    })
    people_service.add_agenda_item(OWNER, shared_session["id"], {
        "body": "Shared agenda",
        "visibility": "shared_intent",
    })
    people_service.create_request(OWNER, relationship["id"], {
        "body": "PRIVATE REQUEST SENTINEL",
        "visibility": "leader_private",
    })
    shared_request = people_service.create_request(OWNER, relationship["id"], {
        "body": "Shared request",
        "visibility": "shared_intent",
    })
    people_service.accept_request(OWNER, shared_request["id"])
    people_service.create_note(OWNER, relationship["id"], {
        "body": "PRIVATE NOTE SENTINEL", "visibility": "leader_private",
    })
    people_service.create_note(OWNER, relationship["id"], {
        "topic": "Shared context", "body": "Shared grounding note", "visibility": "shared_intent",
    })
    people_service.link_project(OWNER, relationship["id"], "proj-platform")
    monkeypatch.setenv(people_family.ACCESS_ENV, "read")

    failed, detail = _call("people.relationship.get", {"relationship_id": relationship["id"]})

    assert failed is False
    rendered = json.dumps(detail, sort_keys=True)
    assert "Shared Relationship" in rendered
    assert "Shared agenda" in rendered
    assert "Shared request" in rendered
    assert "private_prep" not in rendered
    assert "PRIVATE SESSION SENTINEL" not in rendered
    assert "PRIVATE PREP SENTINEL" not in rendered
    assert "PRIVATE AGENDA SENTINEL" not in rendered
    assert "PRIVATE REQUEST SENTINEL" not in rendered
    assert "PRIVATE NOTE SENTINEL" not in rendered
    assert "Shared grounding note" in rendered
    assert len(detail["sessions"]) == 1
    assert len(detail["requests"]) == 1
    assert len(detail["commitments"]) == 1
    assert len(detail["notes"]) == 1
    assert detail["project_refs"] == ["proj-platform"]

    failed, grounding = _call("people.grounding.get", {"relationship_id": relationship["id"]})
    assert failed is False
    assert grounding["policy"] == {
        "employment_decisions": "prohibited",
        "inference": "client_owned",
        "source": "manual",
        "visibility": "shared_intent_only",
    }
    assert grounding["grounding"]["notes"][0]["body"] == "Shared grounding note"
    assert grounding["relationship"]["project_refs"] == ["proj-platform"]


def test_people_mcp_write_flow_uses_domain_service_and_encrypted_authority(
    people_service: PeopleService, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(people_family.ACCESS_ENV, "write")

    failed, relationship = _call("people.relationship.create", {
        "display_name": "MCP Relationship",
        "role_context": "Architecture",
    })
    assert failed is False
    failed, session = _call("people.one_on_one.create", {
        "relationship_id": relationship["id"],
        "agenda": "Weekly continuity",
        "private_prep": "IGNORED PRIVATE INJECTION",
        "visibility": "leader_private",
    })
    assert failed is False
    assert session["visibility"] == "shared_intent"
    assert "private_prep" not in session
    failed, agenda = _call("people.agenda.add", {
        "session_id": session["id"],
        "body": "Discuss the migration",
    })
    assert failed is False
    assert agenda["visibility"] == "shared_intent"
    failed, note = _call("people.note.create", {
        "relationship_id": relationship["id"],
        "topic": "Collaboration",
        "body": "Prefers written design context",
    })
    assert failed is False
    assert note["visibility"] == "shared_intent"
    failed, request = _call("people.request.create", {
        "relationship_id": relationship["id"],
        "body": "Provide design feedback",
    })
    assert failed is False
    assert people_service.list_cards(OWNER) == []
    failed, commitment = _call("people.request.accept", {"request_id": request["id"]})
    assert failed is False
    assert commitment["request_id"] == request["id"]
    assert len(people_service.list_cards(OWNER)) == 1
    failed, transition = _call("people.commitment.transition", {
        "commitment_id": commitment["id"],
        "verb": "done",
    })
    assert failed is False
    assert transition == {"card_id": f"people:{commitment['id']}", "verb": "done"}
    assert people_service.list_cards(OWNER) == []


def test_people_mcp_read_capability_refuses_writes_and_private_record_ids(
    people_service: PeopleService, monkeypatch: pytest.MonkeyPatch
) -> None:
    relationship = people_service.create_relationship(OWNER, {"display_name": "Boundary"})
    private_request = people_service.create_request(OWNER, relationship["id"], {
        "body": "PRIVATE REQUEST BODY",
        "visibility": "leader_private",
    })
    monkeypatch.setenv(people_family.ACCESS_ENV, "read")
    failed, error = _call("people.request.create", {
        "relationship_id": relationship["id"],
        "body": "No write",
    })
    assert failed is True
    assert error == {"error": "people_mcp_write_required"}

    monkeypatch.setenv(people_family.ACCESS_ENV, "write")
    failed, error = _call("people.request.accept", {"request_id": private_request["id"]})
    assert failed is True
    assert error == {"error": "people_mcp_private_record_refused"}
    assert "PRIVATE REQUEST BODY" not in json.dumps(error)
    assert people_service.list_cards(OWNER) == []


def test_people_mcp_resources_share_the_same_capability_and_redaction(
    people_service: PeopleService, monkeypatch: pytest.MonkeyPatch
) -> None:
    relationship = people_service.create_relationship(OWNER, {"display_name": "Resource Relationship"})
    people_service.create_request(OWNER, relationship["id"], {
        "body": "RESOURCE PRIVATE SENTINEL",
        "visibility": "leader_private",
    })
    people_service.create_request(OWNER, relationship["id"], {
        "body": "Resource shared request",
        "visibility": "shared_intent",
    })
    monkeypatch.setenv(people_family.ACCESS_ENV, "read")

    catalog = resources.list_resources()
    assert any(item["uri"] == "holdspeak://people/relationships" for item in catalog["resources"])
    assert any(item["uriTemplate"] == "holdspeak://people/relationships/{id}" for item in catalog["resourceTemplates"])
    result = resources.read_resource(f"holdspeak://people/relationships/{relationship['id']}", OWNER)
    text = result["contents"][0]["text"]
    assert "Resource Relationship" in text
    assert "Resource shared request" in text
    assert "RESOURCE PRIVATE SENTINEL" not in text


def test_people_mcp_catalogue_is_closed_and_does_not_offer_forbidden_operations() -> None:
    names = {tool["name"] for tool in people_family.TOOLS}
    assert names == {
        "people.readiness",
        "people.relationship.list",
        "people.relationship.get",
        "people.grounding.get",
        "people.one_on_one.brief",
        "people.relationship.create",
        "people.one_on_one.create",
        "people.agenda.add",
        "people.note.create",
        "people.request.create",
        "people.request.accept",
        "people.commitment.transition",
        "people.calendar.link",
        "people.calendar.unlink",
        "people.owner_alias.link",
        "people.owner_alias.unlink",
        "people.resolve",
    }
    assert not any(
        fragment in name
        for name in names
        for fragment in ("setup", "archive", "delete", "capture", "transcript", "infer", "search", "sync", "export")
    )
    for tool in people_family.TOOLS:
        assert tool["inputSchema"]["additionalProperties"] is False
        if tool["name"] != "people.readiness":
            assert "PEOPLE DISCLOSURE" in tool["description"]
