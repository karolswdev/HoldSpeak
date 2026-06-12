# Evidence — HS-62-01: The egress badge on Qlippy cards

**Date:** 2026-06-12
**Verdict:** done. Every Qlippy card now states its egress with one compact
badge; the privacy paragraphs are gone from the card layer entirely.

## What shipped

- **The shell** (`presence.astro` + `qlippy.js`): `#qlippy-privacy` (a
  paragraph) replaced by `#qlippy-egress` (a pill). The card contract
  gains `egress: {scope: "local"|"mixed"|"cloud", label?}`; the renderer
  maps scope → glyph (⌂ / ⌂+☁ / ☁) + the label (defaults "Local" /
  "Local + cloud" / "Leaves device"). Tones: local green, mixed/cloud
  orange (the "leaves the device" salience).
- **The cards** (`qlippy-events.js`): `privacyLine()` deleted. Proposal
  and executed-result cards → `cloud` with the target on the badge
  ("☁ slack" — the only information the old paragraph carried that
  mattered survives). Failed result → `local` "Nothing sent". Learned,
  aftercare → `local`. Wake preview → `local` "Local · not typed yet"
  (the not-typed state in three words instead of two sentences).
- **The reversed locks**: the Phase-56 verbatim three-answers lock
  (`test_qlippy_doc_states_the_guarantees_verbatim`) now pins the badge
  contract AND asserts the retired prose never returns;
  `test_actuator_presence_broadcasts.py` pins the cloud badge;
  `test_wake_ux.py` pins the badge state; the shell-id lock follows the
  markup. The typing guide's Qlippy section was truth-updated in the same
  commit (the lock binds doc and UI together — leaving the doc quoting
  retired paragraphs was not an option); HS-62-03 does the wider doc pass.

## Proof

- Live dogfood (`dogfood_story01.py`, real server + Chromium, 11/11,
  zero page errors): the cloud card renders exactly "☁ slack" with the
  `is-cloud` tone and a computed pill radius (the scoped-CSS trap probed,
  not grepped); the local card renders exactly "⌂ Local"; the rendered
  card DOM contains NONE of the five retired privacy phrases.
- Screenshots reviewed: `story01-cloud-card.png` (headline + preview +
  one small pill + buttons — the whole card), `story01-local-card.png`.
- Lock slices: 30 passed across the four updated files.
- Full suite: **2768 passed, 17 skipped** (count unchanged — locks
  rewritten in place). Build clean, 0 `_built/` tracked.
