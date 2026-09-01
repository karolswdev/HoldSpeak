"""HS-160-03: ProjectDeltaService -- the frozen review algorithm (SS7.2).

Implements the twelve deterministic steps from SRS SS7.2:
  1. acquire stable revision + last accepted review cursor
  2. query each source adapter independently
  3. persist observations idempotently (delegated to collector)
  4. freeze through_sequence + source manifest
  5. compare observations + project changes after prior cursor
  6. group by target ref; classify changes
  7. conflict detection (two observations disagreeing about one target)
  8. deterministic proposals from the closed rule table
  9. evidence links + versioned materiality
 10. sort by (materiality desc, event time, kind, id)
 11. model augmentation hook (identity in P2 -- no-op)
 12. store the frozen window

SRS traceability
----------------
- DEL-001: cursor from last accepted review, not latest-two-meetings
- DEL-007: model unavailability leaves deterministic Delta usable
- SYS-020: one open review per project (returns existing if present)
- SYS-022: every proposal states kind/change/time/sources/provenance
- SYS-024: re-reading the stored window is byte-identical
- SYS-025/DOM-008: failed/stale sources produce coverage_degraded
- DOM-005: observation vs assessment vs proposal distinguishable
- TST-004: golden-window repeatability
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from holdspeak.principals import Principal
from holdspeak.project_contracts import (
    CommandResultEnvelope,
    ProjectError,
    ProjectErrorCode,
    ResultKind,
    generate_pchg_id,
    generate_pcmd_id,
    generate_pprop_id,
    generate_prev_id,
)
from holdspeak.refs import format as format_ref, parse as parse_ref
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.service_event_ledger import ServiceEventLedger


# ── Materiality formula version ──────────────────────────────────────
#
# The version string is stored on every review row (in summary_json).
# Changing ANY factor weight, threshold, or scoring function REQUIRES
# bumping this constant.  TST-004 pins both the version string AND a
# canonical scored example to catch silent drift.

MATERIALITY_VERSION = "v1"

# Factor weights (must sum to 1.0).
_FACTOR_WEIGHTS: dict[str, float] = {
    "outcome_relevance": 0.20,
    "lifecycle_severity": 0.25,
    "overdue_blocked": 0.20,
    "decision_impact": 0.15,
    "novelty": 0.10,
    "evidence_confidence": 0.10,
}

assert abs(sum(_FACTOR_WEIGHTS.values()) - 1.0) < 1e-9, "factor weights must sum to 1.0"


# ── Materiality scoring functions (pure, unit-testable) ──────────────


def score_outcome_relevance(proposal: dict[str, Any]) -> float:
    """How relevant is this proposal to the project's stated outcome.

    Deterministic proxy: proposals targeting project-owned items
    (milestones, risks, dependencies) score higher than informational
    observations (meetings, resources).
    """
    kind = proposal.get("proposal_kind", "")
    if kind in ("risk_attention", "milestone_review"):
        return 0.9
    if kind in ("review_flag", "dependency_review"):
        return 0.7
    if kind in ("observation_attention",):
        return 0.5
    if kind in ("conflict",):
        return 0.8
    if kind in ("coverage_degraded",):
        return 0.6
    return 0.3


def score_lifecycle_severity(proposal: dict[str, Any]) -> float:
    """Severity based on the target's lifecycle state.

    Overdue/blocked/broken items score highest; active/healthy lowest.
    """
    facts = _parse_facts(proposal)
    lifecycle = facts.get("lifecycle", "")
    lane = facts.get("lane", "")

    if lane == "overdue" or lifecycle in ("broken", "missed"):
        return 1.0
    if lifecycle in ("at_risk",) or lane in ("stale",):
        return 0.7
    if lifecycle in ("open", "active", "planned"):
        return 0.3
    return 0.2


def score_overdue_blocked(proposal: dict[str, Any]) -> float:
    """Is the item overdue or blocked."""
    kind = proposal.get("proposal_kind", "")
    facts = _parse_facts(proposal)

    if kind == "risk_attention" and facts.get("lane") == "overdue":
        return 1.0
    if facts.get("stale_score"):
        try:
            ss = float(facts["stale_score"])
            return min(1.0, ss)
        except (ValueError, TypeError):
            pass
    if kind == "coverage_degraded":
        return 0.8
    return 0.0


def score_decision_impact(proposal: dict[str, Any]) -> float:
    """Impact on decisions or commitments."""
    kind = proposal.get("proposal_kind", "")
    if kind == "review_flag":
        return 0.8
    if kind == "conflict":
        return 0.7
    return 0.1


def score_novelty(proposal: dict[str, Any]) -> float:
    """Is this new information vs. a recurring observation.

    In P2 all proposals in a fresh window are novel by definition.
    """
    return 0.8


def score_evidence_confidence(proposal: dict[str, Any]) -> float:
    """Confidence in the evidence backing this proposal."""
    provenance = proposal.get("provenance_class", "")
    if provenance == "observed_fact":
        return 1.0
    if provenance == "assessment":
        return 0.7
    if provenance == "proposal":
        return 0.5
    return 0.4


MATERIALITY_FACTORS: dict[str, Any] = {
    "outcome_relevance": score_outcome_relevance,
    "lifecycle_severity": score_lifecycle_severity,
    "overdue_blocked": score_overdue_blocked,
    "decision_impact": score_decision_impact,
    "novelty": score_novelty,
    "evidence_confidence": score_evidence_confidence,
}


def compute_materiality(proposal: dict[str, Any]) -> float:
    """Compute materiality score using the versioned formula.

    Returns a float in [0.0, 1.0].  The formula is a weighted sum of
    the six factor scores, each clamped to [0.0, 1.0].
    """
    total = 0.0
    for factor_name, weight in _FACTOR_WEIGHTS.items():
        scorer = MATERIALITY_FACTORS[factor_name]
        raw = scorer(proposal)
        clamped = max(0.0, min(1.0, raw))
        total += weight * clamped
    return round(total, 6)


def _parse_facts(proposal: dict[str, Any]) -> dict[str, Any]:
    """Extract facts from a proposal's source observations."""
    patch = proposal.get("patch_json", "{}")
    if isinstance(patch, str):
        try:
            return json.loads(patch)
        except (json.JSONDecodeError, TypeError):
            return {}
    if isinstance(patch, dict):
        return patch
    return {}


# ── Closed proposal-rule table (step 8) ──────────────────────────────
#
# Each row maps an observation kind to a deterministic proposal.
# The table is CLOSED: adding a rule requires a code change + test.
# Proposals carry SS5.7 shape: kind/target/patch_json/rationale/evidence.
#
# | Observation Kind       | Proposal Kind          | Rationale Template                                           |
# |------------------------|------------------------|--------------------------------------------------------------|
# | followthrough.overdue  | risk_attention         | Overdue follow-through requires risk attention               |
# | followthrough.stale    | risk_attention         | Stale follow-through may need re-engagement                  |
# | decision.review_due    | review_flag            | Accepted decision is due for periodic review                 |
# | watch.transition       | observation_attention  | Watch source detected a state transition                     |

@dataclass(frozen=True, slots=True)
class ProposalRule:
    """A deterministic proposal rule from the closed table."""
    observation_kind: str
    proposal_kind: str
    rationale_template: str
    provenance_class: str  # "observed_fact" | "assessment" | "proposal"


PROPOSAL_RULES: tuple[ProposalRule, ...] = (
    ProposalRule(
        observation_kind="followthrough.overdue",
        proposal_kind="risk_attention",
        rationale_template="Overdue follow-through requires risk attention",
        provenance_class="assessment",
    ),
    ProposalRule(
        observation_kind="followthrough.stale",
        proposal_kind="risk_attention",
        rationale_template="Stale follow-through may need re-engagement",
        provenance_class="assessment",
    ),
    ProposalRule(
        observation_kind="decision.review_due",
        proposal_kind="review_flag",
        rationale_template="Accepted decision is due for periodic review",
        provenance_class="assessment",
    ),
    ProposalRule(
        observation_kind="watch.transition",
        proposal_kind="observation_attention",
        rationale_template="Watch source detected a state transition",
        provenance_class="observed_fact",
    ),
)

_RULE_BY_KIND: dict[str, ProposalRule] = {
    r.observation_kind: r for r in PROPOSAL_RULES
}

# Observation kinds that are informational (no deterministic proposal).
_INFORMATIONAL_KINDS: frozenset[str] = frozenset({
    "meeting.associated",
    "resource.linked",
    "decision.lifecycle",
})


# ── Change classification vocabulary ─────────────────────────────────

CHANGE_CLASSES: frozenset[str] = frozenset({
    "added", "changed", "closed", "overdue", "blocked",
    "contradicted", "coverage_degraded",
})


def _classify_observation(obs: dict[str, Any]) -> str:
    """Classify a single observation into a change class.

    Uses the observation kind and fact content to determine the class.
    """
    kind = obs.get("observation_kind", "")
    facts = {}
    raw = obs.get("fact_json", "{}")
    if isinstance(raw, str):
        try:
            facts = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass

    if kind == "followthrough.overdue":
        return "overdue"
    if kind == "followthrough.stale":
        return "blocked"
    if kind == "decision.review_due":
        return "changed"
    if kind == "watch.transition":
        event_type = facts.get("event_type", "")
        if event_type in ("closed", "merged", "resolved"):
            return "closed"
        return "changed"

    # Default: "added" for new, informational observations
    return "added"


# ── Decision verbs (DEL-002) ─────────────────────────────────────────

DECISION_VERBS: frozenset[str] = frozenset({
    "accept", "edit_accept", "defer", "dismiss",
})

# ── Registered handler map (SS5.7, HS-160-04) ────────────────────────
#
# The handler map is CLOSED: proposal_kind -> handler action.
# "create_item" means the accept routes through ProjectService.create_item.
# "record_only" means the accepted proposal + its evidence links ARE the
# truth; no external mutation exists for that kind in P2.
# "refuse" means the kind cannot be accepted (e.g. conflict proposals
# are for judgment framing -- dismiss or defer only).
#
# This is the extension seam P4's Steward reuses.

HANDLER_MAP: dict[str, str] = {
    "risk_attention": "create_item",
    "review_flag": "record_only",
    "observation_attention": "record_only",
    "conflict": "refuse",
    "coverage_degraded": "record_only",
}


def _dismissal_basis_hash(source_version: str, normalized_patch: str) -> str:
    """DEL-003: hash(source_version + normalized_patch).

    The basis hash identifies the material content that was dismissed.
    If the same content appears in a future window, the dismissal
    suppresses it.  A changed basis (different source_version or patch)
    yields a linked successor instead.
    """
    h = hashlib.sha256()
    h.update(source_version.encode("utf-8"))
    h.update(b"|")
    h.update(normalized_patch.encode("utf-8"))
    return h.hexdigest()[:32]


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash of a command's request payload (API-002)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _envelope_to_dict(env: CommandResultEnvelope) -> dict[str, Any]:
    """Serialize an envelope to a JSON-safe dict for storage/response."""
    return {
        "result_kind": env.result_kind.value,
        "project_id": env.project_id,
        "project_revision": env.project_revision,
        "changed_refs": [str(r) for r in env.changed_refs],
    }


# ── The service ──────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_utc(value: str) -> datetime:
    """Parse an ISO timestamp to aware-UTC; naive values are assumed UTC.

    The cursor comparison must never depend on string lexicography across
    mixed offset formats (the HS-160-04 counsel-bait: naive local
    captured_at vs UTC-offset prior_opened_at compares wrong silently).
    Unparseable/empty values sort earliest (never past the cursor).
    """
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _deterministic_json(obj: Any) -> str:
    """Serialize to JSON with deterministic key ordering + compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class ProjectDeltaService:
    """The frozen review algorithm (SS7.2, twelve steps).

    Composed behind ProjectService (SS6.1).  Routes are story 05's
    concern; this service owns the domain logic only.

    One-open-review law (SYS-020): if the project already has an open
    review, open_review returns it unchanged.  The caller receives the
    stored window for repeatable inspection (SYS-024).

    HS-160-04: decide_proposal and accept_review extend this service
    with durable decision verbs (DEL-002..006) and atomic review
    acceptance (SYS-023, DEL-005).
    """

    def __init__(
        self,
        db: Any,
        collector: Any,
        *,
        project_service: Any = None,
    ) -> None:
        self._db = db
        self._collector = collector
        self._project_service = project_service
        self._ledger = ServiceEventLedger(db)

    # ── public API ────────────────────────────────────────────────────

    def open_review(
        self,
        principal: Any,
        project_id: str,
    ) -> dict[str, Any]:
        """Open a deterministic review window for a project (SS7.2).

        Returns the review dict (review row + proposals).

        One-open-review law: if an open review already exists for this
        project, it is returned unchanged.  Re-reading the stored window
        is byte-identical (SYS-024).
        """
        project_id = str(project_id).strip()

        # ── One-open-review check ────────────────────────────────────
        existing = self._find_open_review(project_id)
        if existing is not None:
            return self._load_frozen_window(existing)

        # ── Step 1: acquire stable revision + last accepted cursor ───
        revision, from_sequence, prior_opened_at = self._acquire_cursor(
            project_id,
        )

        # ── Step 2: query each source adapter independently ──────────
        coverage = self._collector.collect_all(project_id)

        # ── Step 3: observations persisted idempotently ──────────────
        # (already done by the collector in step 2)

        # ── Step 4: freeze through_sequence + source manifest ────────
        through_sequence = self._compute_through_sequence(project_id)
        source_manifest = self._build_source_manifest(coverage)

        review_id = generate_prev_id()
        review_window_key = review_id
        now = _now_iso()

        # ── Step 5: compare observations after the prior cursor ──────
        new_observations = self._observations_after_cursor(
            project_id, prior_opened_at,
        )

        # ── Step 6: group by target ref + classify ───────────────────
        grouped = self._group_by_target(new_observations)

        # ── Step 7: conflict detection ───────────────────────────────
        conflicts = self._detect_conflicts(grouped, review_window_key)

        # ── Step 8: deterministic proposals from closed rule table ────
        proposals = self._generate_proposals(
            project_id, review_window_key, grouped, now,
        )

        # Add conflict proposals
        for conflict in conflicts:
            proposals.append(conflict)

        # Add coverage_degraded proposals for failed/stale sources
        degraded_proposals = self._coverage_degraded_proposals(
            project_id, review_window_key, source_manifest, now,
        )
        proposals.extend(degraded_proposals)

        # ── Step 9: evidence links + materiality ─────────────────────
        for p in proposals:
            p["materiality_score"] = compute_materiality(p)
            p["materiality"] = str(p["materiality_score"])

        # ── Step 9b: recurrence (DEL-003, DEL-004) ────────────────────
        #
        # Before a new window's proposals are finalized, suppress any
        # whose basis hash matches a dismissed proposal with an unchanged
        # basis (DEL-003); deferred proposals whose deferred_until has
        # passed return flagged as 'returning' (DEL-004).
        proposals = self._apply_recurrence(project_id, proposals, now)

        # Deterministic-ID dedup: two observations of the SAME fact in
        # one window mint the SAME pprop_ id by design — one semantic
        # proposal, not a UNIQUE-constraint crash (the CI same-second
        # collision, HS-160-08). First occurrence wins.
        seen_ids: set = set()
        deduped: list[dict[str, Any]] = []
        for prop in proposals:
            prop_id = prop.get("proposal_id", "")
            if prop_id and prop_id in seen_ids:
                continue
            seen_ids.add(prop_id)
            deduped.append(prop)
        proposals = deduped

        # ── Step 10: sort (materiality desc, event time, kind, id) ───
        proposals.sort(key=lambda p: (
            -p.get("materiality_score", 0.0),
            p.get("observed_at", ""),
            p.get("proposal_kind", ""),
            p.get("proposal_id", ""),
        ))

        # ── Step 11: model augmentation hook (identity in P2) ────────
        proposals = self._model_augmentation(
            {"review_id": review_id, "project_id": project_id},
            proposals,
        )

        # ── Step 12: store the frozen window ─────────────────────────
        summary = {
            "materiality_version": MATERIALITY_VERSION,
            "proposal_count": len(proposals),
            "source_count": len(source_manifest),
        }

        self._store_window(
            review_id=review_id,
            project_id=project_id,
            from_sequence=from_sequence,
            through_sequence=through_sequence,
            source_manifest=source_manifest,
            revision=revision,
            proposals=proposals,
            summary=summary,
            now=now,
        )

        return self._load_frozen_window(
            self._db.project_observations.get_review(review_id),
        )

    # ── HS-160-04: decision verbs (DEL-002..005) ──────────────────────

    def decide_proposal(
        self,
        principal: Principal,
        project_id: str,
        proposal_id: str,
        verb: str,
        *,
        patch: Optional[dict[str, Any]] = None,
        deferred_until: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Apply a durable decision verb to a proposal (DEL-002).

        Verbs: accept | edit_accept | defer | dismiss.

        Idempotent under command_id (API-002): same ID + same request
        hash returns stored result; different hash raises conflict.

        A proposal not 'open' returns a typed conflict (already-decided).

        Accept semantics per kind (the HANDLER_MAP):
        - risk_attention: creates a project_item (kind 'risk' or the
          patch's item_type) VIA ProjectService.create_item. This is the
          REGISTERED HANDLER -- no parallel mutation path (SS5.7).
        - review_flag / observation_attention: record-only. The accepted
          proposal + its evidence links ARE the truth. No external
          mutation exists for these kinds in P2. This is an honest
          reading: the SRS says "applied through a registered command
          handler" but for these kinds the handler IS the acceptance
          record. The handler map documents "record_only".
        - conflict: refuses accept. A conflict proposal is for judgment
          framing (two observations disagree) -- dismiss or defer only.
          Returns a typed capability error.
        - coverage_degraded: record-only (the degraded coverage fact is
          the proposal itself).

        Revision-bump reading (SRS SS5.7 vs DOM-003):
        Proposal decisions do NOT bump project.revision. SS5.7's
        decided_at / decided_by are proposal-level fields. DOM-003's
        "accepted Project mutation" applies at review-accept time, and
        any item created via the handler DOES ride the 158 revision law
        inside ProjectService.create_item. This reading preserves the
        atomic semantics: decisions accumulate, the aggregate mutation
        is accept_review.
        """
        verb = str(verb).strip()
        if verb not in DECISION_VERBS:
            raise ValidationError(
                f"Unknown decision verb: {verb!r}; "
                f"must be one of {sorted(DECISION_VERBS)}",
                code="validation",
            )

        # Idempotency check (API-002)
        req_hash = _request_hash({
            "project_id": project_id,
            "proposal_id": proposal_id,
            "verb": verb,
            "patch": patch,
            "deferred_until": deferred_until,
        })
        if command_id is not None:
            existing_cmd = self._db.projects.get_project_command(command_id)
            if existing_cmd is not None:
                if (existing_cmd["status"] == "completed"
                        and existing_cmd["request_hash"] == req_hash):
                    if existing_cmd["result_json"]:
                        return json.loads(existing_cmd["result_json"])
                    return {"result_kind": "no_change",
                            "project_id": project_id}
                if existing_cmd["request_hash"] != req_hash:
                    raise ConflictError(
                        "idempotency conflict: same command_id "
                        "with different request hash",
                        code="idempotency_conflict",
                        context={"command_id": command_id},
                    )

        # Load the proposal
        proposal = self._db.project_observations.get_proposal(proposal_id)
        if proposal is None:
            raise ValidationError(
                f"Proposal {proposal_id!r} not found",
                code="validation",
            )
        if proposal["project_id"] != project_id:
            raise ValidationError(
                f"Proposal {proposal_id!r} does not belong to "
                f"project {project_id!r}",
                code="validation",
            )

        # Already-decided guard
        if proposal.get("lifecycle") != "open":
            raise ConflictError(
                f"Proposal {proposal_id!r} already decided "
                f"(lifecycle={proposal.get('lifecycle')!r})",
                code="already_decided",
                context={
                    "proposal_id": proposal_id,
                    "lifecycle": proposal.get("lifecycle"),
                },
            )

        now = _now_iso()
        cmd_id = command_id or generate_pcmd_id()
        decided_by = f"principal:{principal.identity}"

        proposal_kind = proposal.get("proposal_kind", "")
        handler_action = HANDLER_MAP.get(proposal_kind, "record_only")

        result: dict[str, Any] = {
            "proposal_id": proposal_id,
            "verb": verb,
            "decided_at": now,
            "decided_by_ref": decided_by,
        }

        if verb == "accept" or verb == "edit_accept":
            # Conflict kind refuses accept
            if handler_action == "refuse":
                raise ValidationError(
                    f"Proposal kind {proposal_kind!r} cannot be accepted "
                    f"(conflict proposals are for judgment framing -- "
                    f"dismiss or defer only)",
                    code="capability",
                )

            effective_patch = patch if (verb == "edit_accept" and patch) else None
            patch_json_str = proposal.get("patch_json", "{}")
            if effective_patch is not None:
                # edit_accept: merge edited fields into existing patch
                try:
                    base_patch = json.loads(patch_json_str) if isinstance(
                        patch_json_str, str) else patch_json_str
                except (json.JSONDecodeError, TypeError):
                    base_patch = {}
                base_patch.update(effective_patch)
                patch_json_str = _deterministic_json(base_patch)

            with self._db._connection() as conn:
                self._db.project_observations.update_proposal_in_transaction(
                    conn, proposal_id,
                    lifecycle="accepted",
                    decided_at=now,
                    decided_by_ref=decided_by,
                )
                # Record the command
                envelope = CommandResultEnvelope(
                    result_kind=ResultKind.PROPOSAL_DECIDED,
                    project_id=project_id,
                    project_revision=0,  # no revision bump
                    changed_refs=(
                        parse_ref(format_ref("project", project_id)),
                    ),
                )
                self._record_command(
                    conn, cmd_id, project_id,
                    "decide_proposal", req_hash, envelope,
                )

            # If handler is create_item, route through ProjectService
            if handler_action == "create_item" and self._project_service:
                try:
                    item_patch = json.loads(patch_json_str) if isinstance(
                        patch_json_str, str) else patch_json_str
                except (json.JSONDecodeError, TypeError):
                    item_patch = {}

                item_type = item_patch.get("item_type", "risk")
                item_payload: dict[str, Any] = {
                    "item_type": item_type,
                    "title": item_patch.get("title",
                                            proposal.get("title", "")),
                    "summary": item_patch.get("summary",
                                              proposal.get("rationale")),
                    # PROVENANCE_KINDS is closed to {"owner"} in P2;
                    # the provenance is recorded in the proposal's
                    # evidence links, not the item's provenance_kind.
                    "provenance_kind": "owner",
                    "source_observation_id": proposal.get(
                        "observation_id", proposal_id),
                }
                # Copy optional fields from patch
                for key in ("severity", "owner_ref", "due_at",
                            "details", "lifecycle"):
                    if key in item_patch:
                        item_payload[key] = item_patch[key]

                # DOM-007 guard: a proposal MUST NOT complete a
                # milestone via create_item. Milestone completion
                # requires the explicit transition_item verb. Strip
                # lifecycle='reached' for milestones silently (the
                # item gets the default lifecycle instead).
                if (item_type == "milestone"
                        and item_payload.get("lifecycle") == "reached"):
                    del item_payload["lifecycle"]

                # Ensure required details for typed items
                # (risk requires likelihood + impact)
                if "details" not in item_payload:
                    if item_type == "risk":
                        item_payload["details"] = {
                            "likelihood": item_patch.get(
                                "likelihood", "medium"),
                            "impact": item_patch.get("impact", "medium"),
                            "mitigation": item_patch.get("mitigation"),
                        }
                    elif item_type == "dependency":
                        item_payload["details"] = {
                            "direction": item_patch.get(
                                "direction", "upstream"),
                            "counterpart_ref": item_patch.get(
                                "counterpart_ref", "unknown"),
                        }
                    elif item_type == "signal":
                        item_payload["details"] = {
                            "metric": item_patch.get("metric", "unknown"),
                        }

                item_result = self._project_service.create_item(
                    principal, project_id, item_payload,
                )
                result["item_id"] = item_result.get("item_id")
                result["item_result"] = item_result

            result["lifecycle"] = "accepted"

        elif verb == "defer":
            with self._db._connection() as conn:
                self._db.project_observations.update_proposal_in_transaction(
                    conn, proposal_id,
                    lifecycle="deferred",
                    decided_at=now,
                    decided_by_ref=decided_by,
                    deferred_until=deferred_until,
                )
                envelope = CommandResultEnvelope(
                    result_kind=ResultKind.PROPOSAL_DECIDED,
                    project_id=project_id,
                    project_revision=0,
                    changed_refs=(
                        parse_ref(format_ref("project", project_id)),
                    ),
                )
                self._record_command(
                    conn, cmd_id, project_id,
                    "decide_proposal", req_hash, envelope,
                )
            result["lifecycle"] = "deferred"
            result["deferred_until"] = deferred_until

        elif verb == "dismiss":
            # DEL-003: compute dismissal_basis_hash
            patch_json_str = proposal.get("patch_json", "{}")
            source_version = self._extract_source_version(proposal)
            basis_hash = _dismissal_basis_hash(source_version, patch_json_str)

            with self._db._connection() as conn:
                self._db.project_observations.update_proposal_in_transaction(
                    conn, proposal_id,
                    lifecycle="dismissed",
                    decided_at=now,
                    decided_by_ref=decided_by,
                    dismissal_basis_hash=basis_hash,
                )
                envelope = CommandResultEnvelope(
                    result_kind=ResultKind.PROPOSAL_DECIDED,
                    project_id=project_id,
                    project_revision=0,
                    changed_refs=(
                        parse_ref(format_ref("project", project_id)),
                    ),
                )
                self._record_command(
                    conn, cmd_id, project_id,
                    "decide_proposal", req_hash, envelope,
                )
            result["lifecycle"] = "dismissed"
            result["dismissal_basis_hash"] = basis_hash

        result.update(_envelope_to_dict(CommandResultEnvelope(
            result_kind=ResultKind.PROPOSAL_DECIDED,
            project_id=project_id,
            project_revision=0,
            changed_refs=(parse_ref(format_ref("project", project_id)),),
        )))
        return result

    def accept_review(
        self,
        principal: Principal,
        project_id: str,
        review_id: str,
        *,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Atomically accept a review (DEL-005, SYS-023).

        ONE transaction (the conn-accepting family):
        1. Review status -> 'accepted' + accepted_at/by +
           project_revision_accepted.
        2. projects.last_review_id/last_review_at forward (the CURSOR).
        3. Revision law envelope (revision+1, pchg_ change row,
           ledger event 'project.review.accepted').
        4. Undecided proposals become 'superseded' (see ruling below).

        Undecided-at-accept ruling:
        DEL-006 says partial-coverage reviews MAY be accepted. The SRS
        says accept "applies accepted proposals... freezes the summary".
        RULING: undecided open proposals become 'superseded' at accept.
        They belonged to a closed window. This serves DEL-003/004
        recurrence best: a superseded proposal is neither dismissed
        (which would suppress via basis hash) nor deferred (which
        would return). If the same material reappears in the next
        window it gets a fresh proposal -- the reviewer did not
        explicitly dismiss it, so it should not be silently suppressed.
        """
        project_id = str(project_id).strip()
        review_id = str(review_id).strip()

        # Idempotency check
        req_hash = _request_hash({
            "project_id": project_id,
            "review_id": review_id,
        })
        if command_id is not None:
            existing_cmd = self._db.projects.get_project_command(command_id)
            if existing_cmd is not None:
                if (existing_cmd["status"] == "completed"
                        and existing_cmd["request_hash"] == req_hash):
                    if existing_cmd["result_json"]:
                        return json.loads(existing_cmd["result_json"])
                    return {"result_kind": "no_change",
                            "project_id": project_id}
                if existing_cmd["request_hash"] != req_hash:
                    raise ConflictError(
                        "idempotency conflict: same command_id "
                        "with different request hash",
                        code="idempotency_conflict",
                        context={"command_id": command_id},
                    )

        # Load the review
        review = self._db.project_observations.get_review(review_id)
        if review is None:
            raise ValidationError(
                f"Review {review_id!r} not found", code="validation",
            )
        if review["project_id"] != project_id:
            raise ValidationError(
                f"Review {review_id!r} does not belong to "
                f"project {project_id!r}", code="validation",
            )
        if review.get("status") != "open":
            raise ConflictError(
                f"Review {review_id!r} is not open "
                f"(status={review.get('status')!r})",
                code="already_decided",
                context={"review_id": review_id,
                         "status": review.get("status")},
            )

        now = _now_iso()
        cmd_id = command_id or generate_pcmd_id()
        accepted_by = f"principal:{principal.identity}"
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            # Read current revision inside the transaction
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
            if row is None:
                raise ValidationError(
                    f"Project {project_id!r} not found", code="validation",
                )
            current_rev = int(row["revision"])
            new_revision = current_rev + 1

            # 1. Bump project revision
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now, project_id),
            )

            # 2. Update review status
            self._db.project_observations.update_review_in_transaction(
                conn, review_id,
                status="accepted",
                project_revision_accepted=new_revision,
                accepted_at=now,
                accepted_by_ref=accepted_by,
            )

            # 3. Advance the cursor (last_review_id/at)
            conn.execute(
                "UPDATE projects SET last_review_id = ?, "
                "last_review_at = ? WHERE id = ?",
                (review_id, now, project_id),
            )

            # 4. Supersede undecided proposals (the ruling above)
            proposals = self._db.project_observations.list_proposals(
                project_id, review_window_key=review_id, lifecycle="open",
            )
            for p in proposals:
                self._db.project_observations.update_proposal_in_transaction(
                    conn, p["id"],
                    lifecycle="superseded",
                    decided_at=now,
                    decided_by_ref=accepted_by,
                )

            # 5. Change row (pchg_)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """INSERT INTO project_changes
                   (id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    change_id, project_id, new_revision,
                    "project.review.accepted",
                    project_ref, accepted_by, cmd_id,
                    None, None,
                    json.dumps({
                        "action": "review.accepted",
                        "review_id": review_id,
                    }),
                    now,
                ),
            )

            # 6. Ledger event
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.review.accepted",
                producer="ProjectDeltaService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "review_id": review_id,
                    "action": "review.accepted",
                },
                refs=[project_ref],
            )

            # 7. Envelope + command record
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.REVIEW_ACCEPTED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id,
                "accept_review", req_hash, envelope,
            )

        result = _envelope_to_dict(envelope)
        result["review_id"] = review_id
        result["accepted_at"] = now
        result["accepted_by_ref"] = accepted_by
        return result

    # ── Decision helpers ────────────────────────────────────────────────

    @staticmethod
    def _extract_source_version(proposal: dict[str, Any]) -> str:
        """Extract the source_version from a proposal for basis hashing.

        DEL-003 (S-1 fix): the source_version is the observation's
        stable fact-version, carried in patch_json["_source_version"].
        Both dismiss-time and recurrence-time hashing derive from the
        same field, so identical facts hash identically across windows.
        """
        patch_raw = proposal.get("patch_json", "{}")
        if isinstance(patch_raw, str):
            try:
                patch_obj = json.loads(patch_raw)
            except (json.JSONDecodeError, TypeError):
                return ""
        else:
            patch_obj = patch_raw
        return patch_obj.get("_source_version", "")

    def _record_command(
        self,
        conn: Any,
        command_id: str,
        project_id: str,
        command_kind: str,
        request_hash: str,
        envelope: CommandResultEnvelope,
    ) -> None:
        """Record a completed command in the idempotency ledger."""
        now_iso = _now_iso()
        result_json = json.dumps(
            _envelope_to_dict(envelope), ensure_ascii=False,
        )
        conn.execute(
            """INSERT INTO project_commands
               (id, project_id, command_kind, request_hash,
                status, result_json, completed_at, created_at)
               VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   status = 'completed',
                   result_json = excluded.result_json,
                   completed_at = excluded.completed_at""",
            (command_id, project_id, command_kind, request_hash,
             result_json, now_iso, now_iso),
        )

    # ── HS-160-04: Recurrence logic (DEL-003, DEL-004) ──────────────

    def _apply_recurrence(
        self,
        project_id: str,
        proposals: list[dict[str, Any]],
        now: str,
    ) -> list[dict[str, Any]]:
        """Apply dismissal suppression and deferred return laws.

        DEL-003: dismissed proposals with unchanged basis (same
        dismissal_basis_hash) are suppressed. A changed basis yields
        a linked successor (predecessor_proposal_id in patch_json).

        DEL-004: deferred proposals whose deferred_until has passed
        RETURN in the new window flagged as 'returning' (not new).
        Un-due deferred proposals stay suppressed.
        """
        delta = self._db.project_observations

        # Gather dismissed proposals and their basis hashes
        dismissed = delta.list_dismissed_proposals(project_id)
        dismissed_hashes: dict[str, dict[str, Any]] = {}
        for d in dismissed:
            bh = d.get("dismissal_basis_hash")
            if bh:
                dismissed_hashes[bh] = d

        # Gather deferred proposals
        deferred = delta.list_deferred_proposals(project_id)
        deferred_by_kind_target: dict[tuple[str, str], dict[str, Any]] = {}
        for df in deferred:
            key = (df.get("proposal_kind", ""), df.get("target_ref", ""))
            deferred_by_kind_target[key] = df

        filtered: list[dict[str, Any]] = []
        returning: list[dict[str, Any]] = []

        for p in proposals:
            patch_str = p.get("patch_json", "{}")
            # S-1: derive source_version from patch_json._source_version
            # (same derivation as _extract_source_version at dismiss time)
            source_version = self._extract_source_version(p)
            basis = _dismissal_basis_hash(source_version, patch_str)

            # DEL-003: dismissed suppression
            if basis in dismissed_hashes:
                # Unchanged basis -> suppress
                continue

            # Check if this is a changed-basis successor of a dismissed
            # proposal. Match by (proposal_kind, target_ref).
            kind_target = (
                p.get("proposal_kind", ""),
                p.get("target_ref", ""),
            )
            predecessor = None
            for d in dismissed:
                if (d.get("proposal_kind", "") == kind_target[0]
                        and d.get("target_ref", "") == kind_target[1]):
                    predecessor = d
                    break

            if predecessor is not None:
                # Changed basis -> linked successor
                pred_patch = p.get("patch_json", "{}")
                if isinstance(pred_patch, str):
                    try:
                        patch_obj = json.loads(pred_patch)
                    except (json.JSONDecodeError, TypeError):
                        patch_obj = {}
                else:
                    patch_obj = dict(pred_patch)
                patch_obj["predecessor_proposal_id"] = predecessor["id"]
                p["patch_json"] = _deterministic_json(patch_obj)

            # DEL-004: check for deferred return
            if kind_target in deferred_by_kind_target:
                df = deferred_by_kind_target[kind_target]
                deferred_until = df.get("deferred_until")
                if deferred_until and deferred_until <= now:
                    # Due -> return as 'returning'
                    p["returning"] = True
                    p["predecessor_proposal_id"] = df["id"]
                    # Embed predecessor in patch_json for persistence
                    deferred_patch = p.get("patch_json", "{}")
                    if isinstance(deferred_patch, str):
                        try:
                            dp_obj = json.loads(deferred_patch)
                        except (json.JSONDecodeError, TypeError):
                            dp_obj = {}
                    else:
                        dp_obj = dict(deferred_patch)
                    dp_obj["predecessor_proposal_id"] = df["id"]
                    dp_obj["returning"] = True
                    p["patch_json"] = _deterministic_json(dp_obj)
                    returning.append(p)
                    del deferred_by_kind_target[kind_target]
                    continue
                elif deferred_until and deferred_until > now:
                    # Un-due -> suppress
                    continue
                # No deferred_until -> treat as returning (no due date
                # means "return next time")
                p["returning"] = True
                p["predecessor_proposal_id"] = df["id"]
                deferred_patch = p.get("patch_json", "{}")
                if isinstance(deferred_patch, str):
                    try:
                        dp_obj = json.loads(deferred_patch)
                    except (json.JSONDecodeError, TypeError):
                        dp_obj = {}
                else:
                    dp_obj = dict(deferred_patch)
                dp_obj["predecessor_proposal_id"] = df["id"]
                dp_obj["returning"] = True
                p["patch_json"] = _deterministic_json(dp_obj)
                returning.append(p)
                del deferred_by_kind_target[kind_target]
                continue

            filtered.append(p)

        # Returning proposals come first (they are flagged, not new)
        return returning + filtered

    # ── Step 1: cursor acquisition ────────────────────────────────────

    def _acquire_cursor(
        self, project_id: str,
    ) -> tuple[int, int, Optional[str]]:
        """Return (revision, from_sequence, prior_opened_at).

        DEL-001: the cursor comes from the last ACCEPTED review's
        through_sequence, not the latest-two-meetings shortcut.
        """
        room = self._db.projects.get_project_room_fields(project_id)
        revision = (room or {}).get("revision") or 0

        last_review_id = (room or {}).get("last_review_id")
        if last_review_id:
            last_review = self._db.project_observations.get_review(
                last_review_id,
            )
            if last_review and last_review.get("status") == "accepted":
                return (
                    revision,
                    last_review.get("through_sequence") or 0,
                    last_review.get("opened_at"),
                )

        # Also check for any accepted review in history
        accepted = self._db.project_observations.list_reviews(
            project_id, status="accepted", limit=1,
        )
        if accepted:
            return (
                revision,
                accepted[0].get("through_sequence") or 0,
                accepted[0].get("opened_at"),
            )

        return (revision, 0, None)

    # ── Step 4: freeze helpers ────────────────────────────────────────

    def _compute_through_sequence(self, project_id: str) -> int:
        """Count all observations for the project (monotonically increasing)."""
        obs = self._db.project_observations.list_observations(
            project_id, limit=10000,
        )
        return len(obs)

    def _build_source_manifest(
        self, coverage: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the frozen source manifest from coverage results.

        Each entry: {state, source_version, observation_count, error?}.
        DOM-008: failed sources produce explicit degraded coverage.
        """
        manifest: dict[str, Any] = {}
        for source_key, result in sorted(coverage.items()):
            entry: dict[str, Any] = {
                "state": result.get("state", "unknown"),
            }
            if result.get("state") == "failed":
                entry["error"] = result.get("error", {})
                entry["observation_count"] = 0
            else:
                entry["observation_count"] = (
                    result.get("inserted", 0) + result.get("no_op", 0)
                )
            manifest[source_key] = entry
        return manifest

    # ── Step 5: observation comparison ────────────────────────────────

    def _observations_after_cursor(
        self,
        project_id: str,
        prior_opened_at: Optional[str],
    ) -> list[dict[str, Any]]:
        """Read observations that entered after the prior review's cursor.

        If no prior review, all observations are returned.
        """
        all_obs = self._db.project_observations.list_observations(
            project_id, limit=10000,
        )
        if prior_opened_at is None:
            return all_obs

        cursor = _parse_utc(prior_opened_at)
        return [
            obs for obs in all_obs
            if _parse_utc(obs.get("captured_at") or "") > cursor
        ]

    # ── Step 6: grouping + classification ─────────────────────────────

    def _group_by_target(
        self, observations: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Group observations by stable target (subject_ref).

        Each group gets a change classification.
        """
        groups: dict[str, list[dict[str, Any]]] = {}
        for obs in observations:
            target = obs.get("subject_ref") or obs.get("id", "")
            groups.setdefault(target, []).append(obs)
        return groups

    # ── Step 7: conflict detection ────────────────────────────────────

    def _detect_conflicts(
        self, grouped: dict[str, list[dict[str, Any]]],
        review_window_key: str = "",
    ) -> list[dict[str, Any]]:
        """Detect conflicting observations for the same target.

        Two observations disagree when they have different content hashes
        for the same subject_ref and observation kind.  The conflict
        proposal carries BOTH source refs (DOM-005: no silent winner).
        """
        conflicts: list[dict[str, Any]] = []
        for target_ref, obs_list in sorted(grouped.items()):
            # Group by observation_kind within the target
            by_kind: dict[str, list[dict[str, Any]]] = {}
            for obs in obs_list:
                kind = obs.get("observation_kind", "")
                by_kind.setdefault(kind, []).append(obs)

            for kind, kind_obs in sorted(by_kind.items()):
                if len(kind_obs) < 2:
                    continue
                # Check for differing content hashes
                hashes = {obs.get("content_hash", "") for obs in kind_obs}
                if len(hashes) > 1:
                    # Conflict: multiple different observations for same target+kind
                    source_refs = sorted({
                        obs.get("source_id", "") for obs in kind_obs
                    })
                    conflict_patch = {
                        "conflicting_sources": source_refs,
                        "conflicting_hashes": sorted(hashes),
                        "observation_kind": kind,
                    }
                    patch_str = _deterministic_json(conflict_patch)
                    proposal_id = generate_pprop_id(
                        project_id=kind_obs[0].get("project_id", ""),
                        review_window_key=review_window_key,
                        proposal_kind="conflict",
                        target_ref=target_ref,
                        normalized_patch=patch_str,
                    )
                    conflicts.append({
                        "proposal_id": proposal_id,
                        "proposal_kind": "conflict",
                        "target_ref": target_ref,
                        "title": f"Conflict: {kind} on {target_ref}",
                        "rationale": (
                            f"Two observations disagree about {kind} "
                            f"on {target_ref}: sources {source_refs}"
                        ),
                        "patch_json": patch_str,
                        "provenance_class": "assessment",
                        "observed_at": max(
                            obs.get("observed_at", "") for obs in kind_obs
                        ),
                        "source_refs": source_refs,
                        "change_class": "contradicted",
                    })
        return conflicts

    # ── Step 8: deterministic proposals ───────────────────────────────

    def _generate_proposals(
        self,
        project_id: str,
        review_window_key: str,
        grouped: dict[str, list[dict[str, Any]]],
        now: str,
    ) -> list[dict[str, Any]]:
        """Apply the closed rule table to observations, producing proposals.

        Each observation that matches a rule in PROPOSAL_RULES generates
        exactly one deterministic proposal.  Informational observations
        (meeting.associated, resource.linked, decision.lifecycle) do not
        generate proposals.
        """
        proposals: list[dict[str, Any]] = []
        for target_ref, obs_list in sorted(grouped.items()):
            for obs in sorted(obs_list, key=lambda o: o.get("observed_at", "")):
                kind = obs.get("observation_kind", "")
                rule = _RULE_BY_KIND.get(kind)
                if rule is None:
                    continue

                change_class = _classify_observation(obs)
                fact_json = obs.get("fact_json", "{}")
                patch_str = fact_json if isinstance(fact_json, str) else _deterministic_json(fact_json)

                proposal_id = generate_pprop_id(
                    project_id=project_id,
                    review_window_key=review_window_key,
                    proposal_kind=rule.proposal_kind,
                    target_ref=target_ref,
                    normalized_patch=patch_str,
                )

                # S-1: thread the observation's source_version into
                # patch_json so both dismiss-time and recurrence-time
                # hashing derive the same stable basis.
                obs_source_version = obs.get("source_version", "")
                try:
                    patch_obj = json.loads(patch_str)
                except (json.JSONDecodeError, TypeError):
                    patch_obj = {}
                patch_obj["_source_version"] = obs_source_version
                patch_str_with_sv = _deterministic_json(patch_obj)

                proposals.append({
                    "proposal_id": proposal_id,
                    "proposal_kind": rule.proposal_kind,
                    "target_ref": target_ref,
                    "title": f"{rule.proposal_kind}: {target_ref}",
                    "rationale": rule.rationale_template,
                    "patch_json": patch_str_with_sv,
                    "provenance_class": rule.provenance_class,
                    "observed_at": obs.get("observed_at", now),
                    "source_refs": [obs.get("source_id", "")],
                    "change_class": change_class,
                    "observation_id": obs.get("id", ""),
                })
        return proposals

    # ── Coverage degraded proposals ───────────────────────────────────

    def _coverage_degraded_proposals(
        self,
        project_id: str,
        review_window_key: str,
        source_manifest: dict[str, Any],
        now: str,
    ) -> list[dict[str, Any]]:
        """Generate coverage_degraded proposals for failed/stale sources.

        SYS-025/DOM-008: a failed or stale source MUST produce explicit
        degraded coverage, never silent "no change".
        """
        proposals: list[dict[str, Any]] = []
        for source_key, entry in sorted(source_manifest.items()):
            state = entry.get("state", "")
            if state not in ("failed", "stale"):
                continue

            patch = {
                "source_key": source_key,
                "state": state,
                "error": entry.get("error", {}),
            }
            patch_str = _deterministic_json(patch)

            proposal_id = generate_pprop_id(
                project_id=project_id,
                review_window_key=review_window_key,
                proposal_kind="coverage_degraded",
                target_ref=f"source:{source_key}",
                normalized_patch=patch_str,
            )

            proposals.append({
                "proposal_id": proposal_id,
                "proposal_kind": "coverage_degraded",
                "target_ref": f"source:{source_key}",
                "title": f"Degraded coverage: {source_key} ({state})",
                "rationale": (
                    f"Source {source_key} is {state}; "
                    f"review may be incomplete"
                ),
                "patch_json": patch_str,
                "provenance_class": "assessment",
                "observed_at": now,
                "source_refs": [source_key],
                "change_class": "coverage_degraded",
            })
        return proposals

    # ── Step 11: model augmentation hook (identity in P2) ─────────────

    @staticmethod
    def _model_augmentation(
        review: dict[str, Any],
        proposals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """P4 extension point: a model may ADD proposals but MUST NOT
        remove or rewrite deterministic entries (SS7.2 step 11).

        In P2 this is the identity function.
        """
        return proposals

    # ── Step 12: store the window ─────────────────────────────────────

    def _store_window(
        self,
        *,
        review_id: str,
        project_id: str,
        from_sequence: int,
        through_sequence: int,
        source_manifest: dict[str, Any],
        revision: int,
        proposals: list[dict[str, Any]],
        summary: dict[str, Any],
        now: str,
    ) -> None:
        """Persist the review row and all proposals atomically.

        S-3: one transaction wrapping the review + all proposals via the
        _in_transaction variants.  A failure on proposal k>1 rolls back
        the review AND proposals 1..k-1 -- all-or-nothing.
        """
        manifest_json = _deterministic_json(source_manifest)
        summary_json = _deterministic_json(summary)

        delta = self._db.project_observations

        with self._db._connection() as conn:
            # Insert the review row
            delta.insert_review_in_transaction(
                conn,
                review_id=review_id,
                project_id=project_id,
                status="open",
                from_sequence=from_sequence,
                through_sequence=through_sequence,
                source_manifest_json=manifest_json,
                project_revision_opened=revision,
                opened_at=now,
                summary_json=summary_json,
            )

            # Insert proposals under this review's window key
            for p in proposals:
                delta.insert_proposal_in_transaction(
                    conn,
                    proposal_id=p["proposal_id"],
                    project_id=project_id,
                    review_window_key=review_id,
                    proposal_kind=p.get("proposal_kind", ""),
                    target_ref=p.get("target_ref", ""),
                    title=p.get("title", ""),
                    rationale=p.get("rationale"),
                    patch_json=p.get("patch_json", "{}"),
                    materiality=p.get("materiality"),
                    confidence=None,
                    producer_kind=p.get("provenance_class"),
                    lifecycle="open",
                )

    # ── Read-back helpers ─────────────────────────────────────────────

    def _find_open_review(self, project_id: str) -> Optional[dict[str, Any]]:
        """Return the existing open review for a project, or None."""
        reviews = self._db.project_observations.list_reviews(
            project_id, status="open", limit=1,
        )
        return reviews[0] if reviews else None

    def _load_frozen_window(
        self, review_row: dict[str, Any],
    ) -> dict[str, Any]:
        """Read-back a frozen window: the review row + its proposals.

        SYS-024: this MUST be byte-identical across reads.
        """
        review_id = review_row["id"]
        project_id = review_row["project_id"]

        proposals = self._db.project_observations.list_proposals(
            project_id, review_window_key=review_id,
        )

        # Re-sort by materiality desc, then by proposal fields for
        # deterministic ordering (the stored list_proposals order may
        # be created_at DESC; we need the canonical materiality order).
        def _sort_key(p: dict[str, Any]) -> tuple:
            mat = p.get("materiality") or "0"
            try:
                mat_f = float(mat)
            except (ValueError, TypeError):
                mat_f = 0.0
            return (
                -mat_f,
                p.get("created_at", ""),
                p.get("proposal_kind", ""),
                p.get("id", ""),
            )

        proposals.sort(key=_sort_key)

        manifest_json = review_row.get("source_manifest_json", "{}")
        if isinstance(manifest_json, str):
            try:
                manifest = json.loads(manifest_json)
            except (json.JSONDecodeError, TypeError):
                manifest = {}
        else:
            manifest = manifest_json

        summary_json = review_row.get("summary_json") or "{}"
        if isinstance(summary_json, str):
            try:
                summary = json.loads(summary_json)
            except (json.JSONDecodeError, TypeError):
                summary = {}
        else:
            summary = summary_json

        return {
            "review_id": review_id,
            "project_id": project_id,
            "status": review_row.get("status", "open"),
            "from_sequence": review_row.get("from_sequence"),
            "through_sequence": review_row.get("through_sequence"),
            "source_manifest": manifest,
            "project_revision_opened": review_row.get(
                "project_revision_opened",
            ),
            "materiality_version": summary.get(
                "materiality_version", MATERIALITY_VERSION,
            ),
            "opened_at": review_row.get("opened_at", ""),
            "proposals": [
                {
                    "id": p["id"],
                    "proposal_kind": p.get("proposal_kind", ""),
                    "target_ref": p.get("target_ref", ""),
                    "title": p.get("title", ""),
                    "rationale": p.get("rationale", ""),
                    "patch_json": p.get("patch_json", "{}"),
                    "materiality": p.get("materiality", "0"),
                    "producer_kind": p.get("producer_kind", ""),
                    "lifecycle": p.get("lifecycle", "open"),
                }
                for p in proposals
            ],
        }
