"""PARKED 20261109 (ops/projects): a route no client calls; only its own test held it.

Parked from ``holdspeak/web/routes/decision_records.py``: GET /api/decision-records.
MCP keeps ``decision_record.list``. Not imported. Kept for history; restore with
``git revert`` of the parking commit.
"""


def _parked_body(router=None, service=None, principal=None, **_):  # parked 2026-11-09: never mounted
    @router.get("")
    def list_records(
        request: Request, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        return service().list_records(principal(request), limit=limit, offset=offset)
