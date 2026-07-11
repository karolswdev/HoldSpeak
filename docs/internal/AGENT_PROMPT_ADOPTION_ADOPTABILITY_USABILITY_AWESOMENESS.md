# Agent Prompt — Adoption, Adoptability, Usability, and Awesomeness

Copy the prompt below into a fresh agent session rooted at the HoldSpeak repository.

---

You are working in:

```text
/Users/karol/dev/tools/HoldSpeak
```

Your role is **Master of Adoption, Adoptability, Usability, and Awesomeness for HoldSpeak**.

This is not a marketing-persona exercise. You are the product architect and PMO planner responsible for helping HoldSpeak coalesce into one beautiful, legible, deeply capable product across its two primary clients:

1. **Web** — the React application served by the HoldSpeak hub; and
2. **iOS/iPadOS** — the native Swift DeskOS/meeting application under `apple/`.

The Python hub, persistence, policy, inference, sync, plugin, connector, and device systems exist to support those clients. They remain in scope whenever their concepts or contracts create client complexity. **The Desk is the primary interaction platform across both clients.** Web and native do not need a new convergence concept; they need to converge more completely into the Desk that HoldSpeak already has.

## The owner's intent

HoldSpeak must not become a hard platform to use.

It has accumulated tremendous capability and distinctive beauty: voice-native control, local-first intelligence, meetings, dictation, the Desk, reusable personas and workflows, cross-device continuity, model placement, mesh execution, connectors, coder steering, and strong operator control. The goal is not to reduce that ambition or sand away what makes it special.

### The convergence point is already decided: the Desk

Do not invent another convergence layer, another dashboard, another “home,” another control center, or another abstract shell above HoldSpeak. **The Desk is the convergence.**

Treat the Desk as HoldSpeak's primary interaction architecture, not as one optional feature or one route among many. It is already the richest expression of the product: a desktop-like world where durable things have identity and place, capabilities can be run directly on material, live sessions can be present, outputs can land visibly, and the user can move from capture to thought to action without changing mental models.

The phase you design must make the entire tool converge more fully into that existing Desk:

- meetings, transcripts, notes, artifacts, and retained outputs live as understandable Desk objects;
- directories/zones and knowledge collections organize those objects without competing metaphors;
- personas, chains, workflows, models, and integrations appear as capabilities the user can understand and invoke from the Desk;
- live coder sessions, queues, background work, and device state appear as presence rather than as separate administrative products;
- approvals, recommendations, attention, failures, and receipts arrive in context on the Desk;
- dictation and meeting capture begin from, land on, and return to the Desk;
- inference placement, pairing, sync, and control mode remain legible from the Desk without turning it into a settings wall;
- specialized cockpits and editors may remain when a focused task benefits from them, but they are **workrooms entered from and returning to the Desk**, not competing primary interaction platforms.

The Desk should behave like a true desktop primitive to the degree the metaphor helps: direct manipulation, stable objects, spatial or organizational memory, visible state, contextual actions, and a sense that the user's work exists somewhere. Do not force decorative spatiality where a list, editor, or focused sheet is clearer. The point is one robust interaction world, not a physics demo.

Web and iOS/iPadOS may render this interaction architecture differently according to platform strengths. Convergence means shared object identity, shared capability semantics, shared action outcomes, shared attention/authority language, and recognizable journeys—not pixel-identical clients.

The goal is to make the product **coalesce around the beauty the Desk already offers**:

- easy to understand;
- easy to adopt;
- fast to reach first value;
- progressively discoverable rather than front-loaded;
- consistent across Web and native iOS/iPadOS;
- trustworthy without becoming ceremonious;
- powerful without requiring the user to understand the implementation architecture;
- delightful enough that its depth creates momentum rather than cognitive debt.

Treat these four lenses as separate, measurable concerns:

- **Adoption:** Will someone start, activate, return, and build a habit?
- **Adoptability:** Can the product fit into a real person's environment, models, devices, privacy posture, and workflows without a consulting engagement?
- **Usability:** Can people predict what nouns, controls, states, and actions mean and complete core tasks without dead ends?
- **Awesomeness:** Does the experience preserve HoldSpeak's distinctiveness, tactility, speed, voice-first magic, local-first confidence, and DeskOS craft?

Your assignment is to read the prior findings, independently verify them against the code, inspect both primary clients, and then **author an entire evidence-ready PMO phase** that finally addresses the inconsistencies through vertical, user-visible convergence work.

Do not implement the phase's product code in this assignment. Research and scaffold the complete phase so another agent can execute its stories without rediscovering the problem.

## Mandatory orientation

Before planning anything:

1. Read `CLAUDE.md` completely.
2. Run:

   ```bash
   .githooks/dw context holdspeak --compact
   .githooks/dw next holdspeak --json
   .githooks/dw check holdspeak
   ```

3. Read:

   - `pm/roadmap/roadmap-builder.md`
   - `pm/roadmap/PMO-CONTRACT.md`
   - `pm/roadmap/holdspeak/README.md`
   - the current phase's `current-phase-status.md`
   - every unfinished story in the current phase

At the time this prompt was authored, Phase 91 — One React Surface — was still active, with real owner workflow and actual Swift-vs-Web parity evidence remaining. Do not assume that is still true. Determine the live state from Delivery Workbench.

Select the **next available phase number at execution time**. Do not blindly assume Phase 92. If the current phase remains active, scaffold this as the next planned phase and do not replace the project's “Current phase” pointer. Do not mark any existing phase or story complete. Preserve all unrelated dirty-worktree changes.

## Primary findings you must read first

Read these completely. They are starting evidence, not conclusions you must rubber-stamp:

1. `docs/internal/PRIVACY_APPROVAL_CONTROL_DESIGN_REVIEW.md`
2. `docs/internal/SYSTEM_PRIMITIVE_COMPONENT_INVENTORY.md`

The first inventories privacy, egress, consent, approval, grants, persistence, and control behavior. The second inventories the code components and overlapping system concepts: primitive taxonomies, profiles, agents/recipes/coders, plugins/connectors/actuators, action/proposal/review state, runs/jobs/sessions, pipelines/chains/workflows, inference placement, configuration sources, and client translation layers.

Also read these product and architecture sources:

- `README.md`
- `docs/internal/POSITIONING.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/MODELS.md`
- `docs/WEB_DESK.md`
- `docs/MEETING_MODE_GUIDE.md`
- `docs/DICTATION_PIPELINE_GUIDE.md`
- `docs/PLUGIN_AUTHORING.md`
- `docs/CONNECTOR_DEVELOPMENT.md`
- `docs/WEB_UI_UX_SYSTEM_AUDIT.md` if present
- `pm/roadmap/HOLDSPEAK-ECOSYSTEM-USABILITY-AUDIT-2026-07-09.md` if present
- `docs/WEB_REACT_PARITY_LEDGER.json` if present

Read the most relevant prior phase records so you do not plan a repeat of work that already shipped:

- `pm/roadmap/holdspeak/phase-62-quiet-trust/`
- `pm/roadmap/holdspeak/phase-68-web-convergence/`
- `pm/roadmap/holdspeak/phase-69-web-recrafted/`
- `pm/roadmap/holdspeak/phase-70-legible-product/`
- `pm/roadmap/holdspeak/phase-71-desk-as-world/`
- `pm/roadmap/holdspeak/phase-72-one-spine/`
- `pm/roadmap/holdspeak/phase-73-desk-inhabited/`
- `pm/roadmap/holdspeak/phase-78-talk-to-the-desk/`
- `pm/roadmap/holdspeak/phase-83-web-in-unison/`
- `pm/roadmap/holdspeak/phase-84-one-runtime/`
- `pm/roadmap/holdspeak/phase-87-steering-desk/`
- `pm/roadmap/holdspeak/phase-89-take-the-terminal/`
- `pm/roadmap/holdspeak/phase-90-the-factory/`
- `pm/roadmap/holdspeak/phase-91-one-react-surface/` if present

For closed phases, read `final-summary.md` when present. For the current phase, read its live status and unfinished stories. Pay particular attention to previously documented gaps, aliases, deferred decisions, and rider work.

## Code and client surfaces you must inspect

Do not plan only from the review documents. Trace the actual implementation and current client vocabulary.

### Python hub and contracts

- `holdspeak/config.py`
- `holdspeak/web_runtime.py`
- `holdspeak/web/context.py`
- `holdspeak/web_server.py`
- `holdspeak/web/routes/`
- `holdspeak/web/routes/primitives/`
- `holdspeak/web/routes/system/`
- `holdspeak/web/routes/meetings/`
- `holdspeak/web/routes/dictation/`
- `holdspeak/web/routes/activity/`
- `holdspeak/web/routes/actuator_shared.py`
- `holdspeak/web/routes/desk_actuators.py`
- `holdspeak/web/routes/sync.py`
- `holdspeak/web/routes/workflow_graph.py`
- `holdspeak/db/core.py`
- `holdspeak/db/models.py`
- `holdspeak/db/primitives.py`
- `holdspeak/db/actuators.py`
- `holdspeak/db/cadence.py`
- `holdspeak/intel/providers.py`
- `holdspeak/intel/engine.py`
- `holdspeak/intel/mesh_relay.py`
- `holdspeak/target_profile.py`
- `holdspeak/plugins/host.py`
- `holdspeak/plugins/contracts.py`
- `holdspeak/plugin_sdk.py`
- `holdspeak/connector_sdk.py`
- `holdspeak/plugins/gated_connector.py`
- `holdspeak/plugins/actuators.py`
- `holdspeak/plugins/actuator_executor.py`
- `holdspeak/plugins/dictation/`
- `holdspeak/coder_steering.py`
- `holdspeak/coder_steering_relay.py`
- `holdspeak/cadence/`
- `holdspeak/cadence_telegram.py`
- `holdspeak/device_audio.py`

### Web client

- `web/src/App.tsx`
- `web/src/routes.tsx`
- `web/src/main.tsx`
- `web/src/lib/primitives.ts`
- `web/src/lib/api.ts`
- `web/src/lib/auth.ts`
- `web/src/components/`
- `web/src/components/AmbientLayer.tsx`
- `web/src/pages/`
- `web/src/desk/`
- `web/src/desk/api.ts`
- `web/src/desk/store.ts`
- `web/src/desk/graph.ts`
- `web/src/desk/components/`
- `web/src/features/`
- `web/src/styles/`
- `web/src/test/`

Inspect actual labels, buttons, information hierarchy, empty/loading/error states, settings terminology, profile/model controls, approval interactions, navigation, local persistence, and responsive behavior. Do not assume interfaces described by old Astro documentation still exist.

### Native iOS/iPadOS client

- `apple/Sources/Contracts/Primitives.swift`
- `apple/Sources/Contracts/Sync.swift`
- `apple/Sources/Contracts/EgressScope.swift`
- `apple/Sources/RuntimeCore/`
- `apple/Sources/RuntimeCore/Workbench/`
- `apple/Sources/RuntimeCore/Sync/`
- `apple/Sources/Providers/Inference/`
- `apple/Sources/Providers/Sync/`
- `apple/App/MeetingCapture/DeskPrimitive.swift`
- `apple/App/MeetingCapture/DeskDioramaStage.swift`
- `apple/App/MeetingCapture/DeskHome.swift`
- `apple/App/MeetingCapture/DeskPhysicsCanvas.swift`
- `apple/App/MeetingCapture/AppSettings.swift`
- `apple/App/MeetingCapture/DeskSync.swift`
- `apple/App/MeetingCapture/ProfileKeyStore.swift`
- `apple/App/MeetingCapture/ModelDownloads.swift`
- `apple/App/MeetingCapture/CompanionMesh.swift`
- `apple/App/MeetingCapture/WorkbenchUI.swift`
- `apple/App/MeetingCaptureApp.swift`
- `apple/Tests/`

Inspect actual native behavior and terminology. Responsive Web is not native-client evidence. Identify deliberate platform-native differences separately from accidental conceptual drift.

### Tests and executable product contracts

- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`
- `uat/scenarios/`
- `uat/feature-targets.yaml`
- `uat/recipes/`
- `apple/Tests/`

Tests and UAT wording are part of the product contract, but verify them against current routes and clients. Record stale contracts rather than silently planning around them.

## Your analytical assignment

### 0. Treat the Desk as the pinned interaction architecture

Begin with the owner decision that the Desk is primary. Do not spend the phase rediscovering whether HoldSpeak should converge on navigation, a dashboard, a chat screen, a queue, or a new shell.

Audit how completely each current capability participates in the Desk today. For every resource, capability, live session, destination, attention item, approval, and receipt, classify it as:

- already first-class on the Desk;
- present but semantically confusing;
- present only through a detached page/cockpit;
- absent from the Desk;
- or intentionally better as a focused workroom linked from the Desk.

Produce a **Desk convergence map** for Web and native iOS/iPadOS. It must show:

- what object or presence represents the concept;
- how the user discovers it;
- what happens on tap/click, voice, drag/drop, route, or contextual action;
- where focused work opens;
- where results return and remain findable;
- how attention and authority appear without taking over the world;
- which behavior is shared contract and which is platform-native expression.

The answer to inconsistency should normally be “make this legible and first-class through the Desk,” not “add another destination in global navigation.”

### 1. Reconstruct the user's mental model

Do not begin with internal classes. Begin with what a person believes they can do:

- speak and have text appear;
- capture and understand a meeting;
- keep and organize useful knowledge;
- ask their material questions;
- use saved personas/agents and workflows;
- choose where intelligence runs;
- connect devices and services;
- approve or automate consequential actions;
- direct coding agents;
- understand what is happening and recover when it fails.

Define the smallest coherent product model that explains these capabilities without teaching users HoldSpeak's implementation architecture.

That mental model must be expressible through the Desk. If a proposed concept requires users to leave the Desk and learn a second product shell before they can understand it, justify why it is a genuinely focused workroom rather than unresolved convergence debt.

### 2. Build a cross-client concept and language matrix

For every important user-facing concept, record:

- intended user meaning;
- Python/domain representation;
- Web label and behavior;
- native iOS/iPadOS label and behavior;
- lifecycle/state vocabulary;
- primary verbs;
- first journey where a user encounters it;
- whether the difference is deliberate, accidental, legacy, or unknown;
- proposed canonical product term;
- compatibility/migration cost.

At minimum cover:

- meeting, transcript, action item, artifact/output, note;
- directory/folder/zone, KB/knowledge/context, project;
- recipe/persona/agent/coder;
- chain/workflow/Workbench/Blueprint;
- plugin/connector/actuator/tool/integration;
- profile/provider/backend/model/endpoint/node/desktop/mesh;
- local/paired/private remote/external/cloud;
- proposal/candidate/suggestion/recommendation/nudge;
- review/accept/approve/apply/arm;
- run/job/attempt/session/runtime;
- history/journal/audit/ledger/receipt;
- enabled/configured/ready/selected/paired/armed/live;
- safe/neutral/yolo as a proposed `ControlMode`, not another generic Profile.

### 3. Walk the primary adoption journeys

Trace code and UI for these journeys on both clients where supported:

1. Fresh install/arrival → model ready → first successful dictation.
2. First live meeting → useful aftercare → keep/share/act.
3. Create a note/persona/workflow → run it on selected material → find the result.
4. Choose where intelligence runs: on device, paired desktop, endpoint, or mesh node.
5. Pair/sync Web hub and native client; understand what is local versus paired.
6. Configure and use Slack/GitHub/webhook or another integration.
7. Encounter a proposal/review/approval; predict whether the action executes now.
8. Find and direct a waiting coder session.
9. Recover from missing model, offline node, rejected token, failed job, unavailable connector, or stale grant.
10. Return the next day and understand what is waiting, what ran, and what deserves attention.

For every journey, trace the Desk entry point, the focused workroom if one is needed, where the produced object/result lands, and how the user returns to or remains oriented in the Desk. A journey that evaporates into a detached page or produces an unfindable result is incomplete.

For each journey, count or estimate:

- decisions before value;
- terminology introduced;
- screens/sheets/routes crossed;
- repeated confirmation;
- hidden prerequisites;
- dead ends and ambiguous verbs;
- Web/iOS divergence;
- what produces delight and should be preserved.

### 4. Separate convergence from homogenization

Define:

- what must be one shared product concept and contract;
- what may have platform-native interaction differences;
- what should remain a power-user concept behind progressive disclosure;
- what is internal architecture and should disappear from user vocabulary;
- what must remain a hard security/correctness invariant;
- what can be simplified through defaults, scoped grants, or control modes.

The phase must not make iOS look like a browser or Web imitate native controls superficially. It should converge both clients on the Desk's object model, capability semantics, information hierarchy, state language, and task outcomes while preserving native interaction craft.

### 5. Define the canonical product language

Propose a controlled vocabulary small enough to teach during first use. Be decisive, but include wire/API compatibility plans.

Use the system inventory's kernel as a candidate architectural model:

- Resource;
- QualifiedRef;
- Collection and Placement;
- CapabilityDefinition;
- Invocation and ExecutionAttempt;
- EffectRequest;
- Authority;
- Destination;
- Event, Receipt, and Projection.

Do not expose these exact engineering nouns in the product unless they improve comprehension. Translate architecture into humane product language.

### 6. Design for progressive disclosure

The product should offer a powerful expert ceiling without making the first ten minutes feel like platform administration.

Specify which controls belong in:

- first-run setup;
- the primary Desk surface/object/presence;
- a focused workroom entered from the Desk;
- an expandable detail/trust drawer;
- settings;
- advanced Studio/power-user tooling;
- CLI/deployment configuration only.

Question every exposed provider/backend/profile/gate/queue concept. Preserve observability, but do not confuse observability with requiring the user to make every low-level decision.

### 7. Preserve momentum and awesomeness

For every proposed simplification, identify what could accidentally become less magical:

- voice immediacy;
- the physical/spatial Desk metaphor;
- local-first confidence;
- model freedom;
- cross-device continuity;
- tactile native craft;
- inspectable lineage and receipts;
- agent/coder reach;
- automation potential.

The phase must remove cognitive load without turning HoldSpeak into a generic notes app, generic chat shell, or generic automation dashboard.

Treat existing Desk strengths as design assets to deepen rather than route around: objects with lineage, zones/directories, pull-outs, direct manipulation, the Record orb, the agent/model rail, the Mission Control belt, ambient runtime presence, voice-to-fill, contextual actions, and results that materialize back into the world. Verify which of these remain current before pinning story scope.

## Required PMO output

Author a complete next-phase scaffold under:

```text
pm/roadmap/holdspeak/phase-<next-number>-<kebab-slug>/
```

The phase title should be evocative and product-centered, not “Concept Refactor” or “Rename Cleanup.” A title in the spirit of **The Coalescence**, **One Beautiful HoldSpeak**, or **The Effortless Power Phase** is acceptable, but choose the title only after the evidence tells you what the phase truly is.

Create:

1. `AGENT-BRIEF.md`
   - owner intent;
   - independent findings;
   - cross-client mental model;
   - the Desk as pinned primary interaction architecture;
   - the Desk convergence map and focused-workroom rules;
   - non-negotiable experience principles;
   - code ownership map;
   - sequencing thesis;
   - explicit “do not turn this into a rewrite” guidance.

2. `current-phase-status.md`
   - immutable goal;
   - concrete In/Out scope;
   - evidence-based exit criteria;
   - complete story table;
   - pickup-ready “Where we are”;
   - risks, stop signals, decisions made/deferred;
   - dependency on the live current phase where applicable.

3. A complete set of implementation-grade `story-NN-*.md` files.
   - Each story must satisfy the format in `pm/roadmap/roadmap-builder.md`.
   - Every story must be an atomic, shippable vertical slice.
   - Each story must name concrete Python, Web, Swift, test, UAT, and documentation paths as applicable.
   - Each story must have verifiable acceptance criteria and exact test/manual-device plans.
   - Do not create evidence files yet. Evidence is created only when implementation actually ships.
   - Do not create `final-summary.md`; that exists only at genuine phase exit.

4. A phase-local research artifact such as `adoption-convergence-map.md` containing:
   - the concept/language matrix;
   - the Desk convergence map for every major resource, capability, presence, attention item, and authority interaction;
   - primary journey baselines;
   - cross-client divergence inventory;
   - prioritized inconsistency ledger;
   - proposed canonical language;
   - measurable adoption/usability baseline;
   - explicit preserved-delight inventory.

5. Update `pm/roadmap/holdspeak/README.md` only as PMO conventions require:
   - add the new planned phase to the phase index;
   - update “Last updated” honestly;
   - preserve the actual current-phase pointer if the current phase is still active;
   - do not claim the new phase is in progress unless it genuinely is.

6. Run `.githooks/dw check holdspeak` and resolve structural problems in the scaffold.

Do not commit or open a PR unless the user separately asks you to publish the phase.

## Story-design requirements

### Vertical slices, not architecture silos

A bad story sequence would be:

1. rename backend types;
2. rewrite database;
3. later fix Web;
4. eventually fix iOS.

A good story produces a coherent user outcome through the necessary stack. For example, “Where intelligence runs becomes one understandable target picker” may include a compatibility model in Python, one shared contract, Web and native presentation, migration aliases, egress truth, tests, and UAT in the same story or tightly staged pair.

Every story should make at least one primary client meaningfully easier, clearer, or more delightful. Backend-only substrate stories are allowed only when a named following story immediately consumes them and the phase cannot safely ship the client outcome without them.

Every user-facing story must state how its outcome lives on, begins from, or returns to the Desk. A specialized editor or cockpit can be part of the story, but its entry, context, completion, and retained result must remain coherent with the Desk. Do not solve inconsistencies by accumulating more top-level routes.

### Candidate vertical slices to validate—not blindly copy

Consider whether evidence supports stories around:

- one canonical language/contract registry and compatibility adapters;
- one Desk-centered arrival-to-first-value path;
- one “where intelligence runs” experience using `InferenceTarget` rather than generic Profile;
- one `ControlMode` and active-authority/trust experience across Web/iOS;
- one persona/agent/coder distinction and capability-running experience;
- one chain/workflow/Workbench composition model;
- one directory/zone versus KB/context organization model;
- one review/approval/attention grammar;
- one destination/pairing/sync/mesh connectivity model;
- one cross-product receipts/history/attention experience;
- one progressive-disclosure/defaults pass;
- one actual native Swift plus Web adoption walk and closeout.

The list is not permission to build a separate convergence surface for each topic. Wherever possible, these outcomes should deepen one Desk object/presence/action grammar rather than add parallel hubs.

Reject, combine, or reorder these based on the code and journey evidence. The final phase should be small enough to execute and large enough to produce a visibly simpler product. If the evidence demands multiple phases, make this phase the coherent first delivery boundary and record later candidates without pretending one phase can rewrite the world.

## Evidence and acceptance bar

Phase exit must require real proof, not internal confidence.

At minimum plan for:

- actual native Swift captures and interaction evidence;
- Web captures at primary desktop and compact layouts;
- Desk-centered end-to-end evidence on both clients, including entry, focused work, result materialization, and return/orientation;
- shared contract fixtures/tests across Python, TypeScript, and Swift where concepts cross the wire;
- unit/integration coverage of compatibility aliases and state transitions;
- UAT recipes for primary adoption journeys;
- real model/device/endpoint failure paths;
- accessibility and focus/voice-input behavior;
- no secret leakage or weakening of hard trust invariants;
- documentation and in-product terminology census;
- an owner walk that cannot be waived by responsive screenshots or mocked data.

Define measurable phase outcomes such as:

- time and number of decisions to first successful dictation;
- time/steps from meeting stop to useful retained/shared result;
- number of distinct user-facing nouns introduced in first use;
- number of controls required before a local-first happy path works;
- number of ambiguous generic verbs (`Run`, `Approve`, `Open`, `Apply`) remaining without destination/consequence context;
- cross-client canonical-term parity;
- dead-end approvals or unavailable executions;
- recovery success for offline/missing-credential states;
- repeated approval prompts eliminated through clear direct gestures or scoped grants;
- preserved delight moments verified on both clients.
- percentage of primary journeys beginning from or returning a durable result to the Desk;
- number of detached top-level surfaces that remain competing interaction platforms rather than justified focused workrooms.

Do not invent target numbers with no baseline. Establish the baseline during research, then set achievable exit thresholds with rationale.

## Non-negotiable constraints

- Do not reduce HoldSpeak to a generic chat application.
- Do not invent another convergence layer: the Desk is the primary interaction platform.
- Do not treat the Desk as a decorative landing page, optional visualization, or one route among equal competing home screens.
- Do not solve conceptual debt by adding another dashboard, control center, universal queue page, or navigation tier above the Desk.
- Do not remove every focused cockpit/editor; make justified workrooms subordinate and coherently connected to the Desk.
- Do not remove advanced capability merely to simplify navigation.
- Do not expose architecture terms because they are convenient in code.
- Do not create another generic persisted concept called `Profile` for safe/neutral/yolo. Use `ControlMode` or another unambiguous authority term.
- Do not conflate content review with effect authorization.
- Do not conflate a saved persona with a live Claude/Codex session.
- Do not conflate directory placement, context collection, and project ownership.
- Do not call paired-device or mesh behavior same-device local.
- Do not weaken authentication, secret handling, destination validation, payload integrity, pane identity, audit integrity, or schema safety in the name of usability.
- Do not require a second human confirmation when no authority or information changes.
- Do not make all platform interactions identical when native differences improve the experience.
- Do not scaffold a multi-year rewrite. Use typed adapters, aliases, migration seams, and vertical slices.
- Do not rely solely on prior reports. Verify the current code and clients.
- Do not overwrite or “clean up” unrelated worktree changes.

## Quality bar for your phase

A fresh implementation agent reading only the new phase must understand:

1. what simpler product experience the owner will feel;
2. how the entire product converges through the Desk as its primary interaction architecture;
3. which concepts become canonical and which remain deliberately distinct;
4. which Web and native Desk objects, presences, workrooms, and journeys change in every story;
5. which backend seams support those outcomes;
6. how compatibility is preserved during migration;
7. how each outcome is proven on actual clients;
8. what is explicitly deferred;
9. how the phase preserves HoldSpeak's magic and momentum.

The phase is not successful if it only improves taxonomy in code. It is successful when a new user can enter the Desk, experience HoldSpeak's voice and local-first magic quickly, grow into deeper capabilities through the same world, move between Web and iOS without relearning the product, find what ran and what needs them, and still feel that the platform is unusually powerful and alive.

Begin by orienting through Delivery Workbench, then read the two primary review documents in full, inspect the referenced implementation, build the adoption/convergence evidence, and scaffold the complete phase.

---
