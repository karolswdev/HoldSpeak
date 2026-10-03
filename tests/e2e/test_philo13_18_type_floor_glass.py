"""PHILO-13-18 (C8) -- the 12 px floor, on the WHOLE Desk, as rendered.

The type-scale ruling (2026-09-21; UX-CANON "The 12 px floor"): readable text
is 12 px or more; only a nontext glyph goes below it, and only when a readable
word or an accessible control name says the same thing.

Through the real hub on an isolated HOME, seeded with the canvas week
(test_philo13_11_chair_glass._seed: projects, meetings, decisions, people, the
brief; a FILE destination), at 1440x900 (mouse) and 393x852 (touch), this rig
walks:

  * the Chair windows (Needs you, Brief, The week, Capture);
  * every Dock application the Dock draws (read from the live Dock, so a new
    AppIcon is walked without an edit here), and every wing of its window;
  * the main object windows: a meeting record, a person, the Room, a decision.

On every state it reads, with the shipping readers:

  S1 the floor: every visible text leaf of the WHOLE document, read by the
     HS-202-05 floor reader (test_hs202_05_first_use_type_floor._MEASURE, its
     glyph rule and glass_infra.FOLDED_WORD_JS unchanged). Zero under 12 px.
  S2 nothing clips, nothing overlaps: glass_infra._rendered_text_faults over
     every visible window and the screen bar (an ellipsis counts as clipped).

Shots of every state go to assets/story-18-shots/ under
HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise), with the
facts per width in ``type-floor-facts-<width>.json``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from .chair_windows import open_chair_window
from .glass_infra import (
    _api,
    _boot,
    _ensure_build,
    _normal_chair,
    _rendered_text_faults,
    _settle,
)
from .test_hs202_05_first_use_type_floor import _FAINT_JS, _MEASURE
from .test_philo13_11_chair_glass import _seed as _canvas_seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the type-floor glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(1500, method="thread")]

TOKEN = "philo13-18-floor"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-18-shots")
SIZES = {1440: 900, 393: 852}
ROOM = "Payments ledger cutover"
CHAIR = ("Needs you", "Brief", "The week", "Capture")
# What S2 reads: every visible window, and the screen bar.
READ_SCOPES = ".desk-window-shell, .desk-menubar"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


class TestTheTypeFloor:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        # The hub shows a folder under HOME as ~ (the canvas did the same). On
        # macOS tmp_path is /var/... -> /private/var/...; HOME is the resolved
        # path, so the FILE destination reads ~/Documents/... as it does for him.
        self.home = (tmp_path / "home").resolve()
        monkeypatch.setenv("HOME", str(self.home))
        _canvas_seed(self.home)
        self.base = base
        self.short = Path(tempfile.mkdtemp(prefix="p1318-", dir="/tmp"))
        (self.short / "Team updates").mkdir()
        try:
            yield
        finally:
            server.stop()
            shutil.rmtree(self.short, ignore_errors=True)

    # ── doors ──────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        page.emulate_media(reduced_motion="reduce")
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            TOKEN,
        )
        # The owner's FILE destination reads ~/Documents/HoldSpeak/Team updates
        # (channels.ts targetToken maps /Users/<name> to ~). A pytest HOME is a
        # 90-character /private/var path no reader of his would see; the
        # destination is a folder of the same length under /tmp (the canvas
        # rig's own HOME was under /tmp), removed by the fixture.
        _api(page, "POST", "/api/channels/destinations",
             {"name": "Team updates", "channel": "file", "folder": str(self.short / "Team updates")}, token=TOKEN)
        # the canvas rig's Workbench (harness/rig.py seed_hub): five items, two DONE
        self.wb = _api(page, "POST", "/api/workbenches",
                       {"name": "Ledger cutover bench", "description": "Agents on the cutover"},
                       token=TOKEN)["workbench"]["id"]
        for i, title in enumerate(["Draft rollback runbook", "Check reconciliation timings",
                                   "Write cutover comms", "Old sampling spike", "Rerun shard benchmark"]):
            item = _api(page, "POST", f"/api/workbenches/{self.wb}/items", {"title": title}, token=TOKEN)["item"]["id"]
            if i in (1, 2):
                _api(page, "PUT", f"/api/workbenches/{self.wb}/items/{item}", {"status": "done"}, token=TOKEN)
        self._fresh(page)
        return browser, page, errors

    def _fresh(self, page: Any) -> None:
        """A fresh Desk: no remembered windows, the Chair on the glass."""
        page.evaluate("localStorage.removeItem('hs.desk.workspace.v1')")
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        try:
            page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=10_000)
        except Exception:  # noqa: BLE001 -- the reads below name what is on the glass
            pass
        page.wait_for_timeout(800)
        _settle(page)

    def _stage(self, page: Any, key: str, scope: str | None = None) -> None:
        page.evaluate("localStorage.removeItem('hs.desk.workspace.v1')")
        page.evaluate(
            """([key, scope]) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key, scope}))""",
            [key, scope],
        )
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _front(page: Any) -> Any:
        return page.locator(".desk-window-shell.is-front").last

    @staticmethod
    def _wings(page: Any) -> list[str]:
        """The faces of the front window: its visible tabs, or its strip menu."""
        front = page.locator(".desk-window-shell.is-front").last
        if not front.count():
            return []
        tabs = front.locator(".desk-wings [role='tab']:visible")
        if tabs.count():
            return [t.strip() for t in tabs.all_inner_texts() if t.strip()]
        strip = front.locator(".desk-wings-menu:visible")
        if strip.count():
            strip.first.click()
            page.locator(".desk-menu-list").first.wait_for()
            names = [t.strip() for t in page.locator(".desk-menu-list [role='menuitemcheckbox']").all_inner_texts()
                     if t.strip()]
            # Close the menu with its own Button: at 393 an Escape here also
            # closed the window (observed 2026-10-02; reported, not this story's).
            strip.first.click()
            return names
        return []

    @staticmethod
    def _pick(page: Any, wing: str) -> None:
        """glass_infra.pick_wing, scoped to the front window (a back window's
        strip is in the DOM too)."""
        front = page.locator(".desk-window-shell.is-front").last
        tab = front.locator(".desk-wings [role='tab']:visible", has_text=wing)
        if tab.count():
            tab.first.click()
            return
        front.locator(".desk-wings-menu:visible").first.click()
        page.locator(".desk-menu-list [role='menuitemcheckbox']", has_text=wing).first.click()

    # ── the read ───────────────────────────────────────────────────────

    def _read(self, page: Any, width: int, state: str, facts: dict[str, Any]) -> None:
        page.wait_for_timeout(300)
        _settle(page)
        floor = page.evaluate(_MEASURE, self.faint)
        faults = _rendered_text_faults(page, READ_SCOPES, on_glass=True)
        # what makes a window scroll sideways (named in the facts when it does)
        sideways = page.evaluate("""() => [...document.querySelectorAll('.desk-window-shell')]
          .filter((w) => w.scrollWidth > w.clientWidth + 1).map((w) => {
            const r = w.getBoundingClientRect();
            const past = [...w.querySelectorAll('*')].filter((e) => e.getBoundingClientRect().right > r.right + 1)
              .slice(0, 6).map((e) => (e.className || e.tagName).toString().slice(0, 60)
                + '@' + Math.round(e.getBoundingClientRect().right));
            return {window: w.getAttribute('aria-label'), scroll: w.scrollWidth, client: w.clientWidth, past};
          })""")
        small = [{"sig": s["sig"], "px": s["px"], "text": s["text"], "path": s["path"]} for s in floor["small"]]
        facts["states"][state] = {
            "leaves": floor["leaves"],
            "front": page.evaluate(
                "() => { const f = [...document.querySelectorAll('.desk-window-shell.is-front')].pop();"
                " return f ? f.getAttribute('aria-label') : null; }"),
            "small": small,
            "clipped": faults["clipped"],
            "overlaps": faults["overlaps"],
            "ellipsis": faults["ellipsis"],
            "inset": faults["inset"],
            "sideways": sideways,
            "scopes": faults["scopes"],
        }
        page.screenshot(path=str(SHOTS / f"floor-{width}-{_slug(state)}.png"))

    _PLANT = """() => {
      const host = [...document.querySelectorAll('.desk-window-shell')].pop();
      const box = document.createElement('div');
      box.id = 'p1318-selftest';
      box.style.cssText = 'position:absolute;left:40px;top:60px;z-index:9;display:flex;gap:8px;background:#000';
      box.innerHTML = '<span id="p1318-small" style="font-size:10px">TEN PX WORD</span>'
        + '<div style="width:40px;overflow:hidden;white-space:nowrap;font-size:12px">CLIPPED BY A HIDDEN BOX</div>'
        + '<span style="font-size:12px">LEFT WORD</span><span style="font-size:12px;margin-left:-30px">OVER WORD</span>';
      host.appendChild(box);
    }"""

    def _selftest(self, page: Any) -> None:
        """A reader that cannot fail proves nothing: plant a 10 px word, a word a
        hidden box clips, and two words that overlap inside a window; all three
        must be read with the same readers and options the walk uses."""
        page.evaluate(self._PLANT)
        floor = page.evaluate(_MEASURE, self.faint)
        faults = _rendered_text_faults(page, READ_SCOPES, on_glass=True)
        page.evaluate("document.getElementById('p1318-selftest').remove()")
        assert any(s["text"] == "TEN PX WORD" for s in floor["small"]), "SELF-TEST: the floor reader missed a 10 px word"
        assert any(c["text"].startswith("CLIPPED BY") for c in faults["clipped"]), \
            f"SELF-TEST: the on-glass reader missed a hidden clip: {faults['clipped']}"
        assert any({"LEFT WORD", "OVER WORD"} <= set(o[:2]) for o in faults["overlaps"]), \
            f"SELF-TEST: the on-glass reader missed an overlap: {faults['overlaps']}"

    def _walk_wings(self, page: Any, width: int, state: str, facts: dict[str, Any]) -> None:
        self._read(page, width, state, facts)
        for wing in self._wings(page)[1:]:
            try:
                self._pick(page, wing)
            except Exception as exc:  # noqa: BLE001 -- a wing that cannot be picked is a fact
                where = page.evaluate("""() => ({front: [...document.querySelectorAll('.desk-window-shell.is-front')]
                    .map((w) => w.getAttribute('aria-label')), menus: document.querySelectorAll('.desk-wings-menu').length,
                    tabs: document.querySelectorAll('.desk-wings [role=tab]').length})""")
                facts["unreached"].append(f"{state} > {wing}: {where} {str(exc)[:200]}")
                page.keyboard.press("Escape")
                continue
            self._read(page, width, f"{state} > {wing}", facts)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_no_readable_text_under_12px(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {"width": width, "states": {}, "unreached": [], "dock": []}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self.faint = page.evaluate(_FAINT_JS)

                self._selftest(page)

                # 1. the Chair windows
                for name in CHAIR:
                    open_chair_window(page, name)
                    self._read(page, width, f"Chair {name}", facts)

                # 2. every Dock application (read from the live Dock), every wing
                labels = page.evaluate(
                    "() => [...document.querySelectorAll('.desk-dock .desk-dock-launch')]"
                    ".map((b) => b.getAttribute('aria-label') || b.textContent.trim())")
                apps = []
                for label in labels:
                    word = (label or "").split(",")[0].strip()
                    if word and word not in apps:
                        apps.append(word)
                facts["dock"] = apps
                assert len(apps) >= 6, f"the Dock drew {apps}; a Dock that did not draw proves nothing"
                for app in apps:
                    self._fresh(page)
                    launch = page.locator(f".desk-dock .desk-dock-launch[aria-label^='{app}']").first
                    if not launch.count() or not launch.is_visible():
                        facts["unreached"].append(f"Dock {app}: no visible launcher")
                        continue
                    self._press(page, launch, width)
                    page.wait_for_timeout(1500)
                    _settle(page)
                    self._walk_wings(page, width, f"Dock {app}", facts)

                # 3. the main object windows
                self._fresh(page)
                self._press(page, page.locator(".desk-dock .desk-dock-launch[aria-label^='Meetings']").first, width)
                page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
                row = page.locator(".meetings-stream-row-body").first
                row.wait_for()
                self._press(page, row, width)
                page.locator(".meetings-detail-head").wait_for()
                self._read(page, width, "Object meeting record", facts)

                self._stage(page, "open-people")
                page.locator(".desk-window-shell[aria-label='People']").wait_for()
                person = page.locator(".desk-window-shell[aria-label='People']").get_by_text("Priya Nair").first
                person.wait_for()
                self._press(page, person, width)
                page.wait_for_timeout(1000)
                self._walk_wings(page, width, "Object person Priya", facts)

                self._stage(page, "open-project-memory", "project:p-ledger")
                page.locator(f".desk-window-shell[aria-label='{ROOM}']").wait_for()
                self._walk_wings(page, width, "Object the Room", facts)

                page.evaluate("localStorage.removeItem('hs.desk.workspace.v1')")
                page.goto(f"{self.base}/?token={TOKEN}&open=workbench:{self.wb}", wait_until="load")
                _normal_chair(page)
                page.locator(".desk-workbench-window").first.wait_for()
                # an unbound bench opens on its configuration (WorkbenchWindow.tsx:1179)
                self._read(page, width, "Object workbench configuration", facts)
                collapse = page.locator(".desk-workbench-window .wb-config-collapse").first
                if collapse.count() and collapse.is_visible():
                    self._press(page, collapse, width)
                    page.locator(".desk-workbench-window .wb-config-strip").first.wait_for()
                    self._read(page, width, "Object workbench", facts)
                else:
                    facts["unreached"].append("Object workbench: no Collapse on the configuration")
                head = page.locator(".desk-workbench-window .wb-card-head").first
                self._press(page, head, width)
                self._read(page, width, "Object workbench item open", facts)

                self._fresh(page)
                if width <= 720:
                    open_chair_window(page, "Brief")
                brief = page.locator("[data-testid='arrival-brief-row']", has_text="Review decision").first
                if brief.count():
                    self._press(page, brief, width)
                    page.wait_for_timeout(1200)
                    self._read(page, width, "Object decision", facts)
                else:
                    facts["unreached"].append("Object decision: no `Review decision` brief row")

            finally:
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                browser.close()
                self._facts(width, facts)

        small = self._small(facts)
        clipped = [f"{k}: {c}" for k, v in facts["states"].items() for c in v["clipped"]]
        overlaps = [f"{k}: {o}" for k, v in facts["states"].items() for o in v["overlaps"]]
        sigs = facts["small_consumers"]
        print(f"TYPE FLOOR {width}: {facts['totals']}; dock {facts['dock']}; unreached {facts['unreached']}")
        if os.environ.get("PHILO13_18_VERBOSE"):
            for line in sorted(small) + clipped + overlaps:
                print("  ", line)
        assert not facts["errors"], facts["errors"]
        assert not facts["unreached"], facts["unreached"]
        assert not small, f"{len(small)} readable texts under 12 px at {width} ({len(sigs)} consumers):\n  " + \
            "\n  ".join(sorted(small)[:80])
        assert not clipped and not overlaps, (
            f"at {width}: {len(clipped)} clipped, {len(overlaps)} overlaps:\n  " + "\n  ".join((clipped + overlaps)[:80]))

    @staticmethod
    def _small(facts: dict[str, Any]) -> set[str]:
        return {f"{k}: {s['text']!r} {s['px']}px ({s['sig']})"
                for k, v in facts["states"].items() for s in v["small"]}

    @classmethod
    def _facts(cls, width: int, facts: dict[str, Any]) -> None:
        sigs = sorted({s["sig"] for v in facts["states"].values() for s in v["small"]})
        facts["totals"] = {
            "states": len(facts["states"]), "small": len(cls._small(facts)), "small_consumers": len(sigs),
            "clipped": sum(len(v["clipped"]) for v in facts["states"].values()),
            "overlaps": sum(len(v["overlaps"]) for v in facts["states"].values())}
        facts["small_consumers"] = sigs
        (SHOTS / f"type-floor-facts-{width}.json").write_text(json.dumps(facts, indent=1) + "\n")
