"""Programs (2026-10-28): a goal cut into steps, each step handed to an agent.

docs/internal/betterment/programs/PROGRAMS-DESIGN-2026-10-28.md. This module
is the one service every transport reaches (REST ``web/routes/programs.py``,
MCP ``mcp/families/program.py``, the runner ``program_runner.py``):

- CRUD: create, plan (steps), start, park, resume, race, checkpoint,
  step_done, decide;
- the state machine of §4 (:data:`STEP_TRANSITIONS`), "worst state wins" for
  the Program (:func:`program_state`);
- the owner's turn (:func:`your_turn`), the wire the faces read, the
  ``program_changed`` frame and ``desk_changed("program", ...)``;
- the handover note of §8 (a desk Note ``program-<id>``, rewritten by the
  engine on every change, filed to the Program's Project);
- authority (§7): the owner does everything; an orchestrating agent creates,
  plans, starts and parks only the Programs it created; a step's launch
  writes checkpoints and its report only on its own step; only the owner
  decides.

Every engine decision is a checkpoint line ``by: engine`` and a kernel
operation ``program.step`` (``kernel/program_ops.py``) with the step as its
target.
"""
from __future__ import annotations

import contextvars
import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

from ..db.programs import ProgramStore
from ..logging_config import get_logger
from ..timestamps import local_now, utc_now_iso
from .brief_words import REPORT_STATES, WAIT_SENTENCES, step_report, wait_line
from .errors import NotFound, ServiceError
from .program_rules import LEVEL_WORDS, level_word

log = get_logger("program_service")

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
#: The channel of the decide call in progress (set by ``decide``, read by
#: ``_checkpoint``): every owner line that call writes names it.
_VIA: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("program_decide_via", default=None)


def via_of(value: Any) -> Optional[str]:
    """The channel of a decide call: ``None`` for the desk, else one of
    ``VIA_CHANNELS``; anything else is refused by name."""
    via = str(value or "desk").strip().lower()
    if via not in VIA_CHANNELS:
        raise ProgramRefused("via_invalid", f"via takes {', '.join(VIA_CHANNELS)}.", status=400)
    return None if via == "desk" else via


#: ``HOLDSPEAK_PROGRAMS=off``: the runner does not tick (every rig hub).
PROGRAMS_ENV = "HOLDSPEAK_PROGRAMS"

#: The check a repository names (``.holdspeak/program.json``), else this one.
DEFAULT_CHECK = "scripts/quick_check.sh"

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_LOCK = threading.RLock()


def programs_on() -> bool:
    return os.environ.get(PROGRAMS_ENV, "on").strip().lower() not in {"off", "0", "false", "no"}


class ProgramRefused(ServiceError):
    """A named refusal (``code``); HTTP and MCP answer ``{error, code}``.
    ``more`` rides on the answer (PG-REQ: ``step_frozen`` names its
    ``field`` and ``reason``)."""

    def __init__(self, code: str, detail: str, *, status: int = 409, **more: Any) -> None:
        super().__init__(code, detail, context={"status": status, **more})


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def agent_label(profile: Optional[str]) -> str:
    return AGENT_LABELS.get(str(profile or ""), str(profile or "") or "Agent")


def _principal_kind(principal: Any) -> str:
    kind = getattr(principal, "kind", None)
    return str(getattr(kind, "value", kind) or "")


def _is_owner(principal: Any) -> bool:
    return _principal_kind(principal) == "owner"


def _launch_of(principal: Any) -> Optional[str]:
    try:
        from .conductor_launch import launch_id_of

        return launch_id_of(principal)
    except Exception:
        return None


#: IMP4: Secure < Normal < YOLO.
_LADDER = {"secure": 0, "normal": 1, "yolo": 2}
#: IMP4: the line an agent's wider control is refused with.
NO_WIDER = "Refused: a program runs no wider than what made it"


def parent_level(principal: Any, db: Any = None) -> Optional[str]:
    """IMP4 (BROCREW-IMPORT "Never wider than the parent"): the widest
    control an agent may give a Program: its own launch's level (a step's
    agent runs at its Program's), else the desk's Control mode. ``None`` for
    the owner: his own press is never capped."""
    if _is_owner(principal):
        return None
    from .control_level import level_for_launch
    from .program_rules import level_of

    launch = _launch_of(principal)
    if launch:
        return level_for_launch(launch, db=db)
    return level_of(_desk_control_mode())


def wider(level: Any, than: Optional[str]) -> bool:
    """``level`` is wider than ``than`` on the ladder (never when ``than`` is
    ``None``: the owner)."""
    return than is not None and _LADDER.get(str(level), 0) > _LADDER.get(str(than), 0)


def _creator(principal: Any) -> str:
    """``owner``, ``launch:<id>`` or ``agent:<identity>``: who made a Program."""
    if _is_owner(principal):
        return "owner"
    launch = _launch_of(principal)
    if launch:
        return f"launch:{launch}"
    return f"agent:{getattr(principal, 'identity', '') or 'unknown'}"


def _seconds_between(start: Optional[str], end: Optional[str] = None) -> Optional[int]:
    from datetime import datetime, timezone

    def parse(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)

    a, b = parse(start), parse(end) or datetime.now(timezone.utc)
    if a is None:
        return None
    return max(0, int((b - a).total_seconds()))


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


# ── the Program's state: worst wins ──────────────────────────────────


#: A step the night parked at its window's end goes on the next night (LANG12):
#: it is the night's, not his.
NIGHT_ENDED = "Night ended"


def _engine_parked(step: Mapping[str, Any]) -> bool:
    return (step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_ENGINE
            and not str(step.get("parked_reason") or "").startswith(NIGHT_ENDED))


def _live(steps: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [step for step in steps if step.get("state") not in CLOSED_STATES and step.get("state") != "failed"]


def history_of(step: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """PG17: the merged PR an imported step stands for (``facts.history``),
    else ``None``. No agent runs such a step; the runner never moves it."""
    found = (step.get("facts") or {}).get("history")
    return dict(found) if isinstance(found, Mapping) and found.get("pr_number") else None


def _history_input(raw: Any, index: int) -> Optional[dict[str, Any]]:
    """Validate a plan step's ``history`` (pr_number and merged_at)."""
    from datetime import datetime, timezone

    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ProgramRefused("history_invalid", f"Step {index}: history is an object.", status=400)
    try:
        number = int(raw.get("pr_number"))
    except (TypeError, ValueError):
        number = 0
    if number < 1:
        raise ProgramRefused("history_invalid", f"Step {index}: history needs a pr_number.", status=400)
    stamp = str(raw.get("merged_at") or "").strip()
    try:
        merged = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        merged = None
    if not stamp or merged is None:
        raise ProgramRefused("history_invalid", f"Step {index}: history needs merged_at (ISO 8601).", status=400)
    merged = (merged if merged.tzinfo else merged.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    url = str(raw.get("pr_url") or "").strip() or None
    head = str(raw.get("head_commit") or "").strip() or None
    return {"pr_number": number, "pr_url": url, "merged_at": merged.isoformat().replace("+00:00", "Z"),
            "head_commit": head}


def history_words(steps: Iterable[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """PG17: ``Merged 15 PRs · 28 Oct to 29 Oct`` for the imported steps."""
    from datetime import datetime

    stamps = sorted(str(item["merged_at"]) for item in (history_of(step) for step in steps) if item)
    if not stamps:
        return None

    def day(value: str) -> str:
        try:
            at = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
        except ValueError:
            return value[:10]
        return f"{at.day} {at.strftime('%b')}"

    first, last = day(stamps[0]), day(stamps[-1])
    count = len(stamps)
    span = first if first == last else f"{first} to {last}"
    return {"prs": count, "first": stamps[0], "last": stamps[-1],
            "words": f"Merged {count} PR{'s' if count != 1 else ''} · {span}"}


def your_turn(program: Mapping[str, Any], steps: Iterable[Mapping[str, Any]],
              requirements: Optional[Iterable[Mapping[str, Any]]] = None,
              proposals: Optional[Iterable[Mapping[str, Any]]] = None) -> list[dict[str, Any]]:
    """What only he can do on this Program, one item per press.

    Design §6 (Control): only a core question, or what the rules send to
    him at the Program's level, is his. At Secure: merges, findings, failed
    steps, race winners, added steps, the Program's Done. At Normal and YOLO:
    core questions, findings left after the rounds, a person to ask for a
    review, and the failed steps once nothing else runs ("one row to him at
    the end").

    A parked Program asks nothing of him: its items are retired while it is
    parked, and Resume raises again what is still held (they are read off
    the steps, never stored)."""
    from .program_rules import level_of

    if str(program.get("state") or "") == "parked":
        return []
    steps = list(steps)
    level = level_of(program.get("control"))
    live = _live(steps)
    items: list[dict[str, Any]] = []
    for step in steps:
        state = str(step.get("state") or "")
        facts = step.get("facts") or {}
        base = {
            "program_id": program["id"], "program_title": program["title"], "step_id": step["id"],
            "ordinal": step["ordinal"], "step_title": step["title"], "launch_id": step.get("launch_id"),
            "since": step.get("updated_at"), "project_id": program.get("project_id"),
            "for_person_id": step.get("for_person_id") or program.get("for_person_id"),
            "pr": {"number": step.get("pr_number"), "url": step.get("pr_url")} if step.get("pr_url") else None,
        }
        label = f"step {step['ordinal']} \u201c{step['title']}\u201d"
        core = facts.get("core")
        # PG-DIRECTION DIR4: a step YOLO parked because he said Later keeps
        # its core question (his Go on resumes it).
        if isinstance(core, Mapping) and not core.get("cleared") and (
                state not in CLOSED_STATES or (state == "parked" and core.get("provisional"))):
            items.append({**base, "id": f"{step['id']}:core", "kind": "core", "core": True,
                          "choices": list(DECIDE_CHOICES["core"]), "reason": core.get("reason"),
                          "title": f"{label.capitalize()}: {core.get('reason')}"})
            continue
        held = facts.get("held_commit") if isinstance(facts.get("held_commit"), Mapping) else None
        held = held if level != "yolo" else None  # YOLO never holds a commit for him (the tick releases it)
        if (held or facts.get("commit_ask")) and state not in CLOSED_STATES and state != "parked":
            # A held commit never expires silently: his row while the gate
            # holds it (``hold``) and after the hold ended with the change
            # left in the worktree.
            items.append({**base, "id": f"{step['id']}:commit", "kind": "commit", "hold": bool(held),
                          "choices": list(DECIDE_CHOICES["commit"]),
                          "title": f"{label[:1].upper() + label[1:]}: the agent's commit waits for you"})
            continue
        limit = facts.get("limit") if isinstance(facts.get("limit"), Mapping) else None
        if state == "waiting":
            items.append({**base, "id": f"{step['id']}:answer", "kind": "answer", "choices": [],
                          "title": f"Answer {label}"})
        elif state == "limited" and limit and limit.get("next") and not limit.get("waiting") and level != "yolo":
            # PG19: Secure and Normal ask him; YOLO continued at once.
            nxt = limit["next"]
            until = f" until {limit['words']}" if limit.get("words") else ""
            items.append({**base, "id": f"{step['id']}:limited", "kind": "limited",
                          "choices": list(DECIDE_CHOICES["limited"]), "next": dict(nxt),
                          "until": limit.get("until"), "until_words": limit.get("words") or "",
                          "agent": agent_label(limit.get("profile") or step.get("profile")),
                          "warning": bool(limit.get("share")),
                          "title": f"{agent_label(limit.get('profile') or step.get('profile'))} is at its limit{until}: "
                                   f"continue in {nxt.get('label') or agent_label(nxt.get('profile'))} now, or wait?"})
        elif state == "merge_ask":
            number = step.get("pr_number")
            pr = f"PR #{number}" if number else (
                f"into {program.get('base_branch') or 'main'}" if facts.get("local_merge") else "the PR")
            items.append({**base, "id": f"{step['id']}:merge", "kind": "merge",
                          "choices": list(DECIDE_CHOICES["merge"]),
                          "title": f"Merge {label}? ({pr}, check green"
                                   f"{', review passed' if step.get('review_verdict') == 'pass' else ''})"})
        elif state == "findings" and facts.get("findings_open"):
            for finding in step.get("findings") or []:
                if finding.get("decision") or not finding.get("to_owner", True) or finding.get("requirement_id"):
                    continue  # PG-REQ: a requirement's finding is its requirement_left row
                items.append({**base, "id": f"{step['id']}:finding:{finding['id']}", "kind": "finding",
                              "finding_id": finding["id"], "level": finding.get("level"),
                              "core": bool(finding.get("core")), "choices": list(DECIDE_CHOICES["finding"]),
                              "title": f"Finding on {label}: {finding.get('text', '')}"})
        elif (_engine_parked(step) and not facts.get("requirements_left")
              and (level == "secure" or facts.get("park_is_his", True) or not live)):
            items.append({**base, "id": f"{step['id']}:parked", "kind": "parked",
                          "choices": list(DECIDE_CHOICES["parked"]),
                          "title": f"Parked {label}: {_parked_words(step.get('parked_reason'))}"})
        if facts.get("awaiting_pick") and state not in CLOSED_STATES:
            items.append({**base, "id": f"{step['id']}:race", "kind": "race", "choices": list(DECIDE_CHOICES["race"]),
                          "title": f"Pick {agent_label(step.get('profile'))} as the winner of {label}?"})
        for index, proposal in enumerate(facts.get("proposed_steps") or []):
            if proposal.get("decision"):
                continue
            items.append({**base, "id": f"{step['id']}:add_step:{index}", "kind": "add_step", "proposal": index,
                          "choices": list(DECIDE_CHOICES["add_step"]),
                          "title": (f"Start a step from checkpoint {str(proposal['start_from'].get('ref') or '').rsplit('/', 1)[-1]} of {label}"
                                    if isinstance(proposal.get("start_from"), Mapping)
                                    else f"Add a step after {label}: {proposal.get('title')}")})
        if state in ("pr_open", "merge_ask") and step.get("gate_review") == "person" and not facts.get("person_approved"):
            name = (facts.get("person") or {}).get("name") or "the reviewer"
            number = step.get("pr_number")
            items.append({**base, "id": f"{step['id']}:ask_review", "kind": "ask_review",
                          "choices": list(DECIDE_CHOICES["ask_review"]),
                          "title": f"Ask {name} to review PR #{number}" if number else f"Ask {name} to review"})
    items.extend(requirement_items(program, steps, requirements, proposals))
    if (level == "secure" and steps and not live and not items and not program.get("closed_at")
            and program.get("state") not in ("drafting", "parked") and not end_pending(program, steps, requirements)):
        items.append({
            "program_id": program["id"], "program_title": program["title"], "step_id": "", "ordinal": 0,
            "step_title": "", "launch_id": None, "since": program.get("updated_at"),
            "project_id": program.get("project_id"), "for_person_id": program.get("for_person_id"), "pr": None,
            "id": f"{program['id']}:close", "kind": "close", "choices": list(DECIDE_CHOICES["close"]),
            "title": f"Close \u201c{program['title']}\u201d: every step is finished",
        })
    return items


# ── PG-REQ §8: what he can change on a step, by its state ────────────

#: The words a frozen field's hover title says (PG-REQ §8).
FROZEN_READ = "The agent has read it"
FROZEN_SET = "The worktree and the agent are set"
FROZEN_BAR = "The bar does not come down while it runs"
FROZEN_MERGED = "It is merged"
#: Every field of a step he may change, in the order of §8.
STEP_FIELDS = ("title", "brief", "amend", "owns", "after", "effort", "agent", "runs_on_then", "race", "gate_check",
               "gate_review", "review_depth", "gate_merge", "requirements", "position", "for_person", "may_call",
               "prefer_idle", "budget")
_STARTED = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review", "findings",
                      "failed"})


def step_fields(step: Mapping[str, Any]) -> tuple[list[str], dict[str, str]]:
    """``(editable, frozen)``: the §8 table for the step's state. ``frozen``
    maps each field he cannot change now to its reason."""
    state = str(step.get("state") or "planned")
    if state in ("planned", "ready"):
        return [field for field in STEP_FIELDS if field != "amend"], {}
    if state in ("merged", "done"):
        return ["title"], {field: FROZEN_MERGED for field in STEP_FIELDS if field != "title"}
    frozen = {"brief": FROZEN_READ, "owns": FROZEN_READ, "after": FROZEN_READ, "effort": FROZEN_SET,
              "agent": FROZEN_SET, "race": FROZEN_SET, "gate_check": FROZEN_BAR, "position": FROZEN_SET,
              "prefer_idle": FROZEN_SET, "budget": FROZEN_SET}
    if state in _STARTED:
        if step.get("gate_review") == "agent":
            frozen["gate_review"] = FROZEN_BAR
        if state in ("review", "findings"):
            frozen["review_depth"] = FROZEN_READ
    else:  # pr_open, merge_ask, parked: the PR is open or he parked it
        frozen.update({"amend": FROZEN_READ, "runs_on_then": FROZEN_SET, "gate_review": FROZEN_BAR,
                       "review_depth": FROZEN_READ})
        if state == "parked":
            frozen.update({"gate_merge": FROZEN_SET, "for_person": FROZEN_SET, "may_call": FROZEN_SET})
    return [field for field in STEP_FIELDS if field not in frozen], frozen


def _turn_base(program: Mapping[str, Any], step: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    step = step or {}
    return {
        "program_id": program["id"], "program_title": program["title"], "step_id": step.get("id") or "",
        "ordinal": step.get("ordinal") or 0, "step_title": step.get("title") or "", "launch_id": step.get("launch_id"),
        "since": step.get("updated_at") or program.get("updated_at"), "project_id": program.get("project_id"),
        "for_person_id": step.get("for_person_id") or program.get("for_person_id"),
        "pr": {"number": step.get("pr_number"), "url": step.get("pr_url")} if step.get("pr_url") else None,
    }


def program_own(requirements: Optional[Iterable[Mapping[str, Any]]]) -> list[Mapping[str, Any]]:
    """PG-REQ: the Program's own requirements (the end check)."""
    return [row for row in requirements or [] if not row.get("step_id") and not row.get("each_step")]


def steps_finished(program: Mapping[str, Any], steps: list[Mapping[str, Any]]) -> bool:
    """Every top step merged, done or parked by him (the end check may run)."""
    top = [step for step in steps if not step.get("race_of")]
    return bool(top) and not _live(steps) and all(
        step.get("state") in FINISHED_STATES or (step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_OWNER)
        for step in top)


def end_pending(program: Mapping[str, Any], steps: list[Mapping[str, Any]],
                requirements: Optional[Iterable[Mapping[str, Any]]]) -> bool:
    """PG-REQ §5: the Program's own required requirements are not all Met or
    Waived after the last step: the Program is not Done yet."""
    from .program_requirements import gates

    if program.get("closed_at") or not steps_finished(program, steps):
        return False
    return any(gates(row) for row in program_own(requirements))


#: PG-IMPORT IMP2: the to-do's presses (BroCrew: Done, Can't do it).
TODO_CHOICES = ("done", "cant")
#: A to-do shows from the step's start to its merge.
TODO_STATES = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review",
                         "findings", "pr_open", "merge_ask"})


def todo_head(agent: str, ordinal: Any) -> str:
    """"Claude Code asks you to do this · step 3"."""
    return f"{agent} asks you to do this" + (f" · step {int(ordinal)}" if ordinal else "")


def his_word(row: Mapping[str, Any], step: Optional[Mapping[str, Any]]) -> bool:
    """A requirement his press judges: Your word, and (JRN14) a Review on a
    step whose review is a person's (no agent reviewer reads it; his word
    at MERGE stands for the person gate)."""
    kind = row.get("kind")
    return kind == "word" or (kind == "review" and (step or {}).get("gate_review") == "person")


def requirement_items(program: Mapping[str, Any], steps: Iterable[Mapping[str, Any]],
                      requirements: Optional[Iterable[Mapping[str, Any]]],
                      proposals: Optional[Iterable[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    """PG-REQ §9: his word on a step at its merge (``requirement_word``), a
    requirement still unmet after the rounds (``requirement_left``), the
    Program's own after the last step, and what an agent proposes."""
    from .program_requirements import judged, label

    steps = list(steps)
    reqs = list(requirements or [])
    by_id = {row["id"]: row for row in reqs}
    items: list[dict[str, Any]] = []

    def word(base: dict[str, Any], row: Mapping[str, Any], where: str) -> dict[str, Any]:
        item = {**base, "id": f"{row['id']}:word", "kind": "requirement_word", "requirement_id": row["id"],
                "choices": ["met", "unmet"], "title": f"{where}: {label(row['ordinal'])} · {row['text']}"}
        walk = (row.get("spec") or {}).get("walk")
        if walk:
            # PG-LANG §6.3: a walk is the steps he does; HoldSpeak never runs it.
            item["walk"] = [str(line) for line in walk]
        return item

    def todo(base: dict[str, Any], row: Mapping[str, Any], step: Mapping[str, Any]) -> dict[str, Any]:
        who = agent_label(step.get("profile") or program.get("default_profile"))
        return {**base, "id": f"{row['id']}:todo", "kind": "todo", "requirement_id": row["id"],
                "choices": list(TODO_CHOICES), "agent": who, "head": todo_head(who, step.get("ordinal")),
                "walk": [str(line) for line in (row.get("spec") or {}).get("walk") or []],
                "title": f"{todo_head(who, step.get('ordinal'))}: {label(row['ordinal'])} · {row['text']}"}

    def left(base: dict[str, Any], row: Mapping[str, Any], where: str, choices: list[str],
             finding_id: Optional[str] = None) -> dict[str, Any]:
        rounds = int(row.get("rounds") or 0)
        line = str((row.get("evidence") or {}).get("line") or "")
        what = (f"{label(row['ordinal'])} is unmet after {rounds} round{'s' if rounds != 1 else ''}" if rounds
                else f"{label(row['ordinal'])} has no answer")
        return {**base, "id": f"{row['id']}:left", "kind": "requirement_left", "requirement_id": row["id"],
                "finding_id": finding_id, "choices": choices,
                "title": f"{where}: {what}" + (f" · {line}" if line else "")}

    for step in steps:
        if step.get("race_of"):
            continue
        state = str(step.get("state") or "")
        facts = step.get("facts") or {}
        base = _turn_base(program, step)
        where = f"Step {step['ordinal']} · {step['title']}"
        own = [row for row in reqs if row.get("step_id") == step["id"]]
        for row in own:
            if not his_word(row, step) or not row.get("required") or row.get("state") != "not_yet":
                continue
            if (row.get("spec") or {}).get("walk") and state in TODO_STATES:
                # PG-IMPORT IMP2 (BroCrew's to-do): a walk is a thing the agent
                # asks him to do by hand, from the step's start to its merge.
                items.append(todo(base, row, step))
            elif state in ("pr_open", "merge_ask"):
                items.append(word(base, row, where))
        seen: set[str] = set()
        for rid in facts.get("requirements_left") or []:
            row = by_id.get(rid)
            if row is not None and not judged(row) and rid not in seen:
                seen.add(rid)
                items.append(left(base, row, where, ["send_back", "waive"]))
        if state == "findings" and facts.get("findings_open"):
            for finding in step.get("findings") or []:
                row = by_id.get(str(finding.get("requirement_id") or ""))
                if row is None or finding.get("decision") or row["id"] in seen or judged(row):
                    continue
                seen.add(row["id"])
                items.append(left(base, row, where, ["send_back", "waive"], finding_id=finding.get("id")))
    if steps_finished(program, steps) and not program.get("closed_at") and program.get("state") not in ("drafting", "parked"):
        base = _turn_base(program, None)
        for row in program_own(reqs):
            if not row.get("required"):
                continue
            if row.get("state") == "not_yet" and row.get("kind") in ("word", "review"):
                # The end check's Review has no reviewer launch over the base
                # diff yet (PG-REQ §6): it is his word until that is built.
                items.append(word(base, row, "The program"))
            elif row.get("state") == "unmet":
                items.append(left(base, row, "The program", ["waive"]))
    step_of = {step["id"]: step for step in steps}
    for row in proposals or []:
        kind = str(row.get("kind") or "")
        if kind not in PROPOSAL_KINDS or row.get("choice") or row.get("overturned_at"):
            continue
        undo = row.get("undo") or {}
        base = _turn_base(program, step_of.get(str(row.get("step_id") or "")))
        items.append({**base, "id": f"proposal:{row['id']}", "kind": kind, "proposal_id": row["id"],
                      "choices": list(DECIDE_CHOICES[kind]), "title": str(undo.get("title") or row.get("line") or "")})
    return items


def limit_words(limit: Optional[Mapping[str, Any]]) -> str:
    """PG19: ``Limited until 14:00 · continuing in Codex`` (a next agent
    waits for his press or the minutes), ``… · waits for the reset`` (no
    next agent is left, or he chose to wait)."""
    limit = limit or {}
    head = f"Limited until {limit['words']}" if limit.get("words") else "Limited"
    nxt = limit.get("next") if isinstance(limit.get("next"), Mapping) else None
    if nxt and not limit.get("waiting"):
        return f"{head} · continuing in {nxt.get('label') or agent_label(nxt.get('profile'))}"
    return f"{head} · waits for the reset"


def seen_of(step: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """PG-IMPORT IMP1: what the engine sees on a step as it writes a
    checkpoint (the head commit when it moved off the base, the checked
    commit and its verdict, the PR number, the state). The step report's
    Checked lines cite the checkpoint that saw each fact."""
    if not step or not step.get("id"):
        return None
    head = step.get("head_commit")
    base = (step.get("facts") or {}).get("base_commit")
    seen = {"commit": head if head and head != base else None, "checked": step.get("checked_commit"),
            "check": step.get("check_verdict"), "pr": step.get("pr_number"), "state": step.get("state")}
    return {key: value for key, value in seen.items() if value not in (None, "")}


def step_wait(program: Mapping[str, Any], step: Mapping[str, Any],
              steps: Iterable[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """PG-IMPORT IMP3: what a step waits on, as ``{cause, line, at?}``, or
    ``None``. The engine's own record first (``facts.wait``: the lane it can
    no longer find, a recovery, a hold that ended, a message that did not
    arrive); else a Planned step that waits on a step that ended without a
    merge (parked by the engine, failed) or is gone from the plan."""
    facts = step.get("facts") or {}
    agent = agent_label(((facts.get("running_on") or {}).get("profile") if isinstance(facts.get("running_on"), Mapping)
                         else None) or step.get("profile") or program.get("default_profile"))
    wait = facts.get("wait") if isinstance(facts.get("wait"), Mapping) else None
    if wait and wait.get("cause") in WAIT_SENTENCES:
        return {"cause": wait["cause"], "at": wait.get("at"),
                "line": wait_line(step.get("ordinal"), agent, str(wait["cause"]))}
    if step.get("state") not in ("planned", "ready") or step.get("race_of"):
        return None
    steps = [row for row in steps if not row.get("race_of")]
    for ordinal in step.get("after") or []:
        named = [row for row in steps if int(row.get("ordinal") or 0) == int(ordinal)]
        ended = not named or all(row.get("state") == "failed" or (
            row.get("state") == "parked" and row.get("parked_by") != PARKED_BY_OWNER) for row in named)
        if ended:
            return {"cause": "target_ended", "line": wait_line(step.get("ordinal"), agent, "target_ended")}
    return None


def program_state(program: Mapping[str, Any], steps: list[Mapping[str, Any]],
                  requirements: Optional[Iterable[Mapping[str, Any]]] = None,
                  proposals: Optional[Iterable[Mapping[str, Any]]] = None) -> str:
    """Worst state wins (AG0). Drafting and Parked are his; the rest is read
    off the steps. PG-REQ: a Program whose own requirements are not judged
    after its last step still runs (the end check)."""
    current = str(program.get("state") or "drafting")
    if current in ("drafting", "parked"):
        return current
    if not steps:
        return "running"
    if your_turn(program, steps, requirements, proposals):
        return "waiting"
    if _live(steps):
        return "running"
    if any(step.get("state") == "failed" for step in steps):
        return "failed"
    if end_pending(program, steps, requirements):
        return "running"
    return "done"


# ── the service ──────────────────────────────────────────────────────


class ProgramService:
    """The one Programs service (REST, MCP and the runner share it)."""

    def __init__(
        self,
        db: Any,
        *,
        store: Optional[ProgramStore] = None,
        clock: Callable[[], str] = utc_now_iso,
        broadcast: Optional[Callable[[str, Any], None]] = None,
        kernel: Optional[Callable[..., Optional[str]]] = None,
        profiles: Optional[Callable[[], Iterable[str]]] = None,
        engines: Optional[Callable[[str], Any]] = None,
        people: Optional[Callable[[], Any]] = None,
        runner: Optional[Callable[[], Any]] = None,
        phone: Optional[Callable[[], Any]] = None,
    ) -> None:
        self.db = db
        self._phone = phone
        self.store = store or ProgramStore(db)
        self._clock = clock
        self._bus = broadcast
        self._kernel = kernel
        self._profiles = profiles
        self._engines = engines
        self._people = people
        self._runner = runner
        #: LANG1: a text apply holds the frames and the ticks of the verbs it
        #: calls, then sends one frame (per thread: other writers go on).
        self._held = threading.local()

    # ── seams ────────────────────────────────────────────────────────

    def runner(self) -> Any:
        if self._runner is not None:
            return self._runner()
        from .program_runner import default_runner

        return default_runner(self)

    def _broadcast(self, frame: str, payload: Mapping[str, Any]) -> None:
        bus = self._bus
        if bus is None:
            try:
                from ..runtime import composition

                bus = composition.broadcast()
            except Exception:
                bus = None
        if bus is None:
            return
        try:
            bus(frame, dict(payload))
        except Exception as exc:  # a dead socket never fails a write
            log.debug(f"program frame dropped: {exc}")

    def _known_profiles(self) -> set[str]:
        """The harness profiles a step may run on (Claude Code, Codex, pi)."""
        if self._profiles is not None:
            return set(self._profiles())
        return set(AGENT_LABELS)

    def engine(self, engine_id: Optional[str]) -> Any:
        """The library engine of ``engine_id`` (``pi_launch.LibraryEngine``),
        ``None`` when the library has none."""
        if not engine_id:
            return None
        if self._engines is not None:
            return self._engines(engine_id)
        from ..delivery.pi_launch import library_engine

        return library_engine(self.db, engine_id)

    def _people_service(self) -> Any:
        if self._people is not None:
            return self._people()
        try:
            from ..mcp.families.people import build_people_service
            from ..runtime import composition

            return composition.service("people_service", build_people_service)
        except Exception:
            return None

    def person_name(self, person_id: Optional[str]) -> str:
        if not person_id:
            return ""
        service = self._people_service()
        try:
            return str((service.display_names() or {}).get(str(person_id)) or "")
        except Exception:
            return ""

    def person_logins(self, person_id: Optional[str]) -> set[str]:
        """The person's names a GitHub review is matched by (their aliases and
        display name), case folded."""
        if not person_id:
            return set()
        service = self._people_service()
        try:
            from ..principals import Principal, PrincipalKind

            record = service.get_relationship(Principal(PrincipalKind.OWNER, "program-engine"), str(person_id))
        except Exception:
            return set()
        record = record.get("relationship", record) if isinstance(record, Mapping) else {}
        names = {str(alias).strip().casefold() for alias in record.get("owner_aliases") or [] if str(alias).strip()}
        if record.get("display_name"):
            names.add(str(record["display_name"]).strip().casefold())
        return names

    # ── reads ────────────────────────────────────────────────────────

    def _program(self, program_id: str) -> dict[str, Any]:
        program = self.store.get_program(str(program_id or ""))
        if program is None:
            raise NotFound("program", str(program_id))
        return program

    def _step(self, program: Mapping[str, Any], step_id: str) -> dict[str, Any]:
        step = self.store.get_step(str(step_id or ""))
        if step is None or step["program_id"] != program["id"]:
            raise NotFound("program_step", str(step_id))
        return step

    # ── PG-REQ: requirements and proposals beside the steps ──────────

    def requirements(self, program_id: str) -> list[dict[str, Any]]:
        return self.store.list_requirements(str(program_id))

    def proposals(self, program_id: str, checkpoints: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
        rows = checkpoints if checkpoints is not None else self.store.list_checkpoints(str(program_id))
        return [row for row in rows if row.get("kind") in PROPOSAL_KINDS]

    def _turn(self, program: Mapping[str, Any], steps: list[Mapping[str, Any]], *,
              requirements: Optional[list[dict[str, Any]]] = None,
              checkpoints: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
        from . import program_delivery

        reqs = requirements if requirements is not None else self.requirements(program["id"])
        items = your_turn(program, steps, reqs, self.proposals(program["id"], checkpoints))
        from . import program_lessons

        # JRN11: the lessons the engine saw, each his to keep or skip.
        items += program_lessons.turn_items(program, checkpoints if checkpoints is not None
                                            else self.store.list_checkpoints(program["id"]))
        if program.get("template") == "audit":
            from . import program_audit

            # JRN9, JRN10: the findings to file (Secure) and the fix program.
            items += program_audit.turn_items(program, steps, checkpoints if checkpoints is not None
                                              else self.store.list_checkpoints(program["id"]))
        if program.get("closed_at") and program_delivery.target(program) is not None:
            # LANG13: a delivery that failed, or that waits for his merge.
            item = program_delivery.turn_item(program, program_delivery.last_line(self, program["id"]))
            if item is not None:
                items.append(item)
        return _with_pages(self.db, program["id"], items, now=self._clock())

    def _deliver_once(self, program: Mapping[str, Any]) -> None:
        """LANG13: a closed Program with a delivery writes it once (the
        ledger's delivery line is the record; a press retries it)."""
        from . import program_delivery

        if not program_delivery.pending(self, program):
            return
        try:
            program_delivery.deliver(self.runner(), program)
        except Exception as exc:  # the delivery never stops the Program's Done
            log.error(f"program {program['id']}: the delivery did not run: {exc}", exc_info=True)

    def _state(self, program: Mapping[str, Any], steps: list[Mapping[str, Any]], *,
               requirements: Optional[list[dict[str, Any]]] = None,
               checkpoints: Optional[list[dict[str, Any]]] = None) -> str:
        reqs = requirements if requirements is not None else self.requirements(program["id"])
        return program_state(program, steps, reqs, self.proposals(program["id"], checkpoints))

    def list(self, principal: Any = None, *, q: Any = None, project_id: Any = None,
             person_id: Any = None) -> dict[str, Any]:
        """Every Program, waiting first, then running, drafting, done, parked;
        the most recently changed first inside a band. PG-REQ §7: ``q``
        (every word in the row's ``search_words``), ``project_id`` and
        ``person_id`` narrow the rows; ``of`` is the count before them."""
        rows = []
        for program in self.store.list_programs():
            steps = self.store.list_steps(program["id"])
            rows.append(self._summary(program, steps))
        everything = len(rows)
        words = [word for word in re.findall(r"[#\w]+", str(q or "").lower()) if word]
        if words:
            rows = [row for row in rows if all(word in row["search_words"] for word in words)]
        if project_id:
            rows = [row for row in rows if row.get("project_id") == str(project_id)]
        if person_id:
            rows = [row for row in rows if any(person["id"] == str(person_id) for person in row.get("persons") or [])]
        _waiting_first(rows)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["state"]] = counts.get(row["state"], 0) + 1
        worst = min((row["state"] for row in rows), key=lambda s: PROGRAM_BAND.get(s, 9), default=None)
        out = {"programs": rows, "counts": {k: v for k, v in counts.items() if v},
               "worst": worst, "worst_word": PROGRAM_WORDS.get(worst or "", "")}
        if words or project_id or person_id:
            out["filter"] = {"q": str(q or "").strip() or None, "project_id": project_id or None,
                             "person_id": person_id or None, "shown": len(rows), "of": everything}
        return out

    def get(self, principal: Any, program_id: str) -> dict[str, Any]:
        program = self._program(program_id)
        steps = self.store.list_steps(program["id"])
        wire = self._wire(program, steps)
        # LANG5: the rows a call left for his press (only when there are some).
        from .program_spoken import on_desk

        held = on_desk(program["id"])
        if held:
            wire["held_shape"] = held
        return wire

    def find(self, principal: Any, *, program_id: Any = None, name: Any = None,
             startable: bool = False) -> dict[str, Any]:
        """PG15: one Program by its id, or by the words he said ("the
        overnight program"): every word must be in its title or its template.
        ``startable`` puts a Drafting or Parked match first. Nothing matches:
        ``program_not_found``; it never makes a Program."""
        if program_id:
            found = self.store.get_program(str(program_id))
            if found is not None:
                return found
        said = str(name or program_id or "").strip()
        words = name_words(said)
        if not words:
            raise ProgramRefused("program_name_required", "Say the name of the program.", status=400)
        matches = []
        for program in self.store.list_programs():
            own = set(name_words(str(program.get("title") or ""))) | set(name_words(str(program.get("template") or "")))
            if all(word in own for word in words):
                matches.append(program)
        if not matches:
            raise ProgramRefused("program_not_found", f"There is no program with the name {said}. I did not start a program.",
                                 status=404)
        if startable:
            matches.sort(key=lambda row: row.get("state") not in ("drafting", "parked"))
        return matches[0]

    def for_project(self, project_id: str) -> list[dict[str, Any]]:
        """The Room's Programs fold (§9b): one row per Program, worst first."""
        rows = [
            self._summary(program, self.store.list_steps(program["id"]))
            for program in self.store.list_programs() if program.get("project_id") == project_id
        ]
        _waiting_first(rows)
        return [{key: row[key] for key in ("id", "title", "state", "state_word", "done", "total", "your_turn",
                                            "updated_at")} for row in rows]

    def for_person(self, person_id: str, *, since: Optional[str] = None) -> list[dict[str, Any]]:
        """The person's Programs (§9b): the room's line, and the 1:1 brief's
        "To show them" (a step merged since ``since``) and "To ask" (a
        finding or a review waits on them)."""
        out = []
        for program in self.store.list_programs():
            steps = self.store.list_steps(program["id"])
            mine = program.get("for_person_id") == person_id or any(
                step.get("for_person_id") == person_id for step in steps)
            if not mine:
                continue
            summary = self._summary(program, steps)
            to_show = [
                {"step_id": step["id"], "title": step["title"], "pr_number": step.get("pr_number"),
                 "pr_url": step.get("pr_url"), "merged_at": step.get("ended_at")}
                for step in steps
                if step.get("state") in FINISHED_STATES and step.get("pr_number")
                and (since is None or str(step.get("ended_at") or "") > str(since))
            ]
            to_ask = [
                {"step_id": item["step_id"], "title": item["title"], "kind": item["kind"]}
                for item in self._turn(program, steps)
                if item["kind"] in ("finding", "ask_review") and (item.get("for_person_id") == person_id)
            ]
            waits = next((item for item in self._turn(program, steps) if item.get("pr")), None)
            line = f"{program['title']} · {summary['done']} of {summary['total']}"
            if waits and waits.get("pr", {}).get("number"):
                line += f" · PR #{waits['pr']['number']} waits on you"
            out.append({"id": program["id"], "title": program["title"], "state": summary["state"],
                        "state_word": summary["state_word"], "done": summary["done"],
                        "total": summary["total"], "line": line, "to_show": to_show, "to_ask": to_ask})
        return out

    def needs_you_items(self) -> list[dict[str, Any]]:
        """Every Program's your-turn items (``needs_you_membership.program_items``)."""
        items: list[dict[str, Any]] = []
        for program in self.store.list_programs():
            if program["state"] == "done":
                # JRN9 to JRN11: a finished Program still asks to file an
                # audit's findings, to make its fix program, and its lessons.
                items.extend(item for item in self._turn(program, self.store.list_steps(program["id"]))
                             if item["kind"] in ("audit_file", "fix_program", "lesson"))
                continue
            if program["state"] in ("drafting", "parked", "done"):
                continue
            items.extend(self._turn(program, self.store.list_steps(program["id"])))
        return items

    def since_morning(self, principal: Any = None, *, now: Any = None) -> dict[str, int]:
        """Today's Since this morning line (design §9 Seams, PG18): of the
        Programs that moved since the local midnight of ``now`` (the Program
        or one of its steps changed), how many run, wait on him (or failed)
        and are done, and how many of their PRs merged today. ``moved`` is 0
        when none moved (the face draws no line)."""
        from datetime import datetime, timezone

        from ..timestamps import local_now

        local = (now or local_now()).astimezone()
        morning = local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)

        def today(value: Any) -> bool:
            if not value:
                return False
            try:
                at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return False
            return (at if at.tzinfo else at.replace(tzinfo=timezone.utc)) >= morning

        out = {"moved": 0, "running": 0, "waiting": 0, "done": 0, "merged": 0}
        for program in self.store.list_programs():
            steps = self.store.list_steps(program["id"])
            # PG17: an imported step moved when it merged, not when it was
            # written; a Program of imported steps only moves with them.
            imported = bool(steps) and all(history_of(step) for step in steps)
            if not ((today(program.get("updated_at")) and not imported) or any(
                    today(step.get("ended_at") if history_of(step) else step.get("updated_at")) for step in steps)):
                continue
            out["moved"] += 1
            state = self._state(program, steps)
            if state == "running":
                out["running"] += 1
            elif state in ("waiting", "failed"):
                out["waiting"] += 1
            elif state == "done":
                out["done"] += 1
            out["merged"] += sum(1 for step in steps if step.get("state") in FINISHED_STATES
                                 and step.get("pr_number") and today(step.get("ended_at")))
        return out

    def counts_for_project(self, project_id: str) -> dict[str, int]:
        rows = self.for_project(project_id)
        return {
            "running": sum(1 for row in rows if row["state"] == "running"),
            "waiting": sum(1 for row in rows if row["state"] == "waiting"),
            "done": sum(1 for row in rows if row["state"] == "done"),
        }

    # ── the wire ─────────────────────────────────────────────────────

    def _top_steps(self, steps: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        return [step for step in steps if not step.get("race_of")]

    def _summary(self, program: Mapping[str, Any], steps: list[dict[str, Any]], *,
                 requirements: Optional[list[dict[str, Any]]] = None,
                 checkpoints: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
        from .program_requirements import counts as requirement_counts

        top = self._top_steps(steps)
        reqs = requirements if requirements is not None else self.requirements(program["id"])
        checkpoints = checkpoints if checkpoints is not None else self.store.list_checkpoints(program["id"])
        state = self._state(program, steps, requirements=reqs, checkpoints=checkpoints)
        turn = self._turn(program, steps, requirements=reqs, checkpoints=checkpoints)
        # A skipped step lets its dependents run (``_ordinal_finished``) but is
        # never counted done: ``done`` counts merged and done steps only.
        done = sum(1 for step in top if any(row.get("state") in FINISHED_STATES for row in steps
                                            if int(row["ordinal"]) == int(step["ordinal"])))
        skipped = sum(1 for step in top if self._ordinal_finished(steps, step["ordinal"])) - done
        last = checkpoints[0] if checkpoints else None
        summary = {
            "id": program["id"], "title": program["title"], "state": state,
            "state_word": PROGRAM_WORDS.get(state, state), "done": done, "skipped": skipped, "total": len(top),
            "your_turn": len([item for item in turn if item["kind"] != "answer"]),
            "asks": len([item for item in turn if item["kind"] == "answer"]),
            "project_id": program.get("project_id"), "control": program["control"],
            "updated_at": program["updated_at"], "created_at": program["created_at"],
            "last_checkpoint": last,
            "in_state_seconds": _seconds_between(program["updated_at"]),
        }
        if state == "parked":
            # The park's reason (``program.park reason``): the list folds the row.
            parked = next((row for row in checkpoints if row.get("kind") == PARK_KIND), None)
            summary["parked_as"] = (parked or {}).get("choice") or None
        # PG-REQ §7, §11: the count of his required requirements, the Project
        # and the person by name, and the words Find a program matches.
        his = len([item for item in turn if item["kind"] in ("requirement_word", "requirement_left", "todo")])
        met = requirement_counts(reqs, his)
        if met:
            summary["requirements_met"] = met
        place = self._place(program)
        summary["project"] = place["project"]
        summary["for_person"] = place["person"] if place["person"] and place["person"].get("id") else None
        persons = sorted({str(pid) for pid in [program.get("for_person_id"), *(step.get("for_person_id") for step in steps)] if pid})
        summary["persons"] = [{"id": pid, "name": self.person_name(pid)} for pid in persons]
        words = [program.get("title"), program.get("goal_markdown"), (place["project"] or {}).get("name"),
                 program.get("template"), *(row["name"] for row in summary["persons"]),
                 *(step.get("title") for step in top), *(f"#{step['pr_number']}" for step in steps if step.get("pr_number"))]
        from ..program_templates import get_template

        shape = get_template(program.get("template")) if program.get("template") else None
        if shape:
            words.append(shape["name"])
        summary["search_words"] = " ".join(" ".join(str(word).split()) for word in words if word).lower()
        history = history_words(steps)
        if history:
            summary["history"] = history
        if state == "done":
            # PG-IMPORT IMP1 (BroCrew's second mark): finished and needs
            # nothing, or finished and raised a decision (a delivery row, a
            # finding or a proposed step nobody decided). Never the Your
            # turn lamp: the work is not frozen.
            needs = bool(turn) or any(
                (not finding.get("decision") and finding.get("to_owner", True))
                for step in steps for finding in step.get("findings") or []) or any(
                not proposal.get("decision") for step in steps
                for proposal in (step.get("facts") or {}).get("proposed_steps") or [])
            summary["finished"] = "needs_decision" if needs else "finished"
            summary["finished_words"] = FINISHED_WORDS[summary["finished"]]
            ended = max((str(step.get("ended_at") or "") for step in steps), default="") or program["updated_at"]
            began = min(str(program["created_at"]), history["first"]) if history else program["created_at"]
            summary["done_in"] = duration_words(_seconds_between(began, ended))
        # PG-WINDOW List: the list's line in his terms and its mini track.
        from .brief_words import list_line, list_track

        summary["track"] = list_track(top, turn)
        summary["line"] = list_line(state, top, turn, history=history, done_in=summary.get("done_in", ""),
                                    ended=max((str(step.get("ended_at") or "") for step in steps), default="")
                                    or program.get("closed_at") or program["updated_at"])
        if state in ("running", "waiting"):
            # PG-IMPORT IMP3: a step that waits on something the plan cannot
            # give it is the program's line ("Step 4 with Claude Code is
            # waiting on something that has ended."). While the program waits
            # on him, only the held step's own wait replaces its line.
            held = {str(item.get("step_id")) for item in turn[:1]}
            wait = next((found for found in (step_wait(program, step, top) for step in top
                                             if state == "running" or str(step["id"]) in held) if found), None)
            if wait:
                summary["line"] = wait["line"]
        return summary

    def _ordinal_finished(self, steps: Iterable[Mapping[str, Any]], ordinal: int) -> bool:
        rows = [step for step in steps if int(step["ordinal"]) == int(ordinal)]
        return any(step.get("state") in FINISHED_STATES for step in rows) or (
            bool(rows) and all(step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_OWNER
                               for step in rows if not step.get("race_of")))

    def _engine_wire(self, profile: Optional[str], engine_id: Optional[str]) -> Optional[dict[str, Any]]:
        if str(profile or "") != "pi-default":
            return None
        if not engine_id:
            return {"id": None, "label": "the desk's engine for coding", "short": "", "assignment": True}
        found = self.engine(engine_id)
        if found is None:
            return {"id": engine_id, "label": engine_id, "short": engine_id, "missing": True}
        return {"id": engine_id, "label": found.label, "short": found.short_name,
                "model": found.engine.model if found.engine is not None else None}

    def requirement_wire(self, program: Mapping[str, Any], row: Mapping[str, Any], step: Optional[Mapping[str, Any]],
                         requirements: list[dict[str, Any]], his: set[str],
                         steps_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        """One requirement as the faces read it (PG-REQ §11)."""
        from .program_requirements import (
            CHECKING_WORD, COMMIT_BOUND, FROZEN_STEP_STATES, KIND_WORDS, NOT_JUDGED_YET, NOT_MEASURED_WORD, STATE_WORDS,
            WAITS_WORD, label, scope_of,
        )

        state = str(row.get("state") or "not_yet")
        kind = str(row.get("kind") or "review")
        copies = ([other for other in requirements if other.get("parent_id") == row["id"]]
                  if scope_of(row) == "every_step" and not row.get("step_id") else [])
        if copies and state != "waived":
            # An every-step parent reads its copies: Unmet when one is, Met
            # when each is Met or Waived, else Not yet.
            state = ("unmet" if any(other.get("state") == "unmet" for other in copies)
                     else "met" if all(other.get("state") in ("met", "waived") for other in copies) else "not_yet")
        step_state = str((step or {}).get("state") or "")
        running = state == "not_yet" and (
            (kind in ("check", "shot", "measure") and step_state == "checking") or (kind == "review" and step_state == "review"))
        head = (step or {}).get("head_commit")
        stale = bool(step and kind in COMMIT_BOUND and row.get("judged_commit") and head and row["judged_commit"] != head)
        word = CHECKING_WORD if running else (WAITS_WORD if row["id"] in his and state == "not_yet" else STATE_WORDS.get(state, state))
        if (kind in NOT_JUDGED_YET or kind == "measure") and state == "not_yet" and not running:
            word = NOT_MEASURED_WORD  # PG-LANG §6.3: until HoldSpeak measured it
        frozen = bool(program.get("closed_at")) or step_state in FROZEN_STEP_STATES
        if frozen or state == "waived":
            choices: list[str] = []
        elif his_word(row, step):
            choices = ["met", "send_back", "waive"] if state == "unmet" else (["unmet", "waive"] if state == "met" else ["met", "unmet", "waive"])
        elif state == "unmet":
            choices = ["send_back", "waive"] if (step or {}).get("launch_id") else ["waive"]
        else:
            choices = ["waive"]
        evidence = dict(row.get("evidence") or {})
        if evidence.get("kind") in ("log", "shot") and evidence.get("ref"):
            evidence["url"] = f"/api/programs/{program['id']}/requirements/{row['id']}/evidence"
        out = {
            "id": row["id"], "ordinal": int(row["ordinal"]), "label": label(row["ordinal"]),
            "program_id": program["id"], "step_id": row.get("step_id"), "scope": scope_of(row),
            "text": row["text"], "kind": kind, "kind_word": KIND_WORDS.get(kind, kind),
            "required": bool(row.get("required")), "spec": dict(row.get("spec") or {}),
            "parent_id": row.get("parent_id"), "state": state, "state_word": word, "running": running,
            "judged_commit": row.get("judged_commit"), "stale": stale, "evidence": evidence,
            "waived_reason": row.get("waived_reason"), "rounds": int(row.get("rounds") or 0), "by": row.get("by"),
            "choices": choices, "judged_at": row.get("judged_at"), "created_at": row.get("created_at"),
        }
        if copies or (scope_of(row) == "every_step" and not row.get("step_id")):
            out["steps"] = sorted(({"step_id": other["step_id"],
                                    "ordinal": int((steps_by_id.get(other["step_id"]) or {}).get("ordinal") or 0),
                                    "state": other.get("state")} for other in copies), key=lambda item: item["ordinal"])
        return out

    def step_wire(self, program: Mapping[str, Any], step: Mapping[str, Any],
                  checkpoints: list[dict[str, Any]], *, requirements: Optional[list[dict[str, Any]]] = None,
                  his: Optional[set[str]] = None,
                  steps_by_id: Optional[Mapping[str, Mapping[str, Any]]] = None) -> dict[str, Any]:
        profile = step.get("profile") or program.get("default_profile")
        engine_id = step.get("engine") if step.get("profile") else (step.get("engine") or program.get("default_engine"))
        facts = step.get("facts") or {}
        running = facts.get("running_on")
        if isinstance(running, Mapping) and running.get("profile") and step.get("state") not in ("planned", "ready"):
            # PG19: the row names the agent that runs it now (a later entry of
            # its Runs on after a handoff, or when the first was at its limit).
            profile, engine_id = running["profile"], running.get("engine")
        last = next((row for row in checkpoints if row["step_id"] == step["id"]), None)
        state = str(step.get("state") or "")
        word = STEP_WORDS.get(state, state)
        if state == "ready" and step.get("held_reason"):
            word = f"Ready · {step['held_reason']}"
        limit = facts.get("limit") if isinstance(facts.get("limit"), Mapping) else None
        if state == "limited":
            word = limit_words(limit)
        check = facts.get("check") or {}
        return {
            "id": step["id"], "ordinal": step["ordinal"], "title": step["title"], "state": state,
            "state_word": word, "station": _STATION_OF.get(state, -1), "stations": list(STATIONS),
            "brief": step.get("brief_markdown") or "", "owns": list(step.get("owns") or []),
            "after": list(step.get("after") or []), "effort": step.get("effort"),
            "profile": profile, "agent": agent_label(profile), "engine": self._engine_wire(profile, engine_id),
            "prefer_idle": bool(step.get("prefer_idle") or program.get("prefer_idle")),
            "may_call": bool(step.get("may_call") or program.get("may_call")),
            "held_reason": step.get("held_reason"), "race": int(step.get("race") or 0),
            "race_of": step.get("race_of"), "gate": {
                "check": bool(step.get("gate_check")), "review": step.get("gate_review") or "none",
                "review_depth": step.get("review_depth"), "merge": step.get("gate_merge"),
            },
            "launch_id": step.get("launch_id"), "branch": step.get("branch"),
            "worktree": Path(step["worktree"]).name if step.get("worktree") else None,
            "pr": {"number": step.get("pr_number"), "url": step.get("pr_url")} if step.get("pr_url") else None,
            "check": {
                "verdict": step.get("check_verdict"), "log": step.get("check_log"),
                "sections": check.get("sections") or [], "reasons": check.get("reasons") or [],
                "command": check.get("command") or program.get("check_command"),
                "minutes": check.get("minutes"), "commit": step.get("checked_commit"),
                "running": bool(check.get("running")),
            },
            "review": {"verdict": step.get("review_verdict"), "round": facts.get("review_round"),
                       "reviewer": agent_label(facts.get("reviewer_profile")) if facts.get("reviewer_profile") else None},
            "findings": list(step.get("findings") or []), "rounds": int(step.get("rounds") or 0),
            "parked_reason": step.get("parked_reason"), "parked_by": step.get("parked_by"),
            "origin_ref": step.get("origin_ref"), "for_person_id": step.get("for_person_id"),
            "for_person": self.person_name(step.get("for_person_id")) or None,
            # PG-IMPORT IMP1: the report in registers (Checked, The agent
            # says, Not checked, Files); the agent's own text is report_text.
            "report": step_report(step, checkpoints, requirements if requirements is not None
                                  else self.requirements(program["id"])),
            "report_text": step.get("report"), "last_checkpoint": last,
            # PG-IMPORT IMP6: he has the lane (Take it over).
            "taken": isinstance(facts.get("taken"), Mapping),
            # PG-IMPORT IMP3: what it waits on ({cause, line}), or None.
            "wait": step_wait(program, step, list((steps_by_id or {}).values())
                              or self.store.list_steps(program["id"])),
            # PG-IMPORT IMP2: finished | failed | interrupted | none.
            "ending": facts.get("ending") if facts.get("ending") in ENDINGS else "none",
            "started_at": step.get("started_at"), "ended_at": step.get("ended_at"),
            "updated_at": step.get("updated_at"),
            "elapsed_seconds": _seconds_between(step.get("started_at"), step.get("ended_at")),
            "elapsed": duration_words(_seconds_between(step.get("started_at"), step.get("ended_at"))),
            # PG19: the ordered agents, the usage limit it stopped at, and
            # each handoff (with the brief he can read under View brief).
            "runs_on": [self.entry_wire(row) for row in self.runs_on_of(program, step)],
            "limit": {key: limit.get(key) for key in ("until", "words", "rule", "line", "share", "next", "waiting",
                                                       "profile", "seen_at", "auto_at")} if limit and state == "limited" else None,
            "handoffs": [dict(row) for row in step.get("handoffs") or []],
            "history": history_of(step),
            # PG-LANG §5.4: the step's context budget (None: the Program's).
            "budget_tokens": step.get("budget_tokens"),
            # PG-LANG §5.4, §12 (LANG6): a step not handed yet carries its size
            # by rule ({tokens, budget, share, fits, words}); the lamp "18k of 32k".
            "estimate": self._estimate(program, step, profile, engine_id, requirements)
            if step.get("state") in ("planned", "ready") else None,
            **self._step_requirements_wire(program, step, requirements, his, steps_by_id),
        }

    def _estimate(self, program: Mapping[str, Any], step: Mapping[str, Any], profile: Optional[str],
                  engine_id: Optional[str], requirements: Optional[list[dict[str, Any]]]) -> Optional[dict[str, Any]]:
        from .program_sizing import step_estimate

        try:
            return step_estimate(self, program, step, profile=profile, engine_id=engine_id, requirements=requirements)
        except Exception as exc:  # a size is a lamp; it never fails the read
            log.warning(f"program step estimate failed: {exc}")
            return None

    def _step_requirements_wire(self, program: Mapping[str, Any], step: Mapping[str, Any],
                                requirements: Optional[list[dict[str, Any]]], his: Optional[set[str]],
                                steps_by_id: Optional[Mapping[str, Mapping[str, Any]]]) -> dict[str, Any]:
        """PG-REQ §11: a step's own requirements and its every-step copies,
        their count, what he can still change and why the rest is frozen,
        and the lines he added to its brief."""
        from .program_requirements import counts as requirement_counts

        reqs = requirements if requirements is not None else self.requirements(program["id"])
        owner_id = step.get("race_of") or step["id"]
        own = [row for row in reqs if row.get("step_id") == owner_id]
        editable, frozen = step_fields(step)
        out: dict[str, Any] = {
            "requirements": [self.requirement_wire(program, row, step, reqs, his or set(), steps_by_id or {step["id"]: step})
                             for row in own],
            "editable": editable, "frozen": frozen,
            "amendments": [{key: item.get(key) for key in ("at", "by", "line", "sent_at")}
                           for item in (step.get("facts") or {}).get("amendments") or []],
        }
        met = requirement_counts(own)
        if met:
            out["requirements_met"] = met
        return out

    def _place(self, program: Mapping[str, Any]) -> dict[str, Any]:
        """The status bar's place line parts (§9b): project, origin, person."""
        project = None
        if program.get("project_id"):
            with self.db._connection() as conn:
                row = conn.execute("SELECT name FROM projects WHERE id=?", (program["project_id"],)).fetchone()
            project = {"id": program["project_id"], "name": str(row["name"]) if row else program["project_id"]}
        origin = None
        if program.get("origin_ref"):
            kind, _, ident = str(program["origin_ref"]).partition(":")
            title = ""
            try:
                if kind == "automation":
                    # PG14: an automation made it; its place line names it.
                    wb = self.db.workbenches.get(ident, include_deleted=True)
                    title = str(getattr(wb, "name", "") or "")
                elif kind == "program":
                    # JRN1: the Program it was split from (and waits on).
                    title = str((self.store.get_program(ident) or {}).get("title") or "")
                else:
                    from .agent_hand_service import item_title

                    title = item_title(self.db, kind, ident)
            except Exception:
                title = ""
            origin = {"ref": program["origin_ref"], "kind": kind, "id": ident, "title": title}
        person = None
        if program.get("for_person_id"):
            person = {"id": program["for_person_id"], "name": self.person_name(program["for_person_id"])}
        return {"project": project, "origin": origin, "person": person}

    def _wire(self, program: Mapping[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
        from .program_requirements import provable, repository_config

        checkpoints = self.store.list_checkpoints(program["id"])
        reqs = self.requirements(program["id"])
        summary = self._summary(program, steps, requirements=reqs, checkpoints=checkpoints)
        turn = self._turn(program, steps, requirements=reqs, checkpoints=checkpoints)
        # PG-WINDOW: the held items' briefs and the steps' stories, in his terms.
        from .brief_words import window_words

        briefs, stories = window_words(program, steps, turn, checkpoints)
        turn = [{**item, "brief": briefs.get(str(item.get("id")))} for item in turn]
        his = {str(item.get("requirement_id")) for item in turn if item.get("requirement_id")}
        by_id = {step["id"]: step for step in steps}
        top = []
        for step in self._top_steps(steps):
            row = self.step_wire(program, step, checkpoints, requirements=reqs, his=his, steps_by_id=by_id)
            row["story"] = stories.get(str(step["id"]), [])
            row["contenders"] = [{**self.step_wire(program, other, checkpoints, requirements=reqs, his=his, steps_by_id=by_id),
                                  "story": stories.get(str(other["id"]), [])}
                                 for other in steps if other.get("race_of") == step["id"]]
            top.append(row)
        config = repository_config(program.get("repo_root"))
        shot_reason = provable("shot", {"case": "x", "width": 393}, config)
        return {
            **summary,
            "goal": program.get("goal_markdown") or "", "repository": {
                "root": program.get("repo_root"), "label": Path(str(program.get("repo_root") or "")).name,
                "base_branch": program.get("base_branch"),
            },
            "check_command": program.get("check_command"),
            "default": {"profile": program.get("default_profile"), "agent": agent_label(program.get("default_profile")),
                        "engine": self._engine_wire(program.get("default_profile"), program.get("default_engine")),
                        "runs_on": [self.entry_wire(row) for row in self.runs_on_of(program, {})]},
            "allowed_profiles": list(program.get("allowed_profiles") or []),
            "may_handoff": bool(program.get("may_handoff")),
            "usage_warning_share": program.get("usage_warning_share"),
            "reviewer": {"profile": program.get("reviewer_profile"),
                         "agent": agent_label(program.get("reviewer_profile")) if program.get("reviewer_profile") else None,
                         "engine": self._engine_wire(program.get("reviewer_profile"), program.get("reviewer_engine"))},
            "prefer_idle": bool(program.get("prefer_idle")), "template": program.get("template") or None,
            "may_call": bool(program.get("may_call")),
            "origin_ref": program.get("origin_ref"), "for_person_id": program.get("for_person_id"),
            "note_id": program.get("note_id"), "note_window": f"pullout:note:{program['note_id']}" if program.get("note_id") else None,
            "place": self._place(program),
            "steps": top, "checkpoints": checkpoints[:200],
            "your_turn_items": turn,
            # PG-REQ §11: the Program's own (the end check) and the every-step
            # parents, in R order; what this repository can prove.
            "requirements": [self.requirement_wire(program, row, None, reqs, his, by_id)
                             for row in reqs if not row.get("step_id")],
            "can_prove": {"check": True, "review": True, "word": True, "shot": not shot_reason,
                          "shot_reason": shot_reason or None},
            "decided_for_you": self.decided_for_you(program["id"]),
            "control_word": level_word(program.get("control")),
            "spend_limit_usd": program.get("spend_limit_usd"), "closed_at": program.get("closed_at"),
            "revision": int(program.get("revision") or 0),
            "status_line": self._status_line(program, summary),
            **self._language_wire(program),
            **self._audit_wire(program, steps, checkpoints),
        }

    def _audit_wire(self, program: Mapping[str, Any], steps: list[dict[str, Any]],
                    checkpoints: list[dict[str, Any]]) -> dict[str, Any]:
        """PG-LANG JRN9 (journey J7): an audit's Findings board, and the fix
        program its MUST findings made (absent on any other Program)."""
        from . import program_audit

        if not program_audit.is_audit(program):
            return {}
        marks = program_audit.marks_of(checkpoints)
        return {"findings_board": program_audit.board(self._top_steps(steps)),
                "fix_program_id": marks.get("fix_program_id") or None}

    def propose_fix(self, principal: Any, program_id: str) -> dict[str, Any]:
        """PG-LANG JRN10 (``program.propose_fix``): a Program in Drafting from
        the audit's MUST findings, one step each, linked to the audit. It is
        never started here."""
        from . import program_audit

        program = self._program(program_id)
        self._require_writer(principal, program, "propose a fix for")
        with _LOCK:
            return program_audit.propose_fix(self, principal, program["id"])

    def _language_wire(self, program: Mapping[str, Any]) -> dict[str, Any]:
        """PG-LANG (§12, the wire): the fields the Program text writes, and
        its interview rounds."""
        planner = None
        if program.get("planner_engine"):
            found = self.engine(program["planner_engine"])
            planner = {"engine": program["planner_engine"], "label": getattr(found, "label", None) or program["planner_engine"]}
        ref = str(program.get("delivery_ref") or "")
        rounds = []
        for row in self.store.list_rounds(program["id"]):
            # LANG9: a question's why, its offered answers, skipped, and what
            # the answer became; the round's count of changes, its waiting question.
            questions = [{**{key: item.get(key) for key in ("id", "text", "answer", "answered_by", "at", "why")},
                          "choices": list(item.get("choices") or []), "skipped": bool(item.get("skipped")),
                          "became": list(item.get("became") or [])} for item in row["questions"]]
            waits = next((item["id"] for item in questions if not item.get("answer") and not item["skipped"]), None)
            rounds.append({"name": row["name"], "state": row["state"], "order": row["ordinal"], "questions": questions,
                           "asked": len(questions), "answered": sum(1 for item in questions if item.get("answer")),
                           "became": sum(len(item["became"]) for item in questions if item.get("answer")),
                           "waiting": waits})
        return {
            "review_depth": program.get("review_depth"), "planner": planner,
            "budget_tokens": program.get("budget_tokens"), "night": program.get("night"),
            "within": list(program.get("within") or []),
            "delivery": {"kind": "dw", "ref": ref[3:], "linked": False} if ref.startswith("dw:") else None,
            "rounds_before_start": bool(program.get("rounds_before_start")), "rounds": rounds,
        }

    def _status_line(self, program: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
        parts = [summary["state_word"], f"{summary['done']} of {summary['total']} done"]
        if summary.get("skipped"):
            parts.append(f"{summary['skipped']} skipped")
        if summary["your_turn"]:
            parts.append(f"{summary['your_turn']} waits on you")
        if program.get("check_command"):
            parts.append(f"check: {_check_name(str(program['check_command']))}")
        parts.append(f"control {level_word(program['control'])}")
        return " · ".join(parts)

    # ── authority ────────────────────────────────────────────────────

    def _require_writer(self, principal: Any, program: Mapping[str, Any], verb: str) -> None:
        if _is_owner(principal):
            return
        if program.get("created_by") == _creator(principal):
            return
        raise ProgramRefused(
            "not_your_program",
            f"Only the owner, or the agent that made this program, may {verb} it.",
            status=403,
        )

    def _require_owner(self, principal: Any, verb: str) -> None:
        if not _is_owner(principal):
            raise ProgramRefused("owner_required", f"Only the owner may {verb}.", status=403)

    # ── validation ───────────────────────────────────────────────────

    def _profile(self, value: Any, field: str) -> Optional[str]:
        if value in (None, ""):
            return None
        profile = str(value).strip()
        aliases = {"claude": "claude-default", "claude-code": "claude-default", "codex": "codex-default",
                   "pi": "pi-default"}
        profile = aliases.get(profile.lower(), profile)
        if profile not in self._known_profiles():
            raise ProgramRefused("profile_unknown", f"{field}: there is no agent profile {profile!r}.", status=400)
        return profile

    def _engine_id(self, value: Any, profile: Optional[str], field: str, *, optional_missing: bool = False) -> Optional[str]:
        """An engine profile id of the model library, for pi only; refused by name."""
        if value in (None, ""):
            return None
        engine_id = str(value).strip()
        if str(profile or "") != "pi-default":
            raise ProgramRefused("engine_needs_pi", f"{field}: an engine is for pi only; {agent_label(profile)} runs on its own model.", status=400)
        found = self.engine(engine_id)
        if found is None:
            if optional_missing:
                return None
            raise ProgramRefused("engine_unknown", f"{field}: the model library has no engine {engine_id!r}.", status=400)
        if getattr(found, "engine", None) is None:
            raise ProgramRefused("engine_not_compatible", f"{field}: pi cannot run on {found.label!r}; it is not an OpenAI-compatible engine.", status=400)
        return engine_id

    def _runs_on(self, raw: Any, field: str) -> list[dict[str, Any]]:
        """PG19: an ordered list of agents (``[{profile, engine}]``, or names);
        the first runs the role, the rest take it over at a usage limit."""
        if raw in (None, "", []):
            return []
        if isinstance(raw, (str, Mapping)):
            raw = [raw]
        if not isinstance(raw, (list, tuple)):
            raise ProgramRefused("runs_on_invalid", f"{field}: give a list of agents.", status=400)
        out: list[dict[str, Any]] = []
        for index, entry in enumerate(raw, start=1):
            if isinstance(entry, str):
                profile_raw, engine_raw = entry, None
            elif isinstance(entry, Mapping):
                profile_raw, engine_raw = entry.get("profile"), entry.get("engine")
            else:
                raise ProgramRefused("runs_on_invalid", f"{field} {index}: an agent is a name or {{profile, engine}}.", status=400)
            profile = self._profile(profile_raw, f"{field} {index}")
            if not profile:
                raise ProgramRefused("runs_on_invalid", f"{field} {index}: name the agent.", status=400)
            engine = self._engine_id(engine_raw, profile, f"{field} {index} engine") if engine_raw else None
            if any(row["profile"] == profile and row["engine"] == engine for row in out):
                continue
            out.append({"profile": profile, "engine": engine})
        if len(out) > MAX_RUNS_ON:
            raise ProgramRefused("runs_on_too_long", f"{field}: at most {MAX_RUNS_ON} agents.", status=400)
        return out

    def _allowed_profiles(self, raw: Any) -> list[str]:
        """PG19: the agents that may receive this repository's context
        (empty: every agent the desk has)."""
        if raw in (None, "", []):
            return []
        if not isinstance(raw, (list, tuple)):
            raise ProgramRefused("allowed_invalid", "Allowed agents is a list of agents.", status=400)
        out: list[str] = []
        for index, value in enumerate(raw, start=1):
            profile = self._profile(value, f"allowed agent {index}")
            if profile and profile not in out:
                out.append(profile)
        return out

    @staticmethod
    def _share(value: Any) -> Optional[float]:
        if value in (None, "", 0, False):
            return None
        try:
            share = float(value)
        except (TypeError, ValueError):
            raise ProgramRefused("usage_warning_invalid", "The usage warning is a share such as 0.9.", status=400)
        if share > 1:
            share = share / 100.0
        if not 0 < share <= 1:
            raise ProgramRefused("usage_warning_invalid", "The usage warning is a share between 0 and 1.", status=400)
        return share

    def runs_on_of(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> list[dict[str, Any]]:
        """PG19: the step's ordered agents. The step's own list, else its one
        agent then the Program's later entries, else the Program's list."""
        own = [dict(row) for row in step.get("runs_on") or [] if isinstance(row, Mapping) and row.get("profile")]
        if own:
            return own
        default = [dict(row) for row in program.get("default_runs_on") or [] if isinstance(row, Mapping) and row.get("profile")]
        if not default:
            default = [{"profile": program.get("default_profile") or "claude-default",
                        "engine": program.get("default_engine") or None}]
        if step.get("profile"):
            first = {"profile": step["profile"], "engine": step.get("engine") or None}
            return [first] + [row for row in default if (row["profile"], row.get("engine")) != (first["profile"], first["engine"])]
        if step.get("engine") and default[0]["profile"] == "pi-default":
            default[0] = {**default[0], "engine": step["engine"]}
        return default

    def entry_wire(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        """One agent of a Runs on list as the faces read it."""
        profile = str(entry.get("profile") or "")
        engine = self._engine_wire(profile, entry.get("engine"))
        label = agent_label(profile)
        if profile == "pi-default":
            label += f" · {engine.get('short') or engine.get('label')}" if engine and not engine.get("assignment") else " · the desk's assignment"
        return {"profile": profile, "engine": entry.get("engine") or None, "agent": agent_label(profile), "label": label}

    def _repository(self, repository: Any, project_id: Optional[str]) -> tuple[str, Optional[str]]:
        """``(repo_root, project_id)``: a path, else the Project's repository;
        a path with no Project is filed under the Project that owns it."""
        root = ""
        if repository not in (None, ""):
            candidate = Path(str(repository)).expanduser()
            if not candidate.is_dir() or not (candidate / ".git").exists():
                raise ProgramRefused("repository_unknown", "The repository is not a git folder on this machine.", status=400)
            root = str(candidate.resolve())
        elif project_id:
            source = self._project_source(project_id)
            if source is None:
                raise ProgramRefused("no_repository", "The project names no local repository. Register one in the project first.")
            root = str(Path(source.primary_path).resolve())
        else:
            raise ProgramRefused("repository_required", "Name a repository or a project.", status=400)
        if not project_id:
            project_id = self._owning_project(root)
        return root, project_id

    def _project_source(self, project_id: str) -> Any:
        try:
            from .agent_hand_service import default_agent_hand_service, resolve_project_repository
            from ..runtime import composition

            hand = composition.service("agent_hand_service", lambda: default_agent_hand_service(self.db))
            registry = hand._launch_service()._registry
            return resolve_project_repository(self.db, project_id, registry, registrations=hand.repositories)
        except Exception as exc:
            log.info(f"project repository not read: {exc}")
            return None

    def _owning_project(self, root: str) -> Optional[str]:
        """The one Project whose repository is ``root``, else ``None``."""
        try:
            with self.db._connection() as conn:
                ids = [str(row[0]) for row in conn.execute("SELECT id FROM projects WHERE is_archived=0")]
        except Exception:
            return None
        found = []
        for project_id in ids:
            source = self._project_source(project_id)
            if source is not None and source.primary_path and str(Path(source.primary_path).resolve()) == root:
                found.append(project_id)
        return found[0] if len(found) == 1 else None

    @staticmethod
    def _check_command(root: str, given: Any) -> tuple[Optional[str], list[str]]:
        """The repository's check (``.holdspeak/program.json`` ``check``),
        else ``scripts/quick_check.sh`` when present; and its required
        sections."""
        from .program_verifier import QUICK_CHECK_REQUIRED

        config: dict[str, Any] = {}
        try:
            config = json.loads((Path(root) / ".holdspeak" / "program.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            config = {}
        command = str(given or "").strip() or str(config.get("check") or "").strip()
        if not command and (Path(root) / DEFAULT_CHECK).exists():
            command = DEFAULT_CHECK
        sections = config.get("sections")
        if not isinstance(sections, list):
            sections = list(QUICK_CHECK_REQUIRED) if command and command.endswith("quick_check.sh") else []
        return (command or None), [str(s) for s in sections]

    # ── writes ───────────────────────────────────────────────────────

    def create(
        self, principal: Any, *, title: str, goal: str = "", repository: Optional[str] = None,
        project_id: Optional[str] = None, base_branch: Optional[str] = None, control: Optional[str] = None,
        check_command: Optional[str] = None, template: Optional[str] = None,
        default_profile: Optional[str] = None, default_engine: Optional[str] = None,
        reviewer_profile: Optional[str] = None, reviewer_engine: Optional[str] = None,
        prefer_idle: Optional[bool] = None, origin_ref: Optional[str] = None,
        for_person_id: Optional[str] = None, spend_limit_usd: Optional[float] = None,
        runs_on: Any = None, allowed_profiles: Any = None, may_handoff: Optional[bool] = None,
        usage_warning_share: Any = None,
        may_call: Optional[bool] = None,
    ) -> dict[str, Any]:
        from ..program_templates import get_template
        from .program_rules import DESK_MODES

        title = " ".join(str(title or "").split())
        if not title:
            raise ProgramRefused("title_required", "A program needs a title.", status=400)
        shape = get_template(template) if template else None
        if template and shape is None:
            raise ProgramRefused("template_unknown", f"There is no template {template!r}.", status=400)
        defaults = dict((shape or {}).get("program") or {})
        raw_control = str(control or defaults.get("control") or _desk_control_mode()).strip().lower()
        control = DESK_MODES.get(raw_control, "")
        if control not in CONTROLS:
            raise ProgramRefused("control_invalid", "Control is secure, normal or yolo.", status=400)
        # IMP4: an agent's Program is made at most at its own level.
        ceiling = parent_level(principal, self.db)
        capped = wider(control, ceiling)
        if capped:
            control = str(ceiling)
        if spend_limit_usd is not None:
            try:
                spend_limit_usd = float(spend_limit_usd)
            except (TypeError, ValueError):
                raise ProgramRefused("spend_limit_invalid", "The spend limit is a number of dollars.", status=400)
            if spend_limit_usd < 0:
                raise ProgramRefused("spend_limit_invalid", "The spend limit is zero or more dollars.", status=400)
        root, project_id = self._repository(repository, project_id or None)
        profile = self._profile(default_profile, "default_profile") or defaults.get("default_profile") or "claude-default"
        engine = self._engine_id(default_engine, profile, "default_engine") if default_engine else (
            self._engine_id(defaults.get("default_engine"), profile, "default_engine", optional_missing=True)
            if defaults.get("default_engine") else None)
        listed = self._runs_on(runs_on, "runs_on")
        if listed:
            profile, engine = listed[0]["profile"], listed[0]["engine"]
        allowed = self._allowed_profiles(allowed_profiles)
        reviewer = self._profile(reviewer_profile, "reviewer_profile") or defaults.get("reviewer_profile")
        reviewer_engine_id = self._engine_id(reviewer_engine, reviewer, "reviewer_engine") if reviewer_engine else None
        command, _sections = self._check_command(root, check_command)
        if origin_ref:
            kind, _, ident = str(origin_ref).partition(":")
            if not kind or not ident:
                raise ProgramRefused("origin_invalid", "An origin is kind:id (meeting, decision, note, project_item).", status=400)
        now = self._clock()
        program = {
            "id": _new_id("program"), "title": title, "goal_markdown": str(goal or "").strip(),
            "project_id": project_id, "repo_root": root,
            "base_branch": str(base_branch or "").strip() or _base_branch(root),
            "control": control, "spend_limit_usd": spend_limit_usd, "check_command": command, "reviewer_profile": reviewer,
            "reviewer_engine": reviewer_engine_id, "default_profile": profile, "default_engine": engine,
            "prefer_idle": bool(prefer_idle if prefer_idle is not None else defaults.get("prefer_idle")),
            "template": (shape or {}).get("id") or "", "origin_ref": origin_ref or None,
            "for_person_id": for_person_id or None, "created_by": _creator(principal),
            "state": "drafting", "note_id": None, "closed_at": None, "revision": 0, "created_at": now, "updated_at": now,
            "default_runs_on": listed if len(listed) > 1 else [], "allowed_profiles": allowed,
            "may_handoff": bool(may_handoff), "usage_warning_share": self._share(usage_warning_share),
            # Phone (2026-10-28): the engine may call him (not only message him)
            # where the Reach rules allow it; default off, on in Overnight.
            "may_call": bool(may_call if may_call is not None else defaults.get("may_call")),
        }
        language = dict((shape or {}).get("language") or {})
        if language:
            # LANG12: a template's Program lines (Dreaming's night, budget,
            # within, depth, planner); a planner the library lacks, or a
            # bound the repository lacks, is left out.
            if language.get("planner_engine") and self.engine(language["planner_engine"]) is None:
                language.pop("planner_engine")
            if language.get("within"):
                language["within"] = [path for path in language["within"] if (Path(root) / path).exists()]
            self._update_language_fields(program, language)
        with _LOCK:
            self.store.save_program(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent",
                             f"Made the program{' from the ' + shape['name'] + ' template' if shape else ''}")
            if capped:
                self._checkpoint(program, None, "engine", f"Made at {level_word(control)}: a program runs no wider "
                                                          "than what made it", kernel=False)
            self._plant_requirements(program, shape)
            self.changed(program["id"], verb="create")
        return self.get(principal, program["id"])

    def update(self, principal: Any, program_id: str, **fields: Any) -> dict[str, Any]:
        """Change a Program's title, goal, Control level, when idle, Project
        (file an unfiled Program) or default Runs on. The owner, or the agent
        that made it; a Program that runs keeps its repository."""
        from .program_rules import DESK_MODES

        program = self._program(program_id)
        self._require_writer(principal, program, "change")
        changed: list[str] = []
        if "title" in fields and fields["title"] is not None:
            title = " ".join(str(fields["title"]).split())
            if not title:
                raise ProgramRefused("title_required", "A program needs a title.", status=400)
            program["title"] = title
            changed.append("title")
        if "goal" in fields and fields["goal"] is not None:
            program["goal_markdown"] = str(fields["goal"]).strip()
            changed.append("goal")
        if fields.get("control") is not None:
            control = DESK_MODES.get(str(fields["control"]).strip().lower(), "")
            if control not in CONTROLS:
                raise ProgramRefused("control_invalid", "Control is secure, normal or yolo.", status=400)
            if wider(control, parent_level(principal, self.db)) and wider(control, program.get("control")):
                # IMP4: an agent never widens it; the owner can.
                self._checkpoint(program, None, "engine", NO_WIDER, kernel=False)
                raise ProgramRefused("control_wider", f"{NO_WIDER}. Ask the owner.")
            program["control"] = control
            changed.append(f"control {level_word(control)}")
        if fields.get("prefer_idle") is not None:
            program["prefer_idle"] = bool(fields["prefer_idle"])
            changed.append("when idle")
        if fields.get("may_call") is not None:
            program["may_call"] = bool(fields["may_call"])
            changed.append("may call you" if program["may_call"] else "may not call you")
        if fields.get("project_id"):
            project_id = str(fields["project_id"])
            with self.db._connection() as conn:
                if conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
                    raise ProgramRefused("project_unknown", "There is no such project.", status=404)
            program["project_id"] = project_id
            changed.append("project")
        if "spend_limit_usd" in fields:
            value = fields["spend_limit_usd"]
            program["spend_limit_usd"] = None if value in (None, "") else float(value)
            changed.append("spend limit")
        if fields.get("default_profile") is not None or fields.get("default_engine") is not None:
            profile = self._profile(fields.get("default_profile"), "default_profile") or program["default_profile"]
            engine = self._engine_id(fields.get("default_engine"), profile, "default_engine")
            program["default_profile"], program["default_engine"] = profile, engine
            changed.append("Runs on")
        if fields.get("runs_on") is not None:
            listed = self._runs_on(fields["runs_on"], "runs_on")
            if not listed:
                raise ProgramRefused("runs_on_invalid", "runs_on: name at least one agent.", status=400)
            program["default_profile"], program["default_engine"] = listed[0]["profile"], listed[0]["engine"]
            program["default_runs_on"] = listed if len(listed) > 1 else []
            changed.append("agents")
        if fields.get("allowed_profiles") is not None:
            program["allowed_profiles"] = self._allowed_profiles(fields["allowed_profiles"])
            changed.append("allowed agents")
        if fields.get("may_handoff") is not None:
            program["may_handoff"] = bool(fields["may_handoff"])
            changed.append("hand off on its own" if program["may_handoff"] else "hand off on your press")
        if "usage_warning_share" in fields:
            program["usage_warning_share"] = self._share(fields["usage_warning_share"])
            changed.append("usage warning")
        if str(fields.get("reviewer_profile") or "").strip().lower() == "none":
            # PG-LANG: ``reviewer none``, said on purpose: no reviewer.
            program["reviewer_profile"], program["reviewer_engine"] = None, None
            changed.append("no reviewer")
        elif fields.get("reviewer_profile") is not None or fields.get("reviewer_engine") is not None:
            reviewer = self._profile(fields.get("reviewer_profile"), "reviewer_profile") or program.get("reviewer_profile")
            program["reviewer_profile"] = reviewer
            program["reviewer_engine"] = self._engine_id(fields.get("reviewer_engine"), reviewer, "reviewer_engine")
            changed.append("reviewer")
        changed += self._update_language_fields(program, fields)
        if not changed:
            raise ProgramRefused("nothing_to_change", "Name a field to change.", status=400)
        with _LOCK:
            self._touch(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent", "Changed " + ", ".join(changed))
            self.changed(program["id"], verb="update")
        if fields.get("control") is not None and program.get("state") in ("running", "waiting", "failed"):
            # A new level decides what waits at once: YOLO releases a held
            # commit (the tick allows it by rule, or commits the change).
            self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def _update_language_fields(self, program: dict[str, Any], fields: Mapping[str, Any]) -> list[str]:
        """PG-LANG (§3.2, §5.4, §5.5, §6.2, §8): the review depth, the
        planner, the budget, the night, within, delivery, rounds before
        start, the check and the person. A key given as ``None`` clears it."""
        from .program_text import parse_night

        changed: list[str] = []
        if "review_depth" in fields:
            depth = str(fields["review_depth"] or "").strip().lower() or None
            if depth is not None and depth not in REVIEW_DEPTHS:
                raise ProgramRefused("review_depth_invalid", "Depth is glance, delta or standard.", status=400)
            program["review_depth"] = depth
            changed.append("review depth")
        if "planner_engine" in fields:
            engine_id = str(fields["planner_engine"] or "").strip() or None
            if engine_id is not None and self.engine(engine_id) is None:
                raise ProgramRefused("engine_unknown", f"planner: the model library has no engine {engine_id!r}.",
                                     status=400)
            program["planner_engine"] = engine_id
            changed.append("planner")
        if "budget_tokens" in fields:
            program["budget_tokens"] = _budget(fields["budget_tokens"], "The budget")
            changed.append("budget")
        if "night" in fields:
            value = fields["night"]
            if value in (None, "", {}):
                program["night"] = None
            else:
                night = parse_night(value)
                if night is None:
                    raise ProgramRefused("night_invalid", "The night is '23:30–07:00 · at most 8 steps'.", status=400)
                program["night"] = night
            changed.append("night")
        if "within" in fields:
            program["within"] = _within(fields["within"])
            changed.append("within")
        if "delivery" in fields:
            program["delivery_ref"] = _delivery(fields["delivery"], str(program.get("repo_root") or ""))
            changed.append("delivery")
        if fields.get("rounds_before_start") is not None:
            program["rounds_before_start"] = bool(fields["rounds_before_start"])
            changed.append("rounds before start")
        if "check_command" in fields:
            given = fields["check_command"]
            if given in (None, "", "none"):
                program["check_command"] = None
            else:
                program["check_command"], _sections = self._check_command(str(program.get("repo_root") or ""), given)
            changed.append("check")
        if "for_person_id" in fields:
            program["for_person_id"] = fields["for_person_id"] or None
            changed.append("person")
        return changed

    def plan(
        self, principal: Any, program_id: str, *, steps: list[Mapping[str, Any]],
        size: Optional[str] = None, replace: bool = False, before: Optional[str] = None, waits: bool = True,
        by: Optional[str] = None,
    ) -> dict[str, Any]:
        """Replace or append steps. A step: ``title``, ``brief``, ``owns``,
        ``after`` (ordinals), ``profile``, ``engine``, ``prefer_idle``,
        ``effort``, ``race``, ``gate_check``, ``gate_review``
        (none|agent|person), ``review_depth``, ``gate_merge``, ``origin_ref``,
        ``for_person_id``, ``history`` (PG17: ``pr_number``, ``merged_at``,
        ``pr_url``, ``head_commit``: work that merged already; it is written
        Merged, no agent runs it). ``size: auto`` sets effort by rule. A
        Program whose steps are all history is Done at once."""
        from ..program_templates import get_template

        program = self._program(program_id)
        self._require_writer(principal, program, "plan")
        if not isinstance(steps, list) or not steps and not replace:
            raise ProgramRefused("steps_required", "Give at least one step.", status=400)
        existing = self.store.list_steps(program["id"])
        if replace and any(step.get("state") not in ("planned", "ready") for step in existing):
            raise ProgramRefused("program_running", "Steps that started cannot be replaced. Park the program, or append.")
        target = None
        if before:
            # PG-REQ §8, Insert before: the new steps take the target's place.
            if replace:
                raise ProgramRefused("before_invalid", "Insert before adds steps; it does not replace them.", status=400)
            target = self._step(program, str(before))
            if target.get("race_of"):
                target = self._step(program, str(target["race_of"]))
            if target["state"] not in ("planned", "ready"):
                raise ProgramRefused("step_frozen", f"Step {target['ordinal']} started. Add the step after it.",
                                     field="position", reason=FROZEN_SET)
        shape = (get_template(program.get("template")) or {}).get("step") or {}
        start = 0 if replace else max((int(step["ordinal"]) for step in existing), default=0)
        now = self._clock()
        made: list[dict[str, Any]] = []
        for index, raw in enumerate(steps, start=1):
            if not isinstance(raw, Mapping):
                raise ProgramRefused("step_invalid", f"Step {index} is not an object.", status=400)
            title = " ".join(str(raw.get("title") or "").split())
            if not title:
                raise ProgramRefused("step_title_required", f"Step {index} needs a title.", status=400)
            owns = [str(item) for item in raw.get("owns") or [] if str(item).strip()]
            brief = str(raw.get("brief") or raw.get("brief_markdown") or "").strip()
            after = [int(value) for value in raw.get("after") or [] if str(value).strip().lstrip("-").isdigit()]
            ordinal = start + index
            if target is not None:
                # It comes after what the step it precedes came after.
                if any(value >= int(target["ordinal"]) or value < 1 for value in after):
                    raise ProgramRefused("after_invalid", f"Step {index} may only come after an earlier step.", status=400)
                after = sorted(set(after) | set(int(v) for v in target.get("after") or []))
            elif any(value >= ordinal or value < 1 for value in after):
                raise ProgramRefused("after_invalid", f"Step {index} may only come after an earlier step.", status=400)
            listed = self._runs_on(raw.get("runs_on"), f"step {index} runs_on")
            if listed:
                profile, engine = listed[0]["profile"], listed[0]["engine"]
            else:
                profile = self._profile(raw.get("profile"), f"step {index} profile")
                run_profile = profile or program["default_profile"]
                engine = self._engine_id(raw.get("engine"), run_profile, f"step {index} engine") if raw.get("engine") else None
            effort = str(raw.get("effort") or "").strip().lower()
            if size == "auto" or not effort:
                effort = triage_effort(brief, owns) if (size == "auto" or not effort) else effort
            if effort not in EFFORTS:
                raise ProgramRefused("effort_invalid", f"Step {index}: effort is low, medium or high.", status=400)
            race = int(raw.get("race") if raw.get("race") is not None else shape.get("race") or 0)
            if race == 1:
                race = 0
            if race < 0 or race > MAX_RACE:
                raise ProgramRefused("race_invalid", f"Step {index}: a race has 2 or 3 agents.", status=400)
            gate_review = raw.get("gate_review")
            if gate_review is None:
                gate_review = "agent" if (shape.get("gate_review") and program.get("reviewer_profile")) else "none"
            elif gate_review is True:
                gate_review = "agent"
            elif gate_review is False:
                gate_review = "none"
            gate_review = str(gate_review).lower()
            if gate_review not in GATE_REVIEW:
                raise ProgramRefused("gate_review_invalid", f"Step {index}: review is none, agent or person.", status=400)
            for_person = raw.get("for_person_id") or None
            if gate_review == "person" and not (for_person or program.get("for_person_id")):
                raise ProgramRefused("person_required", f"Step {index}: a person review names the person (for_person_id).", status=400)
            depth = str(raw.get("review_depth") or program.get("review_depth") or shape.get("review_depth")
                        or "delta").lower()
            if depth not in REVIEW_DEPTHS:
                raise ProgramRefused("review_depth_invalid", f"Step {index}: depth is glance, delta or standard.", status=400)
            merge = str(raw.get("gate_merge") or shape.get("gate_merge") or "level").lower()
            merge = _GATE_MERGE_ALIASES.get(merge, merge)
            if merge not in GATE_MERGE:
                raise ProgramRefused("gate_merge_invalid", f"Step {index}: merge is level, owner or none.", status=400)
            history = _history_input(raw.get("history"), index)
            made.append({
                "id": _new_id("step"), "program_id": program["id"], "ordinal": ordinal, "title": title,
                "brief_markdown": brief, "owns": owns, "after": after, "profile": profile, "engine": engine,
                "prefer_idle": bool(raw.get("prefer_idle")), "may_call": bool(raw.get("may_call")),
                "effort": effort, "race": race, "race_of": None,
                "gate_check": bool(raw.get("gate_check", shape.get("gate_check", True))),
                "gate_review": gate_review, "review_depth": depth, "gate_merge": merge,
                "state": "planned", "held_reason": None, "launch_id": None, "worktree": None, "branch": None,
                "head_commit": None, "checked_commit": None, "pr_url": None, "pr_number": None,
                "check_log": None, "check_verdict": None, "facts": {}, "review_verdict": None,
                "findings": [], "report": None, "rounds": 0, "parked_reason": None, "parked_by": None,
                "origin_ref": raw.get("origin_ref") or None, "for_person_id": for_person,
                "started_at": None, "ended_at": None, "updated_at": now,
                "runs_on": listed if len(listed) > 1 else [], "handoffs": [],
                "budget_tokens": _budget(raw.get("budget_tokens"), f"Step {index}: the budget"),
            })
            if history:
                # PG17: the merged PR it stands for; no worktree, no hand,
                # no checkpoint of its own; the runner never moves it.
                made[-1].update({
                    "state": "merged", "pr_number": history["pr_number"], "pr_url": history["pr_url"],
                    "head_commit": history["head_commit"], "ended_at": history["merged_at"],
                    "facts": {"history": history},
                })
        kept = [] if replace else existing
        imported = [step for step in made if history_of(step)]
        all_history = bool(made) and all(history_of(step) for step in [*kept, *made])
        with _LOCK:
            if replace:
                for step in existing:
                    self.store.delete_step(step["id"])
            if all_history:
                # Every step merged already: the Program is Done, closed at
                # its last merge.
                for step in made:
                    step["state"] = "done"
                program["state"] = "done"
                program["closed_at"] = max(str(step["ended_at"]) for step in [*kept, *made])
            for step in made:
                self.store.save_step(step)
            by = by or ("owner" if _is_owner(principal) else "agent")
            line = f"{'Planned' if replace else 'Added'} {len(made)} step{'s' if len(made) != 1 else ''}"
            if imported:
                line += f"; imported {len(imported)} merged PR{'s' if len(imported) != 1 else ''}"
            if target is not None:
                if waits:
                    target["after"] = sorted(set(int(v) for v in target.get("after") or [])
                                             | {int(step["ordinal"]) for step in made})
                    self._save(target)
                order = [row["id"] for row in self._top_order(program["id"]) if row["id"] not in {step["id"] for step in made}]
                at = order.index(target["id"])
                order[at:at] = [step["id"] for step in made]
                self._reorder(program, order, by=by)
                line = f"Inserted {len(made)} step{'s' if len(made) != 1 else ''} before step " \
                       f"{(self.store.get_step(target['id']) or target)['ordinal']}"
            self._copy_parents(program, made)
            self._plant_step_requirements(program, made)
            self._checkpoint(program, None, by, line)
            self._touch(program)
            self.changed(program["id"], verb="plan")
        return self.get(principal, program["id"])

    def from_action(self, principal: Any, action_id: Any, *, project_id: Any = None) -> dict[str, Any]:
        """JRN13, Run as a program on a project's action row: a Drafting
        Program made from one action. Its goal is the action's words, its
        origin ``action:<id>`` (its merge closes the action, as From the
        desk's steps do), its Project the action's (so the Project's
        repository), and its person the action's owner when exactly one
        person has that name (never a guess)."""
        ident = str(action_id or "").strip()
        if not ident:
            raise ProgramRefused("action_required", "Name the action (action_id).", status=400)
        item = self.db.meetings.get_action_item(ident)
        if item is None:
            raise ProgramRefused("action_unknown", "There is no such action.", status=404)
        project = str(project_id or "").strip()
        if not project and getattr(item, "meeting_id", None):
            with self.db._connection() as conn:
                row = conn.execute("SELECT project_id FROM meeting_projects WHERE meeting_id=? LIMIT 1",
                                   (item.meeting_id,)).fetchone()
            project = str(row["project_id"]) if row else ""
        person = None
        owner = str(getattr(item, "owner", "") or "").strip()
        if owner:
            try:
                found = self._people_service().resolve_owner_candidates(owner)
                if found.get("link") == "linked" and found.get("relationship"):
                    person = str(found["relationship"].get("id") or "") or None
            except Exception:
                person = None
        words = " ".join(str(item.task or "").split())
        title = words if len(words) <= 80 else words[:79].rsplit(" ", 1)[0] + "…"
        return self.create(principal, title=title or "New program", goal=str(item.task or ""),
                           project_id=project or None, template="fast-cycle", origin_ref=f"action:{ident}",
                           for_person_id=person)

    def plan_from_project(self, principal: Any, program_id: str) -> dict[str, Any]:
        """From the desk (§10, §9b): one step per open action of the Project,
        each with ``origin_ref = action:<id>`` (its merge closes the action)."""
        program = self._program(program_id)
        if not program.get("project_id"):
            raise ProgramRefused("project_required", "From the desk needs a program filed to a project.")
        actions = [item for item in self.db.projects.get_project_action_items(program["project_id"])
                   if str(getattr(item, "status", "open") or "open") in ("open", "pending", "")]
        if not actions:
            raise ProgramRefused("no_open_actions", "The project has no open action.")
        steps = [{"title": str(item.task)[:120], "brief": str(item.task), "origin_ref": f"action:{item.id}"}
                 for item in actions]
        return self.plan(principal, program_id, steps=steps, replace=False)

    def start(self, principal: Any, program_id: str) -> dict[str, Any]:
        program = self._program(program_id)
        self._require_writer(principal, program, "start")
        steps = self.store.list_steps(program["id"])
        if not steps and not program.get("night"):
            # LANG12: a night Program may start empty; its backlog fills it.
            raise ProgramRefused("steps_required", "Add a step before you start the program.")
        if program["state"] not in ("drafting", "parked"):
            raise ProgramRefused("program_started", "The program runs already.")
        refused = self._waits_on(program) or start_precheck(program, self._top_steps(steps), git=self.runner()._git)
        if refused is not None:
            raise refused
        with _LOCK:
            program["state"] = "running"
            self._touch(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent", "Started the program")
            self.changed(program["id"], verb="start")
        self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def park(self, principal: Any, program_id: str, *, reason: Any = None) -> dict[str, Any]:
        """Park a Program (the worktrees stay; Resume brings it back).
        ``reason`` (optional): ``proof`` (a run that proved the engine) or
        ``done_with_it`` (he is done with it); the list folds such a row
        (``parked_as`` on the wire; the face draws the fold)."""
        program = self._program(program_id)
        self._require_writer(principal, program, "park")
        why = str(reason or "").strip().lower().replace("-", "_") or None
        if why is not None and why not in PARK_REASONS:
            raise ProgramRefused("park_reason_invalid", "A park reason is proof or done-with-it.", status=400)
        with _LOCK:
            program["state"] = "parked"
            self._touch(program)
            self.store.add_checkpoint(step_id="", program_id=program["id"], at=self._clock(),
                                      by="owner" if _is_owner(principal) else "agent",
                                      line="Parked the program; the worktrees stay" + (
                                          f" ({PARK_REASONS[why]})" if why else ""),
                                      kind=PARK_KIND, choice=why)
            self.changed(program["id"], verb="park")
        self._revoke_pages(program["id"])
        return self.get(principal, program["id"])

    def _revoke_pages(self, program_id: str) -> int:
        """A parked Program's open briefing pages are revoked (their items
        are retired; a page answers nothing now). The count revoked."""
        try:
            from ..db.briefing import BriefingStore

            store = BriefingStore(self.db)
            now = utc_now_iso()
            pages = store.open_like(f"program:{program_id}:", now)
            for page in pages:
                store.revoke(page["id"], now)
                try:
                    from ..runtime import composition

                    composition.notify_desk_changed("reach", page["id"], "revoked")
                except Exception:
                    pass
            return len(pages)
        except Exception as exc:
            log.warning(f"briefing pages of {program_id} not revoked: {exc}")
            return 0

    def resume(self, principal: Any, program_id: str) -> dict[str, Any]:
        program = self._program(program_id)
        self._require_writer(principal, program, "resume")
        if program["state"] not in ("parked", "failed"):
            raise ProgramRefused("program_not_parked", "Only a parked program resumes.")
        with _LOCK:
            program["state"] = "running"
            for step in self.store.list_steps(program["id"]):
                if step["state"] == "failed":
                    self.transition(program, step, "ready", by="owner", line="Resumed after the failure")
            self._touch(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent", "Resumed the program")
            self.changed(program["id"], verb="resume")
        self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def race(self, principal: Any, program_id: str, step_id: str, n: int) -> dict[str, Any]:
        program = self._program(program_id)
        self._require_writer(principal, program, "race")
        step = self._step(program, step_id)
        n = int(n or 0)
        if n < 2 or n > MAX_RACE:
            raise ProgramRefused("race_invalid", "A race has 2 or 3 agents.", status=400)
        if step["state"] not in ("planned", "ready"):
            raise ProgramRefused("step_started", "A step that started cannot become a race.")
        step["race"] = n
        with _LOCK:
            self._save(step)
            self._checkpoint(program, step, "owner" if _is_owner(principal) else "agent", f"A race of {n} agents")
            self.changed(program["id"], step["id"], verb="race")
        return self.get(principal, program["id"])

    def checkpoint(self, principal: Any, program_id: Optional[str], step_id: str, line: str) -> dict[str, Any]:
        """One line on a step (Orca). The owner on any step; a launch only on
        the step it works."""
        line = " ".join(str(line or "").split())[:400]
        if not line:
            raise ProgramRefused("line_required", "A checkpoint needs words.", status=400)
        step, program = self._own_step(principal, program_id, step_id, "write a checkpoint on")
        with _LOCK:
            row = self._checkpoint(program, step, "owner" if _is_owner(principal) else "agent", line, kernel=False)
            self.changed(program["id"], step["id"], verb="checkpoint")
        return {"program_id": program["id"], "step_id": step["id"], "checkpoint": row}

    def step_done(self, principal: Any, program_id: Optional[str], step_id: str, report: str,
                  follow_ups: Optional[list[Any]] = None) -> dict[str, Any]:
        """The step's launch says it is done, with its report. The engine
        still waits for the commit receipt (design §4)."""
        step, program = self._own_step(principal, program_id, step_id, "report on")
        if _is_owner(principal):
            raise ProgramRefused("launch_only", "Only the step's own agent reports it done.", status=403)
        text = str(report or "").strip()[:20000]
        with _LOCK:
            step["report"] = text
            # 2026-10-31: from here every tick reads the branch head; a new
            # commit (from anyone) moves the step to the check.
            step.setdefault("facts", {})["said_done"] = True
            self._save(step)
            audit = program.get("template") == "audit"
            self._checkpoint(program, step, "agent", "Reported its findings" if audit
                             else "Said it is done; the engine waits for the commit", kernel=False)
            for item in follow_ups or []:
                self.propose_step(program, step, item)
            self.changed(program["id"], step["id"], verb="step_done")
        self._tick_now(program["id"])
        return {"program_id": program["id"], "step_id": step["id"], "state": step["state"],
                "waits_for": "nothing: the engine files the findings" if audit else "a new commit on the step's branch"}

    def propose_step(self, program: dict[str, Any], step: dict[str, Any], item: Any) -> None:
        """A step the plan lacked (an agent names it in its report): YOLO
        adds it and says so; Normal and Secure ask him (design §6)."""
        from .program_rules import decide

        title = " ".join(str((item or {}).get("title") if isinstance(item, Mapping) else item or "").split())[:200]
        if not title:
            return
        brief = str((item or {}).get("brief") or title) if isinstance(item, Mapping) else title
        start_from = dict((item or {}).get("start_from") or {}) if isinstance(item, Mapping) else {}
        outcome = decide(program.get("control"), "add_step", {})
        if outcome.to_owner:
            facts = step.setdefault("facts", {})
            proposal = {"title": title, "brief": brief, "decision": None}
            if start_from:
                proposal["start_from"] = start_from
            facts.setdefault("proposed_steps", []).append(proposal)
            self._save(step)
            self._checkpoint(program, step, "engine",
                             f"The agent asks to start a step from {start_from['ref']}; it is yours to add" if start_from
                             else f"The agent names a missing step: {title}; it is yours to add")
            return
        added = self._added_step(program, step, title, brief, start_from=start_from)
        line = (f"Added step {added['ordinal']} \u201c{title}\u201d from {start_from['ref']} (asked by step {step['ordinal']})"
                if start_from else f"Added step {added['ordinal']} \u201c{title}\u201d (named by step {step['ordinal']})")
        self.engine_decision(program, added, "add_step", outcome, line, undo={"step_id": added["id"]})

    def _added_step(self, program: Mapping[str, Any], step: Mapping[str, Any], title: str, brief: str, *,
                    start_from: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        """A step the plan lacked, with the source step's agent and gates.
        PG20: one that starts from a checkpoint ref has no ``after``: its
        worktree starts at the ref (``program_step_spec``)."""
        ordinal = max((int(row["ordinal"]) for row in self.store.list_steps(program["id"])), default=0) + 1
        now = self._clock()
        facts: dict[str, Any] = {"added_by_engine": True}
        if start_from:
            facts = {"start_from": dict(start_from)}
        added = {
            "id": _new_id("step"), "program_id": program["id"], "ordinal": ordinal, "title": title,
            "brief_markdown": brief, "owns": [], "after": [] if start_from else [int(step["ordinal"])], "profile": step.get("profile"),
            "engine": step.get("engine"), "prefer_idle": bool(step.get("prefer_idle")), "effort": triage_effort(brief, []),
            "race": 0, "race_of": None, "gate_check": True, "gate_review": step.get("gate_review") or "none",
            "review_depth": step.get("review_depth") or "delta", "gate_merge": "level", "state": "planned",
            "held_reason": None, "launch_id": None, "worktree": None, "branch": None, "head_commit": None,
            "checked_commit": None, "pr_url": None, "pr_number": None, "check_log": None, "check_verdict": None,
            "facts": facts, "review_verdict": None, "findings": [], "report": None, "rounds": 0,
            "parked_reason": None, "parked_by": None, "origin_ref": None, "for_person_id": step.get("for_person_id"),
            "started_at": None, "ended_at": None, "updated_at": now,
        }
        self.store.save_step(added)
        self._copy_parents(program, [added])
        return added

    def start_from(self, principal: Any, program_id: str, checkpoint_id: Any) -> dict[str, Any]:
        """PG20, Start from here: a new step whose worktree starts at the
        checkpoint's pinned ref, with the source step's brief and agent.
        His press adds it at once (his press is the consent). The step's own
        agent may ask too; then the ladder decides (``add_step``): Secure and
        Normal ask him, YOLO adds it and says so (Decided for you)."""
        program = self._program(program_id)
        row = next((item for item in self.store.list_checkpoints(program["id"])
                    if str(item["id"]) == str(checkpoint_id)), None)
        if row is None:
            raise ProgramRefused("checkpoint_unknown", "There is no such checkpoint on this program.", status=404)
        if not row.get("ref"):
            raise ProgramRefused("checkpoint_not_pinned", "This checkpoint did not pin the worktree.", status=400)
        source = self.store.get_step(str(row["step_id"] or ""))
        if source is None:
            raise NotFound("program_step", str(row["step_id"]))
        if program.get("closed_at"):
            raise ProgramRefused("program_closed", "The program is closed.")
        owner = _is_owner(principal)
        if not owner and _launch_of(principal) != source.get("launch_id"):
            raise ProgramRefused("not_your_step", "Only this step's own agent, or the owner, may start from its checkpoint.",
                                 status=403)
        ref = str(row["ref"])
        n = ref.rsplit("/", 1)[-1]
        start = {"ref": ref, "commit": row.get("ref_commit"), "checkpoint_id": row["id"], "step_id": source["id"]}
        title = f"{source['title']} (from checkpoint {n})"[:200]
        brief = str(source.get("brief_markdown") or source["title"])
        added_id = None
        with _LOCK:
            if owner:
                added = self._added_step(program, source, title, brief, start_from=start)
                added_id = added["id"]
                self._checkpoint(program, added, "owner", f"Started step {added['ordinal']} from {ref}")
            else:
                self.propose_step(program, source, {"title": title, "brief": brief, "start_from": start})
            self._touch(program)
            self.changed(program["id"], added_id or source["id"], verb="start_from")
        self._tick_now(program["id"])
        return {"step_id": added_id, "ref": ref, "program": self.get(principal, program["id"])}

    def _own_step(self, principal: Any, program_id: Optional[str], step_id: str, verb: str) -> tuple[dict[str, Any], dict[str, Any]]:
        step = self.store.get_step(str(step_id or ""))
        if step is None:
            raise NotFound("program_step", str(step_id))
        program = self._program(step["program_id"])
        if program_id and program_id != program["id"]:
            raise NotFound("program_step", str(step_id))
        if _is_owner(principal):
            return step, program
        caller = _launch_of(principal)
        if caller and caller == step.get("launch_id"):
            return step, program
        raise ProgramRefused("not_your_step", f"Only this step's own agent, or the owner, may {verb} this step.", status=403)

    def answer_agent(self, principal: Any, program_id: str, step_id: str, text: str, *, via: Any = None) -> dict[str, Any]:
        """His answer to the step's agent's question (DIR10: from the page or
        Telegram as text): typed to the agent; one owner line on the step
        ("Answered the agent · decided from the briefing page")."""
        self._require_owner(principal, "answer an agent")
        program = self._program(program_id)
        step = self._step(program, step_id)
        said = " ".join(str(text or "").split())
        if not said:
            raise ProgramRefused("answer_required", "Write your answer.", status=400)
        if step.get("state") != "waiting" or not step.get("launch_id"):
            raise ProgramRefused("not_asking", "The step's agent asks nothing now.")
        token = _VIA.set(via_of(via))
        try:
            self.runner().prompt_builder(step, said)
            with _LOCK:
                self._checkpoint(program, step, "owner", f"Answered the agent: {said[:120]}")
                self.changed(program["id"], step["id"], verb="answer")
        finally:
            _VIA.reset(token)
        return {"answered": True, "step_id": step["id"]}

    def decide(
        self, principal: Any, program_id: str, step_id: str, *, kind: str, choice: str,
        finding_id: Optional[str] = None, reason: Optional[str] = None,
        requirement_id: Optional[str] = None, proposal_id: Any = None, via: Any = None,
    ) -> dict[str, Any]:
        """His press on a your-turn item (owner only). PG-REQ: ``requirement``
        (with ``requirement_id``) and the proposal kinds (with
        ``proposal_id``) go to their own verbs. PG-DIRECTION: ``via`` names
        the channel (desk by default); each owner line the call writes says it
        ("Go on: … · decided from the briefing page") and stores it."""
        token = _VIA.set(via_of(via))
        try:
            return self._decide(principal, program_id, step_id, kind=kind, choice=choice, finding_id=finding_id,
                                reason=reason, requirement_id=requirement_id, proposal_id=proposal_id)
        finally:
            _VIA.reset(token)

    def _decide(
        self, principal: Any, program_id: str, step_id: str, *, kind: str, choice: str,
        finding_id: Optional[str] = None, reason: Optional[str] = None,
        requirement_id: Optional[str] = None, proposal_id: Any = None,
    ) -> dict[str, Any]:
        self._require_owner(principal, "decide")
        program = self._program(program_id)
        kind, choice = str(kind or ""), str(choice or "")
        if kind == "close":
            return self.close(principal, program_id)
        if kind == "delivery":
            from . import program_delivery

            with _LOCK:
                answer = program_delivery.decide(self.runner(), program, choice)
                self.changed(program["id"], verb="delivery")
            return {"delivery": answer, "program": self.get(principal, program["id"])}
        if kind == "requirement":
            if not requirement_id:
                raise ProgramRefused("requirement_required", "Name the requirement (requirement_id).", status=400)
            return self.decide_requirement(principal, program_id, str(requirement_id), choice, line=reason)
        if kind in PROPOSAL_KINDS:
            return self.decide_proposal(principal, program_id, proposal_id if proposal_id is not None else finding_id, choice)
        if kind == "lesson":
            from . import program_lessons

            if choice not in DECIDE_CHOICES[kind]:
                raise ProgramRefused("choice_invalid", f"{kind!r} takes {', '.join(DECIDE_CHOICES[kind])}.", status=400)
            lesson = proposal_id if proposal_id is not None else finding_id
            with _LOCK:
                answer = program_lessons.decide(self, principal, program, lesson, choice)
            self._tick_now(program["id"])
            return {**answer, "program": self.get(principal, program["id"])}
        if kind in ("audit_file", "fix_program"):
            from . import program_audit

            if choice not in DECIDE_CHOICES[kind]:
                raise ProgramRefused("choice_invalid", f"{kind!r} takes {', '.join(DECIDE_CHOICES[kind])}.", status=400)
            with _LOCK:
                answer = program_audit.decide(self, principal, program, kind, choice)
            return {**answer, "program": self.get(principal, program["id"])}
        step = self._step(program, step_id)
        if kind not in DECIDE_CHOICES or choice not in DECIDE_CHOICES[kind]:
            raise ProgramRefused("choice_invalid", f"{kind!r} takes {', '.join(DECIDE_CHOICES.get(kind, ())) or 'nothing'}.", status=400)
        answer: dict[str, Any] = {}
        with _LOCK:
            if kind == "merge":
                if step["state"] not in ("merge_ask", "pr_open"):
                    raise ProgramRefused("not_mergeable", "This step has no PR waiting to merge.")
                if choice == "not_yet":
                    step.setdefault("facts", {})["merge_declined_at"] = self._clock()
                    self.transition(program, step, "pr_open", by="owner", line="Not yet: the PR stays open")
                else:
                    if step.get("gate_review") == "person" and not (step.get("facts") or {}).get("person_approved"):
                        raise ProgramRefused("person_review_missing", "The person has not approved the PR on GitHub yet.")
                    if not self.requirements_met(program, step):
                        raise ProgramRefused("requirements_not_met", "A requirement of this step is not met. Press Met, "
                                             "or waive it.")
                    answer = self.runner().merge(program, step, by="owner")
            elif kind == "finding":
                answer = self._decide_finding(program, step, finding_id, choice, reason)
            elif kind == "parked":
                if step["state"] != "parked":
                    raise ProgramRefused("not_parked", "This step is not parked.")
                if choice == "resume":
                    # Resume is idempotent: a step whose commit is checked green
                    # (parked at its push or PR) goes on from its check, in the
                    # same worktree; any other step is handed again into its
                    # own worktree (``ProgramRunner._hand_step``), never refused
                    # as a duplicate.
                    at_pr = bool(step.get("worktree") and step.get("head_commit")
                                 and step.get("checked_commit") == step.get("head_commit")
                                 and step.get("check_verdict") in ("green", "none"))
                    if not at_pr:
                        step["rounds"] = 0
                    step["parked_by"], step["parked_reason"] = None, None
                    self.transition(program, step, "checking" if at_pr else "ready", by="owner",
                                    line="Resumed the step from its green check" if at_pr else "Resumed the step")
                else:
                    step["parked_by"], step["parked_reason"] = PARKED_BY_OWNER, "You skipped this step"
                    self._save(step)
                    self._checkpoint(program, step, "owner", "Skipped the step")
            elif kind == "ask_review":
                answer = self._prepare_review_ask(principal, program, step)
            elif kind == "core":
                facts = step.setdefault("facts", {})
                core = dict(facts.get("core") or {})
                if not core:
                    raise ProgramRefused("no_core_question", "This step asks nothing of you now.")
                if choice == "go_on":
                    core["cleared"] = True
                    facts.setdefault("core_cleared", []).append(str(core.get("kind") or ""))
                    provisional = core.pop("provisional", None)
                    facts["core"] = core
                    self._save(step)
                    self._checkpoint(program, step, "owner", f"Go on: {core.get('reason')}")
                    if isinstance(provisional, Mapping) and step["state"] == "parked":
                        # PG-DIRECTION DIR4: the step YOLO parked when he said
                        # Later goes on from where it stopped.
                        back = str(provisional.get("from") or "")
                        to = back if back in STEP_TRANSITIONS["parked"] else "ready"
                        step["parked_by"], step["parked_reason"] = None, None
                        self.transition(program, step, to, by="owner", line="Resumed the step from its checkpoint")
                else:
                    facts.pop("core", None)
                    self.transition(program, step, "parked", by="owner", parked_by=PARKED_BY_OWNER,
                                    parked_reason="You parked this step", line=f"Parked: {core.get('reason')}")
            elif kind == "commit":
                answer = self._decide_commit(principal, program, step, choice)
            elif kind == "race":
                facts = step.setdefault("facts", {})
                if not facts.get("awaiting_pick"):
                    raise ProgramRefused("not_a_candidate", "This step is not waiting to win its race.")
                facts["awaiting_pick"] = False
                facts["picked"] = True
                self._save(step)
                self.runner().pass_gate(program, step, by="owner")
            elif kind == "add_step":
                answer = self._decide_add_step(principal, program, step, finding_id, choice)
            elif kind == "limited":
                facts = step.setdefault("facts", {})
                limit = dict(facts.get("limit") or {})
                if step["state"] != "limited" or not limit:
                    raise ProgramRefused("not_limited", "This step's agent is not at its limit.")
                if choice == "wait":
                    limit["waiting"] = True
                    limit.pop("auto_at", None)
                    facts["limit"] = limit
                    self._save(step)
                    until = f" until {limit['words']}" if limit.get("words") else ""
                    self._checkpoint(program, step, "owner", f"Wait for the reset{until}")
                else:
                    nxt = limit.get("next")
                    if not nxt:
                        raise ProgramRefused("no_next_agent", "No other agent may take this step now.")
                    reason = "usage_warning" if limit.get("share") is not None else "usage_limit"
                    answer = {"handoff": self.runner().handoff(program, step, nxt, reason=reason, by="owner")}
            self._touch(program)
            self.changed(program["id"], step["id"], verb="decide")
        self._tick_now(program["id"])
        return {**answer, "program": self.get(principal, program["id"])}

    def later(self, principal: Any, program_id: str, item_id: str, *, until: str, until_words: str,
              via: Any = None) -> dict[str, Any]:
        """PG-DIRECTION DIR4 (DIRECTION-2026-10-31.md §7): his Later on a
        your-turn item. It decides nothing: one ledger line ("Later, back at
        13:00 · from Telegram"). At YOLO only, a core question's step is
        parked for now (Overturnable) and the other steps go on; his Go on at
        the next touch resumes it. A merge, an egress, a buy, a setting and a
        credential are never provisional. ``until`` is kept by the caller
        (``held_later``)."""
        self._require_owner(principal, "decide later")
        program = self._program(program_id)
        steps = self.store.list_steps(program["id"])
        item = next((row for row in self._turn(program, steps) if str(row.get("id")) == str(item_id)), None)
        if item is None:
            raise ProgramRefused("not_waiting", "Nothing waits on you there now.")
        channel = via_of(via)
        parked = False
        with _LOCK:
            step = next((row for row in steps if row["id"] == item.get("step_id")), None)
            line = f"Later, back at {until_words}"
            if channel:
                line = f"{line} \u00b7 {LATER_VIA_WORDS[channel]}"
            self.store.add_checkpoint(step_id=str((step or {}).get("id") or ""), program_id=program["id"],
                                      at=self._clock(), by="owner", line=line[:400], via=channel)
            if (item.get("kind") == "core" and step is not None and str(program.get("control") or "") == "yolo"
                    and step["state"] != "parked" and "parked" in STEP_TRANSITIONS.get(step["state"], ())):
                from types import SimpleNamespace

                facts = step.setdefault("facts", {})
                core = dict(facts.get("core") or {})
                core["provisional"] = {"from": step["state"], "until": until}
                facts["core"] = core
                self.transition(program, step, "parked", by="engine", parked_by=PARKED_BY_ENGINE,
                                parked_reason="Parked for now: you said later")
                self.engine_decision(program, step, "later", SimpleNamespace(
                    choice="park", rule="YOLO: you said later, so the step is parked and the other steps go on",
                    overturnable=True), "Parked for now: you said later")
                parked = True
            self._touch(program)
            self.changed(program["id"], (step or {}).get("id"), verb="later")
        self._tick_now(program["id"])
        return {"program_id": program["id"], "item_id": str(item_id), "until": until, "parked": parked}

    def _decide_commit(self, principal: Any, program: dict[str, Any], step: dict[str, Any], choice: str) -> dict[str, Any]:
        """His press on the agent's held commit. Allow: the gate lets the
        held call run, or, when the hold ended, the engine commits the
        worktree on the step's branch (the next tick reads the new head).
        Not now: the held call is denied and the step parks (Resume)."""
        facts = step.setdefault("facts", {})
        held = facts.get("held_commit") if isinstance(facts.get("held_commit"), Mapping) else None
        if not held and not facts.get("commit_ask"):
            raise ProgramRefused("no_held_commit", "This step has no commit that waits for you.")
        runner = self.runner()
        if choice == "allow":
            if held:
                facts.pop("held_commit", None)
                try:
                    runner.gate().decide(str(held["proposal_id"]), approve=True, reason="Allowed from the program",
                                         principal=principal)
                except Exception as exc:
                    # The hold ended before his press: the engine makes the
                    # commit itself, below.
                    log.info(f"held commit not allowed at the gate: {exc}")
                else:
                    self._save(step)
                    self._checkpoint(program, step, "owner", "Allowed the agent's commit")
                    return {}
                facts["commit_ask"] = {"at": self._clock()}
                self._save(step)
            head = runner.commit_worktree(program, step)
            if not head:
                raise ProgramRefused("commit_failed", "git did not make the commit. Look at the step's worktree.")
            self._checkpoint(program, step, "owner", f"Committed the agent's change ({head[:8]})")
            return {"commit": head}
        if held:
            try:
                runner.gate().decide(str(held["proposal_id"]), approve=False, reason="The owner said not now",
                                     principal=principal)
            except Exception as exc:
                log.info(f"held commit not denied: {exc}")
        facts.pop("held_commit", None)
        facts.pop("commit_ask", None)
        self.transition(program, step, "parked", by="owner", parked_by=PARKED_BY_OWNER,
                        parked_reason="You parked this step; the change stays in the worktree",
                        line="Not now: the commit waits; the step is parked")
        return {}

    def handoff(self, principal: Any, program_id: str, step_id: str, to: Any, *, preview: bool = False) -> dict[str, Any]:
        """PG19, by hand: move a step that holds an agent to ``to`` (a name or
        ``{profile, engine}``) in the same worktree, on the same branch.
        ``preview``: the brief only (what is sent, the redaction counts, the
        earlier turns); nothing moves. Owner only; agents never."""
        self._require_owner(principal, "hand a step to another agent")
        program = self._program(program_id)
        step = self._step(program, step_id)
        listed = self._runs_on([to] if to not in (None, "") else [], "to")
        if not listed:
            raise ProgramRefused("to_required", "Name the agent to continue in.", status=400)
        target = listed[0]
        allowed = list(program.get("allowed_profiles") or [])
        if allowed and target["profile"] not in allowed:
            raise ProgramRefused("agent_not_allowed", f"{agent_label(target['profile'])} may not read this repository.", status=403)
        if step.get("state") not in ("briefed", "working", "waiting", "limited", "check_failed") or not step.get("launch_id"):
            raise ProgramRefused("step_not_running", "Only a step with a running agent can be handed off.")
        runner = self.runner()
        current = runner.current_agent(program, step)
        if (current["profile"], current.get("engine")) == (target["profile"], target.get("engine")):
            raise ProgramRefused("same_agent", f"The step already runs on {agent_label(target['profile'])}.", status=400)
        if preview:
            from .program_handoff import redacted_words

            brief = runner.handoff_brief(program, step, target, reason="by_hand", by="owner")
            return {"preview": True, "from": self.entry_wire(current), "to": self.entry_wire(target),
                    "brief": brief.text, "redacted": dict(brief.redacted), "redacted_words": redacted_words(brief.redacted),
                    "earlier_turns": brief.earlier_turns, "bytes": len(brief.text.encode("utf-8"))}
        with _LOCK:
            entry = runner.handoff(program, step, target, reason="by_hand", by="owner")
            self._touch(program)
            self.changed(program["id"], step["id"], verb="handoff")
        self._tick_now(program["id"])
        return {"handoff": {key: value for key, value in entry.items() if key != "brief"},
                "program": self.get(principal, program["id"])}

    def close(self, principal: Any, program_id: str) -> dict[str, Any]:
        """He closes a finished Program (Secure: Done is his press)."""
        self._require_owner(principal, "close a program")
        program = self._program(program_id)
        if _live(self.store.list_steps(program["id"])):
            raise ProgramRefused("program_not_finished", "Steps still run; park them or wait.")
        with _LOCK:
            program["closed_at"] = self._clock()
            self._close_history(program)
            self._touch(program)
            self._checkpoint(program, None, "owner", "Closed the program")
            self.changed(program["id"], verb="close")
        return {"program": self.get(principal, program["id"])}

    def _decide_add_step(self, principal: Any, program: dict[str, Any], step: dict[str, Any],
                         index: Any, choice: str) -> dict[str, Any]:
        facts = step.setdefault("facts", {})
        proposals = list(facts.get("proposed_steps") or [])
        try:
            proposal = proposals[int(index or 0)]
        except (ValueError, IndexError):
            raise ProgramRefused("proposal_unknown", "There is no such proposed step.", status=404)
        proposal["decision"] = choice
        facts["proposed_steps"] = proposals
        self._save(step)
        if choice == "add" and proposal.get("start_from"):
            # PG20: an agent's Start from here, added on his press.
            added = self._added_step(program, step, proposal["title"], proposal.get("brief") or proposal["title"],
                                     start_from=proposal["start_from"])
            self._checkpoint(program, added, "owner", f"Started step {added['ordinal']} from {proposal['start_from']['ref']}")
            return {"added": added["id"]}
        if choice == "add":
            made = self.plan(principal, program["id"], steps=[{"title": proposal["title"],
                                                               "brief": proposal.get("brief") or proposal["title"],
                                                               "after": [int(step["ordinal"])]}])
            return {"added": made["steps"][-1]["id"]}
        self._checkpoint(program, step, "owner", f"Did not add: {proposal['title']}")
        return {}

    # ── PG-REQ: requirements (§3 to §6) ──────────────────────────────

    def _requirement_input(self, program: Mapping[str, Any], text: Any, kind: Any, spec: Any) -> dict[str, Any]:
        """A validated ``{text, kind, spec}``; the kind by rule when he names
        none (decision 5). A requirement with no way to be proven here is
        refused by name (a core question at every level, §4)."""
        from .program_requirements import KINDS, RequirementInvalid, clean_spec, clean_text, guess, provable, repository_config
        from .program_rules import decide

        words = clean_text(text)
        if not words:
            raise ProgramRefused("text_required", "A requirement is one sentence.", status=400)
        chosen = str(kind or "").strip().lower().replace(" ", "_")
        chosen = {"your_word": "word", "owner": "word"}.get(chosen, chosen) or guess(words)[0]
        if chosen not in KINDS:
            raise ProgramRefused("kind_invalid", "A requirement is a check, a review, a shot or your word.", status=400)
        try:
            cleaned = clean_spec(chosen, spec, words)
        except RequirementInvalid as exc:
            raise ProgramRefused(exc.code, exc.detail, status=400)
        why = provable(chosen, cleaned, repository_config(program.get("repo_root")))
        if why:
            outcome = decide(program.get("control"), "requirement_unprovable", {})
            raise ProgramRefused("requirement_unprovable", f"{why}.", status=409, rule=getattr(outcome, "rule", None))
        return {"text": words, "kind": chosen, "spec": cleaned}

    def _frozen_step(self, step: Optional[Mapping[str, Any]], field: str = "requirements") -> None:
        if step is None:
            return
        _editable, frozen = step_fields(step)
        if field in frozen:
            extra = " Add it to the program instead." if field == "requirements" else ""
            raise ProgramRefused("step_frozen", f"Step {step['ordinal']}: {frozen[field]}.{extra}", field=field,
                                 reason=frozen[field])

    def _new_requirement(self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], data: Mapping[str, Any], *,
                         each_step: bool, required: bool, by: str) -> dict[str, Any]:
        now = self._clock()
        row = {
            "id": _new_id("req"), "program_id": program["id"], "step_id": step["id"] if step else None,
            "ordinal": self.store.next_requirement_ordinal(program["id"]), "text": data["text"], "kind": data["kind"],
            "required": bool(required), "spec": dict(data.get("spec") or {}), "each_step": bool(each_step and not step),
            "parent_id": None, "state": "not_yet", "judged_commit": None, "evidence": {}, "waived_reason": None,
            "rounds": 0, "by": by, "created_at": now, "updated_at": now, "judged_at": None,
        }
        self.store.save_requirement(row)
        if row["each_step"]:
            self._copy_parent(program, row, self.store.list_steps(program["id"]))
        return row

    def _copy_parent(self, program: Mapping[str, Any], parent: Mapping[str, Any], steps: Iterable[Mapping[str, Any]]) -> None:
        """An every-step requirement on each step that can still be judged
        (a merged step is history)."""
        have = {row["step_id"] for row in self.requirements(program["id"]) if row.get("parent_id") == parent["id"]}
        now = self._clock()
        for step in steps:
            if step.get("race_of") or step["id"] in have or step.get("state") in ("merged", "done") or history_of(step):
                continue
            self.store.save_requirement({
                **parent, "id": _new_id("req"), "step_id": step["id"], "parent_id": parent["id"], "each_step": True,
                "state": "not_yet", "judged_commit": None, "evidence": {}, "waived_reason": None, "rounds": 0,
                "created_at": now, "updated_at": now, "judged_at": None,
            })

    def _copy_parents(self, program: Mapping[str, Any], steps: Iterable[Mapping[str, Any]]) -> None:
        """New steps get every every-step requirement of the Program."""
        steps = list(steps)
        for parent in self.requirements(program["id"]):
            if not parent.get("step_id") and parent.get("each_step") and parent.get("state") != "waived":
                self._copy_parent(program, parent, steps)

    def _requirement_line(self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], by: str, line: str,
                          requirement_ids: Iterable[str], *, kernel: bool = False) -> None:
        operation_id = self._kernel_record(program, step, line) if kernel and by == "engine" else None
        ids = [str(rid) for rid in requirement_ids]
        undo: dict[str, Any] = {"requirement_id": ids[0]} if len(ids) == 1 else {"requirement_ids": ids}
        seen = seen_of(step) if by == "engine" else None
        if seen:
            undo["seen"] = seen
        line, via = _via_line(by, line[:400])
        self.store.add_checkpoint(step_id=str((step or {}).get("id") or ""), program_id=program["id"], at=self._clock(),
                                  by=by, line=line, operation_id=operation_id, kind="requirement", undo=undo, via=via)

    def require(
        self, principal: Any, program_id: str, *, text: Any = None, kind: Any = None, step_id: Any = None,
        each_step: Any = False, required: Any = True, spec: Any = None, requirement_id: Any = None,
    ) -> dict[str, Any]:
        """Add a requirement (PG-REQ §6): his at once; an orchestrating agent's
        or a step's own agent's goes up the ladder (``requirement_proposed``:
        YOLO adds it and says so, Secure and Normal ask him). With
        ``requirement_id`` it is an edit (his only)."""
        from .program_requirements import label
        from .program_rules import decide

        if requirement_id:
            return self.edit_requirement(principal, program_id, str(requirement_id), text=text, kind=kind,
                                         required=required if required is not True else None, spec=spec)
        program = self._program(program_id)
        if program.get("closed_at"):
            raise ProgramRefused("program_closed", "The program is closed.")
        step = self._step(program, str(step_id)) if step_id else None
        if step is not None and step.get("race_of"):
            step = self._step(program, str(step["race_of"]))
        if step is not None and each_step:
            raise ProgramRefused("scope_invalid", "Every step is a program requirement: name no step.", status=400)
        owner = _is_owner(principal)
        if not owner:
            mine = program.get("created_by") == _creator(principal) or (
                step is not None and _launch_of(principal) and _launch_of(principal) == step.get("launch_id"))
            if not mine:
                raise ProgramRefused("not_your_program", "Only the owner, the agent that made this program, or a "
                                     "step's own agent may propose a requirement.", status=403)
        self._frozen_step(step)
        data = self._requirement_input(program, text, kind, spec)
        where = f"step {step['ordinal']}" if step else ("every step" if each_step else "the program")
        answer: dict[str, Any] = {}
        with _LOCK:
            if owner:
                row = self._new_requirement(program, step, data, each_step=bool(each_step), required=bool(required), by="owner")
                self._requirement_line(program, step, "owner", f"Added {label(row['ordinal'])} on {where} · {row['text']}", [row["id"]])
            else:
                outcome = decide(program.get("control"), "requirement_proposed", {})
                who = agent_label(getattr(principal, "profile", None)) if getattr(principal, "profile", None) else "An agent"
                title = f"{who} proposes a requirement on {where}: {data['text']}"
                if outcome.to_owner:
                    proposal = self.store.add_checkpoint(
                        step_id=str((step or {}).get("id") or ""), program_id=program["id"], at=self._clock(), by="agent",
                        line=title[:400], kind="requirement_proposed",
                        undo={"title": title, "text": data["text"], "kind": data["kind"], "spec": data["spec"],
                              "step_id": (step or {}).get("id"), "each_step": bool(each_step), "required": bool(required)})
                    self._touch(program)
                    self.changed(program["id"], (step or {}).get("id"), verb="require")
                    return {"proposed": proposal, "program": self.get(principal, program["id"])}
                row = self._new_requirement(program, step, data, each_step=bool(each_step), required=bool(required), by="agent")
                self.engine_decision(program, step, "requirement_proposed", outcome,
                                     f"Added {label(row['ordinal'])} on {where} that an agent proposed: {row['text']}",
                                     undo={"requirement_id": row["id"]})
            self._requirement_added(program, step, row)
            self._touch(program)
            self.changed(program["id"], (step or {}).get("id"), verb="require", requirement_id=row["id"])
        self._tick_now(program["id"])
        answer["requirement_id"] = row["id"]
        answer["program"] = self.get(principal, program["id"])
        return answer

    def _plant_requirements(self, program: Mapping[str, Any], shape: Optional[Mapping[str, Any]]) -> None:
        """PG-REQ §10: the template's requirements and the repository's own
        defaults (``.holdspeak/program.json`` ``requirements``), ``by =
        template``. A Review plants only where the steps are reviewed."""
        from ..program_templates import requirements_for, reviewed
        from .program_requirements import repository_config

        review = reviewed(dict(shape)) if shape else False
        items = requirements_for(dict(shape), review=review) if shape else []
        for raw in repository_config(program.get("repo_root")).get("requirements") or []:
            if isinstance(raw, Mapping) and (raw.get("kind") != "review" or review):
                items.append(dict(raw))
        for item in items:
            try:
                data = self._requirement_input(program, item.get("text"), item.get("kind"), item.get("spec"))
            except ProgramRefused as exc:
                log.info(f"a default requirement was not planted ({exc.code}): {item.get('text')}")
                continue
            self._new_requirement(program, None, data, each_step=bool(item.get("each_step", True)),
                                  required=bool(item.get("required", True)), by="template")

    def _plant_step_requirements(self, program: Mapping[str, Any], steps: Iterable[Mapping[str, Any]]) -> None:
        """From the desk (§10): one Review per step from its origin, where
        the step is reviewed."""
        from ..program_templates import get_template

        shape = get_template(program.get("template")) if program.get("template") else None
        for item in (shape or {}).get("step_requirements") or []:
            for step in steps:
                if step.get("gate_review") != "agent" or not str(step.get("origin_ref") or "").startswith("action:"):
                    continue
                try:
                    data = self._requirement_input(program, str(item["text"]).replace("{title}", step["title"]),
                                                   item.get("kind"), None)
                except ProgramRefused:
                    continue
                self._new_requirement(program, step, data, each_step=False, required=bool(item.get("required", True)),
                                      by="template")

    def _requirement_added(self, program: Mapping[str, Any], step: Optional[dict[str, Any]], row: Mapping[str, Any]) -> None:
        """A requirement added after the step's gate passed is judged on the
        PR head (§6): the step goes back through CHECK on the same commit."""
        if step is None or row.get("kind") == "word" or step.get("state") not in ("pr_open", "merge_ask"):
            return
        from .program_requirements import label

        self.transition(program, step, "checking", by="engine",
                        line=f"{label(row['ordinal'])} is judged on the PR head")

    def edit_requirement(self, principal: Any, program_id: str, requirement_id: str, *, text: Any = None,
                         kind: Any = None, required: Any = None, spec: Any = None) -> dict[str, Any]:
        """His edit (§4): a changed sentence, kind, command or window sets a
        Met or Unmet requirement to Not yet. Agents propose; they do not
        edit his requirements (the bar is his)."""
        from .program_requirements import label

        self._require_owner(principal, "change a requirement")
        program = self._program(program_id)
        row = self._requirement(program, requirement_id)
        step = self.store.get_step(row["step_id"]) if row.get("step_id") else None
        self._frozen_step(step)
        changed: list[str] = []
        if text is not None or kind is not None or spec is not None:
            data = self._requirement_input(program, text if text is not None else row["text"],
                                           kind if kind is not None else (row["kind"] if text is None else row["kind"]),
                                           spec if spec is not None else (row.get("spec") if kind is None else None))
            if (data["text"], data["kind"], data["spec"]) != (row["text"], row["kind"], dict(row.get("spec") or {})):
                row.update(data)
                changed.append("the sentence" if text is not None else "how it is proven")
        if required is not None and bool(required) != bool(row.get("required")):
            row["required"] = bool(required)
            changed.append("required" if row["required"] else "not required")
        if not changed:
            raise ProgramRefused("nothing_to_change", "Name a field to change.", status=400)
        reset = "the sentence" in changed or "how it is proven" in changed
        with _LOCK:
            targets = [row] + ([other for other in self.requirements(program["id"]) if other.get("parent_id") == row["id"]]
                               if not row.get("step_id") and row.get("each_step") else [])
            for target in targets:
                target_step = step if target is row else self.store.get_step(str(target.get("step_id") or ""))
                if target is not row and target_step is not None and step_fields(target_step)[1].get("requirements"):
                    continue
                if target is not row:
                    target.update({key: row[key] for key in ("text", "kind", "spec", "required")})
                if reset and target.get("state") in ("met", "unmet"):
                    target.update({"state": "not_yet", "evidence": {}, "judged_commit": None, "judged_at": None})
                target["updated_at"] = self._clock()
                self.store.save_requirement(target)
                if reset and target_step is not None:
                    self._requirement_added(program, target_step, target)
            self._requirement_line(program, step, "owner", f"Changed {label(row['ordinal'])}: " + ", ".join(changed), [row["id"]])
            self._touch(program)
            self.changed(program["id"], row.get("step_id"), verb="require", requirement_id=row["id"])
        self._tick_now(program["id"])
        return {"requirement_id": row["id"], "program": self.get(principal, program["id"])}

    def _requirement(self, program: Mapping[str, Any], requirement_id: str) -> dict[str, Any]:
        row = self.store.get_requirement(str(requirement_id or ""))
        if row is None or row["program_id"] != program["id"]:
            raise NotFound("program_requirement", str(requirement_id))
        return row

    def judge(self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], row: dict[str, Any], state: str,
              evidence: Mapping[str, Any], *, by: str = "engine") -> dict[str, Any]:
        """One judgement on a receipt (§4): the state, the evidence with the
        commit it was judged on, a checkpoint line ``kind = requirement``."""
        from .program_requirements import STATE_WORDS, label

        now = self._clock()
        row.update({"state": state, "evidence": {**dict(evidence), "by": evidence.get("by") or by, "at": now},
                    "judged_commit": evidence.get("commit") or row.get("judged_commit"), "judged_at": now,
                    "updated_at": now})
        if state == "unmet":
            row["rounds"] = int(row.get("rounds") or 0) + 1
        self.store.save_requirement(row)
        tail = f" · {evidence.get('line')}" if evidence.get("line") else ""
        self._requirement_line(program, step, by, f"{label(row['ordinal'])} · {STATE_WORDS.get(state, state)}{tail}",
                               [row["id"]], kernel=True)
        return row

    def requirements_moved(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> None:
        """Decision 4: the step's head commit moved; every Met or Unmet of
        kind check, shot and review goes back to Not yet (his word stays)."""
        from .program_requirements import COMMIT_BOUND, label

        head = step.get("head_commit")
        moved = []
        for row in self.requirements(program["id"]):
            if row.get("step_id") != (step.get("race_of") or step["id"]) or row.get("kind") not in COMMIT_BOUND:
                continue
            if row.get("state") in ("met", "unmet") and row.get("judged_commit") != head:
                row.update({"state": "not_yet", "updated_at": self._clock()})
                self.store.save_requirement(row)
                moved.append(row)
        if moved:
            labels = ", ".join(label(row["ordinal"]) for row in moved)
            self._requirement_line(program, step, "engine", f"The commit moved: {labels} {'is' if len(moved) == 1 else 'are'} "
                                   "judged again", [row["id"] for row in moved])

    def step_requirements(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> list[dict[str, Any]]:
        owner_id = step.get("race_of") or step["id"]
        return [row for row in self.requirements(program["id"]) if row.get("step_id") == owner_id]

    def requirements_met(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> bool:
        """The merge's fact (§6): every required requirement of the step is
        Met or Waived."""
        from .program_requirements import gates

        return not any(gates(row) for row in self.step_requirements(program, step))

    def decide_requirement(self, principal: Any, program_id: str, requirement_id: str, choice: str,
                           line: Optional[str] = None) -> dict[str, Any]:
        """His press on a requirement (owner only): Met or Unmet for his
        word; Waive (with his line, the evidence) and Send back (one more
        round, even after the rounds ran out) for any."""
        from .program_requirements import label

        self._require_owner(principal, "decide a requirement")
        program = self._program(program_id)
        row = self._requirement(program, requirement_id)
        choice = str(choice or "")
        if choice not in DECIDE_CHOICES["requirement"]:
            raise ProgramRefused("choice_invalid", f"A requirement takes {', '.join(DECIDE_CHOICES['requirement'])}.", status=400)
        if row.get("state") == "waived":
            raise ProgramRefused("requirement_waived", f"{label(row['ordinal'])} is waived.")
        step = self.store.get_step(row["step_id"]) if row.get("step_id") else None
        if step is not None and step.get("state") in ("merged", "done"):
            raise ProgramRefused("step_frozen", f"Step {step['ordinal']}: {FROZEN_MERGED}.", field="requirements",
                                 reason=FROZEN_MERGED)
        words = " ".join(str(line or "").split())[:400]
        commit = (step or {}).get("head_commit")
        if choice in ("done", "cant"):
            if row.get("kind") != "word":
                raise ProgramRefused("not_a_todo", f"{label(row['ordinal'])} is not a thing you do by hand.")
            with _LOCK:
                self._answer_todo(program, step, row, choice == "done", words, commit)
                self._touch(program)
                self.changed(program["id"], (step or {}).get("id"), verb="judge", requirement_id=row["id"])
            self._tick_now(program["id"])
            return {"requirement_id": row["id"], "program": self.get(principal, program["id"])}
        with _LOCK:
            if choice in ("met", "unmet"):
                if not his_word(row, step):
                    raise ProgramRefused("not_his_word", "HoldSpeak judges this requirement on the commit. Waive it, "
                                         "or send it back.")
                said = f"You · {_clock_words(self._clock())}" + (f" · {words}" if words else "")
                self.judge(program, step, row, choice, {"kind": "press", "line": said, "commit": commit}, by="owner")
                if choice == "unmet" and step is not None and step.get("launch_id"):
                    self._send_back(program, step, row, words)
            elif choice == "waive":
                if not words:
                    raise ProgramRefused("line_required", "Say in one line why you waive it.", status=400)
                self._waive(program, row, words)
                if step is not None:
                    self._after_waive(program, self.store.get_step(step["id"]) or step, row)
            else:
                if step is None or not step.get("launch_id"):
                    raise ProgramRefused("no_builder", f"{label(row['ordinal'])} has no agent to send it to.")
                self._send_back(program, step, row, words)
            self._touch(program)
            self.changed(program["id"], (step or {}).get("id"), verb="waive" if choice == "waive" else "judge",
                         requirement_id=row["id"])
        self._tick_now(program["id"])
        return {"requirement_id": row["id"], "program": self.get(principal, program["id"])}

    def _answer_todo(self, program: dict[str, Any], step: Optional[dict[str, Any]], row: dict[str, Any], done: bool,
                     note: str, commit: Any) -> None:
        """PG-IMPORT IMP2: his answer to a to-do. Done writes the requirement
        Met (his word, his note the evidence); Can't do it writes it Unmet with
        his note and puts it on the step's left list (Send back or Waive is
        his next choice). The agent is told in the step's next prompt."""
        from .program_requirements import label

        said = f"You · {_clock_words(self._clock())}" + (f" · {note}" if note else "")
        self.judge(program, step, row, "met" if done else "unmet", {"kind": "press", "line": said, "commit": commit},
                   by="owner")
        if step is None:
            return
        step = self.store.get_step(step["id"]) or step
        if not done:
            facts = step.setdefault("facts", {})
            left = [rid for rid in facts.get("requirements_left") or [] if rid != row["id"]]
            facts["requirements_left"] = [*left, row["id"]]
            self._save(step)
        text = (f"The owner did {label(row['ordinal'])} by hand: {row['text']}. Done." if done
                else f"The owner cannot do {label(row['ordinal'])} by hand: {row['text']}.") + (f" The owner: {note}" if note else "")
        self._tell_agent(program, step, text)

    def _tell_agent(self, program: Mapping[str, Any], step: dict[str, Any], text: str) -> None:
        """One line for the step's agent at its next prompt: a running step
        gets it at its next turn boundary (the amendment queue); a step at its
        PR gets it typed now. No agent: the ledger keeps it."""
        if step.get("state") in _STARTED:
            self._apply_amend(program, step, text, by="owner")
            return
        if step.get("launch_id") and step.get("state") in ("pr_open", "merge_ask"):
            try:
                self.runner().prompt_builder(step, f"HoldSpeak on step {step['ordinal']}: {text}")
            except Exception as exc:
                log.info(f"to-do answer not typed: {exc}")

    def _waive(self, program: Mapping[str, Any], row: dict[str, Any], line: str) -> None:
        from .program_requirements import label

        targets = [row]
        if not row.get("step_id") and row.get("each_step"):
            targets += [other for other in self.requirements(program["id"])
                        if other.get("parent_id") == row["id"] and other.get("state") != "met"]
        now = self._clock()
        for target in targets:
            target.update({"state": "waived", "waived_reason": line, "updated_at": now, "judged_at": now,
                           "evidence": {"kind": "press", "line": line, "by": "owner", "at": now,
                                        "commit": target.get("judged_commit")}})
            self.store.save_requirement(target)
        step = self.store.get_step(row["step_id"]) if row.get("step_id") else None
        self._requirement_line(program, step, "owner", f"Waived {label(row['ordinal'])}: {line}", [row["id"]])

    def _after_waive(self, program: dict[str, Any], step: dict[str, Any], row: Mapping[str, Any]) -> None:
        """A waived requirement no longer gates: a step parked on it goes on;
        a finding it made is decided."""
        from .program_requirements import judged

        facts = step.setdefault("facts", {})
        left = [rid for rid in facts.get("requirements_left") or [] if rid != row["id"]]
        by_id = {other["id"]: other for other in self.requirements(program["id"])}
        left = [rid for rid in left if rid in by_id and not judged(by_id[rid])]
        if facts.get("requirements_left") and not left:
            facts["requirements_left"] = []
            if step["state"] == "parked":
                self.transition(program, step, "checking", by="owner", parked_by=None, parked_reason=None, facts=facts,
                                line="The requirement is waived; the step goes on")
                return
        facts["requirements_left"] = left
        findings = list(step.get("findings") or [])
        touched = False
        for finding in findings:
            if finding.get("requirement_id") == row["id"] and not finding.get("decision"):
                finding.update({"decision": "waive", "decided_at": self._clock(), "to_owner": False})
                touched = True
        step["findings"] = findings
        self._save(step)
        if touched and step["state"] == "findings" and all(item.get("decision") or not item.get("to_owner", True)
                                                            for item in findings):
            facts["findings_open"] = False
            self._after_findings(program, step, findings)

    def _send_back(self, program: dict[str, Any], step: dict[str, Any], row: Mapping[str, Any], line: str) -> None:
        """Send back (§6): one line to the builder ("R5 is unmet: <the
        evidence>. <his line>") and one more round, even after the rounds ran
        out."""
        from .program_requirements import label

        evidence = str((row.get("evidence") or {}).get("line") or "").strip()
        text = (f"HoldSpeak on step {step['ordinal']}: {label(row['ordinal'])} is unmet: {row['text']}"
                + (f" ({evidence})" if evidence else "") + "."
                + (f" The owner: {line}" if line else "")
                + " Fix it, commit on this branch, and end your turn.")
        facts = step.setdefault("facts", {})
        facts["requirements_left"] = [rid for rid in facts.get("requirements_left") or [] if rid != row["id"]]
        for finding in step.get("findings") or []:
            if finding.get("requirement_id") == row["id"] and not finding.get("decision"):
                finding.update({"decision": "fix_now", "decided_at": self._clock()})
        facts["findings_open"] = any(not item.get("decision") and item.get("to_owner", True)
                                     for item in step.get("findings") or [])
        step["rounds"] = max(0, int(step.get("rounds") or 0) - 1)
        try:
            self.runner().prompt_builder(step, text)
        except Exception as exc:
            log.info(f"send back not typed: {exc}")
        if step["state"] != "working" and "working" in STEP_TRANSITIONS.get(step["state"], ()):
            self.transition(program, step, "working", by="owner", parked_by=None, parked_reason=None, facts=facts,
                            line=f"Sent {label(row['ordinal'])} back to the agent")
        else:
            self._save(step)
            self._checkpoint(program, step, "owner", f"Sent {label(row['ordinal'])} back to the agent")

    def _after_findings(self, program: dict[str, Any], step: dict[str, Any], findings: list[dict[str, Any]]) -> None:
        """Every finding is decided: the Fix now ones go back to the agent,
        else the review passes and the gate goes on."""
        fix = [item for item in findings if item.get("decision") == "fix_now"]
        if fix:
            words = "\n".join(f"- {item.get('text')}" for item in fix)
            self.runner().prompt_builder(
                step, f"The owner asks you to fix these findings on HoldSpeak's step {step['ordinal']}:\n{words}\n"
                      "Fix them, commit on your branch, and end your turn.")
            step["rounds"] = int(step.get("rounds") or 0)
            step.setdefault("facts", {})["fix_requested_at"] = self._clock()
            self.transition(program, step, "working", by="engine", line="Sent the findings to fix back to the agent")
        else:
            step["review_verdict"] = "pass"
            self._save(step)
            self.runner().pass_gate(program, step, by="owner")

    def decide_proposal(self, principal: Any, program_id: str, proposal_id: Any, choice: str) -> dict[str, Any]:
        """His answer on what an agent proposed (§6): a requirement (Add /
        Skip), a change to a planned step (Apply / Skip), an amendment to a
        running step's brief (Send / Skip)."""
        self._require_owner(principal, "decide a proposal")
        program = self._program(program_id)
        row = next((item for item in self.store.list_checkpoints(program["id"])
                    if str(item["id"]) == str(proposal_id) and item.get("kind") in PROPOSAL_KINDS), None)
        if row is None:
            raise ProgramRefused("proposal_unknown", "There is no such proposal on this program.", status=404)
        if row.get("choice"):
            raise ProgramRefused("proposal_decided", "You answered this proposal already.")
        kind, choice = str(row["kind"]), str(choice or "")
        if choice not in DECIDE_CHOICES[kind]:
            raise ProgramRefused("choice_invalid", f"{kind!r} takes {', '.join(DECIDE_CHOICES[kind])}.", status=400)
        payload = dict(row.get("undo") or {})
        step = self.store.get_step(str(row.get("step_id") or "")) if row.get("step_id") else None
        answer: dict[str, Any] = {}
        with _LOCK:
            split = (payload.get("fields") or {}).get("split") if kind == "step_change" else None
            if split and step is None:
                raise NotFound("program_step", str(row.get("step_id")))
            if choice == "skip" and split:
                # PG-LANG LANG8: Skip on a split runs the step as it is.
                from .program_split import run_as_it_is

                run_as_it_is(self, program, step, by="owner")
            elif choice == "skip":
                self._checkpoint(program, step, "owner", f"Skipped: {payload.get('title') or row['line']}"[:400])
            elif split:
                from .program_split import apply_split

                apply_split(self, program, step, list(split.get("parts") or []), by="owner")
            elif kind == "requirement_proposed":
                from .program_requirements import label

                self._frozen_step(step)
                data = self._requirement_input(program, payload.get("text"), payload.get("kind"), payload.get("spec"))
                added = self._new_requirement(program, step, data, each_step=bool(payload.get("each_step")),
                                              required=bool(payload.get("required", True)), by="agent")
                self._requirement_line(program, step, "owner", f"Added {label(added['ordinal'])} that an agent proposed · "
                                       f"{added['text']}", [added["id"]])
                self._requirement_added(program, step, added)
                answer["requirement_id"] = added["id"]
            elif kind == "step_change":
                if step is None:
                    raise NotFound("program_step", str(row.get("step_id")))
                fields = dict(payload.get("fields") or {})
                if fields.get("remove"):
                    self._remove(program, step, by="owner")
                else:
                    self._apply_step_change(program, step, fields, by="owner")
            else:
                if step is None:
                    raise NotFound("program_step", str(row.get("step_id")))
                self._apply_amend(program, step, str(payload.get("line") or ""), by="agent")
            self.store.decide_checkpoint(int(row["id"]), choice, payload)
            self._touch(program)
            self.changed(program["id"], (step or {}).get("id"), verb="decide", requirement_id=answer.get("requirement_id"))
        self._tick_now(program["id"])
        return {**answer, "program": self.get(principal, program["id"])}

    def requirement_evidence(self, principal: Any, program_id: str, requirement_id: str) -> dict[str, Any]:
        """The file behind a requirement's evidence (its log, or its shot),
        read only inside the worktree the engine judged it in."""
        program = self._program(program_id)
        row = self._requirement(program, requirement_id)
        evidence = row.get("evidence") or {}
        ref = str(evidence.get("ref") or "")
        if evidence.get("kind") not in ("log", "shot") or not ref:
            raise ProgramRefused("no_evidence_file", "This requirement has no log or shot yet.", status=404)
        step = self.store.get_step(row["step_id"]) if row.get("step_id") else None
        roots = [Path(str(step["worktree"]))] if step and step.get("worktree") else []
        roots.append(Path(str(program.get("repo_root") or ".")).parent / f"hs-program-{program['id']}-end")
        path = Path(ref).resolve()
        if not any(path.is_relative_to(root.resolve()) for root in roots) or not path.is_file():
            raise ProgramRefused("no_evidence_file", "The evidence file is not there any more.", status=404)
        media = "image/png" if path.suffix.lower() == ".png" else "text/plain; charset=utf-8"
        return {"path": str(path), "media": media, "kind": evidence.get("kind")}

    # ── PG-REQ §8: adjust while running ──────────────────────────────

    def _top_order(self, program_id: str) -> list[dict[str, Any]]:
        return [step for step in self.store.list_steps(program_id) if not step.get("race_of")]

    def _reorder(self, program: Mapping[str, Any], order: list[str], *, by: str) -> list[str]:
        """Numbers follow the order (decision 6): every step is numbered by
        its place, every ``after`` list is rewritten through the same map, in
        one write under the lock. A started step that changes its number
        keeps its branch and gets one line. A step never lands above a step
        it comes after (the refusal names it)."""
        steps = self.store.list_steps(program["id"])
        top = {step["id"]: step for step in steps if not step.get("race_of")}
        mapping = {int(top[sid]["ordinal"]): index for index, sid in enumerate(order, start=1)}
        for sid in order:
            step = top[sid]
            new = mapping[int(step["ordinal"])]
            for value in step.get("after") or []:
                if int(value) in mapping and mapping[int(value)] >= new:
                    raise ProgramRefused("order_invalid", f"Step {step['ordinal']} comes after step {value}: it cannot "
                                         f"move above it.", status=409)
        lines = []
        for step in steps:
            old = int(step["ordinal"])
            new = mapping.get(old, old)
            after = sorted({mapping.get(int(value), int(value)) for value in step.get("after") or []})
            if new == old and after == list(step.get("after") or []):
                continue
            if new != old and not step.get("race_of") and step.get("state") not in ("planned", "ready"):
                lines.append((step, f"Step {old} is now step {new}"))
            step["ordinal"], step["after"] = new, after
            self._save(step)
        for step, line in lines:
            self._checkpoint(program, step, by, line)
        return [line for _step, line in lines]

    def change_step(self, principal: Any, program_id: str, step_id: str, **fields: Any) -> dict[str, Any]:
        """Change a step (§8): the fields its state leaves open; ``before``
        moves it. His change applies at once; an orchestrating agent's goes
        up the ladder (``step_change``: YOLO applies it and says so, Secure
        and Normal ask him). An agent's field that lowers the bar is one
        ``step_change`` proposal for him at every level, YOLO too (§4.5,
        §7.2). A frozen field is refused with its reason."""
        from .program_rules import decide

        program = self._program(program_id)
        step = self._step(program, step_id)
        fields = {key: value for key, value in fields.items() if key in _CHANGE_FIELDS}
        if not fields:
            raise ProgramRefused("nothing_to_change", "Name a field to change.", status=400)
        _editable, frozen = step_fields(step)
        for key in fields:
            field = _CHANGE_FIELDS[key] if key != "runs_on" or step["state"] in ("planned", "ready") else "runs_on_then"
            if field in frozen:
                detail = (f"Step {step['ordinal']} started. Add the step after it." if field == "position"
                          else f"Step {step['ordinal']}: {frozen[field]}.")
                raise ProgramRefused("step_frozen", detail, field=field, reason=frozen[field])
        if _is_owner(principal):
            with _LOCK:
                self._apply_step_change(program, step, fields, by="owner")
                self._touch(program)
                self.changed(program["id"], step["id"], verb="move" if "before" in fields else "step")
            self._tick_now(program["id"])
            return self.get(principal, program["id"])
        self._require_writer(principal, program, "change")
        outcome = decide(program.get("control"), "step_change", {})
        # §4.5, §7.2: an agent's lower gate goes to him at every level, YOLO too.
        lowered = _lowered_step_fields(step, fields)
        if lowered and not outcome.to_owner:
            fields = {key: value for key, value in fields.items() if key not in lowered}
        title = f"The orchestrator {_change_words(step, fields)}"
        with _LOCK:
            if lowered and not outcome.to_owner:
                words = f"The orchestrator {_change_words(step, lowered)} (this lowers the bar)"
                self.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=self._clock(), by="agent",
                                          line=words[:400], kind="step_change", undo={"title": words, "fields": lowered})
            if fields and outcome.to_owner:
                title += " (this lowers the bar)" if lowered else ""
                self.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=self._clock(), by="agent",
                                          line=title[:400], kind="step_change", undo={"title": title, "fields": dict(fields)})
            elif fields:
                before = {key: step.get(_STORE_KEY.get(key, key)) for key in fields if key != "before"}
                self._apply_step_change(program, step, fields, by="engine")
                self.engine_decision(program, step, "step_change", outcome, title[:400],
                                     undo={"step_id": step["id"], "fields_before": before})
            self._touch(program)
            self.changed(program["id"], step["id"], verb="step")
        self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def _apply_step_change(self, program: Mapping[str, Any], step: dict[str, Any], fields: Mapping[str, Any], *,
                           by: str) -> None:
        """Validate and write the §8 fields (each as ``plan`` validates it)."""
        state = step["state"]
        planned = state in ("planned", "ready")
        changed: list[str] = []
        if "title" in fields:
            title = " ".join(str(fields["title"] or "").split())[:200]
            if not title:
                raise ProgramRefused("step_title_required", "A step needs a title.", status=400)
            step["title"] = title
            changed.append("title")
        if "brief" in fields:
            step["brief_markdown"] = str(fields["brief"] or "").strip()
            changed.append("brief")
        if "owns" in fields:
            step["owns"] = [str(item) for item in fields["owns"] or [] if str(item).strip()]
            changed.append("owns")
        if "after" in fields:
            after = sorted({int(value) for value in fields["after"] or [] if str(value).strip().lstrip("-").isdigit()})
            if any(value >= int(step["ordinal"]) or value < 1 for value in after):
                raise ProgramRefused("after_invalid", f"Step {step['ordinal']} may only come after an earlier step.", status=400)
            step["after"] = after
            changed.append("after")
        if "effort" in fields:
            effort = str(fields["effort"] or "").strip().lower()
            if effort not in EFFORTS:
                raise ProgramRefused("effort_invalid", "Effort is low, medium or high.", status=400)
            step["effort"] = effort
            changed.append("effort")
        if "profile" in fields or "engine" in fields:
            profile = self._profile(fields.get("profile", step.get("profile")), "profile")
            run_profile = profile or program["default_profile"]
            step["profile"] = profile
            step["engine"] = self._engine_id(fields.get("engine"), run_profile, "engine") if fields.get("engine") else None
            changed.append("agent")
        if "runs_on" in fields:
            listed = self._runs_on(fields["runs_on"], "runs_on")
            if planned:
                if listed:
                    step["profile"], step["engine"] = listed[0]["profile"], listed[0]["engine"]
                step["runs_on"] = listed if len(listed) > 1 else []
            else:
                # Started: the first agent is set; only the agents after it change.
                first = self.runs_on_of(program, step)[0]
                step["runs_on"] = [first] + [row for row in listed if (row["profile"], row.get("engine"))
                                             != (first["profile"], first.get("engine"))]
            changed.append("agents")
        if "race" in fields:
            race = int(fields["race"] or 0)
            race = 0 if race == 1 else race
            if race < 0 or race > MAX_RACE:
                raise ProgramRefused("race_invalid", "A race has 2 or 3 agents.", status=400)
            step["race"] = race
            changed.append("race")
        if "gate_check" in fields:
            step["gate_check"] = bool(fields["gate_check"])
            changed.append("check")
        if "for_person_id" in fields:
            # Before the review: ``review <person>`` names the person and the gate at once.
            step["for_person_id"] = fields["for_person_id"] or None
            changed.append("person")
        if "gate_review" in fields:
            value = fields["gate_review"]
            value = "agent" if value is True else "none" if value is False else str(value or "none").lower()
            if value not in GATE_REVIEW:
                raise ProgramRefused("gate_review_invalid", "Review is none, agent or person.", status=400)
            if not planned and value != "agent":
                raise ProgramRefused("step_frozen", f"Step {step['ordinal']}: {FROZEN_BAR}.", field="gate_review",
                                     reason=FROZEN_BAR)
            if value == "person" and not (step.get("for_person_id") or program.get("for_person_id")):
                raise ProgramRefused("person_required", "A person review names the person (for_person_id).", status=400)
            step["gate_review"] = value
            changed.append("review")
        if "review_depth" in fields:
            depth = str(fields["review_depth"] or "").lower()
            if depth not in REVIEW_DEPTHS:
                raise ProgramRefused("review_depth_invalid", "Depth is glance, delta or standard.", status=400)
            step["review_depth"] = depth
            changed.append("review depth")
        if "gate_merge" in fields:
            merge = _GATE_MERGE_ALIASES.get(str(fields["gate_merge"] or "").lower(), str(fields["gate_merge"] or "").lower())
            if merge not in GATE_MERGE:
                raise ProgramRefused("gate_merge_invalid", "Merge is level, owner or none.", status=400)
            if not planned and merge == "none":
                raise ProgramRefused("step_frozen", f"Step {step['ordinal']}: {FROZEN_SET}.", field="gate_merge",
                                     reason=FROZEN_SET)
            step["gate_merge"] = merge
            changed.append("merge")
        if "may_call" in fields:
            step["may_call"] = bool(fields["may_call"])
            changed.append("may call")
        if "prefer_idle" in fields:
            step["prefer_idle"] = bool(fields["prefer_idle"])
            changed.append("when idle")
        if "budget_tokens" in fields:
            step["budget_tokens"] = _budget(fields["budget_tokens"], f"Step {step['ordinal']}: the budget")
            changed.append("budget")
        if changed:
            self._save(step)
            self._checkpoint(program, step, by, f"Changed step {step['ordinal']}: " + ", ".join(changed))
        if "before" in fields:
            self._move(program, step, fields["before"], by=by)

    def _move(self, program: Mapping[str, Any], step: Mapping[str, Any], before: Any, *, by: str) -> None:
        if step["state"] not in ("planned", "ready"):
            raise ProgramRefused("step_frozen", f"Step {step['ordinal']} started; it keeps its place.", field="position",
                                 reason=FROZEN_SET)
        order = [row["id"] for row in self._top_order(program["id"]) if row["id"] != step["id"]]
        target = str(before or "")
        if target in ("", "end"):
            order.append(step["id"])
        else:
            if target not in order:
                raise NotFound("program_step", target)
            order.insert(order.index(target), step["id"])
        before_ordinal = int(step["ordinal"])
        self._reorder(program, order, by=by)
        fresh = self.store.get_step(step["id"]) or step
        if int(fresh["ordinal"]) != before_ordinal:
            self._checkpoint(program, fresh, by, f"Moved step {before_ordinal} to {fresh['ordinal']}")

    def remove_step(self, principal: Any, program_id: str, step_id: str) -> dict[str, Any]:
        """Remove a Planned or Ready step (PG-LANG §3.4): the numbers follow
        the order again and every ``after`` that named it takes what it came
        after, as a move does. A started step stays (``step_stays``). His
        removal applies at once; an orchestrating agent's goes up the ladder
        (``step_change``: YOLO removes it and says so, Secure and Normal ask
        him)."""
        from .program_rules import decide

        program = self._program(program_id)
        step = self._step(program, step_id)
        if step.get("race_of"):
            step = self._step(program, str(step["race_of"]))
        if step["state"] not in ("planned", "ready"):
            raise ProgramRefused("step_stays", f"Step {step['ordinal']} started. It stays.", field="position",
                                 reason=FROZEN_SET)
        if _is_owner(principal):
            with _LOCK:
                self._remove(program, step, by="owner")
                self._touch(program)
                self.changed(program["id"], step["id"], verb="remove")
            self._tick_now(program["id"])
            return self.get(principal, program["id"])
        self._require_writer(principal, program, "change")
        outcome = decide(program.get("control"), "step_change", {})
        title = f"The orchestrator removes step {step['ordinal']}, {step['title']}"
        with _LOCK:
            if outcome.to_owner:
                self.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=self._clock(), by="agent",
                                          line=title[:400], kind="step_change",
                                          undo={"title": title, "fields": {"remove": True}})
            else:
                self._remove(program, step, by="engine")
                self.engine_decision(program, None, "step_change", outcome, title[:400])
            self._touch(program)
            self.changed(program["id"], step["id"], verb="remove")
        self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def _remove(self, program: Mapping[str, Any], step: Mapping[str, Any], *, by: str) -> None:
        if step["state"] not in ("planned", "ready"):
            raise ProgramRefused("step_stays", f"Step {step['ordinal']} started. It stays.", field="position",
                                 reason=FROZEN_SET)
        number = int(step["ordinal"])
        inherited = [int(value) for value in step.get("after") or []]
        for other in self.store.list_steps(program["id"]):
            if other["id"] == step["id"]:
                continue
            if other.get("race_of") == step["id"]:
                self.store.delete_step(other["id"])
                continue
            after = [int(value) for value in other.get("after") or []]
            if number in after:
                other["after"] = sorted({value for value in after if value != number} | set(inherited))
                self._save(other)
        # Its requirements stay as rows (R n is never used again, PG-REQ §3):
        # set aside, not required, out of every count.
        for row in self.requirements(program["id"]):
            if row.get("step_id") != step["id"]:
                continue
            if row.get("parent_id"):
                self.store.delete_requirement(row["id"])
                continue
            row.update(required=False, state="waived", waived_reason=f"Step {number} was removed",
                       updated_at=self._clock())
            self.store.save_requirement(row)
        self.store.delete_step(step["id"])
        order = [row["id"] for row in self._top_order(program["id"])]
        self._reorder(program, order, by=by)
        if by != "engine":  # the engine's removal is its Decided for you line
            self._checkpoint(program, None, by, f"Removed step {number}, {step['title']}")

    def amend(self, principal: Any, program_id: str, step_id: str, line: Any) -> dict[str, Any]:
        """A line added to a started step's brief (§8): typed to the agent at
        its next turn boundary, never into a blocked agent; the first brief
        stays as it was. His at once; an orchestrating agent's by the level
        (``step_amend``)."""
        from .program_rules import decide

        program = self._program(program_id)
        step = self._step(program, step_id)
        words = " ".join(str(line or "").split())[:1000]
        if not words:
            raise ProgramRefused("line_required", "An amendment is one line.", status=400)
        if step["state"] in ("planned", "ready"):
            raise ProgramRefused("step_not_started", f"Step {step['ordinal']} has not started: change its brief.")
        _editable, frozen = step_fields(step)
        if "amend" in frozen:
            raise ProgramRefused("step_frozen", f"Step {step['ordinal']}: {frozen['amend']}. Send it back with a line instead.",
                                 field="amend", reason=frozen["amend"])
        if _is_owner(principal):
            with _LOCK:
                self._apply_amend(program, step, words, by="owner")
                self._touch(program)
                self.changed(program["id"], step["id"], verb="amend")
            self._tick_now(program["id"])
            return self.get(principal, program["id"])
        self._require_writer(principal, program, "amend")
        outcome = decide(program.get("control"), "step_amend", {})
        title = f"The orchestrator adds to step {step['ordinal']}: {words}"
        with _LOCK:
            if outcome.to_owner:
                self.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=self._clock(), by="agent",
                                          line=title[:400], kind="step_amend", undo={"title": title, "line": words})
            else:
                self._apply_amend(program, step, words, by="agent")
                self.engine_decision(program, step, "step_amend", outcome, f"Sent to step {step['ordinal']}: {words}"[:400])
            self._touch(program)
            self.changed(program["id"], step["id"], verb="amend")
        self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def _apply_amend(self, program: Mapping[str, Any], step: dict[str, Any], line: str, *, by: str) -> None:
        at = self._clock()
        facts = step.setdefault("facts", {})
        facts.setdefault("amendments", []).append({"at": at, "by": by, "line": line, "sent_at": None})
        self._save(step)
        who = "the owner" if by == "owner" else "the orchestrator"
        self.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=at, by=by, kind="amend",
                                  line=f"Added to the brief by {who}: {line}"[:400], undo={"line": line})
        try:
            git = self.runner()._git
        except Exception:
            git = None
        write_amendment(step, f"Added by {who} at {_clock_words(at)}", line, git=git)

    # ── PG-LANG LANG1: the Program text (get and apply) ──────────────

    def add_to_night(self, principal: Any, *, kind: Any, item_id: Any, line: Any = None,
                     program_id: Any = None) -> dict[str, Any]:
        """PG-LANG LANG12 / JRN2, Add to tonight: a Door task (``action``), a
        note line (``note`` with ``line``) or a step of another Program
        (``program_step``) becomes a Planned step of the night Program,
        planned by the cheap planner at the window's start
        (``program_night``). His add lands at once; an agent's is a step the
        plan lacked (YOLO adds it and says so; below YOLO it is refused)."""
        from .program_night import add_to_night

        answer = add_to_night(self, principal, kind=kind, item_id=item_id, line=line, program_id=program_id)
        self._tick_now(answer["program_id"])
        return answer

    def text_get(self, principal: Any, program_id: str) -> dict[str, Any]:
        """The Program's text, printed from the tables now, with its lamps
        (PROGRAM-LANGUAGE §3.6)."""
        from .program_text import VERSION, print_program

        wire = self.get(principal, program_id)
        return {"program_id": wire["id"], "text": print_program(wire), "revision": int(wire.get("revision") or 0),
                "version": VERSION}

    def shape(self, principal: Any, program_id: str, sentence: Any, *, apply: bool = False,
              pending: Optional[str] = None) -> dict[str, Any]:
        """PG-LANG LANG3: one sentence becomes change rows (program_shaper);
        LANG5 ``pending``: the rows in the well, so the next sentence adds."""
        from .program_shaper import shape_program

        return shape_program(self, principal, program_id, sentence, apply=apply, pending=pending)

    def drop_held_shape(self, principal: Any, program_id: str) -> dict[str, Any]:
        """LANG5: Not this on the rows a call left on the desk."""
        from .program_spoken import drop

        program = self._program(program_id)
        self._require_writer(principal, program, "shape")
        drop(program["id"])
        return self.get(principal, program["id"])

    # ── PG-LANG LANG9: the interview rounds (program_rounds) ─────────

    def rounds_open(self, principal: Any, program_id: str, names: Any = None) -> dict[str, Any]:
        from .program_rounds import open_rounds

        return open_rounds(self, principal, program_id, names)

    def round_next(self, principal: Any, program_id: str, name: str) -> dict[str, Any]:
        from .program_rounds import ask

        return ask(self, principal, program_id, name)

    def round_answer(self, principal: Any, program_id: str, name: str, *, answer: Any = None, option: Any = None,
                     question_id: Any = None, skip: bool = False, not_this: bool = False,
                     apply: bool = False) -> dict[str, Any]:
        """``{question_id, answer | option | skip}`` (§12); ``not_this``: the
        answer's rows were dismissed, so it became nothing."""
        from . import program_rounds as rounds

        qid = str(question_id) if question_id else None
        if skip:
            return rounds.skip_question(self, principal, program_id, name, qid)
        if not_this:
            return rounds.not_this(self, principal, program_id, name, qid or "")
        return rounds.answer(self, principal, program_id, name, answer, question_id=qid, choice=option, apply=apply)

    def round_decide(self, principal: Any, program_id: str, name: str, choice: Any) -> dict[str, Any]:
        from .program_rounds import decide

        return decide(self, principal, program_id, name, choice)

    def round(self, principal: Any, program_id: str, action: Any, **kw: Any) -> dict[str, Any]:
        from .program_rounds import act

        return act(self, principal, program_id, action, **kw)

    def apply_programs(self, principal: Any, program_id: str, programs: Any, which: Any = "all") -> dict[str, Any]:
        """JRN1: Apply all / Apply this one of a draft that proposes several
        Programs (program_planner.apply_programs)."""
        from .program_planner import apply_programs

        return apply_programs(self, principal, program_id, programs, which)

    def _waits_on(self, program: Mapping[str, Any]) -> Optional["ProgramRefused"]:
        """JRN1: a Program made from a draft's later Program waits on the one
        before it (``origin_ref = program:<id>``) until that one is Done."""
        kind, _, ident = str(program.get("origin_ref") or "").partition(":")
        if kind != "program" or not ident:
            return None
        before = self.store.get_program(ident)
        if before is None or before.get("closed_at") or before.get("state") == "done":
            return None
        steps = self.store.list_steps(ident)
        if steps and self._state(before, steps) == "done":
            return None
        return ProgramRefused("waits_on_program", f"It starts after {before['title']} is done.",
                              program_id=ident)

    def plan_draft(self, principal: Any, program_id: str, *, goal: Any = None, template: Any = None,
                   budget: Any = None, text: Any = None, split: Any = None) -> dict[str, Any]:
        """PG-LANG LANG6: a goal becomes a drafted text, as change rows
        (program_planner); nothing is written until ``text_apply``."""
        from .program_planner import plan_draft

        return plan_draft(self, principal, program_id, goal=goal, template=template, budget=budget, text=text,
                          split=split)

    def shape_engine(self, principal: Any, program_id: str) -> dict[str, Any]:
        """The engine the shaping bar names (``engine: None``: none is set)."""
        from .program_shaper import engine_words

        program = self._program(program_id)
        return {"program_id": program["id"], **engine_words(self.db)}

    def _project_named(self, name: Any) -> Optional[str]:
        words = " ".join(str(name or "").split()).casefold()
        with self.db._connection() as conn:
            rows = conn.execute("SELECT id, name FROM projects WHERE is_archived=0").fetchall()
        found = [str(row["id"]) for row in rows if str(row["name"]).casefold() == words or str(row["id"]) == words]
        return found[0] if len(found) == 1 else None

    def _person_named(self, name: Any) -> Optional[str]:
        words = " ".join(str(name or "").split())
        if not words:
            return None
        try:
            names = dict(self._people_service().display_names() or {})
        except Exception:
            names = {}
        if words in names:
            return words
        found = [pid for pid, said in names.items() if str(said).casefold() == words.casefold()]
        return found[0] if len(found) == 1 else None

    @staticmethod
    def _entries(agents: Any) -> list[dict[str, Any]]:
        return [{"profile": profile, "engine": engine} for profile, engine in agents or []]

    def _check_text_rows(self, principal: Any, program: Mapping[str, Any], wire: Mapping[str, Any],
                         rows: list[Any]) -> None:
        """Refuse by name, before anything is written, what the verbs would
        refuse: an unknown agent or engine, a project or a person the desk
        does not know, a requirement that cannot be proven, his-only edits
        by an agent."""
        owner = _is_owner(principal)

        def guard(row: Any, check: Callable[[], Any]) -> None:
            if row.verdict not in ("allowed", "lowers"):
                return
            try:
                check()
            except ProgramRefused as exc:
                row.refuse(exc.code, exc.detail)

        for row in rows:
            data = row.data
            kind = data.get("kind")
            if kind == "head":
                name, value = data["name"], data["value"]
                if name == "control" and not owner:
                    from .program_rules import level_of

                    if wider(level_of(value), parent_level(principal, self.db)) and wider(
                            level_of(value), program.get("control")) and row.verdict in ("allowed", "lowers"):
                        # IMP4: the text cannot widen it either.
                        row.refuse("control_wider", f"{NO_WIDER}. Ask the owner.")
                        continue
                if name == "agents":
                    guard(row, lambda value=value: self._runs_on(self._entries(value), "agent"))
                elif name == "reviewer" and value[0] != "none":
                    guard(row, lambda value=value: self._engine_id(value[1], self._profile(value[0], "reviewer"), "reviewer"))
                elif name == "planner" and value and self.engine(value) is None:
                    row.refuse("engine_unknown", f"planner: the model library has no engine {value!r}.")
                elif name == "delivery" and value:
                    guard(row, lambda value=value: _delivery(f"dw {value}", str(program.get("repo_root") or "")))
                elif name == "within":
                    guard(row, lambda value=value: _within(list(value)))
                elif name == "check" and value:
                    guard(row, lambda value=value: self._check_command(str(program.get("repo_root") or ""), value))
                elif name == "for_person" and value and self._person_named(value) is None:
                    row.refuse("person_unknown", f"There is no person {value!r} in People.")
                elif name == "allow":
                    guard(row, lambda value=value: self._allowed_profiles(list(value)))
                elif name == "project" and value and self._project_named(value) is None:
                    row.refuse("project_unknown", f"There is no project {value!r}.")
                elif name == "project" and not value:
                    row.refuse("text_bad_value", "A program stays filed to its project.")
            elif kind in ("step", "add_step"):
                step = data.get("step")
                agents = data.get("agents") if kind == "step" else (step.agents if step is not None else None)
                if (kind == "add_step" or data.get("name") == "agents") and agents:
                    guard(row, lambda agents=agents: self._runs_on(self._entries(agents), "agent"))
                person = data.get("value") if data.get("name") == "for_person" else (
                    step.for_person if kind == "add_step" and step is not None else None)
                if person and self._person_named(person) is None and row.verdict in ("allowed", "lowers"):
                    row.refuse("person_unknown", f"There is no person {person!r} in People.")
                if kind == "add_step" and step is not None and step.merged:
                    guard(row, lambda step=step: _history_input(step.merged, 1))
                if kind == "add_step" and step is not None:
                    for req in step.requirements:
                        if req.rid is not None:
                            row.refuse("text_bad_value", f"Line {req.line}: a new step's requirement is R+.")
            elif kind in ("edit_requirement", "waive") and not owner:
                row.refuse("owner_required", "Only the owner changes or waives a requirement.")
            elif kind in ("round", "round_order") and not owner and row.verdict in ("allowed", "lowers"):
                # §12: an agent passes his answer only as a proposal (LANG9).
                row.refuse("owner_required", "Only the owner answers and closes a round.")
            if kind in ("edit_requirement", "require"):
                req = data["row"]
                guard(row, lambda req=req: self._requirement_input(program, req.text, req.kind, req.spec))

    def text_apply(self, principal: Any, program_id: str, text: Any, *, dry_run: bool = True,
                   base: Any = None, allow_lower: Iterable[str] = ()) -> dict[str, Any]:
        """A changed text applied through the service verbs (§3.6): the
        change rows (allowed, refused with the frozen reason, conflict,
        lowers the bar); ``dry_run`` writes nothing. A real apply writes
        only when no row is refused or in conflict and every row that lowers
        the bar is named in ``allow_lower``; then each change goes through
        its verb (update, plan, change_step, amend, require, edit, waive)
        under the lock, one checkpoint names the text's changes, and one
        ``program_changed`` frame says ``text``."""
        from .program_text import (
            VERSION, allowed_model, diff_program_text, parse_program_text, patch, print_program, render,
        )

        if not isinstance(text, str) or not text.strip():
            raise ProgramRefused("text_required", "Give the program text.", status=400)
        program = self._program(program_id)
        wire = self.get(principal, program_id)
        current = print_program(wire)
        base_text = str(base) if isinstance(base, str) and base.strip() else current
        base_model, new_model = parse_program_text(base_text), parse_program_text(text)
        rows = diff_program_text(base_model, new_model, record=wire)
        if base_text != current:
            # §3.6: a field that changed since he read it is a conflict.
            since = {row.id: row for row in diff_program_text(base_model, parse_program_text(current), record=wire)}
            for row in rows:
                moved = since.get(row.id)
                if moved is not None and row.verdict in ("allowed", "lowers"):
                    row.verdict, row.code = "conflict", "text_conflict"
                    what = row.where[0].upper() + row.where[1:]
                    row.reason = f"{what}'s {row.field} changed since you read it: now {moved.after or 'none'}."
        self._check_text_rows(principal, program, wire, rows)
        if not dry_run and any(getattr(row, "code", "") == "control_wider" for row in rows):
            self._checkpoint(program, None, "engine", NO_WIDER, kernel=False)  # IMP4
        asked = [str(item) for item in allow_lower or [] if str(item).strip()]
        owner = _is_owner(principal)
        if asked and not owner:
            # §4.5, §7.2: agents propose; only the owner lowers the bar.
            raise ProgramRefused("owner_required", f"Only the owner lowers the bar. You named: {', '.join(asked)}.",
                                 status=403, rows=asked)
        proposed = [] if owner else self._agent_bar_rows(wire, rows)
        to_owner = {row.id for row in proposed}
        allow = set(asked)
        blocked = [row for row in rows if row.verdict in ("refused", "conflict")
                   or (row.verdict == "lowers" and row.id not in allow and row.id not in to_owner)]
        answer: dict[str, Any] = {
            "program_id": program["id"], "changes": [row.to_wire() for row in rows], "patch": patch(base_text, text),
            "allowed_text": render(allowed_model(base_model, new_model, rows)), "applied": False,
            "text": current, "revision": int(wire.get("revision") or 0), "version": VERSION,
            "refused": sum(1 for row in rows if row.verdict in ("refused", "conflict")),
            "lowers": [row.id for row in rows if row.lowers_bar and row.verdict == "lowers"],
        }
        if not owner:
            answer["proposed"] = sorted(to_owner)
        if dry_run or blocked or not rows:
            return answer
        rest = [row for row in rows if row.id not in to_owner]
        if rest:
            self._apply_text(principal, program, wire, base_model, new_model, rest)
        if proposed:
            answer["proposals"] = self._propose_text_rows(program, wire, proposed)
        # LANG5: rows a call left on the desk are against the old text.
        from .program_spoken import drop

        drop(program["id"])
        fresh = self.get(principal, program["id"])
        answer.update(applied=True, text=print_program(fresh), revision=int(fresh.get("revision") or 0),
                      program=fresh)
        return answer

    def _agent_bar_rows(self, wire: Mapping[str, Any], rows: list[Any]) -> list[Any]:
        """An agent's text never lowers the bar (§4.5, §7.2; PG-REQ §14.7).
        A core question waits for him as a lower bar does (the shaper's
        guard). A Planned or Ready step's lower gate goes to him as a
        ``step_change`` proposal at every level; any other lower bar is
        refused with its reason. Answers the rows that become proposals."""
        from .program_shaper import guard

        guard(rows, wire)
        by_number = {int(step["ordinal"]): step for step in wire.get("steps") or []}
        out = []
        for row in rows:
            if row.verdict != "lowers":
                continue
            data = row.data
            step = by_number.get(data.get("number")) if data.get("kind") == "step" else None
            core = row.code == "core_question"
            if (step is not None and data.get("name") in _PROPOSED_STEP_FIELDS
                    and step.get("state") in ("planned", "ready")):
                row.code = "owner_proposal"
                row.reason = (f"{row.reason} " if core and row.reason else "") + \
                    "Only the owner lowers the bar. This goes to him as a proposal."
                out.append(row)
            elif core:
                row.refuse("owner_required", f"{row.reason} Only the owner answers this.")
            else:
                row.refuse("owner_required", f"Only the owner lowers the bar ({row.where}, {row.field}).")
        return out

    def _propose_text_rows(self, program: Mapping[str, Any], wire: Mapping[str, Any],
                           rows: list[Any]) -> list[int]:
        """The agent's lower gates as one ``step_change`` proposal per step
        (PG-REQ §6): his Apply writes them, his Skip drops them."""
        ids = {int(step["ordinal"]): step["id"] for step in wire.get("steps") or []}
        fields_of: dict[str, dict[str, Any]] = {}
        for row in rows:
            fields_of.setdefault(ids[row.data["number"]], {})[_PROPOSED_STEP_FIELDS[row.data["name"]]] = \
                row.data["value"]
        made: list[int] = []
        with _LOCK:
            for step_id, fields in fields_of.items():
                step = self.store.get_step(step_id) or {}
                title = f"The orchestrator {_change_words(step, fields)} (this lowers the bar)"
                made.append(self.store.add_checkpoint(step_id=step_id, program_id=program["id"], at=self._clock(),
                                                      by="agent", line=title[:400], kind="step_change",
                                                      undo={"title": title, "fields": dict(fields)}))
            self._touch(self._program(program["id"]))
            self.changed(program["id"], verb="text", text=True)
        return made

    def _apply_text(self, principal: Any, program: Mapping[str, Any], wire: Mapping[str, Any], base_model: Any,
                    new_model: Any, rows: list[Any]) -> None:
        pid = program["id"]
        by = "owner" if _is_owner(principal) else "agent"
        by_number = {int(step["ordinal"]): step for step in wire.get("steps") or []}
        keys: dict[str, str] = {f"s{n}": step["id"] for n, step in by_number.items()}

        def kinds(kind: str) -> list[Any]:
            return [row for row in rows if row.data.get("kind") == kind]

        self._held.on = True
        done = 0
        try:
            with _LOCK:
                # 1. The Program.
                fields: dict[str, Any] = {}
                for row in kinds("head"):
                    name, value = row.data["name"], row.data["value"]
                    if name == "agents":
                        fields["runs_on"] = self._entries(value)
                    elif name == "reviewer":
                        if value[0] == "none":
                            fields["reviewer_profile"] = "none"
                        else:
                            fields["reviewer_profile"], fields["reviewer_engine"] = value[0], value[1]
                    elif name == "project":
                        fields["project_id"] = self._project_named(value)
                    elif name == "for_person":
                        fields["for_person_id"] = self._person_named(value) if value else None
                    elif name == "check":
                        fields["check_command"] = value or "none"
                    elif name == "delivery":
                        fields["delivery"] = f"dw {value}" if value else None
                    else:
                        fields[{"when_idle": "prefer_idle", "may_hand_off": "may_handoff", "spend": "spend_limit_usd",
                                "usage_warning": "usage_warning_share", "allow": "allowed_profiles",
                                "depth": "review_depth", "planner": "planner_engine",
                                "budget": "budget_tokens"}.get(name, name)] = value
                if fields:
                    self.update(principal, pid, **fields)
                    done += len(kinds("head"))
                # 2. New steps, appended in their order, then placed.
                added = kinds("add_step")
                if added:
                    before = {step["id"] for step in self.store.list_steps(pid)}
                    raws = []
                    for row in added:
                        step = row.data["step"]
                        raw: dict[str, Any] = {"title": step.title, "brief": step.brief, "owns": list(step.owns),
                                               "after": list(step.after), "prefer_idle": step.when_idle,
                                               "may_call": step.may_call, "origin_ref": step.origin}
                        if step.agents:
                            raw["runs_on"] = self._entries(step.agents)
                        for key, value in (("effort", step.effort), ("race", step.race), ("gate_check", step.check),
                                           ("gate_review", step.review), ("review_depth", step.depth),
                                           ("gate_merge", step.merge), ("budget_tokens", step.budget)):
                            if value is not None:
                                raw[key] = value
                        if step.for_person:
                            raw["for_person_id"] = self._person_named(step.for_person)
                        if step.merged:
                            raw["history"] = dict(step.merged)
                        raws.append(raw)
                    self.plan(principal, pid, steps=raws)
                    made = sorted((step for step in self.store.list_steps(pid) if step["id"] not in before
                                   and not step.get("race_of")), key=lambda step: int(step["ordinal"]))
                    for row, step in zip(added, made):
                        keys[row.data["key"]] = step["id"]
                    done += len(added)
                # 3. Field changes of the steps that were there.
                changes: dict[int, dict[str, Any]] = {}
                after_rows = []
                for row in kinds("step"):
                    name, value, number = row.data["name"], row.data["value"], row.data["number"]
                    if name == "after":
                        after_rows.append(row)
                        continue
                    target = changes.setdefault(number, {})
                    if name == "agents":
                        target["runs_on"] = self._entries(value)
                    elif name == "for_person":
                        target["for_person_id"] = self._person_named(value) if value else None
                    else:
                        target[{"check": "gate_check", "review": "gate_review", "depth": "review_depth",
                                "merge": "gate_merge", "when_idle": "prefer_idle",
                                "budget": "budget_tokens"}.get(name, name)] = value
                for number, step_fields_now in changes.items():
                    self.change_step(principal, pid, keys[f"s{number}"], **step_fields_now)
                    done += 1
                # 4. Order: an ``after`` that loses a step first, then the
                # moves (each one keeps every ``after`` true), then the rest.
                def ordinals() -> dict[str, int]:
                    return {step["id"]: int(step["ordinal"]) for step in self._top_order(pid)}

                def ids(values: Iterable[Any]) -> set[str]:
                    return {keys[value] for value in values if value in keys}

                for row in after_rows:
                    sid = keys[f"s{row.data['number']}"]
                    old = set(by_number[row.data["number"]].get("after") or [])
                    kept = ids(f"s{value}" for value in old) & ids(row.data["value"])
                    now = ordinals()
                    if len(kept) < len(old):
                        self.change_step(principal, pid, sid, after=sorted(now[item] for item in kept))
                # The blocks he took out (Planned steps), once nothing waits on them.
                for row in kinds("remove_step"):
                    self.remove_step(principal, pid, keys.pop(f"s{row.data['number']}"))
                    done += 1
                moves = kinds("move")
                if moves:
                    top = max((step.number for step in base_model.steps if step.number is not None), default=0)
                    order, counter = [], top
                    for step in new_model.steps:
                        if step.number is None:
                            counter += 1
                            order.append(keys.get(f"n{counter}"))
                        elif f"s{step.number}" in keys:
                            order.append(keys[f"s{step.number}"])
                    order = [sid for sid in order if sid]
                    if by != "owner":
                        for row in moves:
                            succ = row.data.get("before")
                            self.change_step(principal, pid, keys[row.data["key"]],
                                             before=keys[succ] if succ else "end")
                    else:
                        guard = 0
                        index = 0
                        while index < len(order) and guard < len(order) * len(order) + 4:
                            guard += 1
                            current = [step["id"] for step in self._top_order(pid)]
                            if current[index] == order[index]:
                                index += 1
                                continue
                            wanted = self.store.get_step(order[index]) or {}
                            if wanted.get("state") in ("planned", "ready"):
                                self.change_step(principal, pid, order[index], before=current[index])
                            else:
                                # A started step keeps its place: the step in
                                # its way goes to where it belongs.
                                other = current[index]
                                at = order.index(other)
                                self.change_step(principal, pid, other,
                                                 before=order[at + 1] if at + 1 < len(order) else "end")
                    done += len(moves)
                for row in after_rows:
                    sid = keys[f"s{row.data['number']}"]
                    now = ordinals()
                    want = sorted(now[item] for item in ids(row.data["value"]))
                    if want != sorted(int(v) for v in (self.store.get_step(sid) or {}).get("after") or []):
                        self.change_step(principal, pid, sid, after=want)
                    done += 1
                # 5. Lines added to started briefs.
                for row in kinds("amend"):
                    self.amend(principal, pid, keys[f"s{row.data['number']}"], row.data["line"])
                    done += 1
                # 6. Requirements: his edits and waives, then the new ones.
                reqs = self.requirements(pid)
                by_rid = {int(item["ordinal"]): item for item in reqs if not item.get("parent_id")}
                for row in kinds("edit_requirement"):
                    req = row.data["row"]
                    self.edit_requirement(principal, pid, by_rid[row.data["rid"]]["id"], text=req.text, kind=req.kind,
                                          required=req.required, spec=dict(req.spec))
                    done += 1
                for row in kinds("waive"):
                    self.decide_requirement(principal, pid, by_rid[row.data["rid"]]["id"], "waive", line=row.data["line"])
                    done += 1
                for row in kinds("require"):
                    req, scope, key = row.data["row"], row.data["scope"], row.data.get("key")
                    self.require(principal, pid, text=req.text, kind=req.kind, spec=dict(req.spec),
                                 required=req.required, each_step=scope == "every step",
                                 step_id=keys.get(key) if key else None)
                    done += 1
                # 7. The rounds (§6.2): their states, order and his answers.
                round_rows = kinds("round") + kinds("round_order")
                if round_rows:
                    self._write_rounds(self._program(pid), new_model.rounds, by=by)
                    done += len(round_rows)
                fresh = self._program(pid)
                lines = sorted({row.line for row in rows if row.line})
                self._checkpoint(fresh, None, by, f"Changed by the text: {done} change{'s' if done != 1 else ''}"
                                 + (f" (line{'s' if len(lines) != 1 else ''} {', '.join(map(str, lines[:12]))})"
                                    if lines else ""))
                self._touch(fresh)
        except ProgramRefused as exc:
            raise ProgramRefused(exc.code, f"{exc.detail} The text stopped there: {done} change"
                                 f"{'s' if done != 1 else ''} before it are written.",
                                 **{key: value for key, value in exc.context.items()})
        finally:
            self._held.on = False
            self.changed(pid, verb="text", text=True)
        self._tick_now(pid)

    def _write_rounds(self, program: Mapping[str, Any], rounds: Iterable[Any], *, by: str) -> None:
        """The text's rounds onto ``program_rounds``: each round's state and
        order, his answers on the engine's questions (kept by place; the
        question rows keep their ids). A round the text no longer has is
        removed (only a round with no question gets that far)."""
        now = self._clock()
        stored = {_fold_name(row["name"]): row for row in self.store.list_rounds(program["id"])}
        keep: set[str] = set()
        for index, item in enumerate(rounds, start=1):
            key = _fold_name(item.name)
            keep.add(key)
            row = stored.get(key) or {"program_id": program["id"], "name": item.name, "questions": []}
            questions = [dict(question) for question in row.get("questions") or []]
            for question, said in zip(questions, item.questions):
                if (question.get("answer") or None) != (said.answer or None):
                    question.update(answer=said.answer or None, answered_by=by if said.answer else None,
                                    at=now if said.answer else None)
            self.store.save_round({"program_id": program["id"], "name": row["name"], "state": item.state,
                                   "ordinal": index, "questions": questions, "updated_at": now})
        for key, row in stored.items():
            if key not in keep:
                self.store.delete_round(program["id"], row["name"])

    # ── Phone: the engine reaches him (Phone design §6) ──────────────

    def reach_phone(
        self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], kind: str, text: str, *,
        reason: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Where the engine writes a core question, a red step after its
        rounds or a finished Program, it asks ``phone_rules.reach`` and acts:
        a message to his phone, a call (when the Program may call and the
        level allows), or nothing. Each reach is one line of Decided for you
        ("Reached you: a message") with its rule. Once per thing: the phone's
        own sweep asks again later (a call after 10 minutes with no reply)."""
        try:
            from ..phone import phone_on

            if not phone_on():
                return None
            if self._phone is not None:
                phone = self._phone()
            else:
                from ..phone.service import default_phone_service

                phone = default_phone_service(self.db)
            origin = (f"program_step:{step['id']}:{kind}" if step else f"program:{program['id']}:{kind}")
            if phone._reaches(origin):
                return None
            result = phone.reach(
                kind, level=program.get("control"), text=text, reason=reason or text, context=text,
                origin_ref=origin, may_call=bool((step or {}).get("may_call") or program.get("may_call")),
                program_step_id=(step or {}).get("id"),
                facts={"night_program": program.get("template") == "overnight"},
            )
        except Exception as exc:
            log.warning(f"the program did not reach the phone: {exc}")
            return None
        if result.get("held") and not result.get("queued"):
            return result
        from types import SimpleNamespace

        outcome = SimpleNamespace(choice=result.get("channel"), rule=result.get("rule"), overturnable=False)
        self.engine_decision(program, step, "reach", outcome, str(result.get("line") or "Reached you"))
        return result

    # ── a call that decides (PG-DIRECTION DIR8) ──────────────────────

    def call_line(self, program_id: str, step_id: Optional[str], line: str, *,
                  note_ref: Optional[str] = None, because: Optional[Mapping[str, Any]] = None,
                  refusal: Optional[str] = None) -> int:
        """One ledger line a call writes about a held item it read: when it
        was asked, what came of it, and the call's transcript Note
        (``undo.note_ref``). It changes nothing else on the Program."""
        program = self._program(program_id)
        undo = {key: value for key, value in (("note_ref", note_ref), ("because", dict(because or {}) or None),
                                              ("refusal", refusal)) if value}
        # DIR8a: the line keeps why the item was on the call and a late answer's refusal.
        ident = self.store.add_checkpoint(step_id=str(step_id or ""), program_id=program["id"], at=self._clock(),
                                          by="owner", line=" ".join(str(line or "").split())[:400], via="call",
                                          undo=undo or None)
        self.changed(program["id"], step_id or None, verb="checkpoint")
        return ident

    # ── Decided for you (design §6, §8) ──────────────────────────────

    def engine_decision(
        self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], kind: str, outcome: Any,
        line: str, *, undo: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Record one engine decision with its rule: a checkpoint ``by:
        engine``, a kernel operation, and a row of Decided for you."""
        operation_id = self._kernel_record(program, step, line)
        at = self._clock()
        undo = dict(undo or {})
        if "pin" not in undo:
            pin = self.pin(step, line)
            if pin:
                undo["pin"] = pin
        seen = seen_of(step)
        if seen:
            undo.setdefault("seen", seen)
        ident = self.store.add_checkpoint(
            step_id=str((step or {}).get("id") or ""), program_id=program["id"], at=at, by="engine", line=line,
            operation_id=operation_id, kind=kind, choice=getattr(outcome, "choice", None),
            rule=getattr(outcome, "rule", None), overturnable=bool(getattr(outcome, "overturnable", False)),
            undo=undo or None,
        )
        return {"id": ident, "at": at, "kind": kind, "choice": getattr(outcome, "choice", None),
                "rule": getattr(outcome, "rule", None)}

    def decided_for_you(self, program_id: str) -> list[dict[str, Any]]:
        return [
            {"id": row["id"], "at": row["at"], "step_id": row["step_id"] or None, "kind": row["kind"],
             "choice": row["choice"], "rule": row["rule"], "line": row["line"],
             "overturnable": bool(row["overturnable"]) and not row["overturned_at"],
             "overturned_at": row["overturned_at"], "operation_id": row["operation_id"],
             "decision_record_id": row.get("decision_record_id")}
            for row in self.store.list_checkpoints(program_id) if row.get("rule")
        ]

    def overturn(self, principal: Any, program_id: str, decision_id: Any) -> dict[str, Any]:
        """Undo an engine decision while it can still be undone (a Later task,
        a Skip, a parked step, an added step; never a merge). Owner only."""
        self._require_owner(principal, "overturn a decision")
        program = self._program(program_id)
        row = next((item for item in self.store.list_checkpoints(program["id"])
                    if str(item["id"]) == str(decision_id) and item.get("rule")), None)
        if row is None:
            raise ProgramRefused("decision_unknown", "There is no such decision on this program.", status=404)
        if not row["overturnable"] or row["overturned_at"]:
            raise ProgramRefused("not_overturnable", "This decision cannot be undone now.")
        undo = row.get("undo") or {}
        if row.get("choice") == "shape":
            # PG-LANG LANG3: a shaped change YOLO applied (program_shaper).
            from .program_shaper import overturn_shape

            return overturn_shape(self, principal, program, row)
        with _LOCK:
            step = self.store.get_step(row["step_id"]) if row["step_id"] else None
            choice = row.get("choice")
            if choice in ("later", "skip") and step is not None:
                for finding in step.get("findings") or []:
                    if finding.get("id") == undo.get("finding_id"):
                        finding.update({"decision": None, "decided_at": None, "to_owner": True})
                        finding.pop("decision_record_id", None)
                if undo.get("decision_record_id"):
                    from . import program_decisions

                    program_decisions.withdraw(self.db, str(undo["decision_record_id"]))
                    records = (step.get("facts") or {}).get("decision_records") or []
                    if undo["decision_record_id"] in records:
                        records.remove(undo["decision_record_id"])
                if undo.get("door_item_id"):
                    self._dismiss_door_item(str(undo["door_item_id"]))
                step.setdefault("facts", {})["findings_open"] = True
                if step["state"] in ("findings", "review", "checking", "pr_open", "merge_ask"):
                    if step["state"] != "findings" and "findings" in STEP_TRANSITIONS.get(step["state"], ()):
                        self.transition(program, step, "findings", by="owner", line="Overturned: the finding is yours")
                    else:
                        self._save(step)
                else:
                    self._save(step)
            elif choice == "park" and step is not None:
                if step["state"] != "parked":
                    raise ProgramRefused("not_overturnable", "The step is not parked any more.")
                step["rounds"] = 0
                step["parked_by"], step["parked_reason"] = None, None
                self.transition(program, step, "ready", by="owner", line="Overturned: the step runs again")
            elif choice == "add" and undo.get("requirement_id"):
                # PG-REQ: an agent's requirement YOLO added; never deleted, set aside.
                added = self.store.get_requirement(str(undo["requirement_id"]))
                if added is not None and added.get("state") != "waived":
                    self._waive(program, added, "You overturned the requirement an agent proposed")
                    added["required"] = False
                    self.store.save_requirement(added)
            elif choice == "apply" and step is not None and undo.get("fields_before") is not None:
                if step["state"] not in ("planned", "ready"):
                    raise ProgramRefused("not_overturnable", "The step started; its change stays.")
                for key, value in dict(undo["fields_before"]).items():
                    step[_STORE_KEY.get(key, key)] = value
                self._save(step)
            elif choice == "split" and undo.get("split"):
                # PG-LANG LANG8: YOLO's split, while every part is Planned or Ready.
                from .program_split import overturn_split

                overturn_split(self, program, row)
            elif choice == "add" and undo.get("step_id"):
                added = self.store.get_step(str(undo["step_id"]))
                if added is not None:
                    if added["state"] in ("planned", "ready"):
                        self.store.delete_step(added["id"])
                    else:
                        self.transition(program, added, "parked", by="owner", parked_by=PARKED_BY_OWNER,
                                        parked_reason="You overturned the added step",
                                        line="Overturned: the added step is parked")
            else:
                raise ProgramRefused("not_overturnable", "This decision cannot be undone.")
            self.store.mark_overturned(int(row["id"]), self._clock())
            self._checkpoint(program, step, "owner", f"Overturned: {row['line']}")
            self._touch(program)
            self.changed(program["id"], row["step_id"] or None, verb="overturn")
        self._tick_now(program["id"])
        return {"program": self.get(principal, program["id"])}

    def _dismiss_door_item(self, item_id: str) -> None:
        try:
            with self.db._connection() as conn:
                conn.execute("UPDATE action_items SET status='dismissed' WHERE id=? AND status='open'", (item_id,))
        except Exception as exc:
            log.info(f"later task not dismissed: {exc}")

    def _decide_finding(self, program: dict[str, Any], step: dict[str, Any], finding_id: Optional[str],
                        choice: str, reason: Optional[str]) -> dict[str, Any]:
        findings = list(step.get("findings") or [])
        finding = next((item for item in findings if item.get("id") == finding_id), None)
        if finding is None:
            raise ProgramRefused("finding_unknown", "There is no such finding on this step.", status=404)
        if finding.get("decision"):
            raise ProgramRefused("finding_decided", "You decided this finding already.")
        finding["decision"] = choice
        finding["decided_at"] = self._clock()
        answer: dict[str, Any] = {}
        if choice == "later":
            answer["door_item"] = self._later_task(program, step, finding)
            finding["door_item_id"] = (answer["door_item"] or {}).get("id")
        elif choice == "skip":
            notes = step.setdefault("facts", {}).setdefault("skips", [])
            typed = str(reason or "").strip() or None
            notes.append({"finding": finding.get("text"), "reason": typed, "at": self._clock()})
            answer["decision_record_id"] = self._propose_skip(program, step, finding, reason=typed, rule=None, by="owner")
        step["findings"] = findings
        self._save(step)
        self._checkpoint(program, step, "owner", {"fix_now": "Fix now", "later": "Later", "skip": "Skip"}[choice]
                         + f": {finding.get('text', '')}"[:300],
                         decision_record_id=answer.get("decision_record_id"))
        if all(item.get("decision") or not item.get("to_owner", True) for item in findings):
            step.setdefault("facts", {})["findings_open"] = False
            self._after_findings(program, step, findings)
        return answer

    def apply_finding_rule(self, program: dict[str, Any], step: dict[str, Any], finding: dict[str, Any],
                           outcome: Any) -> None:
        """The engine's Later or Skip on one finding (Decided for you)."""
        choice = outcome.choice
        finding.update({"decision": choice, "decided_at": self._clock(), "decided_by": "engine", "to_owner": False})
        undo: dict[str, Any] = {"finding_id": finding["id"]}
        if choice == "later":
            item = self._later_task(program, step, finding) or {}
            finding["door_item_id"] = item.get("id")
            undo["door_item_id"] = item.get("id")
            line = f"{finding.get('level')} finding on step {step['ordinal']} \u2192 Later (a Door task): {finding.get('text')}"
        else:
            step.setdefault("facts", {}).setdefault("skips", []).append(
                {"finding": finding.get("text"), "reason": outcome.rule, "at": self._clock()})
            line = f"{finding.get('level')} finding on step {step['ordinal']} \u2192 Skip: {finding.get('text')}"
            # PG16: a rule's Skip of a NOTE is the noise filter, never a
            # proposal; a rule's Skip above NOTE is a judgement and is one.
            if str(finding.get("level") or "NOTE").upper() != "NOTE":
                record_id = self._propose_skip(program, step, finding, reason=None, rule=outcome.rule, by="engine")
                if record_id:
                    undo["decision_record_id"] = record_id
        self.engine_decision(program, step, f"finding_{str(finding.get('level') or 'note').lower()}", outcome,
                             line[:400], undo=undo)

    # ── PG16: decisions from a Program ───────────────────────────────

    def _propose_skip(self, program: Mapping[str, Any], step: dict[str, Any], finding: dict[str, Any], *,
                      reason: Optional[str], rule: Optional[str], by: str) -> Optional[str]:
        """A Skip becomes a proposed decision record (one per finding)."""
        from . import program_decisions

        text = str(finding.get("text") or "")
        level = str(finding.get("level") or "note").lower()
        record_id = program_decisions.propose(
            self.db, self.store, program, step, kind="skip", finding_id=str(finding.get("id") or ""),
            title=f"Skip: {text}", decision=f"Skip this {level} finding on step {step['ordinal']}: {text}",
            reason=reason, rule=rule, by=by, now=self._clock(),
        )
        if record_id:
            finding["decision_record_id"] = record_id
            self._remember_record(step, record_id)
        return record_id

    def propose_merge(self, program: Mapping[str, Any], step: dict[str, Any], outcome: Any) -> Optional[str]:
        """A merge the engine made by rule becomes a proposed decision record."""
        from . import program_decisions

        number = step.get("pr_number")
        review = ", review passed" if step.get("review_verdict") == "pass" else ""
        record_id = program_decisions.propose(
            self.db, self.store, program, step, kind="merge",
            title=f"Merge PR #{number}: {step.get('title')}",
            decision=f"The engine merged PR #{number}, step {step['ordinal']} of {program.get('title')}, "
                     "with no press from you.",
            reason=f"Check green{review}", rule=getattr(outcome, "rule", None), by="engine", now=self._clock(),
        )
        if record_id:
            facts = step.setdefault("facts", {})
            facts["merge_decision_record_id"] = record_id
            self._remember_record(step, record_id)
            self._save(step)
        return record_id

    @staticmethod
    def _remember_record(step: dict[str, Any], record_id: str) -> None:
        records = step.setdefault("facts", {}).setdefault("decision_records", [])
        if record_id not in records:
            records.append(record_id)

    def _later_task(self, program: Mapping[str, Any], step: Mapping[str, Any], finding: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """A finding decided Later: a Door task for him, filed to the Project
        and the person (§9b)."""
        try:
            from ..principals import Principal, PrincipalKind
            from .door_service import DoorService
            from .follow_through_service import FollowThroughService

            door = DoorService(FollowThroughService(self.db), None, None, None, db=self.db)  # type: ignore[arg-type]
            task = f"Later, from {program['title']} step {step['ordinal']}: {finding.get('text', '')}"[:300]
            item = door.add_item(
                Principal(PrincipalKind.OWNER, "program-engine"), task, owner="me", due=None,
                source_type="program_step", source_ref=f"program_step:{step['id']}:{finding.get('id')}",
            )
            ident = str((item or {}).get("id") or "")
            if ident and program.get("project_id"):
                self.store.file_to_project(str(program["project_id"]), f"action:{ident}", self._clock())
            person = step.get("for_person_id") or program.get("for_person_id")
            return {"id": ident or None, "task": task, "project_id": program.get("project_id"), "person_id": person}
        except Exception as exc:
            log.warning(f"later task not made: {exc}")
            return None

    def _prepare_review_ask(self, principal: Any, program: Mapping[str, Any], step: dict[str, Any]) -> dict[str, Any]:
        """The person review gate's press: a send is PREPARED through the
        channel (his press in the Send preview sends; the engine never
        sends)."""
        person = step.get("for_person_id") or program.get("for_person_id")
        name = self.person_name(person) or "the reviewer"
        number = step.get("pr_number")
        text = (f"Hi {name}, could you review PR #{number} ({step.get('pr_url')})? It is step {step['ordinal']} "
                f"of “{program['title']}”: {step['title']}.")
        prepared: Any = None
        try:
            from ..runtime import composition

            channel = composition.service("channel_service", lambda: None)
            if channel is not None and hasattr(channel, "prepare"):
                prepared = channel.prepare(principal, {"body": text, "title": f"Review PR #{number}",
                                                       "source_ref": f"program_step:{step['id']}"})
        except Exception as exc:
            log.info(f"review ask not prepared through the channel: {exc}")
        step.setdefault("facts", {})["review_ask_at"] = self._clock()
        self._save(step)
        self._checkpoint(program, step, "owner", f"Prepared the review ask for {name}")
        return {"prepared": prepared, "draft": text, "person": {"id": person, "name": name}}

    # ── the engine's writes (the runner calls these) ─────────────────

    def transition(self, program: Mapping[str, Any], step: dict[str, Any], to: str, *, by: str = "engine",
                   line: str = "", detail: str = "", ending: Optional[str] = None, **fields: Any) -> dict[str, Any]:
        """Move one step along the table of §4 (a refused move raises), write
        its checkpoint (and the kernel operation for an engine decision)."""
        current = str(step.get("state") or "")
        if to != current and to not in STEP_TRANSITIONS.get(current, frozenset()):
            raise ProgramRefused("transition_invalid", f"A step cannot go from {current} to {to}.")
        old_head = step.get("head_commit")
        step.update(fields)
        now = self._clock()
        step["state"] = to
        if to != current and isinstance((step.get("facts") or {}).get("wait"), Mapping):
            step["facts"] = {key: value for key, value in (step.get("facts") or {}).items() if key != "wait"}
        if to in REPORT_STATES and to != current:
            self._report_files(program, step)
        # PG-IMPORT IMP2 (BroCrew's ending word): how the lane ended, apart
        # from the state. A green finish is finished; the engine names a
        # failed or cut-off end at the move; a step that runs again has none.
        ending = "finished" if to in FINISHED_STATES else ("failed" if to == "failed" else ending)
        if ending or (to != current and to not in REPORT_STATES):
            facts = dict(step.get("facts") or {})
            if ending in ENDINGS:
                facts["ending"] = ending
            else:
                facts.pop("ending", None)
            step["facts"] = facts
        if to != "ready":
            step["held_reason"] = None if to != current else step.get("held_reason")
        if to == "briefed" and not step.get("started_at"):
            step["started_at"] = now
        if to in CLOSED_STATES or to == "failed":
            step["ended_at"] = step.get("ended_at") or now
        elif to in ("ready", "planned"):
            step["ended_at"] = None
        self._save(step)
        if fields.get("head_commit") and fields["head_commit"] != old_head and old_head:
            self.requirements_moved(program, step)  # PG-REQ decision 4
        if to == "pr_open" and current != "pr_open" and step.get("pr_url"):
            from . import program_decisions

            program_decisions.link_pr(self.db, step)
        if line:
            self._checkpoint(program, step, by, line, detail=detail)
        return step

    def take_over(self, principal: Any, program_id: str, step_id: str) -> dict[str, Any]:
        """PG-IMPORT IMP6 (BroCrew: "It says 'take it over', because it IS that
        act"): he has the step's lane. The engine types nothing into it and
        decides nothing for it until Hand it back; a commit on the branch still
        goes to the check. Reversible, so no confirmation."""
        self._require_owner(principal, "take a lane over")
        program = self._program(program_id)
        step = self._step(program, step_id)
        if not step.get("launch_id") or step.get("state") in CLOSED_STATES or step.get("state") in ("planned", "ready"):
            raise ProgramRefused("no_lane", f"Step {step['ordinal']} has no running lane to take over.")
        if not isinstance((step.get("facts") or {}).get("taken"), Mapping):
            with _LOCK:
                step["facts"] = {**(step.get("facts") or {}), "taken": {"by": "owner", "at": self._clock()}}
                self._save(step)
                self._checkpoint(program, step, "owner", "You took the lane over", kernel=False)
                self.changed(program["id"], step["id"], verb="take_over")
        return self.get(principal, program["id"])

    def hand_back(self, principal: Any, program_id: str, step_id: str) -> dict[str, Any]:
        """PG-IMPORT IMP6: the inverse of Take it over; the tick goes on from
        the branch head. No confirmation: taking it again undoes it."""
        self._require_owner(principal, "hand a lane back")
        program = self._program(program_id)
        step = self._step(program, step_id)
        if isinstance((step.get("facts") or {}).get("taken"), Mapping):
            with _LOCK:
                step["facts"] = {key: value for key, value in (step.get("facts") or {}).items() if key != "taken"}
                self._save(step)
                self._checkpoint(program, step, "owner", "You handed the lane back", kernel=False)
                self.changed(program["id"], step["id"], verb="hand_back")
            self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def notice_lost(self, program_id: str, step_id: str, via: str) -> None:
        """PG-IMPORT IMP3: a message to him about this step did not arrive
        (``via``: telegram). The step's row and the list say so until the
        step moves; the ledger keeps one line."""
        step = self.store.get_step(str(step_id or ""))
        if step is None or step.get("program_id") != program_id:
            return
        facts = dict(step.get("facts") or {})
        if (facts.get("wait") or {}).get("cause") == "notice_lost":
            return
        program = self.store.get_program(program_id)
        facts["wait"] = {"cause": "notice_lost", "at": self._clock(), "via": str(via)}
        step["facts"] = facts
        with _LOCK:
            self._save(step)
            if program is not None:
                self.store.add_checkpoint(step_id=step["id"], program_id=program_id, at=self._clock(), by="engine",
                                          kind="notice_lost", line=f"The message to you on {via} did not arrive",
                                          undo={"via": str(via)})
                self.changed(program_id, step["id"], verb="notice_lost")

    def _report_files(self, program: Mapping[str, Any], step: dict[str, Any]) -> None:
        """PG-IMPORT IMP1: the step's diff file names against its base, read
        once as it reaches Done, Merged, Parked or Failed (``facts.files``).
        A git failure leaves the register empty, never stops the move."""
        facts = step.get("facts") or {}
        head = step.get("head_commit")
        if not head or not facts.get("base_commit") or (facts.get("files") or {}).get("commit") == head:
            return
        try:
            reader = getattr(self.runner(), "step_files", None)
            names = list(reader(program, step) or []) if reader else None
        except Exception as exc:
            log.debug(f"step files not read: {exc}")
            names = None
        if names is None:
            return
        step["facts"] = {**facts, "files": {"commit": head, "names": names[:50], "count": len(names)}}

    def _close_history(self, program: Mapping[str, Any]) -> None:
        """PG17: the Program closed; its imported steps go Merged → Done (the
        runner moves only live steps)."""
        for step in self.store.list_steps(program["id"]):
            if step.get("state") == "merged" and history_of(step):
                step["state"] = "done"
                self.store.save_step(step)

    def _save(self, step: dict[str, Any]) -> None:
        step["updated_at"] = self._clock()
        self.store.save_step(step)

    def save_step(self, step: dict[str, Any]) -> None:
        self._save(step)

    def _touch(self, program: dict[str, Any]) -> None:
        program["revision"] = int(program.get("revision") or 0) + 1
        program["updated_at"] = self._clock()
        self.store.save_program(program)

    def _checkpoint(self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], by: str, line: str,
                    *, kernel: bool = True, decision_record_id: Optional[str] = None,
                    detail: str = "") -> dict[str, Any]:
        operation_id = None
        if kernel and by == "engine":
            operation_id = self._kernel_record(program, step, line)
        at = self._clock()
        undo: dict[str, Any] = {"decision_record_id": decision_record_id} if decision_record_id else {}
        if detail:
            undo["detail"] = str(detail)  # the raw words behind the line (the evidence fold), never the line
        seen = seen_of(step) if by == "engine" else None
        if seen:
            undo["seen"] = seen
        pin = self.pin(step, line)
        if pin:
            undo["pin"] = pin
        line, via = _via_line(by, line)
        ident = self.store.add_checkpoint(step_id=str((step or {}).get("id") or ""), program_id=program["id"],
                                          at=at, by=by, line=line, operation_id=operation_id, undo=undo or None,
                                          via=via)
        return {"id": ident, "step_id": (step or {}).get("id") or "", "at": at, "by": by, "line": line,
                "operation_id": operation_id, "decision_record_id": decision_record_id,
                "ref": (pin or {}).get("ref")}

    def pin(self, step: Optional[Mapping[str, Any]], line: str) -> Optional[dict[str, Any]]:
        """PG20: a checkpoint on a step pins its worktree to a hidden ref
        (the runner's git). ``None`` for a Program-wide line; a failure is a
        note on the row, never a stop."""
        if not step or not step.get("id"):
            return None
        if not step.get("worktree"):
            return {"note": "No worktree to pin yet"}
        try:
            return dict(self.runner().pin_checkpoint(step, line) or {}) or None
        except Exception as exc:
            log.debug(f"checkpoint not pinned: {exc}")
            return {"note": "Not pinned: git is not available"}

    def _kernel_record(self, program: Mapping[str, Any], step: Optional[Mapping[str, Any]], line: str) -> Optional[str]:
        """The engine decision as a kernel operation ``program.step``."""
        if self._kernel is not None:
            return self._kernel(program=program, step=step, line=line)
        try:
            from ..kernel.program_ops import record_step_decision

            return record_step_decision(self.db, program, step, line)
        except Exception as exc:
            log.warning(f"program.step kernel receipt not written: {exc}")
            return None

    def changed(self, program_id: str, step_id: Optional[str] = None, *, verb: str = "step",
                requirement_id: Optional[str] = None, text: bool = False) -> None:
        """Recompute the Program's state, rewrite its note, emit the frames.
        PG-REQ: the frame names the requirement and the count when one moved."""
        from . import program_lessons
        from .program_requirements import counts as requirement_counts

        program = self._program(program_id)
        try:
            program_lessons.scan(self, program)  # JRN11: the lesson rule, by rule, no model
        except Exception as exc:  # a lesson never stops a move
            log.warning(f"program {program_id}: the lesson rule did not run: {exc}")
        steps = self.store.list_steps(program_id)
        reqs = self.requirements(program_id)
        state = self._state(program, steps, requirements=reqs)
        if state == "done" and not program.get("closed_at"):
            from .program_rules import decide

            self.reach_phone(program, None, "program_done",
                             f"{program['title']} is finished: every step is done.")

            outcome = decide(program.get("control"), "program_done", {})
            if not outcome.to_owner:
                program["closed_at"] = self._clock()
                self._close_history(program)
                self.store.save_program(program)
                self.engine_decision(program, None, "program_done", outcome, "Closed the program: every step is finished")
        if state == "done" and program.get("closed_at"):
            self._deliver_once(program)
        if state != program["state"]:
            before = program["state"]
            program["state"] = state
            self._touch(program)
            if before not in ("drafting",) or state != "running":
                self._checkpoint(program, None, "engine", _STATE_LINES.get(state, f"The program is {state}"))
        self.write_note(program, steps)
        turn = [item for item in self._turn(program, steps, requirements=reqs) if item["kind"] != "answer"]
        frame: dict[str, Any] = {"program_id": program_id, "step_id": step_id, "state": state, "your_turn": len(turn)}
        if requirement_id:
            frame["requirement_id"] = requirement_id
        met = requirement_counts(reqs, len([item for item in turn if item["kind"] in ("requirement_word", "requirement_left", "todo")]))
        if met:
            frame["requirements_met"] = met
        if text:
            # LANG1: the definition changed; the Text view takes a new base.
            frame["text"] = True
        if getattr(self._held, "on", False):
            return
        self._broadcast("program_changed", frame)
        try:
            from ..runtime import composition

            composition.notify_desk_changed("program", program_id, verb)
        except Exception:
            pass

    def _tick_now(self, program_id: str) -> None:
        """A press moves the program at once (not on the next 30 s tick)."""
        if not programs_on() or getattr(self._held, "on", False):
            return
        try:
            self.runner().tick_program(program_id)
        except Exception as exc:
            log.warning(f"program tick after a press failed: {exc}")

    # ── the handover note (§8) ───────────────────────────────────────

    def note_text(self, program: Mapping[str, Any], steps: list[dict[str, Any]]) -> str:
        summary = self._summary(program, steps)
        lines = [f"# Program: {program['title']}", ""]
        head = [summary["state_word"], f"{summary['done']} of {summary['total']} steps done"]
        if summary.get("skipped"):
            head.append(f"{summary['skipped']} skipped")
        if summary["your_turn"]:
            head.append(f"{summary['your_turn']} wait{'s' if summary['your_turn'] == 1 else ''} on you")
        lines += [" · ".join(head), ""]
        # PG-LANG LANG12: the night's digest on top, while it is fresh.
        from .program_night import note_section

        lines += note_section(self, program)
        place = self._place(program)
        where = []
        if place["project"]:
            where.append(f"Project: {place['project']['name']}")
        if place["origin"]:
            where.append(f"From: {place['origin']['title'] or place['origin']['ref']}")
        if place["person"] and place["person"]["name"]:
            where.append(f"For: {place['person']['name']}")
        if where:
            lines += [" · ".join(where), ""]
        if program.get("goal_markdown"):
            lines += ["## Goal", program["goal_markdown"], ""]
        lines.append("## Your turn")
        turn = [item for item in self._turn(program, steps) if item["kind"] != "answer"]
        asks = [item for item in self._turn(program, steps) if item["kind"] == "answer"]
        for item in turn + asks:
            lines.append(f"- {item['title']}")
        if not turn and not asks:
            lines.append("(nothing)")
        lines += ["", "## Steps"]
        checkpoints = self.store.list_checkpoints(program["id"])
        for step in self._top_steps(steps):
            lines.append(f"{step['ordinal']}. {self._step_line(program, step, checkpoints)}")
            for other in steps:
                if other.get("race_of") == step["id"]:
                    lines.append(f"   - race: {self._step_line(program, other, checkpoints)}")
        parked = [step for step in steps if step.get("state") == "parked"]
        lines += ["", "## Parked"]
        lines += [f"- Step {step['ordinal']} “{step['title']}” ({agent_label(step.get('profile') or program['default_profile'])}): "
                  f"{step.get('parked_reason') or 'parked'}" for step in parked] or ["(none)"]
        lines += self._note_requirements(program, steps)
        skips = [(step, skip) for step in steps for skip in (step.get("facts") or {}).get("skips") or []]
        later = [(step, item) for step in steps for item in step.get("findings") or [] if item.get("decision") == "later"]
        if skips or later:
            lines += ["", "## Decisions"]
            lines += [f"- Skipped on step {step['ordinal']}: {skip['finding']}" + (f" ({skip['reason']})" if skip.get("reason") else "")
                      for step, skip in skips]
            lines += [f"- Later on step {step['ordinal']}: {item.get('text')}" for step, item in later]
        if summary["state"] == "done":
            prs = [step for step in steps if step.get("pr_number") and step.get("state") in FINISHED_STATES]
            lines += ["", f"Done · {local_now().strftime('%Y-%m-%d')} · {len(prs)} PR{'s' if len(prs) != 1 else ''} · {summary.get('done_in', '')}"]
        decided = self.decided_for_you(program["id"])
        if decided:
            lines += ["", "## Decided for you"]
            for row in decided[:30]:
                when = _clock_words(row["at"])
                tail = " · Overturn" if row["overturnable"] else (" · overturned" if row["overturned_at"] else "")
                lines.append(f"- {when} · {row['line']} · rule: {row['rule']}{tail}")
        last = checkpoints[0] if checkpoints else None
        lines += ["", "## Last checked"]
        lines.append(f"{local_now().strftime('%Y-%m-%d %H:%M')} · {last['by'] if last else 'engine'}")
        return "\n".join(lines) + "\n"

    def _note_requirements(self, program: Mapping[str, Any], steps: list[dict[str, Any]]) -> list[str]:
        """PG-REQ: the handover note's Requirements: each sentence, where it
        is, its state; a waive with his line."""
        from .program_requirements import STATE_WORDS, label

        reqs = self.requirements(program["id"])
        if not reqs:
            return []
        ordinal = {step["id"]: step["ordinal"] for step in steps}
        out = ["", "## Requirements"]
        for row in reqs:
            if row.get("step_id") and row.get("parent_id"):
                continue
            if not row.get("step_id"):
                where = "every step" if row.get("each_step") else "the program"
                copies = [other for other in reqs if other.get("parent_id") == row["id"]]
                state = (f"{sum(1 for other in copies if other.get('state') in ('met', 'waived'))} of {len(copies)} steps"
                         if row.get("each_step") else STATE_WORDS.get(row["state"], row["state"]))
            else:
                where = f"step {ordinal.get(row['step_id'], '?')}"
                state = STATE_WORDS.get(row["state"], row["state"])
            if row.get("state") == "waived":
                state = f"Waived: {row.get('waived_reason') or ''}".strip()
            out.append(f"- {label(row['ordinal'])} · {row['text']} · {where} · {state}")
        for row in reqs:
            if row.get("parent_id") and row.get("state") == "waived" and row.get("waived_reason"):
                out.append(f"- {label(row['ordinal'])} on step {ordinal.get(row['step_id'], '?')} · Waived: {row['waived_reason']}")
        return out

    def _step_line(self, program: Mapping[str, Any], step: Mapping[str, Any], checkpoints: list[dict[str, Any]]) -> str:
        wire = self.step_wire(program, step, checkpoints)
        word = wire["state_word"]
        if step.get("pr_number") and step.get("state") in ("pr_open", "merge_ask", "merged", "done"):
            word += f" #{step['pr_number']}"
        parts = [step["title"], "—", word]
        line = f"{step['title']} — {word}"
        if step.get("state") == "planned" and step.get("after"):
            line += f" (after {', '.join(str(v) for v in step['after'])})"
        extra = []
        if step.get("state") not in ("planned", "ready"):
            agent = wire["agent"]
            if wire["engine"] and wire["engine"].get("short"):
                agent += f" · {wire['engine']['short']}"
            extra.append(agent)
            if wire["elapsed"]:
                extra.append(wire["elapsed"])
        last = wire["last_checkpoint"]
        if last and last["by"] == "agent":
            extra.append(f"“{last['line']}”")
        del parts
        return line + (" · " + " · ".join(extra) if extra else "")

    def write_note(self, program: dict[str, Any], steps: list[dict[str, Any]]) -> None:
        """Rewrite the Program's handover note (never by hand)."""
        note_id = f"program-{program['id']}"
        text = self.note_text(program, steps)
        try:
            from ..principals import Principal, PrincipalKind
            from .primitive_service import PrimitiveService
            from ..runtime import composition

            owner = Principal(PrincipalKind.OWNER, "program-engine")
            notes = PrimitiveService(self.db, on_changed=composition.notify_desk_changed)
            existing = self.db.notes.get(note_id)
            if existing is None:
                notes.create_note(owner, note_id=note_id, title=f"Program: {program['title']}",
                                  body_markdown=text, tags=["program"])
            elif existing.body_markdown != text or existing.title != f"Program: {program['title']}":
                notes.update_note(owner, note_id, title=f"Program: {program['title']}", body_markdown=text)
            if program.get("project_id"):
                self.store.file_to_project(str(program["project_id"]), f"note:{note_id}", self._clock())
        except Exception as exc:
            log.warning(f"program note not written: {exc}")
            return
        if program.get("note_id") != note_id:
            program["note_id"] = note_id
            self.store.save_program(program)


#: PG-REQ §8: the step fields ``change_step`` takes -> the §8 table's names.
_CHANGE_FIELDS = {
    "title": "title", "brief": "brief", "owns": "owns", "after": "after", "effort": "effort", "profile": "agent",
    "engine": "agent", "runs_on": "agent", "race": "race", "gate_check": "gate_check", "gate_review": "gate_review",
    "review_depth": "review_depth", "gate_merge": "gate_merge", "for_person_id": "for_person", "may_call": "may_call",
    "prefer_idle": "prefer_idle", "budget_tokens": "budget", "before": "position",
}
#: The text's step fields whose lower bar an agent may propose (PG-LANG
#: §4.5; a core ``owns`` or ``may call`` too) -> the ``change_step`` field.
_PROPOSED_STEP_FIELDS = {"check": "gate_check", "review": "gate_review", "depth": "review_depth",
                         "merge": "gate_merge", "may_call": "may_call", "owns": "owns"}
#: The stored key of a change field (for an overturn's "before" values).
_STORE_KEY = {"brief": "brief_markdown"}


def _with_pages(db: Any, program_id: str, items: list[dict[str, Any]], *, now: Optional[str] = None) -> list[dict[str, Any]]:
    """PG-DIRECTION DIR3: an item with an open briefing page carries
    ``page`` ({package_id, expires_at}); the key is absent otherwise."""
    if not items:
        return items
    try:
        from ..db.briefing import BriefingStore

        pages = BriefingStore(db).open_pages(f"program:{program_id}:", utc_now_iso())
    except Exception as exc:  # a store that cannot read keeps the items as they are
        log.debug(f"briefing pages not read: {exc}")
        return items
    for item in items:
        page = pages.get(f"program:{program_id}:{item['id']}")
        if page:
            item["page"] = page
    return _with_later(db, program_id, items, now=now)


def _with_later(db: Any, program_id: str, items: list[dict[str, Any]], *, now: Optional[str] = None) -> list[dict[str, Any]]:
    """PG-DIRECTION DIR4: an item he deferred carries ``later`` ({until,
    via}) until its next touch; the row of an item that waits no more is
    dropped (a new question on the same step starts fresh)."""
    try:
        from ..db.briefing import HeldLaterStore

        store = HeldLaterStore(db)
        rows = store.like(f"program:{program_id}:")
    except Exception as exc:
        log.debug(f"later rows not read: {exc}")
        return items
    if not rows:
        return items
    now = _utc_text(now or utc_now_iso())
    live = set()
    for item in items:
        ref = f"program:{program_id}:{item['id']}"
        live.add(ref)
        row = rows.get(ref)
        if row and _utc_text(row["until"]) > now:
            item["later"] = {"until": row["until"], "via": row["via"]}
    for ref in set(rows) - live:
        store.drop(ref)
    return items


def _utc_text(stamp: Any) -> str:
    """An ISO stamp as UTC text, so stamps compare as text."""
    from datetime import datetime, timezone

    try:
        value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except ValueError:
        return str(stamp)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _via_line(by: str, line: str) -> tuple[str, Optional[str]]:
    """An owner line written inside a decide call from another channel says
    the channel; ``(line, via)``."""
    via = _VIA.get()
    if by != "owner" or not via:
        return line, None
    return f"{line} \u00b7 {VIA_WORDS[via]}"[:400], via


def _lowered_step_fields(step: Mapping[str, Any], fields: Mapping[str, Any]) -> dict[str, Any]:
    """The ``change_step`` fields that lower the step's bar (PG-LANG §4.5:
    check off; review agent or person to none; depth down; merge owner to
    level or none) or ask a core question (an ``owns`` path outside the
    repository; ``may call``), as the text's guard reads them."""
    from .program_shaper import _outside
    from .program_text import _DEPTH_RANK

    out: dict[str, Any] = {}
    if "gate_check" in fields and step.get("gate_check") and not bool(fields["gate_check"]):
        out["gate_check"] = fields["gate_check"]
    if "gate_review" in fields:
        value = fields["gate_review"]
        value = "agent" if value is True else "none" if value is False else str(value or "none").lower()
        if step.get("gate_review") in ("agent", "person") and value == "none":
            out["gate_review"] = fields["gate_review"]
    if "review_depth" in fields:
        after, before = str(fields["review_depth"] or "").lower(), str(step.get("review_depth") or "delta")
        if after in _DEPTH_RANK and _DEPTH_RANK[after] < _DEPTH_RANK.get(before, 1):
            out["review_depth"] = fields["review_depth"]
    if "gate_merge" in fields:
        merge = str(fields["gate_merge"] or "").lower()
        if step.get("gate_merge") == "owner" and _GATE_MERGE_ALIASES.get(merge, merge) in ("level", "none"):
            out["gate_merge"] = fields["gate_merge"]
    if "owns" in fields:
        before = {str(item) for item in step.get("owns") or []}
        if any(_outside(str(item)) and str(item) not in before for item in fields["owns"] or []):
            out["owns"] = fields["owns"]
    if "may_call" in fields and bool(fields["may_call"]) and not step.get("may_call"):
        out["may_call"] = fields["may_call"]
    return {key: value for key, value in fields.items() if key in out}


def _change_words(step: Mapping[str, Any], fields: Mapping[str, Any]) -> str:
    """"moves step 6 before step 5", "changes step 4: title, brief"."""
    names = [key for key in fields if key != "before"]
    parts = []
    if "before" in fields:
        parts.append(f"moves step {step['ordinal']}" + (" to the end" if fields["before"] in (None, "", "end") else " up the plan"))
    if names:
        parts.append(f"changes step {step['ordinal']}: " + ", ".join(names))
    return " and ".join(parts)


def write_amendment(step: Mapping[str, Any], head: str, line: str,
                    git: Optional[Callable[..., str]] = None) -> Optional[str]:
    """PG-REQ §6: the amendment appended to ``<worktree>/.holdspeak/brief.md``
    under its head ("Added by the owner at 14:02"); the file is kept out of
    git (the worktree's ``info/exclude``), so the check's clean-tree rule
    holds. ``None`` when the step has no worktree yet."""
    worktree = str(step.get("worktree") or "")
    if not worktree or not Path(worktree).is_dir():
        return None
    target = Path(worktree) / ".holdspeak" / "brief.md"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as out:
            out.write(f"\n## {head}\n\n{line}\n")
        # git runs through the runner's one process site (the effect fence).
        found = git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude") if git else ""
        exclude = Path(found) if found else None
        if exclude is not None:
            exclude.parent.mkdir(parents=True, exist_ok=True)
            known = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
            if ".holdspeak/brief.md" not in known.splitlines():
                with exclude.open("a", encoding="utf-8") as out:
                    out.write(("" if known.endswith("\n") or not known else "\n") + ".holdspeak/brief.md\n")
    except Exception as exc:  # a note never stops the step
        log.info(f"amendment not written to the brief file: {exc}")
        return None
    return str(target)


#: The words that do not name a Program ("start the overnight program on the hub").
_NAME_FILLER = frozenset({"the", "a", "an", "my", "our", "program", "programs", "programme", "on", "hub",
                          "please", "this", "that", "called", "named"})


def name_words(text: str) -> list[str]:
    """The words of a Program's name, lower case, without the filler."""
    return [word for word in re.findall(r"[a-z0-9]+", str(text or "").lower()) if word not in _NAME_FILLER]


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


#: Shell words a check may start with that are no file on the PATH.
_SHELL_WORDS = frozenset({"echo", "true", "false", "test", "[", ":", "cd", "exec", "exit", "printf", "set",
                          "export", "if", "for", "while", "case", "{", "(", "!", "."})


def start_precheck(program: Mapping[str, Any], steps: Iterable[Mapping[str, Any]],
                   *, git: Callable[..., str]) -> Optional["ProgramRefused"]:
    """What would stop the program after an agent worked, read before Start
    (program-ed167ae4478b, 2026-10-31: no remote parked step 1 after the
    agent's commit): the repository is a git repository; a step that opens
    a PR has the ``origin`` remote its push targets; the check's program
    exists. ``git(cwd, *args)`` is the runner's git (its stdout, ``""`` on
    a failure). ``None`` when the program can start."""
    import shlex
    import shutil

    root = str(program.get("repo_root") or "")
    if not root:
        return None
    if not Path(root).is_dir() or not git(root, "rev-parse", "--git-dir"):
        return ProgramRefused("repository_not_git", "The repository is not a git folder. Name a git repository.")
    steps = list(steps)
    pushes = any(str(step.get("gate_merge") or "level") != "none" for step in steps) or (
        not steps and bool(program.get("night")))  # a night's steps come from its backlog
    if pushes and not git(root, "remote", "get-url", "origin"):
        return ProgramRefused("repository_no_remote", "The repository has no remote to push to. Add one named "
                              "origin, or set each step to merge: none to keep its branch local.")
    command = str(program.get("check_command") or "").strip()
    try:
        words = shlex.split(command)
    except ValueError:
        return None  # the shell reads it; the check's log says what went wrong
    words = [word for word in words if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", word)]
    words = words[1:] if words[:1] == ["env"] else words
    if not words or words[0] in _SHELL_WORDS:
        return None
    first = words[0]
    found = (Path(first) if Path(first).is_absolute() else Path(root) / first).exists() if "/" in first \
        else shutil.which(first) is not None
    if not found:
        return ProgramRefused("check_not_found", f"The check cannot run: {Path(first).name} is not on this "
                              "machine or in the repository. Install it, or change the check.")
    return None


def _parked_words(reason: Any) -> str:
    """His row's words for a parked step: a push or PR failure in words
    (never git's stderr); any other reason as the engine wrote it."""
    from .brief_words import pr_failure_words

    words = pr_failure_words(reason)
    return f"it {words}" if words else str(reason or "it stopped")


def _check_name(command: str) -> str:
    """``quick_check.sh`` for ``FOO=1 sh scripts/quick_check.sh --x``."""
    import shlex

    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    words = [word for word in words if "=" not in word.split("/")[0] or word.startswith("-")]
    # PG-WINDOW W5: never a flag (``sh -c '…'`` said "check: -c" on his desk).
    words = [word for word in words if word not in ("sh", "bash", "zsh", "uv", "run", "python", "python3", "env")
             and not word.startswith("-")]
    script = next((word for word in words if word.endswith(".sh")), None)
    if script:
        return Path(script).name
    first = words[0].split()[0] if words and words[0].split() else ""
    return Path(first).name if first else command


def _clock_words(stamp: Any) -> str:
    """``19:09`` on the hub's wall clock for a stored UTC stamp."""
    from datetime import datetime

    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).astimezone().strftime("%H:%M")
    except ValueError:
        return str(stamp or "")


def _desk_control_mode() -> str:
    """The desk's current Control mode (``Config.control_mode``) on the ladder."""
    try:
        from ..config import Config
        from .program_rules import level_of

        return level_of(Config.load().control_mode)
    except Exception:
        return "normal"


def _waiting_first(rows: list[dict[str, Any]]) -> None:
    """Your turn, failed, running, drafting, done, parked; newest change first in a band."""
    rows.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    rows.sort(key=lambda row: PROGRAM_BAND.get(row["state"], 9))


def _fold_name(name: Any) -> str:
    return "".join(str(name or "").split()).casefold()


def _budget(value: Any, what: str) -> Optional[int]:
    """A context budget in tokens (PG-LANG §5.4): ``65536``, ``"64k"``;
    ``None`` / ``""``: not set (the Program's, or the engine's window)."""
    if value in (None, "", 0):
        return None
    from .program_text import parse_tokens

    tokens = parse_tokens(value)
    if tokens is None:
        raise ProgramRefused("budget_invalid", f"{what} is a number of tokens ('64k').", status=400)
    return tokens


def _within(value: Any) -> list[str]:
    """PG-LANG §5.5: the paths the Program may own at all, relative to the
    repository (a folder ends with ``/``)."""
    if value in (None, "", []):
        return []
    items = [value] if isinstance(value, str) else value
    if not isinstance(items, (list, tuple)):
        raise ProgramRefused("within_invalid", "Within is a list of paths.", status=400)
    out: list[str] = []
    for item in items:
        for part in str(item).split(","):
            path = part.strip()
            if not path:
                continue
            if path.startswith(("/", "~")) or ".." in Path(path).parts:
                raise ProgramRefused("within_invalid", f"Within: {path!r} is not a path in the repository.", status=400)
            if path not in out:
                out.append(path)
    return out


def _delivery(value: Any, root: str) -> Optional[str]:
    """PG-LANG §8: ``dw <project>/<phase>[/<story>]`` -> ``dw:<ref>``; only
    in a repository with the rails (``.githooks/dw``)."""
    words = " ".join(str(value or "").split())
    if not words or words in ("none", "off"):
        return None
    ref = words[3:].strip() if words.startswith("dw ") else words[3:] if words.startswith("dw:") else ""
    parts = [part for part in ref.split("/") if part.strip()]
    if not 2 <= len(parts) <= 3 or len(parts) != len(ref.split("/")):
        raise ProgramRefused("delivery_invalid", "Delivery is 'dw <project>/<phase>' or 'dw <project>/<phase>/<story>'.",
                             status=400)
    if not (Path(str(root or "")) / ".githooks" / "dw").exists():
        raise ProgramRefused("delivery_no_rails", "This repository has no Delivery Workbench.", status=409)
    return "dw:" + "/".join(part.strip() for part in parts)


def _base_branch(root: str) -> str:
    """The repository's default branch name (``origin/HEAD``), else ``main``."""
    head = Path(root) / ".git"
    try:
        if head.is_file():
            return "main"
        ref = (head / "refs" / "remotes" / "origin" / "HEAD").read_text(encoding="utf-8").strip()
        if ref.startswith("ref: refs/remotes/origin/"):
            return ref.rsplit("/", 1)[-1]
    except OSError:
        pass
    return "main"


def step_origin(db: Any, step_id: str) -> Optional[tuple[str, str]]:
    """The desk item a step's merge closes (§9b): the step's own origin
    (``action:<id>``), else the Program's decision origin. ``None``: none."""
    store = ProgramStore(db)
    step = store.get_step(str(step_id or ""))
    if step is None:
        return None
    ref = str(step.get("origin_ref") or "")
    if not ref:
        program = store.get_program(step["program_id"]) or {}
        program_ref = str(program.get("origin_ref") or "")
        if program_ref.split(":", 1)[0] in ("decision", "decision_record"):
            ref = program_ref
    kind, _, ident = ref.partition(":")
    return (kind, ident) if kind and ident else None


_DEFAULT: Optional[ProgramService] = None
_DEFAULT_DB: Any = None


def default_program_service(db: Any = None) -> ProgramService:
    """The process's one Programs service over the hub database."""
    global _DEFAULT, _DEFAULT_DB
    if db is None:
        from ..runtime import composition
        from ..db import get_database

        db = composition.db_or(get_database)
    if _DEFAULT is None or _DEFAULT_DB is not db:
        _DEFAULT = ProgramService(db)
        _DEFAULT_DB = db
    return _DEFAULT


__all__ = [
    "ACTIVE_STATES", "AGENT_LABELS", "CLOSED_STATES", "DECIDE_CHOICES", "FINISHED_STATES", "MAX_RACE",
    "MAX_ROUNDS", "PROGRAMS_ENV", "PROGRAM_STATES", "PROGRAM_WORDS", "ProgramRefused", "ProgramService",
    "RACE_PROFILES", "STATIONS", "STEP_STATES", "STEP_TRANSITIONS", "STEP_WORDS", "agent_label",
    "VIA_CHANNELS", "VIA_WORDS", "via_of", "default_program_service", "duration_words", "history_of", "history_words", "name_words", "program_state",
    "programs_on", "spoken_state", "step_origin", "triage_effort", "your_turn",
]
