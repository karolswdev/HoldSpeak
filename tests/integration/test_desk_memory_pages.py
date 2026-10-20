"""Memory where he looks, hub half (Betterment Q11, docs/internal/betterment/asking/RECIPE.md).

* Pages run on the Background work engine, else Everything else, with no
  separate assignment: a non-local Background default HoldSpeak made is
  skipped (owner ruling 2026-10-05) and the search goes on to the owner's
  Everything-else engine. It stopped there before and kept every page dark.
* Pages have their own calls each pass: an extraction backlog spent the one
  shared budget, so no page was written in the walk.
* The desk has the person pages' source: "What do others owe me?" beside
  "What do I owe?". A person's window draws the sentences of both that name
  her (web/src/desk/standingPages.tsx ``personPages``); no People id is ever
  written beside a page.

The face half is web/src/pages/cores/__tests__/personPages.app.test.tsx; it
replays the desk pages this file records (web/src/test/wire/memory.desk-pages.wire.json;
HOLDSPEAK_WIRE_WRITE=1 rewrites it). The page engine is slice 5's
deterministic rule engine reading the real prompt; the code under test is
never doubled.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.memory.engine import MemoryEngineUnassigned, _assignment_head, assigned_revision
from holdspeak.memory.pages import (
    PAGE_CAPABILITY,
    PAGE_SET,
    build_payload,
    read,
    resolve_page_writer,
    spec_for,
    write_pending,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.memory_service import MemoryService

from tests.unit.test_batteries_default import mark_made_by_holdspeak
from tests.unit.test_memory_slice4_observations import _desk, _filed_note, _meeting
from tests.unit.test_memory_slice5_pages import Pages
from tests.unit.test_memory_slice3_facts import F, Scripted
from tests.unit.test_memory_slice4_observations import Rules
from holdspeak.memory.extract import extract_pending
from holdspeak.memory.consolidate import consolidate_pending
from holdspeak.memory.retain import sweep
from tests.unit.test_phase143_inference_assignments import OWNER, _profile

WIRE = Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire"


def desk_question_writer() -> Pages:
    """Deterministic replies at the model seam, honoring each real question.

    The general slice-5 writer echoes every input. Here the two directions
    must be distinct so recorded faces cannot hide an I-owe/they-owe mix-up.
    """
    writer = Pages()

    def answer(payload: dict[str, Any]) -> dict[str, Any]:
        question = next(line for line in payload["user_prompt"].splitlines() if line.startswith("Question:"))
        selected = []
        for label, text in Pages.lines(payload).items():
            if not label.startswith("o"):
                continue
            if "What do I owe?" in question and "you owe" not in text.lower():
                continue
            if "What do others owe me?" in question and "owes you" not in text.lower():
                continue
            selected.append({"text": text, "refs": [label]})
        return {"sentences": selected}

    writer.answer = answer
    return writer


def build_desk_answers(db: Database) -> dict[str, Any]:
    """Real memory pipeline, with deterministic models at its three seams."""
    sentences = [
        "You owe Mira feedback on the cutover design document, due Friday.",
        "Mira owes you the rollback runbook, due Thursday.",
        "You owe Theo the on-call handbook, due Friday.",
    ]
    sweep(db)
    extraction = extract_pending(db, Scripted([(text, [F(text, text)]) for text in sentences]))
    assert extraction["facts"] == len(sentences), extraction
    rules = Rules()
    rules.echo = True
    consolidate_pending(db, rules)
    return write_pending(db, desk_question_writer())


def _set(db: Database, command: str, scope: dict[str, Any], profile: str) -> dict[str, Any]:
    return InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": command, "expected_revision": 0, "scope": scope,
        "entries": [{"profile_id": profile, "profile_revision": 1}],
    })


def test_pages_run_on_everything_else_past_a_background_default_holdspeak_made(tmp_path: Path) -> None:
    db = Database(tmp_path / "heads.db")
    _profile(db, "made-lan", boundary="private_network")
    _profile(db, "his-lan", boundary="private_network")
    background = _set(db, "bg", {"kind": "group", "group_id": "background"}, "made-lan")
    mark_made_by_holdspeak(db, background)
    everything = _set(db, "global", {"kind": "global"}, "his-lan")
    with db._connection() as conn:
        assert _assignment_head(conn, PAGE_CAPABILITY) == f"{everything['id']}@1"
    # The ruling stands: a network default HoldSpeak made is never used.
    lonely = Database(tmp_path / "lonely.db")
    _profile(lonely, "made-lan", boundary="private_network")
    mark_made_by_holdspeak(lonely, _set(lonely, "bg", {"kind": "group", "group_id": "background"}, "made-lan"))
    with lonely._connection() as conn:
        assert _assignment_head(conn, PAGE_CAPABILITY) is None


@pytest.mark.parametrize("background_boundary", ("private_network", "cloud"))
def test_page_writer_calls_the_selected_everything_else_revision(
    tmp_path: Path, background_boundary: str,
) -> None:
    """The physical writer must follow the head selected by memory policy.

    The generic planner prefers the Background assignment, while memory's
    policy skips a non-local default HoldSpeak made and selects the owner's
    global head.  This test crosses the real resolver, writer and runner; only
    the model leaf is replaced, and its revision argument proves the physical
    route.
    """
    from tests.unit.test_memory_slice5_pages import _PageEngine

    db = Database(tmp_path / "physical-route.db")
    _profile(db, "background-lan", model="background-model", boundary=background_boundary)
    _profile(db, "owner-global", model="owner-model", boundary="private_network")
    background = _set(
        db,
        "background",
        {"kind": "group", "group_id": "background"},
        "background-lan",
    )
    mark_made_by_holdspeak(db, background)
    global_assignment = _set(db, "global", {"kind": "global"}, "owner-global")
    broker = _configure(db)
    leaf = _PageEngine()
    seen_revisions: list[str] = []

    def factory(revision, **_kwargs):
        seen_revisions.append(str(revision.id))
        return leaf

    broker.inference_runner._engine_factory = factory
    with db._connection() as conn:
        selected_head = _assignment_head(conn, PAGE_CAPABILITY)
        owner_revision = conn.execute(
            "SELECT id FROM deployment_revisions WHERE model=?",
            ("owner-model",),
        ).fetchone()[0]
    selected = assigned_revision(broker, PAGE_CAPABILITY)
    writer = resolve_page_writer(broker, memory_conductor._principal())
    assert selected_head == f"{global_assignment['id']}@1"
    assert selected is not None
    assert writer is not None
    for capability in ("memory.extract", "memory.consolidate"):
        sibling = assigned_revision(broker, capability)
        assert sibling is not None
        assert sibling["assignment_id"] == global_assignment["id"]
        assert sibling["revision_id"] == owner_revision

    writer.write(build_payload(spec_for("desk", "what-i-owe"), [], []))

    assert selected["assignment_id"] == global_assignment["id"]
    assert selected["revision_id"] == owner_revision
    assert seen_revisions == [owner_revision]
    assert seen_revisions == [writer.revision_id]
    receipt = broker.store.receipt(writer.last_operation_id)
    assert receipt["outcome"] == "succeeded"
    operation = broker.store.operation(writer.last_operation_id)
    assert operation["target_ref"] == f"deployment-revision:{owner_revision}"
    assert receipt["operation_id"] == writer.last_operation_id
    assert receipt["result_ref"] == f"memory-page:{global_assignment['id']}"

    InferenceAssignmentService(db).clear_assignment(OWNER, {
        "command_id": "clear-global-page-route",
        "expected_revision": 1,
        "scope": {"kind": "global"},
        "capability_id": PAGE_CAPABILITY,
    })
    assert not writer.live()
    with pytest.raises(MemoryEngineUnassigned):
        writer.write(build_payload(spec_for("desk", "what-i-owe"), [], []))
    assert seen_revisions == [owner_revision]


def test_pages_have_their_own_calls_after_extraction_spends_the_shared_budget(monkeypatch) -> None:
    seen: list[Any] = []

    def spend(db: Any, broker: Any, should_stop: Any, budget: Any) -> dict[str, Any]:
        budget.calls = memory_conductor.EXTRACT_CALLS_PER_PASS  # the backlog spent it
        return {"engine": "x", "calls": budget.calls, "more": 1, "yielded": "", "error": ""}

    monkeypatch.setattr(memory_conductor, "_extract_step", spend)
    monkeypatch.setattr(memory_conductor, "_consolidate_step",
                        lambda db, broker, should_stop, budget: {"engine": "x", "calls": 0, "more": 1, "yielded": "", "error": ""})

    def pages(db: Any, broker: Any, should_stop: Any, budget: Any) -> dict[str, Any]:
        seen.append(budget)
        return {"engine": "x", "pages": 0, "calls": 0, "more": 0, "yielded": "", "error": ""}

    monkeypatch.setattr(memory_conductor, "_page_step", pages)
    memory_conductor._model_steps(None, None, None)
    assert len(seen) == 1
    assert not seen[0].spent(), "the page step got a budget extraction had spent"
    assert seen[0].max_calls == memory_conductor.PAGE_CALLS_PER_PASS


def test_the_desk_says_what_others_owe_him_and_the_read_serves_it(tmp_path: Path) -> None:
    from tests.unit.test_desk_speak import _record

    assert [s.slug for s in PAGE_SET["desk"]] == ["what-i-owe", "what-they-owe-me", "what-changed-this-week"]
    db = _desk(tmp_path)
    # The 1:1 is a real meeting producer.  Its source ref must survive the
    # page write so the person window can open the evidence in one press.
    meeting_ref = _meeting(
        db, "m-mira-1on1",
        "You owe Mira feedback on the cutover design document, due Friday.",
        day=19, project=None,
    )
    db.meetings.update_meeting_metadata("m-mira-1on1", "1:1 with Mira", [])
    _filed_note(db, "n-owed", "Mira owes you the rollback runbook, due Thursday.", None)
    _filed_note(db, "n-theo", "You owe Theo the on-call handbook, due Friday.", None)
    build_report = build_desk_answers(db)
    assert build_report["calls"] == len(PAGE_SET["desk"]) and build_report["more"] == 0
    owe = read(db, "desk", "", "what-i-owe")
    owed = read(db, "desk", "", "what-they-owe-me")
    assert owe is not None and owed is not None
    assert any("Mira owes you the rollback runbook" in sentence["text"] for sentence in owed["sentences"])
    assert all("You owe Mira" not in sentence["text"] for sentence in owed["sentences"])
    pages = MemoryService(db).standing_pages(Principal(PrincipalKind.OWNER, "pages-owner"), scope="desk")
    slugs = [page["slug"] for page in pages["pages"]]
    assert "what-i-owe" in slugs and "what-they-owe-me" in slugs
    owe_page = next(page for page in pages["pages"] if page["slug"] == "what-i-owe")
    assert any(
        "You owe Mira feedback on the cutover design document, due Friday" in sentence["text"]
        and any(ref["ref"] == meeting_ref and ref["opens"] for ref in sentence["refs"])
        for sentence in owe_page["sentences"]
    )
    # No People id is written beside a page: the scope is the desk.
    with db._connection() as conn:
        scopes = {(row[0], row[1]) for row in conn.execute("SELECT scope_kind, scope_id FROM memory_pages")}
    assert ("desk", "") in scopes and not any(kind == "person" for kind, _ in scopes)
    _record("memory.desk-pages.wire", {"pages": pages}, tmp_path,
            "tests/integration/test_desk_memory_pages.py::test_the_desk_says_what_others_owe_him_and_the_read_serves_it",
            folder=WIRE)
