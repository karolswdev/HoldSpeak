# HS-38-04 — Live in-meeting proposals + broadcast

- **Project:** holdspeak
- **Phase:** 38
- **Status:** not-started
- **Depends on:** none (uses the Phase-37 approval API; independent of the connectors)
- **Unblocks:** HS-38-05
- **Owner:** unassigned

## Problem

Today an actuator proposal is only visible when you open a **saved** meeting. For a real
"do this now?" moment, a proposal should surface **during** the meeting — broadcast as it's
produced, shown in the live dashboard, and approvable on the spot — without weakening the
gate (actuators off by default; nothing runs without approval).

## Scope

- **In:**
  - **Broadcast on a new proposal.** When an actuator proposes during a live meeting, emit
    an `actuator_proposed` event through the existing live path (`MeetingSession`
    `on_broadcast` → `WebRuntime` `server.broadcast(type, data)`; the precedent events are
    `intel_status` / `segment` / `intel_complete`). The payload is the proposal (id +
    preview + target + reversibility) — never anything that itself egresses.
  - **A live "pending actions" panel** on the meeting dashboard that lists live proposals
    and offers **Approve / Reject**, reusing the HS-37-03 decision endpoint
    (`POST …/proposals/{id}/decision`) + the Signal proposal-card styling. Approving live
    records the decision (+ audit); execution remains the guarded executor's job.
  - Default **off** (actuators off by default); the saved-meeting "Proposed actions"
    surface (HS-37-03) is unchanged and still works.
- **Out:**
  - Executing automatically on live approval beyond what the guarded executor already does
    (approval → execute is the existing path).
  - New proposal *generation* machinery — surface what the existing dispatch produces.

## Acceptance criteria

- [ ] A new actuator proposal during a live meeting **broadcasts** (`actuator_proposed`)
      and the live dashboard shows it in a pending-actions panel.
- [ ] Approve / Reject from the live panel hits the decision endpoint, flips state + writes
      an audit entry, and performs **no** side effect on its own.
- [ ] Default off; the broadcast carries no egress-capable payload; the saved-meeting
      surface is unchanged.
- [ ] `cd web && npm run build` succeeds (bundle gitignored, not committed); suite green.

## Test plan

- Unit/integration: a proposal produced in a live meeting emits the `actuator_proposed`
  broadcast (assert via the broadcast spy); the live decision path flips state + audits.
- API: the live panel uses the same `decision` endpoint (already covered) — assert no new
  execution path.
- Manual: rebuild; in a live meeting (or a simulated one), confirm the panel appears,
  approve/reject works, and nothing executes without approval.
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- Open question (design): **where live actuators generate** — reuse the
  finalization-time dispatch vs a live dispatch tick. Default: surface proposals as soon as
  the existing dispatch produces them; a dedicated live cadence is a follow-up if the
  finalization timing feels too late.
- Keep the broadcast payload **read-only** — it describes a proposal; it must never carry
  anything that could trigger an effect on receipt.
