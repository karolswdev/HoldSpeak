"""AG15: read agents the owner started in his own tmux panes.

This module is deliberately a read-only edge.  It discovers a pane, proves
that a native Claude Code or Codex process is in that pane's process group,
then gives the existing AG7 rule engine the redacted screen.  HoldSpeak
launches are excluded by their recorded pane/session identity, so this reader
cannot manufacture a launch or a WorkAttempt for a process it did not start.
"""
from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

from ..memory.defense import redact
from .screen_rules import Verdict, last_message, load_manifest, read_screen
from .screen_watch import (
    ANSWER_KEYS,
    ScreenAnswerRefused,
    ScreenRecord,
    ScreenStore,
    capture,
    prompt_reading,
    screen_wire,
)
from .models import asks_a_question

OWN_AGENTS_ENV = "HOLDSPEAK_OWN_AGENTS"
OWN_STORE = ScreenStore()
RUNNING_LAUNCH_STATES = frozenset({"starting", "launched", "registered"})
AGENT_COMMANDS = frozenset({"claude", "codex"})
WRAPPER_COMMANDS = frozenset({"bun", "deno", "node", "python", "python3", "python3.13", "python3.14"})
TMUX_TIMEOUT_SECONDS = 2.0

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def enabled() -> bool:
    """Own-agent discovery is on in the product and off only by an explicit switch."""
    return os.environ.get(OWN_AGENTS_ENV, "").strip().lower() not in {"0", "off", "false", "no"}


def _runner(argv: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TMUX_TIMEOUT_SECONDS,
    )


@dataclass(frozen=True)
class Pane:
    pane_id: str
    pane_pid: int
    session: str
    window: str
    title: str
    path: str


@dataclass(frozen=True)
class Process:
    pid: int
    ppid: int
    pgid: int
    sid: int
    command: str
    agent: Optional[str]


@dataclass(frozen=True)
class OwnAgent:
    pane: Pane
    process: Process
    screen: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        # Keep process evidence useful without returning argv, which can carry
        # a credential or a prompt supplied to a manually started process.
        path = Path(self.pane.path).name if self.pane.path else ""
        return {
            "id": f"own:{self.pane.pane_id}",
            "pane_id": self.pane.pane_id,
            "session": redact(self.pane.session),
            "window": redact(self.pane.window),
            "title": redact(self.pane.title),
            "project": redact(path),
            "agent": self.process.agent,
            "process": {
                "pid": self.process.pid,
                "group": self.process.pgid,
            },
            "screen": self.screen,
        }


def _command_agent(command: str) -> Optional[str]:
    """Recognise a CLI executable, never a free-form argument substring."""
    try:
        argv = shlex.split(command)
    except ValueError:
        return None
    if not argv:
        return None

    def name_of(token: str) -> str:
        return Path(token).name.casefold().removesuffix(".py")

    direct = name_of(argv[0])
    if direct in AGENT_COMMANDS:
        return direct
    if direct not in WRAPPER_COMMANDS:
        return None
    # A fixture or local shim may be launched through an interpreter.  Skip
    # interpreter flags, then accept only the script executable itself.  This
    # rejects `echo claude` and `python unrelated.py claude`.
    for token in argv[1:]:
        if token.startswith("-"):
            continue
        wrapped = name_of(token)
        return wrapped if wrapped in AGENT_COMMANDS else None
    return None


def _run(run: Runner, argv: list[str]) -> Optional["subprocess.CompletedProcess[str]"]:
    try:
        return run(argv)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _panes(run: Runner) -> list[Pane]:
    result = _run(
        run,
        [
            "tmux",
            "list-panes",
            "-a",
            "-F",
            "#{pane_id}\t#{pane_pid}\t#{session_name}\t#{window_index}\t#{pane_title}\t#{pane_current_path}",
        ],
    )
    if result is None or result.returncode != 0:
        return []
    out: list[Pane] = []
    for line in (result.stdout or "").splitlines():
        parts = line.split("\t", 5)
        if len(parts) != 6:
            continue
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        if not parts[0].startswith("%") or pid <= 1:
            continue
        out.append(Pane(parts[0], pid, parts[2], parts[3], parts[4], parts[5]))
    return out


def _processes(run: Runner) -> dict[int, Process]:
    # Darwin calls the session-id format keyword ``sess`` (Linux accepts
    # ``sid``); use the native spelling because this reader runs on the
    # owner's Mac and must prove the actual pane process group there.
    result = _run(run, ["ps", "-A", "-o", "pid=,ppid=,pgid=,sess=,command="])
    if result is None or result.returncode != 0:
        return {}
    out: dict[int, Process] = {}
    for line in (result.stdout or "").splitlines():
        parts = line.strip().split(None, 4)
        if len(parts) != 5:
            continue
        try:
            pid, ppid, pgid, sid = (int(parts[index]) for index in range(4))
        except ValueError:
            continue
        command = parts[4]
        agent = _command_agent(command)
        out[pid] = Process(pid, ppid, pgid, sid, command, agent)
    return out


def _pane_process_groups(run: Runner, panes: Iterable[Pane]) -> dict[str, tuple[int, int]]:
    result = _run(run, ["ps", "-A", "-o", "pid=,pgid=,sess="])
    if result is None or result.returncode != 0:
        return {}
    table: dict[int, tuple[int, int]] = {}
    for line in (result.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            table[int(parts[0])] = (int(parts[1]), int(parts[2]))
        except ValueError:
            continue
    return {pane.pane_id: table[pane.pane_pid] for pane in panes if pane.pane_pid in table}


def _owned_panes(records: Iterable[Mapping[str, Any]]) -> set[tuple[str, str]]:
    owned: set[tuple[str, str]] = set()
    for record in records:
        if str(record.get("state") or "") not in RUNNING_LAUNCH_STATES:
            continue
        target = record.get("target") or {}
        pane = str(target.get("pane_id") or "")
        session = str(record.get("session") or "")
        if pane or session:
            owned.add((pane, session))
    return owned


def _safe_screen_wire(row: ScreenRecord, now: datetime) -> dict[str, Any]:
    wire = screen_wire(row, now) or {}
    for key in ("command", "said", "rule", "since", "at"):
        if isinstance(wire.get(key), str):
            wire[key] = redact(wire[key])
    if isinstance(wire.get("choices"), list):
        wire["choices"] = [
            {"n": str(choice.get("n") or ""), "label": redact(str(choice.get("label") or ""))}
            for choice in wire["choices"] if isinstance(choice, Mapping)
        ]
    return wire


def _prompt_token(screen: str, title: str) -> str:
    """A stable generation token for the visible owner prompt.

    ScreenStore's ``since`` means "when this state began" for AG7.  An own
    pane can replace one blocked prompt with another without changing that
    state, so this edge uses a content token to refuse a stale owner gesture.
    The digest keeps prompt text and possible credentials out of the wire.
    """
    material = f"{screen}\x00{title}".encode("utf-8", "replace")
    return f"own:{hashlib.sha256(material).hexdigest()[:24]}"


def _owner_verdict(agent: str, screen: str, title: str) -> Optional[Verdict]:
    """Apply AG7, then recognise the visible question in a no-hook pane.

    Claude's ordinary prompt box is an idle rule even while its last
    assistant line asks the owner a question.  The hook path supplies that
    distinction for HoldSpeak launches; this narrow owner-pane seam supplies
    the same distinction from the visible question and its menu only.
    """
    verdict = read_screen(agent, screen, title=title)
    if verdict is None or verdict.state != "idle":
        return verdict
    said = last_message(screen)
    if not asks_a_question(said):
        return verdict
    return Verdict(
        agent=verdict.agent,
        state="blocked",
        rule="owner_question",
        priority=verdict.priority,
        region=verdict.region,
        evidence=verdict.evidence,
        manifest=verdict.manifest,
        version=verdict.version,
        source=verdict.source,
        tried=verdict.tried,
    )


def _find_processes(run: Runner, panes: Iterable[Pane], owned: set[tuple[str, str]]) -> list[tuple[Pane, Process]]:
    groups = _pane_process_groups(run, panes)
    processes = _processes(run)
    found: list[tuple[Pane, Process]] = []
    for pane in panes:
        if (pane.pane_id, pane.session) in owned or ("", pane.session) in owned:
            continue
        group = groups.get(pane.pane_id)
        if group is None:
            continue
        _pane_pgid, sid = group

        def belongs_to_pane(process: Process) -> bool:
            """Follow the process tree from a native CLI to the pane shell.

            Interactive shells put a foreground CLI in a new process group,
            while an exec-at-pane rig leaves it in the pane group.  The
            session plus ancestry proves both shapes belong to this pane and
            prevents a same-name process in another local terminal from being
            discovered.
            """
            if process.sid != sid:
                return False
            current = process.pid
            seen: set[int] = set()
            while current not in seen and current > 1:
                if current == pane.pane_pid:
                    return True
                seen.add(current)
                parent = processes.get(current)
                if parent is None:
                    return False
                current = parent.ppid
            return False

        members = [
            process for process in processes.values()
            if process.agent and belongs_to_pane(process)
        ]
        if not members:
            continue
        process = sorted(members, key=lambda item: item.pid)[-1]
        found.append((pane, process))
    return found


def list_own_agents(
    *,
    records: Optional[Iterable[Mapping[str, Any]]] = None,
    runner: Optional[Runner] = None,
    store: Optional[ScreenStore] = None,
    now: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """Read the current own-agent panes and return only redacted facts."""
    if not enabled():
        return []
    run = runner or _runner
    if records is None:
        try:
            from ..delivery.factory_launch import LaunchLedger

            records = LaunchLedger().list()
        except Exception:
            records = []
    panes = _panes(run)
    found = _find_processes(run, panes, _owned_panes(records))
    store = store or OWN_STORE
    clock = now or datetime.now(timezone.utc)
    keep: list[str] = []
    result: list[dict[str, Any]] = []
    for pane, process in found:
        # A manifest is required before a pane is identified as an agent;
        # capture below supplies the screen to the rule engine.
        if load_manifest(process.agent) is None:
            continue
        seen = capture(pane.pane_id, run)
        if seen is None:
            continue
        screen, title = seen
        verdict = _owner_verdict(process.agent, redact(screen), redact(title))
        if verdict is None:
            continue
        key = f"own:{pane.pane_id}"
        keep.append(key)
        store.observe(key, agent=process.agent, target=pane.pane_id, verdict=verdict,
                      screen=redact(screen), title=redact(title), now=clock)
        row = store.get(key)
        if row is None:
            continue
        wire = _safe_screen_wire(row, clock)
        wire["since"] = _prompt_token(redact(screen), redact(title))
        result.append(OwnAgent(pane, process, wire).to_dict())
    store.forget(keep)
    return result


def answer_own_agent(
    pane_id: str,
    *,
    since: str,
    keys: Optional[list[str]] = None,
    text: Optional[str] = None,
    records: Optional[Iterable[Mapping[str, Any]]] = None,
    runner: Optional[Runner] = None,
    store: Optional[ScreenStore] = None,
    send: Optional[Callable[..., dict[str, Any]]] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Re-read and answer one discovered pane through process.input."""
    if not enabled():
        raise ScreenAnswerRefused("own_agents_disabled", "own-agent discovery is off")
    if keys is None and not (text or "").strip():
        raise ScreenAnswerRefused("empty_answer")
    if keys is not None and (not keys or any(key not in ANSWER_KEYS for key in keys)):
        raise ScreenAnswerRefused("unknown_key", ",".join(keys or []))
    rows = list_own_agents(records=records, runner=runner, store=store, now=now)
    row = next((item for item in rows if item.get("pane_id") == pane_id), None)
    if row is None:
        raise ScreenAnswerRefused("pane_gone", "the agent's terminal is gone")
    wire = row.get("screen") or {}
    state = str(wire.get("state") or "")
    if state not in {"approve", "asks"} or str(wire.get("since") or "") != since:
        raise ScreenAnswerRefused("wait_not_current", "the question changed")
    run = runner or _runner
    seen = capture(pane_id, run)
    if seen is None:
        raise ScreenAnswerRefused("pane_gone", "the agent's terminal is gone")
    live = _owner_verdict(str(row.get("agent") or ""), redact(seen[0]), redact(seen[1]))
    if live is None or live.state != "blocked":
        raise ScreenAnswerRefused("wait_not_current", "the prompt left the screen")
    if _prompt_token(redact(seen[0]), redact(seen[1])) != since:
        raise ScreenAnswerRefused("wait_not_current", "the question changed")
    reading = prompt_reading(redact(seen[0]))
    if state == "approve" and reading.get("wait") != "approve":
        raise ScreenAnswerRefused("wait_not_current", "the approval changed")
    if send is None:
        from ..delivery.direct_gesture_input import submit_process_input_from_owner_gesture as send
    if keys is not None:
        named = [key if key in ("Enter", "Escape") else {"literal": key} for key in keys]
        result = send(pane=pane_id, keys=named, session_key=f"own:{pane_id}", agent=str(row.get("agent") or ""))
    else:
        result = send(pane=pane_id, text=str(text).strip(), session_key=f"own:{pane_id}", agent=str(row.get("agent") or ""))
    return {"status": "delivered", "pane_id": pane_id, "agent": row.get("agent"),
            "operation_id": (result or {}).get("operation_id")}


__all__ = ["OWN_AGENTS_ENV", "OWN_STORE", "OwnAgent", "ScreenAnswerRefused", "answer_own_agent", "enabled", "list_own_agents"]
