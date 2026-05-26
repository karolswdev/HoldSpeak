"""DeviceLeg — ESPHome API connection + UDP audio listener.

Owns the connection to the AIPI-Lite (via aioesphomeapi.ReconnectLogic),
the UDP audio listener (with source-IP allowlist + bind-error logging),
and the LCD service handles. Audio chunks land in `audio_queue`; control
frames the device produces (start/stop) land in `control_queue` for the
HoldSpeak leg to forward.
"""

from __future__ import annotations

import asyncio
import errno
import socket
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aioesphomeapi import APIClient, VoiceAssistantEventType
from aioesphomeapi.reconnect_logic import ReconnectLogic

from bridge.audio import AUDIO_QUEUE_MAXSIZE, CONTROL_QUEUE_MAXSIZE
from bridge.reconnect import reconnect_with_backoff
from bridge.settings import Settings
from holdspeak_proto import EventFrame, QueryFrame, StartFrame, StopFrame

# Left-button press duration (ms) at or below which a press counts as
# a "short press" — the gesture wired to the bookmark event in
# AIPI-4-01. Long-press (above this) keeps its existing AIPI-1-05
# AP-mode-entry semantics. 500 ms matches ESPHome's `binary_sensor`
# convention for tap-vs-hold UX.
BOOKMARK_PRESS_THRESHOLD_MS = 500

# AIPI-4-14: window in which a second short release counts as a
# double-tap (cycle meeting-stats gesture) rather than two separate
# bookmark events. Single-tap bookmarks now have ~window-ms latency
# while we wait to see if a second tap arrives. 700 ms matches a
# comfortable human double-tap pace — initial 400 ms was too tight
# in live use (2026-05-10 hardware verification).
LEFT_DOUBLE_TAP_WINDOW_MS = 700


class DeviceLeg:
    """Manages the ESPHome API connection.

    Story 01 opens + holds the connection. Story 02 adds the
    voice_assistant audio subscription that pushes mic frames into a
    shared `audio_queue` for the HoldSpeak leg to forward. Story 03
    plugs button mapping + control frames in alongside.
    """

    def __init__(
        self,
        settings: Settings,
        log: Any,
        *,
        audio_queue: asyncio.Queue[bytes],
        control_queue: asyncio.Queue[str],
        is_in_meeting: Callable[[], bool] | None = None,
        is_agent_waiting: Callable[[], bool] | None = None,
        paint_bookmark_flash: Callable[[], Awaitable[None]] | None = None,
        on_device_ready: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self.settings = settings
        self.log = log.bind(leg="device")
        self.audio_queue = audio_queue
        self.control_queue = control_queue
        # Bookmark-gesture wiring (AIPI-4-01). The leg-construction
        # graph is acyclic by setting these post-construction in
        # `cli.py:_run` — we can't pass `hs_leg.is_in_meeting` here
        # because hs_leg doesn't exist yet at this point in `_run`.
        # Both callbacks default to None so unit tests + the legacy
        # `_run` path work without bookmark wiring.
        self.is_in_meeting = is_in_meeting
        self.is_agent_waiting = is_agent_waiting
        self.paint_bookmark_flash = paint_bookmark_flash
        # AIPI-4-08: called from `_on_connect` after `_cache_lcd_services`
        # + `_cache_button_entities` complete. Lets HoldSpeakLeg re-fire
        # its last-known link-state paint now that the device-leg
        # service handles are cached — fixes the stuck-`[--]` race.
        self.on_device_ready = on_device_ready
        self.client = APIClient(
            address=settings.aipi_host,
            port=settings.aipi_port,
            password=settings.aipi_password or "",
        )
        self.reconnect = ReconnectLogic(
            client=self.client,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
            on_connect_error=self._on_connect_error,
            name=settings.aipi_host,
        )
        # Counter for the once-per-overflow-burst log pattern HoldSpeak uses.
        self._overflow_dropped_chunks: int = 0
        self._overflow_dropped_bytes: int = 0
        # UDP audio listener task — started in self.start(), cancelled in
        # self.stop(). The listener feeds incoming datagrams into the
        # shared audio_queue.
        self._udp_task: asyncio.Task | None = None
        # Source-IP allowlist for UDP audio. Populated by
        # `_refresh_allowed_ips` on each successful device connect;
        # the listener drops datagrams whose source IP isn't in this
        # set so a stranger on the LAN can't inject PCM that gets
        # forwarded to HoldSpeak as the user's voice. While empty
        # (pre-first-connect or a resolver wipeout), datagrams are
        # dropped silently — fail-closed is the right default here.
        self._allowed_ips: set[str] = set()
        self._unauthorized_dropped: int = 0
        # `update_screen` (bottom — persistent activity, AIPI-2-07) +
        # `update_link` (top-right link indicator, AIPI-2-07) +
        # `update_middle` (middle — transient flashes, AIPI-4-11) API
        # service handles, cached on connect so paints don't pay a
        # `list_entities_services` roundtrip each call. Invalidated on
        # disconnect; re-resolved on next `_on_connect`.
        self._update_screen_service: Any | None = None
        self._update_link_service: Any | None = None
        self._update_middle_service: Any | None = None
        # Strong-ref set for fire-and-forget tasks (e.g. session_busy
        # LCD pushback). CPython's `asyncio.create_task` returns a
        # weak-ref-collectable Task; without a held reference, GC can
        # eat the task before it runs.
        self._pending_tasks: set[asyncio.Task] = set()
        # Left-button gesture state for AIPI-4-01. `_left_button_key`
        # is the aioesphomeapi entity key (resolved on connect from
        # `list_entities_services`); state-change callbacks dispatch
        # here when their `.key` matches. `_left_button_press_at_ms`
        # is the wall-clock timestamp of the most recent press —
        # cleared on release so a press-press-release sequence
        # classifies based on the latest press only.
        # `_left_button_sim_key` (AIPI-4-07) caches the simulated
        # template binary_sensor's key so remote-fired presses
        # (`python -m bridge --press left-short`) flow through the
        # exact same classifier as real presses; absent on firmware
        # builds that pre-date AIPI-4-07.
        self._left_button_key: int | None = None
        self._left_button_sim_key: int | None = None
        self._left_button_press_at_ms: int | None = None
        # AIPI-4-14: firmware-side double-tap entity. Pulses ON when the
        # firmware's `on_multi_click` 2-tap pattern matches; bridge fires
        # the cycle event on the rising edge. Cached on connect; absent
        # on firmware builds that pre-date AIPI-4-14.
        self._left_double_tap_event_key: int | None = None
        # AIPI-4-14: when the firmware-side double-tap fires, we record
        # the timestamp here so the bridge-side single-tap classifier
        # can suppress any bookmark scheduled by the two underlying
        # press/release edges that produced the double-tap.
        self._last_double_tap_event_ms: int | None = None
        # AIPI-4-14: double-tap detection state.
        # `_left_button_last_short_release_ms` records the most recent
        # short release that is still waiting to be resolved as
        # bookmark vs double-tap. `_left_button_pending_single_tap`
        # holds the scheduled bookmark-fire task; gets cancelled if a
        # second release arrives in time.
        self._left_button_last_short_release_ms: int | None = None
        self._left_button_pending_single_tap: asyncio.Task | None = None
        # Voice-assistant capture diagnostics. Firmware owns right-button
        # hold-to-talk, but the bridge can measure whether audio arrives
        # promptly after `voice_assistant.start`.
        self._va_started_at_monotonic: float | None = None
        self._va_first_audio_logged: bool = False
        self._audio_monitor_queue: asyncio.Queue[bytes] | None = (
            asyncio.Queue(maxsize=200) if settings.audio_monitor_cmd else None
        )
        self._audio_monitor_task: asyncio.Task | None = None
        self._audio_monitor_dropped_chunks: int = 0

    async def _on_connect(self) -> None:
        self.log.info(
            "connect.device.ok",
            host=self.settings.aipi_host,
            port=self.settings.aipi_port,
        )
        # Refresh the UDP source-IP allowlist before subscribing — the
        # device may have moved to a new DHCP lease since last connect,
        # and we don't want to drop legit audio because the cached IP
        # is stale.
        await self._refresh_allowed_ips()
        # Cache the LCD service handles so push-back (status frames,
        # link transitions, session_busy) doesn't pay an
        # `list_entities_services` roundtrip per call.
        await self._cache_lcd_services()
        # Cache the left-button entity key so state-change callbacks
        # can dispatch by key without a lookup per state event.
        await self._cache_button_entities()
        # Subscribe to state changes for binary_sensor + friends so
        # the bookmark gesture (AIPI-4-01) can detect left-button
        # press/release. Failure here is logged but not fatal —
        # the bridge's audio path doesn't depend on button state.
        try:
            self.client.subscribe_states(self._handle_state_change)
        except Exception as exc:
            self.log.warning(
                "subscribe.states.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
        # AIPI-4-08: signal HoldSpeakLeg that the device is now able to
        # accept LCD paints (service handles cached above). If the
        # HoldSpeak leg handshook before us, its initial link-`[OK]`
        # paint silently no-op'd; this callback gives it a chance to
        # re-paint. Swallow handler errors — link indicator is UX,
        # not correctness.
        if self.on_device_ready is not None:
            try:
                await self.on_device_ready()
            except Exception as exc:
                self.log.warning(
                    "device_ready.handler.error",
                    error=type(exc).__name__,
                    error_msg=str(exc)[:200],
                )
        # Subscribe to voice_assistant. The `handle_start` callback
        # returns the bridge's UDP port; the device opens a UDP socket
        # to it and pushes int16-LE PCM. ESPHome's voice_assistant is
        # UDP-first — returning None from handle_start logs
        # "Server could not be started" and breaks audio silently.
        try:
            self.client.subscribe_voice_assistant(
                handle_start=self._handle_va_start,
                handle_stop=self._handle_va_stop,
            )
            self.log.info("subscribe.voice_assistant.ok")
        except Exception as exc:
            # Subscribe failure is not recoverable in-place: the WS may
            # be up + heartbeating but no audio will ever flow. Log at
            # ERROR (so it surfaces in journalctl) and disconnect so
            # `ReconnectLogic` reschedules a fresh connect attempt.
            self.log.error(
                "subscribe.voice_assistant.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:300],
            )
            try:
                await self.client.disconnect()
            except Exception:
                pass

    async def _cache_lcd_services(self) -> None:
        try:
            _, services = await self.client.list_entities_services()
        except Exception as exc:
            self.log.warning(
                "lcd.services.lookup_error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
            self._update_screen_service = None
            self._update_link_service = None
            return
        by_name = {s.name: s for s in services}
        self._update_screen_service = by_name.get("update_screen")
        self._update_link_service = by_name.get("update_link")
        self._update_middle_service = by_name.get("update_middle")
        if self._update_screen_service is None:
            self.log.warning("update_screen.service.missing")
        if self._update_link_service is None:
            # Older firmware (pre-LCD-pushback) won't have this service.
            # Bridge keeps running; link indicator just stays at whatever
            # the firmware default painted.
            self.log.warning("update_link.service.missing")
        if self._update_middle_service is None:
            # Older firmware (pre-AIPI-4-11) won't have this service.
            # Bridge falls back to painting flashes in the bottom slot
            # (same as before AIPI-4-11) — see HoldSpeakLeg fallback
            # logic.
            self.log.warning("update_middle.service.missing")

    async def _cache_button_entities(self) -> None:
        """Resolve the left-button entity keys (real + simulated).

        Entities come back from the same `list_entities_services` call
        that `_cache_lcd_services` uses; we make a separate call here
        to keep the test surface clean (mocks for one helper don't
        affect the other). Cost is one extra roundtrip per connect —
        negligible against the API's lifecycle.

        AIPI-4-07: also resolves the `left_button_sim` template
        binary_sensor (if present) so remote-fired presses dispatch
        through the same classifier as real presses. The sim entity
        is optional — pre-AIPI-4-07 firmware doesn't have it; absence
        is silent (no warning).
        """
        try:
            entities, _ = await self.client.list_entities_services()
        except Exception as exc:
            self.log.warning(
                "button.entities.lookup_error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
            self._left_button_key = None
            self._left_button_sim_key = None
            self._left_double_tap_event_key = None
            return
        self._left_button_key = None
        self._left_button_sim_key = None
        self._left_double_tap_event_key = None
        for ent in entities:
            object_id = getattr(ent, "object_id", None)
            if object_id == "left_button":
                self._left_button_key = getattr(ent, "key", None)
            elif object_id == "left_button_sim":
                self._left_button_sim_key = getattr(ent, "key", None)
            elif object_id == "left_double_tap_event":
                self._left_double_tap_event_key = getattr(ent, "key", None)
        if self._left_button_key is None:
            # Older firmware or one that doesn't expose left_button as
            # a binary_sensor — bookmark gesture won't fire from real
            # presses, but the sim path (if present) can still fire it.
            self.log.warning("left_button.entity.missing")

    def _handle_state_change(self, state: Any) -> None:
        """Dispatch aioesphomeapi state changes by entity key.

        Most state events aren't ones we care about; we filter to the
        left-button keys cached in `_cache_button_entities` (real +
        simulated, both go through the same classifier). Synchronous
        because aioesphomeapi calls callbacks sync from its
        receive-loop; we hand any async work off via `_spawn`.
        """
        key = getattr(state, "key", None)
        if key is None:
            return
        pressed = bool(getattr(state, "state", False))
        if key == self._left_double_tap_event_key:
            # AIPI-4-14: firmware-side double-tap pulse. Only fire on
            # the rising edge; the OFF transition is the firmware
            # tidying up the template binary_sensor state.
            if pressed:
                self._handle_left_double_tap_event()
            return
        if key != self._left_button_key and key != self._left_button_sim_key:
            return
        self._handle_left_button_state(pressed)

    def _handle_left_double_tap_event(self) -> None:
        """Firmware fired its native double-tap pulse — emit the
        upstream event and stamp the timestamp so the bridge-side
        single-tap classifier can suppress the bookmark that would
        otherwise have been scheduled by the two underlying release
        edges.
        """
        now_ms = int(time.time() * 1000)
        self._last_double_tap_event_ms = now_ms
        self.log.info("left_double_tap_event.received")
        # Cancel any in-flight single-tap timer.
        if self._left_button_pending_single_tap is not None:
            self._left_button_pending_single_tap.cancel()
            self._left_button_pending_single_tap = None
        self._left_button_last_short_release_ms = None
        self._spawn_double_tap_event()

    def _handle_left_button_state(self, pressed: bool) -> None:
        """Classify a left-button state edge as press or release.

        On press: stamp the press time. On release: compute the press
        duration; if ≤ `BOOKMARK_PRESS_THRESHOLD_MS`, fire the bookmark
        attempt. Long presses (above the threshold) are ignored here —
        they're owned by AIPI-1-05's AP-mode-entry firmware handler
        which doesn't depend on the bridge.
        """
        now_ms = int(time.time() * 1000)
        if pressed:
            self._left_button_press_at_ms = now_ms
            return
        # Release.
        press_at = self._left_button_press_at_ms
        self._left_button_press_at_ms = None
        if press_at is None:
            # Release without a preceding press — could be a state
            # replay on first connect, or a missed press event. Don't
            # speculatively fire a bookmark.
            return
        duration_ms = now_ms - press_at
        if duration_ms > BOOKMARK_PRESS_THRESHOLD_MS:
            return
        # AIPI-4-14: classify single vs double tap.
        last_release = self._left_button_last_short_release_ms
        if (
            last_release is not None
            and (now_ms - last_release) <= LEFT_DOUBLE_TAP_WINDOW_MS
        ):
            # Second release inside the window → double-tap. Cancel any
            # pending single-tap bookmark and fire the cycle event.
            self._left_button_last_short_release_ms = None
            if self._left_button_pending_single_tap is not None:
                self._left_button_pending_single_tap.cancel()
                self._left_button_pending_single_tap = None
            self._spawn_double_tap_event()
            return
        # First short release: stamp it and schedule the bookmark
        # fire after the double-tap window. A second release in the
        # window will cancel this task.
        self._left_button_last_short_release_ms = now_ms
        self._left_button_pending_single_tap = asyncio.create_task(
            self._delayed_single_tap()
        )
        self._pending_tasks.add(self._left_button_pending_single_tap)
        self._left_button_pending_single_tap.add_done_callback(
            self._pending_tasks.discard
        )

    async def _delayed_single_tap(self) -> None:
        """Bookmark-fire scheduled `LEFT_DOUBLE_TAP_WINDOW_MS` after a
        short release. If a second release arrives inside the window
        OR the firmware-side double-tap event fires (AIPI-4-14
        on_multi_click), this task is cancelled and the double-tap
        path fires instead.
        """
        try:
            await asyncio.sleep(LEFT_DOUBLE_TAP_WINDOW_MS / 1000.0)
        except asyncio.CancelledError:
            return
        self._left_button_last_short_release_ms = None
        self._left_button_pending_single_tap = None
        # AIPI-4-14: defensive — if the firmware-side double-tap fired
        # within the past second, the two underlying release edges
        # already produced this scheduled bookmark; suppress it.
        if self._last_double_tap_event_ms is not None:
            now_ms = int(time.time() * 1000)
            if now_ms - self._last_double_tap_event_ms <= 1000:
                self.log.info("single_tap.suppressed.recent_double_tap")
                return
        await self._fire_single_tap_attempt()

    async def _fire_single_tap_attempt(self) -> None:
        """Resolve a left-button single tap.

        In a meeting, the single tap is the existing bookmark gesture.
        Outside a meeting, AIPI-4-06 uses the same gesture to ask
        HoldSpeak for the most recent segment and lets the normal
        status-frame LCD path paint the reply.
        """
        if self.is_in_meeting is None:
            self.log.info(
                "event.suppressed",
                gesture="left_single_tap",
                reason="meeting_state_unavailable",
            )
            return
        if self.is_in_meeting():
            await self._fire_bookmark_attempt()
            return
        if self.is_agent_waiting is not None and self.is_agent_waiting():
            self._enqueue_control(
                QueryFrame(name="agent_question", at=int(time.time() * 1000)),
                kind="query",
            )
            self.log.info("query.agent_question.emitted")
            return
        self._enqueue_control(
            QueryFrame(name="last_segment", at=int(time.time() * 1000)),
            kind="query",
        )
        self.log.info("query.last_segment.emitted")

    def _spawn_double_tap_event(self) -> None:
        """Fire-and-forget the double-tap event (AIPI-4-14)."""
        t = asyncio.create_task(self._fire_double_tap_event())
        self._pending_tasks.add(t)
        t.add_done_callback(self._pending_tasks.discard)

    async def _fire_double_tap_event(self) -> None:
        """Emit meeting cycle or agent-target cycle for a double tap."""
        if self.is_in_meeting is None:
            self.log.info(
                "event.suppressed",
                gesture="double_left_click",
                reason="meeting_state_unavailable",
            )
            return
        if self.is_in_meeting():
            self._enqueue_control(
                EventFrame(name="double_left_click", at=time.time()),
                kind="event",
            )
            self.log.info("event.double_left_click.emitted")
            return
        if self.is_agent_waiting is not None and self.is_agent_waiting():
            self._enqueue_control(
                QueryFrame(name="agent_next", at=int(time.time() * 1000)),
                kind="query",
            )
            self.log.info("query.agent_next.emitted")
            return
        self.log.info(
            "event.suppressed",
            gesture="double_left_click",
            reason="not_in_meeting",
        )

    def _spawn_bookmark_attempt(self) -> None:
        """Fire-and-forget the bookmark attempt with strong-ref tracking.

        Held in `_pending_tasks` so CPython doesn't GC the task before
        it runs; auto-removed on done.
        """
        t = asyncio.create_task(self._fire_bookmark_attempt())
        self._pending_tasks.add(t)
        t.add_done_callback(self._pending_tasks.discard)

    async def _fire_bookmark_attempt(self) -> None:
        """Emit a bookmark `EventFrame` if we're in a meeting; suppress otherwise.

        Gating is via the injected `is_in_meeting` callback — see
        `HoldSpeakLeg.is_in_meeting`. The wire event name is
        `long_press` (HoldSpeak's HS-14-07 vocabulary, baked before
        we shipped a gesture); local naming is `bookmark`. Renaming
        the wire event would require a paired HoldSpeak protocol-doc
        story.
        """
        if self.is_in_meeting is None or not self.is_in_meeting():
            self.log.info(
                "event.suppressed",
                gesture="bookmark",
                reason="not_in_meeting",
            )
            return
        self._enqueue_control(
            EventFrame(name="long_press", at=time.time()),
            kind="event",
        )
        self.log.info("event.bookmark.emitted")
        if self.paint_bookmark_flash is not None:
            try:
                await self.paint_bookmark_flash()
            except Exception as exc:
                self.log.warning(
                    "event.bookmark.flash_error",
                    error=type(exc).__name__,
                    error_msg=str(exc)[:200],
                )

    async def _handle_va_start(
        self,
        conversation_id: str,
        sample_rate: int,
        audio_settings: Any,
        wakeword: str | None,
    ) -> int | None:
        """Called when the device fires `voice_assistant.start`.

        Translates into a WS `start` control frame that claims a
        HoldSpeak voice-typing session. Returns the bridge's UDP audio
        port — ESPHome's voice_assistant is UDP-first, so the device
        sends mic frames as datagrams to that port. The bridge's
        `_udp_listener` task drains them into `audio_queue`.
        """
        self.log.info(
            "device.voice_assistant.start",
            conversation_id=conversation_id,
            sample_rate=sample_rate,
            udp_audio_port=self.settings.udp_audio_port,
        )
        self._va_started_at_monotonic = time.monotonic()
        self._va_first_audio_logged = False
        self._enqueue_control(StartFrame(), kind="start")
        return self.settings.udp_audio_port

    async def _handle_va_stop(self, cancelled: bool) -> None:
        """Called when the device fires `voice_assistant.stop`.

        Sends a WS `stop` control frame so HoldSpeak transcribes the
        captured audio and types it on the host. Also signals
        `VOICE_ASSISTANT_RUN_END` to the firmware so its `on_end`
        trigger fires — that's how the firmware re-arms `voice_assistant.start`
        in continuous mode (`aipi.yaml` `voice_assistant.on_end`).
        """
        duration_ms = None
        if self._va_started_at_monotonic is not None:
            duration_ms = int((time.monotonic() - self._va_started_at_monotonic) * 1000)
        self.log.info(
            "device.voice_assistant.stop",
            cancelled=cancelled,
            capture_duration_ms=duration_ms,
            first_audio_seen=self._va_first_audio_logged,
        )
        self._va_started_at_monotonic = None
        self._enqueue_control(StopFrame(), kind="stop")
        try:
            self.client.send_voice_assistant_event(
                VoiceAssistantEventType.VOICE_ASSISTANT_RUN_END, {}
            )
        except Exception as exc:
            self.log.warning(
                "device.run_end.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )

    def _enqueue_control(self, frame: Any, *, kind: str) -> None:
        """Put a control frame onto the outbound queue. Drop + log on overflow."""
        try:
            self.control_queue.put_nowait(frame.model_dump_json())
        except asyncio.QueueFull:
            self.log.warning(
                "control.queue.full",
                frame_type=kind,
                queue_max=CONTROL_QUEUE_MAXSIZE,
            )

    async def update_screen(self, msg: str) -> None:
        """Bottom-label paint via the firmware's `update_screen` API service.

        Carries HoldSpeak's status text + the bridge's chosen activity
        symbol. Failures are logged but never raised — the LCD is a UX
        hint, not a correctness invariant.
        """
        svc = self._update_screen_service
        if svc is None:
            self.log.warning("update_screen.skip", reason="service not cached")
            return
        try:
            await self.client.execute_service(service=svc, data={"msg": msg})
            self.log.info("update_screen.ok", msg=msg[:60])
        except Exception as exc:
            self.log.warning(
                "update_screen.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
                msg=msg[:60],
            )

    async def update_middle(self, text: str) -> None:
        """Middle-label paint via the firmware's `update_middle` API
        service (AIPI-4-11). Carries transient flashes (per-segment
        transcript, bookmark, error) that previously overwrote the
        Recording-tick in the bottom label. Empty string clears.
        """
        svc = self._update_middle_service
        if svc is None:
            # Older firmware (pre-AIPI-4-11) doesn't have this service.
            # Caller is responsible for falling back to update_screen
            # if it cares — we just silently skip.
            return
        try:
            await self.client.execute_service(service=svc, data={"msg": text})
            self.log.info("update_middle.ok", msg=text[:60])
        except Exception as exc:
            self.log.warning(
                "update_middle.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
                msg=text[:60],
            )

    async def update_link(self, state: str) -> None:
        """Top-right link-indicator paint via the firmware's `update_link`
        API service. Bridge calls this on every WS state transition;
        firmware never paints `link_label` on its own.
        """
        svc = self._update_link_service
        if svc is None:
            # Either the firmware predates the link-pushback story or
            # the service-list roundtrip failed on this connect. Skip
            # silently the second time + onward — the cache_lcd_services
            # call already warned.
            return
        try:
            await self.client.execute_service(service=svc, data={"msg": state})
            self.log.info("update_link.ok", state=state)
        except Exception as exc:
            self.log.warning(
                "update_link.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
                state=state,
            )

    def _enqueue_audio_bytes(self, data: bytes) -> None:
        """Push-to-queue path for incoming UDP audio chunks."""
        if not data:
            return
        if (
            self._va_started_at_monotonic is not None
            and not self._va_first_audio_logged
        ):
            self._va_first_audio_logged = True
            self.log.info(
                "audio.first_chunk",
                bytes=len(data),
                ms_after_va_start=int(
                    (time.monotonic() - self._va_started_at_monotonic) * 1000
                ),
            )
        self._enqueue_audio_monitor_bytes(data)
        try:
            self.audio_queue.put_nowait(data)
            if self._overflow_dropped_chunks:
                # Drained — emit one summary log per overflow burst.
                self.log.warning(
                    "audio.queue.overflow.recovered",
                    dropped_chunks=self._overflow_dropped_chunks,
                    dropped_bytes=self._overflow_dropped_bytes,
                )
                self._overflow_dropped_chunks = 0
                self._overflow_dropped_bytes = 0
        except asyncio.QueueFull:
            self._overflow_dropped_chunks += 1
            self._overflow_dropped_bytes += len(data)
            # Throttle log to once per 100 dropped chunks so a long
            # HoldSpeak outage doesn't flood the log.
            if self._overflow_dropped_chunks == 1 or self._overflow_dropped_chunks % 100 == 0:
                self.log.warning(
                    "audio.queue.overflow",
                    dropped_chunks=self._overflow_dropped_chunks,
                    dropped_bytes=self._overflow_dropped_bytes,
                    queue_max=AUDIO_QUEUE_MAXSIZE,
                )

    def _enqueue_audio_monitor_bytes(self, data: bytes) -> None:
        queue = self._audio_monitor_queue
        if queue is None:
            return
        try:
            queue.put_nowait(data)
            if self._audio_monitor_dropped_chunks:
                self.log.warning(
                    "audio.monitor.overflow.recovered",
                    dropped_chunks=self._audio_monitor_dropped_chunks,
                )
                self._audio_monitor_dropped_chunks = 0
        except asyncio.QueueFull:
            self._audio_monitor_dropped_chunks += 1
            if (
                self._audio_monitor_dropped_chunks == 1
                or self._audio_monitor_dropped_chunks % 100 == 0
            ):
                self.log.warning(
                    "audio.monitor.overflow",
                    dropped_chunks=self._audio_monitor_dropped_chunks,
                    queue_max=queue.maxsize,
                )

    async def _audio_monitor_session(self) -> None:
        """Mirror accepted device PCM to an operator-provided debug command."""
        queue = self._audio_monitor_queue
        command = self.settings.audio_monitor_cmd
        if queue is None or not command:
            return

        self.log.info("audio.monitor.start", command=command)
        proc = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
        )
        try:
            assert proc.stdin is not None
            while True:
                chunk = await queue.get()
                proc.stdin.write(chunk)
                try:
                    await asyncio.wait_for(proc.stdin.drain(), timeout=1.0)
                except asyncio.TimeoutError:
                    self.log.warning("audio.monitor.slow")
        except (BrokenPipeError, ConnectionResetError) as exc:
            self.log.warning(
                "audio.monitor.closed",
                error=type(exc).__name__,
                returncode=proc.returncode,
            )
        except asyncio.CancelledError:
            raise
        finally:
            if proc.stdin is not None and not proc.stdin.is_closing():
                proc.stdin.close()
                try:
                    await proc.stdin.wait_closed()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            if proc.returncode is None:
                try:
                    proc.terminate()
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
            self.log.info("audio.monitor.stop", returncode=proc.returncode)

    async def _refresh_allowed_ips(self) -> None:
        """Resolve `aipi_host` and update the UDP source-IP allowlist.

        Runs `getaddrinfo` in the default executor — mDNS resolution can
        block for a second or two and we don't want to stall the event
        loop on every reconnect. On resolver error the existing set is
        preserved (better than wiping to empty on a transient hiccup).
        """
        loop = asyncio.get_running_loop()
        host = self.settings.aipi_host
        try:
            infos = await loop.run_in_executor(
                None,
                lambda: socket.getaddrinfo(host, None, type=socket.SOCK_DGRAM),
            )
        except OSError as exc:
            self.log.warning(
                "udp.allowlist.resolve_error",
                host=host,
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
            return
        new_set = {info[4][0] for info in infos}
        if new_set != self._allowed_ips:
            self.log.info("udp.allowlist", host=host, ips=sorted(new_set))
        self._allowed_ips = new_set

    async def _udp_listener_session(self) -> None:
        """One bind+listen lifecycle for the UDP audio socket.

        ESPHome's voice_assistant.start tells the device to push
        int16-LE PCM datagrams to the port we returned from
        handle_va_start. The bridge accepts datagrams only from IPs in
        `_allowed_ips` (populated by `_refresh_allowed_ips` per device
        connect) so a stranger on the LAN can't inject PCM that gets
        forwarded to HoldSpeak as the user's voice.

        Raises on errors so the surrounding `reconnect_with_backoff`
        retries after a delay (transient bind failures, recvfrom OS
        errors). Cancellation propagates so `stop()` tears it down
        cleanly.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # SO_REUSEADDR lets the bridge rebind through TIME_WAIT after a
        # crash/restart — without it we'd hit EADDRINUSE for ~60s.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", self.settings.udp_audio_port))
        except OSError as exc:
            sock.close()
            # Surface bind failures as a structured ERROR with a
            # remediation hint. The default `udp.error` warning that
            # `reconnect_with_backoff` would log on retry is too
            # generic to act on — a port conflict and a transient
            # OSError look identical.
            if exc.errno == errno.EADDRINUSE:
                self.log.error(
                    "udp.bind.in_use",
                    port=self.settings.udp_audio_port,
                    hint=(
                        "Another process is already bound to UDP "
                        f"{self.settings.udp_audio_port}. Check with "
                        "`ss -ulnp | grep "
                        f"{self.settings.udp_audio_port}`, or set "
                        "UDP_AUDIO_PORT in bridge.env to a free port."
                    ),
                    error_msg=str(exc)[:200],
                )
            elif exc.errno == errno.EACCES:
                self.log.error(
                    "udp.bind.permission_denied",
                    port=self.settings.udp_audio_port,
                    hint=(
                        f"UDP {self.settings.udp_audio_port} requires "
                        "elevated privileges (likely <1024). Pick a "
                        "port ≥ 1024 in UDP_AUDIO_PORT."
                    ),
                    error_msg=str(exc)[:200],
                )
            else:
                self.log.error(
                    "udp.bind.error",
                    port=self.settings.udp_audio_port,
                    errno=exc.errno,
                    error_msg=str(exc)[:200],
                )
            raise
        sock.setblocking(False)
        loop = asyncio.get_running_loop()
        self.log.info("udp.listening", port=self.settings.udp_audio_port)
        try:
            while True:
                data, addr = await loop.sock_recvfrom(sock, 4096)
                src_ip = addr[0]
                if src_ip not in self._allowed_ips:
                    # Empty allowlist (pre-first-connect) or alien
                    # sender. Either way: drop. Throttled log so a
                    # noisy LAN doesn't flood stdout.
                    self._unauthorized_dropped += 1
                    if (
                        self._unauthorized_dropped == 1
                        or self._unauthorized_dropped % 100 == 0
                    ):
                        self.log.warning(
                            "udp.unauthorized_drop",
                            src=src_ip,
                            dropped=self._unauthorized_dropped,
                            allowlist=sorted(self._allowed_ips),
                        )
                    continue
                self._enqueue_audio_bytes(data)
        finally:
            sock.close()

    async def _on_disconnect(self, expected: bool) -> None:
        self.log.warning("disconnect.device", expected=expected)
        # Invalidate cached service handles + button entity keys —
        # the next connect will re-resolve via `_cache_lcd_services`
        # / `_cache_button_entities`.
        self._update_screen_service = None
        self._update_link_service = None
        self._update_middle_service = None
        self._left_button_key = None
        self._left_button_sim_key = None
        self._left_button_press_at_ms = None

    async def _on_connect_error(self, exc: Exception) -> None:
        self.log.warning(
            "connect.device.error",
            error=type(exc).__name__,
            error_msg=str(exc)[:300],
        )

    async def start(self) -> None:
        if self._audio_monitor_queue is not None:
            self._audio_monitor_task = asyncio.create_task(
                self._audio_monitor_session(),
                name="audio_monitor",
            )
        # Start UDP listener BEFORE the device connects so it's ready
        # when the device fires its first voice_assistant.start. Wrapped
        # in `reconnect_with_backoff` so a transient OSError (bind race
        # on restart, recvfrom failure under load) doesn't permanently
        # silence audio — the helper retries the whole bind+listen
        # lifecycle with the same exponential schedule the WS leg uses.
        self._udp_task = asyncio.create_task(
            reconnect_with_backoff(
                self._udp_listener_session, name="udp", log=self.log
            ),
            name="udp_audio_listener",
        )
        await self.reconnect.start()

    async def stop(self) -> None:
        if (
            self._audio_monitor_task is not None
            and not self._audio_monitor_task.done()
        ):
            self._audio_monitor_task.cancel()
            try:
                await self._audio_monitor_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._udp_task is not None and not self._udp_task.done():
            self._udp_task.cancel()
            try:
                await self._udp_task
            except (asyncio.CancelledError, Exception):
                pass
        try:
            await self.reconnect.stop()
        except Exception as exc:
            self.log.warning("stop.device.error", error=str(exc))
