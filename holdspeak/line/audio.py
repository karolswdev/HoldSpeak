"""The call's audio: two unix sockets the ``aupipe`` module connects to.

``say.sock``: our 16 kHz mono s16le PCM into the call, 20 ms frames in real
time (silence when we have nothing to say). ``heard.sock``: the caller's PCM
out of the call, 20 ms frames. The module reconnects for each call, so each
port takes a new connection whenever one comes.

The send keeps at most a small socket buffer of lead (``SEND_BUFFER``, about
125 ms), so a barge-in (``flush``) stops our voice within about that.
"""
from __future__ import annotations

import os
import socket
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from ..logging_config import get_logger

log = get_logger("line.audio")

RATE = 16000
FRAME_MS = 20
FRAME = RATE * FRAME_MS // 1000  # samples in one frame
FRAME_BYTES = FRAME * 2
#: The send buffer of ``say.sock``: the most of our voice ahead of the call.
SEND_BUFFER = 4096
#: The most PCM a ring keeps (a say longer than this is cut).
RING_SECONDS = 120.0


def resample(pcm: np.ndarray, src: int, dst: int) -> np.ndarray:
    """``pcm`` (int16 or float) from ``src`` Hz to ``dst`` Hz, same dtype.

    Polyphase (scipy) when it is installed, else linear interpolation (good
    enough for 8 ↔ 16 kHz speech)."""
    if src == dst or len(pcm) == 0:
        return pcm
    dtype = pcm.dtype
    data = pcm.astype(np.float64)
    try:
        from math import gcd

        import scipy.signal

        g = gcd(int(src), int(dst))
        out = scipy.signal.resample_poly(data, int(dst) // g, int(src) // g)
    except ImportError:
        n = int(round(len(data) * dst / src))
        out = np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data)
    if np.issubdtype(dtype, np.integer):
        return np.clip(np.round(out), -32768, 32767).astype(dtype)
    return out.astype(dtype)


def to_pcm16(audio: np.ndarray) -> np.ndarray:
    """Float audio in [-1, 1] as int16."""
    return (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)


def rms(frame: np.ndarray) -> float:
    if len(frame) == 0:
        return 0.0
    return float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))


class Ring:
    """A thread-safe queue of int16 samples, taken in whole frames.

    ``take`` always answers one whole frame (zeros fill what is missing), so
    the call hears silence, never a gap; ``feed`` takes any number of bytes
    and keeps a partial frame for the next read (a socket read can split a
    frame anywhere)."""

    def __init__(self, *, limit_seconds: float = RING_SECONDS) -> None:
        self._lock = threading.Lock()
        self._chunks: list[np.ndarray] = []
        self._size = 0
        self._limit = int(limit_seconds * RATE)
        self._partial = b""
        #: Samples ever pushed (the index of the next pushed sample).
        self.pushed = 0
        #: Samples ever taken.
        self.taken = 0

    def push(self, samples: np.ndarray) -> int:
        """Queue samples; the stream index (counted in taken samples) at
        which the first one will be taken."""
        samples = np.asarray(samples, dtype=np.int16)
        with self._lock:
            start = self.taken + self._size
            room = max(0, self._limit - self._size)
            if len(samples) > room:
                samples = samples[:room]
            if len(samples):
                self._chunks.append(samples)
                self._size += len(samples)
            self.pushed += len(samples)
            return start

    def feed(self, data: bytes) -> list[np.ndarray]:
        """Bytes from a socket in; the whole frames they complete out."""
        with self._lock:
            data = self._partial + data
            whole = len(data) // FRAME_BYTES * FRAME_BYTES
            self._partial = data[whole:]
        return [np.frombuffer(data[i:i + FRAME_BYTES], dtype=np.int16).copy() for i in range(0, whole, FRAME_BYTES)]

    def take(self, n: int = FRAME) -> np.ndarray:
        out = np.zeros(n, dtype=np.int16)
        with self._lock:
            filled = 0
            while filled < n and self._chunks:
                head = self._chunks[0]
                part = min(n - filled, len(head))
                out[filled:filled + part] = head[:part]
                filled += part
                if part == len(head):
                    self._chunks.pop(0)
                else:
                    self._chunks[0] = head[part:]
            self._size -= filled
            self.taken += n
        return out

    def pending(self) -> int:
        with self._lock:
            return self._size

    def clear(self) -> int:
        """Drop everything queued; how many samples were dropped."""
        with self._lock:
            dropped, self._size, self._chunks = self._size, 0, []
            return dropped


def _serve(path: Path) -> socket.socket:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    os.chmod(path, 0o600)
    server.listen(2)
    return server


class SayPort:
    """``say.sock``: our voice into the call, paced 20 ms frames."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.ring = Ring()
        self._server = _serve(self.path)
        self._stop = threading.Event()
        self._conn: Optional[socket.socket] = None
        self._lock = threading.Lock()
        #: (monotonic time, stream index) of the last frames sent: when a
        #: sample went into the socket (measurement and tests).
        self._sent: list[tuple[float, int]] = []
        self.connected = threading.Event()
        threading.Thread(target=self._accept, name="line-say-accept", daemon=True).start()
        threading.Thread(target=self._pace, name="line-say-pace", daemon=True).start()

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._server.accept()
            except OSError:
                return
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER)
            with self._lock:
                old, self._conn = self._conn, conn
            if old is not None:
                old.close()
            self.connected.set()

    def _pace(self) -> None:
        tick = time.monotonic()
        while not self._stop.is_set():
            with self._lock:
                conn = self._conn
            if conn is not None:
                index = self.ring.taken
                frame = self.ring.take(FRAME)
                now = time.monotonic()
                try:
                    conn.sendall(frame.tobytes())
                    self._sent.append((now, index))
                    if len(self._sent) > 3000:
                        del self._sent[:1000]
                except OSError:
                    with self._lock:
                        if self._conn is conn:
                            self._conn = None
                    self.connected.clear()
            tick += FRAME_MS / 1000
            delay = tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            elif delay < -0.2:
                tick = time.monotonic()  # we fell behind (a stall): start the clock again

    def queue(self, samples: np.ndarray) -> int:
        """Queue PCM to say; the stream index of its first sample."""
        return self.ring.push(samples)

    def sent_at(self, index: int) -> Optional[float]:
        """When stream sample ``index`` went into the socket (monotonic)."""
        for at, first in reversed(self._sent):
            if first <= index < first + FRAME:
                return at + (index - first) / RATE
        return None

    def speaking(self) -> bool:
        return self.ring.pending() > 0

    def flush(self) -> int:
        return self.ring.clear()

    def close(self) -> None:
        self._stop.set()
        try:
            self._server.close()
        except OSError:
            pass
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
        try:
            self.path.unlink()
        except OSError:
            pass


class HeardPort:
    """``heard.sock``: the caller's PCM, one callback per 20 ms frame
    (``on_frame(monotonic_time, frame)``, on the port's own thread)."""

    def __init__(self, path: Path, on_frame: Optional[Callable[[float, np.ndarray], None]] = None) -> None:
        self.path = Path(path)
        self.on_frame = on_frame
        self._server = _serve(self.path)
        self._stop = threading.Event()
        self.connected = threading.Event()
        self._conn: Optional[socket.socket] = None
        threading.Thread(target=self._accept, name="line-heard-accept", daemon=True).start()

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._server.accept()
            except OSError:
                return
            old, self._conn = self._conn, conn
            if old is not None:
                old.close()
            self.connected.set()
            threading.Thread(target=self._read, args=(conn,), name="line-heard-read", daemon=True).start()

    def _read(self, conn: socket.socket) -> None:
        ring = Ring()
        while not self._stop.is_set():
            try:
                chunk = conn.recv(65536)
            except OSError:
                break
            if not chunk:
                break
            now = time.monotonic()
            for frame in ring.feed(chunk):
                callback = self.on_frame
                if callback is not None:
                    try:
                        callback(now, frame)
                    except Exception as exc:  # one bad frame never stops the call's audio
                        log.warning(f"heard frame dropped: {exc}")
        if self._conn is conn:
            self.connected.clear()

    def close(self) -> None:
        self._stop.set()
        try:
            self._server.close()
        except OSError:
            pass
        if self._conn is not None:
            self._conn.close()
        try:
            self.path.unlink()
        except OSError:
            pass


__all__ = ["FRAME", "FRAME_BYTES", "FRAME_MS", "HeardPort", "RATE", "Ring", "SayPort", "resample", "rms", "to_pcm16"]
