"""First run, option A "One screen" (owner ratified 2026-10-05) on the real hub.

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
from .test_firstrun_heard_glass import TOKEN, WAV, WORDS, Source, _display_count, _real_local_ai

pytest.importorskip("playwright.sync_api", reason="first-run glass needs Playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

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
            cal = page.get_by_test_id("firstrun-calendar")
            conn = page.get_by_test_id("firstrun-connections")

            # ── load: the detect reads only; no prompt, no link read, no probe ──
            ask = cal.get_by_role("button", name="Allow calendar access", exact=True)
            expect(ask).to_be_visible()
            expect(cal.get_by_test_id("firstrun-calendar-ask").locator(".gadget-chip-egress")).to_have_text("THIS DEVICE")
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
            expect(work.locator(".gadget-chip-egress")).to_have_text("THIS DEVICE")

            # a link the hub cannot read: CAN'T READ · SERVER REFUSED
            field = cal.get_by_role("textbox", name="Calendar URL", exact=True)
            field.fill(f"{ics.base}/gone.ics")
            expect(cal.locator(".firstrun-field .gadget-chip-egress")).to_have_text("127.0.0.1")
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
            keep_one("Book the room for the Atlas review.")
            notes = _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
            bodies = sorted(n["body_markdown"] for n in notes if n.get("title") == "First dictation")
            assert bodies == sorted([WORDS, "Book the room for the Atlas review."]), notes
            browser.close()
    finally:
        server.stop()
        source.close()
