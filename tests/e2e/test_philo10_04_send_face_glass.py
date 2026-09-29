"""PHILO-10-04 -- the Send face and the destinations, fenced AS RENDERED through
the real hub on an isolated HOME at 1440x900 and 393x852.

Built to the owner's ratified canvases ("Ratify as drawn", 2026-09-29):
pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/
and story-04-destinations-canvas/. Every board here runs on the REAL wire:
story 01's routes and the real file channel (a new file per send, written
and read back). The states come from real producers only:

* SAVED: a folder that takes the file.
* FAILED: a folder the OS refuses the create in (EACCES, mode 0555): the
  file channel's pinned `permission_denied`.
* UNKNOWN: story 01's own recipe (a folder path that leaves no room for the
  file's name: ENAMETOOLONG, off the pinned list).
* DESTINATION CHANGED: the saved folder now resolves elsewhere (renamed and a
  symlink left at its path). DESTINATION PARKED: removed in Settings.
* PREPARED: `channel.prepare` by a remote agent credential issued through
  the real Settings route, and by the owner.
* A lost answer and the reads that get no answer: injected at the browser's
  fetch (a lost answer lets the request reach the hub and commit; the reply
  is dropped).

Each hub record the face is compared with is read in the same test. The
GitHub, Jira, Confluence and email boards need stories 02 and 03's channels
(story 02 also moves the send route off the event loop, which the SENDING
boards need); they are not fenced here.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from ._send_face_glass import Boards
from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Send face glass needs Playwright")

TOKEN = "philo10-04-send-face"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
NAME = "Payments ledger cutover"
UP = "[data-testid=update-posture]"
DS = "[data-testid=destinations]"
REMOTE_HOST = "192.0.2.123"  # TEST-NET-1: never loopback
AGENT_ID = "remote-project-agent"

# The fetch seam: every call to a matched path is recorded; a mode can LOSE the
# answer (the request reaches the hub and commits; the reply is dropped) or
# FAIL it (no answer at all).
FETCH_SEAM = r"""(() => {
  if (window.__seam) return;
  window.__seam = true;
  window.__calls = [];
  try { window.__modes = JSON.parse(sessionStorage.getItem('__modes') || '{}'); } catch (e) { window.__modes = {}; }
  const real = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : input.url;
    const method = (init && init.method) || 'GET';
    const path = url.replace(/^https?:\/\/[^/]+/, '').split('?')[0];
    if (path.startsWith('/api/channels/')) {
      let body = {};
      try { body = init && init.body ? JSON.parse(init.body) : {}; } catch (e) { body = {}; }
      window.__calls.push({method, path, ...body});
    }
    const key = Object.keys(window.__modes).find((k) => { const [m, p] = k.split(' '); return m === method && new RegExp(p).test(path); });
    const mode = key ? window.__modes[key] : null;
    if (mode === 'fail') throw new TypeError('Failed to fetch');
    if (mode === 'lose-once') { delete window.__modes[key]; sessionStorage.setItem('__modes', JSON.stringify(window.__modes)); const res = await real(input, init); await res.text(); throw new TypeError('Failed to fetch'); }
    return real(input, init);
  };
})()"""


def _mode(page: Any, key: str, value: str | None) -> None:
    """Set (or clear) one fetch fault; it survives a reload of the page."""
    page.evaluate("""([k, v]) => { const m = window.__modes || {}; if (v === null) delete m[k]; else m[k] = v;
      window.__modes = m; sessionStorage.setItem('__modes', JSON.stringify(m)); }""", [key, value])


class _PinnedClock(datetime):
    """The boundary clock pinned: every send "leaves" at the same instant."""

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return datetime(2030, 1, 1, 9, 0, 0, tzinfo=tz)  # later than every real created_at: the read order cannot break the tie by luck


def _confirm(loc: Any, armed: str) -> None:
    """ConfirmVerb disarms after 3 s (a measured board outlasts that): arm again, then confirm."""
    if loc.inner_text().strip() != armed:
        loc.click()
        loc.page.wait_for_timeout(150)
    loc.click()


def _long_folder(root: Path) -> Path:
    """Story 01's UNKNOWN recipe: a folder whose path leaves no room for the file's name."""
    limit = os.pathconf("/", "PC_PATH_MAX")
    folder = root.resolve()
    while len(str(folder)) < limit - 25:
        folder = folder / ("a" * min(100, limit - 25 - len(str(folder)) - 1 or 1))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


class TestSendFaceGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.tmp = tmp_path
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        self.locked: list[Path] = []
        self.monkeypatch = monkeypatch
        try:
            yield
        finally:
            for p in self.locked:
                p.chmod(0o755)
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        ctx.add_init_script(FETCH_SEAM)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    @staticmethod
    def _stage(page: Any, key: str, scope: str) -> None:
        page.evaluate("""([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open',
            JSON.stringify({key, scope}))""", [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    def _room(self, page: Any, pid: str) -> None:
        self._stage(page, "open-project-memory", f"project:{pid}")
        page.locator("[data-testid=room-body]").wait_for(timeout=T)
        page.wait_for_timeout(900)
        _settle(page)

    @staticmethod
    def _published(page: Any, pid: str) -> str:
        uid = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"},
                   token=TOKEN)["update"]["id"]
        _api(page, "POST", f"/api/updates/{uid}/publish", {}, token=TOKEN)
        return uid

    @staticmethod
    def _dest(page: Any, name: str, folder: Path, synced: bool = False) -> str:
        return _api(page, "POST", "/api/channels/destinations",
                    {"name": name, "channel": "file", "folder": str(folder), "synced": synced},
                    token=TOKEN)["destination"]["id"]

    @staticmethod
    def _sends(page: Any, uid: str) -> list[dict[str, Any]]:
        return _api(page, "GET", f"/api/channels/sends?update_id={uid}", token=TOKEN)["sends"]

    @staticmethod
    def _deliveries(page: Any, pid: str, uid: str) -> list[dict[str, Any]]:
        ups = _api(page, "GET", f"/api/projects/{pid}/updates", token=TOKEN)["updates"]
        return next(u for u in ups if u["id"] == uid).get("deliveries", [])

    @staticmethod
    def _updates(page: Any) -> None:
        page.locator("[data-testid=updates-verb]").click()
        page.locator("[data-testid=update-list]").wait_for(timeout=T)
        page.wait_for_timeout(500)

    @staticmethod
    def _open_update(page: Any, uid: str) -> None:
        page.locator(f"[data-testid=update-list-item]:has([data-update-id='{uid}'])").first.click()
        page.locator("[data-testid=update-editor]").wait_for(timeout=T)
        page.locator("[data-testid=send-well]").wait_for(timeout=T)
        page.wait_for_timeout(600)

    @staticmethod
    def _back(page: Any) -> None:
        page.locator("[data-testid=update-verb-back]").click()
        page.locator("[data-testid=update-list]").wait_for(timeout=T)
        page.wait_for_timeout(500)

    @staticmethod
    def _row(name: str) -> str:
        """The destination's line (the library puts the testid on the line)."""
        return f"[data-testid=destination-row]:has([data-destination='{name}'])"

    @staticmethod
    def _prow(name: str) -> str:
        """A waiting prepared row: the whole <li> (its line and its open well)."""
        return f"li.surface-ledger-row:has(> [data-testid=prepared-row] [data-destination='{name}'])"

    @staticmethod
    def _drow(name: str) -> str:
        """A Destinations group row: the whole <li>."""
        return f"li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination='{name}'])"

    @staticmethod
    def _open_sel(name: str) -> str:
        return f"[data-testid=send-open][data-destination='{name}']"

    def _pick(self, page: Any, name: str) -> None:
        if not page.locator(self._open_sel(name)).count():
            page.locator(self._row(name)).first.click()
        page.locator(f"{self._open_sel(name)} [data-testid=send-preview], {self._open_sel(name)} [data-testid=preview-failed]").first.wait_for(timeout=T)
        page.wait_for_timeout(400)

    def _unpick(self, page: Any, name: str) -> None:
        if page.locator(self._open_sel(name)).count():
            page.locator(self._row(name)).first.click()
            page.locator(self._open_sel(name)).wait_for(state="detached", timeout=T)

    def _send(self, page: Any, name: str, *, double: bool = False) -> None:
        verb = page.locator(f"{self._open_sel(name)} [data-testid=send-verb], {self._open_sel(name)} [data-testid=send-retry]").first
        page.wait_for_function("(sel) => { const b = document.querySelector(sel); return b && !b.disabled; }",
                               arg=f"{self._open_sel(name)} [data-testid=send-verbs] .btn", timeout=T)
        verb.dblclick() if double else verb.click()
        page.wait_for_function("""(sel) => !!document.querySelector(sel + ' [data-receipt=latest]:not([data-state=dispatching]),' +
            sel + ' [data-testid=send-refused],' + sel + ' [data-testid=send-lost]')""", arg=self._open_sel(name), timeout=T)
        page.wait_for_timeout(600)

    @staticmethod
    def _focus(page: Any) -> None:
        """He comes back to the window: the wells read again (the canvas's return signal)."""
        page.evaluate("window.dispatchEvent(new Event('focus'))")
        page.wait_for_timeout(700)

    def _agent(self) -> Any:
        from starlette.testclient import TestClient

        client = TestClient(self.server.app, client=(REMOTE_HOST, 50000))
        headers = {"Authorization": f"Bearer {TOKEN}"}
        assert client.put("/api/settings/remote", json={"enabled": True}, headers=headers).status_code == 200
        issued = client.post("/api/settings/remote/credentials", json={"identity": AGENT_ID, "palette": "PROJECT"},
                             headers=headers)
        assert issued.status_code == 200, issued.text
        agent = TestClient(self.server.app, client=(REMOTE_HOST, 50001))
        agent.headers.pop("x-holdspeak-token", None)  # the app's own owner token: never the agent's
        agent.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
        return agent

    # ── 1: the first setup loop and the file channel's states ─────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_first_setup_loop_and_every_file_state(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                payments = self.tmp / "Reports" / "Payments"
                payments.mkdir(parents=True)
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)
                page.evaluate("window.__noReload = 1")

                # Board 1: no destination -- one token and one verb.
                page.locator("[data-testid=send-none]").wait_for(timeout=T)
                none = shots.shoot(page, "01-no-destination",
                                   ["[data-testid=send-none]", "[data-testid=send-add-destination]"])
                assert none["send_head"] == "SEND" and not none["destinations"]

                # B1 (B2 ruling): Add destination opens Settings AT the group, the form open.
                page.locator("[data-testid=send-add-destination]").click()
                page.locator("[data-testid=dest-form]").wait_for(timeout=T)
                page.wait_for_timeout(900)
                arrive = shots.shoot(page, "b01-arrive-from-room",
                                     ["[data-send=destinations] .gadget-group-label", "[data-testid=dest-form] select"],
                                     seat=None, anchor=DS)
                assert arrive["dest_head"] == "DESTINATIONS", arrive["dest_head"]

                # B2 + B3: the folder; the name fills from the target and stays editable.
                page.locator("[data-testid=dest-folder]").fill(str(payments))
                page.wait_for_timeout(200)
                assert page.locator("[data-testid=dest-name]").input_value() == "Folder Payments"
                shots.shoot(page, "b02-add-folder", ["[data-testid=dest-folder]", "[data-testid=dest-name]",
                                                     "[data-testid=dest-save]"], anchor=DS)
                page.locator("[data-testid=dest-save]").click()
                page.locator("[data-testid=dest-row]").first.wait_for(timeout=T)
                page.locator("[aria-label^='Close Settings']").first.click()
                page.wait_for_timeout(900)

                # Board 2: back in the Room, the new destination shows with no reload.
                page.locator(self._row("Folder Payments")).wait_for(timeout=T)
                back = shots.shoot(page, "02-back-in-the-room", [self._row("Folder Payments")])
                assert page.evaluate("window.__noReload") == 1, "the Room reloaded"
                assert back["destinations"] and "Folder Payments" in back["destinations"][0]

                # Three more, through the real routes: a synced folder, a folder the OS
                # refuses the create in, and story 01's UNKNOWN recipe.
                team = self.tmp / "Drive" / "Team"
                team.mkdir(parents=True)
                locked = self.tmp / "Locked"
                locked.mkdir()
                self._dest(page, "Team drive", team, synced=True)
                self._dest(page, "Locked folder", locked)
                self._dest(page, "Long path folder", _long_folder(self.tmp / "deep"))
                locked.chmod(0o555)
                self.locked.append(locked)
                self._focus(page)
                page.wait_for_function("document.querySelectorAll('[data-testid=destination-row]').length === 4")
                listed = shots.shoot(page, "03-destinations", [self._row("Folder Payments"), self._row("Team drive")])
                assert [r.split(" FILE ")[0].split(" ", 1)[1] for r in listed["destinations"]] == [
                    "Folder Payments", "Team drive", "Locked folder", "Long path folder"], listed["destinations"]
                assert "SYNCED FOLDER:cloud" in listed["egress_chips"] and "THIS DEVICE:local" in listed["egress_chips"]
                # The literal path keeps its case (the token species uppercases; the literal does not).
                assert "/Reports/Payments" in listed["destinations"][0], listed["destinations"][0]

                # Board 4 (A1): the pick opens the preview and Send in place.
                self._pick(page, "Folder Payments")
                picked = shots.shoot(page, "04-picked-folder",
                                     [self._row("Folder Payments"),
                                      f"{self._open_sel('Folder Payments')} [data-testid=send-preview-field] dd",
                                      f"{self._open_sel('Folder Payments')} [data-testid=send-verb]"])
                assert picked["preview_fields"] == [f"FOLDER {payments.resolve()}"], picked["preview_fields"]
                assert picked["send_verbs"] == [{"text": "Send", "disabled": False, "busy": False}], picked["send_verbs"]

                # Board 5: a DOUBLE click is one send; SAVED + the exact path.
                self._send(page, "Folder Payments", double=True)
                hub = self._sends(page, uid)
                saved = shots.shoot(page, "05-saved-folder",
                                    [f"{self._row('Folder Payments')} [data-testid=send-last-sent]",
                                     f"{self._open_sel('Folder Payments')} [data-testid=send-sent]"])
                assert [s["state"] for s in hub] == ["sent"], hub  # one dispatch for the double click
                path = hub[0]["proof"]["path"]
                assert Path(path).is_file() and Path(path).parent == payments.resolve()
                assert saved["receipts"] == [{"text": f"✓ SAVED {path}", "state": "sent", "code": None}], saved["receipts"]
                assert saved["send_verbs"][0]["text"] == "Send again"

                # Board 6: the history row from story 01's one table.
                dl = self._deliveries(page, pid, uid)
                page.locator("[data-testid=delivery-row]").first.wait_for(timeout=T)
                hist = shots.shoot(page, "06-saved-folder-history", ["[data-testid=delivery-row]"])
                assert hist["history_head"] == "DELIVERY 1", hist["history_head"]
                assert hist["history"][0].startswith(f"✓ Folder Payments SAVED {path}"), hist["history"]
                assert [d["outcome"] for d in dl] == ["sent"] and dl[0]["send_id"] == hub[0]["id"]

                # FAILED (the pinned create refusal): the row keeps LAST SEND FAILED.
                self._unpick(page, "Folder Payments")
                self._pick(page, "Locked folder")
                self._send(page, "Locked folder")
                failed = shots.shoot(page, "17-failed-folder",
                                     [f"{self._row('Locked folder')} [data-testid=send-last-failed]",
                                      f"{self._open_sel('Locked folder')} [data-testid=send-failed]"])
                assert failed["receipts"] == [{"text": "✗ FAILED NO PERMISSION NOTHING SENT", "state": "failed",
                                               "code": "permission_denied"}], failed["receipts"]

                # UNKNOWN (story 01's recipe): no automatic re-send; Send again is a new send.
                self._unpick(page, "Locked folder")
                self._pick(page, "Long path folder")
                self._send(page, "Long path folder")
                unknown = shots.shoot(page, "11-unknown-folder",
                                      [f"{self._row('Long path folder')} [data-testid=send-last-unknown]",
                                       f"{self._open_sel('Long path folder')} [data-testid=send-unknown]"])
                assert unknown["receipts"][0]["state"] == "unknown", unknown["receipts"]
                assert unknown["receipts"][0]["text"] == "⚠ RESULT UNKNOWN FILE NOT CONFIRMED", unknown["receipts"]
                assert unknown["send_verbs"][0]["text"] == "Send again"
                self._unpick(page, "Long path folder")

                # The manual row kept: Mark delivered.
                page.locator("[data-testid=deliver-to]").fill("Priya")
                page.locator("[data-testid=deliver-verb]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=delivery-row]').length >= 3", timeout=T)
                page.wait_for_timeout(500)
                hub_all = self._sends(page, uid)
                dl = self._deliveries(page, pid, uid)
                several = shots.shoot(page, "34-history-several", ["[data-testid=delivery-history]"])
                assert [(d["delivered_to"], d["channel"], d["outcome"]) for d in dl] == [
                    ("Folder Payments", "file", "sent"), ("Long path folder", "file", "unknown"),
                    ("Priya", "manual", "confirmed")], dl
                assert several["history_head"] == "DELIVERY 2", several["history_head"]
                assert several["history_outcomes"] == ["sent", "unknown", "confirmed"]
                assert several["history"][1].startswith("⚠ RESULT UNKNOWN · CHECK Long path folder FILE NOT CONFIRMED"), several["history"]
                assert several["history"][2].startswith("✓ Priya DELIVERED MANUAL"), several["history"]
                # FAILED writes no history row (nothing was delivered).
                assert sorted(s["state"] for s in hub_all) == ["failed", "sent", "unknown"], hub_all
                last = "[data-testid=delivery-history] > li:last-child > [data-testid=delivery-row]"
                shots.shoot(page, "34b-history-manual", [last], seat=f"CENTER:{last}")

                # A2: the list chip is DELIVERY ×N, the same count (isDelivered).
                self._back(page)
                chips = shots.shoot(page, "35-list-chips", ["[data-testid=update-delivered-chip]",
                                                            "[data-testid=update-unknown-chip]"])
                assert chips["list_chips"] == ["⚠ RESULT UNKNOWN ×1", "✓ DELIVERY ×2"], chips["list_chips"]
                assert not chips["words_delivered_word"]

                # A draft has no SEND well.
                page.locator("[data-testid=update-verb-draft-deterministic]").click()
                page.locator("[data-testid=update-editor][data-lifecycle=draft]").wait_for(timeout=T)
                page.wait_for_timeout(600)
                draft = shots.shoot(page, "36-draft-no-send", ["[data-testid=update-verb-back]"], seat=None)
                assert not draft["send_well_present"] and draft["history_head"] is None
                shots.write("send-face-file", {"hub_sends": hub_all, "hub_deliveries": dl})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── 2: prepared sends (A3), the latest by dispatch, the refusals ───────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_prepared_sends_and_the_latest_result(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                folders = {n: self.tmp / n for n in ("Payments", "Ledger", "Moved", "Old")}
                for f in folders.values():
                    f.mkdir()
                ids = {
                    "Folder Payments": self._dest(page, "Folder Payments", folders["Payments"]),
                    "Folder Ledger": self._dest(page, "Folder Ledger", folders["Ledger"]),
                    "Folder Moved": self._dest(page, "Folder Moved", folders["Moved"]),
                    "Folder Old": self._dest(page, "Folder Old", folders["Old"]),
                }
                agent = self._agent()
                prepared: dict[str, str] = {}
                for name in ("Folder Payments", "Folder Moved", "Folder Old"):
                    r = agent.post("/api/channels/sends", json={"update_id": uid, "destination_id": ids[name]})
                    assert r.status_code == 200, r.text
                    prepared[name] = r.json()["send"]["id"]
                prepared["Folder Ledger"] = _api(page, "POST", "/api/channels/sends",
                                                 {"update_id": uid, "destination_id": ids["Folder Ledger"]},
                                                 token=TOKEN)["send"]["id"]
                self._room(page, pid)
                self._updates(page)
                listed = shots.shoot(page, "35b-list-prepared", ["[data-testid=update-prepared-chip]"])
                assert listed["list_chips"] == ["◆ PREPARED ×4"], listed["list_chips"]
                self._open_update(page, uid)

                # Board 26 (A3): prepared first, ONE preview open (the first).
                page.locator("[data-testid=prepared-open]").wait_for(timeout=T)
                first = shots.shoot(page, "26-prepared", ["[data-testid=prepared-row]",
                                                          "[data-testid=prepared-open] [data-testid=prepared-send]"])
                assert first["prepared_open"] == 1 and len(first["prepared"]) == 4, first["prepared"]
                assert first["prepared"][0].startswith("◆ Folder Payments ◆ PREPARED BY REMOTE-PROJECT-AGENT"), first["prepared"]
                assert any("BY YOU" in r for r in first["prepared"]), first["prepared"]
                order = page.evaluate("() => [...document.querySelectorAll('[data-testid=send-well] [data-testid=prepared-list], "
                                      "[data-testid=send-well] [data-testid=destination-list]')].map((e) => e.dataset.testid)")
                assert order == ["prepared-list", "destination-list"], order

                # Board 29: the prepared file send; it stays as its result.
                page.locator("[data-testid=prepared-open] [data-testid=prepared-send]").click()
                page.wait_for_function(f"""() => !!document.querySelector("[data-testid=prepared-result] [data-state=sent]")""", timeout=T)
                page.wait_for_timeout(600)
                hub = {s["id"]: s for s in self._sends(page, uid)}
                sent = hub[prepared["Folder Payments"]]
                done = shots.shoot(page, "29-prepared-file-sent", ["[data-testid=prepared-result]"])
                assert sent["state"] == "sent" and sent["proof"]["path"] == sent["file_path"], sent
                assert done["prepared_results"][0].startswith(f"· Folder Payments ✓ SAVED {sent['proof']['path']}"), done["prepared_results"]
                assert done["prepared_open"] == 1  # the next prepared row opens

                # 28b / 28c: an inline send to Ledger first (SAVED), then the OLDER
                # preparation is sent and FAILS: the destination shows the latest to leave.
                # Codex Astra r1 F3 on #697: the boundary clock PINNED, so both sends
                # carry the same dispatch_started_at; the order is the hub's dispatch_seq.
                from holdspeak.services import channel_service as _cs
                self.monkeypatch.setattr(_cs, "datetime", _PinnedClock)
                self._pick(page, "Folder Ledger")
                self._send(page, "Folder Ledger")
                self._unpick(page, "Folder Ledger")
                folders["Ledger"].chmod(0o555)
                self.locked.append(folders["Ledger"])
                row = self._prow("Folder Ledger")
                if not page.locator(f"{row} [data-testid=prepared-open]").count():
                    page.locator(f"{row} > .surface-ledger-line").click()
                page.locator(f"{row} [data-testid=prepared-send]").click()
                page.wait_for_function("""() => [...document.querySelectorAll('[data-testid=prepared-result] [data-state]')]
                    .some((e) => e.dataset.state === 'failed')""", timeout=T)
                page.wait_for_timeout(600)
                shots.shoot(page, "28-prepared-failed", ["[data-testid=prepared-result] [data-state=failed]"])
                hub = {s["id"]: s for s in self._sends(page, uid)}
                self.monkeypatch.setattr(_cs, "datetime", datetime)
                ledger = sorted((s for s in hub.values() if s["destination_id"] == ids["Folder Ledger"]),
                                key=lambda s: s["dispatch_seq"])
                assert [s["state"] for s in ledger] == ["sent", "failed"], ledger
                assert ledger[0]["dispatch_started_at"] == ledger[1]["dispatch_started_at"], ledger  # an equal clock
                assert ledger[0]["dispatch_seq"] < ledger[1]["dispatch_seq"], ledger
                assert ledger[-1]["id"] == prepared["Folder Ledger"]  # prepared first, left last
                latest = shots.shoot(page, "28b-destination-latest-failed",
                                     [f"{self._row('Folder Ledger')} [data-testid=send-last-failed]"])
                self._pick(page, "Folder Ledger")
                reopened = shots.shoot(page, "28c-destination-reopened",
                                       [f"{self._open_sel('Folder Ledger')} [data-testid=send-failed]"])
                assert [r["state"] for r in reopened["receipts"]] == ["failed"], reopened["receipts"]
                assert "✓" not in " ".join(r["text"] for r in reopened["receipts"])
                self._unpick(page, "Folder Ledger")

                # Board 30: the folder now resolves elsewhere: DESTINATION CHANGED; only Discard.
                moved = folders["Moved"]
                moved.rename(self.tmp / "Moved-elsewhere")
                moved.symlink_to(self.tmp / "Moved-elsewhere")
                row = self._prow("Folder Moved")
                if not page.locator(f"{row} [data-testid=prepared-open]").count():
                    page.locator(f"{row} > .surface-ledger-line").click()
                page.locator(f"{row} [data-testid=prepared-send]").click()
                page.locator(f"{row} [data-testid=prepared-refused-chip]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                changed = shots.shoot(page, "30-prepared-destination-changed",
                                      [f"{row} [data-testid=prepared-refused-chip]", f"{row} [data-testid=prepared-discard]"])
                assert page.locator(f"{row} [data-testid=prepared-refused-chip]").get_attribute("data-code") == "destination_changed"
                assert page.locator(f"{row} [data-testid=prepared-send]").count() == 0
                assert self._sends(page, uid) and {s["id"]: s for s in self._sends(page, uid)}[prepared["Folder Moved"]]["state"] == "prepared"
                assert changed["prepared_open"] == 1

                # Board 31: removed in Settings: DESTINATION PARKED.
                _api(page, "DELETE", f"/api/channels/destinations/{ids['Folder Old']}", {}, token=TOKEN)
                self._focus(page)
                row = self._prow("Folder Old")
                page.locator(f"{row} > .surface-ledger-line").click()
                page.locator(f"{row} [data-testid=prepared-send]").click()
                page.locator(f"{row} [data-testid=prepared-refused-chip]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                shots.shoot(page, "31-prepared-destination-parked", [f"{row} [data-testid=prepared-refused-chip]",
                                                                     f"{row} [data-testid=prepared-discard]"])
                assert page.locator(f"{row} [data-testid=prepared-refused-chip]").get_attribute("data-code") == "destination_parked"

                # Boards 32, 33: Discard armed, then DISCARDED stays as the row's result.
                discard = page.locator(f"{row} [data-testid=prepared-discard]")
                discard.click()
                page.wait_for_timeout(200)
                assert discard.inner_text().strip() == "Discard?"
                shots.shoot(page, "32-discard-armed", [f"{row} [data-testid=prepared-discard]"])
                _confirm(discard, "Discard?")
                page.wait_for_function("""() => [...document.querySelectorAll('[data-testid=prepared-result] [data-state]')]
                    .some((e) => e.dataset.state === 'discarded')""", timeout=T)
                page.wait_for_timeout(500)
                gone = shots.shoot(page, "33-discarded", ["[data-testid=prepared-result] [data-state=discarded]"])
                hub = {s["id"]: s for s in self._sends(page, uid)}
                assert hub[prepared["Folder Old"]]["state"] == "discarded"
                old_row = [r for r in gone["prepared_results"] if r.startswith("· Folder Old ")]
                assert len(old_row) == 1 and "DISCARDED" in old_row[0] and "BY REMOTE-PROJECT-AGENT" in old_row[0], gone["prepared_results"]
                assert latest["last_chips"] and any("LAST SEND FAILED" in c for c in latest["last_chips"])
                shots.write("send-face-prepared", {"hub_sends": list(hub.values())})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── 3: a lost answer and the reads that get no answer ────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_lost_answer_and_every_unreadable_read_are_named(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                a = self._published(page, pid)
                b = self._published(page, pid)
                out = self.tmp / "Payments"
                out.mkdir()
                self._dest(page, "Folder Payments", out)
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, a)

                # Board 21: the send settles at the hub, its answer is lost.
                self._pick(page, "Folder Payments")
                _mode(page, "POST ^/api/channels/send$", "lose-once")
                self._send(page, "Folder Payments")
                lost = shots.shoot(page, "21-lost-answer-a", [f"{self._open_sel('Folder Payments')} [data-testid=send-lost]",
                                                              f"{self._open_sel('Folder Payments')} [data-testid=send-retry]"])
                assert lost["receipts"][0]["text"] == "⚠ NO ANSWER · RESULT UNKNOWN", lost["receipts"]

                # Update B stays clean; back on A the lost line and Retry are there.
                self._back(page)
                self._open_update(page, b)
                update_b_clean = (page.locator("[data-testid=send-lost]").count() == 0
                                  and page.locator("[data-testid=send-retry]").count() == 0
                                  and page.locator("[data-testid=send-open]").count() == 0)
                self._back(page)
                self._open_update(page, a)
                back_on_a = (page.locator("[data-testid=send-lost]").count() == 1
                             and page.locator("[data-testid=send-retry]").count() == 1)
                assert update_b_clean and back_on_a, (update_b_clean, back_on_a)

                # Board 24: Retry reuses the key; the hub answers the settled row: ONE file.
                page.locator("[data-testid=send-retry]").click()
                page.locator(f"{self._open_sel('Folder Payments')} [data-testid=send-sent]").wait_for(timeout=T)
                page.wait_for_timeout(500)
                calls = [c for c in page.evaluate("window.__calls") if c["path"] == "/api/channels/send"]
                hub_a, hub_b = self._sends(page, a), self._sends(page, b)
                retried = shots.shoot(page, "24-retried-one-dispatch",
                                      [f"{self._open_sel('Folder Payments')} [data-testid=send-sent]"])
                assert len(calls) == 2 and calls[0]["command_id"] == calls[1]["command_id"], calls
                assert [s["state"] for s in hub_a] == ["sent"] and hub_b == [], (hub_a, hub_b)
                assert len(list(out.iterdir())) == 1, list(out.iterdir())  # dispatches with the lost key = 1
                assert retried["receipts"][0]["state"] == "sent"
                self._unpick(page, "Folder Payments")

                # Board 37: the destinations read gets no answer.
                _mode(page, "GET ^/api/channels/destinations$", "fail")
                self._focus(page)
                page.locator("[data-testid=destinations-unreadable]").wait_for(timeout=T)
                d_fail = shots.shoot(page, "37-destinations-unreadable", ["[data-testid=destinations-unreadable]"])
                assert "CANNOT READ DESTINATIONS" in page.locator("[data-testid=destinations-unreadable]").inner_text()
                assert page.locator("[data-testid=send-none]").count() == 0 and not d_fail["destinations"]
                _mode(page, "GET ^/api/channels/destinations$", None)
                page.locator("[data-testid=destinations-unreadable-retry]").click()
                page.locator(self._row("Folder Payments")).wait_for(timeout=T)

                # Board 38: the sends read gets no answer (he opens the update again).
                self._back(page)
                _mode(page, "GET ^/api/channels/sends$", "fail")
                page.locator(f"[data-testid=update-list-item]:has([data-update-id='{a}'])").first.click()
                page.locator("[data-testid=sends-unreadable]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                shots.shoot(page, "38-sends-unreadable", ["[data-testid=sends-unreadable]"])
                _mode(page, "GET ^/api/channels/sends$", None)
                page.locator("[data-testid=sends-unreadable-retry]").click()
                page.locator("[data-testid=sends-unreadable]").wait_for(state="detached", timeout=T)

                # Board 39: the history read gets no answer.
                self._back(page)
                _mode(page, "GET ^/api/projects/[^/]+/updates$", "fail")
                page.locator(f"[data-testid=update-list-item]:has([data-update-id='{a}'])").first.click()
                page.locator("[data-testid=history-unreadable]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                shots.shoot(page, "39-history-unreadable", ["[data-testid=history-unreadable]"])
                _mode(page, "GET ^/api/projects/[^/]+/updates$", None)
                page.locator("[data-testid=history-unreadable-retry]").click()
                page.locator("[data-testid=history-unreadable]").wait_for(state="detached", timeout=T)

                # Board 40: the preview gets no answer: NO PREVIEW; Send is not offered.
                _mode(page, "POST ^/api/channels/preview$", "fail")
                self._pick(page, "Folder Payments")
                pv = shots.shoot(page, "40-preview-failed", [f"{self._open_sel('Folder Payments')} [data-testid=preview-failed]"])
                assert pv["send_verbs"] == [], pv["send_verbs"]
                assert "NO PREVIEW" in page.locator("[data-testid=preview-failed]").inner_text()
                shots.write("send-face-faults", {"calls": page.evaluate("window.__calls"), "hub_a": hub_a,
                                                 "update_b_clean": update_b_clean, "back_on_a_before_retry": back_on_a})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── 3b: a known FAILED outlives a failed read (Codex Astra r1 F1 on #697) ──

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_known_failure_outlives_a_failed_sends_read(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                out = self.tmp / "Payments"
                out.mkdir()
                self._dest(page, "Folder Payments", out)
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)
                self._pick(page, "Folder Payments")
                self._send(page, "Folder Payments")
                # The folder turns unwritable, and every sends read from now on gets no answer.
                out.chmod(0o555)
                self.locked.append(out)
                _mode(page, "GET ^/api/channels/sends$", "fail")
                verb = page.locator(f"{self._open_sel('Folder Payments')} [data-testid=send-verb]")
                assert verb.inner_text().strip() == "Send again"
                verb.click()
                page.locator(f"{self._open_sel('Folder Payments')} [data-receipt=latest][data-state=failed]").wait_for(timeout=T)
                page.wait_for_timeout(900)
                calls = [c for c in page.evaluate("window.__calls") if c["path"] == "/api/channels/sends" and c["method"] == "GET"]
                _mode(page, "GET ^/api/channels/sends$", None)
                hub = sorted(self._sends(page, uid), key=lambda s: s["dispatch_seq"])
                f = shots.shoot(page, "r1-failed-read-keeps-failure",
                                [f"{self._row('Folder Payments')} [data-testid=send-last-failed]",
                                 f"{self._open_sel('Folder Payments')} [data-testid=send-failed]"])
                assert [s["state"] for s in hub] == ["sent", "failed"], hub
                assert calls, "the sends read after the press was not attempted"
                assert [r["state"] for r in f["receipts"]] == ["failed"], f["receipts"]
                assert f["receipts"][0]["code"] == "permission_denied", f["receipts"]
                assert any("LAST SEND FAILED" in c for c in f["last_chips"]) and not any("SAVED" in c for c in f["last_chips"]), f["last_chips"]
                assert page.locator("[data-testid=sends-unreadable]").count() == 1  # the failed read is named too
                shots.write("send-face-failed-read", {"hub_sends": hub})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── 4: the Destinations group in Settings -> Connections ──────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_destinations_group(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, DS)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                reports = self.tmp / "Reports"
                reports.mkdir()
                drive = self.tmp / "Drive"
                drive.mkdir()
                self._stage(page, "configure-settings", "integrations")
                page.locator(DS).wait_for(timeout=T)
                page.wait_for_timeout(900)

                # With no destination the add form is the group (no counter of zero).
                form = shots.shoot(page, "b02b-empty-group", ["[data-send=destinations] .gadget-group-label",
                                                              "[data-testid=dest-form] select"])
                assert form["dest_head"] == "DESTINATIONS", form["dest_head"]

                # B3: a synced folder: SYNCED FOLDER, not THIS DEVICE.
                page.locator("[data-testid=dest-folder]").fill(str(drive))
                page.locator("[data-testid=dest-form] label.gadget-check-token").click()
                page.wait_for_timeout(200)
                synced = shots.shoot(page, "b03-add-synced-folder", ["[data-testid=dest-form] label.gadget-check-token",
                                                                     "[data-testid=dest-form-verbs] .gadget-chip-egress"])
                assert "SYNCED FOLDER:cloud" in synced["egress_chips"], synced["egress_chips"]

                # The other channels' forms, as drawn (their Save is story 02 / 03's wire).
                select = page.locator("[data-testid=dest-form] select").first
                for board, value, fill in (
                    ("b04-add-github", "github", [("[data-testid=dest-repo]", "karol/Payments-Ops"), ("[data-testid=dest-number]", "42")]),
                    ("b06-add-confluence", "confluence", [("[data-testid=dest-space]", "98304")]),
                    ("b08-add-email", "email", [("[data-testid=dest-from]", "Karol@Acme.io"), ("[data-testid=dest-to]", "lena@acme.io, tomas@acme.io")]),
                ):
                    select.select_option(value)
                    page.wait_for_timeout(200)
                    for sel, text in fill:
                        page.locator(sel).fill(text)
                    page.wait_for_timeout(200)
                    f = shots.shoot(page, board, [fill[-1][0], "[data-testid=dest-name]"])
                    assert page.locator("[data-testid=dest-form]").get_attribute("data-channel") == value
                    name = page.locator("[data-testid=dest-name]").input_value()
                    assert name == {"github": "karol/Payments-Ops #42", "confluence": "Confluence space 98304",
                                    "email": "Email lena@acme.io"}[value], name
                    if value == "email":
                        key_row = page.locator("[data-testid=dest-key-row]").inner_text()
                        assert key_row.split("\n")[:2] == ["SendGrid key", "—"], key_row  # present or absent; never the key
                        assert "API.SENDGRID.COM:cloud" in f["egress_chips"], f["egress_chips"]

                # Save two folders (the synced one and one on this device).
                select.select_option("file")
                page.locator("[data-testid=dest-folder]").fill(str(drive))
                page.locator("[data-testid=dest-form] label.gadget-check-token").click()
                page.locator("[data-testid=dest-save]").click()
                page.locator("[data-testid=dest-row]").first.wait_for(timeout=T)
                page.locator("[data-testid=dest-add]").click()
                page.locator("[data-testid=dest-folder]").fill(str(reports))
                page.locator("[data-testid=dest-save]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=dest-row]').length === 2", timeout=T)
                page.wait_for_timeout(400)
                hub = _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                lst = shots.shoot(page, "b09-list", ["[data-testid=dest-list]"])
                assert lst["dest_head"] == "DESTINATIONS 2", lst["dest_head"]
                assert sorted((d["name"], d["synced"]) for d in hub) == [("Folder Drive", True), ("Folder Reports", False)], hub

                # B10: the row open, checked.
                row = self._drow("Folder Reports")
                page.locator(f"{row} > .surface-ledger-line").click()
                page.locator(f"{row} [data-testid=dest-check]").click()
                page.locator(f"{row} [data-testid=dest-check-result]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                shots.shoot(page, "b10-row-open-checked", [f"{row} [data-testid=dest-check-result]"])
                assert page.locator(f"{row} [data-testid=dest-check-result]").inner_text().split() == ["✓", "CHECKED"]
                assert page.locator(f"{row} [data-testid=dest-check-result]").get_attribute("data-code") == "ready"
                assert "CHECKED" in page.locator(f"{row} [data-testid=dest-open] dl").inner_text().upper()  # the canvas's Checked time

                # B12, B13: Edit saves a new row and parks the old one.
                page.locator(f"{row} [data-testid=dest-edit]").click()
                page.locator(f"{row} [data-testid=dest-name]").fill("Reports folder")
                shots.shoot(page, "b12-edit", [f"{row} [data-testid=dest-name]", f"{row} [data-testid=dest-save]"])
                page.locator(f"{row} [data-testid=dest-save]").click()
                page.locator("[data-testid=dest-parked]").wait_for(timeout=T)
                page.locator("[data-testid=dest-parked] .gadget-fold-summary, [data-testid=dest-parked] summary").first.click()
                page.wait_for_timeout(300)
                edited = shots.shoot(page, "b13-edited-old-parked", ["[data-testid=dest-parked-row]"])
                hub = _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                assert sorted((d["name"], d["state"]) for d in hub) == [
                    ("Folder Drive", "active"), ("Folder Reports", "parked"), ("Reports folder", "active")], hub
                assert edited["dest_parked"][0].startswith("Folder Reports FILE"), edited["dest_parked"]

                # B14, B15: Remove armed, then parked with its history.
                row = self._drow("Folder Drive")
                page.locator(f"{row} > .surface-ledger-line").click()
                remove = page.locator(f"{row} [data-testid=dest-remove]")
                remove.click()
                page.wait_for_timeout(150)
                assert remove.inner_text().strip() == "Remove?"
                shots.shoot(page, "b14-remove-armed", [f"{row} [data-testid=dest-remove]"])
                # Codex Astra r1 F2 on #697: a Remove with no answer stays open, named, with Retry.
                _mode(page, "DELETE ^/api/channels/destinations/", "fail")
                _confirm(remove, "Remove?")
                page.locator(f"{row} [data-testid=dest-remove-failed]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                not_removed = shots.shoot(page, "b14b-remove-failed", [f"{row} [data-testid=dest-remove-failed]",
                                                                      f"{row} [data-testid=dest-remove-retry]"])
                hub_nr = _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                assert next(d for d in hub_nr if d["name"] == "Folder Drive")["state"] == "active", hub_nr
                assert page.locator(f"{row} [data-testid=dest-open]").count() == 1
                assert page.locator(f"{row} [data-testid=dest-remove-failed]").inner_text().split("\n")[:3] == [
                    "✗", "NOT REMOVED", "NO ANSWER"], page.locator(f"{row} [data-testid=dest-remove-failed]").inner_text()
                assert not_removed["dest_head"] == "DESTINATIONS 2"
                _mode(page, "DELETE ^/api/channels/destinations/", None)
                page.locator(f"{row} [data-testid=dest-remove-retry]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=dest-row]').length === 1", timeout=T)
                page.wait_for_timeout(400)
                if not page.locator("[data-testid=dest-parked-row]").count():
                    page.locator("[data-testid=dest-parked] .gadget-fold-summary, [data-testid=dest-parked] summary").first.click()
                removed = shots.shoot(page, "b15-removed-parked", ["[data-testid=dest-parked]"])
                hub = _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                assert sorted(d["state"] for d in hub) == ["active", "parked", "parked"], hub
                assert len(removed["dest_parked"]) == 2 and removed["dest_head"] == "DESTINATIONS 1"

                # B16: the read gets no answer: CANNOT READ DESTINATIONS, never the empty form.
                _mode(page, "GET ^/api/channels/destinations$", "fail")
                self._stage(page, "configure-settings", "integrations")
                page.locator("[data-testid=dest-unreadable]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                shots.shoot(page, "b16-destinations-unreadable", ["[data-testid=dest-unreadable]"])
                assert page.locator("[data-testid=dest-form]").count() == 0
                shots.write("destinations-group", {"hub": hub})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()
