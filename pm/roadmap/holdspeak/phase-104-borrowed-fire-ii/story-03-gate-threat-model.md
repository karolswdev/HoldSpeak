# HS-104-03 - The gate under attack — restart, replay, TOCTOU

- **Project:** holdspeak
- **Phase:** 104
- **Status:** done
- **Depends on:** HS-104-02
- **Unblocks:** HS-104-07
- **Owner:** unassigned

## The council finding (the bar)

The council's core objection to the AgentGlass design was not a bug
but a *class* of bugs: any gap between what was approved and what
executes. Phase 87 earned its trust the same way — the recycled-pane
and TTL crown cases were stories, not afterthoughts. The gate gets
the same treatment: a dedicated story whose only deliverable is the
gate surviving a hostile checklist, each item proven by a test that
fails on the naive implementation.

## Problem

HS-104-02 ships the mechanism. Until each threat below has a pinned
regression test, the gate's honesty is a claim, not a proof
(Article IX).

## The checklist (each item = one or more pinned tests)

1. **Restart mid-hold.** Hub dies with a proposal `held`; on
   restart the proposal is `invalidated`, the polling hook receives
   deny-with-reason, and no card for it renders on the shade.
2. **Replay of a decided proposal.** The hook (or an attacker on
   loopback with the token) re-POSTs an already-approved idempotency
   key: the hub returns the terminal state, mints nothing, and the
   audit shows one decision, two arrivals.
3. **TOCTOU on the arguments.** A proposal is held; a second POST
   arrives with the same idempotency key but a different args hash:
   refused by name (`args_mismatch`), the original proposal
   `invalidated` (the Phase-87 refuse-AND-revoke reflex), audit row
   written.
4. **Expiry race.** Decision lands at expiry ± ε: exactly one
   terminal state wins; the loser transition is refused by the state
   machine, not lost. Use an injectable clock (the grant store's
   monotonic-clock pattern) — no sleeps.
5. **Double decision.** Approve and Deny race from two clients (two
   desk tabs suffice): first write wins, second gets a typed 409
   naming the standing decision.
6. **Fail-closed integrity.** Gate armed, hub stopped: the hook
   denies. Gate armed, hub returns 500: the hook denies. Gate
   armed, decision poll times out mid-wait: deny. The hook has no
   code path that allows on error.
7. **Unarmed inertness.** Gate off: the hook's fast path adds no
   proposal row, no audit row, and bounded latency (assert on a
   budget, generous but pinned).
8. **Redaction.** No full argument payload anywhere: not in the DB
   row, not on the wire to the shade, not in logs. Grep-census over
   the gate modules, in the HS-87 style.

## Out of scope

- New gate features. This story only hardens; if a threat can't be
  closed without redesign, it blocks HS-104-02's done-ness rather
  than growing scope here.

## Acceptance

- Every checklist item has a test that demonstrably fails when its
  guard is commented out (note the mutation check in evidence for at
  least items 1, 3, and 6 — the load-bearing three).
- The full suite green; the census green.

## Test plan

- **Unit/integration:** as per checklist; the fake-agent rig from
  HS-104-02 reused with fault injection (kill the hub process for
  item 1 and 6 — a real process, not a mock, per the two-process
  proof pattern from Phase 89/94).

## Chef's notes

- Write the attack tests *against the naive design first* if any
  doubt exists about whether they bite — a threat test that passes
  on broken code is worse than none (the "read output before flip"
  rule applies doubly here).
- Item 3's refuse-AND-revoke matters more than it looks: refusing
  the mismatch but leaving the original decidable lets an attacker
  aim the human's Approve at a payload the human never saw.
