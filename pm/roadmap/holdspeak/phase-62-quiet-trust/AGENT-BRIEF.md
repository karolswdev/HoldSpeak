# Phase 62 — Agent Brief (read this first)

**Phase 62 — Quiet Trust** for HoldSpeak. Opened on direct owner feedback
(2026-06-12): the privacy-reassurance prose across the UI is "really
cringey" — notification panes, the HUD, Qlippy cards are full of "nothing
leaves your machine / stored locally / never sent" novels. The owner's ask,
verbatim in spirit: *"you can just literally have a symbol for local only
or local plus cloud or just cloud"* — and redo the screenshots.

## 0. Mission

Trust should be ambient, not narrated. One compact **egress badge** (three
states: local · local+cloud · cloud, glyph + one word) replaces every
privacy paragraph on cards and notifications. Behavioral warnings that
change what the user should DO stay (e.g. "a false detection would type
into the focused app"); reassurance that merely restates the privacy
posture goes. Settings and docs may explain once; cards may not.

## 1. The one thing you must not get wrong

This REVERSES a locked Phase-56 decision (the "three privacy answers
verbatim on every actionable card", doc-locked by
`test_qlippy_doc_states_the_guarantees_verbatim`). Update the locks to pin
the NEW pattern — do not weaken them into nothing, and do not leave any
old-copy lock half-alive. Every screenshot that shows the old copy gets
re-shot from a live run.

## 2. Rules (the standing set)

PMO gate (7 boxes; evidence with done-flips; final-summary at exit); no
`Co-Authored-By`; cadence per shipping commit; one PR, branch
`phase-62-quiet-trust`, merged on green; tests via
`uv run pytest -q --ignore=tests/e2e/test_metal.py`; web source only +
`is:global` for JS-rendered DOM (the badge is JS-rendered on Qlippy cards —
the Astro scoped-CSS trap applies); docs under the live voice guard.

## 3. Ground truth (verified at scaffold)

- **The Qlippy card shell**: `qlippy.js:131` renders `card.privacy` into
  `#qlippy-privacy` (markup `presence.astro:66`, style `.q-privacy`).
  Every card in `qlippy-events.js` passes a `privacy:` paragraph
  (`privacyLine()` for proposals; literals for result/learned/aftercare/
  wake). The native HUD renders this same page — fixing the page fixes
  the overlay.
- **The full prose inventory (web/src)**: `welcome.astro:34` rail foot;
  `settings.astro:120` lead + `:217` wake em-copy tail; `history.astro`
  draft notes (~804), file-issue loop-note (~855), proposal-note (~1184),
  proposal-guard (per-target, HS-61-04); `history-app.js` flashes
  ("Nothing is sent yet." ×2); `LocalPill.astro:23` tooltip;
  `ContextSection.astro:107` tail sentence.
- **Locks pinning the old copy**: `test_doc_drift_guard.py::
  test_qlippy_doc_states_the_guarantees_verbatim` (doc + js markers);
  `test_wake_ux.py:103` ("Nothing has been typed");
  `test_actuator_presence_broadcasts.py` (three-answers comment/asserts);
  `test_presence_qlippy_shell.py:30` (`qlippy-privacy` id);
  `test_history_slack_surfaces.py` (the HS-61 notes + flash + guard copy).
- **Docs quoting the old copy**: `INTELLIGENT_TYPING_GUIDE.md` (the
  Qlippy section's verbatim answers), `USER_GUIDE.md` (wake card copy),
  `MEETING_MODE_GUIDE.md` (aftercare notes in prose + screenshots).
- **Screenshots showing old copy** (re-shoot): the Qlippy card assets in
  doc assets, `docs/assets/aftercare/followup-draft.png`,
  `docs/assets/aftercare/send-to-slack.png`, and any phase screenshots
  embedded in user-facing docs. (Roadmap evidence screenshots stay as
  history — only user-facing docs re-shoot.)
- **The LocalPill** (header "Local only" chip) already IS the ambient
  symbol — the badge reuses its visual language at card scale.

## 4. Stories

- **HS-62-01 — the egress badge on Qlippy cards.** A three-state badge
  (`local` ⌂ / `mixed` ⌂+☁ / `cloud` ☁ + optional target label) rendered
  by the card shell from a structured `egress` field; every card in
  `qlippy-events.js` swaps its `privacy` paragraph for the badge (+ at
  most one short behavioral line where one is load-bearing, e.g. the wake
  card's not-typed state lives in the headline already). Presence shell
  markup/CSS; locks updated to pin the badge.
- **HS-62-02 — the sweep.** Every inventory line in §3: cut or shorten
  the reassurance tails (history notes, flashes, welcome rail, settings
  lead + wake tail, LocalPill tooltip, ContextSection); keep behavioral
  warnings. The HS-61 surface locks updated to the new copy. Build clean.
- **HS-62-03 — docs + the re-shot screenshots.** The Qlippy section of
  the typing guide describes the badge instead of quoting paragraphs
  (verbatim-lock rewritten to pin the badge contract); USER_GUIDE +
  MEETING_MODE_GUIDE aligned; POSITIONING gains the voice rule ("egress
  is stated by the badge, not prose — cards never narrate privacy");
  every user-facing-doc screenshot showing old copy re-shot live.
- **HS-62-04 — closeout.** Live dogfood: a real proposal card + wake-ish
  card render the badge (zero page errors); screenshots reviewed; full
  suite; final-summary; README cadence; PR merged on green; memory.

## 5. Gotchas

- The badge on Qlippy cards is JS-rendered DOM → its CSS must be reachable
  (presence.astro styles the shell today — same pattern, but verify with a
  computed-style probe or screenshot, not grep).
- `privacyLine()` carries the only place the card names its target — the
  cloud badge keeps the target label so that information survives.
- The journal's "Preview only — nothing was typed" is a BEHAVIORAL state
  string (allowlisted verbatim in the voice guard) — not privacy prose;
  leave it.
- `commands.astro` "Runs this on your machine when you say the keyword.
  No confirmation." is a danger warning — leave it.
- Don't forget `uv run pytest -q tests/ -k "qlippy or presence or wake_ux
  or slack_surfaces"` early — the locks fail loudly until updated.
