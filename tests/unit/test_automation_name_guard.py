"""Betterment Automations A1: the user sees "Automation", never "Workbench".

The owner's name for the feature is "Automations" (docs/internal/betterment/
workbench/RECIPE.md, slice A1). Code names, routes, the stored kind and the
MCP tools stay `workbench`; only what the user sees changes. This guard reads
every string the desk can draw (string literals, template text and JSX text in
`web/src`, outside tests and parked faces) and fails on a "workbench" word in
any case. It skips code identifiers (`workbench`, `surface-workbenches`,
`/api/workbenches`, `WorkbenchWindow`) and the Delivery Workbench dev tooling.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "web" / "src"

# A "workbench" word that stands alone: not inside an identifier, a class
# name, a path or a dotted key (those carry - _ . / : or a letter beside it).
WORD = re.compile(r"(?<![\w\-./:#@])workbench(?:es)?(?![\w\-/:@])", re.IGNORECASE)
# The dev tooling keeps its own name (Delivery Workbench, `.githooks/dw`).
EXCLUDED = re.compile(r"Delivery Workbench", re.IGNORECASE)
# A lower-case word in a literal with no space is a key ("workbench"), not text.
CAPITAL = re.compile(r"(?<![\w\-./:#@])Workbench(?:es)?(?![\w\-/:@])")
JSX_TEXT = re.compile(r">([^<>{}();=\[\]]*)<")
REGEX_PRECEDERS = set("(,=:[!&|?{;+-*%>~^") | {""}


def _ui_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(WEB_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        rel = path.relative_to(WEB_SRC).as_posix()
        if (
            "__tests__/" in rel
            or rel.startswith("test/")
            or "/_parked/" in f"/{rel}"
            or re.search(r"\.test\.tsx?$", rel)
            or rel.endswith(".d.ts")
        ):
            continue
        files.append(path)
    return files


def split(source: str) -> tuple[list[tuple[int, str]], str]:
    """Return (string literals with their line, code with literals blanked).

    A small TS/TSX scanner: line and block comments, '…', "…", `…` with
    ${…} nesting, and regex literals. Comments are dropped; code keeps its
    newlines so JSX text still has a line number.
    """
    literals: list[tuple[int, str]] = []
    code: list[str] = []
    i, n, line = 0, len(source), 1
    brace_stack: list[int] = []  # depth of `{` inside each open ${

    def last_significant() -> str:
        for chunk in reversed(code):
            stripped = chunk.rstrip()
            if stripped:
                return stripped[-1]
        return ""

    def read_template(start: int) -> int:
        nonlocal line
        j = start
        buf: list[str] = []
        start_line = line
        while j < n:
            c = source[j]
            if c == "\\":
                buf.append(source[j : j + 2])
                j += 2
                continue
            if c == "`":
                literals.append((start_line, "".join(buf)))
                return j + 1
            if c == "$" and j + 1 < n and source[j + 1] == "{":
                literals.append((start_line, "".join(buf)))
                buf = []
                code.append(" ")
                brace_stack.append(0)
                return -(j + 2)  # back to code inside the template
            if c == "\n":
                line += 1
            buf.append(c)
            j += 1
        literals.append((start_line, "".join(buf)))
        return n

    while i < n:
        c = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if c == "\n":
            line += 1
            code.append(c)
            i += 1
        elif c == "/" and nxt == "/":
            while i < n and source[i] != "\n":
                i += 1
        elif c == "/" and nxt == "*":
            end = source.find("*/", i + 2)
            end = n if end < 0 else end + 2
            chunk = source[i:end]
            line += chunk.count("\n")
            code.append("\n" * chunk.count("\n"))
            i = end
        elif c == "/" and last_significant() in REGEX_PRECEDERS:
            j, in_class = i + 1, False
            while j < n and source[j] != "\n":
                if source[j] == "\\":
                    j += 2
                    continue
                if source[j] == "[":
                    in_class = True
                elif source[j] == "]":
                    in_class = False
                elif source[j] == "/" and not in_class:
                    break
                j += 1
            if j >= n or source[j] != "/":
                code.append(c)  # not a regex after all (a JSX `/>`, a division)
                i += 1
                continue
            code.append(" ")
            i = j + 1
        elif c in "'\"":
            j, buf = i + 1, []
            while j < n and source[j] != c and source[j] != "\n":
                if source[j] == "\\":
                    buf.append(source[j : j + 2])
                    j += 2
                    continue
                buf.append(source[j])
                j += 1
            literals.append((line, "".join(buf)))
            code.append(" ")
            i = j + 1
        elif c == "`":
            r = read_template(i + 1)
            if r < 0:
                i = -r
            else:
                code.append(" ")
                i = r
        elif c == "{" and brace_stack:
            brace_stack[-1] += 1
            code.append(c)
            i += 1
        elif c == "}" and brace_stack:
            if brace_stack[-1] == 0:
                brace_stack.pop()
                r = read_template(i + 1)
                if r < 0:
                    i = -r
                else:
                    code.append(" ")
                    i = r
            else:
                brace_stack[-1] -= 1
                code.append(c)
                i += 1
        else:
            code.append(c)
            i += 1
    return literals, "".join(code)


def _shown(text: str) -> bool:
    text = EXCLUDED.sub("", text)
    if not WORD.search(text):
        return False
    # A lower-case word alone is a key; text has a space or a capital.
    return bool(CAPITAL.search(text)) or bool(re.search(r"\s", text.strip()))


def offenders() -> list[str]:
    found: list[str] = []
    for path in _ui_files():
        literals, code = split(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT).as_posix()
        for line, text in literals:
            if _shown(text):
                found.append(f"{rel}:{line}: {text.strip()[:120]!r}")
        for match in JSX_TEXT.finditer(code):
            text = match.group(1)
            if WORD.search(EXCLUDED.sub("", text)):
                line = code.count("\n", 0, match.start()) + 1
                found.append(f"{rel}:{line}: JSX {text.strip()[:120]!r}")
    return found


def test_the_scanner_reads_literals_jsx_and_skips_code() -> None:
    sample = (
        'const a = "New Workbench"; // Workbench in a comment\n'
        "const b = `${n} workbench runs`;\n"
        'const c = "workbench"; const d = "/api/workbenches"; const e = "desk-workbench-window";\n'
        "const f = /run this workbench/i; const g = <p>Open the Workbench</p>;\n"
        'const h = "Delivery Workbench project"; type W = WorkbenchWindow;\n'
    )
    literals, code = split(sample)
    shown = [text for _, text in literals if _shown(text)]
    assert shown == ["New Workbench", " workbench runs"]
    jsx = [m.group(1) for m in JSX_TEXT.finditer(code) if WORD.search(m.group(1))]
    assert jsx == ["Open the Workbench"]


def test_no_built_ui_string_says_workbench() -> None:
    found = offenders()
    assert not found, (
        'The user sees "Automation" (betterment A1). Rename these visible '
        "strings; code names, routes and the stored kind stay `workbench`:\n"
        + "\n".join(found)
    )


def test_starter_names_say_no_agent() -> None:
    from holdspeak.workbench_templates import list_templates

    for template in list_templates():
        # The starter is the automation; its agent (the recipe) keeps its name.
        assert "Agent" not in template["name"], template["name"]
        assert "workbench" not in template["name"].lower(), template["name"]
        for item in template.get("starter_items", []):
            shown = f"{item.get('title', '')} {item.get('body', '')}".lower()
            assert "workbench" not in shown, item
