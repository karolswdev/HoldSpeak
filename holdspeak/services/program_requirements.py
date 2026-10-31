"""Programs PG-REQ (2026-10-31): the rules of a requirement, no I/O.

docs/internal/betterment/programs/PROGRAMS-REQUIREMENTS-2026-10-31.md. A
requirement is one sentence of the owner's on a Program or on a step, with
the way it is proven:

- **Check**: a command HoldSpeak runs on the step's commit (its log is read
  by ``program_verifier.verify_requirement_log``);
- **Review**: the step's reviewer answers ``REQ R3: MET · …`` or
  ``REQ R3: UNMET · …`` by its id;
- **Shot**: the repository's shot command renders one window at one width
  (``.holdspeak/program.json`` ``shot``);
- **Your word**: he presses Met or Unmet.

This module holds the vocabulary (§4), the kind guessed by rule (§4,
decision 5), the counts (§7) and the wire of one requirement (§11). The
writes live in ``ProgramService``; the judgements in ``ProgramRunner``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

KINDS = ("check", "review", "shot", "word")
KIND_WORDS = {"check": "Check", "review": "Review", "shot": "Shot", "word": "Your word"}
STATES = ("not_yet", "met", "unmet", "waived")
STATE_WORDS = {"not_yet": "Not yet", "met": "Met", "unmet": "Unmet", "waived": "Waived"}
CHECKING_WORD = "Checking"
WAITS_WORD = "Waits for you"
#: The widths a Shot renders at (the desk sweep's sizes).
SHOT_WIDTHS = (393, 1440)
#: The judgements that go back to Not yet when the step's commit moves
#: (decision 4: his word stays as he pressed it).
COMMIT_BOUND = frozenset({"check", "shot", "review"})
#: ``by``: who added it.
BY = ("owner", "agent", "template")

#: Step states in which a requirement of the step no longer changes.
FROZEN_STEP_STATES = frozenset({"merged", "done"})

_BACKTICKS = re.compile(r"`([^`]+)`")
_SHOT = re.compile(r"\b([A-Za-z][\w-]*)\s+window\s+at\s+(393|1440)\b", re.I)
_REQ_LINE = re.compile(r"^\s*(?:[-*]\s*)?REQ\s+R(\d+)\s*[:\-]\s*(MET|UNMET)\b\s*(?:[·:\-—]\s*)?(.*?)\s*$", re.I)


class RequirementInvalid(ValueError):
    """A requirement that cannot be stored as given (``code``, ``detail``)."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code, self.detail = code, detail


def label(ordinal: Any) -> str:
    return f"R{int(ordinal or 0)}"


def guess(text: str) -> tuple[str, dict[str, Any]]:
    """The kind by rule, never by a model (decision 5): text in backticks is
    a Check with that command; a window name followed by "at 393" or
    "at 1440" is a Shot of that case at that width; anything else is a
    Review. Your word is only his choice."""
    words = str(text or "")
    command = _BACKTICKS.search(words)
    if command and command.group(1).strip():
        return "check", {"command": command.group(1).strip()}
    shot = _SHOT.search(words)
    if shot:
        return "shot", {"case": shot.group(1).lower(), "width": int(shot.group(2))}
    return "review", {}


def clean_text(text: Any) -> str:
    return " ".join(str(text or "").split())[:400]


def clean_spec(kind: str, raw: Any, text: str) -> dict[str, Any]:
    """The spec of one kind: check ``{command, expect?}``, shot ``{case,
    width}``, review and word ``{}``. A missing field is filled by the rule
    from the sentence where it can be."""
    raw = dict(raw or {}) if isinstance(raw, Mapping) else {}
    guessed_kind, guessed = guess(text)
    if kind == "check":
        command = str(raw.get("command") or (guessed.get("command") if guessed_kind == "check" else "") or "").strip()
        out: dict[str, Any] = {"command": command} if command else {}
        expect = str(raw.get("expect") or "").strip()
        if expect:
            try:
                re.compile(expect)
            except re.error as exc:
                raise RequirementInvalid("expect_invalid", f"The expected line is not a pattern: {exc}.")
            out["expect"] = expect
        return out
    if kind == "shot":
        case = str(raw.get("case") or (guessed.get("case") if guessed_kind == "shot" else "") or "").strip().lower()
        width = raw.get("width") or (guessed.get("width") if guessed_kind == "shot" else None)
        try:
            width = int(width) if width not in (None, "") else None
        except (TypeError, ValueError):
            width = None
        if width is not None and width not in SHOT_WIDTHS:
            raise RequirementInvalid("width_invalid", "A shot is at 393 or 1440.")
        out = {}
        if case:
            out["case"] = case
        if width:
            out["width"] = width
        return out
    return {}


def provable(kind: str, spec: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    """Why this requirement cannot be proven here, or ``""`` (§4: such a
    requirement is a core question at every level; the add row says so)."""
    if kind == "check" and not spec.get("command"):
        return "A check needs a command"
    if kind == "shot":
        if not str(config.get("shot") or "").strip():
            return "No shot command in this repository"
        if not spec.get("case") or not spec.get("width"):
            return "A shot needs a window and a width"
    return ""


def repository_config(root: Any) -> dict[str, Any]:
    """``.holdspeak/program.json`` of a repository (``{}`` when there is none)."""
    if not root:
        return {}
    try:
        value = json.loads((Path(str(root)) / ".holdspeak" / "program.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def shot_command(config: Mapping[str, Any], spec: Mapping[str, Any]) -> str:
    template = str(config.get("shot") or "")
    return template.replace("{case}", str(spec.get("case") or "")).replace("{width}", str(spec.get("width") or ""))


def shot_image(worktree: str, config: Mapping[str, Any], spec: Mapping[str, Any]) -> Optional[str]:
    """The newest image the shot command wrote for the case and width
    (``shot_image``: a glob under the worktree, with ``{case}`` and
    ``{width}``)."""
    pattern = str(config.get("shot_image") or "").replace("{case}", str(spec.get("case") or "")).replace(
        "{width}", str(spec.get("width") or ""))
    if not pattern or not worktree:
        return None
    found = sorted(Path(worktree).glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return str(found[0]) if found else None


def parse_review(words: Any) -> dict[int, dict[str, str]]:
    """The reviewer's ``REQ R3: MET · …`` / ``REQ R3: UNMET · …`` lines, by
    ordinal (the last answer for an id wins)."""
    out: dict[int, dict[str, str]] = {}
    for line in str(words or "").splitlines():
        match = _REQ_LINE.match(line)
        if match:
            out[int(match.group(1))] = {"answer": match.group(2).upper(), "line": match.group(3).strip(),
                                        "raw": line.strip()}
    return out


def scope_of(requirement: Mapping[str, Any]) -> str:
    """``program`` (the end check), ``every_step`` (the parent and each
    step's copy of it) or ``step`` (a step's own)."""
    if requirement.get("each_step"):
        return "every_step"
    return "step" if requirement.get("step_id") else "program"


def judged(requirement: Mapping[str, Any]) -> bool:
    """Met or Waived: it no longer gates."""
    return requirement.get("state") in ("met", "waived")


def gates(requirement: Mapping[str, Any]) -> bool:
    return bool(requirement.get("required")) and not judged(requirement)


def counted(requirements: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The rows a count counts: the steps' own, each step's copy of an
    every-step one, and the Program's own end-check ones (an every-step
    parent counts through its copies)."""
    return [row for row in requirements if row.get("required") and not (not row.get("step_id") and row.get("each_step"))]


def counts(requirements: Iterable[Mapping[str, Any]], his: int = 0) -> Optional[dict[str, int]]:
    """``{met, total, unmet, waived, his}`` over the required ones; Waived
    counts as met. ``None`` when there is none (the face draws nothing)."""
    rows = counted(requirements)
    if not rows:
        return None
    return {
        "met": sum(1 for row in rows if judged(row)), "total": len(rows),
        "unmet": sum(1 for row in rows if row.get("state") == "unmet"),
        "waived": sum(1 for row in rows if row.get("state") == "waived"), "his": int(his),
    }


def proof_words(requirement: Mapping[str, Any]) -> str:
    """How it is proven, in the builder's brief (§6)."""
    kind = requirement.get("kind")
    spec = requirement.get("spec") or {}
    if kind == "check":
        return "HoldSpeak runs it on your commit"
    if kind == "shot":
        return f"the desk sweep renders {spec.get('case')}-{spec.get('width')}"
    if kind == "word":
        return "the owner says it"
    return "the reviewer judges it"


__all__ = [
    "BY", "CHECKING_WORD", "COMMIT_BOUND", "FROZEN_STEP_STATES", "KINDS", "KIND_WORDS", "RequirementInvalid",
    "SHOT_WIDTHS", "STATES", "STATE_WORDS", "WAITS_WORD", "clean_spec", "clean_text", "counted", "counts", "gates",
    "guess", "judged", "label", "parse_review", "proof_words", "provable", "repository_config", "scope_of",
    "shot_command", "shot_image",
]
