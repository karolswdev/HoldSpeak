"""Producer-backed tests for the opt-in local Desk UI feedback route."""

from __future__ import annotations

import base64
import io
import json
import os
import struct
import urllib.error
import urllib.request
import wave
import zlib
from pathlib import Path
from typing import Any

import pytest

from holdspeak.services.ui_feedback import FEEDBACK_FILES, feedback_root
from tests.e2e.glass_infra import _boot

TOKEN = "ui-feedback-test"
REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "web" / "src" / "desk" / "feedback" / "fixtures"


def _png() -> bytes:
    """One real 1x1 RGB PNG, assembled without a third-party image library."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\x34\x56\x78"))
        + chunk(b"IEND", b"")
    )


def _wav() -> bytes:
    stream = io.BytesIO()
    with wave.open(stream, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16_000)
        writer.writeframes(b"\x00\x00" * 160)
    return stream.getvalue()


def _payload(*, identifier: str = "0123456789abcdef0123456789abcdef", note: str = "draft") -> dict[str, Any]:
    return {
        "id": identifier,
        "captured_at": "2026-10-20T12:00:00+00:00",
        "context": {
            "window": {"kind": "project", "title": "Platform"},
            "selected_text": "The selected element",
            "form_values": {"note": note},
        },
        "audio_base64": base64.b64encode(_wav()).decode("ascii"),
        "screenshot_base64": base64.b64encode(_png()).decode("ascii"),
    }


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    raw = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if raw is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=raw, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def _record(name: str, body: Any) -> None:
    """Opt-in actual-producer recording for frontend transport fixtures."""
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") != "1":
        return
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_status_is_runtime_flag_and_disabled_write_is_404(tmp_path, monkeypatch):
    monkeypatch.delenv("HOLDSPEAK_UI_FEEDBACK", raising=False)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        status, body = _call(base, "GET", "/api/ui-feedback/status")
        assert status == 200
        assert body == {"enabled": False}
        _record("status-disabled.json", body)

        status, body = _call(base, "POST", "/api/ui-feedback", _payload())
        assert status == 404
        assert body["success"] is False
    finally:
        server.stop()


def test_status_and_save_are_owner_authenticated(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        unauthenticated = urllib.request.Request(f"{base}/api/ui-feedback/status", method="GET")
        with pytest.raises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(unauthenticated, timeout=30)
        assert refused.value.code == 401

        status, body = _call(base, "GET", "/api/ui-feedback/status")
        assert status == 200
        assert body == {"enabled": True}
        _record("status-enabled.json", body)
    finally:
        server.stop()


def test_save_publishes_private_durable_bundle_and_exact_retry(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    payload = _payload()
    try:
        status, receipt = _call(base, "POST", "/api/ui-feedback", payload)
        assert status == 200
        assert receipt["success"] is True
        assert receipt["id"] == payload["id"]
        assert receipt["files"] == list(FEEDBACK_FILES)
        _record(
            "save-success.json",
            {**receipt, "directory": "/isolated/.local/share/holdspeak/feedback/" + payload["id"]},
        )

        directory = Path(receipt["directory"])
        assert directory == feedback_root(tmp_path / "home") / payload["id"]
        assert directory.is_dir()
        assert {path.name for path in directory.iterdir()} == set(FEEDBACK_FILES)
        assert directory.stat().st_mode & 0o777 == 0o700
        for name in FEEDBACK_FILES:
            assert (directory / name).stat().st_mode & 0o777 == 0o600

        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        assert report["id"] == payload["id"]
        assert report["captured_at"] == payload["captured_at"]
        assert report["context"] == payload["context"]
        assert report["saved_at"]
        assert set(report["runtime_identity"]) == {
            "backend_version", "backend_revision", "frontend_build"
        }
        assert "database_path" not in report["runtime_identity"]
        assert "config_revision" not in report["runtime_identity"]
        assert "pid" not in report["runtime_identity"]
        assert (directory / "audio.wav").read_bytes() == base64.b64decode(payload["audio_base64"])
        assert (directory / "window.png").read_bytes() == base64.b64decode(payload["screenshot_base64"])

        status, retried = _call(base, "POST", "/api/ui-feedback", payload)
        assert status == 200
        assert retried == receipt

        changed = {**payload, "context": {**payload["context"], "form_values": {"note": "changed"}}}
        status, body = _call(base, "POST", "/api/ui-feedback", changed)
        assert status == 409
        assert body["success"] is False
    finally:
        server.stop()


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "../unsafe"),
        ("audio_base64", base64.b64encode(b"not wav").decode("ascii")),
        ("screenshot_base64", base64.b64encode(b"not png").decode("ascii")),
    ],
)
def test_invalid_payload_is_rejected_without_publishing(tmp_path, monkeypatch, field, value):
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    payload = _payload()
    payload[field] = value
    try:
        status, body = _call(base, "POST", "/api/ui-feedback", payload)
        assert status == 400
        assert body["success"] is False
        assert not (feedback_root(tmp_path / "home") / _payload()["id"]).exists()
    finally:
        server.stop()


def test_failed_publication_leaves_no_complete_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    from holdspeak.services import ui_feedback

    original = ui_feedback._durable_write
    calls = 0

    def fail_once(path, data, mode=0o600):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("test disk failure")
        return original(path, data, mode)

    monkeypatch.setattr(ui_feedback, "_durable_write", fail_once)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        status, body = _call(base, "POST", "/api/ui-feedback", _payload())
        assert status == 500
        assert body["success"] is False
        assert not (feedback_root(tmp_path / "home") / _payload()["id"]).exists()
    finally:
        server.stop()
