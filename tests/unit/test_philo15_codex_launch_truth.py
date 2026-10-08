"""PHILO-15 lane 14: a Codex launch starts without a human, and the lane
tells the truth (rehearsal 1 part B: B41, B42, B46, B48, B50).

1. B41. Codex's folder-trust screen in a worktree has a "Note: You're in a
   subdirectory of a Git project" paragraph between the path and the
   question. The parser reads the path block only (the Note's repository
   root is its own field), so the screen of exactly the launch's worktree is
   answered. Fenced with the panes captured from the real Codex 0.159 on
   2026-10-07 (80x24 from the real launch, 120x40 from a probe).
2. B48. A turn end is ASKS only when a real question waits; with no question
   it is IDLE, or DONE once the launch's PR is open. Needs you and the lane
   read the same rule.
3. B42 / B46 / B50 on the lane wire: the brief's delivery time, the queued
   Re-brief, the PR's own title. Through the real launch path (the K5 rig).
4. B46. Re-brief: typed now when the agent is idle or asks; mid-turn it is
   queued and typed at the turn end (the coder watcher's flush), once.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.agent_context import read_agent_sessions_strict
from holdspeak.agent_context.models import TURN_ASKS, TURN_DONE, TURN_IDLE, asks_a_question, turn_end
from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.delivery import first_message
from holdspeak.services import launch_rebrief
from holdspeak.services.launch_lane import launch_lane
from tests.unit.test_conductor_k5_supervision import (  # noqa: F401  (fixtures)
    KEY,
    _answered,
    _ask,
    _members,
    _responder,
    db,
    launched,
)
from tests.unit.test_agent_hand import OWNER

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "codex"
REAL_80 = FIXTURES / "trust_screen_worktree_note_80x24.txt"
PROBE_120 = FIXTURES / "trust_screen_worktree_note_120x40.txt"
REAL_WORKTREE = "/private/tmp/hs14.G9nv/hs-project_item-pitem_7dead93a465b4032976f3dd82a6d9195"
REAL_ROOT = "/private/tmp/hs14.G9nv/holdspeak-dayone-rehearsal-1558"
PROBE_WORKTREE = "/private/tmp/hs-p15-14-cap.V2tU/wt-x"
PROBE_ROOT = "/private/tmp/hs-p15-14-cap.V2tU/repo"


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


# ── 1. B41: the captured trust screen ────────────────────────────────


def test_the_captured_screen_reads_the_worktree_not_the_note() -> None:
    prompt = first_message.parse_codex_trust_prompt(_lines(REAL_80))
    assert prompt == {"paths": {REAL_WORKTREE}, "root": REAL_ROOT, "cursor": "yes"}
    assert first_message.codex_trust_prompt_for(_lines(REAL_80), REAL_WORKTREE)["cursor"] == "yes"
    # Only exactly the launch's worktree: never the root, never a near path.
    for other in (REAL_ROOT, REAL_WORKTREE + "0", REAL_WORKTREE[:-1]):
        assert first_message.codex_trust_prompt_for(_lines(REAL_80), other) is None


def test_the_wide_capture_reads_the_same() -> None:
    prompt = first_message.parse_codex_trust_prompt(_lines(PROBE_120))
    assert prompt == {"paths": {PROBE_WORKTREE}, "root": PROBE_ROOT, "cursor": "yes"}


@pytest.mark.skipif(os.path.realpath("/tmp") != "/private/tmp", reason="macOS /tmp symlink")
def test_the_launch_path_matches_through_a_symlink() -> None:
    """The hub may hold ``/tmp/...`` (or ``/var/...``); Codex prints the real path."""
    lines = _lines(REAL_80)
    assert first_message.codex_trust_prompt_for(lines, REAL_WORKTREE.replace("/private/tmp", "/tmp"))
    assert first_message.codex_trust_prompt_for(lines, REAL_ROOT.replace("/private/tmp", "/tmp")) is None


def test_the_cursor_on_quit_reads_other_and_a_note_alone_is_no_path() -> None:
    text = REAL_80.read_text(encoding="utf-8")
    on_quit = text.replace("› 1. Trust and continue", "  1. Trust and continue").replace("  2. Quit", "› 2. Quit")
    assert first_message.parse_codex_trust_prompt(on_quit.split("\n"))["cursor"] == "other"
    no_path = text.replace(REAL_WORKTREE[:76] + "\n  " + REAL_WORKTREE[76:] + "\n\n", "")
    assert "Note:" in no_path and first_message.parse_codex_trust_prompt(no_path.split("\n")) is None
    # The screen left in the scrollback (the composer below it) is not live.
    assert first_message.parse_codex_trust_prompt((text.rstrip() + "\n› Ask Codex to do anything\n  ? for shortcuts").split("\n")) is None


# ── 2. B48: the turn end ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("text", "asks"),
    [
        ("Understood — stopping here … Good luck with the merge!", False),
        ("PR #1 is open and the test passes.", False),
        ("You're welcome — take care!", False),
        ("Should I push the branch?", True),
        ("I made the change.\n\nWhich file should hold the test (a or b)?", True),
        ("Is it **ok?**", True),
        ("See https://x.test/?q=1 for the run.", False),
        # The ruling (Astra r2 on #996 / #998): a question anywhere is a
        # question, whatever else the turn end says and however long it is.
        ("Should I deploy to production?\n\nThe change is done and all tests pass.", True),
        ("Hi! Thanks for the brief. Which branch should I push to? Everything else is done.", True),
        # Codex collapses the lines: a question with a 300-character report after it.
        ("Should I push the branch? " + "I wrote SECURITY.md and its test, ran both tests, and committed. " * 5, True),
        ("Should I deploy to production. The change is done.", True),  # an interrogative, no "?"
        ("Want me to open the PR now", True),
        ("I can push it next. The change is done.", False),
        ("", False),
    ],
)
def test_a_question_is_a_question(text: str, asks: bool) -> None:
    assert asks_a_question(text) is asks


def test_the_turn_end_words() -> None:
    stop = {"hook_event_name": "Stop", "question": "Done. PR #1 is open.", "awaiting_response": True}
    assert turn_end(stop) == TURN_IDLE
    assert turn_end(stop, work_done=True) == TURN_DONE
    assert turn_end({**stop, "question": "May I push?"}, work_done=True) == TURN_ASKS
    permission = {"hook_event_name": "Notification", "notification_type": "permission_prompt", "question": "Run ls"}
    assert turn_end(permission) == TURN_ASKS


def _idle(rig, tmp_path, monkeypatch) -> None:
    """The agent's turn ended with no question: Claude Code's idle prompt."""
    from holdspeak import agent_context

    registry = tmp_path / "agent_sessions.json"
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", registry)
    ingest_agent_hook_event(
        agent="claude",
        payload={"session_id": "smoke-session", "cwd": str(rig.worktree), "hook_event_name": "Notification",
                 "notification_type": "idle_prompt", "message": "Claude is waiting for your input"},
        state_path=registry, now=datetime.now(timezone.utc), env={},
    )


def test_an_idle_turn_end_is_not_in_needs_you_and_draws_no_answer(launched, tmp_path, monkeypatch) -> None:
    """The A5 law (Astra r1 on #996): Needs you is what needs HIM. A turn that
    ended with no question is a lane station and a Conductor lamp only: no
    Needs you row, and the responder does not draft or notify for it."""
    _idle(launched, tmp_path, monkeypatch)
    responder = _responder(launched, tmp_path, "yolo")
    assert _members(launched, tmp_path) == []
    assert responder.triage([KEY]) == {"notify": [], "decide": []}
    _ask(launched, tmp_path, monkeypatch, "Shall I open the pull request now?")
    [row] = _members(launched, tmp_path)
    assert row["waitKind"] == "answer" and row["why"] == "TO ANSWER"


# ── 3. the lane wire: B42 brief time, B48 turn end, B50 PR title ─────


def _lane(rig, tmp_path):
    reads = SimpleNamespace(launcher=lambda: SimpleNamespace(_ledger=rig.launches), registry=lambda: rig.registry)
    sessions = read_agent_sessions_strict(state_path=tmp_path / "agent_sessions.json")
    return launch_lane(
        rig.launch_id, db=rig.db, reads=reads, sessions=sessions, answers=rig.store,
        spool_dir=tmp_path / "agent-events",
    )


def test_the_lane_carries_the_brief_time_the_turn_end_and_the_pr_title(launched, tmp_path, monkeypatch) -> None:
    _responder(launched, tmp_path, "safe")
    record = launched.launches.get(launched.launch_id)
    # B42: the delivery receipt's own time (``executed_at``).
    sent_at = record["brief_sent_at"]
    receipt = launched.db.delivery_receipts.get(record["commands"]["instruction"])["receipt"]
    assert sent_at == receipt["executed_at"]
    lane = _lane(launched, tmp_path)
    assert lane["launch"]["brief_sent_at"] == sent_at and lane["launch"]["instruction_state"] == "sent"

    _idle(launched, tmp_path, monkeypatch)
    assert _lane(launched, tmp_path)["wait"]["turn_end"] == TURN_IDLE
    launched.launches.update(launched.launch_id, follow_through={"pr": {
        "number": 7, "url": "https://github.com/acme/app/pull/7", "state": "open",
        "title": "Add SECURITY.md with the reporting address",
    }})
    lane = _lane(launched, tmp_path)
    assert lane["wait"]["turn_end"] == TURN_DONE
    assert lane["follow_through"]["pr"]["title"] == "Add SECURITY.md with the reporting address"


# ── 4. B46: Re-brief now or after this turn ──────────────────────────


def _sessions(tmp_path):
    return lambda: list(read_agent_sessions_strict(state_path=tmp_path / "agent_sessions.json"))


def _hook(rig, tmp_path, event: str, **payload) -> None:
    """One hook event through the real producer (``ingest_agent_hook_event``)."""
    ingest_agent_hook_event(
        agent="claude",
        payload={"session_id": "smoke-session", "cwd": str(rig.worktree), "hook_event_name": event, **payload},
        state_path=tmp_path / "agent_sessions.json", now=datetime.now(timezone.utc), env={},
    )


def _working(rig, tmp_path, monkeypatch) -> None:
    _answered(rig, tmp_path, monkeypatch, "Go on.")
    _hook(rig, tmp_path, "PreToolUse", tool_name="Bash", tool_input={"command": "ls"})


def _permission(rig, tmp_path, message: str) -> None:
    _hook(rig, tmp_path, "Notification", notification_type="permission_prompt", message=message)


def test_rebrief_types_now_when_the_agent_asks_or_idles(launched, tmp_path, monkeypatch) -> None:
    _ask(launched, tmp_path, monkeypatch, "Stopping here.")
    before = len(launched.typed)
    result = launch_rebrief.rebrief(
        launched.launch_id, "Re-brief: also add a README line.", OWNER,
        service=launched.service, db=launched.db, sessions=_sessions(tmp_path),
    )
    assert result["status"] == "delivered", result
    assert [text for _pane, text in launched.typed[before:]] == ["Re-brief: also add a README line."]
    record = launched.launches.get(launched.launch_id)
    assert record.get("queued_rebrief") is None
    assert record["last_rebrief"]["how"] == "now" and record["last_rebrief"]["command_id"] == result["command_id"]


def test_rebrief_mid_turn_is_queued_and_typed_once_at_the_turn_end(launched, tmp_path, monkeypatch) -> None:
    _working(launched, tmp_path, monkeypatch)
    before = len(launched.typed)
    result = launch_rebrief.rebrief(
        launched.launch_id, "Re-brief: use the security address.", OWNER,
        service=launched.service, db=launched.db, sessions=_sessions(tmp_path),
    )
    assert result["status"] == launch_rebrief.QUEUED
    assert launched.typed[before:] == [], "nothing is typed mid-turn"
    queued = launched.launches.get(launched.launch_id)["queued_rebrief"]
    assert queued["text"] == "Re-brief: use the security address." and queued["key"] == KEY
    _responder(launched, tmp_path, "safe")
    assert _lane(launched, tmp_path)["launch"]["queued_rebrief"]["text"] == "Re-brief: use the security address."

    # Another session's turn end does not flush it.
    assert launch_rebrief.flush_queued(["codex:other"], service=launched.service) == []
    approval = queued["approval"]
    assert approval["principal"] == {"kind": "owner", "identity": "owner-session"}

    # A permission prompt is a wait too, but it is the owner's: the flush
    # never types into it, and the Re-brief stays queued.
    _permission(launched, tmp_path, "Run git push origin HEAD?")
    assert launch_rebrief.flush_queued([KEY], service=launched.service, sessions=_sessions(tmp_path)) == []
    assert launched.typed[before:] == []
    assert launched.launches.get(launched.launch_id)["queued_rebrief"]["text"] == "Re-brief: use the security address."

    # The owner approves; the agent works on, then its turn ends: the flush
    # types it once and consumes that wait.
    _hook(launched, tmp_path, "PostToolUse", tool_name="Bash", tool_input={"command": "git push"})
    _idle(launched, tmp_path, monkeypatch)
    assert launch_rebrief.flush_queued([KEY], service=launched.service, sessions=_sessions(tmp_path)) == [KEY]
    assert [text for _pane, text in launched.typed[before:]] == ["Re-brief: use the security address."]
    record = launched.launches.get(launched.launch_id)
    assert record.get("queued_rebrief") is None
    assert launch_rebrief.flush_queued([KEY], service=launched.service, sessions=_sessions(tmp_path)) == []

    # Provenance: the delivery receipt is the owner's press, by its id.
    done = record["last_rebrief"]
    # The delivery's command id is derived from the press (uuid5 of its id
    # and the attempt), so the kernel receipt names the press that approved it.
    assert done["how"] == "after_turn" and done["press_id"] == approval["command_id"]
    assert done["command_id"] == launch_rebrief.attempt_command_id(approval["command_id"], 1)
    assert done["approved_by"] == approval["principal"] and done["approved_at"] == approval["at"]
    stored = launched.db.delivery_receipts.get(done["command_id"])
    assert stored["receipt"]["outcome"] == "delivered"
    assert stored["receipt"]["receipt_id"] == done["receipt_id"]


def test_a_permission_prompt_on_the_pane_is_not_typed_over() -> None:
    permission = {"hook_event_name": "Notification", "notification_type": "permission_prompt",
                  "question": "Run git push?", "lifecycle": "waiting"}
    assert launch_rebrief.mid_turn(permission)
    assert not launch_rebrief.mid_turn({"hook_event_name": "Stop", "question": "Done.", "awaiting_response": True})
    assert launch_rebrief.mid_turn({"hook_event_name": "PostToolUse", "lifecycle": "working"})
    assert not launch_rebrief.mid_turn({"hook_event_name": "PreToolUse", "lifecycle": "ended"})


def test_rebrief_refuses_an_ended_launch(launched, tmp_path) -> None:
    launched.launches.update(launched.launch_id, stopped={"by": "owner", "at": "2026-10-07T00:00:00Z"})
    result = launch_rebrief.rebrief(
        launched.launch_id, "Re-brief: x", OWNER, service=launched.service, db=launched.db, sessions=lambda: [],
    )
    assert result == {"status": "launch_ended"}
    assert launch_rebrief.rebrief("launch_nope", "x", OWNER, service=launched.service) == {"status": "launch_unknown"}


# ── 5. B49: the launch mounts the CONDUCTOR palette, not a read-only set ──


def test_the_codex_launch_mounts_the_conductor_palette_with_its_mutators() -> None:
    """The hub side of B49. A Codex launch gets the streamable HTTP server
    ``holdspeak`` with the launch credential's variable (``codex_args``); that
    credential lists exactly the CONDUCTOR palette (fenced over HTTP in
    ``test_conductor_k6_agent_mcp``), which carries the item and note
    mutators the brief names. Rehearsal lane 14 read Codex's own ``/mcp``:
    "holdspeak: connected (138 tools)". What the model is offered of them is
    Codex's choice (see the PR: on the LAN model it offered none)."""
    from holdspeak.delivery.agent_mcp import CREDENTIAL_ENV, codex_args
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette

    args = codex_args("http://127.0.0.1:8765", "yolo")
    assert 'mcp_servers.holdspeak.url="http://127.0.0.1:8765/api/mcp"' in args
    assert f'mcp_servers.holdspeak.bearer_token_env_var="{CREDENTIAL_ENV}"' in args
    palette = resolve_palette(CONDUCTOR)
    assert {"project.item.update", "project.item.transition", "desk.create", "door.add_item",
            "follow_through.complete"} <= palette
    assert len(palette) == 138


# ── 6. Astra r2 on #996: the wait episode, the FIFO, expiry, provenance ──


def _press(rig, tmp_path, text: str):
    return launch_rebrief.rebrief(
        rig.launch_id, text, OWNER, service=rig.service, db=rig.db, sessions=_sessions(tmp_path),
    )


def _flush(rig, tmp_path):
    return launch_rebrief.flush_queued([KEY], service=rig.service, sessions=_sessions(tmp_path))


def _texts(rig, before):
    return [text for _pane, text in rig.typed[before:]]


def test_a_permission_prompt_that_begins_before_the_keystroke_refuses_the_delivery(launched, tmp_path, monkeypatch) -> None:
    """The interleaving: the flush reads an idle turn end, then a permission
    prompt arrives while it retargets and arms; the delivery is bound to the
    episode it read, so the steering chokepoint refuses ``wait_not_current``
    and nothing is typed. The Re-brief stays queued."""
    _working(launched, tmp_path, monkeypatch)
    before = len(launched.typed)
    assert _press(launched, tmp_path, "Re-brief: one.")["status"] == launch_rebrief.QUEUED
    _idle(launched, tmp_path, monkeypatch)

    original = launched.service.first_message.retarget

    def retarget_then_permission(launch_id):
        _permission(launched, tmp_path, "Run git push origin HEAD?")
        return original(launch_id)

    monkeypatch.setattr(launched.service.first_message, "retarget", retarget_then_permission)
    assert _flush(launched, tmp_path) == []
    assert _texts(launched, before) == []
    record = launched.launches.get(launched.launch_id)
    assert [q["text"] for q in record["queued_rebriefs"]] == ["Re-brief: one."]
    assert not record.get("rebriefs")

    # An immediate press meets the same race: not typed, kept in order.
    monkeypatch.setattr(launched.service.first_message, "retarget", original)
    _hook(launched, tmp_path, "PostToolUse", tool_name="Bash", tool_input={"command": "git push"})
    _idle(launched, tmp_path, monkeypatch)
    monkeypatch.setattr(launched.service.first_message, "retarget", retarget_then_permission)
    result = _press(launched, tmp_path, "Re-brief: two.")
    assert result["status"] == launch_rebrief.QUEUED and result["now"] == "wait_not_current"
    assert _texts(launched, before) == []


def test_presses_queue_in_order_and_each_ends_in_one_receipt(launched, tmp_path, monkeypatch) -> None:
    _working(launched, tmp_path, monkeypatch)
    before = len(launched.typed)
    for n in range(1, 5):  # one more than the queue holds
        assert _press(launched, tmp_path, f"Re-brief: {n}.")["status"] == launch_rebrief.QUEUED
    record = launched.launches.get(launched.launch_id)
    assert [q["text"] for q in record["queued_rebriefs"]] == ["Re-brief: 2.", "Re-brief: 3.", "Re-brief: 4."]
    [superseded] = record["rebriefs"]
    assert superseded["state"] == launch_rebrief.SUPERSEDED and superseded["text_head"] == "Re-brief: 1."
    assert superseded["approved_at"] and superseded["press_id"] and superseded["command_id"] is None

    # Each genuine turn end takes the oldest one, and only that one.
    _idle(launched, tmp_path, monkeypatch)
    assert _flush(launched, tmp_path) == [KEY]
    assert _texts(launched, before) == ["Re-brief: 2."]
    record = launched.launches.get(launched.launch_id)
    assert [q["text"] for q in record["queued_rebriefs"]] == ["Re-brief: 3.", "Re-brief: 4."]
    assert record["rebriefs"][-1]["state"] == launch_rebrief.SENT

    _working(launched, tmp_path, monkeypatch)
    _idle(launched, tmp_path, monkeypatch)
    assert _flush(launched, tmp_path) == [KEY]
    assert _texts(launched, before) == ["Re-brief: 2.", "Re-brief: 3."]


def test_a_delivery_clears_only_its_own_press(launched, tmp_path, monkeypatch) -> None:
    """A press queued while an older one is being typed is kept."""
    _working(launched, tmp_path, monkeypatch)
    _press(launched, tmp_path, "Re-brief: older.")
    _idle(launched, tmp_path, monkeypatch)
    original = launched.service.first_message.retarget

    def retarget_while_a_new_press_lands(launch_id):
        record = launched.launches.get(launch_id)
        newer = {"id": "press-newer", "text": "Re-brief: newer.", "at": record["queued_rebriefs"][0]["at"],
                 "key": KEY, "approval": {"principal": {"kind": "owner", "identity": "owner-session"},
                                          "at": record["queued_rebriefs"][0]["at"], "command_id": "press-newer"}}
        launched.launches.update(launch_id, queued_rebriefs=[*record["queued_rebriefs"], newer])
        return original(launch_id)

    monkeypatch.setattr(launched.service.first_message, "retarget", retarget_while_a_new_press_lands)
    assert _flush(launched, tmp_path) == [KEY]
    record = launched.launches.get(launched.launch_id)
    assert [q["text"] for q in record["queued_rebriefs"]] == ["Re-brief: newer."]


def test_a_press_whose_agent_never_returns_expires_with_a_receipt(launched, tmp_path, monkeypatch) -> None:
    from datetime import timedelta

    _working(launched, tmp_path, monkeypatch)
    pressed = _press(launched, tmp_path, "Re-brief: late.")
    later = datetime.now(timezone.utc) + timedelta(seconds=launch_rebrief.QUEUE_EXPIRY_SECONDS + 60)
    assert launch_rebrief.expire_queued(launched.service, now=later) == 1
    record = launched.launches.get(launched.launch_id)
    assert record["queued_rebriefs"] == [] and record.get("queued_rebrief") is None
    [receipt] = record["rebriefs"]
    assert receipt["state"] == launch_rebrief.EXPIRED and receipt["detail"] == "AGENT NEVER RETURNED"
    assert receipt["press_id"] == pressed["command_id"]


def test_the_steering_chokepoint_refuses_a_changed_wait(monkeypatch) -> None:
    from holdspeak import coder_steering

    sent: list = []
    monkeypatch.setattr(coder_steering, "_require_delivery_authority", lambda *a, **k: {"status": "ok", "pane_id": "%7"})
    monkeypatch.setattr(coder_steering, "current_wait_episode", lambda key: "wait-permission")
    common = dict(current_target="%7", transport=lambda **kw: sent.append(kw), audit=lambda **kw: 1)
    refused = coder_steering.deliver("codex:s1", "Re-brief: x", expected_wait_id="wait-idle", **common)
    assert refused["status"] == "wait_not_current" and sent == []
    assert coder_steering.deliver("codex:s1", "Re-brief: x", expected_wait_id="wait-permission", **common)["status"] == "delivered"
    assert coder_steering.deliver("codex:s1", "steer", **common)["status"] == "delivered"  # unbound: as before
