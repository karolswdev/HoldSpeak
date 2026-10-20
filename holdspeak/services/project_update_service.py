"""The Update Factory: deterministic + model drafting (UPD-001..005).

HS-162-02: the deterministic drafter ships first.  It DEFINES the section
contract and the claim schema the model drafter (03) will be constrained
to.

HS-162-04: thin service verbs for the route wire -- list_updates, get_update,
draft_update_command, save_update, regenerate_update, publish_update.
Publish joins the project revision law in one transaction.

Section contract (UPD-001)
--------------------------
Every update MUST cover six sections in this canonical order:

  1. Progress          -- focus items and their lifecycle states
  2. Decisions         -- accepted/dismissed proposals from the review
  3. Risks & Blockers  -- open risks and broken/at-risk dependencies
  4. Dependencies      -- all dependency items and their states
  5. Next Actions      -- items with upcoming due dates or planned state
  6. Source Coverage    -- caveats when any room section is degraded/absent

A section with nothing to say renders the honest minimal line (e.g.
"No decisions in this window."), not filler.

Claim schema (UPD-002)
----------------------
Every factual sentence in body_md carries a claim entry in claims_json.
The schema is the single authority for both the deterministic and model
drafters:

    {
      "span_id":  str,          # stable id within this draft (s_<section>_<ordinal>)
      "text":     str,          # the sentence or phrase
      "refs":     [str, ...],   # >= 1 canonical refs (item:, decision:, pobs:, etc.)
      "section":  str           # one of the six section keys
    }

When ``verified`` is ``False`` the claim is MARKED for owner review
(UPD-002: unsupported model language).  Deterministic claims omit the
field (always verified); only the model drafter may set it ``False``.

ZERO prose without a locator -- the deterministic drafter does not know
how to lie.

Determinism law
---------------
Same room state => byte-identical body_md + claims_json.  NO wall-clock
content inside the body.  Sort everything canonically.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re as _re
import threading
import time as _time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from holdspeak.timestamps import utc_now_iso
from typing import Any, Callable, Iterable, Optional

from ..db.updates import PublishedUpdateError
from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from ..project_contracts import (
    CommandResultEnvelope,
    ResultKind,
    generate_pchg_id,
    generate_pcmd_id,
    generate_pupd_id,
)
from ..refs import format as format_ref, parse as parse_ref
from .meeting_kind import is_one_on_one, meeting_speakers, title_says_one_on_one
from .memory_grounding import memory_for, project_pages
# Betterment P3: one risk rule for the update and the project window's head.
from .room_health_service import note_risk_lines as _note_risk_lines, risk_sentences as _risk_sentences

#: The marked block the project's memory travels in, inside the draft prompt.
MEMORY_BLOCK_HEADING = "PROJECT MEMORY"
from .errors import ConflictError, NotFound, ServiceError, ValidationError
from .service_event_ledger import ServiceEventLedger

_log = get_logger("services.project_update_service")

# ── Capability identity (HS-162-03) ──────────────────────────────────
PROJECT_UPDATE_CAPABILITY = "project.update_draft"

# ── The named fallback receipt (HS-200-08) ───────────────────────────
#
# A model draft that falls back to the deterministic drafter used to say so
# in a log line only, so the face showed an ordinary deterministic draft and
# nobody could tell a chosen deterministic draft from a failed model one.
# The reason now travels WITH the row: it is encoded on the stored generator
# and projected back out on read as ``fallback_reason`` (the code the face
# already decodes) plus ``fallback_receipt`` (the token it can show).
FALLBACK_GENERATOR_PREFIX = "deterministic:"

FALLBACK_ROUTE_UNRESOLVED = "route_unresolved"
FALLBACK_MODEL_UNAVAILABLE = "model_unavailable"
FALLBACK_NO_OUTPUT = "no_output"
FALLBACK_UNPARSEABLE_OUTPUT = "unparseable_output"

FALLBACK_RECEIPT_TOKENS: dict[str, str] = {
    FALLBACK_ROUTE_UNRESOLVED: "DETERMINISTIC · ROUTE UNRESOLVED",
    FALLBACK_MODEL_UNAVAILABLE: "DETERMINISTIC · MODEL UNAVAILABLE",
    FALLBACK_NO_OUTPUT: "DETERMINISTIC · NO OUTPUT",
    FALLBACK_UNPARSEABLE_OUTPUT: "DETERMINISTIC · OUTPUT UNUSABLE",
}

MODEL_DRAFT_REASON: dict[str, str] = {
    FALLBACK_ROUTE_UNRESOLVED: "no_engine",
    FALLBACK_MODEL_UNAVAILABLE: "no_engine",
    FALLBACK_NO_OUTPUT: "did_not_answer",
    FALLBACK_UNPARSEABLE_OUTPUT: "not_usable",
}


def model_draft_reason(code: str | None) -> str:
    """Map internal model failure codes to the closed face vocabulary."""
    return MODEL_DRAFT_REASON.get(str(code or ""), "did_not_answer")


def fallback_receipt_token(code: str | None) -> str | None:
    """The token the face shows for one fallback reason code."""
    if not code:
        return None
    known = FALLBACK_RECEIPT_TOKENS.get(code)
    if known:
        return known
    return "DETERMINISTIC · " + code.replace("_", " ").upper()


# ── Marker for unverified model claims (UPD-002) ────────────────────
UNVERIFIED_MARKER = "**[UNVERIFIED]**"


# ── The three C2 axes (HS-200-06) ─────────────────────────────────────
#
# Phase 200 CONTRACTS §C2: Kind, Support and Acceptance are INDEPENDENT.
# A valid reference establishes SOURCE LINKAGE and nothing more.  A model
# score can never establish acceptance.

# Kind -- what the statement asserts.
KIND_OBSERVATION = "observation"
KIND_INFERENCE = "inference"
KIND_PROPOSAL = "proposal"
KIND_DECISION = "decision"
KIND_EXECUTION_RESULT = "execution_result"
KIND_OUTCOME_MEASURE = "outcome_measure"
CLAIM_KINDS: tuple[str, ...] = (
    KIND_OBSERVATION,
    KIND_INFERENCE,
    KIND_PROPOSAL,
    KIND_DECISION,
    KIND_EXECUTION_RESULT,
    KIND_OUTCOME_MEASURE,
)

# Support -- what the evidence establishes.
SUPPORT_UNKNOWN = "unknown"
SUPPORT_SOURCE_LINKED = "source_linked"
SUPPORT_SUPPORTED = "supported"
SUPPORT_DISPUTED = "disputed"
SUPPORT_STATES: tuple[str, ...] = (
    SUPPORT_UNKNOWN,
    SUPPORT_SOURCE_LINKED,
    SUPPORT_SUPPORTED,
    SUPPORT_DISPUTED,
)

# Acceptance -- applicable domain or reviewer judgment.
ACCEPTANCE_UNREVIEWED = "unreviewed"
ACCEPTANCE_ACCEPTED = "accepted"
ACCEPTANCE_REJECTED = "rejected"
ACCEPTANCE_SUPERSEDED = "superseded"
ACCEPTANCE_STATES: tuple[str, ...] = (
    ACCEPTANCE_UNREVIEWED,
    ACCEPTANCE_ACCEPTED,
    ACCEPTANCE_REJECTED,
    ACCEPTANCE_SUPERSEDED,
)

# The only two validation methods that may raise support to `supported`.
METHOD_FIELD_MAPPING = "field_mapping"
METHOD_REVIEWER = "reviewer"

# The conservative mapping applied to citation-only `verified` records
# written before HS-200-06.  Recorded on every claim it touches; the
# stored blob is NEVER rewritten in place.
CLAIM_SUPPORT_MAPPING_VERSION = "c2.1"

# Reasons a support record is invalidated.
INVALIDATION_TEXT_EDITED = "text_edited"


# ── Support records (C2) ──────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SupportRecord:
    """What raised a claim above source linkage, and how.

    method:        ``field_mapping`` (deterministic extraction of a
                   recorded status) or ``reviewer`` (a person's
                   attestation through the review path).
    source_version: the EXACT source version checked -- the pinned
                   project revision the claim's refs were read at.
    source_refs:   the refs the check read.
    fields:        the recorded fields the mapping read (field_mapping).
    reviewer_ref:  the attesting person (reviewer).
    checked_at:    wall clock; set ONLY on reviewer records and on
                   invalidation, never on a deterministic draft (the
                   determinism law forbids wall clock in claims_json).
    invalidated_at / invalidation_reason: set when the supported
                   sentence was edited.  The record is KEPT -- support
                   drops, provenance stays.
    """
    method: str
    source_version: str = ""
    source_refs: list[str] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)
    reviewer_ref: str | None = None
    checked_at: str | None = None
    invalidated_at: str | None = None
    invalidation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"method": self.method}
        if self.source_version:
            d["source_version"] = self.source_version
        if self.source_refs:
            d["source_refs"] = list(self.source_refs)
        if self.fields:
            d["fields"] = list(self.fields)
        if self.reviewer_ref:
            d["reviewer_ref"] = self.reviewer_ref
        if self.checked_at:
            d["checked_at"] = self.checked_at
        if self.invalidated_at:
            d["invalidated_at"] = self.invalidated_at
        if self.invalidation_reason:
            d["invalidation_reason"] = self.invalidation_reason
        return d


# ── Claim schema (UPD-002 + C2) ───────────────────────────────────────
#
# This is the SINGLE AUTHORITY for both the deterministic and model
# drafters.  Story 03 and the face import this shape.

@dataclass(frozen=True, slots=True)
class Claim:
    """One factual claim in an update draft.

    span_id:  stable identifier within this draft (s_<section>_<ordinal>).
    text:     the factual sentence or phrase.
    refs:     list of >= 1 canonical refs (item:<id>, decision:<id>, etc.).
    section:  one of the six UPD-001 section keys.
    verified: True (default) for deterministic / cited model claims.
              False for MARKED unverified model claims (UPD-002).
              Omitted from to_dict() when True so deterministic output
              stays byte-identical.  KEPT as provenance -- HS-200-06
              never rewrites it.
    kind / support / acceptance: the three independent C2 axes.
    support_record: what raised support to `supported` (or what was
              invalidated), never deleted once written.
    unknowns: typed unknowns -- a name, deadline or number in the prose
              that the cited source's fields do not carry.
    """
    span_id: str
    text: str
    refs: list[str]
    section: str
    verified: bool = True
    kind: str = KIND_OBSERVATION
    support: str = SUPPORT_UNKNOWN
    acceptance: str = ACCEPTANCE_UNREVIEWED
    support_record: SupportRecord | None = None
    unknowns: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "acceptance": self.acceptance,
            "kind": self.kind,
            "refs": list(self.refs),
            "section": self.section,
            "span_id": self.span_id,
            "support": self.support,
            "text": self.text,
        }
        if self.support_record is not None:
            d["support_record"] = self.support_record.to_dict()
        if self.unknowns:
            d["unknowns"] = [dict(u) for u in self.unknowns]
        if not self.verified:
            d["verified"] = False
        return d


def _field_mapping_support(
    source_version: str,
    refs: list[str],
    fields_read: list[str],
) -> SupportRecord:
    """A deterministic extraction of recorded statuses (C2)."""
    return SupportRecord(
        method=METHOD_FIELD_MAPPING,
        source_version=source_version,
        source_refs=list(refs),
        fields=list(fields_read),
    )


# The six UPD-001 section keys, in canonical order.
SECTION_KEYS: tuple[str, ...] = (
    "progress",
    "decisions",
    "risks_blockers",
    "dependencies",
    "next_actions",
    "source_coverage",
)

# Human-readable section headings for the Markdown body.
_SECTION_HEADINGS: dict[str, str] = {
    "progress": "Progress",
    "decisions": "Decisions",
    "risks_blockers": "Risks & Blockers",
    "dependencies": "Dependencies",
    "next_actions": "Next Actions",
    "source_coverage": "Source Coverage",
}

# Honest minimal lines per section (nothing to say).
_HONEST_MINIMAL: dict[str, str] = {
    "progress": "No focus items in this window.",
    "decisions": "No decisions in this window.",
    "risks_blockers": "No risks or blockers in this window.",
    "dependencies": "No dependencies tracked.",
    "next_actions": "No upcoming actions.",
    # Betterment P1: the old constant ("All sources consulted successfully.")
    # was said whatever was read. Coverage now names what was read; this
    # line shows only when nothing was.
    "source_coverage": "Nothing linked to this project was read.",
}


# ── Section builders (deterministic) ──────────────────────────────────

def _build_progress(
    items_section: dict[str, Any],
    claims: list[Claim],
    source_version: str,
) -> str:
    """Progress section from room items (focus block)."""
    focus = items_section.get("focus", [])
    if not focus:
        return _HONEST_MINIMAL["progress"]

    lines: list[str] = []
    for i, item in enumerate(focus):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        lifecycle = item.get("lifecycle", "unknown")
        item_type = item.get("item_type", "item")
        severity = item.get("severity")

        sev_str = f" [{severity}]" if severity else ""
        text = f"{item_type.capitalize()}{sev_str}: {title} -- {lifecycle}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_{i}"
        claims.append(Claim(
            span_id=f"s_progress_{i}",
            text=text,
            refs=[ref],
            section="progress",
            # A recorded lifecycle read straight off the item row: an
            # observation, supported by a field mapping (C2).
            kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref],
                ["item_type", "severity", "title", "lifecycle"],
            ),
        ))
        lines.append(f"- {text}")

    total = items_section.get("total", len(focus))
    cap = len(focus)
    if total > cap:
        lines.append(f"\n_{total - cap} more items not shown._")

    return "\n".join(lines)


# Proposal lifecycles that record a decided domain judgment.
_PROPOSAL_ACCEPTANCE: dict[str, str] = {
    "accepted": ACCEPTANCE_ACCEPTED,
    "dismissed": ACCEPTANCE_REJECTED,
    "rejected": ACCEPTANCE_REJECTED,
    "superseded": ACCEPTANCE_SUPERSEDED,
}


def _build_decisions(
    review_section: dict[str, Any],
    proposals: list[dict[str, Any]],
    claims: list[Claim],
    source_version: str,
) -> str:
    """Decisions section from the open review's proposals."""
    if not proposals:
        return _HONEST_MINIMAL["decisions"]

    lines: list[str] = []
    ordinal = 0
    for prop in proposals:
        prop_id = prop.get("id", "")
        title = prop.get("title", "Untitled proposal")
        lifecycle = prop.get("lifecycle", "open")
        kind = prop.get("proposal_kind", "")

        text = f"{title} ({kind}) -- {lifecycle}"
        ref = f"decision:{prop_id}" if prop_id else f"decision:unknown_{ordinal}"
        # An ACCEPTED proposal is a decision; anything else is still a
        # proposal.  Acceptance mirrors the recorded decision -- it comes
        # from the review path, never from a model score (C2).
        acceptance = _PROPOSAL_ACCEPTANCE.get(lifecycle, ACCEPTANCE_UNREVIEWED)
        kind = (
            KIND_DECISION if acceptance == ACCEPTANCE_ACCEPTED
            else KIND_PROPOSAL
        )
        record = _field_mapping_support(
            source_version, [ref], ["title", "proposal_kind", "lifecycle"],
        )
        decided_by = prop.get("decided_by_ref")
        if decided_by:
            record = SupportRecord(
                method=record.method,
                source_version=record.source_version,
                source_refs=record.source_refs,
                fields=record.fields,
                reviewer_ref=str(decided_by),
            )
        claims.append(Claim(
            span_id=f"s_decisions_{ordinal}",
            text=text,
            refs=[ref],
            section="decisions",
            kind=kind,
            support=SUPPORT_SUPPORTED,
            acceptance=acceptance,
            support_record=record,
        ))
        lines.append(f"- {text}")
        ordinal += 1

    return "\n".join(lines)


#: The change class a merged PR or a resolved issue carries (the delta's
#: ``_classify_observation``; persisted on the proposal since Conductor K4).
CHANGE_CLASS_CLOSED = "closed"


#: The source-manifest key that freezes what a draft reported as closed.
CLOSURE_KEYS = "closure_keys"
#: PHILO-15 B52: each closure key's row text, frozen with the draft. Its
#: presence also marks a manifest made since PHILO-15, when every draft (a
#: model draft too) carries the rows word for word.
CLOSURE_LINES = "closure_lines"


def merged_line(title: str, number: str, url: str) -> str:
    """The one row a merged PR gets in an update (PHILO-15 B52):
    ``Merged: <PR title> (PR #n) <link>``."""
    name = " ".join(str(title or "").split()) or "Untitled"
    return f"Merged: {name} (PR #{number})" + (f" {url}" if url else "")


def reported_closures(published: list[dict[str, Any]]) -> set[str]:
    """The closure keys the PUBLISHED updates reported (PHILO-15 B52, Astra
    r1 rulings):

    - a published update reports every key frozen into its manifest: its
      draft carried every row, so a row the owner cut before he published is
      an intentional exclusion and stays out;
    - a draft that was discarded or superseded is never published and
      consumes nothing;
    - a manifest from before PHILO-15 (keys, no ``closure_lines``) consumes
      nothing: its model draft may have dropped the row (the B52 loss), so
      the merge is reported once more rather than never."""
    reported: set[str] = set()
    for row in published:
        try:
            frozen = json.loads(row.get("source_manifest_json") or "{}")
        except (TypeError, ValueError):
            frozen = {}
        if isinstance(frozen, dict) and isinstance(frozen.get(CLOSURE_LINES), dict):
            reported.update(str(k) for k in frozen.get(CLOSURE_KEYS) or [])
    return reported


def _row_lines(body_md: str) -> set[str]:
    """The body's lines as rows: list marker and spacing dropped, so a row is
    matched whole (``(PR #1) …/pull/1`` never matches ``…/pull/10``)."""
    out: set[str] = set()
    for line in str(body_md or "").splitlines():
        text = " ".join(line.split())
        if text.startswith(("- ", "* ")):
            text = text[2:]
        if text:
            out.add(text)
    return out

#: Conductor R4: a merged agent PR linked to its origin in the Room
#: (``delivery.follow_through.LINK_OBSERVATION``).
LINK_OBSERVATION_KIND = "conductor.pr_linked"
#: Conductor R4: one merged PR of a Room repository, read by the Heartbeat
#: (``delivery.merged_prs``).
MERGED_OBSERVATION_KIND = "conductor.pr_merged"


def period_closures(
    observations: list[dict[str, Any]],
    completions: list[dict[str, Any]],
    action_tasks: dict[str, str],
    reported: set[str],
) -> list[dict[str, Any]]:
    """What closed and no PUBLISHED update has reported yet, from durable
    records only (never from a review window, which opens and closes on the
    owner's word, and never by a time cutoff, which a draft frozen before its
    publication would miss):

    - a Watch's closing transition (``github.pr.merged``,
      ``jira.issue.resolved``);
    - a ``commitment.completed`` receipt of one of the Project's action items
      that carries PR evidence (Conductor K4: the agent launch's merged PR);
    - a merged agent PR linked to its origin in the Room (R4,
      ``conductor.pr_linked``);
    - any merged PR of a Room repository the Heartbeat read (R4,
      ``conductor.pr_merged``).

    Each closure has a key (the PR URL, else the watch entity and event).
    ``reported`` holds the keys every published update froze into its source
    manifest. One line per key: a PR seen by both paths is reported once."""
    from .project_delta_service import _classify_observation

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    pr_titles: dict[str, str] = {}
    for obs in observations:
        if obs.get("observation_kind") not in (MERGED_OBSERVATION_KIND, LINK_OBSERVATION_KIND):
            continue
        try:
            fact = json.loads(obs.get("fact_json") or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(fact, dict) or not fact.get("pr_url"):
            continue
        title = fact.get("pr_title") if obs.get("observation_kind") == LINK_OBSERVATION_KIND else fact.get("title")
        if title:
            pr_titles.setdefault(str(fact["pr_url"]), " ".join(str(title).split()))
    for event in completions:
        facts = event.get("facts") or {}
        evidence = facts.get("evidence") or {}
        url = str(evidence.get("pr_url") or "")
        action_id = str(facts.get("action_item_id") or "")
        if not url or action_id not in action_tasks:
            continue
        if url in seen or url in reported:
            continue
        seen.add(url)
        number = str(evidence.get("pr_number") or url.rstrip("/").rsplit("/", 1)[-1])
        # PHILO-15 B52/B50: the row names the PR by ITS title (gh's), never
        # the item's: the receipt's own, else the Heartbeat's read of the
        # same merge, else the item's task for a receipt from before.
        title = (
            str(evidence.get("pr_title") or "") or pr_titles.get(url)
            or str(action_tasks[action_id] or "")
        )
        out.append({
            "key": url,
            "order": (str(evidence.get("merged_at") or ""), url),
            "text": merged_line(title, number, url),
            "ref": format_ref("action_item", action_id),
            "fields": ["status", "evidence.pr_url", "evidence.merged_at"],
        })

    def r4_lines(wanted: str) -> None:
        # Conductor R4: a merged agent PR linked to its origin in the Room (a
        # note, a meeting, an issue...), and every merge a Room repository
        # reports (the Heartbeat's merged-only read). One line per PR URL.
        for obs in observations:
            if obs.get("observation_kind") != wanted:
                continue
            try:
                fact = json.loads(obs.get("fact_json") or "{}")
            except (TypeError, ValueError):
                continue
            if not isinstance(fact, dict):
                continue
            url = str(fact.get("pr_url") or "")
            if not url or url in seen or url in reported:
                continue
            seen.add(url)
            number = str(fact.get("pr_number") or url.rstrip("/").rsplit("/", 1)[-1])
            # A link observation's ``title`` is its origin's; the PR's own
            # title is ``pr_title`` (PHILO-15 B52), else the Heartbeat's read.
            title = (
                (fact.get("pr_title") or pr_titles.get(url) or fact.get("title"))
                if wanted == LINK_OBSERVATION_KIND else fact.get("title")
            )
            text = merged_line(str(title or ""), number, url)
            out.append({
                "key": url,
                "order": (str(fact.get("merged_at") or obs.get("observed_at") or ""), url),
                "text": text,
                "ref": f"pobs:{obs.get('id', '')}",
                "fields": ["observation_kind", "fact_json"],
            })

    r4_lines(LINK_OBSERVATION_KIND)
    for obs in observations:
        if obs.get("observation_kind") != "watch.transition":
            continue
        if _classify_observation(obs) != CHANGE_CLASS_CLOSED:
            continue
        try:
            fact = json.loads(obs.get("fact_json") or "{}")
        except (TypeError, ValueError):
            fact = {}
        if not isinstance(fact, dict):
            fact = {}
        entity = str(fact.get("entity_ref") or "").strip()
        event_type = str(fact.get("event_type") or "")
        key = str(fact.get("url") or "") or f"{obs.get('source_id')}:{entity}:{event_type}"
        if key in seen or key in reported:
            continue
        seen.add(key)
        name = " ".join(str(fact.get("entity_title") or entity or "Untitled").split())
        marker = f" (#{entity})" if entity else ""
        outcome = event_type.rsplit(".", 1)[-1] or CHANGE_CLASS_CLOSED
        out.append({
            "key": key,
            "order": (str(obs.get("observed_at") or ""), key),
            # PHILO-15 B52: a merged PR reads as every merged PR does.
            "text": (
                merged_line(name, entity, str(fact.get("url") or ""))
                if event_type == "github.pr.merged" and entity
                else f"Closed: {name}{marker} -- {outcome}"
            ),
            "ref": f"pobs:{obs.get('id', '')}",
            "fields": ["observation_kind", "fact_json"],
        })
    # A Watch's own merge line wins over the Heartbeat's merged-only read.
    r4_lines(MERGED_OBSERVATION_KIND)
    return sorted(out, key=lambda c: c["order"])


def _build_closed(
    closures: list[dict[str, Any]],
    claims: list[Claim],
    source_version: str,
) -> list[str]:
    """Progress lines for what closed in the period (merged, resolved)."""
    lines: list[str] = []
    for ordinal, closure in enumerate(closures):
        claims.append(Claim(
            span_id=f"s_progress_closed_{ordinal}",
            text=closure["text"],
            refs=[closure["ref"]],
            section="progress",
            # Read off a durable record: an observation, a field mapping (C2).
            kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [closure["ref"]], closure["fields"],
            ),
        ))
        lines.append(f"- {closure['text']}")
    return lines


def _carry_closed_rows(
    body_md: str,
    claims_json: str,
    closed_lines: list[str],
    det_claims: list[Claim],
) -> tuple[str, str]:
    """PHILO-15 B52: every closed row of the deterministic inventory, in the
    model draft's Progress, word for word, with its claim. A row the model
    already wrote is not repeated."""
    present = _row_lines(body_md)
    missing = [line for line in closed_lines if " ".join(line.split())[2:] not in present]
    if missing:
        head = f"## {_SECTION_HEADINGS['progress']}\n\n"
        block = "\n".join(missing)
        at = body_md.find(head)
        if at < 0:
            body_md = head + block + "\n\n" + body_md
        else:
            start = at + len(head)
            minimal = _HONEST_MINIMAL["progress"]
            if body_md.startswith(minimal, start):
                body_md = body_md[:start] + block + body_md[start + len(minimal):]
            else:
                body_md = body_md[:start] + block + "\n" + body_md[start:]
    try:
        claims = json.loads(claims_json or "[]")
    except (TypeError, ValueError):
        claims = []
    if isinstance(claims, list):
        texts = {str(c.get("text") or "") for c in claims if isinstance(c, dict)}
        added = [
            c.to_dict() for c in det_claims
            if c.span_id.startswith("s_progress_closed_") and c.text not in texts
        ]
        if added:
            claims_json = json.dumps(claims + added, sort_keys=True, separators=(",", ":"))
    return _drop_repeated_merges(body_md, claims_json, closed_lines)


#: A PR named with its repository: ``owner/repo/pull/4`` (a link), ``owner/repo#4``.
_PR_IN_REPO = _re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?:/pull/|#)(\d+)\b")
#: A PR named by number alone: ``PR #4``, ``pull request #4``.
_PR_BARE = _re.compile(r"\b(?:PR|pull request)\s*#(\d+)\b", _re.IGNORECASE)


def _named_prs(text: str, default_repos: dict[str, set[str]]) -> set[tuple[str, str]]:
    """The (repository, number) pairs a sentence names. A bare ``PR #n`` is
    the Merged rows' repository only when exactly one of them has that
    number (Astra r1 P2-5: never a number alone across repositories)."""
    found = {(m.group(1).lower(), m.group(2)) for m in _PR_IN_REPO.finditer(text)}
    for m in _PR_BARE.finditer(text):
        repos = default_repos.get(m.group(1), set())
        found.add((next(iter(repos)), m.group(1)) if len(repos) == 1 else ("?", m.group(1)))
    return found


def _drop_repeated_merges(
    body_md: str, claims_json: str, closed_lines: list[str],
) -> tuple[str, str]:
    """PHILO-15 B71: a merge is said once, by its ``Merged:`` row. A model
    sentence (and its continuation lines) whose every named PR is one a
    ``Merged:`` row already carries (repository AND number, from the row's
    link) is dropped from the draft, with its claim; a sentence that names any
    other PR is kept. A section it leaves empty reads its honest minimum."""
    merged: set[tuple[str, str]] = set()
    for line in closed_lines:
        for m in _PR_IN_REPO.finditer(line):
            merged.add((m.group(1).lower(), m.group(2)))
    if not merged:
        return body_md, claims_json
    by_number: dict[str, set[str]] = {}
    for repo, number in merged:
        by_number.setdefault(number, set()).add(repo)
    rows = {" ".join(line.split())[2:] for line in closed_lines}
    out: list[str] = []
    dropped_texts: set[str] = set()
    skipping = False
    for line in body_md.splitlines():
        stripped = line.strip()
        if line.startswith("#"):
            skipping = False
            out.append(line)
            continue
        if stripped.startswith(("- ", "* ")):
            text = " ".join(stripped.split())[2:]
            named = _named_prs(text, by_number)
            if text not in rows and named and named <= merged:
                dropped_texts.add(text.replace(UNVERIFIED_MARKER, "").strip())
                skipping = True
                continue
            skipping = False
        elif skipping and stripped:
            continue  # the rest of the dropped sentence
        else:
            skipping = False
        out.append(line)
    if not dropped_texts:
        return body_md, claims_json
    body = _refill_empty_sections("\n".join(out) + ("\n" if body_md.endswith("\n") else ""))
    try:
        claims = json.loads(claims_json or "[]")
    except (TypeError, ValueError):
        return body, claims_json
    if isinstance(claims, list):
        def _first(c: Any) -> str:
            return " ".join(str(c.get("text") or "").split("\n", 1)[0].split())
        kept = [
            c for c in claims
            if not (isinstance(c, dict) and _first(c) in dropped_texts)
        ]
        claims_json = json.dumps(kept, sort_keys=True, separators=(",", ":"))
    return body, claims_json


def _refill_empty_sections(body_md: str) -> str:
    """A ``## <Section>`` left with no content reads its honest minimum."""
    by_heading = {f"## {_SECTION_HEADINGS[k]}": _HONEST_MINIMAL.get(k, "") for k in _SECTION_HEADINGS}
    lines = body_md.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if line in by_heading:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            if not any(ln.strip() for ln in lines[i + 1:j]) and by_heading[line]:
                out.extend(["", by_heading[line], ""])
                i = j
                continue
        i += 1
    return "\n".join(out) + ("\n" if body_md.endswith("\n") else "")


def _build_risks_blockers(
    items_section: dict[str, Any],
    claims: list[Claim],
    source_version: str,
) -> str:
    """Risks & Blockers from room items filtered to risk/dependency types."""
    focus = items_section.get("focus", [])
    risk_items = [
        item for item in focus
        if item.get("item_type") in ("risk", "dependency")
        and item.get("lifecycle") in ("open", "at_risk", "broken")
    ]
    if not risk_items:
        return _HONEST_MINIMAL["risks_blockers"]

    lines: list[str] = []
    for i, item in enumerate(risk_items):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        item_type = item.get("item_type", "item")
        lifecycle = item.get("lifecycle", "unknown")
        severity = item.get("severity")

        sev_str = f" [{severity}]" if severity else ""
        text = f"{item_type.capitalize()}{sev_str}: {title} -- {lifecycle}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_rb_{i}"
        claims.append(Claim(
            span_id=f"s_risks_blockers_{i}",
            text=text,
            refs=[ref],
            section="risks_blockers",
            kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref],
                ["item_type", "severity", "title", "lifecycle"],
            ),
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


def _build_dependencies(
    items_section: dict[str, Any],
    claims: list[Claim],
    source_version: str,
) -> str:
    """Dependencies from room items filtered to dependency type."""
    focus = items_section.get("focus", [])
    dep_items = [
        item for item in focus
        if item.get("item_type") == "dependency"
    ]
    if not dep_items:
        return _HONEST_MINIMAL["dependencies"]

    lines: list[str] = []
    for i, item in enumerate(dep_items):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        lifecycle = item.get("lifecycle", "unknown")
        severity = item.get("severity")

        sev_str = f" [{severity}]" if severity else ""
        text = f"Dependency{sev_str}: {title} -- {lifecycle}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_dep_{i}"
        claims.append(Claim(
            span_id=f"s_dependencies_{i}",
            text=text,
            refs=[ref],
            section="dependencies",
            kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref], ["title", "severity", "lifecycle"],
            ),
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


def _build_next_actions(
    items_section: dict[str, Any],
    claims: list[Claim],
    source_version: str,
) -> str:
    """Next actions: items with planned/active states or upcoming due dates."""
    focus = items_section.get("focus", [])
    action_items = [
        item for item in focus
        if item.get("lifecycle") in ("planned", "active")
        or item.get("due_at") is not None
    ]
    if not action_items:
        return _HONEST_MINIMAL["next_actions"]

    lines: list[str] = []
    for i, item in enumerate(action_items):
        item_id = item.get("id", "")
        title = item.get("title", "Untitled")
        item_type = item.get("item_type", "item")
        lifecycle = item.get("lifecycle", "unknown")
        due_at = item.get("due_at")

        due_str = f", due {due_at}" if due_at else ""
        text = f"{item_type.capitalize()}: {title} -- {lifecycle}{due_str}"
        ref = f"item:{item_id}" if item_id else f"item:unknown_na_{i}"
        claims.append(Claim(
            span_id=f"s_next_actions_{i}",
            text=text,
            refs=[ref],
            section="next_actions",
            kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref],
                ["item_type", "title", "lifecycle", "due_at"],
            ),
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


def _build_source_coverage(
    room: dict[str, Any],
    caveats: list[dict[str, str]],
    claims: list[Claim],
    source_version: str,
) -> str:
    """Source coverage section: appears only when caveats exist."""
    if not caveats:
        return _HONEST_MINIMAL["source_coverage"]

    lines: list[str] = []
    for i, caveat in enumerate(caveats):
        section_name = caveat.get("section", "unknown")
        state = caveat.get("state", "unknown")
        reason = caveat.get("reason", "")

        # PHILO-15 B53: plain words, never a raw code (the update is sent).
        word = {"degraded": "partly read", "absent": "not read"}.get(state, state)
        reason_str = f": {reason.replace('_', ' ')}" if reason else ""
        text = f"{str(section_name).capitalize()} {word}{reason_str}"
        ref = f"project:{room.get('project_id', 'unknown')}"
        claims.append(Claim(
            span_id=f"s_source_coverage_{i}",
            text=text,
            refs=[ref],
            section="source_coverage",
            kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref], ["section", "state", "reason"],
            ),
        ))
        lines.append(f"- {text}")

    return "\n".join(lines)


# ── Source manifest builder ───────────────────────────────────────────

def _build_source_manifest(
    room: dict[str, Any],
    review_id: str | None,
    observation_ids: list[str],
    caveats: list[dict[str, str]],
) -> dict[str, Any]:
    """Build the source_manifest_json recording exactly what the draft saw."""
    manifest: dict[str, Any] = {
        "project_revision": room.get("revision", 0),
    }
    if review_id:
        manifest["review_id"] = review_id
    manifest["observation_ids"] = sorted(observation_ids)
    manifest["caveats"] = sorted(caveats, key=lambda c: c.get("section", ""))
    return manifest


# ── Room section caveat scanner ───────────────────────────────────────

_CAVEAT_SECTIONS = ("items", "meetings", "resources", "changes", "review")


def _scan_caveats(room: dict[str, Any]) -> list[dict[str, str]]:
    """Scan room sections for degraded/absent state (the 158 vocabulary)."""
    caveats: list[dict[str, str]] = []
    for section_key in _CAVEAT_SECTIONS:
        section = room.get(section_key, {})
        state = section.get("state", "absent")
        if state in ("degraded", "absent"):
            caveat: dict[str, str] = {"section": section_key, "state": state}
            error_code = section.get("error_code")
            reason = section.get("reason")
            if error_code:
                caveat["reason"] = error_code
            elif reason:
                caveat["reason"] = reason
            caveats.append(caveat)
    return sorted(caveats, key=lambda c: c["section"])


# ── Deterministic Markdown assembler ──────────────────────────────────

def _assemble_body(sections: dict[str, str]) -> str:
    """Assemble the six sections into the final Markdown body.

    Deterministic: sections are emitted in SECTION_KEYS order.
    """
    parts: list[str] = []
    for key in SECTION_KEYS:
        heading = _SECTION_HEADINGS[key]
        content = sections.get(key, _HONEST_MINIMAL[key])
        parts.append(f"## {heading}\n\n{content}")
    return "\n\n".join(parts) + "\n"


# ── Model drafter helpers (HS-162-03) ────────────────────────────────

_THINK_RE = _re.compile(r"<think>.*?</think>", _re.DOTALL)
_FENCE_RE = _re.compile(r"```(?:json)?\s*(.*?)\s*```", _re.DOTALL)


def _extract_structured_json(raw: str) -> dict[str, Any] | None:
    """Best-effort extraction of a JSON object from an LLM response.

    Strips ``<think>...</think>`` blocks, tries markdown-fenced JSON
    first, then scans for the first balanced ``{...}`` substring.
    Returns ``None`` when no valid JSON dict is found.
    """
    if not raw:
        return None
    cleaned = _THINK_RE.sub("", raw).strip()
    fence = _FENCE_RE.search(cleaned)
    if fence:
        try:
            obj = json.loads(fence.group(1))
            if isinstance(obj, dict):
                return obj
        except (ValueError, TypeError):
            pass
    depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = json.loads(cleaned[start : i + 1])
                    if isinstance(obj, dict):
                        return obj
                except (ValueError, TypeError):
                    pass
                start = -1
    return None


# Model output JSON schema for response_format (structured output).
_MODEL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "sentences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "cited_refs": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["text", "cited_refs"],
                        },
                    },
                },
                "required": ["key", "sentences"],
            },
        },
    },
    "required": ["sections"],
}


def _build_model_prompt(
    inventory_claims: list[Claim], memory: Any | None = None,
) -> dict[str, Any]:
    """Build a prompt payload from the deterministic evidence inventory.

    The model is given every deterministic claim (with its refs) and asked
    to rewrite the sections with better prose, citing the exact refs.

    ``memory`` (a ``MemoryContext``) adds the project's remembered sources
    in one marked block.  Its refs are citable like inventory refs.  With no
    memory the prompt is byte-identical to the one before memory existed.
    """
    by_section: dict[str, list[Claim]] = {}
    for claim in inventory_claims:
        by_section.setdefault(claim.section, []).append(claim)

    inventory_lines: list[str] = []
    for section_key in SECTION_KEYS:
        claims = by_section.get(section_key, [])
        inventory_lines.append(f"\n[section: {section_key}]")
        if claims:
            for c in claims:
                refs_str = ", ".join(c.refs)
                inventory_lines.append(
                    f"- {c.span_id}: {c.text!r} | refs: {refs_str}"
                )
        else:
            honest = _HONEST_MINIMAL.get(section_key, "")
            inventory_lines.append(f"- (empty section -- use: {honest!r})")

    system_prompt = (
        "You are a stakeholder update writer. Rewrite the evidence "
        "inventory below into clear, concise prose that a non-technical "
        "stakeholder can read. Do NOT add any facts, conclusions, or "
        "commentary beyond what the inventory states.\n\n"
        "RULES:\n"
        "1. Every sentence MUST cite at least one ref from the inventory "
        "using the EXACT ref strings provided.\n"
        "2. Preserve every ref from the inventory verbatim -- never "
        "invent, abbreviate, or paraphrase a ref.\n"
        "3. Do NOT add facts, analysis, or value judgments that are not "
        "grounded in the inventory. If you write a sentence that is "
        "not directly supported by an inventory entry, set cited_refs "
        "to an empty list so it can be flagged for review.\n"
        "4. Cover all six sections in order: progress, decisions, "
        "risks_blockers, dependencies, next_actions, source_coverage.\n"
        "5. For empty sections, write the honest minimal line.\n"
        "6. Keep prose concise and factual -- no filler.\n\n"
        "Respond with ONLY a JSON object:\n"
        '{"sections": [{"key": "<section_key>", "sentences": '
        '[{"text": "<sentence>", "cited_refs": ["<ref1>", ...]}]}]}'
    )

    user_prompt = "EVIDENCE INVENTORY:\n" + "\n".join(inventory_lines)
    memory_block = memory.prompt_block(MEMORY_BLOCK_HEADING) if memory else ""
    if memory_block:
        system_prompt += (
            "\n\nThe user message also has a "
            f"[{MEMORY_BLOCK_HEADING}] block: earlier decisions, notes and "
            "meetings of this project. Use it to say what changed and what "
            "is still open. Its refs count as inventory refs: cite them "
            "exactly. Do not state a memory entry as new work of this period."
        )
        user_prompt += "\n\n" + memory_block

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "project_update",
                "schema": _MODEL_OUTPUT_SCHEMA,
            },
        },
    }


# ── The deterministic literal check (HS-200-06, C2) ──────────────────
#
# Generated prose requires a SEPARATE support check.  A valid reference
# buys source linkage only.  Every name, deadline and number the prose
# states must appear in the cited source's fields; whatever does not
# becomes a TYPED UNKNOWN and the claim stays source-linked.

_DATE_LITERAL_RE = _re.compile(
    r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?\b"
)
# A clock time is ONE token (`04:00`), never two numbers (HS-200-11 counsel).
_TIME_LITERAL_RE = _re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_NUMBER_LITERAL_RE = _re.compile(r"(?<![\w-])\d+(?:[.,]\d+)?%?(?![\w-])")
# A capitalised token, hyphenated parts INCLUDED so `Cut-over` and `KAN-7`
# are one token each and never split into halves (HS-200-11 counsel).
_CAP_TOKEN_RE = _re.compile(r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*\b")
_SENTENCE_START_RE = _re.compile(r"(?:^|[.!?:]\s+|--\s+)")

# Capitalized words that are grammar or report vocabulary, not names.
_NAME_STOPWORDS: frozenset[str] = frozenset({
    "A", "Action", "Actions", "Active", "After", "All", "Also", "An",
    "And", "As", "At", "Based", "Before", "Blocked", "Blockers", "Both",
    "But", "By", "Closed", "Completed", "Coverage", "Currently",
    "Deadline", "Decision", "Decisions", "Delivery", "Dependencies",
    "Dependency", "Due", "During", "Each", "Every", "For", "From",
    "However", "If", "In", "Is", "It", "Item", "Items", "Its", "Many",
    "Meeting", "Milestone", "Most", "New", "Next", "No", "None", "Not",
    "Of", "On", "One", "Open", "Or", "Our", "Overall", "Owner", "Per",
    "Planned", "Progress", "Project", "Remaining", "Review", "Risk",
    "Risks", "Signal", "Since", "Some", "Source", "Sources", "Status",
    "Team", "The", "There", "These", "They", "This", "Those", "Three",
    "To", "Two", "Until", "Update", "We", "When", "While", "With",
    "Work", "Workstream", "Who", "What", "Where", "Why", "How", "Nobody",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December", "Superseded",
})


def _normalize_for_match(text: str) -> str:
    """Lowercase, collapse whitespace -- the corroboration haystack."""
    return " ".join(str(text or "").lower().split())


def _is_acronym(token: str) -> bool:
    """`KAN`, `DNS`, `KAN-7`, `QA`: upper-case letters, digits and hyphens only."""
    letters = [c for c in token if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _typed_unknowns(
    text: str,
    source_text: str,
    known_names: Any = (),
) -> list[dict[str, str]]:
    """Literals in ``text`` that the cited source's fields do not carry.

    Returns typed unknowns sorted deterministically:
    ``[{"type": "deadline"|"number"|"name", "value": "..."}]``.

    The NAME rule (HS-200-11 counsel, measured over 30 realistic sentences,
    28 false positives under the old regex):

    - a sentence-initial single capitalised word is grammar, never a name;
    - a hyphenated word is one token and never split into halves;
    - an all-caps token is an acronym, never a name;
    - a sentence with NO source (empty ``source_text``) mints no NAME at
      all -- its face already says ``NO SOURCE``;
    - a name survives only as a MULTI-WORD capitalised sequence, or as a
      single word that matches a known-person alias in ``known_names``
      (the People ledger, the Room's owners).
    """
    haystack = _normalize_for_match(source_text)
    found: set[tuple[str, str]] = set()

    masked = text
    for match in _DATE_LITERAL_RE.finditer(text):
        value = match.group(0)
        if _normalize_for_match(value) not in haystack:
            found.add(("deadline", value))
    masked = _DATE_LITERAL_RE.sub(" ", masked)

    for match in _TIME_LITERAL_RE.finditer(masked):
        value = match.group(0)
        if _normalize_for_match(value) not in haystack:
            found.add(("number", value))
    masked = _TIME_LITERAL_RE.sub(" ", masked)

    for match in _NUMBER_LITERAL_RE.finditer(masked):
        value = match.group(0)
        if _normalize_for_match(value) not in haystack:
            found.add(("number", value))

    if haystack:
        aliases = {_normalize_for_match(n) for n in (known_names or ()) if str(n or "").strip()}
        starts = {m.end() for m in _SENTENCE_START_RE.finditer(masked)}
        runs: list[list[tuple[str, int]]] = []
        current: list[tuple[str, int]] = []
        last_end = -1
        for match in _CAP_TOKEN_RE.finditer(masked):
            token = match.group(0)
            if token in _NAME_STOPWORDS or _is_acronym(token) or any(c.isdigit() for c in token):
                if current:
                    runs.append(current)
                current = []
                last_end = -1
                continue
            gap = masked[last_end:match.start()] if last_end >= 0 else ""
            if current and gap.strip() == "":
                current.append((token, match.start()))
            else:
                if current:
                    runs.append(current)
                current = [(token, match.start())]
            last_end = match.end()
        if current:
            runs.append(current)
        for run in runs:
            value = " ".join(tok for tok, _ in run)
            normalized = _normalize_for_match(value)
            if normalized in haystack:
                continue
            if len(run) >= 2:
                found.add(("name", value))
                continue
            token, at = run[0]
            if normalized in aliases:
                found.add(("name", token))
                continue
            # A single capitalised word: only an alias earns it, and never
            # at the start of a sentence.
            del at

    return [
        {"type": kind, "value": value}
        for kind, value in sorted(found)
    ]


def _known_names_for_room(room: dict[str, Any]) -> set[str]:
    """The Room's own people: item owners, commitment owners, team members.

    The alias set a name unknown may match against -- an invented owner is
    an unknown only when the desk KNOWS that person (HS-200-11 counsel)."""
    names: set[str] = set()
    project = room.get("project") or {}
    for member in project.get("team_members") or project.get("team_members_json") or []:
        if isinstance(member, str) and member.strip():
            names.add(member.strip())
        elif isinstance(member, dict):
            for key in ("name", "display_name", "label"):
                if member.get(key):
                    names.add(str(member[key]).strip())
    for section_key in ("items", "commitments"):
        section = room.get(section_key) or {}
        for item in section.get("items") or []:
            owner = item.get("owner") or item.get("owner_ref")
            if owner and isinstance(owner, str):
                names.add(owner.split(":", 1)[-1].strip())
    return {n for n in names if n}


def _parse_model_output(
    raw: str,
    inventory_refs: frozenset[str],
    inventory_texts: dict[str, str] | None = None,
    known_names: Any = (),
) -> tuple[dict[str, str], list[Claim]] | None:
    """Parse model JSON output into sections + claims.

    Returns ``(sections_dict, claims_list)`` on success, ``None`` if the
    output is unparseable.  Each claim is either verified (all cited_refs
    exist in the inventory) or MARKED (``verified=False``).

    C2 (HS-200-06): generated prose NEVER reaches ``supported`` here.
    A valid ref buys ``source_linked``; an invalid or absent ref leaves
    ``unknown``.  ``inventory_texts`` maps each inventory ref to the
    recorded fields behind it; literals the cited source does not carry
    are recorded as typed unknowns.  Acceptance is always
    ``unreviewed`` -- no model output can move it.
    """
    parsed = _extract_structured_json(raw)
    if parsed is None or "sections" not in parsed:
        return None

    sections: dict[str, str] = {}
    claims: list[Claim] = []

    for section_data in parsed.get("sections", []):
        key = section_data.get("key", "")
        if key not in SECTION_KEYS:
            continue

        sentences = section_data.get("sentences", [])
        lines: list[str] = []

        for i, sentence in enumerate(sentences):
            text = str(sentence.get("text", "")).strip()
            if not text:
                continue
            cited = sentence.get("cited_refs", [])
            if not isinstance(cited, list):
                cited = []

            # Validate: keep only refs that appear in the inventory.
            valid_refs = [r for r in cited if isinstance(r, str) and r in inventory_refs]

            if valid_refs:
                # A real citation establishes SOURCE LINKAGE only (C2).
                # The literal check names what the source cannot carry --
                # an irrelevant citation cannot support invented prose.
                source_text = " ".join(
                    [(inventory_texts or {}).get(r, "") for r in valid_refs]
                    + valid_refs
                )
                claims.append(Claim(
                    span_id=f"s_{key}_{i}",
                    text=text,
                    refs=valid_refs,
                    section=key,
                    verified=True,
                    kind=KIND_INFERENCE,
                    support=SUPPORT_SOURCE_LINKED,
                    acceptance=ACCEPTANCE_UNREVIEWED,
                    unknowns=_typed_unknowns(text, source_text, known_names),
                ))
                lines.append(f"- {text}")
            else:
                # MARKED: unverified claim -- no valid evidence refs.
                claims.append(Claim(
                    span_id=f"s_{key}_{i}",
                    text=text,
                    refs=[],
                    section=key,
                    verified=False,
                    kind=KIND_INFERENCE,
                    support=SUPPORT_UNKNOWN,
                    acceptance=ACCEPTANCE_UNREVIEWED,
                    unknowns=_typed_unknowns(text, ""),
                ))
                # The mark rides EVERY line of the claim (Astra r2): a claim
                # with embedded newlines is omitted whole when it leaves the
                # desk, never only its first line.
                lines.append(f"- {UNVERIFIED_MARKER} " + text.replace("\n", f"\n  {UNVERIFIED_MARKER} "))

        if lines:
            sections[key] = "\n".join(lines)
        else:
            sections[key] = _HONEST_MINIMAL.get(key, "")

    # Fill missing sections with honest minimums.
    for key in SECTION_KEYS:
        if key not in sections:
            sections[key] = _HONEST_MINIMAL.get(key, "")

    return sections, claims


def _route_plan_deployment(broker: Any, capability_id: str) -> tuple[str, str, str]:
    """The authoritative resolution: profile -> plan -> frozen leg (HS-200-08).

    This is the SAME resolver the Ask path runs (``route_probe.preview_route``
    reads exactly this plan): the capability's assignment is planned, and the
    first frozen leg NAMES its deployment revision.  Returns
    ``(deployment_revision_id, assignment_id, profile_id)``, or empty strings
    when this broker carries no planner or the plan does not resolve.
    """
    plans = getattr(getattr(broker, "inference_adoption_service", None), "plans", None)
    if plans is None:
        return "", "", ""
    try:
        from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY

        plan = plans.resolve_route_plan(
            ROUTE_PLANNING_AUTHORITY, capability_id=capability_id,
        )
    except Exception as exc:  # planner refusals are a fallback, never a crash
        _log.warning(
            "Route plan for %s did not resolve: %s", capability_id, exc,
        )
        return "", "", ""
    entries = [e for e in (plan.get("entries") or ()) if e]
    if not entries:
        return "", "", ""
    leg = min(entries, key=lambda e: int(e.get("ordinal") or 0))
    revision_id = str(leg.get("deployment_revision_id") or "")
    assignment_id = str((plan.get("source") or {}).get("assignment_id") or "")
    profile_id = str(leg.get("profile_id") or "")
    if not revision_id:
        return "", "", ""
    # The plan resolves purely (it rolls its snapshot back), so a legacy leg's
    # content-addressed revision may never have been persisted.  The runner
    # refuses a revision it cannot read, so capture it the way Ask does.
    db = getattr(broker, "database", None)
    if db is not None and db.deployment_revisions.get(revision_id) is None:
        captured = _captured_deployment_revision(db, profile_id)
        if not captured:
            return "", "", ""
        if captured != revision_id:
            _log.warning(
                "Frozen leg named %s; captured %s for profile %s.",
                revision_id, captured, profile_id,
            )
        revision_id = captured
    return revision_id, assignment_id, profile_id


def _bound_deployment_revision(db: Any, profile_id: str) -> str:
    """The deployment revision the profile's live binding head points at.

    The second resolver, for a broker with no planner wired.  It reads the
    binding the planner itself reads (``model_profile_binding_heads`` ->
    ``model_profile_binding_revisions.deployment_revision_id``), never the
    ``deployment_revisions.model`` column.
    """
    if not profile_id:
        return ""
    with db._connection() as conn:
        row = conn.execute(
            """SELECT b.deployment_revision_id AS rev
                 FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                WHERE h.profile_id=?""",
            (profile_id,),
        ).fetchone()
        if row is None:
            return ""
        revision_id = str(row["rev"] or "")
        if not revision_id:
            return ""
        exists = conn.execute(
            "SELECT 1 FROM deployment_revisions WHERE id=?", (revision_id,),
        ).fetchone()
    return revision_id if exists is not None else ""


def _captured_deployment_revision(db: Any, profile_id: str) -> str:
    """Capture (and persist) the profile's deployment exactly as Ask does.

    The last resolver: a version-1 profile has no binding row, so the Ask
    path's ``capture_deployment_revision`` is what freezes its deployment.
    """
    if not profile_id:
        return ""
    try:
        from ..deployment_revisions import capture_deployment_revision
        from ..inference_targets import resolve_inference_target

        target = resolve_inference_target(db, profile_id.removeprefix("legacy-"))
        if getattr(target, "deployment", None) is None:
            return ""
        return str(capture_deployment_revision(db, target).id)
    except Exception as exc:
        _log.warning(
            "Could not capture a deployment for profile %s: %s",
            profile_id, exc,
        )
        return ""


def _resolve_for_capability(
    broker: Any,
    capability_id: str,
) -> tuple[str, str, str]:
    """Resolve the deployment revision and assignment ID for a capability.

    Returns ``(deployment_revision_id, assignment_id, profile_id)`` -- the
    profile is the one the route actually resolved through, so provenance
    never has to guess it back out of the revision's ``model`` column.
    Raises ``RuntimeError`` when no route resolves.

    HS-200-08: this used to run
    ``SELECT id FROM deployment_revisions WHERE model=?`` with the ASSIGNED
    PROFILE ID.  A captured revision's ``model`` column holds the real model
    id, so every profile whose id differs from its model id (the owner's own
    "Migrated intel endpoint", for one) resolved NOTHING and the model
    drafter silently fell back to the deterministic one.  A profile id is
    never string-matched against a model column again: resolution goes
    profile -> plan -> frozen leg -> deployment revision, the same path the
    Ask verb takes.
    """
    db = getattr(broker, "database", broker)

    # The planner first: it owns assignment inheritance (a capability with no
    # scoped assignment of its own still resolves through the global one), so
    # asking it first is what makes a real desk's route the drafter's route.
    planned_revision, planned_assignment, planned_profile = (
        _route_plan_deployment(broker, capability_id)
    )

    key = f"capability:{capability_id}"
    with db._connection() as conn:
        head = conn.execute(
            "SELECT assignment_id, revision FROM inference_assignment_heads "
            "WHERE assignment_key=? AND cleared=0",
            (key,),
        ).fetchone()
        entry = None
        if head is not None:
            entry = conn.execute(
                "SELECT profile_id FROM inference_assignments "
                "WHERE assignment_id=? AND assignment_revision=? "
                "ORDER BY ordinal LIMIT 1",
                (str(head["assignment_id"]), head["revision"]),
            ).fetchone()
    assignment_id = str(head["assignment_id"]) if head is not None else ""
    profile_id = str(entry["profile_id"] or "") if entry is not None else ""

    if planned_revision:
        return (
            planned_revision,
            (planned_assignment or assignment_id),
            (planned_profile or profile_id),
        )
    if head is None:
        raise RuntimeError(f"No assignment for {capability_id}")
    if entry is None:
        raise RuntimeError(f"No entries in assignment for {capability_id}")

    bound = _bound_deployment_revision(db, profile_id)
    if bound:
        return bound, assignment_id, profile_id

    captured = _captured_deployment_revision(db, profile_id)
    if captured:
        return captured, assignment_id, profile_id

    raise RuntimeError(
        f"No deployment revision resolves for profile {profile_id}"
    )


# ── Generator provenance (HS-173-02) ─────────────────────────────────

def _resolve_generator_provenance(
    db: Any,
    deployment_rev_id: str,
    profile_id: str = "",
) -> tuple[str, str]:
    """Derive generator host and model display name from a deployment revision.

    Returns ``(host, model_display_name)``.
    Host is derived the same way as 172's ``_placement_host``: node if
    present, else ``endpoint_host(endpoint)``, else boundary or ``"local"``.
    Model display name uses the Concierge's ``engine_display_name``.
    """
    from ..intel.providers import endpoint_host
    from .concierge_service import engine_display_name

    rev = db.deployment_revisions.get(deployment_rev_id)
    if rev is None:
        return ("local", "Unknown engine")

    # Host: same derivation as _placement_host in settings route.
    if rev.node:
        host = str(rev.node)
    else:
        host = endpoint_host(rev.endpoint)
        if not host:
            host = rev.boundary or "local"

    # Model display name: look up the profile for its name and model fields.
    # HS-200-08: the profile the ROUTE resolved through is the truth.  The
    # revision's ``model`` column holds the real model id, so looking a
    # profile up by it only ever worked for a profile named after its model.
    profile = db.profiles.get(profile_id) if profile_id else None
    if profile is None:
        profile = db.profiles.get(rev.model)
    if profile is not None:
        display, quant = engine_display_name(
            profile_name=profile.name or profile.id,
            profile_model=str(getattr(profile, "model", "") or ""),
        )
    else:
        # Fallback to the deployment revision's own engine field.
        display, quant = engine_display_name(profile_name=rev.engine)

    model_name = f"{display} {quant}".strip() if quant else display
    return host, model_name


# ── The conservative migration of citation-only records (HS-200-06) ──
#
# C2: old ``verified`` values retain their original provenance.  The
# stored blob is NEVER rewritten in place -- the mapping is applied when
# a record is READ, and every claim it touches carries
# ``support_mapping_version`` so the face can say MIGRATED and never
# "reviewed by a human".

def migrate_legacy_claim(
    raw: dict[str, Any],
    *,
    generator: str = "deterministic",
) -> dict[str, Any]:
    """Map one citation-only claim onto the three axes, conservatively.

    A citation buys SOURCE LINKAGE at most -- never ``supported``, never
    an acceptance.  ``verified`` is copied through untouched.
    Idempotent: a claim that already carries the axes is returned as-is.
    """
    if not isinstance(raw, dict):
        return raw
    if raw.get("support") in SUPPORT_STATES:
        return raw
    refs = raw.get("refs") or []
    verified = raw.get("verified", True)
    out = dict(raw)
    out["kind"] = (
        KIND_INFERENCE if str(generator).startswith("model")
        else KIND_OBSERVATION
    )
    out["support"] = (
        SUPPORT_SOURCE_LINKED if (refs and verified) else SUPPORT_UNKNOWN
    )
    out["acceptance"] = ACCEPTANCE_UNREVIEWED
    out["support_mapping_version"] = CLAIM_SUPPORT_MAPPING_VERSION
    return out


def migrate_claims_json(
    claims_json: str,
    *,
    generator: str = "deterministic",
) -> str:
    """Apply :func:`migrate_legacy_claim` across a stored claims blob.

    Returns the INPUT STRING unchanged when nothing needed mapping (so
    the determinism law still holds byte for byte).
    """
    if not claims_json:
        return claims_json
    try:
        parsed = json.loads(claims_json)
    except (ValueError, TypeError):
        return claims_json
    if not isinstance(parsed, list):
        return claims_json
    migrated = [migrate_legacy_claim(c, generator=generator) for c in parsed]
    if migrated == parsed:
        return claims_json
    return json.dumps(migrated, sort_keys=True, separators=(",", ":"))


# ── The service ───────────────────────────────────────────────────────

def attach_deliveries(db: Any, updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """PHILO-9-01: each update carries its ``deliveries``, oldest first.

    The owner's Q0 ruling (copy and confirm): each row is one confirmation
    that he delivered the published text himself. The product sends nothing;
    a draft has none.
    """
    by_update = db.project_update_deliveries.list_for_updates(
        [str(u.get("id") or "") for u in updates if u],
    )
    for update in updates:
        if update:
            update["deliveries"] = by_update.get(str(update.get("id") or ""), [])
    return updates


class ProjectUpdateService:
    """The Update Factory service (SRS SS8).

    draft_update reads the Project room truth over ONE pinned revision,
    emits editable Markdown with the UPD-001 sections, and persists via
    UpdatesRepository.  Regenerate = supersede unaccepted draft (UPD-004).
    """

    def __init__(
        self,
        db: Any,
        *,
        project_service: Any,
        delta_service: Any | None = None,
        broker: Any | None = None,
        people_names: Callable[[Principal], Iterable[str]] | None = None,
    ) -> None:
        self._db = db
        self._project_service = project_service
        self._delta_service = delta_service
        self._broker = broker
        # Betterment P2: his People's names, to tell a 1:1 by its speakers.
        # None (MCP, tests): the title rule alone.
        self._people_names = people_names

    # ── C2 read projection (HS-200-06) ───────────────────────────────

    @staticmethod
    def _project_axes(row: dict[str, Any] | None) -> dict[str, Any] | None:
        """Project the three C2 axes onto a row as it is READ.

        Records written before HS-200-06 keep their stored bytes; the
        conservative mapping is applied here, on the way out.

        HS-200-08: a fallback draft stores its reason on the generator
        (``deterministic:<code>``).  It is split back out here so
        ``generator`` stays the two values every caller already knows and
        the reason travels as ``fallback_reason`` + ``fallback_receipt``.
        """
        if not row:
            return row
        out = dict(row)
        generator = str(out.get("generator") or "deterministic")
        reason: str | None = None
        if generator.startswith(FALLBACK_GENERATOR_PREFIX):
            reason = generator[len(FALLBACK_GENERATOR_PREFIX):] or None
            generator = "deterministic"
            out["generator"] = generator
        out["fallback_reason"] = reason
        out["fallback_receipt"] = fallback_receipt_token(reason)
        out["claims_json"] = migrate_claims_json(
            out.get("claims_json") or "",
            generator=generator,
        )
        return out

    # ── Model drafter (HS-162-03) ────────────────────────────────────

    def _draft_with_model(
        self,
        principal: Principal,
        det_claims: list[Claim],
        det_sections: dict[str, str],
        det_body_md: str,
        known_names: Any = (),
        memory: Any | None = None,
    ) -> tuple[str, str, str, str | None, str | None]:
        """Attempt model drafting over the deterministic evidence inventory.

        Returns ``(body_md, claims_json, generator, generator_host,
        generator_model)`` on success.
        Raises ``_ModelDraftFailed`` on any failure (router unavailable,
        model error, timeout, unparseable output).
        """
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.prompt_adapter import CanonicalPromptAdapter
        from ..kernel.runtime import _as_principal

        broker = self._broker
        if broker is None:
            raise _ModelDraftFailed(
                "no_broker", FALLBACK_MODEL_UNAVAILABLE,
                detail="the hub has no engine service",
            )

        runner = broker.inference_runner

        # Resolve deployment revision for the update-draft capability.
        try:
            deployment_rev_id, assignment_id, route_profile_id = (
                _resolve_for_capability(broker, PROJECT_UPDATE_CAPABILITY)
            )
        except RuntimeError as exc:
            raise _ModelDraftFailed(
                f"route_unresolved: {exc}", FALLBACK_ROUTE_UNRESOLVED,
                detail="no engine is set for updates",
            ) from exc

        # HS-173-02: derive generator provenance from the deployment revision.
        gen_host: str | None = None
        gen_model: str | None = None
        try:
            gen_host, gen_model = _resolve_generator_provenance(
                broker.database, deployment_rev_id, route_profile_id,
            )
        except Exception:
            pass  # Provenance is best-effort; never fails the draft.

        # Build the evidence inventory from deterministic claims.
        inventory_refs: frozenset[str] = frozenset(
            ref for claim in det_claims for ref in claim.refs
        )
        # HS-200-06: the recorded fields behind each ref, for the
        # deterministic literal check in _parse_model_output.
        inventory_texts: dict[str, str] = {}
        for claim in det_claims:
            for ref in claim.refs:
                prior = inventory_texts.get(ref, "")
                inventory_texts[ref] = f"{prior} {claim.text}".strip()

        # The project's memory is citable context: its refs join the
        # inventory, and the literal check reads the remembered words.
        if memory:
            inventory_refs = inventory_refs | frozenset(memory.refs)
            for ref, text in memory.texts.items():
                inventory_texts.setdefault(ref, text)

        payload = _build_model_prompt(det_claims, memory)

        # PHILO-9-02 (the steward beat, section 5): a model draft made inside
        # the steward's draft_update effect is that effect's CHILD -- the
        # existing inference.invoke keeps its own admission and receipt, and
        # its deadline is clamped to the effect's (``desk_broker.child_deadline``).
        from ..kernel.project import STEWARD_EFFECT
        from . import project_kernel

        running = project_kernel.current()
        parent_operation_id = (running.operation_id
                               if running is not None and running.name == STEWARD_EFFECT and not running.replay
                               else "")
        request = InvocationRequest(
            deployment_revision=deployment_rev_id,
            definition_origin=ServiceContract.for_payload(
                "project.update.draft", "1", payload,
            ),
            deadline_at=_time.time() + 120,
            payload=payload,
            parent_operation_id=parent_operation_id,
        )

        captured: list[Any] = []

        def _capture(value: Any) -> str:
            captured.append(value)
            return f"update-draft:{assignment_id}"

        try:
            with _as_principal(principal):
                outcome = runner.invoke(
                    request, CanonicalPromptAdapter(), publish=_capture,
                )
        except Exception as exc:
            raise _ModelDraftFailed(
                f"runner_error: {exc}", FALLBACK_MODEL_UNAVAILABLE,
                detail="the call to the engine failed",
            ) from exc

        # Extract raw output -- try direct result first, then captured.
        raw: str | None = None
        result = getattr(outcome, "result", None)
        if isinstance(result, dict) and "output" in result:
            raw = str(result["output"])
        elif captured:
            adapter_result = captured[0]
            if isinstance(adapter_result, dict) and "output" in adapter_result:
                raw = str(adapter_result["output"])

        if raw is None:
            raise _ModelDraftFailed(
                "no_output", FALLBACK_NO_OUTPUT,
                detail="it returned no text",
            )

        # Parse and constrain to the claim schema.
        parsed = _parse_model_output(raw, inventory_refs, inventory_texts, known_names)
        if parsed is None:
            # P0 (betterment/projects): carry WHY up, in plain words.
            structured = _extract_structured_json(raw)
            raise _ModelDraftFailed(
                f"unparseable_output: {len(raw)} chars, starts {raw[:120]!r}",
                FALLBACK_UNPARSEABLE_OUTPUT,
                detail=(
                    "it did not return JSON" if structured is None
                    else "it did not return the expected fields"
                ),
            )

        model_sections, model_claims = parsed
        # Betterment P1: coverage is a record of what was read, never prose.
        model_sections["source_coverage"] = det_sections.get(
            "source_coverage", _HONEST_MINIMAL["source_coverage"])
        model_claims = [c for c in model_claims if c.section != "source_coverage"] + [
            c for c in det_claims if c.section == "source_coverage"]
        body_md = _assemble_body(model_sections)
        claims_json = json.dumps(
            [c.to_dict() for c in model_claims],
            sort_keys=True,
            separators=(",", ":"),
        )
        generator = f"model:{assignment_id}"
        return body_md, claims_json, generator, gen_host, gen_model

    def draft_update(
        self,
        principal: Principal,
        project_id: str,
        *,
        generator: str = "deterministic",
        strict_model_failure: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Draft a project update.

        Reads the room truth at the current revision, builds the six
        UPD-001 sections with claim entries, and persists the draft.

        If an unaccepted draft exists for this project, supersede it
        (draft_revision+1).  NEVER touches a published row.

        Args:
            principal: the acting principal.
            project_id: the project to draft for.
            generator: ``"deterministic"`` (default) or ``"model"``
                       (HS-162-03).
            strict_model_failure: when true, refuse a requested model draft
                       if the model cannot produce a valid result. The normal
                       service path keeps its deterministic fallback.
            persist: when false, return the composed draft (body, claims,
                       manifest, generator) without saving it (Betterment P1:
                       the engine pass saves only when the owner's draft
                       allows it).

        Returns:
            The persisted draft as a dict (from the updates repo).
        """
        want_model = generator == "model"

        # 1. Read the room at ONE pinned revision
        room = self._project_service.room(principal, project_id)
        revision = room.get("revision", 0)

        # 2. Scan caveats and read the linked, non-parked week.
        caveats = _scan_caveats(room) + (week := self._read_week_sources(principal, project_id, room))["caveats"]

        # 3. Read the open review's proposals (if any)
        review_id: str | None = None
        proposals: list[dict[str, Any]] = []
        review_section = room.get("review", {})
        if review_section.get("state") == "ok":
            review_id = review_section.get("open_review_id")
            if review_id:
                proposals = self._db.project_observations.list_proposals(
                    project_id,
                    review_window_key=review_id,
                )
                # Sort deterministically for stable output
                proposals.sort(key=lambda p: (
                    p.get("proposal_kind", ""),
                    p.get("title", ""),
                    p.get("id", ""),
                ))

        # 4. Read observations with evidence links
        observations = self._db.project_observations.list_observations(
            project_id, limit=500,
        )
        observation_ids = sorted([obs["id"] for obs in observations])

        # 5. Build deterministic sections + claims (always -- this is
        #    the evidence inventory the model drafter is constrained to).
        det_claims: list[Claim] = []
        items_section = room.get("items", {})

        # The EXACT source version every field mapping was read at: the
        # one pinned project revision this draft saw (C2).
        source_version = f"project:{project_id}@r{revision}"

        # Conductor K4: what closed in the reporting period (a merged PR, a
        # resolved issue) is reported under Progress, from durable records,
        # whatever the review window does. A closed proposal is not repeated
        # in Decisions.
        undecided = [p for p in proposals if p.get("change_class") != CHANGE_CLASS_CLOSED]
        progress = _build_progress(items_section, det_claims, source_version)
        closures = self._period_closures(principal, project_id, observations)
        closed_lines = _build_closed(closures, det_claims, source_version)
        if closed_lines:
            progress = "\n".join(closed_lines) if progress == _HONEST_MINIMAL["progress"] else (
                progress + "\n" + "\n".join(closed_lines)
            )
        det_sections: dict[str, str] = {
            "progress": progress,
            "decisions": _build_decisions(
                review_section, undecided, det_claims, source_version),
            "risks_blockers": _build_risks_blockers(
                items_section, det_claims, source_version),
            "dependencies": _build_dependencies(
                items_section, det_claims, source_version),
            "next_actions": _build_next_actions(
                items_section, det_claims, source_version),
            "source_coverage": _build_source_coverage(
                room, caveats, det_claims, source_version),
        }

        week["items_read"] = len(items_section.get("focus", []))
        week["project_ref"] = format_ref("project", project_id)
        det_body_md = _assemble_body(_append_week_sources(det_sections, det_claims, source_version, week))
        if not det_claims:
            # PHILO-15 B64 (Astra r2 ruling): nothing observed is one claim,
            # NOTHING TO REPORT, unreviewed by default. The update is refused
            # NOTHING VERIFIED until the owner presses Accept on it; accepted,
            # it is sent as "Nothing to report." (no filler needed).
            det_claims.append(Claim(
                span_id="s_nothing_0", text=NOTHING_TO_REPORT, refs=[], section="progress",
                kind=KIND_OBSERVATION, support=SUPPORT_UNKNOWN,
            ))
            det_body_md = NOTHING_TO_REPORT + "\n"
        det_claims_json = json.dumps(
            [c.to_dict() for c in det_claims],
            sort_keys=True,
            separators=(",", ":"),
        )

        # 6. Build source manifest (byte-identical regardless of generator).
        manifest = _build_source_manifest(
            room, review_id, observation_ids, caveats,
        )
        # What this draft reports as closed, frozen with it: once it is
        # published, the next draft does not report these again.
        manifest = {
            **manifest,
            CLOSURE_KEYS: sorted(c["key"] for c in closures),
            CLOSURE_LINES: {c["key"]: c["text"] for c in closures},
        }
        manifest_json = json.dumps({
            **manifest, "week_source_refs": week["source_refs"],
        }, sort_keys=True, separators=(",", ":"))

        # 7. Choose body + claims based on generator.
        actual_host: str | None = None
        actual_model: str | None = None
        if want_model:
            # The model draft reads the project's memory (the grounding call
            # Ask uses), less what the inventory already holds.  The refs it
            # was given are recorded on the manifest.
            memory = memory_for(
                "project.update_draft",
                self._db,
                project_id=project_id,
                query=" ".join(
                    [str((room.get("project") or {}).get("name") or "")]
                    + [claim.text for claim in det_claims]
                ),
                exclude_refs=[ref for claim in det_claims for ref in claim.refs],
                # The project's standing answers first, when memory has them
                # (MEMORY-DESIGN.md §6); none: the read is today's.
                pages=project_pages(project_id, "what-changed-this-week", "what-is-open"),
            ) if self._broker is not None else None
            try:
                body_md, claims_json, actual_generator, actual_host, actual_model = (
                    self._draft_with_model(
                        principal, det_claims, det_sections, det_body_md,
                        known_names=_known_names_for_room(room),
                        memory=memory,
                    )
                )
                # PHILO-15 B52: the model writes prose; a merged PR's row is
                # a record, carried into the model draft word for word.
                body_md, claims_json = _carry_closed_rows(
                    body_md, claims_json, closed_lines, det_claims,
                )
                if memory:
                    manifest_json = json.dumps({
                        **manifest, "week_source_refs": week["source_refs"],
                        "memory_refs": memory.refs,
                    }, sort_keys=True, separators=(",", ":"))
            except _ModelDraftFailed as exc:
                if strict_model_failure:
                    reason = model_draft_reason(exc.code)
                    _log.warning(
                        "Project update model draft failed: %s (%s): %s",
                        exc.code, exc.detail, exc.reason,
                        extra={"project_id": project_id, "failure_code": exc.code},
                    )
                    raise ServiceError(
                        "project_update_model_failed",
                        "The update engine did not make a draft.",
                        context={
                            "status": 409,
                            "reason": reason,
                            "detail": exc.detail,
                            "generator": "model",
                            "failure_code": exc.code,
                        },
                    ) from exc
                _log.warning(
                    "Project update model draft failed; retaining deterministic fallback",
                    extra={"project_id": project_id, "failure_code": exc.code},
                )
                body_md = det_body_md
                claims_json = det_claims_json
                actual_generator = FALLBACK_GENERATOR_PREFIX + exc.code
                actual_host = actual_model = None
        else:
            body_md = det_body_md
            claims_json = det_claims_json
            actual_generator = "deterministic"

        composed = {
            "body_md": body_md, "claims_json": claims_json,
            "source_manifest_json": manifest_json, "generator": actual_generator,
            "generator_host": actual_host, "generator_model": actual_model,
            "project_revision": revision, "review_id": review_id,
        }
        if not persist:
            return composed
        return self._persist_draft(project_id, composed)

    def _persist_draft(self, project_id: str, composed: dict[str, Any]) -> dict[str, Any]:
        """Save a composed draft: supersede the newest draft, or insert one."""
        body_md = composed["body_md"]
        claims_json = composed["claims_json"]
        manifest_json = composed["source_manifest_json"]
        actual_generator = composed["generator"]
        actual_host = composed.get("generator_host")
        actual_model = composed.get("generator_model")
        revision = composed.get("project_revision") or 0
        review_id = composed.get("review_id")
        # 8. Persist: check for existing unaccepted draft to supersede
        existing_drafts = self._db.project_updates.list_updates(
            project_id, lifecycle="draft",
        )

        if existing_drafts:
            # Supersede the latest unaccepted draft (UPD-004)
            old_draft = existing_drafts[0]  # list is ordered by draft_revision DESC
            new_id = generate_pupd_id()
            try:
                new_row = self._db.project_updates.supersede_draft(
                    old_draft["id"],
                    new_update_id=new_id,
                    body_md=body_md,
                    claims_json=claims_json,
                    source_manifest_json=manifest_json,
                    generator=actual_generator,
                    generator_host=actual_host,
                    generator_model=actual_model,
                )
                return self._project_axes(new_row)
            except PublishedUpdateError:
                # The "draft" was actually published (race).  Fall through
                # to create a fresh draft.
                _log.warning(
                    "Draft %s was published between list and supersede; "
                    "creating a new draft instead.",
                    old_draft["id"],
                )

        # No existing draft (or race recovery): create a new one
        new_id = generate_pupd_id()
        self._db.project_updates.insert_update(
            update_id=new_id,
            project_id=project_id,
            project_revision=revision,
            review_id=review_id,
            draft_revision=1,
            body_md=body_md,
            claims_json=claims_json,
            source_manifest_json=manifest_json,
            generator=actual_generator,
            generator_host=actual_host,
            generator_model=actual_model,
        )
        return self._project_axes(self._db.project_updates.get_update(new_id))

    def write_agent_update(
        self,
        principal: Principal,
        project_id: str,
        *,
        body_md: str,
        source_refs: Iterable[str] = (),
        generator: str = "agent",
    ) -> dict[str, Any]:
        """Persist plain text returned by an update automation.

        The automation runner has already admitted the engine call.  This
        method only records its text in ``project_updates`` and keeps the
        exact refs the run looked at in the source manifest.  A tool-capable
        agent may also save through ``project.update_draft``; the runner's
        final write is idempotent at the ledger level because an older draft
        is superseded by the new revision.
        """
        text = str(body_md or "").strip()
        if not text:
            raise ValidationError("The update engine returned no text.", code="update_empty")
        room = self._project_service.room(principal, project_id)
        refs = list(dict.fromkeys(str(ref).strip() for ref in source_refs if str(ref).strip()))
        claims: list[Claim] = []
        # Agent text is intentionally plain.  Keep one conservative claim per
        # non-empty line so the existing claim/read projection can still show
        # source-linked support without inventing a JSON response contract.
        for ordinal, line in enumerate(text.splitlines()):
            sentence = line.strip()
            if not sentence:
                continue
            claims.append(Claim(
                span_id=f"s_agent_{ordinal}", text=sentence, refs=list(refs),
                section="progress", kind=KIND_OBSERVATION,
                support=SUPPORT_SOURCE_LINKED if refs else SUPPORT_UNKNOWN,
            ))
        composed = {
            "body_md": text + ("\n" if not text.endswith("\n") else ""),
            "claims_json": json.dumps([claim.to_dict() for claim in claims],
                                       sort_keys=True, separators=(",", ":")),
            "source_manifest_json": json.dumps({
                "project_revision": room.get("revision", 0),
                "agent_sources": refs,
            }, sort_keys=True, separators=(",", ":")),
            "generator": str(generator or "agent"),
            "generator_host": None,
            "generator_model": None,
            "project_revision": room.get("revision", 0),
            "review_id": None,
        }
        return self._persist_draft(project_id, composed)

    # ── Betterment P1: the engine pass behind Write update ──────────────
    #
    # Write update saves the records draft at once (``draft_update``), then
    # the face starts this pass. It composes the engine's draft on a daemon
    # thread, off the hub's request loop, and keeps the result on its job
    # row. The result becomes a new draft revision only through
    # ``apply_engine_pass``: at once when the owner has not touched the draft,
    # or on his press ("Use it") when he has. It never overwrites his words.

    def start_engine_pass(
        self, principal: Principal, update_id: str, *, background: bool = True,
        automation_id: str | None = None,
    ) -> dict[str, Any]:
        base = self._db.project_updates.get_update(update_id)
        if base is None:
            raise NotFound("update", update_id)
        if base.get("lifecycle") != "draft":
            raise ConflictError(
                "Only a draft can be improved.", code="engine_pass_not_draft",
                context={"status": 409},
            )
        project_id = str(base["project_id"])
        if automation_id:
            automation = self._db.workbenches.get(str(automation_id))
            expected_target = f"project_updates:{project_id}"
            if automation is None or str(automation.output_target or "") != expected_target:
                raise ValidationError(
                    "The project update automation is missing.",
                    code="project_update_automation_missing",
                )
        job_id = "pujob_" + uuid.uuid4().hex[:24]
        with self._db._connection() as conn:
            conn.execute(
                """INSERT INTO project_update_jobs
                   (id, project_id, base_update_id, base_body_sha, state, started_at)
                   VALUES (?, ?, ?, ?, 'running', ?)""",
                (job_id, project_id, update_id, _body_sha(base.get("body_md")), utc_now_iso()),
            )
        if background:
            threading.Thread(
                target=(self._run_automation_pass if automation_id else self._run_engine_pass),
                args=((principal, job_id, project_id, str(automation_id))
                      if automation_id else (principal, job_id, project_id)),
                name=f"update-{'automation' if automation_id else 'engine'}-pass-{job_id}", daemon=True,
            ).start()
        else:
            if automation_id:
                self._run_automation_pass(principal, job_id, project_id, str(automation_id))
            else:
                self._run_engine_pass(principal, job_id, project_id)
        return self.get_engine_pass(job_id)

    def _run_automation_pass(
        self, principal: Principal, job_id: str, project_id: str, automation_id: str,
    ) -> None:
        """Run the project's Workbench and retain its delivered update row.

        The P1 job is only the existing face-facing wait state.  The producer
        is the real Workbench runner, whose delivery writes the one
        ``project_updates`` row and carries the run's looked-at refs.
        """
        state, reason, detail, result = "succeeded", None, None, None
        try:
            from .workbench_service import WorkbenchService

            run = asyncio.run(WorkbenchService(self._db).run(
                principal, automation_id, memory_enabled=False,
            ))
            deliveries = run.get("deliveries", []) if isinstance(run, dict) else []
            written = next(
                (delivery for delivery in deliveries
                 if str(delivery.get("project_id") or "") == project_id
                 and str(delivery.get("outcome") or "") == "written"),
                None,
            )
            update_id = str((written or {}).get("update_id") or "")
            update = self._db.project_updates.get_update(update_id) if update_id else None
            if update is None:
                raise ServiceError(
                    "project_update_delivery_failed",
                    "The update automation did not write an update.",
                    context={"status": 409, "reason": "did_not_answer"},
                )
            result = self._project_axes(update)
            result["automation_run_id"] = str(run.get("run_id") or "")
            result["automation_id"] = automation_id
        except ServiceError as exc:
            state = "failed"
            reason = str(exc.context.get("reason") or "did_not_answer")
            detail = exc.context.get("detail") or exc.detail
        except Exception:
            _log.warning("project update automation failed", exc_info=True,
                         extra={"project_id": project_id, "job_id": job_id,
                                "automation_id": automation_id})
            state, reason = "failed", "did_not_answer"
        with self._db._connection() as conn:
            conn.execute(
                """UPDATE project_update_jobs
                   SET state = ?, reason = ?, detail = ?, result_json = ?, finished_at = ?
                   WHERE id = ? AND state = 'running'""",
                (state, reason, detail, json.dumps(result) if result else None,
                 utc_now_iso(), job_id),
            )

    def _run_engine_pass(self, principal: Principal, job_id: str, project_id: str) -> None:
        state, reason, detail, result = "succeeded", None, None, None
        try:
            result = self.draft_update(
                principal, project_id, generator="model",
                strict_model_failure=True, persist=False,
            )
        except ServiceError as exc:
            state = "failed"
            reason = str(exc.context.get("reason") or "did_not_answer")
            detail = exc.context.get("detail")
        except Exception:
            _log.warning("update engine pass failed", exc_info=True,
                         extra={"project_id": project_id, "job_id": job_id})
            state, reason = "failed", "did_not_answer"
        with self._db._connection() as conn:
            # A stopped pass keeps its state: its late answer is dropped.
            conn.execute(
                """UPDATE project_update_jobs
                   SET state = ?, reason = ?, detail = ?, result_json = ?, finished_at = ?
                   WHERE id = ? AND state = 'running'""",
                (state, reason, detail, json.dumps(result) if result else None,
                 utc_now_iso(), job_id),
            )

    def recover_engine_passes(self) -> int:
        """At hub start: a pass left ``running`` lost its thread with the old
        process. It is marked failed with a reason in words, so the face
        offers Try again instead of polling forever. Returns the count."""
        with self._db._connection() as conn:
            cur = conn.execute(
                """UPDATE project_update_jobs
                   SET state = 'failed', reason = 'did_not_answer',
                       detail = 'the hub restarted', finished_at = ?
                   WHERE state = 'running'""",
                (utc_now_iso(),),
            )
            return int(cur.rowcount or 0)

    def _job_row(self, job_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_update_jobs WHERE id = ?", (str(job_id),),
            ).fetchone()
        if row is None:
            raise NotFound("update_job", job_id)
        return dict(row)

    def get_engine_pass(self, job_id: str) -> dict[str, Any]:
        """The job as the face reads it (the result's text, never its rows)."""
        row = self._job_row(job_id)
        result = json.loads(row["result_json"]) if row.get("result_json") else None
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "base_update_id": row["base_update_id"],
            "state": row["state"],
            "reason": row.get("reason"),
            "detail": row.get("detail"),
            "started_at": row["started_at"],
            "finished_at": row.get("finished_at"),
            "applied_update_id": row.get("applied_update_id"),
            "body_md": (result or {}).get("body_md"),
            "generator_model": (result or {}).get("generator_model"),
            "generator_host": (result or {}).get("generator_host"),
        }

    def stop_engine_pass(self, principal: Principal, job_id: str) -> dict[str, Any]:
        self._job_row(job_id)
        with self._db._connection() as conn:
            conn.execute(
                """UPDATE project_update_jobs SET state = 'stopped', reason = 'stopped',
                   finished_at = ? WHERE id = ? AND state = 'running'""",
                (utc_now_iso(), job_id),
            )
        return self.get_engine_pass(job_id)

    def apply_engine_pass(
        self, principal: Principal, job_id: str, *, force: bool = False,
    ) -> dict[str, Any]:
        """Save the engine's draft as the next revision.

        Without ``force`` it refuses (``draft_changed``) when the draft the
        pass started from is no longer the newest draft or its words changed:
        the owner edited, so the face offers "Use it" instead.
        """
        row = self._job_row(job_id)
        if row["state"] == "applied" and row.get("applied_update_id"):
            return self._project_axes(self._db.project_updates.get_update(row["applied_update_id"]))
        if row["state"] != "succeeded" or not row.get("result_json"):
            raise ConflictError(
                "The engine draft is not ready.", code="engine_pass_not_ready",
                context={"status": 409},
            )
        drafts = self._db.project_updates.list_updates(row["project_id"], lifecycle="draft")
        latest = drafts[0] if drafts else None
        if latest is None:
            raise ConflictError(
                "The draft was published.", code="draft_changed", context={"status": 409},
            )
        changed = (
            latest["id"] != row["base_update_id"]
            or _body_sha(latest.get("body_md")) != row["base_body_sha"]
        )
        result = json.loads(row["result_json"])
        automation_update_id = str(result.get("id") or "") if result.get("automation_id") else ""
        if changed and not force and not automation_update_id:
            raise ConflictError(
                "The draft changed since the engine started.", code="draft_changed",
                context={"status": 409},
            )
        if automation_update_id:
            automation_update = self._db.project_updates.get_update(automation_update_id)
            if automation_update is None:
                raise ConflictError(
                    "The automation update is no longer available.",
                    code="draft_changed", context={"status": 409},
                )
            # The automation already owns this revision.  An unchanged base
            # draft or the delivered row is safe to adopt; an owner's edit
            # still requires the explicit Use it press.
            base = self._db.project_updates.get_update(row["base_update_id"])
            owner_edited = (
                base is None
                or _body_sha(base.get("body_md")) != row["base_body_sha"]
            )
            other_draft = latest["id"] not in {row["base_update_id"], automation_update_id}
            if (owner_edited or other_draft) and not force:
                raise ConflictError(
                    "The draft changed since the engine started.",
                    code="draft_changed", context={"status": 409},
                )
            saved = self._project_axes(automation_update)
        else:
            saved = self._persist_draft(row["project_id"], result)
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE project_update_jobs SET state = 'applied', applied_update_id = ? WHERE id = ?",
                (saved["id"], job_id),
            )
        return saved

    def _period_closures(
        self, principal: Principal, project_id: str, observations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """:func:`period_closures` over this Project's durable records, less
        what its published updates already reported."""
        reported = reported_closures(self._db.project_updates.list_updates(
            project_id, lifecycle="published", limit=100_000,
        ))
        try:
            tasks = {
                str(a["id"]): str(a.get("task") or "")
                for a in self._project_service.list_action_items(principal, project_id)
            }
        except Exception:
            tasks = {}
        completions = (
            ServiceEventLedger(self._db).list(principal, event_type="commitment.completed", limit=500)
            if tasks else []
        )
        return period_closures(observations, completions, tasks, reported)

    # ── Route-facing verbs (HS-162-04) ─────────────────────────────

    def list_updates(
        self,
        principal: Principal,
        project_id: str,
        *,
        lifecycle: str | None = None,
    ) -> list[dict[str, Any]]:
        """List updates for a project, optionally filtered by lifecycle."""
        self._project_service._require_project(project_id)
        rows = self._db.project_updates.list_updates(
            project_id, lifecycle=lifecycle,
        )
        return attach_deliveries(self._db, [self._project_axes(r) for r in rows])

    def get_update(
        self,
        principal: Principal,
        update_id: str,
    ) -> dict[str, Any]:
        """Fetch a single update by ID.

        Raises NotFound when no row matches.
        """
        row = self._db.project_updates.get_update(update_id)
        if row is None:
            raise NotFound("update", update_id)
        return attach_deliveries(self._db, [self._project_axes(row)])[0]

    def draft_update_command(
        self,
        principal: Principal,
        project_id: str,
        *,
        generator: str = "deterministic",
        command_id: str | None = None,
        strict_model_failure: bool = False,
    ) -> dict[str, Any]:
        """Draft an update with optional command_id replay guard.

        Wraps draft_update with idempotency: if the same command_id
        was already used, the stored result is replayed.

        The result dict includes ``generator`` and ``fallback_reason``
        (non-None only when model was requested but fell back).
        """
        req_hash = _request_hash({
            "project_id": project_id,
            "generator": generator,
            "strict_model_failure": bool(strict_model_failure),
        })
        if command_id is not None:
            existing = self._claim_draft_command(command_id, project_id, req_hash)
            if existing is not None:
                return existing

        try:
            result = self.draft_update(
                principal,
                project_id,
                generator=generator,
                strict_model_failure=strict_model_failure,
            )
        except BaseException as exc:
            if command_id is not None:
                # The claim is released: the same command_id may try again.
                # The record keeps the reason (P0): not_usable, no_engine ...
                context = getattr(exc, "context", None) or {}
                self._db.projects.complete_project_command(
                    command_id, status="failed",
                    error_code=str(context.get("reason") or "draft_failed"),
                )
            raise

        # Surface fallback reason when the model path was requested
        actual_gen = result.get("generator", "deterministic")
        if generator == "model" and actual_gen == "deterministic":
            result["fallback_reason"] = "model_unavailable"

        # Record command for idempotency
        if command_id is not None:
            cmd_id = command_id
        else:
            cmd_id = generate_pcmd_id()
        project_ref = format_ref("project", project_id)
        envelope = CommandResultEnvelope(
            result_kind=ResultKind.CREATED,
            project_id=project_id,
            project_revision=result.get("project_revision", 0),
            changed_refs=(parse_ref(project_ref),),
        )
        self._record_command(
            cmd_id, project_id, "draft_update", req_hash, envelope,
        )

        return result

    def _claim_draft_command(
        self, command_id: str, project_id: str, req_hash: str,
    ) -> dict[str, Any] | None:
        """Claim *command_id* for one draft, atomically (Astra on #867).

        The check and the claim are one ``BEGIN IMMEDIATE`` transaction, so two
        concurrent calls with one command_id make one draft: the first claims
        (a ``pending`` row), the second replays a completed result or is
        refused ``command_in_progress``. A ``failed`` claim may be taken again.
        Returns the stored result to replay, or None when this call holds the
        claim.
        """
        if self._db.projects.get_project(project_id) is None:
            raise NotFound("project", project_id)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT status, request_hash, result_json FROM project_commands WHERE id = ?",
                (command_id,),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO project_commands (id, project_id, command_kind, request_hash, "
                    "status, created_at) VALUES (?, ?, 'draft_update', ?, 'pending', ?)",
                    (command_id, project_id, req_hash, utc_now_iso()),
                )
                return None
            if row["request_hash"] != req_hash:
                raise ConflictError(
                    "idempotency conflict: same command_id with different request hash",
                    code="idempotency_conflict",
                )
            if row["status"] == "completed":
                if row["result_json"]:
                    return json.loads(row["result_json"])
                return {"result_kind": "no_change", "project_id": project_id}
            if row["status"] == "pending":
                raise ConflictError(
                    "this command_id is already drafting; ask again when it ends",
                    code="command_in_progress",
                )
            conn.execute(
                "UPDATE project_commands SET status = 'pending', error_code = NULL WHERE id = ?",
                (command_id,),
            )
            return None

    def save_update(
        self,
        principal: Principal,
        update_id: str,
        *,
        body_md: str | None = None,
        source_refs: Iterable[str] = (),
        generator: str | None = None,
        engine: str | None = None,
        command_id: str | None = None,
    ) -> dict[str, Any]:
        """Save the owner's edit of a draft.

        Stores body_md.  HS-200-06 (C2): editing a SUPPORTED sentence
        INVALIDATES its support -- the claim drops to source-linked (or
        unknown when it carries no ref) and its support record is KEPT,
        stamped with ``invalidated_at`` and a reason.  Provenance is
        never deleted; ``verified`` is never rewritten.
        The updated_at timestamp advancing past created_at is the
        implicit "edited" marker (no schema change needed).

        Raises PublishedUpdateError if the row is published.
        Raises NotFound if the update does not exist.
        """
        normalized_source_refs = list(source_refs or ())
        req_hash = _request_hash({
            "update_id": update_id,
            "body_md": body_md,
            "source_refs": normalized_source_refs,
            "generator": generator,
            "engine": engine,
        })
        if command_id is not None:
            existing = self._db.projects.get_project_command(command_id)
            if existing is not None:
                if (existing["status"] == "completed"
                        and existing["request_hash"] == req_hash):
                    if existing["result_json"]:
                        return json.loads(existing["result_json"])
                    return {"result_kind": "no_change", "update_id": update_id}
                if existing["request_hash"] != req_hash:
                    raise ConflictError(
                        "idempotency conflict: same command_id with different request hash",
                        code="idempotency_conflict",
                    )

        row = self._db.project_updates.get_update(update_id)
        if row is None:
            raise NotFound("update", update_id)

        project_id = row["project_id"]

        # A tool-capable project update agent writes plain text through this
        # same producer.  Keep the update id made by Write update, carry the
        # refs the run looked at, and replace the deterministic generator
        # metadata.  This path deliberately skips the owner's edit-support
        # invalidation: the agent's lines are newly grounded below.
        if principal.kind is PrincipalKind.AGENT:
            text = str(body_md or "").strip()
            if not text:
                raise ValidationError("The update engine returned no text.", code="update_empty")
            refs = list(dict.fromkeys(
                str(ref).strip() for ref in normalized_source_refs if str(ref).strip()
            ))
            if not refs:
                # A CLI agent may omit the optional manifest argument. Its
                # preceding MCP reads are already durable under the run id;
                # use those exact refs before the write is recorded.
                try:
                    from . import run_trace
                    run_id = run_trace.run_id_of(principal.identity)
                    seen = run_trace.use_by_trace(self._db, [run_id]).get(run_id, {})
                    refs = list(dict.fromkeys(
                        str(entry.get("ref") or "").strip()
                        for entry in seen.get("looked_at", [])
                        if str(entry.get("ref") or "").strip()
                    ))
                except Exception:
                    refs = []
            claims = [
                Claim(
                    span_id=f"s_agent_{ordinal}", text=line.strip(), refs=list(refs),
                    section="progress", kind=KIND_OBSERVATION,
                    support=SUPPORT_SOURCE_LINKED if refs else SUPPORT_UNKNOWN,
                ).to_dict()
                for ordinal, line in enumerate(text.splitlines()) if line.strip()
            ]
            try:
                manifest = json.loads(row.get("source_manifest_json") or "{}")
            except (TypeError, ValueError):
                manifest = {}
            if not isinstance(manifest, dict):
                manifest = {}
            manifest["agent_sources"] = refs
            self._db.project_updates.update_draft(
                update_id,
                body_md=text + ("\n" if not text.endswith("\n") else ""),
                claims_json=json.dumps(claims, sort_keys=True, separators=(",", ":")),
                source_manifest_json=json.dumps(manifest, sort_keys=True, separators=(",", ":")),
                generator=str(generator or f"agent:{principal.identity}"),
                generator_model=str(engine or "") or None,
            )
            result = self._project_axes(self._db.project_updates.get_update(update_id))
            cmd_id = command_id or generate_pcmd_id()
            project_ref = format_ref("project", project_id)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=result.get("project_revision", 0),
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(cmd_id, project_id, "save_update", req_hash, envelope)
            return result

        # C2: a supported sentence that no longer appears in the body
        # loses its support; the record stays with its provenance.
        next_claims: str | None = None
        if body_md is not None:
            next_claims = _invalidate_edited_support(
                migrate_claims_json(
                    row.get("claims_json") or "",
                    generator=str(row.get("generator") or "deterministic"),
                ),
                body_md,
            )

        # PHILO-15 B64 (Astra r1 P1-3): the owner's own saved words are
        # reviewed, for those exact words; every earlier claim is kept.
        if body_md is not None and principal.kind is PrincipalKind.OWNER:
            authored = _owner_authored_claims(
                next_claims if next_claims is not None else migrate_claims_json(
                    row.get("claims_json") or "",
                    generator=str(row.get("generator") or "deterministic"),
                ),
                body_md, principal,
            )
            if authored is not None:
                next_claims = authored

        # PublishedUpdateError is raised inside the repo
        self._db.project_updates.update_draft(
            update_id, body_md=body_md, claims_json=next_claims,
        )

        result = self._project_axes(
            self._db.project_updates.get_update(update_id)
        )

        # Record command for idempotency
        cmd_id = command_id or generate_pcmd_id()
        project_ref = format_ref("project", project_id)
        envelope = CommandResultEnvelope(
            result_kind=ResultKind.UPDATED,
            project_id=project_id,
            project_revision=result.get("project_revision", 0),
            changed_refs=(parse_ref(project_ref),),
        )
        self._record_command(
            cmd_id, project_id, "save_update", req_hash, envelope,
        )

        return result

    def regenerate_update(
        self,
        principal: Principal,
        update_id: str,
        *,
        generator: str = "deterministic",
        command_id: str | None = None,
    ) -> dict[str, Any]:
        """Regenerate: supersede an unaccepted draft or create a NEW
        draft when the latest is published.

        Both lifecycle branches delegate to draft_update which handles
        superseding (for drafts) or fresh creation (after published).
        """
        req_hash = _request_hash({
            "update_id": update_id,
            "generator": generator,
        })
        if command_id is not None:
            existing = self._db.projects.get_project_command(command_id)
            if existing is not None:
                if (existing["status"] == "completed"
                        and existing["request_hash"] == req_hash):
                    if existing["result_json"]:
                        return json.loads(existing["result_json"])
                    return {"result_kind": "no_change", "update_id": update_id}
                if existing["request_hash"] != req_hash:
                    raise ConflictError(
                        "idempotency conflict: same command_id with different request hash",
                        code="idempotency_conflict",
                    )

        row = self._db.project_updates.get_update(update_id)
        if row is None:
            raise NotFound("update", update_id)

        project_id = row["project_id"]

        # Both published and draft delegate to draft_update which
        # handles superseding (for drafts) or fresh creation.
        result = self.draft_update(
            principal, project_id, generator=generator,
        )

        # Record command for idempotency
        cmd_id = command_id or generate_pcmd_id()
        project_ref = format_ref("project", project_id)
        envelope = CommandResultEnvelope(
            result_kind=ResultKind.CREATED,
            project_id=project_id,
            project_revision=result.get("project_revision", 0),
            changed_refs=(parse_ref(project_ref),),
        )
        self._record_command(
            cmd_id, project_id, "regenerate_update", req_hash, envelope,
        )

        return result

    def mark_update_delivered(
        self,
        principal: Principal,
        update_id: str,
        delivered_to: str | None = None,
        command_id: str | None = None,
    ) -> dict[str, Any]:
        """Mark it delivered (the Q0 ruling; PHILO-9-02, R4-2): one row per confirmation.

        Admitted only: the delivery row, the operation's terminal state and
        its receipt commit in ONE transaction (``journal_atomic``, through the
        operation's handle), so no row exists without its receipt and no
        receipt without its row. ``operation_id`` comes from the execution
        context, ``project_id`` from the stored update, ``delivered_at`` is
        the confirmation time (the admission of this operation, the same on a
        retry). A replay of the same key answers the original row by its
        operation. A draft or superseded update: ``update_not_published``.
        """
        from holdspeak.db.updates import UpdateNotPublishedError
        from holdspeak.services import project_kernel

        handle = project_kernel.current()
        if handle is None:
            # A replay of a SUCCEEDED mark (the kernel answers from its record).
            raise RuntimeError("project.mark_update_delivered runs only as an admitted operation")
        operation = handle.operation()
        existing = self._delivery_for(handle.operation_id)
        if existing is not None:
            return {"success": True, "delivery": existing}
        row = self._db.project_updates.get_update(update_id)
        if row is None:
            raise NotFound("update", update_id)
        if str(row.get("lifecycle") or "") != "published":
            raise ValidationError(
                f"Update {update_id} is {row.get('lifecycle')}; only a published update can be marked delivered",
                code="update_not_published",
            )
        confirmed_at = datetime.fromtimestamp(float(operation.get("created_at") or 0), tz=timezone.utc)
        written: dict[str, Any] = {}

        def effect(conn: Any) -> None:
            try:
                written.update(self._db.project_update_deliveries.insert_delivery_in_transaction(
                    conn, update_id=update_id, operation_id=handle.operation_id, delivered_to=delivered_to,
                    delivered_at=confirmed_at.isoformat(timespec="seconds"),
                    delivery_id="pdel_" + hashlib.sha256(handle.operation_id.encode()).hexdigest()[:16],
                ))
            except UpdateNotPublishedError as exc:
                raise ValidationError(str(exc), code="update_not_published") from exc

        handle.terminal("succeeded", "succeeded", f"project_update:{update_id}", effect=effect)
        return {"success": True, "delivery": written}

    def _delivery_for(self, operation_id: str) -> dict[str, Any] | None:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT id, update_id, project_id, delivered_at, delivered_to, operation_id "
                "FROM project_update_deliveries WHERE operation_id=?", (operation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def delivery_by_operation(self, operation_id: str) -> dict[str, Any]:
        """The replay answer: the original delivery, found by its operation."""
        existing = self._delivery_for(operation_id)
        if existing is None:
            raise NotFound("delivery", operation_id)
        return {"success": True, "delivery": existing}

    def _project_update_meeting_ids(
        self, principal: Principal, project_id: str,
    ) -> tuple[set[str], set[str]]:
        """Return linked meeting ids split by the existing P2 rule.

        The project ref is a broad container for ordinary grounding callers.
        An update automation has a narrower contract: it uses the same
        meeting-kind classifier as the records drafter, before any source
        text is hydrated. The second set is the eligible ids; keeping this
        decision here lets the Workbench and tool response paths share P2.
        """
        excluded: set[str] = set()
        eligible: set[str] = set()
        people_names: list[str] = []
        if self._people_names is not None:
            try:
                people_names = [str(name) for name in self._people_names(principal) if str(name).strip()]
            except Exception:
                _log.debug("update grounding: People names not read; title rule only", exc_info=True)
        if self._people_names is None:
            # The Workbench delivery path is composed from its database only.
            # Reuse the same People-name read used by the Room when that
            # composition does not inject the web server's callback.
            try:
                from .needs_you_membership import _read_people_names

                people_names = [str(name) for name in (_read_people_names(principal) or ()) if str(name).strip()]
            except Exception:
                people_names = []

        try:
            offset = 0
            while True:
                page = self._project_service.list_meetings(
                    principal, project_id, limit=500, offset=offset,
                )
                if not page:
                    break
                for row in page:
                    meeting_id = str(row.get("id") or "").strip()
                    if not meeting_id:
                        continue
                    title = str(row.get("title") or "")
                    private = title_says_one_on_one(title)
                    try:
                        meeting = self._db.meetings.get_meeting(meeting_id)
                    except Exception:
                        meeting = None
                    if meeting is not None:
                        title = str(getattr(meeting, "title", None) or title)
                        private = private or is_one_on_one(
                            title, meeting_speakers(meeting), people_names,
                        )
                    (excluded if private else eligible).add(meeting_id)
                if len(page) < 500:
                    break
                offset += len(page)
        except Exception:
            # A missing meeting projection must not turn into broad project
            # hydration. The caller still has any explicit safe refs.
            _log.debug("update grounding: linked meetings not read", exc_info=True)

        return excluded, eligible

    def project_update_excluded_refs(
        self, principal: Principal, project_id: str,
    ) -> set[str]:
        """Return canonical refs P2 withholds from an update automation.

        This is deliberately a predicate over the existing project source
        records. It does not change generic project grounding or unlink a
        source. A private meeting's descendants are withheld unless the
        owner explicitly filed that descendant as a project resource; that
        hand-filed edge is an intentional P2 exception for owed work and
        owner-added project material.
        """
        excluded_meetings, _eligible_meetings = self._project_update_meeting_ids(
            principal, project_id,
        )
        excluded = {f"meeting:{meeting_id}" for meeting_id in excluded_meetings}
        excluded.update(f"transcript:{meeting_id}" for meeting_id in excluded_meetings)
        try:
            project_resources = self._project_service.list_resources(principal, project_id)
        except Exception:
            project_resources = []
        explicit_refs = {
            str(resource.get("resource_ref") or "").strip().casefold()
            for resource in project_resources
            if str(resource.get("resource_ref") or "").strip()
        }
        try:
            for action in self._project_service.list_action_items(principal, project_id):
                if str(action.get("meeting_id") or "") in excluded_meetings:
                    action_id = str(action.get("id") or "").strip()
                    if action_id and not (
                        f"action:{action_id}".casefold() in explicit_refs
                        or f"action_item:{action_id}".casefold() in explicit_refs
                    ):
                        excluded.update({f"action:{action_id}", f"action_item:{action_id}"})
            for artifact in self._project_service.list_artifacts(principal, project_id):
                if str(artifact.get("meeting_id") or "") in excluded_meetings:
                    artifact_id = str(artifact.get("id") or "").strip()
                    if artifact_id and f"artifact:{artifact_id}".casefold() not in explicit_refs:
                        excluded.add(f"artifact:{artifact_id}")
            for record_id in self._records_from_meetings(excluded_meetings):
                if not (
                    f"decision:{record_id}".casefold() in explicit_refs
                    or f"decision_record:{record_id}".casefold() in explicit_refs
                    or f"desk_decision:{record_id}".casefold() in explicit_refs
                ):
                    excluded.update({f"decision:{record_id}", f"decision_record:{record_id}"})
        except Exception:
            _log.debug("update grounding: meeting descendants not read", exc_info=True)

        # People notes live in their own encrypted store. A regular note can
        # still be linked to a project by hand; only explicit People/1:1
        # markers are withheld here, preserving ordinary project notes.
        for resource in project_resources:
            raw = str(resource.get("resource_ref") or "").strip()
            kind, _, resource_id = raw.partition(":")
            kind = kind.casefold()
            resource_id = resource_id.split("#", 1)[0].strip()
            if not kind or not resource_id:
                continue
            if kind in {
                "people", "person", "people_note", "grounding_note", "relationship",
                "one_on_one", "one-on-one",
            }:
                excluded.add(f"{kind}:{resource_id}")
                continue
            if kind not in {"note", "notes"}:
                continue
            note = self._db.notes.get(resource_id)
            tags = {str(tag).strip().casefold() for tag in (getattr(note, "tags", None) or [])}
            title = str(getattr(note, "title", "") or "") if note is not None else ""
            people_note = (
                title_says_one_on_one(title)
                or any(
                    tag in {"people", "people_note", "people-note", "person", "1:1", "one-on-one"}
                    or tag.startswith(("people:", "person:"))
                    for tag in tags
                )
            )
            if people_note:
                excluded.update({f"note:{resource_id}", f"notes:{resource_id}"})
        return excluded

    def project_update_grounding_refs(
        self, principal: Principal, project_id: str,
    ) -> list[str]:
        """Expand one project ref to P2-eligible refs for an update run."""
        excluded = {ref.casefold() for ref in self.project_update_excluded_refs(principal, project_id)}
        _excluded_meetings, eligible_meetings = self._project_update_meeting_ids(
            principal, project_id,
        )
        refs = [f"meeting:{meeting_id}" for meeting_id in eligible_meetings]
        try:
            resources = self._project_service.list_resources(principal, project_id)
        except Exception:
            resources = []
        for resource in resources:
            ref = str(resource.get("resource_ref") or "").strip().split("#", 1)[0]
            if not ref or ref.casefold().startswith("project:"):
                continue
            if ref.casefold() not in excluded:
                refs.append(ref)
        return sorted(set(refs))

    def _read_week_sources(
        self,
        principal: Principal,
        project_id: str,
        room: dict[str, Any],
    ) -> dict[str, Any]:
        """Read the persisted, non-parked sources linked to a project.

        Betterment P2 (decision 18): a 1:1 meeting's summary, actions and
        decisions stay out of the update; it is named in ``left_out``.
        """
        meeting_summaries: list[dict[str, Any]] = []
        linked_actions: list[dict[str, Any]] = []
        linked_decisions: list[dict[str, Any]] = []
        caveats: list[dict[str, str]] = []
        source_refs: list[str] = []
        left_out: list[dict[str, str]] = []
        one_on_one_ids: set[str] = set()
        risks: list[dict[str, str]] = []
        notes_read = 0
        people_names: list[str] = []
        try:
            project_resources = self._project_service.list_resources(principal, project_id)
        except Exception:
            project_resources = []
        explicit_refs = {
            str(resource.get("resource_ref") or "").strip().casefold()
            for resource in project_resources
            if str(resource.get("resource_ref") or "").strip()
        }

        def explicitly_filed(kind: str, item_id: str) -> bool:
            return f"{kind}:{item_id}".casefold() in explicit_refs

        if self._people_names is not None:
            try:
                people_names = [str(n) for n in self._people_names(principal) if str(n).strip()]
            except Exception:
                _log.debug("update draft: People names not read; title rule only", exc_info=True)

        meetings: list[dict[str, Any]] = []
        try:
            # Read every active linked page.  A single bounded page would
            # make the success line dishonest for projects with >500 meetings.
            offset = 0
            while True:
                page = self._project_service.list_meetings(
                    principal, project_id, limit=500, offset=offset,
                )
                meetings.extend(page)
                if len(page) < 500:
                    break
                offset += len(page)
        except Exception:
            caveats.append({
                "section": "meetings",
                "state": "degraded",
                "reason": "meetings_read_failed",
            })

        for meeting_row in sorted(
            meetings,
            key=lambda row: (
                str(row.get("started_at") or ""),
                str(row.get("id") or ""),
            ),
            reverse=True,
        ):
            meeting_id = str(meeting_row.get("id") or "").strip()
            if not meeting_id:
                caveats.append({
                    "section": "meetings",
                    "state": "degraded",
                    "reason": "meeting_id_missing",
                })
                continue
            row_title = str(meeting_row.get("title") or "")
            if title_says_one_on_one(row_title):
                one_on_one_ids.add(meeting_id)
                left_out.append({"id": meeting_id, "title": row_title})
                continue
            try:
                meeting = self._db.meetings.get_meeting(meeting_id)
                if meeting is None:
                    caveats.append({
                        "section": "meetings",
                        "state": "degraded",
                        "reason": "meeting_unavailable",
                    })
                    continue
                title = str(meeting.title or row_title or "Meeting")
                if is_one_on_one(title, meeting_speakers(meeting), people_names):
                    one_on_one_ids.add(meeting_id)
                    left_out.append({"id": meeting_id, "title": title})
                    continue
                intel = meeting.intel
                summary = " ".join(
                    str(getattr(intel, "summary", "") or "").split()
                )
                if not summary:
                    caveats.append({
                        "section": "meetings",
                        "state": "degraded",
                        "reason": "meeting_summary_unavailable",
                    })
                    continue
                meeting_ref = format_ref("meeting", meeting_id)
                meeting_summaries.append({
                    "id": meeting_id,
                    "title": str(
                        meeting.title or meeting_row.get("title") or "Meeting"
                    ),
                    "summary": summary,
                })
                source_refs.append(meeting_ref)
                # Betterment P1: a risk the meeting named is a risk.
                for sentence in _risk_sentences(summary):
                    risks.append({"ref": meeting_ref, "source": title, "text": sentence})
            except Exception:
                caveats.append({
                    "section": "meetings",
                    "state": "degraded",
                    "reason": "meeting_summary_read_failed",
                })

        # Betterment P1: the risks a meeting's artifacts list (risk_heatmap).
        try:
            for artifact in self._db.projects.get_project_artifacts(project_id):
                if (
                    str(artifact.meeting_id or "") in one_on_one_ids
                    and not explicitly_filed("artifact", str(artifact.id or ""))
                ):
                    continue
                for entry in (artifact.structured_json or {}).get("risks") or []:
                    text = entry.get("risk") if isinstance(entry, dict) else entry
                    text = " ".join(str(text or "").split())
                    if text:
                        risks.append({
                            "ref": format_ref("meeting", str(artifact.meeting_id)),
                            "source": str(artifact.title or "Meeting"), "text": text,
                        })
        except Exception:
            caveats.append({"section": "meetings", "state": "degraded", "reason": "meeting_risks_read_failed"})

        # Betterment P1: notes filed as the project's sources. A line that
        # names a risk (or every line of a note titled as risks) is a risk.
        try:
            for resource in project_resources:
                kind, _, note_id = str(resource.get("resource_ref") or "").partition(":")
                if kind != "note" or not note_id:
                    continue
                note = self._db.notes.get(note_id)
                if note is None:
                    continue
                notes_read += 1
                note_ref = format_ref("note", note_id)
                source_refs.append(note_ref)
                note_title = " ".join(str(getattr(note, "title", "") or "").split()) or "Note"
                for line in _note_risk_lines(note_title, str(getattr(note, "body_markdown", "") or "")):
                    risks.append({"ref": note_ref, "source": note_title, "text": line})
        except Exception:
            caveats.append({"section": "resources", "state": "degraded", "reason": "notes_read_failed"})

        try:
            actions = self._project_service.list_action_items(
                principal, project_id,
            )
            for action in actions:
                owner = " ".join(str(action.get("owner") or "").split())
                action_id = str(action.get("id") or "").strip()
                status = str(action.get("status") or "pending").strip().lower()
                if (
                    str(action.get("meeting_id") or "") in one_on_one_ids
                    and not (
                        explicitly_filed("action", action_id)
                        or explicitly_filed("action_item", action_id)
                    )
                ):
                    continue
                if (
                    action_id
                    and owner
                    and status in {"pending", "open"}
                ):
                    linked_actions.append({
                        "id": action_id,
                        "task": action.get("task"),
                        "owner": owner,
                        "due": action.get("due"),
                        "status": status,
                        "created_at": action.get("created_at"),
                    })
                    source_refs.append(format_ref("action_item", action_id))
        except Exception:
            caveats.append({
                "section": "meetings",
                "state": "degraded",
                "reason": "action_items_read_failed",
            })

        decisions_section = room.get("decisions", {})
        if decisions_section.get("state") == "degraded":
            caveats.append({
                "section": "decisions",
                "state": "degraded",
                "reason": str(
                    decisions_section.get("error_code")
                    or "decisions_read_failed"
                ),
            })
        else:
            one_on_one_records = self._records_from_meetings(one_on_one_ids)
            for decision in decisions_section.get("items", []):
                decision_id = str(decision.get("id") or "").strip()
                if (
                    decision_id in one_on_one_records
                    and not (
                        explicitly_filed("decision", decision_id)
                        or explicitly_filed("decision_record", decision_id)
                        or explicitly_filed("desk_decision", decision_id)
                    )
                ):
                    continue
                # The Room keeps action-kind confirmed proposals in its
                # decision projection for continuity.  Their action item is
                # already read above; drawing them as decisions duplicates
                # the source and changes its meaning.
                if str(decision.get("kind") or "decision").strip() != "decision":
                    continue
                decision_text = " ".join(
                    str(decision.get("text") or "").split()
                )
                if not decision_id or not decision_text:
                    continue
                linked_decisions.append({
                    "id": decision_id,
                    "text": decision_text,
                    "lifecycle": decision.get("lifecycle"),
                })
                source_refs.append(format_ref("decision", decision_id))

        linked_actions.sort(key=lambda action: (
            str(action.get("created_at") or ""),
            str(action.get("id") or ""),
        ), reverse=True)
        linked_decisions.sort(key=lambda decision: str(decision.get("id") or ""))
        caveats.sort(key=lambda caveat: (
            caveat.get("section", ""), caveat.get("reason", ""),
        ))
        return {
            "meeting_summaries": meeting_summaries,
            "linked_decisions": linked_decisions,
            "linked_actions": linked_actions,
            "caveats": caveats,
            "source_refs": sorted(set(source_refs)),
            "left_out": sorted(left_out, key=lambda m: (m["title"], m["id"])),
            "risks": risks,
            "notes_read": notes_read,
            "sources": _outside_sources(room),
        }

    def _records_from_meetings(self, meeting_ids: set[str]) -> set[str]:
        """The decision records whose source is one of these meetings."""
        if not meeting_ids:
            return set()
        try:
            with self._db._connection() as conn:
                rows = conn.execute(
                    "SELECT record_id FROM decision_record_sources "
                    "WHERE source_type = 'meeting' "
                    "AND source_ref IN (SELECT value FROM json_each(?))",
                    (json.dumps(sorted(meeting_ids)),),
                ).fetchall()
        except Exception:
            _log.debug("update draft: 1:1 decision records not read", exc_info=True)
            return set()
        return {str(row["record_id"]) for row in rows}

    def publish_update(
        self,
        principal: Principal,
        update_id: str,
        *,
        command_id: str | None = None,
    ) -> dict[str, Any]:
        """Publish a draft with the project revision law.

        ONE transaction: publish + revision+1 + project_changes row
        + ServiceEventLedger.append_in_transaction.

        Raises PublishedUpdateError if already published.
        Raises NotFound if the update does not exist.
        """
        row = self._db.project_updates.get_update(update_id)
        if row is None:
            raise NotFound("update", update_id)

        project_id = row["project_id"]
        ledger = ServiceEventLedger(self._db)
        cmd_id = command_id or generate_pcmd_id()

        with self._db._connection() as conn:
            # 1. Publish the update (raises PublishedUpdateError if
            #    already published)
            self._db.project_updates.publish_update_in_transaction(
                conn, update_id,
            )

            # 2. Bump project revision
            proj_row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
            if proj_row is None:
                raise NotFound("project", project_id)
            current_rev = int(proj_row["revision"])
            new_revision = current_rev + 1
            now_iso = utc_now_iso()

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # 3. project_changes row
            project_ref = format_ref("project", project_id)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            req_hash = _request_hash({"update_id": update_id})
            conn.execute(
                """INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None,
                    _request_hash({"update_id": update_id, "lifecycle": "published"}),
                    json.dumps({
                        "action": "update.published",
                        "update_id": update_id,
                    }),
                    now_iso,
                ),
            )

            # 4. ServiceEventLedger
            ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectUpdateService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "update.published",
                    "update_id": update_id,
                },
                refs=[project_ref],
            )

            # 5. The one answer per command, and the admitted operation's end,
            #    in THIS transaction (PHILO-9-02 round three, ruling A): a
            #    failure anywhere rolls back the publication, the answer and
            #    the receipt together.
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            published = self._project_axes(
                self._db.project_updates.get_update_in_transaction(conn, update_id)
            )
            published.update(_envelope_to_dict(envelope))
            from holdspeak.services import project_kernel

            project_kernel.answered(
                conn, command_id=cmd_id, project_id=project_id, command_kind="publish_update",
                request_hash=req_hash, answer=published,
            )
        return published

    # ── The reviewer path (HS-200-06, C2) ───────────────────────────

    def review_claim(
        self,
        principal: Principal,
        update_id: str,
        span_id: str,
        *,
        acceptance: str | None = None,
        support: str | None = None,
    ) -> dict[str, Any]:
        """Record a PERSON's judgment on one claim of a draft.

        Acceptance is a human act: only an OWNER principal may move it.
        No model score, and no agent, can reach this verb (C2).

        ``support="supported"`` writes a REVIEWER support record naming
        the reviewer, the exact source version, and the refs attested.
        It refuses a claim that carries no ref -- attestation still names
        a source.  ``support="disputed"`` needs no ref.

        Raises PublishedUpdateError on a published update (the repo's
        immutability law), NotFound when the update or span is unknown,
        ValidationError on an unauthorized principal or unknown state.
        """
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Only the owner can review a claim",
                code="claim_review_forbidden",
            )
        if acceptance is None and support is None:
            raise ValidationError(
                "Nothing to review: pass acceptance or support",
                code="claim_review_empty",
            )
        if acceptance is not None and acceptance not in ACCEPTANCE_STATES:
            raise ValidationError(
                f"Unknown acceptance state: {acceptance!r}",
                code="claim_acceptance_unknown",
            )
        if support is not None and support not in (
            SUPPORT_SUPPORTED, SUPPORT_DISPUTED, SUPPORT_SOURCE_LINKED,
        ):
            raise ValidationError(
                f"A reviewer cannot set support to {support!r}",
                code="claim_support_unknown",
            )

        row = self._db.project_updates.get_update(update_id)
        if row is None:
            raise NotFound("update", update_id)

        claims_json = migrate_claims_json(
            row.get("claims_json") or "",
            generator=str(row.get("generator") or "deterministic"),
        )
        try:
            claims = json.loads(claims_json or "[]")
        except (ValueError, TypeError):
            claims = []
        if not isinstance(claims, list):
            claims = []

        target: dict[str, Any] | None = None
        for claim in claims:
            if isinstance(claim, dict) and claim.get("span_id") == span_id:
                target = claim
                break
        if target is None:
            raise NotFound("claim", span_id)

        if support == SUPPORT_SUPPORTED and not (target.get("refs") or []):
            raise ValidationError(
                "A reviewer cannot support a claim that cites no source",
                code="claim_support_no_source",
            )

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if acceptance is not None:
            target["acceptance"] = acceptance
        if support is not None:
            target["support"] = support
            record = SupportRecord(
                method=METHOD_REVIEWER,
                source_version=(
                    f"project:{row['project_id']}@r{row['project_revision']}"
                ),
                source_refs=list(target.get("refs") or []),
                reviewer_ref=f"principal:{principal.identity}",
                checked_at=now_iso,
            )
            target["support_record"] = record.to_dict()

        self._db.project_updates.update_draft(
            update_id,
            claims_json=json.dumps(
                claims, sort_keys=True, separators=(",", ":"),
            ),
        )
        return self._project_axes(
            self._db.project_updates.get_update(update_id)
        )

    # ── Internal helpers (HS-162-04) ────────────────────────────────

    def _record_command(
        self,
        command_id: str,
        project_id: str,
        command_kind: str,
        request_hash: str,
        envelope: CommandResultEnvelope,
    ) -> None:
        """Record a completed command in the idempotency ledger."""
        now_iso = utc_now_iso()
        result_json = json.dumps(
            _envelope_to_dict(envelope), ensure_ascii=False,
        )
        with self._db._connection() as conn:
            conn.execute(
                """INSERT INTO project_commands (
                    id, project_id, command_kind, request_hash,
                    status, result_json, completed_at, created_at
                ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = 'completed',
                    result_json = excluded.result_json,
                    completed_at = excluded.completed_at
                """,
                (
                    command_id, project_id, command_kind, request_hash,
                    result_json, now_iso, now_iso,
                ),
            )


def _append_week_sources(
    sections: dict[str, str],
    claims: list[Claim],
    source_version: str,
    week: dict[str, Any],
) -> dict[str, str]:
    """Add linked week lines while retaining the existing Room builders."""
    def add_lines(key: str, lines: list[str]) -> None:
        if not lines:
            return
        current = sections.get(key, _HONEST_MINIMAL[key])
        if current == _HONEST_MINIMAL[key]:
            sections[key] = "\n".join(lines)
        else:
            sections[key] = current + "\n" + "\n".join(lines)

    progress: list[str] = []
    for ordinal, meeting in enumerate(week.get("meeting_summaries", [])):
        meeting_id = str(meeting.get("id") or "").strip()
        title = str(meeting.get("title") or "Meeting").strip() or "Meeting"
        summary = " ".join(str(meeting.get("summary") or "").split())
        if not meeting_id or not summary:
            continue
        text = f"Meeting summary: {title} -- {summary}"
        ref = format_ref("meeting", meeting_id)
        claims.append(Claim(
            span_id=f"s_progress_meeting_{ordinal}", text=text, refs=[ref],
            section="progress", kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref], ["meeting_id", "title", "summary"],
            ),
        ))
        progress.append(f"- {text}")
    add_lines("progress", progress)

    decisions: list[str] = []
    for ordinal, decision in enumerate(week.get("linked_decisions", [])):
        decision_id = str(decision.get("id") or "").strip()
        decision_text = " ".join(str(decision.get("text") or "").split())
        lifecycle = str(decision.get("lifecycle") or "recorded").strip()
        if not decision_id or not decision_text:
            continue
        text = f"Decision: {decision_text} -- {lifecycle}"
        ref = format_ref("decision", decision_id)
        claims.append(Claim(
            span_id=f"s_decisions_meeting_{ordinal}", text=text, refs=[ref],
            section="decisions", kind=KIND_DECISION,
            support=SUPPORT_SUPPORTED,
            acceptance=_PROPOSAL_ACCEPTANCE.get(
                lifecycle, ACCEPTANCE_UNREVIEWED,
            ),
            support_record=_field_mapping_support(
                source_version, [ref], ["text", "lifecycle"],
            ),
        ))
        decisions.append(f"- {text}")
    add_lines("decisions", decisions)

    actions: list[str] = []
    for ordinal, action in enumerate(week.get("linked_actions", [])):
        action_id = str(action.get("id") or "").strip()
        task = " ".join(str(action.get("task") or "").split())
        owner = " ".join(str(action.get("owner") or "").split())
        status = str(action.get("status") or "pending").strip() or "pending"
        due = action.get("due")
        if not action_id or not task or not owner:
            continue
        due_text = f", due {due}" if due else ""
        text = f"Action: {task} -- {status}, owner {owner}{due_text}"
        ref = format_ref("action_item", action_id)
        claims.append(Claim(
            span_id=f"s_next_actions_meeting_{ordinal}", text=text, refs=[ref],
            section="next_actions", kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(
                source_version, [ref], ["task", "owner", "status", "due"],
            ),
        ))
        actions.append(f"- {text}")
    add_lines("next_actions", actions)

    # Betterment P1: risks named in meetings and in notes filed as sources.
    risk_lines: list[str] = []
    seen_risks: set[str] = set()
    for ordinal, risk in enumerate(week.get("risks", [])):
        body = str(risk.get("text") or "").strip()
        if not body or body.casefold() in seen_risks:
            continue
        seen_risks.add(body.casefold())
        text = f"Risk ({risk.get('source') or 'source'}): {body}"
        ref = str(risk.get("ref") or "")
        claims.append(Claim(
            span_id=f"s_risks_blockers_week_{ordinal}", text=text, refs=[ref] if ref else [],
            section="risks_blockers", kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED if ref else SUPPORT_UNKNOWN,
            support_record=_field_mapping_support(source_version, [ref], ["text"]) if ref else None,
        ))
        risk_lines.append(f"- {text}")
    add_lines("risks_blockers", risk_lines)

    # Betterment P1: what was read, and what was not.
    coverage: list[str] = []
    read = [
        _plural(n, one, many) for n, one, many in (
            (len(week.get("meeting_summaries", [])), "meeting", "meetings"),
            (int(week.get("notes_read") or 0), "note", "notes"),
            (len(week.get("linked_decisions", [])), "decision", "decisions"),
            (len(week.get("linked_actions", [])), "action", "actions"),
            (int(week.get("items_read") or 0), "project item", "project items"),
        ) if n
    ]
    sources = week.get("sources", [])
    read += [src["label"] for src in sources if src.get("state") == "live"]
    if read:
        coverage.append("Read: " + ", ".join(read))
    for src in sources:
        if src.get("state") == "live":
            continue
        coverage.append(f"Not read: {src['label']} ({src.get('reason') or 'not checked'})")
    project_ref = str(week.get("project_ref") or "")
    for ordinal, text in enumerate(coverage):
        claims.append(Claim(
            span_id=f"s_source_coverage_read_{ordinal}", text=text,
            refs=[project_ref] if project_ref else [], section="source_coverage",
            kind=KIND_OBSERVATION, support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(source_version, [project_ref], ["sources"]),
        ))
    add_lines("source_coverage", [f"- {line}" for line in coverage])

    # Betterment P2 (decision 18): a 1:1 is named as left out, never quoted.
    left_out: list[str] = []
    for ordinal, meeting in enumerate(week.get("left_out", [])):
        meeting_id = str(meeting.get("id") or "").strip()
        title = " ".join(str(meeting.get("title") or "").split()) or "Meeting"
        if not meeting_id:
            continue
        named = title if title_says_one_on_one(title) else f"{title} (1:1)"
        text = f"Left out: {named}"
        ref = format_ref("meeting", meeting_id)
        claims.append(Claim(
            span_id=f"s_source_coverage_left_out_{ordinal}", text=text, refs=[ref],
            section="source_coverage", kind=KIND_OBSERVATION,
            support=SUPPORT_SUPPORTED,
            support_record=_field_mapping_support(source_version, [ref], ["meeting_id", "title"]),
        ))
        left_out.append(f"- {text}")
    add_lines("source_coverage", left_out)
    return sections


# ── Betterment P1: risks and coverage from the records ──────────────

_PROVIDER_WORDS = {"github": "GitHub", "jira": "Jira", "confluence": "Confluence"}


def _outside_sources(room: dict[str, Any]) -> list[dict[str, str]]:
    """The Room's outside sources (GitHub, Jira, Confluence) with their state."""
    section = room.get("sources") or {}
    if section.get("state") != "ok":
        return []
    out: list[dict[str, str]] = []
    for item in section.get("items") or []:
        provider = str(item.get("provider") or "")
        if provider == "meeting" or item.get("suggested"):
            continue
        label = " ".join(p for p in (_PROVIDER_WORDS.get(provider, provider.capitalize()),
                                     str(item.get("scope") or "").strip()) if p)
        # The Room's one freshness rule (``needs_you_aggregate.source_freshness``):
        # only an available source counts as read; stale, paused, never
        # checked or failing is "not read", with the Room's own reason.
        freshness = str(item.get("freshness") or "")
        if freshness:
            read = freshness == "available"
            reason = str(item.get("freshnessReason") or "").strip()
        else:
            read = str(item.get("state") or "") == "live"
            reason = str(item.get("plainReason") or "").strip()
        out.append({"label": label, "state": "live" if read else "not_read", "reason": reason or "not checked"})
    return out


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


#: PHILO-15 B64 (Astra r2): the one claim of a draft with nothing observed.
NOTHING_TO_REPORT = "Nothing to report."

#: PHILO-15 B64: the provenance of a sentence the owner wrote in the editor.
OWNER_TEXT_FIELD = "owner_text"


def _owner_authored_claims(claims_json: str, body_md: str, principal: Principal) -> str | None:
    """Astra r1 P1-3 ruling: a saved owner-authored replacement counts as
    reviewed for its EXACT new words, with provenance kept. Each body line
    whose words are no claim's words gets an accepted claim naming the owner.
    A line that still carries the desk mark is not authored (formatting is
    not review). Returns the new blob, or None when nothing was added."""
    from .channel_contract import _claim_lines, _section_headings, _sentence, has_desk_mark

    try:
        claims = json.loads(claims_json or "[]")
    except (TypeError, ValueError):
        claims = []
    if not isinstance(claims, list):
        claims = []
    known = {line for c in claims if isinstance(c, dict) for line in _claim_lines(c)}
    neutral = {"Not checked."} | {str(v).strip() for v in _HONEST_MINIMAL.values()}
    by_heading = {f"## {h}": k for k, h in _SECTION_HEADINGS.items()}
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    section = "progress"
    added: list[dict[str, Any]] = []
    ordinal = sum(1 for c in claims if isinstance(c, dict) and str(c.get("span_id", "")).startswith("s_owner_"))
    headings = _section_headings()
    for line in str(body_md or "").splitlines():
        if line.strip() in headings:
            section = by_heading.get(line.strip(), section)
            continue
        # Astra r2: compared with formatting removed, so pasting or re-styling
        # the model's sentence (bold, a list, a quote, a heading, the desk mark
        # unbolded) is never new authorship. Accept is the review gesture.
        words = _sentence(line)
        if not words or words in neutral or words in known or has_desk_mark(line):
            continue
        known.add(words)
        added.append({
            "span_id": f"s_owner_{ordinal}", "text": words, "refs": [], "section": section,
            "kind": KIND_OBSERVATION, "support": SUPPORT_UNKNOWN, "acceptance": ACCEPTANCE_ACCEPTED,
            "support_record": SupportRecord(
                method=METHOD_REVIEWER, fields=[OWNER_TEXT_FIELD],
                reviewer_ref=f"principal:{principal.identity}", checked_at=now_iso,
            ).to_dict(),
        })
        ordinal += 1
    if not added:
        return None
    return json.dumps(claims + added, sort_keys=True, separators=(",", ":"))


def _invalidate_edited_support(
    claims_json: str,
    body_md: str,
) -> str | None:
    """Drop support for every claim whose sentence left the body (C2).

    Returns the rewritten blob, or ``None`` when nothing changed.
    The support record is KEPT and stamped -- provenance survives the
    edit, and ``verified`` is never touched.
    """
    if not claims_json:
        return None
    try:
        claims = json.loads(claims_json)
    except (ValueError, TypeError):
        return None
    if not isinstance(claims, list):
        return None

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        text = str(claim.get("text") or "")
        if not text or text in body_md:
            continue
        if claim.get("support") != SUPPORT_SUPPORTED:
            continue
        claim["support"] = (
            SUPPORT_SOURCE_LINKED if (claim.get("refs") or [])
            else SUPPORT_UNKNOWN
        )
        record = dict(claim.get("support_record") or {})
        record.setdefault("method", METHOD_FIELD_MAPPING)
        record["invalidated_at"] = now_iso
        record["invalidation_reason"] = INVALIDATION_TEXT_EDITED
        claim["support_record"] = record
        changed = True

    if not changed:
        return None
    return json.dumps(claims, sort_keys=True, separators=(",", ":"))


def _body_sha(body_md: Any) -> str:
    return hashlib.sha256(str(body_md or "").encode("utf-8")).hexdigest()


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash of a command's request payload."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _envelope_to_dict(env: CommandResultEnvelope) -> dict[str, Any]:
    """Serialize an envelope to a JSON-safe dict."""
    return {
        "result_kind": env.result_kind.value,
        "project_id": env.project_id,
        "project_revision": env.project_revision,
        "changed_refs": [str(r) for r in env.changed_refs],
    }


class _ModelDraftFailed(Exception):
    """Internal signal: the model drafting path failed; fall back.

    ``code`` is the typed reason the draft's receipt NAMES (HS-200-08);
    ``reason`` stays the full human detail for the log.
    """

    def __init__(
        self, reason: str, code: str = FALLBACK_MODEL_UNAVAILABLE, *, detail: str = "",
    ) -> None:
        self.reason = reason
        self.code = code
        # Plain words for the face (P0): why the draft was not made.
        self.detail = detail
        super().__init__(reason)
