"""Workbench conductor: the scheduler that makes workbenches autonomous (HS-116-07).

A lightweight scheduler running inside the hub process. On hub start, it loads
all workbenches with schedule_enabled=True and checks for due workbenches every
60 seconds. Each scheduled run is a fresh, isolated session — no history
inheritance, explicit context only (the Hermes pattern).
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

from .logging_config import get_logger
from .services.errors import ServiceError

log = get_logger("workbench_conductor")

_conductor: Optional[WorkbenchConductor] = None
_broadcast: Optional[Any] = None


class _SchedulerNotWired(Exception):
    """Internal: a scheduler block skipped because no service is wired."""


_watch_service: Optional[Any] = None
_steward_service: Optional[Any] = None


def get_scheduler_services() -> tuple[Optional[Any], Optional[Any]]:
    """Read the injected scheduler services (HS-167-02).

    Returns ``(watch_service, steward_service)``; either is None when
    set_scheduler_services has not wired it -- callers refuse honestly.
    """
    return _watch_service, _steward_service


def set_scheduler_services(watch_service: Any, steward_service: Any) -> None:
    """Inject the app-wired scheduler services (HS-164-04).

    The conductor must run the SAME fully-wired instances the app
    serves: a bare WatchService(db) has no snapshot fetcher and a bare
    ProjectStewardService has no collector/delta/effect services --
    scheduled work would fail in production while fake-injected unit
    tests stay green (the DoorService-db scar's sibling).
    """
    global _watch_service, _steward_service
    _watch_service = watch_service
    _steward_service = steward_service


def set_broadcast(fn: Any) -> None:
    """Wire the broadcast callback from the hub's WebSocket manager."""
    global _broadcast
    _broadcast = fn


def _emit_broadcast(event_type: str, data: dict) -> None:
    """Emit a workbench event through the hub's broadcast system.

    Never raises: a desk that cannot hear a run is a worse desk, not a
    broken run.
    """
    if _broadcast:
        try:
            _broadcast(event_type, data)
        except Exception as exc:
            log.debug(f"Broadcast emit failed: {exc}")


# Retained Workbench frame helpers (HS-132-03). Programs now announce the
# originating automation through desk_changed; no live runner calls these.


def emit_run_start(*, workbench_id: str, run_id: str, item_count: int) -> None:
    _emit_broadcast(
        "workbench.run_start",
        {"workbench_id": workbench_id, "run_id": run_id,
         "item_count": int(item_count), "at": _now_iso()},
    )


def emit_item_claimed(
    *, workbench_id: str, run_id: str, item_id: str, title: str,
    index: int, total: int,
) -> None:
    _emit_broadcast(
        "workbench.item_claimed",
        {"workbench_id": workbench_id, "run_id": run_id, "item_id": item_id,
         "title": title, "index": int(index), "total": int(total),
         "at": _now_iso()},
    )


def emit_item_done(
    *, workbench_id: str, run_id: str, item_id: str, title: str,
    index: int, total: int,
) -> None:
    _emit_broadcast(
        "workbench.item_done",
        {"workbench_id": workbench_id, "run_id": run_id, "item_id": item_id,
         "title": title, "index": int(index), "total": int(total),
         "at": _now_iso()},
    )


def emit_item_failed(
    *, workbench_id: str, run_id: str, item_id: str, title: str,
    index: int, total: int, error: str,
) -> None:
    _emit_broadcast(
        "workbench.item_failed",
        {"workbench_id": workbench_id, "run_id": run_id, "item_id": item_id,
         "title": title, "index": int(index), "total": int(total),
         "error": str(error), "at": _now_iso()},
    )


def emit_run_complete(
    *, workbench_id: str, run_id: str, disposition: str,
    attempted: int = 0, completed: int = 0, failed: int = 0,
    pending_count: int = 0,
) -> None:
    _emit_broadcast(
        "workbench.run_complete",
        {"workbench_id": workbench_id, "run_id": run_id,
         "disposition": str(disposition), "attempted": int(attempted),
         "completed": int(completed), "failed": int(failed),
         "pending_count": int(pending_count), "at": _now_iso()},
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _cron_is_due(cron_expr: str) -> bool:
    """Delegate to the shared cron module (HS-136-01 factoring)."""
    from .cron import cron_is_due
    return cron_is_due(cron_expr)


def _hydrate_item_grounding(
    db: Any, grounding_json: str, *, query: str = "", exclude_refs: Optional[list[str]] = None,
    project_update_refs: Optional[list[str]] = None,
) -> str:
    """Hydrate an item's grounding refs into text blocks.

    Uses the same hydration pipeline as the recipe chat endpoint — meeting
    transcripts and artifact content are resolved from the canonical store.
    Forwards meeting_ids, artifact_ids, AND refs (qualified refs like
    zone:dir_abc) through the shared hydration pipeline (HS-118-02).
    """
    try:
        grounding = json.loads(grounding_json) if grounding_json else {}
    except (json.JSONDecodeError, TypeError) as exc:
        raise ServiceError("grounding_invalid", "Source list not valid") from exc
    if grounding is None:
        grounding = {}
    if not isinstance(grounding, dict):
        raise ServiceError("grounding_invalid", "Source list not valid")

    sources = [grounding.get(key, []) for key in ("meeting_ids", "artifact_ids", "refs")]
    if any(not isinstance(values, list) or any(not isinstance(ref, str) or not ref.strip() for ref in values)
           for values in sources):
        raise ServiceError("grounding_invalid", "Source list not valid")
    meeting_ids, artifact_ids, refs = sources
    if project_update_refs is not None and refs:
        # A project ref is a broad container for ordinary callers.  Project
        # update automations replace it with the P2-eligible leaf refs before
        # the shared hydrator reads any source text.
        expanded: list[str] = []
        for ref in refs:
            if str(ref).split(":", 1)[0].casefold() == "project":
                expanded.extend(project_update_refs)
            else:
                expanded.append(ref)
        refs = list(dict.fromkeys(expanded))
        if not refs and not meeting_ids and not artifact_ids:
            # No eligible project material means no optional relevance pass:
            # the task still travels separately below, while global memory
            # must never refill a privacy-filtered project container.
            query = ""
    explicit = bool(meeting_ids or artifact_ids or refs)

    if not meeting_ids and not artifact_ids and not refs and not query.strip():
        return ""

    # An explicit attachment is required evidence, never optional enrichment.
    # Keep the existing cap, but refuse rather than silently changing the job.
    from .grounding import GROUNDING_MAX_REFS

    total = len(meeting_ids) + len(artifact_ids) + len(refs)
    if total > GROUNDING_MAX_REFS:
        raise ServiceError(
            "grounding_over_limit", f"Source limit exceeded · {total}/{GROUNDING_MAX_REFS}",
        )

    try:
        from .grounding import hydrate_grounding_blocks
        from .inference_memory_policy import memory_enabled
        blocks, _, _, unknown = hydrate_grounding_blocks(
            db,
            meeting_ids,
            artifact_ids,
            "full",
            qualified_refs=refs if refs else None,
            query=query,
            include_memory=memory_enabled("workbench.item"),
            exclude_refs=exclude_refs,
        )
    except Exception as exc:
        if explicit:
            raise ServiceError("grounding_source_unavailable", "Source unavailable · " + ", ".join(
                [*(f"meeting:{ref}" for ref in meeting_ids), *(f"artifact:{ref}" for ref in artifact_ids), *refs]
            )) from exc
        log.warning(f"Grounding hydration failed: {exc}")
        return ""
    if unknown and explicit:
        raise ServiceError("grounding_source_unavailable", "Source unavailable · " + ", ".join(unknown))
    if unknown:
        log.warning(f"Grounding recall: {len(unknown)} unavailable optional ref(s): {unknown}")
    return "[GROUNDING]\n" + "\n\n".join(blocks) if blocks else ""


from .workbench_templates import MORNING_PREP_ID as _MORNING_PREP_ID  # noqa: E402


class WorkbenchConductor:
    """Background scheduler: due workbenches every 60 seconds, the Programs
    engine every 30 seconds."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_check: dict[str, float] = {}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="workbench-conductor")
        self._thread.start()
        log.info("Workbench conductor started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        log.info("Workbench conductor stopped")

    def _loop(self) -> None:
        last = 0.0
        while not self._stop.is_set():
            # The scheduled runs every 60 s; the Programs engine every 30 s
            # (Programs design §6). ``HOLDSPEAK_PROGRAMS=off`` ticks nothing.
            if time.monotonic() - last >= 59:
                last = time.monotonic()
                try:
                    self._tick()
                except Exception as exc:
                    log.error(f"Conductor tick failed: {exc}", exc_info=True)
            self._tick_programs()
            self._stop.wait(30)

    def _tick_programs(self) -> None:
        """One Programs pass (``services/program_runner.tick``)."""
        try:
            from .services.program_runner import tick as program_tick

            program_tick()
        except Exception as exc:
            log.error(f"Programs tick failed: {exc}", exc_info=True)

    def _tick(self) -> None:
        """One pass (scheduled runs, watches, reactions, the steward drain).

        It writes with no request: ONE ``desk_changed`` frame when it changed
        a row, naming each workbench it ran (2026-10-05).
        """
        from .runtime.announce_scope import announce_writes

        with announce_writes("workbench", "tick") as name:
            self._tick_body(name)

    def _tick_body(self, name: Any = lambda _id: None) -> None:
        try:
            from .db import get_database
            db = get_database()
        except Exception:
            return

        # Betterment daily D9 (owner decision 3): once an engine with the
        # desk's tools exists, Morning prep is made On (once only).
        try:
            from .services.automation_runs import ensure_morning_prep

            if ensure_morning_prep(db):
                name(_MORNING_PREP_ID)
        except Exception as exc:
            log.warning(f"Conductor: Morning prep not made: {exc}")

        workbenches = db.workbenches.list()
        for wb in workbenches:
            if not wb.schedule_enabled or not wb.schedule:
                continue
            if not _cron_is_due(wb.schedule):
                continue
            # Prevent running the same workbench twice in the same minute
            now_minute = time.time() // 60
            last = self._last_check.get(wb.id, 0)
            if last == now_minute:
                continue
            self._last_check[wb.id] = now_minute

            log.info(f"Conductor: workbench '{wb.name}' is due, starting run")
            name(wb.id)
            try:
                from .services.workbench_service import WorkbenchService
                from .principals import Principal, PrincipalKind
                scheduler = Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor")
                loop = asyncio.new_event_loop()
                loop.run_until_complete(WorkbenchService(db).run_scheduled(
                    scheduler, wb.id, due_minute=int(now_minute),
                ))
                loop.close()
            except Exception as exc:
                log.error(f"Conductor: workbench '{wb.name}' run failed: {exc}", exc_info=True)

        # Watch fold 3 (2026-11-08): the legacy Watch refresh and the Reaction
        # projection left this tick. Every watch, an Automation's event start
        # included, is evaluated by the ONE watch scheduler, the heartbeat
        # sweep (WatchService.evaluate_due, see the HS-200-43 note below).

        # Negative-space automation has a separate failure boundary: a broken
        # connector or Reaction must never prevent the idle policy heartbeat.
        try:
            from .principals import Principal, PrincipalKind
            from .services.resourceful_service import ResourcefulService

            owner = Principal(PrincipalKind.OWNER, "local-automation-conductor")
            resourceful_outcomes = asyncio.run(ResourcefulService(db).tick(owner))
            for outcome in resourceful_outcomes:
                if outcome.get("status") in {"completed", "failed"}:
                    log.info("Resourceful conductor: %s", outcome)
        except Exception as exc:
            log.error("Resourceful conductor tick failed: %s", exc, exc_info=True)

        # HS-200-43 (R1): the watch scheduler block that used to live here was
        # DELETED.  There is exactly ONE scheduler for graduated watches now --
        # the heartbeat (`runtime/heartbeat.py` -> `HeartbeatService.run_sweep`
        # -> `WatchService.evaluate_due`).  This block ticked every 60s with no
        # quiet-hours check and no owns_database gate, and advanced
        # `next_evaluation_at` identically to the heartbeat's own call, so the
        # conductor always won the race and quiet hours never actually held
        # evaluation.  `set_scheduler_services` / `get_scheduler_services` stay:
        # they are still the seam the heartbeat, the steward block below, the
        # trigger route (`web/routes/steward.py`) and the MCP trigger tool read.
        #
        # HS-164-04: Steward scheduler -- drain pending steward run_once
        # effects.  Its own failure boundary (see the block above and the
        # others in this tick).
        try:
            from .principals import Principal, PrincipalKind

            if _steward_service is None:
                log.debug("Steward scheduler: no wired service; skipping")
                raise _SchedulerNotWired()
            owner = Principal(PrincipalKind.OWNER, "local-steward-conductor")
            steward_svc = _steward_service
            # PHILO-9-02 (the steward beat, section 4): an unattended run acts
            # as SCHEDULER under the owner's RECORDED policy -- never as a
            # manufactured OWNER. The cadence projections below stay reads.
            scheduler = Principal(PrincipalKind.SCHEDULER, "local-steward-conductor")
            run_outcomes = steward_svc.run_due(scheduler)
            for outcome in run_outcomes:
                if outcome.get("outcome") in {"failed", "error"}:
                    log.warning("Steward scheduler: %s", outcome)
                elif outcome.get("outcome") == "run_started":
                    log.info("Steward scheduler: %s", outcome)

            # HS-164-04: Cadence projections (attention only, never schedule).
            try:
                projections = steward_svc.project_cadence_projections(owner)
                for proj in projections:
                    if proj.get("error"):
                        log.warning("Steward projection: %s", proj)
            except Exception as proj_exc:
                log.warning("Steward projection failed: %s", proj_exc)
        except _SchedulerNotWired:
            pass
        except Exception as exc:
            log.error("Steward scheduler tick failed: %s", exc, exc_info=True)


def start_conductor() -> WorkbenchConductor:
    global _conductor
    if _conductor is None:
        _conductor = WorkbenchConductor()
    _conductor.start()
    return _conductor


def stop_conductor() -> None:
    global _conductor
    if _conductor:
        _conductor.stop()
        _conductor = None
