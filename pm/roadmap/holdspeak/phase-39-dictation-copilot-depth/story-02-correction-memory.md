# HS-39-02 — Correction memory (session learning)

- **Project:** holdspeak
- **Phase:** 39
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-39-05
- **Owner:** unassigned

## Problem

Every utterance is classified and rewritten **independently** — the pipeline
has no memory. When the router picks the wrong block, or target detection
picks the wrong profile, the user's correction evaporates: the very next
similar utterance is mis-handled the same way. DIR-01 deliberately shipped
stateless (§3.2), but a **bounded, session-scoped** correction signal is the
smallest step that makes the copilot feel like it learns, without re-opening
the rolling-context can of worms.

## Scope

- In:
  - A bounded, thread-safe in-process `CorrectionStore` (a small ring; default
    cap ~20) on `WebRuntime`, holding recent user corrections: `(utterance
    gist, corrected block_id / target_profile, timestamp)`.
  - A capture path: when the dry-run / web surface records a correction
    (intent wrong → right block; profile wrong → right target; rewrite
    rejected), it lands in the store. New/extended route under
    `web/routes/dictation/` (e.g. `POST /api/dictation/corrections`).
  - A **session-scoped nudge** consuming the store: the `intent_router` prompt
    gains a few recent corrections as in-context hints, and/or the effective
    match threshold is nudged for a corrected block; `target_profile`
    resolution consults recent profile corrections. All additive and gated
    behind a default-off `corrections_enabled` flag.
  - Secret hygiene: corrections are gist-only (truncated), never store raw
    secrets; reuse the existing secret-rejection helper from
    `project_doc_suggestions` where applicable.
- Out:
  - **Persistence / DB** — in-process only; the store dies with the session
    (DB write is explicitly out — see phase "Decisions deferred").
  - Cross-session learning, embeddings, or a similarity index — recency +
    simple gist match only this story.
  - Changing the meeting-side MIR router.

## Acceptance criteria

- [ ] A `CorrectionStore` exists, is bounded (configurable cap, default ~20),
      thread-safe, and lives on `WebRuntime` (one per process/session).
- [ ] A correction can be recorded via the dictation web surface and is
      retrievable; storing past the cap evicts oldest (ring semantics).
- [ ] With `corrections_enabled=false` (default) **or** an empty store, router
      scores + target resolution are **byte-identical** to pre-story (asserted).
- [ ] With a recorded intent correction, a subsequent similar utterance's
      routing reflects the nudge (in-context hint and/or threshold), proven by
      a unit test with a fake runtime.
- [ ] With a recorded profile correction, target resolution prefers the
      corrected profile for a matching context; manual override still wins.
- [ ] Corrections are gist-only and pass the secret-rejection check; no raw
      secret is ever stored.
- [ ] No DB schema change; no persistence across process restart.

## Test plan

- Unit: new `tests/unit/test_dictation_correction_store.py` — ring cap +
  eviction, thread-safety (concurrent puts), secret rejection, empty-store
  byte-identical routing.
- Unit: extend `tests/unit/test_dictation_intent_router.py` /
  `test_dictation_*` — nudge changes routing only when enabled + populated.
- Integration: `tests/integration/test_web_dictation_*api.py` — the
  corrections endpoint records + reflects in a follow-up dry-run.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a (covered by dry-run integration).

## Notes / open questions

- "Similar utterance" matching: keep it deliberately simple (recency +
  lexical gist / shared block candidates) — no embedding store this phase. If
  recall is poor, that's a HS-39-07 dogfood observation, not a reason to add
  an index now.
- Interaction with HS-39-01: a rejected *rewrite* is a correction signal too,
  but this story does not auto-retune the rewriter prompt beyond recording it;
  keep the rewriter changes in HS-39-01.
- Canon: DIR-01 §3.2 marks rolling-context out of scope. This store is
  session-scoped and bounded, surfaced as hints — if it grows into stateful
  chaining, the spec wins; record the deviation here.
