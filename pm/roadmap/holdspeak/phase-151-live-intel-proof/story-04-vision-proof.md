# HS-151-04 — The vision proof (the snapshot adapter on real metal)

- **Project:** holdspeak
- **Phase:** 151
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-151-05, HS-151-06
- **Owner:** unassigned

## Problem

The Calendar Snapshot adapter (HS-146-07) has never seen a real
vision model — its unit tests send base64 "AAAA" and the 146
ledger carries "no real-vision-model probe has run yet". The owner
ordered the test; the endpoint now EXISTS (8081, proven at
charter: 4/4 events off a week grid — metal-probes.md).

## Scope

### In

1. The FULL product path against http://192.168.1.43:8081/v1: an
   openAICompatible profile + the calendar.snapshot_extract
   assignment (through the real adoption service); IMPORT
   SCREENSHOT / drop with assets/vision-probe-week.png (and one
   messier variant the rig renders — overlapping events, an
   all-day row); the REAL router dispatch → the anchored review
   window → confirm → the generated .ics through the one bounded
   parser → rail events under the snapshot source with provenance
   chips.
2. Assertions: extracted events match the rendered truth (day /
   start / end / title — the rig knows what it drew); the week
   anchor honest (never guessed); refusal paths still refuse by
   name with no vision-capable profile assigned (the 146 grammar).
3. COUNSEL S2: a refusal leg — a non-calendar image (blank/noise)
   must yield zero events or a named refusal on the real model;
   COUNSEL L2: record Qwythos's JSON reliability as a finding
   (8081 has no schema pin).
4. Frames: review window populated, rail with the snapshot chips.
5. The two 146 counsel-ledger riders close or re-ledger honestly
   (422 surfacing; vision pre-filter) — verify on this real path.

### Out

- Any adapter behavior change beyond what the real model forces
  (report deviations to the orchestrator first).
- Touching the 8080 server; downloads to the box.

## Acceptance criteria

1. Screenshot → rail, end-to-end on the real model, ×2 green +
   stamped capture; frames.
2. The 146 "no real vision probe" ledger line CLOSES.
3. Extraction fidelity recorded honestly (including any miss —
   a miss is a finding, not a failure of the story).

## Test plan

The rig ×2 + dw capture; focused route/service suites if touched.
