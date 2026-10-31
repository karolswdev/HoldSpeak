"""Actual control-mode terminal streaming on a private tmux server."""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

import pytest

from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.delivery.terminal_live import TerminalLiveError, TerminalLiveService


pytestmark = pytest.mark.skipif(
    shutil.which("tmux") is None, reason="tmux is required for the live terminal proof"
)


def _tmux(*args: str) -> str:
    result = subprocess.run(
        ["tmux", *args], check=True, capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()


def _send_python(pane: str, script: str) -> None:
    """Run a producer whose marker is not echoed in the typed command."""
    encoded = base64.b64encode(script.encode()).decode()
    command = f"python3 -c \"import base64;exec(base64.b64decode('{encoded}'))\""
    subprocess.run(
        ["tmux", "send-keys", "-t", pane, command, "Enter"], check=True, timeout=10
    )


def _wait_sequence(service: TerminalLiveService, target: dict, at_least: int) -> None:
    until = time.monotonic() + 5
    key = f"{target['target_id']}:{target['target_generation']}"
    while time.monotonic() < until:
        if service.metrics().get(key, {}).get("sequence", 0) >= at_least:
            return
        time.sleep(0.05)
    raise AssertionError(f"control stream did not reach {at_least}: {service.metrics()!r}")


def _next_until(frames, predicate, *, seconds: float = 5):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        frame = next(frames)
        if predicate(frame):
            return frame
    raise AssertionError("live stream frame did not arrive")


def _collect_until(frames, collected: bytearray, required: bytes, *, seconds: float = 5):
    until = time.monotonic() + seconds
    last = None
    while time.monotonic() < until:
        last = next(frames)
        if last["status"] == "output":
            collected.extend(base64.b64decode(last["data"]))
            if required in collected:
                return last
    raise AssertionError(f"stream bytes did not arrive: {required!r}, tail={bytes(collected)!r}")


def _wait_capture_markers(pane: str, markers: list[bytes], *, seconds: float = 5) -> bytes:
    """Wait until the real tmux screen projection contains every producer marker."""
    until = time.monotonic() + seconds
    latest = b""
    while time.monotonic() < until:
        latest = _tmux("capture-pane", "-p", "-e", "-t", pane, "-S", "-200").encode()
        if all(marker in latest for marker in markers):
            return latest
        time.sleep(0.05)
    raise AssertionError(f"tmux capture missed markers: {[marker for marker in markers if marker not in latest]!r}")


@pytest.fixture
def private_pane(monkeypatch: pytest.MonkeyPatch):
    sockets = Path(tempfile.mkdtemp(prefix="hs-live-", dir="/tmp"))
    monkeypatch.setenv("TMUX_TMPDIR", str(sockets))
    monkeypatch.delenv("TMUX", raising=False)
    session = f"hs-live-{uuid.uuid4().hex[:8]}"
    _tmux(
        "-f", "/dev/null", "new-session", "-d", "-s", session,
        "-x", "100", "-y", "30", "bash --noprofile --norc",
    )
    pane = _tmux("list-panes", "-t", session, "-F", "#{pane_id}")
    try:
        yield session, pane
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], check=False, timeout=10)
        for socket in sockets.glob("tmux-*/default"):
            subprocess.run(["tmux", "-S", str(socket), "kill-server"], check=False, timeout=5)
        shutil.rmtree(sockets, ignore_errors=True)


def _live(private_pane, *, ring_max_batches: int = 256):
    _session, pane = private_pane
    targets = TerminalTargetRegistry()
    target = targets.issue(f"pane:{pane}")
    assert target["status"] == "issued", target
    service = TerminalLiveService(
        targets, ring_max_batches=ring_max_batches, ring_max_bytes=64 * 1024
    )
    return service, target, pane


def test_control_stream_bootstrap_preserves_order_split_unicode_and_ansi(
    private_pane, monkeypatch
):
    import holdspeak.delivery.terminal_live as live_module

    monkeypatch.setattr(live_module, "LIVE_HEARTBEAT_SECONDS", 0.05)
    service, target, pane = _live(private_pane)
    subscription = service.subscribe(target["target_id"], target["target_generation"])
    frames = subscription.frames()
    first = next(frames)
    assert first["status"] == "snapshot"
    assert first["sequence"] == 1
    stream_id = first["stream_id"]
    markers = [
        f"live-one-{uuid.uuid4().hex[:8]}".encode(),
        f"live-two-{uuid.uuid4().hex[:8]}".encode(),
        f"live-three-{uuid.uuid4().hex[:8]}".encode(),
    ]
    ansi = b"\x1b[2J\x1b[HALT-SCREEN\x1b[31mRED\x1b[0m"
    collected = bytearray()
    try:
        for index, marker in enumerate(markers):
            if index == 1:
                script = (
                    f"import os,time; os.write(1,{marker + b' unicode-'!r}); "
                    "os.write(1,b'\\xf0\\x9f'); time.sleep(.03); "
                    "os.write(1,b'\\x98\\x80\\n')"
                )
            elif index == 2:
                script = (
                    f"import os; os.write(1,{marker + b' '!r}); "
                    f"os.write(1,{ansi + bytes([10])!r})"
                )
            else:
                script = f"import os; os.write(1,{marker + bytes([10])!r})"
            _send_python(pane, script)
            expected = marker + (
                b"" if index != 1 else b" unicode-\xf0\x9f\x98\x80"
            )
            frame = _collect_until(frames, collected, expected)
            assert frame["stream_id"] == stream_id
            assert frame["sequence"] > 1
        positions = [bytes(collected).find(marker) for marker in markers]
        assert positions == sorted(positions) and all(pos >= 0 for pos in positions), repr(bytes(collected))
        for marker in markers:
            assert collected.count(marker) == 1, marker
        assert b"unicode-\xf0\x9f\x98\x80" in collected
        assert ansi in collected
    finally:
        subscription.close()
        service.close()


def test_startup_snapshot_keeps_screen_lines_that_look_like_control_records(private_pane):
    """A real pane may print protocol-looking text; only tmux's block IDs delimit captures."""
    _session, pane = private_pane
    fake_end = b"%end fake-screen-line"
    fake_error = b"%error fake-screen-line"
    _send_python(pane, f"import os; os.write(1,{fake_end + bytes([10]) + fake_error + bytes([10])!r})")
    _wait_capture_markers(pane, [fake_end, fake_error])
    service, target, _ = _live(private_pane)
    subscription = service.subscribe(target["target_id"], target["target_generation"])
    try:
        frame = next(subscription.frames())
        assert frame["status"] == "snapshot"
        snapshot = base64.b64decode(frame["data"])
        assert fake_end in snapshot
        assert fake_error in snapshot
    finally:
        subscription.close()
        service.close()


def test_control_stream_gap_emits_fresh_real_snapshot(private_pane, monkeypatch):
    import holdspeak.delivery.terminal_live as live_module

    monkeypatch.setattr(live_module, "LIVE_HEARTBEAT_SECONDS", 0.05)
    service, target, pane = _live(private_pane, ring_max_batches=2)
    first_subscription = service.subscribe(target["target_id"], target["target_generation"])
    first_frames = first_subscription.frames()
    stream_id = next(first_frames)["stream_id"]
    markers = [f"gap-{uuid.uuid4().hex[:8]}".encode() for _ in range(4)]
    try:
        for marker in markers:
            _send_python(pane, f"import os; os.write(1,{marker + bytes([10])!r})")
            _wait_sequence(service, target, 2)
        _wait_sequence(service, target, 1 + len(markers))
        _wait_capture_markers(pane, markers)
        slow = service.subscribe(
            target["target_id"], target["target_generation"],
            stream_id=stream_id, resume_sequence=1,
        )
        slow_frames = slow.frames()
        assert next(slow_frames)["status"] == "resync_required"
        snapshot = next(slow_frames)
        assert snapshot["status"] == "snapshot"
        current = base64.b64decode(snapshot["data"])
        assert all(marker in current for marker in markers)
    finally:
        first_subscription.close()
        service.close()


def test_resync_snapshot_includes_output_written_while_capture_is_in_flight(private_pane):
    service, target, pane = _live(private_pane, ring_max_batches=2)
    initial = service.subscribe(target["target_id"], target["target_generation"])
    initial_frames = initial.frames()
    first = next(initial_frames)
    for index in range(4):
        marker = f"resync-before-{index}-{uuid.uuid4().hex[:8]}".encode()
        _send_python(pane, f"import os; os.write(1,{marker + bytes([10])!r})")
    _wait_capture_markers(pane, [f"resync-before-{index}".encode() for index in range(4)])
    slow = service.subscribe(
        target["target_id"], target["target_generation"],
        stream_id=first["stream_id"], resume_sequence=1,
    )
    slow_frames = slow.frames()
    try:
        assert next(slow_frames)["status"] == "resync_required"
        pane_impl = service._panes[(target["target_id"], target["target_generation"])]
        entered = threading.Event()
        release = threading.Event()
        original_refresh = pane_impl._refresh_snapshot

        def delayed_refresh():
            entered.set()
            assert release.wait(5), "resync capture did not release"
            original_refresh()

        pane_impl._refresh_snapshot = delayed_refresh
        result: dict[str, dict] = {}

        def read_snapshot():
            result["frame"] = next(slow_frames)

        reader = threading.Thread(target=read_snapshot, daemon=True)
        reader.start()
        assert entered.wait(5), "resync capture did not start"
        in_flight = f"resync-in-flight-{uuid.uuid4().hex[:8]}".encode()
        _send_python(pane, f"import os; os.write(1,{in_flight + bytes([10])!r})")
        _wait_capture_markers(pane, [in_flight])
        release.set()
        reader.join(5)
        assert not reader.is_alive()
        frame = result["frame"]
        assert frame["status"] == "snapshot"
        assert in_flight in base64.b64decode(frame["data"])
    finally:
        initial.close()
        slow.close()
        service.close()


def test_reader_death_reconnect_uses_a_new_stream_epoch(private_pane):
    """A dead control reader is disposable; the next attach gets a fresh epoch."""
    _session, pane = private_pane
    targets = TerminalTargetRegistry()
    target = targets.issue(f"pane:{pane}")
    service = TerminalLiveService(targets)
    subscription = service.subscribe(target["target_id"], target["target_generation"])
    frames = subscription.frames()
    first = next(frames)
    control = service._panes[(target["target_id"], target["target_generation"])]._control
    assert control is not None and control.process.poll() is None
    control.process.terminate()
    control.process.wait(timeout=5)
    service.close()
    marker = f"reconnected-{uuid.uuid4().hex[:8]}".encode()
    _send_python(pane, f"import os; os.write(1,{marker + bytes([10])!r})")
    _wait_capture_markers(pane, [marker])
    replacement = TerminalLiveService(targets)
    resumed = replacement.subscribe(target["target_id"], target["target_generation"])
    resumed_frames = resumed.frames()
    try:
        snapshot = next(resumed_frames)
        assert snapshot["status"] == "snapshot"
        assert snapshot["stream_id"] != first["stream_id"]
        assert marker in base64.b64decode(snapshot["data"])
    finally:
        subscription.close()
        resumed.close()
        replacement.close()


def test_closing_stream_leaves_shell_alive_and_old_generation_refuses(private_pane):
    service, target, pane = _live(private_pane)
    session, _ = private_pane
    pipe_path = Path(tempfile.mkdtemp(prefix="hs-live-pipe-", dir="/tmp")) / "output.log"
    _tmux("pipe-pane", "-o", "-t", pane, f"cat >> {pipe_path}")
    subscription = service.subscribe(target["target_id"], target["target_generation"])
    frames = subscription.frames()
    assert next(frames)["status"] == "snapshot"
    control = service._panes[(target["target_id"], target["target_generation"])]._control
    assert control is not None
    subscription.close()
    service.close()
    assert control.process.poll() is not None
    with pytest.raises(TerminalLiveError) as closed:
        service.subscribe(target["target_id"], target["target_generation"])
    assert closed.value.status == "stream_unavailable"
    marker = f"alive-{uuid.uuid4().hex[:8]}"
    _send_python(pane, f"import os; os.write(1,{(marker + chr(10)).encode()!r})")
    until = time.monotonic() + 3
    while time.monotonic() < until:
        capture = _tmux("capture-pane", "-p", "-t", pane, "-S", "-20")
        if marker in capture:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("shell did not survive live stream close")
    pipe_until = time.monotonic() + 3
    while time.monotonic() < pipe_until:
        if pipe_path.exists() and marker in pipe_path.read_text(errors="replace"):
            break
        time.sleep(0.05)
    assert pipe_path.exists() and marker in pipe_path.read_text(errors="replace")
    # Keep the session alive while replacing the original pane. A sole-pane
    # kill would correctly terminate the private tmux session itself.
    subprocess.run(
        ["tmux", "split-window", "-t", session, "-d", "bash --noprofile --norc"],
        check=True, timeout=10,
    )
    subprocess.run(["tmux", "kill-pane", "-t", pane], check=True, timeout=10)
    # A shut-down service refuses every subscription.  Use a fresh service
    # over the same immutable registry to prove that the old target itself
    # is refused independently of service lifetime.
    fresh_service = TerminalLiveService(service.targets)
    try:
        with pytest.raises(TerminalLiveError) as refused:
            fresh_service.subscribe(target["target_id"], target["target_generation"])
        assert refused.value.status in {"target_gone", "generation_mismatch"}
    finally:
        fresh_service.close()
