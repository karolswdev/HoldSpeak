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
