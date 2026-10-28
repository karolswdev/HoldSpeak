"""Pending Ask Stop owns its painted target while the local model is held.

The model is a localhost fixture. The real Desk, Ask request and cancel route
run through the isolated hub; this does not claim remote compute was aborted.
"""
from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .engine_stub_rig import _StubHandler, completion_reply
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, clear_hub_windows

pytest.importorskip("playwright.sync_api", reason="pending Ask Stop glass needs Playwright")
pytestmark = [pytest.mark.e2e]

TOKEN = "native-pending-stop-glass"
SHOTS = evidence_dir("native-pending-stop")
ANSWER = "This late local fixture answer must not replace Stopped."
QUESTION = "What should I check before the handoff?"
DRAFT = "Keep this newer question for later."


def _isolated_boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    # DeliveryRegistry freezes its default at import, before _boot changes HOME.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(
        registry_module, "DEFAULT_REGISTRY_PATH",
        tmp_path / "home" / ".holdspeak" / "delivery_sources.json",
    )
    return _boot(tmp_path, monkeypatch, token=TOKEN)


def _stop_geometry(ask: Any) -> dict[str, Any]:
    """Read pixels before a Playwright click can scroll the control."""
    return ask.evaluate("""frame => {
      const stop = [...frame.querySelectorAll('button')]
        .find(button => button.textContent?.trim() === 'Stop');
      const rect = element => element?.getBoundingClientRect().toJSON() ?? null;
      if (!stop) return {missing: 'Stop'};
      const s = stop.getBoundingClientRect(), f = frame.getBoundingClientRect();
      const samples = [];
      for (const row of [1, 3, 5]) for (const col of [1, 3, 5]) {
        const x = s.left + (col / 6) * s.width;
        const y = s.top + (row / 6) * s.height;
        const hit = document.elementFromPoint(x, y);
        samples.push({x, y, owned: hit === stop || stop.contains(hit),
          hit: hit?.tagName || null});
      }
      const center = document.elementFromPoint(s.left + s.width / 2, s.top + s.height / 2);
      return {viewport: {width: innerWidth, height: innerHeight},
        frame: rect(frame), stop: rect(stop),
        inFrame: s.left >= f.left && s.right <= f.right && s.top >= f.top && s.bottom <= f.bottom,
        inViewport: s.left >= 0 && s.right <= innerWidth && s.top >= 0 && s.bottom <= innerHeight,
        centerOwned: center === stop || stop.contains(center), samples,
        runCardCount: document.querySelectorAll('.ambient-theater').length};
    }""")


@pytest.mark.timeout(180)
@pytest.mark.parametrize("width", [1440, 393])
def test_pending_ask_stop_is_reachable_and_cancels_accepted_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    started, release, returned = threading.Event(), threading.Event(), threading.Event()
    requests: list[dict[str, Any]] = []

    class Model(_StubHandler):
        MODEL = "pending-stop-fixture"

        def do_POST(self) -> None:  # noqa: N802 - local HTTP model contract
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            requests.append(request)
            started.set()
            release.wait(20)
            payload = json.dumps({
                "id": "late-answer", "object": "chat.completion", "model": self.MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": ANSWER}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 13, "total_tokens": 25},
            }).encode()
            ctype, payload = completion_reply(request, payload)
            try:
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except OSError:
                # Cancel may close the provider socket before this fixture replies.
                pass
            finally:
                returned.set()

    model = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=model.serve_forever, daemon=True).start()
    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            provider = _api(page, "POST", "/api/inference/model-library/define-endpoint", {
                "draft": {"request_id": "pending-stop-model", "profile_id": "pending-stop-model",
                          "expected_profile_revision": 0, "label": "Pending Stop local model",
                          "provider_family": "openai_compatible", "model": Model.MODEL,
                          "endpoint": f"http://127.0.0.1:{model.server_port}/v1", "requires_key": False},
                "secret": None,
            }, token=TOKEN)["provider"]
            _api(page, "POST", "/api/inference/assignments/set", {
                "command_id": "pending-stop-assignment", "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "ask.answer"},
                "entries": [{"profile_id": provider["profile_id"],
                             "profile_revision": provider["profile_revision"]}],
            }, token=TOKEN)
            clear_hub_windows(page, TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            page.keyboard.press("Control+KeyI")
            ask = page.locator("[id='ask'][data-layer='window']")
            prompt = ask.get_by_role("textbox", name="Ask about your work", exact=True)
            prompt.wait_for()
            prompt.fill(QUESTION)
            with page.expect_request(lambda request: request.url.endswith("/api/ask")
                                     and request.method == "POST") as accepted:
                ask.get_by_role("button", name="Ask", exact=True).click()
            invocation_id = accepted.value.post_data_json["invocation_id"]
            assert invocation_id, accepted.value.post_data_json
            assert started.wait(5), "the isolated model did not receive this Ask"
            stop = ask.get_by_role("button", name="Stop", exact=True)
            expect(stop).to_be_visible()
            expect(ask.get_by_test_id("run-line")).to_have_attribute("data-state", "running")
            prompt.fill(DRAFT)

            geometry = _stop_geometry(ask)
            assert geometry.get("inFrame") and geometry.get("inViewport"), geometry
            assert geometry["centerOwned"] and all(point["owned"] for point in geometry["samples"]), geometry
            assert geometry["runCardCount"] == 0, geometry
            page.screenshot(path=str(SHOTS / f"pending-stop-{width}.png"))
            (SHOTS / f"pending-stop-{width}.json").write_text(json.dumps(geometry, indent=2) + "\n")

            with page.expect_request(lambda request: request.method == "POST"
                                     and request.url.endswith(f"/api/ask/{invocation_id}/cancel")) as cancelled:
                stop.click()
            cancel_request = cancelled.value
            assert cancel_request.url.endswith(f"/api/ask/{invocation_id}/cancel")
            # Ask D1 (#1515): the stopped run is one line under the question
            # (ask-not-answered, reason "stopped") and the status bar says it.
            expect(ask.get_by_test_id("ask-not-answered")).to_have_attribute("data-reason", "stopped")
            expect(ask.get_by_test_id("ask-not-answered")).to_contain_text("Stopped")
            expect(ask.get_by_test_id("ask-status-failed")).to_contain_text("Stopped")
            expect(ask.get_by_role("button", name="Ask again")).to_be_visible()
            expect(ask.get_by_role("region", name="Ask conversation")).to_contain_text(QUESTION)
            expect(prompt).to_have_value(DRAFT)

            release.set()
            assert returned.wait(5), "the held fixture did not attempt its late reply"
            cancel_response = cancel_request.response()
            assert cancel_response is not None and cancel_response.ok, cancel_response
            receipt = cancel_response.json()
            assert receipt["invocation_id"] == invocation_id, receipt
            expect(ask.get_by_test_id("ask-not-answered")).to_contain_text("Stopped")
            assert ANSWER not in ask.inner_text()
            assert len(requests) == 1 and not errors, (requests, errors)
            page.screenshot(path=str(SHOTS / f"stopped-{width}.png"))
            browser.close()
    finally:
        release.set()
        server.stop()
        model.shutdown()
        model.server_close()
