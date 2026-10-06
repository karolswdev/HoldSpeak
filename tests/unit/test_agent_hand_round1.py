"""Conductor K2, Astra round 1 on #898: the nine findings, each fenced with
the real producers (PrimitiveService notes and desk decisions, decision
reconciliation + create_from_meeting, a real Thread and Door, real git, a real
kernel broker and command receipts). tmux and the agent are canned only at the
process edge.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak import coder_gate
from holdspeak.db import Database
from holdspeak.delivery.factory_launch import LaunchService
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_brief import compose_agent_brief
from holdspeak.services.agent_hand_service import AgentHandRefused
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.project_service import ProjectService
from tests.unit.test_agent_hand import (
    OWNER,
    PROJECT,
    _rig,
    _seed,
    _trust_screen,
    _trusting_tmux,
    _wait_for,
)

GITHUB_TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
DB_URL = "postgres://admin:hunter2secret@db.example.com:5432/app"


def _trust_for(lines, path):
    from holdspeak.delivery.first_message import trust_prompt_for

    return trust_prompt_for(lines, path)


def _wait_until(read, ok, timeout=10.0):
    import time

    deadline = time.monotonic() + timeout
    while True:
        row = read() or {}
        if ok(row) or time.monotonic() > deadline:
            assert ok(row), row
            return row
        time.sleep(0.05)


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "hub.db")
    _seed(database)
    return database


def _project(db: Database, name: str) -> str:
    return ProjectService(db).create_project(OWNER, name=name)["id"]


# ── 1. People content never escapes through memory ──────────────────


def test_people_section_of_a_recalled_note_is_cut_before_flattening(db) -> None:
    pid = _project(db, "Payments")
    notes = PrimitiveService(db)
    a = notes.create_note(OWNER, title="Login plan", body_markdown=(
        "Sessions move to Redis.\n\n## People\nAlice is on leave; her 1:1 is Thursday."))
    b = notes.create_note(OWNER, title="Login timeout fix", body_markdown="Raise the timeout to 30 s.")
    for note in (a, b):
        ProjectService(db).add_resource(OWNER, pid, f"note:{note['id']}")

    recalled = compose_agent_brief(db, f"note:{b['id']}", control_mode="yolo")
    assert "Sessions move to Redis." in recalled["text"]  # note A came back through memory
    assert "Alice" not in recalled["text"] and "1:1" not in recalled["text"]
    assert recalled["people_cut"] >= 1

    direct = compose_agent_brief(db, f"note:{a['id']}", control_mode="yolo")
    assert "Sessions move to Redis." in direct["text"]
    assert "Alice" not in direct["text"] and direct["people_cut"] >= 1


def test_a_memory_page_sentence_citing_a_people_source_is_left_out(db) -> None:
    from holdspeak.memory.pages import spec_for, write_page
    from holdspeak.memory.retain import sweep
    from tests.unit.test_memory_slice5_pages import Pages

    pid = _project(db, "Payments")
    decision = PrimitiveService(db).create_decision(
        OWNER, title="Use Redis for sessions", status="accepted",
        context_markdown="Sessions time out.\n\n## People\nAlice owns it but is on leave until Thursday.",
        decision_markdown="Use Redis for sessions.",
    )
    ProjectService(db).add_resource(OWNER, pid, f"decision:{decision['id']}")
    note = PrimitiveService(db).create_note(OWNER, title="Timeout bug", body_markdown="The login times out.")
    ProjectService(db).add_resource(OWNER, pid, f"note:{note['id']}")
    sweep(db)
    written = write_page(db, Pages(), ("project", pid), spec_for("project", "what-we-decided"))
    assert written["sentences"] == 1  # the page holds the People text

    brief = compose_agent_brief(db, f"note:{note['id']}", control_mode="yolo")
    assert "Alice" not in brief["text"] and "Thursday" not in brief["text"]


# ── 2. every composed field is redacted ──────────────────────────────


def test_the_whole_outbound_brief_is_redacted(db, tmp_path) -> None:
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.services.decision_record_service import DecisionRecordService

    pid = _project(db, "Payments")
    started = datetime.now().replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-sec", started_at=started, ended_at=started, title="Ops sync",
        intel=IntelSnapshot(timestamp=started.timestamp(), summary="", action_items=[]),
        intel_status="completed", capture_status="finalized",
    ))
    db.projects.associate_meeting_project(meeting_id="m-sec", project_id=pid, source="manual", confidence=1.0)
    db.plugins.record_artifact(
        artifact_id="artifact-sec", meeting_id="m-sec", artifact_type="decisions", title="Decisions",
        structured_json={"decisions": [{"decision": f"Rotate the CI token {GITHUB_TOKEN} weekly"}]},
        plugin_id="decision_capture",
    )
    db.decisions.reconcile_artifact("artifact-sec")
    decision_id = str(db.decisions.list()[0].id)
    DecisionRecordService(db).create_from_meeting(OWNER, decision_id)
    note = PrimitiveService(db).create_note(OWNER, title="Rotate secrets", body_markdown="Do it.")
    ProjectService(db).add_resource(OWNER, pid, f"note:{note['id']}")
    repo = tmp_path / "repo"
    (repo / ".hs").mkdir(parents=True)
    (repo / ".hs" / "context.md").write_text(f"The test DB is {DB_URL}\n", encoding="utf-8")

    brief = compose_agent_brief(
        db, f"note:{note['id']}", control_mode="yolo", repo_path=str(repo),
        instruction=f"Use {GITHUB_TOKEN} if you must",
    )
    text = brief["text"]
    assert "Rotate the CI token" in text  # the Project decision is in the brief
    assert "The test DB is" in text  # and the .hs/ fact
    for secret in (GITHUB_TOKEN, "hunter2secret", DB_URL):
        assert secret not in text, secret


# ── 3. folder trust: exact path, live prompt, one confirm ────────────


@pytest.mark.parametrize("shown", ["/tmp/hs-action-10", "/tmp/hs-action-1/other", "/tmp/hs-action-1 evil",
                                   "/tmp/hs-action", "/private/tmp/hs-action-1"])
def test_trust_prompt_matches_only_the_exact_path(shown) -> None:
    lines = _trust_screen(shown, cursor_on_yes=True).split("\n")
    assert _trust_for(lines, "/tmp/hs-action-1") is None


def test_trust_prompt_reads_a_wrapped_path_and_the_cursor() -> None:
    path = "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/work/hs-action-ai_1"
    on_no = _trust_for(_trust_screen(path).split("\n"), path)
    on_yes = _trust_for(_trust_screen(path, cursor_on_yes=True).split("\n"), path)
    assert on_no["cursor"] == "no" and on_yes["cursor"] == "yes"


def test_a_trust_prompt_in_the_scrollback_is_not_live() -> None:
    path = "/tmp/hs-action-1"
    stale = _trust_screen(path, cursor_on_yes=True) + "\n\nClaude Code ready\n❯ "
    assert _trust_for(stale.split("\n"), path) is None


def test_an_unchanged_frame_on_yes_gets_one_enter_ever(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False,
               screen=lambda worktree: _trust_screen(worktree, cursor_on_yes=True))
    # The fake agent ignores Enter: the prompt stays on screen, unchanged.
    rig.tmux.on_keys = lambda pane, keys: None
    result = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "trust_state", "timeout")
    rig.tmux.ended = True
    assert [key for _pane, keys in rig.keys_sent for key in keys] == ["Enter"]
    assert record["trust_state"] == "timeout"


def test_a_changed_pane_gets_no_key(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False,
               screen=lambda worktree: _trust_screen(worktree, cursor_on_yes=True))
    rig.tmux.identity_lost_after_peek = True  # the pane is not the one spawned any more
    result = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_until(lambda: rig.launches.get(result["launch_id"]), lambda r: r.get("trust_state"))
    rig.tmux.ended = True
    assert record["trust_state"] not in ("answered", "not_seen")  # refused by the steering path
    assert rig.keys_sent == []
    assert record["commands"]["trust"]  # the refused key is receipted


# ── 4. concurrent arming; a failed creation keeps nothing ────────────


def test_concurrent_arming_loses_no_hold(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    paths = [tmp_path / f"wt-{n}" for n in range(12)]
    barrier = threading.Barrier(len(paths))

    def arm(path):
        barrier.wait()
        rig.hand._arm_gate(path, path.name)

    workers = [threading.Thread(target=arm, args=(path,)) for path in paths]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    config = coder_gate.load_gate_config(rig.gate_path)
    assert sorted(config.armed_paths) == sorted(str(path) for path in paths)
    assert set(config.repos) == {str(path) for path in paths}


def test_a_branch_collision_releases_this_calls_hold_only(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    other = str((tmp_path / "other-repo").resolve())
    coder_gate.save_gate_config(coder_gate.GateConfig(armed=False, repos={other: ["Bash"]}), rig.gate_path)
    subprocess.run(["git", "-C", str(rig.repo), "branch", "hs/action-ai_1"], check=True)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "failed" and result["failure"]["stage"] == "worktree_create"
    assert not rig.worktree.exists() and rig.tmux.sessions == {}
    config = coder_gate.load_gate_config(rig.gate_path)
    assert config.repos == {other: ["Bash"]} and config.armed_paths == []


# ── 5. dedupe keeps distinct events and merges a capture ─────────────


def _transcript(path: Path, *texts: str) -> None:
    rows = [{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": t}]}}
            for t in texts]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _stop(tmp_path, state, transcript, at, *, capture):
    from holdspeak.agent_context.sessions import ingest_agent_hook_event

    return ingest_agent_hook_event(
        agent="claude", payload={"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": "Stop",
                                 "transcript_path": str(transcript)},
        state_path=state, now=at, capture_messages=capture, env={},
    )


def _row(state):
    return json.loads(state.read_text(encoding="utf-8"))["sessions"]["claude:s1"]


T0 = datetime(2026, 10, 6, 9, 0, 0, tzinfo=timezone.utc)


def test_two_stops_with_new_transcript_content_are_two_events(tmp_path) -> None:
    state, transcript = tmp_path / "state.json", tmp_path / "t.jsonl"
    _transcript(transcript, "Should I use Redis?")
    _stop(tmp_path, state, transcript, T0, capture=True)
    _transcript(transcript, "Should I use Redis?", "Should I also drop the old table?")
    _stop(tmp_path, state, transcript, T0 + timedelta(seconds=1), capture=True)
    row = _row(state)
    assert row["event_count"] == 2
    assert row["question"] == "Should I also drop the old table?"


@pytest.mark.parametrize("first_captures", [True, False])
def test_a_doubled_stop_merges_the_capture_in_either_order(tmp_path, first_captures) -> None:
    state, transcript = tmp_path / "state.json", tmp_path / "t.jsonl"
    _transcript(transcript, "Should I use Redis?")
    _stop(tmp_path, state, transcript, T0, capture=first_captures)
    _stop(tmp_path, state, transcript, T0 + timedelta(milliseconds=40), capture=not first_captures)
    row = _row(state)
    assert row["event_count"] == 1
    assert row["question"] == "Should I use Redis?"
    assert row["last_assistant_text"] == "Should I use Redis?"


def test_equal_payloads_without_identity_are_not_merged(tmp_path) -> None:
    from holdspeak.agent_context.sessions import ingest_agent_hook_event

    state = tmp_path / "state.json"
    for offset in (0, 1):
        ingest_agent_hook_event(
            agent="claude", payload={"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": "Stop"},
            state_path=state, now=T0 + timedelta(seconds=offset), env={},
        )
    assert _row(state)["event_count"] == 2


# ── 6. /agent in a real Thread resolves its Project's repository ─────


def test_thread_agent_hands_through_the_declared_operation(tmp_path, monkeypatch) -> None:
    from tests.unit.test_thread_todo import _cleanup, _hub, _wait_done

    hub = _hub(tmp_path / "hub", control_mode="yolo")
    try:
        db, svc = hub["db"], hub["svc"]
        pid = ProjectService(db).create_project(OWNER, name="Railsproj")["id"]
        other = ProjectService(db).create_project(OWNER, name="Elsewhere")["id"]
        for project in (pid, other):
            note = PrimitiveService(db).create_note(
                OWNER, title=f"Plan {project}", body_markdown="Plan the login fix: raise the timeout.")
            ProjectService(db).add_resource(OWNER, project, f"note:{note['id']}")
        from holdspeak.memory.retain import sweep

        sweep(db)  # memory indexes the notes, so the attached Project's search finds them
        thread = svc.create(title="agent test")
        turn = asyncio.run(svc.start_turn(OWNER, thread["id"], "Plan the fix", refs=[f"project:{pid}"]))
        _wait_done(db, turn["assistant_message_id"], timeout=45)

        rig = _rig(tmp_path / "rig", db, monkeypatch, project=pid, item=("action", "x"))
        from holdspeak.runtime.composition import service as runtime_service

        live = runtime_service("agent_hand_service", lambda: None)
        assert live is not None  # the hub's own instance answers the declared operation
        monkeypatch.setattr(live, "_launch_service", lambda: rig.service)
        monkeypatch.setattr(live, "_gate_path", rig.gate_path)
        monkeypatch.setattr(live, "_project_map", {"projects": {}})

        result = asyncio.run(svc.agent_from_thread(OWNER, thread["id"], "Fix the login timeout"))
        hand = result["hand"]
        assert result["project_id"] == pid
        assert hand["status"] == "launched", hand
        item_id = result["item"]["id"]
        assert hand["origin_ref"] == {"kind": "action", "id": item_id}
        assert hand["story_ref"] == {"project": pid, "story_id": f"action-{item_id}"}
        rows = db.project_relationships.list_for_project(pid)
        assert f"action:{item_id}" in [row.resource_ref for row in rows]
        rig.tmux.ended = True

        # Two Projects named in one Thread, none chosen: refused by name.
        turn = asyncio.run(svc.start_turn(OWNER, thread["id"], "Plan the login fix there too",
                                          refs=[f"project:{other}"]))
        _wait_done(db, turn["assistant_message_id"], timeout=45)
        from holdspeak.services.errors import ValidationError

        with pytest.raises(ValidationError) as exc:
            asyncio.run(svc.agent_from_thread(OWNER, thread["id"], "Another fix"))
        assert exc.value.code == "project_ambiguous"
    finally:
        _cleanup(hub)


# ── 7. Codex: readiness first, the receipt decides ───────────────────


def test_codex_without_hooks_holds_the_brief_by_name(tmp_path, db, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    rig = _rig(tmp_path, db, monkeypatch, agent="codex")
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert result["status"] == "launched" and result["instruction_state"] == "hooks_missing"
    assert rig.typed == []
    rig.tmux.ended = True


def test_codex_types_only_after_it_registers(tmp_path, db, monkeypatch) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "hooks.json").write_text('{"hooks": {"x": "holdspeak agent-hook ingest --agent codex"}}')
    monkeypatch.setenv("HOME", str(home))
    gate = {"ready": False}
    rig = _rig(tmp_path, db, monkeypatch, agent="codex", register_when=lambda tmux: gate["ready"],
               screen=lambda worktree: "OpenAI Codex\nLoading the model...")
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert result["instruction_state"] == "pending"
    import time

    time.sleep(0.3)
    assert rig.typed == []  # the startup screen gets nothing
    gate["ready"] = True
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    assert len(rig.typed) == 1 and record["commands"]["instruction"]
    rig.tmux.ended = True


@pytest.mark.parametrize("profile, agent", [("codex-default", "codex"), ("claude-default", "claude")])
def test_a_failed_send_is_never_sent(tmp_path, db, monkeypatch, profile, agent) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "hooks.json").write_text('{"hooks": {"x": "holdspeak agent-hook ingest --agent codex"}}')
    monkeypatch.setenv("HOME", str(home))
    rig = _rig(tmp_path, db, monkeypatch, agent=agent, text_fails=True)
    result = rig.hand.hand(OWNER, "action", "ai_1", profile=profile)
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "transport_error")
    receipt = rig.commands.receipt(record["commands"]["instruction"])
    assert receipt["receipt"]["outcome"] == "transport_error"
    assert record["pending_brief"]["text"]  # still held, for a resume
    rig.tmux.ended = True


# ── 8. a pending brief survives a restart and never ends as success ──


def _restart(rig) -> LaunchService:
    """A new launch service on the same ledger, registry and broker (a hub restart)."""
    service = LaunchService(
        profiles=rig.service._profiles, registry=rig.registry, targets=rig.service._targets,
        commands=rig.commands, attempts=rig.db.work_attempts, ledger=type(rig.launches)(rig.launches._path),
        runner=rig.tmux, local_node_id="local",
    )
    service.bind_kernel(rig.broker)
    return service


def test_a_restart_resumes_the_pending_brief(tmp_path, db, monkeypatch) -> None:
    gate = {"ready": False}
    rig = _rig(tmp_path, db, monkeypatch, register_when=lambda tmux: gate["ready"])
    result = rig.hand.hand(OWNER, "action", "ai_1")
    rig.service._first._running.clear()  # the old waiter is gone with the old hub
    restarted = _restart(rig)
    gate["ready"] = True
    record = _wait_for(lambda: restarted._ledger.get(result["launch_id"]), "instruction_state", "sent")
    assert record["pending_brief"] is None and len(rig.typed) == 1
    rig.tmux.ended = True


def test_a_restart_names_an_interrupted_brief(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    rig.tmux.ended = True  # the agent died while the hub was down
    restarted = _restart(rig)
    assert restarted._ledger.get(result["launch_id"])["instruction_state"] in ("interrupted", "session_gone")


def test_handing_again_resumes_the_same_launch(tmp_path, db, monkeypatch) -> None:
    gate = {"ready": False}
    rig = _rig(tmp_path, db, monkeypatch, register_when=lambda tmux: gate["ready"], text_fails=True)
    first = rig.hand.hand(OWNER, "action", "ai_1")
    _wait_for(lambda: rig.launches.get(first["launch_id"]), "instruction_state", "pending")
    gate["ready"] = True
    _wait_for(lambda: rig.launches.get(first["launch_id"]), "instruction_state", "transport_error")
    rig.tmux.ended = False
    import tests.unit.test_agent_hand_round1 as me  # noqa: F401

    again = rig.hand.hand(OWNER, "action", "ai_1")
    assert again["resumed"] is True and again["launch_id"] == first["launch_id"]
    rig.tmux.ended = True


def test_an_undelivered_launch_ends_failed_not_succeeded(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    rig.tmux.ended = True  # the session exits before it ever registered
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "state", "ended_undelivered")
    receipt = rig.broker.store.receipt(result["operation_id"])
    assert receipt["outcome"] == "failed"
    assert record["instruction_state"] == "session_gone"


# ── 9. the item first; the code rides the refusal ────────────────────


def test_an_unknown_item_is_item_unknown_with_a_code(tmp_path, db, monkeypatch) -> None:
    from holdspeak import operations

    rig = _rig(tmp_path, db, monkeypatch)
    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Unrelated' WHERE id=?", (PROJECT,))
    ops = operations.bind_available({"agent_hand_service": rig.hand})
    with pytest.raises(AgentHandRefused) as exc:
        ops.invoke(OWNER, "agent.hand", {"kind": "action", "id": "x"})
    assert exc.value.code == "item_unknown" and exc.value.context["status"] == 404
