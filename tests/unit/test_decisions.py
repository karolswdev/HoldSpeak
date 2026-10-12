"""HS-109-01 durable decision identity and lifecycle."""
from __future__ import annotations

import datetime
import datetime as dt
import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
import holdspeak.services.monday_brief_service as brief_module
from holdspeak import operations
from holdspeak.db import Database
from holdspeak.db.core import Database, reset_database
from holdspeak.db.decisions import (
    DecisionPromotionRefused,
    DecisionTransitionRefused,
    anchor_decision_timestamp,
    derive_decision_id,
    derive_promoted_artifact_id,
    validate_source_timestamp,
)
from holdspeak.mcp import resources, tools
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.services.sync_service import SyncService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_decisions_router, build_primitives_router
from tests.unit.brief_rule_stub import quiet_needs_you  # noqa: F401  (a fixture)
from tests.unit.test_philo6_04_one_cause_one_row import _app as _app_visible


def _meeting(db: Database, meeting_id: str, started_at: str = "2026-07-01T09:30:00") -> None:
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


def _artifact(
    db: Database,
    artifact_id: str,
    meeting_id: str,
    entries: list[dict],
) -> None:
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": entries},
        plugin_id="decision_capture",
    )


def test_derived_id_is_stable_and_source_scoped() -> None:
    first = {"decision": "Ship the desk", "rationale": "Owner approved"}
    reordered = {"rationale": "Owner approved", "decision": "Ship the desk"}
    assert derive_decision_id("meeting-1", "artifact-1", first) == derive_decision_id(
        "meeting-1", "artifact-1", reordered
    )
    assert derive_decision_id("meeting-1", "artifact-1", first) != derive_decision_id(
        "meeting-2", "artifact-1", first
    )
    assert derive_decision_id("meeting-1", "artifact-1", first) != derive_decision_id(
        "meeting-1", "artifact-2", first
    )


def test_projection_is_idempotent(tmp_path) -> None:
    db = Database(tmp_path / "decisions.db")
    _meeting(db, "meeting-1")
    db.projects.create_project(project_id="project-1", name="Long memory")
    db.projects.associate_meeting_project(
        meeting_id="meeting-1", project_id="project-1", source="manual", confidence=1.0
    )
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [{"decision": "Ship the desk", "rationale": "Owner approved"}],
    )

    # Persisting the artifact IS the projection (the record_artifact
    # chokepoint) — the record exists before any explicit reconcile.
    decision = db.decisions.list()[0]
    first = db.decisions.reconcile_artifact("artifact-1")
    second = db.decisions.reconcile_artifact("artifact-1")

    assert first["unchanged"] == 1 and first["inserted"] == 0
    assert second == {
        "artifacts": 1,
        "decisions": 1,
        "inserted": 0,
        "updated": 0,
        "unchanged": 1,
        "skipped": 0,
    }
    assert [row.id for row in db.decisions.list()] == [decision.id]
    assert [row.id for row in db.decisions.list(project_key="project-1")] == [decision.id]
    assert [row.id for row in db.decisions.list(meeting_id="meeting-1")] == [decision.id]
    assert [row.id for row in db.decisions.list(lifecycle="recorded")] == [decision.id]
    assert decision.project_key == "project-1"
    assert decision.date_basis == "meeting_date"


def test_timestamp_validation_anchor_and_date_basis_transitions(tmp_path) -> None:
    segments = [
        {"text": "We will Ship   the Desk this week", "start_time": 5.0, "end_time": 9.0},
        {"text": "Next topic", "start_time": 10.0, "end_time": 14.0},
    ]
    assert validate_source_timestamp(segments, 5.0) == 5.0
    assert validate_source_timestamp(segments, 14.0) == 14.0
    assert validate_source_timestamp(segments, 14.001) is None
    assert anchor_decision_timestamp(segments, "ship the desk") == 5.0
    assert anchor_decision_timestamp(segments, "ship a desk") is None

    db = Database(tmp_path / "moments.db")
    _meeting(db, "meeting-1", "2026-07-01T09:30:00")
    _segments(
        db,
        "meeting-1",
        ("We will ship the desk this week", 5.0, 9.0),
        ("Next topic", 10.0, 14.0),
    )
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [
            {"decision": "Ship the desk", "source_timestamp": 8.5},
            {"decision": "Keep the fuzzy near match absent"},
        ],
    )
    rows = {row.text: row for row in db.decisions.list()}
    reported = rows["Ship the desk"]
    absent = rows["Keep the fuzzy near match absent"]
    assert reported.source_timestamp == 8.5
    assert reported.provenance_label == "reported"
    assert reported.date_basis == "transcript_moment"
    assert reported.decided_at == "2026-07-01T09:30:08.500000"
    assert absent.source_timestamp is None
    assert absent.provenance_label is None
    assert absent.date_basis == "meeting_date"
    assert absent.decided_at == "2026-07-01T09:30:00"


def test_resolver_maps_offset_to_meetings_own_segment(tmp_path) -> None:
    db = Database(tmp_path / "resolver.db")
    _meeting(db, "meeting-1")
    _meeting(db, "meeting-2")
    _segments(
        db,
        "meeting-1",
        ("Opening", 0.0, 4.0),
        ("The decision", 4.0, 9.0),
    )
    _segments(db, "meeting-2", ("Wrong meeting", 4.0, 9.0))

    moment = db.decisions.resolve_segment("meeting-1", 9.0)

    assert moment is not None
    assert moment.meeting_id == "meeting-1"
    assert moment.segment_index == 1
    assert moment.segment_start == 4.0
    assert moment.segment_end == 9.0
    assert moment.text == "The decision"
    assert db.decisions.resolve_segment("meeting-1", 9.001) is None


def test_lifecycle_transitions_and_bidirectional_supersession(tmp_path) -> None:
    db = Database(tmp_path / "lifecycle.db")
    _meeting(db, "meeting-1")
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [
            {"decision": "Use the old design"},
            {"decision": "Use the finished web spec"},
            {"decision": "Drop the experiment"},
        ],
    )
    db.decisions.reconcile_artifact("artifact-1")
    rows = {row.text: row for row in db.decisions.list()}

    accepted = db.decisions.accept(rows["Use the old design"].id, actor="owner-session")
    assert accepted.operation == "decision.accept"
    assert accepted.from_lifecycle == "recorded"
    assert accepted.to_lifecycle == "accepted"
    with pytest.raises(
        DecisionTransitionRefused, match="illegal_decision_lifecycle_transition"
    ):
        db.decisions.reject(rows["Use the old design"].id, actor="owner-session")

    db.decisions.reject(rows["Drop the experiment"].id, actor="owner-session")
    receipt = db.decisions.supersede(
        rows["Use the old design"].id,
        rows["Use the finished web spec"].id,
        actor="owner-session",
    )
    assert receipt.to_lifecycle == "superseded"
    old_lineage = db.decisions.get_with_lineage(rows["Use the old design"].id)
    new_lineage = db.decisions.get_with_lineage(rows["Use the finished web spec"].id)
    assert old_lineage["lineage"]["superseded_by"]["id"] == rows[
        "Use the finished web spec"
    ].id
    assert [row["id"] for row in new_lineage["lineage"]["supersedes"]] == [
        rows["Use the old design"].id
    ]


def test_meeting_delete_parks_and_the_decision_stays_linked(tmp_path) -> None:
    """``delete_meeting`` parks (PHILO-13: never delete). The meeting row, its
    artifact and the decision's source link all stay."""
    db = Database(tmp_path / "park.db")
    _meeting(db, "meeting-1")
    _artifact(db, "artifact-1", "meeting-1", [{"decision": "Memory survives"}])
    db.decisions.reconcile_artifact("artifact-1")
    decision_id = db.decisions.list()[0].id

    assert db.meetings.delete_meeting("meeting-1") is True
    survivor = db.decisions.get(decision_id)
    assert survivor is not None
    assert survivor.source_state == "linked"
    assert survivor.source_meeting_id == "meeting-1"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT parked FROM meetings WHERE id = 'meeting-1'"
        ).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 1


def test_a_removed_meeting_row_severs_source_without_deleting_decision(tmp_path) -> None:
    """The schema trigger still holds: if a meeting row ever leaves the table,
    the decision survives and says its source is gone. No product path deletes
    a meeting row today (``delete_meeting`` parks), so the row is removed here
    by SQL."""
    db = Database(tmp_path / "sever.db")
    _meeting(db, "meeting-1")
    _artifact(db, "artifact-1", "meeting-1", [{"decision": "Memory survives"}])
    db.decisions.reconcile_artifact("artifact-1")
    decision_id = db.decisions.list()[0].id

    with db._connection() as conn:
        conn.execute("DELETE FROM meetings WHERE id = 'meeting-1'")
    survivor = db.decisions.get(decision_id)
    assert survivor is not None
    assert survivor.source_state == "source_deleted"
    assert survivor.source_meeting_id == "meeting-1"


def test_identity_survives_provenance_reruns() -> None:
    """A rerun that gains a timestamp or sharper rationale updates the SAME
    record — identity anchors on the decision text (HS-109-02)."""
    bare = {"decision": "Ship the desk", "rationale": "v1"}
    timed = {"decision": "Ship the desk", "rationale": "sharper",
             "source_timestamp": 6.0}
    spaced = {"decision": "  Ship   the desk "}
    assert (
        derive_decision_id("m", "a", bare)
        == derive_decision_id("m", "a", timed)
        == derive_decision_id("m", "a", spaced)
    )
    assert derive_decision_id("m", "a", bare) != derive_decision_id(
        "m", "a", {"decision": "Do not ship the desk"}
    )
def test_promotion_id_and_decision_lineage_kind_round_trip(tmp_path) -> None:
    db = Database(tmp_path / "promotion.db")
    _meeting(db, "meeting-1")
    _artifact(db, "artifact-1", "meeting-1", [{"decision": "Keep the kernel honest"}])
    decision = db.decisions.list()[0]
    db.decisions.accept(decision.id, actor="owner-session")

    assert derive_promoted_artifact_id(decision.id, "adr") == derive_promoted_artifact_id(
        decision.id, "adr"
    )
    receipt = db.decisions.promote(decision.id, "adr", actor="owner-session")
    artifact = db.plugins.get_artifact(receipt.artifact_id)
    assert artifact is not None
    assert {tuple(source.values()) for source in artifact.sources} == {
        ("decision", decision.id),
        ("meeting", "meeting-1"),
    }
    reverse = db.plugins.list_artifacts_by_source("decision", decision.id)
    assert [row.id for row in reverse] == [artifact.id]
    forward = db.decisions.get_with_lineage(decision.id)
    assert [row["id"] for row in forward["lineage"]["derived_artifacts"]] == [artifact.id]


def test_supersession_marks_promoted_artifact_and_names_successor(tmp_path) -> None:
    db = Database(tmp_path / "superseded-promotion.db")
    _meeting(db, "meeting-1")
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [{"decision": "Old direction"}, {"decision": "New direction"}],
    )
    rows = {row.text: row for row in db.decisions.list()}
    old, successor = rows["Old direction"], rows["New direction"]
    db.decisions.accept(old.id, actor="owner-session")
    promoted = db.decisions.promote(old.id, "note", actor="owner-session")
    assert db.plugins.get_artifact(promoted.artifact_id).status == "accepted"

    db.decisions.supersede(old.id, successor.id, actor="owner-session")
    assert db.plugins.get_artifact(promoted.artifact_id).status == "rejected"
    with pytest.raises(
        DecisionPromotionRefused,
        match=f"superseded by {successor.id}; promote that one",
    ):
        db.decisions.promote(old.id, "note", actor="owner-session")


def test_promoted_artifact_does_not_reproject_as_a_decision(tmp_path) -> None:
    db = Database(tmp_path / "no-reprojection.db")
    _meeting(db, "meeting-1")
    _artifact(db, "artifact-1", "meeting-1", [{"decision": "One durable record"}])
    decision = db.decisions.list()[0]
    db.decisions.accept(decision.id, actor="owner-session")
    db.decisions.promote(decision.id, "decision_announcement", actor="owner-session")
    assert [row.id for row in db.decisions.list()] == [decision.id]


def test_invalid_artifact_source_kind_is_refused(tmp_path) -> None:
    db = Database(tmp_path / "source-kind.db")
    _meeting(db, "meeting-1")
    with pytest.raises(ValueError, match="Invalid artifact source type"):
        db.plugins.record_artifact(
            artifact_id="bad-source",
            meeting_id="meeting-1",
            artifact_type="note",
            title="Bad source",
            sources=[{"source_type": "decison", "source_ref": "d1"}],
        )


# ── from test_philo3_01_decision_route.py: PHILO-3-01 (A1): the desk decision create route answers, and the fence proves it did not. ──
#
# The defect: ``build_desk_decisions_router`` ran ``del ctx`` while its ``_svc``
# closure still read ``ctx``, so ``POST /api/decisions`` answered 500
# "cannot access free variable 'ctx'" on every desk (aa865f57, HS-200-45).


REPO = Path(__file__).resolve().parents[2]
ROUTE = "holdspeak/web/routes/primitives/decisions.py"
PRE_FIX_COMMIT = "7ce95358"  # main with the ratified Phase 3 charter; still carries `del ctx`

BODY = {
    "title": "Adopt the event bus for desk frames",
    "status": "accepted",
    "decision_markdown": "We use the one bus for every desk frame.",
    "context_markdown": "Source: meeting mtg-philo3-01 review",
    "tags": ["source:meeting:mtg-philo3-01"],
}


def _app(db: Database, monkeypatch, router_factory) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)

    # The hub's order (holdspeak/web_server.py): the lifecycle router is
    # included BEFORE the primitives router, so it owns GET /api/decisions/{id}.
    app.include_router(build_decisions_router(None))
    app.include_router(router_factory(WebContext(get_state=lambda: {})))
    return TestClient(app, raise_server_exceptions=False)


def test_post_decision_through_the_real_route_reads_back(tmp_path, monkeypatch):
    client = _app(Database(tmp_path / "d.db"), monkeypatch, build_primitives_router)
    created = client.post("/api/decisions", json=BODY)
    assert created.status_code == 201, created.text
    decision = created.json()["decision"]
    assert decision["id"].startswith("decision")

    read = client.get(f"/api/decisions/{decision['id']}")
    assert read.status_code == 200, read.text
    back = read.json()["decision"]
    assert back["id"] == decision["id"]
    assert back["title"] == BODY["title"]
    assert back["decision_markdown"] == BODY["decision_markdown"]
    assert back["context_markdown"] == BODY["context_markdown"]
    assert back["tags"] == BODY["tags"]
    assert back["status"] == "accepted"

    listed = client.get("/api/decisions").json()["decisions"]
    assert [d["id"] for d in listed] == [decision["id"]]


def test_pre_fix_route_answers_500_on_create(tmp_path, monkeypatch):
    source = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:{ROUTE}"],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout
    assert "    del ctx\n" in source  # the pre-fix shape this fence exercises
    name = "holdspeak.web.routes.primitives._philo3_01_prefix_decisions"
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "holdspeak.web.routes.primitives"
    sys.modules[name] = module
    try:
        exec(compile(source, f"<{PRE_FIX_COMMIT}:{ROUTE}>", "exec"), module.__dict__)
        client = _app(Database(tmp_path / "p.db"), monkeypatch, module.build_desk_decisions_router)
        created = client.post("/api/decisions", json=BODY)
    finally:
        sys.modules.pop(name, None)
    assert created.status_code == 500
    assert "cannot access free variable 'ctx'" in created.text


# ── from test_philo4_02_decision_rows.py: PHILO-4-02 red fences for decision provenance and Arrival order. ──


NOW = datetime.datetime(2026, 8, 4, 9, 30)


def _upsert_desk_decision(
    db: Database,
    *,
    decision_id: str,
    title: str,
    created_at: str,
) -> None:
    # This is the same durable desk-decision producer used by the desk. The
    # ids are deliberately not a recency signal.
    db.desk_decisions.upsert(
        decision_id=decision_id,
        title=title,
        status="proposed",
        created_at=created_at,
    )


def _fixed_uuid4(*values: str):
    sequence = iter(values)
    return lambda: uuid.UUID(next(sequence))


def test_generate_carries_created_at_on_every_decision_item(tmp_path, monkeypatch, quiet_needs_you):
    db = Database(tmp_path / "brief.db")
    service = MondayBriefService(db, clock=lambda: NOW)
    _upsert_desk_decision(
        db,
        decision_id="decision-z-old",
        title="Old decision one",
        created_at="2026-08-01T08:45:00",
    )
    _upsert_desk_decision(
        db,
        decision_id="decision-a-new",
        title="Newest decision",
        created_at="2026-08-04T08:45:00",
    )
    monkeypatch.setattr(
        brief_module,
        "uuid",
        SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32)),
    )

    generated = service.generate(None, now=NOW)
    reloaded = service.get_latest(None)
    assert reloaded is not None
    assert generated.id == reloaded.id
    assert [item.created_at for item in reloaded.sections["decisions"]] == [
        "2026-08-04T08:45:00",
        "2026-08-01T08:45:00",
    ]
    assert all(item.created_at for item in reloaded.sections["decisions"])


def test_generate_and_reload_sorts_decisions_by_record_created_at(tmp_path, monkeypatch, quiet_needs_you):
    db = Database(tmp_path / "brief.db")
    service = MondayBriefService(db, clock=lambda: NOW)
    _upsert_desk_decision(
        db,
        decision_id="decision-z-old",
        title="Old decision one",
        created_at="2026-08-01T08:45:00",
    )
    _upsert_desk_decision(
        db,
        decision_id="decision-m-old",
        title="Old decision two",
        created_at="2026-08-02T08:45:00",
    )
    _upsert_desk_decision(
        db,
        decision_id="decision-a-new",
        title="Newest decision",
        created_at="2026-08-04T08:45:00",
    )
    # The generated item ids are fixed only to make the pre-fix reload order
    # deterministic. The assertion below uses the record timestamps/text.
    monkeypatch.setattr(
        brief_module,
        "uuid",
        SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32, "2" * 32)),
    )

    service.generate(None, now=NOW)
    reloaded = service.get_latest(None)
    assert reloaded is not None
    assert [item.text for item in reloaded.sections["decisions"]] == [
        "Review decision: Newest decision",
        "Review decision: Old decision two",
        "Review decision: Old decision one",
    ]


def test_generate_carries_created_at_from_meeting_decision_projection(tmp_path):
    db = Database(tmp_path / "brief.db")
    db.meetings.save_meeting(
        MeetingState(
            id="meeting-decision-source",
            title="Decision fixture",
            started_at=datetime.datetime(2026, 8, 3, 8),
            ended_at=datetime.datetime(2026, 8, 3, 8, 30),
        )
    )
    db.plugins.record_artifact(
        artifact_id="decision-artifact",
        meeting_id="meeting-decision-source",
        artifact_type="decisions",
        title="Decision fixture",
        structured_json={"decisions": [{"decision": "Use the local desk"}]},
        plugin_id="decision_capture",
    )
    decision = db.decisions.list(lifecycle="recorded")[0]

    service = MondayBriefService(db, clock=lambda: NOW)
    service.generate(None, now=NOW)
    reloaded = service.get_latest(None)
    assert reloaded is not None
    item = next(
        item for item in reloaded.sections["decisions"]
        if item.text == "Review decision: Use the local desk"
    )
    assert item.created_at == decision.created_at


# ── from test_philo5_one_decision.py: PHILO-5-01: one decision through one contract. ──
#
# The fences, and what turns each one red:
#
# * **In-hub identity** (:class:`TestOneInstanceInTheHub`) — the REAL hub app
#   (``MeetingWebServer``) composes the contract once; the HTTP routes and MCP
#   ``/api/mcp`` reach the same registry, bound to the same ``PrimitiveService``
#   the hub composed. Deliberate mutation: bind a fresh ``PrimitiveService`` in
#   ``composition.install_from_web_context`` -> the identity assertion fails.
# * **Both transports go through invoke** — every decision call over HTTP and
#   over MCP is recorded by the registry's own ``invoke``. Deliberate mutation:
#   a route or the MCP branch that calls the service by hand -> the recording
#   misses it.
# * **Contract refusals** — unknown operation, authority in the arguments,
#   invalid arguments: named ``OperationRefused`` codes, surfaced through both
#   transports' existing envelopes.
# * **Compatibility** — tool names, input schemas and palette behaviour unchanged;
#   palette refusal proved THROUGH dispatch (``tools.py`` ``dispatch_for_palette``)
#   and through the HTTP JSON-RPC handler (MCP-005), plus catalogue filtering.
# * **The export** — ``docs/generated/operations.json`` equals the catalogue.
# * **The residual set** — the committed identities equal the tree's census.
# * **The Codex seams** live in ``test_philo5_codex_seams.py`` (it imports no
#   new symbol, so it runs unchanged on a copy of main for its red).


OWNER = Principal(PrincipalKind.OWNER, "owner")
TOKEN = "philo5-01-token"


def _load_script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ── the real hub, in-process ────────────────────────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The REAL hub app over an isolated database; the root it installed."""
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    root = composition.installed()
    assert root is not None and root.bare_root is False, "the hub installed no root"
    from starlette.testclient import TestClient

    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield server, root, client
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _mcp(client: Any, name: str, arguments: dict[str, Any]) -> Any:
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


class TestOneInstanceInTheHub:
    def test_both_transports_hold_the_one_registry_bound_to_the_hubs_instance(self, hub) -> None:
        _server, root, _client = hub
        ctx = root.web_context
        assert root.operations is not None
        assert ctx.operations is root.operations, "HTTP and MCP hold different registries"
        for name in ("decision.create", "decision.update", "decision.read", "decision.list"):
            assert root.operations.target(name) is root.primitive_service, name
            assert root.operations.target(name) is ctx.primitive_service, name
        # MCP dispatch resolves the SAME object, not a fresh binding.
        assert operations.for_runtime(lambda: pytest.fail("built a fresh one")) is root.operations
        assert operations.for_context(ctx) is root.operations

    def test_every_decision_call_over_http_and_mcp_goes_through_invoke(self, hub, monkeypatch) -> None:
        _server, root, client = hub
        registry = root.operations
        seen: list[str] = []
        real_invoke = registry.invoke

        def recording_invoke(principal: Any, name: str, args: Any = None) -> Any:
            seen.append(name)
            return real_invoke(principal, name, args)

        monkeypatch.setattr(registry, "invoke", recording_invoke)

        # HTTP: create, update, read, list (the hub's real route order).
        created = client.post("/api/decisions", json={"title": "Over HTTP", "status": "proposed"})
        assert created.status_code == 201, created.text
        http_id = created.json()["decision"]["id"]
        updated = client.put(f"/api/decisions/{http_id}", json={"status": "accepted"})
        assert updated.status_code == 200 and updated.json()["decision"]["status"] == "accepted"
        read = client.get(f"/api/decisions/{http_id}")
        assert read.status_code == 200 and read.json()["decision"]["id"] == http_id
        listed = client.get("/api/decisions")
        assert http_id in [d["id"] for d in listed.json()["decisions"]]
        http_calls = list(seen)
        assert http_calls == ["decision.create", "decision.update", "decision.read", "decision.list"]

        # MCP over /api/mcp: the same four, and they see the HTTP write.
        seen.clear()
        is_error, mcp_created = _mcp(client, "desk.create", {"kind": "decisions", "data": {"title": "Over MCP"}})
        assert is_error is False, mcp_created
        is_error, mcp_updated = _mcp(client, "desk.update", {"kind": "decisions", "id": mcp_created["id"], "data": {"status": "accepted"}})
        assert is_error is False and mcp_updated["status"] == "accepted"
        is_error, got = _mcp(client, "desk.get", {"kind": "decisions", "id": http_id})
        assert is_error is False and got["title"] == "Over HTTP"
        is_error, rows = _mcp(client, "desk.list", {"kind": "decisions"})
        assert {http_id, mcp_created["id"]} <= {row["id"] for row in rows}
        assert seen == ["decision.create", "decision.update", "decision.read", "decision.list"]

        # And HTTP reads the MCP write back (one database, one instance).
        back = client.get(f"/api/decisions/{mcp_created['id']}")
        assert back.status_code == 200 and back.json()["decision"]["status"] == "accepted"

    def test_the_http_envelopes_are_unchanged(self, hub) -> None:
        _server, _root, client = hub
        assert client.get("/api/decisions/nope").status_code == 404
        missing = client.put("/api/decisions/nope", json={"title": "x"})
        # PHILO-7-02: an admitted write refused by the service carries its
        # refusal receipt beside the unchanged error (Article XI; R2 class 2).
        body = missing.json()
        receipt = body.pop("receipt")
        assert missing.status_code == 404 and {k: v for k, v in body.items() if k != "operation_id"} == {"error": "Unknown decision: nope"}
        assert (receipt["state"], receipt["outcome"], receipt["operation_id"]) == ("refused", "not_found", body["operation_id"])
        bad = client.post("/api/decisions", json={"title": "t", "status": "nonsense"})
        bad_body = bad.json()
        assert bad.status_code == 400 and {k: v for k, v in bad_body.items() if k not in {"operation_id", "receipt"}} == {"error": "invalid decision status: nonsense"}
        assert bad_body["receipt"]["outcome"] == "invalid_value"  # PHILO-7-02: the refusal's receipt
        # The desk's rename sends `name` for a decision; it was accepted and
        # ignored before this contract and still is (not a new 400).
        made = client.post("/api/decisions", json={"title": "Keep"}).json()["decision"]
        renamed = client.put(f"/api/decisions/{made['id']}", json={"name": "ignored"})
        assert renamed.status_code == 200 and renamed.json()["decision"]["title"] == "Keep"
        assert client.post("/api/decisions", content=b"[]", headers={"Content-Type": "application/json"}).status_code == 400


def test_durable_state_survives_a_new_hub_over_the_same_database(tmp_path: Path, monkeypatch) -> None:
    """Across a restart the object differs; the durable row does not."""
    from starlette.testclient import TestClient

    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "restart.db")

    def boot() -> tuple[Any, Any]:
        reset_database()
        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                                get_state=MagicMock(return_value={})), auth_token=TOKEN)
        client = TestClient(server.app, client=("127.0.0.1", 50000))
        client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        return composition.installed(), client

    try:
        first_root, first = boot()
        is_error, made = _mcp(first, "desk.create", {"kind": "decisions", "data": {"title": "Before restart"}})
        assert is_error is False
        second_root, second = boot()
        assert second_root.operations is not first_root.operations
        is_error, again = _mcp(second, "desk.get", {"kind": "decisions", "id": made["id"]})
        assert is_error is False and again["title"] == "Before restart"
        assert second.get(f"/api/decisions/{made['id']}").json()["decision"] == again
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── the contract's own refusals ─────────────────────────────────────────


class _Primitives:
    """A bare real service over a real database (the registry binds to it)."""


@pytest.fixture
def registry(tmp_path: Path):
    from holdspeak.db import Database
    from holdspeak.services.primitive_service import PrimitiveService

    # PHILO-5-02: the catalogue grew past decisions; bind only what this
    # fixture holds (the lawful partial composition).
    return operations.bind_available({"primitive_service": PrimitiveService(Database(tmp_path / "r.db"))})


def test_the_catalogue_is_explicit_descriptors() -> None:
    names = [d.name for d in operations.DESCRIPTORS]
    # PHILO-5-01's four, then PHILO-5-02's loop, then PHILO-7-01's desk slice
    # -- an explicit list, no framework.
    assert names == [
        "decision.create", "decision.update", "decision.read", "decision.list",
        "meeting.list", "meeting.read", "meeting.import", "meeting.transcribe", "meeting.summary.run",
        "brief.generate", "brief.latest", "brief.shelf.write", "brief.shelf.read",
        "thought.create", "thought.save", "thought.read", "thought.workbench.read", "thought.list",
        # PHILO-7-01: the desk slice, one row per (kind, verb).
        "note.create", "note.read", "note.update", "note.delete", "note.list",
        "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
        "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
        # PHILO-7-02: membership, the remaining decision operations, the receipt read.
        "zone.file", "zone.unfile", "zone.members", "kb.member.add", "kb.member.remove", "kb.members",
        "decision.delete", "decision.status", "decision.supersede",
        "kernel.receipt.read",
        # Memory slice 4: the observations read; slice 5: the page read.
        "memory.observations.read", "memory.page.read",
        # PHILO-9-01: the Room on the contract, one row per operation.
        "project.list", "project.get", "project.get_room", "project.create", "project.door.create",
        "project.update", "project.archive", "project.restore", "project.link", "project.unlink",
        "project.open_review", "project.get_delta", "project.decide_proposal", "project.accept_review",
        "project.list_updates", "project.draft_update", "project.update_draft", "project.publish_update",
        "desk.needs_you",
        "project.item.list", "project.item.create", "project.item.update", "project.item.transition",
        "project.resource.list", "project.resource.add", "project.resource.remove",
        # PHILO-9-02: the steward, the nudges, the watches, the suggested
        # sources, the connections, the Door count and the delivery mark.
        "project.configure_steward", "project.run_steward", "project.stop_steward", "project.get_steward_run",
        "project.steward.trigger", "steward.nudges", "nudge.send", "nudge.dismiss",
        "project.watch.inspect", "project.watch.test", "project.watch.evaluate", "project.watch.set_rules",
        "project.watch.pause", "project.watch.resume", "project.watch.retire", "project.watch.update",
        "project.watch.baseline", "project.suggested_sources", "project.add_suggested_source",
        "project.dismiss_suggested_source", "connection.list", "connection.recheck", "project.door.count",
        "project.mark_update_delivered",
        # PHILO-10-01: the Send.
        "channel.destinations", "channel.save_destination", "channel.remove_destination",
        "channel.check_destination", "channel.preview", "channel.prepare", "channel.discard",
        "channel.send", "channel.sends",
        # PHILO-10-03: the email key (HTTP only; the key is a held input).
        "channel.save_email_key", "channel.save_slack_webhook",
        # The Conductor K1: the one-press hook install (HTTP only, owner only).
        "agent_hooks.install",
        # Conductor R7: the owner's People MCP access (config).
        "people_access.set",
        # PHILO-15 04: the owner's press opens the Calendars privacy pane (HTTP only).
        "calendar.open_settings",
        # PHILO-15 16: the owner names a Project's repository (HTTP only).
        "project.repository.register",
        # Conductor K2: Hand to agent.
        "agent.hand",
        # PHILO-16 16b: the desk's windows (the desk_window.* MCP tools).
        "windows.list", "windows.open", "windows.close", "windows.raise", "windows.arrange",
        "windows.seat",
    ]
    # decision.list takes the empty object; its one optional argument is the
    # HTTP limit (round two: it passes through instead of slicing 500 rows).
    from jsonschema import Draft202012Validator

    list_schema = dict(operations.DECISION_LIST.args_schema)
    Draft202012Validator(list_schema).validate({})
    assert set(list_schema["properties"]) == {"limit"} and list_schema["additionalProperties"] is False
    for descriptor in operations.DESCRIPTORS:
        assert descriptor.version == 1
        assert descriptor.effect in {"read", "write"}
        assert descriptor.refusals[:3] == ("unknown_operation", "invalid_arguments", "authority_in_arguments")
        assert descriptor.completion and descriptor.result and descriptor.exposure


def test_unknown_operation_is_a_named_refusal(registry) -> None:
    with pytest.raises(operations.OperationRefused) as exc:
        registry.invoke(OWNER, "decision.explode", {})
    assert exc.value.code == "unknown_operation"


@pytest.mark.parametrize("field", sorted(operations.AUTHORITY_FIELDS))
def test_an_authority_field_in_the_arguments_is_refused(registry, field) -> None:
    with pytest.raises(operations.OperationRefused) as exc:
        registry.invoke(OWNER, "decision.update", {"decision_id": "d", field: "owner"})
    assert exc.value.code == "authority_in_arguments"


def test_authority_is_refused_through_the_mcp_transport_too() -> None:
    from holdspeak.mcp.server import handle_message_for_principal

    response = handle_message_for_principal({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "desk.create", "arguments": {"kind": "decisions", "data": {"title": "x", "principal": "owner"}}},
    }, OWNER)
    result = response["result"]
    assert result["isError"] is True
    assert "the principal comes from the transport" in json.loads(result["content"][0]["text"])["error"]


def test_binding_fails_at_composition_not_on_first_call() -> None:
    with pytest.raises(RuntimeError, match="no primitive_service"):
        operations.bind({})
    with pytest.raises(RuntimeError, match="has no create_decision"):
        operations.bind({"primitive_service": _Primitives()})


# ── MCP compatibility: schemas, the decisions branch, palettes ─────────


def test_mcp_decisions_branch_validates_with_the_descriptor_schema() -> None:
    """The effective schema of ``desk.create kind=decisions`` IS the descriptor's.

    Pre-contract, an unknown field reached ``create_decision(**data)`` and
    failed as a Python ``TypeError``; now the descriptor refuses it by name.
    Deliberate mutation: bypass ``invoke`` in ``tools._primitive_create`` and
    this message disappears.
    """
    from holdspeak.mcp.tools import ToolError, dispatch

    with pytest.raises(ValueError) as exc:
        dispatch("desk.create", {"kind": "decisions", "data": {"title": "t", "bogus": 1}}, OWNER)
    assert not isinstance(exc.value, ToolError)
    assert isinstance(exc.value, operations.OperationRefused)
    assert exc.value.operation == "decision.create" and exc.value.code == "invalid_arguments"
    made = dispatch("desk.create", {"kind": "decisions", "data": {"title": "t"}}, OWNER)
    assert made["title"] == "t"


def test_published_desk_tool_schemas_are_unchanged_and_admit_every_contract_payload() -> None:
    from jsonschema import Draft202012Validator

    from holdspeak.mcp.tools import PRIMITIVE_KINDS, TOOLS

    by_name = {t["name"]: t["inputSchema"] for t in TOOLS}
    kind = {"type": "string", "enum": list(PRIMITIVE_KINDS)}
    assert by_name["desk.list"] == {"type": "object", "properties": {"kind": kind},
                                    "required": ["kind"], "additionalProperties": False}
    assert by_name["desk.get"]["required"] == ["kind", "id"]
    assert by_name["desk.create"]["properties"]["data"]["type"] == "object"
    assert by_name["desk.update"]["required"] == ["kind", "id", "data"]
    payload = {"title": "t", "status": "accepted", "tags": ["a"], "decided_at": None}
    Draft202012Validator(dict(operations.DECISION_CREATE.args_schema)).validate(payload)
    Draft202012Validator(by_name["desk.create"]).validate({"kind": "decisions", "data": payload})
    Draft202012Validator(by_name["desk.update"]).validate({"kind": "decisions", "id": "d", "data": payload})


def test_palette_refusal_through_dispatch_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import ToolError, dispatch_for_palette, tools_for_palette

    db = Database(tmp_path / "palette.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    read_only = frozenset({"desk.list", "desk.get"})
    assert {t["name"] for t in tools_for_palette(read_only)} == set(read_only)
    with pytest.raises(ToolError, match="not in the configured palette"):
        dispatch_for_palette("desk.create", {"kind": "decisions", "data": {"title": "x"}}, OWNER, read_only)
    assert db.desk_decisions.list() == []
    assert dispatch_for_palette("desk.list", {"kind": "decisions"}, OWNER, read_only) == []
    writable = read_only | {"desk.create"}
    made = dispatch_for_palette("desk.create", {"kind": "decisions", "data": {"title": "x"}}, OWNER, writable)
    assert [d.id for d in db.desk_decisions.list()] == [made["id"]]


def test_palette_refusal_through_the_http_jsonrpc_handler_is_mcp_005() -> None:
    from holdspeak.mcp.server import handle_message_for_principal

    response = handle_message_for_principal({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {"name": "desk.update", "arguments": {"kind": "decisions", "id": "d", "data": {}}},
    }, OWNER, palette=frozenset({"desk.list"}))
    assert response["error"]["code"] == -32005
    data = response["error"]["data"]
    assert {k: data[k] for k in ("code", "tool")} == {"code": "MCP-005", "tool": "desk.update"}
    # PHILO-7-02 round two: the palette refusal of an ADMITTED operation
    # (decision.update) carries its refusal receipt (readback).
    assert data["receipt"]["outcome"] == "mcp_palette_refused" and data["operation_id"] == data["receipt"]["operation_id"]


def test_other_kinds_still_take_the_generic_path(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import dispatch

    db = Database(tmp_path / "notes.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    note = dispatch("desk.create", {"kind": "notes", "data": {"title": "n"}}, OWNER)
    assert dispatch("desk.get", {"kind": "notes", "id": note["id"]}, OWNER)["title"] == "n"
    decision = dispatch("desk.create", {"kind": "decisions", "data": {"title": "d"}}, OWNER)
    # PHILO-7-02: decision.delete is a declared, ADMITTED operation now; its
    # MCP envelope is unchanged plus operation_id and the receipt.
    deleted = dispatch("desk.delete", {"kind": "decisions", "id": decision["id"]}, OWNER)
    assert {k: deleted[k] for k in ("deleted", "id")} == {"deleted": True, "id": decision["id"]}
    assert deleted["receipt"]["state"] == "succeeded" and deleted["operation_id"]


# ── the export and the residual set ─────────────────────────────────────


def test_operations_export_matches_the_catalogue() -> None:
    gen = _load_script("gen_operations_json")
    committed = (REPO / "docs" / "generated" / "operations.json").read_text(encoding="utf-8")
    assert committed == gen.render(), "regenerate: uv run python scripts/gen_operations_json.py"
    exported = json.loads(committed)["operations"]
    assert [op["name"] for op in exported] == [d.name for d in operations.DESCRIPTORS]
    for op, descriptor in zip(exported, operations.DESCRIPTORS):
        assert op["args_schema"] == json.loads(json.dumps(dict(descriptor.args_schema)))
        assert op["exposure"] == list(descriptor.exposure)


def test_the_residual_set_equals_the_trees_census() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    assert census.check(REPO, committed) == []
    for entry in committed["entries"]:
        assert entry["reason"], entry


def test_the_residual_fence_names_a_new_identity_and_a_stale_one() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    dropped = dict(committed, entries=committed["entries"][1:])
    problems = census.check(REPO, dropped)
    assert len(problems) == 1 and problems[0].startswith("NEW residual identity")
    stale = dict(committed, entries=committed["entries"] + [
        {"transport": "mcp", "entry_point": "desk.create", "discriminator": "kind=decisions", "reason": "x"}])
    problems = census.check(REPO, stale)
    assert len(problems) == 1 and problems[0].startswith("PAID entry still listed")


# ── from test_philo7_membership_decisions.py: PHILO-7-02 (step 1): membership and the remaining decision operations on the one contract. ──
#
# The fences, and what turns each one red:
#
# * **Nine explicit descriptors** -- ``zone.file``, ``zone.unfile``,
#   ``zone.members``, ``kb.member.add``, ``kb.member.remove``, ``kb.members``,
#   ``decision.delete``, ``decision.status``, ``decision.supersede`` -- each
#   naming its real ``PrimitiveService`` method and its Article XI admission as
#   the phase status's admission table rules it; plus the ONE new read,
#   ``kernel.receipt.read`` (the MCP tool ``kernel.receipt``).
# * **One instance, one ``invoke``** -- through the REAL hub
#   (``MeetingWebServer``): every HTTP route, MCP tool and the
#   ``holdspeak://zones/{id}/members`` resource of these operations is recorded
#   by the ONE registry's ``invoke``. Red on a ``git archive`` copy of main: the
#   recording is empty (the routes and tools called the service by hand).
# * **Envelopes unchanged** -- each transport answers with the envelope it gave
#   on main (plus ``operation_id`` and ``receipt`` for an admitted write).
# * **The residual set** -- identities 1, 6, 25, 28-33 paid; 293 -> 284; the
#   public tool count 228 -> 229, reported apart (the receipt read).


sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

NINE = (
    "zone.file", "zone.unfile", "zone.members", "kb.member.add", "kb.member.remove", "kb.members",
    "decision.delete", "decision.status", "decision.supersede",
)

#: The admission table, for these rows (phase status, "Article XI as ruled").
ADMISSION = {
    "zone.file": "admitted", "zone.unfile": "admitted", "zone.members": "exempt",
    "kb.member.add": "admitted", "kb.member.remove": "admitted", "kb.members": "exempt",
    "decision.delete": "admitted", "decision.status": "admitted", "decision.supersede": "admitted",
    "decision.create": "admitted", "decision.update": "admitted",
    "decision.read": "exempt", "decision.list": "exempt", "kernel.receipt.read": "exempt",
}

METHODS = {
    "zone.file": "file_member", "zone.unfile": "unfile_member", "zone.members": "list_directory_members",
    "kb.member.add": "add_kb_member", "kb.member.remove": "remove_kb_member", "kb.members": "list_kb_members",
    "decision.delete": "delete_decision", "decision.status": "update_decision_status",
    "decision.supersede": "supersede_decision",
}


def _descriptors() -> dict[str, Any]:
    from holdspeak import operations

    return {d.name: d for d in operations.DESCRIPTORS}


@pytest.fixture
def hub_decisions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def recorded(hub_decisions: Hub, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    registry = hub_decisions.root.operations
    seen: list[str] = []
    real_invoke = registry.invoke

    def recording_invoke(principal: Any, name: str, args: Any = None, **kwargs: Any) -> Any:
        seen.append(name)
        return real_invoke(principal, name, args, **kwargs)

    monkeypatch.setattr(registry, "invoke", recording_invoke)
    return seen


# ── the rows ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", NINE)
def test_each_row_names_its_real_method_and_its_admission(name: str) -> None:
    from holdspeak.services.primitive_service import PrimitiveService

    descriptor = _descriptors()[name]
    assert descriptor.service == "primitive_service" and descriptor.method == METHODS[name]
    assert callable(PrimitiveService.__dict__.get(descriptor.method)), name
    assert descriptor.owner_only is False, f"{name}: no owner-only refusal where main accepted"
    assert descriptor.admission is not None and descriptor.admission.rule == ADMISSION[name]
    assert descriptor.refusals[:3] == ("unknown_operation", "invalid_arguments", "authority_in_arguments")
    assert descriptor.result and descriptor.completion and descriptor.exposure


def test_the_decision_rows_and_the_receipt_read_declare_their_admission() -> None:
    rows = _descriptors()
    for name in ("decision.create", "decision.update", "decision.read", "decision.list", "kernel.receipt.read"):
        assert rows[name].admission is not None and rows[name].admission.rule == ADMISSION[name], name
    read = rows["kernel.receipt.read"]
    assert read.effect == "read" and read.exposure == ("mcp:kernel.receipt",)
    # decision.status has no separately named MCP tool (the phase status's
    # deferred question, decided): HTTP only; MCP's desk.update {status} is decision.update.
    assert [e for e in rows["decision.status"].exposure if e.startswith("mcp")] == []


def test_decision_delete_joins_the_desk_table() -> None:
    from holdspeak import operations

    assert operations.DESK_OPERATIONS[("decision", "delete")] == "decision.delete"


# ── one instance, one invoke (red on main: the recording is empty) ───────


def test_the_nine_are_bound_to_the_hubs_one_instance(hub_decisions: Hub) -> None:
    root = hub_decisions.root
    for name in NINE:
        assert root.operations.target(name) is root.primitive_service, name
    assert root.operations.target("kernel.receipt.read") is root.kernel_read_service


def test_http_routes_go_through_invoke(hub_decisions: Hub, recorded: list[str]) -> None:
    client = hub_decisions.client
    note = client.post("/api/notes", json={"title": "n"}).json()["note"]
    zone = client.post("/api/directories", json={"name": "Z"}).json()["directory"]
    kb = client.post("/api/kbs", json={"name": "K"}).json()["kb"]
    decision = client.post("/api/decisions", json={"title": "D"}).json()["decision"]
    recorded.clear()

    filed = client.put(f"/api/directories/{zone['id']}/members/note:{note['id']}")
    assert filed.status_code == 200 and filed.json()["membership"]["primitive_id"] == f"note:{note['id']}"
    listed = client.get(f"/api/directories/{zone['id']}/members")
    assert listed.status_code == 200 and listed.json()["directory_id"] == zone["id"]
    assert [m["primitive_id"] for m in listed.json()["members"]] == [f"note:{note['id']}"]
    unfiled = client.delete(f"/api/directories/{zone['id']}/members/note:{note['id']}")
    assert unfiled.status_code == 200 and unfiled.json()["success"] is True
    added = client.put(f"/api/kbs/{kb['id']}/members/note:{note['id']}")
    assert added.status_code == 200 and added.json()["member"]["resource_ref"] == f"note:{note['id']}"
    assert [m["resource_ref"] for m in client.get(f"/api/kbs/{kb['id']}/members").json()["members"]] == [f"note:{note['id']}"]
    removed = client.delete(f"/api/kbs/{kb['id']}/members/note:{note['id']}")
    assert removed.status_code == 200 and removed.json()["removed"] is True
    status = client.put(f"/api/decisions/{decision['id']}/status", json={"status": "accepted"})
    assert status.status_code == 200 and status.json()["decision"]["status"] == "accepted"
    successor = client.post(f"/api/decisions/{decision['id']}/supersede")
    assert successor.status_code == 201 and successor.json()["decision"]["title"].startswith("Superseding")
    deleted = client.delete(f"/api/decisions/{decision['id']}")
    assert deleted.status_code == 200 and deleted.json()["success"] is True

    assert recorded == [
        "zone.file", "zone.members", "zone.unfile", "kb.member.add", "kb.members", "kb.member.remove",
        "decision.status", "decision.supersede", "decision.delete",
    ]


def test_mcp_tools_verbs_and_the_resource_go_through_invoke(hub_decisions: Hub, recorded: list[str]) -> None:
    note = hub_decisions.client.post("/api/notes", json={"title": "n"}).json()["note"]
    zone = hub_decisions.client.post("/api/directories", json={"name": "Z"}).json()["directory"]
    kb = hub_decisions.client.post("/api/kbs", json={"name": "K"}).json()["kb"]
    first = hub_decisions.client.post("/api/decisions", json={"title": "D1"}).json()["decision"]
    second = hub_decisions.client.post("/api/decisions", json={"title": "D2"}).json()["decision"]
    recorded.clear()
    ref = f"note:{note['id']}"

    is_error, filed = hub_decisions.mcp("zone.file", {"directory_id": zone["id"], "primitive_id": ref})
    assert is_error is False and filed["primitive_id"] == ref and filed["directory_id"] == zone["id"]
    is_error, members = hub_decisions.mcp("zone.list_members", {"directory_id": zone["id"]})
    assert is_error is False and [m["primitive_id"] for m in members] == [ref]
    assert [m["primitive_id"] for m in hub_decisions.resource(f"holdspeak://zones/{zone['id']}/members")] == [ref]
    is_error, unfiled = hub_decisions.mcp("zone.unfile", {"directory_id": zone["id"], "primitive_id": ref})
    assert is_error is False and (unfiled["deleted"], unfiled["id"]) == (True, ref)
    is_error, added = hub_decisions.mcp("kb.add_member", {"kb_id": kb["id"], "ref": ref})
    assert is_error is False and added["resource_ref"] == ref
    is_error, listed = hub_decisions.mcp("kb.list_members", {"kb_id": kb["id"]})
    assert is_error is False and [m["resource_ref"] for m in listed] == [ref]
    is_error, removed = hub_decisions.mcp("kb.remove_member", {"kb_id": kb["id"], "ref": ref})
    assert is_error is False and (removed["deleted"], removed["id"]) == (True, ref)
    is_error, successor = hub_decisions.mcp("decision.supersede", {"decision_id": first["id"]})
    assert is_error is False and successor["title"].startswith("Superseding")
    is_error, deleted = hub_decisions.mcp("desk.delete", {"kind": "decisions", "id": first["id"]})
    assert is_error is False and (deleted["deleted"], deleted["id"]) == (True, first["id"])
    is_error, verb = hub_decisions.mcp("desk.verb", {"verb_id": "desk.delete", "arguments": {"kind": "decisions", "id": second["id"]}})
    assert is_error is False and (verb["deleted"], verb["id"]) == (True, second["id"])

    assert recorded == [
        "zone.file", "zone.members", "zone.members", "zone.unfile", "kb.member.add", "kb.members",
        "kb.member.remove", "decision.supersede", "decision.delete", "decision.delete",
    ]


def test_the_job_words_point_at_the_admitted_operations() -> None:
    """"put a decision on my review list" and "file a note into a zone" reach ADMITTED operations.

    The words are story 01's catalogue fence (``test_philo7_discovery.JOBS``,
    read from the real ``tools/list``); here: the tool each names is the
    admitted operation, and the receipt tool says how to read its receipt.
    """
    from test_philo7_discovery import JOBS

    from holdspeak import operations
    from holdspeak.mcp.tools import TOOLS

    rows = _descriptors()
    tool, _path = JOBS["file a note into a zone"]
    assert tool == "zone.file" and rows["zone.file"].admission.rule == "admitted"
    tool, path = JOBS["put a decision on my review list"]
    assert (tool, dict(path)["kind"]) == ("desk.create", "decisions")
    assert rows[operations.DESK_OPERATIONS[("decision", "create")]].admission.rule == "admitted"
    receipt_tool = {t["name"]: t for t in TOOLS}["kernel.receipt"]
    assert "receipt of a filing or decision write" in receipt_tool["description"]
    assert "operation_id" in receipt_tool["inputSchema"]["required"]


# ── from test_philo17_decisions_visible.py: PHILO-17 ("what did we decide yesterday?"): a meeting's decisions are ──
# readable per meeting, and Intelligence → Decisions lists every decision on
# the desk with its date and its meeting (``GET /api/decisions?scope=all``).


OWNER_visible = Principal(PrincipalKind.OWNER, "philo17-owner")


def _meeting_visible(db: Database, meeting_id: str, title: str, day: int, decisions: list[str]) -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id, title=title,
        started_at=dt.datetime(2026, 10, day, 9), ended_at=dt.datetime(2026, 10, day, 9, 30),
    ))
    if decisions:
        db.plugins.record_artifact(
            artifact_id=f"{meeting_id}-decisions", meeting_id=meeting_id, artifact_type="decisions",
            title="Meeting decisions", plugin_id="philo17",
            structured_json={"decisions": [{"decision": d, "rationale": "Agreed."} for d in decisions]},
        )


def _seed(db: Database) -> None:
    _meeting_visible(db, "m-sync", "Ledger cutover sync", 9, ["Freeze the old ledger on Nov 5", "Run reconciliation nightly"])
    _meeting_visible(db, "m-arch", "Architecture review", 8, ["Pilot OTel in billing"])
    db.desk_decisions.upsert(decision_id="d-adr", title="Use one schema", status="accepted",
                             decision_markdown="One schema.")


def test_decisions_per_meeting_are_that_meetings_only(tmp_path, monkeypatch):
    db = Database(tmp_path / "per-meeting.db")
    _seed(db)
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)

    body = client.get("/api/decisions", params={"meeting_id": "m-sync"}).json()

    assert sorted(d["text"] for d in body["decisions"]) == [
        "Freeze the old ledger on Nov 5", "Run reconciliation nightly"]
    assert {d["source_meeting_id"] for d in body["decisions"]} == {"m-sync"}


def test_scope_all_lists_every_decision_with_date_meeting_and_record(tmp_path, monkeypatch):
    db = Database(tmp_path / "ledger.db")
    _seed(db)
    freeze = next(d for d in db.decisions.list(meeting_id="m-sync") if d.text.startswith("Freeze"))
    record = DecisionRecordService(db).create_from_meeting(OWNER_visible, freeze.id)
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)

    response = client.get("/api/decisions", params={"scope": "all"})

    assert response.status_code == 200
    body = response.json()
    rows = body["decisions"]
    assert body["page"]["total"] == 4
    by_text = {row["text"]: row for row in rows}
    assert set(by_text) == {
        "Freeze the old ledger on Nov 5", "Run reconciliation nightly", "Pilot OTel in billing", "Use one schema"}
    sync = by_text["Freeze the old ledger on Nov 5"]
    assert (sync["source"], sync["meeting_id"], sync["meeting_title"]) == ("meeting", "m-sync", "Ledger cutover sync")
    assert sync["decided_at"].startswith("2026-10-09")
    assert sync["record_id"] == record["id"]
    assert sync["lifecycle"] == "active"  # the record's state wins over the row's
    assert by_text["Run reconciliation nightly"]["record_id"] is None
    desk = by_text["Use one schema"]
    assert (desk["source"], desk["meeting_id"], desk["meeting_title"]) == ("desk", None, None)
    assert desk["decided_at"]
    # Newest first.
    dates = [row["decided_at"] for row in rows]
    assert dates == sorted(dates, reverse=True)


def test_scope_all_pages_searches_and_reads_one_by_id(tmp_path, monkeypatch):
    db = Database(tmp_path / "pages.db")
    _seed(db)
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)

    first = client.get("/api/decisions", params={"scope": "all", "limit": 2}).json()
    second = client.get("/api/decisions", params={"scope": "all", "limit": 2, "offset": 2}).json()
    assert first["page"]["total"] == second["page"]["total"] == 4
    ids = [r["id"] for r in first["decisions"] + second["decisions"]]
    assert len(set(ids)) == 4

    found = client.get("/api/decisions", params={"scope": "all", "q": "cutover freeze"}).json()
    assert [r["text"] for r in found["decisions"]] == ["Freeze the old ledger on Nov 5"]
    assert found["page"]["total"] == 1

    oldest = second["decisions"][-1]
    one = client.get("/api/decisions", params={"scope": "all", "decision_id": oldest["id"], "limit": 1}).json()
    assert [r["id"] for r in one["decisions"]] == [oldest["id"]]

    mine = client.get("/api/decisions", params={"scope": "all", "meeting_id": "m-arch"}).json()
    assert [r["text"] for r in mine["decisions"]] == ["Pilot OTel in billing"]


def test_a_superseded_or_disputed_record_is_its_rows_state(tmp_path, monkeypatch):
    """Astra r1 (2): supersession and dispute change ``decision_records``
    only; the ledger row reads the record's state, not the source row's."""
    db = Database(tmp_path / "sealed.db")
    _seed(db)
    records = DecisionRecordService(db)
    sync = {d.text: d for d in db.decisions.list(meeting_id="m-sync")}
    old = records.create_from_meeting(OWNER_visible, sync["Freeze the old ledger on Nov 5"].id)
    new = records.create_from_meeting(OWNER_visible, sync["Run reconciliation nightly"].id)
    otel = records.create_from_meeting(OWNER_visible, db.decisions.list(meeting_id="m-arch")[0].id)
    records.supersede(OWNER_visible, old["id"], new["id"])
    records.dispute(OWNER_visible, otel["id"], "Not agreed.")
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)

    rows = {r["text"]: r for r in client.get("/api/decisions", params={"scope": "all"}).json()["decisions"]}

    assert rows["Freeze the old ledger on Nov 5"]["lifecycle"] == "superseded"
    assert rows["Pilot OTel in billing"]["lifecycle"] == "disputed"
    assert rows["Run reconciliation nightly"]["lifecycle"] == "active"


def test_a_confirmed_action_is_never_a_decision(tmp_path, monkeypatch):
    """Astra r1 (1), through the real producers: confirming an ACTION writes a
    ``decisions`` row and an action-kind record; the ledger (the meeting's
    record and Intelligence) never lists it. The confirmed decision is listed
    with the record its proposal names (the identity MeetingDetail joins on)."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.test_philo15_decisions_day_one import OWNER as DAY_ONE_OWNER
    from tests.unit.test_philo15_decisions_day_one import _proposals, _run

    db = _run(tmp_path, monkeypatch)
    service = ProposalBridgeService(db)
    rows = _proposals(db, "m-day-one")
    decision = next(p for p in rows if p["text"] == "Use SQLite for the local meeting ledger")
    action = next(p for p in rows if p["text"].startswith("Write the migration"))
    kept = service.confirm_proposal(DAY_ONE_OWNER, decision["id"])
    service.confirm_proposal(DAY_ONE_OWNER, action["id"])
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)

    for params in ({"scope": "all"}, {"scope": "all", "meeting_id": "m-day-one"}):
        listed = client.get("/api/decisions", params=params).json()["decisions"]
        texts = [r["text"] for r in listed]
        assert not [t for t in texts if t.startswith("Write the migration")], texts
        confirmed = [r for r in listed if r["text"] == "Use SQLite for the local meeting ledger"]
        assert kept["decision_record_id"] in {r["record_id"] for r in confirmed}, confirmed


def test_plain_list_still_answers_desk_decisions(tmp_path, monkeypatch):
    db = Database(tmp_path / "plain.db")
    _seed(db)
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)

    body = client.get("/api/decisions").json()

    assert [d["id"] for d in body["decisions"]] == ["d-adr"]


def _confirmed_decision(tmp_path, monkeypatch):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.test_philo15_decisions_day_one import OWNER as DAY_ONE_OWNER
    from tests.unit.test_philo15_decisions_day_one import _proposals, _run

    db = _run(tmp_path, monkeypatch)
    decision = next(p for p in _proposals(db, "m-day-one")
                    if p["text"] == "Use SQLite for the local meeting ledger")
    kept = ProposalBridgeService(db).confirm_proposal(DAY_ONE_OWNER, decision["id"])
    return db, kept["decision_record_id"]


def _paired_lifecycle(db, record_id, monkeypatch):
    client = _app_visible(db, SQLiteObserver(db._connection), monkeypatch)
    rows = client.get("/api/decisions", params={"scope": "all", "meeting_id": "m-day-one", "limit": 500}).json()
    return [r["lifecycle"] for r in rows["decisions"] if r["record_id"] == record_id]


def test_a_confirmed_decision_reads_replaced_after_its_record_is_superseded(tmp_path, monkeypatch):
    """Astra r2 (1), through the real producers: confirm a decision proposal,
    supersede its record. The meeting's ledger row (what MeetingDetail pairs
    with the proposal by ``decision_record_id``) reads ``superseded``."""
    db, record_id = _confirmed_decision(tmp_path, monkeypatch)
    records = DecisionRecordService(db)
    successor = records.create(OWNER_visible, decision_text="Use Postgres for the meeting ledger",
                               source_type="meeting", source_id="m-day-one")
    assert _paired_lifecycle(db, record_id, monkeypatch) == ["active"]
    records.supersede(OWNER_visible, record_id, successor["id"])
    assert _paired_lifecycle(db, record_id, monkeypatch) == ["superseded"]


def test_a_confirmed_decision_reads_disputed_after_its_record_is_disputed(tmp_path, monkeypatch):
    """Astra r2 (1): the same through ``dispute``."""
    db, record_id = _confirmed_decision(tmp_path, monkeypatch)
    DecisionRecordService(db).dispute(OWNER_visible, record_id, "Not agreed.")
    assert _paired_lifecycle(db, record_id, monkeypatch) == ["disputed"]


def test_a_confirmed_action_is_never_a_decision_search_hit(tmp_path, monkeypatch):
    """Astra r2 (2): a confirmed ACTION's decisions row is in the decision
    search index (the insert trigger); memory search never answers it as a
    ``decision:`` hit. The confirmed decision is still found."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.test_philo15_decisions_day_one import OWNER as DAY_ONE_OWNER
    from tests.unit.test_philo15_decisions_day_one import _proposals, _run

    db = _run(tmp_path, monkeypatch)
    service = ProposalBridgeService(db)
    rows = _proposals(db, "m-day-one")
    decision = next(p for p in rows if p["text"] == "Use SQLite for the local meeting ledger")
    action = next(p for p in rows if p["text"].startswith("Write the migration"))
    service.confirm_proposal(DAY_ONE_OWNER, decision["id"])
    service.confirm_proposal(DAY_ONE_OWNER, action["id"])

    with db._connection() as conn:
        action_row = conn.execute(
            "SELECT source_id FROM decision_records WHERE kind = 'action' AND source_type = 'meeting'"
        ).fetchone()[0]
        # The premise: the action's decisions row is in the decision index.
        assert conn.execute("SELECT COUNT(*) FROM decisions_memory_fts WHERE source_id = ?",
                            (action_row,)).fetchone()[0] == 1
    hits = db.memory.search("migration plan").hits
    refs = [h.source_ref for h in hits]
    assert f"decision:{action_row}" not in refs, refs
    assert not [h for h in hits if h.kind == "decision" and h.title.startswith("Write the migration")], refs
    # The action is still found, as an action.
    assert any(str(r).startswith("action:") for r in refs), refs
    found = db.memory.search("SQLite meeting ledger", kinds=["decision"]).hits
    assert any(str(h.source_ref).startswith("decision:") for h in found), [h.source_ref for h in found]


# ── from test_sync_decision_records_127.py: Local-first sync coverage for durable decision records (HS-127-10). ──


OWNER_records = Principal(PrincipalKind.OWNER, "record-sync-owner")


def test_sync_record_preserves_sources_work_revisions_and_tombstone(tmp_path) -> None:
    source_db = Database(tmp_path / "source.db")
    destination_db = Database(tmp_path / "destination.db")
    source = DecisionRecordService(source_db)
    created = source.create(
        OWNER_records, decision_text="Use Kafka for durable events.", rationale="Ordered replay.",
        source_type="desk", source_id="desk-kafka",
    )
    source.link_work(OWNER_records, created["id"], "project", "Kafka migration")
    source.update_record(OWNER_records, created["id"], {"owner": "Karol"})
    with source_db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_record_sources
               (id, record_id, source_type, source_ref, created_at)
               VALUES ('source-kafka', ?, 'artifact', 'artifact-kafka', '2026-08-07T00:00:00+00:00')""",
            (created["id"],),
        )

    payload = SyncService(source_db).pull(OWNER_records)
    received = SyncService(destination_db).push(OWNER_records, payload)
    copied = DecisionRecordService(destination_db).get(OWNER_records, created["id"])

    assert received["received"]["decision_records"] == 1
    assert copied is not None
    assert {(item["source_type"], item["source_ref"]) for item in copied["sources"]} == {("artifact", "artifact-kafka")}
    assert copied["work"][0]["work_ref"] == "Kafka migration"
    assert copied["revisions"][0]["field_name"] == "owner"

    with source_db._connection() as conn:
        conn.execute("UPDATE decision_records SET deleted = 1, updated_at = '2099-01-01T00:00:00+00:00' WHERE id = ?", (created["id"],))
    tombstone = SyncService(source_db).pull(OWNER_records)
    SyncService(destination_db).push(OWNER_records, tombstone)
    assert DecisionRecordService(destination_db).get(OWNER_records, created["id"]) is None


# ── from test_walk_decision_record_127.py: End-to-end service and MCP walk for HS-127 decision records. ──


OWNER_record = Principal(PrincipalKind.OWNER, "record-walk-owner")


def test_decision_record_walk_from_origins_through_mcp(tmp_path, monkeypatch) -> None:
    reset_database()
    db = Database(tmp_path / "record-walk.db")
    monkeypatch.setattr(tools, "get_database", lambda: db)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    monkeypatch.setattr(resources, "get_database", lambda: db)
    try:
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO meetings (id, started_at, title) VALUES ('meeting-127', '2026-08-07T09:00:00+00:00', 'Kafka choice')"
            )
            conn.execute(
                "INSERT INTO artifacts (id, meeting_id, artifact_type, title) VALUES ('artifact-127', 'meeting-127', 'decisions', 'Kafka choice')"
            )
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, decided_at, date_basis,
                   source_artifact_id, source_meeting_id, source_state, lifecycle,
                   created_at, updated_at, last_modified, deleted)
                   VALUES ('meeting-decision-127', 'Use Kafka for the event stream.',
                   'Ordered durable delivery.', '2026-08-07T09:01:00+00:00', 'meeting_date',
                   'artifact-127', 'meeting-127', 'linked', 'accepted',
                   '2026-08-07T09:01:00+00:00', '2026-08-07T09:01:00+00:00',
                   '2026-08-07T09:01:00+00:00', 0)"""
            )
        db.desk_decisions.upsert(
            decision_id="desk-decision-127", decision_markdown="Use Kafka with a schema registry."
        )
        service = DecisionRecordService(db)

        meeting_record = service.create_from_meeting(OWNER_record, "meeting-decision-127")
        desk_record = service.create_from_desk(OWNER_record, "desk-decision-127")
        meeting_full = service.get(OWNER_record, meeting_record["id"])
        assert meeting_full is not None
        assert {source["source_type"] for source in meeting_full["sources"]} == {"meeting", "artifact"}
        assert set(meeting_record) == set(desk_record)

        service.link_work(OWNER_record, meeting_record["id"], "project", "Kafka migration")
        assert service.records_for_work(OWNER_record, "project", "Kafka migration")[0]["id"] == meeting_record["id"]
        assert meeting_record["id"] in {record["id"] for record in service.search(OWNER_record, "Why Kafka?")}

        sealed = service.supersede(OWNER_record, meeting_record["id"], desk_record["id"], "Schema registry added.")
        successor = service.get(OWNER_record, desk_record["id"])
        assert sealed["successor_id"] == desk_record["id"]
        assert successor is not None and successor["predecessor_id"] == meeting_record["id"]

        returned = tools.dispatch("decision_record.get", {"record_id": desk_record["id"]}, OWNER_record)
        assert returned["id"] == desk_record["id"]
        assert tools.dispatch("decision_record.search", {"query": "Why Kafka?"}, OWNER_record)
        payload = json.loads(resources.read_resource(f"holdspeak://decision-records/{desk_record['id']}", OWNER_record)["contents"][0]["text"])
        assert payload["id"] == desk_record["id"]
    finally:
        reset_database()
