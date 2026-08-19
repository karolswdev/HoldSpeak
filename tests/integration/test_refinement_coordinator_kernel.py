from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from holdspeak.db import Database, reset_database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import AskService
from holdspeak.services.refinement_coordinator import RefinementCoordinator
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


OWNER = Principal(PrincipalKind.OWNER, "kernel-walk-owner")


class _ScriptedEngine:
    active_provider = "local"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        self.prompts.append(user_prompt)
        return '{"kind":"question","question":"Who must act first?","reason":"It fixes the next owner."}'


@pytest.mark.asyncio
async def test_real_kernel_turn_reaches_review_then_answer_does_not_auto_chain(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "kernel-refinement.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    model = tmp_path / "Scripted.gguf"
    model.touch()
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path", lambda: str(model)
    )
    engine = _ScriptedEngine()
    broker = _configure(db)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
    coordinator = RefinementCoordinator(
        db, ask_factory=lambda: AskService(db, broker=broker)
    )
    await coordinator.start()
    service = RefinementThoughtService(db)
    thought = service.create(
        OWNER, request_id="kernel-capture", raw_text="Launch this, but ownership is unclear.",
        source={"kind": "typed"},
    )
    _, invocation = await coordinator.begin(
        OWNER, thought_id=thought["id"], request_id="kernel-refine",
        expected_aggregate_revision=1, expected_working_revision=1,
        expected_attachment_revision=0,
    )
    for _ in range(100):
        current = service.get(OWNER, thought["id"])
        if current["continuity"]["state"] == "review_ready":
            break
        await asyncio.sleep(0.01)
    else:
        pytest.fail("scripted kernel result never became review-ready")

    review_id = current["continuity"]["review_result_id"]
    review = service.review(OWNER, thought["id"], review_id)["review"]
    assert review["question"] == "Who must act first?"
    answered, receipt = service.review_action(
        OWNER, thought["id"], review_id, request_id="kernel-answer", action="answer",
        expected_aggregate_revision=1, expected_working_revision=1,
        expected_attachment_revision=0, answer="Mina owns the first customer call.",
    )
    assert "Question: Who must act first?" in answered["working_note"]["body_markdown"]
    assert "Answer: Mina owns the first customer call." in answered["working_note"]["body_markdown"]
    assert receipt["kind"] == "answer"
    await asyncio.sleep(0.03)
    assert len(engine.prompts) == 1
    assert answered["continuity"]["state"] == "named_failure"
    await coordinator.shutdown()
    reset_database()


def test_meeting_web_server_owns_one_coordinator_for_its_exact_lifespan(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "server-lifecycle.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *args, **kwargs: db)
    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda _label: None,
        on_stop=lambda: None,
        get_state=lambda: {},
    ))
    coordinator = server.refinement_coordinator
    assert coordinator.active_ids == ()
    assert coordinator._accepting is False
    with TestClient(server.app):
        assert server.refinement_coordinator is coordinator
        assert coordinator._accepting is True
        assert coordinator._loop is not None
    assert coordinator._accepting is False
    assert coordinator._loop is None
    assert coordinator.active_ids == ()
    reset_database()
