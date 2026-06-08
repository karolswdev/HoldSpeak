# Phase 53 — Activity Pre-Briefing: final summary

**Status:** CLOSED (7/7). Opened and closed 2026-06-08 on user direction, right after
Phase 52 closed + merged (PR #39). From [backlog](../BACKLOG.md) candidate **F** (local
activity as pre-briefing fuel), picked by the user as the next phase.

## The thesis

HoldSpeak already watches local activity and stores source-cited records, but they live
on the `/activity` ledger you go and inspect. The value is bringing the relevant bit to
you when it helps. So: a small reader that computes source-cited, dismissible nudges from
the activity that already exists, surfaced quietly on the dictation surface, with one
action — "Dictate with this" — that feeds a record into the next dictation. Read-only,
gated by the activity privacy toggle, local, every nudge cites its source.

## A course-correction worth recording

The phase reached 5/6 with a green **no-LLM** dogfood and was ready to close. The user
pushed back: *we have the `.43` LLM endpoint — why dodge real metal?* Chasing the
real-metal proof exposed that the headline action, **"Dictate with this", did not
actually change what the model wrote**:

1. The live dictation path (`run_dictation_pipeline`) built the activity context with no
   `selected_record_id` — it never read the pin.
2. The project-rewriter read only `activity["target"]` / `activity["agent"]` — it never
   consumed activity records, so HS-53-03's `records[0]` pin was inert.

The no-LLM dogfood had been "passing" by testing the engine math and the pinning while
stepping around the one question real metal forces. The user chose to **close the loop
for real** rather than ship the affordance with a noted follow-up. That became HS-53-07,
and it is the most important story in the phase.

## What shipped, story by story

- **HS-53-01 — The nudge engine + dismissal store.** `activity_nudges.py`: a pure reader
  over the existing ledger + the meeting window. Computes 1–3 source-cited nudges (a
  windowed "you touched N things since your last meeting" summary scoped by the previous
  `MeetingSummary.ended_at`, plus per-record suggestions) on a deterministic relevance
  heuristic (recency + entity type + project match) — never an LLM. A dismissal store
  keeps a dismissed nudge gone; off when activity is off. Unit-tested.
- **HS-53-02 — The nudges API.** `GET /api/activity/nudges` (engine drops dismissed) +
  `POST /api/activity/nudges/{id}/dismiss`; empty when activity is off.
- **HS-53-03 — Dictate with this as context.** `build_activity_context(selected_record_id=…)`
  pins the chosen record at `records[0]` (fetched by id if it fell off the window);
  unknown id is a quiet no-op; default path byte-identical.
- **HS-53-04 — The nudge UI.** A Signal-styled `role="region"` "Pre-briefing" block above
  the cockpit tabs with JS-rendered `role="note"` cards — accented glyph, title/summary,
  a citation line (entity · browser/profile · last on date), "Dictate with this" +
  "Dismiss", and a selection pin. Focus-safe; hidden until there is a nudge and activity
  is on. Three screenshots.
- **HS-53-05 — The pre-briefing user guide.** `docs/ACTIVITY_PREBRIEFING.md`, product-tense,
  passes the Phase-51 roadmap-vocab guard, `humanizer` run, linked in the docs index.
- **HS-53-07 — Close the loop (real metal).** The capstone. A process-local one-shot
  selection pin (`dictation_selection.py`) set by `POST /api/activity/nudges/select` and
  consumed by `run_dictation_pipeline`, which now passes `selected_record_id` to
  `build_activity_context`; the project-rewriter names the selected record in **both** the
  draft + refine prompts and is told to ground the rewrite in it. Frontend "Dictate with
  this" / "Clear" POST the selection server-side. Byte-identical when no pin.
- **HS-53-06 — Closeout.** Two green dogfoods, this summary, the docs cadence, PR.

## The proof (HS-53-07, on the `.43` Qwen3.5-9B-Q6 endpoint)

`dogfood_real_llm.py` runs the **same** generic dictation twice over the `.hs` demo
fixture. The dictation names its subject only as "the issue I was just looking at":

- **CONTROL (no selection):** *"Review the open issues in the `ledgerline` repository…"* —
  generic, off the ledger `.hs` context. No `#412`.
- **TREATMENT (selected `github_issue karolswdev/HoldSpeak#412`):** *"Implement the
  `--since` flag in `src/ledgerline/api/charges.py` … as requested in HoldSpeak#412"* —
  fully grounded in the selected issue.

`RESULT: PASS` — the selection demonstrably changes the model output
(`dogfood-real-llm-transcript.txt`). The no-LLM `dogfood.py` (engine math, dismissal
persistence, activity-off, record-pinning) also stays green.

## Two real product guards surfaced (and respected, not papered over)

- The rewrite stage is **`.hs`-gated** (the DIR-01 design): the selected record augments
  an existing rewrite, it does not force one where there is no project context.
- `_rewrite_too_long` caps a draft at ~4x the input: a one-line dictation caps the draft,
  so the dogfood uses a realistic-length utterance — exactly how the feature behaves in
  product.

## Invariants held

Read-only and consenting (a nudge offers; only what the user clicks fires). Gated by the
activity toggle. Source-cited always. Dismissible, quiet, focus-safe. Local-only — nothing
egresses. Byte-identical default when no record is selected.

## Verification

- Full suite **2540 passed, 17 skipped** (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
  was 2523 at HS-53-05 (+17: 8 selection + 5 prompt-grounding + 4 select/clear routes).
- `cd web && npm run build` clean (13 pages, no warnings); 0 `_built/` tracked.
- `dogfood.py` (no LLM) RESULT: PASS; `dogfood_real_llm.py` (`.43`) RESULT: PASS.

## Stories

| Story | Title | Status |
|---|---|---|
| HS-53-01 | The nudge engine + dismissal store | done |
| HS-53-02 | The nudges API | done |
| HS-53-03 | Dictate with this as context | done |
| HS-53-04 | The nudge UI (dictation surface) | done |
| HS-53-05 | Docs: the pre-briefing guide | done |
| HS-53-07 | Close the loop: selection feeds the model (real metal) | done |
| HS-53-06 | Closeout: dogfoods + final-summary + PR | done |

## No follow-on required

The loop is closed and proven end to end. A natural future extension — letting the
selected record influence a rewrite even outside an `.hs` project — is noted but not
needed: the realistic surface for "dictate a reply with this issue" is an `.hs` project,
which works today.
