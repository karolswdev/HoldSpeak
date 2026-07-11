# Phase 92 — The Coalescence

**Status:** PRE-CLOSE IMPLEMENTATION (0/10). Phase 91 remains active.

**Last updated:** 2026-07-11 (the owner explicitly continued through HS-92-10 as
bounded pre-close work; all ten convergence journeys now have separate measured
Web and flagship-native UAT protocols, while Phase 91's HS-91-10 owner and
physical Swift close gate and the actual Phase-92 owner/device campaigns remain).

## Goal

Make HoldSpeak feel like one powerful, understandable product by converging Web
and native journeys on the Desk's shared objects, destinations, attention,
authority, and retained results without rewriting the underlying systems.

## Scope

### In

- A versioned canonical product-language/concept registry with Python,
  TypeScript, and Swift compatibility fixtures.
- Desk-centered arrival to first successful dictation on Web and the canonical
  native root, with retained input and recovery on failure.
- Crash-bounded meeting capture, honest partial processing, native meeting sync,
  and a durable meeting/result return to both Desks.
- One clear distinction among Zone placement, Knowledge membership, and Project
  scope, with coherent grounding and cross-device identity.
- One Persona/Workflow/Coder capability grammar whose runs materialize findable
  artifacts with lineage.
- One `InferenceTarget`/“Runs on” destination contract and actual-placement
  receipt across hub, Web, and Swift.
- Trust-critical repairs, a generated destination/operation inventory,
  commitment-specific decision verbs, scoped grants, and `ControlMode` presets
  that cannot bypass invariants.
- Contextual attention and receipt projections on the Desk, keyboard/VoiceOver
  equivalents, progressive disclosure, failure recovery, and actual-client UAT.

### Out

- A new home, dashboard, control center, global queue route, or shell above the
  Desk.
- A universal entity/event-store rewrite or simultaneous replacement of all
  domain repositories.
- A full third-party plugin sandbox or extension marketplace.
- Pixel-identical Web and Swift UI.
- Full graph-engine unification of Workbench, chains, dictation, connectors,
  and meeting routing.
- Coordinated deletion from third-party systems that HoldSpeak does not control;
  this phase must state those deletion boundaries honestly.
- Removing advanced features solely to reduce navigation.

## Exit criteria (evidence required)

- [ ] `docs/product-language.json` (or an equivalently named versioned registry)
      defines the phase vocabulary and compatibility aliases; Python, Vitest,
      and Swift fixture tests prove identical canonical terms, states,
      destinations, and decision kinds.
- [ ] The basic local first-value path reaches a successful dictation from the
      Desk in no more than three product steps, requires zero LLM/model-placement
      decisions, introduces no more than two technical nouns before success,
      and retains editable text with Retry/Copy/Keep on failure.
- [ ] Native and desktop meeting capture create a provisional durable record at
      Record, keep approximately flat resident memory, and recover bounded-loss
      audio/transcript after forced termination; partial intelligence reads
      “meeting saved” plus named incomplete work, never false `Ready`.
- [ ] A meeting captured offline in the canonical Swift app appears exactly once
      on Web after reconnect with title, transcript, timing, provenance, sync
      state, and aftercare intact; an induced conflict follows the documented
      policy without silent loss.
- [ ] The ten primary adoption journeys in
      `adoption-convergence-map.md` begin on the Desk or a justified native edge,
      enter any focused room with context, and return a durable result or receipt
      to a findable Desk subject.
- [ ] Every consequential run/action shown in the primary clients names its
      actual destination, data scope, authority basis, and outcome; no generic
      `Approve`, `Run`, `Open`, or `Apply` remains when the consequence or
      destination would otherwise be ambiguous.
- [ ] Off-loopback HTTP and WebSocket auth, redacted settings, full-section
      config preservation, Keychain pairing credentials, immutable
      payload/destination approval binding, local-provider no-fallback, pane
      identity, schema safety, and receipt creation pass identically under every
      `ControlMode`.
- [ ] Web keyboard-only and native VoiceOver/Reduce Motion/accessibility-text
      walks complete create, dictate, record/recover, organize, run, approve,
      inspect receipt, and return-to-Desk journeys without a drag-only action.
- [ ] Web desktop/compact and actual iPhone/iPad captures show the same product
      meaning for arrival, Desk, Dictation, Meetings, Settings, Workbench, one
      Integration, one Coder, and one failure; differences are documented as
      platform-native rather than silently drifted.
- [ ] Focused Python/integration/UAT suites, Web typecheck/test/build/audit, Swift
      tests, physical-device owner verdict, terminology census, secret scan, and
      `.githooks/dw check holdspeak` are captured in story evidence; Phase 91 is
      closed before Phase 92 is marked in progress.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-92-01 | The words HoldSpeak uses | in-progress | [story-01](./story-01-the-words-holdspeak-uses.md) | Automated contract green; manual cross-client walk pending |
| HS-92-02 | Trust is true before it is easy | in-progress | [story-02](./story-02-trust-is-true.md) | Auth, secrets, preservation, authority, Keychain, and registry automated proof green; physical-device trust walk pending |
| HS-92-03 | The first words land | in-progress | [story-03](./story-03-the-first-words-land.md) | Desk-first journey, content-free receipts, durable dismissal, native real-delivery route, and recovery automated proof green; physical microphone/device walk pending |
| HS-92-04 | A meeting survives and comes home | in-progress | [story-04](./story-04-a-meeting-comes-home.md) | Provisional/journal/bounded-memory/sync/conflict/recovery automated proof green; long-run fault and physical cross-device walks pending |
| HS-92-05 | One place for every useful thing | in-progress | [story-05](./story-05-one-place-for-everything.md) | Qualified independent axes, both-client actions/pickers/kept snapshots, Project/relationship sync and conflict API automated proof green; owner-visible conflict recovery and physical round-trip pending |
| HS-92-06 | Capabilities make findable results | in-progress | [story-06](./story-06-capabilities-make-results.md) | Invocation/attempt/result envelopes, readiness, no-lowering refusal, Web Workbench return, and Swift receipt decode green; native focused-room/cancellation/manual walks pending |
| HS-92-07 | Every run names where it happens | in-progress | [story-07](./story-07-every-run-names-where.md) | InferenceTarget/Profile alias, five destination classes, shared Web/native picker, named refusal, actual-placement Artifact receipts, docs/doctor, and no borrowed keys green; five physical destination walks pending |
| HS-92-08 | Decisions say what happens next | in-progress | [story-08](./story-08-decisions-say-what-happens.md) | Separate review/authority/execution axes, central four-family ControlMode policy, exact commitment verbs, bounded/revocable grants with use receipts, and Web/Swift/CLI controls green; physical mode/grant/revocation walks pending |
| HS-92-09 | The Desk remembers what needs you | in-progress | [story-09](./story-09-the-desk-remembers.md) | Schema v20 additive projection index, non-sensitive adapters, presentation-only state, Web Desk/Qlippy/Mission Control and native Queue HUD green; forced-failure/device/VoiceOver/next-day walks pending |
| HS-92-10 | The owner walk and evidence close | in-progress | [story-10](./story-10-owner-walk-evidence-close.md) | Ten-journey Web/flagship campaigns, required raw measurements, generated ledger additions, qualified seeding, and UAT harness automation green; genuine owner/device execution pending |

## Where we are

Phase 91 remains the actual current phase, with HS-91-10 open for owner
workflows and actual Swift parity evidence. By direct owner instruction,
HS-92-01 through HS-92-10 have started as bounded pre-close work by the owner's
explicit continuation instructions. The versioned language registry,
compatibility seam, fixture-verified client mappings, primary label migration,
and terminology guard are implemented. The trust slice now adds authenticated
WebSockets, redacted/dedicated secrets, section-safe persistence, mandatory
material authority binding, paired-token Keychain custody, and the shared trust
inventory. HS-92-03 replaces the wizard redirect with a one-step Desk-first
local transcription atom, persists content-free first-value/disposition state,
and sends the native Desk's desktop choice through the real named-Mac Dictate
surface rather than the Meeting recorder, with editable failure recovery.
HS-92-04 adds provisional durable Meeting identity, append-only audio journals,
bounded live buffers, explicit partial/recovery truth, native Meeting sync into
the capture store, recoverable LWW conflicts, and Desk return surfaces. Automated
HS-92-05 adds QualifiedRefs, three non-conflated organization/context axes,
container-aware stale-refusing grounding, exact kept-result relationship
snapshots, and additive relationship sync contracts. Automated checks pass;
HS-92-06 adds schema-v17 Invocation/Attempt receipts without replacing domain
job tables, visible capability readiness/placement/effect metadata, exact Web
Workflow loading and return, native Artifact receipt lineage, and hard refusal
instead of prompt lowering for unsupported graphs. HS-92-07 adds the versioned
InferenceTarget API over ProfileRecord, five non-conflated destination classes,
non-probing readiness, shared Web/native Runs-on selection, explicit alternate
recovery without silent retargeting, local-only same-device execution, and
schema-v18 actual-placement receipts retained on Artifacts. HS-92-08 adds a
typed OperationDescriptor/PolicyDecision resolver, schema-v19 independent
review/authorization/execution axes, atomic actor/effect/destination/data/scope/
time/count Grants with visible use receipts, ControlMode behavior for dictation,
steering, fixed connector writes, and cadence, plus matching Web/Swift/CLI
controls and consequence-specific commitment verbs. HS-92-09 adds contextual
attention and source-linked Receipt projections without copying domain payloads.
HS-92-10 adds two target-qualified ten-journey close campaigns and makes raw
exit measurements a required, durable part of substantive UAT verdicts. All ten
stories stay open for their remaining manual and physical-device walks. This does
not close Phase 91 or advance the current pointer.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The phase becomes a taxonomy rewrite | high | Each story must ship a complete Desk journey and compatibility adapter | a story changes internal names without improving a client outcome |
| Capture/meeting scope overwhelms one PR | high | Land the additive journal/provisional contract behind existing APIs, then consume it in both clients within HS-92-04 | either client needs a separate storage rewrite before a recoverable record can ship |
| Trust modes weaken invariants | high | HS-92-02 lands before modes; invariant matrix runs for all modes | any mode bypasses auth, secrets, destination, payload, pane, audit, or schema checks |
| “One Desk” becomes homogenized UI | medium | Share object/action/outcome semantics, not pixels | acceptance relies on responsive Web as Swift evidence or demands browser controls on native |
| Phase 91 and 92 collide in the Web tree | medium | Keep owner-directed HS-92-01/02/03 work bounded and additive; Phase 91 remains current | Phase-91 UAT evidence is inferred from this work or the pointer advances |
| UAT certifies stale promises | high | Reconcile scenarios with routes/source before reuse | a scenario expects meeting sync/keep-both or generic approval behavior the product does not implement |
| Progressive disclosure hides recovery or trust | medium | First use hides architecture, not consequences; every hidden control has a contextual door | a user must enter Settings to discover where an imminent action goes or why it failed |

## Decisions made (this phase)

- 2026-07-10 — The Desk is the pinned primary interaction architecture; no new
  convergence shell will be designed — direct owner intent in the phase prompt.
- 2026-07-10 — Phase 92 remains planned behind Phase 91; the README current
  pointer stays on Phase 91 — Delivery Workbench live state.
- 2026-07-10 — Direct owner instruction starts HS-92-01 as bounded pre-close
  implementation; Phase 91 remains current and no owner/device evidence is
  waived or inferred — owner instruction plus PMO gate preservation.
- 2026-07-10 — Compatibility adapters and generated fixtures precede wire-name
  removal — current Python/Web/Swift unions and aliases are not safe for a hard
  rename.
- 2026-07-10 — Product terms are Zone, Knowledge, Project, Persona, Workflow,
  Coder session, Integration, Runs on, Proposed action, Grant, and Receipt;
  internal/wire aliases remain documented in the research map — evidence review.
- 2026-07-10 — `safe|neutral|yolo` is `ControlMode`; “Profile” remains only a
  compatibility name for the current inference-target wire and is not reused
  for authority — privacy/system-inventory findings.
- 2026-07-10 — Trust-critical defects land before modes can widen convenience —
  no profile/mode may reinterpret correctness defects as friction.
- 2026-07-10 — Direct owner instruction continued to HS-92-02 before the
  Phase-91 close; implementation may proceed, but physical-device evidence and
  the current-phase pointer remain untouched.
- 2026-07-10 — Direct owner instruction continued to HS-92-03. The Desk is the
  Web arrival surface, basic local transcription precedes optional intelligence,
  dismissal is durable but is not success, and the native desktop choice must
  use the real Dictate contract rather than create a Meeting. Automated proof
  may advance; physical-microphone/device evidence and the Phase-91 pointer do
  not.
- 2026-07-10 — Direct owner instruction continued to HS-92-04. Record must make
  one Meeting durable before audio, journals bound process-death loss, committed
  PCM leaves memory, native capture storage participates in Meeting sync, and
  equal-clock divergence retains the losing value without claiming keep-both.
  Automated proof may advance; long-run/fault/physical-device evidence and the
  Phase-91 pointer do not.
- 2026-07-11 — Direct owner instruction continued to HS-92-06 and requested the
  accumulated work land on `main`. Runs receive one durable Invocation plus
  Attempts and an Artifact result ref; capability readiness is visible before
  Run; an unsupported graph is unavailable and never lowered to a prompt.
  Native Workbench entry/cancellation and manual/physical-device gates remain.
- 2026-07-11 — Direct owner instruction continued to HS-92-07 and required the
  work land on `main`. InferenceTarget is an additive v1 API over ProfileRecord;
  Profile and sync shapes remain supported aliases until no earlier than target
  contract v3. This device, paired device, private endpoint, mesh node, and
  external service stay distinct from engine/model, and unavailable or failed
  remote destinations refuse by name with an explicit alternate rather than
  borrowing credentials or silently retargeting. Five physical destination
  control/treatment walks remain open.
- 2026-07-11 — Direct owner instruction continued to HS-92-08 and required the
  work land on `main`. ControlMode resolves once through a typed central policy;
  Safe, Neutral, and YOLO never weaken hard invariants; reusable external-write
  grants are YOLO-only, fixed-destination, exact-scope, expiring, count-bounded,
  revocable, and use-receipted. Automated and simulator proof may advance;
  physical mode/grant/revocation walks remain open.
- 2026-07-11 — Direct owner instruction continued through HS-92-09 and
  HS-92-10 and required delivery to `main`. Desk attention remains an additive
  non-sensitive read model with presentation-only dismissal. Phase closure uses
  separate production-Web and physical-flagship campaigns for the same ten
  journeys, and substantive UAT verdicts must carry their prompted raw measures.
  No story is marked done, no device verdict is inferred, and Phase 91 remains
  the current pointer.

## Decisions deferred

- Whether `yolo` is the final UI label or an expert CLI alias — decide in
  HS-92-08 owner copy review; default wire value stays `yolo` and UI must explain
  that invariants remain.
- Universal executable graph convergence — revisit after Workflow compatibility
  and result materialization are proven; default is adapters, with Chain as
  linear Workflow shorthand.
- Cross-destination coordinated deletion — revisit when paired-hub retention and
  third-party compensation contracts exist; default is an explicit deletion
  boundary on receipts.
- Full domain-table normalization — revisit only if additive references,
  invocations, and receipts cannot support the journeys; default is no rewrite.
