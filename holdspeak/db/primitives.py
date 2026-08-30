"""Repositories for the desk's synced first-class primitives.

The Primitive Framework hub side: Note, KB, Agent (persona), Chain and Workflow
are canonical, DB-backed, CRUD-able, syncable server domain objects. The desktop
is the canonical store; the iPad / web are authoring ports that sync to it.

Every primitive here is **content/organization/capability-synced**: it carries a
`last_modified` (ISO-8601, last-write-wins conflict key) and a `deleted`
tombstone, mirroring exactly how `meetings`/`artifacts` sync today. A delete is a
tombstone (the row stays, `deleted=1`) so the tombstone propagates to other
surfaces; `purge` is available for hard removal in tests/maintenance.

NOTE on naming overlap (intentional, do not conflate):
- `KBRecord` here is the desk's user-authored knowledge container. It is DISTINCT
  from the existing `project.yaml` kb-map and the `.hs/`/`.holdspeak/` context
  files (project-scoped dictation context).
- `RecipeRecord` here is the canonical persona. It is DISTINCT from
  `holdspeak.agent_context` AgentSession (a live claude/codex coding session).
"""
from __future__ import annotations

import logging
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

from ..logging_config import get_logger
from ..deployment_revisions import DeploymentRevision
from .base import BaseRepository
from .relationships import qualified_ref
from .models import (
    RecipeRecord,
    ChainRecord,
    DecisionRecord,
    DirectoryMembershipRecord,
    DirectoryRecord,
    KBRecord,
    ModelManifestRecord,
    NoteRecord,
    ProfileRecord,
    WorkflowRecord,
)

log = get_logger("db.primitives")
_migration_log = logging.getLogger(__name__)


# ── Zone name uniqueness (HS-118-01) ─────────────────────────────────────────

class ZoneNameTaken(Exception):
    """Raised when a zone name collides with an existing live zone."""

    def __init__(self, existing_name: str) -> None:
        self.existing_name = existing_name
        super().__init__(f"A zone named {existing_name!r} already exists")


def normalize_zone_name(raw: str) -> str:
    """Strip, collapse whitespace, NFC-normalize, casefold.

    Returns the normalized form used for uniqueness comparison.
    """
    s = str(raw or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = unicodedata.normalize("NFC", s)
    s = s.casefold()
    return s


def _now_iso() -> str:
    """ISO-8601 UTC with a trailing `Z`, matching the sync wire contract."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class NoteRepository(BaseRepository):
    """CRUD + sync access for desk Notes (content/synced)."""

    table = "notes"

    def upsert(
        self,
        *,
        note_id: str,
        title: str = "",
        body_markdown: str = "",
        tags: Optional[list[str]] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> NoteRecord:
        """Create or replace a note (idempotent on id). Returns the stored row.

        `created_at` is preserved on update; `updated_at`/`last_modified` advance.
        """
        clean_id = str(note_id or "").strip()
        if not clean_id:
            raise ValueError("note id is required")
        now = _now_iso()
        with self._connection() as conn:
            # Ownership is checked under the same write lock as the mutation:
            # an ordinary writer may not observe "unowned", wait for thought
            # adoption, then overwrite the newly owned working Note.
            conn.execute("BEGIN IMMEDIATE")
            owned = conn.execute("SELECT 1 FROM refinement_thoughts WHERE working_note_id = ?", (clean_id,)).fetchone()
            if owned:
                raise ValueError("thought-owned notes require expected revision")
            self._upsert_in_transaction(
                conn, note_id=clean_id, title=title, body_markdown=body_markdown,
                tags=tags, last_modified=last_modified, deleted=deleted,
                created_at=created_at, now=now,
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def upsert_in_transaction(self, *args: Any, **kwargs: Any) -> None:
        """Refuse the former generic transaction bypass for owned Notes."""
        raise ValueError("generic transaction note writes are not authorized")

    def _upsert_in_transaction(
        self, conn: sqlite3.Connection, *, note_id: str, title: str = "",
        body_markdown: str = "", tags: Optional[list[str]] = None,
        last_modified: Optional[str] = None, deleted: bool = False,
        created_at: Optional[str] = None, now: Optional[str] = None,
    ) -> None:
        """Internal write for a caller that owns an enclosing transaction."""
        now = now or _now_iso()
        existing = conn.execute("SELECT created_at FROM notes WHERE id = ?", (note_id,)).fetchone()
        created = created_at or (existing["created_at"] if existing else now)
        conn.execute(
            """INSERT INTO notes (id, title, body_markdown, tags_json,
                                   created_at, updated_at, last_modified, deleted)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET title=excluded.title,
                 body_markdown=excluded.body_markdown, tags_json=excluded.tags_json,
                 updated_at=excluded.updated_at, last_modified=excluded.last_modified,
                 deleted=excluded.deleted""",
            (note_id, str(title or ""), str(body_markdown or ""),
             self._json_dumps(tags or [], fallback="[]"), created, now,
             last_modified or now, 1 if deleted else 0),
        )

    def get(self, note_id: str, *, include_deleted: bool = False) -> Optional[NoteRecord]:
        clean_id = str(note_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[NoteRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE deleted = 0 ORDER BY updated_at DESC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def list_by_tag(self, tag: str, *, include_deleted: bool = False, limit: int = 500) -> list[NoteRecord]:
        """List notes that contain ``tag`` in their tags_json array (json_each)."""
        bounded = max(1, min(int(limit), 2000))
        clean_tag = str(tag or "").strip()
        if not clean_tag:
            return []
        with self._connection() as conn:
            clause = "" if include_deleted else "AND n.deleted = 0 "
            rows = conn.execute(
                f"SELECT DISTINCT n.* FROM notes n, json_each(n.tags_json) t "
                f"WHERE t.value = ? {clause}"
                f"ORDER BY n.updated_at DESC LIMIT ?",
                (clean_tag, bounded),
            ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, note_id: str) -> bool:
        """Tombstone a note (deleted=1). Returns True if a row was affected."""
        clean_id = str(note_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            owned = conn.execute("SELECT 1 FROM refinement_thoughts WHERE working_note_id = ?", (clean_id,)).fetchone()
            if owned:
                raise ValueError("thought-owned notes require expected revision")
            cur = conn.execute(
                "UPDATE notes SET deleted = 1, last_modified = ?, updated_at = ? WHERE id = ? AND deleted = 0",
                (now, now, clean_id),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, note_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM notes WHERE id = ?", (str(note_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> NoteRecord:
        return NoteRecord(
            id=row["id"],
            title=row["title"],
            body_markdown=row["body_markdown"],
            tags=self._json_loads_list(row["tags_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class DeskDecisionRepository(BaseRepository):
    """CRUD access for Desk-authored Architecture Decision Records."""

    table = "desk_decisions"

    VALID_STATUSES = frozenset({"proposed", "accepted", "superseded", "deprecated"})

    def upsert(
        self,
        *,
        decision_id: str,
        title: str = "",
        status: str = "proposed",
        deciders: Optional[list[str]] = None,
        decided_at: Optional[str] = None,
        context_markdown: str = "",
        decision_markdown: str = "",
        alternatives: Optional[list[dict[str, str]]] = None,
        consequences_markdown: str = "",
        superseded_by: Optional[str] = None,
        tags: Optional[list[str]] = None,
        created_at: Optional[str] = None,
    ) -> DecisionRecord:
        clean_id = str(decision_id or "").strip()
        clean_status = str(status or "proposed").strip().lower()
        if not clean_id:
            raise ValueError("decision id is required")
        if clean_status not in self.VALID_STATUSES:
            raise ValueError(f"invalid decision status: {clean_status}")
        now = _now_iso()
        normalized_alternatives = [
            {"name": str(item.get("name") or ""), "reason": str(item.get("reason") or "")}
            for item in (alternatives or [])
            if isinstance(item, dict)
        ]
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM desk_decisions WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO desk_decisions (
                    id, title, status, deciders_json, decided_at, context_markdown,
                    decision_markdown, alternatives_json, consequences_markdown,
                    superseded_by, tags_json, created_at, updated_at, deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, status=excluded.status,
                    deciders_json=excluded.deciders_json, decided_at=excluded.decided_at,
                    context_markdown=excluded.context_markdown,
                    decision_markdown=excluded.decision_markdown,
                    alternatives_json=excluded.alternatives_json,
                    consequences_markdown=excluded.consequences_markdown,
                    superseded_by=excluded.superseded_by, tags_json=excluded.tags_json,
                    updated_at=excluded.updated_at, deleted=0
                """,
                (
                    clean_id, str(title or ""), clean_status,
                    self._json_dumps(deciders or [], fallback="[]"), decided_at,
                    str(context_markdown or ""), str(decision_markdown or ""),
                    self._json_dumps(normalized_alternatives, fallback="[]"),
                    str(consequences_markdown or ""),
                    str(superseded_by).strip() if superseded_by else None,
                    self._json_dumps(tags or [], fallback="[]"), created, now,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, decision_id: str, *, include_deleted: bool = False) -> Optional[DecisionRecord]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM desk_decisions WHERE id = ?", (str(decision_id or "").strip(),)
            ).fetchone()
        if not row or (row["deleted"] and not include_deleted):
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[DecisionRecord]:
        with self._connection() as conn:
            sql = "SELECT * FROM desk_decisions" + ("" if include_deleted else " WHERE deleted = 0")
            rows = conn.execute(sql + " ORDER BY updated_at DESC LIMIT ?", (max(1, min(int(limit), 2000)),)).fetchall()
        return [self._row(row) for row in rows]

    def update(self, decision_id: str, **patch: Any) -> Optional[DecisionRecord]:
        current = self.get(decision_id)
        if current is None:
            return None
        values = current.to_dict()
        values.update({key: value for key, value in patch.items() if value is not None})
        return self.upsert(
            decision_id=current.id, title=values["title"], status=values["status"],
            deciders=values["deciders"], decided_at=values["decided_at"],
            context_markdown=values["context_markdown"], decision_markdown=values["decision_markdown"],
            alternatives=values["alternatives"], consequences_markdown=values["consequences_markdown"],
            superseded_by=values["superseded_by"], tags=values["tags"], created_at=current.created_at,
        )

    def delete(self, decision_id: str) -> bool:
        now = _now_iso()
        with self._connection() as conn:
            result = conn.execute(
                "UPDATE desk_decisions SET deleted=1, updated_at=? WHERE id=? AND deleted=0",
                (now, str(decision_id or "").strip()),
            )
            return bool(result.rowcount)

    def supersede(self, decision_id: str, replacement_id: str) -> Optional[DecisionRecord]:
        current = self.get(decision_id)
        if current is None:
            return None
        successor = self.upsert(
            decision_id=replacement_id, title=f"Superseding {current.title}",
            status="proposed", deciders=current.deciders, context_markdown=current.context_markdown,
            decision_markdown=current.decision_markdown,
            alternatives=current.to_dict()["alternatives"],
            consequences_markdown=current.consequences_markdown, tags=current.tags,
        )
        self.update(current.id, status="superseded", superseded_by=successor.id)
        return successor

    def _row(self, row: Any) -> DecisionRecord:
        return DecisionRecord(
            id=str(row["id"]), title=str(row["title"]), status=str(row["status"]),
            deciders=self._json_loads_list(row["deciders_json"]), decided_at=row["decided_at"],
            context_markdown=str(row["context_markdown"]),
            decision_markdown=str(row["decision_markdown"]),
            alternatives_json=str(row["alternatives_json"]),
            consequences_markdown=str(row["consequences_markdown"]),
            superseded_by=row["superseded_by"], tags=self._json_loads_list(row["tags_json"]),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
            deleted=bool(row["deleted"]),
        )


class KBRepository(BaseRepository):
    """CRUD + sync access for desk Knowledge Bases (organization/synced).

    The desk's knowledge container — NOT the project.yaml kb-map / .hs context.
    """

    table = "kbs"

    def upsert(
        self,
        *,
        kb_id: str,
        name: str = "",
        member_ids: Optional[list[str]] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> KBRecord:
        clean_id = str(kb_id or "").strip()
        if not clean_id:
            raise ValueError("kb id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM kbs WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO kbs (id, name, member_ids_json, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    member_ids_json = excluded.member_ids_json,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    self._json_dumps(member_ids or [], fallback="[]"),
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
            # Qualified clients write the independent many-to-many edge store.
            # Raw legacy lists remain readable; their kind cannot be guessed.
            if member_ids is not None:
                refs: list[str] = []
                try:
                    refs = [qualified_ref(value) for value in member_ids]
                except ValueError:
                    refs = []
                else:
                    desired = set(refs)
                    if desired:
                        marks = ",".join("?" for _ in desired)
                        conn.execute(
                            "UPDATE knowledge_memberships SET deleted=1,last_modified=? "
                            f"WHERE knowledge_id=? AND deleted=0 AND resource_ref NOT IN ({marks})",
                            (last_modified or now, clean_id, *sorted(desired)),
                        )
                    else:
                        conn.execute(
                            "UPDATE knowledge_memberships SET deleted=1,last_modified=? "
                            "WHERE knowledge_id=? AND deleted=0",
                            (last_modified or now, clean_id),
                        )
                    for ref in sorted(desired):
                        conn.execute(
                            """INSERT INTO knowledge_memberships
                               (knowledge_id,resource_ref,created_at,last_modified,deleted)
                               VALUES (?,?,?,?,0) ON CONFLICT(knowledge_id,resource_ref)
                               DO UPDATE SET last_modified=excluded.last_modified,deleted=0""",
                            (clean_id, ref, now, last_modified or now),
                        )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, kb_id: str, *, include_deleted: bool = False) -> Optional[KBRecord]:
        clean_id = str(kb_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM kbs WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[KBRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM kbs ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM kbs WHERE deleted = 0 ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, kb_id: str) -> bool:
        clean_id = str(kb_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE kbs SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0", (now, clean_id)
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, kb_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM kbs WHERE id = ?", (str(kb_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> KBRecord:
        return KBRecord(
            id=row["id"],
            name=row["name"],
            member_ids=self._json_loads_list(row["member_ids_json"]),
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class RecipeRepository(BaseRepository):
    """CRUD + sync access for Agent personas (capability/synced).

    The canonical persona — NOT agent_context.AgentSession (a live coding session).
    """

    table = "recipes"

    def upsert(
        self,
        *,
        recipe_id: str,
        name: str = "",
        avatar: str = "",
        role: str = "",
        system_prompt: str = "",
        user_template: str = "",
        tools: Optional[list[str]] = None,
        kb_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        manual_context: str = "",
        use_zone_context: bool = False,
        kind: str = "",
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> RecipeRecord:
        clean_id = str(recipe_id or "").strip()
        if not clean_id:
            raise ValueError("agent id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM recipes WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO recipes (id, name, avatar, role, system_prompt, user_template,
                                    tools_json, kb_id, profile_id, manual_context,
                                    use_zone_context, kind, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    avatar = excluded.avatar,
                    role = excluded.role,
                    system_prompt = excluded.system_prompt,
                    user_template = excluded.user_template,
                    tools_json = excluded.tools_json,
                    kb_id = excluded.kb_id,
                    profile_id = excluded.profile_id,
                    manual_context = excluded.manual_context,
                    use_zone_context = excluded.use_zone_context,
                    kind = excluded.kind,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    str(avatar or ""),
                    str(role or ""),
                    str(system_prompt or ""),
                    str(user_template or ""),
                    self._json_dumps(tools or [], fallback="[]"),
                    str(kb_id).strip() if kb_id else None,
                    str(profile_id).strip() if profile_id else None,
                    str(manual_context or ""),
                    1 if use_zone_context else 0,
                    str(kind or ""),
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, recipe_id: str, *, include_deleted: bool = False) -> Optional[RecipeRecord]:
        clean_id = str(recipe_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM recipes WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[RecipeRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM recipes ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM recipes WHERE deleted = 0 ORDER BY name ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, recipe_id: str) -> bool:
        clean_id = str(recipe_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE recipes SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0", (now, clean_id)
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, recipe_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM recipes WHERE id = ?", (str(recipe_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def list_by_kind(self, kind: str, *, include_deleted: bool = False, limit: int = 500) -> list[RecipeRecord]:
        """List recipes filtered by kind (e.g. 'mode')."""
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM recipes WHERE kind = ? ORDER BY name ASC LIMIT ?",
                    (str(kind), bounded),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM recipes WHERE deleted = 0 AND kind = ? ORDER BY name ASC LIMIT ?",
                    (str(kind), bounded),
                ).fetchall()
        return [self._row(r) for r in rows]

    def _row(self, row: Any) -> RecipeRecord:
        return RecipeRecord(
            id=row["id"],
            name=row["name"],
            avatar=row["avatar"],
            role=row["role"],
            system_prompt=row["system_prompt"],
            user_template=row["user_template"],
            tools=self._json_loads_list(row["tools_json"]),
            kb_id=row["kb_id"],
            profile_id=row["profile_id"] if "profile_id" in row.keys() else None,
            manual_context=str(row["manual_context"] or "") if "manual_context" in row.keys() else "",
            use_zone_context=bool(row["use_zone_context"]) if "use_zone_context" in row.keys() else False,
            kind=str(row["kind"] or "") if "kind" in row.keys() else "",
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class ProfileRepository(BaseRepository):
    """CRUD + sync access for RuntimeProfiles (capability/synced, Phase 24).

    SHAPE ONLY — the API key is never stored here; the hub joins its own secret at
    request time. Mirrors the other primitive repos (soft-delete tombstones).
    """

    table = "profiles"

    def upsert(
        self,
        *,
        profile_id: str,
        name: str = "",
        kind: str = "onDevice",
        model_file: str = "",
        base_url: str = "",
        model: str = "",
        node: str = "",
        context_limit: int = 16384,
        requires_key: bool = False,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> ProfileRecord:
        clean_id = str(profile_id or "").strip()
        if not clean_id:
            raise ValueError("profile id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM profiles WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO profiles (id, name, kind, model_file, base_url, model, node,
                                      context_limit, requires_key, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    kind = excluded.kind,
                    model_file = excluded.model_file,
                    base_url = excluded.base_url,
                    model = excluded.model,
                    node = excluded.node,
                    context_limit = excluded.context_limit,
                    requires_key = excluded.requires_key,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    str(kind or "onDevice"),
                    str(model_file or ""),
                    str(base_url or ""),
                    str(model or ""),
                    str(node or ""),
                    int(context_limit or 16384),
                    1 if requires_key else 0,
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, profile_id: str, *, include_deleted: bool = False) -> Optional[ProfileRecord]:
        clean_id = str(profile_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[ProfileRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            sql = "SELECT * FROM profiles" + ("" if include_deleted else " WHERE deleted = 0")
            rows = conn.execute(sql + " ORDER BY name ASC LIMIT ?", (bounded,)).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, profile_id: str) -> bool:
        clean_id = str(profile_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE profiles SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0", (now, clean_id)
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, profile_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM profiles WHERE id = ?", (str(profile_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> ProfileRecord:
        return ProfileRecord(
            id=row["id"],
            name=row["name"],
            kind=row["kind"],
            model_file=row["model_file"],
            base_url=row["base_url"],
            model=row["model"],
            node=row["node"],
            context_limit=int(row["context_limit"]),
            requires_key=bool(row["requires_key"]),
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class ModelManifestRepository(BaseRepository):
    """CRUD + sync access for model MANIFESTS (capability/synced, HSM-16-08).

    Availability only — "this node has this model, with these capabilities."
    The model binary never syncs; no path/url/bytes column exists to leak it.
    Mirrors the other primitive repos (soft-delete tombstones)."""

    table = "model_manifests"

    def upsert(
        self,
        *,
        manifest_id: str,
        node: str = "",
        name: str = "",
        capabilities: Optional[list[str]] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> ModelManifestRecord:
        clean_id = str(manifest_id or "").strip()
        if not clean_id:
            raise ValueError("model manifest id is required")
        import json as _json
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM model_manifests WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO model_manifests (id, node, name, capabilities_json,
                                             created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    node = excluded.node,
                    name = excluded.name,
                    capabilities_json = excluded.capabilities_json,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(node or ""),
                    str(name or ""),
                    _json.dumps([str(c) for c in (capabilities or [])]),
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, manifest_id: str, *, include_deleted: bool = False) -> Optional[ModelManifestRecord]:
        clean_id = str(manifest_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM model_manifests WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[ModelManifestRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            sql = "SELECT * FROM model_manifests" + ("" if include_deleted else " WHERE deleted = 0")
            rows = conn.execute(sql + " ORDER BY node ASC, name ASC LIMIT ?", (bounded,)).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, manifest_id: str) -> bool:
        clean_id = str(manifest_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE model_manifests SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0",
                (now, clean_id),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, manifest_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM model_manifests WHERE id = ?", (str(manifest_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> ModelManifestRecord:
        import json as _json
        try:
            caps = _json.loads(row["capabilities_json"] or "[]")
        except (ValueError, TypeError):
            caps = []
        return ModelManifestRecord(
            id=row["id"],
            node=row["node"],
            name=row["name"],
            capabilities=[str(c) for c in caps] if isinstance(caps, list) else [],
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class ChainRepository(BaseRepository):
    """CRUD + sync access for Chains (capability/synced)."""

    table = "chains"

    def upsert(
        self,
        *,
        chain_id: str,
        name: str = "",
        steps: Optional[list[str]] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> ChainRecord:
        clean_id = str(chain_id or "").strip()
        if not clean_id:
            raise ValueError("chain id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM chains WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO chains (id, name, steps_json, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    steps_json = excluded.steps_json,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    self._json_dumps(steps or [], fallback="[]"),
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, chain_id: str, *, include_deleted: bool = False) -> Optional[ChainRecord]:
        clean_id = str(chain_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM chains WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[ChainRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM chains ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chains WHERE deleted = 0 ORDER BY name ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, chain_id: str) -> bool:
        clean_id = str(chain_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE chains SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0", (now, clean_id)
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, chain_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM chains WHERE id = ?", (str(chain_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> ChainRecord:
        return ChainRecord(
            id=row["id"],
            name=row["name"],
            steps=self._json_loads_list(row["steps_json"]),
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class WorkflowRepository(BaseRepository):
    """CRUD + sync access for Workflows (capability/synced)."""

    table = "workflows"

    def upsert(
        self,
        *,
        workflow_id: str,
        name: str = "",
        prompt: str = "",
        graph_json: Optional[dict[str, Any]] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> WorkflowRecord:
        clean_id = str(workflow_id or "").strip()
        if not clean_id:
            raise ValueError("workflow id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM workflows WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO workflows (id, name, prompt, graph_json, created_at,
                                       last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    prompt = excluded.prompt,
                    graph_json = excluded.graph_json,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    str(prompt or ""),
                    self._json_dumps(graph_json or {}, fallback="{}"),
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, workflow_id: str, *, include_deleted: bool = False) -> Optional[WorkflowRecord]:
        clean_id = str(workflow_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM workflows WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[WorkflowRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM workflows ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM workflows WHERE deleted = 0 ORDER BY name ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, workflow_id: str) -> bool:
        clean_id = str(workflow_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE workflows SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0",
                (now, clean_id),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, workflow_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM workflows WHERE id = ?", (str(workflow_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> WorkflowRecord:
        return WorkflowRecord(
            id=row["id"],
            name=row["name"],
            prompt=row["prompt"],
            graph_json=self._json_loads_dict(row["graph_json"]),
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class DirectoryRepository(BaseRepository):
    """CRUD + sync access for Directories (organization/synced).

    The canonical organization container; the iPad's "zone" rendered spatially.
    Only identity + nesting (`id, name, parent_id`) sync here — geometry/paint is
    per-device layout and lives on the surface, never canonical. Membership (what
    is filed inside) is the separate `DirectoryMembershipRepository`.
    """

    table = "directories"

    def upsert(
        self,
        *,
        directory_id: str,
        name: str = "",
        parent_id: Optional[str] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> DirectoryRecord:
        clean_id = str(directory_id or "").strip()
        if not clean_id:
            raise ValueError("directory id is required")
        clean_name = str(name or "").strip()
        norm = normalize_zone_name(clean_name)
        # Validate character constraints (1-64 after normalization) for live rows.
        if not deleted:
            if not norm:
                raise ValueError("zone name is required")
            if len(norm) > 64:
                raise ValueError("zone name must be 64 characters or fewer")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM directories WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            try:
                conn.execute(
                    """
                    INSERT INTO directories (id, name, name_normalized, parent_id,
                                             created_at, last_modified, deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        name_normalized = excluded.name_normalized,
                        parent_id = excluded.parent_id,
                        last_modified = excluded.last_modified,
                        deleted = excluded.deleted
                    """,
                    (
                        clean_id,
                        clean_name,
                        norm,
                        str(parent_id).strip() if parent_id else None,
                        created,
                        last_modified or now,
                        1 if deleted else 0,
                    ),
                )
            except sqlite3.IntegrityError:
                # The unique partial index on name_normalized fired — find the
                # existing zone that owns this name.
                row = conn.execute(
                    "SELECT name FROM directories "
                    "WHERE name_normalized = ? AND deleted = 0 AND id != ?",
                    (norm, clean_id),
                ).fetchone()
                raise ZoneNameTaken(row["name"] if row else clean_name)
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def find_by_normalized_name(self, name: str) -> Optional[DirectoryRecord]:
        """Look up a live directory by its normalized name."""
        norm = normalize_zone_name(name)
        if not norm:
            return None
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM directories WHERE name_normalized = ? AND deleted = 0",
                (norm,),
            ).fetchone()
        if not row:
            return None
        return self._row(row)

    def get(self, directory_id: str, *, include_deleted: bool = False) -> Optional[DirectoryRecord]:
        clean_id = str(directory_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM directories WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[DirectoryRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM directories ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM directories WHERE deleted = 0 ORDER BY name ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, directory_id: str) -> bool:
        clean_id = str(directory_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE directories SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0",
                (now, clean_id),
            )
            if cur.rowcount:
                # Deleting a Zone returns its contents to the Desk root and its
                # child Zones to the root; nothing can become silently stranded.
                conn.execute(
                    "UPDATE directory_memberships SET deleted = 1, last_modified = ? "
                    "WHERE directory_id = ? AND deleted = 0",
                    (now, clean_id),
                )
                conn.execute(
                    "UPDATE directories SET parent_id = NULL, last_modified = ? "
                    "WHERE parent_id = ? AND deleted = 0",
                    (now, clean_id),
                )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, directory_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM directories WHERE id = ?", (str(directory_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> DirectoryRecord:
        return DirectoryRecord(
            id=row["id"],
            name=row["name"],
            name_normalized=row["name_normalized"] if "name_normalized" in row.keys() else "",
            parent_id=row["parent_id"],
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class DirectoryMembershipRepository(BaseRepository):
    """CRUD + sync access for directory membership edges (organization/synced).

    The canonical formalization of the legacy `filed` map (`hs.desk.filed` on the
    web, the iPad's `filed` dict): a synced map `primitive_id → directory_id`.
    Keyed by `primitive_id` (a primitive is filed in at most one directory), so a
    re-file overwrites the row. This SUPERSEDES the surfaces' local maps; they
    become caches hydrated from / pushed to these rows.

    Tombstone semantics: unfiling sets `deleted=1` (the row stays so the unfile
    propagates). `last_modified` is the last-write-wins conflict key.
    """

    table = "directory_memberships"

    def upsert(
        self,
        *,
        primitive_id: str,
        directory_id: str = "",
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> DirectoryMembershipRecord:
        clean_pid = str(primitive_id or "").strip()
        if not clean_pid:
            raise ValueError("primitive id is required")
        # A live (non-tombstone) membership must name a directory.
        clean_dir = str(directory_id or "").strip()
        if not deleted and not clean_dir:
            raise ValueError("directory id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM directory_memberships WHERE primitive_id = ?",
                (clean_pid,),
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO directory_memberships (primitive_id, directory_id,
                                                   created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(primitive_id) DO UPDATE SET
                    directory_id = excluded.directory_id,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_pid,
                    clean_dir,
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_pid, include_deleted=True)  # type: ignore[return-value]

    def get(self, primitive_id: str, *, include_deleted: bool = False) -> Optional[DirectoryMembershipRecord]:
        clean_pid = str(primitive_id or "").strip()
        if not clean_pid:
            return None
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM directory_memberships WHERE primitive_id = ?", (clean_pid,)
            ).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 2000) -> list[DirectoryMembershipRecord]:
        bounded = max(1, min(int(limit), 5000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM directory_memberships ORDER BY last_modified DESC LIMIT ?",
                    (bounded,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM directory_memberships WHERE deleted = 0 "
                    "ORDER BY last_modified DESC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def list_for_directory(self, directory_id: str) -> list[DirectoryMembershipRecord]:
        """Live (non-tombstone) members filed into one directory."""
        clean_dir = str(directory_id or "").strip()
        if not clean_dir:
            return []
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM directory_memberships "
                "WHERE directory_id = ? AND deleted = 0 ORDER BY last_modified DESC",
                (clean_dir,),
            ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, primitive_id: str) -> bool:
        """Unfile a primitive (tombstone). Returns True if a live row was affected."""
        clean_pid = str(primitive_id or "").strip()
        if not clean_pid:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE directory_memberships SET deleted = 1, last_modified = ? "
                "WHERE primitive_id = ? AND deleted = 0",
                (now, clean_pid),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, primitive_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                "DELETE FROM directory_memberships WHERE primitive_id = ?",
                (str(primitive_id).strip(),),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> DirectoryMembershipRecord:
        return DirectoryMembershipRecord(
            primitive_id=row["primitive_id"],
            directory_id=row["directory_id"],
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


def _backfill_directory_name_normalized(conn: sqlite3.Connection) -> None:
    """One-time backfill: compute name_normalized for all directories and
    disambiguate duplicates among live (deleted=0) rows.

    Idempotent: rows that already have a non-empty name_normalized whose
    value matches normalize_zone_name(name) are skipped.
    """
    rows = conn.execute(
        "SELECT id, name, name_normalized, deleted FROM directories ORDER BY created_at ASC, id ASC"
    ).fetchall()
    # First pass: compute normalized names for all rows.
    updates: list[tuple[str, str]] = []  # (norm, id)
    for row in rows:
        expected = normalize_zone_name(row["name"])
        if row["name_normalized"] == expected and expected:
            continue  # already correct
        updates.append((expected, row["id"]))
    # Apply raw normalized values first.
    for norm, row_id in updates:
        conn.execute(
            "UPDATE directories SET name_normalized = ? WHERE id = ?",
            (norm, row_id),
        )
    # Second pass: disambiguate duplicates among live rows.
    # Bug fix: query ALL existing live normalized names from the DB before
    # starting dedup, so suffix collisions with non-duplicate names are caught.
    live_rows = conn.execute(
        "SELECT id, name, name_normalized FROM directories "
        "WHERE deleted = 0 ORDER BY created_at ASC, id ASC"
    ).fetchall()
    all_live_norms: set[str] = {row["name_normalized"] for row in live_rows if row["name_normalized"]}
    seen: dict[str, int] = {}  # norm -> count of times seen
    for row in live_rows:
        norm = row["name_normalized"]
        if not norm:
            continue
        if norm not in seen:
            seen[norm] = 1
            continue
        # Duplicate: disambiguate with suffix.
        seen[norm] += 1
        counter = seen[norm]
        base_name = row["name"]
        while True:
            suffix = f" ({counter})"
            # Handle 64-char limit: truncate base name to fit, preserving word boundary.
            max_base = 64 - len(suffix)
            if max_base < 1:
                # Extreme edge case: suffix alone exceeds 64 chars.
                candidate = str(counter)
            else:
                truncated = base_name[:max_base]
                # Preserve word boundary: find last space before cut point.
                if len(base_name) > max_base:
                    last_space = truncated.rfind(" ")
                    if last_space > 0:
                        truncated = truncated[:last_space]
                candidate = truncated + suffix
            candidate_norm = normalize_zone_name(candidate)
            if candidate_norm not in seen and candidate_norm not in all_live_norms:
                break
            counter += 1
        seen[candidate_norm] = 1
        all_live_norms.add(candidate_norm)
        _migration_log.info(
            "Zone name migration: zone %s renamed normalized %r -> %r",
            row["id"], norm, candidate_norm,
        )
        conn.execute(
            "UPDATE directories SET name = ?, name_normalized = ? WHERE id = ?",
            (candidate, candidate_norm, row["id"]),
        )


# ── Migration helper (HS-118-01) ─────────────────────────────────────────────

def _backfill_directory_name_normalized(conn: sqlite3.Connection) -> None:
    """One-time backfill: compute name_normalized for all directories and
    disambiguate duplicates among live (deleted=0) rows.

    Idempotent: rows that already have a non-empty name_normalized whose
    value matches normalize_zone_name(name) are skipped.
    """
    rows = conn.execute(
        "SELECT id, name, name_normalized, deleted FROM directories ORDER BY created_at ASC, id ASC"
    ).fetchall()
    # First pass: compute normalized names for all rows.
    updates: list[tuple[str, str]] = []  # (norm, id)
    for row in rows:
        expected = normalize_zone_name(row["name"])
        if row["name_normalized"] == expected and expected:
            continue  # already correct
        updates.append((expected, row["id"]))
    # Apply raw normalized values first.
    for norm, row_id in updates:
        conn.execute(
            "UPDATE directories SET name_normalized = ? WHERE id = ?",
            (norm, row_id),
        )
    # Second pass: disambiguate duplicates among live rows.
    # Bug fix: query ALL existing live normalized names from the DB before
    # starting dedup, so suffix collisions with non-duplicate names are caught.
    live_rows = conn.execute(
        "SELECT id, name, name_normalized FROM directories "
        "WHERE deleted = 0 ORDER BY created_at ASC, id ASC"
    ).fetchall()
    all_live_norms: set[str] = {row["name_normalized"] for row in live_rows if row["name_normalized"]}
    seen: dict[str, int] = {}  # norm -> count of times seen
    for row in live_rows:
        norm = row["name_normalized"]
        if not norm:
            continue
        if norm not in seen:
            seen[norm] = 1
            continue
        # Duplicate: disambiguate with suffix.
        seen[norm] += 1
        counter = seen[norm]
        base_name = row["name"]
        while True:
            suffix = f" ({counter})"
            # Handle 64-char limit: truncate base name to fit, preserving word boundary.
            max_base = 64 - len(suffix)
            if max_base < 1:
                # Extreme edge case: suffix alone exceeds 64 chars.
                candidate = str(counter)
            else:
                truncated = base_name[:max_base]
                # Preserve word boundary: find last space before cut point.
                if len(base_name) > max_base:
                    last_space = truncated.rfind(" ")
                    if last_space > 0:
                        truncated = truncated[:last_space]
                candidate = truncated + suffix
            candidate_norm = normalize_zone_name(candidate)
            if candidate_norm not in seen and candidate_norm not in all_live_norms:
                break
            counter += 1
        seen[candidate_norm] = 1
        all_live_norms.add(candidate_norm)
        _migration_log.info(
            "Zone name migration: zone %s renamed normalized %r -> %r",
            row["id"], norm, candidate_norm,
        )
        conn.execute(
            "UPDATE directories SET name = ?, name_normalized = ? WHERE id = ?",
            (candidate, candidate_norm, row["id"]),
        )


class DeploymentRevisionRepository(BaseRepository):
    """Content-addressed deployment specifications; credentials never enter rows."""

    table = "deployment_revisions"

    def upsert(self, revision: DeploymentRevision) -> DeploymentRevision:
        with self._connection() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO deployment_revisions
                   (id, schema_version, destination_id, kind, engine, model,
                    node, boundary, endpoint, model_path, secret_slot,
                    runtime_id, runtime_revision, artifact_id, manifest_sha256,
                    format, architecture, context_ceiling, capability_sha256)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    revision.id, revision.schema_version,
                    revision.destination_id, revision.kind, revision.engine,
                    revision.model, revision.node, revision.boundary,
                    revision.endpoint,
                    revision.model_path if revision.schema_version == 1 else None,
                    revision.secret_slot, revision.runtime_id,
                    revision.runtime_revision, revision.artifact_id,
                    revision.manifest_sha256, revision.format,
                    revision.architecture, revision.context_ceiling,
                    revision.capability_sha256,
                ),
            )
        return revision

    def get(self, revision_id: str) -> Optional[DeploymentRevision]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM deployment_revisions WHERE id = ?", (str(revision_id),)
            ).fetchone()
        if row is None:
            return None
        return DeploymentRevision(
            id=row["id"], destination_id=row["destination_id"], kind=row["kind"],
            engine=row["engine"], model=row["model"], node=row["node"],
            boundary=row["boundary"], endpoint=row["endpoint"],
            model_path=row["model_path"], secret_slot=row["secret_slot"],
            schema_version=int(row["schema_version"]),
            runtime_id=row["runtime_id"], runtime_revision=row["runtime_revision"],
            artifact_id=row["artifact_id"], manifest_sha256=row["manifest_sha256"],
            format=row["format"], architecture=row["architecture"],
            context_ceiling=int(row["context_ceiling"]),
            capability_sha256=row["capability_sha256"],
        )

    def list(self, *, limit: int = 500) -> list[DeploymentRevision]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM deployment_revisions ORDER BY id LIMIT ?", (bounded,)
            ).fetchall()
        return [self.get(row["id"]) for row in rows if self.get(row["id"]) is not None]
