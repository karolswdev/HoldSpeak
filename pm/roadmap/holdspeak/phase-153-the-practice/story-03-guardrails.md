# HS-153-03 - Guardrails (chat.guardrail, seeds, the advisory row)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** backlog
- **Depends on:** HS-153-01
- **Unblocks:** HS-153-06
- **Owner:** unassigned

## Problem

A cheaper second model watches the hands (counsel M8): before the
per-call admission, one guardrail pass over the last N messages + the
pending calls yields violations/warnings as an in-flow row. Advisory
only — yolo proceeds; safe/neutral flips the decision box default to
Deny; never auto-denies; a guardrail failure is a warning, never a
block (settled design D3).

## Scope

- **In (LANDED `67723588`, verify):** capabilities `chat.guardrail`
  (`{violations[], warnings[]}`) and `chat.compact` (`{summary}`), sealed
  structured output, backfill family `chat-practice-assignments` from
  `chat.turn`; `holdspeak/services/thread_practice.py` runner entrances;
  census rows; `tests/unit/test_hs153_practice_capabilities.py`.
- **In (this story):** guardrail notes — a Note tagged `guardrail`
  {instruction, trigger tools, N}; seeds `effect-guard` (any effect
  touching a person's ledger without a named source) and `egress-guard`
  (cloud egress of a `people.*` read); per-mode enablement (`tools_json`
  sibling key `guardrails`). Loop timing: tool_calls extracted →
  guardrail admission ONCE via `thread_practice` → `thread_guardrail`
  frame + a `guardrail` part on the assistant message → THEN per-call
  admission with `default_decision` carried on `thread_tool_pending`
  (`deny` when a violation names the call and control_mode ≠ yolo).
  Pullout: the guardrail row (violations red, warnings amber, in-flow,
  RAW fold); the decision box honours the default.
- **Out:** auto-deny (recorded), guardrails outside threads.

## Acceptance criteria

- [ ] Real coordinator, fake engines for both capabilities: a pending `people.commitment.transition` without a source → `effect-guard` violation → `thread_guardrail` frame + part; in yolo the call still runs; in safe the pending frame carries `default_decision: deny`.
- [ ] The guardrail engine failing (exception / timeout 10 s) → one `guardrail_failed` warning row; the turn continues; no call denied.
- [ ] The guardrail runs ONCE per pass regardless of call count; disabled per mode → no admission at all (no receipt).
- [ ] Glass 1440 + 393: the row renders, the decision box shows Deny focused by default under a violation.

## Test plan

- **Unit:** `tests/unit/test_hs153_practice_capabilities.py` (extend) + `tests/unit/test_thread_guardrail.py` (real coordinator + fake engine + capture, the story-03/152 pattern).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` leg `guardrail`.
- **Manual / device:** story 06 (`effect-guard` fires on `.43`).

## Notes / open questions

- The guardrail model's payload = the last N message contents + the pending calls' names/args heads — it crosses the fence too: `_m1_redactor` applies to its admission as well (its own `payload_redactor`).
