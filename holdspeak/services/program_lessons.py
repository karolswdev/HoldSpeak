"""Lessons: teaching the engine (PG-JOURNEYS J8; PG-LANG §13b JRN11, JRN12).

PROGRAM-JOURNEYS-2026-10-31.md "J8 · Teaching the engine". All defaults are
approved.

- **JRN11, the lesson rule** (by rule, no model): the same red cause of the
  check on two steps of a Program (the check's first red line, else its
  first reason, read by ``program_verifier``), or the same reviewer finding
  on three steps, is a **Lesson**: one ledger row (``kind = lesson``) and one
  Your turn row "Lesson · …" with **Keep for this program** · **Keep for
  HoldSpeak** · **Skip**. A lesson is never kept by rule, at any level (it
  changes the bar). A cause he skipped is not proposed again in the Program.
- **Keep for this program** adds an every-step Review requirement.
- **JRN12, Keep for HoldSpeak** (the repository): a tiny step of this Program
  that edits ``.holdspeak/program.json`` (one ``requirements`` item), checked,
  reviewed and merged as any step. A new Program plants the repository's
  requirements from the file in his checkout (``_plant_requirements``), so
  it reads the lesson once the merge is in that checkout.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_lessons")

KIND = "lesson"
CHOICES = ("keep_program", "keep_repo", "skip")
#: The steps a cause must hit before it is a lesson.
RED_STEPS, FINDING_STEPS = 2, 3
_PREFIX = re.compile(r"^a line is red:\s*", re.I)


def key_of(source: str, words: str) -> str:
    plain = re.sub(r"\d+", "#", str(words or "").lower())
    plain = re.sub(r"[^a-z#]+", " ", plain).strip()
    return hashlib.sha256(f"{source}:{plain}".encode("utf-8")).hexdigest()[:16]


def red_cause(reasons: list[str]) -> Optional[str]:
    """The cause a red check names: its first red line, else its first reason."""
    rows = [str(reason or "").strip() for reason in reasons or [] if str(reason or "").strip()]
    if not rows:
        return None
    line = next((row for row in rows if _PREFIX.match(row)), rows[0])
    return _PREFIX.sub("", line)[:200]


def note_red(facts: dict[str, Any], reasons: list[str]) -> None:
    """A red check on a step: its cause joins the step's ``lesson_seen``."""
    cause = red_cause(reasons)
    if cause:
        facts.setdefault("lesson_seen", {})[key_of("red", cause)] = {"source": "red", "words": cause}


def note_findings(facts: dict[str, Any], findings: list[Mapping[str, Any]]) -> None:
    """A review's findings on a step (every level; not the engine's own
    "the reviewer gave no answer" rows)."""
    seen = facts.setdefault("lesson_seen", {})
    for finding in findings:
        text = " ".join(str(finding.get("text") or "").split()).rstrip(".")
        if not text or finding.get("requirement_id") or re.match(r"^R\d+ is unmet", text):
            continue
        seen[key_of("finding", text)] = {"source": "finding", "words": text[:200]}


def scan(service: Any, program: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The lesson rule over the Program's steps: each new lesson as a ledger
    row (the engine's line). Idempotent: a cause raised once (kept, skipped
    or open) is never raised again in this Program."""
    steps = [step for step in service.store.list_steps(program["id"])]
    hits: dict[str, dict[str, Any]] = {}
    for step in steps:
        for key, row in ((step.get("facts") or {}).get("lesson_seen") or {}).items():
            hit = hits.setdefault(key, {**row, "key": key, "steps": []})
            ordinal = int(step["ordinal"])
            if ordinal not in hit["steps"]:
                hit["steps"].append(ordinal)
    raised = {str((row.get("undo") or {}).get("key") or "") for row in service.store.list_checkpoints(program["id"])
              if row.get("kind") == KIND}
    made = []
    for key, hit in hits.items():
        need = RED_STEPS if hit["source"] == "red" else FINDING_STEPS
        if key in raised or len(hit["steps"]) < need:
            continue
        hit["steps"].sort()
        hit["title"] = title_of(hit)
        hit["requirement"] = requirement_of(hit)
        step = next(row for row in steps if int(row["ordinal"]) == hit["steps"][-1])
        service.store.add_checkpoint(step_id=step["id"], program_id=program["id"], at=service._clock(), by="engine",
                                     line=hit["title"][:400], kind=KIND, undo=dict(hit))
        made.append(hit)
    return made


def title_of(hit: Mapping[str, Any]) -> str:
    count = len(hit["steps"])
    if hit["source"] == "red":
        return f"Lesson · the check is red with “{hit['words']}”: {count} steps red for it"
    return f"Lesson · “{hit['words']}” on {count} steps"


def requirement_of(hit: Mapping[str, Any]) -> str:
    if hit["source"] == "red":
        return f"The check is not red with “{hit['words']}”"[:400]
    return f"The change does not repeat this finding: {hit['words']}"[:400]


def turn_items(program: Mapping[str, Any], checkpoints: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """One Your turn row per open lesson (no choice yet)."""
    items = []
    for row in checkpoints:
        if row.get("kind") != KIND or row.get("choice"):
            continue
        hit = row.get("undo") or {}
        items.append({
            "id": f"{program['id']}:lesson:{row['id']}", "kind": KIND, "program_id": program["id"],
            "program_title": program["title"], "step_id": row.get("step_id") or "", "ordinal": (hit.get("steps") or [0])[-1],
            "step_title": "", "launch_id": None, "since": row.get("at"), "project_id": program.get("project_id"),
            "for_person_id": program.get("for_person_id"), "pr": None, "title": hit.get("title") or row.get("line"),
            "choices": list(CHOICES), "lesson_id": int(row["id"]), "source": hit.get("source"),
            "words": hit.get("words"), "steps": list(hit.get("steps") or []), "requirement": hit.get("requirement"),
        })
    return items


#: The repository file a kept lesson edits (JRN12).
REPO_FILE = ".holdspeak/program.json"


def decide(service: Any, principal: Any, program: dict[str, Any], lesson_id: Any, choice: str) -> dict[str, Any]:
    """His press on a Lesson row: Keep for this program (an every-step Review
    requirement), Keep for HoldSpeak (a tiny step that edits the repository
    file), or Skip (the cause is not proposed again here)."""
    from .program_service import ProgramRefused

    row = next((item for item in service.store.list_checkpoints(program["id"])
                if item.get("kind") == KIND and str(item["id"]) == str(lesson_id)), None)
    if row is None:
        raise ProgramRefused("lesson_unknown", "There is no such lesson on this program.", status=404)
    if row.get("choice"):
        raise ProgramRefused("not_waiting", "Nothing waits on you there now.")
    hit = dict(row.get("undo") or {})
    answer: dict[str, Any] = {}
    if choice == "keep_program":
        made = service.require(principal, program["id"], text=hit["requirement"], kind="review", each_step=True)
        answer["requirement_id"] = made.get("requirement_id")
        line = f"Lesson kept for this program: {hit['requirement']}"
    elif choice == "keep_repo":
        step = keep_step(service, program, row, hit)
        answer["step_id"] = step["id"]
        line = f"Lesson kept for {_repo_name(program)}: step {step['ordinal']} edits {REPO_FILE}"
    else:
        line = f"Lesson skipped: {hit.get('words')}"
    hit["decided"] = choice
    service.store.decide_checkpoint(int(row["id"]), choice, hit)
    service._checkpoint(program, None, "owner", line[:400])
    service.changed(program["id"], verb="lesson")
    return answer


def _repo_name(program: Mapping[str, Any]) -> str:
    from pathlib import Path

    return Path(str(program.get("repo_root") or "")).name or "the repository"


def keep_step(service: Any, program: dict[str, Any], row: Mapping[str, Any], hit: Mapping[str, Any]) -> dict[str, Any]:
    """JRN12: a tiny step of this Program whose diff is one JSON change: one
    ``requirements`` item in ``.holdspeak/program.json``. It has no ``after``
    and the gates of any step (check, review, merge by the level)."""
    from .program_service import _new_id, triage_effort

    item = {"text": hit["requirement"], "kind": "review", "each_step": True, "required": True}
    brief = (f"Keep a lesson for the repository. Edit `{REPO_FILE}` (make it, with `{{}}`, if it is not there): "
             f"add this object to its `requirements` list (make the list if it is not there):\n\n"
             f"{json.dumps(item, ensure_ascii=False)}\n\nKeep every other key and item as it is. Change no other file.")
    steps = service.store.list_steps(program["id"])
    source = next((step for step in steps if step["id"] == row.get("step_id")), steps[0] if steps else {})
    now = service._clock()
    step = {
        "id": _new_id("step"), "program_id": program["id"],
        "ordinal": max((int(step["ordinal"]) for step in steps), default=0) + 1,
        "title": f"Keep the lesson: {hit.get('words')}"[:120], "brief_markdown": brief, "owns": [REPO_FILE],
        "after": [], "profile": source.get("profile"), "engine": source.get("engine"),
        "prefer_idle": bool(source.get("prefer_idle")), "effort": triage_effort(brief, [REPO_FILE]), "race": 0,
        "race_of": None, "gate_check": True, "gate_review": source.get("gate_review") or "none",
        "review_depth": source.get("review_depth") or "delta", "gate_merge": "level", "state": "planned",
        "held_reason": None, "launch_id": None, "worktree": None, "branch": None, "head_commit": None,
        "checked_commit": None, "pr_url": None, "pr_number": None, "check_log": None, "check_verdict": None,
        "facts": {"lesson_id": int(row["id"]), "from_lesson": True}, "review_verdict": None, "findings": [],
        "report": None, "rounds": 0, "parked_reason": None, "parked_by": None, "origin_ref": f"lesson:{row['id']}",
        "for_person_id": source.get("for_person_id"), "started_at": None, "ended_at": None, "updated_at": now,
    }
    service.store.save_step(step)
    service._copy_parents(program, [step])
    if program.get("closed_at"):
        program["closed_at"] = None  # a closed Program runs its lesson step
    if program.get("state") in ("done",):
        program["state"] = "running"
    service._touch(program)
    return step
