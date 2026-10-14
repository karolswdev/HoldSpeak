# HoldSpeak surface audit — 2026-10-14

Snapshot: main `6e86c666a` (#1199). Owner priority: audit the existing screens,
starting with Conductor → Codex session. Three `gpt-6.1-sol` agents at `xhigh`
audited disjoint lanes; Sol checked the important screenshots and source claims.
No product, test or package code changed. Recommendations are design proposals,
not ratified designs or delivered fixes.

## What the owner encountered

Conductor opens a plain session as a large terminal/control window. In the
observed no-terminal state, the body has a node and an absence label; the
footer spends its space on ARM, CLASSIFY, Keep as note, story Pin and session
identity. At 393 it has a separate scrolling footer and leaves the previous
window showing down the right edge. The work, latest activity and useful next
action are not the leading content.

This is a composition problem. Reuse the existing frame, question well,
activity rows, composer, library controls and receipts to make the work lead.
A new agent framework or another session application is unnecessary.

- [Current session, 1440](../../../.tmp/evidence-shots/surface-audit-conductor/session-plain-no-pane-1440.png)
- [Current session, 393](../../../.tmp/evidence-shots/surface-audit-conductor/session-plain-no-pane-393.png)
- [The working session identified in Conductor, 393](../../../.tmp/evidence-shots/surface-audit-conductor/conductor-populated-393.png)
- [Existing launched question/answer face, 393](../../../.tmp/evidence-shots/surface-audit-conductor/lane-claude-asking-393.png)

The absent pane is a deliberate fixture state. We do not claim real terminal
access is broken. The defect is the face's poor handling of that state and the
controls it emphasizes. A separate source/projection defect loses a working
unbound session's known project when Open resolves its title; this was checked
with a corrected repository fixture at 393.

## Repair order

These groups consolidate the lanes' 21 findings. Each lane report has the
specific source anchors, capture paths, failed tenets and state limits.

| Priority | Owner cost and verified evidence | Concrete repair |
|---|---|---|
| 1. Conductor → session | Empty control console; project identity lost on Open; 92vw phone window; launched question and authority facts repeated. [Conductor findings 1–6](conductor.md#ranked-findings). | Work/project title, one current state, question and Answer when needed, latest actual activity. Terminal is an explicit view. Fold Info, pinning, transport and factory controls. One body scroll; shared full-width phone frame; current action and receipt in the foot. Preserve existing consent and session targeting. |
| 2. Truth of actions and evidence | Unlinked meeting proposal offers Show in transcript because `Number(null)` becomes 0; proposed decision already reads Decided. Rhythm offers an unsaved preference and WRITTEN before success. Commands closes a failed draft; Workbench failures are swallowed. [Work 1](work.md#1-meeting-review-invents-an-exact-transcript-destination-for-an-unlinked-proposal), [Tools 4/6](tools.md#ranked-findings), [Conductor 7](conductor.md#7-workbench-first-use-failures-can-disappear-without-a-receipt). | Validate stored nullable source identity; proposed state stays proposed. Park the preference without a real backend setting. Receipts follow successful writes; failed reads/writes retain context and a named Retry. |
| 3. Readable settings and a short first use | Meetings controls overlap the next caption at 393. First run leads with a 3.0 GB bundle; its 144 MB speech path is conditional on the network branch. Find on LAN sits below downloads and unassigned jobs. [Tools 1–3](tools.md#ranked-findings). | Repair the existing multi-control row's fitting. Make the first sentence and the existing server path visible immediately. Fold optional setup and local downloads. Keep the current engine, download and assignment services. |
| 4. Memory and Project History | Duplicate task text lacks useful owner/source identity; known owner is omitted by the row condition. History reduces named work to Item created · risk/milestone. [Work 2/5](work.md#ranked-findings). | One library result row with task, owner/date, named source and next action. Preserve recorded item titles/identities through history and search. Do not guess that repeated text means one object. |
| 5. Daily scan and Ask | Week eagerly opens full saved summaries and Send forms. Ask still exposes lenses/grounding/budget, and a lens replaces the draft. Needs rows repeat kind/state and several verbs. [Work 3/4/6](work.md#ranked-findings). | Closed weekly rows with a useful excerpt and Open. Show Send when requested. Keep question, mic, engine, source and Ask; fold context tools. One next action per attention row, secondary actions in the existing More menu. |
| 6. Existing component and navigation consistency | Thread mode strip uses raw buttons with no default tab stop. Speak prints a full missing-model path. Setup and Guide duplicate readiness with different repair locations. [Work 7](work.md#7-a-fresh-threads-mode-strip-has-no-keyboard-entry-and-still-uses-raw-controls), [Tools 5/7](tools.md#ranked-findings). | Use the current tab/cycle species with a keyboard entry. Pair the missing-model fact with the existing scoped engine repair. Let one readiness body serve the existing routes; fold raw diagnostics. |
| 7. Audit coverage | The general sweep never opens SessionPullout. Settings More modules, several object editors and operational windows also fall outside its base cases. Some screenshots capture an early blank read. [Census](CENSUS.md). | Keep a named inventory of app → inner object → important state. For each repaired face capture the actual open transition and its populated, empty, unavailable and action-result states. Use the current fixture/rig, with content-readiness assertions. Do not make a new audit framework or widen the nightly suite. |

## First coherent implementation: the agent session

The Tuesday job: see what the coder is doing, answer or direct it, inspect its
terminal when useful. The existing People Prep and inline Note → Task well are
useful references for direct actions in their object window.

1. Resolve the known session/project from the existing all-session projection.
2. Put one human state and latest activity above the question or work stream.
3. Show the question and one answer composer once. Keep the existing grant and
   egress behavior at the action that requires it.
4. Show recorded work/PR facts only when they exist; fold future process stages
   and the duplicate question in the launched lane.
5. Open the existing terminal on request. If unavailable, keep the work visible
   and name the actual state; do not fill the default face with unresolved keys.
6. Fold Classify, story Pin, node/branch/session details and advanced controls.
   Use one body scroller and the shared phone window dimensions.
7. Design the changed face in production components before building. Walk
   working, asking, unavailable and completed sessions through the actual
   Conductor door. Reuse services; keep the change in the existing session/lane
   components rather than creating another subsystem.

This is a coherent screen repair, including its identity, layout, failure state
and actions. A title/spacing-only patch would leave the reported problem.

## Coverage and limits

[CENSUS.md](CENSUS.md) records all **24 application rows** (including three
parked compatibility rows), **20 object-kind mappings**, the four inline
editors and the other window hosts mounted outside the application core list.
It separates mapped, rendered, blocked and parked states.

The existing generic sweep ran once in isolated HOME under the machine lock:
**106 passed, 3 existing xfails**, with **109 PNGs**. Additional retained captures:
12 Conductor/session/lane/Info PNGs, 16 tools/first-run/settings PNGs, and 13 work
PNGs. These counts describe captured files, not unique faces or successful
end-to-end jobs. The reports identify the inspected slices and source-only
claims. An early blank Engines/Person capture was not reported as a dead app;
populated poses were recovered independently.

The most important remaining visual gaps are Workbench internals/chooser,
Tasks/Decisions detail, People Context/History/Info, generic artifact/knowledge/
recipe/sequence/workflow/directory editors, repository/roadmap/delivery/factory
operations, phone Ask/Note→Task and several refusal/result states. Workbench
and phone Note capture attempts stopped at their two-attempt budget; fixture
selector failures are not product defects. None inherits approval from the
green sweep. Real model/agent execution, microphone, terminal keys, account
sign-in, notification delivery, touch and owner acceptance remain unobserved.

## Records

- [Conductor and agent work](conductor.md): seven findings, six paired poses,
  proposed session layout and explicit Workbench gaps.
- [Daily work and meetings](work.md): seven findings, populated work captures,
  proposal-wire evidence and proposed Memory rows.
- [Tools and setup](tools.md): seven findings, eight supplementary paired poses,
  proposed first-use layout and action/persistence traces.
- [Census](CENSUS.md): registry and host inventory, including the unobserved tail.
- [Lane charter](BRIEF.md): exact ownership, limits and no-product-edit boundary.

Source and screenshot checks establish this audit snapshot. Implementation
recommendations remain proposals pending the normal design review. No PR,
merge, owner-session action or deployment was performed for this audit.

## Subsequent implementation

The owner subsequently approved implementation. See
[Surface repair](../SURFACE-REPAIR-2026-10-14.md) for changes, verification and
delivery. This audit remains the original main snapshot. The generic
`.tmp/evidence-shots/desk-sweep/` cache is reused by later quick checks and now
contains their current shots; do not read those as immutable before pictures.
The dedicated audit Conductor, tools and work capture directories remain the
original supplementary observations.
