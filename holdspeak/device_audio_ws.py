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

import json
from typing import Any, Callable, Optional

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

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

log = get_logger("device_audio_ws")

PskProvider = Callable[[], str]
ChunkConsumer = Callable[[str, np.ndarray], None]


def register_device_audio_routes(
    app: Any,
    *,
    device_registry: DeviceRegistry,
    get_psk: PskProvider,
    on_chunk: Optional[ChunkConsumer] = None,
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
            control frame produces audio. HS-14-05 / HS-14-06 wire
            the voice-typing and meeting consumers here.
    """

    @app.websocket("/api/devices/audio")
    async def _ingest(websocket: WebSocket) -> None:  # pragma: no cover - exercised via TestClient
        await _serve_device_audio(
            websocket,
            device_registry=device_registry,
            get_psk=get_psk,
            on_chunk=on_chunk,
        )


async def _serve_device_audio(
    websocket: WebSocket,
    *,
    device_registry: DeviceRegistry,
    get_psk: PskProvider,
    on_chunk: Optional[ChunkConsumer],
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

    try:
        await _dispatch_loop(
            websocket,
            device_registry=device_registry,
            device_id=device_id,
            on_chunk=on_chunk,
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception(
            "device_audio_ws_error",
            extra={"device_id": device_id},
        )
    finally:
        _teardown(device_registry, device_id)


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
            _handle_control(
                msg["text"],
                device_registry=device_registry,
                device_id=device_id,
                recorder=recorder,
                on_chunk=on_chunk,
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


def _handle_control(
    raw: str,
    *,
    device_registry: DeviceRegistry,
    device_id: str,
    recorder: Any,
    on_chunk: Optional[ChunkConsumer],
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

    log.warning(
        "device_audio_unknown_control_type",
        extra={"device_id": device_id, "control_type": ctrl_type},
    )


def _teardown(device_registry: DeviceRegistry, device_id: Optional[str]) -> None:
    if device_id is None:
        return
    recorder = device_registry.recorder_for(device_id)
    if recorder is not None and getattr(recorder, "is_recording", False):
        try:
            recorder.stop_recording()
        except Exception:
            pass
    device_registry.unregister(device_id)
    log.info("device_audio_disconnected", extra={"device_id": device_id})


__all__ = ["register_device_audio_routes"]
