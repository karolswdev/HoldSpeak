"""The single-flight Delivery collector (HS-94-02).

PLATFORM-CONTRACT §11, made concrete:

- one provider pass per registered source, wrapping the source's own
  vendored dw (``dw_argv_base`` semantics from the mission-control
  bridge, per-source repo root);
- single-flight: an in-flight refresh coalesces every concurrent
  caller onto one result — N readers cause exactly one set of dw
  invocations;
- every subprocess call is bounded (per-call timeout + one global
  ``threading.Semaphore``) and runs on whatever worker thread called
  the collector — the routes call via ``asyncio.to_thread`` (the
  Phase-85 event-loop rule);
- payload hash -> snapshot revision; one composed replayable cursor;
- last-known-good retained per source with its ``observed_at``; a
  failing source degrades to a typed status and never erases a
  healthy one;
- unsupported dw schemas disable only the affected capability
  (status ``incompatible``), never the snapshot;
- clients polling the cached snapshot never trigger a fresh dw run —
  refresh happens only past the bounded-age policy or an explicit
  ``invalidate()``.

Error details are CLASSIFIED strings ("dw exited 2", "dw timed
out"), never raw stderr or paths — §12.3 forbids leaking either to
clients.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .read_model import build_snapshot, compose_cursor, parse_cursor, sanitize_event
from .registry import DeliveryRegistry, SourceRecord

DW_TIMEOUT_SECONDS = 30
DEFAULT_MAX_AGE_SECONDS = 15.0
DEFAULT_MAX_SUBPROCESSES = 4
MAX_BUFFERED_EVENTS = 500

# The dw schema versions this collector is proven against
# (tests/unit/test_dw_counterpart_contract.py).
CAPABILITIES_SCHEMA_PROVEN = 1
FEED_SCHEMA_PROVEN = 1
EVENTS_SCHEMA_PROVEN = 2

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def _default_runner(argv: list[str], cwd: Optional[str] = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=DW_TIMEOUT_SECONDS,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class _SourceState:
    """Per-source retained state: the last-known-good rows, the
    per-source dw cursor, and the bounded event buffer."""

    status: str = "unavailable"
    detail: str = "not yet collected"
    observed_at: str = ""
    capabilities: Optional[dict[str, Any]] = None
    projects: Optional[list[dict[str, Any]]] = None
    cursor: str = "0"
    events: list[dict[str, Any]] = field(default_factory=list)


class DeliveryCollector:
    """One collector per hub; one provider pass per source."""

    def __init__(
        self,
        registry: DeliveryRegistry,
        *,
        runner: Optional[Runner] = None,
        dw_argv_factory: Optional[Callable[[Path], Optional[list[str]]]] = None,
        max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
        max_subprocesses: int = DEFAULT_MAX_SUBPROCESSES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._registry = registry
        self._runner = runner or _default_runner
        self._dw_argv = dw_argv_factory or self._default_dw_argv
        self._max_age = float(max_age_seconds)
        self._clock = clock
        self._subprocess_gate = threading.Semaphore(max(1, int(max_subprocesses)))
        self._lock = threading.Lock()
        self._flight: Optional[threading.Event] = None
        self._snapshot: Optional[dict[str, Any]] = None
        self._collected_at: float = float("-inf")
        self._states: dict[str, _SourceState] = {}

    @staticmethod
    def _default_dw_argv(root: Path) -> Optional[list[str]]:
        from ..missioncontrol_bridge import dw_argv_base

        return dw_argv_base(root)

    # ── the public read surface ──────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        """The cached coherent snapshot. A poll inside the bounded-age
        window NEVER shells out (§11); past it, one single-flighted
        refresh runs and every waiter shares the result."""
        with self._lock:
            if (
                self._snapshot is not None
                and (self._clock() - self._collected_at) < self._max_age
            ):
                return self._snapshot
        return self.refresh()

    def refresh(self) -> dict[str, Any]:
        """Single-flight collection: the first caller leads, everyone
        arriving mid-flight waits for the leader's result instead of
        launching a second fleet of CLIs."""
        with self._lock:
            flight = self._flight
            leader = flight is None
            if leader:
                # Re-check freshness at leadership: a caller that saw a
                # stale snapshot but lost the race to a just-finished
                # leader must not launch a second fleet of CLIs.
                if (
                    self._snapshot is not None
                    and (self._clock() - self._collected_at) < self._max_age
                ):
                    return self._snapshot
                flight = self._flight = threading.Event()
        assert flight is not None
        if not leader:
            flight.wait(timeout=DW_TIMEOUT_SECONDS * 4)
            with self._lock:
                if self._snapshot is not None:
                    return self._snapshot
            # The leader failed to produce anything; fall through to a
            # fresh attempt rather than return nothing.
            return self.refresh()
        try:
            snapshot = self._collect()
            with self._lock:
                self._snapshot = snapshot
                self._collected_at = self._clock()
            return snapshot
        finally:
            with self._lock:
                self._flight = None
            flight.set()

    @property
    def has_collected(self) -> bool:
        with self._lock:
            return self._snapshot is not None

    def invalidate(self) -> None:
        """Cursor-invalidation hook: the next read collects fresh.
        Retained state (last-known-good, buffers) stays."""
        with self._lock:
            self._collected_at = float("-inf")

    def events_after(self, cursor_text: Optional[str]) -> dict[str, Any]:
        """Replay from the composed cursor, served from the retained
        buffers — a poll here never runs dw. Unknown or malformed
        cursors replay the whole retained window (safe superset)."""
        per_source = parse_cursor(cursor_text)
        with self._lock:
            cursors: dict[str, str] = {}
            events: list[dict[str, Any]] = []
            for source_id, state in self._states.items():
                cursors[source_id] = state.cursor
                after = _as_int(per_source.get(source_id, "0"))
                for event in state.events:
                    if _as_int(event.get("event_id")) > after:
                        events.append(event)
            return {
                "delivery_schema": 1,
                "cursor": compose_cursor(cursors),
                "events": events,
            }

    def sources_view(self) -> dict[str, Any]:
        """The registry view plus freshness — labels, opaque IDs, and
        typed statuses; no paths, no shelling."""
        with self._lock:
            rows = []
            for source in self._registry.sources():
                state = self._states.get(source.source_id, _SourceState())
                rows.append(
                    {
                        **source.to_wire(),
                        "status": state.status,
                        "detail": state.detail,
                        "observed_at": state.observed_at,
                    }
                )
        return {"registry_schema": 1, "sources": rows}

    def register_source(
        self, path: str, *, label: Optional[str] = None
    ) -> dict[str, Any]:
        """Server-side registration (the §10 POST flow): resolve and
        validate the path here, hand back wire shapes only, and
        invalidate so the next read collects the newcomer."""
        with self._lock:
            source, worktree = self._registry.register(path, label=label)
            self._collected_at = float("-inf")
        return {"source": source.to_wire(), "worktree_id": worktree.worktree_id}

    # ── collection ───────────────────────────────────────────────

    def _run_json(
        self, argv: list[str], cwd: Path
    ) -> tuple[Optional[Any], str]:
        """(document, classified_error). The error string is wire-safe:
        no argv, no stderr, no paths."""
        with self._subprocess_gate:
            try:
                proc = self._runner(argv, str(cwd))
            except subprocess.TimeoutExpired:
                return None, "dw timed out"
            except OSError:
                return None, "dw failed to start"
        if proc.returncode != 0:
            return None, f"dw exited {proc.returncode}"
        try:
            return json.loads(proc.stdout), ""
        except (json.JSONDecodeError, ValueError, TypeError):
            return None, "dw did not return JSON"

    def _collect(self) -> dict[str, Any]:
        generated_at = _utc_now()
        rows: list[dict[str, Any]] = []
        cursors: dict[str, str] = {}
        for source in self._registry.sources():
            with self._lock:
                state = self._states.setdefault(source.source_id, _SourceState())
            self._collect_source(source, state)
            with self._lock:
                cursors[source.source_id] = state.cursor
                rows.append(self._wire_row(source, state))
        return build_snapshot(rows, cursors, generated_at)

    def _collect_source(self, source: SourceRecord, state: _SourceState) -> None:
        """One provider pass. Failures degrade; they never raise and
        never clear retained last-known-good data."""
        root = Path(source.primary_path or "")
        argv_base = self._dw_argv(root) if source.primary_path else None
        if argv_base is None:
            self._degrade(state, "no dw CLI")
            return

        errors: list[str] = []
        disabled: list[str] = []

        caps_doc, err = self._run_json([*argv_base, "capabilities", "--json"], root)
        if caps_doc is None:
            self._degrade(state, err or "capabilities unavailable")
            return
        if (
            not isinstance(caps_doc, dict)
            or caps_doc.get("capabilities_schema") != CAPABILITIES_SCHEMA_PROVEN
        ):
            found = (
                caps_doc.get("capabilities_schema")
                if isinstance(caps_doc, dict)
                else None
            )
            state.status = "incompatible"
            state.detail = (
                f"capabilities_schema {found!r} unsupported "
                f"(proven {CAPABILITIES_SCHEMA_PROVEN})"
            )
            return
        schemas = caps_doc.get("schemas") or {}

        # Projects/stories capability: gated on feed_schema.
        if schemas.get("feed_schema") != FEED_SCHEMA_PROVEN:
            disabled.append("projects")
        else:
            feed_doc, err = self._run_json([*argv_base, "state", "--json"], root)
            if feed_doc is None:
                errors.append(err or "state unavailable")
            elif (
                not isinstance(feed_doc, dict)
                or feed_doc.get("feed_schema") != FEED_SCHEMA_PROVEN
            ):
                disabled.append("projects")
            else:
                state.projects = [
                    p for p in feed_doc.get("projects") or [] if isinstance(p, dict)
                ]
                state.observed_at = _utc_now()

        # Rail-events capability: gated on events_schema (the cursor
        # envelope, dw counterpart HS-94-01).
        if schemas.get("events_schema") != EVENTS_SCHEMA_PROVEN:
            disabled.append("events")
        else:
            events_doc, err = self._run_json(
                [*argv_base, "events", "--json", "--after", state.cursor], root
            )
            if events_doc is None:
                errors.append(err or "events unavailable")
            elif (
                not isinstance(events_doc, dict)
                or events_doc.get("events_schema") != EVENTS_SCHEMA_PROVEN
            ):
                disabled.append("events")
            else:
                fresh = [
                    sanitize_event(e, source.source_id)
                    for e in events_doc.get("events") or []
                    if isinstance(e, dict)
                ]
                state.events = (state.events + fresh)[-MAX_BUFFERED_EVENTS:]
                state.cursor = str(events_doc.get("source_cursor") or state.cursor)

        state.capabilities = {
            "schemas": schemas,
            "statuses": caps_doc.get("statuses") or [],
            "verbs": caps_doc.get("verbs") or [],
            "features": caps_doc.get("features") or {},
            "disabled": disabled,
        }
        if disabled:
            state.status = "incompatible"
            state.detail = "unsupported dw schema for: " + ", ".join(disabled)
        elif errors:
            self._degrade(state, "; ".join(errors))
        else:
            state.status = "live"
            state.detail = ""

    @staticmethod
    def _degrade(state: _SourceState, detail: str) -> None:
        """A failing source keeps its last-known-good rows and its
        original observed_at; the status says how it failed and
        whether anything is retained (§4.1, §13)."""
        state.status = "stale" if state.observed_at else "unavailable"
        state.detail = detail

    @staticmethod
    def _wire_row(source: SourceRecord, state: _SourceState) -> dict[str, Any]:
        return {
            "source_id": source.source_id,
            "node_id": source.node_id,
            "label": source.label,
            "status": state.status,
            "detail": state.detail,
            "observed_at": state.observed_at,
            "capabilities": state.capabilities,
            "worktrees": [wt.to_wire() for wt in source.worktrees],
            # None (not []) when never observed: an empty array only
            # ever means a known-empty source (§13).
            "projects": state.projects,
            # Session/attempt rows join in HS-94-04 (work attempts).
            "sessions": None,
        }


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
