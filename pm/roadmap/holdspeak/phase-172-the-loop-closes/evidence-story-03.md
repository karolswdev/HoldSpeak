# Evidence - HS-172-03

- **Story:** HS-172-03 - The proposal bridge (extracted items as PROPOSALS in NEEDS YOU; Confirm writes through the kernel)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T15:41:13Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.MDyoSS8eNK PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_hs172_loop_wire.py tests/e2e/test_hs172_room_glass.py tests/e2e/test_hs172_meeting_glass.py tests/e2e/test_hs172_arrival_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9c0f7a824701df4be276870aedb5ecfa7247b4b0

```text
....................................                                     [100%]
36 passed in 52.17s
periodic refinement recovery failed
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/holdspeak/services/refinement_coordinator.py", line 514, in _heartbeat_loop
    await asyncio.to_thread(
        self._thoughts.recover_refinements_on_startup
    )
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
                 ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 2747, in uvloop.loop.Loop.run_in_executor
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/concurrent/futures/thread.py", line 171, in submit
    raise RuntimeError('cannot schedule new futures after shutdown')
RuntimeError: cannot schedule new futures after shutdown
periodic refinement recovery failed
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/holdspeak/services/refinement_coordinator.py", line 514, in _heartbeat_loop
    await asyncio.to_thread(
        self._thoughts.recover_refinements_on_startup
    )
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
                 ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 2747, in uvloop.loop.Loop.run_in_executor
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/concurrent/futures/thread.py", line 171, in submit
    raise RuntimeError('cannot schedule new futures after shutdown')
RuntimeError: cannot schedule new futures after shutdown
periodic refinement recovery failed
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/holdspeak/services/refinement_coordinator.py", line 514, in _heartbeat_loop
    await asyncio.to_thread(
        self._thoughts.recover_refinements_on_startup
    )
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
                 ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 2747, in uvloop.loop.Loop.run_in_executor
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/concurrent/futures/thread.py", line 171, in submit
    raise RuntimeError('cannot schedule new futures after shutdown')
RuntimeError: cannot schedule new futures after shutdown
periodic refinement recovery failed
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/holdspeak/services/refinement_coordinator.py", line 514, in _heartbeat_loop
    await asyncio.to_thread(
        self._thoughts.recover_refinements_on_startup
    )
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
                 ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 2747, in uvloop.loop.Loop.run_in_executor
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/concurrent/futures/thread.py", line 171, in submit
    raise RuntimeError('cannot schedule new futures after shutdown')
RuntimeError: cannot schedule new futures after shutdown
```
