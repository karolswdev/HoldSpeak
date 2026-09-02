"""Persistence for Project Updates (§8, UPD-004).

HS-162-01: the update ledger schema repo helpers.  Named-column inserts,
gets, lists, and conn-accepting transaction variants for project_updates.

Placement rationale: delta.py owns observations/proposals/reviews (the
evidence sub-domain).  Updates are a focused sub-domain with their own
lifecycle discipline (draft -> published -> immutable; supersede replaces
an unaccepted draft).  A separate module keeps each file navigable.

Lifecycle law (UPD-004):
- A published update is IMMUTABLE: any write (update/supersede) is refused.
- Superseding marks the old draft superseded and creates draft_revision+1
  in ONE transaction.
- Publishing sets lifecycle='published' + published_at.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseRepository


class PublishedUpdateError(Exception):
    """Raised when a write is attempted against a published update."""


class UpdatesRepository(BaseRepository):
    """Project updates: drafts, publishing, and the lifecycle law."""

    table = "project_updates"  # registration anchor

    # ── insert (create draft) ──────────────────────────────────────────

    def insert_update(
        self,
        *,
        update_id: str,
        project_id: str,
        project_revision: int,
        review_id: Optional[str] = None,
        draft_revision: int = 1,
        body_md: str = "",
        claims_json: str = "{}",
        source_manifest_json: str = "{}",
        generator: str = "deterministic",
    ) -> None:
        """Insert a new draft update."""
        with self._connection() as conn:
            self._insert_update(
                conn,
                update_id=update_id,
                project_id=project_id,
                project_revision=project_revision,
                review_id=review_id,
                draft_revision=draft_revision,
                body_md=body_md,
                claims_json=claims_json,
                source_manifest_json=source_manifest_json,
                generator=generator,
            )

    def insert_update_in_transaction(
        self,
        conn: Any,
        *,
        update_id: str,
        project_id: str,
        project_revision: int,
        review_id: Optional[str] = None,
        draft_revision: int = 1,
        body_md: str = "",
        claims_json: str = "{}",
        source_manifest_json: str = "{}",
        generator: str = "deterministic",
    ) -> None:
        """Insert a new draft update on a caller-owned connection."""
        self._insert_update(
            conn,
            update_id=update_id,
            project_id=project_id,
            project_revision=project_revision,
            review_id=review_id,
            draft_revision=draft_revision,
            body_md=body_md,
            claims_json=claims_json,
            source_manifest_json=source_manifest_json,
            generator=generator,
        )

    @staticmethod
    def _insert_update(
        conn: Any,
        *,
        update_id: str,
        project_id: str,
        project_revision: int,
        review_id: Optional[str],
        draft_revision: int,
        body_md: str,
        claims_json: str,
        source_manifest_json: str,
        generator: str,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id,
                lifecycle, draft_revision, body_md, claims_json,
                source_manifest_json, generator, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(update_id).strip(),
                str(project_id).strip(),
                int(project_revision),
                review_id,
                int(draft_revision),
                body_md,
                claims_json,
                source_manifest_json,
                generator,
                now_iso,
                now_iso,
            ),
        )

    # ── get / list ─────────────────────────────────────────────────────

    def get_update(self, update_id: str) -> Optional[dict[str, Any]]:
        """Load a single update by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_updates WHERE id = ?",
                (str(update_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def get_update_in_transaction(
        self,
        conn: Any,
        update_id: str,
    ) -> Optional[dict[str, Any]]:
        """Load a single update by ID within a caller-owned connection."""
        row = conn.execute(
            "SELECT * FROM project_updates WHERE id = ?",
            (str(update_id).strip(),),
        ).fetchone()
        if not row:
            return None
        return dict(row)

    def list_updates(
        self,
        project_id: str,
        *,
        lifecycle: Optional[str] = None,
        review_id: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List updates for a project, optionally filtered."""
        clean_pid = str(project_id).strip()
        clauses = ["project_id = ?"]
        params: list[Any] = [clean_pid]
        if lifecycle is not None:
            clauses.append("lifecycle = ?")
            params.append(lifecycle)
        if review_id is not None:
            clauses.append("review_id = ?")
            params.append(review_id)
        params.append(max(1, int(limit)))
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM project_updates "
                f"WHERE {' AND '.join(clauses)} "
                f"ORDER BY draft_revision DESC, created_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── update (mutable draft fields) ──────────────────────────────────

    def update_draft(
        self,
        update_id: str,
        *,
        body_md: Optional[str] = None,
        claims_json: Optional[str] = None,
        source_manifest_json: Optional[str] = None,
    ) -> None:
        """Update mutable fields on a draft.

        Raises PublishedUpdateError if the row is published.
        """
        with self._connection() as conn:
            self._update_draft(
                conn,
                update_id=update_id,
                body_md=body_md,
                claims_json=claims_json,
                source_manifest_json=source_manifest_json,
            )

    def update_draft_in_transaction(
        self,
        conn: Any,
        update_id: str,
        *,
        body_md: Optional[str] = None,
        claims_json: Optional[str] = None,
        source_manifest_json: Optional[str] = None,
    ) -> None:
        """Update mutable draft fields on a caller-owned connection.

        Raises PublishedUpdateError if the row is published.
        """
        self._update_draft(
            conn,
            update_id=update_id,
            body_md=body_md,
            claims_json=claims_json,
            source_manifest_json=source_manifest_json,
        )

    @staticmethod
    def _update_draft(
        conn: Any,
        *,
        update_id: str,
        body_md: Optional[str],
        claims_json: Optional[str],
        source_manifest_json: Optional[str],
    ) -> None:
        clean_id = str(update_id).strip()
        # Check lifecycle first
        row = conn.execute(
            "SELECT lifecycle FROM project_updates WHERE id = ?",
            (clean_id,),
        ).fetchone()
        if not row:
            return
        if row[0] != "draft":
            raise PublishedUpdateError(
                f"Cannot modify {row[0]} update {clean_id}"
            )

        updates: list[str] = []
        params: list[Any] = []
        if body_md is not None:
            updates.append("body_md = ?")
            params.append(body_md)
        if claims_json is not None:
            updates.append("claims_json = ?")
            params.append(claims_json)
        if source_manifest_json is not None:
            updates.append("source_manifest_json = ?")
            params.append(source_manifest_json)
        if not updates:
            return
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(clean_id)
        conn.execute(
            f"UPDATE project_updates SET {', '.join(updates)} WHERE id = ?",
            params,
        )

    # ── publish ────────────────────────────────────────────────────────

    def publish_update(self, update_id: str) -> None:
        """Publish a draft update.

        Sets lifecycle='published' and published_at.
        Raises PublishedUpdateError if already published.
        """
        with self._connection() as conn:
            self._publish_update(conn, update_id=update_id)

    def publish_update_in_transaction(
        self,
        conn: Any,
        update_id: str,
    ) -> None:
        """Publish a draft update on a caller-owned connection.

        The conn-accepting variant so the service can publish + bump
        the project revision in one transaction.
        """
        self._publish_update(conn, update_id=update_id)

    @staticmethod
    def _publish_update(conn: Any, *, update_id: str) -> None:
        clean_id = str(update_id).strip()
        row = conn.execute(
            "SELECT lifecycle FROM project_updates WHERE id = ?",
            (clean_id,),
        ).fetchone()
        if not row:
            return
        if row[0] != "draft":
            raise PublishedUpdateError(
                f"Cannot publish {row[0]} update {clean_id}"
            )
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            "UPDATE project_updates "
            "SET lifecycle = 'published', published_at = ?, updated_at = ? "
            "WHERE id = ?",
            (now_iso, now_iso, clean_id),
        )

    # ── supersede (replace unaccepted draft) ───────────────────────────

    def supersede_draft(
        self,
        old_update_id: str,
        *,
        new_update_id: str,
        body_md: str = "",
        claims_json: str = "{}",
        source_manifest_json: str = "{}",
        generator: str = "deterministic",
    ) -> dict[str, Any]:
        """Supersede an unaccepted draft and create the next draft_revision.

        UPD-004: marks old draft superseded + creates draft_revision+1
        in one transaction.

        Raises PublishedUpdateError if the old row is published.
        Returns the new draft as a dict.
        """
        with self._connection() as conn:
            return self._supersede_draft(
                conn,
                old_update_id=old_update_id,
                new_update_id=new_update_id,
                body_md=body_md,
                claims_json=claims_json,
                source_manifest_json=source_manifest_json,
                generator=generator,
            )

    def supersede_draft_in_transaction(
        self,
        conn: Any,
        old_update_id: str,
        *,
        new_update_id: str,
        body_md: str = "",
        claims_json: str = "{}",
        source_manifest_json: str = "{}",
        generator: str = "deterministic",
    ) -> dict[str, Any]:
        """Supersede on a caller-owned connection."""
        return self._supersede_draft(
            conn,
            old_update_id=old_update_id,
            new_update_id=new_update_id,
            body_md=body_md,
            claims_json=claims_json,
            source_manifest_json=source_manifest_json,
            generator=generator,
        )

    @staticmethod
    def _supersede_draft(
        conn: Any,
        *,
        old_update_id: str,
        new_update_id: str,
        body_md: str,
        claims_json: str,
        source_manifest_json: str,
        generator: str,
    ) -> dict[str, Any]:
        clean_old = str(old_update_id).strip()
        old_row = conn.execute(
            "SELECT * FROM project_updates WHERE id = ?",
            (clean_old,),
        ).fetchone()
        if not old_row:
            raise ValueError(f"Update {clean_old} not found")
        old = dict(old_row)
        if old["lifecycle"] == "published":
            raise PublishedUpdateError(
                f"Cannot supersede published update {clean_old}"
            )

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Mark old as superseded
        conn.execute(
            "UPDATE project_updates "
            "SET lifecycle = 'superseded', updated_at = ? "
            "WHERE id = ?",
            (now_iso, clean_old),
        )

        # Create new draft with draft_revision+1, same project_revision pin
        new_draft_rev = int(old["draft_revision"]) + 1
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id,
                lifecycle, draft_revision, body_md, claims_json,
                source_manifest_json, generator, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(new_update_id).strip(),
                old["project_id"],
                old["project_revision"],
                old["review_id"],
                new_draft_rev,
                body_md,
                claims_json,
                source_manifest_json,
                generator,
                now_iso,
                now_iso,
            ),
        )

        # Return the new draft
        new_row = conn.execute(
            "SELECT * FROM project_updates WHERE id = ?",
            (str(new_update_id).strip(),),
        ).fetchone()
        return dict(new_row)
