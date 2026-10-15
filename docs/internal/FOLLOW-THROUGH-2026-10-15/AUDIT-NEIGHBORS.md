# Neighboring attention surfaces — source audit, 2026-10-15

Status: DRAFT · SOURCE ONLY · HOLD FOR BUILD.

Base: `420a0eb28` in `/Users/karol/dev/tools/wt-follow-through-20261015`.
Scope: DecisionsView, DecisionPullout, BriefView and Intelligence navigation.
FollowThroughView belongs to the other audit. No additional opened face was
needed. No product edits, tests, browser work, installs, owner-state reads or
writes, staging or commits were performed for this audit.

Read first: TWO-BRAINS; then CLAUDE's 2026-10-12 fast cycle, the Constitution's
Seven Tenets, UX-CANON and ORCHESTRATION. The three findings below are current
source paths on this base. The implementation commits for #1207, #1208 and
#1209 do not change these four audited face files. This audit does not repeat
their Workbench, Accounts, history, session or knowledge refinements.

## 1. A decision's state token changes its meaning before the owner chooses a state

**Owner cost:** An architect inspecting an accepted decision can mark it
superseded with one press on `accepted ↻`. That press names the current
state, but the stored result is the next state. Getting back to accepted
requires cycling through deprecated and proposed. The same control gives no
pending or failed result.

**Source proof and actual wiring:**

- `web/src/desk/pullouts/DecisionPullout.tsx:71` defines the immediate cycle
  `proposed → accepted → superseded → deprecated → proposed`; line 75 sends
  the computed next state to `PUT /api/decisions/{id}/status`.
- `web/src/desk/pullouts/DecisionPullout.tsx:87` renders the current raw state
  with `↻` as the only control label. No state choices are visible.
- `holdspeak/web/routes/primitives/decisions.py:149` admits that exact status
  write; `holdspeak/services/primitive_service.py:255` updates the stored
  decision. This is a durable mutation, not a presentation toggle.
- `web/src/lib/api.ts:27` returns a Response for HTTP failures rather than
  throwing. DecisionPullout line 79 refreshes for any resolved Response,
  without checking `ok`; it also has no rejection handler or write receipt.
- The real face is registered at `web/src/desk/pullouts/registry.ts:31`.
  DecisionsView opens a Desk decision through
  `web/src/desk/pullouts/views/DecisionsView.tsx:258` and
  `web/src/desk/openObject.ts:180`.

**Small repair to settle on the canvas:** Offer the states through the shared
choice control with plain labels; write only the chosen state. Keep the
current state visible while saving and show the actual result. No extra
confirmation step is needed.

**Tenets:** 3 (clear action that accelerates the owner), 4 (plain words),
5 (shared choice species). UX-CANON A.10 requires honest failed states.

**Focused test candidate:** Extend
`web/src/desk/__tests__/decision.app.test.tsx`. Replay the real decision/status
wire through the real store and API: inspect/open the state choice without a
write; choose a named state and assert the rendered state after the response;
return 403/500 and assert the old state plus a visible failure. Its current
DecisionPullout cases at line 151 cover empty headings and Edit, not state
changes. Test candidate only; not collected or run.

## 2. Brief keeps the previous person's actions after the owner selects a different item

**Owner cost:** Read a person's signals, then select a meeting or decision in
the lookback. Acknowledge and Defer remain unavailable; the footer still
offers actions for the earlier person. The owner must discover that the
person row must first be closed. An agenda press still targets that old
person.

**Source proof and actual wiring:**

- `web/src/desk/pullouts/views/BriefView.tsx:189` and line 192 keep item and
  person selection independently.
- `web/src/desk/pullouts/views/BriefView.tsx:502` handles a lookback press by
  setting only `selectedId` (line 507), then opening the named object through
  `refOpener`. It leaves `selectedPersonId` in place.
- `web/src/desk/pullouts/views/BriefView.tsx:551` changes only person selection.
- `web/src/desk/pullouts/views/BriefView.tsx:589` always gives the person the
  footer subject; line 602 gives that person the verbs before checking the
  newly selected item. The item verbs live in the later branch at line 611.
- `web/src/desk/pullouts/views/BriefView.tsx:604` passes that retained person's
  relationship ID into `addToAgenda`; lines 331 and 344 read that person's
  session and write its agenda. The mismatch reaches real People routes.
- `web/src/desk/pullouts/IntelligencePullout.tsx:121` hosts the real BriefView;
  the Follow-through special case at BriefView line 503 leaves this view and
  is not part of this finding.

**Small repair to settle on the canvas:** Make one selection own the footer.
The last selected person or item must determine its visible subject and
verbs. Show the selected item in the row as well as the footer.

**Tenets:** 2 (remove the functional complexity blocking first use),
3 (the next action follows what the owner chose), 7 (reliable manager work).

**Focused test candidate:** Extend
`web/src/desk/pullouts/views/BriefView.test.tsx`: select Ewa, then Standup;
assert the footer names Standup, offers Acknowledge/Defer, and no longer
offers Ewa's agenda verb. Reverse the selection and assert Ewa's actions.
Drive Acknowledge through the rendered outcome. The existing person-only
case at line 213 and item-only case at line 278 never switch between them.
Use recorded real hub answers for any added fixture. Test candidate only;
not collected or run.

## 3. Failed record navigation silently returns the previous decision record

**Owner cost:** Follow a predecessor or successor to learn which decision
stands. A failed read briefly shows loading, then redraws the old record
without the failure. The owner cannot tell that the requested record was
never read.

**Source proof and actual wiring:**

- `web/src/desk/pullouts/views/DecisionsView.tsx:242` starts `openReceipt`
  without clearing or identifying the previously selected receipt. A failure
  sets `error` at line 248; the selected receipt remains.
- `web/src/desk/pullouts/views/DecisionsView.tsx:297` therefore still renders
  ReceiptDetail after the failed read.
- `web/src/desk/pullouts/views/DecisionsView.tsx:434` shows the spinner while
  loading. At line 435 it renders `error` only when no receipt exists; with
  the old receipt present, the error is ignored and the old content renders.
- The predecessor and successor verbs at
  `web/src/desk/pullouts/views/DecisionsView.tsx:484` and line 486 call this
  same opener. `GET /api/decision-records/{record_id}` is real and can return
  404 at `holdspeak/web/routes/decision_records.py:60`.
- `web/src/desk/pullouts/IntelligencePullout.tsx:146` also supplies the receipt
  ID from external navigation to this component. The failure is not limited
  to an invented test path.

**Small repair to settle on the canvas:** Keep the requested record identity
and its read state together. On failure, make the failed destination and
retry/back action visible. If the previous record stays for context, label
it as the previous record and keep the failure visible.

**Tenets:** 3 (answer why without ambiguous navigation), 7 (trustworthy
decision recall). UX-CANON A.10 requires honest failed states.

**Focused test candidate:** Extend
`web/src/desk/pullouts/views/DecisionsView.test.tsx`: open a real recorded
receipt, press its successor, reject that read, and assert the visible
destination failure plus working Retry/Results. The happy receipt path at
line 170 currently stops before exercising its chain. Test candidate only;
not collected or run.

## Navigation checked; proof still owed

The app registry opens Today at
`web/src/desk/applications.ts:75`; Intelligence owns Day, Brief,
Follow-through and Decisions at `IntelligencePullout.tsx:14`. Segment presses
replace the navigation request at line 108, so the already-fixed invisible
overdue-filter bug is not a new finding. Desk decision refs open the decision
window; meeting decision refs read their owner and drill to Decisions
(`web/src/desk/openObject.ts:180` and line 203).

**Tuesday:** The owner can reach these faces, but a decision-state press,
a Brief subject switch and a failed decision-history read can each make
the next action or visible result mean something other than the latest
choice. Resolve these before claiming the neighboring flow is clear.

**Unknown:** No live rendering or interaction was observed. This audit makes
no geometry, contrast, hit-target, production-console or visual-quality
claim. The parent owns the real isolated-hub reproduction, canvas, 1440/393
shots, final scope, tests and release. These anchors may drift after this
base; reread before briefing a build.
