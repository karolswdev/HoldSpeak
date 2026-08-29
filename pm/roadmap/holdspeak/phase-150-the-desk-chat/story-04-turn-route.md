# HS-150-04 - The turn route (threads API, refs frozen, abort, branch, keep)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** HS-150-01, HS-150-02, HS-150-03
- **Unblocks:** HS-150-05, HS-150-07
- **Owner:** unassigned

## Problem

The ledger, the capability and the stream exist but nothing ties a
user's words to a receipted, streamed assistant message. This story
is the one place a turn is assembled and admitted — and the one place
the People boundary is enforced at message level (counsel M1,
settled-design D4).

## Scope

### In (D4)

- `holdspeak/services/thread_service.py` + `holdspeak/web/routes/threads.py`:
  `POST /api/threads`, `GET /api/threads`, `GET /api/threads/{id}`,
  `PATCH`, `DELETE` (soft), `POST /{id}/turns`, `/abort`, `/branch`,
  `/regenerate`, `/keep`.
- Turn pipeline: persist user message → freeze refs via
  `hydrate_refs_detailed` (unknown ids refuse by name, nothing sent) →
  admit `chat.turn` exactly as Ask admits (`ask_service.py:232–269`)
  → COMMIT assistant row `streaming=1` → broadcast
  `thread_turn_started` → `invoke_stream` with the cadence helper →
  `thread_delta`s → complete/abort → `thread_turn_done`; token totals
  added to the thread.
- **Assembler law:** leaf-path messages after the last cut + system
  prompt + frozen leaves; parts with `sensitive=1` redacted to
  `[people content withheld]` when the frozen plan's egress scope is
  `cloud`; the refs freezer marks People-sourced leaves sensitive.
- `/api/recipes/{id}/chat` → alias creating/reusing a thread bound to
  the recipe; `recipe_chat_results` writers removed.
- Census fixture rows for the new call site (Phase 143 gates).

### Out

Any UI (05/06); tools (DC-02); attachments (out of DC-01).

## Acceptance criteria

- [ ] A turn returns ids immediately; the bus carries started →
      deltas → done; DB rows equal the streamed text after done.
- [ ] Abort within 250 ms leaves `aborted_at`, `streaming=0`, receipt
      `indeterminate`, `thread_turn_done{outcome:'aborted'}`.
- [ ] Branch and regenerate create siblings; `GET` returns the new leaf
      path + siblings map.
- [ ] **M1 pin:** seeded sensitive part + `profile_override` → cloud
      profile ⇒ the provider payload contains none of the sensitive
      text; on a local profile it is present verbatim.
- [ ] Unknown ref id → 4xx naming the id; no model call, no rows past
      the user message.
- [ ] Keep mints an artifact/note with `thread:<id>/<message_id>`
      provenance through the existing keep path.

## Test plan

- **Unit:** `tests/unit/test_thread_service.py` (fake streaming
  adapter; all AC above), `tests/unit/test_phase143_*census.py`.
- **Integration:** `tests/integration/test_threads_api.py` via the
  FastAPI test client with the WebSocket bus captured.
- **Manual / device:** HS-150-08.

## Notes / open questions

No SSE endpoint: the bus is the one live channel (Art. I, one bus).
