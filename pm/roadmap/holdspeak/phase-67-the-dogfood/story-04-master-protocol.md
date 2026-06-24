# HS-67-04 — The master protocol

- **Project:** holdspeak
- **Phase:** 67
- **Status:** built (awaiting commit)
- **Depends on:** HS-67-02, HS-67-03
- **Owner:** unassigned

## Problem

The owner needs one fillable document that exercises literally all of HoldSpeak —
CLI, every web page, both pipelines, import, intel/MIR, actuators, languages,
wake word, learning loop, presence, cross-cutting concerns — and is easy to fill
out and re-run each release.

## Scope

- **In:** `dogfood/PROTOCOL.md` — a preflight, a Tier 1 (plumbing, no LLM) pass,
  a Tier 2 (real-metal `.43`) pass, and a cross-cutting section, each a checklist
  of `Do / Expect / Result / Note` items keyed to the functional inventory
  (~58 checks). `dogfood/RESULTS-TEMPLATE.md` — a per-run header (environment,
  rollup table, verdict, top failures). `dogfood/results/` (gitignored copies).
- **Out:** running the protocol (HS-67-06).

## Acceptance criteria

- [ ] Every surface in the functional inventory appears as at least one check:
      all CLI subcommands; all ~11 web pages; transcript + audio import; the six
      meeting profiles; routing controls; deferred intel; aftercare; the four
      actuator paths; grounded dictation per repo; multi-pass + target detection;
      languages + spoken symbols; learning loop; wake word; activity/nudges;
      presence/Qlippy; diarization; egress badges; export formats; schema safety;
      first-run.
- [ ] Each check is fillable (PASS/FAIL/PARTIAL/SKIP + Note) and self-contained
      (commands/routes inline).
- [ ] The two tiers are clearly separated; Tier 1 needs no `.43`/mic.
- [ ] A findings table collects FAIL/PARTIAL into a worklist.

      See `evidence-story-04.md`.

## Test plan

- Manual: read-through for coverage against the inventory; a dry pass of the
  Tier-1 section to confirm every command/route is real.
- Unit: n/a (prose artifact; the harness it drives is covered by HS-67-03).

## Notes / open questions

- Intel is non-deterministic — checks judge substance, not wording. Keep
  LLM-shaped judgments in the manual protocol, never in the automated tier.
