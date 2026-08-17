# HS-135-11 — The capture hero

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** HS-135-05
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

The product's founding gesture has no home on the front door. The
five-jobs baseline: Record is one click but voice can't trigger it
(F5); Ask AI is the right door for questions but hidden behind Cmd+I
while Speak's cockpit misleads (F2). The hero is the Chair's heart —
the ONLY place (with the Record Orb) that wears the accent gradient.

## Scope

### In

Per L2/L4/L8 and the counsel's F2/F5 scoping:

- The hero: the mic/record instrument centered in the Chair's hero
  region (TransportKey species at hero scale, accent gradient, L1
  pressed grammar, sprite states where the existing mic sprites
  apply). TAP = start meeting recording (the existing Record Orb
  verb); recording state lives IN the hero (elapsed, stop verb) and
  stays consistent with the dock orb.
- Voice trigger: with the hero's mic open, a spoken "start meeting"
  (existing MicButton transcription → command match, no new wake-word
  system) starts recording; the match set is small and named in code.
- Ask AI one tap from the Chair: a hero-adjacent verb (Button species)
  opening the existing Ask AI panel; the hero does NOT merge
  Speak/Ask (Wave 2) — it routes.
- Honest labels: the hero names what a tap does (Article VI).

### Out

- Speak-room changes; the two-doors merge; wake words; TODO capture
  (Wave 2).

## Acceptance criteria

- [ ] Tap starts a real recording; hero shows live state; stop works;
  dock orb agrees (tests + shots).
- [ ] Spoken "start meeting" starts recording (test with transcription
  fixture).
- [ ] Ask AI opens in one tap from the Chair (test).
- [ ] Accent gradient appears ONLY on hero + Record Orb (style grep
  test per law-book addition 4).

## Test plan

- `cd web && npx vitest run` — hero suite + recording/mic suites
  touched; live capture proof rides HS-135-13.
