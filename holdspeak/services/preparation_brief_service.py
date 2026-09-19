"""HS-200-11 -- the preparation brief: one manual preparation path over a
Project's read sources, its carried decisions and its open commitments.

The story's five criteria, and where each is paid here:

1. **A purpose without a calendar.**  ``prepare`` takes the purpose the owner
   typed or spoke and nothing else; no calendar source is read or required.
   The manifest records ``calendar: {"present": False}`` so the face can say
   ``PURPOSE SET BY HAND · NO CALENDAR`` from a stored fact, never a guess.
2. **A source manifest.**  ``build_manifest`` freezes what the draft saw: every
   Room source with its C4 state, observation time and revision; the current
   and superseded decisions carried in (a superseded one names its
   successor); every omission NAMED with its reason and its repair; and, once
   a draft exists, every item the bound left out (``not_included``).  The
   manifest is stored beside the brief and its sha256 is recomputed on every
   read (the ``refinement_attachment_revisions`` freeze mechanic, ruling R3).
3. **Bounded output.**  ``Outline`` is the typed shape both drafters produce:
   at most ``MAX_PRIORITIES`` priorities, ``MAX_QUESTIONS`` questions and
   ``MAX_OBLIGATIONS`` obligations.  Never a source dump -- and never a
   SILENT cut: what was left out is named (counsel P1-3).  Every sentence is
   a ``Claim`` on the three independent C2 axes (HS-200-06).  A sentence the
   model cites to a SUPERSEDED decision is typed ``DECISION · SUPERSEDED``
   and never lands in the outline (counsel P1-2).
4. **Attached to its Project.**  ``project_briefs.project_id`` and the
   ``lifecycle`` flip on ``keep``; the Room lists kept briefs by Project.
5. **Unavailable AI.**  ``route`` reads the frozen route WITHOUT dispatching,
   through the product's own planner and the leg's own revisions (counsel
   P1-1); ``prepare`` with the model drafter refuses with a bounded route
   state and the purpose in the refusal.  The refusal carries the INVOKE
   RECEIPT (counsel P0): whether a request left, to which host, under which
   kernel operation, with what outcome -- so the face never says
   ``NOTHING SENT`` over a request that was sent.  Nothing is written for a
   refused run, and no deterministic fallback is silently substituted.
6. **Stop stops.**  A prepare carries an attempt id; ``stop`` cancels the
   kernel operation under it and marks the attempt, so a run that completes
   after the owner walked away writes NO draft (counsel P1-4).
"""
from __future__ import annotations

import hashlib
import json
import threading
import time as _time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlparse

from ..principals import Principal
from .errors import ConflictError, NotFound, ServiceError, ValidationError
from .project_update_service import (
    ACCEPTANCE_ACCEPTED,
    ACCEPTANCE_UNREVIEWED,
    ACCEPTANCE_SUPERSEDED,
    KIND_DECISION,
    KIND_INFERENCE,
    KIND_OBSERVATION,
    SUPPORT_SOURCE_LINKED,
    SUPPORT_SUPPORTED,
    SUPPORT_UNKNOWN,
    Claim,
    _extract_structured_json,
    _field_mapping_support,
    _known_names_for_room,
    _resolve_for_capability,
    _typed_unknowns,
)

PREPARATION_BRIEF_CAPABILITY = "project.brief_prepare"

# ── The bounded shape (AC3) ───────────────────────────────────────────

MAX_PRIORITIES = 3
MAX_QUESTIONS = 3
MAX_OBLIGATIONS = 3

SECTION_KEYS: tuple[str, ...] = ("priorities", "questions", "obligations")
SECTION_BOUNDS: dict[str, int] = {
    "priorities": MAX_PRIORITIES,
    "questions": MAX_QUESTIONS,
    "obligations": MAX_OBLIGATIONS,
}
# The caption-step headings the document draws (board P3Brief).
SECTION_HEADINGS: dict[str, str] = {
    "priorities": "DECIDE TODAY",
    "questions": "ASK THEM",
    "obligations": "YOU OWE",
}
# The claim section a superseded citation lands in: a ledger under the
# claims, never a line of the document.
SECTION_SUPERSEDED = "superseded"

GENERATOR_DETERMINISTIC = "deterministic"
GENERATOR_MODEL = "model"

LIFECYCLE_DRAFT = "draft"
LIFECYCLE_KEPT = "kept"
LIFECYCLE_DISCARDED = "discarded"

# ── Source coverage vocabulary (C4) ───────────────────────────────────

STATE_AVAILABLE = "available"
STATE_STALE = "stale"
STATE_FAILED = "failed"
STATE_UNAVAILABLE = "unavailable"

# One failure class, one token, one verb (design D1).
_REPAIRS: dict[str, dict[str, str]] = {
    STATE_STALE: {"token": "STALE", "verb": "Retry", "href": "/"},
    STATE_FAILED: {"token": "CANT CHECK", "verb": "Reconnect", "href": "/settings"},
    "credential": {"token": "CREDENTIAL EXPIRED", "verb": "Reconnect", "href": "/settings"},
    "paused": {"token": "PAUSED", "verb": "Resume", "href": "/"},
    "never_checked": {"token": "NEVER CHECKED", "verb": "Refresh", "href": "/"},
}
_CREDENTIAL_MARKERS = ("401", "403", "unauthorized", "unauthorised", "forbidden", "token", "credential")

# ── Route states (AC5) ────────────────────────────────────────────────

ROUTE_READY = "ready"
ROUTE_NOT_SET = "not_set"
ROUTE_KEY_MISSING = "key_missing"
ROUTE_UNAVAILABLE = "unavailable"
ROUTE_UNREACHABLE = "unreachable"
ROUTE_NO_OUTPUT = "no_output"
ROUTE_UNUSABLE = "unusable_output"
ROUTE_STOPPED = "stopped"

ROUTE_TOKENS: dict[str, str] = {
    ROUTE_READY: "READY",
    ROUTE_NOT_SET: "MODEL NOT SET",
    ROUTE_KEY_MISSING: "KEY NOT SET",
    ROUTE_UNAVAILABLE: "ENGINE UNAVAILABLE",
    ROUTE_UNREACHABLE: "ENDPOINT UNREACHABLE",
    ROUTE_NO_OUTPUT: "NO OUTPUT",
    ROUTE_UNUSABLE: "OUTPUT UNUSABLE",
    ROUTE_STOPPED: "STOPPED",
}

_ON_MACHINE_BOUNDARIES = frozenset({"same_device", "local", ""})


def empty_invoke_receipt() -> dict[str, Any]:
    """No kernel operation exists for the attempt: nothing left the machine."""
    return {"sent": False, "operation_id": "", "outcome": "", "send_phase": "", "host": ""}


class PreparationRefused(ServiceError):
    """The model route cannot draft; the purpose is handed back untouched,
    with the invoke receipt so the face can say what actually happened."""

    def __init__(self, route: dict[str, Any], purpose: str) -> None:
        route = dict(route)
        route.setdefault("invoke", empty_invoke_receipt())
        super().__init__(
            "preparation_refused",
            route.get("reason") or ROUTE_TOKENS.get(route.get("state", ""), "refused"),
            context={"route": route, "purpose": purpose, "status": 409},
        )
        self.route = route
        self.purpose = purpose


# ── The typed outline ─────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class OutlineEntry:
    """One bounded line of the brief: its sentence and the claim behind it."""
    text: str
    span_id: str

    def to_dict(self) -> dict[str, str]:
        return {"text": self.text, "span_id": self.span_id}


@dataclass(frozen=True, slots=True)
class Outline:
    """The bounded shape both drafters produce (AC3)."""
    priorities: list[OutlineEntry] = field(default_factory=list)
    questions: list[OutlineEntry] = field(default_factory=list)
    obligations: list[OutlineEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        for key in SECTION_KEYS:
            entries = getattr(self, key)
            if len(entries) > SECTION_BOUNDS[key]:
                raise ValueError(
                    f"{key} holds {len(entries)} entries; the bound is {SECTION_BOUNDS[key]}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {key: [e.to_dict() for e in getattr(self, key)] for key in SECTION_KEYS}

    def body_md(self) -> str:
        lines: list[str] = []
        for key in SECTION_KEYS:
            entries = getattr(self, key)
            if not entries:
                continue
            lines.append(f"## {SECTION_HEADINGS[key]}")
            for entry in entries:
                lines.append(f"- {entry.text}")
            lines.append("")
        return "\n".join(lines).strip()


def outline_from_dict(raw: dict[str, Any]) -> Outline:
    def entries(key: str) -> list[OutlineEntry]:
        out: list[OutlineEntry] = []
        for item in raw.get(key) or []:
            if isinstance(item, dict) and item.get("text"):
                out.append(OutlineEntry(str(item["text"]), str(item.get("span_id") or "")))
        return out
    return Outline(
        priorities=entries("priorities"),
        questions=entries("questions"),
        obligations=entries("obligations"),
    )


@dataclass(frozen=True, slots=True)
class Draft:
    """What a drafter hands back: the bounded outline, its claims, and the
    items the bound left out -- named, never silently dropped (P1-3)."""
    outline: Outline
    claims: list[Claim]
    not_included: list[dict[str, str]] = field(default_factory=list)


def _left_out(title: str, ref: str, section: str, bound: int, *, order: str = "") -> dict[str, str]:
    why = f"over the bound of {bound} for {SECTION_HEADINGS.get(section, section)}"
    if order:
        why = f"{why} · {order}"
    return {"title": title, "ref": ref, "section": section, "why": why}


# ── Time helpers ──────────────────────────────────────────────────────

def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _short_date(value: Any) -> str:
    parsed = _parse_iso(value)
    return parsed.strftime("%m-%d") if parsed else ""


# ── The manifest (AC2) ────────────────────────────────────────────────

def _source_row(item: dict[str, Any], now: datetime) -> dict[str, Any]:
    """One Room source as a coverage row: the eight persisted fields plus
    what the brief needs to cite it back."""
    state_raw = str(item.get("state") or "")
    checked = item.get("checkedAt")
    next_check = item.get("nextCheckAt")
    reason = item.get("plainReason")
    provider = str(item.get("provider") or "")
    repair: dict[str, str] | None = None
    if state_raw == "cant_check":
        state = STATE_FAILED
        lowered = str(reason or "").lower()
        if any(marker in lowered for marker in _CREDENTIAL_MARKERS):
            # One failure class, one token, one verb (D1): an expired
            # credential is CREDENTIAL EXPIRED · <PROVIDER> with Reconnect.
            repair = dict(_REPAIRS["credential"])
            repair["token"] = f"CREDENTIAL EXPIRED · {provider.upper()}" if provider else repair["token"]
        else:
            repair = dict(_REPAIRS[STATE_FAILED])
        reason = reason or "could not check"
    elif state_raw == "paused":
        state = STATE_UNAVAILABLE
        repair = dict(_REPAIRS["paused"])
        reason = reason or "paused"
    elif not checked:
        state = STATE_UNAVAILABLE
        repair = dict(_REPAIRS["never_checked"])
        reason = reason or "never checked"
    else:
        next_dt = _parse_iso(next_check)
        if next_dt is not None and next_dt < now:
            state = STATE_STALE
            repair = dict(_REPAIRS[STATE_STALE])
            reason = reason or "missed its check"
        else:
            state = STATE_AVAILABLE
    return {
        "source_id": str(item.get("watchId") or ""),
        "kind": provider,
        "label": str(item.get("scope") or provider.upper()),
        "state": state,
        "observed_at": checked,
        "revision": checked or "",
        "reason": reason,
        "repair": repair,
        "tokens": [str(t) for t in (item.get("tokens") or [])],
        "host": str(item.get("host") or ""),
        "watch_ids": [str(w) for w in (item.get("watchIds") or [])],
    }


def build_manifest(room: dict[str, Any], purpose: str, *, now: datetime) -> dict[str, Any]:
    """Freeze exactly what a draft over this Room read.

    ``sources`` carries every source with its state; ``omitted`` names the ones
    not read, each with reason and repair; ``decisions`` carries current AND
    superseded records, lifecycle stated and the successor named;
    ``commitments`` the open ones.  ``not_included`` is filled by the drafter.
    """
    sources: list[dict[str, Any]] = []
    section = room.get("sources") or {}
    if section.get("state") == "ok":
        for item in section.get("items") or []:
            if item.get("suggested"):
                continue
            sources.append(_source_row(item, now))
    sources.sort(key=lambda r: (r["kind"], r["label"]))
    omitted = [row for row in sources if row["state"] != STATE_AVAILABLE]

    decisions: list[dict[str, Any]] = []
    dsection = room.get("decisions") or {}
    if dsection.get("state") == "ok":
        for item in dsection.get("items") or []:
            lifecycle = str(item.get("lifecycle") or "active")
            row = {
                "ref": f"decision_record:{item.get('id')}",
                "text": str(item.get("text") or ""),
                "lifecycle": "superseded" if lifecycle == "superseded" else "current",
                "at": item.get("at"),
                "meeting_title": item.get("meeting_title") or "",
                # HS-200-16: the record's own kind, so a consumer never draws
                # a commitment as a decision (the Room's DECISIONS section
                # holds both -- proposal_bridge_service.py:588-590).
                "kind": str(item.get("kind") or "") or "decision",
            }
            if item.get("successor_id"):
                row["successor_ref"] = f"decision_record:{item['successor_id']}"
            decisions.append(row)

    commitments: list[dict[str, Any]] = []
    csection = room.get("commitments") or {}
    if csection.get("state") == "ok":
        for item in csection.get("items") or []:
            commitments.append({
                "ref": f"commitment:{item.get('id')}",
                "text": str(item.get("text") or ""),
                "owner": item.get("owner"),
                "due_at": item.get("dueAt") or item.get("due_at"),
                "kind": str(item.get("kind") or "") or "action",
            })

    available = sum(1 for row in sources if row["state"] == STATE_AVAILABLE)
    return {
        "project_id": str(room.get("project_id") or ""),
        "project_revision": int(room.get("revision") or 0),
        "purpose": purpose,
        "prepared_at": now.isoformat(),
        "calendar": {"present": False},
        "coverage": {
            "expected": len(sources),
            "available": available,
            "complete": available == len(sources),
        },
        "sources": sources,
        "omitted": omitted,
        "decisions": decisions,
        "commitments": commitments,
        "not_included": [],
    }


def manifest_sha256(manifest_json: str) -> str:
    return hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


# ── The deterministic drafter (the shape authority) ───────────────────

def _needs_you_rows(room: dict[str, Any]) -> list[dict[str, Any]]:
    section = room.get("needsYou") or {}
    if section.get("state") != "ok":
        return []
    order = {"danger": 0, "warning": 1, "info": 2}
    rows = [dict(r) for r in (section.get("items") or [])]
    rows.sort(key=lambda r: (order.get(str(r.get("severity") or ""), 3), str(r.get("title") or "")))
    return rows


def _source_ref_for(row: dict[str, Any], manifest: dict[str, Any]) -> str | None:
    """The manifest source row a needs-you row came from -- matched by the
    Watch id the row carries, never by provider kind (counsel P2 vi)."""
    watch_id = str(row.get("watchId") or row.get("watch_id") or "")
    if not watch_id:
        return None
    for src in manifest["sources"]:
        if src["state"] == STATE_AVAILABLE and (
            src["source_id"] == watch_id or watch_id in src["watch_ids"]
        ):
            return f"source:{src['source_id']}"
    return None


def draft_deterministic(room: dict[str, Any], manifest: dict[str, Any]) -> Draft:
    """Priorities, questions and obligations from the Room's recorded fields.

    Every sentence is a field-mapping claim over the ref it names; nothing is
    invented, the bound is enforced by ``Outline`` itself, and what the bound
    left out is named.  Selection is NEWEST FIRST (the Room's own order) and
    the left-out entries say so.
    """
    version = f"project:{manifest['project_id']}@{manifest['project_revision']}"
    claims: list[Claim] = []
    priorities: list[OutlineEntry] = []
    questions: list[OutlineEntry] = []
    obligations: list[OutlineEntry] = []
    not_included: list[dict[str, str]] = []
    order = "newest first"

    # Priorities: current decisions first (what was decided is what the
    # meeting must honour), then the items that need the owner.
    for decision in manifest["decisions"]:
        if decision["lifecycle"] != "current":
            continue
        if len(priorities) >= MAX_PRIORITIES:
            not_included.append(_left_out(decision["text"], decision["ref"], "priorities", MAX_PRIORITIES, order=order))
            continue
        idx = len(priorities)
        span = f"s_priorities_{idx}"
        text = decision["text"]
        claims.append(Claim(
            span_id=span, text=text, refs=[decision["ref"]], section="priorities",
            kind=KIND_DECISION, support=SUPPORT_SUPPORTED, acceptance=ACCEPTANCE_ACCEPTED,
            support_record=_field_mapping_support(version, [decision["ref"]], ["decision_text", "lifecycle"]),
        ))
        priorities.append(OutlineEntry(text, span))
    for row in _needs_you_rows(room):
        ref = _source_ref_for(row, manifest)
        if ref is None:
            continue
        why = str(row.get("why") or "").strip()
        text = f"{row.get('title')} -- {why}" if why else str(row.get("title") or "")
        if len(priorities) >= MAX_PRIORITIES:
            not_included.append(_left_out(text, ref, "priorities", MAX_PRIORITIES, order=order))
            continue
        idx = len(priorities)
        span = f"s_priorities_{idx}"
        claims.append(Claim(
            span_id=span, text=text, refs=[ref], section="priorities",
            kind=KIND_OBSERVATION, support=SUPPORT_SUPPORTED, acceptance=ACCEPTANCE_UNREVIEWED,
            support_record=_field_mapping_support(version, [ref], ["title", "why", "severity"]),
        ))
        priorities.append(OutlineEntry(text, span))

    # Questions: what the record cannot answer -- an owner-less or undated
    # commitment, and a superseded decision the room may still be acting on.
    for commitment in manifest["commitments"]:
        if not commitment["text"]:
            continue
        if not commitment.get("owner"):
            text = f"Who owns: {commitment['text']}?"
            fields = ["owner"]
        elif not commitment.get("due_at"):
            text = f"When is it due: {commitment['text']}?"
            fields = ["due_at"]
        else:
            continue
        if len(questions) >= MAX_QUESTIONS:
            not_included.append(_left_out(text, commitment["ref"], "questions", MAX_QUESTIONS, order=order))
            continue
        idx = len(questions)
        span = f"s_questions_{idx}"
        claims.append(Claim(
            span_id=span, text=text, refs=[commitment["ref"]], section="questions",
            kind=KIND_INFERENCE, support=SUPPORT_SOURCE_LINKED, acceptance=ACCEPTANCE_UNREVIEWED,
            support_record=_field_mapping_support(version, [commitment["ref"]], fields),
        ))
        questions.append(OutlineEntry(text, span))
    for decision in manifest["decisions"]:
        if decision["lifecycle"] != "superseded":
            continue
        text = f"Superseded -- does anyone still act on: {decision['text']}?"
        if len(questions) >= MAX_QUESTIONS:
            not_included.append(_left_out(text, decision["ref"], "questions", MAX_QUESTIONS, order=order))
            continue
        idx = len(questions)
        span = f"s_questions_{idx}"
        claims.append(Claim(
            span_id=span, text=text, refs=[decision["ref"]], section="questions",
            kind=KIND_DECISION, support=SUPPORT_SUPPORTED, acceptance=ACCEPTANCE_SUPERSEDED,
            support_record=_field_mapping_support(version, [decision["ref"]], ["decision_text", "lifecycle"]),
        ))
        questions.append(OutlineEntry(text, span))

    # Obligations: the open commitments, owner and due date as recorded.
    for commitment in manifest["commitments"]:
        if not commitment["text"]:
            continue
        parts = [commitment["text"]]
        if commitment.get("owner"):
            parts.append(f"owner {commitment['owner']}")
        if commitment.get("due_at"):
            parts.append(f"due {_short_date(commitment['due_at']) or commitment['due_at']}")
        text = " -- ".join(parts)
        if len(obligations) >= MAX_OBLIGATIONS:
            not_included.append(_left_out(text, commitment["ref"], "obligations", MAX_OBLIGATIONS, order=order))
            continue
        idx = len(obligations)
        span = f"s_obligations_{idx}"
        claims.append(Claim(
            span_id=span, text=text, refs=[commitment["ref"]], section="obligations",
            kind=KIND_OBSERVATION, support=SUPPORT_SUPPORTED, acceptance=ACCEPTANCE_UNREVIEWED,
            support_record=_field_mapping_support(version, [commitment["ref"]], ["text", "owner", "due_at"]),
        ))
        obligations.append(OutlineEntry(text, span))

    return Draft(Outline(priorities, questions, obligations), claims, not_included)


# ── The model drafter, constrained to the shape ───────────────────────

_MODEL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        key: {
            "type": "array",
            "maxItems": SECTION_BOUNDS[key],
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "cited_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "cited_refs"],
            },
        }
        for key in SECTION_KEYS
    },
    "required": list(SECTION_KEYS),
}


def build_model_prompt(purpose: str, inventory: list[Claim], manifest: dict[str, Any]) -> dict[str, Any]:
    lines: list[str] = [f"PURPOSE: {purpose}"]
    lines.append("\n[decisions carried in]")
    for decision in manifest["decisions"]:
        lines.append(f"- {decision['ref']} [{decision['lifecycle'].upper()}]: {decision['text']!r}")
    lines.append("\n[evidence inventory]")
    for claim in inventory:
        lines.append(f"- {claim.span_id}: {claim.text!r} | refs: {', '.join(claim.refs)}")
    for src in manifest["sources"]:
        if src["state"] == STATE_AVAILABLE and src["tokens"]:
            lines.append(f"- source:{src['source_id']} ({src['label']}): {' · '.join(src['tokens'])!r} | refs: source:{src['source_id']}")
    system_prompt = (
        "You prepare a meeting brief for its owner.  Using ONLY the inventory "
        "below, write at most "
        f"{MAX_PRIORITIES} priorities to decide, {MAX_QUESTIONS} questions to ask "
        f"and {MAX_OBLIGATIONS} obligations owed.\n\n"
        "RULES:\n"
        "1. Every sentence cites at least one ref from the inventory, using the "
        "EXACT ref strings provided.\n"
        "2. Never invent a name, a date or a number the inventory does not state.  "
        "A sentence you cannot cite gets an empty cited_refs list.\n"
        "3. A superseded decision is never presented as current.\n"
        "4. Short, concrete sentences.  No filler.\n\n"
        "Respond with ONLY a JSON object:\n"
        '{"priorities": [{"text": "...", "cited_refs": ["..."]}], '
        '"questions": [...], "obligations": [...]}'
    )
    return {
        "system_prompt": system_prompt,
        "user_prompt": "\n".join(lines),
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "preparation_brief", "schema": _MODEL_OUTPUT_SCHEMA},
        },
    }


def _normalized(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def parse_model_output(
    raw: str,
    inventory_refs: frozenset[str],
    inventory_texts: dict[str, str],
    inventory_claims: list[Claim] | None = None,
    manifest: dict[str, Any] | None = None,
    known_names: Any = (),
) -> Draft | None:
    """Parse the model's JSON into the bounded outline and its claims.

    The bound is enforced by truncation to the section's cap -- and every
    truncated item is NAMED in ``not_included`` (P1-3).  A sentence with a
    valid ref is ``source_linked`` with typed unknowns for the literals the
    cited source does not carry; a sentence with none is ``unknown`` with no
    refs, which the face draws as ``NO SOURCE`` + ``Find support``.

    A sentence the model returns VERBATIM from the deterministic inventory,
    citing that entry's own ref, is that entry: a recorded decision carried
    into the brief unchanged stays ``DECISION · SUPPORTED · ACCEPTED``.  A
    sentence citing a SUPERSEDED decision is typed ``DECISION · SUPERSEDED``
    with its successor and goes to the superseded ledger, never the outline
    (P1-2).
    """
    parsed = _extract_structured_json(raw)
    if parsed is None or not any(key in parsed for key in SECTION_KEYS):
        return None
    verbatim: dict[tuple[str, str], Claim] = {}
    for inv in inventory_claims or []:
        for ref in inv.refs:
            verbatim[(_normalized(inv.text), ref)] = inv
    superseded_refs: dict[str, dict[str, Any]] = {
        d["ref"]: d for d in ((manifest or {}).get("decisions") or []) if d.get("lifecycle") == "superseded"
    }
    sections: dict[str, list[OutlineEntry]] = {}
    claims: list[Claim] = []
    not_included: list[dict[str, str]] = []
    superseded_count = 0
    for key in SECTION_KEYS:
        entries: list[OutlineEntry] = []
        items = parsed.get(key) or []
        if not isinstance(items, list):
            items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            cited = item.get("cited_refs")
            cited = cited if isinstance(cited, list) else []
            valid = [r for r in cited if isinstance(r, str) and r in inventory_refs]
            stale = next((r for r in valid if r in superseded_refs), None)
            if stale is not None:
                # P1-2: a superseded record is never a line of the document.
                record = superseded_refs[stale]
                successor = str(record.get("successor_ref") or "")
                claims.append(Claim(
                    span_id=f"s_superseded_{superseded_count}", text=text, refs=[stale],
                    section=SECTION_SUPERSEDED, verified=True, kind=KIND_DECISION,
                    support=SUPPORT_SOURCE_LINKED, acceptance=ACCEPTANCE_SUPERSEDED,
                    unknowns=([{"type": "superseded_by", "value": successor}] if successor else []),
                ))
                superseded_count += 1
                continue
            if len(entries) >= SECTION_BOUNDS[key]:
                not_included.append(_left_out(text, valid[0] if valid else "", key, SECTION_BOUNDS[key]))
                continue
            span = f"s_{key}_{len(entries)}"
            carried = next(
                (verbatim[(_normalized(text), r)] for r in valid if (_normalized(text), r) in verbatim),
                None,
            )
            if carried is not None:
                claims.append(Claim(
                    span_id=span, text=carried.text, refs=list(carried.refs), section=key,
                    verified=True, kind=carried.kind, support=carried.support,
                    acceptance=carried.acceptance, support_record=carried.support_record,
                    unknowns=list(carried.unknowns),
                ))
                entries.append(OutlineEntry(carried.text, span))
                continue
            if valid:
                source_text = " ".join([inventory_texts.get(r, "") for r in valid] + valid)
                claims.append(Claim(
                    span_id=span, text=text, refs=valid, section=key, verified=True,
                    kind=KIND_INFERENCE, support=SUPPORT_SOURCE_LINKED,
                    acceptance=ACCEPTANCE_UNREVIEWED,
                    unknowns=_typed_unknowns(text, source_text, known_names),
                ))
            else:
                claims.append(Claim(
                    span_id=span, text=text, refs=[], section=key, verified=False,
                    kind=KIND_INFERENCE, support=SUPPORT_UNKNOWN,
                    acceptance=ACCEPTANCE_UNREVIEWED,
                    unknowns=_typed_unknowns(text, "", known_names),
                ))
            entries.append(OutlineEntry(text, span))
        sections[key] = entries
    outline = Outline(sections["priorities"], sections["questions"], sections["obligations"])
    return Draft(outline, claims, not_included)


# ── The service ───────────────────────────────────────────────────────

class _ModelDraftFailed(Exception):
    def __init__(self, state: str, reason: str, receipt: dict[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.state = state
        self.reason = reason
        self.receipt = receipt or empty_invoke_receipt()


def _host_of(endpoint: str, node: str = "") -> str:
    endpoint = str(endpoint or "").strip()
    if endpoint:
        return urlparse(endpoint).hostname or endpoint
    return str(node or "")


def _invocation_id_for(attempt_id: str) -> str:
    """The kernel invocation id an attempt runs under: bounded, alnum."""
    digest = hashlib.sha256(str(attempt_id).encode("utf-8")).hexdigest()
    return "pbrief" + digest[:26]


class PreparationBriefService:
    """Prepare, keep and re-read a Project's preparation briefs."""

    def __init__(
        self,
        db: Any,
        *,
        project_service: Any,
        broker: Any = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._db = db
        self._projects = project_service
        self._broker = broker
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        # Attempts the owner stopped: a run that completes under one of these
        # writes nothing (P1-4).  Process-local, like the runner's own leases.
        self._stopped: set[str] = set()
        self._live: dict[str, str] = {}  # attempt_id -> invocation_id while a run is out
        self._lock = threading.Lock()

    # ── the route (AC5): reads, never dispatches ─────────────────────

    def route(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """The frozen route the model drafter would use, named without a
        single byte leaving the machine."""
        self._projects.room(principal, project_id)  # 404 on an unknown Project
        return self._route_state()

    def _route_state(self) -> dict[str, Any]:
        """Bounded route state read off the FROZEN ROUTE the product's own
        planner resolves (the Ask path's resolver, `_resolve_for_capability`
        -> `_route_plan_deployment`), then the leg's own revisions: the
        deployment revision for boundary, endpoint and secret slot; the
        model-profile revision for the display label.  No selection of its
        own; the target's readiness (a key that is not set) is read from
        the same slot the runner would read (counsel P1-1)."""
        base = {"state": ROUTE_NOT_SET, "token": ROUTE_TOKENS[ROUTE_NOT_SET],
                "host": "", "model": "", "boundary": "", "reason": "",
                "repair": "Set up model", "invoke": empty_invoke_receipt()}
        broker = self._broker
        if broker is None:
            base["reason"] = "no inference broker"
            return base
        try:
            deployment_id, _assignment_id, route_profile = _resolve_for_capability(
                broker, PREPARATION_BRIEF_CAPABILITY,
            )
        except RuntimeError as exc:
            base["reason"] = str(exc)
            return base
        db = getattr(broker, "database", broker)
        facts = self._deployment_facts(db, deployment_id)
        boundary = facts["boundary"]
        host = _host_of(facts["endpoint"], facts["node"])
        model = self._model_label(db, route_profile, facts["model"])
        state = ROUTE_READY
        reason = ""
        if facts["secret_slot"]:
            if not self._slot_has_key(facts["secret_slot"]):
                state = ROUTE_KEY_MISSING
                reason = f"Destination '{model or route_profile}' needs a key in ${facts['secret_slot']}"
        elif facts["model_path"] and facts["kind"] in ("this_device", "local"):
            from pathlib import Path

            if not Path(facts["model_path"]).expanduser().exists():
                state = ROUTE_UNAVAILABLE
                reason = f"model file not found: {facts['model_path']}"
        on_machine = boundary in _ON_MACHINE_BOUNDARIES and not host
        return {
            "state": state,
            "token": ROUTE_TOKENS[state],
            "host": "THIS DEVICE" if (on_machine or boundary == "same_device") else host,
            "model": model,
            "boundary": boundary,
            "reason": reason,
            "repair": "Set up model",
            "invoke": empty_invoke_receipt(),
        }

    @staticmethod
    def _deployment_facts(db: Any, deployment_id: str) -> dict[str, str]:
        empty = {"engine": "", "model": "", "endpoint": "", "node": "", "boundary": "",
                 "secret_slot": "", "model_path": "", "kind": ""}
        if not deployment_id:
            return empty
        try:
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT engine, model, endpoint, node, boundary, secret_slot, model_path, kind "
                    "FROM deployment_revisions WHERE id = ?",
                    (deployment_id,),
                ).fetchone()
        except Exception:
            return empty
        if row is None:
            return empty
        return {key: str(row[key] or "") for key in empty}

    @staticmethod
    def _model_label(db: Any, profile_id: str, deployment_model: str) -> str:
        """The model's display name: the profile revision's own label and
        model identity, through the Concierge's display helper."""
        from .concierge_service import engine_display_name

        label = ""
        identity = deployment_model
        if profile_id:
            try:
                with db._connection() as conn:
                    row = conn.execute(
                        "SELECT label, model_or_artifact_identity FROM model_profile_revisions "
                        "WHERE profile_id = ? ORDER BY revision DESC LIMIT 1",
                        (profile_id,),
                    ).fetchone()
                if row is not None:
                    label = str(row["label"] or "")
                    identity = str(row["model_or_artifact_identity"] or "") or identity
            except Exception:
                pass
        if not label and not identity:
            return ""
        display, quant = engine_display_name(profile_name=label or identity, profile_model=identity)
        name = f"{display} {quant}".strip() if quant else display
        return name.upper()

    @staticmethod
    def _slot_has_key(slot: str) -> bool:
        from ..profile_key_store import ProfileKeyStoreError, resolve_profile_key

        try:
            return bool(resolve_profile_key(slot))
        except ProfileKeyStoreError:
            return False
        except Exception:
            return False

    def preview_manifest(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """The manifest a prepare WOULD bind right now -- the coverage the
        face shows BEFORE the run, from the same builder, with no write."""
        room = self._projects.room(principal, project_id)
        return build_manifest(room, "", now=self._clock())

    # ── stop (P1-4) ──────────────────────────────────────────────────

    def stop(self, attempt_id: str) -> dict[str, Any]:
        """Cancel the kernel operation the attempt runs under and mark the
        attempt so a run that still completes writes no draft."""
        attempt_id = str(attempt_id or "").strip()
        if not attempt_id:
            raise ValidationError("attempt_id is required", code="attempt_required")
        disposition = "not_running"
        with self._lock:
            self._stopped.add(attempt_id)
            invocation_id = self._live.get(attempt_id)
        if invocation_id and self._broker is not None:
            runner = getattr(self._broker, "inference_runner", None)
            cancel = getattr(runner, "cancel", None)
            if callable(cancel):
                try:
                    result = cancel(invocation_id)
                    disposition = str(result if isinstance(result, str) else "requested")
                except Exception as exc:  # the mark still holds: nothing is written
                    disposition = f"cancel_failed: {exc}"
        return {"attempt_id": attempt_id, "stopped": True, "disposition": disposition}

    def _was_stopped(self, attempt_id: str) -> bool:
        with self._lock:
            return attempt_id in self._stopped

    # ── prepare ──────────────────────────────────────────────────────

    def prepare(
        self,
        principal: Principal,
        project_id: str,
        purpose: str,
        *,
        generator: str = GENERATOR_MODEL,
        attempt_id: str = "",
    ) -> dict[str, Any]:
        purpose = str(purpose or "").strip()
        if not purpose:
            raise ValidationError("purpose is required", code="purpose_required")
        if generator not in (GENERATOR_MODEL, GENERATOR_DETERMINISTIC):
            raise ValidationError(
                f"generator must be '{GENERATOR_MODEL}' or '{GENERATOR_DETERMINISTIC}'",
                code="generator_invalid",
            )
        attempt_id = str(attempt_id or "").strip()
        if attempt_id and (len(attempt_id) > 64 or not attempt_id.replace("-", "").replace("_", "").isalnum()):
            raise ValidationError("attempt_id is invalid", code="attempt_invalid")
        room = self._projects.room(principal, project_id)
        now = self._clock()
        manifest = build_manifest(room, purpose, now=now)
        draft = draft_deterministic(room, manifest)
        gen_label = GENERATOR_DETERMINISTIC
        gen_host: str | None = None
        gen_model: str | None = None
        started = _time.monotonic()
        if generator == GENERATOR_MODEL:
            route = self._route_state()
            if route["state"] != ROUTE_READY:
                # Nothing has been sent; the purpose goes back with the reason.
                raise PreparationRefused(route, purpose)
            try:
                draft, gen_label, gen_host, gen_model = self._draft_with_model(
                    principal, purpose, draft.claims, manifest, route,
                    known_names=_known_names_for_room(room), attempt_id=attempt_id,
                )
            except _ModelDraftFailed as exc:
                refused = dict(route)
                refused.update({
                    "state": exc.state,
                    "token": ROUTE_TOKENS.get(exc.state, exc.state.upper()),
                    "reason": exc.reason,
                    "invoke": exc.receipt,
                })
                raise PreparationRefused(refused, purpose) from exc
        if attempt_id and self._was_stopped(attempt_id):
            # The owner walked away while the request was out: no orphan draft.
            refused = {"state": ROUTE_STOPPED, "token": ROUTE_TOKENS[ROUTE_STOPPED],
                       "host": "", "model": "", "boundary": "", "reason": "stopped by the owner",
                       "repair": "", "invoke": empty_invoke_receipt()}
            raise PreparationRefused(refused, purpose)
        elapsed_ms = int((_time.monotonic() - started) * 1000)

        manifest["not_included"] = list(draft.not_included)
        manifest_json = _canonical(manifest)
        brief_id = "pbrief_" + hashlib.sha256(
            f"{project_id}|{purpose}|{now.isoformat()}|{_time.time_ns()}".encode()
        ).hexdigest()[:24]
        claims_json = json.dumps([c.to_dict() for c in draft.claims], sort_keys=True, separators=(",", ":"))
        with self._db._connection() as conn:
            conn.execute(
                """INSERT INTO project_briefs
                   (id, project_id, project_revision, purpose, lifecycle,
                    manifest_revision, manifest_json, manifest_sha256,
                    outline_json, body_md, claims_json,
                    generator, generator_host, generator_model, elapsed_ms,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    brief_id, project_id, manifest["project_revision"], purpose,
                    LIFECYCLE_DRAFT, manifest_json, manifest_sha256(manifest_json),
                    _canonical(draft.outline.to_dict()), draft.outline.body_md(), claims_json,
                    gen_label, gen_host, gen_model, elapsed_ms,
                    now.isoformat(), now.isoformat(),
                ),
            )
        return self.get_brief(principal, brief_id)

    def _draft_with_model(
        self,
        principal: Principal,
        purpose: str,
        inventory: list[Claim],
        manifest: dict[str, Any],
        route: dict[str, Any],
        *,
        known_names: Any = (),
        attempt_id: str = "",
    ) -> tuple[Draft, str, str | None, str | None]:
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.prompt_adapter import CanonicalPromptAdapter
        from ..kernel.runtime import _as_principal

        broker = self._broker
        try:
            deployment_id, assignment_id, _route_profile = _resolve_for_capability(
                broker, PREPARATION_BRIEF_CAPABILITY,
            )
        except RuntimeError as exc:
            raise _ModelDraftFailed(ROUTE_NOT_SET, str(exc)) from exc

        inventory_refs: set[str] = set()
        inventory_texts: dict[str, str] = {}
        for claim in inventory:
            for ref in claim.refs:
                inventory_refs.add(ref)
                prior = inventory_texts.get(ref, "")
                inventory_texts[ref] = f"{prior} {claim.text}".strip()
        for decision in manifest["decisions"]:
            inventory_refs.add(decision["ref"])
            inventory_texts[decision["ref"]] = decision["text"]
        for commitment in manifest["commitments"]:
            inventory_refs.add(commitment["ref"])
            inventory_texts[commitment["ref"]] = " ".join(
                str(v) for v in (commitment["text"], commitment.get("owner"), commitment.get("due_at")) if v
            )
        for src in manifest["sources"]:
            if src["state"] == STATE_AVAILABLE:
                ref = f"source:{src['source_id']}"
                inventory_refs.add(ref)
                inventory_texts[ref] = " ".join([src["label"], *src["tokens"]])

        payload = build_model_prompt(purpose, inventory, manifest)
        invocation_id = _invocation_id_for(attempt_id) if attempt_id else ""
        request = InvocationRequest(
            deployment_revision=deployment_id,
            definition_origin=ServiceContract.for_payload("project.brief.prepare", "1", payload),
            deadline_at=_time.time() + 120,
            payload=payload,
            invocation_id=invocation_id,
        )
        captured: list[Any] = []

        def _capture(value: Any) -> str:
            captured.append(value)
            return f"brief-prepare:{assignment_id}"

        host = str(route.get("host") or "")
        if attempt_id:
            with self._lock:
                self._live[attempt_id] = invocation_id
        try:
            with _as_principal(principal):
                outcome = broker.inference_runner.invoke(
                    request, CanonicalPromptAdapter(), publish=_capture,
                )
        except Exception as exc:
            raise _ModelDraftFailed(ROUTE_UNREACHABLE, str(exc)) from exc
        finally:
            if attempt_id:
                with self._lock:
                    self._live.pop(attempt_id, None)

        # The invoke receipt (P0): a kernel operation exists for this attempt
        # whenever the runner admitted it, and then a request LEFT unless the
        # kernel refused before dispatch.  The face draws the target's egress
        # from this, never from the absence of a result.
        operation_id = str(getattr(outcome, "operation_id", "") or "")
        outcome_state = str(getattr(outcome, "outcome", "") or "")
        send_phase = str(getattr(outcome, "send_phase", "") or "")
        sent = bool(operation_id) and outcome_state != "refused"
        receipt = {"sent": sent, "operation_id": operation_id, "outcome": outcome_state,
                   "send_phase": send_phase, "host": host if sent else ""}

        if attempt_id and self._was_stopped(attempt_id):
            raise _ModelDraftFailed(ROUTE_STOPPED, "stopped by the owner", receipt)
        raw: str | None = None
        result = getattr(outcome, "result", None)
        if isinstance(result, dict) and "output" in result:
            raw = str(result["output"])
        elif captured and isinstance(captured[0], dict) and "output" in captured[0]:
            raw = str(captured[0]["output"])
        if raw is None:
            # The kernel runner returns a physical failure as an OUTCOME with
            # the destination's own error, not as an exception: name it as the
            # route failure it is, in the engine's words (ruling B5).
            outcome_error = str(getattr(outcome, "error", "") or "")
            if outcome_state == "cancelled":
                raise _ModelDraftFailed(ROUTE_STOPPED, outcome_error or "stopped", receipt)
            if outcome_error or (outcome_state and outcome_state != "succeeded"):
                raise _ModelDraftFailed(ROUTE_UNREACHABLE, outcome_error or outcome_state, receipt)
            raise _ModelDraftFailed(ROUTE_NO_OUTPUT, "the model returned nothing", receipt)
        parsed = parse_model_output(
            raw, frozenset(inventory_refs), inventory_texts, inventory, manifest, known_names,
        )
        if parsed is None:
            raise _ModelDraftFailed(ROUTE_UNUSABLE, "the model output could not be read as a brief", receipt)
        return parsed, f"model:{assignment_id}", host or None, route.get("model") or None

    # ── read / list / keep / discard ─────────────────────────────────

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        manifest_json = str(row["manifest_json"] or "{}")
        stored_sha = str(row["manifest_sha256"] or "")
        live_sha = manifest_sha256(manifest_json)
        manifest = json.loads(manifest_json)
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "project_revision": row["project_revision"],
            "purpose": row["purpose"],
            "lifecycle": row["lifecycle"],
            "manifest_revision": row["manifest_revision"],
            "manifest": manifest,
            "manifest_sha256": stored_sha,
            # The freeze, re-verified on EVERY read (ruling R3): a manifest that
            # no longer hashes to what was kept is named, never smoothed over.
            "integrity": "verified" if stored_sha == live_sha else "mismatch",
            "outline": json.loads(str(row["outline_json"] or "{}")),
            "body_md": row["body_md"],
            "claims_json": row["claims_json"],
            "generator": row["generator"],
            "generator_host": row["generator_host"],
            "generator_model": row["generator_model"],
            "elapsed_ms": row["elapsed_ms"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "kept_at": row["kept_at"],
        }

    def get_brief(self, principal: Principal, brief_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM project_briefs WHERE id = ?", (brief_id,)).fetchone()
        if row is None:
            raise NotFound("brief", brief_id)
        return self._row_to_dict(row)

    def list_briefs(
        self, principal: Principal, project_id: str, *, lifecycle: str | None = None, limit: int = 20,
    ) -> list[dict[str, Any]]:
        self._projects.room(principal, project_id)
        bounded = max(1, min(int(limit), 100))
        with self._db._connection() as conn:
            if lifecycle:
                rows = conn.execute(
                    """SELECT * FROM project_briefs WHERE project_id = ? AND lifecycle = ?
                       ORDER BY created_at DESC, id DESC LIMIT ?""",
                    (project_id, lifecycle, bounded),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM project_briefs WHERE project_id = ? AND lifecycle != ?
                       ORDER BY created_at DESC, id DESC LIMIT ?""",
                    (project_id, LIFECYCLE_DISCARDED, bounded),
                ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def keep(self, principal: Principal, brief_id: str) -> dict[str, Any]:
        """Keep is a lifecycle flip on the SAME row: the manifest the draft
        froze is the manifest the kept brief carries (ruling R3)."""
        current = self.get_brief(principal, brief_id)
        if current["lifecycle"] == LIFECYCLE_KEPT:
            return current
        if current["lifecycle"] == LIFECYCLE_DISCARDED:
            raise ConflictError("a discarded brief cannot be kept", code="brief_discarded")
        if current["integrity"] != "verified":
            raise ConflictError(
                "the manifest no longer matches its freeze", code="manifest_mismatch",
            )
        now = self._clock().isoformat()
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE project_briefs SET lifecycle = ?, kept_at = ?, updated_at = ? WHERE id = ?",
                (LIFECYCLE_KEPT, now, now, brief_id),
            )
        return self.get_brief(principal, brief_id)

    def discard(self, principal: Principal, brief_id: str) -> dict[str, Any]:
        current = self.get_brief(principal, brief_id)
        if current["lifecycle"] == LIFECYCLE_KEPT:
            raise ConflictError("a kept brief is not discarded", code="brief_kept")
        now = self._clock().isoformat()
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE project_briefs SET lifecycle = ?, updated_at = ? WHERE id = ?",
                (LIFECYCLE_DISCARDED, now, brief_id),
            )
        return self.get_brief(principal, brief_id)


__all__ = [
    "Draft",
    "MAX_OBLIGATIONS",
    "MAX_PRIORITIES",
    "MAX_QUESTIONS",
    "PREPARATION_BRIEF_CAPABILITY",
    "ROUTE_KEY_MISSING",
    "ROUTE_NOT_SET",
    "ROUTE_READY",
    "ROUTE_STOPPED",
    "ROUTE_TOKENS",
    "ROUTE_UNAVAILABLE",
    "ROUTE_UNREACHABLE",
    "Outline",
    "OutlineEntry",
    "PreparationBriefService",
    "PreparationRefused",
    "SECTION_SUPERSEDED",
    "STATE_AVAILABLE",
    "STATE_FAILED",
    "STATE_STALE",
    "STATE_UNAVAILABLE",
    "build_manifest",
    "build_model_prompt",
    "draft_deterministic",
    "empty_invoke_receipt",
    "manifest_sha256",
    "outline_from_dict",
    "parse_model_output",
]
