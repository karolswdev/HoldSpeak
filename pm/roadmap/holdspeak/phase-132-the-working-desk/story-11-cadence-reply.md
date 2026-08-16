# HS-132-11 — Cadence answers land

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** none
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The Cadence surface renders a reply pad and a Send reply button for an agent
question, and clicking it 404s: `web/src/pages/cores/CadenceCore.tsx:45,113`
POSTs `/api/cadence/loops/{id}/reply`, but
`holdspeak/web/routes/cadence.py:60-79` defines only `/loops/{loop_id}`,
`/snooze`, `/kill`, `/close`. Two named tests are red for exactly this
(`tests/integration/test_cadence_agent.py:94` assert 404 == 200; the
empty/non-agent/missing-pane rejection test asserts 404 == 400). The owner
cannot answer a waiting agent from the desk.

## Scope

### In

- Implement `POST /api/cadence/loops/{loop_id}/reply` delivering the reply
  into the loop's pane/agent per the existing service contract, with named
  400 refusals for empty replies, non-agent loops, and missing panes.
- Surface the delivery result on the Cadence card (success/refusal) through
  the HS-132-06 receipt channel.

### Out

- Cadence/Follow-through consolidation (#450 Wave 2 — backlog); loop
  scheduling changes.

## Acceptance criteria

- [ ] Send reply delivers and the two red tests pass in isolation and
  in-suite.
- [ ] Empty and non-agent replies refuse by name with 400; a missing pane
  refuses by name with 409. (Amended at implementation, 2026-08-15: the
  charter said 400 for all three, but the canonical contract test —
  tests/integration/test_cadence_agent.py:109, from the original CAD-3-03
  contract in 18c0539e — pins the missing pane at 409, which is also the
  truer status for a conflict with live session state. The test won. Owner
  may overrule at the sitting.)
- [ ] The desk shows the delivery outcome.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/integration/test_cadence_agent.py --tb=short`
- vitest: CadenceCore reply outcome rendering.
