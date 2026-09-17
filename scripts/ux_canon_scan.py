#!/usr/bin/env python3
"""
ux_canon_scan.py -- Mechanical UX-canon violation scanner for HoldSpeak faces.

Scans web/src (tsx + css; skips __tests__ and *.test.*) for canon violations
per the owner's rulings in docs/internal/UX-CANON.md, the surface contract,
and the design system.

Usage:
    python scripts/ux_canon_scan.py [--root DIR]
        [--write-census DIR | --json PATH --md PATH --ranking PATH]
        [--write-ceiling PATH [--ceiling-reason TEXT]]

A plain run prints the totals and writes NOTHING.  Every file the scanner
produces is behind an explicit flag (HS-200-44): a guard that dirtied the
tree on every run is how other phases' evidence was rewritten by accident.

Outputs (only when asked for):
    violations.md   — per-face section with file:line and rule
    violations.json — machine-readable for guards
    ranking.md      — faces by Tuesday use x canon debt
    the ceiling     — the ratchet file the guard test reads; a per-rule
                      number may fall freely and may only RISE with a new
                      --ceiling-reason (the dated, down-only shape of HS-200-03)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Face classification
# ---------------------------------------------------------------------------

FACE_DIRS = ("features/", "pages/cores/", "desk/")

# Tuesday-use ranking from THE-TUESDAY-ARC.md section 0 and the 169 recon.
# Higher = more Tuesday use.  Surfaces a Senior Architect managing 3 people
# meets weekly come first.
TUESDAY_USE: dict[str, int] = {
    # Tier 1 -- weekly contact surfaces
    "settingsModels": 8,
    "ConnectionsPane": 8,
    "SettingsCore": 7,
    "DoorCore": 7,
    "ProjectRoomCore": 7,
    "HistoryCore": 6,       # Meetings + aftercare
    "MeetingDetail": 6,
    "PeopleCore": 6,
    "ThreadPullout": 6,
    "DeskComposer": 6,      # the Thread / Ask
    "AttentionDrawer": 5,   # the shade / attention
    "SystemShade": 5,
    "SpeakFace": 5,         # Speak
    "DictationCore": 5,
    # Tier 2 -- regular but not weekly
    "SetupCore": 4,
    "SetupRoot": 4,
    "SetupInterview": 4,
    "ActivationReview": 4,
    "ReviewPosture": 4,
    "StewardPosture": 4,
    "UpdatePosture": 4,
    "Chair": 4,
    "ChairHome": 4,
    "WorkbenchWindow": 3,
    "CadenceCore": 3,
    "ActivityCore": 3,
    "ModelLibraryCore": 3,
    "AssignmentEditor": 3,
    "frontDoor": 3,
    "DeskChrome": 3,
    "DeskWindow": 3,
    # Tier 3 -- infrequent
    "CommandsCore": 2,
    "CompanionCore": 2,
    "LiveCore": 2,
    "ProcessCore": 2,
    "CalendarSnapshotReviewCore": 2,
    "RuntimeDocsCore": 1,
    "TopologyMapView": 1,
    "ComponentsCore": 1,
    "ConstitutionalContextCore": 1,
    "CapabilityAssignmentsCore": 1,
    "settingsTts": 1,
    "settingsBespoke": 1,
    "settingsPrefs": 1,
}

# Weights per rule class for debt scoring.
# A1 modal/raw button/sentence = 3;  zero counter/egress/rail = 2;  others = 1
RULE_WEIGHTS: dict[str, int] = {
    "A1": 3,   # Raw <button> (not the library Button)
    "A3-sentence": 3,   # Sentences in JSX text
    "A3-prose": 3,      # Prose helpers
    "A4": 3,   # Modals
    "A8": 2,   # Counters of zero
    "A9": 2,   # Missing egress
    "B": 1,    # Non-library controls
    "DS6": 2,  # Accent left rails
    "C": 1,    # Type-step collapse
    "raw-ids": 1,  # Raw kinds/ids on the face
    "emoji": 1,    # Emoji/dingbats in JSX text
    "mic": 1,      # Missing MicButton on text input
}


def classify_face(rel: str) -> str | None:
    """Return a face name from a relative path, or None if not a face file."""
    # Only tsx files are faces (css files contribute to their parent face)
    if not rel.endswith(".tsx"):
        return None
    stem = Path(rel).stem
    # Files under features/**, pages/cores/**, desk/** that render
    # a window/core/lane
    for d in FACE_DIRS:
        if rel.startswith(d):
            return stem
    return None


def face_for_file(rel: str) -> str | None:
    """For any file (tsx or css), return the face it belongs to."""
    if rel.endswith(".tsx"):
        return classify_face(rel)
    # CSS: the face is the nearest tsx in the same directory, or the directory name
    parent = str(Path(rel).parent)
    stem = Path(rel).stem
    return stem  # best effort: surface.css -> surface


# ---------------------------------------------------------------------------
# The voice law (rule `mic`) — Constitution Article IV.1
# ---------------------------------------------------------------------------
# "Every text input can be spoken into.  The mic is an affordance of the OS,
# not of any one feature."
#
# HS-176-04 (ruling R9) makes the rule PER ELEMENT.  Every raw `<input>` that
# takes dictatable text and every `<textarea>` under web/src is counted, plus
# every `mic={false}` on a mic-bearing library species — an opt-out is a hole
# the raw-element count cannot see.  An element is COVERED when an explicit
# `<MicButton>` renders inside the same component function (the three species
# render their own).  Everything else is named in MIC_ALLOWLIST with a reason.
#
# The four defects the old file-scoped flag carried (design D2(d).2):
#   (i)   `<textarea` never matched;
#   (ii)  `<StringGadget` counted as an uncovered input (it is covered by
#         definition);
#   (iii) one violation per file however many elements were bare;
#   (iv)  gated on classify_face, so non-face files were never checked.

# `<input type="...">` values that are not dictatable text.  An absent or
# dynamic type is treated as text (StringGadget's own input is `type={type}`).
MIC_TEXT_TYPES = frozenset({"text", "search", "url", "email", "tel"})

# The library species that render a MicButton by default (gadgets.tsx:243,
# gadgets.tsx:315, Surface.tsx:1070).
MIC_SPECIES = ("StringGadget", "PadGadget", "EditInPlace")

# The named allowlist: (path relative to web/src, needle, reason).
#
# The needle is matched against the element's NEIGHBOURHOOD — its own tag text
# plus the two preceding lines — never a line number (line-anchored fences
# move).  Every entry is one element of the HS-176-01 census
# (pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/mic-census-176.md
# §2c and §3): 19 raw non-text controls + 4 justified `mic={false}` opt-outs
# = 23, plus the 24th added by ruling R13 (the Speak face's utterance well).
MIC_ALLOWLIST: tuple[tuple[str, str, str], ...] = (
    # -- 19 raw elements the census names (census §2c) ----------------------
    ("components/signal/Signal.tsx", 'hs-control ${props.className',
     "TextInput library primitive; zero call sites in web/src (dead export)"),
    ("components/signal/Signal.tsx", "signal-textarea",
     "TextArea library primitive; zero call sites in web/src (dead export)"),
    ("desk/surface/gadgets.tsx", "gadget-check-token",
     "CheckGadget (token variant) checkbox — not a text input"),
    ("desk/surface/gadgets.tsx", 'className="gadget-check"',
     "CheckGadget checkbox — not a text input"),
    ("desk/surface/gadgets.tsx", "gadget-mx-row",
     "MxRadio radio — not a text input"),
    ("desk/surface/gadgets.tsx", "gadget-stepper",
     "StepperGadget number — a stepped quantity, not dictatable text"),
    ("desk/surface/gadgets.tsx", 'type="range"',
     "PropGadget slider — not a text input"),
    ("desk/surface/patterns/ChoiceCardGroup.tsx", "surface-choice-card-radio",
     "ChoiceCard radio — not a text input"),
    ("desk/pullouts/ThreadPullout.tsx", "thread-elicitation-boolean",
     "Elicitation boolean checkbox — not a text input"),
    ("desk/pullouts/ThreadPullout.tsx", 'type="number"',
     "Elicitation numeric field — a number, not dictatable text"),
    ("desk/components/ScheduleCreateWindow.tsx", 'type="datetime-local"',
     "Date/time picker — a calendar value, not dictatable text"),
    ("features/project-room/review/ReviewPosture.tsx", "review-defer-date",
     "Defer-until date picker — a calendar value, not dictatable text"),
    ("pages/cores/ModelLibraryCore.tsx", "Hosted provider",
     "Provider key (password) — a secret is never dictated"),
    ("pages/cores/ModelLibraryCore.tsx", "Endpoint provider",
     "Provider key (password) — a secret is never dictated"),
    ("pages/cores/ModelLibraryCore.tsx", 'accept=".gguf,.mlx"',
     "Model file chooser — an OS file picker, not a text input"),
    ("pages/cores/ModelLibraryCore.tsx", "name={groupName}",
     "Model row selection radio — not a text input"),
    ("pages/cores/TopologyMapView.tsx", 'placeholder="Key (optional)"',
     "Provider key (password) — a secret is never dictated"),
    ("pages/cores/TopologyMapView.tsx", 'placeholder="Provider"',
     "Provider key (password) — a secret is never dictated"),
    ("pages/cores/history/ImportSection.tsx", "audio/*,.wav",
     "Audio/transcript import chooser — an OS file picker, not a text input"),
    # -- 4 justified `mic={false}` opt-outs (census §3) ---------------------
    ("desk/components/ScheduleCreateWindow.tsx", 'label="Cron expression"',
     "Cron syntax field — a five-token expression, not dictatable prose"),
    ("pages/cores/CalendarSnapshotReviewCore.tsx", 'key="start"',
     "HH:MM time field — a clock value, not dictatable prose"),
    ("pages/cores/CalendarSnapshotReviewCore.tsx", 'key="end"',
     "HH:MM time field — a clock value, not dictatable prose"),
    ("pages/cores/SettingsCore.tsx", 'key="symbol"',
     "Glyph field (a single symbol such as →) — not dictatable prose"),
    # -- the 24th, ruling R13 (HS-176-05) ----------------------------------
    ("pages/cores/dictation/SpeakFace.tsx", 'label="Utterance"',
     "The Talk transport is this face's mic authority (Article IV.3, R13)"),
)


def _mic_tag_text(content: str, start: int, limit: int = 4000) -> str:
    """The opening tag beginning at `start`, across however many lines.

    Stops at the first `>` outside a string and outside a `{...}` expression,
    so `onChange={(e) => ...}` and `placeholder="https://…"` never end it.
    """
    depth = 0
    quote: str | None = None
    end = min(len(content), start + limit)
    i = start
    while i < end:
        ch = content[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ">" and depth == 0:
            return content[start:i + 1]
        i += 1
    return content[start:end]


def _mic_component_spans(content: str) -> list[tuple[int, int, str]]:
    """(start, end, name) for every top-level function/const in the file."""
    starts: list[tuple[int, str]] = []
    for m in re.finditer(
        r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?'
        r'(?:function\s+(\w+)|const\s+(\w+)\s*[:=])',
        content, re.MULTILINE,
    ):
        starts.append((m.start(), m.group(1) or m.group(2) or "?"))
    if not starts:
        return [(0, len(content), "<module>")]
    spans: list[tuple[int, int, str]] = []
    if starts[0][0] > 0:
        spans.append((0, starts[0][0], "<module>"))
    for i, (off, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(content)
        spans.append((off, end, name))
    return spans


def _mic_is_commented(lines: list[str], line_no: int, col: int) -> bool:
    """True when the match sits inside a `//` or an unclosed `/* */` comment.

    A CLOSED block comment before the element does not comment it out —
    `{/* UX-CANON: … */}<textarea …>` is live code, and three of the census's
    eight gap sites carry exactly that marker.
    """
    if line_no - 1 >= len(lines):
        return False
    line = lines[line_no - 1]
    stripped = line.strip()
    if (stripped.startswith("//") or stripped.startswith("*")
            or stripped.startswith("/*") or stripped.startswith("{/*")):
        return True
    before = line[:col]
    quote: str | None = None
    i = 0
    while i < len(before):
        ch = before[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
        elif before.startswith("//", i):
            return True
        elif before.startswith("/*", i):
            end = before.find("*/", i + 2)
            if end == -1:
                return True
            i = end + 2
            continue
        i += 1
    return False


def _mic_neighbourhood(lines: list[str], line_no: int, tag: str) -> str:
    """The element's tag text plus the two lines above it."""
    lead = lines[max(0, line_no - 3):line_no - 1]
    return "\n".join(lead) + "\n" + tag


def scan_mic(rel_path: str, content: str, lines: list[str]) -> list[Violation]:
    """Rule `mic`, per element (the voice law).  TSX only."""
    if not rel_path.endswith(".tsx"):
        return []

    spans = _mic_component_spans(content)
    mic_offsets = [m.start() for m in re.finditer(r'<MicButton\b', content)]

    def line_of(offset: int) -> int:
        return content.count("\n", 0, offset) + 1

    def covered(offset: int) -> bool:
        """An explicit MicButton inside the same component function."""
        for start, end, _name in spans:
            if start <= offset < end:
                return any(start <= mic < end for mic in mic_offsets)
        return False

    candidates: list[tuple[int, str, str, str]] = []  # offset, kind, what, tag

    for m in re.finditer(r'<(input|textarea)\b', content):
        tag = _mic_tag_text(content, m.start())
        if m.group(1) == "input":
            tm = re.search(r'\btype\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|\{)', tag)
            if tm:
                literal = tm.group(1) if tm.group(1) is not None else tm.group(2)
                # A dynamic `type={...}` has no literal: treat it as text.
                if literal is not None and literal.strip().lower() not in MIC_TEXT_TYPES:
                    continue
        candidates.append((m.start(), "raw", f"<{m.group(1)}>", tag))

    for m in re.finditer(r'<(%s)\b' % "|".join(MIC_SPECIES), content):
        tag = _mic_tag_text(content, m.start())
        if re.search(r'\bmic\s*=\s*\{\s*false\s*\}', tag):
            candidates.append((m.start(), "optout", f"<{m.group(1)} mic={{false}}>", tag))

    violations: list[Violation] = []
    for offset, kind, what, tag in candidates:
        line_no = line_of(offset)
        col = offset - (content.rfind("\n", 0, offset) + 1)
        if _mic_is_commented(lines, line_no, col):
            continue
        # An opt-out is an explicit refusal: a MicButton elsewhere in the
        # component never covers it.
        if kind == "raw" and covered(offset):
            continue
        hood = _mic_neighbourhood(lines, line_no, tag)
        if any(rel_path == path and needle in hood for path, needle, _r in MIC_ALLOWLIST):
            continue
        first = tag.strip().splitlines()[0].strip()
        violations.append(Violation(
            rel_path, line_no, "mic",
            f"No MicButton on {what} (the voice law, Article IV.1): {first[:100]}"))
    return violations


# ---------------------------------------------------------------------------
# Scanning rules
# ---------------------------------------------------------------------------

class Violation:
    __slots__ = ("file", "line", "rule", "text", "confidence")

    def __init__(self, file: str, line: int, rule: str, text: str, confidence: str = "high"):
        self.file = file
        self.line = line
        self.rule = rule
        self.text = text
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "file": self.file,
            "line": self.line,
            "rule": self.rule,
            "text": self.text,
        }
        if self.confidence != "high":
            d["confidence"] = self.confidence
        return d


# ---------------------------------------------------------------------------
# Matching over the file as it is written (HS-200-44)
# ---------------------------------------------------------------------------
# Prettier puts `<button` alone at the end of a line, `<p` alone above its
# attributes, and a text node alone between its tags.  A matcher that runs
# per line over `content.splitlines()` never sees the character after the
# tag name, so it certifies a tree it cannot read (the 2026-09-13 audit,
# §10 defect 4: A1 reported 4 of 175).  Every rule whose target can span
# lines therefore matches over the WHOLE content; the line number is derived
# from the match offset.  Rules whose target is by construction one line (an
# attribute name with its value, a tag name, a CSS property name, a single
# emoji glyph) stay per line, and say so in the audit table in the story.

# Rule-name lists for the sets a change must not shrink: the story's fence
# asserts the post-fix hit set for each of these is a SUPERSET of the
# pre-fix set over the same tree.
WHOLE_FILE_RULES = ("A1", "A3-sentence", "A3-prose", "A9", "raw-ids", "DS6", "C")


def _line_of(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _col_of(content: str, offset: int) -> int:
    return offset - (content.rfind("\n", 0, offset) + 1)


def _is_commented(lines: list[str], line_no: int, col: int) -> bool:
    """A match on a `//` line, a `*` line, or after `//` / `{/*` on its line."""
    if line_no - 1 >= len(lines):
        return False
    line = lines[line_no - 1]
    stripped = line.strip()
    if (stripped.startswith("//") or stripped.startswith("*")
            or stripped.startswith("/*") or stripped.startswith("{/*")):
        return True
    before = line[:col]
    return "//" in before or "{/*" in before


def _line_text_at(lines: list[str], line_no: int) -> str:
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1].strip()
    return ""


def _squash(text: str) -> str:
    """A text node written across lines, read as one line."""
    return " ".join(text.split())


# Rule A1: raw `<button` as an opening tag.  `(?=[\s>/])` accepts the
# newline Prettier leaves after the tag name and refuses `<buttonish>`.
_A1_BUTTON = re.compile(r"<button(?=[\s>/])")

# Rule A3-sentence: a text node between `>` and `<` (never crossing an
# expression brace), read across lines.
_A3_TEXT_NODE = re.compile(r">([^<>{]+)<")
_CODE_INDICATORS = (';', '&&', '||', '=>', 'const ', 'let ', 'var ', 'useState')
# A node that spans lines is admitted only when it reads as prose: a `>` that
# closes a generic and the `<` three statements later are not a text node.
_MULTILINE_CODE_MARKS = ('//', '/*', '*/', '(', ')', ';', '=', '&&', '||')

# Rule A3-prose: `<p` / `<small` with its attributes on any number of lines,
# then the text node that follows the closing `>` of the opening tag.
_A3_PROSE_TAG = re.compile(r"<(?:p|small)\b[^>]*>([^<]+)")

# Rule A8 stays per line: a whole-file rewrite crossed loop bodies and
# template literals (109 hits, none a counter), and the tree holds no
# `{\n  x.length\n}` shape (HS-200-44 audit).

# Rule A9: a provider call whose verb and path Prettier split across lines.
# `[\s\S]{0,200}?` is the bounded stand-in for the old per-line `.*`.
_A9_PROVIDER = (
    re.compile(r"/api/providers/", re.IGNORECASE),
    re.compile(r"\bdiscover\b[\s\S]{0,200}?(?:fetch|api|post|get)", re.IGNORECASE),
    re.compile(r"(?:fetch|api|post|get)[\s\S]{0,200}?\bdiscover\b", re.IGNORECASE),
    re.compile(r"\brecheck\b[\s\S]{0,200}?(?:fetch|api)", re.IGNORECASE),
    re.compile(r"\bevaluate\b[\s\S]{0,200}?(?:fetch|api)", re.IGNORECASE),
)

# Rule raw-ids: a snake_case text node.  The single-line shape is matched per
# line exactly as before; the multi-line shape (`<span>\n  raw_kind\n</span>`)
# is admitted only when the node holds no code character, so a `>` closing a
# generic and the `<` opening the next tag three statements later never pass
# as a text node.  `{x.id}` as a child may sit on its own line after `>`.
_RAW_SNAKE_LINE = re.compile(r">([^<]*[a-z]+_[a-z_]+[^<]*)<")
_RAW_SNAKE_MULTI = re.compile(r">([^<>{}();=]*[a-z]+_[a-z_]+[^<>{}();=]*)<")
_RAW_ID_CHILD_LINE = re.compile(r">\s*\{[^}]*(?:\.\s*id\s*\}|_id\s*\})")
_RAW_ID_CHILD_MULTI = re.compile(r">[ \t]*\n\s*\{[^{}\n]*(?:\.\s*id\s*\}|_id\s*\})")

# Rule DS6 / C: a CSS declaration runs to its `;` (or the block's `}`),
# however many lines the value takes.
_DS6_BORDER_LEFT = re.compile(r"border-left\s*:([^;}]*)")
_DS6_ACCENT_VALUE = re.compile(
    r"(?:var\(--accent|#[0-9a-fA-F]|rgb|hsl|var\(--\w*accent|var\(--\w*color)")
_DS6_TOKEN_VALUE = re.compile(r"^\s*\d+px\s+solid\s+var\(")
_CSS_FONT_SIZE = re.compile(r"font-size\s*:\s*([^;}]+)")
_TSX_FONT_SIZE = re.compile(r"fontSize\s*:\s*[\"']?([^\"'}, \n]+)")
_TSX_BORDER_LEFT = re.compile(r"borderLeft\s*:\s*([^,}]*)")
_TSX_ACCENT_VALUE = re.compile(r"(?:accent|#[0-9a-fA-F]|rgb)")


def scan_file(rel_path: str, content: str, lines: list[str]) -> list[Violation]:
    """Scan a single file for all rule classes."""
    violations: list[Violation] = []
    is_tsx = rel_path.endswith(".tsx")
    is_css = rel_path.endswith(".css")

    # Track per-file state
    has_button_import = False
    has_egress_chip = False
    has_provider_fetch = False
    font_sizes: set[str] = set()

    def at(offset: int) -> tuple[int, int, str]:
        line_no = _line_of(content, offset)
        return line_no, _col_of(content, offset), _line_text_at(lines, line_no)

    if is_tsx:
        # Check imports
        has_button_import = bool(re.search(
            r'import\s+\{[^}]*\bButton\b[^}]*\}\s+from\s+["\'].*signal/Signal["\']',
            content
        ))
        has_egress_chip = "EgressChip" in content
        # The voice law counts per element — see scan_mic().
        violations.extend(scan_mic(rel_path, content, lines))

        # Rule A1: Raw <button (not the library Button), over the whole file.
        # Case-sensitive: <button is raw HTML; <Button is the library component
        # Exclude Signal.tsx (the library itself) and gadgets.tsx (surface kit)
        is_button_library = any(k in rel_path for k in (
            "Signal.tsx", "gadgets.tsx",
        ))
        if not is_button_library:
            for m in _A1_BUTTON.finditer(content):
                line_no, col, stripped = at(m.start())
                if _is_commented(lines, line_no, col):
                    continue
                violations.append(Violation(rel_path, line_no, "A1",
                    f"Raw <button> element (use library Button): {stripped[:100]}"))

        # Rule A3-sentence: text nodes > 60 chars ending in ./!/? or with ", " + verb,
        # read across lines.
        for m in _A3_TEXT_NODE.finditer(content):
            txt = _squash(m.group(1))
            # Skip TypeScript code fragments caught by generic/ternary boundaries
            if any(ind in txt for ind in _CODE_INDICATORS):
                continue
            if "\n" in m.group(1) and any(mark in txt for mark in _MULTILINE_CODE_MARKS):
                continue
            line_no = _line_of(content, m.start(1) + (len(m.group(1)) - len(m.group(1).lstrip())))
            if len(txt) > 60 and re.search(r'[.!?]$', txt):
                violations.append(Violation(rel_path, line_no, "A3-sentence",
                    f"Sentence in JSX text (>60 chars): \"{txt[:80]}...\""))
            elif len(txt) > 60 and re.search(r',\s+\w+(s|ed|ing|es)\b', txt):
                violations.append(Violation(rel_path, line_no, "A3-sentence",
                    f"Sentence in JSX text (verb + comma): \"{txt[:80]}...\""))

        # Rule A3-prose: <p>/<small> with text > 40 chars, the tag on any
        # number of lines.
        for m in _A3_PROSE_TAG.finditer(content):
            txt = _squash(m.group(1))
            if len(txt) > 40:
                line_no, _col, _s = at(m.start())
                violations.append(Violation(rel_path, line_no, "A3-prose",
                    f"Prose in <p>/<small> element: \"{txt[:80]}...\""))

        # Rule A9: Provider fetches without EgressChip (file-level flag)
        has_provider_fetch = any(p.search(content) for p in _A9_PROVIDER)

        # Rule raw-ids: snake_case strings rendered as visible text.
        # Only flag snake_case between > and < (JSX text position).
        def _raw_snake_hits(txt: str, base: int) -> None:
            for sm in re.finditer(r'\b([a-z]+_[a-z_]+)\b', txt):
                snake = sm.group(1)
                if snake in ("aria_label", "data_testid", "class_name",
                             "aria_hidden", "tab_index"):
                    continue
                # Skip property access (e.g. brief.open_commitments, row.display_name)
                pos = sm.start()
                if pos > 0 and txt[pos - 1] == '.':
                    continue
                violations.append(Violation(rel_path, _line_of(content, base + pos), "raw-ids",
                    f"Snake_case literal in rendered text: \"{snake}\""))

        line_start = 0
        for line_text in lines:
            for m in _RAW_SNAKE_LINE.finditer(line_text):
                _raw_snake_hits(m.group(1), line_start + m.start(1))
            line_start += len(line_text) + 1
        for m in _RAW_SNAKE_MULTI.finditer(content):
            if "\n" not in m.group(1):
                continue  # the single-line shape was counted above
            _raw_snake_hits(m.group(1), m.start(1))
        # {foo.id} directly as JSX child text (between > and <): the
        # single-line shape per line as before, plus `>` with the `{x.id}`
        # child on the next line.
        for i, line_text in enumerate(lines, 1):
            if _RAW_ID_CHILD_LINE.search(line_text):
                violations.append(Violation(rel_path, i, "raw-ids",
                    f"ID field rendered as text: {line_text.strip()[:100]}",
                    confidence="medium"))
        for m in _RAW_ID_CHILD_MULTI.finditer(content):
            line_no, _col, stripped = at(m.end() - 1)
            violations.append(Violation(rel_path, line_no, "raw-ids",
                f"ID field rendered as text: {stripped[:100]}",
                confidence="medium"))

        # Inline styles: font-size and border-left values, across lines
        for m in _TSX_FONT_SIZE.finditer(content):
            font_sizes.add(m.group(1).strip())
        for m in _TSX_BORDER_LEFT.finditer(content):
            if _TSX_ACCENT_VALUE.search(m.group(1)):
                line_no, _col, stripped = at(m.start())
                violations.append(Violation(rel_path, line_no, "DS6",
                    f"Inline accent left rail: {stripped[:100]}"))

    if is_css:
        # Rule DS6: Accent left rails (border-left with accent/color), the
        # declaration read to its `;` however many lines it takes.
        for m in _DS6_BORDER_LEFT.finditer(content):
            value = m.group(1)
            line_no, _col, stripped = at(m.start())
            if _DS6_ACCENT_VALUE.search(value):
                violations.append(Violation(rel_path, line_no, "DS6",
                    f"Accent left rail (banned by DESIGN_SYSTEM rule 6): {stripped[:100]}"))
            elif _DS6_TOKEN_VALUE.search(value):
                violations.append(Violation(rel_path, line_no, "DS6",
                    f"Border-left with token (check if accent): {stripped[:100]}",
                    confidence="medium"))

        # Rule C: Collect font-sizes for type-step collapse detection
        for m in _CSS_FONT_SIZE.finditer(content):
            font_sizes.add(_squash(m.group(1)))

    # Line-shaped rules: the target is an attribute with its value, a tag
    # name, a CSS property name, or a single glyph — none of which Prettier
    # splits across lines.
    for i, line_text in enumerate(lines, 1):
        stripped = line_text.strip()

        if is_tsx:
            # Rule A8: Counters of zero (best effort)
            # Skip import lines entirely — identifiers like groundedMatchCount
            # contain "count" but are not rendered counters.
            if not stripped.startswith("import "):
                # .length interpolations without zero guard
                if re.search(r'\{[^}]*\.length\s*\}', line_text):
                    # Check for a zero guard (boolean, ternary, logical, arithmetic)
                    expr_match = re.search(r'\{([^}]*\.length[^}]*)\}', line_text)
                    if expr_match:
                        expr = expr_match.group(1)
                        if not re.search(r'[!?&|+\-]|===?\s*0|!==?\s*0|>\s*0', expr):
                            violations.append(Violation(rel_path, i, "A8",
                                f"Counter may render zero (.length without guard): {stripped[:100]}",
                                confidence="medium"))
                # {count} Noun pattern
                if re.search(r'\{[^}]*(?:count|Count|total|num|len)\b[^}]*\}\s*\w', line_text):
                    if not re.search(r'[?&|]|===?\s*0|!==?\s*0|>\s*0', line_text):
                        violations.append(Violation(rel_path, i, "A8",
                            f"Counter may render zero (count pattern): {stripped[:100]}",
                            confidence="low"))
                # Explicit "0 " or "{0}" patterns (rare but direct)
                if re.search(r'>\s*0\s+\w', line_text):
                    violations.append(Violation(rel_path, i, "A8",
                        f"Literal zero counter in text: {stripped[:100]}",
                        confidence="medium"))
                # ?? 0 pattern (explicitly renders 0 as fallback)
                if re.search(r'\?\?\s*0\b', line_text):
                    # check if it's rendered as text
                    if re.search(r'\{[^}]*\?\?\s*0[^}]*\}', line_text):
                        violations.append(Violation(rel_path, i, "A8",
                            f"Zero fallback rendered (?? 0): {stripped[:100]}",
                            confidence="medium"))

            # Rule A3-sentence: string literals used as prop values (title=, label=, etc.)
            prop_texts = re.findall(r'(?:title|label|description|placeholder|children)=\{?"([^"]{60,})"', line_text)
            for txt in prop_texts:
                if re.search(r'[.!?]$', txt):
                    violations.append(Violation(rel_path, i, "A3-sentence",
                        f"Sentence in prop text: \"{txt[:80]}...\""))

            # Rule A3-prose: className with hint|help|description
            if re.search(r'className\s*=\s*["{][^"]*(?:hint|help|description)', line_text):
                violations.append(Violation(rel_path, i, "A3-prose",
                    f"Prose helper class (hint/help/description): {stripped[:100]}"))

            # Rule A4: Modals
            if re.search(r'role\s*=\s*["\']dialog["\']', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Modal (role=\"dialog\"): {stripped[:100]}"))
            if re.search(r'aria-modal', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Modal (aria-modal): {stripped[:100]}"))
            if re.search(r'<(?:Modal|Dialog)\b', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Modal/Dialog component: {stripped[:100]}"))
            if re.search(r'position:\s*fixed', line_text):
                # Check for backdrop-like patterns
                if re.search(r'(?:backdrop|overlay|modal|z-index)', content[max(0, content.find(line_text)-200):content.find(line_text)+200], re.IGNORECASE):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Fixed overlay (possible modal): {stripped[:100]}", confidence="medium"))

            # Rule B: Non-library controls (raw <input>/<select>/<textarea>)
            # `\b` after the tag name is satisfied by the end of the line, so
            # a multi-line tag is seen.  Exclude files that ARE the library wrappers.
            is_library_file = any(k in rel_path for k in (
                "Signal.tsx", "gadgets.tsx", "MicButton", "StringGadget",
                "EditInPlace", "CycleGadget", "CheckGadget", "PadGadget",
                "LedgerFilter", "ChoiceCard", "surface/controls/",
            ))
            if not is_library_file and re.search(r'<(?:input|select|textarea)\b', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "B",
                        f"Raw control element: {stripped[:100]}"))

            # Rule raw-ids: title/label props that show visible text with raw IDs
            title_match = re.search(r'(?:title|label)=\{[`"]([^`"]*(?:\.\s*id\b|_id\b)[^`"]*)[`"]\}', line_text)
            if title_match:
                violations.append(Violation(rel_path, i, "raw-ids",
                    f"ID rendered in visible prop: {title_match.group(0)[:100]}",
                    confidence="medium"))

            # Rule emoji: Emoji/dingbats in JSX text
            # Unicode ranges for common emoji
            emoji_match = re.search(
                r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]',
                line_text
            )
            if emoji_match:
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    # Exclude aria-hidden elements (intentional decorative emoji)
                    if 'aria-hidden' not in line_text:
                        violations.append(Violation(rel_path, i, "emoji",
                            f"Emoji in JSX text: {stripped[:100]}"))

    # Post-file checks

    # Rule A9: Provider fetch without EgressChip
    if is_tsx and has_provider_fetch and not has_egress_chip:
        violations.append(Violation(rel_path, 1, "A9",
            "Provider fetch found but no EgressChip rendered in this file"))

    # Rule C: Type-step collapse (only for TSX face files)
    if is_tsx and classify_face(rel_path):
        # A face with <= 1 distinct font-size is a defect (from CSS or inline)
        # We can only detect this from CSS + inline; mark as best-effort
        if font_sizes and len(font_sizes) <= 1:
            violations.append(Violation(rel_path, 1, "C",
                f"Type-step collapse: only {len(font_sizes)} distinct font-size ({', '.join(font_sizes)})",
                confidence="medium"))

    violations.sort(key=lambda v: (v.line, v.rule))
    return violations


# ---------------------------------------------------------------------------
# Aggregate: pair CSS with nearest TSX face
# ---------------------------------------------------------------------------

def find_face_files(root: Path) -> list[Path]:
    """Find all scannable files under web/src."""
    result = []
    src = root / "web" / "src"
    if not src.is_dir():
        return result
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix not in (".tsx", ".css"):
            continue
        rel = str(p.relative_to(src))
        if "__tests__" in rel or ".test." in rel or "_parked" in rel:
            continue
        # Only scan face directories
        is_face_dir = False
        for d in FACE_DIRS:
            if rel.startswith(d):
                is_face_dir = True
                break
        if is_face_dir:
            result.append(p)
    return result


def find_mic_files(root: Path) -> list[Path]:
    """Every .tsx under web/src — the voice law's scope (census §Scope).

    Wider than find_face_files(): the mic rule is not gated on face
    classification (design D2(d).2 defect iv), so a text input in a shared
    component outside features/ · pages/cores/ · desk/ is counted too.
    """
    result = []
    src = root / "web" / "src"
    if not src.is_dir():
        return result
    for p in sorted(src.rglob("*.tsx")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(src))
        if "__tests__" in rel or ".test." in rel or "_parked" in rel:
            continue
        result.append(p)
    return result


def file_to_face(rel: str) -> str:
    """Map a relative path to a face name for grouping."""
    stem = Path(rel).stem
    # For CSS files, try to find the face they belong to (same directory tsx)
    return stem


def scan_all(root: Path) -> tuple[dict[str, list[Violation]], list[Violation]]:
    """Scan all face files. Returns (per_face, all_violations)."""
    src = root / "web" / "src"
    files = find_face_files(root)
    per_face: dict[str, list[Violation]] = defaultdict(list)
    all_violations: list[Violation] = []

    # Also scan paired CSS files for each TSX face
    css_companions: dict[str, set[str]] = defaultdict(set)

    for f in files:
        rel = str(f.relative_to(src))
        content = f.read_text(errors="replace")
        file_lines = content.splitlines()
        violations = scan_file(rel, content, file_lines)

        face = file_to_face(rel)
        per_face[face].extend(violations)
        all_violations.extend(violations)

    # The voice law reaches every .tsx, not only the face directories.
    face_paths = {f for f in files}
    for f in find_mic_files(root):
        if f in face_paths:
            continue
        rel = str(f.relative_to(src))
        content = f.read_text(errors="replace")
        violations = scan_mic(rel, content, content.splitlines())
        if not violations:
            continue
        per_face[file_to_face(rel)].extend(violations)
        all_violations.extend(violations)

    return dict(per_face), all_violations


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def build_totals(all_violations: list[Violation]) -> dict[str, dict[str, int]]:
    """Build totals tables: per rule and per face."""
    per_rule: dict[str, int] = defaultdict(int)
    per_face: dict[str, int] = defaultdict(int)
    for v in all_violations:
        per_rule[v.rule] += 1
        face = file_to_face(v.file)
        per_face[face] += 1
    return {"per_rule": dict(per_rule), "per_face": dict(per_face)}


def build_ranking(per_face: dict[str, list[Violation]]) -> list[dict[str, Any]]:
    """Rank faces by Tuesday use x canon debt."""
    ranking = []
    for face, violations in per_face.items():
        if not violations:
            continue
        tuesday = TUESDAY_USE.get(face, 1)
        debt = sum(RULE_WEIGHTS.get(v.rule, 1) for v in violations)
        score = tuesday * debt
        # Find loudest break (highest weight violation)
        loudest = max(violations, key=lambda v: RULE_WEIGHTS.get(v.rule, 1))
        # Count per rule
        rule_counts: dict[str, int] = defaultdict(int)
        for v in violations:
            rule_counts[v.rule] += 1
        ranking.append({
            "face": face,
            "tuesday_use": tuesday,
            "debt": debt,
            "score": score,
            "hits": len(violations),
            "loudest_rule": loudest.rule,
            "loudest_text": loudest.text,
            "rule_counts": dict(rule_counts),
        })
    ranking.sort(key=lambda r: r["score"], reverse=True)
    return ranking


def write_violations_md(path: Path, per_face: dict[str, list[Violation]],
                        totals: dict[str, dict[str, int]]) -> None:
    """Write violations.md."""
    lines = ["# UX Canon Violations Census\n\n"]
    lines.append("Generated by `scripts/ux_canon_scan.py`.\n\n")

    # Totals per rule
    lines.append("## Totals per rule\n\n")
    lines.append("| Rule | Count | Weight |\n|---|---|---|\n")
    for rule in sorted(totals["per_rule"], key=lambda r: totals["per_rule"][r], reverse=True):
        lines.append(f"| {rule} | {totals['per_rule'][rule]} | {RULE_WEIGHTS.get(rule, 1)} |\n")
    lines.append("\n")

    # Totals per face
    lines.append("## Totals per face\n\n")
    lines.append("| Face | Hits |\n|---|---|\n")
    for face in sorted(totals["per_face"], key=lambda f: totals["per_face"][f], reverse=True):
        lines.append(f"| {face} | {totals['per_face'][face]} |\n")
    lines.append("\n")

    # Per-face sections
    for face in sorted(per_face):
        violations = per_face[face]
        if not violations:
            continue
        lines.append(f"## {face}\n\n")
        for v in sorted(violations, key=lambda x: (x.rule, x.line)):
            conf = f" [{v.confidence}]" if v.confidence != "high" else ""
            lines.append(f"- **{v.rule}** `{v.file}:{v.line}`{conf} -- {v.text}\n")
        lines.append("\n")

    path.write_text("".join(lines))


def write_violations_json(path: Path, per_face: dict[str, list[Violation]],
                          totals: dict[str, dict[str, int]]) -> None:
    """Write violations.json."""
    data = {
        "totals": totals,
        "faces": {
            face: [v.to_dict() for v in violations]
            for face, violations in sorted(per_face.items())
            if violations
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n")


def scan(root: Path) -> dict[str, Any]:
    """Run the full scan and return a result dict (totals + faces + face_rule_counts).

    This is the in-process entry point used by the ratchet guard test.
    """
    per_face, all_violations = scan_all(root)
    totals = build_totals(all_violations)
    # Build per-face-per-rule counts (for the ratchet ceiling diff).
    face_rule_counts: dict[str, dict[str, int]] = {}
    for face, violations in per_face.items():
        counts: dict[str, int] = {}
        for v in violations:
            counts[v.rule] = counts.get(v.rule, 0) + 1
        if counts:
            face_rule_counts[face] = counts
    return {
        "totals": totals,
        "faces": {
            face: [v.to_dict() for v in violations]
            for face, violations in sorted(per_face.items())
            if violations
        },
        "face_rule_counts": face_rule_counts,
    }


class CeilingRaised(ValueError):
    """A per-rule ceiling would rise without a new reason."""


def write_ceiling(path: Path, totals: dict[str, dict[str, int]],
                  face_rule_counts: dict[str, dict[str, int]],
                  reason: str | None = None,
                  date: str | None = None) -> dict[str, Any]:
    """Write the ratchet ceiling file (per_rule totals + per-face-per-rule counts).

    All rules in RULE_WEIGHTS are included — zeros explicitly, so
    hard-zero guards can reference the ceiling.

    The file carries a ``ratchet`` block: the date the numbers were measured
    and the reason they stand.  A number may only go DOWN under the existing
    reason; if any per-rule count would rise above the committed ceiling,
    the write is refused unless a NEW reason (different from the one on
    file) is given — the caller changes the reason in the same commit that
    admits the debt (HS-200-03's shape, HS-200-44).
    """
    # Start from all-zero for every known rule, then overlay actual counts.
    per_rule = {r: 0 for r in sorted(RULE_WEIGHTS)}
    per_rule.update(totals["per_rule"])

    previous: dict[str, Any] = {}
    if path.is_file():
        try:
            previous = json.loads(path.read_text())
        except json.JSONDecodeError:
            previous = {}
    prev_rule = previous.get("per_rule", {})
    prev_ratchet = previous.get("ratchet", {})
    risen = {r: (prev_rule.get(r, 0), n) for r, n in per_rule.items()
             if n > prev_rule.get(r, 0)}
    if risen and (not reason or reason == prev_ratchet.get("reason")):
        raise CeilingRaised(
            "ceiling would RISE for " + ", ".join(
                f"{r}: {a} -> {b}" for r, (a, b) in sorted(risen.items()))
            + "; a ceiling only goes down under its reason. Pass a new "
              "--ceiling-reason naming the debt being admitted.")

    data = {
        "per_rule": dict(sorted(per_rule.items())),
        "faces": face_rule_counts,
        "ratchet": {
            "date": date or _dt.date.today().isoformat(),
            "reason": reason or prev_ratchet.get("reason", ""),
        },
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return data


def write_ranking_md(path: Path, ranking: list[dict[str, Any]]) -> None:
    """Write ranking.md."""
    lines = ["# Face Ranking by Tuesday Use x Canon Debt\n\n"]
    lines.append("Weights: A1/A3/A4 (raw button, sentence, modal) = 3; ")
    lines.append("A8/A9/DS6 (zero counter, missing egress, accent rail) = 2; ")
    lines.append("all others (B, C, raw-ids, emoji, mic) = 1.\n\n")
    lines.append("Score = tuesday_use x weighted_debt.\n\n")

    lines.append("| Rank | Face | Tuesday | Debt | Score | Hits | Loudest break |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for i, r in enumerate(ranking, 1):
        lines.append(
            f"| {i} | {r['face']} | {r['tuesday_use']} | {r['debt']} "
            f"| {r['score']} | {r['hits']} | {r['loudest_rule']}: {r['loudest_text'][:60]} |\n"
        )
    lines.append("\n")

    path.write_text("".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan HoldSpeak web/src for UX canon violations. "
                    "Writes nothing unless an output flag is given."
    )
    parser.add_argument("--root", type=Path, default=Path("."),
                        help="Project root (default: cwd)")
    parser.add_argument("--write-census", type=Path, default=None, metavar="DIR",
                        help="Write violations.md, violations.json and ranking.md into DIR")
    parser.add_argument("--json", type=Path, default=None,
                        help="Write the violations JSON to this path")
    parser.add_argument("--md", type=Path, default=None,
                        help="Write the violations Markdown to this path")
    parser.add_argument("--ranking", type=Path, default=None,
                        help="Write the ranking Markdown to this path")
    parser.add_argument("--write-ceiling", type=Path, default=None,
                        help="Write the ratchet ceiling file (per_rule + per-face-per-rule counts)")
    parser.add_argument("--ceiling-reason", default=None,
                        help="The reason the ceiling stands; REQUIRED (and must be new) "
                             "when any per-rule number would rise")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not (root / "web" / "src").is_dir():
        print(f"ERROR: {root / 'web' / 'src'} is not a directory", file=sys.stderr)
        return 1

    per_face, all_violations = scan_all(root)
    totals = build_totals(all_violations)
    ranking = build_ranking(per_face)

    # Every write is explicit.  A plain run leaves the tree untouched.
    md_path = args.md or (args.write_census / "violations.md" if args.write_census else None)
    json_path = args.json or (args.write_census / "violations.json" if args.write_census else None)
    ranking_path = args.ranking or (args.write_census / "ranking.md" if args.write_census else None)

    print(f"Scanned {len(find_face_files(root))} files, found {len(all_violations)} violations across {len(per_face)} faces.")
    if md_path:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_violations_md(md_path, per_face, totals)
        print(f"  violations.md:   {md_path}")
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        write_violations_json(json_path, per_face, totals)
        print(f"  violations.json: {json_path}")
    if ranking_path:
        ranking_path.parent.mkdir(parents=True, exist_ok=True)
        write_ranking_md(ranking_path, ranking)
        print(f"  ranking.md:      {ranking_path}")
    if not (md_path or json_path or ranking_path or args.write_ceiling):
        print("  (nothing written: pass --write-census DIR, --json/--md/--ranking, or --write-ceiling)")

    # Explicit ceiling write, down-only under its reason
    if args.write_ceiling:
        face_rule_counts: dict[str, dict[str, int]] = {}
        for face, violations in per_face.items():
            counts: dict[str, int] = {}
            for v in violations:
                counts[v.rule] = counts.get(v.rule, 0) + 1
            if counts:
                face_rule_counts[face] = counts
        try:
            write_ceiling(args.write_ceiling, totals, face_rule_counts,
                          reason=args.ceiling_reason)
        except CeilingRaised as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"  ceiling:         {args.write_ceiling}")

    # Print summary
    print("\nTotals per rule:")
    for rule in sorted(totals["per_rule"], key=lambda r: totals["per_rule"][r], reverse=True):
        print(f"  {rule}: {totals['per_rule'][rule]}")

    if ranking:
        print(f"\nTop {min(10, len(ranking))} faces:")
        for r in ranking[:10]:
            print(f"  {r['face']:30s}  tuesday={r['tuesday_use']}  debt={r['debt']:3d}  "
                  f"score={r['score']:4d}  loudest={r['loudest_rule']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
