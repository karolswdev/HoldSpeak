"""The local terminal's continuous, byte-preserving stream.

The older :mod:`holdspeak.delivery.terminal` service is intentionally kept as
the snapshot/subscription compatibility path.  This module is the native live
path.  A pane has one tmux control-mode client and a bounded byte ring; each
HTTP subscriber gets a cursor into that ring.  Control mode is read-only and
uses ``ignore-size``, so merely watching a pane cannot resize its host PTY.

There is deliberately no database or ``pipe-pane`` involved here.  tmux owns
the PTY and sends ``%output`` notifications to the control client.  The only
process stopped during cleanup is that client, never the shell in the pane.
"""

from __future__ import annotations

import base64
import queue
import re
import subprocess
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional

from ..coder_steering import Runner, _default_runner

LIVE_CAPTURE_LINES = 200
LIVE_RING_MAX_BATCHES = 256
LIVE_RING_MAX_BYTES = 512 * 1024
LIVE_HEARTBEAT_SECONDS = 15.0
LIVE_IDLE_GRACE_SECONDS = 8.0
CONTROL_START_TIMEOUT_SECONDS = 5.0
CONTROL_STOP_TIMEOUT_SECONDS = 1.0


class TerminalLiveError(RuntimeError):
    """A typed refusal or transient failure before an NDJSON stream starts."""

    def __init__(self, status: str, detail: str = "") -> None:
        super().__init__(detail or status)
        self.status = status
        self.detail = detail or status


def _frame(
    *,
    status: str,
    stream_id: str,
    sequence: int,
    data: bytes | None = None,
    pane: dict[str, int] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "stream_id": stream_id,
        "sequence": int(sequence),
        "encoding": "base64",
    }
    if data is not None:
        result["data"] = base64.b64encode(data).decode("ascii")
    if pane is not None:
        result["pane"] = dict(pane)
    result.update(extra)
    return result


def decode_control_output(value: bytes | str) -> bytes:
    """Decode tmux control-mode's escaped-octal output payload.

    Control mode writes one escaped line per notification.  In particular,
    bytes above ASCII may be represented as ``\\ooo`` and need not be valid
    UTF-8.  Decode the escapes as bytes and leave every other byte untouched.
    """

    raw = value.encode("utf-8", "surrogateescape") if isinstance(value, str) else bytes(value)
    out = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] != 0x5C:  # backslash
            out.append(raw[index])
            index += 1
            continue
        if index + 3 < len(raw) and all(0x30 <= item <= 0x37 for item in raw[index + 1 : index + 4]):
            out.append(int(raw[index + 1 : index + 4], 8))
            index += 4
            continue
        # tmux escapes a literal backslash as ``\\\\``.  A malformed
        # escape remains byte-honest instead of being silently discarded.
        if index + 1 < len(raw) and raw[index + 1] == 0x5C:
            out.append(0x5C)
            index += 2
            continue
        out.append(raw[index])
        index += 1
    return bytes(out)


def _capture_snapshot(
    pane_id: str,
    *,
    runner: Optional[Runner],
    lines: int,
) -> tuple[bytes, dict[str, int] | None]:
    """Capture ANSI screen bytes and geometry through separate read-only tmux calls."""

    run = runner or _default_runner
    try:
        captured = run(
            [
                "tmux",
                "capture-pane",
                "-p",
                "-e",
                "-t",
                pane_id,
                "-S",
                f"-{max(1, min(int(lines), LIVE_CAPTURE_LINES))}",
            ]
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TerminalLiveError("stream_unavailable", str(exc)) from exc
    if captured.returncode != 0:
        detail = (captured.stderr or "").strip() or "tmux refused capture"
        raise TerminalLiveError("target_gone", detail)
    text = captured.stdout or ""
    if isinstance(text, bytes):
        screen = text.rstrip(b"\n")
    else:
        screen = str(text).encode("utf-8", "surrogateescape").rstrip(b"\n")

    geometry: dict[str, int] | None = None
    try:
        sized = run(
            [
                "tmux",
                "display-message",
                "-p",
                "-t",
                pane_id,
                "#{pane_width} #{pane_height} #{cursor_x} #{cursor_y}",
            ]
        )
        if sized.returncode == 0:
            parts = (sized.stdout or b"" if isinstance(sized.stdout, bytes) else str(sized.stdout or "")).split()
            if len(parts) == 4:
                width, height, cursor_x, cursor_y = (int(part) for part in parts)
                geometry = {
                    "width": width,
                    "height": height,
                    "cursor_x": cursor_x,
                    "cursor_y": cursor_y,
                }
    except (OSError, subprocess.TimeoutExpired, TypeError, ValueError):
        # Geometry is additive.  A real screen remains streamable when this
        # optional read is unavailable.
        geometry = None
    return screen, geometry


def _read_geometry(
    pane_id: str, *, runner: Optional[Runner]
) -> dict[str, int] | None:
    """Read host dimensions/cursor and alternate-screen state without a write."""
    run = runner or _default_runner
    try:
        sized = run(
            [
                "tmux",
                "display-message",
                "-p",
                "-t",
                pane_id,
                "#{pane_width} #{pane_height} #{cursor_x} #{cursor_y} #{alternate_on}",
            ]
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if sized.returncode != 0:
        return None
    raw_value = sized.stdout or b""
    raw = raw_value.decode("utf-8", "surrogateescape") if isinstance(raw_value, bytes) else str(raw_value)
    return _parse_geometry(raw)


def _parse_geometry(raw: bytes | str) -> dict[str, int] | None:
    text = raw.decode("utf-8", "surrogateescape") if isinstance(raw, bytes) else str(raw)
    parts = text.split()
    if len(parts) < 4:
        return None
    try:
        width, height, cursor_x, cursor_y = (int(part) for part in parts[:4])
    except (TypeError, ValueError):
        return None
    geometry: dict[str, int] = {
        "width": width,
        "height": height,
        "cursor_x": cursor_x,
        "cursor_y": cursor_y,
    }
    if len(parts) >= 5:
        geometry["alternate"] = 1 if str(parts[4]).strip().lower() in {"1", "on", "true"} else 0
    return geometry


def _bootstrap_snapshot(data: bytes, geometry: dict[str, int] | None) -> bytes:
    """Turn a rendered capture into a safe xterm repaint boundary.

    ``capture-pane`` is a screen projection, not an emulator reset.  Clear the
    active screen before writing it, retain the pane's alternate-screen state,
    and park the cursor where tmux reports it.  The actual PTY notifications
    that follow remain untouched bytes.
    """
    alternate = bool((geometry or {}).get("alternate"))
    mode = b"\x1b[?1049h" if alternate else b"\x1b[?1049l"
    prefix = mode + b"\x1b[2J\x1b[H"
    cursor_x = int((geometry or {}).get("cursor_x", 0)) + 1
    cursor_y = int((geometry or {}).get("cursor_y", 0)) + 1
    # Screen capture rows are a projection with LF separators.  The browser's
    # byte-mode xterm must receive CRLF rows; live PTY notifications below are
    # deliberately not normalized.
    screen = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n").replace(b"\n", b"\r\n")
    return prefix + screen + f"\x1b[{cursor_y};{cursor_x}H".encode("ascii")


class _ControlClient:
    """One tmux ``-C attach-session`` client and its output reader."""

    def __init__(
        self,
        pane_id: str,
        on_output: Callable[..., None],
        *,
        on_boundary: Callable[[], None] | None = None,
        on_closed: Callable[[], None] | None = None,
        popen_factory: Callable[..., Any] | None = None,
        command_timeout: float = CONTROL_START_TIMEOUT_SECONDS,
        lines: int = LIVE_CAPTURE_LINES,
    ) -> None:
        if not re.fullmatch(r"%[0-9]+", str(pane_id)):
            raise TerminalLiveError("target_gone", "tmux control target is not a pane id")
        self.pane_id = str(pane_id)
        self._on_output = on_output
        self._on_boundary = on_boundary
        self._on_closed = on_closed
        self._popen_factory = popen_factory or subprocess.Popen
        self._command_timeout = command_timeout
        self._lines = max(1, min(int(lines), LIVE_CAPTURE_LINES))
        self._process: Any = None
        self._reader: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._startup_ready = threading.Event()
        self._command_lock = threading.Lock()
        self._block_lock = threading.Lock()
        self._block: list[bytes] | None = None
        self._capture_boundary = False
        self._block_done: queue.Queue[tuple[bytes, ...] | BaseException] = queue.Queue(maxsize=8)
        self.error: BaseException | None = None

    def _put_block(self, value: tuple[bytes, ...] | BaseException) -> None:
        # A stale/unsolicited response must never stop the notification reader.
        try:
            self._block_done.put_nowait(value)
        except queue.Full:
            pass

    @property
    def process(self) -> Any:
        return self._process

    def start(self) -> None:
        argv = [
            "tmux",
            "-C",
            "attach-session",
            "-r",  # control client cannot type into the pane
            "-f",
            "ignore-size",  # attaching must not change the host PTY
            "-t",
            self.pane_id,
        ]
        try:
            self._process = self._popen_factory(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise TerminalLiveError("stream_unavailable", str(exc)) from exc
        self._reader = threading.Thread(target=self._read_loop, name="holdspeak-terminal-live", daemon=True)
        self._reader.start()

    def request_capture(self) -> bytes:
        """Request a control-mode capture, preserving the command block boundary."""

        result = self._request_block(
            b"capture-pane -p -e -t " + self.pane_id.encode() + b" -S -" + str(self._lines).encode()
        )
        # Each response line is one captured screen row.  Keep empty trailing
        # rows: they are part of the pane's dimensions and dropping them moves
        # the reconstructed cursor relative to the real screen.
        return b"\n".join(result)

    def request_geometry(self) -> bytes:
        """Read geometry through the same read-only control client."""

        return b"\n".join(
            self._request_block(
                b"display-message -p -t "
                + self.pane_id.encode()
                + b" '#{pane_width} #{pane_height} #{cursor_x} #{cursor_y} #{alternate_on}'"
            )
        ).strip()

    def request_capture_and_geometry(self) -> tuple[bytes, bytes]:
        """Capture the screen and geometry in one serialized control batch.

        tmux executes the two read-only commands in order.  The first
        ``%begin`` is the snapshot watermark; output between it and the second
        ``%end`` remains queued for the live ring and cannot fall through a
        separate geometry request.
        """

        geometry_command = (
            b"display-message -p -t "
            + self.pane_id.encode()
            + b" '#{pane_width} #{pane_height} #{cursor_x} #{cursor_y} #{alternate_on}'"
        )
        with self._command_lock:
            if not self._startup_ready.wait(timeout=self._command_timeout):
                raise TerminalLiveError("stream_unavailable", "tmux control attach timed out")
            if self.error is not None:
                raise TerminalLiveError("stream_unavailable", str(self.error))
            with self._block_lock:
                self._block = []
                self._capture_boundary = False
            try:
                self._write(
                    b"capture-pane -p -e -t "
                    + self.pane_id.encode()
                    + b" -S -"
                    + str(self._lines).encode()
                    + b" ; "
                    + geometry_command
                    + b"\n"
                )
                results: list[tuple[bytes, ...]] = []
                for _ in range(2):
                    try:
                        result = self._block_done.get(timeout=self._command_timeout)
                    except queue.Empty as exc:
                        raise TerminalLiveError("stream_unavailable", "tmux control capture timed out") from exc
                    if isinstance(result, BaseException):
                        raise TerminalLiveError("stream_unavailable", str(result)) from result
                    results.append(tuple(result))
                return b"\n".join(results[0]), b"\n".join(results[1]).strip()
            finally:
                with self._block_lock:
                    self._block = None

    def _request_block(self, command: bytes) -> tuple[bytes, ...]:
        """Run one hard-coded read command and return its protocol block."""

        with self._command_lock:
            if not self._startup_ready.wait(timeout=self._command_timeout):
                raise TerminalLiveError("stream_unavailable", "tmux control attach timed out")
            if self.error is not None:
                raise TerminalLiveError("stream_unavailable", str(self.error))
            with self._block_lock:
                self._block = []
                self._capture_boundary = False
            try:
                self._write(command + b"\n")
                try:
                    result = self._block_done.get(timeout=self._command_timeout)
                except queue.Empty as exc:
                    raise TerminalLiveError("stream_unavailable", "tmux control capture timed out") from exc
                if isinstance(result, BaseException):
                    raise TerminalLiveError("stream_unavailable", str(result)) from result
                return tuple(result)
            finally:
                with self._block_lock:
                    self._block = None

    def _write(self, value: bytes) -> None:
        stream = getattr(self._process, "stdin", None)
        if stream is None:
            raise TerminalLiveError("stream_unavailable", "tmux control client has no stdin")
        try:
            stream.write(value)
            stream.flush()
        except (BrokenPipeError, OSError) as exc:
            raise TerminalLiveError("stream_unavailable", str(exc)) from exc

    def _read_loop(self) -> None:
        stream = getattr(self._process, "stdout", None)
        if stream is None:
            self.error = RuntimeError("tmux control client has no stdout")
            self._ready.set()
            return
        block_started = False
        startup_block = False
        block_marker: tuple[bytes, bytes, bytes] | None = None
        startup_lines: list[bytes] = []
        try:
            while not self._stop.is_set():
                line = stream.readline()
                if not line:
                    break
                if isinstance(line, str):
                    line = line.encode("utf-8", "surrogateescape")
                line = bytes(line).rstrip(b"\r\n")
                # A command response block is arbitrary text.  Check the
                # block state before notification prefixes: a captured line
                # can itself begin with ``%output`` and must not be mistaken
                # for an asynchronous event.
                if block_started:
                    marker = line.split(b" ", 3)
                    is_end = (
                        marker[0] in {b"%end", b"%error"}
                        and len(marker) == 4
                        and block_marker is not None
                        and tuple(marker[1:]) == block_marker
                    )
                    if is_end:
                        if startup_block:
                            if marker[0] == b"%error":
                                self.error = RuntimeError(line[7:].decode("utf-8", "replace"))
                            self._startup_ready.set()
                        else:
                            with self._block_lock:
                                block = tuple(self._block or ())
                                # Each response block has its own bounded
                                # accumulator; a chained geometry block must
                                # never inherit captured screen rows.
                                self._block = []
                            if marker[0] == b"%error":
                                self._put_block(RuntimeError(line[7:].decode("utf-8", "replace")))
                            else:
                                self._put_block(block)
                        block_started = False
                        startup_block = False
                        block_marker = None
                    else:
                        if startup_block:
                            startup_lines.append(line)
                        else:
                            with self._block_lock:
                                if self._block is not None:
                                    self._block.append(line)
                    continue
                if line.startswith(b"%begin "):
                    parts = line.split(b" ", 3)
                    if len(parts) != 4:
                        continue
                    block_started = True
                    block_marker = tuple(parts[1:])
                    with self._block_lock:
                        startup_block = self._block is None
                        capture_boundary = not startup_block and not self._capture_boundary
                        self._capture_boundary = self._capture_boundary or not startup_block
                        if startup_block:
                            startup_lines.clear()
                    if capture_boundary and self._on_boundary is not None:
                        try:
                            self._on_boundary()
                        except Exception:
                            pass
                    continue
                if line.startswith(b"%output "):
                    _marker, _, payload = line.partition(b" ")
                    _pane, _, payload = payload.partition(b" ")
                    # Notifications for an attached session may include other
                    # panes.  Never mix another pane into this target's stream.
                    if _pane.decode("ascii", "ignore") == self.pane_id:
                        self._on_output(
                            decode_control_output(payload),
                            post_boundary=self._capture_boundary,
                        )
                    continue
                with self._block_lock:
                    if block_started and self._block is not None:
                        # Command blocks are arbitrary text; only protocol
                        # markers recognized while a block is open are control
                        # records.  A capture line that happens to begin with
                        # ``%output`` is therefore retained here.
                        self._block.append(line)
        except BaseException as exc:  # reader failure is surfaced to waiters
            self.error = exc
            with self._block_lock:
                if self._block is not None:
                    try:
                        self._block_done.put_nowait(exc)
                    except queue.Full:
                        pass
        finally:
            self._startup_ready.set()
            self._ready.set()
            if self._on_closed is not None:
                try:
                    self._on_closed()
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()
        process = self._process
        if process is None:
            return
        try:
            self._write(b"detach-client\n")
        except TerminalLiveError:
            pass
        try:
            process.wait(timeout=CONTROL_STOP_TIMEOUT_SECONDS)
        except (AttributeError, subprocess.TimeoutExpired):
            # This is the control client only.  Never send a tmux kill command
            # and never signal the pane's shell.
            for method in ("terminate", "kill"):
                try:
                    getattr(process, method)()
                    process.wait(timeout=CONTROL_STOP_TIMEOUT_SECONDS)
                    break
                except (AttributeError, OSError, subprocess.TimeoutExpired):
                    continue


@dataclass
class _Batch:
    sequence: int
    data: bytes


class TerminalLivePane:
    """Shared control client and bounded replay ring for one immutable pane."""

    def __init__(
        self,
        *,
        target_id: str,
        target_generation: str,
        pane_id: str,
        targets: Any,
        runner: Optional[Runner] = None,
        popen_factory: Callable[..., Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
        lines: int = LIVE_CAPTURE_LINES,
        ring_max_batches: int = LIVE_RING_MAX_BATCHES,
        ring_max_bytes: int = LIVE_RING_MAX_BYTES,
        on_idle: Callable[["TerminalLivePane"], None] | None = None,
    ) -> None:
        self.target_id = str(target_id)
        self.target_generation = str(target_generation)
        self.pane_id = str(pane_id)
        self.targets = targets
        self._runner = runner
        self._popen_factory = popen_factory
        self._clock = clock
        self._lines = lines
        self._ring_max_batches = max(1, int(ring_max_batches))
        self._ring_max_bytes = max(1, int(ring_max_bytes))
        self._condition = threading.Condition()
        self._ring: deque[_Batch] = deque()
        self._ring_bytes = 0
        self._sequence = 0
        self._snapshot = b""
        self._snapshot_sequence = 1
        self._pending_output: list[bytes] = []
        self._pending_output_bytes = 0
        self._pending_overflow = False
        self._capture_watermark = 0
        self._pane: dict[str, int] | None = None
        self._control: _ControlClient | None = None
        self._control_error: str | None = None
        self._started = False
        self._closed = False
        self._stream_count = 0
        self._idle_timer: threading.Timer | None = None
        self._on_idle = on_idle
        self._stream_id = "live_" + uuid.uuid4().hex[:16]
        self._start_lock = threading.Lock()

    @property
    def stream_id(self) -> str:
        return self._stream_id

    @property
    def closed(self) -> bool:
        with self._condition:
            return self._closed

    @property
    def sequence(self) -> int:
        with self._condition:
            return self._sequence

    def start(self) -> None:
        # A single control client/ring belongs to a target generation.  Keep
        # the check and attach under one lock so two first subscribers cannot
        # race into two tmux clients.
        with self._start_lock:
            if self._started:
                return
            self._start_impl()

    def _start_impl(self) -> None:
        with self._condition:
            if self._started:
                return
            if self._closed:
                raise TerminalLiveError("stream_unavailable", "terminal stream is closed")
        verified = self.targets.verify(self.target_id, self.target_generation)
        if verified["status"] != "ok":
            raise TerminalLiveError(verified["status"], str(verified.get("detail") or verified["status"]))
        # Start control mode before asking for the snapshot.  tmux serializes
        # the capture command's %begin/%end block with output notifications;
        # the reader therefore has one authoritative boundary, rather than a
        # poll followed by a separately attached client.
        control = _ControlClient(
            self.pane_id,
            self._on_output,
            on_boundary=self._on_capture_boundary,
            on_closed=self._on_control_closed,
            popen_factory=self._popen_factory,
            lines=self._lines,
        )
        control.start()
        try:
            captured, raw_geometry = control.request_capture_and_geometry()
            with self._condition:
                watermark = self._capture_watermark
            geometry = _parse_geometry(raw_geometry)
        except Exception:
            control.stop()
            raise
        with self._condition:
            if self._closed:
                # Shutdown may win while the control client is still waiting
                # for its initial response.  ``close`` could not see this
                # client before it was published, so detach it here instead
                # of allowing a late startup to escape the pane lifecycle.
                reject_start = True
            else:
                reject_start = False
        if reject_start:
            control.stop()
            raise TerminalLiveError("stream_unavailable", "terminal stream is closed")
        with self._condition:
            self._pane = geometry
            self._snapshot = _bootstrap_snapshot(captured, geometry)
            self._snapshot_sequence = max(1, watermark)
            self._sequence = max(1, self._sequence)
            self._control = control
            self._control_error = None
            self._started = True
            pending = tuple(self._pending_output)
            pending_overflow = self._pending_overflow
            self._pending_output.clear()
            self._pending_output_bytes = 0
            self._pending_overflow = False
            for data in pending:
                self._append_batch(data)
            self._condition.notify_all()
        if pending_overflow:
            # Startup output exceeded the bounded handoff buffer.  Refresh the
            # real screen once and make that snapshot the new replay boundary;
            # never grow an unbounded pre-start list.
            try:
                self._refresh_snapshot()
            except TerminalLiveError as exc:
                with self._condition:
                    self._control_error = exc.detail
                    self._condition.notify_all()
        # The command response has been consumed.  Any output batches read
        # after its %begin boundary are already in the ring; bytes before that
        # boundary are part of the snapshot and cannot be replayed twice.

    def _append_batch(self, data: bytes) -> None:
        self._sequence += 1
        batch = _Batch(self._sequence, bytes(data))
        self._ring.append(batch)
        self._ring_bytes += len(batch.data)
        while self._ring and (
            len(self._ring) > self._ring_max_batches or self._ring_bytes > self._ring_max_bytes
        ):
            dropped = self._ring.popleft()
            self._ring_bytes -= len(dropped.data)

    def _on_output(self, data: bytes, *, post_boundary: bool = False) -> None:
        if not data:
            return
        with self._condition:
            if self._closed:
                return
            if not self._started:
                if post_boundary:
                    if self._pending_output_bytes + len(data) <= self._ring_max_bytes:
                        self._pending_output.append(bytes(data))
                        self._pending_output_bytes += len(data)
                    else:
                        self._pending_overflow = True
                # Output received while the initial command is in flight is
                # held nowhere: the command's snapshot is the baseline.  This
                # avoids duplicate initial bytes while keeping the client
                # attached for subsequent notifications.
                return
            self._append_batch(data)
            self._condition.notify_all()

    def _on_capture_boundary(self) -> None:
        with self._condition:
            self._capture_watermark = self._sequence

    def _on_control_closed(self) -> None:
        control: _ControlClient | None = None
        with self._condition:
            if not self._closed and self._control is not None:
                control = self._control
                self._control_error = "tmux control client closed"
                self._control = None
                self._started = False
                # Existing readers finish with a typed absence.  A reconnect
                # starts a new control epoch so an old cursor cannot consume
                # bytes from a restarted reader.
                self._stream_id = "live_" + uuid.uuid4().hex[:16]
                self._condition.notify_all()
        # The reader invokes this callback at EOF.  stop() only detaches the
        # control client process and never joins this reader, so cleanup cannot
        # deadlock on itself and never touches the pane shell.
        if control is not None:
            control.stop()

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            if self._idle_timer is not None:
                self._idle_timer.cancel()
                self._idle_timer = None
            control = self._control
            self._control = None
            self._condition.notify_all()
        if control is not None:
            control.stop()

    def _refresh_snapshot(self) -> None:
        control = self._control
        if control is None:
            raise TerminalLiveError("stream_unavailable", "tmux control client is closed")
        data, raw_geometry = control.request_capture_and_geometry()
        with self._condition:
            watermark = self._capture_watermark
        geometry = _parse_geometry(raw_geometry)
        with self._condition:
            self._pane = geometry
            self._snapshot = _bootstrap_snapshot(data, geometry)
            self._snapshot_sequence = max(1, watermark)

    def subscribe(self, stream_id: str | None, resume_sequence: int | None) -> "TerminalLiveSubscription":
        self.start()
        with self._condition:
            self._stream_count += 1
            if self._idle_timer is not None:
                self._idle_timer.cancel()
                self._idle_timer = None
            requested = str(stream_id or "")
            valid_stream = requested == self._stream_id
            cursor = resume_sequence if valid_stream and resume_sequence is not None else 0
            return TerminalLiveSubscription(self, self._stream_id, cursor, send_snapshot=not valid_stream or resume_sequence is None)

    def unsubscribe(self) -> None:
        """Release one HTTP reader and reap an idle control client."""

        with self._condition:
            if self._stream_count:
                self._stream_count -= 1
            self._condition.notify_all()
            if self._stream_count == 0 and self._started and not self._closed:
                if self._idle_timer is None:
                    self._idle_timer = threading.Timer(LIVE_IDLE_GRACE_SECONDS, self._reap_idle)
                    self._idle_timer.daemon = True
                    self._idle_timer.start()

    def _reap_idle(self) -> None:
        control: _ControlClient | None = None
        with self._condition:
            self._idle_timer = None
            if self._stream_count or not self._started or self._closed:
                return
            # An idle pane is terminally retired.  The service removes this
            # object after the control client is stopped and creates a fresh
            # epoch for a later subscriber; no race can resurrect this ring.
            self._closed = True
            control = self._control
            self._control = None
            self._started = False
            self._control_error = "stream idle timeout"
            self._ring.clear()
            self._ring_bytes = 0
            self._sequence = 0
            self._snapshot = b""
            self._snapshot_sequence = 1
            self._stream_id = "live_" + uuid.uuid4().hex[:16]
            self._condition.notify_all()
        if control is not None:
            control.stop()
        if self._on_idle is not None:
            self._on_idle(self)

    def _verify_before_emit(self) -> dict[str, Any]:
        verified = self.targets.verify(self.target_id, self.target_generation)
        if verified["status"] != "ok":
            return verified
        return verified

    def _next(self, subscription: "TerminalLiveSubscription") -> dict[str, Any] | None:
        # Drain bytes first, then re-prove identity immediately before every
        # yield.  A respawn racing this method can only discard the drained
        # batch; it cannot leak successor-pane bytes to an old stream.
        with self._condition:
            if subscription.closed:
                return None
            if self._closed:
                return _frame(status="stream_unavailable", stream_id=subscription.stream_id, sequence=subscription.cursor, detail="stream closed")
            if subscription.stream_id != self._stream_id:
                return _frame(
                    status="stream_unavailable",
                    stream_id=subscription.stream_id,
                    sequence=subscription.cursor,
                    detail="terminal stream epoch changed",
                )
            if self._control_error:
                return _frame(status="stream_unavailable", stream_id=subscription.stream_id, sequence=subscription.cursor, detail=self._control_error)
            if subscription.send_snapshot:
                needs_refresh = subscription.resync_snapshot
                subscription.send_snapshot = False
                subscription.resync_snapshot = False
                if needs_refresh:
                    # The replay ring is intentionally bounded.  A slow reader
                    # receives a real current screen before its cursor moves
                    # to the live tail.
                    self._condition.release()
                    try:
                        self._refresh_snapshot()
                    finally:
                        self._condition.acquire()
                data = self._snapshot
                seq = self._snapshot_sequence
                subscription.cursor = seq
                pane = dict(self._pane) if self._pane else None
                pending = _frame(status="snapshot", stream_id=subscription.stream_id, sequence=seq, data=data, pane=pane)
            else:
                floor = self._ring[0].sequence if self._ring else self._sequence + 1
                if subscription.cursor + 1 < floor:
                    subscription.cursor = self._sequence
                    pending = _frame(status="resync_required", stream_id=subscription.stream_id, sequence=self._sequence, reason="replay_window_exceeded")
                    subscription.send_snapshot = True
                    subscription.resync_snapshot = True
                else:
                    batches = [batch for batch in self._ring if batch.sequence > subscription.cursor]
                    if batches:
                        batch = batches[0]
                        subscription.cursor = batch.sequence
                        pending = _frame(status="output", stream_id=subscription.stream_id, sequence=batch.sequence, data=batch.data)
                    else:
                        self._condition.wait(timeout=LIVE_HEARTBEAT_SECONDS)
                        if subscription.closed:
                            return None
                        if self._closed:
                            return _frame(status="stream_unavailable", stream_id=subscription.stream_id, sequence=subscription.cursor, detail="stream closed")
                        batches = [batch for batch in self._ring if batch.sequence > subscription.cursor]
                        if batches:
                            batch = batches[0]
                            subscription.cursor = batch.sequence
                            pending = _frame(status="output", stream_id=subscription.stream_id, sequence=batch.sequence, data=batch.data)
                        else:
                            pending = _frame(status="heartbeat", stream_id=subscription.stream_id, sequence=self._sequence)
        verified = self._verify_before_emit()
        if verified["status"] != "ok":
            # Do not emit the drained frame.  The route keeps the typed absence
            # on the stream so the UI can stop/reissue its immutable target.
            return _frame(
                status=verified["status"],
                stream_id=subscription.stream_id,
                sequence=subscription.cursor,
                detail=verified.get("detail") or verified["status"],
            )
        if subscription.closed:
            return None
        if pending.get("status") == "heartbeat" and verified.get("pane"):
            pending["pane"] = dict(verified["pane"])
        return pending


class TerminalLiveSubscription:
    def __init__(self, pane: TerminalLivePane, stream_id: str, cursor: int, *, send_snapshot: bool) -> None:
        self.pane = pane
        self.stream_id = stream_id
        self.cursor = int(cursor)
        self.send_snapshot = bool(send_snapshot)
        self.resync_snapshot = False
        self.closed = False

    def frames(self) -> Iterator[dict[str, Any]]:
        try:
            while not self.closed:
                frame = self.pane._next(self)
                if frame is None:
                    return
                yield frame
                if frame["status"] in {"target_gone", "generation_mismatch", "stream_unavailable"}:
                    return
        finally:
            self.close()

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            self.pane.unsubscribe()


class TerminalLiveService:
    """Compose live panes over the shared :class:`TerminalTargetRegistry`."""

    def __init__(
        self,
        targets: Any,
        *,
        runner: Optional[Runner] = None,
        popen_factory: Callable[..., Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
        lines: int = LIVE_CAPTURE_LINES,
        ring_max_batches: int = LIVE_RING_MAX_BATCHES,
        ring_max_bytes: int = LIVE_RING_MAX_BYTES,
    ) -> None:
        self.targets = targets
        self._runner = runner
        self._popen_factory = popen_factory
        self._clock = clock
        self._lines = lines
        self._ring_max_batches = ring_max_batches
        self._ring_max_bytes = ring_max_bytes
        self._lock = threading.Lock()
        self._panes: dict[tuple[str, str], TerminalLivePane] = {}
        self._closed = False

    def _pane(self, target_id: str, target_generation: str) -> TerminalLivePane:
        verified = self.targets.verify(target_id, target_generation)
        if verified["status"] != "ok":
            raise TerminalLiveError(verified["status"], str(verified.get("detail") or verified["status"]))
        key = (str(target_id), str(target_generation))
        with self._lock:
            if self._closed:
                raise TerminalLiveError("stream_unavailable", "terminal live service is closed")
            pane = self._panes.get(key)
            if pane is None or pane.closed:
                pane = TerminalLivePane(
                    target_id=str(target_id),
                    target_generation=str(target_generation),
                    pane_id=str(verified["pane_id"]),
                    targets=self.targets,
                    runner=self._runner,
                    popen_factory=self._popen_factory,
                    clock=self._clock,
                    lines=self._lines,
                    ring_max_batches=self._ring_max_batches,
                    ring_max_bytes=self._ring_max_bytes,
                    on_idle=self._remove_idle,
                )
                self._panes[key] = pane
            return pane

    def _remove_idle(self, pane: TerminalLivePane) -> None:
        key = (pane.target_id, pane.target_generation)
        with self._lock:
            if self._panes.get(key) is pane:
                self._panes.pop(key, None)

    def subscribe(
        self,
        target_id: Any,
        target_generation: Any,
        *,
        stream_id: str | None = None,
        resume_sequence: int | None = None,
    ) -> TerminalLiveSubscription:
        with self._lock:
            if self._closed:
                raise TerminalLiveError("stream_unavailable", "terminal live service is closed")
        normalized_id = str(target_id or "")
        normalized_generation = str(target_generation or "")
        pane = self._pane(normalized_id, normalized_generation)
        try:
            subscription = pane.subscribe(stream_id, resume_sequence)
        except TerminalLiveError:
            # A timer may retire the pane between lookup and attach.  Retry
            # only after the object proves terminally closed; all other
            # failures retain their typed status.
            if not pane.closed:
                raise
            with self._lock:
                if self._panes.get((normalized_id, normalized_generation)) is pane:
                    self._panes.pop((normalized_id, normalized_generation), None)
            subscription = self._pane(normalized_id, normalized_generation).subscribe(
                stream_id, resume_sequence
            )
        with self._lock:
            if self._closed:
                subscription.close()
                raise TerminalLiveError("stream_unavailable", "terminal live service is closed")
        return subscription

    # Named aliases keep the transport seam readable to callers that treat a
    # live request as opening a stream rather than polling a subscription.
    open_stream = subscribe
    stream = subscribe

    def close(self) -> None:
        with self._lock:
            self._closed = True
            panes = list(self._panes.values())
            self._panes.clear()
        for pane in panes:
            pane.close()

    def metrics(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            panes = dict(self._panes)
        return {f"{target}:{generation}": {"sequence": pane.sequence, "stream_id": pane.stream_id} for (target, generation), pane in panes.items()}


__all__ = [
    "CONTROL_START_TIMEOUT_SECONDS",
    "LIVE_CAPTURE_LINES",
    "LIVE_HEARTBEAT_SECONDS",
    "LIVE_IDLE_GRACE_SECONDS",
    "LIVE_RING_MAX_BATCHES",
    "LIVE_RING_MAX_BYTES",
    "TerminalLiveError",
    "TerminalLivePane",
    "TerminalLiveService",
    "TerminalLiveSubscription",
    "decode_control_output",
]
