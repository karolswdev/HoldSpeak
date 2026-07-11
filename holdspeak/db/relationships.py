"""Independent Desk relationship axes (HS-92-05).

Zone placement, Knowledge membership, and Project relationship deliberately
live in separate stores. Every edge uses a qualified ``kind:id`` reference so
an id collision across primitive kinds cannot mutate or ground the wrong thing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .base import BaseRepository

RESOURCE_KINDS = frozenset({
    "meeting", "transcript", "artifact", "note", "knowledge", "zone",
    "project", "persona", "workflow", "sequence", "integration",
})


def qualified_ref(value: object) -> str:
    text = str(value or "").strip()
    kind, sep, resource_id = text.partition(":")
    kind = kind.strip().lower()
    resource_id = resource_id.strip()
    if not sep or not kind or not resource_id:
        raise ValueError("resource_ref must be qualified as kind:id")
    if kind not in RESOURCE_KINDS:
        raise ValueError(f"unknown resource kind: {kind}")
    return f"{kind}:{resource_id}"


def _now() -> str:
    return datetime.now().isoformat()


@dataclass(frozen=True)
class KnowledgeMembershipRecord:
    knowledge_id: str
    resource_ref: str
    created_at: str
    last_modified: str
    deleted: bool = False

    @property
    def id(self) -> str:
        return f"{self.knowledge_id}|{self.resource_ref}"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "knowledge_id": self.knowledge_id,
                "resource_ref": self.resource_ref, "created_at": self.created_at,
                "last_modified": self.last_modified, "deleted": self.deleted}


@dataclass(frozen=True)
class ProjectRelationshipRecord:
    project_id: str
    resource_ref: str
    relationship: str
    source: str
    confidence: float
    created_at: str
    last_modified: str
    deleted: bool = False

    @property
    def id(self) -> str:
        return f"{self.project_id}|{self.resource_ref}"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "project_id": self.project_id,
                "resource_ref": self.resource_ref, "relationship": self.relationship,
                "source": self.source, "confidence": self.confidence,
                "created_at": self.created_at, "last_modified": self.last_modified,
                "deleted": self.deleted}


class KnowledgeMembershipRepository(BaseRepository):
    def upsert(self, *, knowledge_id: str, resource_ref: str,
               last_modified: Optional[str] = None, deleted: bool = False,
               created_at: Optional[str] = None) -> KnowledgeMembershipRecord:
        kid, ref, now = str(knowledge_id or "").strip(), qualified_ref(resource_ref), _now()
        if not kid:
            raise ValueError("knowledge_id is required")
        with self._connection() as conn:
            if not deleted and conn.execute(
                "SELECT 1 FROM kbs WHERE id = ? AND deleted = 0", (kid,)
            ).fetchone() is None:
                raise ValueError(f"Unknown Knowledge: {kid}")
            prior = conn.execute(
                "SELECT created_at FROM knowledge_memberships WHERE knowledge_id=? AND resource_ref=?",
                (kid, ref),
            ).fetchone()
            conn.execute(
                """INSERT INTO knowledge_memberships
                   (knowledge_id, resource_ref, created_at, last_modified, deleted)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(knowledge_id, resource_ref) DO UPDATE SET
                     last_modified=excluded.last_modified, deleted=excluded.deleted""",
                (kid, ref, created_at or (prior[0] if prior else now),
                 last_modified or now, int(deleted)),
            )
            self._refresh_legacy_json(conn, kid)
        return self.get(kid, ref, include_deleted=True)  # type: ignore[return-value]

    def get(self, knowledge_id: str, resource_ref: str, *,
            include_deleted: bool = False) -> Optional[KnowledgeMembershipRecord]:
        kid, ref = str(knowledge_id or "").strip(), qualified_ref(resource_ref)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_memberships WHERE knowledge_id=? AND resource_ref=?",
                (kid, ref),
            ).fetchone()
        if row is None or (row["deleted"] and not include_deleted):
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False,
             limit: int = 5000) -> list[KnowledgeMembershipRecord]:
        where = "" if include_deleted else "WHERE deleted=0"
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM knowledge_memberships {where} "
                "ORDER BY last_modified DESC LIMIT ?", (max(1, min(limit, 10000)),)
            ).fetchall()
        return [self._row(row) for row in rows]

    def list_for_knowledge(self, knowledge_id: str) -> list[KnowledgeMembershipRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM knowledge_memberships WHERE knowledge_id=? AND deleted=0
                   ORDER BY last_modified DESC""", (str(knowledge_id).strip(),)
            ).fetchall()
        return [self._row(row) for row in rows]

    def list_for_resource(self, resource_ref: str) -> list[KnowledgeMembershipRecord]:
        ref = qualified_ref(resource_ref)
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM knowledge_memberships WHERE resource_ref=? AND deleted=0
                   ORDER BY last_modified DESC""", (ref,)
            ).fetchall()
        return [self._row(row) for row in rows]

    def delete(self, knowledge_id: str, resource_ref: str, *,
               last_modified: Optional[str] = None) -> bool:
        kid, ref = str(knowledge_id).strip(), qualified_ref(resource_ref)
        with self._connection() as conn:
            cur = conn.execute(
                """UPDATE knowledge_memberships SET deleted=1, last_modified=?
                   WHERE knowledge_id=? AND resource_ref=? AND deleted=0""",
                (last_modified or _now(), kid, ref),
            )
            self._refresh_legacy_json(conn, kid)
            return bool(cur.rowcount)

    @staticmethod
    def _refresh_legacy_json(conn: Any, knowledge_id: str) -> None:
        refs = [row[0] for row in conn.execute(
            """SELECT resource_ref FROM knowledge_memberships
               WHERE knowledge_id=? AND deleted=0 ORDER BY resource_ref""",
            (knowledge_id,),
        )]
        conn.execute("UPDATE kbs SET member_ids_json=? WHERE id=?",
                     (json.dumps(refs, separators=(",", ":")), knowledge_id))

    @staticmethod
    def _row(row: Any) -> KnowledgeMembershipRecord:
        return KnowledgeMembershipRecord(
            row["knowledge_id"], row["resource_ref"], row["created_at"],
            row["last_modified"], bool(row["deleted"]))


class ProjectRelationshipRepository(BaseRepository):
    def upsert(self, *, project_id: str, resource_ref: str,
               relationship: str = "member", source: str = "manual",
               confidence: float = 1.0, last_modified: Optional[str] = None,
               deleted: bool = False, created_at: Optional[str] = None,
               ) -> ProjectRelationshipRecord:
        pid, ref, now = str(project_id or "").strip(), qualified_ref(resource_ref), _now()
        relation = str(relationship or "member").strip().lower()
        if not pid:
            raise ValueError("project_id is required")
        if relation not in {"member", "source", "output", "related"}:
            raise ValueError(f"unknown project relationship: {relation}")
        with self._connection() as conn:
            if not deleted and conn.execute(
                "SELECT 1 FROM projects WHERE id=? AND is_archived=0", (pid,)
            ).fetchone() is None:
                raise ValueError(f"Unknown Project: {pid}")
            prior = conn.execute(
                "SELECT created_at FROM project_resources WHERE project_id=? AND resource_ref=?",
                (pid, ref),
            ).fetchone()
            conn.execute(
                """INSERT INTO project_resources
                   (project_id, resource_ref, relationship, source, confidence,
                    created_at, last_modified, deleted)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(project_id, resource_ref) DO UPDATE SET
                     relationship=excluded.relationship, source=excluded.source,
                     confidence=excluded.confidence, last_modified=excluded.last_modified,
                     deleted=excluded.deleted""",
                (pid, ref, relation, str(source or "manual").strip().lower(),
                 max(0.0, min(1.0, float(confidence))),
                 created_at or (prior[0] if prior else now),
                 last_modified or now, int(deleted)),
            )
        return self.get(pid, ref, include_deleted=True)  # type: ignore[return-value]

    def get(self, project_id: str, resource_ref: str, *,
            include_deleted: bool = False) -> Optional[ProjectRelationshipRecord]:
        pid, ref = str(project_id).strip(), qualified_ref(resource_ref)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_resources WHERE project_id=? AND resource_ref=?",
                (pid, ref),
            ).fetchone()
        if row is None or (row["deleted"] and not include_deleted):
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False,
             limit: int = 5000) -> list[ProjectRelationshipRecord]:
        where = "" if include_deleted else "WHERE deleted=0"
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM project_resources {where} "
                "ORDER BY last_modified DESC LIMIT ?", (max(1, min(limit, 10000)),)
            ).fetchall()
        return [self._row(row) for row in rows]

    def list_for_project(self, project_id: str) -> list[ProjectRelationshipRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM project_resources WHERE project_id=? AND deleted=0
                   ORDER BY last_modified DESC""", (str(project_id).strip(),)
            ).fetchall()
        return [self._row(row) for row in rows]

    def list_for_resource(self, resource_ref: str) -> list[ProjectRelationshipRecord]:
        ref = qualified_ref(resource_ref)
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM project_resources WHERE resource_ref=? AND deleted=0
                   ORDER BY last_modified DESC""", (ref,)
            ).fetchall()
        return [self._row(row) for row in rows]

    def delete(self, project_id: str, resource_ref: str, *,
               last_modified: Optional[str] = None) -> bool:
        pid, ref = str(project_id).strip(), qualified_ref(resource_ref)
        with self._connection() as conn:
            cur = conn.execute(
                """UPDATE project_resources SET deleted=1, last_modified=?
                   WHERE project_id=? AND resource_ref=? AND deleted=0""",
                (last_modified or _now(), pid, ref),
            )
            return bool(cur.rowcount)

    @staticmethod
    def _row(row: Any) -> ProjectRelationshipRecord:
        return ProjectRelationshipRecord(
            row["project_id"], row["resource_ref"], row["relationship"],
            row["source"], float(row["confidence"]), row["created_at"],
            row["last_modified"], bool(row["deleted"]))


__all__ = ["KnowledgeMembershipRecord", "KnowledgeMembershipRepository",
           "ProjectRelationshipRecord", "ProjectRelationshipRepository",
           "qualified_ref"]
