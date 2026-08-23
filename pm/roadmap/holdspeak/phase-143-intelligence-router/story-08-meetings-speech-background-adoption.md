# HSEGHS001HS104-143-08 - Meetings, Speech, and Background Adoption

- **Project:** holdspeak
- **Phase:** 143
- **Status:** in-progress
- **Depends on:** 143-04, 143-05, 143-06, 143-07
- **Unblocks:** 143-10, 143-14
- **Owner:** unassigned

## Progress (2026-08-22)

Work rides `feat/hs143-08-meeting-adoption`. Tranche A–C (primitives) is
cold-ratified (Sol RATIFY after a three-fix audit round; ruled specs and the
verification ledger live in `assets/story-08-*`). Phase B slice 1 is complete:
live Meeting analysis, bookmark labels, and auto-title execute as routed
controller-owned children on the atomic five-member session bundle
(aggregate budget groups, deterministic identities, election-gated cards,
`record_only` degradation, recorder-failure unwind). Slice 2 is
complete: routed transcription with day-one same-Meeting bootstrap proven
(auto + explicit backends, fresh DB, migration -> preload -> readiness ->
routed transcript), timeout = unknown, MLX warmup as one bounded preload
child. Slice 3 is complete (Stop = admission close + final pass + bundle
fence/cancel + late-output discard + unconditional legacy aftercare) —
**Phase B is done**. Remaining for this story: Phases C–F of the
handover sequence (deferred queue + plugins, speech lifecycle, background
adopters, migration cleanup). Design canon for the Meeting/speech legs:
`assets/story-08-phase-b-cutover-design.md` (counsel amendments and the
owner's minimal-migration scope ruling are binding).

## Problem

MeetingIntelPlan and SpeechPlan are the proven ordered-revision pattern but
remain parallel authorities. Background services add further route pointers.

## Scope

- **In:** Adapt speech and meeting plans; migrate live/bookmark/title/deferred/plugin,
  Rails, cadence, decision, and delivery capabilities; fix leg/attempt ordinals;
  remove duplicate controls and legacy reads after migration markers.
- **Out:** Arbitrary plugin strings and provider-hidden retries.

## Acceptance criteria

- [ ] Existing histories remain readable and restarts never duplicate egress.
- [ ] Dialect retry then fallback creates three unique children and exact receipts.
- [ ] Speech preload remains lifecycle work, not an owner-facing LLM assignment.
- [ ] Service principals cannot inherit OWNER-only routes implicitly.
- [ ] All migrated call sites leave the legacy-pointer census.

## Test plan

- **Unit:** plugin definitions, ordinals, migrations, and authority.
- **Integration:** meeting/speech restart, offline, Stop, retry, and fallback.
- **Manual / device:** backend/application assignment summaries and receipts;
  shared editable owner glass belongs to Story 13.

## Notes / open questions

The canonical plan replaces the old plan authority without rewriting v1 histories.
