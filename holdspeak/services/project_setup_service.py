"""HS-159-03: ProjectSetupService -- durable interview, deterministic
native suggestions, and atomic finalization.

SRS traceability
----------------
- INT-001..006: durable setup session lifecycle
- INT-004: original text preserved separately from normalized
- INT-005: autosave + resume at every stage
- INT-007/008: suggestions conditioned on real desk facts
- INT-010: deterministic native suggestions (not inference fallback)
- ACT-003: failed/untested proposals refused from activation
- ACT-004: one-transaction finalize (Project + Watches + sources)
- ACT-005: baseline established without events (ledger silence)
- PROV-011: never invent subjects
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import (
    CommandResultEnvelope,
    ResultKind,
    generate_pcmd_id,
    generate_psrc_id,
)
from holdspeak.refs import format as format_ref, parse as parse_ref

# HS-168-02: a minimal OWNER principal used only for the connection
# annotation projection (list_tools reads persisted state, never probes).
_ANNOTATION_PRINCIPAL = Principal(PrincipalKind.OWNER, "setup-annotation")
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.watch_validation import validate_rules


# ── Stage machine (SRS SS5) ───────────────────────────────────────────
#
#  active(outcome -> signals -> proposals -> review)
#      -> completed | abandoned | expired
#
# Each stage implies all prior answers exist.  advance_stage is
# monotonic within the 'active' state; get_setup rehydrates at the
# latest stage.

STAGES = ("outcome", "signals", "proposals", "review")
_STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}

SESSION_STATES = ("active", "completed", "abandoned", "expired")

# How long an untouched session remains valid.
SESSION_TTL = timedelta(hours=24)

# ── Question IDs (SRS SS4.1) ──────────────────────────────────────────

Q_OUTCOME = "outcome"
Q_SIGNALS = "signals"
Q_JIRA_SCOPE = "jira_scope"  # HS-167-02: persisted Jira scope toggles

# ── Cadence presets (SRS SS4.1) ───────────────────────────────────────

CADENCE_PRESETS: dict[str, dict[str, Any]] = {
    "active_work": {"kind": "poll", "every_minutes": 15},
    "normal": {"kind": "poll", "every_minutes": 35},
    "daily": {"kind": "poll", "every_minutes": 1440},
    "weekdays": {"kind": "poll", "every_minutes": 1440, "weekdays_only": True},
}

# ── Native subject kinds (SRS SS8.3) ─────────────────────────────────

NATIVE_SUBJECT_KINDS = frozenset({
    "meetings", "decisions", "door", "evidence",
})

# Maximum proposals generated per suggest() call (legacy; kept for reference).
_MAX_PROPOSALS = 8

# HS-168-02: per-provider cap so every connected provider keeps its top cards.
# 5 GitHub + 5 Jira templates exist; cap at 4 per provider guarantees every
# connected provider's top cards survive (a 3-native + 4-GitHub + 4-Jira = 11
# desk persists cards for ALL THREE).  The value is 4 because each provider
# has 5 templates and 4 is the tightest top that keeps the list usable
# without starving any provider.
_MAX_PROPOSALS_PER_PROVIDER = 4


def _apply_per_provider_cap(
    proposals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply a per-provider cap and reorder: connected providers first, native LAST.

    Each provider keeps at most ``_MAX_PROPOSALS_PER_PROVIDER`` proposals.
    Order within a provider is preserved (the templates' original order).
    The output puts github and jira proposals before native ones (the D7b
    fold fix) so that provider cards are visible above the fold at 393.
    """
    buckets: dict[str, list[dict[str, Any]]] = {}
    for p in proposals:
        pid = p.get("provider_id", "native")
        if pid not in buckets:
            buckets[pid] = []
        if len(buckets[pid]) < _MAX_PROPOSALS_PER_PROVIDER:
            buckets[pid].append(p)

    # Connected providers first, native LAST
    result: list[dict[str, Any]] = []
    for pid in ("github", "jira"):
        result.extend(buckets.pop(pid, []))
    # Any other provider we might have in the future
    for pid in sorted(buckets):
        if pid != "native":
            result.extend(buckets.pop(pid, []))
    # Native last
    result.extend(buckets.pop("native", []))
    return result


def _session_id() -> str:
    return f"psetup_{uuid.uuid4().hex[:12]}"


def _proposal_id() -> str:
    return f"wprop_{uuid.uuid4().hex[:12]}"


def _answer_id() -> str:
    return f"pans_{uuid.uuid4().hex[:12]}"


def _watch_id() -> str:
    return f"watch_{uuid.uuid4().hex[:12]}"


class ProjectSetupService:
    """Durable interview compiler: two questions, real suggestions,
    one atomic finalize (SRS SS10, INT-001..012).
    """

    def __init__(
        self,
        db: Any,
        *,
        project_service: Any | None = None,
        watch_service: Any | None = None,
        github_adapter: Any | None = None,
        jira_adapter: Any | None = None,
        connections_service: Any | None = None,
    ) -> None:
        self._db = db
        self._repo = db.automations
        self._project_service = project_service
        self._watch_service = watch_service
        self._github_adapter = github_adapter
        self._jira_adapter = jira_adapter
        self._connections_service = connections_service
        self._issue_test_calls: int = 0  # HS-166-04: set by _native_test_read

    # ── Guards ──────────────────────────────────────────────────────

    @staticmethod
    def _owner(principal: Principal) -> None:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_principal_required",
                "Setup operations require OWNER principal",
                context={"status": 403},
            )

    # ── Session lifecycle ──────────────────────────────────────────

    def start_setup(
        self,
        principal: Principal,
    ) -> dict[str, Any]:
        """Start a durable setup session (INT-001, INT-005).

        Returns the session dict with state='active', stage='outcome'.
        """
        self._owner(principal)
        session_id = _session_id()
        expires_at = (
            datetime.now(timezone.utc) + SESSION_TTL
        ).isoformat(timespec="seconds")

        return self._repo.create_setup_session(
            session_id=session_id,
            state="active",
            stage="outcome",
            draft_schema="ProjectSetup@1",
            expires_at=expires_at,
        )

    def get_setup(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """Full rehydration: session + latest-revision answers + proposals
        (INT-005 resume seam).

        Honors expires_at: an expired session transitions to 'expired'
        on read and returns in that state.
        """
        session = self._require_session(session_id)

        # Expiry check
        if session["state"] == "active" and session.get("expires_at"):
            try:
                exp = datetime.fromisoformat(session["expires_at"])
                # Ensure TZ-aware comparison
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > exp:
                    self._update_session(session_id, state="expired")
                    session["state"] = "expired"
            except (ValueError, TypeError):
                pass

        # Answers: latest revision per question_id
        all_answers = self._repo.list_setup_answers(session_id)
        latest_answers: dict[str, dict[str, Any]] = {}
        for ans in all_answers:
            qid = ans["question_id"]
            if qid not in latest_answers or ans["revision"] > latest_answers[qid]["revision"]:
                latest_answers[qid] = ans

        # Proposals (HS-168-02: annotated with connection readiness)
        proposals = self._list_proposals(session_id)
        self._annotate_proposals_with_connection(proposals)

        # HS-168-02: known scopes from answers
        known_scopes = self._extract_known_scopes(latest_answers, proposals)

        return {
            **session,
            "answers": latest_answers,
            "proposals": proposals,
            "known_scopes": known_scopes,
        }

    def answer(
        self,
        principal: Principal,
        session_id: str,
        question_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Record an answer (append-only with revision, INT-004).

        Preserves ``original`` text separately from ``normalized``.
        Advances stage per the SS5 machine.
        """
        self._owner(principal)
        session = self._require_active(session_id)

        if question_id not in (Q_OUTCOME, Q_SIGNALS, Q_JIRA_SCOPE):
            raise ValidationError(
                f"Unknown question_id: {question_id!r}",
                code="validation",
            )

        # Compute next revision
        existing_answers = self._repo.list_setup_answers(session_id)
        current_rev = 0
        for ans in existing_answers:
            if ans["question_id"] == question_id:
                current_rev = max(current_rev, ans["revision"])
        next_rev = current_rev + 1

        # INT-004: preserve original and normalized separately.
        # HS-167-02: jira_scope rides the same shape -- the scope JSON
        # string is the text, stored as original=normalized for symmetry.
        answer_data = {
            "original": payload.get("original", payload.get("text", "")),
            "normalized": payload.get("normalized", payload.get("text", "")),
        }

        result = self._repo.create_setup_answer(
            answer_id=_answer_id(),
            session_id=session_id,
            question_id=question_id,
            answer_schema="SetupAnswer@1",
            answer_json=json.dumps(answer_data, ensure_ascii=False),
            revision=next_rev,
        )

        # Advance stage
        new_stage = self._advance_stage(session, question_id)
        if new_stage != session["stage"]:
            self._update_session(session_id, stage=new_stage)

        return result

    def suggest(
        self,
        principal: Principal,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Deterministic native suggestions from real desk facts (INT-010).

        Scans meetings, decisions, door/follow-through items for
        subjects worth watching.  Each proposal is a WatchSpec@1-shaped
        draft.  A desk with no facts yields zero proposals -- the Blank
        path forward (INT-002).  Never invents subjects (PROV-011).
        """
        self._owner(principal)
        session = self._require_active(session_id)

        # Gather desk facts from native sources
        proposals: list[dict[str, Any]] = []

        # 1. Recent meetings (desk-wide)
        try:
            meeting_summaries = self._db.meetings.list_meetings(limit=10)
            if meeting_summaries:
                proposals.append(self._meetings_proposal(
                    session_id, meeting_summaries,
                ))
        except Exception:
            pass  # Degraded: no meetings

        # 2. Decisions with lifecycle 'accepted' (review candidates)
        try:
            decisions = self._db.decisions.list(limit=20)
            review_due = [
                d for d in decisions
                if d.lifecycle == "accepted"
            ]
            if review_due:
                proposals.append(self._decisions_proposal(
                    session_id, review_due,
                ))
        except Exception:
            pass  # Degraded: no decisions

        # 3. Door/follow-through: overdue items
        try:
            from holdspeak.services.follow_through_service import FollowThroughService
            ft_svc = FollowThroughService(self._db)
            board = ft_svc.board(principal)
            overdue_items = board.overdue
            if overdue_items:
                proposals.append(self._door_proposal(
                    session_id, overdue_items, "overdue",
                ))
        except Exception:
            pass  # Degraded: no follow-through

        # 4. Door/follow-through: stale items (waiting lane)
        try:
            from holdspeak.services.follow_through_service import FollowThroughService
            ft_svc = FollowThroughService(self._db)
            board = ft_svc.board(principal)
            waiting_items = board.waiting
            stale_items = [c for c in waiting_items if c.stale_score and c.stale_score > 0.5]
            if stale_items:
                proposals.append(self._door_proposal(
                    session_id, stale_items, "stale",
                ))
        except Exception:
            pass  # Degraded: no follow-through stale

        # 5. GitHub template candidates (HS-161-02, INT-007)
        #    Appear ONLY when the provider is genuinely connected.
        #    Disconnected/unauthenticated => NO github candidates at all
        #    (SETFLOW-004 spirit: no grey theater).
        if self._github_adapter is not None:
            try:
                gh_proposals = self._github_candidates(principal, session_id)
                proposals.extend(gh_proposals)
            except Exception:
                pass  # Degraded: no github candidates

        # HS-166-03: Jira template candidates (beside GitHub)
        if self._jira_adapter is not None:
            try:
                jira_proposals = self._jira_candidates(principal, session_id)
                proposals.extend(jira_proposals)
            except Exception:
                pass  # Degraded: no jira candidates

        # HS-168-02: per-provider cap so every connected provider keeps its
        # top cards (the D2 cap fix).  Order: connected providers first,
        # native LAST (the D7b fold fix).
        capped = _apply_per_provider_cap(proposals)

        # Persist proposals (capped per provider)
        persisted: list[dict[str, Any]] = []
        for p in capped:
            row = self._repo.create_setup_proposal(
                proposal_id=p["id"],
                session_id=session_id,
                provider_id=p["provider_id"],
                spec_schema="WatchSpec@1",
                spec_json=json.dumps(p["spec"], sort_keys=True, separators=(",", ":")),
                rationale_json=json.dumps(p["rationale"], ensure_ascii=False),
                state="proposed",
            )
            persisted.append(row)

        # Advance to proposals stage
        if session["stage"] in ("outcome", "signals"):
            self._update_session(session_id, stage="proposals")

        # HS-168-02: annotate proposals with connection readiness
        self._annotate_proposals_with_connection(persisted, principal)

        return persisted

    # ── Proposal operations ────────────────────────────────────────

    def select_proposal(
        self,
        principal: Principal,
        session_id: str,
        proposal_id: str,
    ) -> dict[str, Any]:
        """Select a proposal for activation (proposed -> selected)."""
        self._owner(principal)
        self._require_active(session_id)
        proposal = self._require_proposal(proposal_id, session_id)

        if proposal["state"] not in ("proposed", "selected"):
            raise ValidationError(
                f"Cannot select proposal in state {proposal['state']!r}",
                code="validation",
            )

        self._update_proposal(proposal_id, state="selected")
        return self._repo.get_setup_proposal(proposal_id) or {}

    def deselect_proposal(
        self,
        principal: Principal,
        session_id: str,
        proposal_id: str,
    ) -> dict[str, Any]:
        """Deselect a proposal (selected -> proposed)."""
        self._owner(principal)
        self._require_active(session_id)
        proposal = self._require_proposal(proposal_id, session_id)

        if proposal["state"] != "selected":
            raise ValidationError(
                f"Cannot deselect proposal in state {proposal['state']!r}",
                code="validation",
            )

        self._update_proposal(proposal_id, state="proposed")
        return self._repo.get_setup_proposal(proposal_id) or {}

    def clarify_proposal(
        self,
        principal: Principal,
        session_id: str,
        proposal_id: str,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        """Bounded edit to a proposal: cadence, action, scope narrowing."""
        self._owner(principal)
        self._require_active(session_id)
        proposal = self._require_proposal(proposal_id, session_id)

        # Load current spec and apply edits
        spec = proposal.get("spec") or {}
        if isinstance(spec, str):
            spec = json.loads(spec)

        if "cadence" in patch:
            cadence_key = patch["cadence"]
            if cadence_key in CADENCE_PRESETS:
                spec["trigger"] = CADENCE_PRESETS[cadence_key]
            elif isinstance(cadence_key, dict):
                spec["trigger"] = cadence_key

        if "action" in patch:
            spec["action"] = patch["action"]

        if "scope" in patch:
            if "subject" not in spec:
                spec["subject"] = {}
            spec["subject"]["scope"] = patch["scope"]

        self._update_proposal(
            proposal_id,
            spec_json=json.dumps(spec, sort_keys=True, separators=(",", ":")),
        )
        return self._repo.get_setup_proposal(proposal_id) or {}

    def test_proposal(
        self,
        principal: Principal,
        session_id: str,
        proposal_id: str,
    ) -> dict[str, Any]:
        """Run the native bounded read for a proposal's subject (ACT-002).

        For native subjects, reuses the desk read seams. A meetings-subject
        test returns current matching meetings. Zero matches with a
        successful read = passed (ACT-002 zero-match honesty).
        """
        self._owner(principal)
        self._require_active(session_id)
        proposal = self._require_proposal(proposal_id, session_id)

        spec = proposal.get("spec") or {}
        if isinstance(spec, str):
            spec = json.loads(spec)

        subject_kind = spec.get("subject", {}).get("kind", "")
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        import time as _time
        t0 = _time.monotonic()
        try:
            entities = self._native_test_read(principal, subject_kind, spec)
            entity_count = len(entities)
            duration_ms = int((_time.monotonic() - t0) * 1000)
            test_result: dict[str, Any] = {
                "entity_count": entity_count,
                "representative_entities": entities[:5],
                "observed_at": now_iso,
                "duration_ms": duration_ms,
                "error": None,
                "message": f"Test passed -- {entity_count} current matches",
            }

            # HS-166-04: enrich jira issue test results with the
            # display contract (same keys WatchService SS8.2 emits).
            if subject_kind == "issue":
                query = spec.get("subject", {}).get("query", {})
                scope_obj = spec.get("subject", {}).get("scope", {})
                conn_ref = query.get("connection_ref", scope_obj.get("connection_ref", ""))
                site = conn_ref.split("|")[0] if "|" in conn_ref else ""
                email = conn_ref.split("|")[1] if "|" in conn_ref else ""
                from holdspeak.services.watch_sources import _compile_jql
                from holdspeak.services.watch_service import (
                    _jira_conditions_summary, _JIRA_TRANSITION_KINDS,
                )
                from holdspeak.services.reaction_service import normalize_snapshot
                normalized = normalize_snapshot("jira", entities)
                test_result["provider"] = "jira"
                test_result["connection"] = {
                    "site": site, "email": email,
                    "connection_ref": conn_ref,
                }
                test_result["projects"] = scope_obj.get("projects", [])
                test_result["normalized_jql"] = (
                    _compile_jql(query) if query else ""
                )
                test_result["matched_conditions"] = (
                    _jira_conditions_summary(normalized["entities"])
                )
                test_result["supported_transitions"] = list(
                    _JIRA_TRANSITION_KINDS
                )
                test_result["calls"] = self._issue_test_calls

            test_state = "passed"
        except Exception as exc:
            duration_ms = int((_time.monotonic() - t0) * 1000)
            test_result = {
                "entity_count": 0,
                "representative_entities": [],
                "observed_at": now_iso,
                "duration_ms": duration_ms,
                "error": {"type": type(exc).__name__, "message": str(exc)},
                "message": f"Test failed: {exc}",
            }
            test_state = "failed"

        self._update_proposal(
            proposal_id,
            test_state=test_state,
            test_result_json=json.dumps(
                test_result, sort_keys=True, separators=(",", ":"),
            ),
        )

        return {
            "proposal_id": proposal_id,
            "test_state": test_state,
            "result": test_result,
        }

    # ── Finalize ───────────────────────────────────────────────────

    def finalize(
        self,
        principal: Principal,
        session_id: str,
        *,
        command_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomic finalization (ACT-004).

        ONE transaction via ProjectService.create_from_setup():
        - Create Project (name from outcome, lifecycle=active)
        - Activate only selected+passed proposals as WatchSpec@1
        - Create watch_rules + project_sources bindings
        - Baseline established WITHOUT events (ACT-005)
        - Mark session completed

        All-or-nothing: failure rolls back everything, leaving
        a recoverable 'active' session (INT-006).

        Blank: finalize with zero selected proposals is lawful (INT-002).
        """
        self._owner(principal)

        # S-1 belt: if the session already carries a project_id, a
        # previous finalize committed but the caller retried (crash
        # recovery, duplicate request).  Return the existing project
        # with no_change instead of creating a duplicate (API-002
        # honest-replay spirit).
        session = self._require_session(session_id)
        if session.get("project_id"):
            return {
                "result_kind": ResultKind.NO_CHANGE.value,
                "project_id": session["project_id"],
                "activated_watches": [],
                "refused_proposals": [],
            }

        if session["state"] != "active":
            raise ServiceError(
                "session_not_active",
                f"Setup session {session_id} is {session['state']}, not active",
                context={"status": 409, "state": session["state"]},
            )

        if self._project_service is None:
            raise ServiceError(
                "project_service_missing",
                "ProjectSetupService requires a composed ProjectService",
            )

        # Gather answers for Project fields
        answers = self._latest_answers(session_id)
        outcome_answer = answers.get(Q_OUTCOME, {})
        outcome_text = outcome_answer.get("answer", {}).get("normalized", "")
        original_text = outcome_answer.get("answer", {}).get("original", "")

        # Infer project name from outcome (WEB-CR-002: editable)
        project_name = outcome_text[:80].strip() or "New Project"

        # Gather selected + passed proposals for activation
        proposals = self._list_proposals(session_id)
        selected = [
            p for p in proposals
            if p["state"] == "selected" and p.get("test_state") == "passed"
        ]
        refused = [
            p for p in proposals
            if p["state"] == "selected" and p.get("test_state") != "passed"
        ]

        # Compose the setup payload
        setup_payload = {
            "name": project_name,
            "purpose": original_text,
            "outcome_text": outcome_text,
            "lifecycle": "active",
            "proposals": selected,
            "session_id": session_id,
        }

        cmd_id = command_id or generate_pcmd_id()

        # Delegate to ProjectService.create_from_setup (one transaction).
        # session_id travels so session completion is atomic with the
        # project creation (S-1: no duplicate-project hazard).
        result = self._project_service.create_from_setup(
            principal,
            setup_payload,
            command_id=cmd_id,
            session_id=session_id,
        )

        # HS-166-05: populate baseline snapshots AFTER the transaction
        # commits. ACT-005 says baseline WITHOUT events -- it does NOT
        # say baseline without a snapshot. An empty snapshot_json causes
        # the first evaluate_due to "discover" everything and fire false
        # effects from nothing.
        activated = result.get("activated_watches", [])
        if activated and self._watch_service is not None:
            for aw in activated:
                wid = aw.get("watch_id", "")
                if not wid:
                    continue
                try:
                    self._watch_service.baseline_watch(principal, wid)
                except Exception:
                    # Fetch failed -- degrade to pending so evaluate_due
                    # knows the baseline is not real.
                    try:
                        self._watch_service._repo.update_watch_spec(
                            wid, baseline_state="pending",
                        )
                    except Exception:
                        pass

        # Attach refused proposals info
        result["refused_proposals"] = [
            {"id": p["id"], "test_state": p.get("test_state", "")}
            for p in refused
        ]

        return result

    # ── Abandon / expire ───────────────────────────────────────────

    def abandon(
        self,
        principal: Principal,
        session_id: str,
    ) -> dict[str, Any]:
        """Abandon a setup session (INT-006: no Project ever)."""
        self._owner(principal)
        self._require_active(session_id)
        self._update_session(session_id, state="abandoned")
        return self._repo.get_setup_session(session_id) or {}

    # ── Native suggestion builders ─────────────────────────────────

    def _meetings_proposal(
        self,
        session_id: str,
        meetings: list[Any],
    ) -> dict[str, Any]:
        """Build a meetings Watch proposal from real desk meetings."""
        meeting_ids = [
            m.id if hasattr(m, "id") else m.get("id", "")
            for m in meetings[:5]
        ]
        meeting_titles = [
            m.title if hasattr(m, "title") else m.get("title", "")
            for m in meetings[:3]
        ]
        return {
            "id": _proposal_id(),
            "provider_id": "native",
            "spec": {
                "schema": "WatchSpec@1",
                "name": "Meeting activity",
                "intent": "Watch associated meetings for new content",
                "provider": {"id": "native", "transport": "local_domain"},
                "subject": {
                    "kind": "meetings",
                    "scope": {"meeting_ids": meeting_ids},
                },
                "trigger": CADENCE_PRESETS["normal"],
                "rules": [{
                    "condition": {
                        "schema": "WatchCondition@1",
                        "operator": "any",
                        "clauses": [
                            {"field": "content", "comparison": "changed"},
                        ],
                    },
                    "actions": [
                        {"schema": "WatchAction@1", "kind": "project.observe"},
                    ],
                }],
                "action": {"schema": "WatchAction@1", "kind": "project.observe"},
                "mode": "yolo",
            },
            "rationale": {
                "fact": f"{len(meetings)} recent meetings",
                "detail": f"Meetings: {', '.join(meeting_titles[:3])}",
                "subject_count": len(meetings),
            },
        }

    def _decisions_proposal(
        self,
        session_id: str,
        decisions: list[Any],
    ) -> dict[str, Any]:
        """Build a decisions Watch proposal from real desk decisions."""
        decision_ids = [
            d.id if hasattr(d, "id") else d.get("id", "")
            for d in decisions[:5]
        ]
        decision_texts = [
            d.text if hasattr(d, "text") else d.get("text", "")
            for d in decisions[:3]
        ]
        return {
            "id": _proposal_id(),
            "provider_id": "native",
            "spec": {
                "schema": "WatchSpec@1",
                "name": "Decision review due",
                "intent": "Watch for decisions needing review",
                "provider": {"id": "native", "transport": "local_domain"},
                "subject": {
                    "kind": "decisions",
                    "scope": {"decision_ids": decision_ids},
                },
                "trigger": CADENCE_PRESETS["daily"],
                "rules": [{
                    "condition": {
                        "schema": "WatchCondition@1",
                        "operator": "any",
                        "clauses": [
                            {"field": "lifecycle", "comparison": "equals", "value": "accepted"},
                        ],
                    },
                    "actions": [
                        {"schema": "WatchAction@1", "kind": "project.observe"},
                    ],
                }],
                "action": {"schema": "WatchAction@1", "kind": "project.observe"},
                "mode": "yolo",
            },
            "rationale": {
                "fact": f"{len(decisions)} decisions pending review",
                "detail": f"Decisions: {', '.join(t[:40] for t in decision_texts[:3])}",
                "subject_count": len(decisions),
            },
        }

    def _door_proposal(
        self,
        session_id: str,
        cards: list[Any],
        flavor: str,
    ) -> dict[str, Any]:
        """Build a door/follow-through Watch proposal from real desk items."""
        card_ids = [c.id for c in cards[:5]]
        card_texts = [c.text for c in cards[:3]]
        name = "Overdue commitments" if flavor == "overdue" else "Stale follow-through"
        intent = (
            "Watch for overdue action items"
            if flavor == "overdue"
            else "Watch for stale follow-through items"
        )
        field = "due" if flavor == "overdue" else "stale_score"
        comparison = "older_than" if flavor == "overdue" else "greater_than"
        value = "7d" if flavor == "overdue" else 0.5
        return {
            "id": _proposal_id(),
            "provider_id": "native",
            "spec": {
                "schema": "WatchSpec@1",
                "name": name,
                "intent": intent,
                "provider": {"id": "native", "transport": "local_domain"},
                "subject": {
                    "kind": "door",
                    "scope": {"card_ids": card_ids},
                },
                "trigger": CADENCE_PRESETS["daily"],
                "rules": [{
                    "condition": {
                        "schema": "WatchCondition@1",
                        "operator": "any",
                        "clauses": [
                            {"field": field, "comparison": comparison, "value": value},
                        ],
                    },
                    "actions": [
                        {"schema": "WatchAction@1", "kind": "project.observe"},
                    ],
                }],
                "action": {"schema": "WatchAction@1", "kind": "project.observe"},
                "mode": "yolo",
            },
            "rationale": {
                "fact": f"{len(cards)} {flavor} items",
                "detail": f"Items: {', '.join(t[:40] for t in card_texts[:3])}",
                "subject_count": len(cards),
            },
        }

    # ── GitHub candidate builder (HS-161-02) ───────────────────────

    def _github_candidates(
        self,
        principal: Principal,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Build GitHub Watch candidates from connected adapter (INT-007).

        Returns candidates ONLY when connection_status says connected.
        Each candidate mirrors the native candidate shape (INT-008):
        source/scope/conditions/action/cadence/readiness/rationale.
        PROV-011: candidates carry needs-scope state -- no invented repos.
        """
        from holdspeak.github_templates import GITHUB_TEMPLATES
        from holdspeak.services.github_provider import STATE_CONNECTED

        adapter = self._github_adapter
        if adapter is None:
            return []

        status = adapter.connection_status(principal)
        if status.get("state") != STATE_CONNECTED:
            return []

        candidates: list[dict[str, Any]] = []
        for tmpl in GITHUB_TEMPLATES:
            # PROV-011: no repo scope yet -- candidate carries needs_scope
            # The interview's clarify step will fill the repo scope.
            spec = {
                "schema": "WatchSpec@1",
                "name": tmpl.name,
                "intent": tmpl.intent,
                "provider": {
                    "id": "github",
                    "transport": "connector_pack",
                },
                "subject": {
                    "kind": "pull_request",
                    "scope": {},  # needs-scope: filled by clarify
                    "query": dict(tmpl.query_defaults),
                },
                "trigger": CADENCE_PRESETS.get(tmpl.cadence_preset, CADENCE_PRESETS["normal"]),
                "rules": tmpl.rules,
                "action": tmpl.rules[0]["actions"][0] if tmpl.rules else {},
                "mode": "yolo",
            }

            account = status.get("display", {}).get("account", "")
            candidates.append({
                "id": _proposal_id(),
                "provider_id": "github",
                "spec": spec,
                "rationale": {
                    "source": "github",
                    "template_id": tmpl.template_id,
                    "fact": f"GitHub connected as {account}" if account else "GitHub connected",
                    "detail": tmpl.intent,
                    "subject_count": 0,
                    "readiness": "needs_scope",
                    "conditions": [
                        c.get("comparison", "") for clause in tmpl.rules
                        for c in clause.get("condition", {}).get("clauses", [])
                    ],
                    "cadence": tmpl.cadence_preset,
                    "action": tmpl.rules[0]["actions"][0].get("kind", "") if tmpl.rules else "",
                },
            })

        return candidates

    # ── Clarify: repo-scope step (HS-161-02) ──────────────────────

    def clarify_repo_scope(
        self,
        principal: Principal,
        session_id: str,
        proposal_id: str,
        *,
        repo: str | None = None,
    ) -> dict[str, Any]:
        """Clarify the repo scope for a GitHub proposal (INT-009).

        Two paths:
        1. Discovered list: adapter.discover() enumerates repos
        2. Typed fallback: adapter.validate_repo() checks one repo

        PROV-011: a candidate never names a repo the adapter did not
        surface/validate.
        """
        self._owner(principal)
        self._require_active(session_id)
        proposal = self._require_proposal(proposal_id, session_id)

        adapter = self._github_adapter
        if adapter is None:
            raise ServiceError(
                "github_adapter_missing",
                "GitHub adapter not configured",
            )

        if repo is not None:
            # Typed fallback: validate the specific repo
            validation = adapter.validate_repo(principal, repo)
            if not validation.get("valid"):
                return {
                    "proposal_id": proposal_id,
                    "scope_state": "invalid",
                    "error": validation.get("error_detail", "Repository validation failed"),
                    "repositories": [],
                }
            repositories = [repo]
        else:
            # Discovered list: enumerate accessible repos
            discovery = adapter.discover(principal)
            if discovery.get("state") not in ("ready", "partial"):
                return {
                    "proposal_id": proposal_id,
                    "scope_state": "discovery_failed",
                    "error": discovery.get("error_detail", "Discovery failed"),
                    "repositories": [],
                }
            repositories = [item["id"] for item in discovery.get("items", [])]
            if not repositories:
                return {
                    "proposal_id": proposal_id,
                    "scope_state": "empty",
                    "error": None,
                    "repositories": [],
                }

        # Apply the repo scope to the proposal spec
        spec = proposal.get("spec") or {}
        if isinstance(spec, str):
            spec = json.loads(spec)

        if "subject" not in spec:
            spec["subject"] = {}
        spec["subject"]["scope"] = {"repositories": repositories}

        # Re-validate rules after scope application
        rationale = proposal.get("rationale") or {}
        if isinstance(rationale, str):
            rationale = json.loads(rationale)
        rationale["readiness"] = "scoped"
        rationale["subject_count"] = len(repositories)

        self._update_proposal(
            proposal_id,
            spec_json=json.dumps(spec, sort_keys=True, separators=(",", ":")),
            rationale_json=json.dumps(rationale, ensure_ascii=False),
        )

        return {
            "proposal_id": proposal_id,
            "scope_state": "scoped",
            "error": None,
            "repositories": repositories,
        }

    # ── Jira candidates (HS-166-03, beside _github_candidates) ─────

    def _jira_candidates(
        self,
        principal: Principal,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Build Jira Watch candidates from connected adapter (INT-007).

        Returns candidates ONLY when at least one Jira connection is
        connected.  PROV-011: candidates carry needs_scope state --
        no invented projects.
        """
        from holdspeak.jira_templates import JIRA_TEMPLATES
        from holdspeak.services.jira_provider import STATE_CONNECTED

        adapter = self._jira_adapter
        if adapter is None:
            return []

        # Check if any connection is connected
        connections = adapter.list_connections(principal)
        connected = [
            c for c in connections
            if c.get("state") == STATE_CONNECTED
        ]
        if not connected:
            return []

        # Use the first connected connection's ref
        first_ref = connected[0].get("connection_ref", connected[0].get("external_connection_ref", ""))

        candidates: list[dict[str, Any]] = []
        for tmpl in JIRA_TEMPLATES:
            spec = {
                "schema": "WatchSpec@1",
                "name": tmpl.name,
                "intent": tmpl.intent,
                "provider": {
                    "id": "jira",
                    "transport": "connector_pack",
                    "connection_ref": first_ref,
                },
                "subject": {
                    "kind": "issue",
                    "scope": {},  # needs-scope: filled by clarify
                    "query": dict(tmpl.query_defaults),
                },
                "trigger": CADENCE_PRESETS.get(tmpl.cadence_preset, CADENCE_PRESETS["normal"]),
                "rules": tmpl.rules,
                "action": tmpl.rules[0]["actions"][0] if tmpl.rules else {},
                "mode": "yolo",
            }

            candidates.append({
                "id": _proposal_id(),
                "provider_id": "jira",
                "spec": spec,
                "rationale": {
                    "source": "jira",
                    "template_id": tmpl.template_id,
                    "fact": f"Jira connected ({first_ref})",
                    "detail": tmpl.intent,
                    "subject_count": 0,
                    "readiness": "needs_scope",
                    "conditions": [
                        c.get("comparison", "") for clause in tmpl.rules
                        for c in clause.get("condition", {}).get("clauses", [])
                    ],
                    "cadence": tmpl.cadence_preset,
                    "action": tmpl.rules[0]["actions"][0].get("kind", "") if tmpl.rules else "",
                },
            })

        return candidates

    # ── Clarify: jira-scope step (HS-166-03) ──────────────────────

    def clarify_jira_scope(
        self,
        principal: Principal,
        session_id: str,
        proposal_id: str,
        *,
        connection_ref: str | None = None,
        projects: list[str] | None = None,
        issue_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Clarify the Jira scope for a Jira proposal.

        Validates the project via adapter.validate_scope.
        PROV-011: never invents projects.
        """
        self._owner(principal)
        self._require_active(session_id)
        proposal = self._require_proposal(proposal_id, session_id)

        adapter = self._jira_adapter
        if adapter is None:
            raise ServiceError(
                "jira_adapter_missing",
                "Jira adapter not configured",
            )

        ref = connection_ref or ""
        validated_projects: list[str] = []

        if projects:
            for proj_key in projects:
                validation = adapter.validate_scope(principal, ref, proj_key)
                if not validation.get("valid"):
                    return {
                        "proposal_id": proposal_id,
                        "scope_state": "invalid",
                        "error": validation.get("error_detail", "Project validation failed"),
                        "projects": [],
                    }
                validated_projects.append(proj_key)
        else:
            # Discover projects
            discovery = adapter.discover(principal, ref, kind="projects")
            if discovery.get("state") not in ("ready", "partial"):
                return {
                    "proposal_id": proposal_id,
                    "scope_state": "discovery_failed",
                    "error": discovery.get("error_detail", "Discovery failed"),
                    "projects": [],
                }
            validated_projects = [item.get("key", item.get("id", "")) for item in discovery.get("items", [])]
            if not validated_projects:
                return {
                    "proposal_id": proposal_id,
                    "scope_state": "empty",
                    "error": None,
                    "projects": [],
                }

        # Apply the scope to the proposal spec
        spec = proposal.get("spec") or {}
        if isinstance(spec, str):
            spec = json.loads(spec)

        if "subject" not in spec:
            spec["subject"] = {}
        spec["subject"]["scope"] = {
            "connection_ref": ref,
            "projects": validated_projects,
            "issue_types": issue_types or [],
        }
        # Also put connection_ref into the query for the source
        if "query" not in spec["subject"]:
            spec["subject"]["query"] = {}
        spec["subject"]["query"]["connection_ref"] = ref

        rationale = proposal.get("rationale") or {}
        if isinstance(rationale, str):
            rationale = json.loads(rationale)
        rationale["readiness"] = "scoped"
        rationale["subject_count"] = len(validated_projects)

        self._update_proposal(
            proposal_id,
            spec_json=json.dumps(spec, sort_keys=True, separators=(",", ":")),
            rationale_json=json.dumps(rationale, ensure_ascii=False),
        )

        return {
            "proposal_id": proposal_id,
            "scope_state": "scoped",
            "error": None,
            "projects": validated_projects,
        }

    # ── Native test reads (reuse desk seams) ───────────────────────

    def _native_test_read(
        self,
        principal: Principal,
        subject_kind: str,
        spec: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Bounded non-mutating read for a native subject kind.

        Returns a list of entity dicts.  The read reuses the same seams
        the suggestion builder used to discover the facts.
        """
        if subject_kind == "meetings":
            scope = spec.get("subject", {}).get("scope", {})
            meeting_ids = scope.get("meeting_ids", [])
            if meeting_ids:
                results = []
                for mid in meeting_ids[:10]:
                    try:
                        meeting = self._db.meetings.get_meeting(mid)
                        if meeting:
                            results.append({
                                "id": meeting.id,
                                "title": meeting.title,
                                "started_at": meeting.started_at.isoformat()
                                if meeting.started_at else None,
                            })
                    except Exception:
                        pass
                return results
            # No specific IDs: list recent
            meetings = self._db.meetings.list_meetings(limit=5)
            return [
                {"id": m.id, "title": m.title,
                 "started_at": m.started_at.isoformat()
                 if m.started_at else None}
                for m in meetings
            ]

        if subject_kind == "decisions":
            scope = spec.get("subject", {}).get("scope", {})
            decision_ids = scope.get("decision_ids", [])
            if decision_ids:
                results = []
                for did in decision_ids[:10]:
                    try:
                        decision = self._db.decisions.get(did)
                        if decision:
                            results.append(decision.to_dict())
                    except Exception:
                        pass
                return results
            decisions = self._db.decisions.list(limit=5)
            return [d.to_dict() for d in decisions]

        if subject_kind == "door":
            from holdspeak.services.follow_through_service import FollowThroughService
            ft_svc = FollowThroughService(self._db)
            board = ft_svc.board(principal)
            items = board.overdue + board.now
            return [
                {"id": c.id, "text": c.text, "owner": c.owner,
                 "due": c.due, "lane": c.lane}
                for c in items[:10]
            ]

        if subject_kind == "evidence":
            # Evidence silence: no native read path yet
            return []

        if subject_kind == "pull_request":
            # HS-161-04: GitHub PR subjects test through the adapter's
            # snapshot path -- a real bounded read returning representative
            # PRs (id/title/state/head_sha), not validation placeholders.
            from holdspeak.services.reaction_service import normalize_snapshot

            adapter = self._github_adapter
            if adapter is None:
                raise ValidationError(
                    "GitHub adapter not configured for pull_request test",
                    code="validation",
                )
            scope = spec.get("subject", {}).get("scope", {})
            repos = scope.get("repositories", [])
            if not repos:
                return []
            # Build the spec subset adapter.snapshot expects:
            # query_kind + query with repository (the first scoped repo).
            snapshot_spec = {
                "query_kind": "pull_requests",
                "query": {"repository": repos[0]},
            }
            raw_entities = adapter.snapshot(principal, snapshot_spec)
            # Normalize through the same path WatchService uses so the
            # representative entities carry id/title/state/head_sha.
            normalized = normalize_snapshot("gh", raw_entities)
            return list(normalized.get("entities", {}).values())[:5]

        if subject_kind == "issue":
            # HS-166-04: Jira issue subjects test through the adapter's
            # search + enrichment path, mirroring JiraWatchSource.snapshot.
            adapter = self._jira_adapter
            if adapter is None:
                raise ValidationError(
                    "Jira adapter not configured for issue test",
                    code="validation",
                )
            scope = spec.get("subject", {}).get("scope", {})
            query = spec.get("subject", {}).get("query", {})
            conn_ref = query.get("connection_ref", "")
            if not conn_ref:
                conn_ref = scope.get("connection_ref", "")
            projects = scope.get("projects", [])
            if not conn_ref:
                self._issue_test_calls = 0
                return []
            # Build JQL from the spec query using the watch_sources compiler.
            # Merge scope.projects into query so _compile_jql includes them.
            from holdspeak.services.watch_sources import _compile_jql
            merged_query = dict(query)
            if projects and "projects" not in merged_query:
                merged_query["projects"] = projects
            jql = _compile_jql(merged_query) if merged_query else ""
            if not jql and projects:
                jql = f"project IN ({', '.join(projects)})"
            if not jql:
                self._issue_test_calls = 0
                return []
            limit = max(1, min(int(query.get("limit") or 50), 200))
            result = adapter.search(
                principal, conn_ref,
                jql=jql, limit=limit, enrich=True,
            )
            items = result.get("items", [])
            self._issue_test_calls = result.get("calls", 1)
            return items[:5]

        raise ValidationError(
            f"Unknown native subject kind: {subject_kind!r}",
            code="validation",
        )

    # ── HS-168-02: connection annotation + known scopes ─────────────

    def _annotate_proposals_with_connection(
        self,
        proposals: list[dict[str, Any]],
        principal: Principal | None = None,
    ) -> None:
        """Inject ``connection: {state, account}`` on every proposal.

        A computed projection at serialization time -- NOT a column.
        When the connections service is None (e.g. unit tests with
        no service wired), proposals carry no annotation.
        """
        if self._connections_service is None:
            return

        # Build a provider_id -> tool entry cache (one call per read)
        p = principal if principal is not None else _ANNOTATION_PRINCIPAL
        try:
            result = self._connections_service.list_tools(p)
            tool_map: dict[str, dict[str, Any]] = {
                t["provider_id"]: t for t in result.get("tools", [])
            }
        except Exception:
            return

        for p in proposals:
            pid = p.get("provider_id", "native")
            tool = tool_map.get(pid)
            if tool is not None:
                p["connection"] = {
                    "state": tool.get("state"),
                    "account": tool.get("account"),
                }

    @staticmethod
    def _extract_known_scopes(
        answers: dict[str, dict[str, Any]],
        proposals: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Build the known_scopes projection from recorded answers.

        Known scopes are recorded by clarify_repo_scope (github) and
        clarify_jira_scope (jira) on the session's answers JSON.  They
        are recorded as question_id entries with structured payloads.

        The face OFFERS them; the service NEVER applies one to another
        proposal.
        """
        github_scopes: list[dict[str, Any]] = []
        jira_scopes: list[dict[str, Any]] = []

        # Walk proposals and read their committed scope from the spec
        for p in proposals:
            pid = p.get("provider_id", "")
            spec = p.get("spec") or {}
            if isinstance(spec, str):
                try:
                    spec = json.loads(spec)
                except Exception:
                    continue

            subject = spec.get("subject", {})
            scope = subject.get("scope", {})

            if pid == "github" and scope.get("repositories"):
                repos = scope["repositories"]
                if repos:
                    # Record the first repository as the known scope
                    watch_name = spec.get("name", "")
                    github_scopes.append({
                        "repository": repos[0] if isinstance(repos, list) else str(repos),
                        "for_proposal_id": p.get("id", ""),
                        "watch_name": watch_name,
                    })
            elif pid == "jira":
                # Check for jira scope data in the provider section or scope
                provider = spec.get("provider", {})
                conn_ref = provider.get("connection_ref", "")
                projects = scope.get("projects", [])
                if conn_ref and projects:
                    site = ""
                    if "|" in conn_ref:
                        site = conn_ref.split("|", 1)[0]
                    watch_name = spec.get("name", "")
                    for pk in projects:
                        jira_scopes.append({
                            "project_key": pk if isinstance(pk, str) else str(pk),
                            "site": site,
                            "for_proposal_id": p.get("id", ""),
                            "watch_name": watch_name,
                        })

        return {"github": github_scopes, "jira": jira_scopes}

    # ── Internal helpers ───────────────────────────────────────────

    def _require_session(self, session_id: str) -> dict[str, Any]:
        session = self._repo.get_setup_session(session_id)
        if not session:
            raise NotFound("setup_session", session_id)
        return session

    def _require_active(self, session_id: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        if session["state"] != "active":
            raise ServiceError(
                "session_not_active",
                f"Setup session {session_id} is {session['state']}, not active",
                context={"status": 409, "state": session["state"]},
            )
        return session

    def _require_proposal(
        self, proposal_id: str, session_id: str,
    ) -> dict[str, Any]:
        proposal = self._repo.get_setup_proposal(proposal_id)
        if not proposal:
            raise NotFound("setup_proposal", proposal_id)
        if proposal["session_id"] != session_id:
            raise NotFound("setup_proposal", proposal_id)
        return proposal

    def _latest_answers(self, session_id: str) -> dict[str, dict[str, Any]]:
        """Return the latest-revision answer per question_id."""
        all_answers = self._repo.list_setup_answers(session_id)
        latest: dict[str, dict[str, Any]] = {}
        for ans in all_answers:
            qid = ans["question_id"]
            if qid not in latest or ans["revision"] > latest[qid]["revision"]:
                latest[qid] = ans
        return latest

    def _list_proposals(self, session_id: str) -> list[dict[str, Any]]:
        """List all proposals for a session."""
        with self._repo._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM watch_setup_proposals WHERE session_id=? "
                "ORDER BY created_at",
                (session_id,),
            ).fetchall()
        return [self._repo._payload(row, "spec", "rationale", "test_result") for row in rows]

    def _update_session(self, session_id: str, **fields: Any) -> None:
        """Update session fields."""
        sets: list[str] = []
        params: list[Any] = []
        for col, val in fields.items():
            sets.append(f"{col}=?")
            params.append(val)
        if not sets:
            return
        sets.append("updated_at=datetime('now')")
        if "state" in fields and fields["state"] == "completed":
            sets.append("completed_at=datetime('now')")
        params.append(session_id)
        with self._repo._connection() as conn:
            conn.execute(
                f"UPDATE project_setup_sessions SET {','.join(sets)} WHERE id=?",
                params,
            )

    def _update_proposal(self, proposal_id: str, **fields: Any) -> None:
        """Update proposal fields."""
        sets: list[str] = []
        params: list[Any] = []
        for col, val in fields.items():
            sets.append(f"{col}=?")
            params.append(val)
        if not sets:
            return
        sets.append("updated_at=datetime('now')")
        params.append(proposal_id)
        with self._repo._connection() as conn:
            conn.execute(
                f"UPDATE watch_setup_proposals SET {','.join(sets)} WHERE id=?",
                params,
            )

    def _advance_stage(
        self,
        session: dict[str, Any],
        question_id: str,
    ) -> str:
        """Compute the next stage after an answer."""
        current = session["stage"]
        if question_id == Q_OUTCOME and current == "outcome":
            return "signals"
        if question_id == Q_SIGNALS and current in ("outcome", "signals"):
            return "proposals"
        return current
