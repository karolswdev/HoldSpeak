"""HS-109-01 archive backfill, synthesis reconciliation, and route authority."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.meeting_aftercare import _decisions_for_meeting
from holdspeak.plugins.builtin.decision_capture import DecisionCapturePlugin
from tests.unit.plugin_dispatch_rig import intel_plugin
from holdspeak.plugins.synthesis import synthesize_and_persist
from holdspeak.principals import agent_credentials
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


def _meeting(db: Database, meeting_id: str, started_at: str) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id,started_at,title) VALUES (?,?,?)",
            (meeting_id, started_at, meeting_id),
        )


def _segments(db: Database, meeting_id: str, *segments: tuple[str, float, float]) -> None:
    with db._connection() as conn:
        for text, start, end in segments:
            conn.execute(
                "INSERT INTO segments (meeting_id,text,speaker,start_time,end_time) VALUES (?,?,?,?,?)",
                (meeting_id, text, "Owner", start, end),
            )


def _artifact(db: Database, artifact_id: str, meeting_id: str, text: str) -> None:
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": [{"decision": text}]},
        plugin_id="decision_capture",
    )


def test_v30_migration_backfills_multi_meeting_archive_and_reruns_cleanly(
    tmp_path: Path,
) -> None:
    path = tmp_path / "archive.db"
    seeded = Database(path)
    _meeting(seeded, "meeting-1", "2026-06-01T10:00:00")
    _meeting(seeded, "meeting-2", "2026-06-02T10:00:00")
    _artifact(seeded, "artifact-1", "meeting-1", "Keep local-first")
    _artifact(seeded, "artifact-2", "meeting-2", "Keep local-first")
    with seeded._connection() as conn:
        conn.execute("DROP TABLE decisions")
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version(version) VALUES (29)")

    migrated = Database(path)
    rows = migrated.decisions.list()
    assert len(rows) == 2
    assert len({row.id for row in rows}) == 2
    assert {row.source_meeting_id for row in rows} == {"meeting-1", "meeting-2"}
    assert migrated.decisions.backfill() == {
        "artifacts": 2,
        "decisions": 2,
        "inserted": 0,
        "updated": 0,
        "unchanged": 2,
        "skipped": 0,
    }


def test_synthesis_persistence_reconciles_decisions_without_plugin_changes(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "synthesis.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    drafts, _lineage = synthesize_and_persist(
        db,
        "meeting-1",
        plugin_runs=[
            {
                "id": "run-1",
                "meeting_id": "meeting-1",
                "window_id": "window-1",
                "plugin_id": "decision_capture",
                "plugin_version": "1",
                "status": "success",
                "created_at": "2026-07-01T10:05:00",
                "output": {
                    "summary": "One decision",
                    "decisions": [
                        {"decision": "Use the persisted record", "rationale": "Queryable"}
                    ],
                },
            }
        ],
    )

    assert [draft.artifact_type for draft in drafts] == ["decisions"]
    assert [row.text for row in db.decisions.list()] == ["Use the persisted record"]
    before = db.decisions.list()[0].id
    synthesize_and_persist(db, "meeting-1", plugin_runs=[{
        "id": "run-1", "meeting_id": "meeting-1", "window_id": "window-1",
        "plugin_id": "decision_capture", "plugin_version": "1", "status": "success",
        "created_at": "2026-07-01T10:05:00",
        "output": {"summary": "One decision", "decisions": [
            {"decision": "Use the persisted record", "rationale": "Queryable"}
        ]},
    }])
    assert [row.id for row in db.decisions.list()] == [before]


def test_capture_projection_carries_reported_moment_and_records_named_drop(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "capture-moment.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    segments = [
        {"text": "Use the durable record", "speaker": "Owner", "start_time": 20.0, "end_time": 28.0}
    ]
    _segments(db, "meeting-1", ("Use the durable record", 20.0, 28.0))
    response = """```json
{"decisions": [
  {"decision": "Use the durable record", "rationale": "Queryable", "source_timestamp": 24.0},
  {"decision": "Do not invent provenance", "rationale": null, "source_timestamp": 99.0}
], "open_questions": []}
```"""
    output = intel_plugin(
        DecisionCapturePlugin(), lambda _messages, **_kw: response
    ).run({"transcript": "Use the durable record", "transcript_segments": segments})
    db.plugins.record_plugin_run(
        meeting_id="meeting-1",
        window_id="window-1",
        plugin_id="decision_capture",
        plugin_version="1",
        status="success",
        output=output,
    )
    persisted_run = db.plugins.list_plugin_runs("meeting-1")[0]
    assert persisted_run.output["provenance_drops"][0]["reason"] == "source_timestamp_out_of_range"
    assert persisted_run.output["provenance_drops"][0]["field"] == "source_timestamp"

    synthesize_and_persist(
        db,
        "meeting-1",
        plugin_runs=[
            {
                "id": "run-1",
                "meeting_id": "meeting-1",
                "window_id": "window-1",
                "plugin_id": "decision_capture",
                "plugin_version": "1",
                "status": "success",
                "created_at": "2026-07-01T10:01:00",
                "output": output,
            }
        ],
    )
    records = {record.text: record for record in db.decisions.list()}
    reported = records["Use the durable record"]
    assert reported.source_timestamp == 24.0
    assert reported.provenance_label == "reported"
    assert reported.date_basis == "transcript_moment"
    assert reported.decided_at == "2026-07-01T10:00:24"
    assert records["Do not invent provenance"].source_timestamp is None


def test_archive_backfill_anchors_exact_substring_only(tmp_path: Path) -> None:
    db = Database(tmp_path / "anchor-backfill.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _artifact(db, "artifact-1", "meeting-1", "Keep local-first")
    _artifact(db, "artifact-2", "meeting-1", "Choose a fuzzy near match")
    assert all(record.date_basis == "meeting_date" for record in db.decisions.list())
    _segments(
        db,
        "meeting-1",
        ("We agreed to keep local-first for the archive", 31.0, 38.0),
        ("We should choose the fuzzy near matching option", 40.0, 47.0),
    )

    result = db.decisions.backfill()
    records = {record.text: record for record in db.decisions.list()}

    assert result["updated"] == 1
    assert records["Keep local-first"].source_timestamp == 31.0
    assert records["Keep local-first"].provenance_label == "anchored"
    assert records["Keep local-first"].date_basis == "transcript_moment"
    assert records["Choose a fuzzy near match"].source_timestamp is None
    assert records["Choose a fuzzy near match"].date_basis == "meeting_date"


def test_decision_moment_agrees_with_aftercare_provenance(tmp_path: Path) -> None:
    db = Database(tmp_path / "aftercare-agreement.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _segments(
        db,
        "meeting-1",
        ("Opening context", 0.0, 10.0),
        ("Use Postgres for durable memory", 10.0, 18.0),
    )
    db.plugins.record_artifact(
        artifact_id="artifact-1",
        meeting_id="meeting-1",
        artifact_type="decisions",
        title="Decisions",
        structured_json={
            "decisions": [{"decision": "Use Postgres", "source_timestamp": 12.0}]
        },
        plugin_id="decision_capture",
    )
    decision = db.decisions.list()[0]
    meeting = db.meetings.get_meeting("meeting-1")
    aftercare = _decisions_for_meeting(db, "meeting-1", meeting.segments)[0]
    moment = db.decisions.resolve_decision_moment(decision.id)

    assert moment is not None
    assert aftercare["source_timestamp"] == decision.source_timestamp == moment.source_timestamp
    assert aftercare["provenance"]["segment_index"] == moment.segment_index
    assert aftercare["provenance"]["segment_start"] == moment.segment_start
    assert aftercare["provenance"]["text_preview"] == moment.text[:120]


def test_v32_migration_adds_decision_moment_columns(tmp_path: Path) -> None:
    path = tmp_path / "v30.db"
    seeded = Database(path)
    with seeded._connection() as conn:
        conn.execute("ALTER TABLE decisions DROP COLUMN provenance_label")
        conn.execute("ALTER TABLE decisions DROP COLUMN source_timestamp")
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version(version) VALUES (30)")

    migrated = Database(path)
    with migrated._connection() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(decisions)")}
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert {"source_timestamp", "provenance_label"}.issubset(columns)
    assert version == 32


def test_decision_routes_require_read_authority_and_owner_lifecycle_principal(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "routes.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _segments(db, "meeting-1", ("We will keep the source memory", 5.0, 11.0))
    _artifact(db, "artifact-1", "meeting-1", "Keep the source memory")
    db.decisions.reconcile_artifact("artifact-1")
    decision_id = db.decisions.list()[0].id
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    callbacks = WebRuntimeCallbacks(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={"id": "decision-routes"}),
    )
    server = MeetingWebServer(
        callbacks, host="127.0.0.1", auth_token="owner-secret"
    )
    owner = TestClient(server.app)

    anonymous = TestClient(server.app)
    anonymous.headers.pop("x-holdspeak-token", None)
    denied_read = anonymous.get("/api/decisions")
    assert denied_read.status_code == 401
    assert denied_read.json()["principal"] == "none"
    assert denied_read.json()["missing_right"] == "read"
    denied_moment = anonymous.get(f"/api/decisions/{decision_id}/moment")
    assert denied_moment.status_code == 401
    assert denied_moment.json()["missing_right"] == "read"

    issued = owner.post(
        "/api/principals/agents", json={"identity": "claude:decision-reader"}
    ).json()
    agent = TestClient(server.app)
    agent.headers.pop("x-holdspeak-token", None)
    agent.headers["Authorization"] = f"Bearer {issued['credential']}"
    denied_agent_read = agent.get("/api/decisions")
    assert denied_agent_read.status_code == 403
    assert denied_agent_read.json()["principal"] == "agent"
    assert denied_agent_read.json()["missing_right"] == "read"
    denied_write = agent.post(f"/api/decisions/{decision_id}/accept")
    assert denied_write.status_code == 403
    assert denied_write.json()["principal"] == "agent"
    assert denied_write.json()["missing_right"] == "owner"

    listed = owner.get("/api/decisions", params={"meeting_id": "meeting-1"})
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()["decisions"]] == [decision_id]
    moment = owner.get(f"/api/decisions/{decision_id}/moment")
    assert moment.status_code == 200
    assert moment.json()["provenance_label"] == "anchored"
    assert moment.json()["moment"]["segment_start"] == 5.0
    assert moment.json()["moment"]["text"] == "We will keep the source memory"
    accepted = owner.post(f"/api/decisions/{decision_id}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["receipt"]["actor"] == "owner-session"
    assert accepted.json()["receipt"]["operation"] == "decision.accept"
    illegal = owner.post(f"/api/decisions/{decision_id}/reject")
    assert illegal.status_code == 409
    assert illegal.json()["error"] == "illegal_decision_lifecycle_transition"
    agent_credentials.revoke("claude:decision-reader")


def test_v32_migration_rebuilds_a_stale_check_table(tmp_path: Path) -> None:
    """A v30 build briefly baked CHECK (date_basis IN ('meeting_date')) into
    live tables; the v32 step must rebuild such tables so transcript moments
    can land, carrying every row and keeping the memory-FTS triggers alive."""
    path = tmp_path / "stale.db"
    seeded = Database(path)
    with seeded._connection() as conn:
        conn.executescript(
            """
            DROP TABLE decisions;
            CREATE TABLE decisions (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                rationale TEXT,
                decided_at TEXT NOT NULL,
                date_basis TEXT NOT NULL DEFAULT 'meeting_date'
                    CHECK (date_basis IN ('meeting_date')),
                source_artifact_id TEXT NOT NULL,
                source_meeting_id TEXT NOT NULL,
                source_state TEXT NOT NULL DEFAULT 'linked',
                project_key TEXT,
                lifecycle TEXT NOT NULL DEFAULT 'recorded',
                superseded_by TEXT REFERENCES decisions(id),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_modified TEXT NOT NULL DEFAULT (datetime('now')),
                deleted INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO decisions (id, text, decided_at, source_artifact_id,
                                   source_meeting_id)
            VALUES ('dec-stale-1', 'Keep the stale row', '2026-01-01T00:00:00',
                    'art-1', 'meeting-1');
            DELETE FROM schema_version;
            INSERT INTO schema_version(version) VALUES (30);
            """
        )

    migrated = Database(path)
    with migrated._connection() as conn:
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='decisions'"
        ).fetchone()[0]
        rows = conn.execute("SELECT id FROM decisions").fetchall()
        triggers = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )
        }
        conn.execute(
            "UPDATE decisions SET date_basis='transcript_moment' "
            "WHERE id='dec-stale-1'"
        )
    assert "date_basis IN ('meeting_date')" not in ddl
    assert [row[0] for row in rows] == ["dec-stale-1"]
    assert {"decisions_memory_ai", "decisions_memory_ad",
            "decisions_memory_au", "decisions_sever_meeting_source"} <= triggers
def _promotion_client(db: Database, monkeypatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    callbacks = WebRuntimeCallbacks(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={"id": "decision-promotion"}),
    )
    return TestClient(
        MeetingWebServer(
            callbacks, host="127.0.0.1", auth_token="owner-secret"
        ).app
    )


def test_promote_route_is_idempotent_and_queryable_both_ways(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "promote-route.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _artifact(db, "artifact-1", "meeting-1", "Keep causal memory")
    decision = db.decisions.list()[0]
    db.decisions.accept(decision.id, actor="owner-session")
    owner = _promotion_client(db, monkeypatch)

    first = owner.post(f"/api/decisions/{decision.id}/promote/adr")
    second = owner.post(f"/api/decisions/{decision.id}/promote/adr")
    assert first.status_code == second.status_code == 200
    assert first.json()["artifact"]["id"] == second.json()["artifact"]["id"]
    assert first.json()["artifact"]["status"] == "accepted"
    assert {(s["source_type"], s["source_ref"]) for s in first.json()["artifact"]["sources"]} == {
        ("decision", decision.id),
        ("meeting", "meeting-1"),
    }
    assert len(db.plugins.list_artifacts_by_source("decision", decision.id)) == 1
    read_back = owner.get(f"/api/decisions/{decision.id}").json()
    assert [a["id"] for a in read_back["lineage"]["derived_artifacts"]] == [
        first.json()["artifact"]["id"]
    ]


def test_model_promotion_admits_before_generation_and_leaves_receipt(
    tmp_path: Path, monkeypatch
) -> None:
    import holdspeak.web.routes.decisions as route_module
    from holdspeak.kernel.runtime import _configure

    db = Database(tmp_path / "model-promotion.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _artifact(db, "artifact-1", "meeting-1", "Use the bounded inference spine")
    decision = db.decisions.list()[0]
    db.decisions.accept(decision.id, actor="owner-session")
    broker = _configure(db)
    events: list[str] = []
    original_submit = broker.submit
    original_decide = broker.decide

    def tracked_submit(*args, **kwargs):
        events.append("submit")
        return original_submit(*args, **kwargs)

    def tracked_decide(*args, **kwargs):
        events.append("decide")
        return original_decide(*args, **kwargs)

    class FakeIntel:
        active_provider = "fake"

    async def fake_generate(_db, _target, _prompt):
        # Generation can only be entered after the operation was admitted and approved.
        assert events == ["submit", "decide"]
        events.append("generate")
        return "# Draft ADR\n\nGenerated for owner review.", FakeIntel()

    monkeypatch.setattr(broker, "submit", tracked_submit)
    monkeypatch.setattr(broker, "decide", tracked_decide)
    monkeypatch.setattr(route_module, "_kernel_service", lambda: broker)
    monkeypatch.setattr(route_module, "_generate_with_model", fake_generate)
    owner = _promotion_client(db, monkeypatch)

    response = owner.post(
        f"/api/decisions/{decision.id}/promote/adr/draft-with-model",
        json={"inference_target_id": "this_machine"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert events == ["submit", "decide", "generate"]
    assert payload["artifact"]["status"] == "draft"
    assert payload["artifact"]["body_markdown"].startswith("# Draft ADR")
    assert payload["inference_target"]["id"] == "this_machine"
    operation = broker.store.operation(payload["operation_id"])
    receipt = broker.store.receipt(payload["operation_id"])
    assert operation["name"] == "inference.run"
    assert receipt["outcome"] == "succeeded"
    assert receipt["result_ref"] == f"artifact:{payload['artifact']['id']}"


def test_superseded_promotion_route_names_successor_without_model_call(
    tmp_path: Path, monkeypatch
) -> None:
    import holdspeak.web.routes.decisions as route_module

    db = Database(tmp_path / "refused-model-promotion.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    db.plugins.record_artifact(
        artifact_id="artifact-1",
        meeting_id="meeting-1",
        artifact_type="decisions",
        title="Decisions",
        structured_json={
            "decisions": [
                {"decision": "Old direction"},
                {"decision": "Successor direction"},
            ]
        },
        plugin_id="decision_capture",
    )
    rows = {row.text: row for row in db.decisions.list()}
    old, successor = rows["Old direction"], rows["Successor direction"]
    db.decisions.accept(old.id, actor="owner-session")
    db.decisions.supersede(old.id, successor.id, actor="owner-session")
    calls = 0

    async def forbidden_generation(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("model called without admission")

    monkeypatch.setattr(route_module, "_generate_with_model", forbidden_generation)
    owner = _promotion_client(db, monkeypatch)
    response = owner.post(
        f"/api/decisions/{old.id}/promote/adr/draft-with-model",
        json={"inference_target_id": "this_machine"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == (
        f"superseded by {successor.id} — promote that one"
    )
    assert calls == 0
