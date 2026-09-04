# HS-169-04 - The wire for the four questions (needs-you items derived from real Watch entities; the read marker; the health inputs; the meeting Watch never offered until it evaluates; MCP twins)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** backlog
- **Depends on:** HS-169-01
- **Unblocks:** HS-169-03
- **Owner:** unassigned

## Problem

The Room's four questions need facts the hub already holds but does not serve as one shape: PR review requests and CI on the base branch, overdue Jira issues, pending Delta proposals, changes since a read marker that does not exist yet, and a native `meeting` Watch that can never evaluate but was offered.

## Scope

- **In:** `GET /api/projects/{id}/room` extended (additive) with `needsYou[]` (source, title, why-token, since, url, verb) derived from the Watch snapshots the wire has (PR `reviewRequests`/`reviewDecision` + updated_at age; CI check failures on the base branch; Jira OVERDUE entities; Delta proposals pending), `sources[]` (scope, count tokens, checkedAt, host, state, plainReason), `health` (state + reason token + the inputs), `sinceRead` (a per-project read marker written when the Room is read; changes grouped by source in phrases — the journal's raw kinds mapped ONCE to phrases in the service), `decisions[]` + `commitments[]` from the existing records; the native `meeting` template retired from suggestion until an adapter exists (a failing existing one reports `plainReason`); MCP twins `project_get_room` extended in place (MCP-001 parity); the sidecar composes on the same service.
- **Out:** new providers; new tables beyond the read marker (one column or one small table — the owner's ruling: migrations stay minimal; additive, self-reconciling).

## Acceptance criteria

- [ ] Characterization tests over a fixture desk: 3 needs-you rows from real-shaped entities; health AT RISK with reason `3 OVERDUE`; sinceRead groups phrases; no raw kind leaks (a guard).
- [ ] Test-path/evaluation parity for the count preview (168's law) — one compile.
- [ ] The meeting template is absent from suggestions on a fresh desk; an existing failing one reports its plain reason.
- [ ] MCP `project_get_room` returns the same shape as the route (a parity test).

## Test plan

`uv run pytest -q tests/unit/test_hs169_wire.py tests/unit -k "room or project_service or watch"` in an isolated HOME; the MCP parity test; schema snapshot regenerated in the same commit as any column.

## Delivered

_(pending)_
