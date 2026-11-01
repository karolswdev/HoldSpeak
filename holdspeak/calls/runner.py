"""One call, turn by turn (relay mode).

The gate (the allowed numbers, then the passphrase), then each thing he says
is one agent turn on the call's own thread; while a turn runs the runner says
"Still working on it." so ai-phone never reaches its 25 s limit; a held tool
call (every send and nudge, and a desk write his control mode holds) is said
as a question and his next words answer it; the answer is said with the read
back from the turn's own record; at the end the transcript is a Note.

The turn itself is behind :class:`Turns` (the hub's thread loop in
:mod:`.service`; a scripted one in a test).
"""
from __future__ import annotations

import asyncio
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Mapping, Optional, Protocol

from ..logging_config import get_logger
from ..timestamps import local_now
from . import decide
from .aiphone import AiPhone, Reply

log = get_logger("calls.runner")

#: ai-phone hangs up 25 s after he stops without a ``say``; say this sooner.
KEEPALIVE_SECONDS = 9.0
#: How long one listen waits for him before it listens again.
LISTEN_SECONDS = 60.0
#: The most of an answer said aloud.
SPOKEN_CHARS = 600
#: Passphrase tries before the call ends.
PASSPHRASE_TRIES = 2
#: A hand slower than this says "working on it" and answers later: as a later
#: turn on the call, or after the hang-up as a message to his phone (Phone,
#: 2026-10-28; agentring's answer-later, ``daemon/.../voice/tools.py``).
ANSWER_LATER_SECONDS = 20.0

SAY_PASSPHRASE = "Hello. Say your passphrase."
PASSPHRASE_AGAIN = "That is not correct. Say your passphrase again."
NOT_SET_UP = "Calls are not set up. Set a passphrase in HoldSpeak first. Goodbye."
NOT_ALLOWED = "This line does not take calls from your number. Goodbye."
STILL_WORKING = "Still working on it."
GOODBYE = "Goodbye."
NO_ENGINE = "My engine cannot use your desk now. I will keep this call as a note."
DID_NOT_ANSWER = "My engine did not answer. Say it again, or call later."
YES_OR_NO = "Say yes or no."
#: LANG5: a held program.shape may also wait on the desk.
YES_OR_NO_LATER = "Say yes, no, or later."
LATER_TOOLS = frozenset({"program.shape"})
#: DIR8: a held program.decide is asked as its read back, whole ("… Say yes
#: to decide, or no."); "later", "wait" and "not now" are Later, never No.
DECIDE_TOOLS = frozenset({"program.decide"})
#: LANG5: the held tools shaped before the question (an engine call).
READ_FIRST = frozenset({"program.shape"})
READING = "One moment. I am reading the program."
WORKING_ON_IT = "I am working on it. I will tell you when it is done."
LATER_PREFIX = "About what you asked: "

_YES = re.compile(r"\b(yes|yeah|yep|yup|sure|ok(ay)?|do it|go ahead|send it|allow( it)?|approved?|correct)\b", re.I)
_NO = re.compile(r"\b(no|nope|don'?t|do not|stop|cancel|deny|wait|not now)\b", re.I)
_BYE = re.compile(r"^\W*(ok(ay)?[, ]+)?(thanks?( you)?[, ]*)?(that'?s all|that is all|good ?bye|bye|hang up|end (the )?call|we'?re done)\b", re.I)


class Turns(Protocol):
    """The agent turn a call runs (the hub's thread loop)."""

    def new_thread(self, title: str) -> str: ...

    async def run(self, thread_id: str, text: str, *, holds: Callable[[list[dict[str, Any]]], None]) -> dict[str, Any]:
        """One turn; returns ``{"text", "used", "error"}``. ``holds`` is called
        with the held tool calls whenever they change."""
        ...

    def hold_words(self, tool_call_id: str, tool: str) -> str: ...

    def decide(self, tool_call_id: str, decision: str) -> bool: ...


@dataclass
class Line:
    who: str  # caller | holdspeak
    text: str
    at: float
    interrupted: bool = False


@dataclass
class CallRecord:
    """A call as the hub keeps it (the API's ``<summary>`` and ``<call>``)."""

    phone_call_id: str
    direction: str  # in | out
    remote: str = ""
    id: str = field(default_factory=lambda: "call_" + uuid.uuid4().hex[:12])
    state: str = "ringing"  # ringing | gate | live | ended
    started_at: float = field(default_factory=time.time)
    answered_at: Optional[float] = None
    ended_at: Optional[float] = None
    transcript: list[Line] = field(default_factory=list)
    hold: Optional[dict[str, str]] = None
    results: list[dict[str, Any]] = field(default_factory=list)
    note_ref: str = ""
    project_ref: str = ""
    thread_id: str = ""
    outcome: str = ""
    ended_by: str = ""
    #: Phone (2026-10-28): what the desk called him about (the turn's brief;
    #: never in the summary).
    context: str = ""
    reason: str = ""
    #: PG-DIRECTION DIR8: the Program step the desk called him about; its
    #: held items are read first, after the passphrase.
    about: str = ""
    #: DIR8a: why the desk called (the reach rule's ``because``), kept on
    #: each item the call reads about that step and on its ledger line.
    because: dict[str, Any] = field(default_factory=dict)

    def add(self, who: str, text: str, *, interrupted: bool = False) -> None:
        text = str(text or "").strip()
        if text:
            self.transcript.append(Line(who, text, time.time(), interrupted))

    def first_words(self) -> str:
        for line in self.transcript:
            if line.who == "caller" and not line.text.startswith("("):
                return line.text[:120]
        return ""

    def summary(self) -> dict[str, Any]:
        duration = None
        if self.answered_at is not None:
            duration = round((self.ended_at or time.time()) - self.answered_at, 1)
        return {
            "id": self.id, "direction": self.direction, "remote": self.remote, "state": self.state,
            "started_at": _iso(self.started_at), "answered_at": _iso(self.answered_at),
            "ended_at": _iso(self.ended_at), "duration_sec": duration, "first_words": self.first_words(),
            "hold": dict(self.hold) if self.hold else None, "results": [dict(r) for r in self.results],
            "note_ref": self.note_ref, "project_ref": self.project_ref,
            "outcome": self.outcome, "ended_by": self.ended_by,
        }

    def full(self) -> dict[str, Any]:
        return {**self.summary(), "transcript": [
            {"who": line.who, "text": line.text, "at": _iso(line.at), "interrupted": line.interrupted}
            for line in self.transcript
        ]}


def _iso(epoch: Optional[float]) -> Optional[str]:
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch).astimezone().isoformat(timespec="seconds")


# ── words ───────────────────────────────────────────────────────────────

def digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def number_allowed(remote: str, allowed: list[str]) -> bool:
    """An empty list lets any caller reach the passphrase. A SIP URI's digits
    end with an allowed number's digits (``+1 212…`` and ``1212…`` match);
    a ``sip:`` entry matches the URI's user and host."""
    if not allowed:
        return True
    remote_text = str(remote or "").lower()
    remote_digits = digits(remote_text.split("@", 1)[0])
    for entry in allowed:
        entry_text = str(entry or "").strip().lower()
        if entry_text.startswith("sip:"):
            if entry_text.removeprefix("sip:") in remote_text:
                return True
            continue
        want = digits(entry_text)
        if len(want) >= 4 and remote_digits.endswith(want[-10:]):
            return True
    return False


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).split())


def passphrase_heard(heard: str, passphrase: str) -> bool:
    want = _norm(passphrase)
    return bool(want) and want in _norm(heard)


def yes_or_no(text: str) -> str:
    """``approve``, ``deny`` or ``""`` (not clear)."""
    no, yes = bool(_NO.search(text or "")), bool(_YES.search(text or ""))
    if no and not yes:
        return "deny"
    if yes and not no:
        return "approve"
    return ""


_LATER = re.compile(r"\b(later|on (my|the) desk|at my desk)\b", re.I)


def is_later(text: str) -> bool:
    """LANG5: "later" (or "put it on my desk"): the rows wait on the desk."""
    return bool(_LATER.search(text or ""))


def is_goodbye(text: str) -> bool:
    return len(str(text or "").split()) <= 8 and bool(_BYE.search(text or ""))


_REF = re.compile(r"\(?\b[a-z_]+:[A-Za-z0-9_./#-]+\b\)?")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def speakable(text: str, limit: int = SPOKEN_CHARS) -> str:
    """Plain spoken words: no markdown, no refs, at most ``limit`` characters,
    cut at a sentence."""
    out = _LINK.sub(r"\1", str(text or ""))
    out = re.sub(r"```.*?```", " ", out, flags=re.S)
    out = _REF.sub("", out)
    out = re.sub(r"^[ \t]*([#>*+-]|\d+\.)+[ \t]*", "", out, flags=re.M)
    out = out.replace("**", "").replace("__", "").replace("`", "").replace("*", "")
    out = re.sub(r"\(\s*[,;]?\s*\)", "", out)
    out = " ".join(out.split())
    if len(out) <= limit:
        return out
    cut = out[:limit]
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return (cut[: stop + 1] if stop > limit // 3 else cut.rsplit(" ", 1)[0] + "…").strip()


_KIND_WORDS = {
    "action_item": "Added a task", "action": "Added a task", "note": "Wrote a note",
    "desk_decision": "Proposed a decision", "decision": "Proposed a decision",
    "project_item": "Added a project item",
    # PG15: on a call the one Program write is program.start (the CALL palette).
    "program": "Started the program",
}


def read_back(used: dict[str, Any], *, skip: frozenset[str] = frozenset()) -> tuple[str, list[dict[str, Any]]]:
    """The read back from the turn's own record (``run_trace``), never from
    the model's words: what it wrote and what it prepared. ``skip``: kinds a
    held call already said (LANG5: a shaped Program's own spoken line)."""
    parts: list[str] = []
    rows: list[dict[str, Any]] = []
    for row in (used or {}).get("wrote") or []:
        label = str(row.get("label") or "").strip()
        kind = str(row.get("kind") or "")
        if kind in skip:
            continue
        words = _KIND_WORDS.get(kind, "Changed")
        parts.append(f"{words}: {label}." if label else f"{words}.")
        rows.append({"kind": kind, "label": label, "ref": str(row.get("ref") or ""),
                     "effect": "started" if kind == "program" else "wrote"})
    for row in (used or {}).get("prepared") or []:
        label = str(row.get("label") or "a send").strip()
        parts.append(f"Prepared {label}.")
        rows.append({"kind": "send", "label": label, "ref": str(row.get("ref") or ""), "effect": "prepared"})
    return (("Done: " + " ".join(parts)) if parts else ""), rows


# ── the runner ──────────────────────────────────────────────────────────

class CallRunner:
    """Runs one answered relay call to its end."""

    def __init__(
        self,
        phone: AiPhone,
        record: CallRecord,
        *,
        turns: Optional[Turns],
        passphrase: str,
        allowed_numbers: list[str],
        greeting: str,
        emit: Callable[[str, CallRecord], None],
        save_note: Callable[[CallRecord], Awaitable[None]],
        engine_ready: bool = True,
        later: Optional[Callable[[CallRecord, str], None]] = None,
        held: Optional[Any] = None,
    ) -> None:
        self._phone = phone
        self.record = record
        self._turns = turns
        self._passphrase = passphrase
        self._allowed = list(allowed_numbers or [])
        self._greeting = greeting
        self._emit = emit
        self._save_note = save_note
        self._engine_ready = engine_ready and turns is not None
        self._hangup_asked = asyncio.Event()
        self._later = later
        #: Turns slower than ANSWER_LATER_SECONDS: (task, holds queue, decided).
        self._late: list[tuple["asyncio.Future[dict[str, Any]]", "asyncio.Queue[list[dict[str, Any]]]", set[str]]] = []
        #: LANG5: record kinds a held call already said (a shaped Program).
        self._said_kinds: frozenset[str] = frozenset()
        #: DIR8: what waits on him (``calls.decide.DeskHeld``), and each held
        #: item this call read, with what came of it (the ledger at the end).
        self._held = held
        self._asked: list[dict[str, Any]] = []

    # ── the phone, with the transcript and the frame ─────────────────

    async def say(self, text: str) -> bool:
        text = str(text or "").strip()
        if not text:
            return True
        reply = await self._phone.say(text, call_id=self.record.phone_call_id)
        if reply.code == 11:  # the call ended before the words
            await self._ended(reply, "them")
            return False
        self.record.add("holdspeak", text, interrupted=reply.data.get("result") == "interrupted")
        self._emit("said", self.record)
        return reply.ok

    async def listen(self) -> Optional[str]:
        """His next words; None when the call is over."""
        while not self._hangup_asked.is_set():
            reply = await self._phone.listen(call_id=self.record.phone_call_id, timeout=LISTEN_SECONDS)
            if reply.code == 10:  # he said nothing yet: the call goes on
                continue
            if reply.ok and reply.kind == "heard":
                text = str(reply.data.get("text") or "").strip()
                if text:
                    self.record.add("caller", text)
                    self._emit("heard", self.record)
                    return text
                continue
            await self._ended(reply, "them")
            return None
        return None

    async def hang_up(self, words: str = GOODBYE, *, ended_by: str = "holdspeak") -> None:
        self._hangup_asked.set()
        if self.record.state == "ended":
            return
        reply = await self._phone.hangup(say=words, call_id=self.record.phone_call_id)
        if words:
            self.record.add("holdspeak", words)
        await self._ended(reply, ended_by, own=True)

    async def _ended(self, reply: Reply, ended_by: str, *, own: bool = False) -> None:
        if self.record.state == "ended":
            return
        data = reply.data or {}
        self.record.state = "ended"
        self.record.ended_at = time.time()
        self.record.outcome = str(data.get("outcome") or "completed")
        mapped = {"agent": "holdspeak", "them": "caller", "hangup_command": "holdspeak"}
        reported = str(data.get("ended_by") or "")
        self.record.ended_by = ended_by if own or not reported else mapped.get(reported, reported)
        self.record.hold = None
        self._emit("ended", self.record)
        try:
            await self._save_note(self.record)
        except Exception as exc:  # the call is over; the note is not a gate
            log.warning(f"call note not saved: {exc}")
        await self._write_ledger()
        self._emit("result", self.record)

    # ── the call ──────────────────────────────────────────────────────

    async def run(self) -> CallRecord:
        record = self.record
        record.answered_at = record.answered_at or time.time()
        try:
            if not await self._gate():
                return record
            record.state = "live"
            self._emit("status", record)
            if not await self.say(self._greeting if self._engine_ready else NO_ENGINE):
                return record
            if self._turns is not None:
                record.thread_id = self._turns.new_thread(f"Call · {local_now():%d %b %H:%M}")
                if record.context and hasattr(self._turns, "set_context"):
                    self._turns.set_context(record.context)
            if self._held is not None and record.about:
                await self.read_held(about=record.about, because=record.because)
            while record.state != "ended":
                heard = await self._listen_or_late()
                if heard is None:
                    break
                if is_goodbye(heard):
                    await self.hang_up(GOODBYE, ended_by="caller")
                    break
                if self._held is not None and decide.is_what_waits(heard):
                    await self.read_held()
                    continue
                if not self._engine_ready:
                    if not await self.say(NO_ENGINE):
                        break
                    continue
                await self._turn(heard)
        except asyncio.CancelledError:
            if record.state != "ended":
                try:
                    await asyncio.shield(self.hang_up(GOODBYE))
                except Exception:
                    pass
            raise
        except Exception as exc:
            log.exception(f"call {record.id} failed: {exc}")
            if record.state != "ended":
                await self.hang_up("Something went wrong on my side. Goodbye.")
        finally:
            self._after_hangup()
        return record

    # ── answer later ──────────────────────────────────────────────────

    async def _listen_or_late(self) -> Optional[str]:
        """His next words; while a slow turn runs, its answer is said as soon
        as it is ready (the listen is stopped and started again)."""
        while True:
            await self._say_late()
            if self.record.state == "ended":
                return None
            pending = [task for task, _q, _d in self._late if not task.done()]
            if not pending:
                return await self.listen()
            listening = asyncio.ensure_future(self.listen())
            done, _ = await asyncio.wait({listening, *pending}, return_when=asyncio.FIRST_COMPLETED)
            if listening in done:
                return listening.result()
            listening.cancel()
            try:
                await listening
            except (asyncio.CancelledError, Exception):
                pass

    async def _say_late(self) -> None:
        """Ask a slow turn's held calls, and say each finished one's answer."""
        for task, holds, decided in list(self._late):
            while not holds.empty():
                for row in holds.get_nowait():
                    call_id = str(row.get("call_id") or "")
                    if call_id and call_id not in decided:
                        decided.add(call_id)
                        if not await self._ask(call_id, str(row.get("tool") or "")):
                            return
            if task.done():
                self._late.remove((task, holds, decided))
                words = self._answer_words(task)
                if words and not await self.say(LATER_PREFIX + words):
                    return

    def _answer_words(self, task: "asyncio.Future[dict[str, Any]]") -> str:
        try:
            result = task.result()
        except (asyncio.CancelledError, Exception) as exc:
            log.info(f"a slow call turn did not answer: {exc}")
            return ""
        text = speakable(str(result.get("text") or ""))
        back, rows = read_back(result.get("used") or {}, skip=self._said_kinds)
        for row in rows:
            if row not in self.record.results:
                self.record.results.append(row)
        if rows:
            self._emit("result", self.record)
        return " ".join(part for part in (text, back) if part)

    def _after_hangup(self) -> None:
        """A slow turn still running when the call ended answers as a message."""
        for task, _holds, _decided in list(self._late):
            self._late.remove((task, _holds, _decided))

            def done(finished: "asyncio.Future[dict[str, Any]]") -> None:
                words = self._answer_words(finished)
                if words and self._later is not None:
                    try:
                        self._later(self.record, words)
                    except Exception as exc:
                        log.warning(f"the later answer was not sent: {exc}")

            if task.done():
                done(task)
            else:
                task.add_done_callback(done)

    async def _gate(self) -> bool:
        record = self.record
        record.state = "gate"
        self._emit("status", record)
        if not number_allowed(record.remote, self._allowed):
            await self.hang_up(NOT_ALLOWED, ended_by="holdspeak")
            return False
        if not self._passphrase:
            await self.hang_up(NOT_SET_UP, ended_by="holdspeak")
            return False
        prompt = SAY_PASSPHRASE
        for _ in range(PASSPHRASE_TRIES):
            if not await self.say(prompt):
                return False
            heard = await self._listen_secret()
            if heard is None:
                return False
            if passphrase_heard(heard, self._passphrase):
                return True
            prompt = PASSPHRASE_AGAIN
        await self.hang_up(GOODBYE, ended_by="holdspeak")
        return False

    async def _listen_secret(self) -> Optional[str]:
        """His passphrase: heard, but kept out of the transcript and the note."""
        text = await self.listen()
        if text is not None and self.record.transcript and self.record.transcript[-1].text == text:
            self.record.transcript[-1].text = "(passphrase)"
            self._emit("heard", self.record)
        return text

    async def _turn(self, heard: str) -> None:
        assert self._turns is not None
        self._said_kinds = frozenset()
        holds: asyncio.Queue[list[dict[str, Any]]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def on_holds(rows: list[dict[str, Any]]) -> None:
            loop.call_soon_threadsafe(holds.put_nowait, list(rows or []))

        task = asyncio.ensure_future(self._turns.run(self.record.thread_id, heard, holds=on_holds))
        decided: set[str] = set()
        started = time.monotonic()
        try:
            while not task.done():
                if time.monotonic() - started >= ANSWER_LATER_SECONDS and self.record.hold is None:
                    # A slow hand: say so and listen on; the answer comes later.
                    self._late.append((task, holds, decided))
                    await self.say(WORKING_ON_IT)
                    return
                getter = asyncio.ensure_future(holds.get())
                wait = min(KEEPALIVE_SECONDS, max(0.05, ANSWER_LATER_SECONDS - (time.monotonic() - started)))
                done, _ = await asyncio.wait({task, getter}, timeout=wait, return_when=asyncio.FIRST_COMPLETED)
                if getter not in done:
                    getter.cancel()
                if task in done:
                    break
                if getter in done:
                    for row in getter.result():
                        call_id = str(row.get("call_id") or "")
                        if call_id and call_id not in decided:
                            decided.add(call_id)
                            if not await self._ask(call_id, str(row.get("tool") or "")):
                                task.cancel()
                                return
                    continue
                if time.monotonic() - started >= ANSWER_LATER_SECONDS:
                    continue  # the top of the loop moves it to later
                if not await self.say(STILL_WORKING):
                    task.cancel()
                    return
            result = task.result()
        except asyncio.CancelledError:
            task.cancel()
            raise
        except Exception as exc:
            log.warning(f"call turn failed: {exc}")
            await self.say(DID_NOT_ANSWER)
            return
        text = speakable(str(result.get("text") or ""))
        back, rows = read_back(result.get("used") or {}, skip=self._said_kinds)
        for row in rows:
            if row not in self.record.results:
                self.record.results.append(row)
        for ref in _project_refs(result.get("used") or {}):
            self.record.project_ref = self.record.project_ref or ref
        if rows:
            self._emit("result", self.record)
        if result.get("error") and not text:
            await self.say(DID_NOT_ANSWER)
            return
        await self.say(" ".join(part for part in (text, back) if part) or "Done.")

    async def _ask(self, tool_call_id: str, tool: str) -> bool:
        """Say a held call as a question; his next words decide it. False
        when the call ended."""
        assert self._turns is not None
        nothing = getattr(self._turns, "nothing_to_ask", None)
        if tool in READ_FIRST:
            # The shaped answer says what changed ("Done: the program … has
            # three changes"); the record's "program" row is not said again.
            self._said_kinds = self._said_kinds | {"program"}
            if not await self.say(READING):
                return False
        # LANG5: a program.shape is shaped here (one engine call): off the loop.
        if nothing is not None and await asyncio.to_thread(nothing, tool_call_id, tool):
            # PG15: nothing would change (no Program has that name): no
            # question; the tool answers so and the turn says it.
            self._turns.decide(tool_call_id, "approve")
            return True
        words = self._turns.hold_words(tool_call_id, tool)
        asked = getattr(self._turns, "hold_question", None)
        read = asked(tool_call_id, tool) if asked is not None else ""
        self.record.hold = {"tool": tool, "words": read or words, "label": words, "call_id": tool_call_id}
        self._emit("hold", self.record)
        question = (f"{read} {YES_OR_NO_LATER}" if read and tool in LATER_TOOLS
                    else read if read and tool in DECIDE_TOOLS
                    else f"{read} {YES_OR_NO}" if read
                    else f"I want to {words[0].lower() + words[1:] if words else 'change your desk'}. {YES_OR_NO}")
        while True:
            if self.record.hold is None:  # decided by the tap on the Calls window
                return True
            if not await self.say(question):
                return False
            if self.record.hold is None:
                return True
            heard = await self.listen()
            if heard is None:
                return False
            if self.record.hold is None:
                return True
            if tool in DECIDE_TOOLS:
                said = decide.yes_no(heard)
                decision = ({"yes": "approve", "no": "deny"}.get(said, "")
                            or ("later" if decide.is_later(heard) else ""))
            else:
                decision = "later" if tool in LATER_TOOLS and is_later(heard) else yes_or_no(heard)
            if decision:
                self.decide(decision, by="voice")
                return True
            question = YES_OR_NO

    def decide(self, decision: str, *, by: str = "tap") -> bool:
        """The held question's answer (his spoken yes, or the tap)."""
        hold = self.record.hold
        if hold is None or self._turns is None:
            return False
        if not self._turns.decide(hold["call_id"], decision):
            return False
        if decision == "approve" and hold.get("tool") in {"channel.send", "nudge.send"}:
            self.record.results.append({
                "kind": "send" if hold["tool"] == "channel.send" else "nudge",
                "label": hold.get("words", ""), "ref": "", "effect": "sent",
            })
        if decision == "approve" and hold.get("tool") == "program.decide":
            self.record.results.append({"kind": "program_decision", "label": hold.get("label", ""), "ref": "",
                                        "effect": "decided"})
        if decision == "approve" and hold.get("tool") == "program.shape":
            self.record.results.append({"kind": "program", "label": hold.get("label", ""), "ref": "", "effect": "changed"})
        self.record.hold = None
        self._emit("decided", self.record)
        return True

    # ── the call that decides (PG-DIRECTION DIR8) ─────────────────────

    async def read_held(self, *, about: str = "", because: Optional[Mapping[str, Any]] = None) -> None:
        """Read what waits on him, one item at a time (§4): the package, his
        choice, the read back, his yes; Later; the next. A call that ends
        decides nothing more; what it did not decide stays held."""
        assert self._held is not None
        try:
            bodies, desk_only = await asyncio.to_thread(self._held.items, about, because)
        except Exception as exc:
            log.warning(f"what waits on him was not read: {exc}")
            await self.say(DID_NOT_ANSWER)
            return
        if not bodies:
            await self.say(decide.NOTHING_WAITS if not desk_only else
                           decide.summary_words([], desk_only).removeprefix("That is all. "))
            return
        if len(bodies) > 1 and not await self.say(f"{decide.count_words(len(bodies))} things wait on you."):
            return
        outcomes: list[dict[str, Any]] = []
        for body in bodies:
            answered = await asyncio.to_thread(self._held.answered, body)
            if answered:
                if not await self.say(decide.answered_words(body, speakable(answered, 200))):
                    return
                continue
            row = {"body": body, "outcome": "", "asked_clock": decide.clock(self._held.now())}
            self._asked.append(row)
            outcomes.append(row)
            step = await self._one_held(row)
            if step is None:
                return  # the call ended: nothing more is decided
            if step == "stop":
                break
        await self.say(decide.summary_words(outcomes, desk_only))

    async def _one_held(self, row: dict[str, Any]) -> Optional[str]:
        """One held item: ``next``, ``stop``, or None when the call ended."""
        body = row["body"]
        if not await self.say(decide.package_words(body)):
            return None
        unclear, noes = 0, 0
        while True:
            heard = await self.listen()
            if heard is None:
                return None
            if decide.is_stop(heard):
                return "stop"
            choice = decide.match_choice(body, heard)
            if choice is None and decide.is_next(heard):
                heard = "later"
            if choice is None and decide.is_later(heard):
                return await self._later_held(row, heard)
            if choice is None:
                if decide.is_waive(heard):
                    words = f"{decide.ON_THE_DESK} {decide.choices_words(body)}"
                else:
                    unclear += 1
                    if unclear > decide.UNCLEAR_TRIES:
                        return "next"  # it stays held; the summary says it still waits
                    words = decide.choices_words(body)
                if not await self.say(words):
                    return None
                continue
            answer = await self._read_back(body, choice)
            if answer is None:
                return None
            if answer == "later":
                return await self._later_held(row, "later")
            if answer == "yes":
                try:
                    await asyncio.to_thread(self._held.decide, body, choice)
                except Exception as exc:
                    detail = str(getattr(exc, "detail", "") or exc) or "It was not decided."
                    row["outcome"] = "answered" if getattr(exc, "code", "") == "answered_already" else ""
                    # IMP5 on the call: the refusal's name rides on the ledger line.
                    row["refusal"] = str((getattr(exc, "context", None) or {}).get("refusal") or "") or None
                    return "next" if await self.say(speakable(detail, 200)) else None
                label = next((c["label"] for c in body["choices"] if c["id"] == choice), choice)
                row.update(outcome="decided", choice=choice, label=label)
                self.record.results.append({"kind": "program_decision", "label": f"{label}: {decide.where_words(body)}",
                                            "ref": str(body.get("ref") or ""), "effect": "decided"})
                self._emit("result", self.record)
                return "next" if await self.say(decide.DECIDED) else None
            noes += 1
            if noes > 1:
                return "next" if await self.say(decide.NOTHING_CHANGED) else None
            if not await self.say(f"{decide.NOTHING_CHANGED} {decide.choices_words(body)}"):
                return None

    async def _read_back(self, body: dict[str, Any], choice: str) -> Optional[str]:
        """The read back, once; ``yes``, ``no``, ``later``, or None (ended)."""
        question = decide.read_back_words(body, choice)
        self.record.hold = {"tool": "program.decide", "words": question, "label": question, "call_id": ""}
        self._emit("hold", self.record)
        try:
            while True:
                if not await self.say(question):
                    return None
                heard = await self.listen()
                if heard is None:
                    return None
                answer = decide.yes_no(heard)
                if not answer and decide.is_later(heard):
                    return "later"
                if answer:
                    return answer
                question = "Say yes to decide, or no."
        finally:
            if self.record.state != "ended":
                self.record.hold = None

    async def _later_held(self, row: dict[str, Any], heard: str) -> Optional[str]:
        """Later with his next touch (or his default); no read back: it
        changes nothing."""
        assert self._held is not None
        while True:
            try:
                until = await asyncio.to_thread(self._held.later, row["body"], heard)
                break
            except ValueError:
                if not await self.say(decide.SAY_A_TIME):
                    return None
                heard = await self.listen()
                if heard is None:
                    return None
                heard = heard if decide.is_later(heard) else f"later {heard}"
            except Exception as exc:
                from ..services.briefing_service import NOT_KEPT

                log.warning(f"later was not recorded: {exc}")
                row["refusal"] = "not_kept"  # IMP5: the same words as the page and Telegram
                return "next" if await self.say(f"{NOT_KEPT}.") else None
        row.update(outcome="later", until_clock=decide.clock(until))
        return "next" if await self.say(f"Later, at {decide.clock(until)}. I will ask again then.") else None

    async def _write_ledger(self) -> None:
        """When the call ends: one ledger line per item it read (§4.6)."""
        if self._held is None or not self._asked:
            return
        title = ""
        if self.record.note_ref:
            started = datetime.fromtimestamp(self.record.answered_at or self.record.started_at)
            title = f"Call · {started:%d %b %H:%M}"
        try:
            await asyncio.to_thread(self._held.ledger, list(self._asked), note_ref=self.record.note_ref,
                                    note_title=title)
        except Exception as exc:
            log.warning(f"the call's ledger was not written: {exc}")


def _project_refs(used: dict[str, Any]) -> list[str]:
    refs = []
    for key in ("wrote", "looked_at"):
        for row in used.get(key) or []:
            ref = str(row.get("ref") or "")
            if ref.startswith("project:"):
                refs.append(ref)
    return refs


__all__ = [
    "ANSWER_LATER_SECONDS", "CallRecord", "CallRunner", "Line", "Turns", "is_goodbye", "is_later", "number_allowed", "passphrase_heard",
    "read_back", "speakable", "yes_or_no",
]
