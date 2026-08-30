# Counsel design-beat — DC-01 The Thread (2026-08-29)

One Opus counsel ruling before builders (the standing law). Verbatim
substance; orchestrator dispositions in **bold**.

## Verdict

**RATIFY-WITH-CONCERNS.** "The plan is constitutionally grounded, the
AGPL fence is disciplined, and roughly two-thirds of the machinery it
needs already exists. The four MUST-FIX items below are design-seam
gaps that will bite during build; none requires a redesign."

## MUST-FIX (all ACCEPTED → settled-design)

- **M1 People boundary in a multi-turn, multi-profile thread.** The
  People MCP boundary guards the *tool call*, not the *message
  history*: a `people.brief` result in an earlier turn would be packed
  into a later cloud-routed turn's context. Required: message-level
  redaction of sensitive parts at assembly time when the route's
  egress is cloud, pinned by a test. → **D1 `sensitive` column, D4
  assembler law, D8 leg 2.**
- **M2 Partial-persistence cadence.** Name it; add a `streaming` flag
  so a reconnecting client can tell a running turn from a crashed one.
  → **D3: 2 s / 500 chars / done; `streaming`; 10 s crash rule.**
- **M3 FTS triggers vs soft-delete.** A content-sync FTS5 table without
  triggers rots silently; deleted branches must leave the index. →
  **D1 triggers copied from `notes_memory_fts`.**
- **M4 Frame ordering.** Commit the assistant row and emit
  `turn_started` BEFORE the provider stream opens; deltas carry `seq`.
  → **D3 sequencing contract.**

## SHOULD-FIX

- **S1** Retire `recipe.chat` into `chat.turn`; migrate its assignment
  row. → **ACCEPTED, D2.**
- **S2** Import dedup key. → **ACCEPTED, D7.**
- **S3** Token accounting: per-turn in `stats_json`, cumulative on
  `threads` at `turn_done`. → **ACCEPTED, D1.**
- **S4** One level of sibling branches in the UI. → **ACCEPTED, D1/D5.**

## Recorded notes (not fixing)

R1 10-pass cap is DC-02 tuning. R2 frozen refs stale by design.
R3 FTS recall honest first step. R4 `stats_json` untyped; meter reads
two fields. R5 no new admission path even with tools.

## Story cut

Plan's eight, with capability (02) moved before the streaming runner
(03) because the runner references the registered capability to build
its route plan. → **ACCEPTED; files renumbered.**

## Required walk legs before any flip

1. Real metal `.43`, llama.cpp Q6, two-turn streamed thread, control
   vs treatment, N1 first-delta proof.
2. People boundary under profile switch, payload asserted clean.
3. Glass exhibit 1440 + 393 cross-read: branched, empty, error.
→ **All three are story 08's acceptance criteria.**
