"""Objects keep their kind; saved and live transcripts share measured seats."""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest
from . import open_rig, list_name_fit_rig
from .glass_infra import _api, _boot, _ensure_build, _settle
from .test_lists_wave14_glass import LONG_NAME, IDENTIFIER

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/evidence-shots/kit14/r5"
TOKEN = "kit-identity-transcript-r5"


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(600)
def test_object_identity_and_transcript_seat(tmp_path, monkeypatch, width):
    from playwright.sync_api import sync_playwright
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, IntelSnapshot, TranscriptSegment
    from holdspeak.calls.runner import CallRecord, Line
    import holdspeak.delivery.factory_launch as launches

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    monkeypatch.setattr(list_name_fit_rig, "TOKEN", TOKEN)
    monkeypatch.setattr(
        launches,
        "DEFAULT_LAUNCHES_PATH",
        tmp_path / "home/.holdspeak/agent_launches.json",
    )
    phase = os.environ.get("KIT_R5_PHASE", "after")
    OUT.mkdir(parents=True, exist_ok=True)
    failures, measures = [], {}

    def check(rule, ok, facts):
        if not ok:
            failures.append({"rule": rule, **facts})

    try:
        list_name_fit_rig.seed_names(tmp_path, base, monkeypatch)
        db = get_database()
        now = datetime.now(timezone.utc)
        words = "Keep the selected source, its saved words and the next architecture review in view. "
        db.meetings.save_meeting(
            MeetingState(
                id="identity-transcript",
                title=LONG_NAME,
                started_at=now - timedelta(hours=1),
                ended_at=now,
                segments=[
                    TranscriptSegment(
                        text=words * 3 + IDENTIFIER,
                        speaker="Architecture reviewer",
                        start_time=float(i * 7),
                        end_time=float(i * 7 + 5),
                    )
                    for i in range(50)
                ],
                intel=IntelSnapshot(
                    timestamp=1, summary="Read the saved architecture review."
                ),
                intel_status="completed",
            )
        )
        for i in range(50):
            db.projects.create_project(
                project_id=f"identity-project-{i}",
                name=LONG_NAME if not i else f"{IDENTIFIER}_{i}",
                description="Review the saved source.",
                keywords=[],
            )
            thread = db.threads.create_thread(
                title=LONG_NAME if not i else f"{IDENTIFIER}_{i}"
            )
            for role, text in [
                ("user", LONG_NAME),
                ("assistant", "Keep the recovery point until the review ends."),
            ]:
                message = db.threads.append_message(thread.id, role=role)
                db.threads.append_part(message.id, kind="text", text=text)
                db.threads.complete_message(message.id)
        db.threads.create_thread(title=LONG_NAME)
        from .test_agents_os_grammar_glass import _seed_fleet

        _seed_fleet(tmp_path / "home", count=50, examples=False)
        tape = json.loads(
            (ROOT / "web/src/desk/calls/__fixtures__/calls.face.json").read_text()
        )
        call = CallRecord(
            phone_call_id="kit-r5",
            id="kit-r5-call",
            direction="in",
            remote=tape["detail"]["remote"],
            state="ended",
            started_at=1794481200,
            answered_at=1794481201,
            ended_at=1794481552,
            outcome="done",
        )
        call.transcript = [
            Line(
                "caller" if i % 2 else "holdspeak",
                words * 3 + IDENTIFIER,
                call.started_at + i * 7,
            )
            for i in range(50)
        ]
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                reduced_motion="reduce",
            )
            page.set_default_timeout(20000)
            if phase == "before":
                from .test_kit_polish_wave14_glass import _before

                monkeypatch.setenv(
                    "KIT14_BASELINE_BUILD", str(ROOT / ".tmp/kit-r5-before-build")
                )
                _before(page)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")

            def shot(app):
                _settle(page)
                page.screenshot(
                    path=str(OUT / f"{app}-{900 if width == 1440 else 393}-{phase}.png")
                )

            def open_window(wid, ref=None, payload=None):
                return list_name_fit_rig.open_window(
                    page, base, wid, width, object_ref=ref, payload=payload
                )

            def identity(win, app, expected, inspector=True):
                if inspector:
                    win.locator(".surface-pane-inspector-head").last.wait_for()
                _settle(page)
                node = (
                    win.locator(
                        ".surface-pane-inspector-head .surface-inspector-object img"
                    ).last
                    if inspector
                    else win.locator(
                        ".object-list-row[aria-selected=true] .object-list-selection-name img"
                    ).first
                )
                value = (
                    node.evaluate(
                        "e=>({src:e.getAttribute('src'),box:e.getBoundingClientRect().toJSON(),loaded:e.complete&&e.naturalWidth>0,head:e.closest('.surface-pane-inspector-head,[role=row]').getBoundingClientRect().toJSON()})"
                    )
                    if node.count()
                    else {"missing": True}
                )
                measures[app] = value
                check(
                    1,
                    not value.get("missing")
                    and value["src"].endswith("/" + expected + ".png")
                    and value["loaded"]
                    and value["box"]["width"] > 0
                    and value["box"]["left"] >= value["head"]["left"] - 1
                    and value["box"]["right"] <= value["head"]["right"] + 1,
                    {"app": app, **value},
                )
                shot(app)

            def by_title(win, name):
                return (
                    win.locator(".object-list-row")
                    .filter(has=page.locator(f"[title={json.dumps(name)}]"))
                    .first
                )

            win = open_window("surface-projects")
            win.locator('[data-object-id="identity-project-0"]').click()
            identity(win, "projects-inspector", "project-drawer")
            win = open_window("surface-project-memory", "project:name-fit-room")
            win.get_by_test_id("room-body").wait_for()
            from .test_native_project_source_return_glass import _files

            _files(win).locator('[data-object-id="note:name-fit-0"]').click()
            identity(win, "room-inspector", "note")
            win = open_window("conductor")
            win.locator('[data-object-id="launch:launch_agents14_0"]').dblclick()
            identity(win, "agents-inspector", "agent-claude-code")
            win = open_window(
                "chair%3Aneeds", payload={"kind": "chair", "ref": "needs"}
            )
            win.get_by_role("grid", name="Needs you", exact=True).locator(
                "[data-object-id][data-kind=agent]"
            ).first.click()
            identity(win, "needs-inspector", "agent-claude-code")
            win = open_window("ask")
            if not win.get_by_role("grid", name="Recent", exact=True).is_visible():
                win.get_by_role("button", name="Recent", exact=True).click()
            by_title(win, LONG_NAME).click()
            identity(win, "ask-inspector", "thread", inspector=False)
            win = open_window("surface-meetings", "meeting:agents14-long")

            def meeting_view(label):
                button = win.get_by_role("tab", name=label, exact=True)
                if button.count() and button.is_visible():
                    button.click()
                else:
                    win.get_by_role(
                        "button", name="Meeting contents more", exact=True
                    ).click()
                    page.get_by_role("menuitem", name=label, exact=True).click()

            meeting_view("Commitments")
            grid = win.get_by_role("grid", name="Commitments", exact=True)
            grid.locator("[data-object-id]").first.click()
            identity(win, "meetings-inspector", "action-item")
            _api(
                page,
                "POST",
                "/api/decision-records/from-desk",
                {
                    "title": LONG_NAME,
                    "status": "proposed",
                    "why": "Keep the saved source.",
                },
                token=TOKEN,
            )
            win = open_window("surface-decisions")
            by_title(win, LONG_NAME).click()
            identity(win, "decisions-inspector", "decision")

            people = _api(page, "GET", "/api/people/relationships", token=TOKEN)[
                "relationships"
            ]
            priya = next(row for row in people if row["display_name"] == "Priya Nair")
            win = open_window("surface-people")
            win.locator(f'[data-object-id="{priya["id"]}"]').focus()
            page.keyboard.press("Enter")
            win = page.locator(f'[id="pullout:people:{priya["id"]}"]')
            win.get_by_test_id("people-composer").wait_for()
            if width == 1440:
                _api(
                    page,
                    "POST",
                    f"/api/desk/windows/pullout:people:{priya['id']}/set_geometry",
                    {
                        "rect": {
                            "x": "-1/2 + 100",
                            "y": "-1/2 + 80",
                            "w": "900px",
                            "h": "600px",
                        }
                    },
                    token=TOKEN,
                )
            win.get_by_role("button", name="Person view", exact=True).click()
            page.get_by_role("menu", name="Person view", exact=True).get_by_text(
                "1:1 brief", exact=True
            ).click()
            win.locator('[data-object-id="next"]').click()
            identity(win, "people-inspector", "meeting")

            def transcript(win, app):
                _settle(page)
                panel = win.locator(".transcript-list").first
                value = panel.evaluate(
                    """list=>{const line=list.querySelector('li'),p=line.querySelector('p'),speaker=line.querySelector('.transcript-speaker'),well=list.closest('.surface-transcript-well,.surface-preference-well'),w=well.getBoundingClientRect(),b=p.getBoundingClientRect(),s=speaker.getBoundingClientRect(),style=getComputedStyle(well);return {well:w.toJSON(),text:b.toJSON(),speaker:s.toJSON(),ownWidth:well.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight),clip:style.clipPath,scroll:well.scrollHeight,client:well.clientHeight};}"""
                )
                measures[app] = value
                narrow = value["ownWidth"] < 360
                check(
                    2,
                    not narrow
                    or value["text"]["top"] >= value["speaker"]["bottom"] - 1
                    and value["text"]["left"] <= value["speaker"]["left"] + 1
                    and value["text"]["width"] >= value["ownWidth"] - 20,
                    {"app": app, **value},
                )
                check(
                    2,
                    value["scroll"] > value["client"],
                    {"app": app, "needs-scroll": value},
                )
                shot(app)
                well = panel.locator(
                    "xpath=ancestor::*[contains(concat(' ',normalize-space(@class),' '),' surface-transcript-well ') or contains(concat(' ',normalize-space(@class),' '),' surface-preference-well ')][1]"
                )

                def whole_words():
                    return well.evaluate(
                        r"""well=>{const b=well.getBoundingClientRect(),parts=getComputedStyle(well).clipPath.match(/inset\(([^)]+)\)/)?.[1].split(' ').map(parseFloat),top=b.top+(parts?.[0]||0),bottom=b.bottom-(parts?.[2]||0),cut=[],walk=document.createTreeWalker(well,NodeFilter.SHOW_TEXT);for(let n=walk.nextNode();n;n=walk.nextNode()){if(!n.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(n);for(const r of range.getClientRects())if(r.bottom>top+.5&&r.top<bottom-.5&&(r.top<top-1||r.bottom>bottom+1))cut.push({text:n.textContent.slice(0,50),box:r.toJSON(),top,bottom});}return cut;}"""
                    )

                check(2, not whole_words(), {"app": app, "cut-at-rest": whole_words()})
                well.evaluate("e=>e.scrollTop+=e.clientHeight*.45")
                _settle(page)
                check(
                    2,
                    not whole_words(),
                    {"app": app, "cut-after-scroll": whole_words()},
                )

            win = open_window("surface-meetings", "meeting:identity-transcript")
            meeting_view("Transcript")
            transcript(win, "meeting-transcript")
            fixtures = ROOT / "web/src/desk/calls/__fixtures__"

            def recorded(name):
                return json.loads((fixtures / name).read_text())

            def calls(route):
                path = route.request.url.split("/api/calls", 1)[1].split("?", 1)[0]
                payload = (
                    {"calls": [call.summary()]}
                    if path == ""
                    else call.full()
                    if path == "/kit-r5-call"
                    else recorded("line.calls.ready.json")
                    if path == "/status"
                    else recorded("line.status.ready.json")
                    if path == "/line/status"
                    else recorded("line.nodes.none.json")
                    if path == "/line/nodes"
                    else None
                )
                route.fulfill(
                    json=payload
                ) if payload is not None else route.continue_()

            page.route("**/api/calls**", calls)
            page.route(
                "**/api/settings",
                lambda route: route.fulfill(
                    json={
                        "calls": {
                            **recorded("line.settings.json"),
                            "enabled": True,
                            "phone_on": True,
                        }
                    }
                ),
            )
            page.route(
                "**/api/phone/status",
                lambda route: route.fulfill(json=recorded("phone.settings.json")),
            )
            win = open_window("surface-calls")
            win.locator('[data-call="kit-r5-call"]').click()
            button = win.get_by_role("button", name="Open transcript", exact=True)
            if button.count() and button.is_visible():
                button.click()
            else:
                win.get_by_role("button", name="Actions ▾", exact=True).first.click()
                page.get_by_role(
                    "menuitem", name="Open transcript", exact=False
                ).click()
            win.get_by_test_id("calls-transcript").wait_for()
            transcript(win, "calls-transcript")
            browser.close()
    finally:
        (OUT.parent / f"r5-measures-{width}-{phase}.json").write_text(
            json.dumps({"measures": measures, "failures": failures}, indent=2)
        )
        server.stop()
    assert not failures, json.dumps(failures, indent=2)
