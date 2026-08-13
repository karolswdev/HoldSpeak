# HS-131-10 — The one-path fence

- **Project:** holdspeak
- **Phase:** 131
- **Status:** blocked
- **Depends on:** HS-131-03, HS-131-04, HS-131-05, HS-131-06, HS-131-07, HS-131-08, HS-131-09, HS-131-13, HS-131-14, HS-131-15, HS-131-16, HS-131-17
- **Unblocks:** HS-131-11, HS-131-12
- **Owner:** unassigned

## Problem

A shared helper is not one path if product callers can still instantiate an
engine, open an SDK stream, invoke a local runtime, or relay to mesh around it.
This codebase already grew several private inference seams after the kernel's
first recipe adapter. The invariant needs an executable census that fails when
another door appears.

## Scope

### In

- Add a strict AST/text census over production Python that identifies every
  model-execution form: SDK calls, local runtimes, streaming opens, fallback,
  mesh relay, and shared Whisper preload/warmup plus
  `Transcriber.transcribe()` execution. Model it
  on `tests/unit/test_gate_chokepoint.py:18-64`.
- Permit heterogeneous physical dispatch only behind one authorized
  runner/gateway interface and a finite reviewed adapter allowlist. The
  constitutional invariant is one admission path, not one SDK-call expression.
  Every allowlisted adapter must require the runner's already-admitted
  invocation context; no product surface or domain service may appear in the
  adapter allowlist.
- Add a parametrized literal-spine test, extending the pattern in
  `tests/unit/test_inference_kernel.py:177-259`, across Ask, Recipe run/chat,
  Sequence, Workflow, manual Workbench, scheduled Workbench, memory writeback,
  Rails, Decision, Delivery, voice, meeting, and dictation.
- Instrument provider dispatch in tests and assert:
  `dispatch_count == admitted_invocation_child_count == terminal_invocation_receipt_count`.
  Exercise fallback/retry as multiple dispatches. Count separate causally linked
  egress effects independently; they neither satisfy nor violate invocation
  cardinality.
- Assert every child carries a real parent/session correlation, immutable
  deployment revision, authenticated authority basis, and one terminal outcome.
- Assert no prompt, token stream, transcript body, dictated text, or audio frame
  enters kernel journal fields.
- Assert cancellation, restart, and indeterminate recovery cannot publish late
  output or mutate an existing terminal receipt.
- Reconcile every candidate against the pre-charter execution census in
  evidence. A genuine new model site blocks this story and triggers an explicit
  charter amendment/new owner story; it cannot be patched into an already
  shipped story or waived as a fence exception.

### Out

- Generated Python/TypeScript contracts or a new code-generation system.
- Broad style lint unrelated to inference.
- Weakening the guard to preserve an old direct caller.

## Acceptance criteria

- [ ] The census reports one authorized runner/gateway interface plus the exact
  finite physical adapter allowlist, including local Whisper preload and
  transcription, and
  exits nonzero when a synthetic product caller or unregistered adapter dispatch
  is introduced.
- [ ] Every named product surface reaches the same literal admission, claim,
  dispatch, and terminalization functions.
- [ ] For success, refusal, failure, cancellation, retry/fallback, and
  indeterminate recovery, provider dispatch count equals invocation admission
  count and terminal invocation receipt count; separate egress receipts remain
  linked and are counted independently.
- [ ] A parent/session operation cannot substitute for an invocation child in
  the cardinality assertion.
- [ ] Every invocation child has causation, deployment revision, and authority
  basis; no caller-supplied placement or owner principal survives validation.
- [ ] Journal-content guards reject prompts, tokens, transcript/dictation bodies,
  and audio.
- [ ] Restart and cancellation proofs show no late domain result and immutable
  terminal receipts.
- [ ] The complete model-execution inventory and disposition ride in evidence;
  any new genuine site has an explicit charter amendment and owner story before
  this fence can close.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_inference_kernel.py tests/unit/test_gate_chokepoint.py tests/unit/test_kernel_effect_fence.py tests/unit/test_intel_egress_invariant.py` plus the new census/cardinality suite.
- Mutation: add one temporary direct SDK/provider call and observe the named
  guard failure; remove it and observe green. Attempt a second changed receipt
  and journal-content leak with the same fail-then-green method.
- Integration: one local, one LAN/cloud-compatible, and one mesh dispatch where
  available; fallback, cancellation, and restart/indeterminate cases.
- Manual / device: n/a; HS-131-12 performs the assembled live proof.

## Notes / open questions

The allowlist may contain provider adapter implementations, but no product
surface or domain service. A wrapper that only records around a direct call does
not satisfy this story.

On 2026-08-12 the owner chartered the complete five-story amendment wave and
authorized this verified blocked checkpoint to ship. The exact eleven-family,
48-site ledger is in
[`assets/hs-131-10/findings-inventory.md`](./assets/hs-131-10/findings-inventory.md);
the ruling and verification judgment are in
[`OWNER-DECISION-PACKAGE-HS-131-10.md`](./OWNER-DECISION-PACKAGE-HS-131-10.md).
HS-131-13 through HS-131-17 must delete or admit every finding before this story
can return to `in-progress` and close. HS-131-11 and HS-131-12 remain held.
