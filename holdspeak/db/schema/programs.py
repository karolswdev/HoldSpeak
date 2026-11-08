"""Agent CLI runs and calls, limit stops, note outcomes, Programs, briefing packages, held later, phone.

Part 17 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """\
-- Betterment E2: one row per run of an agent CLI engine (Claude Code, Codex):
-- when it ran, how it ended (answered, not_signed_in, failed) and the cost the
-- CLI reported (NULL when it reports none). The Engines window sums it for
-- today and this week, and reads NOT SIGNED IN from the last run.
-- Betterment M2: run_id is the run's credential id (agent:run:<run_id>, NULL
-- when the run had no desk tools); item_id is the automation item it ran for
-- (NULL outside an automation), so a result shows its cost.
CREATE TABLE IF NOT EXISTS cli_engine_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    ran_at TEXT NOT NULL,
    outcome TEXT NOT NULL,
    cost_usd REAL,
    run_id TEXT,
    item_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_cli_engine_runs_profile ON cli_engine_runs(profile_id, ran_at);
CREATE INDEX IF NOT EXISTS idx_cli_engine_runs_item ON cli_engine_runs(item_id);
-- Betterment M2: each tool call an agent CLI run made with its run credential
-- (agent:run:<run_id>): the tool, what it did (read, write, prepare), the
-- object it touched (a qualified ref, '' for a list) with its title, and when.
-- An automation result shows them as Looked at, Wrote and Prepared.
CREATE TABLE IF NOT EXISTS agent_run_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    tool TEXT NOT NULL,
    effect TEXT NOT NULL,
    ref TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    detail_json TEXT NOT NULL DEFAULT '{}',
    called_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_run_calls_run ON agent_run_calls(run_id, id);
-- Programs PG21: the last usage-limit stop of each agent harness (claude,
-- codex) that the screen watcher read on this desk: when it was first seen,
-- the notice in its shape (times and dates replaced), the reset it named.
-- One row per harness. With a row the Engines window says the notice is
-- verified; without one, only the documented wording is known.
CREATE TABLE IF NOT EXISTS agent_limit_stops (
    harness TEXT PRIMARY KEY,
    stopped_at TEXT NOT NULL,
    notice TEXT NOT NULL,
    resets_at TEXT,
    rule TEXT NOT NULL
);
-- Betterment Q9 (Find the tasks): the outcome rows the meeting's extraction
-- found in one note (a task with its owner and date, or a proposed decision).
-- They stay with the note: a new Find replaces the rows still proposed and
-- keeps the confirmed ones, each with the task or decision it made
-- (`made_ref`).
CREATE TABLE IF NOT EXISTS note_outcomes (
    id TEXT PRIMARY KEY,
    note_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT '',
    due TEXT NOT NULL DEFAULT '',
    rationale TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'proposed',
    made_ref TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    found_at TEXT NOT NULL,
    confirmed_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_note_outcomes_note ON note_outcomes(note_id, ordinal);
-- Programs (2026-10-28, docs/internal/betterment/programs/): a goal cut into
-- steps; each step is one agent launch in one worktree, checked by a verified
-- log, reviewed, and merged on the owner's press or by delegation. The
-- engine (services/program_runner.py) is the only writer of the states.
-- PG-LANG (2026-10-31, PROGRAM-LANGUAGE-2026-10-31.md §3.2, §5.4, §5.5, §8):
-- the fields the Program text writes. NULL review_depth: the template's; NULL
-- planner_engine: the desk's agent.plan assignment; NULL budget_tokens: the
-- first agent's engine window (a step's NULL: the Program's); night_json
-- {line, start, end, max_steps}; delivery_ref "dw:<project>/<phase>[/<story>]".
CREATE TABLE IF NOT EXISTS programs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    goal_markdown TEXT NOT NULL DEFAULT '',
    project_id TEXT,
    repo_root TEXT NOT NULL DEFAULT '',
    base_branch TEXT NOT NULL DEFAULT 'main',
    control TEXT NOT NULL DEFAULT 'normal',
    spend_limit_usd REAL,
    check_command TEXT,
    reviewer_profile TEXT,
    reviewer_engine TEXT,
    default_profile TEXT NOT NULL DEFAULT 'claude-default',
    default_engine TEXT,
    prefer_idle INTEGER NOT NULL DEFAULT 0,
    template TEXT NOT NULL DEFAULT '',
    origin_ref TEXT,
    for_person_id TEXT,
    created_by TEXT NOT NULL DEFAULT 'owner',
    state TEXT NOT NULL DEFAULT 'drafting',
    note_id TEXT,
    closed_at TEXT,
    revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    default_runs_on_json TEXT NOT NULL DEFAULT '[]',
    allowed_profiles_json TEXT NOT NULL DEFAULT '[]',
    may_handoff INTEGER NOT NULL DEFAULT 0,
    usage_warning_share REAL,
    may_call INTEGER NOT NULL DEFAULT 0,
    review_depth TEXT,
    planner_engine TEXT,
    budget_tokens INTEGER,
    night_json TEXT,
    within_json TEXT NOT NULL DEFAULT '[]',
    delivery_ref TEXT,
    rounds_before_start INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS program_steps (
    id TEXT PRIMARY KEY,
    program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    title TEXT NOT NULL,
    brief_markdown TEXT NOT NULL DEFAULT '',
    owns_json TEXT NOT NULL DEFAULT '[]',
    after_json TEXT NOT NULL DEFAULT '[]',
    profile TEXT,
    engine TEXT,
    prefer_idle INTEGER NOT NULL DEFAULT 0,
    effort TEXT NOT NULL DEFAULT 'medium',
    race INTEGER NOT NULL DEFAULT 0,
    race_of TEXT,
    gate_check INTEGER NOT NULL DEFAULT 1,
    gate_review TEXT NOT NULL DEFAULT 'none',
    review_depth TEXT NOT NULL DEFAULT 'delta',
    gate_merge TEXT NOT NULL DEFAULT 'owner',
    state TEXT NOT NULL DEFAULT 'planned',
    held_reason TEXT,
    launch_id TEXT,
    worktree TEXT,
    branch TEXT,
    head_commit TEXT,
    checked_commit TEXT,
    pr_url TEXT,
    pr_number INTEGER,
    check_log TEXT,
    check_verdict TEXT,
    facts_json TEXT NOT NULL DEFAULT '{}',
    review_verdict TEXT,
    findings_json TEXT NOT NULL DEFAULT '[]',
    report TEXT,
    rounds INTEGER NOT NULL DEFAULT 0,
    parked_reason TEXT,
    parked_by TEXT,
    origin_ref TEXT,
    for_person_id TEXT,
    started_at TEXT,
    ended_at TEXT,
    updated_at TEXT NOT NULL,
    runs_on_json TEXT NOT NULL DEFAULT '[]',
    handoffs_json TEXT NOT NULL DEFAULT '[]',
    may_call INTEGER NOT NULL DEFAULT 0,
    budget_tokens INTEGER,
    -- 2026-11-08 (the prompt step): NULL is an agent step (a launch in a
    -- worktree); 'prompt' is one model call on the assigned engine, with no
    -- repository. deliver: where its answer goes (inbox, needs_you, today,
    -- destination:<id>, project_updates:<id>); sources_json: the About refs
    -- its brief expands when it runs.
    kind TEXT,
    deliver TEXT,
    sources_json TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_program_steps_program ON program_steps(program_id, ordinal);
CREATE TABLE IF NOT EXISTS program_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_id TEXT NOT NULL,
    program_id TEXT NOT NULL,
    at TEXT NOT NULL,
    by_kind TEXT NOT NULL,
    line TEXT NOT NULL,
    operation_id TEXT,
    kind TEXT,
    choice TEXT,
    rule TEXT,
    overturnable INTEGER NOT NULL DEFAULT 0,
    overturned_at TEXT,
    undo_json TEXT NOT NULL DEFAULT '{}',
    via TEXT
);
-- PG-DIRECTION DIR1 (2026-10-31, DIRECTION-2026-10-31.md §11): a briefing
-- package is one held item (or, later, a digest) frozen for a channel. Its
-- page token is never stored: only its SHA-256. answers_json holds the one
-- answer per ref ({choice, via, at, later_until?}).
CREATE TABLE IF NOT EXISTS briefing_packages (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    refs_json TEXT NOT NULL,
    body_json TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    sent_json TEXT NOT NULL DEFAULT '[]',
    answers_json TEXT NOT NULL DEFAULT '{}'
);
-- PG-DIRECTION DIR4 (2026-10-31, DIRECTION-2026-10-31.md §7, §11): Later is
-- an answer. One row per held item he deferred: the next touch (until), the
-- channel he said it on and the package it came from. The item leaves the
-- Needs you count until then and comes back at the next touch.
CREATE TABLE IF NOT EXISTS held_later (
    ref TEXT PRIMARY KEY,
    until TEXT NOT NULL,
    via TEXT NOT NULL,
    at TEXT NOT NULL,
    package_id TEXT
);
-- Programs PG-REQ (2026-10-31, PROGRAMS-REQUIREMENTS-2026-10-31.md §11): one
-- sentence of the owner's on a Program or a step, with the way it is proven
-- (check, review, shot, word), its state and its evidence. A row with no
-- step_id is the Program's own (each_step 0: the end check; each_step 1: the
-- every-step parent, copied to each step with parent_id).
CREATE TABLE IF NOT EXISTS program_requirements (
    id TEXT PRIMARY KEY,
    program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    step_id TEXT,
    ordinal INTEGER NOT NULL,
    text TEXT NOT NULL,
    kind TEXT NOT NULL,
    required INTEGER NOT NULL DEFAULT 1,
    spec_json TEXT NOT NULL DEFAULT '{}',
    each_step INTEGER NOT NULL DEFAULT 0,
    parent_id TEXT,
    state TEXT NOT NULL DEFAULT 'not_yet',
    judged_commit TEXT,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    waived_reason TEXT,
    rounds INTEGER NOT NULL DEFAULT 0,
    by_kind TEXT NOT NULL DEFAULT 'owner',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    judged_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_program_requirements_program ON program_requirements(program_id, step_id, ordinal);
-- PG-LANG (2026-10-31, PROGRAM-LANGUAGE-2026-10-31.md §6.2): the interview
-- rounds of a Program (Architecture, Product, ...). state open | asking | done
-- | skipped; questions_json [{id, text, answer, answered_by, at}]: the engine
-- writes each question, the owner writes each answer.
CREATE TABLE IF NOT EXISTS program_rounds (
    program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'open',
    ordinal INTEGER NOT NULL DEFAULT 0,
    questions_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (program_id, name)
);
-- Phone (2026-10-28, docs/internal/betterment/phone/): the desk reaches the
-- owner on his phone and he reaches the desk. A paired device, the messages
-- both ways, the calls (ringing, answered, missed, declined, ended) and the
-- one sequence-numbered event log the phone and the desk replay from
-- (holdspeak/phone/). A device row in state 'pairing' is a QR not yet
-- scanned (jwt_kid holds the pairing token's hash until it is redeemed).
CREATE TABLE IF NOT EXISTS phone_devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    platform TEXT NOT NULL DEFAULT '',
    push_token TEXT,
    push_kind TEXT,
    sip_identity TEXT,
    jwt_kid TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pairing',
    paired_at TEXT NOT NULL,
    last_seen_at TEXT,
    revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS phone_messages (
    id TEXT PRIMARY KEY,
    seq INTEGER NOT NULL DEFAULT 0,
    direction TEXT NOT NULL,
    text TEXT NOT NULL,
    reply_to TEXT,
    created_at TEXT NOT NULL,
    delivered_at TEXT,
    read_at TEXT,
    origin_ref TEXT,
    program_step_id TEXT
);
CREATE TABLE IF NOT EXISTS phone_calls (
    id TEXT PRIMARY KEY,
    seq INTEGER NOT NULL DEFAULT 0,
    direction TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    context_digest TEXT NOT NULL DEFAULT '',
    urgent INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    answered_at TEXT,
    ended_at TEXT,
    end_reason TEXT,
    transcript_ref TEXT,
    decision_json TEXT,
    transport TEXT NOT NULL DEFAULT 'number',
    calls_turn_id TEXT
);
CREATE TABLE IF NOT EXISTS phone_events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    ts TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_phone_events_ts ON phone_events(ts);
"""
