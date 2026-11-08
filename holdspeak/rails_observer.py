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
import threading
import time
from typing import Any, Callable, Optional

JOURNAL_TAG = "rails-journal"
_EGRESS_BOUNDARY_RANK = {"local": 0, "mesh": 1, "private_network": 2, "cloud": 3}

# HS-88-04: a remote node whose last envelope is older than this reads
# stale — its buffered stream stops, never fabricated (the Phase-85
# liveness posture).
REMOTE_LIVENESS_SECONDS = 90

# Reject events that would smuggle a repo file body across the wire —
# the reach is EVENTS only. Any of these keys means a body is riding.
_BODY_KEYS = {"text", "body", "body_markdown", "content", "file", "contents"}

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
    event's own fields (ts + verb + story + repo + origin) — the raw
    event, never re-derived state."""
    key = "|".join(
        str(event.get(k, "")) for k in ("ts", "event", "story", "repo", "origin_node")
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
        origin = str(e.get("origin_node") or "")
        parts = [
            str(e.get("ts") or ""),
            (f"@{origin}" if origin else "") + str(e.get("repo") or ""),
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
    batch_sha = "sha256:" + hashlib.sha256(rendered.encode()).hexdigest()
    if summarize_fn is None:
        return {
            "events": events,
            "summary": "",
            "degraded": True,
            "event_batch_sha256": batch_sha,
        }
    try:
        summary = summarize_fn(_SYSTEM_PROMPT, rendered).strip()
    except RailsSummaryUnavailable as exc:
        return {
            "events": events,
            "summary": "",
            "degraded": True,
            "event_batch_sha256": batch_sha,
            "route_receipt_id": exc.receipt_id,
        }
    except Exception:
        return {"events": events, "summary": "", "degraded": True, "event_batch_sha256": batch_sha}
    result = {
        "events": events,
        "summary": summary,
        "degraded": not summary,
        "event_batch_sha256": batch_sha,
    }
    receipt_id = str(getattr(summarize_fn, "last_receipt_id", "") or "")
    if receipt_id:
        result["route_receipt_id"] = receipt_id
    egress = str(getattr(summarize_fn, "last_egress", "") or "")
    if egress:
        result["egress"] = egress
    return result


def journal_body(batch: dict[str, Any]) -> str:
    """The journal note's markdown: a provenance line, the events named
    (receipts), then the model's summary (or an honest degraded note)."""
    events = batch.get("events") or []
    n = len(events)
    header = f"> {n} rail event{'s' if n != 1 else ''} observed"
    listing = "\n".join(f"- {line}" for line in format_events_for_model(events).splitlines())
    receipt = str(batch.get("route_receipt_id") or "").strip()
    reference = f"\n\n_(route receipt: {receipt})_" if receipt else ""
    egress = str(batch.get("egress") or "").strip()
    # One frozen route batch has one widest boundary.  Carry it as one compact,
    # visible badge rather than narrating privacy policy into the journal.
    badge = f"\n\n[egress: {egress}]" if egress in _EGRESS_BOUNDARY_RANK else ""
    if batch.get("degraded"):
        tail = "_(summary unavailable — the local model did not answer; events recorded verbatim)_"
    else:
        tail = str(batch.get("summary") or "")
    return f"{header}{badge}\n\n{listing}\n\n{tail}{reference}".rstrip()


def record_journal_entry(db: Any, batch: dict[str, Any], *, title: str) -> Any:
    """Write the batch as a journal note (the deferred-decision default:
    a note tagged `rails-journal`, openable and groundable like any
    primitive). The ONLY write the observer makes — never to the rails."""
    batch_sha = str(batch.get("event_batch_sha256") or "")
    if not batch_sha.startswith("sha256:") or len(batch_sha) != 71:
        batch_sha = "sha256:" + hashlib.sha256(
            format_events_for_model(list(batch.get("events") or [])).encode()
        ).hexdigest()
    # The batch hash is the observer's durable materializer identity. A process
    # restart replays this one note rather than a second note or provider call.
    note = db.notes.upsert(
        note_id="rails-journal-" + batch_sha.removeprefix("sha256:")[:32],
        title=title,
        body_markdown=journal_body(batch),
        tags=[JOURNAL_TAG],
    )
    # HS-200-45 R4: a repository-level note write (the observer's durable
    # materializer); announce it through the composition root's bus.
    from holdspeak.runtime.composition import notify_desk_changed
    notify_desk_changed("note", note.id, "create")
    return note


def list_journal(db: Any, *, limit: int = 50) -> list[Any]:
    """The journal entries, newest first — notes carrying the tag."""
    rows = [
        n for n in db.notes.list(limit=500) if JOURNAL_TAG in (getattr(n, "tags", None) or [])
    ]
    return rows[:limit]


# --- Cross-machine reach (HS-88-04): remote event envelopes ---------------
#
# A far node's worker tails its OWN `dw events` and pushes envelopes to
# the hub; the observer merges them, each event stamped with its origin
# node. The reach is EVENTS only (no repo file bodies cross the wire),
# and honest liveness: a node gone quiet has its stream dropped, never
# fabricated. The buffer is in-memory (a restart clears it, like the
# grant store) — the pull-worker precedent, inverted to a push.

_REMOTE: dict[str, dict[str, Any]] = {}
_REMOTE_LOCK = threading.Lock()


def validate_remote_envelope(envelope: Any) -> tuple[bool, str]:
    """`{node, ts, events: [dict]}`, events-only. (ok, reason)."""
    if not isinstance(envelope, dict):
        return False, "envelope must be an object"
    node = str(envelope.get("node") or "").strip()
    if not node:
        return False, "envelope must name its origin node"
    events = envelope.get("events")
    if not isinstance(events, list):
        return False, "envelope events must be a list"
    for e in events:
        if not isinstance(e, dict):
            return False, "each event must be an object"
        if _BODY_KEYS & set(e.keys()):
            return False, "events carry no file bodies (the reach is events only)"
    return True, ""


def push_remote_envelope(
    envelope: dict[str, Any], *, clock: Callable[[], float] = time.monotonic
) -> tuple[bool, str]:
    """Accept a remote node's envelope into the merge buffer, stamping
    each event with its origin node. (accepted, reason)."""
    ok, reason = validate_remote_envelope(envelope)
    if not ok:
        return False, reason
    node = str(envelope["node"]).strip()
    stamped = [{**e, "origin_node": node} for e in envelope["events"]]
    with _REMOTE_LOCK:
        entry = _REMOTE.get(node, {"events": []})
        entry["last_seen"] = clock()
        entry["events"] = list(entry.get("events", [])) + stamped
        _REMOTE[node] = entry
    return True, ""


def drain_remote_events(
    *, clock: Callable[[], float] = time.monotonic
) -> list[dict[str, Any]]:
    """Return + clear buffered events from LIVE remote nodes; a node past
    the liveness window has its stream DROPPED (stale, never fabricated)."""
    now = clock()
    out: list[dict[str, Any]] = []
    with _REMOTE_LOCK:
        for node in list(_REMOTE):
            entry = _REMOTE[node]
            if now - entry.get("last_seen", 0) > REMOTE_LIVENESS_SECONDS:
                del _REMOTE[node]
                continue
            out.extend(entry.get("events", []))
            entry["events"] = []
    return out


def remote_node_liveness(
    *, clock: Callable[[], float] = time.monotonic
) -> dict[str, bool]:
    """`{node: is_live}` for every remote node the hub has heard from."""
    now = clock()
    with _REMOTE_LOCK:
        return {
            node: (now - entry.get("last_seen", 0)) <= REMOTE_LIVENESS_SECONDS
            for node, entry in _REMOTE.items()
        }


def clear_remote_buffer() -> None:
    """Test seam. A real restart clears the buffer by construction."""
    with _REMOTE_LOCK:
        _REMOTE.clear()


class RailsSummaryUnavailable(RuntimeError):
    """A routed Rails disposition that must become an event-only journal."""

    def __init__(self, reason: str, receipt_id: str = "") -> None:
        super().__init__(reason)
        self.receipt_id = receipt_id


def build_profile_summarizer(
    *, db: Any = None, broker: Any = None, principal: Any = None
) -> SummarizeFn:
    """Return the Rails batch summarizer: one job on the engine assigned to
    ``background.rails_summary``, through the engine door.

    ``last_receipt_id`` names the runner's kernel operation for the batch
    (the journal's route receipt); ``last_egress`` is the engine's lamp word.
    """
    from .kernel.runtime import _service
    from .principals import PrincipalKind
    from .services import engine_door

    if principal is None or principal.kind is not PrincipalKind.SERVICE:
        raise RuntimeError("rails_observer_principal_required")
    db = db or __import__("holdspeak.db", fromlist=["get_database"]).get_database()
    broker = broker or _service()

    def summarize(system_prompt: str, user_prompt: str) -> str:
        from .services.memory_grounding import memory_for

        summarize.last_receipt_id = ""
        summarize.last_egress = ""
        batch_sha = "sha256:" + hashlib.sha256(user_prompt.encode()).hexdigest()
        try:
            engine = engine_door.engine_for(broker, RAILS_SUMMARY_JOB)
        except engine_door.EngineDoorError as exc:
            raise RailsSummaryUnavailable("rails_summary_no_engine") from exc
        payload = engine_door.with_memory(
            broker, engine,
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "temperature": 0.2,
                "max_tokens": 220,
                "event_batch_sha256": batch_sha,
            },
            lambda: memory_for(RAILS_SUMMARY_JOB, db, query=user_prompt[:2000]),
            reserved_output_tokens=220,
        )
        try:
            answer = engine_door.run(
                broker, principal, RAILS_SUMMARY_JOB, payload, engine=engine,
                result_ref="rails-summary:" + batch_sha.removeprefix("sha256:"),
            )
        except engine_door.EngineDoorError as exc:
            summarize.last_receipt_id = exc.operation_id
            raise RailsSummaryUnavailable(
                "rails_summary_" + (exc.outcome or exc.code), exc.operation_id
            ) from exc
        summarize.last_receipt_id = answer.operation_id
        summarize.last_egress = engine_door.egress_of(broker, engine)
        _record_local_readiness(broker, principal, engine)
        return answer.output

    summarize.last_receipt_id = ""  # type: ignore[attr-defined]
    summarize.last_egress = ""  # type: ignore[attr-defined]
    return summarize


RAILS_SUMMARY_JOB = "background.rails_summary"


def _record_local_readiness(broker: Any, principal: Any, engine: Any) -> None:
    """A migrated local Rails engine reads ready after its first answer."""
    adoption = getattr(broker, "inference_adoption_service", None)
    if adoption is None:
        return
    try:
        adoption.record_local_rails_readiness_after_load(principal, deployment_revision_id=engine.revision)
    except Exception:  # no binding (a cloud or legacy engine): nothing to record
        pass


__all__ = [
    "JOURNAL_TAG",
    "REMOTE_LIVENESS_SECONDS",
    "SummarizeFn",
    "build_profile_summarizer",
    "clear_remote_buffer",
    "drain_remote_events",
    "event_signature",
    "format_events_for_model",
    "journal_body",
    "list_journal",
    "new_events",
    "push_remote_envelope",
    "record_journal_entry",
    "remote_node_liveness",
    "summarize_batch",
    "validate_remote_envelope",
]
