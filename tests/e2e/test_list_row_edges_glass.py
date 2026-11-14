"""The shared list settles on complete rows, under its real sticky headings."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_agents_os_grammar_glass import _seed_fleet

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("LIST_EDGE_OUT", str(ROOT / ".tmp/evidence-shots/agents14r3")))
TOKEN = "list-row-edges"
PHASE = os.environ.get("LIST_EDGE_PHASE", "after")

MEASURE = """well => {
  const box=well.getBoundingClientRect(), top=box.top+well.clientTop, bottom=box.bottom;
  const heads=[...well.querySelectorAll('.object-list-group-label')].map(el=>el.getBoundingClientRect());
  const edge=Math.max(top,...heads.filter(r=>r.top<=top+1&&r.bottom>top).map(r=>r.bottom));
  const rows=[...well.querySelectorAll('[data-object-id]')].map(el=>({id:el.dataset.objectId,selected:el.getAttribute('aria-selected')==='true',...el.getBoundingClientRect().toJSON()}));
  const visible=rows.filter(r=>r.bottom>edge+.1&&r.top<bottom-.1);
  return {top,edge,bottom,scroll:well.scrollTop,max:well.scrollHeight-well.clientHeight,
    first:visible[0],last:visible.at(-1),visible,rows,border:parseFloat(getComputedStyle(well).borderBottomWidth)||0, padding:getComputedStyle(well).scrollPaddingTop};
}"""


def _list_face(win, well):
    if not well.is_visible():
        win.get_by_role("button", name="Back", exact=True).click()


def _measure(page, well, name, width, faults, *, selected=False):
    # The shared row fitter settles after scroll input. The sweep also
    # watches the settled pane for motion; this is the row geometry property.
    page.mouse.move(2, 2)
    _settle(page)
    page.wait_for_timeout(350)
    assert well.is_visible(), name
    state = well.evaluate(MEASURE)
    assert state["first"], (name, state)
    page.screenshot(path=str(OUT / f"{name}-{PHASE}-{900 if width == 1440 else 393}.png"))
    first = state["first"]
    if first and first["top"] < state["edge"] - 1:
        faults.append((name, "partial top row", state))
    fits = state["rows"][-1]["bottom"] - state["rows"][0]["top"] <= state["bottom"] - state["edge"] + 1
    if fits and any(row["top"] < state["edge"]-1 or row["bottom"] > state["bottom"]+1 for row in state["rows"]):
        faults.append((name, "a fitting list cuts a row", state))
    if selected:
        picked = next(row for row in state["rows"] if row["selected"])
        if picked["top"] < state["edge"]-1 or picked["bottom"] > state["bottom"]+1:
            faults.append((name, "selected row is not whole", state))
    return state


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.parametrize("face", ["agents", "people", "needs", "activity", "ask-sources"])
@pytest.mark.timeout(240)
def test_shared_list_row_edges_and_cross_app_shots(tmp_path, monkeypatch, width, face):
    from playwright.sync_api import sync_playwright, expect
    import holdspeak.agent_context as context
    from holdspeak.agent_context import event_log
    import holdspeak.delivery.factory_launch as launches
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.people import production_people_store
    from holdspeak.services.people_service import PeopleService
    from tests.integration.test_desk_agents_wire import _ag0_seed

    _ensure_build()
    OUT.mkdir(parents=True, exist_ok=True)
    state = tmp_path / "home/.holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(launches, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(context, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    faults = []
    try:
        _seed_fleet(tmp_path / "home")
        _ag0_seed(tmp_path / "home")
        db = get_database()
        names = [f"web/src/desk/surface/objects/ObjectList.tsx: Review task {i:02d} and keep the saved answer, rollback owner and recovery point in view before the platform architecture review on Friday."
                 if i % 2 == 0 else "`saved_answer_revision_" + "without_spaces_" * 10 + f"{i:02d}`" for i in range(50)]
        notes = []
        primitives = PrimitiveService(db)
        owner = Principal(PrincipalKind.OWNER, "row-edge-rig")
        for i, name in enumerate(names):
            db.activity.upsert_activity_record(source_browser="chrome", url=f"https://example.test/row-edge/{i}", title=name, last_seen_at=datetime.now(timezone.utc))
            db.proposals.create_proposal(meeting_id="agents14-long", project_id=None, kind="decision", text=name, source_plugin="summary")
            notes.append(primitives.create_note(owner, note_id=f"edge-note-{i}", title=name, body_markdown="Keep the recovery point."))
        # As in chair_rig: seed the real encrypted authority before a client
        # subscribes to live People reads. Each relationship is created once.
        store = production_people_store()
        store.initialize()
        people = PeopleService(store)
        for name in names:
            people.create_relationship(owner, {"display_name": name, "relationship_kind": "peer"})
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            if PHASE == "before":
                from .test_kit_polish_wave14_glass import _before
                monkeypatch.setenv("KIT14_BASELINE_BUILD", str(ROOT / ".tmp/agents-r3-held-built"))
                _before(page)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)

            def open_app(app):
                nonlocal page
                from .agents_lane_rig import _http
                from .test_kit_polish_wave14_glass import _before
                # Close the old client before changing the hub's window set.
                # No pending frame/close from one app can race the next one.
                page.close()
                clear_hub_windows_http(base, TOKEN)
                if app != "ask":
                    status, receipt = _http(base, "POST", f"/api/desk/windows/{app}/open", TOKEN, {})
                    assert status == 200, receipt
                    if width == 1440:
                        status, receipt = _http(base, "POST", f"/api/desk/windows/{app}/set_geometry", TOKEN,
                                               {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}})
                        assert status == 200, receipt
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                if PHASE == "before":
                    _before(page)
                if app == "ask":
                    page.route("**/api/ask/engine", lambda route: route.fulfill(json=tools["engine"]))
                    page.route("**/api/inference/assignments", lambda route: route.fulfill(json=tools["assignments"]))
                    page.route("**/api/ask", lambda route: route.fulfill(json=answer))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                if app == "ask":
                    page.keyboard.press("Control+KeyI")
                return page.locator(f'[id="{app}"]')

            if face == "agents":
                win = open_app("conductor")
                expect(win.locator(".surface-mast-facts")).to_contain_text("55 sessions", timeout=15000)
                well = win.get_by_test_id("agents-list").locator(".object-list-rows")
                # The one shared fitter handles grouped, two-line rows.
                target = well.locator('[data-object-id="launch:launch_ag0_done"]')
                target.click()
                _list_face(win, well)
                _measure(page, well, "agents-selected", width, faults, selected=True)
                target.press("ArrowUp")
                expect(well.locator('[aria-selected="true"]')).not_to_have_attribute("data-object-id", "launch:launch_ag0_done")
                _measure(page, well, "agents-keyboard", width, faults, selected=True)
                well.evaluate("el=>{el.scrollTop=183}")
                _measure(page, well, "agents-odd-scroll", width, faults)
                box = well.bounding_box()
                page.mouse.move(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
                page.mouse.wheel(0, 173)
                _measure(page, well, "agents-wheel", width, faults)
                well.evaluate("el=>{el.scrollTop=el.scrollHeight}")
                _measure(page, well, "agents-end", width, faults)

            for app, name, selector in [("surface-people", "people", '[data-testid="people-roster"] .object-list-rows'),
                                        ("chair:needs", "needs", '[data-testid="needs-list"] .object-list-rows'),
                                        ("surface-activity", "activity", '.object-list-rows')]:
                if face != name:
                    continue
                win = open_app(app)
                well = win.locator(selector).first
                try:
                    expect(well.locator('[data-object-id]').first).to_be_visible(timeout=15000)
                except AssertionError:
                    page.screenshot(path=str(ROOT / f".tmp/agents-r3-load-{name}-{PHASE}-{width}.png"))
                    print(win.inner_text()[:2000] if win.count() else f"{app} did not mount")
                    raise
                _measure(page, well, f"{name}-ready", width, faults)
                well.locator('[data-object-id]').last.click()
                _list_face(win, well)
                _measure(page, well, f"{name}-selected", width, faults, selected=True)
                well.evaluate("el=>{el.scrollTop=137}")
                _measure(page, well, f"{name}-odd-scroll", width, faults)
                if name == "people":
                    win.get_by_role("textbox", name="Find a person", exact=True).fill("Review task 00")
                    expect(well.locator('[data-object-id]')).to_have_count(1)
                    fitted = _measure(page, well, "people-fitting-list", width, faults)
                    assert fitted["rows"][-1]["bottom"] - fitted["rows"][0]["top"] <= fitted["bottom"] - fitted["edge"] + 1, fitted

            if face == "ask-sources":
                tools = json.loads((ROOT / "web/src/test/wire/ask.tools.wire.json").read_text())
                answer = {**tools["answer"], "looked_at": [{"ref": f"note:{note['id']}", "title": note["title"], "kind": "note"} for note in notes]}
                win = open_app("ask")
                editor = win.get_by_role("textbox", name="Ask about your work", exact=True)
                editor.fill("Read the recovery points")
                editor.press("Enter")
                well = win.get_by_test_id("ask-looked-at").locator(".object-list-rows")
                expect(well.locator('[data-object-id]')).to_have_count(len(notes))
                well.locator('[data-object-id]').last.click()
                _measure(page, well, "ask-sources-selected", width, faults, selected=True)
                well.evaluate("el=>{el.scrollTop=137}")
                _measure(page, well, "ask-sources-odd-scroll", width, faults)
                well.evaluate("el=>{el.scrollTop=el.scrollHeight}")
                end = _measure(page, well, "ask-sources-end", width, faults, selected=True)
                whole = [row for row in end["visible"] if row["top"] >= end["edge"]-.1 and row["bottom"] <= end["bottom"]+.1]
                gap = max(0, end["bottom"]-end["border"]-end["last"]["bottom"])
                top_gap = max(0, end["first"]["top"]-end["edge"])
                if len(whole) != 3 or len(end["visible"]) != 3 or gap > .1 or top_gap > .1 or end["last"]["id"] != end["rows"][-1]["id"]:
                    faults.append(("ask-sources-end", "Three whole source rows and no end gap", {"whole":len(whole),"gap_px":gap,"top_gap_px":top_gap,**end}))
                report = os.environ.get("LIST_EDGE_REPORT")
                if report:
                    folder = Path(report)
                    folder.mkdir(parents=True, exist_ok=True)
                    (folder/f"ask-sources-end-{900 if width==1440 else 393}.json").write_text(json.dumps({"whole":len(whole),"gap_px":gap,"top_gap_px":top_gap,**end}, indent=2))
            browser.close()
    finally:
        server.stop()
    assert not faults, faults
