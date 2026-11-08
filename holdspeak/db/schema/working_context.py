"""Scoped working context, context dependents and the memory FTS corpora.

Part 5 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- ── HS-200-10: scoped working context ────────────────────────────────────
-- These three tables are declared BEFORE the notes FTS triggers below on
-- purpose.  `notes_memory_ai` / `notes_memory_au` name `context_promotions`
-- in their bodies, and SQLite resolves a trigger body's table names lazily:
-- `CREATE TRIGGER` succeeds naming a missing table and the FIRST
-- `INSERT INTO notes` then raises `no such table: main.context_promotions`
-- -- a desk that cannot save a note.  Within one `executescript(SCHEMA_SQL)`
-- there is no window either way, but declaring the tables first removes even
-- the theoretical one (settled design, "cannot promise" #6, observed).

-- HS-200-10: one promotion of one Interview fact into one canonical record.
-- The quote is a LOCATOR + HASH, never a copy: provenance stays provable, and
-- deleting the source message leaves no copy of it in this row.  It does NOT
-- unwrite the promoted record -- the canonical Note keeps the quoted words on
-- purpose, which is why _revoke_promotion returns record_retained: True.
-- (counsel-on-built F4: the earlier wording read as "revoke deletes my words".)
-- The excerpt-locator idea is
-- borrowed from project_evidence_links.excerpt_locator_json, whose writer has
-- zero references anywhere; this table is deliberately NOT project-scoped,
-- because a promotion must work on a desk with no Project.
-- `promotion_id` and, in new-Note mode, `target_ref` are BOTH deterministic
-- from (thread_id, fact_id) -- the generate_pobs_id pattern
-- (holdspeak/project_contracts.py) -- so a double-click collides here instead
-- of minting two Notes.
-- `target_kind` and `disclosure_state` carry NO CHECK: widening a SQLite CHECK
-- is a table rebuild and stories 11/13/17/20 widen this vocabulary.  The
-- service validates instead.
CREATE TABLE IF NOT EXISTS context_promotions (
    promotion_id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    source_message_id TEXT NOT NULL,
    quote_sha256 TEXT NOT NULL,
    quote_locator_json TEXT NOT NULL DEFAULT '{}',
    target_kind TEXT NOT NULL DEFAULT 'note',
    target_ref TEXT NOT NULL,
    target_revision_label TEXT NOT NULL DEFAULT '',
    target_content_sha256 TEXT NOT NULL DEFAULT '',
    disclosure_state TEXT NOT NULL DEFAULT 'active',
    request_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (thread_id, fact_id, target_ref)
);
-- idx_context_promotions_target is what makes F0's trigger guard and the
-- multi-promotion revoke rule index seeks rather than table scans.
CREATE INDEX IF NOT EXISTS idx_context_promotions_target
    ON context_promotions(target_ref);
CREATE INDEX IF NOT EXISTS idx_context_promotions_source
    ON context_promotions(source_message_id);

-- HS-200-10: the suppression side-table.  Copies calendar_event_link_suppressions:
-- keyed by the DURABLE identity, so re-typing the quote cannot resurrect a
-- promotion the owner revoked.  Forgetting is not suppressing.
CREATE TABLE IF NOT EXISTS context_promotion_suppressions (
    thread_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    target_ref TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT 'revoked',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (thread_id, fact_id, target_ref)
);

-- HS-200-10: the REVERSE index.  refinement_attachment_visible is keyed
-- (thought_id, attachment_revision, ordinal) with the ref only a payload
-- column, so "who consumes note:n1?" is a scan of every revision of every
-- Thought, and revisions are never pruned.  One row per (record, consumer)
-- keeps this table bounded while attachment revisions accumulate.
-- `consumer_kind` carries NO CHECK: stories 11, 13, 17 and 20 add `brief`,
-- `project_facet`, `cadence_run` and `prepared_assignment`.
-- `stale_reason` uses C4's shipped coverage words and only three -- `stale`,
-- `unavailable`, `forbidden` -- with '' meaning fresh.
CREATE TABLE IF NOT EXISTS context_dependents (
    canonical_ref TEXT NOT NULL,
    consumer_kind TEXT NOT NULL,
    consumer_id TEXT NOT NULL,
    consumer_revision INTEGER NOT NULL DEFAULT 0,
    bound_manifest_sha256 TEXT NOT NULL DEFAULT '',
    bound_at TEXT NOT NULL,
    stale_since TEXT,
    stale_reason TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (canonical_ref, consumer_kind, consumer_id)
);
CREATE INDEX IF NOT EXISTS idx_context_dependents_consumer
    ON context_dependents(consumer_kind, consumer_id);

-- HS-109-04: one retrieval contract, three separately ranked FTS corpora.
-- Internal-content tables retain stable text source ids directly; this avoids
-- pretending the stores' TEXT primary keys are FTS integer content_rowids.
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_memory_fts USING fts5(
    source_id UNINDEXED, text, rationale
);
CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_memory_fts USING fts5(
    source_id UNINDEXED, title, body_markdown
);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_memory_fts USING fts5(
    source_id UNINDEXED, title, body_markdown
);

CREATE TRIGGER IF NOT EXISTS decisions_memory_ai AFTER INSERT ON decisions
WHEN NEW.deleted = 0 AND NEW.source_state = 'linked' BEGIN
    INSERT INTO decisions_memory_fts(source_id,text,rationale)
    VALUES(NEW.id,NEW.text,COALESCE(NEW.rationale,''));
END;
CREATE TRIGGER IF NOT EXISTS decisions_memory_ad AFTER DELETE ON decisions BEGIN
    DELETE FROM decisions_memory_fts WHERE source_id=OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS decisions_memory_au AFTER UPDATE ON decisions BEGIN
    DELETE FROM decisions_memory_fts WHERE source_id=OLD.id;
    INSERT INTO decisions_memory_fts(source_id,text,rationale)
    SELECT NEW.id,NEW.text,COALESCE(NEW.rationale,'')
    WHERE NEW.deleted=0 AND NEW.source_state='linked';
END;

CREATE TRIGGER IF NOT EXISTS artifacts_memory_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_memory_fts(source_id,title,body_markdown)
    VALUES(NEW.id,NEW.title,NEW.body_markdown);
END;
CREATE TRIGGER IF NOT EXISTS artifacts_memory_ad AFTER DELETE ON artifacts BEGIN
    DELETE FROM artifacts_memory_fts WHERE source_id=OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS artifacts_memory_au AFTER UPDATE ON artifacts BEGIN
    DELETE FROM artifacts_memory_fts WHERE source_id=OLD.id;
    INSERT INTO artifacts_memory_fts(source_id,title,body_markdown)
    VALUES(NEW.id,NEW.title,NEW.body_markdown);
END;

-- HS-200-10 (F0/L1): reachable by reference, never by relevance.  A note
-- carrying a promotion never enters the relevance corpus AT ALL -- not even
-- transiently, because the promotion transaction writes the deterministic
-- `context_promotions` row BEFORE it upserts the note, so `notes_memory_ai`
-- already sees it.  The guard keys on the EXISTENCE of a promotion, not on
-- `disclosure_state`: once a record has been minted or appended to by
-- promotion it never joins the pool, revoked or not.  Both writers carry the
-- predicate so every later write re-evaluates and the state self-heals.
-- These two bodies are REVISED, not new; older databases are brought forward
-- by `_refresh_revised_triggers` (holdspeak/db/reconcile.py).
CREATE TRIGGER IF NOT EXISTS notes_memory_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_memory_fts(source_id,title,body_markdown)
    SELECT NEW.id,NEW.title,NEW.body_markdown
     WHERE NEW.deleted=0
       AND NOT EXISTS (SELECT 1 FROM context_promotions
                        WHERE target_ref = 'note:' || NEW.id);
END;
CREATE TRIGGER IF NOT EXISTS notes_memory_ad AFTER DELETE ON notes BEGIN
    DELETE FROM notes_memory_fts WHERE source_id=OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS notes_memory_au AFTER UPDATE ON notes BEGIN
    DELETE FROM notes_memory_fts WHERE source_id=OLD.id;
    INSERT INTO notes_memory_fts(source_id,title,body_markdown)
    SELECT NEW.id,NEW.title,NEW.body_markdown
     WHERE NEW.deleted=0
       AND NOT EXISTS (SELECT 1 FROM context_promotions
                        WHERE target_ref = 'note:' || NEW.id);
END;

-- HS-200-10 (AC3): the push half of the reverse index.  A trigger cannot
-- hash, so the mark is deliberately conservative -- over-marking says "check
-- this", under-marking is the breach.  COALESCE keeps the FIRST staleness
-- time.  The WHERE hits the PK's leading column, so a note with no consumers
-- costs one index probe and matches zero rows.
--
-- The lattice, and `forbidden` is TERMINAL:
--   ''  (fresh) -> 'stale'       cleared only by a rebind at the reconcile point
--               -> 'unavailable' cleared by a rebind, OR downgraded to 'stale'
--                                by an UNDELETE (see below)
--               -> 'forbidden'   see the note below: nothing in the product
--                                clears it, and one route wrongly does.
-- No trigger and no ordinary edit may leave `forbidden`.
--
-- TWO CORRECTIONS from counsel-on-built (2026-09-09); the code is right and an
-- earlier version of THIS COMMENT was wrong, so read it as the record.
--
-- 1. `unavailable` -> `stale` on an undelete is DELIBERATE.  The AU branch below
--    reaches 'stale' only when NEW.deleted = 0 -- the record genuinely came
--    back -- so the refresh a consumer would attempt CAN succeed.  This comment
--    used to say "cleared only by a rebind", which the trigger three lines down
--    contradicts.  What is NOT allowed is the reverse: `revoke_promotion` used
--    to overwrite `unavailable` with `stale` while the note was still deleted,
--    sending a consumer to refresh a record that is gone.  That was a real
--    defect and is fixed (interview_service.py preserves both marks now).
--
-- 2. `forbidden` is terminal in intent and LEAKS IN PRACTICE.  A detach deletes
--    the consumer's row outright, so a later re-attach re-inserts it with
--    stale_reason='' -- two ordinary clicks clear a revocation.  Pinned by
--    test_a_detach_then_reattach_currently_clears_a_standing_forbidden and
--    ruled on in story-10 B2: not closed on this commit because the fix
--    (deriving the mark from the record's own state) collides with the ratified
--    P0-2 test, and nothing in the product fences on this table yet.  This matters because
-- refinement_thought_service writes a working Note on EVERY accepted revision:
-- a downgrade here would turn a revocation into an ordinary refreshable
-- staleness on the very next save, and a consumer fencing on `forbidden`
-- would dispatch.
CREATE TRIGGER IF NOT EXISTS context_dependents_note_au AFTER UPDATE ON notes BEGIN
    UPDATE context_dependents
       SET stale_since  = COALESCE(stale_since, datetime('now')),
           stale_reason = CASE WHEN stale_reason = 'forbidden' THEN 'forbidden'
                               WHEN NEW.deleted = 1            THEN 'unavailable'
                               ELSE 'stale' END
     WHERE canonical_ref = 'note:' || NEW.id;
END;
CREATE TRIGGER IF NOT EXISTS context_dependents_note_ad AFTER DELETE ON notes BEGIN
    UPDATE context_dependents
       SET stale_since  = COALESCE(stale_since, datetime('now')),
           stale_reason = CASE WHEN stale_reason = 'forbidden' THEN 'forbidden'
                               ELSE 'unavailable' END
     WHERE canonical_ref = 'note:' || OLD.id;
END;
"""
