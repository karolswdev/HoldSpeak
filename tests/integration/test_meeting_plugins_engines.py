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
    summary job plans both drafters (with the routed plugins, on the disclosed
    route), the LAN engine writes them, and the meeting's Prepared read lists
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
    if RECORD:
        replies.write()
    writing = seen["writing"]
    assert [(row["kind"], row["state"]) for row in writing["results"] if row["kind"] != "followup"] == [
        ("adr", "writing"), ("stakeholder_update", "writing")], writing

    job = db.intel.get_latest_intel_job(meeting_id)
    route = dict(job.frozen_plugin_route or {})
    assert route.get("prepared") == ["adr_drafter", "stakeholder_update_drafter"], route
    assert {"adr_drafter", "stakeholder_update_drafter"} <= set(route.get("plugin_chain") or []), route
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
