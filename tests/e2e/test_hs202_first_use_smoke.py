"""HS-202-01: fixture first-use fence; normal RED, explicit verification GREEN.

HS202_EXPECTED_FAILURES=1 requires the exact observed defect set. Only final
on-screen observations can enter that set. Setup, content loading, HTTP,
persistence, route truth and engine errors always fail normally.
"""
from __future__ import annotations

import os
import re
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pytest
from playwright.sync_api import TimeoutError as BrowserTimeout, expect, sync_playwright

from holdspeak.intel_queue import process_next_intel_job
from holdspeak.intel_queue_conductor import _on_meeting_ready
from holdspeak.kernel.runtime import _configure
from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route
from .glass_infra import (
    REPO, SPEECH_CAPABILITY, _api, _boot, _ensure_build, _normal_chair,
    assign_engine, engine_profile,
)
from .test_hs201_09_connect_engine_glass import _StubHandler
from .test_hs201_one_thing_glass import _quiet_concierge
from .test_hs201_summary_face_glass import _FixtureImportTranscriber, _chip_label

TOKEN = "hs202-first-use"
WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"
WORDS = "The quick brown fox jumps over the lazy dog."
NOTE_TITLE = "Fence architecture note"
NOTE_BODY = "Review the service boundary with the team on Tuesday."
MEETING_TITLE = "Fence fixture meeting"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence"
KNOWN = {
    1440: {"thought-door", "save-confirmation", "import-refresh", "record-refresh", "notes-query"},
    393: {
        "dock-memory", "menu-Desk", "menu-Object", "menu-Window",
        "thought-door", "save-confirmation", "import-refresh", "record-refresh", "notes-query",
    },
}
pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180, method="thread")]


def _loaded(locator):
    """Wait for visible content; job assertions use the exact saved text."""
    locator.wait_for(state="visible", timeout=10_000)
    assert (locator.inner_text() or "").strip() not in {"", "…", "...", "Loading…"}
    return locator


def _hit(locator, *, fit=True):
    if locator.count() != 1 or not locator.is_visible():
        return False
    return locator.evaluate("""(el, fit) => {
      const r = el.getBoundingClientRect();
      const left=Math.max(0,r.left), right=Math.min(innerWidth,r.right);
      const topEdge=Math.max(0,r.top), bottom=Math.min(innerHeight,r.bottom);
      const top = document.elementFromPoint((left+right)/2, (topEdge+bottom)/2);
      return right>left && bottom>topEdge && (!fit || (r.x>=0 && r.y>=0 &&
        r.right<=innerWidth+1 && r.bottom<=innerHeight+1)) &&
        !!top && (top===el || el.contains(top));
    }""", fit)


def _desk(page, base):
    """Between jobs only: clear remembered windows, keeping all saved objects."""
    page.evaluate("localStorage.removeItem('hs.desk.workspace.v1')")
    page.goto(base + "/?token=" + TOKEN)
    _normal_chair(page)
    _loaded(page.get_by_test_id("arrival-display"))
    _loaded(page.get_by_test_id("arrival-capture-bar"))


def _meetings(page, *, recovery=False):
    if recovery:
        print("RECOVERY: open Meetings after the recorded dock failure; not a door pass.")
        page.evaluate("""sessionStorage.setItem(
          'hs.desk.staged-surface-open', JSON.stringify({key:'review-meetings'}))""")
        page.reload()
        _normal_chair(page)
    else:
        door = page.locator(".desk-dock").get_by_role("button", name="Meetings", exact=True)
        assert _hit(door), "Meetings door became unreachable after the dock check"
        door.click()
    _loaded(page.locator(".meetings-head-verbs"))


def _fixture_engine(monkeypatch, db):
    engine = FakeIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(()))
    monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **_: _Route(()))
    return engine


class _AudioImport(_FixtureImportTranscriber):
    def __init__(self, permit):
        self.permit = permit

    def transcribe(self, audio, **admission):
        assert self.permit.wait(10), "The importing row did not load"
        values = np.asarray(audio)
        assert values.size and np.max(np.abs(values)) > 0, "Import received no fixture audio"
        return super().transcribe(audio, **admission)


def _search(page, query, *, keyboard=False):
    door = page.locator(".desk-tools-launch")
    assert _hit(door, fit=False), "Search must have a pointer door; keyboard alone is not sufficient"
    if keyboard:
        # A stationary pointer over the results can select a hovered row
        # when the query reorders them. Exercise the keyboard selection.
        page.mouse.move(0, 0)
        page.keyboard.press("Meta+k")
    else:
        door.click()
    shelf = page.get_by_role("region", name="Tools and Desk search", exact=True)
    _loaded(shelf.get_by_role("option").first)
    field = shelf.get_by_role("combobox", name="Search tools and Desk items", exact=True)
    field.fill(query)
    expect(field).to_have_value(query)
    _loaded(shelf.get_by_role("option").first)
    return shelf, field


def _refind_note(page, note_id):
    # Two navigation gestures: Search, then Enter. Typing is not navigation.
    shelf, field = _search(page, NOTE_TITLE)
    target = shelf.locator('[id="desk-palette-option-note:' + note_id + '"]')
    _loaded(target)
    expect(field).to_have_attribute("aria-activedescendant", target.get_attribute("id"))
    field.press("Enter")
    note = page.get_by_role("region", name=NOTE_TITLE, exact=True)
    _loaded(note.get_by_text(NOTE_BODY, exact=True))
    print("PASS: refind the saved note and its body in two navigation moves")


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_first_use_fence(tmp_path: Path, monkeypatch, width, height):
    _ensure_build()
    _quiet_concierge(monkeypatch)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json"))
    import holdspeak.web_server as web_server
    from holdspeak.db import get_database
    from holdspeak.web.routes import meeting_import
    from holdspeak.services import meeting_service

    received = []
    original_callbacks = web_server.WebRuntimeCallbacks

    def transcribe(audio, **_):
        values = np.asarray(audio)
        assert values.size and np.max(np.abs(values)) > 0, "Speech received no fixture audio"
        received.append(values.size)
        return WORDS

    def callbacks(**kwargs):
        return original_callbacks(**kwargs, on_transcribe=transcribe)

    monkeypatch.setattr(web_server, "WebRuntimeCallbacks", callbacks)
    permit_import, import_done = threading.Event(), threading.Event()
    import_audio = meeting_service.run_meeting_import

    def import_fixture(*args, **kwargs):
        try:
            return import_audio(*args, **kwargs)
        finally:
            import_done.set()

    monkeypatch.setattr(meeting_service, "run_meeting_import", import_fixture)
    monkeypatch.setattr(meeting_import, "_transcriber_factory", lambda _: _AudioImport(permit_import))
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    engine = _fixture_engine(monkeypatch, db)
    stub = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
    thread = threading.Thread(target=stub.serve_forever, daemon=True)
    thread.start()
    failures = set()
    shots = SHOTS if os.environ.get("HS202_EXPORT_SHOTS") == "1" else tmp_path / "shots"
    shots.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height})
            page.set_default_timeout(10_000)
            page.emulate_media(reduced_motion="reduce")

            def shot(name):
                path = shots / (name + "-" + str(width) + ".png")
                page.screenshot(path=str(path))
                assert path.stat().st_size > 2000
                print("SHOT", path.relative_to(REPO) if path.is_relative_to(REPO) else path)

            def check(name, passed, message):
                # No action/click/API runs inside this collector.
                print(("PASS: " if passed else "FAIL: ") + message)
                if not passed:
                    failures.add(name)
                    shot(name)
                return passed

            def observe(name, expression, message, arg=None):
                # Only a bounded final DOM observation can become expected.
                try:
                    page.wait_for_function("""arg => {
                      const visible = el => {
                        if (!el) return false;
                        const r=el.getBoundingClientRect(), s=getComputedStyle(el);
                        return r.width>0 && r.height>0 && r.bottom>0 && r.right>0 &&
                          r.top<innerHeight && r.left<innerWidth && s.visibility==='visible' &&
                          s.display!=='none' && Number(s.opacity)>0;
                      };
                      return (""" + expression + ")(arg); }", arg=arg, timeout=2500)
                except BrowserTimeout:
                    return check(name, False, message)
                return check(name, True, message)

            # Job 1: the real capture/WS path, supplied only by Chromium's WAV device.
            sockets, frames = [], []
            def watch(socket):
                if "/ws/dictation/stream" in socket.url:
                    sockets.append(socket)
                    socket.on("framesent", lambda data: frames.append(data) if isinstance(data, bytes) else None)
            page.on("websocket", watch)
            page.goto(base + "/welcome?token=" + TOKEN)
            talk = _loaded(page.get_by_role("button", name="Click to dictate", exact=True))
            assert _hit(talk), "First Words speech door is unreachable"
            talk.click()
            page.get_by_role("button", name="Stop listening", exact=True).wait_for()
            assert sockets, "Speech did not open its production WebSocket"
            if not frames:
                sockets[0].wait_for_event("framesent", predicate=lambda data: isinstance(data, bytes), timeout=5000)
            page.get_by_role("button", name="Stop listening", exact=True).click()
            expect(page.get_by_role("textbox", name="Your dictated text")).to_have_value(WORDS)
            assert len(received) == 1 and frames
            page.get_by_role("button", name="Keep as Note", exact=True).click()
            first_note = page.get_by_role("region", name="First dictation", exact=True)
            _loaded(first_note.get_by_text(WORDS, exact=True))
            shot("fixture-speech-kept")
            print("PASS: fixture speech became visible text and a kept note; PCM samples", received[0])

            # Job 5: one real UI setup gesture, with a deterministic localhost endpoint.
            _desk(page, base)
            choose = page.get_by_role("button", name="Choose an engine", exact=True)
            _loaded(choose)
            assert _hit(choose)
            choose.click()
            _loaded(page.get_by_test_id("concierge-add-engine"))
            page.get_by_test_id("concierge-add-engine").click()
            address = page.locator("[data-testid='concierge-add-engine-row'] input").first
            endpoint = "http://127.0.0.1:" + str(stub.server_address[1]) + "/v1"
            address.fill(endpoint)
            _loaded(page.get_by_test_id("concierge-add-egress"))
            assert "127.0.0.1" in page.get_by_test_id("concierge-add-egress").inner_text()
            page.get_by_test_id("concierge-add-check").click()
            expect(page.get_by_test_id("concierge-add-model")).to_have_text(_StubHandler.MODEL)
            with page.expect_response(lambda response: response.url.endswith("/define-endpoint")
                                      and response.request.method == "POST") as defined:
                page.get_by_test_id("concierge-add-submit").click()
            assert defined.value.ok, defined.value.text()
            assert defined.value.request.post_data_json["draft"]["endpoint"] == endpoint
            provider = defined.value.json()["provider"]
            assert provider["profile_id"] and provider["profile_revision"] > 0
            page.get_by_test_id("concierge-root").wait_for(state="detached")
            page.get_by_role("button", name="Choose an engine", exact=True).wait_for(state="detached")
            _loaded(page.get_by_test_id("arrival-display"))
            print("PASS: engine setup completed visibly without a reload")
            shot("engine-set")

            # Persistent doors: real hit ownership, normal clicks, loaded destination.
            dock = page.locator(".desk-dock")
            doors = {}
            for key, name in (("speak", "Speak"), ("meetings", "Meetings"), ("memory", "Desk memory")):
                doors[key] = check("dock-" + key,
                                   _hit(dock.get_by_role("button", name=name, exact=True)),
                                   name + " dock door fits and owns its hit target")
            meetings_ok = doors["meetings"]
            if meetings_ok:
                _meetings(page)
                _desk(page, base)
            if width <= 720:
                # HS-202-02 folds the three phone-unrenderable titles into the
                # one reachable Go door. Keep the inventory names so the
                # original five/nine failure vocabulary remains stable.
                go_title = page.locator(".desk-verbbar").get_by_role(
                    "button", name="Go", exact=True
                )
                assert _hit(go_title), "Go menu door is unreachable at 393"
                go_title.click()
                folded = page.get_by_role("menu", name="Go menu", exact=True)
                _loaded(folded.get_by_role("menuitem").first)
                shot("folded-go-menu")

                def folded_item(key, label, message, *, ghosted=False):
                    # A hidden title is not a compact-width door. The content
                    # must be in Go and the row must own a hit after the
                    # menu's nearest scroll path has been used.
                    separate_title = page.locator(".desk-verbbar").get_by_role(
                        "button", name=key.removeprefix("menu-"), exact=True
                    )
                    item = folded.get_by_role("menuitem").filter(has=page.locator(
                        ".desk-menu-label").filter(has_text=re.compile(
                            r"^" + re.escape(label) + r"(?:\s*·|$)")))
                    if item.count() != 1:
                        return check(key, False, message + " (missing from Go)")
                    try:
                        item.scroll_into_view_if_needed(timeout=2500)
                    except BrowserTimeout:
                        return check(key, False, message + " (cannot scroll to Go item)")
                    title_ok = separate_title.count() == 0
                    row_ok = item.is_visible() and _hit(item)
                    # Object/Window may be ghosted by the current context;
                    # either state is valid once the folded row is visible.
                    state_ok = ghosted or item.get_attribute("aria-disabled") != "true"
                    passed = check(key, title_ok and row_ok and state_ok, message)
                    if passed:
                        shot("folded-" + key)
                    else:
                        print("MENU GEOMETRY", key, item.bounding_box(),
                              folded.evaluate("e => ({height:e.clientHeight, scrollHeight:e.scrollHeight, overflow:getComputedStyle(e).overflowY})"))
                    return passed

                folded_item(
                    "menu-Desk", "New Note",
                    "New Note is visible and reachable in the folded Go menu",
                )
                folded_item(
                    "menu-Object", "Open",
                    "Open is visible and reachable as an Object entry in Go",
                    ghosted=True,
                )
                folded_item(
                    "menu-Window", "Close window",
                    "Close window is visible and reachable as a Window entry in Go",
                    ghosted=True,
                )
                page.keyboard.press("Escape")
            else:
                for name in ("Desk", "Object", "Go", "Window"):
                    title = page.locator(".desk-verbbar").get_by_role("button", name=name, exact=True, include_hidden=True)
                    if not check("menu-" + name, _hit(title), name + " menu door is reachable"):
                        continue
                    title.click()
                    menu = page.get_by_role("menu", name=name + " menu", exact=True)
                    _loaded(menu.get_by_role("menuitem").first)
                    print("PASS:", name, "menu content loaded")
                    page.keyboard.press("Escape")

            # Job 3: the named door must lead to a place that keeps a thought.
            _desk(page, base)
            thought = page.get_by_test_id("arrival-develop-thought")
            assert _hit(thought)
            thought.click()
            page.wait_for_function("""() => !!document.querySelector(
              '.speak-face textarea, [id^="editor:note:"] .cm-content, .thought-note-document [aria-label="Note body"]')""")
            note_editor = page.locator(
                '[id^="editor:note:"] .cm-content, .thought-note-document [aria-label="Note body"]')
            if note_editor.count() == 1:
                note_editor.wait_for(state="visible")
                assert note_editor.get_attribute("contenteditable") == "true"
            check("thought-door",
                  note_editor.count() == 1 and note_editor.is_visible(),
                  "Write a thought opens a note authoring surface")
            _desk(page, base)

            # The actual New Note command; no pre-seeded note can satisfy this proof.
            before_notes = {note["id"] for note in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
            desk_menu = page.locator(".desk-verbbar").get_by_role("button", name="Desk", exact=True, include_hidden=True)
            if width <= 720 and "menu-Desk" not in failures:
                # At 393 the actual create path is Go -> New Note. The old
                # keyboard recovery is allowed only after that named check
                # records its inventory failure.
                go_title = page.locator(".desk-verbbar").get_by_role("button", name="Go", exact=True)
                assert _hit(go_title), "Go menu door is unreachable for New Note"
                go_title.click()
                folded = page.get_by_role("menu", name="Go menu", exact=True)
                new_note = folded.get_by_role(
                    "menuitem", name=re.compile(r"^New Note(?:\s|$)")
                )
                assert new_note.count() == 1, "Go menu does not expose New Note"
                new_note.scroll_into_view_if_needed()
                assert _hit(new_note), "Go -> New Note is not reachable at 393"
                new_note.click()
            elif _hit(desk_menu):
                desk_menu.click()
                page.get_by_role("menuitem", name=re.compile(r"^New Note")).click()
            else:
                assert "menu-Desk" in failures
                print("RECOVERY: use New Note keyboard command after the recorded menu failure.")
                page.keyboard.press("Meta+n")
            editor = page.locator(".desk-editor-window")
            _loaded(editor.get_by_role("button", name="Save", exact=True))
            # This new note has no earlier autosave. The editor's own Kept
            # receipt must appear for this edit, not elsewhere on the desk.
            receipt = editor.get_by_role("status").filter(has_text=re.compile(r"^Kept · "))
            assert receipt.count() == 0, "New note already has a Kept receipt before typing"
            editor_id = editor.get_attribute("id")
            assert editor_id and editor_id.startswith("editor:note:")
            with page.expect_response(lambda response: "/api/notes/" in response.url
                                      and response.request.method == "PUT"
                                      and response.request.post_data_json.get("body_markdown") == NOTE_BODY) as persisted:
                editor.get_by_role("textbox", name="Title", exact=True).fill(NOTE_TITLE)
                editor.locator(".cm-content").fill(NOTE_BODY)
            assert persisted.value.ok, persisted.value.text()
            notes = _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
            created = [n for n in notes if n["id"] not in before_notes and n["title"] == NOTE_TITLE]
            assert len(created) == 1 and created[0]["body_markdown"] == NOTE_BODY, {"before": before_notes, "notes": notes}
            note_id = created[0]["id"]
            # The ruled editor autosaves; Save only closes it. Require the
            # fresh keep on glass before the close removes its status node.
            observe("save-confirmation", """id => [...(document.getElementById(id)
              ?.querySelectorAll('[role=status]') || [])]
              .some(e => visible(e) && /^Kept · /.test(e.textContent))""",
                    "The edit has a new visible Kept receipt in its editor before Save",
                    arg=editor_id)
            shot("editor-kept-before-save")
            editor.get_by_role("button", name="Save", exact=True).click()
            editor.wait_for(state="detached")
            saved = _api(page, "GET", "/api/notes/" + note_id, token=TOKEN)["note"]
            assert saved["title"] == NOTE_TITLE and saved["body_markdown"] == NOTE_BODY

            # Job 2: actual file import, transcript, planned host, admitted run.
            _desk(page, base)
            _meetings(page, recovery=not meetings_ok)
            page.locator(".meetings-head-verbs").get_by_role("button", name="Import", exact=True).click()
            page.locator(".surface-dropwell input[type=file]").set_input_files(str(WAV))
            page.get_by_role("textbox", name="Title", exact=True).fill(MEETING_TITLE)
            with page.expect_response(lambda response: "/api/meetings/import" in response.url
                                      and response.request.method == "POST") as imported:
                page.locator(".surface-actions").get_by_role("button", name="Import", exact=True).click()
            assert imported.value.ok, imported.value.text()
            row = page.locator("[data-testid^='meeting-row-']").filter(has_text=MEETING_TITLE)
            _loaded(row)
            meeting_id = row.get_attribute("data-testid").removeprefix("meeting-row-")
            # Hold the fixture until the importing row is on glass. This fixes
            # the order without sleeping or depending on transcription speed.
            permit_import.set()
            assert import_done.wait(10), "Fixture import did not complete"
            assert db.meetings.get_meeting(meeting_id).segments, "Import saved no transcript"
            row.locator(".meetings-stream-row-body").click()
            _loaded(page.locator(".meetings-detail-head"))
            page.get_by_text(WORDS, exact=True).wait_for()
            detail = _api(page, "GET", "/api/meetings/" + meeting_id, token=TOKEN)
            planned = detail["planned_route"]
            assert planned["status"] == "ready" and detail.get("run_receipt") is None
            assert db.intel.get_latest_intel_job(meeting_id) is None and not engine.analyzed
            host = planned["legs"][0]["host"]
            assert len(planned["legs"]) == 1 and host == "127.0.0.1", planned
            assert planned["legs"][0]["profile_id"] == provider["profile_id"]
            assert planned["legs"][0]["profile_revision"] == provider["profile_revision"]
            print("PLANNED", host, planned["selection_hash"])
            imported_ready = observe("import-refresh", """() => {
              const verb=document.querySelector('[data-testid=detail-run-intelligence-btn]');
              return visible(verb);
            }""", "The imported transcript exposes Run summary without a reload")
            if not imported_ready:
                print("RECOVERY: reopen the imported meeting after the recorded import refresh failure.")
                _desk(page, base)
                _meetings(page, recovery=not meetings_ok)
                page.get_by_test_id("meeting-row-" + meeting_id).locator(".meetings-stream-row-body").click()
            route = _loaded(page.get_by_test_id("detail-route"))
            assert _chip_label(host) in route.inner_text()
            run = page.get_by_test_id("detail-run-intelligence-btn")
            assert _hit(run), "Run summary must be reachable on the loaded record"
            route_box, verb_box = route.bounding_box(), run.bounding_box()
            assert route_box and verb_box and abs(route_box["y"] - verb_box["y"]) < 100
            shot("planned-host")
            with page.expect_response(lambda response: response.url.endswith("/intelligence/run")
                                      and response.request.method == "POST") as admitted:
                run.click()
            assert admitted.value.ok, admitted.value.text()
            assert admitted.value.request.post_data_json["expected_selection_hash"] == planned["selection_hash"]
            assert process_next_intel_job(on_meeting_ready=_on_meeting_ready), "The requested summary did not enter the real queue"
            saved = db.meetings.get_meeting(meeting_id)
            assert saved.intel and saved.intel.summary == engine.result.summary and engine.analyzed
            receipt = _api(page, "GET", "/api/meetings/" + meeting_id + "/intel-recovery",
                           token=TOKEN)["run_receipt"]
            assert receipt["outcome"] == "succeeded"
            assert receipt["selection_hash"] == planned["selection_hash"]
            assert receipt["attempts"] and receipt["attempts"][0]["host"] == host
            print("RECEIPT", receipt["outcome"], receipt["selection_hash"], receipt["attempts"][0]["host"])
            refreshed = observe("record-refresh", """([summary, host]) => {
              const text=document.querySelector('[data-testid=meeting-summary-text]');
              const attempts=document.querySelector('[data-testid=summary-record-attempts]');
              return visible(text) && text.textContent.trim()===summary &&
                visible(attempts) && attempts.textContent.includes(host);
            }""", "The open record shows the completed summary and actual host without a reload",
                [engine.result.summary, _chip_label(host)])
            # A stale/missing result is expected today; a visible lie is not.
            summary_on_screen = page.get_by_test_id("meeting-summary-text")
            if summary_on_screen.is_visible():
                expect(summary_on_screen).to_have_text(engine.result.summary)
            attempts_on_screen = page.get_by_test_id("summary-record-attempts")
            if attempts_on_screen.is_visible():
                expect(attempts_on_screen.get_by_text(_chip_label(host), exact=True)).to_be_visible()
            if not refreshed:
                print("RECOVERY: reopen the persisted meeting after the recorded refresh failure.")
                _desk(page, base)
                _meetings(page, recovery=not meetings_ok)
                page.get_by_test_id("meeting-row-" + meeting_id).locator(".meetings-stream-row-body").click()
            expect(page.get_by_test_id("meeting-summary-text")).to_have_text(engine.result.summary)
            assert _chip_label(host) in _loaded(page.get_by_test_id("summary-record-attempts")).inner_text()
            print("PASS: the persisted summary and run receipt agree with the planned host")
            shot("summary-reopened")

            # Generic Notes query: log the selected identity, then execute that row.
            _desk(page, base)
            shelf, field = _search(page, "Notes", keyboard=True)
            active_id = field.get_attribute("aria-activedescendant")
            selected = _loaded(shelf.locator('[id="' + active_id + '"]'))
            selected_text = selected.inner_text()
            selected_label = selected.locator(".desk-deck-label").inner_text().strip()
            note_match = "option-note:" in active_id or selected_label in {"Notes", "Desk memory"}
            print("Notes query highlighted:", selected_text.replace("\n", " / "))
            field.press("Enter")
            shelf.wait_for(state="detached")
            if "option-note:" in active_id:
                selected_note_id = active_id.split("option-note:", 1)[1]
                selected_note = _api(page, "GET", "/api/notes/" + selected_note_id, token=TOKEN)["note"]
                assert selected_note["body_markdown"], "The Notes query selected an empty fixture"
                destination = page.get_by_role("region", name=selected_note["title"], exact=True)
                _loaded(destination.get_by_text(selected_note["body_markdown"], exact=True))
            elif note_match:
                destination = page.get_by_role("region", name=re.compile(r"^(Notes|Desk memory)$"))
                _loaded(destination.get_by_text(NOTE_TITLE, exact=True))
            else:
                # Current fixture deterministically opens Change places. Its grid
                # is the content marker; a loading window cannot certify this defect.
                _loaded(page.locator(".prefs-wallpaper-grid"))
            check("notes-query", note_match, "Typing Notes and Enter reaches notes")

            # Job 4: a new hub and new tab, same HOME/DB; no remembered open subject.
            page.close()
            server.stop()
            server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.set_default_timeout(10_000)
            page.emulate_media(reduced_motion="reduce")
            page.goto(base + "/?token=" + TOKEN)
            _normal_chair(page)
            _loaded(page.get_by_test_id("arrival-display"))
            _refind_note(page, note_id)
            shot("note-after-restart")
            _desk(page, base)
            # Search is a visible pointer door, then Enter opens the saved meeting.
            shelf, field = _search(page, MEETING_TITLE)
            target = shelf.locator('[id="desk-palette-option-meeting:' + meeting_id + '"]')
            _loaded(target)
            expect(field).to_have_attribute("aria-activedescendant", target.get_attribute("id"))
            field.press("Enter")
            meeting = page.get_by_role("region", name=MEETING_TITLE, exact=True)
            _loaded(meeting.get_by_text(engine.result.summary, exact=True))
            restarted = _api(page, "GET", "/api/meetings/" + meeting_id, token=TOKEN)
            assert restarted["run_receipt"] == receipt
            print("PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub")
            shot("meeting-after-restart")
            browser.close()

        if os.environ.get("HS202_EXPECTED_FAILURES") == "1":
            assert failures == KNOWN[width], (
                f"{width}: unexpected defects {sorted(failures-KNOWN[width])}; "
                f"healed/unexercised expected defects {sorted(KNOWN[width]-failures)}"
            )
            print("VERIFIED exact expected failures:", width, sorted(failures))
        else:
            assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
    finally:
        permit_import.set()
        server.stop()
        stub.shutdown()
        stub.server_close()
