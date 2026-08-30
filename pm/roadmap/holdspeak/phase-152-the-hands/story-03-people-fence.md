# HS-152-03 - The People fence (sensitive results, multi-pass redaction)

- **Project:** holdspeak
- **Phase:** 152
- **Status:** backlog
- **Depends on:** HS-152-02
- **Unblocks:** HS-152-06
- **Owner:** unassigned

## Problem

DC-01 redacts sensitive parts at the coordinator, but a tool loop
creates new sensitive material mid-turn: `people.*` results (counsel M1,
M2). The fence must hold on every pass and on every later cloud turn.

## Scope

### In

- `people.*` result parts inserted with `sensitive=1` (M2).
- `_sensitive_texts` accumulated across passes and re-injected before every `payload_redactor` call (M1).
- People effects only via the truth table; the family's own refusals untouched.

### Out

The DC-03 egress-guard (paraphrase laundering — recorded R2).

## Acceptance criteria

- [ ] Through the REAL coordinator: a `people.*` tool result on a local turn, then `profile_override` → cloud; the captured payload contains `[people content withheld]` and no sentinel; the part row has `sensitive=1`.
- [ ] Within one multi-pass turn on a cloud profile, pass 2's payload already withholds pass 1's people result.
- [ ] A non-people tool result passes verbatim on cloud.

## Test plan

- **Unit / integration:** tests/unit/test_thread_people_fence.py (real coordinator + fake engine + capture); the metal script leg 2 extended.
- **Manual / device:** `.43` leg 2 in story 06.
