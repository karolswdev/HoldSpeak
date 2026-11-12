"""Review 11a: the shown snapshot, including related words, governs a write."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from holdspeak.meeting_session import MeetingState, TranscriptSegment, IntelSnapshot
from holdspeak.timestamps import utc_now
from holdspeak.services.errors import ConflictError
from holdspeak.services.proposal_bridge_service import ProposalBridgeService
from holdspeak.services.watch_service import WatchService
from tests.integration.test_room_answer_bindings import hub, OWNER
from tests.watch_seed import seed_watch


def bulk(hub):
    mid = "review-batch"
    hub.db.meetings.save_meeting(MeetingState(id=mid, title="Review snapshot", started_at=utc_now(),
        segments=[TranscriptSegment(text="Keep the reviewed plan.", speaker="Me", start_time=0, end_time=10)],
        intel_status="completed", intel=IntelSnapshot(timestamp=1, topics=[], summary="Keep the reviewed plan.", action_items=[])))
    for kind, text in (("decision", "Keep the reviewed plan"), ("action", "Send the plan")):
        hub.db.proposals.create_proposal(meeting_id=mid, project_id=None, kind=kind, text=text,
            owner_hint="Me", due_hint="Friday", source_plugin="decision_capture", support="supported")
    service = ProposalBridgeService(hub.db)
    shown = service.meeting_review(mid)
    bindings = [row["binding"] for row in shown["proposals"] if row["state"] == "proposed"]
    return mid, service, shown, bindings


@pytest.mark.parametrize("transport", ("service", "http"))
@pytest.mark.parametrize("case", ("missing", "missing_row", "new_row", "stale", "good"))
def test_bulk_answer_is_one_held_snapshot(hub, transport, case):
    mid, service, shown, bindings = bulk(hub)
    if case == "missing_row":
        bindings = bindings[:1]
    if case == "new_row":
        hub.db.proposals.create_proposal(meeting_id=mid, project_id=None, kind="decision", text="A later plan", source_plugin="decision_capture", support="supported")
    if case == "stale":
        service.edit_proposal(OWNER, shown["proposals"][-1]["id"], text="A changed plan")
    body = {} if case == "missing" else {"bindings": bindings}
    if transport == "http":
        result = hub.client.post(f"/api/meetings/{mid}/proposals/accept-reviewed", json=body)
        assert result.status_code == (200 if case == "good" else 409), result.text
        if case != "good":
            assert result.json()["code"] == "answer_stale"
    elif case == "good":
        assert service.accept_reviewed(OWNER, mid, **body)["accepted_count"] == 2
    else:
        with pytest.raises(ConflictError, match="Nothing changed"):
            service.accept_reviewed(OWNER, mid, **body)
    rows = hub.db.proposals.list_proposals(meeting_id=mid)
    assert all(p.state == ("confirmed" if case == "good" else "proposed") for p in rows)
    with hub.db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM decision_records").fetchone()[0] == (2 if case == "good" else 0)


def test_record_bulk_answer(hub):
    mid, service, shown, bindings = bulk(hub)
    gets = {path: hub.ok("GET", path) for path in (f"/api/meetings/{mid}", f"/api/meetings/{mid}?include_parked=true", f"/api/meetings/{mid}/outcome-review")}
    service.edit_proposal(OWNER, shown["proposals"][-1]["id"], text="A changed plan")
    path = f"/api/meetings/{mid}/proposals/accept-reviewed"
    response = hub.client.post(path, json={"bindings": bindings})
    assert response.status_code == 409
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        Path("web/src/desk/__tests__/fixtures/meetings-hub/review11a.json").write_text(json.dumps({"recordedBy": "tests/integration/test_review11a_bindings.py::test_record_bulk_answer", "meeting_id": mid, "gets": gets, "path": path, "bindings": bindings, "refusal": response.json()}, indent=2) + "\n")


def test_bulk_rolls_back_an_earlier_confirm_when_a_later_row_is_stale(hub, monkeypatch):
    mid, service, _, bindings = bulk(hub)
    confirm = service.confirm_proposal
    calls = 0
    def interleave(principal, ident, **kw):
        nonlocal calls
        calls += 1
        if calls == 2:
            kw["_conn"].execute("UPDATE follow_through_proposals SET owner_supplied='Priya' WHERE id=?", (ident,))
        return confirm(principal, ident, **kw)
    monkeypatch.setattr(service, "confirm_proposal", interleave)
    with pytest.raises(ConflictError, match="Nothing changed"):
        service.accept_reviewed(OWNER, mid, bindings=bindings)
    assert all(p.state == "proposed" for p in hub.db.proposals.list_proposals(meeting_id=mid))
    with hub.db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM decision_records").fetchone()[0] == 0


@pytest.mark.parametrize("transport", ("service", "http"))
@pytest.mark.parametrize("drop", (False, True))
def test_completion_uses_the_committed_producer_snapshot(hub, monkeypatch, transport, drop):
    from holdspeak import intel_queue
    from holdspeak.kernel.runtime import _configure
    from tests.unit.test_meeting_deferred_admission import FakeIntel, FakeHost, _Route, _assign_deferred_queue_routes
    from tests.unit.test_hs172_loop_wire import _seed_action_artifact
    mid = "arrival-snapshot"
    hub.db.meetings.save_meeting(MeetingState(id=mid, title="Snapshot", started_at=utc_now(),
        segments=[TranscriptSegment(text="Send the deck", speaker="Me", start_time=0, end_time=10)]))
    if drop:
        old = hub.db.proposals.create_proposal(meeting_id=mid, project_id=None, kind="action", text="Send the deck", owner_hint="Me", source_plugin="old", support="supported")
        hub.db.proposals.dismiss_proposal(old.id)
    if transport == "service":
        _seed_action_artifact(hub.db, mid, [{"task": "Send the deck", "owner": "Me", "due": "Friday"}])
    else:
        _assign_deferred_queue_routes(hub.db)
        _configure(hub.db)
        engine = FakeIntel()
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        monkeypatch.setattr(intel_queue, "get_database", lambda: hub.db)
        monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(()))
        monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(()))
    original = ProposalBridgeService.bridge_meeting_artifacts
    changed = []
    def edit_after_commit(self, *args, **kw):
        created = original(self, *args, **kw)
        for p in created:
            if self.arrival_keeps(p):
                changed.append(p.id)
                self.edit_proposal(OWNER, p.id, owner="Priya")
        return created
    monkeypatch.setattr(ProposalBridgeService, "bridge_meeting_artifacts", edit_after_commit)
    if transport == "service":
        intel_queue._on_intel_complete(hub.db, mid)
    else:
        planned = hub.ok("GET", f"/api/meetings/{mid}")["planned_route"]
        response = hub.client.post(f"/api/meetings/{mid}/intelligence/run", json={"expected_selection_hash": planned["selection_hash"]})
        assert response.status_code == 200, response.text
        assert intel_queue.process_next_intel_job() is True
    assert changed, (hub.db.intel.get_latest_intel_job(mid), hub.db.proposals.list_proposals(meeting_id=mid))
    for ident in changed:
        saved = hub.db.proposals.get_proposal(ident)
        assert saved.state == "proposed"
        assert saved.owner == "Priya"


@pytest.mark.parametrize("transport", ("service", "http"))
def test_project_name_in_the_page_is_in_its_answer_binding(tmp_path, monkeypatch, transport):
    from tests.integration.test_desk_reach_digest import _rig, Clock, _project_proposal
    rig, _, client = _rig(tmp_path, monkeypatch, Clock())
    ref = _project_proposal(rig)
    token = client.post("/api/reach/packages", json={"refs": [ref]}).json()["token"]
    shown = client.get(f"/api/b/{token}").json()["items"][0]
    with rig.db._connection() as conn:
        conn.execute("UPDATE projects SET name='The new project' WHERE id='proj-rv'")
    if transport == "http":
        response = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "accept", "binding": shown["binding"]})
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "answer_stale"
    else:
        from holdspeak.services.project_delta_service import ProjectDeltaService
        with pytest.raises(ConflictError, match="Nothing changed"):
            ProjectDeltaService(rig.db, None).decide_proposal(OWNER, "proj-rv", ref.split(":", 1)[1], "accept", review_id="review-rv", binding=shown["binding"])
    assert rig.db.project_observations.get_proposal(ref.split(":", 1)[1])["lifecycle"] == "open"


@pytest.mark.parametrize("transport", ("service", "http"))
@pytest.mark.parametrize("change", ("snapshot", "reason", "connection_reason", "time_only"))
def test_retire_binds_what_the_source_last_said(hub, transport, change):
    pid = hub.ok("POST", "/api/projects", {"name": "Source snapshot"})["project"]["id"]
    watch = seed_watch(hub.db, watch_id="source-snapshot", connector_id="gh", query_kind="pull_requests", name="Source", query={"repository": "acme/app"})
    hub.db.automations.update_watch_spec(watch["id"], project_id=pid, state="active", schema_version="WatchSpec@1")
    service = WatchService(hub.db)
    shown = service.get_watch(OWNER, watch["id"])
    before = hub.ok("GET", f"/api/projects/{pid}/room")["sources"]["items"][0]
    assert before["watchBindings"][watch["id"]] == shown["binding"]
    if change == "snapshot":
        hub.db.automations.record_refresh(watch["id"], {"entities": [{"id": "pr-1", "state": "open"}]}, [])
    elif change == "reason":
        with hub.db._connection() as conn:
            conn.execute("UPDATE connector_watches SET last_error='Authentication failed' WHERE id=?", (watch["id"],))
    elif change == "connection_reason":
        hub.db.automations.create_provider_connection(connection_id="wpc_github", provider_id="github", state="owner_action_required")
    else:
        with hub.db._connection() as conn:
            conn.execute("UPDATE connector_watches SET last_success_at='2026-11-11T16:00:00+00:00' WHERE id=?", (watch["id"],))
    good = change == "time_only"
    after = hub.ok("GET", f"/api/projects/{pid}/room")["sources"]["items"][0]
    if change == "snapshot":
        assert after["tokens"] != before["tokens"]
    elif change in ("reason", "connection_reason"):
        assert after["plainReason"] != before["plainReason"]
    if transport == "http":
        result = hub.client.post(f"/api/watches/{watch['id']}/retire", json={"binding": shown["binding"]})
        assert result.status_code == (200 if good else 409), result.text
        if not good:
            assert result.json()["code"] == "answer_stale"
    elif good:
        service.retire_watch(OWNER, watch["id"], binding=shown["binding"])
    else:
        with pytest.raises(ConflictError, match="Nothing changed"):
            service.retire_watch(OWNER, watch["id"], binding=shown["binding"])
    assert hub.db.automations.get_watch(watch["id"])["state"] == ("retired" if good else "active")
