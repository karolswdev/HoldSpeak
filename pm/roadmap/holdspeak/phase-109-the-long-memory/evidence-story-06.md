# Evidence - HS-109-06

- **Story:** HS-109-06 - The process window — what is running
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T19:07:24Z

- **Command:** `bash -c cd web && npm run test:web 2>&1 | tail -8 && npm run build 2>&1 | tail -4 && npm run typecheck && npm run guard:architecture && npm run tokens:gate`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
    at hasRealTextChildren (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-af90eea2d5bfb90ad/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-af90eea2d5bfb90ad/web/node_modules/axe-core/axe.js:28249:12) undefined

 Test Files  63 passed (63)
      Tests  365 passed (365)
   Start at  13:07:25
   Duration  13.86s (transform 867ms, setup 1.89s, import 4.68s, tests 3.65s, environment 12.55s)

- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 3.19s

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (186 source files; zero framework residue).

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (61 allow-listed exceptions, all in use)
```

### Captured run — 2026-07-29T19:07:54Z

- **Command:** `bash -c HS_WALK_BASE=http://127.0.0.1:8792 HS_WALK_TOKEN=-MWZLwJDUWcF0tcKwE5PFs4mgvytwA_s uv run --with playwright python scripts/hs109_06_process_window_walk.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
PASS  staged pane found — key=pane:%251819
PASS  real steer delivered (process.input@1) — http=200 status=delivered audit=3
PASS  named kernel refusal minted — http=202 outcome=request_field_not_allowed
PASS  journal carries the walk's events — events=22
PASS  [1440] window opened
PASS  [1440] real rows visible
PASS  [1440] refusal visible
shot: uat/_runs/hs-109-06-walk/process-window-1440.png
PASS  [393] window opened
PASS  [393] real rows visible
PASS  [393] refusal visible
shot: uat/_runs/hs-109-06-walk/process-window-393.png

10/10 beats passed
```

## The walk, narrated

The staged world was `uat.stage --recipe seeded-desk-steering` (golden-local:
a seeded desk plus a REAL tmux coder pane spawned through the product's own
factory route). The rig (`scripts/hs109_06_process_window_walk.py`) drove:

1. **A real steered send** through `/api/coders/pane:%1819/steer` — delivered
   (`status=delivered`, audit id 2), i.e. a real `process.input@1` operation
   through admission, approval, claim, and receipt.
2. **A real named kernel refusal** — `/api/kernel/submit` with an off-contract
   body; the kernel refused with `state=refused`,
   `outcome=request_field_not_allowed`, receipt minted.
3. **The window at both densities**, opened through the registry's own doors
   (the Go menu at 1440; the ⌘K tool shelf at 393 — the row is clicked, the
   shelf search finds "Processes / See what the kernel is running").

All ten beats passed (capture above). Screenshots, read before this flip:

- [assets/process-window-1440.png](./assets/process-window-1440.png) — the
  window with honest zero sections (NEEDS YOU · 0 …), the real Process input
  row Ended ("terminal text 34 bytes submit=True", principal `owner-session`,
  target `node:local`), and the refusals wearing their reason by name.
- [assets/process-window-393.png](./assets/process-window-393.png) — same
  truth at phone density; rows truncate with ellipses, no body overflow.

A refused submit of an unregistered operation type renders its name as
"Unknown" — honest: the kernel never resolved a codec for it; the reason
row carries the named refusal.

## Findings (recorded, not absorbed)

- The events HTTP route exposes no `limit` parameter; the effective batch is
  the backend default (100), not the journal cap (500). The store therefore
  pages until an empty page rather than treating a short page as completion.
  No backend change was made (the story's out-of-scope rule); noted for the
  charter.
- The kernel `awaiting_decision` deep-link lands on the existing attention
  shade (`/#attention`). No existing web UI calls
  `/api/kernel/operations/{id}/decide` today; the window links, it does not
  decide — the gap predates this story.

## Suites

Web chain in the first capture: 365/365, build, typecheck, architecture
guard, token gate — all green. No Python file changed in this story
(`git status` shows web/ + this rig + roadmap only); the Python suite rode
HS-109-01's full run on the same day's tree.
