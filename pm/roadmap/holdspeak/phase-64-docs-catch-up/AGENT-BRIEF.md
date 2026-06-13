# Phase 64 — Agent Brief (read this first)

**Phase 64 — Docs Catch-Up** for HoldSpeak. Opened on owner direction
("Feels like a docs phase is on the books again, no?"). Phase 58 fixed the
story; six phases have shipped since, each documenting itself in its own
guide section — and the front door never caught up.

## 0. Mission

The entry-point docs tell the CURRENT story. Measured at scaffold: the
README has **zero** mentions of the wake word and Send to Slack, and the
two-modes tour stops at the Phase-55 surface; `docs/README.md` (the index)
and `GETTING_STARTED.md` point at nothing newer than import. The deep
guides are current (each phase's docs story did its job) — the gap is
discovery: a new reader cannot find what shipped.

## 1. The one thing you must not get wrong

**Canon governs.** Every new sentence uses POSITIONING's canonical names
(the spoken language setting, the spoken-symbol dictionary, the wake word,
Send to Slack, the egress badge posture: a badge, not prose), the voice
rules (no dashes, the honesty bar, the humanizer standard), and the
existing locks (plugin count "14 built-in plugins" appears in TWO places;
the comparison section is date-stamped; image/link locks are live). Run
`uv run pytest -q tests/unit/test_doc_drift_guard.py` early and often.

## 2. Rules (the standing set)

PMO gate; no `Co-Authored-By`; cadence per shipping commit; one PR, branch
`phase-64-docs-catch-up`, merged on green; full suite via
`--ignore=tests/e2e/test_metal.py`. Humanizer standard on every touched
passage. Docs-only: zero behavior changes.

## 3. Ground truth (verified at scaffold)

- README: "wake word" 0 hits, "Send to Slack" 0, the two-modes table's
  dictation cell ends at activity pre-briefing (P53) and the meeting cell
  at aftercare + facets (P55-ish, import mentioned). The pillars and
  comparison section may also be feature-stale; the "as of mid-2026"
  stamp is still honest.
- `docs/USER_GUIDE.md` IS current: the spoken language setting (~89),
  the wake word section (~100), the spoken-symbol dictionary (~154).
- `docs/MEETING_MODE_GUIDE.md` carries Send to Slack (P61, with
  screenshot) — but nothing upstream points to it.
- `docs/GETTING_STARTED.md` (a numbered first-run walkthrough) has no
  what-next pointers to the P59–P62 surface; `docs/README.md` (the
  index) describes guides at their P58-era scope.
- The voice guard + plugin-count + image/link locks are live in
  `tests/unit/test_doc_drift_guard.py`; screenshots were re-shot in P62
  (post-badge UI) — verify embeds, expect little to re-shoot.

## 4. Stories

- **HS-64-01 — the README catches up.** The two-modes tour absorbs the
  P59–P62 surface (languages incl. the symbol dictionary; the wake word
  with its honest preview-default framing; Send to Slack as aftercare's
  outbound door; trust stated via the badge posture, not new prose); the
  pillars/comparison checked for feature-staleness; locks green; verify
  through the GitHub renderer posture (relative links + raw image URLs).
- **HS-64-02 — the index + Getting Started + the coherence read.**
  `docs/README.md` guide blurbs reflect current scope; GETTING_STARTED
  gains a compact "where to go next" (the wake word, your language,
  voice commands, meetings) without bloating the walkthrough; one
  humanizer-grade read across the P59–P63-added passages in the user
  guides for seams (each was written solo), stale facts fixed.
- **HS-64-03 — closeout.** Full-corpus voice-guard + lock run; an
  embedded-image audit (every screenshot shows post-P62 UI); full suite;
  final-summary; README cadence; PR merged on green; memory.

## 5. Gotchas

- The README image lock curls raw URLs / checks asset paths — keep the
  existing pattern when adding any image.
- "14 built-in plugins" must stay consistent in both places (a lock
  counts the registry).
- The two-modes table cells are long prose — keep them scannable; the
  owner rejects walls of text as much as privacy novels.
- New canonical names must match POSITIONING exactly; the guard bans the
  synonyms ("Slack integration"/"Slack export", "voice macros", …).
