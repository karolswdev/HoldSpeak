# Phase 48 — The Visible Learning Loop ("What HoldSpeak learned") — Final Summary

**Status:** CLOSED (5/5). Opened and closed 2026-06-07.
**Branch:** `phase-48/story-01-learning-digest`. **PR:** to `main`, merged on green CI.

## Why this phase

HoldSpeak already hears rough speech, routes and rewrites it, records every
attempt (the Phase-45 journal), learns from your corrections (the Phase-40
correction memory + Jaccard matcher), and can replay to prove it improved. That
local speech-to-work loop is the product's most ownable idea, and it was
**invisible**: a user saw two raw lists (a Memory tab, a Journal tab) and a buried
multi-field correction form. The user picked "what I learned this week" from the
strategic review and tied it to the open-source push: *"let's make this Open
Source thing happen."* This phase made the loop **visible**, **trustworthy**, and
a **normal ritual**, without changing what the pipeline does.

## What shipped

- **HS-48-01 — The learning digest.** A read-only aggregation
  (`holdspeak/dictation_learning.py`) over the journal + corrections, behind
  `GET /api/dictation/learning-digest?window=week|all`: corrections made,
  dictations corrected, by-block/by-target breakdowns, and a real "learned from N
  similar" per correction. `reach_for_gist` reuses `corrections.similarity` (the
  exact Jaccard the router thresholds on), so the count is the true reach. A
  Signal-styled "What HoldSpeak learned" hero at the top of the Memory tab
  renders it (window toggle, stat cards, breakdown chips, per-correction reach,
  teaching empty state). Proven through real voice by an opt-in `say` -> Whisper
  -> dry-run -> correct -> digest e2e.
- **HS-48-02 — Inline trust signals.** A calm "learned from N similar" chip on
  the dry-run result, journal entries, and the Memory list, plus an honest
  post-correction toast. All counts come from one shared helper
  (`reach_for_gist` / `best_correction_signal`, reusing `best_match_in`); quiet at
  N=0; nothing claimed when `corrections_enabled` is off or a teach was
  secret-filtered.
- **HS-48-03 — The correction ritual.** Correcting is one tap on the dry-run
  result and every journal entry: a shared `correctionRitual` / `wireFixit`,
  "Right" a no-write acknowledgement, "Fix it" the existing correct path
  pre-scoped (block/target in one tap, routed value pre-filled). Reuses
  `POST /journal/{id}/correct` (no new write primitive) and stays focus-safe.
  Also fixed a latent `[hidden]`-vs-`display` leak.
- **HS-48-04 — Docs.** The Intelligent Typing guide §12 tells the loop as one
  five-step story (dictate, correct in one tap, learn, see the digest, replay)
  with real screenshots and a "how the learning works, and its limits" note
  (Jaccard, local, off by default). README + docs index frame it as the
  local-first differentiator.
- **HS-48-05 — Closeout.** This summary, before/after captures, a green dogfood,
  a green suite, the PR.

## Before / after

Real screenshots under `docs/assets/screenshots/`:

- `learning-loop-before-memory.png` / `learning-loop-before-journal.png` — the old
  surfaces: the Memory tab was a raw correction list with no digest; journal
  entries had no "learned from N similar" chip and no one-tap correction.
- `learning-digest-week.png` (+ `-all`, `-empty`) — the new "What HoldSpeak
  learned" digest hero.
- `trust-signals-memory.png` / `trust-signals-journal.png` — the inline
  "learned from N similar" chips where the work happens.
- `correction-ritual.png` — the one-tap right/wrong correction, mid-flow.

The before set was captured by temporarily checking out `5a3c047`'s
`dictation.astro` + `dictation-app.js`, building, and screenshotting, then
restoring the branch versions and rebuilding. The after-state is regenerable via
`scripts/screenshot_learning_digest.py` (boots a real server, no mic/LLM).

## Dogfood (green)

`scripts/dogfood_learning_loop.py` drives the loop over HTTP (stub runtime, no
mic). Closeout run:

```
2. digest before correcting:
   corrections_made=0  dictations_corrected=0  similar_nudged=0
3. corrected the launch-checklist utterance -> intent: action_item
   taught=True  enabled=True  similar=2
4. digest after correcting:
   corrections_made=1  dictations_corrected=1  similar_nudged=2
   by_block=[{'block_id': 'action_item', 'count': 1}]
   correction reach: 'follow up with sam about the launch checklist' -> action_item (learned from 2 similar)
PASS
```

## Tests run

- Dogfood: `scripts/dogfood_learning_loop.py` -> PASS.
- Real-voice e2e (opt-in): `HOLDSPEAK_SPOKEN_DICTATION_E2E=1 uv run pytest -q
  tests/e2e/test_dictation_learning_digest_spoken_e2e.py` -> 1 passed.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` ->
  **2401 passed, 18 skipped** (exit 0).
- `(cd web && npm run build)` clean; **0** `holdspeak/static/_built/` tracked.

## Invariants held

- **Behavior-preserving.** The digest is read-only; correcting reuses the existing
  write path; routing stays byte-identical when corrections are off (the snapshot
  is `None`, so signals are `None`). Pipeline tests green throughout.
- **Honest over hype.** One matcher (`reach_for_gist` / `best_match_in`) feeds the
  digest, the chips, and the toast; surfaces stay quiet at N=0; the
  `corrections_enabled` posture and the secret-filter are respected everywhere;
  the docs state the Jaccard limits plainly.
- **Local-first & focus-safe.** Everything stays local; the dictation bundle keeps
  zero `.focus()`.

## What this unlocks / deferred

- The open-source pitch now lands in the product, not just the README: a tool that
  gets better at your voice, on your machine, and shows you the proof.
- Deferred (unchanged from the phase plan): the public release contract +
  schema-migration policy (a separate pre-release gate); a voice-command grammar;
  any presence-surface right/wrong affordance (cockpit-first held).
