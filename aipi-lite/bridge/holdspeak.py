"""HoldSpeakLeg — WebSocket client for `/api/devices/audio`.

Owns one WS session at a time (handshake → audio + control sender →
status frame dispatch → close). Surrounded by `reconnect_with_backoff`
in `_run` so a flapping HoldSpeak doesn't tight-loop reconnects.

The activity state machine for LCD pushback (sticky / flash / revert)
lives here too — `_paint_activity` is the heart of it.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import websockets
from pydantic import ValidationError

from bridge.lcd import (
    _ACTIVITY_SYMBOLS,
    BOOKMARK_FLASH_MS,
    ERROR_ACTIVITY_SYMBOL,
    ERROR_FLASH_MS,
    LINK_CONNECTING,
    LINK_OFFLINE,
    LINK_ONLINE,
    SESSION_BUSY_FLASH_MS,
    _format_activity,
)
from bridge.reconnect import _close_code_reason
from bridge.settings import Settings
from holdspeak_proto import (
    DEVICE_HANDSHAKE_VERSION,
    ErrorFrame,
    Heartbeat,
    Hello,
    HelloAck,
    Status,
)


class HoldSpeakLeg:
    """Manages a single WebSocket session against `/api/devices/audio`.

    Health is enforced via `websockets`' ping/pong (RFC-6455) — a healthy
    idle HoldSpeak connection produces *zero* unsolicited server frames,
    so a frame-receive timeout would tear down healthy connections.
    Outbound `heartbeat` control frames are still emitted on a 15 s
    cadence so HoldSpeak's logs show device liveness, but they are NOT
    used for inbound timeout detection. Two distinct mechanisms.
    """

    HEARTBEAT_INTERVAL_S = 15.0
    METRICS_INTERVAL_S = 1.0
    QUERY_TIMEOUT_S = 2.0
    QUERY_TEXT_MAX_CHARS = 30

    def __init__(
        self,
        settings: Settings,
        log: Any,
        *,
        audio_queue: asyncio.Queue[bytes],
        control_queue: asyncio.Queue[str],
        on_link_update: Callable[[str], Awaitable[None]] | None = None,
        on_activity_update: Callable[[str], Awaitable[None]] | None = None,
        on_middle_update: Callable[[str], Awaitable[None]] | None = None,
        on_middle_flash: Callable[[int], None] | None = None,
    ) -> None:
        self.settings = settings
        self.log = log.bind(leg="holdspeak")
        self.audio_queue = audio_queue
        self.control_queue = control_queue
        # Two LCD-paint callbacks. The bridge's `_run` wires these to
        # `DeviceLeg.update_link` (top-right) and
        # `DeviceLeg.update_screen` (bottom). Tests can swap in a stub
        # to assert what the leg *would* paint without touching the
        # ESPHome client.
        self.on_link_update = on_link_update
        self.on_activity_update = on_activity_update
        # AIPI-4-11: transient flashes (ttl_ms > 0 status frames, bookmark,
        # error) route here instead of overwriting the bottom activity
        # slot's persistent state (Recording-tick, Ready, etc.).
        self.on_middle_update = on_middle_update
        self.on_middle_flash = on_middle_flash
        self._url = (
            f"ws://{settings.holdspeak_host}:{settings.holdspeak_port}/api/devices/audio"
        )
        # Reset on each session start; ticker emits + zeroes them periodically.
        self._bytes_window: int = 0
        self._frames_window: int = 0
        # Activity (bottom-label) state machine: `_sticky_activity` is
        # the most recent `ttl_ms == 0` paint (rendered, with symbol).
        # A `ttl_ms > 0` paint is a "flash" — `_activity_revert_task`
        # is the timer that puts the sticky back when the flash
        # expires. A new paint cancels any pending revert
        # (newest message wins). `_sticky_text` is the raw status text
        # (no symbol) — used by `is_in_meeting()` as a side-effect-free
        # in-meeting probe (HoldSpeak only emits `Recording`-prefixed
        # status frames during an active meeting per HS-14-07).
        self._sticky_activity: str | None = None
        self._sticky_text: str | None = None
        # AIPI-4-11 v2 (user feedback 2026-05-10): middle slot now
        # persists until replaced by the next flash. No auto-clear
        # timer — the latest spoken segment lingers as "last said"
        # context until another flash arrives. Removed
        # `_middle_clear_task` from the field set; if the previous
        # task field is referenced anywhere, that's a stale reference
        # bug worth fixing rather than silently ignoring.
        # Last link state emitted via `_call_link`. Stored so
        # `republish_link_state()` (called by `DeviceLeg._on_connect`
        # via the `on_device_ready` callback) can re-paint after the
        # device leg's service handles get cached — fixes the race
        # where HoldSpeak handshake wins against the device-leg
        # connect and the initial `[OK]` paint silently no-ops.
        # See AIPI-4-08.
        self._last_link_state: str | None = None
        # Strong-ref set for fire-and-forget tasks (revert timers,
        # session_busy flashes). `asyncio.create_task` returns a
        # weak-ref-collectable Task; CPython can GC it before completion
        # without a held reference.
        self._pending_tasks: set[asyncio.Task] = set()
        self._pending_query_timeout: asyncio.Task | None = None

    async def session(self) -> None:
        """One WebSocket lifecycle: handshake, then heartbeat + receive +
        audio-sender + metrics-ticker loops.

        Returns normally on a clean server close so the outer reconnect
        helper resets the backoff counter; raises on errors so the
        outer helper backs off + retries.
        """
        # Drain any audio that piled up before this session started — the
        # user wasn't speaking *to* HoldSpeak during the gap, so handing
        # those frames over now would just confuse the transcription.
        drained = 0
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                drained += 1
            except asyncio.QueueEmpty:
                break
        if drained:
            self.log.info("audio.queue.drained_before_session", chunks=drained)

        # Reset metrics window for this session.
        self._bytes_window = 0
        self._frames_window = 0

        # Paint link `[..]` while we're trying to connect + handshake;
        # `[OK]` once the handshake lands. The outer `finally` paints
        # `[--]` on any exit (clean OR abrupt) so the LCD reflects
        # "bridge is up but WS is not" while `reconnect_with_backoff`
        # is sleeping between attempts.
        await self._call_link(LINK_CONNECTING)
        try:
            async with websockets.connect(
                self._url,
                ping_interval=15,
                ping_timeout=30,
                close_timeout=2,
                max_size=2 * 1024 * 1024,
            ) as ws:
                await self._handshake(ws)
                await self._call_link(LINK_ONLINE)
                # Initialise the sticky activity to "Ready" so any
                # flash arriving before HoldSpeak has sent a sticky
                # has a sane default to revert to.
                await self._paint_activity("Ready")
                tasks = [
                    asyncio.create_task(self._heartbeat_sender(ws)),
                    asyncio.create_task(self._frame_receiver(ws)),
                    asyncio.create_task(self._audio_sender(ws)),
                    asyncio.create_task(self._control_sender(ws)),
                    asyncio.create_task(self._metrics_ticker()),
                ]
                try:
                    # FIRST_COMPLETED so a server-initiated close
                    # (which only `_frame_receiver` notices — the
                    # other tasks are blocked on queue.get / sleep)
                    # tears the session down promptly. With plain
                    # `gather` the session would hang until the next
                    # heartbeat (~15 s) tried to send and raised
                    # ConnectionClosed.
                    done, _pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                    for t in done:
                        exc = t.exception()
                        if exc is None:
                            # Most likely `_frame_receiver`'s `async for`
                            # iterator ended on a clean server close
                            # (the iterator swallows
                            # ConnectionClosedOK). Treat as clean
                            # session return → outer reconnect resets.
                            continue
                        if isinstance(exc, websockets.ConnectionClosedOK):
                            # 1000/1001 — clean shutdown. Reset backoff.
                            code, _reason = _close_code_reason(exc)
                            self.log.info(
                                "disconnect.holdspeak.clean", code=code
                            )
                            continue
                        if isinstance(exc, websockets.ConnectionClosedError):
                            # 1006/1011/4xxx — abrupt close. Surface
                            # the exception so the outer reconnect
                            # engages exponential backoff instead of
                            # tight-looping.
                            code, reason = _close_code_reason(exc)
                            self.log.warning(
                                "disconnect.holdspeak.abrupt",
                                code=code,
                                reason=reason[:200],
                            )
                            raise exc
                        raise exc
                finally:
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    self._cancel_query_timeout()
                    # Drain cancellations + swallow per-task exceptions
                    # so one cancelled sibling doesn't mask the real
                    # reason the session ended.
                    await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Best-effort link paint on any exit (clean close, abrupt
            # close, exception, cancellation). The handler swallows its
            # own errors via `_call_link`, so a flaky callback can't
            # break session lifecycle here either.
            try:
                await self._call_link(LINK_OFFLINE)
            except Exception:
                pass

    async def _handshake(self, ws: Any) -> None:
        hello = Hello(
            device_id=self.settings.device_id,
            label=self.settings.device_label,
            psk=self.settings.holdspeak_psk.get_secret_value(),
            version=DEVICE_HANDSHAKE_VERSION,
        )
        # PSK is intentionally not included in the structlog field; it's
        # in the JSON payload sent on the wire only.
        self.log.info(
            "handshake.send",
            device_id=hello.device_id,
            label=hello.label,
            version=hello.version,
        )
        await ws.send(hello.model_dump_json())

        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
        except asyncio.TimeoutError as exc:
            raise RuntimeError("handshake.timeout: server didn't ack within 10 s") from exc

        if isinstance(raw, bytes):
            raise RuntimeError(f"handshake.binary: expected JSON ack, got {len(raw)}B binary")

        try:
            ack = HelloAck.model_validate_json(raw)
        except ValidationError as exc:
            raise RuntimeError(f"handshake.invalid_ack: {exc.errors()[0]}") from exc

        self.log.info(
            "connect.holdspeak.handshake.ok",
            device_id=ack.device_id,
            label=ack.label,
        )

    async def _heartbeat_sender(self, ws: Any) -> None:
        while True:
            await asyncio.sleep(self.HEARTBEAT_INTERVAL_S)
            await ws.send(Heartbeat().model_dump_json())

    async def _audio_sender(self, ws: Any) -> None:
        """Drain the audio queue, forward each chunk as a WS binary frame."""
        while True:
            chunk = await self.audio_queue.get()
            await ws.send(chunk)
            self._bytes_window += len(chunk)
            self._frames_window += 1

    async def _control_sender(self, ws: Any) -> None:
        """Drain the control queue, forward each frame as a WS text frame."""
        while True:
            payload = await self.control_queue.get()
            await ws.send(payload)
            self._maybe_track_outbound_query(payload)
            # Log a short preview without the full JSON to keep logs tidy.
            self.log.info("control.sent", preview=payload[:80])

    async def _metrics_ticker(self) -> None:
        """Emit one structured log per second when audio flowed; quiet otherwise."""
        while True:
            await asyncio.sleep(self.METRICS_INTERVAL_S)
            if self._frames_window:
                self.log.info(
                    "audio.bytes_forwarded",
                    bytes_forwarded=self._bytes_window,
                    frames_forwarded=self._frames_window,
                )
                self._bytes_window = 0
                self._frames_window = 0

    async def _frame_receiver(self, ws: Any) -> None:
        async for raw in ws:
            if isinstance(raw, bytes):
                # No inbound binary in the v1 protocol.
                self.log.warning("ws.binary.unexpected", bytes=len(raw))
                continue
            try:
                payload: Any = json.loads(raw)
            except json.JSONDecodeError as exc:
                self.log.warning("ws.json.invalid", error=str(exc), msg=str(raw)[:200])
                continue
            if not isinstance(payload, dict):
                self.log.warning(
                    "ws.payload.not_object",
                    payload_type=type(payload).__name__,
                )
                continue
            self._dispatch(payload)

    def _dispatch(self, payload: dict) -> None:
        msg_type = payload.get("type")
        if msg_type == "status":
            try:
                status = Status.model_validate(payload)
            except ValidationError as exc:
                self.log.warning("ws.status.invalid", error=str(exc))
                return
            text = status.text
            if self._pending_query_timeout is not None:
                text = self._truncate_query_text(text)
            self._cancel_query_timeout()
            self.log.info(
                "ws.status.recv",
                text=text,
                ttl_ms=status.ttl_ms,
            )
            # Sticky (`ttl_ms == 0`) overwrites the activity baseline;
            # flash (`ttl_ms > 0`) paints then reverts after the timeout.
            self._spawn(self._paint_activity(text, status.ttl_ms))
        elif msg_type == "error":
            try:
                err = ErrorFrame.model_validate(payload)
            except ValidationError as exc:
                self.log.warning("ws.error.invalid", error=str(exc))
                return
            self.log.warning("ws.error.recv", code=err.code, reason=err.reason)
            if err.code == "session_busy":
                # User pressed the button while another voice-typing
                # session was active. Flash "Busy" with the busy
                # symbol; HoldSpeak's next status frame will overwrite.
                self._spawn(
                    self._paint_activity(
                        "Busy",
                        ttl_ms=SESSION_BUSY_FLASH_MS,
                        symbol=_ACTIVITY_SYMBOLS["Busy"],
                    )
                )
            else:
                # Generic error — give the user a brief reason on
                # the LCD instead of just logging it.
                self._spawn(
                    self._paint_activity(
                        f"Error: {err.reason}",
                        ttl_ms=ERROR_FLASH_MS,
                        symbol=ERROR_ACTIVITY_SYMBOL,
                    )
                )
        else:
            # The protocol promises unknown control types are non-fatal.
            self.log.warning("ws.unknown.type", type=msg_type)

    def _maybe_track_outbound_query(self, payload: str) -> None:
        """Start a timeout for `query:last_segment` frames.

        V1 deliberately has no request id; any inbound `status` frame
        completes the in-flight query. That matches the HoldSpeak
        contract for AIPI-4-06 and keeps the bridge protocol additive.
        """
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            return
        if not isinstance(obj, dict):
            return
        if obj.get("type") != "query" or obj.get("name") != "last_segment":
            return
        self._cancel_query_timeout()
        task = asyncio.create_task(self._query_timeout())
        self._pending_query_timeout = task
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)

    def _cancel_query_timeout(self) -> None:
        task = self._pending_query_timeout
        self._pending_query_timeout = None
        if task is not None and not task.done():
            task.cancel()

    async def _query_timeout(self) -> None:
        try:
            await asyncio.sleep(self.QUERY_TIMEOUT_S)
        except asyncio.CancelledError:
            return
        if self._pending_query_timeout is not asyncio.current_task():
            return
        self._pending_query_timeout = None
        await self._paint_activity(
            "Query timeout",
            ttl_ms=ERROR_FLASH_MS,
            symbol=ERROR_ACTIVITY_SYMBOL,
        )

    def _truncate_query_text(self, text: str) -> str:
        """Fit a last-segment response to the LCD's empirical width."""
        if len(text) <= self.QUERY_TEXT_MAX_CHARS:
            return text
        return f"{text[: self.QUERY_TEXT_MAX_CHARS - 1]}…"

    def _spawn(self, coro: Awaitable[None]) -> None:
        """Fire-and-forget a coroutine while keeping a strong ref so
        CPython doesn't GC the Task before it runs. Used by `_dispatch`
        to launch LCD paints without blocking the frame-receive loop.
        """
        t = asyncio.create_task(coro)  # type: ignore[arg-type]
        self._pending_tasks.add(t)
        t.add_done_callback(self._pending_tasks.discard)

    async def _call_link(self, state: str) -> None:
        """Best-effort link-label paint via `on_link_update`. The handler
        is expected to swallow its own errors, but we wrap defensively
        so a flaky callback can't break session lifecycle."""
        # Track the most recent state regardless of whether the paint
        # succeeds — `republish_link_state` re-fires the paint when
        # DeviceLeg connects post-handshake.
        self._last_link_state = state
        if self.on_link_update is None:
            return
        try:
            await self.on_link_update(state)
        except Exception as exc:
            self.log.warning(
                "link.handler.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
                state=state,
            )

    async def republish_sticky_activity(self) -> None:
        """Re-paint the most recent sticky activity via `on_activity_update`.

        AIPI-4-10 companion to `republish_link_state` — same race, but
        for the bottom label. The bridge's `_paint_activity("Ready")`
        at handshake time silently no-ops if the device-leg hasn't
        yet cached `_update_screen_service`; this method re-fires the
        sticky after `on_device_ready` lands.

        Uses `_sticky_activity` (rendered text+symbol) not `_sticky_text`
        so the LVGL glyph gets re-applied. No-op if no sticky has been
        set (e.g., handshake hasn't completed yet — the next handshake
        will set it). Flash paints (ttl_ms > 0) are deliberately not
        republished — they're transient by design.
        """
        if self._sticky_activity is None:
            return
        await self._call_activity(self._sticky_activity)

    async def republish_link_state(self) -> None:
        """Re-emit the most recently set link state via `on_link_update`.

        Called by `DeviceLeg._on_connect` (via the `on_device_ready`
        callback wired in `cli.py:_run`) after `_cache_lcd_services`
        completes. Fixes the race where the initial `update_link("[OK]")`
        paint fires before the device-leg API connection has cached
        service handles — without this re-trigger, the LCD's link
        indicator gets stuck at the firmware boot-default `[--]`
        even though both legs are online (AIPI-4-08).

        No-op if no link state has been set yet (e.g., a device-leg
        connect that races *ahead* of the first handshake — the next
        handshake paint will land in order).
        """
        if self._last_link_state is None:
            return
        await self._call_link(self._last_link_state)

    async def _call_activity(self, rendered: str) -> None:
        if self.on_activity_update is None:
            return
        try:
            await self.on_activity_update(rendered)
        except Exception as exc:
            self.log.warning(
                "activity.handler.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
                rendered=rendered[:80],
            )

    async def _call_middle(self, rendered: str) -> None:
        """Paint the middle (flash) label. AIPI-4-11."""
        if self.on_middle_update is None:
            return
        try:
            await self.on_middle_update(rendered)
        except Exception as exc:
            self.log.warning(
                "middle.handler.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
                rendered=rendered[:80],
            )

    async def _paint_activity(
        self,
        text: str,
        ttl_ms: int = 0,
        *,
        symbol: str | None = None,
    ) -> None:
        """Paint to one of the LCD content slots based on lifetime.

        AIPI-4-11: persistent state and transient flashes live in
        different LCD zones now.

        `ttl_ms == 0` (sticky): paints to the BOTTOM activity slot.
            Replaces the persistent state — Recording-tick, Ready, etc.
        `ttl_ms > 0` (flash): paints to the MIDDLE flash slot. Schedules
            a clear task that empties the middle after the TTL. A new
            flash cancels any pending clear so newest-message-wins.

        Stickies and flashes never overwrite each other — they live
        in separate widgets on the firmware side. The bottom keeps
        ticking; the middle is for the transient content.
        """
        rendered = _format_activity(text, symbol)

        if ttl_ms <= 0:
            # Sticky → bottom slot.
            self._sticky_activity = rendered
            self._sticky_text = text
            await self._call_activity(rendered)
            return

        # Flash → middle slot. AIPI-4-11 v2: persists until the next
        # flash replaces it. No auto-clear timer — `ttl_ms` from the
        # protocol is honored as "this is a flash (vs. sticky)" but
        # the duration is ignored. User feedback: shorter timers felt
        # like the LCD was fidgeting; persist-until-replaced lets the
        # user read the segment naturally and reuses the middle slot
        # as a "last said" context cue.
        if self.on_middle_flash is not None:
            try:
                self.on_middle_flash(ttl_ms)
            except Exception as exc:
                self.log.warning(
                    "middle_flash.handler.error",
                    error=type(exc).__name__,
                    error_msg=str(exc)[:200],
                    ttl_ms=ttl_ms,
                )
        await self._call_middle(rendered)

    def is_in_meeting(self) -> bool:
        """True iff the sticky activity says we're in a meeting.

        HoldSpeak only emits `Recording`-prefixed status frames during
        an active meeting (per HS-14-07's status-emitter call sites:
        `Recording 12:34` updated each minute). The sticky text is a
        cheap, side-effect-free probe — no extra state to track.
        """
        text = self._sticky_text
        return text is not None and text.startswith("Recording")

    async def paint_bookmark_flash(self) -> None:
        """Flash `Bookmark` for `BOOKMARK_FLASH_MS` in the activity slot.

        Used by `DeviceLeg` when the user fires the bookmark gesture
        (left-button quick-tap during a meeting). The `_paint_activity`
        state machine handles the revert-to-sticky once the flash
        expires.
        """
        await self._paint_activity(
            "Bookmark",
            ttl_ms=BOOKMARK_FLASH_MS,
            symbol=_ACTIVITY_SYMBOLS.get("Bookmark"),
        )
