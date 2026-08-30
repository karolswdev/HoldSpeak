"""HS-150-01 -- the owner gesture: aliases + resolution + delegated_at.

Every test uses the MemoryKeyStore so ZERO keyring/keychain calls occur.
The 149 seam env (HOLDSPEAK_PEOPLE_KEYSTORE_FILE) is tested via the
headless fixture.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import people as people_family
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.people.keys import FileKeyStore
from holdspeak.people.store import _dev_sidecar_path
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.people_service import (
    OwnerAliasTaken,
    PeopleService,
    PeopleServiceError,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.people import build_people_router


OWNER = Principal(PrincipalKind.OWNER, "owner-gesture-owner")


@pytest.fixture
def service(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


# =============================================================================
# Alias roundtrip (acceptance 1)
# =============================================================================


class TestAliasRoundtrip:
    def test_link_then_resolve_returns_relationship(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ewa"})
        linked = service.link_owner_alias(OWNER, rel["id"], "Ewa S.")
        assert linked["owner_aliases"] is not None
        assert "Ewa S." in linked["owner_aliases"]

        resolved = service.resolve_relationship_by_owner("Ewa S.")
        assert resolved["state"] == "ready"
        assert resolved["relationship"] is not None
        assert resolved["relationship"]["id"] == rel["id"]
        assert resolved["relationship"]["display_name"] == "Ewa"

    def test_unlink_restores_resolve_to_none(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Jan"})
        service.link_owner_alias(OWNER, rel["id"], "JK")
        service.unlink_owner_alias(OWNER, rel["id"], "JK")

        resolved = service.resolve_relationship_by_owner("JK")
        assert resolved["state"] == "ready"
        assert resolved["relationship"] is None

    def test_relink_same_alias_idempotent(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ada"})
        service.link_owner_alias(OWNER, rel["id"], "ADA")
        result = service.link_owner_alias(OWNER, rel["id"], "ada")
        aliases = result["owner_aliases"] or []
        # Only one entry (case-insensitive idempotent).
        assert len(aliases) == 1

    def test_multiple_aliases_per_relationship(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Bob"})
        service.link_owner_alias(OWNER, rel["id"], "Bob")
        service.link_owner_alias(OWNER, rel["id"], "Robert")
        result = service.link_owner_alias(OWNER, rel["id"], "RJ")
        aliases = result["owner_aliases"]
        assert len(aliases) == 3
        assert set(aliases) == {"Bob", "Robert", "RJ"}

        for name in ("Bob", "robert", "rj"):
            resolved = service.resolve_relationship_by_owner(name)
            assert resolved["relationship"]["id"] == rel["id"]


# =============================================================================
# P2 invariant (acceptance 1)
# =============================================================================


class TestP2Invariant:
    def test_alias_taken_by_another_relationship_raises(self, service: PeopleService) -> None:
        holder = service.create_relationship(OWNER, {"display_name": "Holder"})
        rival = service.create_relationship(OWNER, {"display_name": "Rival"})
        service.link_owner_alias(OWNER, holder["id"], "Ada")

        with pytest.raises(OwnerAliasTaken) as exc_info:
            service.link_owner_alias(OWNER, rival["id"], "ada")
        assert exc_info.value.holder_id == holder["id"]
        assert exc_info.value.holder_name == "Holder"

    def test_self_relink_idempotent(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Self"})
        service.link_owner_alias(OWNER, rel["id"], "Self")
        result = service.link_owner_alias(OWNER, rel["id"], "self")
        assert len(result["owner_aliases"] or []) == 1


# =============================================================================
# Reserved strings (acceptance 1)
# =============================================================================


class TestReservedStrings:
    @pytest.mark.parametrize("reserved", ["Me", "REMOTE", "you", "me", "YOU", "Remote"])
    def test_reserved_strings_refused(self, service: PeopleService, reserved: str) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Reserved Test"})
        with pytest.raises(PeopleServiceError, match="owner_alias_reserved"):
            service.link_owner_alias(OWNER, rel["id"], reserved)

    def test_empty_alias_refused(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Empty Test"})
        with pytest.raises(PeopleServiceError, match="owner_alias_required"):
            service.link_owner_alias(OWNER, rel["id"], "")

    def test_whitespace_alias_refused(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "WS Test"})
        with pytest.raises(PeopleServiceError, match="owner_alias_required"):
            service.link_owner_alias(OWNER, rel["id"], "   ")


# =============================================================================
# Readiness-guarded resolution (acceptance 2)
# =============================================================================


class TestGuardedResolution:
    def test_locked_sidecar_returns_unavailable(self, tmp_path: Path) -> None:
        keys = MemoryKeyStore()
        store = EncryptedPeopleStore(tmp_path / "people.sqlite3", keys)
        store.initialize()
        svc = PeopleService(store)
        rel = svc.create_relationship(OWNER, {"display_name": "Locked"})
        svc.link_owner_alias(OWNER, rel["id"], "Alice")

        # Remove the key to simulate a locked sidecar.
        keys.values.clear()

        resolved = svc.resolve_relationship_by_owner("Alice")
        assert resolved["state"] == "unavailable"

    def test_no_match_returns_ready_none(self, service: PeopleService) -> None:
        resolved = service.resolve_relationship_by_owner("nobody")
        assert resolved == {"state": "ready", "relationship": None}


# =============================================================================
# Case-insensitive resolution
# =============================================================================


class TestCaseInsensitivity:
    def test_store_preserves_case_resolve_folds(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Case"})
        service.link_owner_alias(OWNER, rel["id"], "Alice McIntosh")

        # Stored as given.
        detail = service.get_relationship(OWNER, rel["id"])
        assert "Alice McIntosh" in (detail.get("owner_aliases") or [])

        # Resolves case-insensitively.
        for variant in ("alice mcintosh", "ALICE MCINTOSH", "Alice McIntosh"):
            resolved = service.resolve_relationship_by_owner(variant)
            assert resolved["relationship"]["id"] == rel["id"]


# =============================================================================
# delegated_at on every owner-write path (acceptance 3)
# =============================================================================


def _insert_meeting(db: Database, meeting_id: str = "meeting-1") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            (meeting_id, "2026-08-01T09:00:00", "Planning"),
        )


class TestDelegatedAtUpsert:
    """The counsel pair: upsert with SAME owner leaves delegated_at untouched;
    with CHANGED owner stamps it."""

    def _make_intel(self, item_id: str, owner: str) -> Any:
        """Build a minimal intel snapshot with one action item."""
        from holdspeak.meeting_session import IntelSnapshot

        return IntelSnapshot(
            timestamp=1719820800.0,
            topics=[],
            action_items=[{
                "id": item_id,
                "task": "Follow up",
                "owner": owner,
                "due": None,
                "status": "pending",
                "review_state": "pending",
                "source_timestamp": None,
                "created_at": "2026-08-01T09:00:00",
                "completed_at": None,
                "reviewed_at": None,
            }],
            summary="test",
        )

    def test_upsert_same_owner_leaves_delegated_at_untouched(self, db: Database) -> None:
        """Intel re-extraction with SAME owner: owner+delegated_at byte-untouched."""
        _insert_meeting(db)
        intel = self._make_intel("ai-same-owner", "Ada")

        # First upsert: creates the row.
        with db._connection() as conn:
            db.meetings._save_intel(conn, "meeting-1", intel)

        with db._connection() as conn:
            row = conn.execute("SELECT owner, delegated_at FROM action_items WHERE id = 'ai-same-owner'").fetchone()
            assert row["owner"] == "Ada"
            # Fresh insert with an owner: delegated_at is NULL (from the INSERT VALUES).
            assert row["delegated_at"] is None

        # Second upsert: same owner, same task.
        with db._connection() as conn:
            db.meetings._save_intel(conn, "meeting-1", intel)

        with db._connection() as conn:
            row = conn.execute("SELECT owner, delegated_at FROM action_items WHERE id = 'ai-same-owner'").fetchone()
            assert row["owner"] == "Ada"
            # MUST remain untouched (the counsel pair law).
            assert row["delegated_at"] is None

    def test_upsert_changed_owner_stamps_delegated_at(self, db: Database) -> None:
        """Intel re-extraction with CHANGED owner: stamps delegated_at."""
        _insert_meeting(db)
        intel_ada = self._make_intel("ai-change-owner", "Ada")

        with db._connection() as conn:
            db.meetings._save_intel(conn, "meeting-1", intel_ada)

        # Change the owner.
        intel_bob = self._make_intel("ai-change-owner", "Bob")
        with db._connection() as conn:
            db.meetings._save_intel(conn, "meeting-1", intel_bob)

        with db._connection() as conn:
            row = conn.execute("SELECT owner, delegated_at FROM action_items WHERE id = 'ai-change-owner'").fetchone()
            assert row["owner"] == "Bob"
            assert row["delegated_at"] is not None
            # Verify it is a valid ISO timestamp.
            datetime.fromisoformat(row["delegated_at"])


class TestDelegatedAtDelegate:
    def test_delegate_verb_stamps_on_owner_change(self, db: Database) -> None:
        _insert_meeting(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state) "
                "VALUES ('ai-delegate', 'meeting-1', 'Do it', 'Alice', 'open', 'accepted')"
            )
        ft = FollowThroughService(db)
        ft.complete(OWNER, "ai-delegate", "delegate", {"to": "Bob"})

        with db._connection() as conn:
            row = conn.execute("SELECT owner, delegated_at FROM action_items WHERE id = 'ai-delegate'").fetchone()
            assert row["owner"] == "Bob"
            assert row["delegated_at"] is not None

    def test_delegate_verb_same_owner_no_stamp(self, db: Database) -> None:
        _insert_meeting(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state) "
                "VALUES ('ai-del-same', 'meeting-1', 'Do it', 'Alice', 'open', 'accepted')"
            )
        ft = FollowThroughService(db)
        ft.complete(OWNER, "ai-del-same", "delegate", {"to": "Alice"})

        with db._connection() as conn:
            row = conn.execute("SELECT delegated_at FROM action_items WHERE id = 'ai-del-same'").fetchone()
            assert row["delegated_at"] is None


class TestDelegatedAtEditActionItem:
    def test_edit_stamps_on_owner_change(self, db: Database) -> None:
        _insert_meeting(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state) "
                "VALUES ('ai-edit', 'meeting-1', 'Task', 'Alice', 'pending', 'pending')"
            )
        db.meetings.edit_action_item("ai-edit", task="New task", owner="Bob", due=None)

        with db._connection() as conn:
            row = conn.execute("SELECT owner, delegated_at FROM action_items WHERE id = 'ai-edit'").fetchone()
            assert row["owner"] == "Bob"
            assert row["delegated_at"] is not None

    def test_edit_same_owner_no_stamp(self, db: Database) -> None:
        _insert_meeting(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state) "
                "VALUES ('ai-edit-same', 'meeting-1', 'Task', 'Alice', 'pending', 'pending')"
            )
        db.meetings.edit_action_item("ai-edit-same", task="New task", owner="Alice", due=None)

        with db._connection() as conn:
            row = conn.execute("SELECT delegated_at FROM action_items WHERE id = 'ai-edit-same'").fetchone()
            assert row["delegated_at"] is None


class TestDelegatedAtCommitDecision:
    def test_commit_decision_stamps_fresh_insert(self, db: Database) -> None:
        from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

        _insert_meeting(db, "decision-meeting")
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, decided_at, source_artifact_id, source_meeting_id, lifecycle)
                   VALUES (?, ?, ?, ?, ?, 'recorded')""",
                ("dec-1", "Ship it", "2026-08-01", "art-1", "decision-meeting"),
            )
        DecisionLifecycleService(db).transition(OWNER, "dec-1", "accept")

        ft = FollowThroughService(db)
        result = ft.commit_decision(OWNER, "dec-1", owner="Carol", due_at="2026-09-01")

        with db._connection() as conn:
            row = conn.execute(
                "SELECT delegated_at FROM action_items WHERE id = ?",
                (result["action_item_id"],),
            ).fetchone()
            assert row["delegated_at"] is not None

    def test_commit_decision_no_owner_no_stamp(self, db: Database) -> None:
        from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

        _insert_meeting(db, "decision-meeting-2")
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, decided_at, source_artifact_id, source_meeting_id, lifecycle)
                   VALUES (?, ?, ?, ?, ?, 'recorded')""",
                ("dec-2", "Defer it", "2026-08-01", "art-2", "decision-meeting-2"),
            )
        DecisionLifecycleService(db).transition(OWNER, "dec-2", "accept")

        ft = FollowThroughService(db)
        result = ft.commit_decision(OWNER, "dec-2", owner=None)

        with db._connection() as conn:
            row = conn.execute(
                "SELECT delegated_at FROM action_items WHERE id = ?",
                (result["action_item_id"],),
            ).fetchone()
            assert row["delegated_at"] is None


# =============================================================================
# delegated_at on the board read side (acceptance 3 cont.)
# =============================================================================


class TestDelegatedAtBoardReadSide:
    def test_board_card_carries_delegated_at(self, db: Database) -> None:
        _insert_meeting(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state, delegated_at) "
                "VALUES ('ai-board', 'meeting-1', 'Task', 'Alice', 'open', 'accepted', '2026-08-28T12:00:00')"
            )
        board = FollowThroughService(db).board(OWNER)
        cards = board.now + board.waiting + board.overdue + board.unassigned
        card = next(c for c in cards if c.id == "ai-board")
        assert card.delegated_at == "2026-08-28T12:00:00"

    def test_board_card_null_delegated_at(self, db: Database) -> None:
        _insert_meeting(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state) "
                "VALUES ('ai-board-null', 'meeting-1', 'Task', 'Alice', 'open', 'accepted')"
            )
        board = FollowThroughService(db).board(OWNER)
        cards = board.now + board.waiting + board.overdue + board.unassigned
        card = next(c for c in cards if c.id == "ai-board-null")
        assert card.delegated_at is None


# =============================================================================
# Schema grep pin extension (acceptance 4)
# =============================================================================


class TestSchemaGrepPin:
    def test_delegated_at_present_and_no_person_reference(self) -> None:
        """delegated_at must exist in the schema and be a bare timestamp
        with no person/relationship reference (the 138 law)."""
        schema_path = Path(__file__).resolve().parents[2] / "holdspeak" / "db" / "schema.py"
        schema_text = schema_path.read_text()

        # delegated_at must be present.
        assert "delegated_at" in schema_text, "delegated_at column missing from schema.py"

        # Extract only CREATE TABLE / column definitions (skip comments).
        lines = []
        for line in schema_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            lines.append(stripped)
        body = "\n".join(lines)

        # The 138 law: no People-domain identifiers as column names.
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


# =============================================================================
# MCP catalogue extension
# =============================================================================


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


class TestMCPCatalogue:
    def test_catalogue_includes_owner_alias_tools(self) -> None:
        names = {tool["name"] for tool in people_family.TOOLS}
        assert "people.owner_alias.link" in names
        assert "people.owner_alias.unlink" in names
        for tool in people_family.TOOLS:
            if tool["name"] in {"people.owner_alias.link", "people.owner_alias.unlink"}:
                assert "PEOPLE DISCLOSURE" in tool["description"]
                assert tool["inputSchema"]["additionalProperties"] is False

    def test_catalogue_is_closed(self) -> None:
        """The closed-catalogue pattern from 149, extended with the new tools."""
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
        }
        assert not any(
            fragment in name
            for name in names
            for fragment in ("setup", "archive", "delete", "capture", "transcript", "infer", "search", "sync", "export")
        )

    def test_mcp_link_and_resolve(self, mcp_people: PeopleService) -> None:
        rel = mcp_people.create_relationship(OWNER, {"display_name": "MCP Person"})
        failed, result = _mcp_call("people.owner_alias.link", {
            "relationship_id": rel["id"],
            "alias": "MCP Alias",
        })
        assert failed is False
        assert "MCP Alias" in (result.get("owner_aliases") or [])

        # Verify resolve works.
        resolved = mcp_people.resolve_relationship_by_owner("mcp alias")
        assert resolved["relationship"]["id"] == rel["id"]

    def test_mcp_unlink(self, mcp_people: PeopleService) -> None:
        rel = mcp_people.create_relationship(OWNER, {"display_name": "MCP Unlink"})
        _mcp_call("people.owner_alias.link", {
            "relationship_id": rel["id"],
            "alias": "ToRemove",
        })
        failed, result = _mcp_call("people.owner_alias.unlink", {
            "relationship_id": rel["id"],
            "alias": "ToRemove",
        })
        assert failed is False
        assert "ToRemove" not in (result.get("owner_aliases") or [])


# =============================================================================
# HTTP routes
# =============================================================================


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
    def test_post_link_alias_and_get_detail(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        rel = client.post("/api/people/relationships", json={"display_name": "HTTP Alias"}).json()["relationship"]
        resp = client.post(
            f"/api/people/relationships/{rel['id']}/owner-aliases",
            json={"alias": "HTTP Owner"},
        )
        assert resp.status_code == 200
        body = resp.json()["relationship"]
        assert "HTTP Owner" in (body.get("owner_aliases") or [])

        detail = client.get(f"/api/people/relationships/{rel['id']}").json()["relationship"]
        assert "HTTP Owner" in (detail.get("owner_aliases") or [])

    def test_delete_unlink_alias(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        rel = client.post("/api/people/relationships", json={"display_name": "HTTP Unlink Alias"}).json()["relationship"]
        client.post(
            f"/api/people/relationships/{rel['id']}/owner-aliases",
            json={"alias": "ToUnlink"},
        )
        resp = client.request(
            "DELETE",
            f"/api/people/relationships/{rel['id']}/owner-aliases",
            json={"alias": "ToUnlink"},
        )
        assert resp.status_code == 200
        assert "ToUnlink" not in (resp.json()["relationship"].get("owner_aliases") or [])

    def test_p2_returns_409(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        holder = client.post("/api/people/relationships", json={"display_name": "Holder"}).json()["relationship"]
        rival = client.post("/api/people/relationships", json={"display_name": "Rival"}).json()["relationship"]
        client.post(
            f"/api/people/relationships/{holder['id']}/owner-aliases",
            json={"alias": "ConflictAlias"},
        )
        resp = client.post(
            f"/api/people/relationships/{rival['id']}/owner-aliases",
            json={"alias": "conflictalias"},
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert detail["code"] == "owner_alias_taken"
        assert detail["holder_id"] == holder["id"]
        assert detail["holder_name"] == "Holder"

    def test_reserved_returns_422(self, tmp_path: Path) -> None:
        client = _http_client(tmp_path, OWNER)
        rel = client.post("/api/people/relationships", json={"display_name": "Reserved"}).json()["relationship"]
        resp = client.post(
            f"/api/people/relationships/{rel['id']}/owner-aliases",
            json={"alias": "Me"},
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "owner_alias_reserved"
