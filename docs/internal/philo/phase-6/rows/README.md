# PHILO-6-04 — one cause, one row

The route now resolves the durable owner before invoking one observed service.
An unknown id takes the desk registry once. Lifecycle-only records still return
lineage; when both producers own an id, the desk record retains precedence.
No observer or lifecycle service changed. Legacy-only reads also stop producing a false desk NotFound: their one observed row is a success.

## Proof per acceptance box

1. Missing HTTP id: `test_missing_id_has_one_real_observer_failure_row`;
   actual-atlas `observer-rows.json` under both `green-http-*` directories.
2. Legacy lineage: `test_lifecycle_only_id_uses_one_observed_lineage_read`,
   minted through the production artifact projection. Desk precedence:
   `test_desk_owner_wins_when_real_producers_share_an_id`.
3. No global suppression: `test_each_real_service_failure_keeps_its_observer_receipt`;
   `observer-mutation.txt` fails when both actual observers are omitted.
4. Archive red: `pre-fix-missing-id.txt`, `assert 2 == 1`.
5. Actual atlas parity: `verify_parity.py`; HTTP rows 67/68 vs op row 6
   on archive, then HTTP row 67 vs op row 6 after repair, at 1440 and 393.

```text
33 tests collected
33 passed in 11.73s
1440: missing-decision parity FAIL 2:1 -> PASS 1:1
393: missing-decision parity FAIL 2:1 -> PASS 1:1
```

The canonical command output is in the paired Phase 6 evidence-story-04.md.
`collect.txt` and `focused-tests.txt` retain worker proof; Astra reran the same
33 tests through DW. No full suite: the lane brief requires scoped tests only.
Astra inspected both green HTTP after.png shots. These are transport walks,
not a visible refusal claim; the phase closing morning rehearsal remains owed.

## Provenance and exclusions

The eight valid sidecars were produced on rig 1.2.0. Story 05 advances the
shipped rig to 1.3.0 for its continuous paint probe; these protocol cases
do not use that probe. The green HTTP 1440 log is verified by the DW parity
capture; the other three green runs were directly captured by DW.

`baseline.json` records the origin/main archive and route hash. Each raw rig
observation remains unchanged. `walk_one_row.py` retains actual observer rows
read-only before the rig removes its temporary HOME; no missing read is retried.

- `red-http-1440` is an excluded trial: a reused editable install imported the
  built lane. Explicit PYTHONPATH corrected this; the valid baseline is
  `red-http-1440-import-corrected`. It is not a pre-fix pass claim.
- `red-http-393` is an excluded applicability result: the prior atlas only
  named 1440. The user required both widths; the HTTP case now names 393 too.
  Valid baseline: `red-http-393-atlas-width`.
- Default Homebrew Node cannot load libllhttp.9.3; the existing Node 22.21.0
  toolchain was used, without changing the machine installation.
- Archive raw revision/dirty describe its containing worktree. Use baseline.json,
  explicit import root and route hash for source identity, not that inherited Git result.

Tuesday: a missing decision contributes one breakage cause, while legacy
records and actual service failures keep their existing behavior.
