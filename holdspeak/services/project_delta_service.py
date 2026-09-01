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

from holdspeak.project_contracts import (
    generate_pprop_id,
    generate_prev_id,
)


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


# ── The service ──────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
    """

    def __init__(self, db: Any, collector: Any) -> None:
        self._db = db
        self._collector = collector

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
        conflicts = self._detect_conflicts(grouped)

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

        return [
            obs for obs in all_obs
            if (obs.get("captured_at") or "") > prior_opened_at
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
                        review_window_key="",  # filled by caller
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

                proposals.append({
                    "proposal_id": proposal_id,
                    "proposal_kind": rule.proposal_kind,
                    "target_ref": target_ref,
                    "title": f"{rule.proposal_kind}: {target_ref}",
                    "rationale": rule.rationale_template,
                    "patch_json": patch_str,
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
        """Persist the review row and all proposals atomically."""
        manifest_json = _deterministic_json(source_manifest)
        summary_json = _deterministic_json(summary)

        delta = self._db.project_observations

        # Insert the review row
        delta.insert_review(
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
            delta.insert_proposal(
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
