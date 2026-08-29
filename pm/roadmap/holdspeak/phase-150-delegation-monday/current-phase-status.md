# Phase 150 — Delegation + the Chief-of-Staff Brief

**Status:** chartered (0/6).

**Last updated:** 2026-08-29.

## Owner mandate

The owner's pick from the heavy-hitter handover menu (their
standing frame, verbatim law: value for "a Senior Software
Architect, who now manages 3 people"; their genre for this arc:
"another heavy-hitting functional development"). The manager suite
completes: the Door learns waiting-on-WHOM and the Monday Brief
becomes a chief of staff. Branch `feat/hs150-delegation-monday`
from main `c9b0cd25`.

Standing laws with extra weight: docs/PEOPLE_INTEGRATION.md
(explicit gesture, NO inferred identity — the owner-string mapping
is a SECOND gesture, never a match); the 138 law on a PERSISTED
surface (the Monday Brief writes plaintext tables — person
sections are read-time only, pinned); the era's rig laws (every
scar in HANDOVER §4); the web-baseline debt rider is
NON-NEGOTIABLE this phase (two arcs carried it).

## Evidence base

- [`assets/audit-census.md`](./assets/audit-census.md) — the two
  decisive answers: NO code infers owner identity (clean contract
  ground) and the Monday Brief IS PERSISTED (read-time overlay is
  the only lawful shape). The half-built gifts: the server owner
  filter exists un-UI'd; one_on_one_brief is the digest source;
  delegated_at does not exist (WHO without WHEN).
- [`assets/audit-monday-walk.md`](./assets/audit-monday-walk.md) +
  [`assets/audit-walk-shots/`](./assets/audit-walk-shots/) (8
  before-shots) — DELEGATION: PAINFUL (backend-ready,
  gesture-invisible; scan-every-card is the only path); MONDAY:
  person-blind ("a flight-recorder digest, not a chief-of-staff
  brief"); three defects folded into the charter (BriefLane
  first-load null; a persisted path leak; wrong-era verbs on
  person items).
- [`assets/settled-design.md`](./assets/settled-design.md) —
  D1–D6: the encrypted owner_aliases gesture with invariant P2 and
  reserved strings; the read-time board projection + chips over
  the existing filter; the never-persisted person_sections overlay
  with the manager's verbs; the folded defects; the web baseline
  rider.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-150-01 | The owner gesture (aliases + resolution + delegated_at) | ready | [story-01](./story-01-owner-gesture.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-150-02 | The delegation lane (chips, filter, staleness) | ready | [story-02](./story-02-delegation-lane.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-150-03 | The chief-of-staff overlay (person_sections) | ready | [story-03](./story-03-chief-of-staff.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-150-04 | The web-inherited baseline (the debt rider) | ready | [story-04](./story-04-web-baseline.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-150-05 | The record book | ready | [story-05](./story-05-record-book.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-150-06 | The walk and the close | ready | [story-06](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Chartered 2026-08-29 (night) from the census + the Monday walk;
the design counsel ruling is the gate ahead of builders. No story
started.

## Decision log

- **2026-08-29 — owner pick:** Delegation + the Chief-of-Staff
  Brief from the heavy-hitter menu (over JIRA and the live-metal
  proof).
- **2026-08-29 — orchestrator rulings (the spec):** owner mapping
  = encrypted owner_aliases ON the relationship (the second
  explicit gesture; case-insensitive in-memory compare, never
  logged; P2 one-person-per-alias; "Me"/"Remote"/"you" reserved
  and unmappable); delegated_at as a bare lawful timestamp;
  person chips over the EXISTING server filter (group-by-person
  ledgered); person_sections computed in BOTH generate and load
  paths and NEVER inserted (the write-count pin); the manager's
  verbs on person items ("Add to 1:1 agenda" via the real 138
  authority); the three walk defects folded; the web baseline is
  story 04, not a hope. The owner may overrule any row.
- **2026-08-29 — counsel design ruling:** recorded here when it
  returns.

## Risk register

- The persisted-brief boundary is THE risk: every builder touch on
  monday_brief_service must keep person data out of the INSERT
  paths — the pin is chartered, the counsel is asked to attack it.
- Owner-string reality is messy (LLM-extracted, inconsistent
  casing): aliases are per-string on purpose; multiple aliases per
  person expected; unmapped stays honest.
- The Brief surfaces predate four polish arcs — story 03 touches
  render sites (BriefView/BriefLane) that may need era repairs;
  scope to the person sections + the folded defects, ledger the
  full beautify.
- Drift surfaces per the census (door read-model pins, brief
  collectors, transport parity, api-surface on new routes, the
  walk's nine legs).
