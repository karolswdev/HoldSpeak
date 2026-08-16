# HS-114-06 - The honest target

- **Project:** holdspeak
- **Phase:** 114
- **Status:** backlog
- **Depends on:** HS-114-03
- **Unblocks:** HS-114-07
- **Owner:** unassigned

## The thesis (the bar)

`this_machine` tells the truth about local model availability.
RunsOnPicker has an honest empty state. "Hub default" resolves
its actual engine in the label. The persona-chat context budget
bug is fixed. Article VI: honest by construction — unavailable
models must be named where encountered.

## Ground (from the applicability study)

- `InferenceTarget.from_profile()` reports `this_machine` as
  "ready" even when the configured local model file doesn't exist.
  (`holdspeak/inference_targets.py:305-351`)
- RunsOnPicker has no empty-state treatment when no targets exist.
  It falls back to `this_machine` visually but doesn't surface a
  "no destinations" message or a setup affordance.
  (`web/src/desk/components/RunsOnPicker.tsx:14-64`)
- The three feature CycleGadgets show "HUB DEFAULT" with no
  explanation of which engine/model it resolves to.
  (`web/src/pages/cores/settingsModels.tsx:338-342`)
- PersonaChat context budget keys off `persona.profileId` after
  the user changes Runs On to a different target.
  (`web/src/desk/components/PersonaChat.tsx:107-111,350-355`)

## Method

1. **Honest `this_machine` readiness.** In
   `inference_targets.py`, when resolving `this_machine` or
   `onDevice` profiles, check that the configured model file
   actually exists on disk. If not: readiness = `unavailable`,
   reason = `model file not found: ~/Models/gguf/...`. This is
   a backend-only change; the existing LampGadget in Models
   already handles unavailable state.

2. **RunsOnPicker empty state.** When `targets` is empty or all
   targets are unavailable, show a disabled CycleGadget with
   `NO DESTINATIONS` and a dashed affordance below:
   `+ ADD IN SETTINGS > MODELS` that navigates to
   `configure-runs-on`. Same dashed-add pattern as GadgetTable's
   `+ DESTINATION`.

3. **Hub default resolution.** The "HUB DEFAULT" option in the
   three feature CycleGadgets gains a detail suffix resolving the
   actual engine and model: `HUB DEFAULT · LLAMA.CPP · QWEN3.5-4B`
   or `HUB DEFAULT · NO MODEL`. Backend: new
   `GET /api/setup/hub-default-summary` returning
   `{engine, model, available}`.

4. **Persona-chat budget fix.** In `PersonaChat.tsx`, key the
   context budget off the selected `inferenceTargetId`, not the
   persisted `persona.profileId`. When the user changes Runs On,
   the budget updates to reflect the new target's context limit.

## Acceptance

- `this_machine` shows `● UNAVAILABLE · MODEL FILE NOT FOUND`
  when the local model path doesn't exist.
- `this_machine` shows `● READY` only when the model file exists.
- RunsOnPicker shows `NO DESTINATIONS` and `+ ADD IN SETTINGS >
  MODELS` when no targets exist.
- Hub default CycleGadgets show the resolved engine and model name.
- Persona chat context budget updates when Runs On changes.

## Test plan

- `uv run pytest -q tests/unit/ -k inference_target`
- `npx vitest run src/desk/__tests__/`
- Manual: remove local model file, verify this_machine goes red.
