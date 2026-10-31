"""Shaping a Program by a typed sentence (PG-LANG LANG3, 2026-10-31).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §4. One
sentence of his and the Program's current text go to ONE inference call on
the desk's ``agent.plan`` assignment (when no route resolves there, the Ask
engine's ``ask.answer``: the design's other choice, §15.3). The engine
answers the WHOLE changed text; the hub diffs it against the current text
with the LANG1 machinery (``program_text.diff_program_text`` and the
service's own checks), so a shaped change is the same change rows a typed
edit gets. The model never applies anything.

- A text the parser cannot read gets one retry with the parse error quoted;
  then an honest refusal ("The engine's answer could not be read").
- The guard (§4.5): a row that lowers the bar is marked (LANG1's
  ``lowers_bar``); a row that is a core question (a file outside the
  repository, a new phone egress) is marked the same way with its core
  reason; a ``waived`` line from the model is refused ("Only you waive").
  None of these is ever applied by YOLO; each needs his own press.
- No engine, an engine that fails, an engine past the deadline: a refusal
  that names the engine. Nothing is guessed.
- At YOLO with ``apply`` (§4.6, §15.2), the allowed rows apply at once
  through ``text_apply``; the ledger gets one Decided for you row "Shaped by
  a sentence: …" with Overturn while every step it touched is still Planned
  or Ready. Below YOLO nothing applies here: the rows wait for Apply.

Grounding (§4.3, bounded so the call fits a small engine): the text with
its lamps stripped, the repository map cut to the folders the steps own
(and the Program's ``within`` when it has one; at most 200 paths), the
origin Note's lines, the Project's open actions (30 at most), the last 10
checkpoints and the vocabulary (agents, templates, requirement kinds, the
people the Program names).
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_shaper")

CAPABILITY = "agent.plan"
#: §15.3: "the other choice: shaping on the Ask engine". Used only when
#: ``agent.plan`` resolves to no engine on this desk.
FALLBACK_CAPABILITY = "ask.answer"
CONTRACT = "program.shape"
CONTRACT_REVISION = "1"
#: §4.3: temperature 0.2. The deadline is 60 s, not the design's 30 s: the
#: home engine (qwen3.8-27b) reasons before it answers, and one recorded
#: shaping took 25 s (2.4k tokens, most of them thinking). The whole text
#: comes back (not block edits), so the token cap is the text's size plus
#: room to think.
TEMPERATURE = 0.2
DEADLINE_SECONDS = 60
MIN_TOKENS, MAX_TOKENS, THINKING_TOKENS = 3000, 8000, 3500
SENTENCE_MAX = 1000
REPO_PATHS_MAX = 200
NOTE_CHARS_MAX = 8000
ACTIONS_MAX = 30
CHECKPOINTS_MAX = 10
YOLO_RULE = "YOLO applies a shaped change"

#: The grammar card the system prompt carries (§3.2, condensed).
GRAMMAR_CARD = """THE PROGRAM TEXT (version 1)
One statement per line. Two spaces of indent put a line under the last header
(program, every step, at the end, step N, round). Four spaces put a line under a requirement.
Two or more spaces then '#' to the end of a line is a lamp (state only); never write lamps.
'> ' starts a line of the owner's words (a goal or a brief); keep them byte for byte.
'+ ' under a started step is a line added to its brief (an amendment).
' · ' joins short statements on one line (agent Codex · effort high).

program <title>
  goal
  > <his words>
  in <repo> · <branch> · project <name>
  control secure | normal | yolo
  check <command> | none
  agent <AGENTS>                 the default Runs on list
  reviewer <AGENT> [at glance | delta | standard]
  when idle | may call | may hand off
  allow <AGENT>, <AGENT>
  spend up to $<number>
  for <person>
  template <template>
every step | at the end
  R<n> <kind>[ optional]: <sentence>      kinds: check, review, shot, word
    run <command> | expect <pattern> | shot <case> at 393 | 1440
step <n> <title>                 an existing step keeps its number
step + <title>                   a new step; its place in the text is its place in the plan
  owns <path>, <path>
  after <n>, <n>
  agent <AGENTS> · effort low | medium | high
  race 2 | 3
  check off
  review none | agent | <person> [at glance | delta | standard] · merge level | owner | none
  for <person>
  brief
  > <the brief>
  R+ <kind>: <sentence>          a new requirement
AGENTS = AGENT {, then AGENT}; AGENT = Claude Code | Codex | pi [on <engine>] | the desk's agent
Defaults are not written: leave out a line that says the default."""

RULES = """RULES
- Change only what the sentence asks. Every other line stays exactly as it is.
- Answer the WHOLE program text, with the change made, in "text".
- Never touch a frozen field (the list below). Never remove a step or a requirement.
- Never lower a gate, never write 'check off', never write 'waived'.
- Keep his words in '>' lines. Write a new step as 'step +' and a new requirement as 'R+'.
- "say": one short line in his words: what changes.
- When the sentence cannot be read (which step?), set "question" to ONE short question
  and give the text unchanged."""


@dataclass
class ShapeResult:
    """One shaping answer (the brief's ``ShapeResult``)."""

    proposed_text: str
    rows: list[Any]
    refusals: list[dict[str, Any]]
    grounded_on: dict[str, Any]
    latency_ms: int
    engine: str
    say: str = ""
    question: Optional[str] = None
    attempts: int = 1
    capability: str = CAPABILITY
    #: The printed text the rows are against (his base for Apply).
    base_text: str = ""
    prompts: list[dict[str, Any]] = field(default_factory=list, repr=False)


def _refused(code: str, detail: str, status: int = 409, **more: Any) -> Exception:
    from .program_service import ProgramRefused

    return ProgramRefused(code, detail, status=status, **more)


# ── the response format (contract program.shape@1) ───────────────────

def token_cap(text: str) -> int:
    return max(MIN_TOKENS, min(MAX_TOKENS, len(text) // 3 + THINKING_TOKENS))


def response_format() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "program_shape", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["say", "text", "question"],
        "properties": {
            "say": {"type": "string", "maxLength": 300},
            "text": {"type": "string"},
            "question": {"type": ["string", "null"], "maxLength": 300},
        }}}}


# ── grounding ────────────────────────────────────────────────────────

def stripped_text(printed: str) -> str:
    """The text with its lamps out (the run is never sent as definition)."""
    from .program_text import parse_program_text, render

    return render(parse_program_text(printed))


def frozen_list(wire: Mapping[str, Any]) -> list[dict[str, str]]:
    out = []
    for step in wire.get("steps") or []:
        for name, reason in sorted((step.get("frozen") or {}).items()):
            if reason:
                out.append({"where": f"step {step.get('ordinal')}", "field": str(name), "reason": str(reason)})
    return out


def _repo_map(root: Optional[str], folders: Iterable[str]) -> list[str]:
    if not root or not Path(root).is_dir():
        return []
    wanted = sorted({folder for folder in folders if folder is not None})
    if not wanted:
        return []
    try:
        proc = subprocess.run(["git", "-C", root, "ls-files", "--", *wanted], capture_output=True, text=True,
                              timeout=3)
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line][:REPO_PATHS_MAX]


def _folders(wire: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for path in [*(wire.get("within") or [])] + [p for step in wire.get("steps") or [] for p in step.get("owns") or []]:
        text = str(path or "").strip().strip("/")
        if not text or text.startswith("..") or Path(text).is_absolute():
            continue
        parent = str(Path(text).parent)
        out.append("." if parent in ("", ".") else parent)
    return out


def grounding(service: Any, wire: Mapping[str, Any]) -> dict[str, Any]:
    """The bounded grounding of §4.3 (each part may be empty)."""
    from ..program_templates import TEMPLATES
    from .program_text import AGENT_WORDS, KINDS

    root = str((wire.get("repository") or {}).get("root") or "") or None
    paths = _repo_map(root, _folders(wire))
    note_lines = ""
    origin = str(wire.get("origin_ref") or "")
    if origin.startswith("note:"):
        try:
            note = service.db.notes.get(origin.split(":", 1)[1])
            if note is not None and not getattr(note, "deleted", False):
                note_lines = str(note.body_markdown or "")[:NOTE_CHARS_MAX]
        except Exception:
            note_lines = ""
    actions: list[str] = []
    if wire.get("project_id"):
        try:
            items = service.db.projects.get_project_action_items(wire["project_id"])
            actions = [str(item.task)[:200] for item in items
                       if str(getattr(item, "status", "open") or "open") in ("open", "pending", "")][:ACTIONS_MAX]
        except Exception:
            actions = []
    checkpoints = [str(row.get("line") or "") for row in (wire.get("checkpoints") or []) if row.get("line")]
    people = sorted({str(name) for name in [wire.get("for_person")] + [s.get("for_person") for s in wire.get("steps") or []]
                     if name})
    vocabulary = {
        "agents": sorted(set(AGENT_WORDS.values()) | {"the desk's agent"}),
        "templates": [str(item["id"]).replace("-", " ") for item in TEMPLATES],
        "requirement_kinds": list(KINDS),
        "controls": ["secure", "normal", "yolo"],
        "people": people,
    }
    return {"repo_paths": paths, "note": note_lines, "open_actions": actions,
            "checkpoints": checkpoints[:CHECKPOINTS_MAX], "vocabulary": vocabulary}


def messages(sentence: str, text: str, frozen: list[dict[str, str]], ground: Mapping[str, Any],
             error: Optional[str] = None) -> tuple[str, str]:
    """The system and user prompt of ``program.shape@1``."""
    vocabulary = ground.get("vocabulary") or {}
    frozen_words = "\n".join(f"- {row['where']} · {row['field']}: {row['reason']}" for row in frozen) or "- none"
    system = "\n\n".join([
        "You change a HoldSpeak Program by one sentence of its owner. You answer JSON only: "
        '{"say": "...", "text": "...", "question": null}.',
        GRAMMAR_CARD, RULES, "FROZEN FIELDS\n" + frozen_words,
        "VOCABULARY\n" + "\n".join(f"- {key.replace('_', ' ')}: {', '.join(map(str, values)) or 'none'}"
                                   for key, values in vocabulary.items()),
    ])
    parts = ["THE PROGRAM TEXT NOW\n" + text.rstrip("\n")]
    if ground.get("repo_paths"):
        parts.append("FILES IN THE REPOSITORY (under the folders the steps own)\n" + "\n".join(ground["repo_paths"]))
    if ground.get("note"):
        parts.append("THE NOTE THE PROGRAM CAME FROM\n" + str(ground["note"]))
    if ground.get("open_actions"):
        parts.append("THE PROJECT'S OPEN ACTIONS\n" + "\n".join(f"- {item}" for item in ground["open_actions"]))
    if ground.get("checkpoints"):
        parts.append("THE LAST CHECKPOINTS\n" + "\n".join(f"- {item}" for item in ground["checkpoints"]))
    parts.append("THE SENTENCE\n" + sentence)
    if error:
        parts.append("YOUR LAST ANSWER COULD NOT BE READ. The parser said:\n" + error
                     + "\nAnswer again with the whole text, correct.")
    return system, "\n\n".join(parts)


# ── the engine call (the runner's one path, like Find the tasks) ─────

def _broker_for(db: Any) -> Any:
    """The kernel broker over the service's database (idempotent for the
    hub's own database: the live broker is reused)."""
    from ..kernel.runtime import _configure

    return _configure(db)


def _engine_label(db: Any, profile_id: str) -> str:
    if not profile_id:
        return ""
    try:
        with db._connection() as conn:
            row = conn.execute("SELECT label FROM model_profile_revisions WHERE profile_id=? ORDER BY revision DESC "
                               "LIMIT 1", (profile_id,)).fetchone()
        if row is not None and row["label"]:
            return str(row["label"])
    except Exception:
        pass
    return profile_id


def resolve_engine(db: Any) -> tuple[str, str, str, str]:
    """``(capability, revision, profile_id, label)``; refuses by name when
    neither ``agent.plan`` nor the Ask engine resolves."""
    from .project_update_service import _resolve_for_capability

    broker = _broker_for(db)
    for capability in (CAPABILITY, FALLBACK_CAPABILITY):
        try:
            revision, _assignment, profile = _resolve_for_capability(broker, capability)
        except RuntimeError:
            continue
        if revision:
            return capability, revision, profile, _engine_label(db, profile)
    raise _refused("no_engine", "No engine is set for planning. The program is unchanged. Choose one in Engines.", engine=None)


def engine_words(db: Any) -> dict[str, Any]:
    """The engine that shapes on this desk (the bar names it while it
    reads), or ``None`` for both when none is set."""
    try:
        capability, _revision, profile, label = resolve_engine(db)
    except Exception:
        return {"engine": None, "capability": None, "profile": None}
    return {"engine": label or profile, "capability": capability, "profile": profile}


def invoke(db: Any, principal: Any, capability: str, revision: str, payload: dict[str, Any], *,
           contract: str = CONTRACT, contract_revision: str = CONTRACT_REVISION,
           deadline: float = DEADLINE_SECONDS) -> tuple[Optional[str], str]:
    """One routed call; ``(output or None, model)``. The planner
    (``program_planner``) calls it with its own contract and deadline."""
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.prompt_adapter import CanonicalPromptAdapter
    from ..kernel.runtime import _as_principal

    broker = _broker_for(db)
    request = InvocationRequest(
        deployment_revision=revision,
        definition_origin=ServiceContract.for_payload(contract, contract_revision, payload),
        deadline_at=time.time() + deadline,
        payload=payload,
    )
    captured: list[Any] = []

    def _capture(value: Any) -> str:
        captured.append(value)
        return f"{contract.replace('.', '-')}:{revision}"

    with _as_principal(principal):
        outcome = broker.inference_runner.invoke(request, CanonicalPromptAdapter(), publish=_capture)
    if str(getattr(outcome, "outcome", "")) != "succeeded" or not captured:
        return None, ""
    result = captured[0] if isinstance(captured[0], dict) else {"output": captured[0]}
    return str(result.get("output") or ""), str(result.get("model") or "")


def read_answer(output: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """The engine's answer as ``{say, text, question}``, or the reason it
    cannot be read. A bare program text (an engine that ignores the format)
    is read as the text."""
    from ..intel.parsing import _extract_json
    from .program_text import parse_program_text

    raw = str(output or "").strip()
    data: Optional[dict[str, Any]] = None
    try:
        data = _extract_json(raw)
    except Exception:
        data = None
    if data is None and (raw.startswith("# program text") or raw.startswith("program ")):
        data = {"say": "", "text": raw, "question": None}
    if data is None:
        return None, "The answer is not JSON with a 'text'."
    question = data.get("question")
    question = " ".join(str(question).split()) or None if question else None
    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        if question:
            return {"say": str(data.get("say") or ""), "text": "", "question": question}, None
        return None, "The answer has no 'text'."
    model = parse_program_text(text)
    if model.errors:
        return None, "\n".join(error.words if error.words.startswith("Line ") else f"Line {error.line}: {error.words}" for error in model.errors[:8])
    if not model.head.title:
        return None, "The text has no 'program <title>' line."
    return {"say": " ".join(str(data.get("say") or "").split())[:300], "text": text, "question": question}, None


# ── the guard (§4.5) ─────────────────────────────────────────────────

def _outside(path: str) -> bool:
    text = str(path or "").strip()
    return text.startswith(("/", "~")) or text.startswith("..") or "/../" in text


def guard(rows: list[Any], wire: Mapping[str, Any]) -> None:
    """Mark what the engine may not decide: a waive is refused; a core
    question (a file outside the repository, a new phone egress) waits for
    his press like a row that lowers the bar."""
    for row in rows:
        if row.verdict not in ("allowed", "lowers"):
            continue
        data = row.data
        kind = data.get("kind")
        if kind == "waive":
            row.refuse("shape_no_waive", f"{row.where}: Only you waive. Press Waive on the requirement.")
            continue
        core = None
        if kind == "step" and data.get("name") == "owns" and any(_outside(path) for path in data.get("value") or []):
            core = "A file outside the repository."
        elif kind == "add_step" and data.get("step") is not None and any(_outside(p) for p in data["step"].owns):
            core = "A file outside the repository."
        elif (kind == "step" and data.get("name") == "may_call" and data.get("value")) or (
                kind == "head" and data.get("name") == "may_call" and data.get("value")) or (
                kind == "add_step" and data.get("step") is not None and data["step"].may_call):
            core = "The engine may call your phone."
        if core:
            row.verdict, row.lowers_bar, row.code, row.reason = "lowers", True, "core_question", core


def _rows_for(service: Any, principal: Any, program: Mapping[str, Any], wire: Mapping[str, Any],
              base_text: str, text: str) -> tuple[Any, Any, list[Any]]:
    from .program_text import diff_program_text, parse_program_text

    base_model, new_model = parse_program_text(base_text), parse_program_text(text)
    rows = diff_program_text(base_model, new_model, record=wire)
    service._check_text_rows(principal, program, wire, rows)
    guard(rows, wire)
    return base_model, new_model, rows


# ── the shaper ───────────────────────────────────────────────────────

def shape(service: Any, principal: Any, program_id: str, sentence: Any, *,
          invoke_fn: Optional[Callable[..., tuple[Optional[str], str]]] = None,
          pending: Optional[str] = None, rounds: bool = True) -> ShapeResult:
    """One sentence → one call → the change rows (nothing is written).

    LANG5: ``pending`` is the text of the rows that wait in the change well
    (an earlier sentence's ``proposed_text``). The engine reads it in place
    of the current text, so the next sentence adds to those rows; the rows
    stay against the current text, so the well holds every sentence's rows
    until Apply or Not this.

    ``rounds=False`` (an interview answer, LANG9): the round blocks are not
    sent and the text's own rounds are put back on the answer, so the
    engine can never touch a ``?`` line or an ``=`` line."""
    words = " ".join(str(sentence or "").split())
    if not words:
        raise _refused("sentence_required", "Say or type what to change.", status=400)
    if len(words) > SENTENCE_MAX:
        raise _refused("sentence_too_long", f"Say it in {SENTENCE_MAX} characters or fewer.", status=400)
    program = service._program(program_id)
    service._require_writer(principal, program, "shape")
    wire = service.get(principal, program["id"])
    from .program_text import print_program

    printed = print_program(wire)
    text = stripped_text(printed)
    if pending is not None and str(pending).strip():
        from .program_text import parse_program_text, render

        waiting = parse_program_text(str(pending))
        if waiting.errors or not waiting.head.title:
            raise _refused("pending_unreadable", "The changes that wait could not be read. Press Not this, then say "
                                                 "it again.", status=400)
        text = render(waiting)
    if not rounds:
        from .program_text import parse_program_text, render

        unrounded = parse_program_text(text)
        unrounded.rounds = []
        text = render(unrounded)
    frozen = frozen_list(wire)
    ground = grounding(service, wire)
    capability, revision, profile, label = resolve_engine(service.db)
    call = invoke_fn or (lambda payload: invoke(service.db, principal, capability, revision, payload))
    tokens = token_cap(text)
    prompts: list[dict[str, Any]] = []
    started = time.monotonic()
    answer, error, model = None, None, ""
    for attempt in (1, 2):
        system, user = messages(words, text, frozen, ground, error=error if attempt == 2 else None)
        payload = {"system_prompt": system, "user_prompt": user, "temperature": TEMPERATURE, "max_tokens": tokens,
                   "response_format": response_format()}
        prompts.append(payload)
        try:
            output, model = call(payload)
        except Exception as exc:
            log.warning(f"program shaping call failed: {exc}")
            output = None
        engine = model or label
        if output is None:
            if time.monotonic() - started >= DEADLINE_SECONDS:
                raise _refused("engine_timeout", f"{engine} did not answer in {DEADLINE_SECONDS} s. The program is "
                                                 "unchanged. Try again.", status=504, engine=engine)
            raise _refused("engine_failed", f"{engine} did not answer. The program is unchanged. Try again.", status=502,
                           engine=engine)
        answer, error = read_answer(output)
        if answer is not None:
            break
    latency = int((time.monotonic() - started) * 1000)
    engine = model or label
    if answer is None:
        raise _refused("engine_unusable", "The engine's answer could not be read. The program is unchanged. Try again.",
                       status=502, engine=engine, parse_error=error)
    grounded = {"capability": capability, "profile": profile, "repo_paths": len(ground["repo_paths"]),
                "note": bool(ground["note"]), "open_actions": len(ground["open_actions"]),
                "checkpoints": len(ground["checkpoints"]), "frozen": len(frozen)}
    if answer["question"] and not answer["text"]:
        return ShapeResult(proposed_text=text, rows=[], refusals=[], grounded_on=grounded, latency_ms=latency,
                           engine=engine, say=answer["say"], question=answer["question"], attempts=len(prompts),
                           capability=capability, base_text=printed, prompts=prompts)
    if not rounds:
        from .program_text import parse_program_text, render

        answered = parse_program_text(answer["text"])
        answered.rounds = parse_program_text(printed).rounds
        answer["text"] = render(answered)
    _base, _new, rows = _rows_for(service, principal, program, wire, printed, answer["text"])
    refusals = [{"id": row.id, "code": row.code, "reason": row.reason} for row in rows
                if row.verdict in ("refused", "conflict")]
    return ShapeResult(proposed_text=answer["text"], rows=rows, refusals=refusals, grounded_on=grounded,
                       latency_ms=latency, engine=engine, say=answer["say"], question=answer["question"],
                       attempts=len(prompts), capability=capability, base_text=printed, prompts=prompts)


def _answer(service: Any, principal: Any, program: Mapping[str, Any], wire: Mapping[str, Any], base: str,
            proposed: str, rows: list[Any]) -> dict[str, Any]:
    from .program_text import VERSION, allowed_model, parse_program_text, patch, render

    return {
        "program_id": program["id"], "changes": [row.to_wire() for row in rows], "patch": patch(base, proposed),
        "allowed_text": render(allowed_model(parse_program_text(base), parse_program_text(proposed), rows)),
        "applied": False, "text": base, "revision": int(wire.get("revision") or 0), "version": VERSION,
        "refused": sum(1 for row in rows if row.verdict in ("refused", "conflict")),
        "lowers": [row.id for row in rows if row.verdict == "lowers"],
    }


def shape_program(service: Any, principal: Any, program_id: str, sentence: Any, *, apply: bool = False,
                  invoke_fn: Optional[Callable[..., tuple[Optional[str], str]]] = None,
                  pending: Optional[str] = None, rounds: bool = True) -> dict[str, Any]:
    """The REST and MCP answer: the rows of :func:`shape` in the
    ``text_apply`` answer shape (the well draws it as it is), the engine and
    its time; with ``apply`` at YOLO, the allowed rows applied and the
    Decided for you row."""
    from .program_text import allowed_model, parse_program_text, print_program, render

    result = shape(service, principal, program_id, sentence, invoke_fn=invoke_fn, pending=pending, rounds=rounds)
    program = service._program(program_id)
    wire = service.get(principal, program["id"])
    # The rows are against the text the engine read: a field that moved
    # during the call is a conflict at Apply, never hidden.
    base = result.base_text or print_program(wire)
    out = _answer(service, principal, program, wire, base, result.proposed_text, result.rows)
    out.update(sentence=" ".join(str(sentence).split()), say=result.say or _say(result.rows), question=result.question,
               engine=result.engine, latency_ms=result.latency_ms, seconds=round(result.latency_ms / 1000, 1),
               grounded_on=result.grounded_on, refusals=result.refusals, attempts=result.attempts,
               capability=result.capability, proposed_text=result.proposed_text, base=base, decision=None,
               applied_rows=[])
    auto = [row for row in result.rows if row.verdict == "allowed"]
    if not apply or not auto or str(wire.get("control") or "") != "yolo":
        if apply and str(wire.get("control") or "") != "yolo":
            out["held"] = "At Secure and Normal a shaped change waits for Apply."
        return out
    # §4.6: the allowed rows apply at once; the rows that lower the bar, the
    # core questions and the refused rows are put back (the empty-name
    # allow set blocks every ``lowers`` row).
    auto_text = render(allowed_model(parse_program_text(base), parse_program_text(result.proposed_text),
                                     result.rows, allow={"\x00"}))
    numbers = {int(step["ordinal"]): step["id"] for step in wire.get("steps") or []}
    steps_before = set(numbers.values())
    reqs_before = {row["id"] for row in service.requirements(program["id"])}
    applied = service.text_apply(principal, program["id"], auto_text, dry_run=False, base=base)
    if not applied.get("applied"):
        out["held"] = "The change could not apply at once. It waits for Apply."
        return out
    fresh = applied["program"]
    after = print_program(fresh)
    added_steps = [step["id"] for step in fresh.get("steps") or [] if step["id"] not in steps_before]
    added_reqs = [row["id"] for row in service.requirements(program["id"]) if row["id"] not in reqs_before]
    touched = sorted({numbers[row.data["number"]] for row in auto
                      if row.data.get("number") in numbers} | {numbers[int(row.where.split(" ")[1])] for row in auto
                                                                if row.data.get("kind") == "move"
                                                                and row.data.get("key", "").startswith("s")
                                                                and int(row.where.split(" ")[1]) in numbers})
    line = f"Shaped by a sentence: {out['say'] or out['sentence']}"[:400]
    amended = any(row.data.get("kind") == "amend" for row in auto)
    decision = service.engine_decision(
        service._program(program["id"]), None, "shape",
        SimpleNamespace(choice="shape", rule=YOLO_RULE, overturnable=not amended), line,
        undo={"base_text": stripped_text(base), "numbers": {str(k): v for k, v in numbers.items()},
              "added_steps": added_steps, "added_requirements": added_reqs, "touched": touched,
              "sentence": out["sentence"]})
    service._touch(service._program(program["id"]))
    fresh = service.get(principal, program["id"])
    after = print_program(fresh)
    # The rows still waiting for his press, against the text as it is now.
    waiting = [row for row in result.rows if row.verdict == "lowers"]
    rest: list[Any] = []
    residual = after
    if waiting:
        residual = render(_residual(parse_program_text(after), parse_program_text(result.proposed_text), waiting,
                                    numbers, fresh))
        _b, _n, rest = _rows_for(service, principal, service._program(program["id"]), fresh, after, residual)
    out.update(_answer(service, principal, program, fresh, after, residual, rest))
    out.update(applied=True, program=fresh, text=after, base=after, proposed_text=residual, decision=decision,
               applied_rows=[row.to_wire() for row in auto])
    return out


def apply_allowed(service: Any, principal: Any, program_id: str, base: str, proposed: str) -> dict[str, Any]:
    """LANG5, a call's yes: the allowed rows of a shaped answer applied
    through ``text_apply`` (his yes is his press: no Decided for you row);
    the rows that lower the bar or are core questions are put back and come
    back as ``waiting`` (the ``text_apply`` answer shape, against the text as
    it is now) for the change well on the desk. ``applied`` False: nothing
    could apply (a row changed since the read back)."""
    from .program_text import allowed_model, parse_program_text, print_program, render

    program = service._program(program_id)
    wire = service.get(principal, program["id"])
    _b, _n, rows = _rows_for(service, principal, program, wire, base, proposed)
    auto = [row for row in rows if row.verdict == "allowed"]
    waiting = [row for row in rows if row.verdict == "lowers"]
    numbers = {int(step["ordinal"]): step["id"] for step in wire.get("steps") or []}
    if not auto:
        return {"applied": False, "applied_rows": [], "waiting": None}
    auto_text = render(allowed_model(parse_program_text(base), parse_program_text(proposed), rows, allow={"\x00"}))
    applied = service.text_apply(principal, program["id"], auto_text, dry_run=False, base=base)
    if not applied.get("applied"):
        return {"applied": False, "applied_rows": [], "waiting": None}
    fresh = service.get(principal, program["id"])
    out: dict[str, Any] = {"applied": True, "applied_rows": [row.to_wire() for row in auto], "program": fresh,
                           "waiting": None}
    if waiting:
        after = print_program(fresh)
        residual = render(_residual(parse_program_text(after), parse_program_text(proposed), waiting, numbers, fresh))
        _b, _n, rest = _rows_for(service, principal, service._program(program["id"]), fresh, after, residual)
        if rest:
            answer = _answer(service, principal, program, fresh, after, residual, rest)
            answer.update(base=after, proposed_text=residual)
            out["waiting"] = answer
    return out


def _residual(after: Any, proposed: Any, waiting: list[Any], numbers: Mapping[int, str],
              fresh: Mapping[str, Any]) -> Any:
    """The text as it is now with only the rows that wait for his press
    made again on it (the numbers moved when a step was added)."""
    ordinal = {step["id"]: int(step["ordinal"]) for step in fresh.get("steps") or []}
    now = {n: ordinal[sid] for n, sid in numbers.items() if sid in ordinal}
    out = replace(after, head=replace(after.head), steps=[replace(step) for step in after.steps])
    by_number = {step.number: step for step in out.steps}
    for row in waiting:
        data = row.data
        kind = data.get("kind")
        if kind == "head":
            setattr(out.head, data["name"], data["value"])
        elif kind == "step" and data.get("name") != "after" and data.get("number") in now:
            target = by_number.get(now[data["number"]])
            if target is not None:
                setattr(target, data["name"], data["value"])
        elif kind == "edit_requirement":
            from .program_text import _swap_requirement

            _swap_requirement(out, data["rid"], data["row"])
        elif kind == "add_step":
            step = data["step"]
            index = proposed.steps.index(step) if step in proposed.steps else len(proposed.steps)
            succ = next((item.number for item in proposed.steps[index + 1:] if item.number in now), None)
            at = next((i for i, item in enumerate(out.steps) if succ is not None and item.number == now[succ]),
                      len(out.steps))
            out.steps.insert(at, replace(step, after=[now.get(value, value) for value in step.after]))
    return out


def _say(rows: list[Any]) -> str:
    said = [row.say.rstrip(".") for row in rows if row.say][:3]
    return "; ".join(said)


# ── Overturn (§4.6) ──────────────────────────────────────────────────

def overturn_shape(service: Any, principal: Any, program: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """Put back what one YOLO shaping applied: the added steps go, the added
    requirements are set aside, every changed field and the order come back
    through ``text_apply``. Withheld when a step it touched has started."""
    from .program_text import parse_program_text, print_program, render

    undo = dict(row.get("undo") or {})
    pid = program["id"]
    steps = {step["id"]: step for step in service.store.list_steps(pid)}
    for sid in list(undo.get("touched") or []) + list(undo.get("added_steps") or []):
        step = steps.get(sid)
        if step is not None and step.get("state") not in ("planned", "ready"):
            raise _refused("not_overturnable", f"Step {step.get('ordinal')} started. The shaped change stays.")
    from .program_service import _LOCK

    with _LOCK:
        gone = set()
        for sid in undo.get("added_steps") or []:
            if sid in steps:
                gone.add(int(steps[sid]["ordinal"]))
                service.store.delete_step(sid)
        if gone:
            # No step waits for a step that went; the numbers close up.
            for step in service.store.list_steps(pid):
                if set(int(v) for v in step.get("after") or []) & gone:
                    step["after"] = [v for v in step.get("after") or [] if int(v) not in gone]
                    service._save(step)
            service._reorder(program, [step["id"] for step in service._top_order(pid)], by="owner")
        for rid in undo.get("added_requirements") or []:
            added = service.store.get_requirement(str(rid))
            if added is not None and added.get("state") != "waived":
                service._waive(program, added, "You overturned the shaped change")
                added = service.store.get_requirement(str(rid)) or added
                added["required"] = False
                service.store.save_requirement(added)
        wire = service.get(principal, pid)
        current = print_program(wire)
        now_model = parse_program_text(current)
        ordinal = {step["id"]: int(step["ordinal"]) for step in wire.get("steps") or []}
        numbers = {int(k): v for k, v in dict(undo.get("numbers") or {}).items()}
        inverse = parse_program_text(str(undo.get("base_text") or ""))
        renumber = {n: ordinal[sid] for n, sid in numbers.items() if sid in ordinal}
        inverse.steps = [replace(step, number=renumber.get(step.number, step.number),
                                 after=[renumber.get(value, value) for value in step.after]) for step in inverse.steps]
        # A requirement the shaping added stays (set aside), so the inverse keeps it.
        kept = {req.rid for _where, req in inverse.requirements()}
        for where, req in now_model.requirements():
            if req.rid is None or req.rid in kept:
                continue
            if where == "every step":
                inverse.every_step.append(req)
            elif where == "at the end":
                inverse.at_end.append(req)
            else:
                number = int(where.split(" ")[1])
                target = next((step for step in inverse.steps if step.number == number), None)
                if target is not None:
                    target.requirements.append(req)
        inverse_text = render(inverse)
        dry = service.text_apply(principal, pid, inverse_text, dry_run=True, base=current)
        blocked = [item for item in dry["changes"] if item["verdict"] in ("refused", "conflict")]
        if blocked:
            raise _refused("not_overturnable", f"{blocked[0].get('reason') or 'A change cannot be put back.'}")
        if dry["changes"]:
            service.text_apply(principal, pid, inverse_text, dry_run=False, base=current,
                               allow_lower=[item["id"] for item in dry["changes"] if item["verdict"] == "lowers"])
        fresh = service._program(pid)
        service.store.mark_overturned(int(row["id"]), service._clock())
        service._checkpoint(fresh, None, "owner", f"Overturned: {row['line']}")
        service._touch(fresh)
        service.changed(pid, None, verb="overturn", text=True)
    service._tick_now(pid)
    return {"program": service.get(principal, pid)}


__all__ = [
    "CAPABILITY", "CONTRACT", "engine_words", "token_cap", "DEADLINE_SECONDS", "FALLBACK_CAPABILITY", "GRAMMAR_CARD", "ShapeResult", "YOLO_RULE",
    "grounding", "guard", "messages", "overturn_shape", "read_answer", "resolve_engine", "response_format", "shape",
    "shape_program", "stripped_text",
]
