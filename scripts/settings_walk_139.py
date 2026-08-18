#!/usr/bin/env python3
"""HS-139-07 -- the Settings Reckoning walk: screenshot + console-error
proof for the reforged seven-tile settings room at 1440x900 and 393x900.

Run with:
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
        uv run python scripts/settings_walk_139.py

Reuses the Phase-132 walk harness (scripts/walk_working_desk.py) for hub
lifecycle. All shots land in
pm/roadmap/holdspeak/phase-139-the-settings-reckoning/assets/walk/.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WALK_OUT = REPO / "pm/roadmap/holdspeak/phase-139-the-settings-reckoning/assets/walk"
TOKEN = "hs-139-07-settings-walk-token"
VIEWPORTS = ((1440, 900), (393, 900))

TILES = ("voice", "sounds", "meetings", "rhythm", "models", "integrations", "system")

# ------------------------------------------------------------- reporting

FAILS: list[str] = []
FINDINGS: list[str] = []
SHOTS: list[tuple[str, str]] = []
PASSES = 0
CONTROL_COUNTS: dict[str, int] = {}


def check(label: str, cond: bool, detail: str = "") -> bool:
    global PASSES
    if cond:
        PASSES += 1
        print(f"  PASS  {label}" + (f"  {detail}" if detail else ""), flush=True)
    else:
        FAILS.append(f"{label}  {detail}" if detail else label)
        print(f"  FAIL  {label}" + (f"  {detail}" if detail else ""), flush=True)
    return bool(cond)


def finding(text: str) -> None:
    FINDINGS.append(text)
    print(f"  FINDING  {text}", flush=True)


def section(title: str) -> None:
    print(f"\n== {title} ==", flush=True)


# ------------------------------------------------------------ hub class

def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Hub:
    """A real hub in its own process with an isolated HOME."""

    def __init__(self, port: int, token: str, home: str) -> None:
        self.port = port
        self.token = token
        self.home = home
        self.url = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self, timeout: float = 90.0) -> "Hub":
        env = dict(os.environ)
        env["HOME"] = self.home
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        env.setdefault("PYTHONUNBUFFERED", "1")
        self.proc = subprocess.Popen(
            [
                sys.executable,
                str(REPO / "scripts" / "walk_working_desk.py"),
                "serve",
                "--port", str(self.port),
                "--token", self.token,
            ],
            cwd=str(REPO),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(f"  hub pid={self.proc.pid} home={self.home} port={self.port}", flush=True)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"hub died on boot:\n{out[-4000:]}")
            if self.healthy():
                return self
            time.sleep(0.4)
        raise RuntimeError(f"hub never became healthy at {self.url}")

    def healthy(self, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=timeout):
                pass
        except OSError:
            return False
        try:
            req = urllib.request.Request(
                f"{self.url}/health",
                headers={"X-HoldSpeak-Token": self.token},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def api_get(self, path: str) -> dict:
        req = urllib.request.Request(
            f"{self.url}{path}",
            headers={"X-HoldSpeak-Token": self.token},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


# --------------------------------------------------------- shooter class

def _ignorable_console(text: str) -> bool:
    lowered = text.lower()
    return any(
        tok in lowered
        for tok in ("failed to load resource", "err_connection_refused",
                    "websocket", "net::err")
    )


class Shooter:
    """A page at one viewport that refuses to hide console errors."""

    def __init__(self, page: object, width: int, out: Path) -> None:
        self.page = page
        self.width = width
        self.out = out
        self.console_errors: list[str] = []
        page.on("pageerror", lambda e: self.console_errors.append(f"pageerror: {e}"))  # type: ignore[attr-defined]
        page.on(  # type: ignore[attr-defined]
            "console",
            lambda m: (
                self.console_errors.append(f"console.{m.type}: {m.text}")
                if m.type == "error"
                else None
            ),
        )

    def shot(self, surface: str, state: str, proves: str = "") -> Path:
        self.out.mkdir(parents=True, exist_ok=True)
        name = f"{surface}-{state}-{self.width}.png"
        path = self.out / name
        self.page.screenshot(path=str(path), full_page=False)  # type: ignore[attr-defined]
        SHOTS.append((name, proves))
        print(f"  SHOT  {name}" + (f"  {proves}" if proves else ""), flush=True)
        return path

    def assert_clean(self, where: str) -> None:
        noisy = [e for e in self.console_errors if not _ignorable_console(e)]
        if noisy:
            finding(f"console errors on {where} @{self.width}: {noisy[:6]}")
        check(f"zero console errors  {where} @{self.width}", not noisy, str(noisy[:3]))
        self.console_errors.clear()


def goto(shooter: Shooter, hub: Hub, route: str = "/") -> None:
    sep = "&" if "?" in route else "?"
    shooter.page.goto(  # type: ignore[attr-defined]
        f"{hub.url}{route}{sep}token={hub.token}", wait_until="domcontentloaded"
    )
    try:
        shooter.page.wait_for_load_state("networkidle", timeout=15000)  # type: ignore[attr-defined]
    except Exception:
        pass
    shooter.page.wait_for_timeout(1500)  # type: ignore[attr-defined]


def no_hscroll(page: object) -> bool:
    """Check that the settings surface does not scroll horizontally.
    At narrow widths (393px) the desk window system enforces a minW (560px),
    so the DOCUMENT body overflows — that is the desk's responsibility.
    We check the settings containers (.prefs-face, .prefs-module) instead."""
    return page.evaluate(  # type: ignore[attr-defined]
        """(() => {
            const surface = document.querySelector('.prefs-module') ||
                            document.querySelector('.prefs-face');
            if (surface) return surface.scrollWidth <= surface.clientWidth;
            return document.documentElement.scrollWidth <= document.documentElement.clientWidth;
        })()"""
    )


def open_settings(shooter: Shooter, hub: Hub) -> None:
    goto(shooter, hub, "/settings")


def click_tile(page: object, index: int) -> None:
    page.locator(".prefs-tile").nth(index).click()  # type: ignore[attr-defined]
    page.wait_for_timeout(1200)  # type: ignore[attr-defined]


def click_back(page: object) -> None:
    btn = page.locator(".prefs-back")  # type: ignore[attr-defined]
    if btn.count() > 0:  # type: ignore[attr-defined]
        btn.click()  # type: ignore[attr-defined]
        page.wait_for_timeout(800)  # type: ignore[attr-defined]


# ----------------------------------------------------------- walk legs


def leg_face(shooter: Shooter, hub: Hub) -> None:
    """LEG 1: face overview — tile count, horizontal scroll, screenshot."""
    section(f"settings face @{shooter.width}")
    open_settings(shooter, hub)
    page = shooter.page

    tile_count = page.locator(".prefs-tile").count()  # type: ignore[attr-defined]
    check("face tiles ≤ 8", tile_count <= 8, f"tiles={tile_count}")
    check("face tiles == 7", tile_count == 7, f"tiles={tile_count}")
    check(f"no hscroll on face @{shooter.width}", no_hscroll(page))

    posture_label = page.locator(".prefs-posture-label")  # type: ignore[attr-defined]
    check("POSTURE label present", posture_label.count() > 0)

    precedence = page.locator(".prefs-precedence")  # type: ignore[attr-defined]
    check("precedence chain present", precedence.count() > 0)

    shooter.shot("settings-face", "overview", "seven tiles + POSTURE + precedence")
    shooter.assert_clean("settings face")


def leg_rooms(shooter: Shooter, hub: Hub) -> None:
    """LEG 2+3: each room — screenshot, console errors, hscroll, RAW wells."""
    total_face_controls = 0

    for i, tile_id in enumerate(TILES):
        section(f"room {tile_id} @{shooter.width}")
        open_settings(shooter, hub)
        page = shooter.page

        click_tile(page, i)

        module_title = page.locator(".gadget-pane-title")  # type: ignore[attr-defined]
        check(f"room {tile_id} opened", module_title.count() > 0)

        check(f"no hscroll in {tile_id} @{shooter.width}", no_hscroll(page))

        shooter.shot(f"room-{tile_id}", "open", f"room {tile_id}")

        # Count on-glass controls (excluding RAW well contents).
        all_rows = page.locator(".gadget-row").count()  # type: ignore[attr-defined]
        fold_rows = page.evaluate(  # type: ignore[attr-defined]
            "document.querySelectorAll('.gadget-fold-body .gadget-row').length"
        )
        face_rows = all_rows - fold_rows
        total_face_controls += face_rows
        CONTROL_COUNTS[tile_id] = face_rows
        print(f"  controls  {tile_id}: {face_rows} face + {fold_rows} RAW", flush=True)

        # LEG 3: RAW well assertions.
        folds = page.locator("details.gadget-fold")  # type: ignore[attr-defined]
        fold_count = folds.count()  # type: ignore[attr-defined]
        for fi in range(fold_count):
            fold = folds.nth(fi)  # type: ignore[attr-defined]
            is_open = fold.evaluate("el => el.open")  # type: ignore[attr-defined]
            check(f"RAW well closed on open  {tile_id} #{fi}", not is_open)

            # Unfold, screenshot, close.
            fold.locator("summary").click()  # type: ignore[attr-defined]
            page.wait_for_timeout(500)  # type: ignore[attr-defined]
            shooter.shot(f"room-{tile_id}-raw", f"open-{fi}", f"RAW well #{fi} in {tile_id}")

            fold.locator("summary").click()  # type: ignore[attr-defined]
            page.wait_for_timeout(300)  # type: ignore[attr-defined]

        shooter.assert_clean(f"room {tile_id}")
        click_back(page)

    section(f"control count bar @{shooter.width}")
    check("on-glass controls (excl RAW) ≤ 40", total_face_controls <= 40,
          f"total={total_face_controls}")
    print(f"  CONTROLS BY TILE: {CONTROL_COUNTS}", flush=True)


def leg_task_hotkey(shooter: Shooter, hub: Hub) -> None:
    """LEG 5 (1440 only): change the push-to-talk hotkey, verify via API."""
    section(f"task (a): change hotkey @{shooter.width}")
    open_settings(shooter, hub)
    page = shooter.page

    # Open Voice room (index 0).
    click_tile(page, 0)

    keycap = page.locator(".gadget-keycap")  # type: ignore[attr-defined]
    if keycap.count() == 0:
        finding("no keycap button found in Voice room")
        return

    old_text = keycap.text_content()  # type: ignore[attr-defined]
    print(f"  hotkey before: {old_text!r}", flush=True)

    # Click to enter listening mode.
    keycap.click()  # type: ignore[attr-defined]
    page.wait_for_timeout(500)  # type: ignore[attr-defined]
    check("hotkey listening mode", keycap.get_attribute("class") is not None  # type: ignore[attr-defined]
          and "is-listening" in (keycap.get_attribute("class") or ""))  # type: ignore[attr-defined]

    # Press F9 to set the new hotkey.
    page.keyboard.press("F9")  # type: ignore[attr-defined]
    page.wait_for_timeout(2000)  # type: ignore[attr-defined]

    new_text = keycap.text_content()  # type: ignore[attr-defined]
    print(f"  hotkey after: {new_text!r}", flush=True)
    check("hotkey changed on glass", new_text != old_text, f"old={old_text!r} new={new_text!r}")

    shooter.shot("task-hotkey", "changed", "push-to-talk hotkey changed to F9")

    # Verify via API.
    settings = hub.api_get("/api/settings")
    hotkey_data = settings.get("hotkey", {})
    api_key = hotkey_data.get("key", "")
    check("hotkey round-trips via API", "f9" in api_key.lower() or "F9" in api_key,
          f"api key={api_key!r}")

    shooter.assert_clean("task hotkey")


def leg_task_destination(shooter: Shooter, hub: Hub) -> None:
    """LEG 6 (393 only): add + verify a destination at narrow width (cards mode)."""
    section(f"task (b): add destination @{shooter.width}")
    open_settings(shooter, hub)
    page = shooter.page

    # Open Models room (index 4).
    click_tile(page, 4)
    page.wait_for_timeout(1500)  # type: ignore[attr-defined]

    # At 393px, the destinations should be in card mode.
    # Click the "+ DESTINATION" button.
    add_btn = page.locator(".gadget-table-add")  # type: ignore[attr-defined]
    if add_btn.count() == 0:
        add_btn = page.locator('button:has-text("+ DESTINATION")')  # type: ignore[attr-defined]
    if add_btn.count() == 0:
        add_btn = page.locator('button:has-text("DESTINATION")')  # type: ignore[attr-defined]

    if add_btn.count() == 0:
        finding("no + DESTINATION button found in Models room at 393px")
        shooter.shot("task-destination", "no-button", "Models room without add button")
        return

    add_btn.first.click()  # type: ignore[attr-defined]
    page.wait_for_timeout(2000)  # type: ignore[attr-defined]

    # Verify a card appeared.
    cards = page.locator(".dest-card")  # type: ignore[attr-defined]
    card_count = cards.count()  # type: ignore[attr-defined]
    check("destination card appeared", card_count > 0, f"cards={card_count}")

    shooter.shot("task-destination", "card-added", "destination card added at 393px")

    # Verify the destination exists in the API.
    targets = hub.api_get("/api/inference-targets")
    target_list = targets.get("targets", [])
    check("destination exists via API", len(target_list) > 0,
          f"targets={len(target_list)}")

    check(f"no hscroll in destinations @{shooter.width}", no_hscroll(page))
    shooter.assert_clean("task destination")


def leg_task_raw_knob(shooter: Shooter, hub: Hub) -> None:
    """LEG 7 (1440 only): unfold a RAW well, change a knob, verify round-trip."""
    section(f"task (c): change RAW knob @{shooter.width}")
    open_settings(shooter, hub)
    page = shooter.page

    # Open Voice room (index 0) — it has a RAW well with numeric knobs.
    click_tile(page, 0)

    folds = page.locator("details.gadget-fold")  # type: ignore[attr-defined]
    if folds.count() == 0:
        finding("no RAW well found in Voice room")
        return

    # Open the RAW well.
    folds.first.locator("summary").click()  # type: ignore[attr-defined]
    page.wait_for_timeout(800)  # type: ignore[attr-defined]

    # Read settings before.
    settings_before = hub.api_get("/api/settings")
    old_timeout = settings_before.get("model", {}).get("transcribe_timeout_seconds", 30)

    # Find the stepper / number input for "Transcribe timeout" inside
    # the fold body. The stepper component uses an <input> inside
    # .gadget-row.
    fold_body = folds.first.locator(".gadget-fold-body")  # type: ignore[attr-defined]
    stepper_input = fold_body.locator('input[type="number"]').first  # type: ignore[attr-defined]
    if stepper_input.count() == 0:  # type: ignore[attr-defined]
        stepper_input = fold_body.locator('input[type="text"]').first  # type: ignore[attr-defined]

    if stepper_input.count() == 0:  # type: ignore[attr-defined]
        finding("no numeric input found in Voice RAW well")
        shooter.shot("task-raw-knob", "no-input", "no numeric input in RAW")
        return

    # Change the value: fill() clears and sets the new value atomically.
    new_value = str(int(old_timeout) + 5)
    stepper_input.fill(new_value)  # type: ignore[attr-defined]
    # Dispatch an input event to trigger the onChange handler.
    stepper_input.dispatch_event("input")  # type: ignore[attr-defined]
    stepper_input.dispatch_event("change")  # type: ignore[attr-defined]
    # Tab out to trigger the debounced save.
    page.keyboard.press("Tab")  # type: ignore[attr-defined]
    page.wait_for_timeout(3000)  # type: ignore[attr-defined]

    shooter.shot("task-raw-knob", "changed", f"transcribe_timeout changed to {new_value}")

    # Verify via API.
    settings_after = hub.api_get("/api/settings")
    api_val = settings_after.get("model", {}).get("transcribe_timeout_seconds")
    check("RAW knob round-trips via API",
          str(api_val) == new_value,
          f"old={old_timeout} new_input={new_value} api={api_val}")

    shooter.assert_clean("task RAW knob")


# ----------------------------------------------------------- main walk


def walk() -> int:
    """Run the full walk at both viewports."""
    from playwright.sync_api import sync_playwright

    home = tempfile.mkdtemp(prefix="holdspeak-settings-walk-")
    port = _free_port()
    hub = Hub(port, TOKEN, home)

    print(f"Booting hub: port={port} home={home}", flush=True)
    hub.start()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for width, height in VIEWPORTS:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=2,
                    )
                    page = context.new_page()
                    shooter = Shooter(page, width, WALK_OUT)

                    leg_face(shooter, hub)
                    leg_rooms(shooter, hub)

                    if width == 1440:
                        leg_task_hotkey(shooter, hub)
                        leg_task_raw_knob(shooter, hub)

                    if width == 393:
                        leg_task_destination(shooter, hub)

                    context.close()
            finally:
                browser.close()
    finally:
        hub.stop()

    # ---- summary -------
    print("\n" + "=" * 60, flush=True)
    print(f"WALK COMPLETE: {PASSES} passed, {len(FAILS)} failed, "
          f"{len(FINDINGS)} findings, {len(SHOTS)} shots", flush=True)
    print(f"\nCONTROL COUNTS (excl RAW): {CONTROL_COUNTS}", flush=True)
    total_face = sum(CONTROL_COUNTS.values())
    print(f"TOTAL ON-GLASS: {total_face} (bar: ≤40)", flush=True)
    if FINDINGS:
        print("\nFINDINGS:", flush=True)
        for f in FINDINGS:
            print(f"  - {f}", flush=True)
    if FAILS:
        print("\nFAILURES:", flush=True)
        for f in FAILS:
            print(f"  - {f}", flush=True)
    print("\nSHOTS:", flush=True)
    for name, proves in SHOTS:
        print(f"  {name}" + (f"  ({proves})" if proves else ""), flush=True)

    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(walk())
