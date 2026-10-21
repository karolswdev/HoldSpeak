"""The Ask window, AS RENDERED: what only a real browser proves (the test diet).

Betterment Q6 (docs/internal/betterment/asking/RECIPE.md): a desk object
dropped on the Ask window becomes an About chip. The drop is a real HTML drag
from the Screen's note icon (the hand's drag: `hand/drag.ts`) onto the window,
through the real hub on an isolated HOME at 1440 x 900. The phone (393) has no
loose Screen icons to drag; its About is the picker
(web/src/desk/components/about/__tests__/about.app.test.tsx).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair

pytest.importorskip("playwright.sync_api", reason="the Ask glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "ask-glass"
T = 20_000
NOTE_ID, NOTE = "n-mira", "1:1 with Mira"
ICON = f".desk-screen [data-object-id='note:{NOTE_ID}']"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    PrimitiveService(get_database()).create_note(
        Principal(PrincipalKind.OWNER, "karol"), note_id=NOTE_ID, title=NOTE,
        body_markdown="Feedback on her cutover design doc is due Friday.", tags=[])
    try:
        yield base
    finally:
        server.stop()


def test_1440_a_screen_note_dropped_on_ask_becomes_an_about_chip(hub: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                                   reduced_motion="reduce").new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        try:
            page.goto(f"{hub}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            page.locator(ICON).wait_for(timeout=T)
            page.keyboard.press("Control+KeyI")
            body = page.get_by_test_id("ask-body")
            body.wait_for(timeout=T)
            about = page.get_by_test_id("ask-context")
            assert "My whole desk" in about.inner_text()
            # The window opens over the Screen's icons: move it by its title
            # strip until the note's icon is clear.
            icon_box = page.locator(ICON).bounding_box()
            frame = page.locator("[id='ask']")
            box = frame.bounding_box()
            assert icon_box and box
            grab = (box["x"] + 120, box["y"] + 12)
            shift = max(0.0, icon_box["y"] + icon_box["height"] + 24 - box["y"])
            page.mouse.move(*grab)
            page.mouse.down()
            page.mouse.move(grab[0], grab[1] + shift / 2, steps=6)
            page.mouse.move(grab[0], grab[1] + shift, steps=6)
            page.mouse.up()
            moved = frame.bounding_box()
            assert moved and moved["y"] > icon_box["y"] + icon_box["height"], (icon_box, moved)
            page.locator(ICON).drag_to(body)
            about.get_by_test_id("ask-about-chip").filter(has_text=NOTE).wait_for(timeout=T)
            assert "My whole desk" not in about.inner_text()
            assert not errors, errors
        finally:
            browser.close()


@pytest.mark.parametrize("width", [1440, 393])
def test_firefox_ask_enter_clears_at_send_and_keeps_the_next_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """A real private Hub and gated HTTP model; only inference is simulated.

    No intercepted API answers: model admission, Ask orchestration, kept
    thread, durable editor and rendered Firefox layout all use product code.
    """
    import json
    import threading
    from http.server import ThreadingHTTPServer

    from playwright.sync_api import expect, sync_playwright
    from tests._evidence import evidence_dir
    from .engine_stub_rig import _StubHandler
    from .glass_infra import _settle, clear_hub_windows

    answer = "## Platform checkpoint\n\nReview the rollback plan with Mira on Friday."
    release, started = threading.Event(), threading.Event()
    requests: list[dict] = []

    class Model(_StubHandler):
        MODEL = "ask-feedback-fixture"

        def do_POST(self) -> None:  # noqa: N802 - HTTP handler contract
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            requests.append(request)
            started.set()
            release.wait(30)
            body = json.dumps({
                "id": "ask-feedback", "object": "chat.completion", "model": self.MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": answer}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 9, "total_tokens": 21},
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    model = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=model.serve_forever, daemon=True).start()
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = evidence_dir("ask-feedback")
    try:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852},
                                    device_scale_factor=1, reduced_motion="reduce")
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                provider = _api(page, "POST", "/api/inference/model-library/define-endpoint", {
                    "draft": {"request_id": "ask-feedback-model", "profile_id": "ask-feedback-model",
                              "expected_profile_revision": 0, "label": "Ask fixture",
                              "provider_family": "openai_compatible", "model": Model.MODEL,
                              "endpoint": f"http://127.0.0.1:{model.server_port}/v1", "requires_key": False},
                    "secret": None,
                }, token=TOKEN)["provider"]
                _api(page, "POST", "/api/inference/assignments/set", {
                    "command_id": "ask-feedback-assignment", "expected_revision": 0,
                    "scope": {"kind": "capability", "capability_id": "ask.answer"},
                    "entries": [{"profile_id": provider["profile_id"], "profile_revision": provider["profile_revision"]}],
                }, token=TOKEN)
                clear_hub_windows(page, TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.keyboard.press("Control+KeyI")
                window = page.locator("[id='ask'][data-layer='window']")
                editor = window.get_by_role("textbox", name="Ask about your work", exact=True)
                editor.wait_for()
                _settle(page)
                page.screenshot(path=str(shots / f"ask-empty-{width}.png"))
                facts = window.evaluate("""el => {
                  const rect = el.getBoundingClientRect();
                  const fields = node => {const r=node.getBoundingClientRect();return {
                    tag:node.tagName, cls:String(node.className), x:r.x, width:r.width,
                    scroll:node.scrollWidth, client:node.clientWidth,
                    margin:getComputedStyle(node).margin, gap:getComputedStyle(node).gap};};
                  return {window:fields(el), body:fields(el.querySelector('[data-testid="ask-body"]')), overflows:[...el.querySelectorAll('*')].filter(node => {
                    const r=node.getBoundingClientRect();return r.width && (r.right>rect.right+1 || r.left<rect.left-1);
                  }).map(fields)};
                }""")
                (shots / f"ask-layout-{width}.json").write_text(json.dumps(facts, indent=2))
                assert editor.bounding_box()["height"] <= 170
                # The floating resize chrome occupies four pixels of the frame's
                # border box; test the editable body and every visible child.
                assert not facts["overflows"], facts
                assert facts["body"]["scroll"] <= facts["body"]["client"] + 1, facts
                assert window.evaluate("el => {const r=el.getBoundingClientRect();return r.left>=-1 && r.right<=innerWidth+1;}")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                window.get_by_role("button", name="What needs my attention?", exact=True).click()
                expect(editor).to_have_value("What needs my attention?")
                expect(editor).to_be_focused()
                assert not requests
                editor.press("Shift+Enter")
                expect(editor).to_have_value("What needs my attention?\n")
                assert not requests

                question, draft = "What should I review with Mira?", "And what can wait until Monday?"
                editor.fill(question)
                editor.press("Enter")
                expect(editor).to_have_value("")
                expect(window.get_by_role("button", name="Stop", exact=True)).to_be_visible()
                expect(window.get_by_role("region", name="Ask conversation")).to_contain_text(question)
                assert started.wait(10), "Private model did not receive the real Ask"
                editor.fill(draft)
                editor.press("Enter")
                expect(editor).to_have_value(draft)
                assert len(requests) == 1
                page.screenshot(path=str(shots / f"ask-pending-{width}.png"))
                with page.expect_response(lambda response: response.url.endswith("/api/ask")
                                          and response.request.method == "POST") as finished:
                    release.set()
                result = finished.value.json()
                assert finished.value.ok and result.get("output") == answer, result
                expect(window.get_by_role("heading", name="Platform checkpoint", exact=True)).to_be_visible()
                expect(editor).to_have_value(draft)
                assert page.evaluate("JSON.parse(localStorage.getItem('hs.draft.v1.desk-ask')).text") == draft
                assert len(requests) == 1
                kept = _api(page, "GET", f"/api/threads/{result['thread_id']}", token=TOKEN)
                assert question in json.dumps(kept)
                assert "Review the rollback plan" in json.dumps(kept)
                _settle(page)
                assert window.get_by_test_id("ask-body").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                assert window.evaluate("el => {const r=el.getBoundingClientRect();return r.left>=-1 && r.right<=innerWidth+1;}")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(shots / f"ask-answer-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
    finally:
        release.set()
        server.stop()
        model.shutdown()
        model.server_close()
