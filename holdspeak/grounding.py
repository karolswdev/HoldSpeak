"""Shared grounding hydration (HS-87-04).

One hydration truth for ask and steer: `hydrate_refs` loads meeting
and artifact references from the canonical store into raw
`(kind, title, subtitle, text)` blocks; each consumer formats them
its own way (ask's `[MEETING: …]` headers, the steer's `--- from … ---`
fences). Factored verbatim from the Phase-83 ask route — its behavior
is byte-identical, its tests pass unmodified (the Phase-63 move
discipline).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal, Optional

from .db.relationships import qualified_ref

from .logging_config import get_logger

log = get_logger("grounding")

# HSM-15-12 / Phase-83 caps, now shared.
GROUNDING_MAX_REFS = 16
GROUNDING_TRANSCRIPT_CAP = 12_000
GROUNDING_EXPANDS = ("summary", "full")

# The steer's own budget (HS-87-04): a hydrated steer must fit what a
# TUI agent can take in one paste. Shown in the composer; over-cap
# refuses at compose time.
STEER_CONTEXT_CAP_BYTES = 8_000


@dataclass(frozen=True)
class GroundingBlock:
    """One hydrated reference, before any consumer's formatting."""

    kind: str  # "meeting" | "artifact"
    ref: str
    title: str
    subtitle: str  # meeting day, or an artifact's parent-meeting title ("" if none)
    text: str


def meeting_digest(state: Any) -> str:
    """A meeting's summary-level material: intel summary + action items when
    intel exists, else the opening segments (mirrors the iPad's routableText)."""
    parts: list[str] = []
    if state.intel is not None and state.intel.summary:
        parts.append(state.intel.summary)
        items = state.intel.to_dict().get("action_items") or []
        tasks = [str(i.get("task") or i.get("text") or "") for i in items if isinstance(i, dict)]
        tasks = [t for t in tasks if t]
        if tasks:
            parts.append("\n".join(f"- {t}" for t in tasks))
    else:
        parts.append("\n".join(f"{s.speaker}: {s.text}" for s in state.segments[:40]))
    return "\n\n".join(p for p in parts if p)


def hydrate_refs(
    db: Any,
    meeting_ids: list[str],
    artifact_ids: list[str],
    expand: str,
    qualified_refs: Optional[list[str]] = None,
) -> tuple[list[GroundingBlock], list[str]]:
    """Load the referenced meetings/artifacts into raw blocks.

    Returns `(blocks, unknown_ids)`. An id the hub does not hold is
    returned as unknown (the caller refuses loudly; grounding is never
    a best-effort claim). This is the ONE hydration path — ask and
    steer both read here.
    """
    blocks: list[GroundingBlock] = []
    unknown: list[str] = []
    for mid in meeting_ids:
        try:
            state = db.meetings.get_meeting(mid)
        except Exception:
            state = None
        if state is None:
            unknown.append(mid)
            continue
        title = state.title or mid
        day = ""
        try:
            day = state.started_at.date().isoformat()
        except Exception:
            day = ""
        if expand == "full" and state.segments:
            text = "\n".join(f"{s.speaker}: {s.text}" for s in state.segments)
            if len(text) > GROUNDING_TRANSCRIPT_CAP:
                text = (
                    text[:GROUNDING_TRANSCRIPT_CAP]
                    + f"\n[transcript cut at {GROUNDING_TRANSCRIPT_CAP} chars]"
                )
        else:
            text = meeting_digest(state)
        blocks.append(
            GroundingBlock(kind="meeting", ref=mid, title=title, subtitle=day, text=text)
        )
    for aid in artifact_ids:
        try:
            art = db.plugins.get_artifact(aid)
        except Exception:
            art = None
        if art is None:
            unknown.append(aid)
            continue
        of = ""
        if art.meeting_id:
            try:
                parent = db.meetings.get_meeting(art.meeting_id)
                of = (parent.title or "") if parent is not None else ""
            except Exception:
                of = ""
        title = art.title or aid
        body = str(art.body_markdown or "")
        blocks.append(
            GroundingBlock(kind="artifact", ref=aid, title=title, subtitle=of, text=body)
        )
    # HS-92-05: the same qualified resolver serves Ask, steer, Web, and native.
    # Containers resolve their real current members recursively; any stale leaf
    # makes the whole request unknown so callers can refuse rather than pretend.
    visited: set[str] = set()
    for raw_ref in qualified_refs or []:
        try:
            ref = qualified_ref(raw_ref)
        except ValueError:
            unknown.append(str(raw_ref))
            continue
        more, missing = _hydrate_qualified(db, ref, expand, visited)
        blocks.extend(more)
        unknown.extend(missing)
    return blocks, unknown


def _hydrate_qualified(
    db: Any, ref: str, expand: str, visited: set[str]
) -> tuple[list[GroundingBlock], list[str]]:
    if ref in visited:
        return [], []
    visited.add(ref)
    kind, resource_id = ref.split(":", 1)
    if kind in {"meeting", "transcript"}:
        try:
            state = db.meetings.get_meeting(resource_id)
        except Exception:
            state = None
        if state is None:
            return [], [ref]
        day = ""
        try:
            day = state.started_at.date().isoformat()
        except Exception:
            pass
        full = kind == "transcript" or expand == "full"
        text = (
            "\n".join(f"{s.speaker}: {s.text}" for s in state.segments)
            if full else meeting_digest(state)
        )
        if len(text) > GROUNDING_TRANSCRIPT_CAP:
            text = text[:GROUNDING_TRANSCRIPT_CAP] + "\n[content cut at grounding cap]"
        return [GroundingBlock(kind, resource_id, state.title or resource_id, day, text)], []
    if kind == "artifact":
        try:
            art = db.plugins.get_artifact(resource_id)
        except Exception:
            art = None
        if art is None:
            return [], [ref]
        return [GroundingBlock(kind, resource_id, art.title or resource_id, "", str(art.body_markdown or ""))], []
    if kind == "note":
        note = db.notes.get(resource_id)
        if note is None:
            return [], [ref]
        return [GroundingBlock(kind, resource_id, note.title or resource_id, "", note.body_markdown)], []
    if kind == "knowledge":
        kb = db.kbs.get(resource_id)
        if kb is None:
            return [], [ref]
        members = [row.resource_ref for row in db.knowledge_memberships.list_for_knowledge(resource_id)]
        if not members:
            members = [value for value in kb.member_ids if ":" in value]
        return _hydrate_container(db, kind, resource_id, kb.name, members, expand, visited)
    if kind == "zone":
        zone = db.directories.get(resource_id)
        if zone is None:
            return [], [ref]
        members = [row.primitive_id for row in db.directory_memberships.list_for_directory(resource_id)]
        return _hydrate_container(db, kind, resource_id, zone.name, members, expand, visited)
    if kind == "project":
        project = db.projects.get_project(resource_id)
        if project is None:
            return [], [ref]
        members = [row.resource_ref for row in db.project_relationships.list_for_project(resource_id)]
        return _hydrate_container(db, kind, resource_id, project.name, members, expand, visited)
    return [], [ref]


def _hydrate_container(
    db: Any, kind: str, resource_id: str, title: str, members: list[str],
    expand: str, visited: set[str],
) -> tuple[list[GroundingBlock], list[str]]:
    children: list[GroundingBlock] = []
    unknown: list[str] = []
    for member in members[:GROUNDING_MAX_REFS]:
        try:
            canonical = qualified_ref(member)
        except ValueError:
            unknown.append(member)
            continue
        blocks, missing = _hydrate_qualified(db, canonical, expand, visited)
        children.extend(blocks)
        unknown.extend(missing)
    text = "\n\n".join(
        f"[{block.kind.upper()}: {block.title}]\n{block.text}" for block in children
    )
    container = GroundingBlock(kind, resource_id, title or resource_id,
                               f"{len(members)} member(s)", text)
    return [container], unknown


def hydrate_grounding_blocks(
    db: Any, meeting_ids: list[str], artifact_ids: list[str], expand: str,
    qualified_refs: Optional[list[str]] = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Ask's formatting: `(blocks, ids, titles, unknown_ids)` with the
    `[MEETING: …]` / `[ARTIFACT: …]` headers baked in. A thin format
    over `hydrate_refs` — byte-identical to the pre-factoring helper."""
    hydrated, unknown = hydrate_refs(
        db, meeting_ids, artifact_ids, expand, qualified_refs=qualified_refs
    )
    out_blocks: list[str] = []
    ids: list[str] = []
    titles: list[str] = []
    for b in hydrated:
        label = b.kind.upper()
        header = (
            f"[{label}: {b.title} — {b.subtitle}]"
            if b.subtitle
            else f"[{label}: {b.title}]"
        )
        out_blocks.append(f"{header}\n{b.text}" if b.text else header)
        ids.append(b.ref)
        titles.append(b.title)
    return out_blocks, ids, titles, unknown


def compose_steer(
    message: str,
    blocks: list[GroundingBlock],
    *,
    cap_bytes: int = STEER_CONTEXT_CAP_BYTES,
) -> dict[str, Any]:
    """Compose the final steer: the message, then per-object fenced
    blocks with one-line provenance headers, then a count line.

    Returns `{status, text, context_bytes, cap_bytes, refs}`; status
    is `over_cap` (with the size named) when the hydrated context
    exceeds the cap — executed == previewed, so the refusal is at
    compose time, not a silent terminal truncation.
    """
    refs = [f"{b.kind}:{b.ref}" for b in blocks]
    if not blocks:
        return {
            "status": "ok",
            "text": message,
            "context_bytes": 0,
            "cap_bytes": cap_bytes,
            "refs": refs,
        }
    fences: list[str] = []
    for b in blocks:
        subtitle = f" ({b.subtitle})" if b.subtitle else ""
        header = f'--- from {b.kind}: "{b.title}"{subtitle} ---'
        fences.append(f"{header}\n{b.text}\n--- end {b.kind} ---")
    context = "\n\n".join(fences)
    context_bytes = len(context.encode("utf-8"))
    if context_bytes > cap_bytes:
        return {
            "status": "over_cap",
            "context_bytes": context_bytes,
            "cap_bytes": cap_bytes,
            "refs": refs,
        }
    count = len(blocks)
    tail = f"({count} object{'s' if count != 1 else ''} grounded)"
    text = f"{message}\n\n{context}\n\n{tail}"
    return {
        "status": "ok",
        "text": text,
        "context_bytes": context_bytes,
        "cap_bytes": cap_bytes,
        "refs": refs,
    }


# HS-103-03 — grounding VERIFICATION: a citation today asserts provenance
# ("this came from somewhere"); this adds support ("is this actually backed
# by what it cites"). Adapted from researchmind's claim_decomposition.py +
# citation_entailment.py pattern (carry the IDEA, not the code — this repo's
# greenfield posture favors a from-scratch reimplementation over vendoring a
# different stack's file): a dependency-free lexical token-overlap scorer, no
# model call, no network egress. A quiet SIGNAL only — never a hard verdict,
# never blocks or mutates the generated content (a lexical checker false-flags
# legitimate paraphrase too often to assert "this is wrong").
_STOPWORDS = frozenset(
    """
    a an the this that these those is are was were be been being do does did
    have has had having will would shall should may might must can could
    of in on at to for with by from as and or but not no nor so yet
    it its it's he she they them his her their our your my we you i
    there here what which who whom when where why how all any both each
    few more most other some such only own same than too very just
    """.split()
)
_WORD_RE = re.compile(r"[a-z0-9]+")

# Two named thresholds (expect to revisit once real usage data exists):
# ENTAILED — most of the claim's content words appear in the source; PARTIAL —
# roughly a third to two-thirds do (a legitimate paraphrase lands here, not in
# UNSUPPORTED); below PARTIAL, too little of the claim traces to the source to
# call it grounded.
ENTAILMENT_ENTAILED_THRESHOLD = 0.6
ENTAILMENT_PARTIAL_THRESHOLD = 0.3

SupportLabel = Literal["entailed", "partial", "unsupported"]


def _content_tokens(text: str) -> set[str]:
    return {
        w for w in _WORD_RE.findall(text.lower())
        if len(w) > 2 and w not in _STOPWORDS
    }


def entailment_score(claim: str, source_text: str) -> float:
    """How much of `claim`'s content is traceable to `source_text`, as the
    fraction of the claim's significant (non-stopword) tokens that also
    appear in the source. Pure, deterministic, no I/O — a claim with no
    content tokens (too short/trivial to assess) scores 1.0 (never flagged);
    a non-empty claim against an empty source scores 0.0."""
    claim_tokens = _content_tokens(claim)
    if not claim_tokens:
        return 1.0
    source_tokens = _content_tokens(source_text)
    if not source_tokens:
        return 0.0
    return len(claim_tokens & source_tokens) / len(claim_tokens)


def classify_support(score: float) -> SupportLabel:
    if score >= ENTAILMENT_ENTAILED_THRESHOLD:
        return "entailed"
    if score >= ENTAILMENT_PARTIAL_THRESHOLD:
        return "partial"
    return "unsupported"


def decompose_claims(text: str) -> list[str]:
    """Split generated text into atomic claim candidates: one per non-empty
    line (bullets and short paragraphs alike), markdown markers stripped,
    headers and fragments too short to assess dropped."""
    claims: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", raw_line.strip())
        if not line or line.startswith("#") or len(line) < 8:
            continue
        claims.append(line)
    return claims


def score_claims(text: str, source_text: str) -> list[dict[str, Any]]:
    """Decompose `text` into claims and score each against `source_text`.
    Additive metadata only — never mutates `text` itself. A soft signal:
    only `unsupported`/`partial` claims are worth a quiet UI flag; `entailed`
    is not (see `classify_support`)."""
    out: list[dict[str, Any]] = []
    for claim in decompose_claims(text):
        score = entailment_score(claim, source_text)
        label = classify_support(score)
        out.append({
            "text": claim,
            "score": round(score, 3),
            "label": label,
            "flagged": label != "entailed",
        })
    return out


__all__ = [
    "GROUNDING_EXPANDS",
    "GROUNDING_MAX_REFS",
    "GROUNDING_TRANSCRIPT_CAP",
    "STEER_CONTEXT_CAP_BYTES",
    "ENTAILMENT_ENTAILED_THRESHOLD",
    "ENTAILMENT_PARTIAL_THRESHOLD",
    "GroundingBlock",
    "classify_support",
    "compose_steer",
    "decompose_claims",
    "entailment_score",
    "hydrate_grounding_blocks",
    "hydrate_refs",
    "meeting_digest",
    "score_claims",
]
