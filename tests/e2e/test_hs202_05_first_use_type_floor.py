"""HS-202-05 — the 12px floor and 4.5:1 faint text, on the first-use screens.

The type-scale ruling (`docs/internal/checks/type-scale-ruling-2026-09-21.md`)
sets two measured rules this rig holds, on the six screens the owner's
first-use path crosses, at 1440 and 393:

  M7 (the floor)    readable text computes at 12px or more. A nontext
                    glyph may go below it, and only when a readable word
                    or an accessible control name carries the meaning.
  M8 (the contrast) text painted in `--text-faint` makes 4.5:1 on the
                    ground it is really on.

The reading logic is lifted from `scripts/surface_census_measure.js`
(the M7 and M8 blocks) so this rig and the census agree on what a text
leaf, a composited ground and a ratio are. It is NOT the census: the
census's broad counts stay diagnostics (the ruling, §4), and this rig
gates only the two rules above, only on `--text-faint`, only here.

A screen is never "clean because it never opened": every screen asserts
its own loaded selector before it is read.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _normal_chair,
    _settle,
    seed_meeting_engines,
)
from .test_hs201_one_thing_glass import _quiet_concierge

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-05-shots"
TOKEN = "hs202-05-type-floor"
MEETING_ID = "m-hs202-05"
MEETING_TITLE = "First recorded meeting"
WIDTHS = {1440: 900, 393: 852}
FLOOR = 12.0

# The floor ledger: every consumer on a first-use screen whose readable
# text still computes under 12px at HS-202-05's close. Each line is a raw
# CSS size that does NOT read a type token, so the ruling's token change
# could not move it; each belongs to a face this lane does not own (the
# wings, the Dock, the menus and the first-use control markup are
# HS-202-03's; the labels are HS-202-04's). The fence FAILS on anything
# outside this set, so no new sub-floor text can land, and it PRINTS what
# has healed so the set only shrinks. Filled by HS202_05_DUMP.
FLOOR_LEDGER: dict[str, str] = {
    "393|arrival|.arrival-meeting-badge@10px": "OFF",
    "393|arrival|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "393|arrival|.gadget-transport-word@9px": "Talk",
    "393|arrival|h3@10px": "BRIEF",
    "393|meetings-ledger|.arrival-meeting-badge@10px": "OFF",
    "393|meetings-ledger|.desk-wing.is-on@10px": "Outcomes",
    "393|meetings-ledger|.desk-wing@10px": "Review",
    "393|meetings-ledger|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "393|meetings-ledger|.gadget-transport-word@9px": "Talk",
    "393|meetings-ledger|.meetings-stream-fact@10px": "SEP 15",
    "393|meetings-ledger|.meetings-stream-no-transcript@10px": "NO TRANSCRIPT",
    "393|meetings-ledger|.surface-footer-receipt-line@10px": "1 RECORD",
    "393|meetings-ledger|h3@10px": "BRIEF",
    "393|meetings-record|.arrival-meeting-badge@10px": "OFF",
    "393|meetings-record|.desk-wing.is-on@10px": "Outcomes",
    "393|meetings-record|.desk-wing@10px": "Review",
    "393|meetings-record|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "393|meetings-record|.gadget-transport-word@9px": "Talk",
    "393|meetings-record|.meetings-stream-fact@10px": "SEP 15",
    "393|meetings-record|.surface-footer-receipt-line@10px": "1 RECORD",
    "393|meetings-record|.surface-token-axis@11px": "SUMMARY",
    "393|meetings-record|.surface-token@11px": "OFF",
    "393|meetings-record|.surface-well-head@10px": "TRANSCRIPT",
    "393|meetings-record|h3@10px": "BRIEF",
    "393|models|.arrival-meeting-badge@10px": "OFF",
    "393|models|.concierge-checked-at@11px": "CHECKED 3:41 AM",
    "393|models|.concierge-hardware-token@11px": "THIS MAC · M‑SERIES · 36 GB",
    "393|models|.concierge-receipt@11px": "NO ENGINE · SET UP NOTHING",
    "393|models|.concierge-section-label@11px": "FOUND",
    "393|models|.desk-dock-label@10px": "Models",
    "393|models|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "393|models|.gadget-transport-word@9px": "Talk",
    "393|models|h3@10px": "THOUGHTS 1",
    "393|settings|.arrival-meeting-badge@10px": "OFF",
    "393|settings|.desk-wing.is-on@10px": "Settings",
    "393|settings|.desk-wing@10px": "Guide",
    "393|settings|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "393|settings|.gadget-transport-word@9px": "Talk",
    "393|settings|.prefs-receipt@10px": "WRITTEN 10:04",
    "393|settings|.surface-state-chip@10px": "NO DEFAULT",
    "393|settings|.surface-token@10px": "2 ENGINES",
    "393|settings|h3@10px": "THOUGHTS 1",
    "393|thought|.arrival-meeting-badge@10px": "OFF",
    "393|thought|.desk-dock-label@10px": "Thought",
    "393|thought|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "393|thought|.gadget-transport-word@9px": "Talk",
    "393|thought|.surface-footer-receipt-line@10px": "KEPT",
    "393|thought|.surface-token@10px": "NO ENGINE YET",
    "393|thought|.thought-note-ask-label@11px": "ONE QUESTION",
    "393|thought|.thought-note-reads@10px": "READS · NOTHING",
    "393|thought|h3@10px": "THOUGHTS 1",
    "1440|arrival|.arrival-meeting-badge@10px": "OFF",
    "1440|arrival|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "1440|arrival|.gadget-transport-word@9px": "Talk",
    "1440|arrival|h3@10px": "BRIEF",
    "1440|arrival|kbd@10px": "⌘K",
    "1440|meetings-ledger|.arrival-meeting-badge@10px": "OFF",
    "1440|meetings-ledger|.desk-wing.is-on@10px": "Outcomes",
    "1440|meetings-ledger|.desk-wing@10px": "Review",
    "1440|meetings-ledger|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "1440|meetings-ledger|.gadget-transport-word@9px": "Talk",
    "1440|meetings-ledger|.meetings-stream-fact@10px": "SEP 15",
    "1440|meetings-ledger|.meetings-stream-no-transcript@10px": "NO TRANSCRIPT",
    "1440|meetings-ledger|.surface-footer-receipt-line@10px": "1 RECORD",
    "1440|meetings-ledger|h3@10px": "BRIEF",
    "1440|meetings-ledger|kbd@10px": "⌘K",
    "1440|meetings-record|.arrival-meeting-badge@10px": "OFF",
    "1440|meetings-record|.desk-wing.is-on@10px": "Outcomes",
    "1440|meetings-record|.desk-wing@10px": "Review",
    "1440|meetings-record|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "1440|meetings-record|.gadget-transport-word@9px": "Talk",
    "1440|meetings-record|.meetings-stream-compact-facts@10px": "SEP 15 · OFF",
    "1440|meetings-record|.meetings-stream-fact@10px": "SEP 15",
    "1440|meetings-record|.surface-footer-receipt-line@10px": "1 RECORD",
    "1440|meetings-record|.surface-token-axis@11px": "SUMMARY",
    "1440|meetings-record|.surface-token@11px": "OFF",
    "1440|meetings-record|.surface-well-head@10px": "TRANSCRIPT",
    "1440|meetings-record|h3@10px": "BRIEF",
    "1440|meetings-record|kbd@10px": "⌘K",
    "1440|models|.arrival-meeting-badge@10px": "OFF",
    "1440|models|.concierge-checked-at@11px": "CHECKED 3:41 AM",
    "1440|models|.concierge-hardware-token@11px": "THIS MAC · M‑SERIES · 36 GB",
    "1440|models|.concierge-receipt@11px": "NO ENGINE · SET UP NOTHING",
    "1440|models|.concierge-section-label@11px": "FOUND",
    "1440|models|.desk-dock-label@10px": "Models",
    "1440|models|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "1440|models|.gadget-transport-word@9px": "Talk",
    "1440|models|h3@10px": "THOUGHTS 1",
    "1440|models|kbd@10px": "⌘K",
    "1440|settings|.arrival-meeting-badge@10px": "OFF",
    "1440|settings|.desk-wing.is-on@10px": "Settings",
    "1440|settings|.desk-wing@10px": "Guide",
    "1440|settings|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "1440|settings|.gadget-transport-word@9px": "Talk",
    "1440|settings|.prefs-receipt@10px": "WRITTEN 10:04",
    "1440|settings|.surface-state-chip@10px": "NO DEFAULT",
    "1440|settings|.surface-token@10px": "2 ENGINES",
    "1440|settings|h3@10px": "THOUGHTS 1",
    "1440|settings|kbd@10px": "⌘K",
    "1440|thought|.arrival-meeting-badge@10px": "OFF",
    "1440|thought|.desk-dock-label@10px": "Thought",
    "1440|thought|.gadget-chip.gadget-chip-egress@10px": "THIS DEVICE",
    "1440|thought|.gadget-transport-word@9px": "Talk",
    "1440|thought|.surface-footer-receipt-line@10px": "KEPT",
    "1440|thought|.surface-token@10px": "NO ENGINE YET",
    "1440|thought|.thought-note-ask-label@11px": "ONE QUESTION",
    "1440|thought|.thought-note-reads@10px": "READS · NOTHING",
    "1440|thought|h3@10px": "THOUGHTS 1",
    "1440|thought|kbd@10px": "⌘K",
}

# `--text-faint` after the ruling. The rig reads the token from the page
# so it can never drift from design-tokens.json.
_FAINT_JS = "getComputedStyle(document.documentElement).getPropertyValue('--text-faint').trim()"

# The M7/M8 reader. Kept deliberately close to the census's own code so a
# number here means the same thing a number in census.json means.
_MEASURE = """(faintHex) => {
  const parse = (s) => {
    const m = /rgba?\\(([^)]+)\\)/.exec(s || "");
    if (!m) return null;
    const p = m[1].split(/[,\\s\\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const hex = (h) => {
    h = h.replace('#','');
    return { r: parseInt(h.slice(0,2),16), g: parseInt(h.slice(2,4),16),
             b: parseInt(h.slice(4,6),16), a: 1 };
  };
  const same = (a, b) => a && b && a.r === b.r && a.g === b.g && a.b === b.b;
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(c.r) + 0.7152*f(c.g) + 0.0722*f(c.b);
  };
  const over = (fg, bg) => ({ r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a),
                              b: fg.b*fg.a + bg.b*(1-fg.a), a: 1 });
  const path = (el) => {
    const bits = [];
    for (let n = el; n && n.nodeType === 1 && bits.length < 6; n = n.parentElement) {
      let b = n.tagName.toLowerCase();
      if (n.id) { bits.unshift(b + '#' + n.id); break; }
      if (n.className && typeof n.className === 'string')
        b += '.' + n.className.trim().split(/\\s+/).slice(0, 2).join('.');
      bits.unshift(b);
    }
    return bits.join(' > ');
  };
  const ownText = (el) => [...el.childNodes]
    .filter((n) => n.nodeType === 3).map((n) => n.textContent).join('').trim();
  const visible = (el) => {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' &&
           s.display !== 'none' && Number(s.opacity) > 0;
  };

  const leaves = [...document.querySelectorAll('body *')]
    .filter((el) => ownText(el) && visible(el));

  // A nontext glyph is exempt from the floor, and only when a readable
  // word or an accessible name says the same thing. A word or a number
  // is never a glyph.
  const GLYPH = /^[^\\p{L}\\p{N}]+$/u;
  const named = (el) => {
    const host = el.closest('[aria-label],[title],button,a,[role=button]');
    if (!host) return null;
    const label = host.getAttribute('aria-label') || host.getAttribute('title') || '';
    const text = (host.textContent || '').trim();
    const word = (label || text).replace(/[^\\p{L}\\p{N}]/gu, '');
    return word ? (label || text) : null;
  };

  const faint = hex(faintHex);
  const small = [], contrast = [];
  for (const el of leaves) {
    const cs = getComputedStyle(el);
    const text = ownText(el);
    const size = parseFloat(cs.fontSize);

    if (size < 12) {
      const glyph = GLYPH.test(text);
      const alt = glyph ? named(el) : null;
      if (!glyph || !alt) {
        // The signature is the consumer, not the instance: the element's
        // own classes (or its tag) plus the computed size. A face that
        // repeats one styled span twenty times is ONE ledger line.
        const cls = (el.className && typeof el.className === 'string')
          ? '.' + el.className.trim().split(/\s+/).join('.')
          : el.tagName.toLowerCase();
        small.push({ sig: cls + '@' + Math.round(size*100)/100 + 'px',
                     path: path(el), px: Math.round(size*100)/100,
                     text: text.slice(0, 40), glyph, alt });
      }
    }

    const fg = parse(cs.color);
    if (!fg || !same(fg, faint)) continue;   // only --text-faint is gated here
    let painted = false, bg = null;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const bi = getComputedStyle(n).backgroundImage;
      if (bi && bi !== 'none') { painted = true; break; }
      const bc = parse(getComputedStyle(n).backgroundColor);
      if (bc && bc.a > 0) { bg = bg ? over(bg, bc) : bc; if (bg.a >= 0.999) break; }
    }
    if (painted) continue;                    // the census skips these too
    const page = parse(getComputedStyle(document.body).backgroundColor) || {r:255,g:255,b:255,a:1};
    bg = !bg ? page : (bg.a < 1 ? over(bg, page) : bg);
    const eff = fg.a < 1 ? over(fg, bg) : fg;
    const l1 = lum(eff), l2 = lum(bg);
    const ratio = (Math.max(l1,l2)+0.05) / (Math.min(l1,l2)+0.05);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    if (ratio < need)
      contrast.push({ path: path(el), ratio: Math.round(ratio*100)/100, need,
                      px: Math.round(size*10)/10, text: text.slice(0, 40),
                      bg: `rgb(${Math.round(bg.r)}, ${Math.round(bg.g)}, ${Math.round(bg.b)})` });
  }
  return { leaves: leaves.length, small, contrast };
}"""


def _seed(db) -> None:
    from holdspeak.meeting_session.models import MeetingState

    db.meetings.save_meeting(
        MeetingState(
            id=MEETING_ID,
            started_at=datetime(2026, 9, 15, 10, 0),
            title=MEETING_TITLE,
            capture_status="finalized",
        )
    )


def _stage(page, base: str, key: str) -> None:
    """Open a Desk surface by its staged key -- the door every settings and
    Concierge rig uses (web/src/desk/shell.ts:12,52)."""
    page.evaluate(
        """([key]) => {
             localStorage.removeItem('hs.desk.workspace.v1');
             sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key}));
           }""",
        [key],
    )
    page.goto(base + "/?token=" + TOKEN, wait_until="load")
    _normal_chair(page)


def _screens(page, base: str):
    """Yield (name, loaded-locator) for each first-use screen, in order.

    The doors are the ones the story-01 fence and the HS-170/HS-201 rigs
    already walk. Models is the Concierge, NOT `/profiles`: both
    `ModelLibraryCore` rigs skip at module level (HS-170-03 parked that
    face), so `/profiles` would measure a screen the owner cannot reach.
    """

    def desk():
        # localStorage is only readable once the origin is loaded, so the
        # clear always follows a navigation, never precedes the first one.
        page.goto(base + "/?token=" + TOKEN, wait_until="load")
        page.evaluate("localStorage.removeItem('hs.desk.workspace.v1')")
        page.goto(base + "/?token=" + TOKEN, wait_until="load")
        _normal_chair(page)
        page.get_by_test_id("arrival-display").wait_for(state="visible", timeout=20_000)
        page.get_by_test_id("arrival-capture-bar").wait_for(state="visible", timeout=20_000)
        _settle(page)

    desk()
    yield "arrival", page.get_by_test_id("arrival-display")

    _stage(page, base, "review-meetings")
    page.locator(".meetings-head-verbs").wait_for(state="visible", timeout=20_000)
    _settle(page)
    yield "meetings-ledger", page.locator(".meetings-head-verbs")

    row = page.locator("[data-testid='meeting-row-" + MEETING_ID + "']")
    row.wait_for(state="visible", timeout=20_000)
    row.locator(".meetings-stream-row-body").click()
    page.locator(".meetings-detail-head").wait_for(state="visible", timeout=20_000)
    _settle(page)
    yield "meetings-record", page.locator(".meetings-detail-head")

    desk()
    thought = page.get_by_test_id("arrival-develop-thought")
    thought.wait_for(state="visible", timeout=20_000)
    thought.click()
    page.wait_for_function(
        """() => !!document.querySelector(
             '.speak-face textarea, [id^="editor:note:"] .cm-content,'
             + ' .thought-note-document [aria-label="Note body"]')""",
        timeout=20_000,
    )
    _settle(page)
    yield "thought", page.locator(
        '.speak-face, [id^="editor:note:"], .thought-note-document'
    ).first

    _stage(page, base, "open-concierge")
    page.get_by_test_id("concierge-root").wait_for(state="visible", timeout=20_000)
    _settle(page)
    yield "models", page.get_by_test_id("concierge-root")

    _stage(page, base, "configure-settings")
    page.locator(".prefs-hub-headline").wait_for(state="visible", timeout=20_000)
    _settle(page)
    yield "settings", page.locator(".prefs-hub-headline")


@pytest.mark.parametrize("width", sorted(WIDTHS))
def test_first_use_screens_hold_the_floor_and_the_contrast(
    tmp_path: Path, monkeypatch, width: int
) -> None:
    from playwright.sync_api import sync_playwright

    from holdspeak.db import get_database
    from holdspeak.kernel.runtime import _configure

    _quiet_concierge(monkeypatch)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    seed_meeting_engines()
    _seed(db)

    report: dict[str, dict] = {}
    floor_seen: dict[str, dict] = {}
    failures: list[str] = []
    errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": WIDTHS[width]})
        page.set_default_timeout(15_000)
        page.emulate_media(reduced_motion="reduce")
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        faint = None
        for name, loaded in _screens(page, base):
            assert loaded.count() >= 1 and loaded.first.is_visible(), (
                f"{name} never loaded at {width}; a screen that did not open "
                "proves nothing"
            )
            override = os.environ.get("HS202_05_FAINT_OVERRIDE")
            if override:
                # The BEFORE leg: paint the pre-ruling faint gray onto the
                # real screen and read the same M8 logic against it.
                page.evaluate(
                    "v => document.documentElement.style.setProperty('--text-faint', v)",
                    override,
                )
                faint = override
            elif faint is None:
                faint = page.evaluate(_FAINT_JS)
                assert faint.lower() == "#8b93a3", (
                    f"--text-faint is {faint!r}; the ruling's value is #8b93a3"
                )
            # The 44px reserve grows layout at 393. Check EVERY screen for
            # horizontal overflow, not only the last one the loop leaves
            # on the glass.
            if not page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ):
                failures.append(
                    f"{name}@{width} scrolls sideways "
                    + str(page.evaluate(
                        "[document.documentElement.scrollWidth, window.innerWidth]"))
                )
            seen = page.evaluate(_MEASURE, faint)
            report[f"{name}@{width}"] = {
                "leaves": seen["leaves"],
                "under_floor": len(seen["small"]),
                "faint_contrast_fails": len(seen["contrast"]),
            }
            for s in seen["small"]:
                sig = f"{width}|{name}|{s['sig']}"
                floor_seen.setdefault(sig, s)
                if sig not in FLOOR_LEDGER:
                    failures.append(
                        f"{name}@{width} M7 NEW {s['px']}px < {FLOOR}: {s['text']!r} "
                        f"({s['path']})"
                    )
            for c in seen["contrast"]:
                failures.append(
                    f"{name}@{width} M8 {c['ratio']}:1 < {c['need']} at {c['px']}px on "
                    f"{c['bg']}: {c['text']!r} ({c['path']})"
                )

        if os.environ.get("HS202_05_DUMP"):
            Path(os.environ["HS202_05_DUMP"] + f".{width}.json").write_text(
                json.dumps({k: {"px": v["px"], "text": v["text"], "path": v["path"]}
                            for k, v in sorted(floor_seen.items())}, indent=1) + "\n",
                encoding="utf-8")

        if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
            SHOTS.mkdir(parents=True, exist_ok=True)
            (SHOTS / f"first-use-type-floor-{width}.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        recorded = {k for k in FLOOR_LEDGER if k.startswith(f"{width}|")}
        healed = sorted(recorded - set(floor_seen))
        for sig in healed:
            print(f"HEALED {width}: {sig} — {FLOOR_LEDGER[sig]}")
        print(f"FLOOR LEDGER {width}: {len(floor_seen)} of {len(recorded)} "
              f"recorded consumers still under {FLOOR}px; {len(healed)} healed")
        _assert_clean(page, errors)
        browser.close()

    assert not failures, (
        f"the first-use screens do not hold the ruling at {width} "
        f"({len(failures)} observations):\n  " + "\n  ".join(failures[:60])
    )
