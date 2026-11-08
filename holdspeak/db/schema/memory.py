"""The native memory index: sources, chunks, embeddings, facts, observations, pages, jobs.

Part 16 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- The native memory index, slice 1 (docs/internal/MEMORY-DESIGN.md §2).
-- Derived rows only: `holdspeak memory rebuild` drops and rebuilds them from
-- the source tables.  The source tables do not change.
--
-- The ledger: one row per source object memory has seen.
CREATE TABLE IF NOT EXISTS memory_sources (
    source_ref TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    occurred_at TEXT,
    content_sha TEXT NOT NULL,
    chunker_version INTEGER NOT NULL,
    extracted_sha TEXT,
    extractor_version INTEGER,
    state TEXT NOT NULL DEFAULT 'live',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory_chunks (
    id TEXT PRIMARY KEY,
    source_ref TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    anchor TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    occurred_at TEXT,
    content_sha TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_source
    ON memory_chunks(source_ref, ordinal);
-- Keyword search over the chunks (MEMORY-DESIGN.md §3.2): the keyword
-- retriever for the kinds that have no older FTS table, so they are found
-- with no embedding engine.  rowid = memory_chunks.rowid; the write that
-- replaces a source's chunks writes these rows in the same transaction
-- (db/memory_index.py).  A read joins on rowid AND chunk_id, so a row whose
-- rowid no longer names its chunk is never served.
CREATE VIRTUAL TABLE IF NOT EXISTS memory_chunks_fts USING fts5(
    text, chunk_id UNINDEXED, source_ref UNINDEXED
);
-- One table of vectors.  `vector` is float32, unit length, `dim` values.
CREATE TABLE IF NOT EXISTS memory_embeddings (
    item_kind TEXT NOT NULL,
    item_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    dim INTEGER NOT NULL,
    vector BLOB NOT NULL,
    content_sha TEXT NOT NULL,
    PRIMARY KEY (item_kind, item_id, model_id)
);
-- The index generation: one row, moved in the SAME transaction as every write
-- to the three tables above.  A reader's cached vector matrix is good only
-- for the generation it was built at, whichever handle or process wrote.
CREATE TABLE IF NOT EXISTS memory_index_state (
    key TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
-- Memory slice 3 (MEMORY-DESIGN.md §2, §3.1 steps 5-6): facts that the
-- `memory.extract` engine reads from the chunks of a source, the entities they
-- name, and the links between the two.  Derived rows: the extract job writes a
-- source's facts, resolves their entities, retires the old facts and stamps
-- `memory_sources.extracted_sha` in ONE transaction.  No People-store id is
-- ever written here (§5).
CREATE TABLE IF NOT EXISTS memory_entities (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    first_seen TEXT,
    last_seen TEXT,
    mention_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_memory_entities_key
    ON memory_entities(kind, name_key);
CREATE TABLE IF NOT EXISTS memory_facts (
    id TEXT PRIMARY KEY,
    source_ref TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    subject_entity_id TEXT,
    predicate TEXT NOT NULL,
    object_entity_id TEXT,
    object_text TEXT NOT NULL DEFAULT '',
    occurred_start TEXT,
    occurred_end TEXT,
    mentioned_at TEXT,
    confidence REAL NOT NULL DEFAULT 0.5,
    extractor_version INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'live',
    consolidated_at TEXT,
    -- The chunk the fact was read from, as it was: a fact serves only while
    -- that chunk is live with this hash and this anchor.
    chunk_sha TEXT NOT NULL DEFAULT '',
    anchor TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_memory_facts_source
    ON memory_facts(source_ref, state);
CREATE TABLE IF NOT EXISTS memory_fact_entities (
    fact_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (fact_id, entity_id, role)
);
CREATE INDEX IF NOT EXISTS idx_memory_fact_entities_entity
    ON memory_fact_entities(entity_id);
-- The checked answer for each chunk of a source the extract job has read, so
-- a job that stops between two calls (a live call, the call budget) goes on
-- later from the next chunk.  Deleted when the source's facts commit.
CREATE TABLE IF NOT EXISTS memory_extract_parts (
    source_ref TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    chunk_sha TEXT NOT NULL,
    version INTEGER NOT NULL,
    facts_json TEXT NOT NULL,
    PRIMARY KEY (chunk_id, chunk_sha, version)
);
CREATE INDEX IF NOT EXISTS idx_memory_extract_parts_source
    ON memory_extract_parts(source_ref);
-- Memory slice 4 (MEMORY-DESIGN.md §2, §3.3): observations, beliefs with
-- evidence and history.  The `memory.consolidate` job writes a scope's changes
-- in ONE transaction.  An observation is never deleted and never overwritten
-- without a history row; `retired` (no live evidence) leaves every reader.
CREATE TABLE IF NOT EXISTS memory_observations (
    id TEXT PRIMARY KEY,
    scope_kind TEXT NOT NULL,
    scope_id TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'current',
    superseded_by TEXT,
    proof_count INTEGER NOT NULL DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT,
    boundary TEXT NOT NULL DEFAULT '',
    consolidator_version INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_observations_scope
    ON memory_observations(scope_kind, scope_id, state);
-- One fact behind an observation.  The row keeps the chunk the fact was read
-- from (source, id, hash, anchor): it is live evidence only while the fact is
-- live with that same chunk and the chunk is in the source's live text.
CREATE TABLE IF NOT EXISTS memory_observation_evidence (
    observation_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    stance TEXT NOT NULL,
    added_at TEXT NOT NULL,
    source_ref TEXT NOT NULL DEFAULT '',
    chunk_id TEXT NOT NULL DEFAULT '',
    chunk_sha TEXT NOT NULL DEFAULT '',
    anchor TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (observation_id, fact_id)
);
CREATE INDEX IF NOT EXISTS idx_memory_observation_evidence_fact
    ON memory_observation_evidence(fact_id);
-- Append only: the two triggers below refuse an UPDATE or a DELETE.
-- `prior_evidence_json` names the facts behind `prior_text`: a reader shows
-- that text only while one of them is still live evidence.
CREATE TABLE IF NOT EXISTS memory_observation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id TEXT NOT NULL,
    at TEXT NOT NULL,
    prior_text TEXT NOT NULL,
    prior_state TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    fact_ids_json TEXT NOT NULL DEFAULT '[]',
    prior_evidence_json TEXT NOT NULL DEFAULT '[]',
    -- The text version `prior_text` is (memory_observation_versions); NULL on
    -- a row that holds no version (a retire row).
    prior_version INTEGER
);
CREATE INDEX IF NOT EXISTS idx_memory_observation_history_observation
    ON memory_observation_history(observation_id, id);
CREATE TRIGGER IF NOT EXISTS memory_observation_history_no_update
    BEFORE UPDATE ON memory_observation_history BEGIN
    SELECT RAISE(ABORT, 'memory_observation_history is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_observation_history_no_delete
    BEFORE DELETE ON memory_observation_history BEGIN
    SELECT RAISE(ABORT, 'memory_observation_history is append only');
END;
-- INSERT OR REPLACE deletes the old row with no DELETE trigger when
-- recursive_triggers is off: refuse an insert over an existing id.  `id` is
-- the rowid, so this trigger also refuses an insert over a rowid.
CREATE TRIGGER IF NOT EXISTS memory_observation_history_no_replace
    BEFORE INSERT ON memory_observation_history
    WHEN EXISTS (SELECT 1 FROM memory_observation_history WHERE id=NEW.id) BEGIN
    SELECT RAISE(ABORT, 'memory_observation_history is append only');
END;
-- Each text an observation has had, bound to the evidence that made it.
-- A reader serves the NEWEST version that still has a backing group whose
-- facts are ALL live evidence in the observation's scope now; none: the
-- observation is not served.  Append only (four triggers).
CREATE TABLE IF NOT EXISTS memory_observation_versions (
    observation_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    text TEXT NOT NULL,
    at TEXT NOT NULL,
    PRIMARY KEY (observation_id, version)
);
CREATE TRIGGER IF NOT EXISTS memory_observation_versions_no_update
    BEFORE UPDATE ON memory_observation_versions BEGIN
    SELECT RAISE(ABORT, 'memory_observation_versions is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_observation_versions_no_delete
    BEFORE DELETE ON memory_observation_versions BEGIN
    SELECT RAISE(ABORT, 'memory_observation_versions is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_observation_versions_no_replace
    BEFORE INSERT ON memory_observation_versions
    WHEN EXISTS (SELECT 1 FROM memory_observation_versions
                 WHERE observation_id=NEW.observation_id AND version=NEW.version) BEGIN
    SELECT RAISE(ABORT, 'memory_observation_versions is append only');
END;
-- INSERT OR REPLACE can also name an existing rowid with a new key: refuse it.
CREATE TRIGGER IF NOT EXISTS memory_observation_versions_no_rowid_replace
    BEFORE INSERT ON memory_observation_versions
    WHEN EXISTS (SELECT 1 FROM memory_observation_versions WHERE rowid=NEW.rowid) BEGIN
    SELECT RAISE(ABORT, 'memory_observation_versions is append only');
END;
-- The fact groups that back one version: the entry that introduced it, and
-- each later `supports` entry while it was the text served.  A group backs
-- the version only while EVERY fact of it is live evidence.
CREATE TABLE IF NOT EXISTS memory_observation_backing (
    observation_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    grp TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    PRIMARY KEY (observation_id, version, grp, fact_id)
);
-- Append only, as the versions it backs (four triggers: no update, no
-- delete, no insert over a key or over a rowid).
CREATE TRIGGER IF NOT EXISTS memory_observation_backing_no_update
    BEFORE UPDATE ON memory_observation_backing BEGIN
    SELECT RAISE(ABORT, 'memory_observation_backing is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_observation_backing_no_delete
    BEFORE DELETE ON memory_observation_backing BEGIN
    SELECT RAISE(ABORT, 'memory_observation_backing is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_observation_backing_no_replace
    BEFORE INSERT ON memory_observation_backing
    WHEN EXISTS (SELECT 1 FROM memory_observation_backing
                 WHERE observation_id=NEW.observation_id AND version=NEW.version
                   AND grp=NEW.grp AND fact_id=NEW.fact_id) BEGIN
    SELECT RAISE(ABORT, 'memory_observation_backing is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_observation_backing_no_rowid_replace
    BEFORE INSERT ON memory_observation_backing
    WHEN EXISTS (SELECT 1 FROM memory_observation_backing WHERE rowid=NEW.rowid) BEGIN
    SELECT RAISE(ABORT, 'memory_observation_backing is append only');
END;
-- Memory slice 5 (MEMORY-DESIGN.md §2, §3.4): pages, standing answers read
-- with no model call.  One row per (scope, slug): the current page.  Each
-- sentence keeps the inputs it cites (`sentences_json`): an observation and
-- the text version it was shown, or a chunk (id, hash, anchor).  A reader
-- serves a sentence only while every input it cites is live in the page's
-- scope NOW (memory/pages.py `read`).  The old page goes to history.
CREATE TABLE IF NOT EXISTS memory_pages (
    id TEXT PRIMARY KEY,
    scope_kind TEXT NOT NULL,
    scope_id TEXT NOT NULL DEFAULT '',
    slug TEXT NOT NULL,
    question TEXT NOT NULL,
    answer_md TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    sentences_json TEXT NOT NULL DEFAULT '[]',
    -- Every input the page was built from (cited or not), each with the
    -- HASHED content tokens of its text: at read time a sentence holding a
    -- token only withdrawn inputs held is withheld.
    inputs_json TEXT NOT NULL DEFAULT '[]',
    built_at TEXT NOT NULL,
    last_memory_seen_at TEXT NOT NULL,
    -- The changes stamped exactly `last_memory_seen_at` that the job saw
    -- (timestamps are to the second): another change in that second is new.
    seen_keys_json TEXT NOT NULL DEFAULT '[]',
    boundary TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    writer_version INTEGER NOT NULL,
    UNIQUE (scope_kind, scope_id, slug)
);
-- Append only: no update, no delete, no insert over an id (`id` is the
-- rowid, so that trigger also refuses an INSERT OR REPLACE over a rowid; with
-- recursive_triggers off a REPLACE deletes the old row with no DELETE
-- trigger).  No reader serves a history row.
CREATE TABLE IF NOT EXISTS memory_page_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id TEXT NOT NULL,
    built_at TEXT NOT NULL,
    answer_md TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    sentences_json TEXT NOT NULL DEFAULT '[]',
    boundary TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    writer_version INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_page_history_page
    ON memory_page_history(page_id, id);
CREATE TRIGGER IF NOT EXISTS memory_page_history_no_update
    BEFORE UPDATE ON memory_page_history BEGIN
    SELECT RAISE(ABORT, 'memory_page_history is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_page_history_no_delete
    BEFORE DELETE ON memory_page_history BEGIN
    SELECT RAISE(ABORT, 'memory_page_history is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_page_history_no_replace
    BEFORE INSERT ON memory_page_history
    WHEN EXISTS (SELECT 1 FROM memory_page_history WHERE id=NEW.id) BEGIN
    SELECT RAISE(ABORT, 'memory_page_history is append only');
END;
CREATE TRIGGER IF NOT EXISTS memory_page_history_no_rowid_replace
    BEFORE INSERT ON memory_page_history
    WHEN EXISTS (SELECT 1 FROM memory_page_history WHERE rowid=NEW.rowid) BEGIN
    SELECT RAISE(ABORT, 'memory_page_history is append only');
END;
-- One row per model job that failed on its input (a bad output), so a source
-- the engine cannot read waits with a back-off and stops after six tries.  A
-- job that succeeds needs no row: the ledger stamp says it is done.
CREATE TABLE IF NOT EXISTS memory_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    target TEXT NOT NULL,
    input_sha TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT,
    lease_expires_at REAL,
    last_error TEXT,
    boundary TEXT NOT NULL DEFAULT '',
    UNIQUE (kind, target, input_sha, version)
);
"""
