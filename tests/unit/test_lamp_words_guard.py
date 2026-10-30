"""LAMPS-WORDS (2026-10-30): the ratchet for lamp text.

Every lamp says its word in sentence case (UX-CANON sentence case; the
Window grammar: a state is a dot and a word). The species does it once:
LampGadget sends its label through ``stateWords`` and ``.gadget-lamp``
draws the word as it is. This guard keeps the shout from coming back:

- no CSS rule that styles a ``.gadget-lamp`` uppercases it;
- no ``<LampGadget label="...">`` literal is written in caps (write the
  word: ``label="Offline"``, never ``label="OFFLINE"``).

EGRESS-CHIP-WORDS (2026-10-30) extends the ratchet to the chip species
(``.gadget-chip``, ``.gadget-chip-egress``, the SecretRow ``Set`` chip):
EgressChip sends its word through ``stateWords``; a host is shown as typed.

- no CSS rule that styles a chip changes its case (upper or lower);
- no ``<EgressChip label="...">`` literal is written in caps;
- no ``.toUpperCase()`` on a host, a site, a vendor or an agent name;
- no host literal is written in caps (``"GITHUB.COM"``).

ENGINES-WORDS-LAST (2026-10-30) extends it to the Engines window
(``RunsOnCore.tsx``, ``ModelLibraryCore.tsx``): StateChip and Token send
their words through ``stateWords``, and the source says the word too.

- no ``<StateChip label="...">`` literal there is written in caps
  (``label="Added"``, never ``label="ADDED"``);
- no ``<Token>`` there holds a caps literal (``No model matches``).

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


def test_no_css_rule_changes_the_case_of_a_chip():
    hits = []
    for path in _product_files(".css"):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for m in RULE.finditer(text):
            selector, body = m.group(1), m.group(2)
            if re.search(r"gadget-(?:chip|secret)", selector) and re.search(
                r"text-transform:\s*(?:uppercase|lowercase)", body
            ):
                hits.append(f"{path.relative_to(ROOT)}: {selector.strip()}")
    assert not hits, "a chip rule changes the case of its word:\n" + "\n".join(hits)


CHIP_LITERAL = re.compile(r"<EgressChip\b[^>]*?\blabel=\"([^\"]*)\"", re.S)


def test_no_chip_label_literal_is_written_in_caps():
    hits = []
    for path in _product_files(".tsx"):
        for m in CHIP_LITERAL.finditer(path.read_text(encoding="utf-8")):
            word = m.group(1)
            if re.search(r"\b[A-Z]{3,}\b", word) and word == word.upper():
                hits.append(f"{path.relative_to(ROOT)}: label=\"{word}\"")
    assert not hits, "write the chip's word in sentence case:\n" + "\n".join(hits)


# A host, a site, a vendor or an agent name, then `.toUpperCase()`:
# `clone.host.toUpperCase()`, `endpointHostPort(url).toUpperCase()`,
# `AGENT_NAME[id].toUpperCase()`, `${engine.host}${suffix}`.toUpperCase().
HOST_UPPER = re.compile(
    r"(?:[\w.]*(?:[hH]ost|[sS]ite\b|[vV]endor|[dD]omain)[\w.]*(?:\s*\?\?\s*\"[^\"]*\")?\)?"
    r"|(?:AGENT_NAME|PROVIDER_NAME)\[[^\]]+\]"
    r"|endpointHostPort\([^)]*\)"
    r"|`[^`]*\$\{[^}]*(?:host|Host|tool)[^}]*\}[^`]*`"
    r"|\btool\b)\s*\.toUpperCase\(\)"
)


def _product_lines(*suffixes: str):
    for path in _product_files(*suffixes):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            yield path, number, line


def test_no_host_or_vendor_is_uppercased():
    hits = [
        f"{path.relative_to(ROOT)}:{number}: {line.strip()}"
        for path, number, line in _product_lines(".ts", ".tsx")
        if HOST_UPPER.search(line)
    ]
    assert not hits, "show a host or a vendor as typed (no .toUpperCase()):\n" + "\n".join(hits)


CAPS_HOST = re.compile(r"\"(?:[A-Z0-9-]+\.)+(?:COM|NET|ORG|IO|AI|CO|DEV)\b[^\"]*\"")


def test_no_host_literal_is_written_in_caps():
    hits = [
        f"{path.relative_to(ROOT)}:{number}: {line.strip()}"
        for path, number, line in _product_lines(".ts", ".tsx")
        if CAPS_HOST.search(line)
    ]
    assert not hits, "write a host as typed (github.com, not GITHUB.COM):\n" + "\n".join(hits)


ENGINES_FILES = (
    WEB / "features" / "runson" / "RunsOnCore.tsx",
    WEB / "pages" / "cores" / "ModelLibraryCore.tsx",
)
STATE_LITERAL = re.compile(r"<StateChip\b[^>]*?\blabel=\"([^\"]*)\"", re.S)
TOKEN_LITERAL = re.compile(r"<Token\b[^>]*>([^<{]*)<")


def _shout(word: str) -> bool:
    return bool(re.search(r"\b[A-Z]{3,}\b", word)) and word == word.upper()


def test_no_engines_chip_or_token_literal_is_written_in_caps():
    hits = []
    for path in ENGINES_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in (STATE_LITERAL, TOKEN_LITERAL):
            for m in pattern.finditer(text):
                word = m.group(1).strip()
                if word and _shout(word):
                    hits.append(f"{path.relative_to(ROOT)}: {word!r}")
    assert not hits, "write the Engines window's words in sentence case:\n" + "\n".join(hits)
