"""What the Programs engine decides without him (design §6, "Control").

Owner, 2026-10-28: "every step or decision lands with me. No, absolutely not
... if those decisions relate to a core question, then yes, send them back
to me, but multiple levels of this, with YOLO really trying to be as hands
off as possible".

A Program's control is the desk's Control mode ladder: ``secure``,
``normal``, ``yolo``. :func:`decide` is the §6 table, row by row: for one
decision ``kind`` at one level it answers a :class:`Decision` (the engine
acts, under a named rule) or a :class:`CoreQuestion` (it goes to him).
:func:`is_core` is the list of core questions, which go to him at EVERY
level. Routine agent questions are not decided here: the desk's
``AgentResponder`` (ROUTINE class) types its draft under Normal and YOLO,
as built; this module answers only whether the level lets it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

LEVELS = ("secure", "normal", "yolo")
#: The desk's Control mode words -> the ladder (``Config.control_mode``).
DESK_MODES = {"safe": "secure", "secure": "secure", "neutral": "normal", "normal": "normal", "yolo": "yolo"}

#: Review rounds the builder gets for REQUIRED findings, and check rounds.
ROUNDS = {"secure": 2, "normal": 2, "yolo": 3}

KINDS = (
    "routine", "open_pr", "merge", "finding_required", "finding_should", "finding_note", "agent_question",
    "gate_approval", "check_failed", "step_failed", "race_winner", "add_step", "program_done",
)

_SECURITY = re.compile(r"\b(security|secur\w*|vulnerab\w*|injection|xss|csrf|secret|credential|token leak)\b", re.I)
_DATA_LOSS = re.compile(r"\b(data[- ]loss|loses? data|drops? (?:rows|data|the table)|deletes? (?:rows|user data)|corrupt\w*)\b", re.I)


@dataclass(frozen=True)
class Decision:
    """The engine acts: ``choice`` under ``rule``; ``overturnable`` when he
    can still undo it (a Later task, a Skip, a parked step, an added step;
    never a merge)."""

    choice: str
    rule: str
    overturnable: bool = False

    @property
    def to_owner(self) -> bool:
        return False


@dataclass(frozen=True)
class CoreQuestion:
    """It goes to him. ``core`` is True for a question on the core list
    (every level); False when only the level sends it to him."""

    reason: str
    rule: str
    core: bool = False

    @property
    def to_owner(self) -> bool:
        return True


Outcome = Union[Decision, CoreQuestion]


def level_of(value: Any) -> str:
    """A Program's control word on the ladder (default ``normal``)."""
    return DESK_MODES.get(str(value or "").strip().lower(), "normal")


def is_core(facts: Mapping[str, Any]) -> str:
    """The core question these facts raise, or ``""``. Each one goes to him
    at every level:

    - the goal: ``goal_change``;
    - the shape: ``outside_repo``, ``outside_owned`` (files);
    - egress beyond the PR: ``egress``;
    - money: ``spend_usd`` beyond ``spend_limit_usd``, or any spend when the
      limit is unset;
    - authority or config: ``authority``, ``config``, ``gate_hold``;
    - safety: a finding tagged security or data loss (``finding_text`` or
      ``finding_tags``), ``tests_deleted``, ``destructive_migration``;
    - no rule: ``no_rule``.
    """
    if facts.get("goal_change"):
        return "it would change the goal of the program"
    if facts.get("outside_repo"):
        return "it touches files outside the program's repository"
    outside = facts.get("outside_owned")
    if outside:
        names = ", ".join(list(outside)[:3]) if isinstance(outside, (list, tuple, set)) else ""
        return "it touches files no step owns" + (f" ({names})" if names else "")
    if facts.get("egress"):
        return "it would send something beyond the step's own PR"
    spend = facts.get("spend_usd")
    if spend is not None and float(spend or 0) > 0:
        limit = facts.get("spend_limit_usd")
        if limit is None:
            return "it spends money and the program has no spend limit"
        if float(spend) > float(limit):
            return f"it spends more than the program's limit of ${float(limit):.2f}"
    if facts.get("authority"):
        return "it changes who or what may act"
    if facts.get("config"):
        return "it changes the desk's settings"
    if facts.get("gate_hold"):
        return "the gate holds a tool call"
    tags = {str(tag).lower() for tag in facts.get("finding_tags") or []}
    text = str(facts.get("finding_text") or "")
    if "security" in tags or _SECURITY.search(text):
        return "a finding is about security"
    if "data-loss" in tags or "data_loss" in tags or _DATA_LOSS.search(text):
        return "a finding is about data loss"
    if facts.get("tests_deleted"):
        return "the change deletes tests"
    if facts.get("destructive_migration"):
        return "a migration drops or rewrites rows"
    if facts.get("no_rule"):
        return "the engine has no rule for this choice"
    return ""


def decide(level: Any, kind: str, facts: Optional[Mapping[str, Any]] = None) -> Outcome:
    """One row of the §6 table for ``kind`` at ``level``."""
    facts = dict(facts or {})
    level = level_of(level)
    core = is_core(facts)
    if core:
        return CoreQuestion(core, "a core question goes to the owner at every level", core=True)
    if kind not in KINDS:
        return CoreQuestion("the engine has no rule for this choice", "no rule", core=True)
    rounds = int(facts.get("round") or 0)
    if kind == "routine":
        return Decision("act", "the engine starts, re-briefs, checks, reviews and parks a lost racer at every level")
    if kind == "open_pr":
        return Decision("open", "a PR on the owner's own repository is work at every level")
    if kind == "merge":
        if not (facts.get("check_green") and facts.get("review_pass", True)):
            return CoreQuestion("the check is not green or the review did not pass", "no merge without green and PASS")
        if level == "secure":
            return CoreQuestion("Secure: he merges", "Secure: merge is his press")
        return Decision("merge", f"{level.capitalize()} merges on a green check and a passed review")
    if kind == "finding_required":
        allowed = ROUNDS[level]
        if rounds < allowed:
            return Decision("fix", f"a REQUIRED finding goes back to the builder (round {rounds + 1} of {allowed})")
        return CoreQuestion(f"REQUIRED findings are left after {allowed} rounds", f"{level.capitalize()}: {allowed} rounds, then him")
    if kind == "finding_should":
        if level == "secure":
            return CoreQuestion("Secure: he decides a SHOULD finding", "Secure: SHOULD findings are his")
        if level == "yolo" and facts.get("round_open"):
            return Decision("fix", "YOLO: a SHOULD finding is fixed while the builder's round is open")
        return Decision("later", f"{level.capitalize()}: a SHOULD finding becomes a Later task", overturnable=True)
    if kind == "finding_note":
        return Decision("skip", "a NOTE finding is skipped and logged", overturnable=True)
    if kind == "agent_question":
        if level == "secure":
            return CoreQuestion("Secure: he answers the agent", "Secure: agent questions are his")
        if facts.get("routine"):
            return Decision("type_draft", f"{level.capitalize()}: the desk's ROUTINE draft is typed (AgentResponder)")
        return CoreQuestion("the desk's draft is not routine", "a NON-ROUTINE draft waits for him", core=True)
    if kind == "gate_approval":
        if level == "secure":
            return CoreQuestion("Secure: he allows each held call", "Secure: approvals are his")
        if facts.get("gate_allows"):
            return Decision("allow", f"{level.capitalize()}: the gate allows a read, a build or a test by its own rules")
        return CoreQuestion("the gate holds the call", "authority stays with him", core=True)
    if kind == "check_failed":
        allowed = ROUNDS[level]
        if rounds < allowed:
            fresh = level == "yolo" and rounds + 1 == allowed
            return Decision("retry", f"a red check goes back to the builder (round {rounds + 1} of {allowed})"
                            + ("; YOLO's third round" if fresh else ""))
        return decide(level, "step_failed", {**facts, "round": rounds})
    if kind == "step_failed":
        if level == "secure":
            return CoreQuestion("Secure: a failed step is his", "Secure: failures are his")
        if level == "yolo" and not facts.get("replanned"):
            return Decision("replan", "YOLO: one re-plan of a failed step with a smaller brief")
        return Decision("park", f"{level.capitalize()}: a failed step is parked and the rest carries on", overturnable=True)
    if kind == "race_winner":
        if level == "secure":
            return CoreQuestion("Secure: he picks the race winner", "Secure: the winner is his pick")
        return Decision("pick", f"{level.capitalize()}: the first green, reviewed contender wins")
    if kind == "add_step":
        if level == "yolo":
            return Decision("add", "YOLO: the engine adds a missing step and says so", overturnable=True)
        return CoreQuestion(f"{level.capitalize()}: he adds a step the plan lacked", f"{level.capitalize()}: the plan is his")
    if kind == "program_done":
        if level == "secure":
            return CoreQuestion("Secure: he closes the program", "Secure: Done is his")
        return Decision("close", f"{level.capitalize()}: the engine closes a finished program")
    return CoreQuestion("the engine has no rule for this choice", "no rule", core=True)  # pragma: no cover


__all__ = ["CoreQuestion", "DESK_MODES", "Decision", "KINDS", "LEVELS", "ROUNDS", "decide", "is_core", "level_of"]
