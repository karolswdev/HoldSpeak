"""Owner-only calls do not publish their answers through pipeline.events."""
from __future__ import annotations

import asyncio
import json

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.delivery_service import DeliveryService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.setup_service import SetupService
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.services.observer import WITHHELD
from tests.unit.test_web_routes_missioncontrol import FEED_DOC, _make_map, _runner_for

OWNER = Principal(PrincipalKind.OWNER, "privacy-owner")
AGENT = Principal(PrincipalKind.AGENT, "event-reader")


def agent_events(db, monkeypatch, service, method):
    from holdspeak.mcp import tools
    monkeypatch.setattr(tools, "get_database", lambda: db)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    events = tools.dispatch("pipeline.events", {"service": service, "method": method}, AGENT)
    assert events
    for event in events:
        assert event["principal_kind"] == "owner"
        assert event["duration_ms"] >= 0
        assert json.loads(event["result_summary"]) == WITHHELD
    return events


@pytest.mark.parametrize("method", ["belt_state", "belt_journal"])
def test_agent_cannot_read_belt_results(tmp_path, monkeypatch, method):
    from holdspeak import rails_observer
    from copy import deepcopy

    db = Database(tmp_path / "hub.db")
    service = DeliveryService(db, observer=SQLiteObserver(db._connection))
    if method == "belt_state":
        feed = deepcopy(FEED_DOC)
        feed["projects"][0]["current_phase"]["title"] = "PRIVATE-FEED-CONTENT"
        service.configure(map_path=_make_map(tmp_path), runner=_runner_for({"state": feed}))
        answer = service.belt_state(OWNER)
        assert answer["repos"][0]["feed"] == feed
        secret = str(tmp_path / "rails-repo")
    else:
        batch = rails_observer.summarize_batch(
            [{"ts": "t1", "event": "story_status", "story": "HS-1", "repo": "code"}],
            summarize_fn=lambda *_: "PRIVATE-JOURNAL-CONTENT")
        rails_observer.record_journal_entry(db, batch, title="Private journal")
        answer = service.belt_journal(OWNER)
        secret = "PRIVATE-JOURNAL-CONTENT"
        assert secret in answer["entries"][0]["body_markdown"]
    events = agent_events(db, monkeypatch, "DeliveryService", method)
    assert secret not in json.dumps(events)
    assert "PRIVATE-FEED-CONTENT" not in json.dumps(events)


def test_agent_cannot_read_discovery_answers(tmp_path, monkeypatch):
    from holdspeak import setup_runtime
    db = Database(tmp_path / "hub.db")
    service = SetupService(db, observer=SQLiteObserver(db._connection))
    monkeypatch.setattr(setup_runtime, "_default_http_json", lambda *a, **k: (
        200, b'{"data":[{"id":"PRIVATE-MODEL-NAME"}]}'))
    status, answer = service.discover_models(OWNER, base_url="https://owner.example/v1")
    assert status == 200 and answer["models"] == ["PRIVATE-MODEL-NAME"]
    assert "PRIVATE-MODEL-NAME" not in json.dumps(agent_events(db, monkeypatch, "SetupService", "discover_models"))


def test_agent_cannot_read_saved_ask_resume_material(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    service = ProjectService(db, observer=SQLiteObserver(db._connection))
    project = service.create_project(OWNER, {"name": "Project"})
    task = service.save_ask(OWNER, project["id"], {"purpose": "PRIVATE-ASK-MATERIAL"})["task"]
    answer = asyncio.run(service.resume_ask(OWNER, task["id"]))
    assert answer["task"]["purpose"] == "PRIVATE-ASK-MATERIAL"
    assert "PRIVATE-ASK-MATERIAL" not in json.dumps(agent_events(db, monkeypatch, "ProjectService", "resume_ask"))


def test_agent_cannot_read_pr_draft_result_even_for_a_named_refusal(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    service = DeliveryService(db, observer=SQLiteObserver(db._connection))
    # A real empty PR cache refuses before engine work; the observer must
    # withhold the complete result on this branch as on a successful draft.
    service.configure(registry_path=tmp_path / "absent.json")
    status, answer = service.draft_review(OWNER, "missing-source", 1)
    assert status == 404 and answer["error"] == "unknown_pr"
    agent_events(db, monkeypatch, "DeliveryService", "draft_review")


def test_agent_cannot_read_owner_decision_form_answer_or_body(tmp_path, monkeypatch):
    from holdspeak import operations
    from holdspeak.services.decision_record_service import DecisionRecordService
    from holdspeak.services.primitive_service import PrimitiveService

    db = Database(tmp_path / "hub.db")
    service = DecisionRecordService(db, observer=SQLiteObserver(db._connection))
    primitive = PrimitiveService(db)
    registry = operations.bind_available({"primitive_service": primitive, "decision_record_service": service})
    status, answer = service.create_desk_command(OWNER, body={"title": "PRIVATE-DECISION-FORM"},
                                               registry_factory=lambda: registry)
    assert status == 201 and answer["record"]["decision_text"] == "PRIVATE-DECISION-FORM"
    events = agent_events(db, monkeypatch, "DecisionRecordService", "create_desk_command")
    assert "PRIVATE-DECISION-FORM" not in json.dumps(events)
