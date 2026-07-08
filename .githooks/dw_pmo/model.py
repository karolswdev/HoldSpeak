"""Domain model, shared constants, and the core error type."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PHASE_RE = re.compile(r"^phase-(\d+)-(.+)$")
STORY_RE = re.compile(r"^story-(\d+)-(.+)\.md$")
STORY_ID_RE = re.compile(r"^([A-Z][A-Z0-9]*)-(\d+)-(\d+)$")
DONE_STATUSES = {"done", "complete", "closed", "shipped"}
# The single story-status vocabulary (declared for humans in
# roadmap-builder §2.3; a unit test asserts doc/constant parity).
# Write commands reject anything else so a typo can never strand a
# story outside every view.
STORY_OPEN_STATUSES = {"backlog", "ready", "in-progress", "blocked"}
STORY_STATUSES = DONE_STATUSES | STORY_OPEN_STATUSES
# Phase-activity detection tolerates the looser phase-index vocabulary
# (planned/not-started/planning/scaffolded/paused) that may appear in
# legacy story tables and phase indexes.
OPEN_STATUSES = STORY_OPEN_STATUSES | {"planned", "not-started", "planning", "scaffolded", "paused"}

# Read-side terminal statuses for rows a legacy tree retired rather
# than shipped (struck-through rows, cancelled work). Never accepted
# by the write vocabulary above.
CUT_STATUSES = {"cut", "cancelled", "superseded"}

# ── read-side status normalization (WLA-16-01) ────────────────────────
#
# Legacy trees decorate statuses: "**done** (2026-07-07 — twelve new
# tests)", "CLOSED ✅ (6/6)", "in-progress (3/6)". The read layer
# resolves any such cell or header to one comparable token so that
# membership tests and header↔table comparisons see through the
# decoration. Matching happens at token boundaries, leftmost match
# wins, longest keyword first at a given position — "host-complete"
# must never read as "complete". The WRITE vocabulary stays
# STORY_STATUSES, exact: `dw story status` rejects anything else.

_STATUS_KEYWORDS = [
    "in-progress", "in progress", "not-started", "not started",
    "superseded", "cancelled", "scaffolded", "planning", "planned",
    "complete", "shipped", "backlog", "blocked", "paused", "closed",
    "ready", "done", "cut",
]
_STATUS_KEYWORD_RE = re.compile(
    r"(?<![a-z0-9-])("
    + "|".join(k.replace(" ", r"\s+") for k in sorted(_STATUS_KEYWORDS, key=len, reverse=True))
    + r")(?![a-z0-9-])"
)
_STATUS_CANONICAL = {"in progress": "in-progress", "not started": "not-started"}


def normalize_status(raw: str | None) -> str:
    """Resolve a possibly-decorated status string to a comparable token.

    Only the HEAD of the string — everything before the first
    decoration delimiter — is consulted: a keyword found there wins
    (canonicalized); otherwise the head's first token, lowercased.
    Narrative tails are never searched — a cell ending "…the request
    never shipped)" must not read as shipped. Read-side only.
    """
    if not raw:
        return ""
    s = re.sub(r"\*|`|_{2}|~~", "", raw).strip().lower()
    head = re.split(r"[(—–:;,.!]", s, maxsplit=1)[0].strip()
    m = _STATUS_KEYWORD_RE.search(head)
    if m:
        token = re.sub(r"\s+", " ", m.group(1))
        return _STATUS_CANONICAL.get(token, token)
    parts = head.split()
    return parts[0] if parts else ""

# The generator's stand-in body for evidence created without content.
# dw check treats a done story whose evidence still carries this line
# as unproven.
EVIDENCE_PLACEHOLDER = (
    "Evidence body intentionally left for the operator to complete before commit."
)


class DwError(Exception):
    """A refusal or failure the caller can handle.

    The CLI adapter converts this to the historical ``dw: <message>``
    stderr line and exit code; library consumers (workbench server, gate
    engine) catch it instead of dying.
    """

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def die(message: str, code: int = 1) -> None:
    raise DwError(message, code)


@dataclass
class Project:
    slug: str
    path: Path
    prefix: str


@dataclass
class Phase:
    number: int
    slug: str
    path: Path


@dataclass
class StoryRow:
    story_id: str
    title: str
    status: str
    story_file: str
    evidence: str


def row_is_retired(row: StoryRow) -> bool:
    """A retired row is legacy history that will never ship: the ID is
    struck through (`~~HS-1-01~~`) or the status normalizes to a cut
    token. Read-side validators make no file or evidence demands of it
    (WLA-16-02)."""
    story_id = row.story_id.strip()
    if story_id.startswith("~~") and story_id.endswith("~~") and len(story_id) > 4:
        return True
    return normalize_status(row.status) in CUT_STATUSES
