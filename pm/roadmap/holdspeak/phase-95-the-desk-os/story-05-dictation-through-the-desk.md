# HS-95-05 — Dictation through the desk

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-02, HS-95-04
- **Unblocks:** HS-95-08 (its exits count toward the final sweep)

## Problem

Dictation is the product's founding act, and it is the desk's loudest
escape hatch: DeskStartActions "Dictate", the DeskChrome room, the Pullout's
"dictate about subject", and the DeskToolInspector's project-context link
all throw the user onto `/dictation` — a flat page under alien chrome. The
desk's own `MicButton` speak-to-fill proves the runtime works in-world; the
full surface (session, corrections, journal, project context, runs-on) is
what's missing.

## Scope

- In:
  - the DictationPage core (per the HS-95-04 pattern) hosted in a desk
    window: live session, preview-before-type where enabled, corrections,
    journal/review, project-context picker, `RunsOnPicker` — full parity
    with the flat page;
  - subject handoff in-world: "dictate about this" on a Pullout passes the
    subject as the context prop — the window opens pre-scoped to the object,
    no URL encoding;
  - every dictation escape hatch rewired to open the window in place:
    DeskStartActions, the DeskChrome room, Pullout, DeskToolInspector;
  - the flat `/dictation` route kept working through the thin wrapper (its
    end state is HS-95-08's call);
  - mic state honesty: the window and the in-world `MicButton` share one
    recording/permission state — two surfaces never both claim the mic.
- Out:
  - dictation runtime/pipeline changes (DIR-01 territory);
  - the wake-word and voice-command layers (untouched);
  - LivePage/meeting recording (HS-95-06).

## Acceptance criteria

- [ ] The dictation window carries the full flat-page capability from the
      shared core; a real dictation lands text end to end from inside the
      window against the real hub.
- [ ] "Dictate about this" from a Pullout opens the window scoped to that
      subject with the grounding visibly attached, without leaving the desk
      or touching the URL.
- [ ] No desk surface links to `/dictation` anymore (grep-verified across
      `web/src/desk/`); each former exit opens the window.
- [ ] `/dictation` still renders for deep links via the wrapper.
- [ ] Mic arbitration: starting dictation in the window while a speak-to-fill
      is armed (or vice versa) resolves to one owner with an honest refusal
      or handoff — no double capture.
- [ ] The window behaves as a full shell citizen: dock presence, minimize
      (session-preserving), bottom-sheet form at 393px.

## Test plan

- `npm --prefix web test` — core-mount tests, subject-handoff prop tests,
  mic-arbitration unit tests.
- Live proof against the real hub with the real Whisper runtime: a spoken
  sentence lands from the window (the standing bar: real metal, not
  seeded simulation).
- Playwright walk: open from each former exit point, assert scope, at 1440
  and 393.

## Implementation direction

- The core keeps `useResource`; only the subject scope rides the context
  prop. If the journal needs desk-store coordination, add a minimal
  selector, not a second store.
- Reuse `lib/speakToFill`/`lib/dictationRecovery` state as the single mic
  authority; do not duplicate recorder state in the window.
- Minimize must not kill an armed session silently — parked-but-armed shows
  in the dock (icon state), consistent with runtime presence rules.

## Evidence required

- captured test runs;
- the live real-mic proof (command + output via evidence capture);
- before/after: the four former exits, each opening the window (screenshots);
- the grep sweep output showing zero `/dictation` links in `web/src/desk/`.
