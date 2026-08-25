# Story 08 / Phase B cutover design

**Status:** RULED — RATIFY-WITH-AMENDMENTS (Sol, 2026-08-22); the six counsel amendments at the end of this file are binding over conflicting text above.

## Decision

Phase B moves only live-Meeting analysis, labels/title, and Meeting-owned transcription onto the ratified route-plan/controller waist. It does not enable deferred work, plugins, or Stop-to-queue handoff. One `InferenceRoutePlan`, one `InferenceFallbackController`, the capability registry, and the existing runner remain the authorities; the charter forbids parallel replacements (`architecture-contract.md:26-39`, `HANDOVER-STORY-08.md:740-756`).

## Capability and principal mapping

| Work | Capability / frozen policy | Principal and assignment source |
|---|---|---|
| live analysis | `meeting.live_analysis@1`; `retry.structured.standard` | Authenticated **OWNER** `intel_principal`; normal owner precedence. The session refuses rather than synthesizing a principal (`intel_admission.py:96-124`). |
| bookmark label | `meeting.bookmark_label@2`; `retry.text.standard` | Same **OWNER** and owner precedence. |
| auto title | `meeting.auto_title@2`; `retry.text.standard` | Same **OWNER** and owner precedence. |
| transcription | `speech.transcribe@1`; `retry.audio.transcription` | Same **OWNER**, under the Meeting parent; current admission passes `intel_principal` and parent here (`transcribe_admission.py:53-74`). |
| preload | `speech.preload@1`; `retry.internal.lifecycle` | Same **OWNER** only as a derived lifecycle child of that transcription route; never an OWNER assignment. |

The registry fixes these IDs, revisions, visibility, boundaries, and policies (`inference_capabilities.py:1058-1062`); their limits are 4, 4, 4, 2, and 1 physical attempts (`inference_capabilities.py:1166-1171`). No Phase-B route uses SERVICE. The only current service-route policy, `meeting-intel-queue@1`, permits deferred-job capabilities through exact capability rows (`inference_service_route_policy.py:148-184`); do not repurpose it. The parentless `local-model-preload` SERVICE principal is later Phase-D work (`speech_session/session.py:212-232`) and lacks a registered service-route policy.

## Live Meeting bundle

At `MeetingSession.start`, before recorder start and transcription-thread start (`meeting_session/session.py:437-452,494-525`), admit one OWNER `meeting.session` parent plus one atomic bundle. Preserve `definition_ref="meeting:{meeting_id}:intel"`; deadline is start plus the current 12-hour ceiling (`intel_admission.py:61-70,135-157`). Parent input is content-free: meeting ID, provenance, frozen bundle/definition hashes, deadline, and budgets; never transcript, prompt, audio, target ID, endpoint, or secret.

Bundle members, keyed once, are `meeting.live_analysis`, `meeting.bookmark_label`, `meeting.auto_title`, `speech.transcribe`, and nonassignable derived `speech.preload`. Freeze preload in the same transaction from the exact selected transcription deployment, not an assignment lookup; its evidence cross-binds transcription route ID/SHA and deployment. Extend the existing bundle manifest/validator—not a table, registry, planner, or gateway. Current `start()` already atomically freezes and cross-binds members/policy evidence (`inference_parent_route_bundle_service.py:245-355`).

Set `lifecycle_child_budget=8` for MLX (four current candidate repositories maximum × two warming strategies), `0` for faster-whisper, whose `ensure_loaded()` is a no-op (`transcribe.py:99-125,197-230,355-359`). Preserve a 4096 aggregate Meeting-intelligence physical-child budget; reserve `ceil(12h / 10s) × 2 = 8640` transcription physical slots. Thus the MLX parent budget is **13,048**. The existing 4096 budget and ten-second cadence are explicit (`intel_admission.py:64-66`, `transcribe_admission.py:21-47`). Add those aggregate counters to the existing bundle manifest/controller reservation transaction: current bundle arithmetic sums only one policy budget per member (`inference_parent_route_bundle_service.py:183-204`) and would under-budget recurring work. No new table is warranted.

Freeze routes at session admission; freeze operation material only when work exists. For each nonempty audio/window/label/title event, stage private material, call `freeze_operation_for_route_in_transaction`, then `start_execution_in_transaction` atomically (`inference_adoption_service.py:927-980`). The audio loop continues to compose an interval first (`transcribe_loop.py:145-156`). A stopped/terminal bundle parent already refuses a late execution (`inference_fallback_controller.py:115-126`).

## Attempts, winner, and transcription evidence

Delete the new-path call to `run_admitted_capability`: its broad `failed` loop advances entries itself (`intel_child.py:216-260`). The controller owns leg 1/physical 1; compatibility → leg 1/physical 2 with purpose `compatibility`; then eligible fallback → leg 2/physical 3. It derives ordinals and advancement from frozen policy (`inference_fallback_controller.py:244-271,327-369,629-784`). `ProviderCompatibilityRetry` remains typed, but a routed Runner returns to the controller rather than minting a child (`kernel/inference_runner.py:145-175`). `MeetingAdapter`, `run_admitted_child`, and feature/provider dialect loops die on the new path.

Live analysis loses token streaming. Current code broadcasts primary tokens before winner election (`intel_admission.py:442-459`). Buffer each attempt privately; render one final card only after semantic validation and controller election. This is the simplest usable lawful posture. The semantic adapter rejects invalid output before success (`inference_semantic_adapters.py:1-11,139-173`), but coordinator `publish` currently precedes controller settlement (`inference_adoption_service.py:1110-1148`); the Meeting publisher must be a buffer, never a UI publisher. Render only the succeeded result returned after receipt election (`inference_adoption_service.py:1173-1185`).

Transcription publishes exact `{"text": string, "language": null|string}`; the adapter normalizes that closed shape (`inference_semantic_adapters.py:188-195`). Hash contiguous actual sample bytes locally, never caller-supplied SHA: `audio_sha256()` hashes bytes (`speech_session/transcription.py:33-39`) after `Transcriber.transcribe()` canonicalizes the array (`transcribe.py:462-501`). A timeout abandons a native worker today (`transcribe.py:509-535`); map it to `ProviderIndeterminate` after dispatch intent, hence `dispatch_outcome_unknown` and no second model. Runner already terminalizes that signal as physical unknown (`kernel/inference_runner.py:346-353`).

## Preload and Stop

Preload remains lifecycle, not fallback: model-holder and silent-audio are bounded strategies (`speech_session/plan.py:44-47`; `transcribe.py:217-230`). The derived route uses the selected transcription artifact and returns only `{"state": ...}` (`inference_semantic_adapters.py:197-201`). After the speech marker, remove fresh Whisper/preload routing authority from `SpeechSessionPlan`; its resolver currently creates both legacy entries (`speech_session/plan.py:521-553`), but retain its v1 reader. `provider.py` needs no Phase-B routing change: Story 07's routed branch is intent/rewrite only (`speech_session/provider.py:232-254`). Stage names and MLX calls stay; only admission/evidence ownership changes.

Phase-B Stop is **plain bundle fencing/cancellation: no handoff and no deferred row**. Add a no-handoff method to the existing bundle service: derive every active member server-side, call `request_stop_in_transaction`, fence the parent in that transaction, then issue best-effort child cancellation. The handoff primitive demonstrates complete server-side derivation and atomic route stops (`inference_parent_route_bundle_service.py:482-504`); the controller distinguishes pre-send `stopped` from post-dispatch `stopping` (`inference_fallback_controller.py:1004-1083`). Do not call `request_stop_handoff`, which reserves/activates adopter evidence (`inference_parent_route_bundle_service.py:395-577`). Phase C alone supplies queue posture for forever-reserved unknown work; its eventual local-boundary fresh re-run remains distinct from activating old reservation (`story-08-displaced-work-counsel-round1.md:67-85,88-106`).

## Cutover removals, readers, and slices

New live work stops calling `freeze_meeting_intel_plan` (`intel_admission.py:137`), `run_admitted_capability` (`intel_admission.py:424`), and legacy live/label/title seams (`intel_admission.py:442-543`). Callers are `MeetingSession.start` (`meeting_session/session.py:441`), analysis/labels (`intel_analysis.py:105,248`), and Stop (`meeting_session/session.py:601`). Deferred is untouched in B: `DeferredIntelJob.admit` still calls the legacy planner (`deferred_admission.py:139-219`), and `intel_queue.py` calls it/methods (`intel_queue.py:234,476,486,502`). Keep `MeetingIntelPlan`, `SpeechSessionPlan`, legacy child adapters, and DTO/history readers readable; never rewrite v1 bytes.

1. **Bundle and live cards.** Add five-member/derived-preload bundle, aggregate budgets, buffered final projection, controller-only attempts. Tests: extend `test_phase143_meeting_route_primitives.py`, `test_phase143_inference_fallback_controller.py`, `test_meeting_session_admission.py`. Prove ordinals, no token leak, assignment edit after freeze, crash/restart zero duplicate egress. Does not touch queue, plugins, Settings, or handoff.
2. **Meeting transcription.** Route loop audio through frozen transcription; prove byte-derived hash, exact result, MLX lifecycle budget, timeout unknown/no fallback. Tests: `test_transcribe_timeout.py`, `test_transcribe_route.py`, `test_meeting_session_admission.py`, `test_meeting_capture_durability.py`. Does not migrate standalone/wake/hold transcription or pre-session warm.
3. **Fence-only Stop.** Replace live Stop's legacy enqueue with no-handoff bundle fence/cancel; prove all members fenced, late output discarded, restart neither resumes execution nor creates deferred work. Tests: `test_phase143_meeting_route_primitives.py`, `test_meeting_deferred_admission.py`, `test_meeting_kill_recovery.py`. Does not activate, claim, or auto-rerun reserved displaced work.

## Open questions for counsel

1. Ratify the manifest-only aggregate route-budget extension (no new table).
2. Ratify whether Phase-B Stop omits existing deferred aftercare entirely or retains it only for pre-cutover legacy sessions behind an explicit version fence.
3. Confirm Phase D owns closed `local-model-preload@1` SERVICE-policy registration.

---

# Counsel ruling (Sol, 2026-08-22): RATIFY-WITH-AMENDMENTS

The six amendments below are the counsel's exact required text and are
binding over any conflicting statement above. Ruling context: manifest-only
aggregate budgets ratified conditionally (enforcement in the controller's
existing BEGIN IMMEDIATE reservation transaction; never refunded; replay
spends zero); fence-only/no-row Stop REJECTED; Phase-D ownership of
local-model-preload@1 SERVICE policy ratified; buffering ratified (no
elected-stream abstraction in B); the note's 13,048 budget numeral and
single-stream cardinality rejected as wrong.

## Counsel amendment: Phase-B migration and record-only start

This amendment supersedes any reading that leaves Meeting and speech-recognition assignment migration until Phase F.

Phase B moves the `meeting-route-assignments` and `speech-recognition-route-assignments` families forward as startup-owned prerequisites. Schema reconciliation creates the required storage shape only; it MUST NOT seed capability-default assignments, choose a model, invent a built-in profile, or add cloud boundary consent. The startup adapter runs by durable family marker before inference recovery and before any Meeting request. It preserves the exact historically effective primary, exact saved route order, and saved boundary consent; atomically writes assignment effects and the marker; and emits one content-free `InferenceAssignmentMigrationIssue@1` when a blank, dangling, incompatible, or ambiguous legacy value cannot be mapped. `speech.preload` receives no assignment row.

A migration issue or parent/bundle admission refusal MUST NOT fail Meeting capture. The Meeting and audio journal are created, raw recording starts, and the Meeting enters an explicit durable `record_only` transcription state carrying the family, reason code, and repair verb. Intelligence carries its separate visible refusal state. A dropped transcription interval is never represented only by a log message. No assignment repair, provider construction, model download, or model load may be a prerequisite for creating the durable Meeting and starting raw audio capture.

The Phase-B capture front door MUST NOT eagerly construct faster-whisper or any other model-loading backend before the Meeting and audio journal exist. Backend construction and loading occur only after exact route admission as derived lifecycle work, or reuse an already-loaded artifact whose durable lifecycle receipt identifies the same frozen deployment revision.

Phase F retains Settings-reader cutover, post-marker legacy-write refusal, remaining migration families, cleanup, and census closure.

## Counsel amendment: recurring aggregate budget

This amendment supersedes the `13,048` parent-budget numeral.

The bundle manifest contains immutable aggregate budget groups and binds every route member to exactly one group:

- `meeting-intelligence`: the existing shared physical-attempt allocation of `4096` across live analysis, bookmark label, and auto title;
- `meeting-transcription`: every physical attempt for recurring `speech.transcribe` operations;
- `meeting-preload`: every derived `speech.preload` lifecycle operation.

Let:

- `D = 43,200` seconds;
- `T = 10` seconds;
- `I = ceil(D / T)`;
- `S = 2 + count(frozen_requested_remote_device_ids)`, reserving mic, system, and every remote source requested before session admission;
- `A = retry.audio.transcription.total_physical_attempts`, currently `2`;
- `H = 2` additional physical transcription reservations for the existing headroom;
- `P` be the exact frozen preload allocation.

The transcription allocation is `B_transcribe = A * S * (I + 1) + H`; the `+1` covers the final pending pass at Stop. The parent child budget is `4096 + B_transcribe + P`. Per-execution retry-policy limits remain independent and MUST NOT be added again on top of these aggregate allocations.

The aggregate allocations and member bindings are immutable manifest evidence. No mutable JSON counter and no new table are introduced. On every `reserve_next_attempt`, the controller uses the existing `BEGIN IMMEDIATE` transaction to count durable attempt reservations across all route-plan IDs in that budget group, refuses the reservation that would exceed the group allocation, and inserts the new attempt in the same transaction. Every reservation, including failed, abandoned, and physical-outcome-unknown work, spends once and is never refunded. Idempotent replay of the same reservation command spends zero additional capacity.

The exact requested remote-device set is passed into bundle admission before `MeetingSession.start`. No source absent from that frozen set may later acquire transcription capacity under the parent; an attempted undeclared attachment is visibly refused rather than silently dropping its audio.

## Counsel amendment: derived preload authority

Meeting preload remains nonassignable derived lifecycle work under the Phase-B OWNER Meeting parent. The preload member is derived in the parent/bundle transaction from the exact selected `speech.transcribe` deployment revision and cross-binds that transcription route ID, route SHA, deployment revision, engine, model artifact, candidate material, and lifecycle strategy sequence. It never performs an assignment lookup.

For MLX, `P = 8` is permitted only when the exact maximum-four repository candidate sequence and the two strategy names (`model-holder`, `silent-audio`) are frozen into the bundle before work begins. Runtime code may execute that frozen sequence but may not rediscover, reorder, add, or substitute candidates.

For faster-whisper, `P = 0` is permitted only when no model construction or load occurs on the Phase-B path because the same frozen deployment was already loaded under a durable lifecycle receipt. The current eager `WhisperModel` constructor does not satisfy that condition. Otherwise construction/loading becomes one or more explicit derived `speech.preload` operations and `P` includes their physical reservations.

Phase D owns the closed `local-model-preload@1` SERVICE-route policy for the parentless pre-session warm. That policy names only the `local-model-preload` service principal, exact operation set, exact internal capability, allowed local boundaries, and model-revision authority basis. It is not registered or used by Phase-B Meeting preload.

## Counsel amendment: Phase-B Stop preserves deferred aftercare

This amendment supersedes "no handoff and no deferred row," "replace the legacy enqueue," and every Slice-3 assertion that restart creates no deferred work.

Phase-B Stop first closes live admission and invokes one server-derived bundle fence/cancel transaction. That transaction derives every bundle member from durable bundle evidence, requests Stop for every active execution, fences the parent epoch, commits, and then performs best-effort physical child cancellation. Phase B does not call `request_stop_handoff` and does not create a new adopter reservation.

After the live fence, Stop runs the pre-cutover displaced-work derivation and the existing legacy `enqueue_intel_job` path unchanged in payload and queue authority. Sessions with transcript segments retain final analysis; sessions with bookmarks retain bookmark-label refinement; untitled sessions retain auto-title. The legacy enqueue is not gated solely on the existence of a successfully admitted new live bundle. Its Meeting-keyed upsert remains the idempotency boundary.

Phase C alone replaces this legacy row with the atomic claimed-job/parent/route-bundle handoff. Until that Phase-C cutover lands, every Phase-B Stop converges after retry or restart to exactly one legacy deferred job when the existing product predicate requests aftercare. It never converges to zero merely because the live path was migrated first.

## Counsel amendment: publication and recurring identities

Phase B provides no model-token or partial-transcript streaming abstraction. Attempt output remains private through semantic validation, durable attempt-result staging, controller settlement, and winner election. The Meeting UI receives exactly one final succeeded result after the controller receipt identifies the winner and the live bundle fence still permits publication. Failed, invalid, superseded, cancelled, deadline-exhausted, and physical-outcome-unknown attempts publish no model bytes. Mechanical non-model progress state may remain visible.

Every recurring operation and command identity is deterministic across retry and process restart:

- transcription: Meeting ID, frozen source ID, interval start/end, actual canonical-audio SHA, and final-pass flag;
- live analysis: Meeting ID, transcript/window SHA, window bounds, and final flag;
- bookmark label: Meeting ID, bookmark timestamp or durable bookmark identity, context SHA, and summary SHA;
- auto title: Meeting ID and transcript SHA.

A random analysis UUID may remain an in-memory UI supersession token but MUST NOT participate in durable operation, command, reservation, or execution identity. Repeated identical audio on distinct source intervals remains distinct; replay of the same interval adopts the same frozen operation and cannot create duplicate egress.

## Counsel amendment: startup unwind and slice acceptance

Once the parent/bundle transaction commits, every later failure before `capture_status="recording"` idempotently fences/cancels that bundle before the audio-layer start error returns. Inference migration, route resolution, bundle admission, preload, and provider availability failures do not enter this abort path; they degrade to visible record-only capture.

Slice 1 additionally proves: exact one-way Meeting/speech migration; no schema-owned default assignment; no guessed local artifact; no silent cloud route; family-marker replay; no-assignment record-only capture; durable visible repair; raw audio start despite route refusal; and bundle unwind after Meeting-save, journal-open, or recorder-start failure.

Slice 2 additionally proves: mic plus system plus requested-device cardinality; final-pass and headroom arithmetic; aggregate-group exhaustion under concurrent reservations; replay spending zero; no post-freeze source attachment; deterministic interval identity for repeated identical audio; MLX frozen candidate/strategy evidence; faster-whisper construction under lifecycle authority; exact `{text, language}` output; actual-byte SHA; and timeout unknown with no fallback.

Slice 3 proves: every live bundle member fenced; late output discarded; no new reservation after Stop; restart never resumes the fenced live execution; and exactly one legacy deferred row remains queued whenever the pre-cutover aftercare predicate applies. The "creates no deferred work" assertion is deleted.

### Counsel clarification: exact local Whisper migration

The prohibition on choosing a model or inventing a built-in profile does not prohibit converting the owner's historically effective saved Whisper selector into immutable v2 authority.

The `speech-recognition-route-assignments` migration MUST create an exact visible Model Library profile, exact local deployment revision/head, exact binding, and `speech.transcribe` assignment when all of the following hold:

1. the saved model name is nonblank;
2. the saved backend resolves through a closed, versioned built-in speech-artifact mapping to one exact local runtime and artifact identity;
3. the resulting deployment boundary is `same_device`, with empty endpoint and secret material;
4. the saved language is valid and is copied into durable post-marker speech-operation authority;
5. no remote destination, cloud consent, model acquisition, model load, or network egress is required to establish the records.

The migration derives deterministic profile, deployment, binding, assignment, and observation identities from the migration family, normalized selector material, and source SHA. It writes the profile revision, deployment revision/head, content-free readiness observation, binding revision/head, `speech.transcribe` assignment, and family marker atomically. The readiness observation records only locally knowable truth and MUST NOT claim the artifact ready unless that state was actually observed without loading or downloading it. The created profile is a normal owner-visible Model Library profile with provenance `legacy-model-config`; it is not hidden migration machinery.

This conversion preserves the saved historically effective primary; it does not create an assignment for `speech.preload`. After the family marker, speech execution is independent of the legacy ModelConfig selector.

Blank selectors, `backend=auto`, unknown or dangling built-in names, arbitrary repository/path selectors, and anything remote or cloud continue to return `builtin_profile_required` with repair `choose_audio_model_profile`, with no partial profile, binding, assignment, or marker.

*(Ruled by counsel 2026-08-22 against commit 34c3a9b3, superseding the slice-1a unconditional speech refusal; implementation lands with slice 2.)*

### OWNER SCOPE RULING (2026-08-22): migrations stay minimal

The owner, mid-Phase-B: "don't obsess with migrations... I'm pretty much the
only user, don't overdo it." This binds all remaining slices and overrides
any ceremony-expanding reading of the counsel amendments above:

- Migration = read the owner's saved settings once, write the assignment
  rows (and for speech, one visible profile), one transaction, a couple of
  tests. Done.
- No new migration families, issue taxonomies, repair-verb catalogs,
  deterministic-identity derivation rituals, or readiness-observation
  ceremony beyond what already shipped in slice 1a.
- Sol's cheap substantive limits survive: local-only, no download/load at
  migration, created profile visible in the library, auto/blank/unknown/
  remote selectors simply don't migrate.
- record_only capture stays but stays small: one durable state, recording
  never dies because of model config. No repair UI machinery in this phase.

### Orchestrator amendment (2026-08-22): day-one continuity — auto resolves deterministically in migration; readiness bootstraps from the first successful load; MLX warmup ships as one bounded preload child with frozen candidate evidence (P=1, ceremony trimmed per the owner scope ruling). Owner may overrule at the sitting.
