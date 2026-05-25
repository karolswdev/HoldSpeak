# Evidence — AIPI-2-01 — Bridge Skeleton: ESPHome + HoldSpeak Connections

- **Shipped:** 2026-05-07
- **Commit:** `f71947a` (`feat(bridge): AIPI-2-01 skeleton — async forwarder + Pydantic models`)
- **Owner:** karol

## Files touched

- `bridge.py` — rewritten as async forwarder spine (~430 LOC at this story; later split into the `bridge/` package by AIPI-2-08).
- `holdspeak_proto.py` — new. Pydantic models mirroring HoldSpeak's `DeviceHandshake` with `extra="forbid"`: `Hello`, `HelloAck`, `Heartbeat`, `StartFrame`, `StopFrame`, `Status`, `ErrorFrame`, `EventFrame`.
- `tests/test_models.py` — new. 17 cases: round-trip per frame type + negative tests (unknown fields, empty strings, whitespace-only, wrong-type literals).
- `tests/test_reconnect.py` — new. 9 cases covering `_backoff_seconds` schedule + jitter + floor; async cancellation, exception → backoff, attempt-counter reset.
- `pytest.ini` — new.
- `requirements.txt` — added `pydantic`, `structlog`, `websockets`, `pytest`, `pytest-asyncio` (legacy STT/LLM/TTS deps still listed at this story; pruned in AIPI-2-04).

## Verification artifacts

Captured at phase close (2026-05-10) against the AIPI-2-08 package layout:

```
$ .venv/bin/python -m pytest -q
98 passed in 2.80s

$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/python -m bridge --help
usage: __main__.py [-h] [--check | --send-test-audio WAV | --audio-loopback]
AIPI-Lite ↔ HoldSpeak bridge
```

The skeleton's handshake path was implicitly live-verified on 2026-05-08 when AIPI-2-02's UDP fix shipped audio end-to-end through HoldSpeak (handshake must complete before audio flows; transcripts arrived → handshake worked). See `evidence-story-02.md` for the live trace.

## Acceptance criteria — re-checked

- [x] `main()` is an async function running HoldSpeak WS loop + ESPHome `ReconnectLogic` concurrently — `bridge/cli.py:_run` + `bridge/holdspeak.py:HoldSpeakLeg.session`.
- [x] Pydantic models with `extra="forbid"` mirroring `DeviceHandshake` — verified by `tests/test_models.py` (17 cases) and the cross-repo drift test `tests/test_protocol_sync.py` added in AIPI-2-08.
- [x] `reconnect_with_backoff` helper unit-tested — `tests/test_reconnect.py` (9 cases). Schedule is 1s, 2s, 4s, 8s, 16s, 30s with ±25% jitter, floor at the cap.
- [x] `python -m bridge --check` exits 0 on success / 1 on either-endpoint failure with decoded close codes — verified 2026-05-07 against live `aipi.local` (device leg succeeds; HoldSpeak leg surfaces `ConnectionRefusedError` and exits 1 cleanly when no server is running).
- [x] Connect log triplet (`connect.device.ok`, `connect.holdspeak.handshake.ok`, `loop.ready`) — implicitly verified on 2026-05-08 since audio streamed end-to-end (no handshake = no audio).
- [~] HoldSpeak-kill reconnect loop on real server: covered by `tests/test_holdspeak_leg.py` integration tests against a fake `websockets.serve` server (clean + abrupt-close paths) added in AIPI-2-08. **Live `pkill -f holdspeak` smoke deferred — hardware not co-located 2026-05-10.**
- [~] Device unplug/replug → `ReconnectLogic` recovers — `aioesphomeapi.ReconnectLogic` is the upstream class doing this; bridge wires the callbacks. **Live unplug smoke deferred.**
- [~] WS idle behaviour (60s no-frames, no reconnect) — guarded by `ping_interval=15, ping_timeout=30` (RFC-6455 ping/pong, not application-layer frame timing). **Live 60s observation deferred.**
- [~] SIGTERM/SIGINT clean shutdown — implemented via `KeyboardInterrupt`/cancellation in `bridge/cli.py`; **live signal-handling smoke deferred.**

## Deviations from plan

- Story-01 originally targeted ≤ 250 LOC for `bridge.py`. Final count was ~430 (still well under the 1500 LOC the spine grew to before AIPI-2-08 split it into a package). Acceptable scope creep — handshake parsing + reconnect helper + Pydantic plumbing were denser than estimated.
- Live-hardware verification of the four `[ ]` reconnect/idle/signal acceptance items was **deferred to phase close** rather than performed at story close. At phase close (2026-05-10) the user is not co-located with hardware; smoke is waived for this evidence pass and tracked as a phase-level follow-up in `final-summary.md`.

## Follow-ups

- None story-internal. Phase-level: live-hardware reconnect/idle/SIGTERM smoke (covered by phase final-summary's "deferred" list).
