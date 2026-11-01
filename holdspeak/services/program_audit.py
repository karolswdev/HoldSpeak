"""Audit programs: a reviewer-only Program (PG-JOURNEYS J7; PG-LANG §13b JRN8 to JRN10).

PROGRAM-JOURNEYS-2026-10-31.md "J7 · A reviewer-only program". All defaults
are approved.

- **JRN8, the Audit template** (``program_templates.AUDIT``): every step is an
  audit, not a build. Its agent reads its surface (windows of the desk, the
  routes of a diff) and reports findings, one line each: ``MUST: <what> ·
  <evidence>``, ``SHOULD: …`` or ``NOTE: …``. It never commits: ``merge
  none``, no check, no reviewer, and the gate refuses its writes by rule
  (``operation_policy``, ``audit_step``). A commit on an audit step is a core
  question ("an audit changes nothing"). An audit step is done on its report
  (``program.step_done``, else its last words at its turn's end).
- **JRN9, findings filed as Door tasks** (``door.add_item``), the Program and
  the step as their origin, the severity in his words ("Must fix", "Should
  fix", "Noted"). One finding is one task across steps: the same text again
  adds its step to the finding, not a second task. By level: YOLO files all;
  Normal files MUST and SHOULD and keeps a NOTE in the Program; Secure files
  none by rule: one Your turn row "File the audit's findings" (File · Skip).
  The Program's wire carries ``findings_board``.
- **JRN10, a fix program from the MUST findings**: when every audit step has
  reported, a Your turn row "Make a fix program from the 3 MUST" (Make ·
  Skip) at every level; Make (or ``program.propose_fix``) makes a Program in
  Drafting, one step per MUST with a Review requirement that the finding is
  fixed, linked to the audit (``origin_ref program:<id>``). It is never
  started by rule.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_audit")

AUDIT = "audit"
LEVELS = ("MUST", "SHOULD", "NOTE")
LEVEL_WORDS = {"MUST": "Must fix", "SHOULD": "Should fix", "NOTE": "Noted"}
_FINDING = re.compile(r"^\s*(?:[-*]\s*)?(MUST|SHOULD|NOTE)\b\s*[:\-—]?\s*(.+?)\s*$", re.I)
_NONE = re.compile(r"^(?:no|none|zero)(?:\s+findings?)?\.?$", re.I)
_NO_FINDINGS = re.compile(r"\b(?:no|none|zero)\s+findings?\b", re.I)
#: The audit step's rules in its brief (``program_brief.acceptance``).
RULES = (
    "This is an audit. Read and run tests only, in this copy. Change nothing and commit nothing: HoldSpeak "
    "refuses every write.",
    "Report each finding on its own line: `MUST: <what is wrong> · <evidence>`, `SHOULD: …` or `NOTE: …`. "
    "The evidence is a file:line, a route or a screenshot path. MUST is a defect he must fix; SHOULD is worth "
    "fixing; NOTE is for the record.",
    "Name each window, route or file you read. If you find nothing, say `No findings`.",
    "When you are done, call program.step_done with that report. Then end your turn.",
    "If a question blocks you, ask it and wait. Do not guess.",
)
ASK_REPORT = ("HoldSpeak: report your findings, one per line (`MUST: … · evidence`, `SHOULD: …`, `NOTE: …`), "
              "or `No findings`, with program.step_done. Then end your turn.")


def is_audit(program: Mapping[str, Any]) -> bool:
    return str(program.get("template") or "") == AUDIT


def parse(report: Any) -> list[dict[str, str]]:
    """The findings of an audit report: ``[{level, text, evidence, key}]``."""
    out: list[dict[str, str]] = []
    for line in str(report or "").splitlines():
        match = _FINDING.match(line)
        if not match:
            continue
        body = match.group(2).strip()
        if _NONE.match(body):
            continue
        text, _sep, evidence = body.partition(" · ")
        text = " ".join(text.split()).rstrip(".")
        if not text:
            continue
        out.append({"level": match.group(1).upper(), "text": text[:300], "evidence": " ".join(evidence.split())[:300],
                    "key": key_of(text)})
    return out


def key_of(text: str) -> str:
    """One finding across steps: its words without case, spaces or end marks."""
    plain = re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()[:16]


# ── the board ────────────────────────────────────────────────────────

def board(steps: list[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """``findings_board``: every finding of the audit once, with the steps
    that found it, its level words and its Door task."""
    rows: dict[str, dict[str, Any]] = {}
    for step in steps:
        for finding in (step.get("facts") or {}).get("audit_findings") or []:
            row = rows.setdefault(finding["key"], {
                "key": finding["key"], "level": finding["level"], "words": LEVEL_WORDS[finding["level"]],
                "text": finding["text"], "evidence": [], "steps": [], "task_id": None, "filed": False})
            if step["ordinal"] not in row["steps"]:
                row["steps"].append(step["ordinal"])
            if finding.get("evidence") and finding["evidence"] not in row["evidence"]:
                row["evidence"].append(finding["evidence"])
            if finding.get("task_id"):
                row["task_id"], row["filed"] = finding["task_id"], True
            if LEVELS.index(finding["level"]) < LEVELS.index(row["level"]):
                row["level"], row["words"] = finding["level"], LEVEL_WORDS[finding["level"]]
    if not rows and not any((step.get("facts") or {}).get("audit_reported") for step in steps):
        return None
    ordered = sorted(rows.values(), key=lambda row: (LEVELS.index(row["level"]), row["steps"][0]))
    must = sum(1 for row in ordered if row["level"] == "MUST")
    head = (f"{len(ordered)} finding{'s' if len(ordered) != 1 else ''}" + (f" · {must} MUST" if must else "")
            if ordered else "No findings")
    return {"head": head, "total": len(ordered), "must": must,
            "should": sum(1 for row in ordered if row["level"] == "SHOULD"),
            "note": sum(1 for row in ordered if row["level"] == "NOTE"), "rows": ordered}


# ── the engine: an audit step's turn ─────────────────────────────────

def follow(runner: Any, program: dict[str, Any], step: dict[str, Any]) -> None:
    """The audit step's move this tick (``ProgramRunner._follow`` hands every
    audit step here; the build's commit rules never run on an audit)."""
    from .program_runner import _STOPPED, _TURN_END, PARKED_BY_ENGINE

    service = runner.service
    facts = dict(step.get("facts") or {})
    if facts.get("audit_reported"):
        return
    worktree = str(step.get("worktree") or "")
    head = runner._git(worktree, "rev-parse", "HEAD") if worktree else ""
    base = facts.get("base_commit") or step.get("head_commit")
    if head and base and head != base and "audit_commit" not in set(facts.get("core_cleared") or []):
        if not isinstance(facts.get("core"), Mapping):
            runner.raise_core(program, step, "audit_commit", "an audit step made a commit; an audit changes nothing")
        return
    flight = runner.flight(str(step.get("launch_id") or ""))
    state = str(flight.get("state") or "")
    report = str(step.get("report") or "") if facts.get("said_done") else ""
    if not report and state in _TURN_END:
        turn = str(flight.get("turn_id") or "")
        if turn and turn == str(facts.get("last_turn") or ""):
            return  # the turn the engine read already (it asked after it)
        words = runner.review_words(str(step.get("launch_id") or ""))
        facts["last_turn"] = turn or None
        if parse(words) or _NO_FINDINGS.search(words):
            report = words
        elif facts.get("audit_asked"):
            service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE, facts=facts,
                               parked_reason="The audit ended twice with no report",
                               line="The audit ended twice with no report", ending="interrupted")
            return
        else:
            facts["audit_asked"] = True
            step["facts"] = facts
            service.save_step(step)
            try:
                runner.prompt_builder(step, ASK_REPORT)
                service._checkpoint(program, step, "engine", "The audit ended with no report; asked for its findings")
            except Exception as exc:
                log.info(f"audit report ask not typed: {exc}")
                service._checkpoint(program, step, "engine", "The audit ended with no report; the engine could not "
                                    "ask for it. It waits for program.step_done")
            return
    if not report:
        if state in _STOPPED:
            service.transition(program, step, "parked", parked_by=PARKED_BY_ENGINE,
                               parked_reason="The agent stopped before the audit reported",
                               line=f"The agent stopped ({state})", ending="interrupted")
        elif state == "waiting" and step["state"] != "waiting":
            service.transition(program, step, "waiting", line="The agent asks a question")
        elif state in ("working", "resuming", "no_signal") and step["state"] != "working":
            service.transition(program, step, "working")
        return
    found = parse(report)
    step["report"] = report
    file_findings(service, program, step, found)
    facts.update(audit_reported=True, audit_findings=found)
    facts.pop("said_done", None)
    must = sum(1 for row in found if row["level"] == "MUST")
    line = (f"Audited · {len(found)} finding{'s' if len(found) != 1 else ''}" + (f" · {must} MUST" if must else "")
            if found else "Audited · no findings")
    if step["state"] != "checking":
        service.transition(program, step, "checking", facts=facts)
    service.transition(program, step, "done", facts=facts, line=line, detail=report[:4000])


def file_findings(service: Any, program: Mapping[str, Any], step: Mapping[str, Any],
                  found: list[dict[str, Any]]) -> None:
    """JRN9: each finding as a Door task by the Program's level (one task
    for one finding across steps); Secure files none by rule."""
    from .program_rules import level_of

    level = level_of(program.get("control"))
    filed = _filed(service, program)
    for finding in found:
        if finding["key"] in filed:
            finding["task_id"] = filed[finding["key"]]  # the same finding again: its step joins the task
            continue
        if level == "secure" or (level == "normal" and finding["level"] == "NOTE"):
            continue
        task_id = _door_task(service, program, step, finding)
        if task_id:
            finding["task_id"] = task_id
            filed[finding["key"]] = task_id


def _filed(service: Any, program: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for step in service.store.list_steps(program["id"]):
        for finding in (step.get("facts") or {}).get("audit_findings") or []:
            if finding.get("task_id"):
                out.setdefault(finding["key"], finding["task_id"])
    return out


def _door_task(service: Any, program: Mapping[str, Any], step: Mapping[str, Any], finding: Mapping[str, Any]) -> str:
    try:
        from ..principals import Principal, PrincipalKind
        from .door_service import DoorService
        from .follow_through_service import FollowThroughService

        door = DoorService(FollowThroughService(service.db), None, None, None, db=service.db)  # type: ignore[arg-type]
        evidence = f" ({finding['evidence']})" if finding.get("evidence") else ""
        task = f"{LEVEL_WORDS[finding['level']]}: {finding['text']}{evidence}"[:300]
        item = door.add_item(Principal(PrincipalKind.OWNER, "program-engine"), task, owner="me", due=None,
                             source_type="program_step",
                             source_ref=f"program_step:{step['id']}:finding:{finding['key']}")
        ident = str((item or {}).get("id") or "")
        if ident and program.get("project_id"):
            service.store.file_to_project(str(program["project_id"]), f"action:{ident}", service._clock())
        return ident
    except Exception as exc:
        log.warning(f"audit finding not filed: {exc}")
        return ""


# ── the Your turn rows and their presses ─────────────────────────

#: The ledger row that keeps the audit's own presses (``undo`` holds them).
MARK_KIND = "audit"


def marks_of(checkpoints: list[Mapping[str, Any]]) -> dict[str, Any]:
    """The audit's presses so far (``file_decided``, ``fix_decided``,
    ``fix_program_id``): the newest ``audit`` ledger row."""
    row = next((row for row in checkpoints if row.get("kind") == MARK_KIND), None)
    return dict((row or {}).get("undo") or {})


def turn_items(program: Mapping[str, Any], steps: list[Mapping[str, Any]],
               checkpoints: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Secure's File · Skip row (findings not filed) and the fix program's
    Make · Skip row (every step reported, some MUST, none made yet). Each
    row carries the last reported step, so the step's decide route takes it."""
    from .program_rules import level_of

    if not is_audit(program):
        return []
    top = [step for step in steps if not step.get("race_of")]
    reported = [step for step in top if (step.get("facts") or {}).get("audit_reported")]
    if not reported:
        return []
    rows = (board(top) or {}).get("rows") or []
    marks = marks_of(checkpoints)
    last = max(reported, key=lambda step: int(step["ordinal"]))
    base = {"program_id": program["id"], "program_title": program["title"], "step_id": last["id"],
            "ordinal": last["ordinal"], "step_title": last["title"], "launch_id": None,
            "since": last.get("ended_at") or program.get("updated_at"), "project_id": program.get("project_id"),
            "for_person_id": program.get("for_person_id"), "pr": None}
    items = []
    unfiled = [row for row in rows if not row["filed"]]
    if unfiled and level_of(program.get("control")) == "secure" and not marks.get("file_decided"):
        items.append({**base, "id": f"{program['id']}:audit_file", "kind": "audit_file", "choices": ["file", "skip"],
                      "count": len(unfiled),
                      "title": f"{_count(len(unfiled), 'finding')} to file as Door tasks"})
    must = [row for row in rows if row["level"] == "MUST"]
    finished = all((step.get("facts") or {}).get("audit_reported") or step.get("state") in ("done", "parked")
                   for step in top)
    if must and finished and not marks.get("fix_decided"):
        items.append({**base, "id": f"{program['id']}:fix_program", "kind": "fix_program", "choices": ["make", "skip"],
                      "count": len(must),
                      "title": f"A fix program from {_count(len(must), 'MUST finding')}"})
    return items


def _count(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def decide(service: Any, principal: Any, program: dict[str, Any], kind: str, choice: str) -> dict[str, Any]:
    """His press on ``audit_file`` (file · skip) or ``fix_program`` (make · skip)."""
    from .program_service import ProgramRefused

    marks = marks_of(service.store.list_checkpoints(program["id"]))
    if kind == "audit_file":
        if marks.get("file_decided"):
            raise ProgramRefused("not_waiting", "Nothing waits on you there now.")
        filed = file_all(service, program) if choice == "file" else 0
        marks["file_decided"] = choice
        save_marks(service, program, marks, f"Filed {_count(filed, 'finding')} as Door tasks" if choice == "file"
                   else "Kept the findings in the program; none filed")
        return {"filed": filed}
    if marks.get("fix_decided"):
        raise ProgramRefused("not_waiting", "Nothing waits on you there now.")
    if choice == "skip":
        marks["fix_decided"] = "skip"
        save_marks(service, program, marks, "No fix program")
        return {}
    return propose_fix(service, principal, program["id"])


def file_all(service: Any, program: Mapping[str, Any]) -> int:
    """File every finding not filed yet (his File on Secure's row)."""
    filed = 0
    known = _filed(service, program)
    for step in service.store.list_steps(program["id"]):
        facts = dict(step.get("facts") or {})
        found = [dict(row) for row in facts.get("audit_findings") or []]
        if not found:
            continue
        for finding in found:
            if finding.get("task_id"):
                continue
            if finding["key"] in known:
                finding["task_id"] = known[finding["key"]]
                continue
            ident = _door_task(service, program, step, finding)
            if ident:
                finding["task_id"], known[finding["key"]] = ident, ident
                filed += 1
        facts["audit_findings"] = found
        step["facts"] = facts
        service.save_step(step)
    return filed


def propose_fix(service: Any, principal: Any, program_id: str) -> dict[str, Any]:
    """JRN10 (``program.propose_fix``): a Program in Drafting, one step per
    MUST finding, each with a Review requirement that it is fixed, linked to
    the audit (``origin_ref program:<audit id>``). It is never started here:
    his Start (or an orchestrating agent's, on a Program it made) starts it."""
    from .program_service import ProgramRefused, _is_owner

    program = service._program(program_id)
    if not is_audit(program):
        raise ProgramRefused("not_an_audit", "Only an audit program makes a fix program.")
    marks = marks_of(service.store.list_checkpoints(program_id))
    if marks.get("fix_program_id"):
        raise ProgramRefused("fix_made", "The fix program is made already.", fix_program_id=marks["fix_program_id"])
    rows = [row for row in (board(service.store.list_steps(program_id)) or {}).get("rows") or []
            if row["level"] == "MUST"]
    if not rows:
        raise ProgramRefused("no_must_findings", "The audit has no MUST finding to fix.")
    made = service.create(principal, title=f"Fix: {program['title']}"[:120],
                          goal=f"Fix the {_count(len(rows), 'MUST finding')} of the audit “{program['title']}”.",
                          repository=program.get("repo_root") or None, project_id=program.get("project_id"),
                          base_branch=program.get("base_branch") or None, control=program.get("control"),
                          check_command=program.get("check_command") or None, template="fast-cycle",
                          origin_ref=f"program:{program_id}", for_person_id=program.get("for_person_id"))
    steps = []
    for row in rows:
        evidence = f" Evidence: {'; '.join(row['evidence'])}." if row["evidence"] else ""
        steps.append({"title": row["text"][:120], "brief": f"Fix this audit finding: {row['text']}.{evidence}",
                      "origin_ref": f"action:{row['task_id']}" if row.get("task_id") else None})
    service.plan(principal, made["id"], steps=steps)
    planned = sorted(service.store.list_steps(made["id"]), key=lambda step: int(step["ordinal"]))
    for step, row in zip(planned, rows):
        service.require(principal, made["id"], text=f"{row['text']} is fixed"[:400], kind="review", step_id=step["id"])
    marks.update(fix_decided="make", fix_program_id=made["id"])
    save_marks(service, program, marks, f"Made the fix program “{made['title']}”: "
               f"{_count(len(rows), 'step')}, Drafting", by="owner" if _is_owner(principal) else "agent")
    return {"fix_program_id": made["id"], "steps": len(rows), "fix_program": service.get(principal, made["id"])}


def save_marks(service: Any, program: Mapping[str, Any], marks: Mapping[str, Any], line: str, *,
               by: str = "owner") -> None:
    service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by=by,
                                 line=line[:400], kind=MARK_KIND, undo=dict(marks))
    service.changed(program["id"], verb="audit")


__all__ = ["AUDIT", "ASK_REPORT", "LEVEL_WORDS", "MARK_KIND", "RULES", "board", "decide", "file_all",
           "file_findings", "follow", "is_audit", "key_of", "marks_of", "parse", "propose_fix", "turn_items"]
