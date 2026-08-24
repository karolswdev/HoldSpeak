# Phase F cleanup plan — HS-143-08

**Research basis:** branch `feat/hs143-08-meeting-adoption` at `0e889874`,
2026-08-24. This is an executable cleanup plan, not an authorization to
remove compatibility readers indiscriminately. Phase F closes *new-work
routing authority* while preserving readable history and the deliberately
unadopted speech/device paths.

## Binding obligation register (17)

| # | Binding obligation | Source |
|---|---|---|
| 1 | A post-marker Meeting may not create a v1 `MeetingIntelPlan`, resolve a placement, or execute the v1 live child path. | Phase B design, lines 40–46 |
| 2 | Meeting/speech migration may read saved legacy selectors once as a startup source; execution after the marker must not depend on them. | Phase B design, lines 71–82 and 152–169 |
| 3 | Retain historical DTO/record readers and never rewrite stored historical bytes merely to perform the cutover. | Phase C design, lines 54–59 |
| 4 | A normal deferred claim freezes the route, parent, and bundle together; recovery reconstructs those stored IDs and never consults `Config`, host discovery, or a resolver. | Phase C design, lines 26–32 |
| 5 | Unknown/deferred handoff reservations never activate, claim, retry, or sweep. A replacement is a linked *fresh* admission under ordinary policy, not a replay of the old physical attempt. | Phase C design, lines 41–43 and 95 |
| 6 | `speech.transcribe@1` is the sole new-work transcription authority. `SpeechSessionPlan` is a v1/history/compatibility reader, not a post-cutover selector for transcription or preload. | Phase D design, lines 4–8 and 54–77 |
| 7 | Owner/wake speech changes as one complete pipeline only when **both** `speech-recognition-route-assignments` and `thoughts-writing-route-assignments` are present. If either is absent, retain the complete legacy session path; never mix a routed bundle with a plain provider child. | Phase D design, lines 306–316; Phase-D counsel, lines 130–165 |
| 8 | Paired-device capture remains outside this adoption: SERVICE `device-capture`, `paired-device:<id>` basis, legacy transcription path, and an explicit non-stranding proof remain. No incidental device route policy. | Phase D design, lines 233–254 |
| 9 | Transcription/preload are local-only. Mesh/private/remote speech transport must refuse at admission without dispatch; remote transport remains future work. | Phase D design, lines 265–281 |
| 10 | Egress must come from frozen route evidence and show the widest boundary. Routed/unknown work may not be silently labelled `local`. | Phase D design, Amendment 6 at lines 233–254; Phase-E counsel, lines 50–62 |
| 11 | Lexical punctuation remains lexical. Provider-backed `speech.punctuate` is future/non-assignable work. | Phase D design, lines 405–438 and Amendment 6 |
| 12 | Phase F—not E—removes residual direct `resolve_placement`, RuntimeProfile, and request-override authority and closes the routing-authority census. | Phase E design, lines 177–191 |
| 13 | Decision/delivery blank request target uses the OWNER assignment; a nonblank `inference_target_id` is refused as `inference_request_target_override_retired`. Persisted request/receipt bytes remain readable. | Phase E design, lines 320–339 |
| 14 | Rails execution stays assignment/bundle/controller based, preserves one durable widest-boundary badge, and reports known route failure honestly. | Phase-E counsel, lines 95–134 |
| 15 | No new Rails/Cadence/decision/delivery SERVICE policy is created by cleanup. Rails remains sealed SERVICE; Cadence, decision, and delivery remain OWNER request-time work. | Phase E design and counsel |
| 16 | Existing supported histories remain readable, service principals remain closed, and every migrated call site leaves the legacy-pointer census. | Story 08 acceptance, lines 254–270 |
| 17 | The deferred lexical-punctuation stance remains future/non-assignable at story closeout. | `HANDOVER-STORY-08.md`, lines 217–224 |

## Authority-door inventory

The totals count distinct authority/compatibility doors, rather than every
lexical reference. **20 doors: 8 delete, 9 keep/fence, 3 defer to their named
owner.** `Keep` means keep only as a reader, compatibility path, or refusal;
it is not permission for fresh route selection.

### Delete or reduce to a non-authoritative reader (8)

| Door | Current seam | Verdict and concrete change | Why |
|---|---|---|---|
| D1. Meeting placement/freezer | `holdspeak/meeting_session/intel_plan.py:163–322` | Delete `_placement_legs` fresh resolution and `freeze_meeting_intel_plan` as a production admission entrance. Preserve/relocate only the DTO decoding needed to read persisted v1 plan bytes. | It calls `resolve_meeting_placement` and `resolve_placement` from mutable Meeting config. |
| D2. v1 Meeting live executor | `holdspeak/meeting_session/intel_routed_children.py:184–208` | Remove the historical-v1 `run_admitted_capability` execution fallback. Histories may be displayed, but an old plan cannot resume/replay. | Phase B said the branch was temporary through Phase F. |
| D3. Meeting direct runner helper | `holdspeak/meeting_session/intel_child.py:193` and legacy helpers | Delete the direct `InferenceRunner.invoke`/`run_admitted_capability` Meeting execution path after D2/D4 are gone. Move `discard_staged_children`, if still needed by `intel_admission.py:408`, to a neutral owner rather than retaining the runner module. | This is the remaining F-owned direct runner entrance in the product census. |
| D4. Deferred v1 admission object | `holdspeak/meeting_session/deferred_admission.py:125–206,381–400` | Delete `DeferredIntelJob.admit` and v1 child execution/export surface; retain only any independent constants still used by the bound binder (notably `JOB_DEADLINE_SECONDS` at `services/meeting_deferred_queue_binding.py:128`, preferably relocated). | It freezes v1 Meeting configuration and runs the old child path. |
| D5. Pre-C claimed/running executor | `holdspeak/intel_queue.py:604–683,976–1014`; `holdspeak/db/intel.py:912–924` | Delete the `get_legacy_claimed_intel_job` recovery branch, its mutable `Config.load()`/`effective_intel_cloud` readiness logic, and `_admit_deferred_job`. Add a transactional compatibility-cutover routine: an unbound pre-C `claimed`/`running` row becomes permanently inert/reserved historical evidence with a reason/event; it is never executed, claimed, retried, or swept. If recovery is offered, mint a linked fresh normal queue job under current policy only, following the existing unknown-handoff pattern. | The old row may already have physically egressed. Replaying it guesses authority and violates C's unknown-handoff rule. |
| D6. Migrated Meeting settings selector/projection | `holdspeak/services/settings_service.py:59–106,109–116,579–590` | After `meeting-route-assignments`, stop calling `resolve_meeting_placement`/`configured_meeting_deployment` for the settings response and hide/refuse writes to the legacy Meeting routing selectors. Before the marker retain them only as migration source fields. | A settings read must not keep recalculating current v1 placement after cutover. |
| D7. Migrated Rails profile pseudo-pointer | `holdspeak/web_server.py:1119–1157`; `holdspeak/rails_observer.py:291–317`; `holdspeak/services/settings_service.py:799–811` | After `rails-observer-route-assignments`, remove per-tick `Config.load().rails_observer.profile_id`, the profile/config-hash argument to the runtime summarizer, and settings read/write exposure of the pointer. Keep the config value only as startup migration evidence for unmarked installs. | Rails already routes through its frozen bundle; a mutable profile value must not survive as execution-shaped provenance. |
| D8. F-owned obsolete census rows | `tests/unit/test_phase143_routing_authority_census.py:30–47,61–157,266–287,352–364`; `assets/generated-routing-authority-census.md` | Replace F's `legacy-delete` Meeting/planner/queue assertions with a zero-door regression census after D1–D7. Remove only rows whose production seam is actually gone; retain rows owned by 143-07/143-10/143-11. | The census is a guard against authority returning, not a list to erase cosmetically. |

### Keep, but fence to the stated limited role (9)

| Door | Current seam | Required fence/proof |
|---|---|---|
| K1. Historical Meeting plan data | `holdspeak/meeting_session/intel_plan.py:84–141` and any persistence/projection reader | Keep a non-executing v1 decoder/summary so old records render. It must not import a resolver or offer replay. |
| K2. Bound deferred executor | `holdspeak/meeting_session/deferred_bound.py:63–130` | Keep. It reconstructs `job_id` + stored parent/bundle/SHA without Config, planner, host, or legacy plan entrance—the lawful post-F queue executor. |
| K3. Startup migration source reads | `holdspeak/services/inference_adoption_service.py:1722–2056,2180–2464` | Keep only until each family marker exists; read once, write assignment/profile evidence in one transaction, and never turn the read into runtime selection. |
| K4. `SpeechSessionPlan` / resolver for incomplete migration | `holdspeak/speech_session/plan.py:148–257,441–644` | Keep for a partial-marker owner/wake parent and paired-device capture. When both coupled markers exist for non-device work, it may be a validation/history shape only—never choose transcription/preload/provider work. |
| K5. Complete legacy speech session branch | `holdspeak/speech_session/session.py:585–628,734–802` | Keep while either coupled marker is absent and for `DEVICE_SERVICE_IDENTITY`; make the marker predicate and no-mixed-child rule explicit in tests. |
| K6. Legacy speech child runner | `holdspeak/speech_session/child.py:181` | Keep only behind K4/K5. It cannot be removed until a separately chartered paired-device adoption replaces its legacy transcription authority. |
| K7. Entry validation and routed egress accessor | `holdspeak/speech_session/session.py:949–1148`; `holdspeak/speech_session/provider.py:151–180`; CLI `commands/dictation.py:142–162`; web `_helpers.py:676–690` | Keep validation/close ownership, but make `ProviderAdmission` derive egress from `routed_routes` whenever they exist (including text-entry sessions without a transcription member). Fall back to plan egress only in lawful legacy cases. Feed both CLI and web from that same frozen-evidence accessor. |
| K8. Request-target override reader/refusal | `holdspeak/services/decision_lifecycle_service.py:84–101`; `holdspeak/web/routes/delivery_prs.py:252–259` | Keep the boundary read solely to refuse nonblank overrides with `inference_request_target_override_retired`, a distinct refusal receipt, zero bundle/child/provider call. Blank remains routed through OWNER assignment. Stored request/receipt bytes remain readable. |
| K9. Lexical punctuation and speech refusal seams | `holdspeak/speech_session/plan.py:405–438`; `holdspeak/speech_session/provider.py:456–491` | Keep punctuation lexical and retain explicit refusal behavior. Do not assign/freeze/dispatch `speech.punctuate`; retain local-only transcription and no-dispatch mesh/private refusal. |

### Defer; do not make Phase F their owner (3)

| Door family | Current examples | Owner/rationale |
|---|---|---|
| X1. Ask/refinement direct placement | `holdspeak/services/ask_service.py:307–308`; `holdspeak/services/refinement_application_service.py:63–64` | 143-07. Preserve its census entries and do not sweep its adoption surface under Meeting cleanup. |
| X2. Workbench/recipe/cadence/sequence placement and runner entrances | `holdspeak/services/recipe_service.py:130–174`; `schedule_delegation.py:9,18`; `sequence_workflow_service.py:31–33`; `workbench_runner.py:30–41`; `workbench_service.py:167–171,378–414` | 143-10. These are separately owned RuntimeProfile/resolver migrations. |
| X3. Mesh local runner and other canon entrances | `holdspeak/kernel/mesh_local_runner.py:232` plus remaining non-F entries in `test_phase143_inference_capability_census.py:171–199` | Kernel/canon ownership. Do not falsely claim a global direct-runner zero while lawful non-F entrances remain. |

## Ordered implementation slices

### Slice 1 — terminally fence v1 Meeting execution and queue recovery

**Files:** `holdspeak/intel_queue.py:604–683,976–1014`,
`holdspeak/db/intel.py:912–924`, `holdspeak/meeting_session/deferred_admission.py`,
`holdspeak/meeting_session/intel_plan.py:163–322`,
`holdspeak/meeting_session/intel_routed_children.py:184–208`,
`holdspeak/meeting_session/intel_child.py:193`, plus the affected imports,
persistence/history reader, and `tests/unit/test_phase143_intel_queue_inventory.py`,
`tests/unit/test_meeting_deferred_admission.py`, and
`tests/unit/test_phase143_meeting_live_cutover.py`.

1. Add one transactional cutover over pre-C unbound `claimed`/`running` rows.
   Preserve the row, original plan bytes, attempts, and lineage; record a durable
   compatibility-cutover reason/event; make it nonclaimable forever. Do **not**
   reconstruct a `MeetingIntelPlan`, readiness-check a mutable config, or call a
   provider. Reuse the semantic shape of C3 unknown-handoff recovery: a distinct
   linked fresh descriptor can enter the ordinary bound claim path only after the
   old row is inert and ordinary policy admits it.
2. Delete the legacy recovery/admission/direct-runner chain (D2–D5). Ensure a
   current queued legacy-shaped record is claimed through
   `claim_next_intel_job_bound(MeetingDeferredQueueBinder(...))`, not through a
   v1 ad-hoc planner.
3. Delete fresh Meeting resolution/freezing (D1) but retain a deliberately
   non-executing v1 decoder for history/projections. Move the one surviving
   staging-cleanup utility rather than retaining an execution module for it.

**Focused proofs:**

```bash
uv run pytest -q \
  tests/unit/test_phase143_intel_queue_inventory.py \
  tests/unit/test_meeting_deferred_admission.py \
  tests/unit/test_phase143_meeting_live_cutover.py
```

Add/strengthen production-object probes for: (a) a migrated queued row gets one
atomic bound parent/bundle and no v1 resolver call; (b) an old unbound
claimed/running row produces zero provider calls across restart and cannot be
retry/skip/swept into execution; (c) a fresh linked replacement, if policy
allows one, has `origin_job_id`, enters normal C1 binding, and is the only
possible egress; (d) a stored v1 plan remains displayable but has no public
resume/replay route; (e) source/census has no F-owned `InferenceRunner.invoke`
or `resolve_placement` Meeting path.

### Slice 2 — cut marker-gated Settings/Rails authority and close the census

**Files:** `holdspeak/services/settings_service.py:59–116,188–213,579–590,799–839`,
`holdspeak/web_server.py:1119–1157`, `holdspeak/rails_observer.py:291–451`,
`holdspeak/services/inference_adoption_service.py:1722–2056,2180–2464`,
`tests/unit/test_phase143_routing_authority_census.py`,
`tests/unit/test_phase143_inference_capability_census.py`, and
`assets/generated-routing-authority-census.md`.

1. Make settings gates family-specific, not a broad accidental deletion:
   - Meeting marker: hide/refuse its legacy routing controls and eliminate the
     v1 placement summary resolver after migration.
   - Rails marker: hide/refuse `rails_observer.profile_id` and eliminate it from
     recurring runtime input/provenance.
   - Keep only marker-appropriate source fields for unmarked migration.
   - Do not take over the thought/dictation/other-story selectors merely because
     they share a config document. Preserve the Phase-D two-marker meaning for
     owner/wake speech.
2. Make Rails runtime provenance derive from frozen route/bundle evidence, not a
   fresh `profile_id`/`this_machine` config hash. Preserve its proven egress
   badge and known-outcome behavior.
3. Retain the E3 decision/delivery *refusal* boundary—not an override route—and
   prove it remains collision-free and creates no execution object. Then update
   both static/generated censuses to distinguish eliminated F doors from
   legally retained and other-story entries.

**Focused proofs:**

```bash
uv run pytest -q \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_rails_observer.py \
  tests/unit/test_decision_record_service.py \
  tests/unit/test_delivery_factory_routes.py
```

Add probes for each relevant marker absent/present transition: before a marker,
the saved selector can supply the one migration; after it, settings GET omits
and PATCH refuses the selector, runtime mutation cannot alter the next route,
and a restart cannot recover that pointer into route choice. For E3 run the
blank-request success and nonblank-request refusal sequences through real
Decision and delivery HTTP services; assert the latter has a distinct refusal
receipt and zero route/bundle/child/provider calls.

### Slice 3 — preserve the speech compatibility fence while fixing routed egress

**Files:** `holdspeak/speech_session/session.py:585–802,949–1148`,
`holdspeak/speech_session/plan.py:405–644`,
`holdspeak/speech_session/provider.py:114–180,299–491`,
`holdspeak/commands/dictation.py:142–162`,
`holdspeak/web/routes/dictation/_helpers.py:450–483,676–690`, and
`tests/unit/test_dictation_session_admission.py`,
`tests/unit/test_phase143_speech_lifecycle_adoption.py`,
`tests/unit/test_remote_dictation_delivery.py`.

1. Preserve the full pre-cutover fallback and paired-device branch. Refactor only
   enough that a non-device session with **both** markers cannot invoke
   `DictationSessionPlanResolver` to choose transcription/preload/provider work.
   Any remaining `SpeechSessionPlan` object there must be inert validation or
   readable history, while the atomic bundle is the sole execution authority.
2. Put one authoritative `ProviderAdmission`/entry egress accessor behind CLI
   and web. When `routed_routes` exist, take their widest frozen boundary even
   when `transcription_route is None`; use `SpeechSessionPlan.egress_boundary()`
   only for the partial-marker/paired-device legacy cases.
3. Keep provider punctuation unavailable and retain no-dispatch local-only
   speech refusal. Do not let an egress fix create a punctuation capability or
   remote-speech transport policy.

**Focused proofs:**

```bash
uv run pytest -q \
  tests/unit/test_dictation_session_admission.py \
  tests/unit/test_phase143_speech_lifecycle_adoption.py \
  tests/unit/test_remote_dictation_delivery.py
```

Add/retain all four concrete observations: (a) either coupled marker absent
means a wholly legacy owner/wake pipeline; (b) both present yields an atomic
routed pipeline with no plain legacy provider child; (c) with both markers
present, paired-device capture still has SERVICE `device-capture`,
`paired-device:<id>`, **and** `session._route_bundle is None`, with legacy
transcription still functioning; (d) CLI and web show the widest frozen route
boundary for a routed text-entry provider stage, while legacy display remains
correct. Also prove mesh/private transcription refusal has zero dispatch and
that no `speech.punctuate` assignment/route/child is minted.

## Completion checks and risks

### Required final focused sweep

After the three slices, run the union of the focused commands above, then the
story's specified integration proof. Do not call the story done from source
inspection: capture the actual output as Story 08 evidence.

### Risks and mitigations

| Risk | Mitigation / acceptance condition |
|---|---|
| An old claimed/running queue item may already have egressed. | Treat it as unknown historical disposition; never execute it. Fresh work is linked but distinct and normally admitted. |
| Removing a v1 class makes old history unreadable. | Separate reader/DTO decoding from executor/planner removal and use real persisted-v1 fixtures. |
| A marker cleanup removes partial-marker owner/wake or device capture. | Test both one-marker permutations and explicit paired-device `._route_bundle is None`; do not delete `speech_session/child.py`. |
| Egress still falls back to `local` on routed text-entry work. | Route all CLI/web display through a frozen-routes-first accessor and test nonlocal provider-stage routes. |
| Census is “made green” by deleting other stories' rows. | Update only rows demonstrably removed by F; retain owner labels and assert the non-F entrances remain visible. |
| Settings cleanup breaks migration from an unmarked real config. | Gate behavior per family marker and retain the minimal one-transaction source reader until the marker exists. |

## Ruling-shaped questions

None. The only apparent ambiguity—what to do with pre-C unbound claimed/running
queue rows—is already decided by Phase C's unknown-handoff rule: leave old work
inert and, if recovery is allowed, admit a linked fresh job under normal policy;
never replay the old physical attempt.
