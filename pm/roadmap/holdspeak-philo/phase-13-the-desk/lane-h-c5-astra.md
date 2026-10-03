# H-C5 — latest published update

LANE: H-C5, backend handoff for PHILO-13-15 / C5 PR #749. Astra owns
`holdspeak/db/updates.py`, `holdspeak/web/routes/project_updates.py`, the route
fences and this evidence. Worktree: `../wt-philo-13-h-c5-astra`; branch:
`fix/philo-13-h-c5-astra`. Date: 2026-10-03.

OUTCOME: built and verified for the scoped merge. No C5 story status flips.
The existing Room list puts the latest publication first. C5 can consume its
exact id without sorting. Tuesday: the architect gets the current update,
including when an older publication has a greater draft revision (Tenets 1,
3 and 7).

## Contract for C5

`GET /api/projects/{project_id}/updates` returns:

```json
{"updates": [], "latest_published_update_id": null}
```

With publications present, `latest_published_update_id` is the string id of
the first published row. Published rows precede unpublished rows and order
by **`published_at DESC, rowid DESC`**. `rowid` means SQLite insertion order;
it is not added to the response or schema. `draft_revision` and `created_at`
cannot override the publication order. Unpublished rows keep
`draft_revision DESC, created_at DESC`. The existing limit is applied after
ordering.

The same publication order applies to `?lifecycle=published`. A lifecycle
filter applies before selection: when no returned row is published
(including `?lifecycle=draft`), the field is JSON `null`. For C5's unfiltered
read, use `body.latest_published_update_id` directly. The interim sorter in
`web/src/desk/windowSend.tsx` and its test remain Muad'Dib's follow-up in
#749; this lane changes no face source.

## PROOF

All records are under [assets/h-c5](assets/h-c5). Final source base was
`2d1d791a0b12b1f42fecdec0903a74a86a1e7d0b` with this lane's uncommitted diff;
the observations correctly record `dirty: true`. The frontend was rebuilt
from that base (`build.log`).

- `collect-final.log`: 213 collected nodes. `focused-final.log`: **212
  passed, 1 skipped in 22.76s**. The skip is the real-owner-DB check, because
  every run used an isolated HOME. Command:
  `HOME=$(mktemp -d) uv run pytest -q tests/integration/test_update_routes.py tests/unit/test_project_updates_schema.py tests/unit/test_update_drafter.py tests/unit/test_philo_graph_atlas.py`.
- `collect-ordering-v2.txt` names the four route fences. The worker's
  original red-before-fix run is `red-ordering.txt`. All four final fences
  were independently run unchanged (copied as `test_h_c5_exact.py`) against
  original product source `fc12a18d56868fc95a3310eb9cf99c0421a25730`:
  **4 failed in 1.54s**, `red-exact.log`. `red-source.txt` proves the actual
  runtime imports came from `/private/tmp/holdspeak-h-c5-red`, not the fixed
  worktree. The shared installed dependencies were used with `uv run
  --no-sync`, explicit `UV_PROJECT_ENVIRONMENT`, baseline `PYTHONPATH` and
  isolated HOME. The worker's additional baseline run is also retained as
  `red-original-fc12.txt`.
- The fences mint every update through draft/regenerate/publish routes.
  Only the repository clock is controlled. Assertions read real SQLite
  rowids. They cover equal-revision same-second ties, a revision-3 versus
  revision-1 same-second tie, timestamp priority over greater rowid and
  revision, both list filters, no-publication null and unpublished order.
- The committed actual case is
  `docs/internal/philo/graph/atlas-h-c5.json`,
  `case.h_c5.update.latest_first`. Each width ran in its own invocation of
  `scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-h-c5.json --case case.h_c5.update.latest_first --brain astra --viewport <width> --engine none --no-build`.
  HOME was isolated and the Playwright cache path explicit. At 393 the
  clicks use the rig's touch adapter. Both predicates passed, both console
  error arrays are empty, and Astra read all four before/after PNGs.
- [1440 after](assets/h-c5/final-1440/20261003T165342Z-case.h_c5.update.latest_first-astra-1440/after.png)
  and [393 after](assets/h-c5/final-393/20261003T165435Z-case.h_c5.update.latest_first-astra-393/after.png):
  the first visible row has the exact later producer-returned id, is
  published, and has revision 1; the older publication has revision 2.
  The adjacent observations retain the GET response and producer results.
  `observed-contract.json` records independently asserted response order
  and field agreement. Both live pairs actually tied: `16:53:47+00:00`
  at 1440 and `16:54:42+00:00` at 393, on 2026-10-03.
- `docs-checks.log`: OpenAPI, API reference, architecture validation,
  generated capabilities/coverage and graph freshness all exit 0. OpenAPI
  regeneration made no diff. API/source metadata and their generated
  projections changed together. `census.log` reports **0 changed, 0 stale**
  against the sealed graph baseline.

## LEDGER

- Paid defect (b): the read ranked draft revision ahead of publication and
  left same-second ties without insertion order. Fixed here and fenced
  against real producers.
- Harness corrections, paid: the first walk used `--headless`, which means
  no browser in this rig; the next assigned the touch adapter to `wait_for`,
  which it does not support. The third found the correct first row but
  expected a space between two labels whose rendered text has a newline.
  Final predicates independently require both labels on the exact latest
  id in the first row. These attempts are retained under `attempts/`; none
  is counted as passing. No product change was needed for them.
- Existing graph census backlog: 46 new, 5 miscited and 14 subtype-conflict
  notes against its sealed historical baseline (`census.log`); no stale or
  changed entry point in this lane. No sealed evidence was rewritten.
- Environment: the Homebrew Node binary could not load `libllhttp.9.3`.
  Build and glass used the existing Node 22.21.0 installation through PATH.
  No owner installation or machine setting was changed.

## AMENDMENTS

The design remains Muad'Dib's 2026-09-30 rule in Phase 12 story 03. The
dispatch explicitly says: “PR to main, self-merge on your scoped proof
(owner: CI does not gate), merge record on the PR”. This is the authority
for this backend handoff's scoped verification and self-merge. No full-suite
result and no new Muad'Dib counsel-on-built are claimed. C5's own close and
face adoption remain with its owner. No chartered criterion changed.

## UNKNOWN

No owner sitting, full suite or C5 Send-to transition was run in this lane.
The graph rig cleans its temporary HOME at exit, so its retained HTTP
observations establish live persisted publication results; raw rowid
comparisons are proven by the route tests, not a post-exit DB inspection.
