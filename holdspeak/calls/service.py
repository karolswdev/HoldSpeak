"""The hub's calls: status, the listener, place, hang up, decide, the frame.

One service behind the REST routes (``web/routes/calls.py``) and the MCP
tools (``mcp/families/calls.py``). It keeps the last 20 calls in memory (as
ai-phone does); each finished call is a Note on the desk.

"Full auto": while ``calls.enabled`` is on and ai-phone runs, the hub keeps
one ``ai-phone listen`` waiting for a call. ``HOLDSPEAK_CALLS=off`` (rig
hubs) turns the listener and every read of ai-phone's state off.

The phone half is one of two adapters with one surface (LINE design §4):
HoldSpeak's own Line (``holdspeak/line/adapter.py``) or ai-phone.
``calls.line.adapter`` picks; empty means the Line when baresip is found,
else ai-phone when it is (:func:`pick_adapter`). ``HOLDSPEAK_LINE=off``
(every rig) keeps ai-phone as before.
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .aiphone import AiPhone, Reply
from .runner import CallRecord, CallRunner, Turns

log = get_logger("calls.service")

OWNER = Principal(PrincipalKind.OWNER, "owner-calls")

#: The capability a call's turn runs on.
CAPABILITY = "calls.turn"
#: The home engine over Tailscale: a call's default engine when it exists
#: and the owner did not assign ``calls.turn`` himself.
HOME_ENGINE_PROFILE = "engine-tailscale-karol-8080"
#: The calls the hub keeps.
KEEP = 20
#: A listener that cannot reach ai-phone tries again after this long.
RETRY_SECONDS = 15.0

FRAME = "call_state"

#: The system prompt of a call's turn.
CALL_PROMPT = (
    "You are HoldSpeak on a phone call with the owner. He cannot see a screen and he is waiting: "
    "answer in one to three short spoken sentences, plain words, no lists, no markdown, no ids. "
    "When he asks you to do something, do it at once with the fewest tool calls: add a task with "
    "door.add_item (the owner is \"Me\" unless he names someone), write a note with desk.create, "
    "propose a decision (status proposed), add a project item, prepare a send with channel.prepare. "
    "Read a record only when you need it to answer or to act (memory.page first, then the records). "
    "To send a prepared send, call channel.send with its send_id; to post a nudge, call nudge.send: "
    "each one waits for his spoken yes, so call it and the call asks him. Never change settings. "
    "Then say in one sentence what you did."
)


def calls_on() -> bool:
    """``HOLDSPEAK_CALLS=off``: no listener and no read of ai-phone's state."""
    return os.environ.get("HOLDSPEAK_CALLS", "on").strip().lower() not in {"off", "0", "false", "no"}


def _settings() -> Any:
    from ..config import Config

    return Config.load().calls


def line_node_name(where: str) -> str:
    """``calls.line.where`` as the node's name (``this_mac`` is ``this-mac``)."""
    where = str(where or "this_mac")
    return where[5:] if where.startswith("node:") else "this-mac"


def pick_adapter(cfg: Any = None) -> str:
    """``line``, ``ai-phone`` or ``none``: the phone half this hub drives."""
    from ..line import line_on

    cfg = cfg or _settings()
    choice = str((cfg.line or {}).get("adapter") or "")
    if not line_on():
        return "ai-phone" if AiPhone.from_settings(cfg.aiphone_dir) else "none"
    if choice in {"line", "ai-phone"}:
        return choice
    from .aiphone import COMMAND_ENV

    if os.environ.get(COMMAND_ENV, "").strip():
        return "ai-phone"  # a rig (or the owner) named ai-phone whole
    from ..line.supervisor import find_baresip

    if find_baresip() or str((cfg.line or {}).get("where") or "").startswith("node:"):
        return "line"
    return "ai-phone" if AiPhone.from_settings(cfg.aiphone_dir) else "none"


_LINES: dict[str, Any] = {}


def _line_adapter(node: str) -> Any:
    from ..line.adapter import Line

    found = _LINES.get(node)
    if found is None:
        found = _LINES[node] = Line(node, daily_limit=lambda: int(_settings().daily_limit))
    return found


def default_phone() -> Optional[Any]:
    """The adapter :func:`pick_adapter` names (None: none is found)."""
    cfg = _settings()
    kind = pick_adapter(cfg)
    if kind == "line":
        return _line_adapter(line_node_name((cfg.line or {}).get("where")))
    if kind == "ai-phone":
        return AiPhone.from_settings(cfg.aiphone_dir)
    return None


def line_config(node: str) -> dict[str, Any]:
    """What a Line node gets in its ``hello`` answer: its account, the SIP
    password (a carrier line only; from the keystore), the daily limit and
    the owner's name for the AI disclosure."""
    from ..config import Config
    from ..line import secrets as line_secrets

    config = Config.load()
    account = dict((config.calls.line or {}).get("account") or {})
    account.pop("password_ref", None)
    account.pop("connection_id", None)  # the hub's own note of the Telnyx connection
    password = line_secrets.read(line_secrets.SIP_PASSWORD) if account.get("kind") == "telnyx" else ""
    return {"account": account, "password": password, "daily_limit": int(config.calls.daily_limit),
            "owner": str(getattr(config.owner, "name", "") or "")}


class DeskTurns:
    """A call's turn: the hub's thread loop (``ThreadService.start_turn``)
    with the CALL prompt, the CALL palette, ``calls.turn`` and the held
    egress tools."""

    def __init__(self, db: Any, thread_factory: Callable[..., Any], *, profile_override: str = "") -> None:
        self._db = db
        self._factory = thread_factory
        self._override = profile_override
        self._context = ""

    def set_context(self, context: str) -> None:
        """Phone (2026-10-28): the desk called him; the turn knows why."""
        self._context = str(context or "").strip()

    def _service(self) -> Any:
        from ..mcp.palettes import CALL, CALL_HELD_EGRESS, resolve_palette

        prompt = CALL_PROMPT
        if self._context:
            prompt += (
                "\n\nYou called him. What to tell him, what to ask, and what not to decide is below. "
                "Say the reason first, then ask; take his answer as his decision.\n\n" + self._context[:4000]
            )
        return self._factory(
            system_prompt=prompt, palette=resolve_palette(CALL),
            capability_id=CAPABILITY, held_egress=CALL_HELD_EGRESS,
        )

    def new_thread(self, title: str) -> str:
        return str(self._service().create(title=title, profile_override=self._override)["id"])

    async def run(self, thread_id: str, text: str, *, holds: Callable[[list[dict[str, Any]]], None]) -> dict[str, Any]:
        from ..services import ask_desk
        from ..services.run_trace import ask_trace, use_by_trace

        def progress(event: dict[str, Any]) -> None:
            if event.get("state") == "hold":
                holds(list(event.get("holds") or []))

        turn = await ask_desk.run_loop(
            self._service(), OWNER, thread_id=thread_id, question=text, refs=[],
            invocation_id="call_" + uuid.uuid4().hex, progress=progress,
        )
        key = ask_trace(turn["turn_invocation_id"])
        used = await asyncio.to_thread(lambda: use_by_trace(self._db, [key]).get(key) or {})
        return {"text": turn["text"], "used": used, "error": turn["error"], "aborted": turn["aborted"]}

    @staticmethod
    def _handle(tool_call_id: str) -> Any:
        from ..services.thread_service import ThreadService

        return ThreadService._tool_executor._handles.get(tool_call_id)

    def hold_words(self, tool_call_id: str, tool: str) -> str:
        """What leaves, in words: the send's document and destination; the
        nudge's text."""
        from ..services.ask_desk import hold_words

        handle = self._handle(tool_call_id)
        args = dict(getattr(handle, "args", {}) or {})
        try:
            if tool == "channel.send" and args.get("send_id"):
                row = self._db.channel_sends.get(str(args["send_id"])) or {}
                destination = self._db.channel_destinations.get(str(row.get("destination_id") or "")) or {}
                title = _document_title(row)
                where = str(destination.get("name") or "")
                if title or where:
                    return "Send " + (title or "the document") + (f" to {where}" if where else "")
            if tool == "nudge.send" and args.get("text"):
                return "Post this nudge on GitHub: " + str(args["text"])[:160]
            data = args.get("data") if isinstance(args.get("data"), dict) else {}
            label = str(args.get("task") or args.get("title") or data.get("title") or "").strip()
            if label:
                return f"{hold_words(tool)}: {label[:120]}"
        except Exception as exc:  # the words are never a gate
            log.info(f"hold words not read: {exc}")
        return hold_words(tool)

    def decide(self, tool_call_id: str, decision: str) -> bool:
        from ..services.thread_service import ThreadService

        handle = self._handle(tool_call_id)
        if handle is None or handle.state != "awaiting_decision":
            return False
        ThreadService._tool_executor.decide(handle, decision)
        return True


def _document_title(row: dict[str, Any]) -> str:
    import json

    try:
        document = json.loads(row.get("document_json") or "{}")
    except (TypeError, ValueError):
        document = {}
    return str((document or {}).get("title") or "").strip()


class CallsService:
    """The hub's calls (one per hub process)."""

    def __init__(self) -> None:
        self._calls: "OrderedDict[str, CallRecord]" = OrderedDict()
        self._runners: dict[str, CallRunner] = {}
        self._broadcast: Callable[[str, Any], None] = lambda kind, data: None
        self._thread_factory: Optional[Callable[..., Any]] = None
        self._db_fn: Callable[[], Any] = lambda: None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._listener: Optional[asyncio.Task[None]] = None
        self._active: Optional[asyncio.Task[Any]] = None
        self._phone_fn: Callable[[], Optional[AiPhone]] = default_phone
        self._turns_fn: Optional[Callable[[], Optional[Turns]]] = None
        self._lock = threading.Lock()
        #: Phone (2026-10-28): a slow hand's answer after the hang-up.
        self._later_fn: Optional[Callable[[CallRecord, str], None]] = None

    # ── wiring ────────────────────────────────────────────────────────

    def configure(
        self, *, broadcast: Optional[Callable[[str, Any], None]] = None,
        thread_factory: Optional[Callable[..., Any]] = None, db: Optional[Callable[[], Any]] = None,
        phone: Optional[Callable[[], Optional[AiPhone]]] = None, turns: Optional[Callable[[], Optional[Turns]]] = None,
        later: Optional[Callable[[CallRecord, str], None]] = None,
    ) -> None:
        if broadcast is not None:
            self._broadcast = broadcast
        if thread_factory is not None:
            self._thread_factory = thread_factory
        if db is not None:
            self._db_fn = db
        if phone is not None:
            self._phone_fn = phone
        if turns is not None:
            self._turns_fn = turns
        if later is not None:
            self._later_fn = later

    def reset(self) -> None:
        """Forget every call (a test's fresh hub)."""
        self._calls.clear()
        self._runners.clear()

    def _db(self) -> Any:
        db = self._db_fn()
        if db is None:
            from ..db import get_database

            db = get_database()
        return db

    def _emit(self, reason: str, record: CallRecord) -> None:
        try:
            self._broadcast("call_state", {"reason": reason, "call": record.full()})
        except Exception as exc:
            log.debug(f"call frame dropped: {exc}")

    def _keep(self, record: CallRecord) -> None:
        self._calls[record.id] = record
        while len(self._calls) > KEEP:
            oldest = next(iter(self._calls))
            if self._calls[oldest].state != "ended":
                break
            self._calls.pop(oldest)
            self._runners.pop(oldest, None)

    # ── the engine of a call ──────────────────────────────────────────

    def _override_profile(self) -> str:
        """The home engine, unless the owner assigned ``calls.turn`` himself."""
        db = self._db()
        try:
            with db._connection() as conn:
                own = conn.execute(
                    "SELECT 1 FROM inference_assignment_heads WHERE assignment_key=? AND cleared=0",
                    (f"capability:{CAPABILITY}",),
                ).fetchone()
                if own is not None:
                    return ""
                v2 = conn.execute(
                    "SELECT 1 FROM model_profile_revisions WHERE profile_id=? LIMIT 1", (HOME_ENGINE_PROFILE,),
                ).fetchone()
                legacy = conn.execute(
                    "SELECT 1 FROM profiles WHERE id=? AND deleted=0", (HOME_ENGINE_PROFILE,),
                ).fetchone()
        except Exception as exc:
            log.info(f"call engine not read: {exc}")
            return ""
        return HOME_ENGINE_PROFILE if (v2 or legacy) else ""

    def _deployment(self) -> Any:
        from ..services import ask_desk

        db = self._db()
        override = self._override_profile()
        if override:
            from ..services.thread_service import ThreadService

            entries = ThreadService(db, broadcast=lambda *_: None)._override_entries(override)
            if entries:
                entry = dict(entries[0])
                if entry["profile_id"].startswith("legacy-"):
                    entry["profile_schema_version"] = 1
                found = ask_desk.deployment_for_entry(db, entry)
                if found is not None:
                    return found
        return ask_desk._answers_deployment(db, CAPABILITY)

    def engine(self) -> dict[str, Any]:
        from ..services import ask_desk

        deployment = self._deployment()
        if deployment is None:
            return {"profile_id": "", "model": "", "state": "none", "words": "No engine for calls"}
        mode = ask_desk.tools_mode(self._db(), deployment=deployment)
        ready = mode == ask_desk.LOOP
        return {
            "profile_id": str(deployment.profile_id or ""), "model": str(deployment.model or ""),
            "state": "ready" if ready else "no_tools",
            "words": "Ready" if ready else "The engine cannot use the desk's tools",
        }

    def _turns(self) -> Optional[Turns]:
        if self._turns_fn is not None:
            return self._turns_fn()
        if self._thread_factory is None:
            return None
        return DeskTurns(self._db(), self._thread_factory, profile_override=self._override_profile())

    # ── reads ─────────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        cfg = _settings()
        listening = bool(self._listener is not None and not self._listener.done())
        active = self._active_record()
        if not calls_on():
            return {
                "enabled": cfg.enabled, "aiphone": {"state": "off", "words": "Calls are off on this hub"},
                "line": {"node": "", "state": "off", "words": "Off", "address": "", "secrets": {}}, "lines": [], "engine": {"profile_id": "", "model": "", "state": "none", "words": ""},
                "passphrase_set": bool(cfg.passphrase), "listening": False, "active": None, "steps": [],
            }
        phone = self._phone_fn()
        is_line = _is_line(phone)
        if phone is None:
            aiphone = {"state": "not_found", "words": "ai-phone not found"}
            lines: list[dict[str, Any]] = []
        else:
            running = phone.running()
            aiphone = {"state": "running" if running else "not_running",
                       "words": "Running" if running else "ai-phone not running"}
            lines = _lines(phone.state())
        if is_line:
            aiphone = {"state": "off", "words": "The Line is the phone"}
        line = line_status(phone, cfg)
        engine = self.engine()
        if is_line:
            first = [
                {"id": "install", "done": line["state"] != "not_installed", "words": "Install the line: brew install baresip"},
                {"id": "daemon", "done": line["state"] in {"ready", "starting", "not_set_up"}, "words": "Start it: holdspeak line"},
                {"id": "line", "done": line["state"] == "ready", "words": "Add a line: a SIP address, or a Telnyx number"},
            ]
        else:
            first = [
                {"id": "install", "done": aiphone["state"] != "not_found", "words": "Install ai-phone on this Mac"},
                {"id": "daemon", "done": aiphone["state"] == "running", "words": "Start it: uv run ai-phone run"},
                {"id": "line", "done": bool(lines), "words": "Add a line: a SIP address, or a Telnyx number"},
            ]
        steps = [
            *first,
            {"id": "engine", "done": engine["state"] == "ready", "words": "An engine that can use the desk's tools"},
            {"id": "passphrase", "done": bool(cfg.passphrase), "words": "Set a passphrase"},
            {"id": "enable", "done": bool(cfg.enabled), "words": "Turn on calls"},
        ]
        return {
            "enabled": cfg.enabled, "aiphone": aiphone, "line": line, "lines": lines, "engine": engine,
            "passphrase_set": bool(cfg.passphrase), "listening": listening,
            "active": active.summary() if active else None, "steps": steps,
        }

    def list(self) -> list[dict[str, Any]]:
        return [record.summary() for record in reversed(self._calls.values())]

    def get(self, call_id: str) -> Optional[dict[str, Any]]:
        record = self._calls.get(call_id)
        return record.full() if record else None

    def _active_record(self) -> Optional[CallRecord]:
        for record in reversed(self._calls.values()):
            if record.state != "ended":
                return record
        return None

    # ── the loop the hub runs on ──────────────────────────────────────

    def bind_loop(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._loop = loop or asyncio.get_running_loop()

    def _on_loop(self, coroutine: Any, timeout: float = 120.0) -> Any:
        """Run a coroutine on the hub's loop from a worker thread (MCP)."""
        loop = self._loop
        if loop is None or not loop.is_running():
            raise RuntimeError("calls_not_ready")
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            raise RuntimeError("calls_on_loop_thread")
        return asyncio.run_coroutine_threadsafe(coroutine, loop).result(timeout)

    # ── the listener ("full auto") ────────────────────────────────────

    def ensure_listening(self) -> bool:
        """Start the listener when calls are on and enabled (idempotent)."""
        if not calls_on() or not _settings().enabled:
            return False
        if self._listener is not None and not self._listener.done():
            return True
        try:
            self.bind_loop()
        except RuntimeError:
            return False
        self._listener = asyncio.ensure_future(self._listen_forever())
        return True

    async def stop_listening(self) -> None:
        task, self._listener = self._listener, None
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    async def _listen_forever(self) -> None:
        while calls_on() and _settings().enabled:
            outcome = await self.serve_once()
            if outcome in {"no_phone", "not_running", "listener_busy"}:
                await asyncio.sleep(RETRY_SECONDS)
            elif outcome == "failed":
                await asyncio.sleep(1.0)

    async def serve_once(self, *, wait: float = 60.0) -> str:
        """One ``ai-phone listen``: an incoming call runs to its end.
        ``call`` (a call ran), ``timeout``, ``no_phone`` or a reason."""
        phone = self._phone_fn()
        if phone is None:
            return "no_phone"
        reply = await phone.listen(timeout=wait)
        if reply.code == 10:
            return "timeout"
        if reply.ok and reply.kind == "incoming":
            record = CallRecord(phone_call_id=str(reply.data.get("call_id") or ""), direction="in",
                                remote=str(reply.data.get("remote") or ""))
            await self._run_call(phone, record, reason="incoming")
            return "call"
        if reply.ok and reply.kind == "ended":
            return "timeout"  # a relay call that ended while nobody listened
        return reply.reason or "failed"

    def _answer_later(self, record: CallRecord, words: str) -> None:
        """A hand slower than 20 s finished after the hang-up: the answer goes
        to his phone as a message (Phone), else it stays in the call's note."""
        later = self._later_fn
        if later is None:
            try:
                from ..phone import phone_on
                from ..phone.service import default_phone_service

                if not phone_on():
                    return

                def later(rec: CallRecord, text: str) -> None:
                    default_phone_service().send_from_desk(text, origin_ref=f"call:{rec.id}")
            except Exception as exc:
                log.info(f"the later answer has no phone: {exc}")
                return
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.run_in_executor(None, later, record, words)
        else:
            later(record, words)

    async def _run_call(self, phone: AiPhone, record: CallRecord, *, reason: str,
                        greeting: Optional[str] = None) -> CallRecord:
        cfg = _settings()
        turns = self._turns()
        engine_ready = True
        if turns is not None and self._turns_fn is None:
            engine_ready = (await asyncio.to_thread(self.engine))["state"] == "ready"
        record.answered_at = time.time()
        self._keep(record)
        runner = CallRunner(
            phone, record, turns=turns, passphrase=cfg.passphrase, allowed_numbers=cfg.allowed_numbers,
            greeting=greeting or cfg.greeting, emit=self._emit, save_note=self._save_note,
            engine_ready=engine_ready, later=self._answer_later,
        )
        self._runners[record.id] = runner
        self._emit(reason, record)
        self._active = asyncio.ensure_future(runner.run())
        try:
            return await self._active
        finally:
            self._active = None

    # ── the verbs ─────────────────────────────────────────────────────

    async def place(
        self, to: str = "", *, greeting: Optional[str] = None, context: str = "", reason: str = "",
        on_end: Optional[Callable[[CallRecord], None]] = None,
    ) -> dict[str, Any]:
        """``call <to> --relay``; the call runs like an incoming one. ``to``
        defaults to his number (``calls.allowed_numbers[0]``). Phone
        (2026-10-28): ``greeting`` is said after the passphrase (the reason
        the desk called), ``context`` briefs the call's turn, ``on_end``
        gets the record when the call is over."""
        from ..services.errors import ServiceError

        cfg = _settings()
        target = str(to or "").strip() or (cfg.allowed_numbers[0] if cfg.allowed_numbers else "")
        if not target:
            raise ServiceError("calls_no_number", "Set your number in Settings ▸ Calls first.",
                               context={"status": 409, "reason": "no_number"})
        if self._active_record() is not None:
            raise ServiceError("calls_busy", "A call is in progress.", context={"status": 409, "reason": "busy"})
        phone = self._phone_fn() if calls_on() else None
        if phone is None:
            raise ServiceError("calls_not_found", "ai-phone is not found.", context={"status": 409, "reason": "not_found"})
        self.bind_loop()
        await self.stop_listening()  # one listen at a time: the call's own
        reply = await phone.call(target)
        if not (reply.ok and reply.data.get("outcome") == "answered"):
            self.ensure_listening()
            reason = reply.reason or str(reply.data.get("outcome") or "rejected")
            if reason == "rejected" and "no line" in reply.error:
                reason = "no_line"
            raise ServiceError("calls_place_failed", reply.error or f"The call did not connect ({reason}).",
                               context={"status": 409, "reason": reason})
        record = CallRecord(phone_call_id=str(reply.data.get("call_id") or ""), direction="out", remote=target,
                            context=str(context or ""), reason=str(reason or ""))
        self._keep(record)

        async def run_then_listen() -> None:
            try:
                await self._run_call(phone, record, reason="status", greeting=greeting)
            finally:
                self.ensure_listening()
                if on_end is not None:
                    try:
                        on_end(record)
                    except Exception as exc:
                        log.warning(f"call end hook failed: {exc}")

        asyncio.ensure_future(run_then_listen())
        return record.summary()

    async def test_line(self, to: str = "") -> dict[str, Any]:
        """Settings ▸ Calls ▸ Line ▸ Test call: the Line calls him (``to``, else
        his first allowed number), says one line and hangs up. No turn runs."""
        from ..services.errors import ServiceError

        cfg = _settings()
        target = str(to or "").strip() or (cfg.allowed_numbers[0] if cfg.allowed_numbers else "")
        if not target:
            raise ServiceError("calls_no_number", "Set your number or SIP address in Settings ▸ Calls first.",
                               context={"status": 409, "reason": "no_number"})
        phone = self._phone_fn() if calls_on() else None
        if not _is_line(phone):
            raise ServiceError("calls_no_line", "The Line is not the phone on this hub.",
                               context={"status": 409, "reason": "no_line"})
        if self._active_record() is not None:
            raise ServiceError("calls_busy", "A call is in progress.", context={"status": 409, "reason": "busy"})
        reply = await phone.call(target, ring_seconds=30.0)
        if not (reply.ok and reply.data.get("outcome") == "answered"):
            return {"result": reply.reason or str(reply.data.get("outcome") or "failed"), "to": target}
        call_id = str(reply.data.get("call_id") or "")
        await phone.say("This is a test call from your HoldSpeak line. It works.", call_id=call_id)
        await phone.hangup(say="Goodbye.", call_id=call_id)
        return {"result": "answered", "to": target}

    async def hangup(self, call_id: str) -> Optional[dict[str, Any]]:
        record = self._calls.get(call_id)
        if record is None:
            return None
        runner = self._runners.get(call_id)
        if runner is not None and record.state != "ended":
            await runner.hang_up("Goodbye.", ended_by="holdspeak")
        return record.summary()

    def decide(self, call_id: str, decision: str) -> Optional[dict[str, Any]]:
        from ..services.errors import ServiceError, ValidationError

        if decision not in {"approve", "deny"}:
            raise ValidationError("decision must be approve or deny")
        record = self._calls.get(call_id)
        runner = self._runners.get(call_id)
        if record is None or runner is None:
            return None
        if not runner.decide(decision, by="tap"):
            raise ServiceError("calls_nothing_held", "Nothing waits for an answer.",
                               context={"status": 409, "reason": "nothing_held"})
        return record.summary()

    # ── the note ──────────────────────────────────────────────────────

    async def _save_note(self, record: CallRecord) -> None:
        if not record.transcript or all(line.who == "holdspeak" for line in record.transcript):
            return
        await asyncio.to_thread(self._save_note_sync, record)

    def _save_note_sync(self, record: CallRecord) -> None:
        from ..mcp.tools import dispatch

        started = datetime.fromtimestamp(record.answered_at or record.started_at)
        title = f"Call · {started:%d %b %H:%M}"
        body = [f"# {title}", ""]
        for line in record.transcript:
            offset = max(0, int(line.at - (record.answered_at or record.started_at)))
            who = "You" if line.who == "caller" else "HoldSpeak"
            body.append(f"**{who}** ({offset // 60}:{offset % 60:02d}): {line.text}")
        if record.results:
            body += ["", "## Done on this call", ""]
            body += [f"- {row['label'] or row['kind']} ({row['effect']})" for row in record.results]
        created = dispatch("desk.create", {"kind": "notes", "data": {
            "title": title, "body_markdown": "\n".join(body), "tags": ["call"],
        }}, OWNER)
        note_id = _note_id(created)
        if not note_id:
            return
        record.note_ref = f"note:{note_id}"
        if record.project_ref:
            try:
                dispatch("project.resource.add", {
                    "project_id": record.project_ref.split(":", 1)[1], "resource_ref": record.note_ref,
                }, OWNER)
            except Exception as exc:
                log.info(f"call note not filed to {record.project_ref}: {exc}")


def _note_id(created: Any) -> str:
    if not isinstance(created, dict):
        return ""
    for key in ("note_id", "id"):
        if created.get(key):
            return str(created[key])
    for key in ("note", "item", "object", "data"):
        inner = created.get(key)
        if isinstance(inner, dict):
            found = _note_id(inner)
            if found:
                return found
    return ""


def _is_line(phone: Any) -> bool:
    from ..line.adapter import Line

    return isinstance(phone, Line)


#: The Line's state words (the Engines vocabulary).
LINE_WORDS = {"ready": "Ready", "starting": "Starting", "not_running": "Not running", "not_installed": "Not installed",
              "not_set_up": "Not set up", "offline": "Offline", "off": "Off"}


def line_status(phone: Any, cfg: Any) -> dict[str, Any]:
    """``line: {node, state, words, address, secrets}`` for ``GET /api/calls/status``."""
    from ..line import line_on, secrets as line_secrets

    if not _is_line(phone):
        return {"node": "", "state": "off", "words": LINE_WORDS["off"], "address": "", "secrets": {}}
    node = phone.node
    account = (cfg.line or {}).get("account") or {}
    presence = line_secrets.presence() if line_on() else {}
    wire = phone.hub.node_state(node)
    snap = phone.state()
    row = next(iter((snap.get("lines") or {}).values()), {}) if snap else {}
    from ..line.hub import HELLO_STALE_SECONDS

    age = phone.hub.hello_age(node)
    if node != "this-mac" and (age is None or age > HELLO_STALE_SECONDS):
        # LINE-3: another machine's word is its last hello's; after 2 minutes
        # with none, the Line there is not running.
        state = "not_running"
    elif node == "this-mac" and wire in {"never", "offline"}:
        from ..line.supervisor import find_baresip

        if node == "this-mac" and not find_baresip():
            state = "not_installed"
        else:
            state = "not_running"
    elif account.get("kind") == "telnyx" and presence.get("sip_password") == "missing":
        state = "not_set_up"
    elif row.get("state") in {"registered", "listening"}:
        state = "ready"
    elif row.get("state") == "unregistered":
        state = "not_set_up"
    else:
        state = "starting"
    return {"node": node, "state": state, "words": LINE_WORDS[state], "address": str(row.get("address") or ""),
            "secrets": presence, "machine": dict(phone.hub.snapshot(node).get("machine") or {})}


def _lines(state: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for line_id, line in (state.get("lines") or {}).items():
        if not isinstance(line, dict):
            continue
        kind = str(line.get("kind") or "")
        raw = str(line.get("state") or "")
        # ai-phone's own reading: a SIP address has no registrar, so its
        # "unregistered" is listening (``cli_status.line_state``).
        shown = "listening" if kind == "sip" and raw == "unregistered" else raw
        words = {"registered": "Ready", "listening": "Ready", "registering": "Connecting",
                 "degraded": "Not connected", "unregistered": "Not connected", "skipped": "Off"}.get(shown, shown)
        out.append({"id": str(line_id), "kind": kind, "state": shown, "words": words})
    return out


#: The hub's one calls service.
CALLS = CallsService()

__all__ = [
    "CALLS", "CAPABILITY", "CALL_PROMPT", "CallsService", "DeskTurns", "FRAME", "HOME_ENGINE_PROFILE", "calls_on",
    "default_phone", "line_config", "line_node_name", "line_status", "pick_adapter",
]
