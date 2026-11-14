"""The Ask window, AS RENDERED: what only a real browser proves (the test diet).

Betterment Q6 (docs/internal/betterment/asking/RECIPE.md): a desk object
dropped on the Ask window joins its scope (Ask D1: the scope word names it). The drop is a real HTML drag
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


# Deliberately longer than the owner's Tuesday material, including Markdown
# blocks and an unbroken identifier. This is model-stub text, not live inference.
LONG_TOKEN = "architecture_checkpoint_" + "x" * (180 - len("architecture_checkpoint_"))
LONG_SCOPE = "Review the platform recovery point, retained draft, migration result and next owner action before an architecture team signs the deployment checkpoint"
PATH_SCOPE = "web/src/desk/components/architecture/reviews/" + "checkpoint_" * 10 + "AskWorkspace.tsx"


def _shaped_answer():
    return "\n".join([
        "## Platform checkpoint", "", "Review the rollback plan and keep the approved recovery point until the review is complete.", "",
        "| Check | Owner | Result |", "| --- | --- | --- |",
        "| Migration | Mira | Review the rollback record |", "| Recovery | Karol | Keep the checkpoint |", "",
        "```sh", "git status --short", f"checkpoint={LONG_TOKEN}", "```", "",
        *[f"Checkpoint {n}: record the observed result, the owner and the next review date.  " for n in range(1, 43)],
        "", "### Next step", "", "Keep the checkpoint until the review is complete.",
    ])


def _stored_long_thread(db, template):
    """Exercise the real ledger and its public read, rather than forge messages."""
    from holdspeak.services.thread_service import ThreadService
    thread = db.threads.create_thread(title="What do I owe Mira this week?")
    parent = None
    refs = template["thread"]["refs"]
    for n in range(30):
        for role, text in [("user", "When should I tell her?" if n == 29 else f"What do I owe Mira at checkpoint {n + 1}?"), ("assistant", _shaped_answer())]:
            message = db.threads.append_message(thread.id, role=role, parent_id=parent)
            db.threads.append_part(message.id, kind="text", text=text)
            db.threads.complete_message(message.id)
            parent = message.id
            matching = [ref for ref in refs if ref["origin"] == ("reference" if role == "user" else "relevance")]
            # Each original frozen reference already came from the Ask producer.
            if matching:
                db.threads.freeze_refs(thread.id, message.id, [matching[0]])
    service = ThreadService(db, broadcast=lambda *_: None)
    return {"thread": service.get(thread.id), "recent": {"threads": service.list_threads()}, "first": {"thread_id": thread.id}}


def _seat_failures(win, width):
    """All visible text/rows are whole; offscreen content remains scrollable."""
    return win.evaluate(r"""(win, width) => {
      const failures=[];
      const mast=win.querySelector('.surface-mast-facts');
      if (!mast?.textContent?.trim()) failures.push('The Mast scope is blank');
      const about=win.querySelector('[data-testid=ask-context]');
      if (width===393 && (!about || !about.getBoundingClientRect().width || about.closest('[inert]'))) failures.push('About is absent from the verb row');
      const edge=el=>{const box=el.getBoundingClientRect(), clip=getComputedStyle(el).clipPath.match(/inset\(([^)]+)\)/)?.[1].split(' ').map(parseFloat);return {top:box.top+(clip?.[0]||0),bottom:box.bottom+(clip?.length===1?-clip[0]:-(clip?.[2]??clip?.[0]??0))};};
      const reading=win.querySelector('.surface-object-reading');
      if(reading?.getBoundingClientRect().height) {
        const box=edge(reading), walker=document.createTreeWalker(reading,NodeFilter.SHOW_TEXT);
        let cut=false;
        for(let node=walker.nextNode();node;node=walker.nextNode()) {
          if(!node.textContent.trim() || node.parentElement.closest('[aria-hidden=true]')) continue;
          const range=document.createRange();range.selectNodeContents(node);
          if([...range.getClientRects()].some(r=>r.top<box.bottom-.5 && r.bottom>box.bottom+.5)) cut=true;
        }
        if(cut) failures.push('The reader ends in a partial text line');
      }
      const held=win.querySelector('[data-testid=ask-hold]');
      if (held) {
        const box=held.getBoundingClientRect(), composer=win.querySelector('[data-testid=ask-toolbar]').getBoundingClientRect(), mast=win.querySelector('.surface-mast').getBoundingClientRect();
        if(box.top<mast.bottom-1 || box.bottom>composer.top+1) failures.push('The held question leaves its seat');
        for (const row of held.querySelectorAll('.gadget-row')) {
          const value=row.querySelector('.gadget-row-gadget')?.textContent?.trim()||'';
          if (/^\d{4}-\d{2}-\d{2}$/.test(value)) failures.push('A held fact has an ISO date');
          if (/^hidden \(/.test(value)) failures.push('A held fact shows the private-kind label');
          if(row.querySelector('.gadget-row-label')?.textContent?.toLowerCase().endsWith('kind') && /^[a-z]/.test(value)) failures.push('The source kind is not sentence case');
        }
      }
      const sources=win.querySelector('[data-testid=ask-looked-at] .object-list-rows');
      if(sources?.getBoundingClientRect().height) {
        const box=edge(sources), rows=[...sources.querySelectorAll('[data-object-id]')].map(r=>r.getBoundingClientRect());
        if(rows.some(r=>r.top<box.bottom-.5 && r.bottom>box.bottom+.5)) failures.push('Sources ends in a partial row');
        if(width===1440 && rows.filter(r=>r.top>=box.top-.5 && r.bottom<=box.bottom+.5).length<Math.min(4,rows.length)) failures.push('Sources has fewer than four whole rows');
      }
      return failures;
    }""", width)


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
            assert "My whole desk" in about.get_attribute("title")
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
            page.wait_for_function(
                "note => (document.querySelector('[data-testid=\"ask-context\"]')?.title || '').includes(note)",
                arg=NOTE, timeout=T)
            assert "My whole desk" not in about.get_attribute("title")
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
    import os
    import re
    import threading
    from http.server import ThreadingHTTPServer

    from playwright.sync_api import expect, sync_playwright
    from tests._evidence import evidence_dir
    from .engine_stub_rig import _StubHandler, completion_reply
    from .glass_infra import _settle, clear_hub_windows

    answer = _shaped_answer()
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
            ctype, body = completion_reply(request, body)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    model = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=model.serve_forever, daemon=True).start()
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = evidence_dir("ask14r2")
    stage = os.environ.get("ASK_GLASS_STAGE", "after")
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
                              "expected_profile_revision": 0, "label": "Architecture review · local engine",
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
                page.screenshot(path=str(shots / f"checks-empty-{stage}-{900 if width == 1440 else 393}.png"))
                if width == 393:
                    window.get_by_role("button", name="Back from Ask", exact=True).click()
                    expect(window.get_by_text("No recent asks", exact=True)).to_be_visible()
                    page.screenshot(path=str(shots / f"checks-empty-recent-{stage}-393.png"))
                    window.get_by_role("button", name="Back from Ask", exact=True).click()
                facts = window.evaluate("""el => {
                  const rect = el.getBoundingClientRect();
                  const fields = node => {const r=node.getBoundingClientRect();return {
                    tag:node.tagName, cls:String(node.className), x:r.x, width:r.width,
                    scroll:node.scrollWidth, client:node.clientWidth,
                    margin:getComputedStyle(node).margin, gap:getComputedStyle(node).gap};};
                  return {window:fields(el), body:fields(el.querySelector('[data-testid="ask-body"]')), overflows:[...el.querySelectorAll('*')].filter(node => {
                    const r=node.getBoundingClientRect();return !node.closest('[aria-hidden="true"], [inert]') && getComputedStyle(node).visibility!=="hidden" && r.width && (r.right>rect.right+1 || r.left<rect.left-1);
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
                window.get_by_role("row", name=re.compile(r"What needs my attention today\?")).dblclick()
                expect(editor).to_have_value("What needs my attention today?")
                expect(editor).to_be_focused()
                assert not requests
                editor.press("Shift+Enter")
                expect(editor).to_have_value("What needs my attention today?\n")
                assert not requests

                question, draft = "What should I review with Mira?", "And what can wait until Monday?"
                editor.fill(question)
                editor.press("Enter")
                expect(editor).to_have_value("")
                expect(window.get_by_role("button", name="Stop", exact=True)).to_be_visible()
                expect(window.locator(".surface-object-reading").first).to_contain_text(question)
                assert started.wait(10), "Private model did not receive the real Ask"
                editor.fill(draft)
                editor.press("Enter")
                expect(editor).to_have_value(draft)
                assert len(requests) == 1
                page.screenshot(path=str(shots / f"checks-asking-{stage}-{900 if width == 1440 else 393}.png"))
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
                reading = window.locator(".surface-object-reading").first
                reading.evaluate("el => el.scrollTop = 0")
                page.wait_for_timeout(100)
                page.screenshot(path=str(shots / f"checks-answer-{stage}-{900 if width == 1440 else 393}.png"))
                measure = window.locator("[data-testid=ask-turn] .reading-document").evaluate("""el => {
                  const style=getComputedStyle(el), box=el.getBoundingClientRect();
                  return {font:parseFloat(style.fontSize), line:parseFloat(style.lineHeight), width:box.width};
                }""")
                assert measure["font"] >= 14 and measure["line"] >= 21, measure
                assert measure["width"] <= 760, measure
                expect(window.locator("[data-testid=ask-turn] pre code")).to_have_text(f"git status --short\ncheckpoint={LONG_TOKEN}")
                assert reading.evaluate("el => el.scrollHeight > el.clientHeight"), "Long material must scroll in its reading viewport"
                # Text selection and scrolling must not hide the composer.
                expect(editor).to_be_in_viewport()
                expect(window.get_by_role("button", name="Ask", exact=True)).to_be_in_viewport()
                if width == 393:
                    controls = [window.get_by_role("button", name="Ask", exact=True),
                                window.locator("[data-testid=ask-toolbar] button.desk-mic").first]
                    boxes = [control.bounding_box() for control in controls]
                    assert all(boxes) and abs((boxes[0]["y"] + boxes[0]["height"]/2) - (boxes[1]["y"] + boxes[1]["height"]/2)) <= 44, boxes
                    for control in controls:
                        hit = control.evaluate("""el => {
                          const r=el.getBoundingClientRect(), points=[.1,.5,.9];
                          return {w:r.width,h:r.height,owned:points.every(x=>points.every(y=> {
                            const owner=document.elementFromPoint(r.left+r.width*x,r.top+r.height*y);
                            return owner===el || el.contains(owner);
                          }))};
                        }""")
                        assert hit["w"] >= 44 and hit["h"] >= 44 and hit["owned"], hit
                reading.evaluate("el => el.scrollTop = el.scrollHeight")
                actions = window.get_by_test_id("ask-actions")
                expect(actions).to_be_in_viewport(ratio=1)
                page.screenshot(path=str(shots / f"checks-answer-tail-{stage}-{900 if width == 1440 else 393}.png"))
                expect(editor).to_be_in_viewport()
                expect(window.get_by_role("button", name="Ask", exact=True)).to_be_in_viewport()
                assert not errors, errors
            finally:
                browser.close()
    finally:
        release.set()
        server.stop()
        model.shutdown()
        model.server_close()


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_ask_selection_question_sources_and_recovery_fit_the_frame(tmp_path, monkeypatch, width):
    """Recorded real hub answers prove face geometry; no live provider is used.

    The isolated server carries the real websocket frame. Ask/decide/keep
    replies replay the checked-in producer tapes; this test claims rendering.
    """
    import json
    import os
    import re
    from playwright.sync_api import expect, sync_playwright
    from tests._evidence import evidence_dir
    from .glass_infra import _settle, clear_hub_windows

    wire_dir = Path(__file__).resolve().parents[2] / "web/src/test/wire"
    tapes = {key: json.loads((wire_dir / f"{key}.wire.json").read_text())
             for key in ["ask.hold", "ask.thread", "ask.tools", "ask.no-engine", "notes-create"]}
    hold, thread, tools = tapes["ask.hold"], tapes["ask.thread"], tapes["ask.tools"]
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    from holdspeak.db import get_database
    thread = _stored_long_thread(get_database(), thread)
    answer_count = sum(message["role"] == "assistant" for message in thread["thread"]["messages"])
    hold["answer"]["output"] = _shaped_answer()
    shots = evidence_dir("ask14r2")
    stage = os.environ.get("ASK_GLASS_STAGE", "after")
    pending, decisions = [], []
    seat_failures = []
    note_fail = [True]
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            page.add_init_script("crypto.randomUUID = () => 'cccccccc-cccc-cccc-cccc-cccccccccccc'")
            page.route("**/api/ask", lambda route: pending.append(route))
            page.route("**/api/threads", lambda route: route.fulfill(json=thread["recent"]))
            page.route(f"**/api/threads/{thread['first']['thread_id']}", lambda route: route.fulfill(json=thread["thread"]))
            page.route("**/api/ask/engine", lambda route: route.fulfill(json=tools["engine"]))
            page.route("**/api/inference/assignments", lambda route: route.fulfill(json=tools["assignments"]))

            def decide(route):
                decisions.append(route.request.post_data_json)
                if route.request.post_data_json["decision"] == "approve":
                    route.fulfill(status=503, json={})
                else:
                    route.fulfill(json=hold["decided"])

            def note(route):
                if route.request.method != "POST":
                    route.continue_()
                elif note_fail[0]:
                    route.fulfill(status=503, json={})
                else:
                    route.fulfill(status=201, json=tapes["notes-create"]["wire"])

            page.route("**/api/threads/*/decide", decide)
            page.route("**/api/notes", note)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            clear_hub_windows(page, TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            page.keyboard.press("Control+KeyI")
            win = page.locator("[id=ask][data-layer=window]")
            editor = win.get_by_role("textbox", name="Ask about your work", exact=True)
            editor.wait_for()
            _settle(page)

            def shot(state):
                _settle(page)
                page.screenshot(path=str(shots / f"checks-{state}-{stage}-{900 if width == 1440 else 393}.png"))
                seat_failures.extend((state, reason) for reason in _seat_failures(win, width))
                if state == "thread-open" and not win.locator(".surface-object-reading").evaluate("el => {const r=el.getBoundingClientRect(), h=[...el.querySelectorAll('[data-testid=ask-turn] > h3')].at(-1).getBoundingClientRect();return h.top>=r.top-1 && h.bottom<=r.bottom+1;}"):
                    seat_failures.append((state, "The thread opens past its newest question"))
                expect(win.locator(".surface-mast-title")).to_have_count(1)
                if width == 1440:
                    box = win.bounding_box()
                    assert box and box["width"] == 900 and box["height"] == 600, box
                if win.get_by_test_id("ask-reading").is_visible():
                    expect(editor).to_be_in_viewport()
                toolbar = win.get_by_test_id("ask-actions")
                assert toolbar.evaluate("el => {const r=el.getBoundingClientRect(); const buttons=[...el.querySelectorAll(':scope > .kit-toolbar-verbs button')].filter(b=>b.getBoundingClientRect().width && !b.closest('[inert]'));return buttons.every(b=>{const x=b.getBoundingClientRect();return x.top>=r.top && x.bottom<=r.bottom && Math.abs(x.top-buttons[0].getBoundingClientRect().top)<2;});}")
                sources = win.get_by_test_id("ask-looked-at")
                if sources.count() and win.get_by_test_id("ask-reading").is_visible():
                    expect(sources).to_be_visible()
                    assert sources.evaluate("el => {const r=el.querySelector('[role=grid]').getBoundingClientRect(), field=document.querySelector('[data-testid=ask-toolbar]').getBoundingClientRect();return r.bottom<=field.top && [...el.querySelectorAll('button')].filter(n=>!n.closest('[inert]')).every(n=>n.getBoundingClientRect().bottom<=r.bottom+1);}")
                assert win.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")

            def verb(name):
                target = win.get_by_test_id("ask-actions").get_by_role("button", name=name, exact=True)
                if target.count() and target.is_visible():
                    return target
                win.get_by_test_id("ask-actions").get_by_role("button", name="Actions ▾", exact=True).click()
                page.screenshot(path=str(shots / f"checks-actions-open-{stage}-{900 if width == 1440 else 393}.png"))
                return page.get_by_role("menuitem", name=name, exact=True)

            shot("empty-seeded")
            # Recent's list is one well; Return opens the selected saved thread.
            if width == 393:
                verb("Recent").click()
            row = win.get_by_role("grid", name="Recent", exact=True).get_by_role("row", name=re.compile("What do I owe Mira"))
            row.click()
            shot("recent-selected") if width == 1440 else page.screenshot(path=str(shots / f"checks-recent-selected-{stage}-393.png"))
            row.press("Enter")
            expect(win.get_by_test_id("ask-turn")).to_have_count(answer_count)
            shot("thread-open")
            verb(f"Answer: {answer_count}").click()
            shot("answer-menu")
            last_answer = page.get_by_role("menuitem", name=f"{answer_count}. When should I tell her?", exact=True)
            if not last_answer.evaluate("el => {const r=el.closest('[role=menu]').getBoundingClientRect(), w=document.querySelector('[id=ask][data-layer=window]').getBoundingClientRect();return r.top>=w.top && r.bottom<=w.bottom;}"):
                seat_failures.append(("answer-menu", "The answer menu leaves the viewport"))
            last_answer.focus()
            shot("answer-menu-tail")
            if not last_answer.evaluate("el => {const r=el.getBoundingClientRect(), m=el.closest('[role=menu]').getBoundingClientRect();return r.top>=m.top && r.bottom<=m.bottom && r.top>=0 && r.bottom<=innerHeight;}"):
                seat_failures.append(("answer-menu-tail", "The last answer cannot scroll into view"))
            last_answer.press("Enter")
            verb("Recent").click()
            shot("recent-folded" if width == 1440 else "recent-restored")
            verb("Recent").click()
            shot("recent-restored" if width == 1440 else "recent-folded")
            source = win.get_by_test_id("ask-looked-at").last.get_by_role("row", name=re.compile("1:1 with Mira"))
            source.click()
            shot("source-selected")
            source.click(button="right")
            shot("source-menu")
            assert page.get_by_role("menu", name="Sources actions").evaluate("el => {const m=el.getBoundingClientRect(), r=document.querySelector('[data-testid=ask-looked-at] [aria-selected=true]')?.getBoundingClientRect();return r && (m.top>=r.bottom-1 || m.bottom<=r.top+1);}")
            page.keyboard.press("Escape")
            verb("About").click()
            popup = page.get_by_test_id("ask-scope-menu")
            expect(popup).to_be_visible()
            shot("scope-open")
            assert popup.locator("..").evaluate("el => {const r=el.getBoundingClientRect();return r.left>=0 && r.right<=innerWidth;}")
            assert popup.locator(".object-list-rows").evaluate("el => {const r=el.getBoundingClientRect(), row=el.querySelector('[data-object-id]')?.getBoundingClientRect();return !row || (row.top>=r.top-1 && row.bottom<=r.bottom+1);}")
            popup.get_by_role("textbox", name="Find a meeting, note, person").fill("Mira")
            shot("scope-search")
            popup.get_by_role("row", name=re.compile("1:1 with Mira")).dblclick()
            expect(popup).to_have_count(0)
            shot("scope-chosen")
            reading = win.locator(".surface-object-reading").first
            reading.evaluate("el => el.scrollTop = 0")
            verb("Save as note").click()
            expect(win.get_by_role("button", name="Retry", exact=True)).to_be_visible()
            shot("save-failed")
            assert reading.evaluate("el => el.scrollHeight > el.clientHeight")
            reading.evaluate("el => el.scrollTop = el.scrollHeight")
            shot("save-failed-tail")
            assert reading.evaluate("el => {const r=el.getBoundingClientRect(), tail=el.querySelector('article:last-child .reading-document')?.lastElementChild?.getBoundingClientRect();return tail && tail.bottom<=r.bottom+1;}")
            note_fail[0] = False
            win.get_by_role("button", name="Retry", exact=True).click()
            expect(win.get_by_text("Saved to your desk", exact=True)).to_be_visible()
            shot("saved")
            reading.evaluate("el => el.scrollTop = el.scrollHeight")
            shot("saved-tail")
            assert reading.evaluate("el => {const r=el.getBoundingClientRect(), tail=el.querySelector('article:last-child')?.lastElementChild?.getBoundingClientRect();return tail && tail.top>=r.top-1 && tail.bottom<=r.bottom+1;}")
            verb("New ask").click()
            editor.fill("What do I owe Mira this week?")
            editor.press("Enter")
            expect(win.get_by_test_id("run-line")).to_be_visible()
            assert pending
            shot("asking")
            server.broadcast("ask_progress", hold["hold"])
            expect(win.get_by_test_id("ask-hold")).to_be_visible()
            shot("held")
            question = win.get_by_test_id("ask-hold")
            expect(question.get_by_text("Give Mira feedback on the cutover design doc", exact=True)).to_be_visible()
            expect(question.get_by_role("button", name="Deny", exact=True)).to_be_focused()
            for name in ["Deny", "Allow once"]:
                assert question.get_by_role("button", name=name, exact=True).evaluate("""el => {
                  const r=el.getBoundingClientRect(); return [.1,.5,.9].every(x=>[.1,.5,.9].every(y=>{const hit=document.elementFromPoint(r.left+r.width*x,r.top+r.height*y);return hit===el||el.contains(hit);}));
                }""")
            question.get_by_role("button", name="Allow once", exact=True).click()
            expect(question.get_by_text("Answer not sent. Try again.", exact=True)).to_be_visible()
            shot("held-failed")
            for name in ["Deny", "Allow once"]:
                bounds = question.get_by_role("button", name=name, exact=True).evaluate("""el => {
                  const r=el.getBoundingClientRect(), well=el.closest('.surface-pane-inspector').getBoundingClientRect();
                  return {inside:r.top>=well.top && r.bottom<=well.bottom, button:r.toJSON(), well:well.toJSON()};
                }""")
                assert bounds["inside"], bounds
            question.get_by_role("button", name="Deny", exact=True).click()
            expect(win.get_by_test_id("ask-hold")).to_have_count(0)
            assert decisions == [{"call_id": hold["hold"]["holds"][0]["call_id"], "decision": "approve", "binding": hold["hold"]["holds"][0]["binding"]}, {"call_id": hold["hold"]["holds"][0]["call_id"], "decision": "deny", "binding": hold["hold"]["holds"][0]["binding"]}]
            pending.pop().fulfill(json=hold["answer"])
            expect(win.get_by_test_id("ask-turn")).to_be_visible()
            shot("denied-answer")
            verb("Show grounding").click()
            win.get_by_test_id("ask-claims").scroll_into_view_if_needed()
            shot("grounding")
            reading.evaluate("el => el.scrollTop = el.scrollHeight")
            shot("grounding-tail")
            assert win.get_by_test_id("ask-claims").locator("[data-object-id]").last.evaluate("el => {const r=el.getBoundingClientRect(), well=el.closest('.surface-object-reading').getBoundingClientRect();return r.top>=well.top && r.bottom<=well.bottom;}")
            verb("New ask").click()
            editor.fill("What needs attention?")
            editor.press("Enter")
            expect(win.get_by_test_id("run-line")).to_be_visible()
            pending.pop().fulfill(status=tapes["ask.no-engine"]["status"], json=tapes["ask.no-engine"]["refusal"])
            expect(win.get_by_test_id("ask-not-answered")).to_be_visible()
            shot("no-engine")
            assert not seat_failures, seat_failures
            browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("width", [1440, 393])
def test_ask_long_rosters_empty_recent_quote_and_tool_facts(tmp_path, monkeypatch, width):
    """Large collections use real stored names; held facts use the live projector.

    Only the model answer is replayed. No held call is executed or sent.
    """
    import json
    import os
    import re
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.thread_service import ThreadService
    from holdspeak.services.thread_tools import ToolCallHandle
    from holdspeak.services.held_tool_details import held_call_details
    from tests._evidence import evidence_dir
    from .glass_infra import _settle, clear_hub_windows

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "ask-glass")
    primitives = PrimitiveService(db)
    # Sentence names, path- and code-led names, and an unbroken identifier.
    names = [f"{lead} — keep the approved deployment available while the architecture review checks the recovery point, migration result, retained draft and next owner action for the platform team {n:02d}"
             for n, lead in enumerate(["web/src/desk/components/AskWorkspace.tsx", "`held_call_details`", "architecture_review_checkpoint_" + "a" * 96] * 17)][:50]
    names[0], names[1] = LONG_SCOPE, PATH_SCOPE
    notes = [primitives.create_note(owner, note_id=f"ask-long-{n}", title=name, body_markdown="Keep the recovery point until the review is complete.") for n, name in enumerate(names)]
    for name in names:
        db.threads.create_thread(title=name)
    recent = ThreadService(db, broadcast=lambda *_: None).list_threads()
    wire = Path(__file__).resolve().parents[2] / "web/src/test/wire"
    tools = json.loads((wire / "ask.tools.wire.json").read_text())
    # These names and ids come from the same real note producer as the desk.
    answer = {**tools["answer"], "output": _shaped_answer(), "looked_at": [{"ref": f"note:{note['id']}", "title": note["title"], "kind": "note"} for note in notes]}
    shots = evidence_dir("ask14r2")
    stage = os.environ.get("ASK_GLASS_STAGE", "after")
    pending, recent_requests = [], []
    seat_failures = []
    delay_recent = [False]
    invocation = "ask_" + "c" * 32
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.add_init_script("crypto.randomUUID = () => 'cccccccc-cccc-cccc-cccc-cccccccccccc'")
            page.route("**/api/threads", lambda route: recent_requests.append(route) if delay_recent[0] else route.fulfill(json={"threads": []}))
            page.route("**/api/ask", lambda route: pending.append(route))
            page.route("**/api/ask/engine", lambda route: route.fulfill(json=tools["engine"]))
            page.route("**/api/inference/assignments", lambda route: route.fulfill(json=tools["assignments"]))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            clear_hub_windows(page, TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            delay_recent[0] = True
            page.keyboard.press("Control+KeyI")
            win = page.locator("[id=ask][data-layer=window]")
            editor = win.get_by_role("textbox", name="Ask about your work", exact=True)
            editor.wait_for()

            def shot(state):
                _settle(page)
                page.screenshot(path=str(shots / f"{state}-{stage}-{900 if width == 1440 else 393}.png"))
                seat_failures.extend((state, reason) for reason in _seat_failures(win, width))
                assert win.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                assert not errors, errors

            def verb(name):
                bar = win.get_by_test_id("ask-actions")
                target = bar.get_by_role("button", name=name, exact=True)
                if target.count() and target.is_visible():
                    return target
                bar.get_by_role("button", name="Actions ▾", exact=True).click()
                return page.get_by_role("menuitem", name=name, exact=True)

            if width == 393:
                verb("Recent").click()
            shot("1-recent-reading")
            assert recent_requests
            recent_requests.pop().fulfill(json={"threads": []})
            expect(win.get_by_text("No recent asks", exact=True)).to_be_visible()
            shot("1-recent-empty")
            if width == 393:
                win.get_by_role("button", name="Back from Ask", exact=True).click()
            shot("2-empty")
            editor.fill("Check the recovery point")
            editor.press("Enter")
            expect(win.get_by_test_id("run-line")).to_be_visible()
            if width == 393:
                verb("Recent").click()
            expect(win.get_by_role("row", name=re.compile("Check the recovery point"))).to_be_visible()
            shot("1-first-ask")
            if width == 393:
                win.get_by_role("button", name="Back from Ask", exact=True).click()

            for tool, args, state in [
                ("thread.set_status", {"thread_id": "ask-facts", "text": "Reading sources"}, "9-held-undeclared"),
                ("door.add_item", {"task": "Review the platform recovery point", "owner": "Me", "due": "2026-11-20"}, "9-held-task"),
            ]:
                handle = ToolCallHandle(call_id=state, thread_id="ask-facts", turn_operation_id=invocation,
                                        name=tool, args=args, tool_class="effect_proposal", sensitive=False,
                                        state="awaiting_decision", principal=owner)
                details = held_call_details(handle, owner)
                if state == "9-held-undeclared":
                    assert details["facts"] == [{"label": "Write details", "value": "not described"}]
                server.broadcast("ask_progress", {"invocation_id": invocation, "state": "hold", "thread_id": "ask-facts", "holds": [details]})
                question = win.get_by_test_id("ask-hold")
                expect(question).to_be_visible()
                for fact in details["facts"]:
                    expect(question.get_by_text(fact["label"], exact=True)).to_be_visible()
                    expect(question.get_by_text("Nov 20" if fact["label"] == "Due" else fact["value"], exact=True)).to_be_visible()
                shot(state)
            authority = json.loads((wire / "ask.held-authority.wire.json").read_text())["held"]
            server.broadcast("ask_progress", {"invocation_id": invocation, "state": "hold", "thread_id": "ask-facts", "holds": [authority]})
            expect(win.get_by_test_id("ask-hold").get_by_text("Authority binding", exact=True)).to_be_visible()
            shot("9-held-authority")
            reading = win.get_by_test_id("ask-hold").locator(".surface-inspector-fields")
            reading.evaluate("el => el.scrollTop = 0")
            shot("9-held-authority-head")
            reading.evaluate("el => el.scrollTop = el.scrollHeight")
            shot("9-held-authority-tail")
            send = json.loads((wire.parents[1] / "desk/calls/__fixtures__/calls.face.json").read_text())["held"]["hold"]
            server.broadcast("ask_progress", {"invocation_id": invocation, "state": "hold", "thread_id": "ask-facts", "holds": [send]})
            expect(win.get_by_test_id("ask-hold").get_by_text("the team", exact=True)).to_be_visible()
            shot("9-held-send")
            pending.pop().fulfill(json=answer)
            expect(win.get_by_test_id("ask-turn")).to_be_visible()
            shot("3-many-sources")
            expect(editor).to_be_in_viewport()
            if not win.locator(".surface-object-reading").evaluate("el => {const r=el.getBoundingClientRect(), head=el.querySelector('h3').getBoundingClientRect(); return head.top>=r.top && head.bottom<=r.bottom;}"):
                seat_failures.append(("3-many-sources", "The answer opens past its question"))
            sources = win.get_by_test_id("ask-looked-at")
            assert sources.locator("[data-object-id]").count() == len(notes)
            sources.locator("[data-object-id]").last.click()
            expect(sources.get_by_role("button", name="Open source", exact=True)).to_be_enabled()
            expect(editor).to_be_in_viewport()
            shot("3-last-source")
            # The completed answer refreshes Recent through its normal read.
            assert recent_requests
            recent_requests.pop().fulfill(json={"threads": recent})
            if width == 393:
                verb("Recent").click()
            expect(win.get_by_role("grid", name="Recent", exact=True).locator("[data-object-id]")).to_have_count(len(recent))
            shot("2-recent-long")
            if width == 393:
                win.get_by_role("button", name="Back from Ask", exact=True).click()
            verb("New ask").click()
            page.evaluate("source => window.dispatchEvent(new CustomEvent('holdspeak:ask-selection', {detail: source}))", {
                "noteRef": "note:ask-long-0", "text": "Keep the recovery point until the review is complete.",
                "body": "Keep the recovery point until the review is complete.", "range": {"from": 0, "to": 52, "text": "Keep the recovery point until the review is complete."},
                "windowId": "pullout:note:ask-long-0", "scrollTop": 0,
                "source": {"id": "ask-long-0", "kind": "note", "title": names[0], "ref": "note:ask-long-0"},
            })
            expect(win.get_by_test_id("ask-selected-passage")).to_be_visible()
            shot("2-source-quote")
            # Pinned scope without selected text must still name the same note.
            win.get_by_role("button", name="Clear quote", exact=True).click()
            shot("2-pinned-scope")
            verb(re.compile("^About")).press("Enter")
            shot("2-pinned-scope-open")
            page.keyboard.press("Escape")
            page.evaluate("source => window.dispatchEvent(new CustomEvent('holdspeak:ask-selection', {detail: source}))", {
                "noteRef": "note:ask-long-1", "text": "Keep the recovery point until the review is complete.",
                "body": "Keep the recovery point until the review is complete.",
                "range": {"from": 0, "to": 52, "text": "Keep the recovery point until the review is complete."},
                "windowId": "pullout:note:ask-long-1", "scrollTop": 0,
                "source": {"id": "ask-long-1", "kind": "note", "title": names[1], "ref": "note:ask-long-1"},
            })
            shot("2-path-scope")
            verb(re.compile("^About")).press("Enter")
            shot("2-path-scope-open")
            page.get_by_test_id("ask-scope-menu").get_by_role("textbox", name="Find a meeting, note, person").fill("review")
            shot("2-scope-roster")
            page.keyboard.press("Escape")
            assert not seat_failures, seat_failures
            browser.close()
    finally:
        server.stop()
