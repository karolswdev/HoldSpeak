# HS-131-08 design — Meetings are admitted per session

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-10) — the two amendments in the Sol ruling below are binding on implementation  
**Decision boundary:** one authenticated, durable `meeting.session` parent covers live meeting intelligence while capture is active. Every actual provider dispatch is an `inference.invoke@1` trusted child. Post-close deferred work is a new, short-lived admitted queue-job parent, never a revival of the recorded session.

## Context

Live windows call `self._intel.analyze()` directly at `meeting_session/intel_analysis.py:60-102`; deferred base analysis does likewise at `intel_queue.py:193-230`, then runs the routed chain at `:262-307`. `MeetingSession.start()` presently resolves mutable runtime settings and constructs `MeetingIntel` (`meeting_session/session.py:430-515`); `stop()` waits, then performs final Intel and MIR work (`:620-739`). Its `analysis_id` interruption only stops local token consumption (`intel_analysis.py:90-102`), not provider cancellation.

HS-131's established path is `InferenceRunner.invoke()` (`kernel/inference_runner.py:166-230`): hash a versioned `ServiceContract`, admit/claim, build only with `build_intel_for_revision`, dispatch, stage, then elect one child terminal receipt. A supplied `OuterRunContext` selects atomic trusted-child admission, which re-derives the durable parent owner, epoch, warrant, liveness, deadline, and child budget under one transaction (`kernel/trusted_child.py:16-98`).

## 1. Parent, authority, and lifecycle

- Add parent kind `meeting.session` with operation name `meeting.session` in `kernel/runtime.py`, `ParentRunCodec`, and the `kernel_parent_runs.kind` CHECK migration: schema v54 (v53 is HS-131-07 at `db/schema.py:10,1712-15`). Use `ParentRunController.start()` with `definition_ref=meeting:<meeting-id>:intel`, an immutable `definition_revision` equal to the plan hash, and idempotency key `meeting-intel-session:<meeting-id>`.
- Admit it once, immediately after `MeetingSession` creates its `MeetingState` and before an Intel engine exists (`session.py:443-505`). Store its opaque `OuterRunContext` only in the live `MeetingSession`; durable rows retain only the parent operation ID and safe snapshot.
- `_start_meeting()` currently accepts no principal (`runtime/meeting_glue.py:186-268`), so it cannot honestly claim the UI caller. Thread the authenticated route principal through that seam. Device-initiated recording must be issued an explicit, non-owner `meeting-capture` runtime service principal by the local device/runtime authenticator, authorized only for meeting capture/intelligence; it must not synthesize `OWNER`. Until that issuer exists, start recording with intelligence refused/disabled rather than admitting anonymous intelligence.
- The parent deadline is `started_at + 12h`; its finite child budget is 4,096 actual provider attempts. This covers normal long meetings while making resource and authority exhaustion explicit. There is no silent renewal: expiry/budget exhaustion stops live intelligence and may enqueue a separately admitted deferred job. A new 12-hour live session requires an explicit authenticated continuation decision, not an epoch reset or revived parent.
- `stop`, explicit interrupt, revocation, or expiry first cancel the live parent. `ParentRunController.cancel()` advances the epoch and attempts cancellation of the active child; adapter acknowledgement `unknown` is child `indeterminate`, never guessed success/failure (`parent_run.py:219-235`; `inference_runner.py:72-144`). `stop()` must not retain the current direct final Intel/MIR dispatch after cancelling; it queues the existing final work for the deferred path below. Close the live parent after cancellation/drain with its honest terminal outcome.

## 2. Immutable meeting routing/deployment plan

At admission, resolve and persist a `MeetingIntelPlan@1` without transcript/audio content:

- `meeting_id`, capture provenance, meeting configuration revision, routing profile/config hash, enabled-plugin registry/version hash, plan creation time, deadline, and budget;
- capability map `{live-analysis, deferred-base-analysis, plugin:<plugin-id>:<declared-capability>}` to immutable deployment-revision IDs, plus the selected target/boundary metadata needed for receipt refs; and
- plugin order/configuration snapshot and a plan SHA-256 used as `definition_revision`.

Resolution is per capability, not one meeting-wide model. A live-analysis child uses `plan.deployments["live-analysis"]`; a plugin child uses its own declared capability entry even when it differs from live analysis. Each `InvocationRequest.deployment_revision` and its canonical payload repeats that exact ID; the runner resolves it only from `deployment_revisions` and calls `build_intel_for_revision` (`inference_runner.py:188-193`, `inference_targets.py:552-581`). No child may call `resolve_placement`, `resolve_inference_target`, or `build_intel_for_target` after the plan is frozen. A route selecting a plugin/capability absent from the plan is a refused/recorded plugin run, not a fallback to today's configured model.

## 3. The admitted child seams

- **Live window:** replace `MeetingIntel.analyze(transcript, stream=True)` with a `CanonicalPromptAdapter` and `holdspeak.meeting-live-analysis@1`. Payload has schema version, transcript SHA-256, window/segment bounds, prompt/template revision, limits, `final` flag, plan hash, and deployment-revision ID; transcript text is dispatch-only material. Its trusted child carries the live session parent ID/context and deterministic invocation ID from meeting ID, transcript/window hash, capability, and attempt ordinal. Non-model windows (empty, already-running skip) create none.
- **Deferred base analysis:** a claimed queue job can run after the live parent closed, therefore it must not join or revive it. At job claim, admit `meeting.deferred-intel-job` as a distinct short-lived parent with the authenticated queue-worker service principal, meeting ID, transcript hash, queue attempt/idempotency key, and a freshly frozen deferred plan. Its one base-analysis attempt is `holdspeak.meeting-deferred-analysis@1` child. This is a fresh, honest queue authority decision, not a per-window owner decision and not a second *live session* parent.
- **Routed plugins:** run `run_meeting_plugin_chain()` only under that queue-job context. Each actual plugin provider dispatch receives the queue parent's trusted context and `holdspeak.meeting-plugin:<plugin-id>@1` contract. Preserve route order and `build_idempotency_key()` (`meeting_plugins.py:166-196`); deduped/skipped/faulted plugins issue no child. Plugin result/artifact writes are staged projections, never direct writes from provider completion.
- **Retries/fallbacks:** every provider-reaching retry or fallback has a distinct invocation ID and `attempt_ordinal`; it is another trusted child and receipt. Map `IntelJob.attempts`, `_retry_or_fail_job()`'s scheduled retry/terminal failure records (`intel_queue.py:72-122`), and plugin exact idempotency keys to that ordinal. Retrying a queue job creates a new short-lived job parent; it never reopens an old one.

## 4. Publication, cancellation, and latency

- Adapters stream tokens only while their cancellation event is unset. Token broadcasts remain ephemeral and are suppressed after cancellation; final snapshots, queue status, plugin runs, and artifacts are `ProjectionStager` kinds with `discard_on_parent_cancel=True`. Stage their result refs in the runner `publish` callback, finalize transactionally only after the winning child receipt, and discard on cancelled/expired/revoked parent. Meeting kinds have no checkpoint CAS; do **not** add a runner-level post-dispatch parent recheck.
- A child admission is the trusted-child lock/receipt path, not a new top-level owner decision. Its cost lands once per actual live window/provider attempt, before adapter construction; the session parent has already paid placement/authority resolution. A rejected child emits no provider request.
- Parent cancellation fences new continuations atomically. The active provider is cancelled best-effort; unknown remote disposition remains `indeterminate`, and its staged result cannot reach meeting state.

## 5. Contract and journal hygiene

Each service contract hashes the complete canonical payload, including transcript/prompt material, but its `journal_value()` records only `{contract, revision, payload_hash}` (`inference_runner.py:26-31`). Parent input uses IDs, hashes, revisions, deadlines, and capability names only. Do not put transcript body/excerpt, prompt, streamed token, audio frame, API key, warrant, or raw plugin output in `input_snapshot`, operation arguments, refs, errors, or result refs; comply with `kernel/model.py`'s `FORBIDDEN_CONTENT_KEYS` guard. Durable domain tables keep their existing authorized meeting/plugin artifacts outside the kernel journal.

## Invariants

1. Exactly one authenticated `meeting.session` parent exists for one active live-meeting intelligence lifetime; every provider dispatch under it is one trusted `inference.invoke@1` child with one terminal receipt.
2. A closed, cancelled, expired, or revoked live parent cannot admit, claim, or publish another child; it is never revived by deferred work.
3. Every child names the plan-selected immutable deployment revision for its own capability. Missing capability is refusal, never silent retargeting.
4. Every retry/fallback that reaches a provider is a distinct child; skipped, deduped, lexical, empty, and token-only work is not.
5. Meeting artifacts and plugin results finalize only from the winning receipt and are discarded on parent cancellation; provider cancellation uncertainty is indeterminate.
6. Kernel journal content is hashes/refs/metadata only, never meeting content or audio.

## Test matrix

| Acceptance criterion / invariant | Planned focused proof |
| --- | --- |
| One authenticated live parent, frozen multi-capability plan, exact revisions | focused meeting-session admission test; v54 schema/version-pin upgrade test |
| Live calls/cardinality/no child for empty or overlapping windows | `tests/integration/test_intel_streaming.py` asserts children, plan revision, and no direct `analyze` provider seam |
| Deferred work never revives closed session; queue preserves attempts/idempotency | `tests/integration/test_meeting_intel_recovery.py` covers post-stop claim, retry/fallback children, and terminal queue state |
| Routed plugin ordering, different capability revision, dedup/skip | focused plugin-chain/queue test with two plugin capabilities and persisted idempotency key |
| Stop/interrupt/expiry/revocation fences late output | focused session/runner test: cancellation is attempted, unknown is indeterminate, and staged snapshot/plugin artifact is discarded |
| No content leaks to kernel records | focused journal scan for transcript/prompt/token/audio sentinel across parent, children, failures, and receipts |
| Real behavior | LAN live two-window plus deferred routed-plugin run; interrupt during streaming and inspect parent/children/receipts |

## Recorded notes

- **Adversarial hardening, below the bar:** per-token durable receipts, cross-process resumption of a live recording's opaque context, and unlimited automatic session extensions. The finite 12h/4,096 fence is deliberate; a concrete exhausted normal meeting should drive a bounded extension design.
- Bookmark-label and auto-title direct calls at `intel_analysis.py:172-207` and `session.py:688-699` are additional provider seams outside the charter's three named census points. They must be swept into the same live/deferred adapter during implementation if enabled, or explicitly disabled/refused; leaving them direct would violate the story's “every provider call” rule.

## Open questions for Sol

1. Ratify `meeting.session` plus separate `meeting.deferred-intel-job` parent kind, including the statement that a deferred retry is new queue authority rather than revival of a closed live session.
2. Ratify the explicit route-principal propagation and the narrow `meeting-capture` service-principal issuer; identify its canonical issuer/location or rule device-started intelligence unavailable until it exists.
3. Ratify the 12-hour/4,096 finite budget and explicit authenticated continuation rather than automatic extension.
4. Confirm stop means cancel live provider work and route any final analysis/routing through the queue-job parent, preserving eventual output without allowing a post-stop live dispatch.
5. Confirm plugin capability declaration is sufficient to freeze all provider placements at session/job admission; unknown dynamically introduced capabilities refuse rather than resolve late.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The design has the correct authority
boundary: one authenticated parent for live meeting intelligence,
lightweight trusted children for every provider dispatch, and a separate
admitted parent for post-close work. The kernel mechanics support the
claimed liveness, authority, budget, cancellation, receipt, and
publication fences.

### Amendments (binding)

1. **Change each capability entry in `MeetingIntelPlan@1` from one
   deployment revision to an ordered, immutable set of permitted primary
   and fallback deployment revisions, with every child naming the exact
   selected entry and refusing any fallback not frozen in that set.** A
   singular map cannot represent a provider-reaching fallback while
   preserving existing fallback behavior and prohibiting late placement
   resolution. Retries against the same revision remain separate children
   via invocation IDs and attempt ordinals.
2. **Make the stop-to-deferred handoff durable before `stop()` returns,
   and require the deferred job to own every displaced final provider
   seam — final analysis, bookmark refinement, auto-title, and
   provider-backed MIR/plugins — while preserving existing processing,
   ready, partial, failed, ordering, idempotency, and artifact
   outcomes.** Removing the synchronous final dispatch could otherwise
   leave an apparently completed meeting without its outputs; work may
   complete asynchronously, but durable queue state must expose that it
   remains in progress and must not report readiness early.

### Key rulings

- **Separate deferred parent RATIFIED**: a closed live parent cannot
  honestly authorize new children; each queue retry is a NEW job parent
  (a new bounded execution decision), never a reopened epoch. The
  deferred parent needs its own finite deadline/budget derived from its
  frozen work envelope (implementation detail, not unbounded).
- **Bookmark-label and auto-title seams: ABSORBED into HS-131-08.** The
  story's AC governs every actual meeting-intelligence provider call,
  not only the three named census points; leaving either direct would
  make the completion claim false. If a capability is absent from the
  frozen plan the feature is explicitly refused/disabled for the run —
  never direct, never late-resolved. HS-131-10 must not inherit these
  as unfinished implementation.
- **Principal propagation RATIFIED**: the authenticated route principal
  threads through `_start_meeting()`; autonomous device starts require a
  narrow `meeting-capture` service principal minted at the device/
  runtime authentication boundary; refusal-by-default for intelligence
  (recording itself stays available) until that issuer exists.
  Synthesizing OWNER or letting a later queue worker bypass the original
  refusal is authority elevation.
- **12h / 4,096 budget RATIFIED** with explicit authenticated
  continuation creating a NEW bounded parent + plan (causally linked,
  new authority decision); no silent renewal/epoch reset. The budget
  counts distinct admitted provider attempts, not idempotent replays.
- **Missing capability = refusal, not fallback — RATIFIED** as the only
  honest outcome; Amendment 1 makes authorized fallbacks explicit
  instead.
- **Journal hygiene RATIFIED**: hash-the-payload/journal-the-hash is
  correct; FORBIDDEN_CONTENT_KEYS is a backstop, not the defense —
  adapter errors and result refs must be deliberately sanitized, and the
  sentinel journal scan across success/refusal/failure/cancellation/
  indeterminate paths is REQUIRED proof.

### Open-question rulings

1. Yes — meeting.session + meeting.deferred-intel-job; deferred retry =
   new queue authority, never revival.
2. Yes — thread the route principal; device starts use the narrow issuer
   at the device/runtime authentication boundary; intelligence refused
   until it exists.
3. Yes — 12h / 4,096 / explicit authenticated continuation.
4. Yes, subject to Amendment 2 — stop cancels the live parent and routes
   all final provider-backed work through the deferred parent with every
   domain output and honest completion state preserved.
5. Yes, subject to Amendment 1 — declared capabilities freeze every
   permitted primary AND fallback revision; unknown capabilities refuse.

### Sol recorded notes

- No new meeting UI needed for continuation — an authenticated
  runtime/API mechanism suffices; broader UX below the bar.
- Cross-process OuterRunContext restoration, per-token receipts, and
  automatic unlimited extension remain below the bar.
- HS-131-09 may add transcription children under this session parent but
  must not weaken the principal, deadline, cancellation, or
  journal-content fences.

### Orchestrator disposition

Both amendments ADOPTED (real-use defect classes: silent-retargeting via
unfrozen fallbacks; lost/dishonestly-early meeting outputs). The
absorb ruling for bookmark/auto-title is adopted as scope: they migrate
in this story. The census-rule note for the sitting: this is Sol ruling
that intra-family seams inside a story's own AC scope are absorbed, while
cross-family findings (the Cadence get_loop call) remain HS-131-10
charter-amendment fence findings.
