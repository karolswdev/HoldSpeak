"""Room binding refusals stay in the window and can be read again, at both sizes."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_room_os_grammar_glass import _verb, _view

TOKEN = "room-binding-glass"
OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/room14"


@pytest.mark.parametrize("width", (1440, 393))
def test_room_refusals_keep_the_saved_object_and_offer_read_again(tmp_path, monkeypatch, width):
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState
    from holdspeak.timestamps import utc_now
    from tests.integration.test_desk_project_room import FakeLLM, _define_route

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    model = FakeLLM()
    try:
        _define_route(tmp_path / "home", model.endpoint, "binding-local-fixture")
        OUT.mkdir(parents=True, exist_ok=True)
        db = get_database()
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(15000)
            page.goto(f"{base}/?token={TOKEN}")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            for operation in ("confirm", "dismiss", "retire", "answer", "accept", "discard"):
                pid = _api(page, "POST", "/api/projects", {"name": f"Room {operation}"}, token=TOKEN)["project"]["id"]
                obj = operation
                if operation in ("confirm", "dismiss"):
                    mid = f"meeting-{operation}"
                    db.meetings.save_meeting(MeetingState(id=mid, title="Planning", started_at=utc_now(), segments=[]))
                    obj = db.proposals.create_proposal(meeting_id=mid, project_id=pid, kind="decision", text="Approve the replica plan", source_plugin="decision_capture").id
                    path = f"/api/proposals/{obj}/{operation}"
                elif operation == "retire":
                    from tests.watch_seed import seed_watch
                    seed_watch(db, watch_id=obj, connector_id="gh", query_kind="pull_requests", name="Source", query={"repository": "acme/app"})
                    db.automations.update_watch_spec(obj, project_id=pid, state="active", schema_version="WatchSpec@1")
                    path = f"/api/watches/{obj}/retire"
                elif operation in ("answer", "accept"):
                    rid = f"review-{operation}"
                    db.project_observations.insert_review(review_id=rid, project_id=pid, status="open", opened_at="2026-11-11T12:00:00+00:00")
                    db.project_observations.insert_proposal(proposal_id=obj, project_id=pid, review_window_key=rid, proposal_kind="review_flag", title="Check the saved plan", target_ref=f"project:{pid}")
                    suffix = "accept" if operation == "accept" else f"proposals/{obj}/decide"
                    path = f"/api/projects/{pid}/reviews/{rid}/{suffix}"
                else:
                    path = ""
                clear_hub_windows_http(base, TOKEN)
                _api(page, "POST", "/api/desk/windows/surface-project-memory/open", {"object_ref": f"project:{pid}"}, token=TOKEN)
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win = page.locator("#surface-project-memory")
                expect(win.get_by_role("tab", name="Open", exact=True)).to_be_visible()
                if operation == "retire":
                    win.get_by_role("tab", name="Sources", exact=True).click()
                    win.get_by_role("row", name="acme/app", exact=False).click()
                elif operation in ("answer", "accept"):
                    _view(page, win, "Review")
                    expect(win.get_by_role("grid", name="Review", exact=True)).to_be_visible()
                elif operation == "discard":
                    # Only this preparatory inference edge is substituted;
                    # the saved brief and its discard use the real services.
                    def deterministic(route):
                        body = route.request.post_data_json
                        body["generator"] = "deterministic"
                        response = route.fetch(post_data=json.dumps(body))
                        route.fulfill(response=response)
                    prepare_path = f"**/api/projects/{pid}/briefs/prepare"
                    page.route(prepare_path, deterministic)
                    _view(page, win, "Prepare")
                    win.get_by_role("textbox", name="Purpose", exact=True).fill("Read the saved plan")
                    with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/briefs/prepare")) as prepared:
                        _verb(page, win, "Prepare")
                    brief = prepared.value.json()["brief"]
                    obj, path = brief["id"], f"/api/briefs/{brief['id']}/discard"
                    page.unroute(prepare_path)
                else:
                    win.get_by_role("row", name="Approve the replica plan", exact=False).click()
                writes = []
                def race(route):
                    writes.append(route.request.post_data_json)
                    if operation in ("confirm", "dismiss"):
                        db.proposals.edit_proposal(obj, text="A new saved plan")
                    elif operation == "retire":
                        db.automations.update_watch_spec(obj, intent="A new saved source")
                    elif operation in ("answer", "accept"):
                        with db._connection() as conn:
                            conn.execute("UPDATE project_proposals SET patch_json=? WHERE id=?", ('{"title":"A new saved plan"}', obj))
                    else:
                        with db._connection() as conn:
                            conn.execute("UPDATE project_briefs SET body_md=? WHERE id=?", ("A new saved brief", obj))
                    route.continue_()
                page.route("**" + path, race)
                word = {"confirm": "Confirm", "dismiss": "Dismiss", "retire": "Remove", "answer": "Accept", "accept": "Finish review", "discard": "Discard"}[operation]
                _verb(page, win, word)
                if operation in ("dismiss", "retire", "discard"):
                    expect(win.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                    win.get_by_role("button", name=word, exact=True).last.click()
                expect(win.get_by_role("alert").filter(has_text="Nothing changed").first).to_be_visible()
                expect(win.get_by_role("button", name="Cancel", exact=True)).to_have_count(0)
                expected_id = rid if operation == "accept" else obj
                assert writes and writes[0]["binding"]["id"] == expected_id
                assert writes[0]["binding"]["revision"]
                if operation in ("confirm", "dismiss"):
                    assert db.proposals.get_proposal(obj).state == "proposed"
                elif operation == "retire":
                    assert db.automations.get_watch(obj)["state"] == "active"
                elif operation in ("answer", "accept"):
                    assert db.project_observations.get_proposal(obj)["lifecycle"] == "open"
                suffix = "900" if width == 1440 else "393"
                _settle(page)
                for facts in win.locator(".surface-inspector-facts").all():
                    assert "project:proj-" not in facts.inner_text()
                    assert "CLEAR" not in facts.inner_text()
                if operation == "retire":
                    expect(win.locator('.kit-statusbar')).to_contain_text("1 source")
                    expect(win.locator('.kit-statusbar')).not_to_contain_text("1 sources")
                if operation == "discard":
                    expect(win.get_by_role("combobox", name="View", exact=True)).to_have_value("brief")
                    expect(win.locator('.surface-object-reader')).to_contain_text("Draft")
                    expect(win.locator('.surface-object-reader')).not_to_contain_text("draft")
                for notice in win.locator(".surface-action-notice[role=alert]").all():
                    assert notice.evaluate("""e => {
                      const inspector = e.closest('.surface-pane-inspector,.surface-object-reader');
                      const rows = inspector ? [...inspector.querySelectorAll('.gadget-row')] : [];
                      const last = rows.at(-1);
                      return !last || e.getBoundingClientRect().top - last.getBoundingClientRect().bottom < 64;
                    }"""), "The refusal must follow the facts"
                page.screenshot(path=str(OUT / f"10-{operation}-refused-{os.environ.get('ROOM_SHOT_PHASE', 'after')}-{suffix}.png"))
                _verb(page, win, "Read again")
                expect(win.get_by_role("alert").filter(has_text="Nothing changed")).to_have_count(0)
                assert len(writes) == 1
                page.unroute("**" + path)
            browser.close()
    finally:
        model.stop()
        server.stop()
