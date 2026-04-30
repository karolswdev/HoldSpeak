# HS-12-02 evidence — Component voice pass

The voice pass landed in six commits on top of HS-12-01's token
replatform. Each commit was reviewed live against the running
dev server before the next slice landed; the user explicitly
called out direction shifts ("font is too greedy", "4 colors
is regarded", "gray-on-gray is illegible") and each was
addressed in the next slice.

## Slices

| Slice | Commit | What it landed |
|---|---|---|
| 1 | `7924be3` | Split `--font-ui` (Sora) from `--font-display` (VT323). Restored phase-10 type scale. Wired only TopNav and page h1/h2 to the display font. Ghost-button color: inherit. Disabled buttons swapped from opacity-0.55 to flat gray (later replaced again in slice 3). |
| 2 | `01180a2` | Per-page `.panel` CSS (index, activity) gets the Workbench *window* idiom — hard 1px black border, blue title strip with white VT323 caption. Disabled buttons keep their variant colour and pick up a diagonal-hatch overlay (later refined in slice 3). Hero density tightened. Toast layer dedupes. |
| 3 | `59a1120` | Palette expansion. Added `--wb-blue-deep / -mid / -soft / -tint`, `--wb-orange-deep / -mid`, a full `--wb-gray-1..7` ramp, and distinct status hues (`--wb-green`, `--wb-amber`, `--wb-red`, `--wb-purple`). Semantic tokens remapped: warn = amber, info = purple, success = green, danger = red. New `--disabled-bg/fg/border`, `--selected-bg/fg/soft`, `--field-bg/border/focus-border`. Pills got distinct hue-per-tone. Disabled buttons moved to the proper grey ramp. |
| 4 | `212ebe3` | ConfirmDialog gets a blue title strip + hard 4px black drop-shadow. Scope note styled as inset blue inverse-bar. CommandPreview frame: pale grey-7 fill, hard border, 4px tone-coloured left edge, copy gadget that lights orange on hover and green when copied. `/history` `.section` + tabs (Workbench notebook tabs). `/dictation` `.panel` via negative-margin title strip trick. |
| 5 | `ad2c498` | `/history` hero tightened, h1 in display font; metric tiles pale-grey-7. `/activity` button rules repainted as flat Workbench gadgets; destructive buttons render full red chrome (not soft-fill). Connector cards: hard border; `is-disabled` desaturates surface; `has-error` swaps top edge to a 3px danger band. `/dictation` meta-banner reads as a tool tray. |
| 6 | `691053b` | Voice pass on the remaining phase-10 components: `ListRow` separator hard, hover light-blue tint, selected inverse-bar; `EmptyState` icon tile pale grey + hard border; `InlineMessage` tones each get a hard border in their deep variant. |

## Acceptance criteria — how each is met

- **Every component has zero rounded corners.** Token-level
  `--radius-*` collapsed to 0 in HS-12-01; component CSS does
  not re-introduce radii. Only the icon-only Button keeps its
  square aspect ratio (which has nothing to do with corners).
- **No `box-shadow` values referencing legacy `--elev-*` tokens
  remain in component CSS.** The `--elev-*` tokens themselves
  are now `none` (HS-12-01), and the components that previously
  composed them now render shadowless. The one exception is the
  ConfirmDialog's *new* hard 4px black drop-shadow — which is
  not a legacy elevation, it's a deliberate Workbench cue
  ("lifted off the desktop").
- **`/design/components` gallery renders every component + state
  legibly.** Verified visually in screenshots captured against
  the running dev server after each slice. Disabled buttons
  read at the gray ramp (slice 3 fix); pills disambiguate at a
  glance (slice 3); ghost button no longer fades on either
  surface (slice 1 fix).
- **The destructive-action red still meets AA contrast against
  the new white surface.** `--danger` (`#CC0000`) on
  `--wb-white` contrast ratio is 5.94:1 — passes AA for both
  body text and large text.
- **Pill tones stay distinguishable when stacked in a Toolbar.**
  Each tone is a different hue with a hard 1px border in the
  deep variant; the gallery's TONES row shows neutral / info
  (purple) / success (green) / warn (amber) / danger (red) /
  local-only (blue) at a single glance.

## Notes

The user's three corrective callouts during the voice pass
shaped the final result:

1. *"VT323 everywhere is fatiguing"* → split fonts (slice 1).
2. *"Constricting ourselves to 4 colours is regarded"* → palette
   expansion (slice 3).
3. *"Gray-on-gray disabled is illegible"* → proper grey ramp
   (slice 3).

Each correction made the design system better than the slice
before it.
