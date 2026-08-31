# Phase 158 - Project Rooms: The Room (P1)

**Last updated:** 2026-08-31 — 4/6 DONE; 05 fully built (extraction, adoption, rig, beauty ×7 defects, TitleSlotContext for WEB-IA-001, room-fields PATCH gap closed under 02) — AFTER shots verified at 1440+393; before/after sheet in assets/story-05-shots/; AWAITING THE OWNER'S VERDICT (it closes 05 and holds the merge word).

## Goal

The Project becomes a revisioned aggregate with a coherent room
projection: additive schema (identity fields, items, changes,
commands), the revision law (every accepted mutation increments
`projects.revision` exactly once with its change row and ledger event
in the same transaction), command idempotency, `GET /room` replacing
the five-request fan-out, and the Web surface graduating onto it —
while every legacy Project stays readable, restorable, and
route-compatible. Domain slice P1 (`SRS_DOMAIN_DRIVER.md` §14);
DOM-001..012, REF/API laws now enforced by P0's frozen contracts.

Constitution: Art VI (sections that don't exist yet are honestly
absent — no demo state), Art VII (no modals, no prose), Art IX
(shots at 1440+393 on the real hub; the owner's verdict closes the
Web story). Art XI note: P1 ships no Watch/Steward/provider/model
effects, so no new kernel admissions arise; NFR-009 bites from P2a on.

## Scope

- **In:** the six stories below; PR from `feat/project-rooms-p1-the-room`.
- **Out:** setup interview + Watch graduation (P1a), sources/
  observations/reviews/Delta (P2), updates (P3), Steward (P4),
  `project.*` MCP family (P6), Map, multi-Project windows.

## Exit criteria (evidence required)

- [ ] SRS §14 P1 exit: the owner can create/configure/open a REVISIONED Project Room from the desk, and legacy Projects remain intact (pre-Project-Room DB reconciles on a COPY of the real DB; archive/restore round-trips; P0's 275 characterization pins hold or are updated deliberately-and-additively).
- [ ] The revision law holds under test: one revision increment + one `project_changes` row + one ledger event per accepted mutation, atomically; `expected_revision`/`command_id` conflicts are typed via `project_contracts` (its first consumers).
- [ ] `GET /api/projects/{id}/room` is the default Web read path (fan-out retired), revision-stamped, bounded, deterministically ordered; absent-domain sections (sources/updates/steward) are honestly absent, never faked.
- [ ] Shots at 1440+393 on the real hub; beauty pass after the functional pass; THE OWNER'S SHOT VERDICT closes HS-158-05 and holds the merge word.
- [ ] Sweep name-diff zero branch-new; web baseline zero branch-new; counsel close zero open must-fix.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-158-01 | The reconcile (columns, items, changes, commands — proven on a real-DB copy) | done | [story-01-the-reconcile](./story-01-the-reconcile.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-158-02 | The revision law (revision + change + event, atomically; idempotent commands; restore) | done | [story-02-the-revision-law](./story-02-the-revision-law.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-158-03 | The items (typed workstream/milestone/risk/dependency/signal via the service) | done | [story-03-the-items](./story-03-the-items.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-158-04 | The room read (GET /room — one coherent, honest, bounded projection) | done | [story-04-the-room-read](./story-04-the-room-read.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-158-05 | The web graduation (controller extraction, /room adoption, the Room face, shots) | in-progress | [story-05-the-web-graduation](./story-05-the-web-graduation.md) | - |
| HS-158-06 | The close (gates, suite amendments, final summary) | backlog | [story-06-the-close](./story-06-the-close.md) | - |

## Where we are

CHARTERED 2026-08-31 immediately after P0 merged (`6a5bd3e4`).
Anchors spot-re-verified on the new main: project_service.py:15,
schema.py:536 (projects), projects.py:22, ProjectMemoryCore present;
`refs.py` + `project_contracts.py` landed by P0. Machinery read:
`reconcile.py:582 reconcile_schema` auto-adds missing declared
columns (additive ALTER); the five-request fan-out is
ProjectMemoryCore.tsx:384-390; `ServiceEventLedger.append_in_transaction`
at service_event_ledger.py:59. Dependency chain: 01 → 02 → 03/04 →
05 → 06; the web EXTRACTION half of 05 runs parallel to 01/02
(disjoint files).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| P0 pins fight the graduation | high (by design) | additive response fields only; every pin update is deliberate, named in the story, additive | a pin loosened without a story note |
| Reconcile hurts a real DB | low | additive-only declared columns; proof runs on a COPY (never the live file); snapshot regen follows the `r'\\s+'` gotcha | any destructive ALTER; a diff outside new lines in the canonical snapshot |
| /room becomes a kitchen sink | medium | §6.2's section list only; absent domains honestly absent (Art VI) | a fabricated/empty-faked section |
| Web extraction regresses the core | medium | extraction commit changes no behavior; 157 pins + existing suites green before /room adoption | web baseline branch-new |
| Revision law leaks partial writes | medium | one transaction per command; TST-002-style atomicity tests with forced mid-write failures | a change row without its revision/event |
