# HSEGHS001HS104-143-07 - Thoughts, Ask, and Writing Adoption

- **Project:** holdspeak
- **Phase:** 143
- **Status:** backlog
- **Depends on:** 143-04, 143-05, 143-06
- **Unblocks:** 143-10, 143-13, 143-14
- **Owner:** unassigned

## Problem

Thought interview, synthesis, Ask, intent, rewrite, and punctuation still depend
on separate mutable Config targets. They are the smallest coherent adoption
that proves profiles, assignments, frozen plans, and fallback end to end.

## Scope

- **In:** Migrate `thought.interview`, `thought.synthesis`, `ask.answer`,
  `speech.intent_classify`, `speech.rewrite`, and `speech.punctuate`; freeze the
  server-projected chain with Ask/composite reservation; expose application
  summary/override seams for Story 13; one-way Config migration markers.
- **Out:** Meeting/transcription migration and executable tool turns.

## Acceptance criteria

- [ ] Ask uses the visible next-run chain exactly once and receipts actual model, fallback, and boundary.
- [ ] Assignment edits never retarget an in-flight turn.
- [ ] Every leg preserves the same typed operation/result and exact-context law.
- [ ] No-model, incompatible, and overflow states nominate one lawful repair.
- [ ] Upgraded owners keep the same effective primary until they edit an assignment.

## Test plan

- **Unit:** assignment freeze, typed schema, and Config migration fixtures.
- **Integration:** Workbench composite/restart/admission races with primary failure and fallback success.
- **Manual / device:** API-level next-run and runtime receipt walk; shared
  1440/393 chooser glass belongs to Story 13.

## Notes / open questions

Preserve all Phase 141 Workbench cursor, editor, placement, append-effect, and focus laws.
