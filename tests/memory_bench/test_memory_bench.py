"""The memory benchmark (docs/internal/MEMORY-DESIGN.md §7).

FAST: the corpus is written through the real producers, the real sweep cuts
it, and ``FixtureEmbedder`` gives real-model vectors from ``vectors.npz``.
The test prints recall@5 before (keyword + relation, no engine) and after
(fused).

Slow: the same benchmark with the real model, and a drift check of fresh
vectors against the fixture.  Set ``HOLDSPEAK_MEMORY_EMBED_MODEL`` to the
GGUF file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from holdspeak.db import Database
from holdspeak.memory.retain import embed_pending, rebuild, sweep

from . import bench
from .corpus import ATLAS, HARBOR, build_corpus
from .engines import FixtureEmbedder, LlamaCppEmbedder, MissingFixtureVector

PARAPHRASE_GATE = 0.7


@pytest.fixture()
def desk(tmp_path: Path):
    db = Database(tmp_path / "bench.db")
    refs = build_corpus(db)
    return db, refs


def test_no_engine_answer_equals_the_search_before_the_index(desk) -> None:
    """With no engine the answer is today's keyword + relation answer, value
    for value: before the sweep, after the sweep, and after the vectors exist
    but no engine is set."""
    db, refs = desk
    golden = json.loads(bench.GOLDEN.read_text())
    assert bench.keyword_snapshot(db, refs) == golden
    sweep(db)
    assert bench.keyword_snapshot(db, refs) == golden
    embed_pending(db, FixtureEmbedder(bench.FIXTURE))
    assert db.memory_index.stats()["vectors"] > 0
    assert db.memory.embedder is None
    assert bench.keyword_snapshot(db, refs) == golden


def test_an_engine_that_fails_or_has_no_vectors_changes_nothing(desk) -> None:
    db, refs = desk
    golden = json.loads(bench.GOLDEN.read_text())
    sweep(db)
    engine = FixtureEmbedder(bench.FIXTURE)
    # The engine is set but no vector exists yet (the model just arrived).
    db.memory.set_embedder(engine)
    assert bench.keyword_snapshot(db, refs) == golden
    embed_pending(db, engine)

    class Broken:
        model_id = engine.model_id
        dim = engine.dim

        def embed_query(self, text):
            raise RuntimeError("engine is gone")

    db.memory.set_embedder(Broken())
    broken = bench.keyword_snapshot(db, refs)
    for answer in broken.values():
        # The failed call is named; the rest is the keyword answer.
        assert answer["ranking"].pop("engine")["outcome"] == "failed"
    assert broken == golden


def test_recall_before_and_after(desk, capsys) -> None:
    db, refs = desk
    baseline = json.loads(bench.BASELINE.read_text())
    sweep(db)

    before = bench.run(db, refs)
    assert before["groups"] == baseline["keyword"], "the keyword baseline moved"
    # By construction: no paraphrase question shares a content word with a
    # source that answers it, so keyword search finds none of them.
    assert before["groups"]["paraphrase"]["recall@5"] == 0.0

    engine = FixtureEmbedder(bench.FIXTURE)
    embed_pending(db, engine)
    db.memory.set_embedder(engine)
    after = bench.run(db, refs)

    with capsys.disabled():
        print()
        print(bench.table("before: keyword + relation (no engine)", before))
        print(bench.table(f"after: fused, {engine.model_id}", after))

    assert after["groups"]["same_word"]["recall@5"] >= before["groups"]["same_word"]["recall@5"]
    assert after["groups"]["same_word"]["mrr"] >= before["groups"]["same_word"]["mrr"]
    assert after["groups"]["paraphrase"]["recall@5"] >= PARAPHRASE_GATE


def test_project_scope_holds_in_every_retriever(desk) -> None:
    """A scoped question never gets a ref from outside its project, fused."""
    db, refs = desk
    sweep(db)
    engine = FixtureEmbedder(bench.FIXTURE)
    embed_pending(db, engine)
    db.memory.set_embedder(engine)
    members: dict[str, set[str]] = {ATLAS: set(), HARBOR: set()}
    from .corpus import ARTIFACTS, DESK_DECISIONS, MEETINGS, NOTES, THREADS

    for rows in (NOTES, ARTIFACTS, MEETINGS, DESK_DECISIONS, THREADS):
        for row in rows:
            if row[1]:
                members[row[1]].add(refs[row[0]])
    asked = 0
    for question in bench.load_questions():
        project = question.get("project")
        if not project:
            continue
        asked += 1
        result = db.memory.search(question["q"], project_id=project, limit=50)
        assert result.fusion is not None and "vector" in result.fusion["retrievers"]
        got = {hit.source_ref.split("#", 1)[0] for hit in result.hits}
        assert got, question["id"]
        assert got <= members[project], (question["id"], got - members[project])
    assert asked >= 4


def test_kind_and_time_filters_apply_to_the_vector_retriever(desk) -> None:
    db, refs = desk
    sweep(db)
    engine = FixtureEmbedder(bench.FIXTURE)
    embed_pending(db, engine)
    db.memory.set_embedder(engine)
    question = "why did the app launch slip"  # a paraphrase: vector hits only
    notes = db.memory.search(question, kinds="note", limit=50)
    assert notes.hits and {hit.kind for hit in notes.hits} == {"note"}
    assert all(hit.retrieval_origin == "vector" for hit in notes.hits)
    late = db.memory.search(question, kinds="note", time_from="2026-09-12T00:00:00Z", limit=50)
    assert late.hits and all(hit.occurred_at >= "2026-09-12" for hit in late.hits)
    assert len(late.hits) < len(notes.hits)
    never = db.memory.search(question, time_from="2030-01-01", limit=50)
    assert never.hits == []
    held_out = db.memory.search(question, exclude_refs=[refs["n-login"]], limit=50)
    assert refs["n-login"] not in {hit.source_ref for hit in held_out.hits}
    assert refs["n-login"] in {hit.source_ref for hit in notes.hits}


def test_a_fused_hit_keeps_the_shape_callers_read(desk) -> None:
    db, refs = desk
    sweep(db)
    engine = FixtureEmbedder(bench.FIXTURE)
    embed_pending(db, engine)
    before = db.memory.search("CSV export of invoices").to_dict()
    db.memory.set_embedder(engine)
    after = db.memory.search("CSV export of invoices").to_dict()
    assert set(after) == set(before)
    assert set(after["hits"][0]) == set(before["hits"][0])
    assert after["ranking"]["method"] == before["ranking"]["method"]
    assert after["ranking"]["fusion"]["method"] == "reciprocal_rank_fusion"
    assert after["ranking"]["fusion"]["k"] == 60
    # A thread hit names the message, as the keyword pass does.
    thread_hit = next(hit for hit in after["hits"] if hit["kind"] == "thread")
    assert thread_hit["source_ref"].startswith(refs["th-export"] + "#")
    vector_only = db.memory.search("where is the company retreat").to_dict()["hits"][0]
    assert vector_only["source_ref"] == refs["n-offsite"]
    assert vector_only["retrieval_origin"] == "vector"
    assert "Lisbon" in vector_only["snippet"]


def test_rebuild_gives_the_same_hits(desk) -> None:
    db, refs = desk
    engine = FixtureEmbedder(bench.FIXTURE)
    sweep(db)
    embed_pending(db, engine)
    db.memory.set_embedder(engine)
    before = bench.run(db, refs)["ranked"]
    counts = rebuild(db, engine)
    assert counts["sources"] == len(refs) and counts["vectors"] == counts["chunks"] > 0
    assert bench.run(db, refs)["ranked"] == before


def test_a_text_with_no_fixture_vector_fails(desk) -> None:
    db, _refs = desk
    db.notes.upsert(note_id="n-new", title="Not in the fixture", body_markdown="A text nobody embedded.")
    sweep(db)
    with pytest.raises(MissingFixtureVector):
        embed_pending(db, FixtureEmbedder(bench.FIXTURE))


@pytest.mark.slow
@pytest.mark.requires_llama_cpp
def test_bench_with_the_real_model(desk, capsys) -> None:
    model_path = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")
    if not model_path or not Path(model_path).is_file():
        pytest.skip("set HOLDSPEAK_MEMORY_EMBED_MODEL to nomic-embed-text-v1.5.Q8_0.gguf")
    pytest.importorskip("llama_cpp")
    db, refs = desk
    sweep(db)
    before = bench.run(db, refs)
    engine = LlamaCppEmbedder(model_path, model_name="nomic-embed-text-v1.5.Q8_0")
    fixture = FixtureEmbedder(bench.FIXTURE)
    assert engine.model_id == fixture.model_id
    embed_pending(db, engine)
    db.memory.set_embedder(engine)
    after = bench.run(db, refs)
    with capsys.disabled():
        print()
        print(bench.table("before: keyword + relation (no engine)", before))
        print(bench.table(f"after: fused, real model {engine.model_id}", after))
    assert after["groups"]["same_word"]["recall@5"] >= before["groups"]["same_word"]["recall@5"]
    assert after["groups"]["paraphrase"]["recall@5"] >= PARAPHRASE_GATE
    # Drift: a fresh vector is within cosine 0.98 of its fixture.
    with db._connection() as conn:
        texts = [str(row[0]) for row in conn.execute("SELECT text FROM memory_chunks ORDER BY id")]
    fresh = engine.embed_documents(texts)
    held = fixture.embed_documents(texts)
    assert float(np.min(np.sum(fresh * held, axis=1))) >= 0.98


# ── slice 3: the five relation questions (MEMORY-DESIGN.md §7, §8 row 3) ──


def test_the_five_relation_questions_pass_with_recorded_real_facts(desk, capsys) -> None:
    """The relation group, keyword + relation before; the entity walk after,
    over facts the real model gave for this corpus (``facts.json``, replayed
    by ``FixtureExtractor``).  The other groups do not drop below the
    keyword baseline when the facts are fused in."""
    from holdspeak.memory.extract import extract_pending

    from .engines import FixtureExtractor

    db, refs = desk
    sweep(db)
    relation = bench.load_relation_questions()
    assert len(relation) == 5
    before = bench.run(db, refs, questions=relation)
    before_other = bench.run(db, refs)

    engine = FixtureExtractor(bench.FACTS)
    stats = extract_pending(db, engine)
    assert stats["sources"] == len(refs) and stats["facts"] > 0
    after = bench.run(db, refs, questions=relation)
    after_other = bench.run(db, refs)

    with capsys.disabled():
        print()
        print(bench.table("relation, before: keyword + relation (no facts)", before))
        print(bench.table(f"relation, after: + entity walk ({engine.model_id} facts)", after))
        print(bench.table("other groups, after", after_other))
        for question in relation:
            print(f"  {question['id']} {question['q']!r}: {after['ranked'][question['id']][:5]}")

    assert after["groups"]["relation"]["recall@5"] == 1.0
    assert after["groups"]["relation"]["complete@5"] >= before["groups"]["relation"]["complete@5"]
    # Keyword search finds these sources too (a speaker name is indexed), so
    # the group alone proves little.  Two things the entity walk must add:
    # the right source ranks higher, and the walk ALONE (no keyword list)
    # answers each question.  Measured 2026-10-04: the walk alone holds 9 of
    # the 10 expected sources; r04 misses m-atlas-sync, where the model
    # credits the auditors' request to "the auditors", not to Sam.
    assert after["groups"]["relation"]["mrr"] > before["groups"]["relation"]["mrr"]
    from holdspeak.db.memory import _VALID_KINDS

    held = total = 0
    for question in relation:
        walked = db.memory._entity_rows(
            question["q"], selected=tuple(_VALID_KINDS), project=question.get("project"),
            start=None, end=None, excluded=set(),
        )
        got = {row["source_ref"].split("#", 1)[0] for row in walked or []}
        expected = {refs[label] for label in question["expect"]}
        assert expected & got, (question["id"], got)
        held += len(expected & got)
        total += len(expected)
    with capsys.disabled():
        print(f"  the entity walk alone holds {held} of {total} expected sources")
    assert held >= total - 1
    for name in ("same_word", "paraphrase"):
        assert after_other["groups"][name]["recall@5"] >= before_other["groups"][name]["recall@5"]


# ── the hard relation questions: only the entity walk answers them ──────

#: The walk must find the first expected source in the top 5 for at least
#: this share of the hard questions (keyword alone: 0.0 by construction).
HARD_WALK_GATE = 0.85


def _hard_desk(tmp_path: Path):
    from .corpus import build_hard_corpus

    db = Database(tmp_path / "hard.db")
    refs = build_corpus(db)
    refs.update(build_hard_corpus(db))
    sweep(db)
    return db, refs


def _walk_alone(db, question) -> list[str]:
    from holdspeak.db.memory import _VALID_KINDS

    walked = db.memory._entity_rows(
        question["q"], selected=tuple(_VALID_KINDS), project=question.get("project"),
        start=None, end=None, excluded=set(),
    )
    return list(dict.fromkeys(row["source_ref"].split("#", 1)[0] for row in walked or []))


def test_hard_relation_questions_need_the_entity_walk(tmp_path: Path, capsys) -> None:
    """Questions that share no searchable word with the sources that answer
    them: the name is only in a meeting or thread title (the keyword index
    does not read titles of those kinds) or in another source (an alias,
    "T. Wierzbicki" against "Tomasz Wierzbicki").  Keyword search finds none
    of them; the entity walk over the facts the real model gave
    (``relation_hard_facts.json``) finds them.  If the walk is gone from
    fusion, this test fails.

    Vectors find them too (measured 2026-10-04: recall@5 1.000, MRR 0.889):
    the chunker puts the title in front of every chunk, so the vector reads
    the name the extractor reads.  With vectors on, the walk lifts the rank
    (MRR 1.000): r14 "Jane Whitfield want" has a-research first by vector."""
    from holdspeak.memory.extract import extract_pending

    from .engines import FixtureExtractor

    db, refs = _hard_desk(tmp_path)
    hard = bench.load_hard_relation_questions()
    assert len(hard) == 9

    keyword = bench.run(db, refs, questions=hard)
    embedder = FixtureEmbedder(bench.FIXTURE, bench.HARD_VECTORS)
    embed_pending(db, embedder)
    db.memory.set_embedder(embedder)
    vectors = bench.run(db, refs, questions=hard)
    db.memory.set_embedder(None)

    engine = FixtureExtractor(bench.FACTS, bench.HARD_FACTS)
    stats = extract_pending(db, engine)
    assert stats["sources"] == len(refs) and stats["facts"] > 0
    walk = bench.run(db, refs, questions=hard)
    db.memory.set_embedder(embedder)
    walk_vectors = bench.run(db, refs, questions=hard)

    with capsys.disabled():
        print()
        print(bench.table("hard relation: keyword only (no facts, no vectors)", keyword))
        print(bench.table(f"hard relation: keyword + vectors ({embedder.model_id}), no facts", vectors))
        print(bench.table(f"hard relation: keyword + entity walk ({engine.model_id} facts)", walk))
        print(bench.table("hard relation: keyword + vectors + entity walk", walk_vectors))
        names = {ref: label for label, ref in refs.items()}
        for question in hard:
            print(
                f"  {question['id']} {question['q']!r}\n"
                f"      vectors, no facts: {[names[ref] for ref in vectors['ranked'][question['id']][:5]]}\n"
                f"      keyword + walk:    {[names[ref] for ref in walk['ranked'][question['id']][:5]]}\n"
                f"      walk alone:        {[names[ref] for ref in _walk_alone(db, question)[:5]]}"
            )

    group = "relation_hard"
    # By construction no question shares a searchable word with a source it
    # expects, so keyword search finds none of them.
    assert keyword["groups"][group]["recall@5"] == 0.0
    assert walk["groups"][group]["recall@5"] >= HARD_WALK_GATE
    # Measured 2026-10-04 (EXTRACTOR_VERSION 2): 7 of 9 complete. Each
    # question that is complete stays fenced ONE BY ONE; the two known gaps
    # are strict xfails of their own (Astra, #845 iteration 2):
    # - r11 misses n-supplier: "T. Wierzbicki" does not join "Tomasz
    #   Wierzbicki" (test_hard_relation_alias_joins_the_full_name).
    # - r09 finds no Kestrel source without vectors: with no title rule the
    #   model leaves "Kestrel" out of the facts (the title rule invented
    #   projects; test_hard_relation_kestrel_is_complete_by_the_walk).
    known_gaps = {"r09", "r11"}
    for question in hard:
        if question["id"] in known_gaps:
            continue
        expected = {refs[label] for label in question["expect"]}
        assert expected <= set(walk["ranked"][question["id"]][:5]), question["id"]
    assert walk_vectors["groups"][group]["recall@5"] >= HARD_WALK_GATE
    assert walk_vectors["groups"][group]["mrr"] > vectors["groups"][group]["mrr"]


def _dates_of(fact: dict) -> set[str]:
    import re

    found = set(re.findall(r"\d{4}-\d{2}-\d{2}", str(fact.get("text") or "")))
    return found | {str(fact[key])[:10] for key in ("occurred_start", "occurred_end") if fact.get(key)}


def _case_facts(tmp_path: Path, case: dict) -> list[dict]:
    from holdspeak.memory.extract import extract_pending

    from .corpus import build_date_case
    from .engines import FixtureExtractor

    db = Database(tmp_path / f"date-{case['id']}.db")
    ref = build_date_case(db, case)
    sweep(db)
    extract_pending(db, FixtureExtractor(bench.DATE_FACTS))
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT text,occurred_start,occurred_end FROM memory_facts WHERE source_ref=? AND state='live'", (ref,)
        )]


@pytest.mark.parametrize("case", __import__("tests.memory_bench.corpus", fromlist=["DATE_CASES"]).DATE_CASES,
                         ids=lambda case: case["id"])
def test_a_day_with_no_month_takes_its_month_by_tense(tmp_path: Path, case: dict) -> None:
    """Real-model answers (``date_facts.json``, recorded from the LAN model):
    a day with no month is the next such day for a thing to come and the most
    recent such day for a thing that happened; a named month stays; a span
    keeps its length.  No code moves a date: this is the prompt alone."""
    facts = _case_facts(tmp_path, case)
    dates = set().union(*(_dates_of(fact) for fact in facts)) if facts else set()
    for day in case["want"]:
        assert day in dates, (case["id"], day, facts)
    for day in case["never"]:
        assert day not in dates, (case["id"], day, facts)
    if "span" in case:
        spans = {(str(f["occurred_start"])[:10], str(f["occurred_end"])[:10]) for f in facts}
        assert tuple(case["span"]) in spans, (case["id"], facts)


def _hard_dates(tmp_path: Path, label: str) -> set[str]:
    from holdspeak.memory.extract import extract_pending

    from .engines import FixtureExtractor

    db, refs = _hard_desk(tmp_path)
    extract_pending(db, FixtureExtractor(bench.FACTS, bench.HARD_FACTS))
    with db._connection() as conn:
        mine = [dict(row) for row in conn.execute(
            "SELECT text,occurred_start,occurred_end FROM memory_facts WHERE state='live' AND source_ref=?",
            (refs[label],),
        )]
    return set().union(*(_dates_of(fact) for fact in mine)) if mine else set()


@pytest.mark.parametrize("label,future,past", [
    ("m-okonkwo", "2026-10-09", "2026-09-09"),  # "my leave starts on the ninth", 22 Sep
    ("m-santos", "2026-10-15", "2026-09-15"),   # "by the fifteenth", 24 Sep
])
def test_the_hard_sources_give_the_next_such_day(tmp_path: Path, label: str, future: str, past: str) -> None:
    """The #841 findings in the hard corpus: October, never the past day."""
    dates = _hard_dates(tmp_path, label)
    assert future in dates and past not in dates, (label, dates)


@pytest.mark.xfail(strict=True, reason=(
    "Gap, measured 2026-10-04 on qwen3.8-27b: 'T. Wierzbicki confirmed the sensor batch ships on the "
    "twentieth' (note of 2026-09-23) still gives 2026-09-20. The prompt line gives both dates; the model "
    "takes the tense of 'confirmed'. The first-person line ('I confirm ... ships on the twentieth', date "
    "case 'ships') gives 2026-10-20. Two more wordings (a reported-speech example; a shorter rule) did not "
    "fix it and gave empty answers on other date cases."
))
def test_the_supplier_note_gives_the_next_such_day(tmp_path: Path) -> None:
    dates = _hard_dates(tmp_path, "n-supplier")
    assert "2026-10-20" in dates and "2026-09-20" not in dates, dates


def test_no_entity_is_named_after_a_meeting_title(tmp_path: Path) -> None:
    """Astra, #845: a prompt rule on titles made the decision title "Offline
    first for forms" a project entity.  No project entity is a source title."""
    from holdspeak.memory.entities import fold
    from holdspeak.memory.extract import extract_pending

    from .corpus import (
        ARTIFACTS, DESK_DECISIONS, HARD_MEETINGS, HARD_NOTES, HARD_THREADS, MEETINGS, NOTES, THREADS,
    )
    from .engines import FixtureExtractor

    db, _refs = _hard_desk(tmp_path)
    extract_pending(db, FixtureExtractor(bench.FACTS, bench.HARD_FACTS))
    _generation, entities = db.memory_index.entities()
    projects = {str(entity["name_key"]) for entity in entities if entity["kind"] == "project"}
    titles = {
        fold(row[2])
        for rows in (NOTES, ARTIFACTS, MEETINGS, DESK_DECISIONS, THREADS, HARD_NOTES, HARD_MEETINGS, HARD_THREADS)
        for row in rows
    }
    assert not projects & titles, projects & titles


def test_hard_relation_names_stay_apart(tmp_path: Path) -> None:
    """The negative: "John Whitfield" and "Jane Whitfield" are two entities
    (the per-token guard), and each question ranks its own person first in
    the walk."""
    from holdspeak.memory.entities import fold
    from holdspeak.memory.extract import extract_pending

    from .engines import FixtureExtractor

    db, refs = _hard_desk(tmp_path)
    extract_pending(db, FixtureExtractor(bench.FACTS, bench.HARD_FACTS))
    _generation, entities = db.memory_index.entities()
    people = {
        str(entity["id"]): {str(entity["name_key"])} | {fold(alias) for alias in json.loads(entity["aliases_json"] or "[]")}
        for entity in entities if entity["kind"] == "person"
    }
    john = [entity for entity, names in people.items() if "john whitfield" in names]
    jane = [entity for entity, names in people.items() if "jane whitfield" in names]
    assert len(john) == 1 and len(jane) == 1 and john != jane, people

    by_id = {question["id"]: question for question in bench.load_hard_relation_questions()}
    jane_walk = _walk_alone(db, by_id["r14"])
    assert jane_walk[0] == refs["m-jane-w"], jane_walk
    for label in by_id["r14"]["reject"]:
        assert refs[label] not in jane_walk[:1]
        if refs[label] in jane_walk:
            assert jane_walk.index(refs[label]) > jane_walk.index(refs["m-jane-w"])
    john_walk = _walk_alone(db, by_id["r13"])
    assert john_walk[0] == refs["m-john-w"], john_walk


@pytest.mark.xfail(strict=True, reason=(
    "Gap, measured 2026-10-04 (EXTRACTOR_VERSION 2, qwen3.8-27b): with no title rule "
    "the model leaves 'Kestrel' out of the facts of m-kestrel and th-kestrel, so the "
    "walk alone finds neither for r09. A title rule fixed it but invented projects "
    "from meeting titles (Astra, #845). With vectors on, r09 is complete."
))
def test_hard_relation_kestrel_is_complete_by_the_walk(tmp_path: Path) -> None:
    from holdspeak.memory.extract import extract_pending

    from .engines import FixtureExtractor

    db, refs = _hard_desk(tmp_path)
    extract_pending(db, FixtureExtractor(bench.FACTS, bench.HARD_FACTS))
    r09 = next(question for question in bench.load_hard_relation_questions() if question["id"] == "r09")
    got = bench.run(db, refs, questions=[r09])["ranked"]["r09"][:5]
    assert {refs[label] for label in r09["expect"]} <= set(got), got


@pytest.mark.xfail(strict=True, reason=(
    "Gap, measured 2026-10-04: 'T. Wierzbicki' (n-supplier) stays its own entity. "
    "Resolver score 0.585 < 0.6: name 0.5 x 0.83, no shared neighbour (the model "
    "lists 'sensor batch' on the note's fact but not on Tomasz's fact), time 0.2 x 6/7 "
    "(seen 2026-09-23 against 2026-09-24). On the same day it would join (0.614)."
))
def test_hard_relation_alias_joins_the_full_name(tmp_path: Path) -> None:
    """r11: the question says "Tomasz"; n-supplier says only "T. Wierzbicki";
    the full name is only in m-corvid's title.  The walk reaches n-supplier
    only when the two mentions are one entity."""
    from holdspeak.memory.entities import fold
    from holdspeak.memory.extract import extract_pending

    from .engines import FixtureExtractor

    db, refs = _hard_desk(tmp_path)
    extract_pending(db, FixtureExtractor(bench.FACTS, bench.HARD_FACTS))
    _generation, entities = db.memory_index.entities()
    tomasz = [
        {str(entity["name_key"])} | {fold(alias) for alias in json.loads(entity["aliases_json"] or "[]")}
        for entity in entities
        if entity["kind"] == "person" and "wierzbicki" in str(entity["name_key"])
    ]
    assert tomasz == [{"tomasz wierzbicki", "t wierzbicki"}], tomasz
    r11 = next(question for question in bench.load_hard_relation_questions() if question["id"] == "r11")
    assert refs["n-supplier"] in _walk_alone(db, r11)
