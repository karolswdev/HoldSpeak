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
            # Astra r1 (finding 2): the press also set the Default for AI work.
            assert "DEFAULT SET" in _receipt(page), _receipt(page)
            assert page.locator("[data-testid='concierge-root']").count() == 1

            # The set: READY only where the whole group runs. The library
            # engine claims every result an executor checks (Astra r1, 5):
            # Thoughts READY; Agents LIMITED, named in the owner's words.
            page.wait_for_function(
                """() => !!document.querySelector("[data-testid='concierge-set-limit-agents_tools']")""",
                timeout=30_000,
            )
            agents = page.locator("[data-testid='concierge-set-agents_tools']")
            assert "LIMITED" in (agents.text_content() or "")
            assert page.locator("[data-testid='concierge-set-limit-agents_tools']").text_content() == "WITHOUTAGENTS"
            assert "structured result" not in (page.locator("[data-testid='concierge-set-list']").text_content() or "")
            thoughts = page.locator("[data-testid='concierge-set-thoughts_notes']")
            assert "READY" in (thoughts.text_content() or "")
            assert page.locator("[data-testid='concierge-set-chat_practice']").count() == 0
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


def _old_box(engine_url: str) -> None:
    """A hand-made endpoint record from before the Model Library: it answers,
    and it has no model record, so a write for it cannot be made."""
    from holdspeak.db import get_database

    get_database().profiles.upsert(
        profile_id="old-box", name="Old box", kind="openAICompatible",
        base_url=engine_url, model=MODEL,
    )


class TestTwoFailures:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_every_failed_group_is_named_with_its_token(self, width: int, engine_url: str) -> None:
        from playwright.sync_api import sync_playwright

        _old_box(engine_url)
        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _open_models(page)
            for group in ("thoughts_notes", "agents_tools"):
                page.locator(f"[data-testid='concierge-picker-{group}']").click()
                page.locator(f"[data-testid='concierge-picker-well-{group}'] [data-testid$='old-box']").first.click()
                row = page.locator(f"[data-testid='concierge-set-{group}']")
                assert "UNKNOWN · TRY" in (row.text_content() or ""), row.text_content()
            page.locator("[data-testid='concierge-apply']").click()
            # Astra r2 (finding 4): one cause, said once, with its count.
            page.wait_for_function(
                """() => /GROUPS · NO MODEL RECORD/.test(
                    document.querySelector("[data-testid='concierge-receipt']")?.textContent || "")""",
                timeout=30_000,
            )
            receipt = _receipt(page)
            assert receipt.count("NO MODEL RECORD") == 1, receipt
            page.wait_for_function(
                """() => !!document.querySelector("[data-testid='concierge-set-fail-agents_tools']")""",
                timeout=30_000,
            )
            assert page.locator("[data-testid='concierge-set-fail-thoughts_notes']").text_content() == "NO MODEL RECORD"
            _settle(page)
            page.screenshot(path=str(SHOTS / f"receipt-failures-{width}.png"), full_page=False)
            # Astra r2 (finding 3): a reload reads the hub's receipt again.
            _open_models(page)
            page.wait_for_function(
                """() => !!document.querySelector("[data-testid='concierge-set-fail-thoughts_notes']")""",
                timeout=30_000,
            )
            assert "NO MODEL RECORD" in _receipt(page), _receipt(page)
            _settle(page)
            page.screenshot(path=str(SHOTS / f"receipt-failures-reloaded-{width}.png"), full_page=False)
            browser.close()


class TestColdFirstRun:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        # No Whisper anywhere this hub can see: the cold Mac.
        empty = tmp_path / "hf-empty"
        empty.mkdir()
        monkeypatch.setenv("HF_HOME", str(empty))
        monkeypatch.setenv("HF_HUB_CACHE", str(empty / "hub"))
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_lan_box_keeps_the_speech_download(self, width: int, engine_url: str) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            card = page.locator("[data-testid='firstrun-local-ai']")
            card.wait_for(timeout=30_000)
            status = _api(page, "GET", "/api/setup/local-ai", token=TOKEN)
            assert status["speech"]["state"] in {"will_download", "not_covered"}, status["speech"]
            page.locator("[data-testid='firstrun-lan-verb']").click()
            speech = page.locator("[data-testid='firstrun-speech-verb']")
            speech.wait_for(timeout=10_000)
            assert (speech.text_content() or "").startswith("Set up speech · ")
            page.get_by_role("textbox", name="Server address").fill(engine_url)
            page.locator("[data-testid='concierge-add-check']").click()
            page.locator("[data-testid='concierge-add-submit']:not([disabled])").wait_for(timeout=30_000)
            page.locator("[data-testid='concierge-add-submit']").click()
            page.locator("[data-testid='firstrun-lan-receipt']").wait_for(timeout=30_000)
            assert "DEFAULT SET" in (page.locator("[data-testid='firstrun-lan-receipt']").text_content() or "")
            # A server on this machine is THIS DEVICE, never "LAN".
            assert "THIS DEVICE" in (card.text_content() or "")
            assert "LAN ·" not in (card.text_content() or "")
            # Speech is still missing: the download stays, the card is not done.
            assert speech.is_visible()
            assert page.locator("[data-testid='firstrun-first-words']").get_attribute("data-lit") != "true"
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            glob = next(r for r in roster["rows"] if r["id"] == "global")
            assert glob["status"] == "assigned", glob
            _settle(page)
            card.screenshot(path=str(SHOTS / f"firstrun-cold-{width}.png"))
            browser.close()
