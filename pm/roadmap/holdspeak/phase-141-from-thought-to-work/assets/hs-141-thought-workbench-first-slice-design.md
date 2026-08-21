# HS-141 design beat — Thought Workbench first slice

**Status:** implemented and ratified; owner craft amendment applied 2026-08-20.
The amendment makes the real model action visibly **Ask AI**, restores a compact
document-formatting rail, gives the Note 68% of the wide workspace, and
beautifies the context picker without changing its authority or receipt laws.

**Platform continuation:** the proposed
[`Inference Instrument`](../../proposals/inference-instrument.md) preserves this
Workbench contract while making local MLX/GGUF, hosted, private, paired, and
mesh deployments equally selectable beneath the same frozen inference waist.

## Decision

A working Thought opens in one dedicated **Thought Workbench**. It is a Desk
window composed from the existing durable working Note, one-turn refinement,
visible AI context, completion, and receipt/placement truth. It is not a larger
Note pullout, chat thread, stored Workbench primitive, planner, or tool router.

The first slice is deliberately small:

```text
edit the live Note
  -> Ask AI
  -> receive one question or synthesis
  -> if question: Add & ask next, or Add to Note
  -> edit / attach context / Finish Thought / leave at every boundary
```

**Add & ask next** is the primary question action. It atomically appends the
answer and reserves exactly one next refinement turn. That turn may return a
question, synthesis, refusal, or failure; the product copy is not a promise that
a question must result. Quiet **Add to Note** appends the same answer and starts
no turn.

The code namespace is `ThoughtWorkspace`. It must not reuse existing
`WorkbenchWindow`, Workbench tables/services/runs, or
`holdspeak://workbenches/...` resources. This surface creates no stored
Workbench.

## Existing truth and the composition gap

The backend already has the correct authority seams:

* `ThoughtNoteEditor` has a serialized writer, authority epoch, retained failed
  draft, conflict fence, and synchronous flush;
* `RefinementApplicationService` is shared by HTTP and the fourteen current
  Thought MCP commands;
* refinement freezes exact working/context revisions before Ask;
* review actions are receipt-gated and Answer currently appends a canonical
  clarification block without another invocation;
* context is server-hydrated from qualified refs and stale by exact human name;
* invocation/review state survives restart without blind redispatch; and
* result projection already carries actual placement and egress facts.

The gap is `NotePullout`: it currently owns custody, adoption, editor saves,
polling, review, context/default policy, stale repair, completion, filing,
receipts, and a state-dependent footer. The first slice moves that orchestration
behind one projection/controller and leaves `NotePullout` as the ordinary Note
surface plus adoption handoff.

## Product law and copy

1. **The Note is the work.** AI is an interview sidecar to one live document,
   not the main transcript.
2. **One explicit command, one turn.** Only **Ask AI** and
   **Add & ask next** may reserve a turn. Add to Note, Accept, Reject, context,
   Finish, tabs, retries, reads, and restart never do.
3. **Answers visibly enrich the Note.** Both answer paths return one immutable
   append-effect receipt. UI reveal follows its exact hash/range.
4. **YOLO/power-user first.** **Finish Thought** is direct and confirmation-free.
   Keyboard flow is complete; no setup/tutorial blocks the Note.
5. **One visual primary.** A single fixed command-strip action seat changes its
   contents without moving. Quiet valid exits do not become equal primaries.
6. **Context remains explicit.** Human attachment names/state stay visible;
   browser/MCP send refs and cursors, never copied context bodies.
7. **Placement is per-turn truth.** Intended placement is advisory beside Ask;
   actual placement appears only beside a returned result.
8. **Failure leaves useful work.** Note, Attach, Finish, close, and later Resume
   remain useful without model/tool/process availability.
9. **No fake capability.** This slice has no suggestion, outcome palette,
   GitHub/Jira/calendar teaser, native model tool, or disabled future button.
10. **No duplicate subsystem.** No chat history, second writer, generic agent,
    tool router, proposal lifecycle, receipt feed, or window-layout system.

Exact owner verbs are:

| State | Fixed action seat | Quiet adjacent action |
|---|---|---|
| idle, model ready, context current | **Ask AI** | **Finish Thought** |
| ASKING / awaiting projection | **Stop** | **Finish Thought** |
| current question, continuation ready | **Add & ask next** | **Add to Note**, **Finish Thought** |
| current question, continuation unavailable | **Add to Note** | **Finish Thought** |
| current synthesis | **Use this draft** | Reject, **Finish Thought** |
| stale/missing question or synthesis | **Update context** / **Remove it** | **Finish Thought** |
| retryable inference failure | **Try again** | **Finish Thought** |
| no model | **Set up AI** | **Finish Thought** |
| completed | **Resume** | none |

A stale question is non-actionable: neither answer action is present. Repair
supersedes it, then the idle state offers a new Ask. Context mutation likewise
supersedes a current review before publishing the new attachment head.

Transport/domain names such as `refine`, `answer_review`, and `complete` remain
technical compatibility names. They are not ordinary owner copy.

## Amiga-inspired operating grammar

The inspiration is speed and composability, not retro decoration:

* one ordinary movable/resizable Desk window;
* one live document and one fixed Interview pane;
* terse exceptional state, no narration or chat stack;
* direct keyboard execution;
* explicit, bounded receipts;
* no modal workflow, opening animation, splitter, or layout preference; and
* no whole-Desk refresh loop while typing.

Normal chrome contains only the document, its compact formatting rail,
Interview, thin AI-context row, Finish, and one fixed action seat. The
Interview's idle **Ask AI**
text explains what the seat will do; it is not a button. The Interview body may
show quiet **Add to Note**, but never contains **Add & ask next** or another
state primary. There is no ordinary WORKING lamp, permanent placement badge,
latest-action row, receipt timeline, or duplicate title.

## Exact 1440 × 900 composition

Initial geometry is `1080 × 680`, clamped to the shared DeskWindow safe work
band. Minimum wide grammar is `860 × 560`; below `860px` container width the
narrow grammar activates. The Note/Interview split is `68/32`, with Interview
never narrower than `300px`.

```text
+ Thought -------------------------------------------------------------+
| Launch ownership                    | INTERVIEW                     |
| B I U H1 H2 H3 · List 1. Code Link  |                               |
|                                      |                               |
| document body canvas                 | Ask uses the saved Note       |
|                                      | Runs on This device · Local   |
|                                      |                               |
|                                      | or current question/synthesis |
|                                      | [answer                     ] |
|                                      | Add to Note                   |
|                                      | Used Everyday context >        |
| tags                    Filed · Saved|                               |
+---------------------------------------------------------------------+
| AI context  Everyday context · 5 notes                     Attach    |
+---------------------------------------------------------------------+
| Finish Thought                         [fixed state-primary seat]    |
+---------------------------------------------------------------------+
```

The document receives all surplus width. Document and Interview scroll
independently; context and command strip remain fixed. Context detail is capped
and internally scrolls. Placement exists only in Interview.

### Document craft contract

The visual editor is one borderless document:

* title is a heading-sized input in the document, not a labelled field;
* body is one continuous canvas and owns initial edit focus;
* Markdown remains directly typable; a compact borderless rail exposes bold,
  italic, underline, headings, lists, code, link, and quote;
* tags are quiet removable chips plus Add tag;
* filing and save truth share the lower document edge; and
* Original is one thin nonblocking Info disclosure, not footer competition.

Craft counsel rejects the slice if any screenshot or geometry test shows:

1. actual title repeated in window chrome and document;
2. Title/Body/Tags rendered as a Settings-style labelled form;
3. nested card borders around the Note or Interview;
4. a boxed, embossed, or multi-row formatting wall that competes with the Note;
5. body canvas below 60% of available document-pane height at `1440 × 900`;
6. tags/filing/save competing with the body as equal cards;
7. state changes moving/resizing the command-strip action seat;
8. clipped title/question/context, nested horizontal scrolling, or footer wrap;
9. document focus stolen when a question arrives; or
10. a normal-state status/placement/latest-action ornament.

## Exact 393 × 900 composition

At 393 this is a workspace-height sheet under shared safe chrome, not two
crushed columns.

```text
+ Thought -----------------------------------------+
| Note                              Interview 1    |
+--------------------------------------------------+
| Launch ownership                                   |
| Question ready: Who owns the launch?               |
| live document canvas                               |
+--------------------------------------------------+
| AI context  Everyday context · 5 notes    Attach   |
+--------------------------------------------------+
| Finish Thought                     [Answer question] |
+--------------------------------------------------+
```

Note and Interview remain mounted. The unselected pane is `hidden`,
`aria-hidden`, and natively `inert`; it contributes no focus target, label,
shortcut, or live-region output. At a current question:

* Note tab puts one **Answer question** navigation proxy in the same fixed
  command-strip seat. It only opens/focuses Interview and sends no HTTP/MCP
  command.
* Interview puts its state primary in that seat. When continuation is ready it
  is **Add & ask next**, with quiet **Add to Note** beside the answer. When
  continuation is unavailable, the composite is absent and **Add to Note** is
  promoted into the seat; its quiet duplicate is suppressed.

Every state uses the same single seat element and stable DOM/grid bounds; state
changes replace its label/handler rather than inserting a second primary.

The context row is persistent; Attach opens the existing bottom sheet with no
393 search autofocus and pinned Everyday context above the software keyboard.
Targets are at least `44px`; only the selected pane scrolls.

The same compact formatting rail scrolls horizontally on mobile without
reserving a second row. Tags and document Info remain disclosures.
Actual placement appears in Interview only.

## Answer reveal and focus

Both answer receipts identify the exact appended byte range. After response:

* **Add to Note:** 393 switches to Note; desktop uses its already-visible Note.
  The editor verifies the receipt, scrolls the clarification heading into view,
  places the caret at the append end, focuses the body, and makes one polite
  **Answer added to the Note** announcement.
* **Add & ask next:** desktop reveals a brief insertion marker in the Note but
  retains focus in Interview on the new ASKING/Stop state. At 393 it stays in
  Interview and shows **Added to Note · View**; View switches to Note, verifies
  the range, scrolls it into view, and places the caret at append end.

The marker is not a receipt timeline and disappears after the next owner action
or View. Hash/range failure performs no guessed search/focus; it reports an
integrity error and offers one projection reload.

## Keyboard and focus

`Mod` means Meta on macOS/iOS and Control elsewhere. Visible help renders `⌘`
or `Ctrl`. Handlers do not fire during IME composition.

* `Mod-Enter`: invokes the visible fixed-seat primary. On 393 Note/question it
  invokes only the navigation proxy.
* `Mod-S`: drains the sole writer.
* `Escape`: closes the current picker/disclosure; it never Stop/Reject/Finish.
* existing `Mod-K`: remains the Desk command palette.

`Mod-Shift-Enter` may map to Finish only after a platform/browser/editor/AT
collision test. No other new shortcuts ship in v1.

## Opening and speed contract

The navigation snapshot already held by the shell provides immediate paint; no
new cache or durability claim is introduced.

1. Within the next animation frame and `50ms`, paint snapshot title/preview
   beneath an inert **Opening Thought…** veil. Editor, tabs, context, Finish,
   primary, and shortcuts are disabled/inert.
2. Start exactly one workbench projection request. There is no ownership ->
   Thought -> review -> context -> models waterfall.
3. Each open/retry/Thought change increments a request epoch and aborts the old
   `AbortController`. A response can install only when epoch and Thought ID are
   still current. Abort and late response never show an error or replace state.
4. Warm local projection must become editable within `250ms` p95 and `500ms`
   acceptance maximum. Crossing 500ms is a performance-test failure, not a
   fabricated product/network failure. The UI stays honestly Opening.
5. A real transport/service error shows **Could not open this Thought** and one
   Retry. Retry aborts/increments epoch and performs one new read.

Key/tap pending paint is <=`32ms` and makes no HTTP-dependent success claim.
Returned authoritative command state paints <=`100ms` after becoming locally
available.

## Sole writer and mutation gate

Extract `useThoughtWorkingWriter` from `ThoughtNoteEditor` and own one instance
in `ThoughtWorkspaceController`. It preserves:

* synchronous fence and serialized save A / queued edit B;
* `authorityEpoch` and late-save discard;
* retained failed draft plus Retry save;
* external authoritative C conflict fence without later A/B overwrite;
* waiters and exact current authoritative revisions; and
* authority install/reveal without remounting or losing answer/Note drafts.

Ordinary compositor close calls flush and vetoes close on retained failure or
conflict. Forced browser/process teardown makes no durable-save claim; this
slice does not invent a recovery cache. Reopen shows server truth.

Every state-changing mutation except Stop enters one
`runAfterFlush(projection, action)` gate:

1. fence and drain the writer;
2. send nothing on failure/conflict;
3. use the save response's complete fresh workbench projection—no GET;
4. re-evaluate that action against the returned action set/cursor; and
5. send the exact mutation only if still permitted.

This covers Ask, both answer paths, Accept, Reject, context attach/detach/update,
Finish, and Resume. Save returns `{thought, workbench}`. It updates workspace
and local object cache, but never calls `useDesk.refresh()` per keystroke/save.
Chair/list refresh coalesces on close, Finish, or later idle.

Reconcile and Stop are process-control exceptions: neither flushes. Reconcile
pauses while the writer is dirty, saving, failed, or conflicted. Stop must
remain available with a dirty draft. Their responses may merge only newer
process/continuity/action/cursor authority over the controller; they cannot
install working Note/title/tags or clear/replace the writer draft. A successful
save supersedes the prior live/review turn server-side and returns the resulting
full projection.

During ASKING, Interview names **Using saved Note vN** and says exactly:
**Editing now will replace this question.** A dirty draft alone makes no server
claim. The first successful save atomically supersedes/suppresses that
invocation; late output cannot publish into the new cursor.

## Authoritative workbench projection

One transport-neutral query is shared exactly:

```text
RefinementApplicationService.get_workbench(owner, thought_id)
  <-> GET /api/thoughts/{thought_id}/workbench
  <-> holdspeak://thoughts/{thought_id}/workbench
```

It is owner-only, one database read transaction, zero-write, and invokes no
coordinator/provider. It includes no raw Original bytes, attached Note bodies,
frozen prompt material, credential, provider payload, local default-policy
internals, or recent-receipt feed.

### Closed projection shape

```json
{
  "schema_version": 1,
  "process_scope": {
    "kind": "hub_local",
    "hub_id": "hub_...",
    "state": "available"
  },
  "workspace_cursor": {
    "hub_id": "hub_...",
    "thought_id": "thought_...",
    "aggregate_revision": 7,
    "continuity_revision": 11
  },
  "thought": "<canonical Thought DTO>",
  "workspace_state": "question",
  "actions": {
    "primary": {
      "kind": "answer_and_continue",
      "review_result_id": "rresult_..."
    },
    "state": [
      {"kind": "answer_and_continue", "review_result_id": "rresult_..."},
      {"kind": "answer_review", "review_result_id": "rresult_..."},
      {"kind": "reject_review", "review_result_id": "rresult_..."}
    ],
    "ambient": ["update_working", "attach_context", "complete"]
  },
  "review": "<safe current review or null>",
  "context_status": {
    "summary": "Everyday context · 5 notes",
    "state": "current",
    "repair_ref": null
  },
  "inference": {
    "availability": "ready",
    "continuation_admission": "ready",
    "intended_placement": "<advisory current canonical target summary or null>"
  },
  "terminal_status": null
}
```

Closed enums:

* process state: `available`, `unavailable`;
* continuation admission: `ready`, `unavailable` (meaningful only for a current
  question);
* workspace state: `idle`, `reserved`, `in_flight`,
  `awaiting_projection`, `question`, `synthesis`, `stale`, `named_failure`,
  `completed`;
* state action: `refine`, `configure_ai`, `stop_refinement`, `answer_and_continue`,
  `answer_review`, `accept_review`, `reject_review`, `refresh_context`,
  `detach_context`, `complete`, `resume`;
* ambient action: only `update_working`, `attach_context`, `complete`; and
* context state: `empty`, `current`, `stale`, `missing`.

`actions.primary` is one exact member of `actions.state`. Idle/no-model projects
`configure_ai`, which opens Settings directly in Models, while ambient complete
remains available. Ambient actions are not state
recommendations: they state that the working Note can save, the context picker
can attempt a server-listed candidate attach, and Finish is allowed. Candidate
rows remain server authority. Process state and actions describe only this
hub's process truth; they never imply another hub is idle or globally excluded.

`configure_ai` is the one presentation exception to the fixed command seat: on
wide Workbench it renders directly beneath the missing-model explanation. On a
narrow Note tab, the fixed seat is a navigation proxy; after switching to
Interview only the local setup button remains. There is never a duplicate
visible primary.

The 393 **Answer question** proxy is presentation-only and is never projected.

For a current question the reducer checks continuation admission, not merely
whether a model is configured. `ready` admits `answer_and_continue` as the
state primary and retains quiet `answer_review`. `unavailable` omits the
composite entirely and promotes `answer_review` into the fixed seat; Finish
remains quiet. If admission changes after a ready projection but before command
validation, the composite refuses before append/terminal/child work, retains
the answer text and focus, refreshes to the unavailable reducer, and says
exactly: **Couldn't start the next turn. Your answer is still here. Add it to
the Note.** No answer, review, or cursor state changes.

### Durable cursor

Add hub-local `continuity_revision` for a Thought. It starts at zero and
increments once per local authoritative committing transaction that changes
invocation, attempt, review, action, cancellation, recovery, or terminal
authority—regardless of how many child rows that transaction changes.
No-op/idempotent replay does not bump, and the revision does not synchronize.

The explicit cursor is not cryptographic:

```text
(hub_id, thought_id, aggregate_revision, continuity_revision)
```

The canonical hub ID is provisioned during database bootstrap/migration before
the server becomes ready; GET never creates it. There is no cursor secret,
rotation, or key-loss recovery. Replacing/loss of hub identity invalidates old
cursors with `workspace_cursor_hub_mismatch`; the client reads a new projection.
It never silently adopts an old cursor under the new identity.

`answer_and_continue` is new and requires exact equality with all four current
values in addition to its per-kind CAS fields. Optional `workspace_cursor` is
added only to the exact existing Thought-instance mutations consumed by this
workspace: refine/reconcile/Stop; answer/Accept/Reject;
attach/detach/refresh context; and update/complete/Resume. Absent preserves the
old request fields, CAS semantics, and established response fields; supplied
enforces workspace comparison plus every old guard. The Workbench UI always
supplies it. Create, adopt, default-policy, list, and read bodies/responses stay
byte-for-byte unchanged. This is no required-field migration.

Reconcile and Stop have the sole relaxed comparison. Supplied cursor must name
the same hub/Thought, have aggregate revision exactly current, continuity
revision `<=` current, and name the exact current invocation. Reconcile accepts
only reconcilable states; Stop accepts only stoppable states. They may advance
process authority but leave aggregate, working, attachment, and lifecycle heads
unchanged; a committing transaction bumps continuity once.

Every cursor-aware committed command receipt records `committed_post_cursor`
as evidence.
On replay, immutable command/effect/append/child IDs come from the original
receipt, but the response contains a freshly assembled **current** workbench,
not the stored old projection. Thus replay remains exact without rolling the UI
back after later work.

### Terminal reducer

`terminal_status`, when present, is exactly `{code, category, retryable}`.
Category is `owner_terminal`, `integrity`, `indeterminate`, or `retryable`.
Code mapping is an exhaustive allowlist, never a prefix guess; unknown/empty
terminal code is integrity/nonretryable.

Reducer precedence is exact:

1. completed Thought;
2. current live invocation;
3. current receipt-validated review;
4. benign owner terminal;
5. integrity/indeterminate terminal; and
6. retryable terminal, with Try again only if current context/admission allows.

A fixture generated from every production terminal-code write site must fail
when a code lacks one tuple. Old terminal rows cannot override newer
live/review/completed authority.

## One-turn commands

### Ask

`runAfterFlush` supplies the fresh projection, stable request ID, exact
aggregate/working/attachment CAS, and cursor. The service validates context,
freezes material, admits and binds one invocation, and dispatches at most once.
Command/reconcile responses add a complete workbench projection to their
established envelopes, so there is no follow-up GET.

### Add to Note

This is the existing answer-review lifecycle with owner copy changed. One
transaction validates current question and cursors, terminalizes it, appends
the canonical block, writes the action/effect receipt, advances working and
aggregate, and bumps continuity once. It creates no invocation.

### Add & ask next

This new exact command uses one stable `command_id`. In one `BEGIN IMMEDIATE`
it validates:

* current question/review and exact normal cursor/CAS;
* current context, continuation admission `ready`, and no competing live child;
* stable command payload hash; and
* current dispatch-host claim.

It then terminalizes the review, appends the same block, writes immutable action
and effect receipts, advances working/aggregate, freezes the post-answer
working/context snapshot, reserves one child invocation/attempt/physical Ask
ID, binds its dispatch host, and bumps continuity exactly once. All commit or
none commit.

Provider dispatch occurs post-commit. Only the stored child/physical Ask IDs,
frozen hashes, host/lease epoch, and dispatch claim authorize it. Same-command
replay returns the original IDs/effect plus current workbench. Payload mismatch
refuses. If the scheduler dies before physical binding, recovery names the
exact before-dispatch/orphan terminal; answer stays committed and replay/restart
never dispatches. If dispatch may have crossed the boundary, state is
indeterminate and likewise never redispatches.

The browser must not implement answer-then-refine chaining.

### Exact append effect

```json
{
  "kind": "clarification_appended",
  "thought_id": "thought_...",
  "working_revision": 8,
  "prior_body_sha256": "<64 hex>",
  "body_sha256": "<64 hex>",
  "append_utf8_start": 412,
  "append_utf8_end": 503,
  "append_sha256": "<64 hex>",
  "committed_post_cursor": "<explicit cursor>"
}
```

The range begins at prior-body UTF-8 length and includes the conditional blank
line plus exact block:

```text
## Clarification
Question: <validated question>
Answer: <owner answer>
```

The receipt contains no question/answer body. Server validates current input
using existing Note/review validation and refuses the whole mutation if invalid
or too large. It never truncates/coerces and introduces no new global Note limit
or legacy-data migration.

## Placement truth

The workbench uses the current canonical inference-target/Ask receipt DTO and
does not define a new placement taxonomy. Intended placement is a nullable,
advisory current target summary beside Ask. It has no invented configuration
revision and creates no admission/operation.

Actual display requires a valid combined `actual_placement` plus `egress`
receipt from the review. Normalize current optional fields as nullable in the
workbench DTO (`model`, `fallback_reason`, `egress.host`); reject unknown keys,
wrong types, over-current caps, invalid current canonical enum/combination, or
one missing half. Malformed combined proof becomes one **Placement unavailable**
state; fields are never salvaged and intended is never relabelled actual.

Golden real local proof is the current this-machine receipt:

```json
{
  "actual_placement": {
    "target_id": "this_machine",
    "target_name": "This device",
    "target_kind": "this_device",
    "boundary": "same_device",
    "owner": "you",
    "transport": "in_process",
    "data_classes": [
      "instruction", "selected_context", "grounding", "generated_output"
    ],
    "engine": "<actual engine>",
    "model": "<actual model or null>",
    "fallback_reason": null
  },
  "egress": {"scope": "local", "host": null}
}
```

First slice remains pinned to current local refinement; it adds no model,
profile, cloud, or placement selector. Placement appears only in Interview.

## Hub-local process scope

Invocation IDs, host leases, cancellation handles, physical Ask IDs, and
actual placement proof, continuity revision, invocation/review projection, and
`one invocation` invariant are hub-local. They do not synchronize or claim
global exclusivity.

A synced peer has no foreign process truth. If its own local admission is
ready, the owner may explicitly Ask there and that hub owns an independent
invocation. Consequently two hubs can perform model egress for the same synced
Thought. This is disclosed behavior and a first-slice non-goal, not hidden
global serialization. Each resulting Note mutation still meets ordinary
aggregate/working CAS; sync convergence surfaces a normal conflict instead of
silently overwriting either result.

Sync never starts, resumes, reconciles, Stops, or otherwise mutates a turn.
Opening/syncing a Thought is not an Ask. This slice makes no takeover or
handoff claim.

## HTTP and MCP exactness

The existing Thought HTTP/MCP surface keeps its current required fields.
Workbench cursor is optional/additive only on refine/reconcile/Stop,
answer/Accept/Reject, context attach/detach/refresh, and
update/complete/Resume. The Workbench UI supplies it; absent preserves legacy
CAS. Create/adopt/default/list/read remain byte-for-byte unchanged.

Add four exact tools behind `RefinementApplicationService`:

```text
thought.answer_and_continue
thought.update_working
thought.complete
thought.resume
```

The latter three wrap existing HTTP/domain behavior and keep cursor optional;
only `thought.answer_and_continue` requires the explicit cursor. HTTP enters
the same methods. After this slice the Thought family has eighteen tools. No
generic workbench-command tool is added.

Workbench state is additive to mutation responses; it never replaces, renames,
or nests established top-level fields:

* update/resume return `{thought, workbench}`;
* complete, review-action, and context mutations return
  `{thought, receipt, workbench}`; and
* refine, Stop, and Reconcile retain every existing top-level field and add
  `workbench` (`{thought, continuity, workbench}`,
  `{thought, cancellation, workbench}`, and `{thought, workbench}` under their
  current route meanings).

The standalone review read and all other legacy reads retain their exact
existing envelopes. Closed request validation permits only the one optional
cursor addition where specified; response catalogue fixtures protect all old
field names/types while allowing the additive `workbench` member.

Original chooses exact read parity, with no new DTO shape:

```text
GET /api/thoughts/{thought_id}/original
holdspeak://thoughts/{thought_id}/original
  -> {"thought": <existing include_raw=True Thought DTO>}
```

The MCP resource uses the same application method and object inside the normal
resource envelope. It is owner-only, thin/nonblocking, and invokes/mutates
nothing. Specific resource routing must match `/original` before the generic
Thought-detail template. Internal model principals and unauthorized peers
refuse.

## First-slice tool prohibition

The first slice exposes no suggested context/outcome/tool palette and parses no
model prose into an action. The internal model never receives an OWNER MCP
sidecar, OWNER token, or owner Thought/settings/grant/People tool definitions.
It has no generic `call_tool`, self-approval, or direct executor path. Any future
bounded model capability registry/derived lease/child receipts require a
separate ruled design before HS-141-07. Until then the closed interview result
is only question or synthesis and all execution remains absent.

## Fault matrix

| Event | Required result |
|---|---|
| Open/retry races | Abort prior epoch; only current Thought/epoch installs. |
| Dirty normal mutation | Drain; use returned workbench; zero downstream call on failure/conflict. |
| Dirty Reconcile | Pause; never flush or merge document authority. |
| Dirty Stop | Persist suppression without flush; retain draft; merge process authority only. |
| Edit during ASKING | Show exact replacement copy; first successful save suppresses; late result hidden. |
| Save A + edit B + authority C | Epoch discards late A; C wins; B is retained/fenced truthfully. |
| Context changes with review | Mutation supersedes review; stale question has no answer action. |
| Add-to-Note response lost | Replay same request: one append, no child, immutable effect + current workbench. |
| Composite response lost | Replay same command: same append/child IDs + current workbench, no dispatch. |
| Scheduler lost after composite commit | Answer remains; child exact terminal; no replay/restart dispatch. |
| Delayed projection/process response | Explicit cursor ordering rejects or process-only merges it. |
| Malformed placement | Whole combined proof unavailable; intended never substituted. |
| Model unavailable | **Set up AI** opens Models; Note/Attach/Finish remain useful; no dead primary. |
| Continuation admission races | Composite refuses before mutation; answer/focus stay; exact retained-answer copy appears. |
| Same Thought on two hubs | Each may explicitly Ask from local truth; duplicate egress is possible and disclosed; resulting Note writes meet CAS/convergence. |
| Forced teardown | No durable-save claim; reopen server truth. |

## Exact tests

### Service / HTTP / MCP

1. Workbench HTTP and MCP decode to the same closed object from one read
   transaction; repeated GET is zero-write/no-provider and excludes prohibited
   bodies/secrets/receipt feed.
2. Opening-query census proves one request/no waterfall. Performance harness
   proves `50ms` frame, `250ms` p95, `500ms` acceptance maximum.
3. Hub ID exists before readiness; GET cannot create it. Missing/replaced hub
   identity, cross-hub/Thought cursors, equality and relaxed comparison rules
   return exact named outcomes.
4. Continuity bumps once per committing transaction, not per changed row;
   no-op replay does not bump. Delayed response ordering passes.
5. Every terminal write-site code is in the exhaustive reducer fixture; all
   precedence combinations pass; unknown code is integrity/nonretryable.
6. State versus ambient action sets are exact in idle/live/question/synthesis/
   stale/failure/completed states. Question-ready projects composite
   primary plus quiet Add; question-unavailable omits composite and promotes
   Add. An admission race refuses before mutation, retains answer/focus, and
   returns the exact retained-answer copy.
7. Add to Note appends/terminalizes once and creates zero child. Composite fault
   injection at every SQL boundary proves all-or-none append/terminal/receipt/
   frozen child/host claim and one continuity bump.
8. Composite replay/mismatch/lost response/scheduler loss/restart/host loss/
   bound-unknown tests prove immutable effect/child IDs, fresh current workbench,
   committed-post-cursor evidence, and zero redispatch.
9. Append effect recomputes for empty/nonempty/multibyte/duplicate text. Forged
   range/hash refuses UI reveal; existing Note/answer limits reject without
   truncation or partial mutation.
10. Save returns `{thought, workbench}`. Reconcile/Stop accept only same hub/Thought,
    equal aggregate, continuity <= current, exact current invocation and valid
    state; neither returns document authority for merge.
11. Current canonical placement golden local receipt passes. Nullable fields,
    each malformed half/type/key/current cap/enum/combination, and intended-vs-
    actual mismatch tests produce exact unavailable behavior.
12. A two-real-hub test syncs one Thought, explicitly Asks independently on A
    and B, proves two honest hub-local invocations/egress receipts are possible,
    proves sync itself starts/reconciles neither, and makes resulting Note
    writes converge or surface ordinary CAS conflict without hidden global
    exclusivity.
13. Original HTTP/MCP return identical existing include-raw DTO; OWNER succeeds,
    other principals refuse; resource-template routing is exact and zero-write.
14. Eighteen-tool catalogue and closed schemas pass. A legacy body/response
    catalogue proves the exact workspace-consumed mutation list accepts an
    optional cursor, absent keeps old CAS/top-level fields, supplied enforces
    workspace law, and only the new composite requires it. Create/adopt/
    default/list/read remain byte-identical and reject invented cursor fields.
    Additive response fixtures
    prove the exact `thought`/`receipt`/continuity/cancellation plus `workbench`
    envelopes. Internal-model harness has no OWNER sidecar/token/tool
    definitions or generic tool path.

### Writer / controller / UI

1. Request epoch/abort covers retry, Thought switch, unmount, late success, and
   late error. Snapshot preview stays wholly inert until current projection.
2. Sole writer tests save A/edit B, authority C, late A, queued B, failed draft,
   conflict, close flush/veto, forced teardown no claim, tab drafts, and IME.
3. `runAfterFlush` covers every normal mutation; save response is reused with
   no GET. Reconcile pauses dirty; Stop skips flush and process-only merge cannot
   overwrite title/body/tags/draft.
4. Successful save suppresses ASKING/review and returns full projection. No
   per-save `useDesk.refresh`; Chair refresh coalesces at ruled boundaries.
5. Add to Note focus/caret/reveal is exact. Add & ask next stays Interview at
   393 with **Added to Note · View**; desktop retains Interview focus; View uses
   exact receipt range.
6. Fixed action seat retains identical DOM/grid bounds across every state.
   Exactly one visual primary exists; Interview contains no composite button,
   idle Ask text is inert, and the 393 Note proxy sends no mutation. Ready,
   unavailable, and admission-race questions prove promotion/suppression,
   retained answer/focus, and exact refusal copy.
7. Hidden pane remains mounted but hidden/aria-hidden/inert with no tab/live
   output; question arrival never steals document focus.
8. Mod behavior is correct on Mac/non-Mac and during IME; only ruled shortcuts
   fire. Optional Finish shortcut needs explicit collision fixture.
9. Context picker retains refs-only, attach error, close/focus, 393 no-autofocus,
   pinned Everyday, and review-supersession contracts.
10. Document craft rejection list is asserted by DOM/CSS geometry and counsel
    glass; first-slice DOM has no fake capability or stored-Workbench controls.
11. NotePullout ordinary/adoption behavior remains; owned Thoughts focus one
    workspace; no duplicated Thought lifecycle remains after cutover.

### Geometry / accessibility

1. `1440 × 900`: `1080 × 680` is inside safe band; Note plus fixed `360px`
   Interview are usable; body canvas meets 60%; no overflow/footer shift.
2. Below `860px`, narrow grammar activates without nested horizontal scroll.
3. `393 × 900`: sticky header/tabs/context/command leave positive pane height;
   targets >=44px; software keyboard does not cover answer or pinned context.
4. Screen-reader order is tabs -> selected pane -> context -> command strip;
   hidden pane is inert; poll does not reread document.
5. Picker/disclosure/error/reveal focus restoration is exact.

## Required glass

Use fresh isolated HOME/database and ordinary seed path. Record viewport,
browser, hub URL/PID, provider mode, request count/timing, document/body
overflow, and console/page errors. Deterministic provider must traverse real
HTTP/application/kernel/Ask/projection/reconcile/review/Note-write paths.

At `1440 × 900`, capture:

1. inert Opening frame then authoritative normal document—compact formatting
   rail present, with no WORKING badge, permanent placement, latest-action row,
   or duplicate title;
2. ASKING with saved Note version/replacement copy, then edit/save suppression;
3. continuation-ready question with strict actual local/context receipts,
   composite only in the fixed seat, and quiet Add in Interview;
4. continuation-unavailable question with composite absent and Add promoted;
   then a forced readiness race retaining answer/focus with exact refusal copy;
5. Add & ask next append marker, stable IDs, one child; Add-to-Note variant with
   caret reveal and zero child;
6. stale question non-actionable -> named repair -> new Ask;
7. no-model **Set up AI** opens Models, a saved destination restores **Ask AI**,
   direct Finish remains available; and restart has no redispatch.

At `393 × 900`, capture:

1. inert Opening then Note/question with sole **Answer question** proxy;
2. Interview ready with composite only in the fixed seat and quiet **Add to
   Note**; unavailable promotes Add into that identical seat;
3. readiness-race refusal retains typed answer/focus and shows exact copy;
4. composite remains Interview with **Added to Note · View**; View exact caret;
5. Add-to-Note switches/focuses Note directly;
6. Attach sheet with pinned Everyday above keyboard and no search autofocus;
7. stale/no-model setup/document-info/tag states with >=44px and zero overflow.

Phrase-gated provider asserts the exact saved Note and formatted frozen context.
Placement proof checks stored combined receipt, not copy. No cloud/peer/tool
glass is fabricated.

## Staged implementation

1. **P0 state:** continuity cursor/reducer, composite, append receipt, Finish
   copy, full-projection command responses, Original/MCP parity, fault tests.
2. **P0 writer:** headless sole writer, one normal mutation gate,
   process-control exceptions, local cache update/coalesced Chair refresh.
3. **Workspace:** one-request inert opening, document craft, fixed Interview and
   action seat, exact 1440/393 behavior, performance/accessibility.
4. **Move/subtract:** route owned Thoughts, remove Thought branches/footer from
   NotePullout, run glass and counsel.
5. **Later:** a separate ruled model-capability foundation, then HS-141-07/08.
   No placeholder palette enters this slice.

## Roadmap implications — not applied here

When implementation is authorized, update design truth without changing the
phase count:

1. replace ambiguous Answer continuation with explicit **Add to Note** ->
   WORKING and atomic **Add & ask next** -> one refinement turn;
2. standardize next-turn copy as **Ask AI** and completion copy as
   **Finish Thought** while transport names remain;
3. clarify that a dedicated Thought UI is allowed while generic chat/Workbench/
   tool systems remain non-goals;
4. put composition/subtraction in HS-141-09, not a tenth story;
5. record eighteen Thought MCP tools plus Workbench/Original resources only
   after implementation/guards; and
6. require a separate capability design before HS-141-07.

## Kill criteria

Stop and return to design if implementation:

* duplicates Thought lifecycle in NotePullout/workspace or creates stored
  Workbench/chat/tool/proposal/receipt systems;
* chains Answer then refine in browser or lets Add to Note/replay/restart create
  a turn;
* lacks atomic composite, immutable effect/child IDs, fresh replay projection,
  or exact scheduler-loss no-redispatch proof;
* lacks one durable cursor bump/order/reducer law or lets process response
  overwrite dirty document authority;
* bypasses sole writer/normal mutation gate or calls whole-Desk refresh per save;
* hides per-hub process independence, claims global invocation exclusion, or
  lets sync start/reconcile a turn;
* infers actual placement, salvages malformed proof, or adds a placement domain;
* provides internal model OWNER MCP/generic tools or shows fake capability;
* uses a non-inert opening snapshot, installs an aborted/late epoch, or calls
  500ms a product failure;
* moves the action seat, shows multiple primaries, loses answer caret/focus, or
  fails document craft rejection at either width;
* invents durable forced-teardown recovery or global Note migration/limits; or
* claims HTTP/MCP/Original parity not present in exact routes/resources.
