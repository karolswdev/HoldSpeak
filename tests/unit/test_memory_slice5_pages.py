"""Memory slice 5, backend: pages, standing answers read with no model call
(docs/internal/MEMORY-DESIGN.md §1, §2, §3.4, §5, §6, §8 row 5).

Every source is written by its real producer (the meeting, note, thread and
project repositories, the People service).  Facts and observations come
through the real extract and consolidate paths with the slice 4 scripted
engines.  The page engine is a deterministic rule engine that reads the
real prompt: one sentence per input line, citing that line's label.  The
code under test is never doubled.  The router tests use the real router,
assignment service and runner; only the physical model leaf is replaced.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

import pytest

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.inference_capabilities import builtin_capability_definitions
from holdspeak.inference_memory_policy import memory_policy
from holdspeak.kernel.runtime import _configure
from holdspeak.memory import pages as pages_module
from holdspeak.memory.consolidate import CONSOLIDATE_CAPABILITY
from holdspeak.memory.defense import REDACTED
from holdspeak.memory.extract import EXTRACT_CAPABILITY, CallBudget, extract_pending
from holdspeak.memory.pages import (
    PAGE_CAPABILITY, PAGE_SET, PageOutputError, pending_pages, read, resolve_page_writer, spec_for,
    write_page, write_pending,
)
from holdspeak.memory.retain import sweep
from holdspeak.services.memory_grounding import memory_context, memory_for, project_pages

from tests.memory_bench import bench
from tests.memory_bench.corpus import build_corpus
from tests.unit.test_memory_slice3_facts import _memory_text
from tests.unit.test_memory_slice4_observations import (
    Facts, Rules, _desk, _filed_note, _learn, _meeting,
)
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign

PAGE_TABLES = ("memory_pages", "memory_page_history", "memory_jobs")


# ── the deterministic page engine ───────────────────────────────────────

_INPUT_LINE = re.compile(r"^([or]\d+) (?:\[\w+\] \(proof \d+\)|\([^)]*\)): (.*)$")


class Pages:
    """Reads the real prompt: one sentence per input line, the line's text,
    citing the line's label.  ``answer`` overrides; ``during`` runs while
    the engine "reads"."""

    boundary = "local"
    model_id = "pages"

    def __init__(self, *, recall: bool = True) -> None:
        self.recall = recall
        self.payloads: list[dict] = []
        self.calls = 0
        self.answer: Any = None
        self.during: Optional[Callable[[dict], None]] = None

    @staticmethod
    def lines(payload: dict) -> dict[str, str]:
        found = {}
        for line in payload["user_prompt"].splitlines():
            if (m := _INPUT_LINE.match(line)):
                found[m.group(1)] = m.group(2)
        return found

    def write(self, payload: dict) -> Any:
        self.calls += 1
        self.payloads.append(payload)
        if self.during is not None:
            self.during(payload)
        if self.answer is not None:
            return self.answer(payload) if callable(self.answer) else self.answer
        sentences = []
        for label, text in self.lines(payload).items():
            if label.startswith("r") and not self.recall:
                continue
            sentences.append({"text": text[:300], "refs": [label]})
        return {"sentences": sentences}

    def received(self) -> str:
        return "\n".join(p["user_prompt"] for p in self.payloads)


def _aged(db: Database, hours: float = 2) -> Database:
    """Every page built ``hours`` ago (past the once-an-hour gate)."""
    stamp = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    with db._connection() as conn:
        conn.execute("UPDATE memory_pages SET built_at=?", (stamp,))
    return db


def _built(db: Database, writer: Optional[Pages] = None, **kwargs: Any) -> dict:
    """Sweep, extract, consolidate, then write the pages that are due."""
    _learn(db)
    return write_pending(db, writer or Pages(), **kwargs)


def _page(db: Database, scope: tuple[str, str], slug: str, **kwargs: Any) -> Optional[dict]:
    return read(db, scope[0], scope[1], slug, **kwargs)


def _rows(db: Database, *tables: str) -> dict[str, list[tuple]]:
    out: dict[str, list[tuple]] = {}
    with db._connection() as conn:
        for table in tables:
            out[table] = sorted(tuple(str(v) for v in row) for row in conn.execute(f"SELECT * FROM {table}"))
    return out


ATLAS = ("project", "atlas")
HARBOR = ("project", "harbor")
DESK = ("desk", "")
CHANGED = "what-changed-this-week"


# ── the capability ──────────────────────────────────────────────────────


def test_memory_page_is_a_dark_background_capability_with_memory_off() -> None:
    capability = next(c for c in builtin_capability_definitions() if c.id == PAGE_CAPABILITY)
    assert (capability.group_id, capability.group_label) == ("background", "Background")
    assert set(capability.allowed_boundaries) == {"local", "private_network", "mesh", "cloud"}
    assert capability.requires.structured_output is False
    assert capability.output_kind == "memory_page"
    assert memory_policy(PAGE_CAPABILITY).enabled is False


def test_the_fixed_page_set() -> None:
    assert [s.slug for s in PAGE_SET["project"]] == [
        "what-we-decided", "what-is-open", "risks-and-disputes", CHANGED,
    ]
    assert [s.slug for s in PAGE_SET["desk"]] == ["what-i-owe", CHANGED]
    assert set(PAGE_SET) == {"project", "desk"}  # no person pages (see MEMORY-DESIGN.md)
    with pytest.raises(ValueError):
        spec_for("person", "what-i-owe-them")


# ── a page: built, read, stale ──────────────────────────────────────────


def test_a_page_is_built_from_observations_and_recall_and_every_sentence_has_a_ref_that_opens(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Atlas budget is 40k.", "atlas")
    writer = Pages()
    stats = _built(db, writer)
    assert stats["pages"] >= 1 and stats["calls"] == writer.calls
    page = _page(db, ATLAS, CHANGED)
    assert page is not None and page["withheld"] == 0 and page["stale"] is False
    texts = [s["text"] for s in page["sentences"]]
    assert "Atlas launch is 2026-10-01." in texts and "Atlas budget is 40k." in texts
    for sentence in page["sentences"]:
        assert sentence["refs"] and any(ref["opens"] for ref in sentence["refs"]), sentence
    assert {r["ref"] for r in page["sources"]} == {"note:n1", "note:n2"}
    assert page["boundary"] == "local" and page["model"] == "pages" and page["built_at"]
    # No page for a scope memory holds nothing about.
    assert _page(db, HARBOR, CHANGED) is None and _page(db, DESK, "what-i-owe") is None


def test_a_page_read_makes_zero_model_calls(tmp_path: Path, monkeypatch) -> None:
    """The census: a page read (the API, the service, the MCP tool, a
    drafter's memory) admits no model call and runs no engine."""
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.mcp.families import memory as family
    from holdspeak.services.memory_service import MemoryService

    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    calls: list[str] = []

    def no_call(*_a, **_k):
        calls.append("invoke")
        raise AssertionError("a page read made a model call")

    monkeypatch.setattr(InferenceRunner, "invoke", no_call)
    for name in ("resolve_page_writer", "write_page", "write_pending"):
        monkeypatch.setattr(pages_module, name, lambda *_a, _n=name, **_k: calls.append(_n))
    db.memory.set_embedder(None)
    with db._connection() as conn:
        ops_before = conn.execute("SELECT count(*) FROM kernel_operations").fetchone()[0]
    monkeypatch.setattr(family, "db_or", lambda _default: db)
    assert _page(db, ATLAS, CHANGED) is not None
    assert MemoryService(db).page(OWNER, scope="project", project_id="atlas", slug=CHANGED)["page"]
    assert family.dispatch("memory.page", {"project_id": "atlas", "slug": CHANGED}, OWNER)["page"]
    assert memory_for("project.update_draft", db, project_id="atlas", query="Atlas",
                      pages=project_pages("atlas", CHANGED))
    with db._connection() as conn:
        ops_after = conn.execute("SELECT count(*) FROM kernel_operations").fetchone()[0]
    assert calls == [] and ops_after == ops_before


def test_a_new_decision_makes_the_page_stale_then_fresh_after_the_job(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    assert _page(db, ATLAS, CHANGED)["stale"] is False
    # A new decision, by its real producer, filed to Atlas.
    db.desk_decisions.upsert(
        decision_id="d-vendor", title="Vendor", status="accepted", decided_at="2026-10-02",
        context_markdown="", decision_markdown="Atlas vendor is Kestrel.", consequences_markdown="",
    )
    db.project_relationships.upsert(project_id="atlas", resource_ref="desk_decision:d-vendor")
    page = _page(db, ATLAS, CHANGED)
    assert page["stale"] is False  # the sweep has not seen it yet
    sweep(db)
    page = _page(db, ATLAS, CHANGED)
    assert page["stale"] is True and "Kestrel" not in json.dumps(page)
    _learn(db)
    # Inside the hour the page is not written again.
    assert all(d["spec"].slug != CHANGED or d["scope"] != ATLAS for d in pending_pages(db))
    writer = Pages()
    write_pending(_aged(db), writer)
    page = _page(db, ATLAS, CHANGED)
    assert page["stale"] is False and "Kestrel" in json.dumps(page)
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_page_history").fetchone()[0] >= 1


def test_a_fresh_page_is_not_written_again_and_a_second_pass_makes_no_call(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    _aged(db)
    before = _rows(db, *PAGE_TABLES)
    writer = Pages()
    assert write_pending(db, writer)["calls"] == 0  # past the hour but not stale: nothing due
    assert writer.calls == 0 and _rows(db, *PAGE_TABLES) == before


def test_with_no_engine_the_last_page_is_served_with_its_age(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    with db._connection() as conn:
        conn.execute("UPDATE memory_pages SET built_at='2026-01-01T00:00:00+00:00'")
    page = _page(db, ATLAS, CHANGED)
    assert page is not None and page["built_at"].startswith("2026-01-01") and page["age_seconds"] > 86400


# ── read time: a withdrawn source never survives in a sentence ──────────


def _two_notes(db: Database) -> None:
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Atlas budget is 40k.", "atlas")
    _built(db)
    page = _page(db, ATLAS, CHANGED)
    cited = json.dumps(page)
    assert "2026-10-01" in cited and "40k" in cited
    # Both cite kinds carry the withdrawn text: an observation and a chunk.
    with db._connection() as conn:
        stored = json.loads(conn.execute("SELECT sentences_json FROM memory_pages WHERE slug=?", (CHANGED,)).fetchone()[0])
    kinds = {c["kind"] for s in stored if "2026-10-01" in s["text"] for c in s["cites"]}
    assert kinds == {"observation", "chunk"}


@pytest.mark.parametrize("mode", ["edit", "delete", "refile", "exclude"])
def test_a_page_built_before_a_withdrawal_never_serves_the_withdrawn_sentence(tmp_path: Path, mode: str) -> None:
    db = _desk(tmp_path)
    _two_notes(db)
    read_kwargs: dict = {}
    if mode == "edit":
        _filed_note(db, "n1", "Lunch is at noon.", "atlas")
    elif mode == "delete":
        db.notes.delete("n1")
    elif mode == "refile":
        db.project_relationships.upsert(project_id="atlas", resource_ref="note:n1", deleted=True)
        db.project_relationships.upsert(project_id="harbor", resource_ref="note:n1")
    else:
        read_kwargs = {"exclude_refs": ["note:n1"]}

    def check() -> None:
        page = _page(db, ATLAS, CHANGED, **read_kwargs)
        assert page is not None and "2026-10-01" not in json.dumps(page)  # withdrawn
        assert "40k" in json.dumps(page) and page["withheld"] == 2      # the rest stays
        assert all(ref["ref"] != "note:n1" for ref in page["sources"])

    check()                     # before the sweep: read time, not rewrite time
    sweep(db)
    check()                     # after it
    _learn(db)
    check()                     # after extraction and consolidation
    if mode == "refile":
        # Refiling counts at once: Harbor's page never cites Atlas, and
        # Atlas's never cites Harbor.
        write_pending(_aged(db), Pages())
        harbor = _page(db, HARBOR, CHANGED)
        assert harbor is None or "40k" not in json.dumps(harbor)
        assert "2026-10-01" not in json.dumps(_page(db, ATLAS, CHANGED))


@pytest.mark.parametrize("change", ["delete_part", "made_sensitive"])
def test_a_withdrawn_thread_message_never_survives_in_a_desk_page(tmp_path: Path, change: str) -> None:
    db = _desk(tmp_path)
    thread = db.threads.create_thread(title="Planning")
    lunch = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(lunch.id, kind="text", text="Lunch is noon.")
    secret = db.threads.append_message(thread.id, role="user")
    part = db.threads.append_part(secret.id, kind="text", text="Atlas launch is 2026-10-01.")
    _built(db)
    page = _page(db, DESK, CHANGED)
    assert page is not None and "2026-10-01" in json.dumps(page)
    assert any(r["ref"] == f"thread:{thread.id}#{secret.id}" for r in page["sources"])
    if change == "made_sensitive":
        db.threads.append_part(secret.id, kind="text", text=part.text, sensitive=True)
    db.threads.delete_part(part.id)
    for step in (lambda: None, lambda: sweep(db), lambda: _learn(db)):
        step()
        page = _page(db, DESK, CHANGED)
        assert page is not None and "Lunch is noon." in json.dumps(page)  # the rest stays
        assert "2026-10-01" not in json.dumps(page) and page["withheld"] == 2


def test_a_page_built_on_a_refinement_withholds_it_when_the_refinement_is_withdrawn(tmp_path: Path) -> None:
    """#843's rule at page level: the page cites the text version it was
    shown.  When the refinement's source goes, the observation falls back to
    the month, and the page's day sentence is withheld (never served with
    the month's evidence)."""
    db = _desk(tmp_path)
    _filed_note(db, "n-month", "Atlas launch is 2026-10.", "atlas")
    _learn(db)
    _filed_note(db, "n-day", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db, Rules(on_change="refines"))
    write_page(db, Pages(recall=False), ATLAS, spec_for("project", "what-we-decided"))
    page = _page(db, ATLAS, "what-we-decided")
    assert [s["text"] for s in page["sentences"]] == ["Atlas launch is 2026-10-01."]
    db.notes.delete("n-day")
    assert _page(db, ATLAS, "what-we-decided") is None  # not served with the month's evidence
    sweep(db)
    assert _page(db, ATLAS, "what-we-decided") is None


def test_a_superseded_belief_leaves_the_page_at_read_time(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db, Pages(recall=False))
    assert "2026-10-01" in json.dumps(_page(db, ATLAS, CHANGED))
    _filed_note(db, "n2", "Atlas launch is 2026-11-15.", "atlas")
    _learn(db)  # supersedes the October belief
    page = _page(db, ATLAS, CHANGED)
    assert page is None and _page(db, ATLAS, CHANGED) is None


def test_a_sentence_with_no_ref_the_desk_opens_is_never_served(tmp_path: Path) -> None:
    """A dictation has no Desk window.  A sentence that rests only on one is
    withheld, even when the store holds it (the recall never offers one; this
    is the reader's own check)."""
    from holdspeak.memory.consolidate import LiveText
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder, passthrough_run

    db = _desk(tmp_path)
    said = "Desk lunch moves to Friday."
    entry = DictationJournalRecorder(db.dictation_journal).record(
        passthrough_run(said), source="dictation", transcript=said)
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    sweep(db)
    with db._connection() as conn:
        [(chunk_id, chunk_sha, anchor)] = sorted(LiveText(conn).chunks(f"dictation:{entry.id}"))
        [(note_chunk, note_sha, note_anchor)] = sorted(LiveText(conn).chunks("note:nd"))
    cite = {"kind": "chunk", "source_ref": f"dictation:{entry.id}", "chunk_id": chunk_id,
            "chunk_sha": chunk_sha, "anchor": anchor}
    note = {"kind": "chunk", "source_ref": "note:nd", "chunk_id": note_chunk,
            "chunk_sha": note_sha, "anchor": note_anchor}
    db.memory_index.write_page(
        page_id=pages_module.page_id(DESK, CHANGED), scope=DESK, slug=CHANGED, question="What changed this week?",
        answer_md="", sources=[], seen="", version=1,
        sentences=[{"text": said, "cites": [cite]}, {"text": "Desk lunch is noon.", "cites": [note]}],
    )
    page = _page(db, DESK, CHANGED)
    assert [s["text"] for s in page["sentences"]] == ["Desk lunch is noon."] and page["withheld"] == 1


# ── scope ───────────────────────────────────────────────────────────────


def test_two_projects_a_page_never_holds_the_other_projects_word(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "na", "Atlas codename is ZEPHYRATLAS.", "atlas")
    _filed_note(db, "nh", "Harbor codename is QUOKKAHARBOR.", "harbor")
    writer = Pages()
    _built(db, writer)
    for payload in writer.payloads:
        prompt = payload["user_prompt"]
        assert not ("ZEPHYRATLAS" in prompt and "QUOKKAHARBOR" in prompt)
    atlas = json.dumps([_page(db, ATLAS, s.slug) for s in PAGE_SET["project"]])
    harbor = json.dumps([_page(db, HARBOR, s.slug) for s in PAGE_SET["project"]])
    assert "ZEPHYRATLAS" in atlas and "QUOKKAHARBOR" not in atlas
    assert "QUOKKAHARBOR" in harbor and "ZEPHYRATLAS" not in harbor
    drafted = memory_for("project.update_draft", db, project_id="atlas", query="codename",
                         pages=project_pages("atlas", CHANGED, "what-is-open")).prompt_block()
    assert "ZEPHYRATLAS" in drafted and "QUOKKAHARBOR" not in drafted


# ── the answer: cut, fail whole, redact ─────────────────────────────────


def test_a_sentence_whose_ref_is_not_in_the_input_is_cut(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    writer = Pages()
    writer.answer = {"sentences": [
        {"text": "Atlas launch is 2026-10-01.", "refs": ["o1"]},
        {"text": "Harbor is cancelled.", "refs": ["o9"]},          # not in the input
        {"text": "Atlas is late.", "refs": ["o1", "r77"]},         # one ref not in the input
        {"text": "Nobody knows.", "refs": []},                     # no ref
        {"text": "Atlas is fine.", "refs": ["x1"]},                # not a label
    ]}
    stats = _built(db, writer)
    assert stats["pages"] >= 1
    page = _page(db, ATLAS, CHANGED)
    assert [s["text"] for s in page["sentences"]] == ["Atlas launch is 2026-10-01."]
    held = _memory_text(db)
    for cut in ("Harbor is cancelled", "Atlas is late", "Nobody knows", "Atlas is fine"):
        assert cut not in held


# ── attribution (review round 1, Astra, PR #848) ──────────────────────

WITHDRAWALS = ["delete", "edit", "exclude", "refile", "sensitive"]


def _status_and_codename(db: Database, mode: str) -> tuple[tuple[str, str], str, Callable[[], None], dict]:
    """Astra's repro: a status source and a codename source in one scope.
    Returns the scope, the codename's ref, the withdrawal for ``mode`` and
    the read arguments (an exclusion withdraws by the caller's refs)."""
    if mode == "sensitive":
        _filed_note(db, "n-status", "Desk status is approved.", None)
        thread = db.threads.create_thread(title="Planning")
        message = db.threads.append_message(thread.id, role="user")
        part = db.threads.append_part(message.id, kind="text", text="Desk codename is ZEPHYRSECRET.")

        def withdraw() -> None:
            db.threads.append_part(message.id, kind="text", text=part.text, sensitive=True)
            db.threads.delete_part(part.id)

        return DESK, f"thread:{thread.id}", withdraw, {}
    _filed_note(db, "n-status", "Atlas status is approved.", "atlas")
    _filed_note(db, "n-code", "Atlas codename is ZEPHYRSECRET.", "atlas")

    def withdraw() -> None:
        if mode == "delete":
            db.notes.delete("n-code")
        elif mode == "edit":
            _filed_note(db, "n-code", "Lunch is at noon.", "atlas")
        elif mode == "refile":
            db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-code", deleted=True)
            db.project_relationships.upsert(project_id="harbor", resource_ref="note:n-code")

    return ATLAS, "note:n-code", withdraw, ({"exclude_refs": ["note:n-code"]} if mode == "exclude" else {})


def _misattributing(payload: dict) -> dict:
    """The status sentence, rightly cited, and the codename sentence cited
    to the STATUS input (the model's wrong attribution)."""
    lines = Pages.lines(payload)
    status = next(label for label, text in lines.items() if "status is approved" in text)
    word = "Desk" if "Desk status" in lines[status] else "Atlas"
    return {"sentences": [
        {"text": f"{word} status is approved.", "refs": [status]},
        {"text": f"{word} codename is ZEPHYRSECRET.", "refs": [status]},
    ]}


def _drafted(db: Database, scope: tuple[str, str], **kwargs: Any) -> str:
    pages = (scope + (CHANGED,),)
    project = scope[1] or None
    return memory_for("project.update_draft", db, project_id=project, query="status codename",
                      pages=pages, **kwargs).prompt_block()


@pytest.mark.parametrize("mode", WITHDRAWALS)
def test_a_sentence_cited_to_the_wrong_input_is_cut_when_it_is_written(tmp_path: Path, mode: str) -> None:
    db = _desk(tmp_path)
    scope, _ref, withdraw, kwargs = _status_and_codename(db, mode)
    _learn(db)
    writer = Pages()
    writer.answer = _misattributing
    assert write_page(db, writer, scope, spec_for(scope[0], CHANGED))["cut"] == 1
    page = _page(db, scope, CHANGED)
    assert [s["text"] for s in page["sentences"]] == [f"{'Desk' if scope == DESK else 'Atlas'} status is approved."]
    with db._connection() as conn:
        assert "ZEPHYRSECRET" not in conn.execute("SELECT sentences_json||answer_md FROM memory_pages").fetchone()[0]
    withdraw()
    for step in (lambda: None, lambda: sweep(db), lambda: _learn(db)):
        step()
        assert "ZEPHYRSECRET" not in json.dumps(_page(db, scope, CHANGED, **kwargs))
        drafted_kwargs = {"exclude_refs": kwargs["exclude_refs"]} if kwargs else {}
        assert "ZEPHYRSECRET" not in _drafted(db, scope, **drafted_kwargs)


@pytest.mark.parametrize("mode", WITHDRAWALS)
def test_read_time_withholds_a_token_only_a_withdrawn_input_held(tmp_path: Path, mode: str, monkeypatch) -> None:
    """The belt: a page whose sentence carries the codename but cites the
    status input (written past the write-time check, as an older writer
    could) loses that sentence at READ time once the codename's source is
    withdrawn, whatever the sentence cites."""
    db = _desk(tmp_path)
    scope, _ref, withdraw, kwargs = _status_and_codename(db, mode)
    _learn(db)
    real = pages_module.validate_output
    monkeypatch.setattr(pages_module, "validate_output", lambda raw, labels: real(raw, list(labels)))
    writer = Pages()
    writer.answer = _misattributing
    write_page(db, writer, scope, spec_for(scope[0], CHANGED))
    page = _page(db, scope, CHANGED)
    assert "ZEPHYRSECRET" in json.dumps(page) and page["withheld"] == 0  # the codename's source is live
    withdraw()
    for step in (lambda: None, lambda: sweep(db), lambda: _learn(db)):
        step()
        page = _page(db, scope, CHANGED, **kwargs)
        assert "ZEPHYRSECRET" not in json.dumps(page)
        assert page is not None and "status is approved" in json.dumps(page) and page["withheld"] == 1
        drafted_kwargs = {"exclude_refs": kwargs["exclude_refs"]} if kwargs else {}
        drafted = _drafted(db, scope, **drafted_kwargs)
        assert "ZEPHYRSECRET" not in drafted and "status is approved" in drafted


def test_a_number_matches_only_as_a_whole_token(tmp_path: Path) -> None:
    """Astra's repro: "26" is not "2026"."""
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas build is 2026.", "atlas")
    _filed_note(db, "n2", "Atlas budget is 26.", "atlas")
    _learn(db)
    writer = Pages()

    def answer(payload: dict) -> dict:
        lines = Pages.lines(payload)
        build = next(label for label, text in lines.items() if "build is 2026" in text)
        budget = next(label for label, text in lines.items() if "budget is 26" in text)
        return {"sentences": [
            {"text": "Atlas budget is 26.", "refs": [build]},          # wrong input: cut
            {"text": "Atlas budget is 26.", "refs": [build, budget]},  # one cited input holds it
            {"text": "Atlas launch is in October 2026.", "refs": [build]},  # "launch", "october": cut
        ]}

    writer.answer = answer
    assert write_page(db, writer, ATLAS, spec_for("project", CHANGED))["cut"] == 2
    assert [s["text"] for s in _page(db, ATLAS, CHANGED)["sentences"]] == ["Atlas budget is 26."]
    assert pages_module.content_tokens("Atlas budget is 26.") == {"atlas", "budget", "26"}
    # Only the number differs: "26" is not in "2026".
    kept, cut = pages_module.validate_output(
        {"sentences": [{"text": "Atlas budget is 26.", "refs": ["o1"]}]}, {"o1": "Atlas budget is 2026."})
    assert (kept, cut) == ([], 1)


def test_a_name_and_its_claim_must_come_from_one_cited_input(tmp_path: Path) -> None:
    """The open limit of #848: attribution by words let shared words carry
    another input's meaning.  "Atlas owner is Dana" + "Harbor owner is Lee"
    hold every word of "Atlas owner is Lee"; no ONE input holds Atlas, Lee
    and "owner", so it is cut."""
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas owner is Dana.", "atlas")
    _filed_note(db, "n2", "Harbor owner is Lee.", "atlas")
    _learn(db)
    writer = Pages()

    def answer(payload: dict) -> dict:
        lines = Pages.lines(payload)
        dana = next(label for label, text in lines.items() if "owner is Dana" in text)
        lee = next(label for label, text in lines.items() if "owner is Lee" in text)
        return {"sentences": [
            {"text": "Atlas owner is Lee.", "refs": [dana, lee]},      # names from two inputs: cut
            {"text": "Harbor owner is Dana.", "refs": [dana, lee]},    # the same, crossed: cut
            {"text": "Atlas owner is Dana.", "refs": [dana, lee]},     # one input holds it: kept
            {"text": "Harbor owner is Lee.", "refs": [lee]},
        ]}

    writer.answer = answer
    assert write_page(db, writer, ATLAS, spec_for("project", CHANGED))["cut"] == 2
    served = [s["text"] for s in _page(db, ATLAS, CHANGED)["sentences"]]
    assert served == ["Atlas owner is Dana.", "Harbor owner is Lee."]


def test_numbers_from_two_inputs_never_swap(tmp_path: Path) -> None:
    """Astra, #870: "Atlas budget is 40." + "Atlas headcount is 80." gave a
    page that said "Atlas budget is 80." and "Atlas headcount is 40." (both
    cited both inputs).  Each is cut at write; the right sentences serve."""
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas budget is 40.", "atlas")
    _filed_note(db, "n2", "Atlas headcount is 80.", "atlas")
    _learn(db)
    writer = Pages()

    def answer(payload: dict) -> dict:
        lines = Pages.lines(payload)
        budget = next(label for label, text in lines.items() if "budget is 40" in text)
        heads = next(label for label, text in lines.items() if "headcount is 80" in text)
        return {"sentences": [
            {"text": "Atlas budget is 80.", "refs": [budget, heads]},
            {"text": "Atlas headcount is 40.", "refs": [budget, heads]},
            {"text": "The Atlas budget is 40.", "refs": [budget, heads]},   # a paraphrase one input holds
            {"text": "Atlas headcount is 80.", "refs": [heads]},
        ]}

    writer.answer = answer
    assert write_page(db, writer, ATLAS, spec_for("project", CHANGED))["cut"] == 2
    served = [s["text"] for s in _page(db, ATLAS, CHANGED)["sentences"]]
    assert served == ["The Atlas budget is 40.", "Atlas headcount is 80."]


@pytest.mark.parametrize("text,cited,ok", [
    ("Atlas owner is Lee.", ["Atlas owner is Dana.", "Harbor owner is Lee."], False),
    ("Atlas owner is Dana.", ["Atlas owner is Dana.", "Harbor owner is Lee."], True),
    # Astra's #870 repro: numbers swapped between two inputs of one subject.
    ("Atlas budget is 80.", ["Atlas budget is 40.", "Atlas headcount is 80."], False),
    ("Atlas headcount is 40.", ["Atlas budget is 40.", "Atlas headcount is 80."], False),
    # A paraphrase that one input holds still serves (order, case, stopwords).
    ("The Atlas launch date is 2026-10-01.", ["Atlas launch date: 2026-10-01", "Atlas budget is 40."], True),
    ("atlas budget is 40", ["Atlas budget is 40.", "Atlas headcount is 80."], True),
    # A sentence that joins two inputs is cut (a cut serves less, never a wrong claim).
    ("Atlas launch is 2026-10-01 and budget is 40k.", ["Atlas launch is 2026-10-01.", "Atlas budget is 40k."], False),
    ("Atlas launch is 2026.", ["Atlas build is 2026."], False),   # a word no input holds
])
def test_attribution_is_entity_aware(text: str, cited: list[str], ok: bool) -> None:
    assert pages_module.attributed(text, cited) is ok


# ── stale: a second change in the same second (Astra, PR #848) ──────────


def test_a_second_change_in_the_same_second_makes_the_page_stale(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import memory_index

    frozen = datetime.now(timezone.utc).replace(microsecond=0)
    monkeypatch.setattr(memory_index, "_now", lambda: frozen.isoformat(timespec="seconds"))
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Send the weekly report on Monday.", "atlas")  # recall only: no fact
    _built(db)
    page = _page(db, ATLAS, CHANGED)
    assert "Monday" in json.dumps(page) and page["stale"] is False
    _filed_note(db, "n2", "Send the weekly report on Friday.", "atlas")
    _learn(db)  # the same second: every stamp is the same
    page = _page(db, ATLAS, CHANGED)
    assert page["withheld"] == 1 and page["stale"] is True
    later = frozen + timedelta(hours=2)
    assert (ATLAS, CHANGED) in [(d["scope"], d["spec"].slug) for d in pending_pages(db, now=later)]
    write_pending(db, Pages(), now=later)
    assert "Friday" in json.dumps(_page(db, ATLAS, CHANGED))


def test_a_refile_stales_both_projects_pages(tmp_path: Path, monkeypatch) -> None:
    """Open limit of #848: a refile changes no memory row, so the
    destination's page stayed fresh when the moved source was stamped before
    the page's marker.  The scope digest moves the source's key out of
    Atlas's set and into Harbor's."""
    from holdspeak.db import memory_index

    db = _desk(tmp_path)
    clock = {"now": datetime(2026, 10, 5, 9, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr(memory_index, "_now", lambda: clock["now"].isoformat(timespec="seconds"))
    ref = _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)                       # n1 stamped 09:00
    clock["now"] += timedelta(hours=1)
    _filed_note(db, "n2", "Harbor launch is 2026-11-01.", "harbor")
    _built(db)                       # n2 and the pages stamped 10:00
    assert _page(db, ATLAS, CHANGED)["stale"] is False
    assert _page(db, HARBOR, CHANGED)["stale"] is False
    db.project_relationships.upsert(project_id="atlas", resource_ref=ref, deleted=True)
    db.project_relationships.upsert(project_id="harbor", resource_ref=ref)
    assert _page(db, HARBOR, CHANGED)["stale"] is True   # n1's stamp is older than the marker
    assert _page(db, ATLAS, CHANGED) is None or _page(db, ATLAS, CHANGED)["stale"] is True
    later = clock["now"] + timedelta(hours=2)
    due = [(d["scope"], d["spec"].slug) for d in pending_pages(db, now=later)]
    assert (HARBOR, CHANGED) in due and (ATLAS, CHANGED) in due
    write_pending(db, Pages(), now=later)
    assert "2026-10-01" in json.dumps(_page(db, HARBOR, CHANGED))
    assert _page(db, HARBOR, CHANGED)["stale"] is False


def test_a_change_stamped_by_a_clock_that_ran_backwards_makes_the_page_stale(tmp_path: Path, monkeypatch) -> None:
    """Open limit of #848: staleness compared stamps, so a change stamped
    before the page's marker (the clock ran back) was missed.  Content keys
    only: the edit is seen whatever its stamp."""
    from holdspeak.db import memory_index

    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Send the weekly report on Monday.", "atlas")
    _built(db)
    assert _page(db, ATLAS, CHANGED)["stale"] is False
    back = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(timespec="seconds")
    monkeypatch.setattr(memory_index, "_now", lambda: back)
    _filed_note(db, "n2", "Send the weekly report on Friday.", "atlas")
    _learn(db)
    with db._connection() as conn:
        stamp = conn.execute("SELECT updated_at FROM memory_sources WHERE source_ref='note:n2'").fetchone()[0]
        marker = conn.execute("SELECT last_memory_seen_at FROM memory_pages WHERE slug=?", (CHANGED,)).fetchone()[0]
    assert stamp < marker  # the change is stamped before the page saw the scope
    assert _page(db, ATLAS, CHANGED)["stale"] is True


# ── recall: other projects never fill the bound (Astra, PR #848) ────────


def test_other_projects_never_exhaust_a_projects_recall(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import primitives

    db = _desk(tmp_path)
    # The Atlas notes are older (still this week) than the 401 Harbor notes,
    # so the Harbor chunks come first in "newest first".  The note producer
    # stamps from the wall clock: pin it for the two Atlas notes.
    older = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    monkeypatch.setattr(primitives, "_now_iso", lambda: older)
    _filed_note(db, "a1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "a2", "Send the weekly report on Friday.", "atlas")
    monkeypatch.undo()
    for index in range(401):
        _filed_note(db, f"h{index:03d}", f"Harbor item {index} is open.", "harbor")
    sweep(db)
    for slug in ("what-changed-this-week", "risks-and-disputes"):
        recall = pages_module.page_inputs(db, ATLAS, spec_for("project", slug))["recall"]
        assert all(item["source_ref"] in ("note:a1", "note:a2") for item in recall)
    recall = pages_module.page_inputs(db, ATLAS, spec_for("project", CHANGED))["recall"]
    assert {item["source_ref"] for item in recall} == {"note:a1", "note:a2"}
    assert any("Friday" in item["text"] for item in recall)
    write_page(db, Pages(), ATLAS, spec_for("project", CHANGED))
    assert "Friday" in json.dumps(_page(db, ATLAS, CHANGED))


@pytest.mark.parametrize("answer", [
    {"sentences": "not a list"},
    {"sentences": [{"text": "Atlas launch is 2026-10-01.", "refs": ["o1"], "extra": 1}]},
    {"sentences": [{"text": 7, "refs": ["o1"]}]},
    {"sentences": [{"text": "Atlas launch is 2026-10-01.", "refs": "o1"}]},
    {"sentences": [{"text": "Atlas launch is 2026-10-01.", "refs": [1]}]},
    {"sentences": [], "note": "extra key"},
    {"sentences": [{"text": f"Line {i}.", "refs": ["o1"]} for i in range(13)]},
    ["not an object"],
])
def test_a_malformed_answer_fails_whole_writes_nothing_and_backs_off(tmp_path: Path, answer: Any) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    _filed_note(db, "n2", "Atlas budget is 40k.", "atlas")
    _learn(db)
    _aged(db)
    before = _rows(db, "memory_pages", "memory_page_history")
    writer = Pages()
    writer.answer = answer
    stats = write_pending(db, writer)
    assert stats["failed"] >= 1 and stats["pages"] == 0
    assert _rows(db, "memory_pages", "memory_page_history") == before
    with db._connection() as conn:
        jobs = [dict(r) for r in conn.execute("SELECT kind,status,attempts FROM memory_jobs WHERE kind='page'")]
    assert jobs and all(j == {"kind": "page", "status": "queued", "attempts": 1} for j in jobs)
    # The back-off holds: the next pass makes no call on that input.
    again = Pages()
    write_pending(db, again)
    assert again.calls == 0
    with pytest.raises(PageOutputError):
        pages_module.validate_output(answer, ["o1", "r1"])


@pytest.mark.parametrize("raw", [
    "\n".join(["A" * 64, "B" * 64, "C" * 64]),
    "x" * 389 + " ghp_" + "A" * 36,
    "x" * 395 + " ghp_" + "A" * 36,  # the marker crosses the limit: it goes whole
])
def test_a_page_sentence_is_redacted_before_it_is_folded_or_cut(tmp_path: Path, raw: str) -> None:
    from holdspeak.memory.defense import redact

    assert redact(raw) != raw
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    writer = Pages()
    writer.answer = {"sentences": [{"text": raw, "refs": ["o1"]}]}
    _built(db, writer)
    held = _memory_text(db) + json.dumps(_page(db, ATLAS, CHANGED))
    for leak in ("A" * 64, "B" * 64, "C" * 64, "ghp_A"):
        assert leak not in held
    for sentence in (_page(db, ATLAS, CHANGED) or {"sentences": []})["sentences"]:
        assert re.search(r"\[(?!redacted\])", sentence["text"]) is None, sentence


def test_a_secret_never_reaches_the_page_engine_or_a_page(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    secret = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2"
    _filed_note(db, "n-key", f"Deploy token is rotated. The new one is token={secret} now.", "atlas")
    writer = Pages()
    _built(db, writer)
    assert writer.calls and secret not in writer.received()
    assert secret not in _memory_text(db)
    assert REDACTED in json.dumps(_page(db, ATLAS, CHANGED))


# ── history: append only ────────────────────────────────────────────────

PAGE_HISTORY_WRITES = [
    "UPDATE memory_page_history SET answer_md='rewritten'",
    "DELETE FROM memory_page_history",
    "INSERT OR REPLACE INTO memory_page_history(id,page_id,built_at,answer_md,sources_json,writer_version)"
    " SELECT id,page_id,built_at,'rewritten',sources_json,writer_version FROM memory_page_history LIMIT 1",
    "INSERT OR REPLACE INTO memory_page_history(rowid,page_id,built_at,answer_md,sources_json,writer_version)"
    " SELECT rowid,page_id,built_at,'rewritten',sources_json,writer_version FROM memory_page_history LIMIT 1",
    "REPLACE INTO memory_page_history(rowid,page_id,built_at,answer_md,sources_json,writer_version)"
    " VALUES ((SELECT MIN(rowid) FROM memory_page_history),'x','x','rewritten','[]',1)",
]


@pytest.mark.parametrize("statement", PAGE_HISTORY_WRITES)
def test_page_history_refuses_every_rewrite_on_the_real_connection(tmp_path: Path, statement: str) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    _filed_note(db, "n2", "Atlas budget is 40k.", "atlas")
    _learn(db)
    write_pending(_aged(db), Pages())

    def rows() -> list[tuple]:
        reopened = Database(tmp_path / "obs.db")
        with reopened._connection() as conn:
            return [tuple(str(v) for v in r) for r in conn.execute("SELECT rowid,* FROM memory_page_history ORDER BY rowid")]

    before = rows()
    assert before
    with db._connection() as conn:
        assert conn.execute("PRAGMA recursive_triggers").fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError, match="append only"):
            conn.execute(statement)
        conn.commit()
    after = rows()
    assert after == before and "rewritten" not in repr(after)


# ── one transaction; an input that moves ────────────────────────────────


def test_a_job_killed_inside_its_transaction_changes_nothing(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _built(db)
    _filed_note(db, "n2", "Atlas budget is 40k.", "atlas")
    _learn(db)
    _aged(db)
    with db._connection() as conn:
        # The real write runs; the page row write dies AFTER its history row.
        conn.execute("CREATE TEMP TRIGGER die_on_page BEFORE UPDATE ON memory_pages"
                     " BEGIN SELECT RAISE(ABORT, 'the hub stopped'); END")
        conn.commit()
    before = _rows(db, *PAGE_TABLES)
    with pytest.raises(sqlite3.IntegrityError, match="the hub stopped"):
        write_pending(db, Pages())
    with db._connection() as conn:
        conn.execute("DROP TRIGGER die_on_page")
        conn.commit()
    assert _rows(db, *PAGE_TABLES) == before  # the history row went with it


def test_an_input_that_moves_while_the_engine_reads_writes_nothing(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    writer = Pages()
    writer.during = lambda _payload: _filed_note(db, "n1", "Lunch is at noon.", "atlas")
    done = write_page(db, writer, ATLAS, spec_for("project", CHANGED))
    assert done["state"] == "skipped" and done["calls"] == 1
    assert _page(db, ATLAS, CHANGED) is None
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_pages").fetchone()[0] == 0


# ── load: yield and budget before every call ────────────────────────────


def _due_pages(tmp_path: Path) -> Database:
    db = _desk(tmp_path)
    _filed_note(db, "na", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "nh", "Harbor budget is 40k.", "harbor")
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    _learn(db)
    assert len(pending_pages(db)) == 4 + 4 + 2
    return db


def test_the_page_job_yields_before_every_call(tmp_path: Path) -> None:
    db = _due_pages(tmp_path)
    live = {"on": False}
    writer = Pages()
    writer.during = lambda _payload: live.update(on=True)
    stats = write_pending(db, writer, yield_check=lambda: "a meeting is recording" if live["on"] else "")
    assert writer.calls == 1 == stats["calls"] and stats["yielded"] == "a meeting is recording" and stats["more"] == 1


def test_the_budget_counts_every_attempted_call_bad_answers_too(tmp_path: Path) -> None:
    db = _due_pages(tmp_path)
    writer = Pages()
    writer.answer = {"sentences": "not a list"}
    budget = CallBudget(3)
    stats = write_pending(db, writer, budget=budget)
    assert writer.calls == 3 == stats["calls"] == budget.calls and stats["failed"] == 3 and stats["more"] == 1


def test_pages_share_the_pass_budget_in_the_conductor(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.memory import consolidate as consolidate_module

    db = _desk(tmp_path)
    _filed_note(db, "na", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "nh", "Harbor budget is 40k.", "harbor")
    facts, rules, writer = Facts(), Rules(), Pages()
    monkeypatch.setattr("holdspeak.memory.extract.resolve_extractor", lambda *_a: facts)
    monkeypatch.setattr(consolidate_module, "resolve_consolidator", lambda *_a: rules)
    monkeypatch.setattr(pages_module, "resolve_page_writer", lambda *_a: writer)
    monkeypatch.setattr(memory_conductor, "live_work", lambda *_a: "")
    monkeypatch.setattr(memory_conductor, "EXTRACT_CALLS_PER_PASS", 5)
    sweep(db)
    extract, consolidate = memory_conductor._model_steps(db, SimpleNamespace(), None)
    pages = consolidate["pages"]
    assert facts.calls == extract["calls"] == 2 and rules.calls == consolidate["calls"] == 2
    assert writer.calls == pages["calls"] == 1 and pages["more"] == 1  # 2 + 2 + 1 = the budget of 5
    # The conductor's yield check runs before every page call.
    monkeypatch.setattr(memory_conductor, "live_work", lambda *_a: "a meeting is recording")
    report = memory_conductor._page_step(db, SimpleNamespace(), None, CallBudget(24))
    assert report["calls"] == 0 and report["yielded"] == "a meeting is recording" and writer.calls == 1


# ── custody ─────────────────────────────────────────────────────────────


def test_people_store_content_never_becomes_a_page(tmp_path: Path) -> None:
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService

    owner = Principal(PrincipalKind.OWNER, "memory-slice5-owner")
    db = _desk(tmp_path, "holdspeak.db")
    store = EncryptedPeopleStore(tmp_path / "people-private" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    relationship = people.create_relationship(owner, {"display_name": "Zorvane Quillfeather"})
    note = people.create_note(owner, relationship["id"], {"topic": "Growth", "body": "PEOPLESENTINEL is promoted."})
    _meeting(db, "m-plain", "Atlas plan is ready.", day=1)
    writer = Pages()
    _built(db, writer)
    assert writer.calls
    held = _memory_text(db) + json.dumps([_page(db, ATLAS, s.slug) for s in PAGE_SET["project"]])
    for word in ("PEOPLESENTINEL", "Quillfeather", note["id"], relationship["id"]):
        assert word not in writer.received() and word not in held


# ── the drafters ────────────────────────────────────────────────────────

DRAFTERS = ("meeting.deferred_analysis", "project.update_draft", "project.brief_prepare")


@pytest.mark.parametrize("capability", DRAFTERS)
def test_with_no_page_a_drafters_memory_is_byte_identical(tmp_path: Path, capability: str) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "nh", "Harbor budget is 40k.", "harbor")
    _learn(db)  # observations, but no page engine: no page
    policy = memory_policy(capability)
    today = memory_context(db, project_id="atlas", query="Atlas launch", max_excerpts=policy.max_excerpts,
                           excerpt_chars=min(600, policy.block_chars), block_chars=policy.block_chars)
    with_pages = memory_for(capability, db, project_id="atlas", query="Atlas launch",
                            pages=project_pages("atlas", *(s.slug for s in PAGE_SET["project"])))
    assert with_pages.prompt_block() == today.prompt_block() and with_pages == today
    # A page in ANOTHER project changes nothing for Atlas either.
    write_pending(db, Pages())
    assert _page(db, HARBOR, CHANGED) is not None
    db.project_relationships.upsert(project_id="atlas", resource_ref="note:n1", deleted=True)
    db.project_relationships.upsert(project_id="harbor", resource_ref="note:n1")
    again = memory_for(capability, db, project_id="atlas", query="Atlas launch",
                       pages=project_pages("atlas", *(s.slug for s in PAGE_SET["project"])))
    plain = memory_for(capability, db, project_id="atlas", query="Atlas launch")
    assert again.prompt_block() == plain.prompt_block()


def test_a_served_page_leads_the_drafters_block_as_plain_context_inside_the_budget(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Atlas budget is 40k. " + "More words here. " * 80, "atlas")
    _built(db)
    policy = memory_policy("project.update_draft")
    memory = memory_for("project.update_draft", db, project_id="atlas", query="Atlas budget",
                        pages=project_pages("atlas", CHANGED))
    first = memory.excerpts[0]
    assert first.kind == "memory_page" and not first.citable
    assert first.ref not in memory.refs and "What changed this week?" in first.title
    assert "Atlas launch is 2026-10-01." in first.text
    assert len(memory.prompt_block()) <= policy.block_chars
    assert len(memory.excerpts) <= policy.max_excerpts
    # The drafter's own source counts as not live: the page never hands it back.
    own = memory_for("project.update_draft", db, project_id="atlas", query="Atlas budget",
                     exclude_refs=["note:n1"], pages=project_pages("atlas", CHANGED))
    assert "2026-10-01" not in own.prompt_block()


def test_the_meeting_summary_reads_its_projects_pages(tmp_path: Path) -> None:
    from holdspeak.intel_queue import _meeting_memory

    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _meeting(db, "m1", "Atlas vendor is Kestrel.", day=3)
    _learn(db)
    meeting = db.meetings.get_meeting("m1")
    before = _meeting_memory(db, meeting).prompt_block()
    writer = Pages()
    writer.answer = lambda payload: {"sentences": [
        {"text": text, "refs": [label]} for label, text in Pages.lines(payload).items() if label.startswith("o")
    ]}
    for slug in ("what-we-decided", "what-is-open"):
        write_page(db, writer, ATLAS, spec_for("project", slug))
    after = _meeting_memory(db, meeting).prompt_block()
    assert after != before and "(memory page, context only)" in after
    assert "Atlas launch is 2026-10-01." in after
    # The meeting's own belief rests on the meeting: held out of its own memory.
    assert "Kestrel" not in after
    with db._connection() as conn:
        stored = conn.execute("SELECT sentences_json FROM memory_pages WHERE slug='what-we-decided'").fetchone()[0]
    assert "Kestrel" in stored


# ── the MCP tool and the service ────────────────────────────────────────


def test_the_mcp_tool_reads_a_page_and_needs_read(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.mcp.families import memory as family
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError, ValidationError
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.services.thread_tools import tool_class

    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    _built(db)
    monkeypatch.setattr(family, "db_or", lambda _default: db)
    assert "memory.page" in {tool["name"] for tool in family.TOOLS}
    assert TOOL_AUTHORITY["memory.page"] == "work"
    assert tool_class("memory.page") == "evidence_read"
    out = family.dispatch("memory.page", {"project_id": "atlas", "slug": CHANGED}, OWNER)
    assert "Atlas launch is 2026-10-01." in out["page"]["answer"]
    assert out["page"]["sources"][0] == {"ref": "note:n1", "opens": True}
    desk = family.dispatch("memory.page", {"scope": "desk", "slug": CHANGED}, OWNER)["page"]
    assert "Desk lunch" in desk["answer"] and "Atlas" not in desk["answer"]
    assert family.dispatch("memory.page", {"project_id": "harbor", "slug": CHANGED}, OWNER) == {"page": None}
    service = MemoryService(db)
    with pytest.raises(ServiceError):
        service.page(Principal(PrincipalKind.NONE, ""), project_id="atlas", slug=CHANGED)
    for bad in ({"slug": "what-i-owe", "project_id": "atlas"}, {"slug": CHANGED},
                {"slug": "nope", "scope": "desk"}, {"slug": CHANGED, "scope": "desk", "project_id": "atlas"}):
        with pytest.raises(ValidationError):
            service.page(OWNER, **bad)


# ── the router: no engine, a wider assignment, the assigned engine ──────


class _PageEngine:
    """The physical chat leaf the runner builds."""

    active_provider = "fixture"
    active_model = "pages-fixture"

    def __init__(self) -> None:
        self.rules = Rules()
        self.pages = Pages()
        self.prompts: list[dict] = []

    def run_prompt(self, **kwargs):
        self.prompts.append(kwargs)
        name = kwargs["response_format"]["json_schema"]["name"]
        if name == "memory_facts":
            return json.dumps(Facts().extract(kwargs))
        if name == "memory_observations":
            return json.dumps(self.rules.consolidate(kwargs))
        assert name == "memory_page"
        return json.dumps(self.pages.write(kwargs))


@pytest.fixture()
def routed(tmp_path: Path):
    db = Database(tmp_path / "routed.db")
    refs = build_corpus(db)
    broker = _configure(db)
    engine = _PageEngine()
    broker.inference_runner._engine_factory = lambda revision, **_kwargs: engine
    return SimpleNamespace(db=db, refs=refs, broker=broker, engine=engine)


def test_no_page_engine_nothing_is_called_written_or_changed(routed, monkeypatch) -> None:
    golden = json.loads(bench.GOLDEN.read_text())
    _profile(routed.db, "obs-model", model="qwen-lan", boundary="private_network")
    _assign(routed.db, EXTRACT_CAPABILITY, ["obs-model"])
    _assign(routed.db, CONSOLIDATE_CAPABILITY, ["obs-model"])
    monkeypatch.setattr(memory_conductor, "EXTRACT_CALLS_PER_PASS", 1000)
    monkeypatch.setattr(memory_conductor, "CONSOLIDATE_CALLS_PER_PASS", 1000)
    assert resolve_page_writer(routed.broker, OWNER) is None
    report = memory_conductor.tick(routed.db, routed.broker)
    assert report["consolidate"]["jobs"] > 0
    assert report["consolidate"]["pages"]["engine"] == "" and report["consolidate"]["pages"]["calls"] == 0
    names = {p["response_format"]["json_schema"]["name"] for p in routed.engine.prompts}
    assert "memory_page" not in names
    with routed.db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_pages").fetchone()[0] == 0
    assert bench.keyword_snapshot(routed.db, routed.refs) == golden


def test_a_network_default_made_without_the_owners_press_is_never_used_for_pages(routed) -> None:
    # Owner rulings 2026-10-05: a LOCAL or owner-made default is inherited
    # (tests/unit/test_batteries_default.py); a network default HoldSpeak
    # made by itself never is.
    from tests.unit.test_batteries_default import mark_made_by_holdspeak
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    _profile(routed.db, "chat-model", boundary="private_network")
    made = InferenceAssignmentService(routed.db).set_assignment(OWNER, {
        "command_id": "assign-global", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "chat-model", "profile_revision": 1}],
    })
    mark_made_by_holdspeak(routed.db, made)
    assert resolve_page_writer(routed.broker, OWNER) is None


def test_the_assigned_engine_writes_pages_through_the_runner_with_a_receipt(routed, monkeypatch) -> None:
    _profile(routed.db, "obs-model", model="qwen-lan", boundary="private_network")
    _assign(routed.db, EXTRACT_CAPABILITY, ["obs-model"])
    _assign(routed.db, CONSOLIDATE_CAPABILITY, ["obs-model"])
    monkeypatch.setattr(memory_conductor, "EXTRACT_CALLS_PER_PASS", 1000)
    monkeypatch.setattr(memory_conductor, "CONSOLIDATE_CALLS_PER_PASS", 1000)
    memory_conductor.tick(routed.db, routed.broker)
    golden_default = {q: routed.db.memory.search(q).to_dict() for q in ("Atlas", "Harbor budget", "Dana")}
    _assign(routed.db, PAGE_CAPABILITY, ["obs-model"])
    monkeypatch.setattr(memory_conductor, "PAGE_CALLS_PER_PASS", 1000)
    report = memory_conductor.tick(routed.db, routed.broker)
    pages = report["consolidate"]["pages"]
    assert pages["error"] == "" and pages["pages"] > 0 and pages["calls"] >= pages["pages"]
    writer = resolve_page_writer(routed.broker, memory_conductor._principal())
    assert writer.boundary not in ("", "local")
    receipt = routed.broker.store.receipt(next(iter(reversed(writer.operation_ids))))
    assert receipt["outcome"] == "succeeded" and receipt["actor_identity"] == "memory-conductor"
    with routed.db._connection() as conn:
        boundaries = {r[0] for r in conn.execute("SELECT boundary FROM memory_pages")}
        scopes = [tuple(r) for r in conn.execute("SELECT scope_kind,scope_id,slug FROM memory_pages")]
    assert boundaries == {writer.boundary}  # the egress boundary of the call that wrote it
    served = [read(routed.db, kind, scope_id, slug) for kind, scope_id, slug in scopes]
    assert any(served)
    for page in filter(None, served):
        assert page["boundary"] == writer.boundary
        for sentence in page["sentences"]:
            assert any(ref["opens"] for ref in sentence["refs"])
    # A default search is the same with pages in memory.
    assert {q: routed.db.memory.search(q).to_dict() for q in golden_default} == golden_default
