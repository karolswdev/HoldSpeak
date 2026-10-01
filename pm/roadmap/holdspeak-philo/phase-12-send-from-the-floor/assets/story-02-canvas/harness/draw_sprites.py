"""PHILO-12-02 canvas: the proposed Floor sprites, drawn pixel by pixel.

Eight 64x64 base sprites in the house palette (web/ICON-DISCIPLINE.md:
Signal orange #ff6b35, slate greys #0e0f13-#242833, paper whites
#767e8d-#f2f3f5; light from the top left; a clean dark outline; one flat
readable silhouette; no brand logos):

  decision    a gavel on its block            (the decision's own family, F2)
  brief       a folded broadsheet, masthead   (the brief icon, I1)
  ch-file     a manila folder                 (FILE)
  ch-github   a branch graph: three commits    (GITHUB; not the Octocat)
  ch-jira     a ticket stub, notched           (JIRA; not the Jira mark)
  ch-confluence  a pinned board on a stand     (CONFLUENCE; not its mark)
  ch-email    an envelope                      (EMAIL)
  ch-slack    a speech bubble with a hash      (SLACK; not the Slack mark)

The states (_sel, _stale) come from the PRODUCT's own derivation
(web/scripts/gen-sprite-states.py `derive`), imported by path: the same
pixel math every shipped sprite went through. Deterministic: run twice,
byte-identical files. Output: harness/sprites/.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "sprites"
REPO = HERE.parents[6]

INK = (14, 15, 19, 255)          # outline #0e0f13
SLATE = (36, 40, 51, 255)        # #242833
SLATE2 = (58, 64, 79, 255)
STEEL = (118, 126, 141, 255)     # #767e8d
PAPER = (242, 243, 245, 255)     # #f2f3f5
PAPER2 = (212, 215, 222, 255)
PAPER3 = (170, 176, 188, 255)
ORANGE = (255, 107, 53, 255)     # #ff6b35
ORANGE_D = (196, 74, 30, 255)
WOOD = (150, 98, 52, 255)
WOOD_L = (186, 128, 72, 255)
WOOD_D = (104, 66, 34, 255)
MANILA = (222, 178, 92, 255)
MANILA_L = (240, 204, 128, 255)
MANILA_D = (176, 132, 58, 255)
GREEN = (110, 190, 130, 255)
GREEN_D = (66, 132, 86, 255)
BLUE = (110, 150, 210, 255)
BLUE_L = (150, 184, 232, 255)
BLUE_D = (70, 104, 160, 255)
CORK = (190, 150, 98, 255)
CORK_D = (150, 112, 66, 255)
TEAL = (88, 176, 184, 255)
TEAL_D = (52, 124, 134, 255)
VIOLET = (140, 112, 196, 255)
VIOLET_L = (172, 148, 222, 255)
VIOLET_D = (96, 76, 150, 255)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def outline(im: Image.Image) -> Image.Image:
    """A 1px INK outline traced OUTSIDE the alpha edge (4-neighbour)."""
    a = im.getchannel("A").load()
    out = im.copy()
    px = out.load()
    for y in range(64):
        for x in range(64):
            if a[x, y]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 64 and 0 <= ny < 64 and a[nx, ny]:
                    px[x, y] = INK
                    break
    return out


def rect(d, x0, y0, x1, y1, c):
    d.rectangle([x0, y0, x1, y1], fill=c)


def decision():
    im, d = canvas()
    # the block (sounding block), wood, at the foot
    rect(d, 14, 46, 49, 52, WOOD)
    rect(d, 14, 46, 49, 46, WOOD_L)
    rect(d, 14, 52, 49, 52, WOOD_D)
    rect(d, 18, 43, 45, 45, WOOD_D)
    rect(d, 18, 43, 45, 43, WOOD)
    # the handle, diagonal, from the head down to the right
    for i in range(20):
        x, y = 30 + i, 25 + i // 1
        if y > 41:
            break
        rect(d, x, y, x + 2, y + 2, WOOD_L if i % 5 else WOOD)
    # the head: a barrel, slate with orange bands, tilted by placing it upper left
    rect(d, 12, 14, 36, 30, SLATE2)
    rect(d, 12, 14, 36, 15, STEEL)
    rect(d, 12, 29, 36, 30, SLATE)
    rect(d, 15, 12, 33, 13, SLATE2)
    rect(d, 15, 31, 33, 32, SLATE)
    rect(d, 16, 14, 18, 30, ORANGE)
    rect(d, 30, 14, 32, 30, ORANGE)
    rect(d, 16, 14, 18, 15, (255, 150, 110, 255))
    rect(d, 30, 14, 32, 15, (255, 150, 110, 255))
    rect(d, 9, 17, 11, 27, STEEL)    # the striking faces
    rect(d, 37, 17, 39, 27, SLATE)
    return outline(im)


def brief():
    im, d = canvas()
    # a folded broadsheet: the page, a fold line, the masthead bar in orange
    rect(d, 13, 12, 50, 53, PAPER)
    rect(d, 13, 12, 50, 13, (255, 255, 255, 255))
    rect(d, 46, 14, 50, 53, PAPER2)      # the page's right shade
    rect(d, 13, 51, 50, 53, PAPER3)      # the foot
    rect(d, 16, 16, 47, 21, ORANGE)      # masthead
    rect(d, 16, 21, 47, 21, ORANGE_D)
    rect(d, 18, 18, 30, 19, PAPER)       # the masthead's word stroke
    rect(d, 16, 24, 47, 24, SLATE2)      # the rule under it
    # two columns of text lines, a fold through the middle
    for y in range(28, 50, 3):
        rect(d, 16, y, 29, y, STEEL)
        rect(d, 34, y, 46, y, STEEL)
    rect(d, 16, 28, 29, 34, SLATE2)      # the lead picture block
    rect(d, 31, 26, 32, 50, PAPER3)      # the fold
    return outline(im)


def ch_file():
    im, d = canvas()
    rect(d, 10, 18, 28, 23, MANILA_D)    # the tab
    rect(d, 10, 18, 28, 18, MANILA)
    rect(d, 10, 22, 54, 50, MANILA)      # the back
    rect(d, 10, 22, 54, 23, MANILA_L)
    rect(d, 14, 25, 50, 27, PAPER)       # a paper inside
    rect(d, 8, 28, 56, 50, MANILA_L)     # the front flap
    rect(d, 8, 28, 56, 29, (252, 226, 168, 255))
    rect(d, 8, 48, 56, 50, MANILA_D)
    rect(d, 54, 30, 56, 48, MANILA)
    return outline(im)


def ch_github():
    im, d = canvas()
    # a branch graph: main line, a branch that leaves and merges back; three commit nodes
    rect(d, 20, 14, 23, 50, STEEL)       # main line
    rect(d, 20, 14, 21, 50, PAPER2)
    for y in range(22, 32):              # branch out, up right
        x = 22 + (y - 22)
        rect(d, x, 53 - y - 0, x + 3, 53 - y + 3, STEEL)
    rect(d, 40, 18, 43, 30, STEEL)
    for i in range(10):                  # merge back down left
        rect(d, 40 - i * 2, 30 + i * 2 - 2, 43 - i * 2, 33 + i * 2 - 2, STEEL)

    def node(cx, cy, c, cd):
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=cd)
        d.ellipse([cx - 5, cy - 5, cx + 4, cy + 4], fill=c)
        rect(d, cx - 3, cy - 3, cx - 1, cy - 2, PAPER)
    node(21, 13, GREEN, GREEN_D)
    node(42, 18, ORANGE, ORANGE_D)
    node(21, 51, GREEN, GREEN_D)
    return outline(im)


def ch_jira():
    im, d = canvas()
    # a ticket stub: a wide card with a perforated stub on the left, notches top and bottom
    rect(d, 8, 18, 56, 46, BLUE)
    rect(d, 8, 18, 56, 19, BLUE_L)
    rect(d, 8, 45, 56, 46, BLUE_D)
    for y in range(21, 45, 3):           # the perforation
        rect(d, 20, y, 20, y + 1, BLUE_D)
    # notches (transparent bites) at the perforation
    d.ellipse([17, 15, 23, 21], fill=(0, 0, 0, 0))
    d.ellipse([17, 43, 23, 49], fill=(0, 0, 0, 0))
    rect(d, 11, 25, 16, 39, BLUE_L)      # the stub's mark
    rect(d, 25, 24, 50, 26, PAPER)       # the card's lines
    rect(d, 25, 30, 44, 31, PAPER2)
    rect(d, 25, 35, 47, 36, PAPER2)
    rect(d, 45, 38, 51, 42, ORANGE)      # a status square
    return outline(im)


def ch_confluence():
    im, d = canvas()
    # a pinned board on two legs: a cork panel in a wood frame, two pinned pages
    rect(d, 18, 46, 20, 56, WOOD_D)      # legs
    rect(d, 43, 46, 45, 56, WOOD_D)
    rect(d, 8, 10, 55, 48, WOOD)         # frame
    rect(d, 8, 10, 55, 11, WOOD_L)
    rect(d, 8, 47, 55, 48, WOOD_D)
    rect(d, 11, 13, 52, 45, CORK)        # cork
    rect(d, 11, 13, 52, 14, CORK_D)
    rect(d, 15, 18, 30, 40, PAPER)       # page 1
    rect(d, 29, 18, 30, 40, PAPER2)
    for y in (24, 28, 32, 36):
        rect(d, 17, y, 27, y, STEEL)
    rect(d, 34, 16, 48, 34, PAPER)       # page 2
    rect(d, 47, 16, 48, 34, PAPER2)
    for y in (22, 26, 30):
        rect(d, 36, y, 45, y, STEEL)
    rect(d, 21, 16, 23, 18, ORANGE)      # pins
    rect(d, 40, 14, 42, 16, TEAL)
    return outline(im)


def ch_email():
    im, d = canvas()
    rect(d, 8, 18, 55, 47, PAPER)
    rect(d, 8, 18, 55, 19, (255, 255, 255, 255))
    rect(d, 8, 45, 55, 47, PAPER3)
    rect(d, 52, 20, 55, 45, PAPER2)
    for i in range(16):                  # the flap's V
        rect(d, 9 + i * 3 // 2, 20 + i, 10 + i * 3 // 2, 20 + i, PAPER3)
        rect(d, 53 - i * 3 // 2, 20 + i, 54 - i * 3 // 2, 20 + i, PAPER3)
    for i in range(10):                  # the lower folds
        rect(d, 9 + i * 2, 44 - i, 10 + i * 2, 44 - i, PAPER2)
        rect(d, 53 - i * 2, 44 - i, 54 - i * 2, 44 - i, PAPER2)
    rect(d, 28, 33, 35, 38, ORANGE)      # the seal
    rect(d, 28, 33, 35, 33, (255, 150, 110, 255))
    return outline(im)


def ch_slack():
    im, d = canvas()
    # a speech bubble, violet, with a tail at the lower left and a hash on it
    rect(d, 10, 12, 53, 42, VIOLET)
    rect(d, 12, 10, 51, 11, VIOLET)
    rect(d, 12, 43, 51, 44, VIOLET_D)
    rect(d, 10, 12, 53, 13, VIOLET_L)
    rect(d, 52, 14, 53, 42, VIOLET_D)
    for i in range(8):                   # the tail
        rect(d, 16, 44 + i, 24 - i, 44 + i, VIOLET_D if i == 7 else VIOLET)
    # the hash
    for x in (25, 35):
        rect(d, x, 17, x + 3, 38, PAPER)
    for y in (22, 31):
        rect(d, 20, y, 44, y + 3, PAPER)
    rect(d, 25, 17, 26, 38, (255, 255, 255, 255))
    return outline(im)


SPRITES = {
    "decision": decision, "brief": brief,
    "ch-file": ch_file, "ch-github": ch_github, "ch-jira": ch_jira,
    "ch-confluence": ch_confluence, "ch-email": ch_email, "ch-slack": ch_slack,
}


def main() -> None:
    spec = importlib.util.spec_from_file_location("gen_states", REPO / "web/scripts/gen-sprite-states.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)  # type: ignore[union-attr]
    OUT.mkdir(exist_ok=True)
    for name, fn in SPRITES.items():
        base = OUT / f"{name}.png"
        fn().save(base)
        gen.derive(base)          # the product's _sel and _stale
    # a contact sheet for review: rest, sel, stale per row, 4x
    names = list(SPRITES)
    sheet = Image.new("RGBA", (3 * 256, len(names) * 256), (22, 24, 30, 255))
    for r, n in enumerate(names):
        for c, suf in enumerate(("", "_sel", "_stale")):
            sheet.alpha_composite(Image.open(OUT / f"{n}{suf}.png").convert("RGBA").resize((256, 256), Image.NEAREST),
                                  (c * 256, r * 256))
    sheet.save(HERE.parent / "shots" / "sprite-sheet.png")
    print("drew", len(names), "sprites")


if __name__ == "__main__":
    main()
