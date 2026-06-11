# Evidence — HS-56-03: The actuator card (the marquee; absorbs G)

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

## 1. What shipped

**Backend (three small seams, the invariants untouched):**
- The aftercare file-issue route now broadcasts `actuator_proposed` with the
  identical wire-safe shape the live in-meeting path uses (the human
  `preview` only — **the machine payload never rides the broadcast**,
  asserted by test).
- A `rejected` decision broadcasts `actuator_result` from the decision route
  (an approval broadcasts nothing — approving records a decision; execution
  is the executor's separate job, exactly like the dashboard).
- `ActuatorExecutor` gains an optional `on_result` observer fired on the
  `executed` and `failed` transitions (incl. the parity-mismatch failure) —
  **purely observational**: an exploding observer never breaks the audited
  transition it reports on (tested).

**Frontend (`qlippy-events.js`):** consumes `hs-broadcast`:
- `actuator_proposed` → the sticky `alert` card (never auto-expires, never
  auto-decides): "A decision needs you", `target · action · reversible`, the
  preview, and **Approve / Decline** sending the **byte-identical request
  the dashboard sends** (`POST …/proposals/{id}/decision`,
  `JSON.stringify({ decision })` — both asserted against
  `dashboard-app.js`). A failed POST presents an error card.
- `actuator_result` → `executed` (approve sprite + check glyph, "Done —
  {action}"), `failed` (error + x, the error detail, "Nothing egressed."),
  `rejected` (decline + x, "Declined").
- **The G panel** on the actionable card, verbatim-checkable: *Data used*
  (the preview; the exact machine payload stays on this machine until
  approval), *does anything leave* (named target, nothing sent before
  approval), *your controls* (Approve / Decline / dismiss + the dashboard
  remains).

The dashboard investigation settled the mirroring question: **the
dashboard's Approve performs only the decision POST** ("recorded; nothing
runs without it") — so the card does exactly that, nothing more.

## 2. Live dogfood (real proposal, real socket, real audit)

`dogfood_story03.py` — no mocks in the chain: a seeded meeting with an
accepted action → the real aftercare API files a real GitHub-issue proposal
→ its **real broadcast** slides the card out on the connected presence page:

```
PASS  the real aftercare proposal slid the card out with the three privacy answers
PASS  Approve recorded the audited decision (status=approved, by='web-user') — no side effect performed
PASS  Decline → the real actuator_result broadcast presented the Declined card
PASS  zero page errors across the whole run
RESULT: PASS
```

Screenshots reviewed: `story03-real-proposal-card.png` (alert Qlippy with
the composited bang glyph, "github · create_issue", the real preview "Open a
GitHub issue in acme/widgets…", the full privacy panel, Approve/Decline) and
`story03-declined-card.png`.

## 3. Tests + suite

`tests/integration/test_actuator_presence_broadcasts.py` — 4 tests: the
aftercare broadcast (wire-safe, no payload), rejected-broadcasts /
approved-doesn't, the executor observer on executed + failed + the
exploding-observer guarantee, and the dashboard-parity + privacy-marker
page locks.

```
$ uv run pytest -q tests/integration/test_actuator_presence_broadcasts.py
4 passed in 0.81s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2582 passed, 17 skipped in 78.71s (0:01:18)
```

(2578 → 2582.) Build clean; the existing executor/never-egress tests
untouched and green.
