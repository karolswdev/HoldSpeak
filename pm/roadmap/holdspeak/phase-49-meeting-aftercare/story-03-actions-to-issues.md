# HS-49-03 — Close the loop: accepted actions to issues

- **Project:** holdspeak
- **Phase:** 49
- **Status:** done
- **Depends on:** HS-49-01
- **Owner:** unassigned

## Problem
The highest-value loop to close is "we agreed someone will do X" becoming a real
tracked item (a GitHub issue, a webhook, a ticket). The actuator system
(Phase 37/38) already does propose -> approve -> execute with audit, off by
default, and there is a GitHub issue actuator. But it fires on "the first unowned
action item", and aftercare wants the user-driven "take this **accepted** action
and file it" from the surface where they just reviewed it.

## Scope
- **In:**
  - From the aftercare surface, a path that turns an **accepted** action item
    (`review_state = accepted`) into an actuator **proposal** (GitHub issue /
    connector) through the **existing** `propose -> approve -> execute` flow
    (`ActuatorProposal`, `ActuatorRepository`, `ActuatorExecutor`, the
    `github_issue_actuator` / gated-connector pattern).
  - Surface the resulting proposal with the existing approve/reject + execute
    controls and audit trail (reuse `GET /api/meetings/{id}/proposals` +
    `POST .../proposals/{pid}/decision`).
- **Out:** the aggregation (HS-49-01); provenance (HS-49-02); the draft (HS-49-04).
  This story wires accepted actions into the actuator system.

## Acceptance criteria
- [x] An accepted action item can become an actuator proposal from the aftercare
      surface, through the existing propose -> approve -> execute path; **no new
      write primitive** (reuses `record_proposal` + `build_github_issue_connector`).
- [x] Off by default and safe: execution still requires `allow_actuators` + the
      per-project allow-list + a host-injected connector; per-action human
      approval; the payload-parity (TOCTOU) gate and audit trail hold; refusal is
      graceful.
- [x] Behavior-preserving (no auto-execute, no egress without approval); tests
      assert proposal creation from an accepted action + that an unapproved
      proposal never executes; `npm run build` ✓; 0 `_built/` tracked.

## Test plan
- Integration: accept an action -> create a proposal -> it lists as `proposed` ->
  decision approves -> a stub connector executes -> audit row written; an
  unapproved proposal is refused by the executor; reuse
  `tests/integration/test_web_meeting_proposals_api.py` +
  `tests/unit/test_actuator_executor.py` patterns;
  `uv run pytest -q -k "actuator or proposal or meeting or aftercare"`.
- Manual: from the aftercare surface, file an accepted action as a GitHub-issue
  proposal (stub connector), approve, see it execute + audited.

## Notes / open questions
- Reuse `github_issue_actuator` / `gated_connector` (manifest allow-check before
  egress). Do not invent a new connector primitive.
- The existing GitHub actuator targets "first unowned action item"; here the seam
  is the user-selected **accepted** action. Decide whether to generalize the
  existing actuator or add a thin proposal-builder over the same connector
  (favor reuse).
- Make the privacy posture explicit at the point of action (what leaves the
  machine, that it's approval-gated) — ties to the backlog "privacy at decision
  points" bet, kept lightweight here.
