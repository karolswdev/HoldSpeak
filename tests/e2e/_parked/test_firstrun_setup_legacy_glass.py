"""Parked legacy multi-card Setup glass walk.

The active proof lives in ``tests/e2e/test_firstrun_glass.py`` and covers
the current one-face Setup lifecycle. This source remains here for history;
its old selectors and Continue-later journey are not an active contract.
"""
from __future__ import annotations

__test__ = False

# The retained function intentionally uses the original shared rig names.
# Importing this parked source must not probe the owner HOME or run a test.
from tests.e2e.test_firstrun_glass import *  # noqa: F401,F403,E402

@pytest.mark.skip(reason="Parked retired multi-card first-run walk; test_setup_face_uses_everything_adds_people_and_leaves_for_the_desk covers the current face.")
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_first_run_one_screen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
    _ensure_build()
    import holdspeak.calendar_ingest_conductor as ingest
    import holdspeak.web_server as web_server

    now = datetime.now(timezone.utc)
    atlas = now + timedelta(minutes=90)
    eventkit = FakeEventKit(_ics("Work", [("atlas-1", "Atlas weekly", atlas)]))
    eventkit.install(monkeypatch)
    ics = IcsServer(tmp_path, _ics("Team", [("review-1", "Design review", now + timedelta(days=1))]))
    monkeypatch.setenv("SSL_CERT_FILE", str(ics.cert))
    # The ingest the hub's heartbeat runs; "Use it" asks it for one refresh.
    monkeypatch.setattr(ingest, "_conductor", ingest.CalendarIngestConductor())

    original = web_server.WebRuntimeCallbacks
    monkeypatch.setattr(web_server, "WebRuntimeCallbacks",
                        lambda **kwargs: original(**kwargs, on_transcribe=lambda audio, **_: WORDS))
    source = Source()
    source.hold.set()  # every model downloads whole
    _real_local_ai(monkeypatch, source)
    runner = Runner()
    _sign_ins(tmp_path / "home", monkeypatch, tmp_path)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=runner, acli_runner=runner)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    out = Path(os.environ.get("FIRSTRUN_SHOTS") or tmp_path / "shots")
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(15_000)

            def shot(name: str, target: Any = None) -> None:
                page.wait_for_timeout(400)
                if target is not None and width < 720:
                    target.scroll_into_view_if_needed()
                path = out / f"onb-A-{name}-{width}.png"
                page.screenshot(path=str(path), full_page=width < 720)
                print("SHOT", path)

            page.goto(f"{base}/?token={TOKEN}")
            page.get_by_test_id("firstrun").wait_for(timeout=30_000)
            _expand_first_use_setup(page)
            cal = page.get_by_test_id("firstrun-calendar")
            conn = page.get_by_test_id("firstrun-connections")

            # ── load: the detect reads only; no prompt, no link read, no probe ──
            ask = cal.get_by_role("button", name="Allow calendar access", exact=True)
            expect(ask).to_be_visible()
            expect(cal.get_by_test_id("firstrun-calendar-ask").locator(".gadget-chip-egress")).to_have_count(0)  # passive same-device work has no egress badge
            expect(conn.get_by_role("status", name="SIGNED IN · 3")).to_be_visible()
            assert eventkit.prompts == 0 and ics.requests == [] and runner.calls == []
            chips = conn.locator(".gadget-chip-egress").all_inner_texts()
            assert chips == ["GITHUB.COM", SITE.upper(), SITE.upper()], chips

            # ── C1: local AI, his name, his first sentence, kept ──
            page.get_by_test_id("firstrun-local-ai").get_by_role(
                "button", name="Set up local AI · 149 MB", exact=True).click()
            you = page.get_by_test_id("firstrun-you")
            with page.expect_response(lambda r: r.url.endswith("/api/settings") and r.request.method == "PUT"):
                you.get_by_role("textbox", name="Your name", exact=True).fill("Karol Sane")
            words = page.get_by_test_id("firstrun-first-words")
            dictate = words.get_by_role("button", name="◖ Dictate one sentence")
            expect(dictate).to_be_enabled(timeout=30_000)
            dictate.click()
            stop = words.get_by_role("button", name="Stop listening", exact=True)
            page.wait_for_timeout(1200)
            stop.click()
            words.get_by_role("button", name="Keep as note", exact=True).click()
            expect(page.get_by_role("heading", name="Get ready")).to_be_visible()
            expect(page.get_by_test_id("firstrun-local-ai").get_by_text(
                "3 MODELS · 149 MB · FROM HUGGINGFACE.CO")).to_be_visible(timeout=30_000)

            # ── Calendar: lit; the prompt only on his press ──
            expect(cal).to_have_attribute("data-lit", "true")
            ask.click()
            expect(cal.get_by_role("status", name="FOUND · 1")).to_be_visible()
            assert eventkit.prompts == 1
            work = cal.locator("li", has_text="Work")
            expect(work).to_contain_text(EMAIL)
            expect(work.locator(".gadget-chip-egress")).to_have_count(0)

            # a link the hub cannot read: CAN'T READ · SERVER REFUSED
            field = cal.get_by_role("textbox", name="Calendar URL", exact=True)
            field.fill(f"{ics.base}/gone.ics")
            # PHILO-17 runsonwords (#1083): a loopback host is THIS DEVICE.
            expect(cal.locator(".firstrun-field .gadget-chip-egress")).to_have_count(0)
            shot("cal", cal)
            cal.get_by_role("button", name="Add", exact=True).click()
            failed = cal.get_by_test_id("firstrun-calendar-cant-read")
            expect(failed.get_by_role("status", name="CAN'T READ")).to_be_visible()
            expect(failed).to_contain_text("SERVER REFUSED")
            assert ics.requests == ["/gone.ics"]
            shot("cal-failed", cal)

            # a good link: read once, then in use; its host on its row
            field.fill(f"webcal://127.0.0.1:{ics.base.rsplit(':', 1)[1]}/team.ics")
            with page.expect_response(lambda r: r.url.endswith("/api/onboarding/calendar/use")) as used:
                cal.get_by_role("button", name="Add", exact=True).click()
            assert used.value.ok, used.value.text()
            # Add read the link once before Use it; the ingest that Use it
            # starts may read it again in the background.
            assert ics.requests[:2] == ["/gone.ics", "/team.ics"], ics.requests
            team = cal.locator("li", has_text="Team")
            expect(team.get_by_role("status", name="IN USE")).to_be_visible()
            expect(team.locator(".gadget-chip-egress")).to_have_text("127.0.0.1")
            expect(cal.get_by_role("textbox", name="Calendar URL")).to_have_count(0)

            # today's macOS calendar (read 2 s later): Use it -> IN USE; the
            # receipt names TODAY's meeting, not tomorrow's, once the read lands
            expect(cal.locator(".surface-receipt")).to_contain_text("NEXT DESIGN REVIEW", timeout=15_000)
            cal.get_by_role("button", name="Use Work", exact=True).click()
            expect(work.get_by_role("status", name="IN USE")).to_be_visible()
            expect(cal.locator(".surface-receipt")).to_contain_text("NEXT ATLAS WEEKLY", timeout=15_000)
            from holdspeak.config import Config

            urls = [s.url for s in Config.load().calendar.sources]
            assert urls == [f"https://127.0.0.1:{ics.base.rsplit(':', 1)[1]}/team.ics", "eventkit:CAL-WORK-1"], urls
            expect(cal).to_have_attribute("data-selected", "true")

            # ── Connections: lit; each Use it probes its host; CONNECTED is the hub's ──
            expect(conn).to_have_attribute("data-lit", "true")
            conn.get_by_role("button", name="Use GitHub karolswdev", exact=True).click()
            expect(conn.locator("[data-provider='github']").get_by_role("status", name="CONNECTED")).to_be_visible()
            assert ["gh", "auth", "status"] in [c[:3] for c in runner.calls]
            shot("conn", conn)
            conn.get_by_role("button", name=f"Use Jira {EMAIL}", exact=True).click()
            expect(conn.locator("[data-provider='jira']").get_by_role("status", name="CONNECTED")).to_be_visible()
            conn.get_by_role("button", name=f"Use Confluence {EMAIL}", exact=True).click()

            # ── Ready ──
            ready = page.get_by_test_id("firstrun-ready")
            expect(ready.get_by_role("button", name=re.compile("Record Design review"))).to_have_count(0)
            expect(ready.get_by_role("heading", name="Ready, Karol")).to_be_visible()
            strip = [c for c in ready.get_by_test_id("ready-strip").get_by_role("status").all()]
            labels = [c.get_attribute("aria-label") for c in strip]
            assert labels[:2] == ["LOCAL AI · ON DEVICE", "HEARD · 8 WORDS"], labels
            assert re.fullmatch(r"CALENDAR · \d+ THIS WEEK|CALENDAR · IN USE", labels[2]), labels
            assert labels[3] == "SEND TO · GITHUB · JIRA · CONFLUENCE", labels
            verbs = ready.get_by_role("group", name="Start").get_by_role("button")
            expect(verbs).to_have_count(3)
            record = verbs.nth(0)
            expect(record).to_have_text(re.compile(r"Record Atlas weekly · ((MON|TUE|WED|THU|FRI|SAT|SUN) )?\d\d:\d\d"))
            expect(verbs.nth(1)).to_have_text(re.compile("Dictate"))
            expect(verbs.nth(2)).to_have_text(re.compile("Ask about this week"))
            for card in ("firstrun-local-ai", "firstrun-you", "firstrun-first-words",
                         "firstrun-calendar", "firstrun-connections"):
                expect(page.get_by_test_id(card)).to_have_attribute("data-selected", "true")
                assert page.get_by_test_id(card).get_attribute("data-lit") is None, card
            assert _display_count(page) == 1
            expect(page.get_by_role("button", name="Continue later")).to_have_count(0)
            # Nothing is cut: every verb and chip shows its whole text.
            cut = page.eval_on_selector_all(
                "[data-testid='firstrun-ready'] .surface-start-verb-word, [data-testid='ready-strip'] .surface-state-chip",
                "els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)")
            assert cut == [], cut
            page.evaluate("window.scrollTo(0, 0)")
            shot("ready")

            # ── Record arms the next meeting's recording, then the Desk ──
            with page.expect_response(lambda r: r.url.endswith("/api/scheduled-recordings")
                                      and r.request.method == "POST") as armed:
                record.click()
            assert armed.value.ok, armed.value.text()
            page.get_by_test_id("firstrun").wait_for(state="detached", timeout=15_000)
            schedules = _api(page, "GET", "/api/scheduled-recordings", token=TOKEN)["schedules"]
            assert [s.get("title") for s in schedules] == ["Atlas weekly"], schedules
            browser.close()
    finally:
        server.stop()
        source.close()
        ics.close()


@pytest.mark.skip(reason="Parked legacy card walk; the current Setup face walk covers both sizes.")
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_speech_and_first_words_stay_in_reach(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
    """First-use composition and pointer ownership, without capture/download."""
    from playwright.sync_api import sync_playwright
    from tests._evidence import evidence_dir
    from .test_settings_glass import _pointer_owned
    from .type_floor_rig import _MEASURE

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token="first-use-layout")
    out = evidence_dir("surface-repair-first-use")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/welcome?token=first-use-layout", wait_until="load")
            speech = page.get_by_test_id("firstrun-speech-verb")
            speech.wait_for(timeout=20_000)
            page.wait_for_timeout(600)
            exit_verb = page.get_by_role("button", name="Continue later", exact=True)
            words = page.get_by_test_id("firstrun-first-words")
            initial = page.locator(".firstrun").evaluate("""el => {
              const r = name => el.querySelector(name).getBoundingClientRect().toJSON();
              return {speech:r('[data-testid="firstrun-speech-card"]'), words:r('[data-testid="firstrun-first-words"]'),
                folds:[...el.querySelectorAll('.firstrun-chat,.firstrun-optional')].map(x=>x.open)};
            }""")
            page.screenshot(path=str(out / f"first-use-{width}.png"))
            assert initial["words"]["bottom"] < height, initial
            assert initial["folds"] == [False, False], initial
            assert "144 MB" in speech.inner_text(), speech.inner_text()
            # First use is outside the window host; it must still use the
            # readable Workbench ink for the download's egress badge.
            ink = page.evaluate(_MEASURE, "#8b93a3")
            egress_faults = [row for row in ink["contrast"] if "gadget-chip-egress" in row["path"]]
            assert not egress_faults, egress_faults
            _pointer_owned(page, speech, "Set up speech", scrolled=True)
            _pointer_owned(page, exit_verb, "Continue later", scrolled=True)
            page.locator(".firstrun-optional > summary").click()
            page.get_by_test_id("firstrun-agents").scroll_into_view_if_needed()
            _pointer_owned(page, exit_verb, "Continue later after optional setup scroll", scrolled=True)
            page.screenshot(path=str(out / f"first-use-optional-{width}.png"))
            assert errors == [], errors
            browser.close()
    finally:
        server.stop()
