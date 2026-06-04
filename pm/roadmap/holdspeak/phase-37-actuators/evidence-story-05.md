# Evidence — HS-37-05: Reference actuator end-to-end

**Date:** 2026-06-04. **Branch:** `phase-37/hs-37-01-actuator-contract`.

## What shipped

The first concrete actuator, proving the whole loop — propose → approve → execute →
audit — with a **real, observable side effect** and the critical negatives.

### Files

- **`holdspeak/plugins/builtin/followup_ticket_actuator.py` (new)** — two deliberately
  separate halves (the safety split):
  - **`FollowupTicketActuator`** (`kind="actuator"`, `required_capabilities=["actuator"]`)
    — `run(context)` finds the first action item **without an owner** and returns an
    `ActuatorProposal` for the follow-up ticket it *would* write (target `outbox`, a
    faithful preview + a Markdown `payload`). It never reaches out; with nothing to
    propose it raises (→ the host records a plain `error`, no proposal).
  - **`build_outbox_connector(outbox_dir, dry_run=, writer=)`** — the connector the
    executor calls *after* the guards pass: it writes the ticket to a local **outbox**
    file (the egress point — a filesystem write, no network) and returns the path/bytes.
  - **`register_followup_actuator(host)`** — explicit, opt-in registration; **not** in
    `register_builtin_plugins`, so the default plugin set + routing chains are unchanged.

### Design decision (was deferred): the reference side effect

The story's default was "reuse the gh/jira CLI connector." On inspection the existing
`github_cli` connector pack is **read-only by policy** (`gh pr view`/`issue view`) — the
Phase-25 egress posture forbids unattended writes — and a real `gh issue create` needs
credentials and creates real, non-reproducible tickets. So the reference uses a **local
outbox file write**: a genuine, observable, reversible external artifact that is **CI-safe**
(no network, no creds). A gh/jira/webhook connector is a future actuator on the same
`ActuatorExecutor` contract (the executor is connector-agnostic). Recorded here per the
story's "record the choice in the evidence."

## Verification — 7 cases (default suite, real temp-file side effect)

```
$ uv run pytest -q tests/unit/test_actuator_reference.py
7 passed
```

- **Faithful proposal** — the proposal's preview names the unowned task and the payload
  body carries it; the filename is `*.md`.
- **Nothing to propose** — an all-owned context → the actuator raises → host `error` (no
  proposal, no side effect).
- **Capability gate** — without `actuator` in `enabled_capabilities`, proposing is
  `blocked`.
- **Full loop** — propose → persist (`record_actuator_proposal`) → **execute before
  approval is refused** (`ActuatorExecutionError`, no file) → approve → execute → the
  **real file exists on disk** (`executed.result["path"]`, content carries the task) →
  audit chain `[proposed, approved, executed]`.
- **Gate off / not allow-listed** → `ActuatorPolicyError`, no file, proposal stays
  `approved` (retryable once the gate is enabled).
- **Default set unaffected** — `ACTUATOR_ID not in register_builtin_plugins(host)`.

## Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2080 passed, 15 skipped in 57.99s        # +7 (the reference-actuator tests)
$ uv run ruff check holdspeak/plugins/builtin/followup_ticket_actuator.py
All checks passed!    # (+ F821 clean)
```

## Notes

- The full loop here **is** the real loop — the connector performs an actual filesystem
  write (not a mock), so the "side effect is observable" criterion is met without network
  egress or credentials. Re-targeting at gh/jira/webhook is a connector swap on the same
  contract (a future actuator), not a change to the safety machinery.
- Routing is untouched: the actuator is invoked by id in the test (`host.execute`), never
  added to a router chain — so the default dispatch path stays byte-identical.
