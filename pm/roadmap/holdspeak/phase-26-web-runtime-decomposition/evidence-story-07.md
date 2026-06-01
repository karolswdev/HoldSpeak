# Evidence — HS-26-07 — Decomposition Closeout

- **Shipped:** 2026-06-01
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The phase closeout: final size + regression evidence, a phase summary, and the
roadmap flip (Phase 26 → done). No code refactor (story §Out).

## Verification artifacts (captured at closeout)

```
$ git show f77c2d9:holdspeak/web_server.py | wc -l
5658
$ wc -l holdspeak/web_server.py
523
# -> web_server.py reduced 90.8%; a thin assembler (no inline route handlers;
#    only middleware + lifespan + StaticFiles mount + device-WS reg + include_router).

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1879 passed, 13 skipped

$ # route inventory (app.routes) — current vs pre-phase origin/main (f77c2d9):
diff baseline current  ->  identical, 122 HTTP routes, zero path/method changes

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py
All checks passed!
```

`holdspeak/web/` package layout (route counts): `core.py` 2, `meetings.py` 25,
`dictation.py` 26, `activity.py` 38, `pages.py` 7, `system.py` 6, `projects.py` 13
+ `context.py` (WebContext) + `runtime_support.py` (shared helpers).

## Files touched

- `pm/.../final-summary.md` — **new**; the phase summary + exit-criteria recheck.
- `pm/.../current-phase-status.md` — frozen (status → done, all rows done).
- `pm/roadmap/holdspeak/README.md` — phase index 26 → `done`; current-phase
  pointer advanced.
- `pm/.../story-07-decomposition-closeout.md` — status → done.

## Acceptance criteria — re-checked

- [x] Before/after `web_server.py` line count recorded (5658 → 523); thin assembler.
- [x] Route-inventory diff shows zero path/method changes across the phase (122).
- [x] Full suite output captured and green (1879 passed, 13 skipped).
- [x] `final-summary.md` written; `current-phase-status.md` frozen; project README updated.

## Follow-ups

- None for this phase. Next candidates (from `final-summary.md`): resume paused
  Phase 24 / Phase 16; Phase 15 is auth-unblocked.
