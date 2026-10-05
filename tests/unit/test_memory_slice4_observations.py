"""Memory slice 4: observations, beliefs with evidence and history
(docs/internal/MEMORY-DESIGN.md §1, §2, §3.2, §3.3, §5, §8 row 4).

Every source is written by its real producer (the meeting, note, thread and
project repositories, the People service).  Facts come through the real
extract path with a scripted extractor.  The consolidate engine is a
deterministic rule engine that reads the real prompt: facts are written as
"<topic> is <value>.", and it answers by the rule below.  The code under test
is never doubled.  The router tests use the real router, assignment service
and runner; only the physical model leaf is replaced.
"""
from __future__ import annotations

import json
import re
import sqlite3
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
from holdspeak.memory import consolidate as consolidate_module
from holdspeak.memory.consolidate import (
    CONSOLIDATE_CAPABILITY, ConsolidationOutputError, ConsolidationScopeError, consolidate_batch,
    consolidate_pending, desk_ref, pending_batches, read_observations, refresh_observations,
    resolve_consolidator,
)
from holdspeak.memory.defense import REDACTED
from holdspeak.memory.extract import (
    EXTRACT_CAPABILITY, EXTRACT_KINDS, CallBudget, ExtractionOutputError, extract_pending,
    extract_source,
)
from holdspeak.memory.retain import sweep

from tests.memory_bench import bench
from tests.memory_bench.corpus import build_corpus
from tests.unit.test_memory_slice3_facts import F, Scripted, _memory_text, _note
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign

OBS_TABLES = ("memory_observations", "memory_observation_evidence", "memory_observation_history")


# ── the deterministic consolidate engine ────────────────────────────────

_FACT_LINE = re.compile(r"^(f\d+) \([^)]*\): (.*)$")
_OBS_LINE = re.compile(r"^(o\d+) \[(\w+)\]: (.*)$")


def _topic(text: str) -> tuple[str, str]:
    head, _, value = text.rstrip(".").partition(" is ")
    return head.strip().casefold(), value.strip()


class Rules:
    """Reads the real prompt.  For each topic in the facts: an observation
    with the same topic and value -> ``supports``; the same topic and another
    value -> ``on_change`` (supersedes by default); no observation of the
    topic -> one create.  Every fact of a topic goes in one entry."""

    boundary = "local"
    model_id = "rules"

    def __init__(self, on_change: str = "supersedes") -> None:
        self.on_change = on_change
        self.payloads: list[dict] = []
        self.calls = 0
        self.answer: Any = None
        self.during: Optional[Callable[[dict], None]] = None
        self.echo = False

    def parse(self, payload: dict) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
        facts: dict[str, str] = {}
        observations: dict[str, tuple[str, str]] = {}
        for line in payload["user_prompt"].splitlines():
            if (m := _FACT_LINE.match(line)):
                facts[m.group(1)] = m.group(2)
            elif (m := _OBS_LINE.match(line)):
                observations[m.group(1)] = (m.group(2), m.group(3))
        return facts, observations

    def consolidate(self, payload: dict) -> Any:
        self.calls += 1
        self.payloads.append(payload)
        if self.during is not None:
            self.during(payload)
        if self.answer is not None:
            return self.answer(payload) if callable(self.answer) else self.answer
        facts, observations = self.parse(payload)
        if self.echo:
            return {"creates": [{"text": text, "fact_ids": [label], "reason": "echo"}
                                for label, text in facts.items()], "updates": []}
        by_topic: dict[str, list[str]] = {}
        for label, text in facts.items():
            by_topic.setdefault(_topic(text)[0], []).append(label)
        creates, updates = [], []
        for topic, labels in by_topic.items():
            value = _topic(facts[labels[-1]])[1]
            match = next((o for o, (_s, t) in observations.items() if _topic(t)[0] == topic), None)
            if match is None:
                creates.append({"text": facts[labels[-1]], "fact_ids": labels, "reason": "new"})
            elif _topic(observations[match][1])[1] == value:
                updates.append({"observation_id": match, "relation": "supports", "text": "",
                                "fact_ids": labels, "reason": "same"})
            else:
                updates.append({"observation_id": match, "relation": self.on_change,
                                "text": facts[labels[-1]], "fact_ids": labels, "reason": "changed"})
        return {"creates": creates, "updates": updates}

    def received(self) -> str:
        return "\n".join(p["user_prompt"] for p in self.payloads)


# ── real producers ──────────────────────────────────────────────────────


def _desk(tmp_path: Path, name: str = "obs.db") -> Database:
    db = Database(tmp_path / name)
    db.projects.create_project(project_id="atlas", name="Atlas")
    db.projects.create_project(project_id="harbor", name="Harbor")
    return db


def _meeting(db: Database, meeting_id: str, text: str, *, day: int, project: str | None = "atlas") -> str:
    started = datetime(2026, 9, day, 10, 0, 0)
    db.meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=started, ended_at=started, title=f"Sync {meeting_id}",
        segments=[TranscriptSegment(text=text, speaker="Dana", start_time=0.0, end_time=1.0)],
    ))
    if project:
        db.projects.associate_meeting_project(meeting_id=meeting_id, project_id=project, source="manual", confidence=1.0)
    return f"meeting:{meeting_id}"


def _filed_note(db: Database, note_id: str, body: str, project: str | None) -> str:
    _note(db, note_id, f"Note {note_id}", body)
    if project:
        db.project_relationships.upsert(project_id=project, resource_ref=f"note:{note_id}")
    return f"note:{note_id}"


class Facts(Scripted):
    """The scripted extractor: each chunk's facts are the "<topic> is
    <value>." sentences its text holds."""

    def __init__(self) -> None:
        super().__init__()

    def extract(self, payload: dict) -> Any:
        self.calls += 1
        self.payloads.append(payload)
        if self.answer is not None:
            return self.answer
        text = payload["user_prompt"].split("<<<", 1)[1].split(">>>", 1)[0]
        found = re.findall(r"([A-Z][\w ]*? is [\w\-:]+)\.", text)
        return {"facts": [F(f"{sentence}.", sentence.split(" is ")[0], [("Atlas", "project")])
                          for sentence in found]}


def _learn(db: Database, rules: Optional[Rules] = None) -> dict:
    """Sweep, extract, consolidate: the conductor's order."""
    sweep(db)
    extract_pending(db, Facts())
    return consolidate_pending(db, rules or Rules())


def _obs(db: Database, **scope: Any) -> list[dict]:
    return read_observations(db, **scope)


def _obs_hits(db: Database, query: str, **scope: Any) -> list[tuple[str, str, tuple]]:
    hits = db.memory.search(query, kinds="observation", **scope).hits
    return [(h.snippet, h.observation_state, h.evidence) for h in hits]


def _table_rows(db: Database, *tables: str) -> dict[str, list[tuple]]:
    out: dict[str, list[tuple]] = {}
    with db._connection() as conn:
        for table in tables:
            out[table] = sorted(tuple(str(v) for v in row) for row in conn.execute(f"SELECT * FROM {table}"))
    return out


# ── the capability ──────────────────────────────────────────────────────


def test_memory_consolidate_is_a_dark_background_capability() -> None:
    capability = next(c for c in builtin_capability_definitions() if c.id == CONSOLIDATE_CAPABILITY)
    assert (capability.group_id, capability.group_label) == ("background", "Background")
    assert set(capability.allowed_boundaries) == {"local", "private_network", "mesh", "cloud"}
    assert capability.requires.structured_output is False
    assert capability.output_kind == "memory_observations"
    assert memory_policy(CONSOLIDATE_CAPABILITY).enabled is False


# ── §8 row 4: the three acceptance tests ────────────────────────────────


def test_three_meetings_that_say_the_same_thing_give_one_observation_with_proof_3(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    refs = []
    for day, meeting in ((1, "m1"), (2, "m2"), (3, "m3")):
        refs.append(_meeting(db, meeting, "Atlas launch is 2026-10-01.", day=day))
        _learn(db)  # one meeting at a time: create, then supports, supports
    observations = _obs(db, project_id="atlas")
    assert len(observations) == 1
    belief = observations[0]
    assert belief["text"] == "Atlas launch is 2026-10-01."
    assert belief["state"] == "current" and belief["proof_count"] == 3
    assert sorted(item["ref"] for item in belief["evidence"]) == sorted(refs)
    assert all(item["opens"] for item in belief["evidence"])
    with db._connection() as conn:
        assert conn.execute("SELECT proof_count FROM memory_observations").fetchone()[0] == 3
    # Recall: the observation is a hit when the caller names the kind, with
    # its evidence refs; it is fused with the source hits.
    result = db.memory.search("Atlas launch", kinds="observation,meeting")
    kinds = [hit.kind for hit in result.hits]
    assert kinds.count("observation") == 1 and kinds.count("meeting") == 3
    hit = next(h for h in result.hits if h.kind == "observation")
    assert hit.observation_state == "current" and sorted(hit.evidence) == sorted(refs)
    assert result.fusion["retrievers"][-1] == "observation" and result.fusion["observation_count"] == 1


def test_a_default_search_is_the_same_with_observations_in_memory(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    for day, meeting in ((1, "m1"), (2, "m2")):
        _meeting(db, meeting, "Atlas launch is 2026-10-01.", day=day)
    _filed_note(db, "n1", "Atlas owner is Dana.", "atlas")
    sweep(db)
    extract_pending(db, Facts())
    questions = ("Atlas launch", "Atlas owner Dana", "launch")
    scopes = ({}, {"project_id": "atlas"}, {"kinds": "meeting,note"})
    before = {(q, i): db.memory.search(q, **scope).to_dict() for q in questions for i, scope in enumerate(scopes)}
    consolidate_pending(db, Rules())
    assert len(_obs(db)) == 2 and _obs_hits(db, "Atlas launch")
    after = {(q, i): db.memory.search(q, **scope).to_dict() for q in questions for i, scope in enumerate(scopes)}
    assert after == before


def test_a_later_reversal_is_superseded_with_a_history_row_never_an_overwrite(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    for day, meeting in ((1, "m1"), (2, "m2"), (3, "m3")):
        _meeting(db, meeting, "Atlas launch is 2026-10-01.", day=day)
    _learn(db)
    old = _obs(db, project_id="atlas")[0]
    _meeting(db, "m4", "Atlas launch is 2026-11-15.", day=4)
    _learn(db)
    with db._connection() as conn:
        rows = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM memory_observations")}
        history = [dict(r) for r in conn.execute("SELECT * FROM memory_observation_history")]
    assert len(rows) == 2
    before = rows[old["id"]]
    assert before["text"] == "Atlas launch is 2026-10-01."  # never overwritten
    assert before["state"] == "superseded"
    new = rows[before["superseded_by"]]
    assert new["text"] == "Atlas launch is 2026-11-15." and new["state"] == "current"
    assert len(history) == 1 and history[0]["observation_id"] == old["id"]
    assert history[0]["prior_text"] == "Atlas launch is 2026-10-01." and history[0]["prior_state"] == "current"
    # The read API serves both; the superseded one stays readable.
    served = {o["state"]: o for o in _obs(db, project_id="atlas")}
    assert served["superseded"]["superseded_by"] == new["id"]
    assert served["superseded"]["history"][0]["prior_text"] == "Atlas launch is 2026-10-01."
    # Recall serves the belief that stands.
    assert [state for _s, state, _e in _obs_hits(db, "Atlas launch")] == ["current"]


def test_a_fact_from_project_b_is_refused_as_evidence_in_project_a(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "ma", "Atlas launch is 2026-10-01.", day=1, project="atlas")
    _meeting(db, "mb", "Harbor budget is 40k.", day=2, project="harbor")
    sweep(db)
    extract_pending(db, Facts())
    with db._connection() as conn:
        facts = {r["source_ref"]: dict(r) for r in conn.execute("SELECT * FROM memory_facts")}
    engine = Rules()
    before = _table_rows(db, *OBS_TABLES, "memory_facts")
    # 1. A batch for A that holds B's fact: refused before any call.
    with pytest.raises(ConsolidationScopeError):
        consolidate_batch(db, engine, ("project", "atlas"), [facts["meeting:ma"], facts["meeting:mb"]])
    assert engine.calls == 0 and _table_rows(db, *OBS_TABLES, "memory_facts") == before
    # 2. The job never mixes scopes: each prompt holds one project's facts.
    stats = consolidate_pending(db, engine)
    assert stats["jobs"] == 2 and engine.calls == 2
    for payload in engine.payloads:
        assert ("Atlas" in payload["user_prompt"]) != ("Harbor" in payload["user_prompt"])
    by_scope = {o["scope"]["id"]: o for o in _obs(db)}
    assert [e["ref"] for e in by_scope["atlas"]["evidence"]] == ["meeting:ma"]
    assert [e["ref"] for e in by_scope["harbor"]["evidence"]] == ["meeting:mb"]
    # 3. An A observation is never shown in B's prompt.
    _meeting(db, "mb2", "Harbor budget is 40k.", day=3, project="harbor")
    sweep(db)
    extract_pending(db, Facts())
    engine.payloads.clear()
    consolidate_pending(db, engine)
    assert "Atlas" not in engine.received()


def test_a_source_moved_to_another_project_while_the_engine_reads_writes_nothing(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    ref = _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    sweep(db)
    extract_pending(db, Facts())
    engine = Rules()

    def move(_payload: dict) -> None:
        engine.during = None  # once
        db.project_relationships.upsert(project_id="atlas", resource_ref=ref, deleted=True)
        db.project_relationships.upsert(project_id="harbor", resource_ref=ref)

    engine.during = move
    stats = consolidate_pending(db, engine)
    # The Atlas answer is refused at the write; the fact is read again in
    # its new scope in the same pass.
    assert stats["calls"] == 2 and stats["skipped"] == 1 and stats["jobs"] == 1
    with db._connection() as conn:
        scopes = [tuple(r) for r in conn.execute("SELECT scope_kind,scope_id FROM memory_observations")]
    assert scopes == [("project", "harbor")]
    assert [o["scope"] for o in _obs(db)] == [{"kind": "project", "id": "harbor"}]


def test_an_answer_that_names_a_fact_outside_its_input_fails_whole(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "ma", "Atlas launch is 2026-10-01.", day=1)
    sweep(db)
    extract_pending(db, Facts())
    engine = Rules()
    engine.answer = {"creates": [{"text": "Harbor budget is 40k.", "fact_ids": ["f1", "f2"], "reason": "x"}],
                     "updates": []}
    stats = consolidate_pending(db, engine)
    assert stats["failed"] == 1 and stats["jobs"] == 0
    assert _table_rows(db, "memory_observations")["memory_observations"] == []


# ── relations: refines, contradicts; history is append only ─────────────


def test_refines_moves_the_prior_text_to_history(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas launch is 2026-10.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas launch is 2026-10-01.", day=2)
    _learn(db, Rules(on_change="refines"))
    [belief] = _obs(db, project_id="atlas")
    assert belief["text"] == "Atlas launch is 2026-10-01." and belief["state"] == "current"
    # The day is backed by the fact that gave it; the month fact backs the month.
    assert belief["proof_count"] == 1
    assert [h["prior_text"] for h in belief["history"]] == ["Atlas launch is 2026-10."]


def test_contradicts_with_no_winner_makes_both_disputed(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas owner is Dana.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas owner is Lee.", day=2)
    _learn(db, Rules(on_change="contradicts"))
    beliefs = {o["text"]: o for o in _obs(db, project_id="atlas")}
    assert {o["state"] for o in beliefs.values()} == {"disputed"}
    dana = beliefs["Atlas owner is Dana."]
    assert {e["stance"] for e in dana["evidence"]} == {"supports", "contradicts"}
    assert dana["history"][0]["prior_state"] == "current"
    assert sorted(state for _s, state, _e in _obs_hits(db, "Atlas owner")) == ["disputed", "disputed"]


def test_history_is_append_only(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas launch is 2026-10-01.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas launch is 2026-11-15.", day=2)
    _learn(db)
    with db._connection() as conn:
        for statement in ("UPDATE memory_observation_history SET prior_text='x'",
                          "DELETE FROM memory_observation_history"):
            with pytest.raises(sqlite3.IntegrityError, match="append only"):
                conn.execute(statement)


# ── withdrawn text never serves through an observation (#839's rule) ─────


def _served(db: Database, query: str = "Atlas launch") -> list[str]:
    """Every way an observation about the Atlas launch is served: recall,
    the read API (all states), and the in-scope list a consolidation prompt
    would show."""
    texts = [s for s, _state, _e in _obs_hits(db, query)]
    texts += [o["text"] for o in _obs(db)]
    with db._connection() as conn:
        live, scopes = consolidate_module.LiveText(conn), consolidate_module.ScopeReader(conn)
        for scope in (("project", "atlas"), ("project", "harbor"), ("desk", "")):
            texts += [o["text"] for o in consolidate_module.scope_observations(conn, scope, [], live=live, scopes=scopes)]
    return [text for text in texts if "launch" in text]


def test_an_edited_source_never_serves_its_old_observation_and_it_never_reanchors(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    assert _served(db) and set(_served(db)) == {"Atlas launch is 2026-10-01."}
    [old] = _obs(db)
    _filed_note(db, "n1", "Atlas launch is 2026-12-24.", "atlas")
    assert _served(db) == []                      # before the sweep
    sweep(db)
    assert _served(db) == []                      # after it
    during: list[list[str]] = []
    rules = Rules()
    rules.during = lambda _payload: during.append(_served(db))
    extract_pending(db, Facts())
    consolidate_pending(db, rules)
    assert during == [[]]                          # while the engine reads
    assert "2026-10-01" not in rules.received()    # the engine never sees it
    assert "2026-10-01" not in json.dumps(_obs(db)) and "2026-10-01" not in repr(_obs_hits(db, "Atlas launch"))
    # The old observation is retired (with a history row) and never comes back.
    assert refresh_observations(db)["retired"] == 1
    with db._connection() as conn:
        state = conn.execute("SELECT state FROM memory_observations WHERE id=?", (old["id"],)).fetchone()[0]
        reasons = [r[0] for r in conn.execute(
            "SELECT reason FROM memory_observation_history WHERE observation_id=?", (old["id"],))]
    assert state == "retired" and reasons == ["retired: no live evidence"]
    # The note goes back to the old text: the fact is read again with the
    # same id, but the retired observation stays retired.
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    rules = Rules()
    _learn(db, rules)
    assert "[retired]" not in rules.received()  # a retired belief is never an input again
    assert "f1 (" in rules.received()            # the fact that came back is read again
    refresh_observations(db)
    with db._connection() as conn:
        assert conn.execute("SELECT state FROM memory_observations WHERE id=?", (old["id"],)).fetchone()[0] == "retired"
    # The belief stands again, as a NEW observation over the live text.
    served = {o["text"]: o for o in _obs(db) if o["state"] == "current"}
    assert served["Atlas launch is 2026-10-01."]["id"] != old["id"]
    assert old["id"] not in {o["id"] for o in _obs(db)}


def test_a_fact_edited_away_before_consolidation_never_reaches_the_engine(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    sweep(db)
    extract_pending(db, Facts())
    _filed_note(db, "n1", "Atlas launch is 2026-12-24.", "atlas")  # edited before any consolidation
    rules = Rules()
    consolidate_pending(db, rules)
    assert "2026-10-01" not in rules.received()
    assert _served(db) == []


def test_a_fact_the_next_extraction_drops_is_not_live_evidence(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.memory import extract as extract_module

    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    assert _served(db)
    monkeypatch.setattr(extract_module, "EXTRACTOR_VERSION", 2)
    empty = Facts()
    empty.answer = {"facts": []}
    extract_pending(db, empty)  # the same text; the new extractor reads no fact
    with db._connection() as conn:
        assert conn.execute("SELECT state FROM memory_facts").fetchone()[0] == "retired"
    assert _served(db) == []


def test_a_source_moved_out_of_its_project_drops_out_of_evidence(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    ref = _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    assert [o["scope"]["id"] for o in _obs(db)] == ["atlas"]
    db.project_relationships.upsert(project_id="atlas", resource_ref=ref, deleted=True)
    db.project_relationships.upsert(project_id="harbor", resource_ref=ref)
    # Atlas's belief has no evidence in Atlas now: never served there.
    assert _obs(db, project_id="atlas") == []
    assert _obs_hits(db, "Atlas launch", project_id="atlas") == []
    assert refresh_observations(db)["retired"] == 1


def test_an_excluded_source_is_no_evidence_for_that_search(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    assert len(_obs_hits(db, "Atlas launch")) == 1
    assert _obs_hits(db, "Atlas launch", exclude_refs=["note:n1"]) == []
    assert _obs_hits(db, "Atlas launch", project_id="harbor") == []
    assert len(_obs_hits(db, "Atlas launch", project_id="atlas")) == 1


@pytest.mark.parametrize("change", ["delete_part", "made_sensitive"])
def test_a_withdrawn_message_never_serves_through_an_observation(tmp_path: Path, change: str) -> None:
    db = _desk(tmp_path)
    thread = db.threads.create_thread(title="Planning")
    lunch = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(lunch.id, kind="text", text="Lunch is noon.")
    secret = db.threads.append_message(thread.id, role="user")
    part = db.threads.append_part(secret.id, kind="text", text="Atlas launch is 2026-10-01.")
    _learn(db)
    [belief] = [o for o in _obs(db) if "launch" in o["text"]]
    assert [e["ref"] for e in belief["evidence"]] == [f"thread:{thread.id}#{secret.id}"]
    if change == "made_sensitive":
        db.threads.append_part(secret.id, kind="text", text=part.text, sensitive=True)
    db.threads.delete_part(part.id)
    assert _served(db) == []          # before the sweep
    sweep(db)
    assert _served(db) == []          # after it (its facts are gone)
    _learn(db)
    assert _served(db) == []          # after another pass
    refresh_observations(db)
    with db._connection() as conn:
        assert conn.execute("SELECT state FROM memory_observations WHERE id=?", (belief["id"],)).fetchone()[0] == "retired"


def test_a_deleted_source_retires_its_observation_and_keeps_the_other_evidence(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    _filed_note(db, "n2", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    [belief] = _obs(db)
    assert belief["proof_count"] == 2
    db.notes.delete("n1")
    # One source left: still served, with only the live evidence.
    [belief] = _obs(db)
    assert belief["proof_count"] == 1 and [e["ref"] for e in belief["evidence"]] == ["note:n2"]
    db.notes.delete("n2")
    assert _served(db) == []
    sweep(db)
    assert refresh_observations(db)["retired"] == 1 and _served(db) == []


def test_a_history_entry_is_withheld_when_a_version_behind_it_is_not_live(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10.", "atlas")
    _learn(db)
    _filed_note(db, "n2", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db, Rules(on_change="refines"))
    [belief] = _obs(db)
    assert belief["history"][0]["prior_text"] == "Atlas launch is 2026-10."
    db.notes.delete("n1")
    [belief] = _obs(db)
    assert belief["text"] == "Atlas launch is 2026-10-01." and belief["history"] == []
    assert "2026-10." not in json.dumps(belief)


# ── a bad answer; idempotent; a killed job ──────────────────────────────


def test_one_malformed_entry_fails_the_whole_answer_and_the_old_observations_stay(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas launch is 2026-10-01.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas launch is 2026-11-15.", day=2)
    sweep(db)
    extract_pending(db, Facts())
    before = _table_rows(db, *OBS_TABLES)
    good = {"observation_id": "o1", "relation": "supersedes", "text": "Atlas launch is 2026-11-15.",
            "fact_ids": ["f1"], "reason": "changed"}
    bad_answers = [
        {"creates": [], "updates": [good], "deletes": [{"observation_id": "o1"}]},   # a delete verb
        {"creates": [], "updates": [{**good, "relation": "deletes"}]},
        {"creates": [], "updates": [{**good, "observation_id": "o2"}]},              # not in the input
        {"creates": [], "updates": [good, {**good, "relation": "supports", "text": ""}]},  # o1 twice
        {"creates": [], "updates": [{**good, "fact_ids": []}]},
        {"creates": [], "updates": [{**good, "fact_ids": ["f1", "f1"]}]},
        {"creates": [], "updates": [{**good, "text": ""}]},
        {"creates": [], "updates": [{**good, "extra": 1}]},
        {"creates": [{"text": ["a list"], "fact_ids": ["f1"], "reason": ""}], "updates": [good]},
        {"creates": [{"text": "x", "fact_ids": ["f1"]}], "updates": [good]},
        {"updates": [good]},
        [good],
    ]
    rules = Rules()
    with db._connection() as conn:
        facts = [dict(r) for r in conn.execute("SELECT * FROM memory_facts WHERE consolidated_at IS NULL")]
    for bad in bad_answers:
        rules.answer = bad
        with pytest.raises(ConsolidationOutputError):
            consolidate_batch(db, rules, ("project", "atlas"), facts)
    stats = consolidate_pending(db, rules)
    assert stats["failed"] == 1 and stats["jobs"] == 0
    assert _table_rows(db, *OBS_TABLES) == before
    with db._connection() as conn:
        job = dict(conn.execute("SELECT kind,target,status,attempts,next_attempt_at FROM memory_jobs").fetchone())
        assert conn.execute("SELECT count(*) FROM memory_facts WHERE consolidated_at IS NULL").fetchone()[0] == 1
    assert (job["kind"], job["target"], job["status"], job["attempts"]) == ("consolidate", "project:atlas", "queued", 1)
    # Waiting for its retry time: the scope is left out of this pass.
    assert pending_batches(db) == []
    # A good answer later clears the job row.
    with db._connection() as conn:
        conn.execute("UPDATE memory_jobs SET next_attempt_at='2000-01-01T00:00:00+00:00'")
    rules.answer = None
    assert consolidate_pending(db, rules)["jobs"] == 1
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_jobs").fetchone()[0] == 0


def test_a_batch_that_fails_six_times_is_passed_over_and_the_scope_goes_on(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    for index in range(9):
        _filed_note(db, f"n{index}", f"Atlas item{index} is ready{index}.", "atlas")
    sweep(db)
    extract_pending(db, Facts())
    [first] = pending_batches(db)
    assert len(first["facts"]) == 8
    for _ in range(6):
        db.memory_index.record_job_failure(
            kind="consolidate", target=first["target"], input_sha=first["input_sha"], version=1,
            error="bad", boundary="local", max_attempts=6, delay=lambda n: 0)
    [second] = pending_batches(db)
    assert len(second["facts"]) == 1 and second["input_sha"] != first["input_sha"]
    # The next batch succeeds; the failed one stays failed and is not tried again.
    rules = Rules()
    assert consolidate_pending(db, rules)["jobs"] == 1 and rules.calls == 1
    with db._connection() as conn:
        assert dict(conn.execute("SELECT status,attempts FROM memory_jobs").fetchone()) == {"status": "failed", "attempts": 6}
    assert pending_batches(db) == [] and consolidate_pending(db, rules)["calls"] == 0


def test_a_second_pass_makes_no_call_and_no_row(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas launch is 2026-10-01.", day=1)
    _meeting(db, "m2", "Harbor budget is 40k.", day=2, project=None)
    _learn(db)
    before = _table_rows(db, *OBS_TABLES, "memory_facts")
    rules = Rules()
    assert consolidate_pending(db, rules) == {
        "jobs": 0, "created": 0, "updated": 0, "calls": 0, "failed": 0, "skipped": 0,
        "more": 0, "yielded": "", "stopped": 0,
    }
    assert rules.calls == 0 and _table_rows(db, *OBS_TABLES, "memory_facts") == before
    assert refresh_observations(db)["retired"] == 0
    assert _table_rows(db, *OBS_TABLES, "memory_facts") == before
    # The desk scope holds the meeting in no project.
    assert {o["scope"]["kind"] for o in _obs(db)} == {"project", "desk"}


def test_a_job_killed_inside_its_transaction_changes_nothing(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db.memory_index import MemoryIndexRepository

    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas launch is 2026-10-01.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas launch is 2026-11-15.", day=2)
    sweep(db)
    extract_pending(db, Facts())
    before = _table_rows(db, *OBS_TABLES, "memory_facts", "memory_jobs", "memory_index_state")
    answer = db.memory.search("Atlas launch", kinds="observation,meeting").to_dict()
    real = MemoryIndexRepository._history
    calls = {"n": 0}

    def dies(*args, **kwargs):
        calls["n"] += 1
        real(*args, **kwargs)
        raise RuntimeError("the hub stopped")

    monkeypatch.setattr(MemoryIndexRepository, "_history", staticmethod(dies))
    with pytest.raises(RuntimeError):
        consolidate_pending(db, Rules())
    assert calls["n"] == 1  # the new observation and a history row were written inside the transaction
    assert _table_rows(db, *OBS_TABLES, "memory_facts", "memory_jobs", "memory_index_state") == before
    assert db.memory.search("Atlas launch", kinds="observation,meeting").to_dict() == answer


# ── load: yield and budget before every call ────────────────────────────


def _three_scopes(tmp_path: Path) -> Database:
    db = _desk(tmp_path)
    _filed_note(db, "na", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "nh", "Harbor budget is 40k.", "harbor")
    _filed_note(db, "nd", "Desk lunch is noon.", None)
    sweep(db)
    extract_pending(db, Facts())
    assert len(pending_batches(db)) == 3
    return db


def test_consolidation_yields_before_every_call(tmp_path: Path) -> None:
    db = _three_scopes(tmp_path)
    live = {"on": False}
    rules = Rules()
    rules.during = lambda _payload: live.update(on=True)
    stats = consolidate_pending(db, rules, yield_check=lambda: "a meeting is recording" if live["on"] else "")
    assert rules.calls == 1 and stats["calls"] == 1 and stats["yielded"] == "a meeting is recording"
    assert stats["more"] == 1 and stats["jobs"] == 1
    live["on"] = False
    rules.during = None
    assert consolidate_pending(db, rules)["jobs"] == 2 and rules.calls == 3


def test_the_budget_counts_every_attempted_call_bad_answers_too(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    for index in range(5):
        db.projects.create_project(project_id=f"p{index}", name=f"P{index}")
        _filed_note(db, f"n{index}", f"Item{index} state is open.", f"p{index}")
    sweep(db)
    extract_pending(db, Facts())
    rules = Rules()
    rules.answer = {"creates": "not a list", "updates": []}
    budget = CallBudget(3)
    stats = consolidate_pending(db, rules, budget=budget)
    assert rules.calls == 3 == stats["calls"] == budget.calls and stats["failed"] == 3 and stats["more"] == 1


def test_consolidation_shares_the_extract_budget_in_the_conductor(tmp_path: Path, monkeypatch) -> None:
    db = _three_scopes(tmp_path)
    facts, rules = Facts(), Rules()
    broker = SimpleNamespace()
    monkeypatch.setattr("holdspeak.memory.extract.resolve_extractor", lambda *_a: facts)
    monkeypatch.setattr(consolidate_module, "resolve_consolidator", lambda *_a: rules)
    monkeypatch.setattr(memory_conductor, "live_work", lambda *_a: "")
    monkeypatch.setattr(memory_conductor, "EXTRACT_CALLS_PER_PASS", 4)
    _filed_note(db, "nx", "Atlas risk is low.\n\nAtlas cost is 9k.\n\n" + "Words. " * 300, "atlas")
    sweep(db)
    extract, consolidate = memory_conductor._model_steps(db, broker, None)
    assert extract["calls"] + consolidate["calls"] <= 4
    assert facts.calls + rules.calls == extract["calls"] + consolidate["calls"]


# ── no engine; custody ──────────────────────────────────────────────────


class _ObsEngine:
    """The physical chat leaf the runner builds: the rule engine's answer."""

    active_provider = "fixture"
    active_model = "rules-fixture"

    def __init__(self) -> None:
        self.rules = Rules()
        self.prompts: list[dict] = []
        self.fail = False

    def run_prompt(self, **kwargs):
        if self.fail:
            raise RuntimeError("the model stopped")
        self.prompts.append(kwargs)
        name = kwargs["response_format"]["json_schema"]["name"]
        if name == "memory_facts":
            return json.dumps(Facts().extract(kwargs))
        assert name == "memory_observations"
        return json.dumps(self.rules.consolidate(kwargs))


@pytest.fixture()
def routed(tmp_path: Path):
    db = Database(tmp_path / "routed.db")
    refs = build_corpus(db)
    broker = _configure(db)
    engine = _ObsEngine()
    broker.inference_runner._engine_factory = lambda revision, **_kwargs: engine
    return SimpleNamespace(db=db, refs=refs, broker=broker, engine=engine)


def test_no_engine_nothing_is_called_and_recall_is_unchanged(routed) -> None:
    golden = json.loads(bench.GOLDEN.read_text())
    assert resolve_consolidator(routed.broker, OWNER) is None
    report = memory_conductor.tick(routed.db, routed.broker)
    assert report["consolidate"]["engine"] == "" and report["consolidate"]["calls"] == 0
    assert routed.engine.prompts == []
    assert bench.keyword_snapshot(routed.db, routed.refs) == golden


def test_a_wider_assignment_is_never_used_for_consolidation(routed) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    _profile(routed.db, "chat-model")
    InferenceAssignmentService(routed.db).set_assignment(OWNER, {
        "command_id": "assign-global", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "chat-model", "profile_revision": 1}],
    })
    assert resolve_consolidator(routed.broker, OWNER) is None


def test_the_assigned_engine_consolidates_through_the_runner_with_a_receipt(routed, monkeypatch) -> None:
    _profile(routed.db, "obs-model", model="qwen-lan", boundary="private_network")
    _assign(routed.db, EXTRACT_CAPABILITY, ["obs-model"])
    monkeypatch.setattr(memory_conductor, "EXTRACT_CALLS_PER_PASS", 1000)
    monkeypatch.setattr(memory_conductor, "CONSOLIDATE_CALLS_PER_PASS", 1000)
    assert memory_conductor.tick(routed.db, routed.broker)["extract"]["facts"] > 0
    golden_default = {q: routed.db.memory.search(q).to_dict()
                      for q in ("Atlas", "Harbor budget", "Dana", "what does Dana owe on Atlas")}
    _assign(routed.db, CONSOLIDATE_CAPABILITY, ["obs-model"])
    report = memory_conductor.tick(routed.db, routed.broker)
    consolidate = report["consolidate"]
    assert consolidate["error"] == "" and consolidate["jobs"] > 0 and consolidate["calls"] == consolidate["jobs"]
    consolidator = resolve_consolidator(routed.broker, memory_conductor._principal())
    assert consolidator.boundary not in ("", "local")
    receipt = routed.broker.store.receipt(next(iter(reversed(consolidator.operation_ids))))
    assert receipt["outcome"] == "succeeded" and receipt["actor_identity"] == "memory-conductor"
    with routed.db._connection() as conn:
        boundaries = {r[0] for r in conn.execute("SELECT boundary FROM memory_observations")}
    assert boundaries == {consolidator.boundary}  # the egress boundary of the call that wrote it
    # A default search is the same with observations in memory.
    assert routed.db.memory_index.stats()["observations"] > 0
    assert {q: routed.db.memory.search(q).to_dict() for q in golden_default} == golden_default


def test_people_store_content_never_becomes_an_observation(tmp_path: Path) -> None:
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService

    owner = Principal(PrincipalKind.OWNER, "memory-slice4-owner")
    db = _desk(tmp_path, "holdspeak.db")
    store = EncryptedPeopleStore(tmp_path / "people-private" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    relationship = people.create_relationship(owner, {"display_name": "Zorvane Quillfeather"})
    note = people.create_note(owner, relationship["id"], {"topic": "Growth", "body": "PEOPLESENTINEL is promoted."})
    _meeting(db, "m-plain", "Atlas plan is ready.", day=1)
    rules = Rules()
    rules.echo = True  # every fact it is given becomes an observation
    _learn(db, rules)
    assert [o["text"] for o in _obs(db)] == ["Atlas plan is ready."]
    held = _memory_text(db)
    for word in ("PEOPLESENTINEL", "Quillfeather", note["id"], relationship["id"]):
        assert word not in rules.received() and word not in held


def test_a_secret_never_reaches_an_observation_or_the_engine(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    secret = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2"
    _filed_note(db, "n-key", f"Deploy token is rotated. The new one is token={secret} now.", "atlas")
    sweep(db)
    extract_pending(db, Facts())
    rules = Rules()
    rules.answer = lambda payload: {
        "creates": [{"text": f"The deploy key is {secret}.", "fact_ids": ["f1"], "reason": f"saw {secret}"}],
        "updates": [],
    }
    consolidate_pending(db, rules)
    assert secret not in rules.received()
    assert secret not in _memory_text(db)
    [belief] = _obs(db)
    assert REDACTED in belief["text"]


# ── the read API and the MCP tool ───────────────────────────────────────


def test_every_evidence_ref_opens_on_the_desk_or_is_a_declared_no_window_kind() -> None:
    from holdspeak.services.memory_grounding import DESK_REF_KINDS, NO_WINDOW_REF_KINDS

    for kind in EXTRACT_KINDS:
        ref = desk_ref(f"{kind}:x1", "msg1")
        assert ref.split(":", 1)[0] in set(DESK_REF_KINDS) | set(NO_WINDOW_REF_KINDS), (kind, ref)
    assert desk_ref("thread:t1", "m9") == "thread:t1#m9"
    assert desk_ref("action:a1") == "action_item:a1"
    assert desk_ref("decision_record:d1") == "decision:d1"


def test_the_mcp_tool_reads_observations_scoped_and_needs_read(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.mcp.families import memory as family
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.services.thread_tools import tool_class

    db = _desk(tmp_path)
    _meeting(db, "ma", "Atlas launch is 2026-10-01.", day=1, project="atlas")
    _meeting(db, "mb", "Harbor budget is 40k.", day=2, project="harbor")
    _learn(db)
    monkeypatch.setattr(family, "db_or", lambda _default: db)
    assert "memory.observations" in {tool["name"] for tool in family.TOOLS}
    assert TOOL_AUTHORITY["memory.observations"] == "work"
    assert tool_class("memory.observations") == "evidence_read"
    out = family.dispatch("memory.observations", {"project_id": "atlas"}, OWNER)
    assert [o["text"] for o in out["observations"]] == ["Atlas launch is 2026-10-01."]
    assert out["observations"][0]["evidence"][0]["ref"] == "meeting:ma"
    assert family.dispatch("memory.observations", {"scope": "desk"}, OWNER)["count"] == 0
    assert family.dispatch("memory.observations", {}, OWNER)["count"] == 2
    with pytest.raises(ServiceError):
        MemoryService(db).observations(Principal(PrincipalKind.NONE, ""))


# ── Astra's two notes on #839 ───────────────────────────────────────────


def test_an_entity_kind_that_is_a_list_is_a_bad_answer_with_a_back_off(tmp_path: Path) -> None:
    db = Database(tmp_path / "kind-list.db")
    _note(db, "n", "Plan", "Atlas launch is 2026-10-01.")
    sweep(db)
    engine = Scripted()
    engine.answer = {"facts": [{**F("Atlas launch is 2026-10-01.", "Atlas"),
                                "entities": [{"name": "Atlas", "kind": ["project"]}]}]}
    with pytest.raises(ExtractionOutputError):
        extract_source(db, engine, "note:n")
    stats = extract_pending(db, engine)
    assert stats["failed"] == 1
    with db._connection() as conn:
        assert dict(conn.execute("SELECT kind,status,attempts FROM memory_jobs").fetchone()) == {
            "kind": "extract", "status": "queued", "attempts": 1,
        }


def test_the_conductor_reports_the_true_call_count_after_a_provider_error(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "count.db")
    _note(db, "n", "Plan", "Atlas launch is 2026-10-01.")
    sweep(db)

    class Down:
        boundary, model_id, operation_ids, revision_id = "private_network", "down", [], ""

        def extract(self, _payload):
            raise RuntimeError("provider 503")

    monkeypatch.setattr("holdspeak.memory.extract.resolve_extractor", lambda *_a: Down())
    monkeypatch.setattr(memory_conductor, "live_work", lambda *_a: "")
    report = memory_conductor._extract_step(db, SimpleNamespace(), None)
    assert report["error"] == "provider 503" and report["calls"] == 1


# ── review round 1 (Astra, PR #843): the five defects, each fenced ───────


def _month_then_day(db: Database, mode: str) -> tuple[str, Callable[[], None], dict]:
    """The month from one source, the day refined from a second source, and
    the function that withdraws the second source by ``mode``."""
    if mode == "sensitive":
        _filed_note(db, "n-month", "Atlas launch is 2026-10.", None)
        thread = db.threads.create_thread(title="Planning")
        message = db.threads.append_message(thread.id, role="user")
        part = db.threads.append_part(message.id, kind="text", text="Atlas launch is 2026-10-01.")
        scope: dict = {}
        ref = f"thread:{thread.id}"

        def withdraw() -> None:
            db.threads.append_part(message.id, kind="text", text=part.text, sensitive=True)
            db.threads.delete_part(part.id)
    else:
        _filed_note(db, "n-month", "Atlas launch is 2026-10.", "atlas")
        _learn(db)
        ref = _filed_note(db, "general", "Atlas launch is 2026-10-01.", "atlas")
        scope = {"project_id": "atlas"}

        def withdraw() -> None:
            if mode == "move":
                db.project_relationships.upsert(project_id="atlas", resource_ref=ref, deleted=True)
                db.project_relationships.upsert(project_id="harbor", resource_ref=ref)
            elif mode == "delete":
                db.notes.delete("general")
            elif mode == "edit":
                _filed_note(db, "general", "Lunch is at noon.", "atlas")
    if mode == "sensitive":
        sweep(db)
        extract_pending(db, Facts())
        with db._connection() as conn:
            month = [dict(r) for r in conn.execute("SELECT * FROM memory_facts WHERE text LIKE '%2026-10.'")]
        consolidate_batch(db, Rules(), ("desk", ""), month)
    _learn(db, Rules(on_change="refines"))
    [belief] = _obs(db, **scope)
    assert belief["text"] == "Atlas launch is 2026-10-01."
    return ref, withdraw, scope


def _everything_served(db: Database, scope: dict, **search: Any) -> str:
    """Recall, the read API (with history and evidence) and the next prompt's
    view of the observations, as one text."""
    parts = [repr(db.memory.search("Atlas launch", kinds="observation", **scope, **search).to_dict())]
    parts.append(json.dumps(_obs(db)))
    with db._connection() as conn:
        live, scopes = consolidate_module.LiveText(conn), consolidate_module.ScopeReader(conn)
        for each in (("project", "atlas"), ("project", "harbor"), ("desk", "")):
            parts += [o["text"] for o in consolidate_module.scope_observations(conn, each, [], live=live, scopes=scopes)]
    return "\n".join(parts)


@pytest.mark.parametrize("mode", ["move", "delete", "edit", "sensitive"])
def test_a_withdrawn_refinement_falls_back_to_the_text_its_own_evidence_backs(tmp_path: Path, mode: str) -> None:
    db = _desk(tmp_path)
    ref, withdraw, scope = _month_then_day(db, mode)
    withdraw()
    for moment in ("before the sweep", "after the sweep"):
        served_text = _everything_served(db, scope)
        assert "2026-10-01" not in served_text, moment
        [belief] = [o for o in _obs(db) if o["text"].startswith("Atlas launch")]
        assert belief["text"] == "Atlas launch is 2026-10." and belief["proof_count"] == 1, moment
        assert belief["history"] == []  # the refine entry names the withdrawn fact
        assert [e["ref"] for e in belief["evidence"]] == ["note:n-month"]
        sweep(db)
    # Nothing is retired: the month is still backed.
    assert refresh_observations(db)["retired"] == 0
    # The next consolidation in that scope is shown the month, never the day.
    _filed_note(db, "n-more", "Atlas launch is 2026-10.", None if mode == "sensitive" else "atlas")
    rules = Rules()
    _learn(db, rules)
    assert "Atlas launch is 2026-10." in rules.received() and "2026-10-01" not in rules.received()
    # The month's source goes too: now it retires.
    db.notes.delete("n-month")
    db.notes.delete("n-more")
    sweep(db)
    assert refresh_observations(db)["retired"] == 1
    assert "Atlas launch" not in _everything_served(db, scope)


def test_an_excluded_refinement_is_not_served_to_that_search(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    ref, _withdraw, scope = _month_then_day(db, "exclude")
    [(text, _state, evidence)] = _obs_hits(db, "Atlas launch", exclude_refs=[ref], **scope)
    assert text == "Atlas launch is 2026-10." and evidence == ("note:n-month",)
    assert "2026-10-01" not in repr(db.memory.search("Atlas launch", kinds="observation", exclude_refs=[ref]).to_dict())
    # The other searches still see the day.
    assert _obs_hits(db, "Atlas launch", **scope)[0][0] == "Atlas launch is 2026-10-01."


def test_a_refiled_source_stops_counting_in_its_old_project_at_once(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    ref = _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    db.project_relationships.upsert(project_id="atlas", resource_ref=ref, deleted=True)
    db.project_relationships.upsert(project_id="harbor", resource_ref=ref)
    assert "2026-10-01" not in _everything_served(db, {"project_id": "atlas"})
    assert _obs(db, project_id="harbor") == []  # its old belief never moves with it


def test_a_history_reason_with_withdrawn_text_is_withheld(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n-oct", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)
    _filed_note(db, "n-dec", "Atlas launch is 2026-12-24.", "atlas")
    rules = Rules()
    base = rules.consolidate

    def with_reason(payload: dict) -> Any:
        answer = Rules.consolidate(Rules(), payload)
        for item in answer["updates"]:
            item["reason"] = item["text"]  # the reason repeats the new day
        return answer

    rules.answer = with_reason
    _learn(db, rules)
    old = next(o for o in _obs(db) if o["state"] == "superseded")
    assert "2026-12-24" in json.dumps(old["history"])  # shown while it is live
    db.notes.delete("n-dec")
    sweep(db)
    refresh_observations(db)
    [belief] = _obs(db)
    assert belief["id"] == old["id"] and belief["superseded_by"] is None
    assert "2026-12-24" not in json.dumps(_obs(db)) and belief["history"] == []
    assert base is not None


@pytest.mark.parametrize("raw", [
    "\n".join(["A" * 64, "B" * 64, "C" * 64]),
    "x" * 589 + " ghp_" + "A" * 36,
    "x" * 595 + " ghp_" + "A" * 36,  # the marker crosses the limit: it goes whole
])
def test_a_model_text_is_redacted_before_it_is_folded_or_cut(tmp_path: Path, raw: str) -> None:
    from holdspeak.memory.defense import redact

    assert redact(raw) != raw  # the whole text is a secret shape
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    sweep(db)
    extract_pending(db, Facts())
    rules = Rules()
    rules.answer = {"creates": [{"text": raw, "fact_ids": ["f1"], "reason": raw}], "updates": []}
    consolidate_pending(db, rules)
    held = _memory_text(db) + json.dumps(_obs(db))
    for leak in ("A" * 64, "B" * 64, "C" * 64, "ghp_A"):
        assert leak not in held
    # A cut never leaves part of a marker (or of a secret) behind.
    with db._connection() as conn:
        written = [str(r[0]) for r in conn.execute(
            "SELECT text FROM memory_observation_versions UNION ALL SELECT text FROM memory_observations"
            " UNION ALL SELECT prior_text||reason FROM memory_observation_history")]
    for text in written + [o["text"] for o in _obs(db)]:
        assert re.search(r"\[(?!redacted\])", text) is None, text
    [belief] = _obs(db)
    assert belief["text"] in (REDACTED, "x" * 589 + " " + REDACTED, "x" * 595)


def test_a_fact_text_is_redacted_before_it_is_cut(tmp_path: Path) -> None:
    db = Database(tmp_path / "fact-cut.db")
    _note(db, "n", "Plan", "Atlas launch is 2026-10-01.")
    sweep(db)
    engine = Scripted()
    raw = "x" * 589 + " ghp_" + "A" * 36
    engine.answer = {"facts": [F(raw, "Atlas", [("Atlas", "project")], obj=raw)]}
    extract_pending(db, engine)
    assert "ghp_A" not in _memory_text(db)


@pytest.mark.parametrize("answer", [
    # Astra's repro: one fact makes a create AND disputes o1.
    {"creates": [{"text": "Atlas owner is Lee.", "fact_ids": ["f1"], "reason": "new"}],
     "updates": [{"observation_id": "o1", "relation": "contradicts", "text": "Atlas owner is Lee Moreau.",
                  "fact_ids": ["f1"], "reason": "x"}]},
    {"creates": [{"text": "Atlas owner is Lee.", "fact_ids": ["f1"], "reason": "new"}],
     "updates": [{"observation_id": "o1", "relation": "contradicts", "text": "Atlas owner is Lee.",
                  "fact_ids": ["f1"], "reason": "x"}]},
    {"creates": [{"text": "Atlas owner is Dana.", "fact_ids": ["f1"], "reason": "again"}],
     "updates": [{"observation_id": "o1", "relation": "supports", "text": "", "fact_ids": ["f2"], "reason": "x"}]},
    {"creates": [{"text": "Atlas owner is Lee.", "fact_ids": ["f1"], "reason": "new"}],
     "updates": [{"observation_id": "o1", "relation": "contradicts", "text": "Atlas owner is Lee.",
                  "fact_ids": ["f2"], "reason": "x"}]},
])
def test_an_answer_whose_entries_conflict_fails_whole(tmp_path: Path, answer: dict) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas owner is Dana.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas owner is Lee.", day=2)
    _meeting(db, "m3", "Atlas owner is Lee.", day=3)
    sweep(db)
    extract_pending(db, Facts())
    before = _table_rows(db, *OBS_TABLES, "memory_observation_versions", "memory_observation_backing")
    rules = Rules()
    rules.answer = answer
    stats = consolidate_pending(db, rules)
    assert stats["failed"] == 1 and stats["jobs"] == 0
    assert _table_rows(db, *OBS_TABLES, "memory_observation_versions", "memory_observation_backing") == before
    assert [o["state"] for o in _obs(db)] == ["current"]


@pytest.mark.parametrize("table,statement", [
    ("memory_observation_history",
     "INSERT OR REPLACE INTO memory_observation_history(id,observation_id,at,prior_text,prior_state)"
     " SELECT id,observation_id,at,'rewritten',prior_state FROM memory_observation_history LIMIT 1"),
    ("memory_observation_versions",
     "INSERT OR REPLACE INTO memory_observation_versions(observation_id,version,text,at)"
     " SELECT observation_id,version,'rewritten',at FROM memory_observation_versions LIMIT 1"),
    ("memory_observation_versions", "UPDATE memory_observation_versions SET text='rewritten'"),
    ("memory_observation_versions", "DELETE FROM memory_observation_versions"),
])
def test_history_and_versions_refuse_a_replace_on_the_real_connection(tmp_path: Path, table: str, statement: str) -> None:
    db = _desk(tmp_path)
    _meeting(db, "m1", "Atlas launch is 2026-10.", day=1)
    _learn(db)
    _meeting(db, "m2", "Atlas launch is 2026-10-01.", day=2)
    _learn(db, Rules(on_change="refines"))
    before = _table_rows(db, table)
    with db._connection() as conn:
        assert conn.execute("PRAGMA recursive_triggers").fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError, match="append only"):
            conn.execute(statement)
    assert _table_rows(db, table) == before and "rewritten" not in repr(before)


def test_a_belief_two_facts_made_needs_both(tmp_path: Path) -> None:
    db = _desk(tmp_path)
    _filed_note(db, "n1", "Atlas launch is 2026-10-01.", "atlas")
    _filed_note(db, "n2", "Atlas launch is 2026-10-01.", "atlas")
    _learn(db)  # one batch: one create from both facts
    [belief] = _obs(db)
    assert belief["proof_count"] == 2
    db.notes.delete("n2")
    # The text came from both facts together: half of it is no backing.
    assert _obs(db) == [] and _obs_hits(db, "Atlas launch") == []
