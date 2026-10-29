"""Program family (2026-10-28, design §7): the Programs engine over MCP.

Every tool reaches the one service the REST routes use
(``services/program_service.default_program_service``). The authority rules
live in the service, so every transport keeps them:

- ``program.create`` / ``program.plan`` / ``program.start`` /
  ``program.park`` / ``program.resume``: the owner, or an orchestrating agent
  on a Program it created;
- ``program.get`` / ``program.list`` / ``program.templates``: anyone;
- ``program.checkpoint`` / ``program.step_done``: the step's own launch (by
  its credential) and, for checkpoints, the owner; any other caller is
  refused ``not_your_step``;
- ``program.decide``, ``program.overturn`` and ``program.handoff`` (PG19): the owner only (AUTHORITY in ``tool_authority.py``,
  never in the CONDUCTOR palette).
"""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal

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
    },
    "required": ["title"],
    "additionalProperties": False,
}


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


TOOLS: list[dict[str, Any]] = [
    {"name": "program.create",
     "description": "Make a Program: a goal cut into steps, each handed to an agent in its own worktree, checked by a "
                    "verified log, reviewed, and merged on his press at Secure or by the engine at Normal and YOLO (only core questions reach him). Name a "
                    "repository path or a project_id (its repository). It starts in Drafting.",
     "inputSchema": _schema({
         "title": {"type": "string", "minLength": 1, "maxLength": 200},
         "goal": {"type": "string", "maxLength": 12000},
         "repository": {"type": ["string", "null"], "description": "A local git folder."},
         "project_id": {"type": ["string", "null"]},
         "base_branch": {"type": ["string", "null"]},
         "control": {"type": ["string", "null"], "enum": ["secure", "normal", "yolo", None],
                     "description": "The Control level: Secure (he merges and decides), Normal, YOLO (hands off). "
                                    "Default: the desk's Control mode. Core questions reach him at every level."},
         "check_command": {"type": ["string", "null"], "description": "Default: .holdspeak/program.json, else scripts/quick_check.sh."},
         "template": {"type": ["string", "null"], "description": "fast-cycle, build-and-review, race, from-the-desk or overnight."},
         "default_profile": _RUNS_ON["profile"], "default_engine": _RUNS_ON["engine"],
         "reviewer_profile": _RUNS_ON["profile"], "reviewer_engine": _RUNS_ON["engine"],
         "prefer_idle": _RUNS_ON["prefer_idle"],
         "origin_ref": {"type": ["string", "null"], "description": "What started it: meeting:<id>, decision:<id>, note:<id>, project_item:<id>."},
         "for_person_id": {"type": ["string", "null"]},
         "spend_limit_usd": {"type": ["number", "null"], "minimum": 0,
                             "description": "The most a paid engine may cost; unset: any spend is his question."},
         "may_call": {"type": ["boolean", "null"],
                      "description": "The engine may call the owner's phone (not only message it) where the Reach rules allow it. Default off; on in overnight."},
         **_HANDOFF,
     }, ["title"])},
    {"name": "program.plan",
     "description": "Replace or append a Program's steps. size auto sets each step's effort by rule (more than 12 "
                    "files or a refactor: high; one file and one paragraph: low).",
     "inputSchema": _schema({
         "program_id": _ID, "steps": {"type": "array", "items": _STEP},
         "size": {"type": ["string", "null"], "enum": ["auto", None]}, "replace": {"type": ["boolean", "null"]},
     }, ["program_id", "steps"])},
    {"name": "program.update",
     "description": "Change a Program: title, goal, Control level (secure, normal, yolo), when idle, its Project "
                    "(file an unfiled Program), the spend limit, the default and reviewer Runs on.",
     "inputSchema": _schema({
         "program_id": _ID, "title": {"type": ["string", "null"], "maxLength": 200},
         "goal": {"type": ["string", "null"], "maxLength": 12000},
         "control": {"type": ["string", "null"], "enum": ["secure", "normal", "yolo", None]},
         "prefer_idle": _RUNS_ON["prefer_idle"], "project_id": {"type": ["string", "null"]},
         "spend_limit_usd": {"type": ["number", "null"], "minimum": 0},
         "default_profile": _RUNS_ON["profile"], "default_engine": _RUNS_ON["engine"],
         "reviewer_profile": _RUNS_ON["profile"], "reviewer_engine": _RUNS_ON["engine"],
         "may_call": {"type": ["boolean", "null"]},
         **_HANDOFF,
     }, ["program_id"])},
    {"name": "program.start", "description": "Start a Program: its ready steps are handed to agents.",
     "inputSchema": _schema({"program_id": _ID}, ["program_id"])},
    {"name": "program.park", "description": "Park a Program. The worktrees stay; Resume brings it back.",
     "inputSchema": _schema({"program_id": _ID}, ["program_id"])},
    {"name": "program.resume", "description": "Resume a parked Program.",
     "inputSchema": _schema({"program_id": _ID}, ["program_id"])},
    {"name": "program.get",
     "description": "Read one Program: its steps (state, agent, engine, check, review, PR), its checkpoints and what "
                    "waits on the owner.",
     "inputSchema": _schema({"program_id": _ID}, ["program_id"])},
    {"name": "program.list", "description": "List the Programs, waiting first.",
     "inputSchema": _schema({}, [])},
    {"name": "program.checkpoint",
     "description": "Write one line on your step at a meaningful moment. Only the step's own agent (or the owner).",
     "inputSchema": _schema({"step_id": _ID, "line": {"type": "string", "minLength": 1, "maxLength": 400},
                             "program_id": {"type": ["string", "null"]}}, ["step_id", "line"])},
    {"name": "program.step_done",
     "description": "Say your step is done, with your report (files changed, what you left out, the check log path). "
                    "HoldSpeak still waits for the commit on your branch.",
     "inputSchema": _schema({"step_id": _ID, "report": {"type": "string", "maxLength": 20000},
                             "program_id": {"type": ["string", "null"]},
                             "follow_ups": {"type": ["array", "null"], "items": {"type": "string"},
                                            "description": "Steps the plan lacks (YOLO adds them; else the owner decides)."}},
                            ["step_id", "report"])},
    {"name": "program.decide",
     "description": "The owner's decision on a step: a merge (merge, not_yet), a finding (fix_now, later, skip), a "
                    "parked step (resume, skip), a person review (prepare: a send is prepared, he presses Send), "
                    "an agent at its usage limit (limited: continue, wait). "
                    "Owner only.",
     "inputSchema": _schema({
         "program_id": _ID, "step_id": _ID,
         "kind": {"type": "string", "enum": ["merge", "finding", "parked", "ask_review", "core", "race", "add_step", "close",
                                             "limited"]},
         "choice": {"type": "string"}, "finding_id": {"type": ["string", "null"]},
         "reason": {"type": ["string", "null"], "maxLength": 400},
     }, ["program_id", "step_id", "kind", "choice"])},
    {"name": "program.handoff",
     "description": "Move a step that holds an agent to another agent, in the same worktree on the same branch, with "
                    "HoldSpeak's handoff brief as its first message. preview true returns the brief, what was redacted "
                    "and the earlier turns, and moves nothing. Owner only.",
     "inputSchema": _schema({
         "program_id": _ID, "step_id": _ID,
         "to": {"anyOf": [{"type": "string"}, {"type": "object", "properties": {
             "profile": {"type": "string"}, "engine": {"type": ["string", "null"]}}, "required": ["profile"],
             "additionalProperties": False}]},
         "preview": {"type": ["boolean", "null"]},
     }, ["program_id", "step_id", "to"])},
    {"name": "program.overturn",
     "description": "Undo one of the engine's decisions (Decided for you) while it can still be undone: a Later task, "
                    "a Skip, a parked step, an added step. Never a merge. Owner only.",
     "inputSchema": _schema({"program_id": _ID, "decision_id": {"type": ["string", "integer"]}},
                            ["program_id", "decision_id"])},
]

NAMES = frozenset(tool["name"] for tool in TOOLS)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call. Raises LookupError for unowned names."""
    if name not in NAMES:
        raise LookupError(name)
    from holdspeak.services.program_service import default_program_service

    service = default_program_service()
    args = dict(arguments or {})
    if name == "program.create":
        return service.create(principal, **{key: value for key, value in args.items()})
    if name == "program.plan":
        return service.plan(principal, str(args.get("program_id") or ""), steps=list(args.get("steps") or []),
                            size=args.get("size"), replace=bool(args.get("replace")))
    if name == "program.update":
        program_id = str(args.pop("program_id"))
        return service.update(principal, program_id, **args)
    if name == "program.start":
        return service.start(principal, str(args["program_id"]))
    if name == "program.park":
        return service.park(principal, str(args["program_id"]))
    if name == "program.resume":
        return service.resume(principal, str(args["program_id"]))
    if name == "program.get":
        return service.get(principal, str(args["program_id"]))
    if name == "program.list":
        return service.list(principal)
    if name == "program.checkpoint":
        return service.checkpoint(principal, args.get("program_id"), str(args["step_id"]), str(args.get("line") or ""))
    if name == "program.step_done":
        return service.step_done(principal, args.get("program_id"), str(args["step_id"]), str(args.get("report") or ""),
                                 follow_ups=list(args.get("follow_ups") or []))
    if name == "program.overturn":
        return service.overturn(principal, str(args["program_id"]), args["decision_id"])
    if name == "program.handoff":
        return service.handoff(principal, str(args["program_id"]), str(args["step_id"]), args.get("to"),
                               preview=bool(args.get("preview")))
    return service.decide(
        principal, str(args["program_id"]), str(args["step_id"]), kind=str(args.get("kind") or ""),
        choice=str(args.get("choice") or ""), finding_id=args.get("finding_id"), reason=args.get("reason"),
    )


__all__ = ["NAMES", "TOOLS", "dispatch"]
