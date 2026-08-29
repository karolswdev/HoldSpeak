# HS-150-07 - Search, list and retirement (FTS corpus, list view, Threads rows, chat.ts import + delete)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** in-progress
- **Depends on:** HS-150-01, HS-150-05
- **Unblocks:** HS-150-08
- **Owner:** unassigned

## Problem

A thread nobody can find again is a chat app; a thread the desk
search, the People pullout and `memory.search` all know is desk
memory. And the old localStorage chat must die honestly: imported
once, then deleted (settled-design D7).

## Scope

### In (D7)

- `"thread"` in `MemoryRepository._VALID_KINDS` + `_thread_rows()` BM25
  over `thread_messages_fts` (deleted excluded); the `memory.search`
  MCP tool and the Desk search box federate it (no new UI).
- Desk list view band "Threads" (newest-first, last-turn detail,
  token meter meta).
- People and Meeting pullouts: a "Threads" row listing threads whose
  `thread_refs` name the object (read-time projection; People content
  never leaves the sidecar — the row shows thread titles only).
- Web import: on first Desk load, if `localStorage['hs.desk.chats']`
  exists, `POST /api/threads/import`, then remove the key; dedup by
  the server's import hash (counsel S2).
- Delete `web/src/desk/chat.ts` + `__tests__/chat.test.ts`; re-point
  `window.test.ts`, `DeskApp.test.tsx`, `writeReceiptGuard.test.ts`;
  MCP tool docs count arithmetic if any tool changed (the 149
  attribution scar).

### Out

Vector search (parked, RFC §4.2); thread folders (the Desk's
directories are the container).

## Acceptance criteria

- [ ] `memory.search("jenkins")` returns a thread hit with the
      message snippet and thread id; deleted branches never surface.
- [ ] The Desk search box shows thread rows; opening one opens the
      pullout at that message.
- [ ] A Person/Meeting pullout lists its threads; the People row
      carries no People-store content.
- [ ] Import: a seeded localStorage payload becomes threads once;
      reload does not duplicate; the key is gone.
- [ ] `chat.ts` gone; `npm run test:web` green except the six
      verified-inherited names (baseline file lands in 08).

## Test plan

- **Unit:** `tests/unit/test_memory_search.py` (thread corpus),
  vitest for the import hook and list band.
- **Integration:** MCP `memory.search` through the stdio server test.
- **Manual / device:** n/a.

## Notes / open questions

If the search box's federation already caps kinds, add "thread" to
its filter chips rather than a new control.
