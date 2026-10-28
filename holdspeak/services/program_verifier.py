"""The gate's verifier (Programs design §5, from hivehouse): it reads the LOG.

An exit code is a claim; the log is the receipt. The engine writes a header
before the check command runs and a footer after it
(``program_runner.run_check``)::

    program-check: commit <sha>
    program-check: tree clean            (or: tree dirty)
    program-check: command <the command>
    ... the check's own output ...
    program-check: exit <rc>

A check log is green only when ALL of these hold:

1. it names the commit it ran on, and the worktree was clean at the start;
2. every section it opens (``== build``, ``== vitest related``, ...) has a
   result line, and every required section is there;
3. no section is red, and no section appears twice;
4. the check's own verdict line (``QUICK CHECK GREEN``) ends the output.

No log path, or a log that is not there, is never green.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Optional

HEADER = "program-check:"

#: The quick check's section names (scripts/quick_check.sh) -> the short names.
SECTION_NAMES = {
    "build": "build",
    "vitest": "vitest",
    "pytest": "pytest",
    "desk": "sweep",
    "sweep": "sweep",
    "canon": "canon",
    "repo": "repo",
}
#: The sections a quick check log must carry (vitest and pytest run only when
#: the change touches their files).
QUICK_CHECK_REQUIRED = ("build", "sweep", "canon", "repo")
#: Every section the faces draw, in order.
SECTION_ORDER = ("build", "vitest", "pytest", "sweep", "canon", "repo")

_SECTION = re.compile(r"^==\s+(\S+)")
_VERDICT = re.compile(r"^(?:QUICK\s+)?CHECK\s+(GREEN|RED)\b")
_PASSED = re.compile(r"\b(\d+)\s+passed\b")
_FAILED = re.compile(r"\b(\d+)\s+failed\b")
_ERRORS = re.compile(r"\b(\d+)\s+errors?\b")
_RESULT_WORDS = re.compile(r"\b(ok|no tests ran|tolerated)\b|\bRED\b")


def _section_name(raw: str) -> str:
    word = raw.strip().lower()
    return SECTION_NAMES.get(word, word)


def _red_line(line: str) -> bool:
    if "RED" in line.split() or re.search(r"\bRED\b", line):
        return True
    if re.match(r"^\s*(FAILED|ERROR)\b", line):
        return True
    failed = _FAILED.search(line)
    if failed and int(failed.group(1)) > 0:
        return True
    errors = _ERRORS.search(line)
    return bool(errors and int(errors.group(1)) > 0 and "unhandled" not in line)


def _result_line(line: str) -> bool:
    return bool(_PASSED.search(line) or _FAILED.search(line) or _RESULT_WORDS.search(line))


def verify_text(text: str, *, required: Iterable[str] = QUICK_CHECK_REQUIRED) -> dict[str, Any]:
    """The verdict of one check log's text (see the module rules)."""
    reasons: list[str] = []
    commit: Optional[str] = None
    clean: Optional[bool] = None
    exit_code: Optional[int] = None
    sections: dict[str, str] = {}
    order: list[str] = []
    current: Optional[str] = None
    output_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith(HEADER):
            body = line[len(HEADER):].strip()
            if body.startswith("commit "):
                commit = body.split(" ", 1)[1].strip() or None
            elif body == "tree clean":
                clean = True
            elif body.startswith("tree dirty"):
                clean = False
            elif body.startswith("exit "):
                try:
                    exit_code = int(body.split(" ", 1)[1])
                except ValueError:
                    exit_code = None
            continue
        output_lines.append(line)
        match = _SECTION.match(line)
        if match:
            name = _section_name(match.group(1))
            if name in sections:
                reasons.append(f"the section {name} is in the log twice")
                sections[name] = "red"
            else:
                sections[name] = "no result"
                order.append(name)
            current = name
            continue
        if current is None or _VERDICT.match(line.strip()):
            continue
        if _red_line(line):
            sections[current] = "red"
        elif _result_line(line) and sections[current] == "no result":
            sections[current] = "green"
    if not commit:
        reasons.append("the log names no commit")
    if clean is False:
        reasons.append("the worktree had changes that were not committed when the check started")
    elif clean is None:
        reasons.append("the log does not say the worktree was clean")
    for name in required:
        if name not in sections:
            reasons.append(f"the section {name} is not in the log")
    for name in order:
        state = sections[name]
        if state == "no result":
            reasons.append(f"the section {name} has no result line")
        elif state == "red":
            if not any(name in reason and "twice" in reason for reason in reasons):
                reasons.append(f"the section {name} is red")
    last = next((line.strip() for line in reversed(output_lines) if line.strip()), "")
    verdict = _VERDICT.match(last)
    if verdict is None:
        reasons.append("the log does not end with the check's verdict line")
    elif verdict.group(1) == "RED":
        reasons.append("the check's verdict is RED")
    return {
        "green": not reasons,
        "verdict": "green" if not reasons else "red",
        "reasons": reasons,
        "sections": [{"name": name, "state": sections[name]} for name in order],
        "commit": commit,
        "clean": clean,
        "exit": exit_code,
    }


def verify_log(path: Optional[str], *, required: Iterable[str] = QUICK_CHECK_REQUIRED) -> dict[str, Any]:
    """The verdict of the log at ``path``. No path or no file: red."""
    if not path:
        return {"green": False, "verdict": "red", "reasons": ["the check wrote no log"], "sections": [],
                "commit": None, "clean": None, "exit": None}
    target = Path(path)
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"green": False, "verdict": "red", "reasons": ["the check log is not there"], "sections": [],
                "commit": None, "clean": None, "exit": None}
    if not text.strip():
        return {"green": False, "verdict": "red", "reasons": ["the check log is empty"], "sections": [],
                "commit": None, "clean": None, "exit": None}
    return verify_text(text, required=required)


def log_tail(path: Optional[str], lines: int = 40) -> str:
    """The last ``lines`` lines of a check log (the builder's round-two prompt)."""
    if not path:
        return ""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(text.splitlines()[-lines:])


__all__ = [
    "HEADER", "QUICK_CHECK_REQUIRED", "SECTION_ORDER", "log_tail", "verify_log", "verify_text",
]
