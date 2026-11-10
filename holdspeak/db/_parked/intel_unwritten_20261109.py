# PARKED: routed-only readers retired with the unwritten routing tables on 2026-11-09.
from __future__ import annotations

class _Parked__is_unsettled_stop_reservation_in_transaction:
    @staticmethod
    def _is_unsettled_stop_reservation_in_transaction(conn: Any, job: Any | None) -> bool:
        """Whether this exact leaf is an inert C3 Stop reservation.

        Generic Retry/Skip may never rewrite provider-owned work while the Stop
        primitive has no settlement.  Both queue lifecycle fields are checked so
        an old skipped/superseded record cannot later qualify for unknown recovery.
        """
        if (
            job is None
            or str(job["status"] or "") != "reserved"
            or str(job["lifecycle_posture"] or "") != "reserved"
        ):
            return False
        return conn.execute(
            """SELECT 1 FROM inference_parent_stop_handoffs h
                 LEFT JOIN inference_parent_stop_handoff_settlements s
                   ON s.command_id=h.command_id
                WHERE h.evidence_ref=?
                  AND h.evidence_provider_id='meeting-deferred-queue'
                  AND h.evidence_provider_revision=1
                  AND s.command_id IS NULL
                LIMIT 1""",
            (str(job["job_id"]),),
        ).fetchone() is not None


class _Parked_has_unsettled_stop_reservation:
    def has_unsettled_stop_reservation(self, meeting_id: str) -> bool:
        """Return whether the current lineage leaf is an inert Stop handoff."""
        with self._connection() as conn:
            job = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT * FROM current_jobs WHERE meeting_id=? AND current_rank=1 LIMIT 1
                """,
                (meeting_id,),
            ).fetchone()
            return self._is_unsettled_stop_reservation_in_transaction(conn, job)


