# HS-151-01 - The thread ledger (schema + repository + import)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-151-02, HS-151-04, HS-151-07
- **Owner:** unassigned

## Problem

HoldSpeak has no persisted conversation: `web/src/desk/chat.ts` keeps
threads in `localStorage`, the hub stores only `recipe_chat_results` /
`ask_results` projections. Every later story needs a ledger that owns
threads, a message tree, typed parts, frozen refs and a searchable
index — additive, soft-delete, reconcile-safe (settled-design D1).

## Scope

### In (D1)

- One additive block in `holdspeak/db/schema.py`: `threads`,
  `thread_messages` (with `parent_id` tree, `streaming`, kernel
  provenance columns, `deleted_at`), `thread_message_parts` (kind
  union + `sensitive`), `thread_refs` (frozen leaves),
  `thread_messages_fts` with soft-delete-aware triggers, indexes.
- `holdspeak/db/threads.py` `ThreadRepository` (BaseRepository):
  create_thread / get / list / patch / soft_delete / append_message /
  append_part / extend_part_text / mark_streaming / complete_message /
  abort_message / list_path / siblings / freeze_refs / search /
  add_token_totals.
- Snapshot fixture `tests/fixtures/db_schema_canonical.txt`
  regenerated; reconcile proven idempotent on a fresh DB and on a
  COPY of a real v64 DB.
- `POST /api/threads/import` server half (dedup by `import_hash` ref
  row, counsel S2) — the web half is HS-151-07.

### Out

`thread_tool_policy` (DC-02), any route beyond import, any UI.

## Acceptance criteria

- [ ] Fresh DB and real-DB copy reconcile to the same shape; snapshot
      test green; the snapshot diff is exactly the new block.
- [ ] Message tree: append → branch (sibling) → `list_path` returns the
      newest leaf path; `siblings(message_id)` returns `‹ n/m ›` data.
- [ ] Soft-deleting a message removes its parts from
      `thread_messages_fts` (trigger-proven); `search` never returns
      deleted content.
- [ ] `extend_part_text` is append-only and cheap (one UPDATE).
- [ ] Import is idempotent: same payload twice → same thread ids.

## Test plan

- **Unit:** `tests/unit/test_thread_repository.py` (tree, siblings,
  soft-delete+FTS, refs freeze, token totals, import dedup);
  `tests/unit/test_db.py -k "schema or shape"`.
- **Integration:** reconcile against a COPY of the owner's real DB
  (137 law; orchestrator-run, path outside the repo).
- **Manual / device:** n/a.

## Notes / open questions

Frame/route names live in D3/D4; this story never broadcasts.
