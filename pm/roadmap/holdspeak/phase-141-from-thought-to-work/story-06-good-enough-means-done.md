# HS-141-06 — Good enough means done

- **Status:** backlog
- **Depends on:** 141-02, 141-03
- **Unblocks:** 141-04, 141-07, 141-09

## Problem

A refinement loop without a crisp stop becomes expensive chat. “Good enough”
must have one meaning and work without any model.

## Scope

Make **Good enough** one expected-revision transition from Working to a normal
completed Note. Keep it in Inbox or the owner-selected drawer, preserve Original
and refinement history access, remove Unfinished status, and return a stable
local write receipt. Resume refinement remains an explicit later action.
Unfinished/completed belongs to the refinement aggregate, not ad-hoc Note
fields. Inbox placement is ordinary directory membership using the qualified
`note:` ref. Good enough itself is the owner authorization; do not ask Save or
Confirm afterward.

## Acceptance

- [ ] One Good-enough action completes; no READY limbo or second Save decision.
- [ ] No-model fresh HOME completes capture → edit → Good enough → reopen.
- [ ] Ambiguous response retries the same completion; no duplicate Note.
- [ ] Stale working revision names the conflict and offers reload/reapply.
- [ ] Completed Note stays findable after hub/browser restart.

## Tests

Focused state/receipt/idempotency/conflict tests and cold no-model browser leg.
