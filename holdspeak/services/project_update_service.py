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
from holdspeak.timestamps import utc_now_iso
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
from .memory_grounding import memory_for, project_pages

#: The marked block the project's memory travels in, inside the draft prompt.
MEMORY_BLOCK_HEADING = "PROJECT MEMORY"
from .errors import ConflictError, NotFound, ValidationError
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
            raise _ModelDraftFailed("no_broker", FALLBACK_MODEL_UNAVAILABLE)

        runner = broker.inference_runner

        # Resolve deployment revision for the update-draft capability.
        try:
            deployment_rev_id, assignment_id, route_profile_id = (
                _resolve_for_capability(broker, PROJECT_UPDATE_CAPABILITY)
            )
        except RuntimeError as exc:
            raise _ModelDraftFailed(
                f"route_unresolved: {exc}", FALLBACK_ROUTE_UNRESOLVED,
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
            raise _ModelDraftFailed("no_output", FALLBACK_NO_OUTPUT)

        # Parse and constrain to the claim schema.
        parsed = _parse_model_output(raw, inventory_refs, inventory_texts, known_names)
        if parsed is None:
            raise _ModelDraftFailed(
                "unparseable_output", FALLBACK_UNPARSEABLE_OUTPUT,
            )

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

        det_body_md = _assemble_body(_append_week_sources(det_sections, det_claims, source_version, week))
        det_claims_json = json.dumps(
            [c.to_dict() for c in det_claims],
            sort_keys=True,
            separators=(",", ":"),
        )

        # 6. Build source manifest (byte-identical regardless of generator).
        manifest = _build_source_manifest(
            room, review_id, observation_ids, caveats,
        )
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
                if memory:
                    manifest_json = json.dumps({
                        **manifest, "week_source_refs": week["source_refs"],
                        "memory_refs": memory.refs,
                    }, sort_keys=True, separators=(",", ":"))
            except _ModelDraftFailed as exc:
                _log.warning(
                    "Model drafter failed (%s); falling back to deterministic.",
                    exc.reason,
                )
                body_md = det_body_md
                claims_json = det_claims_json
                # HS-200-08: the fallback NAMES its reason on the row, so the
                # face shows a token instead of a log line nobody reads.
                actual_generator = FALLBACK_GENERATOR_PREFIX + exc.code
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
            existing = self._claim_draft_command(command_id, project_id, req_hash)
            if existing is not None:
                return existing

        try:
            result = self.draft_update(principal, project_id, generator=generator)
        except BaseException:
            if command_id is not None:
                # The claim is released: the same command_id may try again.
                self._db.projects.complete_project_command(
                    command_id, status="failed", error_code="draft_failed",
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
                    (command_id, project_id, req_hash, datetime.now().isoformat()),
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

    def _read_week_sources(
        self,
        principal: Principal,
        project_id: str,
        room: dict[str, Any],
    ) -> dict[str, Any]:
        """Read the persisted, non-parked sources linked to a project."""
        meeting_summaries: list[dict[str, Any]] = []
        linked_actions: list[dict[str, Any]] = []
        linked_decisions: list[dict[str, Any]] = []
        caveats: list[dict[str, str]] = []
        source_refs: list[str] = []

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
            try:
                meeting = self._db.meetings.get_meeting(meeting_id)
                if meeting is None:
                    caveats.append({
                        "section": "meetings",
                        "state": "degraded",
                        "reason": "meeting_unavailable",
                    })
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
            except Exception:
                caveats.append({
                    "section": "meetings",
                    "state": "degraded",
                    "reason": "meeting_summary_read_failed",
                })

        try:
            actions = self._project_service.list_action_items(
                principal, project_id,
            )
            for action in actions:
                owner = " ".join(str(action.get("owner") or "").split())
                action_id = str(action.get("id") or "").strip()
                status = str(action.get("status") or "pending").strip().lower()
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
            for decision in decisions_section.get("items", []):
                # The Room keeps action-kind confirmed proposals in its
                # decision projection for continuity.  Their action item is
                # already read above; drawing them as decisions duplicates
                # the source and changes its meaning.
                if str(decision.get("kind") or "decision").strip() != "decision":
                    continue
                decision_id = str(decision.get("id") or "").strip()
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
        }

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
    return sections


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
    """Internal signal: the model drafting path failed; fall back.

    ``code`` is the typed reason the draft's receipt NAMES (HS-200-08);
    ``reason`` stays the full human detail for the log.
    """

    def __init__(self, reason: str, code: str = FALLBACK_MODEL_UNAVAILABLE) -> None:
        self.reason = reason
        self.code = code
        super().__init__(reason)
