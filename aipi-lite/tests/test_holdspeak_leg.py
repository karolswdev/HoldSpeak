"""Integration tests for HoldSpeakLeg.session() against a fake WS server.

Stands up a `websockets.serve` handler that mimics HoldSpeak's
`/api/devices/audio` endpoint just enough to exercise the bridge: it
ACKs the handshake, captures the frames the client sends, optionally
pushes back scripted control frames (status / error), and lets us close
cleanly or abruptly to assert the client's behavior on each.

Closes the gap where the bridge core had no automated coverage — only
the helpers (synth_sine, read_wav_pcm, _backoff_seconds) and the
Pydantic models were unit-tested.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
import structlog
import websockets

from bridge import HoldSpeakLeg, Settings


def _make_settings(port: int) -> Settings:
    """Construct Settings for a test, bypassing the local bridge.env file
    so a developer's real PSK doesn't bleed into the test process."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        holdspeak_host="127.0.0.1",
        holdspeak_port=port,
        holdspeak_psk="test-psk",
        device_id="aipi-test",
        device_label="Test",
        log_level="ERROR",
    )


class FakeHoldSpeak:
    """Minimal /api/devices/audio impl for the bridge to talk to.

    `script` is a list of dicts to JSON-send back to the client *after*
    the handshake completes — used to feed `status` / `error` frames
    into the bridge's dispatch path. `close_after_script` triggers a
    clean WS close once the script has been sent (lets us assert that
    the client returns normally on a server-initiated close).
    """

    def __init__(
        self,
        *,
        ack_label_override: str | None = None,
        script: list[dict[str, Any]] | None = None,
        close_after_script: bool = False,
        abrupt_close: bool = False,
        send_invalid_ack: bool = False,
    ) -> None:
        self.received_text: list[dict[str, Any]] = []
        self.received_binary: list[bytes] = []
        self.connections_seen = 0
        self.handshake_event = asyncio.Event()
        self.first_binary_event = asyncio.Event()
        self.first_post_handshake_text_event = asyncio.Event()
        self.script_done_event = asyncio.Event()
        self._ack_label_override = ack_label_override
        self._script = list(script or [])
        self._close_after_script = close_after_script
        self._abrupt_close = abrupt_close
        self._send_invalid_ack = send_invalid_ack

    async def handler(self, ws: Any) -> None:
        self.connections_seen += 1
        try:
            raw = await ws.recv()
        except websockets.ConnectionClosed:
            return
        hello = json.loads(raw)
        self.received_text.append(hello)

        if self._send_invalid_ack:
            await ws.send('{"this": "is not", "a": "hello-ack"}')
            self.handshake_event.set()
            return

        ack = {
            "type": "hello-ack",
            "device_id": hello["device_id"],
            "label": self._ack_label_override or hello["label"],
        }
        await ws.send(json.dumps(ack))
        self.handshake_event.set()

        for frame in self._script:
            await ws.send(json.dumps(frame))
        self.script_done_event.set()

        if self._close_after_script:
            await ws.close()
            return

        if self._abrupt_close:
            # 1011 ("internal error") → ConnectionClosedError on the
            # client side. Anything other than 1000/1001 is treated as
            # abrupt by `websockets`.
            await ws.close(code=1011, reason="server died")
            return

        try:
            async for msg in ws:
                if isinstance(msg, bytes):
                    self.received_binary.append(msg)
                    if not self.first_binary_event.is_set():
                        self.first_binary_event.set()
                else:
                    self.received_text.append(json.loads(msg))
                    if not self.first_post_handshake_text_event.is_set():
                        self.first_post_handshake_text_event.set()
        except websockets.ConnectionClosed:
            pass


async def _serve(fake: FakeHoldSpeak):
    """Bind to an ephemeral port; return (server-context-manager, port)."""
    server = await websockets.serve(fake.handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


async def _build_leg(
    port: int,
    *,
    on_link_update: Any | None = None,
    on_activity_update: Any | None = None,
    on_middle_update: Any | None = None,
) -> tuple[HoldSpeakLeg, asyncio.Queue[bytes], asyncio.Queue[str]]:
    settings = _make_settings(port)
    log = structlog.get_logger()
    audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=10)
    control_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=10)
    leg = HoldSpeakLeg(
        settings,
        log,
        audio_queue=audio_queue,
        control_queue=control_queue,
        on_link_update=on_link_update,
        on_activity_update=on_activity_update,
        on_middle_update=on_middle_update,
    )
    return leg, audio_queue, control_queue


async def _cancel(task: asyncio.Task) -> None:
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------- Handshake ----------


@pytest.mark.asyncio
async def test_session_handshake_sends_correct_hello():
    fake = FakeHoldSpeak()
    server, port = await _serve(fake)
    try:
        leg, _audio_q, _ctrl_q = await _build_leg(port)
        task = asyncio.create_task(leg.session())
        try:
            await asyncio.wait_for(fake.handshake_event.wait(), timeout=2.0)
        finally:
            await _cancel(task)
    finally:
        server.close()
        await server.wait_closed()

    assert len(fake.received_text) == 1
    hello = fake.received_text[0]
    assert hello["type"] == "hello"
    assert hello["device_id"] == "aipi-test"
    assert hello["label"] == "Test"
    assert hello["psk"] == "test-psk"
    assert hello["version"] == 1


@pytest.mark.asyncio
async def test_session_raises_on_invalid_ack():
    """If the server's hello-ack fails Pydantic validation, the session
    should raise so the outer reconnect helper backs off + retries."""
    fake = FakeHoldSpeak(send_invalid_ack=True)
    server, port = await _serve(fake)
    try:
        leg, _audio_q, _ctrl_q = await _build_leg(port)
        with pytest.raises(RuntimeError, match="handshake.invalid_ack"):
            await asyncio.wait_for(leg.session(), timeout=3.0)
    finally:
        server.close()
        await server.wait_closed()


# ---------- Audio forwarding ----------


@pytest.mark.asyncio
async def test_session_drains_pre_session_audio_then_forwards():
    """Audio that piled up *before* the session started should be
    discarded (the user wasn't speaking to HoldSpeak during the gap),
    and only audio enqueued after the handshake should be forwarded."""
    fake = FakeHoldSpeak()
    server, port = await _serve(fake)
    try:
        leg, audio_q, _ctrl_q = await _build_leg(port)
        # Pre-load audio that should be drained.
        for _ in range(3):
            audio_q.put_nowait(b"\xaa" * 320)

        task = asyncio.create_task(leg.session())
        try:
            await asyncio.wait_for(fake.handshake_event.wait(), timeout=2.0)
            # After handshake, push real audio that should arrive.
            await audio_q.put(b"\xbb" * 320)
            await asyncio.wait_for(fake.first_binary_event.wait(), timeout=2.0)
            # Give the audio-sender a beat to flush.
            await asyncio.sleep(0.05)
        finally:
            await _cancel(task)
    finally:
        server.close()
        await server.wait_closed()

    # Only post-handshake audio should have arrived; the three
    # pre-session chunks should have been drained and never sent.
    assert all(chunk == b"\xbb" * 320 for chunk in fake.received_binary)
    assert b"\xaa" * 320 not in fake.received_binary


# ---------- Control frames ----------


@pytest.mark.asyncio
async def test_session_forwards_control_frames():
    fake = FakeHoldSpeak()
    server, port = await _serve(fake)
    try:
        leg, _audio_q, ctrl_q = await _build_leg(port)
        task = asyncio.create_task(leg.session())
        try:
            await asyncio.wait_for(fake.handshake_event.wait(), timeout=2.0)
            await ctrl_q.put('{"type":"start"}')
            await asyncio.wait_for(
                fake.first_post_handshake_text_event.wait(), timeout=2.0
            )
        finally:
            await _cancel(task)
    finally:
        server.close()
        await server.wait_closed()

    # received_text[0] is the hello; subsequent text frames are control.
    control_frames = list(fake.received_text[1:])
    assert {"type": "start"} in control_frames


# ---------- Server → device dispatch ----------


@pytest.mark.asyncio
async def test_session_busy_paints_middle_with_busy_symbol():
    """AIPI-4-11: `error: session_busy` is a flash; lands in the
    middle slot, not the activity (bottom) slot."""
    fake = FakeHoldSpeak(
        script=[
            {
                "type": "error",
                "code": "session_busy",
                "reason": "another voice-typing session is already active",
            }
        ],
    )
    server, port = await _serve(fake)
    activity_paints: list[str] = []
    middle_paints: list[str] = []

    async def on_activity(rendered: str) -> None:
        activity_paints.append(rendered)

    async def on_middle(rendered: str) -> None:
        middle_paints.append(rendered)

    try:
        leg, _audio_q, _ctrl_q = await _build_leg(
            port, on_activity_update=on_activity, on_middle_update=on_middle
        )
        task = asyncio.create_task(leg.session())
        try:
            # Wait until a middle paint includes "Busy".
            for _ in range(20):
                if any("Busy" in p for p in middle_paints):
                    break
                await asyncio.sleep(0.05)
        finally:
            await _cancel(task)
    finally:
        server.close()
        await server.wait_closed()

    busy_paints = [p for p in middle_paints if "Busy" in p]
    assert busy_paints, f"no Busy paint in middle (got middle={middle_paints!r}, activity={activity_paints!r})"
    # AIPI-4-04: Busy symbol → LV_SYMBOL_WARNING. AIPI-4-11: middle slot.
    assert chr(0xF071) in busy_paints[0]


@pytest.mark.asyncio
async def test_session_paints_status_frames_to_activity():
    """Server-pushed `status` frames should call `on_activity_update`
    with the rendered `<text>  <symbol>` line."""
    fake = FakeHoldSpeak(
        script=[
            {"type": "status", "text": "Listening...", "ttl_ms": 0},
            {"type": "status", "text": "Recording 00:30", "ttl_ms": 0},
        ],
    )
    server, port = await _serve(fake)
    activity_paints: list[str] = []

    async def on_activity(rendered: str) -> None:
        activity_paints.append(rendered)

    try:
        leg, _audio_q, _ctrl_q = await _build_leg(
            port, on_activity_update=on_activity
        )
        task = asyncio.create_task(leg.session())
        try:
            await asyncio.wait_for(fake.script_done_event.wait(), timeout=2.0)
            # Give the dispatch tasks a beat to run.
            for _ in range(20):
                if any("Recording" in p for p in activity_paints):
                    break
                await asyncio.sleep(0.05)
        finally:
            await _cancel(task)
    finally:
        server.close()
        await server.wait_closed()

    # The first paint should be the post-handshake "Ready"; then the
    # two status frames in order. Symbol map: Listening → ">>",
    # Recording → " *".
    rendered_text = " | ".join(activity_paints)
    assert "Ready" in rendered_text, rendered_text
    assert "Listening...  " in activity_paints, activity_paints
    assert "Recording 00:30  " in activity_paints, activity_paints


@pytest.mark.asyncio
async def test_session_status_flash_paints_middle_persists():
    """AIPI-4-11 v2: a ttl_ms > 0 flash paints to MIDDLE and persists
    there until the next flash replaces it. Bottom slot is untouched."""
    fake = FakeHoldSpeak(
        script=[
            {"type": "status", "text": "Recording 00:30", "ttl_ms": 0},
            {"type": "status", "text": "Bookmark @ 47s", "ttl_ms": 200},
        ],
    )
    server, port = await _serve(fake)
    activity_paints: list[str] = []
    middle_paints: list[str] = []

    async def on_activity(rendered: str) -> None:
        activity_paints.append(rendered)

    async def on_middle(rendered: str) -> None:
        middle_paints.append(rendered)

    try:
        leg, _audio_q, _ctrl_q = await _build_leg(
            port,
            on_activity_update=on_activity,
            on_middle_update=on_middle,
        )
        task = asyncio.create_task(leg.session())
        try:
            await asyncio.wait_for(fake.script_done_event.wait(), timeout=2.0)
            # Wait long enough for the 200 ms flash to expire +
            # the middle-clear to fire.
            await asyncio.sleep(0.5)
        finally:
            await _cancel(task)
    finally:
        server.close()
        await server.wait_closed()

    # Bottom (activity) sticky paints: at least one Recording paint
    # (no re-paint after the flash — flash lives in the middle slot).
    recording_in_activity = [p for p in activity_paints if "Recording" in p]
    assert recording_in_activity, (
        f"expected at least one Recording sticky paint, got {activity_paints!r}"
    )
    # Middle slot saw the flash + a clear (empty string).
    bookmark_in_middle = [p for p in middle_paints if "Bookmark" in p]
    assert bookmark_in_middle, (
        f"expected flash in middle, got middle={middle_paints!r}"
    )
    # AIPI-4-11 v2: no auto-clear; the bookmark flash persists in
    # the middle until the next flash. Last middle paint is the
    # bookmark itself.
    assert any("Bookmark" in m for m in middle_paints), middle_paints


@pytest.mark.asyncio
async def test_session_paints_link_transitions():
    """Link should go connecting → online → offline across a clean
    session. AIPI-4-09: codepoints are LV_SYMBOL_REFRESH / WIFI / CLOSE."""
    from bridge import LINK_CONNECTING, LINK_OFFLINE, LINK_ONLINE

    fake = FakeHoldSpeak(close_after_script=True)
    server, port = await _serve(fake)
    link_paints: list[str] = []

    async def on_link(state: str) -> None:
        link_paints.append(state)

    try:
        leg, _audio_q, _ctrl_q = await _build_leg(
            port, on_link_update=on_link
        )
        await asyncio.wait_for(leg.session(), timeout=3.0)
    finally:
        server.close()
        await server.wait_closed()

    assert link_paints == [LINK_CONNECTING, LINK_ONLINE, LINK_OFFLINE], link_paints


@pytest.mark.asyncio
async def test_session_paints_offline_link_on_handshake_failure():
    """If the server sends an invalid ack, the session raises — but
    the LCD must still flip to LINK_OFFLINE (via the outer `finally`)
    so a user staring at the device sees the bridge has dropped the
    WS."""
    from bridge import LINK_CONNECTING, LINK_OFFLINE, LINK_ONLINE

    fake = FakeHoldSpeak(send_invalid_ack=True)
    server, port = await _serve(fake)
    link_paints: list[str] = []

    async def on_link(state: str) -> None:
        link_paints.append(state)

    try:
        leg, _audio_q, _ctrl_q = await _build_leg(
            port, on_link_update=on_link
        )
        with pytest.raises(RuntimeError):
            await asyncio.wait_for(leg.session(), timeout=3.0)
    finally:
        server.close()
        await server.wait_closed()

    assert link_paints[0] == LINK_CONNECTING
    assert link_paints[-1] == LINK_OFFLINE
    # Handshake failed → no LINK_ONLINE paint.
    assert LINK_ONLINE not in link_paints


@pytest.mark.asyncio
async def test_session_does_not_paint_link_if_callback_unset():
    """A consumer that doesn't care about link state shouldn't crash
    the session by the leg trying to call a None callback."""
    fake = FakeHoldSpeak(close_after_script=True)
    server, port = await _serve(fake)
    try:
        leg, _audio_q, _ctrl_q = await _build_leg(port)  # no callbacks
        await asyncio.wait_for(leg.session(), timeout=3.0)
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_session_returns_normally_on_clean_server_close():
    """A server-initiated clean close should not raise — the outer
    reconnect helper relies on a clean return to reset the attempt
    counter (so a brief HoldSpeak restart doesn't push backoff up)."""
    fake = FakeHoldSpeak(close_after_script=True)
    server, port = await _serve(fake)
    try:
        leg, _audio_q, _ctrl_q = await _build_leg(port)
        await asyncio.wait_for(leg.session(), timeout=3.0)
    finally:
        server.close()
        await server.wait_closed()

    assert fake.connections_seen == 1


@pytest.mark.asyncio
async def test_session_raises_on_abrupt_server_close():
    """An abrupt close (e.g. server crash → 1011) must propagate so
    `reconnect_with_backoff` engages exponential backoff. Clean close
    resets the counter; abrupt close keeps it climbing — without that
    distinction a flapping HoldSpeak would get tight retry loops."""
    fake = FakeHoldSpeak(abrupt_close=True)
    server, port = await _serve(fake)
    try:
        leg, _audio_q, _ctrl_q = await _build_leg(port)
        with pytest.raises(websockets.ConnectionClosedError):
            await asyncio.wait_for(leg.session(), timeout=3.0)
    finally:
        server.close()
        await server.wait_closed()
