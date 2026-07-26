# Evidence - HS-103-04

- **Story:** HS-103-04 - Endpoint health — honest fallback across Runs-on destinations
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Captured run — 2026-07-23T04:17:45Z

- **Command:** `bash -c uv run pytest -q tests/unit/test_endpoint_health.py tests/unit/test_endpoint_health_wiring.py tests/unit/test_doctor_command.py tests/unit/test_dictation_runtime.py tests/unit/test_intel_*.py tests/unit/test_engine_off_the_loop.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 33d730d41e93f78c28c7555fd4383b5c85366d21

## Design (thresholds named per the story's own request)

`holdspeak/intel/endpoint_health.py` — a small, thread-safe
`EndpointHealth` circuit breaker keyed by endpoint identity (a base
URL, or model name for the default OpenAI endpoint), reimplemented
from scratch (not vendored) per this project's greenfield-craft
posture. Two named constants with documented reasoning:

- `DEFAULT_FAILURE_THRESHOLD = 3` — enough consecutive failures to
  distinguish "this endpoint is down" from "one request hiccuped,"
  without waiting through a long failure run first.
- `DEFAULT_COOLDOWN_SECONDS = 30.0` — long enough a flapping endpoint
  isn't hammered every request, short enough a genuinely recovered
  endpoint isn't refused for minutes.

`check(key)` returns `(ok, refusal_reason)` — callers must not attempt
the network call when `ok` is `False`. After cooldown, one probe call
is let through (half-open) so recovery doesn't need a manual reset.
`record_success`/`record_failure` update state; `snapshot()` is the
read path for the doctor surface. One process-wide `default_health`
singleton — every wired call site shares state per endpoint identity.

## Wiring (the two named call sites)

- `holdspeak/intel/engine.py` — `MeetingIntel._chat_completion_text`'s
  cloud branch (the meeting-intel path): checks the breaker before
  calling `chat.completions.create`, records success (with latency) or
  failure around it. The local (in-process llama.cpp) branch is
  intentionally NOT wired — it's a local file/subprocess load, not a
  network endpoint the breaker's "unreachable address" framing applies
  to; its own `get_local_intel_runtime_status` already names a missing
  model file honestly.
- `holdspeak/plugins/dictation/runtime_openai_compatible.py` —
  `OpenAICompatibleRuntime.classify` (the dictation-runtime's primary
  LLM call): same before/after pattern, keyed `dictation:{base_url}`.
  `rewrite()` (a secondary call) was left unwired — the story asks for
  "at least" the two most user-visible paths, not every call site.

## Doctor surface

`holdspeak/commands/doctor.py` grew `_check_endpoint_health()`, added
to `collect_doctor_checks()` right after the existing meeting-intel
checks: PASS when no circuit is open (naming "no endpoint calls
recorded yet" when the breaker has never been touched, vs. "no
endpoint circuits open" once it has), WARN naming every open circuit
and its consecutive-failure count when one has tripped.

## Test isolation (a real risk caught before it could bite)

`default_health` is deliberately one process-wide singleton so real
call sites share state — but that makes it global mutable state across
the WHOLE pytest session too. Added an autouse `_reset_endpoint_health`
fixture to `tests/conftest.py` (reset before AND after each test) so a
test that deliberately drives an endpoint to failure can't leave an
open circuit for an unrelated LATER test keying into the same identity
(e.g. two tests both using the class's default base URL). Without
this, cross-test pollution would have been a real, if intermittent,
flake risk.

## Live proof (real hub process, real network attempts)

Staged a hub (`uat.stage --recipe seeded-desk`); confirmed
`GET /api/setup/status`'s `endpoint-health` section (which calls
`collect_doctor_checks()` in the SAME process — the only way "doctor"
can observe a live in-memory breaker) starts PASS ("no endpoint calls
recorded yet"). Created a profile pointing `/api/ask` at
`http://127.0.0.1:1/v1` (a real, deliberately-dead local port — chosen
over a black-holed address so failures return in ~1.2-1.5s instead of
the 180s cloud timeout). Three real `/api/ask` calls each took
~1.2-1.5s and failed with a real connection error; the setup-status
endpoint then read:
```
{"id": "endpoint-health", "status": "warn",
 "detail": "circuit open: cloud:http://127.0.0.1:1/v1 (3 consecutive failures)"}
```
A 4th call returned in **18ms** (vs. ~1.2-1.5s for the real attempts)
with the honest refusal `"endpoint 'cloud:http://127.0.0.1:1/v1' has
been unreachable for 3 consecutive calls; retrying in 21s"` — the
fail-fast path proven live, not just in a unit test. Test profiles
deleted after the walk; hub torn down.

## No regression for the common healthy-endpoint case

Full `uv run pytest -q --ignore=tests/e2e/test_metal.py`: the SAME 6
pre-existing, unrelated failures already documented in HS-103-02/03's
evidence (stale generated manifest/ledger) — 4144 passed (10 more than
HS-103-03's run: this story's own new tests), 37 skipped, no new
failures. The full existing intel/dictation/doctor suites pass
unchanged.

```text
........................................................................ [ 24%]
........................................................................ [ 49%]
........................................................................ [ 74%]
........................................................................ [ 99%]
.                                                                        [100%]
289 passed in 2.71s
```
