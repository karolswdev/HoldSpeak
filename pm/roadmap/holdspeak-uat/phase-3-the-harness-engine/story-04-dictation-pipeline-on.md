# HSU-3-04 — Pipeline-on dictation world (spoken-symbols + preview byte-lock)

- **Project:** holdspeak-uat
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Owner:** unassigned

## Problem

On `golden-local` the dictation pipeline is opt-in-disabled, so the dry-run
returns the raw utterance — the deterministic spoken-symbol matcher (pack-c/02)
and the preview-verbatim byte-lock (pack-c/05) can't be machine-checked
(`PROTOCOL-COVERAGE.md` §3.5). The honest learning-count shipped; this story adds
a **pipeline-on world** so the deterministic dictation transforms are verifiable
without the LLM.

## Scope

- In:
  - A recipe `dictation-pipeline-enabled` (a deck/overlay turning
    `dictation.pipeline.enabled` on with the spoken-symbol dictionary + a
    matcher-only stage set, no LLM runtime required — so it stays local), and a
    `dictation-symbols` seed if a symbol dictionary must be configured.
  - A probe `dry_run_output_contains` {utterance, contains}: POST
    `/api/dictation/dry-run` and assert `final_text` contains the transformed
    token (e.g. "at sign" → "@"), and the double-substitution trap lands once.
  - A probe `preview_matches_verbatim` / `preview_byte_locked`: the preview text
    equals what "Type it" lands, and nothing types on the off path (the
    `/api/dictation/preview` + wake/type token-burn seam).
  - Flip pack-c/02 (spoken-symbols) + pack-c/05 (preview-before-type) to staged.
- Out: the grounded rewrite control-vs-treatment (needs `.43`; already authored
  on `seeded-desk-43`); any product change.

## Acceptance criteria

- [ ] `dictation-pipeline-enabled` boots locally with the pipeline on and the
      spoken-symbol matcher active (no `.43`).
- [ ] `dry_run_output_contains` proves a spoken symbol transforms to its
      character once (the double-substitution trap does not double it).
- [ ] The preview byte-lock probe proves the previewed text is what types, and
      the off path types nothing.
- [ ] pack-c/02 and /05 carry real verdicts; a local test covers each.

## Test plan

- Integration (local): pipeline-on dry-run transforms symbols; preview equals
  typed.
- Manual/device: iPad preview-verbatim beat rides HSU-3-05 where device-gated.

## Notes / open questions

- Read `/api/dictation/dry-run` stages + the spoken-symbol matcher (Phase-59 "one
  combined matcher pass" gotcha) and `/api/dictation/preview` + wake/type token
  burn; confirm the matcher runs without an LLM runtime configured.
