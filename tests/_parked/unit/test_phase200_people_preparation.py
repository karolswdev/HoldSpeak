"""HS-200-14 -- permitted People preparation (planned suite
``phase200_people_preparation``, the unit half).

The five acceptance criteria, each fenced against a REAL encrypted People
store (``EncryptedPeopleStore`` + ``MemoryKeyStore``) and a real
``Database`` -- no MagicMock stands in for the resolver, because a double
that lies about the field a check reads proves nothing (the HS-200-05 scar).

  AC1  an owner string two people could be meant by is AMBIGUOUS and is
       never attributed -- neither by the candidate resolver nor by the
       172-04 Watch-identity resolver (which, pre-fix, attributed a shared
       display name to whichever relationship the store listed first);
  AC2  a linked person carries their open commitments (story 12's chain,
       source span linked) and their observable facts, each with a source;
  AC3  protected People fields never enter the projection, the Room
       snapshot (= MCP ``project.get_room``), the meeting export, or the
       route payload; only ``id`` + ``display_name`` cross;
  AC5  a locked, unconfigured or absent ledger is NAMED and every owner
       the Project names becomes a typed gap -- never an empty section.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database, get_observer
from holdspeak.meeting_exports import render_meeting_export
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.people.keys import PeopleKeyError
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.people_service import PeopleService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.room_people_service import (
    LEDGER_STATES,
    LINK_STATES,
    RESERVED_OWNERS,
    room_people,
    room_people_preparation,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.projects import build_projects_router

OWNER = Principal(PrincipalKind.OWNER, "hs200-14-owner")

#: The four protected content classes (tests/unit/test_people_no_leaks.py:19).
SENTINELS = (
    "PEOPLE-SENTINEL-PRIVATE-PREP",
    "PEOPLE-SENTINEL-AGENDA",
    "PEOPLE-SENTINEL-REQUEST",
    "PEOPLE-SENTINEL-NOTE",
    "PEOPLE-SENTINEL-ALIAS",
    "PEOPLE-SENTINEL-ROLE",
)

#: What a Room row is allowed to carry from the People store (172-07's two
#: fields) -- everything else on the row is the plaintext DB's own data.
LINKED_ROW_KEYS = {
    "relationship_id", "display_name", "link", "commitments", "facts", "omitted_sources",
    "prs_waiting", "assignments_open", "assignments_overdue",
}
GAP_ROW_KEYS = {"owner", "link", "candidates", "commitments"}
CANDIDATE_KEYS = {"relationship_id", "display_name"}


# ── fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "holdspeak.db")


@pytest.fixture()
def projects(db: Database) -> ProjectService:
    return ProjectService(db, observer=get_observer())


def _people(tmp_path: Path, *, key_store: Any = None) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people-private" / "people.v1.sqlite3", key_store or MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


def _seed_project(db: Database, project_id: str = "proj-14", name: str = "Q4 platform") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
            (project_id, name),
        )
    return project_id


def _seed_meeting(db: Database, project_id: str, meeting_id: str = "m-review", title: str = "Architecture review") -> str:
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, 1800.0, 'complete', 'finalized', 'desktop')",
            (meeting_id, (now - timedelta(hours=2)).isoformat(), (now - timedelta(hours=1)).isoformat(), title),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id, source, confidence) "
            "VALUES (?, ?, 'manual', 1.0)",
            (meeting_id, project_id),
        )
    return meeting_id


def _seed_commitment(
    db: Database,
    project_id: str,
    meeting_id: str,
    *,
    owner: str,
    text: str,
    due: str | None = None,
    segment_index: int | None = 3,
    status: str = "open",
) -> str:
    """Story 12's confirmed chain, as ``confirm_proposal`` writes it
    (proposal_bridge_service.py:632-748): decisions -> decision_records
    (+ sources) -> action_items -> decision_commitments, and the confirmed
    proposal that carries the transcript span."""
    now = datetime.now().isoformat()
    decision_id = f"dec-{uuid.uuid4().hex[:12]}"
    record_id = f"record-{uuid.uuid4().hex[:12]}"
    action_id = f"action-{uuid.uuid4().hex[:12]}"
    commitment_id = f"commitment-{uuid.uuid4().hex[:12]}"
    proposal_id = f"prop-{uuid.uuid4().hex[:12]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO decisions (id, text, rationale, decided_at, date_basis, source_timestamp, "
            " provenance_label, source_artifact_id, source_meeting_id, project_key, lifecycle, "
            " created_at, updated_at, last_modified) "
            "VALUES (?, ?, '', ?, 'meeting_date', 12.0, 'anchored', '', ?, ?, 'accepted', ?, ?, ?)",
            (decision_id, text, now, meeting_id, project_id, now, now, now),
        )
        conn.execute(
            "INSERT INTO decision_records (id, decision_text, rationale, alternatives, owner, review_date, "
            " lifecycle, source_type, source_id, created_at, updated_at) "
            "VALUES (?, ?, '', '', ?, '', 'active', 'meeting', ?, ?, ?)",
            (record_id, text, owner, decision_id, now, now),
        )
        conn.execute(
            "INSERT INTO decision_record_sources (id, record_id, source_type, source_ref, created_at) "
            "VALUES (?, ?, 'meeting', ?, ?)",
            (f"record-source-{uuid.uuid4().hex[:12]}", record_id, meeting_id, now),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, "
            " source_timestamp, created_at, delegated_at, source_type, source_ref) "
            "VALUES (?, ?, ?, ?, ?, 'open', 'accepted', 12.0, ?, ?, 'meeting', ?)",
            (action_id, meeting_id, text, owner, due, now, now, meeting_id),
        )
        conn.execute(
            "INSERT INTO decision_commitments (id, decision_id, action_item_id, owner, due_at, status, "
            " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (commitment_id, decision_id, action_id, owner, due, status, now, now),
        )
        conn.execute(
            "INSERT INTO follow_through_proposals "
            "(id, meeting_id, project_id, kind, text, owner_hint, due_hint, source_plugin, fingerprint, "
            " state, model_host, created_at, decision_record_id, commitment_id, segment_index, "
            " span_start, span_end) "
            "VALUES (?, ?, ?, 'action', ?, ?, ?, 'decision_capture', ?, 'confirmed', '192.168.1.43', ?, "
            " ?, ?, ?, 10.0, 14.5)",
            (proposal_id, meeting_id, project_id, text, owner, due, f"fp-{uuid.uuid4().hex[:12]}", now,
             record_id, commitment_id, segment_index),
        )
    return commitment_id


def _seed_watch(
    db: Database,
    project_id: str,
    watch_id: str,
    *,
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    name: str = "karolswdev/HoldSpeak",
    query: dict | None = None,
    snapshot: list[dict[str, Any]] | None = None,
    state: str = "active",
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, "
            " last_success_at, last_error, project_id, state, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), NULL, ?, ?, datetime('now'), datetime('now'))",
            (watch_id, connector_id, query_kind, name, json.dumps(query or {}), json.dumps(snapshot or []), project_id, state),
        )


def _relationship(people: PeopleService, name: str, *, aliases: tuple[str, ...] = (), project: str | None = None, **extra: Any) -> str:
    created = people.create_relationship(OWNER, {"display_name": name, **extra})
    rid = str(created["id"])
    for alias in aliases:
        people.link_owner_alias(OWNER, rid, alias)
    if project:
        people.link_project(OWNER, rid, project)
    return rid


def _by_owner(projection: dict[str, Any], owner: str) -> dict[str, Any]:
    return next(r for r in projection["unresolved"] if r["owner"] == owner)


def _by_name(projection: dict[str, Any], name: str) -> dict[str, Any]:
    return next(r for r in projection["people"] if r["display_name"] == name)


# ── AC1: ambiguous aliases require resolution ───────────────────────


class TestAmbiguousOwners:
    def test_shared_first_name_is_ambiguous_and_never_attributed(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid)
        _seed_commitment(db, pid, mid, owner="Priya", text="Confirm the freeze window", due="2026-09-19")
        people = _people(tmp_path)
        sharma = _relationship(people, "Priya Sharma")
        nair = _relationship(people, "Priya Nair")

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert projection["state"] == "ready"
        assert projection["people"] == [], "an ambiguous owner must not become a linked row"
        gap = _by_owner(projection, "Priya")
        assert gap["link"] == "ambiguous"
        assert {c["relationship_id"] for c in gap["candidates"]} == {sharma, nair}
        assert [c["text"] for c in gap["commitments"]] == ["Confirm the freeze window"]
        assert projection["gaps"]["ambiguous"] == 1
        assert projection["expected"] == 1 and projection["resolved"] == 0

    def test_candidate_resolver_never_guesses(self, tmp_path: Path) -> None:
        people = _people(tmp_path)
        sharma = _relationship(people, "Priya Sharma")
        nair = _relationship(people, "Priya Nair")
        kumar = _relationship(people, "Anil Kumar", aliases=("anil-k",))

        two = people.resolve_owner_candidates("Priya")
        assert two["link"] == "ambiguous" and two["relationship"] is None
        assert {c["id"] for c in two["candidates"]} == {sharma, nair}
        assert set(two["candidates"][0]) == {"id", "display_name"}

        # One near match is a SUGGESTION, not an attribution (D1: never a
        # hedged guess).
        one = people.resolve_owner_candidates("Anil")
        assert one["link"] == "not_linked" and one["relationship"] is None
        assert [c["id"] for c in one["candidates"]] == [kumar]

        # An exact alias or an exact, unique display name links.
        assert people.resolve_owner_candidates("anil-k")["link"] == "linked"
        assert people.resolve_owner_candidates("priya sharma")["relationship"]["id"] == sharma

        # Nobody: not linked, no candidates.
        nobody = people.resolve_owner_candidates("Zbigniew")
        assert nobody["link"] == "not_linked" and nobody["candidates"] == []

        # The reserved owner strings are never a person.
        assert people.resolve_owner_candidates("me")["link"] == "not_linked"

    def test_identical_display_names_no_longer_attribute_by_store_order(self, tmp_path: Path) -> None:
        """The pre-fix defect: ``resolve_relationship_by_watch_identity``
        returned the FIRST of two relationships that share a display name
        (people_service.py, pass 2), attributing one Priya's PRs to the
        other."""
        people = _people(tmp_path)
        first = _relationship(people, "Priya")
        second = _relationship(people, "Priya")

        result = people.resolve_relationship_by_watch_identity("priya")

        assert result["state"] == "ready"
        assert result["relationship"] is None, "a shared display name was attributed to store order"
        assert result.get("ambiguous") is True
        assert {c["id"] for c in result["candidates"]} == {first, second}

    def test_resolution_by_alias_links_the_owner_in_place(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        """`Resolve` = the existing owner-alias link (people_service.link_owner_alias);
        after it the same owner string is LINKED and its commitments move onto
        the person's row."""
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid)
        _seed_commitment(db, pid, mid, owner="Priya", text="Confirm the freeze window")
        people = _people(tmp_path)
        sharma = _relationship(people, "Priya Sharma")
        _relationship(people, "Priya Nair")

        people.link_owner_alias(OWNER, sharma, "Priya")
        projection = room_people_preparation(projects, people, pid, OWNER)

        assert projection["unresolved"] == []
        row = _by_name(projection, "Priya Sharma")
        assert row["relationship_id"] == sharma
        assert [c["text"] for c in row["commitments"]] == ["Confirm the freeze window"]


# ── AC2: source-backed commitments and observable facts ─────────────


class TestSourceBackedPreparation:
    def test_linked_person_carries_commitments_with_span_and_facts_with_source(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid, title="Architecture review")
        cid = _seed_commitment(db, pid, mid, owner="marek", text="Own the PostgreSQL migration", due="2026-09-20", segment_index=4)
        _seed_commitment(db, pid, mid, owner="marek", text="Already done", status="completed")
        _seed_watch(db, pid, "w-prs", snapshot=[
            {"number": 1, "title": "feat A", "state": "OPEN", "reviewRequests": ["marek-k"]},
            {"number": 2, "title": "feat B", "state": "OPEN", "reviewRequests": ["marek-k"]},
            {"number": 3, "title": "merged", "state": "MERGED", "reviewRequests": ["marek-k"]},
        ])
        _seed_watch(db, pid, "w-issues", connector_id="jira", query_kind="issues", name="KAN", snapshot=[
            {"key": "KAN-1", "summary": "task", "assignee": "marek-k", "due_at": "2020-01-01"},
        ])
        people = _people(tmp_path)
        marek = _relationship(people, "Marek Kubiak", aliases=("marek", "marek-k"))

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert projection["state"] == "ready"
        assert projection["expected"] == 1 and projection["resolved"] == 1
        assert projection["gaps"] == {"ambiguous": 0, "not_linked": 0, "unreadable": 0}
        row = _by_name(projection, "Marek Kubiak")
        assert row["relationship_id"] == marek and row["link"] == "linked"
        # The commitment: story 12's record, its due date, its source span.
        assert [c["id"] for c in row["commitments"]] == [cid], "completed commitments stay out"
        commitment = row["commitments"][0]
        assert commitment["text"] == "Own the PostgreSQL migration"
        assert commitment["due_at"] == "2026-09-20"
        assert commitment["source"] == {
            "kind": "meeting", "meeting_id": mid, "label": "Architecture review",
            "segment_index": 4, "span_start": 10.0, "span_end": 14.5,
        }
        # The facts: each with the Watch it came from; nothing inferred.
        facts = {(f["kind"], f["source"]["label"]): f["count"] for f in row["facts"]}
        assert facts == {
            ("prs_waiting", "karolswdev/HoldSpeak"): 2,
            ("assignments_open", "KAN"): 1,
            ("assignments_overdue", "KAN"): 1,
        }
        assert row["prs_waiting"] == 2 and row["assignments_open"] == 1 and row["assignments_overdue"] == 1
        for fact in row["facts"]:
            assert set(fact) == {"kind", "count", "source"}
            assert set(fact["source"]) == {"kind", "watch_id", "connector_id", "label"}
        # Nothing inferred: no score, motive, authority or comparison field.
        assert not {k for k in row if "score" in k or "rank" in k or "sentiment" in k}

    def test_person_linked_to_the_project_appears_without_records(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = _seed_project(db)
        people = _people(tmp_path)
        ania = _relationship(people, "Ania Kowalska", project=pid)
        _relationship(people, "Elsewhere Person", project="proj-other")

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert [r["relationship_id"] for r in projection["people"]] == [ania]
        row = projection["people"][0]
        assert row["commitments"] == [] and row["facts"] == [] and row["omitted_sources"] == []
        assert "prs_waiting" not in row, "counts are absent at zero (A.8)"

    def test_done_commitment_leaves_people_through_the_real_verb(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        """Counsel P0 (probe_closed): `Done` on the Follow-through board writes
        ``decision_commitments.status = 'closed'`` (follow_through_service.py:401);
        the projection read ``!= 'completed'`` and kept it OPEN forever."""
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid)
        cid = _seed_commitment(db, pid, mid, owner="Priya", text="Confirm the freeze window")
        people = _people(tmp_path)
        _relationship(people, "Priya Sharma", aliases=("Priya",))
        with db._connection() as conn:
            action_id = conn.execute("SELECT action_item_id FROM decision_commitments WHERE id = ?", (cid,)).fetchone()[0]
        before = room_people_preparation(projects, people, pid, OWNER)
        assert [c["id"] for c in _by_name(before, "Priya Sharma")["commitments"]] == [cid]

        FollowThroughService(db).complete(OWNER, action_id, "done", {})
        with db._connection() as conn:
            assert conn.execute("SELECT status FROM decision_commitments WHERE id = ?", (cid,)).fetchone()[0] == "closed"

        after = room_people_preparation(projects, people, pid, OWNER)
        assert after["expected"] == 0 and after["people"] == [] and after["unresolved"] == [], "a Done commitment stayed open in PEOPLE"

        FollowThroughService(db).complete(OWNER, action_id, "reopen", {})
        reopened = room_people_preparation(projects, people, pid, OWNER)
        assert [c["id"] for c in _by_name(reopened, "Priya Sharma")["commitments"]] == [cid]

    def test_reserved_owner_strings_never_make_a_row(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        """Counsel P2-i: `me`/`remote`/`you` name the owner himself; the ledger
        refuses them as aliases (people_service._RESERVED_OWNER_ALIASES), so a
        row for them would carry a `Link` refused by name downstream."""
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid)
        for owner in ("me", "Me ", "remote", "you"):
            _seed_commitment(db, pid, mid, owner=owner, text=f"Own the thing myself ({owner})")
        _seed_commitment(db, pid, mid, owner="Zbigniew", text="Someone else's")
        people = _people(tmp_path)

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert [r["owner"] for r in projection["unresolved"]] == ["Zbigniew"]
        assert projection["expected"] == 1
        assert RESERVED_OWNERS == frozenset({"me", "remote", "you"})

    def test_revoked_source_facts_are_omitted_with_the_state_named(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        """Charter test plan "revoked source" (counsel P2-v): a paused or
        retired Watch's counts never appear, and the omission is a typed
        row on the person, not a silent gap."""
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-live", name="karolswdev/HoldSpeak", snapshot=[
            {"number": 1, "title": "feat A", "state": "OPEN", "reviewRequests": ["marek-k"]},
        ])
        _seed_watch(db, pid, "w-paused", name="karolswdev/Paused", state="paused", snapshot=[
            {"number": 2, "title": "feat B", "state": "OPEN", "reviewRequests": ["marek-k"]},
            {"number": 3, "title": "feat C", "state": "OPEN", "reviewRequests": ["marek-k"]},
        ])
        _seed_watch(db, pid, "w-retired", connector_id="jira", query_kind="issues", name="KAN", state="retired", snapshot=[
            {"key": "KAN-1", "summary": "task", "assignee": "marek-k", "due_at": "2020-01-01"},
        ])
        people = _people(tmp_path)
        _relationship(people, "Marek Kubiak", aliases=("marek-k",))

        projection = room_people_preparation(projects, people, pid, OWNER)

        row = _by_name(projection, "Marek Kubiak")
        assert row["prs_waiting"] == 1 and "assignments_open" not in row and "assignments_overdue" not in row
        assert [(f["kind"], f["source"]["label"], f["count"]) for f in row["facts"]] == [("prs_waiting", "karolswdev/HoldSpeak", 1)]
        omitted = sorted((o["label"], o["state"]) for o in row["omitted_sources"])
        assert omitted == [("KAN", "retired"), ("karolswdev/Paused", "paused")]
        for o in row["omitted_sources"]:
            assert set(o) == {"kind", "watch_id", "connector_id", "label", "state"}
        # The shade's list agrees: only the live count.
        assert room_people(projects, people, pid) == [
            {"relationship_id": row["relationship_id"], "display_name": "Marek Kubiak", "prs_waiting": 1},
        ]

    def test_unresolved_watch_login_never_crosses(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-prs", snapshot=[
            {"number": 1, "title": "feat A", "state": "OPEN", "reviewRequests": ["stranger-login"]},
        ])
        people = _people(tmp_path)
        _relationship(people, "Ania Kowalska", aliases=("ania-dev",))

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert "stranger-login" not in json.dumps(projection)
        assert projection["expected"] == 0

    def test_172_list_still_feeds_the_shade(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-prs", snapshot=[
            {"number": 1, "title": "feat A", "state": "OPEN", "reviewRequests": ["ania-dev"]},
        ])
        people = _people(tmp_path)
        ania = _relationship(people, "Ania Kowalska", aliases=("ania-dev",))
        _relationship(people, "No Counts", project=pid)

        assert room_people(projects, people, pid) == [
            {"relationship_id": ania, "display_name": "Ania Kowalska", "prs_waiting": 1},
        ]


# ── AC3: protected fields stay in their permitted paths ──────────────


class TestProtectedFieldsStayHome:
    """Drive the projection with a person carrying every protected field and
    assert the sentinels are absent from EVERY output this story feeds:

      1. the projection dict itself (and its row keys are the allow-list);
      2. the HTTP route payload (``GET /api/projects/{id}/people``);
      3. the Room snapshot -- which IS the MCP ``project.get_room`` result
         (holdspeak/mcp/families/project.py:1181-1183 returns
         ``ProjectService.room`` unchanged);
      4. the meeting export (markdown and json) of the source meeting;
      5. the plaintext database file the projection read from.
    """

    def _seed(self, tmp_path: Path, db: Database) -> tuple[str, str, PeopleService]:
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid)
        _seed_commitment(db, pid, mid, owner="Priya", text="Confirm the freeze window")
        _seed_commitment(db, pid, mid, owner="Nobody Known", text="Bring the runbook")
        people = _people(tmp_path)
        rid = _relationship(
            people, "Priya Sharma", aliases=("Priya", SENTINELS[4]), project=pid,
            role_context=SENTINELS[5],
        )
        session = people.create_one_on_one(OWNER, rid, {"private_prep": SENTINELS[0], "visibility": "leader_private"})
        people.add_agenda_item(OWNER, session["id"], {"body": SENTINELS[1], "visibility": "shared_intent"})
        request = people.create_request(OWNER, rid, {"body": SENTINELS[2], "visibility": "leader_private"})
        people.accept_request(OWNER, request["id"])
        people.create_note(OWNER, rid, {"topic": "Grounding", "body": SENTINELS[3], "visibility": "leader_private"})
        # A second Priya so the ambiguity path (candidates) is exercised too.
        _relationship(people, "Priya Nair")
        return pid, mid, people

    @staticmethod
    def _assert_clean(label: str, text: str) -> None:
        for sentinel in SENTINELS:
            assert sentinel not in text, f"protected field escaped into {label}: {sentinel}"

    def test_projection_carries_only_the_two_permitted_fields(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid, mid, people = self._seed(tmp_path, db)

        projection = room_people_preparation(projects, people, pid, OWNER)
        serialized = json.dumps(projection)

        self._assert_clean("the projection", serialized)
        assert projection["people"], "the alias-linked Priya must be a linked row"
        for row in projection["people"]:
            assert set(row) <= LINKED_ROW_KEYS, f"unexpected People field on a row: {set(row) - LINKED_ROW_KEYS}"
        for row in projection["unresolved"]:
            assert set(row) == GAP_ROW_KEYS
            for candidate in row["candidates"]:
                assert set(candidate) == CANDIDATE_KEYS
        # The relationship's own protected attributes never ride along.
        for field in ("owner_aliases", "role_context", "timezone", "cadence", "calendar_links", "private_prep", "agenda", "notes", "requests", "visibility"):
            assert field not in serialized

    def test_route_snapshot_export_and_db_stay_clean(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid, mid, people = self._seed(tmp_path, db)

        # 2. The HTTP route.
        app = FastAPI()

        @app.middleware("http")
        async def principal_state(request: Request, call_next):  # type: ignore[no-untyped-def]
            request.state.principal = OWNER
            return await call_next(request)

        app.include_router(build_projects_router(WebContext(get_state=lambda: {}, project_service=projects, people_service=people)))
        client = TestClient(app)
        response = client.get(f"/api/projects/{pid}/people")
        assert response.status_code == 200, response.text
        self._assert_clean("GET /api/projects/{id}/people", response.text)
        payload = response.json()
        assert payload["state"] == "ready" and payload["people"][0]["display_name"] == "Priya Sharma"

        # 3. The Room snapshot == MCP project.get_room.
        room = projects.room(OWNER, pid)
        self._assert_clean("ProjectService.room / project.get_room", json.dumps(room, default=str))

        # 4. The meeting export, both formats.
        meeting = db.meetings.get_meeting(mid)
        assert meeting is not None
        for fmt in ("markdown", "json"):
            self._assert_clean(f"meeting export ({fmt})", render_meeting_export(meeting, fmt, artifacts=[]))

        # 5. The plaintext database the projection read from.
        db.close()
        self._assert_clean("holdspeak.db", (tmp_path / "holdspeak.db").read_bytes().decode("latin-1"))

    def test_no_field_is_a_derived_summary(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        """Charter test plan "derived summary" (counsel P2-v): the projection
        is an allow-list of facts with sources.  No key on any row, fact,
        commitment, source or candidate is a score, rank, summary, risk,
        sentiment, comparison or any other derivation -- and the allow-list
        this fence already enforces is the whole vocabulary."""
        pid, _mid, people = self._seed(tmp_path, db)
        _seed_watch(db, pid, "w-prs", snapshot=[
            {"number": 1, "title": "feat A", "state": "OPEN", "reviewRequests": ["Priya Sharma"]},
        ])
        projection = room_people_preparation(projects, people, pid, OWNER)

        forbidden = ("score", "rank", "summary", "sentiment", "risk", "compare", "authority", "motive", "health", "velocity", "performance")

        def keys_of(obj: Any) -> set[str]:
            found: set[str] = set()
            if isinstance(obj, dict):
                found.update(str(k) for k in obj)
                for v in obj.values():
                    found |= keys_of(v)
            elif isinstance(obj, list):
                for v in obj:
                    found |= keys_of(v)
            return found

        every_key = keys_of(projection)
        assert not {k for k in every_key if any(word in k.lower() for word in forbidden)}, every_key
        assert every_key <= (
            {"state", "expected", "resolved", "gaps", "people", "unresolved", "ambiguous", "not_linked", "unreadable"}
            | LINKED_ROW_KEYS | GAP_ROW_KEYS | CANDIDATE_KEYS
            | {"id", "text", "due_at", "owner", "source", "kind", "meeting_id", "label", "segment_index", "span_start", "span_end"}
            | {"count", "watch_id", "connector_id"}
        ), every_key - LINKED_ROW_KEYS
        assert _by_name(projection, "Priya Sharma")["facts"], "the fence walked a row that carries facts"


# ── AC5: missing or locked People context is a typed partial ─────────


class _LockedKeyStore(MemoryKeyStore):
    """A native store that answers but refuses -- what a locked Keychain does
    (keys.py:66-71 maps any backend failure to ``people_key_store_locked``)."""

    def __init__(self) -> None:
        super().__init__()
        self.locked = False

    def get(self, key_id: str) -> bytes:
        if self.locked:
            raise PeopleKeyError("people_key_store_locked")
        return super().get(key_id)


class TestTypedPartials:
    def _project_with_owner(self, db: Database) -> str:
        pid = _seed_project(db)
        mid = _seed_meeting(db, pid)
        _seed_commitment(db, pid, mid, owner="Priya", text="Confirm the freeze window")
        _seed_commitment(db, pid, mid, owner="Marek", text="Own the migration")
        _seed_watch(db, pid, "w-prs", snapshot=[
            {"number": 1, "title": "feat A", "state": "OPEN", "reviewRequests": ["ania-dev"]},
        ])
        return pid

    def test_locked_keychain_is_named_and_every_owner_is_a_locked_gap(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = self._project_with_owner(db)
        keys = _LockedKeyStore()
        people = _people(tmp_path, key_store=keys)
        _relationship(people, "Priya Sharma", aliases=("Priya",))
        keys.locked = True

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert projection["state"] == "locked"
        assert projection["people"] == []
        assert projection["expected"] == 2 and projection["resolved"] == 0
        assert projection["gaps"] == {"ambiguous": 0, "not_linked": 0, "unreadable": 2}
        assert {r["owner"]: r["link"] for r in projection["unresolved"]} == {"Marek": "locked", "Priya": "locked"}
        assert all(r["candidates"] == [] for r in projection["unresolved"])
        assert "ania-dev" not in json.dumps(projection)

    def test_unconfigured_ledger_is_named(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = self._project_with_owner(db)
        store = EncryptedPeopleStore(tmp_path / "never-set-up" / "people.v1.sqlite3", MemoryKeyStore())
        people = PeopleService(store)  # never initialized

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert projection["state"] == "unconfigured"
        assert projection["expected"] == 2 and projection["resolved"] == 0
        assert projection["gaps"]["unreadable"] == 2
        # Counsel P2-ii: the row carries the ledger's OWN state, never LOCKED
        # under a head that says NOT SET UP.
        assert {r["link"] for r in projection["unresolved"]} == {"unconfigured"}

    def test_missing_ledger_entry_is_a_not_linked_gap_not_a_silence(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        pid = self._project_with_owner(db)
        people = _people(tmp_path)
        _relationship(people, "Priya Sharma", aliases=("Priya",))

        projection = room_people_preparation(projects, people, pid, OWNER)

        assert projection["state"] == "ready"
        assert projection["expected"] == 2 and projection["resolved"] == 1
        gap = _by_owner(projection, "Marek")
        assert gap["link"] == "not_linked" and gap["candidates"] == []
        assert [c["text"] for c in gap["commitments"]] == ["Own the migration"]
        assert projection["gaps"] == {"ambiguous": 0, "not_linked": 1, "unreadable": 0}

    def test_no_people_service_is_unavailable_never_empty(self, db: Database, projects: ProjectService) -> None:
        pid = self._project_with_owner(db)

        projection = room_people_preparation(projects, None, pid, OWNER)

        assert projection["state"] == "unavailable"
        assert projection["expected"] == 2 and projection["gaps"]["unreadable"] == 2
        assert {r["link"] for r in projection["unresolved"]} == {"unavailable"}

    def test_a_project_that_names_nobody_is_an_honest_absence(self, tmp_path: Path, db: Database, projects: ProjectService) -> None:
        """No owner, no identity, no link: nothing is named, so the face may
        withhold the section (A.8) -- but ONLY when expected is 0."""
        pid = _seed_project(db)
        store = EncryptedPeopleStore(tmp_path / "never-set-up" / "people.v1.sqlite3", MemoryKeyStore())

        projection = room_people_preparation(projects, PeopleService(store), pid, OWNER)

        assert projection["expected"] == 0 and projection["unresolved"] == [] and projection["people"] == []

    def test_vocabularies_are_closed(self) -> None:
        assert LEDGER_STATES == ("ready", "locked", "unconfigured", "unavailable")
        assert LINK_STATES == ("linked", "ambiguous", "not_linked", "locked", "unconfigured", "unavailable")
