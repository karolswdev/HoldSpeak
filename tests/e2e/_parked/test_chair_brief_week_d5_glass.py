"""Parked by Betterment daily D5 (2026-10-18): the Brief and The week windows
retired into Today, so these browser fences lost their subject. Kept, not run
(tests/e2e/_parked/conftest.py). Their helpers and constants stay in the files
they came from.

- tests/e2e/test_chair_glass.py::TestTheBriefCarriesTheDay (the Brief window's
  rows after the scheduled write; Today's Since yesterday re-reads on the frame).
- tests/e2e/test_chair_glass.py::TestTheChairAsWindows (the four Chair windows;
  the two that stay are fenced by web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx
  and the desk sweep).
- tests/e2e/test_send_glass.py::TestChairMeetingWells (The week's meeting rows and
  their Send wells).
"""


class TestTheBriefCarriesTheDay:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        self.ledger = tmp_path / "agent_launches.json"
        monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", self.ledger)
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=BRIEF_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.timeout(600, method="thread")
    def test_the_open_brief_shows_the_day_when_the_scheduled_write_lands(self) -> None:
        """replaces: tests/e2e/test_philo15_19_brief_day_glass.py::TestTheBriefCarriesTheDay::test_the_open_brief_shows_the_day_when_the_scheduled_write_lands
        (1440; the 393 run differed only in Go as the door: phoneRing.test.tsx:191-206).
        T2 owed: the open Brief re-reading on the hub's desk_changed frame wants a
        ChairHome render over a recorded Brief pair and a delivered frame."""
        width = 1440
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": {1440: 900, 393: 852}[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                from holdspeak.people import production_people_store

                production_people_store().initialize()
                _brief_yesterdays()
                page.goto(f"{self.base}/?token={BRIEF_TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()
                # Yesterday's Brief is on the desk at load; the window opens on it.
                _brief_menu_pick(page, width, "Brief")
                brief = _brief_shell(page, "Brief")
                brief.get_by_test_id("arrival-brief").first.wait_for()
                yesterday = _api(page, "GET", "/api/brief/latest", token=BRIEF_TOKEN)
                title = brief.locator(".desk-window-title").first
                page.wait_for_function(
                    "([el, want]) => el.innerText.trim() === want",
                    arg=[title.element_handle(), yesterday["title"]], timeout=15_000)

                _brief_the_day(page, self.ledger)
                _brief_cadence_tick()

                # B59: no reload. The window re-reads on the hub's frame.
                latest = _api(page, "GET", "/api/brief/latest", token=BRIEF_TOKEN)
                assert latest["id"] != yesterday["id"], "the tick made today's Brief"
                page.wait_for_function(
                    "([el, want]) => el.innerText.trim() === want",
                    arg=[title.element_handle(), latest["title"]], timeout=15_000)
                brief.locator("[data-testid=arrival-brief-row]", has_text="PR merged").wait_for()
                # ORDER RULING: the three rows on the face.
                shown = [r.split("\n")[0].strip() for r in
                         brief.get_by_test_id("arrival-brief-row").all_inner_texts()]
                assert [t.split(": ", 1)[0] for t in shown] == ["PR merged", "Update sent", "PR opened"], shown
                rows = {i["text"]: i for items in latest["sections"].values() for i in items}
                for wanted in (
                    "Decision confirmed: Squash merges only on the rehearsal repository",
                    "Action done: Add a CODEOWNERS file",
                    "Agent launched: Add a CODEOWNERS file",
                    "PR opened: Add CODEOWNERS naming the owner (PR #4)",
                    "PR merged: Add CODEOWNERS naming the owner (PR #4)",
                    "Update sent: Rehearsal repo hygiene",
                    "Meeting recorded: Repo hygiene sync",
                    "Project added: Rehearsal repo hygiene",
                ):
                    assert wanted in rows, (wanted, sorted(rows))
                    assert re.search(r"\d{2}:\d{2}$", rows[wanted]["detail"] or ""), rows[wanted]
                # B73: no JSON, no id, no UTC stamp in any row.
                for text, item in rows.items():
                    assert not _BRIEF_RAW.search(text) and not _BRIEF_RAW.search(item.get("detail") or ""), item
                # One honest NOT READ row: the key-free Brief did not read People.
                assert any(t.startswith("NOT READ · People") for t in rows), sorted(rows)
                row = brief.locator("[data-testid=arrival-brief-row]", has_text="Update sent")
                detail = row.get_by_test_id("arrival-brief-row-detail")
                assert re.fullmatch(r"HoldSpeak folder · \d{2}:\d{2}", detail.inner_text().strip()), \
                    detail.inner_text()
                assert not _BRIEF_RAW.search(brief.inner_text()), brief.inner_text()
                _settle(page)
                page.screenshot(path=str(BRIEF_SHOTS / f"brief-window-after-write-{width}.png"))

                # The whole day, in the Brief's full view (its "N more").
                _brief_press(page, brief.get_by_test_id("arrival-brief-more"), width)
                full = page.get_by_text("PR merged", exact=False).first
                full.wait_for()
                _settle(page)
                page.screenshot(path=str(BRIEF_SHOTS / f"brief-full-{width}.png"))
                intel = page.locator(".desk-window[aria-label='Today']")
                unread = intel.get_by_text("NOT READ · People", exact=False).first
                unread.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(BRIEF_SHOTS / f"brief-full-not-read-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()


class TestChairMeetingWells(_Rig):
    # ── C6b: the Chair's MEETINGS rows (both branches) ──

    @staticmethod
    def _raise_week(page: Any, width: int, *, fresh: bool = False) -> None:
        """The existing Week window can be behind the open Meetings record.

        Betterment shell S0 (#1257): Window > Desk shows only while a window
        is open, so a fresh desk opens Needs you from Go first. S1 (#1259):
        The week left the phone Go (its window retires in daily D5), so at
        393 the hub opens it, the agent door the desk sweep uses."""
        if width > 720:
            if fresh:
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").click()
            page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
            page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").click()
            page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('The week')").click()
        else:
            _api(page, "POST", "/api/desk/windows/chair:week/open", {}, token=H1_TOKEN)
        page.locator(".chair-window--week").wait_for(timeout=H1_T)
        _settle(page)

    @staticmethod
    def _open_from_week(page: Any, title: str, meeting_id: str) -> str:
        row = page.locator(".chair-window--week [data-testid=arrival-meeting-row]").filter(has_text=title)
        row.locator("[data-testid=arrival-meeting-open]").click()
        record = page.locator(f"[id='{MEET}']")
        record.locator("[data-testid=meeting-summary-text]").wait_for(timeout=H1_T)
        record.locator("[data-testid=meeting-send]").click()
        scope = f"[id='{MEET}'] [data-testid=meeting-send-well]:has([data-send=well][data-doc='meeting_summary:{meeting_id}'])"
        page.locator(f"{scope} [data-testid=destination-row]").first.wait_for(timeout=H1_T)
        _settle(page)
        return scope

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_chair_meeting_wells(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

        shots = Boards(H1_SHOTS, width)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                db = get_database()
                now = datetime.now().replace(microsecond=0)
                seg = [TranscriptSegment(text="Two write paths still hit the old ledger.", speaker="Me", start_time=4.0, end_time=9.0)]
                # The healthy branch: a recorded meeting with its stored summary.
                db.meetings.save_meeting(MeetingState(
                    id="c6-sync", started_at=now - timedelta(hours=2), ended_at=now - timedelta(hours=1, minutes=15),
                    title="Ledger cutover sync", segments=seg, intel_status="completed",
                    intel=IntelSnapshot(timestamp=0.0, summary="The team agreed to freeze the old ledger on Nov 3.",
                                        topics=["cutover"])))
                # The retained-summary branch: a stored summary, then a re-run that failed (the
                # intel queue's own enqueue -> claim -> fail); the Chair keeps the summary with its
                # status facts.
                db.meetings.save_meeting(MeetingState(
                    id="c6-retry", started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=30),
                    title="Vendor escalation", segments=seg, intel_status="completed",
                    intel=IntelSnapshot(timestamp=0.0, summary="The vendor owes a fix for the export by Friday.",
                                        topics=["vendor"])))
                db.intel.enqueue_intel_job("c6-retry", transcript_hash="c6-retry-hash")
                claimed = db.intel.claim_next_intel_job(include_scheduled=True)
                assert claimed is not None and claimed.meeting_id == "c6-retry", claimed
                db.intel.fail_intel_job("c6-retry", "engine answered 500")
                team, team_dir = self._dest(page, "Team folder")
                self._reload(page, "The week")

                record = f"[id='{MEET}']"
                OK = self._open_from_week(page, "Ledger cutover sync", "c6-sync")
                assert self._text(page, f"{record} [data-testid=meeting-summary-text]") == \
                    "The team agreed to freeze the old ledger on Nov 3."

                # The Chair's Open now lands in the existing Meetings record.
                # Read its Send well in the same zoomed desktop posture.
                if width > 720:
                    page.locator(f"{record} .desk-gadget-zoom").click()
                    page.wait_for_timeout(600)
                # C6b, the healthy branch: SUMMARY, then SEND with the form picker (44 px at 393).
                picker = f"{OK} [data-testid=doc-forms] select, {OK} [data-testid=doc-forms] .btn"
                c6 = shots.shoot(page, "C6b-chair-meetings-row-well", OK,
                                 [f"{record} [data-testid=meeting-summary-text]",
                                  f"{OK} [data-testid=doc-forms]", f"{OK} [data-testid=destination-row]"],
                                 seat=f"{record} [data-testid=meeting-summary-text]")
                assert "meeting_summary:c6-sync" in c6["wells"], c6["wells"]
                pick_box = page.evaluate("(s) => { const e = document.querySelector(s); const r = e.getBoundingClientRect(); return [r.width, r.height, e.tagName]; }", picker)
                c6["picker_box"] = pick_box
                picker_probe = [o for o in c6["pointer"]["owned"] if o["text"].startswith("Summary") or o["text"] == "Document"]
                c6["picker_owned"] = picker_probe
                assert picker_probe, c6["pointer"]
                if width == 393:
                    # G4 on the Chair: the picker is 44 px tall and owns all nine points of its target.
                    assert pick_box[1] >= 44, pick_box
                    assert all(min(o["target"]) >= 44 for o in picker_probe), picker_probe
                    # PHILO-13-11 (slice two, R2): the old law here scrolled the picker UNDER
                    # the Chair's sticky capture bar and proved the wheel brought it out. The
                    # capture bar is its own window now (on demand from Speak at 393): no bar
                    # floats over The week, so nothing can sit under it. Proven structurally,
                    # and the picker still owns all nine points of its 44 x 44 target.
                    bars_over_week = page.locator(".chair-window--week [data-testid=arrival-capture-bar]").count()
                    owned_nine = page.evaluate("""(sel) => { const p = document.querySelector(sel); p.scrollIntoView({block: 'center'});
                          const r = p.getBoundingClientRect();
                          const cx = r.left + r.width / 2, cy = r.top + r.height / 2, w = Math.max(44, r.width), h = Math.max(44, r.height);
                          const L = cx - w / 2 + 1, R = cx + w / 2 - 1, H1_T = cy - h / 2 + 1, B = cy + h / 2 - 1;
                          return [[cx, cy], [cx, H1_T], [R, cy], [cx, B], [L, cy], [L, H1_T], [R, H1_T], [L, B], [R, B]]
                            .map(([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && p.contains(e); }); }""", picker)
                    c6["picker_after_scroll"] = {"capture_bars_over_the_week": bars_over_week, "nine_points_owned": owned_nine}
                    assert bars_over_week == 0 and all(owned_nine), c6["picker_after_scroll"]
                    # This record fits without scrolling, so centering the picker keeps the board still.
                    shots.shoot(page, "C6f-chair-picker-scrolled-clear-393".replace("-393", ""), OK,
                                [f"{OK} [data-testid=doc-forms]"], seat=None, same_as="C6b-chair-meetings-row-well")

                # The send leg from the Chair row: face = hub row = kernel receipt.
                self._pick(page, OK, "Team folder")
                self._press(page, OK, "Team folder")
                mref = "meeting_summary:c6-sync"
                hub = self._sends(page, mref)
                assert [(s["document_ref"], s["state"]) for s in hub] == [(mref, "sent")], hub
                mpath = hub[0]["proof"]["path"]
                assert Path(mpath).parent == team_dir and "freeze the old ledger" in Path(mpath).read_text()
                with db._connection() as conn:
                    frozen_payload = conn.execute("SELECT payload FROM channel_sends WHERE id=?", (hub[0]["id"],)).fetchone()[0]
                assert Path(mpath).read_bytes() == frozen_payload
                c6s = shots.shoot(page, "C6c-chair-meetings-row-saved", OK,
                                  [f"{opened(OK, 'Team folder')} [data-receipt=latest]"], block="center")
                assert c6s["receipts"] == [{"text": f"✓ SAVED {mpath}", "state": "sent", "code": None}], c6s["receipts"]
                c6s["kernel_send"] = self._face_row_receipt(hub[0], mref)
                self._unpick(page, OK, "Team folder")

                # Return, raise The week, and use the failed record's actual Open.
                if width > 720:
                    page.locator(f"{record} [data-testid=meeting-record-back]").click()
                else:
                    page.locator(f"{record} .desk-gadget-close").click()
                self._raise_week(page, width)
                failed_row = page.locator(".chair-window--week [data-testid=arrival-meeting-row]").filter(has_text="Vendor escalation")
                assert "FAILED" in failed_row.inner_text()
                RT = self._open_from_week(page, "Vendor escalation", "c6-retry")
                assert self._text(page, f"{record} [data-testid=meeting-summary-text]") == \
                    "The vendor owes a fix for the export by Friday."

                # The retained summary keeps its failed-run fact beside the record.
                c6r = shots.shoot(page, "C6e-chair-retained-summary-well", RT,
                                  [f"{record} [data-testid=meeting-summary-state]", f"{record} [data-testid=meeting-summary-text]",
                                   f"{RT} [data-testid=doc-forms]",
                                   f"{RT} [data-testid=destination-row]"],
                                  seat=f"{record} [data-testid=meeting-summary-state]")
                assert "meeting_summary:c6-retry" in c6r["wells"], c6r["wells"]
                assert "FAILED" in self._text(page, f"{record} [data-testid=meeting-summary-state]")

                if width > 720:
                    page.locator(f"{record} .desk-gadget-zoom").click()
                    page.wait_for_timeout(400)
                shots.write("chair-meetings-slack", {"hub_sends": {"meeting": hub},
                                                     "edge_requests": len(self.edge.requests)})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()


@pytest.mark.chair_windows_open
class TestTheChairAsWindows:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=H1_TOKEN)
        self.home = tmp_path / "home"
        _seed(self.home)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=2, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={H1_TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            H1_TOKEN,
        )
        _api(page, "POST", "/api/channels/destinations",
             {"name": "Team updates", "channel": "file",
              "folder": str(self.home / "Documents" / "HoldSpeak" / "Team updates")}, token=H1_TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        try:
            page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=10_000)
        except Exception:  # noqa: BLE001 -- the fences below name what is missing (red on bbf7e9a4)
            pass
        page.wait_for_timeout(1500)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _measure(page: Any, width: int, board: str, facts: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        page.wait_for_timeout(400)
        _settle(page)
        frame = page.evaluate(FRAME_JS, width)
        chair = page.evaluate(CHAIR_JS, width)
        facts[board] = {"frame": frame, "chair": chair}
        return frame, chair

    @staticmethod
    def _fails(frame: dict[str, Any], chair: dict[str, Any], width: int) -> dict[str, Any]:
        fails: dict[str, Any] = {}
        if len(frame["blue"]) != 1 or frame["front"] != frame["blue"] or frame["screen"] != frame["blue"][0]:
            fails["C2 one blue window, named by the screen bar"] = {
                "blue": frame["blue"], "front": frame["front"], "screen": frame["screen"]}
        if frame["ownership"]:
            fails["C5 frame ownership"] = frame["ownership"]
        if frame["clipped"] or frame["sideways"]:
            fails["C5 frame clips"] = {"clipped": frame["clipped"], "sideways": frame["sideways"]}
        if frame["small_text"] or frame["low_contrast"]:
            fails["C5 frame text in place"] = {"small": frame["small_text"], "low": frame["low_contrast"]}
        if chair["clipped"] or chair["sideways"] or chair["overlap"]:
            fails["C5 Chair windows: nothing clips, nothing scrolls sideways, nothing overlaps"] = {
                "clipped": chair["clipped"], "sideways": chair["sideways"], "overlap": chair["overlap"]}
        if chair["low_contrast"]:
            fails["C5 Chair windows: contrast in place"] = chair["low_contrast"]
        if chair["page_scrolls"]:
            fails["C1 the Chair page does not scroll"] = True
        for name, body in chair["bodies"].items():
            if body["overflowY"] not in ("auto", "scroll"):
                fails.setdefault("C1 each window scrolls on its own", []).append({name: body})
        if width > 720 and chair["tiles_overlap"]:
            fails["C1 the four tile"] = chair["tiles_overlap"]
        if width <= 720:
            front = [pane for pane in chair["phone_panes"] if pane["front"]]
            if (len(front) != 1 or chair["usable_windows"] != frame["front"]
                    or any(owner != front[0]["id"] for owner in front[0]["hits"])):
                fails["C4 one usable front pane owns its full work area"] = chair["phone_panes"]
            if frame["content"] is None or frame["content"] < 700 or frame["small_targets"] or chair["small_targets"]:
                fails["C4 393 content and targets"] = {"content": frame["content"], "frame": frame["small_targets"],
                                                      "body": chair["small_targets"]}
        return fails

    @staticmethod
    def _verbs(page: Any) -> dict[str, Any]:
        """C6: the existing verbs, each in its window."""
        def inside(win: str, sel: str) -> int:
            return page.locator(f".desk-window-shell[aria-label='{win}'] {sel}").count()
        return {
            "needs.done": inside("Needs you", "[data-verb='done'], [data-verb='door-verb']"),
            "needs.name_owner": inside("Needs you", "[data-verb='name-owner']"),
            "needs.connect_calendar": inside("Needs you", "[data-verb='connect-calendar']"),
            "needs.choose_engine": inside("Needs you", "[data-verb='setup']"),
            "brief.ack_defer": inside("Brief", "[data-testid='arrival-brief-row'] button"),
            "brief.generate": inside("Brief", "button:has-text('Generate')"),
            "brief.send_well": inside("Brief", ":text('Team updates')"),
            "week.open": inside("The week", "[data-testid='arrival-meeting-row'] button:has-text('Open')"),
            "week.stored": page.evaluate("""() => [...document.querySelectorAll(
                '.desk-window-shell[aria-label="The week"] [data-testid="arrival-meeting-row"]')]
                .filter((r) => (r.querySelector('[data-testid="arrival-meeting-badge"]') || {}).textContent === 'SUMMARY STORED')
                .map((r) => ({run: Boolean(r.querySelector('[data-testid="arrival-run-intel"]')),
                              open: Boolean(r.querySelector('[data-testid="arrival-meeting-open"]'))}))"""),
            "capture": inside("Capture", "[data-testid='arrival-develop-thought'], [data-testid='arrival-record-meeting'], [data-testid='arrival-schedule']"),
        }

    @staticmethod
    def _stop(facts: dict[str, Any], failures: dict[str, Any], tag: str) -> None:
        """No Chair windows to walk: record what the first board measured and fail."""
        failures = {k: v for k, v in failures.items() if v}
        facts["failures"] = failures
        (H1_SHOTS / f"chair-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
        raise AssertionError(json.dumps(failures, indent=2))

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_chair_as_windows(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        tag = f"{width}"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                shell = lambda name: chair_window(page, name)  # noqa: E731
                if width > 720:
                    # C1-4a: the four windows
                    frame, chair = self._measure(page, width, "chair-windows", facts)
                    failures["chair-windows"] = self._fails(frame, chair, width)
                    if sorted(chair["windows"]) != sorted(CHAIR):
                        failures["chair-windows"]["C1 four Chair windows"] = chair["windows"]
                        self._stop(facts, failures, tag)
                    verbs = self._verbs(page)
                    facts["verbs"] = verbs
                    missing = [k for k, v in verbs.items() if k not in ("week.stored",) and not v]
                    stored = verbs["week.stored"]
                    if missing or not stored or any(r["run"] or not r["open"] for r in stored):
                        failures["chair-windows"]["C6 the verbs keep their windows"] = {"missing": missing, "stored": stored}
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4a-chair-windows-{tag}.png"))

                    # C2b: the screen title names the front Chair window after a
                    # press on each one (Astra, #730: it read the Dock-only list).
                    named = {}
                    for name in CHAIR:
                        shell(name).locator(".desk-pullout-title").click()
                        page.wait_for_timeout(250)
                        named[name] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    facts["screen-title-after-press"] = named
                    if any(named[n] != n for n in CHAIR):
                        failures["chair-windows"]["C2 the screen title names each front Chair window"] = named
                    shell("Needs you").locator(".desk-pullout-title").click()

                    # C1-4c: Close closes. PHILO-14 A1 (board A-1): the Chair is
                    # the screen of objects, so no reopen Button stands in its place.
                    shell("Brief").get_by_role("button", name="Close Brief").click()
                    shell("Brief").wait_for(state="detached")
                    frame, chair = self._measure(page, width, "chair-window-closed", facts)
                    failures["chair-window-closed"] = self._fails(frame, chair, width)
                    if "Brief" in chair["windows"] or chair["reopen"]:
                        failures["chair-window-closed"]["C3 close closes; the screen stands"] = {
                            "windows": chair["windows"], "reopen": chair["reopen"]}
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4c-chair-window-closed-{tag}.png"))

                    # C1-4d: Window ▸ Chair, a check on each open one
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").hover()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()
                    # PHILO-16: the Window menu's verbs (Stage carries a check)
                    # sit above; the Chair's windows are their own list, the
                    # Window ▸ Chair submenu. Read that list only.
                    rows = page.evaluate("""() => {
                        // The innermost list holding the Chair rows (a submenu
                        // nests inside the Window list).
                        const list = [...document.querySelectorAll('.desk-menu-list')]
                          .filter((l) => [...l.querySelectorAll('[role="menuitemcheckbox"]')]
                            .some((e) => e.textContent.includes('Needs you'))).pop();
                        return [...(list ? list.querySelectorAll('[role="menuitemcheckbox"]') : [])]
                          .map((e) => [e.textContent.trim(), e.getAttribute('aria-checked')]); }""")
                    facts["window-menu-chair"] = rows
                    want = [["Needs you", "true"], ["Brief", "false"], ["The week", "true"], ["Capture", "true"]]
                    frame, chair = self._measure(page, width, "window-menu-chair", facts)
                    failures["window-menu-chair"] = self._fails(frame, chair, width)
                    if [[t.replace("✓", "").strip(), c] for t, c in rows] != want:
                        failures["window-menu-chair"]["C3 Window ▸ Chair checks the open ones"] = rows
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4d-window-menu-chair-{tag}.png"))
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                    shell("Brief").wait_for()
                    frame, chair = self._measure(page, width, "chair-window-reopened", facts)
                    failures["chair-window-reopened"] = self._fails(frame, chair, width)
                    if frame["screen"] != "Brief" or chair["reopen"]:
                        failures["chair-window-reopened"]["C3 reopened in front"] = {
                            "screen": frame["screen"], "reopen": chair["reopen"]}
                    # PHILO-14 A1: the screen's Needs you drawer reopens its window
                    shell("Needs you").get_by_role("button", name="Close Needs you").click()
                    shell("Needs you").wait_for(state="detached")
                    page.locator(".desk-screen [data-object-id='drawer:needs']").press("Enter")
                    shell("Needs you").wait_for()
                    # a press on a window brings it to the front (one blue)
                    shell("Needs you").locator(".desk-pullout-title").click()
                    frame, chair = self._measure(page, width, "needs-front", facts)
                    failures["needs-front"] = self._fails(frame, chair, width)
                    if frame["blue"] != ["Needs you"]:
                        failures["needs-front"]["C2 the pressed window is the blue one"] = frame["blue"]
                else:
                    # C1-6a: one window at a time, Needs you first
                    frame, chair = self._measure(page, width, "phone-desk", facts)
                    failures["phone-desk"] = self._fails(frame, chair, width)
                    if chair["windows"] != ["Needs you"]:
                        failures["phone-desk"]["C4 one window, Needs you first"] = chair["windows"]
                        self._stop(facts, failures, tag)
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-6a-phone-desk-{tag}.png"))

                    # C2b (393): the screen title names the one Chair window
                    named = {"Needs you": page.get_by_test_id("desk-screen-title").inner_text().strip()}

                    # C1-4a (393): Go ▸ Brief (PHILO-14 A1 #939: the Chair's
                    # windows are Go's first rows, two taps)
                    self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()
                    # PHILO-16: the Window menu's verbs (Stage carries a check)
                    # sit above; the Chair's windows are their own list, the
                    # Window ▸ Chair submenu. Read that list only.
                    rows = page.locator(".desk-verbbar-menu .desk-menu-label").all_inner_texts()
                    rows = [name for name in rows if name in CHAIR]
                    facts["go-chair"] = rows
                    # Brief is a command into Today rather than a checked
                    # Chair-window row; the four owner-facing doors stay.
                    if rows != CHAIR:
                        failures["phone-desk"]["C4 Go has the four Chair rows"] = rows
                    page.keyboard.press("Escape")
                    brief = open_chair_window(page, "Brief")
                    brief_name = brief.get_attribute("aria-label")
                    frame, chair = self._measure(page, width, "chair-windows", facts)
                    failures["chair-windows"] = self._fails(frame, chair, width)
                    if chair["usable_windows"] != [brief_name]:
                        failures["chair-windows"]["C4 one window at a time"] = chair["phone_panes"]
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4a-chair-windows-{tag}.png"))
                    named["Brief"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    open_chair_window(page, "The week")
                    page.wait_for_timeout(250)
                    named["The week"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    open_chair_window(page, "Brief")

                    # C1-4c (393): close gives the work area to the next Chair window
                    # A restored pullout flies back from its Dock chip. Measure
                    # the settled control before sending the original touch.
                    _settle(page)
                    back = shell("Brief").get_by_role("button", name=f"Back from {brief_name}", exact=True)
                    facts["brief-back-target"] = back.evaluate(WHOLE)
                    assert facts["brief-back-target"]["full"] and facts["brief-back-target"]["hit"], facts["brief-back-target"]
                    back.evaluate("""el => el.addEventListener('click', event => {
                        window.__chairBackTap = {trusted: event.isTrusted,
                            label: event.currentTarget.getAttribute('aria-label')};
                    }, {once: true})""")
                    self._press(page, back, width)
                    facts["brief-back-event"] = page.evaluate("window.__chairBackTap")
                    assert facts["brief-back-event"] == {"trusted": True, "label": f"Back from {brief_name}"}
                    shell("Brief").wait_for(state="detached")
                    frame, chair = self._measure(page, width, "chair-window-closed", facts)
                    failures["chair-window-closed"] = self._fails(frame, chair, width)
                    if len(chair["windows"]) != 1 or brief_name in chair["windows"]:
                        failures["chair-window-closed"]["C4 the next Chair window takes the work area"] = chair["windows"]
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4c-chair-window-closed-{tag}.png"))

                    # Capture on demand from the Speak AppIcon
                    self._press(page, page.locator(".desk-dock").get_by_role("button", name="Capture", exact=True), width)
                    shell("Capture").wait_for()
                    frame, chair = self._measure(page, width, "capture-from-speak", facts)
                    failures["capture-from-speak"] = self._fails(frame, chair, width)
                    verbs = self._verbs(page)
                    facts["capture-verbs"] = verbs["capture"]
                    page.wait_for_timeout(250)
                    named["Capture"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    facts["screen-title-per-window"] = named
                    if any(named[n] != (brief_name if n == "Brief" else n) for n in CHAIR):
                        failures["capture-from-speak"]["C2 the screen title names the shown Chair window"] = named
                    if chair["windows"] != ["Capture"] or verbs["capture"] != 3:
                        failures["capture-from-speak"]["C4 Speak opens Capture"] = {
                            "windows": chair["windows"], "capture": verbs["capture"]}

                    # C4b (Muad'Dib's ruling): ONLY the Dock's Speak AppIcon opens
                    # Capture; Go ▸ Speak (the verb, the menu, ⌘1) keeps opening the
                    # Speak (dictation) window, so it stays reachable from the Chair.
                    # PHILO-15 11 (B21, owner ruling 2026-10-07): Speak is not in the
                    # phone Go; at 393 the Speak verb is one Search away.
                    self._press(page, page.locator("button[aria-controls=desk-tool-shelf]"), width)
                    page.locator("input[aria-controls=desk-palette-listbox]").fill("Speak")
                    go_speak = page.locator("[id='desk-palette-option-go.dictate']")
                    go_speak.first.wait_for()
                    self._press(page, go_speak.first, width)
                    try:
                        page.locator(".desk-window-shell[aria-label='Speak']").wait_for(timeout=8_000)
                    except Exception:  # noqa: BLE001 -- the fence below names what opened instead
                        pass
                    page.wait_for_timeout(400)
                    go = {"speak_window": page.locator(".desk-window-shell[aria-label='Speak']").count(),
                          "screen": page.get_by_test_id("desk-screen-title").inner_text().strip()}
                    facts["go-speak"] = go
                    if go["speak_window"] != 1 or go["screen"] != "Speak":
                        failures["capture-from-speak"]["C4b the Speak verb opens the Speak window"] = go
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (H1_SHOTS / f"chair-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()
