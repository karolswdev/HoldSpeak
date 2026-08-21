# HS-141-06 — Finish Thought means done

- **Status:** done
- **Depends on:** 141-02, 141-03
- **Unblocks:** 141-04, 141-07, 141-09

## Problem

A refinement loop without a crisp stop becomes expensive chat. **Finish
Thought** has one meaning and works without any model. The story filename is
retained for stable historical links; the earlier owner-visible label was
removed during the Thought Workbench amendment.

## Scope

Make **Finish Thought** one expected-revision transition from Working to a normal
completed Note. Keep it in Inbox or the owner-selected drawer, preserve Original
and the durable refinement ledger for a subsequent lawful history UI, remove
Unfinished status, and return a stable local write receipt. Resume refinement
remains an explicit later action.
Unfinished/completed belongs to the refinement aggregate, not ad-hoc Note
fields. Inbox placement is ordinary directory membership using the qualified
`note:` ref. Finish Thought itself is the owner authorization; do not ask Save or
Confirm afterward.

## Acceptance

- [x] One Finish Thought action completes; no READY limbo or second Save decision.
- [x] No-model fresh HOME completes capture → edit → Finish Thought → reopen.
- [x] Ambiguous response retries the same completion; no duplicate Note.
- [x] Stale working revision names the conflict and offers reload/reapply.
- [x] Completed Note stays findable after hub/browser restart.

## Tests

Focused state/receipt/idempotency/conflict tests and cold no-model browser leg.

## Bundling note

HS-141-06 and HS-141-05 ship together in the Phase 141 Workbench bundle because
completion, context repair, and the one-primary reducer share one authoritative
Thought projection. Splitting them would publish incompatible backend and Desk
halves; neither story's status is inflated by the bundle.
