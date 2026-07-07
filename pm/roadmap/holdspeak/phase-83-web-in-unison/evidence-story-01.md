# Evidence — HS-83-01: ground this ask, on the web composer

**Date:** 2026-07-07. **Verdict: done.**

## What shipped

- `web/src/desk/grounding.ts` — the data layer: `hubGrounding` (refs-only wire;
  any transcript toggle upgrades `expand` to `full`), `groundingTokens` (the
  ≈4-chars/token estimator over REAL fetched lengths), `groundingLabel`,
  `groundingReceiptRows`, `fetchGroundingMeeting` (GET
  `/api/meetings/{id}` + `/{id}/artifacts`; digest defaults on when intel
  exists, transcript is opt-in — the iPad defaults).
- `web/src/desk/components/GroundingSection.tsx` — the inline expandable
  "Ground this ask" section on the composer: meeting rows, per-meeting
  digest / transcript / per-artifact chips, the live gauge bar with the
  ok/warn/bad tones, the past-budget refusal line.
- `AskPanel.tsx` — the section wired under Runs-on; the Ask button refuses
  while over budget; grounding receipt rows join the pinned print context so a
  kept grounded ask names its grounding; the budget is the picked profile's
  `context_limit` (16,384 fallback).
- `ask.ts` — `runAsk` gains `grounding` (refs only) and returns the hub's
  folded `context_ids/titles`; a 400 renders the hub's error naming
  `unknown_ids` verbatim.

## Receipts

- **Vitest:** 49/49 (`npx vitest run src/desk`) — new `grounding.test.ts`
  locks the wire shape, expand derivation, gauge math (ON-only, real lengths),
  labels, receipts, fetcher defaults, the `runAsk` grounding passthrough +
  folded lineage, and the verbatim refusal. `ask.test.ts` re-pinned for the
  two new result fields.
- **The rig** (`scripts/screenshot_hs83_grounding.py`, the house Playwright
  pattern — real app, scratch DB, capturing engine): drove lasso → composer →
  picker → toggles → grounded run, and ASSERTED the treatment — the captured
  `user_prompt` contains `[MEETING: Q3 kickoff — 2026-07-06]`, the transcript's
  codename, `[ARTIFACT: Decisions — Q3 kickoff]`, and the lasso'd card's
  material, while the request body carried ids only. Gauge and chip text
  asserted non-lying.
- **Screenshots:** `screenshots/hs-83-01-picker.png` (picker + gauge + chips),
  `screenshots/hs-83-01-grounded-print.png` (the grounded answer wearing the
  honest badge).
- **Live .43 control-vs-treatment:** the identical wire was proven against the
  live hub → 192.168.1.43 llama.cpp on 2026-07-06 (ungrounded ask guesses
  "Mesh"; grounded-by-reference ask answers "BLUE LANTERN"; ghost id refuses
  `{"error": "grounding ids not on this hub", "unknown_ids": ["ghost123"]}`) —
  receipts in the HSM-15-12 story header. The full in-browser live walk is
  HS-83-04's closing beat.

## Notes

- The hub half was already merged (#277) — this story added no route changes,
  so `docs/api-surface.json` is untouched.
