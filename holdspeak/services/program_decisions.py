"""PG16: decisions from a Program (design §9b, "What drives it").

A finding resolved **Skip** (by his press or by the rules) and a merge the
engine made **by rule** each become one *proposed* decision record: a Desk
decision in status ``proposed`` with its canonical record
(``DecisionRecordService.create_from_desk``), the reason, the rule and the
level in its context, linked to the Program and to the step's PR
(``link_work``), and filed to the Program's Project. He accepts it in the
Decisions window (no auto-confirm in this slice).

One record per checkpoint: the Desk decision id is derived from the step and
the finding (or the merge), so a second resolve updates the same record. An
accepted record keeps its words. An overturned Skip withdraws its record.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Optional

from ..logging_config import get_logger
from .program_rules import level_word

log = get_logger("program_decisions")

#: The work type of the Program on a record (``decision_record_work``); a PR
#: is ``pr`` with its URL, as follow-through links it.
WORK_PROGRAM = "program"
WORK_PR = "pr"


def _desk_id(kind: str, step_id: str, finding_id: Optional[str] = None) -> str:
    tail = f"-{finding_id}" if finding_id else ""
    return f"program-{kind}-{step_id}{tail}"


def _principal() -> Any:
    from ..principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "program-engine")


def _records(db: Any) -> Any:
    from .decision_record_service import DecisionRecordService

    return DecisionRecordService(db)


def _announce(record_id: str) -> None:
    try:
        from ..runtime import composition

        composition.notify_desk_changed("decision_record", record_id, "propose")
    except Exception:
        pass


def propose(
    db: Any, store: Any, program: Mapping[str, Any], step: Mapping[str, Any], *, kind: str,
    title: str, decision: str, reason: Optional[str], rule: Optional[str], by: str,
    finding_id: Optional[str] = None, now: str,
) -> Optional[str]:
    """Write (or update) the proposed record of one Skip or one merge by
    rule. Returns the record id; ``None`` when the record could not be
    written (the Program goes on: a record is never a gate)."""
    try:
        return _propose(db, store, program, step, kind=kind, title=title, decision=decision, reason=reason,
                        rule=rule, by=by, finding_id=finding_id, now=now)
    except Exception as exc:
        log.warning(f"program decision not proposed: {exc}")
        return None


def _propose(
    db: Any, store: Any, program: Mapping[str, Any], step: Mapping[str, Any], *, kind: str,
    title: str, decision: str, reason: Optional[str], rule: Optional[str], by: str,
    finding_id: Optional[str], now: str,
) -> str:
    desk_id = _desk_id(kind, str(step["id"]), finding_id)
    existing = db.desk_decisions.get(desk_id, include_deleted=True)
    records = _records(db)
    principal = _principal()
    context = "\n".join(line for line in (
        f"Reason: {reason}" if reason else "",
        f"Rule: {rule}" if rule else "",
        f"Control: {level_word(program.get('control'))}",
        f"Decided by: {'you' if by == 'owner' else 'the engine'}",
        f"Program: {program.get('title')}, step {step.get('ordinal')}",
    ) if line)
    project_id = str(program.get("project_id") or "")
    tags = [f"program:{program['id']}"] + ([f"project:{project_id}"] if project_id else [])
    kept = existing is not None and not existing.deleted and existing.status != "proposed"
    if not kept:
        db.desk_decisions.upsert(
            decision_id=desk_id, title=title[:200], status="proposed", context_markdown=context,
            decision_markdown=decision, tags=tags,
            created_at=existing.created_at if existing is not None else None,
        )
    record = records.create_from_desk(principal, desk_id)
    record_id = str(record["id"])
    if not kept:
        with db._connection() as conn:
            conn.execute("UPDATE decision_records SET deleted=0 WHERE id=? AND deleted=1", (record_id,))
        changes = {field: value for field, value in (("decision_text", decision), ("rationale", context))
                   if record.get(field) != value}
        if changes and record.get("lifecycle") == "active":
            records.update_record(principal, record_id, changes)
    records.link_work(principal, record_id, WORK_PROGRAM, str(program["id"]))
    if step.get("pr_url"):
        records.link_work(principal, record_id, WORK_PR, str(step["pr_url"]))
    if project_id:
        store.file_to_project(project_id, f"decision_record:{record_id}", now)
    _announce(record_id)
    return record_id


def link_pr(db: Any, step: Mapping[str, Any]) -> None:
    """The step's PR opened: the step's proposed records govern it too."""
    url = str(step.get("pr_url") or "")
    ids = [str(rid) for rid in (step.get("facts") or {}).get("decision_records") or [] if rid]
    if not url or not ids:
        return
    records = _records(db)
    for record_id in ids:
        try:
            records.link_work(_principal(), record_id, WORK_PR, url)
            _announce(record_id)
        except Exception as exc:
            log.info(f"program decision not linked to the PR: {exc}")


def withdraw(db: Any, record_id: Optional[str]) -> None:
    """An overturned Skip: its proposed record goes (an accepted one stays)."""
    if not record_id:
        return
    try:
        with db._connection() as conn:
            row = conn.execute(
                "SELECT r.source_id FROM decision_records r JOIN desk_decisions dd ON dd.id = r.source_id "
                "WHERE r.id=? AND r.source_type='desk' AND LOWER(dd.status)='proposed'", (record_id,),
            ).fetchone()
            if row is None:
                return
            conn.execute("UPDATE decision_records SET deleted=1 WHERE id=?", (record_id,))
        db.desk_decisions.delete(str(row["source_id"]))
        _announce(str(record_id))
    except Exception as exc:
        log.info(f"program decision not withdrawn: {exc}")


_PR_NUMBER = re.compile(r"/pull/(\d+)/?$")


def room_proposed(db: Any, project_id: str) -> list[dict[str, Any]]:
    """The Room's proposed decisions from Programs: filed to the Project,
    still proposed, each with its Program and its PR."""
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT r.id, r.created_at, dd.title, r.decision_text
               FROM decision_records r
               JOIN desk_decisions dd ON r.source_type = 'desk' AND dd.id = r.source_id
               WHERE r.deleted = 0 AND dd.deleted = 0 AND LOWER(dd.status) = 'proposed'
                 AND EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id = ? AND pr.deleted = 0
                             AND pr.resource_ref = 'decision_record:' || r.id)
                 AND EXISTS (SELECT 1 FROM decision_record_work w WHERE w.record_id = r.id
                             AND w.work_type = ?)
               ORDER BY r.created_at DESC, r.id DESC""",
            (project_id, WORK_PROGRAM),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            work = conn.execute(
                "SELECT work_type, work_ref FROM decision_record_work WHERE record_id=? ORDER BY created_at, id",
                (row["id"],),
            ).fetchall()
            program_id = next((w["work_ref"] for w in work if w["work_type"] == WORK_PROGRAM), "")
            program = conn.execute("SELECT title FROM programs WHERE id=?", (program_id,)).fetchone()
            prs = []
            for w in work:
                if w["work_type"] != WORK_PR:
                    continue
                match = _PR_NUMBER.search(str(w["work_ref"]))
                prs.append({"number": int(match.group(1)) if match else None, "url": w["work_ref"]})
            out.append({
                "id": row["id"], "text": str(row["title"] or row["decision_text"] or ""),
                "at": row["created_at"], "status": "proposed",
                "source_ref": f"decision_record:{row['id']}",
                "program": {"id": program_id, "title": str(program["title"]) if program else ""},
                "prs": prs,
            })
    return out
