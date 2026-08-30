"""HS-154-01 — TTS route tests.

- 404 law: POST /api/tts answers 404 when the extra is absent.
- Status shape: GET /api/tts/status returns {installed: bool, model_ready: bool}.
- Stream shape: POST /api/tts returns streaming WAV with correct header.
- Weights download carries egress badge and receipt.
"""
from __future__ import annotations

import importlib
import json
import struct
import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

REPO = Path(__file__).resolve().parents[2]

# ---- helpers ----


def _app_client():
    """Build a minimal TestClient around the TTS router."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.tts import build_tts_router, _reset_kokoro_state

    _reset_kokoro_state()
    ctx = WebContext(get_state=lambda: {})
    app = FastAPI()
    app.include_router(build_tts_router(ctx))
    return TestClient(app), _reset_kokoro_state


def _inject_fake_kokoro():
    """Inject a fake kokoro_onnx module into sys.modules.

    Returns the mock module and a cleanup function.
    """
    import numpy as np

    fake = types.ModuleType("kokoro_onnx")
    fake.__name__ = "kokoro_onnx"

    class FakeKokoro:
        def __init__(self, model_path: str, voices_path: str):
            self.model_path = model_path
            self.voices_path = voices_path

        def create(self, text: str, voice: str = "af_heart", speed: float = 1.0):
            # Return ~0.1s of silence at 24000 Hz
            sample_rate = 24000
            num_samples = int(0.1 * sample_rate)
            samples = np.zeros(num_samples, dtype=np.float32)
            return samples, sample_rate

    fake.Kokoro = FakeKokoro
    sys.modules["kokoro_onnx"] = fake

    def cleanup():
        sys.modules.pop("kokoro_onnx", None)

    return fake, cleanup


# ---- 404 law: extra absent ----


class TestTtsNotInstalled:
    """When the kokoro-onnx extra is absent, routes 404 with typed code."""

    def test_status_returns_not_installed(self):
        client, reset = _app_client()
        try:
            r = client.get("/api/tts/status")
            assert r.status_code == 200
            data = r.json()
            assert data["installed"] is False
            assert data["model_ready"] is False
        finally:
            reset()

    def test_post_tts_returns_404(self):
        client, reset = _app_client()
        try:
            r = client.post("/api/tts", json={"text": "Hello"})
            assert r.status_code == 404
            data = r.json()
            assert data["code"] == "tts_not_installed"
        finally:
            reset()

    def test_download_returns_404(self):
        client, reset = _app_client()
        try:
            r = client.post("/api/tts/download")
            assert r.status_code == 404
            data = r.json()
            assert data["code"] == "tts_not_installed"
        finally:
            reset()


# ---- status shape ----


class TestTtsStatus:
    """GET /api/tts/status returns a well-shaped response."""

    def test_status_shape_without_extra(self):
        client, reset = _app_client()
        try:
            r = client.get("/api/tts/status")
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data["installed"], bool)
            assert isinstance(data["model_ready"], bool)
        finally:
            reset()

    def test_status_installed_no_model(self):
        """Extra installed but model weights not downloaded."""
        fake, cleanup = _inject_fake_kokoro()
        try:
            client, reset = _app_client()
            try:
                r = client.get("/api/tts/status")
                data = r.json()
                assert data["installed"] is True
                # Model not ready because weight files don't exist
                assert data["model_ready"] is False
            finally:
                reset()
        finally:
            cleanup()

    def test_status_installed_with_model(self, tmp_path):
        """Extra installed AND model weights present."""
        fake, cleanup = _inject_fake_kokoro()
        try:
            from holdspeak.web.routes import tts as tts_module

            # Point weights dir to tmp_path with fake weight files
            weights_dir = tmp_path / "tts"
            weights_dir.mkdir()
            (weights_dir / "kokoro-v0_19.onnx").write_bytes(b"fake-model")
            (weights_dir / "voices.bin").write_bytes(b"fake-voices")

            with patch.object(tts_module, "_model_weights_dir", return_value=weights_dir):
                client, reset = _app_client()
                try:
                    r = client.get("/api/tts/status")
                    data = r.json()
                    assert data["installed"] is True
                    assert data["model_ready"] is True
                finally:
                    reset()
        finally:
            cleanup()


# ---- stream shape ----


class TestTtsStream:
    """POST /api/tts streams a valid WAV with the correct header."""

    def test_stream_returns_wav(self, tmp_path):
        """With fake kokoro + fake weights: WAV header + PCM data."""
        fake, cleanup = _inject_fake_kokoro()
        try:
            from holdspeak.web.routes import tts as tts_module

            weights_dir = tmp_path / "tts"
            weights_dir.mkdir()
            (weights_dir / "kokoro-v0_19.onnx").write_bytes(b"fake-model")
            (weights_dir / "voices.bin").write_bytes(b"fake-voices")

            with patch.object(tts_module, "_model_weights_dir", return_value=weights_dir):
                client, reset = _app_client()
                try:
                    r = client.post("/api/tts", json={"text": "Hello world"})
                    assert r.status_code == 200
                    assert "audio/wav" in r.headers.get("content-type", "")

                    # Verify WAV header
                    wav_data = r.content
                    assert len(wav_data) > 44  # At least the header
                    assert wav_data[:4] == b"RIFF"
                    assert wav_data[8:12] == b"WAVE"
                    assert wav_data[12:16] == b"fmt "
                finally:
                    reset()
        finally:
            cleanup()

    def test_missing_text_returns_400(self, tmp_path):
        fake, cleanup = _inject_fake_kokoro()
        try:
            from holdspeak.web.routes import tts as tts_module

            weights_dir = tmp_path / "tts"
            weights_dir.mkdir()
            (weights_dir / "kokoro-v0_19.onnx").write_bytes(b"fake-model")
            (weights_dir / "voices.bin").write_bytes(b"fake-voices")

            with patch.object(tts_module, "_model_weights_dir", return_value=weights_dir):
                client, reset = _app_client()
                try:
                    r = client.post("/api/tts", json={})
                    assert r.status_code == 400
                    assert r.json()["code"] == "tts_invalid_request"
                finally:
                    reset()
        finally:
            cleanup()

    def test_model_not_ready_returns_503(self):
        """Extra installed but no model files → 503."""
        fake, cleanup = _inject_fake_kokoro()
        try:
            client, reset = _app_client()
            try:
                r = client.post("/api/tts", json={"text": "Hello"})
                assert r.status_code == 503
                assert r.json()["code"] == "tts_model_not_ready"
            finally:
                reset()
        finally:
            cleanup()


# ---- download receipt + egress badge ----


class TestTtsDownload:
    """POST /api/tts/download carries egress badge and receipt."""

    def test_download_receipt_and_egress(self, tmp_path):
        """Successful download returns receipt + egress badge."""
        fake, cleanup = _inject_fake_kokoro()
        try:
            from holdspeak.web.routes import tts as tts_module

            weights_dir = tmp_path / "tts"
            weights_dir.mkdir()

            def fake_download(dest: str):
                """Simulate the download by creating the weight files."""
                d = Path(dest)
                d.mkdir(parents=True, exist_ok=True)
                (d / "kokoro-v0_19.onnx").write_bytes(b"fake-model")
                (d / "voices.bin").write_bytes(b"fake-voices")

            fake.download = fake_download

            with patch.object(tts_module, "_model_weights_dir", return_value=weights_dir):
                client, reset = _app_client()
                try:
                    r = client.post("/api/tts/download")
                    assert r.status_code == 202
                    data = r.json()
                    # Receipt
                    assert "receipt" in data
                    assert data["receipt"]["downloaded"] is True
                    assert "elapsed_s" in data["receipt"]
                    # Egress badge
                    assert "egress" in data
                    assert data["egress"]["host"] == "huggingface.co"
                    assert "bytes_estimate" in data["egress"]
                finally:
                    reset()
        finally:
            cleanup()
