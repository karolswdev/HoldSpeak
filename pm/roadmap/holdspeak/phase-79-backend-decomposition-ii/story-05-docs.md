# HS-79-05 — the docs story

- **Project:** holdspeak
- **Phase:** 79
- **Status:** todo
- **Depends on:** 01–04.
- **Unblocks:** closeout.

## Problem

`docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md` documents the Phase-63 shape;
after this phase it under-describes the backend (three new packages, new
guard budgets). Entry-point docs are unaffected (no behavior changed), but
the internal map must not lie.

## The design

Update the backend structure doc with the three packages, their module lists,
and the guard's budgets; one line in `docs/ARCHITECTURE.md` only if a named
path moved (check; route module names appear there). No user-facing claims
change. Voice guard rules apply to `docs/*.md`.

## Test plan

Doc guards green (voice, drift, mermaid if touched); the api-surface doc
regenerated alongside the manifest in 02/03 (verify no stale module names).
