"""PHILO-16 (C), Astra r1 M1/M2: the switches that keep a walk off real engines
and off the default writer. Both default to the product's own behaviour."""
from __future__ import annotations

from typing import Any

import pytest

from holdspeak.services import inference_default_service as ids


def test_loopback_ports_default_to_the_four_engines(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ids.LOOPBACK_PORTS_ENV, raising=False)
    assert ids.loopback_engine_ports() == ids.LOOPBACK_ENGINE_PORTS


def test_loopback_ports_read_the_env_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.LOOPBACK_PORTS_ENV, "1234, 9999,bad,70000")
    assert ids.loopback_engine_ports() == ((1234, "LM Studio"), (9999, "local engine"))


def test_an_empty_port_list_opens_no_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.LOOPBACK_PORTS_ENV, "")
    asked: list[str] = []

    def getter(url: str, **_: Any) -> tuple[int, bytes]:
        asked.append(url)
        return 200, b'{"data": [{"id": "qwen3:8b"}]}'

    assert ids.scan_loopback_engines(http_get=getter) == []
    assert asked == []


def test_the_scan_reads_only_the_named_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.LOOPBACK_PORTS_ENV, "1234")
    asked: list[str] = []

    def getter(url: str, **_: Any) -> tuple[int, bytes]:
        asked.append(url)
        return 200, b'{"data": [{"id": "qwen3-8b"}]}'

    found = ids.scan_loopback_engines(http_get=getter)
    assert [row["port"] for row in found] == [1234]
    assert asked and all(":1234/" in url for url in asked)


class _NoTouch:
    """Any read of the database or the assignments fails the test."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"the default writer touched {name!r} while off")


def _service() -> ids.InferenceDefaultService:
    return ids.InferenceDefaultService(
        _NoTouch(), assignment_service=_NoTouch(),
        scan=lambda: (_ for _ in ()).throw(AssertionError("scanned while off")),
        find_embed_model=lambda *a, **k: None,
    )


def test_the_default_writer_is_on_unless_named_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ids.DEFAULT_WRITER_ENV, raising=False)
    assert ids.default_writer_on()
    monkeypatch.setenv(ids.DEFAULT_WRITER_ENV, "on")
    assert ids.default_writer_on()
    monkeypatch.setenv(ids.DEFAULT_WRITER_ENV, " OFF ")
    assert not ids.default_writer_on()


def test_off_the_writer_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.DEFAULT_WRITER_ENV, "off")
    service = _service()
    service.kick("detect")
    assert service._thread is None
    assert service.ensure(reason="boot")["status"] == "off"
    assert service.rescan()["status"] == "off"
