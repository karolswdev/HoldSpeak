"""Persistence for Project Delta: observations, evidence links, proposals, reviews.

HS-160-01: the evidence schema repo helpers.  Named-column inserts, gets,
lists, and conn-accepting transaction variants for the four tables introduced
in schema v69 (§5.5-5.8).

Placement rationale: projects.py owns the Project aggregate and HS-158
items/changes/commands (~900 lines).  Delta is a focused sub-domain with
its own append-only / deterministic-identity discipline and will grow its
own service callers (evidence collector, delta service, review accept
transaction).  A separate module keeps each file navigable and avoids a
1 400-line projects.py.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseRepository


class DeltaRepository(BaseRepository):
    """Observations, evidence links, proposals, and review windows."""

    table = "project_observations"  # registration anchor

    # ── project_observations (§5.5, DB-003) ─────────────────────────────

    def insert_observation(
        self,
        *,
        observation_id: str,
        project_id: str,
        source_id: str,
        observation_kind: str,
        subject_ref: Optional[str] = None,
        source_version: str = "",
        observed_at: str,
        captured_at: Optional[str] = None,
        fact_json: str = "{}",
        content_hash: str = "",
        supersedes_observation_id: Optional[str] = None,
        coverage_state: str = "",
    ) -> bool:
        """Insert an observation with INSERT OR IGNORE semantics.

        Returns True if a row was inserted, False if it already existed
        (same deterministic pobs_ ID).  The caller gets a clean no-op
        signal on adapter retries.
        """
        with self._connection() as conn:
            return self._insert_observation(
                conn,
                observation_id=observation_id,
                project_id=project_id,
                source_id=source_id,
                observation_kind=observation_kind,
                subject_ref=subject_ref,
                source_version=source_version,
                observed_at=observed_at,
                captured_at=captured_at,
                fact_json=fact_json,
                content_hash=content_hash,
                supersedes_observation_id=supersedes_observation_id,
                coverage_state=coverage_state,
            )

    def insert_observation_in_transaction(
        self,
        conn: Any,
        *,
        observation_id: str,
        project_id: str,
        source_id: str,
        observation_kind: str,
        subject_ref: Optional[str] = None,
        source_version: str = "",
        observed_at: str,
        captured_at: Optional[str] = None,
        fact_json: str = "{}",
        content_hash: str = "",
        supersedes_observation_id: Optional[str] = None,
        coverage_state: str = "",
    ) -> bool:
        """Insert an observation on a caller-owned connection.

        The caller is responsible for transaction boundaries.
        Returns True if inserted, False on deterministic-ID collision.
        """
        return self._insert_observation(
            conn,
            observation_id=observation_id,
            project_id=project_id,
            source_id=source_id,
            observation_kind=observation_kind,
            subject_ref=subject_ref,
            source_version=source_version,
            observed_at=observed_at,
            captured_at=captured_at,
            fact_json=fact_json,
            content_hash=content_hash,
            supersedes_observation_id=supersedes_observation_id,
            coverage_state=coverage_state,
        )

    @staticmethod
    def _insert_observation(
        conn: Any,
        *,
        observation_id: str,
        project_id: str,
        source_id: str,
        observation_kind: str,
        subject_ref: Optional[str],
        source_version: str,
        observed_at: str,
        captured_at: Optional[str],
        fact_json: str,
        content_hash: str,
        supersedes_observation_id: Optional[str],
        coverage_state: str,
    ) -> bool:
        now_iso = captured_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        cur = conn.execute(
            """INSERT OR IGNORE INTO project_observations
               (id, project_id, source_id, observation_kind, subject_ref,
                source_version, observed_at, captured_at, fact_json,
                content_hash, supersedes_observation_id, coverage_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(observation_id).strip(),
                str(project_id).strip(),
                str(source_id).strip(),
                str(observation_kind).strip(),
                subject_ref,
                source_version,
                observed_at,
                now_iso,
                fact_json,
                content_hash,
                supersedes_observation_id,
                coverage_state,
            ),
        )
        return bool(cur.rowcount)

    def get_observation(self, observation_id: str) -> Optional[dict[str, Any]]:
        """Load a single observation by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_observations WHERE id = ?",
                (str(observation_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def list_observations(
        self,
        project_id: str,
        *,
        source_id: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List observations for a project, optionally filtered by source."""
        clean_pid = str(project_id).strip()
        if source_id:
            rows = self._execute_read(
                "SELECT * FROM project_observations "
                "WHERE project_id = ? AND source_id = ? "
                "ORDER BY observed_at DESC LIMIT ?",
                (clean_pid, str(source_id).strip(), max(1, int(limit))),
            )
        else:
            rows = self._execute_read(
                "SELECT * FROM project_observations "
                "WHERE project_id = ? "
                "ORDER BY observed_at DESC LIMIT ?",
                (clean_pid, max(1, int(limit))),
            )
        return [dict(r) for r in rows]

    # ── project_evidence_links (§5.6) ───────────────────────────────────

    def insert_evidence_link(
        self,
        *,
        link_id: str,
        project_id: str,
        target_ref: str,
        evidence_ref: str,
        relation: str = "",
        observation_id: Optional[str] = None,
        excerpt_locator_json: Optional[str] = None,
    ) -> None:
        """Insert an evidence link."""
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO project_evidence_links
                   (id, project_id, target_ref, evidence_ref, relation,
                    observation_id, excerpt_locator_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(link_id).strip(),
                    str(project_id).strip(),
                    str(target_ref).strip(),
                    str(evidence_ref).strip(),
                    str(relation).strip(),
                    observation_id,
                    excerpt_locator_json,
                ),
            )

    def get_evidence_link(self, link_id: str) -> Optional[dict[str, Any]]:
        """Load a single evidence link by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_evidence_links WHERE id = ?",
                (str(link_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def list_evidence_links(
        self,
        project_id: str,
        *,
        target_ref: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List evidence links for a project, optionally by target ref."""
        clean_pid = str(project_id).strip()
        if target_ref:
            rows = self._execute_read(
                "SELECT * FROM project_evidence_links "
                "WHERE project_id = ? AND target_ref = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (clean_pid, str(target_ref).strip(), max(1, int(limit))),
            )
        else:
            rows = self._execute_read(
                "SELECT * FROM project_evidence_links "
                "WHERE project_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (clean_pid, max(1, int(limit))),
            )
        return [dict(r) for r in rows]

    # ── project_proposals (§5.7) ────────────────────────────────────────

    def insert_proposal(
        self,
        *,
        proposal_id: str,
        project_id: str,
        review_window_key: str = "",
        proposal_kind: str = "",
        target_ref: str = "",
        title: str = "",
        rationale: Optional[str] = None,
        patch_json: str = "{}",
        materiality: Optional[str] = None,
        confidence: Optional[float] = None,
        producer_kind: Optional[str] = None,
        model_receipt_ref: Optional[str] = None,
        lifecycle: str = "open",
        deferred_until: Optional[str] = None,
        dismissal_basis_hash: Optional[str] = None,
    ) -> None:
        """Insert a proposal."""
        with self._connection() as conn:
            self._insert_proposal(
                conn,
                proposal_id=proposal_id,
                project_id=project_id,
                review_window_key=review_window_key,
                proposal_kind=proposal_kind,
                target_ref=target_ref,
                title=title,
                rationale=rationale,
                patch_json=patch_json,
                materiality=materiality,
                confidence=confidence,
                producer_kind=producer_kind,
                model_receipt_ref=model_receipt_ref,
                lifecycle=lifecycle,
                deferred_until=deferred_until,
                dismissal_basis_hash=dismissal_basis_hash,
            )

    def insert_proposal_in_transaction(
        self,
        conn: Any,
        *,
        proposal_id: str,
        project_id: str,
        review_window_key: str = "",
        proposal_kind: str = "",
        target_ref: str = "",
        title: str = "",
        rationale: Optional[str] = None,
        patch_json: str = "{}",
        materiality: Optional[str] = None,
        confidence: Optional[float] = None,
        producer_kind: Optional[str] = None,
        model_receipt_ref: Optional[str] = None,
        lifecycle: str = "open",
        deferred_until: Optional[str] = None,
        dismissal_basis_hash: Optional[str] = None,
    ) -> None:
        """Insert a proposal on a caller-owned connection."""
        self._insert_proposal(
            conn,
            proposal_id=proposal_id,
            project_id=project_id,
            review_window_key=review_window_key,
            proposal_kind=proposal_kind,
            target_ref=target_ref,
            title=title,
            rationale=rationale,
            patch_json=patch_json,
            materiality=materiality,
            confidence=confidence,
            producer_kind=producer_kind,
            model_receipt_ref=model_receipt_ref,
            lifecycle=lifecycle,
            deferred_until=deferred_until,
            dismissal_basis_hash=dismissal_basis_hash,
        )

    @staticmethod
    def _insert_proposal(
        conn: Any,
        *,
        proposal_id: str,
        project_id: str,
        review_window_key: str,
        proposal_kind: str,
        target_ref: str,
        title: str,
        rationale: Optional[str],
        patch_json: str,
        materiality: Optional[str],
        confidence: Optional[float],
        producer_kind: Optional[str],
        model_receipt_ref: Optional[str],
        lifecycle: str,
        deferred_until: Optional[str],
        dismissal_basis_hash: Optional[str],
    ) -> None:
        conn.execute(
            """INSERT INTO project_proposals
               (id, project_id, review_window_key, proposal_kind, target_ref,
                title, rationale, patch_json, materiality, confidence,
                producer_kind, model_receipt_ref, lifecycle,
                deferred_until, dismissal_basis_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(proposal_id).strip(),
                str(project_id).strip(),
                review_window_key,
                proposal_kind,
                target_ref,
                title,
                rationale,
                patch_json,
                materiality,
                confidence,
                producer_kind,
                model_receipt_ref,
                lifecycle,
                deferred_until,
                dismissal_basis_hash,
            ),
        )

    def update_proposal_in_transaction(
        self,
        conn: Any,
        proposal_id: str,
        *,
        lifecycle: Optional[str] = None,
        decided_at: Optional[str] = None,
        decided_by_ref: Optional[str] = None,
        deferred_until: Optional[str] = None,
        dismissal_basis_hash: Optional[str] = None,
    ) -> None:
        """Update mutable proposal fields on a caller-owned connection."""
        updates: list[str] = []
        params: list[Any] = []
        if lifecycle is not None:
            updates.append("lifecycle = ?")
            params.append(lifecycle)
        if decided_at is not None:
            updates.append("decided_at = ?")
            params.append(decided_at)
        if decided_by_ref is not None:
            updates.append("decided_by_ref = ?")
            params.append(decided_by_ref)
        if deferred_until is not None:
            updates.append("deferred_until = ?")
            params.append(deferred_until)
        if dismissal_basis_hash is not None:
            updates.append("dismissal_basis_hash = ?")
            params.append(dismissal_basis_hash)
        if not updates:
            return
        params.append(str(proposal_id).strip())
        conn.execute(
            f"UPDATE project_proposals SET {', '.join(updates)} WHERE id = ?",
            params,
        )

    def get_proposal(self, proposal_id: str) -> Optional[dict[str, Any]]:
        """Load a single proposal by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_proposals WHERE id = ?",
                (str(proposal_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def list_proposals(
        self,
        project_id: str,
        *,
        review_window_key: Optional[str] = None,
        lifecycle: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List proposals for a project, optionally filtered."""
        clean_pid = str(project_id).strip()
        clauses = ["project_id = ?"]
        params: list[Any] = [clean_pid]
        if review_window_key is not None:
            clauses.append("review_window_key = ?")
            params.append(review_window_key)
        if lifecycle is not None:
            clauses.append("lifecycle = ?")
            params.append(lifecycle)
        params.append(max(1, int(limit)))
        rows = self._execute_read(
            f"SELECT * FROM project_proposals "
            f"WHERE {' AND '.join(clauses)} "
            f"ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        )
        return [dict(r) for r in rows]

    # ── project_reviews (§5.8) ──────────────────────────────────────────

    def insert_review(
        self,
        *,
        review_id: str,
        project_id: str,
        status: str = "open",
        from_sequence: Optional[int] = None,
        through_sequence: Optional[int] = None,
        source_manifest_json: str = "{}",
        project_revision_opened: Optional[int] = None,
        project_revision_accepted: Optional[int] = None,
        opened_at: Optional[str] = None,
        accepted_at: Optional[str] = None,
        accepted_by_ref: Optional[str] = None,
        summary_json: Optional[str] = None,
    ) -> None:
        """Insert a review window."""
        now_iso = opened_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connection() as conn:
            self._insert_review(
                conn,
                review_id=review_id,
                project_id=project_id,
                status=status,
                from_sequence=from_sequence,
                through_sequence=through_sequence,
                source_manifest_json=source_manifest_json,
                project_revision_opened=project_revision_opened,
                project_revision_accepted=project_revision_accepted,
                opened_at=now_iso,
                accepted_at=accepted_at,
                accepted_by_ref=accepted_by_ref,
                summary_json=summary_json,
            )

    def insert_review_in_transaction(
        self,
        conn: Any,
        *,
        review_id: str,
        project_id: str,
        status: str = "open",
        from_sequence: Optional[int] = None,
        through_sequence: Optional[int] = None,
        source_manifest_json: str = "{}",
        project_revision_opened: Optional[int] = None,
        project_revision_accepted: Optional[int] = None,
        opened_at: Optional[str] = None,
        accepted_at: Optional[str] = None,
        accepted_by_ref: Optional[str] = None,
        summary_json: Optional[str] = None,
    ) -> None:
        """Insert a review window on a caller-owned connection."""
        now_iso = opened_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._insert_review(
            conn,
            review_id=review_id,
            project_id=project_id,
            status=status,
            from_sequence=from_sequence,
            through_sequence=through_sequence,
            source_manifest_json=source_manifest_json,
            project_revision_opened=project_revision_opened,
            project_revision_accepted=project_revision_accepted,
            opened_at=now_iso,
            accepted_at=accepted_at,
            accepted_by_ref=accepted_by_ref,
            summary_json=summary_json,
        )

    @staticmethod
    def _insert_review(
        conn: Any,
        *,
        review_id: str,
        project_id: str,
        status: str,
        from_sequence: Optional[int],
        through_sequence: Optional[int],
        source_manifest_json: str,
        project_revision_opened: Optional[int],
        project_revision_accepted: Optional[int],
        opened_at: str,
        accepted_at: Optional[str],
        accepted_by_ref: Optional[str],
        summary_json: Optional[str],
    ) -> None:
        conn.execute(
            """INSERT INTO project_reviews
               (id, project_id, status, from_sequence, through_sequence,
                source_manifest_json, project_revision_opened,
                project_revision_accepted, opened_at, accepted_at,
                accepted_by_ref, summary_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(review_id).strip(),
                str(project_id).strip(),
                status,
                from_sequence,
                through_sequence,
                source_manifest_json,
                project_revision_opened,
                project_revision_accepted,
                opened_at,
                accepted_at,
                accepted_by_ref,
                summary_json,
            ),
        )

    def update_review_in_transaction(
        self,
        conn: Any,
        review_id: str,
        *,
        status: Optional[str] = None,
        through_sequence: Optional[int] = None,
        project_revision_accepted: Optional[int] = None,
        accepted_at: Optional[str] = None,
        accepted_by_ref: Optional[str] = None,
        summary_json: Optional[str] = None,
    ) -> None:
        """Update mutable review fields on a caller-owned connection."""
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if through_sequence is not None:
            updates.append("through_sequence = ?")
            params.append(through_sequence)
        if project_revision_accepted is not None:
            updates.append("project_revision_accepted = ?")
            params.append(project_revision_accepted)
        if accepted_at is not None:
            updates.append("accepted_at = ?")
            params.append(accepted_at)
        if accepted_by_ref is not None:
            updates.append("accepted_by_ref = ?")
            params.append(accepted_by_ref)
        if summary_json is not None:
            updates.append("summary_json = ?")
            params.append(summary_json)
        if not updates:
            return
        params.append(str(review_id).strip())
        conn.execute(
            f"UPDATE project_reviews SET {', '.join(updates)} WHERE id = ?",
            params,
        )

    def get_review(self, review_id: str) -> Optional[dict[str, Any]]:
        """Load a single review by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_reviews WHERE id = ?",
                (str(review_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def list_reviews(
        self,
        project_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List reviews for a project, optionally filtered by status."""
        clean_pid = str(project_id).strip()
        if status:
            rows = self._execute_read(
                "SELECT * FROM project_reviews "
                "WHERE project_id = ? AND status = ? "
                "ORDER BY opened_at DESC LIMIT ?",
                (clean_pid, str(status).strip(), max(1, int(limit))),
            )
        else:
            rows = self._execute_read(
                "SELECT * FROM project_reviews "
                "WHERE project_id = ? "
                "ORDER BY opened_at DESC LIMIT ?",
                (clean_pid, max(1, int(limit))),
            )
        return [dict(r) for r in rows]

    # ── HS-160-04: decision + recurrence helpers ────────────────────────

    def list_dismissed_proposals(
        self,
        project_id: str,
        *,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """List dismissed proposals for a project (DEL-003 recurrence)."""
        rows = self._execute_read(
            "SELECT * FROM project_proposals "
            "WHERE project_id = ? AND lifecycle = 'dismissed' "
            "ORDER BY decided_at DESC LIMIT ?",
            (str(project_id).strip(), max(1, int(limit))),
        )
        return [dict(r) for r in rows]

    def list_deferred_proposals(
        self,
        project_id: str,
        *,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """List deferred proposals for a project (DEL-004 return law)."""
        rows = self._execute_read(
            "SELECT * FROM project_proposals "
            "WHERE project_id = ? AND lifecycle = 'deferred' "
            "ORDER BY decided_at DESC LIMIT ?",
            (str(project_id).strip(), max(1, int(limit))),
        )
        return [dict(r) for r in rows]

    def get_proposal_in_transaction(
        self,
        conn: Any,
        proposal_id: str,
    ) -> Optional[dict[str, Any]]:
        """Load a single proposal by ID within a caller-owned connection."""
        row = conn.execute(
            "SELECT * FROM project_proposals WHERE id = ?",
            (str(proposal_id).strip(),),
        ).fetchone()
        if not row:
            return None
        return dict(row)

    # ── internal helpers ────────────────────────────────────────────────

    def _execute_read(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list:
        """Convenience: execute a read query and return all rows."""
        with self._connection() as conn:
            return conn.execute(sql, params).fetchall()
