# HSM-11-04 — Suspend / resume + background audio

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** backlog
- **Depends on:** HSM-2-04, HSM-4-02
- **Owner:** unassigned

## Problem

Phones suspend apps, lock screens, and take calls mid-meeting. The classic mobile
recording bug is losing the tail of a recording when the app backgrounds or the
system reclaims it. The charter's suspend/resume scenario exists to prove the
audio + persistence lifecycle survives this.

## Scope

- **In:** behavior across app suspend/resume, screen lock, and OS reclaim during
  an active recording — verifying no audio is lost and the session resumes cleanly,
  building on Phase-2 capture lifecycle and Phase-4 crash recovery; the
  background-audio posture proven (whatever Phase 2 decided).
- **Out:** the 4-hour endurance bar (HSM-11-01). Thermal/battery (HSM-11-03). New
  features.

## Acceptance criteria

- [ ] Backgrounding/locking the app during an active recording loses no audio; the
      recording continues or cleanly pauses+resumes per the configured posture.
- [ ] An OS reclaim (app killed while suspended) leaves the recorded-so-far meeting
      intact and reopenable (leans on Phase-4 recovery).
- [ ] Resuming the app returns to a coherent state (no duplicate/orphaned session).
- [ ] The proven posture (foreground-only vs. background recording) is stated in
      evidence.

## Test plan

- Manual / device: record, then background / lock / take a call / force-suspend;
  resume and verify the tail is intact; kill-while-suspended and verify recovery.
- Unit: the session-lifecycle state machine (active→suspended→resumed/reclaimed)
  tested over its transitions.

## Notes / open questions

- If the product needs screen-off recording but Phase 2 chose foreground-only,
  this scenario is where that gap surfaces — escalate the background-audio posture
  to the owner (phase risk).
- Build on Phase-4 crash recovery rather than reinventing it; suspend-then-kill is
  a crash-recovery case with a backgrounded prelude.
