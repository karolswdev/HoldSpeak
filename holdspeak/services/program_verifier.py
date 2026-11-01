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
from typing import Any, Iterable, Mapping, Optional

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


def verify_requirement_text(text: str, *, expect: Optional[str] = None) -> dict[str, Any]:
    """PG-REQ §5: the requirement form, for a command that is not the quick
    check (it prints no ``== section`` lines and no verdict line). Met only
    when ALL of these hold:

    1. the log names the commit and the worktree was clean at the start;
    2. the engine's own footer ``program-check: exit 0`` is there (the
       engine wrote it from its own process: its receipt, not the agent's
       claim);
    3. no output line is red by :func:`_red_line` (``FAILED``, ``ERROR``,
       "n failed" with n > 0);
    4. when ``expect`` (a regular expression) is named, a line matches it.
    """
    reasons: list[str] = []
    commit: Optional[str] = None
    clean: Optional[bool] = None
    exit_code: Optional[int] = None
    footer = False
    last_result = ""
    matched = expect is None
    pattern = re.compile(expect) if expect else None
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
                footer = True
                try:
                    exit_code = int(body.split(" ", 1)[1])
                except ValueError:
                    exit_code = None
            continue
        if _red_line(line):
            reasons.append(f"a line is red: {line.strip()[:160]}")
        if _result_line(line):
            last_result = line.strip()
        if pattern is not None and pattern.search(line):
            matched = True
    if not commit:
        reasons.append("the log names no commit")
    if clean is False:
        reasons.append("the worktree had changes that were not committed when the command started")
    elif clean is None:
        reasons.append("the log does not say the worktree was clean")
    if not footer:
        reasons.append("the log has no exit line of the engine")
    elif exit_code != 0:
        reasons.append(f"the command ended with exit {exit_code if exit_code is not None else 'none'}")
    if not matched:
        reasons.append(f"no line matches {expect}")
    return {"met": not reasons, "reasons": reasons[:6], "commit": commit, "clean": clean, "exit": exit_code,
            "line": last_result}


def verify_requirement_log(path: Optional[str], expect: Optional[str] = None) -> dict[str, Any]:
    """The requirement form of the log at ``path``. No path or no file: not Met."""
    empty = {"met": False, "commit": None, "clean": None, "exit": None, "line": ""}
    if not path:
        return {**empty, "reasons": ["the command wrote no log"]}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {**empty, "reasons": ["the log is not there"]}
    if not text.strip():
        return {**empty, "reasons": ["the log is empty"]}
    return verify_requirement_text(text, expect=expect)


#: PG-LANG §6.3 (LANG11): the units a Measure converts between, to its bound's.
_UNIT_SCALE = {
    "ms": ("time", 0.001), "s": ("time", 1.0), "sec": ("time", 1.0), "secs": ("time", 1.0), "second": ("time", 1.0),
    "seconds": ("time", 1.0), "min": ("time", 60.0), "mins": ("time", 60.0), "minute": ("time", 60.0),
    "minutes": ("time", 60.0), "h": ("time", 3600.0), "kb": ("size", 1e3), "mb": ("size", 1e6), "gb": ("size", 1e9),
    "b": ("size", 1.0), "bytes": ("size", 1.0),
}
#: The bound's operator in his words (the result line).
OP_WORDS = {"<": "under", "<=": "at most", ">": "over", ">=": "at least", "=": "equal to"}
_OPS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
        "=": lambda a, b: abs(a - b) < 1e-9}


def _number_words(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.3g}" if abs(value) < 1000 else f"{value:.0f}"


def _in_unit(value: float, unit: str, want: str) -> Optional[float]:
    """``value`` in ``unit`` as ``want`` (``None`` when they do not convert)."""
    unit, want = unit.lower(), want.lower()
    if not want or not unit or unit == want:
        return value
    have, need = _UNIT_SCALE.get(unit), _UNIT_SCALE.get(want)
    if have is None or need is None or have[0] != need[0]:
        return None
    return value * have[1] / need[1]


def verify_measure_text(text: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    """PG-LANG §6.3 (LANG11): a Measure's log. The requirement form holds
    (:func:`verify_requirement_text`: the commit, a clean tree, the engine's
    ``exit 0``, no red line, ``expect`` when named), and the LAST line that
    names the metric and then a number gives the value, in the bound's unit
    when it converts. Met when the value meets the bound. ``line`` is the
    result in his words: "Measured 1.4 s, under 2 s"."""
    metric = str(spec.get("metric") or "").strip()
    op = str(spec.get("op") or "")
    unit = str(spec.get("unit") or "")
    try:
        bound = float(spec.get("bound"))
    except (TypeError, ValueError):
        bound = None
    base = verify_requirement_text(text, expect=spec.get("expect") or None)
    reasons = list(base["reasons"])
    bound_words = f"{OP_WORDS.get(op, op)} {_number_words(bound) if bound is not None else '?'}" + (f" {unit}" if unit else "")
    if not metric or op not in _OPS or bound is None:
        return {**base, "met": False, "reasons": ["the measure has no bound to compare with"], "value": None,
                "line": "Not measured: the measure has no bound"}
    pattern = re.compile(rf"(?<![\w-]){re.escape(metric)}(?![\w-])\D*?(-?\d+(?:\.\d+)?)\s*([A-Za-z%]+)?", re.I)
    found: Optional[tuple[float, str]] = None
    for raw in text.splitlines():
        if raw.startswith(HEADER):
            continue
        for match in pattern.finditer(raw):
            found = (float(match.group(1)), match.group(2) or "")
    if found is None:
        reasons.append(f"the command printed no {metric} number")
        line = f"Not measured: {reasons[0]}"  # a command that did not run says so first
        return {**base, "met": False, "reasons": reasons[:6], "value": None, "line": line}
    value = _in_unit(found[0], found[1] if found[1].lower() in _UNIT_SCALE else "", unit)
    if value is None:
        reasons.append(f"the command printed {found[1]}, which is not {unit}")
        return {**base, "met": False, "reasons": reasons[:6], "value": None, "line": f"Not measured: {reasons[0]}"}
    measured = f"Measured {_number_words(value)}" + (f" {unit}" if unit else "")
    within = _OPS[op](value, bound)
    if not within:
        reasons.append(f"{metric} is {_number_words(value)}{(' ' + unit) if unit else ''}, not {bound_words}")
    if base["reasons"]:
        line = f"Not measured: {base['reasons'][0]}"
    else:
        line = f"{measured}, {bound_words}" if within else f"{measured}, not {bound_words}"
    return {**base, "met": not reasons, "reasons": reasons[:6], "value": value, "line": line}


def verify_measure_log(path: Optional[str], spec: Mapping[str, Any]) -> dict[str, Any]:
    """The Measure form of the log at ``path``. No path or no file: not Met,
    the reason in words ("Not measured: the command wrote no log")."""
    empty = {"met": False, "commit": None, "clean": None, "exit": None, "value": None}
    if not path:
        return {**empty, "reasons": ["the command wrote no log"], "line": "Not measured: the command did not run"}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {**empty, "reasons": ["the log is not there"], "line": "Not measured: the log is not there"}
    return verify_measure_text(text, spec)


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
    "HEADER", "OP_WORDS", "QUICK_CHECK_REQUIRED", "SECTION_ORDER", "log_tail", "verify_log", "verify_measure_log",
    "verify_measure_text", "verify_requirement_log", "verify_requirement_text", "verify_text",
]
