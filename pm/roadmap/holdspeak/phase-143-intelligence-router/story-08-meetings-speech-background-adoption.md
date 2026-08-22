# HSEGHS001HS104-143-08 - Meetings, Speech, and Background Adoption

- **Project:** holdspeak
- **Phase:** 143
- **Status:** backlog
- **Depends on:** 143-04, 143-05, 143-06, 143-07
- **Unblocks:** 143-10, 143-14
- **Owner:** unassigned

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
