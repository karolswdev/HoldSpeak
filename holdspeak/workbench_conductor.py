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

from .constitutional_context import constitutional_receipt
from .logging_config import get_logger
from .services.support import _new_id, inject_skills

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


# ── the five live workbench frames (HS-132-03) ───────────────────────────
#
# WorkbenchWindow and the desk sprite have subscribed to these since
# HS-116-07; nothing ever sent them. WorkbenchRunner calls the helpers below
# at the real transitions, so a running workbench updates without a reload.
# Every payload carries workbench_id — that is how a window decides the
# frame is about itself.


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


def _hydrate_item_grounding(db: Any, grounding_json: str) -> str:
    """Hydrate an item's grounding refs into text blocks.

    Uses the same hydration pipeline as the recipe chat endpoint — meeting
    transcripts and artifact content are resolved from the canonical store.
    Forwards meeting_ids, artifact_ids, AND refs (qualified refs like
    zone:dir_abc) through the shared hydration pipeline (HS-118-02).
    """
    try:
        grounding = json.loads(grounding_json) if grounding_json else {}
    except (json.JSONDecodeError, TypeError):
        return ""
    if not grounding or not isinstance(grounding, dict):
        return ""

    meeting_ids = [str(x) for x in grounding.get("meeting_ids", []) if x]
    artifact_ids = [str(x) for x in grounding.get("artifact_ids", []) if x]
    refs = [str(x) for x in grounding.get("refs", []) if x]

    if not meeting_ids and not artifact_ids and not refs:
        return ""

    # HS-118-02: cap enforcement. Total refs capped at GROUNDING_MAX_REFS (16).
    # Drop order: refs last-added-first, then artifact_ids last-added-first,
    # preserving meeting_ids in their original order.
    from .grounding import GROUNDING_MAX_REFS

    total = len(meeting_ids) + len(artifact_ids) + len(refs)
    if total > GROUNDING_MAX_REFS:
        dropped: list[str] = []
        excess = total - GROUNDING_MAX_REFS

        # Drop from refs (last-added-first = pop from end)
        while excess > 0 and refs:
            dropped.append(refs.pop())
            excess -= 1

        # Drop from artifact_ids (last-added-first = pop from end)
        while excess > 0 and artifact_ids:
            dropped.append(artifact_ids.pop())
            excess -= 1

        log.warning(
            f"Grounding cap exceeded: {total} refs > {GROUNDING_MAX_REFS}, "
            f"dropped {len(dropped)} ref(s): {dropped}"
        )

    try:
        from .grounding import hydrate_grounding_blocks
        blocks, _, _, unknown = hydrate_grounding_blocks(
            db,
            meeting_ids,
            artifact_ids,
            "full",
            qualified_refs=refs if refs else None,
        )
        if unknown:
            log.warning(f"Grounding hydration: {len(unknown)} unknown ref(s) skipped: {unknown}")
        if blocks:
            return "[GROUNDING]\n" + "\n\n".join(blocks)
    except Exception as exc:
        log.warning(f"Grounding hydration failed: {exc}")
    return ""


def _assemble_recipe_context(db: Any, recipe: Any) -> str:
    """Assemble the recipe's standing context: manual_context + KB hydration.

    Mirrors the recipe chat endpoint's context assembly (recipes.py lines 344-351).
    """
    parts: list[str] = []
    if (getattr(recipe, "manual_context", None) or "").strip():
        parts.append(recipe.manual_context)
    kb_id = getattr(recipe, "kb_id", None)
    if kb_id:
        kb = db.kbs.get(kb_id)
        if kb:
            from .services.support import _context_material
            texts: list[str] = []
            for mid in list(getattr(kb, "member_ids", None) or [])[:12]:
                bare = mid.split(":", 1)[1] if ":" in mid else mid
                for kind in ("note", "artifact", "meeting"):
                    _, text = _context_material(db, bare, kind, "")
                    if text:
                        texts.append(text[:1200])
                        break
            if texts:
                parts.append(f"[KB: {kb.name or kb_id}]\n" + "\n\n".join(texts))
    if parts:
        return "[CONTEXT]\n" + "\n\n".join(parts)
    return ""


def _auto_mint_artifact(
    *,
    db: Any,
    item: Any,
    recipe: Any,
    workbench: Any,
    run_id: str,
    target: Any,
    output: str,
) -> Optional[str]:
    """Auto-mint a pending-review artifact for a completed workbench item.

    Idempotent: checks result_artifact_id first (app-level), backed by a DB
    unique constraint on (source_run_id, source_item_id). On a concurrent
    race (IntegrityError), the existing artifact is looked up and linked.

    Returns the artifact ID on success, None on failure (item stays done
    with result but no link).

    Fix notes (HS-118-06 review):
    - Issue 1: uses context-bound kernel API (runtime.submit / _as_principal),
      NOT the private _service(). workbench_mint is a registered operation type.
      Returns None (mint failure) if the kernel refuses.
    - Issue 2: artifact creation and item linking happen in one transaction
      via _persist_and_link_mint_artifact().
    - Issue 3: on IntegrityError from the unique constraint, queries for the
      existing artifact by (source_run_id, source_item_id) and links to it.
    """
    import sqlite3

    # App-level idempotency: already minted?
    existing = db.workbench_items.get(item.id)
    if existing and existing.result_artifact_id:
        log.debug(f"Item '{item.title}' already minted: {existing.result_artifact_id}")
        return existing.result_artifact_id

    try:
        from .web.routes.primitives._shared import _new_id

        # ── Kernel admission (Article XI) ─────────────────────────────
        # Use the context-bound public API, not the private _service().
        # The conductor sets the owner principal via _as_principal().
        operation_id = ""
        try:
            from .kernel.runtime import submit as kernel_submit, receipt as kernel_receipt, _as_principal
            from .principals import Principal, PrincipalKind

            principal = Principal(PrincipalKind.OWNER, "conductor")
            request_id = _new_id("request")
            with _as_principal(principal):
                handle = kernel_submit(
                    {
                        "request_schema": 1,
                        "request_id": request_id,
                        "idempotency_key": f"mint:{run_id}:{item.id}",
                        "operation": {"name": "workbench_mint", "version": 1},
                        "target": {},
                        "arguments": {
                            "recipe_id": recipe.id,
                            "run_id": run_id,
                            "item_id": item.id,
                            "workbench_id": workbench.id,
                        },
                    },
                )
            if handle.get("state") == "refused":
                reason = handle.get("receipt", {}).get("outcome", "unknown")
                log.warning(f"Kernel refused mint for '{item.title}': {reason}")
                # Issue 1 fix: do NOT proceed if kernel refuses
                return None
            operation_id = handle.get("operation_id", "")
        except Exception as kernel_exc:
            log.warning(f"Kernel admission failed for mint of '{item.title}': {kernel_exc}")
            return None

        # ── Build provenance envelope ─────────────────────────────────
        grounding_refs = {}
        try:
            grounding_refs = json.loads(item.grounding_json) if item.grounding_json else {}
        except (json.JSONDecodeError, TypeError):
            pass

        structured_json = {
            "egress": {"boundary": target.boundary, "model": target.model},
            "grounding_refs": grounding_refs,
            "workbench_id": workbench.id,
            "run_id": run_id,
        }

        title = f"{recipe.name or recipe.id}: {item.title}"
        sources = [
            {"source_type": "workbench_item", "source_ref": item.id},
            {"source_type": "recipe", "source_ref": recipe.id},
        ]

        # ── Atomic persist + link (Issue 2 fix) ──────────────────────
        artifact_id = _new_id("artifact")
        try:
            _persist_and_link_mint_artifact(
                db=db,
                artifact_id=artifact_id,
                item=item,
                workbench=workbench,
                run_id=run_id,
                output=output,
                title=title,
                sources=sources,
                structured_json=structured_json,
                target=target,
            )
        except sqlite3.IntegrityError:
            # Issue 3 fix: concurrent race lost the unique-index race.
            # Look up the winning artifact by (source_run_id, source_item_id)
            # and link to it instead of returning failure.
            log.info(f"Concurrent mint race for item '{item.title}', recovering existing artifact")
            artifact_id = _recover_existing_artifact(db, run_id, item)
            if not artifact_id:
                log.warning(f"IntegrityError but no artifact found for item '{item.title}'")
                if operation_id:
                    try:
                        with _as_principal(principal):
                            kernel_receipt(operation_id, "failed", f"item:{item.id}")
                    except Exception:
                        pass
                return None

        # Terminal receipt on the kernel operation
        if operation_id:
            try:
                with _as_principal(principal):
                    kernel_receipt(operation_id, "succeeded", f"artifact:{artifact_id}")
            except Exception as receipt_exc:
                log.debug(f"Kernel receipt failed for mint: {receipt_exc}")

        log.info(f"Minted artifact {artifact_id} for item '{item.title}'")
        return artifact_id

    except Exception as exc:
        log.warning(f"Auto-mint failed for item '{item.title}': {exc}")
        return None


def _persist_and_link_mint_artifact(
    *,
    db: Any,
    artifact_id: str,
    item: Any,
    workbench: Any,
    run_id: str,
    output: str,
    title: str,
    sources: list[dict[str, str]],
    structured_json: dict[str, Any],
    target: Any,
) -> None:
    """Persist the artifact and link it to the item in ONE transaction.

    Issue 2 fix: uses the db's raw connection so both the artifact INSERT
    and the item UPDATE happen atomically. On failure, both roll back.
    """
    from datetime import datetime as _dt
    now_iso = _dt.now().isoformat()
    body = str(output or "")
    sj_str = json.dumps(structured_json or {})

    with db._connection() as conn:
        # Insert artifact
        conn.execute(
            """
            INSERT INTO artifacts (
                id, meeting_id, origin, artifact_type, title, body_markdown,
                structured_json, confidence, status, plugin_id, plugin_version,
                source_run_id, source_item_id, created_at, updated_at
            )
            VALUES (?, NULL, 'run', 'workbench_output', ?, ?, ?, 0.0,
                    'pending-review', 'workbench_run', '1', ?, ?, ?, ?)
            """,
            (artifact_id, title, body, sj_str, run_id, item.id, now_iso, now_iso),
        )
        # Insert artifact sources
        for source in sources:
            conn.execute(
                """
                INSERT INTO artifact_sources (artifact_id, source_type, source_ref, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (artifact_id, source["source_type"], source["source_ref"], now_iso),
            )
        # Link artifact to item + mark mint_attempted
        result_egress_json = json.dumps({"boundary": target.boundary, "model": target.model})
        conn.execute(
            """
            UPDATE workbench_items
            SET result_artifact_id = ?, mint_attempted = 1, last_modified = ?
            WHERE id = ?
            """,
            (artifact_id, now_iso, item.id),
        )


def _recover_existing_artifact(db: Any, run_id: str, item: Any) -> Optional[str]:
    """On IntegrityError, find the winning artifact by (source_run_id, source_item_id)."""
    with db._connection() as conn:
        row = conn.execute(
            "SELECT id FROM artifacts WHERE source_run_id = ? AND source_item_id = ?",
            (run_id, item.id),
        ).fetchone()
    if row:
        existing_id = row["id"]
        # Link the item to the existing artifact
        from datetime import datetime as _dt
        now_iso = _dt.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                """
                UPDATE workbench_items
                SET result_artifact_id = ?, mint_attempted = 1, last_modified = ?
                WHERE id = ?
                """,
                (existing_id, now_iso, item.id),
            )
        return existing_id
    return None


def _mark_mint_attempted(db: Any, item_id: str) -> None:
    """Mark an item as mint_attempted even when minting failed (Issue 4)."""
    from datetime import datetime as _dt
    now_iso = _dt.now().isoformat()
    try:
        with db._connection() as conn:
            conn.execute(
                "UPDATE workbench_items SET mint_attempted = 1, last_modified = ? WHERE id = ?",
                (now_iso, item_id),
            )
    except Exception as exc:
        log.debug(f"Failed to mark mint_attempted for {item_id}: {exc}")


async def run_workbench(workbench_id: str, principal: Any | None = None, *, memory_enabled: bool = True) -> dict:
    """Compatibility seam for authenticated manual Workbench execution."""
    if principal is None:
        from .services.errors import ServiceError
        raise ServiceError("scheduler_principal_required", "An explicit principal is required", context={"status": 403})
    from .kernel.runtime import _service
    from .services.workbench_runner import WorkbenchRunner
    from .db import get_database
    return await WorkbenchRunner(get_database(), _service()).run(
        principal, workbench_id, memory_enabled=memory_enabled
    )


class WorkbenchConductor:
    """Background scheduler that checks for due workbenches every 60 seconds."""

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
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as exc:
                log.error(f"Conductor tick failed: {exc}", exc_info=True)
            self._stop.wait(60)

    def _tick(self) -> None:
        try:
            from .db import get_database
            db = get_database()
        except Exception:
            return

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
            try:
                from .kernel.runtime import _service
                from .services.workbench_runner import WorkbenchRunner
                from .principals import Principal, PrincipalKind
                loop = asyncio.new_event_loop()
                loop.run_until_complete(WorkbenchRunner(db, _service()).run_scheduled(
                    Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor"), wb.id,
                    due_minute=int(now_minute),
                ))
                loop.close()
            except Exception as exc:
                log.error(f"Conductor: workbench '{wb.name}' run failed: {exc}", exc_info=True)

        # Connector Watches and intrinsic events share this heartbeat, while
        # their durable attempt/projection state stays in SQLite.
        try:
            from .db import get_observer
            from .principals import Principal, PrincipalKind
            from .services.reaction_service import ReactionService

            owner = Principal(PrincipalKind.OWNER, "local-automation-conductor")
            reactions = ReactionService(db, observer=get_observer())
            watch_outcomes = asyncio.run(reactions.refresh_due_watches(owner))
            for outcome in watch_outcomes:
                if outcome.get("status") in {"refreshed", "failed"}:
                    log.info("Watch conductor: %s", outcome)
            projection_outcomes = asyncio.run(reactions.process_pending(owner, limit=500))
            for outcome in projection_outcomes:
                if outcome.get("status") == "projection_failed":
                    log.warning("Reaction conductor: %s", outcome)
        except Exception as exc:
            log.error("Reaction conductor tick failed: %s", exc, exc_info=True)

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

        # HS-164-04: Watch scheduler -- evaluate graduated watches that are
        # due.  Independent failure boundary: a broken evaluate_due must never
        # stop run_due or the other conductor duties.
        try:
            from .principals import Principal, PrincipalKind

            if _watch_service is None:
                log.debug("Watch scheduler: no wired service; skipping")
                raise _SchedulerNotWired()
            owner = Principal(PrincipalKind.OWNER, "local-watch-conductor")
            eval_outcomes = _watch_service.evaluate_due(owner)
            for outcome in eval_outcomes:
                if outcome.get("outcome") in {"failed", "skipped_circuit_open"}:
                    log.warning("Watch scheduler: %s", outcome)
                elif outcome.get("outcome") in {"evaluated", "refreshed"}:
                    log.info("Watch scheduler: %s", outcome)
        except _SchedulerNotWired:
            pass
        except Exception as exc:
            log.error("Watch scheduler tick failed: %s", exc, exc_info=True)

        # HS-164-04: Steward scheduler -- drain pending steward run_once
        # effects.  SEPARATE failure boundary from Watch scheduler above.
        try:
            from .principals import Principal, PrincipalKind

            if _steward_service is None:
                log.debug("Steward scheduler: no wired service; skipping")
                raise _SchedulerNotWired()
            owner = Principal(PrincipalKind.OWNER, "local-steward-conductor")
            steward_svc = _steward_service
            run_outcomes = steward_svc.run_due(owner)
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
