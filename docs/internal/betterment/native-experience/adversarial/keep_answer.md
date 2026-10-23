# keep_answer — adversarial review

Workflow id: `keep_answer`  
Job: Keep a useful answer as an Artifact with its source  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`  
Reviewer task: `review_keep_answer`  
Evidence class: source inspection and representative assertions; no test execution, owner observation, or live walk.

VERDICT: DO-NOT-RATIFY

## Totality

The active job starts in Ask, sends a frozen question/context to `/api/ask`,
shows an answer, and keeps the conversation as a durable thread
(`web/src/desk/components/AskPanel.tsx:457-503`). Its answer verbs are Save as
note, Copy, Send, Add to note, and Make it a task
(`web/src/desk/components/AskPanel.tsx:820-867`); Save as note writes answer
text plus human-readable “Looked at” names into a Note
(`web/src/desk/ask.ts:521-539`). The live test asserts Keep and Bin are absent
(`web/src/desk/__tests__/ask.app.test.tsx:282-295`). The brief’s “Ask can retain
a result through the object model” therefore describes an orphaned helper/route,
not the active job. `ArtifactPullout` only reads an Artifact already present
(`web/src/desk/pullouts/ArtifactPullout.tsx:18-42`).

The family must respect the owner’s settled boundary: every Ask is kept as a
thread, with no Keep or Bin (`docs/internal/betterment/DECISIONS.md:47`); the
recipe specifies Save as note (`docs/internal/betterment/asking/RECIPE.md:164-180`).
Audit that shipped job and reconcile the older public Artifact promise. A direct
Artifact endpoint is a separate surface/client contract, not authority to restore Keep. They are not interchangeable: a Note is
editable/sendable; an Artifact is a run result with durable lineage.

FINDINGS:

1. **P0 — the audited job is not reachable.** Evidence:
`web/src/desk/components/AskPanel.tsx:835-841` has no Keep action;
`web/src/desk/ask.ts:544-572` exports `keepAsk`, but no active caller exists;
`tests/unit/test_web_routes_ask.py:434-485` only proves a direct route/service
path. Owner cost: implementation could polish a dead route while Tuesday’s
user can only create a Note, violating Tenets 2 and 3. Correction: re-scope the Desk audit to saved threads/Save as note and fix the
public-guide mismatch. Audit any separate supported Artifact consumer explicitly;
do not add Keep back against the owner’s decision.

2. **P1 — the proposed Artifact would not preserve actual lineage or
boundary.** `AskRunResult` contains `egress`, receipt, grounding,
and `lookedAt` data (`web/src/desk/ask.ts:130-184`), but `AskTurn` drops route
and receipt fields (`web/src/desk/ask.ts:394-403`), and the Keep payload accepts
only lens, prompt, output, and context (`web/src/desk/ask.ts:544-568`). The
service records only those context refs and falls back to a synthetic `card`
source when context is empty (`holdspeak/services/ask_service.py:1160-1172`).
The Artifact type has no egress/receipt fields (`web/src/lib/primitives.ts:159-170`),
and its pullout renders sources but no run boundary (`web/src/desk/pullouts/ArtifactPullout.tsx:61-86`).
Owner cost: a whole-desk answer can be kept with a generic title instead of
the records read, while cloud/private-network use disappears; this fails
Tenet 3 and Constitution Articles III and VI. Correction: persist exact
looked-at/grounding refs plus run route/receipt in the existing Artifact
contract, then show the boundary at the result.

## Convergence

Converge with `ask_whole_desk` (run snapshot), `source_context` (typed
selection), `threads` (turn identity), `notes_editor` (editable Note), and
`feedback` (write outcomes). First consumers are AskPanel and the active Note workspace; ArtifactPullout is conditional on a separately established Artifact consumer.
Keep Note and Artifact separate: merging them erases the editable-document
versus run-linked-result boundary. Reuse the existing registry, pullout,
thread identity, and feedback; do not invent a result store.

## User experience

Source inspection predicts a clear answer-reading face and useful recovery:
the answer remains in a thread, sources are folded/linkable, and failed
Artifact reads expose Retry (`ArtifactPullout.tsx:46-50`). The Artifact-labelled audit does not describe the actual fast path; the user must choose a Note whose
provenance is plain text. No capture was inspected in this review, so beauty, touch
reach, and owner delight are unknown. Preserve the existing Save as note action and same-thread return; a second Keep
action is not the correction. Improve retained source links and truthful outcomes.

CONDITIONS: Align scope with the owner’s no-Keep decision; preserve exact source
and route/receipt snapshots for the active saved result; specify stale-source
behavior and restart recovery. Describe separate Artifact consumers only where supported. Keep source links and
the no-egress/local boundary honest.

MISSED:

1. Highest cost: whole-desk retrieval where `lookedAt` refs differ from the
selected About set.
2. A source changes or disappears between answer and Keep; the answer must
remain readable while Keep names the refusal and permits a deliberate retry.
3. A local versus private-network/cloud run whose boundary must survive in the
kept record and after restart.
4. Reopen the Artifact after a Desk restart, open its source, and return to the
originating Ask without a duplicate.

TUESDAY: The owner can ask and save a Note today, but cannot complete the
audited “keep this answer as an Artifact with its source” job from the active
Ask face.

## Acceptance challenges

1. Ask about one Note, choose Save as note, and verify one editable Note with the exact answer and durable typed source links; the originating thread stays available and no Keep/Bin returns.
2. Ask the whole Desk where retrieval finds a different record set; the saved result retains those exact refs, not only display titles or the selected About set.
3. Change or park a source before saving: the answer remains readable, the existing Artifact endpoint's named refusal is honest if invoked, and the active Note path does not falsely claim a current source. Specify whether it retains a historical snapshot or refuses; do not add a blanket freshness gate to keeping useful text.
4. Save a cloud/private-network answer, restart, reopen the actual saved type, and verify its origin/run boundary and usable return to the thread. A separate Artifact client, if in scope, must prove its own handoff.

UNKNOWN: No tests or live Ask/provider/native/database/owner walk were run.
Existing route and component tests prove seams only, not the active Artifact
job, appearance, performance, accessibility, or owner acceptance.
