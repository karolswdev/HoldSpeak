# HS-136-04 — Docs, walk, and close

- **Project:** holdspeak
- **Phase:** 136
- **Status:** done
- **Depends on:** HS-136-03
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The feature is not shipped until an entry-point reader can find it and
until a live recording has actually fired on real hardware and left its
receipts. Unit tests stub the audio seam by design; the walk cannot.

## Scope

### In

- **Docs at the entry points** (not a new orphan page): USER_GUIDE gets
  a "Schedule a recording" section (create, one-shot vs recurring,
  duration, the countdown, cancel); SECURITY documents the SCHEDULER
  principal, bounded delegation on enable, the IV.3 countdown, and the
  missed/refused receipts; ARCHITECTURE gets a paragraph on the
  conductor and the `_start_meeting` seam.
- **The live walk on real metal** (per house rule: prove on the real
  hub / `.43`, not seeded): create a schedule due in ~1 minute; watch
  the countdown fire; confirm a **real** capture starts and **auto-stops**
  at its duration; confirm receipts for enable, fire, and stop. Then
  the two honest-failure legs: a fire refused because the mic floor is
  held (leaves a refusal receipt), and a missed fire (leaves a missed
  receipt). Both widths where a surface is involved.
- **A reusable harness** in `scripts/` so the walk re-runs.
- **The counsel** (mandatory, fresh `claude-opus-4-6[1m]`): the final
  summary, the evidence, and every judgment call — especially the
  auto-start-via-countdown reconciliation of Article IV.3 — reviewed
  with "what would you not ratify."
- **The final summary** and the operating-cadence updates (README
  current-phase + last-updated, the phase status doc, story rows).

### Out

- New product behavior; this story is proof, docs, and closeout only.

## Acceptance criteria

**AMENDMENT (owner ruling 2026-08-17):** the real-mic-fire metal walk
is **deferred to a documented follow-up** — the owner chose to skip
firing this machine's microphone. The phase closes on the surface
screenshot walk (a real live-product walk, not unit tests alone), the
ten invariants with tests, and the adversarial verification pass. The
end-to-end real-hardware fire is recorded as an open item for the
sitting. The owner may overrule this at the sitting.

- [ ] USER_GUIDE, SECURITY, and ARCHITECTURE updated at their existing
  entry points (no orphan page).
- [x] The live walk shows the surface end to end — done in HS-136-03
  (`scripts/schedule_walk_hs136.py`, 1440 + 393, create control +
  SCHEDULED lane entry, zero console errors). ~~A real scheduled
  recording firing on real hardware with captured receipts~~ — DEFERRED
  per the owner ruling above; documented as a follow-up.
- [x] The refusal (mic held) and missed (hub-down) legs are proven by
  the invariant unit tests (I4, VI.1) and the adversarial pass, not the
  metal walk — DEFERRED with the fire proof above.
- [x] The walk harness is checked into `scripts/`
  (`schedule_walk_hs136.py`) and re-runs.
- [ ] The full suites are green (or every failure name-diffed against
  the pre-phase baseline and ledgered); the counsel's verdict is
  recorded for the sitting.

## Test plan

- Full suite the way CI sees it (isolated HOME, `-n auto`), per
  CLAUDE.md, read before any flip.
- The live walk captured through `.githooks/dw evidence capture`.
