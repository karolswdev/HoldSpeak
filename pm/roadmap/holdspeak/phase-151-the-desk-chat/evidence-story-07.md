# Evidence - HS-151-07

- **Story:** HS-151-07 - Search, list and retirement (FTS corpus, list view, Threads rows, chat.ts import + delete)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T00:00:47Z

- **Command:** `uv run pytest -q tests/unit/test_memory_index.py tests/unit/test_memory_search_threads.py tests/unit/test_mcp_phase133_coder_memory.py tests/unit/test_thread_repository.py tests/integration/test_threads_api.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1350df8cfbfb24cf9cafe827d85bc7f377de06a0

```text
........................................................                 [100%]
56 passed in 13.15s
```

## Orchestrator triage (2026-08-30)

Read: 56 passed — memory index (4), the new thread corpus (8: found by
a word in an assistant part, soft-deleted text never returned,
interleaves with notes without breaking ranking, MCP kinds=["thread"]),
the MCP memory family (11), the thread repository (25 incl. the new
`ref_id` list filter) and the threads API (8). Web half proven in the
desk suite (baseline check 5/5 inherited, zero new reds): the import
hook (6: once, key removed on success, kept on failure), Threads rows
on Person/Meeting pullouts (titles only — People content never leaves
the sidecar), search-result open with `focusMessageId`. Retirement:
`chat.ts`, `PersonaChat.tsx`, `chat.test.ts` deleted; Recipe "Chat
with" → "Continue in thread"; the 143 assignments glass label follows
`chat.turn`. Recorded gap (not fixing): `rebuild_memory_index()` does
not rebuild the trigger-maintained thread FTS — a rebuild path is a
DC-02 rider if it ever drifts.
