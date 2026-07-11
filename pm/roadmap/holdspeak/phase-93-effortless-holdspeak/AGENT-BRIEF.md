# Phase 93 agent brief — Effortless HoldSpeak

## Owner intent

HoldSpeak has enough capability. This phase is the product remediation pass that
makes the capability feel streamlined, robust, and easy to use.

Phase 92 built valuable substrate: canonical language, durable capture seams,
qualified relationships, invocation receipts, explicit inference targets,
authority policy, and Desk projections. It did not yet prove the promised user
outcome. The primary clients still expose competing rooms, old labels, generic
verbs, front-loaded concepts, and unverified failure paths. Phase 93 consumes the
substrate and judges success only by the product the owner can actually use.

The Desk remains the primary interaction architecture. More strongly: the Desk
is HoldSpeak's **AI operating system**, not a simplified launcher in front of a
collection of advanced products. Do not invent a new home, dashboard, queue,
assistant shell, or control center. Streamlining means:

- three obvious daily starts — dictate, record, create;
- advanced power living on the Desk and appearing through familiar OS
  affordances when the current object, selection, process, or task makes it
  relevant;
- focused rooms entered with context and exited back to the originating Desk
  subject;
- one product vocabulary and one consequence grammar on Web and Swift;
- professional, concise product copy that explains work without marketing or
  storytelling;
- speech, drafts, captures, and selected context surviving real failures;
- receipts and recovery attached to the thing the person was working on;
- physical-device and owner evidence gathered throughout the work, not reserved
  for a ceremonial closeout.

The phase is successful when the owner can use HoldSpeak for daily dictation,
meetings, organization, model-backed work, integrations, and coder steering
without consulting the architecture or wondering which subsystem is the real
product. Richness belongs in the Desk experience; ease comes from coherent OS
primitives, direct manipulation, contextual availability, and progressive
mastery—not from moving the powerful product somewhere else.

## The Desk as the AI operating system

Treat the Desk as a real operating environment with a consistent interaction
grammar:

- **Documents and durable things:** Meetings, Notes, Artifacts, Projects, and
  retained Results have stable identity, place, metadata, and lifecycle.
- **Containers and views:** Zones provide placement; Knowledge provides
  reusable context; spatial, list, search, and focused views are different views
  of the same things.
- **Tools and applications:** Personas, Workflows, Integrations, and models are
  runnable Desk capabilities. They may live in a dock/tool shelf, attach to a
  selection, or open an inspector/window; they are not imprisoned in Studio.
- **Processes and presence:** Coder sessions, capture, sync, background runs,
  paired devices, and inference targets appear as live processes/devices with
  status, controls, and recoverable state.
- **System affordances:** selection and multi-selection, contextual menus,
  inspectors/properties, windows/sheets/workrooms, a tool shelf or dock,
  search/launcher, keyboard commands, drag/drop, undo/retry/recovery, status
  indicators, notifications/attention, and receipts form one reusable grammar.
- **Authority and safety:** proposed effects, grants, mode, destinations, and
  receipts appear at the relevant object/tool/process boundary, like OS
  permission and activity surfaces rather than a detached policy product.

`Studio` is a focused construction and deep-configuration workroom. A person may
author a Workflow graph, Persona, Integration binding, or inference destination
there because the task benefits from a dedicated editor. The authored
capability then lives on the Desk, participates in selection and context, can be
launched and inspected there, reports live state there, and returns its results
there. Studio is not the place advanced capabilities go to disappear.

The three control postures are a first-class AI-OS system setting: **Secure**,
**Normal**, and **YOLO**. Secure is cautious; Normal lets routine safe/configured
work flow and asks at consequential boundaries; YOLO produces zero HoldSpeak
approval prompts for eligible configured/registered actions. No posture weakens
authentication, secret custody, destination/payload integrity, pane identity,
configuration integrity, receipts, or schema safety. The exact compatibility
and operation-family contract is in
[control-mode-contract.md](./control-mode-contract.md).

All operational copy follows
[copy-contract.md](./copy-contract.md). The Desk may retain visual character,
motion, spatiality, and Qlippy as a visual presence; the words stay calm,
professional, factual, and task-first. Do not use marketing prose, lore,
anthropomorphic filler, jokes, or cinematic narration to make routine product
behavior feel distinctive.

## The honest starting point

At `1e6a28f3`, Phase 92 changed 293 files and added about 17,800 lines. Focused
automated checks are healthy, but no Phase-92 story is formally done, there are
no Phase-92 evidence files or owner/device debriefs, and the acceptance close is
correctly blocked.

The remaining problem is visible in source, not hypothetical:

- Web primary navigation exposes nine destinations, including five Studio-level
  tools as peers.
- The Desk exposes five create nouns simultaneously.
- Web Desk world objects omit Project and Integration while native has connector
  objects.
- the flagship Swift root still says `Agent Desk` and describes paired delivery
  as `ON-DEVICE · LOCAL MESH`;
- generic `Approve`, `Apply`, `Open`, and `Run` remain on consequential paths;
- Control mode is mainly configuration, not contextual explanation;
- the first-value instrument submits fixed step/decision counts rather than an
  independently observed journey;
- long capture, interruption, offline sync, accessibility, and next-day return
  remain unproven on physical devices;
- the canonical all-tests command and parts of the UAT harness can hang on real
  audio or product-boot boundaries.

The detailed baseline and preserved substrate are in
[remediation-baseline.md](./remediation-baseline.md).

## Product model to preserve

A person needs only this model:

1. My work lives on the Desk as Meetings, Notes, Artifacts, and Projects.
2. I can place work in a Zone and gather material in Knowledge.
3. Personas and Workflows can work on the material I select; Coder sessions are
   live collaborators, not saved Personas.
4. Runs on tells me where intelligence executes.
5. Proposed actions say exactly what will happen and where.
6. The Desk remembers results, failures, and what needs me.

Internal compatibility nouns such as Recipe, Chain, Profile, connector,
actuator, provider, job, and projection remain valid in code and wire contracts
where required. They do not become first-use product lessons.

## Experience rules

Every story must answer:

1. What visible complexity is removed, combined, or deferred?
2. What daily task becomes faster or more predictable?
3. What happens when its dependency fails?
4. Where is the retained input, result, or recovery state?
5. How does the user stay on or return to the Desk?
6. How is the improvement observed on real Web and native clients?

Non-negotiable rules:

- Preserve direct URLs and expert capability while making the Desk—not Studio
  navigation—the primary discovery and operating surface.
- Do not replace five visible controls with one unexplained generic menu, and do
  not call the Desk simplified merely because its capabilities moved elsewhere.
- Do not count a label change as usability unless the action and recovery model
  become clearer.
- Never call paired, mesh, LAN, or external work same-device local.
- Never use a bare approval verb when the decision can execute or queue an
  external effect. In YOLO, do not render an approval step at all for an eligible
  configured operation.
- Every touched surface passes the professional-copy review: exact noun, state,
  consequence, destination, retained work, and next action; no marketing or
  storytelling filler.
- Never lose user-authored speech, text, capture, or selected context on failure.
- Do not add a second receipt, attention, policy, or destination system.
- No drag, hover, long press, or spatial memory may be the only path.
- Web responsive evidence is not Swift evidence; simulator evidence is not
  physical-device evidence.
- React and the flagship Swift client consume the same policy decision and
  reason codes; neither owns a private Secure/Normal/YOLO matrix.
- A story with a user-facing outcome captures before/after evidence from the
  production root in the same story.

## Ownership map

| Outcome | Hub/Python | Web | Swift/native | Proof |
|---|---|---|---|---|
| Front door and progressive disclosure | setup/onboarding routes, primitive summaries | `AppShell.tsx`, `DeskChrome.tsx`, `EmptyDesk.tsx`, Studio pages | `MeetingCaptureApp.swift`, `DeskHome.swift`, `DeskDioramaStage.swift` | before/after route and first-glance walk |
| Workroom entry and return | contextual refs, invocation/result refs | router, Desk pullouts, Dictation/Meetings/Workbench/Settings | Desk routing, Meeting/Workbench/Settings sheets | entry/result/return E2E |
| Product language and consequences | product language, trust destination, operation policy registries | primary labels, Qlippy, Mission Control, History | flagship root, Queue, proposal/review surfaces | generated census + owner comprehension |
| Contextual capability | primitive, project, integration, target APIs | Desk world/tool presence and contextual actions | native Desk tools and pickers | cross-client journey fixtures and captures |
| Dictation resilience | transcription/delivery/onboarding records | First Words, Dictation, speak-to-fill | Dictate model/view and paired delivery | real microphone/fault matrix |
| Meeting resilience | capture journal, recovery, sync/conflicts | Record orb, Live, History, Meeting object | capture/audio store/sync/recovery | long-run, kill, offline, conflict evidence |
| Authority in context | policy, grants, actuators, steering, receipts | trust chip, proposal/session/attention cards | Settings, Desk proposals, Queue HUD | exact-effect matrix in every mode |
| Accessible Desk | pageable semantic APIs | semantic list, focus, compact layout | VoiceOver actions, Dynamic Type, Reduce Motion | keyboard/screen-curtain/device walks |

## Sequencing thesis

1. Simplify the visible front door while establishing the Desk's OS affordance
   grammar; do not reduce the Desk's capability ceiling.
2. Make every focused room return coherently before migrating more tools into
   contextual entry points.
3. Finish the shared language and consequence grammar before judging owner
   comprehension.
4. Make Projects, Integrations, and expert capability first-class Desk tools,
   processes, and objects through contextual actions, inspectors, a tool shelf,
   search/launcher, and focused windows—not more permanent chrome or exile to
   Studio.
5. Prove dictation and meeting resilience independently with real hardware.
6. Make authority and automation understandable where the action occurs.
7. Complete accessibility and scale after the primary action grammar is stable.
8. Close only after sustained owner use, not one scripted happy-path demo.

## Relationship to Phases 91 and 92

Phase 91 remains the current phase until its owner/Swift parity gate is closed.
Phase 93 stays planned and does not move the roadmap pointer.

Phase 93 consumes the Phase-92 substrate but does not require Phase 92 to be
falsely declared successful. Phase-92 owner/device acceptance may be satisfied
only by genuine evidence produced through this remediation, with explicit links
and re-checking; nothing is inherited merely because Phase 93 exists.

## Do not turn remediation into expansion

- Do not add a new navigation tier or universal command center; deepen the Desk
  with reusable OS affordances instead.
- Do not create another generalized domain model.
- Do not rewrite all routes, stores, or Swift roots.
- Do not delete or hide advanced capability just to lower a screenshot's control
  count. A capability must remain discoverable and operable from the Desk.
- Do not spend a story polishing a registry without a visible client outcome.
- Do not postpone owner observation until the closing story.
- Stop if the phase accumulates more top-level concepts than it removes.
