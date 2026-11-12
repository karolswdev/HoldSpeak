"""Kernel parent publication guards and child checkpoints.

Part 12 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- Publication-guard triggers (HS-137-01: moved from migrations.py).
-- A publication callback may terminalize its own parent only by clearing
-- the exact claim in that same update; every ordinary state transition
-- and warrant revocation must wait.
CREATE TRIGGER IF NOT EXISTS kernel_parent_publication_blocks_transition
BEFORE UPDATE OF state ON kernel_parent_runs
WHEN OLD.publication_claim_id != ''
  AND NEW.state != OLD.state
  AND NEW.publication_claim_id = OLD.publication_claim_id
BEGIN
    SELECT RAISE(ABORT, 'kernel_parent_publication_in_progress');
END;

CREATE TRIGGER IF NOT EXISTS kernel_parent_publication_blocks_warrant_revocation
BEFORE UPDATE OF warrant_revoked ON kernel_operations
WHEN OLD.warrant_revoked = 0
  AND NEW.warrant_revoked = 1
  AND EXISTS (
      SELECT 1 FROM kernel_parent_runs p
      WHERE p.operation_id = OLD.operation_id
        AND p.publication_claim_id != ''
  )
BEGIN
    SELECT RAISE(ABORT, 'kernel_parent_publication_in_progress');
END;

-- A receipt-gated, durable domain checkpoint for each admitted model child.
-- ``advanced`` says whether the child won the parent tuple CAS; stale stages are
-- retained as truthful receipt-linked facts but never become graph input.
CREATE TABLE IF NOT EXISTS kernel_parent_checkpoints (
    stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
    parent_operation_id TEXT NOT NULL REFERENCES kernel_parent_runs(operation_id),
    child_invocation_id TEXT NOT NULL,
    execution_epoch INTEGER NOT NULL,
    planned_node TEXT NOT NULL,
    checkpoint_json TEXT NOT NULL,
    advanced INTEGER NOT NULL CHECK (advanced IN (0,1)),
    created_at REAL NOT NULL,
    UNIQUE(parent_operation_id, child_invocation_id)
);
CREATE INDEX IF NOT EXISTS idx_kernel_parent_checkpoints_parent
ON kernel_parent_checkpoints(parent_operation_id, execution_epoch);
"""
