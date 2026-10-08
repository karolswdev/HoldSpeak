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
from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle, park_builtin_folder
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


class _Rig:
    """The hub, the browser and the Room/Settings navigation shared by the Send face fences."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.tmp = tmp_path
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        park_builtin_folder()  # the desk these boards were drawn on (glass_infra.park_builtin_folder)
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
        drafted = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"},
                       token=TOKEN)["update"]
        uid = drafted["id"]
        # PHILO-15 B64: an update with no verified claim is refused; the
        # owner's saved line is reviewed (the draft's shape kept).
        mine = OWNER_BODY
        _api(page, "PUT", f"/api/updates/{uid}", {"body_md": mine}, token=TOKEN)
        _api(page, "POST", f"/api/updates/{uid}/publish", {}, token=TOKEN)
        return uid

    @staticmethod
    def _dest(page: Any, name: str, folder: Path, synced: bool = False) -> str:
        return _api(page, "POST", "/api/channels/destinations",
                    {"name": name, "channel": "file", "folder": str(folder), "synced": synced},
                    token=TOKEN)["destination"]["id"]

    @staticmethod
    def _sends(page: Any, uid: str) -> list[dict[str, Any]]:
        return _api(page, "GET", f"/api/channels/sends?document_ref=project_update:{uid}", token=TOKEN)["sends"]

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


#: PHILO-15 B64: the owner's saved update (an update with no verified claim is
#: refused); the six sections keep the well's layout of a full update.
OWNER_BODY = (
    "## Progress\n\nThe ledger cutover is on track.\n\n## Decisions\n\nNo decisions in this window.\n\n"
    "## Risks & Blockers\n\nNo risks or blockers in this window.\n\n## Dependencies\n\nNo dependencies tracked.\n\n"
    "## Next Actions\n\nNo upcoming actions.\n\n## Source Coverage\n\nAll sources consulted successfully.\n"
)


class TestSendFaceGlass(_Rig):
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
                # The literal keeps its case (the token species uppercases; the literal does not).
                # PHILO-15 lane 12 (B23): the row reads the folder by its NAME (its last two
                # folder names); the full path is the target's hover title.
                assert "Reports/Payments" in listed["destinations"][0], listed["destinations"][0]
                target_title = page.locator(f"{self._row('Folder Payments')} .send-target").first.get_attribute("title")
                assert target_title and target_title.endswith("/Reports/Payments"), target_title

                # Board 4 (A1): the pick opens the preview and Send in place.
                self._pick(page, "Folder Payments")
                picked = shots.shoot(page, "04-picked-folder",
                                     [self._row("Folder Payments"),
                                      f"{self._open_sel('Folder Payments')} [data-testid=send-preview-field] dd",
                                      f"{self._open_sel('Folder Payments')} [data-testid=send-verb]"])
                # B23: the preview's Folder field is the folder's name, never the raw path.
                assert picked["preview_fields"] == [f"FOLDER {'/'.join(payments.resolve().parts[-2:])}"], picked["preview_fields"]
                assert picked["send_verbs"] == [{"text": "Send", "disabled": False, "busy": False}], picked["send_verbs"]

                # Board 5: a DOUBLE click is one send; SAVED + the exact path.
                self._send(page, "Folder Payments", double=True)
                hub = self._sends(page, uid)
                # Codex Astra r2 on #697: the long receipt itself is brought into view (centred), so the
                # on-screen fence cannot pass on a clipped receipt; the row's chip is read from the facts.
                receipt = f"{self._open_sel('Folder Payments')} [data-testid=send-sent]"
                saved = shots.shoot(page, "05-saved-folder", [receipt], seat=f"CENTER:{receipt}")
                assert any("SAVED" in c for c in saved["last_chips"]), saved["last_chips"]
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
                    r = agent.post("/api/channels/sends", json={"document_ref": f"project_update:{uid}", "destination_id": ids[name]})
                    assert r.status_code == 200, r.text
                    prepared[name] = r.json()["send"]["id"]
                prepared["Folder Ledger"] = _api(page, "POST", "/api/channels/sends",
                                                 {"document_ref": f"project_update:{uid}", "destination_id": ids["Folder Ledger"]},
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
                # Seated at the centre: Retry is above the lost line, and the default
                # seat (120 px above the first named element) leaves it under the
                # Room's pinned head at 393.
                lost_line = f"{self._open_sel('Folder Payments')} [data-testid=send-lost]"
                lost = shots.shoot(page, "21-lost-answer-a", [lost_line,
                                                              f"{self._open_sel('Folder Payments')} [data-testid=send-retry]"],
                                   seat=f"CENTER:{lost_line}")
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
                    if value == "email":  # PHILO-15 04: Resend is the default; this board is SendGrid's
                        page.locator("[data-testid=dest-form]").get_by_label("Provider").select_option("sendgrid")
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
                hub = [d for d in _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                       if not d.get("builtin")]  # the parked built-in (park_builtin_folder) is not this board's
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
                hub = [d for d in _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                       if not d.get("builtin")]  # the parked built-in (park_builtin_folder) is not this board's
                assert sorted((d["name"], d["state"]) for d in hub) == [
                    ("Folder Drive", "active"), ("Folder Reports", "parked"), ("Reports folder", "active")], hub
                mine = [r for r in edited["dest_parked"] if not r.startswith("HoldSpeak folder")]  # park_builtin_folder
                assert mine[0].startswith("Folder Reports FILE"), edited["dest_parked"]

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
                hub_nr = [d for d in _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                       if not d.get("builtin")]  # the parked built-in (park_builtin_folder) is not this board's
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
                hub = [d for d in _api(page, "GET", "/api/channels/destinations?include_parked=true", token=TOKEN)["destinations"]
                       if not d.get("builtin")]  # the parked built-in (park_builtin_folder) is not this board's
                assert sorted(d["state"] for d in hub) == ["active", "parked", "parked"], hub
                mine = [r for r in removed["dest_parked"] if not r.startswith("HoldSpeak folder")]  # park_builtin_folder
                assert len(mine) == 2 and removed["dest_head"] == "DESTINATIONS 1"

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


# ── The GitHub, Jira and Confluence boards (story 02's channels) ─────────
#
# The hub, its routes, its kernel and each channel's REAL plan run as they
# ship; only the process edge is canned (story 02's seam,
# `channel_cli.CLI_RUNNER`, with its test rig `tests/unit/_philo10_cli.py`).
# No real gh or acli runs; no account is touched. The Connections reads get
# a canned gh / acli runner the same way (`_boot(gh_runner=, acli_runner=)`).

import subprocess  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))  # story 02 and 01 rigs
from _philo10_cli import EMAIL as ACLI_EMAIL, SITE as ACLI_SITE, Canned  # noqa: E402

GH_LOGIN = "octo-owner"


class _ProviderRunner:
    """The Connections reads' process edge: gh signed in as GH_LOGIN, acli on SITE/EMAIL."""

    def __call__(self, argv: Any, **_: Any) -> subprocess.CompletedProcess[str]:
        argv = [str(a) for a in argv]
        if argv[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(argv, 0, f"Logged in to github.com account {GH_LOGIN} (keyring)\n", "")
        if argv[:3] == ["gh", "api", "user"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"login": GH_LOGIN, "id": 7}), "")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "switch"]:
            return subprocess.CompletedProcess(argv, 0, "switched\n", "")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "status"]:
            return subprocess.CompletedProcess(
                argv, 0, f"✓ Authenticated\n  Site: {ACLI_SITE}\n  Email: {ACLI_EMAIL}\n", "")
        return subprocess.CompletedProcess(argv, 1, "", "unexpected")


def _connect_atlassian(page: Any) -> None:
    """One Jira and one Confluence account on SITE/EMAIL, through the REAL connection-check producer
    (`POST /api/connections/{provider}/recheck`, its acli reads answered at the process edge). Codex Astra r2
    on #697: the earlier direct INSERT used an id production never reads (a lying fixture) -- removed."""
    ref = f"{ACLI_SITE}|{ACLI_EMAIL}"
    for provider in ("jira", "confluence"):
        answer = _api(page, "POST", f"/api/connections/{provider}/recheck", {"ref": ref}, token=TOKEN)
        states = json.dumps(answer)
        assert '"connected"' in states, answer


class TestSendChannelsGlass(_Rig):
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from holdspeak.services import channel_cli

        _ensure_build()
        self.tmp = tmp_path
        self.monkeypatch = monkeypatch
        self.locked: list[Path] = []
        self.canned = Canned(login=GH_LOGIN)
        self.gate: threading.Event | None = None
        self.canned.on_create = self._hold
        monkeypatch.setattr(channel_cli, "CLI_RUNNER", self.canned)
        runner = _ProviderRunner()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=runner, acli_runner=runner)
        park_builtin_folder()  # the desk these boards were drawn on (glass_infra.park_builtin_folder)
        self.server, self.base = server, base
        try:
            yield
        finally:
            if self.gate is not None:
                self.gate.set()
            server.stop()

    def _hold(self, _argv: list[str]) -> None:
        """A create held at the process edge (after the boundary) until released."""
        if self.gate is not None:
            assert self.gate.wait(60), "the held create was never released"

    def _remote(self, page: Any, name: str, channel: str, **fields: Any) -> str:
        body = {"name": name, "channel": channel, **fields}
        status, answer = _api_allow_error(page, "POST", "/api/channels/destinations", body, token=TOKEN)
        assert status == 200, answer
        return answer["destination"]["id"]

    def _wait_receipt(self, page: Any, name: str, state: str) -> None:
        page.locator(f"{self._open_sel(name)} [data-receipt=latest][data-state={state}]").wait_for(timeout=T)
        page.wait_for_timeout(500)

    def _press(self, page: Any, name: str, *, double: bool = False) -> None:
        verb = page.locator(f"{self._open_sel(name)} [data-testid=send-verb]")
        page.wait_for_function("(sel) => { const b = document.querySelector(sel); return b && !b.disabled; }",
                               arg=f"{self._open_sel(name)} [data-testid=send-verb]", timeout=T)
        verb.dblclick() if double else verb.click()

    # ── GitHub: picked, SENDING (held), POSTED, account changed; a prepared send running ──

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_github_sending_posted_and_a_running_prepared_send(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        gh = "acme/Payments #42"
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                dest = self._remote(page, gh, "github", repo="acme/Payments", kind="issue", number=42)
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)

                # Board 7: the preview's fields and the host.
                self._pick(page, gh)
                picked = shots.shoot(page, "07-picked-github", [self._row(gh),
                                     f"{self._open_sel(gh)} [data-testid=send-verb]"])
                assert picked["preview_fields"] == ["REPOSITORY acme/Payments", "ISSUE #42",
                                                    f"ACCOUNT {GH_LOGIN} · github.com"], picked["preview_fields"]
                assert "GITHUB.COM:cloud" in picked["egress_chips"], picked["egress_chips"]

                # Board 8: SENDING -- the create held after the boundary; a double click.
                self.gate = threading.Event()
                self._press(page, gh, double=True)
                self._wait_receipt(page, gh, "dispatching")
                sending = shots.shoot(page, "08-sending", [self._row(gh), f"{self._open_sel(gh)} [data-testid=send-verb]"])
                assert sending["send_verbs"][0]["disabled"] and sending["send_verbs"][0]["busy"], sending["send_verbs"]
                assert any("SENDING" in c for c in sending["last_chips"]), sending["last_chips"]

                # Board 9: released: POSTED + the comment; ONE create for the double click.
                self.gate.set()
                self.gate = None
                self._wait_receipt(page, gh, "sent")
                posted = shots.shoot(page, "09-posted-github", [f"{self._open_sel(gh)} [data-testid=send-sent]"], seat="CENTER:" + f"{self._open_sel(gh)} [data-testid=send-sent]")
                hub = self._sends(page, uid)
                assert len(self.canned.creates()) == 1 and [s["state"] for s in hub] == ["sent"], hub
                href = page.locator(f"{self._open_sel(gh)} [data-testid=send-sent] [data-testid=proof]").get_attribute("data-href")
                assert href == hub[0]["proof"]["url"] and href.startswith("https://github.com/acme/Payments/issues/42#"), href
                assert posted["receipts"][0]["text"] == f"✓ POSTED {gh}", posted["receipts"]

                # Board 20: gh now signed in as someone else: REFUSED, nothing ran.
                self.canned.login = "someone-else"
                self._press(page, gh)
                page.locator(f"{self._open_sel(gh)} [data-testid=send-refused]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                refused = shots.shoot(page, "20-refused-github-account", [f"{self._open_sel(gh)} [data-testid=send-refused]"], seat="CENTER:" + f"{self._open_sel(gh)} [data-testid=send-refused]")
                assert refused["receipts"][0]["code"] == "github_identity_changed", refused["receipts"]
                assert refused["receipts"][0]["text"] == "✗ REFUSED GITHUB ACCOUNT CHANGED NOTHING SENT", refused["receipts"]
                assert len(self.canned.creates()) == 1
                self.canned.login = GH_LOGIN
                self._unpick(page, gh)

                # Boards 26b, 26c, 27: a prepared send running survives Back and return.
                sid = _api(page, "POST", "/api/channels/sends", {"document_ref": f"project_update:{uid}", "destination_id": dest},
                           token=TOKEN)["send"]["id"]
                self._focus(page)
                self._back(page)
                self._open_update(page, uid)
                row = "li.surface-ledger-row:has(> [data-testid=prepared-row])"
                page.locator(f"{row} [data-testid=prepared-send]").wait_for(timeout=T)
                self.gate = threading.Event()
                page.locator(f"{row} [data-testid=prepared-send]").click()
                page.locator("[data-testid=prepared-sending]").wait_for(timeout=T)
                self._back(page)
                self._open_update(page, uid)
                page.locator("[data-testid=prepared-sending]").wait_for(timeout=T)
                stored = {s["id"]: s for s in self._sends(page, uid)}[sid]["state"]
                running = shots.shoot(page, "26b-prepared-running-after-return", ["[data-testid=prepared-sending]"])
                assert stored == "dispatching", stored
                self._pick(page, gh)
                dest_running = shots.shoot(page, "26c-destination-running",
                                           [f"{self._row(gh)} [data-testid=send-last-running]",
                                            f"{self._open_sel(gh)} [data-testid=send-verb]"])
                assert dest_running["send_verbs"][0]["disabled"], dest_running["send_verbs"]
                self.gate.set()
                self.gate = None
                page.wait_for_function("""() => [...document.querySelectorAll('[data-testid=prepared-result] [data-state]')]
                    .some((e) => e.dataset.state === 'sent')""", timeout=T)
                page.wait_for_timeout(900)
                self._unpick(page, gh)
                done = shots.shoot(page, "27-prepared-sent", ["[data-testid=prepared-result]"])
                assert done["prepared_results"][0].startswith(f"· {gh} ✓ POSTED {gh}"), done["prepared_results"]
                assert len(self.canned.creates()) == 2
                shots.write("send-face-github", {"hub_sends": self._sends(page, uid), "running_stored": stored})
                shots.assert_clean()
                assert not errors, errors
            finally:
                if self.gate is not None:
                    self.gate.set()
                browser.close()

    # ── Jira and Confluence: picked, UNKNOWN, COMMENTED, not signed in, BLOG POSTED ──

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_jira_and_confluence(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        jira, conf = "Jira PAY-121", "Confluence space 98304"
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _connect_atlassian(page)
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                self._remote(page, jira, "jira", site=ACLI_SITE, email=ACLI_EMAIL, key="PAY-121")
                self._remote(page, conf, "confluence", site=ACLI_SITE, email=ACLI_EMAIL, space_id="98304")
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)

                self._pick(page, jira)
                picked = shots.shoot(page, "10-picked-jira", [self._row(jira), f"{self._open_sel(jira)} [data-testid=send-verb]"])
                assert picked["preview_fields"] == ["WORK ITEM PAY-121", f"ACCOUNT {ACLI_EMAIL} · {ACLI_SITE}"], picked["preview_fields"]

                # Board 11: no answer from the create: UNKNOWN; Check opens the work item; never re-sent.
                create = ("acli", "jira", "workitem", "comment", "create")

                def _timeout(argv: list[str]) -> Any:
                    raise subprocess.TimeoutExpired(argv, 60)

                self.canned.answers[create] = _timeout
                self._press(page, jira)
                self._wait_receipt(page, jira, "unknown")
                unknown = shots.shoot(page, "11-unknown-jira", [f"{self._open_sel(jira)} [data-testid=send-unknown]",
                                                                f"{self._open_sel(jira)} [data-testid=send-check]"],
                                      seat=f"CENTER:{self._open_sel(jira)} [data-testid=send-unknown]")
                assert unknown["receipts"][0]["text"] == "⚠ RESULT UNKNOWN TIMED OUT", unknown["receipts"]
                assert page.locator(f"{self._open_sel(jira)} [data-testid=send-check]").inner_text().strip() == "Check PAY-121"
                creates_after_unknown = len(self.canned.creates())
                page.wait_for_timeout(1500)
                assert len(self.canned.creates()) == creates_after_unknown  # no automatic re-send

                # Board 12: Send again (a new send, a new key): COMMENTED + the work item.
                del self.canned.answers[create]
                assert page.locator(f"{self._open_sel(jira)} [data-testid=send-verb]").inner_text().strip() == "Send again"
                self._press(page, jira)
                self._wait_receipt(page, jira, "sent")
                commented = shots.shoot(page, "12-commented-jira", [f"{self._open_sel(jira)} [data-testid=send-sent]"], seat="CENTER:" + f"{self._open_sel(jira)} [data-testid=send-sent]")
                assert commented["receipts"][0]["text"] == "✓ COMMENTED PAY-121", commented["receipts"]
                href = page.locator(f"{self._open_sel(jira)} [data-testid=send-sent] [data-testid=proof]").get_attribute("data-href")
                assert href == f"https://{ACLI_SITE}/browse/PAY-121", href
                self._unpick(page, jira)

                # Boards 13-15: Confluence picked; the account signed out; signed in again.
                self._pick(page, conf)
                cpick = shots.shoot(page, "13-picked-confluence", [self._row(conf), f"{self._open_sel(conf)} [data-testid=send-verb]"])
                assert cpick["preview_fields"][0] == "SPACE 98304" and cpick["preview_fields"][1].startswith("TITLE "), cpick["preview_fields"]
                assert cpick["preview_fields"][2] == f"ACCOUNT {ACLI_EMAIL} · {ACLI_SITE}", cpick["preview_fields"]
                # Board 14 (as ratified): the account is signed out -- known BEFORE the boundary,
                # so REFUSED by name, nothing sent, no dispatch (Muad'Dib's ruling on #697).
                switch = ("acli", "confluence", "auth", "switch")
                self.canned.answers[switch] = lambda argv: (1, "", "✗ Error: unauthorized: use 'acli jira auth login' to authenticate")
                creates_before, sends_before = len(self.canned.creates()), len(self._sends(page, uid))
                self._press(page, conf)
                page.locator(f"{self._open_sel(conf)} [data-testid=send-refused]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                signed_out = shots.shoot(page, "14-refused-confluence-sign-in", [f"{self._open_sel(conf)} [data-testid=send-refused]"],
                                         seat=f"CENTER:{self._open_sel(conf)} [data-testid=send-refused]")
                assert signed_out["receipts"][0] == {"text": "✗ REFUSED NOT SIGNED IN NOTHING SENT", "state": "send-refused",
                                                     "code": "atlassian_not_signed_in"}, signed_out["receipts"]
                assert len(self.canned.creates()) == creates_before and len(self._sends(page, uid)) == sends_before
                del self.canned.answers[switch]
                self._focus(page)
                self._press(page, conf)
                self._wait_receipt(page, conf, "sent")
                blog = shots.shoot(page, "15-blog-posted-confluence", [f"{self._open_sel(conf)} [data-testid=send-sent]"], seat="CENTER:" + f"{self._open_sel(conf)} [data-testid=send-sent]")
                href = page.locator(f"{self._open_sel(conf)} [data-testid=send-sent] [data-testid=proof]").get_attribute("data-href")
                assert href == f"https://{ACLI_SITE}/wiki/spaces/OPS/blog/5550001", href
                assert blog["receipts"][0]["text"] == "✓ BLOG POSTED SPACE 98304", blog["receipts"]
                self._unpick(page, conf)

                dl = self._deliveries(page, pid, uid)
                page.locator("[data-testid=delivery-row]").first.wait_for(timeout=T)
                hist = shots.shoot(page, "34c-history-remote", ["[data-testid=delivery-history] > li:first-child > [data-testid=delivery-row]"])
                assert [(d["channel"], d["outcome"]) for d in dl] == [("jira", "unknown"), ("jira", "sent"), ("confluence", "sent")], dl
                assert hist["history_head"] == "DELIVERY 2", hist["history_head"]
                assert [h.split(" ")[0] for h in hist["history"]] == ["⚠", "✓", "✓"], hist["history"]
                assert "COMMENTED" in hist["history"][1] and "BLOG POSTED" in hist["history"][2], hist["history"]
                shots.write("send-face-atlassian", {"hub_deliveries": dl, "hub_sends": self._sends(page, uid)})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── A lock held by another process: REFUSED on the FIRST answer (Codex Astra r2 on #697) ──

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_held_acli_lock_is_refused_on_the_first_answer(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.services import jira_provider

        self.monkeypatch.setattr(jira_provider._ACLI_LOCK, "_timeout", 0.2)
        shots = Boards(SHOTS, width, UP)
        jira = "Jira PAY-121"
        holder = None
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _connect_atlassian(page)
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                self._remote(page, jira, "jira", site=ACLI_SITE, email=ACLI_EMAIL, key="PAY-121")
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)
                self._pick(page, jira)
                # A REAL competing lock: another process holds the acli lock file.
                lock = jira_provider._acli_lockfile_path()
                lock.parent.mkdir(parents=True, exist_ok=True)
                code = ('import fcntl,sys; f=open(sys.argv[1],"a"); fcntl.flock(f,fcntl.LOCK_EX); '
                        'print("locked",flush=True); sys.stdin.read()')
                holder = subprocess.Popen([sys.executable, "-c", code, str(lock)], stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE, text=True)
                assert holder.stdout.readline().strip() == "locked"
                creates = len(self.canned.creates())
                with page.expect_response(lambda r: r.url.endswith("/api/channels/send") and r.request.method == "POST") as resp:
                    self._press(page, jira)
                first = resp.value
                body = first.json()
                page.locator(f"{self._open_sel(jira)} [data-testid=send-refused]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                f = shots.shoot(page, "r2-lock-timeout-refused", [f"{self._open_sel(jira)} [data-testid=send-refused]"],
                                seat=f"CENTER:{self._open_sel(jira)} [data-testid=send-refused]")
                assert first.status == 409 and body["code"] == "lock_timeout", (first.status, body)
                assert body["receipt"]["state"] == "refused" and body["receipt"]["outcome"] == "lock_timeout", body
                assert f["receipts"][0] == {"text": "✗ REFUSED LOCK TIMEOUT NOTHING SENT", "state": "send-refused",
                                            "code": "lock_timeout"}, f["receipts"]
                assert page.locator("[data-testid=send-lost]").count() == 0
                assert len(self.canned.creates()) == creates and self._sends(page, uid) == []
                shots.write("send-face-lock-timeout", {"first": {"status": first.status, **body}})
                shots.assert_clean()
                assert not errors, errors
            finally:
                if holder is not None:
                    holder.stdin.close()
                    holder.wait(timeout=5)
                browser.close()

    # ── The forms save through story 02's wire (B4-B6) ────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_remote_destination_forms_save(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, DS)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _connect_atlassian(page)
                self._stage(page, "configure-settings", "integrations")
                page.locator("[data-testid=dest-form]").wait_for(timeout=T)
                page.wait_for_timeout(900)
                select = page.locator("[data-testid=dest-form] select").first

                # B4: GitHub: the concrete login is read at save.
                select.select_option("github")
                page.locator("[data-testid=dest-repo]").fill("acme/Payments")
                page.locator("[data-testid=dest-number]").fill("42")
                page.locator("[data-testid=dest-save]").click()
                page.locator("[data-testid=dest-row]").first.wait_for(timeout=T)

                # B5: Jira: ONE key only, refused by name; then one key saves.
                page.locator("[data-testid=dest-add]").click()
                select = page.locator("[data-testid=dest-form] select").first
                select.select_option("jira")
                page.wait_for_timeout(200)
                page.locator("[data-testid=dest-key]").fill("PAY-118 PAY-119")
                page.locator("[data-testid=dest-save]").click()
                page.locator("[data-testid=dest-refused]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                one_key = shots.shoot(page, "b05-jira-one-key", ["[data-testid=dest-refused]"], seat="CENTER:[data-testid=dest-refused]")
                code = page.locator("[data-testid=dest-refused]").get_attribute("data-code")
                assert code in {"jira_key_not_single", "jira_key_invalid"}, code
                assert "REFUSED" in page.locator("[data-testid=dest-refused]").inner_text()
                page.locator("[data-testid=dest-key]").fill("PAY-118")
                page.locator("[data-testid=dest-save]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=dest-row]').length === 2", timeout=T)

                # B6: Confluence space.
                page.locator("[data-testid=dest-add]").click()
                page.locator("[data-testid=dest-form] select").first.select_option("confluence")
                page.wait_for_timeout(200)
                page.locator("[data-testid=dest-space]").fill("98304")
                page.locator("[data-testid=dest-save]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=dest-row]').length === 3", timeout=T)
                page.wait_for_timeout(400)
                hub = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
                listed = shots.shoot(page, "b09b-list-remote", ["[data-testid=dest-row]"])
                assert sorted((d["channel"], d["name"]) for d in hub) == [
                    ("confluence", "Confluence space 98304"), ("github", "acme/Payments #42"), ("jira", "Jira PAY-118")], hub
                gh_row = next(d for d in hub if d["channel"] == "github")
                assert gh_row["account"] == {"host": "github.com", "login": GH_LOGIN}, gh_row
                jira_row = next(d for d in hub if d["channel"] == "jira")
                assert jira_row["account"] == {"site": ACLI_SITE, "email": ACLI_EMAIL}, jira_row
                assert listed["dest_head"] == "DESTINATIONS 3"
                assert {"GITHUB.COM:cloud", f"{ACLI_SITE.upper()}:cloud"} <= set(listed["egress_chips"]), listed["egress_chips"]

                # B10: the Jira row checked: the account's state, as the hub keeps it.
                row = self._drow("Jira PAY-118")
                page.locator(f"{row} > .surface-ledger-line").click()
                page.locator(f"{row} [data-testid=dest-check]").click()
                page.locator(f"{row} [data-testid=dest-check-result]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                shots.shoot(page, "b10b-jira-checked", [f"{row} [data-testid=dest-check-result]"])
                answered = page.locator(f"{row} [data-testid=dest-check-result]").get_attribute("data-code")
                check = _api(page, "POST", f"/api/channels/destinations/{jira_row['id']}/check", {}, token=TOKEN)["check"]
                assert answered == check["state"] == "connected", (answered, check)
                assert page.locator(f"{row} [data-testid=dest-check-result]").inner_text().split() == ["✓", "CHECKED"]
                assert jira_row["connection"]["state"] == "connected", jira_row
                shots.write("destinations-remote", {"hub": hub, "check": check, "one_key": one_key["receipts"]})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()


# ── Board 25: UNKNOWN after a restart -- a REAL hub process killed mid-send ──
#
# Story 01's restart rig (tests/unit/test_philo10_send_restart.py HubProcess):
# the hub is a PROCESS on an isolated HOME; its file dispatch writes the file
# and then holds; the owner's press comes from the Room's own Send; the hub is
# killed with SIGKILL; a second hub on the same HOME runs the startup recovery.

@pytest.mark.e2e
@pytest.mark.timeout(600)
@pytest.mark.parametrize("width", WIDTHS)
def test_board_25_unknown_after_a_real_restart(tmp_path: Path, width: int) -> None:
    from playwright.sync_api import sync_playwright
    from test_philo10_send_restart import TOKEN as HUB_TOKEN, HubProcess, _rows, _until

    _ensure_build()
    home, folder = tmp_path / "home", tmp_path / "Payments"
    home.mkdir()
    folder.mkdir()
    shots = Boards(SHOTS, width, UP)
    first = HubProcess(home, hold="after")
    second = None
    try:
        call = first.call
        assert call("PUT", "/api/setup/onboarding", {"disposition": "completed"})[0] == 200
        pid = call("POST", "/api/projects", {"name": NAME})[1]["project"]["id"]
        uid = call("POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})[1]["update"]["id"]
        # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
        assert call("PUT", f"/api/updates/{uid}", {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"})[0] == 200
        assert call("POST", f"/api/updates/{uid}/publish", {})[0] == 200
        assert call("POST", "/api/channels/destinations",
                    {"name": "Folder Payments", "channel": "file", "folder": str(folder)})[0] == 200
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            rig = _Rig()

            def room(url: str) -> None:
                page.goto(f"{url}/?token={HUB_TOKEN}", wait_until="load")
                rig._room(page, pid)
                rig._updates(page)
                rig._open_update(page, uid)

            try:
                room(first.url)
                rig._pick(page, "Folder Payments")
                page.locator(f"{rig._open_sel('Folder Payments')} [data-testid=send-verb]").click()
                row = _until(lambda: next(iter(_rows(home, "SELECT * FROM channel_sends WHERE state='dispatching'")), None))
                _until(lambda: list(folder.iterdir()))  # the file is written; the dispatch holds
                first.kill()
                second = HubProcess(home)
                room(second.url)
                [settled] = _rows(home, "SELECT * FROM channel_sends WHERE id=?", row["id"])
                page.locator("[data-testid=delivery-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(600)
                f = shots.shoot(page, "25-unknown-after-restart",
                                [rig._row("Folder Payments") + " [data-testid=send-last-unknown]",
                                 "[data-testid=delivery-history] > li:first-child > [data-testid=delivery-row]"])
                assert (settled["state"], settled["reason"]) == ("unknown", "interrupted"), settled
                assert f["history"] == [f["history"][0]] and f["history"][0].startswith(
                    "⚠ RESULT UNKNOWN · CHECK Folder Payments INTERRUPTED"), f["history"]
                assert f["history_outcomes"] == ["unknown"] and f["history_head"] == "DELIVERY"
                assert any("LAST SEND UNKNOWN" in c for c in f["last_chips"]), f["last_chips"]
                assert len(list(folder.iterdir())) == 1  # never sent again
                shots.write("send-face-restart", {"settled": {k: settled[k] for k in ("state", "reason", "proof_json")}})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()
    finally:
        if second is not None:
            second.kill()
        if first.proc.poll() is None:
            first.kill()


# ── The email boards (story 03's channel) ────────────────────────────────
#
# Story 03's own seams: the HTTPS edge is its canned handler
# (`channel_email.HTTPS_HANDLER`, the rig `Wire` of tests/unit/
# test_philo10_email_channel.py) under the REAL opener, admission and
# allow-list; the key store is the injected in-memory store, and a guard
# fails the test if anything reaches the real keychain.

from test_philo10_email_channel import SENDER_403, Wire, errors as sg_errors, response as sg_response  # noqa: E402

KEY = "SG.glassKEY04e1f0000abcd.neverOnTheFace0000"
FROM, TO, CC = "karol@acme.io", ["lena@acme.io", "tomas@acme.io"], ["priya@acme.io"]


class _August(datetime):
    """The boundary clock pinned to an old day: a send answered long ago."""

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return datetime(2026, 8, 1, 9, 0, 0, tzinfo=tz)


class TestSendEmailGlass(_Rig):
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import keyring

        from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS
        from holdspeak.services import channel_email

        _ensure_build()
        self.tmp = tmp_path
        self.monkeypatch = monkeypatch
        self.locked: list[Path] = []
        self.memory = channel_email.MemoryEmailKeyStore()
        self.store: Any = self.memory
        monkeypatch.setattr(channel_email, "KEY_STORE", lambda: self.store)

        def never(*_a: Any, **_k: Any) -> Any:
            raise AssertionError("the glass reached the real keychain")

        monkeypatch.setattr(keyring, "get_keyring", never)
        self.wire = Wire()
        monkeypatch.setattr(channel_email, "HTTPS_HANDLER", self.wire.handler)
        EGRESS_EXECUTIONS._results.clear()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        park_builtin_folder()  # the desk these boards were drawn on (glass_infra.park_builtin_folder)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    @staticmethod
    def _key_ref() -> str:
        return f"sendgrid-{FROM}"

    def _email_dest(self, page: Any, name: str = "Email lena@acme.io") -> str:
        status, saved = _api_allow_error(page, "PUT", f"/api/channels/email-keys/{self._key_ref()}",
                                         {"api_key": KEY, "provider": "sendgrid"}, token=TOKEN)
        assert status == 200, saved
        # PHILO-15 04: Resend is the default now; these boards name SendGrid.
        status, dest = _api_allow_error(page, "POST", "/api/channels/destinations", {
            "name": name, "channel": "email", "provider": "sendgrid", "from_email": FROM, "from_name": "Karol", "key_ref": self._key_ref(),
            "to": TO, "cc": CC}, token=TOKEN)
        assert status == 200, dest
        return dest["destination"]["id"]

    def _wait_receipt(self, page: Any, name: str, state: str) -> None:
        page.locator(f"{self._open_sel(name)} [data-receipt=latest][data-state={state}]").wait_for(timeout=T)
        page.wait_for_timeout(500)

    # ── 16-19: picked, FAILED sender not verified, ACCEPTED BY SENDGRID, the history ──

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_email_boards(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        shots = Boards(SHOTS, width, UP)
        em = "Email lena@acme.io"
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                self._email_dest(page)
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)

                # Board 16: the preview parsed back from the frozen SendGrid request.
                self._pick(page, em)
                picked = shots.shoot(page, "16-picked-email", [self._row(em), f"{self._open_sel(em)} [data-testid=send-verb]"])
                fields = picked["preview_fields"]
                assert fields[:3] == ["FROM Karol <karol@acme.io>", "TO lena@acme.io, tomas@acme.io", "CC priya@acme.io"], fields
                assert fields[3].startswith("SUBJECT " + NAME), fields
                assert "API.SENDGRID.COM:cloud" in picked["egress_chips"], picked["egress_chips"]

                # Board 17: SendGrid's pinned 403 for an unverified sender: FAILED, nothing sent.
                self.wire.script = [sg_errors(403, SENDER_403, field="from")]
                page.locator(f"{self._open_sel(em)} [data-testid=send-verb]").click()
                self._wait_receipt(page, em, "failed")
                failed = shots.shoot(page, "17-failed-email-sender", [f"{self._open_sel(em)} [data-testid=send-failed]"],
                                     seat=f"CENTER:{self._open_sel(em)} [data-testid=send-failed]")
                assert failed["receipts"][0] == {"text": "✗ FAILED SENDER NOT VERIFIED NOTHING SENT", "state": "failed",
                                                 "code": "sender_not_verified"}, failed["receipts"]
                assert any("LAST SEND FAILED" in c for c in failed["last_chips"]), failed["last_chips"]

                # Board 18: he verifies the sender in SendGrid; Send again: ACCEPTED BY SENDGRID + the id, exact case.
                self.wire.default = sg_response(202, {"X-Message-Id": "sg-Msg-04AbCd"})
                page.locator(f"{self._open_sel(em)} [data-testid=send-verb]").click()
                self._wait_receipt(page, em, "sent")
                accepted = shots.shoot(page, "18-accepted-by-sendgrid", [f"{self._open_sel(em)} [data-testid=send-sent]"],
                                       seat=f"CENTER:{self._open_sel(em)} [data-testid=send-sent]")
                assert accepted["receipts"][0]["text"] == "✓ ACCEPTED BY SENDGRID ID sg-Msg-04AbCd", accepted["receipts"]
                assert len(self.wire.requests) == 2 and all(r["host"] == "api.sendgrid.com" for r in self.wire.requests)
                self._unpick(page, em)

                # Board 19: the history row; never DELIVERED on an email row.
                dl = self._deliveries(page, pid, uid)
                page.locator("[data-testid=delivery-row]").first.wait_for(timeout=T)
                hist = shots.shoot(page, "19-accepted-history", ["[data-testid=delivery-history] > li:first-child > [data-testid=delivery-row]"])
                assert [(d["channel"], d["outcome"]) for d in dl] == [("email", "sent")], dl
                assert hist["history_head"] == "DELIVERY 1" and len(hist["history"]) == 1, hist
                assert hist["history"][0].startswith(f"✓ {em} ACCEPTED BY SENDGRID ID sg-Msg-04AbCd"), hist["history"]
                assert "DELIVERED" not in hist["history"][0]
                assert KEY not in page.content() and "glassKEY" not in page.content()
                shots.write("send-face-email", {"hub_deliveries": dl, "hub_sends": self._sends(page, uid),
                                                "wire_hosts": [r["host"] for r in self.wire.requests]})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()

    # ── B7, B8, B11: the email form, the key, the sender check ──────────

    @pytest.mark.e2e
    @pytest.mark.timeout(1200)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_email_destination_setup(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.services import channel_email

        import keyring.backends.fail

        def _no_native_store() -> Any:
            # The REAL classifier on a real non-native backend (keyring's `fail` backend): it raises
            # email_key_store_not_native itself.
            return channel_email.NativeEmailKeyStore(backend=keyring.backends.fail.Keyring())

        shots = Boards(SHOTS, width, DS)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = self._published(page, pid)
                self._stage(page, "configure-settings", "integrations")
                page.locator("[data-testid=dest-form]").wait_for(timeout=T)
                page.wait_for_timeout(900)
                page.locator("[data-testid=dest-form] select").first.select_option("email")
                # PHILO-15 04: Resend is the default; these boards are SendGrid's.
                page.locator("[data-testid=dest-form]").get_by_label("Provider").select_option("sendgrid")
                page.locator("[data-testid=dest-from]").fill(FROM)
                page.locator("[data-testid=dest-to]").fill(", ".join(TO))
                key_row = "[data-testid=dest-key-row]"

                def type_key() -> None:
                    page.locator(f"{key_row} .btn", has_text="Replace").click()
                    field = page.locator(f"{key_row} input[type=password]")
                    field.fill(KEY)
                    field.press("Enter")

                # B7: no safe key store: KEY NOT SAVED + why; nothing kept.
                self.monkeypatch.setattr(channel_email, "KEY_STORE", _no_native_store)
                type_key()
                page.locator("[data-testid=dest-key-refused]").wait_for(timeout=T)
                page.wait_for_timeout(300)
                refused = shots.shoot(page, "b07-key-not-saved", ["[data-testid=dest-key-refused]"],
                                      seat="CENTER:[data-testid=dest-key-refused]")
                assert page.locator("[data-testid=dest-key-refused]").get_attribute("data-code") == "email_key_store_not_native"
                assert page.locator("[data-testid=dest-key-refused]").inner_text().split("\n")[1:] == [
                    "KEY NOT SAVED", "NO SAFE KEY STORE"], page.locator("[data-testid=dest-key-refused]").inner_text()
                assert self.memory.values == {}

                # B8: the key saved into the (in-memory) keychain: SET, never the key; then the destination.
                self.monkeypatch.setattr(channel_email, "KEY_STORE", lambda: self.store)
                type_key()
                page.wait_for_function("(sel) => document.querySelector(sel)?.innerText.includes('SET')", arg=key_row, timeout=T)
                page.wait_for_timeout(300)
                keyed = shots.shoot(page, "b08-add-email-key-set", [key_row],
                                    seat=f"CENTER:{key_row}")
                assert self.memory.values == {f"sendgrid:{self._key_ref()}": KEY}  # PHILO-10-07: <provider>:<key_ref>
                assert KEY not in page.content() and "glassKEY" not in page.content()
                page.locator("[data-testid=dest-save]").click()
                page.locator("[data-testid=dest-row]").first.wait_for(timeout=T)
                hub = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
                assert [(d["channel"], d["name"], d["account"]["key_ref"], d["target"]["to"]) for d in hub] == [
                    ("email", "Email lena@acme.io", self._key_ref(), TO)], hub
                assert "API.SENDGRID.COM:cloud" in keyed["egress_chips"], keyed["egress_chips"]

                # B11: Check reports the SENDER, never the key alone. Before any answer: SENDER NOT CHECKED;
                # after SendGrid's pinned 403 for this sender: SENDER NOT VERIFIED.
                row = self._drow("Email lena@acme.io")
                page.locator(f"{row} > .surface-ledger-line").click()
                page.locator(f"{row} [data-testid=dest-check]").click()
                page.locator(f"{row} [data-testid=dest-check-result]").wait_for(timeout=T)
                assert page.locator(f"{row} [data-testid=dest-check-result]").get_attribute("data-code") == "ready"
                assert "SENDER NOT CHECKED" in page.locator(f"{row} [data-testid=dest-check-result]").inner_text()
                dest = hub[0]["id"]
                result = f"{row} [data-testid=dest-check-result]"

                def api_send(script: Any = None) -> dict[str, Any]:
                    digest = _api(page, "POST", "/api/channels/preview", {"document_ref": f"project_update:{uid}", "destination_id": dest},
                                  token=TOKEN)["payload_digest"]
                    if script is not None:
                        self.wire.script = [script]
                    return _api(page, "POST", "/api/channels/send", {"document_ref": f"project_update:{uid}", "destination_id": dest,
                                                                     "preview_digest": digest}, token=TOKEN)

                def check(code: str) -> str:
                    page.locator(f"{row} [data-testid=dest-check]").click()
                    page.wait_for_function("([sel, code]) => document.querySelector(sel)?.dataset.code === code",
                                           arg=[result, code], timeout=T)
                    page.wait_for_timeout(300)
                    return page.locator(result).inner_text().replace("\n", " ")

                # Codex Astra r2's sequence: an OLD acceptance (the boundary clock pinned to Aug 1), then the
                # key replaced through the real producer: the old answer no longer speaks for the key.
                from holdspeak.services import channel_service as _cs

                self.monkeypatch.setattr(_cs, "datetime", _August)
                self.wire.default = sg_response(202, {"X-Message-Id": "sg-Old-0801"})
                assert api_send()["outcome"] == "sent"
                self.monkeypatch.setattr(_cs, "datetime", datetime)
                assert _api_allow_error(page, "PUT", f"/api/channels/email-keys/{self._key_ref()}",
                                        {"api_key": KEY + "B", "provider": "sendgrid"}, token=TOKEN)[0] == 200
                changed = check("key_changed")
                shots.shoot(page, "b11b-email-check-key-changed", [result], seat=f"CENTER:{result}")
                assert changed == "⚠ NOT CHECKED SINCE KEY CHANGE", changed
                # An acceptance after the key: SENDER ACCEPTED with the date of THAT answer (never "verified").
                self.wire.default = sg_response(202, {"X-Message-Id": "sg-New-0929"})
                accepted_send = api_send()["send"]
                accepted = check("sender_accepted")
                shots.shoot(page, "b11c-email-check-accepted", [result], seat=f"CENTER:{result}")
                answered = _api(page, "POST", f"/api/channels/destinations/{dest}/check", {}, token=TOKEN)["check"]
                assert answered["answered_at"] == accepted_send["dispatch_started_at"], (answered, accepted_send)
                assert accepted.startswith("✓ SENDER ACCEPTED LAST SEND ") and "VERIFIED" not in accepted, accepted
                # SendGrid's pinned 403 for this sender, now: SENDER NOT VERIFIED with today's date.
                answer = api_send(sg_errors(403, SENDER_403, field="from"))
                assert (answer["outcome"], answer["send"]["reason"]) == ("failed", "sender_not_verified"), answer
                not_verified = check("sender_not_verified")
                checked = shots.shoot(page, "b11-email-check-not-verified", [result], seat=f"CENTER:{result}")
                check_answer = _api(page, "POST", f"/api/channels/destinations/{dest}/check", {}, token=TOKEN)["check"]
                assert check_answer["state"] == "sender_not_verified" and check_answer["answered_at"], check_answer
                assert not_verified.startswith("✗ SENDER NOT VERIFIED LAST SEND "), not_verified
                assert "SET" in page.locator(f"{row} [data-testid=dest-open] dl").inner_text()  # the key: present only
                check = check_answer
                shots.write("destinations-email", {"hub": hub, "check": check, "refused": refused["named"],
                                                   "checked": checked["named"]})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()
