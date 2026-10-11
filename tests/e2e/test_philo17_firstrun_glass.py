"""PHILO-17 firstrun (U17, U18) on the real hub, at 1440 and 393.

The owner's walk A (2026-10-10): after ten minutes he did not know what the
product is for. "Start here" was three privacy sentences; Setup's "Continue
arrival" opened a different page with no way back to the Get ready cards;
first run's only exit was "Continue later" even when every card was done.

F1  A fresh desk: Start here shows the three jobs, each a working button:
    Record a meeting -> the Live meeting window; Dictate -> Speak (Capture at
    393); Review what needs you -> the Needs you window.
F2  The HoldSpeak menu ▸ Setup ▸ Get ready opens the SAME first-run cards
    (no "arrival" on the face).
F3  The cards done (local AI here, his name, a first dictation before) ->
    "Open my desk" (primary) -> the desk.

Rig: the C1 glass rig (test_firstrun_heard_glass: the real local-AI service,
its files from a 127.0.0.1 source). The first dictation is the milestone the
hub sets on a first success, set here; the seed is the hub's own POST.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _settle, clear_hub_windows
from .test_firstrun_heard_glass import TOKEN, _ready_hub

pytest.importorskip("playwright.sync_api", reason="first-run glass needs Playwright")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

START_HERE = "note:hs-seed-start-here"
JOBS = ("Record a meeting", "Dictate", "Review what needs you")


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


def _start_here(page: Any, base: str) -> Any:
    _desk(page, base, f"&open={START_HERE}")
    body = page.locator(".surface-material", has=page.get_by_role("button", name=JOBS[0], exact=True))
    body.wait_for(timeout=15_000)
    return body


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_firstrun_start_here_and_reopen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
    server, base, source = _ready_hub(tmp_path, monkeypatch)
    from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database

    db = get_database()
    db.milestones.mark(FIRST_DICTATION_SUCCESS)  # a first dictation happened
    db.onboarding.set_disposition("dismissed")  # first run was left once
    out = Path(os.environ.get("FIRSTRUN_SHOTS") or tmp_path / "shots")
    out.mkdir(parents=True, exist_ok=True)
    fails: dict[str, Any] = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            page.set_default_timeout(10_000)

            def shot(name: str) -> None:
                page.wait_for_timeout(350)
                path = out / f"P17-firstrun-{name}-{width}.png"
                page.screenshot(path=str(path))
                print("SHOT", path)

            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)

            # ── F1: Start here = the loop in three jobs, each a working button ──
            body = _start_here(page, base)
            for job in JOBS:
                expect(body.get_by_role("button", name=job, exact=True)).to_be_visible()
            text = body.inner_text()
            if "never automatically included" in text:
                fails["F1 the privacy sentences left Start here"] = text[:200]
            shot("start-here")
            targets = {
                "Record a meeting": "#surface-live",
                # Only the Dock's Speak opens Capture at 393 (ChairDesk.tsx ruling);
                # every other Dictate opens the Speak window at both widths.
                "Dictate": "#surface-dictation",
                "Review what needs you": ".desk-window-shell.chair-window[aria-label='Needs you']",
            }
            for job, target in targets.items():
                try:
                    body = _start_here(page, base)
                    body.get_by_role("button", name=job, exact=True).click()
                    page.locator(target).first.wait_for(state="visible", timeout=15_000)
                except Exception as exc:  # noqa: BLE001 -- the fence names every job that failed
                    fails[f"F1 {width} {job} opens {target}"] = str(exc)[:200]

            # ── F2: HoldSpeak ▸ Setup ▸ Get ready opens the same cards ──
            _desk(page, base)
            page.locator(".desk-mark").click()
            page.locator(".desk-menu-list").first.wait_for()
            _row(page, "Setup").click()
            setup = page.locator("#surface-setup")
            get_ready = setup.get_by_role("button", name="Get ready", exact=True)
            get_ready.wait_for(timeout=15_000)
            if "arrival" in setup.inner_text().lower():
                fails["F2 no 'arrival' on Setup"] = setup.inner_text()[:200]
            get_ready.click()
            face = page.get_by_test_id("firstrun")
            face.wait_for(timeout=15_000)
            for card in ("firstrun-local-ai", "firstrun-you", "firstrun-first-words", "firstrun-calendar",
                         "firstrun-connections", "firstrun-agents"):
                expect(page.get_by_test_id(card)).to_be_attached()
                if page.get_by_test_id(card).locator(".firstrun-card-line").count() != 1:
                    fails[f"F2 {card} has one plain line"] = page.get_by_test_id(card).inner_text()[:120]
            if "arrival" in face.inner_text().lower():
                fails["F2 no 'arrival' on first run"] = "arrival"
            expect(page.get_by_role("button", name="Continue later", exact=True)).to_be_visible()
            shot("reopened")

            # ── F3: the cards done -> Open my desk (primary) -> the desk ──
            local_ai = page.get_by_test_id("firstrun-local-ai")
            local_ai.get_by_role("button", name=re.compile(r"^Set up local AI")).click()
            expect(local_ai.get_by_text("ON DEVICE").first).to_be_visible(timeout=60_000)
            you = page.get_by_test_id("firstrun-you")
            with page.expect_response(lambda r: r.url.endswith("/api/settings") and r.request.method == "PUT"):
                you.get_by_role("textbox", name="Your name", exact=True).fill("Karol Sane")
            open_desk = page.get_by_role("button", name="Open my desk", exact=True)
            expect(open_desk).to_be_visible(timeout=15_000)
            if "btn--primary" not in (open_desk.get_attribute("class") or ""):
                fails["F3 Open my desk is the primary"] = open_desk.get_attribute("class")
            if page.get_by_role("button", name="Continue later", exact=True).count():
                fails["F3 Continue later left once the cards are done"] = "present"
            words = page.get_by_test_id("firstrun-first-words")
            if words.get_attribute("data-selected") != "true":
                fails["F3 First words is done after a first dictation"] = words.get_attribute("data-selected")
            open_desk.scroll_into_view_if_needed()
            shot("all-set")
            open_desk.click()
            face.wait_for(state="detached", timeout=15_000)
            page.locator(".chair:not(.chair-first-value)").wait_for()
            shot("desk-after")
            browser.close()
    finally:
        server.stop()
        source.close()
    assert not fails, fails


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
    from .test_firstrun_heard_glass import WAV

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
            closer = page.get_by_role("button", name="Close Setup", exact=True)
            if closer.count():
                closer.first.click()

            # 2. No speech model on the hub -> "Runs on" -> the Runs on window.
            page.evaluate("window.__denyMic = false")
            words.get_by_role("button", name="Again", exact=True).click()
            runs_on = words.get_by_role("button", name="Runs on", exact=True)
            try:
                runs_on.wait_for(timeout=20_000)
                runs_on.click()
                if not _on_glass(page, "[data-testid='switchboard']"):
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
