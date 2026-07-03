# HS-79-02 — `routes/system.py` becomes the system package

- **Project:** holdspeak
- **Phase:** 79
- **Status:** done — see [`evidence-story-02.md`](./evidence-story-02.md). Five routers +
  a shared-helpers module under one unchanged `build_system_router`; zero non-import body
  drift; manifest regenerated (module fields only); tests unmodified, 2407 + 685 green.
- **Depends on:** nothing (parallel to 01).
- **Unblocks:** HS-79-04.

## Problem

`holdspeak/web/routes/system.py` is 1,299 lines: one `build_system_router`
holding five unrelated families — runtime/device health, the coder board
(`/api/coders/*`), settings GET/PUT, the voice lane (wake type, transcribe,
preview type/discard, commands test), and the `/ws` socket with its
broadcast plumbing.

## The design

`holdspeak/web/routes/system/` with `health.py`, `coders.py`, `settings.py`,
`voice.py`, `ws.py` — each a `build_*_router(ctx)`, composed by
`build_system_router` in `__init__.py` so `routes/__init__.py` and every
caller stay untouched. Bodies verbatim. The API-surface manifest regenerates
in the same commit (module fields only — any path/method diff is a bug).

## Test plan

Full unit + integration suites green; `test_api_surface.py` green against the
regenerated manifest; patch-target edits listed in evidence.
