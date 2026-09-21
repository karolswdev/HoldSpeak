"""HS-202-05 — the library Button owns a 44 x 44 px area at 393.

The ruling (`docs/internal/checks/type-scale-ruling-2026-09-21.md` §3,
rule 4) is explicit that a rectangle measurement is not proof of
ownership: the area must answer `elementFromPoint`, and a real pointer
at the same point must fire that Button's handler and no other. This
fence therefore probes nine points per Button -- the center, four edge
midpoints and four corners of the 44 px area -- with both instruments.

The fixture is isolated on purpose. It is the token layer plus the
library Button's own CSS from `web/src/styles/`, nothing else: no hub,
no bundle, no route. That keeps the fence about the Button contract and
keeps it honest when a sibling lane changes a face.

The CSS directory is read from `HS202_05_CSS_DIR` so the RED run can be
taken against `git show HEAD:web/src/styles/...` without touching the
shared tree.

Three controls, all in one run:
  * OWNED   -- every Button in a dense row and a dense column owns its
               nine points, under both instruments.
  * ADJACENT-- no two of those Buttons' areas intersect at all.
  * CLIPPED -- a Button inside a short `overflow: hidden` well does NOT
               own its area. The fence must SEE that, or it proves
               nothing about the others.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180, method="thread")]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CSS_DIR = REPO / "web/src/styles"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-05-shots"
NARROW = {"width": 393, "height": 852}

# The dense row (`.btn--sm`, 24px painted) and the standard column
# (`.btn`, 28px painted). Short labels first: those are the Buttons whose
# painted face is narrower than the area they must own.
ROW = ["\u00d7", "\u21bb", "Open", "Record"]
COLUMN = ["Review meeting", "Run summary", "Import"]
PAINTED = {"row": 24.0, "col": 28.0}

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
  /* NEGATIVE CONTROL A: a well too short for the area to fit inside, so
     an ANCESTOR answers the clipped points. */
  .fixture-clip {{ height: 24px; overflow: hidden; }}
  /* NEGATIVE CONTROL B: the halo suppressed outright, with nothing but
     the page behind it, so the BODY answers. Round 2 of Astra's counsel:
     the live reader filed that as "covered" and reported no miss. */
  .fixture-bare {{ margin-top: 40px; }}
  .fixture-bare .btn::after {{ content: none; }}
</style></head>
<body>
  <div class="fixture-row">{row}</div>
  <div class="fixture-col">{column}</div>
  <div class="fixture-clip"><button type="button" class="btn btn--sm" id="clipped">Clipped</button></div>
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
#   miss:body      the body/root answered -- nothing is painted there, so
#                  the halo is absent, not covered
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

        # ── the painted face never grew in height ────────────────────
        for i in ids:
            painted = geo[i]["painted"]["h"]
            expected = PAINTED[i[:3]]
            if abs(painted - expected) >= 0.51:
                failures.append(
                    f"{i}: the painted height moved to {painted}px, not {expected}px; "
                    "the ruling keeps 24/28px and grows only the transparent area"
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
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / "button-hit-areas-393.png"),
                            clip={"x": 0, "y": 0, "width": 393, "height": 260})

        lost_kinds: set[str] = set()
        for control, why in (
            ("clipped", "a Button inside a 24px overflow:hidden well"),
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


def test_button_face_is_untouched_at_1440(tmp_path: Path) -> None:
    """The wide desk keeps the Button exactly as it was.

    The 44px area is a narrow-desk rule (`@media (max-width: 420px)`), so
    at 1440 the painted face, its box and its neighbours must be
    identical to the pre-ruling Button. This is the other half of the
    proof: the hit area grew where the ruling says, and nowhere else.
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
                     return { h: el.getBoundingClientRect().height,
                              w: el.getBoundingClientRect().width,
                              marginTop: cs.marginTop, marginBottom: cs.marginBottom,
                              minInline: cs.minInlineSize, halo: after.content };
                   }""",
                i,
            )
            expected = PAINTED[i[:3]]
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
            if box["halo"] not in ("none", "normal"):
                failures.append(f"{i}: the halo pseudo-element exists at 1440 ({box['halo']})")

        if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / "button-hit-areas-1440.png"),
                            clip={"x": 0, "y": 0, "width": 420, "height": 230})
        browser.close()

    assert not failures, (
        "the wide desk's Button changed:\n  " + "\n  ".join(failures)
    )
