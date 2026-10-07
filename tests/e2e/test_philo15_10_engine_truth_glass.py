"""PHILO-15 10 — the engine setup tells the truth, on the glass.

A real hub over an isolated HOME and an OpenAI-compatible stub engine (it
answers ``/models``, ``/props`` with tool support, and a 1-token chat).
Add an engine → Check (READY · TOOLS) → Use this for summaries (the window
stays: USING · <model> · SUMMARIES) → the set reads LIMITED, never READY,
for groups the authority serves only in part → Use these (the window stays:
USING · <model> · N GROUPS · N LIMITED). 1440 + 393.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="PHILO-15 glass needs Playwright")

SHOTS = evidence_dir("docs/internal/philo/phase-15/shots/10-engine-truth")
TOKEN = "philo15-10"
MODEL = "stub-qwen"


class _Engine(BaseHTTPRequestHandler):
    def _json(self, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        if path.endswith("/models"):
            self._json({"object": "list", "data": [{"id": MODEL, "object": "model"}]})
        elif path.endswith("/props"):
            self._json({"chat_template_caps": {"supports_tools": True}})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._json({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    def log_message(self, *_args: Any) -> None:
        return


@pytest.fixture(scope="module")
def engine_url() -> Any:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Engine)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()
    server.server_close()


def _open_models(page: Any) -> None:
    page.evaluate(
        """([key]) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}))""",
        ["open-concierge"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator("[data-testid='concierge-set-list']").wait_for(timeout=30_000)


def _receipt(page: Any) -> str:
    return page.locator("[data-testid='concierge-receipt']").text_content() or ""


class TestEngineTruth:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_ready_means_ready_and_every_press_leaves_a_receipt(self, width: int, engine_url: str) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _open_models(page)

            # Check: the hub asks the server, and names its tool answer.
            page.locator("[data-testid='concierge-add-engine']").click()
            page.get_by_role("textbox", name="Server address").fill(engine_url)
            page.locator("[data-testid='concierge-add-check']").click()
            assert page.locator("[data-testid='concierge-add-tools']").text_content(timeout=30_000) == "TOOLS"

            # Use this for summaries: the window stays and says so.
            page.locator("[data-testid='concierge-add-submit']").click()
            page.wait_for_function(
                """() => (document.querySelector("[data-testid='concierge-receipt']")?.textContent || "")
                           .includes("SUMMARIES")""",
                timeout=30_000,
            )
            assert _receipt(page).startswith(f"USING · {MODEL.upper()}"), _receipt(page)
            assert page.locator("[data-testid='concierge-root']").count() == 1

            # The set: READY only where the whole group runs.
            page.wait_for_function(
                """() => !!document.querySelector("[data-testid='concierge-set-limit-thoughts_notes']")""",
                timeout=30_000,
            )
            thoughts = page.locator("[data-testid='concierge-set-thoughts_notes']")
            assert "LIMITED" in (thoughts.text_content() or "")
            assert "NO THOUGHT DEVELOPMENT" in (thoughts.text_content() or "")
            rows = _api(page, "POST", "/api/concierge/propose", token=TOKEN)["rows"]
            assert not [
                r for r in rows
                if r["state"] == "READY" and r.get("blocked")
            ], rows
            speech = next(r for r in rows if r["group"] == "speech_recognition")
            assert not str(speech.get("engineId") or "").startswith("preset:"), speech
            _settle(page)
            page.locator("[data-testid='concierge-set-list']").screenshot(path=str(SHOTS / f"set-{width}.png"))

            # Use these: the window stays; the receipt names what is limited.
            page.locator("[data-testid='concierge-apply']").click()
            page.wait_for_function(
                """() => /LIMITED/.test(document.querySelector("[data-testid='concierge-receipt']")?.textContent || "")
                         && /^USING/.test(document.querySelector("[data-testid='concierge-receipt']")?.textContent || "")""",
                timeout=30_000,
            )
            assert page.locator("[data-testid='concierge-root']").count() == 1
            assert "DEFAULT SET" in _receipt(page), _receipt(page)
            hub = _api(page, "GET", "/api/settings/hub", token=TOKEN)
            assert hub["models"]["defaultSet"] is True, hub["models"]
            _settle(page)
            page.screenshot(path=str(SHOTS / f"after-use-these-{width}.png"), full_page=False)

            # The footer receipt never runs under Cancel (B27).
            overlap = page.evaluate(
                """() => {
                  const r = document.querySelector("[data-testid='concierge-receipt']").getBoundingClientRect();
                  const c = document.querySelector("[data-testid='concierge-cancel']").getBoundingClientRect();
                  return r.right > c.left + 1 && r.bottom > c.top && r.top < c.bottom;
                }"""
            )
            assert not overlap, "the receipt runs under Cancel"
            browser.close()
        assert not errors, errors
