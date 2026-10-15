# Root review and release verification

## Source review

VERDICT: RATIFY — bounded worker implementation and final release checks verified by root.

FINDINGS: No remaining source blocker in the bounded repair. Root read the
Settings navigation/writer diff, direct trial controller and rendering, probe
adapter/terminal/expected-profile guard, route body validation, and new focused
regressions. This is root review of worker-built code, not Muad'Dib's check or
a claimed independent review of the whole change. Cross-lane review covers
Settings/front end; its author built the probe backend.

CONDITIONS: Met for this bounded release. Final TypeScript, full combined quick
check and actual production UI→probe→receipt observations were read. No owner
model quality claim.

MISSED: The first root typecheck caught four unsupported getByRole exact
options in new Settings tests. Root removed those test-only options; role
queries already match string names exactly, assertions and product unchanged.
The final focused query test and TypeScript run cover this cleanup.

TUESDAY: Settings selects the page it shows; a trial starts at its row, waits
there, and leaves an observable sample result.

UNKNOWN: Actual owner microphone/LAN/cloud inference, paid model quality,
account sign-in and owner acceptance. Same-profile backend retarget before
admission is outside the optional ID-only guard; no planner/consent framework
was added. One representative sample is not a test of every task in a group.

## Root actual Settings graph walk

`case.settings.wing.accounts` in `atlas-settings-trials.json` uses the real
/models alias, then the native Accounts tab/menu. Root read both observations
and after shots. Both passed/settled, no console errors, run-owned HOME/DB,
engine=none. The selected Accounts wing matches its actual account content;
Engines is absent. No account write or scan occurs.

- 1440: `.tmp/graph-walk/settings-trials/accounts-1440/20261015T000942Z-case.settings.wing.accounts-astra-1440/`.
- 393: `.tmp/graph-walk/settings-trials/accounts-393/20261015T001057Z-case.settings.wing.accounts-astra-393/`.

The atlas initially failed its ruled-both-viewports and ID-shape validators.
Root corrected the definition; no validator was weakened. 577 graph/metadata
checks then passed (`.tmp/settings-trials/graph-docs-final.log`).

## Generators

OpenAPI regenerated: 628 paths, same route topology. Capability documentation
generated 10 outputs. Graph join and check passed with 14 existing sealed-pass
subtype notes; the notes are not new resolutions. Census is recorded separately.
The metadata adds executed controlled-leaf probe assertions without promoting
release, platform, owner observation or physical inference status.

Final release checks and live trial evidence are recorded below.

## Release run corrections and historical census

The first combined quick run was RED: 3,595 web tests passed and two app-level
assertions still required the previous job names. Root changed only those copy
expectations (Default engine, Answers and notes, Custom tasks), retaining the
same refusal, Undo and no-write assertions. The focused app file then passed
13/13; the Settings query cleanup passed 29/29. TypeScript passed. Logs:
`.tmp/settings-trials/{quick-release/,runs-on-app-focused.log,settings-query-focused.log,frozen-types-final.log}`.
The same first run passed 671 affected Python checks, 107 desk sweeps with two
existing expected failures, and 15 canon guards. It was not called GREEN.

Census against the historical generated graph (source f575a582) reports
115 new, five removed, zero changed/stale/unread, five miscited and 14 existing
subtype notes. These are recorded historical graph gaps, not assertions that
this Settings patch resolved them. Full output: `.tmp/settings-trials/graph-census.log`.

Root inspected the actual 393 Guide failure and 1440 Retry shots. The failure
shows the existing Try again action and one footer; the successful retry returns
to Guide. The persisted-setting assertions are in navigation.md.

## Live capture finding — loopback locality

The first root desktop capture reached one real POST but no kernel execution.
The next atomic waiting read at both widths exposed the actual visible result:
Not tried / Destination not confirmed. The frozen endpoint revision stores
loopback as private_network; the desk already refines this through
`inference_locality.deployment_lamp`, but the trial preview used the raw word.
Increasing the replay delay did not solve this; the provider was never reached.
This was a product seam finding, not a successful waiting capture.

Root made a surgical fix in the already diagnosed route_probe seam: task_probe
supplies its DB to the pure preview, which uses the existing deployment_lamp
classifier for offMachine/paid. Frozen route leg facts and admission remain
unchanged. Five regression cases cover IPv4 loopback, localhost, IPv6 loopback,
LAN and cloud, with no dispatch. Their first run was RED (preview lacked the DB
argument); all 44 probe/API checks then passed in 5.19 s. Logs:
`.tmp/settings-trials/{endpoint-locality-red,probe-locality-green}.log`.
The prior combined quick run was GREEN before this fix; the complete release
check is rerunning against the corrected final source. The earlier original
observations remain unchanged; replacement captures use protocol-locality-*.

## Final release check — GREEN

Final source, including the loopback fix: production build passed;
3,597 affected web tests in 396 files passed; 676 affected Python checks in
eight files passed (8.22 s); 107 desk sweeps passed with two existing expected
failures (64.66 s); 15 canon guards passed (1.62 s). The complete command ended
QUICK CHECK GREEN. Logs: `.tmp/settings-trials/quick-locality/` and
`.tmp/settings-trials/quick-locality-console.log`. No waiver or skipped sweep.
TypeScript was green after the final frontend freeze; only backend locality,
its five Python regressions and documentation changed afterward.

Root read PASS observations for all five jobs at both widths, exact HTTP/UI
input/output equality, actual terminal/succeeded DB rows, nonzero animation,
phone hit ownership and equal before/after domain/assignment snapshots.
Paths and limits: protocol.md. Root inspected actual waiting and completion
shots at both widths. Graph navigation also passed both widths. The retained
canvas is direction material and was manually previewed before build; the
quick script correctly reports it outside its web/src coverage.

This is a ratification of the bounded repair on this tree, not Muad'Dib's
check, an independent whole-change review, owner acceptance, physical model
quality, or the main watcher's full/postmerge tape. Those remain unknown.
