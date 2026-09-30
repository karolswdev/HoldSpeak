"""PHILO-11-05 part B -- the SEND well on the meeting faces, Destinations with
Slack, the old Slack rows gone: fenced AS RENDERED through the real hub on an
isolated HOME at 1440x900 and 393x852.

Built to the owner's ratified canvases (phase-11 story 03, "Yes...",
2026-09-29): boards C1-C6, D1-D4 and T1
(pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-03-canvas/).

Every state comes from a real producer:

* the meetings: the real meeting repository (``db.meetings.save_meeting``),
  as the story 01 document fixtures mint them; each transcript carries a
  sentinel no well may show;
* Slack: the Destinations FORM on glass saves the webhook through the real
  HTTP-only ``channel.save_slack_webhook`` and the destination through
  ``channel.save_destination``. Only the transport seams are replaced, in the
  hub's own process, as the story 07 Resend rig does: a MEMORY key store
  (``channel_slack.KEY_STORE``) and a recording HTTPS edge
  (``channel_slack.HTTPS_HANDLER``) that answers Slack's exact ``200 ok``.
  The kernel admission, the egress child and the real opener run. The OS
  keychain is never reached (a guard fails the test if it is) and nothing
  leaves the machine;
* the prepared digest: ``channel.prepare`` through its real route;
* the over-limit summary: the real Slack serializer refuses it, and the face
  reads the real HTTP answer (``size`` and ``limit`` top-level integers).

The face's outcome is compared with the hub's send row AND its kernel receipt
in the same test.
"""
from __future__ import annotations

import hashlib
import io
import json
import http.client
import urllib.request
import urllib.response
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from ._send_face_glass import VISIBLE, Boards
from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the meeting faces glass needs Playwright")

TOKEN = "philo11-05b-meeting-faces"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-05b-shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
WEBHOOK = "https://hooks.slack.com/services/T0P11/B0P11/philo11-05b-synthetic-credential"
SECRET_MARK = "philo11-05b-synthetic-credential"
LEGACY = "https://hooks.slack.com/services/LEGACY/ROW/philo11-05b-legacy-sentinel"
SENTINEL = "TRANSCRIPT-SENTINEL-7Q"
SLACK = "Slack #leads"
FOLDER = "Team folder"
MR = ".desk-window [data-seat=meeting]"          # the well in the Meetings record
MW = ".desk-pullout [data-seat=meeting]"         # the well in the meeting window
DS = "[data-testid=destinations]"


class _Edge:
    """The recording HTTPS edge: every request is recorded, then answered with Slack's exact `200 ok`."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def handler(self) -> urllib.request.BaseHandler:
        edge = self

        class Recording(urllib.request.BaseHandler):
            def https_open(self, req: Any) -> Any:
                edge.requests.append({"host": req.host, "url": req.full_url, "method": req.get_method(),
                                      "body": bytes(req.data or b"")})
                raw = io.BytesIO(b"\r\n")
                result = urllib.response.addinfourl(io.BytesIO(b"ok"), http.client.parse_headers(raw), req.full_url, 200)
                result.msg = "recorded"
                return result

        return Recording()


def _seed_meetings(db: Any) -> dict[str, str]:
    """Three meetings through the real repository: one with a summary, one with none, one over Slack's limit."""
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    def seg(text: str) -> list[TranscriptSegment]:
        return [TranscriptSegment(text=f"{text} {SENTINEL}", speaker="Avery", start_time=1.0, end_time=4.0)]

    def item(i: int, task: str) -> dict[str, Any]:
        return {"id": f"p11b-a{i}", "task": task, "owner": "Priya", "due": None, "status": "pending",
                "review_state": "accepted", "source_timestamp": None, "created_at": "2026-09-29T09:00:00"}

    db.meetings.save_meeting(MeetingState(
        id="p11b-sync", started_at=datetime(2026, 9, 29, 9, 0, 0), title="Ledger cutover sync", segments=seg("We cut over."),
        intel=IntelSnapshot(timestamp=1.0, topics=["Ledger cutover", "Reconciliation"],
                            summary="We agreed to freeze the old ledger on Nov 5 and run one more reconciliation first.",
                            action_items=[item(1, "Run the last reconciliation"), item(2, "Tell finance the freeze date")])))
    db.meetings.save_meeting(MeetingState(
        id="p11b-bare", started_at=datetime(2026, 9, 29, 11, 0, 0), title="Vendor call", segments=seg("Hello."),
        intel=IntelSnapshot(timestamp=1.0, topics=[], summary="", action_items=[])))
    words = "The offsite covered every roadmap line in detail. "
    db.meetings.save_meeting(MeetingState(
        id="p11b-offsite", started_at=datetime(2026, 9, 28, 14, 0, 0), title="Planning offsite", segments=seg("Long day."),
        intel=IntelSnapshot(timestamp=1.0, topics=["Roadmap"], summary=(words * 840).strip(), action_items=[])))
    return {"sync": "p11b-sync", "bare": "p11b-bare", "offsite": "p11b-offsite"}


class TestMeetingFacesGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import keyring
        from holdspeak.services import channel_slack

        _ensure_build()
        self.tmp = tmp_path
        self.keys = channel_slack.MemorySlackKeyStore()
        self.edge = _Edge()
        monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: self.keys)
        monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", self.edge.handler)
        monkeypatch.setattr(keyring, "get_keyring", lambda: (_ for _ in ()).throw(
            AssertionError("the meeting faces glass reached the real keychain")))
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    @staticmethod
    def _stage(page: Any, key: str, scope: str | None = None) -> None:
        page.evaluate("""([key, scope]) => { localStorage.removeItem('hs.desk.workspace.v1');
            sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify(scope ? {key, scope} : {key})); }""",
                      [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    def _settings(self, page: Any) -> None:
        self._stage(page, "configure-settings", "integrations")
        page.locator(DS).wait_for(timeout=T)
        page.wait_for_timeout(700)
        _settle(page)

    def _record(self, page: Any, meeting_id: str) -> None:
        """The Meetings window, the record opened by its row (his click)."""
        self._stage(page, "review-meetings")
        row = page.get_by_test_id(f"meeting-row-{meeting_id}")
        row.wait_for(timeout=T)
        row.locator(".meetings-stream-row-body").click()
        page.locator(".meetings-detail-head").wait_for(timeout=T)
        page.wait_for_timeout(900)
        _settle(page)

    @staticmethod
    def _row(scope: str, name: str) -> str:
        return f"{scope} [data-testid=destination-row]:has([data-destination='{name}'])"

    @staticmethod
    def _opened(scope: str, name: str) -> str:
        return f"{scope} [data-testid=send-open][data-destination='{name}']"

    def _pick(self, page: Any, scope: str, name: str) -> None:
        if not page.locator(self._opened(scope, name)).count():
            page.locator(self._row(scope, name)).first.click()
        o = self._opened(scope, name)
        page.locator(f"{o} [data-testid=send-preview], {o} [data-testid=preview-failed], {o} [data-testid=preview-refused]").first.wait_for(timeout=T)
        page.wait_for_timeout(400)

    def _unpick(self, page: Any, scope: str, name: str) -> None:
        if page.locator(self._opened(scope, name)).count():
            page.locator(self._row(scope, name)).first.click()
            page.locator(self._opened(scope, name)).wait_for(state="detached", timeout=T)

    def _press(self, page: Any, scope: str, name: str) -> None:
        o = self._opened(scope, name)
        page.wait_for_function("(sel) => { const b = document.querySelector(sel); return b && !b.disabled; }",
                               arg=f"{o} [data-testid=send-verb]", timeout=T)
        page.locator(f"{o} [data-testid=send-verb]").click()
        page.wait_for_function("""(sel) => !!document.querySelector(sel + ' [data-receipt=latest]:not([data-state=dispatching]),' +
            sel + ' [data-testid=send-refused],' + sel + ' [data-testid=send-lost]')""", arg=o, timeout=T)
        page.wait_for_timeout(600)

    @staticmethod
    def _sends(page: Any, ref: str) -> list[dict[str, Any]]:
        return _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]

    def _egress_count(self) -> int:
        from holdspeak.db import get_database

        with get_database()._connection() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='external.egress'").fetchone()[0])

    def _receipt(self, operation_id: str) -> dict[str, Any]:
        from holdspeak.db import get_database

        with get_database()._connection() as conn:
            row = conn.execute("SELECT state, outcome FROM kernel_receipts WHERE operation_id=?", (operation_id,)).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def _secret_on_page(page: Any, *marks: str) -> list[str]:
        """Every place the page carries a mark: its HTML, and the value of any field."""
        html = page.content()
        values = page.evaluate("() => [...document.querySelectorAll('input, textarea')].map((e) => e.value).join(' ')")
        return [m for m in marks if m in html or m in values]

    @staticmethod
    def _mark(page: Any, text: str, name: str) -> str:
        """Name the smallest element whose text is `text` (any case): a CSS handle for the on-screen law."""
        page.evaluate("""([t, n]) => { const T = t.toUpperCase();
          const ok = (e) => (e.innerText || '').trim().toUpperCase() === T;
          const all = [...document.querySelectorAll('*')].filter((e) => ok(e) && e.getBoundingClientRect().width);
          const el = all.find((e) => ![...e.children].some(ok)) || all[0]; if (el) el.dataset.mark = n; }""", [text, name])
        return f"[data-mark='{name}']"

    @staticmethod
    def _scroll_to_text(page: Any, sel: str, text: str) -> bool:
        """Scroll the text's own line into its scrollers; True when that line is on screen and on top."""
        return page.evaluate("""([sel, t]) => { const b = document.querySelector(sel); if (!b) return false;
          const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
          for (let n = w.nextNode(); n; n = w.nextNode()) { const i = n.textContent.indexOf(t); if (i < 0) continue;
            const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + t.length);
            for (let s = n.parentElement; s; s = s.parentElement) {
              if (!(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) continue;
              const rr = r.getBoundingClientRect(), sr = s.getBoundingClientRect();
              s.scrollTop += rr.top - (sr.top + Math.min(sr.height / 3, 120));
            }
            const q = r.getBoundingClientRect(); const h = document.elementFromPoint(q.left + 2, q.top + q.height / 2);
            return q.top >= 0 && q.bottom <= innerHeight && !!h && b.contains(h); }
          return false; }""", [sel, text])

    @staticmethod
    def _covered(page: Any, sel: str) -> dict[str, Any]:
        return page.evaluate(VISIBLE, [sel])[0]

    # ── the fence ────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_meeting_faces_and_slack_destinations(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.config import Config
        from holdspeak.db import get_database
        import holdspeak.config as config_module

        ids = _seed_meetings(get_database())
        # A legacy webhook in config.json: the retired Credentials row must not come back for it (R7).
        cfg = Config.load()
        cfg.meeting.slack_webhook_url = LEGACY
        cfg.save(path=config_module.CONFIG_FILE)

        boards = Boards(SHOTS, width, DS)
        facts: dict[str, Any] = {"width": width}
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                folder = self.tmp / "Team"
                folder.mkdir()
                _api(page, "POST", "/api/channels/destinations",
                     {"name": FOLDER, "channel": "file", "folder": str(folder), "synced": False}, token=TOKEN)

                # ── before any Slack destination: no aftercare Slack rows, no Credentials Slack row ──
                self._record(page, ids["sync"])
                win = page.locator(".desk-window:has(.meetings-detail-head)").inner_text()
                assert "→ SLACK" not in win, win
                facts["aftercare_rows_before_slack"] = "→ SLACK" in win

                self._settings(page)
                creds = self._mark(page, "Credentials", "creds")
                settings_text = page.locator(".desk-window:has([data-testid=destinations])").inner_text()
                assert "Slack webhook" not in settings_text
                assert not self._secret_on_page(page, LEGACY)
                d4 = boards.shoot(page, "D4-credentials-no-slack-row", [creds], seat=f"CENTER:{creds}", pointer=False)
                facts["credentials_slack_row_before"] = "Slack webhook" in settings_text

                # ── D2b / D2a / D1: the Slack form ──
                page.locator("[data-testid=dest-add]").click()
                page.locator("[data-testid=dest-form]").wait_for(timeout=T)
                page.locator("[data-testid=dest-form] select[aria-label=Channel]").select_option("slack")
                page.locator("[data-testid=dest-form][data-channel=slack]").wait_for(timeout=T)
                key_row = "[data-testid=dest-key-row]"

                def type_webhook(url: str) -> None:
                    page.locator(f"{key_row} .gadget-secret-verbs .btn").first.click()
                    field = page.locator(f"{key_row} input[type=password]")
                    field.fill(url)
                    field.press("Enter")

                type_webhook("https://example.com/hooks/abc")
                page.locator("[data-testid=dest-key-refused]").wait_for(timeout=T)
                refused = page.locator("[data-testid=dest-key-refused]")
                assert refused.get_attribute("data-code") == "slack_webhook_invalid"
                assert " ".join(refused.inner_text().split()) == "✗ KEY NOT SAVED WEBHOOK NOT VALID", refused.inner_text()
                boards.shoot(page, "D2b-webhook-refused", ["[data-testid=dest-key-refused]"], seat="CENTER:[data-testid=dest-key-refused]")
                assert self.keys.values == {}                   # a refused webhook is not kept

                type_webhook(WEBHOOK)
                page.locator(f"{key_row} .gadget-chip[data-set]").wait_for(timeout=T)
                assert page.locator(f"{key_row} .gadget-chip").inner_text().strip() == "SET"
                assert not self._secret_on_page(page, SECRET_MARK), "the webhook is shown again"
                page.locator("[data-testid=dest-slack-label]").fill("#leads")
                page.wait_for_timeout(200)
                assert page.locator("[data-testid=dest-name]").input_value() == SLACK
                boards.shoot(page, "D2a-webhook-saved", [f"{key_row} .gadget-chip"], seat=f"CENTER:{key_row}")
                d1 = boards.shoot(page, "D1-slack-form", [key_row, "[data-testid=dest-slack-label]", "[data-testid=dest-name]",
                                                          "[data-testid=dest-save]"], seat="CENTER:[data-testid=dest-slack-label]")
                assert "HOOKS.SLACK.COM:cloud" in d1["egress_chips"], d1["egress_chips"]

                page.locator("[data-testid=dest-save]").click()
                page.locator(f"[data-testid=dest-row]:has([data-destination='{SLACK}'])").wait_for(timeout=T)
                page.wait_for_timeout(500)
                dests = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
                slack = next(d for d in dests if d["channel"] == "slack")
                assert slack["name"] == SLACK and slack["target"] == {"channel_label": "#leads"}, slack
                assert set(slack["account"]) == {"key_ref"}, slack
                assert self.keys.values == {f"slack:{slack['account']['key_ref']}": WEBHOOK}   # custody: only the key store holds it
                assert SECRET_MARK not in json.dumps(dests)
                assert not self._secret_on_page(page, SECRET_MARK)
                facts["slack_destination"] = {k: slack[k] for k in ("id", "name", "channel", "target")}

                # ── D3: the row, open, Check -- WEBHOOK SET · HOST OK and no post ──
                page.locator(f"[data-testid=dest-row]:has([data-destination='{SLACK}'])").click()
                page.locator("[data-testid=dest-open]").wait_for(timeout=T)
                page.locator("[data-testid=dest-check]").click()
                page.locator("[data-testid=dest-check-result]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                check = " ".join(page.locator("[data-testid=dest-check-result]").inner_text().split())
                assert check == "✓ WEBHOOK SET · HOST OK", check
                assert self.edge.requests == [], "Check posted to Slack"
                row_text = " ".join(page.locator(f"[data-testid=dest-row]:has([data-destination='{SLACK}'])").inner_text().split())
                for token in ("SLACK", "#leads", "WEBHOOK SET", "HOOKS.SLACK.COM"):
                    assert token in row_text, (token, row_text)
                boards.shoot(page, "D3-slack-row-checked",
                             [f"[data-testid=dest-row]:has([data-destination='{SLACK}'])", "[data-testid=dest-check-result]"],
                             seat=f"CENTER:[data-testid=dest-check-result]")
                settings_text = page.locator(".desk-window:has([data-testid=destinations])").inner_text()
                assert "Slack webhook" not in settings_text          # with a Slack destination too
                facts["check"] = check

                # ── Astra counsel r1 F1: the key gone from the store, a fresh page, Edit -- never SET ──
                slot = f"slack:{slack['account']['key_ref']}"
                del self.keys.values[slot]
                self._settings(page)
                page.locator(f"[data-testid=dest-row]:has([data-destination='{SLACK}'])").click()
                page.locator("[data-testid=dest-edit]").click()
                page.locator("[data-testid=dest-form] [data-testid=dest-key-row]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                edit_chip = page.locator(f"{key_row} .gadget-chip").first.inner_text().strip()
                assert edit_chip != "SET", edit_chip
                assert "WEBHOOK SET" not in page.locator("[data-testid=dest-form]").inner_text()
                page.locator("[data-testid=dest-key-check]").click()
                page.locator("[data-testid=dest-key-missing]").wait_for(timeout=T)
                hub_check = _api(page, "POST", f"/api/channels/destinations/{slack['id']}/check", {}, token=TOKEN)["check"]["state"]
                assert hub_check == "slack_webhook_missing", hub_check
                assert page.locator(f"{key_row} .gadget-chip").first.inner_text().strip() != "SET"
                boards.shoot(page, "D5-edit-unknown-webhook-not-set", ["[data-testid=dest-key-missing]"],
                             seat="CENTER:[data-testid=dest-key-row]", anchor=DS)
                assert self.edge.requests == [], "the Edit probe posted to Slack"
                facts["edit_probe"] = {"chip_before_check": edit_chip, "hub_check": hub_check}
                self.keys.values[slot] = WEBHOOK            # the webhook back for the send legs

                # ── C1: the Meetings record -- SUMMARY, then SEND, then TRANSCRIPT ──
                self._record(page, ids["sync"])
                page.locator(f"{MR} [data-testid=destination-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(600)
                order = page.evaluate("""() => { const w = document.querySelector('.desk-window:has(.meetings-detail-head)');
                  const well = w.querySelector('[data-seat=meeting]'); const slab = w.querySelector('.meeting-summary-slab, [data-testid=meeting-summary-text], .summary-text');
                  const tr = [...w.querySelectorAll('*')].find((e) => /^TRANSCRIPT/.test((e.innerText || '').trim()) && e.children.length < 3);
                  const before = (a, b) => !!a && !!b && !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
                  return {window_width: Math.round(w.getBoundingClientRect().width), summary_before_send: before(slab, well),
                          send_before_transcript: before(well, tr), wells: w.querySelectorAll('[data-testid=send-well]').length}; }""")
                facts["record"] = order
                assert order["wells"] == 1 and order["summary_before_send"] and order["send_before_transcript"], order
                win = page.locator(".desk-window:has(.meetings-detail-head)").inner_text()
                assert "→ SLACK" not in win                       # with a Slack destination too
                assert page.locator(f"{MR} [data-testid=send-well]").get_attribute("data-doc") == f"meeting_summary:{ids['sync']}"
                c1 = boards.shoot(page, "C1-meetings-record-send", [f"{MR} [data-testid=doc-forms] select", self._row(MR, SLACK)],
                                  seat=f"CENTER:{MR} [data-testid=doc-forms]", anchor=MR)
                assert c1["send_head"] == "SEND", c1["send_head"]
                picker = page.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.width, r.height]; }",
                                       f"{MR} [data-testid=doc-forms] select")
                facts["picker_box"] = picker
                if width == 393:
                    assert picker[1] >= 44, picker

                # ── C2: the summary as Slack text; never the transcript ──
                self._pick(page, MR, SLACK)
                body = page.locator(f"{self._opened(MR, SLACK)} [data-testid=send-preview-body]").inner_text()
                assert "freeze the old ledger on Nov 5" in body and SENTINEL not in body, body
                c2 = boards.shoot(page, "C2-summary-slack-picked", [self._row(MR, SLACK), f"{self._opened(MR, SLACK)} [data-testid=send-verb]"],
                                  seat=f"CENTER:{self._opened(MR, SLACK)} [data-testid=send-verb]", anchor=MR)
                send_on_top = next(v for v in c2["named"] if "send-verb" in v["sel"])
                assert send_on_top["ok"], send_on_top               # nothing covers Send
                facts["send_not_covered_record"] = send_on_top

                # ── C3: Send -- POSTED, no link; the face equals the hub's row and receipt ──
                self._press(page, MR, SLACK)
                posted = page.locator(f"{self._opened(MR, SLACK)} [data-receipt=latest]")
                assert posted.get_attribute("data-state") == "sent"
                posted_text = " ".join(posted.inner_text().split())
                rows = self._sends(page, f"meeting_summary:{ids['sync']}")
                assert len(rows) == 1, rows
                hub = rows[0]
                assert hub["state"] == "sent" and hub["channel"] == "slack" and hub["destination_id"] == slack["id"], hub
                assert hub["document_ref"] == f"meeting_summary:{ids['sync']}"
                receipt = self._receipt(hub["send_operation_id"])
                assert receipt.get("state") == "succeeded", receipt
                assert posted_text == "✓ POSTED #leads", posted_text
                assert page.locator(f"{self._opened(MR, SLACK)} a[href]").count() == 0     # no message link
                assert len(self.edge.requests) == 1
                req = self.edge.requests[0]
                assert req["host"] == "hooks.slack.com" and req["url"] == WEBHOOK and req["method"] == "POST"
                assert json.loads(req["body"])["text"] == hub["preview"]["text"]         # the bytes he read went
                assert hashlib.sha256(req["body"]).hexdigest() == hub["payload_digest"].split(":")[-1], hub["payload_digest"]
                assert SENTINEL not in req["body"].decode()
                boards.shoot(page, "C3-summary-posted-slack", [f"{self._opened(MR, SLACK)} [data-receipt=latest]"],
                             seat=f"CENTER:{self._opened(MR, SLACK)} [data-receipt=latest]", anchor=MR)
                facts["summary_send"] = {"face": posted_text, "hub_state": hub["state"], "receipt": receipt,
                                         "document_ref": hub["document_ref"], "edge_requests": len(self.edge.requests)}

                # ── C3b: SENDS 1 ──
                self._unpick(page, MR, SLACK)
                page.locator(f"{MR} [data-testid=send-history]").wait_for(timeout=T)
                c3b = boards.shoot(page, "C3b-summary-history", [f"{MR} [data-testid=history-row]"],
                                   seat=f"CENTER:{MR} [data-testid=send-history]", anchor=MR)
                assert c3b["history_head"] == "SENDS 1", c3b["history_head"]
                hist = " ".join(page.locator(f"{MR} [data-testid=history-row]").first.inner_text().split())
                assert "POSTED" in hist and "#leads" in hist, hist

                # ── C5: the digest, PREPARED by channel.prepare, sent from its own row ──
                digest_ref = f"meeting_digest:{ids['sync']}"
                prep = _api(page, "POST", "/api/channels/sends",
                            {"document_ref": digest_ref, "destination_id": slack["id"], "command_id": f"p11b-prep-{width}"},
                            token=TOKEN)["send"]
                assert prep["state"] == "prepared" and prep["document_ref"] == digest_ref, prep
                page.locator(f"{MR} [data-testid=doc-forms] select").select_option("meeting_digest")
                page.locator(f"{MR} [data-testid=send-well][data-doc='{digest_ref}']").wait_for(timeout=T)
                page.locator(f"{MR} [data-testid=prepared-row]").wait_for(timeout=T)
                page.wait_for_timeout(500)
                prepared_body = page.locator(f"{MR} [data-testid=prepared-open] [data-testid=send-preview-body]").inner_text()
                assert "Still open" in prepared_body and SENTINEL not in prepared_body, prepared_body
                win = page.locator(".desk-window:has(.meetings-detail-head)").inner_text()
                assert "DIGEST → SLACK" not in win and "FOLLOW-UP → SLACK" not in win
                boards.shoot(page, "C5-digest-form-slack", [f"{MR} [data-testid=doc-forms] select", f"{MR} [data-testid=prepared-send]"],
                             seat=f"CENTER:{MR} [data-testid=doc-forms]", anchor=MR)
                # C5c as ratified: the digest body itself on screen (its own line, in the preview well).
                body_sel = f"{MR} [data-testid=prepared-open] [data-testid=send-preview-body]"
                on_screen = self._scroll_to_text(page, body_sel, "Still open")
                assert on_screen, "the digest body is not on screen"
                page.mouse.move(1, 1)
                page.wait_for_timeout(250)
                boards.shoot(page, "C5c-digest-body", [], seat=None, anchor=MR, pointer=False)
                facts["digest_body_on_screen"] = on_screen
                page.locator(f"{MR} [data-testid=prepared-send]").click()
                page.locator(f"{MR} [data-testid=prepared-result]").wait_for(timeout=T)
                page.wait_for_timeout(600)
                drows = self._sends(page, digest_ref)
                assert [r["id"] for r in drows] == [prep["id"]] and drows[0]["state"] == "sent", drows
                assert drows[0]["document_ref"] == digest_ref
                assert self._receipt(drows[0]["send_operation_id"]).get("state") == "succeeded"
                dres = " ".join(page.locator(f"{MR} [data-testid=prepared-result]").inner_text().split())
                assert "POSTED" in dres and "#leads" in dres, dres
                assert len(self.edge.requests) == 2 and json.loads(self.edge.requests[1]["body"])["text"] == drows[0]["preview"]["text"]
                dreceipt = self._receipt(drows[0]["send_operation_id"])
                assert dreceipt.get("state") == "succeeded", dreceipt
                boards.shoot(page, "C5d-digest-prepared-posted", [f"{MR} [data-testid=prepared-result]"],
                             seat=f"CENTER:{MR} [data-testid=prepared-result]", anchor=MR)
                facts["digest_send"] = {"face": dres, "hub_state": drows[0]["state"], "document_ref": drows[0]["document_ref"],
                                        "receipt": dreceipt}

                # ── C5b: the follow-up to the folder ──
                followup_ref = f"meeting_followup:{ids['sync']}"
                page.locator(f"{MR} [data-testid=doc-forms] select").select_option("meeting_followup")
                page.locator(f"{MR} [data-testid=send-well][data-doc='{followup_ref}']").wait_for(timeout=T)
                page.locator(f"{MR} [data-testid=destination-row]").first.wait_for(timeout=T)
                self._pick(page, MR, FOLDER)
                assert page.locator(f"{MR} [data-testid=doc-forms] select").input_value() == "meeting_followup"
                boards.shoot(page, "C5b-followup-form-folder", [f"{self._opened(MR, FOLDER)} [data-testid=send-verb]"],
                             seat=f"CENTER:{self._opened(MR, FOLDER)} [data-testid=send-verb]", anchor=MR)
                c5b_body = page.locator(f"{self._opened(MR, FOLDER)} [data-testid=send-preview-body]").inner_text()
                assert SENTINEL not in c5b_body
                self._press(page, MR, FOLDER)
                frows = self._sends(page, followup_ref)
                assert len(frows) == 1 and frows[0]["state"] == "sent" and frows[0]["document_ref"] == followup_ref, frows
                saved = Path(frows[0]["file_path"]).read_text()
                assert SENTINEL not in saved
                freceipt_el = page.locator(f"{self._opened(MR, FOLDER)} [data-receipt=latest]")
                assert freceipt_el.get_attribute("data-state") == "sent"
                fface = " ".join(freceipt_el.inner_text().split())
                assert fface == f"✓ SAVED {frows[0]['file_path']}", (fface, frows[0]["file_path"])
                assert (frows[0].get("proof") or {}).get("path", frows[0]["file_path"]) == frows[0]["file_path"], frows[0]["proof"]
                freceipt = self._receipt(frows[0]["send_operation_id"])
                assert freceipt.get("state") == "succeeded", freceipt
                facts["followup_send"] = {"face": fface, "hub_state": frows[0]["state"], "document_ref": followup_ref,
                                          "file_path": frows[0]["file_path"], "proof": frows[0].get("proof"), "receipt": freceipt}
                page.locator(f"{MR} [data-testid=doc-forms] select").select_option("meeting_summary")

                # ── C4: no summary, no well ──
                self._record(page, ids["bare"])
                page.wait_for_timeout(1200)
                wells = page.locator(".desk-window:has(.meetings-detail-head) [data-testid=send-well]").count()
                assert wells == 0, wells
                head = ".desk-window .meetings-detail-head"
                boards.shoot(page, "C4-no-summary-no-well", [head], seat=None, anchor=head, pointer=False)
                facts["no_summary_wells"] = wells

                # ── T1: over Slack's limit -- the REAL HTTP answer, named, with its size ──
                over_ref = f"meeting_summary:{ids['offsite']}"
                status, answer = _api_allow_error(page, "POST", "/api/channels/preview",
                                                  {"document_ref": over_ref, "destination_id": slack["id"]}, token=TOKEN)
                assert status == 400, (status, answer)
                code = answer.get("error_code") or answer.get("code")
                assert code == "payload_too_large:slack", answer
                assert isinstance(answer["size"], int) and answer["limit"] == 39_000 and answer["size"] > 39_000, answer
                # channel.preview is admission-exempt (holdspeak/channel_operations.py:199): no kernel
                # operation, so no receipt. The kernel record is the ABSENCE of any egress for it.
                assert "operation_id" not in answer and "receipt" not in answer, sorted(answer)
                t1_receipt = {"egress_operations": self._egress_count()}
                assert t1_receipt["egress_operations"] == 2, t1_receipt       # the summary and the digest only
                self._record(page, ids["offsite"])
                page.locator(f"{MR} [data-testid=destination-row]").first.wait_for(timeout=T)
                self._pick(page, MR, SLACK)
                ref_el = page.locator(f"{self._opened(MR, SLACK)} [data-testid=preview-refused]")
                assert ref_el.get_attribute("data-code") == "payload_too_large:slack"
                t1 = " ".join(ref_el.inner_text().split())
                want = f"✗ REFUSED TOO LARGE FOR SLACK {answer['size']:,} / 39,000 CHARACTERS NOTHING SENT HOOKS.SLACK.COM"
                assert t1 == want, (t1, want)
                assert "NO ANSWER" not in page.locator(self._opened(MR, SLACK)).inner_text()
                assert page.locator(f"{self._opened(MR, SLACK)} [data-testid=send-verb]:not([disabled])").count() == 0
                assert self._sends(page, over_ref) == [] and len(self.edge.requests) == 2      # nothing sent
                boards.shoot(page, "T1-over-slack-limit-refused", [f"{self._opened(MR, SLACK)} [data-testid=preview-refused]"],
                             seat=f"CENTER:{self._opened(MR, SLACK)} [data-testid=preview-refused]", anchor=MR)
                facts["t1"] = {"face": t1, "http": {"status": status, "code": code, "size": answer["size"], "limit": answer["limit"]},
                              "receipt": t1_receipt}

                # ── C6: the meeting window -- the same well, its history ──
                page.evaluate("() => localStorage.removeItem('hs.desk.workspace.v1')")
                page.goto(f"{self.base}/?token={TOKEN}&open=meeting:{ids['sync']}", wait_until="load")
                _normal_chair(page)
                page.locator(f"{MW} [data-testid=destination-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(900)
                _settle(page)
                assert page.locator(f"{MW} [data-testid=send-well]").get_attribute("data-doc") == f"meeting_summary:{ids['sync']}"
                mw_width = page.evaluate("(s) => Math.round(document.querySelector(s).closest('.desk-window, .desk-pullout').getBoundingClientRect().width)", MW)
                c6 = boards.shoot(page, "C6-meeting-window-well", [f"{MW} [data-testid=doc-forms] select", self._row(MW, SLACK)],
                                  seat=f"CENTER:{MW} [data-testid=doc-forms]", anchor=MW)
                assert c6["history_head"] == "SENDS 1", c6["history_head"]
                self._pick(page, MW, SLACK)
                c6b = boards.shoot(page, "C6c-meeting-window-picked", [f"{self._opened(MW, SLACK)} [data-testid=send-verb]"],
                                   seat=f"CENTER:{self._opened(MW, SLACK)} [data-testid=send-verb]", anchor=MW)
                assert c6b["named"][0]["ok"], c6b["named"]                  # nothing covers Send in the meeting window
                summary_ref = f"meeting_summary:{ids['sync']}"
                before = {r["id"] for r in self._sends(page, summary_ref)}
                self._press(page, MW, SLACK)
                wrows = [r for r in self._sends(page, summary_ref) if r["id"] not in before]
                assert len(wrows) == 1, wrows
                w = wrows[0]
                assert w["state"] == "sent" and w["document_ref"] == summary_ref and w["destination_id"] == slack["id"], w
                wreceipt = self._receipt(w["send_operation_id"])
                assert wreceipt.get("state") == "succeeded", wreceipt
                wface_el = page.locator(f"{self._opened(MW, SLACK)} [data-receipt=latest]")
                assert wface_el.get_attribute("data-state") == "sent"
                wface = " ".join(wface_el.inner_text().split())
                assert wface == "✓ POSTED #leads", wface
                assert page.locator(f"{self._opened(MW, SLACK)} a[href]").count() == 0
                assert len(self.edge.requests) == 3 and json.loads(self.edge.requests[2]["body"])["text"] == w["preview"]["text"]
                c6d = boards.shoot(page, "C6d-meeting-window-posted", [f"{self._opened(MW, SLACK)} [data-receipt=latest]"],
                                   seat=f"CENTER:{self._opened(MW, SLACK)} [data-receipt=latest]", anchor=MW)
                facts["window_send"] = {"face": wface, "hub_state": w["state"], "document_ref": w["document_ref"], "receipt": wreceipt}
                facts["meeting_window_width"] = mw_width

                # The laws on every board (touched text: 12 px floor; the host's own heads are ledgered, inherited).
                assert not boards.hidden, boards.hidden
                for key, f in boards.facts.items():
                    assert f["window"], key
                    assert not f["small_text"]["touched"], (key, f["small_text"]["touched"])
                    assert f["raw_buttons"]["touched"] == [], (key, f["raw_buttons"])
                    assert not f["modal"], key
                    assert not f["h_overflow"], key
                    assert not f["preview_has_raw"], key
                    bad = [p for p in f.get("pointer", []) if not p["owned"]]
                    assert not bad, (key, bad)
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
                facts["d4"] = {"named": d4["named"]}
            finally:
                boards.write("meeting-faces", {"facts": facts})
                browser.close()
