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
    "pr_open": frozenset({"merge_ask", "merged", "parked", "failed"}),
    "merge_ask": frozenset({"merged", "pr_open", "parked"}),
    "merged": frozenset({"done"}),
    "done": frozenset(),
    "parked": frozenset({"ready", "planned"}),
    "failed": frozenset({"ready", "parked"}),
}

#: A step in one of these holds an agent (the board's live rows).
ACTIVE_STATES = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review", "findings"})
#: Finished: its dependents may run.
FINISHED_STATES = frozenset({"merged", "done"})
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
    "race": ("pick",),
    "add_step": ("add", "skip"),
    "close": ("close",),
    # PG19: the agent is at its usage limit: continue in the next agent now,
    # or wait for the reset.
    "limited": ("continue", "wait"),
}



#: ``HOLDSPEAK_PROGRAMS=off``: the runner does not tick (every rig hub).
PROGRAMS_ENV = "HOLDSPEAK_PROGRAMS"

#: The check a repository names (``.holdspeak/program.json``), else this one.
DEFAULT_CHECK = "scripts/quick_check.sh"

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_LOCK = threading.RLock()


def programs_on() -> bool:
    return os.environ.get(PROGRAMS_ENV, "on").strip().lower() not in {"off", "0", "false", "no"}


class ProgramRefused(ServiceError):
    """A named refusal (``code``); HTTP and MCP answer ``{error, code}``."""

    def __init__(self, code: str, detail: str, *, status: int = 409) -> None:
        super().__init__(code, detail, context={"status": status})


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


def _engine_parked(step: Mapping[str, Any]) -> bool:
    return step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_ENGINE


def _live(steps: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [step for step in steps if step.get("state") not in CLOSED_STATES and step.get("state") != "failed"]


def your_turn(program: Mapping[str, Any], steps: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """What only he can do on this Program, one item per press.

    Design §6 (Control): only a core question, or what the rules send to
    him at the Program's level, is his. At Secure: merges, findings, failed
    steps, race winners, added steps, the Program's Done. At Normal and YOLO:
    core questions, findings left after the rounds, a person to ask for a
    review, and the failed steps once nothing else runs ("one row to him at
    the end")."""
    from .program_rules import level_of

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
        if isinstance(core, Mapping) and not core.get("cleared") and state not in CLOSED_STATES:
            items.append({**base, "id": f"{step['id']}:core", "kind": "core", "core": True,
                          "choices": list(DECIDE_CHOICES["core"]), "reason": core.get("reason"),
                          "title": f"{label.capitalize()}: {core.get('reason')}"})
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
            pr = f"PR #{number}" if number else "the PR"
            items.append({**base, "id": f"{step['id']}:merge", "kind": "merge",
                          "choices": list(DECIDE_CHOICES["merge"]),
                          "title": f"Merge {label}? ({pr}, check green"
                                   f"{', review passed' if step.get('review_verdict') == 'pass' else ''})"})
        elif state == "findings" and facts.get("findings_open"):
            for finding in step.get("findings") or []:
                if finding.get("decision") or not finding.get("to_owner", True):
                    continue
                items.append({**base, "id": f"{step['id']}:finding:{finding['id']}", "kind": "finding",
                              "finding_id": finding["id"], "level": finding.get("level"),
                              "core": bool(finding.get("core")), "choices": list(DECIDE_CHOICES["finding"]),
                              "title": f"Finding on {label}: {finding.get('text', '')}"})
        elif _engine_parked(step) and (level == "secure" or facts.get("park_is_his", True) or not live):
            items.append({**base, "id": f"{step['id']}:parked", "kind": "parked",
                          "choices": list(DECIDE_CHOICES["parked"]),
                          "title": f"Parked {label}: {step.get('parked_reason') or 'it stopped'}"})
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
    if (level == "secure" and steps and not live and not items and not program.get("closed_at")
            and program.get("state") not in ("drafting", "parked")):
        items.append({
            "program_id": program["id"], "program_title": program["title"], "step_id": "", "ordinal": 0,
            "step_title": "", "launch_id": None, "since": program.get("updated_at"),
            "project_id": program.get("project_id"), "for_person_id": program.get("for_person_id"), "pr": None,
            "id": f"{program['id']}:close", "kind": "close", "choices": list(DECIDE_CHOICES["close"]),
            "title": f"Close \u201c{program['title']}\u201d: every step is finished",
        })
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


def program_state(program: Mapping[str, Any], steps: list[Mapping[str, Any]]) -> str:
    """Worst state wins (AG0). Drafting and Parked are his; the rest is read
    off the steps."""
    current = str(program.get("state") or "drafting")
    if current in ("drafting", "parked"):
        return current
    if not steps:
        return "running"
    if your_turn(program, steps):
        return "waiting"
    if _live(steps):
        return "running"
    if any(step.get("state") == "failed" for step in steps):
        return "failed"
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

    def list(self, principal: Any = None) -> dict[str, Any]:
        """Every Program, waiting first, then running, drafting, done, parked;
        the most recently changed first inside a band."""
        rows = []
        for program in self.store.list_programs():
            steps = self.store.list_steps(program["id"])
            rows.append(self._summary(program, steps))
        _waiting_first(rows)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["state"]] = counts.get(row["state"], 0) + 1
        worst = min((row["state"] for row in rows), key=lambda s: PROGRAM_BAND.get(s, 9), default=None)
        return {"programs": rows, "counts": {k: v for k, v in counts.items() if v},
                "worst": worst, "worst_word": PROGRAM_WORDS.get(worst or "", "")}

    def get(self, principal: Any, program_id: str) -> dict[str, Any]:
        program = self._program(program_id)
        steps = self.store.list_steps(program["id"])
        return self._wire(program, steps)

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
                for item in your_turn(program, steps)
                if item["kind"] in ("finding", "ask_review") and (item.get("for_person_id") == person_id)
            ]
            waits = next((item for item in your_turn(program, steps) if item.get("pr")), None)
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
            if program["state"] in ("drafting", "parked", "done"):
                continue
            items.extend(your_turn(program, self.store.list_steps(program["id"])))
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
            if not (today(program.get("updated_at")) or any(today(step.get("updated_at")) for step in steps)):
                continue
            out["moved"] += 1
            state = program_state(program, steps)
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

    def _summary(self, program: Mapping[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
        top = self._top_steps(steps)
        state = program_state(program, steps)
        turn = your_turn(program, steps)
        done = sum(1 for step in top if self._ordinal_finished(steps, step["ordinal"]))
        checkpoints = self.store.list_checkpoints(program["id"])
        last = checkpoints[0] if checkpoints else None
        summary = {
            "id": program["id"], "title": program["title"], "state": state,
            "state_word": PROGRAM_WORDS.get(state, state), "done": done, "total": len(top),
            "your_turn": len([item for item in turn if item["kind"] != "answer"]),
            "asks": len([item for item in turn if item["kind"] == "answer"]),
            "project_id": program.get("project_id"), "control": program["control"],
            "updated_at": program["updated_at"], "created_at": program["created_at"],
            "last_checkpoint": last,
            "in_state_seconds": _seconds_between(program["updated_at"]),
        }
        if state == "done":
            ended = max((str(step.get("ended_at") or "") for step in steps), default="") or program["updated_at"]
            summary["done_in"] = duration_words(_seconds_between(program["created_at"], ended))
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

    def step_wire(self, program: Mapping[str, Any], step: Mapping[str, Any],
                  checkpoints: list[dict[str, Any]]) -> dict[str, Any]:
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
            "report": step.get("report"), "last_checkpoint": last,
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
        }

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
        checkpoints = self.store.list_checkpoints(program["id"])
        summary = self._summary(program, steps)
        top = []
        for step in self._top_steps(steps):
            row = self.step_wire(program, step, checkpoints)
            row["contenders"] = [self.step_wire(program, other, checkpoints)
                                 for other in steps if other.get("race_of") == step["id"]]
            top.append(row)
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
            "your_turn_items": your_turn(program, steps),
            "decided_for_you": self.decided_for_you(program["id"]),
            "control_word": level_word(program.get("control")),
            "spend_limit_usd": program.get("spend_limit_usd"), "closed_at": program.get("closed_at"),
            "revision": int(program.get("revision") or 0),
            "status_line": self._status_line(program, summary),
        }

    def _status_line(self, program: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
        parts = [summary["state_word"], f"{summary['done']} of {summary['total']} done"]
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
        with _LOCK:
            self.store.save_program(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent",
                             f"Made the program{' from the ' + shape['name'] + ' template' if shape else ''}")
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
        if fields.get("reviewer_profile") is not None or fields.get("reviewer_engine") is not None:
            reviewer = self._profile(fields.get("reviewer_profile"), "reviewer_profile") or program.get("reviewer_profile")
            program["reviewer_profile"] = reviewer
            program["reviewer_engine"] = self._engine_id(fields.get("reviewer_engine"), reviewer, "reviewer_engine")
            changed.append("reviewer")
        if not changed:
            raise ProgramRefused("nothing_to_change", "Name a field to change.", status=400)
        with _LOCK:
            self._touch(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent", "Changed " + ", ".join(changed))
            self.changed(program["id"], verb="update")
        return self.get(principal, program["id"])

    def plan(
        self, principal: Any, program_id: str, *, steps: list[Mapping[str, Any]],
        size: Optional[str] = None, replace: bool = False,
    ) -> dict[str, Any]:
        """Replace or append steps. A step: ``title``, ``brief``, ``owns``,
        ``after`` (ordinals), ``profile``, ``engine``, ``prefer_idle``,
        ``effort``, ``race``, ``gate_check``, ``gate_review``
        (none|agent|person), ``review_depth``, ``gate_merge``, ``origin_ref``,
        ``for_person_id``. ``size: auto`` sets effort by rule."""
        from ..program_templates import get_template

        program = self._program(program_id)
        self._require_writer(principal, program, "plan")
        if not isinstance(steps, list) or not steps and not replace:
            raise ProgramRefused("steps_required", "Give at least one step.", status=400)
        existing = self.store.list_steps(program["id"])
        if replace and any(step.get("state") not in ("planned", "ready") for step in existing):
            raise ProgramRefused("program_running", "Steps that started cannot be replaced. Park the program, or append.")
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
            if any(value >= ordinal or value < 1 for value in after):
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
            depth = str(raw.get("review_depth") or shape.get("review_depth") or "delta").lower()
            if depth not in REVIEW_DEPTHS:
                raise ProgramRefused("review_depth_invalid", f"Step {index}: depth is glance, delta or standard.", status=400)
            merge = str(raw.get("gate_merge") or shape.get("gate_merge") or "level").lower()
            merge = _GATE_MERGE_ALIASES.get(merge, merge)
            if merge not in GATE_MERGE:
                raise ProgramRefused("gate_merge_invalid", f"Step {index}: merge is level, owner or none.", status=400)
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
            })
        with _LOCK:
            if replace:
                for step in existing:
                    self.store.delete_step(step["id"])
            for step in made:
                self.store.save_step(step)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent",
                             f"{'Planned' if replace else 'Added'} {len(made)} step{'s' if len(made) != 1 else ''}")
            self._touch(program)
            self.changed(program["id"], verb="plan")
        return self.get(principal, program["id"])

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
        if not steps:
            raise ProgramRefused("steps_required", "Add a step before you start the program.")
        if program["state"] not in ("drafting", "parked"):
            raise ProgramRefused("program_started", "The program runs already.")
        with _LOCK:
            program["state"] = "running"
            self._touch(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent", "Started the program")
            self.changed(program["id"], verb="start")
        self._tick_now(program["id"])
        return self.get(principal, program["id"])

    def park(self, principal: Any, program_id: str) -> dict[str, Any]:
        program = self._program(program_id)
        self._require_writer(principal, program, "park")
        with _LOCK:
            program["state"] = "parked"
            self._touch(program)
            self._checkpoint(program, None, "owner" if _is_owner(principal) else "agent",
                             "Parked the program; the worktrees stay")
            self.changed(program["id"], verb="park")
        return self.get(principal, program["id"])

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
            self._save(step)
            self._checkpoint(program, step, "agent", "Said it is done; the engine waits for the commit", kernel=False)
            for item in follow_ups or []:
                self.propose_step(program, step, item)
            self.changed(program["id"], step["id"], verb="step_done")
        self._tick_now(program["id"])
        return {"program_id": program["id"], "step_id": step["id"], "state": step["state"],
                "waits_for": "a new commit on the step's branch"}

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

    def decide(
        self, principal: Any, program_id: str, step_id: str, *, kind: str, choice: str,
        finding_id: Optional[str] = None, reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """His press on a your-turn item (owner only)."""
        self._require_owner(principal, "decide")
        program = self._program(program_id)
        kind, choice = str(kind or ""), str(choice or "")
        if kind == "close":
            return self.close(principal, program_id)
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
                    answer = self.runner().merge(program, step, by="owner")
            elif kind == "finding":
                answer = self._decide_finding(program, step, finding_id, choice, reason)
            elif kind == "parked":
                if step["state"] != "parked":
                    raise ProgramRefused("not_parked", "This step is not parked.")
                if choice == "resume":
                    step["rounds"] = 0
                    step["parked_by"], step["parked_reason"] = None, None
                    self.transition(program, step, "ready", by="owner", line="Resumed the step")
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
                    facts["core"] = core
                    self._save(step)
                    self._checkpoint(program, step, "owner", f"Go on: {core.get('reason')}")
                else:
                    facts.pop("core", None)
                    self.transition(program, step, "parked", by="owner", parked_by=PARKED_BY_OWNER,
                                    parked_reason="You parked this step", line=f"Parked: {core.get('reason')}")
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
                   line: str = "", **fields: Any) -> dict[str, Any]:
        """Move one step along the table of §4 (a refused move raises), write
        its checkpoint (and the kernel operation for an engine decision)."""
        current = str(step.get("state") or "")
        if to != current and to not in STEP_TRANSITIONS.get(current, frozenset()):
            raise ProgramRefused("transition_invalid", f"A step cannot go from {current} to {to}.")
        step.update(fields)
        now = self._clock()
        step["state"] = to
        if to != "ready":
            step["held_reason"] = None if to != current else step.get("held_reason")
        if to == "briefed" and not step.get("started_at"):
            step["started_at"] = now
        if to in CLOSED_STATES or to == "failed":
            step["ended_at"] = step.get("ended_at") or now
        elif to in ("ready", "planned"):
            step["ended_at"] = None
        self._save(step)
        if to == "pr_open" and current != "pr_open" and step.get("pr_url"):
            from . import program_decisions

            program_decisions.link_pr(self.db, step)
        if line:
            self._checkpoint(program, step, by, line)
        return step

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
                    *, kernel: bool = True, decision_record_id: Optional[str] = None) -> dict[str, Any]:
        operation_id = None
        if kernel and by == "engine":
            operation_id = self._kernel_record(program, step, line)
        at = self._clock()
        undo: dict[str, Any] = {"decision_record_id": decision_record_id} if decision_record_id else {}
        pin = self.pin(step, line)
        if pin:
            undo["pin"] = pin
        ident = self.store.add_checkpoint(step_id=str((step or {}).get("id") or ""), program_id=program["id"],
                                          at=at, by=by, line=line, operation_id=operation_id, undo=undo or None)
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

    def changed(self, program_id: str, step_id: Optional[str] = None, *, verb: str = "step") -> None:
        """Recompute the Program's state, rewrite its note, emit the frames."""
        program = self._program(program_id)
        steps = self.store.list_steps(program_id)
        state = program_state(program, steps)
        if state == "done" and not program.get("closed_at"):
            from .program_rules import decide

            self.reach_phone(program, None, "program_done",
                             f"{program['title']} is finished: every step is done.")

            outcome = decide(program.get("control"), "program_done", {})
            if not outcome.to_owner:
                program["closed_at"] = self._clock()
                self.store.save_program(program)
                self.engine_decision(program, None, "program_done", outcome, "Closed the program: every step is finished")
        if state != program["state"]:
            before = program["state"]
            program["state"] = state
            self._touch(program)
            if before not in ("drafting",) or state != "running":
                self._checkpoint(program, None, "engine", _STATE_LINES.get(state, f"The program is {state}"))
        self.write_note(program, steps)
        turn = [item for item in your_turn(program, steps) if item["kind"] != "answer"]
        self._broadcast("program_changed", {
            "program_id": program_id, "step_id": step_id, "state": state, "your_turn": len(turn),
        })
        try:
            from ..runtime import composition

            composition.notify_desk_changed("program", program_id, verb)
        except Exception:
            pass

    def _tick_now(self, program_id: str) -> None:
        """A press moves the program at once (not on the next 30 s tick)."""
        if not programs_on():
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
        if summary["your_turn"]:
            head.append(f"{summary['your_turn']} wait{'s' if summary['your_turn'] == 1 else ''} on you")
        lines += [" · ".join(head), ""]
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
        turn = [item for item in your_turn(program, steps) if item["kind"] != "answer"]
        asks = [item for item in your_turn(program, steps) if item["kind"] == "answer"]
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


def _check_name(command: str) -> str:
    """``quick_check.sh`` for ``FOO=1 sh scripts/quick_check.sh --x``."""
    import shlex

    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    words = [word for word in words if "=" not in word.split("/")[0] or word.startswith("-")]
    words = [word for word in words if word not in ("sh", "bash", "uv", "run", "python", "env")]
    return Path(words[0]).name if words else command


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
    "default_program_service", "duration_words", "program_state", "programs_on", "step_origin",
    "triage_effort", "your_turn",
]
