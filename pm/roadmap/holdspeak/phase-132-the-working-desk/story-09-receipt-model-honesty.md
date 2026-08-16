# HS-132-09 — The receipt names what loaded

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-132-10, HS-132-14
- **Owner:** unassigned

## Problem

The last surviving instance of the issue-#450 defect class, reproduced live
in the audit: with `intel_provider='cloud'` and a local realtime model, an
Ask on `this_machine` executes the local GGUF while the receipt, the Ask
footer ("RAN ON ... MODEL", `AskPanel.tsx:253-278`), and the hub's advertised
manifest all print the cloud model id. Chain of causes:

- `holdspeak/kernel/prompt_adapter.py:20` reads
  `engine.active_model`/`engine.model`; `MeetingIntel` defines neither
  (`holdspeak/intel/engine.py:115-136`), so the executed-model report is
  always `''`.
- `ask_service.py:105,123,149` then falls back to `_hub_model()`, and
  `sync_service.py:539-542` answers with the cloud id whenever
  `meeting.intel_provider == 'cloud'` — a describer that never consults
  `resolve_meeting_placement`.
- The same fallback poisons Recipe chat (`recipes.py:122`,
  `recipe_service.py:102,129`), the no-retarget refusal (a user naming the
  model the device actually runs is refused with "it runs 'gpt-5-mini'",
  `ask_service.py:105-109`), and the manifest row advertised to paired
  devices (`sync_service.py:721-731`).
- Existing tests stub `_hub_model_name` to a constant
  (`test_web_routes_ask.py:80` + 7 more), which is why the class regressed
  unnoticed.
- Latent sibling: the onDevice blank-`model_file` fallback to the global
  meeting model (`providers.py:820`) — currently unreachable through a ready
  target, same shape as the defect just fixed.

## Scope

### In

- `MeetingIntel` exposes a real `active_model` set at load time (local: model
  path stem; cloud: cloud model id), so the kernel adapter reports the
  executed model.
- Ask and Recipe chat derive `selected_model` from the admitted deployment's
  identity, never from `_hub_model_name`.
- `_hub_model_name` is retired as a placement/model describer: the hub
  manifest and Ask's advertised model route through the configured meeting
  deployment (`resolve_meeting_placement`/`configured_meeting_deployment`).
- The no-retarget refusal compares against the model the destination
  actually loads.
- The onDevice blank-`model_file` fallback refuses by name (as HS-131-13 did
  for the local branch).
- An executable receipt-honesty fence: parametrized test running the real
  body asserting readiness-model == executed-model == receipt-model ==
  advertised-model for `this_machine`, `onDevice`, `openAICompatible`,
  `meshNode`, and hub-default-cloud; the `_hub_model_name` stubs in existing
  tests replaced with honest fixtures.

### Out

- The placement UI (HS-132-10); mesh/paired receipt divergence beyond the
  fence's mesh leg (unknowns become ledger entries if the fence finds them).

## Acceptance criteria

- [ ] The audit's live reproduction now prints the executed model in the
  receipt, the Ask footer payload, and the placement receipt.
- [ ] Recipe run and chat agree on the model name for the same agent.
- [ ] A user naming the genuinely loaded model is accepted; the refusal
  message names the true model otherwise.
- [ ] Paired-device manifest rows name what the desktop would actually load,
  both mismatch directions.
- [ ] The receipt-honesty fence passes and fails on an injected divergence.

## Test plan

- The new parametrized fence (unit).
- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_deployment_identity.py tests/unit/test_ask_no_retarget.py tests/unit/test_meeting_placement_policy.py tests/unit/test_web_routes_ask.py tests/unit/test_web_routes_recipe_chat.py --tb=short`
- Live `.43` proof rides HS-132-14.
