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

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.memory.engine import _assignment_head
from holdspeak.memory.pages import PAGE_CAPABILITY, PAGE_SET, read
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.memory_service import MemoryService

from tests.unit.test_batteries_default import mark_made_by_holdspeak
from tests.unit.test_memory_slice4_observations import _desk, _filed_note
from tests.unit.test_memory_slice5_pages import Pages, _built
from tests.unit.test_phase143_inference_assignments import OWNER, _profile

WIRE = Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire"


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
    # (The scripted extractor learns "X is Y." facts; the second sentence of
    # each note rides in its recall chunk, as slice 5's own desk pages do.)
    _filed_note(db, "n-owe", "Feedback for Mira is due. You owe Mira feedback on her cutover design doc by Friday.", None)
    _filed_note(db, "n-owed", "Runbook from Mira is due. Mira owes you the rollback runbook by Thursday.", None)
    _filed_note(db, "n-theo", "Handbook for Theo is due. Theo owns the on-call handbook.", None)
    _built(db, Pages())
    owe = read(db, "desk", "", "what-i-owe")
    owed = read(db, "desk", "", "what-they-owe-me")
    assert owe is not None and owed is not None
    pages = MemoryService(db).standing_pages(Principal(PrincipalKind.OWNER, "pages-owner"), scope="desk")
    slugs = [page["slug"] for page in pages["pages"]]
    assert "what-i-owe" in slugs and "what-they-owe-me" in slugs
    # No People id is written beside a page: the scope is the desk.
    with db._connection() as conn:
        scopes = {(row[0], row[1]) for row in conn.execute("SELECT scope_kind, scope_id FROM memory_pages")}
    assert ("desk", "") in scopes and not any(kind == "person" for kind, _ in scopes)
    _record("memory.desk-pages.wire", {"pages": pages}, tmp_path,
            "tests/integration/test_desk_memory_pages.py::test_the_desk_says_what_others_owe_him_and_the_read_serves_it",
            folder=WIRE)
