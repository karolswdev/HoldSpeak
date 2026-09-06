"""Repeatable interviews: real persistence, provenance, replay, and scope."""
from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID, SECTION_BY_ID
from holdspeak.services.interview_service import InterviewService
from holdspeak.services.thread_modes import palette_for, seed_modes
from holdspeak.services.thread_service import ThreadService

OWNER = Principal(PrincipalKind.OWNER, "interview-owner")


@pytest.fixture
def rig(tmp_path):
    db = Database(tmp_path / "interview.db")
    seed_modes(db)
    thread = ThreadService(db, broadcast=lambda *_: None).create(recipe_id=INTERVIEW_MODE_ID)
    yield db, thread["id"], InterviewService(db)
    db.close()


def command(rig, event, **kwargs):
    _db, tid, svc = rig
    return svc.command(OWNER, tid, command_id=kwargs.pop("command_id", uuid.uuid4().hex), expected_revision=kwargs.pop("expected_revision", svc.get(tid)["revision"]), event=event, **kwargs)


def fact(rig, text="Stop losing decision context", fact_id="goal", basis="stated"):
    db, tid, _svc = rig
    message = db.threads.append_message(tid, role="user")
    db.threads.append_part(message.id, kind="text", text=text)
    return command(rig, {"kind": "fact", "fact_id": fact_id, "text": text, "basis": basis, "source_message_id": message.id, "quote": text})


def suggestion(rig, suggestion_id="brief", title="Decision brief", feasibility="manual"):
    return command(rig, {"kind": "suggestion", "suggestion_id": suggestion_id, "title": title, "benefit": "Recover rationale before a review", "behavior": "Prepare a scoped manual decision brief", "basis": "Hypothesis based on the stated context-recovery goal", "prerequisites": "Relevant decision evidence and a compatible model", "fact_ids": ["goal"], "feasibility": feasibility})


@pytest.mark.parametrize("section", list(SECTION_BY_ID))
def test_sections_resume_independently_without_new_threads(rig, section):
    fact(rig)
    state = command(rig, {"kind": "section", "section": section})
    db, tid, svc = rig
    assert state["section"] == section
    reopened = Database(db.db_path)
    try:
        assert InterviewService(reopened).get(tid)["facts"] == state["facts"]
        assert len(reopened.threads.list()) == 1
    finally:
        reopened.close()
    assert ThreadService(db, broadcast=lambda *_: None).get(tid)["interview"]["revision"] == svc.get(tid)["revision"]


def test_command_replay_and_conflict_are_atomic(rig):
    event = {"kind": "section", "section": "projects"}
    original = command(rig, event, command_id="once", expected_revision=0)
    replay = command(rig, event, command_id="once", expected_revision=0)
    assert replay["revision"] == original["revision"] == 1
    assert replay["replayed"] is True
    with pytest.raises(ServiceError, match="different change"):
        command(rig, {"kind": "section", "section": "decisions"}, command_id="once")
    with pytest.raises(ServiceError, match="reload"):
        command(rig, {"kind": "section", "section": "decisions"}, expected_revision=0)
    assert rig[2].get(rig[1])["section"] == "projects"


def test_goal_correction_invalidates_suggestions_and_removal_drops_derived_context(rig):
    fact(rig)
    suggestion(rig)
    state = fact(rig, "Reduce unnecessary notifications")
    assert state["suggestions"]["brief"]["disposition"] == "stale"
    with pytest.raises(ServiceError):
        command(rig, {"kind": "disposition", "suggestion_id": "brief", "disposition": "try"})
    state = command(rig, {"kind": "remove_fact", "fact_id": "goal"})
    assert state["facts"] == state["suggestions"] == {}


@pytest.mark.parametrize("choice", ["dismissed", "deferred", "kept"])
def test_repeated_suggestion_cannot_erase_owner_choice(rig, choice):
    fact(rig)
    suggestion(rig)
    command(rig, {"kind": "disposition", "suggestion_id": "brief", "disposition": choice})
    state = suggestion(rig, suggestion_id="new-model-id")
    assert list(state["suggestions"]) == ["brief"]
    assert state["suggestions"]["brief"]["disposition"] == choice


def test_manual_trial_removes_setup_effects_from_palette(rig):
    fact(rig)
    command(rig, {"kind": "section", "section": "projects"})
    suggestion(rig)
    assert "project.setup.finalize" in palette_for(rig[0], rig[1])
    command(rig, {"kind": "disposition", "suggestion_id": "brief", "disposition": "try"})
    palette = palette_for(rig[0], rig[1])
    assert "project.get_room" in palette
    assert "project.setup.finalize" not in palette
    assert "interview.change_section" not in palette
    assert "interview.record_fact" not in palette


def test_unsupported_idea_cannot_be_started(rig):
    fact(rig)
    suggestion(rig, feasibility="unsupported_idea")
    with pytest.raises(ServiceError):
        command(rig, {"kind": "disposition", "suggestion_id": "brief", "disposition": "try"})


@pytest.mark.parametrize("source", ["assistant", "other-thread", "invented-quote", "sensitive"])
def test_fact_requires_actual_permitted_user_provenance(rig, source):
    db, tid, _svc = rig
    other = db.threads.create_thread() if source == "other-thread" else None
    message = db.threads.append_message(other.id if other else tid, role="assistant" if source == "assistant" else "user")
    db.threads.append_part(message.id, kind="text", text="Actual input", sensitive=source == "sensitive")
    with pytest.raises(ServiceError):
        command(rig, {"kind": "fact", "fact_id": "goal", "text": "A goal", "basis": "stated", "source_message_id": message.id, "quote": "Invented" if source == "invented-quote" else "Actual input"})
    assert rig[2].get(tid)["revision"] == 0


def test_people_handoff_refuses_before_input_persistence(rig):
    command(rig, {"kind": "section", "section": "people"})
    db, tid, _svc = rig
    with pytest.raises(ServiceError, match="Continue in People"):
        asyncio.run(ThreadService(db, broadcast=lambda *_: None).start_turn(OWNER, tid, "Protected relationship input"))
    assert db.threads.list_path(tid) == []


def test_other_principal_cannot_edit_interview(rig):
    _db, tid, svc = rig
    with pytest.raises(ServiceError, match="requires the owner"):
        svc.command(Principal(PrincipalKind.AGENT, "agent"), tid, command_id="x", expected_revision=0, event={"kind": "section", "section": "projects"})


def test_soft_delete_removes_interview_context(rig):
    fact(rig)
    db, tid, _svc = rig
    db.threads.soft_delete(tid)
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM interview_sessions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM interview_events").fetchone()[0] == 0


def test_model_payload_retains_structured_state_after_history_cut(rig):
    fact(rig)
    suggestion(rig)
    db, tid, svc = rig
    message = db.threads.append_message(tid, role="system")
    db.threads.complete_message(message.id, stats_json=json.dumps({"compaction": True}))
    db.threads.append_part(message.id, kind="text", text="Conversation compacted")
    user = db.threads.append_message(tid, role="user")
    db.threads.append_part(user.id, kind="text", text="Revisit my goals")
    payload = ThreadService(db, broadcast=lambda *_: None)._assemble_payload(tid, user.id, db.threads.get(tid))
    context = json.loads(payload["messages"][1]["content"].split("\n", 1)[1])
    assert context["facts"]["goal"]["text"] == svc.get(tid)["facts"]["goal"]["text"]
    assert context["suggestions"]["brief"]["benefit"]
    assert context["user_message_id"] == user.id


@pytest.mark.parametrize("change", ["delete", "sensitive", "draft"])
def test_withdrawn_source_cannot_reappear_in_context_or_suggestions(rig, change):
    state = fact(rig)
    suggestion(rig)
    db, tid, svc = rig
    part = db.threads.get_parts(state["facts"]["goal"]["source_message_id"])[0]
    if change == "delete":
        db.threads.delete_part(part.id)
    else:
        with db._connection() as conn:
            conn.execute(f"UPDATE thread_message_parts SET {change}=1 WHERE id=?", (part.id,))
    assert svc.get(tid)["facts"] == svc.get(tid)["suggestions"] == {}
    assert svc.context(tid, "next-message")["fact_index"] == []
    with pytest.raises(ServiceError):
        suggestion(rig, suggestion_id="reused-source")


def test_bound_dispatch_rejects_other_thread_and_withdrawn_tool(rig):
    db, tid, _svc = rig
    calls = []
    dispatch = ThreadService(db, broadcast=lambda *_: None, tool_dispatch_fn=lambda *args: calls.append(args))._bound_tool_dispatch(tid)
    with pytest.raises(ServiceError, match="differs"):
        dispatch("interview.get", {"thread_id": "another-thread"}, OWNER)
    with pytest.raises(ServiceError, match="unavailable"):
        dispatch("project.setup.finalize", {"session_id": "x"}, OWNER)
    assert calls == []


def test_context_compaction_keeps_domain_evidence_failures_and_complete_call_pairs():
    def pair(name, ident, content):
        return [{"role": "assistant", "tool_calls": [{"id": ident, "function": {"name": name}}]}, {"role": "tool", "tool_call_id": ident, "content": json.dumps(content)}]
    domain = pair("project.get_room", "evidence", {"decisions": ["actual-decision"]})
    first_write = pair("interview.record_fact", "saved", {"revision": 1})
    failure = pair("interview.suggest", "failed", {"error": "revision conflict"})
    latest = pair("interview.suggest", "saved-idea", {"revision": 2})
    assert ThreadService._interview_exchange_history(domain + first_write + failure + latest) == domain + failure + latest


def test_setup_continuation_reuses_live_session_and_replaces_expired_session(rig):
    db, tid, svc = rig
    command(rig, {"kind": "section", "section": "projects"})
    sessions = []
    active_state = "active"
    def domain(name, arguments, principal):
        assert principal is OWNER
        if name == "project.setup.resume":
            return {"id": arguments["session_id"], "state": active_state}
        assert name == "project.setup.start"
        sessions.append(f"session-{len(sessions)}")
        return {"id": sessions[-1], "state": "active"}
    dispatch = ThreadService(db, broadcast=lambda *_: None, tool_dispatch_fn=domain)._bound_tool_dispatch(tid)
    first = dispatch("project.setup.start", {}, OWNER)
    assert dispatch("project.setup.start", {}, OWNER)["id"] == first["id"]
    assert svc.get(tid)["setup_session_id"] == first["id"]
    with pytest.raises(ServiceError, match="continuation"):
        dispatch("project.setup.finalize", {"session_id": "someone-elses-session"}, OWNER)
    active_state = "expired"
    replacement = dispatch("project.setup.start", {}, OWNER)
    assert replacement["id"] != first["id"]
    assert svc.get(tid)["setup_session_id"] == replacement["id"]
