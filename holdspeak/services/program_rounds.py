"""The interview rounds (PG-LANG LANG9, 2026-10-31).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §6.2, §6.5
station 3, §9.4, §12; PROGRAM-JOURNEYS-2026-10-31.md J1 and "Reconciled".
From a goal or a planning draft, the engine asks the few questions that
change the plan, in named rounds (his names: Architecture, Product, Stack,
Verification, Delivery), ONE question at a time.

- ``open_rounds``: the default rounds (or the names given) in
  ``program_rounds``, each ``open``. A round the Program has already stays.
- ``ask``: one call on the shaper's machinery (the ``agent.plan``
  assignment, else the Ask engine; the runner's one path; one retry with
  the reason; an honest refusal), contract ``program.round@1``: in, the
  Program text without lamps, the round's charter line, the questions so
  far, the grounding the planner reads (the repository map, the Note, the
  Project's open actions); out ``{question, why_it_matters, choices, done}``.
  ``done: true`` closes the round by the engine's word. A question that
  waits is answered again without a call.
- ``answer``: his words (typed, spoken, or an offered choice) are the ``=``
  line; then ONE shaping call (``program_shaper``) with the sentence "In the
  <round> round, to '<question>', the owner said '<answer>'", the round
  blocks left out of that prompt. The rows wait in the change well for
  Apply (source ``round:<name>``); at YOLO with ``apply`` the allowed rows
  land as any shaped change does. The question keeps what it became.
- ``skip_question``, ``skip_round``, ``done`` (withheld while a question
  waits), ``reopen`` (Ask more, also while the Program runs).
- Rounds help; they do not gate Start (§15.5). ``?`` lines are the
  engine's: the text refuses a changed one (``program_text``).
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from . import program_shaper as shaper

log = get_logger("program_rounds")

CONTRACT = "program.round"
CONTRACT_REVISION = "1"
TEMPERATURE = 0.2
#: The home engine thinks before it answers; a question is short.
DEADLINE_SECONDS = 120
MAX_TOKENS = 5000
#: "the few questions that change the plan": after this many, the round is done by rule.
QUESTIONS_MAX = 4
CHOICES_MAX = 3
ANSWER_MAX = 300

#: §6.2: the default rounds and their charter lines (the names are his).
CHARTERS: dict[str, str] = {
    "Architecture": "the boundaries, the data, what must not change, where the risk is",
    "Product": "who it is for, what he will see, what 'done' looks like to that person",
    "Stack": "the libraries, the versions, the commands, what the repository already has",
    "Verification": "how each claim is proven: which tests, which windows, which numbers",
    "Delivery": "the order, the merge rule, the control level, the night",
}
DEFAULT_ROUNDS = tuple(CHARTERS)

ROUND_RULES = f"""RULES FOR A QUESTION
- Ask ONE question: the one whose answer would change the plan most in this round.
- Never ask what the goal or the text already answers. Never ask a question asked before.
- "question": one short sentence, at most 20 words, in plain words.
- "why_it_matters": one short line: what in the plan the answer decides (a step, a requirement, a gate).
- "choices": up to {CHOICES_MAX} short answers he can press, at most 8 words each, the most likely first;
  [] when no short answer fits.
- "done": true, with "question" empty, when no question is left in this round that would change the plan."""


def _refused(code: str, detail: str, status: int = 409, **more: Any) -> Exception:
    from .program_service import ProgramRefused

    return ProgramRefused(code, detail, status=status, **more)


def response_format() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "program_round", "strict": True, "schema": {
        "type": "object", "additionalProperties": False,
        "required": ["question", "why_it_matters", "choices", "done"],
        "properties": {
            "question": {"type": "string", "maxLength": 300},
            "why_it_matters": {"type": "string", "maxLength": 300},
            "choices": {"type": "array", "maxItems": CHOICES_MAX, "items": {"type": "string", "maxLength": 80}},
            "done": {"type": "boolean"},
        }}}}


def charter(name: str) -> str:
    for key, line in CHARTERS.items():
        if key.casefold() == str(name).strip().casefold():
            return line
    return f"what the {name} round of this program must settle"


def _fold(name: Any) -> str:
    return "".join(str(name or "").split()).casefold()


def _clean(text: Any, limit: int) -> str:
    return " ".join(str(text or "").split())[:limit]


# ── the round rows ───────────────────────────────────────────────────

def _rounds(service: Any, pid: str) -> list[dict[str, Any]]:
    return service.store.list_rounds(pid)


def _round(service: Any, pid: str, name: Any) -> dict[str, Any]:
    key = _fold(name)
    found = next((row for row in _rounds(service, pid) if _fold(row["name"]) == key), None)
    if found is None:
        raise _refused("round_unknown", f"The program has no round {_clean(name, 60) or 'of that name'}.", status=404)
    return found


def waiting(round_: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """The question that waits for his answer (one at a time)."""
    return next((item for item in round_.get("questions") or []
                 if not item.get("answer") and not item.get("skipped")), None)


def _writable(service: Any, principal: Any, pid: str, verb: str) -> dict[str, Any]:
    program = service._program(pid)
    service._require_writer(principal, program, verb)
    if program.get("state") == "done":
        raise _refused("program_closed", "The program is done. Reopen it to ask more.")
    return program


def _save(service: Any, pid: str, row: Mapping[str, Any]) -> None:
    service.store.save_round({**row, "program_id": pid, "updated_at": service._clock()})


def _changed(service: Any, pid: str, line: Optional[str] = None, *, by: str = "owner") -> None:
    program = service._program(pid)
    if line:
        service._checkpoint(program, None, by, line)
    service._touch(service._program(pid))
    service.changed(pid, verb="round", text=True)


def _who(principal: Any) -> str:
    from .program_service import _is_owner

    return "owner" if _is_owner(principal) else "agent"


def open_rounds(service: Any, principal: Any, program_id: str, names: Any = None) -> dict[str, Any]:
    """The rounds to ask (the defaults, or ``names``), each ``open``; a round
    the Program has already keeps its state and its questions."""
    from .program_service import _LOCK

    program = _writable(service, principal, program_id, "round")
    pid = program["id"]
    wanted = [_clean(name, 40) for name in (names or []) if _clean(name, 40)] or list(DEFAULT_ROUNDS)
    with _LOCK:
        have = _rounds(service, pid)
        known = {_fold(row["name"]) for row in have}
        order = max((int(row["ordinal"]) for row in have), default=0)
        added = []
        for name in wanted:
            if _fold(name) in known:
                continue
            order += 1
            known.add(_fold(name))
            _save(service, pid, {"name": name, "state": "open", "ordinal": order, "questions": []})
            added.append(name)
        if added:
            _changed(service, pid)
    return {"program": service.get(principal, pid), "added": added}


# ── the engine call (contract program.round@1) ───────────────────────

def messages(text: str, round_: Mapping[str, Any], ground: Mapping[str, Any], repo: Mapping[str, Any], *,
             error: Optional[str] = None) -> tuple[str, str]:
    """The system and user prompt of ``program.round@1``."""
    name = str(round_["name"])
    system = "\n\n".join([
        "You run one interview round on a HoldSpeak Program: you ask its owner, a senior software architect, "
        "the one question that changes the plan most. You answer JSON only: "
        '{"question": "...", "why_it_matters": "...", "choices": ["..."], "done": false}.',
        shaper.GRAMMAR_CARD, ROUND_RULES,
    ])
    asked = list(round_.get("questions") or [])
    parts = [
        "THE PROGRAM TEXT NOW\n" + text.rstrip("\n"),
        f"THE ROUND: {name}\nIn this round you ask about {charter(name)}.",
    ]
    if asked:
        lines = []
        for item in asked:
            lines.append(f"? {item.get('text')}")
            lines.append(f"= {item['answer']}" if item.get("answer") else "= (he skipped it)")
        parts.append(f"THIS ROUND SO FAR ({len(asked)} of at most {QUESTIONS_MAX} questions)\n" + "\n".join(lines))
    if repo.get("likely"):
        parts.append("FILES THE GOAL IS LIKELY ABOUT (size in tokens)\n" + "\n".join(repo["likely"]))
    if repo.get("headings"):
        parts.append("THE REPOSITORY'S WORKING AGREEMENTS (headings)\n" + "\n".join(repo["headings"]))
    if repo.get("recent"):
        parts.append("THE LAST CHANGES MERGED\n" + "\n".join(f"- {item}" for item in repo["recent"]))
    if ground.get("note"):
        parts.append("THE NOTE THE PROGRAM CAME FROM\n" + str(ground["note"]))
    if ground.get("open_actions"):
        parts.append("THE PROJECT'S OPEN ACTIONS\n" + "\n".join(f"- {item}" for item in ground["open_actions"]))
    if error:
        parts.append("YOUR LAST ANSWER COULD NOT BE READ: " + error + "\nAnswer again, correct.")
    return system, "\n\n".join(parts)


def read_question(output: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """The engine's answer as ``{question, why, choices, done}``, or the
    reason it cannot be read."""
    from ..intel.parsing import _extract_json

    try:
        data = _extract_json(str(output or "").strip())
    except Exception:
        data = None
    if not isinstance(data, dict):
        return None, "The answer is not JSON."
    done = data.get("done") is True
    question = _clean(data.get("question"), 300)
    if not done and not question:
        return None, "The answer has no 'question' and 'done' is not true."
    choices: list[str] = []
    for item in data.get("choices") if isinstance(data.get("choices"), list) else []:
        word = _clean(item, 80)
        if word and word.casefold() not in {choice.casefold() for choice in choices}:
            choices.append(word)
    return {"question": "" if done else question, "why": "" if done else _clean(data.get("why_it_matters"), 300),
            "choices": [] if done else choices[:CHOICES_MAX], "done": done}, None


def ask(service: Any, principal: Any, program_id: str, name: Any, *,
        invoke_fn: Optional[Callable[..., tuple[Optional[str], str]]] = None) -> dict[str, Any]:
    """The ONE next question of a round (or the round done by the engine's
    word). A question that waits is answered again without a call."""
    from .program_planner import repo_ground
    from .program_service import _LOCK
    from .program_text import print_program

    program = _writable(service, principal, program_id, "round")
    pid = program["id"]
    if not _rounds(service, pid) and _fold(name) in {_fold(item) for item in DEFAULT_ROUNDS}:
        open_rounds(service, principal, pid)
    row = _round(service, pid, name)
    if row["state"] in ("done", "skipped"):
        raise _refused("round_closed", f"Round {row['name']} is {row['state']}. Press Ask more to open it again.")
    held = waiting(row)
    if held is not None:
        return _asked(service, principal, pid, row, held, engine=None, seconds=0.0)
    if len(row.get("questions") or []) >= QUESTIONS_MAX:
        return _close(service, principal, pid, row, by="engine",
                      line=f"Round {row['name']} done: {QUESTIONS_MAX} questions asked")
    wire = service.get(principal, pid)
    text = shaper.stripped_text(print_program(wire))
    ground = shaper.grounding(service, wire)
    repo = repo_ground(str((wire.get("repository") or {}).get("root") or "") or None,
                       str(wire.get("goal") or "") + "\n" + str(ground.get("note") or ""))
    capability, revision, _profile, label = shaper.resolve_engine(service.db)
    call = invoke_fn or (lambda payload: shaper.invoke(service.db, principal, capability, revision, payload,
                                                       contract=CONTRACT, contract_revision=CONTRACT_REVISION,
                                                       deadline=DEADLINE_SECONDS))
    started = time.monotonic()
    answer, error, model = None, None, ""
    for attempt in (1, 2):
        system, user = messages(text, row, ground, repo, error=error if attempt == 2 else None)
        payload = {"system_prompt": system, "user_prompt": user, "temperature": TEMPERATURE,
                   "max_tokens": MAX_TOKENS, "response_format": response_format()}
        try:
            output, model = call(payload)
        except Exception as exc:
            log.warning(f"program round call failed: {exc}")
            output = None
        engine = model or label
        if output is None:
            if time.monotonic() - started >= DEADLINE_SECONDS:
                raise _refused("engine_timeout", f"{engine} did not answer in {DEADLINE_SECONDS} s. Try again.",
                               status=504, engine=engine)
            raise _refused("engine_failed", f"{engine} did not answer. Try again.", status=502, engine=engine)
        answer, error = read_question(output)
        if answer is not None:
            break
    engine = model or label
    seconds = round(time.monotonic() - started, 1)
    if answer is None:
        raise _refused("engine_unusable", "The engine's question could not be read. Try again.", status=502,
                       engine=engine, parse_error=error)
    with _LOCK:
        row = _round(service, pid, name)
        if answer["done"]:
            out = _close(service, principal, pid, row, by="engine", line=f"Round {row['name']} done: no question left")
            out.update(engine=engine, seconds=seconds)
            return out
        question = {"id": f"q-{uuid.uuid4().hex[:10]}", "text": answer["question"], "why": answer["why"],
                    "choices": answer["choices"], "answer": None, "answered_by": None, "at": None,
                    "skipped": False, "became": [], "asked_at": service._clock(), "engine": engine}
        row = {**row, "state": "asking", "questions": [*(row.get("questions") or []), question]}
        _save(service, pid, row)
        _changed(service, pid)
    return _asked(service, principal, pid, row, question, engine=engine, seconds=seconds)


def _asked(service: Any, principal: Any, pid: str, row: Mapping[str, Any], question: Mapping[str, Any], *,
           engine: Optional[str], seconds: float) -> dict[str, Any]:
    return {"round": row["name"], "state": "asking", "done": False, "question": dict(question), "engine": engine,
            "seconds": seconds, "program": service.get(principal, pid)}


def _close(service: Any, principal: Any, pid: str, row: Mapping[str, Any], *, by: str, line: str,
           state: str = "done") -> dict[str, Any]:
    _save(service, pid, {**row, "state": state})
    _changed(service, pid, line, by=by)
    return {"round": row["name"], "state": state, "done": True, "question": None, "engine": None, "seconds": 0.0,
            "program": service.get(principal, pid)}


# ── his answer becomes text ──────────────────────────────────────────

def _became(row: Mapping[str, Any]) -> str:
    """One proposed row in a few words: ``step 1 owns``, ``R+ measure``, ``+ step``."""
    where, field, op = str(row.get("where") or ""), str(row.get("field") or ""), str(row.get("op") or "")
    if field == "requirement" and op == "add":
        kind = str(row.get("after") or "").split(":", 1)[0].split(" ")[0]
        return f"R+ {kind}".strip()
    if field == "step" and op == "add":
        return f"+ {where}"
    return f"{where} {field.replace('_', ' ')}".strip()


#: §6.2's sentence alone ("In the <round> round, to '<question>', the owner
#: said '<answer>'") made the real engine answer "Confirmed" and change
#: nothing (recorded 2026-10-31): the shaper's rule is "change only what the
#: sentence asks". So the sentence also says where an answer goes.
WRITE_IT = ("Write this answer into the plan where it belongs: a step's brief ('>' lines), a step's owns, a new "
            "requirement (R+ check, review, shot, word or measure) or a gate. A step that has not started gets "
            "'>' lines, never '+' lines.")


def sentence_of(round_name: str, question: str, said: str, why: str = "") -> str:
    """§6.2: the sentence the shaping call reads (at most the shaper's 1000 characters)."""
    head = f"In the {round_name} round, to '{question}'"
    tail = f", the owner said '{said}'. {WRITE_IT}"
    room = shaper.SENTENCE_MAX - len(head) - len(tail) - 4
    if why and room > 40:
        head += f" ({why[:room].rstrip()})"
    return (head + tail)[:shaper.SENTENCE_MAX]


def answer(service: Any, principal: Any, program_id: str, name: Any, said: Any = None, *,
           question_id: Optional[str] = None, choice: Any = None, apply: bool = False,
           invoke_fn: Optional[Callable[..., tuple[Optional[str], str]]] = None) -> dict[str, Any]:
    """His answer to the waiting question (or, by ``question_id``, a new
    answer to one he answered while the round is not done): the ``=`` line,
    then one shaping call; the rows (source ``round:<name>``) wait for Apply."""
    from .program_service import _LOCK, _is_owner
    from .program_shaper import shape_program

    words = _clean(choice if choice not in (None, "") else said, ANSWER_MAX)
    if not words:
        raise _refused("answer_required", "Say, type or press an answer.", status=400)
    program = _writable(service, principal, program_id, "round")
    pid = program["id"]
    with _LOCK:
        row = _round(service, pid, name)
        if row["state"] in ("done", "skipped"):
            raise _refused("round_closed", f"Round {row['name']} is {row['state']}. Press Ask more to open it again.")
        questions = [dict(item) for item in row.get("questions") or []]
        target = next((item for item in questions if question_id and item.get("id") == question_id), None) \
            or (waiting(row) if not question_id else None)
        if target is None:
            raise _refused("no_question", f"No question of round {row['name']} waits. Press Ask.", status=409)
        target = next(item for item in questions if item.get("id") == target.get("id"))
        target.update(answer=words, answered_by=_who(principal), at=service._clock(), skipped=False, became=[])
        _save(service, pid, {**row, "questions": questions})
        _changed(service, pid)
    out = shape_program(service, principal, pid,
                        sentence_of(row["name"], str(target["text"]), words, str(target.get("why") or "")),
                        apply=apply and _is_owner(principal), invoke_fn=invoke_fn, rounds=False)
    source = f"round:{row['name']}"
    for item in out.get("changes") or []:
        item["source"] = source
    for item in out.get("applied_rows") or []:
        item["source"] = source
    became = [_became(item) for item in [*(out.get("applied_rows") or []), *(out.get("changes") or [])]
              if item.get("verdict") in ("allowed", "lowers")]
    with _LOCK:
        row = _round(service, pid, name)
        questions = [dict(item) for item in row.get("questions") or []]
        for item in questions:
            if item.get("id") == target["id"]:
                item["became"] = list(dict.fromkeys(became))
        _save(service, pid, {**row, "questions": questions})
        _changed(service, pid)
    out.update(source=source, round=row["name"], round_question={**target, "became": list(dict.fromkeys(became))},
               program=service.get(principal, pid))
    return out


def not_this(service: Any, principal: Any, program_id: str, name: Any, question_id: str) -> dict[str, Any]:
    """Not this on an answer's rows: the answer stays, it became nothing."""
    from .program_service import _LOCK

    program = _writable(service, principal, program_id, "round")
    pid = program["id"]
    with _LOCK:
        row = _round(service, pid, name)
        questions = [dict(item) for item in row.get("questions") or []]
        for item in questions:
            if item.get("id") == question_id:
                item["became"] = []
        _save(service, pid, {**row, "questions": questions})
        _changed(service, pid)
    return {"round": row["name"], "program": service.get(principal, pid)}


# ── the presses: Skip question, Skip round, Done with, Ask more ──────

def skip_question(service: Any, principal: Any, program_id: str, name: Any,
                  question_id: Optional[str] = None) -> dict[str, Any]:
    from .program_service import _LOCK

    program = _writable(service, principal, program_id, "round")
    pid = program["id"]
    with _LOCK:
        row = _round(service, pid, name)
        held = waiting(row)
        if held is None or (question_id and held.get("id") != question_id):
            raise _refused("no_question", f"No question of round {row['name']} waits.")
        questions = [dict(item) for item in row.get("questions") or []]
        for item in questions:
            if item.get("id") == held["id"]:
                item.update(skipped=True, at=service._clock(), answered_by=_who(principal))
        _save(service, pid, {**row, "questions": questions})
        _changed(service, pid)
    return {"round": row["name"], "skipped": held["id"], "program": service.get(principal, pid)}


def decide(service: Any, principal: Any, program_id: str, name: Any, choice: Any) -> dict[str, Any]:
    """``done`` (Done with <round>; withheld while a question waits), ``skip``
    (Skip round; always there), ``reopen`` (Ask more; also while it runs)."""
    from .program_service import _LOCK

    program = _writable(service, principal, program_id, "round")
    pid = program["id"]
    verb = str(choice or "").strip().lower()
    if verb not in ("done", "skip", "reopen"):
        raise _refused("bad_choice", "Choose done, skip or reopen.", status=400)
    by = _who(principal)
    with _LOCK:
        row = _round(service, pid, name)
        if verb == "reopen":
            if row["state"] not in ("done", "skipped"):
                return {"round": row["name"], "state": row["state"], "program": service.get(principal, pid)}
            _save(service, pid, {**row, "state": "open"})
            _changed(service, pid, f"Round {row['name']} open again", by=by)
            return {"round": row["name"], "state": "open", "program": service.get(principal, pid)}
        if verb == "done":
            if waiting(row) is not None:
                raise _refused("round_question_waits",
                               f"A question of round {row['name']} waits. Answer it or press Skip question.")
            changes = sum(len(item.get("became") or []) for item in row.get("questions") or [])
            line = f"Round {row['name']} done" + (f": {changes} change{'s' if changes != 1 else ''}" if changes else "")
            out = _close(service, principal, pid, row, by=by, line=line)
            return {"round": row["name"], "state": "done", "program": out["program"]}
        # skip: a waiting question goes with the round.
        questions = [dict(item) for item in row.get("questions") or []]
        for item in questions:
            if not item.get("answer") and not item.get("skipped"):
                item.update(skipped=True, at=service._clock(), answered_by=by)
        out = _close(service, principal, pid, {**row, "questions": questions}, by=by,
                     line=f"Round {row['name']} skipped", state="skipped")
        return {"round": row["name"], "state": "skipped", "program": out["program"]}


def act(service: Any, principal: Any, program_id: str, action: Any, *, round_name: Any = None, answer_text: Any = None,
        choice: Any = None, question_id: Optional[str] = None, names: Any = None, apply: bool = False) -> dict[str, Any]:
    """The one MCP verb ``program.round``."""
    verb = str(action or "").strip().lower()
    if verb == "open":
        return open_rounds(service, principal, program_id, names)
    if not round_name:
        raise _refused("round_required", "Name the round.", status=400)
    if verb == "next":
        return ask(service, principal, program_id, round_name)
    if verb == "answer":
        return answer(service, principal, program_id, round_name, answer_text, question_id=question_id, choice=choice,
                      apply=apply)
    if verb == "skip_question":
        return skip_question(service, principal, program_id, round_name, question_id)
    if verb == "not_this":
        return not_this(service, principal, program_id, round_name, str(question_id or ""))
    if verb in ("done", "skip", "reopen"):
        return decide(service, principal, program_id, round_name, verb)
    raise _refused("bad_action", "Choose open, next, answer, skip_question, not_this, done, skip or reopen.", status=400)


__all__ = ["CHARTERS", "CONTRACT", "DEFAULT_ROUNDS", "QUESTIONS_MAX", "ROUND_RULES", "act", "answer", "ask", "charter",
           "decide", "messages", "not_this", "open_rounds", "read_question", "response_format", "sentence_of",
           "skip_question", "waiting"]
