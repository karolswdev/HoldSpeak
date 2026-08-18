# HS-140-04 — The quiet return

- **Project:** holdspeak
- **Phase:** 140
- **Status:** backlog
- **Depends on:** 140-01, 140-02, 140-03
- **Unblocks:** 140-05
- **Owner:** delegated Terra worker; orchestrator adjudicates

## Problem

Progressive disclosure is only honest if the product returns cleanly. Success
and Continue later must restore the normal Chair without losing the result,
replaying onboarding, or revealing controls that do nothing.

## Scope

- **In:** keep the mounted first-value composition after transcript success so
  its local editable draft and finishing actions remain; define/test exit after
  a finishing action and Continue later; accept that a reload after transcript
  success follows the already-completed server disposition into normal Chair;
  refresh setup state without a page ritual; restore normal Chair, lanes,
  Floor door, dock, and launchers; ensure every shown hero action opens a real
  surface or shows a named refusal.
- **Out:** restructuring normal lanes, changing open posture, Dashboard Door
  features, deleting `/welcome` compatibility.

## Acceptance criteria

- [ ] Continue later restores normal Chair and remains dismissed after reload.
- [ ] Transcript arrival marks server success but does not unmount the current
  composition before edit/finishing choice; a later reload may enter normal
  Chair from the durable completed disposition.
- [ ] A kept note is visible after the transition.
- [ ] Chair lanes, Floor, dock, and launchers return exactly once.
- [ ] Every visible returned hero action opens its surface or shows refusal.
- [ ] Existing deep links open and are not trapped behind first-value mode.

## Test plan

- **Web integration:** completion/defer/reload, draft preservation, deep links,
  no duplicate chrome, hero action feedback.
- **Local browser:** both exit paths at both widths.

## Notes

Do not auto-dismiss when transcription arrives; the owner must choose what to
do with the sentence.
