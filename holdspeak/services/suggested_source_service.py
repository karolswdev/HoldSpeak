"""HS-172-06: Suggested sources -- transcript-derived source proposals for Rooms.

A post-intel scanner finds repo mentions (owner/repo) and Jira issue keys
(PROJ-123) in meeting transcripts and maps them to SUGGESTED source rows
on the Room.  The user accepts or dismisses; dismissed suggestions never
recur for the same (project_id, reference) pair.  Accept creates a Watch
source through the existing add-source path.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from ..logging_config import get_logger

_log = get_logger("services.suggested_source")

# ---- Regexes ----------------------------------------------------------------

# GitHub owner/repo: alphanumeric + hyphens/dots/underscores, separated by /.
# Must be preceded by whitespace, line start, or a URL prefix.
_REPO_RE = re.compile(
    r"(?:^|(?<=\s)|(?<=github\.com/))"
    r"([a-zA-Z0-9][a-zA-Z0-9._-]*/[a-zA-Z0-9][a-zA-Z0-9._-]*)",
)

# Jira-style issue key: uppercase project prefix + hyphen + digits.
_JIRA_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")


class SuggestedSourceService:
    """Stateless scanner + CRUD over the source_suggestions table."""

    def __init__(self, db: Any) -> None:
        self._db = db

    # ---- Scanner -------------------------------------------------------------

    def scan_transcript(
        self,
        transcript_text: str,
        project_id: str,
        meeting_id: str,
        *,
        connected_jira_keys: set[str] | None = None,
        existing_source_refs: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Scan transcript text for repo and issue mentions.

        Returns a list of suggestion dicts (not yet persisted).
        Filters out:
        - References that already exist as Watch sources on the Room.
        - References already suggested (pending or dismissed) for this Room.
        - Jira keys whose project prefix is not in connected_jira_keys.
        """
        connected_jira_keys = connected_jira_keys or set()
        existing_source_refs = existing_source_refs or set()

        # Normalize existing source refs by provider for case-insensitive dedup.
        existing_gh = {r.lower() for r in existing_source_refs}
        existing_jira = {r.upper() for r in existing_source_refs}

        # Existing suggestions for this project (normalized per provider).
        existing_suggestion_pairs = self._existing_ref_pairs(project_id)

        suggestions: list[dict[str, Any]] = []
        seen_refs: set[str] = set()

        # GitHub repos -- dedup lower-cased.
        for match in _REPO_RE.finditer(transcript_text):
            ref = match.group(1)
            norm = ref.lower()
            if norm in seen_refs:
                continue
            seen_refs.add(norm)
            if norm in existing_gh:
                continue
            if ("github", norm) in existing_suggestion_pairs:
                continue
            suggestions.append({
                "provider": "github",
                "reference": ref,
            })

        # Jira keys -- dedup upper-cased.
        for match in _JIRA_KEY_RE.finditer(transcript_text):
            key = match.group(1)
            norm = key.upper()
            project_prefix = norm.rsplit("-", 1)[0]
            if connected_jira_keys and project_prefix not in connected_jira_keys:
                continue
            if norm in seen_refs:
                continue
            seen_refs.add(norm)
            if norm in existing_jira:
                continue
            if ("jira", norm) in existing_suggestion_pairs:
                continue
            suggestions.append({
                "provider": "jira",
                "reference": key,
            })

        return suggestions

    def create_suggestions(
        self,
        project_id: str,
        meeting_id: str,
        suggestions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Persist scanned suggestions as pending rows."""
        rows: list[dict[str, Any]] = []
        now = datetime.now().isoformat()
        conn = self._db._connection()
        for s in suggestions:
            row_id = f"ssug_{uuid.uuid4().hex[:12]}"
            conn.execute(
                "INSERT OR IGNORE INTO source_suggestions "
                "(id, project_id, meeting_id, provider, reference, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                (row_id, project_id, meeting_id, s["provider"], s["reference"], now),
            )
            rows.append({
                "id": row_id,
                "project_id": project_id,
                "meeting_id": meeting_id,
                "provider": s["provider"],
                "reference": s["reference"],
                "status": "pending",
                "created_at": now,
            })
        conn.commit()
        return rows

    # ---- CRUD ----------------------------------------------------------------

    def list_suggestions(
        self, project_id: str, *, status: str = "pending",
    ) -> list[dict[str, Any]]:
        """List suggestions for a project filtered by status."""
        conn = self._db._connection()
        rows = conn.execute(
            "SELECT * FROM source_suggestions WHERE project_id=? AND status=? "
            "ORDER BY created_at",
            (project_id, status),
        ).fetchall()
        return [dict(row) for row in rows]

    def accept_suggestion(self, suggestion_id: str) -> dict[str, Any]:
        """Mark a suggestion as accepted.  Returns the updated row."""
        conn = self._db._connection()
        conn.execute(
            "UPDATE source_suggestions SET status='accepted' WHERE id=?",
            (suggestion_id,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM source_suggestions WHERE id=?", (suggestion_id,),
        ).fetchone()
        if row is None:
            from .errors import NotFound
            raise NotFound("suggestion", suggestion_id)
        return dict(row)

    def dismiss_suggestion(self, suggestion_id: str) -> dict[str, Any]:
        """Mark a suggestion as dismissed.  Returns the updated row."""
        conn = self._db._connection()
        conn.execute(
            "UPDATE source_suggestions SET status='dismissed' WHERE id=?",
            (suggestion_id,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM source_suggestions WHERE id=?", (suggestion_id,),
        ).fetchone()
        if row is None:
            from .errors import NotFound
            raise NotFound("suggestion", suggestion_id)
        return dict(row)

    def get_suggestion(self, suggestion_id: str) -> dict[str, Any]:
        """Get a single suggestion by ID."""
        conn = self._db._connection()
        row = conn.execute(
            "SELECT * FROM source_suggestions WHERE id=?", (suggestion_id,),
        ).fetchone()
        if row is None:
            from .errors import NotFound
            raise NotFound("suggestion", suggestion_id)
        return dict(row)

    # ---- Helpers -------------------------------------------------------------

    def _existing_ref_pairs(self, project_id: str) -> set[tuple[str, str]]:
        """All (provider, normalized_ref) already suggested for this project.

        GitHub refs are normalized lower-cased; Jira refs upper-cased.
        A dismissed suggestion is included so it is never raised again.
        """
        conn = self._db._connection()
        rows = conn.execute(
            "SELECT provider, reference FROM source_suggestions WHERE project_id=?",
            (project_id,),
        ).fetchall()
        pairs: set[tuple[str, str]] = set()
        for row in rows:
            provider = row["provider"]
            ref = row["reference"]
            if provider == "github":
                pairs.add(("github", ref.lower()))
            elif provider == "jira":
                pairs.add(("jira", ref.upper()))
            else:
                pairs.add((provider, ref))
        return pairs
