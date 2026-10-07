"""The built-in "HoldSpeak folder" in the SEND well, AS RENDERED through the real
hub on an isolated HOME at 1440x900 and 393x852 (owner ruling 2026-10-05,
"strong defaults, batteries included").

Two desks: Documents plain (THIS DEVICE), and Documents synced by iCloud
Drive (the detector's OS-call boundary answers the iCloud xattr for the
isolated HOME's Documents only): the chip and the receipt say ICLOUD.

A fresh desk has no saved destination. The brief on the Chair (a real
``POST /api/brief/generate``) shows ONE destination row, the built-in
HoldSpeak folder, picked: the preview and Send are open with no click; the
egress chip says THIS DEVICE. Send writes the file into the isolated HOME's
Documents/HoldSpeak/Sent (made by this send) and the row shows SAVED. The
shots go to ``$HOLDSPEAK_BUILTIN_SHOTS`` when it is set (the owner's look),
else to the evidence scratch.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the SEND well glass needs Playwright")

TOKEN = "builtin-send-folder"
SIZES = {1440: 900, 393: 852}
T = 20_000
CH = ".chair [data-seat=brief]"
NAME = "HoldSpeak folder"
ROW = f"{CH} [data-testid=destination-row]:has([data-destination='{NAME}'])"
OPEN = f"{CH} [data-testid=send-open][data-destination='{NAME}']"


def _shots() -> Path:
    target = os.environ.get("HOLDSPEAK_BUILTIN_SHOTS")
    path = Path(target) if target else evidence_dir("builtin-send-folder")
    path.mkdir(parents=True, exist_ok=True)
    return path


class TestBuiltinSendFolderGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.tmp = tmp_path
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    def _icloud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from holdspeak.services import channel_contract

        documents = os.path.realpath(self.tmp / "home" / "Documents")
        os.makedirs(documents, exist_ok=True)
        monkeypatch.setattr(channel_contract, "PLATFORM", "darwin")
        monkeypatch.setattr(channel_contract, "_read_xattr", lambda path, name: (
            b"com.apple.CloudDocs.iCloudDriveFileProvider/glass" if path == documents else None))

    def _shoot(self, page: Any, name: str, width: int) -> None:
        box = page.locator(CH).first.bounding_box()
        assert box is not None
        page.screenshot(path=str(_shots() / f"{name}-{width}.png"),
                        clip={"x": max(box["x"] - 8, 0), "y": max(box["y"] - 8, 0),
                              "width": min(box["width"] + 16, width), "height": min(box["height"] + 16, SIZES[width])})

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    @pytest.mark.parametrize("docs", ["plain", "icloud"])
    def test_the_builtin_folder_is_one_picked_row_and_send_writes_into_documents(
            self, width: int, docs: str, monkeypatch: pytest.MonkeyPatch) -> None:
        from playwright.sync_api import sync_playwright

        if docs == "icloud":
            self._icloud(monkeypatch)
        chip = "ICLOUD" if docs == "icloud" else "THIS DEVICE"

        sent = Path(os.path.realpath(self.tmp / "home" / "Documents")) / "HoldSpeak" / "Sent"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                listed = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
                assert [d["id"] for d in listed] == ["holdspeak-folder"], listed
                _api(page, "POST", "/api/decisions", {"title": "Freeze the old ledger on Nov 3", "status": "proposed",
                                                      "decision_markdown": "Freeze the old ledger on Nov 3."}, token=TOKEN)
                brief = _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
                ref = f"monday_brief:{brief['id']}"
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                # PHILO-14 A1 (#939): the Brief window starts closed; open it by the gesture.
                open_chair_window(page, "Brief")
                page.wait_for_timeout(600)
                _settle(page)

                # One row, picked with no click: the preview and Send are open.
                page.locator(ROW).wait_for(timeout=T)
                assert page.locator(f"{CH} [data-testid=destination-row]").count() == 1
                assert page.locator(f"{CH} [data-testid=send-none]").count() == 0
                page.locator(f"{OPEN} [data-testid=send-preview]").wait_for(timeout=T)
                line = " ".join(page.locator(ROW).first.inner_text().split())
                assert NAME in line and "FILE" in line and chip in line, line
                assert ("THIS DEVICE" in line) == (docs == "plain") and ("ICLOUD" in line) == (docs == "icloud"), line
                assert "~/Documents/HoldSpeak/Sent" in line, line
                assert not sent.exists(), "the folder is made by the first send, never before"
                page.locator(ROW).first.scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                self._shoot(page, f"01-{docs}-builtin-row-picked", width)

                verb = f"{OPEN} [data-testid=send-verb]"
                page.wait_for_function("(s) => { const b = document.querySelector(s); return b && !b.disabled; }",
                                       arg=verb, timeout=T)
                page.locator(verb).first.click()
                page.locator(f"{OPEN} [data-receipt=latest][data-state=sent]").first.wait_for(timeout=T)
                page.wait_for_timeout(700)
                [row] = _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]
                assert row["state"] == "sent" and row["destination_id"] == "holdspeak-folder", row
                written = sorted(p for p in sent.iterdir() if p.is_file())
                assert [str(p) for p in written] == [row["proof"]["path"]], (written, row["proof"])
                receipt = " ".join(page.locator(f"{OPEN} [data-receipt=latest]").first.inner_text().split())
                assert "SAVED" in receipt, receipt
                assert ("ICLOUD" in receipt) == (docs == "icloud"), receipt
                assert row["proof"].get("egress") == ("icloud" if docs == "icloud" else None), row["proof"]
                self._shoot(page, f"02-{docs}-builtin-row-saved", width)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_phase11_brief_send_to_a_saved_folder_with_the_builtin_present(self, width: int) -> None:
        """Astra's note on #864: one older flow WITH the built-in present (not parked).

        The Phase 11 brief flow on the Chair: a saved folder beside the
        built-in; nothing is picked by itself (two destinations); he picks the
        saved folder and sends; the file lands there, the built-in folder is
        not made, and the built-in row stays as it was. Then he picks the
        built-in and sends: its own file, its own receipt.
        """
        from playwright.sync_api import sync_playwright

        sent = Path(os.path.realpath(self.tmp / "home" / "Documents")) / "HoldSpeak" / "Sent"
        team_dir = (self.tmp / "Reports" / "Team").resolve()
        team_dir.mkdir(parents=True)
        team_row = f"{CH} [data-testid=destination-row]:has([data-destination='Team folder'])"
        team_open = f"{CH} [data-testid=send-open][data-destination='Team folder']"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Team folder", "channel": "file", "folder": str(team_dir)}, token=TOKEN)
                _api(page, "POST", "/api/decisions", {"title": "Freeze the old ledger on Nov 3", "status": "proposed",
                                                      "decision_markdown": "Freeze the old ledger on Nov 3."}, token=TOKEN)
                brief = _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
                ref = f"monday_brief:{brief['id']}"
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                # PHILO-14 A1 (#939): the Brief window starts closed; open it by the gesture.
                open_chair_window(page, "Brief")
                page.wait_for_timeout(600)
                _settle(page)

                page.locator(team_row).wait_for(timeout=T)
                page.locator(ROW).wait_for(timeout=T)
                assert page.locator(f"{CH} [data-testid=destination-row]").count() == 2
                assert page.locator(f"{CH} [data-testid=send-open]").count() == 0, "two destinations: nothing picked by itself"

                page.locator(team_row).first.click()
                page.locator(f"{team_open} [data-testid=send-preview]").wait_for(timeout=T)
                verb = f"{team_open} [data-testid=send-verb]"
                page.wait_for_function("(s) => { const b = document.querySelector(s); return b && !b.disabled; }",
                                       arg=verb, timeout=T)
                page.locator(verb).first.click()
                page.locator(f"{team_open} [data-receipt=latest][data-state=sent]").first.wait_for(timeout=T)
                [row] = _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]
                assert row["destination_name"] == "Team folder" and row["state"] == "sent", row
                assert len([p for p in team_dir.iterdir() if p.is_file()]) == 1
                assert not sent.exists(), "a send to a saved folder never makes the built-in folder"
                builtin_line = " ".join(page.locator(ROW).first.inner_text().split())
                assert "THIS DEVICE" in builtin_line and "SAVED" not in builtin_line, builtin_line

                page.locator(ROW).first.click()
                page.locator(f"{OPEN} [data-testid=send-preview]").wait_for(timeout=T)
                verb = f"{OPEN} [data-testid=send-verb]"
                page.wait_for_function("(s) => { const b = document.querySelector(s); return b && !b.disabled; }",
                                       arg=verb, timeout=T)
                page.locator(verb).first.click()
                page.locator(f"{OPEN} [data-receipt=latest][data-state=sent]").first.wait_for(timeout=T)
                rows = _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]
                sent_to = {r["destination_name"] for r in rows if r["state"] == "sent"}
                assert sent_to == {"Team folder", NAME} and len(rows) == 2, rows
                assert len([p for p in sent.iterdir() if p.is_file()]) == 1
                assert len([p for p in team_dir.iterdir() if p.is_file()]) == 1
                assert not errors, errors
            finally:
                browser.close()
