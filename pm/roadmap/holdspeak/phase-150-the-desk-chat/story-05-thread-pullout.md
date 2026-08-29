# HS-150-05 - The Thread on the Desk (primitive, verbs, ThreadPullout, streaming renderer)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** in-progress
- **Depends on:** HS-150-04
- **Unblocks:** HS-150-06, HS-150-07
- **Owner:** unassigned

## Problem

Art. I/II: chat is not a screen; a Thread is a desk object that opens
in a pullout like a Note. Nothing on the Desk knows kind `thread`
(settled-design D5).

## Scope

### In (D5)

- `"thread"` in `PrimitiveKind`; the two `satisfies` gates
  (`world.ts`, `pullouts/registry.ts`) and `DeskListView.BAND_LABEL`
  rows; a sprite glyph in the existing family (never an emoji).
- `web/src/desk/threads.ts` (the API client + zustand slice replacing
  `chat.ts`'s role): list/get/create/turn/abort/branch/regenerate/
  keep/patch/delete; bus subscription applying `thread_delta` by
  `seq`, dropping duplicates, refetch-and-reconcile on reconnect.
- `ThreadPullout.tsx`: head (in-place title · egress lamp via
  `inferenceEgress.ts` · status line · token meter); body rows: user,
  assistant (`StreamingMaterial` append-safe over `Material`,
  finalizes to `Material` at done), reasoning folded behind RAW, error
  row in-flow, CRASHED row (`streaming=1` older than 10 s) with Retry,
  `‹ n/m ›` sibling picker, receipt short-id per assistant row.
- Verbs on the registry: `New thread` (desk), `Continue in thread`
  (object; wired into `floorMenu.ts` object menus per the 148
  grammar), `Keep as note`, `Keep as artifact`, `Fork here`, `Stop`.
- Receipt bar (`useWriteReceipt`) for keep/branch/delete.

### Out

The composer (06), search/list bands beyond the label (07).

## Acceptance criteria

- [ ] Type gates compile; `npm run typecheck` (or the web check chain)
      green.
- [ ] A streamed turn renders progressively in a real-Chromium probe
      (jsdom lies about focus/paint — standing law); the finished row
      renders code blocks + mermaid through `Material`.
- [ ] Two clients on the same thread both stream; a reload mid-turn
      shows the partial and continues.
- [ ] CRASHED + Retry, error row, empty state, branched picker all
      render without overlap at 1440 and 393.
- [ ] "Continue in thread" from a Meeting/Note/Person seeds the ref
      chip and opens the pullout.

## Test plan

- **Unit:** vitest `web/src/desk/__tests__/threads.test.ts`
  (delta application, seq dedup, crash rule), `ThreadPullout.test.tsx`.
- **Integration:** real-Chromium probe under
  `tests/e2e/test_hs150_thread_glass.py` (rig pattern: 149's
  `story-04-rig.py`).
- **Manual / device:** shots reviewed by the orchestrator (cross-read).

## Notes / open questions

Owner sees shots before merge (standing law) — story 08 gathers them.
