"""LAMPS-WORDS (2026-10-30): the ratchet for lamp text.

Every lamp says its word in sentence case (UX-CANON sentence case; the
Window grammar: a state is a dot and a word). The species does it once:
LampGadget sends its label through ``stateWords`` and ``.gadget-lamp``
draws the word as it is. This guard keeps the shout from coming back:

- no CSS rule that styles a ``.gadget-lamp`` uppercases it;
- no ``<LampGadget label="...">`` literal is written in caps (write the
  word: ``label="Offline"``, never ``label="OFFLINE"``).

Parked files (``_parked``) and tests are not product faces.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "src"


def _product_files(*suffixes: str) -> list[Path]:
    out = []
    for path in WEB.rglob("*"):
        if path.suffix not in suffixes:
            continue
        rel = path.relative_to(WEB).as_posix()
        if "_parked" in rel or "__tests__" in rel or ".test." in path.name:
            continue
        out.append(path)
    return out


RULE = re.compile(r"([^{}]*)\{([^{}]*)\}")


def test_no_css_rule_uppercases_a_lamp():
    hits = []
    for path in _product_files(".css"):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for m in RULE.finditer(text):
            selector, body = m.group(1), m.group(2)
            if "gadget-lamp" in selector and re.search(r"text-transform:\s*uppercase", body):
                hits.append(f"{path.relative_to(ROOT)}: {selector.strip()}")
    assert not hits, "a lamp rule uppercases its word:\n" + "\n".join(hits)


LAMP_LITERAL = re.compile(r"<LampGadget\b[^>]*?\blabel=\"([^\"]*)\"", re.S)


def test_no_lamp_label_literal_is_written_in_caps():
    hits = []
    for path in _product_files(".tsx"):
        for m in LAMP_LITERAL.finditer(path.read_text(encoding="utf-8")):
            word = m.group(1)
            # Two or more caps letters in a row that make a whole word of
            # three letters or more: a shout, not an acronym like PR or CI.
            if re.search(r"\b[A-Z]{3,}\b", word) and word == word.upper():
                hits.append(f"{path.relative_to(ROOT)}: label=\"{word}\"")
    assert not hits, "write the lamp's word in sentence case:\n" + "\n".join(hits)
