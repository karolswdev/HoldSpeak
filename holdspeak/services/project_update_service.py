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

import hashlib
import json
import re as _re
import time as _time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

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
from .errors import ConflictError, NotFound, ValidationError
from .service_event_ledger import ServiceEventLedger

_log = get_logger("services.project_update_service")

# ── Capability identity (HS-162-03) ──────────────────────────────────
PROJECT_UPDATE_CAPABILITY = "project.update_draft"

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
    "source_coverage": "All sources consulted successfully.",
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

        reason_str = f": {reason}" if reason else ""
        text = f"Section '{section_name}' {state}{reason_str}"
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


def _build_model_prompt(inventory_claims: list[Claim]) -> dict[str, Any]:
    """Build a prompt payload from the deterministic evidence inventory.

    The model is given every deterministic claim (with its refs) and asked
    to rewrite the sections with better prose, citing the exact refs.
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

    return {
        "system_prompt": system_prompt,
        "user_prompt": "EVIDENCE INVENTORY:\n" + "\n".join(inventory_lines),
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
_NUMBER_LITERAL_RE = _re.compile(r"(?<![\w-])\d+(?:[.,]\d+)?%?(?![\w-])")
_NAME_LITERAL_RE = _re.compile(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b")

# Capitalized words that are grammar or report vocabulary, not names.
# A capitalized word outside this set that the cited source does not
# carry is reported as a typed unknown -- including at the start of a
# sentence, where "Priya owes ..." must not hide behind grammar.
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
    "Work", "Workstream",
})


def _normalize_for_match(text: str) -> str:
    """Lowercase, collapse whitespace -- the corroboration haystack."""
    return " ".join(str(text or "").lower().split())


def _typed_unknowns(text: str, source_text: str) -> list[dict[str, str]]:
    """Literals in ``text`` that the cited source's fields do not carry.

    Returns typed unknowns sorted deterministically:
    ``[{"type": "deadline"|"number"|"name", "value": "..."}]``.
    """
    haystack = _normalize_for_match(source_text)
    found: set[tuple[str, str]] = set()

    masked = text
    for match in _DATE_LITERAL_RE.finditer(text):
        value = match.group(0)
        if _normalize_for_match(value) not in haystack:
            found.add(("deadline", value))
    masked = _DATE_LITERAL_RE.sub(" ", masked)

    for match in _NUMBER_LITERAL_RE.finditer(masked):
        value = match.group(0)
        if _normalize_for_match(value) not in haystack:
            found.add(("number", value))

    for match in _NAME_LITERAL_RE.finditer(masked):
        value = match.group(0)
        if value in _NAME_STOPWORDS:
            continue
        if _normalize_for_match(value) not in haystack:
            found.add(("name", value))

    return [
        {"type": kind, "value": value}
        for kind, value in sorted(found)
    ]


def _parse_model_output(
    raw: str,
    inventory_refs: frozenset[str],
    inventory_texts: dict[str, str] | None = None,
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
                    unknowns=_typed_unknowns(text, source_text),
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
                lines.append(f"- {UNVERIFIED_MARKER} {text}")

        if lines:
            sections[key] = "\n".join(lines)
        else:
            sections[key] = _HONEST_MINIMAL.get(key, "")

    # Fill missing sections with honest minimums.
    for key in SECTION_KEYS:
        if key not in sections:
            sections[key] = _HONEST_MINIMAL.get(key, "")

    return sections, claims


def _resolve_for_capability(
    db: Any,
    capability_id: str,
) -> tuple[str, str]:
    """Resolve the deployment revision and assignment ID for a capability.

    Returns ``(deployment_revision_id, assignment_id)``.
    Raises ``RuntimeError`` if no assignment exists.
    """
    key = f"capability:{capability_id}"
    with db._connection() as conn:
        head = conn.execute(
            "SELECT assignment_id, revision FROM inference_assignment_heads "
            "WHERE assignment_key=? AND cleared=0",
            (key,),
        ).fetchone()
        if head is None:
            raise RuntimeError(f"No assignment for {capability_id}")
        assignment_id = str(head["assignment_id"])
        entry = conn.execute(
            "SELECT profile_id FROM inference_assignments "
            "WHERE assignment_id=? AND assignment_revision=? "
            "ORDER BY ordinal LIMIT 1",
            (assignment_id, head["revision"]),
        ).fetchone()
        if entry is None:
            raise RuntimeError(
                f"No entries in assignment for {capability_id}"
            )
        profile_id = entry["profile_id"]
        rev = conn.execute(
            "SELECT id FROM deployment_revisions WHERE model=? LIMIT 1",
            (profile_id,),
        ).fetchone()
        if rev is None:
            raise RuntimeError(
                f"No deployment revision for profile {profile_id}"
            )
        return str(rev["id"]), assignment_id


# ── Generator provenance (HS-173-02) ─────────────────────────────────

def _resolve_generator_provenance(
    db: Any,
    deployment_rev_id: str,
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
    ) -> None:
        self._db = db
        self._project_service = project_service
        self._delta_service = delta_service
        self._broker = broker

    # ── C2 read projection (HS-200-06) ───────────────────────────────

    @staticmethod
    def _project_axes(row: dict[str, Any] | None) -> dict[str, Any] | None:
        """Project the three C2 axes onto a row as it is READ.

        Records written before HS-200-06 keep their stored bytes; the
        conservative mapping is applied here, on the way out.
        """
        if not row:
            return row
        out = dict(row)
        out["claims_json"] = migrate_claims_json(
            out.get("claims_json") or "",
            generator=str(out.get("generator") or "deterministic"),
        )
        return out

    # ── Model drafter (HS-162-03) ────────────────────────────────────

    def _draft_with_model(
        self,
        principal: Principal,
        det_claims: list[Claim],
        det_sections: dict[str, str],
        det_body_md: str,
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
            raise _ModelDraftFailed("no_broker")

        runner = broker.inference_runner

        # Resolve deployment revision for the update-draft capability.
        try:
            deployment_rev_id, assignment_id = _resolve_for_capability(
                broker.database, PROJECT_UPDATE_CAPABILITY,
            )
        except RuntimeError as exc:
            raise _ModelDraftFailed(f"no_assignment: {exc}") from exc

        # HS-173-02: derive generator provenance from the deployment revision.
        gen_host: str | None = None
        gen_model: str | None = None
        try:
            gen_host, gen_model = _resolve_generator_provenance(
                broker.database, deployment_rev_id,
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

        payload = _build_model_prompt(det_claims)

        request = InvocationRequest(
            deployment_revision=deployment_rev_id,
            definition_origin=ServiceContract.for_payload(
                "project.update.draft", "1", payload,
            ),
            deadline_at=_time.time() + 120,
            payload=payload,
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
            raise _ModelDraftFailed(f"runner_error: {exc}") from exc

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
            raise _ModelDraftFailed("no_output")

        # Parse and constrain to the claim schema.
        parsed = _parse_model_output(raw, inventory_refs, inventory_texts)
        if parsed is None:
            raise _ModelDraftFailed("unparseable_output")

        model_sections, model_claims = parsed
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

        Returns:
            The persisted draft as a dict (from the updates repo).
        """
        want_model = generator == "model"

        # 1. Read the room at ONE pinned revision
        room = self._project_service.room(principal, project_id)
        revision = room.get("revision", 0)

        # 2. Scan for caveats (degraded/absent sections)
        caveats = _scan_caveats(room)

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

        det_sections: dict[str, str] = {
            "progress": _build_progress(
                items_section, det_claims, source_version),
            "decisions": _build_decisions(
                review_section, proposals, det_claims, source_version),
            "risks_blockers": _build_risks_blockers(
                items_section, det_claims, source_version),
            "dependencies": _build_dependencies(
                items_section, det_claims, source_version),
            "next_actions": _build_next_actions(
                items_section, det_claims, source_version),
            "source_coverage": _build_source_coverage(
                room, caveats, det_claims, source_version),
        }

        det_body_md = _assemble_body(det_sections)
        det_claims_json = json.dumps(
            [c.to_dict() for c in det_claims],
            sort_keys=True,
            separators=(",", ":"),
        )

        # 6. Build source manifest (byte-identical regardless of generator).
        manifest = _build_source_manifest(
            room, review_id, observation_ids, caveats,
        )
        manifest_json = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"),
        )

        # 7. Choose body + claims based on generator.
        actual_host: str | None = None
        actual_model: str | None = None
        if want_model:
            try:
                body_md, claims_json, actual_generator, actual_host, actual_model = (
                    self._draft_with_model(
                        principal, det_claims, det_sections, det_body_md,
                    )
                )
            except _ModelDraftFailed as exc:
                _log.warning(
                    "Model drafter failed (%s); falling back to deterministic.",
                    exc.reason,
                )
                body_md = det_body_md
                claims_json = det_claims_json
                actual_generator = "deterministic"
                actual_host = None
                actual_model = None
        else:
            body_md = det_body_md
            claims_json = det_claims_json
            actual_generator = "deterministic"

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
        return [self._project_axes(r) for r in rows]

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
        return self._project_axes(row)

    def draft_update_command(
        self,
        principal: Principal,
        project_id: str,
        *,
        generator: str = "deterministic",
        command_id: str | None = None,
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
        })
        if command_id is not None:
            existing = self._db.projects.get_project_command(command_id)
            if existing is not None:
                if (existing["status"] == "completed"
                        and existing["request_hash"] == req_hash):
                    if existing["result_json"]:
                        return json.loads(existing["result_json"])
                    return {"result_kind": "no_change", "project_id": project_id}
                if existing["request_hash"] != req_hash:
                    raise ConflictError(
                        "idempotency conflict: same command_id with different request hash",
                        code="idempotency_conflict",
                    )

        result = self.draft_update(principal, project_id, generator=generator)

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

    def save_update(
        self,
        principal: Principal,
        update_id: str,
        *,
        body_md: str | None = None,
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
        req_hash = _request_hash({
            "update_id": update_id,
            "body_md": body_md,
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
            now_iso = datetime.now().isoformat()

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

            # 5. Command idempotency ledger
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            result_json = json.dumps(
                _envelope_to_dict(envelope), ensure_ascii=False,
            )
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
                    cmd_id, project_id, "publish_update", req_hash,
                    result_json, now_iso, now_iso,
                ),
            )

        # Return the published update with the envelope merged in
        published = self._project_axes(
            self._db.project_updates.get_update(update_id)
        )
        published.update(_envelope_to_dict(envelope))
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
        now_iso = datetime.now().isoformat()
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
    """Internal signal: the model drafting path failed; fall back."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
