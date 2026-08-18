# HS-140-03 — Recovery stays here

- **Project:** holdspeak
- **Phase:** 140
- **Status:** backlog
- **Depends on:** 140-02
- **Unblocks:** 140-04, 140-05
- **Owner:** delegated Terra worker; orchestrator adjudicates

## Problem

Microphone or transcription trouble can turn first use into a tour of Setup
and Models. Recoverable failures should recover in place; configuration should
appear only when it is the exact next action.

## Scope

- **In:** audit `DICTATION_FAILURES` for permission denied, missing local
  transcription, no speech, timeout/transcription failure, and retained-audio
  retry; give each plain copy and one next action; retain typed fallback; pass
  `retainScope: "first-words"` into the existing stream session and prove the
  real failure→reload→retry path; route setup-needed failures through the
  existing `openSurfaceOr("configure-setup", "/setup")` seam with honest,
  generic Setup wording unless a real failure-specific destination exists.
- **Out:** setup wizard, cloud/key enrollment, new failure enum, router redesign,
  or swallowed refusals.

## Acceptance criteria

- [ ] Permission denial names the browser/OS permission repair in place.
- [ ] No speech offers Retry without claiming transcription failed.
- [ ] `FirstWords` passes `retainScope: "first-words"`; retained audio survives
  reload and Retry does not require re-recording.
- [ ] Unavailable local transcription offers one honest Setup action through
  the existing setup surface; no nonexistent deep-link is implied.
- [ ] The textarea remains usable as typed fallback in every failure state.
- [ ] Every action makes progress, shows a receipt, or names a refusal.

## Test plan

- **Web unit:** one case per failure contract plus a real stream-stop failure
  writing `first-words` pending audio, reload/retry, and typed fallback.
- **Local browser:** microphone denied, no-speech, and unavailable transcription
  at both widths.

## Notes

Setup is a recovery action, not part of learning to dictate.
