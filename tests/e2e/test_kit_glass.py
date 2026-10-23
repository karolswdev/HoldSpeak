"""The kit (the library Button), rendered: an exact geometry relation jsdom
cannot read (moved whole from test_p16_kit_verb_glass.py, push 2 of the test
diet, 2026-10-12; the source is parked in tests/e2e/_parked/).

Phase 16 (the interior kit, §11 "Verb"; Astra r1 M6): the library Button
is ONE plate height, rendered.

A real hub on an isolated HOME. The Project's window (the Room window of the
canvas) holds verbs of every plated form the kit draws: ghost dense (Room,
History, Steward, Get Info), secondary dense (Open), the FilterBar tokens.
At 1440 each one's painted height is 32 px (the modern Button, dense or not).
At 393 each one owns a 44 px Button face. Shots to
`.tmp/evidence-shots/p16-kit-verb/`.

Also here (moved whole, push 2 of the test diet, 2026-10-12): two fences on a
file:// fixture of the token layer and the library Button's CSS, no hub.
The CSS directory is read from `HS202_05_CSS_DIR`, so a RED run can be taken
against `git show HEAD:web/src/styles/...` without touching the shared tree.

1. The Button owns a 44 x 44 px area at 393

The ruling (`docs/internal/checks/type-scale-ruling-2026-09-21.md` §3,
rule 4) is explicit that a rectangle measurement is not proof of
ownership: the area must answer `elementFromPoint`, and a real pointer
at the same point must fire that Button's handler and no other. This
fence therefore probes nine points per Button -- the center, four edge
midpoints and four corners of the 44 px area -- with both instruments.

Three controls, all in one run:
  * OWNED   -- every Button in a dense row and a dense column owns its
               nine points, under both instruments.
  * ADJACENT-- no two of those Buttons' areas intersect at all.
  * CLIPPED -- a Button inside a short `overflow: hidden` well does NOT
               own its area. The fence must SEE that, or it proves
               nothing about the others.

2. The disabled Button stays distinct after --text-faint moves

`--disabled-fg` IS `--text-faint` (`tokens.css:148`), so the type-scale
ruling's contrast fix (`#767e8d` -> `#8b93a3`) lightens every disabled
label toward live text. Muad'Dib's check named that risk: "Disabled
controls may lose distinction from muted text" (the ruling's check
table). The ruling's answer keeps the `disabled` attribute, the
`not-allowed` cursor and the flat treatment, and REFUSES the generic
skill's 0.38-0.5 opacity because it would cut the measured contrast.

This fence holds that answer. A disabled Button must differ from its
enabled twin in FOUR independent channels, and its own label must still
make 4.5:1 on its own ground.

The negative control is the point of the fence: a Button whose ONLY
difference from its twin is a gray label must FAIL here. Without that,
the fence would pass on a face that states "disabled" in gray alone.

Shots (HS202_05_EXPORT_SHOTS=1) land the enabled/disabled pair at 1440
and 393 in the story's assets.
"""
from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import open_project_drawer, _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the kit Verb glass needs Playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

TOKEN = "p16-kit-verb"
SHOTS = evidence_dir("p16-kit-verb")

MEASURE = """(win) => [...win.querySelectorAll('.btn')]
  // Screen-reader-only submit proxies have no painted plate (zero clip).
  // A merely short or narrow visible Button must still fail the census.
  .filter((b) => b.offsetParent && getComputedStyle(b).clip !== 'rect(0px, 0px, 0px, 0px)')
  .map((b) => {
    const r = b.getBoundingClientRect();
    const halo = getComputedStyle(b, '::after');
    return {
      word: b.textContent.trim().slice(0, 24),
      cls: b.className,
      h: Math.round(r.height * 10) / 10,
      halo: halo.content !== 'none' ? parseFloat(halo.height) || 0 : 0,
    };
  })"""


@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
def test_every_verb_is_one_plate_height(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            project = _api(page, "POST", "/api/projects", {
                "name": "Payments ledger cutover", "command_id": "p16-kit-verb",
            }, token=TOKEN)["project"]["id"]
            open_project_drawer(page, url, project, TOKEN)  # PHILO-17 U30: the parked drawer, by its key
            _normal_chair(page)
            window = page.locator(".drawer-window").last
            window.wait_for(timeout=20_000)
            window.get_by_role("button", name="History", exact=True).wait_for(timeout=20_000)
            _settle(page)
            verbs = window.evaluate(MEASURE)
            words = {v["word"] for v in verbs}
            expected = {"Icons", "List", "Room", "History", "Watch sources", "Get Info"}
            if width == 1440:
                expected.add("Open")
            assert expected <= words, verbs
            if width == 1440:
                heights = {v["h"] for v in verbs}
                assert heights == {32.0}, json.dumps(verbs, indent=2)
            else:
                heights = {v["h"] for v in verbs}
                assert heights == {44.0}, json.dumps(verbs, indent=2)
                assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")
                # Betterment shell S0 (#1257, UX-CANON A.11): a footer extra
                # that cannot run (Open, busy here) is withheld, and More is
                # not drawn when it would hold nothing (SurfaceFooter.tsx).
                assert not window.get_by_role("button", name="More actions", exact=True).count(), verbs
                assert window.is_visible()
            page.screenshot(path=str(SHOTS / f"kit-verb-{width}.png"))
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── the library Button on a file:// fixture (from test_hs202_05_*) ─────────

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CSS_DIR = REPO / "web/src/styles"
BUTTON_SHOTS = evidence_dir("button-glass")
NARROW = {"width": 393, "height": 852}

# The dense row (`.btn--sm`) and the standard column (`.btn`) both use the
# modern Button face. Short labels first: those are the Buttons whose painted
# face is narrower than the area they must own.
ROW = ["\u00d7", "\u21bb", "Open", "Record"]
COLUMN = ["Review meeting", "Run summary", "Import"]
DESKTOP_PAINTED = {"row": 32.0, "col": 32.0}
PHONE_PAINTED = {"row": 44.0, "col": 44.0}

# The nine points, as fractions of the half-width / half-height of the
# 44px area, inset by one device pixel so a point is never on the seam.
PROBES = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


def _css() -> str:
    """tokens.css + global.css, with the @import lines dropped.

    `@import` of a node_modules font package cannot resolve on file://,
    and a web font changes no box in this fixture: every assertion is
    about the rendered rectangles, which the fixture reads for itself.
    """
    css_dir = Path(os.environ.get("HS202_05_CSS_DIR", DEFAULT_CSS_DIR))
    tokens = (css_dir / "tokens.css").read_text(encoding="utf-8")
    glob = (css_dir / "global.css").read_text(encoding="utf-8")
    glob = re.sub(r'^@import\s+[^;]+;\s*$', "", glob, flags=re.MULTILINE)
    return tokens + "\n" + glob


def _fixture_html() -> str:
    row = "\n".join(
        f'<button type="button" class="btn btn--sm" id="row{i}">{label}</button>'
        for i, label in enumerate(ROW)
    )
    column = "\n".join(
        f'<button type="button" class="btn" id="col{i}">{label}</button>'
        for i, label in enumerate(COLUMN)
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{_css()}</style>
<style>
  body {{ margin: 0; padding: 16px; }}
  .fixture-row {{ display: flex; gap: var(--space-2); align-items: center; }}
  .fixture-col {{ display: grid; gap: var(--space-2); justify-items: start; }}
  /* NEGATIVE CONTROL A: the inner well is too short for the area to fit
     inside, while its 44px outer ancestor remains under the probes. The
     clipped points therefore reach an ANCESTOR, not the page body. */
  .fixture-clip-outer {{ width: 44px; height: 44px; }}
  .fixture-clip {{ width: 44px; height: 28px; overflow: hidden; }}
  /* NEGATIVE CONTROL B: this known-broken target has no pointer path, with
     nothing but the page behind it, so the BODY answers. The phone Button
     owns its full box now; keep this failure independent of its face. */
  .fixture-bare {{ margin-top: 40px; pointer-events: none; }}
  .fixture-bare .btn::after {{ content: none; }}
</style></head>
<body>
  <div class="fixture-row">{row}</div>
  <div class="fixture-col">{column}</div>
  <div class="fixture-clip-outer"><div class="fixture-clip"><button type="button" class="btn btn--sm" id="clipped">Clipped</button></div></div>
  <div class="fixture-bare"><button type="button" class="btn btn--sm" id="bare">No halo</button></div>
  <script>
    window.__fired = [];
    for (const b of document.querySelectorAll('button')) {{
      b.addEventListener('click', () => window.__fired.push(b.id));
    }}
  </script>
</body></html>"""


_GEOMETRY = """(id) => {
  const el = document.getElementById(id);
  const r = el.getBoundingClientRect();
  const hit = parseFloat(getComputedStyle(el).getPropertyValue('--desk-button-hit-size')) || 0;
  // The area is centred on the painted face. It is never narrower than
  // `hit`, and never wider than the painted face -- a neighbour in the
  // same row must keep every one of its own points.
  const halfW = Math.max(hit, r.width) / 2;
  const halfH = Math.max(hit, r.height) / 2;
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;
  return {
    id, painted: { w: r.width, h: r.height },
    area: { left: cx - halfW, right: cx + halfW, top: cy - halfH, bottom: cy + halfH,
            w: halfW * 2, h: halfH * 2 },
    cx, cy, halfW, halfH,
  };
}"""

# The ONE classifier both HS-202-05 hit readers use. Round 2 of Astra's
# counsel found the live reader calling a BODY hit "covered by a layer in
# front" -- a check that cannot fail proves nothing. A point belongs to
# the Button or it does not; everything else is a MISS, and the label
# says which kind so a layering fact is still distinguishable from a clip.
#
#   own            the Button, or something inside it, answered
#   miss:nothing   elementFromPoint found no element at all
#   miss:body      the body/root (or the Chair's screen, PHILO-14 A1) answered
#                  -- no window paints there, so the halo is absent, not covered
#   miss:ancestor  an ancestor answered -- it CLIPPED the halo
#   miss:sibling   a box in the SAME layer answered -- a neighbour owns it
#   covered        a box in a DIFFERENT layer, in front, answered
#
# Only `own` passes. Only `covered` is a ledger line. The rest fail.
OWNERSHIP_JS = """
  const HS202_LAYER = '.desk-surface-window, .desk-pullout, .desk-window,'
    + ' .desk-next-window, [role=dialog], [role=menu], .desk-dock, .desk-verbbar';
  const hs202Classify = (el, x, y) => {
    const top = document.elementFromPoint(x, y);
    if (!top) return { outcome: 'miss:nothing', owner: null };
    if (top === el || el.contains(top)) return { outcome: 'own', owner: null };
    const owner = top.id
      || (typeof top.className === 'string' && top.className.trim())
      || top.tagName;
    if (top === document.body || top === document.documentElement)
      return { outcome: 'miss:body', owner };
    // PHILO-14 A1: the Chair's screen of objects is the desk's glass, under
    // every window (z 0): a point on it is the body, not a layer in front.
    if (top.closest('.desk-screen') && !el.closest('.desk-screen'))
      return { outcome: 'miss:body', owner };
    if (top.contains(el)) return { outcome: 'miss:ancestor', owner };
    return { outcome: top.closest(HS202_LAYER) === el.closest(HS202_LAYER)
               ? 'miss:sibling' : 'covered', owner };
  };
"""

_OWNS = """([id, x, y]) => {
""" + OWNERSHIP_JS + """
  const el = document.getElementById(id);
  const seen = hs202Classify(el, x, y);
  return { owner: seen.owner, outcome: seen.outcome, ours: seen.outcome === 'own' };
}"""


def _points(g: dict) -> list[tuple[float, float, str]]:
    out = []
    for fx, fy in PROBES:
        x = g["cx"] + fx * (g["halfW"] - 1)
        y = g["cy"] + fy * (g["halfH"] - 1)
        name = {(0, 0): "center"}.get((fx, fy), f"({fx:+d},{fy:+d})")
        out.append((x, y, name))
    return out


def _overlap(a: dict, b: dict) -> bool:
    return not (
        a["right"] <= b["left"] + 0.01
        or b["right"] <= a["left"] + 0.01
        or a["bottom"] <= b["top"] + 0.01
        or b["bottom"] <= a["top"] + 0.01
    )


@pytest.mark.timeout(180, method="thread")
def test_button_owns_44px_at_393(tmp_path: Path) -> None:
    page_html = tmp_path / "button-hit-fixture.html"
    page_html.write_text(_fixture_html(), encoding="utf-8")

    ids = [f"row{i}" for i in range(len(ROW))] + [f"col{i}" for i in range(len(COLUMN))]
    failures: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport=NARROW)
        page.emulate_media(reduced_motion="reduce")
        page.goto(page_html.as_uri())
        page.wait_for_selector("#clipped")

        geo = {i: page.evaluate(_GEOMETRY, i) for i in ids}

        # ── the painted face follows the phone contract ────────────────────
        for i in ids:
            painted = geo[i]["painted"]["h"]
            expected = PHONE_PAINTED[i[:3]]
            if abs(painted - expected) >= 0.51:
                failures.append(
                    f"{i}: the painted height moved to {painted}px, not {expected}px; "
                    "the phone Button owns a 44px painted face"
                )

        # ── OWNED: elementFromPoint + a real pointer, nine points ────
        for i in ids:
            g = geo[i]
            if g["area"]["w"] < 43.99 or g["area"]["h"] < 43.99:
                failures.append(
                    f"{i}: area is {g['area']['w']:.1f}x{g['area']['h']:.1f}px, under 44x44"
                )
                continue
            for x, y, name in _points(g):
                seen = page.evaluate(_OWNS, [i, x, y])
                if not seen["ours"]:
                    failures.append(
                        f"{i}: elementFromPoint at {name} ({x:.1f},{y:.1f}) "
                        f"returned {seen['owner']!r} [{seen['outcome']}], not this Button"
                    )
                    continue
                page.evaluate("window.__fired = []")
                page.mouse.click(x, y)
                fired = page.evaluate("window.__fired")
                if fired != [i]:
                    failures.append(
                        f"{i}: a real pointer at {name} fired {fired!r}, not exactly [{i!r}]"
                    )

        # ── ADJACENT: no two areas may intersect ─────────────────────
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                ga, gb = geo[ids[a]], geo[ids[b]]
                if _overlap(ga["area"], gb["area"]):
                    failures.append(
                        f"{ids[a]} and {ids[b]} share points: "
                        f"{ga['area']} overlaps {gb['area']}"
                    )

        # ── the two negative controls: the fence must SEE a lost area ─
        controls = {}
        for control in ("clipped", "bare"):
            g = page.evaluate(_GEOMETRY, control)
            controls[control] = [
                page.evaluate(_OWNS, [control, x, y]) for x, y, _ in _points(g)
            ]
        if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
            # The debug overlay: one outline per owned area, drawn from the
            # SAME geometry the assertions probe.
            page.evaluate("""(boxes) => {
              for (const b of boxes) {
                const o = document.createElement('div');
                o.style.cssText = `position:absolute;left:${b.left}px;top:${b.top}px;`
                  + `width:${b.w}px;height:${b.h}px;outline:1px dashed #a86e4a;`
                  + `outline-offset:-1px;pointer-events:none;z-index:9`;
                document.body.appendChild(o);
              }
            }""", [dict(geo[i]["area"], **{"left": geo[i]["area"]["left"] + page.evaluate("scrollX"),
                                            "top": geo[i]["area"]["top"] + page.evaluate("scrollY")})
                   for i in ids])
            BUTTON_SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(BUTTON_SHOTS / "button-hit-areas-393.png"),
                            clip={"x": 0, "y": 0, "width": 393, "height": 260})

        lost_kinds: set[str] = set()
        for control, why in (
            ("clipped", "a Button clipped by an inner 28px overflow:hidden well"),
            ("bare", "a Button whose halo is suppressed, with only the page behind it"),
        ):
            seen = controls[control]
            outcomes = {o["outcome"] for o in seen}
            lost = outcomes - {"own"}
            lost_kinds |= lost
            if not lost:
                failures.append(
                    f"NEGATIVE CONTROL {control}: {why} appeared to own its whole "
                    "44px area, so this fence cannot see a lost hit area and proves "
                    "nothing about the others"
                )
            # THE round-2 contract. `covered` is a ledger line, not a
            # failure, so a reader that files a lost point there can never
            # go red. A control that loses its area must lose it as a
            # `miss:*`, never as coverage.
            if "covered" in lost:
                failures.append(
                    f"NEGATIVE CONTROL {control}: {why} filed a lost point as "
                    "'covered'; coverage is a ledger line, so this reader cannot fail"
                )

        # Both miss branches must be exercised by the pair, or one of them
        # is dead code that has never been shown to work.
        for branch in ("miss:body", "miss:ancestor"):
            if branch not in lost_kinds:
                failures.append(
                    f"NEGATIVE CONTROL: no control produced {branch!r} "
                    f"(saw {sorted(lost_kinds)}); that branch is unproven"
                )

        browser.close()

    assert not failures, "hit ownership at 393 is not proven:\n  " + "\n  ".join(failures)


@pytest.mark.timeout(180, method="thread")
def test_button_face_is_untouched_at_1440(tmp_path: Path) -> None:
    """The wide desk keeps the modern 32px Button face.

    The 44px Button is a narrow-desk rule (`@media (max-width: 420px)`), so
    at 1440 the painted face, its box and its neighbours stay at the modern
    32px contract. This is the other half of the proof: the phone target
    changes where the ruling says, and nowhere else.
    """
    page_html = tmp_path / "button-hit-fixture-wide.html"
    page_html.write_text(_fixture_html(), encoding="utf-8")
    ids = [f"row{i}" for i in range(len(ROW))] + [f"col{i}" for i in range(len(COLUMN))]
    failures: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.emulate_media(reduced_motion="reduce")
        page.goto(page_html.as_uri())
        page.wait_for_selector("#clipped")

        for i in ids:
            box = page.evaluate(
                """(id) => {
                     const el = document.getElementById(id);
                     const cs = getComputedStyle(el);
                     const after = getComputedStyle(el, '::after');
                     const number = (value) => {
                       const n = parseFloat(value);
                       return Number.isFinite(n) ? n : null;
                     };
                     return { h: el.getBoundingClientRect().height,
                              w: el.getBoundingClientRect().width,
                              marginTop: cs.marginTop, marginBottom: cs.marginBottom,
                              minInline: cs.minInlineSize,
                              border: number(cs.borderTopWidth),
                              after: {
                                top: number(after.top), right: number(after.right),
                                bottom: number(after.bottom), left: number(after.left),
                                pointerEvents: after.pointerEvents,
                              } };
                   }""",
                i,
            )
            expected = DESKTOP_PAINTED[i[:3]]
            if abs(box["h"] - expected) >= 0.51:
                failures.append(f"{i}: painted height {box['h']}px, not {expected}px at 1440")
            for side in ("marginTop", "marginBottom"):
                if box[side] not in ("0px", "auto"):
                    failures.append(
                        f"{i}: {side} is {box[side]} at 1440; the reserve is a narrow-desk rule"
                    )
            if box["minInline"] not in ("auto", "0px"):
                failures.append(
                    f"{i}: min-inline-size is {box['minInline']} at 1440; "
                    "the 44px width belongs to the narrow desk"
                )
            border = box["border"] or 0.0
            for side in ("top", "right", "bottom", "left"):
                inset = box["after"][side]
                if inset is None or abs(inset + border) >= 0.51:
                    failures.append(
                        f"{i}: the hit-face ::after {side} inset is {inset}px; "
                        f"expected the {border}px border edge only"
                    )
            if box["after"]["pointerEvents"] != "auto":
                failures.append(
                    f"{i}: the hit-face ::after pointer-events is "
                    f"{box['after']['pointerEvents']!r}, not 'auto'"
                )

        if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
            BUTTON_SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(BUTTON_SHOTS / "button-hit-areas-1440.png"),
                            clip={"x": 0, "y": 0, "width": 420, "height": 230})
        browser.close()

    assert not failures, (
        "the wide desk's Button changed:\n  " + "\n  ".join(failures)
    )


# ── 2. the disabled Button stays distinct ───────────────────────────────

WIDTHS = {1440: 900, 393: 852}

_PAIR = """
  <div class="pair">
    <button type="button" class="btn" id="on-btn">Run summary</button>
    <button type="button" class="btn" id="off-btn" disabled>Run summary</button>
  </div>
  <div class="pair">
    <button type="button" class="btn btn--primary" id="on-primary">Record</button>
    <button type="button" class="btn btn--primary" id="off-primary" disabled>Record</button>
  </div>
  <div class="pair">
    <button type="button" class="btn btn--sm" id="on-sm">Open</button>
    <button type="button" class="btn btn--sm" id="off-sm" disabled>Open</button>
  </div>
  <div class="pair gray-only">
    <button type="button" class="btn" id="on-gray">Export</button>
    <button type="button" class="btn" id="off-gray" disabled>Export</button>
  </div>
"""

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>%s</style>
<style>
  body { margin: 0; padding: 20px; background: var(--bg); }
  .pair { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
</style></head><body>%s</body></html>""" % (_css(), _PAIR)


_READ = """(id) => {
  const el = document.getElementById(id);
  const cs = getComputedStyle(el);
  const parse = (s) => {
    const m = /rgba?\\(([^)]+)\\)/.exec(s || "");
    if (!m) return null;
    const p = m[1].split(/[,\\s\\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const over = (fg, bg) => ({ r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a),
                              b: fg.b*fg.a + bg.b*(1-fg.a), a: 1 });
  // The ground the label is really on: the Button's own fill composited
  // over the page, exactly the way the census reads it.
  let bg = parse(cs.backgroundColor);
  const page = parse(getComputedStyle(document.body).backgroundColor) || {r:255,g:255,b:255,a:1};
  bg = !bg || bg.a <= 0 ? page : (bg.a < 1 ? over(bg, page) : bg);
  const fg = parse(cs.color);
  const eff = fg.a < 1 ? over(fg, bg) : fg;
  const l1 = lum(eff), l2 = lum(bg);
  return {
    disabledAttr: el.disabled,
    color: cs.color, background: cs.backgroundColor, borderColor: cs.borderTopColor,
    borderStyle: cs.borderTopStyle, boxShadow: cs.boxShadow, cursor: cs.cursor, opacity: cs.opacity,
    ratio: Math.round(((Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05)) * 100) / 100,
  };
}"""

# Independent material and pointer channels. Gray alone is never enough.
CHANNELS = ("background", "borderColor", "borderStyle", "boxShadow", "cursor")
REAL_PAIRS = [("on-btn", "off-btn"), ("on-primary", "off-primary"), ("on-sm", "off-sm")]


def _distinct(on: dict, off: dict) -> list[str]:
    return [c for c in CHANNELS if on[c] != off[c]]


@pytest.mark.parametrize("width", sorted(WIDTHS))
@pytest.mark.timeout(180, method="thread")
def test_disabled_button_stays_distinct(tmp_path: Path, width: int) -> None:
    page_html = tmp_path / "disabled-fixture.html"
    page_html.write_text(HTML, encoding="utf-8")
    failures: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": WIDTHS[width]})
        page.emulate_media(reduced_motion="reduce")
        page.goto(page_html.as_uri())
        page.wait_for_selector("#off-gray")

        for on_id, off_id in REAL_PAIRS:
            on, off = page.evaluate(_READ, on_id), page.evaluate(_READ, off_id)
            if not off["disabledAttr"]:
                failures.append(f"{off_id}: the semantic `disabled` attribute is gone")
            if off["cursor"] != "not-allowed":
                failures.append(f"{off_id}: cursor is {off['cursor']!r}, not 'not-allowed'")
            if off["boxShadow"] != "none":
                failures.append(f"{off_id}: the bevel survived ({off['boxShadow']}); "
                                "the disabled treatment is flat")
            if float(off["opacity"]) < 0.999:
                failures.append(f"{off_id}: opacity {off['opacity']} — the ruling refuses "
                                "an opacity dim; it cuts the measured contrast")
            changed = _distinct(on, off)
            if len(changed) < 3:
                failures.append(
                    f"{off_id}: only {changed or 'no'} channel(s) separate it from {on_id}; "
                    "gray alone never states the disabled position"
                )
            if off["ratio"] < 4.5:
                failures.append(
                    f"{off_id}: the disabled label reads {off['ratio']}:1 on its own ground, "
                    "under the ruling's 4.5:1"
                )

        # ── NEGATIVE CONTROL ─────────────────────────────────────────
        # Built by construction, not by a second stylesheet: every channel
        # but the label's gray is copied from the enabled twin, so this
        # pair IS the "gray alone" face the ruling refuses.
        page.evaluate("""() => {
          const on = document.getElementById('on-gray');
          const off = document.getElementById('off-gray');
          const cs = getComputedStyle(on);
          for (const prop of ['background-color','border-color','border-style','box-shadow','cursor','opacity'])
            off.style.setProperty(prop, cs.getPropertyValue(prop), 'important');
        }""")
        gray_on, gray_off = page.evaluate(_READ, "on-gray"), page.evaluate(_READ, "off-gray")
        if len(_distinct(gray_on, gray_off)) >= 3:
            failures.append(
                "NEGATIVE CONTROL: a Button whose only difference is its gray label "
                "passed the channel count, so this fence cannot see a gray-only "
                "disabled state and proves nothing about the others"
            )

        if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
            BUTTON_SHOTS.mkdir(parents=True, exist_ok=True)
            page.locator(".pair").first.screenshot(
                path=str(BUTTON_SHOTS / f"disabled-pair-{width}.png")
            )
        browser.close()

    assert not failures, (
        f"the disabled Button is not distinct at {width}:\n  " + "\n  ".join(failures)
    )
