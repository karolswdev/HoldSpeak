"""HS-109-04 cross-kind route authority and project grounding integration."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.grounding import hydrate_refs_detailed
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


def _seed(db: Database) -> None:
    db.projects.create_project(project_id="p1", name="Memory Project")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions
               (id,text,rationale,decided_at,date_basis,source_artifact_id,
                source_meeting_id,source_state,project_key,lifecycle,
                created_at,updated_at,last_modified,deleted)
               VALUES ('d1','Retry twice','bounded retry policy','2024-01-01',
                       'meeting_date','source-a','source-m','linked','p1','accepted',
                       '2024-01-01','2024-01-01','2024-01-01',0)"""
        )
    db.plugins.record_artifact(
        artifact_id="a1",
        meeting_id="",
        artifact_type="memo",
        title="Retry playbook",
        body_markdown="The retry policy has a bounded backoff.",
        updated_at="2025-01-01",
    )
    db.notes.upsert(
        note_id="n1",
        title="Retry note",
        body_markdown="Retry policy observations.",
        last_modified="2026-01-01",
        created_at="2026-01-01",
    )
    db.project_relationships.upsert(project_id="p1", resource_ref="artifact:a1")
    db.project_relationships.upsert(project_id="p1", resource_ref="note:n1")


def test_cross_kind_route_requires_read_principal_and_returns_citable_hits(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "route.db")
    _seed(db)
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={"id": "memory-route"}),
        ),
        host="127.0.0.1",
        auth_token="owner-secret",
    )
    owner = TestClient(server.app)
    anonymous = TestClient(server.app)
    anonymous.headers.pop("x-holdspeak-token", None)

    denied = anonymous.get("/api/memory/search", params={"query": "retry policy"})
    assert denied.status_code == 401
    assert denied.json()["missing_right"] == "read"

    response = owner.get(
        "/api/memory/search",
        params={"query": "retry policy", "project_id": "p1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert {hit["source_ref"] for hit in payload["hits"]} == {
        "decision:d1",
        "artifact:a1",
        "note:n1",
    }
    assert all(hit["snippet"] for hit in payload["hits"])
    assert payload["ranking"]["method"] == "per_kind_bm25_interleave"

    empty = owner.get(
        "/api/memory/search", params={"query": "unfindablequasar", "project_id": "p1"}
    )
    assert empty.status_code == 200
    assert empty.json()["hits"] == []
    assert empty.json()["page"]["total"] == 0


def test_project_hydration_relevance_differs_from_labeled_recency_fallback(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "grounding.db")
    db.projects.create_project(project_id="p1", name="Archive")
    db.notes.upsert(
        note_id="old-relevant",
        title="Retry policy",
        body_markdown="Retry twice with bounded backoff.",
        last_modified="2020-01-01",
        created_at="2020-01-01",
    )
    db.notes.upsert(
        note_id="new-irrelevant",
        title="Office lunch",
        body_markdown="Choose soup.",
        last_modified="2026-01-01",
        created_at="2026-01-01",
    )
    db.project_relationships.upsert(
        project_id="p1", resource_ref="note:old-relevant", last_modified="2020-01-01"
    )
    db.project_relationships.upsert(
        project_id="p1", resource_ref="note:new-irrelevant", last_modified="2026-01-01"
    )

    relevant = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=["project:p1"], query="retry backoff"
    )
    assert relevant.selection == "relevance"
    assert relevant.source_refs == ["note:old-relevant"]

    fallback = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=["project:p1"]
    )
    assert fallback.selection == "recency_fallback"
    assert fallback.source_refs[0] == "note:new-irrelevant"
    assert fallback.source_refs != relevant.source_refs
