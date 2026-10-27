"""P03 browser proof: active Note persistence and Thought's editing binder.

The Components capture source is local text, not microphone or ASR evidence.
It renders the production ThoughtDocumentPane and DeskEditor with isolated IO.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from tests.e2e.chair_windows import go_group
from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from .test_desk_sweep import TARGET_JS

pytest.importorskip("playwright.sync_api", reason="P03 glass needs Playwright")

TOKEN = "native-thought-voice-glass"
HEIGHT = {1440: 900, 393: 852}
THOUGHT = ".desk-window.thought-workspace-window"
SHOTS = "native-input-wave3"
VOICE_WORDS = "Confirm the boundary before rollout."
BASE_BODY = "Review the source before rollout."


def _isolated_boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    # The registry default is frozen at import time, before _boot sets HOME.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(
        registry_module, "DEFAULT_REGISTRY_PATH",
        tmp_path / "home" / ".holdspeak" / "delivery_sources.json",
    )
    return _boot(tmp_path, monkeypatch, token=TOKEN)


def _start(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)


def _new_note(page: Any, width: int) -> None:
    menu = "desk" if width == 1440 else "go"
    page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
    if width == 393:
        go_group(page, "New", lambda option: option.click())
    label = "New Note" if width == 1440 else "Note"
    page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first.click()


def _body(window: Any) -> Any:
    return window.locator(".thought-note-body .cm-content").first


def _editor_text(scope: Any) -> str:
    return "\n".join(scope.locator(".cm-line").all_text_contents()).strip()


def _pattern(page: Any, label: str) -> None:
    page.get_by_test_id("design-reference").wait_for(timeout=15_000)
    direct = page.get_by_role("navigation", name="Patterns").get_by_role("button", name=label, exact=True)
    if direct.count():
        direct.click()
        return
    folded = page.get_by_role("navigation", name="Patterns").get_by_role("button")
    assert folded.count() == 1, folded.all_text_contents()
    folded.click()
    page.locator("[role^='menuitem']").filter(has_text=label).first.click()


def _target_check(page: Any, selector: str) -> None:
    faults = page.evaluate(TARGET_JS, selector)
    assert not faults, faults


def _recovery_actions_visible(window: Any) -> None:
    """Check painted actions before Playwright can scroll them into view."""
    actions = window.evaluate("""frame => {
      const well = frame.querySelector('[data-testid=thought-voice-recovery]');
      if (!well) return [];
      const frameRect = frame.getBoundingClientRect();
      const wellRect = well.getBoundingClientRect();
      return [...well.querySelectorAll('button')].map(button => {
        const rect = button.getBoundingClientRect();
        const hit = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
        return {label: button.textContent.trim(), rect: rect.toJSON(),
          inWell: rect.top >= wellRect.top && rect.bottom <= wellRect.bottom,
          inFrame: rect.top >= frameRect.top && rect.bottom <= frameRect.bottom,
          inViewport: rect.top >= 0 && rect.bottom <= innerHeight,
          hit: hit === button || button.contains(hit)};
      });
    }""")
    assert {entry["label"] for entry in actions} == {"Insert at caret", "Copy"}, actions
    assert all(entry["inWell"] and entry["inFrame"] and entry["inViewport"] and entry["hit"] for entry in actions), actions


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_components_captured_selection_and_stale_recovery_are_one_undo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Real CodeMirror keys test the same binder with fixture-only delivery."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(
                viewport={"width": width, "height": HEIGHT[width]},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            # Keep Copy wholly inside this browser context. The real OS
            # clipboard belongs to the owner even when HOME is isolated.
            context.add_init_script("""(() => {
              let copied = '';
              Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
                __isolated: true,
                writeText: async text => { copied = String(text); },
                readText: async () => copied,
              }});
            })();""")
            page = context.new_page()
            page.set_default_timeout(15_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _start(page, base)
            page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            _pattern(page, "Editing")
            specimen = page.get_by_test_id("reference-editing")
            content = specimen.locator(".cm-content")
            content.wait_for()
            assert _editor_text(specimen) == BASE_BODY
            assert specimen.get_by_role("button", name="Speak the note").count() == 0
            writes: list[str] = []
            page.on("request", lambda request: writes.append(request.url)
                    if request.method != "GET" and ("/api/notes" in request.url or "/api/thoughts" in request.url) else None)

            # Select the word with real editor keys, then move focus before
            # delivery: the captured range still wins one CodeMirror change.
            content.click()
            page.keyboard.press("Home")
            for _ in range(11):
                page.keyboard.press("ArrowRight")
            for _ in range(6):
                page.keyboard.press("Shift+ArrowRight")
            assert page.evaluate("window.getSelection()?.toString()") == "source"
            specimen.get_by_role("button", name="Capture target").click()
            specimen.get_by_role("button", name="Deliver local text").click()
            assert _editor_text(specimen) == BASE_BODY.replace("source", VOICE_WORDS)
            assert specimen.get_by_text("NOT INSERTED").count() == 0
            content.click()
            page.keyboard.press("Meta+z")
            assert _editor_text(specimen) == BASE_BODY
            page.screenshot(path=str(shots / f"editing-selection-{width}.png"), full_page=False)

            # A post-capture edit changes the document generation. Delivery
            # stays as recoverable text, then explicit Insert uses today's
            # caret and one Undo restores only that insertion.
            content.click()
            page.keyboard.press("End")
            specimen.get_by_role("button", name="Capture target").click()
            content.click()
            page.keyboard.press("End")
            page.keyboard.type(" Newer draft.")
            assert _editor_text(specimen) == BASE_BODY + " Newer draft."
            specimen.get_by_role("button", name="Deliver local text").click()
            assert _editor_text(specimen) == BASE_BODY + " Newer draft."
            specimen.get_by_text("NOT INSERTED").wait_for()
            assert VOICE_WORDS in specimen.get_by_test_id("thought-voice-recovery").inner_text()
            content.click()
            page.keyboard.press("End")
            specimen.get_by_role("button", name="Capture target").click()
            content.click()
            page.keyboard.press("End")
            page.keyboard.type(" Another edit.")
            specimen.get_by_role("button", name="Deliver local text").click()
            assert _editor_text(specimen) == BASE_BODY + " Newer draft. Another edit."
            assert specimen.get_by_test_id("thought-voice-recovery").inner_text().count(VOICE_WORDS) == 2
            if width == 393:
                capture_box = specimen.get_by_role("button", name="Capture target").bounding_box()
                recovery_box = specimen.get_by_test_id("thought-voice-recovery").bounding_box()
                assert capture_box and recovery_box
                overlap_x = min(capture_box["x"] + capture_box["width"], recovery_box["x"] + recovery_box["width"]) - max(capture_box["x"], recovery_box["x"])
                overlap_y = min(capture_box["y"] + capture_box["height"], recovery_box["y"] + recovery_box["height"]) - max(capture_box["y"], recovery_box["y"])
                assert overlap_x <= 0 or overlap_y <= 0, (capture_box, recovery_box)
                _target_check(page, "[data-testid='reference-editing']")
            page.screenshot(path=str(shots / f"editing-retained-{width}.png"), full_page=False)
            content.click()
            page.keyboard.press("End")
            specimen.get_by_role("button", name="Insert at caret").click()
            assert _editor_text(specimen) == BASE_BODY + " Newer draft. Another edit." + VOICE_WORDS + "\n\n" + VOICE_WORDS
            assert specimen.get_by_text("NOT INSERTED").count() == 0
            content.click()
            page.keyboard.press("Meta+z")
            assert _editor_text(specimen) == BASE_BODY + " Newer draft. Another edit."

            # The read-only specimen retains words and permits Copy, but it
            # exposes neither capture nor insertion into its CodeMirror body.
            page.get_by_role("combobox", name="Example state").select_option("read-only")
            specimen.get_by_text("Read only", exact=True).first.wait_for()
            assert specimen.get_by_role("button", name="Capture target").is_disabled()
            assert specimen.get_by_role("button", name="Insert at caret").is_disabled()
            assert specimen.locator(".cm-content").get_attribute("contenteditable") == "false"
            specimen.get_by_role("button", name="Copy", exact=True).click()
            assert page.evaluate("navigator.clipboard.__isolated === true")
            assert page.evaluate("navigator.clipboard.readText()") == VOICE_WORDS
            assert _editor_text(specimen) == BASE_BODY
            assert not writes, writes
            if width == 393:
                _target_check(page, "[data-testid='reference-editing']")
            page.screenshot(path=str(shots / f"editing-read-only-{width}.png"), full_page=False)
            assert not errors, errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_production_note_words_survive_close_reopen_and_second_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """The real Note writer keeps each document under its own identity."""
    from playwright.sync_api import sync_playwright

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
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _start(page, base)
            before = {item["id"] for item in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
            _new_note(page, width)
            first = page.locator(THOUGHT).first
            _body(first).wait_for()
            notes = [item for item in _api(page, "GET", "/api/notes", token=TOKEN)["notes"] if item["id"] not in before]
            assert len(notes) == 1, notes
            first_id = notes[0]["id"]
            first_words = "First note keeps the source boundary."
            _body(first).click()
            page.keyboard.type(first_words)
            assert _editor_text(first) == first_words
            first.locator(".desk-gadget-close").first.click()
            first.wait_for(state="detached")
            page.wait_for_function(
                """async ([id, words, token]) => {
                  const r = await fetch('/api/notes', {headers:{authorization:`Bearer ${token}`}});
                  return (await r.json()).notes?.some(n => n.id === id && n.body_markdown === words);
                }""",
                arg=[first_id, first_words, TOKEN], timeout=15_000,
            )
            page.goto(f"{base}/?token={TOKEN}&open=note:{first_id}", wait_until="load")
            _normal_chair(page)
            first = page.locator(THOUGHT).first
            _body(first).wait_for()
            assert _editor_text(first) == first_words
            page.screenshot(path=str(shots / f"thought-reopened-{width}.png"), full_page=False)

            # The next Note opens while the first stays mounted; editing it
            # cannot retarget the first editor or its persisted record.
            _new_note(page, width)
            page.locator(THOUGHT).nth(1).wait_for()
            second = page.locator(THOUGHT).nth(1)
            second_words = "Second note owns a different draft."
            _body(second).click()
            page.keyboard.type(second_words)
            assert _editor_text(second) == second_words
            assert _editor_text(first) == first_words
            if width == 393:
                _target_check(page, THOUGHT)
            page.screenshot(path=str(shots / f"thought-two-notes-{width}.png"), full_page=False)
            if width == 1440:
                # The Note writer can acknowledge while another window has
                # focus. An editor rerender must not take that focus back.
                page.locator(".desk-dock-launch[aria-label^='Today']").click()
                today = page.locator(".desk-window[aria-label='Today']")
                today.wait_for()
                today.locator(".desk-gadget-close").first.focus()
                assert page.evaluate("document.activeElement?.closest('.desk-window')?.getAttribute('aria-label')") == "Today"
                page.wait_for_timeout(900)
                assert page.evaluate("document.activeElement?.closest('.desk-window')?.getAttribute('aria-label')") == "Today"
                today.locator(".desk-gadget-close").first.click()
            second.locator(".desk-gadget-close").first.click()
            second.wait_for(state="detached")
            assert _editor_text(first) == first_words
            after = [item for item in _api(page, "GET", "/api/notes", token=TOKEN)["notes"] if item["id"] not in before]
            assert len(after) == 2, after
            assert len({item["id"] for item in after}) == 2
            assert not errors, errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_production_fake_transcripts_stay_with_their_note_after_reopen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Synthetic socket finals exercise real MicButton and default desk memory.

    The browser gets a fake audio device and the socket is routed before
    navigation. No speech provider or hardware transcribes these words.
    """
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(Path(__file__).resolve().parents[2] / "tests/fixtures/core_path_smoke_16k.wav"),
            ])
            page = browser.new_page(
                viewport={"width": width, "height": HEIGHT[width]},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            page.context.grant_permissions(["microphone"])
            page.set_default_timeout(20_000)
            errors: list[str] = []
            frames: list[str] = []
            routed: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def fake_socket(route: Any) -> None:
                routed.append(route.url)

                def receive(message: str | bytes) -> None:
                    if not isinstance(message, str):
                        return
                    frames.append(message)
                    if json.loads(message).get("type") == "end":
                        route.send(json.dumps({"type": "final", "text": VOICE_WORDS}))

                route.on_message(receive)

            page.route_web_socket(lambda url: "/ws/dictation/stream" in url, fake_socket)
            _start(page, base)
            before = {item["id"] for item in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
            _new_note(page, width)
            window = page.locator(THOUGHT).first
            content = _body(window)
            content.wait_for()
            created = [item for item in _api(page, "GET", "/api/notes", token=TOKEN)["notes"] if item["id"] not in before]
            assert len(created) == 1, created
            note_id = created[0]["id"]
            content.click()
            page.keyboard.type("Voice target before edit.")

            for index, local_edit in enumerate((" Newer local text.", " Another local edit."), start=1):
                window.get_by_role("button", name="Speak the note", exact=True).click()
                stop = window.get_by_role("button", name="Stop listening")
                stop.wait_for(timeout=15_000)
                content.click()
                page.keyboard.press("End")
                page.keyboard.type(local_edit)
                stop.click()
                recovery = window.get_by_test_id("thought-voice-recovery")
                recovery.wait_for(timeout=15_000)
                page.wait_for_function(
                    "([expected, text]) => (document.querySelector('[data-testid=thought-voice-recovery]')?.textContent || '').split(text).length - 1 === expected",
                    arg=[index, VOICE_WORDS], timeout=15_000,
                )
                assert _editor_text(window) == "Voice target before edit." + " Newer local text." + (" Another local edit." if index == 2 else "")

            assert len(routed) == 2, routed
            assert sum(json.loads(frame).get("type") == "start" for frame in frames) == 2
            assert sum(json.loads(frame).get("type") == "end" for frame in frames) == 2
            _recovery_actions_visible(window)
            if width == 393:
                _target_check(page, THOUGHT)
            page.screenshot(path=str(shots / f"thought-voice-retained-{width}.png"), full_page=False)
            window.locator(".desk-gadget-close").first.click()
            window.wait_for(state="detached")

            _new_note(page, width)
            other = page.locator(THOUGHT).first
            _body(other).wait_for()
            assert other.get_by_test_id("thought-voice-recovery").count() == 0
            other.locator(".desk-gadget-close").first.click()
            other.wait_for(state="detached")

            page.goto(f"{base}/?token={TOKEN}&open=note:{note_id}", wait_until="load")
            _normal_chair(page)
            reopened = page.locator(THOUGHT).first
            content = _body(reopened)
            content.wait_for()
            recovery = reopened.get_by_test_id("thought-voice-recovery")
            recovery.wait_for(timeout=15_000)
            assert recovery.inner_text().count(VOICE_WORDS) == 2
            prior = "Voice target before edit. Newer local text. Another local edit."
            assert _editor_text(reopened) == prior
            _recovery_actions_visible(reopened)
            if width == 393:
                _target_check(page, THOUGHT)
            page.screenshot(path=str(shots / f"thought-voice-reopened-{width}.png"), full_page=False)

            content.click()
            page.keyboard.press("End")
            recovery.get_by_role("button", name="Insert at caret").click()
            assert _editor_text(reopened) == prior + VOICE_WORDS + "\n\n" + VOICE_WORDS
            assert reopened.get_by_test_id("thought-voice-recovery").count() == 0
            content.click()
            page.keyboard.press("Meta+z")
            assert _editor_text(reopened) == prior
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
