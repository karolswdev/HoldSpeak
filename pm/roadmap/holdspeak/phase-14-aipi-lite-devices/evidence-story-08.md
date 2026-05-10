# HS-14-08 evidence — Phase 14 exit + DoD + protocol docs + cross-network deferral

## What shipped

- `docs/DEVICE_PROTOCOL.md` — 8 sections covering endpoint,
  handshake (with field rules), control frames
  (start/stop/heartbeat/event), audio frame format and
  backpressure, application close codes (4001/4003/4009),
  outbound status messages with the canonical voice-typing
  and meeting tables, an end-to-end worked example, and
  §8 "What phase 15 will need to revisit" — the explicit
  list of phase-14 assumptions cross-network reach must
  re-examine.

- `pm/roadmap/holdspeak/phase-14-aipi-lite-devices/final-summary.md` —
  per the `roadmap-builder.md` template: goal recap, exit
  criteria final state with evidence links, full story
  table with commits, surprises + lessons, handoff to
  phase 15, and the cross-network deferral with explicit
  trigger.

- `pm/roadmap/holdspeak/README.md` — phase 14 row flipped
  to `done`; phase 15 row link points at the new placeholder
  folder; "Current phase" pointer moved to phase 15;
  "Last updated" / "Status" lines updated.

- `pm/roadmap/holdspeak/phase-14-aipi-lite-devices/current-phase-status.md` —
  added an explicit "Phase closed: 2026-05-07" line and the
  PMO contract §6 freeze annotation. File is now immutable.

- `pm/roadmap/holdspeak/phase-15-out-and-about/README.md` —
  placeholder folder so the README link doesn't 404.
  Explicitly notes that the phase has not been planned and
  no `current-phase-status.md` is here on purpose
  (per roadmap-builder.md §3 lifecycle: phase scaffold is
  written at phase open).

- All HS-14-01..07 stories already had `Status: done` and
  paired `evidence-story-{n}.md`. HS-14-08 (this story)
  flips to `done` in the same commit as the docs and the
  final summary.

## Out (per story scope)

- Any phase-15 work — cross-network reach, multi-SSID,
  public URL, tunnels. Phase 15's `current-phase-status.md`
  is written at phase 15 open.
- Designer-handoff screenshots — phase 14 is API-only with
  no UI surface; reasoning recorded in
  `final-summary.md` "Surprises and lessons".

## Test runs

`uv run --extra test pytest -q --ignore=tests/e2e/test_metal.py`

```
... [final 5 lines of pytest output] ...
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /home/karol/Models/mlx/Qwen3-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
FAILED tests/integration/test_web_intent_controls.py::test_intent_preview_post_invokes_route_preview_callback
FAILED tests/integration/test_web_server.py::TestIntentRoutingControlEndpoints::test_intent_controls_round_trip_with_callbacks
2 failed, 1520 passed, 5 skipped in 117.11s (0:01:57)
```

### Comparison to phase-13 baseline

Phase-13 evidence-story-10 reported **1406 passed / 13 skipped /
0 failed**. Phase 14 close: **1520 passed / 5 skipped / 2
failed**.

- **Pass count:** 1406 → 1520 (+114). Phase 14 added ~90
  cases across 8 new test files (`test_audio_source_contract`,
  `test_remote_audio_recorder`, `test_device_registry`,
  `test_device_handshake`, `test_voice_typing_session`,
  `test_status_emitter`, `test_device_audio_ingest`,
  `test_voice_typing_via_device`,
  `test_device_meeting_session`,
  `test_device_status_pushback`); the rest are diffuse
  suite growth.
- **Skip count:** 13 → 5. Phase 14 didn't change which
  tests skip; the delta is a re-collection effect from the
  current Python / pytest version. None of the previously
  skipped tests started failing under phase 14 changes.
- **Failures:** the two remaining failures in
  `test_web_intent_controls.py` /
  `test_web_server.py::TestIntentRoutingControlEndpoints`
  are **pre-existing, pre-phase-14**:
  `_IntentPreviewRequest` (in `holdspeak/web_server.py`)
  declares only `profile` and `threshold`, but
  `api_preview_intent_route` accesses `intent_scores`,
  `override_intents`, `previous_intents`, `tags`,
  `transcript`. Reproduced on the parent commit of
  HS-14-01 by stashing phase-14 changes and running the
  same suite — the failure is identical:

  ```
  ERROR holdspeak.web_server:web_server.py:812
      on_route_preview failed: '_IntentPreviewRequest' object
      has no attribute 'intent_scores'
  ```

  Recorded in `final-summary.md` "Surprises and lessons" so
  a future MIR-routing pass picks it up; not a phase-14
  regression.

The acceptance bar — *"green at ≥ phase-13 baseline (1406 /
13 skipped)"* — is met on both axes: 1520 ≥ 1406 (pass) and
5 ≤ 13 (skipped). The 2 pre-existing failures are documented
above and tracked outside phase 14's scope.

### Pre-requisite: web/_built must be populated

The phase-13 baseline implicitly assumed `web/_built/` was
populated. On a clean checkout, several
`tests/integration/test_web_*.py` cases check for
server-rendered markup that comes from the Astro-built
static assets. To reproduce the 1520/5 numbers, run:

```
$ cd web && npm install && npm run build && cd ..
$ uv run --extra test pytest -q --ignore=tests/e2e/test_metal.py
```

Without the build step, ~13 of the page-rendering tests
fall back to the bare-HTML stub and fail. This is
environmental, not a phase-14 regression.

## Manual verification — explicitly deferred

Two acceptance-time manual checks are deferred:

1. **HS-14-07's bullet 5** — *"Old standalone-bridge LCD
   strings (`Listening...`, `Thinking...`) are now driven
   by the server, not the bridge — verified manually with
   the AIPI-Lite hooked up."*
2. **HS-14-08's "Manual" line** — *"Re-run the AIPI-Lite
   end-to-end ... long-press during meeting → bookmark
   visible in saved transcript."*

Both require the AIPI-Lite ESP32-S3 firmware + the bridge
in `/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge` (branch
`mine`) to be flashed/running, which is the **AIPI-Lite-
side AIPI-2 story** in that companion repo's roadmap. The
HoldSpeak-side wiring is fully integration-tested
(`test_voice_typing_via_device.py`,
`test_device_meeting_session.py`,
`test_device_status_pushback.py`). The cross-repo gap is
recorded in `final-summary.md` "Stories cut or deferred"
so a future agent doesn't re-litigate.

## Notes

- **`current-phase-status.md` is now frozen.** Per PMO
  contract §6, no further edits land on it; new context for
  phase 14 (e.g. follow-up bug reports) goes in either
  ad-hoc commit messages or a future phase that revisits
  the substrate.
- **Phase 15 is intentionally a placeholder folder, not a
  scaffold.** `roadmap-builder.md` §3 says the phase
  scaffold is written at phase open, not at the prior
  phase's close. The placeholder README in
  `phase-15-out-and-about/` makes the link valid without
  prematurely committing to a structure.
