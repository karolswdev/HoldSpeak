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

import queue
import secrets
import subprocess
import threading
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
# Review T4: what a voice note may cost, whatever Telegram says about it.
PCM_BYTES_A_SECOND = 32_000                 # 16 kHz, one channel, 16 bits: what the decoder writes
DECODE_SECONDS = 60.0                       # the decoder's wall clock
VOICE_JOB_SECONDS = 180.0                   # fetch, decode and hear, end to end
ASK_JOB_SECONDS = 120.0                     # one Ask, end to end
WORKER_QUEUE = 3                            # jobs that wait behind the one that runs
WORKER_LATE = 2                             # abandoned jobs that may still hold a thread
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
BUSY_WORDS = "Your desk is busy. Send it again in a minute."
VOICE_SLOW_WORDS = "Your desk did not read this voice note in three minutes. Nothing was kept. Send it again."
ASK_SLOW_WORDS = "Your desk did not answer in two minutes. Nothing changed. Ask again."
NOT_KEPT_WORDS = "Your desk could not keep this now. Nothing changed. Send it again."
CLEAR_FAILED_WORDS = "Your desk could not clear the words that wait. Nothing changed. Try again."
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


def _decode_bytes(data: bytes) -> Any:
    """16 kHz mono floats from the bytes of one voice note, through
    ``ffmpeg`` on a pipe. Review T4:

    - the audio goes in on stdin and no file is made, so a kill leaves
      nothing behind;
    - the DECODED amount is what counts, not the length Telegram said: the
      decoder is told to stop a second after :data:`VOICE_MAX_SECONDS`, this
      reader stops it at that many bytes, and a clip that is longer is
      refused (:class:`VoiceRefused`);
    - the wall clock is :data:`DECODE_SECONDS`.

    The arguments are fixed: nothing Telegram sent is in them.
    """
    import numpy as np

    from ..meeting_import import TARGET_SAMPLE_RATE

    cap = VOICE_MAX_SECONDS * PCM_BYTES_A_SECOND
    cmd = ["ffmpeg", "-v", "error", "-i", "pipe:0", "-t", str(VOICE_MAX_SECONDS + 1),
           "-f", "s16le", "-ac", "1", "-ar", str(TARGET_SAMPLE_RATE), "pipe:1"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    late = threading.Event()

    def stop() -> None:
        late.set()
        proc.kill()

    def feed() -> None:
        try:
            assert proc.stdin is not None
            proc.stdin.write(data)
        except (BrokenPipeError, OSError, ValueError):
            pass
        finally:
            try:
                proc.stdin.close()  # type: ignore[union-attr]
            except (BrokenPipeError, OSError, ValueError):
                pass

    clock = threading.Timer(DECODE_SECONDS, stop)
    clock.daemon = True
    feeder = threading.Thread(target=feed, name="reach-voice-feed", daemon=True)
    chunks: list[bytes] = []
    total = 0
    too_long = False
    try:
        clock.start()
        feeder.start()
        assert proc.stdout is not None
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > cap:
                too_long = True
                break
            chunks.append(chunk)
    finally:
        clock.cancel()
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        for pipe in (proc.stdout, proc.stdin):
            try:
                if pipe is not None:
                    pipe.close()
            except (BrokenPipeError, OSError, ValueError):
                pass
    if too_long:
        raise VoiceRefused(VOICE_TOO_LONG_WORDS)
    if late.is_set():
        raise RuntimeError("the decoder did not end in time")
    pcm = b"".join(chunks)
    if not pcm:
        raise RuntimeError("the decoder gave no audio")
    return np.frombuffer(pcm[: len(pcm) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768.0


def decode_voice(data: bytes) -> Any:
    """The audio as the speech engine takes it (16 kHz mono floats). No
    file is made (:func:`_decode_bytes`)."""
    return _decode_bytes(data)


# ── the words that wait ──────────────────────────────────────────────


#: One reader and writer of the row at a time: his press comes on the poll
#: thread and an offer is made on the worker (:class:`_Worker`).
_LOCK = threading.RLock()


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
    store could not be written (then nothing is offered). The store is
    pruned AFTER the insert (review T4): it never holds more than
    :data:`PENDING_MAX`."""
    with _LOCK:
        state = _state(tg)
        key = secrets.token_urlsafe(12)
        while key in state["pending"]:
            key = secrets.token_urlsafe(12)
        state["pending"][key] = {"words": words, "kind": kind, "gen": tg._generation(),
                                 "message_id": None, "at": time.time()}
        state = _pruned(tg, state)
        return key if tg._save_policy(INBOUND_POLICY, state) else None


def _bind(tg: Any, key: str, result: Optional[Mapping[str, Any]]) -> bool:
    """The words are bound to the message their buttons are on. False when
    that could not be stored: an entry with no message is never taken
    (:func:`_claim`), so the caller withdraws the offer."""
    message_id = ((result or {}).get("result") or {}).get("message_id")
    with _LOCK:
        state = _state(tg)
        row = state["pending"].get(key)
        if row is None:
            return False
        if not (result or {}).get("ok", False) or message_id is None:
            state["pending"].pop(key, None)      # the offer was not sent: nothing waits
            tg._save_policy(INBOUND_POLICY, state)
            return False
        row["message_id"] = message_id
        return bool(tg._save_policy(INBOUND_POLICY, state))


def _claim(tg: Any, key: str, message_id: Any, act: str) -> tuple[Optional[dict[str, Any]], str]:
    """Take the words of ``key`` for ONE act, written before the act runs
    (review T4): ``(row, "ok")``, or ``(None, "gone")`` when the press is not
    on their own message, in this pairing, within a day, or they were taken
    already, or ``(None, "not_saved")`` when the mark could not be written
    (then nothing is done). A press that comes two times finds the mark."""
    with _LOCK:
        state = _pruned(tg, _state(tg))
        row = state["pending"].get(key)
        if (row is None or row.get("message_id") is None
                or str(row["message_id"]) != str(message_id) or row.get("used")):
            return None, "gone"
        row["used"] = act
        if not tg._save_policy(INBOUND_POLICY, state):
            return None, "not_saved"
        return dict(row), "ok"


def _release(tg: Any, key: str) -> None:
    """The act did not happen: the words wait again."""
    with _LOCK:
        state = _state(tg)
        row = state["pending"].get(key)
        if row is not None and row.pop("used", None) is not None:
            tg._save_policy(INBOUND_POLICY, state)


def _forget(tg: Any, key: str) -> None:
    with _LOCK:
        state = _state(tg)
        if state["pending"].pop(key, None) is not None:
            tg._save_policy(INBOUND_POLICY, state)


def forget_all(tg: Any) -> bool:
    """A new pairing: no words of the pairing before wait (they were his;
    the chat is another). True when the store was written."""
    with _LOCK:
        return bool(tg._save_policy(INBOUND_POLICY, {"pending": {}}))


def tick(tg: Any) -> int:
    """The reach tick: words older than a day, of another pairing, or over
    the count leave the store now, not at his next message (review T4).
    The number that left."""
    with _LOCK:
        state = _state(tg)
        before = len(state["pending"])
        state = _pruned(tg, state)
        gone = before - len(state["pending"])
        if gone:
            tg._save_policy(INBOUND_POLICY, state)
        return gone


def waiting_count(tg: Any) -> int:
    with _LOCK:
        return len(_pruned(tg, _state(tg))["pending"])


# ── one bounded worker ───────────────────────────────────────────────


class _Job:
    def __init__(self, run: Any, late: Any, limit: float) -> None:
        self.run, self.late, self.limit = run, late, limit


class _Worker:
    """ONE thread for the slow work (a voice note is fetched, decoded and
    heard; an Ask is answered), so that the poll, the answers to questions,
    the ticks and the outbox never wait on it (review T4).

    At most :data:`WORKER_QUEUE` jobs wait. Each job has an end-to-end
    limit: at the limit it is abandoned (its ``gone`` event is set, so it
    writes and sends nothing more) and ``late`` says so in one line.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[Optional[_Job]] = queue.Queue(maxsize=WORKER_QUEUE)
        self._stopped = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._late: list[threading.Thread] = []
        self._start = threading.Lock()

    def room(self) -> bool:
        self._late = [thread for thread in self._late if thread.is_alive()]
        return not self._stopped.is_set() and not self._queue.full() and len(self._late) < WORKER_LATE

    def submit(self, job: _Job) -> bool:
        if not self.room():
            return False
        with self._start:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._loop, name="reach-inbound", daemon=True)
                self._thread.start()
        try:
            self._queue.put_nowait(job)
        except queue.Full:
            return False
        return True

    def _loop(self) -> None:
        while not self._stopped.is_set():
            job = self._queue.get()
            if job is None:
                return
            self._do(job)

    def _do(self, job: _Job) -> None:
        gone, done = threading.Event(), threading.Event()

        def body() -> None:
            try:
                job.run(gone)
            except Exception as exc:
                log.warning(f"telegram: an inbound job failed ({type(exc).__name__})")
            finally:
                done.set()

        thread = threading.Thread(target=body, name="reach-inbound-job", daemon=True)
        thread.start()
        if done.wait(job.limit) or self._stopped.is_set():
            return
        gone.set()
        self._late.append(thread)
        try:
            job.late()
        except Exception as exc:
            log.warning(f"telegram: a late job was not said ({type(exc).__name__})")

    def stop(self) -> None:
        """Shutdown: the loop ends; a job that runs is not waited for."""
        self._stopped.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass


def _worker(tg: Any) -> _Worker:
    worker = getattr(tg, "_inbound_worker", None)
    if worker is None:
        worker = _Worker()
        tg._inbound_worker = worker
    return worker


def _inline(tg: Any) -> bool:
    """A test runs the job where it is asked (``tg.inbound_inline``)."""
    return bool(getattr(tg, "inbound_inline", False))


def has_room(tg: Any) -> bool:
    return _inline(tg) or _worker(tg).room()


def _submit(tg: Any, chat_id: str, run: Any, late: Any, limit: float, kind: str) -> dict[str, Any]:
    if _inline(tg):
        return run(threading.Event())
    if _worker(tg).submit(_Job(run, late, limit)):
        return {"action": f"{kind}_queued"}
    tg._send(chat_id, BUSY_WORDS, data_class="reach_answer")
    return {"action": "busy"}


def shutdown(tg: Any) -> None:
    worker = getattr(tg, "_inbound_worker", None)
    if worker is not None:
        worker.stop()


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


def stays_on_desk(result: Mapping[str, Any]) -> bool:
    """True unless the Ask's own record says its words may leave this Mac.

    Review T4: the record is ``provenance`` (``ask_service._given_refs``):
    the refs the answer was GIVEN, from an Ask that ran with no tools, so it
    read nothing else. The words go only when that record is there, is
    complete, says no tools, and names no People content (the custody
    boundary of ``needs_you_membership.withhold_people_content``: People
    content does not leave in a notification). Anything else stays on the
    desk: an answer with no record, an Ask that could use tools, a People
    ref. The words themselves are never read to decide this."""
    record = result.get("provenance")
    if not isinstance(record, Mapping) or record.get("tools") != "none" or record.get("complete") is not True:
        return True
    refs = record.get("refs")
    if not isinstance(refs, (list, tuple)):
        return True
    return any(str(ref).split(":", 1)[0].lower() in _PEOPLE_REF_KINDS for ref in refs)


carries_people = stays_on_desk


def answer_message(question: str, result: Mapping[str, Any], open_url: Optional[str]) -> Message:
    text = str(result.get("output") or "").strip()
    if not text:
        return Message(lines=(ASK_FAILED_WORDS,))
    if stays_on_desk(result):
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


def _admit_voice(tg: Any, voice: Mapping[str, Any]) -> None:
    """What is known before anything is fetched: the length and the size
    Telegram says, a local speech engine, a decoder. Raises
    :class:`VoiceRefused` with the one line he gets."""
    from .telegram_reach import TELEGRAM_OWNER

    if int(voice.get("duration") or 0) > VOICE_MAX_SECONDS:
        raise VoiceRefused(VOICE_TOO_LONG_WORDS)
    if int(voice.get("file_size") or 0) > VOICE_MAX_BYTES:
        raise VoiceRefused(VOICE_TOO_LARGE_WORDS)
    try:
        local = tg._reads().speech_local(TELEGRAM_OWNER)
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


def _words_of(tg: Any, voice: Mapping[str, Any]) -> str:
    """The words of one admitted voice note, heard on this Mac; raises
    :class:`VoiceRefused` with the one line he gets. The size is looked at
    before the fetch (``getFile`` says it) and the read is capped; the
    length is the DECODED length (:func:`_decode_bytes`), whatever the note
    said about itself."""
    from .telegram_reach import TELEGRAM_OWNER

    reads = tg._reads()
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
    another person is his send, and is read as his). What can be refused at
    once is refused here; the fetch, the decode and the hearing run on the
    worker, with an end-to-end limit, and the poll does not wait."""
    note = dict(message.get("voice") or {})
    try:
        _admit_voice(tg, note)
    except VoiceRefused as refused:
        tg._send(chat_id, refused.words, data_class="reach_answer")
        return {"action": "voice_refused", "words": refused.words}

    def run(gone: threading.Event) -> dict[str, Any]:
        try:
            words = _words_of(tg, note)
        except VoiceRefused as refused:
            if gone.is_set():
                return {"action": "voice_abandoned"}
            tg._send(chat_id, refused.words, data_class="reach_answer")
            return {"action": "voice_refused", "words": refused.words}
        if gone.is_set():
            return {"action": "voice_abandoned"}     # said already; the words are not kept
        return _offer(tg, chat_id, words, "voice")

    def late() -> None:
        tg._send(chat_id, VOICE_SLOW_WORDS, data_class="reach_answer")

    return _submit(tg, chat_id, run, late, VOICE_JOB_SECONDS, "voice")


def thought(tg: Any, chat_id: str, text: str, *, question_waits: bool = False) -> dict[str, Any]:
    """Words that answer nothing: offered back, deciding nothing."""
    return _offer(tg, chat_id, " ".join(text.split()), "text", question_waits=question_waits)


def _offer(tg: Any, chat_id: str, words: str, kind: str, *, question_waits: bool = False) -> dict[str, Any]:
    from .telegram_reach import TelegramRefused

    key = _keep(tg, words, kind)
    if key is None:
        tg._send(chat_id, NOT_KEPT_WORDS, data_class="reach_answer")
        return {"action": f"{kind}_not_kept"}
    made = heard_message(words, key) if kind == "voice" else thought_message(words, key, question_waits=question_waits)
    try:
        result = tg._send(chat_id, made, data_class="reach_answer")
    except TelegramRefused:
        _forget(tg, key)
        tg._send(chat_id, VOICE_NOT_SHOWN_WORDS, data_class="reach_answer")
        return {"action": f"{kind}_not_shown"}
    if not _bind(tg, key, result):
        # Review T4: the words are not bound to their message, so no press
        # can take them. The offer is withdrawn: the buttons go, one line
        # says to send it again, and nothing waits.
        _forget(tg, key)
        message_id = ((result or {}).get("result") or {}).get("message_id")
        if message_id is not None:
            tg._edit(chat_id, message_id, Message(lines=(NOT_KEPT_WORDS,)))
        else:
            tg._send(chat_id, NOT_KEPT_WORDS, data_class="reach_answer")
        return {"action": f"{kind}_not_kept"}
    return {"action": "heard" if kind == "voice" else "thought", "key": key}


def tap(tg: Any, chat_id: str, callback_id: str, message: Mapping[str, Any], key: str, act: str) -> dict[str, Any]:
    """His press under words he sent. Only here is a thing written, through
    the operation that owns it. The words are taken for the act BEFORE it
    runs (:func:`_claim`), so two presses, or a press after a crash, write
    one thing at most."""
    from .telegram_reach import TELEGRAM_OWNER, TelegramRefused, _clock

    message_id = message.get("message_id")
    if act not in ("note", "task", "drop", "ask"):
        tg._ack(callback_id)
        return {"action": "ignored"}
    if act == "ask" and not has_room(tg):
        tg._ack(callback_id, BUSY_WORDS)       # nothing is taken: he can press again
        return {"action": "busy"}
    row, why = _claim(tg, key, message_id, act)
    if row is not None and act == "ask" and row.get("kind") != "text":
        _release(tg, key)
        row, why = None, "gone"
    if row is None:
        tg._ack(callback_id, GONE_WORDS if why == "gone" else NOT_WRITTEN_WORDS)
        return {"action": "inbound_gone" if why == "gone" else "not_written"}
    words = str(row.get("words") or "")
    reads = tg._reads()
    clock = _clock(tg._stamp())
    open_url = tg.link_for("/")
    if act == "drop":
        _forget(tg, key)
        tg._ack(callback_id, "Discarded.")
        tg._edit(chat_id, message_id, Message(lines=(DISCARD_WORDS,)))
        return {"action": "discarded"}
    if act == "ask":
        _forget(tg, key)
        tg._ack(callback_id, ASKING_WORDS)
        tg._edit(chat_id, message_id, done_message(words, ASKING_WORDS.rstrip("."), clock))

        def run(gone: threading.Event) -> dict[str, Any]:
            try:
                result = dict(reads.ask(TELEGRAM_OWNER, words) or {})
            except Exception as exc:
                log.info(f"telegram: ask did not answer ({type(exc).__name__})")
                if gone.is_set():
                    return {"action": "ask_abandoned"}
                code = f"{getattr(exc, 'code', '')} {getattr(exc, 'detail', '')}".lower()
                none_set = any(mark in code for mark in ("engine", "assignment", "no_target", "not_configured", "model"))
                tg._send(chat_id, ASK_NO_ENGINE_WORDS if none_set else ASK_FAILED_WORDS, data_class="reach_answer")
                return {"action": "ask_failed", "no_engine": none_set}
            if gone.is_set():
                return {"action": "ask_abandoned"}   # said already; the answer is on his desk
            made = answer_message(words, result, open_url)
            try:
                tg._send(chat_id, made, data_class="reach_answer")
            except TelegramRefused:
                tg._send(chat_id, Message(lines=(ASK_ON_DESK_WORDS,), open_url=open_url,
                                          desk_words="Open it on your desk."), data_class="reach_answer")
                return {"action": "asked", "on_desk": True}
            return {"action": "asked", "on_desk": stays_on_desk(result)}

        def late() -> None:
            tg._send(chat_id, ASK_SLOW_WORDS, data_class="reach_answer")

        return _submit(tg, chat_id, run, late, ASK_JOB_SECONDS, "ask")
    try:
        if act == "note":
            reads.note(TELEGRAM_OWNER, words)
        else:
            reads.task(TELEGRAM_OWNER, task_words(words))
    except Exception as exc:
        detail = exc.detail if isinstance(exc, ServiceError) else ""
        log.info(f"telegram: words were not kept ({type(exc).__name__})")
        _release(tg, key)                        # nothing was written: the words wait again
        tg._ack(callback_id, cut_words(detail or NOT_WRITTEN_WORDS, 180))
        return {"action": "not_written"}
    _forget(tg, key)
    outcome = NOTE_WORDS.rstrip(".") if act == "note" else f"{TASK_WORDS.rstrip('.')}: {task_words(words)}"
    tg._ack(callback_id, NOTE_WORDS if act == "note" else TASK_WORDS)
    tg._edit(chat_id, message_id, done_message(words, outcome, clock, open_url=open_url))
    return {"action": "noted" if act == "note" else "tasked"}
