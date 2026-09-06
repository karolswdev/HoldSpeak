# HS-190-03 — The command core: idempotency, CAS, state machines

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-190-02, HS-190-04
- **Unblocks:** HS-190-05, HS-190-06, HS-190-07, HS-190-08, HS-190-09, HS-190-11
- **Owner:** unassigned

## Problem

Core Memory mutations span proposals, claims, scope changes, privacy changes,
source deletion, and removal. Without one typed command boundary, retries and
concurrent edits can publish contradictory truth or report failure after a
successful commit.

## Scope

- **In:** command envelope; actor/authority record; stable result and error
  registry; idempotency ledger; payload-digest conflict detection; one or more
  expected-version preconditions; transactional mutation/outbox boundary;
  proposal, claim-version, correction, and removal state machines; consumption
  of source-owner events without taking over canonical source state machines;
  post-timeout status lookup.
- **Out:** source adapters, cryptography, planner, product UI, and background
  derivative execution.

## Acceptance criteria

- [ ] Same command ID + same canonical payload returns the durable original
  result; same ID + different payload returns a stable conflict error.
- [ ] CAS validates every supplied precondition atomically and reports the
  exact stale subjects without partially publishing mutations.
- [ ] All transitions are closed and validated; correction forks/cycles,
  resurrection after removal, and invalid proposal acceptance are refused.
- [ ] Domain mutation, command result, and required source-outbox rows commit in one
  transaction; crash before commit leaves none and crash after commit replays
  the committed result.
- [ ] Typed errors cross Python/HTTP/MCP boundaries without string parsing and
  without private values in the envelope.
- [ ] Timeout-after-commit can be reconciled by command ID without repeating
  side effects.

## Test plan

- **Unit:** canonical payload identity, every state transition, typed envelope.
- **Concurrency:** simultaneous matching/conflicting CAS and multi-subject CAS.
- **Fault:** crash/timeout before and after commit, duplicate delivery, recovery
  scan, locked database, and outbox publication retry.
- **Contract:** Python, HTTP, and MCP fixtures normalize to the same outcome.

## Notes / open questions

- CF-0 §7 and TXN-001–004 are normative.
- Command success means durable domain intent, not completion of eventual
  derivative purge; removal exposes its barrier/progress separately.
