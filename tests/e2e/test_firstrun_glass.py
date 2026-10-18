"""The first run in a real browser (the firstrun app's browser file).

Renamed from test_firstrun_one_screen_glass.py (the test diet, push 2,
2026-10-12). Both tests need a real browser: the dictation step records
through the browser's microphone stream (getUserMedia, Chromium's fake
device playing a WAV; jsdom has no media capture), and the second test
reloads the page between two kept notes. The cards' faces are also
web/src/desk/firstrun/__tests__/firstrun.app.test.tsx and FirstRun.test.tsx;
the hub routes are tests/integration/test_desk_firstrun.py.

First run, option A "One screen" (owner ratified 2026-10-05) on the real hub.

Canvas YDTpkaJqFs3hyrZ4g581Mx §1, artboards onb-A-{cal,conn,ready}. Calendar
and Connections are two more cards on the C1 first-run screen; when every
step is done, Ready goes to the top with three verbs from his own data.

Every read and write is the real hub (PR #868's onboarding routes, the
settings, connections, calendar ingest, Door and scheduled-recording
services). Only the leaves are fixtures, all inside the isolated HOME:

* EventKit: ``holdspeak.macos_calendar``'s four calls are replaced (one
  calendar, "Work"; its events as ICS). No real macOS permission is read
  and no prompt can show.
* The calendar link: an HTTPS server on 127.0.0.1 with a self-signed
  certificate the hub trusts through ``SSL_CERT_FILE``.
* gh / acli: their config files under the isolated HOME (``GH_CONFIG_DIR``
  and ``XDG_CONFIG_HOME`` unset, so the owner's real config is never read),
  stub executables on PATH, and the canned runners the other connections
  glass tests use.
* Local AI and the first sentence: the C1 glass rig
  (``test_firstrun_heard_glass``).

The flow, at 1440 and 393: C1 done -> Calendar lit; the macOS prompt only
on his press; a link the hub cannot read (CAN'T READ · SERVER REFUSED); a
good link (its host named once typed) -> IN USE; the macOS calendar ->
IN USE -> Connections lit; GitHub, Jira, Confluence -> CONNECTED -> Ready,
Karol; Record <next meeting> arms its recording and opens the Desk.

Also here (lane e2e-high-1):

First run in a real browser: the real local-AI service, a fake mic device
and the real media tracks.

Kept by the test diet (push 2, 2026-10-12), one file for the First-run app.
Was tests/e2e/test_firstrun_heard_glass.py; its blocked-mic leg is
web/src/desk/firstrun/__tests__/FirstRun.test.tsx.

First run "C1 · Heard first" (owner ratified 2026-10-05) on the real hub.

A cold isolated HOME opens on the first-run face. Every read and write is
the real hub, "Set up local AI" included: the merged #856 service
(`LocalAISetupService`, GET/POST /api/setup/local-ai) runs whole. Only its
leaves are replaced, the way #856's own fences replace them
(tests/unit/test_local_ai_setup.py): the pinned files are small blobs
served by a file server on this device (the real pins name 3 GB on
huggingface.co), and the runtime-readiness probe says ready (the blob is
not a loadable model). The download, the per-file `on_device` reads, the
one egress receipt, the stop and the resume are the service's own.

The owner's name goes through `PUT /api/settings`, the first sentence
through the real dictation socket (Chromium's fake device plays a WAV; the
hub's transcriber is a fixture), and Keep as note through `POST /api/notes`.

The flow, at 1440 and 393: before -> running (First words lights when the
Whisper files land, while the chat model still downloads) -> stopped
(the connection drops) -> Try again resumes -> ready -> listening ->
writing -> heard (his words at the display step) -> Keep as note creates
the note and the face stays (option A "One screen": Calendar and
Connections are next) -> Open my desk opens the Desk (PHILO-17).

Shots go to $FIRSTRUN_SHOTS when it is set (the owner's comparison page),
else to the test's tmp folder.
"""
from __future__ import annotations

import os
import re
import ssl
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import SPEECH_CAPABILITY, _api, _boot, _ensure_build, assign_engine, engine_profile


def _expand_first_use_setup(page: Any) -> None:
    """Existing media/account flows explicitly enter the optional setup wells."""
    page.locator(".firstrun-chat, .firstrun-optional").evaluate_all("els => els.forEach(el => { el.open = true; })")


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

pytest.importorskip("playwright.sync_api", reason="first-run glass needs Playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402
import functools
import hashlib
import json
from types import SimpleNamespace
from .glass_infra import REPO

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

EMAIL = "karol@acme.com"
SITE = "acme.atlassian.net"


def _ics(name: str, events: list[tuple[str, str, datetime]]) -> bytes:
    stamp = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//glass//EN", f"X-WR-CALNAME:{name}"]
    for uid, title, start in events:
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp(start)}", f"DTSTART:{stamp(start)}",
                  f"DTEND:{stamp(start + timedelta(minutes=30))}", f"SUMMARY:{title}", "END:VEVENT"]
    return ("\r\n".join(lines + ["END:VCALENDAR", ""])).encode()


class FakeEventKit:
    """The four EventKit calls the hub makes. The prompt is counted, never shown."""

    def __init__(self, ics: bytes) -> None:
        self.state = "not_determined"
        self.prompts = 0
        self.ics = ics
        self.delay = 2.0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import holdspeak.macos_calendar as macos

        monkeypatch.setattr(macos, "access_state", lambda: self.state)
        monkeypatch.setattr(macos, "request_access", self.request_access)
        monkeypatch.setattr(macos, "list_calendars", self.list_calendars)
        monkeypatch.setattr(macos, "read_calendar_ics", self.read_calendar_ics)

    def read_calendar_ics(self, source: str, **_: Any) -> bytes:
        # Astra #876 P2: today's calendar reads slowly; tomorrow's link is
        # already on the Door. Ready must wait for this read.
        time.sleep(self.delay)
        return self.ics

    def request_access(self, timeout: float = 120.0) -> str:
        self.prompts += 1
        self.state = "full_access"
        return self.state

    def list_calendars(self) -> list[dict[str, Any]]:
        if self.state != "full_access":
            return []
        return [{"id": "CAL-WORK-1", "title": "Work", "account": EMAIL, "kind": "caldav"}]


class IcsServer:
    """HTTPS on 127.0.0.1: /team.ics is a calendar; anything else is 404."""

    def __init__(self, tmp: Path, ics: bytes) -> None:
        cert, key = tmp / "ics-cert.pem", tmp / "ics-key.pem"
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-keyout", str(key),
             "-out", str(cert), "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1"],
            check=True, capture_output=True,
        )
        self.cert = cert
        self.requests: list[str] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                server.requests.append(self.path)
                if self.path != "/team.ics":
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/calendar")
                self.send_header("Content-Length", str(len(ics)))
                self.end_headers()
                self.wfile.write(ics)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cert), str(key))
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"https://127.0.0.1:{self.server.server_address[1]}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class Runner:
    """The canned gh / acli answers (the shape test_philo9_b1 uses)."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(
                argv, 0, stdout="Logged in to github.com account karolswdev (keyring)\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "switch"]:
            return subprocess.CompletedProcess(argv, 0, stdout="switched\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "status"]:
            return subprocess.CompletedProcess(
                argv, 0, stdout=f"✓ Authenticated\n  Site: {SITE}\n  Email: {EMAIL}\n", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected")


def _sign_ins(home: Path, monkeypatch: pytest.MonkeyPatch, tmp: Path) -> None:
    """gh and acli sign-ins as files under the isolated HOME; stubs on PATH."""
    monkeypatch.delenv("GH_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    gh = home / ".config" / "gh"
    gh.mkdir(parents=True, exist_ok=True)
    (gh / "hosts.yml").write_text(
        "github.com:\n    users:\n        karolswdev:\n    git_protocol: https\n    user: karolswdev\n",
        encoding="utf-8")
    acli = home / ".config" / "acli"
    acli.mkdir(parents=True, exist_ok=True)
    profile = (f"current_profile: cloud-1:acct-1\nprofiles:\n  - site: {SITE}\n    email: {EMAIL}\n"
               "    cloud_id: cloud-1\n    account_id: acct-1\n    display_name: Karol Sane\n    auth_type: oauth\n")
    for product in ("jira", "confluence"):
        (acli / f"{product}_config.yaml").write_text(profile, encoding="utf-8")
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    for tool in ("gh", "acli"):
        stub = bin_dir / tool
        stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")


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


def test_a_reload_after_keep_never_replaces_the_kept_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Astra #876 P1, her sequence through the real note producer: dictate A,
    Keep as note, reload, dictate B, Keep as note -> two notes, A and B."""
    _ensure_build()
    import holdspeak.web_server as web_server

    sentences = iter([WORDS, "Book the room for the Atlas review."])
    original = web_server.WebRuntimeCallbacks
    monkeypatch.setattr(web_server, "WebRuntimeCallbacks",
                        lambda **kwargs: original(**kwargs, on_transcribe=lambda audio, **_: next(sentences)))
    source = Source()
    source.hold.set()
    _real_local_ai(monkeypatch, source)
    monkeypatch.delenv("GH_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.set_default_timeout(15_000)
            page.goto(f"{base}/?token={TOKEN}")
            page.get_by_test_id("firstrun").wait_for(timeout=30_000)
            _expand_first_use_setup(page)
            page.get_by_test_id("firstrun-local-ai").get_by_role(
                "button", name="Set up local AI · 149 MB", exact=True).click()

            def keep_one(text: str) -> None:
                words = page.get_by_test_id("firstrun-first-words")
                dictate = words.get_by_role("button", name="◖ Dictate one sentence")
                expect(dictate).to_be_enabled(timeout=30_000)
                dictate.click()
                page.wait_for_timeout(1000)
                words.get_by_role("button", name="Stop listening", exact=True).click()
                expect(words.get_by_test_id("heard-quote").locator("blockquote")).to_have_text(f"“{text}”")
                with page.expect_response(lambda r: r.url.endswith("/api/notes") and r.request.method == "POST") as made:
                    words.get_by_role("button", name="Keep as note", exact=True).click()
                assert made.value.ok, made.value.text()

            keep_one(WORDS)
            page.reload()
            page.get_by_test_id("firstrun").wait_for(timeout=30_000)
            _expand_first_use_setup(page)
            keep_one("Book the room for the Atlas review.")
            notes = _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
            bodies = sorted(n["body_markdown"] for n in notes if "dictation" in (n.get("tags") or []))
            assert bodies == sorted([WORDS, "Book the room for the Atlas review."]), notes
            browser.close()
    finally:
        server.stop()
        source.close()


# ══ lane e2e-high-1 ════════════════════════════════════════

TOKEN = "firstrun-c1"

WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"

WORDS = "Send the cutover plan to Priya before Friday."

MB = 1_000_000

WHISPER_REPO = "mlx-community/whisper-base-mlx"

STARTER_PATH = "/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_K_M.gguf"

def _blob(tag: bytes, size: int, magic: bytes = b"") -> bytes:
    return (magic + tag * (size // len(tag) + 1))[:size]

@functools.cache
def _pins() -> SimpleNamespace:
    """Small pinned blobs (#856's fence shape), sized so the face reads true."""
    from holdspeak.memory.local_model import PinnedModel
    from holdspeak.services.local_ai_setup_service import STARTER_PRESET_ID

    def pin(repository: str, filename: str, content: bytes, magic: bytes, label: str) -> PinnedModel:
        return PinnedModel(
            name=filename, label=label, repository=repository, revision="r1", filename=filename,
            sha256=hashlib.sha256(content).hexdigest(), size=len(content), license="MIT",
            architecture="test", context_ceiling=2048, magic=magic,
        )

    config, weights = b'{"model_type": "whisper"}', _blob(b"whisper-weights-", 14 * MB)
    embed, starter = _blob(b"embed-", 15 * MB, b"GGUF"), _blob(b"starter-", 120 * MB, b"GGUF")
    whisper = (pin(WHISPER_REPO, "config.json", config, b"", "whisper-base-mlx"),
               pin(WHISPER_REPO, "weights.npz", weights, b"", "whisper-base-mlx"))
    embed_pin = pin("nomic-ai/nomic-embed-text-v1.5-GGUF", "nomic-embed-text-v1.5.Q8_0.gguf", embed, b"GGUF",
                    "nomic-embed-text v1.5")
    starter_sha = "sha256:" + hashlib.sha256(starter).hexdigest()
    manifest = {"files": [{"path": "Qwen3.5-4B-Q4_K_M.gguf", "sha256": starter_sha, "size": len(starter)}]}
    manifest_sha = "sha256:" + hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    catalog = {"catalog_revision": 9, "entries": [{
        "id": STARTER_PRESET_ID, "label": "Qwen3.5 4B",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
        "source": {"repository": "unsloth/Qwen3.5-4B-GGUF", "revision": "r1",
                   "filename": "Qwen3.5-4B-Q4_K_M.gguf", "file_sha256": starter_sha,
                   "manifest_sha256": manifest_sha, "download_bytes": len(starter),
                   "installed_bytes": len(starter), "peak_free_bytes": len(starter) * 2,
                   "license": "Apache-2.0"},
    }]}
    files = {f"/{WHISPER_REPO}/config.json": config, f"/{WHISPER_REPO}/weights.npz": weights,
             f"/{embed_pin.repository}/{embed_pin.filename}": embed, STARTER_PATH: starter}
    return SimpleNamespace(whisper=whisper, embed=embed_pin, catalog=catalog, files=files)

class Source:
    """The model host, on this device. The chat model's first answer sends
    half its bytes, then holds until the rig releases it; `drop` ends that
    answer short (the connection drops). A resume (Range) answers whole."""

    def __init__(self) -> None:
        self.files = _pins().files
        self.hold = threading.Event()
        self.drop = False
        self.requests: list[tuple[str, str]] = []
        source = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                header = self.headers.get("Range", "")
                source.requests.append((self.path, header))
                body = source.files.get(self.path)
                if body is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                start = int(header[6:].split("-")[0]) if header.startswith("bytes=") else 0
                if start:
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")
                else:
                    self.send_response(200)
                rest = body[start:]
                self.send_header("Content-Length", str(len(rest)))
                self.end_headers()
                if self.path == STARTER_PATH and not start:
                    half = len(rest) // 2
                    self.wfile.write(rest[:half])
                    self.wfile.flush()
                    source.hold.wait(60)
                    if source.drop:
                        return  # short answer: the client reads a broken download
                    rest = rest[half:]
                self.wfile.write(rest)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def url_for(self, model: Any) -> str:
        return f"{self.base}/{model.repository}/{model.filename}"

    def close(self) -> None:
        self.hold.set()
        self.server.shutdown()
        self.server.server_close()

def _real_local_ai(monkeypatch: pytest.MonkeyPatch, source: Source) -> None:
    """The hub builds the REAL #856 service; only its leaves point here."""
    from holdspeak.services import local_ai_setup_service as module
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.meaning_search_service import MeaningSearchService
    from holdspeak.services.model_profile_service import ModelProfileService

    pins = _pins()
    allowed = lambda host: host == "127.0.0.1"  # noqa: E731
    monkeypatch.setattr(ModelProfileService, "_local_runtime_readiness",
                        staticmethod(lambda runtime_id: ("ready", "ready")))
    monkeypatch.setattr("holdspeak.whisper_models._PINNED", {("mlx", "base"): pins.whisper})
    real = module.LocalAISetupService

    def build(db: Any, *, meaning_search: Any, broker_provider: Any = None, **_: Any) -> Any:
        meaning = MeaningSearchService(
            db, assignment_service=InferenceAssignmentService(db), broker_provider=broker_provider,
            model=pins.embed, source_url=source.url_for(pins.embed), allowed_host=allowed,
            wake=lambda: None,
        )
        return real(
            db, meaning_search=meaning, broker_provider=broker_provider,
            config_provider=lambda: SimpleNamespace(model=SimpleNamespace(name="base", backend="mlx")),
            catalog_provider=lambda: pins.catalog, url_for=source.url_for, allowed_host=allowed,
        )

    monkeypatch.setattr(module, "LocalAISetupService", build)

def _seed_lan_proposal(monkeypatch: pytest.MonkeyPatch) -> str:
    """One ready LAN engine, stored as a proposal by #855's own producer
    (`InferenceDefaultService._record_proposals`); detection is the leaf."""
    from holdspeak.db import get_database
    from holdspeak.services import concierge_service
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.inference_default_service import InferenceDefaultService

    from .glass_infra import ENGINE_PROFILE

    engine = {
        "id": f"lan:{ENGINE_PROFILE}", "kind": concierge_service.KIND_LAN, "name": "qwen3.8-27b",
        "host": "192.168.1.43", "state": concierge_service.STATE_READY,
        "baseUrl": "http://192.168.1.43:8080/v1", "profileId": ENGINE_PROFILE, "profileRevision": 1,
    }
    monkeypatch.setattr(concierge_service, "detect", lambda **_: {"engines": [engine]})
    db = get_database()
    service = InferenceDefaultService(db, assignment_service=InferenceAssignmentService(db))
    assert service._record_proposals() == 1
    return engine["id"]

def _no_cut(page: Any, selector: str) -> list[str]:
    """Every matching label whose text is cut (scrollWidth > clientWidth)."""
    return page.eval_on_selector_all(
        selector, "els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)")

def _display_count(page: Any) -> int:
    """Elements on the face drawn at the display step (26 px, weight 650)."""
    return page.eval_on_selector_all(
        "[data-testid='firstrun'] *",
        """els => els.filter(e => {
            const s = getComputedStyle(e);
            const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
            return own && s.fontSize === '26px' && s.fontWeight === '650';
        }).length""")

@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_first_run_heard_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
    _ensure_build()
    import holdspeak.web_server as web_server

    gate = threading.Event()
    heard: list[int] = []
    original = web_server.WebRuntimeCallbacks

    def transcribe(audio: Any, **_: Any) -> str:
        import numpy as np

        assert np.asarray(audio).size, "the hub got no audio"
        heard.append(1)
        assert gate.wait(30), "the rig never released the transcript"
        return WORDS

    monkeypatch.setattr(web_server, "WebRuntimeCallbacks",
                        lambda **kwargs: original(**kwargs, on_transcribe=transcribe))
    source = Source()
    _real_local_ai(monkeypatch, source)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    # This profile becomes the global AI default below. Qualify the fixture
    # for the provider routes the speech-session admission freezes too.
    from holdspeak.db import get_database
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
    from .glass_infra import ENGINE_PROFILE, SUMMARY_CAPABILITY

    _profile(get_database(), ENGINE_PROFILE, claims=(
        "language", "structured_output", _result_claim(SUMMARY_CAPABILITY),
        _result_claim(SPEECH_CAPABILITY), _result_claim("speech.intent_classify"),
        _result_claim("speech.rewrite"),
    ), modalities=("language", "text", "audio"))
    assign_engine(SPEECH_CAPABILITY, 1)
    proposal_id = _seed_lan_proposal(monkeypatch)
    out = Path(os.environ.get("FIRSTRUN_SHOTS") or tmp_path / "shots")
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(10_000)

            def shot(name: str) -> None:
                page.wait_for_timeout(350)
                path = out / f"C1-{name}-{width}.png"
                page.screenshot(path=str(path), full_page=width < 720)
                print("SHOT", path)

            page.goto(f"{base}/?token={TOKEN}")
            face = page.get_by_test_id("firstrun")
            face.wait_for(timeout=30_000)
            _expand_first_use_setup(page)
            local_ai = page.get_by_test_id("firstrun-local-ai")
            words = page.get_by_test_id("firstrun-first-words")

            # ── before: one press, its size, the host on the row that leaves ──
            press = local_ai.get_by_role("button", name="Set up local AI · 149 MB", exact=True)
            expect(press).to_be_visible()
            expect(local_ai.locator(".gadget-chip-egress")).to_have_text("HUGGINGFACE.CO")
            expect(words.get_by_role("button", name="Dictate one sentence")).to_be_disabled()
            expect(words.get_by_text("WAITS FOR SPEECH")).to_be_visible()
            assert _display_count(page) == 1
            # FOUND: the stored LAN proposal, its egress chip on its row.
            found = page.get_by_test_id("firstrun-found")
            expect(found).to_contain_text("qwen3.8-27b")
            expect(found).to_contain_text("LAN SERVER")
            expect(found.locator(".gadget-chip-egress")).to_have_text("192.168.1.43 · LAN")
            shot("before")

            # ── You: the name and the aliases, stored ──
            you = page.get_by_test_id("firstrun-you")
            with page.expect_response(lambda r: r.url.endswith("/api/settings") and r.request.method == "PUT"):
                you.get_by_role("textbox", name="Your name", exact=True).fill("Karol Sane")
            alias = you.get_by_role("textbox", name="Also called", exact=True)
            alias.fill("Karol")
            alias.press("Enter")
            with page.expect_response(lambda r: r.url.endswith("/api/settings") and r.request.method == "PUT"
                                      and "KS" in (r.request.post_data or "")):
                alias.fill("KS, me")
            expect(you.get_by_role("status", name="SET", exact=True)).to_be_visible()
            from holdspeak.config import Config

            owner = Config.load().owner
            assert owner.name == "Karol Sane" and owner.aliases == ["Karol", "KS", "me"], owner

            # ── running: the Whisper files land first; the chat model holds half-way ──
            words_shut = words.get_by_role("button", name="Dictate one sentence", exact=True)
            expect(words_shut).to_be_disabled()
            press.click()
            expect(local_ai.get_by_role("group", name="Local AI download")).to_be_visible()
            dictate = words.get_by_role("button", name="◖ Dictate one sentence")
            expect(dictate).to_be_enabled(timeout=20_000)
            expect(words).to_have_attribute("data-lit", "true")
            expect(words.get_by_role("status", name="SPEECH READY")).to_be_visible()
            chat = local_ai.locator("[role='listitem'][data-status='running']")
            expect(chat).to_contain_text("Chat")
            expect(chat).to_contain_text("/ 120 MB")
            done = local_ai.locator("[role='listitem'][data-status='done']")
            expect(done).to_have_count(2)
            # The Whisper files are on this device before the chat model is.
            pins = _pins()
            assert [p for p, _ in source.requests][:3] == [
                f"/{WHISPER_REPO}/config.json", f"/{WHISPER_REPO}/weights.npz",
                f"/{pins.embed.repository}/{pins.embed.filename}"], source.requests
            # The species fix: the running label is whole at every width.
            assert _no_cut(page, "[data-testid='firstrun-local-ai'] [role='listitem'] > span:nth-child(2)") == []
            expect(local_ai.get_by_role("button", name="Stop", exact=True)).to_be_visible()
            shot("running")

            # ── stopped: the connection drops; the plain reason and one verb ──
            source.drop = True
            source.hold.set()
            expect(local_ai.get_by_role("status", name="CAN'T DOWNLOAD")).to_be_visible(timeout=20_000)
            expect(local_ai.get_by_text("The download stopped. Try again to continue.")).to_be_visible()
            # Speech stays: First words is still open.
            expect(dictate).to_be_enabled()
            shot("failed")

            # ── Try again resumes the part file -> ready ──
            source.drop = False
            local_ai.get_by_role("button", name="Try again", exact=True).click()
            expect(local_ai.get_by_text("3 MODELS · 149 MB · FROM HUGGINGFACE.CO")).to_be_visible(timeout=30_000)
            assert any(p == STARTER_PATH and r.startswith("bytes=") for p, r in source.requests), source.requests
            expect(local_ai.locator(".gadget-chip-egress")).to_have_count(0)

            # ── Use it: the owner's press makes the LAN engine the default ──
            with page.expect_response(lambda r: r.url.endswith("/api/inference/defaults/use-proposal")) as used:
                found.get_by_role("button", name="Use qwen3.8-27b", exact=True).click()
            assert used.value.ok, used.value.text()
            assert used.value.request.post_data_json == {"proposal_id": proposal_id}
            expect(found.get_by_role("status", name="IN USE · DEFAULT")).to_be_visible()
            from holdspeak.db import get_database

            with get_database()._connection() as conn:
                row = conn.execute(
                    "SELECT state FROM inference_default_proposals WHERE engine_id=?", (proposal_id,)).fetchone()
            assert row["state"] == "used"

            # ── listening -> writing -> heard ──
            if width < 720:
                dictate.scroll_into_view_if_needed()
            dictate.click()
            stop = words.get_by_role("button", name="Stop listening", exact=True)
            try:
                expect(stop).to_be_visible()
            except AssertionError as error:
                raise AssertionError(f"First words after Dictate: {words.inner_text()}") from error
            expect(words.get_by_text("LISTENING")).to_be_visible()
            page.wait_for_timeout(1500)
            shot("done-1")
            stop.click()
            expect(words.get_by_text("WRITING")).to_be_visible()
            shot("done-2")
            gate.set()
            quote = words.get_by_test_id("heard-quote")
            expect(quote.locator("blockquote")).to_have_text(f"“{WORDS}”")
            expect(quote).to_contain_text("8 WORDS")
            assert heard == [1]
            # One display element: his words. The heading stepped down.
            assert _display_count(page) == 1
            assert quote.locator("blockquote").evaluate("e => getComputedStyle(e).fontSize") == "26px"
            expect(page.get_by_role("heading", name="Heard")).to_be_visible()
            expect(words.get_by_role("button", name="Again", exact=True)).to_be_visible()
            if width < 720:
                # 393: his words come first, on screen without a scroll.
                page.evaluate("window.scrollTo(0, 0)")
                box = quote.locator("blockquote").bounding_box()
                assert box and box["y"] + box["height"] <= height, box
                tops = [page.get_by_test_id(t).bounding_box()["y"]
                        for t in ("firstrun-first-words", "firstrun-local-ai", "firstrun-you")]
                assert tops[0] < tops[1] and tops[0] < tops[2], tops
            shot("done-3")

            # ── Keep as note: a real note; option A keeps the one screen
            #    (Calendar and Connections are next), then Open my desk ──
            with page.expect_response(lambda r: r.url.endswith("/api/notes") and r.request.method == "POST") as made:
                words.get_by_role("button", name="Keep as note", exact=True).click()
            assert made.value.ok, made.value.text()
            note = made.value.json()["note"]
            assert note["body_markdown"] == WORDS and note["title"] == "Send the cutover plan to Priya"
            expect(page.get_by_role("heading", name="Get ready")).to_be_visible()
            expect(words.get_by_role("button", name="Keep as note", exact=True)).to_have_count(0)
            # PHILO-17: the C1 cards are done, so the exit is "Open my desk".
            expect(page.get_by_role("button", name="Continue later", exact=True)).to_have_count(0)
            page.get_by_role("button", name="Open my desk", exact=True).click()
            page.get_by_test_id("firstrun").wait_for(state="detached", timeout=15_000)
            page.locator(".chair:not(.chair-first-value)").wait_for()
            browser.close()
    finally:
        gate.set()
        server.stop()
        source.close()

_GATED_MIC = """(() => {
  const media = navigator.mediaDevices;
  const original = media.getUserMedia.bind(media);
  let release;
  window.__gate = new Promise((resolve) => { release = resolve; });
  window.__grant = () => release();
  window.__streams = [];
  media.getUserMedia = async (constraints) => {
    await window.__gate;               // the permission prompt, pending
    const stream = await original(constraints);
    window.__streams.push(stream);
    return stream;
  };
})()"""

_LIVE_TRACKS = """() => (window.__streams || []).flatMap((s) => s.getTracks())
    .filter((t) => t.readyState === 'live').length"""

def _ready_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str, Source]:
    _ensure_build()
    source = Source()
    source.hold.set()  # no stop half-way: every model downloads whole
    _real_local_ai(monkeypatch, source)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    engine_profile()
    assign_engine(SPEECH_CAPABILITY, 1)
    return server, base, source

def _speech_ready(page: Any, base: str) -> Any:
    page.goto(f"{base}/?token={TOKEN}")
    page.get_by_test_id("firstrun").wait_for(timeout=30_000)
    _expand_first_use_setup(page)
    local_ai = page.get_by_test_id("firstrun-local-ai")
    local_ai.get_by_role("button", name="Set up local AI · 149 MB", exact=True).click()
    dictate = page.get_by_test_id("firstrun-first-words").get_by_role("button", name="◖ Dictate one sentence")
    expect(dictate).to_be_enabled(timeout=30_000)
    return dictate

@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_a_grant_after_continue_later_leaves_no_live_mic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    """Pending permission -> Continue later -> grant -> zero live tracks."""
    server, base, source = _ready_hub(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height})
            page.set_default_timeout(10_000)
            page.add_init_script(_GATED_MIC)
            dictate = _speech_ready(page, base)
            dictate.click()
            page.wait_for_timeout(300)  # the acquisition is pending
            assert page.evaluate(_LIVE_TRACKS) == 0
            page.get_by_role("button", name="Continue later", exact=True).click()
            page.get_by_test_id("firstrun").wait_for(state="detached", timeout=15_000)
            page.evaluate("window.__grant()")
            page.wait_for_function("() => window.__streams.length > 0")
            page.wait_for_timeout(500)
            assert page.evaluate(_LIVE_TRACKS) == 0, "a live microphone outlived the card"
            browser.close()
    finally:
        server.stop()
        source.close()


# ── PHILO-17 firstrun F4 and F5: the recovery doors open their windows ON
#    GLASS over first run (a real fake-device microphone; which window is on
#    top at a point). Moved from test_philo17_firstrun_glass.py (push 2 of
#    the test diet, lane e2e-low-2); its F1-F3 are vitest:
#    surface/__tests__/materialDoors.test.tsx, pages/cores/__tests__/setupCoreInfo.test.tsx,
#    firstrun/__tests__/OneScreen.test.tsx. ──

from .glass_infra import _settle, clear_hub_windows  # noqa: E402


def _row(page: Any, label: str) -> Any:
    """The menu row whose label is `label` (its name also carries a keycap)."""
    return page.locator("[role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(f"^{re.escape(label)}$"))).last


def _desk(page: Any, base: str, query: str = "") -> None:
    if not page.url.startswith(base):
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    clear_hub_windows(page, TOKEN)
    page.goto(f"{base}/?token={TOKEN}{query}", wait_until="load")
    page.locator(".chair:not(.chair-first-value)").wait_for(timeout=30_000)
    _settle(page)


# ── F4 (Astra r1 on #1085): First words' two recovery doors open a window ON
#    GLASS, on a fresh first run and on one opened again from Setup. ──

_TOGGLE_MIC = """(() => {
  const media = navigator.mediaDevices;
  const real = media.getUserMedia.bind(media);
  media.getUserMedia = async (c) => {
    if (window.__denyMic) throw new DOMException("Requested device not found", "NotFoundError");
    return real(c);
  };
})()"""

# The window is painted, and the topmost element at its centre is inside it
# (not under the first-run face).
_ON_TOP = """(el) => {
  const r = el.getBoundingClientRect();
  if (r.width < 2 || r.height < 2) return false;
  const x = Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2));
  const y = Math.min(innerHeight - 1, Math.max(0, r.top + Math.min(r.height / 2, 40)));
  const top = document.elementFromPoint(x, y);
  return !!top && el.contains(top);
}"""


def _on_glass(page: Any, selector: str) -> bool:
    loc = page.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=15_000)
    except Exception:  # noqa: BLE001
        return False
    page.wait_for_timeout(400)
    return bool(loc.evaluate(_ON_TOP))


@pytest.mark.parametrize("mode", ["fresh", "reopened"])
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_first_words_recovery_doors_open_on_glass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int, mode: str,
) -> None:
    # No on_transcribe on this hub: the speech socket answers
    # "transcription_unavailable" (the missing_model failure).
    server, base, source = _ready_hub(tmp_path, monkeypatch)

    if mode == "reopened":
        from holdspeak.db import get_database

        get_database().onboarding.set_disposition("dismissed")
    fails: dict[str, Any] = {}
    out = Path(os.environ.get("FIRSTRUN_SHOTS") or tmp_path / "shots")
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(10_000)
            page.add_init_script(_TOGGLE_MIC)
            if mode == "reopened":
                _desk(page, base)
                page.locator(".desk-mark").click()
                page.locator(".desk-menu-list").first.wait_for()
                _row(page, "Setup").click()
                page.locator("#surface-setup").get_by_role("button", name="Get ready", exact=True).click()
            else:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            page.get_by_test_id("firstrun").wait_for(timeout=30_000)
            _expand_first_use_setup(page)
            local_ai = page.get_by_test_id("firstrun-local-ai")
            local_ai.get_by_role("button", name=re.compile(r"^Set up local AI")).click()
            words = page.get_by_test_id("firstrun-first-words")
            dictate = words.get_by_role("button", name="◖ Dictate one sentence", exact=True)
            expect(dictate).to_be_enabled(timeout=60_000)

            # 1. No microphone -> "Check the microphone" -> the Setup window.
            page.evaluate("window.__denyMic = true")
            dictate.click()
            check = words.get_by_role("button", name="Check the microphone", exact=True)
            check.wait_for()
            check.click()
            if not _on_glass(page, "#surface-setup"):
                fails[f"F4 {mode} {width} Check the microphone opens Setup on glass"] = "not on glass"
            page.screenshot(path=str(out / f"P17-firstrun-{mode}-mic-{width}.png"))
            closer = page.get_by_role("button", name=re.compile(r"^(Close|Back from) Setup$"))
            if closer.count():
                closer.first.click()

            # 2. No speech model on the hub -> "Runs on" -> the Runs on window.
            page.evaluate("window.__denyMic = false")
            words.get_by_role("button", name="Again", exact=True).click()
            runs_on = words.get_by_role("button", name="Engines", exact=True)
            try:
                runs_on.wait_for(timeout=20_000)
                runs_on.click()
                if not _on_glass(page, "[data-testid='runson-root']"):
                    fails[f"F4 {mode} {width} Runs on opens on glass"] = "not on glass"
            except Exception as exc:  # noqa: BLE001
                fails[f"F4 {mode} {width} the missing model offers Runs on"] = str(exc)[:200]
            page.screenshot(path=str(out / f"P17-firstrun-{mode}-runson-{width}.png"))
            # The first run is still there behind the recovery window.
            if not page.get_by_test_id("firstrun").count():
                fails[f"F4 {mode} {width} first run stays"] = "gone"
            browser.close()
    finally:
        server.stop()
        source.close()
    assert not fails, fails


# ── F5 (Astra r2 on #1085): Runs on open BEFORE Get ready waits off glass;
#    pressing "Runs on" (the configure-runs-on alias) brings it back; leaving
#    first run keeps every window, on glass and in the hub's rows. ──
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_waiting_runs_on_comes_back_through_its_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    server, base, source = _ready_hub(tmp_path, monkeypatch)
    from holdspeak.db import get_database


    get_database().onboarding.set_disposition("dismissed")
    fails: dict[str, Any] = {}
    out = Path(os.environ.get("FIRSTRUN_SHOTS") or tmp_path / "shots")
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(10_000)
            _desk(page, base)
            # Runs on first (HoldSpeak ▸ Runs on), then Setup ▸ Get ready.
            page.locator(".desk-mark").click()
            page.locator(".desk-menu-list").first.wait_for()
            _row(page, "Engines").click()
            page.get_by_test_id("runson-root").wait_for(timeout=15_000)
            page.locator(".desk-mark").click()
            page.locator(".desk-menu-list").first.wait_for()
            _row(page, "Setup").click()
            page.locator("#surface-setup").get_by_role("button", name="Get ready", exact=True).click()
            page.get_by_test_id("firstrun").wait_for(timeout=30_000)
            _expand_first_use_setup(page)
            page.wait_for_timeout(400)
            if page.get_by_test_id("runson-root").count() or page.locator("#surface-setup").count():
                fails[f"F5 {width} his windows wait off glass"] = "on glass"
            _expand_first_use_setup(page)
            local_ai = page.get_by_test_id("firstrun-local-ai")
            local_ai.get_by_role("button", name=re.compile(r"^Set up local AI")).click()
            words = page.get_by_test_id("firstrun-first-words")
            dictate = words.get_by_role("button", name="◖ Dictate one sentence", exact=True)
            expect(dictate).to_be_enabled(timeout=60_000)
            dictate.click()
            runs_on = words.get_by_role("button", name="Engines", exact=True)
            runs_on.wait_for(timeout=20_000)
            runs_on.click()
            if not _on_glass(page, "[data-testid='runson-root']"):
                fails[f"F5 {width} the waiting Runs on comes back on glass"] = "not on glass"
            page.screenshot(path=str(out / f"P17-firstrun-waiting-runson-{width}.png"))

            # Leave first run: every window is kept, on glass and in the hub.
            page.get_by_role("button", name=re.compile(r"^(Close|Back from) Settings$")).first.click()
            if width < 720:
                # The first Back leaves the scoped engine choice; the second
                # closes Settings. Both presses use the frame's real control.
                page.get_by_test_id("runson-root").wait_for(state="detached")
                if page.locator("#surface-settings").count():
                    page.locator("#surface-settings").get_by_role("button", name="Back from Settings", exact=True).click()
            page.locator("#surface-settings").wait_for(state="detached")
            page.get_by_role("button", name="Continue later", exact=True).click()
            page.get_by_test_id("firstrun").wait_for(state="detached", timeout=15_000)
            page.wait_for_timeout(800)
            hub = page.evaluate(
                """async (t) => (await (await fetch('/api/desk/windows',
                    {headers: {Authorization: 'Bearer ' + t}})).json())""", TOKEN)
            ids = {w.get("id") for w in hub.get("windows") or []}
            if "surface-setup" not in ids:
                fails[f"F5 {width} Setup (open before Get ready) is in the hub's rows"] = sorted(ids)
            if page.locator("#surface-setup").count() == 0:
                fails[f"F5 {width} Setup comes back on the desk"] = "absent"
            if "surface-settings" in ids or "surface-concierge" in ids:
                fails[f"F5 {width} Engines, closed in first run, stays closed"] = sorted(ids)
            # Runs on again from the desk: the same window id, on glass.
            page.locator(".desk-mark").click()
            page.locator(".desk-menu-list").first.wait_for()
            _row(page, "Engines").click()
            if not _on_glass(page, "[data-testid='runson-root']"):
                fails[f"F5 {width} Runs on opens again on the desk"] = "not on glass"
            hub = page.evaluate(
                """async (t) => (await (await fetch('/api/desk/windows',
                    {headers: {Authorization: 'Bearer ' + t}})).json())""", TOKEN)
            ids = {w.get("id") for w in hub.get("windows") or []}
            if not {"surface-setup", "surface-settings"} <= ids or "surface-concierge" in ids:
                fails[f"F5 {width} hub rows hold the retained and the new window"] = sorted(ids)
            page.screenshot(path=str(out / f"P17-firstrun-after-leave-{width}.png"))
            browser.close()
    finally:
        server.stop()
        source.close()
    assert not fails, fails
