# HS-26-03 — Extract Dictation / Agent-Hook Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** done
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** Claude (agent)

## Problem

The dictation-pipeline config, blocks, project-context, agent-hook, and
intent-control routes (`/api/dictation/*`, `/api/intents/*`) are a self-contained
cluster ready to move behind the HS-26-01 seam.

## Scope

### In

- Move `/api/dictation/*` (config, blocks, agent-context, project KB) and
  `/api/intents/*` (profile/override/control) routes into `routes/dictation.py`.
- Read from the shared context; no behavior change.

### Out

- Other domains (HS-26-02, HS-26-04, HS-26-05).
- Callback removal beyond these routes (HS-26-06).

## Acceptance criteria

- [x] Listed routes are served from the new module; none remain inline.
- [x] Existing dictation/intent web tests pass unchanged.
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (dictation or intent)"`.
- Integration: dictation config round-trip via the runtime.
- Manual: n/a.

## Notes / open questions

- Confirm whether intent-control routes belong with dictation or meetings; keep
  with dictation unless tests suggest otherwise.
- **Resolved:** intent-control routes shipped **with dictation** (one cohesive
  pipeline cluster); tests pass there unchanged.
- **Shipped as one module** (`routes/dictation.py`, 1608 lines, 26 routes + all
  private helpers). The cluster's helpers (`_resolve_project_context`,
  block-config IO, dry-run, the `project_doc_suggestions` per-app dict) are used
  by no other domain and moved with it. `web_server.py` 4691 → 3133 (−1558).
- **WebContext param is `web_ctx`, not `ctx`** — project-kb handlers use a local
  `ctx` project dict; the rename avoids the shadow. `_GLOBAL_BLOCKS_PATH` is read
  through the `web_server` module for monkeypatch parity. See `evidence-story-03.md`.
