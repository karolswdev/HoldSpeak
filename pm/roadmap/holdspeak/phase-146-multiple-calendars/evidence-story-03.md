# Evidence - HS-146-03

- **Story:** HS-146-03 - The settings list editor (joy surface)
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T22:40:55Z

- **Command:** `zsh -c cd web && npx vitest run src/pages/cores/__tests__/SettingsCalendar.test.tsx 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 130e208ec0ffee2abaf627845c40246fa1be38e5

```text
 Test Files  1 passed (1)
      Tests  12 passed (12)
   Start at  16:40:56
   Duration  1.00s (transform 248ms, setup 40ms, import 343ms, tests 369ms, environment 178ms)
```

## Orchestrator triage note

Captured: the reworked SettingsCalendar vitest file (12 passed —
list-editor render, add/remove/toggle, per-source chips, refusal
rendering, `calendarSourceEgressChips` units). Orchestrator
verification on top: typecheck provenance 13 pre-existing / 0 new;
the `_calendar_subscription` retirement grep proof (zero reads in
SettingsCore/SettingsCalendar; two type-level declarations remain
honestly while the server still ships the legacy fact — story 04's
retirement); the worker's beauty pass (column proportions 2fr/5fr/
32px/max-content, the egress strip, the composed wrapper) verified
on real glass by the orchestrator's shot rig
(`assets/story-0304-shots/settings-editor-*.png`): the empty state
leads with one obvious + ADD SOURCE act, two sources render as clean
LABEL/URL/ON rows with mics and in-world remove. Shots eyeballed
before the flip; the formal owner set is story 05's.

Sweep note: the full close sweep is deferred to the next checkpoint
per the phase cadence; in-round glass = both door e2e files serial
green + the 7-leg walk (story-04 round) + this story's focused
suites.
