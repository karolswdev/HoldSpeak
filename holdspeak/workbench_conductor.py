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
from .skill_injection import inject_skills

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
    """
    try:
        grounding = json.loads(grounding_json) if grounding_json else {}
    except (json.JSONDecodeError, TypeError):
        return ""
    if not grounding or not isinstance(grounding, dict):
        return ""

    meeting_ids = grounding.get("meeting_ids", [])
    artifact_ids = grounding.get("artifact_ids", [])
    if not meeting_ids and not artifact_ids:
        return ""

    try:
        from .grounding import hydrate_grounding_blocks
        blocks, _, _, _ = hydrate_grounding_blocks(
            db,
            [str(x) for x in meeting_ids if x],
            [str(x) for x in artifact_ids if x],
            str(grounding.get("expand", "summary")),
        )
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
            from .web.routes.primitives.ask import _context_material
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
    from .web.routes.primitives._shared import _new_id
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
        recipe.system_prompt or f"You are {recipe.name}, a helpful assistant.",
        recipe.id,
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

    # Complete the run receipt
    run_record = db.workbench_runs.complete(
        run_id,
        items_attempted=attempted,
        items_completed=completed,
        items_failed=failed,
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
