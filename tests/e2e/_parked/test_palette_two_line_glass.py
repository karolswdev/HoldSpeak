"""⌘K memory results, option B "Two-line hit" (canvas YDTpkaJqFs3hyrZ4g581Mx §3,
owner ratified 2026-10-05), AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch). Meetings and notes are saved by the real producers
(``db.meetings.save_meeting``, ``db.notes.upsert``); the real memory sweep
cuts and embeds them (``rebuild``) with a fixture engine that knows one
concept (going back: rollback, back, revert, fallback, undo). He types
``rollback``: the meeting that SAYS rollback is a KEYWORD hit with the word
marked; the note that says "go back to the old cluster" and the 1:1 that
says "fallback" are MEANING hits. Each MEMORY row is two lines: the title,
then the snippet, the FoundBy token and the day. The selected row's plate
reads at least 4.5:1, measured from the computed colours.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from .glass_infra import _assert_readable, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the palette glass needs Playwright")

TOKEN = "palette-two-line"
SHOTS = evidence_dir("palette-two-line-shots")
SIZES = {1440: 900, 393: 852}
QUERY = "rollback"
GOING_BACK = {"rollback", "back", "revert", "fallback", "undo"}
KEYWORD_ROW = "[id='desk-palette-option-memory:meeting:m-atlas']"
MEANING_ROW = "[id='desk-palette-option-memory:note:n-cutover']"
MEANING_MEETING_ROW = "[id='desk-palette-option-memory:meeting:m-marek']"


class GoingBackEngine:
    """The fixture engine: axis 0 is the concept "going back"; the other
    seven axes are a small hashed bag of the remaining words."""

    model_id = "going-back-fixture@8"
    dim = 8
    boundary = "local"
    revision_id = "going-back-fixture"
    assignment_head = "going-back-fixture"

    def _vector(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        for word in re.findall(r"[a-z0-9]+", str(text).lower()):
            if word in GOING_BACK:
                vector[0] += 1.0
            else:
                vector[1 + hashlib.sha256(word.encode()).digest()[0] % 7] += 0.15
        norm = float(np.linalg.norm(vector)) or 1.0
        return vector / norm

    def embed_documents(self, texts):
        return np.vstack([self._vector(t) for t in texts]) if texts else np.zeros((0, self.dim), np.float32)

    def embed_query(self, text):
        return self._vector(text)


def _luminance(rgb: list[float]) -> float:
    c = [x / 255 for x in rgb]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a: list[float], b: list[float]) -> float:
    x, y = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


class TestPaletteTwoLineHit:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        engine = GoingBackEngine()
        # The memory conductor resolves this engine on every tick (the one
        # assignment), so it never clears the engine the rig set.
        import holdspeak.memory.engine as memory_engine

        monkeypatch.setattr(memory_engine, "resolve_embedder", lambda *_a, **_k: engine)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import MeetingState, TranscriptSegment
        from holdspeak.memory.retain import rebuild

        db = get_database()
        self.atlas_at = datetime.now().replace(microsecond=0) - timedelta(days=4)
        db.meetings.save_meeting(MeetingState(
            id="m-atlas", started_at=self.atlas_at, ended_at=self.atlas_at + timedelta(minutes=30),
            title="Atlas weekly",
            segments=[TranscriptSegment(text="Priya takes the rollback plan; Marek reviews it on Thursday.",
                                        speaker="Priya", start_time=3.0, end_time=8.0)]))
        marek_at = self.atlas_at - timedelta(days=2)
        db.meetings.save_meeting(MeetingState(
            id="m-marek", started_at=marek_at, ended_at=marek_at + timedelta(minutes=25), title="1:1 Marek",
            segments=[TranscriptSegment(text="Marek asks who owns the fallback for Atlas.",
                                        speaker="Marek", start_time=2.0, end_time=6.0)]))
        # The artboard's local OBJECTS row: a note whose TITLE says rollback.
        db.notes.upsert(note_id="n-runbook", title="Rollback runbook draft", body_markdown="Steps for Thursday.")
        db.notes.upsert(note_id="n-cutover", title="Cutover after the freeze",
                        body_markdown="If the cutover fails, we go back to the old cluster in one step.")
        counts = rebuild(db, engine)
        assert counts["vectors"] >= 3, counts
        db.memory.set_embedder(engine)
        try:
            yield
        finally:
            server.stop()

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click(timeout=8_000)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_keyword_and_meaning_hits_draw_two_lines(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=2, has_touch=width < 720,
                                      reduced_motion="reduce")
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                _settle(page)
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill(QUERY)
                for sel in (KEYWORD_ROW, MEANING_ROW, MEANING_MEETING_ROW):
                    page.locator(sel).wait_for(timeout=8_000)
                # The pointer leaves the list: the selection is the top row, not a hover.
                if width >= 720:
                    page.mouse.move(2, 2)
                page.wait_for_timeout(300)

                facts = page.evaluate("""(sels) => sels.map((sel) => {
                  const row = document.querySelector(sel);
                  const label = row.querySelector('.desk-deck-label');
                  const snip = row.querySelector('.desk-deck-snippet');
                  const meta = row.querySelector('.desk-deck-hit-meta');
                  const range = document.createRange(); range.selectNodeContents(label.firstChild);
                  const title = range.getBoundingClientRect();
                  const s = snip.getBoundingClientRect(); const m = meta.getBoundingClientRect();
                  return { title: label.firstChild.textContent, snippet: snip.textContent,
                    marks: [...row.querySelectorAll('mark.desk-deck-mark')].map((x) => x.textContent),
                    by: [...row.querySelectorAll('.surface-foundby')].map((x) => x.textContent),
                    day: (row.querySelector('.desk-deck-day') || {}).textContent || '',
                    order: title.bottom <= s.top + 1 && s.bottom <= m.top + 1,
                    snippetFont: getComputedStyle(snip).fontFamily,
                    height: Math.round(row.getBoundingClientRect().height) }; })""",
                    [KEYWORD_ROW, MEANING_ROW, MEANING_MEETING_ROW])
                keyword, meaning, meaning_meeting = facts
                assert keyword["title"] == "Atlas weekly", keyword
                assert keyword["snippet"].endswith("Priya takes the rollback plan; Marek reviews it on Thursday."), keyword
                assert keyword["marks"] and all(m.lower() == "rollback" for m in keyword["marks"]), keyword
                assert keyword["by"] == ["KEYWORD"], keyword
                assert keyword["day"] == self.atlas_at.strftime("%m-%d"), keyword
                assert meaning["title"] == "Cutover after the freeze", meaning
                assert meaning["snippet"].startswith("If the cutover fails"), meaning   # the title is line one only
                assert "go back to the old cluster" in meaning["snippet"], meaning
                assert meaning["by"] == ["MEANING"] and meaning["marks"] == [], meaning
                assert re.fullmatch(r"\d{2}-\d{2}", meaning["day"]), meaning
                assert meaning_meeting["by"] == ["MEANING"], meaning_meeting
                assert not meaning_meeting["snippet"].startswith("1:1 Marek"), meaning_meeting
                # The local title match is the top row, as on the artboard.
                assert "Rollback runbook draft" in page.locator(".desk-deck-row.is-selected").inner_text()
                for row in facts:
                    assert row["order"], row            # title, then snippet, then FoundBy + day
                    assert row["height"] > 26, row      # two lines, not the 26 px ledger row
                    assert "Inter" in row["snippetFont"] or "sans" in row["snippetFont"], row

                # The selected row reads ≥ 4.5:1 (computed colours, as rendered).
                sel = page.evaluate("""() => { const r = document.querySelector('.desk-deck-row.is-selected');
                  const cs = getComputedStyle(r); const num = (c) => c.match(/[\\d.]+/g).slice(0, 3).map(Number);
                  return { bg: num(cs.backgroundColor), fg: num(cs.color), text: r.textContent }; }""")
                assert _contrast(sel["bg"], sel["fg"]) >= 4.5, sel

                # Everything in the shelf is whole and inside it; no side scroll.
                _assert_readable(page, "#desk-palette-listbox", f"palette {width}")
                in_shelf = page.evaluate("""(sel) => { const r = document.querySelector(sel).getBoundingClientRect();
                  const s = document.getElementById('desk-tool-shelf').getBoundingClientRect();
                  return r.left >= s.left - 1 && r.right <= s.right + 1
                    && document.documentElement.scrollWidth <= innerWidth; }""", KEYWORD_ROW)
                assert in_shelf
                page.screenshot(path=str(SHOTS / f"palette-two-line-{width}.png"))
                page.locator("#desk-tool-shelf").screenshot(path=str(SHOTS / f"palette-two-line-{width}-face.png"))

                # The selection walks onto a MEMORY row: its snippet and tokens take the plate's ink.
                page.locator("[aria-controls=desk-palette-listbox]").focus()
                for _ in range(20):
                    if page.locator(f"{KEYWORD_ROW}.is-selected").count():
                        break
                    page.keyboard.press("ArrowDown")
                assert page.locator(f"{KEYWORD_ROW}.is-selected").count() == 1, "the selection never reached the row"
                ink = page.evaluate("""(sel) => { const r = document.querySelector(sel);
                  const num = (c) => c.match(/[\\d.]+/g).slice(0, 3).map(Number);
                  return { bg: num(getComputedStyle(r).backgroundColor),
                           snip: num(getComputedStyle(r.querySelector('.desk-deck-snippet')).color) }; }""",
                    KEYWORD_ROW)
                assert _contrast(ink["bg"], ink["snip"]) >= 4.5, ink
                # Astra #1039: a PROJECTS row's `N OPEN` badge on the selected
                # plate. The rig seeds no Room, so a badge of the species
                # DeskToolShelf renders is placed in the selected row and the
                # shelf's own CSS is measured on it (its ground is its own
                # background when painted, else the plate under it).
                badge = page.evaluate("""(sel) => { const r = document.querySelector(sel);
                  const b = document.createElement('span'); b.className = 'desk-deck-badge'; b.textContent = '2 OPEN';
                  r.querySelector('.desk-deck-kind').before(b);
                  const num = (c) => c.match(/[\d.]+/g).map(Number);
                  const cs = getComputedStyle(b); const bg = num(cs.backgroundColor);
                  const out = { fg: num(cs.color).slice(0, 3), bg: bg.slice(0, 3), alpha: bg.length > 3 ? bg[3] : 1,
                                plate: num(getComputedStyle(r).backgroundColor).slice(0, 3) };
                  b.remove(); return out; }""", KEYWORD_ROW)
                assert badge["alpha"] in (0, 1), badge          # no wash: the plate, or an opaque chip
                badge_ground = badge["plate"] if badge["alpha"] == 0 else badge["bg"]
                assert _contrast(badge_ground, badge["fg"]) >= 4.5, badge
                page.locator("#desk-tool-shelf").screenshot(
                    path=str(SHOTS / f"palette-two-line-{width}-memory-selected.png"))
                # #882 review 2: a hovered row and a keyboard-focused row ink every
                # child on the plate (snippet, FoundBy, day), as rendered.
                inks = """(sel) => { const r = document.querySelector(sel);
                  const num = (c) => c.match(/[\\d.]+/g).slice(0, 3).map(Number);
                  const ink = (q) => num(getComputedStyle(r.querySelector(q)).color);
                  return { bg: num(getComputedStyle(r).backgroundColor), selected: r.classList.contains('is-selected'),
                           focus: r.matches(':focus-visible'), hover: r.matches(':hover'),
                           snip: ink('.desk-deck-snippet'), by: ink('.surface-foundby'), day: ink('.desk-deck-day') }; }"""

                def plate_inks(state: dict, where: str) -> None:
                    for child in ("snip", "by", "day"):
                        assert _contrast(state["bg"], state[child]) >= 4.5, (where, child, state)

                if width >= 720:
                    page.locator(MEANING_ROW).hover()
                    page.wait_for_timeout(400)
                    hovered = page.evaluate(inks, MEANING_ROW)
                    # The deck moves its selection to the row under the pointer
                    # (onPointerEnter), so a hovered row is also the selected one.
                    assert hovered["hover"], hovered
                    plate_inks(hovered, "hover")
                    page.mouse.move(2, 2)
                focused = None
                page.locator("[aria-controls=desk-palette-listbox]").focus()
                for _ in range(30):
                    page.keyboard.press("Tab")
                    state = page.evaluate("""() => { const a = document.activeElement;
                      return a && a.id && a.id.startsWith('desk-palette-option-memory:')
                        && !a.classList.contains('is-selected') && a.matches(':focus-visible') ? '#' + CSS.escape(a.id) : null; }""")
                    if state:
                        page.wait_for_timeout(400)   # the plate's colour transition settles
                        focused = page.evaluate(inks, state)
                        break
                assert focused and focused["focus"] and not focused["selected"], "no keyboard-focused unselected memory row"
                assert focused["bg"] != [0, 0, 0], focused   # the plate is painted (not transparent)
                plate_inks(focused, "focus-visible")
                page.locator("#desk-tool-shelf").screenshot(path=str(SHOTS / f"palette-two-line-{width}-focused.png"))
                assert not errors, errors
            finally:
                browser.close()
