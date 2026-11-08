"""One decision writer (2026-11-08): ``DecisionRecordService.create`` is the
ONE writer of ``decision_records``.

The meeting Decide well (``POST /api/decision-records/from-desk``) and the
Needs-you Accept (proposal confirm) both reach it. It writes the record, its
sources, the owner's Person reference and the Project filing
(``project_resources`` ``decision_record:<id>``, member: where every Project
reader joins) in ONE transaction, so the client makes one call.

The People seam is a stand-in with ``PeopleService.resolve_owner_candidates``'
documented answer shape: the real store is encrypted in the Keychain, which a
test never touches.
"""
from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import decision_records as record_routes

OWNER = Principal(PrincipalKind.OWNER, "owner-session")


class People:
    """``resolve_owner_candidates`` / ``display_names`` answer shapes."""

    def __init__(self, people: dict[str, str]) -> None:
        self._people = people  # id -> display name

    def resolve_owner_candidates(self, owner: str) -> dict:
        found = [pid for pid, name in self._people.items()
                 if owner.casefold() in {name.casefold(), name.split()[0].casefold()}]
        if len(found) == 1:
            return {"state": "ready", "link": "linked",
                    "relationship": {"id": found[0], "display_name": self._people[found[0]]},
                    "candidates": []}
        return {"state": "ready", "link": "not_linked", "relationship": None, "candidates": []}

    def display_names(self) -> dict[str, str]:
        return dict(self._people)


def _filings(db: Database, record_id: str) -> list[tuple[str, str]]:
    with db._connection() as conn:
        return [(r["project_id"], r["relationship"]) for r in conn.execute(
            "SELECT project_id, relationship FROM project_resources "
            "WHERE resource_ref = ? AND deleted = 0", (f"decision_record:{record_id}",),
        )]


def _client(db: Database, monkeypatch) -> TestClient:
    monkeypatch.setattr(record_routes, "get_database", lambda: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, primitive_service=PrimitiveService(db))
    app.include_router(record_routes.build_decision_records_router(ctx))
    return TestClient(app)


# ── the writer ──────────────────────────────────────────────────────────


def test_create_files_the_record_and_writes_the_person_in_one_transaction(tmp_path):
    db = Database(tmp_path / "writer.db")
    db.projects.create_project(project_id="atlas", name="Atlas")
    records = DecisionRecordService(db, people=People({"person-mira": "Mira Okafor"}))

    record = records.create(
        OWNER, decision_text="Adopt quorumdb", owner="Mira",
        source_type="meeting", source_id="dec-1",
        sources=(("meeting", "m1"),), project_id="atlas",
    )

    assert record["project_id"] == "atlas" and record["owner_person_id"] == "person-mira"
    assert record["owner"] == "Mira"  # his words stay the display name
    assert _filings(db, record["id"]) == [("atlas", "member")]
    read = records.get(OWNER, record["id"])
    assert read["project_id"] == "atlas" and read["owner_person_id"] == "person-mira"
    assert {(s["source_type"], s["source_ref"]) for s in read["sources"]} == {
        ("meeting", "m1"), ("person", "person-mira"),
    }


def test_free_text_owner_with_no_person_stays_text(tmp_path):
    db = Database(tmp_path / "text.db")
    records = DecisionRecordService(db, people=People({"person-mira": "Mira Okafor"}))

    record = records.create(OWNER, decision_text="Keep one ledger", owner="Theo",
                            source_type="desk", source_id="d-1")

    assert record["owner"] == "Theo" and record["owner_person_id"] is None
    assert records.get(OWNER, record["id"])["owner_person_id"] is None


def test_an_unknown_project_writes_nothing(tmp_path):
    db = Database(tmp_path / "unknown.db")
    records = DecisionRecordService(db)

    with pytest.raises(ValueError, match="Unknown Project"):
        records.create(OWNER, decision_text="File it nowhere", source_type="desk",
                       source_id="d-2", project_id="no-such-project")

    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 0


# ── the meeting Decide well: one call ──────────────────────────────────


def test_from_desk_files_the_record_in_its_project_in_one_call(tmp_path, monkeypatch):
    """Red on main (2204b9d57): the POST filed nothing; the client made a
    second PUT to file the record in the project."""
    db = Database(tmp_path / "from-desk.db")
    db.projects.create_project(project_id="atlas", name="Atlas")
    client = _client(db, monkeypatch)

    made = client.post("/api/decision-records/from-desk", json={
        "decision_text": "Adopt quorumdb", "title": "Adopt quorumdb", "status": "accepted",
        "project_id": "atlas", "project_name": "Atlas", "meeting_id": "m1",
    })

    assert made.status_code == 201, made.text
    record = made.json()["record"]
    assert _filings(db, record["id"]) == [("atlas", "member")]
    assert record["project_id"] == "atlas"
    # The Room reads it where it already looks.
    room = ProjectService(db)._read_room_decisions("atlas")
    assert record["id"] in {row["id"] for row in room["items"]}


def test_from_desk_carries_the_deciders_and_the_person(tmp_path, monkeypatch):
    db = Database(tmp_path / "deciders.db")
    monkeypatch.setattr(DecisionRecordService, "_people_service",
                        lambda self: People({"person-mira": "Mira Okafor"}))
    client = _client(db, monkeypatch)

    named = client.post("/api/decision-records/from-desk", json={
        "title": "Freeze on Sunday", "deciders": ["Mira", "theo@example.com", "Mira"],
    }).json()["record"]
    assert named["owner"] == "Mira, theo@example.com"
    assert named["owner_person_id"] == "person-mira"

    by_id = client.post("/api/decision-records/from-desk", json={
        "title": "Write the runbook", "owner_person_id": "person-mira",
    }).json()["record"]
    assert by_id["owner_person_id"] == "person-mira"
    assert by_id["owner"] == "Mira Okafor"


def test_from_desk_refuses_an_unknown_project_before_it_writes(tmp_path, monkeypatch):
    db = Database(tmp_path / "refused.db")
    client = _client(db, monkeypatch)

    refused = client.post("/api/decision-records/from-desk", json={
        "title": "File it nowhere", "project_id": "no-such-project",
    })

    assert refused.status_code == 400
    assert db.desk_decisions.list() == []


# ── Needs-you Accept: proposal confirm through the same writer ──────────


def test_proposal_confirm_writes_no_record_of_its_own():
    """No INSERT into ``decision_records`` (or its sources) remains in the
    proposal bridge: the record goes through ``DecisionRecordService.create``."""
    path = Path(__file__).resolve().parents[2] / "holdspeak/services/proposal_bridge_service.py"
    strings = [node.value for node in ast.walk(ast.parse(path.read_text()))
               if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    writes = [s for s in strings if "INSERT" in s.upper() and "DECISION_RECORD" in s.upper()]
    assert writes == []


def _seed_meeting(db: Database, meeting_id: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds,
                                     intel_status, capture_status)
               VALUES (?, ?, ?, 'Ledger sync', 300, 'disabled', 'finalized')""",
            (meeting_id, datetime.now().isoformat(), datetime.now().isoformat()),
        )


def test_proposal_confirm_files_the_decision_and_names_the_person(tmp_path, monkeypatch):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = Database(tmp_path / "confirm.db")
    db.projects.create_project(project_id="atlas", name="Atlas")
    _seed_meeting(db, "m-sync")
    monkeypatch.setattr(DecisionRecordService, "_people_service",
                        lambda self: People({"person-mira": "Mira Okafor"}))
    proposal = db.proposals.create_proposal(
        meeting_id="m-sync", project_id="atlas", kind="decision",
        text="Cut-over runs on the read replica first", owner_hint="Mira",
        source_plugin="decision_capture",
    )
    assert proposal is not None

    kept = ProposalBridgeService(db).confirm_proposal(OWNER, proposal.id)

    assert "error" not in kept, kept
    record = DecisionRecordService(db).get(OWNER, kept["decision_record_id"])
    assert record["source_type"] == "meeting" and record["source_id"] == kept["decision_id"]
    assert record["project_id"] == "atlas"
    assert record["owner_person_id"] == "person-mira" and record["owner"] == "Mira"
    assert record["review_date"] is None  # never '' (that read as due for review)
    assert {("meeting", "m-sync"), ("proposal", proposal.id), ("person", "person-mira")} <= {
        (s["source_type"], s["source_ref"]) for s in record["sources"]
    }
    assert _filings(db, record["id"]) == [("atlas", "member")]
    assert kept["action_item_id"] is None and kept["commitment_id"] is None
