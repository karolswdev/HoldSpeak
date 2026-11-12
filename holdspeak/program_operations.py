"""The Programs verbs on the one declared contract (2026-11-08, one contract).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``desk_window_operations.py`` is. Each descriptor states
one Programs verb once: its ``ProgramService`` call (``call``, and
``web_call`` where the HTTP shape differs: by id, not by his words; the desk's
own field names), its HTTP method and path, its MCP tool schema, its
authority class and its thread class. ``web/routes/programs.py`` produces the
routes and ``mcp/families/program.py`` the tool rows from these rows, both
through ``OperationRegistry.invoke``.

A row with no ``tool_schema`` is HTTP only: another tool reaches the same verb
(``program.decide`` kind ``close``, ``requirement`` and the proposal kinds;
``program.require`` with ``requirement_id``; ``program.round``). A row with no
``http`` is MCP only. The evidence read answers a file: its route stays
hand-written (``web/routes/programs.py`` ``HAND_WRITTEN``).

The contract adds nothing to what the transports did before: the arguments
schema is any object (the service validates, as it did), there is no
admission (no kernel operation, no receipt: the engine keeps its own ledger),
and the service announces each change itself (``program_changed``).

The authority rules live in the service, so every transport keeps them:

- ``program.create`` / ``program.plan`` / ``program.start`` /
  ``program.park`` / ``program.resume``: the owner, or an orchestrating agent
  on a Program it created;
- ``program.get`` / ``program.list`` / ``program.templates``: anyone;
- ``program.checkpoint`` / ``program.step_done``: the step's own launch (by
  its credential) and, for checkpoints, the owner; any other caller is
  refused ``not_your_step``;
- ``program.start_from`` (PG20): the owner (the step is added) or the step's
  own launch (the ladder decides: Secure and Normal ask him, YOLO adds it);
- ``program.decide``, ``program.overturn``, ``program.handoff`` (PG19),
  ``program.step_take`` and ``program.step_hand_back`` (IMP6): the owner
  only (AUTHORITY, never in the CONDUCTOR palette).
- PG-REQ (2026-10-31): ``program.require`` (add a requirement, or his edit
  of one), ``program.step_update`` (change a step, move it) and
  ``program.amend`` (a line added to a started step's brief): his at once;
  an orchestrating agent's (and, for ``program.require``, a step's own
  agent's) by the Control level. No tool says a requirement is met: the
  engine judges it, or he presses (``program.decide`` kind ``requirement``).
- PG-LANG (2026-10-31): ``program.text`` reads a Program as its text;
  ``program.text_apply`` previews or applies a changed text through the
  verbs above, so each change keeps its own authority rule;
  ``program.plan_draft`` drafts a Program from its goal; ``program.round``
  runs the interview rounds; ``program.shape`` turns one sentence into change
  rows (it writes nothing, except at YOLO with ``apply``);
  ``program.add_to_night`` puts an item in tonight's dreaming program.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.held_arguments import held_arguments, text, hidden, named

WORK, AUTHORITY = "work", "authority"
READ, EFFECT = "evidence_read", "effect_proposal"

Call = Callable[[Any, Any, dict[str, Any]], Any]

_ANY_OBJECT = {"type": "object"}
_ANSWER_BINDING = {
    "type": ["object", "null"],
    "description": "Question binding from the program wire: selected step, revision and latest visible ledger checkpoint. Required for HTTP answers.",
    "properties": {"program_id": {"type": "string"}, "step_revision": {"type": "string"}, "step_id": {"type": "string"}, "revision": {"type": "integer"}, "checkpoint_id": {"type": "integer"}},
    "required": ["step_id", "revision", "checkpoint_id"], "additionalProperties": False,
}

_PRINCIPAL = ("derived by the transport (HTTP auth middleware; MCP auth resolver); the Programs service checks "
              "the owner, the orchestrating agent or the step's own launch")
_REFUSALS = _CONTRACT_REFUSALS + ("the Programs service's named refusals (ProgramRefused: code, detail, status)",)


#: The ProgramService method each verb reaches (``program.templates`` reads the template list itself).
_METHODS: dict[str, str] = {
    "program.list": "list", "program.templates": "templates", "program.create": "create",
    "program.from_action": "from_action", "program.add_to_night": "add_to_night", "program.get": "get",
    "program.update": "update", "program.plan": "plan", "program.start": "start",
    "program.park": "park", "program.resume": "resume", "program.decide": "decide",
    "program.race": "race", "program.handoff": "handoff", "program.start_from": "start_from",
    "program.overturn": "overturn", "program.step_update": "change_step", "program.step_take": "take_over",
    "program.step_hand_back": "hand_back", "program.amend": "amend", "program.require": "require",
    "program.requirement_edit": "edit_requirement", "program.requirement_decide": "decide_requirement", "program.proposal_decide": "decide_proposal",
    "program.requirement_evidence": "requirement_evidence", "program.text": "text_get", "program.text_apply": "text_apply",
    "program.shape_engine": "shape_engine", "program.shape": "shape", "program.shape_held_drop": "drop_held_shape",
    "program.plan_draft": "plan_draft", "program.plan_programs": "apply_programs", "program.rounds_open": "rounds_open",
    "program.round_next": "round_next", "program.round_answer": "round_answer", "program.round_decide": "round_decide",
    "program.close": "close", "program.propose_fix": "propose_fix", "program.step_remove": "remove_step",
    "program.round": "round", "program.checkpoint": "checkpoint", "program.step_done": "step_done",
}


def _op(name: str, call: Call, http: Optional[tuple[str, str]] = None, *, method: Optional[str] = None,
        schema: Optional[Mapping[str, Any]] = None, description: str = "", authority: str = WORK,
        thread: Optional[str] = EFFECT, status: int = 200, web: Optional[Call] = None,
        handler: Optional[str] = None, question: Any = False,
        owner_commands: tuple[str, ...] = ()) -> OperationDescriptor:
    """One Programs verb as a descriptor (``method``: the ProgramService method it reaches)."""
    if question:
        from holdspeak.principals import PrincipalKind
        from holdspeak.services.program_definitions import ProgramRefused

        def guarded(target: Call, *, command: bool) -> Call:
            def invoke(service: Any, principal: Any, args: dict[str, Any]) -> Any:
                needs_binding = question(args) if callable(question) else question
                owner_command = command and owner_commands and getattr(principal, "kind", None) is PrincipalKind.OWNER
                if needs_binding and authority == AUTHORITY and getattr(principal, "kind", None) is not PrincipalKind.OWNER:
                    service._require_owner(principal, "answer this question")
                if needs_binding and args.get("binding") is None and not owner_command:
                    raise ProgramRefused("answer_stale", "This question changed. Read it again.", status=409)
                return target(service, principal, args)
            return invoke

        web = guarded(web or call, command=False)
        call = guarded(call, command=True)
    exposure = ((f"http:{http[0]} {http[1]}",) if http else ()) + ((f"mcp:{name}",) if schema is not None else ())
    return OperationDescriptor(
        name=name, version=1, description=description or f"The Programs verb {name} (HTTP only).",
        args_schema=_ANY_OBJECT, principal=_PRINCIPAL + (f"; unbound owner commands: {', '.join(owner_commands)}; internal rule dispatch" if owner_commands else ""), effect="read" if thread == READ else "write",
        result="the ProgramService answer (a Program wire, a list, or the verb's own shape)",
        refusals=_REFUSALS, completion="the answer; each change is also a program_changed frame",
        exposure=exposure, service="program_service", method=method or _METHODS[name], announces_changes=True,
        call=call, web_call=web, http=http, http_status=status,
        handler=handler or "api_programs_" + name.split(".", 1)[1], tool_schema=schema,
        authority=authority, thread=thread, question_binding=bool(question),
    )


_ID = {"type": "string", "minLength": 1, "maxLength": 128}
_RUNS_ON = {
    "profile": {"type": ["string", "null"], "description": "Runs on: claude-default (Claude Code), codex-default (Codex) or pi-default (pi)."},
    "engine": {"type": ["string", "null"], "description": "For pi only: an engine profile id of the model library (model_library.get). Empty: the desk's engine for coding work."},
    "prefer_idle": {"type": ["boolean", "null"], "description": "pi only: start the step only when its engine is idle (a foreground use always wins)."},
}
#: PG19: Runs on as an ordered list: the first runs the role, the rest take
#: the step over at a usage limit.
_RUNS_ON_LIST = {"type": ["array", "null"], "maxItems": 4, "items": {"anyOf": [
    {"type": "string"},
    {"type": "object", "properties": {"profile": {"type": "string"}, "engine": {"type": ["string", "null"]}},
     "required": ["profile"], "additionalProperties": False},
]}, "description": "The agents in order (claude-default, codex-default, pi-default with an engine). The first runs "
                   "it; the next takes over when one stops at its usage limit."}
_HANDOFF = {
    "runs_on": _RUNS_ON_LIST,
    "allowed_profiles": {"type": ["array", "null"], "items": {"type": "string"},
                         "description": "The agents that may read this repository. Empty: every agent."},
    "may_handoff": {"type": ["boolean", "null"], "description": "Normal: hand off on its own after 10 minutes at a limit."},
    "usage_warning_share": {"type": ["number", "null"], "minimum": 0, "maximum": 1,
                            "description": "Hand off at a turn end once a harness reports this share of its window (0.9). Off by default."},
}

_STEP = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "brief": {"type": "string", "maxLength": 12000},
        "owns": {"type": "array", "items": {"type": "string"}, "description": "The files this step owns."},
        "after": {"type": "array", "items": {"type": "integer", "minimum": 1}, "description": "The step numbers it waits for."},
        **_RUNS_ON,
        "runs_on": _RUNS_ON_LIST,
        "effort": {"type": ["string", "null"], "enum": ["low", "medium", "high", None]},
        "race": {"type": ["integer", "null"], "minimum": 0, "maximum": 3, "description": "2 or 3: that many agents race on it."},
        "gate_check": {"type": ["boolean", "null"]},
        "gate_review": {"type": ["string", "boolean", "null"], "description": "none, agent (the Program's reviewer) or person (for_person_id reviews the PR on GitHub)."},
        "review_depth": {"type": ["string", "null"], "enum": ["glance", "delta", "standard", None]},
        "gate_merge": {"type": ["string", "null"], "enum": ["owner", "auto", "none", None]},
        "origin_ref": {"type": ["string", "null"], "description": "The desk item it came from (action:<id>): its merge closes it."},
        "for_person_id": {"type": ["string", "null"], "description": "The person this step is owed to (a People id)."},
        "may_call": {"type": ["boolean", "null"], "description": "The engine may call the owner's phone about this step where the Reach rules allow it."},
        "no_diff_ok": {"type": ["boolean", "null"], "description": "The step may end with no change (else a step that writes nothing goes back to its agent)."},
        "kind": {"type": ["string", "null"], "enum": ["agent", "prompt", "desk", None],
                 "description": "agent (default): an agent in a worktree. prompt: one model call on the engine "
                                "assigned to automations, with no repository; the brief is the call, the answer "
                                "is the step's report. desk: the brief is a JSON list of {op, args} display requests; "
                                "only mark, say and scroll. No repository or agent. The step waits for each Desk answer."},
        "deliver": {"type": ["string", "null"], "maxLength": 200,
                    "description": "A prompt step: where the answer goes: inbox (default), needs_you, today, "
                                   "destination:<id> (prepared; he presses Send) or project_updates:<project id>."},
        "sources": {"type": ["array", "null"], "items": {"type": "string", "maxLength": 200}, "maxItems": 50,
                    "description": "A prompt step: what it is about (note:<id>, meetings:this_week, person:<id>, ...)."},
        "history": {
            "type": ["object", "null"],
            "description": "A step that merged already (PG17): it is written Merged with this PR and merge time; "
                           "no agent runs it. A Program of only history steps is Done.",
            "properties": {
                "pr_number": {"type": "integer", "minimum": 1},
                "pr_url": {"type": ["string", "null"], "maxLength": 400},
                "merged_at": {"type": "string", "description": "The merge time (ISO 8601)."},
                "head_commit": {"type": ["string", "null"], "maxLength": 64},
            },
            "required": ["pr_number", "merged_at"],
            "additionalProperties": False,
        },
    },
    "required": ["title"],
    "additionalProperties": False,
}


#: PG15: a Program by its id or by the words he said.
_BY_NAME = {
    "program_id": {"type": ["string", "null"], "maxLength": 128},
    "name": {"type": ["string", "null"], "maxLength": 200,
             "description": "Words of the Program's title or its template (fast-cycle, build-and-review, race, "
                            "from-the-desk, overnight)."},
}


def _schema(properties: dict[str, Any], required: list[str], *, held: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {**(held or {}), "type": "object", "properties": properties, "required": required, "additionalProperties": False}


_SPEC = {"type": ["object", "null"], "additionalProperties": False, "properties": {
    "command": {"type": "string", "maxLength": 2000, "description": "Check: the command HoldSpeak runs on the step's commit."},
    "expect": {"type": "string", "maxLength": 400, "description": "Check: a pattern one line of the log must match."},
    "case": {"type": "string", "maxLength": 200, "description": "Shot: the desk sweep case (the window)."},
    "width": {"type": "integer", "enum": [393, 1440]},
    "metric": {"type": "string", "maxLength": 80, "description": "Measure: the name the log prints the number with (p95)."},
    "op": {"type": "string", "enum": ["<", "<=", ">", ">=", "="]},
    "bound": {"type": "number", "description": "Measure: the number the value must meet."},
    "unit": {"type": "string", "maxLength": 20, "description": "Measure: ms, s, min, MB, ..."},
    "walk": {"type": "array", "items": {"type": "string", "maxLength": 400}, "maxItems": 30,
             "description": "Your word: the steps the owner will do (a walk)."},
}}
_TOKENS = {"type": ["integer", "string", "null"], "description": "A context budget in tokens: 65536 or \"64k\"."}
#: PG-REQ §8: the step fields program.step_update takes.
_STEP_UPDATE = {
    "title": {"type": "string", "minLength": 1, "maxLength": 200},
    "brief": {"type": "string", "maxLength": 12000},
    "owns": {"type": "array", "items": {"type": "string"}},
    "after": {"type": "array", "items": {"type": "integer", "minimum": 1}},
    **_RUNS_ON,
    "runs_on": _RUNS_ON_LIST,
    "effort": {"type": "string", "enum": ["low", "medium", "high"]},
    "race": {"type": "integer", "minimum": 0, "maximum": 3},
    "gate_check": {"type": "boolean"},
    "gate_review": {"type": ["string", "boolean"]},
    "review_depth": {"type": "string", "enum": ["glance", "delta", "standard"]},
    "gate_merge": {"type": "string", "enum": ["level", "owner", "auto", "none"],
                   "description": "level (the Control level decides), owner (his press) or none (no PR)."},
    "for_person_id": {"type": ["string", "null"]},
    "may_call": {"type": "boolean"},
    "prefer_idle": {"type": "boolean", "description": "Start it only when its engine is idle (Planned or Ready steps)."},
    "budget_tokens": _TOKENS,
    "before": {"type": ["string", "null"], "description": "Move it before this step id (\"end\": to the end). Planned or Ready steps only."},
}


_CREATE_FIELDS = (
    "title", "goal", "repository", "project_id", "base_branch", "control", "check_command", "template",
    "default_profile", "default_engine", "reviewer_profile", "reviewer_engine", "prefer_idle", "origin_ref",
    "for_person_id", "spend_limit_usd", "runs_on", "allowed_profiles", "may_handoff", "usage_warning_share", "may_call",
    "steps",
)
_UPDATE_FIELDS = (
    "title", "goal", "control", "prefer_idle", "project_id", "spend_limit_usd", "default_profile", "default_engine",
    "reviewer_profile", "reviewer_engine", "runs_on", "allowed_profiles", "may_handoff", "usage_warning_share", "may_call",
    # PG-LANG: the fields the Program text writes.
    "review_depth", "planner_engine", "budget_tokens", "night", "within", "delivery", "rounds_before_start",
    "check_command", "for_person_id",
)
_STEP_IDS = ("program_id", "step_id")


def _pid(a: Mapping[str, Any]) -> str:
    return str(a["program_id"])


def _sid(a: Mapping[str, Any]) -> str:
    return str(a["step_id"])


def _templates(_s: Any, _p: Any, _a: dict[str, Any]) -> dict[str, Any]:
    from holdspeak.program_templates import TEMPLATES

    return {"templates": [{key: template[key] for key in ("id", "name", "description")} for template in TEMPLATES]}


def _create(s: Any, p: Any, a: dict[str, Any]) -> Any:
    args = {key: a.get(key) for key in _CREATE_FIELDS if key in a}
    args.setdefault("title", "")
    return s.create(p, **args)


def _by_name(start: bool) -> Call:
    """PG15: ``program.start`` and ``program.get`` by id or by his words.

    By ``name`` (a call says "the overnight program"), no match and a start of
    a Program that runs already are answers, not errors: ``spoken`` says what
    is so, and nothing starts. By ``program_id`` alone the refusals stay.
    Each answer carries ``spoken``: the state in one or two sentences."""

    def call(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        from holdspeak.services.program_definitions import ProgramRefused, spoken_state

        def said(wire: dict[str, Any], **more: Any) -> dict[str, Any]:
            return {**wire, **more, "spoken": spoken_state(wire)}

        by_name = bool(str(args.get("name") or "").strip())
        try:
            found = service.find(principal, program_id=args.get("program_id"), name=args.get("name"), startable=start)
        except ProgramRefused as refused:
            if by_name and refused.code == "program_not_found":
                return {"found": False, "started": False, "spoken": refused.detail}
            raise
        if not start:
            return said(service.get(principal, str(found["id"])))
        if by_name and found.get("state") not in ("drafting", "parked"):
            return said(service.get(principal, str(found["id"])), started=False)
        return said(service.start(principal, str(found["id"])), started=True)

    return call


def _decide(s: Any, p: Any, a: dict[str, Any]) -> Any:
    return s.decide(
        p, _pid(a), str(a.get("step_id") or ""), kind=str(a.get("kind") or ""), choice=str(a.get("choice") or ""),
        finding_id=a.get("finding_id"), reason=a.get("reason"), requirement_id=a.get("requirement_id"),
        proposal_id=a.get("proposal_id"), via=a.get("via"),
        expected_delivery_checkpoint_id=a.get("expected_delivery_checkpoint_id"), binding=a.get("binding"),
        expected_commit_binding=a.get("expected_commit_binding"),
    )


def _decide_web(s: Any, p: Any, a: dict[str, Any]) -> Any:
    return s.decide(
        p, _pid(a), _sid(a), kind=str(a.get("kind") or ""), choice=str(a.get("choice") or ""),
        finding_id=a.get("finding_id"), reason=a.get("reason"), via=a.get("via"),
        proposal_id=a.get("proposal_id", a.get("lesson_id")),  # The identity of the proposal or lesson.
        # HS-S32: a delivery press names the delivery line it answers.
        expected_delivery_checkpoint_id=a.get("expected_delivery_checkpoint_id"), binding=a.get("binding"),
        expected_commit_binding=a.get("expected_commit_binding"),
    )


def _require(s: Any, p: Any, a: dict[str, Any]) -> Any:
    return s.require(p, _pid(a), **{key: value for key, value in a.items() if key != "program_id" and value is not None})


def _require_web(s: Any, p: Any, a: dict[str, Any]) -> Any:
    keys = ("text", "kind", "step_id", "each_step", "required", "spec")
    return s.require(p, _pid(a), **{key: a[key] for key in keys if key in a})


def _text(s: Any, p: Any, a: dict[str, Any]) -> Any:
    found = s.find(p, program_id=a.get("program_id"), name=a.get("name"))
    return s.text_get(p, str(found["id"]))


def _text_preview(a: Mapping[str, Any]) -> bool:
    dry = a.get("dry_run") if a.get("dry_run") is not None else a.get("preview")
    return dry is not False


def _text_apply(s: Any, p: Any, a: dict[str, Any]) -> Any:
    return s.text_apply(p, _pid(a), a.get("text"), dry_run=_text_preview(a), base=a.get("base"),
                        allow_lower=list(a.get("allow_lower") or []), binding=a.get("binding"), proposal_id=a.get("proposal_id"))


def _text_apply_web(s: Any, p: Any, a: dict[str, Any]) -> Any:
    allow = a.get("allow_lower") if isinstance(a.get("allow_lower"), list) else []
    return s.text_apply(p, _pid(a), a.get("text"), dry_run=_text_preview(a), base=a.get("base"),
                        allow_lower=[str(item) for item in allow], binding=a.get("binding"), proposal_id=a.get("proposal_id"))


def _pending(a: Mapping[str, Any]) -> Optional[str]:
    return a.get("pending") if isinstance(a.get("pending"), str) else None


def _shape(s: Any, p: Any, a: dict[str, Any]) -> Any:
    from holdspeak.services.program_definitions import ProgramRefused

    try:
        found = s.find(p, program_id=a.get("program_id"), name=a.get("name"))
    except ProgramRefused as refused:
        if str(a.get("name") or "").strip() and refused.code == "program_not_found":
            said = " ".join(str(a.get("name")).split())
            return {"found": False, "applied": False, "spoken": f"There is no program with the name {said}. Nothing changed."}
        raise
    # LANG5: on a call his spoken answer to the read back runs here.
    from holdspeak.services import program_spoken

    held = program_spoken.take(found["id"], a.get("sentence"))
    if held is not None:
        return program_spoken.run(s, p, held)
    return s.shape(p, str(found["id"]), a.get("sentence"), apply=a.get("apply") is True, pending=_pending(a), binding=a.get("binding"))


def _round(s: Any, p: Any, a: dict[str, Any]) -> Any:
    return s.round(p, _pid(a), a.get("action"), round_name=a.get("round"), answer_text=a.get("answer"),
                   choice=a.get("choice"), question_id=a.get("question_id"), names=a.get("names"),
                   apply=a.get("apply") is True, binding=a.get("binding"))


def _names(a: Mapping[str, Any]) -> Optional[list[Any]]:
    return a.get("names") if isinstance(a.get("names"), list) else None


def _round_answer(s: Any, p: Any, a: dict[str, Any]) -> Any:
    """The face's answer press: ``skip`` and ``not_this`` are their own actions."""
    qid = str(a["question_id"]) if a.get("question_id") else None
    action = "skip_question" if a.get("skip") is True else "not_this" if a.get("not_this") is True else "answer"
    return s.round(p, _pid(a), action, round_name=a["name"], answer_text=a.get("answer"), choice=a.get("option"),
                   question_id=qid if action != "not_this" else (qid or ""), apply=a.get("apply") is True, binding=a.get("binding"))


def _round_decide(s: Any, p: Any, a: dict[str, Any]) -> Any:
    """Done with, Skip round, Ask more: the round's own three choices only."""
    from holdspeak.services.program_rounds import _refused

    choice = str(a.get("choice") or "").strip().lower()
    if choice not in ("done", "skip", "reopen"):
        raise _refused("bad_choice", "Choose done, skip or reopen.", status=400)
    return s.round(p, _pid(a), choice, round_name=a["name"], binding=a.get("binding"))


def _requirement_edit(s: Any, p: Any, a: dict[str, Any]) -> Any:
    """His edit: only the fields the body names change (``required`` too)."""
    fields = {key: a[key] for key in ("text", "kind", "required", "spec") if key in a}
    return s.require(p, _pid(a), requirement_id=str(a["requirement_id"]), **fields)


#: Any proposal kind reaches ``decide_proposal``; the proposal's own row names its kind.
_PROPOSAL = "requirement_proposed"


def _schema(properties: dict[str, Any], required: list[str], *, held: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {**(held or {}), "type": "object", "properties": properties, "required": required, "additionalProperties": False}


_STEP_REF = _schema({"program_id": _ID, "step_id": _ID}, ["program_id", "step_id"])
_PROGRAM_REF = _schema({"program_id": _ID}, ["program_id"])
_P = _op

#: The Programs verbs, in HTTP mount order (the recorded route list keeps it),
#: then the MCP-only verbs. The MCP tools list in this order too.
PROGRAM_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _P("program.list", lambda s, p, a: s.list(p, q=a.get("q"), project_id=a.get("project_id"), person_id=a.get("person_id")),
       ("GET", "/api/programs"), thread=READ,
       description="List the Programs, waiting first. q: words every row must have (title, goal, project, person, "
                   "step titles, #PR, template); project_id and person_id narrow the rows.",
       schema=_schema({"q": {"type": ["string", "null"], "maxLength": 200},
                       "project_id": {"type": ["string", "null"]},
                       "person_id": {"type": ["string", "null"]}}, [])),
    _P("program.templates", _templates, ("GET", "/api/programs/templates"), thread=READ,
       description="List the Program templates: id, name and description (fast-cycle, build-and-review, race, "
                   "from-the-desk, overnight, dreaming, audit). program.create takes the id as template.",
       schema=_schema({}, [])),
    _P("program.create", _create, ("POST", "/api/programs"), status=201,
       description="Make a Program: a goal cut into steps, each handed to an agent in its own worktree, checked by a "
                   "verified log, reviewed, and merged on his press at Secure or by the engine at Normal and YOLO (only core questions reach him). Name a "
                   "repository path or a project_id (its repository); a Program of only prompt steps needs none. "
                   "It starts in Drafting.",
       schema=_schema({
           "title": {"type": "string", "minLength": 1, "maxLength": 200},
           "goal": {"type": "string", "maxLength": 12000},
           "repository": {"type": ["string", "null"], "description": "A local git folder."},
           "project_id": {"type": ["string", "null"]},
           "base_branch": {"type": ["string", "null"]},
           "control": {"type": ["string", "null"], "enum": ["secure", "normal", "yolo", None],
                       "description": "The Control level: Secure (he merges and decides), Normal, YOLO (hands off). "
                                      "Default: the desk's Control mode. Core questions reach him at every level."},
           "check_command": {"type": ["string", "null"], "description": "Default: .holdspeak/program.json, else scripts/quick_check.sh."},
           "template": {"type": ["string", "null"], "description": "fast-cycle, build-and-review, race, from-the-desk, overnight, dreaming or audit."},
           "default_profile": _RUNS_ON["profile"], "default_engine": _RUNS_ON["engine"],
           "reviewer_profile": _RUNS_ON["profile"], "reviewer_engine": _RUNS_ON["engine"],
           "prefer_idle": _RUNS_ON["prefer_idle"],
           "origin_ref": {"type": ["string", "null"], "description": "What started it: meeting:<id>, decision:<id>, note:<id>, project_item:<id>."},
           "for_person_id": {"type": ["string", "null"]},
           "spend_limit_usd": {"type": ["number", "null"], "minimum": 0,
                               "description": "The most a paid engine may cost; unset: any spend is his question."},
           "may_call": {"type": ["boolean", "null"],
                        "description": "The engine may call the owner's phone (not only message it) where the Reach rules allow it. Default off; on in overnight."},
           "steps": {"type": ["array", "null"], "items": _STEP,
                     "description": "The steps, written at once. A Program of only prompt steps needs no repository."},
           **_HANDOFF,
       }, ["title"])),
    _P("program.from_action", lambda s, p, a: s.from_action(p, a.get("action_id"), project_id=a.get("project_id")),
       ("POST", "/api/programs/from-action"), status=201,
       description="Make a Program in Drafting from one open action of a Project: its title, its Project's "
                   "repository, and its person when the action has one owner. It is never started here.",
       schema=_schema({"action_id": _ID, "project_id": {"type": ["string", "null"]}}, ["action_id"])),
    _P("program.add_to_night",
       lambda s, p, a: s.add_to_night(p, kind=a.get("kind"), item_id=a.get("item_id"), line=a.get("line"),
                                      program_id=a.get("program_id")),
       ("POST", "/api/programs/tonight"),
       description="Add one item to tonight's dreaming program (the one Program with a night line, or program_id): "
                   "a Door task (kind action), a note line (kind note, with line) or a step of another Program "
                   "(kind program_step). It becomes a Planned step; at the night's start the planner cuts it into "
                   "one tiny step inside the program's bounds. The same item twice is one step. The owner's add "
                   "lands at once; an orchestrating agent's lands at YOLO only (Decided for you, Overturn).",
       schema=_schema({
           "kind": {"type": "string", "enum": ["action", "note", "program_step"]},
           "item_id": _ID,
           "line": {"type": ["string", "null"], "maxLength": 1000, "description": "kind note: the note line."},
           "program_id": {"type": ["string", "null"], "maxLength": 128,
                          "description": "The night Program; empty: the one Program with a night line."},
       }, ["kind", "item_id"])),
    _P("program.get", _by_name(start=False), ("GET", "/api/programs/{program_id}"), thread=READ,
       web=lambda s, p, a: s.get(p, _pid(a)),
       description="Read one Program, by program_id or by name: its steps (state, agent, engine, check, review, PR), "
                   "its checkpoints (each with the hidden ref it pinned the step's worktree to, ref and ref_commit), "
                   "what waits on the owner, and spoken (its state in one or two sentences to say on a call).",
       schema=_schema(_BY_NAME, [])),
    _P("program.update", lambda s, p, a: s.update(p, _pid(a), **{key: a[key] for key in _UPDATE_FIELDS if key in a}),
       ("PATCH", "/api/programs/{program_id}"),
       description="Change a Program: title, goal, Control level (secure, normal, yolo), when idle, its Project "
                   "(file an unfiled Program), the spend limit, the default and reviewer Runs on (reviewer_profile "
                   "\"none\": no reviewer), the review depth, the planner engine, the context budget, the night "
                   "(\"23:30–07:00 · at most 8 steps\"), within (the paths it may own), delivery (\"dw "
                   "<project>/<phase>\"; only where the repository has Delivery Workbench), rounds before start, "
                   "the check command (\"none\": no check) and the person it is for. null clears a field.",
       schema=_schema({
           "program_id": _ID, "title": {"type": ["string", "null"], "maxLength": 200},
           "goal": {"type": ["string", "null"], "maxLength": 12000},
           "control": {"type": ["string", "null"], "enum": ["secure", "normal", "yolo", None]},
           "prefer_idle": _RUNS_ON["prefer_idle"], "project_id": {"type": ["string", "null"]},
           "spend_limit_usd": {"type": ["number", "null"], "minimum": 0},
           "default_profile": _RUNS_ON["profile"], "default_engine": _RUNS_ON["engine"],
           "reviewer_profile": _RUNS_ON["profile"], "reviewer_engine": _RUNS_ON["engine"],
           "may_call": {"type": ["boolean", "null"]},
           **_HANDOFF,
           "review_depth": {"type": ["string", "null"], "enum": ["glance", "delta", "standard", None]},
           "planner_engine": {"type": ["string", "null"], "description": "An engine of the model library that plans."},
           "budget_tokens": _TOKENS,
           "night": {"type": ["string", "object", "null"], "description": "\"23:30–07:00 · at most 8 steps\", or "
                                                                       "{start, end, max_steps}."},
           "within": {"type": ["array", "null"], "items": {"type": "string"}},
           "delivery": {"type": ["string", "null"], "description": "\"dw <project>/<phase>[/<story>]\"; null: off."},
           "rounds_before_start": {"type": ["boolean", "null"]},
           "check_command": {"type": ["string", "null"], "maxLength": 2000},
           "for_person_id": {"type": ["string", "null"]},
       }, ["program_id"])),
    _P("program.plan",
       lambda s, p, a: s.plan(p, _pid(a), steps=a.get("steps") if isinstance(a.get("steps"), list) else [],
                              size=a.get("size"), replace=bool(a.get("replace")), before=a.get("before") or None,
                              waits=a.get("waits") is not False),
       ("POST", "/api/programs/{program_id}/plan"),
       description="Replace or append a Program's steps. size auto sets each step's effort by rule (more than 12 "
                   "files or a refactor: high; one file and one paragraph: low). A step with history (pr_number, "
                   "merged_at) is work that merged already: it is written Merged and no agent runs it.",
       schema=_schema({
           "program_id": _ID, "steps": {"type": "array", "items": _STEP},
           "size": {"type": ["string", "null"], "enum": ["auto", None]}, "replace": {"type": ["boolean", "null"]},
           "before": {"type": ["string", "null"], "description": "Insert the steps before this Planned or Ready step id."},
           "waits": {"type": ["boolean", "null"], "description": "With before: that step also comes after the new ones (default true)."},
       }, ["program_id", "steps"])),
    _P("program.start", _by_name(start=True), ("POST", "/api/programs/{program_id}/start"),
       web=lambda s, p, a: s.start(p, _pid(a)),
       description="Start a Program: its ready steps are handed to agents. Name it by program_id, or by name (words "
                   "of its title or its template, \"overnight\"). It never makes a Program.",
       schema=_schema(_BY_NAME, [], held=held_arguments("Start a Program",
           named(["program_id", "name"], "Program", "program.get", {"program_id": "program_id", "name": "name"}, "title"),
           named(["program_id", "name"], "Where", "program.get", {"program_id": "program_id", "name": "name"}, "repository.label")))),
    _P("program.park", lambda s, p, a: s.park(p, _pid(a), reason=a.get("reason"), binding=a.get("binding"), note=a.get("note")),
       ("POST", "/api/programs/{program_id}/park"), question=True,
       description="Park a Program. The worktrees stay; Resume brings it back. reason (optional): proof (a run that "
                   "proved the engine) or done-with-it; the list folds such a row (parked_as).",
       schema=_schema({"program_id": _ID, "binding": _ANSWER_BINDING, "note": {"type": ["string", "null"], "maxLength": 2000}, "reason": {"type": ["string", "null"],
                                                     "enum": ["proof", "done-with-it", "done_with_it", None]}},
                      ["program_id"])),
    _P("program.resume", lambda s, p, a: s.resume(p, _pid(a)), ("POST", "/api/programs/{program_id}/resume"),
       description="Resume a parked Program.", schema=_PROGRAM_REF),
    _P("program.decide", _decide, ("POST", "/api/programs/{program_id}/steps/{step_id}/decide"),
       authority=AUTHORITY, web=_decide_web, question=True, owner_commands=("program_decide", "requirement commands"),
       description="The owner's decision on a step: a merge (merge, not_yet), the agent's held commit (commit: allow, not_now), a finding (fix_now, later, skip), a "
                   "parked step (resume, skip), a person review (prepare: a send is prepared, he presses Send), "
                   "an agent at its usage limit (limited: continue, wait), a requirement (requirement with "
                   "requirement_id: met, unmet, waive with reason, send_back), what an agent proposed "
                   "(proposal_id: requirement_proposed add or skip, step_change apply or skip, step_amend send or skip; "
                   "a split of a step too big for its budget is a step_change: apply splits it, skip runs it as it is), "
                   "the delivery at Done (delivery, no step_id: retry, merge, check, skip, with "
                   "expected_delivery_checkpoint_id from the row). A commit requires expected_commit_binding from the shown row. Owner only.",
       schema=_schema({
           "program_id": _ID, "step_id": {"type": ["string", "null"], "maxLength": 128},
           "kind": {"type": "string", "enum": ["merge", "finding", "parked", "ask_review", "core", "race", "add_step", "close",
                                               "limited", "commit", "requirement", "requirement_proposed", "step_change", "step_amend",
                                               "delivery"]},
           "choice": {"type": "string"}, "finding_id": {"type": ["string", "null"]},
           "reason": {"type": ["string", "null"], "maxLength": 400},
           "requirement_id": {"type": ["string", "null"]},
           "proposal_id": {"type": ["string", "integer", "null"]},
           "via": {"type": ["string", "null"], "enum": ["desk", "phone", "call", "telegram", "page", None],
                   "description": "Where he answered (desk by default); the ledger line names it."},
           "binding": _ANSWER_BINDING,
           "expected_commit_binding": {"type": "object", "properties": {"hold_id": {"type": ["string", "null"]},
                "change_revision": {"type": "string"}}, "required": ["hold_id", "change_revision"], "additionalProperties": False},
           "expected_delivery_checkpoint_id": {"type": ["integer", "null"],
                                               "description": "A delivery: the row's delivery line (required)."},
       }, ["program_id", "kind", "choice"], held=held_arguments("Answer a Program",
           named("program_id", "Program", "program.get", {"program_id": "program_id"}, "title"),
           hidden("step_id", "Step"), text("kind", "Question"), text("choice", "Answer"), text("reason", "Reason"),
           hidden("finding_id", "Finding"), hidden("requirement_id", "Requirement"), hidden("proposal_id", "Proposal"),
           text("via", "Through"), hidden("binding", "Saved revision", "token"),
           hidden("expected_commit_binding", "Commit revision", "token"),
           hidden("expected_delivery_checkpoint_id", "Delivery revision", "token")))),
    _P("program.race", lambda s, p, a: s.race(p, _pid(a), _sid(a), int(a.get("n") or 0)),
       ("POST", "/api/programs/{program_id}/steps/{step_id}/race"),
       description="Make a step that has not started a race: n agents (2 or 3) do the same step, each in its own "
                   "worktree. The owner's change applies at once; an orchestrating agent's follows the Control level.",
       schema=_schema({"program_id": _ID, "step_id": _ID, "n": {"type": "integer", "minimum": 2, "maximum": 3}},
                      ["program_id", "step_id", "n"])),
    _P("program.handoff",
       lambda s, p, a: s.handoff(p, _pid(a), _sid(a), a.get("to"), preview=bool(a.get("preview"))),
       ("POST", "/api/programs/{program_id}/steps/{step_id}/handoff"), authority=AUTHORITY, thread=None,
       description="Move a step that holds an agent to another agent, in the same worktree on the same branch, with "
                   "HoldSpeak's handoff brief as its first message. preview true returns the brief, what was redacted "
                   "and the earlier turns, and moves nothing. Owner only.",
       schema=_schema({
           "program_id": _ID, "step_id": _ID,
           "to": {"anyOf": [{"type": "string"}, {"type": "object", "properties": {
               "profile": {"type": "string"}, "engine": {"type": ["string", "null"]}}, "required": ["profile"],
               "additionalProperties": False}]},
           "preview": {"type": ["boolean", "null"]},
       }, ["program_id", "step_id", "to"])),
    _P("program.start_from", lambda s, p, a: s.start_from(p, _pid(a), a["checkpoint_id"], binding=a.get("binding")),
       ("POST", "/api/programs/{program_id}/checkpoints/{checkpoint_id}/start-from"), question=True,
       description="Start a new step from a checkpoint: its worktree starts at the checkpoint's pinned ref "
                   "(refs/holdspeak/checkpoints/<step>/<n>, in program.get's checkpoints), with the source step's "
                   "brief and agent. The owner's call adds the step. The step's own agent may ask: at YOLO the "
                   "step is added and listed under Decided for you; at Secure and Normal the owner decides.",
       schema=_schema({"program_id": _ID, "binding": _ANSWER_BINDING, "checkpoint_id": {"type": ["string", "integer"]}},
                      ["program_id", "checkpoint_id"])),
    _P("program.overturn", lambda s, p, a: s.overturn(p, _pid(a), a["decision_id"]),
       ("POST", "/api/programs/{program_id}/decisions/{decision_id}/overturn"), authority=AUTHORITY, thread=None,
       description="Undo one of the engine's decisions (Decided for you) while it can still be undone: a Later task, "
                   "a Skip, a parked step, an added step. Never a merge. Owner only.",
       schema=_schema({"program_id": _ID, "decision_id": {"type": ["string", "integer"]}},
                      ["program_id", "decision_id"])),
    _P("program.step_update",
       lambda s, p, a: s.change_step(p, _pid(a), _sid(a), **{k: v for k, v in a.items() if k not in _STEP_IDS}),
       ("PATCH", "/api/programs/{program_id}/steps/{step_id}"), handler="api_programs_step_change",
       description="Change a step: the fields its state leaves open (a Planned step: all; a started step: title, "
                   "the agents after the first, raise the review to agent, merge level or owner, the person; an "
                   "open PR: title, merge, the person). before moves a Planned or Ready step; numbers follow the "
                   "order. A frozen field is refused with its reason (step_frozen). The owner's change applies at "
                   "once; an orchestrating agent's goes to the owner at Secure and Normal, YOLO applies it.",
       schema=_schema({"program_id": _ID, "step_id": _ID, **_STEP_UPDATE}, ["program_id", "step_id"])),
    _P("program.step_take", lambda s, p, a: s.take_over(p, _pid(a), _sid(a)),
       ("POST", "/api/programs/{program_id}/steps/{step_id}/take"), authority=AUTHORITY, thread=None,
       description="Take over the running lane of a step: the owner types to its agent, and the engine waits. "
                   "program.step_hand_back gives the lane back. Owner only.",
       schema=_STEP_REF),
    _P("program.step_hand_back", lambda s, p, a: s.hand_back(p, _pid(a), _sid(a)),
       ("POST", "/api/programs/{program_id}/steps/{step_id}/hand-back"), authority=AUTHORITY, thread=None,
       description="Give a lane that the owner took over back to the engine. Owner only.",
       schema=_STEP_REF),
    _P("program.amend", lambda s, p, a: s.amend(p, _pid(a), _sid(a), a.get("line")),
       ("POST", "/api/programs/{program_id}/steps/{step_id}/amend"), handler="api_programs_step_amend",
       description="Add one line to a started step's brief. HoldSpeak types it to the step's agent at its next turn "
                   "boundary (never into a blocked agent); the first brief stays as it was. The owner's line goes "
                   "at once; an orchestrating agent's goes to the owner at Secure and Normal, YOLO sends it.",
       schema=_schema({"program_id": _ID, "step_id": _ID, "line": {"type": "string", "minLength": 1, "maxLength": 1000}},
                      ["program_id", "step_id", "line"])),
    _P("program.require", _require, ("POST", "/api/programs/{program_id}/requirements"), status=201, web=_require_web,
       description="Add one requirement: one sentence the owner wants true, on the Program (judged after the last "
                   "step), on every step (each_step), or on one step (step_id). kind: check (a command, in "
                   "backticks or spec.command), review (the step's reviewer answers REQ Rn: MET or UNMET), shot "
                   "(spec.case and spec.width, 393 or 1440), word (the owner presses Met; spec.walk lists his "
                   "steps), measure (spec.command and a bound: metric, op, bound, unit; HoldSpeak runs it at CHECK "
                   "and the last line naming the metric gives the value, judged against the bound). No kind: the rule "
                   "guesses it. An agent's requirement is a proposal: at YOLO it is added and listed under "
                   "Decided for you; at Secure and Normal the owner adds or skips it. With requirement_id it "
                   "changes one (the owner only). No tool marks a requirement met.",
       schema=_schema({
           "program_id": _ID, "text": {"type": ["string", "null"], "maxLength": 400},
           "kind": {"type": ["string", "null"], "enum": ["check", "review", "shot", "word", "measure", None]},
           "step_id": {"type": ["string", "null"]}, "each_step": {"type": ["boolean", "null"]},
           "required": {"type": ["boolean", "null"]}, "spec": _SPEC,
           "requirement_id": {"type": ["string", "null"]},
       }, ["program_id"])),
    # 2026-11-09 (one entry per verb): his edit, his press on a requirement or a
    # proposal and his Close enter the service where program.require and
    # program.decide do (require with requirement_id; decide with the kind), so
    # the route and the tool reach one method with one argument rule.
    _P("program.requirement_edit", _requirement_edit,
       ("PATCH", "/api/programs/{program_id}/requirements/{requirement_id}"), method="require"),
    _P("program.requirement_decide",
       lambda s, p, a: s.decide(p, _pid(a), str(a["binding"].get("step_id") or "") if isinstance(a.get("binding"), Mapping) else "", kind="requirement", choice=str(a.get("choice") or ""),
                                requirement_id=str(a["requirement_id"]), reason=a.get("line"), binding=a.get("binding")),
       ("POST", "/api/programs/{program_id}/requirements/{requirement_id}/decide"), authority=AUTHORITY, question=True,
       method="decide"),
    _P("program.proposal_decide",
       lambda s, p, a: s.decide(p, _pid(a), "", kind=_PROPOSAL, choice=str(a.get("choice") or ""),
                                proposal_id=str(a["proposal_id"]), binding=a.get("binding")),
       ("POST", "/api/programs/{program_id}/proposals/{proposal_id}/decide"), authority=AUTHORITY, question=True,
       method="decide"),
    _P("program.requirement_evidence", lambda s, p, a: s.requirement_evidence(p, _pid(a), str(a["requirement_id"])),
       ("GET", "/api/programs/{program_id}/requirements/{requirement_id}/evidence"), thread=READ,
       description="Read the evidence of one requirement: the check's log, the shot, the review's line or the "
                   "measured value the engine judged it by, with its verdict.",
       schema=_schema({"program_id": _ID, "requirement_id": _ID}, ["program_id", "requirement_id"])),
    _P("program.text", _text, ("GET", "/api/programs/{program_id}/text"), thread=READ,
       web=lambda s, p, a: s.text_get(p, _pid(a)),
       description="Read one Program as its text (PG-LANG §3): one statement per line, the steps with their briefs, "
                   "agents, gates and requirements; the run is in lamps after '#' (never read back). Defaults are not "
                   "written. revision is the Program's revision. By program_id or by name, as program.get.",
       schema=_schema(_BY_NAME, [])),
    _P("program.text_apply", _text_apply, ("POST", "/api/programs/{program_id}/text"), web=_text_apply_web, question=lambda a: not _text_preview(a),
       description="Change a Program by its text: give the whole changed text (from program.text). dry_run true (the "
                   "default) writes nothing and returns the change rows: op, where, field, before, after, verdict "
                   "(allowed, refused with code and reason, conflict, lowers) and lowers_bar; allowed_text is your text "
                   "with every refused change put back. dry_run false applies only when no row is refused or in "
                   "conflict, and a row that lowers the bar only when its id is in allow_lower (the owner only). An "
                   "agent's lower gate on a Planned step goes to the owner as a proposal (proposed); any other "
                   "lower bar from an agent is refused (owner_required). A new step is 'step +', a new requirement 'R+'; a started step takes a line with '+'. base: the text you read, "
                   "so a field changed since then is a conflict. Never write 'waived'.",
       schema=_schema({
           "program_id": _ID, "binding": _ANSWER_BINDING, "proposal_id": {"type": "string"}, "text": {"type": "string", "minLength": 1, "maxLength": 200000},
           "dry_run": {"type": ["boolean", "null"], "description": "Default true: preview only."},
           "preview": {"type": ["boolean", "null"], "description": "The same as dry_run (PG-LANG §12)."},
           "base": {"type": ["string", "null"], "maxLength": 200000},
           "allow_lower": {"type": ["array", "null"], "items": {"type": "string"},
                           "description": "The owner only: ids of the rows that lower the bar that may apply."},
       }, ["program_id", "text"])),
    _P("program.shape_engine", lambda s, p, a: s.shape_engine(p, _pid(a)), ("GET", "/api/programs/{program_id}/shape"),
       thread=READ,
       description="Read which engine shapes this Program (program.shape, program.plan_draft): {engine, capability}, "
                   "or null when no engine is set.",
       schema=_PROGRAM_REF),
    _P("program.shape", _shape, ("POST", "/api/programs/{program_id}/shape"),
       web=lambda s, p, a: s.shape(p, _pid(a), a.get("sentence"), apply=a.get("apply") is True, pending=_pending(a), binding=a.get("binding")),
       description="Change a Program by one sentence (PG-LANG §4): the hub sends the sentence and the Program's text "
                   "to the planning engine (agent.plan) in one call, diffs the engine's whole text against the "
                   "current text and returns the change rows as program.text_apply does, with say, engine and "
                   "latency_ms. Nothing is written: apply with program.text_apply (text: allowed_text or "
                   "proposed_text, base: base). apply true applies the allowed rows at once only at YOLO and "
                   "lists them under Decided for you (Overturn); a row that lowers the bar or is a core question "
                   "never applies here. The engine never waives. On a call (LANG5): name the Program by its words "
                   "(name) and give his sentence; the call reads the changes back and waits for his spoken yes; "
                   "say the answer's spoken line.",
       schema=_schema({
           **_BY_NAME, "binding": _ANSWER_BINDING, "sentence": {"type": "string", "minLength": 1, "maxLength": 1000},
           "apply": {"type": ["boolean", "null"], "description": "At YOLO only: apply the allowed rows at once."},
           "pending": {"type": ["string", "null"], "maxLength": 200000,
                       "description": "The proposed_text of rows that wait: the engine reads it, so this sentence "
                                      "adds to them."},
       }, ["sentence"], held=held_arguments("Change a Program",
           named(["program_id", "name"], "Program", "program.get", {"program_id": "program_id", "name": "name"}, "title"),
           text("sentence", "Change"), text("apply", "Apply"), hidden("pending", "Pending text"),
           hidden("binding", "Saved revision", "token")))),
    _P("program.shape_held_drop", lambda s, p, a: s.drop_held_shape(p, _pid(a)),
       ("DELETE", "/api/programs/{program_id}/shape/held"),
       description="Not this: drop the change rows that a shaping call left waiting on this Program. Nothing else "
                   "changes.",
       schema=_PROGRAM_REF),
    _P("program.plan_draft",
       lambda s, p, a: s.plan_draft(p, _pid(a), goal=a.get("goal"), template=a.get("template"),
                                    budget=a.get("budget"), text=a.get("text"), split=a.get("split")),
       ("POST", "/api/programs/{program_id}/plan/draft"),
       description="Draft a Program in Drafting from its goal (PG-LANG §5): the hub sends the goal (or the Note it "
                   "came from), the template's shape, the repository map, the Project's open actions and the budget "
                   "to the planning engine (agent.plan) in one call, and returns the whole drafted text as change "
                   "rows as program.text_apply does (each row source 'plan'; an added step has its size, "
                   "'18k of 32k'; a step over the working share is 'step_too_big' after one split). Nothing is "
                   "written: apply with program.text_apply (text: proposed_text, base: base). To split one step "
                   "of a draft: text (the draft) and split (the step's place).",
       schema=_schema({
           "program_id": _ID, "goal": {"type": ["string", "null"], "maxLength": 8000},
           "template": {"type": ["string", "null"]},
           "budget": {"type": ["string", "integer", "null"], "description": "The builder's context: 64k or 65536."},
           "text": {"type": ["string", "null"], "maxLength": 200000},
           "split": {"type": ["integer", "null"], "description": "With text: the place of the step to split."},
       }, ["program_id"])),
    _P("program.plan_programs", lambda s, p, a: s.apply_programs(p, _pid(a), a.get("programs"), a.get("which", "all")),
       ("POST", "/api/programs/{program_id}/plan/programs"),
       description="Apply a draft that proposes more than one Program (program.plan_draft's programs): which all "
                   "applies each; a place (0, 1, ...) applies that one. The first is this Program; each other is a "
                   "new Program in Drafting that starts after the one before it is Done. Drafting only.",
       schema=_schema({
           "program_id": _ID,
           "programs": {"type": "array", "items": {"type": "object"}, "minItems": 1,
                        "description": "The proposed programs of the draft, each with its text."},
           "which": {"type": ["string", "integer"], "description": "all, or the place of one program."},
       }, ["program_id", "programs"])),
    # 2026-11-09: the rounds' presses enter where program.round does (one
    # service verb, ``program_rounds.act``); the four per-press methods are parked.
    _P("program.rounds_open", lambda s, p, a: s.round(p, _pid(a), "open", names=_names(a)),
       ("POST", "/api/programs/{program_id}/rounds"), method="round"),
    _P("program.round_next", lambda s, p, a: s.round(p, _pid(a), "next", round_name=a["name"]),
       ("POST", "/api/programs/{program_id}/rounds/{name}/next"), method="round"),
    _P("program.round_answer", _round_answer, ("POST", "/api/programs/{program_id}/rounds/{name}/answer"),
       method="round", question=True),
    _P("program.round_decide", _round_decide, ("POST", "/api/programs/{program_id}/rounds/{name}/decide"),
       method="round", question=True),
    _P("program.close", lambda s, p, a: s.decide(p, _pid(a), "", kind="close", choice="", binding=a.get("binding")),
       ("POST", "/api/programs/{program_id}/close"), authority=AUTHORITY, method="decide", question=True),
    # MCP only: the step's own agent, the audit's fix and the rounds as one tool.
    _P("program.propose_fix", lambda s, p, a: s.propose_fix(p, _pid(a)),
       description="From an audit Program (template audit), make a fix Program in Drafting: one step per MUST "
                   "finding, each with a Review requirement that it is fixed, linked to the audit. It is never "
                   "started here.",
       schema=_PROGRAM_REF),
    _P("program.step_remove", lambda s, p, a: s.remove_step(p, _pid(a), _sid(a), binding=a.get("binding")),
       ("DELETE", "/api/programs/{program_id}/steps/{step_id}"), question=True,
       description="Remove a Planned or Ready step. The numbers follow the order again; a step that came after it "
                   "comes after what it came after. A started step stays (step_stays). The owner's removal applies "
                   "at once; an orchestrating agent's goes to the owner at Secure and Normal, YOLO removes it.",
       schema=_schema({"program_id": _ID, "step_id": _ID, "binding": _ANSWER_BINDING}, ["program_id", "step_id"])),
    _P("program.round", _round, question=lambda a: a.get("action") in ("answer", "skip_question", "not_this", "done", "skip", "reopen"),
       description="The interview rounds of a Program (PG-LANG §6.2): Architecture, Product, Stack, Verification, "
                   "Delivery by default. action 'open' makes the rounds (names to choose others); 'next' asks the "
                   "planning engine for the ONE next question of a round that would change the plan "
                   "({question: {id, text, why, choices}} or done); 'answer' stores the answer (answer, or one of "
                   "the choices as choice) and returns the change rows it implies as program.text_apply does "
                   "(source 'round:<name>'; apply them with program.text_apply); 'skip_question', 'not_this' (the "
                   "rows were dismissed), 'done' (withheld while a question waits), 'skip' (the round) and "
                   "'reopen' (ask more). Rounds never gate Start.",
       schema=_schema({
           "program_id": _ID,
           "action": {"type": "string", "enum": ["open", "next", "answer", "skip_question", "not_this", "done", "skip",
                                                 "reopen"]},
           "round": {"type": ["string", "null"], "maxLength": 40},
           "answer": {"type": ["string", "null"], "maxLength": 300},
           "choice": {"type": ["string", "null"], "maxLength": 80},
           "binding": _ANSWER_BINDING, "question_id": {"type": ["string", "null"]},
           "names": {"type": ["array", "null"], "items": {"type": "string", "maxLength": 40}, "maxItems": 12},
           "apply": {"type": ["boolean", "null"], "description": "At YOLO, the owner only: apply the allowed rows."},
       }, ["program_id", "action"])),
    _P("program.checkpoint",
       lambda s, p, a: s.checkpoint(p, a.get("program_id"), _sid(a), str(a.get("line") or "")),
       description="Write one line on your step at a meaningful moment. Only the step's own agent (or the owner).",
       schema=_schema({"step_id": _ID, "line": {"type": "string", "minLength": 1, "maxLength": 400},
                       "program_id": {"type": ["string", "null"]}}, ["step_id", "line"])),
    _P("program.step_done",
       lambda s, p, a: s.step_done(p, a.get("program_id"), _sid(a), str(a.get("report") or ""),
                                   follow_ups=list(a.get("follow_ups") or [])),
       description="Say your step is done, with your report (files changed, what you left out, the check log path). "
                   "HoldSpeak still waits for the commit on your branch.",
       schema=_schema({"step_id": _ID, "report": {"type": "string", "maxLength": 20000},
                       "program_id": {"type": ["string", "null"]},
                       "follow_ups": {"type": ["array", "null"], "items": {"type": "string"},
                                      "description": "Steps the plan lacks (YOLO adds them; else the owner decides)."}},
                      ["step_id", "report"])),
)

#: An MCP tool name -> its operation (each tool is its own operation).
TOOL_OPERATIONS: dict[str, str] = {op.name: op.name for op in PROGRAM_OPERATIONS if op.tool_schema is not None}


class _LiveProgramService:
    """The bound target: the process's one ProgramService, read at each call
    (``default_program_service``), so a rebuilt database or a test's own
    service is the one the call reaches."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.services.program_service import default_program_service

        return getattr(default_program_service(), name)


LIVE_PROGRAM_SERVICE = _LiveProgramService()

__all__ = ["LIVE_PROGRAM_SERVICE", "PROGRAM_OPERATIONS", "TOOL_OPERATIONS"]
