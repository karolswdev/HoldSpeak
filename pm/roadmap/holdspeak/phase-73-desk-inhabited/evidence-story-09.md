# Evidence — HS-73-09 — Docs + the locks

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **The entry points now tell the truth** (the Phase-64 lesson — feature
  docs must touch the entry points): `docs/GETTING_STARTED.md`'s arrival
  section and route table speak the Desk — a returning user lands on the
  Desk (objects in a spatial world; tap to open in place, drag onto a
  zone to file, the orb to record, the rail to ask), the four-door tour
  became "the Desk plus three rooms reached from its menu", and `/`'s
  route row reads "The Desk: your primitives as a spatial world".
  Checked and already true elsewhere: `README.md` never toured pages by
  name; `welcome.astro` never says "Home"; `ARCHITECTURE.md`'s only
  "desk" mentions are the iPad relay routes.
- **The mechanical locks** (`tests/unit/test_desk_locks.py`, 5 tests,
  grep-shaped and instant):
  1. No dialog takeovers on the desk tree (`aria-modal`,
     `role="dialog"`).
  2. No browser microphone on the desk tree (`getUserMedia`) — the orb
     drives the hub recorder.
  3. No privacy narration in desk UI surfaces — the banned phrases
     ("leaves your machine" etc.), with `setup.ts` as the single allowed
     home of the canonical egress-badge strings (POSITIONING canon,
     the Phase-62 REFUSE pattern).
  4. The positions contract stays bare: the literal `"hs.diorama.pos"`
     present, `zustand/middleware` absent (a persist envelope would
     break the legacy map byte-compat).
  5. The front door stays the Desk with the first-run guard inline
     (`client:only="react"` + the `/api/setup/status` →
     `/welcome`/`/setup` guard asserted in `index.astro`).

## Verification artifacts

- The locks: **5 passed**.
- The documentation guards (voice/dash/canon sweeps): **85 passed, 2
  skipped** on the updated prose.
- Full suite at ship: **3071 passed, 37 skipped, 0 failures** (3066 + the
  5 new locks).

## Acceptance criteria — re-checked

- [x] Entry points updated where they lied; verified-unchanged entry
      points listed explicitly.
- [x] The no-modal / no-mic / no-prose / positions / front-door rules are
      tests now, not memories.

## Deviations from plan

- None of substance; the lock scoping (desk tree, with `setup.ts` as the
  badge-string home) follows HS-73-08's honest-scoping note.

## Follow-ups

- HS-73-10: the closeout walk (the phase's exit ritual).
