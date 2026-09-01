"""Universal Watch facade over the graduated connector_watches table.

SRS §2: WatchService becomes the universal application facade;
ReactionService delegates or is incrementally absorbed behind
compatibility tests.  No competing Project-only Watch root.

SRS §10: specification/lifecycle/test/baseline/list/read facade.

Traceability
------------
- ACT-002: test_watch zero-match semantics
- ACT-005: baseline_watch never emits events
- ACT-008: material edits stale test/baseline, increment revision
- ACT-009: retire_watch stops future evaluation, retains history
- SS7.2/7.3: WatchCondition@1/WatchAction@1 validation (via watch_validation)
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.observer import (
    NullObserver,
    PipelineObserver,
    observe_service,
)
from holdspeak.services.reaction_service import diff_snapshots, normalize_snapshot
from holdspeak.watch_validation import (
    validate_action,
    validate_condition,
    validate_rules,
)


def _rule_id() -> str:
    return f"wrule_{uuid.uuid4().hex[:12]}"


# Material fields on connector_watches.  Changing any of these
# triggers revision+1 and stales test_state + baseline_state (ACT-008).
_MATERIAL_FIELDS: frozenset[str] = frozenset({
    "subject_kind", "query", "trigger_kind", "trigger",
})


# ── SS8.1 github transition kinds (diff_snapshots vocabulary) ──────
#
# The closed set of event_type values that diff_snapshots produces for
# connector_id == "gh".  Surfaced in the test display payload as
# "supported_transitions" so the consumer knows what future diffs can
# detect without reading the source code.

_GITHUB_TRANSITION_KINDS: tuple[str, ...] = (
    "github.pr.opened",
    "github.pr.state_changed",
    "github.pr.merged",
    "github.pr.review_requested",
    "github.pr.review_decision_changed",
    "github.pr.checks_changed",
    "github.pr.head_changed",
)


def _github_conditions_summary(
    entities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a summary of present conditions across entities (SS8.1).

    Returns a compact map:
    - states: {"open": 3, "closed": 1}
    - checks: {"success": 2, "failure": 1}
    - review_decisions: {"approved": 1, "": 3}
    - drafts: count of draft PRs
    """
    states: dict[str, int] = {}
    checks: dict[str, int] = {}
    review_decisions: dict[str, int] = {}
    drafts = 0
    for e in entities.values():
        s = e.get("state", "")
        states[s] = states.get(s, 0) + 1
        c = e.get("checks", "")
        checks[c] = checks.get(c, 0) + 1
        rd = e.get("review_decision", "")
        review_decisions[rd] = review_decisions.get(rd, 0) + 1
        if e.get("is_draft"):
            drafts += 1
    return {
        "states": states,
        "checks": checks,
        "review_decisions": review_decisions,
        "drafts": drafts,
    }


def _classify_test_error(exc: Exception) -> tuple[str, str]:
    """Map an exception to a PROV-009 typed code + detail string."""
    if isinstance(exc, ValidationError):
        return "query_invalid", str(exc)
    if isinstance(exc, ServiceError):
        code = getattr(exc, "code", "") or ""
        if "unavailable" in code:
            return "unavailable", str(exc)
        if "refused" in code:
            return "scope_denied", str(exc)
        if "invalid" in code:
            return "query_invalid", str(exc)
        return "unavailable", str(exc)
    if isinstance(exc, (TimeoutError, OSError)):
        return "unavailable", str(exc)
    return "unavailable", str(exc)


@observe_service
class WatchService:
    """Facade over the graduated connector_watches table (SRS SS10)."""

    def __init__(
        self,
        db: Any,
        *,
        observer: PipelineObserver | None = None,
        snapshot_fetcher: Any | None = None,
    ) -> None:
        self._db = db
        self._repo = db.automations
        self._observer = observer or NullObserver()
        self._snapshot_fetcher = snapshot_fetcher

    # ── Guards ──────────────────────────────────────────────────────

    @staticmethod
    def _owner(principal: Principal) -> None:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_principal_required",
                "Watch operations require OWNER principal",
                context={"status": 403},
            )

    # ── Reads ───────────────────────────────────────────────────────

    def list_watches(
        self,
        principal: Principal,
        *,
        project_id: str | None = None,
        state: str | None = None,
        connector: str | None = None,
    ) -> list[dict[str, Any]]:
        """List watches with optional filters."""
        watches = self._repo.list_watches()
        if project_id is not None:
            watches = [w for w in watches if w.get("project_id") == project_id]
        if state is not None:
            watches = [w for w in watches if w.get("state") == state]
        if connector is not None:
            watches = [w for w in watches if w.get("connector_id") == connector]
        return watches

    def get_watch(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Get a watch with its full spec including rules."""
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        watch["rules"] = self._repo.list_rules(watch_id)
        return watch

    # ── Lifecycle ───────────────────────────────────────────────────

    def update_watch(
        self,
        principal: Principal,
        watch_id: str,
        *,
        name: str | None = None,
        intent: str | None = None,
        subject_kind: str | None = None,
        query: dict[str, Any] | None = None,
        trigger_kind: str | None = None,
        trigger: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a watch.  Material edits stale test/baseline (ACT-008).

        Material fields: subject_kind, query, trigger_kind, trigger.
        Non-material fields: name, intent.
        """
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)

        # Detect whether any material field is being changed.
        material_change = False
        provided: dict[str, Any] = {}
        if subject_kind is not None:
            provided["subject_kind"] = subject_kind
        if query is not None:
            provided["query"] = query
        if trigger_kind is not None:
            provided["trigger_kind"] = trigger_kind
        if trigger is not None:
            provided["trigger"] = trigger
        if any(k in _MATERIAL_FIELDS for k in provided):
            material_change = True

        # Apply non-material fields via graduated columns.
        spec_updates: dict[str, Any] = {}
        if intent is not None:
            spec_updates["intent"] = intent

        # Apply material fields.
        if subject_kind is not None:
            spec_updates["subject_kind"] = subject_kind
        if trigger_kind is not None:
            spec_updates["trigger_kind"] = trigger_kind
        if trigger is not None:
            spec_updates["trigger_json"] = json.dumps(
                trigger, sort_keys=True, separators=(",", ":"),
            )

        # Material edits: revision+1, stale test/baseline (ACT-008).
        if material_change:
            current_revision = int(watch.get("revision") or 0)
            spec_updates["revision"] = current_revision + 1
            spec_updates["test_state"] = "stale"
            spec_updates["baseline_state"] = "stale"

        # Write graduated columns.
        if spec_updates:
            self._repo.update_watch_spec(watch_id, **spec_updates)

        # Write original columns (name, query_json) that are not in
        # the graduation set.
        with self._repo._connection() as conn:
            if name is not None:
                conn.execute(
                    "UPDATE connector_watches SET name=?,updated_at=datetime('now') WHERE id=?",
                    (name.strip(), watch_id),
                )
            if query is not None:
                conn.execute(
                    "UPDATE connector_watches SET query_json=?,updated_at=datetime('now') WHERE id=?",
                    (json.dumps(query, sort_keys=True, separators=(",", ":")), watch_id),
                )

        return self.get_watch(principal, watch_id)

    def pause_watch(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Pause a watch (state='paused')."""
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        self._repo.update_watch_spec(watch_id, state="paused")
        return self.get_watch(principal, watch_id)

    def resume_watch(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Resume a paused watch (state='active')."""
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        self._repo.update_watch_spec(watch_id, state="active")
        return self.get_watch(principal, watch_id)

    def retire_watch(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Retire a watch (ACT-009).

        Stops future evaluation while retaining all rows, observations,
        evaluations, effects, and resulting history.
        """
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        self._repo.update_watch_spec(watch_id, state="retired")
        return self.get_watch(principal, watch_id)

    # ── Test ────────────────────────────────────────────────────────

    def test_watch(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Bounded, non-mutating read through the snapshot machinery (ACT-002).

        Fetches the current provider snapshot, normalises it, persists
        test_state and test_result_json.  Does NOT advance the baseline
        and does NOT emit events or trigger actions.

        Zero matches with a successful read = PASSED with
        'Test passed . 0 current matches' semantics (ACT-002).

        For github-family watches, the test_result carries every SS8.1
        field: provider, connection, repository, normalized query,
        entity count, up to 5 representative PRs, matched conditions,
        supported transitions, observation time, duration, and typed
        error/partial state (PROV-009).
        """
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        connector_id = watch.get("connector_id", "")
        query = watch.get("query") or {}

        t0 = time.monotonic()
        try:
            entities = self._fetch(principal, watch)
            snapshot = normalize_snapshot(connector_id, entities)
            entity_count = len(snapshot["entities"])
            representative = list(snapshot["entities"].values())[:5]
            duration_ms = int((time.monotonic() - t0) * 1000)

            test_result: dict[str, Any] = {
                "entity_count": entity_count,
                "representative_entities": representative,
                "observed_at": now,
                "duration_ms": duration_ms,
                "error": None,
                "message": f"Test passed · {entity_count} current matches",
            }

            # SS8.1: enrich github-family watches with the full display
            # payload.
            if connector_id == "gh":
                test_result["provider"] = "github"
                test_result["connection"] = (
                    watch.get("provider_connection_id") or ""
                )
                test_result["repository"] = query.get("repository", "")
                test_result["normalized_query"] = query
                test_result["matched_conditions"] = (
                    _github_conditions_summary(snapshot["entities"])
                )
                test_result["supported_transitions"] = list(
                    _GITHUB_TRANSITION_KINDS
                )

            test_state = "passed"
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            error_code, _error_detail = _classify_test_error(exc)

            test_result = {
                "entity_count": 0,
                "representative_entities": [],
                "observed_at": now,
                "duration_ms": duration_ms,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "code": error_code,
                },
                "message": f"Test failed: {exc}",
            }

            # SS8.1: github-family failures still carry provider context.
            if connector_id == "gh":
                test_result["provider"] = "github"
                test_result["connection"] = (
                    watch.get("provider_connection_id") or ""
                )
                test_result["repository"] = query.get("repository", "")
                test_result["normalized_query"] = query

            test_state = "failed"

        self._repo.update_watch_spec(
            watch_id,
            test_state=test_state,
            test_result_json=json.dumps(
                test_result, sort_keys=True, separators=(",", ":"),
            ),
            last_test_at=now,
        )

        return {
            "watch_id": watch_id,
            "test_state": test_state,
            "result": test_result,
        }

    # ── Baseline ────────────────────────────────────────────────────

    def baseline_watch(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Establish the baseline snapshot (ACT-005).

        Sets snapshot_json and baseline_state='established' WITHOUT
        emitting any events or transitions.  The service-event ledger
        MUST stay silent.
        """
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)

        try:
            snapshot = normalize_snapshot(
                watch["connector_id"], self._fetch(principal, watch),
            )
            # record_refresh with events=[] writes the snapshot without
            # creating any service events -- this IS the ACT-005 guarantee.
            self._repo.record_refresh(watch_id, snapshot, [])
        except Exception as exc:
            self._repo.record_refresh_error(watch_id, str(exc))
            raise

        # Mark the graduated baseline_state column.
        self._repo.update_watch_spec(watch_id, baseline_state="established")

        return {
            "watch_id": watch_id,
            "baseline_state": "established",
            "entity_count": len(snapshot["entities"]),
        }

    # ── Evaluate ────────────────────────────────────────────────────

    def evaluate_once(
        self,
        principal: Principal,
        watch_id: str,
    ) -> dict[str, Any]:
        """Manual evaluation: snapshot -> diff -> transitions -> observations.

        MANUAL only (P5 owns scheduling).  Fetches a fresh snapshot,
        diffs it against the stored baseline via diff_snapshots (which
        already speaks GitHub PR semantics: review/checks/head/state/
        merge), persists a watch_evaluations row, emits watch.transition
        observations via the 160 collector discipline (deterministic
        pobs_ IDs, evidence links, the project binding as source), and
        advances the baseline.

        Idempotent: UNIQUE(watch_id, watch_revision, source_revision)
        ensures the same source revision evaluates once.  Repeated
        identical snapshots produce zero new observations (WAT-006's
        spirit at the read level).
        """
        from holdspeak.project_contracts import generate_pobs_id
        from holdspeak.refs import format as format_ref

        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)

        connector_id = watch.get("connector_id", "")
        watch_revision = int(watch.get("revision") or 0)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # 1. Fetch fresh snapshot via the admitted adapter path.
        entities = self._fetch(principal, watch)
        snapshot = normalize_snapshot(connector_id, entities)

        # 2. Compute source_revision (deterministic hash of snapshot).
        snapshot_json_str = json.dumps(
            snapshot, sort_keys=True, separators=(",", ":"),
        )
        source_revision = hashlib.sha256(
            snapshot_json_str.encode("utf-8"),
        ).hexdigest()[:32]

        # 3. Idempotency: same (watch_id, watch_revision, source_revision)?
        existing = self._repo.find_evaluation_by_source(
            watch_id, watch_revision, source_revision,
        )
        if existing is not None:
            return {
                "watch_id": watch_id,
                "evaluation_id": existing["id"],
                "state": "no_op",
                "transitions": 0,
                "observation_ids": [],
                "message": "Identical snapshot already evaluated",
            }

        # 4. Diff against the stored baseline.
        baseline = watch.get("snapshot") or {}
        transitions = diff_snapshots(connector_id, baseline, snapshot)

        # 5. Persist: evaluation + observations + baseline in one txn.
        evaluation_id = f"weval_{uuid.uuid4().hex[:12]}"
        observation_ids: list[str] = []

        project_id = watch.get("project_id") or ""
        source_key = ""
        if project_id:
            sources = self._repo.list_project_sources(project_id)
            for s in sources:
                if s.get("source_ref") == f"watch:{watch_id}":
                    source_key = s.get("id", "")
                    break
        if not source_key:
            source_key = f"watch:{watch_id}"

        try:
            with self._db._connection() as conn:
                # 5a. Evaluation row.
                self._repo.create_evaluation_in_transaction(
                    conn,
                    evaluation_id=evaluation_id,
                    watch_id=watch_id,
                    watch_revision=watch_revision,
                    source_revision=source_revision,
                    trigger_kind="manual",
                    state="completed",
                    started_at=now,
                    completed_at=now,
                )

                # 5b. Observations for each transition (160 collector
                #     discipline: deterministic pobs_ IDs, watch.transition
                #     kind, canonical subject refs).
                if project_id and transitions:
                    for event in transitions:
                        entity_ref = event.get("entity_ref", "")
                        event_type = event.get("event_type", "")
                        facts = event.get("facts", {})
                        fact = {
                            "event_type": event_type,
                            "entity_ref": entity_ref,
                            "changed": facts.get("changed", {}),
                        }
                        fact_str = json.dumps(
                            fact, sort_keys=True, separators=(",", ":"),
                        )
                        content_hash = hashlib.sha256(
                            fact_str.encode("utf-8"),
                        ).hexdigest()[:32]

                        obs_id = generate_pobs_id(
                            adapter="watch",
                            source_id=source_key,
                            source_version=event.get("source_revision", ""),
                            fact_key=content_hash,
                        )

                        was_inserted = (
                            self._db.project_observations
                            .insert_observation_in_transaction(
                                conn,
                                observation_id=obs_id,
                                project_id=project_id,
                                source_id=source_key,
                                observation_kind="watch.transition",
                                subject_ref=format_ref("watch", watch_id),
                                source_version=event.get(
                                    "source_revision", "",
                                ),
                                observed_at=now,
                                fact_json=fact_str,
                                content_hash=content_hash,
                            )
                        )
                        if was_inserted:
                            observation_ids.append(obs_id)

                # 5c. Update evaluation with observation IDs.
                if observation_ids:
                    conn.execute(
                        "UPDATE watch_evaluations "
                        "SET observation_ids_json=? WHERE id=?",
                        (
                            json.dumps(
                                observation_ids, separators=(",", ":"),
                            ),
                            evaluation_id,
                        ),
                    )

                # 5d. Advance baseline (same snapshot write as
                #     record_refresh but inside the caller's transaction).
                conn.execute(
                    "UPDATE connector_watches "
                    "SET snapshot_json=?, last_success_at=datetime('now'), "
                    "last_error=NULL, updated_at=datetime('now') "
                    "WHERE id=?",
                    (snapshot_json_str, watch_id),
                )
        except sqlite3.IntegrityError:
            # S-3 counsel: TOCTOU on the UNIQUE(watch_id, watch_revision,
            # source_revision) constraint.  find_evaluation_by_source ran
            # outside the write transaction; a concurrent evaluation
            # inserted the row first.  Return the typed no_op result
            # exactly as if the idempotency check had caught it.
            existing = self._repo.find_evaluation_by_source(
                watch_id, watch_revision, source_revision,
            )
            if existing is not None:
                return {
                    "watch_id": watch_id,
                    "evaluation_id": existing["id"],
                    "state": "no_op",
                    "transitions": 0,
                    "observation_ids": [],
                    "message": "Identical snapshot already evaluated (concurrent)",
                }
            # If somehow the row still doesn't exist, re-raise.
            raise

        # 5e. Graduated columns (non-critical; outside the txn).
        self._repo.update_watch_spec(
            watch_id,
            baseline_state="established",
            last_evaluated_at=now,
        )

        return {
            "watch_id": watch_id,
            "evaluation_id": evaluation_id,
            "state": "completed",
            "transitions": len(transitions),
            "observation_ids": observation_ids,
            "message": (
                f"Evaluation complete: {len(transitions)} transitions, "
                f"{len(observation_ids)} observations"
            ),
        }

    # ── Rules ───────────────────────────────────────────────────────

    def set_rules(
        self,
        principal: Principal,
        watch_id: str,
        rules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Replace rules for a watch (replace-by-ordinal).

        Validates WatchCondition@1 and WatchAction@1 shapes.
        Rules are material -- changing them increments revision and
        stales test_state + baseline_state (ACT-008).
        """
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)

        # Validate all rules before any mutation.
        errors = validate_rules(rules)
        if errors:
            raise ValidationError(
                "Invalid watch rules",
                context={"errors": [str(e) for e in errors]},
            )

        # Delete existing rules and insert replacements.
        with self._repo._connection() as conn:
            conn.execute(
                "DELETE FROM watch_rules WHERE watch_id=?", (watch_id,),
            )

        created_rules: list[dict[str, Any]] = []
        for ordinal, rule in enumerate(rules):
            row = self._repo.create_rule(
                rule_id=_rule_id(),
                watch_id=watch_id,
                ordinal=ordinal,
                condition_schema="WatchCondition@1",
                condition_json=json.dumps(
                    rule["condition"], sort_keys=True, separators=(",", ":"),
                ),
                action_schema="WatchAction@1",
                action_json=json.dumps(
                    rule["actions"], sort_keys=True, separators=(",", ":"),
                ),
            )
            created_rules.append(row)

        # Material change: revision+1, stale test/baseline.
        current_revision = int(watch.get("revision") or 0)
        self._repo.update_watch_spec(
            watch_id,
            revision=current_revision + 1,
            test_state="stale",
            baseline_state="stale",
        )

        return {
            "watch_id": watch_id,
            "rules": created_rules,
            "revision": current_revision + 1,
        }

    # ── Fetch seam ──────────────────────────────────────────────────

    def _fetch(
        self,
        principal: Principal,
        watch: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Reuse ReactionService._fetch's seam (same snapshot_fetcher
        callable or the same default import path).  No duplication of
        the provider fetch logic.
        """
        if self._snapshot_fetcher is not None:
            return self._snapshot_fetcher(
                principal,
                connector_id=watch["connector_id"],
                query_kind=watch["query_kind"],
                query=watch["query"],
            )
        from holdspeak.services.watch_sources import fetch_watch_snapshot

        return fetch_watch_snapshot(
            principal,
            connector_id=watch["connector_id"],
            query_kind=watch["query_kind"],
            query=watch["query"],
        )
