# Production trial protocol — worker handoff

This is controlled-provider protocol evidence, not physical model or owner
observation. The probe lane authored the backend and API wire. Root reviews
that backend separately. The cross-lane source review here covers Settings
and trial UI only.

## Bounded source review

Settings has one navigation selection in `SettingsCore.tsx:1246`. Scope
entry, frame wings, hub doors and Back all write that selection. The
`surface-settings` window instance resets it on a new external entry,
including an entry with the same scope; compositor geometry is stored
separately, so a drag does not change this instance. Guide stays inside
SettingsFace and keeps the pending settings writer mounted. No finding in
this bounded source read.

The trial UI maps five jobs to the backend's fixed sample capabilities.
`useRunsOn.ts:502` builds the full displayed target chain, including the
summary capability override, and rejects missing destinations. The press
compares profile revision, engine, destination and chain length against the
rendered bindings before requesting inference. It sends their profile IDs
to the backend guard. The library Button supplies loading and blocks a
second press. Result text comes from boolean success and terminal fields;
empty success has the neutral `No text returned` label. The default row
has no sample capability and no Try. No finding in this bounded source
read. Production observations below decide whether that behavior ran.

## Recorded wire for frontend checks

`.tmp/settings-trials/probe-wire.json` contains an answer and blank answer
recorded from the real MeetingWebServer ASGI HTTP route through FastAPI
TestClient, with real adopted route/controller/runner and only the provider
leaf controlled. Both return `READY`, `ok: true`, `outcome: succeeded`;
the blank answer returns `emptyOutput: true`. Its isolated database was
under the helper's temporary HOME. The JSON labels its transport and
engine mode. The recording script is
`.tmp/settings-trials/record_probe.py`; the successful log is
`.tmp/settings-trials/probe-wire-recording-2.log`.

The first recording setup lacked the ASGI owner's auth header and was
refused as unauthenticated. The second read the app's owner token and
succeeded. No auth bypass or product change was used.

## Production case

Script: `.tmp/settings-trials/probe_production.py`. Each invocation runs
one width and one real `scripts.graph_walk.Hub` in its own retained HOME.
It uses the existing Model Library endpoint and assignment HTTP producers.
The replay provider is loopback only. The fixed public sample carrier and
three-second delay are explicit additions to a copy of the retained
`tests/fixtures/philo5_summary_reply.json`; observations label this
controlled leaf and retain its digest.

The case uses normal motion. It checks one Try press, exactly one real
probe POST, the Button's `aria-busy`, disabled state and visible Signal
spinner with a nonzero animation duration. At 393 it checks ownership of
nine points spanning at least 44 px. The final UI input/output must equal
the real HTTP result, and the returned execution ID must name a DB row
with state `terminal` and outcome `succeeded`. It also compares domain and
assignment rows before and after all trials. The browser never replays a
probe response.

The first 1440 setup stopped before opening a browser: the isolated hub
created its default between the global roster read and global assignment
write, which returned an honest CAS conflict. Evidence:
`.tmp/settings-trials/production-1440-attempt1/observation.json`. The rig's
one bounded correction uses each job's own group assignment producer and
its exact roster revision. No production validator was changed.

## Post-run handoff — second setup, not an original observation

The second setup completed all five real group assignments; their actual
responses remain in
`.tmp/settings-trials/production-1440-attempt2/producer-setup.json`.
The existing `tests/e2e/runs_on.py:42` helper then raised a Playwright
strict-mode error: its `switchboard` locator matched both the assignments
list and the Download board. This is a rig locator defect. It does not
establish a product timeout. The initial worker report inferred a timeout
from the short tail; reading the full raw stack corrected that report.

Raw log:
`.tmp/settings-trials/probe-production-1440-attempt2.log`. No Try gesture
was reached. No successful TCP probe, spinner observation, hit ownership,
visible trial output, receipt joined to that UI action, or 393 capture is
claimed. The attempted bundle was `f2da720cc4042fec`.

The scratch rig then called browser.close after Playwright's context had
already stopped; that cleanup error interrupted its final observation
write. No final original observation or failure screenshot exists for
attempt two. None was reconstructed or edited. The retained raw log and
producer responses are the evidence for this labelled handoff.

The worker stopped at the two-setup-attempt limit. A process read matched
no surviving `wt-settings-trials-20261014/scripts/graph_walk.py serve`
process, so no process kill was needed or performed. Root owns the next
capture with a locator scoped to `runson-assignments` and the Settings
Models entry. There is no third worker setup or production change.

## Verified and unknown

Verified here: source cross-review; 39 focused Python checks (logs in
probe.md); answer and empty-success ASGI wire recordings with real kernel
receipts and a controlled provider leaf; production build; real endpoint
and five group assignment HTTP producers in an isolated graph Hub.

Unknown here: the production UI-to-probe-to-receipt chain, spinner
animation, 393 hit ownership and both final viewport shots. Root's new
run must supply that evidence. Physical model correctness and the owner's
live verdict remain outside this controlled protocol proof.

## Root continuation — actual trial observations

Root scoped the assignments locator and entered Settings through /models.
The first two root captures exposed a real loopback permission mismatch;
root.md records the original observations and surgical classifier correction.
They do not prove successful waiting or inference.

After that fix, `.tmp/settings-trials/protocol-locality-1440/observation.json`
records all five actual one-press UI→HTTP→kernel→visible-output trials, each
with Signal animation `signal-spin` / `0.7s`, aria-busy, disabled action,
exactly one probe POST and a joined terminal/succeeded DB receipt. Root read
those five records and inspected Answers waiting and meeting completion shots.
The recorded provider leaf uses a 10-second controlled delay; output is a
fixed public carrier, not physical model correctness.

That invocation ended FAIL on the whole-case non-write comparison: the rig
captured its baseline before first browser arrival seeded the two starter Notes
and six starter recipes. Those seeded rows are visible in its isolated DB;
no successful non-write comparison is claimed for that run. Root moved the
baseline after normal arrival and actual Models load, before the first Try,
and now saves both original before/after snapshots. Replacement captures are
separate output directories; no earlier observation was rewritten.

Final settled-baseline desktop and phone observations are recorded below once
read; the original worker handoff above remains an honest account of that run.

### Final settled-baseline observations — PASS

Root read both original observations, their request/response and DB joins,
before/after snapshots, and actual desktop/phone waiting/completion shots:

- `.tmp/settings-trials/protocol-locality-1440-settled/` — board layout,
  five jobs, PASS. Root inspected Answers waiting and meeting completion.
- `.tmp/settings-trials/protocol-locality-393/` — list layout, five jobs,
  PASS. Root inspected Answers waiting and completion.

Both used production frontend build e449d97876a9c9f1 and normal motion.
Every job made exactly one real POST, showed the library signal-spin animation
(0.7s), aria-busy and a disabled Try button while pending, then showed the
HTTP sample input/output and a named Completed result. Every returned execution
ID joins to a terminal/succeeded row in that invocation's isolated DB.
All five phone actions own nine points across a 44-pixel-high target.
Both before/after snapshots compare equal for the named domain and assignment
tables; Default engine has no trial; neither browser emitted a page error.
Each output directory retains ten actual screenshots, observation.json,
producer-setup.json, domain-before.json, domain-after.json and hub.log.

The replay leaf intentionally returns the same public carrier for several
jobs. It proves dispatch/result plumbing and schema handling, not a useful
physical model answer to 2+2 or clean-up. The observations label engine_mode
replayed and its SHA256. No owner desk data, mic, LAN or cloud was used.
