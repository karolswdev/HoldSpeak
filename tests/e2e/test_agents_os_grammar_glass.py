"""Agents selection, question, reading wells and forms on the real isolated hub."""
from pathlib import Path
import os
import copy
import shutil
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows, clear_hub_windows_http
from .conductor_rig import _seed

OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/agents14r2"
PHASE = "before" if os.environ.get("AGENTS14_R2_BEFORE") else "after"
TOKEN = "agents13"


def _seed_fleet(home: Path, count: int = 50, *, examples: bool = True) -> None:
    """Real producers, fifty more tasks, path-led names and unbroken identifiers."""
    from datetime import datetime, timedelta, timezone
    from holdspeak.db import get_database
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    if examples:
        _seed(home)
    now = datetime.now(timezone.utc)
    names = [
        (f"web/src/desk/conductor/AgentPane.tsx: Review task {i:02d} and keep the rollback owner, the saved answer, the failed write and its retry in the same window before the release on Friday.")
        if i % 2 == 0 else f"`agent_launch_answer_expected_pane_fingerprint_{i:02d}_" + "revision_" * 15 + "`"
        for i in range(count)
    ]
    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="agents14-long", title="Release review", started_at=now - timedelta(hours=1), ended_at=now,
        intel=IntelSnapshot(timestamp=1, topics=[], summary="Release review", action_items=[{
            "id": f"agents14-task-{i}", "task": name, "status": "pending", "review_state": "accepted",
            "created_at": now.isoformat(), "owner": None, "due": None, "source_timestamp": None,
        } for i, name in enumerate(names)]), intel_status="completed",
    ))
    ledger = LaunchLedger()
    with db._connection() as conn:
        items = [(name, str(conn.execute("SELECT id FROM action_items WHERE task=?", (name,)).fetchone()[0])) for name in names]
    for i, (name, item) in enumerate(items):
        attempt = db.work_attempts.create(
            source_id="src_ledger", worktree_id=f"wt_agents14_{i}", project="payments-ledger",
            story_id=f"action-{item}", node_id="this-node", session_id=None, target_id=f"tgt_agents14_{i}",
            kind="launch", exact=True, claimed_by="launch:claude-default", state="working", origin_ref=f"action:{item}",
        )
        ledger.record({
            "launch_schema": 1, "launch_id": f"launch_agents14_{i}", "state": "launched", "node_id": "this-node",
            "profile_id": "claude-default", "gate": "gated", "branch": f"hs/agents14-{i}",
            "session": f"hs-agents14-{i}", "origin_ref": {"kind": "action", "id": item},
            "attempt_id": attempt.attempt_id,
            "launched_at": now.isoformat(), "control_mode": "normal", "instruction_state": "sent", "brief_text": name,
        })


def _reference_build(page) -> None:
    if PHASE == "before":
        from .test_kit_polish_wave14_glass import _before
        snapshot = OUT.parents[1] / "agents14r2-baseline-build"
        if not (snapshot / "index.html").exists():
            shutil.copytree(OUT.parents[2] / "holdspeak/static/_built", snapshot, dirs_exist_ok=True)
        os.environ["KIT14_BASELINE_BUILD"] = str(snapshot)
        _before(page)


def _open_agents(page, base: str, width: int) -> None:
    # Wait for the hub's acknowledged window before sizing or reading it.
    clear_hub_windows(page, TOKEN)
    _api(page, "POST", "/api/desk/windows/conductor/open", {}, token=TOKEN)
    if width == 1440:
        _api(page, "POST", "/api/desk/windows/conductor/set_geometry",
             {"rect": {"x": "-1/2 + 240", "y": "-1/2 + 100", "w": "900px", "h": "600px"}}, token=TOKEN)
    page.goto(f"{base}/conductor?token={TOKEN}", wait_until="load")


def _whole_state_words(win) -> set[str]:
    measured=win.get_by_test_id("conductor-pill").evaluate_all("""els=>els.flatMap(el=>{
        const r=el.getBoundingClientRect(),well=el.closest('.object-list-rows'),box=well?.getBoundingClientRect();
        if(!box||!r.width||!r.height||r.bottom<=box.top||r.top>=box.bottom)return [];
        return [{id:el.closest('[data-object-id]').getAttribute('data-object-id'),word:el.textContent,
          fits:el.scrollWidth<=el.clientWidth+1&&[...el.querySelectorAll('span')].every(s=>s.scrollWidth<=s.clientWidth+1)}];
    })""")
    assert all(row["fits"] for row in measured), [row for row in measured if not row["fits"]]
    return {row["id"] for row in measured}


def _read_the_fleet(page, win) -> None:
    """Every state is whole when its row enters the viewport; no offscreen width fence."""
    well=win.get_by_test_id("agents-list").locator(".object-list-rows")
    expected=set(well.locator('[data-object-id]').evaluate_all("els=>els.map(el=>el.getAttribute('data-object-id'))"))
    well.evaluate("el=>{el.scrollTop=0}")
    _settle(page)
    seen=_whole_state_words(win)
    first=True
    while well.evaluate("el=>el.scrollTop+el.clientHeight<el.scrollHeight-1"):
        previous=well.evaluate("el=>el.scrollTop")
        well.evaluate("el=>{el.scrollTop+=Math.max(1,el.clientHeight*.75)}")
        _settle(page)
        if first:
            page.screenshot(path=str(OUT/f"scroll-55-{PHASE}-{900 if page.viewport_size['width']==1440 else 393}.png"))
            first=False
        assert well.evaluate("el=>el.scrollTop") > previous, "The list must keep the owner's scroll"
        seen |= _whole_state_words(win)
    assert expected <= seen, f"Rows not read: {expected-seen}"
    well.evaluate("el=>{el.scrollTop=0}")
    _settle(page)


def _press(win, verb: str, label: str) -> None:
    button = win.get_by_test_id(verb)
    if button.count() and button.is_visible():
        button.click()
    else:
        import re
        win.get_by_role("button", name=re.compile(r"^Actions")).click()
        win.page.get_by_role("menuitem", name=label, exact=True).click()

@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.parametrize("crowded", [True])
@pytest.mark.parametrize("pane", ["work", "records"])
@pytest.mark.timeout(240)
def test_agents_selection_and_inspector_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, crowded: bool, pane: str) -> None:
    from playwright.sync_api import sync_playwright, expect
    import holdspeak.agent_context as context
    from holdspeak.agent_context import event_log
    import holdspeak.delivery.factory_launch as launches
    state=tmp_path/"home/.holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(launches,"DEFAULT_LAUNCHES_PATH",state/"agent_launches.json")
    monkeypatch.setattr(context,"AGENT_CONTEXT_FILE",state/"agent_sessions.json")
    monkeypatch.setattr(event_log,"default_spool_dir",lambda:state/"agent-events")
    _ensure_build()
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        (_seed_fleet if crowded else _seed)(tmp_path/"home")
        from tests.integration.test_desk_agents_wire import _ag0_seed
        _ag0_seed(tmp_path/"home")
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            _reference_build(page)
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}",wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            _open_agents(page,base,width)
            win=page.locator("#conductor")
            expect(win.get_by_test_id("conductor-row").first).to_be_visible(timeout=15000 if crowded else 5000)
            if crowded:
                expect(win.locator(".surface-mast-facts")).to_contain_text("55 sessions")
            suffix=900 if width==1440 else 393
            def shot(name: str) -> None:
                _settle(page)
                assert win.evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                assert win.locator(".aw-plate,.surface-mast:not(.surface-mast--framed),.surface-rail").count()==0
                _whole_state_words(win)
                assert not win.locator(".surface-mast-facts").inner_text().endswith("this…")
                if PHASE == "after" and name in {"waiting", "answer-draft", "answer-refused"}:
                    answer = win.get_by_test_id("conductor-answer").bounding_box()
                    facts = win.get_by_test_id("conductor-ask-row").locator(".surface-inspector-facts").last.bounding_box()
                    assert answer and facts and 0 <= facts["y"] - answer["y"] - answer["height"] <= 20, (answer, facts)
                    expect(win.get_by_role("tab", name="Files", exact=True)).to_have_count(0)
                state_name = f"crowded-{name}" if crowded else name
                page.screenshot(path=str(OUT/f"{state_name}-{PHASE}-{suffix}.png"))
            def choose_view(name: str) -> None:
                target=win.get_by_role("tab",name=name,exact=True)
                if not target.count() or not target.is_visible():
                    win.get_by_role("button",name="Agent view more",exact=True).click()
                    win.get_by_role("menuitem",name=name,exact=True).click()
                else:
                    target.click()
            def pick(ref: str) -> None:
                back=win.get_by_role("button",name="Back",exact=True)
                if width==393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is not None:
                    back.click()
                row=win.locator(f'[data-testid="agents-list"] [data-object-id="{ref}"]')
                row.scroll_into_view_if_needed()
                _settle(page)
                row.click()
                expect(row).to_have_attribute("aria-selected","true")
                if width == 393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is None:
                    row.press("Enter")
                expect(win.get_by_test_id("agents-mast")).to_be_visible()
            shot("list")
            if pane == "work":
                _read_the_fleet(page,win)
            for i, state_name in ([(0, "path-name"), (1, "identifier-name")] if crowded else []):
                pick(f"launch:launch_agents14_{i}")
                shot(state_name)
                choose_view("Facts")
                shot(f"{state_name}-facts")
                choose_view("Now")
            pick("launch:launch_c4_runbook")
            expect(win.get_by_test_id("agent-row-question")).to_be_visible()
            assert win.get_by_test_id("agent-row-question").evaluate("""el=>{const well=el.closest('.surface-preference-well'), box=well.getBoundingClientRect();const range=document.createRange();range.selectNodeContents(el);const first=[...range.getClientRects()].find(r=>r.height>0);return first && first.top>=box.top-1 && first.bottom<=box.bottom+1;}"""), "The question's first line must be in its reading well"
            expect(win.get_by_test_id("conductor-ask-row")).to_have_attribute("data-feedback-redact","true")
            q = win.get_by_test_id("agent-row-question").bounding_box()
            field = win.get_by_test_id("agent-row-answer-field").bounding_box()
            assert q and field and field["y"] - q["y"] - q["height"] <= 36, "Answer must follow the question"
            shot("waiting")
            win.get_by_test_id("agent-row-answer-field").fill("Keep Jordan as the owner")
            shot("answer-draft")
            # No real terminal is present: the hub refuses and the input must stay.
            win.get_by_test_id("conductor-answer").click()
            expect(win.get_by_test_id("agent-row-refusal")).to_be_visible()
            expect(win.get_by_test_id("agent-row-answer-field")).to_have_value("Keep Jordan as the owner")
            shot("answer-refused")
            shot("waiting-files")
            for tab in ["Activity","Facts"]:
                choose_view(tab)
                shot(f"waiting-{tab.lower()}")
            choose_view("Now")
            expect(win.get_by_test_id("agent-row-answer-field")).to_have_value("Keep Jordan as the owner")
            if pane == "work":
                pick("launch:launch_c4_recon")
                shot("working")
                _press(win,"conductor-bar-stop","Stop")
                expect(win.get_by_role("button",name="Cancel",exact=True)).to_be_focused()
                shot("stop-question")
                win.get_by_role("button",name="Cancel",exact=True).click()
                _press(win,"conductor-bar-terminal","Open terminal")
                expect(win.get_by_test_id("lane-raw-pane")).to_be_visible()
                shot("terminal-unavailable")
                _press(win,"conductor-bar-terminal","Back to the agent")
                _press(win,"conductor-bar-tell","Tell it")
                win.get_by_role("textbox",name="Tell it",exact=True).fill("Keep the checkpoint")
                shot("tell-it")
                win.get_by_role("button",name="Cancel",exact=True).click()
            if pane == "records":
                pick("launch:launch_c4_flag")
                shot("pull-request")
                for tab in ["Activity","Files","Facts"]:
                    choose_view(tab)
                    if PHASE == "after" and tab == "Files":
                        expect(win.get_by_text("No local files. Use Open the PR to read its files.", exact=True)).to_be_visible()
                    shot(f"pr-{tab.lower()}")
                pick("launch:launch_ag0_done")
                shot("done")
                # Installed agents keep their connection and installation actions.
                pick("agent:claude")
                shot("installed")
                for name in ["Activity","Facts"]:
                    choose_view(name)
                    shot(f"installed-{name.lower()}")
            win.get_by_test_id("conductor-start").click()
            expect(win.get_by_test_id("conductor-start-words")).to_be_visible()
            shot("start")
            win.get_by_test_id("conductor-start-words").fill("Write the rollback note")
            shot("start-draft")
            assert not errors,errors
            browser.close()
    finally:
        server.stop()

@pytest.mark.parametrize("width",[1440,393])
@pytest.mark.parametrize("kind",["unbreakable","long-id"])
@pytest.mark.timeout(240)
def test_agents_keeps_a_full_question_and_answer_seat(tmp_path: Path,monkeypatch: pytest.MonkeyPatch,width:int,kind:str)->None:
    from playwright.sync_api import sync_playwright,expect
    from .test_agents_glass import _seed as seed_question,_isolate,UNBREAKABLE,LONG_ID
    question=UNBREAKABLE if kind=="unbreakable" else LONG_ID
    _ensure_build()
    _isolate(tmp_path,monkeypatch)
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        seed_question(tmp_path/"home",question)
        _seed_fleet(tmp_path/"home", count=54, examples=False)
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            _reference_build(page)
            page.goto(f"{base}/?token={TOKEN}",wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            _open_agents(page,base,width)
            win=page.locator("#conductor")
            row=win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_p16_words"]')
            row.click()
            words=win.get_by_test_id("agent-row-question")
            expect(words).to_be_visible()
            assert words.text_content().strip()==question.replace("`","")
            assert words.evaluate("el=>el.scrollWidth<=el.clientWidth+1")
            assert words.evaluate("""el=>{
                const seat=el.closest('.surface-preference-well'), parent=seat.parentElement;
                const siblings=[...parent.children].filter(e=>e!==seat&&getComputedStyle(e).display!=='none');
                const free=parent.clientHeight-siblings.reduce((n,e)=>n+e.getBoundingClientRect().height,0)-(parseFloat(getComputedStyle(parent).rowGap)||0)*siblings.length;
                const line=parseFloat(getComputedStyle(el.querySelector('p')||el).lineHeight);
                return seat.clientHeight >= Math.min(el.scrollHeight,free)-line-1;
            }"""), "The question uses the space left by its answer, on whole lines"
            if kind == "long-id":
                detail=words.evaluate("""el=>{const seat=el.closest('.surface-preference-well');return {question:el.getBoundingClientRect().toJSON(),well:seat.getBoundingClientRect().toJSON(),content:el.scrollHeight,ancestors:[seat.parentElement,seat.parentElement.parentElement].map(el=>({box:el.getBoundingClientRect().toJSON(),children:[...el.children].map(c=>({cls:c.className,box:c.getBoundingClientRect().toJSON()}))}))};}""")
                page.screenshot(path=str(OUT/f"question-fit-{PHASE}-{900 if width==1440 else 393}.png"))
                assert words.evaluate("el=>el.closest('.surface-preference-well').clientHeight>=el.scrollHeight-1"), detail
            field=win.get_by_test_id("agent-row-answer-field")
            expect(field).to_be_visible()
            field.fill("Keep the owner named in the runbook")
            button=win.get_by_test_id("conductor-answer")
            expect(button).to_be_visible()
            assert button.evaluate("el=>{const r=el.getBoundingClientRect(),w=el.closest('#conductor').getBoundingClientRect();return r.top>=w.top&&r.bottom<=w.bottom&&r.left>=w.left&&r.right<=w.right;}")
            _settle(page)
            page.screenshot(path=str(OUT/f"question-{kind}-{PHASE}-{900 if width==1440 else 393}.png"))
            browser.close()
    finally:
        server.stop()

@pytest.mark.parametrize("width",[1440,393])
@pytest.mark.timeout(240)
def test_agents_recorded_questions_and_restart(tmp_path:Path,monkeypatch:pytest.MonkeyPatch,width:int)->None:
    """The existing producer tapes supply uncommon lifecycle states; no agent runs."""
    import json
    from playwright.sync_api import sync_playwright,expect
    fixtures=Path(__file__).resolve().parents[2]/"web/src/desk/__tests__/fixtures"
    def wire(group:str,name:str):
        return json.loads((fixtures/group/f"{name}.wire.json").read_text())["wire"]
    case=["agents-ag7"]
    _ensure_build()
    from .test_agents_glass import _isolate
    _isolate(tmp_path,monkeypatch)
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    _seed_fleet(tmp_path/"home", count=55, examples=False)
    from .agents_lane_rig import _http
    status, produced = _http(base,"GET","/api/coders/sessions",TOKEN)
    assert status == 200, produced
    extras = [row for row in produced["flights"] if str(row.get("launch_id", "")).startswith("launch_agents14_")]
    def fleet():
        data=wire(case[0],"coders-sessions.checked" if case[0]=="agents-ag0" else "coders-sessions")
        ids={row.get("launch_id") or row.get("origin_ref") for row in data["flights"]+data["history"]}
        data["flights"].extend(copy.deepcopy(extras[:55-len(ids)]))
        data["count"]=len(data["flights"])
        return data
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            page.goto(f"{base}/?token={TOKEN}",wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            def recorded_page():
                fresh=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
                _reference_build(fresh)
                fresh.route("**/api/coders/sessions**",lambda route:route.fulfill(json=fleet()))
                fresh.route("**/api/agent/launches/launch_ag7_held/lane**",lambda route:route.fulfill(json=wire("agents-ag7","lane.held")))
                fresh.route("**/api/agent/launches/launch_ag0_done/lane**",lambda route:route.fulfill(json=wire("agents-ag0","lane.done")))
                fresh.route("**/api/agent/launches/*/resume",lambda route:route.fulfill(status=409,json=wire("agents-ag6","resume.refused")))
                return fresh
            def open_case(group:str):
                nonlocal page
                # Each tape is a separate desk snapshot, with no old page cache or close still in flight.
                page.close()
                clear_hub_windows_http(base,TOKEN)
                page=recorded_page()
                case[0]=group
                tape=json.loads((fixtures/group/("coders-sessions.checked.wire.json" if group=="agents-ag0" else "coders-sessions.wire.json")).read_text())
                page.clock.set_fixed_time(tape["captured_at"])
                status, opened = _http(base,"POST","/api/desk/windows/conductor/open",TOKEN,{})
                assert status == 200, opened
                if width == 1440:
                    status, sized = _http(base,"POST","/api/desk/windows/conductor/set_geometry",TOKEN,
                                           {"rect":{"x":"-1/2 + 240","y":"-1/2 + 100","w":"900px","h":"600px"}})
                    assert status == 200, sized
                page.goto(f"{base}/conductor?token={TOKEN}",wait_until="load")
                _normal_chair(page)
                win=page.locator("#conductor")
                try:
                    expect(win.locator(".surface-mast-facts")).to_contain_text("55 sessions", timeout=15000)
                    expect(win.get_by_test_id("conductor-row").first).to_be_visible()
                except AssertionError:
                    page.screenshot(path=str(OUT.parents[1]/f"agents-load-{group}-{PHASE}-{width}.png"))
                    print(page.evaluate("""() => ({windows:[...document.querySelectorAll('.desk-window-shell')].map(el=>({id:el.id,cls:el.className})),rows:document.querySelectorAll('[data-testid="conductor-row"]').length,scoped:document.querySelectorAll('#conductor [data-testid="conductor-row"]').length,first:document.querySelector('[data-testid="conductor-row"]')?.outerHTML.slice(0,500)})"""))
                    raise
                return win
            findings=[]
            def shot(win,name:str):
                _settle(page)
                assert win.evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                if name == "checked":
                    reading = win.locator(".surface-tab-panel > .surface-preference-well").bounding_box()
                    verbs = win.locator(".surface-tab-panel").bounding_box()
                    assert reading and verbs and reading["y"] + reading["height"] <= verbs["y"] + verbs["height"] + 1
                page.screenshot(path=str(OUT/f"{name}-{PHASE}-{900 if width==1440 else 393}.png"))
                if name == "remove-question":
                    if not win.get_by_role("tablist",name="Agent progress").count():
                        findings.append("1: Remove lost the step track")
                    if not win.get_by_role("log",name="Latest activity").count():
                        findings.append("1: Remove lost the last activity")
                    well=win.locator(".surface-tab-panel > .surface-preference-well").bounding_box()
                    for part in (win.get_by_role("tablist",name="Agent progress"),win.get_by_role("log",name="Latest activity")):
                        box=part.bounding_box() if part.count() else None
                        if box and well and (box["y"] < well["y"]-1 or box["y"]+box["height"] > well["y"]+well["height"]+1):
                            findings.append("1: Remove hides progress or the last activity outside its well")
                if name == "checked":
                    row=win.get_by_text("Launched",exact=True).locator("..").bounding_box()
                    well=win.locator(".surface-tab-panel > .surface-preference-well").bounding_box()
                    if row and well and row["y"] < well["y"]+well["height"] and row["y"]+row["height"] > well["y"]+well["height"]+1:
                        findings.append("2: Launched is a partial row")
                    if not win.get_by_text("Launched",exact=True).evaluate("""el=>{const row=el.closest('.gadget-row'), box=row.getBoundingClientRect();for(let p=row.parentElement;p&&p!==el.closest('.surface-tab-panel');p=p.parentElement){if(['auto','scroll','hidden','clip'].includes(getComputedStyle(p).overflowY)){const b=p.getBoundingClientRect();if(box.top<b.top-1||box.bottom>b.bottom+1)return false;}}return box.height>0;}"""):
                        findings.append("2: Launched is outside its facts or reading well")
                if name == "restart" and width == 1440:
                    hovering=win.locator('[data-testid="agents-list"] [aria-selected="false"]:hover')
                    if hovering.count() and hovering.first.evaluate("el=>getComputedStyle(el).backgroundColor !== 'rgba(0, 0, 0, 0)'"):
                        findings.append("3: Another row wears a hover ground at rest")
                if win.get_by_text("Could not mark it seen",exact=True).count():
                    findings.append(f"6: {name} shows an automatic seen failure")
                if width == 393 and not win.locator(".surface-mast-facts").inner_text().endswith("3 here"):
                    findings.append(f"4: {name} does not keep both compact counts")

                if name in {"checked", "remove-question"}:
                    fit = win.locator(".surface-tab-panel > .surface-preference-well").evaluate("""el=>({well:el.getBoundingClientRect().toJSON(),panel:el.parentElement.getBoundingClientRect().toJSON(),scroll:el.scrollHeight,height:el.clientHeight})""")
                    print(name, width, fit)
                    assert fit["well"]["bottom"] <= fit["panel"]["bottom"] + 1, fit
                    strip = win.locator(".desk-surface-foot").bounding_box()
                    assert strip and fit["well"]["bottom"] <= strip["y"] + 1, fit
                    if name == "remove-question":
                        said = win.get_by_test_id("lane-result-said").evaluate("""el=>{const range=document.createRange();range.selectNodeContents(el);return range.getBoundingClientRect().toJSON();}""")
                        assert said["top"] >= fit["well"]["top"] - 1 and said["bottom"] <= min(strip["y"],fit["well"]["bottom"])+1, (said, fit)
                if name == "restart":
                    assert win.locator('[data-testid="agents-list"] [aria-selected="true"]').count() == 1
            win=open_case("agents-ag7")
            target=win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_ag7_held"]')
            target.scroll_into_view_if_needed()
            _settle(page)
            target.click()
            expect(target).to_have_attribute("aria-selected", "true")
            if width == 393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is None:
                target.press("Enter")
            expect(win.get_by_test_id("conductor-held-call")).to_be_visible()
            assert win.get_by_test_id("agent-row-command").evaluate("""el=>{const box=el.closest('.surface-preference-well').getBoundingClientRect();const range=document.createRange();range.selectNodeContents(el);const first=[...range.getClientRects()].find(r=>r.height>0);return first && first.top>=box.top-1 && first.bottom<=box.bottom+1;}"""), "The held command must remain in view"
            expect(win.get_by_test_id("conductor-deny")).to_be_focused()
            assert win.get_by_test_id("conductor-deny").evaluate("el=>parseFloat(getComputedStyle(el).outlineWidth)") >= 2
            expect(win.get_by_text("The agent runs this command one time.", exact=True)).to_be_visible()
            shot(win,"permission-held")
            win=open_case("agents-ag0")
            target=win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_ag0_done"]')
            target.scroll_into_view_if_needed()
            _settle(page)
            target.click()
            expect(target).to_have_attribute("aria-selected", "true")
            if width == 393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is None:
                target.press("Enter")
            shot(win,"checked")
            _press(win,"conductor-bar-remove","Remove")
            question=win.get_by_role("region",name="Remove Draft test scaffolding for flags?",exact=True)
            expect(question).to_be_visible()
            expect(question.get_by_role("button",name="Cancel",exact=True)).to_be_focused()
            shot(win,"remove-question")
            question.get_by_role("button",name="Cancel",exact=True).click()
            win=open_case("agents-ag6")
            target=win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_ag0_ghost"]')
            target.scroll_into_view_if_needed()
            _settle(page)
            target.click()
            expect(target).to_have_attribute("aria-selected", "true")
            if width == 393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is None:
                target.press("Enter")
            shot(win,"restart")
            _press(win,"conductor-bar-resume","Resume")
            expect(win.get_by_test_id("conductor-stop-receipt")).to_contain_text("Not resumed" if PHASE == "before" else "The agent did not resume; use Hand again.")
            shot(win,"resume-refused")
            win=open_case("agents-ag8")
            queued=win.locator('[data-testid="agents-list"] [data-object-id^="queue:"]').first
            queued.scroll_into_view_if_needed()
            _settle(page)
            queued.click()
            expect(queued).to_have_attribute("aria-selected", "true")
            if width == 393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is not None:
                win.get_by_role("button",name="Back",exact=True).click()
            queued.scroll_into_view_if_needed()
            _settle(page)
            queued.click(button="right")
            expect(queued).to_have_attribute("aria-selected", "true")
            menu=page.get_by_role("menu",name="Agents actions",exact=True)
            shot(win,"queued-menu")
            try:
                expect(menu.get_by_role("menuitem",name="Cancel task",exact=True)).to_be_enabled()
            except AssertionError:
                print({"menus":page.locator('[role="menu"]').evaluate_all("els=>els.map(el=>({label:el.getAttribute('aria-label'),text:el.innerText}))"),"pane":win.get_by_test_id("agents-pane").inner_text()[:1500],"picked":win.locator('[data-testid="agents-list"] [aria-selected="true"]').get_attribute("data-object-id")})
                raise
            menu.get_by_role("menuitem",name="Cancel task",exact=True).click()
            question=win.get_by_role("region",name="Cancel Tidy the ledger runbook?",exact=True)
            expect(question).to_be_visible()
            expect(question.get_by_role("button",name="Keep it",exact=True)).to_be_focused()
            shot(win,"queue-question")
            question.get_by_role("button",name="Keep it",exact=True).click()
            shot(win,"queued")
            browser.close()
            assert not findings, "\n".join(findings)
    finally:
        server.stop()
