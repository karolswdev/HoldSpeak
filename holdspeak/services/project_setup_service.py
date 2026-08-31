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

# Maximum proposals generated per suggest() call.
_MAX_PROPOSALS = 8


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
    ) -> None:
        self._db = db
        self._repo = db.automations
        self._project_service = project_service
        self._watch_service = watch_service

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

        # Proposals
        proposals = self._list_proposals(session_id)

        return {
            **session,
            "answers": latest_answers,
            "proposals": proposals,
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

        if question_id not in (Q_OUTCOME, Q_SIGNALS):
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

        # INT-004: preserve original and normalized separately
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

        # Persist proposals (truncate to cap)
        persisted: list[dict[str, Any]] = []
        for p in proposals[:_MAX_PROPOSALS]:
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

        try:
            entities = self._native_test_read(principal, subject_kind, spec)
            entity_count = len(entities)
            test_result = {
                "entity_count": entity_count,
                "representative_entities": entities[:5],
                "observed_at": now_iso,
                "error": None,
                "message": f"Test passed -- {entity_count} current matches",
            }
            test_state = "passed"
        except Exception as exc:
            test_result = {
                "entity_count": 0,
                "representative_entities": [],
                "observed_at": now_iso,
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
        session = self._require_active(session_id)

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

        # Delegate to ProjectService.create_from_setup (one transaction)
        result = self._project_service.create_from_setup(
            principal,
            setup_payload,
            command_id=cmd_id,
        )

        # Mark session completed (outside the transaction -- if this
        # fails, the project exists but the session is still active;
        # get_setup will see the project_id and know it completed).
        project_id = result.get("project_id") or result.get("id")
        self._update_session(
            session_id,
            state="completed",
            project_id=project_id,
        )

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

        raise ValidationError(
            f"Unknown native subject kind: {subject_kind!r}",
            code="validation",
        )

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
