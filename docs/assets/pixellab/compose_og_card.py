#!/usr/bin/env python3
"""Compose the HoldSpeak social/OG card (1280x640) from the pixellab brand mark.

HS-33-05. PixelLab produces small transparent sprites (max 400px), not wide
banners — so the GitHub social card is *composed* here from the generated
`holdspeak-mark.png` plus the existing workflow spot-art, on the Signal palette.
This keeps the card reproducible: regenerate the mark via the pixellab MCP (see
README.md for the object ID + prompt), then re-run this script.

    uv run python3 docs/assets/pixellab/compose_og_card.py

Outputs:
  - docs/assets/pixellab/social-card.png  (1280x640, the GitHub social preview)
  - docs/assets/pixellab/holdspeak-icon-256.png  (square app icon, padded)
  - web/public/apple-touch-icon.png  (180x180 brand refresh)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]

# Signal palette (web/src/styles/tokens.css).
BG = (14, 15, 19)          # --bg  #0E0F13
SURFACE = (21, 23, 29)     # --surface-1 #15171D
SURFACE2 = (28, 31, 39)    # --surface-2 #1C1F27
TEXT = (242, 243, 245)     # --text #F2F3F5
MUTED = (155, 160, 170)
ACCENT = (255, 107, 53)    # --accent #FF6B35

# Closest available faces to the Signal stack (Space Grotesk / Inter / JetBrains
# Mono): SF for the wordmark, Menlo (mono) for the tagline.
SF = "/System/Library/Fonts/SFNS.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _scaled(img: Image.Image, target_h: int) -> Image.Image:
    """Integer-ish nearest-neighbour upscale to keep pixels crisp."""
    factor = max(1, round(target_h / img.height))
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def _fit_font(path: str, text: str, max_size: int, budget: int) -> ImageFont.FreeTypeFont:
    """Largest font (≤ max_size) whose `text` fits within `budget` px."""
    size = max_size
    while size > 8:
        font = _font(path, size)
        if font.getlength(text) <= budget:
            return font
        size -= 1
    return _font(path, 8)


def compose_card() -> None:
    card = Image.new("RGBA", (1280, 640), BG + (255,))
    draw = ImageDraw.Draw(card)

    # Subtle raised panel + an accent baseline (the "signal").
    draw.rectangle([0, 0, 1280, 8], fill=ACCENT)
    draw.rectangle([0, 632, 1280, 640], fill=SURFACE2)

    # Brand mark, upscaled crisp, left.
    mark = Image.open(HERE / "holdspeak-mark.png").convert("RGBA")
    mark = _scaled(mark, 360)
    mx, my = 96, (640 - mark.height) // 2 - 24
    card.alpha_composite(mark, (mx, my))

    # Wordmark + tagline, right of the mark — auto-fit to the card width.
    tx = mx + mark.width + 64
    budget = 1280 - tx - 56
    wordmark = _fit_font(SF, "HoldSpeak", 132, budget)
    draw.text((tx, 188), "HoldSpeak", font=wordmark, fill=TEXT)
    tagline = "Local-first voice input & meeting intelligence"
    draw.text((tx + 3, 344), tagline, font=_fit_font(MONO, tagline, 30, budget), fill=ACCENT)
    sub = "hold a key  ·  speak  ·  release"
    draw.text((tx + 3, 392), sub, font=_fit_font(MONO, sub, 26, budget), fill=MUTED)

    # The three pillars as a small spot-art row at the bottom-left.
    icons = [
        "hold-to-talk-microphone.png",
        "meeting-intelligence-notebook.png",
        "project-aware-typing.png",
    ]
    ix, iy = tx + 4, 470
    for name in icons:
        ic = Image.open(HERE / name).convert("RGBA")
        ic = _scaled(ic, 96)
        card.alpha_composite(ic, (ix, iy))
        ix += ic.width + 28

    out = HERE / "social-card.png"
    card.convert("RGB").save(out)
    print(f"wrote {out.relative_to(REPO)} ({card.width}x{card.height})")


def compose_icons() -> None:
    mark = Image.open(HERE / "holdspeak-mark.png").convert("RGBA")
    # Square padded app icon on transparent bg.
    side = 256
    icon = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    m = _scaled(mark, int(side * 0.78))
    icon.alpha_composite(m, ((side - m.width) // 2, (side - m.height) // 2))
    out256 = HERE / "holdspeak-icon-256.png"
    icon.save(out256)
    print(f"wrote {out256.relative_to(REPO)} (256x256)")

    # apple-touch-icon: 180x180 on the Signal canvas (no transparency for iOS).
    touch = Image.new("RGBA", (180, 180), BG + (255,))
    m2 = _scaled(mark, 132)
    touch.alpha_composite(m2, ((180 - m2.width) // 2, (180 - m2.height) // 2))
    touch_out = REPO / "web" / "public" / "apple-touch-icon.png"
    touch.convert("RGB").save(touch_out)
    print(f"wrote {touch_out.relative_to(REPO)} (180x180)")


if __name__ == "__main__":
    compose_card()
    compose_icons()
