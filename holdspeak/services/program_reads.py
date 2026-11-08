"""The Program reads: pure queries over the Program store (2026-11-08).

Each function takes the database (``db``) it reads and answers what the
``ProgramService`` method of the same purpose answered before the move.
``ProgramService`` keeps a thin method of the same name and signature that
calls the function here, so every transport, the runner and every test are
unchanged.

The list rows, the detail wire (``_wire``), the step and requirement wires,
the owner's turn (``your_turn``, ``_turn``), the Program's state, the
family, ``for_project`` and ``for_person``, ``since_morning`` and the
ledger readers live here. The runtime (the lock, the held frames, the
runner, admission, the text apply, plan, decide, merge, delivery and
review) stays in ``program_service``.

One way only: this module imports the Program store, the Program vocabulary
(``program_definitions``), the brief words and the service errors. It never
imports ``program_service``, ``program_runner`` or ``program_text``. A read
that needs a collaborator the service holds (the clock, a person's name, a
library engine, a step's size) takes it as a keyword argument. Sibling
modules a read used before the move are still imported inside the read.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

from ..db.programs import ProgramStore
from ..logging_config import get_logger
from ..timestamps import utc_now_iso
from .brief_words import WAIT_SENTENCES, step_report, wait_line
from .errors import NotFound
from .program_definitions import (
    AUDIT_STATIONS, CLOSED_STATES, DECIDE_CHOICES, ENDINGS, FINISHED_STATES, FINISHED_WORDS, FROZEN_BAR,
    FROZEN_MERGED, FROZEN_READ, FROZEN_SET, NIGHT_ENDED, PARK_KIND, PARKED_BY_ENGINE, PARKED_BY_OWNER,
    PARKED_BY_PROGRAM, PLAN_GOAL_KIND, PROGRAM_BAND, PROGRAM_WORDS, PROPOSAL_KINDS, ProgramRefused, STATIONS,
    STEP_FIELDS, STEP_WORDS, TODO_CHOICES, TODO_STATES, _AUDIT_STATION_OF, _STATION_OF, agent_label,
    duration_words, history_of, programs_on,
)
from .program_rules import level_word

# The same logger name the reads logged under inside the service.
log = get_logger("program_service")

#: The collaborators a read takes from the service that holds them: its
#: clock, a person's display name, a library engine, a step's size.
Clock = Callable[[], str]
Names = Callable[[Optional[str]], str]
Engines = Callable[[Optional[str]], Any]
Sizer = Callable[..., Optional[dict[str, Any]]]


# ── the pure reads over rows (moved whole; program_service re-exports them) ──


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


def race_group(steps: Iterable[Mapping[str, Any]], step: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """A race step and its contenders (``[]`` for a step that is no race)."""
    parent = step.get("race_of") or (step.get("id") if int(step.get("race") or 0) >= 2 else None)
    if not parent:
        return []
    return [row for row in steps if row.get("id") == parent or row.get("race_of") == parent]


def race_all_red(group: list[Mapping[str, Any]]) -> bool:
    """PG-JOURNEYS J5: every contender of a race failed its rounds (parked by
    the engine as failed, not by the race)."""
    return len(group) >= 2 and all(
        _engine_parked(row) and (row.get("facts") or {}).get("ending") == "failed" for row in group)


def _race_red_as_one(items: list[dict[str, Any]], steps: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """J5: when both contenders are red after their rounds, the race fails as
    one step: one Parked row on the race step with both logs."""
    out: list[dict[str, Any]] = []
    done: set[str] = set()
    by_id = {str(row.get("id")): row for row in steps}
    for item in items:
        step = by_id.get(str(item.get("step_id") or ""))
        group = race_group(steps, step) if step is not None and item.get("kind") == "parked" else []
        if not group or not race_all_red(group):
            out.append(item)
            continue
        parent = next(row for row in group if not row.get("race_of"))
        if parent["id"] in done:
            continue
        done.add(parent["id"])
        logs = [{"agent": agent_label(row.get("profile")), "log": row.get("check_log"), "step_id": row["id"]}
                for row in group]
        out.append({**item, "id": f"{parent['id']}:parked", "step_id": parent["id"], "race": True, "logs": logs,
                    "race_both_red": True,
                    "title": (f"Parked step {parent['ordinal']} “{parent['title']}”: both contenders are "
                              "red after their rounds" if len(group) == 2 else
                              f"Parked step {parent['ordinal']} “{parent['title']}”: every contender is "
                              "red after its rounds")})
    return out


def _engine_parked(step: Mapping[str, Any]) -> bool:
    return (step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_ENGINE
            and not str(step.get("parked_reason") or "").startswith(NIGHT_ENDED))


def _live(steps: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [step for step in steps if step.get("state") not in CLOSED_STATES and step.get("state") != "failed"]


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
        if state in ("pr_open", "merge_ask") and step.get("gate_review") == "person" and _ask_review(facts):
            name = (facts.get("person") or {}).get("name") or "the reviewer"
            number = step.get("pr_number")
            items.append({**base, "id": f"{step['id']}:ask_review", "kind": "ask_review",
                          "choices": list(DECIDE_CHOICES["ask_review"]),
                          "title": f"Ask {name} to review PR #{number}" if number else f"Ask {name} to review"})
    items = _race_red_as_one(items, steps)
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


def _ask_review(facts: Mapping[str, Any]) -> bool:
    """HS-S25: offer "Ask <person> to review" when the latest complete read
    shows no approval or a request for changes; never when the read was not
    usable (asking again does not fix a read) or a merge is requested."""
    shown = facts.get("person_review")
    if isinstance(shown, Mapping) and shown.get("state"):
        return shown["state"] in ("not_approved", "changes")
    return not facts.get("person_approved")


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
    if step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_PROGRAM:
        return {"cause": "program_parked", "line": wait_line(step.get("ordinal"), agent, "program_parked")}
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


#: The words that do not name a Program ("start the overnight program on the hub").
_NAME_FILLER = frozenset({"the", "a", "an", "my", "our", "program", "programs", "programme", "on", "hub",
                          "please", "this", "that", "called", "named"})


def name_words(text: str) -> list[str]:
    """The words of a Program's name, lower case, without the filler."""
    return [word for word in re.findall(r"[a-z0-9]+", str(text or "").lower()) if word not in _NAME_FILLER]


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


def _waiting_first(rows: list[dict[str, Any]]) -> None:
    """Your turn, failed, running, drafting, done, parked; newest change first in a band."""
    rows.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    rows.sort(key=lambda row: PROGRAM_BAND.get(row["state"], 9))


# ── the reads over the store (ProgramService delegates here) ─────


def require_program(db: Any, program_id: str) -> dict[str, Any]:
    program = ProgramStore(db).get_program(str(program_id or ""))
    if program is None:
        raise NotFound("program", str(program_id))
    return program


def require_step(db: Any, program: Mapping[str, Any], step_id: str) -> dict[str, Any]:
    step = ProgramStore(db).get_step(str(step_id or ""))
    if step is None or step["program_id"] != program["id"]:
        raise NotFound("program_step", str(step_id))
    return step


def requirement_rows(db: Any, program_id: str) -> list[dict[str, Any]]:
    return ProgramStore(db).list_requirements(str(program_id))


def proposal_rows(db: Any, program_id: str, checkpoints: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
    rows = checkpoints if checkpoints is not None else ProgramStore(db).list_checkpoints(str(program_id))
    return [row for row in rows if row.get("kind") in PROPOSAL_KINDS]


def _turn(db: Any, program: Mapping[str, Any], steps: list[Mapping[str, Any]], *,
          requirements: Optional[list[dict[str, Any]]] = None,
          checkpoints: Optional[list[dict[str, Any]]] = None, clock: Clock) -> list[dict[str, Any]]:
    from . import program_delivery

    reqs = requirements if requirements is not None else requirement_rows(db, program["id"])
    items = your_turn(program, steps, reqs, proposal_rows(db, program["id"], checkpoints))
    from . import program_lessons

    # JRN11: the lessons the engine saw, each his to keep or skip.
    items += program_lessons.turn_items(program, checkpoints if checkpoints is not None
                                        else ProgramStore(db).list_checkpoints(program["id"]))
    if program.get("template") == "audit":
        from . import program_audit

        # JRN9, JRN10: the findings to file (Secure) and the fix program.
        items += program_audit.turn_items(program, steps, checkpoints if checkpoints is not None
                                          else ProgramStore(db).list_checkpoints(program["id"]))
    # The live walk (2026-11-01): Close is the last thing he is asked, after
    # the audit's and the lessons' rows (they are added after your_turn's).
    items = [item for item in items if item["kind"] != "close"] + [item for item in items if item["kind"] == "close"]
    if program.get("closed_at") and program_delivery.target(program) is not None:
        # LANG13: a delivery that failed, or that waits for his merge.
        rows = [row for row in (checkpoints if checkpoints is not None
                                else ProgramStore(db).list_checkpoints(program["id"])) if row.get("kind") == "delivery"]
        item = program_delivery.turn_item(program, rows[0] if rows else None, rows)
        if item is not None:
            items.append(item)
    return _with_pages(db, program["id"], items, now=clock())


def _state(db: Any, program: Mapping[str, Any], steps: list[Mapping[str, Any]], *,
           requirements: Optional[list[dict[str, Any]]] = None,
           checkpoints: Optional[list[dict[str, Any]]] = None) -> str:
    reqs = requirements if requirements is not None else requirement_rows(db, program["id"])
    return program_state(program, steps, reqs, proposal_rows(db, program["id"], checkpoints))


def program_list(db: Any, principal: Any = None, *, q: Any = None, project_id: Any = None,
                 person_id: Any = None, clock: Clock, person_name: Names) -> dict[str, Any]:
    """Every Program, waiting first, then running, drafting, done, parked;
    the most recently changed first inside a band. PG-REQ §7: ``q``
    (every word in the row's ``search_words``), ``project_id`` and
    ``person_id`` narrow the rows; ``of`` is the count before them."""
    rows = []
    programs = ProgramStore(db).list_programs()
    steps_of: dict[str, list[dict[str, Any]]] = {}
    for program in programs:
        steps = steps_of[program["id"]] = ProgramStore(db).list_steps(program["id"])
        rows.append(_summary(db, program, steps, clock=clock, person_name=person_name))
    # PG-IMPORT IMP7: each row names the Program it came from; a parent
    # carries its family's count and one worst state.
    by_id = {row["id"]: row for row in rows}
    for program, row in zip(programs, rows):
        parent = parent_of(db, program)
        if parent and parent in by_id:
            row["parent_id"] = parent
    for row in rows:
        kids = [other for other in rows if other.get("parent_id") == row["id"]]
        if kids:
            worst = min((other["state"] for other in kids), key=lambda s: PROGRAM_BAND.get(s, 9))
            row["kin"] = {"children": len(kids), "worst": worst, "worst_word": PROGRAM_WORDS.get(worst, worst)}
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
    tonight = night_of(programs, steps_of)
    if tonight is not None:
        out["night"] = tonight
    return out


#: A step of a night Program that waits for the night (not handed yet).
NIGHT_QUEUED_STATES = frozenset({"planned", "ready"})


def night_of(programs: list[dict[str, Any]], steps_of: Mapping[str, list[dict[str, Any]]]) -> Optional[dict[str, Any]]:
    """The night, from the rows the list already read: ``{program_id, start,
    queued}``. ``queued`` counts the steps of the night Programs (a ``night``
    line, not Drafting or Parked) that wait for the night; ``program_id`` is
    the first night Program with a queued step, ``start`` its night line's
    start (``HH:MM``, local). ``None`` when the engine is off
    (``HOLDSPEAK_PROGRAMS=off``), no Program has a night line, or nothing is
    queued: the face draws nothing, never a zero."""
    if not programs_on():
        return None
    first: Optional[dict[str, Any]] = None
    queued = 0
    for program in programs:
        night = program.get("night")
        if not isinstance(night, Mapping) or not night.get("start") or program.get("state") in ("drafting", "parked"):
            continue
        waiting = sum(1 for step in steps_of.get(program["id"]) or []
                      if step.get("state") in NIGHT_QUEUED_STATES and not step.get("race_of"))
        if waiting and first is None:
            first = program
        queued += waiting
    if first is None:
        return None
    return {"program_id": first["id"], "start": str(first["night"]["start"]), "queued": queued}


def get(db: Any, principal: Any, program_id: str, *, clock: Clock, person_name: Names, engine: Engines, estimate: Sizer,
        reach: Optional[Callable[[list[dict[str, Any]], Optional[str]], list[dict[str, Any]]]] = None) -> dict[str, Any]:
    program = require_program(db, program_id)
    steps = ProgramStore(db).list_steps(program["id"])
    wire = _wire(db, program, steps, clock=clock, person_name=person_name, engine=engine, estimate=estimate)
    if reach is not None:
        # HS-S35: each pinned checkpoint says whether its ref is reachable now.
        wire["checkpoints"] = reach(wire["checkpoints"], program.get("repo_root"))
    # LANG5: the rows a call left for his press (only when there are some).
    from .program_spoken import on_desk

    held = on_desk(program["id"])
    if held:
        wire["held_shape"] = held
    # PG-IMPORT IMP7: the Program's family in one object.
    wire["family"] = family(db, program, clock=clock, person_name=person_name)
    return wire


def parent_of(db: Any, program: Mapping[str, Any]) -> Optional[str]:
    """The Program this one came from: ``origin_ref`` ``program:<id>``
    (an audit's fix program) or ``program_step:<id>``, else the Program
    whose step's agent made it (``created_by`` ``launch:<id>``)."""
    kind, _, ident = str(program.get("origin_ref") or "").partition(":")
    if kind == "program" and ident and ident != program.get("id"):
        return ident.split(":", 1)[0]
    step = None
    if kind == "program_step" and ident:
        step = ProgramStore(db).get_step(ident.split(":", 1)[0])
    created = str(program.get("created_by") or "")
    if step is None and created.startswith("launch:"):
        with db._connection() as conn:
            row = conn.execute("SELECT program_id FROM program_steps WHERE launch_id = ? LIMIT 1",
                               (created.split(":", 1)[1],)).fetchone()
        return str(row["program_id"]) if row and row["program_id"] != program.get("id") else None
    parent = (step or {}).get("program_id")
    return str(parent) if parent and parent != program.get("id") else None


def _family_row(db: Any, program: Mapping[str, Any], *, ending: bool, clock: Clock, person_name: Names) -> dict[str, Any]:
    summary = _summary(db, program, ProgramStore(db).list_steps(program["id"]), clock=clock, person_name=person_name)
    row = {"id": program["id"], "name": program["title"], "state": summary["state"],
           "state_word": summary["state_word"], "line": summary.get("line") or ""}
    if ending:
        row["ending"] = {"done": "finished", "failed": "failed"}.get(summary["state"], "none")
    return row


def family(db: Any, program: Mapping[str, Any], programs: Optional[list[dict[str, Any]]] = None, *,
           clock: Clock, person_name: Names) -> dict[str, Any]:
    """``{parent: {id, name, state, state_word, line} | None, children:
    [{id, name, state, state_word, ending, line}]}``: the Program it came
    from and the Programs it made (BroCrew's forest, in one object)."""
    parent_id = parent_of(db, program)
    parent = ProgramStore(db).get_program(parent_id) if parent_id else None
    everything = programs if programs is not None else ProgramStore(db).list_programs()
    children = [other for other in everything if other["id"] != program["id"] and parent_of(db, other) == program["id"]]
    children.sort(key=lambda other: str(other.get("created_at") or ""))
    return {"parent": _family_row(db, parent, ending=False, clock=clock, person_name=person_name) if parent else None,
            "children": [_family_row(db, child, ending=True, clock=clock, person_name=person_name) for child in children]}


def find(db: Any, principal: Any, *, program_id: Any = None, name: Any = None,
         startable: bool = False) -> dict[str, Any]:
    """PG15: one Program by its id, or by the words he said ("the
    overnight program"): every word must be in its title or its template.
    ``startable`` puts a Drafting or Parked match first. Nothing matches:
    ``program_not_found``; it never makes a Program."""
    if program_id:
        found = ProgramStore(db).get_program(str(program_id))
        if found is not None:
            return found
    said = str(name or program_id or "").strip()
    words = name_words(said)
    if not words:
        raise ProgramRefused("program_name_required", "Say the name of the program.", status=400)
    matches = []
    for program in ProgramStore(db).list_programs():
        own = set(name_words(str(program.get("title") or ""))) | set(name_words(str(program.get("template") or "")))
        if all(word in own for word in words):
            matches.append(program)
    if not matches:
        raise ProgramRefused("program_not_found", f"There is no program with the name {said}. I did not start a program.",
                             status=404)
    if startable:
        matches.sort(key=lambda row: row.get("state") not in ("drafting", "parked"))
    return matches[0]


def for_project(db: Any, project_id: str, *, clock: Clock, person_name: Names) -> list[dict[str, Any]]:
    """The Room's Programs fold (§9b): one row per Program, worst first."""
    rows = [
        _summary(db, program, ProgramStore(db).list_steps(program["id"]), clock=clock, person_name=person_name)
        for program in ProgramStore(db).list_programs() if program.get("project_id") == project_id
    ]
    _waiting_first(rows)
    # The Room's row draws the Programs window's step dots: the same track.
    return [{key: row.get(key) for key in ("id", "title", "state", "state_word", "done", "total", "your_turn",
                                            "updated_at", "track")} for row in rows]


def for_person(db: Any, person_id: str, *, since: Optional[str] = None, clock: Clock,
               person_name: Names) -> list[dict[str, Any]]:
    """The person's Programs (§9b): the room's line, and the 1:1 brief's
    "To show them" (a step merged since ``since``) and "To ask" (a
    finding or a review waits on them)."""
    out = []
    for program in ProgramStore(db).list_programs():
        steps = ProgramStore(db).list_steps(program["id"])
        mine = program.get("for_person_id") == person_id or any(
            step.get("for_person_id") == person_id for step in steps)
        if not mine:
            continue
        summary = _summary(db, program, steps, clock=clock, person_name=person_name)
        to_show = [
            {"step_id": step["id"], "title": step["title"], "pr_number": step.get("pr_number"),
             "pr_url": step.get("pr_url"), "merged_at": step.get("ended_at")}
            for step in steps
            if step.get("state") in FINISHED_STATES and step.get("pr_number")
            and (since is None or str(step.get("ended_at") or "") > str(since))
        ]
        to_ask = [
            {"step_id": item["step_id"], "title": item["title"], "kind": item["kind"]}
            for item in _turn(db, program, steps, clock=clock)
            if item["kind"] in ("finding", "ask_review") and (item.get("for_person_id") == person_id)
        ]
        waits = next((item for item in _turn(db, program, steps, clock=clock) if item.get("pr")), None)
        line = f"{program['title']} · {summary['done']} of {summary['total']}"
        if waits and waits.get("pr", {}).get("number"):
            line += f" · PR #{waits['pr']['number']} waits on you"
        out.append({"id": program["id"], "title": program["title"], "state": summary["state"],
                    "state_word": summary["state_word"], "done": summary["done"],
                    "total": summary["total"], "line": line, "to_show": to_show, "to_ask": to_ask})
    return out


def needs_you_items(db: Any, *, clock: Clock) -> list[dict[str, Any]]:
    """Every Program's your-turn items (``needs_you_membership.program_items``)."""
    items: list[dict[str, Any]] = []
    for program in ProgramStore(db).list_programs():
        if program["state"] == "done":
            # JRN9 to JRN11: a finished Program still asks to file an
            # audit's findings, to make its fix program, and its lessons.
            items.extend(item for item in _turn(db, program, ProgramStore(db).list_steps(program["id"]), clock=clock)
                         if item["kind"] in ("audit_file", "fix_program", "lesson"))
            continue
        if program["state"] in ("drafting", "parked", "done"):
            continue
        items.extend(_turn(db, program, ProgramStore(db).list_steps(program["id"]), clock=clock))
    return items


def since_morning(db: Any, principal: Any = None, *, now: Any = None) -> dict[str, int]:
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
    for program in ProgramStore(db).list_programs():
        steps = ProgramStore(db).list_steps(program["id"])
        # PG17: an imported step moved when it merged, not when it was
        # written; a Program of imported steps only moves with them.
        imported = bool(steps) and all(history_of(step) for step in steps)
        if not ((today(program.get("updated_at")) and not imported) or any(
                today(step.get("ended_at") if history_of(step) else step.get("updated_at")) for step in steps)):
            continue
        out["moved"] += 1
        state = _state(db, program, steps)
        if state == "running":
            out["running"] += 1
        elif state in ("waiting", "failed"):
            out["waiting"] += 1
        elif state == "done":
            out["done"] += 1
        out["merged"] += sum(1 for step in steps if step.get("state") in FINISHED_STATES
                             and step.get("pr_number") and today(step.get("ended_at")))
    return out


def counts_for_project(db: Any, project_id: str, *, clock: Clock, person_name: Names) -> dict[str, int]:
    rows = for_project(db, project_id, clock=clock, person_name=person_name)
    return {
        "running": sum(1 for row in rows if row["state"] == "running"),
        "waiting": sum(1 for row in rows if row["state"] == "waiting"),
        "done": sum(1 for row in rows if row["state"] == "done"),
    }


def _top_steps(steps: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [step for step in steps if not step.get("race_of")]


def _summary(db: Any, program: Mapping[str, Any], steps: list[dict[str, Any]], *,
             requirements: Optional[list[dict[str, Any]]] = None,
             checkpoints: Optional[list[dict[str, Any]]] = None, clock: Clock, person_name: Names) -> dict[str, Any]:
    from .program_requirements import counts as requirement_counts

    top = _top_steps(steps)
    reqs = requirements if requirements is not None else requirement_rows(db, program["id"])
    checkpoints = checkpoints if checkpoints is not None else ProgramStore(db).list_checkpoints(program["id"])
    state = _state(db, program, steps, requirements=reqs, checkpoints=checkpoints)
    turn = _turn(db, program, steps, requirements=reqs, checkpoints=checkpoints, clock=clock)
    # A skipped step lets its dependents run (``_ordinal_finished``) but is
    # never counted done: ``done`` counts merged and done steps only.
    done = sum(1 for step in top if any(row.get("state") in FINISHED_STATES for row in steps
                                        if int(row["ordinal"]) == int(step["ordinal"])))
    skipped = sum(1 for step in top if _ordinal_finished(steps, step["ordinal"])) - done
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
    origin = str(program.get("origin_ref") or "")
    if origin.startswith("workbench:"):
        # 2026-11-08: a run of an automation; the rail shows one tile per automation.
        summary["automation_id"] = origin.partition(":")[2]
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
    place = _place(db, program, person_name=person_name)
    summary["project"] = place["project"]
    summary["for_person"] = place["person"] if place["person"] and place["person"].get("id") else None
    persons = sorted({str(pid) for pid in [program.get("for_person_id"), *(step.get("for_person_id") for step in steps)] if pid})
    summary["persons"] = [{"id": pid, "name": person_name(pid)} for pid in persons]
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
    if state == "drafting" and str(program.get("origin_ref") or "").startswith("after:"):
        # JRN1 (the walk, 2026-11-01): a chained Program says, while it
        # waits, which one it starts after.
        before = ProgramStore(db).get_program(str(program["origin_ref"]).partition(":")[2])
        if before is not None and _waits_on(db, program) is not None:
            summary["line"] = f"Starts after {before['title']}"
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


def _ordinal_finished(steps: Iterable[Mapping[str, Any]], ordinal: int) -> bool:
    rows = [step for step in steps if int(step["ordinal"]) == int(ordinal)]
    return any(step.get("state") in FINISHED_STATES for step in rows) or (
        bool(rows) and all(step.get("state") == "parked" and step.get("parked_by") == PARKED_BY_OWNER
                           for step in rows if not step.get("race_of")))


def _engine_wire(profile: Optional[str], engine_id: Optional[str], *, engine: Engines) -> Optional[dict[str, Any]]:
    if str(profile or "") != "pi-default":
        return None
    if not engine_id:
        return {"id": None, "label": "the desk's engine for coding", "short": "", "assignment": True}
    found = engine(engine_id)
    if found is None:
        return {"id": engine_id, "label": engine_id, "short": engine_id, "missing": True}
    return {"id": engine_id, "label": found.label, "short": found.short_name,
            "model": found.engine.model if found.engine is not None else None}


def requirement_wire(program: Mapping[str, Any], row: Mapping[str, Any], step: Optional[Mapping[str, Any]],
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


def step_wire(db: Any, program: Mapping[str, Any], step: Mapping[str, Any],
              checkpoints: list[dict[str, Any]], *, requirements: Optional[list[dict[str, Any]]] = None,
              his: Optional[set[str]] = None,
              steps_by_id: Optional[Mapping[str, Mapping[str, Any]]] = None, engine: Engines, person_name: Names,
              estimate: Sizer) -> dict[str, Any]:
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
    audit = program.get("template") == "audit"
    return {
        "id": step["id"], "ordinal": step["ordinal"], "title": step["title"], "state": state,
        "state_word": word, "station": (_AUDIT_STATION_OF if audit else _STATION_OF).get(state, -1),
        "stations": list(AUDIT_STATIONS if audit else STATIONS),
        "brief": step.get("brief_markdown") or "", "owns": list(step.get("owns") or []),
        # 2026-11-08: "prompt" is one model call (no agent, no worktree); its
        # answer goes where ``deliver`` says, its brief reads ``sources``.
        "kind": step.get("kind") or "agent", "deliver": step.get("deliver"),
        "sources": list(step.get("sources") or []),
        "after": list(step.get("after") or []), "effort": step.get("effort"),
        "profile": profile, "agent": agent_label(profile), "engine": _engine_wire(profile, engine_id, engine=engine),
        "prefer_idle": bool(step.get("prefer_idle") or program.get("prefer_idle")),
        "may_call": bool(step.get("may_call") or program.get("may_call")),
        "held_reason": step.get("held_reason"), "race": int(step.get("race") or 0),
        "race_of": step.get("race_of"),
        # J5: the race failed as one step (every contender red after its rounds).
        "race_both_red": bool(steps_by_id and not step.get("race_of")
                              and race_all_red(race_group(steps_by_id.values(), step))),
        "gate": {
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
        "for_person": person_name(step.get("for_person_id")) or None,
        # PG-IMPORT IMP1: the report in registers (Checked, The agent
        # says, Not checked, Files); the agent's own text is report_text.
        "report": step_report(step, checkpoints, requirements if requirements is not None
                              else requirement_rows(db, program["id"])),
        "report_text": step.get("report"), "last_checkpoint": last,
        # PG-IMPORT IMP6: he has the lane (Take it over).
        "taken": isinstance(facts.get("taken"), Mapping),
        # PG-IMPORT IMP3: what it waits on ({cause, line}), or None.
        "wait": step_wait(program, step, list((steps_by_id or {}).values())
                          or ProgramStore(db).list_steps(program["id"])),
        # PG-IMPORT IMP2: finished | failed | interrupted | none.
        "ending": facts.get("ending") if facts.get("ending") in ENDINGS else "none",
        "started_at": step.get("started_at"), "ended_at": step.get("ended_at"),
        "updated_at": step.get("updated_at"),
        "elapsed_seconds": _seconds_between(step.get("started_at"), step.get("ended_at")),
        "elapsed": duration_words(_seconds_between(step.get("started_at"), step.get("ended_at"))),
        # PG19: the ordered agents, the usage limit it stopped at, and
        # each handoff (with the brief he can read under View brief).
        "runs_on": [entry_wire(row, engine=engine) for row in runs_on_of(program, step)],
        "limit": {key: limit.get(key) for key in ("until", "words", "rule", "line", "share", "next", "waiting",
                                                   "profile", "seen_at", "auto_at")} if limit and state == "limited" else None,
        "handoffs": [dict(row) for row in step.get("handoffs") or []],
        "history": history_of(step),
        # PG-LANG §5.4: the step's context budget (None: the Program's).
        "budget_tokens": step.get("budget_tokens"),
        # PG-LANG §5.4, §12 (LANG6): a step not handed yet carries its size
        # by rule ({tokens, budget, share, fits, words}); the lamp "18k of 32k".
        "estimate": estimate(program, step, profile, engine_id, requirements)
        if step.get("state") in ("planned", "ready") else None,
        **_step_requirements_wire(db, program, step, requirements, his, steps_by_id),
    }





def _step_requirements_wire(db: Any, program: Mapping[str, Any], step: Mapping[str, Any],
                            requirements: Optional[list[dict[str, Any]]], his: Optional[set[str]],
                            steps_by_id: Optional[Mapping[str, Mapping[str, Any]]]) -> dict[str, Any]:
    """PG-REQ §11: a step's own requirements and its every-step copies,
    their count, what he can still change and why the rest is frozen,
    and the lines he added to its brief."""
    from .program_requirements import counts as requirement_counts

    reqs = requirements if requirements is not None else requirement_rows(db, program["id"])
    owner_id = step.get("race_of") or step["id"]
    own = [row for row in reqs if row.get("step_id") == owner_id]
    editable, frozen = step_fields(step)
    out: dict[str, Any] = {
        "requirements": [requirement_wire(program, row, step, reqs, his or set(), steps_by_id or {step["id"]: step})
                         for row in own],
        "editable": editable, "frozen": frozen,
        "amendments": [{key: item.get(key) for key in ("at", "by", "line", "sent_at")}
                       for item in (step.get("facts") or {}).get("amendments") or []],
    }
    met = requirement_counts(own)
    if met:
        out["requirements_met"] = met
    return out


def _place(db: Any, program: Mapping[str, Any], *, person_name: Names) -> dict[str, Any]:
    """The status bar's place line parts (§9b): project, origin, person."""
    project = None
    if program.get("project_id"):
        with db._connection() as conn:
            row = conn.execute("SELECT name FROM projects WHERE id=?", (program["project_id"],)).fetchone()
        project = {"id": program["project_id"], "name": str(row["name"]) if row else program["project_id"]}
    origin = None
    if program.get("origin_ref"):
        kind, _, ident = str(program["origin_ref"]).partition(":")
        title = ""
        try:
            if kind == "automation":
                # PG14: an automation made it; its place line names it.
                wb = db.workbenches.get(ident, include_deleted=True)
                title = str(getattr(wb, "name", "") or "")
            elif kind in ("program", "after"):
                # The Program it came from; JRN1's ``after``: the one it waits on.
                title = str((ProgramStore(db).get_program(ident) or {}).get("title") or "")
            else:
                from .agent_hand_service import item_title

                title = item_title(db, kind, ident)
        except Exception:
            title = ""
        origin = {"ref": program["origin_ref"], "kind": kind, "id": ident, "title": title}
    person = None
    if program.get("for_person_id"):
        person = {"id": program["for_person_id"], "name": person_name(program["for_person_id"])}
    return {"project": project, "origin": origin, "person": person}


def _wire(db: Any, program: Mapping[str, Any], steps: list[dict[str, Any]], *, clock: Clock, person_name: Names, engine: Engines,
          estimate: Sizer) -> dict[str, Any]:
    seams = {"engine": engine, "person_name": person_name, "estimate": estimate}
    from .program_requirements import provable, repository_config

    # A plan_goal claim the steps made unneeded (planned by hand first)
    # did nothing: it is no line of the ledger he reads (nor the shaper's).
    checkpoints = [row for row in ProgramStore(db).list_checkpoints(program["id"])
                   if not (row.get("kind") == PLAN_GOAL_KIND and row.get("choice") == "skipped")]
    reqs = requirement_rows(db, program["id"])
    summary = _summary(db, program, steps, requirements=reqs, checkpoints=checkpoints, clock=clock, person_name=person_name)
    turn = _turn(db, program, steps, requirements=reqs, checkpoints=checkpoints, clock=clock)
    # PG-WINDOW: the held items' briefs and the steps' stories, in his terms.
    from .brief_words import window_words

    briefs, stories = window_words(program, steps, turn, checkpoints, status=_status_line(program, summary))
    turn = [{**item, "brief": briefs.get(str(item.get("id")))} for item in turn]
    his = {str(item.get("requirement_id")) for item in turn if item.get("requirement_id")}
    by_id = {step["id"]: step for step in steps}
    top = []
    for step in _top_steps(steps):
        row = step_wire(db, program, step, checkpoints, requirements=reqs, his=his, steps_by_id=by_id, **seams)
        row["story"] = stories.get(str(step["id"]), [])
        row["contenders"] = [{**step_wire(db, program, other, checkpoints, requirements=reqs, his=his,
                                             steps_by_id=by_id, **seams),
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
                    "engine": _engine_wire(program.get("default_profile"), program.get("default_engine"), engine=engine),
                    "runs_on": [entry_wire(row, engine=engine) for row in runs_on_of(program, {})]},
        "allowed_profiles": list(program.get("allowed_profiles") or []),
        "may_handoff": bool(program.get("may_handoff")),
        "usage_warning_share": program.get("usage_warning_share"),
        "reviewer": {"profile": program.get("reviewer_profile"),
                     "agent": agent_label(program.get("reviewer_profile")) if program.get("reviewer_profile") else None,
                     "engine": _engine_wire(program.get("reviewer_profile"), program.get("reviewer_engine"), engine=engine)},
        "prefer_idle": bool(program.get("prefer_idle")), "template": program.get("template") or None,
        "may_call": bool(program.get("may_call")),
        "origin_ref": program.get("origin_ref"), "for_person_id": program.get("for_person_id"),
        "note_id": program.get("note_id"), "note_window": f"pullout:note:{program['note_id']}" if program.get("note_id") else None,
        "place": _place(db, program, person_name=person_name),
        "steps": top, "checkpoints": checkpoints[:200],
        "your_turn_items": turn,
        # PG-REQ §11: the Program's own (the end check) and the every-step
        # parents, in R order; what this repository can prove.
        "requirements": [requirement_wire(program, row, None, reqs, his, by_id)
                         for row in reqs if not row.get("step_id")],
        "can_prove": {"check": True, "review": True, "word": True, "shot": not shot_reason,
                      "shot_reason": shot_reason or None},
        "decided_for_you": decided_for_you(db, program["id"]),
        "control_word": level_word(program.get("control")),
        "spend_limit_usd": program.get("spend_limit_usd"), "spend_note": spend_note(program.get("spend_limit_usd")),
        "closed_at": program.get("closed_at"),
        "revision": int(program.get("revision") or 0),
        "status_line": _status_line(program, summary),
        **_language_wire(db, program, engine=engine),
        **_audit_wire(program, steps, checkpoints),
    }


def spend_note(amount: Any) -> Optional[str]:
    """HS-S24 (D20/G24 ruled 2026-11-07, disclosure-only): the amount he
    typed is a note he reads on the Program's face, never a cap. ``None``
    when he set none. ``spend note · 40 USD``; cents only when he typed them."""
    if amount is None or amount == "":
        return None
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return None
    words = f"{value:.0f}" if value == int(value) else f"{value:.2f}"
    return f"spend note · {words} USD"


def _audit_wire(program: Mapping[str, Any], steps: list[dict[str, Any]],
                checkpoints: list[dict[str, Any]]) -> dict[str, Any]:
    """PG-LANG JRN9 (journey J7): an audit's Findings board, and the fix
    program its MUST findings made (absent on any other Program)."""
    from . import program_audit

    if not program_audit.is_audit(program):
        return {}
    marks = program_audit.marks_of(checkpoints)
    return {"findings_board": program_audit.board(_top_steps(steps)),
            "fix_program_id": marks.get("fix_program_id") or None}


def _language_wire(db: Any, program: Mapping[str, Any], *, engine: Engines) -> dict[str, Any]:
    """PG-LANG (§12, the wire): the fields the Program text writes, and
    its interview rounds."""
    planner = None
    if program.get("planner_engine"):
        found = engine(program["planner_engine"])
        planner = {"engine": program["planner_engine"], "label": getattr(found, "label", None) or program["planner_engine"]}
    ref = str(program.get("delivery_ref") or "")
    rounds = []
    for row in ProgramStore(db).list_rounds(program["id"]):
        # LANG9: a question's why, its offered answers, skipped, and what
        # the answer became; the round's count of changes, its waiting question.
        questions = [{**{key: item.get(key) for key in ("id", "text", "answer", "answered_by", "at", "why", "rule")},
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


def _status_line(program: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    parts = [summary["state_word"], f"{summary['done']} of {summary['total']} done"]
    if summary.get("skipped"):
        parts.append(f"{summary['skipped']} skipped")
    if summary["your_turn"]:
        # The walk (2026-11-01): "3 waits on you" read wrong.
        parts.append(f"{summary['your_turn']} {'waits' if summary['your_turn'] == 1 else 'wait'} on you")
    if program.get("check_command"):
        parts.append(f"check: {_check_name(str(program['check_command']))}")
    parts.append(f"control {level_word(program['control'])}")
    return " · ".join(parts)


def runs_on_of(program: Mapping[str, Any], step: Mapping[str, Any]) -> list[dict[str, Any]]:
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


def entry_wire(entry: Mapping[str, Any], *, engine: Engines) -> dict[str, Any]:
    """One agent of a Runs on list as the faces read it."""
    profile = str(entry.get("profile") or "")
    wired = _engine_wire(profile, entry.get("engine"), engine=engine)
    label = agent_label(profile)
    if profile == "pi-default":
        label += f" · {wired.get('short') or wired.get('label')}" if wired and not wired.get("assignment") else " · the desk's assignment"
    return {"profile": profile, "engine": entry.get("engine") or None, "agent": agent_label(profile), "label": label}


def _waits_on(db: Any, program: Mapping[str, Any]) -> Optional["ProgramRefused"]:
    """JRN1: a Program made from a draft's later Program waits on the one
    before it (``origin_ref = after:<id>``) until that one is Done. A
    Program another one made (``program:<id>``: a fix program, an agent's
    child) never waits on it."""
    kind, _, ident = str(program.get("origin_ref") or "").partition(":")
    if kind != "after" or not ident:
        return None
    before = ProgramStore(db).get_program(ident)
    if before is None or before.get("closed_at") or before.get("state") == "done":
        return None
    steps = ProgramStore(db).list_steps(ident)
    if steps and _state(db, before, steps) == "done":
        return None
    return ProgramRefused("waits_on_program", f"It starts after {before['title']} is done.",
                          program_id=ident)


def decided_for_you(db: Any, program_id: str) -> list[dict[str, Any]]:
    return [
        {"id": row["id"], "at": row["at"], "step_id": row["step_id"] or None, "kind": row["kind"],
         "choice": row["choice"], "rule": row["rule"], "line": row["line"],
         "overturnable": bool(row["overturnable"]) and not row["overturned_at"],
         "overturned_at": row["overturned_at"], "operation_id": row["operation_id"],
         "decision_record_id": row.get("decision_record_id")}
        for row in ProgramStore(db).list_checkpoints(program_id) if row.get("rule")
    ]
