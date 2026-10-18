"""Betterment Engines E6: the user sees "Engines", never "Runs on" or "Concierge".

One name everywhere (docs/internal/betterment/engines/DESIGN.md §"The words"):
the window title, the Settings row, the palette and the docs say Engines.
Routes and code names stay (`configure-runs-on`, `features/runson`,
`/api/concierge/*`, `useConciergeController`); only what the user sees changes.

This guard reads every string the desk can draw (string literals, template text
and JSX text in `web/src`, outside tests and parked faces; the scanner is the
Automations name guard's) and the user docs (`README.md`, `docs/*.md`). It
fails on "Runs on" / "RUNS ON" or "Concierge" / "CONCIERGE" as words. Plain
English stays: "the summary runs on <host>" is lower case and is not the name.
"""
from __future__ import annotations

import re
from pathlib import Path

from tests.unit.test_automation_name_guard import JSX_TEXT, _ui_files, split

ROOT = Path(__file__).resolve().parents[2]

# The old names as words: not inside an identifier, a class name, a path or a
# key (those carry - _ . / : or a letter beside the word).
OLD_NAME = re.compile(r"(?<![\w\-./:#@])(?:Runs on|RUNS ON|Concierge|CONCIERGE)(?![\w\-/:@])")
# JSX text that runs into an expression (`Runs on{" "}{places}`) ends at `{`.
JSX_LEAD = re.compile(r">([^<>{}();=\[\]]*)\{")
# The glossary keeps one row for each former name, so a reader can find it.
GLOSSARY_FORMER = re.compile(r"^\| (?:Concierge|Runs on) \| The former name of ")


def ui_offenders() -> list[str]:
    found: list[str] = []
    for path in _ui_files():
        literals, code = split(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT).as_posix()
        for line, text in literals:
            if OLD_NAME.search(text):
                found.append(f"{rel}:{line}: {text.strip()[:120]!r}")
        for pattern in (JSX_TEXT, JSX_LEAD):
            for match in pattern.finditer(code):
                if OLD_NAME.search(match.group(1)):
                    line = code.count("\n", 0, match.start()) + 1
                    found.append(f"{rel}:{line}: JSX {match.group(1).strip()[:120]!r}")
    return sorted(set(found))


def doc_offenders() -> list[str]:
    found: list[str] = []
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        rel = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line) and not GLOSSARY_FORMER.match(line):
                found.append(f"{rel}:{number}: {line.strip()[:120]}")
    return found


def test_the_guard_reads_names_and_skips_code_and_plain_english() -> None:
    sample = (
        'const a = "Runs on"; const b = `Configure Runs on`;\n'
        'const c = "configure-runs-on"; const d = "/api/concierge/detect";\n'
        "const e = <p>Open the Concierge</p>; const f = <span>Runs on{\" \"}{x}</span>;\n"
        'const g = "Summary runs on this host"; type H = ConciergeController;\n'
        'const i = "RUNS ON LIVES IN MODELS";\n'
    )
    literals, code = split(sample)
    shown = [text for _, text in literals if OLD_NAME.search(text)]
    assert shown == ["Runs on", "Configure Runs on", "RUNS ON LIVES IN MODELS"]
    jsx = sorted({m.group(1) for p in (JSX_TEXT, JSX_LEAD) for m in p.finditer(code) if OLD_NAME.search(m.group(1))})
    assert jsx == ["Open the Concierge", "Runs on"]


def test_no_built_ui_string_says_runs_on_or_concierge() -> None:
    found = ui_offenders()
    assert not found, (
        'The user sees "Engines" (betterment E6). Rename these visible strings; '
        "routes and code names stay:\n" + "\n".join(found)
    )


def test_no_user_doc_says_runs_on_or_concierge() -> None:
    found = doc_offenders()
    assert not found, (
        'The user docs say "Engines" (betterment E6); the glossary keeps one '
        '"former name" row for each old name:\n' + "\n".join(found)
    )
