# Phase 92 agent brief — The Coalescence

## Owner intent

HoldSpeak must become easier to enter, understand, and inhabit without losing
the power that makes it unusual. The convergence point is already chosen: the
Desk is the primary interaction architecture on Web and native Apple clients.
Do not add another home, dashboard, universal queue, or control center above it.

The owner should feel one product:

- speech begins from the Desk or a platform-native edge and lands somewhere
  visible;
- meetings, notes, transcripts, artifacts, and retained results have stable
  identity and a place;
- personas, workflows, models, integrations, and coders are understandable
  capabilities or presences, not competing product shells;
- focused rooms open from a Desk object and return a result to that object or
  to an obvious place on the Desk;
- attention, authority, failure, and receipts arrive in context without
  turning the Desk into an administration wall;
- Web and Swift share meaning and outcomes while retaining platform-native
  controls, layout, and motion.

The phase is measured through four separate lenses:

- **Adoption:** reach first value, return, and form a habit.
- **Adoptability:** fit real devices, model placement, privacy posture, and
  workflows without a consulting engagement.
- **Usability:** predict nouns, states, actions, and recovery.
- **Awesomeness:** preserve voice immediacy, Desk tactility, local-first
  confidence, inspectable lineage, and agent reach.

## Independent findings

The source and executable-contract review found a product with strong parts and
weak translation seams.

1. The Desk already is the right architecture. Web made it the front door in
   Phase 73; grounded conversations, model chat, steering, and the factory now
   live there. Replacing it would discard shipped advantage.
2. The type systems still disagree. Sync has 11 kinds, Web Desk has 11 kinds,
   and native `PrimitiveKind` has 15 kinds plus narrower card/object enums.
   Several are valid projections, but each surface describes its union as
   canonical.
3. User language crosses abstraction levels. `Profile`, `Agent`, `Action`,
   `Run`, `Context`, `Local`, `Approve`, and `Pending` each mean multiple things.
4. Trust is fragmented. The reviewed tree still has an unauthenticated general
   WebSocket off loopback, a settings read that returns the full config, a
   settings write that reconstructs only selected top-level sections, optional
   approval payload binding, and an Apple pairing token in `AppStorage`.
5. Some failures disappear. Web Desk create, update, file, and Record-orb
   failures are caught without an actionable visible recovery state.
6. The native production root remains conditional. `MeetingCaptureApp` ships
   `DioStage`, while several claimed workflows remain behind environment roots.
   The production Desk still offers “Talk to the desktop” but executes the
   local meeting-capture path.
7. Capture and continuity are adoption blockers. Native and desktop capture
   commit the durable meeting at Stop; native Desk sync explicitly emits
   `meetings: []`; post-capture intelligence can fail and still settle as
   “Ready.”
8. Some UAT wording is stale. The cross-device scenario claims native meeting
   sync and keep-both recovery, while current Swift omits meetings and its
   conflict policy is last-write-wins without a keep-both artifact.
9. The product's delight is real: the Record orb, materializing objects,
   spatial zones, grounded Ask, the persona rail, live coder presence, the
   Mission Control belt, explicit egress badges, and lineage-rich kept results.
   Simplification must deepen these, not route around them.

The detailed evidence, baselines, language decisions, and divergence ledger are
in [adoption-convergence-map.md](./adoption-convergence-map.md).

## Cross-client mental model

A person should need only this model:

1. **Your work lives on the Desk.** Meetings, notes, and kept artifacts are
   things. Zones place them; Knowledge gathers material for answers; Projects
   say which endeavor they belong to.
2. **Capabilities work on those things.** A Persona is reusable behavior, a
   Workflow is reusable multi-step behavior, and an Integration connects a
   named service. A Coder is a live session, not a saved Persona.
3. **Every run says where it happens.** “Runs on” names this device, a paired
   device, a private endpoint/node, or an external service before the run and
   on its receipt.
4. **Consequential actions say what happens next.** Review judges content;
   approval authorizes an exact effect; an armed grant permits a bounded set of
   repeated effects. Buttons name the commitment.
5. **The Desk remembers.** Results materialize, failures retain the user's
   input, attention stays attached to its subject, and receipts answer what ran,
   where, why, and with what outcome.

Engineering may use `Resource`, `QualifiedRef`, `CapabilityDefinition`,
`Invocation`, `ExecutionAttempt`, `EffectRequest`, `Authority`, `Destination`,
`Event`, `Receipt`, and `Projection`. Do not force those words into the UI when
the product terms above are clearer.

## The Desk is pinned

Every user-facing story must answer all six questions:

1. Which Desk object or presence is the entry point?
2. Which direct, voice, drag, route, or contextual action starts the work?
3. Is a focused room necessary, and why is it better than an in-world panel?
4. Where does the result materialize and remain findable?
5. How do failure, attention, authority, and receipts attach to the subject?
6. Which semantics are shared and which interaction is deliberately native?

Allowed focused rooms include Dictation, live Meeting, the Meeting archive,
Workbench, detailed Settings, and advanced integration setup. They are rooms
entered with context and exited back to a stable Desk object, not peers
competing to be the product's home.

## Non-negotiable experience principles

- The Desk remains the primary world, not a decorative landing page.
- Basic local transcription requires no LLM selection.
- No user-authored speech, text, or capture disappears on failure.
- A kept result has stable identity, lineage, and a place.
- `Persona` and `Coder session` never share one label.
- `Runs on` never uses a generic `Profile` label in product UI.
- Zone placement, Knowledge membership, and Project scope remain distinct.
- Review acceptance never grants effect authority.
- Approval binds the destination and material payload; a changed proposal needs
  new authority.
- `safe`, `neutral`, and `yolo` are values of `ControlMode`, not inference
  profiles, and no mode bypasses authentication, secret handling, destination
  validation, payload integrity, pane identity, audit, or schema safety.
- “Local” means this device. Paired, mesh, LAN, and external destinations are
  named as boundary crossings.
- Every spatial action has a keyboard, VoiceOver, and non-drag equivalent.
- Web compact evidence is never credited as native Swift evidence.

## Code ownership map

| Concern | Python/hub | Web | Swift/native | Proof |
|---|---|---|---|---|
| Canonical product contract | `holdspeak/db/models.py`, `holdspeak/db/primitives.py`, new additive contract module | `web/src/lib/primitives.ts`, generated fixtures/types | `apple/Sources/Contracts/` | Python, Vitest, Swift fixture parity |
| Desk objects and placement | `holdspeak/web/routes/primitives/`, `holdspeak/web/routes/sync.py` | `web/src/desk/` | `DeskPrimitive.swift`, `DeskDioramaStage.swift`, `DeskSync.swift` | route tests, Desk tests, device walk |
| Arrival/dictation | `holdspeak/setup_status.py`, `holdspeak/web/routes/setup.py`, dictation routes/runtime | `WelcomePage.tsx`, `DictationPage.tsx`, Desk inputs | production `DioStage`, `DictateView`/models | real mic and delivery receipts |
| Capture/meeting return | meeting recorder/session/import/repos/routes | `RecordOrb.tsx`, `LivePage.tsx`, `HistoryPage.tsx`, Desk pullout | `MeetingCapture`, `MeetingAudioStore`, `DeskDioramaStage`, sync provider | kill/recovery, aftercare, sync, captures |
| Inference placement | `holdspeak/intel/`, profile repository/routes, setup/doctor | target pickers, Desk run/chat, settings | `RuntimeProfile`, Providers/Inference, `RunsOnPicker` | cross-language fixtures, actual destination receipts |
| Authority and receipts | web auth/settings, actuators, steering, cadence, sync | trust drawer, proposal/attention components | `EgressScope`, pairing/key store, proposal and queue UI | auth/invariant matrix, owner decisions |
| Accessibility and return | typed API states | Desk object/list/focus/error grammar | semantic actions, list/lane, Reduce Motion, Dynamic Type | keyboard, VoiceOver, physical device |

## Sequencing thesis

1. Freeze meaning and compatibility before changing labels independently.
2. Repair trust-critical seams before introducing more permissive control
   behavior.
3. Close first-use and capture-loss failures before polishing expert paths.
4. Make content/placement and capability/result journeys coherent.
5. Normalize execution destination, then normalize authority and decisions.
6. Finish with one contextual attention/receipt grammar and an actual Web plus
   Swift owner walk.

Stories are vertical slices. Additive registry/adaptor work is acceptable only
when its story also changes a user-visible Desk outcome. Existing wire names
remain compatibility aliases until every Python, TypeScript, Swift, sync, and
UAT consumer is proven migrated.

## Do not turn this into a rewrite

- Do not replace the 52-table persistence model with a universal entity store.
- Do not create a new shell, navigation tier, or “everything” screen.
- Do not migrate every internal class merely to make names aesthetically pure.
- Do not force Workflow, dictation pipelines, connector pipelines, and meeting
  plugin routing into one graph engine during this phase.
- Do not delete advanced capabilities. Put their setup behind progressive
  disclosure and make their Desk entry/result coherent.
- Do not make Swift imitate browser controls or Web imitate Swift animation.
- Do not weaken or postpone trust invariants to make a demo feel smoother.

Use versioned adapters, generated fixtures, aliases with removal notes, and
small route/view-model seams. Stop if a story requires simultaneous replacement
of the canonical stores, all APIs, and both clients before any user outcome can
ship.
