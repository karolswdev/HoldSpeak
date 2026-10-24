# Native-experience design proposal: adversarial review

**DRAFT — local worker advisory invoked by Astra; not Muad'Dib's check.**
**UNCHECKED — awaiting Muad'Dib.** No product code, build, deploy, provider or
native action, owner-state write, test, or acceptance walk was performed.

Scope: review of D1–D10, the seven journeys, the workflow map, both canvas
artifacts, the derived delivery plan, the governing canon, and the relevant
47-family reviews. This is a design check, not a claim that any job was run.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **P1 — The visual packet does not yet make all seven whole jobs concrete.**
   The proposal calls the journeys complete and promises ten desktop/narrow
   compositions (`docs/internal/betterment/native-experience/DESIGN-PROPOSAL.md:19-25`),
   but the canvas packet contains only five paired board groups
   (`docs/internal/betterment/native-experience/design-proposal/CANVASES.md:8-12`).
   Those boards cover J5, J1/J3, J6 Settings, J2 retained Meeting, and a J7
   Components specimen (`CANVASES.md:41-49`). There is no concrete composition
   for J4's Project → Agent/Automation → Result → Project return, for the
   Meeting → Today/Needs → Nudge/Send return, or for the J6 Setup → Engines →
   Accounts → originating-job return. The J7 terminal/feedback loop is text in
   the journey, not a board. The delivery plan confirms that it is deriving
   work from “five canvas boards” (`DELIVERY-PLAN.md:6-10`), while the synthesis
   requires complete jobs and 1440/393 proof, including meeting action/Today,
   account/engine handoff, and selected-source return
   (`adversarial/SYNTHESIS.md:101-118`). This fails Tenets 3, 5 and 7: the
   owner cannot judge the actual Tuesday composition or return focus from the
   static packet.

   **Condition:** add compact desktop/narrow state boards for the missing J4,
   Today/Needs/Send, readiness, and terminal/feedback return scenes, or state
   explicitly that those jobs are text-only design scope and remove the claim
   that the packet has concrete compositions for the complete seven-job set.
   Each added board must keep the current application, operation, source and
   return identities visible; it must not become a global monitor, wizard or
   second stack.

2. **P1 — Source capability and Ask handoff are not bounded tightly enough.**
   The delivery plan proposes the first Ask from “a selected Thought or
   repository source” (`DELIVERY-PLAN.md:114-131`). The source-context review
   records the opposite boundary: the repository object verb is withheld when
   the provider has no `ask` capability, while another Ask path can still admit
   a selected repository id without that guard (`adversarial/source_context.md:36-47`).
   The proposal says Source → Ask carries real material and provenance
   (`DESIGN-PROPOSAL.md:220-227`), and J5 says Ask attachment is distinct from
   Hand (`design-proposal/JOURNEYS.md:217-227`), but neither defines the
   provider capability matrix, the typed unsupported result, or the exact
   source revision/return behavior for a repository file or folder. This risks
   inventing a producer capability and violates Tenets 1, 3, 6 and 7.

   **Condition:** settle the first Ask source as the supported Thought/Project/
   People path, and make repository/file attachment conditional on a declared
   provider `ask` capability. Unsupported or stale repository sources must stay
   selected and show a typed refusal with Back/Retry, never broaden to whole-Desk
   context or silently disappear. Put the qualified source id, revision or
   captured quote, provider provenance and return opener in the map, plan and
   J5/J3 jobs. Any egress badge must be provider-derived rather than a default
   assertion.

3. **P1 — J2 still under-specifies imported-source truth and recovery.** The
   journey now says untimed material is read-only and avoids a fake timestamp
   seek (`design-proposal/JOURNEYS.md:96-124`), but it does not name the source
   filename/format, `real` versus `synthetic` timestamp basis, editable-date
   suggestion, terminal import receipt, or the distinction between `Re-import`
   and summary `Run`. The import review identifies all four gaps: provenance and
   timestamp basis are lost, failed import cannot reacquire its source, dates
   have conflicting semantics, and the import receipt is unspecified
   (`adversarial/meeting_import.md:11-21`). The plan only says “a failed import
   re-imports” (`DELIVERY-PLAN.md:153-158`). The review also notes that import
   may automatically enqueue intelligence under an existing setting, so a
   universal press-`Run` path needs an explicit policy
   (`adversarial/meeting_import.md:23-25`). This fails Tenets 3 and 6 and
   Article VI: a Tuesday user can mistake file time or synthetic cues for
   meeting facts and can retry the wrong operation.

   **Condition:** make the import face show source name/format, provenance and
   `real|synthetic` timing basis; keep source facts after failure; provide
   distinct `Re-import` versus summary retry/Run with one durable import
   identity and receipt; and state whether intelligence is automatic under the
   existing setting or owner-started. Preserve the same Meeting id and return
   route after restart. Do not add a new import wizard or invented capture
   resume.

4. **P1 — J4 compresses existing Hand, launch, result and Gate authority into
   an invented `Start` step.** The journey says `Hand`/`Run`, then “press
   `Start`,” and later “Answer or approve only the wait” while showing only
   `launchId`, `turnId` and last words (`design-proposal/JOURNEYS.md:171-209`).
   The active Hand surface has different paths and labels (`Hand`, `Launch`,
   and `Start when one is free`) and distinct queued-delivery behavior
   (`web/src/desk/components/HandSheet.tsx:405-458,641-656`;
   `adversarial/agent_hand.md:55-62`). The result review requires
   `launchId + sessionKey + turnId`, authoritative worktree/used/last-word
   facts, durable New/seen and close/reopen, and separate answer versus Gate
   approval/recovery semantics (`adversarial/agent_result.md:21-29,33-65`).
   This fails Tenets 1, 3, 5 and 7: a worker could add a confirmation verb or
   monitor that is not the existing authority, and the owner could not tell
   “not delivered” from “delivered but not read.”

   **Condition:** use the exact existing verb for each path; define the visual
   sequence as preview → owner-authorized Hand/Launch or queue → cancel/refusal
   → result. Retain source/target, account/engine/egress, branch/worktree,
   `launchId`, `sessionKey`, `turnId`, used/changed resources, review result and
   receipt. Keep `Answer`, `Approve/Deny`, `Stop`, `Resume` and `Hand again`
   distinct, with New/seen and terminal-gone/unknown states. Reuse Conductor,
   Lane/ResultBlock and terminal authority; do not introduce a universal run
   monitor.

5. **P1 — `feedback` still conflates two different user jobs.** The workflow
   map defines it as operation outcome feedback and names Process, Send, Ask and
   Needs as consumers (`design-proposal/WORKFLOW-MAP.md:115-121`), while J7
   only says to capture window state plus screenshot/audio/transcript and return
   (`design-proposal/JOURNEYS.md:286-328`). The feedback review says these are
   distinct jobs: the current `UiFeedbackHost` saves a bundle, captures
   screenshot/audio, and retries transcription, whereas ProcessCore is the
   operation ledger; it requires both contracts and their own return/recovery
   evidence (`adversarial/feedback.md:10-27,33-50`). The plan's “second feedback
   consumer such as Send or Process” is also not a settled consumer choice
   (`DELIVERY-PLAN.md:248-265`). This fails Tenets 2, 3, 5 and 7.

   **Condition:** retain the existing feedback family without creating a second
   service, but map both responsibilities explicitly: user-report capture
   (host/window generation, selected state, screenshot/audio, saved bundle id,
   transcription route, cancel and ASR-only retry) and operation outcome
   (target, egress, receipt, unknown/retry and return). Name the first real
   operation consumer and its first/second convergence consumer instead of
   “such as.” Keep a failed report from changing the domain operation result or
   stealing the originating window.

6. **P1 — Convergence order is not one settled falsification sequence.** P01
   says the second real consumer is “Settings or the Thought workspace,” while
   P03 calls Thought first and Settings second (`DELIVERY-PLAN.md:45-59,92-109`).
   P04 likewise permits Ask to start from either Thought or a repository source
   (`DELIVERY-PLAN.md:114-127`), and P10 leaves its second feedback consumer as
   “such as Send or Process” (`DELIVERY-PLAN.md:248-261`). This makes “reuse
   earned by a second consumer” a future choice, not a design decision. The
   source strategy explicitly calls for resource, Settings and active Thought
   to falsify the shared contract before broad rollout
   (`adversarial/SYNTHESIS.md:101-112`). It fails Tenets 1, 3, 5 and 7.

   **Condition:** publish one order and one first/second consumer table across
   D10, P01/P03/P04/P10, the workflow map and the canvas notes. My recommended
   order is RepoWindow read/inspect first, Settings as the unlike revision
   consumer, active Thought as the editor/IME counterexample, then Ask/source;
   the owner may choose another order, but workers must not choose it during
   implementation. Name ProcessCore and UiFeedbackHost separately for the two
   feedback jobs. Components remains fixture-only and never counts as the second
   production consumer. Also correct the malformed dependency phrase “P08
   You/P03 input” (`DELIVERY-PLAN.md:33-35`) before briefing a worker; it is not
   an actionable order.

7. **P1 — Native input is described as a shared contract but not yet as
   per-consumer policy.** D5 correctly retains native inputs, CodeMirror,
   IME/undo and target generation (`DESIGN-PROPOSAL.md:156-177`), and J1 binds
   the active Thought caret (`design-proposal/JOURNEYS.md:60-83`). It does not
   settle the required `replace` versus `append` versus selection/caret policy
   for Thought, Ask/Thread, Settings fields and retained editor paths. The
   native-input review identifies those as different active contracts and warns
   that a universal caret adapter would be wrong (`adversarial/native_input.md:9-23`).
   Speech review likewise requires target binding at Talk release and a named
   stale-target recovery (`adversarial/speech_dictation.md:9-21`). This fails
   Tenets 1, 3, 5 and 7 if a future shared seam silently overwrites a field or
   replaces the active Thought writer.

   **Condition:** add a small consumer table before implementation: active
   Thought/CodeMirror selection replacement and undo; Ask/Thread composer
   append and request snapshot; Settings replacement-field writer/revision;
   retained legacy editor only where still supported. For each, state Talk
   release binding, IME guard, late-result refusal/recovery, focus return and
   receipt. Keep the active ThoughtWorkspaceWindow and Settings writer as the
   authorities; do not create a generic editor runtime.

CONDITIONS: Resolve the seven conditions above in the proposal packet and
derived plan before a worker brief or implementation: add or explicitly bound
the missing visual return scenes; publish source/provider capability and
per-consumer input tables; close import provenance/re-import semantics; use
existing Hand/result/feedback authorities and exact labels; and settle the
first/second production-consumer order. Keep all artifacts DRAFT/UNCHECKED
until Muad'Dib checks them. These are design clarifications, not a new approval
rail or authorization to build.

MISSED:

1. Highest cost: the owner still cannot inspect the J4 and Today/Needs/Send
   return compositions at 1440/393, even though the journeys claim those jobs.
2. Repository/file Ask capability and source revision gating can produce a
   misleading source handoff if not made explicit.
3. Feedback capture versus operation outcome can lose either the saved report
   bundle or the operation receipt/return if treated as one state machine.
4. Meeting import provenance and re-import semantics remain a trust failure
   for untimed or failed files.
5. Exact agent result/Gate and per-consumer input semantics are still easy to
   flatten into a generic monitor or editor.

TUESDAY: Not yet—the packet has credible text paths and good domain boundaries,
but the owner cannot judge several required return scenes or trust the
provider, feedback, import and delegated-result boundaries from the current
visual/design record.

UNKNOWN: No tests, builds, browser shots, live Desk walk, provider/native
operation, owner-state access, assistive-technology/performance run, or owner
acceptance was performed. Static HTML was read as a proposal only. This worker
authored JOURNEYS.md and therefore did not independently audit that file; Root
and the canvas/workflow reviewers must independently inspect it. This report is
the local worker advisory invoked by Astra, never Muad'Dib's check.

## Fixes re-check — 2026-10-23

**DRAFT — local worker advisory re-check invoked by Astra; not Muad'Dib's
check.**
**UNCHECKED — awaiting Muad'Dib.** This is the one permitted fixes re-check;
the initial findings and dissent above are retained verbatim.

RECHECK VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Initial finding 1 is closed.** The canvas packet now declares nine paired
   desktop/narrow groups (`design-proposal/CANVASES.md:8-13`) and maps F–I to
   the missing J4 result return, Meeting → Today/Needs → Send, readiness
   handoff, and ProcessCore/UiFeedbackHost return scenes
   (`design-proposal/CANVASES.md:50-54`). The HTML contains actual desktop and
   393 compositions for those groups (`design-proposal/CANVASES.html:430-540`),
   including source identity, result/session facts, frozen Send bytes, readiness
   authorities, receipts and origin return. The original packet-size finding
   remains above as historical dissent; this re-check condition is satisfied.

2. **Initial findings 2–7 are closed by the fixes.** The provider/source
   capability matrix now makes Thought/Project/People the supported first Ask
   path and requires a declared provider capability, qualified material and
   provenance for repository/file Ask; unsupported or stale sources retain
   selection and return (`DESIGN-PROPOSAL.md:252-261`; `JOURNEYS.md:248-259`).
   J2 now records filename/format/provenance, real versus synthetic timing,
   editable suggested date, terminal receipt, `Re-import` versus summary
   `Run`, and the current auto-queue policy (`JOURNEYS.md:101-140`). J4 now
   uses the existing `Launch`/`Start when one is free` paths and retains
   launch/session/turn/result facts, `Send again`, Answer, Gate and
   Stop/Resume boundaries (`JOURNEYS.md:191-227`). Feedback separates
   ProcessCore outcome from UiFeedbackHost report capture, saved bundle,
   cancel fencing and ASR-only retry (`JOURNEYS.md:315-355`;
   `design-proposal/WORKFLOW-MAP.md:118`). D5 names per-consumer replacement
   and append policies and binds web/native targets at Talk release
   (`DESIGN-PROPOSAL.md:171-193`). D10 and the plan now publish one explicit
   convergence sequence and named first/next consumers
   (`DESIGN-PROPOSAL.md:345-358`; `DELIVERY-PLAN.md:45-54,122-125,262-269`).
   The malformed P08/P03 ordering and open “such as” consumer choices are no
   longer present. These conditions are satisfied; their original objections
   remain above for auditability.

3. **New — P10 has a contradictory consumer statement.** The plan calls
   “the first P01/P02 production pattern in Components” a real consumer, then
   says “Components remains fixture-only” and later says it uses a fixture
   adapter (`DELIVERY-PLAN.md:262-269`). That wording can brief a worker to
   treat the reference as production adoption, contrary to the Components
   boundary and the explicit fixture-only rule (`CANVASES.md:50`;
   `DESIGN-PROPOSAL.md:355-356`). This fails Tenets 1, 3 and 5 if left
   unresolved.

   **Condition:** name the first real consumer as the actual P01/P02 surface
   (for example RepoWindow), and describe Components only as the fixture
   mirror of that already-settled seam. Do not count it as a second production
   consumer or adoption proof.

4. **New — several in-frame canvas labels are UI prose.** The journeys state
   that faces use labels and verbs rather than help paragraphs
   (`design-proposal/JOURNEYS.md:16-19`), and UX-CANON makes a sentence on a
   face a defect (`docs/internal/UX-CANON.md:60-64`). The added static boards
   nevertheless paint explanatory sentences inside app frames, for example
   “Both location and selection stay in place” and “Retry stays local”
   (`design-proposal/CANVASES.html:342,358`), “Source and composer remain in
   place until a profile, engine and account are selected”
   (`design-proposal/CANVASES.html:498`), and “Capture does not change the
   operation ledger or steal focus” (`design-proposal/CANVASES.html:524`). The
   artifact is static, so this is not
   a product-code violation, but it makes the proposed face contradict the
   governing language rule and obscures which words are actual UI labels.

   **Condition:** before owner/Muad'Dib ratification, either move explanatory
   sentences outside the app frames as canvas annotations or reduce in-frame
   copy to ASD-STE100 labels, states, names and one-line empty-state facts.
   Keep the recovery identity visible without turning the face into a manual.

CONDITIONS: Initial conditions 1–7 are satisfied by the current packet. Before
the artifact can be ratified or used for a worker brief, resolve the P10
Components consumer wording and classify/reduce the in-frame canvas prose.
Keep all artifacts DRAFT/UNCHECKED until Muad'Dib checks them; this report
does not authorize implementation.

MISSED: The highest remaining design risk is the P10 wording, because it can
turn a fixture into a false production-consumer claim. Next is the canvas
copy boundary, because the owner may read explanatory sentences as shipped
UI. The static packet still does not prove real provider, editor, feedback,
native, or persistence behavior.

TUESDAY: Conditionally—the required return scenes are now judgeable at both
widths, but the two wording conditions must be resolved before the face can
be treated as a trustworthy implementation brief.

UNKNOWN: No tests, builds, browser shots, live Desk walk, provider/native
operation, owner-state access, assistive-technology/performance run, or owner
acceptance was performed. Static HTML and Markdown were inspected only. The
self-authored JOURNEYS.md limitation remains: this worker cannot provide an
independent author review of that file; Root and the canvas/workflow reviewers
must do so. This remains a local worker advisory invoked by Astra, never
Muad'Dib's check.

## Astra disposition after the one fixes re-check

The reviewer's final two wording conditions above are preserved. Astra then
corrected P10 to name RepoWindow as the production consumer and Components
only as its fixture mirror (`DELIVERY-PLAN.md`, P10). This is not a claim of
production adoption.

Astra moved explanatory copy out of the app frames, retained actual document/
answer content and concise state labels, separated Answer from alternative
Gate/Resume states, and separated a fresh prepared Send from its unknown
outcome variant. The initial narrow-window stacks clipped their controls;
they were replaced with one useful primary window plus explicit return and
external scene context. Setup now illustrates a Local text engine profile,
not an owner/speech profile; Accounts remains optional source/destination
identity. Browser bounds and visual inspection are checks of these static
illustrations only. No third worker review round was requested.

The proposal's execution-tracking section names the present draft position
and ties later package slices to journey/workflow IDs, PRs, task evidence and
owner feedback. Existing TRACKER and pm/STATUS keep their separate meanings.
No recipe or owner-acceptance state is promoted by this record.

The two wording conditions are addressed in source. Muad'Dib's check, real
producer/native/assistive-technology behavior, whole-job walks, performance
and owner visual judgment remain open. The packet is DRAFT/UNCHECKED and no
implementation was started. The local advisory is not Muad'Dib's check.

### Root verification of this draft

- Local navigation: 11 Markdown files passed `scripts/check_docs.py`.
- Trace reconciliation: exact 47 inventory IDs, 47 individual review links,
  47 primary-package joins, seven journey coverage groups and ten package
  assignments agree.
- Static canvas: 18 artboards rendered in Chromium 143.0.7499.4 under isolated
  HOME and the shared test lock: nine 1440×900, nine 393×852. Window and frame
  control bounding checks reported no overflow after the narrow corrections.
  Root inspected the scene images in `.tmp/design-proposal/`; these are local
  working previews, not production screenshots or committed evidence assets.
- Rendered HTML SHA-256:
  `01bc6e8fcc3918925023f48cdcf890e2549b493de0c061f110ce73aef8207530`.

Bounds are not pixel or craft acceptance. Some gallery captures show clipped
head text despite the measured bounds; capture/paint and final chrome remain
visual review points. No production browser task, hardware/OS behavior,
provider effect or owner acceptance is inferred from the static gallery.
