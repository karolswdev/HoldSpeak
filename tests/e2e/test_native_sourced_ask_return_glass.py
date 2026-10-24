"""P04 first slice on glass: a selected Note is Ask's source and return door.

Only the model's answer is synthetic. Ask, Thread and Save as note use the
isolated hub's real routes and writers. Components is a local specimen.
"""
from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .engine_stub_rig import _StubHandler
from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from .test_desk_sweep import TARGET_JS

pytest.importorskip("playwright.sync_api", reason="P04 glass needs Playwright")

TOKEN = "native-sourced-ask-glass"
SHOTS = "native-sourced-ask-wave4"
HEIGHT = {1440: 900, 393: 852}
NOTE_ID = "n-source-return"
NOTE_TITLE = "Source return review"
QUOTE = "Confirm the handoff before Friday."
SOURCE_BODY = "\n".join(f"Review line {i:02d}: keep this source local." for i in range(90)) + "\n" + QUOTE
ANSWER = "The handoff remains local. Keep the review with the source Note."
THOUGHT = ".desk-window.thought-workspace-window"


def _isolated_boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    # The delivery registry freezes its default before _boot changes HOME.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(
        registry_module, "DEFAULT_REGISTRY_PATH",
        tmp_path / "home" / ".holdspeak" / "delivery_sources.json",
    )
    return _boot(tmp_path, monkeypatch, token=TOKEN)


def _start(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.goto(f"{base}/?token={TOKEN}&open=note:{NOTE_ID}", wait_until="load")
    _normal_chair(page)


def _visible_tail(frame: Any) -> str:
    # CodeMirror virtualizes long bodies. Read the real viewport's last line.
    return frame.locator(".thought-note-body .cm-line").last.inner_text()


def _selection_and_scroll(frame: Any) -> dict[str, Any]:
    return frame.locator(".thought-note-body .cm-content").evaluate("""element => {
      const view = element.closest('.cm-editor');
      const selection = window.getSelection();
      return {text: selection?.toString() || '', scroll: view?.querySelector('.cm-scroller')?.scrollTop || 0};
    }""")


def _current_caret_visible(frame: Any) -> None:
    """Read the painted caret before a Playwright action can scroll it."""
    state = frame.evaluate("""root => {
      const content = root.querySelector('.thought-note-body .cm-content');
      const scroller = root.querySelector('.thought-note-body .cm-scroller');
      const footer = root.querySelector('.surface-footer:has(.thought-note-foot)');
      const selection = window.getSelection();
      const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
      const caret = range?.getClientRects()[0] || range?.getBoundingClientRect();
      const editorBox = scroller?.getBoundingClientRect();
      const footBox = footer?.getBoundingClientRect();
      const caretBox = caret?.toJSON();
      const line = selection?.anchorNode?.parentElement?.closest('.cm-line');
      const hit = caret && editorBox ? document.elementFromPoint(
        Math.max(editorBox.left + 2, Math.min(caret.left, editorBox.right - 2)),
        caret.top + Math.max(1, caret.height / 2)) : null;
      return {focused: document.activeElement === content,
        insideEditor: !!selection?.anchorNode && content?.contains(selection.anchorNode),
        collapsed: !!selection?.isCollapsed,
        text: selection?.toString() || '', lineText: line?.textContent || '', caret: caretBox,
        scroller: editorBox?.toJSON(), footer: footBox?.toJSON(),
        inEditor: !!caret && !!editorBox && caret.top >= editorBox.top - 1
          && caret.bottom <= editorBox.bottom + 1 && caret.left >= editorBox.left - 1
          && caret.right <= editorBox.right + 1,
        aboveFooter: !!caret && !!footBox && caret.bottom <= footBox.top - 1,
        inViewport: !!caret && caret.top >= 0 && caret.bottom <= innerHeight,
        hitInEditor: !!hit && !!scroller && scroller.contains(hit)};
    }""")
    assert state["focused"] and state["insideEditor"] and state["collapsed"] and not state["text"], state
    assert state["lineText"].endswith("Newer source words."), state
    assert state["inEditor"] and state["aboveFooter"] and state["inViewport"] and state["hitInEditor"], state


def _visible_before_scroll(frame: Any, label: str) -> None:
    """Playwright auto-scroll would hide a clipped return verb."""
    state = frame.evaluate("""(root, name) => {
      const button = [...root.querySelectorAll('button')].find(x => x.textContent.trim() === name);
      if (!button) return {missing: name};
      const a = button.getBoundingClientRect(), f = root.getBoundingClientRect();
      const x = a.left + a.width / 2, y = a.top + a.height / 2;
      const hit = document.elementFromPoint(x, y);
      return {rect: a.toJSON(), frame: f.toJSON(),
        inFrame: a.left >= f.left && a.right <= f.right && a.top >= f.top && a.bottom <= f.bottom,
        inViewport: a.left >= 0 && a.right <= innerWidth && a.top >= 0 && a.bottom <= innerHeight,
        hit: hit === button || button.contains(hit)};
    }""", label)
    assert state.get("inFrame") and state.get("inViewport") and state.get("hit"), state


def _target_check(page: Any, selector: str) -> None:
    faults = page.evaluate(TARGET_JS, selector)
    assert not faults, faults


def _raise_ask(page: Any) -> None:
    # Public depth gadget sends the front Note behind the existing Ask.
    page.locator(f"{THOUGHT} .desk-gadget-depth").first.click()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_selected_note_ask_save_and_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """One real source, real Ask/thread/Note writes and two return routes."""
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    started, release = threading.Event(), threading.Event()

    class Model(_StubHandler):
        MODEL = "source-return-fixture"
        requests: list[dict[str, Any]] = []

        def do_POST(self) -> None:  # noqa: N802 - local HTTP model contract
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.requests.append(request)
            started.set()
            release.wait(20)
            payload = json.dumps({
                "id": "source-answer", "object": "chat.completion", "model": self.MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": ANSWER}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 13, "total_tokens": 25},
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    _ensure_build()
    model = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=model.serve_forever, daemon=True).start()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    PrimitiveService(get_database()).create_note(
        Principal(PrincipalKind.OWNER, "karol"), note_id=NOTE_ID,
        title=NOTE_TITLE, body_markdown=SOURCE_BODY, tags=[],
    )
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(
                viewport={"width": width, "height": HEIGHT[width]},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            # No owner clipboard state is read or changed.
            context.add_init_script("""(() => {
              let copied = '';
              Object.defineProperty(navigator, 'clipboard', {configurable:true, value:{
                writeText: async text => {copied = String(text)},
                readText: async () => copied,
              }});
            })();""")
            page = context.new_page()
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _start(page, base)
            provider = _api(page, "POST", "/api/inference/model-library/define-endpoint", {
                "draft": {"request_id": "source-return-model", "profile_id": "source-return-model",
                          "expected_profile_revision": 0, "label": "Source return local model",
                          "provider_family": "openai_compatible", "model": Model.MODEL,
                          "endpoint": f"http://127.0.0.1:{model.server_port}/v1", "requires_key": False},
                "secret": None,
            }, token=TOKEN)["provider"]
            _api(page, "POST", "/api/inference/assignments/set", {
                "command_id": "source-return-assignment", "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "ask.answer"},
                "entries": [{"profile_id": provider["profile_id"], "profile_revision": provider["profile_revision"]}],
            }, token=TOKEN)
            note = page.locator(THOUGHT).first
            editor = note.locator(".thought-note-body .cm-content")
            editor.wait_for()
            # CodeMirror's long content element extends well below its
            # viewport; click the visible scroller, then use real keys.
            note.locator(".thought-note-body .cm-scroller").click(position={"x": 28, "y": 28})
            page.keyboard.press("ControlOrMeta+End")
            page.keyboard.press("Home")
            page.keyboard.press("Shift+End")
            captured = _selection_and_scroll(note)
            assert captured["text"] == QUOTE, captured
            assert captured["scroll"] > 0, captured
            assert _visible_tail(note) == QUOTE
            note.get_by_role("button", name="Ask about this", exact=True).click()
            ask = page.locator("[id='ask'][data-layer='window']")
            source = ask.get_by_test_id("ask-selected-passage")
            source.wait_for()
            expect(source).to_contain_text(QUOTE)
            expect(ask.get_by_test_id("ask-context")).to_contain_text(NOTE_TITLE)
            assert "My whole desk" not in ask.get_by_test_id("ask-context").inner_text()
            _visible_before_scroll(ask, "Back to Thought")
            if width == 393:
                _target_check(page, "[id='ask']")
            page.screenshot(path=str(shots / f"note-source-ask-{width}.png"))

            # The source control remains outside the folded quote and an
            # answer's long-running state. Back returns the exact CM range.
            source.locator("summary").click()
            expect(source.get_by_role("button", name="Back to Thought")).to_be_visible()
            _visible_before_scroll(ask, "Back to Thought")
            source.get_by_role("button", name="Back to Thought").click()
            expect(note).to_be_visible()
            page.wait_for_function("""() => window.getSelection()?.toString() === 'Confirm the handoff before Friday.'""")
            returned = _selection_and_scroll(note)
            assert returned["scroll"] == captured["scroll"], (captured, returned)
            assert _visible_tail(note) == QUOTE
            page.screenshot(path=str(shots / f"note-source-return-{width}.png"))

            # Answer transport is fake; the real API keeps the Thread and
            # Save-as-note writer uses the answer's looked-at qualified refs.
            _raise_ask(page)
            ask.get_by_role("textbox", name="Ask about your work", exact=True).fill("What should I review?")
            with page.expect_response(lambda response: response.url.endswith("/api/ask") and response.request.method == "POST") as finished:
                ask.get_by_role("button", name="Ask", exact=True).click()
                expect(ask.get_by_role("button", name="Stop", exact=True)).to_be_visible()
                assert started.wait(5), "The isolated model did not receive the Ask"
                _visible_before_scroll(ask, "Back to Thought")
                expect(page.locator(".ambient-theater strong")).to_have_text("Ask")
                if width == 393:
                    _target_check(page, "[id='ask']")
                page.screenshot(path=str(shots / f"note-source-pending-{width}.png"))
                release.set()
            response = finished.value
            result = response.json()
            assert response.ok and result["output"] == ANSWER, result
            assert result.get("thread_id") and len(Model.requests) == 1, result
            assert f"note:{NOTE_ID}" in json.dumps(result), result
            expect(ask.get_by_test_id("ask-turn")).to_contain_text(ANSWER)
            kept = _api(page, "GET", f"/api/threads/{result['thread_id']}", token=TOKEN)
            assert NOTE_ID in json.dumps(kept) and ANSWER in json.dumps(kept), kept
            before = {row["id"] for row in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
            ask.get_by_role("button", name="Save as note").click()
            expect(ask.get_by_role("button", name="Open note")).to_be_visible()
            saved = [row for row in _api(page, "GET", "/api/notes", token=TOKEN)["notes"] if row["id"] not in before]
            assert len(saved) == 1, saved
            saved_body = saved[0]["body_markdown"]
            assert ANSWER in saved_body and f"thread:{result['thread_id']}" in saved_body, saved_body
            assert f"note:{NOTE_ID}" in saved_body, saved_body
            page.screenshot(path=str(shots / f"note-source-saved-{width}.png"))

            # A closed source uses the canonical opener. The return is still
            # scoped to this Note and restores the original selected range.
            ask.locator(".desk-gadget-depth").first.click()
            note.locator(".desk-gadget-close").first.click()
            note.wait_for(state="detached")
            _visible_before_scroll(ask, "Back to Thought")
            ask.get_by_role("button", name="Back to Thought").click()
            note = page.locator(THOUGHT).first
            note.locator(".thought-note-body .cm-content").wait_for()
            page.wait_for_function("""() => window.getSelection()?.toString() === 'Confirm the handoff before Friday.'""")
            assert _visible_tail(note) == QUOTE
            page.screenshot(path=str(shots / f"note-source-closed-return-{width}.png"))

            # The quote's old offset must not be applied to a changed body.
            changed = " Newer source words."
            body = note.locator(".thought-note-body .cm-content")
            note.locator(".thought-note-body .cm-scroller").click(position={"x": 28, "y": 28})
            page.keyboard.press("ControlOrMeta+End")
            page.keyboard.type(changed)
            assert _visible_tail(note) == QUOTE + changed
            _raise_ask(page)
            _visible_before_scroll(ask, "Back to Thought")
            ask.get_by_role("button", name="Back to Thought").click()
            expect(note).to_contain_text("SOURCE CHANGED")
            assert _selection_and_scroll(note)["text"] != QUOTE
            assert _visible_tail(note) == QUOTE + changed
            _current_caret_visible(note)
            page.screenshot(path=str(shots / f"note-source-changed-{width}.png"))

            # Named response fixture for refs the current desk cannot open.
            # The Save-as-note write remains real; this second answer is not
            # a claim that the server pinned those display-only sources.
            _raise_ask(page)
            ask.get_by_role("button", name="New ask").click()
            display_answer = "These two references can be named, but not opened here."
            display_wire = {
                **result, "output": display_answer, "thread_id": "",
                "message_ids": {"answer": "display-only-answer"},
                "looked_at": [
                    {"ref": f"note:{NOTE_ID}", "title": NOTE_TITLE},
                    {"ref": "kb:fixture", "title": "Knowledge result"},
                    {"ref": "directory:fixture", "title": "Directory result"},
                ],
            }
            page.route("**/api/ask", lambda route: route.fulfill(
                status=200, content_type="application/json", body=json.dumps(display_wire)), times=1)
            ask.get_by_role("textbox", name="Ask about your work", exact=True).fill("Which references can I inspect?")
            ask.get_by_role("button", name="Ask", exact=True).click()
            expect(ask.get_by_test_id("ask-turn")).to_contain_text(display_answer)
            before_display = {row["id"] for row in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
            ask.get_by_role("button", name="Save as note").click()
            expect(ask.get_by_role("button", name="Open note")).to_be_visible()
            display_notes = [row for row in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
                             if row["id"] not in before_display]
            assert len(display_notes) == 1, display_notes
            display_body = display_notes[0]["body_markdown"]
            assert f"](note:{NOTE_ID})" in display_body, display_body
            assert "Knowledge result (kb:fixture)" in display_body, display_body
            assert "Directory result (directory:fixture)" in display_body, display_body
            assert "](kb:" not in display_body and "](directory:" not in display_body, display_body
            assert len(Model.requests) == 1
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
        model.shutdown()
        model.server_close()


@pytest.mark.timeout(180)
@pytest.mark.parametrize("width", [1440, 393])
def test_reference_source_frame_keeps_back_during_busy_and_quote_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Components renders the same source frame with local actions only."""
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": HEIGHT[width]},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            page.set_default_timeout(20_000)
            writes: list[str] = []
            page.on("request", lambda request: writes.append(request.url)
                    if request.method != "GET" and any(path in request.url for path in ("/api/ask", "/api/notes", "/api/threads")) else None)
            page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            selector = page.get_by_role("group", name="Patterns").get_by_role("button", name="Conversation", exact=True)
            if selector.count():
                selector.click()
            else:
                page.get_by_role("group", name="Patterns").get_by_role("button").click()
                page.locator("[role^='menuitem']").filter(has_text="Conversation").first.click()
            specimen = page.get_by_test_id("reference-conversation")
            specimen.wait_for()
            assert specimen.locator(".desk-mic").count() == 0
            source = specimen.get_by_test_id("ask-selected-passage")
            expect(source).to_contain_text("The source stays beside the decision.")
            page.get_by_role("combobox", name="Example state").select_option("busy")
            source.locator("summary").click()
            expect(source.get_by_role("button", name="Back to Thought")).to_be_visible()
            _visible_before_scroll(specimen, "Back to Thought")
            source.get_by_role("button", name="Back to Thought").click()
            expect(specimen.get_by_text("LOCAL RETURN", exact=True)).to_be_visible()
            if width == 393:
                _target_check(page, "[data-testid='reference-conversation']")
            page.screenshot(path=str(shots / f"reference-conversation-source-{width}.png"))
            assert not writes, writes
            browser.close()
    finally:
        server.stop()
