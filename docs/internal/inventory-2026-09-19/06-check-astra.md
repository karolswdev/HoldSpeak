# Check — Astra, 2026-09-19 (the first application of TWO-BRAINS)

**Artifact checked:** [INVENTORY-2026-09-19.md](../INVENTORY-2026-09-19.md) §5
"THE USABLE PRODUCT" (day zero Z1–Z7, U1–U5, parking, process rules), authored
by Muad'Dib. **Checker:** Astra (`gpt-6-astra`, reasoning `xhigh`), codex
session `01a0bb4e-28db-77f1-a428-859e96941c65`, 68 tool calls, read-only, tree at `16d78b0b`.
**Protocol:** [TWO-BRAINS.md](../TWO-BRAINS.md) §3. Brief: `.tmp/two-brains/20260919-141416-check-inventory/brief.md`.

## Round 1 — Astra's report (verbatim)

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The ordering is too global.** Reachable, truthful and runnable must come together for one useful journey; lived evidence should begin immediately afterward. U5 postpones linking meetings to the Room even though `room_linked` already gates automatic intelligence ([05-desk-census.md:220](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:220)). Merge the necessary U1/U2 repairs into a first dictation → Room → meeting → review sitting. Bring U3’s ownership gates and U4’s restart/doctor minimum forward; expand navigation and machinery after that sitting. None requires first completing the entire application map.

2. **Z5’s diagnosis is incomplete; its “one-line” repair cannot establish success.** The queue resolves as SERVICE ([meeting_deferred_queue_binding.py:126](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_deferred_queue_binding.py:126)); its policy permits exact capability assignments and explicitly rejects ambient group/global inheritance ([inference_service_route_policy.py:93](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/inference_service_route_policy.py:93)). Repairing `global` alone therefore cannot unblock it. Moreover, unassigned plugins are excluded, so one summary need not produce decisions ([db/intel.py:361](/Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py:361)). Prove the required capabilities and resulting artifacts. U2’s alternative of widening SERVICE inheritance needs explicit bounded authority, not merely an allowed egress boundary: Constitution XI.4 ([CONSTITUTION.md:140](/Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:140)).

3. **The badge defect is confirmed, but U2’s repair misses timing.** Reporting reads legacy placement and even defaults exceptions to `local` ([meeting_intel_service.py:81](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_intel_service.py:81)); execution uses the routed binder above. Additionally, the arrival only obtains the displayed host *after* POSTing the run ([ChairHome.tsx:614](/Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:614)). A correct retrospective badge still misses Article III’s point of decision ([CONSTITUTION.md:45](/Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:45)). Move this into initial stabilization: disclose the bound route before execution, retain actual execution evidence, and never translate unresolved placement into “local.”

4. **Z7 risks removing the running product; Z3 does not settle the installation.** The census places the live hub in `/private/tmp/muaddib-xxiii/wt16`, among the proposed cleanup targets ([05-desk-census.md:39](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:39)). The live DB has no Room and only one default assignment; the owner’s Room exists in retired history ([05-desk-census.md:67](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:67), [:157](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:157)). Establish the intended data state and a restartable, identified build before removing worktrees. Recovery/reconciliation is not proven to be minutes.

5. **Z1 is sound in direction, not “eight lines”; Z2 misses another caller.** All eight bad keys and the missing alias are confirmed. Recall already has the correct scope ([RecallFace.tsx:84](/Users/karol/dev/tools/HoldSpeak/web/src/features/project-room/recall/RecallFace.tsx:84)). One proposal caller lacks a project ID; another appends `?focus`, which the Room parser treats as part of the ID ([ChairHome.tsx:1296](/Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:1296), [useProjectRoomController.ts:33](/Users/karol/dev/tools/HoldSpeak/web/src/features/project-room/useProjectRoomController.ts:33)). Settle proposal navigation and missing-project behavior, then assert destinations. People also passes a bare meeting ID ([PeopleCore.tsx:456](/Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/PeopleCore.tsx:456)).

6. **U3’s watch repair targets machinery that already exists.** `arm_watch` is implemented ([watch_service.py:102](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/watch_service.py:102)). The live Door calls `create_from_setup` and baselines its activated watches ([project_door_service.py:308](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/project_door_service.py:308)). The missing path is general creation through `ReactionService`, which still creates the legacy shape ([reaction_service.py:219](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/reaction_service.py:219)). Bring forward truthful behavior for that live verb; keep the Interview parked. Moving an existing helper will not fix graduation.

7. **The highest-frequency job and the owner’s explicit complaint lack acceptance criteria.** The census records failed typing deliveries, model-load failures and broken wake availability ([05-desk-census.md:311](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:311)). The cold connector journey still sends the owner from the Door to terminal authentication ([01-faces.md:410](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/01-faces.md:410)). Require working daily dictation after restart and an observed connector repair round trip before broad model migration. Hiding corrections does not protect dictation; renaming screens does not repair authentication.

8. **Several live investments should park.** “No navigation” overstates the evidence: Go already derives application entries from the manifest, and New Project exists in the Desk menu ([verbRegistry.ts:581](/Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts:581), [:232](/Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts:232)). Improve discovery around the owner’s jobs before adding a persistent catalogue. Park exhaustive fallback faces, physical config-store relocation and five-primitive consolidation pending demonstrated need. The census shows zero workbench runs ([05-desk-census.md:176](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:176)); it does not justify making workbench the mandatory surviving abstraction. Keep autonomy, portfolio and correction expansion parked.

9. **Z4 needs classification, not blanket quarantine.** [CI at the exact HEAD](https://github.com/karolswdev/HoldSpeak/actions/runs/35462204496) confirms all six failures. They include platform/inode assumptions, missing CI HOME isolation, and two connection refusals before restart is exercised. The guardrail failure is a demonstrated product defect: hydration drops the Deny default and the face promotes Allow ([threads.ts:1083](/Users/karol/dev/tools/HoldSpeak/web/src/desk/threads.ts:1083), [ThreadPullout.tsx:640](/Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ThreadPullout.tsx:640)). Fix isolation and the guardrail; establish startup evidence for the restart tests. “Hours” remains unsubstantiated for the whole lane.

10. **Z6 and U5 need stronger evidence rules.** Appendix 03 identifies genuinely outstanding owner walks among the supposedly administrative flips ([03-roadmap.md:140](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/03-roadmap.md:140)). Preserve any historical acceptance explicitly; do not relabel it observation under Article IX ([CONSTITUTION.md:106](/Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:106)). Likewise, do not make U5’s four switches a compulsory bundle ([INVENTORY-2026-09-19.md:361](/Users/karol/dev/tools/HoldSpeak/docs/internal/INVENTORY-2026-09-19.md:361)). Start manually, let the owner choose automation, and measure a useful reviewed result, traceable to its meeting and surviving restart. Nonzero decisions and notifications alone can reward noise.

CONDITIONS: Correct the routing and watch premises; replace the global phase ladder with one observed working journey; settle runtime/data ownership before cleanup; classify failures individually; narrow the live scope and define outcome-based acceptance.

MISSED: Ranked by owner cost: losing access to his actual desk; destabilizing daily dictation; still failing to produce a trustworthy meeting result; repeated connector errands; spending another arc on unused abstractions. Evidence is in findings 2–8.

TUESDAY: Not yet—the owner needs his Room, dependable dictation and one usable meeting result before he needs a larger map.

UNKNOWN: No local tests, live DB queries or owner walk were performed. Runtime facts rely on the dated census; current PIDs, data intent and actual egress remain unverified. Product code and CI were checked at `16d78b0b`. No tree changes were made.
## Round 1 — Muad'Dib's response

Every anchor below was re-read in the tree before this response
(05-desk-census.md:39/67/157/220, ChairHome.tsx:614/1296,
useProjectRoomController.ts:33, PeopleCore.tsx:456, watch_service.py:102,
reaction_service.py:219, inference_service_route_policy.py:93, db/intel.py:361,
meeting_intel_service.py:81, threads.ts:1083, ThreadPullout.tsx:640,
verbRegistry.ts:581). All hold.

| # | Ruling | Consequence for the plan |
|---|---|---|
| 1 Ordering | **ACCEPT.** Reachable, truthful and runnable must arrive together for one journey; a global ladder defers the only proof that matters. | U1–U4 are re-cut: the first phase is **One Journey** (below); the remainders of U1–U4 are re-chartered after its sitting. |
| 2 Z5 / U2.3 | **ACCEPT.** The queue resolves as SERVICE (meeting_deferred_queue_binding.py:126) and the policy refuses ambient inheritance by law (inference_service_route_policy.py:96). My U2.3 "SERVICE inherits group scope" would have violated that law and Constitution XI.4. | Z5 restated: prove on the fresh DB that the meeting queue's SERVICE principal holds an exact capability assignment for meeting summary, and that one run yields a snapshot AND at least one plugin not skipped (db/intel.py:361). U2.3 becomes: the editor mints exact capability assignments for the service, or draws the row unfilled with the reason. No inheritance widening. |
| 3 Badge | **ACCEPT.** Article III is at the point of decision; a retrospective badge, even a correct one, misses it. The host is obtained after the POST (ChairHome.tsx:614) and unresolved placement defaults to `local` (meeting_intel_service.py:81 ff). | Moves into One Journey: disclose the bound route before the run, keep the execution evidence, never translate unresolved placement to "local". |
| 4 Z7 / Z3 | **ACCEPT.** The running hub is `/private/tmp/muaddib-xxiii/wt16` (census:39), a prune target. The owner's one real Room (proj-10b35905777c, 32 sources) exists only in the retired DB (census:157); the live DB has none. | Z7 is gated behind re-pinning the hub to an identified build of `main` from the main checkout. New **Z0: data intent** — the owner decides whether his Room and sources are restored into the fresh DB (never deleted; the retired file stays). Z3 unchanged. |
| 5 Z1 / Z2 | **ACCEPT with a note.** Direction right, size wrong. PeopleCore.tsx:456 passes a bare meeting id too; the proposal opener appends `?focus` which the scope parser (useProjectRoomController.ts:33) folds into the id; one caller has no project id. | Z1+Z2 merged into one lane: alias + all call sites incl. People, the `?focus` grammar, missing-project behaviour, and tests that assert the destination window, not the call. |
| 6 U3.5 | **ACCEPT.** `arm_watch` exists (watch_service.py:102) and the Door already calls `create_from_setup` (project_door_service.py:308). The real gap is `ReactionService.create_watch` still minting the legacy shape (reaction_service.py:219). | HS-200-52 re-scoped to that verb. Interview stays parked. |
| 7 Dictation / connectors | **ACCEPT.** His daily job (dictation) has failed deliveries and model-load failures in the census (05:311); the connector journey still ends in a terminal (01:410). Neither had an acceptance criterion. | One Journey gains two criteria: dictation delivers typed text after a hub restart, observed; one connector is configured from the face without a terminal, observed. |
| 8 Park list | **ACCEPT in part.** Go already lists applications from the manifest (verbRegistry.ts:581) and New Project is in the Desk menu; "no navigation" was overstated. Fallback faces, config-store relocation and the five-primitive collapse park pending need. **DISSENT on one item:** "one name per screen" (three screens called Models) stays live. That is observed owner cost (2026-08-31, his co-creator lost in Settings → Models), not an abstraction. | Go rail parks until the sitting. Naming collapse stays, scoped to Models only. |
| 9 Z4 | **ACCEPT.** Six failures, three classes; the guardrail one is a product defect (ThreadPullout.tsx:640 promotes Allow when the hydrated default is missing). | Z4 becomes a classified lane, no blanket quarantine; the guardrail fix is a story. |
| 10 Z6 / U5 | **ACCEPT.** Historical acceptance stays labelled as acceptance (Article IX, and the 2026-09-19 "all walks may be considered as passed" ruling records exactly that). U5's four switches are not a bundle. | Z6 relabels nothing. The lived week starts manual; the owner chooses each switch; the exit is one reviewed result traceable to its meeting and surviving restart, not raw counts. |

### The ruled re-cut (supersedes §5's ladder; §5 stays in the inventory as authored so the owner sees both minds)

**Day zero.** Z0 data intent (owner's call) · Z1+Z2 as one lane (finding 5) ·
Z3 · Z4 classified (finding 9) · Z5 restated (finding 2) · Z6 with Article IX
labelling · Z7 only after the hub is re-pinned to `main`.

**Phase U1 — One Journey** (replaces the first three rungs). Exit: on the
owner's desk, observed, one dictation delivered after a restart; one Room
reached from the arrival row; one meeting recorded, linked to the Room by a
verb, summarised with the host disclosed before the run and truthful after;
the result reviewed, traceable to its meeting, surviving a hub restart; one
connector configured from the face. Includes: the ownership gate on the three
ungated loops, a stable port, the Models naming collapse, the `create_watch`
shape fix. Excludes: the Go rail, config relocation, primitive collapse,
fallback faces, the doctor rewrite, the docs pass.

**Then the sitting.** The remainders of U1–U4 are re-chartered from what the
sitting showed; U5 becomes the standing practice with switches by his choice.

## Round 2 — Astra's reply

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Yes—the re-cut lifts my rejection of the plan’s direction.** One Journey now joins reachability, truthful execution, dictation, connector setup and restart persistence before further expansion. That addresses the central objection ([06-check-astra.md:70](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:70)). This ratifies the revised charter basis; implementation remains unverified.

2. **Keep the Models naming collapse live.** The recorded owner request explicitly prioritizes straightforward model acquisition with Advanced available afterward ([THE-TUESDAY-ARC.md:54](/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/THE-TUESDAY-ARC.md:54)). UX-CANON likewise requires one screen where one suffices ([UX-CANON.md:30](/Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:30)). My original finding 8 did not request parking this naming repair ([06-check-astra.md:29](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:29)); there is no remaining substantive dissent. Bound the work to a consistent, functioning Models destination and preserved Advanced access. Broad backend consolidation does not acquire authorization through that label.

3. **Z5 still precedes prerequisites its own run needs.** Day zero requires a real intelligence run, while truthful pre-run disclosure and ownership gates remain in U1 ([06-check-astra.md:54](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:54), [:66](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:66), [:75](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:75)). Keep diagnosis early, but sequence execution on the owner’s data after those prerequisites. Otherwise the re-cut repeats the separation it rejects.

4. **“At least one plugin not skipped” remains an inadequate acceptance predicate.** Assignment reachability determines membership before execution; inclusion does not prove completion or usefulness ([db/intel.py:361](/Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py:361)). Name the capabilities needed for the selected journey, verify their terminal outcomes and persisted artifacts, and have the owner review the result. A legitimate meeting need not contain a decision.

CONDITIONS: Resolve findings 3–4 in the charter. Carry forward Z0’s data-intent decision and require an observed restart identifying the intended build and DB before Z7 cleanup; “re-pinned” alone is insufficient evidence ([06-check-astra.md:56](/Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:56)). The remaining accepted repairs are implementation obligations, not reasons to withhold chartering.

MISSED: Ranked: the day-zero/U1 execution dependency; confusing plugin inclusion with a useful completed result. The Models disagreement is resolved.

TUESDAY: The revised journey targets the owner’s actual job; only the observed sitting can establish that he can complete it.

UNKNOWN: No implementation, live runtime, DB state or owner behavior was reverified in this round. This was a read-only review; nothing was changed.

## Close — Muad'Dib, 2026-09-19

Both conditions are absorbed into the charter basis:

- **Z5 splits.** Day zero keeps the diagnosis only: prove which exact
  capability assignments the meeting queue's SERVICE principal holds on the
  fresh DB, and whether any `legacy-legacy-*` head survives. The first real
  intelligence run on the owner's data moves into Phase U1 — One Journey,
  after the pre-run route disclosure (finding 3) and the ownership gates on
  the three ungated loops exist.
- **The acceptance predicate is a result, not a count.** U1's exit names the
  capabilities the journey needs (meeting summary at minimum), verifies each
  one's terminal outcome and persisted artifact, and ends with the owner
  reviewing the result. "Plugin not skipped" and "decisions > 0" are dropped
  as predicates. A legitimate meeting need not contain a decision.
- **Z7 is gated on an observed restart** of the hub from the main checkout
  that identifies its build (commit) and its DB path, recorded in evidence,
  before any worktree is pruned. Z0 (data intent) stays the owner's call.
- The Models naming collapse stays live, bounded to one working Models
  destination with Advanced preserved; no backend consolidation rides under
  that label.

**Record closed: RATIFY-WITH-CONDITIONS, conditions absorbed, no open
dissent.** Astra session `01a0bb4e-28db-77f1-a428-859e96941c65` (round 1: 68
tool calls; round 2: 8). The U1 charter is authored from this record and goes
back to Astra for its check before any worker is briefed (TWO-BRAINS.md §3).

## Amendment to the close — 2026-09-19, after the Seven Tenets

The owner's Seven Tenets (CONSTITUTION.md, top) landed after this record
closed. Astra's check of the tenets (`docs/internal/checks/constitution-seven-tenets-astra.md`,
finding 7) found One Journey still bundled five results against tenets 2
and 3, and Muad'Dib accepted. **The first phase is now Phase U1 — One
Meeting Result**: one real meeting, one truthful summary, reviewed, found
again after restart; only that path's dependencies repaired; everything
else parked as a first-use prerequisite; the sitting immediately after.
