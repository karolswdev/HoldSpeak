# Phase 37 — Actuators — Final Summary

**Status:** CLOSED ✅ — 7/7 stories shipped. **Closed:** 2026-06-04.

The phase that turns on the plugin system's **third kind** — the **actuator** — without
ever letting an external side effect happen silently. Every story exists to serve one
invariant:

> **No external side effect occurs without an explicit, audited, per-action human
> approval — and what executes is exactly what was previewed.**

An actuator *proposes* a side effect (file a ticket, post a message); the effect only
happens after a human approves it and the governance gate admits it, performed by a
separate guarded executor that re-checks payload parity and writes an audit trail.

## The egress-posture review (the headline)

There is **no code path** by which an actuator's side effect runs without all of:

1. **A registered, capability-enabled actuator** — actuators are *not* in
   `register_builtin_plugins`; one must be explicitly registered, and `actuator` must be
   in the host's `enabled_capabilities`, or proposing is `blocked`.
2. **A persisted `approved` proposal** — `ActuatorExecutor.execute` refuses anything whose
   status isn't `approved` (`ActuatorExecutionError`); approval is a deliberate human act
   via the UI / decision endpoint, recorded with `decided_by` + an audit entry.
3. **The governance gate** — `MeetingConfig.allow_actuators` (master switch, default
   `False`) **and** membership of `allowed_actuators` (per-project allow-list); a refusal
   raises `ActuatorPolicyError` with **no state change**. Default-safe: off + empty ⇒
   nothing runs.
4. **Payload parity** — the side effect is built from the proposal's stored `payload`; a
   hash mismatch between what was approved and what would execute aborts to `failed` with
   **no outbound call** (TOCTOU guard).
5. **An audit row** — every terminal transition (`executed` / `failed`) is recorded via
   `transition_proposal`, carrying the payload hash.

The negative is proven, not asserted: the reference-actuator tests execute **before**
approval, with the gate off, and when not allow-listed — each produces **no side effect**
(no outbound call; the local outbox file is absent). Visual: `evidence/actuator_lifecycle.png`
(awaiting-approval → executed-with-audit-trail → rejected); the approval surface itself in
`evidence/approval_surface.png`.

## What shipped

| Story | Target → result |
|---|---|
| **HS-37-01** | Actuator **contract** + unblock the kind. `ActuatorProposal` (target/action/preview/payload/reversible/required_capabilities) with `from_run_output` validation; `plugin_sdk` accepts `kind: actuator` + the `actuator` capability; the host runs an actuator to a **`proposed`** result (never an inline side effect; a malformed proposal is a plain `error`). Default path byte-identical. |
| **HS-37-02** | Proposal **persistence + lifecycle**. `ActuatorRepository` (`db.actuators`) + `actuator_proposals` / `actuator_proposal_audit` tables; idempotent; the lifecycle `proposed → approved → executed | rejected | failed` (retry from `failed`) enforced; a row per transition. Canonical schema snapshot regenerated. |
| **HS-37-03** | **Approval surface**. `GET /proposals` (a pure read) + `POST …/decision` (`approved`|`rejected`, never executes); a Signal "Proposed actions" card stack (preview + target + reversibility + Approve/Reject), decided rows quieted. |
| **HS-37-04** | **Guarded executor + governance gate**. `ActuatorExecutor` — status + policy gate + payload parity + injected-connector egress + audited `executed`/`failed`; `MeetingConfig.allow_actuators` + `allowed_actuators` (default-safe). |
| **HS-37-05** | **Reference actuator end-to-end**. `followup_ticket_actuator` (proposes a follow-up ticket for an unowned action item) + `build_outbox_connector` (a local-file side effect, CI-safe) + opt-in registration; the full loop + the negatives proven against a real file. |
| **HS-37-06** | **Actuator documentation** (dedicated story, user ask). `docs/PLUGIN_AUTHORING.md` Actuators section + a `README.md` paragraph + doc-truth reconciliation (no live doc calls actuators deferred). |
| **HS-37-07** | Closeout — egress-posture review, the lifecycle demo, this summary. |

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **2,080 passed, 15 skipped**. The actuator stack alone: **55** tests
  (`test_actuator_contract` / `_repository` / `_executor` / `_reference` +
  `test_web_meeting_proposals_api`).
- **Routing invariants intact:** no actuator is registered by default and none is in a
  router chain, so `test_intent_router` / `test_intent_dispatch` / `test_intent_pipeline`
  are unchanged and green (18 passed). The host's `proposed` status and the dispatch
  proposal-persistence hook are additive + dormant by default.
- **No silent egress, by construction** — see the review above; the default suite makes
  no real outbound call (the reference connector writes a local file; executor tests use a
  spy).
- **Bundle:** `holdspeak/static/_built/` is a gitignored build product — rebuilt to verify,
  **0 files tracked**; only `web/src/**` source committed.
- **Docs:** `docs/PLUGIN_AUTHORING.md` Actuators section + the README paragraph; doc
  drift-guard + live-doc link-check green.
- **Branch:** `phase-37/hs-37-01-actuator-contract` (phase open + 7 story commits + the
  docs-story roadmap commit).

## Decisions of record

- **The unit of work is a *proposal*, not an action** — an actuator never executes inline.
- **Per-action approval *always*** — `MeetingConfig.allow_actuators` + `allowed_actuators`
  are *additional* gates; neither removes the approval+audit step.
- **The audit log is a dedicated table** (`actuator_proposal_audit`, CASCADE-scoped).
- **The reference side effect is a local outbox file**, not the deferred gh/jira default —
  the existing `github_cli` pack is read-only by Phase-25 policy and real `gh issue create`
  needs creds / makes real tickets; a local outbox is real, observable, reversible, and
  CI-safe. gh/jira/webhook are future connectors on the same `ActuatorExecutor` contract.
- **Documentation is its own story (HS-37-06)** — promoted from a closeout footnote on
  direct user ask.

## Handoff → the next frontier

The actuator machinery is complete and safe; the natural extensions (none committed):

- **More connectors** — gh/jira/webhook actuators on the same `ActuatorExecutor` contract
  (the read-only `github_cli` pack would need a write-permitted, gated variant).
- **Live proposals** — surface actuator proposals during an in-progress meeting (today the
  approval UI is the saved-meeting detail) + a broadcast on new proposals.
- **Multi-step / chained actions** and **per-role governance** (who may approve which
  actuator) — both deliberately out of scope this phase.
