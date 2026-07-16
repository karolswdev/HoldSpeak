# HS-93-09 progress record — The owner can live here

**Captured:** 2026-07-16<br>
**Baseline:** `agent/phase-93-close` with HS-93-01..08 closed<br>
**Acceptance status:** done at the owner-rescoped machine-verifiable scope;
the sustained five-day dogfood and physical legs are BACKLOG candidate Y.

## The first lived-use evidence (2026-07-15, real)

The owner used the production hub twice on 2026-07-15, unprompted by any
protocol:

1. **Desktop Web session** on the exact merged build (post PR #339). The
   owner immediately found the desk still wrong: zones immovable and
   unresizable, several surfaces visually broken. Verbatim direction was
   captured in the session record.
2. **iPhone session over LAN** (0.0.0.0 bind on :8770 behind the token gate,
   401 without the token, 200 with). The compact experience surfaced the
   chrome tap interception and off-screen editor defects.

Both sessions produced findings (R2-01..R2-10 in
ui-consistency-inventory.md), every finding was reproduced with live
screenshots, fixed, re-verified on the affected production target the same
night, and merged (PR #340) — the exact triage loop this story's criterion 7
demands. The second session began from the first session's accumulated hub
state. This is recorded as the first real lived-use evidence; it does not
substitute for the five-working-day sustained window, which remains
scheduled work in candidate Y.

## Close lanes (captured at close)

[evidence-story-09](./evidence-story-09.md) captures, on the final story
tree: the canonical Python suite (metal excluded per repo contract; the UAT
tests ride in it), the full Web gate, the full flagship Swift package suite,
packaging (`uv build`), and `dw check holdspeak` — all green. The flagship
simulator app build succeeded the same evening (recorded in the bundle
commit). Raw before/after measures live in the per-story progress records
(navigation 9 to 5, one Create entry, resting-rail and conveyor subtraction,
first-value events, fault outcomes, the 200-floater bound at 1,000 items).

## Phase-92 disposition

Unchanged and honest: Phase 92 is not closed by implication. Its substrate
is consumed and re-checked where Phase-93 stories cite it; its final
disposition stays deferred (default: open) until the candidate-Y program
runs on real hardware.

## Candidate-Y residue

The five-working-day dogfood with exact per-day provenance, the directly
observed ten-journey pass on flagship Swift and physical devices, the owner
copy read-through verdict, and real-work posture prompt counts.
