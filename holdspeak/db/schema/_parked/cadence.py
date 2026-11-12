# PARKED 2026-11-12: unused next-action store; old databases keep their rows.
SQL = """
CREATE TABLE IF NOT EXISTS cadence_next_actions (
    id TEXT PRIMARY KEY,
    loop_id TEXT NOT NULL REFERENCES cadence_loops(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body_markdown TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0,
    reversible INTEGER NOT NULL DEFAULT 1,
    proposal_id TEXT,
    generated_by TEXT NOT NULL DEFAULT 'deterministic',
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cadence_next_actions_loop ON cadence_next_actions(loop_id);

"""
