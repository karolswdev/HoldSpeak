# PARKED: routed-only readers retired with the unwritten routing tables on 2026-11-09.
from __future__ import annotations

class _Parked__route_plan_dependencies:
    def _route_plan_dependencies(self, conn: Any, profile_id: str) -> list[dict[str, str]]:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='inference_route_plan_entries'"
        ).fetchone()
        if present is None:
            return []
        return [
            {"kind": "route_plan", "id": str(row["plan_id"])}
            for row in conn.execute(
                """SELECT DISTINCT plan_id FROM inference_route_plan_entries
                     WHERE profile_id=? ORDER BY plan_id""",
                (profile_id,),
            ).fetchall()
        ]
