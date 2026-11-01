"""Delivery at Done (PG-LANG LANG13, 2026-11-01).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §8 (dw at
two points only; §15.9 approved). A Program whose ``delivery`` is
``dw <project>/<phase>[/<story>]`` writes ONE delivery when it closes, never
in his working tree:

1. a scratch worktree at the base head on ``program/<slug>/delivery``
   (``hs-program-<id>-delivery`` beside the repository);
2. the repository's own Delivery Workbench (``.githooks/dw``, the argv base
   of ``missioncontrol_bridge.dw_argv_base``): ``dw story create`` when the
   ref names no story, then ``dw story evidence --from-file`` with the
   Program's Done (§8.3) and ``dw story status … done``;
3. one commit, one push, one PR "Delivery: <title> done", merged by the
   Program's merge rule (Normal and YOLO merge it; at Secure it is his row).

Each outcome is one ledger line ``kind = delivery``: "Delivered to dw
app/1/01 (PR #12)"; at Secure "The delivery PR #12 waits for your merge";
a failure "Could not deliver to dw app/1: <words>" (git's or dw's own words
stay in the checkpoint's ``undo.detail``, never in the line), and his Your
turn row ``delivery`` (Retry or Skip; Merge or Skip at Secure). What dw never
sees (§8.4): steps beyond their PR numbers, briefs, checkpoints, findings,
transcripts, worktree paths. The link point (reading ``dw context`` at
create) and a milestone's ``dw phase close`` are not built yet.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from ..logging_config import get_logger
from ..timestamps import local_now

log = get_logger("program_delivery")

KIND = "delivery"
#: The ledger choices of a delivery line.
DELIVERED, PR_OPEN, FAILED, SKIPPED = "delivered", "pr_open", "failed", "skipped"
CHOICES_FAILED = ("retry", "skip")
CHOICES_MERGE = ("merge", "skip")
_STORY = re.compile(r"story-(\d+)-[^/]*\.md\s*$")


class DeliveryFailed(Exception):
    """One stage of the delivery failed: ``words`` for him, ``detail`` raw."""

    def __init__(self, words: str, detail: str = "") -> None:
        super().__init__(words)
        self.words, self.detail = words, detail


def target(program: Mapping[str, Any]) -> Optional[dict[str, str]]:
    """``{project, phase, story?, words}`` of ``delivery_ref``
    (``dw:app/1/01``), else ``None``."""
    ref = str(program.get("delivery_ref") or "")
    if not ref.startswith("dw:"):
        return None
    parts = [part for part in ref[3:].split("/") if part]
    if len(parts) not in (2, 3):
        return None
    out = {"project": parts[0], "phase": parts[1], "story": parts[2] if len(parts) == 3 else "",
           "words": "dw " + "/".join(parts)}
    return out


def last_line(service: Any, program_id: str) -> Optional[dict[str, Any]]:
    """The Program's newest delivery line (the ledger is the record)."""
    for row in service.store.list_checkpoints(program_id):
        if row.get("kind") == KIND:
            return row
    return None


def pending(service: Any, program: Mapping[str, Any]) -> bool:
    """The Program closed with a delivery that no line answered yet."""
    return bool(program.get("closed_at")) and target(program) is not None and last_line(service, program["id"]) is None


def evidence(service: Any, program: Mapping[str, Any]) -> str:
    """§8.3: the Program's Done, nothing more (PR numbers, the requirements'
    count and lines, the Decided-for-you counts, the handover note)."""
    from .program_requirements import counts, label

    steps = [step for step in service.store.list_steps(program["id"]) if not step.get("race_of")]
    prs = sorted({int(step["pr_number"]) for step in steps if step.get("pr_number")})
    day = local_now().strftime("%Y-%m-%d")
    lines = [f"## Program: {program['title']} — Done {day}"]
    lines.append("- PRs: " + (", ".join(f"#{n}" for n in prs) if prs else "none"))
    reqs = service.requirements(program["id"])
    met = counts(reqs)
    if met:
        waived = f" ({met['waived']} waived)" if met.get("waived") else ""
        lines.append(f"- Requirements: {met['met']} of {met['total']} met{waived}")
        for row in reqs:
            if not row.get("required") or (not row.get("step_id") and row.get("each_step")):
                continue
            said = str((row.get("evidence") or {}).get("line") or row.get("state") or "")
            lines.append(f"  - {label(row['ordinal'])} {row.get('kind')} · {row.get('text')} · {said}"[:300])
    decided = service.decided_for_you(program["id"])
    if decided:
        merges = sum(1 for row in decided if row.get("kind") == "merge")
        later = sum(1 for row in decided if row.get("choice") == "later")
        overturned = sum(1 for row in decided if row.get("overturned_at"))
        lines.append(f"- Decided for you: {len(decided)} (merges {merges}, Later {later}); overturned {overturned}")
    lines.append(f"- Handover note: {program.get('note_id') or 'program-' + program['id']}")
    return "\n".join(lines) + "\n"


def _words_of(stage: str, raw: str) -> str:
    from .brief_words import pr_failure_words

    if stage == "push":
        return pr_failure_words(f"git push failed: {raw}") or "could not push the delivery branch"
    return {
        "rails": "the repository has no Delivery Workbench",
        "worktree": "HoldSpeak could not make the delivery worktree",
        "create": "Delivery Workbench did not create the story",
        "evidence": "Delivery Workbench did not take the evidence",
        "status": "Delivery Workbench did not mark the story done",
        "commit": "the delivery had nothing to commit",
        "pr": "could not open the delivery PR on GitHub",
        "merge": "GitHub did not merge the delivery PR",
    }.get(stage, "the delivery stopped")


def deliver(runner: Any, program: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """Write the delivery of a closed Program once; the ledger line written,
    or ``None`` when there is nothing to deliver."""
    service = runner.service
    where = target(program)
    if where is None or not program.get("closed_at"):
        return None
    try:
        number, branch = _write(runner, program, where)
    except DeliveryFailed as exc:
        return _line(service, program, FAILED, f"Could not deliver to {where['words']}: {exc.words}",
                     detail=exc.detail, words=exc.words)
    from .program_rules import level_of

    if level_of(program.get("control")) == "secure":
        return _line(service, program, PR_OPEN, f"The delivery PR #{number} to {where['words']} waits for your merge",
                     pr_number=number, branch=branch)
    return merge(runner, program, number, branch)


def merge(runner: Any, program: Mapping[str, Any], number: Any, branch: str = "", *, by: str = "engine") -> dict[str, Any]:
    """``gh pr merge --squash`` of the delivery PR; its ledger line."""
    service = runner.service
    where = target(program) or {"words": "the delivery"}
    cwd = str(program.get("repo_root") or "")
    proc = runner._run(["gh", "pr", "merge", str(number), "--squash"], cwd=cwd)
    if proc.returncode != 0:
        raw = " ".join(f"{proc.stderr or ''} {proc.stdout or ''}".split())
        return _line(service, program, FAILED, f"Could not deliver to {where['words']}: {_words_of('merge', raw)}",
                     detail=raw[:2000], words=_words_of("merge", raw), pr_number=number, branch=branch, by=by)
    return _line(service, program, DELIVERED, f"Delivered to {where['words']} (PR #{number})", pr_number=number,
                 branch=branch, by=by)


def _line(service: Any, program: Mapping[str, Any], choice: str, line: str, *, detail: str = "", words: str = "",
          pr_number: Any = None, branch: str = "", by: str = "engine") -> dict[str, Any]:
    undo: dict[str, Any] = {}
    if detail:
        undo["detail"] = str(detail)[:2000]
    if words:
        undo["words"] = words
    if pr_number:
        undo["pr_number"] = int(pr_number)
    if branch:
        undo["branch"] = branch
    operation_id = service._kernel_record(program, None, line) if by == "engine" else None
    ident = service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by=by,
                                         line=line, operation_id=operation_id, kind=KIND, choice=choice,
                                         undo=undo or None)
    return {"id": ident, "line": line, "choice": choice}


def _run_or_fail(runner: Any, argv: list[str], cwd: str, stage: str) -> str:
    try:
        proc = runner._run(argv, cwd=cwd)
    except Exception as exc:
        raise DeliveryFailed(_words_of(stage, str(exc)), str(exc)) from exc
    if proc.returncode != 0:
        raw = " ".join(f"{proc.stderr or ''} {proc.stdout or ''}".split())
        raise DeliveryFailed(_words_of(stage, raw), raw[:2000])
    return str(proc.stdout or "")


def _write(runner: Any, program: Mapping[str, Any], where: Mapping[str, str]) -> tuple[int, str]:
    from ..missioncontrol_bridge import dw_argv_base
    from .agent_hand_service import branch_slug

    root = str(program.get("repo_root") or "")
    base = str(program.get("base_branch") or "main")
    branch = f"program/{branch_slug(program['title'], 32) or 'program'}/delivery"
    path = Path(root).parent / f"hs-program-{program['id']}-delivery"
    runner._git(root, "fetch", "-q", "origin", base)
    ref = f"origin/{base}" if runner._git(root, "rev-parse", "--verify", "--quiet", f"origin/{base}") else base
    if path.is_dir():
        runner._git(root, "worktree", "remove", "--force", str(path))
    _run_or_fail(runner, ["git", "-C", root, "worktree", "add", "-q", "-B", branch, str(path), ref], root, "worktree")
    tree = str(path)
    dw = dw_argv_base(path)
    if dw is None or not (path / ".githooks" / "dw").exists():
        raise DeliveryFailed(_words_of("rails", ""), "no .githooks/dw at the base head")
    project, phase, story = where["project"], where["phase"], where.get("story") or ""
    if not story:
        out = _run_or_fail(runner, [*dw, "story", "create", project, phase, str(program["title"])[:120]], tree, "create")
        found = next((_STORY.search(line) for line in reversed(out.splitlines()) if _STORY.search(line)), None)
        if found is None:
            raise DeliveryFailed(_words_of("create", ""), out[-500:])
        story = found.group(1)
    scratch = tempfile.mkdtemp(prefix="hs-program-delivery-")
    evidence_file = Path(scratch) / "evidence.md"
    evidence_file.write_text(evidence(runner.service, program), encoding="utf-8")
    _run_or_fail(runner, [*dw, "story", "evidence", project, phase, story, "--from-file", str(evidence_file), "--force"],
                 tree, "evidence")
    _run_or_fail(runner, [*dw, "story", "status", project, phase, story, "done"], tree, "status")
    _run_or_fail(runner, ["git", "-C", tree, "add", "-A", "--", "pm/roadmap"], tree, "commit")
    title = f"Delivery: {program['title']} done"[:200]
    _run_or_fail(runner, ["git", "-C", tree, "commit", "-q", "-m", title], tree, "commit")
    _run_or_fail(runner, ["git", "-C", tree, "push", "-u", "origin", branch], tree, "push")
    body = (f"The delivery of the HoldSpeak program “{program['title']}” to {where['words']}/{story}.\n\n"
            + evidence(runner.service, program))
    out = _run_or_fail(runner, ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body],
                       tree, "pr")
    url = next((line.strip() for line in out.splitlines() if "/pull/" in line), "")
    found = re.search(r"/pull/(\d+)/?$", url)
    if found is None:
        raise DeliveryFailed(_words_of("pr", ""), out[-500:])
    return int(found.group(1)), branch


def turn_item(program: Mapping[str, Any], row: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """His Your turn row for a delivery that failed (Retry or Skip) or that
    waits for his merge at Secure (Merge or Skip); ``None`` otherwise."""
    if row is None or row.get("choice") not in (FAILED, PR_OPEN):
        return None
    undo = row.get("undo") or {}
    where = (target(program) or {}).get("words") or "the delivery"
    if row.get("choice") == FAILED:
        choices, title = CHOICES_FAILED, f"Deliver “{program['title']}” to {where}: it {undo.get('words') or 'stopped'}"
    else:
        choices, title = CHOICES_MERGE, f"Merge the delivery PR #{undo.get('pr_number')} of “{program['title']}”?"
    return {
        "program_id": program["id"], "program_title": program["title"], "step_id": "", "ordinal": 0,
        "step_title": "", "launch_id": None, "since": row.get("at"), "project_id": program.get("project_id"),
        "for_person_id": program.get("for_person_id"),
        "pr": {"number": undo.get("pr_number"), "url": None} if undo.get("pr_number") else None,
        "id": f"{program['id']}:delivery", "kind": KIND, "choices": list(choices), "title": title,
    }


def decide(runner: Any, program: Mapping[str, Any], choice: str) -> dict[str, Any]:
    """His press on the delivery row: Retry (write it again), Merge (the PR
    at Secure) or Skip (the Program stays Done, undelivered)."""
    service = runner.service
    row = last_line(service, program["id"])
    item = turn_item(program, row)
    if item is None:
        from .program_service import ProgramRefused

        raise ProgramRefused("no_delivery_waits", "No delivery waits for you.")
    if choice not in item["choices"]:
        from .program_service import ProgramRefused

        raise ProgramRefused("choice_invalid", f"The delivery takes {', '.join(item['choices'])}.", status=400)
    undo = (row or {}).get("undo") or {}
    if choice == "skip":
        return _line(service, program, SKIPPED, "Skipped the delivery", by="owner")
    if choice == "merge":
        return merge(runner, program, undo.get("pr_number"), str(undo.get("branch") or ""), by="owner")
    service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="owner",
                                 line="Retried the delivery")
    return deliver(runner, program) or {}


__all__ = ["DeliveryFailed", "KIND", "decide", "deliver", "evidence", "last_line", "merge", "pending", "target",
           "turn_item"]
