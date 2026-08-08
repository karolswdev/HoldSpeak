# Evidence - HS-128-10

- **Story:** HS-128-10 - The walk
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T02:53:06Z

- **Command:** `bash -c cd web && npx vitest run src/desk/pullouts/IntelligenceWalk.test.tsx --maxWorkers=2 && npm run typecheck && cd .. && uv run pytest -q tests/unit/test_follow_through_service.py tests/unit/test_monday_brief_service.py tests/unit/test_decision_receipt_service.py tests/unit/test_receipts_routes.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cd182c72d68f0885981d833a0523230f01953ccf

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  5 passed (5)
   Start at  20:53:07
   Duration  934ms (transform 185ms, setup 38ms, import 272ms, tests 383ms, environment 170ms)


> holdspeak-web@0.0.1 typecheck
> tsc --noEmit

============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 58 items

tests/unit/test_follow_through_service.py .....................          [ 36%]
tests/unit/test_monday_brief_service.py ..................               [ 67%]
tests/unit/test_decision_receipt_service.py ..................           [ 98%]
tests/unit/test_receipts_routes.py .                                     [100%]

============================== 58 passed in 8.09s ==============================
```
