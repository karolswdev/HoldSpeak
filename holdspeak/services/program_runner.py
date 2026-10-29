"""The Programs engine's tick (design §6).

The workbench conductor calls :meth:`ProgramRunner.tick` every 30 s
(``HOLDSPEAK_PROGRAMS=off``: never); a press (start, resume, decide,
step_done) ticks its Program at once. One tick, for each running Program:

1. **Dispatch**: a planned step whose ``after`` steps are finished is
   ``ready``; a ready step is handed (``AgentHandService.hand(kind=
   "program_step")``) while a working slot is free (``agents.working_at_once``
   across the desk). A pi step that prefers idle time waits ("Ready ·
   waiting for qwen") until its engine is idle in the hub's engine lanes.
   A race step gets its contenders (Claude Code, Codex, pi) first.
2. **Follow**: the launch's state (the AG0 flight): working, waiting (his
   turn, Needs you through ``coder_items``), or a turn end. A turn end with
   a new commit (``git rev-parse HEAD`` in the worktree, a receipt) is
   ``checking``; one with no commit is told once to commit, then parked.
3. **Check**: the gate command in the worktree (through
   ``scripts/test_lock.py`` when the repository has it and the command does
   not take the lock itself), with an isolated HOME, to
   ``<worktree>/.tmp/program-check/<step>/<ts>.log``; the verifier reads the
   log. Red: the log tail goes back to the agent (round 2), then the step
   parks with his Needs you row.
4. **Review**: AG12's pair on the builder launch (the hub's coder watcher
   ticks it); PASS goes on, findings go back to the builder once, then they
   are his (Fix now / Later / Skip).
5. **PR and merge**: the engine pushes the branch and opens the PR
   (``gh pr create``, the launch's own repository); the Heartbeat's
   follow-through reads it. CI green: Secure asks him (Merge?); Normal and
   YOLO merge (``gh pr merge --squash``) and log it under Decided for you. Merged is the
   follow-through's receipt, never the engine's claim.
6. **Note** and frames when anything changed (``ProgramService.changed``).

Every process this module starts goes through :func:`_default_runner`, the
one subprocess site (``tests/unit/test_kernel_effect_fence.py``).
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .program_service import (
    ACTIVE_STATES, PARKED_BY_ENGINE, PARKED_BY_RACE, RACE_PROFILES,
    ProgramRefused, ProgramService, agent_label, duration_words, programs_on,
)
from .program_rules import HANDOFF_AFTER_MINUTES, decide, is_core, level_of
from .program_verifier import log_tail, verify_log

log = get_logger("program_runner")

#: The longest a check may run before it is killed (its log says so).
CHECK_TIMEOUT_SECONDS = 3600
#: git / gh calls.
CALL_TIMEOUT_SECONDS = 120
#: The tick's cadence (the conductor's loop).
TICK_SECONDS = 30

#: Flight states whose agent stopped: the step parks with his row.
_STOPPED = frozenset({"ended", "expired", "stopped_by_restart", "resume_failed", "checked"})
#: Flight states of a turn that ended.
_TURN_END = frozenset({"done", "pr_open", "merged"})
#: Programs the tick walks.
_TICKED = frozenset({"running", "waiting", "failed"})

_CHECK_LOCK = threading.Lock()
_PROGRAM_LOCKS: dict[str, threading.Lock] = {}
_PROGRAM_LOCKS_GUARD = threading.Lock()
_RUNNING_CHECKS: dict[str, threading.Thread] = {}

#: PG19: when a limit notice names no reset time, its agent counts as
#: limited this long after the handoff (a plan's usage window).
UNKNOWN_RESET_HOURS = 5
#: PG19: a handoff's reason in the checkpoint's words.
REASON_WORDS = {"usage_limit": "usage limit", "usage_warning": "usage warning", "by_hand": "by hand"}


def utc_iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _default_runner(argv: list[str], cwd: Optional[str] = None, env: Optional[Mapping[str, str]] = None,
                    timeout: int = CALL_TIMEOUT_SECONDS, stdout: Any = None) -> Any:
    """The engine's one process site: git and gh in a step's worktree, and
    the gate command writing its log."""
    return subprocess.run(
        argv, cwd=cwd, env=dict(env) if env is not None else None, stdin=subprocess.DEVNULL,
        stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.STDOUT if stdout is not None else subprocess.PIPE,
        text=True, errors="replace", timeout=timeout,
    )


def _program_lock(program_id: str) -> threading.Lock:
    with _PROGRAM_LOCKS_GUARD:
        return _PROGRAM_LOCKS.setdefault(program_id, threading.Lock())


def _reviewer_key(profile: Optional[str]) -> str:
    return {"codex-default": "codex", "claude-default": "claude", "pi-default": "pi"}.get(str(profile or ""), "")


class ProgramRunner:
    """One tick over the Programs. Every collaborator is a seam; production
    builds them in :func:`default_runner`."""

    def __init__(
        self,
        service: ProgramService,
        *,
        hand: Optional[Callable[[], Any]] = None,
        ledger: Optional[Callable[[], Any]] = None,
        launch_state: Optional[Callable[[str], Mapping[str, Any]]] = None,
        run: Callable[..., Any] = _default_runner,
        prompt: Optional[Callable[[str, str], Any]] = None,
        review_tick: Optional[Callable[[], Any]] = None,
        idle: Optional[Callable[[Optional[str]], tuple[bool, str]]] = None,
        async_checks: bool = True,
        principal: Any = None,
    ) -> None:
        self.service = service
        self.db = service.db
        self._hand = hand
        self._ledger = ledger
        self._launch_state = launch_state
        self._run = run
        self._prompt = prompt
        self._review_tick = review_tick
        self._idle = idle
        self._async = async_checks
        if principal is None:
            from ..kernel.program_ops import RUNNER

            principal = RUNNER
        self.principal = principal

    # ── seams ────────────────────────────────────────────────────────

    def hand(self) -> Any:
        if self._hand is not None:
            return self._hand()
        from ..runtime import composition
        from .agent_hand_service import default_agent_hand_service

        return composition.service("agent_hand_service", lambda: default_agent_hand_service(self.db))

    def ledger(self) -> Any:
        if self._ledger is not None:
            return self._ledger()
        return self.hand()._launch_service()._ledger

    def flight(self, launch_id: str) -> dict[str, Any]:
        if self._launch_state is not None:
            return dict(self._launch_state(launch_id) or {})
        from .agent_flights import flight_of_launch

        try:
            return dict(flight_of_launch(self.db, launch_id, ledger=self.ledger()) or {})
        except Exception as exc:
            log.debug(f"flight not read: {exc}")
            return {}

    def engine_idle(self, engine_id: Optional[str]) -> tuple[bool, str]:
        """Whether the engine a pi step runs on is idle now, and its short
        name: no foreground turn holds it and no background job runs on it
        (``engine_lanes``), and no other Program step works on it."""
        if self._idle is not None:
            return self._idle(engine_id)
        from ..engine_lanes import LANES

        found = self.service.engine(engine_id) if engine_id else None
        if found is None:
            try:
                from ..delivery.pi_launch import coding_engine

                engine = coding_engine(self.db)
                key, name = f"{engine.endpoint.strip().rstrip('/')}|{engine.model}", (re.match(r"[A-Za-z]+", engine.model) or [engine.model])[0]
            except Exception:
                return True, ""
        else:
            key, name = found.lane_key, found.short_name
        if key and (LANES.holds(key) or LANES.busy_with(key)):
            return False, str(name).lower()
        return True, str(name).lower()

    def _git(self, cwd: str, *args: str) -> str:
        try:
            proc = self._run(["git", "-C", cwd, *args], cwd=cwd)
        except Exception as exc:
            log.debug(f"git {args[:1]} failed: {exc}")
            return ""
        return str(proc.stdout or "").strip() if proc.returncode == 0 else ""

    def prompt_builder(self, step: Mapping[str, Any], text: str) -> Any:
        """Type the engine's words into the step's agent, at a turn boundary
        only (never into a blocked agent: design §4)."""
        launch_id = str(step.get("launch_id") or "")
        if not launch_id:
            return None
        if self._prompt is not None:
            return self._prompt(launch_id, text)
        from .agent_review import AgentReviewLoop

        loop = AgentReviewLoop(self.db, self.hand(), ledger=self.ledger())
        return loop._prompt_builder(launch_id, text)

    # ── the tick ─────────────────────────────────────────────────────

    def tick(self) -> list[str]:
        """One pass over every running Program; the ids that changed."""
        if not programs_on():
            return []
        if self._review_tick is not None:
            try:
                self._review_tick()
            except Exception as exc:
                log.warning(f"review tick failed: {exc}")
        moved = []
        for program in self.service.store.list_programs():
            if program["state"] not in _TICKED:
                continue
            try:
                if self.tick_program(program["id"]):
                    moved.append(program["id"])
            except Exception as exc:
                log.error(f"program {program['id']} tick failed: {exc}", exc_info=True)
        return moved

    def tick_program(self, program_id: str) -> bool:
        lock = _program_lock(program_id)
        if not lock.acquire(blocking=False):
            return False
        try:
            return self._tick_program(program_id)
        finally:
            lock.release()

    def _tick_program(self, program_id: str) -> bool:
        program = self.service.store.get_program(program_id)
        if program is None or program["state"] not in _TICKED:
            return False
        before = self._fingerprint(program_id)
        steps = self.service.store.list_steps(program_id)
        for step in steps:
            try:
                # A step may take several moves in one tick (a turn end, the
                # check, the PR); each move is its own checkpoint.
                for _ in range(6):
                    before_state = step["state"]
                    self._advance(program, step, steps)
                    fresh = self.service.store.get_step(step["id"]) or step
                    step.clear()
                    step.update(fresh)
                    if step["state"] == before_state:
                        break
            except ProgramRefused as exc:
                log.info(f"step {step['id']}: {exc.code}")
            except Exception as exc:
                log.error(f"step {step['id']} failed to advance: {exc}", exc_info=True)
        self._promote(program)
        self._dispatch(program)
        changed = self._fingerprint(program_id) != before
        if changed:
            self.service.changed(program_id, verb="step")
        return changed

    def _fingerprint(self, program_id: str) -> tuple:
        return tuple(
            (step["id"], step["state"], step.get("held_reason"), step.get("pr_number"), step.get("check_verdict"),
             step.get("review_verdict"), len(step.get("findings") or []), step.get("rounds"))
            for step in self.service.store.list_steps(program_id)
        )

    # ── 1. dispatch ──────────────────────────────────────────────────

    def _promote(self, program: Mapping[str, Any]) -> None:
        steps = self.service.store.list_steps(program["id"])
        for step in steps:
            if step["state"] != "planned" or step.get("race_of"):
                continue
            if all(self.service._ordinal_finished(steps, ordinal) for ordinal in step.get("after") or []):
                self.service.transition(program, step, "ready")

    def _free_slots(self) -> int:
        try:
            hand = self.hand()
            return int(hand.working_at_once) - int(hand.working_count())
        except Exception as exc:
            log.debug(f"slots not read: {exc}")
            return 0

    def _dispatch(self, program: dict[str, Any]) -> None:
        steps = self.service.store.list_steps(program["id"])
        ready = [step for step in steps if step["state"] == "ready"]
        if not ready:
            return
        for step in ready:
            if int(step.get("race") or 0) >= 2 and not step.get("race_of"):
                self._make_contenders(program, step, steps)
        steps = self.service.store.list_steps(program["id"])
        ready = [step for step in steps if step["state"] == "ready"]
        slots = self._free_slots()
        busy_engines = {self._engine_of(program, other) for other in steps
                        if other["state"] in ACTIVE_STATES and self._profile_of(program, other) == "pi-default"}
        for step in ready:
            entry = self.first_agent(program, step)
            if entry is None:
                self._hold(step, "waiting for an agent's limit to reset")
                continue
            profile, engine = entry["profile"], entry.get("engine")
            if profile == "pi-default" and (step.get("prefer_idle") or program.get("prefer_idle")):
                idle, name = self.engine_idle(engine)
                if not idle or engine in busy_engines:
                    self._hold(step, f"waiting for {name or 'the engine'}")
                    continue
            if slots <= 0:
                self._hold(step, "waiting for a free agent")
                continue
            if self._core_hold(step):
                continue
            spend = self._spend_core(program, step, profile, engine)
            if spend:
                self.raise_core(program, step, "spend", spend)
                continue
            if self._hand_step(program, step, profile, engine):
                slots -= 1
                if profile == "pi-default":
                    busy_engines.add(engine)

    def _spend_core(self, program: Mapping[str, Any], step: Mapping[str, Any], profile: str,
                    engine: Optional[str]) -> str:
        """Money is a core question (design §6): pi on a hosted (paid) engine
        with no spend limit set. A local or LAN engine costs nothing; Claude
        Code and Codex run on his own subscriptions (no per-call spend the
        engine can see)."""
        if profile != "pi-default" or "spend" in set((step.get("facts") or {}).get("core_cleared") or []):
            return ""
        found = self.service.engine(engine) if engine else None
        boundary = str(getattr(getattr(found, "engine", None), "boundary", "") or "").lower()
        if boundary not in ("hosted", "cloud", "remote_paid"):
            return ""
        return is_core({"spend_usd": 1.0, "spend_limit_usd": program.get("spend_limit_usd")}) if program.get(
            "spend_limit_usd") is None else ""

    def _hold(self, step: dict[str, Any], reason: str) -> None:
        if step.get("held_reason") != reason:
            step["held_reason"] = reason
            self.service.save_step(step)

    @staticmethod
    def _profile_of(program: Mapping[str, Any], step: Mapping[str, Any]) -> str:
        running = (step.get("facts") or {}).get("running_on")
        if isinstance(running, Mapping) and running.get("profile"):
            return str(running["profile"])
        return str(step.get("profile") or program.get("default_profile") or "claude-default")

    @staticmethod
    def _engine_of(program: Mapping[str, Any], step: Mapping[str, Any]) -> Optional[str]:
        running = (step.get("facts") or {}).get("running_on")
        if isinstance(running, Mapping) and running.get("profile"):
            return running.get("engine") or None
        if step.get("profile"):
            return step.get("engine") or None
        return step.get("engine") or program.get("default_engine") or None

    # ── PG19: Runs on as a list, the usage limit, the handoff ───────

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def limited_agents(self) -> dict[tuple[str, Optional[str]], Optional[datetime]]:
        """The agents at their usage limit now, read off every Program: a
        limited step's own agent, and the agent a step was handed away from
        at a limit (until its reset). ``None``: no reset time known."""
        now = self._now()
        out: dict[tuple[str, Optional[str]], Optional[datetime]] = {}

        def note(profile: Any, engine: Any, until: Any) -> None:
            moment = _parse(until)
            if moment is not None and moment <= now:
                return
            out[(str(profile or ""), engine or None)] = moment

        for program in self.service.store.list_programs():
            for step in self.service.store.list_steps(program["id"]):
                limit = (step.get("facts") or {}).get("limit")
                if step.get("state") == "limited" and isinstance(limit, Mapping) and not limit.get("share"):
                    note(limit.get("profile"), limit.get("engine"), limit.get("until"))
                for entry in step.get("handoffs") or []:
                    if entry.get("reason") != "usage_limit":
                        continue
                    until = entry.get("until")
                    if not until:
                        # No reset time was shown: a plan's window is five hours.
                        at = _parse(entry.get("at"))
                        until = utc_iso(at + timedelta(hours=UNKNOWN_RESET_HOURS)) if at else None
                    note(entry.get("from_profile"), entry.get("from_engine"), until)
        return out

    def _usable(self, program: Mapping[str, Any], entry: Mapping[str, Any],
                limited: Mapping[tuple[str, Optional[str]], Any]) -> bool:
        """An entry is on (the desk has the agent), allowed for this
        repository, and not at its own limit."""
        profile = str(entry.get("profile") or "")
        try:
            known = self.service._known_profiles()
        except Exception:
            known = {profile}
        if profile not in known:
            return False
        allowed = list(program.get("allowed_profiles") or [])
        if allowed and profile not in allowed:
            return False
        return (profile, entry.get("engine") or None) not in limited and (profile, None) not in limited

    def first_agent(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """The first allowed and available entry of the step's Runs on."""
        limited = self.limited_agents()
        for entry in self.service.runs_on_of(program, step):
            if self._usable(program, entry, limited):
                return dict(entry)
        return None

    def next_agent(self, program: Mapping[str, Any], step: Mapping[str, Any],
                   current: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """The next entry after ``current`` that may take the step (then
        the ones before it), skipping off, disallowed and limited agents."""
        limited = dict(self.limited_agents())
        limited[(str(current.get("profile") or ""), current.get("engine") or None)] = None
        entries = self.service.runs_on_of(program, step)
        key = (current.get("profile"), current.get("engine") or None)
        index = next((i for i, row in enumerate(entries) if (row["profile"], row.get("engine") or None) == key), -1)
        ordered = entries[index + 1:] + entries[:max(index, 0)] if index >= 0 else entries
        for entry in ordered:
            if self._usable(program, entry, limited):
                return dict(entry)
        return None

    def current_agent(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> dict[str, Any]:
        return {"profile": self._profile_of(program, step), "engine": self._engine_of(program, step)}

    def _limit_follow(self, program: dict[str, Any], step: dict[str, Any], flight: Mapping[str, Any]) -> bool:
        """PG19: read the flight's usage-limit notice. True when the step's
        move this tick is the limit's (the rest of the follow waits)."""
        notice = flight.get("limit") if isinstance(flight.get("limit"), Mapping) else None
        facts = dict(step.get("facts") or {})
        state = str(flight.get("state") or "")
        if notice and notice.get("share") is not None:
            wanted = program.get("usage_warning_share")
            turn = str(flight.get("turn_id") or "")
            if not wanted or float(notice["share"]) < float(wanted) or state not in _TURN_END or not turn:
                notice = None   # a share below his warning, or mid-turn: work on
            elif f"{step.get('launch_id')}:{turn}" in (facts.get("handed_turns") or []):
                notice = None
        if not notice:
            if step["state"] == "limited":
                facts.pop("limit", None)
                step["facts"] = facts
                if state not in ("working", "resuming") and step.get("launch_id"):
                    facts["last_turn"] = str(flight.get("turn_id") or "") or facts.get("last_turn")
                    try:
                        self.prompt_builder(step, "HoldSpeak: your usage window reset. Continue the step where you stopped.")
                    except Exception as exc:
                        log.info(f"reset prompt not typed: {exc}")
                self.service.transition(program, step, "working", facts=facts, line="The limit reset; the agent works again")
                return True
            return False
        current = self.current_agent(program, step)
        turn_key = f"{step.get('launch_id')}:{flight.get('turn_id') or notice.get('line') or ''}"
        old = dict(facts.get("limit") or {})
        nxt = self.next_agent(program, step, current)
        limit = {
            "until": notice.get("until"), "words": notice.get("words") or "", "rule": notice.get("rule"),
            "line": notice.get("line") or "", "share": notice.get("share"),
            "profile": current["profile"], "engine": current.get("engine"), "turn": turn_key,
            "seen_at": old.get("seen_at") if old.get("turn") == turn_key else utc_iso(self._now()),
            "waiting": bool(old.get("waiting")) if old.get("turn") == turn_key else False,
            "next": self.service.entry_wire(nxt) if nxt else None,
        }
        handed = turn_key in (facts.get("handed_turns") or [])
        if limit["next"] and not limit["waiting"] and program.get("may_handoff") and level_of(program.get("control")) == "normal":
            seen = _parse(limit["seen_at"]) or self._now()
            limit["auto_at"] = utc_iso(seen + timedelta(minutes=HANDOFF_AFTER_MINUTES))
        facts["limit"] = limit
        who = agent_label(current["profile"])
        if step["state"] != "limited":
            words = f" until {limit['words']}" if limit["words"] else ""
            line = (f"{who} reported {round(float(limit['share']) * 100)}% of its usage window" if limit["share"] is not None
                    else f"{who} stopped at its usage limit{words}")
            self.service.transition(program, step, "limited", facts=facts, line=line)
        elif old != limit:
            step["facts"] = facts
            self.service.save_step(step)
        seen = _parse(limit["seen_at"]) or self._now()
        outcome = decide(program.get("control"), "limited", {
            "next": bool(nxt), "handed": handed, "waiting": limit["waiting"],
            "may_handoff": bool(program.get("may_handoff")),
            "minutes": (self._now() - seen).total_seconds() / 60.0,
        })
        if not outcome.to_owner and outcome.choice == "handoff" and nxt is not None:
            fresh = self.service.store.get_step(step["id"]) or step
            reason = "usage_warning" if limit["share"] is not None else "usage_limit"
            self.handoff(program, fresh, nxt, reason=reason, by="engine", outcome=outcome)
        return True

    def _git_out(self, cwd: str, *args: str) -> str:
        """git's stdout as it is (``status --porcelain`` keeps its columns)."""
        try:
            proc = self._run(["git", "-C", cwd, *args], cwd=cwd)
        except Exception as exc:
            log.debug(f"git {args[:1]} failed: {exc}")
            return ""
        return str(proc.stdout or "").rstrip("\n") if proc.returncode == 0 else ""

    def handoff_brief(self, program: Mapping[str, Any], step: Mapping[str, Any], to: Mapping[str, Any], *,
                      reason: str, by: str) -> Any:
        """The brief the next agent receives (deterministic, redacted)."""
        from .program_handoff import brief_of, gather

        current = self.current_agent(program, step)
        inputs = gather(self.service, program, step, to_label=self.service.entry_wire(to)["label"],
                        from_label=self.service.entry_wire(current)["label"], reason=reason, by=by, git=self._git_out)
        return brief_of(inputs)

    def handoff(self, program: dict[str, Any], step: dict[str, Any], to: Mapping[str, Any], *, reason: str,
                by: str = "engine", outcome: Any = None) -> dict[str, Any]:
        """Continue the step in ``to``: the earlier launch is handed off, the
        hand starts the next agent in the same worktree on the same branch
        with the brief as its first message, and the step records it."""
        from .agent_hand_service import AgentHandRefused
        from .program_handoff import redacted_words

        brief = self.handoff_brief(program, step, to, reason=reason, by=by)
        current = self.current_agent(program, step)
        old_launch = str(step.get("launch_id") or "")
        ledger = self.ledger()
        before = (ledger.get(old_launch) or {}) if old_launch else {}
        now = utc_iso(self._now())
        if old_launch:
            ledger.update(old_launch, state="handed_off", stopped={"by": by, "at": now, "reason": reason})
        try:
            answer = self.hand().hand(
                self.principal, "program_step", step["id"], profile=to["profile"],
                project_id=program.get("project_id"), engine=to.get("engine"), handoff_brief=brief.text,
            )
        except AgentHandRefused as exc:
            answer = {"status": "refused", "failure": {"stage": exc.reason}}
        if answer.get("status") != "launched" or not answer.get("launch_id"):
            if old_launch and before:
                ledger.update(old_launch, state=before.get("state") or "launched", stopped=before.get("stopped"))
            failure = (answer.get("failure") or {}).get("stage") or answer.get("status") or "failed"
            self.service._checkpoint(program, step, "engine", f"Could not hand off to {agent_label(to['profile'])} ({failure})")
            raise ProgramRefused("handoff_failed", f"The next agent did not start ({failure}).")
        facts = dict(step.get("facts") or {})
        limit = dict(facts.pop("limit", None) or {})
        handed = list(facts.get("handed_turns") or [])
        if limit.get("turn"):
            handed.append(limit["turn"])
        facts.update({"handed_turns": handed[-20:], "running_on": {"profile": to["profile"], "engine": to.get("engine")},
                      "last_turn": None, "nudged": False})
        entries = list(step.get("handoffs") or [])
        to_wire, from_wire = self.service.entry_wire(to), self.service.entry_wire(current)
        entries.append({
            "at": now, "from": from_wire["label"], "from_profile": current["profile"], "from_engine": current.get("engine"),
            "to": to_wire["label"], "to_profile": to["profile"], "to_engine": to.get("engine"), "reason": reason, "by": by,
            "brief_ref": f"program_step:{step['id']}/handoff/{len(entries) + 1}", "brief": brief.text,
            "redacted": dict(brief.redacted), "redacted_words": redacted_words(brief.redacted),
            "earlier_turns": brief.earlier_turns, "launch_from": old_launch or None, "launch_to": answer["launch_id"],
            "until": limit.get("until"),
        })
        worktree = answer.get("worktree") or {}
        step["handoffs"] = entries
        line = f"Handed to {to_wire['label']} · {REASON_WORDS.get(reason, reason)}"
        self.service.transition(program, step, "briefed", launch_id=answer["launch_id"], facts=facts,
                                branch=worktree.get("branch") or step.get("branch"))
        if by == "engine" and outcome is not None:
            self.service.engine_decision(program, step, "handoff", outcome, line)
        else:
            self.service.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=self.service._clock(),
                                              by=by, line=line, kind="handoff", choice=str(len(entries)))
        return entries[-1]

    def _make_contenders(self, program: dict[str, Any], step: dict[str, Any], steps: list[dict[str, Any]]) -> None:
        existing = [other for other in steps if other.get("race_of") == step["id"]]
        n = min(int(step.get("race") or 0), len(RACE_PROFILES))
        if existing or n < 2:
            return
        if not step.get("profile"):
            step["profile"] = RACE_PROFILES[0]
            self.service.save_step(step)
        taken = {step["profile"]}
        profiles = [profile for profile in RACE_PROFILES if profile not in taken][: n - 1]
        for index, profile in enumerate(profiles, start=2):
            contender = {**step, "id": f"{step['id']}-r{index}", "race_of": step["id"], "race": 0,
                         "profile": profile, "engine": None, "facts": {}, "findings": [], "launch_id": None,
                         "runs_on": [], "handoffs": [],
                         "worktree": None, "branch": None, "started_at": None, "ended_at": None}
            self.service.save_step(contender)
        self.service._checkpoint(program, step, "engine",
                                 "A race: " + ", ".join(agent_label(p) for p in [step["profile"], *profiles]))

    def _hand_step(self, program: dict[str, Any], step: dict[str, Any], profile: str, engine: Optional[str]) -> bool:
        from .agent_hand_service import AgentHandRefused

        try:
            answer = self.hand().hand(
                self.principal, "program_step", step["id"], profile=profile,
                project_id=program.get("project_id"), engine=engine,
            )
        except AgentHandRefused as exc:
            if exc.reason == "launch_cap_reached":
                self._hold(step, "waiting for a free agent")
                return False
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                                    parked_reason=f"The hand refused: {exc.reason}",
                                    line=f"Could not hand the step: {exc.reason}")
            return False
        if answer.get("status") != "launched" or not answer.get("launch_id"):
            failure = (answer.get("failure") or {}).get("stage") or answer.get("status") or "failed"
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                                    parked_reason=f"The agent did not start ({failure})",
                                    line=f"The agent did not start ({failure})")
            return False
        worktree = answer.get("worktree") or {}
        path = self._worktree_path(program, str(worktree.get("name") or ""))
        base = self._git(path, "rev-parse", "HEAD") if path else ""
        facts = dict(step.get("facts") or {})
        facts.update({"base_commit": base or None, "last_turn": None, "nudged": False,
                      "running_on": {"profile": profile, "engine": engine}})
        who = agent_label(profile)
        found = self.service.engine(engine) if engine else None
        if profile == "pi-default":
            who += f" on {found.label}" if found is not None else " on the desk's engine"
        self.service.transition(
            program, step, "briefed", launch_id=answer["launch_id"], worktree=path,
            branch=worktree.get("branch"), head_commit=base or None, facts=facts,
            line=f"Handed to {who} in {worktree.get('name')}",
        )
        return True

    def _worktree_path(self, program: Mapping[str, Any], name: str) -> str:
        if not name:
            return ""
        from ..delivery.factory_launch import LaunchRefused, derive_worktree_path

        try:
            return str(derive_worktree_path(str(program.get("repo_root") or ""), name))
        except LaunchRefused:
            return ""

    # ── 2-5. follow one step ─────────────────────────────────────────

    def _advance(self, program: dict[str, Any], step: dict[str, Any], steps: list[dict[str, Any]]) -> None:
        state = step["state"]
        if self._core_hold(step) and state != "checking":
            return
        if (step.get("facts") or {}).get("awaiting_pick"):
            return
        if state in ("briefed", "working", "waiting", "limited", "check_failed"):
            self._follow(program, step)
        elif state == "checking":
            self._check(program, step)
        elif state in ("review", "findings"):
            self._review(program, step)
        elif state in ("pr_open", "merge_ask"):
            self._pr(program, step)
        elif state == "merged":
            self.service.transition(program, step, "done")

    def _follow(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        flight = self.flight(str(step.get("launch_id") or ""))
        state = str(flight.get("state") or "")
        if state not in ("starting", "") and state not in _STOPPED and self._limit_follow(program, step, flight):
            return
        facts = dict(step.get("facts") or {})
        if state in ("starting", ""):
            return
        if state in _STOPPED:
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                                    parked_reason="The agent stopped before the step was done",
                                    line=f"The agent stopped ({state})")
            return
        if state in ("working", "resuming", "no_signal"):
            if step["state"] != "working":
                self.service.transition(program, step, "working")
            return
        if state == "waiting":
            if step["state"] != "waiting":
                self.service.transition(program, step, "waiting", line="The agent asks a question")
            return
        if state not in _TURN_END:
            return
        turn = str(flight.get("turn_id") or "")
        if turn and turn == facts.get("last_turn"):
            return  # the turn the engine already read (it prompted after it)
        head = self._git(str(step.get("worktree") or ""), "rev-parse", "HEAD")
        facts["last_turn"] = turn or None
        facts["turns"] = int(facts.get("turns") or 0) + 1
        if not turn and step["state"] == "check_failed" and head == step.get("head_commit"):
            return  # no turn id: wait for the commit of the fix
        if head and head != step.get("head_commit"):
            facts["nudged"] = False
            self.service.transition(program, step, "checking", head_commit=head, facts=facts,
                                    line=f"New commit {head[:8]}; the check runs")
            return
        if facts.get("nudged"):
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE, facts=facts,
                                    parked_reason="The agent ended its turn twice with no commit",
                                    line="The agent ended its turn twice with no commit")
            return
        facts["nudged"] = True
        step["facts"] = facts
        self.service.save_step(step)
        try:
            self.prompt_builder(step, "HoldSpeak: the step moves on a commit. Commit your work on this branch, "
                                      "then end your turn.")
            self.service._checkpoint(program, step, "engine", "The turn ended with no commit; asked the agent to commit")
        except Exception as exc:
            log.info(f"commit nudge not typed: {exc}")

    # ── 3. the check ─────────────────────────────────────────────────

    def _check(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        facts = dict(step.get("facts") or {})
        core = facts.get("core")
        if isinstance(core, Mapping):
            if not core.get("cleared"):
                return  # his turn: the core question
            facts.pop("core", None)
            step["facts"] = facts
            self.service.save_step(step)
            if step.get("check_verdict") == "green" and step.get("checked_commit") == step.get("head_commit"):
                self._after_check(program, step)
                return
        check = dict(facts.get("check") or {})
        if not step.get("gate_check") or not program.get("check_command"):
            step["check_verdict"] = "none"
            step["checked_commit"] = step.get("head_commit")
            self.service.save_step(step)
            self._after_check(program, step)
            return
        if check.get("commit") == step.get("head_commit") and check.get("finished"):
            self._verdict(program, step, check)
            return
        if step["id"] in _RUNNING_CHECKS and _RUNNING_CHECKS[step["id"]].is_alive():
            return
        check = {"commit": step.get("head_commit"), "running": True, "finished": False,
                 "command": program["check_command"], "started": time.time()}
        facts["check"] = check
        step["facts"] = facts
        self.service.save_step(step)
        self.service._checkpoint(program, step, "engine", f"Running the check: {program['check_command']}")
        if self._async:
            thread = threading.Thread(target=self._run_check_thread, args=(program["id"], step["id"]),
                                      daemon=True, name=f"program-check-{step['id']}")
            _RUNNING_CHECKS[step["id"]] = thread
            thread.start()
        else:
            self._run_check_thread(program["id"], step["id"])
            fresh = self.service.store.get_step(step["id"]) or step
            self._verdict(program, fresh, dict((fresh.get("facts") or {}).get("check") or {}))

    def _run_check_thread(self, program_id: str, step_id: str) -> None:
        with _CHECK_LOCK:
            program = self.service.store.get_program(program_id)
            step = self.service.store.get_step(step_id)
            if program is None or step is None:
                return
            path, rc = self.run_check(program, step)
            step = self.service.store.get_step(step_id) or step
            facts = dict(step.get("facts") or {})
            check = dict(facts.get("check") or {})
            check.update({"running": False, "finished": True, "log": path, "exit": rc,
                          "minutes": round((time.time() - float(check.get("started") or time.time())) / 60, 1)})
            facts["check"] = check
            step["facts"] = facts
            step["check_log"] = path
            self.service.save_step(step)
        _RUNNING_CHECKS.pop(step_id, None)
        if self._async:
            self.tick_program(program_id)

    def check_argv(self, worktree: str, command: str) -> list[str]:
        """The gate command, through the test lock when the repository has
        it (a quick check takes the lock per stage itself: never twice)."""
        argv = ["sh", "-c", command]
        if (Path(worktree) / "scripts" / "test_lock.py").exists() and "quick_check" not in command:
            argv = ["uv", "run", "python", "scripts/test_lock.py", "--", *argv]
        return argv

    def run_check(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> tuple[Optional[str], Optional[int]]:
        """Run the gate in the step's worktree to its log; ``(log path, rc)``."""
        worktree = str(step.get("worktree") or "")
        if not worktree or not Path(worktree).is_dir():
            return None, None
        from ..timestamps import utc_now

        stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
        folder = Path(worktree) / ".tmp" / "program-check" / str(step["id"])
        folder.mkdir(parents=True, exist_ok=True)
        log_path = folder / f"{stamp}.log"
        commit = self._git(worktree, "rev-parse", "HEAD")
        dirty = self._git(worktree, "status", "--porcelain", "--untracked-files=no")
        command = str(program.get("check_command") or "")
        scratch = tempfile.mkdtemp(prefix="hs-program-check-")
        real_home = os.environ.get("HOME_REAL") or os.path.expanduser("~")
        env = {**os.environ, "HOME": scratch, "HOME_REAL": real_home,
               "PLAYWRIGHT_BROWSERS_PATH": os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
               or str(Path(real_home) / "Library" / "Caches" / "ms-playwright"),
               "npm_config_cache": os.environ.get("npm_config_cache") or str(Path(real_home) / ".npm"),
               "HOLDSPEAK_PROGRAMS": "off"}
        rc: Optional[int] = None
        with log_path.open("w", encoding="utf-8") as out:
            out.write(f"program-check: commit {commit}\n")
            out.write("program-check: tree clean\n" if not dirty else f"program-check: tree dirty ({len(dirty.splitlines())} files)\n")
            out.write(f"program-check: command {command}\n")
            out.flush()
            try:
                proc = self._run(self.check_argv(worktree, command), cwd=worktree, env=env,
                                 timeout=CHECK_TIMEOUT_SECONDS, stdout=out)
                rc = int(proc.returncode)
            except subprocess.TimeoutExpired:
                out.write(f"\nprogram-check: the check ran past {CHECK_TIMEOUT_SECONDS} s and was stopped\n")
            except Exception as exc:
                out.write(f"\nprogram-check: the check did not run: {exc}\n")
            out.write(f"program-check: exit {rc if rc is not None else 'none'}\n")
        try:
            import shutil

            shutil.rmtree(scratch, ignore_errors=True)
        except Exception:
            pass
        return str(log_path), rc

    def _required_sections(self, program: Mapping[str, Any]) -> list[str]:
        _command, sections = self.service._check_command(str(program.get("repo_root") or ""), program.get("check_command"))
        return sections

    def _verdict(self, program: dict[str, Any], step: dict[str, Any], check: dict[str, Any]) -> None:
        result = verify_log(check.get("log"), required=self._required_sections(program))
        facts = dict(step.get("facts") or {})
        facts["check"] = {**check, "sections": result["sections"], "reasons": result["reasons"], "verified": True}
        step["facts"] = facts
        step["check_log"] = check.get("log")
        step["check_verdict"] = result["verdict"]
        step["checked_commit"] = step.get("head_commit")
        minutes = check.get("minutes")
        took = f" · {duration_words(int(float(minutes) * 60))}" if minutes is not None else ""
        if result["green"]:
            self.service.save_step(step)
            self.service._checkpoint(program, step, "engine", f"Checked · green{took} · {check.get('log')}")
            self._after_check(program, step)
            return
        why = "; ".join(result["reasons"][:3])
        done_rounds = int(step.get("rounds") or 0) + 1
        step["rounds"] = done_rounds
        outcome = decide(program.get("control"), "check_failed",
                         {"round": done_rounds, "replanned": bool(facts.get("replanned"))})
        if outcome.to_owner or outcome.choice == "park":
            self.fail_step(program, step, f"The check failed {done_rounds} times ({why})", outcome)
            return
        tail = log_tail(check.get("log"), 40)
        if outcome.choice == "replan":
            facts = dict(step.get("facts") or {})
            facts["replanned"] = True
            step["facts"], step["rounds"] = facts, 0
            self.service.transition(program, step, "check_failed", line="")
            self.service.engine_decision(program, step, "step_failed", outcome,
                                         f"Re-planned step {step['ordinal']} with a smaller brief after {done_rounds} red checks")
            text = (f"HoldSpeak on step {step['ordinal']}: the check stayed red ({why}). Re-plan: make the smallest "
                    f"change that meets the step's brief and leave the rest for a later step. The log is "
                    f"{check.get('log')}. Its last lines:\n{tail}\nCommit on this branch and end your turn.")
        else:
            self.service.transition(program, step, "check_failed", line="")
            self.service.engine_decision(program, step, "check_failed", outcome,
                                         f"Check red on step {step['ordinal']}, round {done_rounds} ({why}); sent the log back")
            text = (f"HoldSpeak on step {step['ordinal']}: the check is red ({why}). The log is {check.get('log')}. "
                    f"Its last lines:\n{tail}\nFix it, commit on this branch, and end your turn.")
        try:
            self.prompt_builder(step, text)
        except Exception as exc:
            log.info(f"log tail not typed: {exc}")

    def fail_step(self, program: dict[str, Any], step: dict[str, Any], reason: str, outcome: Any) -> None:
        """A step that failed after its rounds: Secure sends it to him; Normal
        and YOLO park it and carry on (Decided for you, overturnable)."""
        facts = dict(step.get("facts") or {})
        facts["park_is_his"] = bool(outcome.to_owner)
        self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE, parked_reason=reason,
                                facts=facts, line="" if not outcome.to_owner else f"Parked: {reason}")
        if not outcome.to_owner:
            self.service.engine_decision(program, step, "step_failed", outcome,
                                         f"Parked step {step['ordinal']} and carried on: {reason}")

    def diff_facts(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> dict[str, Any]:
        """The core-question facts a step's diff raises (design §6): files no
        step owns, deleted tests, a migration that drops or rewrites rows."""
        worktree = str(step.get("worktree") or "")
        base = str((step.get("facts") or {}).get("base_commit") or "")
        if not worktree or not base:
            return {}
        names = self._git(worktree, "diff", "--name-status", f"{base}..HEAD")
        files: list[tuple[str, str]] = []
        for line in names.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                files.append((parts[0][:1], parts[-1]))
        facts: dict[str, Any] = {}
        owned = [str(item) for item in step.get("owns") or []]
        if owned:
            import fnmatch

            outside = [path for _status, path in files
                       if not any(path == own or path.startswith(own.rstrip("/") + "/") or fnmatch.fnmatch(path, own)
                                  for own in owned)]
            if outside:
                facts["outside_owned"] = outside
        if any(status == "D" and re.search(r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]*\.py$|\.test\.[jt]sx?$", path)
               for status, path in files):
            facts["tests_deleted"] = True
        added = self._git(worktree, "diff", "--unified=0", f"{base}..HEAD")
        if re.search(r"^\+.*\b(DROP\s+TABLE|DROP\s+COLUMN|TRUNCATE|DELETE\s+FROM)\b", added, re.I | re.M):
            facts["destructive_migration"] = True
        return facts

    def raise_core(self, program: dict[str, Any], step: dict[str, Any], kind: str, reason: str) -> None:
        facts = dict(step.get("facts") or {})
        facts["core"] = {"kind": kind, "reason": reason, "at": self.service._clock()}
        step["facts"] = facts
        self.service.save_step(step)
        self.service._checkpoint(program, step, "engine", f"A core question for you: {reason}")

    def _core_hold(self, step: Mapping[str, Any]) -> bool:
        core = (step.get("facts") or {}).get("core")
        return isinstance(core, Mapping) and not core.get("cleared")

    def _after_check(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        cleared = set((step.get("facts") or {}).get("core_cleared") or [])
        if "diff" not in cleared:
            reason = is_core(self.diff_facts(program, step))
            if reason:
                self.raise_core(program, step, "diff", reason)
                return
        review = step.get("gate_review") or "none"
        if review == "agent" and step.get("review_verdict") != "pass":
            self._attach_review(program, step)
            return
        if review == "agent" and step.get("review_verdict") == "pass" and (step.get("facts") or {}).get("reviewed_commit") not in (None, step.get("checked_commit")):
            self._attach_review(program, step)
            return
        self.pass_gate(program, step)

    def _reviewer(self, program: Mapping[str, Any], step: Mapping[str, Any]) -> tuple[str, Optional[str]]:
        from .program_service import DEFAULT_REVIEWER

        builder = self._profile_of(program, step)
        profile = str(program.get("reviewer_profile") or DEFAULT_REVIEWER.get(builder, "codex-default"))
        engine = program.get("reviewer_engine") if profile == "pi-default" else None
        return profile, engine

    def _attach_review(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        """AG12's pair on the builder launch: the hub's coder watcher starts
        the reviewer in a scratch copy, read-only, at the checked commit."""
        from .agent_review import initial_review

        profile, engine = self._reviewer(program, step)
        pair = initial_review(_reviewer_key(profile)) or {}
        depth = step.get("review_depth") or "delta"
        pair.update({
            "builder": agent_label(self._profile_of(program, step)),
            "item": {"kind": "program_step", "id": step["id"], "title": step["title"]},
            "acceptance": [f"Review depth: {depth}.", *(step.get("owns") and [f"The step owns: {', '.join(step['owns'])}"] or []),
                           "Name each finding MUST (required) or SHOULD."],
            **({"engine": engine} if engine else {}),
        })
        try:
            self.ledger().update(str(step["launch_id"]), review=pair)
        except Exception as exc:
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                                    parked_reason="The reviewer could not be set up",
                                    line=f"The reviewer could not be set up: {exc}")
            return
        facts = dict(step.get("facts") or {})
        facts.update({"reviewer_profile": profile, "review_round": 0, "reviewed_commit": None})
        self.service.transition(program, step, "review", facts=facts, review_verdict=None,
                                line=f"{agent_label(profile)} reviews at depth {depth}")

    def _review_pair(self, step: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        if not step.get("launch_id"):
            return None
        try:
            record = self.ledger().get(str(step["launch_id"])) or {}
        except Exception:
            return None
        pair = record.get("review")
        return dict(pair) if isinstance(pair, Mapping) and pair.get("requested") else None

    def _review(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        facts = dict(step.get("facts") or {})
        if step["state"] == "findings" and facts.get("findings_open"):
            return  # his turn: the findings the rules sent to him
        pair = self._review_pair(step)
        if pair is None:
            return
        status = str(pair.get("status") or "")
        round_ = int(pair.get("round") or 0)
        facts["review_round"] = round_
        if status == "reviewing" and step["state"] != "review":
            step["facts"] = facts
            self.service.transition(program, step, "review", line=f"Review round {round_}")
            return
        if status == "awaiting_builder_commit" and round_ >= 1:
            if step["state"] != "findings":
                left = (pair.get("result") or {}).get("findings_left") or []
                findings = [{"id": f"r{round_}f{i}", "level": "REQUIRED", "text": str(item.get("text") or ""),
                             "decision": "fix", "to_owner": False} for i, item in enumerate(left, start=1)]
                facts["findings_open"] = False
                self.service.transition(program, step, "findings", findings=findings, facts=facts,
                                        line="")
                self.service.engine_decision(
                    program, step, "finding_required",
                    decide(program.get("control"), "finding_required", {"round": round_ - 1}),
                    f"Round {round_}: {len(findings)} REQUIRED finding{'s' if len(findings) != 1 else ''} back to the builder")
            return
        if status not in ("done", "needs_you"):
            return
        last = next((row for row in reversed(pair.get("rounds") or []) if isinstance(row, Mapping)), {})
        words = str(last.get("result") or "")
        should = [item for item in last.get("findings") or [] if str(item.get("level")) == "SHOULD"]
        notes = [{"level": "NOTE", "text": m.group(1).strip()}
                 for m in re.finditer(r"^\s*(?:[-*]\s*)?NOTE\s*[:\-]\s*(.+)$", words, re.M | re.I)]
        must = list((pair.get("result") or {}).get("findings_left") or pair.get("findings_left") or []) if status == "needs_you" else []
        level = program.get("control")
        if status == "needs_you" and must and not any("unclear" in str(item.get("text") or "") for item in must):
            outcome = decide(level, "finding_required", {"round": round_, "finding_text": " ".join(
                str(item.get("text") or "") for item in must)})
            if not outcome.to_owner and outcome.choice == "fix":
                # YOLO's third round: the findings go back once more; AG12
                # starts the next reviewer at the new commit.
                pair["status"] = "awaiting_builder_commit"
                self.ledger().update(str(step["launch_id"]), review=pair)
                words_back = "\n".join(f"MUST: {item.get('text')}" for item in must)
                try:
                    self.prompt_builder(step, f"Review findings for round {round_}:\n{words_back}\nFix the MUST findings, then commit.")
                except Exception as exc:
                    log.info(f"round three not typed: {exc}")
                self.service.engine_decision(program, step, "finding_required", outcome,
                                             f"Round {round_ + 1}: the REQUIRED findings go back to the builder")
                return
        findings: list[dict[str, Any]] = []
        for index, item in enumerate(must, start=1):
            text = str(item.get("text") or "")
            core = bool(is_core({"finding_text": text}))
            findings.append({"id": f"f{index}", "level": "REQUIRED", "text": text, "decision": None,
                             "to_owner": True, "core": core})
        for index, item in enumerate(should, start=1):
            findings.append({"id": f"s{index}", "level": "SHOULD", "text": str(item.get("text") or ""), "decision": None})
        for index, item in enumerate(notes, start=1):
            findings.append({"id": f"n{index}", "level": "NOTE", "text": item["text"], "decision": None})
        for finding in findings:
            if finding["level"] == "REQUIRED":
                continue
            kind = "finding_should" if finding["level"] == "SHOULD" else "finding_note"
            outcome = decide(level, kind, {"finding_text": finding["text"], "round_open": False})
            if outcome.to_owner:
                finding["to_owner"] = True
                finding["core"] = getattr(outcome, "core", False)
            else:
                self.service.apply_finding_rule(program, step, finding, outcome)
        his = [finding for finding in findings if finding.get("to_owner") and not finding.get("decision")]
        step["findings"] = findings
        step["review_verdict"] = "pass" if status == "done" else "fail"
        facts["reviewed_commit"] = str(pair.get("last_builder_commit") or "") or None
        if his:
            facts["findings_open"] = True
            step["facts"] = facts
            self.service.transition(program, step, "findings",
                                    line=f"{len(his)} finding{'s' if len(his) != 1 else ''} for you")
            return
        step["facts"] = facts
        reviewed = facts["reviewed_commit"]
        if reviewed and step.get("checked_commit") and reviewed != step.get("checked_commit"):
            self.service.transition(program, step, "checking", head_commit=reviewed,
                                    line="Review passed on a newer commit; the check runs again")
            return
        self.service.save_step(step)
        self.service._checkpoint(program, step, "engine", f"Review passed (round {round_})")
        self.pass_gate(program, step)

    def pass_gate(self, program: dict[str, Any], step: dict[str, Any], *, by: str = "engine") -> None:
        """The check is green and the review passed: win the race, then the
        PR (or Done for a step with no PR gate)."""
        if not self._win_race(program, step):
            return
        if step.get("gate_merge") == "none":
            self.service.transition(program, step, "done", line="Done (this step has no PR)")
            return
        self.open_pr(program, step)

    def _win_race(self, program: dict[str, Any], step: dict[str, Any]) -> bool:
        parent_id = step.get("race_of") or (step["id"] if int(step.get("race") or 0) >= 2 else None)
        if not parent_id:
            return True
        group = [other for other in self.service.store.list_steps(program["id"])
                 if other["id"] == parent_id or other.get("race_of") == parent_id]
        if any((other.get("facts") or {}).get("won") for other in group if other["id"] != step["id"]):
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_RACE,
                                    parked_reason="Lost the race", line="Lost the race")
            return False
        facts = dict(step.get("facts") or {})
        outcome = decide(program.get("control"), "race_winner", {})
        if outcome.to_owner and not facts.get("picked"):
            if not facts.get("awaiting_pick"):
                facts["awaiting_pick"] = True
                step["facts"] = facts
                self.service.save_step(step)
                self.service._checkpoint(program, step, "engine",
                                         f"{agent_label(self._profile_of(program, step))} is green and reviewed: yours to pick")
            return False
        facts["awaiting_pick"] = False
        facts["won"] = True
        step["facts"] = facts
        self.service.save_step(step)
        winner = agent_label(self._profile_of(program, step))
        took = duration_words(self._elapsed(step))
        for other in group:
            if other["id"] == step["id"] or other["state"] in ("parked", "merged", "done"):
                continue
            self.service.transition(program, other, "parked", parked_by=PARKED_BY_RACE,
                                    parked_reason=f"Lost the race to {winner}",
                                    line=f"Lost the race to {winner}")
        if outcome.to_owner:
            self.service._checkpoint(program, step, "owner", f"Picked {winner} as the winner")
        else:
            self.service.engine_decision(program, step, "race_winner", outcome, f"{winner} won the race in {took}")
        return True

    @staticmethod
    def _elapsed(step: Mapping[str, Any]) -> Optional[int]:
        from .program_service import _seconds_between

        return _seconds_between(step.get("started_at"))

    def open_pr(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        """Push the branch and open the PR (a PR on his own repository is
        WORK, as the hand does today)."""
        worktree, branch = str(step.get("worktree") or ""), str(step.get("branch") or "")
        base = str(program.get("base_branch") or "main")
        title = f"{program['title']}: {step['title']}"[:200]
        body = (f"Step {step['ordinal']} of the HoldSpeak program “{program['title']}”.\n\n"
                f"{step.get('brief_markdown') or ''}\n\n"
                f"Check: {step.get('check_verdict') or 'none'} on {str(step.get('checked_commit') or '')[:12]}"
                f" (log {step.get('check_log') or 'none'}).\n"
                f"Review: {step.get('review_verdict') or 'none'}.\n"
                f"The PR body names the item: program_step:{step['id']}.\n")
        if step.get("report"):
            body += f"\nThe agent's report:\n\n{step['report'][:6000]}\n"
        push = self._run(["git", "-C", worktree, "push", "-u", "origin", branch], cwd=worktree)
        if push.returncode != 0:
            self._pr_failed(program, step, "git push", push)
            return
        created = self._run(["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body],
                            cwd=worktree)
        if created.returncode != 0:
            self._pr_failed(program, step, "gh pr create", created)
            return
        url = next((line.strip() for line in str(created.stdout or "").splitlines() if "/pull/" in line), "")
        number = int(url.rstrip("/").rsplit("/", 1)[-1]) if re.search(r"/pull/\d+/?$", url) else None
        self.service.transition(program, step, "pr_open", pr_url=url or None, pr_number=number,
                                line=f"Opened PR #{number}" if number else "Opened the PR")

    def _pr_failed(self, program: dict[str, Any], step: dict[str, Any], what: str, proc: Any) -> None:
        detail = " ".join(str(proc.stdout or proc.stderr or "").split())[:200]
        self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                                parked_reason=f"{what} failed: {detail or proc.returncode}",
                                line=f"{what} failed; parked")

    # ── 5. the PR to its merge ───────────────────────────────────────

    def _pr(self, program: dict[str, Any], step: dict[str, Any]) -> None:
        record = {}
        try:
            record = self.ledger().get(str(step.get("launch_id") or "")) or {}
        except Exception:
            record = {}
        follow = record.get("follow_through") or {}
        pr = follow.get("pr") or {}
        facts = dict(step.get("facts") or {})
        if pr.get("number") and not step.get("pr_number"):
            step["pr_number"], step["pr_url"] = pr.get("number"), pr.get("url")
        if str(pr.get("state") or "") == "merged" or follow.get("pr_state") == "pr_merged":
            self.service.transition(program, step, "merged", facts=facts,
                                    line=f"Merged #{step.get('pr_number') or pr.get('number')}")
            return
        if follow.get("pr_state") == "pr_closed_unmerged":
            self.service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                                    parked_reason="The PR was closed without a merge",
                                    line="The PR was closed without a merge")
            return
        if not pr or facts.get("merge_requested_at"):
            return
        if step.get("gate_review") == "person" and not facts.get("person_approved"):
            logins = self.service.person_logins(step.get("for_person_id") or program.get("for_person_id"))
            approved = {str(login).casefold() for login in pr.get("approved_by") or []}
            if logins and approved & logins:
                facts["person_approved"] = True
                step["facts"] = facts
                self.service.save_step(step)
                self.service._checkpoint(program, step, "engine", "The person approved the PR on GitHub")
            else:
                if facts.get("person") is None:
                    person = step.get("for_person_id") or program.get("for_person_id")
                    facts["person"] = {"id": person, "name": self.service.person_name(person)}
                    step["facts"] = facts
                    self.service.save_step(step)
                return
        ci = str(pr.get("ci") or "none")
        if ci == "failing":
            if not facts.get("ci_failing_noted"):
                facts["ci_failing_noted"] = True
                step["facts"] = facts
                self.service.save_step(step)
                self.service._checkpoint(program, step, "engine", f"CI fails on PR #{step.get('pr_number')}")
            return
        if ci not in ("passing", "none"):
            return
        outcome = decide(program.get("control"), "merge", {
            "check_green": step.get("check_verdict") in ("green", "none"),
            "review_pass": step.get("gate_review") != "agent" or step.get("review_verdict") == "pass",
        })
        if not outcome.to_owner and step.get("gate_merge") != "owner":
            try:
                self.merge(program, step, by="engine", outcome=outcome)
            except ProgramRefused as exc:
                log.info(f"engine merge refused: {exc.code}")
            return
        if step["state"] == "pr_open" and not facts.get("merge_declined_at"):
            self.service.transition(program, step, "merge_ask",
                                    line=f"Merge? PR #{step.get('pr_number')}: check green"
                                         f"{', review passed' if step.get('review_verdict') == 'pass' else ''}")

    def merge(self, program: dict[str, Any], step: dict[str, Any], *, by: str, outcome: Any = None) -> dict[str, Any]:
        """``gh pr merge --squash`` on his press or by delegation. The merge
        itself is the follow-through's receipt (the next tick reads it)."""
        number = step.get("pr_number")
        if not number:
            raise ProgramRefused("pr_unknown", "The step has no PR number yet.")
        cwd = str(step.get("worktree") or program.get("repo_root") or "")
        proc = self._run(["gh", "pr", "merge", str(number), "--squash"], cwd=cwd)
        if proc.returncode != 0:
            detail = " ".join(str(proc.stdout or proc.stderr or "").split())[:200]
            self.service._checkpoint(program, step, "engine", f"Merge of PR #{number} failed: {detail}")
            raise ProgramRefused("merge_failed", f"gh could not merge PR #{number}: {detail}")
        facts = dict(step.get("facts") or {})
        facts["merge_requested_at"] = self.service._clock()
        facts["merged_by"] = by
        step["facts"] = facts
        self.service.save_step(step)
        if by == "owner" or outcome is None:
            self.service._checkpoint(program, step, "owner", f"Merged PR #{number} on his press")
        else:
            review = ", review passed" if step.get("review_verdict") == "pass" else ""
            self.service.engine_decision(program, step, "merge", outcome,
                                         f"Merged PR #{number} of step {step['ordinal']} (check green{review})")
        return {"merge": {"pr_number": number, "by": by}}


_DEFAULT: Optional[ProgramRunner] = None


def default_runner(service: Optional[ProgramService] = None) -> ProgramRunner:
    """The process's runner over the one Programs service."""
    global _DEFAULT
    from .program_service import default_program_service

    service = service or default_program_service()
    if _DEFAULT is None or _DEFAULT.service is not service:
        _DEFAULT = ProgramRunner(service)
    return _DEFAULT


def tick() -> list[str]:
    """The conductor's call (``workbench_conductor``)."""
    if not programs_on():
        return []
    return default_runner().tick()


__all__ = ["CHECK_TIMEOUT_SECONDS", "ProgramRunner", "TICK_SECONDS", "default_runner", "tick"]
