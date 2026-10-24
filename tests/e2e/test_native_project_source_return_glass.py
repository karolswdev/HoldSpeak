"""P06 Project Files → Note → Ask → saved Note/Thread → exact Project return.

The projects, filed Note, Thought, Ask, Thread, and saved Note use the real
isolated hub. Only the language model's answer is local synthetic material.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .engine_stub_rig import _StubHandler
from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from .test_desk_sweep import TARGET_JS

pytest.importorskip("playwright.sync_api", reason="P06 source return needs Playwright")

TOKEN = "native-project-source-glass"
SHOTS = "native-project-source-wave7"
HEIGHT = {1440: 900, 393: 852}
PROJECT_A = "p-source-a"
PROJECT_B = "p-source-b"
PROJECT_A_NAME = "Atlas review"
PROJECT_B_NAME = "Beacon review"
NOTE_ID = "n-project-source"
NOTE_REF = f"note:{NOTE_ID}"
NOTE_TITLE = "Architecture review source"
QUOTE = "Mira owns the Friday review."
BODY = "\n".join(f"Architecture line {n:02d}: keep the source in the Note." for n in range(45)) + "\n" + QUOTE
ANSWER = "Mira owns the Friday review. Keep the next check in the source Note."
THOUGHT = ".desk-window.thought-workspace-window"


def _boot_isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    # The delivery registry freezes its default before _boot changes HOME.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(
        registry_module, "DEFAULT_REGISTRY_PATH",
        tmp_path / "home" / ".holdspeak" / "delivery_sources.json",
    )
    return _boot(tmp_path, monkeypatch, token=TOKEN)


def _seed() -> None:
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.project_service import ProjectService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    for project_id, name in ((PROJECT_A, PROJECT_A_NAME), (PROJECT_B, PROJECT_B_NAME)):
        db.projects.create_project(project_id=project_id, name=name, description="Review the filed source.", keywords=[])
    PrimitiveService(db).create_note(owner, note_id=NOTE_ID, title=NOTE_TITLE, body_markdown=BODY, tags=[])
    projects = ProjectService(db)
    projects.add_resource(owner, PROJECT_A, NOTE_REF)
    projects.add_resource(owner, PROJECT_B, NOTE_REF)


def _start(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)


def _components_ready(page: Any) -> None:
    """Enter Components from its actual route, crossing First Sentence if shown."""
    page.wait_for_function("""() => {
      const visible = e => !!e && e.getClientRects().length > 0 &&
        getComputedStyle(e).visibility !== 'hidden';
      return visible(document.querySelector('.chair.chair-first-value')) ||
        visible(document.querySelector('#surface-components .reference-pattern-selector'));
    }""")
    gate = page.locator(".chair.chair-first-value")
    if gate.is_visible():
        gate.get_by_role("button", name=re.compile(r"^(Continue later|Open my desk)$")).click()
    page.locator("#surface-components").wait_for(state="visible")
    page.get_by_role("group", name="Patterns").wait_for(state="visible")


def _open_project(page: Any, project_id: str, name: str) -> Any:
    page.locator("[aria-controls=desk-tool-shelf]").first.click()
    field = page.locator("[aria-controls=desk-palette-listbox]")
    field.wait_for()
    field.fill(name)
    page.locator(f"[id='desk-palette-option-project.open.{project_id}']").click()
    room = page.locator("#surface-project-memory")
    room.get_by_test_id("room-head").wait_for()
    assert room.locator(".room-head-name-measure").text_content() == name
    return room


def _files(room: Any) -> Any:
    fold = room.get_by_test_id("room-fold-files")
    fold.wait_for()
    if fold.locator("details").get_attribute("open") is None:
        fold.locator("summary").click()
    files = room.get_by_test_id("room-files")
    files.wait_for()
    return files


def _hit_before_action(root: Any, selector: str) -> None:
    """Read visibility and hit ownership before Playwright can scroll."""
    state = root.evaluate("""(root, selector) => {
      const button = root.querySelector(selector);
      if (!button) return {missing: selector};
      const b = button.getBoundingClientRect(), w = root.getBoundingClientRect();
      const x = b.left + b.width / 2, y = b.top + b.height / 2;
      const hit = document.elementFromPoint(x, y);
      return {button: b.toJSON(), window: w.toJSON(),
        inWindow: b.left >= w.left && b.right <= w.right && b.top >= w.top && b.bottom <= w.bottom,
        inViewport: b.left >= 0 && b.right <= innerWidth && b.top >= 0 && b.bottom <= innerHeight,
        hit: hit === button || button.contains(hit)};
    }""", selector)
    assert state.get("inWindow") and state.get("inViewport") and state.get("hit"), state


def _open_filed_note(page: Any, room: Any) -> Any:
    files = _files(room)
    row = files.locator(f"[data-object-id='{NOTE_REF}']")
    row.wait_for()
    row.locator(".object-list-open").click()
    from playwright.sync_api import expect

    expect(files.get_by_test_id("room-files-open")).to_be_enabled()
    _hit_before_action(room, "[data-testid='room-files-open']")
    files.get_by_test_id("room-files-open").click()
    note = page.locator(f"[id='pullout:{NOTE_REF}']")
    note.locator(".thought-note-body .cm-content").wait_for()
    return note


def _front(page: Any, target: Any) -> None:
    for _ in range(6):
        if "is-front" in (target.get_attribute("class") or ""):
            return
        page.locator(".desk-window.is-front .desk-gadget-depth").first.click()
    assert "is-front" in (target.get_attribute("class") or ""), "the target window stayed behind"


def _return_project(page: Any, window: Any, name: str, width: int) -> Any:
    if width == 393:
        button = window.locator(".desk-gadget-close")
        assert button.get_attribute("aria-label").startswith("Back from ")
    else:
        button = window.get_by_role("button", name=f"Return to {name}", exact=True)
    selector = ".desk-gadget-close" if width == 393 else "button"
    if width == 393:
        _hit_before_action(window, selector)
    else:
        state = button.evaluate("""b => {const r=b.getBoundingClientRect(), h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
          return {inViewport:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight, hit:h===b||b.contains(h)};}""")
        assert state["inViewport"] and state["hit"], state
    button.click()
    room = page.locator("#surface-project-memory")
    room.get_by_test_id("room-head").wait_for()
    from playwright.sync_api import expect

    expect(room.locator(".room-head-name-measure")).to_have_text(name)
    return room


def _focused_filed_row(room: Any) -> dict[str, Any]:
    """Read focus and viewport before any Playwright locator action."""
    state = room.evaluate("""(root, ref) => {
      const row = [...root.querySelectorAll('[data-object-id]')].find(x => x.dataset.objectId === ref);
      const button = row?.querySelector('.object-list-open');
      const box = button?.getBoundingClientRect();
      const frame = root.getBoundingClientRect();
      return {row: !!row, selected: row?.getAttribute('aria-selected'), focused: document.activeElement === button,
        box: box?.toJSON(), frame: frame.toJSON(),
        inFrame: !!box && box.left >= frame.left && box.right <= frame.right && box.top >= frame.top && box.bottom <= frame.bottom,
        inViewport: !!box && box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight};
    }""", NOTE_REF)
    assert state["row"] and state["selected"] == "true" and state["focused"], state
    assert state["inFrame"] and state["inViewport"], state
    return state


def _phone_targets(page: Any, selector: str) -> None:
    faults = page.evaluate(TARGET_JS, selector)
    assert not faults, faults


def _configure_model(page: Any, port: int) -> None:
    provider = _api(page, "POST", "/api/inference/model-library/define-endpoint", {
        "draft": {"request_id": "project-source-model", "profile_id": "project-source-model",
                  "expected_profile_revision": 0, "label": "Project source local model",
                  "provider_family": "openai_compatible", "model": "project-source-fixture",
                  "endpoint": f"http://127.0.0.1:{port}/v1", "requires_key": False},
        "secret": None,
    }, token=TOKEN)["provider"]
    _api(page, "POST", "/api/inference/assignments/set", {
        "command_id": "project-source-assignment", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": provider["profile_id"], "profile_revision": provider["profile_revision"]}],
    }, token=TOKEN)


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_project_filed_note_ask_save_lineage_and_exact_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Project A's selected Note stays A after B opens that Note, then returns."""
    from playwright.sync_api import expect, sync_playwright

    class Model(_StubHandler):
        MODEL = "project-source-fixture"
        requests: list[dict[str, Any]] = []

        def do_POST(self) -> None:  # noqa: N802 - isolated model endpoint
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.requests.append(request)
            payload = json.dumps({
                "id": "project-source-answer", "object": "chat.completion", "model": self.MODEL,
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": ANSWER}}],
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
    server, base = _boot_isolated(tmp_path, monkeypatch)
    _seed()
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": HEIGHT[width]},
                                    has_touch=width == 393, is_mobile=width == 393,
                                    reduced_motion="reduce")
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _start(page, base)
            _configure_model(page, model.server_port)

            room = _open_project(page, PROJECT_A, PROJECT_A_NAME)
            files = _files(room)
            expect(files.locator(f"[data-object-id='{NOTE_REF}']")).to_be_visible()
            if width == 393:
                _phone_targets(page, "#surface-project-memory [data-testid='room-fold-files']")
            page.screenshot(path=str(shots / f"project-files-open-{width}.png"))
            note = _open_filed_note(page, room)
            assert NOTE_TITLE in note.inner_text()
            source_thought = _api(page, "GET", f"/api/thoughts/for-note/{NOTE_ID}", token=TOKEN)["thought"]
            note.locator(".thought-note-body .cm-scroller").click(position={"x": 28, "y": 28})
            page.keyboard.press("ControlOrMeta+End")
            page.keyboard.press("Home")
            page.keyboard.press("Shift+End")
            assert page.evaluate("window.getSelection()?.toString()") == QUOTE
            captured_scroll = note.locator(".thought-note-body .cm-scroller").evaluate("element => element.scrollTop")
            assert captured_scroll > 0
            note.get_by_role("button", name="Ask about this", exact=True).click()
            ask = page.locator("[id='ask'][data-layer='window']")
            expect(ask.get_by_test_id("ask-selected-passage")).to_contain_text(QUOTE)
            expect(ask.get_by_test_id("ask-context")).to_contain_text(NOTE_TITLE)
            page.screenshot(path=str(shots / f"project-ask-source-{width}.png"))

            room = _open_project(page, PROJECT_B, PROJECT_B_NAME)
            b_note = _open_filed_note(page, room)
            assert b_note.get_attribute("id") == note.get_attribute("id")
            # The Note existed before B's Open; editor.wait_for alone would
            # return before this second opener finishes its Desk refresh and
            # raises the window. Wait for the public presentation of B Open.
            expect(b_note).to_have_class(re.compile(r"\bis-front\b"))
            if width == 1440:
                expect(b_note.get_by_role("button", name=f"Return to {PROJECT_B_NAME}")).to_be_visible()
            else:
                _phone_targets(page, f"[id='pullout:{NOTE_REF}'] .desk-pullout-head")
            _front(page, ask)
            ask.get_by_role("textbox", name="Ask about your work", exact=True).fill("Who owns the Friday review?")
            with page.expect_response(lambda response: response.url.endswith("/api/ask") and response.request.method == "POST") as asked:
                ask.get_by_role("button", name="Ask", exact=True).click()
            response = asked.value
            sent = response.request.post_data_json
            result = response.json()
            assert response.ok and result["output"] == ANSWER and result["thread_id"], result
            assert sent["source_snapshot"] == {
                "ref": NOTE_REF, "thought_id": source_thought["id"],
                "working_revision": source_thought["working_revision"],
                "body_sha256": hashlib.sha256(BODY.encode()).hexdigest(),
            }, sent
            assert sent["context"] == [{"id": NOTE_ID, "kind": "note", "title": NOTE_TITLE, "ref": NOTE_REF}], sent
            assert PROJECT_A not in json.dumps(sent) and PROJECT_B not in json.dumps(sent), sent
            assert len(Model.requests) == 1
            expect(ask.get_by_test_id("ask-turn")).to_contain_text(ANSWER)
            if width == 393:
                page.screenshot(path=str(shots / "project-answer-before-save-393.png"))
                fronts = page.evaluate("""() => [...document.querySelectorAll('[data-layer=window].is-front')]
                  .map(node => ({id: node.id, label: node.getAttribute('aria-label')}))""")
                assert fronts == [{"id": "ask", "label": "Ask"}], fronts
            kept = _api(page, "GET", f"/api/threads/{result['thread_id']}", token=TOKEN)
            assert ANSWER in json.dumps(kept) and NOTE_ID in json.dumps(kept), kept

            before = {row["id"] for row in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
            ask.get_by_role("button", name="Save as note").click()
            expect(ask.get_by_role("button", name="Open note")).to_be_visible()
            saved = [row for row in _api(page, "GET", "/api/notes", token=TOKEN)["notes"] if row["id"] not in before]
            assert len(saved) == 1 and ANSWER in saved[0]["body_markdown"], saved
            assert NOTE_REF in saved[0]["body_markdown"] and f"thread:{result['thread_id']}" in saved[0]["body_markdown"]
            filed = [r["resource_ref"] for r in _api(page, "GET", f"/api/projects/{PROJECT_A}/resources", token=TOKEN)["resources"]]
            assert f"note:{saved[0]['id']}" not in filed, filed  # Open is job navigation, not filing.
            page.screenshot(path=str(shots / f"project-answer-saved-{width}.png"))

            # The old Note was opened from B; A's captured Ask rebinds it.
            ask.get_by_role("button", name="Back to Thought").click()
            expect(note).to_be_visible()
            page.wait_for_function("() => window.getSelection()?.toString() === 'Mira owns the Friday review.'")
            assert note.locator(".thought-note-body .cm-scroller").evaluate("e => e.scrollTop") == captured_scroll
            if width == 1440:
                expect(note.get_by_role("button", name=f"Return to {PROJECT_A_NAME}")).to_be_visible()
            if width == 1440:
                _front(page, note)
                note.locator(".desk-gadget-close").click()
                note.wait_for(state="detached")
                _front(page, ask)
                ask.get_by_role("button", name="Back to Thought").click()
                note = page.locator(f"[id='pullout:{NOTE_REF}']")
                note.locator(".thought-note-body .cm-content").wait_for()
                page.wait_for_function("() => window.getSelection()?.toString() === 'Mira owns the Friday review.'")

            _front(page, ask)
            ask.get_by_role("button", name="Open note").click()
            saved_note = page.locator(f"[id='pullout:note:{saved[0]['id']}']")
            saved_note.locator(".thought-note-body .cm-content").wait_for()
            fold = saved_note.locator(".reading-object-links")
            fold.locator("summary").click()
            expect(fold.get_by_role("button", name=NOTE_TITLE)).to_be_visible()
            expect(fold.get_by_role("button", name="Ask thread")).to_be_visible()
            if width == 393:
                _phone_targets(page, f"[id='pullout:note:{saved[0]['id']}'] .reading-object-links")
            page.screenshot(path=str(shots / f"project-saved-links-{width}.png"))
            fold.get_by_role("button", name=NOTE_TITLE).click()
            expect(note).to_have_class(re.compile(r"\bis-front\b"))
            _front(page, saved_note)
            fold.get_by_role("button", name="Ask thread").click()
            expect(ask.get_by_test_id("ask-turn")).to_contain_text(ANSWER)
            expect(ask).to_have_class(re.compile(r"\bis-front\b"))

            # The loaded Thread has its own Project navigation, even though
            # loading a thread clears its old selected passage.
            if width == 393:
                _phone_targets(page, "#ask .desk-pullout-head")
            room = _return_project(page, ask, PROJECT_A_NAME, width)
            expect(room.get_by_test_id("room-files-return")).to_have_text("FILED HERE")
            _focused_filed_row(room)
            if width == 393:
                _phone_targets(page, "#surface-project-memory [data-testid='room-fold-files']")
            page.screenshot(path=str(shots / f"project-return-focused-{width}.png"))
            assert _api(page, "GET", f"/api/projects/{PROJECT_A}/resources", token=TOKEN)["resources"]
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
        model.shutdown()
        model.server_close()


@pytest.mark.timeout(180)
def test_project_return_reads_current_membership_and_note_before_focusing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Moved, missing and failed material never become a stale FILED HERE."""
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    _ensure_build()
    server, base = _boot_isolated(tmp_path, monkeypatch)
    _seed()
    projects = ProjectService(get_database())
    owner = Principal(PrincipalKind.OWNER, "karol")
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _start(page, base)
            room = _open_project(page, PROJECT_A, PROJECT_A_NAME)
            note = _open_filed_note(page, room)

            projects.remove_resource(owner, PROJECT_A, NOTE_REF)
            room = _return_project(page, note, PROJECT_A_NAME, 1440)
            expect(room.get_by_test_id("room-files-return")).to_have_text("NOT FILED HERE")
            assert room.get_by_test_id("room-files-open").is_disabled()
            page.screenshot(path=str(shots / "project-return-not-filed-1440.png"))
            projects.add_resource(owner, PROJECT_A, NOTE_REF)

            # This Note was previously read and shown. A fresh 404 now wins
            # over its cached title and the retained filed membership.
            def missing_note(route: Any) -> None:
                route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')

            page.route(f"**/api/notes/{NOTE_ID}**", missing_note)
            _front(page, note)
            room = _return_project(page, note, PROJECT_A_NAME, 1440)
            expect(room.get_by_test_id("room-files-return")).to_have_text("NOTE NOT AVAILABLE")
            assert room.get_by_test_id("room-files-open").is_disabled()
            assert not room.locator(f"[data-object-id='{NOTE_REF}'][aria-selected='true']").count()
            page.screenshot(path=str(shots / "project-return-note-unavailable-1440.png"))
            page.unroute(f"**/api/notes/{NOTE_ID}**", missing_note)

            def failed_resources(route: Any) -> None:
                route.fulfill(status=503, content_type="application/json", body='{"error":"unavailable"}')

            page.route(f"**/api/projects/{PROJECT_A}/resources**", failed_resources)
            _front(page, note)
            room = _return_project(page, note, PROJECT_A_NAME, 1440)
            expect(room.get_by_test_id("room-files-return")).to_have_text("RESOURCES NOT READ")
            assert room.get_by_test_id("room-files-open").is_disabled()
            expect(room.get_by_test_id("room-files-retry")).to_be_visible()
            page.screenshot(path=str(shots / "project-return-resources-not-read-1440.png"))
            page.unroute(f"**/api/projects/{PROJECT_A}/resources**", failed_resources)
            room.get_by_test_id("room-files-retry").click()
            expect(room.get_by_test_id("room-files-return")).to_have_text("FILED HERE")
            _focused_filed_row(room)
            page.screenshot(path=str(shots / "project-return-retry-focused-1440.png"))

            # The first return's fetch completes last. Only the later current
            # read may decide membership, read the Note, and focus its row.
            page.evaluate("""ref => {
              const prior = window.fetch.bind(window);
              const hold = {taken:false, release:null, done:null};
              window.__projectResourceHold = hold;
              window.fetch = (...args) => {
                const url = String(typeof args[0] === 'string' ? args[0] : args[0].url);
                if (url.includes(`/api/projects/${ref}/resources`) && !hold.taken) {
                  hold.taken = true;
                  const response = prior(...args);
                  let finish;
                  hold.done = new Promise(resolve => {finish = resolve;});
                  return new Promise((resolve, reject) => {
                    hold.release = () => response.then(
                      value => {resolve(value); finish();},
                      error => {reject(error); finish();});
                  });
                }
                return prior(...args);
              };
            }""", PROJECT_A)
            _front(page, note)
            _return_project(page, note, PROJECT_A_NAME, 1440)
            expect(room.get_by_test_id("room-files-return")).to_have_text("CHECKING FILES")
            assert page.evaluate("window.__projectResourceHold.taken")
            _front(page, note)
            _return_project(page, note, PROJECT_A_NAME, 1440)
            expect(room.get_by_test_id("room-files-return")).to_have_text("FILED HERE")
            _focused_filed_row(room)
            page.evaluate("async () => { const hold = window.__projectResourceHold; hold.release(); await hold.done; }")
            expect(room.get_by_test_id("room-files-return")).to_have_text("FILED HERE")
            _focused_filed_row(room)
            assert not errors, errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
@pytest.mark.parametrize("width", [1440, 393])
def test_reference_filed_notes_uses_local_read_and_open_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Components paints the production Files species with a local adapter."""
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _boot_isolated(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": HEIGHT[width]},
                                    has_touch=width == 393, is_mobile=width == 393,
                                    reduced_motion="reduce")
            page.set_default_timeout(20_000)
            page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
            _components_ready(page)
            pattern = page.get_by_role("group", name="Patterns").get_by_role("button", name="Lists", exact=True)
            if pattern.count():
                pattern.click()
            else:
                page.get_by_role("group", name="Patterns").get_by_role("button").click()
                page.locator("[role^='menuitem']").filter(has_text="Lists").first.click()
            page.get_by_role("combobox", name="Example state").select_option("filed-notes")
            specimen = page.get_by_test_id("reference-filed-notes")
            specimen.wait_for()
            requests: list[str] = []

            def observe(request: Any) -> None:
                # Components' host may finish unrelated Desk collection
                # reads. The local fixture must never read its synthetic
                # Project/Note or call a writer, model, or Thought adopter.
                fixture_read = any(part in request.url for part in (
                    "/api/projects/local-project", "/api/notes/review-record",
                    "/api/thoughts/for-note/review-record",
                ))
                mutation = request.method != "GET" and (
                    "/api/" in request.url or "/v1/chat/completions" in request.url)
                if fixture_read or mutation:
                    requests.append(f"{request.method} {request.url}")

            page.on("request", observe)
            files = _files(specimen)
            row = files.locator("[data-object-id='note:review-record']")
            row.wait_for()
            expect(row).to_contain_text("Review record")
            row.locator(".object-list-open").click()
            _hit_before_action(specimen, "[data-testid='room-files-open']")
            files.get_by_test_id("room-files-open").click()
            expect(specimen.locator(".reference-receipt[role='status']")).to_contain_text(
                "OPENED LOCALLY · note:review-record · local-project")
            if width == 393:
                _phone_targets(page, "[data-testid='reference-filed-notes']")
            page.screenshot(path=str(shots / f"reference-filed-notes-{width}.png"))
            assert not requests, requests
            browser.close()
    finally:
        server.stop()
