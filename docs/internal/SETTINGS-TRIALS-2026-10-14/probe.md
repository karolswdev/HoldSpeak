# Probe trace and repair — HOLD SHIP

Status: root settled the repair; implementation and focused checks complete.
Base: a9f07971d. Worktree: wt-settings-trials-20261014.

## Contradictory Answers result

`web/src/features/concierge/api.ts:385` posts `task: true`, optional
`capabilityId`, and optional `confirmOffMachine` to the existing
`/api/concierge/probe`. `holdspeak/web/routes/concierge.py:213` authenticates
the owner and calls `route_probe.task_probe`.

`holdspeak/services/route_probe.py:254` applies a second test after the
kernel outcome: nonblank `result.output`. The existing Ask schema accepts
an empty string (`holdspeak/inference_capabilities.py:871`). Therefore
`outcome: succeeded` plus empty output becomes `ok: false`, state
`UNREACHABLE`, and reason `inference_succeeded`. The face renders those
fields faithfully as BROKEN / INFERENCE SUCCEEDED. This is a backend
contract contradiction, not a reason-token parsing problem.

`InferenceAdoptionService.execute` returns success only after the runner
validates the frozen result schema, stores the attempt result, and the
controller elects its winner (`inference_adoption_service.py:1590`,
`:1661`). A probe must preserve that terminal truth. If a sample needs
nonblank text, that validation must happen before election; a blank
sample must not invent a failure after a successful receipt.

## Wire and capability boundary before repair

The allowlist is exactly `ask.answer`; the reported group is always
`thoughts_notes` (`route_probe.py:33`). The fixed sample uses the existing
Ask adapter, 16 output tokens, no context, and the route obtained from the
assignment resolver. It persists route, admission, attempt and terminal
receipt rows; it does not publish a Note or other domain object.

The current task response contains state, boolean ok, capabilityId,
group, outcome, reasonCode, served engine/model/boundary/host, latencyMs,
routePlanId, executionId, operationId, frozen legs and allModelsFailed.
Off-machine refusal happens before admission, reports REFUSED/false and
`route_probe_off_machine_not_confirmed`, and sends no inference bytes.

Other Runs on jobs currently call `conciergeProbe(detectId, ...)`
(`web/src/features/runson/useRunsOn.ts:559`). Its implementation reads
`/models`, checks a local file, or returns key presence / NOT_SET
(`concierge_service.py:1142`). It does not execute the selected job.

## Settled bounded sample map

| Board job | Existing capability | Existing result adapter | Sample scope |
| --- | --- | --- | --- |
| writing_dictation | speech.rewrite | CanonicalPromptAdapter | Rewrite one fixed sentence. |
| thoughts_notes | ask.answer | _AskAnswerAdapter | Answer one fixed question. |
| meetings | meeting.deferred_analysis | inference_semantic_adapters.adapter_for + fixed JSON | Summarize a fixed short transcript. No Meeting record or queued job. |
| agents_tools | recipe.run | CanonicalPromptAdapter / _RecipeResultAdapter | Run one fixed instruction. No saved recipe, tool turn or effect. |
| background | background.rails_summary | adapter_for, named summary | Summarize a fixed event. No event journal, cadence or memory write. |
| default | Try withheld | none | Global-only selection is absent from the ordinary public resolver. |

`agent.plan` and `agent.code` are registry capabilities but are absent
from `EXECUTING_CAPABILITIES`; using them in this adoption service would
require a wider change (`inference_adoption_service.py:42`).

Default must not be mapped blindly to Ask: resolution precedence is
invocation, subject, capability, group, global
(`inference_assignment_service.py:2204`). `resolve_route_plan` and
`admit` expose no global-only selector. A selected default model can
otherwise be replaced by the Answers group assignment during a trial.
The root withheld this row's Try. No planner, adoption or assignment
service changed.

## Implemented contract

- `route_probe.py:31` closes the sample set over the five existing
  adopted capabilities above. All request material is fixed public
  text; the output limit and reserved budget are both 512 tokens
  (`:69`, `:273`, `:287`). The former 16-token budget might suppress
  visible output from a reasoning model, but no physical cause was
  verified.
- `route_probe.py:92` retains the Ask adapter, canonical text adapters
  for rewrite/recipe, and existing closed semantic adapters for the
  meeting and background summaries. The meeting sample parses JSON
  inside its physical attempt; invalid JSON or schema fails before
  election. It uses a bounded prompt, not the domain Meeting analyzer,
  which has its own larger output budget.
- `route_probe.py:237` compares every preview profile against optional
  `expectedProfileIds`. A hidden capability override or changed
  profile produces `REFUSED`, `ok: false`, and
  `route_probe_assignment_changed` before admission or dispatch. The
  existing off-machine/paid refusal remains at `:245`.
- `route_probe.py:312` reads the terminal receipt outcome. A succeeded
  empty result stays `READY`, `ok: true`, `outcome: succeeded`, with
  empty reasonCode and `emptyOutput: true`. No reason-code string is
  reinterpreted as success. Each response carries `testedTask`,
  `sampleInput`, `sampleOutput`, and `emptyOutput`; summary samples
  return their summary text as sampleOutput.
- `holdspeak/web/routes/concierge.py:228` validates and forwards the
  optional displayed profile list. `web/src/features/concierge/api.ts:389`
  exposes `conciergeTaskProbe(capabilityId?, confirmOffMachine?,
  expectedProfileIds?)`; its response type at `:181` adds the four
  optional sample fields for compatibility with older consumers.

The profile guard is a bounded check of IDs in the preview. It does not
bind same-profile endpoint/deployment revision changes, nor make
preview and admission atomic. The root explicitly kept the existing
frontend displayed job/engine/host check and kernel frozen-route
authority; this change adds no target-revision or host fields.

## Focused regression proof

Only these two existing files ran:

- `tests/unit/test_phase200_readiness.py`: successful empty Ask output
  keeps successful terminal status; all supported sample capabilities
  execute through real coordinator/controller/runner with only the
  provider leaf controlled; incorrect structured output fails before
  winner election; off-machine refusal dispatches nothing; fallback
  remains inside the frozen route; no domain records or assignments
  change.
- `tests/integration/test_concierge_readiness.py`: exact job/capability
  wire, invalid capability, and truthful terminal fields.

Commands go through `.tmp/settings-trials/locked.py`, isolated HOME and
the machine test lock. Provider-leaf control proves protocol behavior;
it does not prove a physical model answered. No owner DB, hub, Keychain,
microphone, LAN, paid endpoint or external send has been used.

| Run | Result | Log |
| --- | --- | --- |
| Existing baseline collect | 22 tests collected in 0.78s | `.tmp/settings-trials/probe-collect-baseline.log` |
| Added regression collect | 39 tests collected in 0.74s | `.tmp/settings-trials/probe-collect-regressions.log` |
| Regressions before product repair | 17 failed, 22 passed in 4.01s | `.tmp/settings-trials/probe-regressions-red.log` |
| First repair run | 2 failed, 37 passed in 4.29s; meeting fixture used a generic claim instead of its exact result-schema claim | `.tmp/settings-trials/probe-regressions-green.log` |
| Final focused run | 39 passed in 3.92s | `.tmp/settings-trials/probe-regressions-green-2.log` |

The successful sample checks read `inference_route_executions` and
observe `(terminal, succeeded)` for each job. They compare rows before
and after in Meetings, Notes, recipes, Workflows, memory facts/pages,
cadence loops and both assignment head/revision tables. The rows do not
change. This is controlled-provider protocol proof. There are no lane
screenshots because the lane changes the backend/API wire; root and the
trial-face lane own production shots.

`git diff --check` on the five product/test files is clean. No staging,
commit, dependency change or worker SHIP was performed.

## Root live seam correction

Root's actual UI capture found loopback trials refused before admission because
preview used the raw private_network word. See root.md for the original failed
observations. Task preview now reads the real deployment endpoint with the
existing deployment_lamp classifier, matching the desk. Five added locality
regressions plus the existing probe/API files pass 44/44 in 5.19 s, isolated HOME:
`.tmp/settings-trials/probe-locality-green.log`. The first new run was RED.
This changes permission classification only; it does not rewrite frozen legs,
route policy, the planner, or external destination rules.
