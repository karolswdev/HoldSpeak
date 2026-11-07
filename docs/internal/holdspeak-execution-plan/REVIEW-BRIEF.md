# HoldSpeak research direction review

**Current direction remains a coherent technical-life hub, evolved surgically across frontend and backend.** The two jobs are project/repository/delivery work and engineering-organization leadership. The owner has confirmed that purpose, not particular feature mergers, module moves or implementation. The latest instruction authorizes detailed Markdown planning. Start with the [ordered plan](EXECUTION_INDEX.md), then the assigned slice; [product vision](PRODUCT-VISION-AND-JOURNEYS.md), [target proposal](NEXTGEN-TARGET-PROPOSAL.md) and [decisions](DECISIONS.md) are supporting context.

## What the accumulated evidence changes

The stronger diagnosis is no longer just “some files mix responsibilities.” Several useful producers, transactions and controls already exist, but their evidence or identity does not always survive into the next UI or orchestration decision. Moving folders alone would leave those gaps intact.

**Recommended emphasis for review:** establish the meaning and owner of each important transition first, then choose the smallest interface or placement change that makes it reliable and easy for an agent to understand. Common questions are useful; a common workflow engine, universal work-item model or new platform is not justified by these findings.

## Three boundaries worth designing together

### 1. Recorded evidence is not always current permission or readiness

The latest [human-review trace](NEXTGEN-JOURNEYS-AND-NAVIGATION.md#human-review-appendix-recorded-approval-versus-current-review-state-1500-follow-up) finds that PR receipts already reflect newer review information, while a Program's remembered approval can skip later requested-change handling during a wait. The design question is the freshness policy for the existing gate, not whether to build another GitHub ingestion system. Preserve reviewer feedback, distinguish unavailable reads from actual changed reviews, and keep GitHub's own protections independent. No unwanted merge was observed.

This sharpens earlier distinctions: a numeric spending field is not evidence of an enforced cap, dependency readiness is not proof of a fresh starting tree, and a night-planning bound is not a filesystem sandbox. These need explicit domain contracts, not a single generic “ready” flag. Existing Automation/CLI budget transport, exact checkpoints, same-worktree continuation and authorized-writer controls remain valuable. See the [bounded journey evidence](NEXTGEN-JOURNEYS-AND-NAVIGATION.md) and pending D20/D23/D25.

### 2. One user operation can cross multiple durable effects

The latest [People Add trace](NEXTGEN-JOURNEYS-AND-NAVIGATION.md#director-commitment-recovery-one-add-spans-two-durable-writes-1530-follow-up) shows request creation followed by acceptance. The backend already accepts the same request idempotently, but another Add can create a new ID after a partial or uncertain result. Still-requested rows also have the existing Asked-of-you recovery surface. The missing design contract is how that UI operation retains its acknowledged identity and reports what is known. Actual duplicate commitments were not observed.

This joins the queue and delivery findings: a missing queue entry does not establish cancellation, and a known PR should not be treated as though no external identity exists. Reconcile what is known before any further effect; do not turn uncertainty into a fresh attempt or silently duplicate prior work. Keep requests distinct from accepted commitments, Program Done distinct from delivery completion, and newer edits distinct from a retry of an earlier intention. Whether to retain/resume the two-step People operation or introduce an atomic domain command is still a review choice, not a selected abstraction.

### 3. A coherent view must declare its coverage and authority

People's private obligations, ordinary actions, canonical decisions and retained source records do not become interchangeable because they appear together. Needs You intentionally omits private commitments owed by reports from its People overlay; existing relationship detail and 1:1 briefs still preserve them. Nudge crosses into an ordinary saved Note before a separate intentional Send. No external disclosure was established. Authored decision filing also needs to distinguish current canonical membership from historical source context.

Consolidate navigation and show the relevant context, but retain encrypted authority, obligation direction, verified destinations and existing correction commands. Archive, Program Park and Stop have different scopes. A wider overview or project-wide pause needs an explicit choice, not an inferred meaning of a shared label. These concerns are already detailed in D16/D18/D19/D22/D24 and the [journey trace](NEXTGEN-JOURNEYS-AND-NAVIGATION.md); they are not a mandate to merge storage or add another workspace.

## What this means for code structure

The existing structural candidates still matter: Project Room reads and transactional commands have different responsibilities; Program siblings rely on central-service exports; shared Send composition reaches into Settings; runtime construction is not all in the apparent composition home. The [structural review](STRUCTURAL-REVIEW.md) and target compare retaining clear façades/contracts with narrower moves. No particular package tree follows automatically from the recurring patterns.

A local change should have a discoverable owner, relevant interface and focused proof. Large cohesive files are acceptable. No 300/500-line cap, tiny-file target or blanket rewrite is proposed. The [Python analyses](PYTHON-STATIC-ANALYSIS-V2.md) and [dead-code ledger](DEAD-CODE-REVIEW.md) remain qualified source evidence, not deletion lists; dynamic registrations and supported compatibility must be checked.

## What needs supervision next

1. **Review the whole route, not a list of isolated fixes:** the [ordered plan](EXECUTION_INDEX.md#3-detailed-slices-and-proposed-order) shows how the existing detailed slices compose the build/delivery and director/follow-through jobs, and where the detailed plan is still incomplete.
2. **Review the proposed first outcome, S11 creation context:** [the ordered plan](EXECUTION_INDEX.md#3-detailed-slices-and-proposed-order) recommends explicit project choice before global creation, matching the existing backend. The alternative is an unbound Draft with a broader lifecycle design. Select or redirect the priority, then review the full local G11 interaction; the summary does not approve it. Spending-contract planning is independent, not a prerequisite. Choosing product purpose or publishing the plan resolves neither behavior nor implementation authority.
3. **Keep authority and publication separate:** the authorized documentation-only draft PR makes the review package accessible; it does not authorize application changes, provider actions, test execution or shipping. The [publication checklist](PACKAGE_VALIDATION.md#documentation-publication-readiness) records the bounded publication scope.

Confidence is high in the cited, independently checked source distinctions, but the proposed synthesis remains for review. No live complete user journey, provider effect, product build/test or complete frontend compiler graph was executed for this reconciliation. Detailed tasks follow the later planning instruction; silence is not approval.

## Detailed journey plan checkpoint

There is one backlog: the **HS- hierarchy in [EXECUTION_INDEX](EXECUTION_INDEX.md)**. Its thirteen detailed conditional implementation stories and forty-seven task briefs (including the separate spending-contract task) connect creation, existing project work, action fulfillment, starting input, planning bounds, human review, delivery recovery, person identity, canonical filing, People promise recovery, obligation coverage, navigation and Project read ownership. The target explains why; stories define outcomes; tasks define bounded implementation/proof. Older E/S and NG outlines are historical inputs, not parallel assignments.

Known-request recovery and directional coverage are now detailed in HS-S33 and HS-S43; their gates and implementation remain pending. Coverage uses a normal People entry, not an all-obligations screen. Nudge copy scope and integrated director proof remain separate. Spending now has a concrete contract-resolution task, not enforcement briefs: choose the promise/scope, preserve legacy authority and map every covered caller. Queue/checkpoint/Thread recovery, other structural candidates and whole-product capability parity remain roadmap-level. These gaps are visible in the existing hierarchy, not disguised as finished work or duplicated into another list of tickets. The [HS-S24 gate](epics/HS-E20-program-contracts.md#hs-s24-spending-contract-gate) preserves three unselected branches. Internal planner-stop promises and creator-agent amount writes rule out silently treating a stored number as paid-engine consent. No overrun was observed; external/provider controls and separate CLI transport remain distinct. The current People recovery branch remains same-mount only, and only documentation publication is now authorized; implementation remains unassigned.
