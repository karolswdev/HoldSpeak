"""Honest isolated-HOME browser glass for the Thought Workbench first slice.

HS-201-12 re-pointed the FACE half of this rig, doctrine (a): the settled
design of story 12 rebuilt this window as one column of four bands, so the
formatting rail, the Info verb, the Note/Interview tab nav, the two-pane
geometry, the "Added to Note" marker chip and the chained turn
("Add & ask next") are gone from it — every assertion about them described
a face that no longer exists. What this rig still owns, and still proves
against the real hub, is the CUSTODY half: a durable Note edit made while
the AI runs suppresses the frozen question; the working-save sequence is
409-then-200 under the write fence; the raw capture never leaves the hub;
a service restart never redispatches settled work. The band composition
itself is fenced by `test_hs201_12_thought_note_glass.py`.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Workbench glass needs Playwright")
pytest.importorskip("fastapi.testclient", reason="Workbench glass needs web dependencies")

TOKEN = "hs141-workbench-glass"


class _InterviewEngine:
    active_provider = "deterministic-thought-interview"

    def __init__(self) -> None:
        self.calls = 0
        self.block_next = False
        self.started = threading.Event()
        self.release = threading.Event()

    def run_prompt(self, *, user_prompt: str, **_kwargs: object) -> str:
        self.calls += 1
        assert "Launch ownership" in user_prompt
        if self.block_next:
            self.block_next = False
            self.started.set()
            assert self.release.wait(10), "blocked interview engine was never released"
            return ('{"kind":"question","question":"STALE QUESTION MUST NOT APPEAR",'
                    '"reason":"This result belongs to the pre-edit Note."}')
        return ('{"kind":"question","question":"Who owns the launch?",'
                '"reason":"A named owner makes the Note actionable."}')


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: 'Bearer hs141-workbench-glass',
              ...(body ? {'content-type': 'application/json'} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_workbench_real_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    model = tmp_path / "deterministic-this-machine.gguf"
    model.touch()
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    provider = {"path": str(model)}
    monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path", lambda: provider["path"])
    reset_database()
    database = db_core.get_database()
    engine = _InterviewEngine()
    broker = _configure(database)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
    callbacks = WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {})
    server = MeetingWebServer(callbacks, auth_token=TOKEN)
    url = server.start()
    errors: list[str] = []
    console_errors: list[str] = []
    requests: list[str] = []
    responses: list[tuple[str, int]] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("request", lambda request: requests.append(request.url) if "/api/thoughts/" in request.url else None)
            page.on("response", lambda response: responses.append((response.url, response.status)) if "/api/thoughts/" in response.url else None)
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            created = _api(page, "POST", "/api/thoughts", {
                "request_id": str(uuid.uuid4()),
                "raw_text": "RAW CUSTODY PHRASE — launch ownership first capture.",
                "source": {"kind": "typed"},
                "initial_note": {
                    "title": "Launch ownership",
                    "body_markdown": "Launch ownership needs one accountable person.",
                    "tags": ["launch"],
                },
            })
            thought = created["thought"]
            page.evaluate(
                "([id, receipt]) => sessionStorage.setItem(`hs.thought.default-context-receipt.${id}`, JSON.stringify(receipt))",
                [thought["id"], created["default_context_receipt"]],
            )
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.get_by_role("region", name="Thought", exact=True)
            try:
                workspace.wait_for(timeout=10000)
            except Exception:
                page.screenshot(path=f"/tmp/holdspeak-thought-workbench-open-failure-{width}.png", full_page=False)
                raise AssertionError({"body": page.locator("body").inner_text(), "errors": errors,
                                      "console": console_errors, "requests": requests})
            page.get_by_role("region", name="Note", exact=True).wait_for()
            band = page.get_by_role("region", name="One question", exact=True)
            band.wait_for(timeout=10000)
            ask = band.get_by_role("button", name="Ask", exact=True)
            ask.wait_for()
            assert workspace.locator(".btn--primary:visible").count() == 1
            assert workspace.locator(".btn--primary:visible").inner_text().strip() == "Finish"
            assert page.get_by_text("Good enough").count() == 0
            assert page.get_by_text("Keep refining").count() == 0
            assert page.get_by_text("Finish instead").count() == 0
            # Doctrine (a): the rail, the tabs and the second pane left this
            # window with the story-12 design; their absence is the proof.
            assert workspace.get_by_role("toolbar", name="Markdown formatting").count() == 0
            assert workspace.get_by_role("region", name="Interview", exact=True).count() == 0
            assert workspace.get_by_role("button", name="Info", exact=True).count() == 0

            window_box = workspace.bounding_box()
            assert window_box and window_box["y"] >= 48
            assert window_box["y"] + window_box["height"] <= 900
            note_box = page.get_by_role("region", name="Note", exact=True).bounding_box()
            band_box = band.bounding_box()
            foot_box = workspace.locator(".surface-footer").bounding_box()
            assert note_box and band_box and foot_box
            # One column, four bands, in order, all inside the window.
            assert note_box["y"] + note_box["height"] <= band_box["y"] + 1
            assert band_box["y"] + band_box["height"] <= foot_box["y"] + 1
            assert foot_box["y"] + foot_box["height"] <= window_box["y"] + window_box["height"] + 1
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.evaluate("document.body.scrollWidth <= innerWidth")
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-idle-{width}.png", full_page=False)

            # A real durable Note edit while ASKING must suppress the frozen
            # result. The stale question never reaches owner-visible state.
            engine.block_next = True
            ask.click()
            page.wait_for_function(
                "el => el?.textContent?.trim() === 'Stop'",
                arg=band.get_by_role("button").first.element_handle(),
                timeout=10000,
            )
            assert engine.started.wait(5)
            note_editor = page.get_by_role("textbox", name="Note body")
            assert note_editor.get_attribute("contenteditable") == "true"
            note_editor.click()
            page.keyboard.press("Meta+ArrowDown")
            page.keyboard.press("Enter")
            page.keyboard.insert_text("Edited while asking.")
            assert "Edited while asking." in note_editor.inner_text()
            page.keyboard.press("Control+s")
            deadline = time.time() + 5
            edited = _api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
            while "Edited while asking." not in edited["working_note"]["body_markdown"] and time.time() < deadline:
                time.sleep(0.05)
                edited = _api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
            assert "Edited while asking." in edited["working_note"]["body_markdown"]
            working_statuses = [status for path, status in responses if path.endswith(f"/api/thoughts/{thought['id']}/working")]
            assert working_statuses[-2:] == [409, 200], working_statuses
            engine.release.set()
            band.get_by_role("button", name="Ask", exact=True).wait_for(timeout=20000)
            assert page.get_by_text("STALE QUESTION MUST NOT APPEAR", exact=True).count() == 0

            # ── The one question, answered with the one verb ──
            band.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=20000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.fill("Mina owns the launch.")
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-question-{width}.png", full_page=False)
            assert band.get_by_role("button", name="Add to note", exact=True).count() == 1
            assert band.get_by_role("button", name="Add & ask next").count() == 0
            assert workspace.locator(".btn--primary:visible").count() == 1
            band.get_by_role("button", name="Add to note", exact=True).click()
            page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for(timeout=20000)
            assert workspace.locator(".thought-note-body .cm-scroller").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            # The answer is a pure write: no second turn was dispatched.
            time.sleep(0.35)
            assert engine.calls == 2, engine.calls

            # Raw capture stays on the hub: this window never asks for it.
            assert page.get_by_text("RAW CUSTODY PHRASE — launch ownership first capture.", exact=True).count() == 0
            assert not any(path.endswith(f"/api/thoughts/{thought['id']}/original") for path in requests)

            # The Reads well is in-window (no portal overlay) and Escape-safe.
            change = workspace.get_by_role("button", name="Change", exact=True)
            change.click()
            well = page.get_by_role("region", name="What the AI reads")
            well.wait_for(timeout=10000)
            assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
            well_box = well.bounding_box()
            assert well_box and well_box["y"] + well_box["height"] <= window_box["y"] + window_box["height"] + 1
            page.screenshot(path=f"/tmp/holdspeak-thought-context-well-{width}.png", full_page=False)
            well.press("Escape")
            assert page.get_by_role("region", name="What the AI reads").count() == 0
            page.wait_for_function("el => el === document.activeElement", arg=change.element_handle(), timeout=5000)

            unexpected_before_restart = [
                message for message in console_errors
                if "server responded with a status of 409 (Conflict)" not in message
            ]
            assert not unexpected_before_restart, console_errors
            console_errors.clear()

            # Restart the real HTTP service on the same durable isolated HOME.
            # Reloading must project the settled work, never redispatch it.
            restart_port = server.port
            server.stop()
            server = MeetingWebServer(callbacks, port=restart_port, auth_token=TOKEN)
            assert server.start() == url
            page.reload(wait_until="load")
            page.get_by_role("region", name="Thought", exact=True).wait_for(timeout=10000)
            page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for()
            time.sleep(0.35)
            assert engine.calls == 2, "service restart redispatched settled work"
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            workspace = page.get_by_role("region", name="Thought", exact=True)
            assert workspace.locator(".btn--primary:visible").count() == 1
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-{width}.png", full_page=False)

            # The workbench read is one bounded projection, and no page/console
            # exception or horizontal escape is hidden by the screenshot.
            assert sum(path.endswith(f"/api/thoughts/{thought['id']}/workbench") for path in requests) >= 1
            assert not errors, errors
            unexpected_console = [
                message for message in console_errors
                if "ERR_CONNECTION_REFUSED" not in message
            ]
            assert not unexpected_console, console_errors
            browser.close()
    finally:
        server.stop()
