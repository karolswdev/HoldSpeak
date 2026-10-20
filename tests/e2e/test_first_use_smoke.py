"""The first use, end to end in a real browser: the smoke every PR runs
(scripts/glass_for.py SMOKE).

Was tests/e2e/test_hs202_first_use_smoke.py (renamed by the test diet,
push 2, 2026-10-12; the walk is unchanged).

HS-202-01: fixture first-use fence; normal RED, explicit verification GREEN.

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
from .engine_stub_rig import _StubHandler
from .concierge_rig import _quiet_concierge
from .meeting_rig import _FixtureImportTranscriber, _chip_label, _wait_record_host
from tests._evidence import evidence_dir
from .chair_windows import go_group, open_chair_window
from . import runs_on

TOKEN = "hs202-first-use"
WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"
WORDS = "The quick brown fox jumps over the lazy dog."
NOTE_TITLE = "Fence architecture note"
NOTE_BODY = "Review the service boundary with the team on Tuesday."
MEETING_TITLE = "Fence fixture meeting"
SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence")
# PHILO-15-03: every step passes at both widths once the gestures follow
# the A-1 screen (#939) and the A5 drawer (#935); nothing is expected red.
KNOWN = {1440: set(), 393: set()}
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


def _desk(page, base, *, capture=False):
    """Between jobs only: clear remembered windows, keeping all saved objects."""
    # PHILO-16 (16b): the hub remembers the windows; clear them there too.
    from .glass_infra import clear_hub_windows

    clear_hub_windows(page, TOKEN)
    page.evaluate("localStorage.removeItem('hs.desk.workspace.v1')")
    page.goto(base + "/?token=" + TOKEN)
    _normal_chair(page)
    # PHILO-14 A1 (#939): the Chair is the screen; its windows open on
    # demand: Window > Chair > Capture at 1440, the Dock's Speak at 393.
    _loaded(page.get_by_test_id("desk-screen"))
    if capture:
        if page.viewport_size["width"] > 720:
            # Betterment shell S0/S1 (#1257, #1259): Window > Desk shows only
            # while a window is open; Go > Needs you opens one first.
            page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
            page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").click()
            page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
            page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").click()
            page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Capture')").click()
        open_chair_window(page, "Capture")
        _loaded(page.get_by_test_id("arrival-capture-bar"))


def _needs(page):
    """The attention bell opens its own list at both widths."""
    drawer = page.locator(".needs-drawer")
    if not drawer.count() or not drawer.is_visible():
        bell = page.get_by_test_id("desk-bell")
        bell.wait_for()
        assert _hit(bell), "Needs you bell is unreachable"
        bell.click()
    return _loaded(page.locator(".needs-drawer [data-testid='arrival-display']"))


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
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
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
    # PHILO-17: "after every meeting" queues a summary at Import by itself.
    # Job 2's subject is the owner's Run press (the planned host beside the
    # verb, the admitted run, its receipt), so the setting is OFF here. The
    # automatic path has its own fences (tests/integration/test_desk_meetings.py,
    # test_hs201_summary_producer_chain).
    monkeypatch.setattr(
        "holdspeak.services.meeting_backlog_service._configured_auto_mode", lambda: "off"
    )
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    engine = _fixture_engine(monkeypatch, db)
    stub = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
    thread = threading.Thread(target=stub.serve_forever, daemon=True)
    thread.start()
    # Same-device routes intentionally have no passive egress badge. Use a
    # LAN-named fixture to preserve this walk's visible destination proof,
    # while its sole discovery socket still reaches the loopback stub.
    import holdspeak.setup_runtime as setup_runtime

    fixture_host = "192.168.77.43"
    fixture_endpoint = f"http://{fixture_host}:8080/v1"
    stub_endpoint = f"http://127.0.0.1:{stub.server_address[1]}/v1"
    discover_endpoint_models = setup_runtime.discover_endpoint_models
    endpoint_tool_support = setup_runtime.endpoint_tool_support

    def discover_fixture_endpoint(base_url, *args, **kwargs):
        assert str(base_url) == fixture_endpoint, base_url
        return discover_endpoint_models(stub_endpoint, *args, **kwargs)

    def check_fixture_tools(base_url, *args, **kwargs):
        assert str(base_url) == fixture_endpoint, base_url
        # Check reads /props and may POST a one-token tool probe after /models.
        # Keep all physical fixture traffic on loopback, with the real parser.
        return endpoint_tool_support(stub_endpoint, *args, **kwargs)

    monkeypatch.setattr(setup_runtime, "discover_endpoint_models", discover_fixture_endpoint)
    monkeypatch.setattr(setup_runtime, "endpoint_tool_support", check_fixture_tools)
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
            # PHILO-17 U17: /welcome opens the Get ready cards; the First
            # words card is the same production WebSocket path the parked
            # /welcome page used. Its button waits for speech on this device,
            # so the rig reports speech on device for this job only.
            import holdspeak.whisper_models as whisper_models

            real_readiness = whisper_models.speech_readiness
            whisper_models.speech_readiness = lambda name, backend, **k: {
                "model": str(name or "base"), "backend": str(backend or "auto"),
                "state": "on_device", "ready": True, "bytes": 0,
            }
            try:
                page.goto(base + "/welcome?token=" + TOKEN)
                words_card = page.get_by_test_id("setup-face")
                name = words_card.get_by_role("textbox", name="Your name", exact=True)
                name.fill("Fence owner")
                name.press("Tab")
                talk = _loaded(words_card.get_by_role("button", name="Say one sentence", exact=True))
                expect(talk).to_be_enabled(timeout=15_000)
                talk.scroll_into_view_if_needed()
                assert _hit(talk, fit=False), "First Words speech door is unreachable"
                talk.click()
                page.get_by_role("button", name="Stop listening", exact=True).wait_for()
                assert sockets, "Speech did not open its production WebSocket"
                if not frames:
                    sockets[0].wait_for_event("framesent", predicate=lambda data: isinstance(data, bytes), timeout=5000)
                page.get_by_role("button", name="Stop listening", exact=True).click()
                expect(words_card.get_by_text(WORDS)).to_be_visible()
                assert len(received) == 1 and frames
                with page.expect_response(lambda response: response.url.endswith("/api/notes")
                                          and response.request.method == "POST") as kept:
                    words_card.get_by_role("button", name="Keep as note", exact=True).click()
                assert kept.value.ok, kept.value.text()
                note = kept.value.json()["note"]
                assert db.notes.get(note["id"]).body_markdown == WORDS
                expect(words_card.get_by_role("button", name="Keep as note", exact=True)).to_have_count(0)
                expect(words_card.get_by_test_id("heard-quote").get_by_role("status", name="HEARD", exact=True)).to_be_visible()
            finally:
                whisper_models.speech_readiness = real_readiness
            shot("fixture-speech-kept")
            print("PASS: fixture speech became visible text and a kept note; PCM samples", received[0])

            # Job 5: one real UI setup gesture, with the LAN-named local fixture.
            _desk(page, base)
            # Betterment daily D8: "No engine for summaries" asks in Needs you
            # only when a meeting waits for a summary; this desk has none yet,
            # so the owner's door is HoldSpeak > Engines (both widths).
            mark = page.locator(".desk-mark")
            assert _hit(mark), "The HoldSpeak menu is unreachable"
            mark.click()
            page.locator(".desk-menu-list").first.wait_for()
            choose = page.locator("[role^=menuitem]").filter(
                has=page.locator(".desk-menu-label", has_text=re.compile(r"^Engines$"))).last
            _loaded(choose)
            assert _hit(choose)
            choose.click()
            # ST7: Engines is its own canonical window.
            models = page.locator("#surface-engines")
            models.wait_for()
            _loaded(models.get_by_test_id("concierge-add-engine"))
            page.get_by_test_id("concierge-add-engine").click()
            # Betterment E4: Add an engine unfolds into the kinds; the LAN
            # fixture is "A server on my network", which asks for its address.
            page.get_by_test_id("runson-kind-lan").click()
            address = page.locator("[data-testid='concierge-add-engine-row'] input").first
            endpoint = fixture_endpoint
            address.fill(endpoint)
            _loaded(page.get_by_test_id("concierge-add-egress"))
            assert fixture_host in page.get_by_test_id("concierge-add-egress").inner_text()
            setup_checks, endpoint_writes = [], []

            def record_setup_request(request):
                if request.method != "POST":
                    return
                if request.url.endswith("/api/setup/discover-models"):
                    setup_checks.append(request)
                elif request.url.endswith("/define-endpoint"):
                    endpoint_writes.append(request)

            page.on("request", record_setup_request)
            with page.expect_response(lambda response: response.url.endswith("/api/setup/discover-models")
                                      and response.request.method == "POST") as checked:
                page.get_by_test_id("concierge-add-check").click()
            assert checked.value.ok, checked.value.text()
            assert checked.value.json()["ok"] is True
            assert checked.value.json()["models"] == [_StubHandler.MODEL]
            assert len(setup_checks) == 1
            assert setup_checks[0].post_data_json == {"base_url": endpoint, "check_tools": True}
            expect(address).to_have_value(endpoint)
            # Betterment E3: Check fills the picker; he presses Use on the model.
            pick = page.locator(f"[data-testid='concierge-add-pick'][data-model='{_StubHandler.MODEL}']")
            expect(pick).to_be_visible()
            with page.expect_response(lambda response: response.url.endswith("/define-endpoint")
                                      and response.request.method == "POST") as defined:
                pick.get_by_test_id("concierge-add-use").click()
            assert defined.value.ok, defined.value.text()
            assert len(endpoint_writes) == 1
            assert defined.value.request.post_data_json["draft"]["endpoint"] == endpoint
            assert defined.value.request.post_data_json["draft"]["model"] == _StubHandler.MODEL
            page.remove_listener("request", record_setup_request)
            provider = defined.value.json()["provider"]
            assert provider["profile_id"] and provider["profile_revision"] > 0
            # Betterment E5: What runs where is the face (the drag switchboard
            # is parked behind Builder tools). One pick on Meeting summaries
            # sets the summaries. The window stays: the receipt is in its foot.
            what = models.get_by_test_id("runson-what")
            what.wait_for()
            pick_row = what.get_by_test_id("runson-what-pick-summaries")
            expect(pick_row).to_be_enabled()
            pick_row.click()
            option = what.get_by_test_id(f"runson-what-option-summaries-{provider['profile_id']}")
            with page.expect_response(lambda response: response.url.endswith("/api/inference/assignments/set")) as assigned:
                option.click()
            assert assigned.value.ok, assigned.value.text()
            assignment = assigned.value.request.post_data_json
            assert assignment["scope"] == {"kind": "capability", "capability_id": "meeting.deferred_analysis"}, assignment
            assert assignment["entries"][0]["profile_id"] == provider["profile_id"], assignment
            runs_on.wait_receipt(page, r"^SET ")
            assert runs_on.receipt(page).upper().startswith("SET "), runs_on.receipt(page)
            assert page.locator("[data-testid='runson-undo']").count() == 1
            # The hub has its summary engine: no setup row asks for one.
            assert not any(b.get("key") == "summary" for b in
                           _api(page, "GET", "/api/desk/needs-you", token=TOKEN).get("blockers", []))
            settings = page.locator("#surface-settings")
            back = settings.get_by_role("button", name="Back from Settings" if width < 720 else "Close Settings", exact=True)
            back.click()
            if width < 720:
                # Back leaves the scoped Models view before leaving Settings.
                settings.locator(".settings-home").wait_for()
                back.click()
            settings.wait_for(state="detached")
            _needs(page)
            print("PASS: engine setup completed visibly without a reload")
            shot("engine-set")

            # Persistent doors: real hit ownership, normal clicks, loaded destination.
            dock = page.locator(".desk-dock")
            doors = {}
            essential = (
                [("today", "Today", '[id="pullout:intelligence:desk"] [data-testid=today-day]'),
                 ("capture", "Capture", '[aria-label="Capture"] [data-testid=arrival-capture-bar]'),
                 ("meetings", "Meetings", ".meetings-head-verbs"),
                 ("people", "People", "#surface-people .desk-surface-body")]
                if width <= 720 else
                [("speak", "Speak", ".speak-face"),
                 ("meetings", "Meetings", ".meetings-head-verbs"),
                 ("today", "Today", '[id="pullout:intelligence:desk"] [data-testid=today-day]')]
            )
            for key, name, destination in essential:
                door = dock.get_by_role("button", name=name, exact=True)
                doors[key] = check("dock-" + key, _hit(door),
                                   name + " dock door fits and owns its hit target")
                if doors[key]:
                    door.click()
                    _loaded(page.locator(destination))
                    _desk(page, base)
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
                folded = page.locator(".desk-verbbar-menu[role=menu]")  # its name follows the open group at 393 (C5)
                _loaded(folded.get_by_role("menuitem").first)
                shot("folded-go-menu")

                def folded_item(key, label, message, *, ghosted=False):
                    # A hidden title is not a compact-width door. The content
                    # must be in Go and the row must own a hit after the
                    # menu's nearest scroll path has been used.
                    separate_title = page.locator(".desk-verbbar").get_by_role(
                        "button", name=key.removeprefix("menu-"), exact=True
                    )
                    # PHILO-13-17 (C7, Q3; ratified 2026-10-03): Go is grouped
                    # at 393, so each menu is one row of Go (Go ▸ Desk ▸ ...).
                    go_group(page, key.removeprefix("menu-"))
                    item = folded.get_by_role("menuitem").filter(has=page.locator(
                        ".desk-menu-label").filter(has_text=re.compile(
                            r"^" + re.escape(label) + r"(?:\s*·|$)")))
                    if item.count() != 1:
                        folded.locator(".desk-menu-back").click()
                        return check(key, False, message + " (missing from Go)")
                    try:
                        item.scroll_into_view_if_needed(timeout=2500)
                    except BrowserTimeout:
                        folded.locator(".desk-menu-back").click()
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
                    folded.locator(".desk-menu-back").click()
                    return passed

                # PHILO-15 11 (B21, owner ruling 2026-10-07): Go at 393 is the
                # Chair's windows, the Dock's places, the projects and New ▸
                # (Thought / Meeting / Project / Person). Desk ▸ Object ▸
                # Window ▸ are not on the phone; each window has its own menu.
                folded_item(
                    "menu-New", "Note",
                    "Note is visible and reachable at Go ▸ New",
                )
                page.keyboard.press("Escape")
            else:
                # Betterment shell S0 (#1257): with nothing selected the bar
                # reads Desk Go Window (no Object title), and Window with no
                # window open holds one line, "No windows open".
                bar = page.locator(".desk-verbbar")
                check("menu-Object",
                      bar.get_by_role("button", name="Object", exact=True, include_hidden=True).count() == 0,
                      "Object menu is not drawn with nothing selected")
                for name in ("Desk", "Go", "Window"):
                    title = bar.get_by_role("button", name=name, exact=True, include_hidden=True)
                    if not check("menu-" + name, _hit(title), name + " menu door is reachable"):
                        continue
                    title.click()
                    menu = page.get_by_role("menu", name=name + " menu", exact=True)
                    if name == "Window":
                        _loaded(menu.locator(".desk-menu-note").filter(has_text="No windows open"))
                    else:
                        _loaded(menu.get_by_role("menuitem").first)
                    print("PASS:", name, "menu content loaded")
                    page.keyboard.press("Escape")

            # The actual New Note command; no pre-seeded note can satisfy this
            # proof. Betterment Q8: the Capture door below opens the same
            # sticky as New Note, and New Note uses an empty note again, so
            # the count starts before both.
            before_notes = {note["id"] for note in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}

            # Job 3: the named door must lead to a place that keeps a thought.
            _desk(page, base, capture=True)
            thought = page.get_by_test_id("arrival-develop-thought")
            assert _hit(thought)
            thought.click()
            # Betterment C8: New note makes its record on the first character.
            page.get_by_test_id("arrival-new-note").locator("textarea").press("P")
            page.wait_for_function("""() => !!document.querySelector(
              '.speak-face textarea, [id^="editor:note:"] .cm-content, .thought-note-document [aria-label="Note body"]')""")
            note_editor = page.locator(
                '[id^="editor:note:"] .cm-content, .thought-note-document [aria-label="Note body"]')
            if note_editor.count() == 1:
                note_editor.wait_for(state="visible")
                assert note_editor.get_attribute("contenteditable") == "true"
            check("thought-door",
                  note_editor.count() == 1 and note_editor.is_visible(),
                  "New note opens a note authoring surface")
            _desk(page, base)

            desk_menu = page.locator(".desk-verbbar").get_by_role("button", name="Desk", exact=True, include_hidden=True)
            if width <= 720:
                # PHILO-15 11 (B21): New Note left the phone Go (New ▸ is four
                # kinds). At 393 New Note is one Search away: the Search tap,
                # the words, a tap on the row.
                search = page.locator("button[aria-controls=desk-tool-shelf]")
                search.wait_for()
                search.click()
                box = page.locator("input[aria-controls=desk-palette-listbox]")
                box.wait_for()
                box.fill("New Note")
                new_note = page.locator("[id='desk-palette-option-desk.new-note']")
                new_note.wait_for()
                assert _hit(new_note), "Search -> New Note is not reachable at 393"
                new_note.click()
            elif _hit(desk_menu):
                desk_menu.click()
                page.get_by_role("menuitem", name=re.compile(r"^New Note")).click()
            else:
                assert "menu-Desk" in failures
                print("RECOVERY: use New Note keyboard command after the recorded menu failure.")
                page.keyboard.press("Meta+n")
            # Betterment Q8 (one note): New Note opens the sticky, never the
            # form editor. Its first line names it (thoughtTitle.ts).
            editor = page.locator(".desk-window.thought-workspace-window")
            _loaded(editor.get_by_role("button", name="Done", exact=True))
            # New Note uses the empty note the Capture door made above again
            # (newThought.ts), so its window may already say when it was kept;
            # the save of THIS edit is proven by its PATCH below.
            editor_id = editor.get_attribute("id")
            assert editor_id and editor_id.startswith("pullout:note:")
            typed = f"{NOTE_TITLE}\n{NOTE_BODY}"
            with page.expect_response(lambda response: "/api/thoughts/" in response.url
                                      and response.url.endswith("/working")
                                      and response.request.method == "PATCH"
                                      and (response.request.post_data_json or {}).get("body_markdown") == typed) as persisted:
                editor.locator(".thought-note-body .cm-content").fill(typed)
            assert persisted.value.ok, persisted.value.text()
            notes = _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
            created = [n for n in notes if n["id"] not in before_notes and n["title"] == NOTE_TITLE]
            assert len(created) == 1 and created[0]["body_markdown"] == typed, {"before": before_notes, "notes": notes}
            note_id = created[0]["id"]
            # The editor autosaves; Done flushes and closes it. Require the
            # fresh keep on glass before the close removes its status node.
            observe("save-confirmation", """id => [...(document.getElementById(id)
              ?.querySelectorAll('[role=status]') || [])]
              .some(e => visible(e) && /^Saved /.test(e.textContent))""",
                    "The edit has a new visible Saved receipt in its editor before Done",
                    arg=editor_id)
            shot("editor-kept-before-save")
            editor.get_by_role("button", name="Done", exact=True).click()
            editor.wait_for(state="detached")
            saved = _api(page, "GET", "/api/notes/" + note_id, token=TOKEN)["note"]
            assert saved["title"] == NOTE_TITLE and saved["body_markdown"] == typed

            # Job 2: actual file import, transcript, planned host, admitted run.
            _desk(page, base)
            _meetings(page, recovery=not meetings_ok)
            # Capture C3 (#1271): Import opens the file picker at once; the
            # chosen file opens the import form.
            with page.expect_file_chooser() as chooser:
                page.locator(".meetings-head-verbs").get_by_role("button", name="Import", exact=True).click()
            chooser.value.set_files(str(WAV))
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
            assert len(planned["legs"]) == 1 and host == fixture_host, planned
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
            expect(route.locator(".gadget-chip-egress")).to_have_text(f"{host} · LAN")
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
            # PHILO-16 R2: this step reads the record's OWN state (the summary
            # and the attempts drawn in the open record), not the viewport. At
            # 393 the run's result lands under the Run button, inside the
            # record's scroll, and where the browser leaves the scroll after
            # the click varies run to run: measured failing at summary top
            # 907 px in an 852 px viewport, with the right text drawn 0.43 s
            # after the receipt. Freshness without a reload is the claim here;
            # `drawn` is `visible` without the viewport bounds.
            refreshed = observe("record-refresh", """([summary, host]) => {
              const drawn = el => {
                if (!el || !el.isConnected) return false;
                const r=el.getBoundingClientRect(), s=getComputedStyle(el);
                return r.width>0 && r.height>0 && s.visibility==='visible' &&
                  s.display!=='none' && Number(s.opacity)>0;
              };
              const text=document.querySelector('[data-testid=meeting-summary-text]');
              // PHILO-17 U16: the host is said ONCE: on the slab, or on the
              // window foot when the foot already names it.
              const win=text && (text.closest('.desk-surface-window') || document);
              const said=win ? ['[data-testid=summary-record-attempts]', '.surface-footer-egress']
                .map(sel => win.querySelector(sel)).filter(el => drawn(el) && el.textContent.includes(host)) : [];
              return drawn(text) && text.textContent.trim()===summary && said.length===1;
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
            _wait_record_host(page, _chip_label(host), scope=".desk-surface-window:has([data-testid=meeting-summary-text])")
            print("PASS: the persisted summary and run receipt agree with the planned host")
            # PHILO-16 R2 (Astra item 2): `drawn` proves layout; the owner must
            # SEE it. After the real-signal wait, the record is scrolled to the
            # attempts row and the summary, and both must sit in the viewport.
            # PHILO-17 U16: the host row is the slab's attempts, or (when the
            # foot names the host) the window foot.
            host_row = "summary-record-attempts" if page.get_by_test_id("summary-record-attempts").count() else None
            for test_id in (host_row, "meeting-summary-text"):
                if test_id:
                    page.get_by_test_id(test_id).scroll_into_view_if_needed()
            in_view = page.evaluate("""() => [document.querySelector('[data-testid=summary-record-attempts]') ? 'summary-record-attempts' : 'foot', 'meeting-summary-text'].map(id => {
              const el = id === 'foot'
                ? document.querySelector('.desk-surface-window:has([data-testid=meeting-summary-text]) .surface-footer-egress')
                : document.querySelector(`[data-testid=${id}]`);
              if (!el) return [id, false];
              const r=el.getBoundingClientRect();
              return [id, r.width>0 && r.height>0 && r.top>=0 && r.left>=0 &&
                r.bottom<=innerHeight && r.right<=innerWidth];
            })""")
            assert all(ok for _, ok in in_view), f"{width}: the run's result is not in view: {in_view}"
            shot("summary-reopened")

            # Generic Notes query: log the selected identity, then execute that row.
            _desk(page, base)
            shelf, field = _search(page, "Notes", keyboard=True)
            active_id = field.get_attribute("aria-activedescendant")
            selected = _loaded(shelf.locator('[id="' + active_id + '"]'))
            selected_text = selected.inner_text()
            selected_label = selected.locator(".desk-deck-label").inner_text().strip()
            note_match = "option-note:" in active_id or selected_label in {"Notes", "Memory"}
            print("Notes query highlighted:", selected_text.replace("\n", " / "))
            field.press("Enter")
            shelf.wait_for(state="detached")
            if "option-note:" in active_id:
                selected_note_id = active_id.split("option-note:", 1)[1]
                selected_note = _api(page, "GET", "/api/notes/" + selected_note_id, token=TOKEN)["note"]
                assert selected_note["body_markdown"], "The Notes query selected an empty fixture"
                destination = page.get_by_role("region", name=selected_note["title"], exact=True)
                # The sticky draws each line of the note as its own line.
                _loaded(destination.get_by_text(selected_note["body_markdown"].splitlines()[-1], exact=True))
            elif note_match:
                destination = page.get_by_role("region", name=re.compile(r"^(Notes|Memory)$"))
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
            _loaded(page.get_by_test_id("desk-screen"))
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
            # PHILO-17: the meeting's own window holds the whole record (its
            # Send well previews the same words); the summary is its slab.
            summary = _loaded(meeting.get_by_test_id("meeting-summary-text"))
            expect(summary).to_have_text(engine.result.summary)
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
