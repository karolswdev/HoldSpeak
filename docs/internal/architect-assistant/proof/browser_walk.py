"""Production browser walk on an isolated hub and scripted model fixture."""
import json
import os
import re
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[4]
with_desktops = "--desktops" in sys.argv
(root / ".tmp").mkdir(exist_ok=True)
sys.path.insert(0, str(root))
original_home = Path.home()
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(original_home / "Library/Caches/ms-playwright"))
original_expanduser = os.path.expanduser

with tempfile.TemporaryDirectory(prefix="holdspeak-interview-walk-") as directory:
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
        from tests.integration.test_interview_conversation import InterviewModelFixture
        from playwright.sync_api import sync_playwright, expect

        class PausedInterviewModelFixture(InterviewModelFixture):
            def __init__(self):
                super().__init__()
                self.awaiting_answer = threading.Event()
                self.release_answer = threading.Event()

            def run_prompt_stream(self, **kwargs):
                if self.calls == 2:
                    self.awaiting_answer.set()
                    assert self.release_answer.wait(30), "Browser did not release the final answer"
                yield from super().run_prompt_stream(**kwargs)
        reset_database()
        db = get_database(isolated / "walk.db")
        seed_modes(db)
        config = Config()
        config.control_mode = "yolo"
        token = "interview-isolated-walk"
        with patch.object(Config, "load", return_value=config), patch.object(runtime, "_mode", return_value="yolo"):
            server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}), auth_token=token, host="127.0.0.1")
            url = server.start()
            broker = runtime._service()
            _profile(db, "interview-walk", context_ceiling=65536)
            InferenceAssignmentService(db).set_assignment(OWNER, {"command_id": "walk-assignment", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [{"profile_id": "interview-walk", "profile_revision": 1}]})
            engine = PausedInterviewModelFixture()
            broker.inference_runner._engine_factory = lambda *_a, **_kw: engine
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    context = browser.new_context(viewport={"width": 1440, "height": 900})
                    api = context.request
                    headers = {"Authorization": f"Bearer {token}"}
                    for path, body in [("/api/desk/seed", {}), ("/api/setup/onboarding", {"disposition": "completed"})]:
                        method = api.put if "onboarding" in path else api.post
                        response = method(url + path, data=body, headers=headers)
                        assert response.ok, response.text()
                    response = api.post(url + "/api/threads", data={"title": "Architecture decision context", "recipe_id": INTERVIEW_MODE_ID}, headers=headers)
                    assert response.ok, response.text()
                    tid = response.json()["id"]
                    page = context.new_page()
                    page_errors = []
                    page.on("pageerror", lambda error: page_errors.append(str(error)))
                    page.goto(f"{url}/?token={token}&open=thread:{tid}", wait_until="load")
                    composer = page.locator(".thread-composer-input")
                    composer.wait_for(timeout=20000)
                    composer.fill("Recover decision context")
                    if with_desktops:
                        page.get_by_role("button", name="Floor", exact=True).click()
                        page.get_by_role("button", name="Change places", exact=True).click()
                        page.get_by_label("Favorite Night Train", exact=True).click()
                        page.locator('[data-atmosphere-choice="night-train"]').click()
                        page.locator('[data-atmosphere="night-train"] canvas[data-ready="true"]').wait_for(timeout=20000)
                        page.locator("#surface-places").get_by_role("button", name="Settle in", exact=True).click()
                        page.locator('[data-settled="true"]').wait_for()
                        expect(composer).to_have_value("Recover decision context")
                        page.screenshot(path=str(root / ".tmp/integration-desktop-interview.png"), full_page=True)
                        page.keyboard.press("Escape")
                        expect(page.locator('[data-settled="true"]')).to_have_count(0)
                    page.locator(".thread-foot").get_by_role("button", name="Send", exact=True).click()
                    deadline = time.monotonic() + 20
                    while not engine.awaiting_answer.is_set() and time.monotonic() < deadline:
                        page.wait_for_timeout(50)
                    assert engine.awaiting_answer.is_set(), "Tools did not finish before the answer pause"
                    activity = page.get_by_test_id("tool-activity")
                    expect(activity).to_have_count(1, timeout=10000)
                    rows = activity.get_by_test_id("tool-row")
                    expect(rows).to_have_count(2, timeout=10000)
                    assert not activity.evaluate("el => el.open")
                    for row in rows.all():
                        expect(row).not_to_be_visible()
                    expect(page.locator(".thread-row-assistant > .thread-row-body")).to_have_text("")
                    page.screenshot(path=str(root / ".tmp/tool-activity-before-answer.png"), full_page=True)
                    # An explicit choice to inspect survives the final reply.
                    activity.locator("summary").first.click()
                    for row in rows.all():
                        expect(row).to_be_visible()
                    engine.release_answer.set()
                    deadline = time.monotonic() + 30
                    detail = {}
                    while time.monotonic() < deadline:
                        detail = api.get(url + f"/api/threads/{tid}", headers=headers).json()
                        if detail["interview"]["suggestions"].get("brief") and any(m["role"] == "assistant" and m.get("completed_at") for m in detail["messages"]):
                            break
                        time.sleep(.1)
                    assert detail["interview"]["suggestions"].get("brief"), detail
                    expect(page.locator(".thread-row-assistant > .thread-row-body")).to_contain_text("A manual decision review brief", timeout=10000)
                    assert activity.evaluate("el => el.open"), "Reply reset the reader's disclosure choice"
                    activity.locator("summary").first.click()
                    for row in rows.all():
                        expect(row).not_to_be_visible()
                    page.screenshot(path=str(root / ".tmp/tool-activity-after-answer.png"), full_page=True)
                    page.get_by_role("button", name=re.compile("^Context")).click()
                    page.get_by_text("Decision review brief", exact=True).wait_for(timeout=10000)
                    assert page.locator(".thread-messages").bounding_box()["height"] >= 100, "Expanded context crowded out the conversation"
                    page.get_by_role("button", name="Try draft", exact=True).scroll_into_view_if_needed()
                    page.screenshot(path=str(root / ".tmp/interview-walk-1440.png"), full_page=True)
                    page.get_by_role("button", name="Try draft", exact=True).click()
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline:
                        detail = api.get(url + f"/api/threads/{tid}", headers=headers).json()
                        completed = [m for m in detail["messages"] if m["role"] == "assistant" and m.get("completed_at")]
                        if len(completed) == 2:
                            break
                        time.sleep(.1)
                    assert len(completed) == 2 and not completed[-1].get("error_json")
                    assert detail["interview"]["suggestions"]["brief"]["disposition"] == "try"
                    page.get_by_role("button", name="Keep as artifact", exact=True).last.click()
                    page.wait_for_timeout(500)
                    with db._connection() as conn:
                        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] >= 1
                    page.get_by_label("Section", exact=True).select_option("decisions")
                    page.wait_for_timeout(400)
                    page.reload(wait_until="load")
                    page.get_by_label("Section", exact=True).wait_for(timeout=10000)
                    assert page.get_by_label("Section", exact=True).input_value() == "decisions"
                    if with_desktops:
                        assert page.evaluate('localStorage.getItem("hs.desk.atmosphere")') == "night-train"
                        assert page.evaluate('JSON.parse(localStorage.getItem("hs.desk.atmosphere.favorites"))') == ["night-train"]
                        expect(page.locator('[data-settled="true"]')).to_have_count(0)
                    page.set_viewport_size({"width": 393, "height": 852})
                    page.wait_for_timeout(500)
                    page.get_by_role("button", name=re.compile("^Context")).click()
                    page.screenshot(path=str(root / ".tmp/interview-walk-393.png"), full_page=True)
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Horizontal overflow"
                    page.get_by_label("Section", exact=True).select_option("people")
                    page.get_by_role("button", name="Open People", exact=True).wait_for()
                    assert page.locator(".thread-composer-input").count() == 0
                    page.screenshot(path=str(root / ".tmp/interview-walk-people-393.png"), full_page=True)
                    facts = api.get(url + f"/api/threads/{tid}", headers=headers).json()["interview"]["facts"]
                    assert len(facts) == 1
                    assert not page_errors, page_errors
                    print(json.dumps({"result": "pass", "model": "scripted fixture; not live model quality", "desktops": "Night Train renders; change places and settle preserve Thread draft; preference and favorite survive reload" if with_desktops else "not exercised", "viewports": [1440, 393], "model_passes": engine.calls, "tool_activity": "collapsed before final answer; manual expansion preserved at completion", "revisit": "same thread, section and fact retained", "people": "handoff before composer input", "screenshots": ["tool-activity-before-answer.png", "tool-activity-after-answer.png", "interview-walk-1440.png", "interview-walk-393.png", "interview-walk-people-393.png"]}))
                    browser.close()
            finally:
                engine.release_answer.set()
                server.stop()
                runtime._dispose(broker)
                reset_database()
