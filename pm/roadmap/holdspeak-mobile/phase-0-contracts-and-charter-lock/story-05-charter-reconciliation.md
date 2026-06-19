# HSM-0-05 — Charter reconciliation & decisions lock

- **Project:** holdspeak-mobile
- **Phase:** 0
- **Status:** in-progress
- **Depends on:** none (can run in parallel with HSM-0-01..04)
- **Unblocks:** clean entry to Phase 5 (tech decision) and Phase 11 (gate list)
- **Owner:** unassigned

## Problem

The charter arrived truncated mid-"Quality Gates" (Gate 3), and it defers real
decisions: the Track-F inference engine, the contracts package home, and the
version scheme. Building Phases 5–11 on a reconstructed gate list or unresolved
decisions risks re-baselining work mid-flight. This story settles the open items
before they cost a phase.

## Scope

- **In:** confirm the full Quality Gate list with the owner against the
  `CHARTER.md` reconstruction; record the confirmed list as canon. Lock (or
  explicitly park with a default + trigger) the deferred decisions: Track-F
  engine, `holdspeak-contracts` home, `contract_version` scheme. Seed the
  program-level risk register (in this phase's `current-phase-status.md` and/or a
  program risks doc). Add a one-line cross-link from the `holdspeak` roadmap so
  the mobile program is discoverable.
- **Out:** making the Track-F engine choice itself (that is Phase 5's
  evaluation; this story only confirms it stays deferred with a clean default).

## Acceptance criteria

- [ ] The Quality Gate list is confirmed by the owner and `CHARTER.md` §"Quality
      gates" is updated to remove the "reconstructed" caveat (or corrected to the
      owner's actual list).
- [ ] Each deferred decision has either a locked answer or a recorded default +
      revisit-trigger in the phase decision register.
- [ ] The program risk register exists with stop signals.
- [ ] The `holdspeak` roadmap (or its README/HANDOVER) carries a one-line pointer
      to `holdspeak-mobile/` so the program is discoverable.

## Test plan

- Manual: owner confirmation captured (quote it in evidence); `CHARTER.md` diff
  shows the gate caveat resolved.
- Unit: n/a (planning/canon deliverable).

## Progress (2026-06-18 — owner confirmations received)

- **Quality Gates 3–7: confirmed as-reconstructed.** `CHARTER.md` updated — the
  reconstruction is now the official gate list of record (caveats removed).
- **Timestamps: standardize on UTC `Z`.** Folded into the serialization contract
  (§2), the conformance fixture, and a `validate.py` UTC-Z check (green). Desktop
  bare-local normalizes at the contract boundary (Phase-10 adapter concern).
- **Track-F engine:** stays a Phase-5 measured pick, now pre-grounded by the
  owner's inference brief (candidate set Core ML / llama.cpp+GGUF / MLC-LLM).
- **Package home + version scheme:** locked in HSM-0-03.
- **Remaining for this story:** seed/confirm the program risk register and add the
  one-line discoverability pointer from the `holdspeak` roadmap to this program.

## Notes / open questions

- This is the only Phase-0 story that needs an owner decision rather than code
  reading; surface it early so it doesn't block the close.
- If the owner's real Gate list differs materially from the reconstruction,
  re-check the affected phases' exit criteria (Phases 3/5/6/10/11) and note any
  changes in their status docs.
