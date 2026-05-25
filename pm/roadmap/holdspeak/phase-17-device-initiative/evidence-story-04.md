# Evidence — HS-17-04 — Phase Closeout

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-17-04](./story-04-dod.md)

## What changed

- Consolidated `docs/DEVICE_PROTOCOL.md` with:
  - `device_health` schema, example, validation rules, and API exposure.
  - `query:last_segment` schema, fallback behavior, unknown-query behavior, and status-frame response semantics.
  - current meeting status-frame behavior, including 1s Recording ticks and display-only transcript noise filtering.
- Wrote [final-summary.md](./final-summary.md).
- Froze [current-phase-status.md](./current-phase-status.md) with a phase-closed notice.
- Updated the parent roadmap phase index to mark Phase 17 done.
- Wrote `.tmp/CONTRACT.md` with all required PMO boxes checked.

## Verification

```bash
.venv/bin/pytest -q
```

Result: `1774 passed, 21 skipped in 124.09s`.

```bash
npm run build
```

Result from `web/`: passed; 7 static pages built.

```bash
git diff --check
```

Result: passed.

## Acceptance Criteria

- [x] `docs/DEVICE_PROTOCOL.md` lists both new frame types.
- [x] `evidence-story-{01,02,03}.md` files exist.
- [x] `final-summary.md` follows roadmap-builder §2.5.
- [x] Parent README phase index row 17 is `done`.
- [x] `current-phase-status.md` has a phase-closed notice and pointer to final summary.
- [x] AIPI-Lite unblock signal names AIPI-4-05 and AIPI-4-06.
- [x] Full test suite green.
- [x] PMO contract certification written.

## Deviations

- Browser screenshot evidence was not captured because Playwright is not installed in this virtualenv. The current web stack instead verifies the served dashboard shell, bundled JS helper markers, `/api/devices/health`, and WebSocket/runtime update paths.
