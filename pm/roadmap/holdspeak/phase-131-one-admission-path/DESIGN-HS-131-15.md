# HS-131-15 design — Speech side doors become admitted one-shot sessions

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-13) — the seven amendments in the Sol ruling below are binding on implementation
**Decision boundary:** the browser and CLI dry-runs retain the full configured DictationPipeline. Each provider-bearing invocation opens one fresh, short, credential-authenticated `dictation.session` before runtime construction; every physical provider attempt is one exact-revision `inference.invoke@1` child. An intentionally LLM-disabled configuration may remain lexical and mints no inference child. Missing authentication, admission, liveness, or exact revision is a named fatal refusal, never a lexical fallback.

## Context and constitutional test

The current browser helper and `holdspeak dictation dry-run` each call
`build_pipeline` without HS-131-09's speech-session admission. The shared browser
helper is also used by remote dictation, journal replay, and block-template
preview, so fixing only the named `/api/dictation/dry-run` decorator would leave
the same executable door reachable through another route.

`WFS-CFG-005` requires the browser dry-run to run the **full** DictationPipeline,
and `DIR-F-010` requires the CLI dry-run to do the same and print each stage
result. Retaining provider work therefore preserves source canon; it also requires
admission under Articles V.2–4 and XI.1–3. Topology (`asyncio.to_thread`, local
CLI, local model) grants no exemption. Article III.2 requires egress disclosure
from the admitted frozen plan before the CLI constructs or warms a provider and
at the existing browser decision badge.

The owner's yolo-mode rigor bar controls the review: repair realistic races,
crashes, silent retargeting, dishonest receipts, and late writes. Forced native
termination, cross-store crash atomicity, and attacker-with-owner-process
hardening remain recorded notes rather than owner friction.

## 1. Entry-point rulings

| Entry | Ruling | Principal and authority | Parent / lifetime | Publication owner |
| --- | --- | --- | --- | --- |
| `POST /api/dictation/dry-run` | **ADMIT** the full configured pipeline | `request.state.principal`, installed by credential middleware; never payload data, loopback location, or synthesized owner. | One fresh `dictation.session`, aim `browser-rehearse`, 90-second deadline, 12-child budget, synthetic-text capabilities only. Disconnect/cancel/expiry/revocation closes it. | Route owns JSON, suggestions, and application-journal output. Each model-derived publication goes through the session election. |
| `POST /api/dictation/journal/{id}/replay` | **ADMIT** | Middleware principal; add `Request`. | Fresh short session, aim `journal-replay`; never an open-mic parent. Run helper off-loop. | Route owns the replay response; disconnect cancels and discards. |
| `POST /api/dictation/blocks/from-template?dry_run=true` | **ADMIT preview only** | Middleware principal; add `Request`. | Fresh short session, aim `template-preview`; run helper off-loop. The earlier block creation is a separate completed effect. | If preview fails after block creation, return “created” plus a named preview failure; never imply rollback. |
| `POST /api/dictation/remote` non-raw processing | **ADMIT** | The middleware principal already used for the delivery claim. | Fresh session, aim `remote-delivery`, enclosing provider work through the final pre-delivery gate. It never borrows open-mic authority. | The accepted idempotent send is committed work: HTTP disconnect does **not** revoke it. It continues to a terminal delivery claim or honest indeterminate state. Explicit expiry/revocation before the effect gate prevents delivery. |
| `holdspeak dictation dry-run` | **ADMIT when provider-backed; intentional LLM-disabled mode remains lexical** | The top-level CLI obtains a hub-issued owner credential and asks the centralized authenticator to derive the principal. It may not mint `Principal(OWNER)`, call `hold_gesture_principal`, infer from UID/TTY/loopback/process location, or accept `--principal`. Missing credential refuses before provider construction. | One fresh `dictation.session`, aim `cli-dry-run`, 90 seconds / 12 children, synthetic-text capabilities only. `KeyboardInterrupt`, failure, expiry, or revocation terminally closes it. | Print one concise frozen-plan egress line before provider construction; buffer all stage/result text and publish only through the live session election. No keyboard effect. |

The CLI's provided credential is the established `HOLDSPEAK_TOKEN` bearer; the
expected side is the hub's configured `meeting.web_auth_token`. Production
dispatch passes those distinct sides through the same central owner derivation
used at the web edge. There is no config-token fallback on the provided side. A
standalone command with no valid credential refuses by name; it does not issue
itself a credential merely to run.

## 2. Freeze once; construct only from the plan

1. Load one full `Config` object and one deployment-registry snapshot.
2. Derive the provider capabilities from the methods that physically run:
   - `intent-classify` for the configured intent-router stage;
   - `rewrite` for project rewriting;
   - `rewrite` for `target_detect_llm_enabled`, because
     `apply_model_assisted_target` calls `runtime.rewrite`;
   - provider punctuation only when a provider-backed punctuation stage exists.
   Synthetic text never plans Whisper transcription or preload.
3. Admit one finite `dictation.session` with the explicit principal, entry aim,
   deadline, child budget, config/registry snapshots, and those capabilities.
   `DictationSessionPlanResolver` freezes each capability's ordered deployment
   revisions, authority/config hashes, and egress boundary.
4. Validate the live admission and every required planned capability before
   `_try_build_runtime`; only then call `build_pipeline(..., admission=...)`.
   `admission=None` can never construct or return a model-bearing runtime.
5. Runtime construction, including warm-on-start, uses the frozen deployment
   revision (or the exact immutable registry resolution already admitted). It may
   not independently re-run current placement and then hope revision rebinding
   corrects dispatch later.
6. The existing speech provider/revision adapter performs physical calls.
   Classify, response-format compatibility, classifier retry, rewrite passes,
   future provider punctuation, local/cloud, and mesh are each separate children
   when they physically attempt work. No route- or CLI-specific provider adapter
   is introduced.

An intentionally disabled pipeline executes its declared lexical behavior, names
provider stages as skipped, constructs no runtime, and creates zero inference
children. Runtime unavailability may remain a named visible limitation only when
no provider object or physical attempt was created; authentication/admission/
revision failure may never be mapped onto that state.

## 3. Shared helper and fatal speech channel

`_run_dictation_dry_run_text` takes the caller's exact config snapshot, explicit
live session/provider admission, and publication fence as required keyword-only
inputs. It accepts no principal, parent ID, warrant, placement, client profile,
or caller-supplied revision. All four production callers open and own their fresh
route session; none joins a browser open-mic interval or self-mints inside the
helper.

The helper checks the fence before construction, before pipeline work, after each
provider-bearing continuation, and before candidate publication. The pipeline
must distinguish fatal speech signals from ordinary stage failures:

- `SpeechSessionRefused`, `SpeechProviderFailure`, exact-revision mismatch,
  expiry/revocation, and child-budget refusal propagate unchanged to the parent;
- `DictationPipeline.run` and model-assisted target detection re-raise those
  signals before broad `except Exception` degradation;
- the kernel's safe refusal reason is preserved instead of rewriting every
  refusal to `speech_provider_fenced`;
- DIR-F-003 remains for ordinary plugin/stage failures only, explicitly marked
  degraded rather than mistaken for provider success.

This closes the current quiet-raw-text path where a session refusal is caught,
`current_text` resets to the utterance, and a successful response/journal row
lands. The target-profile heuristic likewise cannot hide a missing `rewrite`
capability.

The client-supplied `profile_id` remains non-authoritative. Placement comes only
from the frozen plan; this story must not “fix” the currently ignored field into
a client-chosen deployment.

## 4. Cancellation, terminal ownership, and publication election

### One terminal owner

Once admission succeeds, one `try/finally` owner is responsible for an honest
terminal parent outcome on success, refusal, provider failure, cancellation,
expiry, and every escaped exception. Session close/cancel persistence failure is
not swallowed as `""`; it surfaces as indeterminate. Every blocking helper call
runs off the event loop so a mesh relay can continue serving claim polls.

### Atomic publication gate

Extend `SessionFence` with one lock-protected publication permit/callback. The
same local election guards cancellation and model-derived publication:

1. acquire the fence lock;
2. recheck local cancellation and durable deadline/revocation/liveness;
3. if live, admit the bounded callback while holding the election;
4. otherwise refuse/discard without the callback.

If publication wins, it precedes cancellation; if cancellation wins, no later
response, suggestion, application-journal row, replay result, buffered stdout,
or pre-delivery handoff occurs. The content-free telemetry ring may remain an
explicitly recorded observation only if it contains no utterance/result body;
otherwise it joins the publication gate. Do not add a runner-level post-dispatch
parent check.

### Preview versus committed send

Dry-run, journal replay, and template preview are cancellable computations; a
disconnect cancels their session and suppresses model-derived output. Remote
delivery changes authority lifetime once its idempotency claim is accepted: a
phone disconnect is not revocation of the user's committed send. The work is
shielded/transferred until the terminal delivery claim, while explicit session
expiry/revocation before the delivery gate still refuses. After the effect gate
wins, the existing delivery operation/receipt owns the typing effect.

Template block persistence is likewise independent. A preview refusal after a
successful block write returns the created block plus a named preview failure so
a retry cannot duplicate or falsely “undo” the completed write.

### Existing live dictation gap

`runtime/dictation_capture.py` checks its fence, calls
`text_processor.process(text)`, then can enter `_maybe_dispatch_voice_command`
without another election. Add the same publication/effect election immediately
after text processing and immediately before voice-command dispatch. A
cancellation winner discards and returns; it is not an ordinary unmatched command.

## 5. Terminal outcomes and journal hygiene

- Success: all physical children have immutable terminal receipts; publication
  wins while the session is live; parent closes succeeded exactly once.
- Named pre-dispatch refusal/provider failure: the admitted child (when one
  exists) ends honestly refused/failed; no successful model-derived publication;
  parent ends failed/refused.
- Disconnect for a cancellable preview, command interrupt, expiry, revocation, or
  explicit cancellation: parent closes by the existing named outcome; new
  children refuse and late publication loses the election.
- Remote disconnect after accepted delivery claim: work continues to terminal
  success/failure/indeterminate; it is not silently cancelled.
- No provider capability selected: lexical execution creates zero inference
  children but still has finite entry ownership where the route/command needs its
  publication fence.

Kernel operation/event/receipt fields contain only IDs, capabilities, hashes,
exact revisions/destinations, ordinals, timing/counts, authority basis, and fixed
safe reason classes. Audio, dictated/input text, block templates, prompts,
completions, token streams, rewritten text, credentials, warrants, and raw
provider exceptions stay outside kernel rows. Existing application stores retain
product content only through their publication owner/election.

## 6. Invariants

1. Every provider-bearing browser/CLI entry has a credential-authenticated finite
   parent and frozen plan before construction.
2. Provider construction without a real live admission or required exact revision
   refuses; no authentication/admission failure becomes lexical success.
3. Every physical provider attempt has exactly one `inference.invoke@1` child and
   one immutable terminal receipt under the entry parent.
4. Intentionally lexical configuration constructs no runtime and mints no child.
5. Config/registry mutation after admission cannot retarget construction, warmup,
   dispatch, egress disclosure, or publication.
6. Cancellation and model-derived publication share one election; no output lands
   after cancellation wins.
7. Synthetic text sessions never consume Whisper/open-mic authority.
8. Speech admission never substitutes for the separate keyboard/delivery effect
   operation.
9. Kernel rows remain content-free.

## 7. Focused proof matrix

| Contract | Required proof |
| --- | --- |
| Browser authority/session | All four provider-bearing HTTP paths derive `request.state.principal`; missing/none principal refuses before construction; payload principal/parent/profile fields cannot select authority or placement. |
| CLI authentication/egress | Valid hub credential derives owner through the centralized authenticator; absent/invalid token refuses; forbidden synthetic owner helpers are unreachable; frozen-plan egress prints before runtime construction/warmup. |
| Frozen construction | One config + registry snapshot; mutate both after admission and prove construction/dispatch/egress stay on planned revision. Target-detection-only plan includes `rewrite`. |
| Shared-helper closure | Dry-run, remote, replay, and template callers pass a fresh session; missing/duck-typed/ended/cross-session/open-mic values refuse. |
| Fatal channel | Pipeline and target detector propagate speech refusal/failure/expiry/revision/budget signals; ordinary stage failures retain explicit degraded behavior. |
| Cardinality | Success, provider failure, compatibility/classifier retry, rewrite passes, mesh/local/cloud prove physical attempts = dispatched children = terminal receipts for the dispatched cohort. |
| Lexical control | Intentionally disabled provider config never enters runtime factory and creates zero inference children. |
| Cancellation/publication | Exercise both sides of the atomic gate for response, suggestion, journal, replay, buffered stdout, and pre-delivery handoff; preview disconnect discards; remote disconnect after claim completes the terminal idempotency record. |
| Terminal cleanup | Every exception path closes; close persistence failure surfaces indeterminate; no 90-second zombie parent. |
| Template honesty/event loop | Mesh-backed replay/template runs off-loop; created block + preview failure reports both truths and does not duplicate. |
| Voice-command gap | Cancel after `text_processor.process` and before `_maybe_dispatch_voice_command`; prove zero connector/typing effect. |
| Hygiene | Scan parent, child, event, receipt, refusal, failure, cancellation, retry, and indeterminate rows for unique content/credential sentinels. |
| Fence mutation | In disposable edits, restore each bare production `build_pipeline` call and prove exact `dictation-dry-run` / `dictation-command` fence failure, then restore green. |
| Census | Remove both findings, add no product scope to `ADAPTER_ALLOWLIST`, preserve zero unregistered sites. |

Focused integration executes browser and CLI production entrances under isolated
HOME with one retained provider capability and inspects parent, child, revision,
receipt, egress, and publication rows. HS-131-12 owns the assembled real-mic walk;
this story's real hub/model proof must still be traceably present before closeout.

## Recorded notes

- Forced termination of an already-running uninterruptible MLX/llama call remains
  below the owner's bar. Honest indeterminate child outcome plus publication
  fencing is sufficient.
- A process crash between an external content-store write and parent terminal
  receipt remains a cross-store reconciliation concern. Ordinary exceptions and
  in-process races are not excused by that note.
- Hardening internal Python helpers against an attacker already controlling the
  owner process remains out of scope. Ordinary automation/agent invocation is why
  CLI authentication cannot be fabricated.
- A dedicated `dictation.preview` parent kind, preview idempotency key, and forced
  native-call termination are not required by this story.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The full browser and CLI behaviors may remain,
but the draft's unproved CLI owner boundary, mutable construction, swallowed
refusals, shared cancellation semantics, and check-then-write fence were blockers.

### Binding amendments

1. **Authenticate CLI through a hub-issued credential and centralized owner
   derivation.** Never infer or mint owner identity locally. Missing credential
   refuses before provider construction; intentional LLM-disabled behavior alone
   may stay lexical.
2. **Freeze once and construct from that exact plan.** One config/registry
   snapshot, required capability validation before runtime construction, frozen
   target for warmup/dispatch, and `rewrite` (not classify) for model-assisted
   target detection.
3. **Create a fatal speech-failure channel.** Session/provider/refusal/revision/
   expiry/budget signals escape broad stage/target catches, preserve their safe
   reasons, and cannot become raw-text/heuristic success.
4. **Give every invocation a fresh owner and guaranteed terminal cleanup.** No
   open-mic borrowing; every blocking route helper is off-loop; every admitted
   parent has one non-swallowing terminal owner.
5. **Separate cancellable previews from committed effects.** Preview disconnect
   discards; accepted remote send continues; explicit pre-effect expiry/revocation
   refuses; template creation and preview report their independent outcomes.
6. **Implement a real publication election and close the live-command gap.** One
   lock-protected fence decides cancellation versus publication/effect handoff,
   including the post-processing voice-command interval.
7. **Derive egress and proof from the frozen plan.** Disclose CLI egress before
   construction; badge/disclosure cannot read mutable placement; hostile proof
   covers authentication, retargeting, fatal propagation, terminality, mesh
   off-loop behavior, both race orders, remote/template truth, hygiene, and census.

### Orchestrator disposition

All seven amendments are ADOPTED. They address realistic ordinary callers and
failure modes under the owner's yolo bar. The Plan survey's permanently lexical
CLI alternative is not selected because DIR-F-010 still requires the full
configured pipeline; credential absence produces a named refusal rather than a
fabricated owner or a silent behavior downgrade.
