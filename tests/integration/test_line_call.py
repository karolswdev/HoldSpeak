"""The Line (2026-10-29): a whole call through the hub's Calls runner on the
Line adapter (LINE design §4: the runner does not change).

The phone half is the real Line node (baresip supervised, ctrl_tcp, the two
sockets, the end-of-speech rule, the manners) on the fake baresip, a real
separate process replaying a real baresip 4.12.0's recorded events; his
words are tones the tone STT hears back (``tests/fixtures/fake_baresip.py``).
The turn is the hub's real thread loop on ``calls.turn`` with the HOME
engine's RECORDED reply (``tests/fixtures/call_turn_home.json``), the same as
``test_calls_turn.py``'s ai-phone walk.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from holdspeak.line.adapter import Line
from tests.fixtures.line_rig import running_node
from tests.integration.test_calls_turn import (  # noqa: F401  (hub is a fixture)
    RECORDED, REMOTE, _RecordedHomeEngine, _action_items, _note, _service, _write_config, hub,
)

pytestmark = pytest.mark.timeout(180, method="thread")

SIP = {"account": {"kind": "sip", "user": "holdspeak"}, "daily_limit": 20, "owner": "Karol"}


def _run(hub: Any, monkeypatch: pytest.MonkeyPatch, caller: list[dict[str, Any]]) -> tuple:
    _write_config()
    monkeypatch.delenv("HOLDSPEAK_AI_PHONE", raising=False)
    frames: list[tuple[str, Any]] = []
    passes = [dict(p) for p in RECORDED["passes"]]
    service = _service(hub, monkeypatch, lambda model: _RecordedHomeEngine(model, passes, []), frames)

    async def call() -> tuple:
        async with running_node({"incoming": {"remote": REMOTE}, "caller": caller}, config=SIP) as rig:
            line = Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json")
            service.configure(phone=lambda: line)
            outcome = await service.serve_once(wait=10)
            return outcome, rig.commands(), rig.node.heard_times

    outcome, commands, heard = asyncio.run(call())
    return outcome, service, frames, commands, heard


def test_a_call_on_the_line_hears_him_does_the_job_and_says_the_answer(hub, monkeypatch) -> None:
    """A heard question → the turn adds the task → the answer is said with the
    read back; "that's all" ends it; the call is a Note."""
    outcome, service, frames, commands, heard = _run(hub, monkeypatch, [
        {"say": "Blue heron."}, {"say": RECORDED["question"]}, {"say": "That's all, thanks."}])
    assert outcome == "call"
    [task] = _action_items(hub.db)
    assert task["task"] == "Nudge Tomás about the runbook" and task["owner"] == "Me", task
    [record] = service.list()
    full = service.get(record["id"])
    said = [line["text"] for line in full["transcript"] if line["who"] == "holdspeak"]
    final = RECORDED["passes"][-1]["choices"][0]["message"]["content"].strip()
    assert said[0] == "Hello. Say your passphrase." and said[1] == "Hello Karol. What can I do?"
    assert said[2] == f"{final} Done: Added a task: {task['task']}.", said
    assert said[-1] == "Goodbye."
    heard_words = [line["text"] for line in full["transcript"] if line["who"] == "caller"]
    assert heard_words == ["(passphrase)", RECORDED["question"], "That's all, thanks."]
    assert record["ended_by"] == "caller" and record["state"] == "ended"
    note = _note(hub.db, record["note_ref"])
    assert RECORDED["question"] in note.body_markdown and "heron" not in note.body_markdown.lower()
    assert [c["command"] for c in commands if "command" in c] == ["accept", "hangup"]
    # The end-of-speech rule: each utterance was text well under a second after he stopped.
    assert len(heard) == 3 and all(h["text_at"] - h["end_of_speech"] < 0.6 for h in heard), heard


def test_he_speaks_over_the_answer_and_the_runner_keeps_it_as_interrupted(hub, monkeypatch) -> None:
    outcome, service, frames, commands, heard = _run(hub, monkeypatch, [
        {"say": "Blue heron."}, {"say": RECORDED["question"]}, {"say": "That's all, thanks.", "barge_ms": 400}])
    assert outcome == "call"
    [record] = service.list()
    full = service.get(record["id"])
    answer = [line for line in full["transcript"] if line["who"] == "holdspeak"][2]
    assert answer["text"].startswith(RECORDED["passes"][-1]["choices"][0]["message"]["content"].strip()[:20])
    assert answer["interrupted"] is True, full["transcript"]
    assert full["transcript"][-1]["text"] == "Goodbye." and record["ended_by"] == "caller"
