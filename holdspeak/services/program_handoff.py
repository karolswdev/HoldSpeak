"""Programs PG19: the handoff brief (taken from Moonfold's provider handoff,
MIT; see THIRD_PARTY_NOTICES.md).

When a step's agent stops at its usage limit, or he moves the step by hand,
the next agent continues in the same worktree on the same branch. It does
not get the earlier agent's conversation; it gets this brief, which
HoldSpeak builds WITHOUT a model from what it already holds:

- who and where: the Program, the step, the agents, the reason;
- the goal in his words, then the step's brief;
- the plan and its progress (every step and its state), this step's
  checkpoints;
- what he said since (his checkpoints and re-briefs, newest first);
- the files changed on the branch (``launch_lane.worktree_facts``),
  ``git status --porcelain`` and ``git diff --stat`` against the step's
  base commit;
- the last red check's log tail, the open asks, the limit line;
- the repository's CLAUDE.md or AGENTS.md (clipped);
- how to continue.

:func:`gather` reads the database and git; :func:`build` is pure: the
same inputs give the same bytes (``tests/unit/test_program_handoff.py``
pins a golden brief). :func:`redact_counted` passes the text through the
desk's redactor (``memory.defense``) and counts what it replaced by kind:
keys, tokens, passwords, private keys.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..memory.defense import REDACTED, _apply, redaction_spans

REASONS = ("usage_limit", "usage_warning", "by_hand")

LIMITS = {
    "goal": 1500, "brief": 3000, "said": 8, "said_line": 400, "checkpoints": 10, "files": 50,
    "status_lines": 60, "stat_lines": 60, "tail_lines": 20, "tail_chars": 1500, "instructions": 4000,
}

#: The redaction kinds the preview counts, in the order it names them.
KINDS = ("key", "token", "password", "private_key", "other")
KIND_WORDS = {"key": ("key", "keys"), "token": ("token", "tokens"), "password": ("password", "passwords"),
              "private_key": ("private key", "private keys"), "other": ("other secret", "other secrets")}


@dataclass(frozen=True)
class HandoffInputs:
    """Everything the brief says, already read."""

    program_title: str
    step_ordinal: int
    step_total: int
    step_title: str
    from_label: str
    to_label: str
    reason: str
    by: str = "engine"
    goal: str = ""
    step_brief: str = ""
    plan: tuple[tuple[int, str, str, str], ...] = ()          # (ordinal, title, mark, state word)
    checkpoints: tuple[str, ...] = ()                          # this step's lines, oldest first
    said: tuple[str, ...] = ()                                 # his lines, newest first
    files: tuple[str, ...] = ()                                # "M path"
    git_status: Optional[str] = None
    diff_stat: Optional[str] = None
    failing_check: Optional[tuple[str, str]] = None            # (command, log tail)
    open_asks: tuple[str, ...] = ()
    limit_line: str = ""
    instructions: Optional[tuple[str, str]] = None             # (file name, text)
    branch: str = ""
    base_branch: str = ""
    worktree: str = ""
    earlier_turns: int = 0
    gate: str = ""


@dataclass(frozen=True)
class HandoffBrief:
    text: str
    redacted: dict[str, int] = field(default_factory=dict)
    earlier_turns: int = 0

    @property
    def redacted_words(self) -> str:
        return redacted_words(self.redacted)


def _clip(text: str, limit: int) -> str:
    value = str(text or "").strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _one_line(text: str, limit: int) -> str:
    return _clip(" ".join(str(text or "").split()), limit)


def _clip_lines(text: str, limit: int) -> str:
    lines = str(text or "").rstrip().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[:limit] + [f"… {len(lines) - limit} more lines"])


def _tail(text: str, lines: int, chars: int) -> str:
    tail = "\n".join(str(text or "").rstrip().splitlines()[-lines:])
    return tail if len(tail) <= chars else "…" + tail[-(chars - 1):]


def _fenced(text: str) -> str:
    """Quoted output: a fence inside is broken up so it cannot close ours."""
    return "\n".join(["```", str(text).replace("```", "`​``"), "```"])


_REASON = {
    "usage_limit": "{frm} reached its usage limit, so HoldSpeak moved the step to you, {to}.",
    "usage_warning": "{frm} is close to its usage limit, so HoldSpeak moved the step to you, {to}, before it stops.",
    "by_hand": "The owner moved the step from {frm} to you, {to}.",
}


def build(inputs: HandoffInputs) -> str:
    """The brief's text (not yet redacted). Pure."""
    reason = _REASON.get(inputs.reason, _REASON["by_hand"]).format(frm=inputs.from_label, to=inputs.to_label)
    parts: list[str] = [
        "# Handoff brief",
        f"HoldSpeak on step {inputs.step_ordinal} of {inputs.step_total} of the program “{inputs.program_title}”. {reason}",
        "This brief is HoldSpeak's, built from the step's record without a model; the owner's words are quoted as his. "
        "You do not get the earlier agent's conversation.",
        "",
        "## Where",
        f"- Step {inputs.step_ordinal}: {inputs.step_title}",
        f"- Worktree: {inputs.worktree or 'the step worktree'} (the same one; continue here)",
        f"- Branch: {inputs.branch or 'the step branch'} (from {inputs.base_branch or 'main'}; do not make a new branch)",
    ]
    if inputs.earlier_turns:
        parts.append(f"- Earlier turns on this step: {inputs.earlier_turns} (not included)")
    if inputs.goal.strip():
        parts += ["", "## The goal", "The goal of the program, in the owner's words:", _fenced(_clip(inputs.goal, LIMITS["goal"]))]
    parts += ["", "## This step", _fenced(_clip(inputs.step_brief or inputs.step_title, LIMITS["brief"]))]
    if inputs.plan:
        parts += ["", "## The plan and progress", "`[x]` done, `[~]` this step or running, `[ ]` not started."]
        parts += [f"- {mark} {ordinal} {_one_line(title, 200)} ({word})" for ordinal, title, mark, word in inputs.plan]
    if inputs.checkpoints:
        rows = list(inputs.checkpoints)[-LIMITS["checkpoints"]:]
        parts += ["", "## Checkpoints on this step", "Oldest first."] + [f"- {_one_line(line, 300)}" for line in rows]
    if inputs.said:
        rows = list(inputs.said)[: LIMITS["said"]]
        parts += ["", "## What the owner said since", "Newest first. These still apply."]
        parts += [f"- {_one_line(line, LIMITS['said_line'])}" for line in rows]
        if len(inputs.said) > len(rows):
            parts.append(f"- … {len(inputs.said) - len(rows)} earlier lines")
    if inputs.files:
        rows = list(inputs.files)[: LIMITS["files"]]
        parts += ["", "## Files changed on the branch"] + [f"- {row}" for row in rows]
        if len(inputs.files) > len(rows):
            parts.append(f"- … {len(inputs.files) - len(rows)} more files")
    if inputs.git_status is not None or inputs.diff_stat is not None:
        parts += ["", "## The worktree now"]
        if inputs.git_status is not None:
            parts += ["`git status --porcelain`:", _fenced(_clip_lines(inputs.git_status, LIMITS["status_lines"]) or "(clean)")]
        if inputs.diff_stat is not None:
            parts += ["`git diff --stat` against the step's base:",
                      _fenced(_clip_lines(inputs.diff_stat, LIMITS["stat_lines"]) or "(no change)")]
    problems: list[str] = []
    if inputs.failing_check:
        command, tail = inputs.failing_check
        problems += [f"- The last check was red: `{_one_line(command, 200)}`. The end of its log:",
                     _fenced(_tail(tail, LIMITS["tail_lines"], LIMITS["tail_chars"]))]
    if inputs.limit_line:
        problems.append(f"- The earlier agent stopped with: {_one_line(inputs.limit_line, 240)}")
    for ask in inputs.open_asks:
        problems.append(f"- Open: {_one_line(ask, 240)}")
    if problems:
        parts += ["", "## Open problems"] + problems
    if inputs.instructions:
        name, text = inputs.instructions
        parts += ["", f"## Repository instructions ({name})", _fenced(_clip(text, LIMITS["instructions"]))]
    parts += [
        "", "## How to continue",
        "Check the worktree against this brief before you change anything. Do not redo finished work. "
        "Continue with what is left of this step, commit on this branch, and end your turn. "
        + (f"HoldSpeak runs `{inputs.gate}` on your last commit. " if inputs.gate else "")
        + "Write one line with program.checkpoint to say where you pick up, and call program.step_done with your "
        "report when you are done.",
    ]
    return "\n".join(parts).strip() + "\n"


# ── redaction, counted by kind ───────────────────────────────────────


def _kind(span: str) -> str:
    low = span.casefold()
    if "-----begin" in low or ("\n" in span and len(span) > 120):
        return "private_key"
    if "password" in low or "passwd" in low or "://" in span:
        return "password"
    if any(word in low for word in ("api_key", "api-key", "apikey", "sk-", "akia", "sg.", "atatt", "secret")):
        return "key"
    if any(word in low for word in ("token", "bearer", "authorization", "gh", "github_pat_", "xox", "eyj")):
        return "token"
    return "other"


def redact_counted(text: str) -> tuple[str, dict[str, int]]:
    """``text`` through the desk's redactor, and how many it replaced, by
    kind (only the kinds with one or more)."""
    value = str(text or "")
    spans = redaction_spans(value)
    counts: dict[str, int] = {}
    for start, end in spans:
        kind = _kind(value[start:end])
        counts[kind] = counts.get(kind, 0) + 1
    return (_apply(value, spans) if spans else value), {kind: counts[kind] for kind in KINDS if counts.get(kind)}


def redacted_words(counts: Mapping[str, int]) -> str:
    """``2 keys, 1 token`` (empty when nothing was redacted)."""
    words = []
    for kind in KINDS:
        n = int(counts.get(kind) or 0)
        if n:
            one, many = KIND_WORDS[kind]
            words.append(f"{n} {one if n == 1 else many}")
    return ", ".join(words)


def brief_of(inputs: HandoffInputs) -> HandoffBrief:
    text, counts = redact_counted(build(inputs))
    return HandoffBrief(text=text, redacted=counts, earlier_turns=inputs.earlier_turns)


# ── reading the record ───────────────────────────────────────────────

_MARK_DONE = frozenset({"merged", "done"})
_MARK_LIVE = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review", "findings",
                        "pr_open", "merge_ask"})


def _instructions(worktree: str) -> Optional[tuple[str, str]]:
    for name in ("CLAUDE.md", "AGENTS.md"):
        try:
            text = (Path(worktree) / name).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if text.strip():
            return name, text
    return None


def gather(
    service: Any, program: Mapping[str, Any], step: Mapping[str, Any], *, to_label: str, from_label: str,
    reason: str, by: str = "engine", git: Optional[Callable[..., str]] = None,
    facts_reader: Optional[Callable[[str, str], Mapping[str, Any]]] = None,
) -> HandoffInputs:
    """Read the step's record and its worktree into :class:`HandoffInputs`.

    ``git(cwd, *args) -> stdout`` (the runner's seam); ``facts_reader(launch_id,
    path)`` is ``launch_lane.worktree_facts``."""
    from .program_service import your_turn
    from .program_verifier import log_tail

    steps = service.store.list_steps(program["id"])
    checkpoints = service.store.list_checkpoints(program["id"])
    wire = {row["id"]: service.step_wire(program, row, checkpoints) for row in steps}
    top = [row for row in steps if not row.get("race_of")]
    plan = []
    for row in sorted(top, key=lambda r: int(r["ordinal"])):
        state = str(row.get("state") or "")
        mark = "[x]" if state in _MARK_DONE else "[~]" if (row["id"] == step["id"] or state in _MARK_LIVE) else "[ ]"
        word = "this step" if row["id"] == step["id"] else wire[row["id"]]["state_word"]
        plan.append((int(row["ordinal"]), str(row["title"]), mark, word))
    own = [row for row in reversed(checkpoints) if row["step_id"] == step["id"] and row["by"] in ("agent", "engine")
           and row.get("kind") != "handoff"]
    # His own lines on this step (a checkpoint, a re-brief, a decide), newest
    # first; the Program-wide lines are the service's record of his presses.
    said = [row["line"] for row in checkpoints if row["by"] == "owner" and row["step_id"] == step["id"]
            and row.get("kind") != "handoff"]
    worktree = str(step.get("worktree") or "")
    files: list[str] = []
    status = diff = None
    if worktree and Path(worktree).is_dir():
        if facts_reader is not None:
            facts = dict(facts_reader(str(step.get("launch_id") or ""), worktree) or {})
        else:
            from .launch_lane import worktree_facts

            facts = dict(worktree_facts(str(step.get("launch_id") or ""), worktree) or {})
        files = [f"{row.get('status', '?')} {row.get('path')}" for row in facts.get("files") or [] if row.get("path")]
        if git is not None:
            status = git(worktree, "status", "--porcelain")
            base = str((step.get("facts") or {}).get("base_commit") or "")
            diff = git(worktree, "diff", "--stat", base) if base else git(worktree, "diff", "--stat")
    failing = None
    if step.get("check_log") and step.get("check_verdict") not in (None, "green"):
        failing = (str((step.get("facts") or {}).get("check", {}).get("command") or program.get("check_command") or "the check"),
                   log_tail(step.get("check_log"), LIMITS["tail_lines"]))
    asks = [item["title"] for item in your_turn(program, steps)
            if item.get("step_id") == step["id"] and item["kind"] not in ("limited",)]
    limit = (step.get("facts") or {}).get("limit") or {}
    return HandoffInputs(
        program_title=str(program["title"]), step_ordinal=int(step["ordinal"]), step_total=len(top),
        step_title=str(step["title"]), from_label=from_label, to_label=to_label, reason=reason, by=by,
        goal=str(program.get("goal_markdown") or ""), step_brief=str(step.get("brief_markdown") or ""),
        plan=tuple(plan), checkpoints=tuple(row["line"] for row in own), said=tuple(said), files=tuple(files),
        git_status=status, diff_stat=diff, failing_check=failing, open_asks=tuple(asks),
        limit_line=str(limit.get("line") or "") if reason != "by_hand" else "",
        instructions=_instructions(worktree) if worktree else None,
        branch=str(step.get("branch") or ""), base_branch=str(program.get("base_branch") or ""),
        worktree=Path(worktree).name if worktree else "",
        earlier_turns=int((step.get("facts") or {}).get("turns") or 0),
        gate=str(program.get("check_command") or "") if step.get("gate_check") else "",
    )


__all__ = ["HandoffBrief", "HandoffInputs", "KINDS", "REASONS", "brief_of", "build", "gather", "redact_counted",
           "redacted_words", "REDACTED"]
