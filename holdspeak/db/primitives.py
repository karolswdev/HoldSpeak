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
- `AgentRecord` here is the canonical persona. It is DISTINCT from
  `holdspeak.agent_context` AgentSession (a live claude/codex coding session).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    AgentRecord,
    ChainRecord,
    DirectoryMembershipRecord,
    DirectoryRecord,
    KBRecord,
    NoteRecord,
    ProfileRecord,
    WorkflowRecord,
)

log = get_logger("db.primitives")


def _now_iso() -> str:
    """ISO-8601 UTC with a trailing `Z`, matching the sync wire contract."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class NoteRepository(BaseRepository):
    """CRUD + sync access for desk Notes (content/synced)."""

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
            existing = conn.execute(
                "SELECT created_at FROM notes WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO notes (id, title, body_markdown, tags_json,
                                   created_at, updated_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    body_markdown = excluded.body_markdown,
                    tags_json = excluded.tags_json,
                    updated_at = excluded.updated_at,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(title or ""),
                    str(body_markdown or ""),
                    self._json_dumps(tags or [], fallback="[]"),
                    created,
                    now,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

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

    def delete(self, note_id: str) -> bool:
        """Tombstone a note (deleted=1). Returns True if a row was affected."""
        clean_id = str(note_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
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


class KBRepository(BaseRepository):
    """CRUD + sync access for desk Knowledge Bases (organization/synced).

    The desk's knowledge container — NOT the project.yaml kb-map / .hs context.
    """

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


class AgentRepository(BaseRepository):
    """CRUD + sync access for Agent personas (capability/synced).

    The canonical persona — NOT agent_context.AgentSession (a live coding session).
    """

    def upsert(
        self,
        *,
        agent_id: str,
        name: str = "",
        avatar: str = "",
        role: str = "",
        system_prompt: str = "",
        user_template: str = "",
        tools: Optional[list[str]] = None,
        kb_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> AgentRecord:
        clean_id = str(agent_id or "").strip()
        if not clean_id:
            raise ValueError("agent id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM agents WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO agents (id, name, avatar, role, system_prompt, user_template,
                                    tools_json, kb_id, profile_id, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    avatar = excluded.avatar,
                    role = excluded.role,
                    system_prompt = excluded.system_prompt,
                    user_template = excluded.user_template,
                    tools_json = excluded.tools_json,
                    kb_id = excluded.kb_id,
                    profile_id = excluded.profile_id,
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
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, agent_id: str, *, include_deleted: bool = False) -> Optional[AgentRecord]:
        clean_id = str(agent_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM agents WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[AgentRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM agents ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM agents WHERE deleted = 0 ORDER BY name ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, agent_id: str) -> bool:
        clean_id = str(agent_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE agents SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0", (now, clean_id)
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, agent_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM agents WHERE id = ?", (str(agent_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> AgentRecord:
        return AgentRecord(
            id=row["id"],
            name=row["name"],
            avatar=row["avatar"],
            role=row["role"],
            system_prompt=row["system_prompt"],
            user_template=row["user_template"],
            tools=self._json_loads_list(row["tools_json"]),
            kb_id=row["kb_id"],
            profile_id=row["profile_id"] if "profile_id" in row.keys() else None,
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class ProfileRepository(BaseRepository):
    """CRUD + sync access for RuntimeProfiles (capability/synced, Phase 24).

    SHAPE ONLY — the API key is never stored here; the hub joins its own secret at
    request time. Mirrors the other primitive repos (soft-delete tombstones).
    """

    def upsert(
        self,
        *,
        profile_id: str,
        name: str = "",
        kind: str = "onDevice",
        model_file: str = "",
        base_url: str = "",
        model: str = "",
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
                INSERT INTO profiles (id, name, kind, model_file, base_url, model,
                                      context_limit, requires_key, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    kind = excluded.kind,
                    model_file = excluded.model_file,
                    base_url = excluded.base_url,
                    model = excluded.model,
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
            context_limit=int(row["context_limit"]),
            requires_key=bool(row["requires_key"]),
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class ChainRepository(BaseRepository):
    """CRUD + sync access for Chains (capability/synced)."""

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
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM directories WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO directories (id, name, parent_id, created_at,
                                         last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    parent_id = excluded.parent_id,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    str(parent_id).strip() if parent_id else None,
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

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
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, directory_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM directories WHERE id = ?", (str(directory_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> DirectoryRecord:
        return DirectoryRecord(
            id=row["id"],
            name=row["name"],
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
