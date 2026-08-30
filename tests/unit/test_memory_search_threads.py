"""HS-150-07 thread corpus in MemoryRepository search."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from holdspeak.db import Database


def _seed_thread(
    db: Database,
    thread_id: str,
    title: str,
    parts: list[tuple[str, str, str]],
    *,
    updated_at: float | None = None,
    deleted_thread: bool = False,
) -> None:
    """Seed a thread with messages and parts for FTS tests.

    *parts* is a list of (message_id, role, text) triples.
    Each message gets one text part at ordinal 0.
    """
    now = updated_at or time.time()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO threads(id,title,created_at,updated_at,last_turn_at,deleted_at)"
            " VALUES (?,?,?,?,?,?)",
            (thread_id, title, now, now, now, now if deleted_thread else None),
        )
        for msg_id, role, text in parts:
            conn.execute(
                "INSERT INTO thread_messages(id,thread_id,role,created_at,updated_at)"
                " VALUES (?,?,?,?,?)",
                (msg_id, thread_id, role, now, now),
            )
            part_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO thread_message_parts(id,message_id,ordinal,kind,text)"
                " VALUES (?,?,0,'text',?)",
                (part_id, msg_id, text),
            )


def _soft_delete_message(db: Database, message_id: str) -> None:
    with db._connection() as conn:
        conn.execute(
            "UPDATE thread_messages SET deleted_at=? WHERE id=?",
            (time.time(), message_id),
        )


# -------------------------------------------------------------------
# 1. A seeded thread is found by a word in an assistant part.
# -------------------------------------------------------------------
def test_thread_found_by_assistant_part(tmp_path: Path) -> None:
    db = Database(tmp_path / "thread_search.db")
    _seed_thread(
        db,
        "t1",
        "Jenkins pipeline",
        [("m1", "user", "why is the build red"),
         ("m2", "assistant", "the jenkins pipeline has a flaky stage")],
    )
    hits = db.memory.search("jenkins", kinds=["thread"]).hits
    assert len(hits) == 1
    hit = hits[0]
    assert hit.kind == "thread"
    assert hit.source_ref.startswith("thread:t1")
    assert "t1" in hit.source_ref
    assert hit.title == "Jenkins pipeline"
    assert "jenkins" in hit.snippet.lower() or "<mark>" in hit.snippet


# -------------------------------------------------------------------
# 2. Soft-deleted message text never surfaces.
# -------------------------------------------------------------------
def test_soft_deleted_message_excluded(tmp_path: Path) -> None:
    db = Database(tmp_path / "thread_deleted.db")
    _seed_thread(
        db,
        "t2",
        "Build secrets",
        [("m3", "assistant", "kubernetes deployment token leaked")],
    )
    assert db.memory.search("kubernetes", kinds=["thread"]).total == 1
    _soft_delete_message(db, "m3")
    assert db.memory.search("kubernetes", kinds=["thread"]).total == 0


# -------------------------------------------------------------------
# 3. Deleted thread is excluded.
# -------------------------------------------------------------------
def test_deleted_thread_excluded(tmp_path: Path) -> None:
    db = Database(tmp_path / "thread_del_thread.db")
    _seed_thread(
        db,
        "t3",
        "Archived conversation",
        [("m4", "assistant", "terraform state drift detected")],
        deleted_thread=True,
    )
    assert db.memory.search("terraform", kinds=["thread"]).total == 0


# -------------------------------------------------------------------
# 4. Interleave: threads merge with notes without breaking ranking.
# -------------------------------------------------------------------
def test_interleave_threads_with_notes(tmp_path: Path) -> None:
    db = Database(tmp_path / "interleave.db")
    # Seed a note about retry
    db.notes.upsert(
        note_id="n1",
        title="Retry config",
        body_markdown="retry policy budget allocation",
        last_modified="2026-01-01T00:00:00",
        created_at="2026-01-01T00:00:00",
    )
    with db._connection() as conn:
        conn.execute("UPDATE notes SET updated_at='2026-01-01T00:00:00' WHERE id='n1'")

    # Seed a thread about retry
    _seed_thread(
        db,
        "t4",
        "Retry discussion",
        [("m5", "assistant", "we need a retry policy for the gateway")],
        updated_at=1767225600.0,  # 2026-01-01 00:00:00 UTC
    )

    all_hits = db.memory.search("retry").hits
    kinds_found = {hit.kind for hit in all_hits}
    assert "note" in kinds_found
    assert "thread" in kinds_found
    # Interleave puts rank-1 of each kind in the first tier
    assert all_hits[0].kind_rank == 1
    assert all(0.0 <= hit.normalized_score <= 1.0 for hit in all_hits)
    assert [hit.rank for hit in all_hits] == list(range(1, len(all_hits) + 1))


# -------------------------------------------------------------------
# 5. source_ref carries message_id after '#'.
# -------------------------------------------------------------------
def test_source_ref_carries_message_id(tmp_path: Path) -> None:
    db = Database(tmp_path / "thread_ref.db")
    _seed_thread(
        db,
        "t5",
        "Deployment checklist",
        [("m6", "user", "run the migration"),
         ("m7", "assistant", "canary deployment started successfully")],
    )
    hits = db.memory.search("canary", kinds=["thread"]).hits
    assert len(hits) == 1
    ref = hits[0].source_ref
    # Format: thread:<thread_id>#<message_id>
    assert ref.startswith("thread:t5#")
    message_id = ref.split("#", 1)[1]
    assert message_id == "m7"


# -------------------------------------------------------------------
# 6. Multiple matching parts in one thread produce a single hit.
# -------------------------------------------------------------------
def test_multiple_parts_one_hit(tmp_path: Path) -> None:
    db = Database(tmp_path / "thread_dedup.db")
    _seed_thread(
        db,
        "t6",
        "Database tuning",
        [("m8", "user", "postgres vacuum settings"),
         ("m9", "assistant", "postgres vacuum should run nightly")],
    )
    hits = db.memory.search("postgres", kinds=["thread"]).hits
    assert len(hits) == 1
    assert hits[0].source_ref.startswith("thread:t6#")


# -------------------------------------------------------------------
# 7. kind="thread" accepted by _normalize_kinds.
# -------------------------------------------------------------------
def test_normalize_kinds_accepts_thread() -> None:
    from holdspeak.db.memory import MemoryRepository
    assert "thread" in MemoryRepository._normalize_kinds(["thread"])
    assert "thread" in MemoryRepository._normalize_kinds(None)  # default


# -------------------------------------------------------------------
# 8. MCP tool memory.search with kind="thread" works end-to-end.
# -------------------------------------------------------------------
def test_mcp_memory_search_thread_kind(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "mcp_thread.db")
    _seed_thread(
        db,
        "t7",
        "CI pipeline",
        [("m10", "assistant", "sonarqube analysis complete for the branch")],
    )

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.memory_service import MemoryService
    svc = MemoryService(db=db)
    principal = Principal(PrincipalKind.OWNER, "test-owner")
    result = svc.search(principal, "sonarqube", kind="thread")
    assert result["page"]["total"] == 1
    assert result["hits"][0]["kind"] == "thread"
    assert "sonarqube" in result["hits"][0]["snippet"].lower() or "<mark>" in result["hits"][0]["snippet"]
