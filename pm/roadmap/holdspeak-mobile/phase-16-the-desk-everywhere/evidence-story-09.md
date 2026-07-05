# Evidence — HSM-16-09 (the Ask AI atom)

**Done 2026-07-04, sim-proven; the real-metal walk rides 16-06 per the story's acceptance.**

## The truth-up first

The resume survey's claim "zero Ask-AI code exists (grep-verified)" was **wrong** — the grep
missed the atom shipped under other names: `askBundle` (lasso → bundle bar), `DioRouteSheet`
(lens grid + prompt + `VoiceFillMic` + `RunsOnPicker`), the routing theater, and
`DioPrintedCard` (keep/bin). Recorded here so the correction is as loud as the claim.

## What this story actually built

1. **The full Ask lineage** (`apple/Sources/RuntimeCore/Desk/DeskRecords.swift`):
   `RunProvenance` grew `contextIds` / `contextTitles` / `prompt` with a decode-tolerant
   custom `init(from:)`; `OutputRecord` carries them through the structured wire
   (`context_ids` / `context_titles` / `prompt`, emitted only when present so recipe/chain
   provenance keeps the exact legacy shape) and renders one canonical `sources` row per
   lasso'd card plus the ask's own row. `runRoute` now stamps this provenance on BOTH the
   single-card route and the bundle ask, with `viaKind: "ask"`.
2. **Two egress-honesty bugs fixed** (`DeskDioramaStage.swift` `runAssembled` + the theater
   call site): both surfaces derived "where did this run" from the app-wide
   `InferenceConfigStore.isLocal`, ignoring the per-run profile override the sheet lets you
   pick — a cloud-profile ask printed a card claiming local. Both now resolve
   `resolveProfile(recipeProfileId:)` for THIS run; a cloud run's badge names the profile's
   real `egressHost`.
3. **Off the scrim**: `DioRouteSheet` now composes inside `DioAtelierPanel` (the 17-08
   posture — desk visible, tap-away cancels); `DioPrintedCard` lost its 0.7 black scrim and
   **prints from the AI core it ran through** (`birth` offset → spring into reading position).
4. The lineage row learned the ask glyph (`wand.and.stars`).

## Proof

- `swift test`: **467 passed / 9 skipped / 0 failures** including the new
  `testAskProvenanceRoundTrip` (full lineage through the wire and back; per-context sources
  rows) and `testRecipeProvenanceKeepsLegacyWireShape` (no ask keys on a recipe run — the
  golden-pin safety), plus the legacy-decode asserts (pre-Ask rows decode to empty, never
  throw).
- App simulator build green (`gen-meeting-capture.rb` → xcodebuild, iPad Air 13-inch (M4)).
- Live sim proof via three new `HS_DESK_ASK` affordances (selected / compose / printed),
  each driving the same state the taps drive — screenshots committed:
  - `screenshots/hsm-16-09-ask-selected.png` — the lasso'd cards + the bundle bar.
  - `screenshots/hsm-16-09-ask-compose.png` — the Ask panel off the scrim: lens grid,
    RUNS ON picker, speak-to-fill mic, honest On-device chip, the desk visible behind.
  - `screenshots/hsm-16-09-ask-printed.png` — the printed card wearing its lineage
    ("3 items → Distill"), the On-device badge, Bin / Keep on desk, the desk visible.
