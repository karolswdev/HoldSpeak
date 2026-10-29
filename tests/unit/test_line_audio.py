"""The Line (2026-10-29): the audio bridge: the ring, resampling, the two
unix sockets in real time (the aupipe module's side played by the test)."""
from __future__ import annotations

import socket
import time

import numpy as np

from holdspeak.line.audio import FRAME, FRAME_BYTES, RATE, HeardPort, Ring, SayPort, resample
from tests.fixtures.fake_baresip import peak_hz, tone
from tests.fixtures.line_rig import short_dir


def test_the_ring_answers_whole_frames_and_keeps_a_split_frame() -> None:
    ring = Ring()
    first = ring.push(np.arange(500, dtype=np.int16))
    assert first == 0 and ring.pending() == 500
    frame = ring.take()
    assert len(frame) == FRAME and frame[0] == 0 and frame[-1] == FRAME - 1
    tail = ring.take()
    assert list(tail[:180]) == list(range(320, 500)) and not tail[180:].any()  # silence, never a gap
    assert ring.push(np.ones(10, dtype=np.int16)) == 2 * FRAME
    assert ring.clear() == 10 and ring.pending() == 0
    pcm = np.arange(FRAME * 2, dtype=np.int16).tobytes()
    feeder = Ring()
    assert feeder.feed(pcm[:100]) == [] and len(feeder.feed(pcm[100:700])) == 1
    rest = feeder.feed(pcm[700:])
    assert len(rest) == 1 and rest[0][-1] == FRAME * 2 - 1


def test_resampling_keeps_the_tone_between_8_16_and_24_khz() -> None:
    voice = tone(440.0, 500)
    down = resample(voice, RATE, 8000)
    assert len(down) == len(voice) // 2 and down.dtype == np.int16
    assert abs(peak_hz(resample(down, 8000, RATE)) - 440.0) < 5
    pocket = np.sin(2 * np.pi * 440.0 * np.arange(12000) / 24000).astype(np.float32)
    assert len(resample(pocket, 24000, RATE)) == 8000


def _connect(path) -> socket.socket:
    for _ in range(100):
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(str(path))
            return sock
        except OSError:
            time.sleep(0.01)
    raise AssertionError("no socket")


def test_say_sock_paces_20_ms_frames_and_a_flush_stops_the_voice() -> None:
    root = short_dir()
    port = SayPort(root / "say.sock")
    module = _connect(root / "say.sock")
    try:
        port.connected.wait(2)
        port.queue(tone(1000.0, 1000))
        got, start = b"", time.monotonic()
        while time.monotonic() - start < 0.5:
            got += module.recv(65536)
        frames = len(got) // FRAME_BYTES
        # Real time: about 25 frames in 0.5 s (plus the socket's small lead), not the whole second.
        assert 15 <= frames <= 25 + 4096 // FRAME_BYTES + 2, frames
        assert port.speaking()
        port.flush()
        assert not port.speaking()
        module.settimeout(0.5)
        time.sleep(0.3)
        tail = b""
        while len(tail) < FRAME_BYTES * 10:
            tail += module.recv(65536)
        late = np.frombuffer(tail[-FRAME_BYTES * 4:], dtype=np.int16)
        assert not late.any()  # after the lead drains, silence
    finally:
        module.close()
        port.close()


def test_heard_sock_hands_each_frame_to_the_line_whatever_the_reads_split() -> None:
    root = short_dir()
    frames: list[np.ndarray] = []
    port = HeardPort(root / "heard.sock", lambda at, frame: frames.append(frame))
    module = _connect(root / "heard.sock")
    try:
        pcm = tone(700.0, 100).tobytes()  # 5 frames
        module.sendall(pcm[:333])
        time.sleep(0.05)
        module.sendall(pcm[333:])
        deadline = time.monotonic() + 2
        while len(frames) < 5 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(frames) == 5 and np.concatenate(frames).tobytes() == pcm
    finally:
        module.close()
        port.close()
