# HS-151-07 — The fired-session admission (the attended leg's rider)

- **Project:** holdspeak
- **Phase:** 151
- **Status:** done
- **Depends on:** HS-151-06 (its attended leg exposed this)
- **Unblocks:** the attended leg's completion
- **Owner:** unassigned

## Problem

The attended leg descended a four-defect admission ladder and hit
bedrock: **live meeting sessions cannot freeze their transcription
route on any HOME without speech assignment heads — for ANY
principal, owner included.** Empirically proven (probe recorded in
the phase log): an authenticated owner POST /api/meeting/start on a
wired fresh HOME refuses `no_assignment`; the meeting records and
persists EMPTY. Fresh installs seed zero assignments; speech models
never register as profiles (no assignment is even creatable); the
speech stack's own capability-only owner mechanism
(freeze_capability_only_owner_route_in_transaction — the parentless
warm's seam, speech_session/session.py:1233) is NOT what the
meeting bundle's transcription route resolves through
(intel_admission.py:161-183 routes speech.transcribe like a model
capability). Defects #7 (out-of-scope wiring, FIXED),
#8 (contract-name probe, FIXED), #9 (SCHEDULER unadmittable,
PARTIALLY addressed: SERVICE principal + sealed
scheduled-recording@1 policy + four-capability wiring shipped),
#10 (this story's core).

## Scope (counsel rules the design first)

### In

1. The meeting bundle's TRANSCRIPTION (and derived preload) route
   freezes via the speech stack's capability-only owner mechanism
   — the same lawful seam wake and the parentless warm use — for
   OWNER sessions AND for the SERVICE scheduled-recording lane
   (the owner armed the schedule; transcription is local-only).
   Counsel rules the exact seam.
2. The intel members keep their assignment resolution (they ARE
   model capabilities); Design-A-style honesty if any optional
   member cannot freeze is counsel's question.
3. Pins: a fresh-HOME owner live session transcribes; a
   conductor-fired session transcribes; empty-transcript-on-
   refusal can never again be silent (the refusal must surface).
4. The attended leg re-runs green after; story 06 completes.

### Out

- Registering speech models as Model Library profiles (a future
  arc if counsel prefers that shape).

## Acceptance criteria

1. Counsel-ratified design; fresh-HOME live capture transcribes
   under owner AND fired sessions; pins both.
2. The attended leg green end-to-end with the honesty header.

## Test plan

Focused admission/bundle suites + the pins + the attended rig.
