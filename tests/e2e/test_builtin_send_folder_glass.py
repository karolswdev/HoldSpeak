"""The built-in "HoldSpeak folder" in the SEND well, AS RENDERED through the real
hub on an isolated HOME at 1440x900 and 393x852 (owner ruling 2026-10-05,
"strong defaults, batteries included").

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

    def _shoot(self, page: Any, name: str, width: int) -> None:
        box = page.locator(CH).first.bounding_box()
        assert box is not None
        page.screenshot(path=str(_shots() / f"{name}-{width}.png"),
                        clip={"x": max(box["x"] - 8, 0), "y": max(box["y"] - 8, 0),
                              "width": min(box["width"] + 16, width), "height": min(box["height"] + 16, SIZES[width])})

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_builtin_folder_is_one_picked_row_and_send_writes_into_documents(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

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
                if width <= 720:
                    open_chair_window(page, "Brief")
                    page.wait_for_timeout(600)
                _settle(page)

                # One row, picked with no click: the preview and Send are open.
                page.locator(ROW).wait_for(timeout=T)
                assert page.locator(f"{CH} [data-testid=destination-row]").count() == 1
                assert page.locator(f"{CH} [data-testid=send-none]").count() == 0
                page.locator(f"{OPEN} [data-testid=send-preview]").wait_for(timeout=T)
                line = " ".join(page.locator(ROW).first.inner_text().split())
                assert NAME in line and "FILE" in line and "THIS DEVICE" in line, line
                assert "~/Documents/HoldSpeak/Sent" in line, line
                assert not sent.exists(), "the folder is made by the first send, never before"
                page.locator(ROW).first.scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                self._shoot(page, "01-builtin-row-picked", width)

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
                assert "SAVED" in " ".join(page.locator(OPEN).first.inner_text().split())
                self._shoot(page, "02-builtin-row-saved", width)
                assert not errors, errors
            finally:
                browser.close()
