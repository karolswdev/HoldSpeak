# Phase 158 — Project Rooms: The Room (P1) — Final summary

**Closed:** 2026-08-31. **Counsel:** RATIFY-W-C — zero must-fix, one
S (documented, P2-deferred), conditions discharged in the close
commit. **The owner's shot verdict:** round 1 BOUNCED, round 2 PASS
("PASS — close it") — the verdict that closed HS-158-05 and holds
the merge word. 6/6 stories done with evidence.

## What the phase proved

The SRS §14 P1 exit is real: the owner can create, configure, and
open a REVISIONED Project Room, and every legacy Project survived.

- **Schema v67** (real-DB-copy proven): projects' §5.1 identity,
  enriched resources, `project_items`/`project_changes`/
  `project_commands`.
- **The revision law:** 12 write commands; one revision + one change
  row + one ledger event per accepted mutation (8 single-transaction
  correct; 4 legacy-wrapping methods carry the documented S-1
  three-transaction divergence — P2's composition work owes the fix);
  typed `stale_revision`/`idempotency_conflict`; `restore` joined the
  verbs; the §5.1 room fields earned their HTTP write path after the
  glass exposed the gap.
- **Typed items:** five kinds, closed vocabularies + per-type
  lifecycles, DOM-007 verb guard, closed details schemas, the
  severity CASE rank (the alphabetical bug died).
- **`GET /room`:** one deterministic projection (observed_at from
  persisted state — byte-identical no-write reads), honest
  `ok|degraded|absent` sections, fault isolation, caps 5/10.
- **The Web graduation:** extraction under the P0 pins, /room as the
  one-request first render, the Room face with desktop composition
  (SurfaceColumns + a truthful right rail), TitleSlotContext carrying
  the scoped name into the window head (WEB-IA-001 — a new window-
  grammar seam mirroring WingSlotContext), two beauty rounds under
  the owner's eye.

## What the glass taught (the phase's real lessons)

1. The rig serves the BUILT gitignored bundle — vitest proves source
   while the hub serves dist. Build before every shot run.
2. TWO self-consistent fixture lies passed vitest and died on the
   glass: imagined change-row field names ("Change" × 8), then the
   dotted action dialect ("Item.created"). Fixtures must speak the
   backend's dialect — only the glass proves they do.
3. The room-fields PATCH gap was invisible until a rig tried to seed
   §5.1 through the API.

## Gates

- Full suite CI-style: 12F/7968P in 21:47 vs main's fresh 26-name
  baseline (run 33412916883 @ 6a5bd3e4) — 2 name-diff candidates,
  both isolated GREEN on files the branch never touched. Zero true
  branch-new.
- Web: check exit 0 (bundle gate passed); baseline 1862P/1F across
  two runs with a DIFFERENT untouched-file flake each time — three
  candidates total, all isolated green (9/9, 9/9, 28/28).
- Counsel RATIFY-W-C; conditions discharged (S-1 documented + P2
  items N-1/N-3; CONTRACTS-P0 gained the `project` row); counsel-157
  N-2 resolved (SRS §3.2 split).
- Suite side effects: 185 regenerated shot PNGs restored to HEAD
  (the 157 scar, honored).

## P2 backlog (from this close)

- S-1: single-transaction the four legacy-wrapping writes.
- N-1: empty-patch update_project must not burn a revision.
- N-3: unfold the `fields` array in change labels.

## The road from here

P1a "The Interview" charters after the merge, anchors re-verified —
the standing rule.
