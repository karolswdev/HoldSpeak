"""Recordings selection, confirmation and bounded wells at both Desk sizes."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_desk_sweep import AIR_WORDS_JS, LIST_GRAMMAR_JS, _start_app_walk

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "recordings-grammar"


def _recorded(name: str) -> dict[str, Any]:
    source = (ROOT / f"web/src/desk/recordings/__fixtures__/{name}.ts").read_text()
    return json.loads(source[source.index("= {") + 2:].strip().removesuffix(";"))


def _verb(page: Any, window: Any, label: str, *, more: bool = False) -> None:
    button = window.get_by_role("button", name="More" if more else label, exact=True)
    if button.is_visible():
        button.click()
    else:
        window.get_by_role("button", name="Actions ▾", exact=True).click()
        page.get_by_role("menuitem", name="More" if more else label, exact=False).click()
    if more:
        page.get_by_role("menuitem", name=label, exact=False).click()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_recordings_selection_and_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = ROOT / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    listed = _recorded("recordings.list")
    ready = _recorded("recording.ready")
    failed = _recorded("recording.failed")
    payload = {**listed}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.route("**/api/recordings", lambda route, _request: route.fulfill(json=payload))
            clear_hub_windows_http(base, TOKEN)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            # Film only a test canvas; no screen, microphone or provider is used.
            media = page.evaluate("""async () => {
              const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 360;
              const ink = canvas.getContext('2d'); ink.fillStyle = '#10192b'; ink.fillRect(0, 0, 640, 360);
              ink.fillStyle = '#ffffff'; ink.font = '32px sans-serif'; ink.fillText('Desk recording', 40, 180);
              const stream = canvas.captureStream(0), track = stream.getVideoTracks()[0], chunks = [];
              const recorder = new MediaRecorder(stream, {mimeType:'video/webm;codecs=vp9'});
              recorder.ondataavailable = event => chunks.push(event.data);
              const ended = new Promise(resolve => recorder.onstop = resolve);
              const begun = new Promise(resolve => recorder.onstart = resolve);
              recorder.start(); track.requestFrame(); await begun;
              for (let frame = 0; frame < 6; frame++) {
                ink.fillRect(40 + frame * 8, 220, 6, 6); track.requestFrame(); await new Promise(requestAnimationFrame);
              }
              recorder.stop(); await ended; stream.getTracks().forEach(track => track.stop());
              return {video:Array.from(new Uint8Array(await new Blob(chunks, {type:'video/webm'}).arrayBuffer())), poster:canvas.toDataURL()};
            }""")
            page.route("**/api/recordings/*/video*", lambda route: route.fulfill(body=bytes(media["video"]), content_type="video/webm"))
            page.route("**/api/recordings/*/poster*", lambda route: route.fulfill(body=base64.b64decode(media["poster"].split(",", 1)[1]), content_type="image/png"))
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'open-recordings'}))")
            page.reload(wait_until="load")
            _normal_chair(page)
            window = page.locator("#surface-recordings")
            window.get_by_test_id("recordings-window").wait_for()
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-recordings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)

            def shot(state: str) -> None:
                _settle(page)
                assert window.evaluate("""el => {
                  const body = el.querySelector('.desk-surface-body');
                  const pane = el.querySelector('[data-testid=recordings-window]');
                  return body.scrollHeight <= body.clientHeight + 1 && body.scrollWidth <= body.clientWidth + 1
                    && pane.scrollHeight <= pane.clientHeight + 1;
                }"""), state
                assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-recordings"), state
                assert not page.evaluate(AIR_WORDS_JS, "#surface-recordings")["air"], state
                assert window.evaluate("""el => [...el.querySelectorAll('video')].every(video => {
                  const box = video.getBoundingClientRect();
                  const seat = video.closest('.gadget-row-gadget').getBoundingClientRect();
                  return box.right <= seat.right + 1 && box.width <= seat.width + 1;
                })"""), state
                assert window.evaluate("""el => [...el.querySelectorAll('.surface-pane-inspector')].every(inspector => {
                  const well = inspector.querySelector('.surface-preference-well');
                  const actions = inspector.querySelector(':scope > .surface-pane-actions');
                  return !well || !actions || well.getBoundingClientRect().bottom <= actions.getBoundingClientRect().top + 1;
                })"""), state
                assert window.locator('[data-testid=recordings-row] button').count() == 0
                page.screenshot(path=str(shots / f"recordings-{state}-{'900x600' if width == 1440 else '393'}-after.png"))

            def select(recording_id: str) -> Any:
                row = window.locator(f'[data-object-id="{recording_id}"]')
                row.click()
                expect(row).to_have_attribute("aria-selected", "true")
                return row

            def reopen(next_payload: dict[str, Any]) -> None:
                nonlocal payload
                payload = next_payload
                page.reload(wait_until="load")
                _normal_chair(page)
                window.get_by_test_id("recordings-window").wait_for()
                _settle(page)

            shot("list")
            expect(window.get_by_text("Select a recording.", exact=True)).to_be_visible()
            row = select(ready["id"])
            shot("ready")
            window.locator(".surface-preference-well").evaluate("el => el.scrollTop = el.scrollHeight")
            shot("details-end")
            window.locator(".surface-preference-well").evaluate("el => el.scrollTop = 0")
            assert window.get_by_test_id("recordings-row").filter(has_text="Ready").count() == 0
            # The list keeps room for the header and three complete rows.
            assert window.locator(".surface-list-pane-list").evaluate("""el => {
              const head = el.querySelector('.object-list-head').getBoundingClientRect();
              const row = el.querySelector('.object-list-row').getBoundingClientRect();
              const well = el.querySelector('.object-list-rows').getBoundingClientRect();
              return well.height >= row.height * 3 - 1;
            }""")
            row.press("ArrowUp")
            expect(window.locator(f'[data-object-id="{failed["id"]}"]')).to_have_attribute("aria-selected", "true")
            expect(window.get_by_test_id("recordings-wait")).to_be_in_viewport()
            shot("failed")
            select(ready["id"])
            row.click(button="right")
            expect(page.get_by_role("menuitem", name="Open note", exact=False)).to_be_visible()
            shot("context-menu")
            page.keyboard.press("Escape")
            _verb(page, window, "Remove")
            expect(window.get_by_role("region", name="Remove recording?", exact=True)).to_be_visible()
            shot("remove")
            window.get_by_role("button", name="Cancel", exact=True).click()
            expect(row).to_have_attribute("aria-selected", "true")
            window.get_by_role("tab", name="Video", exact=True).click()
            expect(window.get_by_test_id("recordings-video")).to_be_visible()
            window.get_by_test_id("recordings-video").evaluate("async video => { video.muted = true; await video.play(); video.pause(); }")
            assert window.get_by_test_id("recordings-video").evaluate("video => video.videoWidth") == 640
            shot("video")
            window.get_by_role("tab", name="Links", exact=True).click()
            shot("links")
            _verb(page, window, "Storage", more=True)
            expect(window.get_by_test_id("settings-recordings-usage")).to_have_text("30 days")
            shot("storage")
            window.get_by_role("button", name="Done", exact=True).click()
            _verb(page, window, "New recording")
            shot("capture")
            # This opens only the form; no physical picker or microphone is used.
            window.get_by_role("button", name="Cancel", exact=True).click()
            window.get_by_role("textbox", name="Find a recording", exact=True).fill("not-here")
            expect(window.get_by_text("No recordings found", exact=True)).to_be_visible()
            shot("find")
            for state, filename in (("empty", "recordings.empty"), ("encoding", "recording.stopped"), ("recording", "recording.recording"), ("webm", "recording.ready"), ("unshared", "recording.ready")):
                data = _recorded(filename)
                if "recordings" not in data:
                    data = {**listed, "recordings": [data]}
                if state == "webm":
                    data["recordings"][0]["encoder"] = "webm"
                if state == "unshared":
                    data["recordings"][0].update(shared=False, links={"tailnet": None, "local": None})
                reopen(data)
                if state != "empty":
                    select(data["recordings"][0]["id"])
                if state == "webm":
                    window.get_by_role("tab", name="Video", exact=True).click()
                    window.get_by_test_id("recordings-video").evaluate("async video => { video.muted = true; await video.play(); video.pause(); }")
                shot(state)
            reopen(_recorded("recordings.empty"))
            page.evaluate("Object.defineProperty(navigator.mediaDevices, 'getDisplayMedia', {configurable:true, value:undefined})")
            _verb(page, window, "New recording")
            expect(window.get_by_text("Record from your computer", exact=True)).to_be_visible()
            shot("unavailable")
            reopen(listed)
            page.evaluate("localStorage.setItem('hs:walk-voice', 'off')")
            _start_app_walk(page)
            script = json.loads((ROOT / "web/src/desk/walks/recordings.walk.json").read_text())
            for step in script["steps"]:
                expect(page.get_by_test_id("walk-question")).to_have_text(step["ask"]["question"])
                page.get_by_test_id("walk-choice-0").click()
            expect(page.get_by_test_id("walk-end")).to_be_visible()
            shot("walk")
            page.close()
            browser.close()
    finally:
        server.stop()
