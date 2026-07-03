# Evidence — HS-79-02 — `routes/system.py` becomes the system package

**Status:** done (2026-07-03).

## The move

`holdspeak/web/routes/system.py` (1,299 lines, one `build_system_router` holding five
unrelated families) → `holdspeak/web/routes/system/`:

| Module | Lines | Concern |
|---|---|---|
| health.py | 59 | device + runtime status reads |
| coders.py | 340 | the coder board (`/api/coders/*`) + its session-age helper and constants |
| settings.py | 701 | settings GET + the deep-merged PUT, its validators and regexes |
| voice.py | 202 | wake type, hub transcribe, the preview one-shots, the command test |
| ws.py | 63 | the one `/ws` socket |
| _shared.py | 49 | the state-shape helpers health and coders both consume |
| __init__.py | 26 | `build_system_router` composes the five — public surface unchanged |

Total 1,440 (package plumbing accounts for the delta). `settings.py` at 701 is the
one module over the P63 module budget — it is a single concern (the PUT validation
matrix) and gets its own named budget in HS-79-04 rather than a silent split.

## Verbatim accounting

Programmatic check against `git show HEAD:`: **zero non-import body lines differ**.
The 19 non-verbatim lines are all lazy in-body imports retargeted one package level
deeper (`from ...x` → `from ....x`; the same class as HS-79-01's three). Route paths
and methods byte-identical: the regenerated `docs/api-surface.json` diff is
**module fields only** (the Phase-72 accepted class).

**Patch-target edits in tests: zero** (no test patches `routes.system` attributes).
Tests unmodified.

## Proven

`uv run pytest -q tests/unit` **2407 passed** · `tests/integration` **685 passed**
(the `/ws` socket, settings round-trips, and the coder board are integration-covered)
· manifest regenerated in the same commit.
