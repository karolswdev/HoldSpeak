"""The review of the Telegram inbound work (#2306), fixed forward.

One part per point of the review. Telegram is a fake transport, Ask runs on
a fake engine through the real door, the decoder is a seam, and ONE test
runs the real ``ffmpeg`` on a clip made here that is longer than it says.

1. An Ask from Telegram runs with no tools, for every engine kind.
2. The words of an answer leave only with a record that says they may.
3. A voice note costs a bounded amount: bytes, decoded seconds, wall clock,
   one worker, a short queue.
4. A press writes one thing at most.
5. Words that wait are pruned and cleared, or the act is refused.
"""
from __future__ import annotations

import asyncio
import io
import math
import shutil
import stat
import struct
import threading
import time
import wave
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.intel.cli_engine import CliEngine
from holdspeak.services import reach_commands, reach_inbound, telegram_reach
from holdspeak.services.ask_service import AskService, _AskAnswerAdapter
from holdspeak.services.telegram_reach import TelegramRefused
from tests.unit.test_ask_engine_door import OWNER as ASK_OWNER
from tests.unit.test_ask_engine_door import assign_answers
from tests.unit.test_cli_engine import calls, egress, fake_bin  # noqa: F401
from tests.unit.test_mcp_ask import _call_ok, _patch_ask  # noqa: F401
from tests.unit.test_reach_commands import say, texts
from tests.unit.test_reach_inbound import Reads, buttons, d, notes, press, sent_id, tasks, voice  # noqa: F401
from tests.unit.test_reach_telegram import keystore  # noqa: F401
from tests.unit.test_reach_telegram_guards import OTHER_TOKEN
from tests.unit.test_reach_telegram_setup import OWNER

REAL_DECODE = getattr(reach_inbound, "_decode_bytes", None)   # None on a tree before the fix: each test then fails by itself
QUESTION = "Add a task: email Dana about the cutover."


# ── 1. Ask from Telegram has no tools ────────────────────────────────

class Writer:
    """An agent engine that writes when it has the desk's tools."""

    desk_tools = True
    wrote: list[str] = []
    prompts: list[str] = []

    def run_prompt(self, **kwargs: Any) -> str:
        Writer.prompts.append(str(kwargs.get("system_prompt") or ""))
        if self.desk_tools:
            Writer.wrote.append("door.add_item")
            return "Done. I added the task."
        return "I cannot add it from here. Your desk is needed for that."


@pytest.fixture
def ask(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    db = Database(tmp_path / "ask-t4.db")
    broker = assign_answers(db, Writer)
    Writer.wrote, Writer.prompts = [], []
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    return AskService(db, broker=broker)


def test_an_ask_with_no_tools_cannot_write_and_says_the_desk_is_needed(ask: Any) -> None:
    result = asyncio.run(ask.ask(ASK_OWNER, QUESTION, no_tools=True))
    assert Writer.wrote == []                                  # the engine had no tools to write with
    assert "Your desk is needed for that" in result["output"]
    assert "You have no tools in this run" in Writer.prompts[-1]
    assert result["provenance"] == {"tools": "none", "refs": [], "complete": True}
    # The rig bites: the same engine, asked with its tools, writes.
    asyncio.run(ask.ask(ASK_OWNER, QUESTION))
    assert Writer.wrote == ["door.add_item"]


def test_no_tools_and_desk_tools_together_are_refused(ask: Any) -> None:
    from holdspeak.services.errors import ServiceError

    with pytest.raises(ServiceError):
        asyncio.run(ask.ask(ASK_OWNER, QUESTION, no_tools=True, desk_tools=True))
    assert Writer.wrote == []


def test_a_real_cli_engine_gets_no_credential_and_no_server_with_no_tools(fake_bin: Path, egress: list) -> None:
    class Inner:
        def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> dict[str, Any]:
            return {"output": engine.run_prompt(user_prompt="Add a task")}

    engine = CliEngine.from_endpoint("cli:codex")
    assert engine.desk_tools is True
    _AskAnswerAdapter(Inner(), no_tools=True).dispatch(engine, {}, None)
    (call,) = calls(fake_bin, "codex")
    assert call["credential"] == ""                            # no run credential was made: no desk operation can be called
    assert not any("mcp_servers.holdspeak" in part and "enabled=false" not in part for part in call["argv"])
    assert engine.desk_tools is True                           # the routed engine itself is not changed


def test_the_ask_operation_takes_tools_none_and_telegram_sends_it(_patch_ask, monkeypatch) -> None:
    _call_ok("ask.run", {"question": "Who owns it?", "tools": "none"})
    assert _patch_ask.calls[-1][2]["no_tools"] is True
    seen: list[Any] = []
    monkeypatch.setattr("holdspeak.mcp.tools.dispatch", lambda name, args, principal: seen.append((name, args)) or {})
    reach_commands.Reads().ask(OWNER, "Who owns it?")
    assert seen == [("ask.run", {"question": "Who owns it?", "tools": "none"})]


# ── 2. the words of an answer leave only with a record ───────────────

def ask_from_telegram(d: Any, answer: dict[str, Any], question: str = "What did Dana tell me?") -> tuple[dict, str]:
    d.reads.answer_of = answer
    d.tg.handle_update(say(question))
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Ask my desk"], sent_id(d.bot)))
    return out, d.bot.of("sendMessage")[-1]["text"]


def test_a_real_answer_given_people_content_sends_no_word(d, ask: Any) -> None:
    answer = asyncio.run(ask.ask(ASK_OWNER, "What did Dana tell me?", no_tools=True,
                                 context=[{"kind": "person", "id": "p1", "title": "Dana"}]))
    assert answer["provenance"]["refs"] == ["person:p1"]
    out, said = ask_from_telegram(d, answer)
    assert out == {"action": "asked", "on_desk": True}
    assert "The answer is on your desk." in said and "desk is needed" not in said


def test_a_real_answer_with_no_record_sends_no_word(d, ask: Any) -> None:
    answer = asyncio.run(ask.ask(ASK_OWNER, "What did Dana tell me?", no_tools=True))
    answer.pop("provenance")                                   # the shape of an Ask that could use tools
    out, said = ask_from_telegram(d, answer)
    assert out == {"action": "asked", "on_desk": True}
    assert "The answer is on your desk." in said and "desk is needed" not in said


@pytest.mark.parametrize("record", [
    {"tools": "desk", "refs": [], "complete": True},
    {"tools": "none", "refs": [], "complete": False},
    {"tools": "none", "refs": None, "complete": True},
    {"tools": "none", "refs": ["note:n1", "one_on_one:o1"], "complete": True},
])
def test_a_record_that_does_not_clear_the_words_keeps_them_on_the_desk(d, record: dict[str, Any]) -> None:
    out, said = ask_from_telegram(d, {"output": "Dana is unhappy.", "provenance": record})
    assert out == {"action": "asked", "on_desk": True} and "unhappy" not in said


def test_a_real_plain_answer_goes(d, ask: Any) -> None:
    answer = asyncio.run(ask.ask(ASK_OWNER, QUESTION, no_tools=True))
    out, said = ask_from_telegram(d, answer, QUESTION)
    assert out == {"action": "asked", "on_desk": False}
    assert "Your desk is needed for that" in said


# ── 3. what a voice note may cost ────────────────────────────────────

def test_a_file_larger_than_the_limit_is_not_fetched(d) -> None:
    d.bot.instead["getFile"] = {"ok": True, "result": {"file_id": "f7", "file_path": "voice/file_7.oga",
                                                       "file_size": reach_inbound.VOICE_MAX_BYTES + 1}}
    out = d.tg.handle_update(voice(size=0))                    # the message itself says no size
    assert out["action"] == "voice_refused" and "too large" in texts(d.bot)[-1]
    assert d.fetched == [] and d.decoded == [] and reach_inbound.waiting_count(d.tg) == 0


def fake_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> Path:
    folder = tmp_path / "fake-ffmpeg"
    folder.mkdir()
    script = folder / "ffmpeg"
    script.write_text("#!/usr/bin/env python3\nimport os, sys, time\n" + body)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{folder}:{__import__('os').environ['PATH']}")
    return folder


def test_a_decoder_that_never_stops_writing_is_stopped_at_the_cap(tmp_path, monkeypatch) -> None:
    fake_ffmpeg(tmp_path, monkeypatch, "open(os.path.join(os.path.dirname(__file__), 'argv'), 'w').write(' '.join(sys.argv[1:]))\n"
                                       "while True:\n    sys.stdout.buffer.write(b'\\0' * 65536)\n")
    monkeypatch.setattr(reach_inbound, "VOICE_MAX_SECONDS", 2)
    began = time.monotonic()
    with pytest.raises(reach_inbound.VoiceRefused) as refused:
        REAL_DECODE(b"OggS")
    assert refused.value.words == reach_inbound.VOICE_TOO_LONG_WORDS
    assert time.monotonic() - began < 20
    argv = (tmp_path / "fake-ffmpeg" / "argv").read_text()
    assert "-i pipe:0" in argv and "-t 3" in argv              # stdin in; the decoder is told to stop too
    assert reach_inbound.PCM_BYTES_A_SECOND == 32_000 and reach_inbound.DECODE_SECONDS == 60.0


def test_a_decoder_that_hangs_is_killed_at_its_wall_clock(tmp_path, monkeypatch) -> None:
    fake_ffmpeg(tmp_path, monkeypatch, "time.sleep(600)\n")
    monkeypatch.setattr(reach_inbound, "DECODE_SECONDS", 0.5)
    began = time.monotonic()
    with pytest.raises(RuntimeError):
        REAL_DECODE(b"OggS")
    assert time.monotonic() - began < 20


def clip(seconds: float) -> bytes:
    made = io.BytesIO()
    with wave.open(made, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(i / 8))) for i in range(int(16000 * seconds))))
    return made.getvalue()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed on this machine")
def test_the_real_ffmpeg_refuses_a_clip_that_is_longer_than_it_says(d, monkeypatch) -> None:
    monkeypatch.setattr(reach_inbound, "_decode_bytes", REAL_DECODE)
    monkeypatch.setattr(reach_inbound, "VOICE_MAX_SECONDS", 2)
    d.tg.fetch_file = lambda path: clip(1.0)
    assert d.tg.handle_update(voice(duration=1))["action"] == "heard"
    (audio,) = d.reads.heard_audio
    assert 15000 <= len(audio) <= 17000                        # one second at 16 kHz, decoded from the pipe
    d.tg.fetch_file = lambda path: clip(6.0)                   # six seconds; the message says one
    out = d.tg.handle_update(voice(duration=1))
    assert out["action"] == "voice_refused" and out["words"] == reach_inbound.VOICE_TOO_LONG_WORDS
    assert len(d.reads.heard_audio) == 1                       # the long clip was never heard
    assert reach_inbound.waiting_count(d.tg) == 1


def chat() -> Any:
    said: list[str] = []
    return SimpleNamespace(said=said, _send=lambda chat_id, text, keyboard=None, *, data_class: said.append(text))


def wait_for(check: Any, seconds: float = 10.0) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if check():
            return True
        time.sleep(0.01)
    return False


def test_one_job_runs_three_wait_and_the_next_gets_the_busy_line() -> None:
    tg = chat()
    release, running, ran = threading.Event(), threading.Event(), []

    def job(name: str) -> Any:
        def run(gone: threading.Event) -> dict[str, Any]:
            running.set()
            release.wait(10)
            ran.append((name, threading.current_thread().name))
            return {}
        return run

    try:
        assert reach_inbound._submit(tg, "1", job("a"), lambda: None, 30, "voice") == {"action": "voice_queued"}
        assert running.wait(10)
        for name in "bcd":
            assert reach_inbound._submit(tg, "1", job(name), lambda: None, 30, "voice") == {"action": "voice_queued"}
        assert reach_inbound.WORKER_QUEUE == 3 and not reach_inbound.has_room(tg)
        began = time.monotonic()
        assert reach_inbound._submit(tg, "1", job("e"), lambda: None, 30, "voice") == {"action": "busy"}
        assert time.monotonic() - began < 1                    # the caller (the poll) did not wait
        assert tg.said == ["Your desk is busy. Send it again in a minute."]
    finally:
        release.set()
    assert wait_for(lambda: len(ran) == 4)
    assert [name for name, _thread in ran] == list("abcd")     # one at a time, in order
    reach_inbound.shutdown(tg)
    assert wait_for(lambda: not tg._inbound_worker._thread.is_alive())


def test_a_voice_note_that_takes_too_long_is_abandoned_and_keeps_nothing(d, monkeypatch) -> None:
    d.tg.inbound_inline = False
    monkeypatch.setattr(reach_inbound, "VOICE_JOB_SECONDS", 0.3)
    release = threading.Event()

    def slow(principal: Any, audio: Any) -> str:
        release.wait(20)
        return "words that came too late"
    d.reads.transcribe = slow
    try:
        began = time.monotonic()
        assert d.tg.handle_update(voice()) == {"action": "voice_queued"}
        assert time.monotonic() - began < 2                    # the poll does not wait for the hearing
        assert wait_for(lambda: reach_inbound.VOICE_SLOW_WORDS in texts(d.bot))
    finally:
        release.set()
    assert wait_for(lambda: not any(t.name == "reach-inbound-job" and t.is_alive() for t in threading.enumerate()))
    assert reach_inbound.waiting_count(d.tg) == 0 and notes(d.db) == []
    assert not any("too late" in text for text in texts(d.bot))
    assert (reach_inbound.VOICE_JOB_SECONDS, reach_inbound.ASK_JOB_SECONDS) == (0.3, 120.0)
    reach_inbound.shutdown(d.tg)


def test_an_ask_that_takes_too_long_says_one_line(d, monkeypatch) -> None:
    d.tg.inbound_inline = False
    monkeypatch.setattr(reach_inbound, "ASK_JOB_SECONDS", 0.3)
    release = threading.Event()

    def slow(principal: Any, question: str) -> dict[str, Any]:
        release.wait(20)
        return {"output": "late words", "provenance": {"tools": "none", "refs": [], "complete": True}}
    d.reads.ask = slow
    try:
        d.tg.handle_update(say("Who owns the cutover window?"))
        out = d.tg.handle_update(press(dict(buttons(d.bot))["Ask my desk"], sent_id(d.bot)))
        assert out == {"action": "ask_queued"}
        assert wait_for(lambda: reach_inbound.ASK_SLOW_WORDS in texts(d.bot))
    finally:
        release.set()
    assert wait_for(lambda: not any(t.name == "reach-inbound-job" and t.is_alive() for t in threading.enumerate()))
    assert not any("late words" in text for text in texts(d.bot))
    reach_inbound.shutdown(d.tg)


def test_stop_does_not_wait_for_a_job_that_runs(d) -> None:
    d.tg.inbound_inline = False
    release = threading.Event()
    d.reads.transcribe = lambda principal, audio: release.wait(20) and "" or ""
    try:
        d.tg.handle_update(voice())
        began = time.monotonic()
        d.reach.stop()
        assert time.monotonic() - began < 1
        assert d.tg._inbound_worker._stopped.is_set()
    finally:
        release.set()


# ── 4. a press writes one thing at most ──────────────────────────────

def failing(d: Any, monkeypatch: pytest.MonkeyPatch, when: Any) -> dict[str, bool]:
    """The store of the words that wait refuses the writes ``when`` names,
    while ``on``."""
    real = d.tg._save_policy
    switch = {"on": True}

    def save(name: str, state: Any) -> bool:
        if switch["on"] and name == reach_inbound.INBOUND_POLICY and when(state):
            return False
        return real(name, state)
    monkeypatch.setattr(d.tg, "_save_policy", save)
    return switch


def used(state: Any) -> bool:
    return any(row.get("used") for row in state.get("pending", {}).values())


def test_the_words_are_marked_used_before_the_note_is_written(d) -> None:
    d.tg.handle_update(voice())
    seen: list[Any] = []
    real = reach_commands.Reads.note

    def note(principal: Any, words: str) -> Any:
        seen.append(dict(d.tg._policy(reach_inbound.INBOUND_POLICY)["pending"]))
        return real(d.reads, principal, words)
    d.reads.note = note
    d.tg.handle_update(press(dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)))
    ((row,),) = [list(rows.values()) for rows in seen]
    assert row["used"] == "note"                               # durable before the write ran


def test_a_mark_that_is_not_written_writes_nothing(d, monkeypatch) -> None:
    d.tg.handle_update(voice())
    data, message_id = dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)
    failing(d, monkeypatch, used)
    assert d.tg.handle_update(press(data, message_id))["action"] == "not_written"
    assert notes(d.db) == [] and tasks(d.db) == []


def test_a_second_press_after_a_write_that_was_not_forgotten_writes_nothing(d, monkeypatch) -> None:
    d.tg.handle_update(voice())
    data, message_id = dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)
    store = failing(d, monkeypatch, lambda state: not state.get("pending"))    # the entry cannot be removed
    assert d.tg.handle_update(press(data, message_id))["action"] == "noted"
    store["on"] = False
    assert d.tg.handle_update(press(data, message_id))["action"] == "inbound_gone"
    task = data.rsplit("|", 1)[0] + "|task"
    assert d.tg.handle_update(press(task, message_id))["action"] == "inbound_gone"
    assert len(notes(d.db)) == 1 and tasks(d.db) == []


def test_words_with_no_message_cannot_be_taken(d) -> None:
    key = reach_inbound._keep(d.tg, "words with no message", "text")
    for message_id in (None, 0, "None", sent_id(d.bot)):
        assert reach_inbound._claim(d.tg, key, message_id, "note") == (None, "gone")
    assert d.tg.handle_update(press(f"r1|in|{key}|note", sent_id(d.bot)))["action"] == "inbound_gone"
    assert notes(d.db) == []


def test_an_offer_that_cannot_be_bound_is_withdrawn_with_one_line(d, monkeypatch) -> None:
    store = failing(d, monkeypatch, lambda state: any(row.get("message_id") for row in state.get("pending", {}).values()))
    out = d.tg.handle_update(say("Remember to move the freeze to Friday"))
    assert out == {"action": "text_not_kept"}
    edited = d.bot.of("editMessageText")[-1]
    assert reach_inbound.NOT_KEPT_WORDS in edited["text"] and not (edited.get("reply_markup") or {}).get("inline_keyboard")
    store["on"] = False
    assert reach_inbound.waiting_count(d.tg) == 0
    assert "freeze" not in str(d.tg._policy(reach_inbound.INBOUND_POLICY))


# ── 5. the words that wait, at rest ──────────────────────────────────

def test_the_store_never_holds_more_than_twenty(d) -> None:
    for number in range(reach_inbound.PENDING_MAX + 5):
        d.tg.handle_update(say(f"Thought number {number} about the freeze"))
        assert len(d.tg._policy(reach_inbound.INBOUND_POLICY)["pending"]) <= reach_inbound.PENDING_MAX
    kept = " ".join(reach_inbound._memory(d.tg)[key] for key in d.tg._policy(reach_inbound.INBOUND_POLICY)["pending"])
    assert "number 24 " in kept and "number 0 " not in kept    # the oldest went
    assert len(reach_inbound._memory(d.tg)) == reach_inbound.PENDING_MAX, "the memory holds no more than the store"
    assert "number" not in str(d.tg._policy(reach_inbound.INBOUND_POLICY)), "no word is at rest"


def test_the_reach_tick_removes_words_that_are_a_day_old(d, monkeypatch) -> None:
    d.tg.handle_update(say("Remember to move the freeze to Friday"))
    assert len(d.tg._policy(reach_inbound.INBOUND_POLICY)["pending"]) == 1
    assert "freeze" in str(reach_inbound._memory(d.tg)) and "freeze" not in str(d.tg._policy(reach_inbound.INBOUND_POLICY))
    later = time.time() + reach_inbound.PENDING_SECONDS + 5
    monkeypatch.setattr(reach_inbound.time, "time", lambda: later)
    d.reach.tick()
    assert d.tg._policy(reach_inbound.INBOUND_POLICY) == {"pending": {}}
    assert reach_inbound._memory(d.tg) == {}


def not_cleared(d: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, bool]:
    d.tg.handle_update(say("Remember to move the freeze to Friday"))
    return failing(d, monkeypatch, lambda state: True)


def test_unpair_is_refused_when_the_words_cannot_be_cleared(d, monkeypatch) -> None:
    not_cleared(d, monkeypatch)
    with pytest.raises(TelegramRefused) as refused:
        d.tg.unpair(OWNER)
    assert refused.value.detail == "Your desk could not clear the words that wait. Nothing changed. Try again."
    assert telegram_reach.paired_chat() is not None            # nothing changed


def test_remove_is_refused_when_the_words_cannot_be_cleared(d, monkeypatch) -> None:
    not_cleared(d, monkeypatch)
    token = telegram_reach.bot_token()
    username = (d.tg._setup().get("bot") or {}).get("username")
    with pytest.raises(TelegramRefused) as refused:
        d.tg.remove_bot(OWNER, username)
    assert refused.value.code == "not_cleared"
    assert telegram_reach.bot_token() == token and telegram_reach.paired_chat() is not None


def test_a_new_token_is_refused_when_the_words_cannot_be_cleared(d, monkeypatch) -> None:
    store = not_cleared(d, monkeypatch)
    token = telegram_reach.bot_token()
    with pytest.raises(TelegramRefused) as refused:
        d.tg.save_token(OWNER, OTHER_TOKEN)
    assert refused.value.code == "not_cleared" and telegram_reach.bot_token() == token
    store["on"] = False
    d.tg.unpair(OWNER)                                         # a clear that works: the words are gone
    assert d.tg._policy(reach_inbound.INBOUND_POLICY) == {"pending": {}}
