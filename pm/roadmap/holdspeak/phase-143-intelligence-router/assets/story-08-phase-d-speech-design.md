# Story 08 / Phase D speech lifecycle design
**Status:** design for counsel review. **Scope:** route adoption only; no UI, new
owner control, or second inference spine.
## Decision
Phase D makes `speech.transcribe@1` the only new-work transcription authority
for standalone dictation, hold-to-talk, wake, and session transcription. It
reuses the Phase-B route-plan/controller waist, frozen deployment construction,
semantic adapter, audio-evidence rule, and unknown-dispatch law. The old
`SpeechSessionPlan` remains a v1/history reader only.
## Surface and principal map
| Surface | Principal and smallest parent | New route authority |
|---|---|---|
| Standalone speak-to-fill | authenticated **OWNER**; one short `dictation.session` per click unless it is inside an already-live browser interval | Freeze one `speech.transcribe` route with that parent. Current code already chooses the one-shot parent outside an interval and rides the interval parent inside one (`runtime/dictation_capture.py:372-408`; `speech_session/session.py:607-626`). |
| Hold-to-talk | local **OWNER**; one `dictation.session` from accepted press through release/tail, not one parent per audio function | Freeze at press; every transcription child rides it. The hold is already admitted before capture and has a bounded parent shape (`runtime/dictation_capture.py:516-524`; `speech_session/session.py:584-604`). |
| Wake | autonomous **SERVICE** `wake-capture`, never a fabricated OWNER; one bounded `wake.session` per configured wake capture | Freeze one exact `speech.transcribe` route under the existing wake authority. The current principal and parent kind are explicit (`speech_session/session.py:142-151,629-649`). |
| Meeting/session transcription | authenticated **OWNER** under the existing `meeting.session`, never a second dictation parent | Keep the Phase-B bundle member and deterministic interval operation. The routed path already uses the Meeting parent and route member (`meeting_session/transcribe_admission.py:54-144`). |
A short dictation does **not** borrow a stale global/session parent. A live open
browser interval is the sole exception: its already-admitted parent is the
smallest truthful scope (`runtime/dictation_capture.py:372-395`). Paired-device
capture is out of this slice; it retains its existing SERVICE parent shape
(`speech_session/session.py:154-195`).
### Parentless warm
The only parentless work is pre-session warming. Register closed policy
`local-model-preload@1` for SERVICE identity `local-model-preload`, operation
set `{inference.invoke@1}`, internal capability `speech.preload@1`, and
`allowed_boundaries=("local",)` (same-device deployment only). Its authority basis is the exact frozen
`speech.transcribe` deployment revision selected from the owner assignment;
it is not a Config hash, a global/group assignment, or an ambient process
identity. This is the Phase-B-ratified Phase-D ownership boundary
(`assets/story-08-phase-b-cutover-design.md:110-118`).
The present pre-session path has the right narrow SERVICE identity and only
`inference.invoke@1`, but derives its warrant from mutable model-config bytes
and resolves a legacy plan (`speech_session/session.py:198-232,930-967`).
Replace that construction with the frozen assignment/deployment evidence and
sealed policy. Follow the existing registry pattern: SERVICE is default-deny,
may use only capability assignment rows, and its policy freezes capability
revision/schema and allowed boundaries (`services/inference_service_route_policy.py:1-8,33-70,98-141`). No OWNER preload assignment row is created.
## Frozen-route contract
- Reuse the single owner-visible `speech.transcribe` assignment/profile
  migrated in Phase B; `speech.preload` is internal/nonassignable
  (`inference_capabilities.py:1058-1059`; `assets/story-08-phase-b-cutover-design.md:153-169`).
- Construct/reuse `Transcriber` only from frozen `model_name`, `backend`, and
  `language`, never a post-freeze Config read (`runtime/transcriber_state.py:64-101`).
- Reuse the closed semantic adapter: transcription returns exactly
  `{text, language}` and preload exactly `{state}` (`services/inference_semantic_adapters.py:191-204,222-255`).
- Hash the actual canonical contiguous float32 bytes after conversion, never a
  caller-provided digest. `Transcriber` currently canonicalizes then hashes
  the bytes (`transcribe.py:505-521`); `audio_sha256` hashes the supplied bytes
  themselves (`speech_session/transcription.py:33-39`).
- A timed native worker can remain alive after the caller returns
  (`transcribe.py:552-581`). Map `TranscriberTimeoutError` to
  `ProviderIndeterminate`, then terminalize `dispatch_outcome_unknown`: no
  retry and no fallback. This is the existing Phase-B Meeting adapter law
  (`meeting_session/transcribe_admission.py:155-177`).
## Authority removal and compatibility
New speech work must not call `DictationSessionPlanResolver` for transcription
or preload. Today it injects `whisper-transcribe`/`whisper-preload`, captures a
mutable-config local deployment, and returns those entries as plan authority
(`speech_session/plan.py:478-605`). `TranscriptionAdmission` then selects the
plan primary and dispatches through legacy child helpers (`speech_session/transcription.py:87-180`); the parentless warm does the same (`speech_session/session.py:930-967`). Remove those new-work branches after the speech migration marker.
Keep plan DTO/history readers. The complete remaining production consumer map
is: `SpeechSession` stores/creates the plan (`speech_session/session.py:270-351,459-581`), `TranscriptionAdmission` consumes it, generic speech-child helpers
assert it (`speech_session/child.py:126-208`), and `ProviderAdmission` still
has legacy plan fall-through while its routed branch uses the adoption service
(`speech_session/provider.py:207-303`). Phase D removes only transcription/
preload authority; Story-07 intent/rewrite routing remains on its routed branch.
New Meeting work already retains only the historical reader branch
(`meeting_session/intel_admission.py:276-278`; `meeting_session/transcribe_admission.py:248-277`).
Delete hidden MLX candidate loops as routing/attempt authority. Freeze the
bounded candidate-and-stage sequence before stage one; submit each
`model-holder` or `silent-audio` action as an explicit `speech.preload`
lifecycle operation under the selected parent/SERVICE policy. A known
no-generation stage failure may advance only to the next frozen lifecycle
stage; indeterminate, cancellation, refusal, deadline, or exhausted sequence
stops. Current nested candidate/stage loops are in `transcribe.py:224-249` and
`transcribe.py:251-277`; they must not decide new attempts. Likewise remove
feature/provider response-format compatibility ownership: current classify
keeps a feature-owned response-format leg (`speech_session/provider.py:334-339,421-469`); the frozen controller policy owns any compatible retry.
## Warm reuse
Warm stages are lifecycle, never model fallback. The loaded artifact is
reusable only when the later Meeting/dictation's frozen construction identity
matches it; Phase B clears a mismatched instance and keeps a match
(`meeting_session/intel_admission.py:255-275`). Record the warm receipt against
the frozen deployment revision. A later route may reuse that artifact without a
second load only after this identity/receipt check; otherwise it runs its own
bounded lifecycle sequence. No preload result appears in an owner assignment.
## Two slices and focused proof
1. **Route all live speech transcription.** Cut standalone, hold, wake, and
   remaining session paths to frozen `speech.transcribe`; retain product output
   and legacy history readers. Add focused coverage in
   `tests/unit/test_transcribe_route.py`, `tests/unit/test_transcribe_timeout.py`,
   `tests/unit/test_dictation_session_admission.py`,
   `tests/unit/test_speech_side_door_admission.py`, and the Phase-B Meeting
   route tests. Prove parent shape, assignment edit after freeze, exact semantic
   output, actual-byte SHA (including forged caller SHA), and timeout unknown
   with zero second attempt/fallback. Product boundary: legacy execution stays
   readable; every new entry either transcribes through the route or refuses
   before audio/model dispatch.
2. **Cut pre-session warm.** Add `local-model-preload@1`, replace legacy plan
   warm admission, and flatten frozen lifecycle stages. Cover closed SERVICE
   policy, no group/global inheritance, no owner preload row, local-boundary
   refusal, frozen deployment-revision mismatch, stage bounds, unknown-stop,
   and later identity-match reuse in
   `tests/unit/test_dictation_session_admission.py`,
   `tests/unit/test_transcriber_init_race.py`, and a new focused
   `tests/unit/test_phase143_speech_lifecycle_adoption.py`. Product boundary:
   a denied/failed warm defers to the first lawful transcription; dictation
   capture itself never becomes unavailable because warming was denied.
## Open questions for counsel
1. Does `ServiceRoutePolicyDefinition.authority_basis` need a bounded
   deployment-revision parameter form, or a fixed policy basis plus an exact
   revision cross-bind in frozen evidence? Its current lookup key is exact
   string equality (`services/inference_service_route_policy.py:81-95,110-123`).
2. Ratify one explicit lifecycle operation per candidate/stage versus retaining
   Phase-B's Meeting-only single bounded sequence; Phase D's stated hidden-loop
   removal favors the former.
3. Must warm reuse compare the deployment-revision ID in addition to the
   current backend/model/language construction match
   (`meeting_session/intel_admission.py:255-272`)?

---

# Counsel ruling (Sol, 2026-08-23): RATIFY-WITH-AMENDMENTS

The six amendments below are the counsel's exact required text and are
binding over any conflicting statement above. Open-question rulings:
(1) authority basis = fixed exact string `local-model-preload:assigned-speech-route`
+ immutable evidence cross-bind (no parameterized matching);
(2) ONE bounded P=1 preload sequence — the per-candidate/stage operation
language above (lines 69-76) is SUPERSEDED;
(3) warm reuse requires deployment-revision ID + durable receipt, not just
backend/model/language. Implementation is blocked until these amendments
are incorporated (they now are, by this appendix).

## Counsel amendments

### 1. Atomic speech parent and route authority

For every new-work non-Meeting speech session, persist the existing
capture parent and its complete frozen route manifest atomically through
the parent-route-bundle transaction seam. Standalone one-shot, browser
interval, and hold parents freeze `speech.transcribe@1` under the
authenticated OWNER at admission. Wake freezes `speech.transcribe@1`
under the `wake-capture` SERVICE principal at wake-session admission. A
one-shot inside an already-live browser interval reuses that interval's
frozen route member; it does not freeze a second route or admit a second
parent. Meeting keeps its existing Phase-B `meeting.session` bundle
member unchanged.

No path may persist a usable parent and later attach transcription
authority through a separate partial binding. New-work transcription
uses the frozen route member, while `SpeechSessionPlan` remains live only
for historical transcription reconstruction and provider capabilities
outside this Phase-D cutover.

### 2. Closed SERVICE policies and derived parentless preload

Do not add parameterized authority-basis matching. Register
`local-model-preload@1` with SERVICE identity `local-model-preload`,
exact authority basis
`local-model-preload:assigned-speech-route`, policy context
`local-model-preload`, operation set `{inference.invoke@1}`, internal
execution capability `speech.preload@1`, capability-only assignment
source, and `allowed_boundaries=("local",)`.

In one transaction, resolve and freeze the exact owner-visible
`speech.transcribe` capability assignment selected for the warm, then
derive the nonassignable `speech.preload` route from that frozen source
route using the existing derived-preload contract. Frozen evidence
cross-binds the source assignment identity and revision, transcription
route ID and SHA, deployment-revision ID, engine, model artifact,
candidate sequence, and lifecycle-stage sequence. No
`speech.preload` assignment row is read or created, and mutable
ModelConfig bytes provide no post-migration execution authority.

Register a closed `wake-capture@1` SERVICE route policy as well. Use
exact authority basis `wake-capture:configured-capture`; cross-bind the
configured wake revision in immutable parent and principal evidence
rather than placing an arbitrary revision suffix in the registry lookup
key. The policy names the existing wake operation set,
`speech.transcribe@1`, capability-only assignment lookup, and only the
boundaries that `speech.transcribe@1` permits. No OWNER principal is
synthesized.

### 3. One bounded P=1 preload sequence

This amendment supersedes the per-candidate/per-stage operation language
above. One warm attempt is one `speech.preload@1` lifecycle operation
with P=1. Before that operation begins, freeze the complete ordered
candidate list, ordered stage list (`model-holder`, `silent-audio`), and
stop rules in route evidence.

The adapter may walk only that frozen sequence. It checks cancellation
before every physical call; advances only after a known caught
no-generation stage failure; returns immediately on success; and stops
on cancellation, refusal, deadline, indeterminate physical disposition,
or exhaustion. No later physical call may begin after a stop condition.
Runtime code may not rediscover, reorder, append, or substitute
candidates or stages. Internal candidate/stage iteration is lifecycle
execution, not routing or fallback authority, and does not mint one
kernel operation per stage.

### 4. Deployment-revision-bound warm reuse

A later transcription may reuse a loaded artifact only when all of the
following match its frozen route: deployment-revision ID, backend,
model, and normalized language. Reuse also requires a durable successful
preload/load receipt cross-bound to that deployment revision.

Store the deployment-revision ID with the loaded runtime state and its
receipt provenance. A runtime with missing revision provenance, a
different revision ID, or no durable successful receipt is not reusable
even when backend/model/language strings match; clear or replace it and
run the later route's own bounded lifecycle sequence.

### 5. Binding Slice-1 day-one standalone continuity

Slice 1 must include a production-path continuity test for standalone
speak-to-fill. Starting from a fresh database and the owner's migrated
saved local speech selector, including `backend=auto`, run the real
migration/startup path and perform the first standalone speak-to-fill
transcription through its short `dictation.session`.

The test must prove: one visible `speech.transcribe` profile and
assignment; no `speech.preload` assignment; deterministic `auto`
resolution; no manual profile, assignment, or readiness repair; one
bounded P=1 preload when the selected artifact is not already loaded;
successful routed transcript output; a successful
`speech.transcribe` route receipt; and readiness updated only after the
successful admitted load. A denied or failed pre-session warm does not
disable capture: the first lawful transcription may perform the same
bounded warm.

### 6. Complete consumer, compatibility, and egress cutover

Replace the claim that `SpeechSessionPlan` is globally history-only with
the narrower rule that it no longer authorizes new-work transcription or
preload. Inventory and preserve its remaining live consumers, including
CLI egress output, dictation runtime target construction, web dictation
egress, entry-admission validation, `SpeechEntry`, and provider
classify/rewrite/punctuate behavior not migrated by Phase D.

Paired-device capture remains out of Phase D adoption and therefore
retains its existing SERVICE principal, `dictation.session`, and legacy
transcription authority. Add a focused non-regression fence proving the
speech migration marker does not strand that path. Do not add a
`device-capture` route policy as an incidental scope expansion.

For every migrated speech surface, derive transcription egress from the
frozen `speech.transcribe` route rather than from a missing-plan
`local` default. When transcription is followed by provider-backed
dictation stages, report the widest boundary across the frozen
transcription and provider routes. Focused tests must cover local, mesh,
and private-network transcription and prove that none is mislabeled
`local`.

---

# Counsel ruling round 2 (Sol, 2026-08-24): five blocked-item rulings

Full record with required proofs: `story-08-phase-d-counsel.md`
(brief: `story-08-phase-d-rulings-brief.md`). The amendment texts below
are counsel's exact words and are binding over any conflicting
statement above, including amendments 1–6 where explicitly superseded.

### 7. Local-only speech execution (rules R1)

In Slice 1, `speech.transcribe@1` and its derived `speech.preload@1`
lifecycle are same-device capabilities with
`allowed_boundaries=("local",)`. Every SERVICE policy that authorizes
either capability repeats that boundary. A `speech.transcribe`
assignment containing a `mesh` or `private_network` leg is refused
during route admission before transcriber construction or audio/model
dispatch; it is never executed locally under the remote deployment
identity.

Amendment 6's final sentence is replaced with: "Focused tests must
prove that successful transcription is badged `local`, and that mesh
and private-network transcription routes are refused at admission with
no dispatch and no false `local` receipt. Remote speech execution
remains future work until an explicit audio transport and semantic
adapter exist."

### 8. Cold wake lifecycle (rules R2)

`wake-capture@1` authorizes exactly `speech.transcribe@1` and the
nonassignable derived `speech.preload@1` lifecycle member, with
capability-only assignment lookup and `allowed_boundaries=("local",)`.
In the same transaction that admits the `wake.session` parent and
freezes its transcription route, derive exactly one P=1 preload member
from that frozen route using the existing derived-preload contract. Its
deployment revision, candidate sequence, stage sequence, and stop rules
come only from the frozen transcription evidence. No `speech.preload`
assignment is read or created, and no OWNER principal is synthesized.

### 9. Configured wake revision binding (rules R3; supersedes part of amendment 2)

Cross-bind `wake_capture_revision` in the immutable `wake.session`
parent input snapshot. Do not add that value to
`InferenceFeaturePrincipalPolicyEvidence@1`. Principal evidence instead
binds the exact `wake-capture@1` policy identity, policy revision and
SHA, `wake-capture` SERVICE identity,
`wake-capture:configured-capture` authority basis, and `wake.session`
parent kind. This supersedes Amendment 2's requirement to duplicate the
configured wake revision in principal evidence.

### 10. Coupled non-Meeting speech cutover (rules R4)

Activate the Phase-D speech parent-route bundle only when both
`speech-recognition-route-assignments` and
`thoughts-writing-route-assignments` migration markers are present. If
either marker is absent, retain the complete legacy session path for
that parent. Once both markers are present, `SpeechSessionPlan` no
longer authorizes transcription or preload, and every configured routed
classify/rewrite capability is frozen as a member of the same bundle as
`speech.transcribe`. A single parent may not combine a bundled speech
member with a plain legacy provider child.

### 11. Faster-whisper constructor exception (rules R5)

Amendment 3 governs separable MLX lifecycle loading. Faster-whisper is
a local-only, constructor-inseparable exception: `WhisperModel(...)`
may construct and load from the frozen backend, model, and language
after the capture parent and complete frozen speech route have been
admitted but before the `speech.transcribe` child is claimed.
Constructor work may not select or advance a route leg, dispatch audio,
or mint a preload or transcription receipt. The subsequent audio
invocation remains authorized only inside the routed
`speech.transcribe` child. Slice 1 does not wrap faster-whisper
construction in `speech.preload@1`; the constructor seam is retained as
a ledger note.
