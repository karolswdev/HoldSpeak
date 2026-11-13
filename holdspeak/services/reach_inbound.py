"""What the owner SENDS to the bot: a voice note, a thought in words, a
photo or a file.

A voice note is fetched from Telegram through the one transport, decoded and
transcribed ON THIS MAC by his speech engine, and answered with the words
and three buttons. Words with no question become a note or an Ask. Nothing
is written until he presses: the words wait at most a day in the reach
store (the cadence policy row ``reach_telegram_inbound``), bound to the
pairing generation and to the message their buttons are on.

Every write goes through an operation that exists (``desk.create``,
``door.add_item``, ``ask.run``) and the speech door's admitted transcription
(``on_transcribe_admitted``); this module has no note, task, Ask or
transcription code of its own. They are reached through
:class:`reach_commands.Reads`, so a test gives its own.

The bot token: the file URL holds it (``/file/bot<token>/<path>``). It is
joined into the URL in ``telegram_reach.file_request`` only (the one module
that names the Bot API) and used in :func:`fetch_file`; it is never stored, never
logged and never put in an error text.
"""
from __future__ import annotations

import os
import secrets
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Mapping, Optional

from ..logging_config import get_logger
from .errors import ServiceError
from .telegram_writer import Button, Message

log = get_logger("services.reach_inbound")

INBOUND_POLICY = "reach_telegram_inbound"   # the cadence policy row: words that wait for his press
PENDING_SECONDS = 24 * 3600                 # words wait at most a day
PENDING_MAX = 20                            # more than this: the oldest go
VOICE_MAX_SECONDS = 5 * 60
VOICE_MAX_BYTES = 20 * 1024 * 1024          # Telegram's download limit for a bot
SHOWN_CHARS = 1200                          # the words shown in the chat; all of them wait
QUOTE_CHARS = 120                           # the first words, quoted back
TASK_CHARS = 240                            # a task's words (``door.add_item`` has a title and no detail)
CALLBACK = "r1"                             # the one button-data scheme (telegram_reach.CALLBACK)
FILE_TIMEOUT = 30.0
_LOCAL = frozenset({"local", "same_device"})
#: A reference of these kinds is People content (``thread_service._PEOPLE_REF_KINDS``
#: and the People custody boundary of ``needs_you_membership.withhold_people_content``).
_PEOPLE_REF_KINDS = frozenset({"person", "people", "relationship", "one_on_one", "people_commitment",
                               "people_note", "commitment"})

HEARD_HEAD = "I heard"
VOICE_TOO_LONG_WORDS = "This voice note is longer than five minutes. Nothing was kept. Send a shorter one."
VOICE_TOO_LARGE_WORDS = "This voice note is too large to fetch. Nothing was kept. Send a shorter one."
VOICE_REMOTE_WORDS = "Your speech engine is not on this Mac. Voice notes need a local one."
VOICE_NO_ENGINE_WORDS = "No speech engine is set on your desk. Nothing was kept. Set one in Settings, then send it again."
VOICE_NO_DECODER_WORDS = "This Mac cannot read a Telegram voice note: ffmpeg is not installed. Nothing was kept."
VOICE_NOT_FETCHED_WORDS = "Your desk could not fetch this voice note. Nothing was kept. Send it again."
VOICE_NOT_READ_WORDS = "Your desk could not read this voice note. Nothing was kept. Send it again."
VOICE_NO_WORDS = "I heard no words. Nothing was kept."
VOICE_NOT_SHOWN_WORDS = "The words hold something that is never sent to Telegram. Nothing was kept."
MEDIA_WORDS = "I cannot keep photos or files yet. Send words or a voice note."
GONE_WORDS = "These words are gone. Nothing was kept. Send them again."
NOTE_WORDS = "Kept as a note on your desk."
TASK_WORDS = "Added as a task."
DISCARD_WORDS = "Discarded. Nothing was kept."
NOT_WRITTEN_WORDS = "Your desk could not keep this now. Nothing changed. Press again."
ASKING_WORDS = "Asking your desk."
ASK_NO_ENGINE_WORDS = "No engine is set for Ask on your desk. Set one in Settings."
ASK_FAILED_WORDS = "Your desk could not answer now. Nothing changed. Ask again."
ASK_ON_DESK_WORDS = "The answer is on your desk."
THOUGHT_QUESTION = "Keep it, or ask your desk?"
QUESTION_WAITS_WORDS = "A question waits. To answer it, reply to it or press its button."
HELP_LINES = (
    "A voice note: I write the words I hear. You keep them as a note or a task.",
    "Words with no question: you keep them as a note, or ask your desk.",
    "Photos and files: I cannot keep them yet.",
)


class VoiceRefused(Exception):
    """A voice note that is not read; ``words`` is the one line he gets."""

    def __init__(self, words: str) -> None:
        super().__init__(words)
        self.words = words


# ── the file, from Telegram to this Mac ──────────────────────────────


def fetch_file(token: str, path: str, *, timeout: float = FILE_TIMEOUT) -> bytes:
    """The bytes of one file the bot was sent, through ``run_external_egress``
    (connector ``reach-telegram``, data class ``reach_voice_fetch``). The
    record holds the destination and no content. Raises :class:`VoiceRefused`
    with a line that holds no token."""
    from ..kernel.external_egress import run_external_egress
    from .telegram_reach import CONNECTOR, file_request

    request = file_request(token, path)
    destination = "telegram:file:bot"
    try:
        response = run_external_egress(
            connector_id=CONNECTOR, destination=destination, data_classes=("reach_voice_fetch",),
            payload_material={"method": "file"}, sender=urllib.request.urlopen, args=(request,),
            kwargs={"timeout": timeout}, allowed_destinations=(destination,),
        )
        with response:
            data = response.read(VOICE_MAX_BYTES + 1)
    except Exception as exc:
        # The exception's text can hold the URL, and the URL holds the token:
        # only the exception's TYPE is said.
        log.warning(f"telegram: a voice note was not fetched ({type(exc).__name__})")
        raise VoiceRefused(VOICE_NOT_FETCHED_WORDS) from None
    if len(data) > VOICE_MAX_BYTES:
        raise VoiceRefused(VOICE_TOO_LARGE_WORDS)
    return data


def can_decode() -> bool:
    """Telegram's voice format (OGG with Opus) is read through ``ffmpeg``,
    as every compressed meeting import is (``meeting_import.FFMPEG_SUFFIXES``)."""
    from ..meeting_import import ffmpeg_available

    return ffmpeg_available()


def _decode_path(path: str) -> Any:
    from pathlib import Path

    from ..meeting_import import load_audio

    audio, _rate = load_audio(Path(path))
    return audio


def decode_voice(data: bytes) -> Any:
    """The audio as the speech engine takes it (16 kHz mono floats). The
    bytes stand in one temp file for the decoder and the file is removed
    before this returns, whatever happened."""
    handle, path = tempfile.mkstemp(prefix="holdspeak-voice-", suffix=".oga")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        return _decode_path(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ── the words that wait ──────────────────────────────────────────────


def _state(tg: Any) -> dict[str, Any]:
    state = tg._policy(INBOUND_POLICY)
    pending = state.get("pending")
    return {"pending": dict(pending) if isinstance(pending, dict) else {}}


def _pruned(tg: Any, state: dict[str, Any]) -> dict[str, Any]:
    now = time.time()
    generation = tg._generation()
    kept = {key: row for key, row in state["pending"].items()
            if isinstance(row, dict) and row.get("gen") == generation
            and now - float(row.get("at") or 0) < PENDING_SECONDS}
    for key in sorted(kept, key=lambda k: float(kept[k].get("at") or 0))[:max(0, len(kept) - PENDING_MAX)]:
        kept.pop(key, None)      # more than the store holds: the oldest go
    state["pending"] = kept
    return state


def _keep(tg: Any, words: str, kind: str) -> Optional[str]:
    """Words that wait for his press, under a new random key; None when the
    store could not be written (then nothing is offered)."""
    state = _pruned(tg, _state(tg))
    key = secrets.token_urlsafe(12)
    while key in state["pending"]:
        key = secrets.token_urlsafe(12)
    state["pending"][key] = {"words": words, "kind": kind, "gen": tg._generation(),
                             "message_id": None, "at": time.time()}
    return key if tg._save_policy(INBOUND_POLICY, state) else None


def _bind(tg: Any, key: str, result: Optional[Mapping[str, Any]]) -> None:
    message_id = ((result or {}).get("result") or {}).get("message_id")
    state = _state(tg)
    row = state["pending"].get(key)
    if row is None:
        return
    if not (result or {}).get("ok", False):
        state["pending"].pop(key, None)      # the offer was not sent: nothing waits
    elif message_id is not None:
        row["message_id"] = message_id
    tg._save_policy(INBOUND_POLICY, state)


def _take(tg: Any, key: str, message_id: Any, *, forget: bool) -> Optional[dict[str, Any]]:
    """The words of ``key`` when the press is on their own message, in this
    pairing, within a day; else None. ``forget`` removes them."""
    state = _pruned(tg, _state(tg))
    row = state["pending"].get(key)
    if row is None or (row.get("message_id") is not None and str(row["message_id"]) != str(message_id)):
        tg._save_policy(INBOUND_POLICY, state)
        return None
    if forget:
        state["pending"].pop(key, None)
    tg._save_policy(INBOUND_POLICY, state)
    return dict(row)


def forget_all(tg: Any) -> None:
    """A new pairing: no words of the pairing before wait (they were his;
    the chat is another)."""
    tg._save_policy(INBOUND_POLICY, {"pending": {}})


def waiting_count(tg: Any) -> int:
    return len(_pruned(tg, _state(tg))["pending"])


# ── words ────────────────────────────────────────────────────────────


def cut_words(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0] or text[:limit]
    return cut + "…"


def note_title(words: str) -> str:
    return cut_words(first_sentence(words), 80)


def first_sentence(words: str) -> str:
    text = " ".join(str(words).split())
    for index, char in enumerate(text):
        if char in ".!?" and (index + 1 == len(text) or text[index + 1] == " "):
            return text[: index + 1]
    return text


def task_words(words: str) -> str:
    return cut_words(first_sentence(words), TASK_CHARS).rstrip(".")


def _button(key: str, act: str, words: str) -> Button:
    return Button(words, f"{CALLBACK}|in|{key}|{act}")


def heard_message(words: str, key: str) -> Message:
    count = len(words.split())
    shown = cut_words(words, SHOWN_CHARS)
    closing = (f"{count} words. All of them wait for your press.",) if shown != " ".join(words.split()) else ()
    return Message(head=HEARD_HEAD, lines=(shown,), closing=closing, buttons=(
        (_button(key, "note", "Keep as a note"), _button(key, "task", "Make it a task")),
        (_button(key, "drop", "Discard"),),
    ))


def thought_message(words: str, key: str, *, question_waits: bool = False) -> Message:
    closing = (QUESTION_WAITS_WORDS,) if question_waits else ()
    return Message(lines=(f"“{cut_words(words, QUOTE_CHARS)}”",), question=THOUGHT_QUESTION, closing=closing, buttons=(
        (_button(key, "note", "Keep as a note"), _button(key, "ask", "Ask my desk")),
    ))


def done_message(words: str, outcome: str, clock: str, *, open_url: Optional[str] = None) -> Message:
    return Message(lines=(f"“{cut_words(words, QUOTE_CHARS)}”", f"{outcome} · {clock}"), open_url=open_url)


def carries_people(result: Mapping[str, Any]) -> bool:
    """True when the Ask answer was made from People content: a thing it
    looked at is of a People kind. Such an answer stays on the desk (the
    rule of ``needs_you_membership.withhold_people_content``: People content
    does not leave in a notification)."""
    for row in result.get("looked_at") or []:
        ref = str((row or {}).get("ref") or "") if isinstance(row, Mapping) else ""
        if ref.split(":", 1)[0].lower() in _PEOPLE_REF_KINDS:
            return True
    return False


def answer_message(question: str, result: Mapping[str, Any], open_url: Optional[str]) -> Message:
    text = str(result.get("output") or "").strip()
    if not text:
        return Message(lines=(ASK_FAILED_WORDS,))
    if carries_people(result):
        return Message(head=cut_words(question, QUOTE_CHARS), lines=(ASK_ON_DESK_WORDS,), open_url=open_url,
                       desk_words="Open it on your desk.")
    lines = tuple(line for line in (part.strip() for part in text.splitlines()) if line)
    return Message(head=cut_words(question, QUOTE_CHARS), lines=lines, open_url=open_url)


# ── what he sent ─────────────────────────────────────────────────────

MEDIA_KEYS = ("photo", "document", "video", "audio", "animation", "sticker", "video_note", "contact",
              "location", "poll")


def kind_of(message: Mapping[str, Any]) -> Optional[str]:
    """``voice``, ``media`` or None (a message of words, or nothing we read)."""
    if isinstance(message.get("voice"), Mapping):
        return "voice"
    if any(message.get(key) for key in MEDIA_KEYS):
        return "media"
    return None


def media(tg: Any, chat_id: str) -> dict[str, Any]:
    tg._send(chat_id, MEDIA_WORDS, data_class="reach_answer")
    return {"action": "media_refused"}


def _fetch(tg: Any, path: str) -> bytes:
    fetcher = getattr(tg, "fetch_file", None)
    if fetcher is not None:
        return bytes(fetcher(path))
    from .telegram_reach import bot_token

    return fetch_file(bot_token(), path)


def _words_of(tg: Any, voice: Mapping[str, Any]) -> str:
    """The words of one voice note, heard on this Mac; raises
    :class:`VoiceRefused` with the one line he gets."""
    from .telegram_reach import TELEGRAM_OWNER

    if int(voice.get("duration") or 0) > VOICE_MAX_SECONDS:
        raise VoiceRefused(VOICE_TOO_LONG_WORDS)
    if int(voice.get("file_size") or 0) > VOICE_MAX_BYTES:
        raise VoiceRefused(VOICE_TOO_LARGE_WORDS)
    reads = tg._reads()
    try:
        local = reads.speech_local(TELEGRAM_OWNER)
    except Exception as exc:
        log.info(f"telegram: the speech engine was not read ({type(exc).__name__})")
        local = None
    if local is None:
        raise VoiceRefused(VOICE_NO_ENGINE_WORDS)
    if not local:
        # The audio would leave this Mac a second time: it is not fetched.
        raise VoiceRefused(VOICE_REMOTE_WORDS)
    if not can_decode():
        raise VoiceRefused(VOICE_NO_DECODER_WORDS)
    told = tg._api("getFile", {"file_id": str(voice.get("file_id") or "")}, data_class="reach_voice_fetch")
    info = told.get("result") if isinstance(told.get("result"), Mapping) else {}
    path = str(info.get("file_path") or "")
    if not told.get("ok") or not path:
        raise VoiceRefused(VOICE_NOT_FETCHED_WORDS)
    if int(info.get("file_size") or 0) > VOICE_MAX_BYTES:
        raise VoiceRefused(VOICE_TOO_LARGE_WORDS)
    data = _fetch(tg, path)
    if len(data) > VOICE_MAX_BYTES:
        raise VoiceRefused(VOICE_TOO_LARGE_WORDS)
    try:
        audio = decode_voice(data)
        del data
        words = str(reads.transcribe(TELEGRAM_OWNER, audio) or "")
    except VoiceRefused:
        raise
    except Exception as exc:
        log.info(f"telegram: a voice note was not read ({type(exc).__name__})")
        raise VoiceRefused(VOICE_NOT_READ_WORDS) from None
    words = " ".join(words.split())
    if not words:
        raise VoiceRefused(VOICE_NO_WORDS)
    return words


def voice(tg: Any, chat_id: str, message: Mapping[str, Any]) -> dict[str, Any]:
    """A voice note from the owner (he sent it: a note he forwards from
    another person is his send, and is read as his)."""
    try:
        words = _words_of(tg, dict(message.get("voice") or {}))
    except VoiceRefused as refused:
        tg._send(chat_id, refused.words, data_class="reach_answer")
        return {"action": "voice_refused", "words": refused.words}
    return _offer(tg, chat_id, words, "voice")


def thought(tg: Any, chat_id: str, text: str, *, question_waits: bool = False) -> dict[str, Any]:
    """Words that answer nothing: offered back, deciding nothing."""
    return _offer(tg, chat_id, " ".join(text.split()), "text", question_waits=question_waits)


def _offer(tg: Any, chat_id: str, words: str, kind: str, *, question_waits: bool = False) -> dict[str, Any]:
    from .telegram_reach import TelegramRefused

    key = _keep(tg, words, kind)
    if key is None:
        tg._send(chat_id, NOT_WRITTEN_WORDS.replace(" Press again.", " Send it again."), data_class="reach_answer")
        return {"action": f"{kind}_not_kept"}
    made = heard_message(words, key) if kind == "voice" else thought_message(words, key, question_waits=question_waits)
    try:
        result = tg._send(chat_id, made, data_class="reach_answer")
    except TelegramRefused:
        _take(tg, key, None, forget=True)
        tg._send(chat_id, VOICE_NOT_SHOWN_WORDS, data_class="reach_answer")
        return {"action": f"{kind}_not_shown"}
    _bind(tg, key, result)
    return {"action": "heard" if kind == "voice" else "thought", "key": key}


def tap(tg: Any, chat_id: str, callback_id: str, message: Mapping[str, Any], key: str, act: str) -> dict[str, Any]:
    """His press under words he sent. Only here is a thing written, through
    the operation that owns it."""
    from .telegram_reach import TELEGRAM_OWNER, TelegramRefused, _clock

    message_id = message.get("message_id")
    if act not in ("note", "task", "drop", "ask"):
        tg._ack(callback_id)
        return {"action": "ignored"}
    row = _take(tg, key, message_id, forget=act == "drop")
    if row is None or (act == "ask" and row.get("kind") != "text"):
        tg._ack(callback_id, GONE_WORDS)
        return {"action": "inbound_gone"}
    words = str(row.get("words") or "")
    reads = tg._reads()
    clock = _clock(tg._stamp())
    open_url = tg.link_for("/")
    if act == "drop":
        tg._ack(callback_id, "Discarded.")
        tg._edit(chat_id, message_id, Message(lines=(DISCARD_WORDS,)))
        return {"action": "discarded"}
    if act == "ask":
        tg._ack(callback_id, ASKING_WORDS)
        _take(tg, key, message_id, forget=True)
        tg._edit(chat_id, message_id, done_message(words, ASKING_WORDS.rstrip("."), clock))
        try:
            result = dict(reads.ask(TELEGRAM_OWNER, words) or {})
        except Exception as exc:
            log.info(f"telegram: ask did not answer ({type(exc).__name__})")
            code = f"{getattr(exc, 'code', '')} {getattr(exc, 'detail', '')}".lower()
            none_set = any(mark in code for mark in ("engine", "assignment", "no_target", "not_configured", "model"))
            tg._send(chat_id, ASK_NO_ENGINE_WORDS if none_set else ASK_FAILED_WORDS, data_class="reach_answer")
            return {"action": "ask_failed", "no_engine": none_set}
        made = answer_message(words, result, open_url)
        try:
            tg._send(chat_id, made, data_class="reach_answer")
        except TelegramRefused:
            tg._send(chat_id, Message(lines=(ASK_ON_DESK_WORDS,), open_url=open_url,
                                      desk_words="Open it on your desk."), data_class="reach_answer")
            return {"action": "asked", "on_desk": True}
        return {"action": "asked", "on_desk": carries_people(result)}
    try:
        if act == "note":
            reads.note(TELEGRAM_OWNER, words)
        else:
            reads.task(TELEGRAM_OWNER, task_words(words))
    except Exception as exc:
        detail = exc.detail if isinstance(exc, ServiceError) else ""
        log.info(f"telegram: words were not kept ({type(exc).__name__})")
        tg._ack(callback_id, cut_words(detail or NOT_WRITTEN_WORDS, 180))
        return {"action": "not_written"}
    _take(tg, key, message_id, forget=True)
    outcome = NOTE_WORDS.rstrip(".") if act == "note" else f"{TASK_WORDS.rstrip('.')}: {task_words(words)}"
    tg._ack(callback_id, NOTE_WORDS if act == "note" else TASK_WORDS)
    tg._edit(chat_id, message_id, done_message(words, outcome, clock, open_url=open_url))
    return {"action": "noted" if act == "note" else "tasked"}
