"""Betterment AG7: the screen watcher (agents/DESIGN.md, "Seeing every agent").

Every 2 s the hub's coder watcher (``web_server._coder_frames_loop``) reads
the visible screen and the title of each live agent's tmux pane and keeps
one record per agent here, in memory:

- the rule's verdict (``screen_rules.read_screen``): the state, the rule id,
  the evidence lines, the rule file and its version;
- herdr's completion sequence: a turn that goes idle AFTER the screen showed
  it working is a finished turn (``turn_id``); a start-up idle, or an idle
  the hub met on its first read, is not;
- what a blocked screen asks (the command and the numbered choices) and the
  agent's last words.

The merge (``merged_state``) is herdr's order of authority: the hook first,
then the rule, then **No signal** once neither said anything for
:data:`NO_SIGNAL_SECONDS`. A rule that says ``skip_state_update`` (a
transcript viewer open) keeps the state it had.

Agents: each running launch (its tmux session) and each live hook session
that names its tmux pane. ``HOLDSPEAK_SCREEN_RULES=off`` reads no pane at
all (a rig hub on the owner's tmux socket).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Optional

from ..logging_config import get_logger
from .screen_rules import Verdict, read_screen, last_message, load_manifest, prompt_reading

log = get_logger("agent_context.screen_watch")

#: ``off`` reads no pane (a rig hub that shares the owner's tmux). Default on.
SCREEN_RULES_ENV = "HOLDSPEAK_SCREEN_RULES"

#: herdr's "unknown", in our words: no hook and no rule for this long.
NO_SIGNAL_SECONDS = 10 * 60

#: A hook older than this no longer outranks a rule that matched.
HOOK_FRESH_SECONDS = NO_SIGNAL_SECONDS

#: Launch states whose agent may be on a screen now.
RUNNING_LAUNCH_STATES = frozenset({"launched", "registered"})

TMUX_TIMEOUT_SECONDS = 2.0

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def enabled() -> bool:
    return os.environ.get(SCREEN_RULES_ENV, "").strip().lower() not in {"0", "off", "false", "no"}


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ScreenRecord:
    """One agent's screen, as the watcher last read it."""

    key: str
    agent: str
    target: str
    verdict: Verdict
    #: The state the record holds (a ``skip_state_update`` rule keeps it).
    state: str
    sampled_at: datetime
    #: When ``state`` began.
    since: datetime
    #: The last read a rule (not the fallback) matched; ``None``: never.
    matched_at: Optional[datetime]
    #: The first read of this agent (the No signal clock with no match).
    first_at: datetime
    #: The screen showed it working since its last finished turn.
    worked: bool = False
    #: The finished turn's id (``screen:<when it went idle>``); ``None`` while it works.
    turn_id: Optional[str] = None
    wait: Optional[str] = None
    command: Optional[str] = None
    choices: list[dict[str, str]] = field(default_factory=list)
    said: str = ""
    title: str = ""
    aliases: tuple[str, ...] = ()


class ScreenStore:
    """The watcher's records, by key (``launch:<id>`` or ``<agent>:<session>``)
    and by alias (a launch's bound session key)."""

    def __init__(self) -> None:
        self._rows: dict[str, ScreenRecord] = {}
        self._alias: dict[str, str] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._rows.clear()
            self._alias.clear()

    def get(self, key: str) -> Optional[ScreenRecord]:
        with self._lock:
            row = self._rows.get(key)
            if row is None and key in self._alias:
                row = self._rows.get(self._alias[key])
            return replace(row) if row is not None else None

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._rows)

    def forget(self, keep: Iterable[str]) -> None:
        """Drop the agents the last pass did not read (their pane is gone)."""
        keep = set(keep)
        with self._lock:
            for key in [k for k in self._rows if k not in keep]:
                row = self._rows.pop(key)
                for alias in row.aliases:
                    if self._alias.get(alias) == key:
                        self._alias.pop(alias, None)

    def observe(
        self, key: str, *, agent: str, target: str, verdict: Verdict, screen: str, title: str,
        now: datetime, aliases: tuple[str, ...] = (),
    ) -> bool:
        """Fold one read in. Returns True when what a face shows changed
        (the state, the finished turn or what a prompt asks)."""
        with self._lock:
            old = self._rows.get(key)
            state = verdict.state
            if verdict.skip_state_update and old is not None:
                state = old.state
            matched = verdict.fallback is None and not verdict.skip_state_update
            row = ScreenRecord(
                key=key, agent=agent, target=target, verdict=verdict, state=state,
                sampled_at=now,
                since=old.since if old is not None and old.state == state else now,
                matched_at=now if matched else (old.matched_at if old is not None else None),
                first_at=old.first_at if old is not None else now,
                worked=old.worked if old is not None else False,
                turn_id=old.turn_id if old is not None else None,
                title=title, aliases=aliases,
            )
            if state == "working":
                row.worked, row.turn_id = True, None
            elif state == "idle" and row.worked:
                # herdr's completion sequence: idle after real work is a
                # finished turn; a start-up idle never is.
                row.worked, row.turn_id = False, f"screen:{_iso(now)}"
            if state == "blocked":
                reading = prompt_reading(screen)
                row.wait, row.command, row.choices = reading["wait"], reading["command"], reading["choices"]
            if state == "idle":
                row.said = last_message(screen)
            elif old is not None and state != "working":
                row.said = old.said
            self._rows[key] = row
            for alias in aliases:
                self._alias[alias] = key
            if old is None:
                return True
            return (old.state, old.turn_id, old.wait, old.command, old.choices) != (
                row.state, row.turn_id, row.wait, row.command, row.choices
            )


#: The hub's one store (the watcher writes, the flights read).
STORE = ScreenStore()


def merged_state(row: Optional[ScreenRecord], now: datetime) -> Optional[str]:
    """What the screen alone says, in the desk's words: ``working``,
    ``approve`` / ``asks`` (blocked, or a finished turn whose last words ask),
    ``done`` (a finished turn), ``idle`` (Quiet), ``no_signal``; ``None``
    with no record."""
    from .models import asks_a_question

    if row is None:
        return None
    anchor = row.matched_at or row.first_at
    if row.verdict.fallback is not None and (now - anchor).total_seconds() > NO_SIGNAL_SECONDS:
        return "no_signal"
    if row.state == "working":
        return "working"
    if row.state == "blocked":
        return "approve" if row.wait == "approve" else "asks"
    if row.state == "unknown":
        return "no_signal" if (now - anchor).total_seconds() > NO_SIGNAL_SECONDS else None
    if row.turn_id:
        return "asks" if asks_a_question(row.said) else "done"
    return "idle"


def screen_wire(row: Optional[ScreenRecord], now: datetime) -> Optional[dict[str, Any]]:
    """The record as the faces read it (on a flight and a session row)."""
    if row is None:
        return None
    return {
        "state": merged_state(row, now),
        "rule": row.verdict.rule,
        "wait": row.wait if row.state == "blocked" else None,
        "command": row.command if row.state == "blocked" else None,
        "choices": list(row.choices) if row.state == "blocked" else [],
        "turn_id": row.turn_id,
        "said": row.said or None,
        "at": _iso(row.sampled_at),
    }


# ── reading tmux ──────────────────────────────────────────────────────


def _runner(argv: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, errors="replace",
        timeout=TMUX_TIMEOUT_SECONDS,
    )


def capture(target: str, runner: Optional[Runner] = None) -> Optional[tuple[str, str]]:
    """The pane's visible screen and its title (``#{pane_title}``, which tmux
    sets from the agent's OSC title); ``None`` when tmux cannot read it."""
    if runner is None and shutil.which("tmux") is None:
        return None
    run = runner or _runner
    try:
        screen = run(["tmux", "capture-pane", "-p", "-t", target])
        if screen.returncode != 0:
            return None
        title = run(["tmux", "display-message", "-p", "-t", target, "#{pane_title}"])
    except (OSError, subprocess.TimeoutExpired):
        return None
    pane_title = (title.stdout or "").rstrip("\n") if title.returncode == 0 else ""
    return (screen.stdout or "").rstrip("\n"), pane_title


@dataclass(frozen=True)
class Target:
    key: str
    agent: str
    target: str
    aliases: tuple[str, ...] = ()


def targets(records: Iterable[Mapping[str, Any]], sessions: Iterable[Any], bound: Mapping[str, str]) -> list[Target]:
    """The panes to read: each running launch's tmux session (``launch:<id>``,
    with its bound session key as an alias), then each live hook session that
    names its tmux pane and no launch holds. ``bound`` maps launch id to the
    session key its Work attempt bound."""
    from ..delivery.factory_launch import agent_of_profile
    from .models import LIFECYCLE_ENDED

    out: list[Target] = []
    held: set[str] = set()
    for record in records:
        if str(record.get("state") or "") not in RUNNING_LAUNCH_STATES:
            continue
        if (record.get("follow_through") or {}).get("done"):
            continue
        name = str(record.get("session") or "")
        launch_id = str(record.get("launch_id") or "")
        if not name or not launch_id:
            continue
        key = bound.get(launch_id, "")
        if key:
            held.add(key)
        out.append(Target(f"launch:{launch_id}", agent_of_profile(record.get("profile_id")), name, (key,) if key else ()))
    for session in sessions:
        agent = str(getattr(session, "agent", "") or "")
        sid = str(getattr(session, "session_id", "") or "")
        pane = str(getattr(session, "tmux_pane", "") or "")
        key = f"{agent}:{sid}"
        if not (agent and sid and pane) or key in held:
            continue
        if str(getattr(session, "lifecycle", "") or "") == LIFECYCLE_ENDED:
            continue
        out.append(Target(key, agent, pane))
    return out


def tick(
    store: Optional[ScreenStore] = None,
    *,
    records: Optional[Iterable[Mapping[str, Any]]] = None,
    sessions: Optional[Iterable[Any]] = None,
    db: Any = None,
    runner: Optional[Runner] = None,
    now: Optional[datetime] = None,
) -> list[str]:
    """One pass: read every agent's pane and fold the verdicts in. Returns
    the frame keys whose face changed (``launch:<id>`` or a session key)."""
    if not enabled():
        return []
    store = store or STORE
    clock = now or datetime.now(timezone.utc)
    if records is None:
        from ..delivery.factory_launch import LaunchLedger

        records = LaunchLedger().list()
    records = list(records)
    if sessions is None:
        from . import list_agent_sessions

        sessions = list_agent_sessions()
    bound: dict[str, str] = {}
    if db is None and any(str(r.get("attempt_id") or "") for r in records):
        try:
            from ..db import get_database

            db = get_database()
        except Exception:
            db = None
    if db is not None:
        for record in records:
            attempt_id = str(record.get("attempt_id") or "")
            if not attempt_id:
                continue
            try:
                attempt = db.work_attempts.get(attempt_id)
            except Exception:
                attempt = None
            key = str(getattr(attempt, "session_id", "") or "")
            if key:
                bound[str(record.get("launch_id") or "")] = key
    changed: list[str] = []
    read: list[str] = []
    for target in targets(records, sessions, bound):
        if load_manifest(target.agent) is None:
            continue
        seen = capture(target.target, runner)
        if seen is None:
            continue
        screen, title = seen
        verdict = read_screen(target.agent, screen, title=title)
        if verdict is None:
            continue
        read.append(target.key)
        if store.observe(target.key, agent=target.agent, target=target.target, verdict=verdict,
                         screen=screen, title=title, now=clock, aliases=target.aliases):
            changed.append(target.key)
    store.forget(read)
    return changed


# ── explain (coder.explain, "Why this state") ─────────────────────────


def _age(stamp: Any, now: datetime) -> Optional[int]:
    try:
        moment = datetime.fromisoformat(str(stamp or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return max(0, int((now - moment).total_seconds()))


def hook_is_fresh(session: Any, now: datetime) -> bool:
    """The hook still outranks the screen: it spoke within
    :data:`HOOK_FRESH_SECONDS`, or the session waits on the owner (a wait
    does not go stale)."""
    from .models import is_blocked

    if session is None:
        return False
    if is_blocked(session):
        return True
    age = _age(getattr(session, "updated_at", None) if not isinstance(session, Mapping) else session.get("updated_at"), now)
    return age is not None and age <= HOOK_FRESH_SECONDS


def explain(
    key: str, *, session: Any = None, state: Optional[str] = None, source: Optional[str] = None,
    store: Optional[ScreenStore] = None, now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Why an agent has its state: which source decided (``hook``,
    ``screen`` or ``none``), the hook's last event and its age, the rule, the
    evidence lines, the rule file and its version, and the age of the read."""
    clock = now or datetime.now(timezone.utc)
    row = (store or STORE).get(key)
    get = (lambda name: session.get(name)) if isinstance(session, Mapping) else (lambda name: getattr(session, name, None))
    hook = None
    if session is not None:
        hook = {
            "event": get("hook_event_name"),
            "lifecycle": get("lifecycle"),
            "notification": get("notification_type"),
            "at": get("updated_at"),
            "age_seconds": _age(get("updated_at"), clock),
        }
    screen = None
    if row is not None:
        v = row.verdict
        screen = {
            "state": merged_state(row, clock),
            "rule": v.rule,
            "fallback": v.fallback,
            "priority": v.priority,
            "region": v.region,
            "evidence": list(v.evidence),
            "rules_file": v.manifest,
            "rules_version": v.version,
            "rules_source": v.source,
            "title": row.title,
            "at": _iso(row.sampled_at),
            "age_seconds": max(0, int((clock - row.sampled_at).total_seconds())),
            "since": _iso(row.since),
            "matched_at": _iso(row.matched_at) if row.matched_at else None,
        }
    if source is None:
        source = "hook" if hook_is_fresh(session, clock) else ("screen" if screen and screen["state"] else "none")
    return {"key": key, "state": state, "source": source, "hook": hook, "screen": screen}


__all__ = [
    "HOOK_FRESH_SECONDS", "NO_SIGNAL_SECONDS", "SCREEN_RULES_ENV", "STORE", "ScreenRecord", "ScreenStore",
    "Target", "capture", "enabled", "explain", "hook_is_fresh", "merged_state", "screen_wire", "targets", "tick",
]
