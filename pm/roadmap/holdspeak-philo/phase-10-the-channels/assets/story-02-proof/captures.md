# Proof captures — PHILO-10-02 The GitHub and Atlassian channels (and the nudge)

An asset, not `evidence-story-02.md`: the story stays in-progress until the real-account leg (story 06), and the gate rejects evidence for a story that does not flip done (`pm/roadmap/PMO-CONTRACT.md` section 6, `orphan-evidence`). Each run below was captured with `.githooks/dw evidence capture`; the done-flip commit carries them into `evidence-story-02.md`.

**Status:** in-progress. Every criterion but the real-account leg holds (the leg is story 06's, on the owner's own session, per target he authorizes). Built by the Fedaykin lane (Opus 5.5) on `feat/philo-10-02` from main `3be017db`.

## What was built

- **GATE 1** — `holdspeak/services/channel_contract.py` `redact`: the error is cut to 240 characters BEFORE the excerpt scan (at most 231 windows, each a C-speed `in`, deduplicated); the scan reads at most `REDACT_SCAN_LIMIT` = 1 MiB of payload (above every CLI limit); a larger payload withholds the text whole (`[redacted]`, fail closed). `Outcome.reason` is a fixed code chosen from the RAW native answer by each channel's pinned list and never passes through `redact`; the only free text is `Outcome.detail`, always redacted, kept as `proof_json.error` of a failed or unknown row.
- **GATE 2** — `holdspeak/web/routes/channels.py`: every route awaits `run_in_threadpool(call_sync, …)`; `holdspeak/web/routes/steward.py`: `nudge.send` in the threadpool; `holdspeak/web/routes/mcp_http.py`: `tools/call` of `channel.send` and `nudge.send` in the threadpool (the other tools keep today's path: scoped, Tenet 1).
- **The CLI seam** (design section 6) — `build_gated_connector(…, principal, parent_operation_id, broker)` → `_route` → `PermissionGate.execute_subprocess(…)` → `run_subprocess_operation(…, parent_operation_id)`; `local-owner` stays the default only for callers outside an admitted operation (`connector_runtime.py`); `kernel/causation.py` then binds each child to the send (same principal).
- **The channels** — `holdspeak/services/channel_cli.py` (registered in `CHANNELS`): GitHub (`gh issue|pr comment <n> --repo … --body-file <0600 file>`, proof = the comment URL for the frozen target; `{host, login}` frozen at save from `gh api user --hostname`, re-read before the boundary: `github_identity_changed`, `github_not_logged_in`, `github_identity_unverified`), Jira (`acli jira workitem comment create --key <ONE key> --body-file … --json`; `jira_key_not_single`; `_guard` refuses `--jql`, `--filter`, `--edit-last` and any argv off the manifest), Confluence (`acli confluence blog create --space-id <id> --from-json <0600 file> --json`; title and storage-format body in the file). Atlassian: switch → status → create as three `subprocess.exec` children under `_ACLI_LOCK`; create only when status names the frozen site and email. Size limits by name: GitHub 65,536 and Jira 32,767 characters, Confluence 1,000,000 bytes. Outcomes: SENT = exit 0 + proof; FAILED = the pinned list only (gh exit 4, not found, permission; acli unauthorized, not found, can't be edited; the switch or status step failed; the kernel refused the child; the binary missing); UNKNOWN = everything else (an unpinned exit, exit 0 without a proof, a timeout, an interrupted child). A take-over of a `dispatching` CLI row answers UNKNOWN `interrupted`, never dispatches.
- **Destinations** — `channel.save_destination` takes `github` (host, repo, kind, number), `jira` (site, email, key), `confluence` (site, email, space_id); each view carries `connection: {id, state, last_checked_at}` from `watch_provider_connections` (Phase 9 B1: `never_checked`, `connected`, …), shown and never the identity.
- **The nudge (F4, F5)** — `ProjectStewardService.send_nudge` → `_send_nudge_on_channel`: the GitHub channel's plan, file, child and outcome rules (`GitHubChannel.comment`); a durable boundary (`proposed` → `sending`, committed before gh); the settle (step, ledger row, kernel receipt) in ONE transaction; FAILED (known) → back to `proposed`; UNKNOWN → step `unknown`, kernel `indeterminate`, never offered again; the reaper and the startup recovery end a `sending` nudge `unknown` (`kernel/channel_send._nudge_ended_effect`). The nudge card shows `⚠ RESULT UNKNOWN · CHECK #<n>` with no Send verb (a small change on a ratified species forced by correctness, as story 01's UNKNOWN row; for the owner's canvas review in story 04).
- **The steward prepares (Q5)** — effect kind `prepare_send`: for each destination in the run's FROZEN `bounds.send_destination_ids`, the project's latest published update is prepared as a `channel.prepare` CHILD of the run under the run's actor (owner, scheduler or agent), once per update and destination. `kernel/project_codec.py`: a steward child `channel.send` / `channel.discard` is refused `owner_principal_required` with a receipt.

## Criteria → fences (all in `tests/unit/test_philo10_cli_channels.py` unless named)

| Criterion | Fence | Red first |
|---|---|---|
| GATE 1 cost | `test_gate1_the_redactors_worst_case_is_bounded` (and the bench below: worst 0.37 s) | G1a: 11.53 s on story 01's scan |
| GATE 1 named code | `test_gate1_a_document_with_the_clis_error_phrase_keeps_the_named_code` | G1b: `github_[redacted]_denied` |
| GATE 2 | `test_gate2_the_hub_answers_a_read_during_a_slow_send[http, mcp]` (a real socket hub process, a 1.5 s send; read < 0.5 s) | G2a/G2b: the read waited 1.38 s |
| one `channel.send`, children parented (F5) | `test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[×3]`, `test_f5_…` | main (F5: parent `''`); M1, M2 |
| nudge timeout UNKNOWN, not offered (F4) | `test_f4_…`, `test_a_nudge_whose_settle_fails_after_the_comment_never_posts_twice_and_the_reaper_says_unknown` | main (F4: `send_failed`, back to proposed); M3, M14, M15 |
| argv prefix, no body, file = digest, forbidden plans | `test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[×3]`, `test_a_plan_with_a_forbidden_flag_or_a_second_key_cannot_be_built` | M8, M9, M10, M18 |
| acli lock; a second send waits | `test_an_atlassian_send_runs_inside_the_acli_lock_and_a_second_waits`, `test_a_status_that_names_another_account_never_creates` | M7 |
| GitHub identity A → B | `test_a_github_destination_saved_as_a_is_refused_when_gh_is_b` (the connection row rewritten to B does not change it) | M6 |
| Confluence title | `test_the_confluence_title_is_in_the_frozen_digest_and_never_in_argv_or_a_receipt` | M11 |
| outcome clauses | `test_only_a_pinned_error_is_failed_everything_else_unknown[5 cases × 3 channels]` | M4, M5 |
| no body in argv / a subprocess receipt; owner principal, parent, broker | the argv fence (sentinel over argv, `kernel_receipts`, `kernel_operations`, `kernel_journal`, the subprocess native results) and the children fence | M1, M2, M10 |
| the steward prepares; its send refused | `test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused`, `test_the_scheduled_steward_prepares_under_its_own_identity` | M12, M13 |
| size limits by name | `test_an_oversize_body_is_refused_by_name_before_any_dispatch[github, jira]` | M17 |
| crash / replay / restart for the CLI boundary | `test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[×3]`; `test_a_real_kill_during_a_gh_create_ends_unknown_once_and_the_replay_never_runs_gh_again` (a fake `gh` on PATH, the hub process SIGKILLed while gh runs, a new process: UNKNOWN `interrupted`, the replay never runs gh again, the body file was 0600) | M16 |
| the real-account leg | NOT MET in this lane (story 06) | — |

## Changed existing tests (and why)

- `tests/unit/test_hs173_nudge_wire.py`: `--body` → `--body-file` (the body leaves argv); the auth-failure case uses gh's real exit 4 (an unpinned exit 1 is now UNKNOWN, by design section 4).
- `tests/unit/test_philo9_02_round_three.py`, `tests/unit/test_philo5_the_loop_r2.py`: the canned gh answer `…/pull/7#c1` → `…/pull/7#issuecomment-1` (gh's real shape; a URL that is not the comment's is UNKNOWN now).
- `tests/e2e/test_hs173_health_glass.py`: its stub patched `build_github_pr_connector`, which the nudge no longer calls, so it would have reached a real `gh`; it now cans `channel_cli.CLI_RUNNER` and the service's runner. Not run in this lane (e2e).
- `tests/unit/_philo10_send.py`, `test_philo10_send_recovery.py`, `test_philo10_send_restart.py`: the spies take `dispatch(row, seam)` / `check_before_dispatch(target, **kw)`; the restart child gains `hold="slow"` (GATE 2) and `extra_env` (the fake gh).
- `tests/unit/test_philo10_send_contract.py`: `SIZE_LIMITS` rows are `(limit, unit)`.
- `tests/unit/test_kernel_effect_fence.py`: `GitHubChannel.login` classified "mandatory authenticated owner read" (the `_run_gh` twin).
- `docs/internal/philo/graph/atlas-phase9.json`: one anchor moved (`mcp_http.py:438` → `:452`).

## Unknown / not verified

- The real-account leg (criterion 11): no real `gh` or `acli` call ran; the `acli --json` answer shapes (proof: `id` / `commentId`, `self` / `_links.webui`), the JSON field names `acli confluence blog create --from-json` reads (this build writes `{title, status: current, body: {representation: storage, value}}`, `--space-id` in argv), and the pinned error phrases are UNVERIFIED until it runs. If `--from-json` cannot carry the title, the design's named fallback (`--from-file` + `--title`, the title then in argv) is Muad'Dib's ruling.
- The kernel line budget stays red at 432 (`holdspeak/kernel/project.py`, main 432; this story adds zero lines there).
- The e2e glass rigs, the full suite, and a rendered shot of the nudge card's UNKNOWN row at 1440 and 393 were not run in this lane.
- `tests/unit/test_philo10_rig_op.py` failed once under `-n 4` early in the build (`scripts/graph_walk.py:2358` RuntimeError) and passed alone and in every later parallel run; not diagnosed.

## Captured runs

The first scoped-suite capture below failed on two fences: the kernel line budget (inherited, main 432, captured below) and one atlas anchor my nudge-card edit moved (`ProjectRoomCore.tsx` `ItemsSection` 992 -> 1018), fixed and captured again after it. The mutation run and the docs checks ran on the same tree.

### Captured run — 2026-09-29T01:29:26Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/unit/test_philo10_cli_channels.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 47b1316b4539585afbeee4d751b4a286b91fd4c7

```text
tests/unit/test_philo10_cli_channels.py::test_gate1_the_redactors_worst_case_is_bounded
tests/unit/test_philo10_cli_channels.py::test_gate1_a_document_with_the_clis_error_phrase_keeps_the_named_code
tests/unit/test_philo10_cli_channels.py::test_gate2_the_hub_answers_a_read_during_a_slow_send[http]
tests/unit/test_philo10_cli_channels.py::test_gate2_the_hub_answers_a_read_during_a_slow_send[mcp]
tests/unit/test_philo10_cli_channels.py::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[github]
tests/unit/test_philo10_cli_channels.py::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[jira]
tests/unit/test_philo10_cli_channels.py::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[confluence]
tests/unit/test_philo10_cli_channels.py::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[github]
tests/unit/test_philo10_cli_channels.py::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[jira]
tests/unit/test_philo10_cli_channels.py::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[confluence]
tests/unit/test_philo10_cli_channels.py::test_a_plan_with_a_forbidden_flag_or_a_second_key_cannot_be_built
tests/unit/test_philo10_cli_channels.py::test_an_atlassian_send_runs_inside_the_acli_lock_and_a_second_waits
tests/unit/test_philo10_cli_channels.py::test_a_status_that_names_another_account_never_creates
tests/unit/test_philo10_cli_channels.py::test_a_github_destination_saved_as_a_is_refused_when_gh_is_b
tests/unit/test_philo10_cli_channels.py::test_an_oversize_body_is_refused_by_name_before_any_dispatch[github-65536]
tests/unit/test_philo10_cli_channels.py::test_an_oversize_body_is_refused_by_name_before_any_dispatch[jira-32767]
tests/unit/test_philo10_cli_channels.py::test_the_confluence_title_is_in_the_frozen_digest_and_never_in_argv_or_a_receipt
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[unpinned_exit-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[unpinned_exit-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[unpinned_exit-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_no_proof-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_no_proof-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_no_proof-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_malformed-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_malformed-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_malformed-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[timeout-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[timeout-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[timeout-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[pinned-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[pinned-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[pinned-confluence]
tests/unit/test_philo10_cli_channels.py::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[github]
tests/unit/test_philo10_cli_channels.py::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[jira]
tests/unit/test_philo10_cli_channels.py::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[confluence]
tests/unit/test_philo10_cli_channels.py::test_f5_the_nudges_gh_child_is_parented_under_the_owner
tests/unit/test_philo10_cli_channels.py::test_f4_a_nudge_whose_gh_times_out_is_unknown_and_never_offered_again
tests/unit/test_philo10_cli_channels.py::test_a_nudge_whose_settle_fails_after_the_comment_never_posts_twice_and_the_reaper_says_unknown
tests/unit/test_philo10_cli_channels.py::test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused
tests/unit/test_philo10_cli_channels.py::test_the_scheduled_steward_prepares_under_its_own_identity
tests/unit/test_philo10_cli_channels.py::test_a_real_kill_during_a_gh_create_ends_unknown_once_and_the_replay_never_runs_gh_again

41 tests collected in 0.19s
```

### Captured run — 2026-09-29T01:29:30Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/redact-bench.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 47b1316b4539585afbeee4d751b4a286b91fd4c7

```text
  0.000 s  Codex: 2000-char error x 10 MiB
  0.000 s  Codex: repetitive 10 MiB
  0.086 s  2000-char error x 1 MiB (the scan limit)
  0.365 s  near-miss aaaaa.. x 1 MiB
  0.154 s  near-miss ab.. x 1 MiB
  0.267 s  near-miss aab.. x 1 MiB
worst 0.365 s (story 01 on Codex's cases: 8.68 s and 26.99 s; the fence bound: 2 s)
```

### Captured run — 2026-09-29T01:29:32Z

- **Command:** `zsh .tmp/main_red.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 47b1316b4539585afbeee4d751b4a286b91fd4c7

```text
holdspeak from /private<main 3be017db>/holdspeak/__init__.py
```

> **Note (the lane, 2026-09-28):** the two captures above are superseded. The bench's dict keyed two near-miss cases alike (`aaaaa..`), so one case was not printed; the key now carries the pattern length. The `main_red.sh` capture ran without an isolated HOME: `tests/conftest.py:319` (`HOLDSPEAK_ALLOW_REAL_HOME`) refused the run before any test, so its output is only the import line and nothing touched the real HOME. The script now makes its own isolated HOME; both are captured again below.

### Captured run — 2026-09-29T01:30:49Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/redact-bench.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7f238f51057bf4821f1b6b37e8cc23e243459068

```text
  0.000 s  Codex: 2000-char error x 10 MiB
  0.000 s  Codex: repetitive 10 MiB
  0.085 s  2000-char error x 1 MiB (the scan limit)
  0.266 s  near-miss aaaaa..(10) x 1 MiB
  0.152 s  near-miss ab..(2) x 1 MiB
  0.267 s  near-miss aab..(3) x 1 MiB
  0.370 s  near-miss aaaaa..(31) x 1 MiB
worst 0.370 s (story 01 on Codex's cases: 8.68 s and 26.99 s; the fence bound: 2 s)
```

### Captured run — 2026-09-29T01:30:51Z

- **Command:** `zsh .tmp/main_red.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7f238f51057bf4821f1b6b37e8cc23e243459068

```text
holdspeak from /private<main 3be017db>/holdspeak/__init__.py
E       AssertionError: ({'name': 'subprocess.exec', 'operation_id': 'op_6f270becec0342a4878a957d39058961', 'outcome': 'succeeded', 'parent_op....send', 'operation_id': 'op_a4df4ff2d2ce43d7b732598adb3b7702', 'outcome': 'succeeded', 'parent_
E       assert '' == 'op_a4df4ff2d...2598adb3b7702'
E         
E         - op_a4df4ff2d2ce43d7b732598adb3b7702
E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_b35aef8938ec4b4ea466f05bd061986a","receipt":{"receipt_id":"rcpt_3e87fd9504234157959ee23d4a662edd","operation_id":
E       assert 409 == 200
E        +  where 409 = <Response [409 Conflict]>.status_code
FAILED tests/unit/test_philo10_cli_channels.py::test_f5_the_nudges_gh_child_is_parented_under_the_owner
FAILED tests/unit/test_philo10_cli_channels.py::test_f4_a_nudge_whose_gh_times_out_is_unknown_and_never_offered_again
2 failed, 39 deselected in 8.10s
```

### Captured run — 2026-09-29T01:31:39Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 -rf --basetemp=.tmp/bt-ev tests/unit/test_philo10_cli_channels.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_rig_op.py tests/unit/test_hs173_nudge_wire.py tests/unit/test_philo9_02_round_three.py tests/unit/test_kernel_effect_fence.py tests/unit/test_philo9_mark_delivered.py tests/unit/test_philo9_delivery_record.py tests/unit/test_philo9_steward_restart.py tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_owner_only_code.py tests/unit/test_philo9_project_grant.py tests/unit/test_philo9_command_race.py tests/unit/test_philo9_discovery.py tests/unit/test_philo9_02_rig_op.py tests/unit/test_philo7_membership_decisions.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo5_the_loop_r2.py tests/unit/test_philo5_graph_op.py tests/unit/test_project_mcp.py tests/unit/test_project_mcp_palette.py tests/unit/test_project_mcp_driver.py tests/unit/test_project_mcp_commands.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py tests/unit/test_db.py tests/unit/test_philo_graph_atlas.py tests/unit/test_doc_drift_guard.py tests/unit/test_kernel_broker.py tests/integration/test_kernel_real_hub.py tests/integration/test_principal_separation.py tests/integration/test_hs165_mcp_walk.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 02cad494187e662a577e1fd4f09c93520d8727d8

```text
bringing up nodes...
bringing up nodes...

F....................................................................... [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 41%]
........................................................................ [ 49%]
........................................................................ [ 57%]
........................................................................ [ 65%]
........................................................................ [ 74%]
........................................................................ [ 82%]
...................................................F.................... [ 90%]
........................................................................ [ 98%]
...........                                                              [100%]
=================================== FAILURES ===================================
______________ test_kernel_broker_modules_stay_within_line_budget ______________
[gw6] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-10-02/.venv/bin/python

    def test_kernel_broker_modules_stay_within_line_budget() -> None:
        offenders: list[str] = []
        for path in _broker_modules():
            budget = (
                _BROKER_INIT_BUDGET if path.name == "__init__.py" else _BROKER_MODULE_BUDGET
            )
            relative = path.relative_to(_REPO).as_posix()
            allowed = max(budget, _BROKER_BUDGET_DEBT.get(relative, 0))
            lines = _line_count(path)
            if lines > allowed:
                recorded = _BROKER_BUDGET_DEBT.get(relative)
                ceiling = (
                    f"recorded debt of {recorded}" if recorded else f"{budget}-line budget"
                )
                offenders.append(
                    f"kernel broker module over its {ceiling}: "
                    f"{path.relative_to(_REPO)}: {lines} lines"
                )
>       assert not offenders, (
            "broker density guard failed — carve a typed concern module; don't bump "
            "the budget:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: broker density guard failed — carve a typed concern module; don't bump the budget:
E           kernel broker module over its 300-line budget: holdspeak/kernel/project.py: 432 lines
E       assert not ['kernel broker module over its 300-line budget: holdspeak/kernel/project.py: 432 lines']

tests/unit/test_kernel_effect_fence.py:1281: AssertionError
______ test_every_source_reference_lands_on_its_symbol[atlas-phase9.json] ______
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-10-02/.venv/bin/python

every_atlas = {'atlas_version': 'phase9-room', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 25, 'edge_ids': ['edg... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}

    def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
        """A line number is evidence, not identity (brief section 1).
    
        The cited line must still hold the cited symbol, or the reference has
        drifted and the claim behind it is no longer proven.
        """
        problems: list[str] = []
        for state in every_atlas["states"]:
            for ref in state["sources"]:
                target = REPO / ref["path"]
                if not target.is_file():
                    problems.append(f"{state['id']}: missing file {ref['path']}")
                    continue
                lines = target.read_text(errors="replace").splitlines()
                if not 1 <= ref["line"] <= len(lines):
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                    )
                    continue
                line = lines[ref["line"] - 1]
                if ref["symbol"] not in line:
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                        f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                    )
>       assert not problems, "\n".join(problems)
E       AssertionError: state.desk_presentation.p9_room_face: web/src/features/project-room/ProjectRoomCore.tsx:992 no longer holds 'function ItemsSection' (line reads '}')
E       assert not ["state.desk_presentation.p9_room_face: web/src/features/project-room/ProjectRoomCore.tsx:992 no longer holds 'function ItemsSection' (line reads '}')"]

tests/unit/test_philo_graph_atlas.py:279: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9.json]
2 failed, 873 passed in 158.83s (0:02:38)
```

### Captured run — 2026-09-29T01:34:20Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02cad494187e662a577e1fd4f09c93520d8727d8

```text
== scripts/gen_operations_json.py --check
OK docs/generated/operations.json
== scripts/gen_mcp_sidecar_doc.py --check
wrote docs/MCP_SIDECAR.md
  246 tools across 43 families
== scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
== scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
== scripts/philo_api_reference.py --check
API reference checked
== scripts/philo_openapi_reference.py --check
OpenAPI: 579 paths
== scripts/philo_boundary_census.py --check
Boundary candidate census checked
== scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
== scripts/philo_config_reference.py --check
Configuration declaration reference is current
== scripts/philo_graph_reference.py --check
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
== scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
== scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
== scripts/check_doc_coverage.py --check
Documentation coverage checked.
== scripts/residual_census.py --check
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-10-02
DOCS RC=0
```

### Captured run — 2026-09-29T01:35:10Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02cad494187e662a577e1fd4f09c93520d8727d8

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 15.69s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 14.18 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 4.13s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 6.59s
    first assertion: E           AssertionError: the read waited 1.382 s during the send (baseline 0.005 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 7.79s
    first assertion: E           AssertionError: the read waited 1.394 s during the send (baseline 0.003 s)
CAUGHT M1 the CLI children unparented: rc=1 1 failed in 3.37s
    first assertion: E           AssertionError: {'name': 'subprocess.exec', 'operation_id': 'op_471daf64a0dd4885a6f6cb571626d800', 'outcome': 'succeeded', 'parent_operation_id': ''
CAUGHT M2 the CLI children under the default local-owner (the seam's principal not threaded): rc=1 1 failed in 3.60s
    first assertion: E       AssertionError: {"send":{"id":"chs_fa091955bf189556b3b0dd89","document_ref":"project_update:pupd_159e1f082c4040dc823daf90666cde52","destination_id":"chd
CAUGHT M3 a nudge's UNKNOWN treated as a known failure (F4, main's mapping): rc=1 1 failed in 3.63s
    first assertion: E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_9d248dac20ba4bf7a849b3e54712fd0a"
CAUGHT M4 an unpinned nonzero exit is FAILED: rc=1 1 failed in 3.61s
    first assertion: E           AssertionError: {'operation_id': 'op_11e4101de5d94afd941a502fbd7bd285', 'outcome': 'failed', 'receipt': {'actor_identity': 'owner-sess...b.com', 'lo
CAUGHT M5 exit 0 without a proof is SENT: rc=1 1 failed in 3.55s
    first assertion: E           AssertionError: {'operation_id': 'op_008ad1fd1ee949f4bfff5b120a7d4e14', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...', 'site': 
CAUGHT M6 the GitHub login not compared before the boundary: rc=1 1 failed in 3.33s
    first assertion: E       AssertionError: {"send":{"id":"chs_488881aedc7c319fd7fe6d7e","document_ref":"project_update:pupd_97388b529131411fb5a6eae208b186dd","destination_id":"chd
CAUGHT M7 the Atlassian create outside the acli lock: rc=1 1 failed in 33.65s
    first assertion: E       AssertionError: condition never held
CAUGHT M8 a plan may carry --jql, --filter or --edit-last: rc=1 1 failed in 2.74s
    first assertion: E           Failed: DID NOT RAISE <class 'ValueError'>
CAUGHT M9 a second Jira key accepted: rc=1 1 failed in 2.21s
    first assertion: E           holdspeak.services.errors.ValidationError: A Jira destination needs one work item key, like ABC-123
CAUGHT M10 the body in argv, not in the private file: rc=1 1 failed in 1.50s
    first assertion: E       AssertionError: assert 'failed' == 'sent'
CAUGHT M11 the Confluence title in argv: rc=1 1 failed in 2.21s
    first assertion: E           assert (False)
CAUGHT M12 the steward's child send admitted (no owner-press rule): rc=1 1 failed in 1.82s
    first assertion: E       AssertionError: assert ('sent', 'op_...2eadca7ee676') == ('prepared', ...2eadca7ee676')
CAUGHT M13 the scheduler may not submit the steward's prepare: rc=1 1 failed in 1.66s
    first assertion: E       ValueError: too many values to unpack (expected 1)
CAUGHT M14 the nudge without its durable boundary (it stays proposed while gh runs): rc=1 1 failed in 1.60s
    first assertion: E       AssertionError: assert 'proposed' == 'sending'
CAUGHT M15 the reaper leaves a sending nudge as it is: rc=1 1 failed in 1.58s
    first assertion: E       KeyError: 'outcome'
CAUGHT M16 a CLI take-over dispatches from a dispatching row as from a prepared one: rc=1 1 failed in 1.61s
    first assertion: E       AssertionError: assert ('sent', None) == ('unknown', 'interrupted')
CAUGHT M17 the per-channel size limit dropped: rc=1 1 failed in 1.56s
    first assertion: E       AssertionError: {"send":{"id":"chs_e144357ed5bdfdaf6499f25a","document_ref":"project_update:pupd_8a590d9d71984e909a3a62fd42eaa105","destination_id":"chd
CAUGHT M18 the file mode not private: rc=1 1 failed in 1.52s
    first assertion: E       assert 420 == 384
22/22 mutations caught
```

### Captured run — 2026-09-29T01:37:40Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02cad494187e662a577e1fd4f09c93520d8727d8

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2944 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T01:38:49Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/unit/test_philo_graph_atlas.py tests/unit/test_kernel_effect_fence.py -rf`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 16de12c222fd1fc60312ac2da471f036e3ae6577

```text
........................................................................ [ 70%]
..........................F...                                           [100%]
=================================== FAILURES ===================================
______________ test_kernel_broker_modules_stay_within_line_budget ______________

    def test_kernel_broker_modules_stay_within_line_budget() -> None:
        offenders: list[str] = []
        for path in _broker_modules():
            budget = (
                _BROKER_INIT_BUDGET if path.name == "__init__.py" else _BROKER_MODULE_BUDGET
            )
            relative = path.relative_to(_REPO).as_posix()
            allowed = max(budget, _BROKER_BUDGET_DEBT.get(relative, 0))
            lines = _line_count(path)
            if lines > allowed:
                recorded = _BROKER_BUDGET_DEBT.get(relative)
                ceiling = (
                    f"recorded debt of {recorded}" if recorded else f"{budget}-line budget"
                )
                offenders.append(
                    f"kernel broker module over its {ceiling}: "
                    f"{path.relative_to(_REPO)}: {lines} lines"
                )
>       assert not offenders, (
            "broker density guard failed — carve a typed concern module; don't bump "
            "the budget:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: broker density guard failed — carve a typed concern module; don't bump the budget:
E           kernel broker module over its 300-line budget: holdspeak/kernel/project.py: 432 lines
E       assert not ['kernel broker module over its 300-line budget: holdspeak/kernel/project.py: 432 lines']

tests/unit/test_kernel_effect_fence.py:1281: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
1 failed, 101 passed in 10.41s
```

### Captured run — 2026-09-29T01:39:05Z

- **Command:** `zsh -c echo "main 3be017db: $(git show 3be017dbe:holdspeak/kernel/project.py | wc -l | tr -d " ") lines; this branch: $(wc -l < holdspeak/kernel/project.py | tr -d " ") lines (holdspeak/kernel/project.py)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 16de12c222fd1fc60312ac2da471f036e3ae6577

```text
main 3be017db: 432 lines; this branch: 432 lines (holdspeak/kernel/project.py)
```

### Captured run — 2026-09-29T01:39:05Z

- **Command:** `zsh -c cd web && npx vitest run src/features/project-room/health.test.ts && npx tsc --noEmit -p . && echo TSC-OK`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 16de12c222fd1fc60312ac2da471f036e3ae6577

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-02/web


 Test Files  1 passed (1)
      Tests  25 passed (25)
   Start at  19:39:06
   Duration  1.16s (transform 595ms, setup 72ms, import 783ms, tests 7ms, environment 213ms)

TSC-OK
```
