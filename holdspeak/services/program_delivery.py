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
transcripts, worktree paths. JRN5 (2026-11-01, ``program_dw``): the link
point reads ``dw context`` at create; a delivery to a whole phase (no story
in the ref) also runs ``dw phase close`` in the same commit, and its line
says "· phase closed" (dw's refusal keeps the phase open: "· the phase stays
open", ``undo.phase``).

HS-S32 (G32, the first branch; DECISIONS 2026-11-07): each new line carries
``undo.receipt``: the recorded target, the stage the delivery reached,
whether a remote write was attempted, and the acknowledged PR (canonical URL,
number, branch, base, prepared head). A known PR is continued, never made
again: **Check** reads it on GitHub (``gh pr view <url> --json``, read only);
an open match with no merge request offers **Merge** (a committed
``merge_requested_at`` line first, then ``gh pr merge <url> --squash
--match-head-commit <head>``, then a read); a merged match is Delivered.
**Retry** is offered only when the receipt shows the delivery stopped before
any push, create or merge. **Skip** ends the follow-up and calls nothing.
Every press names the line it answers (``expected_delivery_checkpoint_id``).
Not claimed: crash-safe dispatch, exactly-once delivery, a process lock.
"""
from __future__ import annotations

import json
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
#: HS-S32: the receipt's version, and what one read of the PR asks GitHub.
RECEIPT_V = 1
_READ_FIELDS = "url,number,state,headRefOid,baseRefName,headRefName,isCrossRepository"
_READ_MAX = 20000
_PR_URL = re.compile(r"^https://[^/\s]+/[^/\s]+/[^/\s]+/pull/(\d+)$")
#: Stages before any remote write (a Retry repeats nothing remote).
_LOCAL_STAGES = ("worktree", "rails", "create", "evidence", "status", "commit")
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
    phase: dict[str, Any] = {}
    track: dict[str, Any] = {"stage": "", "remote": False, "pr": {}}
    try:
        number, branch = _write(runner, program, where, phase, track)
    except DeliveryFailed as exc:
        return _line(service, program, FAILED, f"Could not deliver to {where['words']}: {exc.words}",
                     detail=exc.detail, words=exc.words, phase=phase, receipt=_receipt(program, where, track))
    from .program_rules import level_of

    receipt = _receipt(program, where, track)
    if level_of(program.get("control")) == "secure":
        return _line(service, program, PR_OPEN, f"The delivery PR #{number} to {where['words']} waits for your merge"
                     + _phase_words(phase, merged=False), pr_number=number, branch=branch, phase=phase,
                     receipt=receipt)
    return merge(runner, program, number, branch, phase=phase, receipt=receipt)


def _receipt(program: Mapping[str, Any], where: Mapping[str, str], track: Mapping[str, Any]) -> dict[str, Any]:
    """HS-S32: what the delivery reached, for a later Check, Merge or Retry."""
    return {"v": RECEIPT_V, "stage": str(track.get("stage") or ""), "remote": bool(track.get("remote")),
            "target": {"ref": str(program.get("delivery_ref") or ""), "words": str(where.get("words") or "")},
            "pr": {key: value for key, value in dict(track.get("pr") or {}).items() if value}}


def _phase_words(phase: Mapping[str, Any], *, merged: bool = True) -> str:
    """JRN5: what the delivery did to the phase, on its line."""
    if not phase:
        return ""
    if not phase.get("closed"):
        return " · the phase stays open"
    return " · phase closed" if merged else " · it closes the phase"


def merge(runner: Any, program: Mapping[str, Any], number: Any, branch: str = "", *, by: str = "engine",
          phase: Optional[Mapping[str, Any]] = None, receipt: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
    """The engine's ``gh pr merge --squash`` of a new delivery PR (Normal,
    YOLO); its ledger line. HS-S32: a merge that did not answer yes keeps the
    PR and a ``merge_requested_at`` marker (the PR is checked, never made or
    merged again by a press)."""
    service = runner.service
    where = target(program) or {"words": "the delivery"}
    cwd = str(program.get("repo_root") or "")
    receipt = {**dict(receipt or {}), "stage": "merge", "remote": True}
    try:
        proc = runner._run(["gh", "pr", "merge", str(number), "--squash"], cwd=cwd)
        code, raw = proc.returncode, " ".join(f"{proc.stderr or ''} {proc.stdout or ''}".split())
    except Exception as exc:  # a thrown transport is an unknown result, not a safe repeat
        code, raw = -1, str(exc)
    if code != 0:
        receipt.update(merge_requested_at=service._clock(), merge_requested_by=by)
        return _line(service, program, FAILED, f"Could not deliver to {where['words']}: {_words_of('merge', raw)}",
                     detail=raw[:2000], words=_words_of("merge", raw), pr_number=number, branch=branch, by=by,
                     phase=phase, receipt=receipt)
    return _line(service, program, DELIVERED, f"Delivered to {where['words']} (PR #{number})" + _phase_words(phase or {}),
                 pr_number=number, branch=branch, by=by, phase=phase, receipt=receipt)


def _line(service: Any, program: Mapping[str, Any], choice: str, line: str, *, detail: str = "", words: str = "",
          pr_number: Any = None, branch: str = "", by: str = "engine",
          phase: Optional[Mapping[str, Any]] = None, receipt: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
    undo: dict[str, Any] = {}
    if phase:
        undo["phase"] = dict(phase)  # JRN5: the phase close the delivery carried
    if detail:
        undo["detail"] = str(detail)[:2000]
    if words:
        undo["words"] = words
    if pr_number:
        undo["pr_number"] = int(pr_number)
    if branch:
        undo["branch"] = branch
    if receipt:
        undo["receipt"] = dict(receipt)  # HS-S32: additive; old readers keep pr_number/branch
    operation_id = service._kernel_record(program, None, line) if by == "engine" else None
    ident = service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by=by,
                                         line=line, operation_id=operation_id, kind=KIND, choice=choice,
                                         undo=undo or None)
    return {"id": ident, "line": line, "choice": choice}


def _run_or_fail(runner: Any, argv: list[str], cwd: str, stage: str,
                 track: Optional[dict[str, Any]] = None) -> str:
    if track is not None:
        track["stage"] = stage
    try:
        proc = runner._run(argv, cwd=cwd)
    except Exception as exc:
        raise DeliveryFailed(_words_of(stage, str(exc)), str(exc)) from exc
    if proc.returncode != 0:
        raw = " ".join(f"{proc.stderr or ''} {proc.stdout or ''}".split())
        raise DeliveryFailed(_words_of(stage, raw), raw[:2000])
    return str(proc.stdout or "")


def _write(runner: Any, program: Mapping[str, Any], where: Mapping[str, str],
           phase_out: Optional[dict[str, Any]] = None, track: Optional[dict[str, Any]] = None) -> tuple[int, str]:
    from ..missioncontrol_bridge import dw_argv_base
    from .agent_hand_service import branch_slug

    track = track if track is not None else {}
    track.setdefault("pr", {})
    root = str(program.get("repo_root") or "")
    base = str(program.get("base_branch") or "main")
    branch = f"program/{branch_slug(program['title'], 32) or 'program'}/delivery"
    track["pr"].update(branch=branch, base=base)
    path = Path(root).parent / f"hs-program-{program['id']}-delivery"
    track["stage"] = "worktree"
    runner._git(root, "fetch", "-q", "origin", base)
    ref = f"origin/{base}" if runner._git(root, "rev-parse", "--verify", "--quiet", f"origin/{base}") else base
    if path.is_dir():
        runner._git(root, "worktree", "remove", "--force", str(path))
    _run_or_fail(runner, ["git", "-C", root, "worktree", "add", "-q", "-B", branch, str(path), ref], root, "worktree",
                 track)
    tree = str(path)
    dw = dw_argv_base(path)
    if dw is None or not (path / ".githooks" / "dw").exists():
        track["stage"] = "rails"
        raise DeliveryFailed(_words_of("rails", ""), "no .githooks/dw at the base head")
    project, phase, story = where["project"], where["phase"], where.get("story") or ""
    if not story:
        out = _run_or_fail(runner, [*dw, "story", "create", project, phase, str(program["title"])[:120]], tree, "create",
                           track)
        found = next((_STORY.search(line) for line in reversed(out.splitlines()) if _STORY.search(line)), None)
        if found is None:
            raise DeliveryFailed(_words_of("create", ""), out[-500:])
        story = found.group(1)
    scratch = tempfile.mkdtemp(prefix="hs-program-delivery-")
    evidence_file = Path(scratch) / "evidence.md"
    evidence_file.write_text(evidence(runner.service, program), encoding="utf-8")
    _run_or_fail(runner, [*dw, "story", "evidence", project, phase, story, "--from-file", str(evidence_file), "--force"],
                 tree, "evidence", track)
    _run_or_fail(runner, [*dw, "story", "status", project, phase, story, "done"], tree, "status", track)
    if not where.get("story") and phase_out is not None:
        # JRN5: a delivery to a whole phase closes it (a major point); dw's
        # refusal (a story still open) keeps it open and says so.
        closed = runner._run([*dw, "phase", "close", project, phase, "--summary",
                              f"{program['title']} is done (HoldSpeak program)."[:200]], cwd=tree)
        raw = " ".join(f"{closed.stderr or ''} {closed.stdout or ''}".split())
        phase_out.update({"project": project, "phase": phase, "closed": closed.returncode == 0,
                          **({} if closed.returncode == 0 else {"words": raw[:300]})})
    _run_or_fail(runner, ["git", "-C", tree, "add", "-A", "--", "pm/roadmap"], tree, "commit", track)
    title = f"Delivery: {program['title']} done"[:200]
    _run_or_fail(runner, ["git", "-C", tree, "commit", "-q", "-m", title], tree, "commit", track)
    head = runner._git(tree, "rev-parse", "HEAD")
    if head:
        track["pr"]["head"] = head
    # HS-S32: from here a failure is not known to be free of remote effects.
    track["remote"] = True
    _run_or_fail(runner, ["git", "-C", tree, "push", "-u", "origin", branch], tree, "push", track)
    body = (f"The delivery of the HoldSpeak program “{program['title']}” to {where['words']}/{story}.\n\n"
            + evidence(runner.service, program))
    out = _run_or_fail(runner, ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body],
                       tree, "pr", track)
    url = next((line.strip() for line in out.splitlines() if "/pull/" in line), "")
    found = _PR_URL.match(url)
    if found is None:
        raise DeliveryFailed(_words_of("pr", ""), out[-500:])
    track["pr"].update(url=url, number=int(found.group(1)))
    return int(found.group(1)), branch


# ── HS-S32: the known delivery PR (Check, Merge, Retry, Skip) ─────────

def _receipt_of(row: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    receipt = ((row or {}).get("undo") or {}).get("receipt")
    return dict(receipt) if isinstance(receipt, Mapping) else {}


def known_pr(receipt: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """The acknowledged delivery PR of a receipt when its identity is whole
    (canonical URL, number, branch, base, prepared head), else ``None``."""
    pr = receipt.get("pr") if isinstance(receipt.get("pr"), Mapping) else {}
    url, number = str(pr.get("url") or ""), pr.get("number")
    found = _PR_URL.match(url)
    if (found is None or not isinstance(number, int) or int(found.group(1)) != number
            or not all(str(pr.get(key) or "") for key in ("branch", "base", "head"))):
        return None
    return {"url": url, "number": number, "branch": str(pr["branch"]), "base": str(pr["base"]),
            "head": str(pr["head"])}


def recovery(row: Optional[Mapping[str, Any]], rows: Optional[list[Mapping[str, Any]]] = None) -> Optional[dict[str, Any]]:
    """What a held delivery line allows: ``{state, choices, number, url}``.

    - ``retry``: the receipt shows a stop before any remote write, and no
      other delivery line shows one (Retry, Skip);
    - ``open``: a known PR, no merge request (Merge, Check, Skip);
    - ``requested``: a known PR with an unconfirmed merge request (Check, Skip);
    - ``unknown``: a known PR whose last result is not confirmed (Check, Skip);
    - ``blocked``: no whole identity (old lines, an unconfirmed create or
      push): Skip only.
    ``None`` when the line holds nothing (delivered, skipped)."""
    if row is None or row.get("choice") not in (FAILED, PR_OPEN):
        return None
    receipt = _receipt_of(row)
    pr = known_pr(receipt)
    legacy_number = ((row.get("undo") or {}).get("pr_number")) or None
    out: dict[str, Any] = {"number": pr["number"] if pr else legacy_number, "url": pr["url"] if pr else None}
    if pr is not None:
        if receipt.get("merge_requested_at"):
            return {**out, "state": "requested", "choices": ["check", "skip"]}
        if row.get("choice") == PR_OPEN:
            return {**out, "state": "open", "choices": ["merge", "check", "skip"]}
        return {**out, "state": "unknown", "choices": ["check", "skip"]}
    remote_seen = any(_receipt_of(other).get("remote") or _receipt_of(other).get("pr", {}).get("number")
                      or (other.get("undo") or {}).get("pr_number")
                      for other in rows or [] if other.get("kind") == KIND and other.get("id") != row.get("id"))
    if (row.get("choice") == FAILED and receipt.get("v") and receipt.get("stage") in _LOCAL_STAGES
            and receipt.get("remote") is False and not remote_seen):
        return {**out, "state": "retry", "choices": list(CHOICES_FAILED)}
    return {**out, "state": "blocked", "choices": ["skip"]}


#: The face's words for each state (the row's quiet fact).
_STATE_WORDS = {"retry": "Not delivered", "open": "PR #{n} open", "requested": "PR #{n} · Not confirmed",
                "unknown": "PR #{n} · Not confirmed", "blocked": "Not confirmed"}


def turn_item(program: Mapping[str, Any], row: Optional[Mapping[str, Any]],
              rows: Optional[list[Mapping[str, Any]]] = None) -> Optional[dict[str, Any]]:
    """His Your turn row for a delivery line that holds (see
    :func:`recovery`); ``None`` otherwise. ``expected_delivery_checkpoint_id``
    names the line, and every press sends it back."""
    state = recovery(row, rows)
    if state is None or row is None:
        return None
    undo = row.get("undo") or {}
    receipt = _receipt_of(row)
    where = str((receipt.get("target") or {}).get("words") or "") or (target(program) or {}).get("words") \
        or "the delivery"
    number = state.get("number")
    if state["state"] in ("retry", "blocked") and row.get("choice") == FAILED and not number:
        title = f"Deliver “{program['title']}” to {where}: it {undo.get('words') or 'stopped'}"
    elif state["state"] == "open":
        title = f"Merge the delivery PR #{number} of “{program['title']}”?"
    else:
        title = f"The delivery PR #{number} of “{program['title']}” is not confirmed" if number else \
            f"The delivery of “{program['title']}” to {where} is not confirmed"
    happened = {
        "requested": f"A merge of the delivery PR #{number} is requested. GitHub has not confirmed it",
        "unknown": f"HoldSpeak could not confirm the delivery PR #{number}: {undo.get('words') or 'no answer'}",
        "blocked": ("HoldSpeak cannot confirm the delivery PR #{n}. It may be on GitHub".format(n=number) if number
                    else "HoldSpeak cannot confirm what reached GitHub for this delivery"),
    }.get(state["state"], "")
    if state["state"] == "blocked" and not number and receipt.get("v") is None and row.get("choice") == FAILED:
        happened = ""  # an old line: its own words (the title's), with Skip only
    words = _STATE_WORDS[state["state"]].format(n=number)
    return {
        "program_id": program["id"], "program_title": program["title"], "step_id": "", "ordinal": 0,
        "step_title": "", "launch_id": None, "since": row.get("at"), "project_id": program.get("project_id"),
        "for_person_id": program.get("for_person_id"),
        "pr": {"number": number, "url": state.get("url")} if number else None,
        "id": f"{program['id']}:delivery", "kind": KIND, "choices": list(state["choices"]), "title": title,
        "expected_delivery_checkpoint_id": int(row["id"]),
        "delivery": {"state": state["state"], "words": words, **({"happened": happened} if happened else {})},
    }


def _read(runner: Any, program: Mapping[str, Any], pr: Mapping[str, Any]) -> dict[str, Any]:
    """One bounded read of the known PR by its URL (read only). Returns
    ``{result, words, observed}``; result is merged, open, closed,
    mismatch or unavailable. Nothing but a whole match is ever a yes."""
    cwd = str(program.get("repo_root") or "")
    try:
        proc = runner._run(["gh", "pr", "view", pr["url"], "--json", _READ_FIELDS], cwd=cwd)
    except Exception:
        return {"result": "unavailable", "words": "HoldSpeak could not read the PR on GitHub", "observed": {}}
    if proc.returncode != 0:
        return {"result": "unavailable", "words": "HoldSpeak could not read the PR on GitHub", "observed": {}}
    try:
        data = json.loads(str(proc.stdout or "")[:_READ_MAX])
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return {"result": "unavailable", "words": "GitHub's answer was not readable", "observed": {}}
    state = str(data.get("state") or "").upper()
    observed = {"state": state[:20], "head": str(data.get("headRefOid") or "")[:64],
                "base": str(data.get("baseRefName") or "")[:200]}
    if (data.get("url") != pr["url"] or data.get("number") != pr["number"] or data.get("isCrossRepository") is not False
            or data.get("headRefName") != pr["branch"] or data.get("baseRefName") != pr["base"]):
        return {"result": "mismatch", "words": "the PR on GitHub is not the delivery PR HoldSpeak opened",
                "observed": observed}
    if data.get("headRefOid") != pr["head"]:
        return {"result": "mismatch", "words": "the PR on GitHub has commits HoldSpeak did not prepare",
                "observed": observed}
    if state == "MERGED":
        return {"result": "merged", "words": "GitHub shows the PR merged", "observed": observed}
    if state == "OPEN":
        return {"result": "open", "words": "GitHub shows the PR open", "observed": observed}
    if state == "CLOSED":
        return {"result": "closed", "words": "GitHub shows the PR closed, not merged", "observed": observed}
    return {"result": "unavailable", "words": "GitHub's answer was not readable", "observed": observed}


def _observed_line(runner: Any, program: Mapping[str, Any], row: Mapping[str, Any], receipt: Mapping[str, Any],
                   read: Mapping[str, Any], *, by: str) -> dict[str, Any]:
    """The ledger line of one read: Delivered on a merged match; the PR open;
    else not confirmed. The identity, target, phase and any merge request
    stay on the line until GitHub shows the PR merged."""
    service = runner.service
    undo = row.get("undo") or {}
    pr = known_pr(receipt) or {}
    number, branch = pr.get("number"), str(pr.get("branch") or "")
    where = str((receipt.get("target") or {}).get("words") or "the delivery")
    phase = undo.get("phase") or {}
    out = {**dict(receipt), "observed": {**dict(read.get("observed") or {}), "at": service._clock()}}
    if read["result"] == "merged":
        out.pop("merge_requested_at", None)
        out.pop("merge_requested_by", None)
        out["reconciled"] = True
        return _line(service, program, DELIVERED, f"Delivered to {where} (PR #{number})" + _phase_words(phase),
                     pr_number=number, branch=branch, by=by, phase=phase, receipt=out)
    if read["result"] == "open":
        tail = " · a merge is requested, not confirmed" if out.get("merge_requested_at") else ""
        return _line(service, program, PR_OPEN, f"The delivery PR #{number} to {where} is open on GitHub{tail}",
                     pr_number=number, branch=branch, by=by, phase=phase, receipt=out)
    return _line(service, program, FAILED, f"Could not confirm the delivery PR #{number} to {where}: {read['words']}",
                 words=str(read["words"]), pr_number=number, branch=branch, by=by, phase=phase,
                 receipt={**out, "stage": "check"})


def check(runner: Any, program: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """Check: one read of the known PR; its truthful line. Never a merge,
    a push, a create or a dw command."""
    receipt = _receipt_of(row)
    pr = known_pr(receipt)
    assert pr is not None  # recovery() offers Check on a whole identity only
    return _observed_line(runner, program, row, receipt, _read(runner, program, pr), by="owner")


def owner_merge(runner: Any, program: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """His Merge of a known PR (a fresh Secure PR, or one Check found open):
    the committed request line first (``merge_requested_at``), then a read,
    then at most one head-guarded merge by URL, then a read. An append that
    fails sends nothing; the request stays on every later line until GitHub
    shows the PR merged."""
    service = runner.service
    undo = row.get("undo") or {}
    receipt = _receipt_of(row)
    pr = known_pr(receipt)
    assert pr is not None
    where = str((receipt.get("target") or {}).get("words") or "the delivery")
    phase = undo.get("phase") or {}
    requested = {**receipt, "stage": "merge", "remote": True, "merge_requested_at": service._clock(),
                 "merge_requested_by": "owner"}
    barrier = _line(service, program, PR_OPEN, f"You asked to merge the delivery PR #{pr['number']} to {where} · "
                    "not confirmed", pr_number=pr["number"], branch=pr["branch"], by="owner", phase=phase,
                    receipt=requested)
    held = {**row, "id": barrier["id"], "undo": {**undo, "receipt": requested}}
    read = _read(runner, program, pr)
    if read["result"] != "open":
        return _observed_line(runner, program, held, requested, read, by="owner")
    cwd = str(program.get("repo_root") or "")
    try:
        proc = runner._run(["gh", "pr", "merge", pr["url"], "--squash", "--match-head-commit", pr["head"]], cwd=cwd)
        code, raw = proc.returncode, " ".join(f"{proc.stderr or ''} {proc.stdout or ''}".split())
    except Exception as exc:
        code, raw = -1, str(exc)
    if code != 0:
        return _line(service, program, FAILED, f"Could not deliver to {where}: {_words_of('merge', raw)}",
                     detail=raw[:2000], words=_words_of("merge", raw), pr_number=pr["number"], branch=pr["branch"],
                     by="owner", phase=phase, receipt=requested)
    return _observed_line(runner, program, held, requested, _read(runner, program, pr), by="owner")


def decide(runner: Any, program: Mapping[str, Any], choice: str,
           expected_delivery_checkpoint_id: Any = None) -> dict[str, Any]:
    """His press on the delivery row: Check (read the known PR), Merge (a
    known open PR), Retry (a stop before any remote write) or Skip (the
    Program stays Done; nothing is called). The press names the line it
    answers; a missing or older line is refused before anything runs."""
    from .program_definitions import ProgramRefused

    service = runner.service
    rows = [row for row in service.store.list_checkpoints(program["id"]) if row.get("kind") == KIND]
    row = rows[0] if rows else None
    item = turn_item(program, row, rows)
    if item is None or row is None:
        raise ProgramRefused("no_delivery_waits", "No delivery waits for you.")
    expected = expected_delivery_checkpoint_id
    if expected in (None, ""):
        raise ProgramRefused("delivery_binding_required",
                             "Read the delivery again: this press does not name the delivery line it answers.",
                             status=409)
    try:
        expected = int(expected)
    except (TypeError, ValueError):
        raise ProgramRefused("delivery_binding_invalid", "The delivery line is not a number.", status=400) from None
    if expected != int(row["id"]):
        raise ProgramRefused("delivery_changed", "The delivery changed. Read it again.", status=409)
    if choice not in item["choices"]:
        raise ProgramRefused("choice_invalid", f"The delivery takes {', '.join(item['choices'])}.", status=400)
    undo = row.get("undo") or {}
    receipt = _receipt_of(row)
    state = item["delivery"]["state"]
    if choice == "skip":
        pr = known_pr(receipt)
        number = (pr or {}).get("number") or undo.get("pr_number")
        if state == "retry":
            line = "Skipped the delivery: Done, not delivered"
        else:
            line = f"Skipped the delivery: PR #{number} not confirmed" if number else \
                "Skipped the delivery: not confirmed"
        kept = {**receipt, "skipped_from": int(row["id"])} if receipt else None
        return _line(service, program, SKIPPED, line, by="owner", phase=undo.get("phase") or None,
                     pr_number=number, branch=str(undo.get("branch") or ""), receipt=kept)
    if choice == "check":
        return check(runner, program, row)
    if choice == "merge":
        return owner_merge(runner, program, row)
    recorded = str((receipt.get("target") or {}).get("ref") or "")
    if recorded != str(program.get("delivery_ref") or ""):
        raise ProgramRefused("delivery_target_changed",
                             f"The delivery was to {(receipt.get('target') or {}).get('words') or 'another target'}. "
                             "Its target changed since; Retry does not move it.", status=409)
    service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="owner",
                                 line="Retried the delivery")
    return deliver(runner, program) or {}


__all__ = ["DeliveryFailed", "KIND", "check", "decide", "deliver", "evidence", "known_pr", "last_line", "merge",
           "owner_merge", "pending", "recovery", "target", "turn_item"]
