#!/usr/bin/env python3
"""HS-202-04 — the shot walk for names and repeats on the touched flows.

One real hub per viewport, isolated HOME, Playwright Chromium, 1440x900
and 393x852. It changes no product code and NEVER opens the microphone:
the browser context is given no microphone permission.

It photographs each label this story changed, in place on a real face:

  live-summary        Live: the host row, the `Summary` section in the
                      gear door, the footer receipt with no `SEG`
  meetings-empty      the cold Meetings face: the headline keeps the
                      all-clear, the rail states the next move
  settings-hub        the Settings hub's Meetings row: `SUMMARY ON/OFF`
  settings-meetings   the meetings module's `Summary` row
  floor-list-zone     an empty zone: `EMPTY`, never `0 ITEMS`, and its
                      accessible name recorded as a fact
  ask-session         Ask AI's session head: `SESSION`, never `· 0 TURNS`
  speak-door          the Speak gear door: no `Runs 0`, `RAW · READINESS`
  sequence-pullout    a saved Sequence's own verb: `Edit Sequence`

Two labels cannot be staged on a fixture hub and are NOT claimed here:
the Meetings gear door's `Retry` needs a FAILED intel queue job (no mint
route exists), and the Room's `Meeting · … · Segment N` needs a Project
Room with a linked person and a Watch. Their fences carry the proof
(`pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx`,
`features/project-room/__tests__/provenanceWords202.test.ts`).

Run:
    HOME=$(mktemp -d) \
    PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
        uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/\
assets/story-04-shots/shoot.py
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[6]
TOKEN = "hs-202-04-shot-walk-token"
VIEWPORTS = ((1440, 900), (393, 852))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class Hub:
    def __init__(self, port: int, token: str, home: str) -> None:
        self.port, self.token, self.home = port, token, home
        self.url = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self, timeout: float = 180.0) -> "Hub":
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
            cwd=str(REPO), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
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

    def healthy(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1.0):
                pass
        except OSError:
            return False
        try:
            req = urllib.request.Request(
                f"{self.url}/health", headers={"X-HoldSpeak-Token": self.token})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:  # noqa: BLE001
            return False

    def api(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.url}{path}", data=data, method=method,
            headers={"X-HoldSpeak-Token": self.token,
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except Exception:  # noqa: BLE001
                    return resp.status, raw[:400]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()[:400]
        except Exception as exc:  # noqa: BLE001
            return 0, repr(exc)

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def shoot(page, name: str, width: int) -> None:
    path = HERE / f"{name}-{width}.png"
    page.screenshot(path=str(path))
    print(f"    shot {path.name}", flush=True)


def settle(page, ms: int = 900) -> None:
    page.wait_for_timeout(ms)


def step(name: str, facts: dict[str, Any], width: int, fn) -> None:
    """One step. A miss is RECORDED, never fatal and never silent."""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        facts.setdefault("step_errors", {}).setdefault(str(width), {})[name] = repr(exc)[:300]
        print(f"    !! {name}: {exc}", flush=True)


def close_shelf(page) -> None:
    for _ in range(3):
        if not page.locator("#desk-tool-shelf").count():
            return
        box = page.locator("#desk-tool-shelf input")
        if box.count():
            try:
                box.first.press("Escape")
            except Exception:  # noqa: BLE001
                pass
        settle(page, 400)
        if not page.locator("#desk-tool-shelf").count():
            return
        launch = page.locator(".desk-tools-launch")
        if launch.count():
            try:
                launch.first.click(timeout=3000, force=True)
            except Exception:  # noqa: BLE001
                pass
        settle(page, 400)


def close_windows(page) -> None:
    for _ in range(3):
        lights = page.locator("[aria-label^='Close ']")
        if not lights.count():
            break
        for i in range(lights.count() - 1, -1, -1):
            try:
                lights.nth(i).click(timeout=1500)
            except Exception:  # noqa: BLE001
                pass
        settle(page, 500)
    settle(page, 500)


def goto_desk(page, hub: Hub, width: int, facts: dict[str, Any]) -> None:
    """Load the desk. A cold desk answers with the First Words gate; its
    only escape ("Continue later") reaches the desk behind it."""
    page.goto(f"{hub.url}/?token={hub.token}", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:  # noqa: BLE001
        pass
    settle(page, 2500)
    gate = page.locator(".desk-first-words")
    if gate.count():
        escape = page.locator(".desk-first-words .btn--ghost")
        if escape.count():
            try:
                escape.first.click(timeout=15000, force=True)
            except Exception:  # noqa: BLE001
                facts.setdefault("gate_escape_failed", {})[str(width)] = True
            settle(page, 3000)


def open_surface(page, query: str) -> None:
    """Open a surface the way a person does: the ⌘K shelf."""
    close_shelf(page)
    launch = page.locator(".desk-tools-launch")
    if launch.count():
        launch.first.click(timeout=8000)
        settle(page, 700)
    box = page.locator("#desk-tool-shelf input")
    if box.count():
        box.first.fill(query)
        settle(page, 900)
        page.keyboard.press("Enter")
    settle(page, 4500)
    close_shelf(page)


def walk(page, width: int, hub: Hub, facts: dict[str, Any]) -> None:
    goto_desk(page, hub, width, facts)

    def menu_verb(menu: str, name: str) -> bool:
        """Press a verb through its own menu.

        Astra's counsel on #599, finding/condition 4: at 393 the menu bar
        renders ONLY `go`, and the Desk/Object/Window entries are folded
        inside it (HS-202-02; `desk/__tests__/phoneDoors.test.tsx:104`).
        A rig that only knows the `desk` menu cannot reach the Floor's
        view verbs at phone width — which is why the first round recorded
        "the list face did not open at 393" as if it were a product fact.
        The fold carries about forty rows, so the entry is scrolled to
        before it is pressed."""
        close_shelf(page)
        for candidate in (menu, "go"):
            title = page.locator(
                f'[data-menu-id="{candidate}"] .desk-verbbar-title')
            if not title.count():
                continue
            title.first.click(timeout=5000)
            settle(page, 700)
            item = page.get_by_role("menuitem", name=name)
            if not item.count():
                page.keyboard.press("Escape")
                settle(page, 400)
                continue
            try:
                item.first.scroll_into_view_if_needed(timeout=3000)
            except Exception:  # noqa: BLE001
                pass
            item.first.click(timeout=5000)
            settle(page, 1500)
            facts.setdefault("menu_door_used", {}).setdefault(
                str(width), {})[name] = candidate
            return True
        return False

    def live() -> None:
        # The orb IS Live's door (the census: Live has no Go/dock entry).
        orb = page.locator(".desk-dock .desk-orb")
        if orb.count():
            try:
                orb.first.click(timeout=8000)
                settle(page, 4000)
            except Exception:  # noqa: BLE001
                pass
        if not page.locator("#surface-live").count():
            open_surface(page, "Live meeting")
        root = page.locator("#surface-live")
        facts.setdefault("live", {})[str(width)] = {
            "window": root.count(),
            "facts_line": (root.locator(".surface-fact-line").first.inner_text().strip()
                           if root.locator(".surface-fact-line").count() else "ABSENT"),
            "footer_receipt": (
                root.locator(".surface-footer-receipt-line").first.inner_text().strip()
                if root.locator(".surface-footer-receipt-line").count() else "ABSENT"),
            "section_labels": [
                root.locator("h3").nth(i).inner_text().strip()
                for i in range(root.locator("h3").count())
            ],
            "body_has_SEG": "SEG" in (root.inner_text() if root.count() else ""),
        }
        shoot(page, "live-summary", width)
        # The gear door carries the second `Summary` section.
        gear = root.locator("[aria-label*='Configure'], .desk-wing-gear, "
                            "button[title*='Configure']")
        if gear.count():
            try:
                gear.first.click(timeout=5000)
                settle(page, 2000)
            except Exception:  # noqa: BLE001
                pass
        facts["live"][str(width)]["door_labels"] = [
            root.locator("h3").nth(i).inner_text().strip()
            for i in range(root.locator("h3").count())
        ]
        shoot(page, "live-door-summary", width)
        close_windows(page)

    def meetings_empty() -> None:
        """The seeded desk holds one meeting; the cold face is the state
        this story's M6 record was taken on, so clear it first."""
        status, body = hub.api("GET", "/api/meetings?limit=50")
        rows = (body or {}).get("meetings", []) if isinstance(body, dict) else []
        for row in rows:
            hub.api("DELETE", f"/api/meetings/{row.get('id')}")
        facts.setdefault("meetings_cleared", {})[str(width)] = len(rows)
        page.reload(wait_until="domcontentloaded")
        settle(page, 3000)
        open_surface(page, "Meetings")
        root = page.locator("#surface-meetings")
        head = root.locator(".surface-display")
        empty = root.locator(".surface-state[data-kind='empty']")
        facts.setdefault("meetings_empty", {})[str(width)] = {
            "window": root.count(),
            "headline": head.first.inner_text().strip() if head.count() else "ABSENT",
            "empty_lines": [
                empty.nth(i).inner_text().strip().replace("\n", " ")
                for i in range(empty.count())
            ],
            "no_meetings_yet_count": (root.inner_text() if root.count() else "")
            .count("No meetings yet"),
        }
        shoot(page, "meetings-empty", width)
        close_windows(page)

    def settings_hub() -> None:
        open_surface(page, "Settings")
        root = page.locator("#surface-settings")
        chips = root.locator(".surface-state-chip, .signal-state-chip")
        facts.setdefault("settings_hub", {})[str(width)] = {
            "window": root.count(),
            "chips": [chips.nth(i).inner_text().strip()
                      for i in range(chips.count())],
            "body_has_INTELLIGENCE": "INTELLIGENCE" in (
                root.inner_text() if root.count() else ""),
        }
        shoot(page, "settings-hub", width)

        meetings_row = root.get_by_text("Meetings", exact=True)
        if meetings_row.count():
            try:
                meetings_row.first.click(timeout=5000)
                settle(page, 2500)
            except Exception:  # noqa: BLE001
                pass
        labels = root.locator(".gadget-row-label")
        facts["settings_hub"][str(width)]["meetings_module_rows"] = [
            labels.nth(i).inner_text().strip() for i in range(labels.count())
        ]
        shoot(page, "settings-meetings", width)
        close_windows(page)

    def floor_zone() -> None:
        """An empty zone: `EMPTY` in the cell, and no `0 items` in the
        accessible name a screen reader hears."""
        status, body = hub.api(
            "POST", "/api/directories", {"name": "Launch"})
        facts.setdefault("zone_minted", {})[str(width)] = status
        page.reload(wait_until="domcontentloaded")
        settle(page, 3000)
        close_shelf(page)
        # The list face lives on the FLOOR, not the arrival: open the
        # Floor from the dock first, then flip its view.
        floor = page.locator(".desk-dock .desk-dock-launch[aria-label*='Floor']")
        if floor.count():
            try:
                floor.first.click(timeout=6000)
                settle(page, 2500)
            except Exception:  # noqa: BLE001
                pass
        facts.setdefault("floor_opened", {})[str(width)] = page.locator(
            ".desk-floor, .desk-stage, .desk-listmode").count()
        # The Floor's view verbs are Floor-scoped. The menu door is the
        # one a person uses (the Desk menu at 1440, the folded Go menu at
        # 393); the palette is the fallback.
        menu_verb("desk", "List view")
        if not page.locator(".desk-listmode").count():
            open_surface(page, "List view")
            settle(page, 1200)
        facts.setdefault("list_view_opened", {})[str(width)] = (
            page.locator(".desk-listmode").count() > 0)
        settle(page, 1500)
        names = page.evaluate(
            "() => [...document.querySelectorAll('[aria-label]')]"
            ".map(e => e.getAttribute('aria-label'))"
            ".filter(n => n && n.includes('zone'))"
        )
        facts.setdefault("floor_list", {})[str(width)] = {
            "list_view": page.locator(".desk-listmode").count(),
            "rows": page.locator("tr").count(),
        }
        cells = page.evaluate(
            "() => [...document.querySelectorAll('td')]"
            ".map(c => (c.textContent || '').trim())"
        )
        facts.setdefault("floor_zone", {})[str(width)] = {
            "zone_aria_names": names,
            "zero_item_names": [n for n in names if "0 item" in n],
            "zero_item_cells": [c for c in cells if c in ("0 ITEMS", "0 ITEM")],
            "empty_cells": [c for c in cells if c == "EMPTY"],
        }
        shoot(page, "floor-list-zone", width)
        # back to the spatial Floor for the next steps
        menu_verb("desk", "Spatial view")
        if page.locator(".desk-listmode").count():
            open_surface(page, "Spatial view")
        settle(page, 1200)

    def ask_session() -> None:
        close_shelf(page)
        open_surface(page, "Ask AI")
        settle(page, 1500)
        head = page.locator(".desk-ask-body .surface-well-head")
        facts.setdefault("ask", {})[str(width)] = {
            "panel": page.locator(".desk-ask").count(),
            "session_head": head.first.inner_text().strip() if head.count() else "ABSENT",
        }
        shoot(page, "ask-session", width)
        close_windows(page)

    def speak_door() -> None:
        open_surface(page, "Speak")
        root = page.locator("#surface-dictation")
        gear = page.get_by_role("button", name="Configure dictation")
        if gear.count():
            try:
                gear.first.click(timeout=5000)
                settle(page, 2500)
            except Exception:  # noqa: BLE001
                pass
        labels = root.locator(".gadget-row-label")
        folds = root.locator(".gadget-fold-title, .gadget-fold summary, "
                             ".gadget-fold-head")
        text = root.inner_text() if root.count() else ""
        facts.setdefault("speak_door", {})[str(width)] = {
            "window": root.count(),
            "rows": [labels.nth(i).inner_text().strip()
                     for i in range(labels.count())],
            "folds": [folds.nth(i).inner_text().strip().replace("\n", " ")
                      for i in range(folds.count())],
            "has_runs_row": "Runs" in [labels.nth(i).inner_text().strip()
                                       for i in range(labels.count())],
            "has_wire_details": "Wire details" in text,
            "has_raw_readiness": "RAW · READINESS" in text,
        }
        shoot(page, "speak-door", width)
        close_windows(page)

    def sequence_pullout() -> None:
        status, body = hub.api(
            "POST", "/api/chains",
            {"name": "Release readiness", "steps": []})
        facts.setdefault("sequence_minted", {})[str(width)] = status
        page.reload(wait_until="domcontentloaded")
        settle(page, 3500)
        close_shelf(page)
        open_surface(page, "Release readiness")
        settle(page, 2000)
        pullout = page.locator(".desk-pullout")
        text = pullout.first.inner_text() if pullout.count() else ""
        facts.setdefault("sequence", {})[str(width)] = {
            "pullout": pullout.count(),
            "has_edit_sequence": "Edit Sequence" in text,
            "has_edit_chain": "Edit chain" in text,
        }
        shoot(page, "sequence-pullout", width)
        close_windows(page)

    step("live", facts, width, live)
    step("settings", facts, width, settings_hub)
    step("ask", facts, width, ask_session)
    step("speak-door", facts, width, speak_door)
    step("sequence", facts, width, sequence_pullout)
    step("floor-zone", facts, width, floor_zone)
    # LAST: clearing the ledger is destructive for every other step.
    step("meetings-empty", facts, width, meetings_empty)


def main() -> int:
    # The owner's real desk is never touched: this rig refuses to run
    # unless HOME is a throwaway directory (the scar behind
    # `reference_walk_seeds_in_real_db.md`).
    home = os.path.realpath(os.environ.get("HOME", ""))
    temp_root = os.path.realpath(tempfile.gettempdir())
    if not home or not (home.startswith(temp_root) or home.startswith("/tmp")):
        print(f"REFUSED: run with an isolated HOME=$(mktemp -d) (got {home!r})",
              file=sys.stderr)
        return 2
    from playwright.sync_api import sync_playwright

    HERE.mkdir(parents=True, exist_ok=True)
    facts: dict[str, Any] = {"home": home}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width, height in VIEWPORTS:
            print(f"  == {width}x{height} ==", flush=True)
            viewport_home = tempfile.mkdtemp(prefix=f"hs202-04-{width}-")
            hub = Hub(_free_port(), TOKEN, viewport_home).start()
            facts.setdefault("hubs", {})[str(width)] = hub.url
            # NO microphone permission: the browser refuses `getUserMedia`
            # and no device is ever opened.
            context = browser.new_context(
                viewport={"width": width, "height": height},
                permissions=[],
            )
            page = context.new_page()
            page.on("pageerror",
                    lambda e: facts.setdefault("page_errors", []).append(str(e)[:300]))
            page.on("console", lambda m: (
                facts.setdefault("console_errors", []).append(m.text[:300])
                if m.type == "error" else None))
            page.on("response", lambda r: (
                facts.setdefault("bad_responses", []).append(
                    f"{r.status} {r.request.method} {r.url.split('?')[0]}")
                if r.status >= 400 else None))
            try:
                walk(page, width, hub, facts)
            finally:
                context.close()
                hub.stop()
        browser.close()
    (HERE / "walk-facts.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
