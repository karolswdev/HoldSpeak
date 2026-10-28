#!/usr/bin/env python3
"""Direction D icon family (owner pick 2026-10-24): flat Workbench.

Front-on flat silhouettes, two or three flat tones per material, a navy
#263b53 outline and a hard Workbench bevel (light edge top left in the
material's paper tint, shade edge bottom right in its darker tone). Light
comes from the upper left. No gradients, perspective or tilt.

This script is the source of truth for every SVG under
``web/design/icons/{world,system,settings}``. It writes one 64-unit source
per name. The source carries its optical level as CSS custom properties on
the root (``--ow`` outline, ``--u`` bevel offset, ``--lw`` line weight);
``gen-illustrated-icons.py`` overrides them for the 32 and 20 px exports
(see ``LEVELS`` there). ``.detail`` marks trim that may vanish below 64.

    uv run python web/scripts/gen-icons-d.py            # write the sources
    uv run python web/scripts/gen-icons-d.py --check    # compare, no writes

Then export with ``web/scripts/gen-illustrated-icons.py``.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "design" / "icons"
INK = "#263b53"

M = {  # material: base, light (paper tint), shade
    "blue":   ("#477fe0", "#a9c8ff", "#2b58ad"),
    "teal":   ("#259c96", "#8fe0d6", "#166e69"),
    "violet": ("#8870cb", "#cdbff5", "#5c479c"),
    "amber":  ("#ecaa45", "#ffe0a3", "#b0731a"),
    "grey":   ("#9fb3c8", "#e2ebf4", "#6b829b"),
    "greyL":  ("#c9d7e6", "#eef4fa", "#8ea4bc"),
    "paper":  ("#f4f8fc", "#ffffff", "#bccadb"),
    "navy":   ("#263b53", "#5a7799", "#14202f"),
    "mint":   ("#8ff0df", "#dafff7", "#3fb5a3"),
    "red":    ("#e2554f", "#ffa79f", "#a3302b"),
}

# The 64-unit level. 64 px: 2.5-unit bevel under a 1.5 outline (u = bevel + ow/2).
ROOT_VARS = "--ow:1.5px;--u:3.25px;--nu:-3.25px;--lw:1"
STYLE = (
    "<style>svg{" + ROOT_VARS + "}"
    ".ol{stroke-width:var(--ow)}"
    ".bv{transform:translate(var(--u),var(--u))}"
    ".bvn{transform:translate(var(--nu),var(--nu))}</style>"
)


def col(ref):
    if ref == "ink":
        return INK
    n, _, t = ref.partition(".")
    b, l, d = M[n]
    return {"": b, "light": l, "dark": d}[t]


def f(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def pts(p):
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


def rtop_d(x, y, w, h, r):
    return (f"M{f(x)} {f(y+h)}V{f(y+r)}A{f(r)} {f(r)} 0 0 1 {f(x+r)} {f(y)}H{f(x+w-r)}"
            f"A{f(r)} {f(r)} 0 0 1 {f(x+w)} {f(y+r)}V{f(y+h)}Z")


def bubble_d(x, y, w, h, r, tail):
    """A speech bubble with its tail under the left or right corner."""
    b = y + h
    if tail == "left":
        bottom = f"H{f(x+18)}L{f(x+6)} {f(b+8)}L{f(x+10)} {f(b)}H{f(x+r)}"
    else:
        bottom = f"H{f(x+w-10)}L{f(x+w-6)} {f(b+8)}L{f(x+w-18)} {f(b)}H{f(x+r)}"
    return (f"M{f(x+r)} {f(y)}H{f(x+w-r)}A{f(r)} {f(r)} 0 0 1 {f(x+w)} {f(y+r)}"
            f"V{f(b-r)}A{f(r)} {f(r)} 0 0 1 {f(x+w-r)} {f(b)}{bottom}"
            f"A{f(r)} {f(r)} 0 0 1 {f(x)} {f(b-r)}V{f(y+r)}A{f(r)} {f(r)} 0 0 1 {f(x+r)} {f(y)}Z")


def gear(cx, cy, ro, ri, n):
    p, step = [], 2 * math.pi / n
    for i in range(n):
        a = i * step - math.pi / 2
        for ang, r in ((a - step * .30, ri), (a - step * .2, ro), (a + step * .2, ro), (a + step * .30, ri)):
            p.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return p


def star(cx, cy, ro, ri):
    return [(cx + (ro if i % 2 == 0 else ri) * math.cos(-math.pi / 2 + i * math.pi / 5),
             cy + (ro if i % 2 == 0 else ri) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]


def loop_band(cx, cy, ro, ri, a0, sweep, head):
    """A heavy loop: an annulus segment ending in an arrowhead (degrees, clockwise)."""
    steps = 28
    outer = [(cx + ro * math.cos(math.radians(a0 + sweep * k / steps)),
              cy + ro * math.sin(math.radians(a0 + sweep * k / steps))) for k in range(steps + 1)]
    inner = [(cx + ri * math.cos(math.radians(a0 + sweep * k / steps)),
              cy + ri * math.sin(math.radians(a0 + sweep * k / steps))) for k in reversed(range(steps + 1))]
    a1 = math.radians(a0 + sweep)
    mid = (ro + ri) / 2
    tip = math.radians(a0 + sweep + head)
    arrow = [(cx + (ro + 3.5) * math.cos(a1), cy + (ro + 3.5) * math.sin(a1)),
             (cx + mid * math.cos(tip), cy + mid * math.sin(tip)),
             (cx + (ri - 3.5) * math.cos(a1), cy + (ri - 3.5) * math.sin(a1))]
    return outer + arrow + inner


# shape constructors -> svg element head without fill/stroke
def R(x, y, w, h, r):
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(r)}"'


def T(x, y, w, h, r):
    return f'<path d="{rtop_d(x, y, w, h, r)}"'


def C(cx, cy, r):
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}"'


def P(p):
    return f'<polygon points="{pts(p)}"'


def D(d):
    return f'<path d="{d}"'


# part: ("s", shape, mat, opts) | ("l", points, colour, width, opts) | ("a", path_d, colour, width, opts)
def S(shape, mat, **o):
    return ("s", shape, mat, o)


def L(p, c, w, **o):
    return ("l", p, c, w, o)


def A(d, c, w, **o):
    return ("a", d, c, w, o)


# ── shared constructions ───────────────────────────────────────────────

def folder(front, emblem=(), flag=False):
    """Grey-blue paper back and tab, a coloured front (the zone's colour)."""
    parts = [
        S(T(9, 10, 19, 9, 3), "grey", plain=True),
        S(R(9, 15, 46, 36, 3), "grey", plain=True),
        S(R(13, 19, 38, 20, 2), "paper", plain=True),
        L([(18, 24), (37, 24)], "grey.dark", 2, detail=True),
    ]
    if flag:  # the Project mark: a pennant on a pole, read at 20 px
        parts += [L([(43, 27), (43, 7)], "navy", 2.6),
                  S(P([(43, 5.5), (57, 12), (43, 18.5)]), "amber")]
    parts.append(S(R(7, 26, 50, 29, 3), front))
    return parts + list(emblem)


def agent(tile, detail):
    """A front portrait tile: Claude Code, Codex and pi differ by colour + one detail."""
    parts = [
        S(R(7, 7, 50, 50, 11), tile),
        S(T(16, 42, 32, 14, 11), "navy", plain=True),
        S(R(20, 14, 24, 25, 9), "grey"),
    ]
    if detail == "claude":   # wide visor, two eyes, a spark on the chest
        parts += [S(R(23, 21, 18, 9, 4), "navy", plain=True),
                  S(R(26, 24, 4, 3, 1.5), "mint", nool=True), S(R(34, 24, 4, 3, 1.5), "mint", nool=True),
                  S(P([(32, 45), (33.6, 48.4), (37, 50), (33.6, 51.6), (32, 55), (30.4, 51.6), (27, 50), (30.4, 48.4)]), "amber", nool=True)]
    elif detail == "codex":  # one long slit visor, a collar bar
        parts += [S(R(23, 22, 18, 7, 3.5), "navy", plain=True),
                  S(R(26, 24.5, 12, 2, 1), "mint", nool=True),
                  S(R(26, 46, 12, 3, 1.5), "teal", nool=True)]
    elif detail == "pi":     # round eyes, an antenna ball
        parts += [L([(32, 14), (32, 10)], "navy", 2),
                  S(C(32, 10, 2.6), "amber", plain=True),
                  S(R(23, 21, 18, 9, 4), "navy", plain=True),
                  S(C(28, 25.5, 2), "mint", nool=True), S(C(36, 25.5, 2), "mint", nool=True)]
    else:                    # the generic Agents app: two ear bolts
        parts += [S(R(16, 22, 5, 9, 2.5), "grey", plain=True), S(R(43, 22, 5, 9, 2.5), "grey", plain=True),
                  S(R(23, 21, 18, 9, 4), "navy", plain=True),
                  S(C(28, 25.5, 2), "mint", nool=True), S(C(36, 25.5, 2), "mint", nool=True)]
    return parts


def page(fill="paper"):
    return [S(P([(14, 7), (40, 7), (50, 17), (50, 56), (14, 56)]), fill),
            S(P([(40, 7), (40, 17), (50, 17)]), "grey", plain=True)]


def mic(dx=0, small=False):
    x = lambda v: v + dx
    w = 0.86 if small else 1
    cx = x(32)
    hw = 15 * w
    return [
        L([(cx - hw, 25), (cx - hw, 32), (cx - hw * .8, 39), (cx - hw * .4, 43), (cx, 44), (cx + hw * .4, 43), (cx + hw * .8, 39), (cx + hw, 32), (cx + hw, 25)], "grey", 3, outlined=True),
        L([(cx, 45), (cx, 50)], "grey", 3, outlined=True),
        S(R(cx - 12, 50, 24, 6, 3), "grey"),
        S(R(cx - 9, 6, 18, 32, 9), "grey"),
        S(R(cx - 9, 29, 18, 5, 0), "teal", plain=True),
        L([(cx - 4.5, 13), (cx + 4.5, 13)], "navy", 2),
        L([(cx - 4.5, 18), (cx + 4.5, 18)], "navy", 2, detail=True),
        L([(cx - 4.5, 23), (cx + 4.5, 23)], "navy", 2),
    ]


MEETING = [
    S(R(8, 14, 48, 42, 4), "paper"),
    S(T(8, 14, 48, 12, 4), "blue"),
    S(R(18, 8, 5, 10, 2.5), "grey", plain=True),
    S(R(41, 8, 5, 10, 2.5), "grey", plain=True),
    S(C(24.5, 35, 5), "blue", plain=True),
    S(T(17, 42, 15, 10, 7), "blue", plain=True),
    S(C(39.5, 35, 5), "blue", plain=True),
    S(T(32, 42, 15, 10, 7), "blue", plain=True),
]
PEOPLE = [
    S(C(41, 19, 8), "grey"),
    S(T(28, 31, 26, 21, 12), "grey"),
    S(C(25, 25, 9), "teal"),
    S(T(10, 38, 30, 18, 14), "teal"),
]
GEAR = [
    S(P(gear(32, 32, 25, 19, 8)), "grey"),
    S(C(32, 32, 10), "blue"),
    S(C(32, 32, 4), "navy", plain=True),
]
LOOP = [  # heavier, two-tone: a bevelled band, not a thin stroke
    S(P(loop_band(32, 32, 23, 14, -70, 285, 22)), "violet"),
    S(P(gear(32, 32, 10, 7, 6)), "paper"),
    S(C(32, 32, 3.4), "violet", plain=True),
]
CARTRIDGE = [
    S(P([(12, 8), (44, 8), (52, 16), (52, 56), (12, 56)]), "grey"),
    S(R(18, 15, 27, 22, 2), "violet"),
    L([(23, 22), (38, 22)], "violet.light", 2, detail=True),
    L([(23, 28), (34, 28)], "violet.light", 2, detail=True),
    S(R(20, 44, 4, 8, 1.5), "navy", nool=True),
    S(R(27, 44, 4, 8, 1.5), "navy", nool=True),
    S(R(34, 44, 4, 8, 1.5), "navy", nool=True),
    S(R(41, 44, 4, 8, 1.5), "navy", nool=True),
]
MEMORY = (
    [S(R(6, 19 + 9 * i, 9, 4, 2), "grey", plain=True) for i in range(3)]
    + [S(R(49, 19 + 9 * i, 9, 4, 2), "grey", plain=True) for i in range(3)]
    + [S(R(19 + 9 * i, 6, 4, 9, 2), "grey", plain=True) for i in range(3)]
    + [S(R(19 + 9 * i, 49, 4, 9, 2), "grey", plain=True) for i in range(3)]
    + [S(R(13, 13, 38, 38, 5), "grey"),
       S(R(22, 22, 20, 20, 3), "violet"),
       S(R(27, 27, 10, 10, 2), "violet.light" if False else "paper", nool=True, detail=True)]
)
METRONOME = [  # a wedge on a plinth, the arm swung right
    S(P([(24, 7), (40, 7), (49, 46), (15, 46)]), "amber"),
    S(P([(27.5, 13), (36.5, 13), (41, 38), (23, 38)]), "paper", plain=True),
    L([(32, 38), (42, 13)], "navy", 2.8),
    S(R(36.5, 18.5, 8, 7, 2), "grey", plain=True),
    S(C(32, 38, 3), "navy", plain=True),
    S(R(9, 44, 46, 12, 3), "grey"),
]
# A desk telephone, front on (Calls, 2026-10-28): the blue handset lies on a
# grey cradle; the keys are trim that vanishes below 64.
HANDSET_D = ("M6 23Q6 13 16 13H48Q58 13 58 23V29Q58 32 55 32H47Q44 32 44 29V25"
             "H20V29Q20 32 17 32H9Q6 32 6 29Z")
TELEPHONE = (
    [S(P([(15, 28), (49, 28), (56, 56), (8, 56)]), "grey")]
    + [S(R(20 + 9 * c, 37 + 7 * r, 6, 4, 1.5), "paper", nool=True, detail=True)
       for r in range(2) for c in range(3)]
    + [S(D(HANDSET_D), "blue")]
)
CHAT = [
    S(D(bubble_d(20, 8, 36, 24, 8, "right")), "grey"),
    S(D(bubble_d(8, 20, 38, 26, 8, "left")), "blue"),
    S(C(18, 33, 2.6), "paper", nool=True),
    S(C(27, 33, 2.6), "paper", nool=True),
    S(C(36, 33, 2.6), "paper", nool=True),
]


# ── the family: every active name ──────────────────────────────────────

WORLD = {
    "action-item": [
        S(R(11, 7, 42, 50, 4), "paper"),
        S(R(17, 15, 9, 9, 2), "teal"),
        L([(19, 19.5), (21, 21.5), (24.5, 17)], "paper", 2),
        S(R(30, 17.5, 17, 4, 2), "grey", nool=True),
        S(R(17, 29, 9, 9, 2), "teal"),
        L([(19, 33.5), (21, 35.5), (24.5, 31)], "paper", 2),
        S(R(30, 31.5, 14, 4, 2), "grey", nool=True),
        S(R(17, 43, 9, 9, 2), "paper", plain=True),
        S(R(30, 45.5, 17, 4, 2), "grey", nool=True, detail=True),
    ],
    "agent-claude-code": agent("amber", "claude"),
    "agent-codex": agent("teal", "codex"),
    "agent-pi": agent("violet", "pi"),
    "artifact": page() + [
        S(R(19, 23, 26, 20, 2), "blue"),
        S(P([(21, 41), (28, 32), (33, 37), (36, 34), (43, 41)]), "paper", nool=True),
        S(C(38.5, 28.5, 2.6), "amber", nool=True),
        S(R(19, 48, 18, 3.5, 1.75), "grey", nool=True, detail=True),
    ],
    "call": TELEPHONE,
    "cartridge": CARTRIDGE,
    "conductor-drawer": folder("paper", emblem=[
        S(R(24, 31, 16, 19, 4.5), "amber"),
        S(R(27, 36, 10, 5, 2.5), "navy", plain=True),
        S(C(30, 38.5, 1.2), "mint", nool=True), S(C(34, 38.5, 1.2), "mint", nool=True),
    ]),
    "decision": page() + [
        S(R(19, 18, 16, 3.5, 1.75), "grey", nool=True),
        S(R(19, 25, 22, 3.5, 1.75), "grey", nool=True, detail=True),
        S(C(39, 42, 10.5), "violet"),
        L([(34, 42), (37.5, 45.5), (44, 38.5)], "paper", 3),
    ],
    "meeting": MEETING,
    "memory": MEMORY,
    "note": page() + [
        S(R(20, 26, 22, 5, 2.5), "amber", nool=True),
        S(R(20, 36, 24, 4, 2), "grey", nool=True),
        S(R(20, 45, 16, 4, 2), "grey", nool=True, detail=True),
    ],
    "parked-drawer": [
        S(R(9, 22, 46, 34, 3), "amber"),
        S(R(7, 12, 50, 12, 3), "amber"),
        S(R(24, 31, 16, 6, 3), "navy", plain=True),
    ],
    "people-ledger": [
        S(R(15, 10, 40, 46, 4), "paper", plain=True),
        S(R(9, 7, 41, 47, 4), "teal"),
        S(R(9, 7, 8, 47, 3), "teal.dark", plain=True),
        S(R(23, 15, 21, 25, 3), "paper"),
        S(C(33.5, 23, 4.2), "teal", plain=True),
        S(T(26.5, 30, 14, 7, 6), "teal", plain=True),
    ],
    "person": [
        S(C(32, 21, 10), "teal"),
        S(T(13, 35, 38, 21, 17), "teal"),
    ],
    "project-drawer": folder("blue", flag=True),
    "pull-request": [
        L([(20, 20), (20, 44)], "grey", 5, outlined=True),
        A("M44 44V30Q44 19 34 19H30", "grey", 5, outlined=True),
        S(P([(31, 12.5), (23.5, 19), (31, 25.5)]), "grey", plain=True),
        S(C(20, 15, 6), "teal"),
        S(C(20, 49, 6), "teal"),
        S(C(44, 49, 6), "teal"),
    ],
    "repository": [
        S(R(9, 7, 46, 49, 4), "grey"),
        S(R(14, 12, 36, 19, 2), "teal"),
        S(R(20, 15.5, 24, 12, 3), "paper", plain=True),
        L([(28, 18), (24.5, 21.5), (28, 25)], "navy", 2),
        L([(36, 18), (39.5, 21.5), (36, 25)], "navy", 2),
        S(R(14, 35, 36, 16, 2), "teal"),
        S(R(26, 40.5, 12, 5, 2.5), "paper", plain=True),
    ],
    "smart-drawer": folder("paper", emblem=[
        L([(36, 45), (42, 51)], "navy", 3.6),
        S(C(31, 40, 7.5), "blue"),
        S(C(31, 40, 3.6), "paper", plain=True),
    ]),
    "thread": CHAT,
    # The zone folders: the front wears the zone's colour (web/src/desk/sprites.ts ZONE_HUES).
    "zone-drawer": folder("blue"),
    "zone-drawer-teal": folder("teal"),
    "zone-drawer-violet": folder("violet"),
    "zone-drawer-amber": folder("amber"),
}

SYSTEM = {
    "cadence-metronome": METRONOME,
    "dock-agents": agent("blue", "generic"),
    "dock-delivery": [
        S(P([(7, 31), (56, 9), (27, 39)]), "paper"),
        S(P([(27, 39), (56, 9), (36, 54)]), "blue"),
        S(P([(27, 39), (29, 51), (33.5, 46)]), "grey", plain=True),
    ],
    "dock-desk-memory": MEMORY,
    "dock-intelligence": [
        S(R(23, 41, 18, 13, 3), "grey"),
        L([(24, 46), (40, 46)], "grey.dark", 1.6, detail=True),
        S(C(32, 25, 17), "amber"),
        L([(26, 29), (29, 23), (32, 29), (35, 23), (38, 29)], "navy", 2.2),
        S(R(29, 54, 6, 3, 1.5), "navy", nool=True),
    ],
    "dock-meetings": MEETING,
    "dock-panes": [
        S(R(8, 9, 48, 46, 4), "grey"),
        S(R(13, 18, 18, 32, 2), "navy", plain=True),
        S(R(33, 18, 18, 32, 2), "navy", plain=True),
        L([(17, 26), (21, 30), (17, 34)], "mint", 2.4),
        S(R(23, 32, 5, 2.4, 1.2), "mint", nool=True),
        S(R(37, 25, 10, 2.4, 1.2), "mint", nool=True),
        S(R(37, 31, 7, 2.4, 1.2), "mint", nool=True),
        S(R(37, 37, 9, 2.4, 1.2), "mint", nool=True, detail=True),
        S(C(14, 13.5, 1.5), "navy", nool=True, detail=True),
        S(C(19, 13.5, 1.5), "navy", nool=True, detail=True),
    ],
    "dock-people": PEOPLE,
    "dock-settings": GEAR,
    "dock-speak": mic(),
    "empty-loops": LOOP,
    "empty-nudges": [S(P(star(32, 33, 25, 11)), "amber")],
    "floor-grid": [S(R(9 + 16 * c, 9 + 16 * r, 14, 14, 2.5), "blue" if (c, r) == (1, 1) else "paper")
                   for r in range(3) for c in range(3)],
    "menu-bell": [
        S(C(32, 10, 3.5), "amber", plain=True),
        S(D("M18 44C18 30 20 15 32 15C44 15 46 30 46 44Z"), "amber"),
        S(C(32, 51, 4.5), "navy", plain=True),
        S(R(11, 41, 42, 7, 3.5), "amber"),
    ],
    "menu-mark": [
        S(D(bubble_d(9, 9, 46, 34, 10, "left")), "blue"),
        S(R(20, 22, 4, 10, 2), "paper", nool=True),
        S(R(27, 17, 4, 20, 2), "paper", nool=True),
        S(R(34, 20, 4, 14, 2), "paper", nool=True),
        S(R(41, 24, 4, 6, 2), "paper", nool=True),
    ],
    "menu-search": [
        L([(38, 38), (51, 51)], "grey", 7, outlined=True),
        S(C(27, 27, 17), "blue"),
        S(C(27, 27, 10.5), "paper"),
    ],
    "mic-listening": mic(small=True) + [
        A("M11 18Q6 25 11 32", "teal", 3, outlined=True),
        A("M53 18Q58 25 53 32", "teal", 3, outlined=True),
    ],
    "mic-recording": mic(dx=-4) + [S(C(49, 13, 6), "red")],
    "mic": mic(),
    "record-orb": [
        S(C(32, 32, 23), "paper"),
        S(C(32, 32, 14), "red"),
    ],
}

SETTINGS = {
    "integrations": [
        L([(32, 44), (32, 54)], "teal", 5, outlined=True),
        S(R(24, 7, 5, 14, 2.5), "greyL", plain=True),
        S(R(35, 7, 5, 14, 2.5), "greyL", plain=True),
        S(R(17, 18, 30, 27, 7), "grey"),
        S(R(17, 33, 30, 5, 0), "teal", plain=True),
    ],
    "meetings": MEETING,
    "models": CARTRIDGE,
    "rhythm": METRONOME,
    "sounds": [
        S(R(14, 7, 36, 50, 5), "grey"),
        S(C(32, 18, 5), "navy", plain=True),
        S(C(32, 39, 12), "blue"),
        S(C(32, 39, 4.5), "navy", plain=True),
    ],
    "system": [
        S(R(28, 42, 8, 8, 0), "grey", plain=True),
        S(R(18, 49, 28, 6, 3), "grey"),
        S(R(8, 9, 48, 35, 4), "grey"),
        S(R(13, 14, 38, 25, 2), "blue", plain=True),
        S(R(18, 19, 17, 11, 2), "paper", nool=True),
    ],
    "voice": mic(),
    "wallpaper": [
        S(R(8, 10, 48, 44, 4), "paper"),
        S(R(14, 16, 36, 32, 2), "blue", plain=True),
        S(P([(14, 48), (14, 41), (24, 31), (33, 40), (39, 35), (50, 45), (50, 48)]), "teal", nool=True),
        S(C(40, 24, 4), "amber", nool=True),
        S(R(14, 16, 36, 32, 2), "blue", nool=True, fill_none=True),
    ],
}

FAMILIES = {"world": WORLD, "system": SYSTEM, "settings": SETTINGS}


def render(name, parts):
    defs, body, n = [], [], 0
    for p in parts:
        kind, o = p[0], p[-1]
        out = []
        if kind in ("l", "a"):
            w = p[3]
            geom = f'<polyline points="{pts(p[1])}"' if kind == "l" else f'<path d="{p[1]}"'
            if o.get("outlined"):
                out.append(f'{geom} fill="none" stroke="{INK}" style="stroke-width:calc({f(w)}px * var(--lw) + var(--ow) * 1.8)"/>')
            out.append(f'{geom} fill="none" stroke="{col(p[2])}" style="stroke-width:calc({f(w)}px * var(--lw))"/>')
        else:
            shape, mat = p[1], p[2]
            fill = col(mat)
            if o.get("fill_none"):  # a closing outline over a picture window
                out.append(f'{shape} fill="none" stroke="{INK}" class="ol"/>')
            elif o.get("nool"):
                out.append(f'{shape} fill="{fill}"/>')
            elif o.get("plain") or "." in mat:
                out.append(f'{shape} fill="{fill}" stroke="{INK}" class="ol"/>')
            else:
                b, l, d = M[mat]
                n += 1
                sid = f"{name}-s{n}"
                defs.append(f'{shape} id="{sid}"/>')
                defs.append(f'<clipPath id="{name}-c{n}"><use href="#{sid}"/></clipPath>')
                defs.append(f'<clipPath id="{name}-m{n}"><use href="#{sid}" class="bvn" transform="translate(-3.25 -3.25)"/></clipPath>')
                out.append(
                    f'<g clip-path="url(#{name}-c{n})"><use href="#{sid}" fill="{l}"/>'
                    f'<use href="#{sid}" fill="{d}" class="bv" transform="translate(3.25 3.25)"/>'
                    f'<g clip-path="url(#{name}-m{n})"><use href="#{sid}" fill="{b}" class="bv" transform="translate(3.25 3.25)"/></g></g>'
                    f'<use href="#{sid}" fill="none" stroke="{INK}" class="ol"/>')
        if o.get("detail"):
            body.append(f'<g class="detail">{"".join(out)}</g>')
        else:
            body.extend(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{STYLE}'
            f'<defs>{"".join(defs)}</defs>'
            f'<g stroke-linejoin="round" stroke-linecap="round">{"".join(body)}</g></svg>\n')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="compare the sources, write nothing")
    ap.add_argument("--out", type=Path, default=ROOT, help="write somewhere else (a sheet)")
    args = ap.parse_args()
    stale = 0
    for family, designs in FAMILIES.items():
        folder_path = args.out / family
        folder_path.mkdir(parents=True, exist_ok=True)
        for name, parts in designs.items():
            svg = render(name, parts)
            target = folder_path / f"{name}.svg"
            if args.check:
                if not target.exists() or target.read_text(encoding="utf-8") != svg:
                    print(f"different: {target}")
                    stale += 1
            else:
                target.write_text(svg, encoding="utf-8")
    total = sum(len(d) for d in FAMILIES.values())
    if args.check:
        print(f"{total - stale}/{total} sources match the generator")
        return 1 if stale else 0
    print(f"wrote {total} D sources under {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
