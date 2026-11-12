# PARKED 2026-11-12: Programs create and deliver new Automation runs.
from __future__ import annotations
import json
from typing import Any
from holdspeak.services.automation_runs import (
    OCCURRENCE, hand_item_id, hand_sources, _delivery_principal, _deliver_one, _finished_notices, log,
)

def materialize_hand_items(db: Any, wb: Any) -> list[Any]:
    """Create or read one occurrence item for every eligible source item."""
    from holdspeak.timestamps import utc_now_iso

    items: list[Any] = []
    instruction = str(getattr(wb, "instruction", "") or "").strip()
    for source in hand_sources(db, wb):
        item_id = hand_item_id(wb.id, source["ref"])
        context = {
            OCCURRENCE: True,
            "agent_hand": {
                "source_ref": source["ref"],
                "kind": source["kind"],
                "id": source["id"],
                "status": "pending",
            },
        }
        # Materialisation itself is a race with another Run press.  Insert
        # only when absent under the database write lock; an existing row's
        # launch context is immutable to this step.
        with db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing_row = conn.execute("SELECT id FROM workbench_items WHERE id=?", (item_id,)).fetchone()
            if existing_row is None:
                now = utc_now_iso()
                conn.execute(
                    """INSERT INTO workbench_items
                       (id, workbench_id, title, body, priority, status,
                        grounding_json, context_json, created_at, last_modified)
                       VALUES (?, ?, ?, ?, 3, 'pending', ?, ?, ?, ?)""",
                    (item_id, wb.id, source["title"], instruction,
                     json.dumps({"refs": [source["ref"]]}, sort_keys=True),
                     json.dumps(context, sort_keys=True), now, now),
                )
        existing = db.workbench_items.get(item_id, include_parked=True)
        if existing is None:
            continue
        items.append(existing)
    return items

def deliver_run(db: Any, principal: Any, run: Any) -> list[dict[str, Any]]:
    """Put each new occurrence result of one run where its automation says.

    Idempotent: a note, a Door item or a prepared send is made once for one
    result. A failed delivery is logged and returned; it never fails the run.
    """
    run_id = str((run or {}).get("run_id") or "") if isinstance(run, dict) else ""
    if not run_id or (isinstance(run, dict) and run.get("replayed")):
        return []
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT a.id AS artifact_id, a.source_run_id, i.id AS item_id, i.workbench_id, i.title, i.result
               FROM artifacts a JOIN workbench_items i ON i.id = a.source_item_id
               WHERE a.source_run_id = ? AND i.status = 'done'
                 AND json_extract(i.context_json, '$.occurrence') = 1""",
            (run_id,),
        ).fetchall()
    outcomes = []
    for row in rows:
        wb = db.workbenches.get(str(row["workbench_id"]), include_deleted=True)
        if wb is None:
            continue
        try:
            outcomes.append(_deliver_one(db, _delivery_principal(principal), wb, dict(row)))
        except Exception as exc:  # a result stays readable on the automation
            log.warning("automation %s: delivery of %s failed: %s", wb.id, row["artifact_id"], exc)
            outcomes.append({"artifact_id": row["artifact_id"], "target": wb.output_target,
                             "outcome": "failed", "error": str(exc)})
    _finished_notices(db, rows)
    return outcomes
