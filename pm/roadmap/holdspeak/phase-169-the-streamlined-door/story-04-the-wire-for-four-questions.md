# HS-169-04 - The wire for the four questions (needs-you items derived from real Watch entities; the read marker; the health inputs; the meeting Watch never offered until it evaluates; MCP twins)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** done
- **Depends on:** HS-169-01
- **Unblocks:** HS-169-03
- **Owner:** unassigned

## Problem

The Room's four questions need facts the hub already holds but does not serve as one shape: PR review requests and CI on the base branch, overdue Jira issues, pending Delta proposals, changes since a read marker that does not exist yet, and a native `meeting` Watch that can never evaluate but was offered.

## Scope

- **In:** `GET /api/projects/{id}/room` extended (additive) with `needsYou[]` (source, title, why-token, since, url, verb) derived from the Watch snapshots the wire has (PR `reviewRequests`/`reviewDecision` + updated_at age; CI check failures on the base branch; Jira OVERDUE entities; Delta proposals pending), `sources[]` (scope, count tokens, checkedAt, host, state, plainReason), `health` (state + reason token + the inputs), `sinceRead` (a per-project read marker written when the Room is read; changes grouped by source in phrases — the journal's raw kinds mapped ONCE to phrases in the service), `decisions[]` + `commitments[]` = the decision records whose source meeting is linked to the project (the existing project ↔ meeting link; commitments via their decision; a query, no new column — counsel M2); a `branch_ci` query kind on the GitHub source (`gh run list --branch <base> --limit 1` → conclusion + age) behind the Door's default `CI` Watch and the Room's `CI RED ON MAIN` row (counsel M1 — new wire, named here); the per-project read marker as ONE nullable column (additive, schema snapshot regenerated in the same commit — counsel S3); the health derivation (AT RISK when overdue > 0 OR CI failing OR a review waiting > 3 days; else ON TRACK; the reason token = the first true input) pinned by tests; the native `meeting` template retired from suggestion until an adapter exists (a failing existing one reports `plainReason`); MCP twins `project_get_room` extended in place (MCP-001 parity); the sidecar composes on the same service.
- **Out:** new providers; new tables beyond the read marker (one column or one small table — the owner's ruling: migrations stay minimal; additive, self-reconciling).

## Acceptance criteria

- [ ] Characterization tests over a fixture desk: 3 needs-you rows from real-shaped entities; health AT RISK with reason `3 OVERDUE`; sinceRead groups phrases; no raw kind leaks (a guard).
- [ ] Test-path/evaluation parity for the count preview (168's law) — one compile.
- [ ] The meeting template is absent from suggestions on a fresh desk; an existing failing one reports its plain reason.
- [ ] MCP `project_get_room` returns the same shape as the route (a parity test).

## Test plan

`uv run pytest -q tests/unit/test_hs169_wire.py tests/unit -k "room or project_service or watch"` in an isolated HOME; the MCP parity test; schema snapshot regenerated in the same commit as any column.

## Delivered (2026-09-05)

- `GET /api/projects/{id}/room` extended additively: `needsYou` (PR review requests / CHANGES_REQUESTED aged by updated_at; `CI failing on <base>` from the new `branch_ci` kind; Jira OVERDUE entities; pending Delta proposals; ordered by severity), `sources` (scope, zero-omitted count tokens, checkedAt, nextCheckAt, host, state live/paused/cant_check, plainReason mapped once), `health` (`assessment` at_risk/on_track — the section stamp owns `state` — reason = first true input of overdue > 0, CI failing, review waiting > 3 days, target passed), `sinceRead` (read marker + groups in phrases; a guard forbids raw kinds), `decisions` + `commitments` (records whose source meeting is linked via meeting_projects — a query, no column), `target` (daysLeft, passed), `nextCheckAt` (soonest live source). `POST /api/projects/{id}/room/read` writes the ONE new nullable column `projects.room_read_at` (schema declarative, snapshot regenerated, fence green).
- `branch_ci` query kind on GitHubWatchSource (`gh run list --repo <r> --branch <base> --limit 1 --json conclusion,status,name,url,updatedAt,headBranch`; `run list` allow-listed in github_cli; template `watch.github.branch_ci` labelled CI).
- The native meeting template retired from suggestions (project_setup_service.py:347-359, parked not deleted); an existing meeting watch reports `No local adapter for meeting activity yet`.
- MCP `project_get_room` returns the same shape from the same service (parity test).
- model.ts decode + types for every new field (model.test.ts 34).
- Tests: tests/unit/test_hs169_wire.py 27; 15 setup-service tests that used the meeting proposal as a fixture given honest edits; evidence: 149 passed (wire + setup service + templates + room read + the schema fence).
