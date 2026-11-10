# Parked: SetupService.scan_lan is the one LAN discovery operation.
from typing import Any

class _ParkedBody:
    def discover_lan(self, principal: Any) -> dict[str, Any]:
        """Find private-LAN OpenAI-compatible engines for this one press; it reads ``/v1/models`` and writes nothing."""
        from ..kernel.external_egress import EgressOperationRefused
        from .errors import ServiceError
        from .lan_engine_discovery import checked_at, scan_lan_engines

        try:
            result = scan_lan_engines(principal=principal)
        except EgressOperationRefused as exc:
            raise ServiceError("concierge_lan_refused", exc.reason, context={"status": 403}) from exc
        return {**result, "checkedAt": checked_at()}
