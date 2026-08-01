# The icon discipline (HS-105-01)

The written law for every sprite that enters the desk's world layer.
Guarded by `src/desk/gl/__tests__/iconCell.test.ts`; values that are
numbers live in `src/desk/gl/sceneModel.ts` and nowhere else. The
reference mindset is Workbench 2.0: an icon is a live handle, not a
mascot.

## The cell

- Art is **64×64 pixel art, rendered 1:1** — never fractionally
  scaled, never tilted, never size-jittered. Integer-true or absent.
- Every kind renders in the **same cell**: 80px selection box, art
  centered, two-line label beneath at the label type size. No kind
  gets a bigger picture; importance is expressed by state, never by
  scale.
- Distinct **silhouette per kind** (cassette, page, crystal, drawer,
  cartridge, avatar…). Color supports the silhouette; it never
  substitutes for it — forty objects must sort by shape at a glance.
  A directory is a drawer.

## States are images

- Every sprite ships as a **set on disk**: `<name>.png` (rest),
  `<name>_sel.png` (selected: brightened + 1px light rim),
  `<name>_stale.png` (desaturated, dimmed). Derived deterministically
  by `scripts/gen-sprite-states.py` — rerun it after adding any base
  sprite; the guard fails on a missing state file.
- Selection is the CELL: the box fill + outline, the lit image, and
  the label inverting onto an accent chip — three cues, one state.
- Runtime filters may never substitute for a state image.

## Badges

- A badge exists only when a **named live field** feeds it (the
  audited map in `pm/roadmap/holdspeak/phase-105-workbench/
  research-badge-source-map.md`). A decorative badge is the mascot
  problem, smaller. Absent data renders as absence — never zero,
  never a guess.
- Anchors: needs-you top-left · freshness tick top-right · member
  count bottom-right · posture marks bottom-left. Badges anchor to
  the **art bounds at rest** and the **box bounds when selected**.
- Counts and marks only. A badge that needs a sentence is a card's
  job.

## New art (the Pixellab recipe)

Prompt discipline: "small crisp OS desktop icon of <thing>, 48px
pixel art, muted <kind-glow> and slate palette, single light source
from top-left, clean dark outline, flat readable silhouette, Amiga
Workbench 2.0 icon style, no background" — then pad to the 64px
canvas, pick from the candidate pack against THIS document (reject
mushy silhouettes and missing outlines), bank under
`public/desk/sprites/`, rerun the state script.

## System chrome sprites (HS-110-02)

Every system chrome element that is NOT text follows the icon
family's art language. They live under `public/desk/sprites/system/`
and are registered in `src/desk/systemSprites.ts`.

### Sizes

| Element | Size | Notes |
|---------|------|-------|
| Dock launchers | 32×32 | Speak, Meetings, Agents, Settings |
| Window gadgets | 16×16 | Close, Minimize, Maximize |
| Menu glyphs | 16×16 | HoldSpeak mark, bell, search lens |
| RecordOrb | 48×48 | The one "hot" element on the shelf |
| Backdrop tile | 64×64 | Seamless, muted crosshatch pattern |

### Prompt discipline (system chrome)

Same palette (Signal orange `#ff6b35` + slate greys `#0e0f13` to
`#242833` + paper whites `#767e8d` to `#f2f3f5`), same top-left
light source, same clean dark outlines. The style reference for
generation is always an existing icon family sprite (e.g. cassette).

### States

- Gadget rest: muted (55% opacity)
- Gadget hover: full opacity (the cluster-hover reveal)
- Gadget active: brightness 1.3
- Dock sprite hover: brightened (matching the icon `_sel` treatment)

### The rule

System GRAPHICS are pixel art; system TEXT is the type scale. No
text-as-graphics (Unicode dingbats) and no graphics-as-text.
