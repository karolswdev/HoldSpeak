"""``/api/devices/audio`` WebSocket route — remote PCM ingest.

A device opens the WebSocket, sends a single JSON
``DeviceHandshake`` frame, then alternates JSON control frames
(``start`` / ``stop`` / ``heartbeat``) with binary int16 LE PCM
frames. The server registers the device, drives a per-device
:class:`RemoteAudioRecorder`, and hands assembled audio off to the
caller-supplied ``on_chunk`` consumer (set by HS-14-05 /
HS-14-06).

This module owns nothing but routing + dispatch — auth, registry,
backpressure, and audio decoding all live in
:mod:`holdspeak.device_audio`.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Optional, TYPE_CHECKING

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from .audio import AudioSource
from .device_audio import (
    DeviceRegistry,
    DuplicateLabelError,
    HandshakeError,
    InvalidHandshakeError,
    PskMismatchError,
    WS_CLOSE_DUPLICATE_LABEL,
    WS_CLOSE_INVALID_HANDSHAKE,
    parse_handshake,
    verify_psk,
)
from .logging_config import get_logger

if TYPE_CHECKING:
    from .device_status import DeviceStatusEmitter

log = get_logger("device_audio_ws")

PskProvider = Callable[[], str]
ChunkConsumer = Callable[[str, np.ndarray], None]
# Voice-typing handlers (HS-14-05). When set, the dispatcher
# delegates start/stop semantics to these instead of calling
# ``recorder.start_recording`` / ``recorder.stop_recording``
# directly. ``start`` returns ``False`` to signal the device that
# another session is active; ``stop`` returns the captured audio
# (or ``None`` if the session was never owned by this device).
VoiceStartHandler = Callable[[str, AudioSource], bool]
VoiceStopHandler = Callable[[str, AudioSource], Optional[np.ndarray]]
# Called from the disconnect-cleanup path so the runtime can drop
# any session this device still owns. Receives the device id only;
# the source has already been removed from the registry.
VoiceCancelHandler = Callable[[str], None]
# HS-14-07 — inbound device → server event channel. ``at`` is the
# device-side timestamp the firmware tagged the event with (any
# numeric type or ``None``); the runtime uses it as a bookmark
# anchor when ``name == "long_press"``.
EventHandler = Callable[[str, str, Optional[float]], None]


def register_device_audio_routes(
    app: Any,
    *,
    device_registry: DeviceRegistry,
    get_psk: PskProvider,
    on_chunk: Optional[ChunkConsumer] = None,
    on_voice_start: Optional[VoiceStartHandler] = None,
    on_voice_stop: Optional[VoiceStopHandler] = None,
    on_voice_cancel: Optional[VoiceCancelHandler] = None,
    status_emitter: Optional["DeviceStatusEmitter"] = None,
    on_event: Optional[EventHandler] = None,
) -> None:
    """Mount ``WebSocket /api/devices/audio`` on ``app``.

    Args:
        app: A FastAPI application.
        device_registry: Single shared registry instance.
        get_psk: Callable returning the current configured PSK.
            Called once per handshake so a freshly rotated PSK
            takes effect on the next reconnect without restarting
            the runtime.
        on_chunk: Optional consumer invoked with
            ``(device_id, audio_ndarray)`` whenever a ``stop``
            control frame produces audio. Used by integration
            tests that need raw access to the audio. When voice
            handlers are wired (HS-14-05 / HS-14-06), audio
            ownership moves to those handlers and ``on_chunk``
            is **not** invoked from the stop path.
        on_voice_start: Optional handler called on each ``start``
            control frame. Returns ``True`` when the device's
            voice-typing session was accepted; ``False`` when
            another session is already active (the WS dispatcher
            sends a ``session_busy`` error frame back). When
            unset, the dispatcher falls back to calling
            ``recorder.start_recording()`` directly.
        on_voice_stop: Optional handler called on each ``stop``
            control frame; returns the captured audio (or
            ``None``). When set, owns the audio — ``on_chunk`` is
            not invoked. When unset, the dispatcher falls back to
            calling ``recorder.stop_recording()`` and forwarding
            the result to ``on_chunk``.
    """

    @app.websocket("/api/devices/audio")
    async def _ingest(websocket: WebSocket) -> None:  # pragma: no cover - exercised via TestClient
        await _serve_device_audio(
            websocket,
            device_registry=device_registry,
            get_psk=get_psk,
            on_chunk=on_chunk,
            on_voice_start=on_voice_start,
            on_voice_stop=on_voice_stop,
            on_voice_cancel=on_voice_cancel,
            status_emitter=status_emitter,
            on_event=on_event,
        )


async def _serve_device_audio(
    websocket: WebSocket,
    *,
    device_registry: DeviceRegistry,
    get_psk: PskProvider,
    on_chunk: Optional[ChunkConsumer],
    on_voice_start: Optional[VoiceStartHandler] = None,
    on_voice_stop: Optional[VoiceStopHandler] = None,
    on_voice_cancel: Optional[VoiceCancelHandler] = None,
    status_emitter: Optional["DeviceStatusEmitter"] = None,
    on_event: Optional[EventHandler] = None,
) -> None:
    """Drive the lifecycle of a single device-audio WebSocket connection."""

    await websocket.accept()

    device_id: Optional[str] = None
    try:
        device_id = await _do_handshake(
            websocket,
            device_registry=device_registry,
            get_psk=get_psk,
        )
    except HandshakeError as exc:
        log.info(
            "device_audio_handshake_rejected",
            extra={"close_code": exc.code, "reason": str(exc)},
        )
        await websocket.close(code=exc.code)
        return
    except DuplicateLabelError as exc:
        log.info(
            "device_audio_handshake_label_conflict",
            extra={"reason": str(exc)},
        )
        await websocket.close(code=WS_CLOSE_DUPLICATE_LABEL)
        return
    except WebSocketDisconnect:
        log.info("device_audio_handshake_disconnected_early")
        return

    log.info("device_audio_connected", extra={"device_id": device_id})

    # Outbound writer task — drains the per-connection asyncio queue
    # and sends each message over the WebSocket. The queue accepts a
    # ``None`` sentinel to break the writer cleanly on disconnect.
    out_queue: "asyncio.Queue[Optional[dict]]" = asyncio.Queue()
    loop = asyncio.get_running_loop()
    if status_emitter is not None:
        def _enqueue_status(text: str, ttl_ms: int) -> None:
            msg = {"type": "status", "text": str(text), "ttl_ms": int(ttl_ms)}
            try:
                loop.call_soon_threadsafe(out_queue.put_nowait, msg)
            except RuntimeError:
                # Loop is shutting down; drop the message.
                pass

        status_emitter.register(device_id, _enqueue_status)

    writer_task: Optional[asyncio.Task[None]] = asyncio.create_task(
        _writer_loop(websocket, out_queue, device_id=device_id)
    )

    try:
        await _dispatch_loop(
            websocket,
            device_registry=device_registry,
            device_id=device_id,
            on_chunk=on_chunk,
            on_voice_start=on_voice_start,
            on_voice_stop=on_voice_stop,
            on_event=on_event,
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception(
            "device_audio_ws_error",
            extra={"device_id": device_id},
        )
    finally:
        if status_emitter is not None:
            status_emitter.unregister(device_id)
        await out_queue.put(None)
        try:
            await asyncio.wait_for(writer_task, timeout=1.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            writer_task.cancel()
        _teardown(device_registry, device_id, on_voice_cancel=on_voice_cancel)


async def _writer_loop(
    websocket: WebSocket,
    queue: "asyncio.Queue[Optional[dict]]",
    *,
    device_id: str,
) -> None:
    """Pull messages from ``queue`` and write them as JSON frames.

    Exits on the ``None`` sentinel or on any send error. Errors do
    not bubble — the read loop will detect the disconnect.
    """
    while True:
        msg = await queue.get()
        if msg is None:
            return
        try:
            await websocket.send_json(msg)
        except Exception:
            log.info(
                "device_audio_status_send_failed",
                extra={"device_id": device_id},
            )
            return


async def _do_handshake(
    websocket: WebSocket,
    *,
    device_registry: DeviceRegistry,
    get_psk: PskProvider,
) -> str:
    """Run the handshake; on success return the registered device id."""

    first = await websocket.receive()
    msg_type = first.get("type")
    if msg_type == "websocket.disconnect":
        raise InvalidHandshakeError("disconnected before handshake")

    text = first.get("text")
    if text is None:
        raise InvalidHandshakeError("first frame must be JSON text")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidHandshakeError(f"invalid handshake JSON: {exc}") from exc

    handshake = parse_handshake(payload)

    expected_psk = get_psk() or ""
    if not verify_psk(handshake.psk, expected_psk):
        raise PskMismatchError("psk mismatch")

    descriptor = device_registry.register(handshake.device_id, handshake.label)

    await websocket.send_json(
        {"type": "hello-ack", "device_id": descriptor.id, "label": descriptor.label}
    )
    return descriptor.id


async def _dispatch_loop(
    websocket: WebSocket,
    *,
    device_registry: DeviceRegistry,
    device_id: str,
    on_chunk: Optional[ChunkConsumer],
    on_voice_start: Optional[VoiceStartHandler] = None,
    on_voice_stop: Optional[VoiceStopHandler] = None,
    on_event: Optional[EventHandler] = None,
) -> None:
    """Read frames until the peer disconnects or sends a malformed control."""

    recorder = device_registry.recorder_for(device_id)
    if recorder is None:
        # Should be impossible — registration just happened — but
        # guard anyway so a future race doesn't crash the route.
        log.error("device_audio_recorder_missing", extra={"device_id": device_id})
        return

    while True:
        msg = await websocket.receive()
        if msg.get("type") == "websocket.disconnect":
            return

        if "text" in msg and msg["text"] is not None:
            await _handle_control(
                websocket,
                msg["text"],
                device_registry=device_registry,
                device_id=device_id,
                recorder=recorder,
                on_chunk=on_chunk,
                on_voice_start=on_voice_start,
                on_voice_stop=on_voice_stop,
                on_event=on_event,
            )
            continue

        if "bytes" in msg and msg["bytes"] is not None:
            recorder.push(msg["bytes"])
            device_registry.touch(device_id)
            continue

        # Unknown frame shape — ignore but log so a misbehaving
        # client can be diagnosed.
        log.warning(
            "device_audio_unknown_frame",
            extra={"device_id": device_id, "keys": list(msg.keys())},
        )


async def _handle_control(
    websocket: WebSocket,
    raw: str,
    *,
    device_registry: DeviceRegistry,
    device_id: str,
    recorder: AudioSource,
    on_chunk: Optional[ChunkConsumer],
    on_voice_start: Optional[VoiceStartHandler],
    on_voice_stop: Optional[VoiceStopHandler],
    on_event: Optional[EventHandler] = None,
) -> None:
    try:
        control = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning(
            "device_audio_bad_control_frame",
            extra={"device_id": device_id, "reason": str(exc)},
        )
        return

    if not isinstance(control, dict):
        log.warning(
            "device_audio_bad_control_frame",
            extra={"device_id": device_id, "reason": "not a JSON object"},
        )
        return

    ctrl_type = control.get("type")

    if ctrl_type == "start":
        if on_voice_start is not None:
            try:
                accepted = on_voice_start(device_id, recorder)
            except Exception:
                log.exception(
                    "device_audio_voice_start_failed",
                    extra={"device_id": device_id},
                )
                return
            if not accepted:
                try:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "session_busy",
                            "reason": "another voice-typing session is already active",
                        }
                    )
                except Exception:
                    pass
                return
        else:
            if not recorder.is_recording:
                try:
                    recorder.start_recording()
                except Exception:
                    log.exception(
                        "device_audio_start_failed",
                        extra={"device_id": device_id},
                    )
                    return
        device_registry.touch(device_id)
        return

    if ctrl_type == "stop":
        if on_voice_stop is not None:
            try:
                audio = on_voice_stop(device_id, recorder)
            except Exception:
                log.exception(
                    "device_audio_voice_stop_failed",
                    extra={"device_id": device_id},
                )
                return
            device_registry.touch(device_id)
            # Voice handler owns the audio; ``on_chunk`` is not
            # invoked from this path.
            _ = audio
            return

        if not recorder.is_recording:
            device_registry.touch(device_id)
            return
        try:
            audio = recorder.stop_recording()
        except Exception:
            log.exception(
                "device_audio_stop_failed",
                extra={"device_id": device_id},
            )
            return
        device_registry.touch(device_id)
        if on_chunk is not None:
            try:
                on_chunk(device_id, audio)
            except Exception:
                log.exception(
                    "device_audio_on_chunk_failed",
                    extra={"device_id": device_id},
                )
        return

    if ctrl_type == "heartbeat":
        device_registry.touch(device_id)
        return

    if ctrl_type == "event":
        name = control.get("name")
        if not isinstance(name, str) or not name:
            log.warning(
                "device_audio_event_missing_name",
                extra={"device_id": device_id},
            )
            return
        raw_at = control.get("at")
        at: Optional[float]
        if isinstance(raw_at, (int, float)):
            at = float(raw_at)
        else:
            at = None
        device_registry.touch(device_id)
        if on_event is not None:
            try:
                on_event(device_id, name, at)
            except Exception:
                log.exception(
                    "device_audio_event_handler_failed",
                    extra={"device_id": device_id, "event_name": name},
                )
        return

    log.warning(
        "device_audio_unknown_control_type",
        extra={"device_id": device_id, "control_type": ctrl_type},
    )


def _teardown(
    device_registry: DeviceRegistry,
    device_id: Optional[str],
    *,
    on_voice_cancel: Optional[VoiceCancelHandler] = None,
) -> None:
    if device_id is None:
        return
    if on_voice_cancel is not None:
        try:
            on_voice_cancel(device_id)
        except Exception:
            log.exception(
                "device_audio_voice_cancel_failed",
                extra={"device_id": device_id},
            )
    recorder = device_registry.recorder_for(device_id)
    if recorder is not None and getattr(recorder, "is_recording", False):
        try:
            recorder.stop_recording()
        except Exception:
            pass
    device_registry.unregister(device_id)
    log.info("device_audio_disconnected", extra={"device_id": device_id})


__all__ = ["register_device_audio_routes"]
