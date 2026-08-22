# Phase 143 repository census — routing before consolidation

**Captured:** 2026-08-21 from merged `main` after Phase 142 Story 06.
**Purpose:** charter evidence; implementation stories must refresh anchors.

## Existing authorities and proved patterns

| Plane | Current authority / seam | Evidence | Phase 143 consequence |
|---|---|---|---|
| Mutable destination | `ProfileRecord` plus built-in `this_machine`; `InferenceTarget` resolves readiness/placement | `holdspeak/inference_targets.py` | preserve profile identity; remove post-freeze mutable reads |
| Immutable execution | content-addressed `DeploymentRevision` v1/v2 consumed by `InferenceRunner` | `holdspeak/deployment_revisions.py`, `holdspeak/kernel/inference_runner.py` | sole executable revision registry remains |
| Local artifacts/deployments | Phase 142 artifact ledger and mutable `inference_deployments` heads | `holdspeak/services/inference_acquisition_service.py`, `holdspeak/services/inference_setup_service.py` | profiles point to deployment heads; do not duplicate artifact/runtime truth |
| Thoughts pointer | `Config.thoughts.inference_target_id` | `holdspeak/config/integrations.py`, `holdspeak/inference_targets.py` | migrate to `thought.interview`/`thought.synthesis` assignments |
| Dictation pointer | `Config.dictation.runtime.profile_id` plus runtime knobs | `holdspeak/config/model.py`, `holdspeak/intel/providers.py` | split intent/rewrite/punctuation capabilities; keep runtime policy typed |
| Meeting pointer | `Config.meeting.intel_profile_id` plus local/auto/cloud legacy placement | `holdspeak/config/meeting.py`, `holdspeak/intel/providers.py` | migrate meeting capability family, not one blunt pointer |
| Background pointer | `Config.rails_observer.profile_id`; Cadence uses bounded service inference | `holdspeak/config/integrations.py`, `holdspeak/services/cadence_service.py`, `holdspeak/web_server.py` | explicit background capability assignments |
| Workbench/Recipe precedence | Workbench profile → Recipe profile → default; frozen revision rebuilt from one transaction | `holdspeak/deployment_revisions.py:resolve_workbench_deployment_revision` | preserve visible result through sparse subject assignments |
| Meeting ordered fallbacks | `MeetingIntelPlan` freezes ordered deployment revisions per capability; engine fallback disabled | `holdspeak/meeting_session/intel_plan.py`, `intel_child.py` | proved template for canonical route plans/controller |
| Speech capabilities | transcribe/preload/intent/rewrite/punctuate are already stable constants | `holdspeak/speech_session/plan.py` | seed canonical registry; keep speech vs text requirements distinct |
| Meeting capabilities | live analysis, bookmark, title, deferred analysis, plugins, Whisper | `holdspeak/meeting_session/intel_plan.py` | seed canonical registry and adapters |
| Tool authority | future `ToolTurnController`/private lease ruled; owner MCP sidecar forbidden | `proposals/inference-catalog-and-context-policy.md` | required prerequisite for executable tool-aware fallback |
| Admission waist | every physical model call is `inference.invoke@1` through `InferenceRunner` | Phase 131 census and `tests/unit/test_one_path_census.py` | expand census; controller remains above runner |

## Fragmentation visible today

The repository-wide pointer census contains hundreds of `profile_id`,
`inference_target_id`, `intel_profile_id`, deployment revision, and target
references across Config, database objects, services, web types, tests, and
docs. Not all are routing authority; Story 01 must classify each as:

1. mutable assignment pointer;
2. immutable execution evidence;
3. display/projection only;
4. credential/provider identity;
5. unrelated use of the word profile; or
6. dead/legacy path to delete.

Known duplicated owner controls include Models by job, meeting intelligence
placement, Workbench/Recipe model selectors, Agent destinations, and background
assistance. They must converge on one Assignment editor rather than receive new
fallback controls independently.

## Existing fallbacks/retries that require classification

| Mechanism | Current truth | Required treatment |
|---|---|---|
| Meeting local→cloud | frozen as real second revision in `MeetingIntelPlan`; each provider attempt is a child | adapt into canonical plan/controller without regression |
| Deferred meeting retries | new admitted parent/attempt with exponential schedule | remain scheduling retry; do not conflate with same-turn model fallback |
| Dictation lexical fallback | deterministic non-model degradation on classifier failure | preserve as product fallback, but do not misreport as model profile fallback |
| Provider dialect retry | may create a winning attempt beneath current adapters | census and make physical attempt cardinality explicit; no hidden second HTTP call |
| Ask/Thought terminal retry | new owner-visible turn/invocation | distinguish explicit Try again from automatic route fallback |
| Tool result limitation | design-only until Tool Capability Foundation executes | no executable claim before prerequisite story |

## Initial owner-facing capability groups

Default Assignments glass is intentionally stable at five summary rows:

* Default for AI work
* Thoughts & notes
* Writing & dictation
* Meetings
* Agents & tools

Background tasks and every leaf capability exist in the searchable override
disclosure. Issues and explicit overrides rise into default glass. Capability
count may grow without permanent-screen growth.

## Audit commands for Story 01

```bash
rg -n 'profile_id|inference_target_id|intel_profile_id|target_profile|deployment_revision_id' holdspeak web/src tests
rg -n 'CAPABILITY_|capability=' holdspeak -g '*.py'
rg -n 'run_prompt|InferenceRunner|inference.invoke|build_intel|provider' holdspeak -g '*.py'
rg -n 'fallback|retry|attempt_ordinal|indeterminate|cancel' holdspeak -g '*.py'
```

The story converts these reads into checked-in generated fixtures and AST/static
guards. This hand census is orientation, not the close gate.
