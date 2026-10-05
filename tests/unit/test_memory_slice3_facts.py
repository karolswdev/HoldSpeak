"""Memory slice 3: facts, entities, entity resolution and the entity walk
(docs/internal/MEMORY-DESIGN.md §1, §3.1 steps 5-6, §3.2, §5, §8 row 3, §9).

Every source is written by its real producer (the note, meeting and thread
repositories, the People service).  The engine is a scripted extractor (a
fixed answer per prompt) or the benchmark's recorded real-model answers; the
code under test is never doubled.  The router tests use the real router,
assignment service and runner; only the physical model leaf is replaced.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

import pytest

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.inference_capabilities import builtin_capability_definitions
from holdspeak.inference_memory_policy import memory_policy
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session.models import MeetingState, TranscriptSegment
from holdspeak.memory import extract as extract_module
from holdspeak.memory.defense import REDACTED
from holdspeak.memory.entities import token_guard
from holdspeak.memory.extract import (
    EXTRACT_CAPABILITY, EXTRACT_KINDS, ExtractionOutputError, extract_pending,
    extract_source, resolve_extractor,
)
from holdspeak.memory.retain import rebuild, sweep

from tests.memory_bench import bench
from tests.memory_bench.corpus import build_corpus
from tests.memory_bench.engines import fixture_key
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign

FACT_TABLES = ("memory_facts", "memory_entities", "memory_fact_entities", "memory_jobs")
FACTS_FIXTURE = Path(bench.HERE) / "facts.json"


def F(text: str, subject: str = "", entities=(), *, kind: str = "state", obj: str = "", start=None) -> dict:
    return {
        "text": text, "kind": kind, "subject": subject, "predicate": "is", "object": obj,
        "occurred_start": start, "occurred_end": None, "confidence": 0.9,
        "entities": [{"name": name, "kind": ekind} for name, ekind in entities],
    }


class Scripted:
    """A fixed answer per prompt: the first rule whose words are in the
    prompt's text gives the facts.  It keeps every payload it received and
    can run a hook during a call."""

    boundary = "local"
    model_id = "scripted"

    def __init__(self, rules: list[tuple[str, list[dict]]] | None = None, *, echo: bool = False) -> None:
        self.rules = list(rules or [])
        self.echo = echo
        self.payloads: list[dict] = []
        self.calls = 0
        self.during: Optional[Callable[[dict], None]] = None
        self.answer: Any = None

    def extract(self, payload: dict) -> Any:
        self.calls += 1
        self.payloads.append(payload)
        if self.during is not None:
            self.during(payload)
        if self.answer is not None:
            return self.answer
        prompt = payload["user_prompt"]
        for words, facts in self.rules:
            if words in prompt:
                return {"facts": facts}
        if self.echo:
            # Every word the engine was given becomes a fact and an entity, so
            # any text it received would be found in a memory table.
            text = prompt.split("<<<", 1)[1].split(">>>", 1)[0].strip()
            return {"facts": [F(text[:500], "Echo", [(text[:100], "topic")])]}
        return {"facts": []}

    def received(self) -> str:
        return "\n".join(payload["user_prompt"] for payload in self.payloads)


def _rows(db: Database, *tables: str) -> dict[str, list[tuple]]:
    out: dict[str, list[tuple]] = {}
    with db._connection() as conn:
        for table in tables or FACT_TABLES:
            out[table] = sorted(
                tuple(str(value) for value in row)
                for row in conn.execute(f"SELECT * FROM {table}")
            )
    return out


def _counts(db: Database) -> dict[str, int]:
    with db._connection() as conn:
        return {table: int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]) for table in FACT_TABLES}


def _memory_text(db: Database) -> str:
    """Every text value of every memory_* table."""
    parts: list[str] = []
    with db._connection() as conn:
        tables = [
            str(row[0]) for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'memory_%'"
            )
        ]
        for table in tables:
            for row in conn.execute(f"SELECT * FROM {table}"):
                parts.extend(str(value) for value in tuple(row) if not isinstance(value, bytes))
    return "\n".join(parts)


def _note(db: Database, note_id: str, title: str, body: str) -> None:
    db.notes.upsert(note_id=note_id, title=title, body_markdown=body)


def _meeting(db: Database, meeting_id: str, turns: list[tuple[str, str]], *, title: str = "") -> None:
    started = datetime(2026, 9, 14, 10, 0, 0)
    db.meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=started, ended_at=started, title=title or f"Meeting {meeting_id}",
        segments=[
            TranscriptSegment(text=text, speaker=speaker, start_time=float(i), end_time=float(i) + 1)
            for i, (speaker, text) in enumerate(turns)
        ],
    ))


def _refs(db: Database, query: str, **scope: Any) -> list[str]:
    return [hit.source_ref for hit in db.memory.search(query, **scope).hits]


# ── the capability ──────────────────────────────────────────────────────


def test_memory_extract_is_a_background_capability_with_memory_off() -> None:
    capability = next(c for c in builtin_capability_definitions() if c.id == EXTRACT_CAPABILITY)
    assert (capability.group_id, capability.group_label) == ("background", "Background")
    assert capability.owner_visibility == "owner"
    assert set(capability.allowed_boundaries) == {"local", "private_network", "mesh", "cloud"}
    # The closed schema is the call's response_format and code checks it; the
    # registry gate is off so a plain language profile (the LAN endpoint) can
    # be assigned.
    assert capability.requires.structured_output is False
    assert capability.output_kind == "memory_facts"
    assert memory_policy(EXTRACT_CAPABILITY).enabled is False
    assert EXTRACT_KINDS == {
        "meeting", "decision", "decision_record", "desk_decision", "action", "note",
        "thread", "artifact", "project_update",
    }


# ── the router: no engine, a wider engine, the assigned engine ──────────


class _FactsEngine:
    """The physical chat leaf the runner builds: it answers each prompt with
    the recorded real-model answer for it."""

    active_provider = "fixture"
    active_model = "qwen-fixture"

    def __init__(self) -> None:
        data = json.loads(FACTS_FIXTURE.read_text())
        self.answers = data["answers"]
        self.prompts: list[dict] = []
        self.fail = False

    def run_prompt(self, **kwargs):
        if self.fail:
            raise RuntimeError("the model stopped")
        self.prompts.append(kwargs)
        assert kwargs["response_format"]["json_schema"]["name"] == "memory_facts"
        return json.dumps(self.answers[fixture_key(kwargs)])


@pytest.fixture()
def routed(tmp_path: Path):
    db = Database(tmp_path / "routed.db")
    refs = build_corpus(db)
    broker = _configure(db)
    engine = _FactsEngine()
    broker.inference_runner._engine_factory = lambda revision, **_kwargs: engine
    return SimpleNamespace(db=db, refs=refs, broker=broker, engine=engine)


def test_no_engine_the_jobs_wait_and_recall_is_unchanged(routed) -> None:
    golden = json.loads(bench.GOLDEN.read_text())
    assert resolve_extractor(routed.broker, OWNER) is None
    report = memory_conductor.tick(routed.db, routed.broker)
    assert report["extract"] == {
        "engine": "", "sources": 0, "facts": 0, "calls": 0, "more": 0, "yielded": "", "error": "",
    }
    assert routed.engine.prompts == []
    # The jobs wait: every "yes" source is pending, none is stamped.
    pending = routed.db.memory_index.pending_extraction(EXTRACT_KINDS, extract_module.EXTRACTOR_VERSION)
    assert len(pending) == len(routed.refs)
    assert _counts(routed.db) == {table: 0 for table in FACT_TABLES}
    assert bench.keyword_snapshot(routed.db, routed.refs) == golden


def test_a_wider_assignment_is_never_used_for_extraction(routed) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    _profile(routed.db, "chat-model")
    InferenceAssignmentService(routed.db).set_assignment(OWNER, {
        "command_id": "assign-global", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "chat-model", "profile_revision": 1}],
    })
    assert resolve_extractor(routed.broker, OWNER) is None
    report = memory_conductor.tick(routed.db, routed.broker)
    assert report["extract"]["engine"] == "" and routed.engine.prompts == []


def test_the_assigned_engine_extracts_through_the_runner_with_a_receipt(routed, monkeypatch) -> None:
    _profile(routed.db, "facts-model", model="qwen-lan", boundary="private_network")
    _assign(routed.db, EXTRACT_CAPABILITY, ["facts-model"])
    monkeypatch.setattr(memory_conductor, "EXTRACT_CALLS_PER_PASS", 1000)
    extractor = resolve_extractor(routed.broker, OWNER)
    assert extractor is not None

    report = memory_conductor.tick(routed.db, routed.broker)

    extract = report["extract"]
    assert extract["error"] == "" and extract["sources"] == len(routed.refs)
    assert extract["calls"] == len(routed.engine.prompts) > 0
    stats = routed.db.memory_index.stats()
    assert stats["facts"] == extract["facts"] > 0 and stats["entities"] > 0
    # Nothing waits after the pass, and a second tick makes no engine call.
    assert routed.db.memory_index.pending_extraction(EXTRACT_KINDS, extract_module.EXTRACTOR_VERSION) == []
    calls = len(routed.engine.prompts)
    again = memory_conductor.tick(routed.db, routed.broker)
    assert again["extract"]["calls"] == 0 and len(routed.engine.prompts) == calls


def test_each_chunk_call_is_one_admitted_child_with_a_receipt(routed) -> None:
    _profile(routed.db, "facts-model", model="qwen-lan")
    _assign(routed.db, EXTRACT_CAPABILITY, ["facts-model"])
    extractor = resolve_extractor(routed.broker, memory_conductor._principal())
    ref = routed.refs["m-atlas-sync"]
    sweep(routed.db)
    done = extract_source(routed.db, extractor, ref)
    assert done["state"] == "written" and done["calls"] == 1
    receipt = routed.broker.store.receipt(extractor.last_operation_id)
    assert receipt["outcome"] == "succeeded"
    assert receipt["target_ref"] == f"deployment-revision:{extractor.revision_id}"
    assert receipt["actor_identity"] == "memory-conductor"


def test_an_engine_failure_ends_the_pass_and_charges_no_source(routed) -> None:
    golden = json.loads(bench.GOLDEN.read_text())
    _profile(routed.db, "facts-model", model="qwen-lan")
    _assign(routed.db, EXTRACT_CAPABILITY, ["facts-model"])
    routed.engine.fail = True
    report = memory_conductor.tick(routed.db, routed.broker)
    assert report["extract"]["error"] and report["extract"]["sources"] == 0
    assert _counts(routed.db) == {table: 0 for table in FACT_TABLES}  # no job row: no source charged
    assert bench.keyword_snapshot(routed.db, routed.refs) == golden
    routed.engine.fail = False
    memory_conductor.tick(routed.db, routed.broker)
    assert routed.db.memory_index.stats()["facts"] > 0


# ── idempotent; version bump; a killed job; rebuild ─────────────────────


def _bench_desk(tmp_path: Path):
    from tests.memory_bench.engines import FixtureExtractor

    db = Database(tmp_path / "facts.db")
    refs = build_corpus(db)
    sweep(db)
    return db, refs, FixtureExtractor(FACTS_FIXTURE)


def test_a_second_run_over_the_same_sources_makes_no_new_rows(tmp_path: Path) -> None:
    db, refs, engine = _bench_desk(tmp_path)
    first = extract_pending(db, engine)
    assert first["sources"] == len(refs) and first["facts"] > 0
    before = _rows(db)
    calls = engine.calls
    # The ledger says done: no engine call at all.
    second = extract_pending(db, engine)
    assert second["calls"] == 0 and engine.calls == calls
    assert _rows(db) == before
    # Forced: every job runs again over the same text.  Same ids, no new row.
    for ref in refs.values():
        assert extract_source(db, engine, ref)["state"] == "written"
    assert engine.calls > calls
    assert _counts(db) == {table: len(rows) for table, rows in before.items()}
    assert _rows(db, "memory_facts", "memory_fact_entities") == {
        table: before[table] for table in ("memory_facts", "memory_fact_entities")
    }


def test_a_version_bump_replaces_facts_with_no_gap_in_recall(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "bump.db")
    _note(db, "n-owner", "Cutover owner", "Dana owns the runbook for the cutover.")
    sweep(db)
    v1 = Scripted([("runbook", [F("Dana Whitfield owns the cutover runbook.", "Dana Whitfield",
                                  [("Dana Whitfield", "person")])])])
    assert extract_pending(db, v1)["sources"] == 1
    question = "what does Whitfield own"
    assert _refs(db, question) == ["note:n-owner"]  # found only by the entity walk
    assert db.memory.search(question).hits[0].retrieval_origin == "entity"

    bumped = extract_module.EXTRACTOR_VERSION + 1
    monkeypatch.setattr(extract_module, "EXTRACTOR_VERSION", bumped)
    seen_during: list[list[str]] = []
    v2 = Scripted([("runbook", [F("Dana Whitfield is the owner of the cutover runbook.", "Dana Whitfield",
                                  [("Dana Whitfield", "person")])])])
    # While the v2 engine runs, recall still has the v1 facts.
    v2.during = lambda _payload: seen_during.append(_refs(db, question))
    stats = extract_pending(db, v2)
    assert stats["sources"] == 1 and seen_during == [["note:n-owner"]]
    with db._connection() as conn:
        rows = conn.execute("SELECT text,extractor_version,state FROM memory_facts").fetchall()
        stamp = conn.execute(
            "SELECT extractor_version FROM memory_sources WHERE source_ref='note:n-owner'"
        ).fetchone()[0]
    assert [tuple(r) for r in rows] == [("Dana Whitfield is the owner of the cutover runbook.", bumped, "live")]
    assert stamp == bumped
    assert _refs(db, question) == ["note:n-owner"]


def test_a_job_killed_inside_its_transaction_leaves_recall_unchanged(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.memory import entities

    db = Database(tmp_path / "kill.db")
    _note(db, "n-a", "Atlas owner", "Dana owns Atlas.")
    _note(db, "n-b", "Harbor owner", "Lee owns Harbor.")
    sweep(db)
    engine = Scripted([
        ("Dana owns", [F("Dana Whitfield owns Atlas.", "Dana Whitfield", [("Dana Whitfield", "person"), ("Atlas", "project")])]),
        ("Lee owns", [
            F("Lee Moreau owns Harbor.", "Lee Moreau", [("Lee Moreau", "person")]),
            F("Harbor ships in May.", "Harbor", [("Harbor", "project")]),
        ]),
    ])
    extract_source(db, engine, "note:n-a")
    before = _rows(db)
    before_ledger = _rows(db, "memory_sources")
    answer = db.memory.search("Whitfield Moreau").to_dict()

    real = entities.resolve
    calls = {"n": 0}

    def dies_on_the_second(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("the hub stopped")
        return real(*args, **kwargs)

    monkeypatch.setattr(entities, "resolve", dies_on_the_second)
    with pytest.raises(RuntimeError):
        extract_source(db, engine, "note:n-b")
    assert calls["n"] == 2  # the first fact and its entity were written inside the transaction
    assert _rows(db) == before and _rows(db, "memory_sources") == before_ledger
    assert db.memory.search("Whitfield Moreau").to_dict() == answer


def test_rebuild_regenerates_the_same_facts(tmp_path: Path) -> None:
    db, refs, engine = _bench_desk(tmp_path)
    extract_pending(db, engine)
    before = _rows(db, "memory_facts", "memory_entities", "memory_fact_entities")
    answers = {q: _refs(db, q) for q in ("what does Dana owe on Atlas", "what did Lee report")}
    counts = rebuild(db, extractor=engine)
    assert counts["facts"] > 0 and counts["extracted"] == len(refs)
    assert _rows(db, "memory_facts", "memory_entities", "memory_fact_entities") == before
    assert {q: _refs(db, q) for q in answers} == answers
    # Without an engine the rebuild leaves the facts to the hub's next pass.
    counts = rebuild(db)
    assert counts["facts"] == 0 and counts["entities"] == 0


# ── entity resolution ───────────────────────────────────────────────────


def test_john_smith_and_jane_smith_stay_two_entities(tmp_path: Path) -> None:
    db = Database(tmp_path / "smith.db")
    _note(db, "n-john", "Cutover", "John Smith owns the Atlas cutover.")
    _note(db, "n-jane", "Budget", "Jane Smith reviews the Atlas budget.")
    _note(db, "n-dana1", "Runbook", "Dana Lee writes the Atlas runbook.")
    _note(db, "n-dana2", "Rollback", "Dana tests the Atlas rollback.")
    sweep(db)
    engine = Scripted([
        ("John Smith", [F("John Smith owns the Atlas cutover.", "John Smith", [("John Smith", "person"), ("Atlas", "project")])]),
        ("Jane Smith", [F("Jane Smith reviews the Atlas budget.", "Jane Smith", [("Jane Smith", "person"), ("Atlas", "project")])]),
        ("Dana Lee", [F("Dana Lee writes the Atlas runbook.", "Dana Lee", [("Dana Lee", "person"), ("Atlas", "project")])]),
        ("Dana tests", [F("Dana tests the Atlas rollback.", "Dana", [("Dana", "person"), ("Atlas", "project")])]),
    ])
    for ref in ("note:n-john", "note:n-jane", "note:n-dana1", "note:n-dana2"):
        extract_source(db, engine, ref)
    with db._connection() as conn:
        people = {
            str(r["name"]): json.loads(r["aliases_json"])
            for r in conn.execute("SELECT name,aliases_json FROM memory_entities WHERE kind='person'")
        }
    # Same project, same week, a near name: still two people (the token guard).
    assert set(people) == {"John Smith", "Jane Smith", "Dana Lee"}
    # A one-word name with shared neighbours and time joins the full name.
    assert people["Dana Lee"] == ["Dana"]
    assert token_guard("john smith", "jane smith") is False
    assert token_guard("j. smith", "john smith") is True
    assert _refs(db, "what does Jane Smith review")[0] == "note:n-jane"


# ── the entity walk ─────────────────────────────────────────────────────


def test_the_entity_walk_keeps_scope_and_names_the_message(tmp_path: Path) -> None:
    db = Database(tmp_path / "walk.db")
    db.projects.create_project(project_id="atlas", name="Atlas")
    db.projects.create_project(project_id="harbor", name="Harbor")
    _note(db, "n-in", "Plan", "The rollout plan is ready.")
    db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-in")
    _note(db, "n-out", "Other", "The pricing page is ready.")
    db.project_relationships.upsert(project_id="harbor", resource_ref="note:n-out")
    thread = db.threads.create_thread(title="Chat")
    first = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(first.id, kind="text", text="Lunch is at noon.")
    second = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(second.id, kind="text", text="The rollout needs a sign-off.")
    sweep(db)
    engine = Scripted([
        ("rollout plan", [F("Quentin Ashby wrote the rollout plan.", "Quentin Ashby", [("Quentin Ashby", "person")])]),
        ("pricing page", [F("Quentin Ashby owns the pricing page.", "Quentin Ashby", [("Quentin Ashby", "person")])]),
        ("sign-off", [F("Quentin Ashby must sign off the rollout.", "Quentin Ashby", [("Quentin Ashby", "person")])]),
    ])
    extract_pending(db, engine)
    everything = db.memory.search("what is Ashby doing")
    assert {hit.source_ref for hit in everything.hits} == {
        "note:n-in", "note:n-out", f"thread:{thread.id}#{second.id}",
    }
    assert all(hit.retrieval_origin == "entity" for hit in everything.hits)
    assert everything.fusion["retrievers"] == ["entity"]
    assert everything.hits[0].snippet.startswith("Quentin Ashby")
    assert _refs(db, "what is Ashby doing", project_id="atlas") == ["note:n-in"]
    assert _refs(db, "what is Ashby doing", kinds="thread") == [f"thread:{thread.id}#{second.id}"]
    assert "note:n-in" not in _refs(db, "what is Ashby doing", exclude_refs=["note:n-in"])
    # A question that names no entity: the answer is the keyword answer.
    assert db.memory.search("pricing").fusion is None


# ── custody ─────────────────────────────────────────────────────────────


def test_people_store_content_never_becomes_a_fact_or_an_entity(tmp_path: Path) -> None:
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService

    owner = Principal(PrincipalKind.OWNER, "memory-slice3-owner")
    db = Database(tmp_path / "holdspeak.db")
    store = EncryptedPeopleStore(tmp_path / "people-private" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    relationship = people.create_relationship(owner, {"display_name": "Zorvane Quillfeather"})
    note = people.create_note(owner, relationship["id"], {"topic": "Growth", "body": "PEOPLESENTINEL wants a promotion."})
    _meeting(db, "m-plain", [("Dana", "I will send the Atlas plan on Friday.")], title="Atlas sync")

    engine = Scripted(echo=True)  # every text it is given becomes a fact and an entity
    counts = rebuild(db, extractor=engine)
    assert counts["facts"] == 1 and engine.calls == 1
    held = _memory_text(db)
    assert "Atlas plan" in held  # the plain source is memory
    for word in ("PEOPLESENTINEL", "Quillfeather", note["id"], relationship["id"]):
        assert word not in engine.received()
        assert word not in held


def test_a_secret_never_reaches_a_fact_an_entity_or_the_engine(tmp_path: Path) -> None:
    db = Database(tmp_path / "secret.db")
    secret = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2"
    _note(db, "n-key", "Deploy key", f"The deploy uses token={secret} for Atlas.")
    sweep(db)
    engine = Scripted([("Deploy key", [
        F(f"The Atlas deploy uses the key {secret}.", "Atlas deploy",
          [("Atlas", "project"), (secret, "system")], obj=secret),
    ])])
    extract_pending(db, engine)
    assert secret not in engine.received() and REDACTED in engine.received()
    held = _memory_text(db)
    assert secret not in held
    with db._connection() as conn:
        text, obj = conn.execute("SELECT text,object_text FROM memory_facts").fetchone()
        names = [str(r[0]) for r in conn.execute("SELECT name FROM memory_entities")]
    assert REDACTED in text and REDACTED in obj
    assert names == ["Atlas"]  # a name that holds a secret is no entity


def test_a_source_refused_since_the_sweep_never_reaches_the_engine(tmp_path: Path) -> None:
    db = Database(tmp_path / "refused.db")
    thread = db.threads.create_thread(title="Planning")
    message = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(message.id, kind="text", text="The REFUSEDWORD budget moves to May.")
    _meeting(db, "m-parked", [("Lee", "The PARKEDWORD launch slips a week.")])
    _meeting(db, "m-kept", [("Ana", "The KEPTWORD review is on Monday.")])
    sweep(db)
    # After the sweep and before the job: the thread is deleted and the
    # meeting is parked.  The index still holds both.
    assert db.threads.soft_delete(thread.id)
    db.meetings.delete_meeting("m-parked")  # the product parks; it never deletes
    engine = Scripted(echo=True)
    stats = extract_pending(db, engine)
    assert stats["sources"] == 1 and stats["skipped"] == 2
    received = engine.received()
    assert "KEPTWORD" in received
    assert "REFUSEDWORD" not in received and "PARKEDWORD" not in received
    derived = repr(_rows(db, "memory_facts", "memory_entities"))
    assert "REFUSEDWORD" not in derived and "PARKEDWORD" not in derived
    # Neither is stamped: the next sweep removes their chunks.
    with db._connection() as conn:
        stamped = {str(r[0]) for r in conn.execute(
            "SELECT source_ref FROM memory_sources WHERE extracted_sha IS NOT NULL")}
    assert stamped == {"meeting:m-kept"}


def test_a_source_that_leaves_takes_its_facts_and_its_only_names(tmp_path: Path) -> None:
    db = Database(tmp_path / "leave.db")
    _meeting(db, "m-1", [("Lee", "Odalys Brennick will ship the beta.")])
    _meeting(db, "m-2", [("Ana", "Atlas ships in May.")])
    sweep(db)
    engine = Scripted([
        ("Odalys", [F("Odalys Brennick will ship the Atlas beta.", "Odalys Brennick",
                      [("Odalys Brennick", "person"), ("Atlas", "project")])]),
        ("ships in May", [F("Atlas ships in May.", "Atlas", [("Atlas", "project")])]),
    ])
    extract_pending(db, engine)
    assert _refs(db, "what will Brennick ship") == ["meeting:m-1"]
    db.meetings.delete_meeting("m-1")  # parked
    # Before the next sweep recall already refuses it (admission now).
    assert "meeting:m-1" not in _refs(db, "what will Brennick ship")
    sweep(db)
    held = repr(_rows(db, "memory_facts", "memory_entities", "memory_fact_entities"))
    assert "Brennick" not in held and "m-1" not in held
    assert "Atlas" in held  # still named by the kept meeting


# ── load: yield, bound, order, back-off ──────────────────────────────────


def test_extraction_yields_to_a_live_meeting_and_a_live_local_call(routed, monkeypatch) -> None:
    from holdspeak.kernel.local_runtime_lease import (
        acquire_local_runtime_lease, release_local_runtime_lease,
    )

    _profile(routed.db, "facts-model", model="qwen-lan")
    _assign(routed.db, EXTRACT_CAPABILITY, ["facts-model"])
    monkeypatch.setattr(memory_conductor, "_live_check", lambda: "a meeting is recording")
    report = memory_conductor.tick(routed.db, routed.broker)
    assert report["extract"]["yielded"] == "a meeting is recording"
    assert report["extract"]["more"] == 1 and routed.engine.prompts == []

    monkeypatch.setattr(memory_conductor, "_live_check", None)
    lease = acquire_local_runtime_lease(routed.db, operation_id="op-live-chat", deployment_revision_id="r")
    local = SimpleNamespace(boundary="local", operation_ids=[])
    remote = SimpleNamespace(boundary="private_network", operation_ids=[])
    assert memory_conductor.live_work(routed.db, local) == "a local model call is live"
    assert memory_conductor.live_work(routed.db, remote) == ""
    release_local_runtime_lease(routed.db, lease)
    assert memory_conductor.live_work(routed.db, local) == "a local model call ended just now"
    # The engine's own call is not a reason to wait.
    assert memory_conductor.live_work(routed.db, SimpleNamespace(boundary="local", operation_ids=["op-live-chat"])) == ""


def test_a_pass_is_bounded_and_the_backlog_runs_oldest_last(tmp_path: Path) -> None:
    db, refs, engine = _bench_desk(tmp_path)
    stats = extract_pending(db, engine, max_calls=3)
    # The bound is checked before EVERY call: exactly 3 calls.
    assert stats["more"] == 1 and stats["calls"] == 3 == engine.calls
    assert 0 < stats["sources"] < len(refs)
    with db._connection() as conn:
        done = [str(r[0]) for r in conn.execute(
            "SELECT source_ref FROM memory_sources WHERE extracted_sha IS NOT NULL")]
        newest = [str(r[0]) for r in conn.execute(
            "SELECT source_ref FROM memory_sources ORDER BY COALESCE(occurred_at,'') DESC,source_ref")]
    assert sorted(done) == sorted(newest[: stats["sources"]])
    assert stats["calls"] == engine.calls


def test_a_bad_answer_backs_off_and_stops_after_six_tries(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "bad.db")
    _note(db, "n-bad", "Bad", "A text the engine cannot read.")
    sweep(db)
    engine = Scripted()
    engine.answer = {"not": "the schema"}
    with pytest.raises(ExtractionOutputError):
        extract_source(db, engine, "note:n-bad")
    stats = extract_pending(db, engine)
    assert stats["failed"] == 1
    with db._connection() as conn:
        job = dict(conn.execute("SELECT status,attempts,next_attempt_at FROM memory_jobs").fetchone())
    assert job["status"] == "queued" and job["attempts"] == 1 and job["next_attempt_at"]
    # Waiting for its retry time: not pending now.
    assert extract_pending(db, engine)["failed"] == 0
    far = "2999-01-01T00:00:00+00:00"
    index = db.memory_index
    version = extract_module.EXTRACTOR_VERSION
    for _ in range(5):
        for ref, sha in index.pending_extraction(EXTRACT_KINDS, version, now=far):
            index.record_job_failure(kind="extract", target=ref, input_sha=sha, version=version, error="bad",
                                     boundary="local", max_attempts=6, delay=lambda n: 0)
    with db._connection() as conn:
        assert dict(conn.execute("SELECT status,attempts FROM memory_jobs").fetchone()) == {"status": "failed", "attempts": 6}
    assert index.pending_extraction(EXTRACT_KINDS, version, now=far) == []
    # The text changes: the job is new, and a good answer clears the row.
    _note(db, "n-bad", "Bad", "A text the engine can read now.")
    sweep(db)
    engine.answer = {"facts": [F("The text is readable.", "Text", [("Readable text", "topic")])]}
    assert extract_pending(db, engine)["sources"] == 1
    assert _counts(db)["memory_jobs"] == 0


# ── review round 1 (Astra, PR #839): the five defects, each fenced ───────


def _brennick_note(db: Database) -> Scripted:
    _note(db, "n", "Plan", "Odalys Brennick owns the Atlas launch.")
    sweep(db)
    engine = Scripted([
        ("Brennick", [F("Odalys Brennick owns the Atlas launch.", "Odalys Brennick",
                        [("Odalys Brennick", "person"), ("Atlas", "project")])]),
        ("Moreau", [F("Lee Moreau owns the Harbor budget.", "Lee Moreau",
                      [("Lee Moreau", "person"), ("Harbor", "project")])]),
    ])
    assert extract_pending(db, engine)["sources"] == 1
    assert _refs(db, "what does Brennick own") == ["note:n"]
    return engine


def _entity_hits(db: Database, query: str) -> list[tuple[str, str]]:
    """What the entity walk returns, and a check that no search hit at all
    shows the withdrawn sentence."""
    from holdspeak.db.memory import _VALID_KINDS

    rows = db.memory._entity_rows(
        query, selected=tuple(_VALID_KINDS), project=None, start=None, end=None, excluded=set()
    ) or []
    walked = [(row["source_ref"], row["snippet"]) for row in rows]
    if not walked:
        assert all("Brennick" not in hit.snippet for hit in db.memory.search(query).hits)
    return walked


def test_withdrawn_text_never_serves_through_a_fact(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "withdrawn.db")
    _brennick_note(db)
    _note(db, "n", "Plan", "Lee Moreau owns the Harbor budget.")
    # Before the sweep, after it, and while the new text is read: the old
    # sentence is never an answer.
    assert _entity_hits(db, "what does Brennick own") == []
    sweep(db)
    assert _entity_hits(db, "what does Brennick own") == []
    engine = Scripted([("Moreau", [F("Lee Moreau owns the Harbor budget.", "Lee Moreau",
                                     [("Lee Moreau", "person")])])])
    during: list[list] = []
    engine.during = lambda _payload: during.append(_entity_hits(db, "what does Brennick own"))
    assert extract_pending(db, engine)["sources"] == 1
    assert during == [[]]
    assert _entity_hits(db, "what does Brennick own") == []
    assert _refs(db, "what does Moreau own") == ["note:n"]


def test_an_edit_while_the_engine_reads_is_never_committed(tmp_path: Path) -> None:
    db = Database(tmp_path / "edit-during.db")
    _note(db, "n", "Plan", "Odalys Brennick owns the launch.")
    sweep(db)
    engine = Scripted([("Brennick", [F("Odalys Brennick owns the launch.", "Odalys Brennick",
                                       [("Odalys Brennick", "person")])])])
    engine.during = lambda _payload: _note(db, "n", "Plan", "Lee Moreau owns the budget.")
    done = extract_source(db, engine, "note:n")
    assert done["state"] == "skipped" and done["calls"] == 1
    assert _counts(db)["memory_facts"] == 0
    with db._connection() as conn:
        assert conn.execute(
            "SELECT extracted_sha FROM memory_sources WHERE source_ref='note:n'"
        ).fetchone()[0] is None
    assert _entity_hits(db, "what does Brennick own") == []


@pytest.mark.parametrize("change", ["delete_part", "made_sensitive"])
def test_a_withdrawn_message_never_serves_and_its_anchor_never_moves(tmp_path: Path, change: str) -> None:
    db = Database(tmp_path / f"{change}.db")
    thread = db.threads.create_thread(title="Planning")
    lunch = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(lunch.id, kind="text", text="Lunch is at noon.")
    secret = db.threads.append_message(thread.id, role="user")
    part = db.threads.append_part(secret.id, kind="text", text="Odalys Brennick owns the confidential launch.")
    sweep(db)
    engine = Scripted([
        ("Brennick", [F("Odalys Brennick owns the confidential launch.", "Odalys Brennick",
                        [("Odalys Brennick", "person")])]),
        ("Lunch", [F("Lunch is at noon.", "Lunch", [("Lunch", "topic")])]),
    ])
    extract_pending(db, engine)
    assert _entity_hits(db, "what does Brennick own") == [
        (f"thread:{thread.id}#{secret.id}", "Odalys Brennick owns the confidential launch.")
    ]
    if change == "made_sensitive":
        db.threads.append_part(secret.id, kind="text", text=part.text, sensitive=True)
    db.threads.delete_part(part.id)
    assert _entity_hits(db, "what does Brennick own") == []          # before the sweep
    sweep(db)
    assert _entity_hits(db, "what does Brennick own") == []          # after it
    with db._connection() as conn:
        anchor = conn.execute(
            "SELECT anchor FROM memory_facts WHERE text LIKE 'Odalys Brennick%'"
        ).fetchone()[0]
    assert anchor == secret.id  # the stored fact keeps its own message; it never takes the lunch one
    extract_pending(db, engine)
    assert _entity_hits(db, "what does Brennick own") == []          # after re-extraction
    assert "Brennick" not in repr(_rows(db, "memory_facts", "memory_entities"))


def test_unchanged_text_keeps_its_facts_through_a_version_bump(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "keep.db")
    engine = _brennick_note(db)
    monkeypatch.setattr(extract_module, "EXTRACTOR_VERSION", extract_module.EXTRACTOR_VERSION + 1)
    during: list[list] = []
    engine.during = lambda _payload: during.append(_refs(db, "what does Brennick own"))
    assert extract_pending(db, engine)["sources"] == 1
    assert during == [["note:n"]]


CHAINS = {
    "smith": ["John Smith", "J. Smith", "Jane Smith"],
    "dana": ["Dana Lee", "Dana", "Dana Kim"],
}


@pytest.mark.parametrize("chain", sorted(CHAINS))
@pytest.mark.parametrize("order", list(__import__("itertools").permutations(range(3))))
def test_an_alias_chain_never_joins_two_full_names(tmp_path: Path, chain: str, order) -> None:
    db = Database(tmp_path / "chain.db")
    names = [CHAINS[chain][index] for index in order]
    rules = []
    for position, name in enumerate(names):
        _note(db, f"n{position}", f"Task {position}", f"{name} owns Atlas task {position}.")
        rules.append((f"Atlas task {position}.", [F(f"{name} owns Atlas task {position}.", name,
                                                    [(name, "person"), ("Atlas", "project")])]))
    sweep(db)
    engine = Scripted(rules)
    for position in range(3):
        extract_source(db, engine, f"note:n{position}")
    with db._connection() as conn:
        people = [
            {fold_key(str(r["name"]))} | {fold_key(a) for a in json.loads(r["aliases_json"])}
            for r in conn.execute("SELECT name,aliases_json FROM memory_entities WHERE kind='person'")
        ]
    full = [fold_key(name) for name in CHAINS[chain] if len(name.split()) > 1 and "." not in name]
    for names_of_one in people:
        assert not set(full) <= names_of_one, (names, people)


def fold_key(name: str) -> str:
    from holdspeak.memory.entities import fold

    return fold(name)


def test_the_call_budget_and_a_live_meeting_are_checked_before_every_call(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "per-call.db")
    thread = db.threads.create_thread(title="Long")
    for index in range(30):
        message = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(message.id, kind="text", text=f"Step {index} of the Atlas plan is ready.")
    sweep(db)
    engine = Scripted()
    # The budget: 24 calls, then the source stops half way and goes on later.
    first = extract_pending(db, engine, max_calls=24)
    assert first["calls"] == 24 == engine.calls and first["more"] == 1 and first["sources"] == 0
    second = extract_pending(db, engine, max_calls=24)
    assert second["calls"] == 6 and second["sources"] == 1 and engine.calls == 30

    # A meeting starts after the first call, inside one source: the job
    # stops before the next call, not at the next source.
    thread2 = db.threads.create_thread(title="Long 2")
    for index in range(30):
        message = db.threads.append_message(thread2.id, role="user")
        db.threads.append_part(message.id, kind="text", text=f"Item {index} of the Harbor plan.")
    sweep(db)
    live = {"on": False}
    engine2 = Scripted()
    engine2.during = lambda _payload: live.update(on=True)
    stats = extract_pending(db, engine2, yield_check=lambda: "a meeting is recording" if live["on"] else "")
    assert engine2.calls == 1 and stats["calls"] == 1 and stats["yielded"] == "a meeting is recording"
    live["on"] = False
    engine2.during = None
    extract_pending(db, engine2)
    # It went on from the next chunk: no chunk was read twice.
    prompts = [payload["user_prompt"] for payload in engine2.payloads]
    assert len(prompts) == len(set(prompts)) == 30


def test_extraction_yields_to_a_live_chat_turn_on_the_same_lan_model(tmp_path: Path) -> None:
    import asyncio

    from holdspeak.kernel.inference_stream import Delta
    from holdspeak.services.thread_service import ThreadService
    from tests.unit.test_phase143_inference_assignments import _result_claim

    db = Database(tmp_path / "lan.db")
    broker = _configure(db)
    _profile(db, "shared-lan", model="same-endpoint-model", boundary="private_network",
             claims=("language", _result_claim("chat.turn")))
    _assign(db, EXTRACT_CAPABILITY, ["shared-lan"])
    _assign(db, "chat.turn", ["shared-lan"])
    _note(db, "n", "Plan", "Dana owns Atlas.")
    sweep(db)
    started, release = threading.Event(), threading.Event()
    extract_calls: list[bool] = []

    class Engine:
        active_provider = "fixture"
        active_model = "same-endpoint-model"

        def run_prompt_stream(self, **_kwargs):
            started.set()
            assert release.wait(15)
            yield Delta(kind="text", text="Hello.")
            yield Delta(kind="done")

        def run_prompt(self, **_kwargs):
            extract_calls.append(started.is_set() and not release.is_set())
            return '{"facts": []}'

    broker.inference_runner._engine_factory = lambda revision, **_kwargs: Engine()
    done = threading.Event()
    service = ThreadService(db, broadcast=lambda kind, _data: done.set() if kind == "thread_turn_done" else None,
                            broker=broker)
    thread = db.threads.create_thread(title="Live chat")
    try:
        asyncio.run(service.start_turn(OWNER, thread.id, "Write a short greeting."))
        assert started.wait(10)
        extractor = resolve_extractor(broker, OWNER)
        assert extractor is not None and extractor.boundary == "private_network"
        assert memory_conductor.live_work(db, extractor) == "a model call on the same engine is live"
        report = memory_conductor._extract_step(db, broker, None)
        assert report["yielded"] == "a model call on the same engine is live"
        assert report["calls"] == 0 and extract_calls == []
    finally:
        release.set()
        done.wait(10)
    # The chat ended: the extraction runs.
    report = memory_conductor._extract_step(db, broker, None)
    assert report["sources"] == 1 and extract_calls == [False]


def test_every_attempted_call_counts_against_the_budget(tmp_path: Path) -> None:
    db = Database(tmp_path / "bad-budget.db")
    for index in range(30):
        _note(db, f"n{index}", f"Note {index}", f"Fact number {index} about Atlas.")
    sweep(db)
    engine = Scripted()
    engine.answer = {"items": []}  # not the schema
    stats = extract_pending(db, engine, max_calls=24)
    assert engine.calls == 24 and stats["calls"] == 24 and stats["failed"] == 24 and stats["more"] == 1


def test_one_malformed_entry_fails_the_answer_and_the_old_facts_stay(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "malformed.db")
    _brennick_note(db)
    before = _rows(db, "memory_facts", "memory_entities", "memory_fact_entities")
    monkeypatch.setattr(extract_module, "EXTRACTOR_VERSION", extract_module.EXTRACTOR_VERSION + 1)
    engine = Scripted()
    good = F("Odalys Brennick owns the Atlas launch.", "Odalys Brennick", [("Odalys Brennick", "person")])
    for bad in (
        {"facts": [{"txet": "Odalys Brennick owns the Atlas launch."}]},
        {"facts": [good, {**good, "kind": "rumour"}]},
        {"facts": [good, {**good, "entities": [{"name": "Atlas"}]}]},
        {"facts": [good, {**good, "confidence": "high"}]},
        {"facts": [good], "notes": "extra"},
    ):
        engine.answer = bad
        with pytest.raises(ExtractionOutputError):
            extract_source(db, engine, "note:n")
    stats = extract_pending(db, engine)
    assert stats["failed"] == 1 and stats["sources"] == 0
    assert _rows(db, "memory_facts", "memory_entities", "memory_fact_entities") == before
    assert _refs(db, "what does Brennick own") == ["note:n"]
    with db._connection() as conn:
        assert dict(conn.execute("SELECT status,attempts FROM memory_jobs").fetchone()) == {
            "status": "queued", "attempts": 1,
        }


def test_a_short_name_two_full_names_could_take_is_its_own_entity(tmp_path: Path) -> None:
    db = Database(tmp_path / "ambiguous.db")
    texts = ["Dana Lee owns Atlas task 0.", "Dana Kim owns Atlas task 1.", "Dana owns Atlas task 2."]
    rules = []
    for position, text in enumerate(texts):
        _note(db, f"n{position}", f"Task {position}", text)
        name = text.split(" owns")[0]
        rules.append((f"Atlas task {position}.", [F(text, name, [(name, "person"), ("Atlas", "project")])]))
    sweep(db)
    engine = Scripted(rules)
    for position in range(3):
        extract_source(db, engine, f"note:n{position}")
    with db._connection() as conn:
        people = {str(r["name"]): json.loads(r["aliases_json"])
                  for r in conn.execute("SELECT name,aliases_json FROM memory_entities WHERE kind='person'")}
    assert people == {"Dana Lee": [], "Dana Kim": [], "Dana": []}


# ── a day with no month is the next such day (EXTRACTOR_VERSION 2) ─────


def _dated(text: str, start: Optional[str], end: Optional[str] = None) -> dict:
    return {"text": text, "occurred_start": start, "occurred_end": end}


def test_the_prompt_says_a_day_with_no_month_is_the_next_such_day() -> None:
    prompt = extract_module.SYSTEM_PROMPT
    assert "next such day on or after the date of the source" in prompt
    assert "never before the date of the source" in prompt
    assert extract_module.EXTRACTOR_VERSION >= 2


def test_a_past_day_with_no_month_is_stored_as_the_next_such_day(tmp_path: Path) -> None:
    """The model gives 2026-09-09 for "the ninth" in a meeting of 2026-09-14.
    The stored fact (text and dates) says 2026-10-09."""
    db = Database(tmp_path / "day.db")
    _meeting(db, "m-leave", [("Remote", "My leave starts on the ninth.")], title="1:1 with Rafael Okonkwo")
    sweep(db)
    wrong = {**F("Rafael Okonkwo's leave starts on 2026-09-09.", "Rafael Okonkwo",
                 [("Rafael Okonkwo", "person")], kind="event", start="2026-09-09")}
    extract_pending(db, Scripted([("ninth", [wrong])]))
    with db._connection() as conn:
        rows = [tuple(r) for r in conn.execute("SELECT text,occurred_start FROM memory_facts")]
    assert rows == [("Rafael Okonkwo's leave starts on 2026-10-09.", "2026-10-09")]


@pytest.mark.parametrize("fact,chunk,expected", [
    # Moved: a thing still to come, a bare day, a past date in the source month.
    (_dated("Rafael's leave starts on 2026-09-09.", "2026-09-09"), "My leave starts on the ninth.",
     _dated("Rafael's leave starts on 2026-10-09.", "2026-10-09")),
    (_dated("Beatriz requires the numbers by 2026-09-15.", None), "I need the numbers by the 15th.",
     _dated("Beatriz requires the numbers by 2026-10-15.", None)),
    (_dated("Tomasz will ship the batch on 2026-09-20.", "2026-09-22T09:00:00", "2026-09-20"),
     "It ships on the twentieth.",
     _dated("Tomasz will ship the batch on 2026-10-20.", "2026-09-22T09:00:00", "2026-10-20")),
    # The end moves with a moved start ("from the ninth for three weeks").
    (_dated("Rafael will be away from 2026-09-09.", "2026-09-09", "2026-09-30"), "Away from the ninth for three weeks.",
     _dated("Rafael will be away from 2026-10-09.", "2026-10-09", "2026-10-30")),
    # "the first" alone is a day.
    (_dated("The report is due 2026-09-01.", "2026-09-01"), "It is due on the first.",
     _dated("The report is due 2026-10-01.", "2026-10-01")),
])
def test_the_guard_moves_a_past_day_that_is_still_to_come(fact: dict, chunk: str, expected: dict) -> None:
    assert extract_module.roll_past_days([fact], chunk, "2026-09-22T16:00:00") == [expected]


@pytest.mark.parametrize("fact,chunk", [
    # A past event: the fact's words do not say "still to come".
    (_dated("Rafael finished the migration on 2026-09-09.", "2026-09-09"), "I finished it on the ninth."),
    # The chunk names the month: the model read it as said.
    (_dated("The freeze will start on 2026-09-09.", "2026-09-09"), "The freeze starts on the ninth of September."),
    (_dated("The freeze will start on 2026-09-09.", "2026-09-09"), "The freeze starts September the ninth."),
    # No bare day in the chunk, or another day than the one the chunk says.
    (_dated("The freeze will start on 2026-09-09.", "2026-09-09"), "The freeze starts soon."),
    (_dated("The freeze will start on 2026-09-08.", "2026-09-08"), "The freeze starts on the ninth."),
    # "the first week" is not a day.
    (_dated("Ana will pair with Lee on 2026-09-01.", "2026-09-01"), "Ana pairs with Lee in the first week."),
    # A date in another month than the source's, or not before the source.
    (_dated("The freeze will start on 2026-08-09.", "2026-08-09"), "The freeze starts on the ninth."),
    (_dated("The freeze will start on 2026-09-29.", "2026-09-29"), "The freeze starts on the twenty-ninth."),
])
def test_the_guard_never_moves_a_date_it_cannot_prove_wrong(fact: dict, chunk: str) -> None:
    assert extract_module.roll_past_days([fact], chunk, "2026-09-22T16:00:00") == [fact]


def test_a_day_the_next_month_does_not_have_goes_to_the_month_after() -> None:
    fact = _dated("The audit will start on 2027-01-30.", "2027-01-30")
    assert extract_module.roll_past_days([fact], "It starts on the thirtieth.", "2027-01-31") == [
        _dated("The audit will start on 2027-03-30.", "2027-03-30")
    ]
