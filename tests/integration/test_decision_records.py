"""HS-109-01 archive backfill, synthesis reconciliation, and route authority."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
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
    """HS-132-12: rebuilt against the seam HS-131-07 actually shipped.

    The guard used to patch ``decisions._generate_with_model`` — a
    route-side model callable HS-131-07 deliberately deleted so drafting
    could only happen as the admitted promotion child inside
    ``DecisionLifecycleService`` (see decisions.py's HS-131-13 note). The
    invariant is unchanged and is asserted here at the real seam: the
    model provider is never entered until the kernel has admitted and
    approved the promotion operation, and the run leaves a receipt.
    """
    import holdspeak.web.routes.decisions as route_module
    from holdspeak.kernel.runtime import _configure

    db = Database(tmp_path / "model-promotion.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _artifact(db, "artifact-1", "meeting-1", "Use the bounded inference spine")
    decision = db.decisions.list()[0]
    db.decisions.accept(decision.id, actor="owner-session")
    # The routed branch obtains its sole model authority from an exact OWNER
    # capability assignment, not a request target override.
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    _profile(db, "promotion")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-integration-promotion", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion", "profile_revision": 1}],
    })
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

        def run_prompt(self, **_kwargs):
            # Generation can only be entered after the promotion operation
            # was admitted (submitted) and approved (decided).
            assert events[:2] == ["submit", "decide"], events
            events.append("generate")
            return "# Draft ADR\n\nGenerated for owner review."

    monkeypatch.setattr(broker, "submit", tracked_submit)
    monkeypatch.setattr(broker, "decide", tracked_decide)
    monkeypatch.setattr(route_module, "_kernel_service", lambda: broker)
    # The ONE model seam left: the kernel's inference runner builds the
    # engine for the admitted child. There is no route-side alternative.
    monkeypatch.setattr(
        broker.inference_runner, "_engine_factory", lambda _revision, **_kw: FakeIntel()
    )
    owner = _promotion_client(db, monkeypatch)

    response = owner.post(
        f"/api/decisions/{decision.id}/promote/adr/draft-with-model",
        json={},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert events[:2] == ["submit", "decide"]
    assert events[-1] == "generate"
    assert payload["artifact"]["status"] == "draft"
    assert payload["artifact"]["body_markdown"].startswith("# Draft ADR")
    assert payload["placement"] == {
        "source": "frozen_owner_assignment", "egress": {"scope": "local"}
    }
    # The promotion's own (parent) operation carries the run's receipt …
    parent = broker.store.operation(payload["operation_id"])
    parent_receipt = broker.store.receipt(payload["operation_id"])
    assert parent["name"] == "decision.promotion-draft"
    assert parent_receipt["outcome"] == "succeeded"
    # The receipt points at the artifact the admitted run actually produced.
    assert parent_receipt["result_ref"] == payload["artifact"]["id"]
    # … and the model call rode as its admitted inference child.
    child_id = payload["invocation"]["operation_id"]
    child = broker.store.operation(child_id)
    assert child["name"] == "inference.invoke"
    assert child["parent_operation_id"] == payload["operation_id"]
    assert broker.store.receipt(child_id)["outcome"] == "succeeded"


def _superseded_promotion_rig(db: Database):
    """One superseded decision and its named successor."""
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
    return old, successor


def test_superseded_promotion_route_refuses_without_a_model_call(
    tmp_path: Path, monkeypatch
) -> None:
    """HS-132-12: rebuilt against the seam HS-131-07 shipped.

    The old guard patched ``decisions._generate_with_model``, the
    route-side model callable HS-131-07 deleted. The only model path left
    is the kernel's inference runner, so the fence is planted there: a
    superseded decision is refused before anything is admitted, and the
    provider is never reached.
    """
    import holdspeak.web.routes.decisions as route_module
    from holdspeak.kernel.runtime import _configure

    db = Database(tmp_path / "refused-model-promotion.db")
    old, _successor = _superseded_promotion_rig(db)
    broker = _configure(db)
    calls = 0

    def forbidden_generation(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("model called without admission")

    monkeypatch.setattr(broker.inference_runner, "invoke", forbidden_generation)
    monkeypatch.setattr(route_module, "_kernel_service", lambda: broker)
    owner = _promotion_client(db, monkeypatch)
    response = owner.post(
        f"/api/decisions/{old.id}/promote/adr/draft-with-model",
        json={},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "decision_promotion_refused"
    assert body["decision_id"] == old.id
    assert calls == 0
    # Nothing was admitted: no promotion operation was ever opened.
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
        ).fetchone()[0] == 0
    # The successor IS named at the source of the refusal …
    from holdspeak.db.decisions import DecisionPromotionRefused

    with pytest.raises(DecisionPromotionRefused) as raised:
        db.decisions.assert_promotable(old.id)
    assert raised.value.detail == f"superseded by {_successor.id}; promote that one"


def test_superseded_promotion_route_names_successor(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "refused-names-successor.db")
    old, successor = _superseded_promotion_rig(db)
    owner = _promotion_client(db, monkeypatch)
    response = owner.post(
        f"/api/decisions/{old.id}/promote/adr/draft-with-model",
        json={},
    )
    assert response.status_code == 409
    assert successor.id in response.text
