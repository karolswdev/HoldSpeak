# HS-200-05: Prove physical voice capture, correction, and custody

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-02, HS-200-03, HS-200-04
- **Unblocks:** HS-200-12, HS-200-16, HS-200-40
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** AA-UX-002; AA-ENV-003; AC-02, AC-26; C1, C11

## Problem

Voice is central to HoldSpeak. Browser fixtures cannot establish microphone permissions, actual text delivery, or learning from a real correction.

## Scope

Exercise the physical macOS capture path, existing correction memory, retry, and saved-record recovery. Repair demonstrated gaps.

Implementation seams: Speech-session admission; dictation runtime; correction memory; microphone session; dictation journal.

Out: New wake-word engines, new transcription models, and native-device parity.

## Acceptance criteria

- [x] A physical hotkey dictation reaches the intended target and leaves its actual receipt.
- [x] Browser capture supports one spoken Project task with visible microphone ownership.
- [x] Permission denial, silence, interruption, and failed transcription retain recoverable user input where the capture contract permits.
- [x] One real correction is saved and applied by the existing matcher on a relevant replay, with honest counts.
- [x] Kept speech and correction records survive process restart. No duplicate typing occurs on an uncertain delivery retry.

**How these are satisfied (read this before citing a box above).** The machine
half of every criterion is proven by the tests captured in
[evidence-story-05](evidence-story-05.md) §1. The physical half is **accepted, not
observed**: on 2026-09-19 the owner ruled "all walks may be considered as passed".
Only two physical facts were ever observed — the hotkey landing text in a focused
application, and the dictation journal surviving a hub restart, both on 2026-09-08
(`current-phase-status.md:294-300`). A denied microphone permission, silence, an
interruption, a real correction replay and an uncertain delivery retry were never
performed by anyone. §2 of the evidence file lists which is which.

## Test plan

Existing speech/dictation admission suites plus planned phase200_voice_custody coverage. Physical: microphone, hotkey, denied permission, replay, and restart on the attested owner platform.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G0](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
