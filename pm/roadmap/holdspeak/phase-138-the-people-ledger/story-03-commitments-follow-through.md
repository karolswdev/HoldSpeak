# HS-138-03 — Commitments join Follow-through

- **Project:** holdspeak
- **Phase:** 135
- **Status:** ready
- **Depends on:** 135-01, 135-02
- **Unblocks:** 135-04, 135-05
- **Owner:** delegated Terra worker; primary adjudicates

## Problem

Manager promises must join HoldSpeak's one obligation surface without becoming
plaintext `action_items`, Cadence loops, or a second People task board.

## Scope

- **In:** explicit request→manager-commitment transition; narrow encrypted
  projection interface; ephemeral FollowThrough cards; source-dispatched done,
  dismiss, reopen; Desk deep link; named locked/unsupported status.
- **Out:** `action_items`/Cadence/schema writes, background collection, brief/nudge,
  snooze/delegate, exports/audits, meeting source fabrication.

## Acceptance criteria

- [ ] A request creates no card until explicit acceptance; acceptance is idempotent
  and creates exactly one encrypted commitment/card.
- [ ] Board hydration stores/caches nothing and returns a People card only to the
  authorized local owner; locked People does not break ordinary cards.
- [ ] Done/dismiss/reopen mutate the encrypted authority exactly once. Snooze and
  delegate refuse with `people_commitment_verb_unsupported` and no mutation.
- [ ] No People row/content lands in main DB, `action_items`, `cadence_*`, FTS, sync,
  logs, receipt refs, or exports.

## Test plan

- **Unit:** projection/source dispatch/idempotency/unsupported verbs plus full
  ordinary FollowThrough regression file.
- **Integration:** relationship request→accept→board→done→reopen; DB/Cadence scan.
- **Manual/device:** open People card from Follow-through and round-trip lifecycle.
