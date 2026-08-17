# HS-135-14 — The chrome speaks Workbench

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

Owner direction (2026-08-17, mid-phase, screenshots in hand): the
system chrome icons are sparse and ugly — the 16×16 `mic.png` "reads
as a lightbulb" and sits misaligned in the note editor (an orphaned
square mic button floats below Tags aligned to nothing); one green
document sprite carries every empty state regardless of meaning;
Cadence has no visual identity at all. The whole system family is
NINE sprites (`web/src/desk/systemSprites.ts`). The owner's bar:
"Workbench had an excellent and very clear icon style… that level of
hygiene. It was beautiful. It was delightful." And: "we have PixelLab
MCP — let's use it."

The method is proven and the style is OWNER-RATIFIED (2026-08-17,
verbatim: "The bell bright is nice, that's the kind of style I want
man! AMIGA OS FOREVER" — the first gloomy mold was REJECTED: "Too
gloomy. This is not an RPG"). The mold is the BRIGHT palette
([assets/icon-palette.png](./assets/icon-palette.png) — silver-white,
light silver, mid slate, ink, pure white, 2 embers, workbench
blue-grey) forced through PixelLab's
palette constraint, one prompt template carrying the laws (hard
single-color outline, no anti-aliasing, top-left light, two shades
per surface, 32×32 for crisp 2x in 16px slots). Owner-approved castings (2026-08-17): bright-bell.png (the ratified
reference), bright-mic.png, and bright-metronome.png — all three in
the session forge (scratchpad icon-forge/) and adopted as the family
seeds; the full contact sheet still rides to the owner before wiring. Everything casts BRIGHT —
silver-forward, cheerful, crisp; dark fills are forbidden.

## Scope

### In

- **The mold as a tool:** a small committed script
  (`scripts/icon_forge.py` or docs in the assets) recording the
  palette, the prompt template, and the casting laws so future icons
  come from the same mold.
- **The family, regenerated at 32×32 through the mold:** mic (idle +
  listening + recording states), record orb (harmonized), the four
  dock icons and three menu glyphs re-cast for consistency, cadence
  metronome identity, and PER-MEANING empty-state glyphs (no loops =
  resting metronome; no nudges = quiet bell; the green document
  retires from universal duty — inventory every empty-state call
  site and give each meaning its glyph or an honest shared default).
- **Wiring:** `systemSprites.ts` (the no-orphan guard in
  systemSprites.test.ts must stay green), retina-correct rendering
  (32px assets in 16px slots, pixelated image-rendering where the
  desk already sets it).
- **The alignment fix:** the note-editor's orphaned mic button below
  Tags — either seated properly with its field (vertically centered,
  right-aligned inside the field well like the title/Tags mics) or
  given an honest label/home; the in-field mics vertically centered
  using the new `--size-icon-md` token.
- **Owner sign-off gate:** the regenerated family lands in the phase
  assets as a contact sheet FIRST; the orchestrator shows the owner
  before wiring (art tested on the real desk — standing rule).

### Out

- Object/floor sprites (already crafted, praised by the audits);
  Qlippy; toolbar glyph redesign (SVG VerbGlyphs won per HS-111-09 —
  unchanged); Cadence's UX comprehensibility (setup-flows audit →
  next leg).

## Acceptance criteria

- [ ] Every system sprite in `systemSprites.ts` is a palette-mold
  casting at 32×32; the no-orphan guard is green.
- [ ] Mic states render idle/listening/recording distinctly; the
  editor mics are aligned (screenshot pair before/after).
- [ ] Cadence's window carries the metronome identity; empty states
  are per-meaning.
- [ ] The contact sheet rode to the owner before wiring (noted in
  evidence).
- [ ] `cd web && npx vitest run` touched suites green.

## Test plan

- systemSprites tests + touched component suites; before/after
  screenshots in evidence; both-widths rendering rides HS-135-13.
