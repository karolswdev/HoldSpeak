"""The ambient dw observer (HS-88-03).

A local model keeps a running journal of what the rails do — story
flips, gate refusals, evidence captures, phase closes. The observer is
READ-ONLY and OFF BY DEFAULT: it consumes a bounded `dw events` tail
(the `missioncontrol_bridge` posture, a receipt) plus the one bus's
frames, summarizes each batch of NEW events on a RuntimeProfile the
owner chose, and writes ONE thing — a journal note tagged
`rails-journal`. It never writes to the rails; anything it would DO is
a proposal through the actuator flow.

This module is the pure core (event diffing, batch summary, journal
body). The hub loop that drives it lives in `web_server`; the model
call is injected so tests need no LLM.
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable, Optional

JOURNAL_TAG = "rails-journal"

_SYSTEM_PROMPT = (
    "You keep a terse running journal of a software delivery pipeline. "
    "Given a batch of raw rail events (story status flips, commit-gate "
    "passes and refusals, evidence captures, phase closes), write two or "
    "three plain sentences noting what changed and anything worth a "
    "human's attention. State only what the events say; invent nothing."
)

# A summarize function: takes (system_prompt, user_prompt) → summary text.
SummarizeFn = Callable[[str, str], str]


def event_signature(event: dict[str, Any]) -> str:
    """A stable id for one rail event, for diffing what is NEW. Uses the
    event's own fields (ts + verb + story + a detail digest) — the raw
    event, never re-derived state."""
    key = "|".join(
        str(event.get(k, "")) for k in ("ts", "event", "story", "repo")
    )
    detail = event.get("detail")
    if detail is not None:
        key += "|" + hashlib.sha256(
            repr(sorted(detail.items()) if isinstance(detail, dict) else detail).encode()
        ).hexdigest()[:12]
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def new_events(
    events: list[dict[str, Any]], seen: set[str]
) -> tuple[list[dict[str, Any]], set[str]]:
    """The events whose signature the observer has not journaled, plus
    the updated seen-set. Order preserved (oldest first if the caller
    passes them so)."""
    fresh: list[dict[str, Any]] = []
    updated = set(seen)
    for e in events:
        sig = event_signature(e)
        if sig in updated:
            continue
        updated.add(sig)
        fresh.append(e)
    return fresh, updated


def format_events_for_model(events: list[dict[str, Any]]) -> str:
    """A compact, faithful rendering of the batch for the summarizer —
    the events' own fields, one per line, no interpretation."""
    lines: list[str] = []
    for e in events:
        parts = [
            str(e.get("ts") or ""),
            str(e.get("repo") or ""),
            str(e.get("event") or ""),
            str(e.get("story") or ""),
        ]
        detail = e.get("detail")
        if isinstance(detail, dict) and detail:
            parts.append(
                " ".join(f"{k}={v}" for k, v in detail.items() if v not in (None, ""))
            )
        lines.append("  ".join(p for p in parts if p))
    return "\n".join(lines)


def summarize_batch(
    events: list[dict[str, Any]], *, summarize_fn: Optional[SummarizeFn]
) -> dict[str, Any]:
    """One journal batch: the events + a model summary. When the model
    is unavailable (no fn, or it raises), degrade to an event-only
    entry — a typed absence, never a fabricated summary."""
    rendered = format_events_for_model(events)
    if summarize_fn is None:
        return {"events": events, "summary": "", "degraded": True}
    try:
        summary = summarize_fn(_SYSTEM_PROMPT, rendered).strip()
    except Exception:
        return {"events": events, "summary": "", "degraded": True}
    return {"events": events, "summary": summary, "degraded": not summary}


def journal_body(batch: dict[str, Any]) -> str:
    """The journal note's markdown: a provenance line, the events named
    (receipts), then the model's summary (or an honest degraded note)."""
    events = batch.get("events") or []
    n = len(events)
    header = f"> {n} rail event{'s' if n != 1 else ''} observed"
    listing = "\n".join(f"- {line}" for line in format_events_for_model(events).splitlines())
    if batch.get("degraded"):
        tail = "_(summary unavailable — the local model did not answer; events recorded verbatim)_"
    else:
        tail = str(batch.get("summary") or "")
    return f"{header}\n\n{listing}\n\n{tail}".rstrip()


def record_journal_entry(db: Any, batch: dict[str, Any], *, title: str) -> Any:
    """Write the batch as a journal note (the deferred-decision default:
    a note tagged `rails-journal`, openable and groundable like any
    primitive). The ONLY write the observer makes — never to the rails."""
    from .web.routes.primitives._shared import _new_id

    return db.notes.upsert(
        note_id=_new_id("note"),
        title=title,
        body_markdown=journal_body(batch),
        tags=[JOURNAL_TAG],
    )


def list_journal(db: Any, *, limit: int = 50) -> list[Any]:
    """The journal entries, newest first — notes carrying the tag."""
    rows = [
        n for n in db.notes.list(limit=500) if JOURNAL_TAG in (getattr(n, "tags", None) or [])
    ]
    return rows[:limit]


def build_profile_summarizer(profile_id: str = "") -> SummarizeFn:
    """Production summarizer: run the prompt on the named RuntimeProfile
    (else the hub default), through the SAME intel seam ask uses. Kept
    out of the pure core so tests inject a fake instead."""

    def summarize(system_prompt: str, user_prompt: str) -> str:
        from .db import get_database

        prof = None
        if profile_id:
            prof = get_database().profiles.get(profile_id)
        if prof is not None and not prof.deleted:
            from .intel.providers import build_meeting_intel_for_profile

            intel = build_meeting_intel_for_profile(
                kind=prof.kind, base_url=prof.base_url, model=prof.model,
                profile_id=prof.id, node=getattr(prof, "node", ""),
            )
        else:
            from .intel.providers import build_configured_meeting_intel

            intel = build_configured_meeting_intel()
        return intel.run_prompt(
            system_prompt=system_prompt, user_prompt=user_prompt,
            temperature=0.2, max_tokens=220,
        )

    return summarize


__all__ = [
    "JOURNAL_TAG",
    "SummarizeFn",
    "build_profile_summarizer",
    "event_signature",
    "format_events_for_model",
    "journal_body",
    "list_journal",
    "new_events",
    "record_journal_entry",
    "summarize_batch",
]
