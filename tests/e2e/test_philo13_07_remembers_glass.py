"""PHILO-13-07 (B2) -- the Desk remembers, fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch: every press a tap). The canvas week is minted by the real producers
(test_philo13_06_open_glass._seed). One job, then a real page reload:

  * the decision window (palette `decision:d-freeze`), then iconified
    (1440: its Iconify gadget; 393 has no Iconify gadget, so there the
    decision window is only checked to be in the saved document);
  * the Room on `Payments ledger cutover`: Updates -> Draft -> typed words,
    NOT saved; at 1440 the Room window is moved first;
  * People on Priya (her commitment row), the 1:1s tab, an agenda item
    typed and NOT added;
  * the Intelligence window, opened and CLOSED (close means gone).

After the reload, the fence reads the glass: the Room is back in the editor
with the typed words (no PUT was sent by restore), People is back on Priya
on 1:1s with the typed item, the moved Room is where it was (1440), the
iconified decision is still iconified (1440: on its Dock chip, not drawn),
and Intelligence is not back. The red-on-main proof is the vitest fence
(web/src/desk/__tests__/deskRemembers.philo1307.test.tsx); this glass was
not run against main.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_06_open_glass import COMMITMENT, _seed
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the remembers glass needs Playwright")

TOKEN = "philo13-06-open"  # _seed's own _http speaks this token
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-07-shots")
SIZES = {1440: 900, 393: 852}
ROOM_WORDS = "Dry run passed Tuesday; EU shard backup plan due Friday; Priya owns the rollback runbook."
AGENDA = "Ask Priya about the EU shard backup plan"
DECISION = "Freeze the old ledger on Nov 5"

WINDOWS_JS = r"""() => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
  .filter((w) => { const r = w.getBoundingClientRect(); const cs = getComputedStyle(w);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; })
  .map((w) => { const r = w.getBoundingClientRect();
    return {id: w.id, title: (w.getAttribute('aria-label') || '').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]}; })"""


class _Rig:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.ids = _seed(tmp_path / "home", base)
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=15_000)
        page.wait_for_timeout(1500)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click(timeout=8_000)

    def _palette(self, page: Any, query: str, option: str, width: int) -> None:
        self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
        page.locator("[aria-controls=desk-palette-listbox]").fill(query)
        opt = page.locator(f"[id='desk-palette-option-{option}']")
        try:
            opt.wait_for(timeout=8_000)
        except Exception:
            ids = page.evaluate("() => [...document.querySelectorAll('[id^=desk-palette-option-]')].map(o => o.id)")
            raise AssertionError(f"no palette option {option!r}; options: {ids}")
        self._press(page, opt, width)

    def _chair_window(self, page: Any, width: int, name: str) -> None:
        """At 393, Go > <name>; at 1440 the window stands."""
        shell = page.locator(f".desk-window-shell[aria-label='{name}']")
        if width > 720 or (shell.count() and shell.first.is_visible() and
                           shell.first.evaluate("e => e.classList.contains('is-front')")):
            return
        # PHILO-14 A1 (#939): the Chair's windows are Go's first rows at 393.
        for loc in (
            page.locator(".desk-verbbar-item[data-menu-id='go'] button"),
            page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"),
        ):
            loc.first.wait_for()
            self._press(page, loc.first, width)
            page.wait_for_timeout(250)
        shell.wait_for()
        _settle(page)

    def _windows(self, page: Any) -> list[dict[str, Any]]:
        return page.evaluate(WINDOWS_JS)

    def _workspace(self, page: Any) -> dict[str, Any]:
        return json.loads(page.evaluate("() => localStorage.getItem('hs.desk.workspace.v1') || '{}'"))



class TestTheDeskRemembers(_Rig):
    @pytest.mark.parametrize("width", list(SIZES))
    def test_windows_places_and_drafts_return_after_a_reload(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            puts: list[str] = []
            page.on("request", lambda r: puts.append(f"{r.method} {r.url}")
                    if r.method in ("PUT", "POST") and ("/api/updates/" in r.url or "/agenda" in r.url) else None)
            try:
                # 3. People on Priya, the 1:1s tab, an agenda item typed, not added
                self._chair_window(page, width, "Needs you")
                commitment = page.locator(".desk-window-shell[aria-label='Needs you'] .surface-ledger-line",
                                          has_text=COMMITMENT).first
                self._press(page, commitment, width)
                people = page.locator(".desk-window[aria-label='People'], .desk-window-shell[aria-label='People']").first
                people.get_by_role("tab", name="1:1s").wait_for()
                self._press(page, people.get_by_role("tab", name="1:1s"), width)
                pad = people.get_by_role("textbox", name="Agenda item")
                pad.wait_for()
                self._press(page, pad, width)
                page.keyboard.type(AGENDA)
                page.wait_for_timeout(400)

                # 4. Intelligence: opened, then closed (close means gone)
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Intelligence']"), width)
                close = page.locator(".desk-gadget-close[aria-label='Close Intelligence']")
                close.wait_for()
                page.wait_for_timeout(500)
                self._press(page, close, width)
                close.wait_for(state="detached")

                # 1. the decision window
                self._palette(page, "freeze", "decision:d-freeze", width)
                page.locator(f".desk-pullout[aria-label='{DECISION}']").wait_for()
                _settle(page)

                # 2. the Room: Updates -> Draft -> typed words, not saved
                self._palette(page, "Payments", "project.open.p-ledger", width)
                room = page.locator("#surface-project-memory")
                self._press(page, room.get_by_test_id("updates-verb"), width)
                self._press(page, room.get_by_test_id("update-verb-draft-deterministic"), width)
                editor = room.locator("[contenteditable=true]").first
                editor.wait_for()
                self._press(page, editor, width)
                page.keyboard.press("Control+End")
                page.keyboard.type(" " + ROOM_WORDS)
                page.wait_for_timeout(400)
                if width >= 720:
                    head = room.locator(".desk-window-head, .desk-window-title").first
                    box = head.bounding_box()
                    assert box
                    page.mouse.move(box["x"] + 40, box["y"] + box["height"] / 2)
                    page.mouse.down()
                    page.mouse.move(box["x"] + 160, box["y"] + box["height"] / 2 + 60, steps=8)
                    page.mouse.up()
                    page.wait_for_timeout(500)
                room_rect = next(w["rect"] for w in self._windows(page) if w["id"] == "surface-project-memory")

                # 5. at 1440 the decision is iconified (393 has no Iconify gadget)
                if width >= 720:
                    deck = page.locator(f".desk-pullout[aria-label='{DECISION}']")
                    self._press(page, deck.locator(f"[aria-label='Iconify {DECISION}']"), width)
                    page.wait_for_timeout(900)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"B2-01-before-reload-{width}.png"))
                before = {"windows": self._windows(page), "workspace": self._workspace(page),
                          "room_rect": room_rect, "writes": list(puts)}

                # ── the reload ──
                page.reload(wait_until="load")
                _normal_chair(page)
                room = page.locator("#surface-project-memory")
                editor = room.locator("[contenteditable=true]").first
                editor.wait_for(timeout=20_000)
                page.wait_for_function(
                    "(w) => [...document.querySelectorAll('#surface-project-memory [contenteditable=true]')].some(e => e.innerText.includes(w))",
                    arg=ROOM_WORDS, timeout=15_000)
                people = page.locator(".desk-window[aria-label='People'], .desk-window-shell[aria-label='People']").first
                people.get_by_role("textbox", name="Agenda item").wait_for(timeout=20_000)
                page.wait_for_timeout(1200)
                _settle(page)
                after_windows = self._windows(page)
                page.screenshot(path=str(SHOTS / f"B2-02-after-reload-{width}.png"))
                tab = people.locator(".people-lenses [role=tab][aria-selected=true]").inner_text().strip()
                agenda = people.get_by_role("textbox", name="Agenda item").input_value()
                person = people.locator(".people-detail-head strong").inner_text().strip()
                room_after = next((w["rect"] for w in after_windows if w["id"] == "surface-project-memory"), None)
                titles = [w["title"] for w in after_windows]
                decision_drawn = any(DECISION in t for t in titles)
                chips = page.evaluate("() => [...document.querySelectorAll('.desk-dock-chip button')].map(b => (b.getAttribute('aria-label') || b.textContent || '').trim())")
                proof = {"width": width, "before": before, "after_windows": after_windows,
                         "people": {"person": person, "tab": tab, "agenda": agenda},
                         "room_rect_after": room_after, "dock_chips": chips,
                         "writes_after_reload": [p for p in puts if p not in before["writes"]]}
                (SHOTS / f"B2-proof-{width}.json").write_text(json.dumps(proof, indent=1) + "\n")

                assert person == "Priya Nair", proof
                assert tab == "1:1s", proof
                assert agenda == AGENDA, proof
                assert not proof["writes_after_reload"], "restore sent a write"
                assert not before["writes"], "nothing was saved or sent before the reload"
                assert not any("Intelligence" in t for t in titles), "the closed Intelligence window came back"
                if width >= 720:
                    # PHILO-14 A1 (#939, Astra's P2): saved positions are restored;
                    # unsaved ones are placed again (C1-1 seat / cascade). The
                    # moved Room comes back exactly; the untouched People window
                    # was never saved and lands whole in the band, hiding no
                    # other window's title bar.
                    assert room_after == room_rect, (room_rect, room_after)
                    people_id = next(w["id"] for w in after_windows if w["title"] == "People")
                    assert people_id not in before["workspace"]["panel"]["rects"], before["workspace"]["panel"]
                    pr = next(w["rect"] for w in after_windows if w["id"] == people_id)
                    assert pr[0] >= 0 and pr[1] >= 0 and pr[0] + pr[2] <= 1440 and pr[1] + pr[3] <= 900, pr
                    for other in after_windows:
                        if other["id"] == people_id:
                            continue
                        x, y, w, h = other["rect"]
                        hides = pr[0] <= x and pr[0] + pr[2] >= x + w and pr[1] <= y and pr[1] + pr[3] >= y + 44
                        assert not hides, (people_id, pr, other)
                    assert not decision_drawn, "the iconified decision came back drawn"
                    assert "pullout:decision:d-freeze" in self._workspace(page)["panel"]["min"]
                    assert any(DECISION in c for c in chips), chips
                else:
                    assert "decision:d-freeze" in self._workspace(page)["windows"]["pullouts"]
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_closed_window_stays_gone_after_a_reload(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._palette(page, "freeze", "decision:d-freeze", width)
                card = page.locator(f".desk-pullout[aria-label='{DECISION}']")
                card.wait_for()
                page.wait_for_timeout(600)
                page.reload(wait_until="load")
                _normal_chair(page)
                card.wait_for(timeout=20_000)  # it came back
                page.wait_for_timeout(800)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"B2-03-came-back-{width}.png"))
                self._press(page, card.locator(f"[aria-label='Close {DECISION}']"), width)
                card.wait_for(state="detached")
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".desk-window-shell[aria-label='Needs you']").first.wait_for(state="attached")
                page.wait_for_timeout(2500)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"B2-04-closed-stays-gone-{width}.png"))
                titles = [w["title"] for w in self._windows(page)]
                (SHOTS / f"B2-closed-{width}.json").write_text(json.dumps(
                    {"windows": titles, "workspace": self._workspace(page)}, indent=1) + "\n")
                assert not any(DECISION in t for t in titles), titles
                assert "decision:d-freeze" not in self._workspace(page)["windows"]["pullouts"]
                assert not errors, errors
            finally:
                browser.close()


class TestSliceTwoReturns(_Rig):
    """B2 slice two, on the same rig: the meeting window with its SEND form
    pick and its unfinished Decide title, the Delivery board, the Trust
    window and Schedule recording with its typed title all come back after a
    reload; the closed ones stay gone. Red on the slice-one head 22287ab1
    (vitest fence deskRemembers2.philo1307.test.tsx; this glass was not run
    against it)."""

    DECIDE = "Freeze the old ledger after the dry run"
    SCHEDULE = "Ledger cutover dry run"

    def _present(self, page: Any) -> dict[str, Any]:
        return page.evaluate("""() => ({
          meeting: !!document.querySelector(".desk-pullout [data-testid=meeting-decide-well]"),
          form: (document.querySelector(".desk-pullout [data-testid=doc-forms] select") || {}).value || null,
          decide: (document.querySelector(".desk-pullout [aria-label='Decision title']") || {}).value ?? null,
          board: !!document.querySelector(".desk-dlv-board"),
          trust: !!document.querySelector("#trust"),
          schedule: (document.querySelector("[id='schedule:__create__'] input[aria-label='Title']") || {}).value ?? null,
        })""")

    def _front(self, page: Any, width: int, title: str) -> None:
        """The window's Dock chip brings it forward (it returned on its
        remembered plane, so a later window may cover it)."""
        chip = page.locator(f".desk-dock-chip button[aria-label^='Focus {title}']").first
        if chip.count():
            self._press(page, chip, width)
        else:
            page.locator(f"[aria-label='{title}'] .desk-pullout-head, #trust .desk-pullout-head").first.click(position={"x": 200, "y": 10}, force=False)
        page.wait_for_timeout(500)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_families_and_drafts_return_and_closed_stay_gone(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            writes: list[str] = []
            page.on("request", lambda r: writes.append(f"{r.method} {r.url}")
                    if r.method in ("PUT", "POST", "DELETE") and "/api/" in r.url
                    and not any(p in r.url for p in ("/preview", "/subscriptions", "/peek", "/brief/generate")) else None)
            try:
                # 1. the meeting window: Digest, then Decide -> a title, not saved
                page.goto(f"{self.base}/?token={TOKEN}&open=meeting:m-standup", wait_until="load")
                _normal_chair(page)
                well = page.locator(".desk-pullout [data-testid=meeting-decide-well]").first
                well.wait_for(timeout=20_000)
                page.locator(".desk-pullout [data-testid=doc-forms] select").first.select_option("meeting_digest")
                self._press(page, well.get_by_role("button", name="Decide", exact=True), width)
                well.get_by_role("textbox", name="Decision title").fill(self.DECIDE)
                # 2. the Delivery board from the Dock
                self._press(page, page.get_by_role("button", name="Delivery", exact=True).first, width)
                page.locator(".desk-dlv-board").wait_for()
                # 3. the Trust window from the privacy badge
                self._press(page, page.locator("[aria-label^='Privacy and trust']").first, width)
                page.locator("#trust").wait_for()
                # 4. Schedule recording from Capture, a typed title, not saved
                if width <= 720:  # Capture opens from the Speak AppIcon at 393 (R2)
                    self._press(page, page.locator(".desk-dock [aria-label^='Speak']").first, width)
                    page.locator(".desk-window-shell.chair-window[aria-label='Capture']").wait_for()
                self._press(page, page.get_by_test_id("arrival-schedule").first, width)
                title = page.locator("[id='schedule:__create__'] input[aria-label='Title']")
                title.wait_for()
                title.fill(self.SCHEDULE)
                page.wait_for_timeout(500)
                _settle(page)
                before = self._present(page)
                page.screenshot(path=str(SHOTS / f"B2-05-slice2-before-reload-{width}.png"))
                typed_writes = list(writes)

                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".desk-pullout [data-testid=meeting-decide-well]").first.wait_for(state="attached", timeout=20_000)
                page.locator("[id='schedule:__create__']").wait_for(state="attached", timeout=20_000)
                page.wait_for_timeout(1500)
                _settle(page)
                after = self._present(page)
                page.screenshot(path=str(SHOTS / f"B2-06-slice2-after-reload-{width}.png"))

                # close two of them, reload: they stay gone. Each comes to the
                # front first (it returned on its remembered plane, so a later
                # window may cover it): through the frame's own JS focus seam
                # is not a gesture he has, so the fence uses the Window menu.
                self._front(page, width, "Data boundaries")
                self._press(page, page.locator("#trust [aria-label^='Close']").first, width)
                page.locator("#trust").wait_for(state="detached")
                self._front(page, width, "Delivery")
                self._press(page, page.locator(".desk-dlv-board [aria-label^='Close']").first, width)
                page.locator(".desk-dlv-board").wait_for(state="detached")
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator("[id='schedule:__create__']").wait_for(state="attached", timeout=20_000)
                page.wait_for_timeout(1500)
                _settle(page)
                closed = self._present(page)
                page.screenshot(path=str(SHOTS / f"B2-07-slice2-closed-stay-gone-{width}.png"))
                proof = {"width": width, "before": before, "after": after, "after_close": closed,
                         "writes_before_reload": typed_writes,
                         "writes_after": [w for w in writes if w not in typed_writes]}
                (SHOTS / f"B2-slice2-proof-{width}.json").write_text(json.dumps(proof, indent=1) + "\n")

                assert after == {"meeting": True, "form": "meeting_digest", "decide": self.DECIDE,
                                 "board": True, "trust": True, "schedule": self.SCHEDULE}, proof
                assert closed["board"] is False and closed["trust"] is False, proof
                assert closed["schedule"] == self.SCHEDULE and closed["decide"] == self.DECIDE, proof
                assert not proof["writes_before_reload"] and not proof["writes_after"], "a draft was saved or sent"
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_an_emptied_room_draft_stays_empty_until_save(self, width: int) -> None:
        """Astra's B2 condition: the Room body cleared to nothing stays empty
        and UNSAVED after a reload and after a close/reopen; Save clears the
        draft. Red on 22287ab1 (vitest fence; the old saved text came back)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            puts: list[str] = []
            page.on("request", lambda r: puts.append(r.method) if r.method == "PUT" and "/api/updates/" in r.url else None)
            try:
                self._palette(page, "Payments", "project.open.p-ledger", width)
                room = page.locator("#surface-project-memory")
                self._press(page, room.get_by_test_id("updates-verb"), width)
                self._press(page, room.get_by_test_id("update-verb-draft-deterministic"), width)
                editor = room.locator("[contenteditable=true]").first
                editor.wait_for()
                self._press(page, editor, width)
                page.keyboard.press("ControlOrMeta+a")
                page.keyboard.press("Backspace")
                page.wait_for_timeout(400)
                empty_js = "e => !!e.querySelector('.cm-placeholder') && [...e.querySelectorAll('.cm-line')].every(l => !(l.textContent || '').replace(l.querySelector('.cm-placeholder')?.textContent || '', '').trim())"
                assert editor.evaluate(empty_js), "the body did not clear"

                def state() -> dict[str, Any]:
                    r = page.locator("#surface-project-memory")
                    r.locator("[contenteditable=true]").first.wait_for(timeout=20_000)
                    page.wait_for_timeout(800)
                    ed = r.locator("[contenteditable=true]").first
                    return {"body": "" if ed.evaluate(empty_js) else ed.inner_text().strip()[:80],
                            "unsaved": "UNSAVED" in r.inner_text().upper(),
                            "drafts": {k: v for k, v in self._workspace(page).get("drafts", {}).items() if k.startswith("room/")}}

                page.reload(wait_until="load")
                _normal_chair(page)
                after_reload = state()
                page.screenshot(path=str(SHOTS / f"B2-08-empty-draft-after-reload-{width}.png"))
                # close the Room and reopen it by its normal opener
                self._press(page, page.locator("#surface-project-memory [aria-label^='Close']").first, width)
                page.locator("#surface-project-memory").wait_for(state="detached")
                self._palette(page, "Payments", "project.open.p-ledger", width)
                after_reopen = state()
                page.screenshot(path=str(SHOTS / f"B2-09-empty-draft-after-reopen-{width}.png"))
                self._press(page, page.locator("#surface-project-memory").get_by_role("button", name="Save", exact=True), width)
                page.wait_for_timeout(1500)
                saved = {"puts": list(puts), "drafts": {k: v for k, v in self._workspace(page).get("drafts", {}).items() if k.startswith("room/")},
                         "unsaved": "UNSAVED" in page.locator("#surface-project-memory").inner_text().upper()}
                page.screenshot(path=str(SHOTS / f"B2-10-empty-draft-saved-{width}.png"))
                proof = {"width": width, "after_reload": after_reload, "after_reopen": after_reopen, "after_save": saved}
                (SHOTS / f"B2-empty-draft-{width}.json").write_text(json.dumps(proof, indent=1) + "\n")
                for leg in (after_reload, after_reopen):
                    assert leg["body"] == "" and leg["unsaved"], proof
                    assert list(leg["drafts"].values()) == [""], proof
                assert saved["puts"] == ["PUT"], proof
                assert saved["drafts"] == {} and not saved["unsaved"], proof
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_j5_the_thought_window_returns_with_its_words(self, width: int) -> None:
        """J5's return leg (grounding faces-jobs.md:113, J5-04): he writes a
        thought, it autosaves, he reloads: the Thought window is back with his
        words, 0 gestures (was 3 to find it again)."""
        from playwright.sync_api import sync_playwright

        words = "Shard backup plan: ask Priya before Friday"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                if width <= 720:  # Capture opens from the Speak AppIcon at 393 (R2)
                    self._press(page, page.locator(".desk-dock [aria-label^='Speak']").first, width)
                    page.locator(".desk-window-shell.chair-window[aria-label='Capture']").wait_for()
                self._press(page, page.get_by_test_id("arrival-develop-thought").first, width)
                field = page.locator(".desk-window[aria-label^='Thought'] .thought-note-body .cm-content, .desk-window .thought-note-body .cm-content").first
                field.wait_for(timeout=15_000)
                self._press(page, field, width)
                page.keyboard.type(words)
                page.wait_for_timeout(2500)  # the writer's 450 ms autosave lands
                page.reload(wait_until="load")
                _normal_chair(page)
                back = page.locator(".thought-note-body .cm-content", has_text=words).first
                back.wait_for(state="attached", timeout=20_000)
                page.wait_for_timeout(800)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"B2-11-j5-thought-after-reload-{width}.png"))
                (SHOTS / f"B2-j5-{width}.json").write_text(json.dumps(
                    {"width": width, "regestures_after_reload": 0, "thought_back": True,
                     "windows": [w["title"] for w in self._windows(page)]}, indent=1) + "\n")
                assert not errors, errors
            finally:
                browser.close()
