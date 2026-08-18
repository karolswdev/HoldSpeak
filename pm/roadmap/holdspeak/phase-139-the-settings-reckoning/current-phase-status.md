# Phase 139 — The Settings Reckoning

**Status:** complete (8/8; PR #465 merged 2026-08-18).

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
| HS-139-05 | Seven tiles | done | [story-05](./story-05-seven-tiles.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-139-06 | The docs sweep | done | [story-06](./story-06-the-docs-sweep.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-139-07 | The walk | done | [story-07](./story-07-the-walk.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-139-08 | Open throttle | done | [story-08](./story-08-open-throttle.md) | [evidence-story-08](./evidence-story-08.md) |

## Risk register

| Risk | Guard | Stop signal |
|---|---|---|
| A "dead" dial secretly had a consumer | every kill re-verified by grep + the full suite before the flip | any test or runtime path reads a killed field |
| Fold-to-object breaks the settings write path | withRevision() concurrency helper reused; focused route tests | settings PUT regressions |
| RAW wells become a second junk drawer on the face | RAW is folded/closed by default, one well per module, plain listing | RAW content visible without an explicit unfold |
| Old config.json keys crash load after field deletion | Config.load tolerance verified by test (unknown keys ignored) | boot failure on a pre-reckoning config.json |
| The cut regresses the owner's real workflow | dispositions table is owner-visible; sitting may overrule any row | owner names a lost dial they used |

## Decision log

- 2026-08-18 — PR #465 merged. The owner accepted the Settings/Models work;
  Phase 140 supersedes the previously named Dashboard Door with The First
  Sentence complexity cut.
- 2026-08-18 — PRE-MERGE SOBER-EYE REPAIR: a fresh Terra cold review
  withheld the owner sitting on two should-fixes. The Companion repository
  control on Delivery now names a rejected/stale settings write and reloads
  server truth instead of leaving an optimistic lie on glass; its focused
  stale-revision test passes 1/1. Entry-point docs now state the actual fresh
  posture (YOLO, actuators on, People MCP write), the pinned-on dictation
  pipeline, and the surviving custody/refusal/egress/receipt boundaries.
  Roadmap status is staged/active 8/8 pending the owner's nod, and the UAT
  phase ledger was regenerated (2/2 guard tests). Full Python gate: 6012
  passed / 48 skipped; three xdist-HOME Chromium setup errors passed 3/3
  serially under the real HOME. Full web gate: 1153 passed; five inherited
  reds remain in untouched files (container-query allowlist, BriefLane
  swallowed-write guard, and three stale `GO`-button expectations). The
  production web build passes. Owner sitting remains the merge trigger.
- 2026-08-17 — AMENDED: HS-139-08 "Open throttle" added by owner ruling
  ("loosen security to the floor" — completes ledger-not-gate): permissive
  defaults everywhere (POSTURE=YOLO, actuators on, MCP families on); hard
  boundary stays (custody, People refusal matrix, egress badges, receipts).
- 2026-08-17 — Census correction (HS-139-03 worker): FOLD-TO-OBJECT is six
  rows, not seven — the census summary's count was off by one; all six
  moved home. Story text notes the discrepancy.
- 2026-08-17 — Chartered from the census; owner blessed the headline cut
  (101→33, 14→7 tiles, dead dials die, knobs fold to RAW, meetings
  config moves home). Row-level overrule remains open at the sitting.

## Counsel verdict (close, 2026-08-18)

**RATIFY-WITH-CONCERNS, no blockers.** Hard boundary verified clean:
custody/crypto zero-diff, People refusal matrix untouched, egress
badges untouched, yolo auto-execution and manual approve+execute share
the same receipt writer (actuator_executor.py:249). Kills spot-checked
clean against dynamic access; RAW folds unpersisted and round-trip
proven. Should-fix items BOTH FIXED before merge: evidence-story-08
recaptured with the yolo-receipt suites (104 tests); story-03 amended
seven→six with the row-64 correction. Ledgered: (L1) People MCP
_BOUNDARY string still claims env-var restriction though default is
now write (people.py:46, 11 tool descriptions); (L2) actuators.py
propose/issue_grant parameter defaults still "neutral" — harmless, all
callers explicit, yolo refuses grants; (L3) soft-pin behavior: an
existing config.json with pipeline enabled:false keeps it until the
next settings write — intended; (L4) story-05 evidence double-capture
(first failed on wrong cwd) — environmental; (L5) pre-existing React
act() warnings in settingsModels vitest.

## Where we are

All 8 stories are complete and merged. Seven tiles shipped (Voice, Sounds & Presence,
Meetings, Rhythm, Models, Integrations, System). Open throttle shipped:
POSTURE=YOLO, actuators on with wildcard allowlists, People MCP
defaults write, all boundary suites green. Docs sweep done: SECURITY.md
states the YOLO default honestly and names the hard boundary. The walk:
76 passed, 0 failed, 0 findings, 29 shots at 1440x900 and 393x900.
Measured bars: face = 7 tiles (bar <=8), on-glass controls = 29
(bar <=40), zero horizontal scroll, RAW wells closed on open. Three
tasks on glass: (a) hotkey changed + API round-trip, (b) destination
added at 393px cards mode + API verified, (c) RAW knob changed + API
round-trip. Zero console errors everywhere.
