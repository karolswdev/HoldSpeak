"""The kernel receipt readback as an application operation (PHILO-7-02).

One read over the SAME ``kernel.read`` the HTTP route serves
(``GET /api/kernel/read?refs=operation:<id>&view=receipt``,
``holdspeak/web/routes/system/kernel_routes.py``). Read-only (Article XI.5):
it makes no kernel operation. The kernel's own read scope applies: an agent
reads only its own operations (``principal_read_scope_required``).
"""
from __future__ import annotations

from typing import Any


class KernelReadService:
    def __init__(self, db: Any) -> None:
        self._db = db

    def read_receipt(self, principal: Any, operation_id: str) -> dict[str, Any]:
        from ..kernel.runtime import _configure

        ref = str(operation_id or "")
        ref = ref if ref.startswith("operation:") else f"operation:{ref}"
        return _configure(self._db).read([ref], "receipt", "committed", principal)
