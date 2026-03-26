"""CRT-style scanline / noise overlay for a subtle texture."""

from __future__ import annotations

import time

from rich.text import Text
from textual.widget import Widget


class CrtOverlay(Widget):
    """A lightweight, low-opacity scanline/noise overlay.

    This is intentionally subtle: it provides a "Quake HUD" texture without
    reducing readability or looking gimmicky on screenshares.
    """

    can_focus = False

    def on_mount(self) -> None:
        # Slow refresh to keep it dynamic without being distracting.
        self.set_interval(0.35, self.refresh)

    @staticmethod
    def _lcg(seed: int) -> int:
        # 32-bit LCG parameters (Numerical Recipes).
        return (1664525 * seed + 1013904223) & 0xFFFFFFFF

    def render(self) -> Text:
        width = max(1, self.size.width)
        height = max(1, self.size.height)

        # Time-based seed so it subtly "moves" over time.
        seed = int(time.time() * 10) & 0xFFFFFFFF

        lines: list[str] = []
        for y in range(height):
            # Stronger scanline rows, weaker in-between.
            base_density = 0.060 if (y % 2 == 0) else 0.028
            row_seed = (seed ^ (y * 0x9E3779B1)) & 0xFFFFFFFF

            chars: list[str] = []
            s = row_seed
            for _x in range(width):
                s = self._lcg(s)
                r = s / 0x100000000
                if r < (base_density * 0.12):
                    chars.append("░")
                elif r < base_density:
                    chars.append("·")
                else:
                    chars.append(" ")
            lines.append("".join(chars))

        return Text("\n".join(lines))

