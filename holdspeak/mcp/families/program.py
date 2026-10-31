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
- ``program.start_from`` (PG20): the owner (the step is added) or the step's
  own launch (the ladder decides: Secure and Normal ask him, YOLO adds it);
- ``program.decide``, ``program.overturn`` and ``program.handoff`` (PG19): the owner only (AUTHORITY in ``tool_authority.py``,
  never in the CONDUCTOR palette).
- PG-REQ (2026-10-31): ``program.require`` (add a requirement, or his edit
  of one), ``program.step_update`` (change a step, move it) and
  ``program.amend`` (a line added to a started step's brief): his at once;
  an orchestrating agent's (and, for ``program.require``, a step's own
  agent's) by the Control level. No tool says a requirement is met: the
  engine judges it, or he presses (``program.decide`` kind ``requirement``).
- PG-LANG LANG1 (2026-10-31): ``program.text`` (anyone) reads a Program as
  its text; ``program.text_apply`` previews a changed text as change rows
  (allowed, refused by name, conflict, lowers the bar) and, with
  ``dry_run`` false, applies it through the verbs above, so each change
  keeps its own authority rule. A row that lowers the bar applies only when
  its id is in ``allow_lower``.
- PG-LANG LANG6 (2026-10-31): ``program.plan_draft`` drafts a Program in
  Drafting from its goal, as change rows (``program_planner``).
- PG-LANG LANG9 (2026-10-31): ``program.round`` runs the interview rounds
  (``program_rounds``): open, next (one question), answer (the shaped rows
  wait for Apply), skip_question, done, skip, reopen. An agent's answer is a
  proposal: only the owner's lands at YOLO.
- PG-LANG LANG3 (2026-10-31): ``program.shape`` turns one sentence into the
  same change rows through one planning-engine call; it writes nothing,
  except at YOLO with ``apply`` (the allowed rows, one Decided for you row).
- PG-LANG fields (2026-10-31): ``program.update`` writes the review depth,
  the planner, the budget, the night, within, delivery, rounds before start,
  the check and the person (``reviewer_profile: "none"`` takes the reviewer
  off); ``program.step_remove`` removes a Planned step (the text's removed
  block); ``program.require`` takes ``measure`` and a word's ``walk``.
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


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


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
                    "files or a refactor: high; one file and one paragraph: low). A step with history (pr_number, "
                    "merged_at) is work that merged already: it is written Merged and no agent runs it.",
     "inputSchema": _schema({
         "program_id": _ID, "steps": {"type": "array", "items": _STEP},
         "size": {"type": ["string", "null"], "enum": ["auto", None]}, "replace": {"type": ["boolean", "null"]},
         "before": {"type": ["string", "null"], "description": "Insert the steps before this Planned or Ready step id."},
         "waits": {"type": ["boolean", "null"], "description": "With before: that step also comes after the new ones (default true)."},
     }, ["program_id", "steps"])},
    {"name": "program.update",
     "description": "Change a Program: title, goal, Control level (secure, normal, yolo), when idle, its Project "
                    "(file an unfiled Program), the spend limit, the default and reviewer Runs on (reviewer_profile "
                    "\"none\": no reviewer), the review depth, the planner engine, the context budget, the night "
                    "(\"23:30–07:00 · at most 8 steps\"), within (the paths it may own), delivery (\"dw "
                    "<project>/<phase>\"; only where the repository has Delivery Workbench), rounds before start, "
                    "the check command (\"none\": no check) and the person it is for. null clears a field.",
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
     }, ["program_id"])},
    {"name": "program.start", "description": "Start a Program: its ready steps are handed to agents. Name it by "
                                            "program_id, or by name (words of its title or its template, "
                                            "\"overnight\"). It never makes a Program.",
     "inputSchema": _schema(_BY_NAME, [])},
    {"name": "program.park", "description": "Park a Program. The worktrees stay; Resume brings it back.",
     "inputSchema": _schema({"program_id": _ID}, ["program_id"])},
    {"name": "program.resume", "description": "Resume a parked Program.",
     "inputSchema": _schema({"program_id": _ID}, ["program_id"])},
    {"name": "program.get",
     "description": "Read one Program, by program_id or by name: its steps (state, agent, engine, check, review, PR), "
                    "its checkpoints (each with the hidden ref it pinned the step's worktree to, ref and ref_commit), "
                    "what waits on the owner, and spoken (its state in one or two sentences to say on a call).",
     "inputSchema": _schema(_BY_NAME, [])},
    {"name": "program.list", "description": "List the Programs, waiting first. q: words every row must have "
                                           "(title, goal, project, person, step titles, #PR, template); "
                                           "project_id and person_id narrow the rows.",
     "inputSchema": _schema({"q": {"type": ["string", "null"], "maxLength": 200},
                             "project_id": {"type": ["string", "null"]},
                             "person_id": {"type": ["string", "null"]}}, [])},
    {"name": "program.require",
     "description": "Add one requirement: one sentence the owner wants true, on the Program (judged after the last "
                    "step), on every step (each_step), or on one step (step_id). kind: check (a command, in "
                    "backticks or spec.command), review (the step's reviewer answers REQ Rn: MET or UNMET), shot "
                    "(spec.case and spec.width, 393 or 1440), word (the owner presses Met; spec.walk lists his "
                    "steps), measure (spec.command and a bound: metric, op, bound, unit; it stays Not measured yet "
                    "until its verifier exists and does not hold a merge). No kind: the rule "
                    "guesses it. An agent's requirement is a proposal: at YOLO it is added and listed under "
                    "Decided for you; at Secure and Normal the owner adds or skips it. With requirement_id it "
                    "changes one (the owner only). No tool marks a requirement met.",
     "inputSchema": _schema({
         "program_id": _ID, "text": {"type": ["string", "null"], "maxLength": 400},
         "kind": {"type": ["string", "null"], "enum": ["check", "review", "shot", "word", "measure", None]},
         "step_id": {"type": ["string", "null"]}, "each_step": {"type": ["boolean", "null"]},
         "required": {"type": ["boolean", "null"]}, "spec": _SPEC,
         "requirement_id": {"type": ["string", "null"]},
     }, ["program_id"])},
    {"name": "program.step_update",
     "description": "Change a step: the fields its state leaves open (a Planned step: all; a started step: title, "
                    "the agents after the first, raise the review to agent, merge level or owner, the person; an "
                    "open PR: title, merge, the person). before moves a Planned or Ready step; numbers follow the "
                    "order. A frozen field is refused with its reason (step_frozen). The owner's change applies at "
                    "once; an orchestrating agent's goes to the owner at Secure and Normal, YOLO applies it.",
     "inputSchema": _schema({"program_id": _ID, "step_id": _ID, **_STEP_UPDATE}, ["program_id", "step_id"])},
    {"name": "program.step_remove",
     "description": "Remove a Planned or Ready step. The numbers follow the order again; a step that came after it "
                    "comes after what it came after. A started step stays (step_stays). The owner's removal applies "
                    "at once; an orchestrating agent's goes to the owner at Secure and Normal, YOLO removes it.",
     "inputSchema": _schema({"program_id": _ID, "step_id": _ID}, ["program_id", "step_id"])},
    {"name": "program.amend",
     "description": "Add one line to a started step's brief. HoldSpeak types it to the step's agent at its next turn "
                    "boundary (never into a blocked agent); the first brief stays as it was. The owner's line goes "
                    "at once; an orchestrating agent's goes to the owner at Secure and Normal, YOLO sends it.",
     "inputSchema": _schema({"program_id": _ID, "step_id": _ID, "line": {"type": "string", "minLength": 1, "maxLength": 1000}},
                            ["program_id", "step_id", "line"])},
    {"name": "program.text",
     "description": "Read one Program as its text (PG-LANG §3): one statement per line, the steps with their briefs, "
                    "agents, gates and requirements; the run is in lamps after '#' (never read back). Defaults are not "
                    "written. revision is the Program's revision. By program_id or by name, as program.get.",
     "inputSchema": _schema(_BY_NAME, [])},
    {"name": "program.text_apply",
     "description": "Change a Program by its text: give the whole changed text (from program.text). dry_run true (the "
                    "default) writes nothing and returns the change rows: op, where, field, before, after, verdict "
                    "(allowed, refused with code and reason, conflict, lowers) and lowers_bar; allowed_text is your text "
                    "with every refused change put back. dry_run false applies only when no row is refused or in "
                    "conflict, and a row that lowers the bar only when its id is in allow_lower. A new step is "
                    "'step +', a new requirement 'R+'; a started step takes a line with '+'. base: the text you read, "
                    "so a field changed since then is a conflict. Never write 'waived'.",
     "inputSchema": _schema({
         "program_id": _ID, "text": {"type": "string", "minLength": 1, "maxLength": 200000},
         "dry_run": {"type": ["boolean", "null"], "description": "Default true: preview only."},
         "preview": {"type": ["boolean", "null"], "description": "The same as dry_run (PG-LANG §12)."},
         "base": {"type": ["string", "null"], "maxLength": 200000},
         "allow_lower": {"type": ["array", "null"], "items": {"type": "string"},
                         "description": "Ids of the rows that lower the bar that may apply."},
     }, ["program_id", "text"])},
    {"name": "program.shape",
     "description": "Change a Program by one sentence (PG-LANG §4): the hub sends the sentence and the Program's text "
                    "to the planning engine (agent.plan) in one call, diffs the engine's whole text against the "
                    "current text and returns the change rows as program.text_apply does, with say, engine and "
                    "latency_ms. Nothing is written: apply with program.text_apply (text: allowed_text or "
                    "proposed_text, base: base). apply true applies the allowed rows at once only at YOLO and "
                    "lists them under Decided for you (Overturn); a row that lowers the bar or is a core question "
                    "never applies here. The engine never waives. On a call (LANG5): name the Program by its words "
                    "(name) and give his sentence; the call reads the changes back and waits for his spoken yes; "
                    "say the answer's spoken line.",
     "inputSchema": _schema({
         **_BY_NAME, "sentence": {"type": "string", "minLength": 1, "maxLength": 1000},
         "apply": {"type": ["boolean", "null"], "description": "At YOLO only: apply the allowed rows at once."},
         "pending": {"type": ["string", "null"], "maxLength": 200000,
                     "description": "The proposed_text of rows that wait: the engine reads it, so this sentence "
                                    "adds to them."},
     }, ["sentence"])},
    {"name": "program.plan_draft",
     "description": "Draft a Program in Drafting from its goal (PG-LANG §5): the hub sends the goal (or the Note it "
                    "came from), the template's shape, the repository map, the Project's open actions and the budget "
                    "to the planning engine (agent.plan) in one call, and returns the whole drafted text as change "
                    "rows as program.text_apply does (each row source 'plan'; an added step has its size, "
                    "'18k of 32k'; a step over the working share is 'step_too_big' after one split). Nothing is "
                    "written: apply with program.text_apply (text: proposed_text, base: base). To split one step "
                    "of a draft: text (the draft) and split (the step's place).",
     "inputSchema": _schema({
         "program_id": _ID, "goal": {"type": ["string", "null"], "maxLength": 8000},
         "template": {"type": ["string", "null"]},
         "budget": {"type": ["string", "integer", "null"], "description": "The builder's context: 64k or 65536."},
         "text": {"type": ["string", "null"], "maxLength": 200000},
         "split": {"type": ["integer", "null"], "description": "With text: the place of the step to split."},
     }, ["program_id"])},
    {"name": "program.round",
     "description": "The interview rounds of a Program (PG-LANG §6.2): Architecture, Product, Stack, Verification, "
                    "Delivery by default. action 'open' makes the rounds (names to choose others); 'next' asks the "
                    "planning engine for the ONE next question of a round that would change the plan "
                    "({question: {id, text, why, choices}} or done); 'answer' stores the answer (answer, or one of "
                    "the choices as choice) and returns the change rows it implies as program.text_apply does "
                    "(source 'round:<name>'; apply them with program.text_apply); 'skip_question', 'not_this' (the "
                    "rows were dismissed), 'done' (withheld while a question waits), 'skip' (the round) and "
                    "'reopen' (ask more). Rounds never gate Start.",
     "inputSchema": _schema({
         "program_id": _ID,
         "action": {"type": "string", "enum": ["open", "next", "answer", "skip_question", "not_this", "done", "skip",
                                               "reopen"]},
         "round": {"type": ["string", "null"], "maxLength": 40},
         "answer": {"type": ["string", "null"], "maxLength": 300},
         "choice": {"type": ["string", "null"], "maxLength": 80},
         "question_id": {"type": ["string", "null"]},
         "names": {"type": ["array", "null"], "items": {"type": "string", "maxLength": 40}, "maxItems": 12},
         "apply": {"type": ["boolean", "null"], "description": "At YOLO, the owner only: apply the allowed rows."},
     }, ["program_id", "action"])},
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
     "description": "The owner's decision on a step: a merge (merge, not_yet), the agent's held commit (commit: allow, not_now), a finding (fix_now, later, skip), a "
                    "parked step (resume, skip), a person review (prepare: a send is prepared, he presses Send), "
                    "an agent at its usage limit (limited: continue, wait), a requirement (requirement with "
                    "requirement_id: met, unmet, waive with reason, send_back), what an agent proposed "
                    "(proposal_id: requirement_proposed add or skip, step_change apply or skip, step_amend send or skip). "
                    "Owner only.",
     "inputSchema": _schema({
         "program_id": _ID, "step_id": {"type": ["string", "null"], "maxLength": 128},
         "kind": {"type": "string", "enum": ["merge", "finding", "parked", "ask_review", "core", "race", "add_step", "close",
                                             "limited", "requirement", "requirement_proposed", "step_change", "step_amend"]},
         "choice": {"type": "string"}, "finding_id": {"type": ["string", "null"]},
         "reason": {"type": ["string", "null"], "maxLength": 400},
         "requirement_id": {"type": ["string", "null"]},
         "proposal_id": {"type": ["string", "integer", "null"]},
         "via": {"type": ["string", "null"], "enum": ["desk", "phone", "call", "telegram", "page", None],
                 "description": "Where he answered (desk by default); the ledger line names it."},
     }, ["program_id", "kind", "choice"])},
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
    {"name": "program.start_from",
     "description": "Start a new step from a checkpoint: its worktree starts at the checkpoint's pinned ref "
                    "(refs/holdspeak/checkpoints/<step>/<n>, in program.get's checkpoints), with the source step's "
                    "brief and agent. The owner's call adds the step. The step's own agent may ask: at YOLO the "
                    "step is added and listed under Decided for you; at Secure and Normal the owner decides.",
     "inputSchema": _schema({"program_id": _ID, "checkpoint_id": {"type": ["string", "integer"]}},
                            ["program_id", "checkpoint_id"])},
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
                            size=args.get("size"), replace=bool(args.get("replace")), before=args.get("before") or None,
                            waits=args.get("waits") is not False)
    if name == "program.require":
        program_id = str(args.pop("program_id"))
        return service.require(principal, program_id, **{key: value for key, value in args.items() if value is not None})
    if name == "program.step_update":
        program_id, step_id = str(args.pop("program_id")), str(args.pop("step_id"))
        return service.change_step(principal, program_id, step_id, **args)
    if name == "program.step_remove":
        return service.remove_step(principal, str(args["program_id"]), str(args["step_id"]))
    if name == "program.amend":
        return service.amend(principal, str(args["program_id"]), str(args["step_id"]), args.get("line"))
    if name == "program.update":
        program_id = str(args.pop("program_id"))
        return service.update(principal, program_id, **args)
    if name == "program.text":
        found = service.find(principal, program_id=args.get("program_id"), name=args.get("name"))
        return service.text_get(principal, str(found["id"]))
    if name == "program.text_apply":
        dry = args.get("dry_run") if args.get("dry_run") is not None else args.get("preview")
        return service.text_apply(principal, str(args["program_id"]), args.get("text"), dry_run=dry is not False,
                                  base=args.get("base"), allow_lower=list(args.get("allow_lower") or []))
    if name == "program.plan_draft":
        return service.plan_draft(principal, str(args["program_id"]), goal=args.get("goal"),
                                  template=args.get("template"), budget=args.get("budget"), text=args.get("text"),
                                  split=args.get("split"))
    if name == "program.round":
        return service.round(principal, str(args["program_id"]), args.get("action"), round_name=args.get("round"),
                             answer_text=args.get("answer"), choice=args.get("choice"),
                             question_id=args.get("question_id"), names=args.get("names"),
                             apply=args.get("apply") is True)
    if name == "program.shape":
        from holdspeak.services.program_service import ProgramRefused

        try:
            found = service.find(principal, program_id=args.get("program_id"), name=args.get("name"))
        except ProgramRefused as refused:
            if str(args.get("name") or "").strip() and refused.code == "program_not_found":
                said = " ".join(str(args.get("name")).split())
                return {"found": False, "applied": False,
                        "spoken": f"There is no program with the name {said}. Nothing changed."}
            raise
        # LANG5: on a call his spoken answer to the read back runs here.
        from holdspeak.services import program_spoken

        held = program_spoken.take(found["id"], args.get("sentence"))
        if held is not None:
            return program_spoken.run(service, principal, held)
        return service.shape(principal, str(found["id"]), args.get("sentence"), apply=args.get("apply") is True,
                             pending=args.get("pending") if isinstance(args.get("pending"), str) else None)
    if name in ("program.start", "program.get"):
        return _by_name(service, name, args, principal)
    if name == "program.park":
        return service.park(principal, str(args["program_id"]))
    if name == "program.resume":
        return service.resume(principal, str(args["program_id"]))
    if name == "program.list":
        return service.list(principal, q=args.get("q"), project_id=args.get("project_id"), person_id=args.get("person_id"))
    if name == "program.checkpoint":
        return service.checkpoint(principal, args.get("program_id"), str(args["step_id"]), str(args.get("line") or ""))
    if name == "program.step_done":
        return service.step_done(principal, args.get("program_id"), str(args["step_id"]), str(args.get("report") or ""),
                                 follow_ups=list(args.get("follow_ups") or []))
    if name == "program.overturn":
        return service.overturn(principal, str(args["program_id"]), args["decision_id"])
    if name == "program.start_from":
        return service.start_from(principal, str(args["program_id"]), args["checkpoint_id"])
    if name == "program.handoff":
        return service.handoff(principal, str(args["program_id"]), str(args["step_id"]), args.get("to"),
                               preview=bool(args.get("preview")))
    return service.decide(
        principal, str(args["program_id"]), str(args.get("step_id") or ""), kind=str(args.get("kind") or ""),
        choice=str(args.get("choice") or ""), finding_id=args.get("finding_id"), reason=args.get("reason"),
        requirement_id=args.get("requirement_id"), proposal_id=args.get("proposal_id"), via=args.get("via"),
    )


def _by_name(service: Any, name: str, args: dict[str, Any], principal: Principal) -> Any:
    """PG15: ``program.start`` and ``program.get`` by id or by his words.

    By ``name`` (a call says "the overnight program"), no match and a start of
    a Program that runs already are answers, not errors: ``spoken`` says what
    is so, and nothing starts. By ``program_id`` alone the refusals stay.
    Each answer carries ``spoken``: the state in one or two sentences."""
    from holdspeak.services.program_service import ProgramRefused, spoken_state

    def said(wire: dict[str, Any], **more: Any) -> dict[str, Any]:
        return {**wire, **more, "spoken": spoken_state(wire)}

    by_name = bool(str(args.get("name") or "").strip())
    start = name == "program.start"
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


__all__ = ["NAMES", "TOOLS", "dispatch"]
