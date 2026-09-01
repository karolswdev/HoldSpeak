# Phase 160 - Project Rooms: The Delta (P2)

**Last updated:** 2026-09-01 — 6/8 DONE + 06's functional face committed: THE §14 SENTENCE STANDS ON GLASS ×2 (keyboard-decided loop, zero duplicates on reopen, byte-identical windows, the degraded leg honest). Beauty round on the face in flight → THE OWNER'S VERDICT closes 06 → 08.

## Goal

The repeat-use loop: evidence collectors read the citizens the desk
already owns (meetings, decisions, follow-through, resources, watch
observations — never re-reading providers), the FROZEN review
algorithm (§7.2, twelve steps, versioned materiality) turns them
into deterministic evidence-linked proposals, and the owner decides
— accept / edit-and-accept / defer / dismiss — with the cursor
advancing atomically and dismissals staying dismissed. The /room's
`review` section goes from honest absence to real. Domain slice P2
(SRS_DOMAIN_DRIVER §14); SYS-020..025, DEL-001..007, DOM-005/008,
TST-003/004.

Constitution: Art VI (degraded coverage is stated, never "no
change" — SYS-025), Art VII (review is a posture in Now, never a
modal — WEB-IA-003), Art IX (shots; THE OWNER'S VERDICT closes the
face). Art XI: collectors are computation over local truth; no
egress, no model in the deterministic path (DEL-007).

## Scope

- **In:** the eight stories below; PR from `feat/project-rooms-p2-the-delta`.
- **Out:** updates/Update Factory (P3), Steward (P4), GitHub live
  slice (P2a), scheduling (P5), model-added explanations (§7.2 step
  11 — the seam exists, the model stays out), MCP (P6).

## Exit criteria (evidence required)

- [ ] §14 P2 exit: ONE REAL Project produces repeatable evidence-linked Delta with honest partial coverage — on glass (07), re-run identical (SYS-024), degraded leg honest (SYS-025).
- [ ] Golden Delta tests (TST-004): frozen-window repeatability, ordering, conflict retention, dismissal/defer recurrence laws, model-independent results.
- [ ] Adapter contract (TST-003): retry dedup, stale/failed coverage, partial success — one failing adapter never discards the others.
- [ ] Accept advances the cursor atomically (DEL-005/SYS-023) under the revision law; every proposal decision durable (DEL-002).
- [ ] Shots 1440+393; beauty pass; THE OWNER'S VERDICT closes 06 and holds the merge word.
- [ ] Sweep zero unexplained branch-new; web gates green; counsel zero open must-fix.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-160-01 | The evidence schema (§5.5-5.8, v69, real-DB proof) | done | [story-01-the-evidence-schema](./story-01-the-evidence-schema.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-160-02 | The collectors (five native adapters, TST-003 laws) | done | [story-02-the-collectors](./story-02-the-collectors.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-160-03 | The frozen review (§7.2 twelve steps, golden tests) | done | [story-03-the-frozen-review](./story-03-the-frozen-review.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-160-04 | The decisions (accept/edit/defer/dismiss, the cursor, the recurrence laws) | done | [story-04-the-decisions](./story-04-the-decisions.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-160-05 | The wire + the room (routes; the review section becomes real) | done | [story-05-the-wire](./story-05-the-wire.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-160-06 | The review face (the posture in Now, J/K/A/E/L/X — shots + verdict) | in-progress | [story-06-the-review-face](./story-06-the-review-face.md) | - |
| HS-160-07 | The walk (repeatable Delta on glass, the degraded leg) | done | [story-07-the-walk](./story-07-the-walk.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-160-08 | The close (gates, suite amendments, final summary) | backlog | [story-08-the-close](./story-08-the-close.md) | - |

## Where we are

CHARTERED. Chain: 01 → 02 → 03 → 04 → 05 → 06 ∥ 07(after 06's
functional face) → 08. Laws carried: workers scoped; isolated HOME
scripts; build before every shot; fixtures speak the wire; restore
churned PNGs; -F commit messages; absolute paths; the P2 backlog
walls from 158/159 stand recorded in 159's final summary.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The algorithm drifts under iteration | high (by nature) | §7.2's steps are numbered law; materiality VERSIONED; golden tests pin windows byte-for-byte | a golden test loosened without a suite amendment |
| Delta becomes an inbox | medium | materiality caps + grouping by meaning (PV-012/020); the face shows the capped set | an uncapped proposal flood in a shot |
| Collectors re-read providers | low | watch adapter consumes canonical evaluations ONLY (§7.1) | a provider fetch in a collector |
| Dismissals resurrect | medium | DEL-003's basis-hash law + recurrence tests | a dismissed proposal reappearing unchanged |
