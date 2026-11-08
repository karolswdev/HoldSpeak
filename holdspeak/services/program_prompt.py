"""The prompt step (2026-11-08): one model call on the assigned engine.

A Program step of kind ``prompt`` runs no agent, needs no repository and no
worktree. Its brief is the step's text plus its sources (expanded into an
``[ABOUT]`` block and the source text, the way an automation's run reads
them); the engine door (``engine_door.run``) runs it once on the engine the
owner assigned to the job, with the assignment chain's one retry. The answer
is the step's report; the door's receipt is on the step (``facts.prompt``);
the answer goes where the step's ``deliver`` says (``automation_runs.
deliver_text``: a project update, an Inbox note, a Needs you item, a
prepared send, or Today).

The step moves ready -> briefed -> working -> done in one hand (or failed
with the door's words). The runner hands it on its tick like any step;
:func:`run_now` runs a Program's ready prompt steps at once, for a caller
that waits on the answer.
"""
from __future__ import annotations

import json
import threading
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_prompt")

#: The step kind.
PROMPT = "prompt"
#: The job the call runs as: the owner's assignment for automation work.
JOB = "workbench.item"
#: Where an answer goes when the step names nowhere.
DEFAULT_DELIVER = "inbox"
#: The engine's answer is cut to this many characters on the step.
REPORT_LIMIT = 20000

#: The prompt steps whose call runs now (one hand per step at a time).
_RUNNING: set[str] = set()
_RUNNING_GUARD = threading.Lock()


def is_prompt(step: Mapping[str, Any]) -> bool:
    return str(step.get("kind") or "") == PROMPT


def all_prompt(steps: Any) -> bool:
    """Every step given is a prompt step (and there is at least one)."""
    rows = [row for row in steps or [] if isinstance(row, Mapping)]
    return bool(rows) and all(str(row.get("kind") or "") == PROMPT for row in rows)


def running(step_id: str) -> bool:
    with _RUNNING_GUARD:
        return step_id in _RUNNING


def brief_of(db: Any, step: Mapping[str, Any], principal: Any = None) -> tuple[str, str, list[str], list[str]]:
    """``(system, user, refs, excluded)``: the call's prompt, the source refs
    it read, and (a project update) the refs a tool-capable engine must not
    read. A project update reads its P2-eligible refs, the records draft and
    the standing pages (``automation_runs.project_update_material``)."""
    from ..workbench_conductor import _hydrate_item_grounding
    from .automation_runs import PLAIN_SYSTEM_PROMPT, PROJECT_UPDATES_PREFIX, expand_sources, project_update_material

    body = str(step.get("brief_markdown") or "").strip()
    refs, about = expand_sources(db, [str(ref) for ref in step.get("sources") or []])
    if about:
        body = f"{body}\n\n[ABOUT]\n" + "\n".join(about)
    deliver = str(step.get("deliver") or "")
    eligible: Optional[list[str]] = None
    material, excluded = "", []
    if deliver.startswith(PROJECT_UPDATES_PREFIX):
        eligible, material, excluded = project_update_material(db, principal, deliver[len(PROJECT_UPDATES_PREFIX):])
    grounding = ""
    if refs:
        grounding = _hydrate_item_grounding(
            db, json.dumps({"refs": refs}), query=f"{step.get('title') or ''}\n{body}",
            project_update_refs=eligible)
    parts = [part for part in (grounding, material, f"[TASK]\n{step.get('title') or ''}", body) if part]
    return PLAIN_SYSTEM_PROMPT, "\n\n".join(parts), refs, excluded


def _default_broker() -> Any:
    from ..kernel.runtime import _service

    return _service()


def claim(step_id: str) -> bool:
    """Take the step's one hand. ``False`` when its call runs already."""
    with _RUNNING_GUARD:
        if step_id in _RUNNING:
            return False
        _RUNNING.add(step_id)
        return True


def release(step_id: str) -> None:
    with _RUNNING_GUARD:
        _RUNNING.discard(step_id)


def run_claimed(runner: Any, program: Mapping[str, Any], step: dict[str, Any], *,
                broker: Optional[Callable[[], Any]] = None) -> None:
    """Run one claimed prompt step to its end, then give the hand back."""
    try:
        _run(runner, program, step, broker or _default_broker)
    finally:
        release(step["id"])


def hand(runner: Any, program: Mapping[str, Any], step: dict[str, Any], *,
         broker: Optional[Callable[[], Any]] = None) -> bool:
    """Run one prompt step to its end, in this thread. ``False`` when it runs already."""
    if not claim(step["id"]):
        return False
    run_claimed(runner, program, step, broker=broker)
    return True


def _run(runner: Any, program: Mapping[str, Any], step: dict[str, Any], broker: Callable[[], Any]) -> None:
    from . import engine_door
    from .automation_runs import PROJECT_UPDATES_PREFIX
    from .workbench_runner import _MeteredPromptAdapter

    service = runner.service
    deliver = str(step.get("deliver") or DEFAULT_DELIVER)
    if step["state"] == "ready":
        service.transition(program, step, "briefed", line="Asked the engine")
    if step["state"] == "briefed":
        service.transition(program, step, "working")
    try:
        system, user, refs, excluded = brief_of(service.db, step, runner.principal)
    except Exception as exc:  # a source that cannot be read fails the step before any call
        service.transition(program, step, "failed", line=f"The sources were not read · {exc}"[:400])
        return
    project_id = deliver[len(PROJECT_UPDATES_PREFIX):] if deliver.startswith(PROJECT_UPDATES_PREFIX) else ""
    adapter = _MeteredPromptAdapter(program.get("spend_limit_usd"), project_id=project_id)
    payload = {
        "system_prompt": system, "user_prompt": user,
        # The run's cost and what its agent used are keyed by the step (run_trace).
        "item_id": step["id"],
        # A project update lets a tool-capable engine read the project and
        # save its text through the CONDUCTOR set, as an automation did.
        "tool_palette": "CONDUCTOR" if project_id else "ASK",
        "output_target": deliver,
        "project_update_excluded_refs": excluded if project_id else None,
    }
    try:
        door = broker()
        wb = _automation_of(service.db, program)
        # An automation's run is on the engine its With line names.
        engine = engine_door.engine_for(door, JOB, subject=("workbench", str(wb.id)) if wb is not None else None)
        answer = engine_door.run(door, runner.principal, JOB, payload, engine=engine, adapter=adapter,
                                 result_ref=f"program-step:{step['id']}")
    except engine_door.EngineDoorError as exc:
        facts = dict(step.get("facts") or {})
        facts["prompt"] = {"operation_id": exc.operation_id, "outcome": exc.outcome or exc.code}
        step["facts"] = facts
        service.transition(program, step, "failed", line=f"The engine gave no answer · {exc.detail}"[:400])
        return
    except Exception as exc:
        log.error(f"prompt step {step['id']}: the call failed: {exc}", exc_info=True)
        service.transition(program, step, "failed", line=f"The engine gave no answer · {exc}"[:400])
        return
    text = answer.output.strip()[:REPORT_LIMIT]
    facts = dict(step.get("facts") or {})
    facts["prompt"] = {
        "operation_id": answer.operation_id, "model": answer.model, "engine": answer.engine.revision,
        "assignment": answer.engine.assignment, "egress": engine_door.egress_of(door, answer.engine),
        "tokens": int(adapter.tokens or 0), "refs": refs,
    }
    step["report"] = text
    step["facts"] = facts
    service.save_step(step)
    delivered = _deliver(service, program, step, deliver, text, refs)
    facts = dict(step.get("facts") or {})
    facts["delivered"] = delivered
    step["facts"] = facts
    line = f"Answered on {answer.model or 'the engine'} · {_delivered_words(delivered)}"
    service.transition(program, step, "done", line=line[:400])
    _finished_notice(service.db, program)


def _automation_of(db: Any, program: Mapping[str, Any]) -> Any:
    """The automation that started this Program (its origin), or None."""
    from .automation_runs import PROGRAM_ORIGIN_PREFIX

    origin = str(program.get("origin_ref") or "")
    if not origin.startswith(PROGRAM_ORIGIN_PREFIX):
        return None
    return db.workbenches.get(origin[len(PROGRAM_ORIGIN_PREFIX):], include_deleted=True)


def _finished_notice(db: Any, program: Mapping[str, Any]) -> None:
    """An automation's run made a new result: one quiet notice
    (``HeartbeatService.finished_notice``). A failed notice is a log line."""
    wb = _automation_of(db, program)
    if wb is None or getattr(wb, "deleted", False):
        return
    try:
        from .heartbeat_service import HeartbeatService

        HeartbeatService(db).finished_notice(str(wb.id), str(wb.name or "Automation"), 1)
    except Exception as exc:
        log.warning(f"program {program['id']}: finished notice failed: {exc}")


def _deliver(service: Any, program: Mapping[str, Any], step: Mapping[str, Any], deliver: str, text: str,
             refs: list[str]) -> dict[str, Any]:
    from ..kernel.program_ops import RUNNER
    from .automation_runs import deliver_text

    try:
        return deliver_text(
            service.db, RUNNER, deliver, key=f"program_step:{step['id']}",
            title=str(program.get("title") or step.get("title") or "Result"), body=text,
            refs=refs or [str(ref) for ref in step.get("sources") or []],
            generator=f"agent:program:{program['id']}",
            origin_words=_origin_words(service.db, program),
            used_item_id=str(step["id"]),
        )
    except Exception as exc:  # the answer stays on the step; the delivery is named failed
        log.warning(f"prompt step {step['id']}: delivery to {deliver} failed: {exc}")
        return {"target": deliver, "outcome": "failed", "error": str(exc)[:400]}


def _origin_words(db: Any, program: Mapping[str, Any]) -> str:
    wb = _automation_of(db, program)
    if wb is not None:
        return f"From the automation [{wb.name or 'Automation'}](/?open=workbench:{wb.id})."
    return f"From the program [{program.get('title') or 'Program'}](/?open=program:{program['id']})."


def _delivered_words(delivered: Mapping[str, Any]) -> str:
    target = str(delivered.get("target") or "")
    outcome = str(delivered.get("outcome") or "")
    if outcome == "failed":
        return f"not delivered: {delivered.get('error') or 'the delivery failed'}"
    if target.startswith("project_updates:"):
        return "wrote the project update"
    if target.startswith("destination:"):
        return "prepared the send" if outcome == "prepared" else "the send was prepared already"
    return {"inbox": "filed in the Inbox", "needs_you": "added to Needs you", "today": "shown on Today"}.get(
        target, outcome or "kept")


def run_now(runner: Any, program_id: str) -> list[str]:
    """Run the Program's ready prompt steps now, in this thread (a caller
    that waits on the answer). The ids of the steps it ran."""
    ran: list[str] = []
    service = runner.service
    for _ in range(8):  # a later step becomes ready when the one before it is done
        program = service.store.get_program(program_id)
        if program is None or program.get("state") not in ("running", "waiting", "failed"):
            break
        runner._promote(program)
        ready = [step for step in service.store.list_steps(program_id)
                 if step["state"] == "ready" and is_prompt(step) and step["id"] not in ran]
        if not ready:
            break
        for step in ready:
            if hand(runner, program, step, broker=getattr(runner, "_broker", None)):
                ran.append(step["id"])
        service.changed(program_id, verb="step")
    return ran
