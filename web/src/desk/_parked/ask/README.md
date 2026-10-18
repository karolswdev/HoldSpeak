# Parked: the Ask AI card's tests

- `askPanelRunsOn.test.tsx` — the Ask AI card of HS-111-05 and the
  2026-10-17 composition: Keep / Bin, the drag-to-keep answer, `GROUNDED ON
  N OF M`, the Question fold, Edit question and the Run details receipt.
  Betterment Q4 ("One Ask window", DECISIONS #14) retired those faces: every
  Ask is kept as a thread, Save as note files an answer, Looked at replaces
  the grounding receipt. The kept behaviours (the Note passage handoff,
  Choose engine, a closed window abandons its wait) are proven in
  `web/src/desk/__tests__/ask.app.test.tsx`. Not collected (`_parked`).
