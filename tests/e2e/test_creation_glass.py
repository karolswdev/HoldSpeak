"""Every New verb opens the thing it made, at once -- fenced AS RENDERED.

The fault (inventory 2026-10-03, A-apps row 33): Desk -> New Note / Knowledge /
Agent / Thread made the record and showed nothing. The window is drawn from
the store's object, and the store took the object only when a full desk read
ended. On a desk with a roadmap that read takes 2 to 5 s (`GET /api/roadmaps`),
so the press looked dead and the records piled up unseen.

Through the real hub on an isolated HOME, at 1440x900 and 393x852, on the
one desk (PHILO-17: the Floor is parked). The one thing this rig adds is the slow read: the
page delays its own `GET /api/roadmaps` by 4 s (the real hub still answers
it). Every record is made by the product's own verb.

* New Note / Knowledge / Agent / Thread (the Desk menu; Search at 393, PHILO-15 11):
  one press, one POST, and its window is on the glass, in front, inside
  1.5 s -- while the desk read is still in flight. The name typed at once
  is still there after the old read and the new read have both landed.
* New Decision asks the name first (PHILO-13-08): no record before the name;
  after the name its window opens inside 1.5 s.
* (Betterment Q10: the palette leg, New Knowledge, left with the verb.)
  (Betterment AG1: New Agent left the Desk menu.)

Was tests/e2e/test_new_verbs_open_glass.py. The press-to-window facts are also
web/src/desk/__tests__/creation.app.test.tsx; this file keeps what needs a
real browser: the name field has the keys, the new window is in front
(elementFromPoint), and Cmd-N twice (the test diet, push 2, 2026-10-12).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the New verbs glass needs Playwright")

TOKEN = "new-verbs-open"
SHOTS = evidence_dir("tests/e2e/shots/new-verbs-open")
SIZES = {1440: 900, 393: 852}
READ_DELAY_MS = 4000
OPENS_WITHIN_MS = 1500

# The slow desk read: the page waits 4 s before it sends GET /api/roadmaps.
SLOW_READ = """(() => {
  const real = window.fetch.bind(window);
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = ((init && init.method) || 'GET').toUpperCase();
    if (method === 'GET' && /\\/api\\/roadmaps(\\?|$)/.test(url))
      return new Promise((r) => setTimeout(r, %d)).then(() => real(input, init));
    return real(input, init);
  };
})()""" % READ_DELAY_MS

WINDOW_IDS = "() => [...document.querySelectorAll('.desk-window')].map((w) => w.id)"

# (menu label, the POST path that makes it, True when its window is an editor with a name field)
# Betterment Q4 ("One Ask window"): Desk ▸ New Thread opens the Ask window and
# makes no record; the thread is kept when its first question is answered
# (web/src/desk/__tests__/ask.app.test.tsx, "a thread opened anywhere opens in Ask").
# Betterment Q8 (one note): New Note opens the sticky; its keys go to the note
# body, not to a name field (tests/e2e/test_thought_glass.py proves the keys).
# Betterment Q10: New Knowledge left the New list (a collection is a drawer).
VERBS = [
    ("New Note", "/api/notes", False),
]


class TestEveryNewVerbOpensItsWindow:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str], list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720,
                                  reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        posts: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.on("request", lambda r: posts.append(r.url.split("?")[0].replace(self.base, ""))
                if r.method == "POST" else None)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        _api(page, "POST", "/api/notes",
             {"title": "Ledger cutover risks", "body_markdown": "rollback owner: Jordan", "tags": []}, token=TOKEN)
        page.add_init_script(SLOW_READ)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(READ_DELAY_MS + 1500)  # the first desk read lands
        _settle(page)
        del posts[:]
        return browser, page, errors, posts

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def _menu_verb(self, page: Any, width: int, label: str) -> None:
        if width < 720:
            # PHILO-15 11 (B21, owner ruling 2026-10-07): Go at 393 has no Desk ▸
            # (New ▸ is Thought / Meeting / Project / Person); every New verb is
            # one Search away: the Search tap, the words, a tap on the row.
            self._press(page, page.locator("button[aria-controls=desk-tool-shelf]"), width)
            box = page.locator("input[aria-controls=desk-palette-listbox]")
            box.wait_for()
            box.fill(label)
            item = page.locator("#desk-palette-listbox [role=option]", has_text=label).first
            item.wait_for()
            self._press(page, item, width)
            return
        self._press(page, page.locator(".desk-verbbar-item[data-menu-id='desk'] button"), width)
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first
        item.wait_for()
        self._press(page, item, width)

    @staticmethod
    def _new_window(page: Any, before: list[str], what: str) -> Any:
        """The one window that was not there before the press, inside 1.5 s, in front."""
        try:
            handle = page.wait_for_function(
                """(before) => {
                  const made = [...document.querySelectorAll('.desk-window')].filter((w) => !before.includes(w.id));
                  return made.length ? made[0].id : false;
                }""", arg=before, timeout=OPENS_WITHIN_MS, polling=50)
        except Exception as exc:  # the red on main: nothing opens while the read runs
            raise AssertionError(
                f"{what}: no window inside {OPENS_WITHIN_MS} ms; windows: {page.evaluate(WINDOW_IDS)}") from exc
        made = [w for w in page.evaluate(WINDOW_IDS) if w not in before]
        assert made == [handle.json_value()], (what, "one press, one window", made)
        win = page.locator(f"[id='{made[0]}']")
        front = page.evaluate(
            """(id) => {
              const w = document.getElementById(id); const r = w.getBoundingClientRect();
              const hit = (x, y) => { const e = document.elementFromPoint(x, y); return !!e && w.contains(e); };
              return hit(r.left + r.width / 2, r.top + 12) && hit(r.left + r.width / 2, r.top + r.height / 2);
            }""", made[0])
        assert front, (what, "its window is not in front", made[0])
        return win

    def _close(self, page: Any, win: Any, width: int) -> None:
        prefix = "Back from " if width < 720 else "Close "
        self._press(page, win.locator(f".desk-gadget-close[aria-label^='{prefix}']"), width)
        win.wait_for(state="detached")

    @pytest.mark.parametrize("width", list(SIZES))
    def test_new_drawer_starts_its_name_on_the_active_desk(self, width: int) -> None:
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser, page, errors, posts = self._page(pw, width)
            try:
                with page.expect_response(lambda response: response.url.endswith("/api/directories")
                                          and response.request.method == "POST") as created:
                    self._menu_verb(page, width, "New Drawer")
                assert created.value.ok, created.value.text()
                directory = created.value.json()["directory"]
                field = page.get_by_role("textbox", name="Drawer name", exact=True)
                expect(field).to_be_focused(timeout=5000)
                page.screenshot(path=str(SHOTS / f"new-drawer-before-name-{width}.png"))
                hit = field.evaluate("""el => {
                    const r = el.getBoundingClientRect();
                    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                    return {onField: hit === el, rect: r.toJSON(), hit: hit?.outerHTML.slice(0, 350)};
                }""")
                assert hit["onField"], hit
                assert field.evaluate("el => el.selectionStart === 0 && el.selectionEnd === el.value.length")
                page.keyboard.type("Build notes")
                field.press("Enter")
                expect(field).to_have_count(0)
                rows = _api(page, "GET", "/api/directories", token=TOKEN)["directories"]
                assert any(row["id"] == directory["id"] and row["name"] == "Build notes" for row in rows), rows
                assert posts.count("/api/directories") == 1, posts
                assert errors == [], errors
                page.screenshot(path=str(SHOTS / f"new-drawer-{width}.png"))
            finally:
                browser.close()

    @pytest.mark.parametrize("face", ["chair"])
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_new_verb_opens_its_window_at_once(self, width: int, face: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, posts = self._page(pw, width)
            try:
                proof: list[str] = []
                for label, path, editor in VERBS:
                    before, sent = page.evaluate(WINDOW_IDS), len(posts)
                    self._menu_verb(page, width, label)
                    win = self._new_window(page, before, f"{label} on the {face} at {width}")
                    assert posts[sent:].count(path) == 1, (label, "one press, one record", posts[sent:])
                    if editor:
                        # The name field has the keys at once; the name stays through both reads.
                        try:
                            page.wait_for_function(
                                "(id) => { const a = document.activeElement; return !!a && a.tagName === 'INPUT' && document.getElementById(id).contains(a); }",
                                arg=win.get_attribute("id"), timeout=OPENS_WITHIN_MS, polling=50)
                        except Exception as exc:
                            raise AssertionError(f"{label}: the name field does not have the keys") from exc
                        page.keyboard.type(" ledger")
                    page.screenshot(path=str(SHOTS / f"{label.replace(' ', '-').lower()}-{face}-{width}.png"))
                    page.wait_for_timeout(READ_DELAY_MS + 1500)  # the old read and the new read land
                    assert win.count() == 1 and win.is_visible(), (label, "the window closed under a desk read")
                    if editor:
                        value = win.locator("input").first.input_value()
                        assert value.endswith(" ledger"), (label, "the typed name was lost", value)
                    proof.append(f"{label}: one POST {path}, window {win.get_attribute('id')}")
                    self._close(page, win, width)

                # New Decision: the name first, no record before it (PHILO-13-08).
                before, sent = page.evaluate(WINDOW_IDS), len(posts)
                self._menu_verb(page, width, "New Decision")
                # The owner, 2026-10-25: New Decision opens a window of its own;
                # Create closes it and the record opens in the Decisions window.
                naming = page.locator("#surface-new-decision")
                naming.locator("[data-testid=palette-name]").wait_for(timeout=OPENS_WITHIN_MS)
                page.wait_for_timeout(800)
                assert "/api/decision-records/from-desk" not in posts[sent:], ("a decision was made before its name", posts[sent:])
                naming.locator("[data-testid=palette-name]").fill("Freeze the old ledger")
                page.keyboard.press("Enter")
                naming.wait_for(state="detached", timeout=OPENS_WITHIN_MS)
                win = self._new_window(page, before + ["surface-new-decision"], f"New Decision on the {face} at {width}")
                assert posts[sent:].count("/api/decision-records/from-desk") == 1, posts[sent:]
                page.screenshot(path=str(SHOTS / f"new-decision-{face}-{width}.png"))
                page.wait_for_timeout(READ_DELAY_MS + 1500)
                assert win.count() == 1 and win.is_visible(), "the decision window closed under a desk read"
                assert "Freeze the old ledger" in win.inner_text() or win.locator(
                    "input, textarea").evaluate_all("(els) => els.some((e) => e.value === 'Freeze the old ledger')")
                proof.append(f"New Decision: one POST /api/decisions after the name, window {win.get_attribute('id')}")
                if width < 720:
                    # The Decisions window's reader: on the phone the title-bar
                    # Back returns to the list first, then closes the window.
                    self._press(page, win.get_by_test_id("decision-reader-back"), width)
                    win.get_by_test_id("decisions-row").first.wait_for(timeout=OPENS_WITHIN_MS * 4)
                self._close(page, win, width)

                # Betterment Q10: the palette leg pressed New Knowledge, which
                # left the New list; the palette's Enter on a New verb is now
                # left untested in a browser (Search's Enter on a row is palette.app.test.tsx's).

                (SHOTS / f"proof-{face}-{width}.txt").write_text("\n".join(proof) + "\n")
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()

    # Astra's condition on #781: two quick presses made two records and one editor.
    @pytest.mark.parametrize("width", list(SIZES))
    def test_two_quick_presses_make_one_record(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        def count(page: Any, path: str, key: str) -> int:
            return len([r for r in _api(page, "GET", path, token=TOKEN)[key] if not r.get("deleted")])

        with sync_playwright() as pw:
            browser, page, errors, posts = self._page(pw, width)
            try:
                proof: list[str] = []
                legs = [("New Note", "/api/notes", "notes")]  # Betterment Q10: no New Knowledge
                for label, path, key in legs:
                    before, sent, kept = page.evaluate(WINDOW_IDS), len(posts), count(page, path, key)
                    if width >= 720 and label == "New Note":
                        # The key, twice, with no wait (⌘N from a body window).
                        page.locator(".chair-window--needs .desk-window-title").first.click()
                        page.keyboard.press("Meta+n")
                        page.keyboard.press("Meta+n")
                    else:
                        self._menu_verb(page, width, label)
                        self._menu_verb(page, width, label)
                    win = self._new_window(page, before, f"{label} twice at {width}")
                    page.wait_for_timeout(READ_DELAY_MS + 1500)  # every read lands
                    made = [w for w in page.evaluate(WINDOW_IDS) if w not in before]
                    assert made == [win.get_attribute("id")], (label, "two presses, more than one window", made)
                    assert posts[sent:].count(path) == 1, (label, "two presses, more than one POST", posts[sent:])
                    assert count(page, path, key) == kept + 1, (label, "two presses, more than one record on the hub")
                    self._new_window(page, before, f"{label} twice at {width}, after the reads")  # still in front
                    page.screenshot(path=str(SHOTS / f"twice-{label.replace(' ', '-').lower()}-{width}.png"))
                    proof.append(f"{label} twice: one POST {path}, one record, window {made[0]} in front")
                    self._close(page, win, width)
                    page.wait_for_timeout(READ_DELAY_MS + 1000)  # the NEW beat ends; the next leg starts clean
                (SHOTS / f"proof-twice-{width}.txt").write_text("\n".join(proof) + "\n")
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()
