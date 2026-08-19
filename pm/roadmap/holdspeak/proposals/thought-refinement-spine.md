# Proposal — From Thought to Work

> **Status:** owner-directed design proposal; risk analysis complete; not yet
> an implementation charter.
>
> **Recorded:** 2026-08-18.
>
> **Owner direction:** rough speech should enter a continuing AI clarification
> loop, gain explicitly attached context, become richer over successive turns,
> and suggest concrete, tool-backed outcomes such as a bug report.
>
> **Precondition:** Phase 140's first-sentence simplification remains the front
> door. This proposal must not restore the control-room complexity it removed.

## 1. Product thesis

HoldSpeak is not merely speech-to-text and should not become a smarter filing
cabinet. Its regular-user loop is:

```text
capture a rough thought
  → safeguard the original
  → clarify one useful question at a time
  → attach visible context
  → maintain an editable working synthesis
  → suggest a typed result or tool-backed action
  → let the owner accept, edit, defer, or reject
  → execute through existing policy and receipt machinery
```

The AI does not guess once and silently file the fragment. It helps the owner
establish what the thought means. Filing and action become useful after the
thought has earned a shape.

The working phrase is **draft-to-proposal loop**. “Thought compiler” is a useful
design metaphor, not required owner-facing vocabulary.

## 2. Settled product laws

1. **Raw before AI.** Browser storage is only a recovery cache. One server
   transaction must persist an immutable raw snapshot and its first visible
   working Note before the first model call can begin.
2. **Working text is separate.** AI synthesis and owner edits live in a durable,
   revisioned working Note. Accepting proposed text is an explicit owner edit;
   the raw snapshot remains byte-equal and one-tap reachable.
3. **One question at a time, only by owner continuation.** **Keep refining** may
   request the single most useful next question. A model response never starts
   another turn automatically. The owner can answer, edit, attach context, say
   “Good enough,” or leave.
4. **Two kinds of question stay distinct.** A semantic clarification may help
   the thought become useful. Once a tool is selected, required-field questions
   derive from that tool's authoritative schema and say why the field is needed.
   A model must never present an invented preference as a tool requirement.
5. **Context is explicit and visible.** The default attachment set is empty.
   Notes, Artifacts, Meetings, and Knowledge collections are the currently
   hydrated kinds. Each attached qualified ref is shown as a chip, hydrated by
   the server, and named in the receipt. People, drawers, projects, and files do
   not appear until each has real authorization, hydration, deletion, and
   receipt semantics.
6. **Suggestion is not execution.** A model may suggest a result shape or an
   actually available tool. It cannot create authority, invent a connection,
   or execute.
7. **Local and external acceptance stay different.** A local preview binds the
   raw/working/context revisions and becomes an owner-authorized typed service
   write with a stable local write receipt. For an external effect, the first
   durable proposal lifecycle is the existing `ActuatorProposal`; no new record
   duplicates its payload, state, approval, idempotency, audit, or receipt.
8. **Existing authority wins.** External execution uses the existing operation
   policy, posture, actuator proposal/executor, mandatory linked kernel
   admission for this new flow, idempotency, and receipts. This proposal creates
   no second executor or second policy decision.
9. **Failure stays useful.** Missing model, refusal, timeout, unavailable tool,
   or ambiguous external result leaves original and working text editable and
   locally saveable.
10. **Reload resumes, never restarts.** Every nonterminal state returns to the
    same thought, working text, attachments, outstanding question, and proposal
    after browser or hub restart.

## 3. Owner-facing composition

The ordinary Chair gets one primary action: **Develop a thought**. The full
Speak operations console remains an advanced dictation surface, not this loop.
After Phase 140's first Keep, the opened note contains one visible **Develop
this thought** action; the owner does not have to rediscover the generic Chair
verb. Daily captures create the same thought surface directly.

The thought surface has four quiet regions:

1. **Working thought** — the editable synthesis and the primary focus.
2. **One question** — one voice/text answer field with its reason when the
   question is schema-required.
3. **Context** — compact visible chips plus one Attach context control using the
   existing grounding picker.
4. **Next shape** — initially folded; suggestions such as Note, Decision,
   Follow-through, Brief, GitHub issue, or Slack draft appear only when useful.

The working Note appears in Inbox immediately as **Unfinished** and is also
reachable from one **Resume unfinished thoughts** path on the Chair. A persistent
`Original kept · <time/source>` cue reveals the immutable raw snapshot in one
action.

There is one primary action per state. In Working, **Keep refining** is primary
when a model is available; without one, **Good enough** is primary. In a question
state, **Answer** is primary. In a ready/proposal state, the exact local Create
or external Propose/Run action is primary. **Attach context**, **Good enough**,
and other valid exits remain secondary or under one visible More disclosure at
393px. Four equal persistent buttons are forbidden.

**Good enough** marks the current working Note complete, keeps it in Inbox (or
its owner-selected drawer), closes the refinement, and leaves it reopenable as a
normal Note with its Original cue and refinement history. No separate Save as
note decision competes with it because the working Note is already durable.

When a concrete proposal exists, the proposal itself owns Edit, Accept/Run,
Reject, and Retry/Reconcile. Advanced tool setup is not inserted into the
capture loop.

## 4. State machine

```text
COMPOSING_LOCAL (browser recovery cache only)
  ├─ server transaction succeeds ─→ RAW_DURABLE(raw_snapshot, working_rev=1)
  └─ failure/reload ───────────────→ COMPOSING_LOCAL

RAW_DURABLE
  └─ open visible Unfinished working Note ─→ WORKING

WORKING
  ├─ attach/detach context ─→ WORKING (new attachment revision)
  ├─ request refinement ────→ REFINING
  ├─ owner edit ────────────→ WORKING (new working revision)
  ├─ good enough ───────────→ COMPLETED_NOTE + stable local write receipt
  └─ leave/reload ──────────→ WORKING

REFINING
  ├─ proposed synthesis/question ─→ REVIEW_REFINEMENT
  ├─ failure/refusal/timeout ─────→ WORKING
  └─ reload ──────────────────────→ reconcile known invocation to a persisted
                                     review result, otherwise WORKING

REVIEW_REFINEMENT
  ├─ accept/edit ───────────→ WORKING (new working revision)
  ├─ reject ────────────────→ WORKING
  └─ answer question ───────→ REFINING

COMPLETED_NOTE
  ├─ preview Note/Decision ─→ LOCAL_PREVIEW
  ├─ choose external effect → existing ACTUATOR_PROPOSAL
  └─ resume refining ───────→ WORKING

LOCAL_PREVIEW (not an authority lifecycle)
  ├─ source/context revision changed ─→ STALE_PREVIEW with named repair
  ├─ owner accepts ──────────→ typed primitive service write + stable receipt
  ├─ reject/defer ───────────→ COMPLETED_NOTE
  └─ reload ─────────────────→ regenerate from frozen refinement revisions

ACTUATOR_PROPOSAL (existing durable state machine is the first external record)
  ├─ source/context revision changed ─→ refuse with Update proposal
  ├─ missing adapter-required field ──→ WORKING with named requirement
  ├─ owner/posture transition ────────→ existing actuator + linked kernel path
  └─ reject/defer ────────────────────→ existing actuator terminal/deferred state

EXTERNAL_EXECUTION
  ├─ executed ──────────────→ EXECUTED + immutable receipt/link
  ├─ failed/refused ────────→ terminal named result
  └─ indeterminate ─────────→ RECONCILE_REQUIRED; never blind retry
```

A model invocation may have its own durable operation/placement receipt, but its
output cannot advance refinement/product state without an accepted persisted
owner transition.

## 5. Reuse map and required additions

### Reuse

- `FirstWords` proves local recovery cache, caller-supplied stable Note IDs,
  ambiguous-response retry, and staged open. It does **not** prove raw-before-AI
  server durability. Extract the retry/open pattern; do not reuse its
  onboarding/seed/disposition component as daily architecture.
- `durableDraft` remains a composing safety net, never the authoritative shared
  record.
- `AskService` remains the grounded inference authority: server-side ref
  hydration, deployment revision, placement/egress claims, and kept Artifact.
- `GroundingSelection.resources` and qualified refs become the single
  owner-facing Attached context abstraction, beginning only with kinds the
  server already hydrates truthfully.
- `NoteEditor` / `EditorAIProposal` supply the existing explicit Accept/Reject
  grammar, but must target the working draft rather than mutate the original.
- Notes and Desk Decisions are the first typed local outcomes. Artifact authoring
  and generic follow-through creation do not exist today; they require separate
  adapters before they may be offered.
- `ActuatorProposal`, `ActuatorExecutor`, operation policy, kernel admission,
  and receipts remain the sole external-effect path.

### Add

1. A durable refinement record that owns the immutable raw byte snapshot plus
   its hash/source/time, links the visible working Note, and records attachment
   revisions, one-question invocations/results, accepted working revisions, and
   completion. Two ordinary mutable Notes are not sufficient original custody.
2. Optimistic revision/CAS semantics for the working Note; Notes currently have
   timestamps and tombstones but no revision history.
3. Owner-authorized typed local-write adapters for Note and Desk Decision with
   stable request IDs and receipts. The refinement record may retain the preview
   lineage, but it is not a second proposal lifecycle or executor.
4. A narrow availability/schema adapter over real local outcomes and existing
   actuator destinations. No universal tool registry exists today; the adapter
   must not become a generic agent tool router.
5. Direct construction of the existing `ActuatorProposal` for accepted external
   payloads, with mandatory linked kernel admission for this new flow.
6. One receipt projection that presents local result, capability result, or
   actuator/kernel result in owner language without flattening their internal
   safety differences.

### Consolidate or hide

- Merge Ask lasso contexts, grounding resources, and client-side contextual
  action sources into one ref-based Attach context interaction.
- Stop browser-side serialization of authoritative context material for
  capability runs; pass refs and hydrate server-side.
- Keep Rails, Mission Control, global constitutional/workbench context, coder
  routing, and Delivery details out of the ordinary thought loop.
- Do not add a generic chat-thread, planner, agent, tool router, or second
  proposal/executor subsystem.

## 6. Tool truth as of this proposal

| Destination | Current write capability | Law for this loop |
|---|---|---|
| Local Note / Desk Decision | Yes | First typed local outcomes after owner acceptance. |
| Artifact / generic follow-through creation | No general authoring contract | Do not offer until a typed adapter exists. |
| GitHub issue | Yes, through existing actuator proposal | May be offered with a configured/selected repo; local `gh` readiness can still refuse at execution. |
| Slack webhook post | Yes, through existing actuator proposal | May be offered as a draft/proposal. |
| Jira | **No. Read-only CLI enrichment only.** Create, assign, transition, and login are rejected. | May suggest the generic shape “bug report”; must not offer “Create in Jira” until a Jira actuator and secret/authority contract ship. |
| Calendar | **No external write.** Current connector derives local meeting candidates only. | Must not offer external calendar creation. |

Tool suggestions come from the new narrow availability/schema adapter over
actual domain and actuator capabilities, not a model's memory of popular SaaS
products. Current generic capability descriptors and GitHub/Slack request DTOs
are not authoritative form schemas. Required-field clarification does not ship
for a destination until its typed adapter validates and exposes those fields.
An unavailable destination may be named only as an unavailable future
connection, never as a working button.

Future Jira write support is a separate actuator story: authentication/secret
custody, site/project identity, authoritative create schema and custom fields,
payload preview, idempotency/reconciliation, policy mapping, audit, and live
failure evidence must all land together.

## 7. Configuration doctrine

The loop requires no setup to save and edit a thought. Model refinement appears
only when a configured runtime is available; otherwise the working draft and
Good enough remain a complete path to a normal Note.

Connections and destinations should bind to explicit context, not create a new
global setup ceremony. A Work/project context may eventually name a GitHub repo,
Jira site/project, Slack channel, vocabulary note, or team scope. Attaching that
context makes its available tools relevant for that thought. Personal context
does not inherit Work tools.

The only ordinary per-thought controls are attachments and the chosen proposal
destination. Slack uses existing host configuration and GitHub uses host-local
`gh` authentication. Credentials are never copied into Notes, attached context,
model prompts, proposal payloads, receipts, or sync.

## 8. Risk analysis

| ID | Severity | Failure | Required guard | Stop signal / proof |
|---|---|---|---|---|
| R1 | P0 | AI overwrites or loses the owner's raw thought. | Server transaction persists an immutable raw snapshot and working Note before any AI request; browser cache is not authority. | Fault injection before/during/after the transaction/model call; original byte-equal after reload. |
| R2 | P0 | Concurrent edits or retries silently clobber the working draft. | Working revision + expected-revision CAS; explicit conflict recovery. | Two clients edit same revision and both appear successful. |
| R3 | P0 | Hidden or stale context leaks private material to a model/tool. | Default none; visible qualified refs; server hydration; attachment revision frozen per run/proposal. | Any prompt/receipt contains material from an unshown or deleted ref. |
| R4 | P0 | Proposed text is mistaken for an approved local/external action. | Refinement preview; owner-authorized typed local write; existing `ActuatorProposal` as first external lifecycle. | A model response creates domain/external state without an owner/policy transition. |
| R5 | P0 | Retry duplicates a GitHub/Slack/future Jira effect. | Stable proposal and execution idempotency keys; reconcile ambiguous outcomes; never rerun AI on execution retry. | Two remote objects for one accepted proposal. |
| R6 | P0 | Model invents tool requirements, destinations, or successful capabilities. | The narrow availability/schema adapter over real domain/actuator contracts is the only execution truth; schema-required questions are labeled. | UI offers Jira/calendar creation before a real actuator or claims requirements absent from its typed adapter. |
| R7 | P0 | New flow bypasses operation policy, posture, actuator parity, or kernel admission. | Thin adapters only; existing executor remains sole external-effect seam; kernel binding mandatory for this new flow even though legacy actuator execution can run without one. | Any external connector call originates from refinement UI/service directly or lacks the required linked operation. |
| R8 | P1 | Refinement becomes an endless expensive chat. | One question; owner-visible stop; bounded turn/token budgets; compact/restartable history. | No reachable Good enough/Save action or unbounded automatic continuation. |
| R9 | P1 | No model makes the primary product a dead end. | Every state remains editable and locally saveable; model controls disappear/refuse plainly. | Fresh HOME cannot complete capture → save → reopen. |
| R10 | P1 | Context picker repeats current 14-item cognitive wall. | One Attach interaction with search and pinned/recent context; no auto-selection. | Everyday context requires scanning an unfiltered system catalog, especially at 393px. |
| R11 | P1 | A parallel chat/tool/proposal subsystem forks receipts and authority. | Reuse Note → Ask → Artifact → Actuator → Kernel; density/census tests for new execution paths. | A second executor, generic tool router, or UI-only durable proposal appears. |
| R12 | P1 | Abandon/reload loses question, attachments, proposal, or draft relationship. | Durable refinement/link records; restart matrix for every state. | Reload returns to generic Ask/Chair or repeats a model/tool side effect. |
| R13 | P1 | Tool configuration becomes another Models-screen-sized burden. | No setup for local loop; connections contextual and progressively disclosed. | First capture requires Models, connectors, project IDs, or schema forms. |
| R14 | P1 | Tool suggestion outruns source freshness. | Freeze source/working/context revisions; revalidate before proposal acceptance/execution. | Edited/deleted source silently executes an old payload. |
| R15 | P1 | Mobile surface becomes a transcript/chat/context/form stack. | One active region and one primary action per state; folded history/original/proposals; both-width glass gate. | 393px requires horizontal scroll or shows more than one primary decision. |
| R16 | P2 | “Thought compiler” or proposal vocabulary leaks as product jargon. | Owner copy stays develop/refine/context/good enough/create. | Cold owner must understand compiler, grounding, schema, actuator, or revision. |
| R17 | P1 | Original custody exists technically but is invisible, or revision drift yields a mysterious disabled action. | Persistent Original-kept cue; stale preview/proposal names changed source and offers Update proposal. | Owner cannot prove the original survived or cannot explain/repair a refused acceptance. |

## 9. Sequencing and kill criteria

The design must be validated in narrow vertical slices:

1. **Durability keystone:** one transaction creates immutable raw snapshot +
   visible Unfinished working Note; CAS, Original-kept cue, Inbox/Resume entry,
   Good enough, and reload pass with no model. Kill or redesign if this copies
   `FirstWords` onboarding or invents a universal chat table.
2. **One grounded refinement:** one persisted Ask-backed invocation/result,
   Notes plus the seeded Everyday-context Knowledge collection first, visible
   Accept/Reject, owner-triggered continuation, fail-open. Kill or redesign if
   original text can be mutated or browser-copied context becomes authoritative.
   Expand other context kinds only after each resolver proves hydration,
   authority, deletion, and receipt truth.
3. **Typed local write:** Note and Desk Decision only, via owner-authorized
   service adapters and stable receipt. Kill or redesign if domain types are
   flattened into generic JSON or a second proposal lifecycle appears.
4. **One existing external driver:** GitHub issue or Slack proposal through the
   existing actuator/kernel path. Kill or redesign if execution requires a
   second policy decision or duplicate receipt truth.
5. **Jira only after its own contract:** do not simulate it in the refinement
   phase.

Three rounds of defects in one invariant class trigger a design review. Five
rounds surface the remaining rigor/cost choice to the owner, per orchestration
law.

## 10. Proof jobs

The foundation cold job is:

> Capture a rough thought; atomically preserve the original and create one
> visible Unfinished working Note in Inbox; reach Everyday context within one
> Attach interaction; refine only after the owner chooses Keep refining;
> edit/accept the working version; choose Good enough; and reopen the completed
> Note with its Original-kept cue after hub/browser restart. Repeat with no model
> or destination controls and complete the same useful Note path.

The first tool-backed job is:

> Refine a reproducible bug report, select the actually available GitHub issue
> destination with an explicit repository, inspect the exact existing actuator
> preview/payload, execute once through a kernel-linked actuator under the
> current posture, and reopen both source thought and receipts. An ambiguous
> response must reconcile without duplication. A required-field clarification
> is added only after a real typed GitHub schema adapter exists.

Both jobs must pass at 1440×900 and 393×900 with zero console errors or
horizontal overflow. The owner sees the finished glass before merge. GitHub CI
is not watched or used as a gate by owner ruling.

## 11. Held decisions before charter

1. Owner-facing name: **Develop a thought**, **Shape a thought**, or another
   phrase. The architecture must not depend on the label.
2. Whether Phase 141 includes the existing GitHub/Slack external slice or closes
   after typed local writes. Jira remains separate either way.

The custody decision is settled: the working Note appears in Inbox immediately
as **Unfinished**, and the Chair also offers **Resume unfinished thoughts**.

No product implementation begins until these held decisions are resolved in the
charter or explicitly left for the owner sitting.

## 12. Review record

The proposal was written from three independent read-only audits of the current
product and code: structural/reuse and connector truth, live cold-owner
composition at both widths, and state-machine/authority counsel. The first
adversarial review returned AMEND for raw-authority ambiguity, an invented
GitHub schema question, parallel-proposal risk, mobile action competition,
invisible original custody, context-picker overload, and factual capability
overclaims. Each was corrected in this document.

Final verdicts on 2026-08-18:

- architecture and connector truth: **RATIFY**;
- state machine, authority, and risk register: **RATIFY**;
- cold-owner composition and no-model path: **RATIFY**.

These verdicts ratify the design/risk record, not implementation or tool claims
beyond the explicit current-capability table.
