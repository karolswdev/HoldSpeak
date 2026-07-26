#!/usr/bin/env python3
"""HS-105-01 — derive the state images for every world sprite.

For each base sprite in web/public/desk/sprites/ this writes two REAL
sibling images (the Workbench dual-image rule — state is a second
image on disk, never a runtime filter):

  <name>_sel.png   — brightened facets + a 1px light rim traced around
                     the alpha edge (lit from within);
  <name>_stale.png — desaturated and dimmed.

Deterministic pixel math (no models, no randomness): running it twice
produces byte-identical files, so the guard can assert freshness by
regenerating and comparing. Skips derived files as inputs.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageEnhance

SPRITES = Path(__file__).resolve().parents[1] / "public" / "desk" / "sprites"
RIM = (232, 240, 255, 190)  # the light rim, cool white


def rim_mask(alpha: Image.Image) -> Image.Image:
    """1px outline just inside the alpha edge (dilate minus original)."""
    w, h = alpha.size
    src = alpha.load()
    out = Image.new("L", (w, h), 0)
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y] < 40:
                continue
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h or src[nx, ny] < 40:
                    edge = True
                    break
            if edge:
                dst[x, y] = 255
    return out


def derive(base: Path) -> None:
    im = Image.open(base).convert("RGBA")
    alpha = im.getchannel("A")

    sel = ImageEnhance.Brightness(im).enhance(1.24)
    sel = ImageEnhance.Color(sel).enhance(1.08)
    rim = Image.new("RGBA", im.size, RIM)
    sel.paste(rim, (0, 0), rim_mask(alpha))
    sel.putalpha(alpha)
    sel.save(base.with_name(f"{base.stem}_sel.png"))

    stale = ImageEnhance.Color(im).enhance(0.22)
    stale = ImageEnhance.Brightness(stale).enhance(0.86)
    stale.putalpha(alpha.point(lambda a: int(a * 0.88)))
    stale.save(base.with_name(f"{base.stem}_stale.png"))


def main() -> int:
    bases = [
        p
        for p in sorted(SPRITES.glob("*.png"))
        if not p.stem.endswith(("_sel", "_stale"))
    ]
    if not bases:
        print(f"no sprites found under {SPRITES}", file=sys.stderr)
        return 1
    for p in bases:
        derive(p)
    print(f"derived sel+stale for {len(bases)} sprites in {SPRITES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
