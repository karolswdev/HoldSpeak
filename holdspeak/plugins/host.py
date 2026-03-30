"""Plugin host runtime for MIR execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import time
from threading import Lock
from typing import Any, Protocol

from ..logging_config import get_logger

log = get_logger("plugins.host")

_SENSITIVE_KEY_TOKENS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "authorization",
    "auth",
)


class HostPlugin(Protocol):
    """Minimal plugin contract for host execution."""

    id: str
    version: str

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class PluginRunResult:
    """Execution result for one plugin invocation."""

    plugin_id: str
    plugin_version: str
    status: str  # success | error | timeout | deduped | blocked | queued
    idempotency_key: str
    duration_ms: float
    output: dict[str, Any] | None = None
    error: str | None = None
    deduped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "error": self.error,
            "deduped": self.deduped,
        }


@dataclass(frozen=True)
class DeferredPluginRun:
    """Queued plugin run scheduled for deferred processing."""

    plugin_id: str
    plugin_version: str
    meeting_id: str
    window_id: str
    transcript_hash: str
    idempotency_key: str
    context: dict[str, Any]
    queued_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "meeting_id": self.meeting_id,
            "window_id": self.window_id,
            "transcript_hash": self.transcript_hash,
            "idempotency_key": self.idempotency_key,
            "context": dict(self.context),
            "queued_at": self.queued_at,
        }


def build_idempotency_key(
    *,
    meeting_id: str,
    window_id: str,
    plugin_id: str,
    transcript_hash: str,
) -> str:
    payload = json.dumps(
        {
            "meeting_id": str(meeting_id),
            "window_id": str(window_id),
            "plugin_id": str(plugin_id),
            "transcript_hash": str(transcript_hash),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PluginHost:
    """Registry + execution host with idempotency and timeout isolation."""

    def __init__(
        self,
        *,
        default_timeout_seconds: float = 2.0,
        enabled_capabilities: set[str] | None = None,
        allow_actuators: bool = False,
    ) -> None:
        self._plugins: dict[str, HostPlugin] = {}
        self._default_timeout_seconds = max(0.01, float(default_timeout_seconds))
        self._idempotency_cache: dict[str, PluginRunResult] = {}
        self._allow_actuators = bool(allow_actuators)
        self._enabled_capabilities = {
            str(cap).strip().lower()
            for cap in (enabled_capabilities or set())
            if str(cap).strip()
        }
        self._deferred_lock = Lock()
        self._deferred_runs: list[DeferredPluginRun] = []
        self._deferred_keys: set[str] = set()
        self._metrics_lock = Lock()
        self._metrics: dict[str, int] = {
            "runs_total": 0,
            "success": 0,
            "error": 0,
            "timeout": 0,
            "deduped": 0,
            "blocked": 0,
            "queued": 0,
        }

    def get_metrics(self) -> dict[str, int]:
        with self._metrics_lock:
            return {
                "runs_total": int(self._metrics["runs_total"]),
                "success": int(self._metrics["success"]),
                "error": int(self._metrics["error"]),
                "timeout": int(self._metrics["timeout"]),
                "deduped": int(self._metrics["deduped"]),
                "blocked": int(self._metrics["blocked"]),
                "queued": int(self._metrics["queued"]),
            }

    def reset_metrics(self) -> None:
        with self._metrics_lock:
            for key in self._metrics:
                self._metrics[key] = 0

    def _increment_metric(self, status: str) -> None:
        key = str(status).strip().lower()
        with self._metrics_lock:
            self._metrics["runs_total"] += 1
            if key in self._metrics:
                self._metrics[key] += 1

    def register(self, plugin: HostPlugin) -> None:
        plugin_id = str(getattr(plugin, "id", "")).strip()
        if not plugin_id:
            raise ValueError("Plugin must define non-empty `id`")
        if not hasattr(plugin, "run"):
            raise ValueError("Plugin must implement run(context)")
        self._plugins[plugin_id] = plugin

    def get_plugin(self, plugin_id: str) -> HostPlugin | None:
        return self._plugins.get(str(plugin_id))

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins.keys())

    def _is_actuator_plugin(self, plugin: HostPlugin) -> bool:
        kind = str(getattr(plugin, "kind", "")).strip().lower()
        return kind in {"actuator", "actuators"}

    def _missing_capabilities(self, plugin: HostPlugin) -> list[str]:
        required = [
            str(cap).strip().lower()
            for cap in (getattr(plugin, "required_capabilities", None) or [])
            if str(cap).strip()
        ]
        missing = sorted({cap for cap in required if cap not in self._enabled_capabilities})
        return missing

    def _is_deferred_plugin(self, plugin: HostPlugin) -> bool:
        mode = str(getattr(plugin, "execution_mode", "inline")).strip().lower()
        if mode in {"deferred", "queued", "queue", "heavy"}:
            return True
        return bool(getattr(plugin, "defer_execution", False))

    def _intent_set(self, context: dict[str, Any]) -> list[str]:
        intents = [
            str(intent).strip().lower()
            for intent in (context.get("active_intents") or [])
            if str(intent).strip()
        ]
        deduped: list[str] = []
        for intent in intents:
            if intent not in deduped:
                deduped.append(intent)
        return deduped

    def _context_keys(self, context: dict[str, Any]) -> list[str]:
        return sorted(str(key) for key in context.keys())

    def _redacted_keys(self, context: dict[str, Any]) -> list[str]:
        redacted: list[str] = []
        for key in context.keys():
            normalized = str(key).strip().lower()
            if any(token in normalized for token in _SENSITIVE_KEY_TOKENS):
                redacted.append(str(key))
        return sorted(redacted)

    def _log_event(
        self,
        *,
        event: str,
        meeting_id: str,
        window_id: str,
        plugin_id: str,
        intent_set: list[str],
        context: dict[str, Any],
        status: str | None = None,
        error: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "event": event,
            "meeting_id": str(meeting_id),
            "window_id": str(window_id),
            "plugin_id": str(plugin_id),
            "intent_set": list(intent_set),
            "context_keys": self._context_keys(context),
            "redacted_keys": self._redacted_keys(context),
        }
        if status is not None:
            payload["status"] = str(status)
        if error is not None:
            payload["error"] = str(error)
        log.info(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def list_deferred_runs(
        self,
        *,
        meeting_id: str | None = None,
        limit: int | None = None,
    ) -> list[DeferredPluginRun]:
        """Return queued deferred plugin runs in FIFO order."""
        with self._deferred_lock:
            runs = list(self._deferred_runs)
        if meeting_id:
            clean_meeting_id = str(meeting_id)
            runs = [run for run in runs if run.meeting_id == clean_meeting_id]
        if limit is not None:
            runs = runs[: max(0, int(limit))]
        return runs

    def pop_next_deferred_run(self) -> DeferredPluginRun | None:
        """Pop one deferred plugin run from the queue."""
        with self._deferred_lock:
            if not self._deferred_runs:
                return None
            run = self._deferred_runs.pop(0)
            self._deferred_keys.discard(run.idempotency_key)
            return run

    def process_next_deferred_run(
        self,
        *,
        timeout_seconds: float | None = None,
        allow_duplicate: bool = False,
    ) -> PluginRunResult | None:
        """Execute the next queued deferred run, if available."""
        queued = self.pop_next_deferred_run()
        if queued is None:
            return None
        return self.execute(
            queued.plugin_id,
            context=dict(queued.context),
            meeting_id=queued.meeting_id,
            window_id=queued.window_id,
            transcript_hash=queued.transcript_hash,
            timeout_seconds=timeout_seconds,
            allow_duplicate=allow_duplicate,
            defer_heavy=False,
        )

    def execute(
        self,
        plugin_id: str,
        *,
        context: dict[str, Any],
        meeting_id: str,
        window_id: str,
        transcript_hash: str,
        timeout_seconds: float | None = None,
        allow_duplicate: bool = False,
        defer_heavy: bool = True,
    ) -> PluginRunResult:
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            raise KeyError(f"Unknown plugin: {plugin_id}")

        key = build_idempotency_key(
            meeting_id=meeting_id,
            window_id=window_id,
            plugin_id=plugin_id,
            transcript_hash=transcript_hash,
        )

        intent_set = self._intent_set(context)
        self._log_event(
            event="mir_plugin_run_start",
            meeting_id=meeting_id,
            window_id=window_id,
            plugin_id=plugin_id,
            intent_set=intent_set,
            context=context,
        )

        if self._is_actuator_plugin(plugin) and not self._allow_actuators:
            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status="blocked",
                idempotency_key=key,
                duration_ms=0.0,
                error="Actuator plugins are disabled by default",
            )
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
                error=result.error,
            )
            return result

        missing_capabilities = self._missing_capabilities(plugin)
        if missing_capabilities:
            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status="blocked",
                idempotency_key=key,
                duration_ms=0.0,
                error=f"Missing capabilities: {', '.join(missing_capabilities)}",
            )
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
                error=result.error,
            )
            return result

        cached = self._idempotency_cache.get(key)
        if cached is not None and not allow_duplicate:
            result = PluginRunResult(
                plugin_id=cached.plugin_id,
                plugin_version=cached.plugin_version,
                status="deduped",
                idempotency_key=key,
                duration_ms=0.0,
                output=cached.output,
                error=cached.error,
                deduped=True,
            )
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
                error=result.error,
            )
            return result

        if defer_heavy and self._is_deferred_plugin(plugin):
            with self._deferred_lock:
                if key in self._deferred_keys and not allow_duplicate:
                    result = PluginRunResult(
                        plugin_id=plugin_id,
                        plugin_version=str(getattr(plugin, "version", "unknown")),
                        status="deduped",
                        idempotency_key=key,
                        duration_ms=0.0,
                        output={"deferred": True},
                        deduped=True,
                    )
                    self._increment_metric(result.status)
                    self._log_event(
                        event="mir_plugin_run_finish",
                        meeting_id=meeting_id,
                        window_id=window_id,
                        plugin_id=plugin_id,
                        intent_set=intent_set,
                        context=context,
                        status=result.status,
                    )
                    return result

                queued_run = DeferredPluginRun(
                    plugin_id=plugin_id,
                    plugin_version=str(getattr(plugin, "version", "unknown")),
                    meeting_id=str(meeting_id),
                    window_id=str(window_id),
                    transcript_hash=str(transcript_hash),
                    idempotency_key=key,
                    context=dict(context),
                    queued_at=datetime.now().isoformat(),
                )
                self._deferred_runs.append(queued_run)
                self._deferred_keys.add(key)

            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status="queued",
                idempotency_key=key,
                duration_ms=0.0,
                output={"deferred": True, "queued_at": queued_run.queued_at},
            )
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
            )
            return result

        run_timeout = self._default_timeout_seconds if timeout_seconds is None else max(0.01, float(timeout_seconds))
        started_at = time.monotonic()

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(plugin.run, dict(context))
        try:
            raw_output = future.result(timeout=run_timeout)
            duration_ms = (time.monotonic() - started_at) * 1000.0
            output = raw_output if isinstance(raw_output, dict) else {"result": raw_output}
            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status="success",
                idempotency_key=key,
                duration_ms=duration_ms,
                output=output,
            )
            self._idempotency_cache[key] = result
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
            )
            return result
        except FutureTimeoutError:
            future.cancel()
            duration_ms = (time.monotonic() - started_at) * 1000.0
            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status="timeout",
                idempotency_key=key,
                duration_ms=duration_ms,
                error=f"Timed out after {run_timeout:.2f}s",
            )
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
                error=result.error,
            )
            return result
        except Exception as exc:
            duration_ms = (time.monotonic() - started_at) * 1000.0
            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status="error",
                idempotency_key=key,
                duration_ms=duration_ms,
                error=f"{type(exc).__name__}: {exc}",
            )
            self._increment_metric(result.status)
            self._log_event(
                event="mir_plugin_run_finish",
                meeting_id=meeting_id,
                window_id=window_id,
                plugin_id=plugin_id,
                intent_set=intent_set,
                context=context,
                status=result.status,
                error=result.error,
            )
            return result
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def execute_chain(
        self,
        plugin_chain: list[str],
        *,
        context: dict[str, Any],
        meeting_id: str,
        window_id: str,
        transcript_hash: str,
        timeout_seconds: float | None = None,
        defer_heavy: bool = True,
    ) -> list[PluginRunResult]:
        """Execute chain left-to-right while isolating plugin failures."""
        results: list[PluginRunResult] = []
        for plugin_id in plugin_chain:
            try:
                result = self.execute(
                    plugin_id,
                    context=context,
                    meeting_id=meeting_id,
                    window_id=window_id,
                    transcript_hash=transcript_hash,
                    timeout_seconds=timeout_seconds,
                    defer_heavy=defer_heavy,
                )
            except Exception as exc:
                key = build_idempotency_key(
                    meeting_id=meeting_id,
                    window_id=window_id,
                    plugin_id=plugin_id,
                    transcript_hash=transcript_hash,
                )
                result = PluginRunResult(
                    plugin_id=plugin_id,
                    plugin_version="unknown",
                    status="error",
                    idempotency_key=key,
                    duration_ms=0.0,
                    error=f"{type(exc).__name__}: {exc}",
                )
            results.append(result)
        return results
