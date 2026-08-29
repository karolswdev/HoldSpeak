# Phase 148 audit — the Amiga menu reference grammar

Opus research agent, 2026-08-29, primary sources (AmigaOS Wiki /
the Commodore UI Style Guide / intuition.h / era galleries). The
full cited report lives in the audit transcript; this is the
working condensation. Companions: [audit-census.md](./audit-census.md),
[audit-menus-live.md](./audit-menus-live.md).

## The grammar (what Workbench menus actually were)

1. **Text-only items.** Standard Intuition menus carried NO item
   icons — ever. The grammar is: terse label (1–3 words) +
   checkmark lane (left) + Amiga-key glyph & command char (right) +
   separators + `»` submenu indicator + `…` for dialog-openers.
   Icon columns arrived with Windows 95, not the Amiga. (MagicMenu,
   an aftermarket commodity, added imagery later — explicitly
   non-canonical.)
2. **HIGHCOMP hover** — the select box complement/inverse-videos on
   pointer-over. THE distinctive Amiga hover.
3. **Ghosting = stipple**: "a pattern of dots in the shadow color"
   over the item's select box only. Style Guide law, verbatim:
   *"Whenever a menu or menu item is inappropriate or unavailable
   for selection, it should be ghosted. Never allow the user to
   select something that does nothing in response."* CSS
   reproduction: 2×2 checkerboard (repeating-conic-gradient trick),
   shadow tone, ~40-50% opacity; sparser (3×3/4×4) if too dense on
   dark.
4. **The shortcut glyph**: the "fancy A" (Right-Amiga; outline
   variant) as a small ROM bitmap ≈ one character span, flush-right
   + the single command character at the rightmost edge —
   column-aligned across items (COMMWIDTH 27px hi-res). The keycap
   POSITION always carried a drawn glyph — this is where a sprite
   is authentic.
5. **Checkmark lane**: CHECKWIDTH (19px hi-res) reserved on the
   left for toggle items; blank when unchecked; Style Guide:
   toggles indent to make the lane a visual cue. Workbench used
   square-check for toggles and circle-with-dot for mutual-exclude.
6. **Separators**: recessed 1px rules (shine above/shadow below in
   the 2.0 bevel system); group by function; separate toggles from
   non-toggles.
7. **2.0+ material**: grey #AAAAAA ground, black shadow, white
   shine, 1px bevels, light from upper-left; Topaz 8 bitmap mono.
8. Style Guide rules adopted verbatim into the 148 spec: the
   ghosting law (3 above), the ellipsis rule, terse labels,
   separator grouping, no-title-repetition, right-justified
   shortcut column, toggle indentation.

## The recommendation (agent's, with the tension named)

Authentic translation = HIGHCOMP hover, stipple ghosting, drawn
keycap glyph flush-right, checkmark lane, recessed separators,
`»`/`…` conventions — all direct fits for the dark Signal
Workbench. A LEFT icon column is where tribute becomes Windows 95;
the one place a sprite is unambiguously reverent is the keycap
glyph (the fancy-A's seat) and the toggle-lane marks.

**The open owner question this creates:** the owner's ask was
"glyphs" — the mock round presents the honest options side by side:
(A) the Purist — full authentic grammar, no icon column; (B) the
Tribute-Plus — grammar + a restrained left glyph column everywhere;
(C) the Hybrid — grammar everywhere, glyph column ONLY in launcher
contexts (Go / Launch› / New›) where items are PROGRAMS and KINDS
that already own sprite identities in the dock and palette, while
verb menus (Object/Window) stay text-pure. The orchestrator's
recommendation is C: dock-parity for nouns, Amiga purity for verbs.
