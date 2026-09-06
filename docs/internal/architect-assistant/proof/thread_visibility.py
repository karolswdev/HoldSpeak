"""Exercise live Thread visibility in a production browser and isolated hub.

The controlled model pauses before first text and completion. HTTP acceptance
is delayed in the browser, then a second case drops every WebSocket frame.
No owner conversation or model endpoint is used.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[4]
(root / ".tmp").mkdir(exist_ok=True)
sys.path.insert(0, str(root))
original_home = Path.home()
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(original_home / "Library/Caches/ms-playwright"))
original_expanduser = os.path.expanduser


class PausedModel:
    active_provider = "fixture-local"
    active_model = "thread-visibility-fixture"

    def __init__(self):
        self.first = threading.Event()
        self.finish = threading.Event()

    def run_prompt_stream(self, **kwargs):
        from holdspeak.kernel.inference_stream import Delta
        assert self.first.wait(30), "Browser never released first text"
        yield Delta(kind="text", text="The response is arriving.\n\n" + "An architecture observation to read.\n\n" * 35)
        assert self.finish.wait(30), "Browser never released completion"
        yield Delta(kind="text", text="The response is complete.")
        yield Delta(kind="usage", meta={"prompt_tokens": 50, "completion_tokens": 200})
        yield Delta(kind="done")


with tempfile.TemporaryDirectory(prefix="holdspeak-thread-visibility-") as directory:
    isolated = Path(directory)

    def expanduser(path):
        value = os.fspath(path)
        if isinstance(value, str) and (value == "~" or value.startswith("~/")):
            return str(isolated) + value[1:]
        return original_expanduser(path)

    with patch.object(Path, "home", return_value=isolated), patch("os.path.expanduser", side_effect=expanduser):
        from holdspeak.db import get_database, reset_database
        from holdspeak.config import Config
        from holdspeak.kernel import runtime
        from holdspeak.services.thread_modes import seed_modes
        from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
        from tests.unit.test_phase143_inference_assignments import OWNER, _profile
        from playwright.sync_api import sync_playwright, expect

        reset_database()
        db = get_database(isolated / "visibility.db")
        seed_modes(db)
        config = Config()
        config.control_mode = "yolo"
        token = "thread-visibility-isolated"
        with patch.object(Config, "load", return_value=config), patch.object(runtime, "_mode", return_value="yolo"):
            server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}), auth_token=token, host="127.0.0.1")
            url = server.start()
            broker = runtime._service()
            _profile(db, "visibility", context_ceiling=65536)
            InferenceAssignmentService(db).set_assignment(OWNER, {"command_id": "visibility-assignment", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [{"profile_id": "visibility", "profile_revision": 1}]})
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    context = browser.new_context(viewport={"width": 1440, "height": 900})
                    api = context.request
                    headers = {"Authorization": f"Bearer {token}"}
                    assert api.post(url + "/api/desk/seed", data={}, headers=headers).ok
                    assert api.put(url + "/api/setup/onboarding", data={"disposition": "completed"}, headers=headers).ok
                    cases = []
                    for connected in (True, False):
                        engine = PausedModel()
                        broker.inference_runner._engine_factory = lambda *_a, **_kw: engine
                        response = api.post(url + "/api/threads", data={"title": "Prompt visibility", "recipe_id": INTERVIEW_MODE_ID}, headers=headers)
                        assert response.ok, response.text()
                        tid = response.json()["id"]
                        page = context.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        if not connected:
                            page.route_web_socket("**/*", lambda socket: None)
                        held = []

                        def hold_ack(route):
                            response = route.fetch()
                            assert response.ok, response.text()
                            held.append((route, response))

                        page.route("**/api/threads/*/turns", hold_ack)
                        page.goto(f"{url}/?token={token}&open=thread:{tid}", wait_until="load")
                        composer = page.locator(".thread-composer-input")
                        expect(composer).to_be_visible(timeout=20000)
                        prompt = "Keep my prompt visible while we discuss the transformation."
                        composer.fill(prompt)
                        page.locator(".thread-foot").get_by_role("button", name="Send", exact=True).click()
                        user = page.locator(".thread-messages").get_by_text(prompt, exact=True)
                        expect(user).to_be_visible(timeout=2000)
                        expect(composer).to_have_value(prompt)
                        expect(composer).to_be_disabled()
                        page.screenshot(path=str(root / ".tmp/thread-visibility-pending.png"))
                        deadline = time.monotonic() + 10
                        while not held and time.monotonic() < deadline:
                            page.wait_for_timeout(50)
                        assert len(held) == 1, "No HTTP acknowledgement captured"
                        held[0][0].fulfill(response=held[0][1])
                        expect(composer).to_have_value("")
                        expect(user).to_have_count(1)
                        expect(page.locator(".thread-foot").get_by_role("button", name="Stop", exact=True)).to_be_visible()
                        engine.first.set()
                        expect(page.locator(".thread-messages")).to_contain_text("The response is arriving.", timeout=15000)
                        body = page.locator(".thread-pullout-body")
                        body.evaluate("el => { el.scrollTop = 0; el.dispatchEvent(new Event('scroll', {bubbles:true})); }")
                        expect(user).to_be_in_viewport()
                        page.screenshot(path=str(root / f".tmp/thread-visibility-{'live' if connected else 'offline'}.png"))
                        engine.finish.set()
                        expect(page.locator(".thread-messages")).to_contain_text("The response is complete.", timeout=15000)
                        expect(page.locator(".thread-foot").get_by_role("button", name="Send", exact=True)).to_be_visible(timeout=10000)
                        expect(user).to_be_in_viewport()
                        assert body.evaluate("el => el.scrollTop") < 40, "A reply pulled the reader away from their prompt"
                        expect(user).to_have_count(1)
                        assert not errors, errors
                        detail = api.get(url + f"/api/threads/{tid}", headers=headers).json()
                        assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
                        assert not detail["messages"][-1].get("error_json")
                        cases.append({"websocket": "connected" if connected else "all frames dropped", "prompt_before_ack": True, "partial_before_completion": True, "completion_without_reload": True, "reader_scroll_preserved": True, "one_saved_turn": True})
                        page.close()
                    print(json.dumps({"result": "pass", "model": "paused fixture", "cases": cases}))
                    browser.close()
            finally:
                if "engine" in locals():
                    engine.first.set()
                    engine.finish.set()
                server.stop()
                runtime._dispose(broker)
                reset_database()
