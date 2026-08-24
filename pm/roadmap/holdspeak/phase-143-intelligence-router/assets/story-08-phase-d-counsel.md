# Counsel record — Phase D slice 1 ruling round (HS-143-08)

Sol counsel, 2026-08-24. ONE capped ruling round on the five blocked
items in `story-08-phase-d-rulings-brief.md` (facts verified against the
current tree the same day). Verbatim record below; orchestrator
dispositions at the end. Verdict: **RATIFY-WITH-NOTES** conditions set —
one fix round, then ship.

---

**OWNER'S BAR:** HoldSpeak always runs YOLO mode; a finding counts only
when a normal product action reproduces damage. Crash-window,
sleep-resume, takeover-race, and adversarial scenarios are ledger notes
by default even when a probe reproduces them. Counsel is capped at this
one ruling round and at most one fix round, then RATIFY-WITH-NOTES and
ship—the five-round C1 loop is the never-again example. This is one
owner's laptop: migrations stay minimal, and there is no
backwards-compatibility ceremony.

**Read:** the rulings brief, the Phase D speech design, and the cited
production seams for route execution, bundle admission, SERVICE policy
evidence, marker cutover, and both transcriber backends.

## R1 — Mesh/private-network speech execution

**RULING — option (a):** Scope speech transcription to local execution
now. There is no remote-audio transport or remote transcription adapter
in Slice 1, so advertising mesh or private-network execution would be
false authority and risks a false receipt. `speech.transcribe@1` and its
derived lifecycle capability are local-only; owner and SERVICE route
admission must refuse any assignment containing a non-local speech leg
before transcriber construction or audio/model dispatch. Remote speech
transport is a ledgered future capability, not Slice-1 work.

**BINDING AMENDMENT TEXT:**

> **Local-only speech execution.** In Slice 1, `speech.transcribe@1`
> and its derived `speech.preload@1` lifecycle are same-device
> capabilities with `allowed_boundaries=("local",)`. Every SERVICE
> policy that authorizes either capability repeats that boundary. A
> `speech.transcribe` assignment containing a `mesh` or
> `private_network` leg is refused during route admission before
> transcriber construction or audio/model dispatch; it is never
> executed locally under the remote deployment identity.
>
> Amendment 6's final sentence is replaced with: "Focused tests must
> prove that successful transcription is badged `local`, and that mesh
> and private-network transcription routes are refused at admission
> with no dispatch and no false `local` receipt. Remote speech
> execution remains future work until an explicit audio transport and
> semantic adapter exist."

**REQUIRED PROOF:** Focused production-object tests must show one
ordinary local speech action completing through the real
migration/profile/assignment, parent-bundle, controller,
semantic-adapter, and receipt path with `local` egress; then
parameterized mesh and private-network assignments must each refuse
during real route admission with no transcriber construction, route
execution, physical backend call, or misleading receipt. Do not use
hand-built route plans, decorated admissions, or fake controllers.

## R2 — Cold MLX wake capture

**RULING — option (i):** Extend `wake-capture@1` narrowly with the same
nonassignable derived preload lifecycle already used by owner speech.
Cold MLX wake is a normal product action and presently fails, so it
cannot be ledgered away or replaced with an honest-but-broken cold
refusal. Wake admission must atomically freeze transcription and derive
exactly one P=1 preload member from that route; it remains a SERVICE
session and creates no OWNER or preload assignment.

**BINDING AMENDMENT TEXT:**

> **Cold wake lifecycle.** `wake-capture@1` authorizes exactly
> `speech.transcribe@1` and the nonassignable derived `speech.preload@1`
> lifecycle member, with capability-only assignment lookup and
> `allowed_boundaries=("local",)`. In the same transaction that admits
> the `wake.session` parent and freezes its transcription route, derive
> exactly one P=1 preload member from that frozen route using the
> existing derived-preload contract. Its deployment revision, candidate
> sequence, stage sequence, and stop rules come only from the frozen
> transcription evidence. No `speech.preload` assignment is read or
> created, and no OWNER principal is synthesized.

**REQUIRED PROOF:** A focused cold-path test must use the production
`Database`, broker, `SpeechSession`, parent-route bundle, controller,
routed admission, and a normally constructed production
`Transcriber`/`_MlxTranscriber` whose initial `loaded` state is false.
It must not use `Transcriber.__new__`, a subclass that bypasses
`_MlxTranscriber.__init__`, a `loaded=True` backend fake, or a
decorated admission. Only the external MLX physical boundary may be
bounded for the test. The ordinary wake action must produce one
`wake-capture` SERVICE parent, bundled `speech.transcribe` plus derived
`speech.preload`, exactly one P=1 preload execution before
transcription, a successful routed transcript and receipts, and no
OWNER or preload assignment.

## R3 — Configured wake revision evidence

**RULING — option (a):** Narrow Amendment 2. The configured wake
revision is already durably cross-bound in the immutable parent
snapshot, which is the evidence describing what this particular wake
session was configured to do. The closed principal evidence describes
who and under which fixed policy the route may execute; its existing
exact policy identity, revision, SHA, SERVICE identity, authority
basis, and parent kind are sufficient. Do not widen the generic schema
or mint a wake-only v2 merely to duplicate one immutable parent fact.

**BINDING AMENDMENT TEXT:**

> **Configured wake revision binding.** Cross-bind
> `wake_capture_revision` in the immutable `wake.session` parent input
> snapshot. Do not add that value to
> `InferenceFeaturePrincipalPolicyEvidence@1`. Principal evidence
> instead binds the exact `wake-capture@1` policy identity, policy
> revision and SHA, `wake-capture` SERVICE identity,
> `wake-capture:configured-capture` authority basis, and `wake.session`
> parent kind. This supersedes Amendment 2's requirement to duplicate
> the configured wake revision in principal evidence.

**REQUIRED PROOF:** Using production wake admission and route
reconstruction, a focused test must show that the persisted parent
snapshot contains the exact `wake_config_revision` for the active
configuration, that an ordinary configuration change produces a
different persisted revision on the next session, and that both routes
reconstruct successfully under the unchanged exact
`InferenceFeaturePrincipalPolicyEvidence@1` schema with the closed
`wake-capture@1` identity. No optional field, schema v2, hand-built
evidence, or decorated policy object is permitted.

## R4 — Partial marker cutover

**RULING — couple the cutover:** A parent must not mix bundled
transcription authority with legacy plain provider children. The
smallest honest fix is one cutover condition: non-Meeting Phase-D
speech routing activates only when both speech-recognition and
thoughts/writing migration markers are present. A partial-marker
installation remains wholly on the existing legacy session path; once
both markers exist, transcription and every configured routed
classify/rewrite member freeze into the same bundle. This preserves
ordinary pipeline behavior without inventing a new capacity mechanism
or expanding provider migration scope.

**BINDING AMENDMENT TEXT:**

> **Coupled non-Meeting speech cutover.** Activate the Phase-D speech
> parent-route bundle only when both
> `speech-recognition-route-assignments` and
> `thoughts-writing-route-assignments` migration markers are present.
> If either marker is absent, retain the complete legacy session path
> for that parent. Once both markers are present, `SpeechSessionPlan`
> no longer authorizes transcription or preload, and every configured
> routed classify/rewrite capability is frozen as a member of the same
> bundle as `speech.transcribe`. A single parent may not combine a
> bundled speech member with a plain legacy provider child.

**REQUIRED PROOF:** Focused production-object tests must exercise the
normal configured dictation pipeline in both relevant states. With only
the speech marker present, the real session must remain wholly legacy,
complete configured classify/rewrite behavior, create no route bundle,
and suffer no child-capacity loss. With both markers present, the real
session must freeze transcription and all configured routed provider
members into one bundle, execute the ordinary pipeline successfully
within its existing parent budget, and create no plain legacy provider
child under that parent. No synthetic session shell, decorated provider
admission, or fake bundle is proof.

## R5 — Faster-whisper constructor load

**RULING — option (a):** Ratify a narrow local-only exception.
Faster-whisper's library API makes model construction and loading
inseparable, while Slice 1's governed audio invocation remains
separable. Reworking that library boundary into a fictional preload
operation would reopen Amendment 3 without improving the ordinary
product path. Construction may therefore occur after the parent and
frozen local speech route exist but before the transcription child; it
may not select another route, claim a lifecycle receipt, or move the
audio invocation outside the routed transcription child. Record the
constructor seam as a ledger note and ship.

**BINDING AMENDMENT TEXT:**

> **Faster-whisper constructor exception.** Amendment 3 governs
> separable MLX lifecycle loading. Faster-whisper is a local-only,
> constructor-inseparable exception: `WhisperModel(...)` may construct
> and load from the frozen backend, model, and language after the
> capture parent and complete frozen speech route have been admitted
> but before the `speech.transcribe` child is claimed. Constructor work
> may not select or advance a route leg, dispatch audio, or mint a
> preload or transcription receipt. The subsequent audio invocation
> remains authorized only inside the routed `speech.transcribe` child.
> Slice 1 does not wrap faster-whisper construction in
> `speech.preload@1`; the constructor seam is retained as a ledger
> note.

**REQUIRED PROOF:** One focused ordinary faster-whisper action must use
production session, bundle, transcriber-state, `Transcriber`,
controller, and receipt objects. It must show that the parent and local
frozen route exist before production transcriber construction, that
construction receives only the frozen backend/model/language, that no
inference child or route execution is claimed by construction, and that
the subsequent audio call creates exactly one routed `speech.transcribe`
execution with a successful transcript receipt and `local` egress. Do
not assemble a transcriber with `__new__`, substitute a decorated
admission, or use a fake HoldSpeak controller.

**RATIFY-WITH-NOTES:** The one and only fix round must implement the
five amendments above, add the specified focused production-object
proofs, and ledger only the deferred remote speech transport plus the
faster-whisper constructor exception; after that, there is no further
counsel round—ship.

---

## Orchestrator dispositions (2026-08-24)

- **R1-R5 ACCEPTED as ruled.** All five match the brief's verified
  facts; R1/R3/R5 follow the orchestrator's recommendations, R2 chose
  the recommended option (i), R4 chose coupling (the stricter of the
  two options offered — accepted, it removes the mixed-parent state
  entirely instead of guarding it).
- Marker names in R4's amendment verified real in the current tree
  (`speech-recognition-route-assignments`,
  `thoughts-writing-route-assignments` — used across
  speech_session/session.py, plan.py, services/*).
- The five binding amendment texts are appended verbatim to
  `story-08-phase-d-speech-design.md` as amendments 7–11.
- Ledger entries opened by this ruling: (1) remote speech
  transport/adapter — future capability, refused honestly at admission
  until built; (2) faster-whisper constructor-inseparable load — narrow
  local-only exception, seam recorded.
- ONE fix round dispatched to a Terra worker; orchestrator owns the
  full-suite sweep afterward. No further counsel round.

---

# Phase D capped counsel pass (Sol, 2026-08-24, post-commit — both slices)

Fresh Sol session scoped to Phase D at `5aadd02a`. Verified amendments
1–11 in the committed code with its own probes and the four proof
files (79 passed, isolated HOME). Verdict: **ONE FIX ROUND REQUIRED —
two ordinary-path findings; then RATIFY-WITH-NOTES and ship.**

## Finding D1 — The default cold-wake action is dead after migration

Ordinary action: fresh migrated install, default Dictation Pipeline
unchanged (`enabled=True`, stages `intent-router`/`kb-enricher`,
pinned on at config/meeting.py:341-348), wake enabled, speak after the
wake phrase. Reproduced: wake admission refuses
`inference_service_route_policy_denied` — bundled speech admission
adds every configured provider capability for all routed non-Meeting
sessions including wake (speech_session/session.py:599-677), but
`wake-capture@1` authorizes only transcribe+preload
(inference_service_route_policy.py:184-199), so freezing the default
`speech.intent_classify` member refuses. No parent, no transcript, no
wake action. The R2 proof concealed the state by pinning the pipeline
false (test_dictation_session_admission.py:508) and no-op'ing the
production pipeline in its host (146-147). If routed wake provider
work is authorized, SERVICE execution also needs the bound parent
(provider.py:276-284). Required proof: the ordinary cold wake action
through normal Config (default pipeline ON), production Database +
startup migration + broker + SpeechSession + atomic bundle +
controller + routed admission + normally constructed unloaded
MLX transcriber (only the external MLX library bounded) reaching a
successful transcript AND configured wake output, one SERVICE
wake.session, no OWNER/preload assignment, no plain legacy provider
child, every reached model stage in one lawful bundle.

## Finding D2 — A lawfully deferred faster-whisper warm lies forever as "warming"

Ordinary action: select faster-whisper, Warm on Start enabled,
restart. Reproduced: parentless preload correctly defers
(constructor-inseparable) but runtime status stays `warming`
indefinitely — status set to warming before the thread starts
(transcriber_state.py:194-199), the deferral catch returns without
settling (161-178), exposed via activity.py:195-196. Capture stays
available; the glass lies. Required proof: production runtime against
a real migrated DB, backend=faster-whisper, warm-on-start on —
deferral with no construction/dispatch/execution/receipt, status
settling truthfully to a non-active state, and the first ordinary
speak-to-fill still admitting parent + frozen local route before
production faster-whisper construction with exactly one routed
transcription execution and successful local receipt (only the
external faster-whisper library bounded).

## Ledger notes (Sol)

- Remote speech transport: correctly refused at admission; future work.
- Faster-whisper constructor exception: honored; R5 proof is
  production-shaped.
- Cold-MLX R2 proof honors the anti-fake constraint (real unloaded
  transcriber) but its disabled pipeline hid Finding D1.
- The standalone continuity test still uses `Transcriber.__new__` + an
  internal `_MlxTranscriber` subclass — proof debt (migration/bundle/
  controller continuity proven; production constructor continuity
  not). No ordinary failure reproduced; stays ledgered.
- Actual-byte hashing verified: audio canonicalized to contiguous
  float32 before digest; callers cannot supply a competing digest
  (transcribe.py:549-588).

## Orchestrator disposition (2026-08-24)

- **D1 ACCEPTED — direction ruled: authorize routed wake provider
  work.** Wake's product behavior (wake → transcribe → configured
  pipeline action) is the tired-Tuesday expectation; making wake
  transcription-only would break it. Amendment 8 is narrowly amended
  (visible amendment, owner may overrule): `wake-capture@1` authorizes
  `speech.transcribe@1`, the derived `speech.preload@1`, AND the
  routed dictation-pipeline capabilities the wake flow dispatches
  (capability-only lookup; transcribe/preload stay local-only per
  amendment 7; provider stages keep the boundaries their capabilities
  permit, as on the owner dictation path). A wake parent never mixes a
  bundled member with a plain legacy provider child (amendment 10
  holds).
- **D2 ACCEPTED** — settle warm status truthfully on deferral.
- Both proofs as Sol specified. ONE Terra fix round dispatched; after
  it, Phase D is RATIFIED-WITH-NOTES per the cap.

## Fix round landed — PHASE D RATIFIED-WITH-NOTES (2026-08-24)

The single fix round implemented both findings per Sol's proof specs:
D1 — `wake-capture@1` extended to the routed wake pipeline tail
(amendment 8-bis in the design doc); routed provider execution
resolves its immutable deployment from the frozen route-plan member;
the new production proof
`test_phase_d_default_cold_wake_runs_its_complete_routed_bundle` runs
the ordinary cold wake with the DEFAULT pipeline ON (transcript +
configured wake output, one SERVICE parent, no legacy provider child),
and the R2 mask (no-op'd pipeline / pinned-false default) is removed.
D2 — admission deferral settles status to `not_loaded`
(`test_phase_d_faster_whisper_deferred_warm_settles_before_first_speak_to_fill`
proves deferral without construction/receipt, truthful status, and the
first speak-to-fill admitting parent + frozen route before
faster-whisper construction). Orchestrator verified independently
(focused 284 passed; confirming sweep 6432 passed / zero branch-new —
68 inherited + 4 known xdist load flakes each serial-green ×2). Per
the cap there is no further counsel round: **Phase D is
RATIFIED-WITH-NOTES.** Ledger carried: remote speech transport;
faster-whisper constructor seam; continuity-test `__new__` proof debt.
