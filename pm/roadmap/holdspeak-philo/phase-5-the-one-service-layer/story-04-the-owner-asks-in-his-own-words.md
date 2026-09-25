# PHILO-5-04 - The owner asks in his own words

- **Project:** holdspeak-philo
- **Phase:** 5
- **Status:** done
- **Depends on:** PHILO-5-03
- **Unblocks:** the phase close
- **Owner:** Astra (Luna); Muad'Dib checks
- **Owner review:** PENDING; technical lane completion is separate (amendment below).
- **Council tag:** the owner's D3 and proof mode; Astra r2 Closing proof

## Problem

The owner ruled the closing use: Codex drives it (D3), rehearsed, the owner skims shots (proof mode). Until the loop runs from a normal-language request through Codex against an isolated hub, the catalogue is not shown to be client-neutral, and the owner has no evidence that the job lands on the Desk. Story 01 proves the path (`scripts/graph_walk.py:1494,1517`, `holdspeak/mcp/server.py:119,144`, `scripts/astra:20,50`); this story uses it for the whole job.

## Scope

- **In:** Astra drives the normal-language meeting job through Codex against an isolated hub (import, summary, decision, next-day brief, the Thought's save); the MCP transcript and the Desk shots at 1440 and 393 retained; Muad'Dib checks; the owner reviews the shots.
- **Out:** everything the phase status lists as out; a live sitting; the owner's own client; already-open brief refresh (the shots use a fresh/reopened Desk read for the brief).

## Acceptance criteria

- [x] The request is ordinary words; no operation name, argument or test clock appears in the request, and the owner is never asked to operate them.
- [x] Run against an isolated HOME via the story 01 Codex configuration; the effective HOME, lock and DB path retained; never the desk.
- [x] The MCP transcript and the Desk shots at 1440 and 393 are retained: the summary, the decision, the dated next-day brief and the saved Thought on the Desk; summary delivery without manual refresh; the brief on a fresh/reopened Desk read.
- [x] Real-engine and replayed runs, if both occur, are retained and labelled separately.
- [x] Technical rehearsal completes with Muad'Dib's check recorded; the evidence
  reads "REHEARSED; OWNER REVIEW PENDING" and never as an observed sitting.
- [ ] The owner reviews the published shots; record the review in the tree.
  This downstream item remains pending at the technical lane's done flip.
- [x] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

Fence-law proof: [000904Z](assets/story-04-shots/verification/receipt-tests/run-20260925T000904Z.out), [001056Z](assets/story-04-shots/verification/receipt-tests/run-20260925T001056Z.out), [001255Z](assets/story-04-shots/verification/receipt-tests/run-20260925T001255Z.out), and [recorder mutation outputs](assets/story-04-shots/verification/recorder/).
[Closing check and conditions paid](checks/story-04-closing-muaddib.md).

Technical acceptance proof: [rehearsal record](../../../../docs/internal/philo/phase-5/his-words/rehearsal.md),
[final transcript and config](assets/story-04-shots/final/20260925T001407Z-his-words-real/observations.json),
and [evidence](evidence-story-04.md). No replay was used for the closing rehearsal.

## Carried in from story 03

The lane brief assigns these six items as work or as an explicit ledger
entry with a reason. This section was absent from the lane's starting
revision, `9c653937`; the items are traced to [story 03's ledger](story-03-lane-report.md#ledger)
and the phase's Decisions deferred. A ledgered box means accounted for,
not fixed.

- [x] **PAID — Import fixture hash:** the actual S1 op case cites the real
  fixture hash in both the op step and provenance. [Observation](assets/story-04-shots/carried/import-hash-op/20260924T234859Z-case.closure.chain.s1_import_complete.op-astra-1440/observation.json),
  [structural mutation red](assets/story-04-shots/verification/recorder/mutation-hash.out).
  Old observations remain intact.
- [x] **LEDGERED — Shelf refusal before registry dispatch:** preserve the
  transport-schema origin and never count that branch as registry reach.
  [Ledger, row 1](story-04-lane-report.md#ledger).
- [x] **PAID / LEDGERED — Missing-decision refusal:** the actual HTTP/browser
  and canonical op pair both refuse, but observer parity is **FAIL: 2 rows
  versus 1**. [HTTP rows](assets/story-04-shots/carried/verification/missing-browser-missing-id-rows.txt),
  [op rows](assets/story-04-shots/carried/verification/missing-op-missing-id-rows.txt),
  [repair ledger, row 2](story-04-lane-report.md#ledger).
- [x] **PAID — S4 at 393:** saved decision content is readable on the face;
  the real producer's before predicate is false and the after predicate passes.
  [393 shot](assets/story-04-shots/carried/s4-393/20260924T233554Z-case.closure.chain.s4_saved_content-astra-393/after.png),
  [observation](assets/story-04-shots/carried/s4-393/20260924T233554Z-case.closure.chain.s4_saved_content-astra-393/observation.json).
  The same case also passes at 1440; this closes missing proof, not a product repair.
- [x] **LEDGERED — Empty import shown as SAVED:** named seams, owner cost,
  and product follow-up owed. [Ledger, row 3](story-04-lane-report.md#ledger).
- [x] **LEDGERED — Transient zero-decided toast:** named seams, canon failure,
  and product follow-up owed. [Ledger, row 4](story-04-lane-report.md#ledger).

The inherited decision-admission question remains separate, unruled, and
assigned to the owner's ruling / later phase as recorded by story 02.


## Carried in from story 03 (Muad'Dib's counsel C3 — work, not notes)

- [ ] SAVED shown on the Arrival while the durable state is `import_failed` (an empty VTT import): the face must not lie — fix the honest state (no design; the existing failure idiom) with a fence red pre-fix, or a named follow-up with a fence-as-observed if the fix needs a canvas.
- [ ] S4 at 393: after Done the reading view is blank — cause found; fixed if product-only, else ledgered with the shot.
- [ ] One missing HTTP decision read produces TWO broke rows (`holdspeak/web/routes/decisions.py:58-61` falls through from the registry NotFound to the lifecycle service): one cause, one row; fence red pre-fix.
- [ ] Shelf schema drift: the MCP tool enum refuses before dispatch while the descriptor says it will not pre-empt (`operations.py:421-431`) — align (descriptor or schema) with a schema-alignment fence.
- [ ] Structural fence: the rig (`scripts/graph_walk.py`, `philo5_pairs.py`) never imports `holdspeak.operations` in-process (a second composition); red by mutation.
- [ ] Ledgered: op observations carry a forced `viewport: 1440` label and a `-1440` run id — a reader can take an op run for a face; note it in the rig's observation schema or drop the label for op runs (small).

## Effort (council-style estimate, not a promise)

1 day (Astra r2)

## Test plan

- **Unit:** scoped recorder and transcript/prompt fences, plus the actual-atlas
  schema fence. Existing Codex-seam and graph-rig tests run with an isolated
  HOME. No full suite or metal test, as the lane brief requires.
- **Integration:** the Codex → proxy → isolated hub run, transcript and shots retained under this phase's assets.
- **Manual / device:** the owner reviews the shots (rehearsed, owner-reviewed shots — PENDING; not a sitting).

## Notes

- 2026-09-24 — chartered from draft r3 + Astra r2 (`checks/charter-astra-r2.md`, the Closing proof position and the story-04 amendment).

## AMENDMENTS — owner's lane brief, 2026-09-24

The owner directs: "flip via `dw story status … done` after evidence" and
"push; PR to main; do NOT merge — Muad'Dib counsels on built and PUBLISHES the shots for the owner's review."
This orders technical completion before the downstream review. The original
combined acceptance is visibly split above. The technical done flip does not
complete owner review. Phase exit criterion 5 stays unchecked until that
review is recorded in the tree. The story row, evidence, phase update and PR
carry **OWNER REVIEW PENDING**. [Both brains' scope check](checks/story-04-scope-muaddib.md).

The original "Unit: none new" test plan is also amended: complete server-side
MCP recording and the prompt/write-path invariants require focused fences.
These preserve real producer behavior and receive deliberate mutation reds.
The recorder supplies a server witness; the Codex transcript supplies the
client witness. Their calls and results must reconcile.

The owner's same brief requires `Brief ready …` with the next-day brief on
Arrival. Muad'Dib ratified the diagnosed receipt seam: the existing Article
III receipt now also identifies the latest durable brief on a fresh read.
This is a narrow semantic amendment to the phase's no-face-change scope,
not a new layout, wording or already-open refresh promise. The real missing-
receipt shots and a rendered pre-fix red must precede the surgical change;
a later Generate must replace the receipt using a different real producer
payload. [Design and check](../../../../docs/internal/philo/phase-5/his-words/receipt-seam.md).

The former 202 empty-brief/reload test was replaced. Its empty-headline
assertions remain in `briefLoadAndDate.philo303.test.tsx:135` and
`triagedHeadline.philo404.test.tsx:225`; quiet-branch Generate remains in
`generateAlwaysReachable.philo401.test.tsx:315`. These surviving fences
are named in the lane report and closing-check evidence.
