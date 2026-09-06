"""Shared grounding hydration (HS-87-04).

One hydration truth for ask and steer: `hydrate_refs` loads canonical
references into raw `(kind, title, subtitle, text)` blocks; each consumer
formats them its own way (ask's `[MEETING: …]` headers, the steer's
`--- from … ---` fences). Project references select their bounded member
set by memory relevance when a query is present, or by labeled recency when
it is not, and expand as individually citable source blocks.
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


def _memory_repo(db: object):
    """The relationship-aware index, when this handle carries one.

    A database handle opened before the memory indexes existed (and the
    narrow doubles some callers pass) has no ``memory`` repository. Recall
    is an enrichment, never a precondition: without the repository the pass
    is a no-op and the caller keeps the evidence it already resolved.
    """

    return getattr(db, "memory", None)


# The steer's own budget (HS-87-04): a hydrated steer must fit what a
# TUI agent can take in one paste. Shown in the composer; over-cap
# refuses at compose time.
STEER_CONTEXT_CAP_BYTES = 8_000


@dataclass(frozen=True)
class GroundingBlock:
    """One hydrated reference, before any consumer's formatting."""

    kind: str  # meeting | artifact | decision | note | container kind
    ref: str
    title: str
    subtitle: str  # meeting day, or an artifact's parent-meeting title ("" if none)
    text: str


@dataclass(frozen=True)
class GroundingHydrationResult:
    """Additive selection receipt for bounded grounding hydration."""

    blocks: list[GroundingBlock]
    unknown: list[str]
    selection: str
    matched_count: int
    overflow_count: int

    @property
    def source_refs(self) -> list[str]:
        return [f"{block.kind}:{block.ref}" for block in self.blocks]


def meeting_digest(state: Any) -> str:
    """A meeting's summary-level material: intel summary + action items when
    intel exists, else the opening segments (mirrors the iPad's routableText)."""
    parts: list[str] = []
    if state.intel is not None and state.intel.summary:
        parts.append(state.intel.summary)
        items = state.intel.to_dict().get("action_items") or []
        tasks = [
            str(i.get("task") or i.get("text") or "")
            for i in items
            if isinstance(i, dict)
        ]
        tasks = [t for t in tasks if t]
        if tasks:
            parts.append("\n".join(f"- {t}" for t in tasks))
    else:
        parts.append("\n".join(f"{s.speaker}: {s.text}" for s in state.segments[:40]))
    return "\n\n".join(p for p in parts if p)


def hydrate_refs_detailed(
    db: Any,
    meeting_ids: list[str],
    artifact_ids: list[str],
    expand: str,
    qualified_refs: Optional[list[str]] = None,
    *,
    query: Optional[str] = None,
    include_memory: bool = False,
    exclude_refs: Optional[list[str]] = None,
) -> GroundingHydrationResult:
    """Load refs with an honest receipt for selection and bounded overflow."""
    blocks: list[GroundingBlock] = []
    unknown: list[str] = []
    stats: dict[str, Any] = {
        "selection": "explicit",
        "matched_count": 0,
        "overflow_count": 0,
    }
    visited: set[str] = set()
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
            GroundingBlock(
                kind="meeting", ref=mid, title=title, subtitle=day, text=text
            )
        )
        visited.add(f"meeting:{mid}")
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
            GroundingBlock(
                kind="artifact", ref=aid, title=title, subtitle=of, text=body
            )
        )
        visited.add(f"artifact:{aid}")
    # HS-92-05: the same qualified resolver serves Ask, steer, Web, and native.
    # Containers resolve their real current members recursively; any stale leaf
    # makes the whole request unknown so callers can refuse rather than pretend.
    for raw_ref in qualified_refs or []:
        try:
            ref = qualified_ref(raw_ref)
        except ValueError:
            unknown.append(str(raw_ref))
            continue
        more, missing = _hydrate_qualified(
            db, ref, expand, visited, query=query, stats=stats
        )
        blocks.extend(more)
        unknown.extend(missing)

    # Model-bearing consumers opt into the same retrieval pass even when the
    # user did not manually attach a Project or source.  Project refs already
    # perform a scoped search in ``_hydrate_qualified``; a second global pass
    # would both duplicate evidence and escape that scope.
    has_project_ref = any(
        str(raw_ref).strip().lower().startswith("project:")
        for raw_ref in qualified_refs or []
    )
    has_explicit_sources = bool(meeting_ids or artifact_ids or qualified_refs)
    memory = _memory_repo(db)
    if (
        include_memory
        and memory is not None
        and query
        and str(query).strip()
        and not has_project_ref
        and not has_explicit_sources
    ):
        excluded = {
            str(ref).split("#", 1)[0]
            for ref in (exclude_refs or [])
            if str(ref).strip()
        }
        search = memory.search(
            str(query),
            limit=GROUNDING_MAX_REFS + len(excluded),
            exclude_refs=excluded,
        )
        members = [hit.source_ref for hit in search.hits][:GROUNDING_MAX_REFS]
        more, missing = _hydrate_members(
            db, members, expand, visited, query=query, stats=stats
        )
        blocks.extend(more)
        unknown.extend(missing)
        stats["selection"] = "ecosystem_relevance"
        stats["overflow_count"] = int(stats["overflow_count"]) + max(
            0, search.total - len(members)
        )
    # Expanded containers still obey the original global 16-ref context cap.
    # Count every project-search/container miss plus any cross-container excess;
    # only then cut, so the receipt always says exactly how many matched sources
    # the bounded prompt had to leave out.
    overflow = int(stats["overflow_count"])
    matched = len(blocks) + overflow
    if len(blocks) > GROUNDING_MAX_REFS:
        overflow += len(blocks) - GROUNDING_MAX_REFS
        blocks = blocks[:GROUNDING_MAX_REFS]
    return GroundingHydrationResult(
        blocks=blocks,
        unknown=unknown,
        selection=str(stats["selection"]),
        matched_count=matched,
        overflow_count=overflow,
    )


def hydrate_refs(
    db: Any,
    meeting_ids: list[str],
    artifact_ids: list[str],
    expand: str,
    qualified_refs: Optional[list[str]] = None,
    *,
    query: Optional[str] = None,
    include_memory: bool = False,
    exclude_refs: Optional[list[str]] = None,
) -> tuple[list[GroundingBlock], list[str]]:
    """Compatibility tuple over :func:`hydrate_refs_detailed`."""
    result = hydrate_refs_detailed(
        db,
        meeting_ids,
        artifact_ids,
        expand,
        qualified_refs=qualified_refs,
        query=query,
        include_memory=include_memory,
        exclude_refs=exclude_refs,
    )
    return result.blocks, result.unknown


def _hydrate_qualified(
    db: Any,
    ref: str,
    expand: str,
    visited: set[str],
    *,
    query: Optional[str] = None,
    stats: Optional[dict[str, Any]] = None,
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
            if full
            else meeting_digest(state)
        )
        if len(text) > GROUNDING_TRANSCRIPT_CAP:
            text = text[:GROUNDING_TRANSCRIPT_CAP] + "\n[content cut at grounding cap]"
        return [
            GroundingBlock(kind, resource_id, state.title or resource_id, day, text)
        ], []
    if kind == "artifact":
        try:
            art = db.plugins.get_artifact(resource_id)
        except Exception:
            art = None
        if art is None:
            return [], [ref]
        return [
            GroundingBlock(
                kind,
                resource_id,
                art.title or resource_id,
                "",
                str(art.body_markdown or ""),
            )
        ], []
    if kind == "note":
        note = db.notes.get(resource_id)
        if note is None:
            return [], [ref]
        return [
            GroundingBlock(
                kind, resource_id, note.title or resource_id, "", note.body_markdown
            )
        ], []
    if kind == "decision":
        decision = db.decisions.get(resource_id)
        if decision is None:
            return [], [ref]
        rationale = f"\n\nRationale: {decision.rationale}" if decision.rationale else ""
        return [
            GroundingBlock(
                kind,
                resource_id,
                decision.text,
                decision.decided_at,
                decision.text + rationale,
            )
        ], []
    if kind in {
        "decision_record",
        "desk_decision",
        "action",
        "project_item",
        "workbench_item",
        "cadence",
    }:
        queries = {
            "decision_record": (
                "SELECT decision_text title,COALESCE(rationale,'')||CASE WHEN alternatives IS NULL OR alternatives='' THEN '' ELSE '\n\nAlternatives: '||alternatives END text,updated_at subtitle FROM decision_records WHERE id=? AND deleted=0"
            ),
            "desk_decision": (
                "SELECT CASE WHEN title='' THEN decision_markdown ELSE title END title,context_markdown||CASE WHEN decision_markdown='' THEN '' ELSE '\n\nDecision: '||decision_markdown END||CASE WHEN consequences_markdown='' THEN '' ELSE '\n\nConsequences: '||consequences_markdown END text,status subtitle FROM desk_decisions WHERE id=? AND deleted=0"
            ),
            "action": (
                "SELECT task title,task||CASE WHEN owner IS NULL OR owner='' THEN '' ELSE '\nOwner: '||owner END||CASE WHEN due IS NULL OR due='' THEN '' ELSE '\nDue: '||due END text,status subtitle FROM action_items WHERE id=?"
            ),
            "project_item": (
                "SELECT title,COALESCE(summary,'')||CASE WHEN details_json IS NULL OR details_json='' THEN '' ELSE '\n\nDetails: '||details_json END text,item_type||' · '||lifecycle subtitle FROM project_items WHERE id=?"
            ),
            "workbench_item": (
                "SELECT title,body||CASE WHEN result IS NULL OR result='' THEN '' ELSE '\n\nResult: '||result END text,status subtitle FROM workbench_items WHERE id=? AND status!='dismissed'"
            ),
            "cadence": (
                "SELECT title,summary||CASE WHEN owner IS NULL OR owner='' THEN '' ELSE '\nOwner: '||owner END text,status||' · '||priority subtitle FROM cadence_loops WHERE id=? AND status!='killed'"
            ),
        }
        with db._connection() as conn:
            row = conn.execute(queries[kind], (resource_id,)).fetchone()
        if row is None:
            return [], [ref]
        text = str(row["text"] or "")
        if len(text) > GROUNDING_TRANSCRIPT_CAP:
            text = text[:GROUNDING_TRANSCRIPT_CAP] + "\n[content cut at grounding cap]"
        return [
            GroundingBlock(
                kind,
                resource_id,
                str(row["title"] or resource_id),
                str(row["subtitle"] or ""),
                text,
            )
        ], []
    if kind == "thread":
        # Search identifies the best matching message as ``thread:id#message``;
        # grounding returns the coherent parent conversation.
        thread_id = resource_id.split("#", 1)[0]
        thread = db.threads.get(thread_id)
        if thread is None or thread.deleted_at is not None:
            return [], [ref]
        lines: list[str] = []
        for message in db.threads.list_path(thread_id):
            text = "\n".join(
                str(part.text)
                for part in db.threads.get_parts(message.id)
                if part.kind == "text"
                and part.text
                and not part.sensitive
                and not part.draft
            ).strip()
            if text:
                lines.append(f"{message.role}: {text}")
        body = "\n\n".join(lines)
        if len(body) > GROUNDING_TRANSCRIPT_CAP:
            body = body[:GROUNDING_TRANSCRIPT_CAP] + "\n[content cut at grounding cap]"
        return [
            GroundingBlock(
                kind,
                thread_id,
                thread.title or thread_id,
                "conversation",
                body,
            )
        ], []
    if kind == "knowledge":
        kb = db.kbs.get(resource_id)
        if kb is None:
            return [], [ref]
        members = [
            row.resource_ref
            for row in db.knowledge_memberships.list_for_knowledge(resource_id)
        ]
        if not members:
            members = [value for value in kb.member_ids if ":" in value]
        return _hydrate_container(
            db,
            kind,
            resource_id,
            kb.name,
            members,
            expand,
            visited,
            query=query,
            stats=stats,
        )
    if kind == "zone":
        zone = db.directories.get(resource_id)
        if zone is None:
            return [], [ref]
        members = [
            row.primitive_id
            for row in db.directory_memberships.list_for_directory(resource_id)
        ]
        return _hydrate_container(
            db,
            kind,
            resource_id,
            zone.name,
            members,
            expand,
            visited,
            query=query,
            stats=stats,
        )
    if kind == "project":
        project = db.projects.get_project(resource_id)
        if project is None:
            return [], [ref]
        memory = _memory_repo(db)
        # No index on this handle: fall through to the relationship listing
        # below, which is the honest recency answer rather than an error.
        if memory is not None and query and str(query).strip():
            search = memory.search(
                str(query),
                project_id=resource_id,
                limit=GROUNDING_MAX_REFS,
            )
            members = [hit.source_ref for hit in search.hits]
            if stats is not None:
                stats["selection"] = "relevance"
                stats["matched_count"] = int(stats["matched_count"]) + search.total
                stats["overflow_count"] = int(stats["overflow_count"]) + max(
                    0, search.total - len(members)
                )
        else:
            all_members = [
                row.resource_ref
                for row in db.project_relationships.list_for_project(resource_id)
            ]
            members = all_members[:GROUNDING_MAX_REFS]
            if stats is not None:
                stats["selection"] = "recency_fallback"
                stats["matched_count"] = int(stats["matched_count"]) + len(all_members)
                stats["overflow_count"] = int(stats["overflow_count"]) + max(
                    0, len(all_members) - len(members)
                )
        # A project expands to its selected source blocks. It is not flattened into
        # one anonymous container, so every model-visible block keeps a citable ref.
        return _hydrate_members(db, members, expand, visited, query=query, stats=stats)
    return [], [ref]


def _hydrate_members(
    db: Any,
    members: list[str],
    expand: str,
    visited: set[str],
    *,
    query: Optional[str] = None,
    stats: Optional[dict[str, Any]] = None,
) -> tuple[list[GroundingBlock], list[str]]:
    children: list[GroundingBlock] = []
    unknown: list[str] = []
    for member in members[:GROUNDING_MAX_REFS]:
        try:
            canonical = qualified_ref(member)
        except ValueError:
            unknown.append(member)
            continue
        blocks, missing = _hydrate_qualified(
            db, canonical, expand, visited, query=query, stats=stats
        )
        children.extend(blocks)
        unknown.extend(missing)
    return children, unknown


def _hydrate_container(
    db: Any,
    kind: str,
    resource_id: str,
    title: str,
    members: list[str],
    expand: str,
    visited: set[str],
    *,
    query: Optional[str] = None,
    stats: Optional[dict[str, Any]] = None,
) -> tuple[list[GroundingBlock], list[str]]:
    children, unknown = _hydrate_members(
        db, members, expand, visited, query=query, stats=stats
    )
    text = "\n\n".join(
        f"[{block.kind.upper()}: {block.title}]\n{block.text}" for block in children
    )
    container = GroundingBlock(
        kind, resource_id, title or resource_id, f"{len(members)} member(s)", text
    )
    return [container], unknown


def hydrate_grounding_blocks_detailed(
    db: Any,
    meeting_ids: list[str],
    artifact_ids: list[str],
    expand: str,
    qualified_refs: Optional[list[str]] = None,
    *,
    query: Optional[str] = None,
    include_memory: bool = False,
    exclude_refs: Optional[list[str]] = None,
) -> tuple[list[str], list[str], list[str], GroundingHydrationResult]:
    """Ask formatting plus the additive selection/overflow receipt."""
    result = hydrate_refs_detailed(
        db,
        meeting_ids,
        artifact_ids,
        expand,
        qualified_refs=qualified_refs,
        query=query,
        include_memory=include_memory,
        exclude_refs=exclude_refs,
    )
    out_blocks: list[str] = []
    ids: list[str] = []
    titles: list[str] = []
    for block in result.blocks:
        label = block.kind.upper()
        header = (
            f"[{label}: {block.title} — {block.subtitle}]"
            if block.subtitle
            else f"[{label}: {block.title}]"
        )
        ref_line = f"[REF: {block.kind}:{block.ref}]"
        out_blocks.append(
            f"{header}\n{ref_line}\n{block.text}"
            if block.text
            else f"{header}\n{ref_line}"
        )
        ids.append(block.ref)
        titles.append(block.title)
    return out_blocks, ids, titles, result


def hydrate_grounding_blocks(
    db: Any,
    meeting_ids: list[str],
    artifact_ids: list[str],
    expand: str,
    qualified_refs: Optional[list[str]] = None,
    *,
    query: Optional[str] = None,
    include_memory: bool = False,
    exclude_refs: Optional[list[str]] = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Compatibility tuple preserving the pre-HS-109-04 result shape."""
    blocks, ids, titles, result = hydrate_grounding_blocks_detailed(
        db,
        meeting_ids,
        artifact_ids,
        expand,
        qualified_refs=qualified_refs,
        query=query,
        include_memory=include_memory,
        exclude_refs=exclude_refs,
    )
    return blocks, ids, titles, result.unknown


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
        fences.append(
            f"{header}\n[ref: {b.kind}:{b.ref}]\n{b.text}\n--- end {b.kind} ---"
        )
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
        w for w in _WORD_RE.findall(text.lower()) if len(w) > 2 and w not in _STOPWORDS
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
        out.append(
            {
                "text": claim,
                "score": round(score, 3),
                "label": label,
                "flagged": label != "entailed",
            }
        )
    return out


__all__ = [
    "GROUNDING_EXPANDS",
    "GROUNDING_MAX_REFS",
    "GROUNDING_TRANSCRIPT_CAP",
    "STEER_CONTEXT_CAP_BYTES",
    "ENTAILMENT_ENTAILED_THRESHOLD",
    "ENTAILMENT_PARTIAL_THRESHOLD",
    "GroundingBlock",
    "GroundingHydrationResult",
    "classify_support",
    "compose_steer",
    "decompose_claims",
    "entailment_score",
    "hydrate_grounding_blocks",
    "hydrate_grounding_blocks_detailed",
    "hydrate_refs",
    "hydrate_refs_detailed",
    "meeting_digest",
    "score_claims",
]
