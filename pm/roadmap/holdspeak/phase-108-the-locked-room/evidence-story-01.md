# Evidence - HS-108-01

- **Story:** HS-108-01 - The warrant room
- **Status:** done
- **Date:** 2026-07-29; adversarial closeout re-audit 2026-07-30

## Captured proof

```text
$ uv run --extra test pytest -q tests/unit/test_privileged_desktop_executor.py tests/unit/test_typer.py tests/unit/test_desktop_type_text_kernel.py
.................                                                        [100%]
17 passed in 0.82s
```

The group includes a real spawned child over the anonymous pipe plus
negative forgery, replay, payload swap, policy-version drift, request-shape,
expiry, and focus-generation cases. The injected raw driver call list stays
empty for every negative case. Driver failure consumes the warrant before a
replay can reach raw input.

The closeout re-audit found and fixed a desynchronization edge: after a pipe
timeout, the still-alive child previously let `_start()` return true on a
later call. The executor now checks its broken state first. The regression
proves the timeout is indeterminate, the endpoint becomes unavailable, and a
second operation is never written to that pipe.
