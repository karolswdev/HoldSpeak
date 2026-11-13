"""What the owner sends to the bot becomes useful, and decides nothing.

A voice note is fetched, decoded and heard on this Mac, and offered back
with three buttons; words with no question are offered as a note or an Ask;
a photo or a file gets one line. Nothing is written until he presses, and a
press writes through the operation that owns the thing (``desk.create``,
``door.add_item``: the REAL ones, on this rig's database). Telegram is a
fake transport, the speech door and Ask are fakes, the decoder is a seam;
nothing here calls Telegram or a model.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services import reach_commands, reach_inbound
from holdspeak.services import telegram_reach
from tests.unit.test_reach_commands import Reads as CommandReads
from tests.unit.test_reach_commands import desk as command_desk
from tests.unit.test_reach_commands import say, texts
from tests.unit.test_reach_telegram import OWNER_CHAT, keystore  # noqa: F401
from tests.unit.test_reach_telegram_setup import OWNER, TOKEN

VOICE_PATH = "voice/file_7.oga"
HEARD = "Ask Dana for the cutover window. Then tell the team on Friday."


class Reads(CommandReads):
    """The hub's reads. The note and the task are the real operations
    (``reach_commands.Reads``); the speech door and Ask are said here."""

    note = reach_commands.Reads.note
    task = reach_commands.Reads.task

    def __init__(self) -> None:
        super().__init__()
        self.local: bool | None = True
        self.heard = HEARD
        self.heard_audio: list[Any] = []
        self.asked: list[str] = []
        # The shape of ``ask.run`` with ``tools: "none"`` (``ask_service``): the
        # answer and the record of what it was given.
        self.answer_of: dict[str, Any] | Exception = {
            "output": "Dana owns it.\nThe window is Friday 18:00.",
            "provenance": {"tools": "none", "refs": ["note:n1"], "complete": True}}

    def speech_local(self, principal: Any) -> bool | None:
        assert principal.kind is PrincipalKind.OWNER
        return self.local

    def transcribe(self, principal: Any, audio: Any) -> str:
        self.heard_audio.append(audio)
        return self.heard

    def ask(self, principal: Any, question: str) -> dict[str, Any]:
        self.asked.append(question)
        if isinstance(self.answer_of, Exception):
            raise self.answer_of
        return dict(self.answer_of)


@pytest.fixture
def d(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    made = command_desk(tmp_path)
    made.tg.reads = made.reads = Reads()
    composition.install(composition.bare(made.db, label="pytest"))
    made.bot.instead["getFile"] = {"ok": True, "result": {"file_id": "f7", "file_path": VOICE_PATH, "file_size": 2048}}
    made.fetched = []
    made.tg.fetch_file = lambda path: made.fetched.append(path) or b"OggS-not-real-audio"
    made.decoded = []
    monkeypatch.setattr(reach_inbound, "can_decode", lambda: True)

    made.tg.inbound_inline = True            # the worker's job runs where it is asked

    def decode(data: bytes) -> Any:
        made.decoded.append(data)
        return [0.0] * 16
    monkeypatch.setattr(reach_inbound, "_decode_bytes", decode)
    made.link = "https://desk.example/"
    made.tg._link = lambda path: made.link
    yield made
    composition.install(composition.bare(label="pytest"))


def voice(duration: int = 12, size: int = 2048, sender: Any = OWNER_CHAT, chat: Any = OWNER_CHAT,
          extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"update_id": 910, "message": {
        "message_id": 9, "chat": {"id": chat, "type": "private"}, "date": 1794581000,
        "from": {"id": sender, "first_name": "K"},
        "voice": {"file_id": "f7", "duration": duration, "mime_type": "audio/ogg", "file_size": size},
        **(extra or {})}}


def buttons(bot: Any, index: int = -1) -> list[tuple[str, str]]:
    rows = (bot.of("sendMessage")[index].get("reply_markup") or {}).get("inline_keyboard") or []
    return [(button["text"], button.get("callback_data", "")) for row in rows for button in row]


def press(data: str, message_id: int, sender: Any = OWNER_CHAT) -> dict[str, Any]:
    return {"update_id": 911, "callback_query": {"id": "cb9", "data": data, "from": {"id": sender}, "message": {
        "message_id": message_id, "chat": {"id": OWNER_CHAT, "type": "private"}, "text": ""}}}


def notes(db: Any) -> list[dict[str, Any]]:
    from holdspeak.mcp.tools import dispatch

    return [row for row in dispatch("desk.list", {"kind": "notes"}, OWNER) if not row.get("deleted")]


def tasks(db: Any) -> list[str]:
    with db._connection() as conn:
        return [str(row[0]) for row in conn.execute("SELECT task FROM action_items").fetchall()]


def sent_id(bot: Any) -> int:
    return bot.next_id


# ── 1. a voice note ──────────────────────────────────────────────────

def test_a_voice_note_gives_the_words_and_three_buttons_and_writes_nothing(d) -> None:
    out = d.tg.handle_update(voice())
    assert out["action"] == "heard"
    said = texts(d.bot)[-1]
    assert "I heard" in said and "Ask Dana for the cutover window." in said
    assert [words for words, _data in buttons(d.bot)] == ["Keep as a note", "Make it a task", "Discard"]
    assert all(data.startswith("r1|in|") and len(data.encode()) <= 64 for _words, data in buttons(d.bot))
    assert notes(d.db) == [] and tasks(d.db) == []           # nothing is written until he presses
    assert d.bot.of("getFile") == [{"file_id": "f7"}] and d.fetched == [VOICE_PATH]
    assert len(d.reads.heard_audio) == 1


def test_the_audio_is_in_no_file_and_the_token_is_in_no_log_line(d, caplog, tmp_path, monkeypatch) -> None:
    import tempfile

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))
    with caplog.at_level(logging.DEBUG):
        d.tg.handle_update(voice())
    assert d.decoded == [b"OggS-not-real-audio"]             # the decoder gets the bytes on a pipe
    assert os.listdir(scratch) == []                         # and the audio is in no file, at any time
    assert TOKEN not in caplog.text
    kept = d.tg._policy(reach_inbound.INBOUND_POLICY)
    assert TOKEN not in str(kept) and VOICE_PATH not in str(kept) and "api.telegram.org" not in str(kept)


def test_the_real_fetch_says_no_token_when_it_fails(monkeypatch, caplog) -> None:
    def refuse(**kwargs: Any) -> Any:
        raise OSError(f"could not open {kwargs['args'][0].full_url}")
    monkeypatch.setattr("holdspeak.kernel.external_egress.run_external_egress", refuse)
    with caplog.at_level(logging.DEBUG), pytest.raises(reach_inbound.VoiceRefused) as caught:
        reach_inbound.fetch_file(TOKEN, VOICE_PATH)
    assert TOKEN not in caplog.text and TOKEN not in str(caught.value) and TOKEN not in caught.value.words
    assert caught.value.__cause__ is None                    # the error that holds the URL is not carried on


def test_the_fetch_is_an_egress_record_with_no_content(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    class Answer:
        def __enter__(self) -> "Answer":
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def read(self, size: int) -> bytes:
            return b"audio"

    def egress(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return Answer()
    monkeypatch.setattr("holdspeak.kernel.external_egress.run_external_egress", egress)
    assert reach_inbound.fetch_file(TOKEN, VOICE_PATH) == b"audio"
    assert seen["connector_id"] == telegram_reach.CONNECTOR and seen["data_classes"] == ("reach_voice_fetch",)
    assert TOKEN not in str(seen["payload_material"]) and TOKEN not in seen["destination"]
    assert VOICE_PATH not in str(seen["payload_material"])


def test_keep_as_a_note_makes_one_note_through_the_note_operation(d) -> None:
    d.tg.handle_update(voice())
    key_data = dict(buttons(d.bot))["Keep as a note"]
    out = d.tg.handle_update(press(key_data, sent_id(d.bot)))
    assert out["action"] == "noted"
    (note,) = notes(d.db)
    assert note["body_markdown"] == HEARD and note["title"] == "Ask Dana for the cutover window."
    assert "Kept as a note on your desk" in d.bot.of("editMessageText")[-1]["text"]
    # The same press again writes nothing more: the words are gone.
    assert d.tg.handle_update(press(key_data, sent_id(d.bot)))["action"] == "inbound_gone"
    assert len(notes(d.db)) == 1


def test_make_it_a_task_makes_one_task_through_the_task_operation(d) -> None:
    d.tg.handle_update(voice())
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Make it a task"], sent_id(d.bot)))
    assert out["action"] == "tasked"
    assert tasks(d.db) == ["Ask Dana for the cutover window"] and notes(d.db) == []
    assert "Added as a task: Ask Dana for the cutover window" in d.bot.of("editMessageText")[-1]["text"]


def test_discard_forgets_the_words(d) -> None:
    d.tg.handle_update(voice())
    assert d.tg.handle_update(press(dict(buttons(d.bot))["Discard"], sent_id(d.bot)))["action"] == "discarded"
    assert reach_inbound.waiting_count(d.tg) == 0 and notes(d.db) == [] and tasks(d.db) == []
    assert HEARD not in str(d.tg._policy(reach_inbound.INBOUND_POLICY))


def test_a_remote_speech_engine_refuses_and_fetches_nothing(d) -> None:
    d.reads.local = False
    out = d.tg.handle_update(voice())
    assert out["action"] == "voice_refused"
    assert texts(d.bot)[-1] == "Your speech engine is not on this Mac. Voice notes need a local one."
    assert d.bot.of("getFile") == [] and d.fetched == [] and d.reads.heard_audio == []
    assert reach_inbound.waiting_count(d.tg) == 0


def test_no_speech_engine_and_no_decoder_each_say_why(d, monkeypatch) -> None:
    d.reads.local = None
    d.tg.handle_update(voice())
    assert "No speech engine is set" in texts(d.bot)[-1]
    d.reads.local = True
    monkeypatch.setattr(reach_inbound, "can_decode", lambda: False)
    d.tg.handle_update(voice())
    assert "ffmpeg is not installed" in texts(d.bot)[-1] and d.fetched == []


def test_a_six_minute_voice_note_and_a_large_one_are_refused(d) -> None:
    assert d.tg.handle_update(voice(duration=360))["action"] == "voice_refused"
    assert "longer than five minutes" in texts(d.bot)[-1]
    assert d.tg.handle_update(voice(size=21 * 1024 * 1024))["action"] == "voice_refused"
    assert "too large" in texts(d.bot)[-1]
    assert d.fetched == [] and reach_inbound.waiting_count(d.tg) == 0


def test_a_button_of_the_pairing_before_keeps_nothing(d) -> None:
    d.tg.handle_update(voice())
    data = dict(buttons(d.bot))["Keep as a note"]
    message_id = sent_id(d.bot)
    d.tg._new_generation()                                   # a new pairing
    assert d.tg.handle_update(press(data, message_id))["action"] == "inbound_gone"
    assert notes(d.db) == [] and HEARD not in str(d.tg._policy(reach_inbound.INBOUND_POLICY))


def test_a_press_on_another_message_keeps_nothing(d) -> None:
    d.tg.handle_update(voice())
    data = dict(buttons(d.bot))["Keep as a note"]
    assert d.tg.handle_update(press(data, sent_id(d.bot) + 50))["action"] == "inbound_gone"
    assert notes(d.db) == []


def test_words_wait_at_most_a_day(d, monkeypatch) -> None:
    d.tg.handle_update(voice())
    data = dict(buttons(d.bot))["Keep as a note"]
    import time as real_time

    later = real_time.time() + reach_inbound.PENDING_SECONDS + 5
    monkeypatch.setattr(reach_inbound.time, "time", lambda: later)
    assert d.tg.handle_update(press(data, sent_id(d.bot)))["action"] == "inbound_gone"
    assert notes(d.db) == []


def test_another_user_gets_nothing(d) -> None:
    before = len(d.bot.calls)
    assert d.tg.handle_update(voice(sender=4242))["action"] == "ignored"          # another user in his chat
    assert d.tg.handle_update(voice(sender=4242, chat=4242))["action"] == "ignored"  # another chat
    assert len(d.bot.calls) == before and d.fetched == []
    d.tg.handle_update(voice())
    data = dict(buttons(d.bot))["Keep as a note"]
    assert d.tg.handle_update(press(data, sent_id(d.bot), sender=4242))["action"] == "rejected"
    assert notes(d.db) == []


def test_the_words_are_never_in_the_summary_view_or_a_log_line(d, caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        d.tg.handle_update(voice())
    assert "cutover" not in caplog.text
    assert "cutover" not in str(d.tg.summary()) and "cutover" not in str(d.tg.status())


# ── 2. words that answer nothing ─────────────────────────────────────

def test_plain_words_get_two_buttons_and_decide_nothing(d) -> None:
    out = d.tg.handle_update(say("Remember to move the freeze to Friday"))
    assert out["action"] == "thought"
    assert "Remember to move the freeze to Friday" in texts(d.bot)[-1]
    assert [words for words, _data in buttons(d.bot)] == ["Keep as a note", "Ask my desk"]
    assert notes(d.db) == [] and d.reads.asked == []
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)))
    assert out["action"] == "noted"
    (note,) = notes(d.db)
    assert note["body_markdown"] == "Remember to move the freeze to Friday"


def test_a_bare_yes_still_gets_the_how_to_answer_line(d) -> None:
    for word in ("yes", "Yes.", "ok", "no", "later", "not now"):
        out = d.tg.handle_update(say(word))
        assert out["action"] == "no_package"
        assert texts(d.bot)[-1] == telegram_reach.NO_TARGET_WORDS
        assert buttons(d.bot) == []
    assert reach_inbound.waiting_count(d.tg) == 0


def test_ask_my_desk_sends_the_answer_back(d) -> None:
    d.tg.handle_update(say("Who owns the cutover window?"))
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Ask my desk"], sent_id(d.bot)))
    assert out == {"action": "asked", "on_desk": False}
    assert d.reads.asked == ["Who owns the cutover window?"]
    answer = d.bot.of("sendMessage")[-1]
    assert "Dana owns it." in answer["text"] and "Friday 18:00" in answer["text"]
    urls = [b.get("url") for row in (answer.get("reply_markup") or {}).get("inline_keyboard", []) for b in row]
    assert urls == [d.link] and "token" not in d.link


def test_an_answer_made_from_people_content_stays_on_the_desk(d) -> None:
    d.reads.answer_of = {"output": "Dana said she is unhappy with her role.",
                         "provenance": {"tools": "none", "refs": ["person:p1"], "complete": True}}
    d.tg.handle_update(say("What did Dana tell me?"))
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Ask my desk"], sent_id(d.bot)))
    assert out == {"action": "asked", "on_desk": True}
    said = d.bot.of("sendMessage")[-1]["text"]
    assert "The answer is on your desk." in said and "unhappy" not in said


def test_ask_with_no_engine_says_so(d) -> None:
    from holdspeak.services.errors import ServiceError

    d.reads.answer_of = ServiceError("no_engine", "No engine is assigned to ask.answer.")
    d.tg.handle_update(say("Who owns the cutover window?"))
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Ask my desk"], sent_id(d.bot)))
    assert out == {"action": "ask_failed", "no_engine": True}
    assert texts(d.bot)[-1] == "No engine is set for Ask on your desk. Set one in Settings."


def test_a_voice_note_cannot_be_asked(d) -> None:
    d.tg.handle_update(voice())
    data = dict(buttons(d.bot))["Keep as a note"].rsplit("|", 1)[0] + "|ask"
    assert d.tg.handle_update(press(data, sent_id(d.bot)))["action"] == "inbound_gone"
    assert d.reads.asked == []


# ── 3. a photo or a file ─────────────────────────────────────────────

@pytest.mark.parametrize("field,value", [
    ("photo", [{"file_id": "p1", "width": 90, "height": 90}]),
    ("document", {"file_id": "d1", "file_name": "plan.pdf"}),
    ("video", {"file_id": "v1", "duration": 3}),
])
def test_a_photo_or_a_file_gets_one_line_and_is_not_fetched(d, field: str, value: Any) -> None:
    update = voice()
    del update["message"]["voice"]
    update["message"][field] = value
    update["message"]["caption"] = "the plan"
    assert d.tg.handle_update(update)["action"] == "media_refused"
    assert texts(d.bot)[-1] == "I cannot keep photos or files yet. Send words or a voice note."
    assert d.bot.of("getFile") == [] and d.fetched == [] and reach_inbound.waiting_count(d.tg) == 0


# ── 4. /help ─────────────────────────────────────────────────────────

def test_help_lists_what_he_can_send(d) -> None:
    d.tg.handle_update(say("/help"))
    said = texts(d.bot)[-1]
    assert "A voice note" in said and "Words with no question" in said and "Photos and files" in said


# ── the default reads ────────────────────────────────────────────────

def test_the_speech_engine_is_local_only_when_every_engine_of_the_chain_is(monkeypatch) -> None:
    from types import SimpleNamespace

    chain: list[dict[str, Any]] = []
    assignments = SimpleNamespace(resolve_effective=lambda principal, capability_id: (
        {"assignment": {"entries": list(chain)}} if capability_id == "speech.transcribe" else {}))
    root = SimpleNamespace(web_context=SimpleNamespace(inference_assignment_service=assignments))
    monkeypatch.setattr("holdspeak.runtime.composition.current", lambda: root)
    reads = reach_commands.Reads()
    assert reads.speech_local(OWNER) is None
    chain[:] = [{"boundary": "local"}, {"boundary": "same_device"}]
    assert reads.speech_local(OWNER) is True
    chain.append({"boundary": "lan"})
    assert reads.speech_local(OWNER) is False


def test_the_transcription_goes_through_the_speech_door_and_closes_its_admission(monkeypatch) -> None:
    from types import SimpleNamespace

    closed: list[str] = []
    asked: list[dict[str, Any]] = []

    def admitted(audio: Any, **kwargs: Any) -> Any:
        asked.append(kwargs)
        return SimpleNamespace(text="the words", provider=SimpleNamespace(egress_boundary=boundary[0]),
                               close=closed.append)
    boundary = ["local"]
    root = SimpleNamespace(web_context=SimpleNamespace(on_transcribe_admitted=admitted))
    monkeypatch.setattr("holdspeak.runtime.composition.current", lambda: root)
    assert reach_commands.Reads().transcribe(OWNER, [0.0]) == "the words"
    assert closed == ["succeeded"] and asked[0]["verbatim"] is True and asked[0]["principal"] is OWNER
    boundary[0] = "cloud"
    with pytest.raises(RuntimeError):
        reach_commands.Reads().transcribe(OWNER, [0.0])
    assert closed[-1] == "failed"
