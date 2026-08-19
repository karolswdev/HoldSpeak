# HS-140-05 — The quiet return

- **Project:** holdspeak
- **Phase:** 140
- **Status:** done
- **Depends on:** 140-02, 140-03, 140-04
- **Unblocks:** 140-06
- **Owner:** delegated Terra worker; orchestrator adjudicates

## Problem

Progressive disclosure is only honest if the product returns cleanly and opens
into something worth using. Success and Continue later must apply the robust
default pack, then restore the normal Chair without losing the result,
replaying onboarding, or revealing controls that do nothing.

## Scope

- **In:** keep the mounted first-value composition after transcript success so
  its local editable draft and finishing actions remain; before completing
  onboarding or Continue later, invoke ordinary desk seed and refresh normal
  data; only then persist completed/dismissed disposition; keep an in-place
  Retry if furnishing fails so reload remains in first-value mode; restore
  Chair, lanes, Floor, dock, and launchers; every shown hero action opens a
  surface or names refusal.
- **Out:** restructuring normal lanes, changing open posture, Dashboard Door
  features, deleting `/welcome` compatibility, a second bootstrap service.

## Acceptance criteria

- [x] Continue later performs ordinary seed before persisting dismissal, then
  restores normal Chair and remains dismissed after reload.
- [x] Transcript arrival records `transcript_received` but does not complete
  onboarding or unmount before ordinary seed and the owner's finishing choice.
- [x] Completion persists only after ordinary seed succeeds; reload can never
  enter normal Chair with an unattempted default pack.
- [x] Ordinary seed respects live edits and tombstones from any earlier partial
  attempt; it does not force-restore defaults.
- [x] Furnishing failure stays in the current composition with one Retry and
  does not claim the normal product is ready.
- [x] A kept note is visible after the transition alongside the default pack.
- [x] Chair lanes, Floor, dock, and launchers return exactly once.
- [x] Every visible returned hero action opens its surface or shows refusal.
- [x] Existing deep links open and are not trapped behind first-value mode.

## Test plan

- **Web integration:** completion/defer/reload with seed success/failure,
  missing-default repair, draft preservation, deep links, no duplicate chrome,
  hero action feedback.
- **Python:** onboarding completion plus default-pack presence is retry-safe and
  never overwrites owner edits.
- **Local browser:** both exit paths at both widths, furnished before reveal.

## Notes

Do not auto-dismiss when transcription arrives; the owner chooses what to do
with the sentence. Do not display a fake progress tour while seeding; this is a
small local idempotent operation with an honest failure state.
