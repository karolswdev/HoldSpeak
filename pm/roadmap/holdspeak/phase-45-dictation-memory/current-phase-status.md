# Phase 45 — Dictation Memory & the Moment of Truth

**Status:** IN PROGRESS (1/6). Opened 2026-06-06 on user direction ("think really
hard around the experience … scaffold a phase that will be oh-so-meaningful")
after a grounded look at how HoldSpeak feels to live with.

**Last updated:** 2026-06-06 (**HS-45-01 — the dictation journal persistence
spine — DONE**: `dictation_journal` table + `DictationJournalRepository` + a
side-channel `DictationJournalRecorder` wired into both the live + dry-run paths,
config toggle [default ON] + retention cap + secret redaction. Proven by 13 unit
+ 2 integration tests AND a **true end-to-end run against `.43`** [real pipeline
→ real LLM → real DB row: a 446-char ramble journaled with routing/target/
per-stage latency]. Suite 2343/17; journal-off ⇒ byte-identical).

## The thesis — why this phase

**Your meetings are remembered. Your voice isn't.**

A meeting in HoldSpeak gets a rich afterlife: a searchable archive, transcripts,
speaker labels, extracted artifacts, action items, exports, a beautiful
`/history`. But **dictation — the daily-driver, the thing a user does dozens of
times a day — is a black box that evaporates the instant it types.** Verified
against live code:

- **No journal.** No record of *what I said → what it became (intent/block) →
  where it went (target) → how long it took*. Only a **gist-only** correction
  ring (`plugins/dictation/corrections.py`) + **in-memory** latency quantiles
  (`plugins/dictation/telemetry_store.py`, a 20-run ring). No
  `dictation_journal` table exists in `holdspeak/db/`. Restart ⇒ even that is
  gone.
- **No moment of truth.** When a dictation lands wrong, the user fixes it *in
  the target app* and — maybe — teaches it later via a separate **Memory tab**.
  Correction is **reactive and out-of-flow** (`/api/dictation/corrections` POST,
  `web/routes/dictation/pipeline.py`). The nudge mechanism is good
  (`intent_router.py` Jaccard ≥ 0.5 → confidence boost) but it never *coaches in
  the moment*.
- **No undo, no replay.** A past utterance can't be re-run through the
  now-tuned pipeline; the "it's learning me" promise is never made *tangible*.
- **Opaque latency.** Per-utterance, the user can't see where time/decisions
  went (capture → transcribe → route → rewrite → type). Only aggregate p50/p95
  on `/api/dictation/readiness`.

This phase gives the dictation loop **the soul the meeting side already has**:
remember every utterance (locally, privately), let the user **review** it,
**correct it in the moment** (and have the fix *stick*), **replay** it to see
the copilot got better, and make the pipeline **observable** per-utterance.
Turn "I spoke and hoped" into "I spoke, I can see it, I can fix it, it learned."

## Goal

Give the daily-driver dictation loop a persistent, private, reviewable memory and
a tight in-the-moment correct-and-teach loop — turning a black box into a
trusted, learning companion — without changing what gets typed.

## Scope

- **In:** a persistent **dictation journal** (table + repository + retention +
  secret-filter + toggle + wipe); a **Journal** review surface on `/dictation`
  (timeline · search/filter · per-utterance latency strip · copy · delete/clear
  · local-only trust statement); an **in-the-moment correct-and-teach** loop
  (review the just-typed result, one-tap fix → writes a correction → marks the
  journal entry corrected; focus-safe; works for real dictation *and* dry-run);
  **replay** (re-run a stored utterance through the current pipeline, before/after
  diff, opt-in re-insert); a **docs** story; a **closeout** (no-mic dogfood +
  before/after + PR).
- **Out:** the correction *engine* (the store + Jaccard nudge already exist from
  Phase 40 — this phase adds the in-moment *surface* + journal linkage, not a new
  memory engine); meeting-side history (already rich); any change to routing /
  rewrite / typing *output*; bulk/auto replay; cloud sync of the journal (the
  journal is local-only by design).

## Exit criteria (evidence required)

- A `dictation_journal` table + `DictationJournalRepository` exist; rows are
  written for **both** real dictation and dry-run, secret-filtered, retention-
  capped; `tests/fixtures/db_schema_canonical.txt` regenerated in the same
  commit. (HS-45-01)
- A user can **review** their dictation history on `/dictation` (search, filter,
  per-utterance latency, copy, delete/clear) at the Phase-44 premium bar.
  (HS-45-02)
- A user can **correct a dictation in the moment** (no Memory-tab detour); the
  correction teaches future routing AND the journal entry shows `corrected`;
  the surface never steals keyboard focus. Proven via the dry-run path (no mic).
  (HS-45-03)
- A user can **replay** a past utterance through the current pipeline and see
  before → after; adding a correction then replaying demonstrably changes the
  result. (HS-45-04)
- Public docs describe the journal + its privacy posture + the in-moment loop +
  replay; doc-drift/link-check green. (HS-45-05)
- **Invariants held:** journal-disabled (or empty) ⇒ dictation behavior
  **byte-identical**; journaling is a side-channel over `on_run` (typed output
  unchanged); no transcript content leaves the machine; suite green; **0**
  `holdspeak/static/_built/` tracked. (all stories; re-asserted at HS-45-06)

## Invariants

- **Local-first & private by default.** The journal is local-only, secret-
  filtered (reuse the correction store's filter), retention-capped, with a
  one-click wipe + per-entry delete. Privacy comes from *local + filter + wipe*,
  not from being off. (Locked decision below.)
- **Behavior-preserving.** Journaling is a side-channel observer over the
  existing pipeline `on_run` hook — the routed/typed **output is byte-identical**
  to today. Journal-disabled/empty ⇒ byte-identical.
- **Focus-safe.** Any in-the-moment surface NEVER steals keyboard focus (the
  same invariant as desktop presence) — the dictation flow is sacred.
- **Provable remotely (no mic).** Everything is exercised via the dry-run
  pipeline + the web cockpit + unit/integration tests; the author is remote with
  no mic.
- **Accessible + the Phase-44 bar.** New UI carries the wizard's premium bar
  (glow, hero/eyebrow grammar, pill nav, elevated surfaces) with visible focus,
  reduced-motion, SVG glyphs, contrast.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-45-01 | Dictation journal — the persistence spine | done | [story-01-journal-persistence.md](./story-01-journal-persistence.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-45-02 | The Journal — a reviewable utterance timeline | backlog | [story-02-journal-surface.md](./story-02-journal-surface.md) | — |
| HS-45-03 | The moment of truth — correct in flow, and it teaches | backlog | [story-03-moment-of-truth.md](./story-03-moment-of-truth.md) | — |
| HS-45-04 | Replay — prove it learned | backlog | [story-04-replay.md](./story-04-replay.md) | — |
| HS-45-05 | Docs — the dictation journal & its privacy posture | backlog | [story-05-docs.md](./story-05-docs.md) | — |
| HS-45-06 | Closeout — before/after + dogfood + PR | backlog | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

**HS-45-01 (the spine) is DONE.** The journal table + `DictationJournalRepository`
exist; a `DictationJournalRecorder` writes one row per run (best-effort,
secret-redacted) at the same post-run seam telemetry uses, wired into both the
live runtime (`source='dictation'`) and the dry-run path (`source='dry_run'`).
Journaling defaults ON (local), is retention-capped, and is a pure side-channel
(off ⇒ byte-identical, proven). It was exercised end-to-end against the live
`.43` endpoint (real pipeline → real DB row). Next up is the pair **HS-45-02**
(the review surface on `/dictation`) and **HS-45-03** (correct-in-the-moment,
which sets `corrected`/`correction_id` via `mark_corrected`), both reading this
spine. Sequence: 01 ✅ → (02, 03) → 04 → 05 → 06.

> **Note:** the `openai` package was installed into the dev venv to run the real
> `.43` e2e (it's the optional `dictation-openai` extra, not a new hard dep).

## Active risks

- **Privacy perception.** A persistent record of everything spoken is sensitive.
  Mitigation: local-only, secret-filtered (parity with the correction store),
  retention cap, one-click wipe, per-entry delete, a clear in-UI trust
  statement, and a settings toggle. Make the posture *first-class*, not a
  footnote.
- **Side-channel discipline.** The journal write must never alter timing/output
  of the typed result. Mitigation: write after the `on_run` hook fires (the same
  seam telemetry uses), best-effort, failures swallowed — a journal error must
  never break a dictation.
- **No-mic provability.** Real dictation can't run here. Mitigation: the dry-run
  pipeline produces the same `PipelineRun` shape and is journaled with
  `source='dry_run'`; the dogfood + tests drive everything through dry-run.
- **Schema-snapshot lockstep.** The canonical fresh-schema snapshot must be
  regenerated in the same commit as the table addition (repo rule).

## Decisions made (this phase)

- **The journal defaults ON, local.** It mirrors the meeting archive (on by
  default, curatable). Privacy is delivered via local-only + secret-filter +
  retention + wipe, not via default-off — otherwise the feature is invisible and
  the "it remembers" experience never lands. A settings toggle still lets a user
  disable it.
- **Reuse the Phase-40 correction engine.** HS-45-03 adds the in-moment *surface*
  + the journal↔correction linkage; it does NOT build a new memory/nudge engine.
- **One row per run, both sources.** Real dictation and dry-run both write a
  journal row, tagged by `source`, so the no-mic path is first-class (and the
  dogfood is honest).

## Decisions deferred

- **Retention default** (last-N vs N-days vs both) — settle in HS-45-01; start
  with a generous last-N cap, configurable.
- **Where the in-moment surface lives** (dashboard panel vs presence HUD vs a
  transient toast) — settle in HS-45-03; the dry-run result panel is the
  guaranteed no-mic surface; the real-dictation surface is the design question.
- **Replay re-insert** (whether replay can *type* the improved result, opt-in vs
  preview-only) — settle in HS-45-04; default to preview + explicit opt-in
  insert, focus-safe.
