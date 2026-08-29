"""HS-150-01: Thread ledger repository tests.

Covers: tree/leaf path, siblings n/m, soft-delete removes from FTS via trigger,
extend_part_text append-only, freeze_refs, token totals, import idempotency,
reconcile idempotent on a fresh DB twice.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.db.threads import (
    Thread,
    ThreadMessage,
    ThreadMessagePart,
    ThreadRef,
    ThreadRepository,
)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Fresh isolated database."""
    return Database(tmp_path / "test_threads.db")


# ---------------------------------------------------------------------------
# Thread CRUD
# ---------------------------------------------------------------------------

class TestThreadCRUD:
    def test_create_and_get(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        thread = repo.create_thread(title="Test thread", recipe_id="r1")
        assert thread.id.startswith("th_")
        assert thread.title == "Test thread"
        assert thread.recipe_id == "r1"
        assert thread.deleted_at is None
        assert thread.token_in == 0
        assert thread.token_out == 0

        fetched = repo.get(thread.id)
        assert fetched is not None
        assert fetched.id == thread.id
        assert fetched.title == "Test thread"

    def test_list_excludes_deleted(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        t1 = repo.create_thread(title="A")
        t2 = repo.create_thread(title="B")
        assert len(repo.list()) == 2

        repo.soft_delete(t1.id)
        listed = repo.list()
        assert len(listed) == 1
        assert listed[0].id == t2.id

    def test_patch(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        thread = repo.create_thread(title="Old")
        patched = repo.patch(thread.id, title="New", profile_override="prof1")
        assert patched is not None
        assert patched.title == "New"
        assert patched.profile_override == "prof1"


# ---------------------------------------------------------------------------
# Message tree: append, branch (sibling), list_path, siblings
# ---------------------------------------------------------------------------

class TestMessageTree:
    def test_linear_path(self, db: Database) -> None:
        """append -> append -> list_path returns root-to-leaf."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Linear")
        m1 = repo.append_message(t.id, role="user")
        m2 = repo.append_message(t.id, role="assistant", parent_id=m1.id)
        m3 = repo.append_message(t.id, role="user", parent_id=m2.id)

        path = repo.list_path(t.id)
        assert len(path) == 3
        assert path[0].id == m1.id
        assert path[1].id == m2.id
        assert path[2].id == m3.id

    def test_branch_newest_leaf(self, db: Database) -> None:
        """Branch = sibling row sharing parent_id; list_path picks newest leaf."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Branch")
        m1 = repo.append_message(t.id, role="user")
        # First reply.
        m2a = repo.append_message(t.id, role="assistant", parent_id=m1.id)
        # Second reply (branch / sibling of m2a).
        time.sleep(0.01)  # Ensure distinct created_at.
        m2b = repo.append_message(t.id, role="assistant", parent_id=m1.id)

        path = repo.list_path(t.id)
        # Newest leaf is m2b (the branch), so path = [m1, m2b].
        assert len(path) == 2
        assert path[0].id == m1.id
        assert path[1].id == m2b.id

    def test_siblings_n_m(self, db: Database) -> None:
        """siblings(message_id) returns (n, m) for sibling picker."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Siblings")
        m1 = repo.append_message(t.id, role="user")
        m2a = repo.append_message(t.id, role="assistant", parent_id=m1.id)
        time.sleep(0.01)
        m2b = repo.append_message(t.id, role="assistant", parent_id=m1.id)
        time.sleep(0.01)
        m2c = repo.append_message(t.id, role="assistant", parent_id=m1.id)

        assert repo.siblings(m2a.id) == (1, 3)
        assert repo.siblings(m2b.id) == (2, 3)
        assert repo.siblings(m2c.id) == (3, 3)
        # Root message has no siblings -> (1, 1).
        assert repo.siblings(m1.id) == (1, 1)

    def test_siblings_root_messages(self, db: Database) -> None:
        """Multiple root messages (no parent_id) are siblings of each other."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Roots")
        r1 = repo.append_message(t.id, role="user")
        time.sleep(0.01)
        r2 = repo.append_message(t.id, role="user")

        assert repo.siblings(r1.id) == (1, 2)
        assert repo.siblings(r2.id) == (2, 2)


# ---------------------------------------------------------------------------
# Soft-delete removes from FTS via trigger
# ---------------------------------------------------------------------------

class TestSoftDeleteFTS:
    def test_soft_delete_message_removes_from_fts(self, db: Database) -> None:
        """Soft-deleting a message removes its parts from FTS (trigger M3)."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="FTS delete test")
        m = repo.append_message(t.id, role="user")
        repo.append_part(m.id, kind="text", text="unique_searchable_xylophone_text")

        # Should be findable before delete.
        results = repo.search("unique_searchable_xylophone_text")
        assert len(results) > 0
        assert results[0]["thread_id"] == t.id

        # Soft-delete the message.
        now = time.time()
        with db._connection() as conn:
            conn.execute(
                "UPDATE thread_messages SET deleted_at=?, updated_at=? WHERE id=?",
                (now, now, m.id),
            )

        # Should NOT be findable after delete.
        results_after = repo.search("unique_searchable_xylophone_text")
        assert len(results_after) == 0

    def test_soft_delete_thread_removes_from_fts(self, db: Database) -> None:
        """Soft-deleting a thread cascades message soft-deletes, clearing FTS."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Thread FTS")
        m = repo.append_message(t.id, role="assistant")
        repo.append_part(m.id, kind="text", text="quixotic_thread_delete_token")

        assert len(repo.search("quixotic_thread_delete_token")) > 0

        repo.soft_delete(t.id)

        assert len(repo.search("quixotic_thread_delete_token")) == 0

    def test_search_never_returns_deleted(self, db: Database) -> None:
        """search() never returns content from deleted messages (belt + trigger)."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Search test")
        m1 = repo.append_message(t.id, role="user")
        repo.append_part(m1.id, kind="text", text="findme_alpha_word")
        m2 = repo.append_message(t.id, role="assistant", parent_id=m1.id)
        repo.append_part(m2.id, kind="text", text="findme_beta_word")

        # Both findable.
        assert len(repo.search("findme_alpha_word")) == 1
        assert len(repo.search("findme_beta_word")) == 1

        # Soft-delete m2 only.
        now = time.time()
        with db._connection() as conn:
            conn.execute(
                "UPDATE thread_messages SET deleted_at=?, updated_at=? WHERE id=?",
                (now, now, m2.id),
            )

        # m1 still findable, m2 not.
        assert len(repo.search("findme_alpha_word")) == 1
        assert len(repo.search("findme_beta_word")) == 0


# ---------------------------------------------------------------------------
# extend_part_text: append-only, one UPDATE
# ---------------------------------------------------------------------------

class TestExtendPartText:
    def test_append_only(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Extend")
        m = repo.append_message(t.id, role="assistant")
        p = repo.append_part(m.id, kind="text", text="Hello")

        repo.extend_part_text(p.id, " world")
        parts = repo.get_parts(m.id)
        assert len(parts) == 1
        assert parts[0].text == "Hello world"

        repo.extend_part_text(p.id, "!")
        parts2 = repo.get_parts(m.id)
        assert parts2[0].text == "Hello world!"

    def test_extend_from_null(self, db: Database) -> None:
        """extend_part_text works when text is initially NULL."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Null extend")
        m = repo.append_message(t.id, role="assistant")
        p = repo.append_part(m.id, kind="text")  # text=None (default).

        repo.extend_part_text(p.id, "first chunk")
        parts = repo.get_parts(m.id)
        assert parts[0].text == "first chunk"

    def test_extend_updates_fts(self, db: Database) -> None:
        """FTS index reflects extended text."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="FTS extend")
        m = repo.append_message(t.id, role="assistant")
        p = repo.append_part(m.id, kind="text", text="initial_xylophone_token")

        assert len(repo.search("initial_xylophone_token")) > 0

        repo.extend_part_text(p.id, " appended_zephyr_token")

        # New term should be findable.
        assert len(repo.search("appended_zephyr_token")) > 0


# ---------------------------------------------------------------------------
# freeze_refs
# ---------------------------------------------------------------------------

class TestFreezeRefs:
    def test_freeze_and_retrieve(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Refs test")
        m = repo.append_message(t.id, role="user")

        refs = repo.freeze_refs(t.id, m.id, [
            {"ref_kind": "meeting", "ref_id": "mtg_001", "version": "1",
             "frozen_json": {"title": "Monday standup"}},
            {"ref_kind": "note", "ref_id": "note_002"},
        ])

        assert len(refs) == 2
        assert refs[0].ref_kind == "meeting"
        assert refs[0].ref_id == "mtg_001"
        assert '"title"' in refs[0].frozen_json
        assert refs[1].ref_kind == "note"

        # get_refs returns them.
        all_refs = repo.get_refs(t.id)
        assert len(all_refs) == 2

    def test_thread_level_refs(self, db: Database) -> None:
        """Refs with message_id=None are thread-level (e.g. import_hash)."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Thread refs")

        refs = repo.freeze_refs(t.id, None, [
            {"ref_kind": "import_hash", "ref_id": "abc123"},
        ])

        assert len(refs) == 1
        assert refs[0].message_id is None
        assert refs[0].ref_kind == "import_hash"


# ---------------------------------------------------------------------------
# Token totals
# ---------------------------------------------------------------------------

class TestTokenTotals:
    def test_add_token_totals(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Tokens")
        assert t.token_in == 0
        assert t.token_out == 0

        repo.add_token_totals(t.id, token_in=100, token_out=50)
        t2 = repo.get(t.id)
        assert t2 is not None
        assert t2.token_in == 100
        assert t2.token_out == 50

        repo.add_token_totals(t.id, token_in=200, token_out=100)
        t3 = repo.get(t.id)
        assert t3 is not None
        assert t3.token_in == 300
        assert t3.token_out == 150

    def test_negative_totals_clamped(self, db: Database) -> None:
        """Negative values are clamped to 0 (no negative increments)."""
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Negative tokens")
        repo.add_token_totals(t.id, token_in=50, token_out=25)
        repo.add_token_totals(t.id, token_in=-10, token_out=-5)
        t2 = repo.get(t.id)
        assert t2 is not None
        assert t2.token_in == 50  # Not reduced.
        assert t2.token_out == 25


# ---------------------------------------------------------------------------
# Import idempotency (D7)
# ---------------------------------------------------------------------------

class TestImportIdempotency:
    def _make_payload(self) -> list[dict]:
        return [
            {
                "title": "Imported thread",
                "recipe_id": "recipe_1",
                "created_at": "2025-01-01T00:00:00Z",
                "messages": [
                    {"role": "user", "parts": [{"kind": "text", "text": "Hello bot"}]},
                    {"role": "assistant", "parts": [{"kind": "text", "text": "Hi there"}]},
                ],
            },
        ]

    def test_import_creates_thread(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        payload = self._make_payload()
        result = repo.import_threads(payload)
        assert len(result) == 1

        thread_id = list(result.values())[0]
        thread = repo.get(thread_id)
        assert thread is not None
        assert thread.title == "Imported thread"
        assert thread.recipe_id == "recipe_1"

        # Verify messages.
        path = repo.list_path(thread_id)
        assert len(path) == 2
        assert path[0].role == "user"
        assert path[1].role == "assistant"

    def test_import_idempotent(self, db: Database) -> None:
        """Same payload twice -> same thread ids (dedup by import_hash)."""
        repo: ThreadRepository = db.threads
        payload = self._make_payload()

        result1 = repo.import_threads(payload)
        result2 = repo.import_threads(payload)

        assert result1 == result2
        # Only one thread exists.
        assert len(repo.list()) == 1

    def test_import_different_payload_creates_new(self, db: Database) -> None:
        repo: ThreadRepository = db.threads

        payload1 = [{"title": "A", "recipe_id": "r1", "created_at": "t1",
                      "messages": [{"role": "user", "text": "hello"}]}]
        payload2 = [{"title": "B", "recipe_id": "r2", "created_at": "t2",
                      "messages": [{"role": "user", "text": "world"}]}]

        r1 = repo.import_threads(payload1)
        r2 = repo.import_threads(payload2)

        all_ids = set(r1.values()) | set(r2.values())
        assert len(all_ids) == 2

    def test_import_hash_stored_as_ref(self, db: Database) -> None:
        """The import_hash is stored as a thread_refs row of kind 'import_hash'."""
        repo: ThreadRepository = db.threads
        payload = self._make_payload()
        result = repo.import_threads(payload)
        thread_id = list(result.values())[0]

        refs = repo.get_refs(thread_id)
        import_refs = [r for r in refs if r.ref_kind == "import_hash"]
        assert len(import_refs) == 1
        assert import_refs[0].ref_id == list(result.keys())[0]


# ---------------------------------------------------------------------------
# Streaming lifecycle
# ---------------------------------------------------------------------------

class TestStreamingLifecycle:
    def test_mark_streaming_complete(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Stream")
        m = repo.append_message(t.id, role="assistant")
        assert not m.streaming

        repo.mark_streaming(m.id)
        m2 = repo.get_message(m.id)
        assert m2 is not None
        assert m2.streaming

        m3 = repo.complete_message(m.id, receipt_id="rcpt_1", stats_json='{"tokens": 42}')
        assert m3 is not None
        assert not m3.streaming
        assert m3.completed_at is not None
        assert m3.receipt_id == "rcpt_1"
        assert m3.stats_json == '{"tokens": 42}'

    def test_abort_message(self, db: Database) -> None:
        repo: ThreadRepository = db.threads
        t = repo.create_thread(title="Abort")
        m = repo.append_message(t.id, role="assistant")
        repo.mark_streaming(m.id)

        m2 = repo.abort_message(m.id)
        assert m2 is not None
        assert not m2.streaming
        assert m2.aborted_at is not None


# ---------------------------------------------------------------------------
# Reconcile idempotent
# ---------------------------------------------------------------------------

class TestReconcileIdempotent:
    def test_fresh_db_twice_same_shape(self, tmp_path: Path) -> None:
        """Creating a fresh DB twice produces the same schema shape."""
        import re
        import sqlite3

        def dump_shape(db_path: Path) -> str:
            Database(db_path)
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            ).fetchall()
            shape = "\n".join(
                f"{r['type']} {r['name']}: {re.sub(r'\\s+', ' ', (r['sql'] or '').strip())}"
                for r in rows
            )
            conn.close()
            return shape

        shape1 = dump_shape(tmp_path / "db1.db")
        shape2 = dump_shape(tmp_path / "db2.db")
        assert shape1 == shape2

    def test_reconcile_idempotent_on_existing(self, tmp_path: Path) -> None:
        """Opening a DB a second time (reconcile re-runs) does not change shape."""
        import re
        import sqlite3
        from holdspeak.db.reconcile import reconcile_schema

        db_path = tmp_path / "idempotent.db"
        Database(db_path)

        # Run reconcile again.
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        reconcile_schema(conn, db_path=db_path)

        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        shape_after = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows
        )
        conn.close()

        # Compare against a third fresh DB.
        db_path2 = tmp_path / "fresh2.db"
        Database(db_path2)
        conn2 = sqlite3.connect(str(db_path2))
        conn2.row_factory = sqlite3.Row
        rows2 = conn2.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        shape_fresh = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows2
        )
        conn2.close()

        assert shape_after == shape_fresh
