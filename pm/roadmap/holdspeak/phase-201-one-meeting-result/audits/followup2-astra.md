# Lane A follow-up 2 — summary route reporting

Astra session: `01a0bbc3-9bbd-7513-a76d-f6cc139fae2d`.
Worktree: `/Users/karol/dev/tools/wt-201-a`; branch: `feat/hs-201-a`;
PR: [#588](https://github.com/karolswdev/HoldSpeak/pull/588), open.

The caller's quiet combined-tree run (`eb295598`, containing `a07d4bb5`)
identified two failures which pass on pristine main. Astra reproduced both
on untouched lane A product code at `5b479963`, before these repairs. The raw
run is in `../evidence-story-03.md`, capture `2026-09-20T03:43:08Z`.

## Classification

| Failure | Class | Why and required repair |
|---|---|---|
| `tests/uat/test_egress_cloud.py::test_cloud_card_names_target_and_remains_unexecuted` | **b — real regression**, with an **a** fixture migration | Retiring live-analysis reporting also hid an assigned manual summary destination. The old deck merely sets retired config fields; it must now select the exact summary assignment. Keep the `api.openai.com` disclosure and unexecuted-proposal assertions. Derive reporting from the same SERVICE route as `planned_route`. |
| `tests/unit/test_mesh_liveness_surfaces.py::test_doctor_runtime_profiles_names_the_mesh_node` | **b — real regression**, with an **a** fixture/copy migration | Doctor lost the answer to which model runs a summary. Pin the fixture to the exact summary assignment and retain both `Pocket 4B` and `walk-edge` in the sentence. Name the job “Meeting summary”; keep live analysis off for Record as a separate fact. |

Neither failure is classified **c**. A fixture update alone cannot discharge
either product regression. These findings fail Article III and Tenets 3/7.

## Original red tail — before product edits

```text
RecipeVerifyError: recipe 'egress-cloud-card' failed to verify:
egress_scope_is: egress scope='local', endpoints=[]
(want 'cloud' target containing 'api.openai.com')

assert "meeting intel: profile 'Pocket 4B' (mesh node 'walk-edge')"
in 'Live analysis is off for Record; no dictation pipeline is enabled.'

2 failed in 5.29s
```

## Scope

The correction is summary-route reporting, not a reconnection of live
analysis. The settled `planned_route` leg/hash contract stays intact. A
display adapter can add labels from the already selected immutable profile
and deployment revisions. No new schema, authority, or execution path is
needed. Tests use isolated HOME and controlled provider discovery. Lane B
continues to own `web/**`; no owner microphone or desk state is used.

## Verified repair

`holdspeak/services/meeting_route_projection.py:134` adds display labels to a
copy of the existing SERVICE route. Its exact immutable profile revision
supplies the profile label, and its deployment revision supplies the node.
The public six-field leg contract and selection hash remain unchanged.

`holdspeak/setup_status.py:125` and `holdspeak/trust_destinations.py:143`
use that route for summary egress. Remote fallback legs are disclosed even
when the first leg is local. An absent assignment cannot inherit cloud
posture from the retired config. Trust calls the job “Meeting summary”,
including when the route is unavailable.

`holdspeak/commands/doctor.py:524` uses the same projection. Its mesh sentence
is `Meeting summary: profile 'Pocket 4B' (mesh node 'walk-edge')`; the next fact
is `Live analysis is off for Record.` The doctor's Trust destinations check
also receives the database, so its destination count agrees with the route.

The UAT fixture now creates a profile through Model Library's public HTTP
producer and selects the exact summary capability assignment. Only provider
discovery and key lookup are stubbed in the isolated product subprocess.
The cloud target, proposed state, no execution, and idempotency assertions
remain. The recipe requires this discovery fixture and refuses ordinary
invocation before provider contact; it is not a live OpenAI readiness test.
The related deck assertion and reporter copy assertions are class **a**
updates. The routing census changed only six line anchors, not its counts or
allowed sites. No `web/**` file changed.

## Root verification

All workers held before the root's final focused run. Every pytest used an
isolated HOME. Root collected **184 tests** (`2026-09-20T04:05:41Z`) and ran
them with `-n auto` (`2026-09-20T04:06:08Z`), including both caller-named tests,
doctor/setup/trust, route/hash/receipt/refusal contracts, assignment, source
guards, and UAT recipe/deck/subprocess-boundary checks. Tail:

```text
........................................................................ [ 39%]
........................................................................ [ 78%]
........................................                                 [100%]
184 passed in 13.30s
```

Root also ran the isolated real hub/Chromium walk (`2026-09-20T04:06:33Z`):

```text
DISCOVERY_CALLS ['https://api.openai.com/v1']
ROUTE_EXECUTIONS 0
PAGE_ERRORS []
.
1 passed in 6.95s
```

The discovery list records the stub call, not network traffic. No provider
execution, owner microphone, or owner database was used. Root inspected
[1440](../assets/lane-a-followup2/summary-trust-1440.png) and
[393](../assets/lane-a-followup2/summary-trust-393.png): the settled Trust window
shows the full cloud host, the manual-summary operation, and no receipt.
An early screenshot caught the opening transition; the test now waits for
the window to settle before checking host bounds and taking the shot.
The 393 chrome badge still clips its visible label; its accessible label
names the host and opening Trust displays the full host. This face limitation
is a lane B handoff, not a claimed fix. Desktop badge contrast is also a face
concern visible in the shot.

The initial two-failure red capture above is the proof before any product
repair. The worker's new-law doctor fence additionally reached both expected
summary assertions before its doctor edit (`2 failed in 0.91s`). Root read
that tail and the worker's collection/pass output; root's own captures are
the delivery proof. No fresh full-suite green is claimed.

## Delivery boundary

This is a follow-up to HS-201-03 and the reporting retirement in HS-201-02.
No story flips, migration, execution policy, or live-analysis reconnection.
PR #588 stays open for Muad'Dib's combined-tree verification and merge.
The earlier inherited Delivery Workbench doctor/check debt remains outside
this scope. The commit and post-commit main integration are recorded in the
PR/lane delivery report; no main checkout or lane B tree was modified.
