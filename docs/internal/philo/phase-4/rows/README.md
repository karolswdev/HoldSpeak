# PHILO-4-02 — visible decision rows

Owner: Astra. Worktree: `../wt-philo-4-02`. Branch: `feat/philo-4-02-rows`.
Codex session: `01a0d21a-e795-7861-9995-cf31f0eed09b`.
Base: `566495b0` (`origin/main`, archived before implementation).
Design authority: Phase 4 owner ratification, story 01 canvas ask 2.

## Rule

Keep the three-row cap. Decisions lead, newest first by the decision
record's `created_at`. Other sections retain their order. The headline
and fold count retain their existing counting rules.

Tuesday: one Generate must leave yesterday's triage untouched and put the
new decision in the first readable Arrival row.

## Fixture ruling: THIS WEEK

The canvas round-six item 7 is correct about the full producer:
`generate` passes `_commitments_due_rows` ids to `_collect_decisions`.
An open commitment due Friday September 25 is counted in THIS WEEK on
both Wednesday September 23 and Thursday September 24. Its separate
`Commitment due` row is suppressed from decisions. A source decision
that is still recorded can independently produce a `Review decision` row.
The canvas's `c1` is therefore an illustrative row, not the full producer's
output for that due date. This lane preserves that existing de-duplication;
it changes decision selection order, not commitment routing.

## Verification environment

The default Homebrew Node 25 binary fails to load `libllhttp.9.3.dylib`.
This lane uses the already installed Node 22.21.0 through a command-scoped
PATH. Both the lane and `.tmp/philo402-main` archive have their own
`uv sync --extra dev` environments. Every pytest uses an isolated HOME.
The LAN engine health response is retained in `engine-health.log`.
No full serial suite is run: the lane brief assigns full coverage to PR CI.

## Records

The baseline is an actual `git archive origin/main` copy in
`.tmp/philo402-main`, with only the new fences copied in. Raw output:

- `red-producer.log`: `2 failed in 0.71s` — missing `BriefItem.created_at`
  and oldest decision first on reload.
- `red-rendered.log`: `Test Files  1 failed (1)` / `Tests  2 failed (2)` —
  first paint and Generate replacement leave changed/broke/waiting in the cap.
- `red-readable.log`: `3 failed, 5 passed in 5.13s` — missing predicate,
  whole-ledger atlas scope, missing shared schema enum.
- `this-week.log`: the real meeting save → artifact projection → acceptance
  → commitment writer → full producer establishes c1's THIS WEEK placement
  on both canvas dates. `verify_this_week.py` is the repeatable probe.

Final producer RED adds the meeting projection path: `red-producer-final.log`
reports `3 failed in 1.29s`. The core two tests are unchanged.

Orchestrator verification:

- `collect-python.log`: 210 tests collected across the scoped Python files.
- `green-python-attempt1.log`: `1 failed, 209 passed in 106.98s (0:01:46)`.
  Only active source anchors failed; service, week, breakage, schema and
  rig calibration tests passed. The repaired references were rechecked below.
- `baseline-atlas-anchors.log`: archived main also fails three producer
  anchors (`is_empty`, `No changes`, `SHELF_STATES`). This is the reproduction,
  not a worker's claim of inherited failure.
- `green-python.log`: `90 passed in 3.35s`, including all new producer and
  real-browser readability fences, atlas integrity and story 01 wording fences.
- `collect-rendered.log`: both new rendered fence names.
- `green-rendered.log`: `Test Files  14 passed (14)` / `Tests  81 passed (81)`.

## Ledger

- **(a) Source-reference drift, paid here.** Three active atlas anchors were
  already wrong on main; this lane shifted seventeen others. All twenty now
  point at their real symbols. Sealed passes and historical observations are
  unchanged. Home: this README and the two atlas logs.
- **(b) Product defect, paid here.** Missing decision recency and decisions-last
  concatenation hid the newest decision. Timestamp persistence and ordering
  have red/green fences. Home: PHILO-4-02.
- **(c) Environment limitation.** Homebrew Node fails on a missing linked
  library. Existing Node 22.21.0 runs the lane; no machine install was changed.
- The real chain's ASR/summary fidelity and the owner's sitting remain the
  Phase 3 ledger's costs; this story verifies visibility and retention.
- **(a) Ordering follow-up, recorded by built counsel.** Arrival repeats
  the producer's sort; producer chronology is the rule. Missing-timestamp
  ties and mixed naive/UTC timestamps across different browser/hub zones
  are not covered by these walks. No claim of cross-zone ordering is made.
- **(b) Existing focus cost.** Disabling Generate drops focus to body
  (PHILO-4-01); these observations confirm it. The scroll correction adds
  no focus change and does not claim to repair the existing loss.

## Actual atlas observations (all retained)

- `20260924T065401Z`, as-written 1440: PASS. The new decision is first,
  `(256,359,928,44)`, all nine hit points owned. Day-one brief has four
  untouched items and an empty shelf. The next-day id differs. No breakage
  was present; this run does not pay story 03's separate rig obligation.
- `20260924T065829Z`, as-written 393: FAIL. The new decision is first,
  `(12,470,369,114)`, inside 393×852, but all three bottom points at y=582
  belong to the sticky capture bar. The after shot confirms covered bottom
  padding; the current title and verbs are readable. The whole-row fence
  is deliberately stronger and protects a further wrapped line.
  `rig-393.log` retains this red; it will not be overwritten by a later run.
- `20260924T071241Z` (393) and `20260924T071337Z` (1440): as-written
  PASS after the measured-clearance/native-scroll correction. First row
  at `(12,401,369,114)` and `(256,359,928,44)`, respectively; all nine
  hit points owned. At 393 the capture bar measures 138 px; both CSS
  clearances are 138 px. The stored brief and shelf are unchanged.
- `20260924T071443Z` (393) and `20260924T071600Z` (1440): separately
  named breakage variant PASS. Both daily briefs contain the same real
  observer failure under distinct brief-scoped ids. `closure-proof-seam.json`
  retains all four runs' identities, timestamps and DB comparisons.

The variant first failed schema validation because its GET setup omitted
the required `body: null` (`green-python-seam.log`: `1 failed, 91 passed in
4.08s`). Added the explicit null; the API runtime already treated omission
as null. The complete 92-test rerun passes (`green-python-final.log`,
`92 passed in 3.90s`).

The read-only closure checker initially compared `/var` and `/private/var`
literally. It now resolves the macOS alias before verifying that the DB is
inside the temporary HOME. Observations were not edited.

## Direct covered-transition fence

The passing atlas starts its second Generate with the old row already clear
after day-one setup. A separate real-browser fence positions a short existing
row just above the actual bar, clicks Generate once, and checks the longer
replacement without any post-click test scroll. Its inputs are labelled
browser API fixtures; the real producer is proved separately. The probe is
the same real `_SNAPSHOT_JS`, not a hand-built observation.

- Two initial fixture attempts failed during setup (route glob and scroll
  position); `red-rendered-clearance.log` and `red-generated-clearance.log`
  are not product reds.
- `red-clearance-final.log`: the first native-scroll implementation FAILS
  at `all_owned` (`1 failed in 5.68s`), row `(12,478,369,135)`, bottom
  points at y=611 owned by the bar.
- `red-clearance-main.log`: the same fence on archived origin/main FAILS
  at `all_owned` (`1 failed in 18.05s`).
- The Chair reserves another 89 px below the bar for the wrapped dock.
  Native scroll padding must cover that existing band plus the measured
  138 px bar. The CSS now uses the same dock tokens as `dock.css`.
- `green-clearance.log`: `1 passed in 10.23s`; scroll padding 227 px,
  end clearance 138 px, all nine row hit points owned. Collection is in
  `collect-clearance.log`. No fixed phone height or hand-written scroll
  delta is used in product code.

Final actual-atlas runs, all PASS on `index-Y37FyLq1.js`:
as-written 1440 `20260924T072614Z`, 393 `20260924T072514Z`;
breakage variant 1440 `20260924T072814Z`, 393 `20260924T072722Z`.
All eight final before/after shots were inspected. Exact full run ids,
positions and scope are in `lane-report.md`; `closure-proof.json` retains
the independently checked ids, dates, all-owned samples and DB comparisons.

Closing counsel: `checks/rows-built-muaddib.md` in the phase records
RATIFY-WITH-CONDITIONS; all conditions are paid. The checker's C2 reply
is RATIFY: the schema inventory is pinned September 19 archaeology, so
its regeneration/check changes no historical schema. The live boundary
census is regenerated (`final-census.log`). Nothing here claims an owner
sitting or permission to merge.
