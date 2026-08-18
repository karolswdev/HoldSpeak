# Phase 139 — The Settings Reckoning

**Status:** active (4/7).

**Last updated:** 2026-08-18.

## Owner mandate

The owner browsed the Settings surface (2026-08-17) and ruled it
depressing: operator-grade complexity where a personal tool should be. A
read-only census (audit/settings-census.md, 33 before-shots) measured the
room: **101 controls on glass, of which 5 are provably dead, 2 are
duplicates, 31 are operator wiring, 12 should be hardcoded defaults, and
7 belong on the objects they configure. The honest room contains 33
controls in 7 tiles.** The owner blessed the cut: "Let's fucking fix this
shit." Sequencing ruled 2026-08-17: this phase precedes the Dashboard
Door (now Phase 140).

## Goal

Cut the Settings surface from 101 controls / 14 tiles to ~33 controls /
7 tiles with zero capability loss: dead dials die, defaults hardcode,
object-level config moves home, operator knobs fold behind RAW, and the
room that remains operates with joy at both widths.

## Constitutional grounding

- **Article VI (honest by construction):** five dials save values nothing
  reads — silent no-ops. They die.
- **Article VII / edit-in-world:** meeting capture and export config
  belongs on the Meetings surface, not a global panel.
- **Owner standing rules:** laws over dials (one density law, ember-only,
  Phase 112's one-dial law); debug hides behind RAW; setup flows must be
  joyful — ugly-but-lawful is rejected.

## Evidence base

`audit/settings-census.md` — full disposition table with file:line for
every control (renders / persists / consumer / disposition / why).
Before-shots in `audit/`. The full 33-shot set lives in the audit
session's scratchpad; the walk story re-shoots everything after.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-139-01 | Kill the liars | done | [story-01](./story-01-kill-the-liars.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-139-02 | Defaults are law | done | [story-02](./story-02-defaults-are-law.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-139-03 | Config goes home | done | [story-03](./story-03-config-goes-home.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-139-04 | The RAW wells | done | [story-04](./story-04-the-raw-wells.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-139-05 | Seven tiles | ready | [story-05](./story-05-seven-tiles.md) | — |
| HS-139-06 | The docs sweep | ready | [story-06](./story-06-the-docs-sweep.md) | — |
| HS-139-07 | The walk | ready | [story-07](./story-07-the-walk.md) | — |

## Risk register

| Risk | Guard | Stop signal |
|---|---|---|
| A "dead" dial secretly had a consumer | every kill re-verified by grep + the full suite before the flip | any test or runtime path reads a killed field |
| Fold-to-object breaks the settings write path | withRevision() concurrency helper reused; focused route tests | settings PUT regressions |
| RAW wells become a second junk drawer on the face | RAW is folded/closed by default, one well per module, plain listing | RAW content visible without an explicit unfold |
| Old config.json keys crash load after field deletion | Config.load tolerance verified by test (unknown keys ignored) | boot failure on a pre-reckoning config.json |
| The cut regresses the owner's real workflow | dispositions table is owner-visible; sitting may overrule any row | owner names a lost dial they used |

## Decision log

- 2026-08-17 — Chartered from the census; owner blessed the headline cut
  (101→33, 14→7 tiles, dead dials die, knobs fold to RAW, meetings
  config moves home). Row-level overrule remains open at the sitting.

## Where we are

HS-139-01 done, HS-139-02 done, HS-139-03 done, HS-139-04 done. All
31 FOLD-TO-RAW operator knobs now fold behind one RAW well per module
(FoldGadget, closed by default, unfold state not persisted). Module
faces above the wells contain only KEEP-disposition controls.
Transcription: 1 RAW knob; Voice Typing: 6; Wake Word: 3; Meetings:
20; Cadence: 3; Devices: dynamic walker; Models: 4; Integrations: 2
RAW secrets. Every folded knob still reads/writes its config path.
128 backend + 17 vitest green.
