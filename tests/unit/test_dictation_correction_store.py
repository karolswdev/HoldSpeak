"""HS-39-02: session correction-memory store tests.

HS-40-02 adds the optional-persistence cases (load-on-construct, write-through,
survive-a-restart, no-repo-byte-identical).
"""

from __future__ import annotations

import shutil
import tempfile
import threading
from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.plugins.dictation.corrections import (
    CorrectionStore,
    best_match_in,
    similarity,
)


def test_record_and_recent_roundtrip():
    store = CorrectionStore()
    assert store.record("intent", "fix the cli thing", "code_exercise") is True
    assert len(store) == 1
    recent = store.recent("intent")
    assert recent[0].kind == "intent"
    assert recent[0].value == "code_exercise"
    assert recent[0].key == "fix the cli thing"


def test_record_rejects_invalid_kind_or_empty():
    store = CorrectionStore()
    assert store.record("bogus", "text", "value") is False
    assert store.record("intent", "   ", "value") is False
    assert store.record("intent", "text", "") is False
    assert len(store) == 0


def test_record_rejects_secret_like_gist():
    store = CorrectionStore()
    assert store.record("intent", "my key is sk-abcdef0123456789abcd", "code_exercise") is False
    assert len(store) == 0


def test_ring_evicts_oldest_past_cap():
    store = CorrectionStore(cap=3)
    for i in range(5):
        store.record("intent", f"utterance number {i}", f"block_{i}")
    assert len(store) == 3
    values = [c.value for c in store.recent("intent")]  # newest-first
    assert values == ["block_4", "block_3", "block_2"]


def test_gist_is_length_bounded():
    store = CorrectionStore()
    store.record("intent", "x " * 500, "block")
    assert len(store.recent("intent")[0].key) <= 200


def test_similarity_bounds():
    assert similarity("fix the cli", "fix the cli") == 1.0
    assert similarity("fix the cli", "quarterly budget review") == 0.0
    assert 0.0 < similarity("fix the cli bug", "fix the cli now") < 1.0


def test_best_match_prefers_recent_on_tie():
    store = CorrectionStore()
    store.record("intent", "fix the cli", "old_block")
    store.record("intent", "fix the cli", "new_block")  # identical key, newer
    match = best_match_in(store.snapshot(), "intent", "fix the cli", min_similarity=0.5)
    assert match is not None
    assert match.value == "new_block"


def test_best_match_respects_kind_and_threshold():
    store = CorrectionStore()
    store.record("target", "fix the cli", "codex_cli")
    # Wrong kind → no intent match.
    assert best_match_in(store.snapshot(), "intent", "fix the cli", min_similarity=0.5) is None
    # Below threshold → no match.
    assert best_match_in(store.snapshot(), "target", "totally different words here", min_similarity=0.5) is None
    # Right kind + similar → match.
    assert best_match_in(store.snapshot(), "target", "fix the cli", min_similarity=0.5) is not None


def test_thread_safe_concurrent_records():
    store = CorrectionStore(cap=1000)

    def worker(start: int) -> None:
        for i in range(100):
            store.record("intent", f"phrase {start}-{i}", f"block_{start}_{i}")

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(store) == 800  # 8 workers * 100, no lost updates / corruption


# ── HS-40-02: optional persistence ────────────────────────────────────


@pytest.fixture
def repo():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "store.db")
    yield database.dictation_corrections
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_record_writes_through_to_repository(repo):
    store = CorrectionStore(repository=repo)
    assert store.record("intent", "fix the cli thing", "code_exercise") is True
    # In-memory ring updated…
    assert len(store) == 1
    # …and the durable repository persisted it.
    persisted = repo.recent_corrections()
    assert len(persisted) == 1
    assert persisted[0].kind == "intent"
    assert persisted[0].gist == "fix the cli thing"
    assert persisted[0].value == "code_exercise"


def test_secret_and_invalid_are_not_persisted(repo):
    store = CorrectionStore(repository=repo)
    assert store.record("intent", "my key is sk-abcdef0123456789abcd", "code_exercise") is False
    assert store.record("bogus", "text", "value") is False
    assert len(store) == 0
    assert repo.recent_corrections() == []


def test_store_loads_recent_on_construction(repo):
    repo.record_correction(kind="intent", gist="seeded utterance", value="code_exercise")
    repo.record_correction(kind="target", gist="route this", value="codex_cli")
    store = CorrectionStore(repository=repo)
    assert len(store) == 2
    # Newest-first, and the gist round-tripped as `Correction.key`.
    keys = [c.key for c in store.recent()]
    assert "seeded utterance" in keys and "route this" in keys


def test_survives_a_simulated_restart(repo):
    """A fresh store over the same repo sees corrections the old store made."""
    old = CorrectionStore(repository=repo)
    old.record("intent", "remember the cli fix", "code_exercise")
    # Simulate a process restart: a brand-new store, same durable repo.
    restarted = CorrectionStore(repository=repo)
    assert len(restarted) == 1
    match = best_match_in(restarted.snapshot(), "intent", "remember the cli fix", min_similarity=0.5)
    assert match is not None
    assert match.value == "code_exercise"


def test_load_respects_cap_newest_first(repo):
    for i in range(5):
        repo.record_correction(kind="intent", gist=f"utterance number {i}", value=f"block_{i}")
    store = CorrectionStore(cap=3, repository=repo)
    assert len(store) == 3
    values = [c.value for c in store.recent("intent")]  # newest-first
    assert values == ["block_4", "block_3", "block_2"]
