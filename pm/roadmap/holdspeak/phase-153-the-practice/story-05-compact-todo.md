# HS-153-05 - Compaction and todo (chat.compact cut row, door.add_item)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** backlog
- **Depends on:** HS-153-02
- **Unblocks:** HS-153-06
- **Owner:** unassigned

## Problem

Long threads need a cut that keeps the fence (counsel M7), and a todo
said in a thread must land on the Door — never a parallel list
(settled design D5).

## Scope

- **In (LANDED `67723588`, verify):** `action_items.meeting_id`
  nullable + `source_type`/`source_ref`; `DoorService.add_item`; MCP
  `door.add_item` (effect_proposal, `source_type='thread'`); the
  `chat.compact` capability + `thread_practice` entrance.
- **In (this story):** `/compact` → `POST /api/threads/{id}/compact` →
  `chat.compact` admission over the leaf path (through the real
  coordinator, `payload_redactor` applied) → a `system` row with
  `stats_json = {"compaction": true, "cut_at": <message_id>}` and a text
  part = the summary; the assembler includes only that row and what
  follows; the summary part is `sensitive=1` when ANY summarized part
  was, and its text joins `_sensitive_texts`. Pullout: the cut marker row
  ("compacted · N messages", RAW fold shows the summary). `/todo <text>`
  → `door.add_item` through the SAME executor path as a model call
  (receipt row); the Door card provenance case `thread` ("from a thread"
  chip opening the pullout at the message).
- **Out:** automatic compaction on context pressure (R1 adaptive cap).

## Acceptance criteria

- [ ] After `/compact`, the next turn's admitted payload contains the summary + later messages only (captured via the real coordinator); a thread with a sensitive part before the cut yields a sensitive summary that the cloud payload withholds.
- [ ] `/todo buy the cake` → an `action_items` row with `source_type='thread'`, `source_ref=<message_id>`, `meeting_id NULL`; the Door board shows it with the `thread` provenance chip; the receipt row appears in the thread.
- [ ] Glass 1440 + 393: cut marker + the Door card with the thread chip; the chip opens the pullout.

## Test plan

- **Unit:** `tests/unit/test_thread_compaction.py` (assembler cut + sensitivity inheritance + real coordinator capture); `tests/unit/test_hs153_practice_capabilities.py` (extend for the route).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` legs `compact`, `todo`.
- **Manual / device:** story 06.

## Notes / open questions

- The cut is a row, not a deletion: fork/regenerate before the cut still works; the assembler's "after the last compaction cut" rule is the only reader.
