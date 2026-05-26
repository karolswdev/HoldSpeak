"""Command-line entrypoints + the long-running `_run` lifecycle.

`main` is the argparse dispatcher; it routes to one of:
  - `_run` (default) — production lifecycle, both legs + signal handlers
  - `_check` — pre-flight smoke test against both endpoints
  - `_send_test_audio` — one-shot WAV → HoldSpeak (bypasses device leg)
  - `_audio_loopback` — continuous sine → HoldSpeak (bypasses device leg)
"""

from __future__ import annotations

import argparse
import asyncio
import errno
import json
import signal
import socket
import sys
import wave
from typing import Any

import structlog
import websockets
from aioesphomeapi import APIClient

from bridge.audio import (
    AUDIO_QUEUE_MAXSIZE,
    BYTES_PER_SECOND,
    CONTROL_QUEUE_MAXSIZE,
    TEST_AUDIO_CHUNK_BYTES,
    TEST_AUDIO_CHUNK_MS,
    read_wav_pcm,
    synth_sine_pcm,
)
from bridge.companion_status import CompanionStatusPoller
from bridge.device import DeviceLeg
from bridge.holdspeak import HoldSpeakLeg
from bridge.logging_setup import configure_logging
from bridge.reconnect import _close_code_reason, reconnect_with_backoff
from bridge.settings import Settings, load_settings
from holdspeak_proto import (
    DEVICE_HANDSHAKE_VERSION,
    WS_CLOSE_DUPLICATE_LABEL,
    WS_CLOSE_INVALID_HANDSHAKE,
    WS_CLOSE_PSK_MISMATCH,
    ErrorFrame,
    Hello,
    HelloAck,
    StartFrame,
    Status,
    StopFrame,
)


async def _run(settings: Settings) -> None:
    log = structlog.get_logger()
    log.info(
        "config.loaded",
        aipi_host=settings.aipi_host,
        aipi_port=settings.aipi_port,
        holdspeak_host=settings.holdspeak_host,
        holdspeak_port=settings.holdspeak_port,
        # Length, not the value — confirms a non-empty PSK was loaded
        # without writing the secret to the log.
        psk_length=len(settings.holdspeak_psk.get_secret_value()),
        device_id=settings.device_id,
        device_label=settings.device_label,
    )

    audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=AUDIO_QUEUE_MAXSIZE)
    control_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=CONTROL_QUEUE_MAXSIZE)
    device = DeviceLeg(
        settings, log, audio_queue=audio_queue, control_queue=control_queue
    )

    async def _on_link(state: str) -> None:
        await device.update_link(state)

    async def _on_activity(rendered: str) -> None:
        await device.update_screen(rendered)

    # AIPI-4-11: transient flashes go to the firmware's middle label
    # so they don't fight with the bottom's persistent state.
    async def _on_middle(rendered: str) -> None:
        await device.update_middle(rendered)

    companion = CompanionStatusPoller(settings, log, on_middle_update=_on_middle)
    holdspeak = HoldSpeakLeg(
        settings,
        log,
        audio_queue=audio_queue,
        control_queue=control_queue,
        on_link_update=_on_link,
        on_activity_update=_on_activity,
        on_middle_update=_on_middle,
        on_middle_flash=companion.hold_middle_for,
    )
    # Bookmark-gesture wiring (AIPI-4-01). Both legs exist now, so
    # close the cycle: device queries hs for "in meeting?" and asks
    # hs to paint the bookmark flash on emission. Late-bound so the
    # leg dependency graph stays acyclic at construction time.
    device.is_in_meeting = holdspeak.is_in_meeting
    device.is_agent_waiting = companion.is_agent_waiting
    device.paint_bookmark_flash = holdspeak.paint_bookmark_flash
    # Link-race fix (AIPI-4-08) + activity-race fix (AIPI-4-10): when
    # the device leg finishes caching LCD service handles, ask hs to
    # re-fire both its last link-state paint and its last sticky
    # activity. Without these, a HoldSpeak handshake that wins against
    # the device-leg connect leaves the LCD's link indicator stuck at
    # the firmware boot-default and the activity slot showing ASCII
    # `Ready` instead of the bridge's intended `Ready  <LV_SYMBOL_OK>`.
    async def _on_device_ready() -> None:
        companion.force_repaint()
        await holdspeak.republish_link_state()
        await holdspeak.republish_sticky_activity()

    device.on_device_ready = _on_device_ready

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Windows / restricted contexts — fall back to KeyboardInterrupt.
            pass

    log.info("loop.starting")

    holdspeak_task = asyncio.create_task(
        reconnect_with_backoff(holdspeak.session, name="holdspeak", log=log),
        name="holdspeak_loop",
    )
    companion_task = asyncio.create_task(
        companion.run(),
        name="companion_status_loop",
    )
    await device.start()
    log.info("loop.ready")

    try:
        await stop_event.wait()
    finally:
        log.info("shutdown.begin")
        holdspeak_task.cancel()
        companion_task.cancel()
        try:
            await device.stop()
        except Exception as exc:
            log.warning("shutdown.device.error", error=str(exc))
        try:
            await holdspeak_task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.warning("shutdown.holdspeak.error", error=str(exc))
        try:
            await companion_task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.warning("shutdown.companion.error", error=str(exc))
        log.info("shutdown.complete")


def _check_udp_port(port: int) -> str | None:
    """Try to bind UDP `port` (with SO_REUSEADDR, like the live listener)
    and immediately release. Returns None on success, an error string on
    failure (already includes a remediation hint where possible).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            return (
                f"UDP {port} already in use. Run "
                f"`ss -ulnp | grep {port}` to find the holder, or set "
                f"UDP_AUDIO_PORT in bridge.env to a free port."
            )
        if exc.errno == errno.EACCES:
            return (
                f"UDP {port} requires elevated privileges (likely <1024). "
                f"Pick a port ≥ 1024 in UDP_AUDIO_PORT."
            )
        return f"UDP {port} bind failed (errno={exc.errno}): {exc}"
    finally:
        sock.close()
    return None


async def _check(settings: Settings) -> int:
    """Connect to both endpoints, run handshake, exit 0 on success.

    "Deep check" — beyond the minimum WS handshake, also verifies:
      1. UDP audio port is bindable (catches port conflicts).
      2. Firmware has both `update_screen` and `update_link` API
         services (catches an outdated firmware before users notice
         the LCD doesn't update).
      3. HoldSpeak echoes back the configured `device_id` (catches
         a HOLDSPEAK_HOST/PORT pointing at the wrong instance).
    """
    log = structlog.get_logger()

    # ---- UDP port bindable ----
    err = _check_udp_port(settings.udp_audio_port)
    if err is not None:
        sys.stderr.write(f"ERROR: {err}\n")
        return 1
    log.info("check.udp.ok", port=settings.udp_audio_port)

    # ---- device leg ----
    device_client = APIClient(
        address=settings.aipi_host,
        port=settings.aipi_port,
        password=settings.aipi_password or "",
    )
    service_names: set[str] = set()
    try:
        await asyncio.wait_for(device_client.connect(login=True), timeout=10)
        try:
            _, services = await asyncio.wait_for(
                device_client.list_entities_services(), timeout=10
            )
            service_names = {s.name for s in services}
        except Exception as exc:
            sys.stderr.write(
                f"ERROR: device service-list failed: {type(exc).__name__}: {exc}\n"
            )
            return 1
    except Exception as exc:
        sys.stderr.write(
            f"ERROR: device endpoint failed: {type(exc).__name__}: {exc}\n"
        )
        return 1
    finally:
        try:
            await device_client.disconnect()
        except Exception:
            pass
    log.info(
        "check.device.ok",
        host=settings.aipi_host,
        services=sorted(service_names),
    )

    # Service availability — warn (not fail) when missing so a user
    # running an older firmware can still use the bridge in degraded
    # mode (no LCD pushback for the missing label).
    for required in ("update_screen", "update_link"):
        if required not in service_names:
            sys.stderr.write(
                f"WARNING: firmware missing API service `{required}`. "
                f"Bridge will run, but LCD pushback for that label is "
                f"disabled. Re-flash with the current aipi.yaml to fix.\n"
            )

    # ---- holdspeak leg ----
    url = f"ws://{settings.holdspeak_host}:{settings.holdspeak_port}/api/devices/audio"
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=2) as ws:
            hello = Hello(
                device_id=settings.device_id,
                label=settings.device_label,
                psk=settings.holdspeak_psk.get_secret_value(),
                version=DEVICE_HANDSHAKE_VERSION,
            )
            await ws.send(hello.model_dump_json())
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            if isinstance(raw, bytes):
                raise RuntimeError(f"expected JSON ack, got {len(raw)}B binary")
            ack = HelloAck.model_validate_json(raw)
            # HoldSpeak echoes back the device_id we sent. A mismatch is
            # almost certainly a config error pointing at a different
            # HoldSpeak instance — fail --check loudly so the user
            # doesn't waste time staring at "no transcript appears."
            if ack.device_id != settings.device_id:
                sys.stderr.write(
                    f"ERROR: holdspeak ack returned device_id "
                    f"{ack.device_id!r}, expected {settings.device_id!r}. "
                    f"This usually means HOLDSPEAK_HOST/PORT points at "
                    f"a different HoldSpeak instance than you intended.\n"
                )
                return 1
    except websockets.ConnectionClosed as exc:
        code, reason = _close_code_reason(exc)
        if code == WS_CLOSE_PSK_MISMATCH:
            sys.stderr.write(
                "ERROR: holdspeak endpoint rejected PSK (4003 PSK mismatch). "
                "Check HOLDSPEAK_PSK against `holdspeak device-psk show`.\n"
            )
        elif code == WS_CLOSE_DUPLICATE_LABEL:
            sys.stderr.write(
                f"ERROR: holdspeak endpoint rejected label "
                f"({settings.device_label!r} already in use, 4009).\n"
            )
        elif code == WS_CLOSE_INVALID_HANDSHAKE:
            sys.stderr.write(
                f"ERROR: holdspeak endpoint rejected handshake (4001 invalid). "
                f"Reason: {reason or 'no reason given'}\n"
            )
        else:
            sys.stderr.write(
                f"ERROR: holdspeak endpoint closed "
                f"(code={code}, reason={reason!r}).\n"
            )
        return 1
    except Exception as exc:
        sys.stderr.write(
            f"ERROR: holdspeak endpoint failed: {type(exc).__name__}: {exc}\n"
        )
        return 1
    log.info("check.holdspeak.ok", url=url)
    print("OK: udp + device + holdspeak handshake successful")
    return 0


async def _send_test_audio(settings: Settings, wav_path: str) -> int:
    """Standalone smoke-test mode: handshake → start → stream a WAV → stop → exit.

    Bypasses the device leg. Useful for verifying the HoldSpeak audio
    path in isolation. Streams the WAV at real-time pace (3200 B / 100 ms
    = 16 kHz mono int16) so HoldSpeak's 2 s buffer cap doesn't drop
    earlier audio when the file is longer than 2 s.
    """
    log = structlog.get_logger().bind(mode="send-test-audio", wav=wav_path)
    try:
        pcm = read_wav_pcm(wav_path)
    except (OSError, wave.Error, ValueError) as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    log.info(
        "test_audio.loaded",
        bytes=len(pcm),
        seconds=len(pcm) / BYTES_PER_SECOND,
    )

    url = f"ws://{settings.holdspeak_host}:{settings.holdspeak_port}/api/devices/audio"
    chunk_size = TEST_AUDIO_CHUNK_BYTES
    chunk_interval_s = TEST_AUDIO_CHUNK_MS / 1000.0

    try:
        async with websockets.connect(url, ping_interval=15, close_timeout=2) as ws:
            await ws.send(
                Hello(
                    device_id=settings.device_id,
                    label=settings.device_label,
                    psk=settings.holdspeak_psk.get_secret_value(),
                    version=DEVICE_HANDSHAKE_VERSION,
                ).model_dump_json()
            )
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            HelloAck.model_validate_json(raw)
            log.info("handshake.ok")

            await ws.send(StartFrame().model_dump_json())
            log.info("control.start.sent")

            sent = 0
            for offset in range(0, len(pcm), chunk_size):
                chunk = pcm[offset : offset + chunk_size]
                await ws.send(chunk)
                sent += len(chunk)
                await asyncio.sleep(chunk_interval_s)
            log.info("audio.streamed", bytes=sent)

            await ws.send(StopFrame().model_dump_json())
            log.info("control.stop.sent")

            # Give HoldSpeak a moment to send transcription status frames
            # back before we close. Loop briefly + log any inbound text.
            try:
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10)
                    if isinstance(raw, bytes):
                        log.warning("ws.binary.unexpected", bytes=len(raw))
                        continue
                    payload = json.loads(raw)
                    msg_type = payload.get("type")
                    if msg_type == "status":
                        status = Status.model_validate(payload)
                        log.info(
                            "ws.status.recv",
                            text=status.text,
                            ttl_ms=status.ttl_ms,
                        )
                        # The transcript snippet has a non-zero ttl; treat
                        # it as the terminal signal and exit.
                        if status.ttl_ms > 0:
                            break
                    elif msg_type == "error":
                        err = ErrorFrame.model_validate(payload)
                        log.warning("ws.error.recv", code=err.code, reason=err.reason)
            except asyncio.TimeoutError:
                log.info("test_audio.no_terminal_status")

        print("OK: test audio streamed to HoldSpeak")
        return 0
    except websockets.ConnectionClosed as exc:
        code, reason = _close_code_reason(exc)
        sys.stderr.write(
            f"ERROR: holdspeak endpoint closed (code={code}, reason={reason!r}).\n"
        )
        return 1
    except Exception as exc:
        sys.stderr.write(
            f"ERROR: send-test-audio failed: {type(exc).__name__}: {exc}\n"
        )
        return 1


async def _audio_loopback(settings: Settings) -> int:
    """Standalone debug mode: handshake → start → stream a 440 Hz sine forever.

    Use to verify the WS audio path is alive without a real device. The
    sine has no semantic content, so HoldSpeak should accept it without
    decode errors and produce no transcription. Exit on Ctrl-C.
    """
    log = structlog.get_logger().bind(mode="audio-loopback")
    sine = synth_sine_pcm(freq_hz=440.0, duration_s=1.0)
    log.info("loopback.ready", chunk_bytes=len(sine), freq_hz=440.0)

    url = f"ws://{settings.holdspeak_host}:{settings.holdspeak_port}/api/devices/audio"
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    try:
        async with websockets.connect(url, ping_interval=15, close_timeout=2) as ws:
            await ws.send(
                Hello(
                    device_id=settings.device_id,
                    label=settings.device_label,
                    psk=settings.holdspeak_psk.get_secret_value(),
                    version=DEVICE_HANDSHAKE_VERSION,
                ).model_dump_json()
            )
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            HelloAck.model_validate_json(raw)
            log.info("handshake.ok")

            await ws.send(StartFrame().model_dump_json())
            log.info("control.start.sent")

            sent_frames = 0
            while not stop_event.is_set():
                await ws.send(sine)
                sent_frames += 1
                if sent_frames % 10 == 0:
                    log.info("loopback.sent", frames=sent_frames)
                # Pace at real-time. Use a wait with timeout so Ctrl-C
                # interrupts cleanly rather than hanging on sleep.
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=1.0)
                    break
                except asyncio.TimeoutError:
                    continue

            await ws.send(StopFrame().model_dump_json())
            log.info("control.stop.sent")
        return 0
    except Exception as exc:
        sys.stderr.write(
            f"ERROR: audio-loopback failed: {type(exc).__name__}: {exc}\n"
        )
        return 1


async def _press(
    client: Any,
    services_by_name: dict,
    gesture: str,
    log: Any,
    *,
    settle_s: float | None = None,
) -> int:
    """Fire one remote-simulation gesture on an already-connected device.

    Pure-logic helper: takes a connected client + name→service map +
    a gesture string, calls the matching ESPHome simulate service
    with the right `duration_ms`. Returns 0 on success, 1 on
    missing-service / bad-gesture / execute-service error.

    Mapping:
      - `left-short`   → `simulate_left_press(duration_ms=100)`
      - `left-long`    → `simulate_left_press(duration_ms=6000)`
      - `voice-typing` → `simulate_voice_typing(duration_ms=3000)`

    `settle_s` is the wait between `execute_service` and return (so the
    integration wrapper's `disconnect()` doesn't race the firmware's
    state-publish completion — see the inline comment near the sleep).
    Default: `duration_ms / 1000 + 0.5`. Tests pass 0 to skip.
    """
    if gesture == "left-short":
        svc_name, duration_ms = "simulate_left_press", 100
    elif gesture == "left-long":
        svc_name, duration_ms = "simulate_left_press", 6000
    elif gesture == "voice-typing":
        svc_name, duration_ms = "simulate_voice_typing", 3000
    else:
        # argparse `choices=` should make this unreachable; defensive.
        log.error("press.gesture.unknown", gesture=gesture)
        return 1
    svc = services_by_name.get(svc_name)
    if svc is None:
        log.error(
            "press.service.missing",
            service=svc_name,
            hint=(
                "Flash AIPI-4-07 firmware (aipi.yaml). The simulate "
                "services + the left_button_sim binary_sensor ship "
                "together."
            ),
        )
        return 1
    try:
        await client.execute_service(service=svc, data={"duration_ms": duration_ms})
    except Exception as exc:
        log.error(
            "press.execute.error",
            service=svc_name,
            error=type(exc).__name__,
            error_msg=str(exc)[:200],
        )
        return 1
    # `execute_service` returns after queuing the frame, not after the
    # firmware finishes the script (publish ON → delay duration_ms →
    # publish OFF). If we disconnect immediately, the firmware's state
    # publishes can race the connection close and silently drop —
    # observed on hardware 2026-05-10 (state changes never reached
    # subscribed clients on a 100 ms simulate). Wait long enough for
    # the full press script to land + a 500 ms buffer for state
    # propagation, then return.
    wait = settle_s if settle_s is not None else (duration_ms / 1000.0 + 0.5)
    if wait > 0:
        await asyncio.sleep(wait)
    log.info("press.fired", gesture=gesture, duration_ms=duration_ms)
    return 0


async def _remote_press(settings: Settings, gesture: str) -> int:
    """Connect to the device, fire one gesture, disconnect.

    AIPI-4-07: dev infra for hardware verification when the device is
    out of physical reach. Doesn't touch HoldSpeak — the running
    bridge process (if any) handles wire-side emission via its own
    state-change subscription.
    """
    log = structlog.get_logger().bind(mode="remote-press", gesture=gesture)
    client = APIClient(
        address=settings.aipi_host,
        port=settings.aipi_port,
        password=settings.aipi_password or "",
    )
    try:
        await client.connect(login=True)
    except Exception as exc:
        sys.stderr.write(
            f"ERROR: connect to {settings.aipi_host}:{settings.aipi_port} "
            f"failed: {type(exc).__name__}: {exc}\n"
        )
        return 1
    try:
        try:
            _, services = await client.list_entities_services()
        except Exception as exc:
            log.error(
                "press.list_services.error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
            return 1
        services_by_name = {s.name: s for s in services}
        return await _press(client, services_by_name, gesture, log)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPI-Lite ↔ HoldSpeak bridge")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Connect to both endpoints, run handshake, exit 0 on success.",
    )
    mode.add_argument(
        "--send-test-audio",
        metavar="WAV",
        help="Stream a 16 kHz mono int16 WAV to HoldSpeak as a one-shot test, "
        "then exit. Bypasses the device leg.",
    )
    mode.add_argument(
        "--audio-loopback",
        action="store_true",
        help="Continuously stream a 440 Hz sine wave to HoldSpeak. Bypasses "
        "the device leg. Exit on Ctrl-C.",
    )
    mode.add_argument(
        "--press",
        choices=["left-short", "left-long", "voice-typing"],
        metavar="GESTURE",
        help="(AIPI-4-07) Remotely fire a gesture on the device by calling "
        "its ESPHome simulate service. Useful when the device is physically "
        "out of reach. left-short = 100 ms left-button press (bookmark "
        "gesture); left-long = 6 s left-button press (AP-mode entry); "
        "voice-typing = 3 s of audio capture. Requires firmware ≥ AIPI-4-07.",
    )
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.log_level)

    if args.check:
        return asyncio.run(_check(settings))
    if args.send_test_audio:
        return asyncio.run(_send_test_audio(settings, args.send_test_audio))
    if args.audio_loopback:
        return asyncio.run(_audio_loopback(settings))
    if args.press:
        return asyncio.run(_remote_press(settings, args.press))
    asyncio.run(_run(settings))
    return 0
