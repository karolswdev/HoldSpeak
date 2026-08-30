# HS-153-01 - Modes as recipes (kind, seeds, allow-lists, mode tabs)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** done
- **Depends on:** HS-152-06
- **Unblocks:** HS-153-02, HS-153-03, HS-153-06
- **Owner:** unassigned

## Problem

A Thread with hands needs a practice: what it may touch and how it
speaks. warpdrv's "modes" become recipes (settled design D1) — one
binding through `threads.recipe_id`, no parallel `mode_id`, and the
executor's palette becomes the mode's allow-list ∩ the classification
map. Without a mode the palette is `CHAT_PALETTE` (152 addendum).

## Scope

- **In (data layer — LANDED `9cb769a9`, verify, do not rebuild):**
  additive `recipes.kind` (`'' | 'mode'`), `holdspeak/services/thread_modes.py`
  (mode lookup, allow-list ∩ classes, palette for a thread), seeds
  `hs-seed-mode-{desk,chase,draft,plan}` in `holdspeak/seeds/fresh-desk.yaml`
  with the S4 allow-lists, `tests/unit/test_thread_modes.py`.
- **In (this story):** the executor/palette seam — `ThreadService`
  offers `thread_modes.palette_for(thread)` instead of `CHAT_PALETTE`
  when a mode is bound (Draft = no `tools` key at all); the truth table
  still gates effects. `PATCH /api/threads/{id} {recipe_id}` binds a
  mode (applies from the NEXT turn — in-flight passes keep theirs).
  Composer head mode tabs (Desk · Chase · Draft · Plan · custom recipes
  of kind `mode`), colour from `avatar`, keyboard reachable; the bound
  mode's name in the pullout head; `threads.ts` state + `setMode()`.
- **Out:** guardrails per mode (03), slash `/mode` (02).

## Acceptance criteria

- [ ] Through the REAL coordinator (fake engine): a thread bound to `Draft` admits a payload with no `tools`; bound to `Chase`, the admitted palette contains `people.commitment.transition` and not `desk.delete`; a mid-turn switch changes nothing until the next turn.
- [ ] A mode's allow-list naming an unclassified tool is dropped, never offered (fail-closed, logged once).
- [ ] Glass 1440 + 393: mode tabs render, the active tab is marked, switching writes `recipe_id` (GET shows it), no horizontal overflow.

## Test plan

- **Unit:** `tests/unit/test_thread_modes.py` (extend: palette seam through `ThreadService.start_turn` with the real coordinator, the "next turn" rule).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` leg `modes`.
- **Manual / device:** story 06 walk leg (Desk→Chase on `.43`).

## What shipped

### Files changed

- **`holdspeak/services/thread_modes.py`** -- added `palette_for(db, thread_id) -> frozenset[str] | None`: returns None when no mode is bound (caller falls back to CHAT_PALETTE), the mode's `tools & TOOL_NAMES` when bound. Unclassified names in a custom mode's allow-list are dropped and logged ONCE per (mode id) at WARNING (fail-closed). Added `_warned_modes` set for dedup.
- **`holdspeak/services/thread_service.py`** -- added `ThreadService._palette_for(thread_id)`, the ONE helper both `start_turn` and `_run_streaming_turn` call. Draft (empty palette) omits the `tools` key entirely so the pass loop runs one pass (no tool schemas). The `_run_streaming_turn` executor now reads `tool_schemas` from the payload (frozen at admission) rather than re-resolving -- enforcing the "next turn" rule. `ThreadService.patch` now accepts `recipe_id` with validation (empty string unbinds; non-mode recipe = 400). `_thread_dict` returns a resolved `mode: {id, name, avatar} | null`.
- **`holdspeak/db/threads.py`** -- `ThreadRepository.patch` accepts `recipe_id`.
- **`holdspeak/web/routes/threads.py`** -- PATCH handler passes `recipe_id`, added ValidationError handler.
- **`web/src/desk/threads.ts`** -- added `ThreadMode` interface, `mode` field on `ThreadWire`, `recipe_id` on `patchThread`, `setMode(threadId, recipeId)` action on the zustand store (optimistic update + PATCH + GET).
- **`web/src/desk/components/ModeTabs.tsx`** -- new component: mode tabs (Desk/Chase/Draft/Plan + custom), coloured dot from avatar, active tab marked (`aria-selected`/`aria-pressed`), arrow-key + Enter reachable, overflow-x container for 393.
- **`web/src/desk/pullouts/ThreadPullout.tsx`** -- ModeTabs above the composer, mode badge in the pullout head.
- **`web/src/desk/pullouts/thread-pullout.css`** -- mode tab and badge styles.
- **`tests/unit/test_thread_modes.py`** -- extended: `TestPaletteFor` (5 tests), `TestRealCoordinatorModePalette` (3 tests: Draft no-tools, Chase palette, mid-turn switch), `TestSeedOnFreshDatabase`.
- **`web/src/desk/__tests__/ModeTabs.test.tsx`** -- 9 vitest tests (renders tabs, active marking, selection, unbind, arrow keys, disabled, role, colored dot).
- **`tests/e2e/test_hs153_practice_glass.py`** -- glass leg `modes` at 1440 and 393 (tabs render, active marking, switching writes recipe_id, GET confirms, mode badge, no horizontal overflow). Structured with shared fixture/helper section for later stories.

### The seam

Both `tool_schemas_for(CHAT_PALETTE)` sites (start_turn L345 and _run_streaming_turn L471) now go through `ThreadService._palette_for(thread_id)` which delegates to `thread_modes.palette_for`. The palette is resolved ONCE at admission time in `start_turn`; the executor in `_run_streaming_turn` reads tool schemas from the payload (frozen at admission), not by re-resolving. A mid-turn PATCH changes nothing until the next turn.

### Real-path defects found and fixed

1. **Default-to-Desk was wrong for unbound threads (HS-153-01 ruling #1).** `allowed_tools_for_thread` defaulted to `_DESK_TOOLS` when no mode was bound. The settled design + 152 addendum says unbound threads use `CHAT_PALETTE` (which is wider than Desk -- it includes `people.*` effects, `follow_through.*`, `zone.*`, etc.). Fixed by making `palette_for` return None for unbound threads; the caller falls back to `CHAT_PALETTE`.
2. **`_run_streaming_turn` re-resolved the palette independently of `start_turn`.** The two `tool_schemas_for(CHAT_PALETTE)` calls were not coupled. If the payload was admitted with one palette and the executor resolved a different one, the model's `tools` and the executor's gate would disagree. Fixed: the executor now reads `payload["tools"]` (frozen at admission) instead of independently calling `tool_schemas_for`.
3. **Draft mode admitted an empty `tools` array, causing the executor to spin up.** When `tools` was `[]` (empty list), the pass loop would create a `ThreadToolExecutor` (because `tool_dispatch_fn` was set) and run up to 10 passes waiting for tool calls that could never come. Fixed: `start_turn` omits the `tools` key entirely for empty palettes; `_run_streaming_turn` checks `"tools" in payload` before creating the executor.

## Notes / open questions

- The seam is `_run_streaming_turn`/`start_turn` where `tool_schemas_for(CHAT_PALETTE)` is called (two sites; both go through one `palette_for`).
- Custom mode = any recipe the owner sets `kind='mode'` on in the recipe editor (one checkbox; no new editor).
