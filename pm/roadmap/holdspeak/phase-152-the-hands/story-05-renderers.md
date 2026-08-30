# HS-152-05 - The renderers and the status line

- **Project:** holdspeak
- **Phase:** 152
- **Status:** done
- **Depends on:** HS-152-04
- **Unblocks:** HS-152-06
- **Owner:** unassigned

## Problem

A tool result that renders as raw JSON is a coder's chat; a manager's
desk renders the meeting chip, the person card, the board lanes
(settled-design D5, counsel S3).

## Scope

### In

- Per-kind renderers reusing existing desk components (meeting, person = display name + readiness only, board, note, decision); unknown → key/value; RAW fold always.
- `thread.set_status` MCP tool (one new tool; docs count arithmetic) → `threads.status_line` → `thread_status_line` frame → the head.
- Error rows per taxonomy code.

### Out

Anything DC-03+.

## Acceptance criteria

- [x] Fixture results of each known kind render their component (vitest); unknown renders the table; RAW present on all.
- [x] `thread.set_status` from a fake engine updates the head live on glass.
- [x] Tool count documented = registry count (arithmetic in evidence).

## Test plan

- **Unit / integration:** vitest renderers; tests/unit/test_mcp_tools.py; doc guard tests
- **Manual / device:** shots reviewed by the orchestrator.

## What shipped (2026-08-30, opus worker + orchestrator review)

- **Result kind, derived once server-side** (`thread_tools.derive_result_kind`):
  meeting / person / board / note (`desk.{get,create,update,list}` on
  notes) / decision / data — carried on the result frame and the part meta.
- **Renderers** (`ThreadPullout.tsx`): one result block per receipted row
  — meeting, person (display name + readiness only), board, note (with
  "+N more"), decision; unknown → key/value table; a collapsed **RAW ▸**
  fold on every row; a TRUNCATED tag when the cap fired; every taxonomy
  code (`tool_execution_failed`, `tool_timeout`, `tool_denied`,
  `pass_cap_reached`, `tool_unknown`) renders its in-flow error row.
  Reuse ruling: the desk's lanes (`DoorBoardLane`, `MeetingsLane`,
  `DecisionsView`) are API-bound (fetch loops, store subscriptions,
  router) and cannot be embedded in a row without a modal or a second
  fetch; the renderers are built from the SAME Surface primitives those
  lanes are built from (`SurfaceRows`/`SurfaceRow`, `Material`,
  `intelBadge`) — one material, no lookalike CSS.
- **`thread.set_status`** — a new MCP family `thread` (`holdspeak/mcp/families/thread.py`,
  effect_proposal, in `CHAT_PALETTE`): writes `threads.status_line`; the
  loop emits `thread_status_line` after dispatch; the head shows the
  persisted line on load and live from the frame; the transient
  "Processing (pass N)…" is replaced by the persisted line before
  `thread_turn_done` (the 04 nit). Tool count: **141 → 142, families
  30 → 31** in README / docs/README / docs/MCP_SIDECAR (doc-drift guard
  green).
- **The lease byte cap, D2, was missing**: `ToolResult.bytes` counted
  and never cut. Now `TOOL_RESULT_BYTE_CAP = 32768` — the JSON text is
  truncated at a UTF-8 boundary, the part meta carries
  `{"truncated": true, "original_bytes": N}`, the model's next-pass tool
  message is the truncated text, the row shows TRUNCATED.
- **Wire ruling:** no payload on the live `thread_tool_result` frame
  (200-char summary only); the client refreshes the thread after
  `thread_turn_done` and hydrates rows from the persisted tool parts —
  one source of truth for what was said to the model.
- **Two real defects found by glass**: tool-role messages were rendered
  as assistant rows (pushing the tool row off-screen; the JSON text shown
  twice) — filtered, results live on the tool row only; and `desk.list`
  fell through to the table (missing from the note kind). The 04
  boolean-checkbox alignment fixed.
- **Proof:** vitest 47, unit 113 (+ census 42 serial; one one-path census
  test is order-sensitive under `-n 4` and passes alone/serially —
  recorded), glass `test_hs152_renderers_glass.py` 2 legs + the 04 file
  4 legs = 6 on the real hub, both widths; web baseline zero branch-new;
  6 shots in `assets/story-05-shots/` reviewed by the orchestrator.
