"""PHILO-11-05a -- the SEND well on the brief and decision faces, fenced AS
RENDERED through the real hub on an isolated HOME at 1440x900 and 393x852.

Built to the owner's ratified canvases (phase-11 story 03, "Yes..."): boards
A1-A6 (the brief on the Chair and in Intelligence -> BRIEF), B1-B5 (the
decision window, the Room's DECISIONS & COMMITMENTS rows, Intelligence ->
DECISIONS), T2 (PREVIEW CHANGED -> a fresh preview -> another press) and T3
(the Chair after its last brief item is triaged). Each face sends its OWN
``document_ref``; each fence reads the hub's send row and compares the face's
outcome with it in the same test.

Every fixture comes from a real producer: the brief from
``POST /api/brief/generate``; the desk decision from ``POST /api/decisions``
and its change from ``PUT /api/decisions/<id>``; the meeting-proposal record
from the decision_capture artifact through ``ProposalBridgeService`` (what the
intel queue runs) and ``POST /api/proposals/<id>/confirm``; a plain record from
``DecisionRecordService.create``; the prepared sends from ``channel.prepare``
(``POST /api/channels/sends``) by a remote agent credential issued through the
real Settings route. The recorded meeting itself is written through the
product's DB layer (no route records a meeting without audio; the canvas did
the same). Destinations are folders: nothing leaves the machine.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from ._doc_send_glass import Boards
from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from .chair_windows import open_chair_window
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the document SEND well glass needs Playwright")

TOKEN = "philo11-05a-doc-send"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-05a-proof/shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
PROJECT = "Payments ledger cutover"
REMOTE_HOST = "192.0.2.123"  # TEST-NET-1: never loopback
AGENT_ID = "remote-project-agent"

CH = ".chair [data-seat=brief]"                       # the Chair's brief seat
# PHILO-13-11 (slice two): the Chair is four windows (.chair-window); the
# Intelligence and decision seats are the OTHER windows.
IB = ".desk-window:not(.chair-window) [data-seat=brief]"                 # Intelligence -> BRIEF
DD = ".desk-window:not(.chair-window) [data-seat=desk-decision]"         # the decision window
DR = ".desk-window:not(.chair-window) .receipt-detail [data-seat=decision-record]"   # Intelligence -> DECISIONS
RR = "[data-testid=room-body] [data-seat=decision-record]"        # a Room decision row, unfolded

# The species' stamp (features/channels/channels.ts `stamp`), in the page's zone.
STAMP_JS = """(iso) => { const M = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  const d = new Date(iso); const p = (n) => String(n).padStart(2, "0");
  return `${M[d.getMonth()]} ${d.getDate()} ${p(d.getHours())}:${p(d.getMinutes())}`; }"""


def row(scope: str, name: str) -> str:
    return f"{scope} [data-testid=destination-row]:has([data-destination='{name}'])"


def opened(scope: str, name: str) -> str:
    return f"{scope} [data-testid=send-open][data-destination='{name}']"


WEBHOOK = "https://hooks.slack.com/services/T0P11/B0P11/philo11-05a-synthetic-credential"
SECRET_MARK = "philo11-05a-synthetic-credential"
SLACK = "Slack #leads"


class _Edge:
    """The recording HTTPS edge: every request is recorded, then answered with Slack's exact `200 ok`."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def handler(self) -> Any:
        import http.client
        import io
        import urllib.request
        import urllib.response

        edge = self

        class Recording(urllib.request.BaseHandler):
            def https_open(self, req: Any) -> Any:
                edge.requests.append({"host": req.host, "url": req.full_url, "method": req.get_method(),
                                      "body": bytes(req.data or b"")})
                result = urllib.response.addinfourl(io.BytesIO(b"ok"), http.client.parse_headers(io.BytesIO(b"\r\n")),
                                                    req.full_url, 200)
                result.msg = "recorded"
                return result

        return Recording()


class _Rig:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.tmp = tmp_path
        # The People store on a file key in this HOME (no macOS Keychain in an isolated HOME).
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        # Slack's transport seams only, in the hub's own process (part B's pattern): a MEMORY
        # key store and a recording HTTPS edge that answers Slack's exact `200 ok`. The kernel
        # admission, the egress child and the real opener run; the OS keychain is never
        # reached (a guard fails the test if it is); nothing leaves the machine.
        import keyring
        from holdspeak.services import channel_slack

        self.keys = channel_slack.MemorySlackKeyStore()
        self.edge = _Edge()
        monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: self.keys)
        monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", self.edge.handler)
        monkeypatch.setattr(keyring, "get_keyring", lambda: (_ for _ in ()).throw(
            AssertionError("the glass reached the real keychain")))
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        # The wheel moves the page in one step (no smooth-scroll animation under the probe).
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    def _reload(self, page: Any, chair: str | None = None) -> None:
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        # PHILO-13-11 (slice two, R2): at 393 one Chair window at a time; the
        # seat under test (Brief, The week) is opened through Go ▸ Chair.
        if chair and page.viewport_size["width"] <= 720:
            open_chair_window(page, chair)
            page.wait_for_timeout(600)
        _settle(page)

    def _dest(self, page: Any, name: str) -> tuple[str, Path]:
        folder = (self.tmp / "Reports" / name.replace(" ", "")).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        did = _api(page, "POST", "/api/channels/destinations",
                   {"name": name, "channel": "file", "folder": str(folder)}, token=TOKEN)["destination"]["id"]
        return did, folder

    @staticmethod
    def _sends(page: Any, ref: str) -> list[dict[str, Any]]:
        return _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]

    @staticmethod
    def _kernel(operation_id: str) -> dict[str, Any]:
        """The kernel's own record of an operation: its row and its ONE terminal receipt."""
        from holdspeak.db import get_database

        with get_database()._connection() as conn:
            row = conn.execute(
                "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.target_ref,"
                " r.state AS receipt_state, r.outcome AS receipt_outcome, r.result_ref,"
                " (SELECT COUNT(*) FROM kernel_receipts x WHERE x.operation_id = o.operation_id) AS receipts"
                " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id = o.operation_id"
                " WHERE o.operation_id = ?", (operation_id,)).fetchone()
        assert row is not None, operation_id
        return dict(row)

    @staticmethod
    def _kernel_refusals(name: str, outcome: str) -> list[dict[str, Any]]:
        from holdspeak.db import get_database

        with get_database()._connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT o.operation_id, o.name, o.state, o.target_ref, r.state AS receipt_state, r.outcome AS receipt_outcome"
                " FROM kernel_operations o JOIN kernel_receipts r ON r.operation_id = o.operation_id"
                " WHERE o.name = ? AND r.outcome = ?", (name, outcome))]

    def _face_row_receipt(self, send: dict[str, Any], ref: str, *, principal: str = "owner") -> dict[str, Any]:
        """face = row = receipt: the hub's send row and the kernel's receipt of its send
        operation agree (sent -> succeeded, the same document, one receipt)."""
        k = self._kernel(send["send_operation_id"])
        assert k["name"] == "channel.send" and k["receipts"] == 1, k
        assert (send["state"], k["state"], k["receipt_state"]) == ("sent", "succeeded", "succeeded"), (send, k)
        assert k["result_ref"] == f"channel_send:{send['id']}", (k, send["id"])
        assert k["target_ref"] in (f"document:{ref}", f"channel_send:{send['id']}"), (k, ref)
        assert k["principal_kind"] == principal, k
        return k

    @staticmethod
    def _slack(page: Any) -> str:
        """A Slack destination through the real routes: the held webhook save, then the destination."""
        key_ref = _api(page, "POST", "/api/channels/slack-webhooks", {"webhook_url": WEBHOOK}, token=TOKEN)["key_ref"]
        return _api(page, "POST", "/api/channels/destinations",
                    {"name": SLACK, "channel": "slack", "key_ref": key_ref, "channel_label": "#leads"},
                    token=TOKEN)["destination"]["id"]

    @staticmethod
    def _focus(page: Any) -> None:
        page.evaluate("window.dispatchEvent(new Event('focus'))")
        page.wait_for_timeout(800)

    @staticmethod
    def _stamp(page: Any, iso: str) -> str:
        return page.evaluate(STAMP_JS, iso)

    def _agent(self) -> Any:
        from starlette.testclient import TestClient

        client = TestClient(self.server.app, client=(REMOTE_HOST, 50000))
        headers = {"Authorization": f"Bearer {TOKEN}"}
        assert client.put("/api/settings/remote", json={"enabled": True}, headers=headers).status_code == 200
        issued = client.post("/api/settings/remote/credentials", json={"identity": AGENT_ID, "palette": "PROJECT"},
                             headers=headers)
        assert issued.status_code == 200, issued.text
        agent = TestClient(self.server.app, client=(REMOTE_HOST, 50001))
        agent.headers.pop("x-holdspeak-token", None)
        agent.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
        return agent

    @staticmethod
    def _pick(page: Any, scope: str, name: str) -> None:
        if not page.locator(opened(scope, name)).count():
            page.locator(row(scope, name)).first.click()
        page.locator(f"{opened(scope, name)} [data-testid=send-preview], {opened(scope, name)} [data-testid=preview-refused], "
                     f"{opened(scope, name)} [data-testid=preview-failed]").first.wait_for(timeout=T)
        page.wait_for_timeout(400)

    @staticmethod
    def _unpick(page: Any, scope: str, name: str) -> None:
        if page.locator(opened(scope, name)).count():
            page.locator(row(scope, name)).first.click()
            page.locator(opened(scope, name)).wait_for(state="detached", timeout=T)
            page.wait_for_timeout(300)

    @staticmethod
    def _press(page: Any, scope: str, name: str, expect: str = "[data-receipt=latest][data-state=sent]") -> None:
        sel = f"{opened(scope, name)} [data-testid=send-verb]"
        page.wait_for_function("(s) => { const b = document.querySelector(s); return b && !b.disabled; }", arg=sel, timeout=T)
        page.locator(sel).first.click()
        page.locator(f"{opened(scope, name)} {expect}").first.wait_for(timeout=T)
        page.wait_for_timeout(700)

    @staticmethod
    def _text(page: Any, sel: str) -> str:
        return " ".join(page.locator(sel).first.inner_text().split())

    @staticmethod
    def _close_windows(page: Any) -> None:
        for _ in range(6):
            btn = page.locator(".desk-window:not(.chair-window) [aria-label^='Close ']")
            if not btn.count():
                break
            btn.last.click()
            page.wait_for_timeout(500)

    @staticmethod
    def _open_decision(page: Any, title: str, decision_id: str) -> None:
        page.locator("[aria-controls=desk-tool-shelf]").first.click()
        page.locator("[aria-controls=desk-palette-listbox]").fill(title)
        page.locator(f"[id='desk-palette-option-decision:{decision_id}']").click()
        page.locator(f"{DD} [data-testid=send-well]").wait_for(timeout=T)
        page.wait_for_timeout(800)
        _settle(page)

    @staticmethod
    def _open_intelligence(page: Any, tab: str | None = None) -> None:
        page.locator("button.desk-dock-app").first.click()
        page.locator(".desk-window .intelligence-pullout").first.wait_for(timeout=T)
        if tab:
            page.locator(".intelligence-segment", has_text=tab).first.click()
        page.wait_for_timeout(900)
        _settle(page)


class TestBriefAndDecisionSendGlass(_Rig):
    # ── A + T3: the brief on the Chair and in Intelligence -> BRIEF ────────

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_brief_well_on_the_chair_and_in_intelligence(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _api(page, "POST", "/api/projects", {"name": PROJECT}, token=TOKEN)
                for title, text in (("Freeze the old ledger on Nov 3", "Freeze the old ledger on Nov 3."),
                                    ("Cut over by space, not by region", "Cut over by space, not by region.")):
                    # A PROPOSED desk decision is a brief item ("Review decision: ...").
                    _api(page, "POST", "/api/decisions", {"title": title, "status": "proposed", "decision_markdown": text},
                         token=TOKEN)
                # A person the brief's People overlay reads at render time (the canvas's seed).
                _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
                priya = _api(page, "POST", "/api/people/relationships", {"display_name": "Priya Nair"}, token=TOKEN)["relationship"]["id"]
                _api(page, "POST", f"/api/people/relationships/{priya}/owner-aliases", {"alias": "Priya"}, token=TOKEN)
                brief = _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
                ref = f"monday_brief:{brief['id']}"
                items = [it for sec in brief["sections"].values() for it in sec]
                assert len(items) >= 2, brief
                self._reload(page, "Brief")

                # A1: no destination -- the Chair's brief carries the well: one token, one verb.
                page.locator(f"{CH} [data-testid=send-none]").wait_for(timeout=T)
                a1 = shots.shoot(page, "A1-brief-chair-no-destination", CH,
                                 [f"{CH} [data-testid=send-none]", f"{CH} [data-testid=send-add-destination]"], block="center")
                assert a1["wells"] == [ref], a1["wells"]
                assert a1["send_head"] == "SEND", a1["send_head"]

                team, team_dir = self._dest(page, "Team folder")
                ledger, ledger_dir = self._dest(page, "Ledger folder")
                # A4: an agent prepared a send of the brief (channel.prepare).
                r = self._agent().post("/api/channels/sends", json={"document_ref": ref, "destination_id": ledger})
                assert r.status_code == 200, r.text
                prepared_id = r.json()["send"]["id"]
                self._reload(page, "Brief")

                chip = ".chair [data-testid=arrival-brief] [data-testid=doc-prepared-chip]"
                page.locator(chip).wait_for(timeout=T)
                a4 = shots.shoot(page, "A4-brief-prepared-chair", CH, [chip], block="center")
                head = page.evaluate("""(chip) => { const c = document.querySelector(chip); const head = c.closest('.surface-section-head');
                  const h3 = head.querySelector('h3'); const gen = head.querySelector('[data-testid=arrival-brief-generate]');
                  const lr = h3.getBoundingClientRect(), cr = c.getBoundingClientRect(), gr = gen.getBoundingClientRect();
                  const lh = parseFloat(getComputedStyle(h3).lineHeight) || parseFloat(getComputedStyle(h3).fontSize) * 1.3;
                  return {label: h3.innerText.trim(), label_lines: Math.round(lr.height / lh), label_fs: parseFloat(getComputedStyle(h3).fontSize),
                    chip: c.innerText.replace(/\\s+/g, ' ').trim(), chip_below_label: cr.top >= lr.bottom - 1, generate_below_label: gr.top >= lr.bottom - 1,
                    chip_right_of_label: cr.left >= lr.right - 1, generate: [Math.round(gr.width), Math.round(gr.height)]}; }""", chip)
                a4["head"] = head
                assert head["chip"] == "◆ PREPARED ×1", head
                assert head["label_lines"] == 1, head   # the label keeps its line
                if width == 393:
                    # Canvas A4 at 393 (Muad'Dib's ruling): the whole group -- the chip, the
                    # badge and Generate -- wraps UNDER the label.
                    assert head["chip_below_label"] and head["generate_below_label"], head
                else:
                    assert head["chip_right_of_label"] and not head["generate_below_label"], head

                # A4b: the prepared row, first in SEND, with its egress; its document is the brief.
                page.locator(f"{CH} [data-testid=prepared-row]").wait_for(timeout=T)
                a4b = shots.shoot(page, "A4b-brief-prepared-row", CH,
                                  [f"{CH} [data-testid=prepared-row]", f"{CH} [data-testid=prepared-send]"])
                hub_prepared = next(s for s in self._sends(page, ref) if s["id"] == prepared_id)
                assert hub_prepared["document_ref"] == ref and hub_prepared["state"] == "prepared", hub_prepared
                # The agent's prepare is a kernel operation with its one receipt, under the agent.
                kp = self._kernel(hub_prepared["prepare_operation_id"])
                assert (kp["name"], kp["state"], kp["receipt_state"], kp["receipts"]) == ("channel.prepare", "succeeded", "succeeded", 1), kp
                assert kp["principal_identity"] == AGENT_ID, kp
                a4b["kernel_prepare"] = kp
                preview_text = page.locator(f"{CH} [data-testid=prepared-preview] [data-testid=send-preview-body]").inner_text()
                assert re.search(r"Generated: \d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2}", preview_text), preview_text[:300]
                assert not re.search(r"\d{4}-\d{2}-\d{2}T|\d{2}:\d{2}:\d{2}\.\d+", preview_text), preview_text[:300]
                day = self._stamp(page, brief["generated_at"])[:-6]
                assert a4b["prepared"][0].startswith(f"◆ Ledger folder ◆ PREPARED BY {AGENT_ID.upper()} BRIEF {day}"), a4b["prepared"]
                assert "THIS DEVICE" in a4b["prepared"][0], a4b["prepared"]

                # A4c: Send on the prepared row: it stays as its result; the hub's row is that result.
                page.locator(f"{CH} [data-testid=prepared-send]").click()
                page.locator(f"{CH} [data-testid=prepared-result]").wait_for(timeout=T)
                page.wait_for_timeout(700)
                hub_prepared = next(s for s in self._sends(page, ref) if s["id"] == prepared_id)
                assert hub_prepared["state"] == "sent", hub_prepared
                # face = row = receipt: his press is the owner's channel.send, one succeeded receipt.
                k_a4c = self._face_row_receipt(hub_prepared, ref)
                ppath = hub_prepared["proof"]["path"]
                assert Path(ppath).is_file() and Path(ppath).parent == ledger_dir, ppath
                sent_text = Path(ppath).read_text()
                assert "Monday Brief" in sent_text, sent_text[:200]
                # The sent bytes carry the readable generated time, as the preview does.
                gen_line = next(ln for ln in sent_text.splitlines() if ln.startswith("Generated: "))
                assert re.fullmatch(r"Generated: \d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2}", gen_line), gen_line
                assert gen_line in preview_text, (gen_line, preview_text[:300])   # one format: preview == bytes
                a4c = shots.shoot(page, "A4c-brief-prepared-saved", CH,
                                  [f"{CH} [data-testid=prepared-result]", f"{CH} [data-testid=send-history] .surface-section-head"])
                assert a4c["prepared"][0].startswith(f"· Ledger folder ✓ SAVED {ppath} BY {AGENT_ID.upper()}"), a4c["prepared"]
                assert a4c["history_head"] == "SENDS 1", a4c["history_head"]
                a4c["kernel_send"] = k_a4c
                assert page.locator(chip).count() == 0   # no counter at zero

                # A2: Intelligence -> BRIEF, after PEOPLE: SEND; the pick opens the preview and Send.
                self._open_intelligence(page)
                page.locator(f"{IB} [data-testid=destination-row]").first.wait_for(timeout=T)
                self._pick(page, IB, "Team folder")
                a2 = shots.shoot(page, "A2-brief-picked-folder", IB,
                                 [row(IB, "Team folder"), f"{opened(IB, 'Team folder')} [data-testid=send-verb]"])
                assert a2["wells"] == [ref], a2["wells"]
                assert a2["preview_fields"] == [f"FOLDER {team_dir}"], a2["preview_fields"]
                # One pick with the Chair's seat of the same brief (the species' store).
                shared_pick = page.locator(opened(CH, "Team folder")).count()
                a2["chair_row_open"] = shared_pick
                assert shared_pick == 1, "the Chair's seat does not show the same pick"

                # A3: Send -> SAVED + the exact path; SENDS 2 (no Mark delivered).
                self._press(page, IB, "Team folder")
                hub = self._sends(page, ref)
                sent = [s for s in hub if s["destination_id"] == team and s["state"] == "sent"]
                assert len(sent) == 1 and all(s["document_ref"] == ref for s in hub), hub
                path = sent[0]["proof"]["path"]
                assert Path(path).is_file() and Path(path).parent == team_dir
                receipt = self._text(page, f"{opened(IB, 'Team folder')} [data-receipt=latest]")
                assert receipt == f"✓ SAVED {path}", receipt
                k_a3 = self._face_row_receipt(sent[0], ref)
                self._unpick(page, IB, "Team folder")
                a3 = shots.shoot(page, "A3-brief-saved-history", IB,
                                 [f"{row(IB, 'Team folder')} [data-testid=send-last-sent]",
                                  f"{IB} [data-testid=send-history] .surface-section-head"])
                assert a3["history_head"] == "SENDS 2", a3["history_head"]
                assert any(h.startswith(f"✓ Team folder SAVED {path}") for h in a3["history"]), a3["history"]
                a3["kernel_send"] = k_a3

                # A5: the brief changes after the send -- a new person signal (an agenda item
                # for Priya's 1:1, through the same routes BriefView's "Add to 1:1 agenda" uses),
                # and a same-day Generate returns the SAME brief id. The brief's People section
                # is read at render time, so its words change; the well reads the new preview and
                # offers Send again; the press sends the new words.
                one = _api(page, "POST", f"/api/people/relationships/{priya}/one-on-ones",
                           {"visibility": "shared_intent"}, token=TOKEN)["one_on_one"]["id"]
                _api(page, "POST", f"/api/people/one-on-ones/{one}/agenda",
                     {"body": "Review the rollback plan", "visibility": "shared_intent", "state": "open",
                      "source": {"kind": "brief"}}, token=TOKEN)
                again = _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
                assert again["id"] == brief["id"], (again["id"], brief["id"])
                # The same Intelligence -> BRIEF window, still open: picking reads a fresh preview.
                self._pick(page, IB, "Team folder")
                body = f"{opened(IB, 'Team folder')} [data-testid=send-preview-body]"
                page.wait_for_function("(s) => (document.querySelector(s)?.innerText || '').includes('Priya Nair')", arg=body, timeout=T)
                verb = self._text(page, f"{opened(IB, 'Team folder')} [data-testid=send-verb]")
                page.evaluate("""(sel) => { const b = document.querySelector(sel);
                  const all = [...b.querySelectorAll('*')].filter((e) => e.innerText.includes('Priya Nair'));
                  const el = all.find((e) => ![...e.children].some((c) => c.innerText.includes('Priya Nair')));
                  if (el) { el.dataset.mark = 'a5-new-words'; el.scrollIntoView({block: 'center'}); } }""", body)
                page.wait_for_timeout(300)
                a5 = shots.shoot(page, "A5-brief-changed-send-again", IB, ["[data-mark=a5-new-words]"], seat=None)
                assert verb == "Send again", verb
                a5["verb"] = verb
                page.evaluate("(sel) => document.querySelectorAll(sel + ' *').forEach((e) => { e.scrollTop = 0; })", opened(IB, "Team folder"))
                shots.shoot(page, "A5b-brief-changed-verb", IB, [f"{opened(IB, 'Team folder')} [data-testid=send-verb]",
                                                               f"{row(IB, 'Team folder')} [data-testid=send-last-sent]"],
                            seat=row(IB, "Team folder"))
                self._press(page, IB, "Team folder")
                newer = [s for s in self._sends(page, ref) if s["destination_id"] == team and s["state"] == "sent" and s["id"] != sent[0]["id"]]
                assert len(newer) == 1, newer
                assert "Priya Nair" in Path(newer[0]["proof"]["path"]).read_text()
                assert "Priya Nair" not in Path(path).read_text()   # the first send kept its own words
                self._face_row_receipt(newer[0], ref)
                latest_team = newer[0]
                self._unpick(page, IB, "Team folder")
                self._close_windows(page)

                # T3: all brief items but one handled through the real shelf route; the Chair's
                # own Ack on glass then handles the last one and the Chair changes branch.
                latest_items = [it for sec in _api(page, "GET", "/api/brief/latest", token=TOKEN)["sections"].values() for it in sec]
                for it in latest_items[1:]:
                    _api(page, "POST", f"/api/brief/items/{it['id']}/shelf", {"state": "acknowledged"}, token=TOKEN)
                self._reload(page, "Brief")
                ack = page.locator(".chair [data-testid=arrival-brief] .btn", has_text="Ack").first
                ack.wait_for(timeout=T)
                self._pick(page, CH, "Team folder")
                t_sel = f"{opened(CH, 'Team folder')} [data-receipt=latest]"
                h_sel = f"{CH} [data-testid=history-row]:has([data-to='Team folder'])"
                c_sel = f"{row(CH, 'Team folder')} [data-testid=send-last-sent]"

                def receipt_now() -> dict[str, Any]:
                    return {"latest": self._text(page, t_sel), "state": page.locator(t_sel).first.get_attribute("data-state"),
                            "row_chip": self._text(page, c_sel), "history": self._text(page, h_sel)}

                shots.shoot(page, "T3a-chair-last-item", CH, [".chair [data-testid=arrival-brief] .surface-section-head", f"{CH} [data-send=well] .surface-section-head"],
                            seat=".chair [data-testid=arrival-brief]")
                shots.shoot(page, "T3a2-chair-last-item-receipt", CH, [t_sel, c_sel], seat=row(CH, "Team folder"))
                before = receipt_now()
                assert "1 THING WAITING" in page.locator(".chair [data-testid=arrival-brief] .surface-section-head").first.inner_text()
                ack.click()
                page.locator(".chair [data-testid=arrival-brief-headline], .chair [data-testid=arrival-brief-handled]").first.wait_for(timeout=T)
                page.wait_for_timeout(900)
                assert page.locator(".chair [data-testid=arrival-brief] .btn", has_text="Ack").count() == 0
                shots.shoot(page, "T3b-chair-after-last-ack", CH,
                            [".chair [data-testid=arrival-brief] .surface-section-head", f"{CH} [data-send=well] .surface-section-head"],
                            seat=".chair [data-testid=arrival-brief]")
                # At the same scroll seat the receipt is the same pixels before and after (allowed).
                t3b = shots.shoot(page, "T3b2-chair-after-last-ack-receipt", CH, [t_sel, c_sel], seat=row(CH, "Team folder"),
                                  same_as="T3a2-chair-last-item-receipt")
                after = receipt_now()
                # The SAME receipt (state, target, time) after the branch change, equal to the hub's row.
                hub_row = next(s for s in self._sends(page, ref) if s["id"] == latest_team["id"])
                t3_kernel = self._face_row_receipt(hub_row, ref)
                when = self._stamp(page, hub_row["settled_at"])
                assert before == after, (before, after)
                assert after["state"] == hub_row["state"] == "sent", (after, hub_row)
                assert after["latest"] == f"✓ SAVED {hub_row['proof']['path']}", after
                assert after["row_chip"] == f"✓ SAVED {when[-5:]}", (after, when)
                assert after["history"] == f"✓ Team folder SAVED {hub_row['proof']['path']} {when}", (after, when)
                t3b["receipt_before"], t3b["receipt_after"], t3b["hub_row"], t3b["kernel_send"] = before, after, hub_row, t3_kernel

                # T3c: ordinary scrolling (the wheel) brings the receipt's history row out from
                # under the Chair's sticky capture bar; the receipt is still there.
                # PHILO-13-11 (slice two): the Brief is its own window; the wheel turns over
                # that window's body (the viewport's centre is the screen between windows).
                box = page.locator(".chair-window--brief .chair-window-body").bounding_box()
                vw, vh = 2 * box["x"] + box["width"], 2 * box["y"] + box["height"]
                target = h_sel
                page.mouse.move(vw / 2, vh / 2)
                clear = False
                for _ in range(24):
                    clear = page.evaluate("""(sel) => { const e = document.querySelector(sel); if (!e) return false; const r = e.getBoundingClientRect();
                      const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 4, r.top + 4], [r.right - 4, r.bottom - 4]];
                      return pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !!h && e.contains(h); }); }""", target)
                    if clear:
                        break
                    page.mouse.move(vw / 2, vh / 2)
                    page.mouse.wheel(0, 90)
                    page.wait_for_timeout(150)
                t3c = shots.shoot(page, "T3c-scrolled-clear-of-capture-bar", CH, [target], seat=None)
                t3c["cleared_by_wheel"] = clear
                assert clear, "the Team folder receipt was not reached by ordinary scrolling"
                assert receipt_now() == after

                shots.write("brief-send", {"brief": {"id": brief["id"], "ref": ref}, "hub_sends": self._sends(page, ref)})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── B1-B3 + T2: the decision window ─────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_decision_window_well_and_preview_changed(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                title = "Freeze the old ledger on Nov 3"
                dec = _api(page, "POST", "/api/decisions", {
                    "title": title, "status": "accepted", "deciders": ["Karol", "Priya"],
                    "context_markdown": "The cutover rehearsal showed two write paths into the old ledger.",
                    "decision_markdown": "Freeze the old ledger on Nov 3. All writes go to the new ledger after that day.",
                    "consequences_markdown": "- Finance runs one extra reconciliation.\n- Rollback window closes Nov 10."},
                    token=TOKEN)["decision"]
                ref = f"desk_decision:{dec['id']}"
                team, team_dir = self._dest(page, "Team folder")
                self._reload(page)
                self._open_decision(page, title, dec["id"])

                # B1: after CONSEQUENCES, SEND; the pick opens the preview and Send; nothing covers Send.
                self._pick(page, DD, "Team folder")
                b1 = shots.shoot(page, "B1-decision-window-picked", DD,
                                 [row(DD, "Team folder"), f"{opened(DD, 'Team folder')} [data-testid=send-verb]"])
                assert b1["wells"] == [ref], b1["wells"]
                if width == 1440:
                    assert 380 <= b1["window_width"] <= 440, b1["window_width"]   # the real ~400 px window
                footer = [" ".join(t.split()) for t in page.locator(".desk-window:has([data-seat=desk-decision]) .surface-footer .btn").all_inner_texts()]
                b1["footer_verbs"] = footer
                assert {"Copy", "Dictate about this", "Edit"} <= set(footer), footer   # R8: copy unchanged

                # B2: Send -> SAVED; the hub's row is the decision, its file the decision's words.
                self._press(page, DD, "Team folder")
                hub = self._sends(page, ref)
                assert [(s["document_ref"], s["state"]) for s in hub] == [(ref, "sent")], hub
                path = hub[0]["proof"]["path"]
                assert Path(path).parent == team_dir and "Nov 3" in Path(path).read_text()
                b2 = shots.shoot(page, "B2-decision-saved", DD,
                                 [f"{opened(DD, 'Team folder')} [data-receipt=latest]", f"{row(DD, 'Team folder')} [data-testid=send-last-sent]"],
                                 seat=row(DD, "Team folder"))
                assert b2["receipts"] == [{"text": f"✓ SAVED {path}", "state": "sent", "code": None}], b2["receipts"]
                b2["kernel_send"] = self._face_row_receipt(hub[0], ref)
                self._unpick(page, DD, "Team folder")
                b2b = shots.shoot(page, "B2b-decision-history", DD,
                                  [f"{DD} [data-testid=send-history] .surface-section-head", f"{DD} [data-testid=history-row]"])
                when = self._stamp(page, hub[0]["settled_at"])
                assert b2b["history_head"] == "SENDS 1" and b2b["history"] == [f"✓ Team folder SAVED {path} {when}"], b2b["history"]

                # B3: Edit after a send, on glass. Edit unmounts the well (it sends the stored
                # decision, not a draft); Done stores the edit and mounts it again; the preview
                # shows the new words and the verb is Send again; the press sends them.
                win = page.locator(".desk-window:has(.desk-decision-card)").last
                win.get_by_role("button", name="Edit", exact=True).click()
                page.locator(f"{DD} [data-testid=send-well]").wait_for(state="detached", timeout=T)
                pad = win.locator(".desk-decision-editor textarea").nth(1)
                pad.fill("Freeze the old ledger on Nov 5. All writes go to the new ledger after that day.")
                win.get_by_role("button", name="Done", exact=True).click()
                page.locator(f"{DD} [data-testid=destination-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(800)
                self._pick(page, DD, "Team folder")
                body = f"{opened(DD, 'Team folder')} [data-testid=send-preview-body]"
                page.wait_for_function("(s) => (document.querySelector(s)?.innerText || '').includes('Nov 5')", arg=body, timeout=T)
                b3verb = self._text(page, f"{opened(DD, 'Team folder')} [data-testid=send-verb]")
                page.evaluate("""(sel) => { const b = document.querySelector(sel);
                  const el = [...b.querySelectorAll('p, li')].find((e) => e.innerText.includes('Nov 5'));
                  if (el) { el.dataset.mark = 'b3-edit'; el.scrollIntoView({block: 'center'}); } }""", body)
                page.wait_for_timeout(300)
                b3 = shots.shoot(page, "B3-decision-edited-send-again", DD, ["[data-mark=b3-edit]"], seat=None)
                assert b3verb == "Send again", b3verb
                b3["verb"] = b3verb
                self._press(page, DD, "Team folder")
                edited = [s for s in self._sends(page, ref) if s["id"] != hub[0]["id"]]
                assert len(edited) == 1 and edited[0]["state"] == "sent", edited
                b3_decided = Path(edited[0]["proof"]["path"]).read_text().split("## Decision\n")[1].split("##")[0]
                assert "Nov 5" in b3_decided and "Nov 3" not in b3_decided, b3_decided
                b3b = shots.shoot(page, "B3b-decision-edited-sent", DD, [f"{opened(DD, 'Team folder')} [data-receipt=latest]"],
                                  seat=row(DD, "Team folder"))
                assert b3b["receipts"] == [{"text": f"✓ SAVED {edited[0]['proof']['path']}", "state": "sent", "code": None}], b3b["receipts"]
                b3b["kernel_send"] = self._face_row_receipt(edited[0], ref)
                self._unpick(page, DD, "Team folder")
                before_t2 = {s["id"] for s in self._sends(page, ref)}

                # T2: he reads the preview; the decision changes in another place; Send refuses
                # PREVIEW CHANGED, the well reads a fresh preview, another press sends it.
                self._pick(page, DD, "Team folder")
                assert "Nov 5" in page.locator(f"{opened(DD, 'Team folder')} [data-testid=send-preview-body]").inner_text()
                _api(page, "PUT", f"/api/decisions/{dec['id']}",
                     {"decision_markdown": "Freeze the old ledger on Nov 6. All writes go to the new ledger after that day."}, token=TOKEN)
                page.locator(f"{opened(DD, 'Team folder')} [data-testid=send-verb]").click()
                page.locator(f"{opened(DD, 'Team folder')} [data-testid=send-refused][data-code=preview_changed]").wait_for(timeout=T)
                page.wait_for_function("(s) => (document.querySelector(s)?.innerText || '').includes('Nov 6')",
                                       arg=f"{opened(DD, 'Team folder')} [data-testid=send-preview-body]", timeout=T)
                page.wait_for_timeout(500)
                t2a = shots.shoot(page, "T2a-preview-changed-fresh-preview", DD,
                                  [f"{opened(DD, 'Team folder')} [data-testid=send-refused]",
                                   f"{opened(DD, 'Team folder')} [data-testid=send-verb]"], seat=row(DD, "Team folder"))
                refused = self._text(page, f"{opened(DD, 'Team folder')} [data-testid=send-refused]")
                assert refused == "✗ REFUSED PREVIEW CHANGED NOTHING SENT", refused
                assert not t2a["no_answer_shown"]
                # T2a2: the changed passage itself (Nov 6), scrolled into view in the fresh preview.
                page.evaluate("""(sel) => { const b = document.querySelector(sel);
                  const el = [...b.querySelectorAll('p, li')].find((e) => e.innerText.includes('Nov 6'));
                  if (el) { el.dataset.mark = 'changed-passage'; el.scrollIntoView({block: 'center'}); } }""",
                              f"{opened(DD, 'Team folder')} [data-testid=send-preview-body]")
                page.wait_for_timeout(300)
                shots.shoot(page, "T2a2-preview-changed-passage", DD, ["[data-mark=changed-passage]"], seat=None)
                hub_mid = self._sends(page, ref)
                assert {s["id"] for s in hub_mid} == before_t2, hub_mid   # nothing sent by the refused press
                # The refused press is a kernel operation with its receipt (refused, preview_changed).
                refusals = self._kernel_refusals("channel.send", "preview_changed")
                assert len(refusals) == 1 and refusals[0]["receipt_state"] == "refused", refusals
                assert refusals[0]["target_ref"] == f"document:{ref}", refusals
                t2a["kernel_refusal"] = refusals[0]
                self._press(page, DD, "Team folder")
                hub2 = self._sends(page, ref)
                new = [s for s in hub2 if s["id"] not in before_t2]
                assert len(new) == 1 and new[0]["state"] == "sent" and new[0]["document_ref"] == ref, hub2
                path2 = new[0]["proof"]["path"]
                decided = Path(path2).read_text().split("## Decision\n")[1].split("##")[0]
                assert "Nov 6" in decided and "Nov 5" not in decided, decided   # the fresh words went
                t2b = shots.shoot(page, "T2b-preview-changed-sent", DD,
                                  [f"{opened(DD, 'Team folder')} [data-receipt=latest]"], seat=row(DD, "Team folder"))
                assert t2b["receipts"] == [{"text": f"✓ SAVED {path2}", "state": "sent", "code": None}], t2b["receipts"]
                t2b["kernel_send"] = self._face_row_receipt(new[0], ref)

                shots.write("decision-send", {"decision": dec["id"], "hub_sends": hub2})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── B4, B4b, B5: the decision RECORD -- the Room's rows and Intelligence -> DECISIONS ──

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_decision_record_wells_in_the_room_and_intelligence(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment
        from holdspeak.services.decision_record_service import DecisionRecordService
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        shots = Boards(SHOTS, width)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": PROJECT}, token=TOKEN)["project"]["id"]
                db = get_database()
                start = datetime.now().replace(microsecond=0) - timedelta(hours=3)
                segs = [TranscriptSegment(text="Two write paths still hit the old ledger.", speaker="Me", start_time=4.0, end_time=9.0),
                        TranscriptSegment(text="Finance runs one more reconciliation before the freeze.", speaker="Priya",
                                          start_time=10.0, end_time=16.0)]
                db.meetings.save_meeting(MeetingState(
                    id="m-sync", started_at=start, ended_at=start + timedelta(minutes=45), title="Ledger cutover sync",
                    segments=segs, intel=IntelSnapshot(timestamp=0.0, summary="The team agreed to freeze the old ledger.",
                                                       topics=["cutover"]), intel_status="completed"))
                _api(page, "POST", f"/api/projects/{pid}/meetings/m-sync", {}, token=TOKEN)
                # The decision_capture plugin's own output shape, then the bridge the intel queue runs.
                db.plugins.record_artifact(
                    artifact_id="m-sync-decisions", meeting_id="m-sync", artifact_type="decisions", title="Decisions",
                    plugin_id="decision_capture", status="draft",
                    structured_json={"decisions": [
                        {"decision": "Finance runs one more reconciliation before the freeze",
                         "rationale": "The last run found 3 unmatched entries.", "source_timestamp": 10.0},
                        {"decision": "Freeze the old ledger on Nov 3", "rationale": "Two write paths remain.",
                         "source_timestamp": 4.0}]})
                proposals = ProposalBridgeService(db).bridge_meeting_artifacts("m-sync")
                finance = next(p for p in proposals if p.text.startswith("Finance"))
                confirmed = _api(page, "POST", f"/api/proposals/{finance.id}/confirm", {}, token=TOKEN)
                mtg = confirmed.get("decision_record_id") or confirmed.get("record_id") or (confirmed.get("record") or {}).get("id")
                assert mtg, confirmed
                # The plain record: minted from the meeting's lifecycle decision (the service the MCP
                # tool decision_record.create_from_meeting calls).
                if not db.decisions.list(meeting_id="m-sync"):
                    db.decisions.reconcile_artifact("m-sync-decisions")
                freeze = next(d for d in db.decisions.list(meeting_id="m-sync") if d.text.startswith("Freeze"))
                plain = DecisionRecordService(db).create_from_meeting(None, freeze.id)["id"]
                team, team_dir = self._dest(page, "Team folder")
                # B4: an agent prepared a send of the meeting-proposal record (channel.prepare).
                r = self._agent().post("/api/channels/sends", json={"document_ref": f"decision_record:{mtg}", "destination_id": team})
                assert r.status_code == 200, r.text
                prepared = r.json()["send"]
                assert prepared["document_ref"] == f"decision_record:{mtg}", prepared   # never meeting_decision:<id>
                self._reload(page)

                page.locator("[aria-controls=desk-tool-shelf]").first.click()
                page.locator("[aria-controls=desk-palette-listbox]").fill(PROJECT)
                page.get_by_text(f"Open {PROJECT}").first.click(timeout=T)
                page.locator("[data-testid=room-body]").wait_for(timeout=T)
                page.locator("[data-testid=decision-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(1200)
                _settle(page)
                mtg_row = "[data-testid=decision-row]:has([data-testid=doc-prepared-chip])"
                b4 = shots.shoot(page, "B4-room-row-prepared-chip", "[data-testid=room-body]", [mtg_row], block="center")
                rows = [" ".join(t.split()) for t in page.locator("[data-testid=decision-row]").all_inner_texts()]
                b4["rows"] = rows
                assert len(rows) == 2, rows
                assert any(t.startswith("MTG Finance runs one more reconciliation") and "◆ PREPARED ×1" in t for t in rows), rows
                assert b4["room_open_verbs"] == [0, 0], b4["room_open_verbs"]   # G1: the dead Open withheld

                # B4b: the row unfolds in place and holds the record's well; the prepared row first.
                page.locator(mtg_row).first.click()
                page.locator(f"{RR} [data-testid=prepared-row]").wait_for(timeout=T)
                page.wait_for_timeout(500)
                b4b = shots.shoot(page, "B4b-room-row-open-prepared", "[data-testid=room-body]",
                                  [f"{RR} [data-testid=prepared-label]", f"{RR} [data-testid=prepared-send]"])
                assert b4b["wells"] == [f"decision_record:{mtg}"], b4b["wells"]
                assert b4b["prepared"][0].startswith(f"◆ Team folder ◆ PREPARED BY {AGENT_ID.upper()} D-{mtg.removeprefix('record-')[:6].upper()}"), b4b["prepared"]
                page.locator(f"{RR} [data-testid=prepared-send]").click()
                page.locator(f"{RR} [data-testid=prepared-result]").wait_for(timeout=T)
                page.wait_for_timeout(700)
                hub = self._sends(page, f"decision_record:{mtg}")
                assert [(s["id"], s["state"]) for s in hub] == [(prepared["id"], "sent")], hub
                kp = self._kernel(hub[0]["prepare_operation_id"])
                assert (kp["name"], kp["receipt_state"], kp["principal_identity"]) == ("channel.prepare", "succeeded", AGENT_ID), kp
                k_mtg = self._face_row_receipt(hub[0], f"decision_record:{mtg}")
                mpath = hub[0]["proof"]["path"]
                assert Path(mpath).parent == team_dir and "Finance runs one more reconciliation" in Path(mpath).read_text()
                b4c = shots.shoot(page, "B4c-room-row-prepared-saved", "[data-testid=room-body]",
                                  [f"{RR} [data-testid=prepared-result]"], block="center")
                assert b4c["prepared"][0].startswith(f"· Team folder ✓ SAVED {mpath}"), b4c["prepared"]
                assert b4c["history_head"] == "SENDS 1", b4c["history_head"]
                b4c["kernel_send"], b4c["kernel_prepare"] = k_mtg, kp
                page.locator("[data-testid=decision-row]", has_text="Finance runs").first.click()   # fold it again
                page.wait_for_timeout(400)

                # The plain row: unfolds, picks, sends ITS record.
                page.locator("[data-testid=decision-row]", has_text="Freeze the old ledger").first.click()
                page.locator(f"{RR} [data-testid=destination-row]").first.wait_for(timeout=T)
                self._pick(page, RR, "Team folder")
                self._press(page, RR, "Team folder")
                hub_plain = self._sends(page, f"decision_record:{plain}")
                assert [(s["document_ref"], s["state"]) for s in hub_plain] == [(f"decision_record:{plain}", "sent")], hub_plain
                ppath = hub_plain[0]["proof"]["path"]
                b4d = shots.shoot(page, "B4d-room-plain-row-saved", "[data-testid=room-body]",
                                  [f"{opened(RR, 'Team folder')} [data-receipt=latest]"], block="center")
                assert b4d["receipts"] == [{"text": f"✓ SAVED {ppath}", "state": "sent", "code": None}], b4d["receipts"]
                b4d["kernel_send"] = self._face_row_receipt(hub_plain[0], f"decision_record:{plain}")
                self._close_windows(page)

                # B5: Intelligence -> DECISIONS, the record: SEND after its fields.
                self._open_intelligence(page, "Decisions")
                page.locator(".desk-window .receipts-results .surface-ledger-line", has_text="Freeze the old ledger on Nov 3").first.click()
                page.locator(f"{DR} [data-testid=destination-row]").first.wait_for(timeout=T)
                self._pick(page, DR, "Team folder")
                b5 = shots.shoot(page, "B5-record-intelligence-picked", DR,
                                 [row(DR, "Team folder"), f"{opened(DR, 'Team folder')} [data-testid=send-verb]"])
                assert b5["wells"] == [f"decision_record:{plain}"], b5["wells"]
                assert "Send again" in [v["text"] for v in b5["send_verbs"]], b5["send_verbs"]   # the Room's send is this record's
                self._press(page, DR, "Team folder")
                hub_plain2 = self._sends(page, f"decision_record:{plain}")
                new = [s for s in hub_plain2 if s["id"] != hub_plain[0]["id"]]
                assert len(new) == 1 and new[0]["state"] == "sent", hub_plain2
                k_b5 = self._face_row_receipt(new[0], f"decision_record:{plain}")
                self._unpick(page, DR, "Team folder")
                b5b = shots.shoot(page, "B5b-record-intelligence-history", DR,
                                  [f"{DR} [data-testid=send-history] .surface-section-head", f"{DR} [data-testid=history-row]"])
                assert b5b["history_head"] == "SENDS 2", b5b["history_head"]
                assert any(h.startswith(f"✓ Team folder SAVED {new[0]['proof']['path']}") for h in b5b["history"]), b5b["history"]

                shots.write("record-send", {"records": {"mtg": mtg, "plain": plain},
                                            "hub_sends": {"mtg": hub, "plain": hub_plain2}})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()


class TestChairMeetingsAndBriefToSlack(_Rig):
    # ── C6b: the Chair's MEETINGS rows (both branches) + A6: the brief to Slack ──

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_chair_meeting_wells_and_the_brief_to_slack(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

        shots = Boards(SHOTS, width)
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
                slack = self._slack(page)
                assert self.keys.values and not self.edge.requests
                self._reload(page, "The week")

                ok_row = "li.surface-ledger-row:has(> [data-testid=arrival-meeting-row]):has([data-send=well][data-doc$=':c6-sync'])"
                rt_row = "li.surface-ledger-row:has(> [data-testid=arrival-meeting-row]):has([data-send=well][data-doc$=':c6-retry'])"
                OK = f"{ok_row} [data-seat=meeting]"
                RT = f"{rt_row} [data-seat=meeting]"
                page.locator(f"{OK} [data-testid=destination-row]").first.wait_for(timeout=T)
                page.locator(f"{RT} [data-testid=destination-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(600)

                # PHILO-13-11 (slice two): at 1440 The week is 36 % of the right column;
                # the meeting well is read with the window zoomed (board C1-4b).
                if width > 720:
                    page.get_by_role("button", name="Zoom The week").click()
                    page.wait_for_timeout(600)
                # C6b, the healthy branch: SUMMARY, then SEND with the form picker (44 px at 393).
                picker = f"{OK} [data-testid=doc-forms] select, {OK} [data-testid=doc-forms] .btn"
                c6 = shots.shoot(page, "C6b-chair-meetings-row-well", OK,
                                 [f"{ok_row} .meeting-summary-slab, {ok_row} [data-testid=meeting-summary-text]",
                                  f"{OK} [data-testid=doc-forms]", f"{OK} [data-testid=destination-row]"],
                                 seat=f"{ok_row} [data-testid=arrival-meeting-row]")
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
                          const L = cx - w / 2 + 1, R = cx + w / 2 - 1, T = cy - h / 2 + 1, B = cy + h / 2 - 1;
                          return [[cx, cy], [cx, T], [R, cy], [cx, B], [L, cy], [L, T], [R, T], [L, B], [R, B]]
                            .map(([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && p.contains(e); }); }""", picker)
                    c6["picker_after_scroll"] = {"capture_bars_over_the_week": bars_over_week, "nine_points_owned": owned_nine}
                    assert bars_over_week == 0 and all(owned_nine), c6["picker_after_scroll"]
                    shots.shoot(page, "C6f-chair-picker-scrolled-clear-393".replace("-393", ""), OK, [f"{OK} [data-testid=doc-forms]"], seat=None)

                # The send leg from the Chair row: face = hub row = kernel receipt.
                self._pick(page, OK, "Team folder")
                self._press(page, OK, "Team folder")
                mref = "meeting_summary:c6-sync"
                hub = self._sends(page, mref)
                assert [(s["document_ref"], s["state"]) for s in hub] == [(mref, "sent")], hub
                mpath = hub[0]["proof"]["path"]
                assert Path(mpath).parent == team_dir and "freeze the old ledger" in Path(mpath).read_text()
                c6s = shots.shoot(page, "C6c-chair-meetings-row-saved", OK,
                                  [f"{opened(OK, 'Team folder')} [data-receipt=latest]"], block="center")
                assert c6s["receipts"] == [{"text": f"✓ SAVED {mpath}", "state": "sent", "code": None}], c6s["receipts"]
                c6s["kernel_send"] = self._face_row_receipt(hub[0], mref)
                self._unpick(page, OK, "Team folder")

                # C6b, the retained-summary branch: the summary with its status facts, then SEND.
                c6r = shots.shoot(page, "C6e-chair-retained-summary-well", RT,
                                  [f"{rt_row} [data-testid=arrival-summary-status]", f"{RT} [data-testid=doc-forms]",
                                   f"{RT} [data-testid=destination-row]"],
                                  seat=f"{rt_row} [data-testid=arrival-meeting-row]")
                assert "meeting_summary:c6-retry" in c6r["wells"], c6r["wells"]
                assert "FAILED" in self._text(page, f"{rt_row} [data-testid=arrival-summary-status]")

                if width > 720:   # PHILO-13-11: the Chair's screen again (The week un-zoomed)
                    page.get_by_role("button", name="Zoom The week").click()
                    page.wait_for_timeout(400)
                # A6: the brief to Slack. A person signal (an agenda item on Priya's 1:1) puts a
                # People section in the brief; one item is acknowledged on the shelf. The
                # Slack-text preview carries the person lines and no Ack/Defer mark.
                _api(page, "POST", "/api/decisions", {"title": "Freeze the old ledger on Nov 3", "status": "proposed",
                                                     "decision_markdown": "Freeze the old ledger on Nov 3."}, token=TOKEN)
                _api(page, "POST", "/api/decisions", {"title": "Cut over by space, not by region", "status": "proposed",
                                                     "decision_markdown": "Cut over by space."}, token=TOKEN)
                _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
                priya = _api(page, "POST", "/api/people/relationships", {"display_name": "Priya Nair"}, token=TOKEN)["relationship"]["id"]
                _api(page, "POST", f"/api/people/relationships/{priya}/owner-aliases", {"alias": "Priya"}, token=TOKEN)
                one = _api(page, "POST", f"/api/people/relationships/{priya}/one-on-ones",
                           {"visibility": "shared_intent"}, token=TOKEN)["one_on_one"]["id"]
                _api(page, "POST", f"/api/people/one-on-ones/{one}/agenda",
                     {"body": "Review the rollback plan", "visibility": "shared_intent", "state": "open",
                      "source": {"kind": "brief"}}, token=TOKEN)
                brief = _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
                bref = f"monday_brief:{brief['id']}"
                items = [it for sec in brief["sections"].values() for it in sec]
                _api(page, "POST", f"/api/brief/items/{items[0]['id']}/shelf", {"state": "acknowledged"}, token=TOKEN)
                self._reload(page, "Brief")
                page.locator(f"{CH} [data-testid=destination-row]").first.wait_for(timeout=T)
                self._pick(page, CH, SLACK)
                body = f"{opened(CH, SLACK)} [data-testid=send-preview-body]"
                text = page.locator(body).inner_text()
                assert "*People*" in text and "Priya Nair" in text, text[-600:]
                assert not any(w in text.upper() for w in ("ACKNOWLEDGED", "DEFERRED", " ACK ", "DEFER")), text
                # The person line itself on screen (the Slack text is one text block: the line's own
                # range is scrolled into view and must be on top where it is drawn).
                on = page.evaluate("""([sel, t]) => { const b = document.querySelector(sel); if (!b) return false;
                  const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
                  for (let n = w.nextNode(); n; n = w.nextNode()) { const i = n.textContent.indexOf(t); if (i < 0) continue;
                    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + t.length);
                    for (let s = n.parentElement; s; s = s.parentElement) {
                      if (!(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) continue;
                      const rr = r.getBoundingClientRect(), sr = s.getBoundingClientRect();
                      s.scrollTop += rr.top - (sr.top + Math.min(sr.height / 3, 120)); }
                    const q = r.getBoundingClientRect(); const h = document.elementFromPoint(q.left + 2, q.top + q.height / 2);
                    return q.top >= 0 && q.bottom <= innerHeight && !!h && b.contains(h); }
                  return false; }""", [body, "Priya Nair"])
                page.wait_for_timeout(300)
                a6 = shots.shoot(page, "A6-brief-slack-person-sections", CH, [], seat=None)
                a6["person_line_on_screen"] = on
                assert on, "the person line is not on screen"
                page.evaluate("(sel) => document.querySelectorAll(sel + ' *').forEach((e) => { e.scrollTop = 0; })", opened(CH, SLACK))
                self._press(page, CH, SLACK)
                hub_s = [s for s in self._sends(page, bref) if s["destination_id"] == slack]
                assert [s["state"] for s in hub_s] == ["sent"], hub_s
                posted = json.loads(self.edge.requests[-1]["body"])["text"]
                assert self.edge.requests[-1]["host"] == "hooks.slack.com" and len(self.edge.requests) == 1, self.edge.requests
                # The bytes that went are the text he read: the preview is parsed back from them.
                assert "Priya Nair" in posted, posted[-400:]
                assert " ".join(posted.split()) == " ".join(text.split()), (posted[:300], text[:300])
                a6b = shots.shoot(page, "A6b-brief-slack-posted", CH, [f"{opened(CH, SLACK)} [data-receipt=latest]"],
                                  seat=row(CH, SLACK))
                assert a6b["receipts"] == [{"text": "✓ POSTED #leads", "state": "sent", "code": None}], a6b["receipts"]
                assert page.locator(f"{CH} [data-testid=proof][data-href]").count() == 0   # POSTED has no link
                a6b["kernel_send"] = self._face_row_receipt(hub_s[0], bref)
                assert not any(SECRET_MARK in str(v) for v in (page.content(), hub_s[0]))

                shots.write("chair-meetings-slack", {"hub_sends": {"meeting": hub, "brief_slack": hub_s},
                                                     "edge_requests": len(self.edge.requests)})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()
