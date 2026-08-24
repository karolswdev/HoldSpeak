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
    return db.notes.upsert(
        note_id="rails-journal-" + batch_sha.removeprefix("sha256:")[:32],
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


def _canonical_sha256(value: Any) -> str:
    import json

    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def build_profile_summarizer(profile_id: Optional[str] = None, *, db: Any = None,
                             broker: Any = None, principal: Any = None,
                             observer_config_source_sha256: str | None = None) -> SummarizeFn:
    """Return the routed, frozen Rails batch summarizer.

    ``profile_id`` is migration-era source evidence only.  It is deliberately
    never resolved by this call: a SERVICE route can use only its exact
    capability assignment.  The event rendering is hashed before admission;
    prompts are staged only below the frozen route member.
    """
    from .kernel.runtime import _service
    from .principals import PrincipalKind
    from .services.errors import ValidationError
    from .services.inference_parent_route_bundle_service import InferenceParentRouteBundleService
    from .services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
    from .kernel.prompt_adapter import CanonicalPromptAdapter
    from .services.inference_semantic_adapters import adapter_for_frozen_definition

    if principal is None or principal.kind is not PrincipalKind.SERVICE:
        raise RuntimeError("rails_observer_principal_required")
    db = db or __import__("holdspeak.db", fromlist=["get_database"]).get_database()
    broker = broker or _service()
    adoption = broker.inference_adoption_service
    bundles = InferenceParentRouteBundleService(broker, adoption)
    config_sha = observer_config_source_sha256 or _canonical_sha256(
        {"profile_id": str(profile_id or "this_machine")}
    )

    def summarize(system_prompt: str, user_prompt: str) -> str:
        # ``user_prompt`` is exactly ``format_events_for_model``.  Its digest is
        # the replay boundary; neither config nor a profile is consulted below.
        batch_sha = "sha256:" + hashlib.sha256(user_prompt.encode()).hexdigest()
        command_id = "rails-batch:" + batch_sha.removeprefix("sha256:")
        input_snapshot = {
            "event_batch_sha256": batch_sha,
            "event_count": len(user_prompt.splitlines()) if user_prompt else 0,
            "observer_config_source_sha256": config_sha,
        }
        # The batch identity is replayable across process restarts; a wall-clock
        # admission deadline would make the same batch command conflict. The
        # controller still closes every elected batch, so this is only a durable
        # identity fence, not a standing dispatch lease.
        deadline = 4_102_444_800.0  # 2100-01-01 UTC
        try:
            started = bundles.start(
                principal,
                command_id=command_id,
                parent_kind="rails.observer-batch",
                definition_ref="rails-observer:journal-batch",
                definition_revision="2",
                input_snapshot=input_snapshot,
                deadline_at=deadline,
                routes=(
                    {
                        "key": "rails-summary",
                        "capability_id": "background.rails_summary",
                        "invocation_id": command_id,
                    },
                ),
            )
        except ValidationError as exc:
            refusal = bundles.record_pre_route_refusal(
                principal,
                command_id=command_id,
                parent_kind="rails.observer-batch",
                definition_ref="rails-observer:journal-batch",
                definition_revision="2",
                input_snapshot=input_snapshot,
                deadline_at=deadline,
                reason=exc.code,
            )
            raise RailsSummaryUnavailable(exc.code, str(refusal["receipt"].get("receipt_id") or "")) from exc

        parent = started["parent"]
        member = next(
            (item for item in started["bundle"]["members"] if item["key"] == "rails-summary"),
            None,
        )
        if not isinstance(member, dict) or not str(member.get("route_plan_id") or ""):
            receipt = broker.parent_run_controller.close(
                parent.context,
                "refused",
                "rails-summary:frozen-member-missing",
                principal=principal,
            )
            raise RailsSummaryUnavailable("inference_rails_frozen_member_missing", str(receipt.get("receipt_id") or ""))
        payload = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": 0.2,
            "max_tokens": 220,
            "event_batch_sha256": batch_sha,
        }
        operation_id = "rails-summary:" + batch_sha.removeprefix("sha256:")
        try:
            admitted = adoption.admit_on_frozen_route(
                principal,
                command_id="admit:" + command_id,
                route_plan_id=str(member["route_plan_id"]),
                capability_id="background.rails_summary",
                operation_id=operation_id,
                payload=payload,
                reserved_output_tokens=220,
                parent_operation_id=parent.operation_id,
            )
            route = adoption.plans.get_route_plan(
                ROUTE_PLANNING_AUTHORITY, str(member["route_plan_id"])
            )
            boundaries = [str(item.get("boundary") or "") for item in route.get("entries", ())]
            rank = {"local": 0, "mesh": 1, "private_network": 2, "cloud": 3}
            if not boundaries or any(boundary not in rank for boundary in boundaries):
                raise RuntimeError("inference_rails_frozen_route_boundary_invalid")
            frozen_egress = max(boundaries, key=lambda boundary: rank[boundary])
            definition = adoption._frozen_capability_definition(str(member["route_plan_id"]))

            routed = adoption.execute(
                principal,
                execution_id=str(admitted["execution"]["id"]),
                adapter=adapter_for_frozen_definition(definition, CanonicalPromptAdapter().dispatch),
                parent_context=parent.context,
            )
        except Exception as exc:
            # Admission failures after a valid parent/bundle still need its one
            # parent terminal disposition, but never manufacture a child result.
            receipt = broker.parent_run_controller.close(
                parent.context, "refused", "rails-summary:admission-failed", principal=principal
            )
            raise RailsSummaryUnavailable("rails_summary_unavailable", str(receipt.get("receipt_id") or "")) from exc
        outcome = str(routed.get("outcome") or "indeterminate")
        # A known route failure is not dispatch uncertainty.  Keep every known
        # controller terminal outcome at the SERVICE parent; only a genuinely
        # indeterminate route remains indeterminate here.
        parent_outcome = (
            outcome
            if outcome in {"succeeded", "refused", "failed", "cancelled", "indeterminate"}
            else "indeterminate"
        )
        receipt = broker.parent_run_controller.close(
            parent.context,
            parent_outcome,
            "rails-summary:" + str((routed.get("receipt") or {}).get("receipt_id") or outcome),
            principal=principal,
        )
        entry = route["entries"][0]
        if outcome == "succeeded" and int(entry.get("profile_schema_version", 1)) == 2:
            # The child has completed and the parent receipt is now durable;
            # this is the first truthful observation of a migrated local path.
            adoption.record_local_rails_readiness_after_load(
                principal,
                deployment_revision_id=str(entry["deployment_revision_id"]),
            )
        summarize.last_receipt_id = str(receipt.get("receipt_id") or "")
        summarize.last_egress = frozen_egress if outcome == "succeeded" else ""
        if outcome != "succeeded" or not isinstance(routed.get("result"), dict):
            raise RailsSummaryUnavailable("rails_summary_" + outcome, summarize.last_receipt_id)
        value = routed["result"]
        return str(value["summary"])

    summarize.last_receipt_id = ""  # type: ignore[attr-defined]
    summarize.last_egress = ""  # type: ignore[attr-defined]
    return summarize


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
