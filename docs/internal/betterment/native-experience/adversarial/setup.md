# setup

Job: Check device readiness and use what was found  
Baseline: `55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_setup`  
Evidence class: source/assertion inspection plus supplied 1440/393 captures; no tests, live calls, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The public job is larger than “readiness”: `holdspeak doctor` must repair a
broken installation or state its limit (`docs/USE_CASES.md:19`), while Setup
must find local facts, adopt resources, show outcomes, and return the owner to
work (`docs/internal/betterment/setup/RECIPE.md:120-230`). The brief inspected only
`web/src/pages/cores/SetupCore.tsx:1-100`, the parked body. The
active component at `web/src/pages/cores/SetupCore.tsx:200-209` loads
`/api/setup/found` and renders `SetupFace`; it is not the doctor/status face.

FINDINGS:

1. **P0 — The active family and public repair boundary are absent.** The named
test, `tests/unit/test_setup_status.py:39-211`, proves the doctor adapter, not
the active found/adopt flow. Meanwhile
`docs/OPERATIONS.md:21-45` says Setup shows doctor checks, but
`web/src/desk/firstrun/SetupFace.tsx:55-83,260-306` consumes a different inventory and
`web/src/pages/cores/SetupCore.tsx:30-198` is parked. Cost: implementation can improve the wrong
screen while doctor, Engines, and Setup disagree. This fails Tenets 2, 3 and 7. Correction: bound the audit to
both surfaces and state the split: doctor/status repairs runtime readiness;
Setup adopts found resources; Engines owns per-job assignment/readiness.

2. **P0 — Workflow identity, receipt and recovery are missing.**
The route returns kernel fields and a receipt (`holdspeak/web/routes/setup.py:93-108`),
but `web/src/desk/firstrun/SetupFace.tsx:338-390` reduces the answer to a local row state, rereads,
and drops the receipt. “Use everything” presses rows serially
(`web/src/desk/firstrun/SetupFace.tsx:420-422`) even though the shared operation supports `id: all`
and per-row outcomes (`holdspeak/setup_operations.py:59-84`; `holdspeak/services/setup_service.py:484-540`). The face does wait for `actionAnswer` and rereads inventory; it does not optimistically declare every row working. Cost: a timeout/reload can lose the immediate operation handle or make a partial aggregate harder to reconcile.
This fails Tenets 3 and 6 and Constitution Article IX. Correction: join UI/CLI/MCP row outcomes to their existing operation receipts and inventory facts; define retry and interrupted-return semantics. Both UI and backend may process rows serially; serial execution itself is not a defect and does not require a new workflow graph.

3. **High — Setup and Engines claim the same engine job.** Setup engine use
sets a global assignment (`holdspeak/services/setup_service.py:546-566`),
while Engines computes readiness and fit per job, including speech exclusion
(`web/src/features/runson/model.ts:346-367`; `web/src/features/runson/RunsOnCore.tsx:740-788`). Assertions keep Speech
unassigned while other jobs use a text engine
(`web/src/features/runson/__tests__/engines.app.test.tsx:496-516`). Cost: a
Setup adoption success can be mistaken for readiness of every task. The service explicitly selects Everything else and already excludes speech; that is a useful boundary, not a speech-assignment defect. This fails
Tenets 3 and 6. Correction: Setup records “engine adopted” and hands off to
Engines for capability fit; never imply all jobs are ready, and keep speech
separate.

4. **High — return-to-work and narrow-screen fast path are unspecified.**
`web/src/desk/firstrun/SetupFace.tsx:442-445` always seeds onboarding and opens Today, even when
Setup was opened from Settings or a recovery door; it does not preserve the
origin surface. The supplied 393 capture (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-setup-393.png`)
shows the face ending at “Your name”, with people, Not found and Open my desk
below the viewport; imports at `web/src/desk/firstrun/SetupFace.tsx:9-18` have no `ScrollHint`. Cost: a tired owner loses the task that sent him to Setup and
has no demonstrated discovery path to the remaining work at 393. Below-fold content and lack of a ScrollHint import do not by themselves prove scrolling is broken. This fails Tenets 3, 5 and 6.
Correction: separate first-run handoff from later repair, preserve origin and
focus, and prove a named scrolling well at 393.

## Convergence

`engines_assignment` consumes the adopted engine/profile and owns job fit;
`accounts`, `agent_hand`, `people_prep`, `feedback`, `speech_dictation` and
`settings` can reuse operation outcome, stable identity, state, egress,
`SurfaceRow`, `StateChip`, `EgressChip`, and receipts.
Keep Setup as the first consumer of found-resource adoption, not a second
Engines registry or a generic doctor wizard. Do not merge all boundaries:
doctor diagnostics, Engines capability selection, and Setup’s local fast path
have different owners and recovery.

## User experience

The supplied 1440 capture shows a legible “Use everything found”, found rows,
and egress placement; the 393 capture shows useful stacking but an incomplete
first view. That is a source/capture judgment, not beauty or owner delight.
Interrupted adoption and a Today-only return need a stated Tuesday policy; serial row processing itself can be appropriate.

CONDITIONS: inspect the active SetupFace and assertions; define doctor versus Setup versus Engines ownership; converge operation IDs, receipts and recovery; specify origin return and 393 scrolling before implementation.

MISSED:

1. Doctor failure repaired from Setup, with the same state after restart.
2. LAN/text engine adopted while Speech remains unassigned and fit is visible.
3. Aggregate adoption interrupted or retried without duplicate effects.
4. Setup opened from Speak/Engines returns to that task at 393.

TUESDAY: Not yet—the face can find and press things, but cannot promise a repairable, recoverable return to the owner’s actual work.

## Acceptance challenges

1. On a fresh desk, press **Use everything found**; one workflow yields every row’s terminal result, reload preserves it, and retry does not duplicate an effect.
2. Adopt a LAN text engine; Engines shows per-job fit, Speech remains `No engine`, and Ask names the actual host.
3. Repair a missing speech model from the Speak recovery door, restart, and return to Speak with its draft/focus intact.
4. At 393, reach People, Not found and Open my desk; the well is announced and return preserves origin.

UNKNOWN: No tests or live configuration/API/provider/native/performance/owner-state actions were performed. Captures are not owner acceptance; anchors may drift.
