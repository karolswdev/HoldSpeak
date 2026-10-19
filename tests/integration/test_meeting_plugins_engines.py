"""Capture C4: the meeting's model plugins run on the engine set in Engines.

The architecture review is imported with ONE engine set in Engines (the
Default engine, as the capture walk set it). The summary job carries its
disclosed route (HS-201); its routed plugins must run on that same route and
store their runs and artifacts. Before C4 a planned route emptied the plugin
chain (``db/intel.py``), so ``plugin-runs`` stayed empty.

The production import, backlog, queue binder, route controller, kernel and
drainer run over SQLite. The one seam is the engine the admitted deployment
builds (``holdspeak.intel.engine.MeetingIntel``): it replays the replies the
real LAN engine gave (``qwen3.8-27b`` at 192.168.1.43:8080), recorded in
``tests/fixtures/capture_plugins_engine_replies.json``.
``HOLDSPEAK_WIRE_WRITE=1`` records them again from the real engine.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.config import Config
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_import import import_transcript
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meeting_route_projection import project_route
from tests.unit.test_hs201_route_contract import OWNER
from tests.unit.test_model_library_providers import _draft, _library

pytestmark = pytest.mark.timeout(240, method="signal")

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
TRANSCRIPT = FIXTURES / "capture_architecture_review.txt"
REPLIES = FIXTURES / "capture_plugins_engine_replies.json"
LAN_ENDPOINT = "http://192.168.1.43:8080/v1"
LAN_MODEL = "qwen3.8-27b"
RECORD = os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1"


def _key(messages: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(messages, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _plugin_of(messages: Any) -> str:
    system = str((messages or [{}])[0].get("content") or "")
    return system.split("\n", 1)[0][:80]


class _Replies:
    """The recorded engine replies: one summary, one reply per plugin prompt."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = (
            {"summary": None, "completions": {}}
            if RECORD
            else json.loads(REPLIES.read_text(encoding="utf-8"))
        )
        self.calls: list[str] = []

    def write(self) -> None:
        self.data.update(
            about=(
                "Capture C4: the real LAN engine's replies for the architecture "
                "review import (tests/integration/test_meeting_plugins_engines.py). "
                "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it."
            ),
            endpoint=LAN_ENDPOINT,
            model=LAN_MODEL,
            recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        REPLIES.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _engine_seam(monkeypatch: pytest.MonkeyPatch, replies: _Replies) -> None:
    from holdspeak.intel import engine as engine_module

    real_class = engine_module.MeetingIntel

    class _Engine:
        """The engine the admitted deployment builds: replay, or record live."""

        active_provider = "cloud"

        def __init__(self, **kwargs: Any) -> None:
            self.active_model = str(kwargs.get("cloud_model") or "")
            self.base_url = str(kwargs.get("cloud_base_url") or "")
            self._real = real_class(**kwargs) if RECORD else None

        def analyze(self, transcript: str, *, stream: bool = False, **kwargs: Any) -> IntelResult:
            assert stream is False
            replies.calls.append("summary")
            if self._real is not None:
                result = self._real.analyze(transcript, stream=False, **kwargs)
                replies.data["summary"] = {
                    "topics": list(result.topics),
                    "action_items": [
                        {"task": a.task, "owner": a.owner, "due": a.due} for a in result.action_items
                    ],
                    "summary": result.summary,
                    "decisions": result.decisions,
                    "raw_response": result.raw_response,
                    "error": result.error,
                }
                return result
            stored = replies.data["summary"]
            return IntelResult(
                topics=list(stored["topics"]),
                action_items=[ActionItem(**item) for item in stored["action_items"]],
                summary=stored["summary"],
                raw_response=stored["raw_response"],
                error=stored["error"],
                decisions=stored["decisions"],
            )

        def _chat_completion_text(self, messages: Any, **kwargs: Any) -> str:
            key = _key(messages)
            replies.calls.append(_plugin_of(messages))
            if self._real is not None:
                text = self._real._chat_completion_text(messages, **kwargs)
                replies.data["completions"][key] = {"prompt": _plugin_of(messages), "reply": text}
                return text
            stored = replies.data["completions"].get(key)
            assert stored is not None, f"no recorded reply for {_plugin_of(messages)!r}; record with HOLDSPEAK_WIRE_WRITE=1"
            return str(stored["reply"])

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", _Engine)


def _rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    import holdspeak.db as hsdb

    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": [LAN_MODEL]},
    )
    # The hub's own drainer is not part of this rig: the test drains once.
    monkeypatch.setattr("holdspeak.intel_queue_conductor.wake_intel_queue_conductor", lambda: None)
    library = _library(tmp_path, store_path=tmp_path / "keys.json")
    db = library._db
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *args, **kwargs: db)
    _configure(db)
    return db, library


def _add_engine(library: Any, profile_id: str, endpoint: str) -> int:
    """Add one engine the way Engines does (Model Library ▸ define endpoint)."""
    library.define_endpoint(
        OWNER,
        _draft(
            request_id=f"c4-{profile_id}",
            profile_id=profile_id,
            provider_family="openai_compatible",
            endpoint=endpoint,
            model=LAN_MODEL,
            requires_key=False,
        ),
        None,
    )
    with library._db._connection() as conn:
        return int(
            conn.execute(
                "SELECT MAX(revision) FROM model_profile_revisions WHERE profile_id=?",
                (profile_id,),
            ).fetchone()[0]
        )


def _assign(db: Any, scope: dict[str, str], profile_id: str, revision: int, command: str) -> None:
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": command,
            "expected_revision": 0,
            "scope": scope,
            "entries": [{"profile_id": profile_id, "profile_revision": revision}],
        },
    )


def _import(db: Any) -> str:
    result = import_transcript(
        TRANSCRIPT,
        db=db,
        config=Config(),
        title="Architecture review: idempotent retries",
        started_at=datetime(2026, 10, 16, 11, 0, 0),
    )
    assert result.intel_job_enqueued is True, "the import did not queue its summary"
    return str(result.state.id)


def _drain(db: Any, meeting_id: str) -> None:
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    job = db.intel.get_latest_intel_job(meeting_id)
    assert job is not None and job.status == "succeeded", (job.status, job.last_error)


def _drain_drafts(db: Any, meeting_id: str) -> Any:
    """Capture C5c: run the drafts-only job queued when the summary published."""
    from holdspeak.intel_queue import process_next_intel_job

    jobs = db.intel.list_prepare_jobs(meeting_id)
    assert jobs and jobs[0].status == "queued", [(j.status, j.last_error) for j in jobs]
    assert process_next_intel_job() is True
    job = db.intel.list_prepare_jobs(meeting_id)[0]
    assert job.status == "succeeded", (job.status, job.last_error)
    return job


def test_the_architecture_review_import_runs_its_plugins_on_the_engines_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db, library = _rig(tmp_path, monkeypatch)
    revision = _add_engine(library, "lan-qwen", LAN_ENDPOINT)
    _assign(db, {"kind": "global"}, "lan-qwen", revision, "c4-default-engine")
    route = project_route(db, invocation_id="meeting:c4")
    assert route["status"] == "ready"
    assert [leg["host"] for leg in route["legs"]] == ["192.168.1.43"]

    replies = _Replies()
    _engine_seam(monkeypatch, replies)
    meeting_id = _import(db)
    job = db.intel.get_latest_intel_job(meeting_id)
    assert job is not None and job.planned_route["selection_hash"] == route["selection_hash"]

    _drain(db, meeting_id)
    if RECORD:
        replies.write()

    runs = {run.plugin_id: run for run in db.plugins.list_plugin_runs(meeting_id, limit=100)}
    statuses = {plugin_id: run.status for plugin_id, run in runs.items()}
    assert statuses.get("requirements_extractor") == "success", statuses
    assert statuses.get("decision_capture") == "success", statuses
    assert not [
        run for run in runs.values() if "Missing capabilities" in str(run.error or "")
    ], {plugin_id: run.error for plugin_id, run in runs.items()}
    # The plugins asked the engine (recorded replies), not a stand-in.
    assert "summary" in replies.calls
    assert len([call for call in replies.calls if call != "summary"]) >= 2

    # Their outputs are stored for the meeting, parsed from the engine's reply
    # (a reply cut at the token budget stores a "did not contain" failure).
    requirements = runs["requirements_extractor"].output or {}
    assert requirements.get("requirements"), requirements
    decisions = runs["decision_capture"].output or {}
    assert decisions.get("decisions"), decisions
    assert any("option a" in json.dumps(item).lower() or "dedupe key" in json.dumps(item).lower()
               for item in decisions["decisions"]), decisions["decisions"]
    artifacts = db.plugins.list_artifacts(meeting_id)
    assert {"requirements_extractor", "decision_capture"} <= {
        str(artifact.plugin_id) for artifact in artifacts
    }, [(artifact.plugin_id, artifact.artifact_type) for artifact in artifacts]


def test_a_plugin_whose_route_was_not_shown_is_skipped_with_a_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HS-201 stands: the disclosed route is the plugins' only destination."""
    db, library = _rig(tmp_path, monkeypatch)
    summary_rev = _add_engine(library, "lan-qwen", LAN_ENDPOINT)
    other_rev = _add_engine(library, "other-lan", "http://192.168.1.77:8080/v1")
    # The summary runs on the LAN engine; every other job (the plugins too)
    # falls to a Default engine on another host the summary route never names.
    _assign(
        db, {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
        "lan-qwen", summary_rev, "c4-summary",
    )
    _assign(db, {"kind": "global"}, "other-lan", other_rev, "c4-other-default")

    replies = _Replies()
    _engine_seam(monkeypatch, replies)
    meeting_id = _import(db)
    _drain(db, meeting_id)

    job = db.intel.get_latest_intel_job(meeting_id)
    assert tuple(job.frozen_plugin_members or ()) == ()
    skipped = dict(job.frozen_plugin_route or {}).get("plugin_chain_skipped") or []
    assert skipped and {item["reason"] for item in skipped} == {"route_not_shown"}
    assert db.plugins.list_plugin_runs(meeting_id, limit=100) == []
    assert replies.calls == ["summary"]


# ── Capture C5: the meeting prepares its Results ─────────────────────────────

PREPARED_FIXTURE = (
    Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures"
    / "meetings-hub" / "prepared.json"
)


def _lan_rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _Replies]:
    db, library = _rig(tmp_path, monkeypatch)
    revision = _add_engine(library, "lan-qwen", LAN_ENDPOINT)
    _assign(db, {"kind": "global"}, "lan-qwen", revision, "c5-default-engine")
    replies = _Replies()
    _engine_seam(monkeypatch, replies)
    return db, replies


def test_the_architecture_review_prepares_the_adr_and_the_stakeholder_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The review says "write the ADR" and "the stakeholder update": the
    summary publishes first, then a drafts-only job writes both drafters on
    the disclosed route (capture C5c), the LAN engine writes them, and the meeting's Prepared read lists
    the follow-up, the ADR draft and the update, ready, each tied to the
    action it serves."""
    from holdspeak.meeting_plugins import prepared_results

    db, replies = _lan_rig(tmp_path, monkeypatch)
    # While the summary is being written (the job claimed, its plan frozen),
    # the Prepared read says each draft is being written.
    from holdspeak.intel import engine as engine_module

    seen: dict[str, Any] = {}
    replaying = engine_module.MeetingIntel

    class _Watching(replaying):  # type: ignore[misc,valid-type]
        def analyze(self, transcript: str, **kwargs: Any) -> Any:
            seen.setdefault("writing", prepared_results(db, meeting_ids[0]))
            return super().analyze(transcript, **kwargs)

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", _Watching)
    meeting_ids: list[str] = []
    meeting_ids.append(_import(db))
    meeting_id = meeting_ids[0]
    _drain(db, meeting_id)
    during = seen["writing"]
    assert [(row["kind"], row["state"]) for row in during["results"] if row["kind"] != "followup"] == [
        ("adr", "writing"), ("stakeholder_update", "writing")], during

    # Capture C5c: the summary is published FIRST. The summary job planned no
    # draft; the drafts wait in their own job, and the meeting is ready.
    job = db.intel.get_latest_intel_job(meeting_id)
    route = dict(job.frozen_plugin_route or {})
    assert not route.get("prepared"), route
    assert not {"adr_drafter", "stakeholder_update_drafter"} & set(route.get("plugin_chain") or []), route
    published = db.meetings.get_meeting(meeting_id)
    assert published.intel_status == "ready" and published.intel.summary, published.intel_status
    assert not [r for r in db.plugins.list_plugin_runs(meeting_id, limit=100)
                if r.plugin_id in {"adr_drafter", "stakeholder_update_drafter"}]
    writing = prepared_results(db, meeting_id)
    assert [(row["kind"], row["state"]) for row in writing["results"] if row["kind"] != "followup"] == [
        ("adr", "writing"), ("stakeholder_update", "writing")], writing
    drafts = _drain_drafts(db, meeting_id)
    assert dict(drafts.frozen_plugin_route or {}).get("prepared") == ["adr_drafter", "stakeholder_update_drafter"]
    if RECORD:
        replies.write()
    statuses = {run.plugin_id: run.status for run in db.plugins.list_plugin_runs(meeting_id, limit=100)}
    assert statuses.get("adr_drafter") == "success", statuses
    assert statuses.get("stakeholder_update_drafter") == "success", statuses

    body = prepared_results(db, meeting_id)
    rows = {row["kind"]: row for row in body["results"]}
    assert [row["kind"] for row in body["results"]] == ["followup", "adr", "stakeholder_update"], body
    assert all(row["state"] == "ready" for row in body["results"]), body
    assert rows["followup"]["document_ref"] == f"meeting_followup:{meeting_id}"
    assert "idempot" in rows["adr"]["body_markdown"].lower(), rows["adr"]
    assert rows["adr"]["artifact_id"] and rows["stakeholder_update"]["artifact_id"]
    tasks = {str(item.id): item.task for item in db.meetings.list_action_items(
        include_completed=True, meeting_id=meeting_id)}
    assert any("ADR" in tasks[item_id] for item_id in rows["adr"]["serves"]), (rows["adr"]["serves"], tasks)
    assert rows["stakeholder_update"]["serves"], tasks
    _recorded_prepared(db, meeting_id, writing=writing)


def test_a_failed_draft_never_holds_the_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ADR drafter fails (the hub's declared plugin fault point). The
    summary still publishes; the Prepared row says it failed, in words."""
    from holdspeak.meeting_plugins import prepared_results

    monkeypatch.setenv("HOLDSPEAK_FAULT", "intel.plugin:adr_drafter")
    db, _replies = _lan_rig(tmp_path, monkeypatch)
    meeting_id = _import(db)
    _drain(db, meeting_id)  # asserts the job SUCCEEDED
    _drain_drafts(db, meeting_id)  # a failed draft still ends its job

    meeting = db.meetings.get_meeting(meeting_id)
    assert meeting.intel is not None and meeting.intel.summary, "the summary did not publish"
    rows = {row["kind"]: row for row in prepared_results(db, meeting_id)["results"]}
    assert rows["adr"]["state"] == "failed", rows["adr"]
    assert rows["adr"]["reason"] == "The engine did not finish this draft."
    assert rows["stakeholder_update"]["state"] == "ready", rows["stakeholder_update"]
    _recorded_failed(prepared_results(db, meeting_id), meeting_id)


def _recorded_failed(body: dict[str, Any], meeting_id: str) -> None:
    """The face test's recorded failed draft (prepared-failed.json)."""
    path = PREPARED_FIXTURE.with_name("prepared-failed.json")
    live = json.loads(json.dumps(body).replace(meeting_id, "c5-review"))
    if RECORD:
        path.write_text(json.dumps({
            "_source": "Recorded from the hub's Prepared read by tests/integration/"
                       "test_meeting_plugins_engines.py::test_a_failed_draft_never_holds_the_summary "
                       "(the ADR drafter failed at the hub's declared plugin fault point). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit a field a test reads.",
            "prepared": live,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stored = json.loads(path.read_text(encoding="utf-8"))["prepared"]
    shape = lambda b: [(r["kind"], r["state"], r.get("reason")) for r in b["results"]]  # noqa: E731
    assert shape(stored) == shape(live), "re-record with HOLDSPEAK_WIRE_WRITE=1"


def _recorded_prepared(db: Any, meeting_id: str, *, writing: dict[str, Any]) -> None:
    """The face test's recorded hub (meetings.app.test.tsx): every GET the
    meeting window makes for this meeting, served by a real MeetingWebServer
    over this database. HOLDSPEAK_WIRE_WRITE=1 rewrites the file; otherwise
    the stored Prepared read must have the same shape as the live one."""
    from fastapi.testclient import TestClient

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_a, **_k: None, on_stop=lambda *_a, **_k: None,
                            get_state=lambda: None),
        host="127.0.0.1",
    )
    client = TestClient(server.app)
    base = f"/api/meetings/{meeting_id}"
    paths = [
        f"{base}?include_parked=true", f"{base}/artifacts", f"{base}/aftercare",
        f"{base}/intent-timeline", f"{base}/proposals", f"{base}/follow-through-proposals",
        f"/api/decisions?scope=all&limit=500&meeting_id={meeting_id}", f"{base}/intel-recovery",
        f"{base}/prepared",
    ]
    bodies = {}
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code, response.text[:200])
        bodies[path.replace(meeting_id, "c5-review")] = json.loads(
            json.dumps(response.json()).replace(meeting_id, "c5-review"))

    def shape(body: dict[str, Any]) -> Any:
        return [(row["kind"], row["state"], len(row.get("serves") or [])) for row in body["results"]]

    bodies["/api/meetings/c5-review/prepared#writing"] = json.loads(
        json.dumps(writing).replace(meeting_id, "c5-review"))
    live = bodies["/api/meetings/c5-review/prepared"]
    if RECORD:
        PREPARED_FIXTURE.write_text(json.dumps({
            "_source": "Recorded from a real MeetingWebServer by tests/integration/"
                       "test_meeting_plugins_engines.py::test_the_architecture_review_prepares_the_adr_"
                       "and_the_stakeholder_update (the LAN engine's recorded replies; the meeting id is "
                       "c5-review). HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit a field "
                       "a test reads.",
            "_now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **bodies,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stored = json.loads(PREPARED_FIXTURE.read_text(encoding="utf-8"))["/api/meetings/c5-review/prepared"]
    assert shape(stored) == shape(live), "re-record with HOLDSPEAK_WIRE_WRITE=1"


# ── Capture C5b: Write again and Prepare… are drafts-only jobs ───────────────


def test_write_again_runs_only_the_draft_and_never_the_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ADR drafter failed on the summary run. Write again queues a
    drafts-only job on the route he was shown: the ADR is written, the summary,
    its run receipt and the meeting's summary state stay exactly as they were,
    and the engine is asked for no second summary."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.meeting_plugins import prepared_results
    from holdspeak.services.errors import ConflictError, ValidationError
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    monkeypatch.setenv("HOLDSPEAK_FAULT", "intel.plugin:adr_drafter")
    db, replies = _lan_rig(tmp_path, monkeypatch)
    meeting_id = _import(db)
    _drain(db, meeting_id)
    _drain_drafts(db, meeting_id)
    monkeypatch.delenv("HOLDSPEAK_FAULT")
    before = db.meetings.get_meeting(meeting_id)
    receipt_before = db.intel.get_run_receipt(meeting_id)
    summary_job = db.intel.get_latest_intel_job(meeting_id)
    rows = {row["kind"]: row for row in prepared_results(db, meeting_id)["results"]}
    assert rows["adr"]["state"] == "failed" and rows["adr"]["retry"] is True, rows["adr"]
    summaries = replies.calls.count("summary")

    service = MeetingIntelService(db)
    route = project_route(db, invocation_id=f"meeting:{meeting_id}")
    with pytest.raises(ValidationError):
        service.prepare_result(OWNER, meeting_id, plugin_id="decision_capture",
                               expected_selection_hash=route["selection_hash"])
    queued = service.prepare_result(OWNER, meeting_id, plugin_id="adr_drafter",
                                    expected_selection_hash=route["selection_hash"])
    assert queued["state"] == "queued", queued
    with pytest.raises(ConflictError):  # one live job per meeting
        service.prepare_result(OWNER, meeting_id, plugin_id="risk_heatmap",
                               expected_selection_hash=route["selection_hash"])
    writing = {row["kind"]: row for row in prepared_results(db, meeting_id)["results"]}
    assert writing["adr"]["state"] == "writing", writing["adr"]
    # The meeting's summary state is not the drafts job's.
    assert db.meetings.get_meeting(meeting_id).intel_status == before.intel_status == "ready"
    assert db.intel.get_latest_intel_job(meeting_id).job_id == summary_job.job_id

    assert process_next_intel_job() is True
    after = db.meetings.get_meeting(meeting_id)
    rows = {row["kind"]: row for row in prepared_results(db, meeting_id)["results"]}
    assert rows["adr"]["state"] == "ready", rows["adr"]
    assert "idempot" in rows["adr"]["body_markdown"].lower()
    assert after.intel_status == "ready"
    assert after.intel.summary == before.intel.summary
    assert db.intel.get_run_receipt(meeting_id) == receipt_before
    assert db.intel.get_latest_intel_job(meeting_id).job_id == summary_job.job_id
    assert replies.calls.count("summary") == summaries, "the summary was written again"
    jobs = db.intel.list_prepare_jobs(meeting_id)
    assert jobs and jobs[0].status == "succeeded", [(j.job_id, j.status, j.last_error) for j in jobs]

    # The Send document is the clean draft (no synthesis frame).
    from holdspeak.services.document_sources import render_document

    doc = render_document(db, f"artifact:{rows['adr']['artifact_id']}")
    body = str(getattr(doc, "body_md", None) or getattr(doc, "markdown", None) or doc)
    assert "Adr Drafter" not in body and "Source windows" not in body and "ADR(s)" not in body, body[:300]
    assert body.startswith("# ADR: "), body[:120]
