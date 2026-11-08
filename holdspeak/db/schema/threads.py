"""Scheduled recordings, calendar ingest, the thread ledger and its FTS, tool policy, Front Door plans.

Part 13 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- v61 (HS-136-01): Scheduled recordings — owner-set cron-driven capture.
CREATE TABLE IF NOT EXISTS scheduled_recordings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    cron_expr TEXT NOT NULL,
    tz TEXT NOT NULL DEFAULT 'UTC',
    one_shot INTEGER NOT NULL DEFAULT 0 CHECK (one_shot IN (0,1)),
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0,1)),
    revision INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL,
    last_fired_at REAL,
    next_fire_at REAL,
    armed_at REAL,
    deadline_at REAL,
    state TEXT NOT NULL DEFAULT 'idle'
        CHECK (state IN ('idle','arming','recording','stopped','cancelled','refused','missed')),
    last_outcome TEXT NOT NULL DEFAULT '',
    last_receipt_id TEXT NOT NULL DEFAULT '',
    delegation_receipt_id TEXT NOT NULL DEFAULT '',
    calendar_event_id TEXT NOT NULL DEFAULT '',
    calendar_uid TEXT NOT NULL DEFAULT '',
    calendar_source_id TEXT NOT NULL DEFAULT '',
    born_from TEXT NOT NULL DEFAULT '',
    -- HS-175 counsel C3: the owner's cancel is final.  Stamped (epoch) by
    -- the owner's Cancel; with (calendar_source_id, calendar_uid) it is the
    -- tombstone the calendar refresh honours.  Additive, nullable.
    owner_cancelled_at REAL,
    -- HS-175 counsel re-read (1): the tombstone is keyed by OCCURRENCE --
    -- (calendar_source_id, calendar_uid, calendar_starts_at) -- so Cancel
    -- on one standup of a series means "this one", never the series.
    -- The event's starts_at exactly as projected (the parser's UTC string).
    calendar_starts_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_scheduled_recordings_enabled
ON scheduled_recordings(enabled, next_fire_at) WHERE enabled=1;
-- HS-147-01: invariant L1 — one live arm per calendar event.
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_recordings_calendar_event_armed
ON scheduled_recordings(calendar_event_id) WHERE calendar_event_id != '' AND enabled = 1;

-- HS-144-02: Calendar ingest is a replace-on-success ICS projection.
-- HS-146-01: source_id + source_label for multi-source plumbing.
CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    location TEXT,
    meeting_url TEXT,
    last_seen_at REAL NOT NULL,
    subscription_revision TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    source_label TEXT NOT NULL DEFAULT '',
    attendees_json TEXT NOT NULL DEFAULT '[]'
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_calendar_events_source_uid_start
ON calendar_events(source_id, uid, starts_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_upcoming
ON calendar_events(starts_at, id);

-- HS-151-01: The thread ledger — persistent desk conversations.
-- Interview control state composes Threads; citizen records retain their owners.
CREATE TABLE IF NOT EXISTS interview_sessions (
    thread_id TEXT PRIMARY KEY REFERENCES threads(id) ON DELETE CASCADE,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interview_events (
    thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    command_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    revision INTEGER NOT NULL,
    event_kind TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (thread_id, command_id),
    UNIQUE (thread_id, revision)
);

CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    recipe_id TEXT NOT NULL DEFAULT '',
    profile_override TEXT NOT NULL DEFAULT '',
    directory_id TEXT NOT NULL DEFAULT '',
    parent_thread_id TEXT NOT NULL DEFAULT '',
    status_line TEXT NOT NULL DEFAULT '',
    call_mode INTEGER NOT NULL DEFAULT 0,
    token_in INTEGER NOT NULL DEFAULT 0,
    token_out INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    last_turn_at REAL,
    deleted_at REAL
);
CREATE INDEX IF NOT EXISTS idx_threads_updated
ON threads(updated_at);

CREATE TRIGGER IF NOT EXISTS interview_thread_deleted
AFTER UPDATE OF deleted_at ON threads
WHEN NEW.deleted_at IS NOT NULL
BEGIN
    DELETE FROM interview_sessions WHERE thread_id=NEW.id;
    DELETE FROM interview_events WHERE thread_id=NEW.id;
END;

CREATE TABLE IF NOT EXISTS thread_messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES threads(id),
    parent_id TEXT REFERENCES thread_messages(id),
    role TEXT NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    streaming INTEGER NOT NULL DEFAULT 0,
    operation_id TEXT NOT NULL DEFAULT '',
    receipt_id TEXT NOT NULL DEFAULT '',
    invocation_id TEXT NOT NULL DEFAULT '',
    egress_scope TEXT NOT NULL DEFAULT '',
    egress_host TEXT NOT NULL DEFAULT '',
    model_id TEXT NOT NULL DEFAULT '',
    route_plan_id TEXT NOT NULL DEFAULT '',
    stats_json TEXT NOT NULL DEFAULT '',
    error_json TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    completed_at REAL,
    aborted_at REAL,
    deleted_at REAL,
    egress_receipt_id TEXT NOT NULL DEFAULT '',
    egress_fallback INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_thread_messages_thread_created
ON thread_messages(thread_id, created_at);

CREATE TABLE IF NOT EXISTS thread_message_parts (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES thread_messages(id),
    ordinal INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('text','reasoning','tool_call','attachment','annotation','guardrail','guardrail_failed')),
    text TEXT,
    tool_call_id TEXT NOT NULL DEFAULT '',
    attachment_ref TEXT NOT NULL DEFAULT '',
    meta_json TEXT NOT NULL DEFAULT '',
    sensitive INTEGER NOT NULL DEFAULT 0,
    draft INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_thread_message_parts_message_ordinal
ON thread_message_parts(message_id, ordinal);

-- HS-200-10 (F0/L4, P0-1): `origin` records HOW a frozen ref arrived, not WHEN.
--   'reference'  the owner named it (an explicit ref on the turn, a member of
--                a container he attached, or a seed ref on thread creation)
--   'relevance'  a relevance/grounding pass produced it
--   ''           UNKNOWN -- every row written before this column existed, and
--                any row whose writer did not stamp it
-- The default is the empty string, NOT 'relevance', for two reasons.  A
-- `thread_refs` row is a RECEIPT, and stamping a pre-existing row 'relevance'
-- would assert something the database does not know; '' says "unknown"
-- honestly.  And the L4 replay fence is an ALLOW-LIST -- it keeps only
-- 'reference' -- so unknown fences, which is the fail-closed direction:
-- over-fencing a replay costs the model one block the owner can hand it again
-- by reference, while under-fencing is the breach.
--
-- The column replaces a TIMESTAMP comparison that could not survive a second
-- device.  `context_promotions.created_at` is the REMOTE wall clock copied
-- verbatim on merge (`sync_service.py:630-640`, held out of the LWW field set
-- at `:654-656`), and the post-sync corpus repair (`:672-700`) never touches
-- `thread_refs`; comparing that clock against a LOCAL `thread_refs.created_at`
-- read a relevance body as "arrived by reference" on every device that froze
-- it before the promotion synced in.
CREATE TABLE IF NOT EXISTS thread_refs (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES threads(id),
    message_id TEXT REFERENCES thread_messages(id),
    ref_kind TEXT NOT NULL DEFAULT '',
    ref_id TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '',
    frozen_json TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    origin TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_thread_refs_thread
ON thread_refs(thread_id);

-- FTS for thread message parts (content-synced, counsel M3 soft-delete aware).
CREATE VIRTUAL TABLE IF NOT EXISTS thread_messages_fts USING fts5(
    text,
    content=thread_message_parts
);

-- Insert trigger: index part text only if parent message is not soft-deleted.
CREATE TRIGGER IF NOT EXISTS thread_messages_fts_ai
AFTER INSERT ON thread_message_parts
WHEN NEW.text IS NOT NULL
BEGIN
    INSERT INTO thread_messages_fts(rowid, text)
    SELECT NEW.rowid, NEW.text
    WHERE NOT EXISTS (
        SELECT 1 FROM thread_messages WHERE id = NEW.message_id AND deleted_at IS NOT NULL
    );
END;

-- Delete trigger: remove part from FTS index.
CREATE TRIGGER IF NOT EXISTS thread_messages_fts_ad
AFTER DELETE ON thread_message_parts
WHEN OLD.text IS NOT NULL
BEGIN
    INSERT INTO thread_messages_fts(thread_messages_fts, rowid, text)
    VALUES('delete', OLD.rowid, OLD.text);
END;

-- Update trigger: re-index on text change (extend_part_text path).
CREATE TRIGGER IF NOT EXISTS thread_messages_fts_au
AFTER UPDATE OF text ON thread_message_parts
BEGIN
    INSERT INTO thread_messages_fts(thread_messages_fts, rowid, text)
    SELECT 'delete', OLD.rowid, OLD.text WHERE OLD.text IS NOT NULL;
    INSERT INTO thread_messages_fts(rowid, text)
    SELECT NEW.rowid, NEW.text
    WHERE NEW.text IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM thread_messages WHERE id = NEW.message_id AND deleted_at IS NOT NULL
    );
END;

-- Message soft-delete trigger: remove all parts of a deleted message from FTS.
CREATE TRIGGER IF NOT EXISTS thread_messages_fts_msg_soft_delete
AFTER UPDATE OF deleted_at ON thread_messages
WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
BEGIN
    INSERT INTO thread_messages_fts(thread_messages_fts, rowid, text)
    SELECT 'delete', p.rowid, p.text
    FROM thread_message_parts p
    WHERE p.message_id = NEW.id AND p.text IS NOT NULL;
END;

-- HS-152-02: Per-thread tool policy — append-only, newest wins, never updated.
CREATE TABLE IF NOT EXISTS thread_tool_policy (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES threads(id),
    tool_name TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('allow','ask','deny')),
    set_at REAL NOT NULL,
    deleted_at REAL
);
CREATE INDEX IF NOT EXISTS idx_thread_tool_policy_thread_tool
ON thread_tool_policy(thread_id, tool_name, set_at DESC);

-- HS-156-02: Front Door apply plans — durable, resumable pack application.
CREATE TABLE IF NOT EXISTS front_door_apply_plans (
    id TEXT PRIMARY KEY,
    pack_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running','done','failed')),
    items_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""
