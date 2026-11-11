"""Hub-local callbacks behind the declared system operations.

The composition root binds the running hub's context, never a second runtime.
Reads keep the old fail-soft state and status envelopes. Queue processing is
the owner's press and uses the runtime's existing queue callback.
"""
from __future__ import annotations

from typing import Any

from ..logging_config import get_logger
from .errors import ServiceError, ValidationError

log = get_logger("system_service")


class SystemService:
    def __init__(self, context: Any) -> None:
        self._context = context
        import threading
        self._worker: list[Any] = []
        self._key_guard = threading.Lock()
        self._key_locks: dict[str, Any] = {}

    def state(self, principal: Any) -> dict[str, Any]:
        try:
            return self._context.get_state() or {}
        except Exception as exc:
            log.error("get_state failed: %s", exc)
            return {}

    def devices_health(self, principal: Any) -> dict[str, Any]:
        from ..meeting_session import _device_descriptor_to_dict

        return {"devices": [_device_descriptor_to_dict(row) for row in self._context.device_registry.active()]}

    def runtime_status(self, principal: Any) -> dict[str, Any]:
        from ..runtime_status import _normalize_runtime_status_payload

        state = self.state(principal)
        callback = self._context.on_get_status
        if callback is not None:
            try:
                payload = callback()
            except Exception as exc:
                log.error("on_get_status failed: %s", exc)
                raise ServiceError("runtime_status_failed", str(exc), context={"status": 500}) from exc
            if not isinstance(payload, dict):
                return {"status": "ok", "runtime_status": payload}
        else:
            payload = {}
        return _normalize_runtime_status_payload(payload, state)

    def identity(self, principal: Any) -> dict[str, Any]:
        from ..runtime_identity import identity_report

        return identity_report(detailed=True)

    def process_plugin_jobs(self, principal: Any, *, max_jobs: int | None = None,
                            mode: str = "respect_backoff") -> dict[str, Any]:
        callback = self._context.on_process_plugin_jobs
        if callback is None:
            raise ServiceError("plugin_queue_unavailable", "Deferred plugin queue processing not supported",
                               context={"status": 501})
        if max_jobs is not None and (isinstance(max_jobs, bool) or not isinstance(max_jobs, int) or max_jobs <= 0):
            raise ValidationError("max_jobs must be greater than 0")
        mode = str(mode or "respect_backoff").strip().lower()
        if mode not in {"respect_backoff", "retry_now"}:
            raise ValidationError("mode must be respect_backoff or retry_now")
        data = callback(max_jobs=max_jobs, include_scheduled=mode == "retry_now")
        result = dict(data) if isinstance(data, dict) else {"processed": int(data)}
        result.update(mode=mode, success=True)
        self._context.broadcast("plugin_jobs_processed", result)
        return result

    def _blocking_io_tools(self) -> frozenset[str]:
        """The tools that run beside the ordered queue: declared blocking I/O, and the long tools."""
        from .. import operations as _operations
        from ..mcp.long_tools import LONG_TOOLS

        return frozenset(d.name for d in _operations.DESCRIPTORS if d.blocking_io) | frozenset(LONG_TOOLS)

    def _locks_for(self, keys: list[str]) -> list[Any]:
        """One lock per key (``holdspeak/mcp/long_tools.py:lock_keys``), made once."""
        import threading
        with self._key_guard:
            return [self._key_locks.setdefault(key, threading.Lock()) for key in keys]

    def _tool_worker(self) -> Any:
        """The one thread that runs MCP tool calls, first in, first out."""
        if not self._worker:
            from concurrent.futures import ThreadPoolExecutor

            self._worker.append(ThreadPoolExecutor(max_workers=1, thread_name_prefix="holdspeak-mcp-tools"))
        return self._worker[0]

    async def mcp_message(self, principal: Any, message: dict[str, Any], *, palette: Any,
                          call_gate: Any, resource_gate: Any, run_agent: bool,
                          client_host: str, identity_label: str, credential_identity: str | None, origin_value: str) -> Any:
        """Run protocol work on the one queue, preserving per-object locks and trace custody."""
        from ..mcp.server import handle_message_for_principal
        from ..services.observer import _origin, _caller, _caller_identity

        def handle() -> Any:
            # Per-key locks (Astra on #867): calls on one object run one at a
            # time, whichever path they take; calls on different objects run
            # in parallel. Taken in sorted order, so no two calls deadlock.
            held: list[Any] = []
            call: dict[str, Any] = {}
            if message.get("method") == "tools/call":
                call = message.get("params") if isinstance(message.get("params"), dict) else {}
                arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
                from ..mcp.long_tools import lock_keys, run_lock_keys

                keys = run_lock_keys if run_agent else lock_keys
                held = self._locks_for(keys(str(call.get("name") or ""), arguments))
            for lock in held:
                lock.acquire()
            origin_token = _origin.set(origin_value)
            caller_token = _caller.set(client_host)
            identity_token = _caller_identity.set(identity_label)
            try:
                gates = (
                    {"call_gate": call_gate, "resource_gate": resource_gate}
                    if call_gate is not None or resource_gate is not None
                    else {}
                )
                response = handle_message_for_principal(message, principal, palette=palette, **gates)
                if run_agent and message.get("method") == "tools/call":
                    # Betterment M2: the run's call, against its run (Looked
                    # at / Wrote / Prepared on the automation's result).
                    from ..services import run_trace

                    run_trace.record_call(
                        run_trace.run_id_of(credential_identity),
                        str(call.get("name") or ""), call.get("arguments"), response,
                    )
                elif credential_identity is not None and message.get("method") == "tools/call":
                    # Betterment AG10: a launched agent's call, against its
                    # launch (Looked at / Wrote / Prepared on its Result).
                    from ..services import run_trace

                    launch_key = run_trace.launch_key_of(credential_identity)
                    if launch_key:
                        run_trace.record_call(
                            launch_key, str(call.get("name") or ""), call.get("arguments"), response,
                        )
                return response
            finally:
                _origin.reset(origin_token)
                _caller.reset(caller_token)
                _caller_identity.reset(identity_token)
                for lock in reversed(held):
                    lock.release()

        # A tool call never runs on the event loop. A tool message is synchronous;
        # one that calls an async service hands the coroutine back to this loop
        # (``holdspeak/mcp/aio.py``) and waits for it, and on the loop that wait
        # is impossible (before 2026-10-03 every async tool refused here).
        #
        # Order (PHILO-10-02 GATE 2, kept): tool calls run ONE AT A TIME, in
        # arrival order, on the one MCP worker thread. The services are not
        # safe for two writers (two ``desk.update`` calls on one Note lose a
        # change). Two exceptions run on the thread pool beside that queue: an
        # operation that DECLARES blocking I/O
        # (``OperationDescriptor.blocking_io``) and a tool named in
        # ``holdspeak/mcp/long_tools.py`` (a model call, gh, acli). Every call
        # takes its per-key locks first (``handle`` above), so a slow tool
        # holds only the calls on its own objects. A third: every call of an
        # agent CLI run (``run_agent`` above), whose parent may be the very
        # call the queue is running.
        # The flag decides ordering only; no tool needs it to work.
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        if message.get("method") != "tools/call":
            response = handle()
        elif run_agent or params.get("name") in self._blocking_io_tools():
            from starlette.concurrency import run_in_threadpool

            response = await run_in_threadpool(handle)
        else:
            import asyncio

            response = await asyncio.get_running_loop().run_in_executor(self._tool_worker(), handle)


        return response
