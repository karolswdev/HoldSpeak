"""PARKED 20261108 (late evening, the left-routes pass): service methods only a parked route called.

Parked from ``holdspeak/services/recipe_service.py``: RecipeService.cancel.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


class _ParkedBody:  # parked 2026-11-08: kept at method indent, never imported
    def cancel(self, principal: Principal, invocation_id: str) -> dict[str, str]:
        from ..kernel.runtime import _as_principal
        with _as_principal(principal): return {"invocation_id": invocation_id, "disposition": self._runner.cancel(invocation_id)}
