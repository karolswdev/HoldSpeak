# Evidence - HS-154-03

- **Story:** HS-154-03 - Call mode (threads.call_mode, chip, frame — M9)
- **Status:** done
- **Date:** 2026-08-30

## Proof

### Captured run — 2026-08-30T22:44:30Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/0888c2e6-1181-42ed-82a8-6a85427876d8/scratchpad/scoped.sh tests/unit/test_thread_call_mode.py tests/unit/test_thread_service.py tests/unit/test_realtime_frame_registry.py tests/unit/test_api_surface.py -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8c0d63ce4ba2cf8b7a06d668a949bc3b837b693c

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 48 items

tests/unit/test_thread_call_mode.py ...........                          [ 22%]
tests/unit/test_thread_service.py .....................                  [ 66%]
tests/unit/test_realtime_frame_registry.py ...........                   [ 89%]
tests/unit/test_api_surface.py .....                                     [100%]

============================= 48 passed in 18.64s ==============================
```
