# HS-155-03 - thread.notification: the child reports; the parent's next pass listens

- **Project:** holdspeak
- **Phase:** 155
- **Status:** backlog
- **Depends on:** HS-155-02
- **Unblocks:** HS-155-04, HS-155-05
- **Owner:** unassigned

## Problem

A backgrounded child must be able to report without interrupting the
owner: child → parent messages are frames + rows the parent's NEXT pass
consumes as tool-role messages (settled design D3; RFC §6.9).

## Scope

- **In:** `thread.notification` — a row on the parent thread
  {from_thread_id, text, created_at, consumed} + a frame (frames module
  + web mirror + registry fence). The child's turn completion (and an
  explicit child "report" path) writes one. The parent's next pass
  prepends unconsumed notifications as `tool` role messages (the 152
  exchange format) and marks them consumed atomically. R5 (recorded):
  last writer wins on concurrent parent/child writes — no locks. The
  pullout renders the notification row in-flow (provenance chip to the
  child, RAW fold, the 152-05 renderer pattern).
- **Out:** cross-desk notifications, digests.

## Acceptance criteria

- [ ] Real coordinator: a child completion writes the row + frame; the parent's next captured payload contains the notification as a tool message; a second pass does not repeat it (consumed).
- [ ] Sensitivity: a child answer built on People reads keeps sensitive=1 into the notification, and the parent's fence withholds it from a cloud route.
- [ ] vitest: the notification row renders with the child provenance chip; the chip jumps to the child.

## Test plan

- **Unit:** `tests/unit/test_thread_notifications.py`.
- **Integration:** glass leg `crew-notify`.
- **Manual / device:** story 05.

## Notes / open questions

- The fence check is the story's heart — a child must not become a People-egress laundering path.
