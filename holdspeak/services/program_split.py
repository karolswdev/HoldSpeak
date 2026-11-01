"""Step sizing at dispatch and the split by level (PG-LANG LANG8, 2026-10-31).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §5.4 (the
64k rule) and §15.8 (``WORKING_SHARE = 0.5``, approved). Before the runner
hands a step (``program_runner._dispatch``), its estimate (by rule, no model,
``program_sizing``) is read against its budget's working share. A step that
does not fit is not handed: it is held with the words "Too big for qwen ·
41k of 32k", one checkpoint says why in his words, and the rule
``program_rules.decide(level, "step_too_big")`` decides:

- **YOLO**: ONE planning call (``program.split@1``, on the ``agent.plan``
  assignment through the shaper's path) cuts it into 2 to 4 parts that
  together own what it owned; the parts take its place (Insert before, then
  the step is removed: the step after it waits for the last part), and one
  Decided for you line says "Split step 3 … into 3 parts: steps 3–5"
  (Overturn while every part is Planned or Ready).
- **Secure and Normal**: the same call; the split is a ``step_change``
  proposal on the step (the PG-REQ proposal path): **Apply** splits it,
  **Skip** runs it as it is (the estimate is written into the checkpoint).
- No planning engine, an answer that cannot be read twice, or a part that is
  still too big after a split: the engine has no rule (a core question,
  ``no_rule``): **Go on** runs it as it is, **Park** parks it.

A part keeps the step's agent, gates, budget and person; the last part keeps
the step's origin (its merge closes the desk item) and its own requirements;
every part gets the every-step requirements (``plan`` copies them).
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from . import program_sizing as sizing

log = get_logger("program_split")

CONTRACT = "program.split"
CONTRACT_REVISION = "1"
TEMPERATURE = 0.2
DEADLINE_SECONDS = 240
MAX_TOKENS = 8000
PARTS_MIN, PARTS_MAX = 2, 4
#: The core-question kind a step too big with no split raises (its Go on runs it as it is).
CORE_KIND = "too_big"
#: A split in flight, per step (the async runner asks the planner off the tick).
_ASKING: dict[str, threading.Thread] = {}

SPLIT_RULES = """RULES
- Cut the step into 2 to 4 parts, in the order they run: each part comes after the part before it.
- Together the parts own what the step owns, and nothing else. A part may own a file inside an owned folder.
  Each part owns at most 3 paths.
- One concern per part. Its brief is one to four sentences, under 400 words: what the change does and how
  the part is checked.
- Each part must fit in the size given below, with its brief and the files it owns.
- "say": one short line: the parts and why."""


def schema() -> dict[str, Any]:
    part = {"type": "object", "additionalProperties": False, "required": ["title", "brief", "owns"],
            "properties": {"title": {"type": "string", "maxLength": 120},
                           "brief": {"type": "string", "maxLength": 3000},
                           "owns": {"type": "array", "maxItems": 3, "items": {"type": "string", "maxLength": 300}}}}
    return {"type": "json_schema", "json_schema": {"name": "program_split", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["say", "parts"],
        "properties": {"say": {"type": "string", "maxLength": 300},
                       "parts": {"type": "array", "minItems": PARTS_MIN, "maxItems": PARTS_MAX, "items": part}}}}}


# ── the words ────────────────────────────────────────────────────────

def size_words(size: Mapping[str, Any]) -> str:
    """``41k of 32k`` (the one denominator, §5.4)."""
    return f"{sizing.k_words(int(size['tokens']))} of {sizing.k_words(int(size['share']))}"


def why_words(step: Mapping[str, Any], size: Mapping[str, Any]) -> str:
    """The checkpoint in his words."""
    return (f"Step {step['ordinal']} is too big for one agent run (about {sizing.k_words(int(size['tokens']))} tokens "
            f"against {sizing.k_words(int(size['share']))}, half of the {sizing.k_words(int(size['budget']))} budget)")


def _engine_word(size: Mapping[str, Any]) -> str:
    return str(size.get("engine") or "its engine")


# ── the planning call ────────────────────────────────────────────────

def _inside(path: str, owned: list[str]) -> bool:
    clean = path.strip().strip("/")
    return any(clean == own.strip().strip("/") or clean.startswith(own.strip().rstrip("/") + "/") for own in owned)


def read_parts(output: str, step: Mapping[str, Any]) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """The engine's answer as ``{say, parts}``, or the reason it cannot be used."""
    from ..intel.parsing import _extract_json

    try:
        data = _extract_json(str(output or "").strip())
    except Exception:
        data = None
    if not isinstance(data, Mapping):
        return None, "The answer is not JSON with 'parts'."
    raw = data.get("parts")
    if not isinstance(raw, list) or not PARTS_MIN <= len(raw) <= PARTS_MAX:
        return None, f"Give {PARTS_MIN} to {PARTS_MAX} parts."
    owned = [str(path) for path in step.get("owns") or [] if str(path).strip()]
    parts: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            return None, f"Part {index} is not an object."
        title = " ".join(str(item.get("title") or "").split())[:120]
        brief = str(item.get("brief") or "").strip()
        owns = [str(path).strip() for path in item.get("owns") or [] if str(path).strip()]
        if not title or not brief:
            return None, f"Part {index} needs a title and a brief."
        if len(owns) > 3:
            return None, f"Part {index} owns more than 3 paths."
        outside = [path for path in owns if owned and not _inside(path, owned)]
        if outside:
            return None, f"Part {index} owns {outside[0]}, which the step does not own."
        parts.append({"title": title, "brief": brief, "owns": owns})
    left = [own for own in owned if not any(_inside(path, [own]) for part in parts for path in part["owns"])]
    if left:
        return None, f"No part owns {left[0]}: together the parts own what the step owns."
    return {"say": " ".join(str(data.get("say") or "").split())[:300], "parts": parts}, None


def messages(program: Mapping[str, Any], step: Mapping[str, Any], size: Mapping[str, Any],
             error: Optional[str] = None) -> tuple[str, str]:
    """The system and user prompt of ``program.split@1``."""
    system = "\n\n".join([
        "You split one step of a HoldSpeak Program into smaller steps that a small model can build. "
        'You answer JSON only: {"say": "...", "parts": [{"title": "...", "brief": "...", "owns": ["..."]}]}.',
        SPLIT_RULES,
        f"SIZE\nThe agent that builds each part ({_engine_word(size)}) has a context of "
        f"{sizing.k_words(int(size['budget']))} tokens; a part must fit in {sizing.k_words(int(size['share']))} "
        "tokens with its brief and the files it owns.",
    ])
    root = str(program.get("repo_root") or "") or None
    owns = [f"- {path}  ({sizing.k_words(sizing.chars_tokens(sizing.path_bytes(root, path)))})"
            for path in step.get("owns") or []]
    parts = [
        f"THE PROGRAM\n{program.get('title') or ''}\n{str(program.get('goal_markdown') or '').strip()}".rstrip(),
        f"THE STEP (too big: about {size_words(size)} tokens)\nstep {step['ordinal']} {step['title']}\nbrief\n"
        + "\n".join(f"> {line}" for line in str(step.get("brief_markdown") or step["title"]).splitlines() if line.strip()),
        "IT OWNS (size in tokens)\n" + ("\n".join(owns) if owns else "- nothing"),
    ]
    if error:
        parts.append("YOUR LAST ANSWER COULD NOT BE USED. The reason:\n" + error + "\nAnswer again, correct.")
    return system, "\n\n".join(parts)


def ask(service: Any, principal: Any, program: Mapping[str, Any], step: Mapping[str, Any], size: Mapping[str, Any],
        *, invoke_fn: Optional[Callable[[dict[str, Any]], tuple[Optional[str], str]]] = None,
        ) -> tuple[Optional[list[dict[str, Any]]], str, Optional[str]]:
    """ONE planning call with one retry: ``(parts or None, engine, reason)``."""
    from . import program_shaper as shaper

    try:
        capability, revision, _profile, label = shaper.resolve_engine(service.db)
    except Exception as exc:
        return None, "", str(getattr(exc, "detail", "") or "No engine is set for planning.")
    call = invoke_fn or (lambda payload: shaper.invoke(service.db, principal, capability, revision, payload,
                                                       contract=CONTRACT, contract_revision=CONTRACT_REVISION,
                                                       deadline=DEADLINE_SECONDS))
    error: Optional[str] = None
    model = ""
    for _attempt in (1, 2):
        system, user = messages(program, step, size, error)
        payload = {"system_prompt": system, "user_prompt": user, "temperature": TEMPERATURE,
                   "max_tokens": MAX_TOKENS, "response_format": schema()}
        try:
            output, model = call(payload)
        except Exception as exc:
            log.warning(f"program split call failed: {exc}")
            output = None
        if output is None:
            return None, model or label, f"{model or label or 'The engine'} did not answer"
        answer, error = read_parts(output, step)
        if answer is not None:
            return answer["parts"], model or label, None
    return None, model or label, f"its answer could not be used ({error})"


# ── the dispatcher's check ───────────────────────────────────────────

def step_size(service: Any, program: Mapping[str, Any], step: Mapping[str, Any], profile: Optional[str],
              engine: Optional[str]) -> Optional[dict[str, Any]]:
    from .program_sizing import step_estimate

    try:
        return step_estimate(service, program, step, profile=profile, engine_id=engine,
                             requirements=service.requirements(program["id"]))
    except Exception as exc:  # a size never fails the dispatch
        log.warning(f"program step size not read: {exc}")
        return None


def dispatch_hold(runner: Any, program: dict[str, Any], step: dict[str, Any], profile: str,
                  engine: Optional[str]) -> bool:
    """True when the step is too big to hand now (``step_too_big``)."""
    from .program_rules import decide

    facts = step.get("facts") or {}
    if facts.get("run_anyway") or CORE_KIND in set(facts.get("core_cleared") or []):
        return False
    size = step_size(runner.service, program, step, profile, engine)
    if not size or size.get("fits") is not False:
        return False
    runner._hold(step, str(size["words"]))
    split = facts.get("split") if isinstance(facts.get("split"), Mapping) else {}
    if split.get("state") in ("asking", "proposed") or runner._core_hold(step):
        return True
    service = runner.service
    facts = dict(step.get("facts") or {})
    facts["too_big"] = {key: size.get(key) for key in ("tokens", "budget", "share", "engine", "words")}
    step["facts"] = facts
    service.save_step(step)
    service._checkpoint(program, step, "engine", why_words(step, size))
    if facts.get("split_from"):
        # A part of a split that is still too big is not cut again.
        runner.raise_core(program, step, CORE_KIND, f"step {step['ordinal']} is still too big after a split "
                                                    f"(about {size_words(size)} tokens) and the engine has no rule for it")
        return True
    outcome = decide(program.get("control"), "step_too_big", {})
    _mark(service, step, "asking")
    if getattr(runner, "_async", False):
        thread = threading.Thread(target=_ask_and_act, args=(runner, program["id"], step["id"], size, outcome),
                                  daemon=True, name=f"program-split-{step['id']}")
        _ASKING[step["id"]] = thread
        thread.start()
    else:
        _ask_and_act(runner, program["id"], step["id"], size, outcome)
    return True


def _mark(service: Any, step: dict[str, Any], state: str, **more: Any) -> None:
    facts = dict(step.get("facts") or {})
    facts["split"] = {"state": state, "at": service._clock(), **more}
    step["facts"] = facts
    service.save_step(step)


def _ask_and_act(runner: Any, program_id: str, step_id: str, size: Mapping[str, Any], outcome: Any) -> None:
    from .program_runner import _program_lock

    service = runner.service
    try:
        program = service.store.get_program(program_id)
        step = service.store.get_step(step_id)
        if program is None or step is None:
            return
        started = time.monotonic()
        parts, engine, reason = ask(service, runner.principal, program, step, size)
        seconds = round(time.monotonic() - started, 1)
        lock = _program_lock(program_id) if getattr(runner, "_async", False) else None
        if lock is not None:
            lock.acquire()
        try:
            program = service.store.get_program(program_id)
            step = service.store.get_step(step_id)
            if program is None or step is None or step["state"] not in ("planned", "ready"):
                return
            if parts is None:
                _mark(service, step, "failed", reason=reason)
                runner.raise_core(program, step, CORE_KIND,
                                  f"step {step['ordinal']} is too big for one agent run (about {size_words(size)} "
                                  f"tokens) and the planner could not split it: {reason}")
                return
            if outcome.to_owner:
                propose(service, program, step, size, parts, engine=engine, seconds=seconds)
            else:
                made = apply_split(service, program, step, parts, by="engine")
                first, last = made[0]["ordinal"], made[-1]["ordinal"]
                line = (f"Split step {step['ordinal']} (too big for {_engine_word(size)} · {size_words(size)}) into "
                        f"{len(made)} parts: steps {first} to {last}")
                service.engine_decision(program, None, "step_too_big", outcome, line[:400], undo={"split": {
                    "parts": [row["id"] for row in made], "step": _snapshot(step), "size": dict(size),
                    "proposed": parts}})
            service._touch(program)
            service.changed(program_id, None, verb="split")
        finally:
            if lock is not None:
                lock.release()
    except Exception as exc:
        log.error(f"program split of {step_id} failed: {exc}", exc_info=True)
    finally:
        _ASKING.pop(step_id, None)
    if getattr(runner, "_async", False):
        runner.tick_program(program_id)


# ── the proposal, the split, run as it is, overturn ─────────────────

def proposal_title(step: Mapping[str, Any], size: Mapping[str, Any], parts: list[Mapping[str, Any]]) -> str:
    return (f"Split step {step['ordinal']} (too big for {_engine_word(size)} · {size_words(size)}) into {len(parts)} "
            f"parts: " + " · ".join(str(part["title"]) for part in parts) + ". Skip runs it as it is.")


def propose(service: Any, program: Mapping[str, Any], step: dict[str, Any], size: Mapping[str, Any],
            parts: list[dict[str, Any]], *, engine: str = "", seconds: Optional[float] = None) -> int:
    """Secure and Normal: the split is his (a ``step_change`` proposal)."""
    title = proposal_title(step, size, parts)
    _mark(service, step, "proposed", engine=engine or None, seconds=seconds)
    return service.store.add_checkpoint(
        step_id=step["id"], program_id=program["id"], at=service._clock(), by="engine", line=title[:400],
        kind="step_change", undo={"title": title[:400], "fields": {"split": {"parts": parts, "size": dict(size)}}})


def _snapshot(step: Mapping[str, Any]) -> dict[str, Any]:
    keys = ("title", "brief_markdown", "owns", "profile", "engine", "prefer_idle", "may_call", "effort",
            "gate_check", "gate_review", "review_depth", "gate_merge", "origin_ref", "for_person_id", "budget_tokens")
    return {key: step.get(key) for key in keys} | {"ordinal": step.get("ordinal"), "id": step.get("id")}


def _part_row(step: Mapping[str, Any], part: Mapping[str, Any], *, last: bool) -> dict[str, Any]:
    return {
        "title": part["title"], "brief": part["brief"], "owns": list(part.get("owns") or []),
        "profile": step.get("profile"), "engine": step.get("engine") if step.get("profile") else None,
        "prefer_idle": bool(step.get("prefer_idle")), "may_call": bool(step.get("may_call")),
        "effort": "low" if step.get("effort") == "low" else "medium", "gate_check": bool(step.get("gate_check", True)),
        "gate_review": step.get("gate_review") or "none", "review_depth": step.get("review_depth"),
        "gate_merge": step.get("gate_merge") or "level", "for_person_id": step.get("for_person_id"),
        "budget_tokens": step.get("budget_tokens"), "origin_ref": step.get("origin_ref") if last else None,
    }


def apply_split(service: Any, program: Mapping[str, Any], step: dict[str, Any], parts: list[Mapping[str, Any]], *,
                by: str) -> list[dict[str, Any]]:
    """The parts take the step's place; the step is removed (§5.4)."""
    from .program_service import _LOCK, FROZEN_SET, ProgramRefused

    if step["state"] not in ("planned", "ready"):
        raise ProgramRefused("step_frozen", f"Step {step['ordinal']} started. It is not split.", field="position",
                             reason=FROZEN_SET)
    from ..kernel.program_ops import RUNNER

    with _LOCK:
        before = {row["id"] for row in service.store.list_steps(program["id"])}
        rows = [_part_row(step, part, last=index == len(parts) - 1) for index, part in enumerate(parts)]
        service.plan(RUNNER, program["id"], steps=rows, before=step["id"], waits=True, by=by)
        made = sorted((row for row in service.store.list_steps(program["id"]) if row["id"] not in before),
                      key=lambda row: int(row["ordinal"]))
        # Each part comes after the part before it.
        for prev, part in zip(made, made[1:]):
            part["after"] = sorted(set(int(value) for value in part.get("after") or []) | {int(prev["ordinal"])})
        for part in made:
            facts = dict(part.get("facts") or {})
            facts["split_from"] = {"step_id": step["id"], "ordinal": step["ordinal"], "title": step["title"]}
            part["facts"] = facts
            service.save_step(part)
        # The step's own requirements go to the last part.
        for row in service.requirements(program["id"]):
            if row.get("step_id") == step["id"] and not row.get("parent_id"):
                row["step_id"] = made[-1]["id"]
                service.store.save_requirement(row)
        # The step after it waits for the last part (the parts chain from what it came after).
        target = service.store.get_step(step["id"]) or step
        target["after"] = [int(made[-1]["ordinal"])]
        service.save_step(target)
        service._remove(program, target, by="engine")
        if by != "engine":
            service._checkpoint(program, None, by, f"Split step {step['ordinal']} into {len(made)} parts")
    return [service.store.get_step(row["id"]) or row for row in made]


def run_as_it_is(service: Any, program: Mapping[str, Any], step: dict[str, Any], *, by: str) -> None:
    """Skip on the split: the step is handed as it is; the estimate goes in the checkpoint."""
    facts = dict(step.get("facts") or {})
    facts["run_anyway"] = True
    if isinstance(facts.get("split"), Mapping):
        facts["split"] = {**facts["split"], "state": "declined"}
    size = facts.get("too_big") or {}
    step["facts"] = facts
    step["held_reason"] = None
    service.save_step(step)
    words = f" (about {size_words(size)} tokens)" if size.get("tokens") and size.get("share") else ""
    service._checkpoint(program, step, by, f"Runs as it is: step {step['ordinal']}{words}")


def overturn_split(service: Any, program: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    """Undo YOLO's split while every part is Planned or Ready: the step is
    back in the parts' place, and the split is his (a proposal)."""
    from ..kernel.program_ops import RUNNER
    from .program_service import ProgramRefused

    undo = dict((row.get("undo") or {}).get("split") or {})
    parts = [service.store.get_step(str(ident)) for ident in undo.get("parts") or []]
    parts = [part for part in parts if part is not None]
    if not parts or any(part["state"] not in ("planned", "ready") for part in parts):
        raise ProgramRefused("not_overturnable", "A part of the split started; the split stays.")
    old = dict(undo.get("step") or {})
    raw = {"title": old.get("title") or "Step", "brief": old.get("brief_markdown") or "", "owns": old.get("owns") or [],
           "profile": old.get("profile"), "engine": old.get("engine") if old.get("profile") else None,
           "prefer_idle": bool(old.get("prefer_idle")), "may_call": bool(old.get("may_call")),
           "effort": old.get("effort") or "medium", "gate_check": bool(old.get("gate_check", True)),
           "gate_review": old.get("gate_review") or "none", "review_depth": old.get("review_depth"),
           "gate_merge": old.get("gate_merge") or "level", "for_person_id": old.get("for_person_id"),
           "budget_tokens": old.get("budget_tokens"), "origin_ref": old.get("origin_ref")}
    parts.sort(key=lambda part: int(part["ordinal"]))
    before = {step["id"] for step in service.store.list_steps(program["id"])}
    service.plan(RUNNER, program["id"], steps=[raw], before=parts[0]["id"], waits=True, by="owner")
    back = next(step for step in service.store.list_steps(program["id"]) if step["id"] not in before)
    for req in service.requirements(program["id"]):
        if req.get("step_id") == parts[-1]["id"] and not req.get("parent_id"):
            req["step_id"] = back["id"]
            service.store.save_requirement(req)
    for part in reversed(parts):
        service._remove(program, service.store.get_step(part["id"]) or part, by="engine")
    back = service.store.get_step(back["id"]) or back
    size = dict(undo.get("size") or {})
    facts = dict(back.get("facts") or {})
    facts["too_big"] = {key: size.get(key) for key in ("tokens", "budget", "share", "engine", "words")}
    back["facts"] = facts
    service.save_step(back)
    proposed = [dict(part) for part in undo.get("proposed") or []]
    if len(proposed) >= PARTS_MIN:
        propose(service, program, back, size, proposed)


__all__ = ["CONTRACT", "CORE_KIND", "PARTS_MAX", "PARTS_MIN", "apply_split", "ask", "dispatch_hold", "messages",
           "overturn_split", "propose", "proposal_title", "read_parts", "run_as_it_is", "schema", "size_words",
           "why_words"]
