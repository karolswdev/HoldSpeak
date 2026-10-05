"""Memory on the Desk (canvas section 2, option B): the read routes the three
faces draw from.

* ``GET /api/memory/recall`` carries ``beliefs`` (one more kind of recall
  card): current / disputed / superseded, evidence tokens, ``against`` on a
  contradicting ref, the superseded text in the current belief's history.
* ``GET /api/memory/pages`` serves one scope's standing pages: no model
  call, no withheld count, project A never shows project B, redacted text,
  ``new_sources`` counted in scope only, the owner's READ right.

Sources are written by their real producers; facts, observations and pages
come through the real extract, consolidate and page paths with the slice 4
and slice 5 fixture engines (the code under test is never doubled).
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.memory.defense import REDACTED
from holdspeak.memory.pages import write_pending
from holdspeak.memory.retain import sweep
from holdspeak.principals import Principal, PrincipalKind

from tests.unit.test_memory_slice4_observations import Rules, _desk, _filed_note, _learn, _meeting
from tests.unit.test_memory_slice5_pages import Pages

OWNER = Principal(PrincipalKind.OWNER, "memory-faces-owner")
SECRET = "ghp_" + "Z9y8X7w6V5u4T3s2R1q0P9o8"


def _seed(db: Database) -> None:
    """Atlas: a superseded cutover, a disputed rollback owner, a secret.
    Harbor: one belief of its own.  The desk: one note in no project."""
    _meeting(db, "m1", "Atlas cutover is 10-10. Rollback owner is Marek.", day=24)
    _learn(db)
    _filed_note(db, "n2", "Atlas cutover is 10-17.", "atlas")
    _learn(db)
    _meeting(db, "m3", "Rollback owner is Priya.", day=29)
    _learn(db, Rules("contradicts"))
    _filed_note(db, "n-key", f"Deploy token is rotated. The new one is token={SECRET} now.", "atlas")
    _filed_note(db, "nh", "Harbor budget is 40k.", "harbor")
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    _learn(db)
    write_pending(db, Pages())


def _app(db: Database, principal: Principal) -> TestClient:
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.memory import build_memory_router

    app = FastAPI()

    @app.middleware("http")
    async def _principal(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_memory_router(WebContext(get_state=lambda: {}, memory_service=MemoryService(db))))
    return TestClient(app)


@pytest.fixture
def seeded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    reset_database()
    db = _desk(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _seed(db)
    yield db, _app(db, OWNER)
    reset_database()


# ── beliefs in Desk memory ──────────────────────────────────────────────


def test_recall_draws_beliefs_current_and_superseded_with_history(seeded) -> None:
    _db, client = seeded
    body = client.get("/api/memory/recall", params={"query": "cutover"}).json()
    beliefs = {b["text"]: b for b in body["beliefs"]}
    current, old = beliefs["Atlas cutover is 10-17."], beliefs["Atlas cutover is 10-10."]
    assert current["state"] == "current" and current["kind"] == "belief"
    assert current["project"] == {"id": "atlas", "name": "Atlas"}
    assert [e["ref"] for e in current["evidence"]] == ["note:n2"]
    assert current["evidence"][0]["token"].startswith("NOTE ") and current["evidence"][0]["opens"] is True
    # The old text unfolds under the current belief, marked SUPERSEDED.
    assert [(h["text"], h["word"]) for h in current["history"]] == [("Atlas cutover is 10-10.", "SUPERSEDED")]
    assert old["state"] == "superseded" and old["since"] and old["history"] == []
    assert old["evidence"][0]["token"] == "MTG 09-24 · 10:00"
    # Counted in the head's one count; current comes first.
    assert body["remembered"] >= 2 and body["beliefs"][0]["state"] == "current"


def test_recall_draws_a_disputed_pair_with_the_contradicting_ref_marked_against(seeded) -> None:
    _db, client = seeded
    beliefs = client.get("/api/memory/recall", params={"query": "rollback"}).json()["beliefs"]
    assert {b["state"] for b in beliefs} == {"disputed"} and len(beliefs) == 2
    marek = next(b for b in beliefs if "Marek" in b["text"])
    assert [(e["token"], e["against"]) for e in marek["evidence"]] == [
        ("MTG 09-24 · 10:00", False), ("MTG 09-29 · 10:00", True),
    ]


def test_beliefs_ride_the_all_filter_only(seeded) -> None:
    _db, client = seeded
    for chosen in ("decisions", "commitments", "briefs", "meetings"):
        body = client.get("/api/memory/recall", params={"query": "cutover", "filter": chosen}).json()
        assert body["beliefs"] == [], chosen


def test_the_wordless_recall_reads_the_newest_current_and_disputed_beliefs(seeded) -> None:
    _db, client = seeded
    beliefs = client.get("/api/memory/recall", params={"recent": "1"}).json()["beliefs"]
    assert beliefs and {b["state"] for b in beliefs} <= {"current", "disputed"}


def test_no_consolidation_means_no_beliefs_and_no_pages(tmp_path: Path, monkeypatch) -> None:
    reset_database()
    db = _desk(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _filed_note(db, "n1", "Atlas cutover is 10-17.", "atlas")
    sweep(db)  # memory holds the note; no engine made a belief or a page
    client = _app(db, OWNER)
    assert client.get("/api/memory/recall", params={"query": "cutover"}).json()["beliefs"] == []
    assert client.get("/api/memory/pages", params={"project_id": "atlas"}).json() == {"pages": []}
    assert client.get("/api/memory/pages", params={"scope": "desk"}).json() == {"pages": []}
    reset_database()


# ── standing pages ──────────────────────────────────────────────────────


def test_the_project_pages_come_in_the_fixed_order_with_tokens_and_no_withheld_count(seeded) -> None:
    _db, client = seeded
    pages = client.get("/api/memory/pages", params={"project_id": "atlas"}).json()["pages"]
    assert [p["slug"] for p in pages] == ["what-we-decided", "what-is-open", "risks-and-disputes",
                                          "what-changed-this-week"]
    for page in pages:
        assert "withheld" not in page and page["model"] == "pages" and page["built_at"]
        assert page["stale"] is False and page["new_sources"] == 0
        for sentence in page["sentences"]:
            assert sentence["refs"] and all(r["token"] for r in sentence["refs"])


def test_project_a_never_shows_project_b_or_the_desk(seeded) -> None:
    _db, client = seeded
    atlas = json.dumps(client.get("/api/memory/pages", params={"project_id": "atlas"}).json())
    harbor = json.dumps(client.get("/api/memory/pages", params={"project_id": "harbor"}).json())
    desk = json.dumps(client.get("/api/memory/pages", params={"scope": "desk"}).json())
    assert "Atlas cutover" in atlas and "Harbor" not in atlas and "lunch" not in atlas
    assert "Harbor budget" in harbor and "Atlas" not in harbor and "lunch" not in harbor
    assert "Desk lunch" in desk and "Atlas" not in desk and "Harbor" not in desk


def test_a_secret_is_redacted_on_the_way_out(seeded) -> None:
    _db, client = seeded
    text = json.dumps(client.get("/api/memory/pages", params={"project_id": "atlas"}).json())
    text += json.dumps(client.get("/api/memory/recall", params={"query": "token"}).json())
    assert SECRET not in text and REDACTED in text


def test_a_new_source_in_scope_makes_the_page_stale_and_counts_it(seeded) -> None:
    db, client = seeded
    _filed_note(db, "n-new", "Atlas freeze is 10-12.", "atlas")
    _filed_note(db, "n-harbor", "Harbor freeze is 11-01.", "harbor")
    sweep(db)
    pages = client.get("/api/memory/pages", params={"project_id": "atlas"}).json()["pages"]
    changed = next(p for p in pages if p["slug"] == "what-changed-this-week")
    # The Harbor note is not Atlas's: one new source, not two.
    assert changed["stale"] is True and changed["new_sources"] == 1


@pytest.mark.parametrize("params", [{"scope": "project"}, {"scope": "desk", "project_id": "atlas"},
                                    {"scope": "person"}, {}])
def test_a_bad_scope_is_refused(seeded, params) -> None:
    _db, client = seeded
    assert client.get("/api/memory/pages", params=params).status_code == 400


def test_the_pages_route_needs_the_read_right(seeded) -> None:
    db, _client = seeded
    nobody = _app(db, Principal(PrincipalKind.NONE, ""))
    response = nobody.get("/api/memory/pages", params={"project_id": "atlas"})
    assert response.status_code == 401 and "Atlas" not in response.text


def test_the_pages_route_is_the_owners_by_the_edge_map() -> None:
    from holdspeak.principals import PrincipalRight, required_right

    assert required_right("GET", "/api/memory/pages") is PrincipalRight.OWNER


# ── People custody ──────────────────────────────────────────────────────


def test_people_store_content_never_reaches_a_belief_or_a_page(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.services.people_service import PeopleService

    reset_database()
    db = _desk(tmp_path, "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    store = EncryptedPeopleStore(tmp_path / "people-private" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    relationship = people.create_relationship(OWNER, {"display_name": "Zorvane Quillfeather"})
    note = people.create_note(OWNER, relationship["id"], {"topic": "Growth", "body": "PEOPLESENTINEL is promoted."})
    _seed(db)
    client = _app(db, OWNER)
    held = "".join(
        client.get(url, params=params).text for url, params in (
            ("/api/memory/pages", {"project_id": "atlas"}), ("/api/memory/pages", {"scope": "desk"}),
            ("/api/memory/recall", {"query": "is"}), ("/api/memory/recall", {"recent": "1"}),
        )
    )
    for word in ("PEOPLESENTINEL", "Quillfeather", note["id"], relationship["id"]):
        assert word not in held
    reset_database()


def test_the_memory_faces_module_reads_nothing_from_the_people_store() -> None:
    """The fence: the module that shapes beliefs and pages imports no People
    module, so no People field, alias or id can steer what it reads."""
    import holdspeak.services.memory_faces as module

    tree = ast.parse(Path(module.__file__).read_text())
    imported = [
        f"{node.module or ''}.{alias.name}" if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    ]
    assert not [name for name in imported if "people" in name.lower()], imported
    assert "relationship" not in Path(module.__file__).read_text().lower()


def test_sources_counts_distinct_sources_not_facts(tmp_path: Path, monkeypatch) -> None:
    """Astra's repro (PR #877 P2): one note with two supporting facts is ONE
    source.  ``proof_count`` stays the fact count; the card reads
    ``source_count``."""
    reset_database()
    db = _desk(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _filed_note(db, "n1", "Atlas freeze is 10-12. Atlas freeze is 10-12.", "atlas")
    _learn(db)
    belief = _app(db, OWNER).get("/api/memory/recall", params={"query": "freeze"}).json()["beliefs"][0]
    assert belief["proof_count"] == 2
    assert belief["source_count"] == 1
    reset_database()
