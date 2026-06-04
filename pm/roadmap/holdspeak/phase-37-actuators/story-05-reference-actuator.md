# HS-37-05 — Reference actuator end-to-end

- **Project:** holdspeak
- **Phase:** 37
- **Status:** not-started
- **Depends on:** HS-37-04
- **Unblocks:** HS-37-06
- **Owner:** unassigned

## Problem

The contract, persistence, approval UI, and executor are only believable when one real
actuator runs the whole loop. This story ships exactly **one** reference actuator and
proves proposal → approve → execute → audit end-to-end — and, critically, that **nothing
runs without approval**.

## Scope

- **In:**
  - **One** reference actuator (default: reuse an existing connector — a gh/jira CLI
    follow-up, e.g. `followup_ticket_actuator` that proposes "file a follow-up issue for
    the unowned action item"; final target chosen at this story's design step). It
    declares `kind: actuator`, a `required_capabilities` (e.g. `actuator` + the connector's
    capability), and emits an `ActuatorProposal` with a faithful preview + payload.
  - Wire it through the full stack: host proposes → persisted → shown in the approval UI →
    approved → guarded executor runs it via the connector → `executed` + audit.
  - An **opt-in** integration/spoken test (gated like the spoken-e2e) that drives the real
    loop once: asserts the preview is shown, approval is required, execution happens only
    after approval, and an audit entry is written. Plus a **negative** assertion: with no
    approval (or the gate off), no side effect occurs.
  - Register the actuator behind the gate so the **default** suite + routing are unaffected.
- **Out:**
  - A second actuator or a general actuator pack (one reference only this phase).
  - Autonomous/unattended execution.

## Acceptance criteria

- [ ] The reference actuator proposes a faithful action (preview == payload meaning); it
      surfaces in the approval UI.
- [ ] End-to-end (opt-in): approve → execute → `executed` + audit entry; the side effect
      is observable (e.g. the connector dry-run/real call recorded).
- [ ] **Negative:** no approval (or gate off / not allow-listed) ⇒ no side effect, proposal
      stays `proposed`/blocked; asserted explicitly.
- [ ] Default suite + routing unaffected (actuator gated/unregistered by default).
- [ ] Suite green; the new module ruff + F821 clean.

## Test plan

- Opt-in integration/spoken test (gate + capability on): full loop, with the connector in
  a controlled/dry-run mode so it's deterministic; verified once for real if the connector
  target is reachable (document the run).
- Negative test (default suite): actuator present but gate off / unapproved ⇒ no outbound
  call (spy), proposal not `executed`.
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- Decision (this story): the concrete target — default reuse the gh/jira CLI connector
  (least new infra) over a new webhook primitive; record the choice in the evidence.
- Keep the actuator's `run()` pure-ish: build the proposal from the meeting context
  (e.g. an unowned action item), don't reach out — reaching out is the executor's job.
- Mirror the plugin authoring/testing pattern from `docs/PLUGIN_AUTHORING.md`; HS-37-06
  extends that doc with the actuator specifics.
