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

FIELD-LABELS-WORDS (2026-10-30) extends it to the field and check-box
labels (see the last two tests).

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


# FIELD-LABELS-WORDS (2026-10-30) extends the ratchet to the field and
# check-box label species: the StringGadget caption (``.gadget-string-caption``),
# the token check (``.gadget-check-token-face``), the check and its word
# (``.gadget-checkline-word``), the plain check (``.gadget-check``) and the
# group legend (``.gadget-group-label``). The Window grammar: a label is sans
# in sentence case; sections are "never mono uppercase". The caption step's
# caps (UX-CANON C) stays for the eyebrow species (``.surface-eyebrow``) only.

FIELD_LABEL = re.compile(
    r"\.gadget-(?:string-caption|check-token(?:-face)?|checkline-word|check|group-label)(?![\w-])"
)


def test_no_css_rule_uppercases_a_field_or_check_label():
    hits = []
    for path in _product_files(".css"):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for m in RULE.finditer(text):
            selector, body = m.group(1), m.group(2)
            if FIELD_LABEL.search(selector) and re.search(r"text-transform:\s*uppercase", body):
                hits.append(f"{path.relative_to(ROOT)}: {' '.join(selector.split())}")
    assert not hits, "a field or check label rule uppercases its word:\n" + "\n".join(hits)


FIELD_LITERAL = re.compile(r"<(?:CheckGadget|StringGadget|GadgetGroup|PadGadget)\b[^>]*?\blabel=\"([^\"]*)\"", re.S)


def test_no_field_or_check_label_literal_is_written_in_caps():
    hits = []
    for path in _product_files(".tsx"):
        for m in FIELD_LITERAL.finditer(path.read_text(encoding="utf-8")):
            word = m.group(1)
            if _shout(word):
                hits.append(f"{path.relative_to(ROOT)}: label=\"{word}\"")
    assert not hits, "write the field or check label in sentence case:\n" + "\n".join(hits)


# WORDS-LEFTOVERS (2026-10-30) closes the words wave: no CSS rule under
# web/src draws a word in caps, except the species below. Each one is named
# with its reason; a new caps rule fails here.
ALLOWED_CAPS = {
    # UX-CANON §C: the caption step in caps is the eyebrow species, and only it.
    ".surface-eyebrow": "the eyebrow caption (canon)",
    # A key cap: the legend engraved on a key (Settings ▸ the hotkey well).
    ".gadget-keycap": "a key cap legend",
    # The transport key: a square hardware key; its legend is engraved on the key face.
    ".gadget-transport-key": "a key face legend",
    # `::first-letter` capitalises one letter: it MAKES sentence case of a word
    # the wire sends in lower case.
    "::first-letter": "sentence case of a lower-case word",
}


def test_no_css_rule_draws_caps_but_the_named_species():
    hits = []
    for path in _product_files(".css"):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for m in RULE.finditer(text):
            selector, body = " ".join(m.group(1).split()), m.group(2)
            if not re.search(r"text-transform:\s*uppercase", body):
                continue
            if any(allowed in selector for allowed in ALLOWED_CAPS):
                continue
            hits.append(f"{path.relative_to(ROOT)}: {selector}")
    assert not hits, (
        "a CSS rule draws its words in caps (write sentence case; only the eyebrow "
        "and the named key species keep caps):\n" + "\n".join(hits)
    )


def test_no_html_content_word_is_written_in_caps():
    """A `content:` word in CSS (a ::before/::after label) is a product word too."""
    hits = []
    for path in _product_files(".css"):
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for m in re.finditer(r"content:\s*\"([^\"]+)\"", text):
            if _shout(m.group(1)):
                hits.append(f"{path.relative_to(ROOT)}: content: \"{m.group(1)}\"")
    assert not hits, "write the CSS content word in sentence case:\n" + "\n".join(hits)


# `.toUpperCase()` that does NOT shout: the first letter of a word (sentence
# case), a two- or three-letter initial or emblem, a compare or a lookup key.
UPPER_HARMLESS = re.compile(
    r"(?:charAt\(0\)|\[0\]\??|\b(?:c|ch|letter|character|value|m)\b)\.toUpperCase\(\)"
    r"|slice\(0,\s*[23]\)\.toUpperCase\(\)"
    r"|toUpperCase\(\)\s*(?:===|!==|\.startsWith|\])"
)
# The words wave's debt: the files that still uppercase a word for the face,
# with the count of such lines. Strict: a line fixed means the count here goes
# down (or the file leaves); a new file or a higher count fails. The species
# (Token, StateChip, StatusStrip, FoldGadget, StatusBar) send their text through
# `stateWords`, so most of these draw sentence case already; the source should
# say the word.
UPPER_DEBT: dict[str, int] = {
    "desk/attention.ts": 3,
    "desk/components/DeskToolShelf.tsx": 1,
    "desk/components/MissionControlConveyor.tsx": 3,
    "desk/components/UsedLines.tsx": 1,
    "desk/components/workbench/runLifecycle.ts": 2,
    "desk/conductor/store.ts": 1,
    "desk/coverage.ts": 1,
    "desk/documentSends.tsx": 2,
    "desk/firstrun/AgentsCard.tsx": 1,
    "desk/hooks/useWriteReceipt.ts": 5,
    "desk/lane/LaneWindow.tsx": 1,
    "desk/lane/laneWire.ts": 2,
    "desk/missioncontrol.ts": 1,
    "desk/needs/needsFace.ts": 1,
    "desk/needsYou.ts": 4,
    "desk/pullouts/editors/NoteEditor.tsx": 2,
    "desk/surface/egress.ts": 6,
    "desk/surface/kit.tsx": 1,
    "desk/surface/objects/kinds.ts": 1,
    "desk/surface/patterns/ClaimAxes.tsx": 2,
    "desk/surface/patterns/CoverageRow.tsx": 2,
    "desk/surface/plainFailure.ts": 1,
    "desk/surface/send/SendWell.tsx": 2,
    "desk/zoneName.ts": 1,
    "features/channels/channels.ts": 2,
    "features/concierge/useConciergeController.ts": 3,
    "features/project-room/ProjectRoomCore.tsx": 2,
    "features/project-room/RoomPeopleSection.tsx": 1,
    "features/project-room/prepare/PreparePosture.tsx": 2,
    "features/project-room/prepare/model.ts": 1,
    "features/project-room/recall/BeliefCard.tsx": 1,
    "features/project-room/steward/StewardPosture.tsx": 2,
    "features/project-room/update/model.ts": 4,
    "features/runson/RunsOnCore.tsx": 1,
    "features/runson/stateWord.ts": 1,
    "features/runson/useRunsOn.ts": 2,
    "lib/dictationRecovery.ts": 1,
    "meetings/MeetingIntelRecovery.tsx": 1,
    "meetings/summaryRoute.ts": 1,
    "pages/cores/PeopleCore.tsx": 3,
    "pages/cores/ProcessCore.tsx": 1,
    "pages/cores/ProjectsCore.tsx": 1,
    "pages/cores/dictation/DictationSections.tsx": 1,
    "pages/cores/history/MeetingRecord.tsx": 2,
    "pages/cores/history/PreparedResults.tsx": 1,
    "pages/cores/history/useMeetingData.tsx": 1,
    "pages/cores/settingsPrefs.tsx": 4,
}


def _upper_lines() -> dict[str, int]:
    out: dict[str, int] = {}
    for path, _number, line in _product_lines(".ts", ".tsx"):
        stripped = line.strip()
        if "toUpperCase()" not in line or stripped.startswith(("*", "//", "/*")):
            continue
        rel = path.relative_to(WEB).as_posix()
        if rel == "desk/surface/words.ts":  # the one place that cases words
            continue
        if UPPER_HARMLESS.search(line):
            continue
        out[rel] = out.get(rel, 0) + 1
    return out


def test_to_upper_case_only_shrinks():
    now = _upper_lines()
    grew = {k: v for k, v in now.items() if v > UPPER_DEBT.get(k, 0)}
    healed = {k: v for k, v in UPPER_DEBT.items() if now.get(k, 0) < v}
    assert not grew, (
        "a source uppercases a word for the face (say the word in sentence case, "
        "or send it through stateWords):\n" + "\n".join(f"{k}: {v}" for k, v in sorted(grew.items()))
    )
    assert not healed, (
        "a debt line is fixed: lower its count in UPPER_DEBT (strict ratchet):\n"
        + "\n".join(f"{k}: {UPPER_DEBT[k]} -> {now.get(k, 0)}" for k in sorted(healed))
    )
