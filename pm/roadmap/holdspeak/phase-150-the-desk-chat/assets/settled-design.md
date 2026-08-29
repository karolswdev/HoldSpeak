# Phase 150 settled design — The Thread (DC-01)

The design-beat spec. Ruled by the orchestrator 2026-08-29 from the
seam census ([audit-census.md](./audit-census.md)) and one Opus
counsel ruling ([counsel-design-beat.md](./counsel-design-beat.md),
RATIFY-WITH-CONCERNS, M1–M4 all accepted). The parent RFC is
`docs/internal/PLAN_PHASE_DESK_CHAT.md`. Builders implement, they do
not redesign; the owner may overrule any row.

## The one sentence

A Thread is a desk object: the owner opens one from anything on the
desk (or from nothing), talks to it by voice or keyboard with `@`-refs
frozen at the moment of asking, watches the answer stream token by
token over the one bus, sees one egress badge and one receipt per
turn, can stop it, branch it, keep it — and finds it again by search,
because every byte of it lives in the hub's SQLite, never in a browser.

## Defaults taken for the RFC's §14 questions

Thread = Desk window (pullout), not a wing. Effect tools default yolo
(DC-02's concern; DC-01 has no tools). Kokoro server-side, later
(DC-04). No external MCP server. `recipe.chat` is RETIRED into
`chat.turn` (counsel S1).

## D1 — the ledger (story 01)

Additive block in `holdspeak/db/schema.py` before the closing `"""`
(pattern: `scheduled_recordings` L3355–3396 for CHECKs + indexes,
`notes_memory_fts` L1190–1198 for triggers):

```
threads(id PK, title, recipe_id, profile_override, directory_id,
        parent_thread_id, status_line, token_in INT DEFAULT 0,
        token_out INT DEFAULT 0, created_at, updated_at, last_turn_at,
        deleted_at)
thread_messages(id PK, thread_id FK, parent_id NULL FK self,
        role CHECK ('user','assistant','system','tool'),
        streaming INT NOT NULL DEFAULT 0,             -- counsel M2
        operation_id, receipt_id, invocation_id,
        egress_scope, egress_host, model_id, route_plan_id,
        stats_json, error_json,
        created_at, updated_at, completed_at, aborted_at, deleted_at)
thread_message_parts(id PK, message_id FK, ordinal INT,
        kind CHECK ('text','reasoning','tool_call','attachment','annotation'),
        text, tool_call_id, attachment_ref, meta_json,
        sensitive INT NOT NULL DEFAULT 0)             -- counsel M1
thread_refs(id PK, thread_id FK, message_id FK, ref_kind, ref_id,
        version, frozen_json, created_at)
thread_messages_fts (FTS5, content=thread_message_parts, text)
  + INSERT/UPDATE/DELETE triggers that EXCLUDE parts whose parent
    message has deleted_at NOT NULL, and a trigger on
    thread_messages.deleted_at that removes the parts (counsel M3)
indexes: threads(updated_at), thread_messages(thread_id, created_at),
         thread_message_parts(message_id, ordinal), thread_refs(thread_id)
```

`thread_tool_policy` is DC-02's (not created here). Soft-delete only
(never DROP/DELETE rows — the reconcile law). `threads.token_in/out`
are SUM projections updated at `turn_done` from
`stats_json.prompt_tokens/completion_tokens` (counsel S3, R4).
Branch = sibling row sharing `parent_id`; the *current leaf* of a
thread is the newest non-deleted message on the chosen path; the UI
shows one level of siblings (`‹ n/m ›`) and collapses deeper history
(counsel S4).

`ThreadRepository` (`holdspeak/db/threads.py`) copies
`ScheduledRecordingRepository`'s CRUD shape: create_thread, get,
list (newest-first, excludes deleted), soft_delete, append_message,
append_part / extend_part_text, mark_streaming, complete_message,
abort_message, list_path (messages on the leaf path), siblings,
freeze_refs, search. Snapshot fixture
`tests/fixtures/db_schema_canonical.txt` regenerated in the same
commit; proven on a COPY of the owner's real DB (the 137 law).

## D2 — the capability (story 02)

`_capability("chat.turn", …)` in `holdspeak/inference_capabilities.py`
(`builtin_capability_definitions`, L1039–1082, next to `ask.answer`).
`recipe.chat` is retired: removed from the sealed registry, its
assignment chain migrated to `chat.turn` by one additive backfill
(`_apply_data_backfills`, family `chat-route-assignments`: copy the
`recipe.chat` chain if present else the `ask.answer` chain). The three
generated ledgers and their fail-closed tests are updated in the same
commit (`EXPECTED_CALL_SITES` / `PRODUCT_RUNNER_ENTRANCES` rows for the
new service). Assignments UI shows `chat.turn` as "Desk chat" with no
new UI code (it lists the registry).

## D3 — the streaming seam (story 03)

- `InferenceRunner.invoke_stream(request, adapter, *, on_delta, …)`
  beside `invoke` (`holdspeak/kernel/inference_runner.py:147`): same
  admission/plan/receipt envelope, but the adapter dispatch yields
  deltas; the runner calls `on_delta(Delta)` for each and writes the
  receipt at `done` (outcome succeeded), `indeterminate` on cancel or
  stream error after the first delta, and applies fallback ONLY
  before the first delta (the RFC's rule; counsel ratified).
- Provider side: reuse `MeetingIntel._chat_completion_stream`
  (`holdspeak/intel/engine.py:337`) — extend it to yield typed
  `Delta(kind ∈ text|reasoning|usage|done|error, text, meta)` reading
  `delta.content`, `delta.reasoning_content` and the final `usage`.
  Non-streaming callers untouched.
- Frames (append to `RUNTIME_FRAME_TYPES` + `web/src/runtime/frames.ts`,
  drift test `tests/unit/test_realtime_frame_registry.py`):
  `thread_turn_started {thread_id, message_id, user_message_id,
  model_id, egress}`, `thread_delta {thread_id, message_id, ordinal,
  kind, text, seq}`, `thread_turn_done {thread_id, message_id,
  receipt_id, outcome, egress, stats}`. Frame names use the
  registry's underscore dialect.
- Sequencing contract (counsel M4): the assistant message row is
  COMMITTED with `streaming=1` and `thread_turn_started` is broadcast
  BEFORE the provider stream opens. Deltas carry a monotonically
  increasing `seq` per message.
- Persistence cadence (counsel M2): buffered text is flushed to the
  part every 2 s OR every 500 chars, whichever first, and at
  done/abort; `updated_at` moves on each flush. A client that loads a
  message with `streaming=1` and `updated_at` older than 10 s renders
  it as CRASHED with a Retry verb.
- Abort: `POST /api/threads/{id}/abort` → runner cancel (the existing
  `threading.Event`) → `aborted_at`, `streaming=0`, receipt
  `indeterminate`, `thread_turn_done{outcome:'aborted'}` within 250 ms.

## D4 — the turn route + assembler (story 04)

`holdspeak/web/routes/threads.py` + `holdspeak/services/thread_service.py`:

- `POST /api/threads` `{title?, recipe_id?, seed_refs[]}` → thread.
- `GET /api/threads`, `GET /api/threads/{id}` (path + siblings map +
  refs), `DELETE` (soft), `PATCH` (title, profile_override).
- `POST /api/threads/{id}/turns` `{text, refs[], parent_id?}` →
  persists user message (+ `annotation` parts later) → freezes refs via
  `hydrate_refs_detailed` (`holdspeak/grounding.py:76`; unknown ids
  refuse by name, nothing is sent) → admits `chat.turn` through
  `inference_adoption_service.admit/execute` exactly as Ask does
  (`ask_service.py:232–269`; principal owner-session) → commits the
  assistant row → broadcasts started → streams. Returns `{thread_id,
  user_message_id, assistant_message_id}` immediately; the bus carries
  the rest (no SSE endpoint — one bus).
- `POST /api/threads/{id}/abort`, `POST /api/threads/{id}/branch`
  `{message_id, text}` (edit-and-resend = new sibling user message +
  turn), `POST /api/threads/{id}/regenerate` `{message_id}` (sibling
  assistant turn), `POST /api/threads/{id}/keep` `{message_id, as:
  'artifact'|'note'}` (reuses Ask's keep path; provenance =
  `thread:<id>/<message_id>`).
- **Assembler law (counsel M1):** context = recipe/system prompt +
  messages on the leaf path after the last compaction cut + frozen ref
  leaves. Any part with `sensitive=1` (set by DC-02 for `people.*`
  results; set in DC-01 by the refs freezer when a ref resolves to a
  People-sourced leaf) is REDACTED to `[people content withheld]` when
  the frozen route plan's egress scope is `cloud`. Pinned by a test
  that seeds a sensitive part, switches `profile_override` to a cloud
  profile, and asserts the provider payload contains zero of it.
- The census gate: the new service gets its literal rows in the
  Phase 143 fixtures (D2).
- `/api/recipes/{id}/chat` becomes a 303-style alias: it creates (or
  reuses the newest open) thread with that `recipe_id` and runs the
  turn; the old body shape is not preserved (the product is unreleased).

## D5 — the Thread on the Desk (story 05)

- `PrimitiveKind` gains `"thread"` (`web/src/lib/primitives.ts:28`);
  the two `satisfies` gates (`world.ts:30`, `pullouts/registry.ts:24`)
  and `DeskListView` `BAND_LABEL` get their rows. Glyph: a speech-
  ribbon in the existing sprite family (the icon reforge kit); never
  an emoji.
- `ThreadPullout.tsx` (pattern `DirectoryPullout.tsx`): head = title
  (in-place editable) · model/egress lamp (`inferenceEgress.ts`) ·
  status line · token meter; body = turn rows (user row; assistant row
  = `StreamingMaterial` — an append-safe wrapper over
  `surface/Material.tsx` that re-renders the current part's text
  cheaply and, at `turn_done`, hands the finished text to the ordinary
  `Material` so code blocks/mermaid finalize); reasoning parts folded
  behind RAW; error row in-flow (never overlapping); CRASHED row with
  Retry; `‹ n/m ›` sibling picker on branched rows; foot = the
  composer (story 06).
- Subscribes via `useRuntimeBus().subscribe` to the three frames;
  ignores frames for other threads; applies deltas by `seq`, drops
  duplicates, and on reconnect refetches the thread and reconciles.
- Verbs on the registry (`verbRegistry.ts:165` VERBS): `New thread`
  (desk scope), `Continue in thread` (object scope — seeds the object
  as a ref; wired into `floorMenu.ts` object menus with the 148
  grammar), `Keep as note`, `Keep as artifact`, `Fork here`, `Stop`.
- Receipt bar via `useWriteReceipt` for keep/branch/delete; every
  assistant row shows the receipt id short-form.

## D6 — the composer (story 06)

Foot of the pullout: textarea with the standing `MicButton`
(click-to-toggle; the result lands in the textarea, voice ARMS, never
sends — Art. IV), `@` opens `InletAutocomplete` extended from zones to
primitives (meeting/note/artifact/decision/person by title; selecting
adds a ref chip above the field — the chip IS the attachment; file
upload is out of DC-01), `/` opens the verb palette filtered to thread
verbs, Enter sends, Shift+Enter newline, Esc stops a running turn;
Send flips to Stop while `streaming`. No modal anywhere.

## D7 — search, list, retirement (story 07)

`"thread"` joins `_VALID_KINDS` in `holdspeak/db/memory.py` with a
`_thread_rows()` BM25 query over `thread_messages_fts` (title + text,
excluding deleted); `memory.search` MCP tool and the Desk search box
federate it with no new UI. Desk list view band "Threads". People and
Meeting pullouts gain a "Threads" row listing threads whose
`thread_refs` name them. `POST /api/threads/import` takes the old
`localStorage['hs.desk.chats']` payload; dedup key =
sha256(recipe_id + first user text + created ts) stored in
`threads.status_line`? NO — in a `thread_refs` row of kind
`import_hash` (counsel S2); a second import returns existing ids. The
web client imports once on first Desk load, then deletes the key;
`web/src/desk/chat.ts` and its tests are deleted; `window.test.ts`,
`DeskApp.test.tsx`, `writeReceiptGuard.test.ts` re-pointed at the
thread module.

## D8 — the walk and the close (story 08)

Three legs, counsel-required, before the phase flips:
1. **Real metal `.43`** — a two-turn streamed thread over llama.cpp
   Q6; deltas observed on the bus; first delta ≤ 1.5 s; receipts +
   egress on both turns; rows match the glass. Control = the old
   non-streaming Ask blob for the same prompt.
2. **People boundary under profile switch** — seeded sensitive part,
   `profile_override` → cloud, provider payload asserted clean
   (unit + the walk's recorded payload).
3. **Glass exhibit** 1440 + 393, cross-read: populated + branched,
   empty, error (provider unreachable), crashed-with-Retry; occlusion
   tell on every frame.
Plus: a "thread" leg appended to `scripts/door_walk_hs144.py`
("Continue in thread" from a Door item → streamed reply → receipt);
docs story law (README + USER_GUIDE entry points, MCP tool count
arithmetic); `web-inherited-baseline.txt` (handover §3.D debt rider);
close counsel; AGPL check (no file cites a warpdrv path; the clone is
gone).

## Recorded notes (counsel R1–R5, orchestrator-ruled: not fixing)

R1 10-pass cap (DC-02). R2 frozen refs go stale by design. R3 FTS
recall is mediocre — honest first step. R4 `stats_json` untyped; the
meter reads only the two token fields. R5 no new admission path,
even in DC-02.
