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


def set_broadcast(fn: Any) -> None:
    """Wire the broadcast callback from the hub's WebSocket manager."""
    global _broadcast
    _broadcast = fn


def _emit(event_type: str, data: dict) -> None:
    """Emit a workbench event through the hub's broadcast system."""
    if _broadcast:
        try:
            _broadcast(event_type, data)
        except Exception as exc:
            log.debug(f"Broadcast emit failed: {exc}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _cron_is_due(cron_expr: str) -> bool:
    """Simple cron check: minute hour dom month dow.

    Weekday mapping: cron uses 0=Sunday, 1=Monday, ..., 6=Saturday.
    Python's weekday() uses 0=Monday, ..., 6=Sunday.
    We convert Python's weekday to cron convention before matching.
    """
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return False
        now = datetime.now()
        # Convert Python weekday (0=Mon) to cron weekday (0=Sun)
        cron_dow = (now.weekday() + 1) % 7
        fields = [
            (parts[0], now.minute),
            (parts[1], now.hour),
            (parts[2], now.day),
            (parts[3], now.month),
            (parts[4], cron_dow),
        ]
        for pattern, value in fields:
            if pattern == "*":
                continue
            if pattern.startswith("*/"):
                step = int(pattern[2:])
                if step <= 0 or value % step != 0:
                    return False
                continue
            allowed = set()
            for part in pattern.split(","):
                if "-" in part:
                    lo, hi = part.split("-", 1)
                    allowed.update(range(int(lo), int(hi) + 1))
                else:
                    allowed.add(int(part))
            if value not in allowed:
                return False
        return True
    except (ValueError, IndexError):
        return False


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


async def run_workbench(workbench_id: str) -> dict:
    """Execute one workbench run: process all pending items, produce a receipt.

    Each run is a FRESH session — no chat history from previous runs.
    The prompt stack:
      constitutional context (injected by engine.run_prompt)
      → recipe system prompt + skills
      → recipe standing context (manual_context + KB)
      → item grounding (hydrated meetings/artifacts)
      → item body (the task itself)
    """
    from .db import get_database
    from .inference_targets import resolve_inference_target, build_intel_for_target
    from .intel.models import MeetingIntelError

    db = get_database()
    wb = db.workbenches.get(workbench_id)
    if not wb:
        return {"error": f"workbench {workbench_id} not found"}

    # Wake gate: skip if no pending items
    items = db.workbench_items.list_for_workbench(workbench_id, status="pending")
    if not items:
        log.info(f"Workbench {wb.name}: no pending items, skipping")
        return {"skipped": True, "reason": "no pending items"}

    # Resolve the recipe
    recipe = db.recipes.get(wb.recipe_id) if wb.recipe_id else None
    if not recipe:
        return {"error": f"workbench {wb.name}: no recipe assigned"}

    # Resolve and CHECK the target
    target = resolve_inference_target(db, wb.profile_id or "this_machine")
    if not target.ready:
        reason = getattr(target, "readiness_reason", "") or "target unavailable"
        log.warning(f"Workbench {wb.name}: target not ready — {reason}")
        return {"error": f"target not ready: {reason}"}

    # Start the run receipt
    run_id = _new_id("wbrun")
    db.workbench_runs.create(run_id=run_id, workbench_id=workbench_id)

    # Build the intel engine
    try:
        intel = build_intel_for_target(target, db)
    except Exception as exc:
        log.error(f"Workbench {wb.name}: failed to build intel: {exc}")
        db.workbench_runs.complete(run_id, status="failed",
                                   egress_boundary=getattr(target, "boundary", ""))
        return {"error": str(exc)}

    # Get constitutional context receipt for stamping
    ctx_receipt = constitutional_receipt()

    # Assemble the system prompt: recipe prompt + skills
    system_prompt = inject_skills(
        db, recipe.system_prompt or f"You are {recipe.name}, a helpful assistant.", recipe.id,
    )

    # Assemble the recipe's standing context (manual_context + KB)
    recipe_context = _assemble_recipe_context(db, recipe)

    # Record which skills were injected
    skills_used: list[str] = []
    try:
        skill_records = db.skills.list_for_recipe(recipe.id, active_only=True)
        skills_used = [s.id for s in skill_records]
        if skills_used:
            log.info(f"Workbench {wb.name}: {len(skills_used)} skills injected")
    except Exception:
        pass

    # Recall agent memory
    from .workbench_memory import recall_for_prompt, append_memory
    memory_block = recall_for_prompt(workbench_id)
    if memory_block:
        log.info(f"Workbench {wb.name}: {memory_block.count(chr(10))} memory entries recalled")

    # Emit run start
    _emit("workbench.run_start", {
        "workbench_id": workbench_id,
        "run_id": run_id,
        "item_count": len(items),
    })

    # Process items in priority order
    attempted = 0
    completed = 0
    failed = 0
    mint_failures = 0

    for item in items:
        attempted += 1
        now = _now_iso()

        # Claim the item
        db.workbench_items.upsert(
            item_id=item.id, workbench_id=workbench_id,
            title=item.title, body=item.body, priority=item.priority,
            status="claimed", claimed_at=now,
        )
        _emit("workbench.item_claimed", {
            "workbench_id": workbench_id,
            "item_id": item.id,
            "title": item.title,
            "index": attempted,
            "total": len(items),
        })

        # Build the user prompt with real grounding
        user_parts: list[str] = []

        # Recipe standing context
        if recipe_context:
            user_parts.append(recipe_context)

        # Agent memory — recalled observations from prior runs
        if memory_block:
            user_parts.append(memory_block)

        # Item grounding — hydrated from the canonical store
        item_grounding = _hydrate_item_grounding(db, item.grounding_json)
        if item_grounding:
            user_parts.append(item_grounding)

        # The item itself
        user_parts.append(f"[TASK]\n{item.title}")
        if item.body:
            user_parts.append(item.body)

        user_prompt = "\n\n".join(user_parts)

        try:
            output = await asyncio.to_thread(
                intel.run_prompt,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            done_now = _now_iso()
            db.workbench_items.upsert(
                item_id=item.id, workbench_id=workbench_id,
                title=item.title, body=item.body, priority=item.priority,
                status="done", result=output,
                result_egress={"boundary": target.boundary, "model": target.model},
                completed_at=done_now, claimed_at=now,
            )
            completed += 1
            log.info(f"Workbench {wb.name}: item '{item.title}' done")

            # ── Auto-mint: kernel-admitted artifact minting (HS-118-06) ──
            mint_artifact_id = _auto_mint_artifact(
                db=db,
                item=item,
                recipe=recipe,
                workbench=wb,
                run_id=run_id,
                target=target,
                output=output,
            )
            if mint_artifact_id:
                _emit("workbench.item_minted", {
                    "workbench_id": workbench_id,
                    "item_id": item.id,
                    "artifact_id": mint_artifact_id,
                    "artifact_title": f"{recipe.name or recipe.id}: {item.title}",
                })
            else:
                # Issue 8: record mint failure count
                mint_failures += 1
                # Mark mint_attempted so the UI shows Retry instead of Keep
                _mark_mint_attempted(db, item.id)

            # Terminal writeback — ask the agent what to remember
            try:
                wb_prompt = (
                    "Based on the task and your output, what ONE thing should future "
                    "runs on this workbench remember? Reply with a single sentence. "
                    "If nothing is worth remembering, reply exactly 'nothing'."
                )
                writeback = await asyncio.to_thread(
                    intel.run_prompt,
                    system_prompt="You are a concise assistant. Reply in one sentence only.",
                    user_prompt=f"Task: {item.title}\n\nYour output:\n{(output or '')[:500]}\n\n{wb_prompt}",
                )
                writeback_text = (writeback or "").strip()
                if writeback_text.lower() not in ("nothing", "nothing.", ""):
                    append_memory(
                        workbench_id, run_id, "observation", writeback_text,
                        item_title=item.title,
                        provenance={"egress": target.boundary, "model": target.model},
                    )
            except Exception as wb_exc:
                log.debug(f"Writeback failed for '{item.title}': {wb_exc}")

            _emit("workbench.item_done", {
                "workbench_id": workbench_id,
                "item_id": item.id,
                "title": item.title,
                "result_preview": (output or "")[:200],
            })
        except (MeetingIntelError, Exception) as exc:
            log.warning(f"Workbench {wb.name}: item '{item.title}' failed: {exc}")
            db.workbench_items.upsert(
                item_id=item.id, workbench_id=workbench_id,
                title=item.title, body=item.body, priority=item.priority,
                status="failed", result=f"Error: {exc}",
                result_egress={"boundary": target.boundary, "error": str(exc)},
                completed_at=_now_iso(), claimed_at=now,
            )
            failed += 1
            _emit("workbench.item_failed", {
                "workbench_id": workbench_id,
                "item_id": item.id,
                "title": item.title,
                "error": str(exc),
            })

    # Complete the run receipt (Issue 8: includes mint_failures)
    run_record = db.workbench_runs.complete(
        run_id,
        items_attempted=attempted,
        items_completed=completed,
        items_failed=failed,
        mint_failures=mint_failures,
        total_tokens=0,  # honest: we can't track tokens through run_prompt yet
        egress_boundary=target.boundary,
        model=target.model,
        constitutional_context_revision=ctx_receipt["revision"],
        constitutional_context_hash=ctx_receipt["content_hash"],
        skills_injected=skills_used,
        status="completed" if failed == 0 else "failed",
    )

    log.info(
        f"Workbench {wb.name}: run complete — "
        f"{completed}/{attempted} items done, {failed} failed, "
        f"egress={target.boundary}, model={target.model}"
    )
    _emit("workbench.run_complete", {
        "workbench_id": workbench_id,
        "run_id": run_id,
        "completed": completed,
        "failed": failed,
        "attempted": attempted,
        "model": target.model,
        "egress_boundary": target.boundary,
        "workbench_name": wb.name,
    })
    return run_record.to_dict() if run_record else {"completed": True}


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
                loop = asyncio.new_event_loop()
                loop.run_until_complete(run_workbench(wb.id))
                loop.close()
            except Exception as exc:
                log.error(f"Conductor: workbench '{wb.name}' run failed: {exc}", exc_info=True)


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
