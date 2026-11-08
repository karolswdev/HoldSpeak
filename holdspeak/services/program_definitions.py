"""The Program vocabulary and its one refusal (HS-S51, 2026-11-08).

The words every Program reader shares: the Program and step states, the
state machine of design §4, the your-turn kinds and their choices, the
control levels and their words, the proposal and to-do kinds, the frozen
field reasons; the one named refusal :class:`ProgramRefused`; and the pure
helpers that turn a row into words (``agent_label``, ``duration_words``,
``history_of``, ``triage_effort``, ``spoken_state``, ``via_of``).

One direction only: this module imports nothing from ``program_service``,
``program_runner`` or ``program_text``. ``program_service`` re-exports every
name here, so ``program_service.ProgramRefused is
program_definitions.ProgramRefused``. The runtime (the lock, the held flag,
the default service and runner, their caches) stays in the service.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Optional

from .errors import ServiceError
from .program_rules import LEVEL_WORDS

# ── vocabulary ───────────────────────────────────────────────────────

PROGRAM_STATES = ("drafting", "running", "waiting", "done", "parked", "failed")
STEP_STATES = (
    "planned", "ready", "briefed", "working", "waiting", "limited", "checking", "check_failed", "review",
    "findings", "pr_open", "merge_ask", "merged", "done", "parked", "failed",
)

#: The state machine of design §4: every move the engine or he may make.
STEP_TRANSITIONS: dict[str, frozenset[str]] = {
    "planned": frozenset({"ready", "parked"}),
    "ready": frozenset({"briefed", "planned", "parked"}),
    "briefed": frozenset({"working", "waiting", "limited", "checking", "parked", "failed"}),
    "working": frozenset({"briefed", "waiting", "limited", "checking", "parked", "failed"}),
    "waiting": frozenset({"briefed", "working", "limited", "checking", "parked", "failed"}),
    # PG19: the agent stopped at its usage limit; a handoff re-briefs the
    # step in the next agent (``briefed``), a reset lets it go on.
    "limited": frozenset({"briefed", "working", "waiting", "checking", "parked", "failed"}),
    "checking": frozenset({"review", "pr_open", "check_failed", "done", "parked", "failed"}),
    "check_failed": frozenset({"briefed", "working", "waiting", "limited", "checking", "parked", "failed"}),
    "review": frozenset({"pr_open", "findings", "checking", "done", "parked", "failed"}),
    "findings": frozenset({"review", "working", "checking", "pr_open", "done", "parked", "failed"}),
    # PG-REQ: a requirement added on the PR head is judged there (checking),
    # and his Send back or an Unmet word gives the builder one more round
    # on the same branch and PR (working).
    "pr_open": frozenset({"merge_ask", "merged", "parked", "failed", "checking", "working"}),
    "merge_ask": frozenset({"merged", "pr_open", "parked", "checking", "working"}),
    "merged": frozenset({"done"}),
    "done": frozenset(),
    # PG-REQ: a step parked with a requirement left goes on when he waives
    # it (checking) or sends it back (working).
    "parked": frozenset({"ready", "planned", "checking", "working"}),
    "failed": frozenset({"ready", "parked"}),
}

#: Why a Program was parked, when he says (``program.park reason``); the list
#: folds such a row (``parked_as``).
PARK_REASONS = {"proof": "a proof run", "done_with_it": "done with it"}
PARK_KIND = "program_park"

#: A step in one of these holds an agent (the board's live rows).
ACTIVE_STATES = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review", "findings"})
#: Finished: its dependents may run.
FINISHED_STATES = frozenset({"merged", "done"})
#: PG-IMPORT IMP2: how a step's lane ended, apart from its state ("none" is
#: no word: it runs, or nothing ended it).
ENDINGS = ("finished", "failed", "interrupted")
#: PG-IMPORT IMP1: the achromatic mark of a Done Program.
FINISHED_WORDS = {"finished": "finished", "needs_decision": "finished · needs a decision"}
#: Nothing more happens to it unless he says so.
CLOSED_STATES = frozenset({"merged", "done", "parked"})

#: The station track of the board (design §9): which station each state lights.
STATIONS = ("brief", "work", "check", "review", "pr", "merge")
_STATION_OF = {
    "planned": -1, "ready": -1, "briefed": 0, "working": 1, "waiting": 1, "limited": 1, "checking": 2,
    "check_failed": 2, "review": 3, "findings": 3, "pr_open": 4, "merge_ask": 5, "merged": 5,
    "done": 5, "parked": -1, "failed": -1,
}
#: PG-LANG JRN8: an audit step's track. It reads, its findings are read,
#: and they are filed; nothing is checked, opened as a PR or merged.
AUDIT_STATIONS = ("brief", "work", "review", "file")
_AUDIT_STATION_OF = {
    "planned": -1, "ready": -1, "briefed": 0, "working": 1, "waiting": 1, "limited": 1, "checking": 1,
    "check_failed": 1, "review": 2, "findings": 2, "pr_open": 3, "merge_ask": 3, "merged": 3,
    "done": 3, "parked": -1, "failed": -1,
}

#: The words a state reads on a face (sentence case; ``stateWords`` draws them).
STEP_WORDS = {
    "planned": "Planned", "ready": "Ready", "briefed": "Briefed", "working": "Working",
    "waiting": "Asks you", "limited": "Limited", "checking": "Checking", "check_failed": "Check failed",
    "review": "In review", "findings": "Findings", "pr_open": "PR open", "merge_ask": "Merge?",
    "merged": "Merged", "done": "Done", "parked": "Parked", "failed": "Failed",
}
PROGRAM_WORDS = {
    "drafting": "Drafting", "running": "Running", "waiting": "Your turn", "done": "Done",
    "parked": "Parked", "failed": "Failed",
}
_STATE_LINES = {
    "running": "The program runs", "waiting": "The program waits on you", "done": "The program is done",
    "failed": "The program failed", "parked": "The program is parked",
}
#: Waiting-first (DeckHand): the Programs list's bands, in order.
PROGRAM_BAND = {"waiting": 0, "failed": 1, "running": 2, "drafting": 3, "done": 4, "parked": 5}

CONTROLS = ("secure", "normal", "yolo")
#: The printed words of the levels: one source (``program_rules.level_word``).
CONTROL_WORDS = LEVEL_WORDS
#: ``level``: the Program's Control level decides (Secure asks him, Normal
#: and YOLO merge); ``owner``: his press for this step at any level;
#: ``none``: no PR (a research step; its result note is the work).
GATE_MERGE = ("level", "owner", "none")
_GATE_MERGE_ALIASES = {"auto": "level", "": "level"}
GATE_REVIEW = ("none", "agent", "person")
REVIEW_DEPTHS = ("glance", "delta", "standard")
EFFORTS = ("low", "medium", "high")
#: The race's contenders, in order (design §6: Claude Code, Codex, pi).
RACE_PROFILES = ("claude-default", "codex-default", "pi-default")
MAX_RACE = 3
#: Two rounds, then him (AG12, hivehouse).
MAX_ROUNDS = 2
#: PG19: the longest Runs on list (the three harnesses and one more engine).
MAX_RUNS_ON = 4

AGENT_LABELS = {"claude-default": "Claude Code", "codex-default": "Codex", "pi-default": "pi"}
#: The default reviewer pairing (decision 4): Codex reviews Claude Code and back.
DEFAULT_REVIEWER = {"claude-default": "codex-default", "codex-default": "claude-default",
                    "pi-default": "claude-default"}

#: ``parked_by``: who parked a step. Only an engine park is his turn.
PARKED_BY_OWNER, PARKED_BY_ENGINE, PARKED_BY_RACE = "owner", "engine", "race"
#: The owner's ruling of 2026-11-01: park stops the steps. A step parked with
#: its Program keeps the state it had in ``facts.park_from``; Resume puts it back.
PARKED_BY_PROGRAM = "program"
PARKED_WITH_PROGRAM = "Parked with the program"

#: Your-turn kinds and the choices of each (the REST decide body).
DECIDE_CHOICES = {
    "merge": ("merge", "not_yet"),
    "finding": ("fix_now", "later", "skip"),
    "parked": ("resume", "skip"),
    "ask_review": ("prepare",),
    "core": ("go_on", "park"),
    # 2026-10-31: the step's agent's commit, held by the gate or not made.
    "commit": ("allow", "not_now"),
    "race": ("pick",),
    "add_step": ("add", "skip"),
    "close": ("close",),
    # PG19: the agent is at its usage limit: continue in the next agent now,
    # or wait for the reset.
    "limited": ("continue", "wait"),
    # PG-REQ: a requirement (his word, one left after the rounds), and what
    # an agent proposes: a requirement, a change to a planned step, an
    # amendment to a running step's brief.
    # PG-IMPORT IMP2: ``done`` and ``cant`` answer a to-do (a Your word walk).
    "requirement": ("met", "unmet", "waive", "send_back", "done", "cant"),
    "requirement_proposed": ("add", "skip"),
    "step_change": ("apply", "skip"),
    "step_amend": ("send", "skip"),
    # PG-LANG LANG13: the delivery at Done failed (retry) or waits for his
    # merge at Secure (merge); skip leaves the Program Done, undelivered.
    "delivery": ("retry", "merge", "skip"),
    # PG-LANG JRN9, JRN10 (journey J7): an audit's findings to file (Secure),
    # and the fix program its MUST findings make.
    "audit_file": ("file", "skip"),
    "fix_program": ("make", "skip"),
    # PG-LANG JRN11, JRN12 (journey J8): a lesson the engine saw; never kept by rule.
    "lesson": ("keep_program", "keep_repo", "skip"),
}
#: PG-REQ: the proposal kinds (a checkpoint row each, ``choice`` empty until
#: he answers).
PROPOSAL_KINDS = ("requirement_proposed", "step_change", "step_amend")



#: PG-DIRECTION DIR1 (DIRECTION-2026-10-31.md §3 "The decision record"):
#: where his answer came from. ``desk`` (or none) is the desk; each other
#: channel names itself in the ledger line and in ``program_checkpoints.via``.
VIA_CHANNELS = ("desk", "phone", "call", "telegram", "page")
VIA_WORDS = {"phone": "decided on your phone", "call": "decided on a call", "telegram": "decided from Telegram",
             "page": "decided from the briefing page"}
#: DIR4: the ledger's words for a Later said on a channel.
LATER_VIA_WORDS = {"phone": "on your phone", "call": "on a call", "telegram": "from Telegram",
                   "page": "from the briefing page"}


def via_of(value: Any) -> Optional[str]:
    """The channel of a decide call: ``None`` for the desk, else one of
    ``VIA_CHANNELS``; anything else is refused by name."""
    via = str(value or "desk").strip().lower()
    if via not in VIA_CHANNELS:
        raise ProgramRefused("via_invalid", f"via takes {', '.join(VIA_CHANNELS)}.", status=400)
    return None if via == "desk" else via


class ProgramRefused(ServiceError):
    """A named refusal (``code``); HTTP and MCP answer ``{error, code}``.
    ``more`` rides on the answer (PG-REQ: ``step_frozen`` names its
    ``field`` and ``reason``)."""

    def __init__(self, code: str, detail: str, *, status: int = 409, **more: Any) -> None:
        super().__init__(code, detail, context={"status": status, **more})


def agent_label(profile: Optional[str]) -> str:
    return AGENT_LABELS.get(str(profile or ""), str(profile or "") or "Agent")


def duration_words(seconds: Optional[int]) -> str:
    """``41 min``, ``1 h 12``, ``under a minute``."""
    if seconds is None:
        return ""
    minutes = seconds // 60
    if minutes < 1:
        return "under a minute"
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60} h {minutes % 60:02d}"


# ── triage (design §6: by rule, not by model) ────────────────────────


def triage_effort(brief: str, owns: Iterable[str]) -> str:
    """``high`` for a step owning more than 12 files or naming a refactor or
    a migration; ``low`` for a one-paragraph brief with one file; else
    ``medium``."""
    files = [str(item) for item in owns or [] if str(item).strip()]
    text = str(brief or "")
    if len(files) > 12 or re.search(r"\b(refactor\w*|migrat\w*)\b", text, re.I):
        return "high"
    paragraphs = [part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    if len(files) == 1 and len(paragraphs) <= 1:
        return "low"
    return "medium"


#: A step the night parked at its window's end goes on the next night (LANG12):
#: it is the night's, not his.
NIGHT_ENDED = "Night ended"


def history_of(step: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """PG17: the merged PR an imported step stands for (``facts.history``),
    else ``None``. No agent runs such a step; the runner never moves it."""
    found = (step.get("facts") or {}).get("history")
    return dict(found) if isinstance(found, Mapping) and found.get("pr_number") else None


#: The words a frozen field's hover title says (PG-REQ §8).
FROZEN_READ = "The agent has read it"
FROZEN_SET = "The worktree and the agent are set"
FROZEN_BAR = "The bar does not come down while it runs"
FROZEN_MERGED = "It is merged"
#: Every field of a step he may change, in the order of §8.
STEP_FIELDS = ("title", "brief", "amend", "owns", "after", "effort", "agent", "runs_on_then", "race", "gate_check",
               "gate_review", "review_depth", "gate_merge", "requirements", "position", "for_person", "may_call",
               "prefer_idle", "budget")


#: PG-IMPORT IMP2: the to-do's presses (BroCrew: Done, Can't do it).
TODO_CHOICES = ("done", "cant")
#: A to-do shows from the step's start to its merge.
TODO_STATES = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review",
                         "findings", "pr_open", "merge_ask"})


#: The state of a Program, said on a call.
_SPOKEN_STATE = {
    "drafting": "is not started", "running": "runs", "waiting": "waits on you", "done": "is done",
    "parked": "is parked", "failed": "failed",
}


def spoken_state(wire: Mapping[str, Any]) -> str:
    """PG15: one or two spoken sentences from a Program's state: its steps,
    what waits on him, the last decision. No count of zero."""
    title = str(wire.get("title") or "The program").strip().rstrip(".")
    state = _SPOKEN_STATE.get(str(wire.get("state") or ""), "has no state")
    total, done = int(wire.get("total") or 0), int(wire.get("done") or 0)
    first = f"{title} {state}"
    if total:
        first += f": {done} of {total} {'step is' if total == 1 else 'steps are'} done"
    parts = [first + "."]
    more = []
    turn = int(wire.get("your_turn") or 0) + int(wire.get("asks") or 0)
    if turn:
        more.append(f"{turn} {'thing waits' if turn == 1 else 'things wait'} on you")
    decided = [row for row in (wire.get("decided_for_you") or []) if row.get("line")]
    if decided:
        more.append("the last decision: " + str(decided[0]["line"]).strip().rstrip("."))
    if more:
        sentence = ", and ".join(more)
        parts.append(sentence[0].upper() + sentence[1:] + ".")
    return " ".join(parts)


__all__ = [
    "ACTIVE_STATES",
    "AGENT_LABELS",
    "AUDIT_STATIONS",
    "CLOSED_STATES",
    "CONTROLS",
    "CONTROL_WORDS",
    "DECIDE_CHOICES",
    "DEFAULT_REVIEWER",
    "EFFORTS",
    "ENDINGS",
    "FINISHED_STATES",
    "FINISHED_WORDS",
    "FROZEN_BAR",
    "FROZEN_MERGED",
    "FROZEN_READ",
    "FROZEN_SET",
    "GATE_MERGE",
    "GATE_REVIEW",
    "LATER_VIA_WORDS",
    "MAX_RACE",
    "MAX_ROUNDS",
    "MAX_RUNS_ON",
    "NIGHT_ENDED",
    "PARKED_BY_ENGINE",
    "PARKED_BY_OWNER",
    "PARKED_BY_PROGRAM",
    "PARKED_BY_RACE",
    "PARKED_WITH_PROGRAM",
    "PARK_KIND",
    "PARK_REASONS",
    "PROGRAM_BAND",
    "PROGRAM_STATES",
    "PROGRAM_WORDS",
    "PROPOSAL_KINDS",
    "ProgramRefused",
    "RACE_PROFILES",
    "REVIEW_DEPTHS",
    "STATIONS",
    "STEP_FIELDS",
    "STEP_STATES",
    "STEP_TRANSITIONS",
    "STEP_WORDS",
    "TODO_CHOICES",
    "TODO_STATES",
    "VIA_CHANNELS",
    "VIA_WORDS",
    "agent_label",
    "duration_words",
    "history_of",
    "spoken_state",
    "triage_effort",
    "via_of",
]
