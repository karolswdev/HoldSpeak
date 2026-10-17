# Three daily-work repairs — 2026-10-17

Owner instruction: pick the three most pressing items and solve them tonight.
This continues the flagship programme with Sol HIGH builders and Astra owning
selection, integration, verification and delivery. Base `76a44ad70`; worktree
`/Users/karol/dev/tools/wt-tonight-three-20261017`, branch
`fix/tonight-three-20261017`. The last product full run passed16,580; these are
newly diagnosed gaps, not a reopened claim that the earlier116 cases failed.

The Tuesday jobs are: send a report once despite a reload, leave a meeting with
its useful outcomes intact, and trust a Workbench to use the attached evidence.
These rank ahead of the observed localhost/127.0.0.1 entry mismatch. Same-origin
credential persistence already works; no auth bypass or sign-in framework is
part of this work. Tenets1,2,3,5,7 govern the scope.

## 1. Retain an uncertain Send across reload

Current SendWell keeps its command/body/preview only in a module store. Slow
pre-dispatch verification can precede the durable channel_sends row. A reload
then loses the key while the sends list is still correctly empty; another
press can dispatch under a second command. Anchors: SendWell64/406,
channel_service574/608, project_kernel274. Verify anchors; they drift.

Persist the unresolved command synchronously in tab storage before POST.
Restore the original document/target/body/preview and explicit Retry after
reload; never send automatically. Retry uses the identical command. Settlement
or a terminal refusal clears it; operation_in_progress retains it. A storage
failure must not dispatch a command whose reload custody was not established.
Retain existing post-boundary authoritative sends/receipts and later distinct
Send again. Preserve draft and document isolation. No TTL that silently turns
an uncertain send into a new command; no new delivery queue/framework.

Existing ratified SendWell composition is the direction: original preview,
named uncertain outcome and its existing Retry in the same well. No new face,
modal or settings. Before/after screenshots cover desktop and phone.

Exclusive lane: `web/src/desk/surface/send/SendWell.tsx`, a small pending-command
helper beside it, its component tests, `tests/e2e/test_send_glass.py`. The shared
channel words file may change only for the named local-storage refusal/retry
reason; coordinate its exact path with root. No backend delivery rewrite.
Prove the old failure with the real isolated folder channel: hold before its
durable boundary, press, reload, Retry, release; one command, row and exact file.
Also cover post-boundary settlement, unreadable sends, and in-progress refusal.

## 2. Complete Meeting follow-through from saved analysis

The queue commits a succeeded job/READY Meeting before bridging extractor
artifacts to proposals. Bridge exceptions are swallowed. Restart's existing
terminal-parent repair closes the parent without doing that work. Source:
intel_queue681/688/805, db/intel1801/1809, proposal_bridge_service1218/1249.

Saved computation and completed local publication must be distinct facts.
Retain saved summary, artifacts, route receipts and job identity on a bridge
failure. Repair the deterministic local publication from those saved results,
without a fresh model call, successor inference job or changed route. Required
proposal publication precedes READY/unseen notification and parent completion;
source suggestions remain best effort. Settled durable transition: after the
provider/plugin artifacts have finalized, retain the same claimed job with its
existing `lifecycle_posture` set to `publication_pending`. Required publication
runs before normal complete_bound/READY. A recovered pending job bypasses
bound.execute entirely and uses only saved artifacts. Existing lease takeover,
parent epoch/deadline and transcript fences still apply. A failed local repair
uses requested_at as its next due time; this posture alone observes that due
filter, allowing other queued work to progress. Local Retry makes the same job
due; it never creates an inference successor. Skip is allowed only without a
live pending bearer and ends that row permanently. Eligible old succeeded/OPEN
rows with a missing close adopt this same guarded repair; cancelled, expired,
closed, skipped or changed-transcript work does not publish new proposals.
Each proposal INSERT and final READY transition check the exact publication
job/lease/epoch/parent/transcript inside their writer transaction. The existing
proposal bridge and proposal repository may gain that narrow optional guard;
other callers retain their current behavior. No new queue, table or framework.
Confirm must retain the exact action ID it creates; a completed action stays
Done after reload. Existing confirmed proposals with a missing link resolve
through their saved commitment, decision record and same-meeting action. No
migration is needed. This defect was reproduced by the final follow-through
walk; the existing producer wire fixture is regenerated without weakening its
equality assertion.
Partial bridge/restart must not duplicate proposals. Skip/cancellation must not
be reversed by a repair scan.
The abandoned-parent reaper must leave this exact pending publication eligible
for repair while its deadline remains valid; its close transaction must not race
the transition into publication pending. Cancellation remains authoritative.

The existing Meeting recovery slab is the direction: retained summary,
plain incomplete-outcomes state and local Retry. Refresh it on record revision
with stale-read protection, so an already-open Meeting exposes the recovery.
No new workflow. Exclusive lane: `holdspeak/intel_queue.py`,
`holdspeak/db/intel.py`, `holdspeak/services/meeting_intel_service.py`,
`holdspeak/services/proposal_bridge_service.py`, `holdspeak/db/proposals.py`,
the specific pending-publication close-time fence in
`holdspeak/kernel/parent_terminal.py`,
`web/src/meetings/MeetingIntelRecovery.tsx`, its existing component tests and the
revision prop in `MeetingDetail.tsx`/`MeetingRecord.tsx`; focused Python outcome/deferred-admission
tests. Any extra shared path requires a scope decision, not a sibling edit.

Prove failure before/after one proposal, restart at completion boundaries,
same saved computation and exact rows, zero extra provider calls, local Retry,
no resurrection after Skip, and updated recovery controls at1440/393.

## 3. Refuse incomplete Workbench grounding

The conductor logs unknown references/hydration exceptions and returns partial
or empty grounding; the runner dispatches anyway and can publish a done item.
Source: workbench_conductor215–221, services/workbench_runner287–305,
kernel/workbench_projection40–41. This does not establish the cause of the
owner's earlier PR-review result; it establishes a current failure path.

Explicitly attached sources must all resolve before this item's provider call.
Missing/unreadable grounding produces a named per-item failure, no output
artifact and no provider call. Preserve instruction, references and identity;
valid siblings continue. Empty attachment sets remain valid. Do not silently
drop explicit references at the existing limit; refuse an over-limit input
with the existing limit intact. Restore the source and Re-run the same item
with its exact content. Keep cancellation/epoch ownership intact.

The existing failed-item treatment and Re-run are the composition direction;
no new picker or workflow. Exclusive lane: `holdspeak/workbench_conductor.py`,
`holdspeak/services/workbench_runner.py`,
`tests/unit/test_conductor_ref_hydration.py`,
`tests/unit/test_workbench_runner_migration.py`, and the existing
`workbenchOperates.test.tsx` rendered transition test. Shared hydrator changes
require root agreement. Prove missing and mixed sources, hydration failure,
valid sibling progress, durable input/failure, no false artifact, same-item
retry after source restoration and desktop/phone observation.
The failure test also exposed Re-run clearing grounding/context because the
update service supplied None for omitted fields. Preserve those existing values
in `holdspeak/services/workbench_service.py`; explicit replacements still apply.

## Worker and release discipline

Each worker changes only its exclusive files and verifies current anchors.
Other lane paths, root docs, serving/proof trees and owner data are do-not-touch.
Focused budgets are the named files/cases only; root approves a directly
necessary expansion. All test/build/browser/bootstrap jobs serialize through
`scripts/test_lock.py` with isolated HOME, native effects/real CLI disabled,
private test keystores and no owner credentials/providers/microphone. Never
run `tests/e2e/test_metal.py`. Real producers and exact saved rows/files are the
proof; fabricated successful replies and relaxed assertions are not.

Workers supply collection output, red/green run tails and screenshot paths;
HOLD FOR SHIP, no staging/commits/merge/deployment. No destructive git verbs.
Root reads the evidence, checks the integrated job, runs the ordinary quick,
merges under CLAUDE's fast cycle, formally reviews after merge and delivers
normally when the owner hub is idle. Full-main execution follows the product
merge and failures are fixed forward. Source/build equality, current runtime,
the three outcomes and remaining limits go in the release record and STATUS.
