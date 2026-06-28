# Evidence — HSM-20-01 — The `DeskCamera` foundation

**Date:** 2026-06-27. **Branch:** `holdspeak-mobile/phase20-01-deskcamera`.

## What shipped

One width authority (`DeskCamera`), derived from `horizontalSizeClass` first and geometry width
second, with the four strays folded into it.

- **New:** `apple/App/MeetingCapture/DeskCamera.swift` — `enum DeskCamera { case wide, narrow, lane }`
  + `resolve(sizeClass:width:)` (size class first; `.compact ⇒ .lane`, else `width < 500 ⇒ .narrow`
  else `.wide`) + `isWide`/`isLane`/`railCollapses` + the `cardWidth(_:in:margin:)` lane clamp helper
  that 20-02/04 use to fit every fixed card into 390pt.
- **`DeskDioramaStage.swift`:**
  - `@Environment(\.horizontalSizeClass)` read on `DioStage`; `let camera = DeskCamera.resolve(...)`
    computed once per frame inside the body's `GeometryReader` (the single derivation site).
  - Stray `:2977` `w >= 500` (decorative title) → `camera.isWide`.
  - Stray `:3085` `let compact = w < 500` (rail collapse) → `camera.railCollapses`.
  - Stray `:3546` `let b = UIScreen.main.bounds` (summon demo) → the geometry `w`/`h`.
  - Stray `DioLiveTranscriptModal` `UIScreen.main.bounds.height * 0.62` → a local `GeometryReader`
    height (it had no root geometry).

The 500pt narrow/wide boundary was chosen deliberately to be **byte-equivalent** with the
`w < 500` / `w >= 500` checks it replaces, so iPad renders identically at `.wide`/`.narrow`. This
story changes *who decides width*, not *what the lane looks like* (that is 20-02).

## Proof

- `grep -rn "UIScreen.main.bounds| w < 500| w >= 500"` across the App target returns **only comment
  references** (the stray code is gone); exactly one `DeskCamera.resolve` call site.
- `swift test`: **381 passed, 8 skipped, 0 failures.**
- iPhone-17-Pro sim `xcodebuild`: **BUILD SUCCEEDED.** iPad-sim (same iphonesimulator product):
  **BUILD SUCCEEDED.**
- `screenshots/2001-ipad-wide.png` — iPad `.wide` renders the full diorama (decorative title shown,
  rail open) exactly as `main`.
- `screenshots/2001-iphone-compact.png` — iPhone `.lane` renders the compact diorama (title hidden,
  rail collapsed to the edge tab) byte-equivalent to the pre-change baseline.

Device proof deferred to HSM-20-05 (the gate). Until then the iPhone cell stays a forward
constraint.
