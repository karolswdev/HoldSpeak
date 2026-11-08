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
    # The proposal's own chain stays a decision's (no action of its own) ...
    assert kept["action_item_id"] is None and kept["commitment_id"] is None
    # ... and the owned, filed record is committed once, to Mira.
    assert _commitments(db) == [(f"commitment-{record['id']}", kept["decision_id"], "Mira")]
    assert record["committed_to"] == "Mira"
    replay = ProposalBridgeService(db).confirm_proposal(OWNER, proposal.id)
    assert replay["replayed"] is True
    assert len(_commitments(db)) == 1


# ── 2026-11-08: a decision with an owner commits once ───────────────────


def _commitments(db: Database) -> list[tuple[str, str, str]]:
    with db._connection() as conn:
        return [(r["id"], r["decision_id"], r["owner"]) for r in conn.execute(
            "SELECT id, decision_id, owner FROM decision_commitments ORDER BY created_at")]


def _desk_client(db: Database, monkeypatch) -> TestClient:
    db.projects.create_project(project_id="atlas", name="Atlas")
    monkeypatch.setattr(DecisionRecordService, "_people_service",
                        lambda self: People({"person-mira": "Mira Okafor"}))
    return _client(db, monkeypatch)


def test_a_from_desk_decision_with_an_owner_commits_once(tmp_path, monkeypatch):
    """Red on main (6f5923221): the record named Mira and filed in Atlas, and
    nobody was asked to do anything (no action item, no commitment)."""
    db = Database(tmp_path / "commit.db")
    client = _desk_client(db, monkeypatch)

    made = client.post("/api/decision-records/from-desk", json={
        "title": "Adopt quorumdb", "status": "accepted",
        "project_id": "atlas", "owner_person_id": "person-mira",
    })

    assert made.status_code == 201, made.text
    record = made.json()["record"]
    assert _commitments(db) == [(f"commitment-{record['id']}", record["source_id"], "Mira Okafor")]
    assert record["committed_to"] == "Mira Okafor"
    with db._connection() as conn:
        action = conn.execute("SELECT task, owner, due, status FROM action_items").fetchall()
    assert [tuple(row) for row in action] == [("Adopt quorumdb", "Mira Okafor", None, "open")]
    # The Room's decision row names the same person (#1891 follow-up).
    room = ProjectService(db)._read_room_decisions("atlas")
    assert [(i["id"], i["committed_to"]) for i in room["items"]] == [(record["id"], "Mira Okafor")]


def test_a_second_accept_makes_no_second_commitment(tmp_path, monkeypatch):
    db = Database(tmp_path / "accept.db")
    client = _desk_client(db, monkeypatch)

    made = client.post("/api/decision-records/from-desk", json={
        "title": "Freeze on Sunday", "status": "proposed",
        "project_id": "atlas", "owner_person_id": "person-mira",
    }).json()
    assert _commitments(db) == []  # proposed: nothing to commit yet

    desk_id = made["decision"]["id"]
    PrimitiveService(db).update_decision_status(OWNER, desk_id, "accepted")
    PrimitiveService(db).update_decision_status(OWNER, desk_id, "accepted")

    assert _commitments(db) == [(f"commitment-{made['record']['id']}", desk_id, "Mira Okafor")]


def test_no_owner_or_no_project_commits_nothing(tmp_path, monkeypatch):
    db = Database(tmp_path / "none.db")
    client = _desk_client(db, monkeypatch)

    unowned = client.post("/api/decision-records/from-desk", json={
        "title": "Keep one ledger", "status": "accepted", "project_id": "atlas",
    }).json()["record"]
    unfiled = client.post("/api/decision-records/from-desk", json={
        "title": "Write the runbook", "status": "accepted", "owner_person_id": "person-mira",
    }).json()["record"]

    assert _commitments(db) == []
    assert unowned["committed_to"] is None and unfiled["committed_to"] is None


def test_the_route_answers_the_writers_commitment(tmp_path, monkeypatch):
    """The MCP/SDK route reaches the same function: no second commitment."""
    from holdspeak.services.follow_through_service import FollowThroughService

    db = Database(tmp_path / "route.db")
    client = _desk_client(db, monkeypatch)
    record = client.post("/api/decision-records/from-desk", json={
        "title": "Adopt quorumdb", "status": "accepted",
        "project_id": "atlas", "owner_person_id": "person-mira",
    }).json()["record"]

    again = FollowThroughService(db).commit_decision(OWNER, record["id"])

    assert again["id"] == f"commitment-{record['id']}" and again["replayed"] is True
    assert len(_commitments(db)) == 1


def _calls(tree: ast.AST) -> dict[str, set[str]]:
    """Each function's name -> the attribute names it calls."""
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            found.setdefault(node.name, set()).update(
                call.func.attr for call in ast.walk(node)
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute))
    return found


def test_one_place_builds_the_decision_commitment():
    """The writer and the route reach ONE function; only it inserts the
    commitment (the proposal bridge's action chain is an action's own)."""
    root = Path(__file__).resolve().parents[2] / "holdspeak"
    inserts: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            if any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                   and "INSERT INTO DECISION_COMMITMENTS" in " ".join(c.value.upper().split())
                   for c in ast.walk(fn)):
                inserts.setdefault(str(path.relative_to(root)), []).append(fn.name)
    assert inserts == {
        "services/follow_through_service.py": ["commit_decision_in_transaction"],
        "services/proposal_bridge_service.py": ["confirm_proposal"],
    }
    service = _calls(ast.parse((root / "services/follow_through_service.py").read_text()))
    assert "commit_decision_in_transaction" in service["commit_decision"]
    writer = _calls(ast.parse((root / "services/decision_record_service.py").read_text()))
    assert "commit_decision_in_transaction" in writer["_commit"]
    assert "_commit" in writer["create"] and "_commit_if_owned" in writer["sync_from_desk"]
    route = _calls(ast.parse((root / "web/routes/follow_through.py").read_text()))
    assert "commit_decision" in route["commit_decision"]
