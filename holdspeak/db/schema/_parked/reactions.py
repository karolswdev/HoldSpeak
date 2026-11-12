"""Parked: the Reaction event projection has no live reader or writer after one watch (#2232)."""

SQL = """
-- A projection row says only that one event was materialized into one item and,
-- optionally, one kernel operation. Execution outcome belongs to the immutable
-- kernel receipt, never to a second mutable delivery state machine.
CREATE TABLE IF NOT EXISTS reaction_event_projections (
    reaction_id TEXT NOT NULL REFERENCES connector_reactions(id) ON DELETE CASCADE,
    event_id TEXT NOT NULL REFERENCES service_events(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES workbench_items(id),
    operation_id TEXT,
    receipt_id TEXT,
    projected_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (reaction_id, event_id)
);

"""
