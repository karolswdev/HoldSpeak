"""Speak-to-fill: the transcribe proxy, honest about the run's state.

The site records a WAV and posts it to the conductor, which proxies to the run's
OWN transcribe route (local Whisper, no egress). The proxy must be honest: down
run → not up; unreachable → say so; a real boot → a structured answer, never a
crash.
"""

from __future__ import annotations

import io
import wave

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


def _silence_wav(seconds: float = 0.3) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buf.getvalue()


@pytest.fixture
def client(fake_products):
    mgr = RunManager(Database(), boot_timeout=1.0, link_caches=False)
    app = create_app(mgr)
    with TestClient(app) as c:
        yield c


def test_transcribe_rejects_empty_body(client):
    sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
    assert client.post(f"/api/sittings/{sid}/transcribe", content=b"").status_code == 400


def test_transcribe_up_but_unreachable_is_honest(client):
    # Fake product reports 'up' but nothing actually serves the transcribe route,
    # so the proxy honestly reports it could not reach the product — never fakes.
    sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
    r = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav())
    body = r.json()
    assert body["ok"] is False
    assert "reach" in body["error"].lower() or "not up" in body["error"].lower()


def test_transcribe_down_run_is_honest(client, fake_products):
    fake_products.boot_ok = False
    sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
    body = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav()).json()
    assert body["ok"] is False
    assert "not up" in body["error"].lower()
