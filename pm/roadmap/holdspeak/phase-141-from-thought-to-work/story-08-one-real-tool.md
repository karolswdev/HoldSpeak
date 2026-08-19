# HS-141-08 — One real tool

- **Status:** backlog
- **Depends on:** 141-07
- **Unblocks:** 141-09

## Problem

The phase must prove thought-to-work rather than stop at a nicer Note. GitHub
issue creation exists; Jira write does not. The proof must use real capability
truth and the existing effect spine.

## Scope

Expose GitHub issue availability through the narrow adapter only when the
existing host configuration `meeting.companion_github_repo` names the
repository. Phase 141 adds no repo picker or second configuration path. Freeze
the config key/value provenance with the refinement revisions and revalidate it
before proposal and execution. Build the exact existing actuator preview and
payload, create the existing
`ActuatorProposal` as the first durable external proposal, require linked kernel
admission for this new flow, and execute under current posture. The adapter is
thin and explicit: `broker.submit(actuator.egress)` → `broker.decide` → existing
executor claim; refinement code never calls `gh` itself. Under the default YOLO
posture a configured eligible proposal proceeds without a redundant approval;
Neutral/Safe retain their existing decision step.

Capability truth has two levels: `meeting.companion_github_repo` can establish
**Repo configured**, but local `gh` authentication/readiness remains **Unknown
until execution** and may refuse truthfully then. A stable local request key
prevents local redispatch where outcome is known. Because `gh issue create`
provides no remote idempotency contract, a dispatched request with a lost or
ambiguous response enters **Needs manual reconciliation** and is never
automatically reissued or falsely called exactly-once.

Extend the existing actuator and linked-kernel lifecycle with one durable
**Needs manual reconciliation** / indeterminate outcome for post-dispatch
ambiguity. This is not a second executor. Ordinary decide/reapprove/retry routes
must refuse while indeterminate; only an explicit reconciliation transition can
record the remote outcome and release or close it. The linked kernel receipt
must remain indeterminate until that transition.

Do not add Jira, calendar, a generic form/schema engine, or a second executor.

## Acceptance

- [ ] No GitHub button without `meeting.companion_github_repo`; the glass
  distinguishes **Repo configured** from **GitHub readiness unknown until
  execution**, and no new repo selection system appears.
- [ ] Frozen proposal records repo/config provenance and refuses with Update
  proposal if the configured repo changes before execution.
- [ ] Preview/payload/source/destination parity is rechecked before effect.
- [ ] Source/context drift requires Update proposal.
- [ ] Known local retries never redispatch; ambiguous post-dispatch outcomes enter
  **Needs manual reconciliation** with no automatic retry and no remote
  exactly-once claim.
- [ ] Direct actuator decision/reapproval routes cannot move an indeterminate
  proposal back to execution; explicit reconciliation is durable and receipted.
- [ ] Refusal/failed/indeterminate states retain the completed thought and exact
  repair/reconcile action.
- [ ] Actuator audit and linked kernel receipt both resolve from the thought.

## Tests

Focused adapter/actuator/kernel/local-dedup/manual-reconciliation tests plus a live
configured GitHub issue drill only at the owner-authorized sitting boundary.
