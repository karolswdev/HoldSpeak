"""Selection grammar and every preference pane at the owner's window sizes."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _settle, clear_hub_windows_http
from .test_settings_page_glass import TOKEN, _open_page
from .test_desk_sweep import AIR_WORDS_JS, LIST_GRAMMAR_JS


@pytest.mark.timeout(240)
def test_settings_selection_grammar_and_pane_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _settings_pane_shots(tmp_path, monkeypatch)


@pytest.mark.timeout(240)
def test_settings_repair_pane_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _settings_pane_shots(tmp_path, monkeypatch, only=("accounts", "engines"))


def _settings_pane_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, only: tuple[str, ...] | None = None) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    root = Path(__file__).resolve().parents[2]
    fixtures = root / "web/src/desk/__tests__/fixtures"
    shots = root / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    reach_shots = root / ".tmp/evidence-shots/settings-diet-r3"
    reach_shots.mkdir(parents=True, exist_ok=True)
    chain = json.loads((root / "web/src/features/runson/__tests__/fixtures/settings-chain.recorded.json").read_text())
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                accounts = json.loads((fixtures / "connections-wire/connections-checked.json").read_text())
                for endpoint, recording in (
                    ("/api/connections", "connections-wire/connections-checked.json"),
                    ("/api/channels/destinations", "destinations-wire/list-two.json"),
                    ("/api/settings/hub", "settings-wire/hub.json"),
                ):
                    payload = json.loads((fixtures / recording).read_text())
                    payload = payload.get("wire", payload)
                    page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                    if endpoint == "/api/channels/destinations":
                        page.route(f"**{endpoint}?*", lambda route, _request, payload=payload: route.fulfill(json=payload))
                for tool in accounts["tools"]:
                    page.route(f"**/api/connections/{tool['provider_id']}/recheck", lambda route, _request, tool=tool: route.fulfill(json=tool))
                for endpoint, payload in chain["gets"].items():
                    page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                    if endpoint == "/api/channels/destinations":
                        page.route(f"**{endpoint}?*", lambda route, _request, payload=payload: route.fulfill(json=payload))
                engine_step = [chain["steps"][0]]
                held_editors: list[tuple[Any, str]] = []
                holding_engines = [bool(only)]
                def editor(route: Any) -> None:
                    scope = route.request.post_data_json.get("scope", {})
                    key = "default" if scope.get("kind") == "global" else "summaries" if scope.get("capability_id") == "meeting.deferred_analysis" else None
                    if key:
                        if holding_engines[0]:
                            held_editors.append((route, key))
                        else:
                            route.fulfill(json=engine_step[0]["editors"][key])
                    else:
                        route.continue_()
                page.route("**/api/inference/assignments/editor", editor)
                def set_chain(route: Any) -> None:
                    body = route.request.post_data_json
                    step = next(step for step in chain["steps"] if step.get("body") and step["body"]["expected_revision"] == body["expected_revision"] and step["body"]["entries"] == body["entries"])
                    engine_step[0] = step
                    route.fulfill(json=step["answer"])
                page.route("**/api/inference/assignments/set", set_chain)
                call_fixtures = root / "web/src/desk/calls/__fixtures__"
                for endpoint, recording in (
                    ("/api/calls/status", "line.calls.ready.json"),
                    ("/api/calls/line/status", "line.status.ready.json"),
                    ("/api/calls/line/nodes", "line.nodes.ready.json"),
                    ("/api/phone/status", "phone.settings.json"),
                    ("/api/phone/push", "phone.push.stored.json"),
                ):
                    payload = json.loads((call_fixtures / recording).read_text())
                    page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                for endpoint, recording in (("/api/settings/remote", "grant-remote-project-live.json"), ("/api/projects", "grant-projects.json")):
                    payload = json.loads((fixtures / "settings-wire" / recording).read_text())
                    page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                settings = json.loads((fixtures / "settings-wire/settings.json").read_text())
                settings["calls"] = {**json.loads((call_fixtures / "line.settings.json").read_text()), "phone_on": True, "phone_urgent_dnd": False}
                calendar = json.loads((fixtures / "settings-wire/calendar-sources-one.json").read_text())
                # Vary only identity fields of real recorded calendar sources.
                sources = [{**calendar["sources"][0], "id": f"feed-{i}", "label": name} for i, name in enumerate(("Home", "Woodward", "Work"))]
                calendar["sources"] = sources
                settings["calendar"]["sources"] = [{"id": source["id"], "label": source["label"], "url": f"eventkit:{source['id']}", "enabled": True} for source in sources]
                page.route("**/api/settings", lambda route: route.fulfill(json=settings) if route.request.method == "GET" else route.continue_())
                page.route("**/api/calendar/sources", lambda route: route.fulfill(json=calendar))
                _open_page(page, base)
                assert page.request.get(f"{base}/api/settings", headers={"authorization": f"Bearer {TOKEN}"}).json()["dictation"]["spoken_symbols"] == []
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-settings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                _settle(page)
                window = page.locator("#surface-settings")
                rail = window.get_by_role("navigation", name="Settings sections")
                panes = rail.locator("[data-rail-id]").evaluate_all("els => els.map(el => el.dataset.railId)")
                for pane in panes:
                    if only and pane not in only:
                        continue
                    if not rail.is_visible():
                        page.get_by_test_id("settings-back").click()
                    window.get_by_test_id(f"settings-index-{pane}").click()
                    section = window.locator(f"[data-settings-section='{pane}']")
                    section.wait_for(state="visible")
                    _settle(page)
                    lane_shots = root / ".tmp/evidence-shots/send-engines11"
                    lane_shots.mkdir(parents=True, exist_ok=True)
                    if pane == "engines" and only:
                        loading = section.get_by_role("combobox", name="Everything else engines", exact=True)
                        expect(loading.locator("option:checked")).to_have_text("Reading…")
                        loading_rows = section.locator("[data-testid^=settings-job-]").evaluate_all("els => els.map(el => el.getBoundingClientRect().height)")
                        fit = loading.evaluate("el => ({control:el.getBoundingClientRect().height,row:el.closest('[role=row]').getBoundingClientRect().height})")
                        page.screenshot(path=str(lane_shots / f"9-engines-reading-{900 if width == 1440 else 393}.png"))
                        assert fit["control"] <= fit["row"], fit
                        holding_engines[0] = False
                        for route, key in held_editors:
                            route.fulfill(json=engine_step[0]["editors"][key])
                        held_editors.clear()
                        expect(loading.locator("option:checked")).to_have_text("Codex, then Gemini CLI")
                        assert loading_rows == section.locator("[data-testid^=settings-job-]").evaluate_all("els => els.map(el => el.getBoundingClientRect().height)")
                    def shot(state: str) -> None:
                        # Settings' Meetings tabs must not overwrite Records shots.
                        if state.startswith("meetings-"):
                            state = f"settings-{state}"
                        _settle(page)
                        _bounded(window)
                        assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-settings")
                        if width == 1440 and pane in ("meetings", "speak", "notices", "calls", "this-mac"):
                            overflow = section.locator(".surface-preference-well:visible").evaluate_all("""els => els.filter(el => !el.closest('.surface-pane-inspector, .surface-list-pane-preview') && el.scrollHeight > el.clientHeight + 1).map(el => ({text:el.innerText, height:el.clientHeight, content:el.scrollHeight}))""")
                            assert not overflow, overflow
                        if pane in ("calls", "notices", "speak", "meetings", "this-mac"):
                            assert not section.evaluate(SETTINGS_GROUPS_JS)
                        if pane == "engines":
                            page.screenshot(path=str(lane_shots / f"8-10-{state}-{900 if width == 1440 else 393}.png"))
                        page.screenshot(path=str(shots / f"{state}-{'900x600' if width == 1440 else '393'}-after.png"))

                    def list_verb(label: str) -> None:
                        button = section.get_by_role("button", name=label, exact=True)
                        if button.is_visible():
                            button.click()
                        else:
                            section.get_by_role("button", name="Actions ▾", exact=True).click()
                            page.get_by_role("menu").last.get_by_role("menuitem", name=re.compile("^" + re.escape(label))).click()

                    def choose_tab(label: str) -> None:
                        target = section.get_by_role("tab", name=label, exact=True)
                        if target.count() and target.is_visible():
                            target.click()
                        else:
                            section.get_by_role("button", name=re.compile(" more$")).last.click()
                            page.get_by_role("menu").last.get_by_role("menuitem", name=label, exact=True).click()
                        _settle(page)

                    if pane == "accounts":
                        for tab in ("Services", "Calendars", "Send to"):
                            section.get_by_role("tab", name=tab, exact=True).click()
                            _settle(page)
                            _bounded(window)
                            if width == 1440:
                                assert all(row.bounding_box()["height"] >= 26 for row in section.locator("[role=row][data-object-id]:visible").all())
                            else:
                                assert all(row.bounding_box()["height"] >= 44 for row in section.locator("[role=row][data-object-id]:visible").all())
                            assert section.locator('[role="row"] button, .surface-ledger-row button, .surface-row button').count() == 0
                            suffix = {"Services": "services", "Calendars": "calendars", "Send to": "send-to"}[tab]
                            page.screenshot(path=str(shots / f"accounts-{suffix}-{'900x600' if width == 1440 else '393'}-after.png"))
                            if only and tab == "Calendars":
                                row = section.locator('[role=row][data-object-id]:visible').first
                                row.click()
                                row.press("Enter")
                                shot("calendars-inspector")
                                expect(row).to_be_visible()
                                assert row.bounding_box()["y"] < section.get_by_test_id("calendar-well").bounding_box()["y"]
                                section.get_by_role("region", name="Calendar", exact=True).get_by_role("button", name="Cancel", exact=True).click()
                                section.get_by_role("button", name="Remove calendar").click()
                                shot("calendars-remove")
                                section.get_by_role("button", name="Cancel", exact=True).click()
                                section.get_by_role("button", name="Add calendar").click()
                                shot("calendars-add-menu")
                                page.get_by_role("menuitem", name="Add feed", exact=True).click()
                                shot("calendars-add-feed")
                                section.get_by_role("button", name="Cancel", exact=True).click()
                                section.get_by_role("button", name="Add calendar").click()
                                page.get_by_role("menuitem", name="Mac calendars", exact=True).click()
                                shot("calendars-mac")
                                section.get_by_role("region", name="Mac calendars", exact=True).get_by_role("button", name="Done", exact=True).click()
                            if only and tab == "Send to":
                                row = section.locator('[data-testid=dest-row]').first
                                row.click()
                                list_verb("Open")
                                shot("send-to-details")
                                expect(section.locator(".surface-pane-inspector:has([data-testid=dest-open])").get_by_role("button", name="Done", exact=True)).to_have_count(0)
                                list_verb("Edit")
                                shot("send-to-edit")
                                shot("sendto-inspector")
                                expect(row).to_be_visible()
                                assert not page.evaluate(AIR_WORDS_JS, "#surface-settings")["air"]
                                save = section.get_by_test_id("dest-save")
                                save.scroll_into_view_if_needed()
                                shot("kit-sendto-actions")
                                expect(save).to_be_visible()
                                section.get_by_test_id("dest-cancel").click()
                                list_verb("Remove destination")
                                shot("send-to-remove")
                                section.get_by_role("button", name="Cancel", exact=True).click()
                                list_verb("Add destination")
                                shot("send-to-add")
                                assert not page.evaluate(AIR_WORDS_JS, "#surface-settings")["air"]
                                section.get_by_test_id("dest-cancel").click()
                                section.get_by_role("combobox", name="Destinations", exact=True).select_option("parked")
                                shot("send-to-parked")
                                section.get_by_role("combobox", name="Destinations", exact=True).select_option("active")

                        section.get_by_role("tab", name="Services", exact=True).click()
                        assert section.locator('[role="row"]').filter(has_text="Confluence").count() == 0
                        section.get_by_role("button", name="Add account", exact=True).click()
                        shot("services-add-menu")
                        page.get_by_role("menuitem", name="Confluence", exact=True).click()
                        shot("services-add-confluence")
                        section.get_by_role("region", name="Add Confluence account", exact=True).get_by_role("button", name="Cancel", exact=True).click()
                        row = section.get_by_text("GitHub", exact=True)
                        row.click()
                        expect(section.get_by_role("button", name="Sign in…", exact=True)).to_be_enabled()
                        row.click(button="right")
                        menu = page.get_by_role("menu", name="Services actions", exact=True)
                        expect(menu.get_by_role("menuitem", name="Sign in…", exact=False)).to_be_visible()
                        page.keyboard.press("Escape")
                        # The app menu receives the same selection verbs in the active window.
                        window.locator(".desk-window-title").click()
                        switcher = page.get_by_test_id("desk-screen-switcher")
                        if switcher.is_visible():
                            switcher.click()
                            page.get_by_role("menuitem", name="Settings", exact=True).click()
                            app_menu = page.get_by_role("menu").last
                        else:
                            head = page.get_by_test_id("desk-screen-title")
                            expect(head).to_have_attribute("data-app-window", "surface-settings")
                            head.get_by_role("button").click()
                            app_menu = page.get_by_role("menu", name="Settings menu", exact=True)
                        expect(app_menu.get_by_role("menuitem", name="Sign in…", exact=False)).to_be_visible()
                        expect(app_menu.get_by_role("menuitem", name="Show me", exact=True)).to_have_count(0)
                        page.keyboard.press("Escape")
                    else:
                        _bounded(window)
                        assert section.locator("h1, h2, .settings-mast, .settings-plate").count() == 0
                        assert section.locator('[role="row"] button, .surface-ledger-row button, .surface-row button').count() == 0
                        page.screenshot(path=str(shots / f"{pane}-{'900x600' if width == 1440 else '393'}-after.png"))
                        if pane == "engines":
                            _bounded(window)
                            if width == 1440:
                                assert all(row.bounding_box()["height"] >= 26 for row in section.locator("[role=row][data-object-id]:visible").all())
                            else:
                                assert all(row.bounding_box()["height"] >= 44 for row in section.locator("[role=row][data-object-id]:visible").all())
                            assert section.locator('[role="row"] button, .surface-ledger-row button, .surface-row button').count() == 0
                            expect(section.get_by_role("combobox", name="Everything else engines", exact=True).locator("option:checked")).to_have_text("Codex, then Gemini CLI")
                            if only:
                                shot("engines-jobs")
                                section.get_by_role("combobox", name="Everything else engines", exact=True).select_option("order")
                                shot("engines-order")
                                order = section.get_by_role("region", name="Everything else: engine order", exact=True)
                                order.get_by_text("Gemini CLI", exact=True).click()
                                order.get_by_role("button", name="Move up", exact=True).click()
                                expect(order.locator("[data-object-id]").first).to_contain_text("Gemini CLI")
                                shot("engines-moved")
                                order.get_by_role("button", name="Remove from order", exact=True).click()
                                question = section.get_by_role("region", name="Remove Gemini CLI from Everything else?", exact=True)
                                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_in_viewport(ratio=1)
                                expect(question.get_by_role("button", name="Remove", exact=True)).to_be_in_viewport(ratio=1)
                                shot("engines-remove-question")
                                question.get_by_role("button", name="Remove", exact=True).click()
                                expect(order.locator("[data-object-id]")).to_have_count(1)
                                order.get_by_role("button", name="Add engine", exact=True).click()
                                menu = page.get_by_role("menu", name="Engine order actions", exact=True)
                                expect(menu.get_by_role("menuitem", name="Gemini CLI", exact=True)).to_be_visible()
                                expect(menu.get_by_role("menuitem", name="Whisper mlx base", exact=True)).to_have_count(0)
                                shot("engines-add-menu")
                                box, button = menu.bounding_box(), order.get_by_role("button", name="Add engine", exact=True).bounding_box()
                                assert box["y"] >= button["y"] + button["height"] - 1, (box, button)
                                menu.get_by_role("menuitem", name="Gemini CLI", exact=True).click()
                                expect(order.locator("[data-object-id]")).to_have_count(2)
                                section.get_by_role("region", name="Everything else: engine order", exact=True).get_by_role("button", name="Done", exact=True).click()
                            section.get_by_role("tab", name="Engines", exact=True).click()
                            shot("engines-installed")
                            list_verb("Model library")
                            library = section.get_by_test_id("settings-engines-library")
                            for tab in ("Engines", "Speech", "Search"):
                                library.get_by_role("combobox", name="Model library category", exact=True).select_option(tab.lower())
                                _settle(page)
                                page.screenshot(path=str(lane_shots / f"10-engines-library-{tab.lower()}-{900 if width == 1440 else 393}.png"))
                                page.screenshot(path=str(shots / f"engines-library-{tab.lower()}-{'900x600' if width == 1440 else '393'}-after.png"))
                            if only:
                                library.get_by_role("combobox", name="Model library category", exact=True).select_option("engines")
                                library.get_by_role("button", name="Add an engine", exact=True).click()
                                expect(library.get_by_test_id("runson-kind-agent")).to_be_in_viewport(ratio=1)
                                shot("engines-add")
                                section.get_by_role("region", name="Add engine", exact=True).get_by_role("button", name="Done", exact=True).click()
                            section.get_by_role("region", name="Model library", exact=True).get_by_role("button", name="Done", exact=True).first.click()
                            if only:
                                for endpoint in ("/api/concierge/detect", "/api/inference/assignments"):
                                    page.route(f"**{endpoint}", lambda route: route.abort("connectionfailed"))
                                if not rail.is_visible():
                                    page.get_by_test_id("settings-back").click()
                                window.get_by_test_id("settings-index-accounts").click()
                                if not rail.is_visible():
                                    page.get_by_test_id("settings-back").click()
                                window.get_by_test_id("settings-index-engines").click()
                                expect(section.get_by_text("Engines not read", exact=True)).to_be_visible()
                                shot("engines-read-failed")
                                for endpoint, payload in chain["gets"].items():
                                    page.route(f"**{endpoint}", lambda route, payload=payload: route.fulfill(json=payload))
                    # One tab selector per pane, with a compact pop-up for long strips.
                    if pane not in ("accounts", "engines"):
                        tabs = section.get_by_role("tablist").all()
                        assert len(tabs) <= 1
                        compact = section.locator(".surface-tab-choice:visible select")
                        if compact.count():
                            choices = compact.locator("option").evaluate_all("els => els.map(el => ({id: el.value, label: el.textContent}))")
                            for choice in choices:
                                compact.select_option(choice["id"])
                                shot(f"{pane}-{choice['label'].lower().replace(' ', '-')}")
                        elif tabs:
                            for label in tabs[0].get_by_role("tab").all_text_contents():
                                tabs[0].get_by_role("tab", name=label, exact=True).click()
                                shot(f"{pane}-{label.lower().replace(' ', '-')}")
                        assert section.locator('[role="row"] button, .surface-ledger-row button, .surface-row button').count() == 0
                    if pane == "speak":
                        section.get_by_role("tab", name="Symbols", exact=True).click()
                        section.get_by_role("button", name="Add symbol", exact=True).click()
                        section.get_by_role("textbox", name="Spoken phrase 1").fill("right arrow")
                        page.screenshot(path=str(shots / f"speak-symbol-draft-{'900x600' if width == 1440 else '393'}-after.png"))
                        _bounded(window)
                        section.get_by_role("region", name="Spoken symbol", exact=True).get_by_role("button", name="Done").click()
                    if pane == "notices":
                        def reach_shot(state: str) -> None:
                            shot(state)
                            page.screenshot(path=str(reach_shots / f"{state}-{'900x600' if width == 1440 else '393'}-after.png"))

                        for urgent in (False, True):
                            settings["calls"]["phone_urgent_dnd"] = urgent
                            _open_page(page, base)
                            expect(rail).to_be_visible()
                            window.get_by_test_id("settings-index-notices").click()
                            choose_tab("When")
                            timing = section.get_by_role("region", name="When to reach you", exact=True)
                            label = timing.get_by_text("Urgent calls", exact=True)
                            if urgent:
                                expect(label).to_be_visible()
                                row = label.locator("xpath=..")
                                expect(row.get_by_text("Ring through Do Not Disturb", exact=True)).to_be_visible()
                                assert row.locator("input, select, button").count() == 0
                            else:
                                expect(label).to_have_count(0)
                            reach_shot("reach-when-urgent-" + str(urgent).lower())
                        choose_tab("Brief")
                        choices = section.get_by_role("grid", name="Brief choices")
                        expect(choices.get_by_role("row").first).to_have_attribute("aria-selected", "true")
                        expect(section.get_by_role("combobox", name="Digest", exact=True)).to_be_visible()
                        assert choices.get_by_role("columnheader").count() == 0
                        assert section.get_by_role("button", name="Open choice", exact=True).count() == 0
                        for label in ("Digest and Later", "Notices", "Morning brief", "Sweep and loops"):
                            row = choices.get_by_role("row").filter(has_text=label).first
                            row.click()
                            if label != "Sweep and loops":
                                form = section.get_by_role("region", name=label, exact=True)
                                expect(form).to_be_visible()
                                control = form.locator("input, select, textarea, button").filter(visible=True).first
                                row.press("Enter")
                                expect(control).to_be_focused()
                                row.dblclick()
                                expect(control).to_be_focused()
                            assert section.get_by_role("button", name="Done", exact=True).count() == 0
                            reach_shot("reach-" + label.lower().replace(" ", "-"))
                        assert section.get_by_role("tab").count() <= 4
                    if pane == "calls":
                        choose_tab("Phone")
                        expect(section.get_by_test_id("phone-device-row")).to_be_in_viewport()
                        pairing_payload = json.loads((call_fixtures / "phone.pair.json").read_text())
                        page.route("**/api/phone/pair", lambda route: route.fulfill(json=pairing_payload))
                        section.get_by_test_id("phone-pair").click()
                        shot("calls-phone-pair")
                        section.get_by_test_id("phone-pair-cancel").click()
                        choose_tab("Phone alerts")
                        bundle = section.get_by_test_id("phone-push-bundle")
                        field = bundle.get_by_role("textbox", name="App bundle ID", exact=True)
                        bundle_row = section.locator(".gadget-row").filter(has=page.get_by_test_id("phone-push-bundle"))
                        label = bundle_row.locator(".gadget-row-label")
                        assert field.bounding_box()["x"] > label.bounding_box()["x"]
                        assert bundle.get_by_role("button", name="Save", exact=True).bounding_box()["x"] >= bundle_row.locator(".gadget-row-gadget").bounding_box()["x"]
                        for key in ("phone-push-p8", "phone-push-key-id", "phone-push-team-id"):
                            section.get_by_test_id(key).dblclick()
                            shot("calls-" + key + "-edit")
                            section.get_by_role("button", name="Cancel", exact=True).click()
                        choose_tab("Numbers")
                        section.get_by_role("button", name="Add number", exact=True).click()
                        shot("calls-number-add")
                        section.get_by_role("button", name="Cancel", exact=True).click()
                        choose_tab("Line")
                        expect(section.get_by_test_id("line-test").locator(".gadget-row-label")).to_have_text(f"To{settings['calls']['allowed_numbers'][0]}")
                        expect(section.get_by_test_id("line-test-call")).to_have_text("Test call")
                        shot("calls-test-destination")
                        section.get_by_role("button", name="Add machine", exact=True).click()
                        shot("calls-machine-add")
                        section.get_by_role("button", name="Cancel", exact=True).click()
                        row = section.get_by_test_id("line-place").filter(has_text="karol")
                        row.click()
                        section.get_by_role("button", name="Revoke machine", exact=True).click()
                        shot("calls-machine-revoke")
                        expect(section.get_by_role("region", name="Revoke karol?", exact=True)).to_be_visible()
                        section.get_by_role("button", name="Cancel", exact=True).click()
                        choose_tab("Calls")
                        expect(section.get_by_role("checkbox", name="Calls on")).to_be_visible()
                        assert section.get_by_role("grid", name="Set up calls").count() == 0
                        section.get_by_role("button", name="Change passphrase", exact=True).click()
                        shot("calls-passphrase")
                        # Provisioning states use the same recorded provider answers as the app tests.
                        telnyx_payload: dict[str, Any] = {}
                        page.route("**/api/calls/line/telnyx/status", lambda route: route.fulfill(json=telnyx_payload))
                        numbers_payload = json.loads((call_fixtures / "line.telnyx.numbers.212.json").read_text())
                        page.route("**/api/calls/line/telnyx/numbers?area=212", lambda route: route.fulfill(json=numbers_payload))
                        for stage in ("noKey", "keySaved", "connected", "assigned"):
                            settings["calls"] = {**json.loads((call_fixtures / f"line.telnyx.settings.{stage}.json").read_text()), "phone_on": True}
                            telnyx_payload = json.loads((call_fixtures / f"line.telnyx.status.{stage}.json").read_text())
                            if not rail.is_visible():
                                page.get_by_test_id("settings-back").click()
                            window.get_by_test_id("settings-index-desk").click()
                            if not rail.is_visible():
                                page.get_by_test_id("settings-back").click()
                            window.get_by_test_id("settings-index-calls").click()
                            choose_tab("Line account")
                            shot(f"calls-account-{stage.lower()}")
                            choose_tab("Telnyx")
                            shot(f"calls-telnyx-{stage.lower()}")
                            if stage == "connected":
                                section.get_by_role("textbox", name="Area code", exact=True).fill("212")
                                section.get_by_test_id("telnyx-find").click()
                                expect(section.get_by_test_id("telnyx-number").first).to_be_visible()
                                shot("calls-telnyx-numbers")
                                section.get_by_test_id("telnyx-number").first.click()
                                section.get_by_role("button", name="Buy…", exact=True).click()
                                shot("calls-telnyx-buy-question")
                                expect(section.get_by_text("Buy +1 212 555 0100 for $1.00 a month and $1.00 upfront?", exact=True)).to_be_visible()
                                section.get_by_role("button", name="Cancel", exact=True).click()
                    if pane == "this-mac":
                        choose_tab("Details")
                        section.get_by_text("Device details", exact=True).click()
                        expect(section.get_by_test_id("runtime-backend")).to_be_in_viewport()
                        expect(section.get_by_test_id("runtime-path")).to_be_in_viewport()
                        shot("this-mac-device-details")
                        details = section.locator("details[open]")
                        assert details.locator("input, select, button").count() == 0

                        section.get_by_role("tab", name="Device", exact=True).click()
                        section.get_by_role("button", name="Reset desk to defaults…", exact=True).click()
                        shot("this-mac-reset")
                        section.get_by_role("region", name="Reset the desk?", exact=True).get_by_role("button", name="Cancel", exact=True).click()
                        section.get_by_role("tablist", name="This Mac", exact=True).get_by_role("tab", name="Access", exact=True).click()
                        section.get_by_text("sweep-runner", exact=True).click()
                        list_verb("Details…")
                        shot("access-details")
                        expect(section.get_by_role("region", name="sweep-runner", exact=True).get_by_role("button", name="Done", exact=True)).to_have_count(0)
                        list_verb("Projects…")
                        shot("access-projects")
                        section.get_by_role("region", name="sweep-runner: projects", exact=True).get_by_role("button", name="Done", exact=True).click()
                        list_verb("Issue credential")
                        section.get_by_role("textbox", name="Credential name", exact=True).fill("Review runner")
                        shot("access-issue")
                        section.get_by_role("region", name="Issue credential", exact=True).get_by_role("button", name="Cancel", exact=True).click()
                        section.get_by_role("tablist", name="This Mac", exact=True).get_by_role("tab", name="Keys", exact=True).click()
                        section.locator('[role="row"][data-object-id="web_token"]').dblclick()
                        shot("key-details")
                        key = section.get_by_role("region", name="Web pairing token", exact=True)
                        expect(key.get_by_role("textbox")).to_have_value("")
                        key.get_by_role("textbox").fill("Review draft")
                        shot("key-replace")
                        key.get_by_role("button", name="Cancel", exact=True).click()
                    assert rail.locator(".surface-spine").count() == 0
                    assert all(not node.inner_text() for node in rail.locator(".surface-rail-state").all())
                assert errors == [], errors
                page.close()
            browser.close()
    finally:
        server.stop()


def _bounded(window: Any) -> None:
    clipped_labels = window.locator(".gadget-row-label:visible").evaluate_all("""els=>els.filter(el=>el.clientWidth && el.scrollWidth > el.clientWidth+1).map(el=>({word:el.innerText,seat:el.clientWidth,needed:el.scrollWidth}))""")
    assert not clipped_labels, clipped_labels
    assert window.evaluate("""el => {
      const pane = el.querySelector('.pref-pane');
      const body = el.querySelector('.desk-surface-body');
      return pane.scrollHeight <= pane.clientHeight + 1 && body.scrollHeight <= body.clientHeight + 1
        && body.scrollWidth <= body.clientWidth + 1;
    }"""), window.bounding_box()

    assert window.evaluate("""el => [...el.querySelectorAll('.surface-list-pane-list')].every(seat => {
      const row = seat.querySelector('[data-object-id][aria-selected="true"]');
      const well = row?.closest('.object-list-rows');
      if (!row || !well) return true;
      const r = row.getBoundingClientRect(), w = well.getBoundingClientRect();
      return !r.width || !r.height || (r.top >= w.top - 1 && r.bottom <= w.bottom + 1);
    })"""), "The selected row must remain visible above its inspector"


# Read the rendered grammar, including composed rows, rather than component counts.
SETTINGS_GROUPS_JS = r"""section => {
  const visible = el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
  const failures = [];
  for (const group of section.querySelectorAll('.gadget-group, .surface-pane-group')) {
    if (!visible(group)) continue;
    const rows = [...group.querySelectorAll('.gadget-row, .object-list-row')]
      .filter(row => visible(row) && row.closest('.gadget-group, .surface-pane-group') === group);
    const heading = [...group.children].find(el => el.matches('h3, .gadget-group-label') && visible(el));
    if (rows.length === 1 && heading) failures.push(`One row repeats a group heading: ${heading.textContent}`);
  }
  if (section.matches('[data-settings-section="calls"]')) {
    const left = section.getBoundingClientRect().left;
    for (const row of section.querySelectorAll('.gadget-row')) {
      if (visible(row) && Math.abs(row.getBoundingClientRect().left - left) > 1)
        failures.push(`Calls row has a second left edge: ${row.textContent.trim().slice(0, 60)}`);
    }
  }
  for (const pane of section.querySelectorAll('.surface-list-pane')) {
    if (!visible(pane)) continue;
    const list = pane.querySelector('.surface-list-pane-list .object-list');
    const preview = pane.querySelector(':scope > .surface-list-pane-preview');
    if (!list || !preview) continue;
    const left = list.getBoundingClientRect().left;
    for (const el of preview.querySelectorAll('.gadget-row, .gadget-group-label, .surface-pane-group > h3, .surface-pane-inspector-head')) {
      if (visible(el) && Math.abs(el.getBoundingClientRect().left - left) > 1)
        failures.push(`Second left edge: ${el.textContent.trim().slice(0, 60)}`);
    }
  }
  return failures;
}"""
