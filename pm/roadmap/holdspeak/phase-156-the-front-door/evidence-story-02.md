# Evidence - HS-156-02

- **Story:** HS-156-02 - One confirmation applies everything
- **Status:** done
- **Date:** 2026-08-30

## Proof

### Captured run — 2026-08-31T02:43:17Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/0888c2e6-1181-42ed-82a8-6a85427876d8/scratchpad/run_tests.sh tests/unit/test_front_door_apply.py tests/unit/test_front_door_recommendation.py tests/unit/test_api_surface.py tests/unit/test_no_positional_inserts.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** db6c8e4c5b783f056010e8eb1a92f9d917b04a0e

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 73 items

tests/unit/test_front_door_apply.py ...........................          [ 36%]
tests/unit/test_front_door_recommendation.py ........................... [ 73%]
...........                                                              [ 89%]
tests/unit/test_api_surface.py .....                                     [ 95%]
tests/unit/test_no_positional_inserts.py ...                             [100%]

============================== 73 passed in 4.45s ==============================
```
