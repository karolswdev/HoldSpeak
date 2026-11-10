"""The running hub's callbacks: declared HTTP-only operations with reasons.

These reads belong to the page shell and the loaded runtime. They are not
portable off-hub MCP reads. Queue processing uses the hub's bound callback.
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor


def _read(name: str, method: str, path: str, handler: str, description: str, reason: str, *,
          owner_only: bool = False) -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description,
        args_schema={"type": "object", "properties": {}, "additionalProperties": False},
        principal="derived by the HTTP edge", effect="read", result="the loaded hub's callback answer",
        refusals=_CONTRACT_REFUSALS + (("owner_required",) if owner_only else ()),
        completion="synchronous; a read of this running hub", exposure=(f"http:GET {path}",),
        service="system_service", method=method, owner_only=owner_only, blocking_io=True,
        call=lambda s, p, a: getattr(s, method)(p), http=("GET", path), handler=handler,
        http_only_reason=reason,
    )


SYSTEM_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _read("system.state", "state", "/api/state", "api_state", "Read the current meeting state.",
          "The Desk reads the running hub's meeting callback; no off-hub state exists."),
    _read("system.devices.health", "devices_health", "/api/devices/health", "api_devices_health",
          "Read the active devices on this hub.", "The page shell reads the running hub's device registry."),
    _read("system.runtime.status", "runtime_status", "/api/runtime/status", "api_runtime_status",
          "Read the loaded runtime's status.", "The page shell reads the running hub's status callback."),
    _read("system.identity", "identity", "/api/system/identity", "api_system_identity",
          "Read the loaded runtime identity and its repair diagnoses.",
          "Owner diagnostics contain the database path, process id and owner-lock record.", owner_only=True),
    OperationDescriptor(
        name="plugin_job.process", version=1, description="Process the hub's deferred plugin queue once.",
        args_schema={"type": "object", "properties": {"max_jobs": {"type": ["integer", "null"]},
                                                    "mode": {"type": "string"}}, "additionalProperties": False},
        principal="derived by the HTTP edge; the owner's press", effect="write", result="{processed, mode, success}",
        refusals=_CONTRACT_REFUSALS + ("owner_required", "plugin_queue_unavailable", "ValidationError"),
        completion="synchronous; announces plugin_jobs_processed once",
        exposure=("http:POST /api/plugin-jobs/process",), service="system_service", method="process_plugin_jobs",
        owner_only=True, owner_press=True, blocking_io=True, authority="config",
        call=lambda s, p, a: s.process_plugin_jobs(p, **a), http=("POST", "/api/plugin-jobs/process"),
        handler="process", http_only_reason="The owner's local press drains the running hub's in-process queue.",
    ),
)


def system_service(context: Any) -> Any:
    """A partial route composition uses the same callback adapter as the hub."""
    from holdspeak.services.system_service import SystemService

    return SystemService(context)
