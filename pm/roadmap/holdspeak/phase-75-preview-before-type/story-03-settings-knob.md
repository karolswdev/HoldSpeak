# HS-75-03 — The settings knob (cockpit config)

- **Status:** done
- **Severity:** MED
- **Depends on:** HS-75-01
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## What

(See the phase status doc's exit criteria row for HS-75-03 — the scaffold
keeps the contract there; this file carries the build notes and the Done
record.)

## Test plan

- Story-specific tests per the exit criteria row; the full suite green at
  ship; every proof read, not assumed.

## Done

Shipped. The Voice-section checkbox (searchable, the em-hint idiom); the
settings PUT carries the field; and the round-trip test caught a REAL
bug — Config.load's explicit dictation constructor dropped the field, so
the knob would silently revert on every restart. Fixed; GET→PUT→GET
proven on the real routes. 8/8; suite 3088/37. See
[evidence-story-03.md](./evidence-story-03.md).
