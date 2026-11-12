"""Sibling services use public ports and retain the answers from their owners."""
from types import SimpleNamespace

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_service import ProjectService
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.thread_turns import _ToolExecutorAggregator


def test_retired_next_actions_have_no_new_store_or_writer(tmp_path):
    db = Database(tmp_path / "fresh.db")
    with db._connection() as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='cadence_next_actions'").fetchone() is None
    assert not hasattr(db.cadence, "add_next_action")
    db.close()


def test_room_people_sources_come_from_the_project_port(tmp_path):
    from holdspeak.services.room_people_service import room_people_preparation
    from holdspeak.services.errors import NotFound

    db = Database(tmp_path / "project.db")
    service = ProjectService(db)
    owner = Principal(PrincipalKind.OWNER, "project-port-test")
    project_id = service.create_project(owner, {"name": "Atlas"})["id"]
    sources = service.people_preparation_sources(project_id)
    assert sources == {"commitments": [], "watches": []}
    with pytest.raises(NotFound):
        service.people_preparation_sources("missing")

    class ProjectPort:
        def people_preparation_sources(self, requested):
            assert requested == project_id
            return sources

    assert room_people_preparation(ProjectPort(), None, project_id, owner) == room_people_preparation(service, None, project_id, owner)
    db.close()


def test_calls_answers_through_the_thread_port(monkeypatch):
    from holdspeak.calls.service import DeskTurns

    handle = SimpleNamespace(call_id="held", state="awaiting_decision")
    answers = []
    executor = SimpleNamespace(_handles={"held": handle}, decide=lambda h, d, answer=None: answers.append((h, d)))
    aggregator = _ToolExecutorAggregator()
    aggregator.register("turn", executor)
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    ThreadService.answer_tool_handle(handle, "deny")
    assert answers == [(handle, "deny")]
    with pytest.raises(ValueError, match="No active executor"):
        ThreadService.answer_tool_handle(SimpleNamespace(call_id="missing"), "deny")

    # The caller needs only the public lookup and answer, not the executor.
    monkeypatch.setattr(ThreadService, "tool_handle", lambda call_id: handle)
    monkeypatch.setattr(ThreadService, "answer_tool_handle", lambda h, d: answers.append((h, d)))
    monkeypatch.setattr(ThreadService, "_tool_executor", object())
    turns = DeskTurns(None, lambda **kw: None)
    assert turns.decide("held", "approve")
    assert answers[-1] == (handle, "approve")
    handle.state = "admitted"
    assert not turns.decide("held", "approve")


def test_ask_reads_only_held_calls_of_its_turn_through_the_thread_port(monkeypatch):
    from holdspeak.services.ask_desk import _holds, hold_words

    pending = SimpleNamespace(call_id="held", name="note.create", state="awaiting_decision")
    done = SimpleNamespace(call_id="done", state="admitted")
    aggregator = _ToolExecutorAggregator()
    aggregator.register("turn", SimpleNamespace(_handles={"held": pending, "done": done}))
    aggregator.register("other", SimpleNamespace(_handles={"elsewhere": pending}))
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    assert ThreadService.held_tool_calls("turn") == [pending]
    assert ThreadService.held_tool_calls("missing") == []
    monkeypatch.setattr(ThreadService, "held_tool_calls", lambda message_id: [pending] if message_id == "turn" else [])
    monkeypatch.setattr(ThreadService, "_tool_executor", object())
    assert _holds("turn") == [{"call_id": "held", "tool": "note.create", "words": hold_words("note.create")}]
    assert _holds("missing") == []
