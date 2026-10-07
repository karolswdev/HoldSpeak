"""HS-172-03: Proposal bridge -- intel artifacts to follow-through proposals.

After an intel job completes, reads decision_capture and action_owner_enforcer
artifacts and writes PROPOSALS into ``follow_through_proposals``.
Confirm/dismiss go through the kernel.

HS-200-12 -- the full production chain, made to preserve what it reads:

* **The real extractor's key.**  ``decision_capture`` writes
  ``{"decision": ..., "rationale": ..., "source_timestamp": ...}``
  (``plugins/builtin/decision_capture.py:_extract_decisions``); the bridge read
  ``dec["text"]`` and so bridged ZERO decisions from a real run.  Both keys are
  read now.
* **Evidence.**  Every proposal carries the transcript SPAN it came from
  (``span_start``/``span_end``/``segment_index``): a verified
  ``source_timestamp`` resolves to the segment that contains it; an item
  without one is anchored by a deterministic quote match over the recorded
  segments.  No match, no span, and the face says so.
* **Support (C2).**  A deterministic field mapping over the recorded
  transcript -- never a model score -- raises support: an exact quote of the
  sentence inside its span is ``supported``; a resolved span without the quote
  is ``source_linked``; no span is ``unknown``.  An edit of the sentence drops
  a supported proposal to ``source_linked`` and KEEPS the record with
  ``invalidation_reason=text_edited`` (``project_update_service.py:139``).
* **Retry identity.**  ``retry_key`` is deterministic over (meeting id,
  extraction revision = the job's frozen transcript hash, kind, span,
  ordinal-in-span).  A repeated completion, a model retry and a lost
  acknowledgement resolve to the SAME row in ANY state; the older
  ``fingerprint`` index was partial over ``proposed`` and let a re-run re-mint
  a proposal the owner had already confirmed.
* **Idempotent verbs.**  Confirm on a confirmed proposal replays its durable
  result (the same record and commitment ids) instead of erroring; the flip to
  ``confirmed`` is one conditional UPDATE inside the record-chain transaction,
  so two racing confirms produce one chain.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from holdspeak.timestamps import utc_now_iso
from typing import Any, Optional

from ..db.core import Database
from ..db.proposals import Proposal
from ..logging_config import get_logger
from ..principals import Principal
from ..services.observer import current_correlation_id
from ..services.service_event_ledger import ServiceEventLedger
from .project_update_service import (
    INVALIDATION_TEXT_EDITED,
    METHOD_FIELD_MAPPING,
    SUPPORT_SOURCE_LINKED,
    SUPPORT_SUPPORTED,
    SUPPORT_UNKNOWN,
)

log = get_logger("proposal_bridge")

# The two extractors whose artifacts we read.
_DECISION_PLUGIN = "decision_capture"
_ACTION_PLUGIN = "action_owner_enforcer"
# PHILO-15 08 (B02): the summary run's own decisions and action items
# (kernel/meeting_plugin_projection.py ``_write_summary_items``). The bridge
# reads them for a kind no plugin artifact covers, so a meeting yields
# proposals on day one and a plugin run never doubles them.
_SUMMARY_PLUGIN = "meeting_summary"
_SUMMARY_CAPABILITY = "meeting.deferred_analysis"

# The deterministic quote match: a proposal whose content words are (almost)
# all present in one segment is ANCHORED there.  This is a mapping over the
# recorded transcript, not a score: the threshold is a fixed constant and the
# result is a span, never a confidence.
_ANCHOR_OVERLAP = 0.6
_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the to of and or in on at for with by is are was were be we will "
    "our it this that as from into".split()
)


def _norm(text: str) -> str:
    return " ".join(_WORD_RE.findall(str(text or "").lower()))


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(str(text or "").lower()) if w not in _STOP}


def _seg(segment: Any, name: str) -> Any:
    if isinstance(segment, dict):
        return segment.get(name)
    return getattr(segment, name, None)


class Evidence:
    """Where in the transcript a proposal came from, and what that proves."""

    __slots__ = ("span_start", "span_end", "segment_index", "support", "record")

    def __init__(
        self,
        span_start: Optional[float],
        span_end: Optional[float],
        segment_index: Optional[int],
        support: str,
        record: Optional[dict[str, Any]],
    ) -> None:
        self.span_start = span_start
        self.span_end = span_end
        self.segment_index = segment_index
        self.support = support
        self.record = record

    @property
    def anchored(self) -> bool:
        return self.segment_index is not None


def locate_evidence(
    segments: Any,
    text: str,
    timestamp: Any,
    *,
    meeting_id: str,
    revision: str,
) -> Evidence:
    """Resolve a proposal's transcript evidence deterministically.

    1. A numeric ``timestamp`` inside a segment's [start, end] anchors the
       proposal to that segment.
    2. Otherwise the segment holding the most of the sentence's content words
       anchors it, when that is at least ``_ANCHOR_OVERLAP`` of them.
    3. Support is ``supported`` only when the normalized sentence is a verbatim
       quote of the anchoring segment (a field mapping over ``segments.text``);
       an anchor without the quote is ``source_linked``; no anchor is
       ``unknown``.
    """
    rows = list(segments or [])
    index: Optional[int] = None
    # 1. the verified point.
    if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
        t = float(timestamp)
        for i, seg in enumerate(rows):
            try:
                start = float(_seg(seg, "start_time"))
                end = float(_seg(seg, "end_time"))
            except (TypeError, ValueError):
                continue
            if start <= t <= end:
                index = i
                break
    # 2. the quote match.
    words = _content_words(text)
    if index is None and words:
        best, best_ratio = None, 0.0
        for i, seg in enumerate(rows):
            seg_words = _content_words(str(_seg(seg, "text") or ""))
            if not seg_words:
                continue
            ratio = len(words & seg_words) / len(words)
            if ratio > best_ratio:
                best, best_ratio = i, ratio
        if best is not None and best_ratio >= _ANCHOR_OVERLAP:
            index = best
    if index is None:
        return Evidence(None, None, None, SUPPORT_UNKNOWN, None)
    seg = rows[index]
    try:
        start = float(_seg(seg, "start_time"))
        end = float(_seg(seg, "end_time"))
    except (TypeError, ValueError):
        start, end = 0.0, 0.0
    ref = f"meeting:{meeting_id}#segment:{index}"
    quoted = bool(_norm(text)) and _norm(text) in _norm(str(_seg(seg, "text") or ""))
    if quoted:
        record = {
            "method": METHOD_FIELD_MAPPING,
            "source_version": revision,
            "source_refs": [ref],
            "fields": ["segments.text"],
        }
        return Evidence(start, end, index, SUPPORT_SUPPORTED, record)
    return Evidence(start, end, index, SUPPORT_SOURCE_LINKED, None)


def retry_key(
    meeting_id: str,
    revision: str,
    kind: str,
    evidence: Evidence,
    ordinal: int,
    text: str,
) -> str:
    """The deterministic identity of one extracted proposal.

    Anchored: (meeting, revision, kind, span, ordinal-in-span) -- a retry that
    rewords the same decision at the same place is the same proposal.
    Unanchored: (meeting, revision, kind, normalized text) -- there is nothing
    else to hold it to.
    """
    if evidence.anchored:
        raw = (
            f"{meeting_id}|{revision}|{kind}|span:"
            f"{evidence.span_start:.3f}-{evidence.span_end:.3f}|{ordinal}"
        )
    else:
        raw = f"{meeting_id}|{revision}|{kind}|text:{_norm(text)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _tomorrow_stamp() -> str:
    """The start of tomorrow, local time, as an ISO stamp with its offset."""
    from datetime import datetime, timedelta

    now = datetime.now().astimezone()
    start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()


def is_deferred(p: Any, now: Any = None) -> bool:
    """True while a proposed row's Defer stamp is in the future."""
    from datetime import datetime

    stamp = str(getattr(p, "deferred_until", None) or "").strip()
    if not stamp:
        return False
    try:
        until = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    if until.tzinfo is None:
        until = until.astimezone()
    current = now or datetime.now().astimezone()
    return until > current


class ProposalBridgeService:
    """Bridge intel artifacts into follow-through proposals."""

    def __init__(self, db: Database) -> None:
        self._db = db

    # ── bridge: artifacts -> proposals ──────────────────────────────

    def bridge_meeting_artifacts(
        self,
        meeting_id: str,
        *,
        model_host: str | None = None,
        job: Any = None,
    ) -> list[Proposal]:
        """Read extractor artifacts for a meeting, create proposals.

        Returns the newly created proposals (empty if all were deduped).
        ``model_host`` defaults to the recorded host on the intel job row;
        never resolved from config in the read path.  ``job`` is the intel
        job that just completed (HS-200-12: its transcript hash is the
        extraction revision every proposal is keyed under); when omitted the
        meeting's current job is read.
        """
        created: list[Proposal] = []

        if job is None:
            try:
                job = self._db.intel.get_latest_intel_job(meeting_id)
            except Exception:
                job = None
        # HS-172-02: read the recorded host from the job row.
        if model_host is None:
            model_host = (
                str(getattr(job, "model_host", "") or "")
                or self._db.intel.get_intel_job_model_host(meeting_id)
            )

        meeting = self._db.meetings.get_meeting(meeting_id)
        segments = list(getattr(meeting, "segments", None) or [])
        revision = str(getattr(job, "transcript_hash", "") or "")
        if not revision and meeting is not None:
            try:
                revision = meeting.transcript_hash()
            except Exception:
                revision = ""

        # Resolve project_id for this meeting.
        project_ids = self._db.projects.get_meeting_projects(meeting_id)
        project_id = project_ids[0]["project_id"] if project_ids else None

        provenance = {
            "job_id": str(getattr(job, "job_id", "") or "") or None,
            "job_attempt": int(getattr(job, "attempts", 0) or 0) or None,
            "model_host": model_host,
        }

        # Read artifacts from the two extractors.
        artifacts = self._db.plugins.list_artifacts(meeting_id, limit=2000)

        span_ordinals: dict[tuple[str, float, float], int] = {}
        # A kind a plugin covers -- one that wrote, or one this job planned
        # (it may write on a retry) -- is that plugin's; the summary's items of
        # that kind are not bridged, so one decision never reads twice.
        plugin_ids = {art.plugin_id for art in artifacts} | {
            str(member.get("plugin_id") or "")
            for member in tuple(getattr(job, "frozen_plugin_members", ()) or ())
            if isinstance(member, dict)
        }
        for art in artifacts:
            if art.plugin_id == _SUMMARY_PLUGIN:
                created.extend(
                    self._bridge_summary_artifact(
                        meeting_id, project_id, art, segments, revision,
                        provenance, span_ordinals, job,
                        decisions=_DECISION_PLUGIN not in plugin_ids,
                        actions=_ACTION_PLUGIN not in plugin_ids,
                    )
                )
            elif art.plugin_id == _DECISION_PLUGIN:
                created.extend(
                    self._bridge_decision_artifact(
                        meeting_id, project_id, art, segments, revision,
                        provenance, span_ordinals, job,
                    )
                )
            elif art.plugin_id == _ACTION_PLUGIN:
                created.extend(
                    self._bridge_action_artifact(
                        meeting_id, project_id, art, segments, revision,
                        provenance, span_ordinals, job,
                    )
                )

        return created

    def _mint(
        self,
        *,
        meeting_id: str,
        project_id: Optional[str],
        kind: str,
        text: str,
        artifact: Any,
        plugin: str,
        segments: list[Any],
        revision: str,
        provenance: dict[str, Any],
        span_ordinals: dict[tuple[str, float, float], int],
        job: Any,
        timestamp: Any,
        speaker: Any,
        owner_hint: Any = None,
        due_hint: Any = None,
        rationale: Any = None,
        action_item_id: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> Optional[Proposal]:
        evidence = locate_evidence(
            segments, text, timestamp, meeting_id=meeting_id, revision=revision,
        )
        ordinal = 0
        if evidence.anchored:
            slot = (kind, float(evidence.span_start or 0.0), float(evidence.span_end or 0.0))
            ordinal = span_ordinals.get(slot, 0)
            span_ordinals[slot] = ordinal + 1
        key = retry_key(meeting_id, revision, kind, evidence, ordinal, text)
        return self._db.proposals.create_proposal(
            meeting_id=meeting_id,
            project_id=project_id,
            kind=kind,
            text=text,
            owner_hint=owner_hint,
            due_hint=due_hint,
            source_artifact_id=artifact.id,
            source_plugin=plugin,
            segment_timestamp=(
                float(timestamp)
                if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool)
                else evidence.span_start
            ),
            speaker_label=speaker,
            model_host=provenance.get("model_host"),
            retry_key=key,
            extraction_revision=revision or None,
            job_id=provenance.get("job_id"),
            job_attempt=provenance.get("job_attempt"),
            extraction_model=self._extraction_model(job, capability or f"meeting.plugin.{plugin}"),
            span_start=evidence.span_start,
            span_end=evidence.span_end,
            segment_index=evidence.segment_index,
            support=evidence.support,
            support_record=evidence.record,
            rationale=str(rationale).strip() if isinstance(rationale, str) and rationale.strip() else None,
            action_item_id=action_item_id,
        )

    def _bridge_summary_artifact(
        self,
        meeting_id: str,
        project_id: Optional[str],
        artifact: Any,
        segments: list[Any],
        revision: str,
        provenance: dict[str, Any],
        span_ordinals: dict[tuple[str, float, float], int],
        job: Any,
        *,
        decisions: bool,
        actions: bool,
    ) -> list[Proposal]:
        """PHILO-15 08: the summary's decisions and action items as proposals.

        An action proposal names the summary's own ``action_items`` row, so
        Confirm accepts that row and Decline dismisses it (one obligation,
        one row). An anchored action gives its row the transcript moment.
        """
        created: list[Proposal] = []
        structured = self._parse_structured(artifact)
        if decisions:
            for dec in structured.get("decisions") or []:
                if not isinstance(dec, dict):
                    continue
                text = str(dec.get("decision") or dec.get("text") or "").strip()
                if not text:
                    continue
                prop = self._mint(
                    meeting_id=meeting_id, project_id=project_id, kind="decision",
                    text=text, artifact=artifact, plugin=_SUMMARY_PLUGIN,
                    segments=segments, revision=revision, provenance=provenance,
                    span_ordinals=span_ordinals, job=job, timestamp=None, speaker=None,
                    rationale=dec.get("rationale"), capability=_SUMMARY_CAPABILITY,
                )
                if prop is not None:
                    created.append(prop)
        if actions:
            for item in structured.get("action_items") or []:
                if not isinstance(item, dict):
                    continue
                text = str(item.get("task") or "").strip()
                if not text:
                    continue
                action_item_id = str(item.get("action_item_id") or "").strip() or None
                prop = self._mint(
                    meeting_id=meeting_id, project_id=project_id, kind="action",
                    text=text, artifact=artifact, plugin=_SUMMARY_PLUGIN,
                    segments=segments, revision=revision, provenance=provenance,
                    span_ordinals=span_ordinals, job=job, timestamp=None, speaker=None,
                    owner_hint=item.get("owner"), due_hint=item.get("due"),
                    action_item_id=action_item_id, capability=_SUMMARY_CAPABILITY,
                )
                if prop is None:
                    continue
                created.append(prop)
                if action_item_id and prop.span_start is not None:
                    # The moment the item was said: Follow-through quotes it
                    # instead of "source moment unavailable".
                    with self._db._connection() as conn:
                        conn.execute(
                            "UPDATE action_items SET source_timestamp = ? "
                            "WHERE id = ? AND source_timestamp IS NULL",
                            (prop.span_start, action_item_id),
                        )
        return created

    def _bridge_decision_artifact(
        self,
        meeting_id: str,
        project_id: Optional[str],
        artifact: Any,
        segments: list[Any],
        revision: str,
        provenance: dict[str, Any],
        span_ordinals: dict[tuple[str, float, float], int],
        job: Any,
    ) -> list[Proposal]:
        """Extract decisions from a decision_capture artifact."""
        created: list[Proposal] = []
        structured = self._parse_structured(artifact)
        decisions = structured.get("decisions") or []
        for dec in decisions:
            if not isinstance(dec, dict):
                continue
            # HS-200-12: the REAL plugin's key is `decision`; `text` is the
            # shape the HS-172 tests seeded.  Both are read.
            text = str(dec.get("text") or dec.get("decision") or "").strip()
            if not text:
                continue
            prop = self._mint(
                meeting_id=meeting_id, project_id=project_id, kind="decision",
                text=text, artifact=artifact, plugin=_DECISION_PLUGIN,
                segments=segments, revision=revision, provenance=provenance,
                span_ordinals=span_ordinals, job=job,
                timestamp=dec.get("source_timestamp"), speaker=dec.get("speaker"),
                # HS-200-13 (AC1): the plugin's `rationale` rides with the
                # proposal so the confirmed record can say WHY.
                rationale=dec.get("rationale"),
            )
            if prop is not None:
                created.append(prop)
        return created

    def _bridge_action_artifact(
        self,
        meeting_id: str,
        project_id: Optional[str],
        artifact: Any,
        segments: list[Any],
        revision: str,
        provenance: dict[str, Any],
        span_ordinals: dict[tuple[str, float, float], int],
        job: Any,
    ) -> list[Proposal]:
        """Extract action items from an action_owner_enforcer artifact."""
        created: list[Proposal] = []
        structured = self._parse_structured(artifact)
        items = structured.get("action_items") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            text = str(item.get("task") or item.get("text") or "").strip()
            if not text:
                continue
            prop = self._mint(
                meeting_id=meeting_id, project_id=project_id, kind="action",
                text=text, artifact=artifact, plugin=_ACTION_PLUGIN,
                segments=segments, revision=revision, provenance=provenance,
                span_ordinals=span_ordinals, job=job,
                timestamp=item.get("source_timestamp"), speaker=item.get("speaker"),
                owner_hint=item.get("owner"), due_hint=item.get("due"),
            )
            if prop is not None:
                created.append(prop)
        return created

    def _extraction_model(self, job: Any, capability: str) -> Optional[str]:
        """The model the bound job's FROZEN route ran this extractor on.

        Read from the bundle member → route plan → deployment revision, the
        same chain ``BoundDeferredIntelJob.egress_model_host`` reads the host
        from.  None when the job carries no bundle (a pre-C row, a test seed).
        """
        bundle_id = str(getattr(job, "bundle_id", "") or "")
        if not bundle_id:
            return None
        try:
            with self._db._connection() as conn:
                row = conn.execute(
                    """SELECT d.model
                         FROM inference_parent_route_bundle_members m
                         JOIN inference_route_plan_entries e ON e.plan_id = m.route_plan_id
                         JOIN deployment_revisions d ON d.id = e.deployment_revision_id
                        WHERE m.bundle_id = ? AND m.capability_id IN (?, 'meeting.deferred_analysis')
                        ORDER BY CASE WHEN m.capability_id = ? THEN 0 ELSE 1 END,
                                 e.route_leg_ordinal
                        LIMIT 1""",
                    (bundle_id, capability, capability),
                ).fetchone()
        except Exception:
            return None
        if row is None:
            return None
        model = str(row["model"] or "").strip()
        return model or None

    @staticmethod
    def _parse_structured(artifact: Any) -> dict[str, Any]:
        """Parse the artifact's structured_json."""
        raw = getattr(artifact, "structured_json", None)
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}

    # ── edit (HS-200-12) ────────────────────────────────────────────

    @staticmethod
    def _invalidated(proposal: Proposal, now: str) -> tuple[str, Optional[dict[str, Any]]]:
        """What an edit of the sentence does to the support axis (C2, R5).

        A supported sentence drops to source_linked; its record is KEPT with
        the invalidation stamped.  An already-linked or unknown sentence keeps
        its support but gains the same invalidation stamp so the face can
        say EDITED.
        """
        record = dict(proposal.support_record or {})
        if not record:
            record = {"method": METHOD_FIELD_MAPPING}
        record["invalidated_at"] = now
        record["invalidation_reason"] = INVALIDATION_TEXT_EDITED
        support = (
            SUPPORT_SOURCE_LINKED
            if proposal.support == SUPPORT_SUPPORTED or proposal.segment_index is not None
            else proposal.support
        )
        return support, record

    def edit_proposal(
        self,
        principal: Principal,
        proposal_id: str,
        *,
        text: Optional[str] = None,
        owner: Optional[str] = None,
        due: Optional[str] = None,
    ) -> dict[str, Any]:
        """Amend a proposed row in place and return its durable projection.

        Edit-then-confirm (ruling R5): the edit is persisted on the proposal
        now; the record chain is minted on Confirm.  A changed sentence drops
        support (C2); a supplied owner or due resolves that typed unknown.
        """
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}
        if proposal.state != "proposed":
            return {"error": "Proposal already decided", "code": proposal.state}
        new_text = str(text).strip() if text is not None else None
        if new_text == "":
            return {"error": "The sentence cannot be empty"}
        now = utc_now_iso()
        support: Optional[str] = None
        record: Optional[dict[str, Any]] = None
        if new_text is not None and new_text != proposal.text:
            support, record = self._invalidated(proposal, now)
        else:
            new_text = None
        if new_text is None and owner is None and due is None:
            return {"success": True, "proposal": self._serialize(proposal), "unchanged": True}
        updated = self._db.proposals.edit_proposal(
            proposal_id,
            text=new_text,
            owner=owner.strip() if isinstance(owner, str) else owner,
            due=due.strip() if isinstance(due, str) else due,
            support=support,
            support_record=record,
        )
        if updated is None:
            return {"error": "Proposal already decided"}
        with self._db._connection() as conn:
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="proposal.edited",
                producer="ProposalBridgeService",
                subject_ref=f"proposal:{proposal_id}",
                source_revision=updated.extraction_revision or "",
                facts={
                    "proposal_id": proposal_id,
                    "kind": updated.kind,
                    "text": updated.text,
                    "original_text": updated.original_text,
                    "owner": updated.owner,
                    "due": updated.due,
                    "support": updated.support,
                    "text_edited": new_text is not None,
                },
                refs=[f"proposal:{proposal_id}", f"meeting:{updated.meeting_id}"],
                correlation_id=current_correlation_id(),
                causation_id=f"proposal:{proposal_id}",
            )
        return {"success": True, "proposal": self._serialize(updated)}

    # ── confirm / dismiss ───────────────────────────────────────────

    def _durable_result(self, proposal: Proposal, *, replayed: bool) -> dict[str, Any]:
        """The durable ids a confirmed proposal resolved to, read back."""
        record_id = proposal.decision_record_id
        commitment_id = proposal.commitment_id
        decision_id = action_id = None
        with self._db._connection() as conn:
            if record_id:
                row = conn.execute(
                    "SELECT source_id FROM decision_records WHERE id = ?", (record_id,)
                ).fetchone()
                decision_id = str(row["source_id"]) if row else None
            if commitment_id:
                row = conn.execute(
                    "SELECT action_item_id FROM decision_commitments WHERE id = ?",
                    (commitment_id,),
                ).fetchone()
                action_id = str(row["action_item_id"]) if row else None
        return {
            "proposal_id": proposal.id,
            "state": "confirmed",
            "original_text": proposal.original_text,
            "decision_id": decision_id,
            "decision_record_id": record_id,
            "action_item_id": action_id,
            "commitment_id": commitment_id,
            "replayed": replayed,
            "proposal": self._serialize(proposal),
        }

    def confirm_proposal(
        self,
        principal: Principal,
        proposal_id: str,
        *,
        text: Optional[str] = None,
        owner: Optional[str] = None,
        due: Optional[str] = None,
    ) -> dict[str, Any]:
        """Confirm a proposal: write decision_record + commitment through the kernel.

        Both decision-kind and action-kind create the full chain:
        decisions -> decision_records (+ sources) -> action_items -> decision_commitments
        so the Room's DECISIONS & COMMITMENTS reads see them.

        HS-200-12: idempotent.  A second confirm (a retried POST after a lost
        acknowledgement, a double click) returns the SAME durable result with
        ``replayed: true``; the state flip is a conditional UPDATE inside the
        chain's transaction, so two racing confirms mint one chain.
        """
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}
        if proposal.state == "confirmed":
            return self._durable_result(proposal, replayed=True)
        if proposal.state == "dismissed":
            return {"error": "Proposal already dismissed", "code": "dismissed"}
        # HS-200-12 (counsel P2-i): `follow_through_proposals` has no FK to
        # meetings, so a proposal outlives its meeting; the chain below
        # references the meeting (decisions.source_meeting_id) and raised a
        # bare IntegrityError.  Say it, before anything is written.
        meeting = self._db.meetings.get_meeting(proposal.meeting_id)
        if meeting is None:
            retained = self._db.meetings.get_meeting(
                proposal.meeting_id, include_parked=True
            )
            if retained is not None and retained.parked:
                return {
                    "error": "The meeting is parked; restore it before confirming this proposal.",
                    "code": "meeting_parked",
                }
            return {
                "error": "The meeting this proposal came from was deleted; nothing can be kept from it.",
                "code": "meeting_deleted",
            }

        edited_text = str(text).strip() if text is not None else None
        if edited_text == "":
            edited_text = None
        text_changed = edited_text is not None and edited_text != proposal.text
        final_text = edited_text or proposal.text
        final_owner = owner or proposal.owner
        final_due = due or proposal.due
        now = utc_now_iso()
        support: Optional[str] = None
        record: Optional[dict[str, Any]] = None
        if text_changed:
            support, record = self._invalidated(proposal, now)

        decision_id = f"dec-{uuid.uuid4().hex[:16]}"
        record_id = f"record-{uuid.uuid4().hex[:16]}"
        record_source_id = f"record-source-{uuid.uuid4().hex[:16]}"
        action_id = f"action-{uuid.uuid4().hex[:16]}"
        commitment_id = f"commitment-{uuid.uuid4().hex[:16]}"
        anchored = proposal.segment_index is not None
        provenance = {
            "meeting_id": proposal.meeting_id,
            "span_start": proposal.span_start,
            "span_end": proposal.span_end,
            "segment_index": proposal.segment_index,
            "extraction_revision": proposal.extraction_revision,
            "job_id": proposal.job_id,
            "job_attempt": proposal.job_attempt,
            "extraction_model": proposal.extraction_model,
            "model_host": proposal.model_host,
            "support": support or proposal.support,
        }

        with self._db._connection() as conn:
            # 0. The atomic claim: flip proposed -> confirmed FIRST, inside
            #    this transaction.  rowcount 0 means another confirm won the
            #    race; nothing below has been written, so replay theirs.
            flipped = self._db.proposals.confirm_proposal(
                proposal_id,
                text=edited_text if text_changed else None,
                owner=owner,
                due=due,
                decision_record_id=record_id,
                commitment_id=commitment_id,
                support=support,
                support_record=record,
                conn=conn,
            )
            if flipped is None:
                winner = self._db.proposals.get_proposal(proposal_id)
                if winner is not None and winner.state == "confirmed":
                    return self._durable_result(winner, replayed=True)
                return {"error": "Proposal not found or already decided"}

            # 1. decisions row (raw meeting decision, lifecycle=accepted).
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, decided_at, date_basis,
                    source_timestamp, provenance_label, source_artifact_id,
                    source_meeting_id, project_key, lifecycle,
                    created_at, updated_at, last_modified)
                   VALUES (?, ?, ?, ?, 'meeting_date', ?, ?, ?, ?, ?, 'accepted',
                           ?, ?, ?)""",
                (
                    decision_id, final_text, proposal.rationale or "", now,
                    proposal.span_start if anchored else proposal.segment_timestamp,
                    "anchored" if anchored else "reported",
                    proposal.source_artifact_id or "",
                    proposal.meeting_id,
                    self._project_key(proposal.project_id),
                    now, now, now,
                ),
            )

            # 2. decision_records row (the durable canon the Room reads).
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, rationale, alternatives, owner,
                    review_date, lifecycle, source_type, source_id,
                    created_at, updated_at)
                   VALUES (?, ?, ?, '', ?, '', 'active', 'meeting', ?,
                           ?, ?)""",
                (record_id, final_text, proposal.rationale or "", final_owner, decision_id, now, now),
            )

            # 3. decision_record_sources: the meeting (what every Room read
            #    joins on), the proposal (the extraction provenance row), and
            #    the transcript span when the sentence is anchored.
            conn.execute(
                """INSERT INTO decision_record_sources
                   (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (record_source_id, record_id, proposal.meeting_id, now),
            )
            conn.execute(
                """INSERT INTO decision_record_sources
                   (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'proposal', ?, ?)""",
                (f"record-source-{uuid.uuid4().hex[:16]}", record_id, proposal_id, now),
            )
            if anchored:
                conn.execute(
                    """INSERT INTO decision_record_sources
                       (id, record_id, source_type, source_ref, created_at)
                       VALUES (?, ?, 'transcript', ?, ?)""",
                    (
                        f"record-source-{uuid.uuid4().hex[:16]}", record_id,
                        f"meeting:{proposal.meeting_id}#segment:{proposal.segment_index}",
                        now,
                    ),
                )

            # 4. action_items row.  PHILO-15 08: a summary action proposal
            #    stands for the summary's own row; Confirm accepts THAT row
            #    (no second copy of one obligation).
            delegated_at = now if final_owner else None
            linked = None
            if proposal.action_item_id:
                linked = conn.execute(
                    "SELECT id FROM action_items WHERE id = ?", (proposal.action_item_id,),
                ).fetchone()
            if linked is not None:
                action_id = str(linked["id"])
                conn.execute(
                    """UPDATE action_items SET task = ?, owner = ?, due = ?,
                       status = 'open', review_state = 'accepted', reviewed_at = ?,
                       delegated_at = COALESCE(delegated_at, ?),
                       source_timestamp = COALESCE(source_timestamp, ?)
                       WHERE id = ?""",
                    (
                        final_text, final_owner, final_due, now, delegated_at,
                        proposal.span_start if anchored else proposal.segment_timestamp,
                        action_id,
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO action_items
                       (id, meeting_id, task, owner, due, status,
                        review_state, source_timestamp, created_at, delegated_at,
                        source_type, source_ref)
                       VALUES (?, ?, ?, ?, ?, 'open', 'accepted', ?, ?, ?, 'meeting', ?)""",
                    (
                        action_id, proposal.meeting_id, final_text,
                        final_owner, final_due,
                        proposal.span_start if anchored else proposal.segment_timestamp,
                        now, delegated_at, proposal.meeting_id,
                    ),
                )

            # 5. decision_commitments linking decision to action_item.
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'open', ?, ?)""",
                (commitment_id, decision_id, action_id, final_owner, final_due, now, now),
            )

            # Kernel receipt (Article XI).
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="proposal.confirmed",
                producer="ProposalBridgeService",
                subject_ref=f"proposal:{proposal_id}",
                source_revision=record_id,
                facts={
                    "proposal_id": proposal_id,
                    "kind": proposal.kind,
                    "decision_id": decision_id,
                    "decision_record_id": record_id,
                    "action_item_id": action_id,
                    "commitment_id": commitment_id,
                    "text": final_text,
                    "original_text": proposal.original_text,
                    "text_edited": text_changed or bool(proposal.edited_at),
                    "owner": final_owner,
                    "due": final_due,
                    "provenance": provenance,
                },
                refs=[
                    f"proposal:{proposal_id}",
                    f"meeting:{proposal.meeting_id}",
                    f"decision:{decision_id}",
                    f"decision_record:{record_id}",
                    f"action_item:{action_id}",
                    f"commitment:{commitment_id}",
                ],
                correlation_id=current_correlation_id(),
                causation_id=f"proposal:{proposal_id}",
            )

        # HS-172-03: dirty marker so the needs-you cache refreshes.
        try:
            from .needs_you_aggregate import mark_needs_you_dirty
            mark_needs_you_dirty(self._db)
        except Exception:
            pass

        return {
            "proposal_id": proposal_id,
            "state": "confirmed",
            "original_text": proposal.original_text,
            "decision_id": decision_id,
            "decision_record_id": record_id,
            "action_item_id": action_id,
            "commitment_id": commitment_id,
            "replayed": False,
            "proposal": self._serialize(flipped),
        }

    def dismiss_proposal(
        self,
        principal: Principal,
        proposal_id: str,
    ) -> dict[str, Any]:
        """Dismiss a proposal without creating any record (idempotent)."""
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}
        if proposal.state == "dismissed":
            return {
                "proposal_id": proposal_id, "state": "dismissed", "replayed": True,
                "proposal": self._serialize(proposal),
            }
        if proposal.state == "confirmed":
            return {"error": "Proposal already confirmed", "code": "confirmed"}

        with self._db._connection() as conn:
            dismissed = self._db.proposals.dismiss_proposal(proposal_id, conn=conn)
            if dismissed is None:
                later = self._db.proposals.get_proposal(proposal_id)
                if later is not None and later.state == "dismissed":
                    return {
                        "proposal_id": proposal_id, "state": "dismissed",
                        "replayed": True, "proposal": self._serialize(later),
                    }
                return {"error": "Proposal not found or already decided"}
            # PHILO-15 08: Decline of a summary action declines its row too
            # (an accepted row is the owner's own and stays).
            if proposal.action_item_id:
                conn.execute(
                    "UPDATE action_items SET status = 'dismissed' "
                    "WHERE id = ? AND review_state != 'accepted'",
                    (proposal.action_item_id,),
                )
            # Receipt for the dismissal.
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="proposal.dismissed",
                producer="ProposalBridgeService",
                subject_ref=f"proposal:{proposal_id}",
                source_revision="",
                facts={
                    "proposal_id": proposal_id,
                    "kind": proposal.kind,
                    "text": proposal.text,
                },
                refs=[f"proposal:{proposal_id}"],
                correlation_id=current_correlation_id(),
                causation_id=f"proposal:{proposal_id}",
            )

        # HS-172-03: dirty marker so the needs-you cache refreshes.
        try:
            from .needs_you_aggregate import mark_needs_you_dirty
            mark_needs_you_dirty(self._db)
        except Exception:
            pass

        return {
            "proposal_id": proposal_id, "state": "dismissed", "replayed": False,
            "proposal": self._serialize(dismissed),
        }

    def defer_proposal(
        self,
        principal: Principal,
        proposal_id: str,
        *,
        until: Optional[str] = None,
    ) -> dict[str, Any]:
        """PHILO-15 08: Defer -- the row leaves Needs until ``until``.

        Default: the start of tomorrow, local time. The row stays proposed;
        the meeting's Review still lists it. A second Defer moves the stamp.
        """
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}
        if proposal.state != "proposed":
            return {"error": "Proposal already decided", "code": proposal.state}
        stamp = str(until or "").strip() or _tomorrow_stamp()
        deferred = self._db.proposals.defer_proposal(proposal_id, stamp)
        if deferred is None:
            return {"error": "Proposal already decided"}
        with self._db._connection() as conn:
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="proposal.deferred",
                producer="ProposalBridgeService",
                subject_ref=f"proposal:{proposal_id}",
                source_revision="",
                facts={"proposal_id": proposal_id, "kind": proposal.kind, "until": stamp},
                refs=[f"proposal:{proposal_id}", f"meeting:{proposal.meeting_id}"],
                correlation_id=current_correlation_id(),
                causation_id=f"proposal:{proposal_id}",
            )
        try:
            from .needs_you_aggregate import mark_needs_you_dirty
            mark_needs_you_dirty(self._db)
        except Exception:
            pass
        return {
            "proposal_id": proposal_id, "state": "proposed", "deferred_until": stamp,
            "proposal": self._serialize(deferred),
        }

    # ── accept reviewed (HS-200-12, counsel P1-1) ───────────────────

    @staticmethod
    def _held_reason(p: Proposal) -> Optional[str]:
        """Why `Accept reviewed` leaves a row alone, or None when it may go.

        RULING: the bulk verb confirms only rows whose support is SUPPORTED
        or LINKED and that carry no typed unknown.  An unsupported sentence
        and an unknown owner/due each need his own hand on the row.
        """
        if p.support not in {SUPPORT_SUPPORTED, SUPPORT_SOURCE_LINKED}:
            return "unsupported"
        if p.kind == "action" and (not p.owner or not p.due):
            return "unknown"
        return None

    def accept_reviewed(self, principal: Principal, meeting_id: str) -> dict[str, Any]:
        """Confirm every eligible proposed row of one meeting; name the rest.

        Returns ``accepted`` (the durable results), ``left`` (id + reason per
        held row) and the counts the receipt reads (``unsupported``,
        ``unknown``).  Rows of an earlier transcript revision are held too
        (``prior``): a bulk verb never decides beside a decision already made.
        """
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            return {"error": "Meeting not found"}
        try:
            revision = meeting.transcript_hash()
        except Exception:
            revision = ""
        accepted: list[dict[str, Any]] = []
        left: list[dict[str, Any]] = []
        counts = {"unsupported": 0, "unknown": 0, "prior": 0}
        for p in self._db.proposals.list_proposals(meeting_id=meeting_id, state="proposed"):
            reason = self._held_reason(p)
            if reason is None and revision and p.extraction_revision and p.extraction_revision != revision:
                reason = "prior"
            if reason is not None:
                counts[reason] += 1
                left.append({"proposal_id": p.id, "reason": reason})
                continue
            result = self.confirm_proposal(principal, p.id)
            if "error" in result:
                left.append({"proposal_id": p.id, "reason": str(result.get("code") or "refused")})
                continue
            accepted.append(result)
        return {
            "meeting_id": meeting_id,
            "accepted": accepted,
            "accepted_count": len(accepted),
            "left": left,
            "left_count": len(left),
            **counts,
        }

    # ── reads ───────────────────────────────────────────────────────

    def list_meeting_proposals(
        self,
        meeting_id: str,
        state: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List proposals for a meeting."""
        proposals = self._db.proposals.list_proposals(
            meeting_id=meeting_id, state=state,
        )
        return [self._serialize(p) for p in proposals]

    def list_project_proposals(
        self,
        project_id: str,
        state: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List proposals for a project (via meeting_projects)."""
        proposals = self._db.proposals.list_proposals(
            project_id=project_id, state=state,
        )
        return [self._serialize(p) for p in proposals]

    def meeting_review(self, meeting_id: str) -> dict[str, Any]:
        """HS-200-12: the ONE projection the review face reads.

        The job (its id, attempt and lineage), the transcript coverage, the
        Project the meeting is linked to, and every proposal with its
        evidence -- the rows still to review and the rows already kept.
        """
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            return {"error": "Meeting not found"}
        segments = list(getattr(meeting, "segments", None) or [])
        try:
            job = self._db.intel.get_latest_intel_job(meeting_id)
        except Exception:
            job = None
        proposals = [
            self._serialize(p)
            for p in self._db.proposals.list_proposals(meeting_id=meeting_id)
        ]
        # Oldest first: the order they were extracted in.
        proposals.sort(key=lambda p: (str(p.get("created_at") or ""), str(p.get("id"))))

        project: Optional[dict[str, Any]] = None
        try:
            links = self._db.projects.get_meeting_projects(meeting_id)
        except Exception:
            links = []
        if links:
            pid = str(links[0]["project_id"])
            name = ""
            try:
                row = self._db.projects.get_project(pid)
                name = str(getattr(row, "name", "") or "")
            except Exception:
                name = ""
            project = {"id": pid, "name": name}

        status = str(getattr(job, "status", "") or "").strip().lower()
        attempts = int(getattr(job, "attempts", 0) or 0)
        # The attempt the face is looking at: a queued successor has not
        # incremented yet, so its coming attempt is attempts + 1.
        attempt = attempts + 1 if status in {"queued", "reserved"} else max(attempts, 1) if job else 0
        origin = str(getattr(job, "origin_job_id", "") or "")
        job_id = str(getattr(job, "job_id", "") or "")
        job_payload = None
        if job is not None:
            job_payload = {
                "job_id": job_id,
                "origin_job_id": origin or None,
                # A second attempt of the same descriptor: `origin_job_id`
                # alone is not it (the stop-handoff row is superseded by the
                # first real freeze and already has one), so the honest
                # token is the attempt ordinal.
                "same_job": attempt > 1,
                "status": status,
                "attempt": attempt,
                "attempts": attempts,
                "last_error": getattr(job, "last_error", None),
                "model_host": getattr(job, "model_host", None),
                "extraction_model": self._extraction_model(
                    job, f"meeting.plugin.{_DECISION_PLUGIN}"
                ),
                "requested_at": job.requested_at.isoformat() if getattr(job, "requested_at", None) else None,
                "updated_at": job.updated_at.isoformat() if getattr(job, "updated_at", None) else None,
            }
        intel_state = str(getattr(meeting, "intel_status", "") or "").strip().lower()
        completed = getattr(meeting, "intel_completed_at", None)
        # Coverage: the whole transcript is the material one bound analysis
        # reads (intel_queue.py joins every segment), so a finished read is
        # N OF N; anything else has no honest numerator and says so.
        read_complete = status == "succeeded" or intel_state in {"complete", "ready"}
        coverage = {
            "turns": len(segments),
            "read": len(segments) if read_complete else None,
            "state": (
                "available" if read_complete
                else "reading" if status in {"claimed", "running"}
                else "queued" if status in {"queued", "reserved"}
                else "failed" if status in {"failed", "refused"} or intel_state in {"error", "failed"}
                else "unread"
            ),
            "observed_at": completed.isoformat() if completed else (
                job.updated_at.isoformat() if job is not None and getattr(job, "updated_at", None) else None
            ),
        }
        started = getattr(meeting, "started_at", None)
        # HS-200-12 (counsel P1-2): the no-duplicate law holds per transcript
        # revision.  Rows keyed under an EARLIER revision are still this
        # meeting's, and the face lists them beside the current ones so a
        # re-read after a transcript change never doubles a decision silently.
        try:
            revision = meeting.transcript_hash()
        except Exception:
            revision = ""
        prior = [
            p for p in proposals
            if revision and p.get("extraction_revision") and p["extraction_revision"] != revision
        ]
        extractors = self._extractor_rows(
            meeting_id, job, status, intel_state, proposals, revision,
        )
        return {
            "meeting_id": meeting_id,
            "title": getattr(meeting, "title", "") or "",
            "started_at": started.isoformat() if started else None,
            # PHILO-15 08 (B02 ruling 3): one honest row per extractor of the
            # latest read -- ran (with its count), skipped (why), failed (why).
            "extractors": extractors,
            "revision": revision or None,
            "prior_revision": {
                "decided": sum(1 for p in prior if p["state"] != "proposed"),
                "open": sum(1 for p in prior if p["state"] == "proposed"),
            },
            "project": project,
            "job": job_payload,
            "coverage": coverage,
            "extracted_at": completed.isoformat() if completed else None,
            "proposals": proposals,
        }

    _SUCCESS = frozenset({"success", "succeeded", "ok", "completed", "proposed", "deduped"})
    _SKIP = frozenset({"skipped", "disabled", "blocked"})

    def _extractor_rows(
        self,
        meeting_id: str,
        job: Any,
        status: str,
        intel_state: str,
        proposals: list[dict[str, Any]],
        revision: str,
    ) -> list[dict[str, Any]]:
        """What each extractor of the latest read did (PHILO-15 08).

        ``state`` is ``ran`` / ``skipped`` / ``failed``; ``count`` is the
        proposals it left under the current transcript revision; ``reason``
        says why a row did not run. A job still queued or running has no rows:
        the face says it is reading.
        """
        if job is None or status in {"queued", "reserved", "claimed", "running"}:
            return []

        def produced(plugin_id: str) -> int:
            return sum(
                1 for p in proposals
                if p.get("source_plugin") == plugin_id
                and (not revision or not p.get("extraction_revision")
                     or p.get("extraction_revision") == revision)
            )

        rows: list[dict[str, Any]] = []
        if status in {"failed", "refused"} or intel_state in {"error", "failed"}:
            reason = str(getattr(job, "last_error", "") or "").strip() or status.upper()
            rows.append({"id": _SUMMARY_PLUGIN, "label": "Summary", "state": "failed",
                         "count": None, "reason": reason})
            return rows
        if status == "succeeded" or intel_state in {"complete", "ready"}:
            rows.append({"id": _SUMMARY_PLUGIN, "label": "Summary", "state": "ran",
                         "count": produced(_SUMMARY_PLUGIN), "reason": None})
        seen: set[str] = set()
        try:
            runs = self._db.plugins.list_plugin_runs(meeting_id, limit=200)
        except Exception:
            runs = []
        for run in runs:
            if run.plugin_id in seen:
                continue
            seen.add(run.plugin_id)
            state = str(run.status or "").strip().lower()
            label = run.plugin_id.replace("_", " ").capitalize()
            if state in self._SUCCESS:
                rows.append({"id": run.plugin_id, "label": label, "state": "ran",
                             "count": produced(run.plugin_id), "reason": None})
            elif state in self._SKIP:
                rows.append({"id": run.plugin_id, "label": label, "state": "skipped",
                             "count": None, "reason": str(run.error or state).strip()})
            else:
                rows.append({"id": run.plugin_id, "label": label, "state": "failed",
                             "count": None, "reason": str(run.error or state).strip()})
        route = dict(getattr(job, "frozen_plugin_route", {}) or {})
        for skipped in route.get("plugin_chain_skipped") or []:
            plugin_id = str((skipped or {}).get("plugin_id") or "").strip()
            if not plugin_id or plugin_id in seen:
                continue
            seen.add(plugin_id)
            reason = str((skipped or {}).get("reason") or "skipped").replace("_", " ")
            rows.append({"id": plugin_id, "label": plugin_id.replace("_", " ").capitalize(),
                         "state": "skipped", "count": None, "reason": reason})
        return rows

    @staticmethod
    def _serialize(p: Proposal) -> dict[str, Any]:
        unknowns: list[dict[str, str]] = []
        if p.kind == "action":
            if not p.owner:
                unknowns.append({"type": "owner", "value": "unknown"})
            if not p.due:
                unknowns.append({"type": "due", "value": "unknown"})
        return {
            "id": p.id,
            "meeting_id": p.meeting_id,
            "project_id": p.project_id,
            "kind": p.kind,
            "text": p.text,
            "owner_hint": p.owner_hint,
            "due_hint": p.due_hint,
            "owner": p.owner,
            "due": p.due,
            # HS-200-12 (counsel P1-3): what HE supplied vs what was extracted.
            "owner_supplied": p.owner_supplied,
            "due_supplied": p.due_supplied,
            "source_artifact_id": p.source_artifact_id,
            "source_plugin": p.source_plugin,
            "segment_timestamp": p.segment_timestamp,
            "speaker_label": p.speaker_label,
            "model_host": p.model_host,
            "state": p.state,
            "original_text": p.original_text,
            "decision_record_id": p.decision_record_id,
            "rationale": p.rationale,
            "commitment_id": p.commitment_id,
            "created_at": p.created_at,
            "decided_at": p.decided_at,
            # HS-200-12: evidence, provenance, the three axes, the unknowns.
            "retry_key": p.retry_key,
            "extraction_revision": p.extraction_revision,
            "job_id": p.job_id,
            "job_attempt": p.job_attempt,
            "extraction_model": p.extraction_model,
            "span_start": p.span_start,
            "span_end": p.span_end,
            "segment_index": p.segment_index,
            "claim_kind": "proposal",
            "support": p.support,
            "support_record": p.support_record,
            "acceptance": p.acceptance,
            "unknowns": unknowns,
            "edited_at": p.edited_at,
            "text_edited": bool(p.edited_at) and p.text != (p.original_text or p.text),
            "action_item_id": p.action_item_id,
            "deferred_until": p.deferred_until,
        }

    @staticmethod
    def _project_key(project_id: Optional[str]) -> Optional[str]:
        """The project_id serves as project_key in the decisions table."""
        return project_id or None
