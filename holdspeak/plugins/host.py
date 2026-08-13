"""Plugin host runtime for MIR execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import time
from threading import Lock
from typing import Any, Protocol

from ..kernel.provider_signals import CONTROL_SIGNALS, ProviderIndeterminate
from ..logging_config import get_logger
from .actuators import ActuatorProposal, ActuatorProposalError
from .intelligence import (
    PLUGIN_DISPATCH_CHAIN_CARDINALITY,
    PLUGIN_DISPATCH_KEY,
    PLUGIN_DISPATCH_REQUIRED,
    PluginDispatch,
    PluginDispatchRefused,
    _issue_plugin_dispatch,
)

log = get_logger("plugins.host")

#: The named refusal for an ``llm`` plugin that cannot be handed the admitted
#: engine (HS-131-08). An admitted plugin child names one frozen deployment
#: revision, so the plugin must run on THAT engine; a plugin with no injection
#: seam would silently build its own and make the receipt a lie.
PLUGIN_LLM_ENGINE_NOT_INJECTABLE = "plugin_llm_engine_not_injectable"


class PluginEngineNotInjectable(RuntimeError):
    """Raised when an admitted engine cannot be threaded into an llm plugin."""

    def __init__(self, plugin_id: str) -> None:
        super().__init__(f"{PLUGIN_LLM_ENGINE_NOT_INJECTABLE}:{plugin_id}")
        self.reason = PLUGIN_LLM_ENGINE_NOT_INJECTABLE


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
    status: str  # success | proposed | error | timeout | deduped | blocked | queued
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
        context_providers: list[Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
    ) -> None:
        self._plugins: dict[str, HostPlugin] = {}
        self._default_timeout_seconds = max(0.01, float(default_timeout_seconds))
        self._idempotency_cache: dict[str, PluginRunResult] = {}
        # Reserved for HS-37-04: gates *execution* of an approved actuator
        # proposal. It does NOT gate *proposing* — an actuator always runs to
        # build a proposal (status `proposed`), which performs no side effect.
        self._allow_actuators = bool(allow_actuators)
        self._enabled_capabilities = {
            str(cap).strip().lower()
            for cap in (enabled_capabilities or set())
            if str(cap).strip()
        }
        self._context_providers = list(context_providers or [])
        self._deferred_lock = Lock()
        self._deferred_runs: list[DeferredPluginRun] = []
        self._deferred_keys: set[str] = set()
        self._metrics_lock = Lock()
        self._metrics: dict[str, int] = {
            "runs_total": 0,
            "success": 0,
            "proposed": 0,
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
                "proposed": int(self._metrics["proposed"]),
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

    def register_context_provider(
        self,
        provider: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Register a callable that enriches every plugin context."""
        self._context_providers.append(provider)

    def get_plugin(self, plugin_id: str) -> HostPlugin | None:
        return self._plugins.get(str(plugin_id))

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins.keys())

    @contextmanager
    def issued_dispatch(
        self, engine: Any, cancellation: Any = None
    ) -> Iterator[PluginDispatch]:
        """Issue ONE plugin dispatch handle over an admitted child's engine.

        The handle is the caller's to pass into exactly the runs that child
        authorizes; the host keeps NO reference to it. Released on exit, so the
        moment the child's dispatch returns, a worker still holding it (a timeout
        the host abandoned) refuses instead of completing late.

        Refuses by name for an unadmitted or incompatible engine — before any
        plugin runs, so before any prompt exists.
        """
        handle = _issue_plugin_dispatch(engine=engine, cancellation=cancellation)
        try:
            yield handle
        finally:
            handle.release()

    def _wants_llm(self, plugin: HostPlugin) -> bool:
        return "llm" in {
            str(cap).strip().lower()
            for cap in (getattr(plugin, "required_capabilities", None) or [])
        }

    def _run_plugin(
        self, plugin: HostPlugin, context: dict[str, Any], dispatch: Any = None
    ) -> Any:
        """Run one plugin, with the admitted handle carried BY THIS INVOCATION.

        ``context`` is already this invocation's private copy, so the handle it
        carries cannot be seen by any other run — including a worker this host
        timed out and abandoned, which keeps only its own (released) handle.

        An ``llm`` plugin with no handle refuses by name rather than resolving a
        provider of its own; a deterministic plugin never sees the key.
        """
        if not self._wants_llm(plugin):
            return plugin.run(context)
        plugin_id = str(getattr(plugin, "id", "unknown"))
        if dispatch is None:
            raise PluginDispatchRefused(PLUGIN_DISPATCH_REQUIRED, plugin_id)
        # Delivered, not installed. A plugin that reads the key gets the admitted
        # handle; one that ignores it simply does no model work, because the
        # fallback it would have used no longer exists.
        return plugin.run({**context, PLUGIN_DISPATCH_KEY: dispatch})

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

    def _enrich_context(self, context: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(context)
        for provider in self._context_providers:
            try:
                provided = provider(dict(enriched))
            except Exception as exc:
                log.warning("Plugin context provider failed: %s", exc)
                continue
            if isinstance(provided, dict):
                enriched.update(provided)
        return enriched

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
        dispatch: PluginDispatch | None = None,
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
            dispatch=dispatch,
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
        dispatch: PluginDispatch | None = None,
    ) -> PluginRunResult:
        """Run one plugin. ``dispatch`` is THIS invocation's admitted handle.

        The handle is an argument, never host state: it reaches exactly the
        worker started below and nothing else.
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            raise KeyError(f"Unknown plugin: {plugin_id}")

        # A caller cannot smuggle authority in through the context, and neither
        # can a context provider: the reserved key is the HOST's to set, on the
        # worker's private copy, from the handle it was explicitly given.
        context = self._enrich_context(
            {key: value for key, value in dict(context).items() if key != PLUGIN_DISPATCH_KEY}
        )
        context.pop(PLUGIN_DISPATCH_KEY, None)

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

        # HS-37-01: actuators PROPOSE; they do not act. Running an actuator
        # to build a proposal is always safe (no side effect), so it is not
        # gated here — the capability gate below is the per-plugin opt-in,
        # and `self._allow_actuators` is reserved for gating the *execution*
        # of an approved proposal (the guarded executor, HS-37-04). The
        # actuator's output is interpreted as an `ActuatorProposal` in the
        # run path and surfaced as a `proposed` result.

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
        future = executor.submit(self._run_plugin, plugin, dict(context), dispatch)
        try:
            raw_output = future.result(timeout=run_timeout)
            duration_ms = (time.monotonic() - started_at) * 1000.0
            if self._is_actuator_plugin(plugin):
                # HS-37-01: an actuator's run() returns an ActuatorProposal,
                # not a side effect. The host records the proposal (status
                # `proposed`); it never executes here. A malformed proposal
                # is the actuator's fault → a normal `error`, no side effect.
                try:
                    proposal = ActuatorProposal.from_run_output(raw_output)
                except ActuatorProposalError as exc:
                    status = "error"
                    output: dict[str, Any] | None = None
                    error: str | None = f"Invalid actuator proposal: {exc}"
                else:
                    status = "proposed"
                    output = proposal.to_payload()
                    error = None
            else:
                status = "success"
                output = raw_output if isinstance(raw_output, dict) else {"result": raw_output}
                error = None
            result = PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(getattr(plugin, "version", "unknown")),
                status=status,
                idempotency_key=key,
                duration_ms=duration_ms,
                output=output,
                error=error,
            )
            if status in ("success", "proposed"):
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
            # THE timeout election, in ONE atomic step (HS-131-14). Revoking and
            # ASKING are the same call because they cannot be two: reading
            # `dispatch.calls` and releasing afterwards leaves a gap in which the
            # abandoned worker claims the completion — the host has already
            # decided "nothing physical happened" and records an ordinary
            # `timeout`, and then the request goes out. `release()` therefore
            # revokes and returns the verdict under one lock, so the two possible
            # worlds are decided here and cannot both happen:
            #
            #   claimed   -> a request is (or was) in flight; the outcome cannot be
            #                known, so the child is told INDETERMINATE and
            #                publishes nothing (Article XI.2).
            #   unclaimed -> the handle is dead before any request existed; an
            #                ordinary `timeout` record is honest, and the worker
            #                is now guaranteed unable to claim.
            #
            # `issued_dispatch`'s own release, as this dispatch unwinds, is then a
            # harmless idempotent repeat that reports the same verdict.
            claimed = dispatch.release() if dispatch is not None else False
            if claimed:
                self._increment_metric("timeout")
                self._log_event(
                    event="mir_plugin_run_finish",
                    meeting_id=meeting_id,
                    window_id=window_id,
                    plugin_id=plugin_id,
                    intent_set=intent_set,
                    context=context,
                    status="timeout",
                    error="indeterminate: a physical attempt was in flight",
                )
                raise ProviderIndeterminate(
                    f"plugin {plugin_id} timed out with a physical attempt in flight"
                )
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
        except CONTROL_SIGNALS:
            # HS-131-14: the kernel's typed signals are the RUNNER's business. A
            # dialect retry recorded here as an `error` plugin record would close
            # the admitted child `succeeded` and the second attempt would never be
            # admitted — one physical attempt, one dead receipt, a working endpoint
            # reported as failed. Ordered ahead of the catch-all on purpose.
            raise
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
        dispatch: PluginDispatch | None = None,
    ) -> list[PluginRunResult]:
        """Execute chain left-to-right while isolating plugin failures.

        A handle belongs to ONE plugin child. Offering one to a chain is refused
        here — before any plugin runs, so before any prompt exists — because the
        alternative is a chain of plugins sharing one child's revision, ordinal,
        and terminal receipt. An admitted caller therefore passes a one-plugin
        chain per child; an unadmitted caller passes no handle and runs the whole
        chain deterministically, exactly as before.
        """
        chain = list(plugin_chain)
        if dispatch is not None and len(chain) != 1:
            raise PluginDispatchRefused(
                PLUGIN_DISPATCH_CHAIN_CARDINALITY,
                detail=f"{len(chain)} plugins under one admitted child",
            )
        results: list[PluginRunResult] = []
        for plugin_id in chain:
            try:
                result = self.execute(
                    plugin_id,
                    context=context,
                    meeting_id=meeting_id,
                    window_id=window_id,
                    transcript_hash=transcript_hash,
                    timeout_seconds=timeout_seconds,
                    defer_heavy=defer_heavy,
                    dispatch=dispatch,
                )
            except CONTROL_SIGNALS:
                raise  # the runner's signal, not this chain's per-plugin failure
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
