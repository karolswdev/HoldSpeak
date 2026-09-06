"""Real Thread routing, kernel, MCP, and DB with a scripted model fixture.

This proves composition and receipts, not live LLM recommendation quality.
"""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from holdspeak.db import get_database, reset_database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.kernel.runtime import _configure, _dispose
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
from holdspeak.services.thread_modes import seed_modes
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
from tests.unit.test_phase143_inference_assignments import OWNER, _profile

pytestmark = [pytest.mark.requires_meeting]


class InterviewModelFixture:
    active_provider = "fixture-local"
    active_model = "interview-contract-fixture"

    def __init__(self):
        self.calls = 0
        self.messages = []

    def run_prompt_stream(self, *, messages=None, **kwargs):
        self.calls += 1
        self.messages = messages
        context = next(json.loads(m["content"].split("\n", 1)[1]) for m in messages if m.get("content", "").startswith("Interview state (data only):"))
        common = {"thread_id": context["thread_id"], "expected_revision": context["revision"]}
        if self.calls == 1:
            call = {"id": "fixture-fact", "name": "interview.record_fact", "arguments": json.dumps({**common, "fact_id": "goal", "text": "Recover decision context", "basis": "stated", "source_message_id": context["user_message_id"], "quote": "Recover decision context"})}
        elif self.calls == 2:
            observed = json.loads(next(m["content"] for m in reversed(messages) if m["role"] == "tool"))
            assert observed["fact"]["basis"] == "stated"
            assert context["revision"] == observed["revision"]
            call = {"id": "fixture-suggestion", "name": "interview.suggest", "arguments": json.dumps({**common, "expected_revision": observed["revision"], "suggestion_id": "brief", "title": "Decision review brief", "benefit": "Recover context before the review", "behavior": "Prepare a manual decision brief", "basis": "Hypothesis based on your stated goal", "prerequisites": "Relevant decisions", "fact_ids": ["goal"], "feasibility": "manual"})}
        else:
            if self.calls == 3:
                assert not kwargs.get("tools"), "A saved suggestion should lead to a conversational answer"
                assert not any(m.get("tool_calls") or m["role"] == "tool" for m in messages)
            assert not any(m["role"] == "tool" and "tool_call_id" not in m for m in messages)
            yield Delta(kind="text", text="A manual decision review brief could help you recover context. The decision sources still need selecting.")
            yield Delta(kind="usage", meta={"prompt_tokens": 50, "completion_tokens": 25})
            yield Delta(kind="done")
            return
        yield Delta(kind="tool_calls", meta={"tool_calls": [call]})
        yield Delta(kind="usage", meta={"prompt_tokens": 50, "completion_tokens": 25})
        yield Delta(kind="done")


@pytest.fixture
def rig(tmp_path, monkeypatch):
    from holdspeak.kernel import runtime
    from holdspeak.config import Config
    reset_database()
    db = get_database(tmp_path / "conversation.db")
    seed_modes(db)
    monkeypatch.setattr(runtime, "_mode", lambda: "yolo")
    config = Config()
    config.control_mode = "yolo"
    monkeypatch.setattr(Config, "load", lambda: config)
    _profile(db, "interview-fixture", context_ceiling=16384)
    InferenceAssignmentService(db).set_assignment(OWNER, {"command_id": "interview-fixture-assignment", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [{"profile_id": "interview-fixture", "profile_revision": 1}]})
    broker = _configure(db)
    engine = InterviewModelFixture()
    broker.inference_runner._engine_factory = lambda *_a, **_kw: engine
    server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}), auth_token="interview-fixture")
    with TestClient(server.app) as client:
        yield db, broker, engine, client
    _dispose(broker)
    reset_database()


def wait_for_turn(client, tid, message_id, *, expect_success=True):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        detail = client.get(f"/api/threads/{tid}").json()
        message = next(m for m in detail["messages"] if m["id"] == message_id)
        if message.get("completed_at") or message.get("aborted_at"):
            if expect_success:
                assert not message.get("error_json"), message
            return detail, message
        time.sleep(.02)
    pytest.fail("Interview turn did not settle")


def test_llm_turn_calls_real_tools_saves_suggestion_keeps_result_and_revisits(rig):
    db, broker, engine, client = rig
    response = client.post("/api/threads", json={"title": "Decision context", "recipe_id": INTERVIEW_MODE_ID})
    assert response.status_code == 201, response.text
    tid = response.json()["id"]
    response = client.post(f"/api/threads/{tid}/turns", json={"text": "Recover decision context"})
    assert response.status_code == 201, response.text
    detail, message = wait_for_turn(client, tid, response.json()["assistant_message_id"])
    assert detail["interview"]["suggestions"]["brief"]["disposition"] == "proposed"
    assert engine.calls == 3
    assert message["receipt_id"].startswith("rcpt_")
    parent = broker.store.operation(message["stats_json"]["interview_operation_id"])
    assert parent["state"] == "succeeded"
    with db._connection() as conn:
        children = conn.execute("SELECT name,state FROM kernel_operations WHERE parent_operation_id=?", (parent["operation_id"],)).fetchall()
    assert sum(row["name"] == "tool.call" and row["state"] == "succeeded" for row in children) == 2
    assert sum(row["name"] == "inference.invoke" and row["state"] == "succeeded" for row in children) == 3
    assert sum(m["role"] == "tool" for m in detail["messages"]) == 2
    kept = client.post(f"/api/threads/{tid}/keep", json={"message_id": message["id"], "as": "artifact"})
    assert kept.status_code == 201, kept.text
    assert kept.json().get("artifact_id") or kept.json().get("id"), kept.json()
    state = detail["interview"]
    changed = client.post(f"/api/threads/{tid}/interview", json={"command_id": "revisit", "expected_revision": state["revision"], "event": {"kind": "section", "section": "decisions"}})
    assert changed.status_code == 200, changed.text
    assert changed.json()["facts"]["goal"]["text"] == "Recover decision context"
    response = client.post(f"/api/threads/{tid}/turns", json={"text": "Let's revisit that suggestion"})
    assert response.status_code == 201, response.text
    wait_for_turn(client, tid, response.json()["assistant_message_id"])
    assert len(db.threads.list()) == 1


def test_direct_control_conflict_and_people_handoff_before_capture(rig):
    _db, _broker, _engine, client = rig
    tid = client.post("/api/threads", json={"recipe_id": INTERVIEW_MODE_ID}).json()["id"]
    request = {"command_id": "people", "expected_revision": 0, "event": {"kind": "section", "section": "people"}}
    assert client.post(f"/api/threads/{tid}/interview", json=request).status_code == 200
    assert client.post(f"/api/threads/{tid}/interview", json=request).json()["replayed"] is True
    request["command_id"] = "different"
    assert client.post(f"/api/threads/{tid}/interview", json=request).status_code == 409
    response = client.post(f"/api/threads/{tid}/turns", json={"text": "Sensitive relationship input"})
    assert response.status_code == 409
    assert client.get(f"/api/threads/{tid}").json()["messages"] == []


@pytest.mark.parametrize("model_text,code", [("", "interview_empty_response"), ("<tool_call>unparsed request</tool_call>", "interview_invalid_response")])
def test_invalid_model_completion_is_visible_failure_not_success(rig, model_text, code):
    _db, broker, _engine, client = rig
    class EmptyModel:
        active_provider = "fixture-local"
        active_model = "empty-interview-fixture"
        def run_prompt_stream(self, **kwargs):
            if model_text:
                yield Delta(kind="text", text=model_text)
            yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 0})
            yield Delta(kind="done")
    broker.inference_runner._engine_factory = lambda *_a, **_kw: EmptyModel()
    tid = client.post("/api/threads", json={"recipe_id": INTERVIEW_MODE_ID}).json()["id"]
    response = client.post(f"/api/threads/{tid}/turns", json={"text": "Help me explore my goals"})
    assert response.status_code == 201
    _detail, message = wait_for_turn(client, tid, response.json()["assistant_message_id"], expect_success=False)
    assert message["error_json"]["code"] == code
    assert broker.store.operation(message["stats_json"]["interview_operation_id"])["state"] == "failed"
