# Tonight's three repairs — release record

In progress on `fix/tonight-three-20261017`, based on `76a44ad70`.
The owner asked Astra to select and solve the three highest-cost daily issues.
Scope and settled behavior are in [PLAN.md](PLAN.md).

## Send once through a reload

The real baseline produced two command IDs, two succeeded operations, two sent
rows and two identical files when the browser reloaded before the first durable
send row. The repair saves the unresolved command, exact body and preview in
tab storage before POST. Reload restores explicit Retry. It neither dispatches
automatically nor expires an unresolved command. A storage failure blocks a new
dispatch; an in-progress response retains the original command. A fresh Send
waits for a successful history read; an exact held Retry remains available
when that read is unavailable.

The actual folder-channel regression now passes at 1440 and 393: same command,
one operation, one sent row, exact file bytes. A newer saved draft survives Retry
and Back. All eight tests in `tests/e2e/test_send_glass.py` passed in 82.25s;
43 SendWell component tests passed in 2.24s. Collection and red/green logs are in
`.tmp/tonight/send-{red,components,file-collect,file}.log`; original duplicate
facts are `.tmp/tonight/send-red-facts.json`. Paired shots and final row/file
facts are under `.tmp/evidence-shots/docs/internal/TONIGHT-THREE-2026-10-17/send-reload/`.

The paired graph walk `case.tonight.send.reload_retry` also passes through
real Note/preview/Retry/file/receipt routes after a declared browser 503.
Observations and shots: `.tmp/graph-walk/tonight/send-{1440,393}/`. The
browser 503 means its first request never reached the server; the separate
real held-server regression above proves the pre-row duplicate race. Both
observations name isolated DB paths, base revision and dirty candidate source.

This is tab-scoped reload recovery. Closing the tab or clearing its storage is
not covered; external recipients were not contacted.

## Use every explicitly attached Workbench source

Missing or unreadable sources, malformed source lists and inputs above the
unchanged 16-reference limit fail the affected item before provider dispatch.
Other valid items continue. The failure retains instruction, source references,
context and identity. Historical output artifacts stay saved; the failed
attempt has no current artifact pointer. Re-run now preserves omitted grounding
and context instead of replacing them with empty objects.

The old behavior failed 11 new cases. Final focused Python execution:
54 passed in 3.42s (`.tmp/tonight/workbench-green-final.log`); collection 54
(`workbench-collect-final.log`). Twelve rendered component cases passed in 3.21s
(`workbench-ui-types-final.log`); final TypeScript passes. A real runner/service recording feeds the failed-card and
same-ID Re-run component test; no successful model envelope is replayed there.
The runner test restores a real Note and verifies its exact text reaches the
provider seam on the same item, with one successful artifact. It also proves
valid sibling progress, cancellation during source read, no dispatch for failed
grounding, deliberate replacement/clear, and retained historical artifacts.

This does not establish the cause of the owner's earlier PR-review receipt.
Semantic quality of provider output is outside these failure-path checks.

Four actual graph cases pass: missing-source and same-ID Re-run, each at 1440
and 393. Real recipe/Workbench/Note producers and real run/update routes supply
all state. The failure has zero child calls and no artifact. After restoring
the Note, the actual Re-run PUT retains the same item, instruction, refs and
context. Nine-point hit checks prove the failure is readable after normal
scrolling in the default window. Details and exact observation paths are in
`.tmp/tonight/workbench-runtime-facts.json`, with shots under
`.tmp/graph-walk/tonight-workbench/`. The declared engine fixture supplies route
inventory only; the walk does not claim completed provider output. The rig
removes its isolated DB at teardown; observations retain actual API row payloads.

## Finish Meeting outcomes from saved analysis

The queue keeps completed analysis and unfinished local publication separate.
A committed publication pending job retains its saved summary, artifacts, route
receipt and identity. Required proposal writes and READY each check the current
executor, parent and transcript inside the writer transaction. A local failure
retries those writes from saved results; it creates no inference successor.
Skip is final, cancellation wins, and backoff lets other Meetings progress.
The existing recovery controls refresh when the open Meeting changes.

The three central old cases failed before repair. The two assigned Python files
plus the real-producer wire checks now pass 81 cases in 7.74s
(`.tmp/tonight/meeting-expanded-green.log`), including failure
before/after one proposal, fresh DB/broker resume, exact five proposals, unchanged
saved artifacts and provider counts, crashes around bridge/READY/unseen,
Skip/sibling progress, and per-insert cancellation/expiry/transcript/takeover.
The ordinary pre-marker replay is checked with a recent parent heartbeat;
stale-parent recovery is proven after publication pending or succeeded was
committed. It is not a new recovery policy for every abandoned computation.
Seven recovery component tests pass, including revision refresh, stale GET
after POST, and a previous Meeting's late action. Paired actual hub/browser
checks show retained summary, local Retry, repaired proposals and stable IDs
after reload, with zero added provider calls. Shots, facts and a retained copy
of the isolated DB are `.tmp/evidence-shots/tonight-meeting/`.
The extended walk found an additional real defect: Confirm created an action
and commitment but left the proposal's action link empty. Two regression cases
failed before repair. Confirm now saves the link in its existing transaction;
old confirmed/unlinked proposals resolve through their existing commitment,
record and same-meeting action. The final actual API/browser sequence confirms
a decision and action, completes that action, reloads, and sees the same IDs and
Done state at both widths with no new inference. Root inspected both final
shots and the retained DB. Final proof is
`.tmp/evidence-shots/tonight-meeting-followthrough-3/`; the failed API/DB witness
remains in `tonight-meeting-followthrough-2/`. The recovery wire fixture was
regenerated from actual producers; its equality guard remains intact.

The initial People warning came from an unconfigured isolated HOME: the real
relationships read returned503, normal People setup succeeded, then the read
returned an empty list. Final shots use that normally configured test store;
this does not claim the owner's People store had the same problem.

## Integration and delivery

The first ordinary quick passed4,132 related UI checks but failed the stored
recovery wire fixture (1,838 Python passes); that fixture is now regenerated.
It also recorded one Components-window HTTP503 in the sweep (108 passes),
not reproduced in the focused check or final combined sweep; its exact endpoint
and cause remain unknown. The sweep now retains the console resource URL. Canon17, TypeScript and documentation75 pass. The first
quick logs remain retained; no release is claimed from that red run.

Final ordinary quick GREEN: 4,132 related UI tests (414 files), 1,841 affected
Python tests in79.29s, all109 desktop/phone sweep cases in63.56s, and17 canon
checks. TypeScript passes. Capability/doc coverage/graph join checks and75
documentation guards pass;27 Workbench atlas checks pass. The atlas schema now
accepts the existing HTTP inventory namespace with explicit methods and strict
route tokens; the two referenced IDs exist in `static-astra.json`.
Source/build identity is `426015d9eee42d70` (built2026-10-17T07:06:50.658Z).

PR merge, formal postmerge review, idle-hub delivery and full-main execution
follow this verified candidate. Runtime walks are
isolated from the owner's HOME, database, microphone and external credentials.
Use the authenticated address printed by `holdspeak web`; a bare alternate
loopback origin is not a working Desk-entry claim.
