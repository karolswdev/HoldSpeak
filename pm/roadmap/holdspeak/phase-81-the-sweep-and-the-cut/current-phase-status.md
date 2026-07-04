# Phase 81 — The Sweep and the Cut (dogfood small findings + the v0.4.0 prep)

**Status:** OPEN — 1/6.

**Last updated:** 2026-07-04 (HS-81-01 done: the F-10 empty-input guard — `ProjectRewriter.run` no-ops (`reason="empty_input"`) before the model when the latest text is empty/whitespace, covering both an empty transcript and a prior stage that emptied it; 3 tests, the model provably never called (`runtime.calls == []`); dictation battery 310 unit + 179 integration green. Earlier: opened — the handover's ranked items 1 + 3 composed into one phase; the tag stays the owner's button, Phase-65 rule.)

## Why this phase exists

The first recorded dogfood run (`dogfood/results/2026-07-04.md`, Phase 67) filed a
12-row findings ledger. The headline (F-05) was fixed the same day (Phase 80). What
remains is the small-findings tail — one MED behavior bug, one FAIL row, and a
basket of LOW paper cuts — and the handover's rank-1 move: prep the v0.4.0 release
while the record is fresh, folding the fixes in first so the cut ships them.

The survey (this open) grounded every finding in code:

- **F-10 (MED):** `plugins/dictation/builtin/project_rewriter.py` — `run()` never
  checks for an empty utterance; handed `""` with `.hs` context present, the model
  fabricates a plausible task. The guard belongs before the rewrite, next to the
  existing `no_hs_context` no-op.
- **F-07 (the run's one FAIL):** journaling is nested inside the pipeline gate.
  Both the web dry-run (`web/routes/dictation/_helpers.py:497` early-return) and
  the live runner (`dictation_runner.py:144` early-return) skip the journal
  entirely when `pipeline.enabled=false`, even with `journal_enabled=true`. The
  CLI dry-run never journals by design (stateless debugger) and stays that way.
- **F-01 (LOW, systemic):** `web/src/components/GenerationTheater.astro:18`
  references `/theater/theaterorb.png` root-relative; the Astro base is `/_built`
  (every other public asset says `/_built/...`), so the orb 404s on every
  theater-bearing page.
- **F-03 (LOW):** `commands/dictation.py _resolved_blocks` only honors
  `--project`; dry-run already cwd-detects via `detect_project_for_cwd()`.
- **F-04 (LOW): did not reproduce at survey.** `hs import dogfood/PROTOCOL.md`
  exits 1 today (`main.py:407` raises `SystemExit(run_import_command(args))`,
  which returns 1 on `validate_format` failure) — verified via the exact recorded
  repro through `dogfood/hs`. The story locks it with a test and re-scores the row.
- **F-12 (LOW):** `meeting_exports.py` renders json/markdown/txt; the protocol
  expects srt too. Segments carry timestamps; the renderer is cheap.
- **F-08 (docs) / F-06 (harness) / F-11 (protocol):** the blocks example pairs
  `mode: append` with a `{raw_text}` template (doubles the text); the dogfood env
  default still names the retired Qwen3.5 model; T2-13's wording contradicts the
  ratified Phase-61 approval-is-the-gate design.

## Load-bearing calls

- **The journal follows `journal_enabled`, not `pipeline.enabled`.** A pipeline-off
  dictation/dry-run journals a passthrough row (no stages, final = transcript);
  the typed output stays byte-identical. Defaults are unchanged for fresh installs
  only insofar as journaling was already on by default under the pipeline; the
  review surface simply stops lying about tier-1 activity.
- **Prep only, never the tag.** HS-81-06 leaves main one owner-button away from
  v0.4.0: version bumped, CHANGELOG rolled, build + suite verified per
  `docs/RELEASING.md`. The tag IS the publish (Phase 65) and is not ours to push.
- **Findings get re-scored where they were filed.** Fixed rows earn an addendum in
  `dogfood/results/2026-07-04.md`, the Phase-80 pattern.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-81-01 | F-10: the empty-input guard in `ProjectRewriter` — **leads** | done (3 tests; model never called on empty) | none |
| HS-81-02 | F-01: the theater orb 404 (`/_built` prefix) + un-prefixed asset sweep | todo | none |
| HS-81-03 | CLI honesty: F-03 blocks cwd-detect · F-04 exit-code lock · F-12 srt export | todo | none |
| HS-81-04 | F-07: the journal follows `journal_enabled` when the pipeline is off | todo | none |
| HS-81-05 | Docs + harness + protocol truth (F-08, F-06, F-11) + the results addendum | todo | HS-81-01..04 |
| HS-81-06 | The v0.4.0 cut prep (version, CHANGELOG roll, build + suite green) | todo | HS-81-01..05 |

## Where we are

The one MED is closed: an empty utterance can no longer be dressed up as a
task by the rewriter. Next: the orb (HS-81-02) and the CLI honesty basket.
