"""Unit tests for ``DeviceStatusEmitter`` (HS-14-07)."""

from __future__ import annotations

from typing import List, Tuple

import pytest

from holdspeak.device_status import DeviceStatusEmitter


class _CapturingSender:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, int]] = []

    def __call__(self, text: str, ttl_ms: int) -> None:
        self.calls.append((text, ttl_ms))


class _RaisingSender:
    def __call__(self, text: str, ttl_ms: int) -> None:
        raise RuntimeError("queue full")


class _StubRegistry:
    def __init__(self, labels: dict[str, str]) -> None:
        self._labels = labels

    def get(self, device_id: str):
        if device_id not in self._labels:
            return None

        class _D:
            def __init__(self, label: str) -> None:
                self.label = label

        return _D(self._labels[device_id])


class TestDeviceStatusEmitter:
    def test_send_with_no_registered_sender_returns_false(self) -> None:
        emitter = DeviceStatusEmitter()
        assert emitter.send("ghost", "hi") is False

    def test_register_then_send_invokes_sender(self) -> None:
        emitter = DeviceStatusEmitter()
        sender = _CapturingSender()

        emitter.register("aipi-1", sender)
        ok = emitter.send("aipi-1", "Listening...", ttl_ms=0)

        assert ok is True
        assert sender.calls == [("Listening...", 0)]
        assert emitter.is_registered("aipi-1") is True

    def test_unregister_drops_sender(self) -> None:
        emitter = DeviceStatusEmitter()
        sender = _CapturingSender()
        emitter.register("aipi-1", sender)
        emitter.unregister("aipi-1")

        ok = emitter.send("aipi-1", "after-unregister")

        assert ok is False
        assert sender.calls == []
        assert emitter.is_registered("aipi-1") is False

    def test_send_swallows_sender_exceptions(self) -> None:
        emitter = DeviceStatusEmitter()
        emitter.register("aipi-1", _RaisingSender())

        # Must not raise to the caller; returns False because the
        # send did not succeed.
        assert emitter.send("aipi-1", "boom") is False

    def test_broadcast_returns_delivery_count(self) -> None:
        emitter = DeviceStatusEmitter()
        a, b = _CapturingSender(), _CapturingSender()
        emitter.register("aipi-1", a)
        emitter.register("aipi-2", b)

        delivered = emitter.broadcast(
            ["aipi-1", "aipi-2", "ghost"],
            "Bookmark @ 12s",
            ttl_ms=2000,
        )

        assert delivered == 2
        assert a.calls == [("Bookmark @ 12s", 2000)]
        assert b.calls == [("Bookmark @ 12s", 2000)]

    def test_label_substitution_against_registry(self) -> None:
        emitter = DeviceStatusEmitter(label_lookup=_StubRegistry({"aipi-1": "Karol"}))
        sender = _CapturingSender()
        emitter.register("aipi-1", sender)

        emitter.send("aipi-1", "{label} is recording", ttl_ms=0)

        assert sender.calls == [("Karol is recording", 0)]

    def test_label_substitution_falls_back_to_device_id(self) -> None:
        emitter = DeviceStatusEmitter(label_lookup=_StubRegistry({}))
        sender = _CapturingSender()
        emitter.register("aipi-1", sender)

        emitter.send("aipi-1", "{label}: hi")
        assert sender.calls == [("aipi-1: hi", 0)]

    def test_active_device_ids(self) -> None:
        emitter = DeviceStatusEmitter()
        assert emitter.active_device_ids() == []

        emitter.register("a", _CapturingSender())
        emitter.register("b", _CapturingSender())
        assert sorted(emitter.active_device_ids()) == ["a", "b"]

        emitter.unregister("a")
        assert emitter.active_device_ids() == ["b"]
