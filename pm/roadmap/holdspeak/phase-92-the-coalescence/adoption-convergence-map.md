# Adoption and Desk convergence map

**Research date:** 2026-07-10  
**Scope:** pulled `main` at `d955fab0`; Python hub, one React Web client,
canonical Swift root and Desk, contracts, tests, UAT, and prior phase evidence.  
**Measurement note:** counts below come from source and existing captured audits.
No stopwatch or physical-device timing was performed during planning, so no
time-to-value number is invented.

## 1. Evidence and method

The phase was derived from:

- the complete privacy/approval review and system primitive inventory;
- product, architecture, security, model, Desk, meeting, dictation, plugin, and
  connector canon;
- Phase 62, 68–73, 78, 83–84, 87, 89–91 records;
- React routes, Desk source, Signal audit, and parity ledger;
- Python configuration, persistence, inference, extension, authority, sync,
  and route seams;
- Swift contracts, production root, `DioStage`, capture, sync, model, pairing,
  Workbench, and tests;
- UAT feature ownership and representative arrival, Desk, meeting, dictation,
  sync, integration, failure, steering, and native scenarios.

Prior reports were checked against current source. Findings that still reproduce
are in the inconsistency ledger. Findings superseded by the React cutover are
not planned again.

## 2. Smallest coherent product model

| What the person believes | Product concept | Internal support, not first-use vocabulary |
|---|---|---|
| My work exists somewhere | Desk item with stable identity | Resource + QualifiedRef + Projection |
| I can put it somewhere | Zone placement | Directory + membership/Placement |
| I can collect material for answers | Knowledge | KB/Collection membership |
| It belongs to an endeavor | Project | Project relationship/work scope |
| I can reuse a way of thinking | Persona | Recipe/CapabilityDefinition |
| I can reuse several steps | Workflow | Workflow; Chain compatibility shorthand |
| A coding process is waiting for me | Coder session | AgentSession/coder presence |
| I can connect a service | Integration | Connector/adapter/tool binding |
| Intelligence can run in different places | Runs on | InferenceTarget + selection + resolved placement |
| Something wants to affect the world | Proposed action | EffectRequest |
| I can permit exactly this or a bounded set | Approval or Grant | Authority decision |
| I can see what happened | Receipt | Execution/effect receipt plus source event |

This model is expressible through the Desk. Dictation, live capture, Meeting
detail, Workbench, and advanced Integration setup remain focused rooms because
their dense task benefits from a dedicated surface. Their entry, subject,
completion, and retained result must remain Desk-coherent.

## 3. Canonical product language

### 3.1 Controlled vocabulary

| Canonical product term | Meaning | Compatibility/internal terms | Migration rule |
|---|---|---|---|
| **Desk** | Primary world where work, capabilities, presence, attention, and results live | home, dashboard, DeskOS | `/` and canonical Swift root stay the entry; other rooms return here |
| **Meeting** | Captured/imported conversation aggregate | session in capture internals | “Session” is reserved for a live interactive relationship |
| **Transcript** | Time/speaker material owned by a Meeting | segments | Never a peer top-level resource unless deliberately detached |
| **Action item** | Work a person should complete | `ActionItem`, architectural `WorkItem` | Never use “Action” alone for an external effect |
| **Result** | Transient output printed by a run | execution result | Keep or discard is explicit |
| **Artifact** | Kept generated result with identity and lineage | `Artifact`, native `OutputRecord` | “Output” remains an internal/compatibility noun |
| **Note** | User-authored durable text | NoteRecord | Unchanged |
| **Zone** | Desk placement/folder; one findable home | Directory, folder, Placement | Product UI says Zone; wire keeps `directory` alias |
| **Knowledge** | Named, potentially many-to-many grounding collection | KB, Knowledge base, ContextCollection | First mention “Knowledge collection”; UI may shorten to Knowledge |
| **Project** | Ongoing endeavor/work scope | project association, `.hs` project context | Never substitute for Zone or Knowledge |
| **Persona** | Saved reusable role/prompt/tools/knowledge | Recipe, Agent persona, PersonaDefinition | Wire/API `recipe` remains an alias; “Agent” is removed from this product meaning |
| **Coder session** | Live Claude/Codex process and its waiting/steering presence | AgentSession, Coder | Never called Persona |
| **Workflow** | Saved reusable composition of steps/capabilities | Workflow, Blueprint, Workbench graph | Workbench is the focused editor; result returns to the source/Desk |
| **Sequence** | Advanced linear Workflow shorthand | Chain | Keep `chain` wire; do not teach it during first use |
| **Integration** | Named connection to a service/system | plugin, connector, actuator, adapter, tool | Packaging/SDK docs may retain precise internal terms |
| **Runs on** | User-facing answer to where intelligence executes | Profile, provider, backend, endpoint, node | The value is an `InferenceTarget`; no generic Profile label in UI |
| **This device** | Same-device processing/storage | local, on-device | “Local” is explanatory detail, not a claim about paired/LAN work |
| **Paired device** | Named user-paired HoldSpeak peer | desktop, hub, companion | Counts as egress from this device |
| **Private endpoint/node** | Named LAN/tunnel/mesh destination | mesh, desktop, self-hosted cloud provider | Name the device/host and data scope |
| **External service** | Named third-party/public destination | cloud, Slack, GitHub, Telegram, webhook | Name service/host and data scope |
| **Proposed action** | Exact consequential effect awaiting authority | proposal, actuator proposal, EffectRequest | Card says whether approval executes immediately |
| **Review** | Judge content quality/correctness | accept/reject artifact/action item | Never grants authority |
| **Approve and …** | Authorize an exact immutable effect | approve | Button finishes with consequence/destination |
| **Grant / Arm** | Bounded reusable authority | steering grant | Show target, operations, expiry/count, and revoke |
| **Run** | One request to a capability | invocation | Button adds object/capability when context is otherwise ambiguous |
| **Attempt** | One fulfillment/retry of a Run | job, try | Detail/receipt vocabulary, not primary UI |
| **Receipt** | Durable answer to what ran, where, why, and outcome | audit, ledger, journal row, event | Feature journals may remain; Receipt is the cross-product projection |
| **Control mode** | Confirmation/automation preset | proposed run profile, authority preset | Wire enum `safe|neutral|yolo`; never an inference Profile |

### 3.2 State language

| State | Exact meaning | Must not be conflated with |
|---|---|---|
| **Off** | Persisted preference disables feature | unconfigured, unavailable |
| **Not set up** | Required definition/credential is absent | off, offline |
| **Ready** | Dependencies currently allow an attempt | selected, enabled |
| **Selected** | Current preference/target | ready |
| **Paired** | Trusted peer relationship exists | reachable, synced |
| **Connected** | Transport is currently reachable | paired |
| **Armed** | Active bounded grant exists | live, enabled |
| **Live** | Session/process is currently operating | armed, ready |
| **Queued** | Durable work awaits an attempt | pending review |
| **Needs review** | Content decision is unresolved | proposed action |
| **Needs approval** | Exact effect lacks authority | needs review |
| **Failed** | Attempt reached a terminal error | offline, unavailable |
| **Partial** | Durable primary result exists; named secondary work is incomplete | ready/complete |

`pending` is not sufficient without an axis. Existing wire values may survive,
but every client adapter must map them into a qualified state.

## 4. Cross-client concept matrix

| Concept | Python/domain | Current Web | Current Swift | Drift | Canonical outcome / cost |
|---|---|---|---|---|---|
| Meeting | meeting aggregate + segments/intel | Meeting object + `/live` + `/history` | `MeetingPrimitive`, local capture store | native capture/sync ownership differs | Meeting; high cost because durable/sync lifecycle changes |
| Transcript | segments | Meeting pullout/detail tab | meeting section plus separate `transcript` primitive kind | projection promoted only on Swift | Meeting-owned Transcript; medium adapter cost |
| Action item | `ActionItem`, status + review axes | “Actions,” “Action,” open/done | actions projection/section | wording and lifecycle mix | Action item; low label, medium state cost |
| Result/artifact | plugin output, Artifact record | printed result then Artifact object | `OutputRecord`/OutputPrimitive | output/artifact naming | transient Result, kept Artifact; medium aliases |
| Note | Note repository | Note object | NoteRecord/Primitive | largely aligned | Note; low cost |
| Zone | Directory + membership | UI Zone, contract Directory | ZoneRec projects Directory | current docs/UI mix Zone/Directory/folder | Zone product term, Directory wire; medium census |
| Knowledge | KB with embedded member IDs | “KB” create chip; “Knowledge base” contract | KB/Knowledge UI | acronym/placement confusion | Knowledge collection; medium UI/membership work |
| Project | Project repository + `.hs` context | project roots/rules/context scattered | limited Desk expression | often conflated with grounding | Project work scope; medium relationship/UI work |
| Persona | RecipeRecord, `/api/recipes` | contract type `Agent`, UI Recipe/Agent | RecipeRecord, UI Agent | three names for saved behavior | Persona with `recipe` compatibility; medium-high census |
| Coder | coder registry/session/steering | Coder object and session pullout | AgentSessionPrimitive/coder views | “agent” leaks into native/internal | Coder session; medium label/contract work |
| Workflow | WorkflowRecord, graph subset runner | Workflow + Workbench | WorkflowDefinition + rich Workbench/Blueprint | execution support differs | Workflow + support result; high adapter/testing cost |
| Chain | ordered recipes | Chain primitive | ChainRecord | taught as peer capability | Sequence, advanced linear Workflow; medium |
| Integration | plugin/connector/actuator stacks | separate Activity/Commands/proposals; not Desk-first | connector Desk objects | packaging nouns exposed inconsistently | Integration product term; high route/authority mapping |
| Inference target | ProfileRecord + provider/backend config | Profiles page, “cloud-capable” | RuntimeProfile, RunsOnPicker | profile/cloud/local drift | “Runs on” + InferenceTarget; medium compatibility |
| Destination | endpoint/node/peer/host/pane fields | local/local+cloud/cloud badges | on-device/local+target/cloud | topology and trust conflated | named boundary + owner + data scope; high registry work |
| Proposed action | ActuatorProposal mixed lifecycle | History and Mission Control cards | send/mesh proposal cards | Approve may send or only authorize | Proposed action + commitment verb; high contract/UI |
| Review | action/artifact review fields | Accept/review states | review surfaces/rings | generic accept can look like authority | Review decision; medium state split |
| Grant | steering in-memory TTL | ARM/countdown | steering grants | strongest aligned pattern | Grant/Arm for target+time; low extension, high generalization |
| Control mode | absent | absent | absent | new concept risk | `ControlMode`, after P0 trust fixes; medium-high |
| Run/attempt | feature-specific runs/jobs | Run buttons, queues, status strings | local/hub runs, Queue HUD | no shared attempt/receipt | Run + Attempt detail; high additive adapter |
| History/receipt | many repositories | archive, journal, Activity, Queue, belt | local histories, Queue HUD | user must visit many surfaces | contextual Receipt projection; high index/read-model work |
| Readiness | config + runtime probes | enabled/ready/live/cloud-capable | paired/configured/offline/live | axes collapse | qualified state vocabulary; medium |

## 5. Desk convergence map

| Subject | Current Desk presence | Target entry/action | Focused room | Result/return | Shared contract vs native expression |
|---|---|---|---|---|---|
| Meeting | Web/Swift object; native may be local-only | Record orb or platform-native record edge | Live room for dense capture | provisional object immediately; finalized Meeting and child artifacts in place | same ID/lifecycle; desktop dual audio vs native mic craft |
| Transcript | hidden in Meeting pullout/detail | Open Meeting → Transcript | archive only for search/edit/export | remains owned by Meeting | shared segments; native/Web layout differs |
| Action item | Meeting section/aftercare | contextual Review/File/Complete | Meeting detail for bulk work | changed state visible on Meeting; external act gets Receipt | separate review/work/effect axes |
| Artifact | object/output card | Keep Result or open Meeting derivative | full editor only when necessary | stable object with source/via lineage | same QualifiedRef/lineage; native print animation retained |
| Note | first-class object | create/edit/speak in place | none for ordinary edit | autosaved object; visible error retains draft | same fields; native movable editor vs Web inline panel |
| Zone | Web shelf/Swift zone/lane | drag or Move/File action | semantic list/tree for accessibility | object remains findable in Zone | shared placement; geometry remains device-local |
| Knowledge | object/crystal | add/remove selected material; “Use as knowledge” | detail for membership/search | grounding picker names Knowledge source | collection distinct from Zone |
| Project | weak/fragmented | assign/view Project from object context | Project workroom when cross-object management is needed | project chip/relationship returns to objects | shared work-scope ref; platform-specific picker |
| Persona | Web rail/object; Swift character | open conversation or run on selected material | focused Persona editor | reply can be kept as Artifact beside source | PersonaDefinition contract; conversation stays device-local unless explicitly kept |
| Workflow | object + Workbench | drop/run or contextual Run Workflow | Workbench editor | Artifact materializes by source; graph support/refusal receipt | shared versioned graph/support result; native canvas vs Web canvas |
| Coder session | live object/pullout | watch free; Arm; speak/send; classify | in-Desk session pullout is preferred | note/story/receipt stays attached to Coder presence | shared grant/pane/action semantics; platform-native key palette |
| Integration | first-class mainly on Swift | drop/share/contextual “Send with …” | setup sheet/Settings for credential/config | Proposed action and Receipt attach to source | shared destination/effect contract; service-native auth differs |
| Inference target | rail/profile picker | “Runs on” beside impending run | advanced target editor | actual target appears on Result/Receipt | InferenceTarget wire/alias; pickers native to platform |
| Sync/pairing | pills/settings, inconsistent meeting scope | named peer presence; Sync now/pause | connection setup | per-object pending/synced/local-only/error plus Receipt | shared link/status axes; Keychain native secret storage |
| Queue/background work | Queue HUD/belt/pages | ambient presence on subject/object | detail drawer for attempts | completion/failure Receipt returns to subject | shared attempt envelope; no universal queue page |
| Recommendation/nudge | Qlippy, Cadence, activity cards | contextual suggested next act | detail only if evidence needs space | dismiss/act changes Attention projection, not subject truth | shared Attention envelope, feature content retained |
| Proposed action | proposal cards in several places | commitment-specific button | trust detail drawer | executed/failed Receipt on source and destination | EffectRequest/authority split; platform cards differ |
| Grant/Control mode | steering only / absent | trust chip shows mode and active grants | trust drawer for change/revoke | every use creates Receipt | shared evaluator/reason codes; CLI mode remains visible |
| Failure | hub dot/toast/route alert, uneven | inline on the subject with Retry/Copy/Keep | detail for diagnostics | user input remains; recovery outcome receipts | shared error categories; platform presentation differs |
| Receipt | feature-specific histories | recent receipt chip on subject and Desk attention | Receipt detail drawer | durable, searchable via subject/destination | additive index over domain records, not table rewrite |

## 6. Primary journey baselines

Counts are source-derived estimates of visible screens/decisions, not timings.

| # | Journey | Current baseline | Desk break | Phase target |
|---:|---|---|---|---|
| 1 | Arrival → first dictation | Web wizard has 6 steps, 4 backend choices, optional model/server/model decisions, explicit Save/Test, one physical dictation, optional Presence; basic path can continue without proving success. Swift production root teaches Desk/Zone gestures before a verified dictation path. | setup is a wizard/architecture lesson; native desktop-dictation option is false | ≤3 product steps, 0 LLM placement decisions for basic transcription, ≤2 technical nouns, real success/failure receipt |
| 2 | First meeting → aftercare | Web/Swift Record starts in memory and durable meeting appears at Stop. Native runs 2 default lenses and forces progress to `Ready` after a failure. | no provisional durable object; native result may not sync/return | durable object at Record; honest partial state; aftercare/artifacts attach and sync |
| 3 | Create capability → run → find result | Web exposes 5 create chips (`Note`, `KB`, `Recipe`, `Zone`, `Workflow`); run buttons say `Run`; native adds Persona/Chain/Workflow/Ask paths. | three capability nouns and generic verbs; results vary between transient and kept | Persona/Workflow journey, explicit source/capability, result materializes with lineage |
| 4 | Choose where intelligence runs | Web uses Profiles, Runtime destinations, on device/cloud-capable/mesh; native uses Runs on plus On device/Cloud/Local+target. | provider/topology/trust mixed | one Runs-on picker, named boundary/data scope before and after |
| 5 | Pair and sync | Web token path is session storage; Apple pairing token is AppStorage; native Desk sync excludes meetings; state distinguishes some errors well. | “synced” does not mean all classes; peer secret storage inconsistent | named peer, data-class scope, Keychain secret, per-object honest state, meeting continuity |
| 6 | Configure/use Integration | Slack hidden until configured and then proposal-gated; GitHub/webhook/Telegram/connector packs use other setup/gates. | integrations live in settings/pages and approval semantics vary | Integration object/contextual act, named destination/data, exact next action and Receipt |
| 7 | Review/approve | History uses Approve/Decline; Mission Control uses Approve/Reject; native send uses Approve & send; accepted content can later become a proposal. | same-looking verbs mean different commitments | Review vs Approve split; button states effect and destination; immutable binding |
| 8 | Direct waiting Coder | Web is strongest: Coder object → watch → hold ARM → countdown → steer/keys/factory/classify. Swift has parallel steering surface. | terminology and accessibility remain uneven | preserve flow; canonical Coder/Grant terms, non-hold/VoiceOver equivalent, receipts |
| 9 | Recover from failure | Web Desk mutations and orb can fall back to idle/hub dot; endpoint/mesh routes often name errors; Swift offers some explicit fallback but capture/post-processing can lie. | user text/capture can vanish or appear complete | typed failure categories, retained input, Retry/Copy/Keep, no false complete |
| 10 | Return tomorrow | meetings/archive, dictation journal, Activity, Cadence, Qlippy, Queue HUD, belt, steering audit, and sync each own attention/history. | no single subject-centered answer to “what needs me/what ran?” | contextual Desk attention plus unified Receipt index; no detached global queue shell |

### Baseline counts to preserve and reduce

- 18 React product routes including aliases/support routes; primary chrome shows
  Desk, Dictation, Meetings, five Studio entries, and Settings.
- 11 Web primitive kinds, 15 Swift primitive kinds, and 11 sync kinds.
- At least three visible approval verb pairs across primary surfaces.
- Five Desk create-chip nouns before progressive disclosure.
- Zero currently measured physical-device time-to-value. HS-92-03 must capture
  the real baseline before claiming a time reduction.

## 7. Cross-client divergence inventory

| Priority | Divergence | Classification | Resolution |
|---|---|---|---|
| P0 | Swift “Talk to the desktop” executes meeting capture | accidental/false | wire to real dictation with exactly-once receipt or remove until real |
| P0 | Swift Desk sync emits no meetings while UAT/docs claim continuity | accidental/legacy split | integrate capture store with sync and correct scenarios |
| P0 | Web `/ws` lacks off-loopback token enforcement | correctness/security | authenticate handshake identically to HTTP |
| P0 | Settings read returns secrets; PUT drops top-level sections | correctness/security | redacted view models + secret ops + section-safe persistence |
| P0 | Capture is stop-time durable and memory grows with duration | architecture gap | shared provisional/journal/recovery contract, platform implementations |
| P0 | Web Desk mutations/record failures can disappear | usability defect | typed result/error state on subject, retained optimistic content |
| P1 | Web says Recipe/Agent; Swift says Recipe/Agent; live process also Agent internally | accidental/legacy | Persona product term, Coder session live term, aliases |
| P1 | Directory/Zone/KB/Project all group work | mixed deliberate/accidental | preserve Placement, Collection, Work scope; canonical UI terms |
| P1 | Profile/provider/backend/target/node mix placement and engine | accidental | InferenceTarget + Runs on + actual destination Receipt |
| P1 | Swift promotes Meeting projections to primitive kinds; Web does not | deliberate presentation | classify as projections, keep native rendering |
| P1 | Approval combines authorization and execution states | architecture debt | separate authority and attempt state; commitment verbs |
| P1 | `pending` spans work, review, queue, attention, and proposals | accidental | qualified state axes/adapters |
| P1 | Egress grammar calls paired desktop cloud | accidental | boundary/owner/identity/data-scope destination view |
| P1 | Web Desk object is pointer-only; Swift canvas has gesture-only actions | accessibility debt | semantic list/actions and deterministic focus |
| P2 | Chain and Workflow are peer authoring concepts | legacy convenience | Sequence as advanced Workflow shorthand |
| P2 | Focused rooms remain top-level-addressable | deliberate | retain direct links; make Desk entry/result canonical |

## 8. Prioritized inconsistency ledger

1. **Trust truth:** WebSocket auth, settings secrets/config loss, Apple pairing
   secret storage, approval payload/destination binding.
2. **Speech truth:** real native desktop dictation, retained failed text, basic
   local first value without model administration.
3. **Capture truth:** provisional durability, bounded memory, honest partial
   processing, native meeting sync.
4. **Identity/language:** canonical registry and adapters; Persona/Coder,
   Zone/Knowledge/Project, Workflow/Sequence, Runs on.
5. **Destination truth:** named boundary, data scope, availability, and actual
   placement on every run.
6. **Authority truth:** review vs approval, exact commitments, scoped grants,
   ControlMode after invariants.
7. **Result truth:** transient Result vs kept Artifact, lineage, findable return.
8. **Attention truth:** subject-centered attention and receipts, no new global
   management product.
9. **Access truth:** keyboard, VoiceOver, Reduce Motion, large text, non-drag
   equivalents.
10. **Contract truth:** stale UAT/docs updated from the same registries and real
    production roots.

## 9. Progressive-disclosure placement

| Layer | Belongs here |
|---|---|
| First run | permissions with recovery, basic local transcription, one first success, optional named model-server path only when chosen |
| Desk | objects, Record, voice-to-fill, contextual Run/Send/Review, Runs on summary, active grant/mode signal, failures, recent receipts |
| Focused room | live capture, transcript search/edit/export, dictation learning detail, Workbench graph editing, Integration credential setup |
| Trust/detail drawer | destination identity, data classes, authority basis, grant TTL/count/revoke, receipt lineage, deletion boundary |
| Settings | durable preferences, default target, retention, background behavior, pairing management |
| Studio | advanced target authoring, workflow/sequence construction, connector/plugin diagnostics, local run metrics |
| CLI/deployment | bind/port/data paths, pack directories, headless fallback config, expert `--control-mode` override |

Provider classes, backend names, raw key-env fields, queue implementation,
plugin kinds, and routing presets do not belong in first use.

## 10. Preserved delight inventory

Every story must name which of these it exercises:

- the Record orb as the obvious capture verb;
- voice-to-fill on the input where work is happening;
- materialize/glow/print moments when a durable object or result arrives;
- spatial Zone memory plus a semantic list/tree alternative;
- lasso/grounded Ask over exactly selected material;
- Persona rail conversations and explicit Keep to Desk;
- local model freedom and per-run destination choice;
- visible lineage/source chips and exact receipts;
- live Coder presence, watch-free/steer-armed consent, and tactile key control;
- Mission Control belt and Qlippy as contextual presence, not nagging;
- platform-native motion, haptics, sheets, keyboard focus, and accessibility;
- honest refusal that names what failed and preserves the user's work.

## 11. Measurable phase outcomes

Targets are based on the source baselines above. HS-92-03 and HS-92-10 must add
real time measurements rather than retroactively inventing them.

| Measure | Baseline | Exit threshold |
|---|---:|---:|
| Product steps before basic first dictation | 6 wizard screens plus physical gesture | ≤3 from Desk arrival |
| LLM placement decisions before basic dictation | 1 backend choice, with optional model/server decisions | 0 |
| Technical nouns taught before first value | at least 5 (`model`, backend choices, runtime/profile language) | ≤2 |
| Primary journeys with Desk entry and durable Desk return/receipt | mixed; meeting/capability/attention paths incomplete | 10/10 |
| Cross-client canonical-term parity in controlled census | not measured; known Recipe/Agent/Profile/Zone drift | 100% for registry-governed UI strings |
| Ambiguous consequential generic verbs | multiple `Run`, `Approve`, `Apply`, `Open` | 0 in primary journeys without adjacent consequence context |
| Silent primary mutation/capture failures | reproduced in Web; capture loss risk on both runtimes | 0 in forced-failure matrix |
| Native meeting classes represented as synced when omitted | meeting omitted but sync/UAT can imply otherwise | 0; all per-object states truthful |
| Hard invariants that vary by ControlMode | mode absent | 0 across full invariant matrix |
| Drag-only/pointer-only primary Desk actions | present on both clients | 0 |
| Actual-client evidence | Web audit complete; Phase 91 Swift/owner gate pending | Web desktop/compact + physical iPhone/iPad owner evidence |

## 12. Deferred candidates after this boundary

- physical normalization of every domain table onto the architectural kernel;
- full executable-graph unification for system and user-authored pipelines;
- third-party plugin sandboxing and marketplace distribution;
- coordinated deletion/compensation across Slack, GitHub, Telegram, backups,
  paired inboxes, and CLI caches;
- fleet administration for many mesh/steering nodes;
- calibrating numeric confidence on a labeled corpus, beyond replacing false
  precision with provenance and review state.

These are not excuses for drift inside Phase 92. The phase still ships the
additive references, destination/authority/receipt contracts needed by its
journeys and records honest compatibility seams for later removal.
