# HS-131-09 design — Dictation and transcription are admitted per session

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-10) — the eight amendments in the Sol ruling below are binding on implementation  
**Decision boundary:** one admitted, finite session parent covers the authority lifetime; each actual Whisper or dictation-provider dispatch is one `inference.invoke@1` trusted child and terminal receipt. Capture/VAD/buffering/token handling are not invocations.

## Context

`Transcriber` calls MLX directly for its silent fallback preload (`transcribe.py:201-225`) and both MLX and faster-whisper transcription (`:227-275`, `:315-340`). It is shared by meeting transcription (`meeting_session/transcribe_loop.py:60-70`), desktop/browser dictation (`runtime/dictation_capture.py:30-49,283-292`), and wake (`runtime/wake_glue.py:204-237`). Dictation then calls providers directly at OpenAI-compatible classify/rewrite (`plugins/dictation/runtime_openai_compatible.py:126-200`), llama.cpp classify/rewrite (`runtime_llama_cpp.py:134-169`), mesh relay (`runtime_mesh_relay.py:106-110`), and the two-attempt intent-router loop (`builtin/intent_router.py:169-190`).

HS-131-08 establishes `InferenceRunner`, `OuterRunContext`, `ServiceContract`, trusted children, immutable ordered revision lists, and `run_admitted_capability`; reuse those shapes without runner/broker domain branches. `meeting.session` already owns its principal/deadline/cancellation/journal fences. The existing typing/delivery effect admission remains a distinct operation.

## 1. Parents, principals, and finite session plans

- Add `dictation.session` and `wake.session` parent kinds/operation names, `ParentRunCodec` entries, and the `kernel_parent_runs.kind` CHECK as schema **v56** (v55 is the established platform). Keep operation-name literals centralized; update the expected version pins and symbolic consumers only. No change to generic runner/broker.
- A desktop hold admits exactly one `dictation.session` after `VoiceTypingSession.begin()` accepts at `runtime/dictation_capture.py:422-468`; release (`:470-491`) closes capture but leaves that parent live only while its bounded transcribe/pipeline tail drains. The authenticated desktop-route/runtime principal admits it. Failed/busy press admits nothing.
- Browser open mic admits one `dictation.session` when `startOpenMic()` begins (`web/src/lib/micSession.ts:352`), passes its opaque live parent context to each server utterance request, and cancels/closes it at `stopOpenMic()`/`closeMicSession()` (`:365`, `:267`). It covers all utterances in that click-to-toggle interval, never a per-utterance owner decision. A reconnect cannot recreate context: it obtains a new authenticated session.
- Wake admits one bounded `wake.session` after armed capture yields nontrivial audio (`wake_glue.py:185-202`). It has no live route caller: mint narrow `PrincipalKind.SERVICE` identity `wake-capture`, allowed only `wake.session@1` and its trusted `inference.invoke@1` children, with `authority_basis="configured-wake:<wake-config-revision>"`. The owner configuration is `Config.wake_word` (`config/core.py:214-229,283`), specifically enabled/action/armed-window at `config/device.py:59-90`; configuration arms the action under the Phase-107 ruling, not a fabricated `OWNER` principal.
- Persist a content-free `DictationSessionPlan@1` / `WakeSessionPlan@1`: parent/session ID, authenticated actor or service identity, authority/config revision, insertion aim/context hash, plan hash, start/deadline, child budget, pipeline/config/registry hashes, and `capabilities: capability -> [exact deployment revisions in ordered primary/fallback order]`. Include `whisper-transcribe`, `intent-classify`, `rewrite`, and `punctuate` when enabled. A missing capability/revision refuses; no post-admission placement resolution.
- Hold deadline is `release + 90s`, budget 12 provider attempts: comfortably above one transcription plus the bounded classifier retry and configured stages, but no abandoned tail. Browser open-mic expires at `min(open+30m, last-utterance+90s)` with a 1,024-child budget; its 30-minute ceiling prevents an indefinitely armed mic from retaining authority. Wake deadline is capture completion + 30s and budget 8. Expiry/cancel closes the parent; continuation is a new authenticated session, never an epoch reset.

## 2. Contracts, adapter seams, and fallback

- Make `Transcriber.transcribe(audio, *, outer_context, capability="whisper-transcribe")` require a live context for every nonempty model dispatch. `Transcriber` validates/normalizes audio before the child, then invokes `InferenceRunner` with `holdspeak.whisper-transcribe@1`; its canonical dispatch-only payload includes audio SHA-256, sample count/rate, backend/model options, language, plan hash, and selected revision. It journals only the hash and safe metadata. Empty/invalid audio creates no child.
- Thread the existing meeting `OuterRunContext` from `MeetingSession` through `TranscribeLoopMixin._transcribe_audio()` to `Transcriber`; each interval is a `whisper-transcribe` child of the live **existing** `meeting.session`, not a `dictation.session`. If no live meeting context remains, drop/refuse the interval before Whisper.
- Dictation and wake retain their parent contexts from Section 1 through `_kick_off_transcribe`, `_transcribe_and_type`, `_transcribe_wake`, and `transcribe_audio`. `text_processor.process()` is lexical/non-model work unless a configured provider-backed punctuation stage is selected; that selected stage is `holdspeak.dictation-punctuate@1`.
- MLX `ModelHolder.get_model` is an invocation too: in session opening it is a `holdspeak.whisper-preload@1` child of that live session; silent-audio fallback is likewise one preload child, not an unreceipted internal call. Pre-session warmup may use only `SERVICE("local-model-preload", {("inference.invoke", 1)}, "configured-local-model-preload:<revision>")` under a new explicit `model.local_model_preload_authority` config knob containing the enabled authority basis/config revision. Absent/blank/mismatched authority defers preload to the first admitted session (or refuses if the caller requires warmup) before any MLX dispatch.
- Replace provider methods with adapters invoked by `run_admitted_capability(context, plan.capabilities[capability], ...)`: `holdspeak.dictation-intent-classify@1`, `holdspeak.dictation-rewrite@1`, and `holdspeak.dictation-punctuate@1`. The walker advances only after the adapter returns its honest failed/error-result classification. The OpenAI `response_format` retry at `runtime_openai_compatible.py:126-156`, intent router’s two classify attempts, and any provider-reaching compatibility fallback are separate children with distinct attempt ordinals and terminal receipts; a validation/lexical no-match is not.
- The mesh adapter must pass the same frozen selected revision and warrant through the existing mesh envelope used by `intel/mesh_relay.py:88-105`; `runtime_mesh_relay.py:102-116` must not build a fresh target or envelope. llama.cpp and OpenAI adapters get the selected frozen revision before construction, not mutable runtime settings.

## 3. Cancellation, publication, and journal hygiene

- Mic close, hold tail cancellation, wake stop, revocation, deadline, or budget exhaustion first calls `ParentRunController.cancel()`. Trusted-child submit/claim revalidates parent liveness, authority, expiry, epoch, and budget atomically, so no new utterance/provider dispatch starts after the fence. Actively running native/remote work is cancelled best-effort; no acknowledgement is `indeterminate`.
- Carry the parent context/cancellation event into the dictation continuation. Before `text_processor` provider stages, rewrite publication, preview issuance, `process_transcript`/`run_dictation_pipeline`, and the delivery seam, check cancellation and discard text. The concrete landing boundary is before `type_text_from_owner_gesture` in `_transcribe_and_type` and `wake_glue.py:248-253`; delivery still performs its own existing effect admission and idempotency after this inference fence, never a duplicate inference-side delivery receipt.
- Stage any preview/rewrite/pipeline result as a per-kind projection with `discard_on_parent_cancel=True`; finalize only from the winning child receipt. Do not add a runner-level post-dispatch parent recheck. Existing native dictation records remain the authorized content store.
- Parent/child inputs, contracts, errors, result refs, and receipts contain IDs, capability, revision, counts/durations, safe reason code, and SHA-256 only. Never journal audio, transcript/dictated text, prompt, completion/token stream, API key, warrant, or raw provider exception; adapters map errors to sanitized class/reason strings.

## 4. Latency and A/B proof

- Parent plan admission is paid once at hold press/open-mic/wake arm and is off the release-to-landed hot path. On release, the hot path is `transcribe -> classify/rewrite/punctuation -> existing delivery`; it pays one trusted-child admission/claim per actual provider dispatch, before adapter construction. No provider dispatch skips a receipt.
- Phase 107 measured approximately **25 ms/op** admission price; HS-131-02 supplies the runner’s measured per-invocation cost. Thus the bounded added hot-path cost is `N * child-admission-cost` for actual calls (normally Whisper plus only enabled stages), not a top-level decision per utterance or per frame. Frozen plans avoid route/model lookup; the only cheap path is trusted-child admission, which still creates the receipt and validates liveness. This must be measured, not assumed: release-to-landed median and p95 may regress by at most `max(25 ms, 5%)` each.
- Extend `scripts/measure_dictation_latency.py` `_percentiles()` (`:182-191`) and summary schema to report `p95`, retaining `release_to_landed_ms` from key release through driver-sink `landed_at` (`:249-287`). Run the exact command `uv run python scripts/measure_dictation_latency.py --warmups 2 --runs 20 --typing-mode driver` on a clean-fork control and story branch consecutively, same 16 kHz fixture, machine, model, backend, config, and driver sink; preserve both JSON lines and compare median/p95 by the written threshold.

## Invariants

1. One authenticated mic-open/hold/wake lifetime has one finite parent; every actual model invocation under it has exactly one child and terminal receipt.
2. Each child uses one exact ordered-plan revision; provider-reaching retry/fallback is another child, while VAD/capture/buffer/token/non-model work is not.
3. Child admission/claim never repeats the owner decision but always validates live, unrevoked, unexpired parent authority and budget.
4. Cancellation/expiry/revocation fences new work and late text before preview/rewrite/delivery; effect admission remains separate.
5. Kernel journal rows are hashes and safe metadata, never speech or model content.
6. The release-to-landed median and p95 regression stays within `max(25 ms, 5%)` against the contemporaneous control.

## Test matrix

| Acceptance criterion / invariant | Planned focused proof |
| --- | --- |
| Hold one parent; browser interval one parent/many utterances | `test_dictation_runtime.py`: press/release and authenticated browser open/close context/cardinality |
| Wake service authority, plan, deadline/budget | focused wake test: config revision basis; no owner synthesis; expiry/refusal |
| Whisper/MLX preload routing | shared Transcriber tests: meeting/dictation/wake child parent, in-session preload, pre-session authorized/defer/refuse |
| All provider seams, exact revisions, fallback/retry receipts | runtime/intent tests for OpenAI, llama, mesh envelope, response-format fallback, classifier retry, missing-plan refusal |
| No child for non-model work | VAD/capture/buffer/empty/lexical punctuation and token-stream cardinality tests |
| Liveness, cancellation, no late landing | dictation/wake/meeting tests cancel before provider completion and assert no preview/rewrite/type while delivery admission remains singular |
| Journal privacy | sentinel scan across parent/child success, refusal, error, cancellation, indeterminate, preload paths |
| A/B and device behavior | prescribed 2+20 control/branch driver A/B with median+p95; manual real browser two-utterance open mic, desktop hold, wake, cancel-before-land, receipt inspection |

## Recorded notes

- Below the rigor bar: per-frame/per-token receipts, cross-process restoration of opaque browser contexts, automatic unlimited open-mic extension, and forced termination of uninterruptible native MLX work. The bounded deadlines and `indeterminate` receipt are deliberate.
- The existing browser `micSession` lifecycle is client-side evidence only; server admission must derive its principal from authenticated route/session credentials, never a client-supplied principal or parent ID alone.
- The current wake config has no explicit `authority_basis` field and the model config has no preload-authority knob. Their additions are required before autonomous wake/preload admission; until then those invocations refuse/defer rather than infer authority from local process identity.

## Open questions for Sol

1. Ratify v56’s two parent kinds and 90s/12, 30m/1,024, and 30s/8 session fences, or set different bounded product limits.
2. Ratify `wake-capture` and `local-model-preload` narrow SERVICE identities and the exact `configured-wake:<revision>` / `model.local_model_preload_authority` basis formats.
3. Confirm whether browser speak-to-fill (`transcribe_audio`) joins the surrounding browser mic session or must admit a short authenticated `dictation.session` per click; it cannot remain contextless.
4. Confirm that the existing dictation pipeline can expose every selected capability and ordered revisions at session admission without late mutable config reads; otherwise name the minimal plan resolver seam.
5. Confirm the runtime cancellation carrier/seam that reaches `process_transcript` and preview issuance without changing the separate delivery-effect contract.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The design has the right constitutional
shape: one finite parent per actual authority lifetime, one trusted child
and terminal receipt per model dispatch, no children for mechanical audio
work, and a separate effect admission for landing text.

### Amendments (binding; hot-path cost stated by Sol per amendment)

1. **Bind desktop and browser acquisition to a monotonic
   session-generation token; if release/stop or admission failure wins
   before acquisition completes, cancel any newly admitted parent, tear
   down capture, and discard the audio.** (Release-before-admission /
   stop-before-open / orphan-parent races. Cost: one in-memory comparison
   at acquisition; none on release-to-landed.)
2. **Admit a hold with a 30-minute capture ceiling and a preauthorized
   90-second drain, then atomically SEAL it on release to
   `min(start+30m+90s, release+90s)` and close immediately when the tail
   finishes.** ("release+90s" is not an honest persisted deadline at
   press. Cost: one parent-state transition at release, INCLUDED in the
   A/B median/p95 accounting.)
3. **When a browser parent reaches its inactivity/30m/budget/cancel/
   revocation fence, force the client mic interval CLOSED — a new
   authenticated click, never a silently replaced parent.** (One visible
   interval must not cross authority epochs. Cost: terminal paths only.)
4. **Derive `configured-wake:<revision>` deterministically from the
   canonical persisted WakeWordConfig; do NOT add a user-authored wake
   authority_basis field. ADD the `model.local_model_preload_authority`
   knob; unauthorized pre-session preload defers/refuses.** (Existing
   enabled+action+armed-window already arms wake per the Phase-107
   ruling; refusing for a redundant field would wrongly disable
   authorized wake. Cost: plan construction only.)
5. **Wake child budget 12, not 8.** (A first-session path can consume
   nine children legitimately.)
6. **Transcription-bearing meeting.session plans add
   `ceil(session_max_duration / TRANSCRIBE_INTERVAL) + 2` children to
   the 4096 allocation (8418 at 10s/12h).** (Twelve hours = 4320
   transcription children before any intel child — deterministic
   exhaustion of the advertised session. Cost: none; same atomic check
   against a larger frozen bound.)
7. **Every explicit ModelHolder.get_model attempt and every silent-audio
   fallback dispatch is a separate SIBLING `holdspeak.whisper-preload@1`
   child, completed before the ordinary transcription child; preload
   adapters must not reacquire transcription_lock.** (One broad child or
   nesting hides invocations; sibling sequencing avoids
   invocation-in-invocation lock cycles. Cost: one child admission on a
   normal first-session preload; authorized pre-session warmup removes
   both from release-to-landed.)
8. **The browser `last-utterance+90s` lease refreshes atomically inside
   the first Whisper child claim of that utterance, bounded by open+30m;
   empty/invalid/VAD-only/buffering activity never refreshes it.**
   (A separate lease round-trip would make the latency claim dishonest;
   non-model activity must not retain authority. Cost: zero extra round
   trips.)

### Key rulings

- **Session fences ratified as amended**: hold = press→release+bounded
  drain (30m ceiling); browser = 30m/1024/90s-inactivity with visible
  closure on any fence; wake = 30s/12; meeting budget per Amendment 6.
  Threading the exact existing meeting OuterRunContext respects
  HS-131-08's fences.
- **Principals ratified**: authenticated route/runtime principal for
  desktop/browser (parent handles opaque, server-issued, bound to the
  authenticated route + generation — never a client-supplied parent id);
  SERVICE `wake-capture` (wake.session@1 + its planned children only)
  under `configured-wake:<derived revision>`; SERVICE
  `local-model-preload` under
  `configured-local-model-preload:<revision>` from the new knob. The
  preload knob is in-scope and required; refusal-by-default correct for
  preload, INCORRECT for an enabled valid revisioned wake config.
- **Latency ruling**: the honest desktop bound is ONE release seal plus
  N trusted-child admissions. Browser inactivity refresh adds no round
  trip. Preload contributes only when a preload dispatch occurs and
  cannot be excluded from first-use A/B results. The max(25ms,5%)
  median+p95 threshold is controlling; if the seal or child path
  exceeds it, optimize — the threshold is not waived. One documented
  p95 estimator (nearest-rank acceptable) on both sides.
- **MLX boundary**: distinct sibling children (get_model → receipt;
  failed → second preload child before silent fallback; then the
  transcribe child). An API performing inseparable internal lazy loading
  as part of one model call stays one child — but today's explicit
  get_model, fallback transcribe, and ordinary transcribe are separate
  invocations.
- **Speak-to-fill (OQ3)**: inside an active open-mic interval it joins
  that parent; a one-shot click outside admits one short authenticated
  dictation.session and closes after its bounded tail; it may not borrow
  an unrelated or stale global mic context.
- **Plan resolver (OQ4)**: one minimal session-opening seam
  (`DictationSessionPlanResolver.resolve(config_snapshot,
  registry_snapshot, principal, insertion_aim)`); adapters receive the
  frozen deployment directly, never reconstruct from mutable settings.
- **Cancellation carrier (OQ5)**: the immutable OuterRunContext +
  cancellation token passes EXPLICITLY through _kick_off_transcribe,
  _transcribe_and_type, _transcribe_wake, transcribe_audio, provider
  continuations, process_transcript, preview issuance, and pipeline
  callbacks — each closure captures its own context; NO ambient mutable
  "current dictation session" field.
- **Journal**: adapters map exceptions to fixed safe classes before
  journaling; str(exc) never crosses into kernel records.
- **A/B**: protocol sufficient; preserve both JSON summaries + commit/
  fixture/config identity; 20-run p95 tail sensitivity is a recorded
  limitation, not grounds to weaken the owner's threshold.

### Sol recorded notes

- Insertion aim is provenance/plan input, never landing authority — the
  separately bound effect admission prevents silent retargeting.
- A model-heavy browser interval may legitimately exhaust 1024 children
  before 30 minutes; visible closure + a fresh click is correct.
- Forced termination of uninterruptible native MLX stays below the bar;
  fence publication + honest indeterminate is sufficient.
- No runner/broker domain conditionals; no runner-level post-dispatch
  parent recheck.

### Orchestrator disposition

All eight amendments ADOPTED — each names a real-use defect (races 1/3,
dishonest deadline 2, wrongly-disabled wake vs unauthorized preload 4,
deterministic budget exhaustion 5/6, hidden invocations + lock cycles 7,
dishonest latency accounting 8). Amendment 6's arithmetic is the
standout: Sol computed the 12-hour exhaustion the draft missed.
