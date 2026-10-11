"""PHILO-17 (lane doors) -- one primary door per application; the menus index.

The owner, 2026-10-10: "How many doors an app keeps is dependent on best
UI/UX practices and your determination of them." The plan (ONE-DESK-PLAN.md
§3) and Muad'Dib's rulings: Speak, Meetings and Intelligence ride the Dock;
People and the Conductor are desk drawers; Settings, Runs on, Connections
and Setup are in the HoldSpeak menu; Go is the index (seven applications,
Projects ▸, Tools ▸); projects left the Dock. One name per thing: the Dock's
Missed list, the Memory application; "Desk memory" is nowhere.

Through ONE real hub on an isolated HOME and the built bundle, with three
projects:

  D1 (1440) the Dock is Intelligence, Speak, Meetings and the launchers; it
     does not overflow; no project, People, Conductor or Settings tile.
  D2 (1440) Go is the nine rows; Projects ▸ lists the three; Tools ▸ the six;
     no ⌘1-⌘4 hint; the HoldSpeak menu is Refresh + the four setup rows.
  D3 (1440) every application opens from its kept door.
  D4 (393) Go keeps the B21 shape without Settings; the HoldSpeak menu opens
     Settings.
  D5 (both) "Desk memory" and "List view" appear nowhere: not in the text,
     not in a name, with Go, the HoldSpeak menu and Missed open.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the doors glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "philo17-doors"
SHOTS = evidence_dir("docs/internal/philo/phase-17/doors-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000
PROJECTS = ["Ledger cutover", "Platform observability", "Hiring loop"]

GO_ROWS = ["Speak", "Meetings", "Intelligence", "Ask AI", "People", "Conductor", "Memory", "Projects", "Tools"]
TOOLS = ["Workbenches", "Activity", "Processes", "Rhythm", "Commands", "Context"]
MARK_ROWS = ["Refresh from hub", "Settings", "Runs on", "Connections", "Setup"]
PHONE_GO = ["Needs you", "Brief", "The week", "Capture", "Meetings", "People", "Conductor", *sorted(PROJECTS), "New"]

# The rows of the innermost open menu list (a submenu nests in its parent).
ROWS_JS = r"""(n) => {
  const lists = [...document.querySelectorAll('.desk-menu-list')];
  const list = lists[lists.length - 1 - (n || 0)];
  if (!list) return null;
  return [...list.querySelectorAll(':scope > [role^=menuitem], :scope > * > [role^=menuitem]')]
    .map((e) => (e.querySelector('.desk-menu-label') || e).textContent.replace(/\s+/g, ' ').trim());
}"""

# Every word a user can read or hear on the page.
WORDS_JS = r"""() => {
  const out = [document.body.innerText];
  for (const e of document.querySelectorAll('[aria-label],[title]'))
    out.push(e.getAttribute('aria-label') || '', e.getAttribute('title') || '');
  return out.join('\n');
}"""

DOCK_JS = r"""() => {
  const d = document.querySelector('.desk-dock');
  const r = d.getBoundingClientRect();
  return {scroll: d.scrollWidth, client: d.clientWidth, right: Math.round(r.right), vw: innerWidth,
    apps: [...d.querySelectorAll('[data-app]')].map((e) => e.getAttribute('data-app')),
    launchers: [...d.querySelectorAll('[data-launcher]')].map((e) => e.getAttribute('aria-label')),
    projects: d.querySelectorAll('.desk-dock-project').length};
}"""

SHELLS_JS = r"""() => [...document.querySelectorAll('.desk-window-shell:not([data-departing]), .conductor-window')]
  .map((s) => s.getAttribute('aria-label') || (s.classList.contains('conductor-window') ? 'Conductor' : ''))"""


def _seed() -> None:
    from holdspeak.db import get_database

    db = get_database()
    for i, name in enumerate(PROJECTS):
        db.projects.create_project(project_id=f"p-door-{i}", name=name, description="", keywords=[])


def _row(page: Any, label: str) -> Any:
    """The menu row whose label is `label` (its name also carries a keycap)."""
    return page.locator("[role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(f"^{re.escape(label)}$"))).last


class TestDoors:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _fresh(self, page: Any) -> None:
        clear_hub_windows(page, TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        _settle(page)

    def _menu(self, page: Any, which: str) -> list[str]:
        if which == "mark":
            page.locator(".desk-mark").click()
        else:
            page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
        page.locator(".desk-menu-list").first.wait_for()
        return page.evaluate(ROWS_JS, 0)

    def _no_old_names(self, page: Any, where: str, fails: dict[str, Any]) -> None:
        words = page.evaluate(WORDS_JS)
        for old in ("Desk memory", "List view"):
            if old in words:
                fails[f"D5 no '{old}' ({where})"] = [line for line in words.splitlines() if old in line][:3]

    def _opens(self, page: Any, door: Callable[[], None], name: str) -> list[str]:
        self._fresh(page)
        door()
        want = re.compile(name)
        deadline = time.monotonic() + T / 1000
        while time.monotonic() < deadline:
            hits = [n for n in page.evaluate(SHELLS_JS) if want.search(n or "")]
            if hits:
                return hits
            page.wait_for_timeout(250)
        raise AssertionError(f"no window named {name!r}")

    def test_one_door_per_application(self) -> None:
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                ctx = browser.new_context(viewport={"width": 1440, "height": SIZES[1440]}, device_scale_factor=1)
                page = ctx.new_page()
                page.set_default_timeout(T)
                errors: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                self._fresh(page)

                # ── D1: the Dock ────────────────────────────────────────────
                dock = page.evaluate(DOCK_JS)
                if dock["apps"] != ["intelligence:desk", "surface-dictation", "surface-meetings"]:
                    fails["D1 the Dock seats Intelligence, Speak, Meetings"] = dock["apps"]
                if dock["projects"]:
                    fails["D1 no project tile"] = dock["projects"]
                if dock["scroll"] > dock["client"] + 1 or dock["right"] > dock["vw"]:
                    fails["D1 the Dock does not overflow with three projects"] = dock
                if not any(label.startswith("Missed") for label in dock["launchers"]):
                    fails["D1 the Missed launcher"] = dock["launchers"]
                page.screenshot(path=str(SHOTS / "1440-dock.png"))

                # ── D2: Go and the HoldSpeak menu ───────────────────────────
                go = self._menu(page, "go")
                if go != GO_ROWS:
                    fails["D2 Go is the nine rows"] = go
                go_text = page.locator(".desk-menu-list").first.inner_text()
                if re.search(r"⌘[1-4]\b", go_text):
                    fails["D2 no ⌘1-⌘4 hint"] = go_text
                self._no_old_names(page, "Go open", fails)
                page.screenshot(path=str(SHOTS / "1440-go.png"))
                page.get_by_role("menuitem", name="Projects").click()
                projects = page.evaluate(ROWS_JS, 0)
                if sorted(p for p in (projects or []) if p in PROJECTS) != sorted(PROJECTS):
                    fails["D2 Go ▸ Projects lists the three"] = projects
                page.keyboard.press("Escape")
                page.keyboard.press("Escape")
                self._menu(page, "go")
                page.get_by_role("menuitem", name="Tools").click()
                tools = page.evaluate(ROWS_JS, 0)
                if [t for t in (tools or []) if t in TOOLS] != TOOLS or "Settings" in (tools or []):
                    fails["D2 Go ▸ Tools is the six"] = tools
                page.keyboard.press("Escape")
                page.keyboard.press("Escape")
                mark = self._menu(page, "mark")
                if mark != MARK_ROWS:
                    fails["D2 the HoldSpeak menu is the setup rows"] = mark
                self._no_old_names(page, "HoldSpeak menu open", fails)
                page.keyboard.press("Escape")

                # D5 with Missed open (the Dock launcher opens the shade).
                page.locator(".desk-dock [data-launcher='attention']").click()
                page.get_by_role("group", name="Missed").wait_for()
                self._no_old_names(page, "Missed open", fails)
                page.screenshot(path=str(SHOTS / "1440-missed.png"))

                # ── D3: every application opens from its kept door ──────────
                def dock_tile(app: str) -> Callable[[], None]:
                    return lambda: page.locator(f".desk-dock [data-app='{app}']").click()

                def drawer(key: str) -> Callable[[], None]:
                    return lambda: page.locator(f".desk-screen [data-object-id='{key}']").dblclick()

                def go_row(*path: str) -> Callable[[], None]:
                    def run() -> None:
                        self._menu(page, "go")
                        for label in path:
                            _row(page, label).click()
                    return run

                def mark_row(label: str) -> Callable[[], None]:
                    def run() -> None:
                        self._menu(page, "mark")
                        _row(page, label).click()
                    return run

                doors: list[tuple[str, Callable[[], None], str]] = [
                    ("Speak (Dock)", dock_tile("surface-dictation"), "^Speak"),
                    ("Meetings (Dock)", dock_tile("surface-meetings"), "^Meetings"),
                    ("Intelligence (Dock)", dock_tile("intelligence:desk"), "^Intelligence"),
                    ("People (drawer)", drawer("drawer:people"), "^People"),
                    ("Conductor (drawer)", drawer("drawer:conductor"), "^Conductor"),
                    ("Ask AI (Go)", go_row("Ask AI"), "Ask"),
                    ("Memory (Go)", go_row("Memory"), "^Memory"),
                    ("a project (Go ▸ Projects)", go_row("Projects", PROJECTS[0]), f"^{PROJECTS[0]}"),
                    ("Workbenches (Go ▸ Tools)", go_row("Tools", "Workbenches"), "^Workbenches"),
                    ("Settings (HoldSpeak)", mark_row("Settings"), "^Settings"),
                    ("Runs on (HoldSpeak)", mark_row("Runs on"), "^Runs on"),
                    ("Connections (HoldSpeak)", mark_row("Connections"), "^(Settings|Connections)"),
                    ("Setup (HoldSpeak)", mark_row("Setup"), "^Setup"),
                ]
                for what, door, name in doors:
                    try:
                        self._opens(page, door, name)
                    except Exception as exc:  # noqa: BLE001 -- the fence names every door that failed
                        fails[f"D3 {what} opens"] = {"error": str(exc)[:160], "shells": page.evaluate(SHELLS_JS)}
                page.screenshot(path=str(SHOTS / "1440-last-door.png"))
                if errors:
                    fails["1440 no page errors"] = errors[:5]
                ctx.close()

                # ── D4: the phone ───────────────────────────────────────────
                ctx = browser.new_context(viewport={"width": 393, "height": SIZES[393]},
                                          device_scale_factor=1, has_touch=True)
                page = ctx.new_page()
                page.set_default_timeout(T)
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                self._fresh(page)
                go = self._menu(page, "go")
                if go != PHONE_GO:
                    fails["D4 393 Go keeps the B21 shape without Settings"] = go
                self._no_old_names(page, "393 Go open", fails)
                page.screenshot(path=str(SHOTS / "393-go.png"))
                page.keyboard.press("Escape")
                try:
                    self._opens(page, mark_row("Settings"), "^Settings")
                except Exception as exc:  # noqa: BLE001
                    fails["D4 393 the HoldSpeak menu opens Settings"] = str(exc)[:160]
                self._fresh(page)
                self._no_old_names(page, "393 desk", fails)
                page.screenshot(path=str(SHOTS / "393-desk.png"))
                if errors:
                    fails["393 no page errors"] = errors[:5]
                ctx.close()
            finally:
                browser.close()
        (SHOTS / "fails.json").write_text(json.dumps(fails, indent=1, default=str))
        assert not fails, fails
