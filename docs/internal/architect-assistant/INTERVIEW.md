# Repeatable interviews: from intent to a working setup

Status: proposed design, version 0.2, 2026-09-05. Requirements: AA-IVW-001–AA-IVW-018 in [SRS](SRS.md). Behavioral proof: AC-30–AC-38 in [ACCEPTANCE](ACCEPTANCE.md). This is a product and implementation recipe; proposed contracts below are not installed APIs.

## 1. Product intent

The owner can describe their work, explore possibilities with an LLM, and turn a useful suggestion into a tested configuration through the same conversation. They can return whenever their goals, projects, relationships, or responsibilities change. The interview is a continuing way of operating HoldSpeak, available inside the existing Desk.

An interview may begin with “Help me get started,” “Let's revisit my projects,” “What should I automate?”, or “I keep becoming the bottleneck for decisions.” It should establish enough context to deliver one useful outcome, then offer a next step. Completing a comprehensive profile is never a prerequisite for value.

The LLM contributes adaptive questioning, synthesis, and creative suggestions. A deterministic controller governs saved state, permitted transitions, argument validation, execution authority, and verification. MCP exposes discoverable capabilities and tool calls; the application supplies the domain semantics and durable workflow. The [MCP tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) defines discovery, input/output schemas, and invocation without prescribing a particular conversational interface.

## 2. Independently repeatable sections

| Section | Questions that matter | Useful result and canonical destination |
|---|---|---|
| Goals | What should improve? For whom? By when? What would count as progress? | User-stated outcomes, constraints, and review criteria linked to existing Projects or a scoped Note/Thought. Hypothesized goals remain suggestions. |
| Projects | Which streams matter now? Which already exist? Where is their evidence? | Reused or deliberately created Project, verified source scope, and useful initial view through Project setup/services. |
| Things you care about | What needs attention? What is a meaningful change? What is noise? | Scoped attention preferences and candidate Watch rules, with explicit observation limits and source freshness. |
| Cadences | What do you repeatedly prepare, review, chase, or summarize? How often is useful? | Manual recipe or supported recurring configuration with time zone, output destination, and test result. Scheduling depends on the actual R3 capability. |
| People related to a topic | Who contributes, decides, reviews, or depends on this? What shared commitments matter? | Explicit relationships and permitted shared-intent preparation through People services; organizational authority is user/source supplied. |
| Decision log | What was decided, why, by whom, against which alternatives? What remains open? When should this be revisited? | Linked existing decision records, draft decision packets, unresolved questions, and supported review triggers. A draft is never silently promoted to an accepted organizational decision. |
| Working style and delegation | What should be prepared for you? What do you want to direct manually? What effects may a configured agent perform? | Preferences, manual recipes, and, when available, bounded Assignment/automation proposals using the R2/R3 contracts. |
| Sources and models | Which missing prerequisite prevents this particular outcome? | A precise setup handoff and proof of a compatible model/source, surfaced only when needed. |

Sections share qualified references and authorized facts. They do not maintain separate editable copies of a Project, person, decision, or commitment. In this baseline there is no established universal `goal.*` tool family: retain goals in existing scoped records, adding a typed facet only where implementation review finds a genuine storage gap.

There is no required section order. From a Project Room, “Revisit what I care about here” starts with that Project. From a decision, “Help me understand when we should revisit this” starts with the selected record. An owner may jump sections, skip a question, resume later, finish early, or use the existing direct controls.

## 3. The conversation and its durable state

The session has a stable ID, revision, descriptor versions, selected section, target references, and an interaction cursor. The transcript is a view of events; it is not the database from which configuration must be reconstructed on every turn.

| State component | Required semantics |
|---|---|
| Facts | Value, scope, source reference or user-turn provenance, observed/confirmed time, revision, disclosure class, and status: stated, observed, inferred, unknown, declined, or stale. User-stated preference does not imply permission to execute. |
| Questions | Purpose, facts sought, answers already supplied, skip/snooze state, and why an additional answer matters to the current outcome. |
| Suggestions | Stable ID/revision, goal connection, reasoning, supplied evidence or hypothesis labels, dependencies, disposition, and feasibility. |
| Proposed change | Exact target and observed revision, before/after effect, prerequisites, destinations, actual capabilities, applicable posture, and verification plan. |
| Operations | Command identity and payload digest, admitted operation references, receipts, actual read-back evidence, and unresolved effects. |
| Continuation | Pending question or handoff, completed steps, unresolved gaps, relevant canonical revisions, and what the user can do next. |

Suggested session states are `exploring`, `ready`, `applying`, `verifying`, `complete_for_scope`, `needs_input`, `paused`, `partial`, and `abandoned`. Completion means the selected outcome has its required evidence, or an explicitly chosen draft/manual result is kept. It does not mean every section is complete or every future automation is active.

The controller accepts typed events such as `AnswerRecorded`, `FactCorrected`, `SuggestionSelected`, `PlanPrepared`, `OperationObserved`, and `VerificationRecorded`. A versioned reducer determines legal transitions. Replaying the same accepted events against the same recorded inputs produces the same state and no repeated effect. Fresh model calls may produce different language and proposals; temperature settings are not a determinism guarantee.

Bound the model loop by turns, tool attempts, elapsed time, and applicable usage limits. Finish at a useful stopping point or ask for the next material input. A model timeout preserves accepted facts and the last recoverable step.

## 4. Intelligent interviewing

The model receives the selected section's purpose, authorized relevant facts, available capability summaries, unresolved questions, and prior suggestion dispositions. It asks the next question most likely to change the proposed outcome, usually one question at a time. It can follow an unexpected answer, connect sections, challenge an assumption, or offer concrete alternatives. It should explain a requested detail when its relevance is not apparent.

Extracting a fact from an answer produces a typed proposal that the controller validates. Ambiguous names resolve against actual records. “Alex owns this” may establish the user's statement about a responsibility; it cannot silently establish formal approval authority or select among several Alex records. Low confidence must not be converted into an invented fact merely to complete a form.

Do not re-ask known unchanged facts. Ask a targeted clarification when a correction changes scope, creates a conflict, or invalidates a consequential plan. Treat “skip,” “not now,” and “stop suggesting this” as meaningful dispositions. Store the minimum needed preference under the applicable retention rules, and make it inspectable and changeable.

Users can inspect “What this interview knows,” correct facts, remove optional preferences, and see which suggestions depend on them. Removal uses the owning service and invalidates derived context; it does not promise erasure of independent authoritative records.

## 5. Suggestions that earn their place

The LLM may invent useful combinations beyond a preset list. A goal to reduce decision bottlenecks, three related Projects, recurring review meetings, and stale decision records could support a proposal for a cross-project unresolved-decision brief. The connection is a hypothesis about usefulness until the owner assesses it.

Each suggestion includes:

1. The expected benefit and the user-stated goal or concern it addresses.
2. The evidence, preference, or explicit assumption behind the recommendation; contrary evidence and missing coverage where material.
3. A concrete behavior: trigger or manual entry, inputs and scope, output, destination, and allowed effects.
4. Setup needs, likely attention burden, available usage estimates, and uncertainty. No invented hours saved or unsupported cost guarantees.
5. Feasibility: `ready_to_prepare`, `needs_input`, `needs_connection`, or `unsupported_idea`. Preparing still validates current authority and runtime support.
6. The available next action: try once, edit, configure, keep as an idea, defer, or dismiss, limited to implemented operations.

Show at most three suggestions initially, with access to more. Prefer relevance and usefulness over the number of automations installed. A suggestion can recommend fewer notifications, a manual decision practice, or retiring a redundant recipe. Dismissed suggestions do not recur without a material new reason or an explicit request to reconsider them.

Separate generating candidate ideas from preparing executable plans. The model can propose an unsupported integration as an idea; it cannot invent a tool name, connector scope, successful source read, or configured schedule to make the idea look available. An empty decision log supports an invitation to capture decisions, not a claim that the organization has no decisions.

## 6. Capability discovery and execution

Build a section-specific tool palette from the live application's registered capabilities, available services/adapters, authenticated principal, and applicable policy. Reuse MCP schemas for model calls. Add reviewed application metadata describing domain purpose, prerequisites, actual effects, record ownership, idempotency, verification, privacy, and repair paths. Tool names and third-party annotations alone cannot establish these semantics.

The palette carries a catalog revision/digest. Preparing a plan resolves exact tool versions, canonical targets, and preconditions. Before an effect, recheck any relevant capability, scope, policy, or record revision that may have changed. Invalidate a stale plan and describe the material change. Missing services or live callbacks produce an honest unsupported result.

Within HoldSpeak, use the common registered capability/domain-service path with the live principal and kernel admission. External clients can use MCP transport over the same contracts. Do not route a restricted in-app request through the local owner-identity stdio sidecar to acquire greater authority. Synchronous family dispatch is not automatically suitable for an existing async event loop.

The model proposes typed next steps: ask, read, suggest, prepare, apply, verify, hand off, or finish. The controller validates arguments and state before dispatch. Source documents and tool outputs remain data; they cannot enlarge the palette, alter policy, or authorize effects. A schema-valid call is still subject to business preconditions and actual authority.

“Use the Friday version for this Project” can supply the owner intent for the exact displayed proposal under existing policy. Bind that intent to its revision and scope. “Interesting” records interest; it is insufficient to infer an unspecified schedule or destination. Reuse existing owner authorization and control posture; do not add a second approval ceremony to a deliberate Configure action.

## 7. Configuration, proof, and recovery

Preparing exposes the meaningful before/after change: Project, source scope, frequency/time zone if applicable, output, destination, and effects. Technical receipts are available through disclosure, not inserted into ordinary interview questions.

Apply steps through the owning services, persisting intent before dispatch. Domain operations retain their existing transaction boundaries. A sequence spanning Project setup, a model route, and a schedule is not one global atomic transaction. Record each committed step and reconcile after interruption; use compensation only where supported and authorized.

Verify actual behavior with the appropriate bounded source test, compatible model attempt, saved-record read-back, and one first result where applicable. A model saying “done” or a successful transport response is insufficient. A successful source read with zero matching items may be valid; distinguish that from unavailable coverage and explain its value limit.

For a recurring recipe, read back enabled state, exact scope, next trigger, effective authority, and destination. Keep “saved draft,” “configured,” “first result verified,” and “scheduled occurrence verified” distinct. R1 can produce a useful manual recipe; it must not imply R3 reliability.

Retries reuse command identity only for the same semantic payload. A changed payload conflicts or gets a new explicit revision. Following a lost acknowledgement, reconcile persisted operation state and owning records before retrying. If the service cannot establish whether an external effect occurred, retain `partial`/indeterminate and require resolution before repeating it.

Closing or abandoning the conversation does not undo committed configuration. Show what remains active and provide its actual pause/disable action. A reopened session resumes from evidence, not by replaying its chat as new commands.

## 8. Revisiting any section

On entry, load the selected canonical records and compare relevant revisions with the previous interview. Summarize known context and the change under discussion. Editing “daily” to “weekly” updates the identified recipe, preserving lineage, instead of creating another one.

Use stable target identity and domain uniqueness rules; names are search aids. If several recipes or people match, resolve the ambiguity before a dependent mutation. Changes made through direct controls or another session are first-class updates. Rebase proposed changes against them, and invalidate suggestions whose goal, source access, or assumptions no longer hold.

Interviews may suggest a future review date. Automatic re-interview prompts need an enabled cadence and attention policy. Merely completing an interview does not authorize recurring interruptions.

The Project setup service currently expires transient setup sessions after 24 hours. Reuse its lifecycle for the current setup attempt; store durable cross-session preferences and interview continuation separately. If its session expires, create/reconcile a new attempt against canonical state, then revalidate proposals and tests. Never stretch an expired setup ID into permanent user memory.

## 9. Privacy and missing prerequisites

Partition context before capture persistence, prompt construction, and tool invocation. The ordinary Thread/Desk data plane must not receive leader-private People answers for later redaction. Route a protected section through an existing permitted People flow, or avoid soliciting protected content there. Use opaque references and content-free continuation metadata across boundaries where allowed. Shared-intent People MCP tools do not expose the entire protected domain.

Cross-section suggestions use only context available to that session and model destination. They must not reveal hidden relationships, personal judgments, or protected notes through a generated brief, suggestion rationale, embedding, or debug record. No personality scoring or inferred authority.

With no compatible LLM, retain a minimal deterministic interview: capture intent, choose a relevant section/target, show the known missing prerequisite, and hand off to the existing Models surface. Adopt Concierge where integrated and verified. Resume after an actual compatible probe. Creative suggestions become available when the model runs; initial capture does not depend on the LLM configuring itself.

Authentication, operating-system permissions, or unsupported operations may require an existing native UI/CLI/browser handoff. Preserve the continuation and verify the resulting capability. Do not ask the user to paste credentials into the chat.

## 10. Reuse and the concrete gaps

| Inspected seam | Evidence and implementation disposition |
|---|---|
| [ProjectSetupService](../../../holdspeak/services/project_setup_service.py) | Durable outcome/signals/proposals/review stages; selected source proposal tests; atomic Project/Watch finalization. Compose it as the Projects section. |
| [Project MCP family](../../../holdspeak/mcp/families/project.py) | `project.setup.start/resume/answer/suggest/finalize` exist. Service-level proposal selection/deselection/testing and repo clarification lack equivalent setup-proposal MCP verbs in this baseline roster. Complete coverage with shared validation. `project.watch.test` tests an existing Watch and cannot replace testing a setup proposal. |
| [Thread schemas/executor](../../../holdspeak/services/thread_tools.py), [mode palettes](../../../holdspeak/services/thread_modes.py) | `tool_schemas_for` already converts registered MCP schemas for model calls. Ordinary palettes exclude project/provider tools; the Project tool set is empty at this baseline. Add an explicitly scoped interview palette through actual capability admission. |
| [MCP registry](../../../holdspeak/mcp/tools.py) | Reuse schemas and service composition. Audit each selected family’s validation, async behavior, and live adapter availability; registry membership alone is insufficient. |
| [Cadence](../../../holdspeak/mcp/families/cadence.py), [reactions](../../../holdspeak/mcp/families/reactions.py) | Cadence and Watch/Reaction operations exist with particular semantics. They are not a universal cron API. Some apparent reads, including configured `cadence.get_loop`, may invoke a model. Legacy Watches and Project setup proposals require their own correct adapters. |
| [People](../../../holdspeak/mcp/families/people.py) | Content-free readiness and shared-intent relationship/1:1/agenda/commitment paths exist. Protected setup and content need their existing disclosure boundary and supported handoffs. |
| Decision tools in [MCP registry](../../../holdspeak/mcp/tools.py) | Decision-record list/get/search and creation from meeting/Desk paths exist. Audit support for each requested revision/review operation rather than inventing a generic decision-log update tool. |
| [MCP sidecar contract](../../MCP_SIDECAR.md) | Local stdio runs as owner and lacks selected live reply/process callbacks. Preserve identity and advertise gaps when designing in-app or external execution. |
| Incoming Concierge/Heartbeat | Observed in the other development checkout, as documented in [BASELINE](BASELINE.md). Integrate and prove relevant setup/schedule capabilities at the selected runtime; do not claim them deployed from disk presence. |

The practical claim is “many reusable domain capabilities already exist.” Complete the selected interview's real business path before calling it executable end to end.

## 11. A worked conversation

Illustrative scenario, not a claim about Karol's actual records:

> **Owner:** My goal is to stop being the bottleneck for every architecture decision.
>
> **Interview:** Which part takes most of your time: reconstructing context, deciding who should decide, or chasing follow-through?
>
> **Owner:** Reconstructing context, mostly for the migration and platform projects.
>
> **Interview:** I found these two matching Projects. The migration Project has linked decisions; the platform Project has source coverage gaps. I suggest a decision brief that collects open questions, relevant changes, and the last recorded rationale. We can try it once, then decide whether a cadence helps.
>
> **Owner:** Try migration first. I'd want it before Friday's review, not every day.
>
> **Interview:** I'll prepare the migration brief using its selected sources. The proposed recurring version is Friday at 09:00 in your configured time zone, saved in that Project. It would prepare a draft and leave decisions to you.

The exact proposed schedule is visibly a proposal until the owner selects it or gives an unambiguous instruction covering it. If time zone or review time is unknown, ask before preparing that recurring change. The manual trial can proceed independently with sufficient existing intent.

The controller resolves actual Project/decision/source records, validates the plan, generates and keeps a real brief, and checks the owning record. If scheduling is unsupported, it keeps a manual recipe and names that gap. If the owner configures a supported recurring version, the controller applies it and reads back its next trigger. A later “move that to Thursday afternoon” revises the same identified configuration, resolving the exact time if necessary.

The same interview could subsequently suggest linking a decision owner, preparing a permitted 1:1 agenda, or testing a delegation recipe. Each suggestion has its own evidence and scope; none follows automatically from accepting the first brief.

## 12. Implementation recipe and extension contract

1. **Audit one complete path.** Choose one existing Project, one stated goal, and one useful manual decision brief. Inventory the actual read, prepare, write, and verify operations; close missing MCP/common-service coverage before exposing them to the model.
2. **Implement durable coordination.** Add the versioned interview reducer, events, scoped fact references, proposal/plan revisions, operation links, and resume/rebase behavior. Keep canonical domain writes in their owning services.
3. **Add the model adapter.** Use typed outputs and the curated tool palette for adaptive questioning and suggestion generation. Validate semantics, preserve failures, and separate proposed next steps from admitted effects.
4. **Compose the existing Desk interaction.** Provide section entry, conversational input with voice, facts/suggestions/change preview, continuation, and actual results through existing primitives. Keep direct controls reachable.
5. **Prove the first useful result and repeat.** Finish the selected manual setup, revisit it with a changed preference, interrupt midway, and demonstrate no duplicate effect. Add supported scheduling only behind its own R3 proof.
6. **Extend sections and evaluate usefulness.** Add Goals, Projects, Attention, Cadences, Decision log, People, and Delegation descriptors progressively. R1 supports discussing all sections and producing honest drafts/handoffs; R2/R3 effects remain gated by actual capabilities.

A versioned section descriptor declares purpose, entry context, question anchors, fact schema and provenance, canonical owners, privacy class, capabilities/preconditions, proposal and verification templates, completion evidence, and migration behavior. Sections may use custom domain adapters where their semantics differ. Adding a section should require a descriptor, any missing domain adapter, and acceptance fixtures—not another conversation engine. Descriptor changes cannot silently broaden existing authorization or execute saved proposals.

Quality evaluation covers cold start, changed goals, repeated interviews, ambiguous people/projects, missing sources/models, conflicting records, protected context, unsupported ideas, and stale plans. Mechanical tests establish determinism and recovery; live owner judgments establish whether suggestions are useful. Both are needed before describing this as a daily helper.
