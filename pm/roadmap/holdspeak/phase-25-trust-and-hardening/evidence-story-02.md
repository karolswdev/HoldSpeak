# Evidence — HS-25-02 — Web-Runtime Auth Token + Non-Loopback Bind Guard

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

A token gate for the FastAPI web runtime, **enforced only off-loopback** (user
decision): loopback binds stay open exactly as before; a non-loopback bind
requires a token both to bind and on every request. This is the Phase 15
unblocker — the mechanism is dormant at today's hardcoded `127.0.0.1` default and
activates the moment a non-loopback host is introduced.

## Files touched

- `holdspeak/web_auth.py` — **new** module mirroring the device-PSK pattern:
  `generate_web_token`, `verify_web_token` (`hmac.compare_digest`, fails closed),
  `is_loopback_host`, `ensure_web_token` (lazy gen + persist),
  `nonloopback_bind_blocked`, `extract_request_token` (header / Bearer / `?token=`).
- `holdspeak/config.py` — `MeetingConfig.web_auth_token: str = ""`.
- `holdspeak/web_server.py` — `auth_token` ctor param; `_web_auth_gate` HTTP
  middleware (off-loopback only; exempts `/health`, `/api/devices/audio`, and
  `/_built` static); bind guard + exposure warning in `start()`; imported
  `Request`.
- `holdspeak/web_runtime.py` — passes `auth_token=ensure_web_token(config)`.
- `holdspeak/commands/doctor.py` — `_check_web_auth` ("Web runtime auth") + import.
- `tests/unit/test_web_auth.py` — **new**, 7 cases (token gen/verify, loopback
  detection, bind-blocked, token extraction, lazy ensure+persist).
- `tests/integration/test_web_auth_gate.py` — **new**, 3 cases (loopback open;
  off-loopback 401/200 via header/Bearer/query + static open; bind refused).
- `tests/unit/test_web_runtime.py` — `_config` double gained `web_auth_token`.

## Verification artifacts

```
$ uv run pytest -q tests/unit/test_web_auth.py tests/integration/test_web_auth_gate.py
10 passed

$ uv run pytest -q tests/integration/test_web_auth_gate.py tests/unit/test_web_auth.py \
    tests/unit/test_doctor_command.py
41 passed

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
9 failed, 1854 passed, 13 skipped
  (+10 tests vs the HS-25-01 baseline of 1844; the 9 failures are the SAME
   pre-existing failures documented in evidence-story-01.md — stale _built
   bundle + missing Safari fixture — unrelated to this change.)

$ uv run ruff check holdspeak/web_auth.py holdspeak/commands/doctor.py \
    holdspeak/web_server.py tests/integration/test_web_auth_gate.py
All checks passed!
  (web_runtime.py still carries the pre-existing unused CYCLE_ORDER import;
   left untouched per rule #5 — not part of this story.)
```

## Acceptance criteria — re-checked

- [x] Off-loopback data/mutation routes → 401 without a valid token; `/health`,
      device-audio WS, and `/_built` static stay open — `test_web_auth_gate.py`.
- [x] `hmac.compare_digest`; no token logged.
- [x] Default localhost launch unchanged (loopback open; token auto-generated +
      persisted for when it is needed).
- [x] Non-loopback bind without token refused with actionable error; with token,
      an exposure warning is logged.
- [x] `doctor` reports the auth + bind posture.

## Deviations from plan

Per the user's decision, auth is enforced **only off-loopback** rather than
"always on, auto-applied." This removed the need to inject a token into the
bundled localhost client (loopback is open), simplifying the change.

## Follow-ups

- `/ws` WebSocket token gating off-loopback (HTTP middleware doesn't cover WS).
- Browser token injection for off-loopback browser sessions (pairs with HS-25-08).
- Both are noted in the story; neither is reachable while `host` is loopback-only.
