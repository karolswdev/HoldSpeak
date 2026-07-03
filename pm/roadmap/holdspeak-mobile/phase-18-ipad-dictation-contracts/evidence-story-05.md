# Evidence — HSM-18-05 — Activity pre-briefing, the source-cited nudge client

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-18-05-nudges`. The client methods
landed in an earlier wave (`HTTPDesktopClient+Activity.swift` + `ActivityNudge` contracts);
this closes the story: the nudge cards, the "Dictate with this" close, and the hub hole
that would have made the close a lie.

## 1. The remote lane never grounded — fixed

The **third silent relay hole of the audit's pattern** (after the 18-02 macro relay and the
18-01 double-rewrite): the Phase-53 selection pin existed, the LOCAL runner consumed it
(`dictation_runner.py`, HS-53-07), and the remote path never did — a "Dictate with this"
tap from the iPad would have parked a record the next remote dictation silently ignored.
Now:

- `_run_dictation_dry_run_text` gains kw-only `activity_context` (`None` keeps the
  historical target-only dict byte-identical).
- `api_dictation_remote` mirrors the runner's HS-53-07 block: consume the one-shot pin,
  `build_activity_context(selected_record_id=...)`, thread it through.
- Tests (17/17 in `test_web_routes_remote_dictation.py`):
  `test_selection_pin_grounds_the_remote_dictation` (the pin's context reaches the pipeline
  call, and the SECOND dictation gets none — one-shot honored),
  `test_no_pin_keeps_remote_dictation_byte_identical`.

## 2. The nudge cards (DictateView)

Nudges ride the same probe as readiness (quiet when absent). Each card: title, body, the
source citation chips, **Dismiss** (server-side dismissal), and — when a citation carries a
record — **Dictate with this**, which parks the record on the hub and flips the card to
**Armed** (accent ring + fill). Delivery clears the armed state (the hub consumed the pin).
Window-kind nudges render dismiss-only. `groundedNudge` also clears if its nudge is
dismissed.

Screenshot: [`hsm-18-05-nudge-cards.png`](./screenshots/hsm-18-05-nudge-cards.png) — the
record nudge Armed, the window nudge dismiss-only, over the live waveform.

## 3. The live-hub proof (real compute, no seeded UI)

Real `ActivityRecord` rows in the scratch hub's ledger (privacy toggle enabled), and the
simulator app connected live:

- `GET /api/activity/nudges` **computed** a window nudge + two record nudges from the real
  ledger; `POST /api/activity/nudges/select {record_id: 1}` → `{"selected": 1}` (validated
  against the ledger).
- [`hsm-18-05-live-hub-nudges.png`](./screenshots/hsm-18-05-live-hub-nudges.png) — the iPad
  rendering those real nudges ("You were looking at github_pr karolswdev/HoldSpeak#216 · 1
  visit on github.com"), each cited, under the live readiness strip.

## Honest boundaries

- The **model-visible effect** of the grounding (the rewrite demonstrably changing with the
  record, Phase 53's control-vs-treatment bar) needs a live rewriter endpoint — currently
  down (see evidence-story-01 §boundaries). The threading is contract-proven
  (pin → context → pipeline call, one-shot); the model-effect re-proof rides the 18-06 gate
  with the endpoint the owner picks.
- The briefing panel (`briefing()` client method) stays unconsumed by this screen — the
  nudges are the story's deliverable; the briefing surface is 19-x territory
  (meeting-adjacent).

## Suites

`uv run pytest -q tests/unit` **2403 passed** · `tests/integration` **685 passed** ·
`swift test` **417 passed** · meeting-capture app xcodebuild green.
