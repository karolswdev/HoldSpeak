# Follow-through and attention surfaces — settled direction

Base `420a0eb28`; isolated `wt-follow-through-20261015`. Owner: Follow-through
is confusing and ugly; continue scouring/refining existing surfaces.
Tenets 2/3/5/6/7: can the architect see the task, owner and date, act once,
and understand what changed? Existing library material, actual canonical
writers, no new task system/form framework. Owner judges the release live.

Root before walk: real Note + Door task producers on isolated hub, four date/
owner states, opened actions and assignment, missing source and last Done/
refused Undo. Six states at 1440/393, existing release bundle cfa38b02306c2789.
Root read actual shots. Snooze on a real new `open` task leaves it on board;
refused Undo after last Done has no visible failure. These are observed.
Neighbor findings are source-backed, with live proof owed; audits are snapshots.

## Follow-through face

- Keep one library lane ledger per populated group, one heading/count only.
  Overdue first, To review second, Due soon (`now`) then Later (`waiting`).
  These are date/review buckets, not a claim about who owes whom. No invented
  Mine/They owe classification. Empty groups disappear; empty whole board
  and active overdue filter retain distinct honest states and clear action.
- Task wraps fully at narrow widths. Full owner name (mapped display name or
  actual owner), `No owner` if missing; explicit due facts (`Today`, `Tomorrow`,
  `Due in N days`, `N days overdue`, `No date`). Age, if shown, names its real
  timestamp: Assigned or Added, never a claim that work is waiting. No zero
  day counters. Reuse StateChip/SurfaceLedgerRow wrap/paper/standard type steps.
- Visible row actions: real source word (Open note/thread/meeting/decision/
  People); never a mysterious source glyph or a dead missing-source button.
  Source unavailable is a small fact only when no verified ref. Task row
  opens Details; Done can be directly visible on action/People rows.
- Expanded row composes inset GadgetGroup/GadgetRow. Explicit Owner field,
  Assign button (same delegate writer); Due date StringGadget with ISO value/
  placeholder and Save date (existing follow-through `due` writer). Preserve
  in-progress/newer drafts and reference/source identity; fields do not save
  merely by changing them. Existing Snooze says Tomorrow, Dismiss separate.
  Clear Cancel closes editor without a write. People never gains unsupported
  owner/date/snooze controls. No new dropdown/date species/framework.
- Source=decision/cadence_loop rows use existing cadence close/kill/snooze
  endpoints, labelled Close/Stop/Tomorrow. Never send loop.id to action complete;
  never manufacture an action Undo for a closed cadence loop. Decision source
  remains real decision ref. Cadence without a source gets no false meeting
  opener; a real Rhythm door may be used if existing registry supports it.
- One synchronous pending-write guard; disable conflicting writes while a
  request is pending, permit reading. Keep accepted board visible on refresh;
  initial read alone blocks the face. Show pending/result/failure through kit
  states. Write error and exact Retry remain visible even when board/filter
  becomes empty. Rejected assignment/date/Undo keep values/context. Newer reads
  cannot be replaced by old reads; keep existing bus refresh/filter/source paths.
- Done receipt remains available through empty transitions. Ordinary action
  receipt keeps existing 8s persistence/Undo. People receipt stays in memory
  only; never persist decrypted People body or opaque People receipt. On read,
  discard legacy People localStorage receipts. No claims about microphone or
  real encrypted store from UI doubles. Existing People authority is unchanged.
- Focus-card navigation expands AND scrolls the actual target into view after
  its board read; no background scroll on ordinary refresh.

Follow builder owns FollowThroughView.tsx, its test, IntelligenceTruth/Walk
and IntelligencePullout tests if changed words/semantics require them,
intelligence.css FOLLOW-THROUGH slice only, and BUILD-FOLLOW.md. Neighbor lane
owns BriefView/DecisionsView/DecisionPullout and their tests/new local CSS.
Shared library, host navigation, backend, root canvas/docs/status: do not touch.
Exact allowed vitest scope: FollowThroughView.test.tsx, IntelligenceTruth.test.tsx,
IntelligenceWalk.test.tsx, IntelligencePullout.test.tsx. Add focused cases for
wrap/full identity/source, lawful route dispatch, assignment/date custody,
last Done/refused Undo/Retry, private receipt persistence and target scrolling.
Collect/run exact scope only through root locked helper. No browser/build/install.

## Canonical backend seams

Snooze must work before collection. Within the existing complete transaction,
when an action has no linked loop, insert one canonical meeting_action loop
using existing cadence schema/defaults/source identity, then snooze it. Do
not create one for unrelated verbs or split the transaction. Existing loops
and source upsert preserve lifecycle state. Return actual loop identity.
Keep current accepted Snooze input compatibility. No new schema/service.

Suppress a meeting_decision loop in board when its decision is represented by
an associated action/commitment; action remains canonical obligation. Keep
standalone loops and normal meeting_action dedupe. Do not merge by text or
invent a second status authority. Existing People projection/observer privacy
and completion receipts remain unchanged.

Backend builder owns holdspeak/services/follow_through_service.py,
tests/unit/test_follow_through_service.py and BUILD-BACKEND.md only. May run
exact service unit file plus tests/unit/test_follow_through_pipeline.py and
person_enrichment tests. Real canonical producer/service assertions: newly
added open task snoozes out of board before collection, idempotent single loop,
collector upsert preserves snooze, owner/date/done unchanged, represented
accepted decision yields one obligation, standalone loops remain. Add date/
owner only in UI against existing writer; no unrelated backend feature.

## Neighbor faces

- Brief: latest person OR item selection owns the footer. Selecting an item
  clears prior person, selecting person clears prior item. Highlight actual
  selected row. Keep existing object opening, agenda, Acknowledge/Defer and
  late draft/request guards. No new selection manager or redesign of Today.
- Decisions: record reader uses one Material paper reader with named source/
  context fields and inset details. Existing source/work/chain verbs remain
  explicit words, no [GO]/opaque-id-only navigation. Empty sections fold/omit
  without losing real record fields. A failed requested record has its own
  visible error, exact Retry and Results; cannot silently redraw old record.
  Guard late reads and Back so old request cannot replace latest destination.
- Decision window: replace immediate hidden status cycling with library
  CycleGadget listing actual existing states. Inspect/open does not write;
  explicit named choice invokes existing PUT. Check HTTP response, keep prior
  state on refusal, visible failure/Retry. Avoid optimistic status lies and
  pending duplicate writes. Named inset edit groups and Material body, existing
  context/decision/consequences drafts, Copy/Send/filing must remain intact.

Neighbor builder owns BriefView.tsx, DecisionsView.tsx, DecisionPullout.tsx,
BriefView.test.tsx, DecisionsView.test.tsx, decision.app.test.tsx and a NEW
attention-records.css imported by those faces, BUILD-NEIGHBORS.md. Do not edit
shared intelligence.css (Follow lane owns slice), libraries/host/backend.
Exact vitest scope those three tests plus philo301DecisionFace.test.tsx,
philo301DecisionNoLoss.test.tsx, philo605DecisionBodyDiagnosis.test.tsx.
Preserve recorded wire diet; collect/run only exact scope, no build/browser.

## All workers

Verify anchors against base and current source; other workers share this tree.
All test calls: `.venv/bin/python .tmp/follow-through/locked.py LABEL --web
./node_modules/.bin/vitest list|run <exact paths> --maxWorkers=2` or isolated
locked pytest exact allowed paths. Never bare owner HOME, DB, keystores,
provider CLI, clipboard, hardware, real egress. Root owns actual walks, canvas
before face build, independent finished review, quick, staging, PR/merge and
normal local redeploy. Report exact collected names/red/green/unknowns.
No stage/commit/moving git verbs. HOLD FOR SHIP.
