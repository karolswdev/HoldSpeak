"""HS-142-02 real HTTP-byte acquisition glass at both ruled widths."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="model acquisition glass needs Playwright")

TOKEN = "hs142-model-acquisition-glass"


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {authorization: 'Bearer hs142-model-acquisition-glass',
                      ...(body ? {'content-type': 'application/json'} : {})},
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


def _catalog(body: bytes) -> tuple[str, bytes]:
    from holdspeak.mesh_authority import ed25519

    digest = hashlib.sha256(body).hexdigest()
    manifest = {"files": [{"path": "glass.gguf", "sha256": f"sha256:{digest}", "size": len(body)}]}
    manifest_sha = "sha256:" + hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    entry = {
        "kind": "local_artifact_preset",
        "activation": "download",
        "id": "preset_glass_local",
        "experience": "quick",
        "label": "Quick local glass AI",
        "runtime_id": "llama_cpp_prompt_v1",
        "runtime_min_revision": "0.3.34",
        "format": "gguf",
        "boundary": "same_device",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
        "source": {
            "repository": "holdspeak/glass-model",
            "revision": "a" * 40,
            "filename": "glass.gguf",
            "file_sha256": f"sha256:{digest}",
            "manifest_sha256": manifest_sha,
            "download_bytes": len(body),
            "installed_bytes": len(body),
            "peak_free_bytes": len(body) * 2,
            "license": "Apache-2.0",
        },
        "platforms": ["darwin_arm64", "linux_x86_64", "linux_aarch64"],
        "applicability": {"state": "applicable", "reason": None},
    }
    unsigned = {
        "schema_version": 1,
        "catalog_revision": 42,
        "generated_at": "2026-08-21T00:00:00Z",
        "expires_at": "2036-08-01T00:00:00Z",
        "signing_key_id": "glass",
        "entries": [entry],
    }
    private = hashlib.sha256(b"holdspeak-hs142-glass-only").digest()
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    envelope = json.dumps(
        {**unsigned, "signature": ed25519.sign(private, canonical).hex()},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return envelope, ed25519.public_key(private)


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_download_verify_activate_and_project_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    import holdspeak.inference_setup_catalog as catalog_module
    import holdspeak.services.inference_acquisition_service as acquisition_module
    import holdspeak.services.inference_setup_service as setup_module
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    model = b"GGUF" + (b"holdspeak-glass-model" * 131_072)
    envelope, public = _catalog(model)
    monkeypatch.setattr(catalog_module, "_PACKAGED_CATALOG_JSON", envelope)
    monkeypatch.setattr(catalog_module, "_PACKAGED_CATALOG_TRUST_ROOTS", {"glass": public})
    monkeypatch.setattr(setup_module, "_package_available", lambda module: module == "llama_cpp")
    monkeypatch.setattr(setup_module, "_package_revision", lambda distribution, fallback: "0.3.35" if distribution == "llama-cpp-python" else fallback)
    monkeypatch.setattr(acquisition_module.importlib.metadata, "version", lambda _name: "0.3.35")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def do_GET(self):
            start = 0
            value = self.headers.get("Range", "")
            if value.startswith("bytes="):
                start = int(value.removeprefix("bytes=").removesuffix("-"))
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{len(model) - 1}/{len(model)}")
            else:
                self.send_response(200)
            self.send_header("Content-Length", str(len(model) - start))
            self.end_headers()
            for offset in range(start, len(model), 65_536):
                self.wfile.write(model[offset : offset + 65_536])
                self.wfile.flush()
                time.sleep(0.004)

    byte_server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    byte_thread = threading.Thread(target=byte_server.serve_forever, daemon=True)
    byte_thread.start()
    model_url = f"http://127.0.0.1:{byte_server.server_port}/glass.gguf"

    original_init = acquisition_module.InferenceAcquisitionApplicationService.__init__

    def injected_init(self, *args, **kwargs):
        kwargs["source_url_builder"] = lambda _plan: model_url
        kwargs["allowed_download_host"] = lambda host: host == "127.0.0.1"
        return original_init(self, *args, **kwargs)

    monkeypatch.setattr(acquisition_module.InferenceAcquisitionApplicationService, "__init__", injected_init)

    home = tmp_path / "home"
    home.mkdir()
    browser_cache = Path(os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        Path.home() / "Library/Caches/ms-playwright",
    ))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            page.goto(f"{url}/profiles", wait_until="load")

            surface = page.locator(".models-setup")
            surface.get_by_role("heading", name="Choose your AI", exact=True).wait_for()
            radio = surface.get_by_role("radio", name=re.compile("Quick local glass AI"))
            radio.check()
            action = surface.get_by_role("button", name="DOWNLOAD & USE QUICK", exact=True)
            assert surface.locator(".models-capability-action button").count() == 1
            action.click()
            surface.get_by_text(re.compile(
                "Downloading Quick local glass AI|Verifying the published checksum|Installing verified model bytes"
            )).first.wait_for(timeout=10_000)
            surface.get_by_text("IN USE FOR THOUGHTS", exact=True).wait_for(timeout=20_000)

            setup = _api(page, "GET", "/api/inference/setup")["setup"]
            revision = setup["current_thought_deployment"]["execution_revision"]
            assert revision["schema_version"] == 2
            assert revision["artifact_id"].startswith("artifact_")
            assert revision["context_ceiling"] == 8192
            assert "model_path" not in json.dumps(setup)
            assert str(home) not in json.dumps(setup)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if width == 393:
                box = surface.locator(".models-capability-action").bounding_box()
                assert box and box["width"] <= 393
            page.screenshot(path=f"/tmp/holdspeak-model-acquisition-{width}.png", full_page=False)
            assert errors == []
            browser.close()
    finally:
        server.stop()
        byte_server.shutdown()
        byte_server.server_close()
