"""Agents selection, question, reading wells and forms on the real isolated hub."""
from pathlib import Path
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from .conductor_rig import _seed

OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/agents13/r2"
TOKEN = "agents13"


def _press(win, verb: str, label: str) -> None:
    button = win.get_by_test_id(verb)
    if button.count() and button.is_visible():
        button.click()
    else:
        import re
        win.get_by_role("button", name=re.compile(r"^Actions")).click()
        win.page.get_by_role("menuitem", name=label, exact=True).click()

@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(240)
def test_agents_selection_and_inspector_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
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
        _seed(tmp_path/"home")
        from tests.integration.test_desk_agents_wire import _ag0_seed
        _ag0_seed(tmp_path/"home")
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}",wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            clear_hub_windows(page,TOKEN)
            page.goto(f"{base}/conductor?token={TOKEN}",wait_until="load")
            _normal_chair(page)
            win=page.locator("#conductor")
            expect(win.get_by_test_id("conductor-row").first).to_be_visible()
            if width==1440:
                _api(page,"POST","/api/desk/windows/conductor/set_geometry",{"rect":{"x":"-1/2 + 240","y":"-1/2 + 100","w":"900px","h":"600px"}},token=TOKEN)
            suffix=900 if width==1440 else 393
            def shot(name: str) -> None:
                _settle(page)
                assert win.evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                assert win.locator(".aw-plate,.surface-mast:not(.surface-mast--framed),.surface-rail").count()==0
                assert win.get_by_test_id("conductor-pill").evaluate_all("els=>els.every(el=>el.scrollWidth<=el.clientWidth+1 && [...el.querySelectorAll('span')].every(s=>s.scrollWidth<=s.clientWidth+1))"), "A state pill must show whole words"
                page.screenshot(path=str(OUT/f"{name}-{suffix}.png"))
            def choose_view(name: str) -> None:
                target=win.get_by_role("tab",name=name,exact=True)
                if not target.count() or not target.is_visible():
                    win.get_by_role("button",name="Agent view more",exact=True).click()
                    win.get_by_role("menuitem",name=name,exact=True).click()
                else: target.click()
            def pick(ref: str) -> None:
                back=win.get_by_role("button",name="Back",exact=True)
                if width==393 and win.locator(".surface-list-pane").get_attribute("data-detail-open") is not None: back.click()
                row=win.locator(f'[data-testid="agents-list"] [data-object-id="{ref}"]')
                row.click()
                expect(row).to_have_attribute("aria-selected","true")
                expect(win.get_by_test_id("agents-mast")).to_be_visible()
            shot("list")
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
            for tab in ["Activity","Files","Facts"]:
                choose_view(tab)
                shot(f"waiting-{tab.lower()}")
            choose_view("Now")
            expect(win.get_by_test_id("agent-row-answer-field")).to_have_value("Keep Jordan as the owner")
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
            pick("launch:launch_c4_flag")
            shot("pull-request")
            for tab in ["Activity","Files","Facts"]:
                choose_view(tab)
                shot(f"pr-{tab.lower()}")
            pick("launch:launch_ag0_done")
            shot("done")
            # Installed agents keep their connection and installation actions.
            pick("agent:claude")
            shot("installed")
            for name in ["Activity","Files","Facts"]:
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
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            page.goto(f"{base}/?token={TOKEN}",wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            clear_hub_windows(page,TOKEN)
            page.goto(f"{base}/conductor?token={TOKEN}",wait_until="load")
            _normal_chair(page)
            win=page.locator("#conductor")
            if width==1440:
                _api(page,"POST","/api/desk/windows/conductor/set_geometry",{"rect":{"x":"-1/2 + 240","y":"-1/2 + 100","w":"900px","h":"600px"}},token=TOKEN)
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
                page.screenshot(path=str(OUT/f"question-fit-{900 if width==1440 else 393}.png"))
                assert words.evaluate("el=>el.closest('.surface-preference-well').clientHeight>=el.scrollHeight-1"), detail
            field=win.get_by_test_id("agent-row-answer-field")
            expect(field).to_be_visible()
            field.fill("Keep the owner named in the runbook")
            button=win.get_by_test_id("conductor-answer")
            expect(button).to_be_visible()
            assert button.evaluate("el=>{const r=el.getBoundingClientRect(),w=el.closest('#conductor').getBoundingClientRect();return r.top>=w.top&&r.bottom<=w.bottom&&r.left>=w.left&&r.right<=w.right;}")
            _settle(page)
            page.screenshot(path=str(OUT/f"question-{kind}-{900 if width==1440 else 393}.png"))
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
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            page.route("**/api/coders/sessions**",lambda route:route.fulfill(json=wire(case[0],"coders-sessions.checked" if case[0]=="agents-ag0" else "coders-sessions")))
            page.route("**/api/agent/launches/launch_ag7_held/lane**",lambda route:route.fulfill(json=wire("agents-ag7","lane.held")))
            page.route("**/api/agent/launches/launch_ag0_done/lane**",lambda route:route.fulfill(json=wire("agents-ag0","lane.done")))
            page.route("**/api/agent/launches/*/resume",lambda route:route.fulfill(status=409,json=wire("agents-ag6","resume.refused")))
            page.goto(f"{base}/?token={TOKEN}",wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            def open_case(group:str):
                case[0]=group
                tape=json.loads((fixtures/group/("coders-sessions.checked.wire.json" if group=="agents-ag0" else "coders-sessions.wire.json")).read_text())
                page.clock.set_fixed_time(tape["captured_at"])
                clear_hub_windows(page,TOKEN)
                page.goto(f"{base}/conductor?token={TOKEN}",wait_until="load")
                _normal_chair(page)
                if width==1440:
                    _api(page,"POST","/api/desk/windows/conductor/set_geometry",{"rect":{"x":"-1/2 + 240","y":"-1/2 + 100","w":"900px","h":"600px"}},token=TOKEN)
                win=page.locator("#conductor")
                expect(win.get_by_test_id("conductor-row").first).to_be_visible()
                return win
            def shot(win,name:str):
                _settle(page)
                assert win.evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                if name == "checked":
                    reading = win.locator(".surface-tab-panel > .surface-preference-well").bounding_box()
                    verbs = win.locator(".surface-tab-panel").bounding_box()
                    assert reading and verbs and reading["y"] + reading["height"] <= verbs["y"] + verbs["height"] + 1
                page.screenshot(path=str(OUT/f"{name}-{900 if width==1440 else 393}.png"))
                from .test_kit_polish_wave14_r2_glass import capture_state
                capture_state(page, win, "agents", name, width)
            win=open_case("agents-ag7")
            win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_ag7_held"]').click()
            expect(win.get_by_test_id("conductor-held-call")).to_be_visible()
            assert win.get_by_test_id("agent-row-command").evaluate("""el=>{const box=el.closest('.surface-preference-well').getBoundingClientRect();const range=document.createRange();range.selectNodeContents(el);const first=[...range.getClientRects()].find(r=>r.height>0);return first && first.top>=box.top-1 && first.bottom<=box.bottom+1;}"""), "The held command must remain in view"
            expect(win.get_by_test_id("conductor-deny")).to_be_focused()
            assert win.get_by_test_id("conductor-deny").evaluate("el=>parseFloat(getComputedStyle(el).outlineWidth)") >= 2
            expect(win.get_by_text("The agent runs this command one time.", exact=True)).to_be_visible()
            shot(win,"permission-held")
            win=open_case("agents-ag8")
            queued=win.locator('[data-testid="agents-list"] [data-object-id^="queue:"]').first
            queued.click(button="right")
            menu=page.get_by_role("menu",name="Agents actions",exact=True)
            shot(win,"queued-menu")
            try:
                expect(menu.get_by_role("menuitem",name="Cancel",exact=True)).to_be_enabled()
            except AssertionError:
                print({"menus":page.locator('[role="menu"]').evaluate_all("els=>els.map(el=>({label:el.getAttribute('aria-label'),text:el.innerText}))"),"pane":win.get_by_test_id("agents-pane").inner_text()[:1500],"picked":win.locator('[data-testid="agents-list"] [aria-selected="true"]').get_attribute("data-object-id")})
                raise
            menu.get_by_role("menuitem",name="Cancel",exact=True).click()
            question=win.get_by_role("region",name="Cancel Tidy the ledger runbook?",exact=True)
            expect(question).to_be_visible()
            expect(question.get_by_role("button",name="Keep it",exact=True)).to_be_focused()
            shot(win,"queue-question")
            question.get_by_role("button",name="Keep it",exact=True).click()
            shot(win,"queued")
            win=open_case("agents-ag0")
            win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_ag0_done"]').click()
            shot(win,"checked")
            _press(win,"conductor-bar-remove","Remove")
            question=win.get_by_role("region",name="Remove Draft test scaffolding for flags?",exact=True)
            expect(question).to_be_visible()
            expect(question.get_by_role("button",name="Cancel",exact=True)).to_be_focused()
            shot(win,"remove-question")
            question.get_by_role("button",name="Cancel",exact=True).click()
            win=open_case("agents-ag6")
            win.locator('[data-testid="agents-list"] [data-object-id="launch:launch_ag0_ghost"]').click()
            shot(win,"restart")
            _press(win,"conductor-bar-resume","Resume")
            expect(win.get_by_test_id("conductor-stop-receipt")).to_contain_text("Not resumed")
            shot(win,"resume-refused")
            browser.close()
    finally:
        server.stop()
