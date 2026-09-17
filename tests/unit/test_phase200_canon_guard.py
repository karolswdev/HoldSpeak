"""HS-200-44 — the canon guard sees what it claims to guard.

Planned suite ``phase200_canon_guard``.  The UX-canon scanner
(``scripts/ux_canon_scan.py``) underwrites the owner's ruling that every verb
is the library Button.  Until this story its A1 matcher ran ``<button[\\s>/]``
per line over ``content.splitlines()``, so a tag Prettier wrote as ``<button``
alone on its line never matched: it reported 4 of 175 (2026-09-13 audit §10
defect 4).  Four fences:

(a) a fixture holding every ``<button`` shape, and a ``<buttonish>`` decoy,
    is counted exactly;
(b) every other rule the story fixed for the same blindness catches both the
    single-line and the multi-line shape;
(c) over the real ``web/src`` the scanner's A1 equals an INDEPENDENT count
    written here (not the scanner's own function), and reconciles with the
    doc-claims registry's ``raw_button_count()`` by an explained difference;
(d) a plain run writes nothing under the repo.

To prove the fence bites, point it at the pre-fix scanner::

    HS200_CANON_SCANNER=/path/to/old/ux_canon_scan.py \\
        HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_canon_guard.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.unit.doc_claims.registry import raw_button_count

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(os.environ.get("HS200_CANON_SCANNER")
              or REPO_ROOT / "scripts" / "ux_canon_scan.py")
WEB_SRC = REPO_ROOT / "web" / "src"


def _load_scanner():
    spec = importlib.util.spec_from_file_location("hs200_44_ux_canon_scan", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hits(rel: str, body: str, rule: str) -> list[int]:
    mod = _load_scanner()
    return sorted(v.line for v in mod.scan_file(rel, body, body.splitlines())
                  if v.rule == rule)


# ---------------------------------------------------------------------------
# (a) A1 sees every shape of a raw <button>, and only a <button>
# ---------------------------------------------------------------------------

BUTTON_SHAPES = (
    'export function Face() {\n'
    '  return (\n'
    '    <div>\n'
    '      <button onClick={go}>Go</button>\n'                       # line 4: single line
    '      <button\n'                                                # line 5: Prettier
    '        className="x"\n'
    '        onClick={go}\n'
    '      >\n'
    '        Go\n'
    '      </button>\n'
    '      <button/>\n'                                              # line 11: self-closing
    '      <buttonish>not a button</buttonish>\n'                   # line 12: decoy
    '      {/* a comment naming <button> is not a button */}\n'
    '    </div>\n'
    '  );\n'
    '}\n'
)


def test_a1_counts_every_shape_and_not_the_decoy() -> None:
    lines = _hits("features/test/Face.tsx", BUTTON_SHAPES, "A1")
    assert lines == [4, 5, 11], (
        f"A1 found lines {lines}; expected the single-line tag (4), the "
        "Prettier multi-line tag (5) and the self-closing tag (11), and not "
        "the <buttonish> decoy (12) or the comment (13)"
    )


# ---------------------------------------------------------------------------
# (b) every other rule fixed for the same blindness, both shapes
# ---------------------------------------------------------------------------

def test_a3_sentence_sees_a_wrapped_text_node() -> None:
    one_line = (
        'export function Face() {\n'
        '  return <span>Recovered your local draft after relaunch. It remains editable below.</span>;\n'
        '}\n'
    )
    wrapped = (
        'export function Face() {\n'
        '  return (\n'
        '    <span>\n'
        '      Recovered your local draft after relaunch. It remains editable\n'
        '      below.\n'
        '    </span>\n'
        '  );\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", one_line, "A3-sentence") == [2]
    assert _hits("features/test/Face.tsx", wrapped, "A3-sentence") == [4]


def test_a3_sentence_does_not_read_code_between_tags_as_prose() -> None:
    body = (
        'export function Face() {\n'
        '  return cond ? (\n'
        '    <A />\n'
        '  ) : (\n'
        '    // HS-000-00, a comment long enough to look like a sentence, ends here.\n'
        '    <B />\n'
        '  );\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", body, "A3-sentence") == []


def test_a3_prose_sees_a_paragraph_with_attributes_on_their_own_lines() -> None:
    one_line = (
        'export function Face() {\n'
        '  return <p className="hint">This is a helper paragraph with more than forty characters.</p>;\n'
        '}\n'
    )
    wrapped = (
        'export function Face() {\n'
        '  return (\n'
        '    <p\n'
        '      role="status"\n'
        '    >\n'
        '      This is a helper paragraph with more than forty characters.\n'
        '    </p>\n'
        '  );\n'
        '}\n'
    )
    assert 2 in _hits("features/test/Face.tsx", one_line, "A3-prose")
    assert _hits("features/test/Face.tsx", wrapped, "A3-prose") == [3]


def test_raw_ids_sees_a_snake_case_text_node_on_its_own_line() -> None:
    one_line = (
        'export function Face() {\n'
        '  return <span>open_pull_requests</span>;\n'
        '}\n'
    )
    wrapped = (
        'export function Face() {\n'
        '  return (\n'
        '    <span>\n'
        '      open_pull_requests\n'
        '    </span>\n'
        '  );\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", one_line, "raw-ids") == [2]
    assert _hits("features/test/Face.tsx", wrapped, "raw-ids") == [4]


def test_raw_ids_does_not_read_a_generic_and_a_later_tag_as_a_text_node() -> None:
    body = (
        'interface Brief {\n'
        '  sections: Record<string, BriefItem[]>;\n'
        '  is_empty: boolean;\n'
        '}\n'
        'export function Face() {\n'
        '  return <span>ok</span>;\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", body, "raw-ids") == []


def test_raw_ids_sees_an_id_child_on_its_own_line() -> None:
    one_line = (
        'export function Face() {\n'
        '  return <span>{row.id}</span>;\n'
        '}\n'
    )
    wrapped = (
        'export function Face() {\n'
        '  return (\n'
        '    <span>\n'
        '      {row.id}\n'
        '    </span>\n'
        '  );\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", one_line, "raw-ids") == [2]
    assert _hits("features/test/Face.tsx", wrapped, "raw-ids") == [4]


def test_ds6_sees_a_css_declaration_wrapped_over_lines() -> None:
    one_line = ".rail {\n  border-left: 3px solid var(--accent);\n}\n"
    wrapped = ".rail {\n  border-left:\n    3px solid var(--accent);\n}\n"
    assert _hits("features/test/face.css", one_line, "DS6") == [2]
    assert _hits("features/test/face.css", wrapped, "DS6") == [2]


def test_ds6_sees_an_inline_style_wrapped_over_lines() -> None:
    one_line = (
        'export function Face() {\n'
        '  return <div style={{ borderLeft: "3px solid var(--accent)" }} />;\n'
        '}\n'
    )
    wrapped = (
        'export function Face() {\n'
        '  return (\n'
        '    <div\n'
        '      style={{\n'
        '        borderLeft:\n'
        '          "3px solid var(--accent)",\n'
        '      }}\n'
        '    />\n'
        '  );\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", one_line, "DS6") == [2]
    assert _hits("features/test/Face.tsx", wrapped, "DS6") == [5]


def test_a9_sees_a_provider_call_split_over_lines() -> None:
    one_line = (
        'export function Face() {\n'
        '  fetch("/x/discover", { method: "post" });\n'
        '  return null;\n'
        '}\n'
    )
    wrapped = (
        'export function Face() {\n'
        '  fetch(\n'
        '    "/x/discover",\n'
        '    { method: "post" },\n'
        '  );\n'
        '  return null;\n'
        '}\n'
    )
    assert _hits("features/test/Face.tsx", one_line, "A9") == [1]
    assert _hits("features/test/Face.tsx", wrapped, "A9") == [1]


# ---------------------------------------------------------------------------
# (c) the real tree: the scanner's A1 equals an independent count
# ---------------------------------------------------------------------------

FACE_DIRS = ("features/", "pages/cores/", "desk/")
LIBRARY_FILES = ("Signal.tsx", "gadgets.tsx")


def _in_scanner_scope(rel: str) -> bool:
    return (rel.startswith(FACE_DIRS)
            and "__tests__" not in rel and ".test." not in rel
            and "_parked" not in rel
            and not any(k in rel for k in LIBRARY_FILES))


def _in_registry_scope(rel: str) -> bool:
    return not any(k in rel for k in (*LIBRARY_FILES, "__tests__"))


def _independent_raw_buttons(in_scope) -> int:
    """A count written here, not the scanner's: tokenize the whole file."""
    total = 0
    for path in sorted(WEB_SRC.rglob("*.tsx")):
        rel = path.relative_to(WEB_SRC).as_posix()
        if not in_scope(rel):
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for m in re.finditer(r"<button(?=[\s>/])", text):
            line_no = text.count("\n", 0, m.start())
            line = lines[line_no]
            col = m.start() - (text.rfind("\n", 0, m.start()) + 1)
            stripped = line.strip()
            before = line[:col]
            if stripped.startswith(("//", "*", "/*", "{/*")):
                continue
            if "//" in before or "{/*" in before:
                continue
            total += 1
    return total


def test_scanner_a1_equals_an_independent_count_over_web_src() -> None:
    mod = _load_scanner()
    scanner_a1 = int(mod.scan(REPO_ROOT)["totals"]["per_rule"].get("A1", 0))
    independent = _independent_raw_buttons(_in_scanner_scope)
    assert scanner_a1 == independent, (
        f"the scanner reports A1={scanner_a1} but an independent whole-file "
        f"count over the same scope finds {independent}: the guard does not "
        "see what it claims to guard"
    )


def test_scanner_a1_reconciles_with_the_doc_claims_registry() -> None:
    """``raw_button_count()`` (HS-200-46) reads every non-test ``.tsx`` under
    ``web/src`` except the two library files; the scanner reads only the face
    directories and also skips ``*.test.*`` and ``_parked``.  The difference
    is exactly the raw buttons in files the scanner does not scan."""
    mod = _load_scanner()
    scanner_a1 = int(mod.scan(REPO_ROOT)["totals"]["per_rule"].get("A1", 0))
    registry = raw_button_count()
    outside = _independent_raw_buttons(
        lambda rel: _in_registry_scope(rel) and not _in_scanner_scope(rel))
    assert registry == scanner_a1 + outside, (
        f"registry {registry} != scanner {scanner_a1} + {outside} outside the "
        "scanner's scope (design/, _parked, *.test.tsx)"
    )


# ---------------------------------------------------------------------------
# (d) a plain run writes nothing under the repo
# ---------------------------------------------------------------------------

def _tree_fingerprint() -> dict[str, str]:
    """Every file the scanner has ever written, hashed, plus git's view."""
    watched = [
        REPO_ROOT / "tests" / "ux_canon_ceiling.json",
        *sorted((REPO_ROOT / "pm" / "roadmap" / "holdspeak"
                 / "phase-170-the-great-pass" / "assets" / "census").glob("*")),
    ]
    fp = {
        str(p.relative_to(REPO_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in watched if p.is_file()
    }
    status = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True, text=True, timeout=60,
    )
    if status.returncode == 0:
        fp["git status --porcelain"] = status.stdout
    return fp


def test_a_plain_run_writes_nothing_under_the_repo() -> None:
    before = _tree_fingerprint()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)],
        capture_output=True, text=True, timeout=120, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    after = _tree_fingerprint()
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))
    assert not changed, (
        "a plain scanner run changed the tree: " + ", ".join(changed)
        + "\n(every write must sit behind --write-census / --json / --md / "
          "--ranking / --write-ceiling)"
    )
