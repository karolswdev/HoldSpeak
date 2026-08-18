# Phase 139 — The Settings Reckoning: final summary

**Status:** 8/8 done and staged on PR #465. Owner sitting and merge nod
pending.

## The mandate

The Settings room exposed 101 controls across 14 tiles: five dead dials,
two duplicates, operator wiring on the face, defaults presented as choices,
and configuration separated from the objects it governed. The owner ruled
that a personal tool should not feel like an operator console and blessed the
cut before implementation.

## What is staged

- The face is seven job-named tiles with 29 controls on glass: Voice, Sounds
  & Presence, Meetings, Rhythm, Models, Integrations, and System.
- Five no-op controls and two duplicate controls are gone. Twelve choices
  became hardcoded laws. Six object-owned controls moved home. Thirty-one
  operator knobs live behind closed RAW wells.
- Fresh installs use the owner-ruled open posture: YOLO, actuators enabled
  with wildcard allowlists, and local-owner People MCP write access.
- The hard boundary remains: encryption and key custody, the People refusal
  matrix, egress disclosure, exact-destination execution, and durable
  receipts/refusals.
- Entry-point docs describe that posture and the pinned-on dictation pipeline
  honestly. Secure and Normal still retain per-action approval.

## The usability proof

The isolated-HOME walk passed **76 checks / 0 failures / 0 findings** and
captured 29 shots at 1440×900 and 393×900. It measured seven face tiles,
29 on-glass controls, no horizontal scroll, and every RAW well closed on
open. Three real tasks completed with API round-trip proof: change the
dictation hotkey, add a destination in narrow cards mode, and change a RAW
knob. Every room reported zero console errors.

The before and after evidence lives in `audit/` and `assets/walk/`. The owner
must see the after shots and nod before merge.

## Sober-eye repair

A fresh Terra reviewer withheld the sitting on two findings that the original
walk and counsel missed:

1. The Companion repository control on Delivery optimistically changed on
   glass but swallowed a stale/rejected settings write. It now names the
   refusal and reloads server truth. The focused 409 test proves the alert,
   the revision-bearing PUT, and the reconciled value (**1/1 passed**).
2. Several entry-point docs still claimed the old default-off posture or told
   the owner to enable a pipeline that is now pinned on. The docs, People MCP
   tool descriptions, roadmap snapshot, and generated UAT phase map now agree
   with runtime truth (**43/43 focused guards passed**).

The re-audit found no remaining product blocker. It ruled the seven-tile room
legible at both widths and the hard boundary intact.

## Gate and ledger

- Full Python gate: **6012 passed / 48 skipped**. Three Playwright setup
  errors were caused by xdist worker HOMEs lacking the installed Chromium;
  the exact live-bus tests passed **3/3 serially** under the real HOME.
- Full web gate: **1153 passed / 5 inherited failures**. The five names are in
  untouched files: the container-query allowlist, the BriefLane swallowed-
  write guard, and three Workbench tests that still look for the renamed
  `GO` button. The new Delivery test passed inside the run.
- Production web build passed. Local typecheck retains six pre-existing
  errors, including the already-present Delivery settings inference line.
- `dw check` still reports an inherited Phase 101 evidence/story mismatch;
  Phase 139's own structural close error is discharged by this summary.

## Counsel and owner decisions

The close counsel verdict was **RATIFY-WITH-CONCERNS, no blockers**. Its two
should-fixes landed before the first close candidate. The later sober-eye
findings above also landed before the sitting. Remaining counsel ledger items
are recorded in `current-phase-status.md`.

The owner may still overrule any census disposition. Merge remains gated on
the owner's visual nod. After that, the proposed next leg is Phase 140, The
Dashboard Door: TODO kanban, upcoming meetings, and scheduled recording on a
front door the owner would actually use on a Tuesday.

## Pointers

- Phase status, decisions, and ledger: `current-phase-status.md`
- Walk proof and screenshot index: `evidence-story-07.md`
- Open-posture proof: `evidence-story-08.md`
- Sober-eye repair captures: `evidence-story-03.md` and
  `evidence-story-06.md`
