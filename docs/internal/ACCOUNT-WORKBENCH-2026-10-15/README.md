# Accounts and Workbench refinement

Base `3d46ffdc3`; isolated worktree `wt-account-layout-20261015`. The owner showed
Accounts' connected/check-age overflow and orphan Add Jira action, then added
Workbench as another messy surface. The two bounded builder lanes use the
existing Workbench kit. No new backend, authority, provider or form framework.
The owner's later clarification identified the **opened workbench and
controls**, which is the primary target of this pass.

## Direction and repair

[Settled direction](DESIGN.md), [library canvas](canvas/index.html) and
[current Workbench source audit](AUDIT-WORKBENCH.md). Root rendered and read
Accounts, Items and Configuration specimens at 1440/393 before build; they
use declared example data and do not prove a connection or model response.
Owner judges the actual release live. Earlier result/read-recovery repairs
from #1207 remain.

Accounts gives identity, whole wrapping status, and coherent provider actions
separate room within its existing ledger. The last provider account owns Add
and the existing inline well. Mounted forms and their refusal/Retry survive
Cancel/sign-in switching behind native hidden; accepted fields clear without
erasing newer edits.
Provider Check, per-row busy refs, Add and refresh retain their actual paths.
[Exact focused Accounts proof](BUILD-ACCOUNTS.md).

Workbench uses a named inset instruction composer, grouped configuration,
folded roster/details, paper item readers and explicit instruction labels.
The shared Pad accepts native combobox attributes/ref while retaining control
of its owned values/handlers. Enter Add, Shift+Enter newline and source
selection retain existing writers and draft fences. Known missing-engine
Run doors agree, and Home counts/labels distinguish real done/running/failed
work. The source audit expressly excludes earlier repaired defects.

Root also reproduced shared Pad resize clipping on production before build:
width566→327, height stayed271 while scrollHeight rose634, overflow hidden.
The repair reuses measurement on observed width changes with cleanup.

## Verification record

Before production captures: 7 states at each width using the previous release
bundle ba2f122cf1be2253. The first desktop rig stopped on a Configure selector
when the real blank workbench says Choose agent; corrected baseline retains
its failed output separately. Root read Accounts, Items, Configuration,
Schedule and item editor shots. Recorded account wire is replayed with
relative check ages/long strings; no live provider/credential claim. The
owner's screenshot remains direct evidence of the narrower overflow; the
baseline long-label example fits at640/393 while still exposing the detached
Add row and cramped structure.

Focused proof: Accounts **65/65** (15 app plus 50 existing pane cases),
Workbench/shared Pad **87/87** across eight files followed by **20/20** in
the instruction file with its added mic pairing case (88 total current
Workbench cases). [Workbench collection and run tails](BUILD-WORKBENCH.md) and
[finished independent source review](REVIEW.md). Root read the worker logs;
TypeScript found one unsupported Testing Library query option, corrected
without a product change. The final compiler run passed.

Root's production walks captured **15 states at each width**, with no page
errors, under `after-final-1440/` and `after-final-393/`. Accounts' status text
fits its wrapping chip at both widths; Add belongs to the provider account
row. Cancel/reopen keeps site/email, the refused request keeps Retry and
inputs, and the accepted retry refreshes the account list. Account requests
are declared replays. Workbench uses real local CRUD: Home reads 3 ITEMS,
1 PENDING, 1 DONE, 1 FAILED; Shift+Enter adds a newline without submission;
an unavailable Add preserves the complete two-line draft and Retry saves it
exactly once. Agent binding is stored by the real producer. Configuration,
custom library mode/schedule controls, item instruction/result material and
the missing-engine Runs repair were inspected. Schedule firing was not run.

The first after desktop rig stopped on a title selector that matched both the
original item and the newly added item. Its output remains in `after-1440/`;
the final rig uses the exact existing item title. Screens and geometry,
including the bound identity in the Schedule shot, were read by root.

Actual width resize now measures Pad **518→287 px**, height **303→712 px**;
at the narrow width clientHeight and scrollHeight both equal 712. The original
bundle kept height 271 while scrollHeight grew to 634. Both observations and
shots remain in `resize-before/` and `resize-after/`.

The graph rig's real producer case `case.workbench.add.multiline` passed at
1440 and 393, with pointer and native browser touch respectively. In each,
the first click dispatched POST items, returned 201, and the GET predicate
observed exactly one item with both lines intact. Initial feedback and terminal
outcome were separately read: settled in 1.074/1.084 seconds, within the 30
second bound. Root read before/after shots and verified the fresh HOME/DB
paths, base revision with dirty source and no model substitution. Outputs:
`graph-add-1440/20261015T155236Z-case.workbench.add.multiline-astra-1440/`
and `graph-add-393/20261015T155306Z-case.workbench.add.multiline-astra-393/`.

All runtime paths above are under `.tmp/account-workbench/`, not tracked
observations. Initial after proof used bundle `ef27afd1e6fb65ab`
(`index-PSToqurJ.js`).

## Wider check and fixes

The first combined quick check found 3 web failures (4929 passed), 651 affected
Python passed, 107 desktop/phone sweeps passed (2 existing xfails), and one
canon failure (16 passed). Its logs remain in `quick-final/` and
`quick-final.log`; they are not reported as green.

Two existing pane cases exposed form remount/refusal loss during a sign-in
detour. The repair keeps the same Add subtree mounted and native-hidden in
both populated and empty provider rows; closed expansion space/tint is hidden
by scoped CSS. The original pane tests are unchanged. Both lifecycle paths
have red/green proof in BUILD-ACCOUNTS.md.

The shared Pad uses the existing Workbench grammar mic, which writes the
instruction and resolves its references. A second default Pad mic would create
two capture paths. The canon scanner now records that exact field/path in its
existing named exception ledger. Label exceptions match their own tag, so an
adjacent field cannot inherit one. The new real-component test injects at the
MicButton transcript callback and checks the full Add payload and resolver
path; it does not claim microphone hardware. Scanner collect/run: **58/58**,
including unrelated neighboring/different-face opt-outs. A stale exception
for Thread's old raw checkbox was parked; base already uses CheckGadget.
The ceiling did not change.

The wider related web selection also exposed the unchanged container guard
counting retained `_parked` CSS. Both the failing test and CSS were already in
base. Its glob now excludes parked sources like the canon scanner, while
requiring active global CSS so an empty glob cannot pass. Exact focused red
then green: `container-law-before.log` / `container-law-fixed.log`.

Final source re-check: RATIFY, no confirmed remaining finding. The reviewer
records the missed Accounts lifecycle defect and the bounded repair.
Root repeated the production walks after the lifecycle repair:
**16 states at each width**, `release-walk-1440/` and `release-walk-393/`, no
page errors. The added detour explicitly hides the refused form, opens Sign
in, and reopens the same Add flow with its email, refusal and Retry intact;
the accepted request then refreshes the third account. The declared replay
marks an existing example account as requiring sign-in. Root read the final
account rows, restored refusal, opened Workbench controls and readers at
both widths. All earlier actual CRUD predicates still pass. These walks
used bundle `cfa38b02306c2789` (`index-BBA5A_Ui.js`). Release TypeScript passes.
Final combined quick rerun **GREEN** against `3d46ffdc3`: build passes,
**4935 web tests / 521 files**, **709 affected Python tests**, **107 desk
sweeps** at both widths (2 existing xfails), and **17 canon guards**.
Logs: `quick-release.log` and `quick-release/{build,vitest,py,sweep,canon}.log`.
Root read the run tails and final verdict. Product source remained frozen;
the final build ID is `cfa38b02306c2789`, matching the final browser walks.
The quick check does not cover canvas files outside web/src; root rendered
and read those before build as recorded above. No ceiling was raised.

Capability documentation check passes (10 generated outputs); graph join
check passes with the same 14 pre-existing subtype notes. There is no existing
Workbench/Accounts-row capability metadata record to update; unrelated
activity connector claims were not repurposed. Routes/backend are unchanged.

## Limits

All walks use isolated HOME/DB/keystores. Account GET/Add/Check are declared
wire replays for layout, API dispatch and draft testing; they prove no native
sign-in or provider health. Workbench CRUD uses real local producers; authored
results/status edits are not inference or a real running agent. No microphone,
OS clipboard, external dispatch, actual schedule firing or physical phone
claim. Owner acceptance, full main tape and Astra postmerge review are separate.
