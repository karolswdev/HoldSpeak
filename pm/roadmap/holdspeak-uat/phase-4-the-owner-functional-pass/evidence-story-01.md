# Evidence - HSU-4-01

- **Story:** HSU-4-01 - Executable functional protocol + exact bootstrap
- **Status:** done
- **Date:** 2026-07-09

> **Preservation note:** This evidence proves the original HSU-4-01 delivery as
> it existed on the captured index tree. It predates protocol v2 and therefore
> does not prove target-qualified React/Swift acceptance. In particular, phone-
> width browser evidence is React layout evidence, never Swift evidence. Current
> acceptance follows `uat/CHARTER.md` and requires independent target-specific
> legs plus matching native device attestation.

## Proof

### Captured run — 2026-07-10T02:55:01Z

- **Command:** `uv run pytest -q tests/uat/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text
........................................................................ [ 58%]
...................................................                      [100%]
123 passed in 423.64s (0:07:03)
```

### Captured run — 2026-07-10T03:04:05Z

- **Command:** `npm --prefix uat/web test`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text

> holdspeak-uat-site@0.1.0 test
> vitest run


 RUN  v2.1.9 /Users/karol/dev/tools/HoldSpeak/uat/web

 ✓ src/api.test.js (1 test) 2ms
 ✓ src/store.test.js (5 tests) 2ms

 Test Files  2 passed (2)
      Tests  6 passed (6)
   Start at  21:04:05
   Duration  398ms (transform 23ms, setup 54ms, collect 31ms, tests 3ms, environment 370ms, prepare 59ms)
```

### Captured run — 2026-07-10T03:04:06Z

- **Command:** `npm --prefix uat/web run build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text

> holdspeak-uat-site@0.1.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 48 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:  0.30 kB
dist/assets/index-DsPxhs1N.css    7.49 kB │ gzip:  2.27 kB
dist/assets/index-qullRamX.js   171.85 kB │ gzip: 55.00 kB
✓ built in 322ms
```

### Captured run — 2026-07-10T03:04:21Z

- **Command:** `uv run python scripts/uat_site_walk.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/scripts/uat_site_walk.py", line 114, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/scripts/uat_site_walk.py", line 74, in main
    page.wait_for_selector("text=Choose a pack", timeout=10000)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py", line 8213, in wait_for_selector
    self._sync(
    ~~~~~~~~~~^
        self._impl_obj.wait_for_selector(
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            selector=selector, timeout=timeout, state=state, strict=strict
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    )
    ^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_sync_base.py", line 115, in _sync
    return task.result()
           ~~~~~~~~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_page.py", line 419, in wait_for_selector
    return await self._main_frame.wait_for_selector(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py", line 369, in wait_for_selector
    await self._channel.send(
        "waitForSelector", self._timeout, locals_to_params(locals())
    )
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py", line 69, in send
    return await self._connection.wrap_api_call(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py", line 559, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.TimeoutError: Page.wait_for_selector: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("text=Choose a pack") to be visible
```

### Captured run — 2026-07-10T03:05:03Z

- **Command:** `uv run python scripts/uat_site_walk.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text
captured home
captured walkthrough
captured verdict cast
captured phone home
screenshots in /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak-uat/phase-1-the-mechanics/assets
```

### Captured run — 2026-07-10T03:05:29Z

- **Command:** `uv run python scripts/uat_site_walk.py --out pm/roadmap/holdspeak-uat/phase-4-the-owner-functional-pass/assets`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text
captured home
captured walkthrough
captured verdict cast
captured phone home
screenshots in pm/roadmap/holdspeak-uat/phase-4-the-owner-functional-pass/assets
```

### Captured run — 2026-07-10T03:07:46Z

- **Command:** `npm --prefix uat/web run build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text

> holdspeak-uat-site@0.1.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 48 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:  0.30 kB
dist/assets/index-std1mUk9.css    7.60 kB │ gzip:  2.30 kB
dist/assets/index-RXpHFSYT.js   171.85 kB │ gzip: 55.00 kB
✓ built in 331ms
```

### Captured run — 2026-07-10T03:07:47Z

- **Command:** `uv run python scripts/uat_site_walk.py --out pm/roadmap/holdspeak-uat/phase-4-the-owner-functional-pass/assets`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6eebb991b39969c1e07113c967f17a4b34981c88

```text
captured home
captured walkthrough
captured verdict cast
captured phone home
screenshots in pm/roadmap/holdspeak-uat/phase-4-the-owner-functional-pass/assets
```
