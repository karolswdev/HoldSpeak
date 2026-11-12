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


from ..kernel.prompt_adapter import CanonicalPromptAdapter  # noqa: E402


class _MeteredPromptAdapter(CanonicalPromptAdapter):
    """The canonical adapter, plus the tokens the provider said it used.

    The sealed result shape stays {output, provider, model}. The count travels
    on this adapter instance, which the runner keeps for its one child."""

    def __init__(self, spend_limit_usd: float | None = None, work_folder: str | None = None, *,
                 desk_tools: bool = True, project_id: str = "", scope_items: tuple[str, ...] = ()) -> None:
        self.tokens = 0
        #: Betterment A4: the automation's Spend limit per run; it overrides
        #: the engine's own limit on an agent CLI that enforces one.
        self.spend_limit_usd = spend_limit_usd
        #: Betterment M2 follow-up (orchestrator ruling): the memory call
        #: after an item runs WITHOUT the desk's tools on an agent CLI.
        self.desk_tools = desk_tools
        #: Project scope for an update automation's run credential.
        self.project_id = str(project_id or "").strip()
        #: The refs delegated to an agent CLI run's credential (Codex on #2140).
        self.scope_items = tuple(scope_items)
        #: Betterment A10: the folder an agent CLI works in, read only (the
        #: automation's Folder source). An HTTP engine has no folder: ignored.
        self.work_folder = work_folder

    def _limited(self, engine: Any) -> Any:
        preset = getattr(engine, "preset", None)
        limit = (self.spend_limit_usd is not None and hasattr(engine, "spend_limit_usd")
                 and getattr(preset, "enforces_spend_limit", False))
        no_tools = not self.desk_tools and getattr(engine, "desk_tools", False)
        folder = bool(self.work_folder) and hasattr(engine, "work_folder")
        project_scope = bool(self.project_id) and hasattr(engine, "project_id")
        delegated = bool(self.scope_items) and hasattr(engine, "scope_items")
        if not limit and not no_tools and not folder and not project_scope and not delegated:
            return engine
        # A copy for this one call: the routed engine may be shared.
        import copy

        limited = copy.copy(engine)
        if limit:
            limited.spend_limit_usd = self.spend_limit_usd
        if no_tools:
            limited.desk_tools = False
        if folder:
            limited.work_folder = self.work_folder
        if project_scope:
            limited.project_id = self.project_id
        if delegated:
            limited.scope_items = self.scope_items
        return limited

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> dict[str, str]:
        engine = self._limited(engine)
        from .run_trace import for_item

        # Betterment M2: an agent CLI run records the item it ran for, so the
        # result shows the run's cost and what its agent used.
        with for_item(str(payload.get("item_id") or "")):
            if self.desk_tools:
                # MCP M5: an HTTP engine whose server takes tool calls runs
                # the item through the hub's tool loop, with the desk's tools.
                from .engine_tool_loop import answer_item

                looped = answer_item(engine, payload, cancellation)
                if looped is not None:
                    result, tokens = looped
                    self.tokens += tokens
                    return result
            result = super().dispatch(engine, payload, cancellation)
        try:
            usage = dict(getattr(engine, "last_usage", None) or {})
            self.tokens += int(usage.get("total_tokens") or 0)
        except (TypeError, ValueError):
            pass  # an engine without a provider count reports none, never a guess
        return result


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
    from .automation_runs import PROJECT_UPDATES_PREFIX, checked_work_folder
    from .errors import ServiceError

    service = runner.service
    deliver = str(step.get("deliver") or DEFAULT_DELIVER)
    if step["state"] == "planned":
        # A caller that waits runs it before any tick promoted it (the engine may be off).
        service.transition(program, step, "ready")
    if step["state"] == "ready":
        service.transition(program, step, "briefed", line="Asked the engine")
    if step["state"] == "briefed":
        service.transition(program, step, "working")
    started_by = _automation_of(service.db, program)
    try:
        folder = (checked_work_folder(service, started_by, project_id=program.get("project_id"),
                                      sources=list(step.get("sources") or [])) if started_by is not None else None)
    except ServiceError as exc:
        step["facts"] = {**(step.get("facts") or {}), "prompt": {"error": exc.detail, "outcome": exc.code}}
        service.transition(program, step, "failed", line=exc.detail)
        return
    try:
        system, user, refs, excluded = brief_of(service.db, step, runner.principal)
    except Exception as exc:  # a source that cannot be read fails the step before any call
        service.transition(program, step, "failed", line=f"The sources were not read · {exc}"[:400])
        return
    project_id = deliver[len(PROJECT_UPDATES_PREFIX):] if deliver.startswith(PROJECT_UPDATES_PREFIX) else ""
    # Betterment A10: an automation's agent CLI engine works in its Folder source, read only.
    from .github_provider import delegated_repo_ref

    lessons_of = started_by if not project_id else None
    if lessons_of is not None:
        # An automation's lessons from its earlier runs ride before the task.
        from ..workbench_memory import recall_for_prompt

        recalled = recall_for_prompt(str(lessons_of.id))
        if recalled:
            user = f"{recalled}\n\n{user}"
    # An event start delegates its repository to the run (Codex on #2140).
    repository = str(((step.get("facts") or {}).get("run_context") or {}).get("repository") or "")
    adapter = _MeteredPromptAdapter(program.get("spend_limit_usd"), folder, project_id=project_id,
                                    scope_items=(delegated_repo_ref(repository),) if repository else ())
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
        # The engine's own words are the result's reason (the automation's Results show them).
        facts["prompt"] = {"operation_id": exc.operation_id, "outcome": exc.outcome or exc.code,
                           "error": exc.error or exc.detail}
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
    if lessons_of is not None:
        _keep_lesson(door, runner.principal, answer.engine, lessons_of, program, step, text)
    _finished_notice(service.db, program)


LESSON_QUESTION = ("Based on the task and your output, what ONE thing should future runs on this workbench "
                   "remember? Reply with a single sentence. If nothing is worth remembering, reply exactly 'nothing'.")


def _keep_lesson(door: Any, principal: Any, engine: Any, wb: Any, program: Mapping[str, Any],
                 step: Mapping[str, Any], text: str) -> None:
    """An automation's run keeps one lesson for its next runs (the
    automation's Lessons): one short call on the same engine, with no desk
    tools. A failed call or "nothing" keeps none; it never fails the run."""
    from . import engine_door
    from ..workbench_memory import append_memory
    
    title = str(program.get("title") or step.get("title") or "")
    payload = {"system_prompt": "You are a concise assistant. Reply in one sentence only.",
               "user_prompt": f"Task: {title}\n\nYour output:\n{text[:500]}\n\n{LESSON_QUESTION}",
               "item_id": step["id"]}
    try:
        # The automation's Spend limit per run holds for this call too.
        answer = engine_door.run(door, principal, JOB, payload, engine=engine,
                                 adapter=_MeteredPromptAdapter(program.get("spend_limit_usd"), desk_tools=False),
                                 result_ref=f"program-step-lesson:{step['id']}")
    except Exception as exc:
        log.info(f"prompt step {step['id']}: no lesson kept: {exc}")
        return
    lesson = answer.output.strip()
    if lesson and lesson.strip(" .'\"").lower() != "nothing":
        append_memory(str(wb.id), str(program["id"]), "observation", lesson, item_title=title,
                      provenance={"operation_id": answer.operation_id, "receipt_id": answer.operation_id})


def _automation_of(db: Any, program: Mapping[str, Any]) -> Any:
    """The automation that started this Program (its origin), or None."""
    from .automation_runs import PROGRAM_ORIGIN_PREFIX

    origin = str(program.get("origin_ref") or "")
    if not origin.startswith((PROGRAM_ORIGIN_PREFIX, "automation:")):
        return None
    return db.workbenches.get(origin.split(":", 1)[1], include_deleted=True)


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
