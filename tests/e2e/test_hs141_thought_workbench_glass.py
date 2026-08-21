"""Honest isolated-HOME browser glass for the Thought Workbench first slice."""
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
            primary = workspace.locator(".thought-state-primary")
            primary.wait_for()
            assert primary.inner_text() == "Ask AI"
            idle_box = primary.bounding_box()
            assert idle_box
            assert workspace.locator(".btn--primary:visible").count() == 1
            assert page.get_by_text("Good enough").count() == 0
            assert page.get_by_text("Keep refining").count() == 0
            assert page.get_by_text("Finish instead").count() == 0
            formatting = workspace.get_by_role("toolbar", name="Markdown formatting")
            formatting.wait_for()
            for control in ["Bold", "Italic", "Underline"]:
                assert formatting.get_by_role("button", name=control).is_visible()
            assert formatting.get_by_role("button", name="H1").is_visible()
            assert formatting.get_by_role("button", name="List").is_visible()

            window_box = workspace.bounding_box()
            assert window_box and window_box["y"] >= 48
            assert window_box["y"] + window_box["height"] <= 900
            note_box = page.get_by_role("region", name="Note", exact=True).bounding_box()
            if width == 1440:
                interview_box = page.get_by_role("region", name="Interview", exact=True).bounding_box()
                assert window_box["width"] >= 1000, workspace.evaluate("el => ({style: el.getAttribute('style'), width: getComputedStyle(el).width, minWidth: getComputedStyle(el).minWidth, classes: el.className})")
                assert note_box and interview_box
                assert note_box["width"] >= 650 and note_box["height"] >= 360
                assert 300 <= interview_box["width"] <= 380 and interview_box["height"] >= 360
                assert note_box["x"] + note_box["width"] <= interview_box["x"] + 1
                assert note_box["y"] == pytest.approx(interview_box["y"], abs=1)
            else:
                hidden_interview = workspace.locator(".thought-interview")
                assert hidden_interview.get_attribute("aria-hidden") == "true"
                assert hidden_interview.get_attribute("inert") is not None
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.evaluate("document.body.scrollWidth <= innerWidth")
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-idle-{width}.png", full_page=False)

            # A real durable Note edit while ASKING must suppress the frozen
            # result. The stale question never reaches owner-visible state.
            engine.block_next = True
            primary.click()
            if width == 1440:
                page.get_by_text("Finding one useful question…", exact=True).wait_for(timeout=10000)
            else:
                page.wait_for_function(
                    "el => el?.textContent?.trim() === 'Stop'",
                    arg=primary.element_handle(),
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
            page.wait_for_function("el => el?.textContent?.trim() === 'Ask AI'", arg=primary.element_handle(), timeout=20000)
            assert page.get_by_text("STALE QUESTION MUST NOT APPEAR", exact=True).count() == 0

            primary.click()
            if width == 393:
                page.wait_for_function("el => el?.textContent?.trim() === 'Answer question'", arg=primary.element_handle(), timeout=20000)
                assert primary.inner_text() == "Answer question"
                primary.click()
            page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=20000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.fill("Mina owns the launch.")
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-question-{width}.png", full_page=False)
            assert primary.inner_text() == "Add & ask next"
            question_box = primary.bounding_box()
            assert question_box and idle_box
            assert question_box["x"] == pytest.approx(idle_box["x"], abs=1)
            assert question_box["y"] == pytest.approx(idle_box["y"], abs=1)
            assert question_box["width"] == pytest.approx(idle_box["width"], abs=1)
            assert workspace.locator(".btn--primary:visible").count() == 1

            # Admission is re-evaluated under the write fence. Remove the only
            # target after the question: answer/focus/key survive the refusal.
            provider["path"] = None
            primary.click()
            page.get_by_text("Couldn't start the next turn. Your answer is still here. Add it to the Note.", exact=True).wait_for(timeout=10000)
            assert answer.input_value() == "Mina owns the launch."
            assert answer.evaluate("el => el === document.activeElement")
            assert engine.calls == 2

            # The refusal did not mutate the review. Restore readiness and
            # reopen its fresh reducer, then exercise the atomic composite.
            provider["path"] = str(model)
            page.reload(wait_until="load")
            workspace = page.get_by_role("region", name="Thought", exact=True)
            workspace.wait_for(timeout=10000)
            primary = workspace.locator(".thought-state-primary")
            if width == 393:
                workspace.get_by_role("button", name="Interview 1", exact=True).click()
            page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=10000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.fill("Mina owns the launch.")
            with page.expect_response(
                lambda response: response.url.endswith("/answer-and-continue"),
                timeout=10000,
            ) as composite_response:
                primary.click()
            composite = composite_response.value
            composite_body = composite.json()
            assert composite.status == 202, composite_body
            marker_name = "Added to Note · View" if width == 393 else "Added to Note"
            marker = workspace.get_by_role("button", name=marker_name, exact=True)
            try:
                marker.wait_for(timeout=10000)
            except Exception:
                raise AssertionError({
                    "composite": composite_body,
                    "workspace": workspace.inner_text(),
                    "errors": errors,
                    "console": console_errors,
                })
            if width == 393:
                marker.click()
            page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for()
            assert workspace.locator(".thought-document-body .cm-scroller").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            deadline = time.time() + 10
            while engine.calls < 3 and time.time() < deadline:
                time.sleep(0.05)
            assert engine.calls == 3
            time.sleep(0.35)
            assert engine.calls == 3, "composite child was dispatched more than once"

            # Raw capture stays absent until the owner explicitly opens Info.
            assert page.get_by_text("RAW CUSTODY PHRASE — launch ownership first capture.", exact=True).count() == 0
            assert not any(path.endswith(f"/api/thoughts/{thought['id']}/original") for path in requests)
            info = workspace.get_by_role("button", name="Info", exact=True)
            info.click()
            page.get_by_text("RAW CUSTODY PHRASE — launch ownership first capture.", exact=True).wait_for()
            page.keyboard.press("Escape")
            assert page.get_by_text("RAW CUSTODY PHRASE — launch ownership first capture.", exact=True).count() == 0
            page.wait_for_function("el => el === document.activeElement", arg=info.element_handle())

            # The real context sheet is reachable, Escape-safe, and touch-safe.
            context_rack = workspace.get_by_label("AI context")
            context_rack.get_by_role("button", name="Attach").click()
            picker = page.get_by_role("region", name="Attach context")
            picker.wait_for()
            assert picker.get_by_text("Choose what AI may use for this Thought.").is_visible()
            assert picker.get_by_placeholder("Find a note…").is_visible()
            picker_box = picker.bounding_box()
            assert picker_box and picker_box["y"] >= 12
            assert picker_box["y"] + picker_box["height"] <= 848
            page.screenshot(path=f"/tmp/holdspeak-thought-context-picker-{width}.png", full_page=False)
            if width == 393:
                for control in [picker.get_by_role("button", name="Close"), picker.get_by_role("button", name="Browse all notes")]:
                    box = control.bounding_box()
                    assert box and box["height"] >= 44
            page.keyboard.press("Escape")
            assert picker.count() == 0
            assert context_rack.evaluate("el => el === document.activeElement")

            unexpected_before_restart = [
                message for message in console_errors
                if "server responded with a status of 409 (Conflict)" not in message
            ]
            assert not unexpected_before_restart, console_errors
            console_errors.clear()

            # Restart the real HTTP service on the same durable isolated HOME.
            # Reloading must project the existing child, never redispatch it.
            restart_port = server.port
            server.stop()
            server = MeetingWebServer(callbacks, port=restart_port, auth_token=TOKEN)
            assert server.start() == url
            page.reload(wait_until="load")
            page.get_by_role("region", name="Thought", exact=True).wait_for(timeout=10000)
            page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for()
            time.sleep(0.35)
            assert engine.calls == 3, "service restart redispatched a completed child"
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
