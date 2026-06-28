# HSM-20-01 — The `DeskCamera` foundation (one width authority + the lane helper)

- **Project:** holdspeak-mobile
- **Phase:** 20
- **Status:** done — **leads the phase.** Every other story asks this story's camera.
  (Sim-proven; device walk deferred to 20-05.)
- **Depends on:** nothing (it consolidates what ships today).
- **Unblocks:** 20-02 (the desk reads the camera), 20-03, 20-04 (forms read the camera).
- **Owner:** unassigned
- **Evidence:** `evidence-story-01.md`.

## Problem

There is no single answer to "how wide are we." Compact adaptation is one ad-hoc check
(`DeskDioramaStage.swift:3085` `let compact = w < 500`), the hidden-title check is a second
(`:2977` `... && w >= 500`), and two views read `UIScreen.main.bounds` directly (`:2035`, `:3546`)
— which **lies in iPad split-view** (the screen is wide; your slice is narrow). Adding more
`w < 500` checks per screen would multiply this debt across ~20 views and still break on
split-view and rotate. The vision is explicit: introduce ONE width authority and *delete the
strays* (`EXPERIENCE-VISION-2026-06-27.md:128`).

## The design

1. **`enum DeskCamera { case wide, narrow, lane }`** — the one authority.
   - Derive it from **`@Environment(\.horizontalSizeClass)` FIRST, geometry width SECOND.**
     `.compact` size class ⇒ `.lane` (this is the only correct iPhone-vs-iPad-split-view signal);
     a `.regular` class with width below a tablet-split threshold ⇒ `.narrow`; otherwise `.wide`.
     Width alone is a tiebreaker, never the primary signal.
   - Plumb it once: read `horizontalSizeClass` + the top `GeometryReader` width at the `DioStage`
     root and pass a `DeskCamera` down (an `@Environment` key or an explicit parameter — pick one
     and use it everywhere). Do NOT re-derive width per view.
2. **A lane card-sizing helper** that extends the in-world card pattern shipped this session:
   a width-relative cap, e.g. `func laneWidth(_ ideal: CGFloat, in width: CGFloat, margin: CGFloat
   = 16) -> CGFloat { min(ideal, width - 2*margin) }`, so a `width: 380` card becomes
   `min(380, width − 32)` on lane and is unchanged on wide. This is the single helper 20-02/04 use
   to clamp every fixed card.
3. **Delete the strays** (verified targets):
   - `:3085` `let compact = w < 500` → `camera != .wide`.
   - `:2977` `... && w >= 500 ? 1 : 0` → `camera == .wide`.
   - `:2035` `.frame(height: UIScreen.main.bounds.height * 0.62)` → use the `GeometryReader` height.
   - `:3546` `let b = UIScreen.main.bounds` → the camera's geometry.
   After this story, `grep -n "UIScreen.main.bounds\|w < 500\|w >= 500" App/**/*.swift` returns
   **only** the `DeskCamera` derivation site.

## Scope

- **In:** the `DeskCamera` enum + its derivation + plumbing; the `laneWidth` helper; deleting the
  four strays; the existing rail-collapse behavior re-expressed through the camera (byte-equivalent
  rendering on iPad — no visual change at `.wide`/`.narrow`).
- **Out:** the lane card column (20-02); the pull-out migration (20-02); any new screen layout.
  This story changes *who decides width*, not *what the lane looks like*.

## Proof

- `swift test` green; the iPhone-sim AND iPad-sim `xcodebuild` both green (§6 of the handover).
- iPad sim screenshot is **visually identical** to `main` at `.wide` and `.narrow` (this is a
  pure consolidation — prove you broke nothing).
- The `grep` above returns only the derivation site.
- Device proof deferred to 20-05.
</content>
