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

GO_ROWS = ["Speak", "Meetings", "Today", "Ask AI", "People", "Conductor", "Memory", "Projects", "Tools"]
TOOLS = ["Workbenches", "Activity", "Processes", "Rhythm", "Commands", "Context"]
MARK_ROWS = ["Refresh from hub", "Settings", "Runs on", "Connections", "Setup"]
PHONE_GO = ["Needs you", "Brief", "The week", "Capture", "Meetings", "Ask AI", "People", "Conductor", *sorted(PROJECTS), "New"]

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


def _seed() -> str:
    """Three projects, and one report whose 1:1 series is linked to an event
    in 3 hours (the People drawer's next 1:1). Returns that time as HH:MM."""
    import time as _time
    from datetime import datetime, timedelta, timezone

    from holdspeak.db import get_database
    from holdspeak.people import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService

    db = get_database()
    for i, name in enumerate(PROJECTS):
        db.projects.create_project(project_id=f"p-door-{i}", name=name, description="", keywords=[])
    start = (datetime.now(timezone.utc) + timedelta(hours=3)).replace(second=0, microsecond=0)
    iso = start.isoformat().replace("+00:00", "Z")
    end = (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO calendar_events (id, uid, title, starts_at, ends_at, last_seen_at, subscription_revision,"
            " source_id, source_label) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("ev-door-1on1", "uid-avery-1on1", "Avery / Karol 1:1", iso, end, _time.time(), "r1", "door-cal", "Work"))
        conn.commit()
    owner = Principal(PrincipalKind.OWNER, "karol")
    store = production_people_store()
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(owner, {"display_name": "Avery Chen", "relationship_kind": "direct_report"})
    people.link_calendar_series(owner, rel["id"], "uid-avery-1on1", "door-cal", "Avery / Karol 1:1")
    return start.astimezone().strftime("%H:%M")


def _press(page: Any, target: Any) -> None:
    """A real gesture: a finger tap on a phone page, a mouse click on a desk."""
    if (page.viewport_size or {}).get("width", 1440) < 720:
        target.tap()
    else:
        target.click()


# Is this Dock control fully on the shelf's visible page (left of More)?
ON_SHELF_JS = r"""(el) => {
  const d = el.closest('.desk-dock'); const more = d.querySelector('.desk-dock-more');
  const r = el.getBoundingClientRect(), b = d.getBoundingClientRect();
  const edge = more && getComputedStyle(more).display !== 'none' ? more.getBoundingClientRect().left : b.right;
  return r.width > 0 && r.left >= b.left - 0.5 && r.right <= edge + 0.5;
}"""


def _press_dock(page: Any, selector: str) -> None:
    """Press a Dock control as the phone does: page the shelf with More
    (a real tap) until the control is on the visible page, then tap it."""
    target = page.locator(selector).first
    for _ in range(6):
        if target.evaluate(ON_SHELF_JS):
            _press(page, target)
            return
        _press(page, page.locator(".desk-dock .desk-dock-more"))
        page.wait_for_timeout(450)
    raise AssertionError(f"{selector} never came onto the Dock's visible page")


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
        self.next_1on1 = _seed()
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
            _press(page, page.locator(".desk-mark"))
        else:
            _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"))
        page.locator(".desk-menu-list").first.wait_for()
        return page.evaluate(ROWS_JS, 0)

    def _no_old_names(self, page: Any, where: str, fails: dict[str, Any]) -> None:
        words = page.evaluate(WORDS_JS)
        for old in ("desk memory", "list view"):
            hits = [line for line in words.splitlines() if old in line.lower()]
            if hits:
                fails[f"D5 no '{old}' ({where})"] = hits[:3]

    def _one_on_one(self, page: Any, width: int, fails: dict[str, Any]) -> None:
        """The People drawer shows the next 1:1 (it left the Dock with People)."""
        want = f"1:1 {self.next_1on1}"
        caption = page.locator("[data-testid='desk-icon-caption-drawer:people']")
        try:
            caption.wait_for(timeout=T)
            text = caption.inner_text().strip()
        except Exception as exc:  # noqa: BLE001
            text = f"missing: {str(exc)[:80]}"
        if text != want:
            fails[f"{width} the People drawer shows the next 1:1"] = {"want": want, "got": text}
        label = page.locator(".desk-screen [data-object-id='drawer:people']").get_attribute("aria-label") or ""
        if want not in label:
            fails[f"{width} the People drawer says the next 1:1"] = label

    def _doors(self, page: Any, width: int, fails: dict[str, Any]) -> None:
        """D3: every application opens from each kept door, and the window
        holds that application's LOADED content (and scope)."""
        phone = width < 720

        def dom_click(selector: str) -> Callable[[], None]:
            # A real press; at 393 the shelf is paged with More first.
            return lambda: _press_dock(page, selector)

        def drawer(key: str) -> Callable[[], None]:
            def run() -> None:
                icon = page.locator(f".desk-screen [data-object-id='{key}']")
                icon.focus()
                page.keyboard.press("Enter")
            return run

        def go_row(*path: str) -> Callable[[], None]:
            def run() -> None:
                self._menu(page, "go")
                for label in path:
                    _press(page, _row(page, label))
            return run

        def mark_row(label: str) -> Callable[[], None]:
            def run() -> None:
                self._menu(page, "mark")
                _press(page, _row(page, label))
            return run

        def missed_memory() -> None:
            _press_dock(page, ".desk-dock [data-launcher='attention']")
            _press(page, page.get_by_role("group", name="Missed").get_by_role("button", name="Memory", exact=True))

        settings = "#surface-settings"
        # (door, how, the loaded content, what must NOT be there)
        doors: list[tuple[str, Callable[[], None], str, str | None]] = [
            # At 393 Speak opens the Chair's Capture window (PHILO-15 11).
            ("Speak (Dock)", dom_click(".desk-dock [data-app='surface-dictation']"),
             ".desk-window-shell[aria-label='Capture']" if phone else "#surface-dictation .speak-footer", None),
            ("Meetings (Dock)", dom_click(".desk-dock [data-app='surface-meetings']"), "#surface-meetings .meetings-head-verbs", None),
            ("Today (Dock)", dom_click(".desk-dock [data-app='intelligence:desk']"), ".intelligence-segment", None),
            ("People (drawer)", drawer("drawer:people"), "#surface-people >> text=Avery Chen", None),
            ("People (Go)", go_row("People"), "#surface-people >> text=Avery Chen", None),
            ("Conductor (drawer)", drawer("drawer:conductor"), ".conductor-window", None),
            ("Conductor (Go)", go_row("Conductor"), ".conductor-window", None),
            ("Change places (Dock)", dom_click(".desk-dock [aria-label='Change places']"),
             "#surface-places >> role=button[name='All places']", None),
            ("Settings (HoldSpeak)", mark_row("Settings"), f"{settings} .surface-ledger-primary >> text=Meetings",
             f"{settings} [data-testid='connections-github']"),
            ("Runs on (HoldSpeak)", mark_row("Runs on"), "[data-testid='switchboard']", None),
            ("Connections (HoldSpeak)", mark_row("Connections"), f"{settings} [data-testid='connections-github']", None),
            ("Setup (HoldSpeak)", mark_row("Setup"), "#surface-setup >> text=/Readiness checks|Everything is ready/", None),
        ]
        doors.append(("Ask AI (Go)", go_row("Ask AI"), ".desk-ask textarea, .desk-ask [role=textbox]", None))
        if phone:
            doors.append(("Memory (Missed ▸ Memory)", missed_memory,
                          "#surface-project-memory [aria-label='Search memory']", None))
        else:
            doors += [
                ("Memory (Go)", go_row("Memory"), "#surface-project-memory [aria-label='Search memory']", None),
                ("Workbenches (Go ▸ Tools)", go_row("Tools", "Workbenches"), "#surface-workbenches", None),
            ]
        for what, door, content, absent in doors:
            try:
                self._fresh(page)
                door()
                page.locator(content).first.wait_for(timeout=T)
                if absent:
                    page.wait_for_timeout(600)
                    if page.locator(absent).count():
                        fails[f"D3 {width} {what}: the right scope"] = f"{absent} is on glass"
                if "Memory" in what:
                    self._no_old_names(page, f"{width} Memory open", fails)
            except Exception as exc:  # noqa: BLE001 -- the fence names every door that failed
                fails[f"D3 {width} {what} opens loaded"] = {"error": str(exc)[:200], "shells": page.evaluate(SHELLS_JS)}
        page.screenshot(path=str(SHOTS / f"{width}-last-door.png"))

        # ── D6: a Room opens, iconifies to its own Dock tile, comes back ──
        room = PROJECTS[0]
        try:
            self._fresh(page)
            (go_row(room) if phone else go_row("Projects", room))()
            shell = page.locator(f".desk-window-shell[aria-label='{room}']")
            shell.wait_for(timeout=T)
            if phone:
                # The phone's own way: a Chair window takes the work area and
                # the window in front falls to its Dock tile (393 has no
                # Iconify gadget).
                go_row("Needs you")()
                page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=T)
            else:
                _press(page, page.locator(f"[aria-label='Iconify {room}']").first)
            seat = page.locator(".desk-dock [data-seat='surface-project-memory']")
            seat.wait_for(timeout=T)
            if not (seat.get_attribute("aria-label") or "").startswith(room):
                fails[f"D6 {width} the Room's tile names it"] = seat.get_attribute("aria-label")
            page.screenshot(path=str(SHOTS / f"{width}-room-seated.png"))
            _press_dock(page, ".desk-dock [data-seat='surface-project-memory']")
            page.locator("#surface-project-memory").wait_for(state="visible", timeout=T)
            page.locator(".desk-dock [data-seat='surface-project-memory']").wait_for(state="detached", timeout=T)
        except Exception as exc:  # noqa: BLE001
            fails[f"D6 {width} Room open → iconify → restore from its tile"] = {
                "error": str(exc)[:200], "shells": page.evaluate(SHELLS_JS)}

        # ── D7 (Astra r2): Go ▸ Ask AI, Go ▸ Capture, Go ▸ Ask AI shows Ask ──
        if phone:
            try:
                self._fresh(page)
                ask = page.locator(".desk-ask")
                go_row("Ask AI")()
                ask.wait_for(state="visible", timeout=T)
                go_row("Capture")()
                page.locator(".desk-window-shell[aria-label='Capture']").wait_for(state="visible", timeout=T)
                ask.wait_for(state="hidden", timeout=T)
                go_row("Ask AI")()
                ask.wait_for(state="visible", timeout=T)
                page.locator(".desk-ask textarea, .desk-ask [role=textbox]").first.wait_for(state="visible", timeout=T)
                page.screenshot(path=str(SHOTS / "393-ask-back.png"))
            except Exception as exc:  # noqa: BLE001
                fails["D7 393 Go ▸ Ask AI after Capture shows Ask again"] = {
                    "error": str(exc)[:200], "shells": page.evaluate(SHELLS_JS)}

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
                self._one_on_one(page, 1440, fails)

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

                self._doors(page, 1440, fails)
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
                self._one_on_one(page, 393, fails)
                go = self._menu(page, "go")
                if go != PHONE_GO:
                    fails["D4 393 Go keeps the B21 shape without Settings"] = go
                self._no_old_names(page, "393 Go open", fails)
                page.screenshot(path=str(SHOTS / "393-go.png"))
                page.keyboard.press("Escape")
                mark = self._menu(page, "mark")
                if mark != MARK_ROWS:
                    fails["D4 393 the HoldSpeak menu is the setup rows"] = mark
                page.keyboard.press("Escape")
                self._doors(page, 393, fails)
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
