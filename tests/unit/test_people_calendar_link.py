"""HS-149-02 -- the link: calendar series link/resolve/unlink.

Every test uses the headless file keystore seam (HS-149-01) or the
MemoryKeyStore so ZERO keyring/keychain calls occur end-to-end.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.mcp import server
from holdspeak.mcp.families import people as people_family
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.people.keys import FileKeyStore
from holdspeak.people.store import PeopleReadiness, _dev_sidecar_path
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import (
    PeopleService,
    PeopleServiceError,
    SeriesAlreadyLinked,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.people import build_people_router


OWNER = Principal(PrincipalKind.OWNER, "calendar-link-owner")


@pytest.fixture
def service(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


@pytest.fixture
def headless_service(tmp_path: Path) -> PeopleService:
    """Full headless lifecycle through the file keystore seam."""
    keyfile = tmp_path / "headless-keys.json"
    file_store = FileKeyStore(keyfile)
    sidecar = _dev_sidecar_path(keyfile)
    people_store = EncryptedPeopleStore(sidecar, file_store)
    people_store.initialize()
    return PeopleService(people_store)


# -- Link / resolve roundtrip (acceptance 1) ----------------------------------


class TestLinkResolveRoundtrip:
    def test_link_then_resolve_returns_relationship(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ewa"})
        linked = service.link_calendar_series(
            OWNER, rel["id"], "uid-weekly-1on1", "cal-outlook", "1:1 w/ Ewa",
        )
        assert linked["calendar_links"] is not None
        assert len(linked["calendar_links"]) == 1
        link = linked["calendar_links"][0]
        assert link["uid"] == "uid-weekly-1on1"
        assert link["source_id"] == "cal-outlook"
        assert link["label"] == "1:1 w/ Ewa"
        assert "linked_at" in link

        resolved = service.resolve_relationship_by_series("uid-weekly-1on1", "cal-outlook")
        assert resolved["state"] == "ready"
        assert resolved["relationship"] is not None
        assert resolved["relationship"]["id"] == rel["id"]
        assert resolved["relationship"]["display_name"] == "Ewa"

    def test_unlink_restores_resolve_to_none(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Jan"})
        service.link_calendar_series(OWNER, rel["id"], "uid-a", "cal-1", "Weekly sync")
        service.unlink_calendar_series(OWNER, rel["id"], "uid-a", "cal-1")

        resolved = service.resolve_relationship_by_series("uid-a", "cal-1")
        assert resolved["state"] == "ready"
        assert resolved["relationship"] is None

    def test_relink_same_relationship_is_idempotent(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Karol"})
        service.link_calendar_series(OWNER, rel["id"], "uid-x", "cal-1", "Old title")
        updated = service.link_calendar_series(OWNER, rel["id"], "uid-x", "cal-1", "New title")
        assert len(updated["calendar_links"]) == 1
        assert updated["calendar_links"][0]["label"] == "New title"

    def test_headless_seam_link_resolve(self, headless_service: PeopleService) -> None:
        """Full round-trip through the file keystore seam -- zero keychain."""
        keyring_spy = MagicMock()
        import sys
        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(sys.modules, "keyring", keyring_spy)
            rel = headless_service.create_relationship(OWNER, {"display_name": "Headless"})
            headless_service.link_calendar_series(
                OWNER, rel["id"], "uid-hl", "src-hl", "Headless 1:1",
            )
            resolved = headless_service.resolve_relationship_by_series("uid-hl", "src-hl")
        assert resolved["state"] == "ready"
        assert resolved["relationship"]["id"] == rel["id"]
        assert keyring_spy.get_password.call_count == 0
        assert keyring_spy.set_password.call_count == 0


# -- P1 invariant: series_already_linked (acceptance 1) -----------------------


class TestP1Invariant:
    def test_p1_refuses_when_another_relationship_holds_series(self, service: PeopleService) -> None:
        rel_a = service.create_relationship(OWNER, {"display_name": "Alice"})
        rel_b = service.create_relationship(OWNER, {"display_name": "Bob"})
        service.link_calendar_series(OWNER, rel_a["id"], "uid-shared", "cal-1", "Team sync")

        with pytest.raises(SeriesAlreadyLinked) as exc_info:
            service.link_calendar_series(OWNER, rel_b["id"], "uid-shared", "cal-1", "Team sync")
        assert str(exc_info.value) == "series_already_linked"
        assert exc_info.value.holder_id == rel_a["id"]
        assert exc_info.value.holder_name == "Alice"

    def test_p1_allows_same_uid_different_source(self, service: PeopleService) -> None:
        rel_a = service.create_relationship(OWNER, {"display_name": "Alice"})
        rel_b = service.create_relationship(OWNER, {"display_name": "Bob"})
        service.link_calendar_series(OWNER, rel_a["id"], "uid-same", "cal-outlook", "Event A")
        # Different source_id -- no conflict.
        linked = service.link_calendar_series(OWNER, rel_b["id"], "uid-same", "cal-google", "Event B")
        assert len(linked["calendar_links"]) == 1

    def test_p1_ignores_archived_relationships(self, service: PeopleService) -> None:
        rel_old = service.create_relationship(OWNER, {"display_name": "Former"})
        rel_new = service.create_relationship(OWNER, {"display_name": "Current"})
        service.link_calendar_series(OWNER, rel_old["id"], "uid-reuse", "cal-1", "Reusable")
        service.archive_relationship(OWNER, rel_old["id"])
        # Archived relationship should not block linking.
        linked = service.link_calendar_series(OWNER, rel_new["id"], "uid-reuse", "cal-1", "Reusable")
        assert linked["calendar_links"][0]["uid"] == "uid-reuse"

    def test_multiple_links_on_one_relationship(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Multi"})
        service.link_calendar_series(OWNER, rel["id"], "uid-1", "cal-1", "Event 1")
        linked = service.link_calendar_series(OWNER, rel["id"], "uid-2", "cal-1", "Event 2")
        assert len(linked["calendar_links"]) == 2


# -- Guarded resolution (acceptance 2) ----------------------------------------


class TestGuardedResolution:
    def test_locked_sidecar_returns_unavailable(self, tmp_path: Path) -> None:
        """When the store is not ready, resolution says 'unavailable', never empty."""
        keys = MemoryKeyStore()
        store = EncryptedPeopleStore(tmp_path / "people.sqlite3", keys)
        store.initialize()
        svc = PeopleService(store)
        rel = svc.create_relationship(OWNER, {"display_name": "Test"})
        svc.link_calendar_series(OWNER, rel["id"], "uid-locked", "cal-1", "Locked test")

        # Remove the key to simulate a locked sidecar.
        keys.values.clear()
        resolved = svc.resolve_relationship_by_series("uid-locked", "cal-1")
        assert resolved["state"] == "unavailable"
        assert "relationship" not in resolved

    def test_unconfigured_store_returns_unavailable(self, tmp_path: Path) -> None:
        store = EncryptedPeopleStore(tmp_path / "nonexistent.sqlite3", MemoryKeyStore())
        svc = PeopleService(store)
        resolved = svc.resolve_relationship_by_series("uid-x", "cal-x")
        assert resolved["state"] == "unavailable"

    def test_ready_store_no_link_returns_none(self, service: PeopleService) -> None:
        resolved = service.resolve_relationship_by_series("uid-missing", "cal-missing")
        assert resolved == {"state": "ready", "relationship": None}


# -- Relationship detail includes calendar_links ------------------------------


class TestRelationshipDetail:
    def test_get_relationship_includes_calendar_links(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Detail"})
        service.link_calendar_series(OWNER, rel["id"], "uid-d", "cal-d", "Detail event")
        detail = service.get_relationship(OWNER, rel["id"])
        assert detail["calendar_links"] == [
            {"uid": "uid-d", "source_id": "cal-d", "label": "Detail event", "linked_at": detail["calendar_links"][0]["linked_at"]},
        ]

    def test_list_relationships_includes_calendar_links(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Listed"})
        service.link_calendar_series(OWNER, rel["id"], "uid-l", "cal-l", "Listed event")
        listed = service.list_relationships(OWNER)
        assert listed[0]["calendar_links"] is not None
        assert listed[0]["calendar_links"][0]["uid"] == "uid-l"


# -- Validation ---------------------------------------------------------------


class TestValidation:
    def test_empty_uid_refuses(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Val"})
        with pytest.raises(PeopleServiceError, match="people_calendar_link_required"):
            service.link_calendar_series(OWNER, rel["id"], "", "cal-1", "Label")

    def test_empty_source_id_refuses(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Val"})
        with pytest.raises(PeopleServiceError, match="people_calendar_link_required"):
            service.link_calendar_series(OWNER, rel["id"], "uid-1", "", "Label")

    def test_unlink_empty_uid_refuses(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Val"})
        with pytest.raises(PeopleServiceError, match="people_calendar_link_required"):
            service.unlink_calendar_series(OWNER, rel["id"], "", "cal-1")

    def test_unlink_nonexistent_is_idempotent(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Val"})
        result = service.unlink_calendar_series(OWNER, rel["id"], "uid-never-linked", "cal-1")
        assert result["calendar_links"] is None or result["calendar_links"] == []


# -- Schema grep pin (acceptance 3) -------------------------------------------


class TestSchemaGrepPin:
    def test_no_person_or_relationship_referencing_columns_in_schema(self) -> None:
        """The 138 law made mechanical: no People-referencing column in the
        plaintext DB schema. This test fails if anyone adds a person_id,
        people_id, relationship_id, or display_name column to schema.py.
        """
        schema_path = Path(__file__).resolve().parents[2] / "holdspeak" / "db" / "schema.py"
        schema_text = schema_path.read_text()

        # Extract only CREATE TABLE / column definitions (skip comments).
        lines = []
        for line in schema_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            lines.append(stripped)
        body = "\n".join(lines)

        # These patterns are People-domain identifiers that must NEVER appear
        # as column names in the plaintext schema.
        forbidden_columns = [
            r"\bperson_id\b",
            r"\bpeople_id\b",
            r"\brelationship_id\b",
            r"\bdisplay_name\b",
            r"\bpeople_relationship\b",
        ]
        for pattern in forbidden_columns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            assert not matches, (
                f"People-referencing column pattern {pattern!r} found in "
                f"holdspeak/db/schema.py (the 138 law): {matches}"
            )


# -- HTTP route tests ---------------------------------------------------------


def _http_client(tmp_path: Path, principal: Principal) -> TestClient:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    svc = PeopleService(store)
    app = FastAPI()

    @app.middleware("http")
    async def _stamp(request: Request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_people_router(WebContext(
        get_state=lambda: {},
        people_service=svc,
    )))
    return TestClient(app)


class TestHTTPRoutes:
    def test_post_link_and_get_detail_includes_links(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        rel = client.post("/api/people/relationships", json={"display_name": "HTTP Person"}).json()["relationship"]
        resp = client.post(
            f"/api/people/relationships/{rel['id']}/calendar-links",
            json={"uid": "uid-http", "source_id": "cal-http", "label": "HTTP Event"},
        )
        assert resp.status_code == 200
        body = resp.json()["relationship"]
        assert body["calendar_links"][0]["uid"] == "uid-http"
        assert body["calendar_links"][0]["label"] == "HTTP Event"

        detail = client.get(f"/api/people/relationships/{rel['id']}").json()["relationship"]
        assert detail["calendar_links"][0]["uid"] == "uid-http"

    def test_delete_unlink(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        rel = client.post("/api/people/relationships", json={"display_name": "HTTP Unlink"}).json()["relationship"]
        client.post(
            f"/api/people/relationships/{rel['id']}/calendar-links",
            json={"uid": "uid-del", "source_id": "cal-del", "label": "To delete"},
        )
        resp = client.request(
            "DELETE",
            f"/api/people/relationships/{rel['id']}/calendar-links",
            json={"uid": "uid-del", "source_id": "cal-del"},
        )
        assert resp.status_code == 200
        assert resp.json()["relationship"]["calendar_links"] == []

    def test_p1_returns_409(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        rel_a = client.post("/api/people/relationships", json={"display_name": "Holder"}).json()["relationship"]
        rel_b = client.post("/api/people/relationships", json={"display_name": "Rival"}).json()["relationship"]
        client.post(
            f"/api/people/relationships/{rel_a['id']}/calendar-links",
            json={"uid": "uid-conflict", "source_id": "cal-c", "label": "Conflicted"},
        )
        resp = client.post(
            f"/api/people/relationships/{rel_b['id']}/calendar-links",
            json={"uid": "uid-conflict", "source_id": "cal-c", "label": "Conflicted"},
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert detail["code"] == "series_already_linked"
        assert detail["holder_id"] == rel_a["id"]
        assert detail["holder_name"] == "Holder"


# -- MCP tool tests -----------------------------------------------------------


def _mcp_call(name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, Any]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


@pytest.fixture
def mcp_people(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "mcp-people" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    svc = PeopleService(store)
    monkeypatch.setattr(people_family, "build_people_service", lambda: svc)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    monkeypatch.delenv(people_family.ACCESS_ENV, raising=False)
    return svc


class TestMCPTools:
    def test_catalogue_includes_calendar_tools(self) -> None:
        names = {tool["name"] for tool in people_family.TOOLS}
        assert "people.calendar.link" in names
        assert "people.calendar.unlink" in names
        for tool in people_family.TOOLS:
            if tool["name"] in {"people.calendar.link", "people.calendar.unlink"}:
                assert "PEOPLE DISCLOSURE" in tool["description"]
                assert tool["inputSchema"]["additionalProperties"] is False

    def test_mcp_link_and_unlink(self, mcp_people: PeopleService) -> None:
        rel = mcp_people.create_relationship(OWNER, {"display_name": "MCP Person"})
        failed, result = _mcp_call("people.calendar.link", {
            "relationship_id": rel["id"],
            "uid": "uid-mcp",
            "source_id": "cal-mcp",
            "label": "MCP Weekly",
        })
        assert failed is False
        assert result["calendar_links"][0]["uid"] == "uid-mcp"

        failed, result = _mcp_call("people.calendar.unlink", {
            "relationship_id": rel["id"],
            "uid": "uid-mcp",
            "source_id": "cal-mcp",
        })
        assert failed is False
        assert result["calendar_links"] == []

    def test_mcp_link_requires_write(self, mcp_people: PeopleService, monkeypatch: pytest.MonkeyPatch) -> None:
        rel = mcp_people.create_relationship(OWNER, {"display_name": "Read-only"})
        monkeypatch.setenv(people_family.ACCESS_ENV, "read")
        failed, error = _mcp_call("people.calendar.link", {
            "relationship_id": rel["id"],
            "uid": "uid-ro",
            "source_id": "cal-ro",
        })
        assert failed is True
        assert error["error"] == "people_mcp_write_required"

    def test_mcp_p1_refusal(self, mcp_people: PeopleService) -> None:
        rel_a = mcp_people.create_relationship(OWNER, {"display_name": "MCP Holder"})
        rel_b = mcp_people.create_relationship(OWNER, {"display_name": "MCP Rival"})
        _mcp_call("people.calendar.link", {
            "relationship_id": rel_a["id"],
            "uid": "uid-p1",
            "source_id": "cal-p1",
            "label": "Held",
        })
        failed, error = _mcp_call("people.calendar.link", {
            "relationship_id": rel_b["id"],
            "uid": "uid-p1",
            "source_id": "cal-p1",
            "label": "Conflicted",
        })
        assert failed is True
        assert error["error"] == "series_already_linked"

    def test_mcp_relationship_get_includes_calendar_links(self, mcp_people: PeopleService) -> None:
        rel = mcp_people.create_relationship(OWNER, {"display_name": "MCP Detail"})
        mcp_people.link_calendar_series(OWNER, rel["id"], "uid-detail", "cal-d", "Detail event")
        failed, detail = _mcp_call("people.relationship.get", {"relationship_id": rel["id"]})
        assert failed is False
        assert detail["calendar_links"] is not None
        assert detail["calendar_links"][0]["uid"] == "uid-detail"

    def test_mcp_grounding_includes_calendar_links(self, mcp_people: PeopleService) -> None:
        rel = mcp_people.create_relationship(OWNER, {"display_name": "Grounding"})
        mcp_people.link_calendar_series(OWNER, rel["id"], "uid-gr", "cal-gr", "Grounded event")
        failed, grounding = _mcp_call("people.grounding.get", {"relationship_id": rel["id"]})
        assert failed is False
        assert grounding["relationship"]["calendar_links"] is not None
        assert grounding["relationship"]["calendar_links"][0]["uid"] == "uid-gr"
