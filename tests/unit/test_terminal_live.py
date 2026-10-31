"""Focused invariants for the native tmux control-mode terminal stream."""

from __future__ import annotations

import base64
import queue
import threading
import time

from holdspeak.delivery import terminal_live


class Targets:
    def __init__(self) -> None:
        self.live = True

    def verify(self, target_id: str, generation: str) -> dict:
        if not self.live:
            return {"status": "generation_mismatch", "detail": "target recycled"}
        return {
            "status": "ok",
            "target_id": target_id,
            "target_generation": generation,
            "pane_id": "%5",
            "pane": {"width": 80, "height": 24, "cursor_x": 2, "cursor_y": 3},
        }


class FakeControl:
    last: "FakeControl | None" = None

    def __init__(self, pane_id, on_output, *, on_boundary=None, on_closed=None, **_kwargs):
        self.pane_id = pane_id
        self.on_output = on_output
        self.on_boundary = on_boundary
        self.on_closed = on_closed
        self.stopped = False
        type(self).last = self

    def start(self):
        return None

    def request_capture(self):
        if self.on_boundary:
            self.on_boundary()
        return b"hello\n"

    def request_geometry(self):
        return b"80 24 2 3 0"

    def request_capture_and_geometry(self):
        return self.request_capture(), self.request_geometry()

    def stop(self):
        self.stopped = True


def _pane(monkeypatch):
    monkeypatch.setattr(terminal_live, "_ControlClient", FakeControl)
    return terminal_live.TerminalLivePane(
        target_id="term_1",
        target_generation="gen_1",
        pane_id="%5",
        targets=Targets(),
    )


def test_initial_snapshot_and_actual_output_are_base64_bytes(monkeypatch):
    pane = _pane(monkeypatch)
    subscription = pane.subscribe(None, None)
    frames = subscription.frames()
    snapshot = next(frames)
    assert snapshot["status"] == "snapshot"
    assert snapshot["sequence"] == 1
    assert base64.b64decode(snapshot["data"]).startswith(b"\x1b[?1049l\x1b[2J")
    pane._on_output(b"\x00\xff\x1b[31m", post_boundary=True)
    output = next(frames)
    assert output["status"] == "output"
    assert output["sequence"] == 2
    assert base64.b64decode(output["data"]) == b"\x00\xff\x1b[31m"
    frames.close()
    assert FakeControl.last is not None and not FakeControl.last.stopped


def test_identity_is_rechecked_after_drain_before_emit(monkeypatch):
    pane = _pane(monkeypatch)
    subscription = pane.subscribe(None, None)
    frames = subscription.frames()
    next(frames)
    pane._on_output(b"successor must not leak", post_boundary=True)
    pane.targets.live = False
    refused = next(frames)
    assert refused["status"] == "generation_mismatch"
    assert b"successor" not in base64.b64decode(refused.get("data") or "")
    frames.close()


def test_idle_disconnect_keeps_bounded_replay_during_grace(monkeypatch):
    pane = _pane(monkeypatch)
    first = pane.subscribe(None, None)
    frames = first.frames()
    snapshot = next(frames)
    frames.close()
    pane._on_output(b"resume-me", post_boundary=True)
    resumed = pane.subscribe(snapshot["stream_id"], snapshot["sequence"])
    resumed_frames = resumed.frames()
    output = next(resumed_frames)
    assert output["status"] == "output"
    assert base64.b64decode(output["data"]) == b"resume-me"
    resumed_frames.close()


def test_new_view_uses_refreshed_snapshot_watermark(monkeypatch):
    pane = _pane(monkeypatch)
    first = pane.subscribe(None, None)
    first_frames = first.frames()
    initial = next(first_frames)
    pane._on_output(b"before-refresh", post_boundary=True)
    assert next(first_frames)["status"] == "output"
    pane._refresh_snapshot()
    second = pane.subscribe(initial["stream_id"], None)
    second_frames = second.frames()
    refreshed = next(second_frames)
    assert refreshed["status"] == "snapshot"
    assert refreshed["sequence"] == pane._snapshot_sequence
    assert refreshed["sequence"] > initial["sequence"]
    second_frames.close()
    first_frames.close()


def test_idle_grace_reaps_control_client_without_killing_shell(monkeypatch):
    monkeypatch.setattr(terminal_live, "LIVE_IDLE_GRACE_SECONDS", 0.01)
    pane = _pane(monkeypatch)
    subscription = pane.subscribe(None, None)
    frames = subscription.frames()
    next(frames)
    frames.close()
    time.sleep(0.05)
    assert pane._started is False
    assert FakeControl.last is not None and FakeControl.last.stopped


def test_close_during_startup_detaches_unpublished_control(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []

    class BlockingControl(FakeControl):
        def request_capture_and_geometry(self):
            started.set()
            assert release.wait(1.0)
            return b"hello\n", b"80 24 2 3 0"

    monkeypatch.setattr(terminal_live, "_ControlClient", BlockingControl)
    pane = terminal_live.TerminalLivePane(
        target_id="term_1",
        target_generation="gen_1",
        pane_id="%5",
        targets=Targets(),
    )

    def subscribe() -> None:
        try:
            pane.subscribe(None, None)
        except BaseException as exc:  # the typed shutdown refusal is asserted below
            errors.append(exc)

    worker = threading.Thread(target=subscribe)
    worker.start()
    assert started.wait(1.0)
    pane.close()
    release.set()
    worker.join(timeout=1.0)

    assert not worker.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], terminal_live.TerminalLiveError)
    assert errors[0].status == "stream_unavailable"
    assert BlockingControl.last is not None and BlockingControl.last.stopped
    assert pane._control is None


def test_control_eof_is_typed_and_next_subscriber_restarts(monkeypatch):
    pane = _pane(monkeypatch)
    first = pane.subscribe(None, None)
    old_stream_id = first.stream_id
    frames = first.frames()
    next(frames)
    control = FakeControl.last
    assert control is not None
    control.on_closed()
    assert next(frames)["status"] == "stream_unavailable"
    assert pane._started is False
    frames.close()
    restarted = pane.subscribe(old_stream_id, 1)
    restarted_frames = restarted.frames()
    assert next(restarted_frames)["status"] == "snapshot"
    assert restarted.stream_id != old_stream_id
    restarted_frames.close()


def test_old_subscription_cannot_receive_bytes_after_eof_restart(monkeypatch):
    pane = _pane(monkeypatch)
    old = pane.subscribe(None, None)
    old_frames = old.frames()
    next(old_frames)
    control = FakeControl.last
    assert control is not None
    old_stream_id = old.stream_id
    control.on_closed()
    replacement = pane.subscribe(old_stream_id, 1)
    replacement_frames = replacement.frames()
    assert next(replacement_frames)["status"] == "snapshot"
    pane._on_output(b"replacement-bytes", post_boundary=True)
    refused = next(old_frames)
    assert refused["status"] == "stream_unavailable"
    assert refused["stream_id"] == old_stream_id
    replacement_frames.close()
    old_frames.close()


class _QueuedStdout:
    def __init__(self) -> None:
        self.items: queue.Queue[bytes] = queue.Queue()

    def readline(self):
        return self.items.get()


class _ControlProcess:
    def __init__(self) -> None:
        self.stdout = _QueuedStdout()
        self.stdin = self
        self.stderr = self
        self.commands: list[bytes] = []
        self.returncode = 0
        self.stdout.items.put(b"%begin 1 0 0\n")
        self.stdout.items.put(b"%end 1 0 0\n")

    def write(self, value: bytes) -> None:
        self.commands.append(value)
        if value.startswith(b"capture-pane "):
            for line in (
                b"%begin 2 1 0\n",
                b"%end captured-content\n",
                b"%output %5 \\303\\251\n",
                b"%end 2 1 0\n",
            ):
                self.stdout.items.put(line)
        elif value == b"detach-client\n":
            self.stdout.items.put(b"")

    def flush(self):
        return None

    def wait(self, timeout=None):
        return 0

    def terminate(self):
        return None

    def kill(self):
        return None


def test_control_parser_matches_the_open_block_before_capture_markers():
    process = _ControlProcess()
    seen: list[bytes] = []
    client = terminal_live._ControlClient(
        "%5",
        lambda data, **_kwargs: seen.append(data),
        popen_factory=lambda *args, **kwargs: process,
    )
    client.start()
    captured = client.request_capture()
    client.stop()
    assert b"%end captured-content" in captured
    assert b"%output %5" in captured
    assert seen == []
    assert process.commands == [b"capture-pane -p -e -t %5 -S -200\n", b"detach-client\n"]
