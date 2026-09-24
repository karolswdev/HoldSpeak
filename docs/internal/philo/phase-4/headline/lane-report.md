# PHILO-4-04 — Astra build lane report

LANE: PHILO-4-04, The triaged headline. Owner Astra; checker Muad'Dib.
Worktree `/Users/karol/dev/tools/wt-philo-4-04`, branch
`feat/philo-4-04-headline`, [PR #627](https://github.com/karolswdev/HoldSpeak/pull/627).
Main `6cfc64e0` was merged first through the gate as `e4cf7d08`.
Workers: `headline_fences`, `headline_atlas`, `headline_storage`, all
`gpt-5.6-luna` at `xhigh` by actual rollout metadata in `worker-runtime.json`.
The original canvas-only report is parked at `canvas-lane-report.md`.

OUTCOME: **built**. The saved headline/date remain in place; the quiet
Arrival adds `ALL n HANDLED` below the date only when every Arrival row has
an acknowledged/deferred shelf state and n is positive. THIS WEEK is
excluded, including when the headline total is larger. `No changes`, a
partial shelf and a hidden unshelved row do not acquire a handled line.
Generating, failure and same-day receipt retain the line. No new control,
API/schema change, stored-count rewrite or live-region announcement.
Story 04 is done with paired captured evidence. PR #627 stays open for the
invoking brain's counsel on built; Astra does not merge. The owner's
sitting was waived, and no owner observation is claimed.

PROOF:

| Acceptance box | Result and evidence |
| --- | --- |
| Snapshot versus current triage, stored counts retained | PASS. `ChairHome.tsx:886` derives the valid shelf state; `:1395` keeps headline/date/handled order. `triagedHeadline.philo404.test.tsx` checks six rows and a seven-row `_compose` variant with only six Arrival rows. `test_philo4_04_headline_storage.py` reads all six item fields, headline and dates unchanged after real shelf writes, same-day generation and a fresh service read. |
| Canvas before build, owner ratification | PASS. Main ratification `89208bae`; story notes and `assets/story-04-canvas/README.md`. Board 7c was explicitly selected. Retained 8a/8b/9 PNGs use the earlier alternative placement; board 7c controls all built states. |
| Intended-state red, no zero header, unchanged history | PASS. `rendered-red-origin-main-20260924T0818Z.md` records the archive/command. `baseline-integrity.json` verifies the archived product is byte-identical to `origin/main` and the final fence/fixture match both trees. Five positive cases fail on the missing line; three negative controls already pass. Final fences exclude `BRIEF · 0`, retain the three generation states, and preserve the empty result. Actual atlas and retained DB/API snapshots independently verify full production generation and shelf writes. |

Red, verbatim (`rendered-red-origin-main-20260924T0818Z.txt`):

```text
 Test Files  1 failed (1)
      Tests  5 failed | 3 passed (8)
```

The five failures are six-row handled, THIS WEEK exclusion, generating,
generation failure and same-day success. They fail on
`Unable to find an element by: [data-testid="arrival-brief-handled"]`.
The final new-fence green (`rendered-green-20260924T0824Z.txt`):

```text
 Test Files  1 passed (1)
      Tests  8 passed (8)
```

Final orchestrator scoped verification, captured at `2026-09-24T14:20:09Z`
through `dw evidence capture` using `verify_lane.py`:

```text
90 passed, 2 warnings in 3.65s
 Test Files  6 passed (6)
      Tests  36 passed (36)
API reference checked
Boundary candidate census checked
```

`final-collect-python.log` contains all 90 collected test names;
`final-collect-rendered.log` contains all 36 rendered names. Run tails are
`final-green-python.log` and `final-green-rendered.log`. The graph check
passes with its 14 recorded pre-existing subtype-conflict notes
(`final-philo_graph_reference.log`). `git diff --check` passes; evidence
churn check reports no ` M` paths under `pm/roadmap/holdspeak/`.
No full suite was run: the lane brief explicitly requires scoped tests.

Actual atlas `case.philo404.arrival_triaged_headline.all_handled`, final
production bundle `index-yOpsX1bz.js`:

| Width | Run id | Verdict | Handled geometry |
| --- | --- | --- | --- |
| 1440 | `20260924T142054Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440` | PASS, settled | x256 y364 w928 h18 |
| 393 | `20260924T142158Z-case.philo404.arrival_triaged_headline.all_handled-astra-393` | PASS, settled | x12 y371 w369 h18 |

Each run uses one real isolated hub, two production-created decisions,
Generate on the face, then row-scoped Ack and Defer. `readable_text`
passes; all nine hit points belong to the line. The stored headline is
`2 decisions waiting.` before and after; the after face shows it above
`ALL 2 HANDLED` and the existing generation receipt. Zero browser errors.
The before snapshot has no handled element; the final shelf response is
POST 200 for the actual deferred item. `observation-proof.json` checks
brief/item fields unchanged, both shelf states stored, and DB paths inside
the isolated HOMEs. It was captured at `2026-09-24T14:22:40Z`.

Astra inspected all final before/after PNGs beside board 7c. Shots and
unaltered observations live under
`pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/<run-id>/`.
Earlier passing runs `20260924T141351Z`/`20260924T141445Z` are retained;
the final pair was rebuilt after the guard-only source correction.
All commands ride in the same commit's `evidence-story-04.md`.

LEDGER:

- **a — source verification corrections, paid here:** three live atlas
  anchors moved with the insertion (`atlas-run.log`: 1 failed, 72 passed;
  final atlas suite green). The A8 scanner initially could not see the
  enclosing JSX guard (`verification-attempt1-green-python.log`: 1 failed,
  89 passed). Guard and label now share a source line; the scanner and
  ceiling are unchanged. API test references and boundary line anchors
  were regenerated after the reference check named drift
  (`verification-attempt2-api-reference.log`). All final checks pass.
- **b — no unresolved product regression found.** A drafted direct-SQL
  commitment fixture was rejected. The final six-row persistence proof
  uses explicit collector adapters plus real compose/store/shelf/readback;
  the two-decision atlas is full-generation proof. Neither claims the
  current collectors put c1 in Arrival. The seventh-row variant uses the
  real `_compose` string `1 commitment due`, correcting the draft's
  hand-copied `1 commitment due this week` headline.
- **c — verification/environment issues, no flake claim:** the first
  archive invocation lacked jsdom config (`rendered-red-origin-main-20260924T0809Z.txt`);
  its 16 errors are not product-red evidence. Final archive command is
  correct. The first readback summarizer treated an absent DOM text as a
  string; it now explicitly asserts absence. Two existing invalid-escape
  warnings come from the scratch guard reading the unrelated HS-202-05
  file. Node 22.21.0 was used. Intermediate duplicate attempts are parked
  under `.tmp/philo404-build-attempts/`; required final red/green remain here.

AMENDMENTS: none. Owner ratification and sitting waiver stand. No source
scanner ceiling was raised, no acceptance criterion was weakened, and no
phase closure or merge is claimed. The capability-verifier skill's actual
atlas procedure was followed; this story adds no catalogue capability or
release/owner-observation claim.

UNKNOWN: Muad'Dib's counsel on built and PR CI after push are pending at
handoff. Full suites and an owner sitting were not run under this brief.
No build or verification blocker remains. The original six-row fixture is
composition/persistence proof with named collector adapters; the actual
atlas's full producer has two decisions. It does not exercise commitment
collection or a model.

TUESDAY: yes — after handling the last row, the owner can see that Arrival
triage is complete while the saved headline still records its old counts.
