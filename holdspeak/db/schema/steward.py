"""Steward policy, runs and steps, suggested sources, follow-through, calendar links, preparation brief, carry, attention.

Part 15 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- HS-163-01: Steward policy — per-Project: eligible effect kinds, YOLO flags,
-- bounds (retry counts, per-run action caps, cooldowns per STW-008).
CREATE TABLE IF NOT EXISTS steward_policies (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    eligible_effect_kinds_json TEXT NOT NULL DEFAULT '[]',
    yolo_flags_json TEXT NOT NULL DEFAULT '{}',
    max_retries INTEGER NOT NULL DEFAULT 3,
    max_actions_per_run INTEGER NOT NULL DEFAULT 10,
    cooldown_seconds INTEGER NOT NULL DEFAULT 0,
    bounds_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    -- HS-164-01: explicit per-project unattended opt-in (default OFF).
    unattended_enabled INTEGER NOT NULL DEFAULT 0,
    -- HS-173-04: per-project nudge comment template ({days} placeholder).
    nudge_template TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    -- PHILO-9-02 (the steward beat, section 4): the owner's latest admitted
    -- operation that wrote these terms (project.configure_steward, or
    -- project.archive turning unattended runs off). NULL: never recorded.
    configure_operation_id TEXT REFERENCES kernel_operations(operation_id)
);
CREATE INDEX IF NOT EXISTS idx_steward_policies_project
    ON steward_policies(project_id);

-- HS-163-01: Steward runs — the durable run record (STW-001).
-- state: queued|running|stopping|completed|failed|interrupted.
-- phase: observe|compare|propose|act|verify|record.
-- STW-002: partial unique index enforces at most one active run per project.
CREATE TABLE IF NOT EXISTS steward_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    policy_id TEXT REFERENCES steward_policies(id),
    state TEXT NOT NULL DEFAULT 'queued',
    phase TEXT NOT NULL DEFAULT 'observe',
    requested_by TEXT NOT NULL DEFAULT '',
    stop_requested_at TEXT,
    watermark TEXT NOT NULL DEFAULT '',
    summary_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    -- PHILO-9-02 (the steward beat, section 2): the run's kernel operation
    -- (required for every admitted run; NULL only on a run from before) and
    -- its frozen authority (the policy snapshot and its provenance).
    operation_id TEXT REFERENCES kernel_operations(operation_id),
    authority_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_steward_runs_project
    ON steward_runs(project_id, state);
CREATE UNIQUE INDEX IF NOT EXISTS uq_steward_runs_operation
    ON steward_runs(operation_id) WHERE operation_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_steward_runs_one_active_per_project
    ON steward_runs(project_id)
    WHERE state IN ('queued', 'running', 'stopping');

-- HS-163-01: Steward steps — the STW-005 reconciliation substrate.
-- Each step in a run: phase, seq, effect kind, idempotency_key for dedup,
-- expected/observed state JSON for verification (STW-004), receipts, errors.
CREATE TABLE IF NOT EXISTS steward_steps (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES steward_runs(id) ON DELETE CASCADE,
    phase TEXT NOT NULL DEFAULT '',
    seq INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'pending',
    effect_kind TEXT NOT NULL DEFAULT '',
    idempotency_key TEXT NOT NULL DEFAULT '',
    expected_state_json TEXT NOT NULL DEFAULT '{}',
    observed_state_json TEXT NOT NULL DEFAULT '{}',
    receipt_json TEXT NOT NULL DEFAULT '{}',
    error_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_steward_steps_run
    ON steward_steps(run_id, phase, seq);
CREATE INDEX IF NOT EXISTS idx_steward_steps_idempotency
    ON steward_steps(idempotency_key);

-- HS-163-01: Steward command records — replay substrate.
-- Each command that triggered or drove a steward action.
CREATE TABLE IF NOT EXISTS steward_commands (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES steward_runs(id) ON DELETE CASCADE,
    step_id TEXT REFERENCES steward_steps(id),
    command_kind TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_steward_commands_run
    ON steward_commands(run_id);

-- HS-172-06: Suggested sources — transcript-derived source proposals for Rooms.
-- Each row is a suggestion (pending / accepted / dismissed); dismissed
-- suggestions never recur for the same (project_id, reference) pair.
CREATE TABLE IF NOT EXISTS source_suggestions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    meeting_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    reference TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_source_suggestions_project
    ON source_suggestions(project_id, status);
CREATE INDEX IF NOT EXISTS idx_source_suggestions_dedup
    ON source_suggestions(project_id, reference);

-- HS-172-03: Follow-through proposals — intel-extracted decisions and action
-- items that arrive as PROPOSALS in NEEDS YOU.  Lifecycle: proposed ->
-- confirmed | dismissed.  Confirmed proposals create real decision_records /
-- action_items through the kernel; dismissed ones disappear.  Dedup by
-- (meeting_id, fingerprint) so a re-run never duplicates.
CREATE TABLE IF NOT EXISTS follow_through_proposals (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    project_id TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('decision', 'action')),
    text TEXT NOT NULL,
    owner_hint TEXT,
    due_hint TEXT,
    source_artifact_id TEXT,
    source_plugin TEXT NOT NULL,
    segment_timestamp REAL,
    speaker_label TEXT,
    model_host TEXT,
    fingerprint TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'proposed'
        CHECK (state IN ('proposed', 'confirmed', 'dismissed')),
    original_text TEXT,
    decision_record_id TEXT,
    commitment_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT,
    -- HS-200-12: the retry identity and the evidence a proposal carries.
    -- `retry_key` is deterministic over (meeting, extraction revision, kind,
    -- transcript span, ordinal-in-span) so a repeated completion, a model
    -- retry and a lost acknowledgement resolve to the SAME row in ANY state
    -- (the fingerprint index above is partial over 'proposed' and let a
    -- re-run re-mint a proposal the owner had already confirmed).
    retry_key TEXT,
    extraction_revision TEXT,
    job_id TEXT,
    job_attempt INTEGER,
    extraction_model TEXT,
    span_start REAL,
    span_end REAL,
    segment_index INTEGER,
    support TEXT NOT NULL DEFAULT 'unknown',
    support_record_json TEXT,
    owner_supplied TEXT,
    due_supplied TEXT,
    edited_at TEXT,
    -- HS-200-13 (AC1): the rationale the extractor read beside the decision.
    -- Without it a confirmed record carried `rationale ''` and recall could
    -- return the decision but never WHY (the plugin has said why all along).
    rationale TEXT,
    -- PHILO-15 08: the action_items row a summary action proposal stands for.
    -- Confirm accepts THAT row (no second copy); Decline dismisses it.
    action_item_id TEXT,
    -- PHILO-15 08: Defer hides a proposed row from Needs until this stamp.
    deferred_until TEXT
);
CREATE INDEX IF NOT EXISTS idx_ftp_meeting
    ON follow_through_proposals(meeting_id, state);
CREATE INDEX IF NOT EXISTS idx_ftp_project
    ON follow_through_proposals(project_id, state);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ftp_dedup
    ON follow_through_proposals(meeting_id, fingerprint)
    WHERE state = 'proposed';
-- HS-200-12: one proposal per retry identity, whatever its state.
CREATE UNIQUE INDEX IF NOT EXISTS idx_ftp_retry_key
    ON follow_through_proposals(meeting_id, retry_key)
    WHERE retry_key IS NOT NULL;

-- HS-175-02: Calendar event to Room (project) matcher join table.
CREATE TABLE IF NOT EXISTS calendar_event_projects (
    calendar_event_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    match_source TEXT NOT NULL DEFAULT 'title'
        CHECK (match_source IN ('title', 'attendee', 'manual')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (calendar_event_id, project_id)
);
CREATE INDEX IF NOT EXISTS idx_cep_project
    ON calendar_event_projects(project_id);

-- HS-175 counsel C5: a durable Unlink.  The owner's unlink of an
-- (event, Room) pair is keyed by the event's (source, uid) rather than
-- its projection id, so it survives both the matcher's re-run and the
-- projection id regenerating when the event's time changes.  A manual
-- link clears it.  Additive; never rebuilt.
CREATE TABLE IF NOT EXISTS calendar_event_link_suppressions (
    calendar_source_id TEXT NOT NULL,
    calendar_uid TEXT NOT NULL,
    project_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (calendar_source_id, calendar_uid, project_id)
);
-- HS-200-41: a Room ask that outlived the tab.  `/api/ask` is one blocking
-- request/response (holdspeak/web/routes/primitives/ask.py) and persists
-- nothing -- the kernel journals a payload hash, and `ask_results` holds the
-- answer without the question.  This row is therefore the ONLY durable record
-- of what was asked.  It pins the invocation identity BEFORE dispatch so an
-- answer that lands while the tab is gone can be CLAIMED out of `ask_results`
-- after a restart instead of paid for twice (ruling B3).
--
-- `state` carries the full posture-6 vocabulary so the `TaskResume` species can
-- draw rows from every owner (ruling B8), but this table's own writers reach
-- only the honest subset: `saved`, `failed`, `accepted`, `discarded`.  `running`
-- and `waiting` belong to owners that have a job row; an ask has none.
-- `Discard` is a state, never a DELETE (ruling B6).
-- `stopped_reason` is the target's own words, quoted verbatim from the refusal
-- that raised them; nothing here is ever a composed sentence (ruling B5).
-- `custody_*` is who SAVED the row (the `SAVED HERE` token, ruling B7);
-- `dispatch_*` is the live lease held while a resume is in flight, mirroring
-- `refinement_invocations.dispatch_host_id`, and is what startup recovery
-- reconciles.  Additive; never rebuilt.
CREATE TABLE IF NOT EXISTS project_ask_tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    invocation_id TEXT NOT NULL UNIQUE,
    purpose TEXT NOT NULL,
    lens TEXT NOT NULL DEFAULT 'Project',
    recipe_key TEXT NOT NULL DEFAULT '',
    grounding_json TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL DEFAULT 'saved'
        CHECK (state IN ('saved', 'running', 'waiting', 'failed',
                         'incomplete', 'accepted', 'discarded')),
    stopped_reason TEXT NOT NULL DEFAULT '',
    stopped_code TEXT NOT NULL DEFAULT '',
    custody_host_id TEXT NOT NULL DEFAULT '',
    custody_lease_epoch INTEGER NOT NULL DEFAULT 0,
    dispatch_host_id TEXT NOT NULL DEFAULT '',
    dispatch_lease_epoch INTEGER NOT NULL DEFAULT 0,
    resume_order INTEGER NOT NULL DEFAULT 0,
    saved_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    settled_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_ask_tasks_resume
    ON project_ask_tasks(state, resume_order DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_project_ask_tasks_project
    ON project_ask_tasks(project_id, state);

-- HS-200-11: the preparation brief, bound to its Project (story 11 AC4) with
-- its SOURCE MANIFEST frozen beside it (AC2).  `monday_briefs` is window-keyed
-- and carries no project_id (design D3, "the preparation seam"); a sibling
-- table is the additive answer, never a rebuild of that one.
-- `manifest_json` records exactly what the draft read -- every source with its
-- state, observation time and revision, the current and superseded decisions
-- carried in, and every named omission with its reason and repair.
-- `manifest_sha256` is recomputed and compared on every read, the
-- `refinement_attachment_revisions` freeze mechanic reused (ruling R3).
-- `outline_json` is the BOUNDED typed shape (priorities · questions ·
-- obligations) both drafters produce (AC3); `claims_json` carries the three
-- C2 axes per sentence (HS-200-06).  `generator*` copies the data boundary
-- pattern of `project_updates`.  Keep is a lifecycle flip, never a copy.
CREATE TABLE IF NOT EXISTS project_briefs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    project_revision INTEGER NOT NULL DEFAULT 0,
    purpose TEXT NOT NULL,
    lifecycle TEXT NOT NULL DEFAULT 'draft'
        CHECK (lifecycle IN ('draft', 'kept', 'discarded')),
    manifest_revision INTEGER NOT NULL DEFAULT 1,
    manifest_json TEXT NOT NULL DEFAULT '{}',
    manifest_sha256 TEXT NOT NULL DEFAULT '',
    outline_json TEXT NOT NULL DEFAULT '{}',
    body_md TEXT NOT NULL DEFAULT '',
    claims_json TEXT NOT NULL DEFAULT '[]',
    generator TEXT NOT NULL DEFAULT 'deterministic',
    generator_host TEXT,
    generator_model TEXT,
    elapsed_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    kept_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_briefs_project
    ON project_briefs(project_id, lifecycle, created_at DESC);

-- HS-200-13: the carry mark.  `Carry into brief` on the Desk memory face
-- attaches a decision record BY REFERENCE to the next preparation of its
-- Project (C3) -- the row names the record and never copies it, so a record
-- superseded between the recall and the preparation resolves to the CURRENT
-- one when the manifest is built (holdspeak/services/brief_carry.py,
-- `pending_carries`).  `consumed_at` / `consumed_by` are stamped by the
-- preparation that read the mark (HS-200-11, `consume_carries`); a pending
-- mark is one with `consumed_at IS NULL`.  Identity is ONE MARK PER CURRENT
-- RECORD, enforced by resolution at write time (`carry_into_brief` replays
-- when the pressed record resolves to an already-pending one); the unique
-- index on the pressed ref below is only the belt against a double press.
-- Additive; never rebuilt.
CREATE TABLE IF NOT EXISTS preparation_carries (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    record_ref TEXT NOT NULL,
    carried_at TEXT NOT NULL,
    carried_by TEXT NOT NULL DEFAULT '',
    consumed_at TEXT,
    consumed_by TEXT
);
CREATE INDEX IF NOT EXISTS idx_preparation_carries_project
    ON preparation_carries(project_id, consumed_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_preparation_carries_pending
    ON preparation_carries(project_id, record_ref)
    WHERE consumed_at IS NULL;

-- HS-200-13 (AC5): the attention aggregate's last SUCCESSFUL observation per
-- source, made durable.  HS-200-15 left `LastKnownStore` process-local, so a
-- hub restart forgot every item a failed source had last said; the store now
-- writes through to this row and reads it back on a cold miss.  One row per
-- source id; `items_json` is the list of attention rows exactly as the
-- aggregate built them.  Additive; never rebuilt.
CREATE TABLE IF NOT EXISTS needs_you_last_known (
    source_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    observed_at TEXT NOT NULL,
    items_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);
"""
