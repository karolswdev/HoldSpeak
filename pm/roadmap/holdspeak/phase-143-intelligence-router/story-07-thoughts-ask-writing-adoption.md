# HSEGHS001HS104-143-07 - Thoughts, Ask, and Writing Adoption

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-04, 143-05, 143-06
- **Unblocks:** 143-10, 143-13, 143-14
- **Owner:** unassigned

## Problem

Thought interview, Ask, intent, rewrite, and punctuation still depend
on separate mutable Config targets. They are the smallest coherent adoption
that proves profiles, assignments, frozen plans, and fallback end to end.

## Scope

- **In:** Migrate `thought.interview` (including its question-or-synthesis
  result union), `ask.answer`,
  `speech.intent_classify`, `speech.rewrite`, and `speech.punctuate`; freeze the
  server-projected chain with Ask/composite reservation; expose application
  summary/override seams for Story 13; one-way Config migration markers.
- **Out:** Meeting/transcription migration, executable tool turns, and any
  independently assignable `thought.synthesis` until a genuinely distinct
  admitted operation and result contract exist.

## Acceptance criteria

- [x] Ask uses the visible next-run chain exactly once and receipts actual model, fallback, and boundary.
- [x] Assignment edits never retarget an in-flight turn.
- [x] Every executable leg preserves the same typed operation/result and exact-context law.
- [x] No-model, incompatible, and overflow states nominate one lawful repair.
- [x] Upgraded owners with explicit v2 profiles keep the same effective primary until they edit an assignment; implicit `this_machine` receives one deterministic repair instead of an invented profile.

## Test plan

- **Unit:** assignment freeze, typed schema, and Config migration fixtures.
- **Integration:** Workbench composite/restart/admission races with primary failure and fallback success.
- **Manual / device:** API-level next-run and runtime receipt walk; shared
  1440/393 chooser glass belongs to Story 13.

## Notes / open questions

Preserve all Phase 141 Workbench cursor, editor, placement, append-effect, and focus laws.

`speech.punctuate` remains an explicitly non-executing registry capability in
this story because the selected production stage is lexical. It owns no route
evidence provider and cannot be admitted as model work until a provider-backed
punctuation stage is actually selected.
