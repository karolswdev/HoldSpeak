# HANDOVER — 2026-06-30 — Desk sprite library: variety + a per-object icon picker

Owner: "why did we not create a lot more resources (cassette, note, …) so we could at random generate
those for those kinds of objects? Better yet, let the user select which icon to use."

Two things shipped, both realized:

## 1. The system (`App/MeetingCapture/SpriteStore.swift`)

- `DeskSprites.variants(kind)` — the per-kind sprite pool (only lists sprites that actually ship as
  `<name>.png`; a missing one would render `DeskSprite`'s placeholder). Add art = drop the png in
  `App/`, bundle it in `gen-meeting-capture.rb`, append it here.
- `SpriteStore` (a plain UserDefaults-backed enum, NOT an `ObservableObject` — so the struct primitives
  can read it from their `glyph` getter without an `@MainActor`/Sendable cascade; the Swift 6 build
  rejected a `static let shared` mutable singleton):
  - VARIETY: `sprite(id:kind:fallback:)` returns an explicit override, else a **stable** variant
    `pool[abs(djb2(id)) % count]`. Uses a djb2 hash, NOT `String.hashValue` (which is seeded per
    launch and would reshuffle every icon on every cold start).
  - CHOICE: `chosen(id)` / `set(id,to:)` persist a per-object override.
- Primitives consult it: `MeetingPrimitive` / `NotePrimitive` / `KBPrimitive` `.glyph` →
  `SpriteStore.sprite(...)`. The desk re-renders when the picker closes (a state change), so glyphs
  recompute against the fresh value (no observation needed).
- The picker: `DioIconPicker` (an in-world gallery: an "Auto" cell that clears the override + every
  variant). Opened from the pull-out header sprite (a pencil badge hints it's tappable,
  `DioPullout.onChangeIcon`) and from the lane long-press menu ("Change icon"). Gated to
  `spriteKinds = [.meeting, .note, .kb]`.

## 2. The art (PixelLab MCP, matched to the existing style)

Generated with `create_1_direction_object` (top-down, 128px, 4-candidate review). The DEFAULT PixelLab
style matched the existing sprites well — no base64 style-reference needed (which would have been
token-heavy). Picked the best, downloaded the rotation PNGs (curl needs
`dangerouslyDisableSandbox`), bundled, registered, dismissed the review jobs.
- **cassette3/4/5** — "SIDE A", "MIX TAPE #3", "DANCE CLASSICS" (meetings now have 5 tapes).
- **note2/3/4** — pink / green / blue sticky notes (+ the original yellow).
- **crystal2/3/4** — ruby / emerald / amethyst clusters (+ the original blue).

Sim-verified: a desk of 6 meetings shows 6 different cassettes; the picker shows "Choose an icon" with
Auto + all five tapes. (Notes/KBs use the identical proven path.)

## Next (same recipe)

More kinds (artifacts/outputs, KBs already done), or per-meeting "shuffle" affordance. Drop png →
bundle in gen line ~61 → append to `DeskSprites.variants`.
