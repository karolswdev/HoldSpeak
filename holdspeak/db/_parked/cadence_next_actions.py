# PARKED 2026-11-12: no reachable caller or reader of saved next actions.
from __future__ import annotations

import uuid
from holdspeak.cadence.models import NextBestAction
from holdspeak.timestamps import utc_now_iso as _now


class _ParkedBody:
    # ── next actions ───────────────────────────────────────────────────────
    def add_next_action(self, action: NextBestAction) -> str:
        action_id = action.id or uuid.uuid4().hex
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cadence_next_actions
                    (id, loop_id, kind, title, body_markdown, confidence, reversible,
                     proposal_id, generated_by, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (action_id, action.loop_id, action.kind, action.title, action.body_markdown,
                 action.confidence, 1 if action.reversible else 0, action.proposal_id,
                 action.generated_by, action.generated_at or _now()),
            )
        return action_id

