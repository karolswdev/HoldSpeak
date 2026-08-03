# HS-114-03 - Per-destination probe

- **Project:** holdspeak
- **Phase:** 114
- **Status:** in-progress
- **Depends on:** —
- **Unblocks:** HS-114-06, HS-114-07
- **Owner:** unassigned

## The thesis (the bar)

Every destination row in the Models table has its own TEST action
and a model discovery dropdown. The global "Probe" that tests the
wrong target is replaced. Article IX: proof over claim — on the
real hub. Article VI: honest by construction — the readiness lamp
tells the truth.

## Ground (from the applicability study)

- Models "Probe" invokes `POST /api/setup/runtime-test` which
  validates the saved dictation pointer, not the row being edited.
  (`web/src/pages/cores/settingsModels.tsx:197-210`,
  `holdspeak/setup_runtime.py:146-241`)
- `discover_endpoint_models()` exists and works. No React consumer.
  (`holdspeak/setup_runtime.py:41-119`)
- `POST /api/setup/discover-models` route exists. No frontend calls it.
  (`holdspeak/web/routes/setup.py:163-197`)
- Destination table uses GadgetTable with armed FORGET? and + DESTINATION.
  (`web/src/pages/cores/settingsModels.tsx:254-322`)
- LampGadget already renders STATE column with ok/warn/fail tones.
  (`web/src/desk/surface/gadgets.css:632-660`)

## Method

1. **New backend route: `POST /api/inference-targets/{id}/probe`.**
   Resolves the profile, calls `discover_endpoint_models(base_url,
   api_key)`, returns `{reachable, latency_ms, models, error}`.
   For `onDevice` kind, checks model file existence.

2. **Per-row TEST action** in the GadgetTable. Same armed-verb
   pattern as FORGET?. Calls the new probe route. Result renders
   as an inline LampGadget update in the STATE column:
   `● READY 42ms` or `● UNREACHABLE connection refused`.

3. **Model discovery CycleGadget.** When a row has `base_url` and
   a successful probe, the MODEL cell becomes a CycleGadget
   populated from the probe's model list. Falls back to
   StringGadget (free text) when no probe has run or endpoint
   unreachable.

4. **Remove the global PROBE button.** Per-row test replaces it.

## Acceptance

- Each destination row has a TEST action that probes THAT endpoint.
- Successful probe shows green lamp with latency.
- Failed probe shows red lamp with error reason.
- Model field shows CycleGadget with discovered models after
  successful probe.
- Model field falls back to free text when no probe results.
- The old global Probe button is removed.
- Existing seed/settings tests passing.

## Test plan

- `uv run pytest -q tests/unit/ -k "profiles or inference_target"`
- `npx vitest run src/desk/__tests__/` (settings-related)
- Manual: TEST a live .43 endpoint, TEST a dead endpoint.
