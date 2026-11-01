"""Dreaming: a Program that runs only at night (PG-LANG LANG12, JRN2, 2026-10-31).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §5.5 and
PROGRAM-JOURNEYS-2026-10-31.md J2 "The dreaming program". All defaults are
approved (§15, 2026-10-31).

- **The window.** A Program with ``night 23:30–07:00 · at most 8 steps``
  hands steps only inside its window. Outside it, every Ready step is held
  with "sleeps until 23:30"; with ``at most``, the night stops handing after
  that many steps ("the night's 8 steps ran").
- **Add to tonight** (:func:`add_to_night`, ``program.add_to_night``): a Door
  task, a note line or a step of another Program becomes a Planned step of
  the night Program, marked for tonight's planning (no magic word).
- **Planned at the window's start.** At the first tick inside the window,
  each marked step goes to the cheap planner (``program.night_item@1``, ONE
  call per item on the ``agent.plan`` assignment, through the shaper's
  path): a tiny step of at most three files inside ``within``. Until it is
  planned, it is held with "planning for tonight". With no engine, it runs
  as written; sizing (LANG8) still holds a step that is too big.
- **The morning digest.** After the window ends, ONE line: "Since last
  night: 4 steps done, 1 waits on you, 1 split" is written once per night (a
  ``night_digest`` checkpoint), on top of the handover note as "Since last
  night", and sent through Reach (``ReachService.night_line``).

2026-11-01 (J2 on the hub, the rest of LANG12, JRN3, JRN4):

- **The Dreaming template** (``program_templates.DREAMING``).
- **The backlog by rule** (:func:`read_backlog`), once at the window's
  start: the open Door tasks with the word "dream", and the Later tasks of
  the Program's own findings; each becomes one step for tonight's planner
  (as Add to tonight; YOLO adds it and says so; below YOLO one line says how
  many wait for his Add to tonight), never more than the night's room.
- **The red-main hold** (JRN3, :func:`red_main_filter`): when the base
  branch's newest finished run on GitHub (``gh run list``) failed, the night
  plans ONE step "Make main green" first and holds the rest ("waits: main is
  red") until a run is green again.
- **Two red steps in a row stop the night** ("the night stopped after two
  red steps"; the digest says so).
- **The window's end** (:func:`end_working`): a step whose agent still works
  is asked to commit what it has; at its turn's end (or 10 minutes later) the
  engine commits what is left and parks it: "Night ended; parked with a
  commit".
- **The morning digest goes through Reach** (JRN4): ``night_line`` carries
  the night's Your turn items; Reach sends it at the digest hour as the one
  morning message, with a briefing page link for the first held item.

Not built here: the canon scanner's residues and the failing tests of the
last main run as backlog sources, ``within`` as a core-question bound on the
diff, and one briefing page for several items (the page's digest half is
DIR9).
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from . import program_sizing as sizing

log = get_logger("program_night")

CONTRACT = "program.night_item"
CONTRACT_REVISION = "1"
TEMPERATURE = 0.2
DEADLINE_SECONDS = 240
MAX_TOKENS = 6000
#: The digest is written in the hours after the window's end, never later.
DIGEST_HOURS = 12
#: The note shows the last digest this long.
NOTE_HOURS = 20
#: The kinds Add to tonight takes.
ITEM_KINDS = ("action", "note", "program_step")
#: The checkpoint kind of a night's digest.
DIGEST_KIND = "night_digest"
#: The checkpoint kinds of a night's backlog read, its red-main hold and its stop.
BACKLOG_KIND, RED_MAIN_KIND, STOP_KIND = "night_backlog", "night_red_main", "night_stop"
#: A night stops after this many red steps in a row (PG-LANG §5.5).
RED_IN_A_ROW = 2
#: How long a step's agent has to commit what it has after the window's end.
END_MINUTES = 10
#: How long the base branch's state is read again (seconds).
RED_READ_SECONDS = 120
_DREAM = __import__("re").compile(r"\bdream(s|ing)?\b", __import__("re").I)
_RED_CACHE: dict[str, tuple[float, Optional[str]]] = {}
#: The step states a working agent holds at the window's end.
_AGENT_STATES = ("briefed", "working", "waiting", "limited", "check_failed")
_PLANNING: dict[str, threading.Thread] = {}

ITEM_RULES = """RULES
- One tiny step: one concern, at most 3 owned paths (the files the change edits), each inside the bounds below.
- "title": what the change does, under 80 characters.
- "brief": one to four sentences, under 400 words: what the change does and how it is checked.
- "owns": the paths. Use a path from the files below when it exists; a new path when the file is new.
- The step must fit in the size given below, with its brief and the files it owns.
- "say": one short line."""


# ── the window ───────────────────────────────────────────────────────

def _hm(text: str) -> tuple[int, int]:
    hour, minute = str(text).split(":", 1)
    return int(hour), int(minute)


def window(night: Mapping[str, Any], moment: datetime) -> tuple[datetime, datetime]:
    """The night window that started last at or before ``moment`` (local, aware)."""
    local = moment.astimezone()
    sh, sm = _hm(night["start"])
    eh, em = _hm(night["end"])
    start = local.replace(hour=sh, minute=sm, second=0, microsecond=0)
    if start > local:
        start -= timedelta(days=1)
    end = start.replace(hour=eh, minute=em)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def inside(night: Mapping[str, Any], moment: datetime) -> bool:
    start, end = window(night, moment)
    return start <= moment.astimezone() < end


def night_key(start: datetime) -> str:
    """The night's name: the local date it started on."""
    return start.strftime("%Y-%m-%d")


def _parse(stamp: Any) -> Optional[datetime]:
    try:
        value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _between(stamp: Any, start: datetime, end: datetime) -> bool:
    value = _parse(stamp)
    return value is not None and start <= value <= end


# ── the dispatcher's checks ──────────────────────────────────────────

def night_room(runner: Any, program: Mapping[str, Any], ready: list[dict[str, Any]]) -> Optional[int]:
    """How many steps the night may still hand now: ``None`` (no night, or
    no ``at most``), ``0`` (asleep, or the night's steps ran: each Ready step
    is held with the words), else the room left."""
    night = program.get("night")
    if not isinstance(night, Mapping) or not night.get("start"):
        return None
    now = runner._now()
    start, end = window(night, now)
    if not start <= now.astimezone() < end:
        for step in ready:
            runner._hold(step, f"sleeps until {night['start']}")
        return 0
    stopped = _red_in_a_row(runner, program, start, end)
    if stopped:
        for step in ready:
            runner._hold(step, f"the night stopped after {RED_IN_A_ROW} red steps")
        return 0
    most = night.get("max_steps")
    if not most:
        return None
    ran = sum(1 for step in runner.service.store.list_steps(program["id"])
              if not step.get("race_of") and _between(step.get("started_at"), start, end))
    room = int(most) - ran
    if room <= 0:
        for step in ready:
            runner._hold(step, f"the night's {most} step{'s' if int(most) != 1 else ''} ran")
        return 0
    return room


def _night_rows(runner: Any, program: Mapping[str, Any], start: datetime, end: datetime) -> list[dict[str, Any]]:
    return [step for step in runner.service.store.list_steps(program["id"])
            if not step.get("race_of") and _between(step.get("started_at"), start, end)]


def _red(step: Mapping[str, Any]) -> bool:
    from .program_service import PARKED_BY_ENGINE

    return step.get("state") == "failed" or (step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_ENGINE
                                             and not str(step.get("parked_reason") or "").startswith("Night ended"))


def _red_in_a_row(runner: Any, program: Mapping[str, Any], start: datetime, end: datetime) -> bool:
    """The night's last ``RED_IN_A_ROW`` finished steps are all red; the
    first time, one ``night_stop`` line says so."""
    from .program_service import CLOSED_STATES

    ended = sorted((step for step in _night_rows(runner, program, start, end)
                    if step.get("state") in CLOSED_STATES or step.get("state") == "failed"),
                   key=lambda step: str(step.get("ended_at") or step.get("updated_at") or ""))
    last = ended[-RED_IN_A_ROW:]
    if len(last) < RED_IN_A_ROW or not all(_red(step) for step in last):
        return False
    key = night_key(start)
    service = runner.service
    if not any(row.get("kind") == STOP_KIND and (row.get("undo") or {}).get("night") == key
               for row in service.store.list_checkpoints(program["id"])):
        service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="engine",
                                     line=f"The night stopped after {RED_IN_A_ROW} red steps in a row",
                                     kind=STOP_KIND, undo={"night": key})
    return True


# ── JRN3: no step is handed while the base branch is red ─────────────

def base_red(runner: Any, program: Mapping[str, Any]) -> Optional[str]:
    """The base branch's newest finished run on GitHub (``gh run list``), in
    words when it failed ("Nightly failed on 1a2b3c4d"); ``None`` when it is
    green, still running, or cannot be read (no gh, no remote: the night is
    never held on a guess). Read again after ``RED_READ_SECONDS``."""
    import json as _json

    root = str(program.get("repo_root") or "")
    base = str(program.get("base_branch") or "main")
    key = f"{program['id']}:{root}:{base}"
    cached = _RED_CACHE.get(key)
    if cached is not None and time.monotonic() - cached[0] < RED_READ_SECONDS:
        return cached[1]
    words: Optional[str] = None
    try:
        proc = runner._run(["gh", "run", "list", "--branch", base, "--limit", "5", "--json",
                            "conclusion,status,name,headSha"], cwd=root)
        rows = _json.loads(proc.stdout or "[]") if proc.returncode == 0 else []
    except Exception as exc:
        log.debug(f"the base branch's runs not read: {exc}")
        rows = []
    done = [row for row in rows if isinstance(row, Mapping) and str(row.get("status") or "") == "completed"]
    if done and str(done[0].get("conclusion") or "") in ("failure", "timed_out", "startup_failure"):
        words = f"{done[0].get('name') or 'the check'} failed on {str(done[0].get('headSha') or '')[:8]}".strip()
    _RED_CACHE[key] = (time.monotonic(), words)
    return words


def _green_step(steps: list[Mapping[str, Any]], key: str) -> Optional[Mapping[str, Any]]:
    from .program_service import CLOSED_STATES

    return next((step for step in steps if ((step.get("facts") or {}).get("night_green") or {}).get("night") == key
                 and step.get("state") not in CLOSED_STATES), None)


def red_main_filter(runner: Any, program: Mapping[str, Any], ready: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The Ready steps the night may hand now. Main red: ONE step "Make main
    green" is planned first (once a night) and is the only one handed; the
    rest wait ("waits: main is red"). Green again: one line, and all go on."""
    night = program.get("night")
    if not isinstance(night, Mapping) or not night.get("start"):
        return ready
    service = runner.service
    start, _end = window(night, runner._now())
    key = night_key(start)
    red = base_red(runner, program)
    rows = [row for row in service.store.list_checkpoints(program["id"]) if row.get("kind") == RED_MAIN_KIND
            and (row.get("undo") or {}).get("night") == key]
    if red is None:
        if rows and rows[0].get("choice") == "red":
            service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="engine",
                                         line="Main is green again; the night goes on", kind=RED_MAIN_KIND,
                                         choice="green", undo={"night": key})
        return ready
    steps = service.store.list_steps(program["id"])
    green = _green_step(steps, key)
    if green is None:
        from ..kernel.program_ops import RUNNER

        base = str(program.get("base_branch") or "main")
        first = next((step for step in steps if step["state"] in ("planned", "ready") and not step.get("race_of")), None)
        before = {row["id"] for row in steps}
        service.plan(RUNNER, program["id"], steps=[{
            "title": f"Make {base} green",
            "brief": (f"The base branch {base} is red: {red}. Find the cause in that run's log and make it green. "
                      "Change only what the red run names; add no feature."),
        }], before=first["id"] if first else None, waits=False, by="engine")
        green = next(row for row in service.store.list_steps(program["id"]) if row["id"] not in before)
        facts = dict(green.get("facts") or {})
        facts["night_green"] = {"night": key, "red": red}
        green["facts"] = facts
        service.save_step(green)
        service.store.add_checkpoint(step_id=green["id"], program_id=program["id"], at=service._clock(), by="engine",
                                     line=f"Main is red ({red}): step {green['ordinal']} makes it green first; "
                                          "the rest wait", kind=RED_MAIN_KIND, choice="red", undo={"night": key})
        service.changed(program["id"], green["id"], verb="night")
    elif not rows or rows[0].get("choice") != "red":
        service.store.add_checkpoint(step_id=green["id"], program_id=program["id"], at=service._clock(), by="engine",
                                     line=f"Main is red again ({red}); the rest wait", kind=RED_MAIN_KIND,
                                     choice="red", undo={"night": key})
    # The insert renumbered the steps: read the Ready rows again.
    ready = [fresh for fresh in (service.store.get_step(step["id"]) for step in ready) if fresh is not None]
    allowed = []
    for step in ready:
        if step["id"] == green["id"]:
            allowed.append(step)
        else:
            runner._hold(step, "waits: main is red")
    return allowed


# ── the window's end: a working step commits what it has and parks ───

def end_working(runner: Any, program: Mapping[str, Any], start: datetime, end: datetime) -> int:
    """After the window: each step whose agent still holds it is asked once
    to commit what it has; at its turn's end, or ``END_MINUTES`` after the
    ask, the engine commits what is left and parks it. The steps still
    waiting for their agent."""
    from .program_service import PARKED_BY_ENGINE

    service = runner.service
    waiting = 0
    now = runner._now()
    for step in _night_rows(runner, program, start, end):
        if step.get("state") not in _AGENT_STATES or not step.get("launch_id"):
            continue
        facts = dict(step.get("facts") or {})
        asked = facts.get("night_end")
        flight = runner.flight(str(step["launch_id"]))
        turn_over = str(flight.get("state") or "") not in ("working", "starting", "")
        if not asked:
            if not turn_over:
                try:
                    runner.prompt_builder(step, "HoldSpeak: the night ended. Commit what you have on this branch "
                                                "now, then end your turn.")
                except Exception as exc:
                    log.info(f"the night's end was not typed: {exc}")
                facts["night_end"] = {"at": service._clock(), "turn": str(flight.get("turn_id") or "")}
                step["facts"] = facts
                service.save_step(step)
                service._checkpoint(program, step, "engine", "The night ended: asked the agent to commit what it has")
                waiting += 1
                continue
        else:
            at = _parse(asked.get("at"))
            late = at is not None and now - at >= timedelta(minutes=END_MINUTES)
            ended = turn_over and str(flight.get("turn_id") or "") != str(asked.get("turn") or "")
            if not (ended or late or turn_over):
                waiting += 1
                continue
        head = runner.commit_worktree(program, step) or runner._git(str(step.get("worktree") or ""), "rev-parse", "HEAD")
        with_commit = bool(head) and head != (facts.get("base_commit") or step.get("head_commit") or "")
        facts.pop("night_end", None)
        service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE, facts=facts,
                           head_commit=head or step.get("head_commit"),
                           parked_reason="Night ended; parked with a commit" if with_commit else "Night ended; parked",
                           line="Night ended; parked with a commit" if with_commit else "Night ended; parked",
                           ending="interrupted")
    return waiting


# ── the backlog by rule, at the window's start ───────────────────────

def backlog_items(service: Any, program: Mapping[str, Any]) -> list[dict[str, str]]:
    """The open Door tasks the night may take, by rule (never invented):
    the word "dream" in the task, or a Later task of one of this Program's
    own findings. ``[{kind, id, task}]``, oldest first."""
    own = {step["id"] for step in service.store.list_steps(program["id"])}
    out = []
    try:
        rows = service.db.meetings.list_action_items(include_completed=False)
    except Exception as exc:
        log.debug(f"the backlog was not read: {exc}")
        return []
    for row in reversed(rows):
        task = str(getattr(row, "task", "") or "")
        source_type = str(getattr(row, "source_type", "") or "")
        source_ref = str(getattr(row, "source_ref", "") or "")
        later = source_type == "program_step" and source_ref.split(":")[1:2] and source_ref.split(":")[1] in own
        if _DREAM.search(task) or later:
            out.append({"kind": "action", "id": str(row.id), "task": task})
    return out


def wake_parked(runner: Any, program: Mapping[str, Any]) -> int:
    """At the window's start, a step the last night parked at its end goes
    on from its checkpoint, in its own worktree (Resume's path)."""
    from .program_service import NIGHT_ENDED

    service = runner.service
    woke = 0
    for step in service.store.list_steps(program["id"]):
        if step.get("state") == "parked" and str(step.get("parked_reason") or "").startswith(NIGHT_ENDED):
            step["parked_by"], step["parked_reason"] = None, None
            service.transition(program, step, "ready", line="Goes on tonight from where the night ended")
            woke += 1
    if woke:
        fresh = service._program(program["id"])
        if fresh.get("closed_at"):
            # A Done night Program opens again for tonight (one record, one Note).
            fresh["closed_at"] = None
            service.store.save_program(fresh)
            service._checkpoint(fresh, None, "engine", "Opened again for tonight")
        service.changed(program["id"], None, verb="night")
    return woke


def read_backlog(runner: Any, program: Mapping[str, Any], start: datetime, end: datetime) -> int:
    """Once a night, at its start: the backlog's items become steps for
    tonight's planner, up to the night's room. YOLO adds them and says so
    (Overturn); below YOLO one line says how many wait for his Add to
    tonight. The count added."""
    from ..principals import Principal, PrincipalKind
    from .program_rules import level_of
    from .program_service import CLOSED_STATES

    service = runner.service
    key = night_key(start)
    if any(row.get("kind") == BACKLOG_KIND and (row.get("undo") or {}).get("night") == key
           for row in service.store.list_checkpoints(program["id"])):
        return 0
    taken = {((step.get("facts") or {}).get("night_item") or {}).get("ref") for step in service.store.list_steps(program["id"])}
    items = [item for item in backlog_items(service, program) if f"action:{item['id']}" not in taken]
    night = program.get("night") or {}
    open_now = sum(1 for step in service.store.list_steps(program["id"])
                   if step.get("state") not in CLOSED_STATES and step.get("state") != "failed")
    room = max(0, int(night.get("max_steps") or len(items) + open_now) - open_now)
    items = items[:room]
    added = 0
    if items and level_of(program.get("control")) == "yolo":
        engine = Principal(PrincipalKind.AGENT, "program-engine:night-backlog")
        for item in items:
            try:
                if add_to_night(service, engine, kind=item["kind"], item_id=item["id"], program_id=program["id"])["added"]:
                    added += 1
            except Exception as exc:
                log.info(f"backlog item {item['id']} not added: {exc}")
        line = f"Read the backlog for tonight: {added} item{'s' if added != 1 else ''} added"
    elif items:
        line = (f"The backlog has {len(items)} item{'s' if len(items) != 1 else ''} for tonight; "
                "Add to tonight takes each")
    else:
        line = "Read the backlog for tonight: nothing new"
    service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="engine", line=line,
                                 kind=BACKLOG_KIND, undo={"night": key, "items": [item["id"] for item in items]})
    return added


def step_hold(runner: Any, program: Mapping[str, Any], step: dict[str, Any]) -> bool:
    """A step marked for tonight waits for its planning."""
    if (step.get("facts") or {}).get("night_plan") != "pending":
        return False
    runner._hold(step, "planning for tonight")
    return True


# ── the planning call (one per item) ─────────────────────────────────

def schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "program_night_item", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["say", "title", "brief", "owns"],
        "properties": {"say": {"type": "string", "maxLength": 300}, "title": {"type": "string", "maxLength": 120},
                       "brief": {"type": "string", "maxLength": 3000},
                       "owns": {"type": "array", "maxItems": 3, "items": {"type": "string", "maxLength": 300}}}}}}


def _inside_within(path: str, within: list[str]) -> bool:
    clean = path.strip().strip("/")
    return not within or any(clean == bound.strip().strip("/") or clean.startswith(bound.strip().rstrip("/") + "/")
                             for bound in within)


def read_item(output: str, within: list[str]) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    from ..intel.parsing import _extract_json

    try:
        data = _extract_json(str(output or "").strip())
    except Exception:
        data = None
    if not isinstance(data, Mapping):
        return None, "The answer is not JSON with a 'title', a 'brief' and 'owns'."
    title = " ".join(str(data.get("title") or "").split())[:120]
    brief = str(data.get("brief") or "").strip()
    owns = [str(path).strip() for path in data.get("owns") or [] if str(path).strip()]
    if not title or not brief:
        return None, "Give a title and a brief."
    if len(owns) > 3:
        return None, "Own at most 3 paths."
    outside = [path for path in owns if not _inside_within(path, within)]
    if outside:
        return None, f"{outside[0]} is outside the bounds: {', '.join(within)}."
    return {"say": " ".join(str(data.get("say") or "").split())[:300], "title": title, "brief": brief,
            "owns": owns}, None


def messages(program: Mapping[str, Any], step: Mapping[str, Any], *, budget: Optional[int], engine_word: str,
             repo: Mapping[str, Any], error: Optional[str] = None) -> tuple[str, str]:
    """The system and user prompt of ``program.night_item@1``."""
    within = list(program.get("within") or [])
    system_parts = [
        "You plan one tiny step of a HoldSpeak Program that runs at night on a small model. "
        'You answer JSON only: {"say": "...", "title": "...", "brief": "...", "owns": ["..."]}.',
        ITEM_RULES,
        "BOUNDS\n" + ("\n".join(f"- {bound}" for bound in within) if within else "- the whole repository"),
    ]
    if budget:
        system_parts.append(f"SIZE\nThe agent that builds the step ({engine_word}) has a context of "
                            f"{sizing.k_words(budget)} tokens; the step must fit in "
                            f"{sizing.k_words(sizing.share_of(budget))} tokens with its brief and the files it owns.")
    item = dict((step.get("facts") or {}).get("night_item") or {})
    parts = [f"THE PROGRAM\n{program.get('title') or ''}\n{str(program.get('goal_markdown') or '').strip()}".rstrip(),
             "THE ITEM (the owner's words)\n" + (str(step.get("brief_markdown") or "").strip() or step["title"])]
    if item.get("from"):
        parts.append(f"WHERE IT IS FROM\n{item['from']}")
    if repo.get("likely"):
        parts.append("FILES THE ITEM IS LIKELY ABOUT (size in tokens)\n" + "\n".join(repo["likely"][:40]))
    if error:
        parts.append("YOUR LAST ANSWER COULD NOT BE USED. The reason:\n" + error + "\nAnswer again, correct.")
    return "\n\n".join(system_parts), "\n\n".join(parts)


def ask_item(service: Any, principal: Any, program: Mapping[str, Any], step: Mapping[str, Any], *,
             invoke_fn: Optional[Callable[[dict[str, Any]], tuple[Optional[str], str]]] = None,
             ) -> tuple[Optional[dict[str, Any]], str, Optional[str]]:
    """ONE planning call with one retry: ``(fields or None, engine, reason)``."""
    from . import program_shaper as shaper
    from .program_planner import repo_ground

    try:
        capability, revision, _profile, label = shaper.resolve_engine(service.db)
    except Exception as exc:
        return None, "", str(getattr(exc, "detail", "") or "No engine is set for planning.")
    call = invoke_fn or (lambda payload: shaper.invoke(service.db, principal, capability, revision, payload,
                                                       contract=CONTRACT, contract_revision=CONTRACT_REVISION,
                                                       deadline=DEADLINE_SECONDS))
    root = str(program.get("repo_root") or "") or None
    words = f"{step['title']}\n{step.get('brief_markdown') or ''}"
    repo = repo_ground(root, words)
    profile = str(step.get("profile") or program.get("default_profile") or "claude-default")
    budget, engine_word = sizing.budget_of(service, explicit=None, program_budget=program.get("budget_tokens"),
                                           step_budget=step.get("budget_tokens"),
                                           agent=(profile, step.get("engine") or program.get("default_engine")),
                                           default_engine=program.get("default_engine"))
    within = list(program.get("within") or [])
    error: Optional[str] = None
    model = ""
    for _attempt in (1, 2):
        system, user = messages(program, step, budget=budget, engine_word=engine_word, repo=repo, error=error)
        payload = {"system_prompt": system, "user_prompt": user, "temperature": TEMPERATURE,
                   "max_tokens": MAX_TOKENS, "response_format": schema()}
        try:
            output, model = call(payload)
        except Exception as exc:
            log.warning(f"night planning call failed: {exc}")
            output = None
        if output is None:
            return None, model or label, f"{model or label or 'the engine'} did not answer"
        answer, error = read_item(output, within)
        if answer is not None:
            return answer, model or label, None
    return None, model or label, f"its answer could not be used ({error})"


def plan_pending(runner: Any, program_id: str) -> bool:
    """Plan every step marked for tonight (one call each)."""
    service = runner.service
    moved = False
    for step in service.store.list_steps(program_id):
        program = service.store.get_program(program_id)
        if program is None:
            return moved
        if (step.get("facts") or {}).get("night_plan") != "pending" or step["state"] not in ("planned", "ready"):
            continue
        started = time.monotonic()
        fields, engine, reason = ask_item(service, runner.principal, program, step)
        fresh = service.store.get_step(step["id"])
        if fresh is None or fresh["state"] not in ("planned", "ready"):
            continue
        facts = dict(fresh.get("facts") or {})
        if fields is None:
            facts["night_plan"] = "as_written"
            fresh["facts"] = facts
            fresh["held_reason"] = None
            service.save_step(fresh)
            service._checkpoint(program, fresh, "engine", f"Runs as written tonight: the planner could not plan it ({reason})"[:400])
        else:
            facts["night_plan"] = "planned"
            facts["night_planned"] = {"engine": engine or None, "seconds": round(time.monotonic() - started, 1),
                                      "say": fields.get("say") or ""}
            fresh.update(title=fields["title"], brief_markdown=fields["brief"], owns=list(fields["owns"]), facts=facts,
                         held_reason=None)
            service.save_step(fresh)
            service._checkpoint(program, fresh, "engine",
                                f"Planned for tonight: step {fresh['ordinal']} · {fields['title']}"[:400])
        moved = True
    if moved:
        service.changed(program_id, None, verb="night")
    return moved


def _plan_thread(runner: Any, program_id: str) -> None:
    try:
        plan_pending(runner, program_id)
    except Exception as exc:
        log.error(f"night planning of {program_id} failed: {exc}", exc_info=True)
    finally:
        _PLANNING.pop(program_id, None)
    runner.tick_program(program_id)


# ── the morning digest ───────────────────────────────────────────────

def _plural(n: int, one: str, many: str) -> str:
    return one.format(n=n) if n == 1 else many.format(n=n)


def digest_lines(service: Any, program: Mapping[str, Any], start: datetime, end: datetime) -> list[str]:
    """``["Since last night: 4 steps done, 1 waits on you, 1 split", "Merged: #1710 · #1711"]``;
    ``[]`` when the night did nothing (no counter of zero is written)."""
    from .program_service import FINISHED_STATES

    steps = service.store.list_steps(program["id"])
    done = [step for step in steps if not step.get("race_of") and step.get("state") in FINISHED_STATES
            and _between(step.get("ended_at"), start, end)]
    parked = [step for step in steps if step.get("state") == "parked"
              and _between(step.get("ended_at") or step.get("updated_at"), start, end + timedelta(hours=DIGEST_HOURS))]
    waits = [item for item in service._turn(program, steps) if item.get("kind") != "answer"]
    splits = 0
    for row in service.store.list_checkpoints(program["id"]):
        if not _between(row.get("at"), start, end):
            continue
        if row.get("kind") == "step_too_big" and row.get("choice") == "split":
            splits += 1
        elif row.get("kind") == "step_change" and ((row.get("undo") or {}).get("fields") or {}).get("split"):
            splits += 1
    stopped = any(row.get("kind") == STOP_KIND and (row.get("undo") or {}).get("night") == night_key(start)
                  for row in service.store.list_checkpoints(program["id"]))
    red_rows = sorted((row for row in service.store.list_checkpoints(program["id"])
                       if row.get("kind") == RED_MAIN_KIND and (row.get("undo") or {}).get("night") == night_key(start)),
                      key=lambda row: str(row.get("at") or ""))
    waited = ""
    if red_rows:
        began = _parse(red_rows[0].get("at"))
        green = next((row for row in red_rows if row.get("choice") == "green"), None)
        until = _parse(green.get("at")) if green else end
        if began and until:
            from .program_service import duration_words

            waited = f"waited {duration_words(int((until - began).total_seconds()))} for a green main"
    parts = [part for part in (
        _plural(len(done), "{n} step done", "{n} steps done") if done else "",
        f"{len(parked)} parked" if parked else "",
        _plural(len(waits), "{n} waits on you", "{n} wait on you") if waits else "",
        f"{splits} split" if splits else "",
        waited,
        f"stopped after {RED_IN_A_ROW} red steps" if stopped else "",
    ) if part]
    if not parts:
        return []
    lines = ["Since last night: " + ", ".join(parts)]
    prs = [f"#{step['pr_number']}" for step in done if step.get("pr_number")]
    if prs:
        lines.append("Merged: " + " · ".join(prs))
    return lines


def last_digest(service: Any, program_id: str) -> Optional[dict[str, Any]]:
    return next((row for row in service.store.list_checkpoints(program_id) if row.get("kind") == DIGEST_KIND), None)


def note_section(service: Any, program: Mapping[str, Any]) -> list[str]:
    """The handover note's top section, while the last digest is fresh."""
    row = last_digest(service, program["id"])
    if row is None:
        return []
    at, now = _parse(row.get("at")), _parse(service._clock())
    if at is None or now is None or now - at > timedelta(hours=NOTE_HOURS):
        return []
    lines = list((row.get("undo") or {}).get("lines") or [row["line"]])
    head, rest = lines[0], lines[1:]
    return ["## Since last night", head.split(": ", 1)[1] if head.startswith("Since last night: ") else head,
            *rest, ""]


def _reach(runner: Any) -> Any:
    if getattr(runner, "_reach", None) is not None:
        return runner._reach()
    from .reach_service import default_reach_service

    return default_reach_service(runner.db)


def write_digest(runner: Any, program: Mapping[str, Any], start: datetime, end: datetime) -> Optional[dict[str, Any]]:
    """Once per night: the checkpoint, the note, the Reach line."""
    service = runner.service
    key = night_key(start)
    if any(row.get("kind") == DIGEST_KIND and (row.get("undo") or {}).get("night") == key
           for row in service.store.list_checkpoints(program["id"])):
        return None
    lines = digest_lines(service, program, start, end)
    if not lines:
        return None
    service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="engine",
                                 line=lines[0][:400], kind=DIGEST_KIND, undo={"night": key, "lines": lines})
    service.changed(program["id"], None, verb="night")
    sent: Optional[dict[str, Any]] = None
    held = [f"program:{program['id']}:{item['id']}" for item in service._turn(program, service.store.list_steps(program["id"]))
            if item.get("kind") != "answer"]
    try:
        sent = _reach(runner).night_line(f"program:{program['id']}:night:{key}", f"{program['title']}\n{lines[0]}",
                                         items=held)
    except Exception as exc:
        log.info(f"the night's digest was not sent: {exc}")
    return {"night": key, "lines": lines, "reach": sent}


def tick_nights(runner: Any) -> list[str]:
    """Every Program with a night line: plan tonight's items inside the
    window; write the digest after it. The ids that moved."""
    moved: list[str] = []
    now = runner._now()
    for program in runner.service.store.list_programs():
        night = program.get("night")
        if not isinstance(night, Mapping) or not night.get("start") or program.get("state") in ("drafting", "parked"):
            continue
        start, end = window(night, now)
        local = now.astimezone()
        if start <= local < end:
            if program.get("state") in ("running", "waiting", "failed") or program.get("closed_at"):
                try:
                    if wake_parked(runner, program) + read_backlog(runner, program, start, end):
                        moved.append(program["id"])
                except Exception as exc:
                    log.error(f"the backlog of {program['id']} was not read: {exc}", exc_info=True)
            pending = [step for step in runner.service.store.list_steps(program["id"])
                       if (step.get("facts") or {}).get("night_plan") == "pending"
                       and step["state"] in ("planned", "ready")]
            if not pending or program["id"] in _PLANNING:
                continue
            if getattr(runner, "_async", False):
                thread = threading.Thread(target=_plan_thread, args=(runner, program["id"]), daemon=True,
                                          name=f"program-night-{program['id']}")
                _PLANNING[program["id"]] = thread
                thread.start()
            elif plan_pending(runner, program["id"]):
                moved.append(program["id"])
            continue
        # After the window (the window that started last has ended): its digest.
        if end <= local < end + timedelta(hours=DIGEST_HOURS):
            if end_working(runner, program, start, end):
                continue  # the digest waits for the parked rows
            if write_digest(runner, program, start, end) is not None:
                moved.append(program["id"])
    return moved


# ── Add to tonight (JRN2) ────────────────────────────────────────────

def night_program(service: Any, program_id: Any = None) -> dict[str, Any]:
    """The Program the item goes to: the one named, else the one Program with
    a night line."""
    from .program_service import ProgramRefused

    if program_id:
        program = service._program(str(program_id))
        if not program.get("night"):
            raise ProgramRefused("no_night", f"{program['title']} has no night line. Add one: night 23:30–07:00.",
                                 status=409)
        return program
    found = [row for row in service.store.list_programs() if row.get("night")]
    if not found:
        raise ProgramRefused("no_night_program", "No program runs at night. Add a night line to one: "
                                                 "night 23:30–07:00 · at most 8 steps.", status=409)
    if len(found) > 1:
        raise ProgramRefused("night_program_ambiguous", "More than one program runs at night. Name one: "
                             + ", ".join(row["title"] for row in found[:5]) + ".", status=409)
    return found[0]


def _item(service: Any, kind: str, item_id: str, line: Any) -> dict[str, Any]:
    """``{ref, title, brief, owns, origin_ref, from}`` of the item."""
    from .program_service import ProgramRefused

    if kind not in ITEM_KINDS:
        raise ProgramRefused("night_kind_invalid", "Add to tonight takes a Door task (action), a note line (note) "
                                                   "or a program step (program_step).", status=400)
    if not item_id:
        raise ProgramRefused("night_item_required", "Name the item (item_id).", status=400)
    if kind == "program_step":
        step = service.store.get_step(item_id)
        if step is None:
            raise ProgramRefused("night_item_unknown", "There is no such step.", status=404)
        source = service.store.get_program(step["program_id"]) or {}
        return {"ref": f"program_step:{item_id}", "title": step["title"], "brief": step.get("brief_markdown") or "",
                "owns": list(step.get("owns") or []), "origin_ref": None,
                "from": f"Step {step['ordinal']} of the program {source.get('title') or ''}".strip()}
    from .agent_hand_service import item_exists, item_title

    if not item_exists(service.db, kind, item_id):
        raise ProgramRefused("night_item_unknown", "There is no such item on the desk.", status=404)
    title = item_title(service.db, kind, item_id) or item_id
    if kind == "note":
        words = " ".join(str(line or "").split())
        if not words:
            raise ProgramRefused("night_line_required", "Give the note line (line).", status=400)
        return {"ref": f"note:{item_id}:{words[:200]}", "title": words[:120], "brief": words, "owns": [],
                "origin_ref": None, "from": f"A line of the note {title}"}
    return {"ref": f"action:{item_id}", "title": title[:120], "brief": title, "owns": [],
            "origin_ref": f"action:{item_id}", "from": "A task on the Door"}


def add_to_night(service: Any, principal: Any, *, kind: Any, item_id: Any, line: Any = None,
                 program_id: Any = None) -> dict[str, Any]:
    """Mark one item for tonight's planning (a Planned step of the night Program)."""
    from ..kernel.program_ops import RUNNER
    from .program_rules import decide
    from .program_service import _LOCK, CLOSED_STATES, ProgramRefused, _is_owner

    item = _item(service, str(kind or "").strip(), str(item_id or "").strip(), line)
    program = night_program(service, program_id)
    for step in service.store.list_steps(program["id"]):
        if ((step.get("facts") or {}).get("night_item") or {}).get("ref") == item["ref"] \
                and step.get("state") not in CLOSED_STATES:
            return {"added": False, "program_id": program["id"], "step_id": step["id"], "ordinal": step["ordinal"],
                    "say": f"It is in tonight already: step {step['ordinal']}", "program": service.get(principal, program["id"])}
    outcome = None
    if not _is_owner(principal):
        # An agent's add is a step the plan lacked: YOLO adds it and says so.
        outcome = decide(program.get("control"), "add_step", {})
        if outcome.to_owner:
            raise ProgramRefused("owner_required", "Only you add to tonight at Normal and Secure; at YOLO the "
                                                   "engine adds it and says so.", status=403)
    with _LOCK:
        before = {row["id"] for row in service.store.list_steps(program["id"])}
        service.plan(RUNNER, program["id"], steps=[{"title": item["title"], "brief": item["brief"], "owns": item["owns"],
                                                    "origin_ref": item["origin_ref"]}],
                     by="owner" if outcome is None else "engine")
        step = next(row for row in service.store.list_steps(program["id"]) if row["id"] not in before)
        facts = dict(step.get("facts") or {})
        facts.update(night_plan="pending", night_item={"ref": item["ref"], "kind": str(kind), "from": item["from"],
                                                       "at": service._clock()})
        step["facts"] = facts
        service.save_step(step)
        fresh = service._program(program["id"])
        if fresh.get("closed_at"):
            # A Done night Program opens again for tonight (one record, one Note).
            fresh["closed_at"] = None
            service.store.save_program(fresh)
            service._checkpoint(fresh, None, "engine", "Opened again for tonight")
        line_words = f"Added to tonight: step {step['ordinal']} · {item['title']}"
        if outcome is not None:
            service.engine_decision(fresh, step, "add_step", outcome, line_words[:400], undo={"step_id": step["id"]})
        else:
            service._checkpoint(fresh, step, "owner", line_words[:400])
        service._touch(fresh)
        service.changed(program["id"], step["id"], verb="night")
    return {"added": True, "program_id": program["id"], "step_id": step["id"], "ordinal": step["ordinal"],
            "say": line_words, "program": service.get(principal, program["id"])}


__all__ = ["BACKLOG_KIND", "CONTRACT", "DIGEST_KIND", "ITEM_KINDS", "RED_MAIN_KIND", "STOP_KIND", "add_to_night",
           "ask_item", "backlog_items", "base_red", "wake_parked", "digest_lines", "end_working", "inside", "messages",
           "night_program", "night_room", "note_section", "plan_pending", "read_backlog", "read_item",
           "red_main_filter", "step_hold", "tick_nights", "window", "write_digest"]
