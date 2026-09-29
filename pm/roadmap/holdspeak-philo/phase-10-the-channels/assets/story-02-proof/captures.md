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

- **The nudge job end to end is NOT claimed.** Every nudge fence seeds its `proposed` step directly (`tests/unit/test_philo5_the_loop_r2.py:341`). Codex found that the real Door → watch → steward path makes NO nudge: the watch normalizer (`holdspeak/services/reaction_service.py:44`) drops `number` and `createdAt`, which the nudge producer needs. The defect is inherited from main and ledgered with an owner and a home: `pm/roadmap/holdspeak/BACKLOG.md` "The real Door → watch → steward path makes no nudge". This story proves only the send of a nudge that exists: its path, its parent, its outcome.
- **One owner-only rule in this branch** is `kernel/channel_send.OWNER_PRESS` (`channel.send`, `channel.discard`), read ONLY by `kernel/project_codec.py` `authorize` to refuse a steward run's child send. It lives in the codec, not in a separate thread-tool list. When #694 merges, its one source (the codec's owner-only set) must cover `channel.send` and `nudge.send`; this is checked at that merge.
- The real-account leg (criterion 11): no real `gh` or `acli` call ran; the `acli --json` answer shapes (proof: `id` / `commentId`, `self` / `_links.webui`), the JSON field names `acli confluence blog create --from-json` reads (this build writes `{title, status: current, body: {representation: storage, value}}`, `--space-id` in argv), and the pinned error phrases are UNVERIFIED until it runs. If `--from-json` cannot carry the title, the design's named fallback (`--from-file` + `--title`, the title then in argv) is Muad'Dib's ruling.
- The kernel line budget stays red at 432 (`holdspeak/kernel/project.py`, main 432; this story adds zero lines there).
- The e2e glass rigs, the full suite, and a rendered shot of the nudge card's UNKNOWN row at 1440 and 393 were not run in this lane.
- `tests/unit/test_philo10_rig_op.py` failed once under `-n 4` early in the build (`scripts/graph_walk.py:2358` RuntimeError) and passed alone and in every later parallel run; not diagnosed.

## Round two (Codex Astra r1 DO-NOT-RATIFY, `checks/story-02-built-astra-r1.md`)

| Finding | Paid by | Fence (red first) |
|---|---|---|
| 1. UNKNOWN nudge offered Send again after remount or reload | `initialNudgeCard` (model.ts): the card starts from the step's persisted state; the Room keeps its own UNKNOWN answer across close/reopen; `pr_number` on the wire's `nudge` | `web/src/features/project-room/__tests__/nudgeUnknown10.test.tsx` (Codex's two rendered cases; red on the old initializer, mutation W1); `tests/e2e/test_philo10_02_nudge_unknown_glass.py` at 1440 and 393 on the real hub (press, close/reopen, reload; one `gh` call) |
| 2. MCP setup's identity read on the event loop | every MCP `tools/call` in the threadpool (derived, not a list); `POST /api/connections/{provider}/recheck` and `POST /api/providers/github/connection/recheck` in the threadpool | `test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub[4 cases]` (a real socket hub, a 1.5 s fake `gh`; mutations G2c, G2d) |
| 3. the nudge producer (inherited) | BACKLOG entry with owner and home | — (not claimed) |

Not paid: the other provider routes that run `gh`/`acli` on the loop (`holdspeak/web/routes/providers.py` discover and status reads) are inherited Phase 9 routes, not this story's operations.

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


## Round two captures

The scoped run below is red on one fence only: the inherited kernel line budget (`holdspeak/kernel/project.py` 432 lines on main and here). An earlier round-two run, not captured, found two moved atlas anchors (`ProjectRoomCore.tsx` `ItemsSection` 1018 -> 1028, `mcp_http.py` grant route 452 -> 451); both were fixed before these captures. One uncaptured web-baseline run showed a branch-new `src/desk/components/FirstWords.test.tsx` clipboard failure. This branch does not touch that file, it passed 3 of 3 alone, and the captured run below is zero branch-new: a load flake, recorded, not diagnosed. The four shots are in `assets/story-02-shots/` (`nudge-unknown-1-after-send-{1440,393}.png`, `nudge-unknown-2-after-reload-{1440,393}.png`), for the owner's canvas review in story 04. Seen in them, and not this story's: at 393 the bottleneck row's why token (`… 1 PR WAITING`) runs past the window edge.

### Captured run — 2026-09-29T02:21:27Z

- **Command:** `zsh -c cd web && npx vitest run src/features/project-room/__tests__/nudgeUnknown10.test.tsx src/features/project-room/health.test.ts && npx tsc --noEmit -p . && echo TSC-OK`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-02/web


 Test Files  2 passed (2)
      Tests  27 passed (27)
   Start at  20:21:27
   Duration  1.01s (transform 803ms, setup 134ms, import 1.18s, tests 74ms, environment 397ms)

TSC-OK
```

### Captured run — 2026-09-29T02:21:38Z

- **Command:** `env PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm HOLDSPEAK_EVIDENCE_WRITE=1 .tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/e2e/test_philo10_02_nudge_unknown_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

```text
..                                                                       [100%]
2 passed in 36.67s
```

### Captured run — 2026-09-29T02:22:18Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/unit/test_philo10_cli_channels.py -k slow_cli_read`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

```text
....                                                                     [100%]
4 passed, 41 deselected in 19.76s
```

### Captured run — 2026-09-29T02:22:39Z

- **Command:** `bash .tmp/r2-scoped.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  6%]
........................................................................ [ 13%]
........................................................................ [ 20%]
........................................................................ [ 27%]
........................................................................ [ 34%]
........................................................................ [ 41%]
........................................................................ [ 48%]
..........F............................................................. [ 55%]
........................................................................ [ 62%]
........................................................................ [ 69%]
........................................................................ [ 75%]
........................................................................ [ 82%]
........................................................................ [ 89%]
........................................................................ [ 96%]
...................................                                      [100%]
=================================== FAILURES ===================================
______________ test_kernel_broker_modules_stay_within_line_budget ______________
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-10-02/.venv/bin/python

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
1 failed, 1042 passed in 307.55s (0:05:07)
```

### Captured run — 2026-09-29T02:27:48Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

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

### Captured run — 2026-09-29T02:28:26Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 10.67s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 9.43 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 2.70s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 5.52s
    first assertion: E           AssertionError: the read waited 1.399 s during the send (baseline 0.001 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 5.07s
    first assertion: E           AssertionError: the read waited 1.416 s during the send (baseline 0.003 s)
CAUGHT G2c (round two) MCP tool calls on the event loop again (setup's identity read): rc=1 1 failed in 5.51s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.510 s during the slow gh call
CAUGHT G2d (round two) the HTTP recheck on the event loop: rc=1 1 failed in 5.08s
    first assertion: E           AssertionError: http-recheck: the read waited 1.338 s during the slow gh call
CAUGHT W1 (round two) the nudge card starts open whatever its step's persisted state: rc=1    Duration  3.11s (transform 1.20s, setup 149ms, import 1.73s, tests 110ms, environment 913ms)
    first assertion: × UNKNOWN survives closing and reopening the card 78ms
CAUGHT M1 the CLI children unparented: rc=1 1 failed in 3.35s
    first assertion: E           AssertionError: {'name': 'subprocess.exec', 'operation_id': 'op_736e508a0ea24ee9bac743edb270246e', 'outcome': 'succeeded', 'parent_operation_id': ''
CAUGHT M2 the CLI children under the default local-owner (the seam's principal not threaded): rc=1 1 failed in 2.58s
    first assertion: E       AssertionError: {"send":{"id":"chs_997189ae2bf01030136ba49e","document_ref":"project_update:pupd_fd695397542e4fe6bd02cc359e8e032c","destination_id":"chd
CAUGHT M3 a nudge's UNKNOWN treated as a known failure (F4, main's mapping): rc=1 1 failed in 2.46s
    first assertion: E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_4e3b1ef4eec04ce9ad3828658d4be05d"
CAUGHT M4 an unpinned nonzero exit is FAILED: rc=1 1 failed in 2.84s
    first assertion: E           AssertionError: {'operation_id': 'op_b943719659c04bcb8229745097fe7fc4', 'outcome': 'failed', 'receipt': {'actor_identity': 'owner-sess...b.com', 'lo
CAUGHT M5 exit 0 without a proof is SENT: rc=1 1 failed in 2.84s
    first assertion: E           AssertionError: {'operation_id': 'op_13c2c02a29234a93a9527e7ec39dce9a', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...', 'site': 
CAUGHT M6 the GitHub login not compared before the boundary: rc=1 1 failed in 3.08s
    first assertion: E       AssertionError: {"send":{"id":"chs_5737fa4f5633c3884ecfbbaf","document_ref":"project_update:pupd_0b8e4a709dd1400bbcca02aae6f82fcf","destination_id":"chd
CAUGHT M7 the Atlassian create outside the acli lock: rc=1 1 failed in 33.06s
    first assertion: E       AssertionError: condition never held
CAUGHT M8 a plan may carry --jql, --filter or --edit-last: rc=1 1 failed in 2.95s
    first assertion: E           Failed: DID NOT RAISE <class 'ValueError'>
CAUGHT M9 a second Jira key accepted: rc=1 1 failed in 3.48s
    first assertion: E           holdspeak.services.errors.ValidationError: A Jira destination needs one work item key, like ABC-123
CAUGHT M10 the body in argv, not in the private file: rc=1 1 failed in 3.17s
    first assertion: E       AssertionError: assert 'failed' == 'sent'
CAUGHT M11 the Confluence title in argv: rc=1 1 failed in 2.74s
    first assertion: E           assert (False)
CAUGHT M12 the steward's child send admitted (no owner-press rule): rc=1 1 failed in 2.84s
    first assertion: E       AssertionError: assert ('sent', 'op_...0f72324fdc9c') == ('prepared', ...0f72324fdc9c')
CAUGHT M13 the scheduler may not submit the steward's prepare: rc=1 1 failed in 2.26s
    first assertion: E       ValueError: too many values to unpack (expected 1)
CAUGHT M14 the nudge without its durable boundary (it stays proposed while gh runs): rc=1 1 failed in 2.68s
    first assertion: E       AssertionError: assert 'proposed' == 'sending'
CAUGHT M15 the reaper leaves a sending nudge as it is: rc=1 1 failed in 2.69s
    first assertion: E       KeyError: 'outcome'
CAUGHT M16 a CLI take-over dispatches from a dispatching row as from a prepared one: rc=1 1 failed in 2.76s
    first assertion: E       AssertionError: assert ('sent', None) == ('unknown', 'interrupted')
CAUGHT M17 the per-channel size limit dropped: rc=1 1 failed in 2.73s
    first assertion: E       AssertionError: {"send":{"id":"chs_50251cafb46de3d3a30b28a4","document_ref":"project_update:pupd_75fe292b2c2147658825a8e82dc52f59","destination_id":"chd
CAUGHT M18 the file mode not private: rc=1 1 failed in 2.60s
    first assertion: E       assert 420 == 384
25/25 mutations caught
```

### Captured run — 2026-09-29T02:31:05Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 413ed38f05e8023a1c0bfc44e6d0bdf16bcdef5c

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2946 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```


## Round three (Codex Astra r2 DO-NOT-RATIFY, `checks/story-02-built-astra-r2.md`)

| Finding | Paid by | Fence (red first) |
|---|---|---|
| 1. P1 the blanket MCP threadpool exposed a settings race | (a) reverted: `OperationDescriptor.blocking_io` (declared on `channel.send`, `channel.save_destination`, `nudge.send`, `connection.recheck`; exported in `docs/generated/operations.json`) decides the threadpool on MCP (`mcp_http.py` `_blocking_io_tools`) and on the channel routes; (b) `settings_service._SETTINGS_WRITE` around the revision check + read/merge/write; `Config.save` writes a temporary file, fsyncs it, then `os.replace` | `tests/unit/test_philo10_settings_atomic.py` (3 fences; all three red on b52bfcdb, captured below; mutations S1, S2); the slow-gh fence still green (mutations G2c, G2e) |
| 2. P1 a late UNKNOWN missed a card reopened mid-send | the Room holds `NudgeLocal` per bottleneck (pending, unknown, failed, sent) and keys the card by it; a pending card is busy (no second post) | `nudgeUnknown10.test.tsx` "UNKNOWN survives a close and reopen while Send is still in flight" (Codex's probe; red without the key, mutation W2); the real-hub glass now closes and reopens the card while the answer is held in flight, at 1440 and 393 |
| 3. #694's one owner-only table | owed at the merge of main | — |

Not in this round: other operations that run a CLI on the loop today (for example `project.watch.test`) do not declare `blocking_io` yet; they are inherited, and #694's per-tool classification table is the home for the flag.

### Round three captures

The scoped run is red on the inherited kernel line budget only (432 on main and here). The first mutation capture below exits 1 on a script fault, not a missed mutation: row W1's source text had moved in this round (the card's initializer now reads the Room's live state). S2 was also red for the wrong reason: its mutation broke the first save instead of tearing a write. Both rows are corrected, and the second mutation capture is the verdict: 29/29 caught, with S2 red on the torn file. The four shots in `assets/story-02-shots/` are re-shot: the glass now closes and reopens the card while the answer is held in flight.

### Captured run — 2026-09-29T03:16:52Z

- **Command:** `zsh .tmp/b52_red.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
E               AssertionError: (0, [(False, {'settings': {'_calendar_sources': [], '_calendar_subscription': {'egress': False, 'host': '', 'kind': 'd..., 'refresh_seconds': 900}, '_placement': {'meeting': {...}}, '_revi
E               assert (2 == 1)
E                +  where 2 = len([(False, {'settings': {'_calendar_sources': [], '_calendar_subscription': {'egress': False, 'host': '', 'kind': 'disab...cal', 'model': 'Qwen3.5-9B-Instruct-Q6_K', 'node': '', ...}}, '_r
E       AssertionError: ['accepted', 'accepted']
E       assert ['accepted', 'accepted'] == ['accepted', 'settings_stale']
E         
E         At index 1 diff: 'accepted' != 'settings_stale'
E         Use -v to get more diff
E       assert ('{\n  "config...oss_meeting_r' == '{\n  "config...": []\n  }\n}'
E         
E         Skipping 347 identical leading characters in diff, use -v to show
E         - _sounds": true
E         ?           ^^^
E         + _sounds": false
E         ?           ^^^^
E             },...
E         
E         ...Full output truncated (137 lines hidden), use '-vv' to show)
FAILED tests/unit/test_philo10_settings_atomic.py::test_concurrent_mcp_settings_updates_with_one_revision_let_exactly_one_win
FAILED tests/unit/test_philo10_settings_atomic.py::test_the_settings_service_itself_lets_exactly_one_same_revision_write_win
FAILED tests/unit/test_philo10_settings_atomic.py::test_a_settings_write_that_fails_midway_leaves_the_previous_file_whole
3 failed in 9.01s
```

### Captured run — 2026-09-29T03:17:36Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/unit/test_philo10_settings_atomic.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
...                                                                      [100%]
3 passed in 6.40s
```

### Captured run — 2026-09-29T03:18:17Z

- **Command:** `zsh -c cd web && npx vitest run src/features/project-room/__tests__/nudgeUnknown10.test.tsx src/features/project-room/health.test.ts && npx tsc --noEmit -p . && echo TSC-OK`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-02/web


 Test Files  2 passed (2)
      Tests  28 passed (28)
   Start at  21:18:20
   Duration  11.33s (transform 10.59s, setup 9.90s, import 3.06s, tests 188ms, environment 8.87s)

TSC-OK
```

### Captured run — 2026-09-29T03:18:53Z

- **Command:** `env PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm HOLDSPEAK_EVIDENCE_WRITE=1 .tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/e2e/test_philo10_02_nudge_unknown_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
..                                                                       [100%]
2 passed in 44.95s
```

### Captured run — 2026-09-29T03:19:42Z

- **Command:** `bash .tmp/r2-scoped.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  6%]
........................................................................ [ 13%]
........................................................................ [ 20%]
........................................................................ [ 27%]
........................................................................ [ 34%]
........................................................................ [ 41%]
................................................................F....... [ 48%]
........................................................................ [ 55%]
........................................................................ [ 61%]
........................................................................ [ 68%]
........................................................................ [ 75%]
........................................................................ [ 82%]
........................................................................ [ 89%]
........................................................................ [ 96%]
......................................                                   [100%]
=================================== FAILURES ===================================
______________ test_kernel_broker_modules_stay_within_line_budget ______________
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-10-02/.venv/bin/python

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
1 failed, 1045 passed in 201.38s (0:03:21)
```

### Captured run — 2026-09-29T03:23:04Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

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

### Captured run — 2026-09-29T03:23:46Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 12.07s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 10.74 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 2.33s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 4.62s
    first assertion: E           AssertionError: the read waited 1.415 s during the send (baseline 0.002 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 4.71s
    first assertion: E           AssertionError: the read waited 1.389 s during the send (baseline 0.002 s)
CAUGHT G2c (round three) MCP tool calls on the event loop again (setup's identity read): rc=1 1 failed in 5.57s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.455 s during the slow gh call
CAUGHT G2d (round two) the HTTP recheck on the event loop: rc=1 1 failed in 5.51s
    first assertion: E           AssertionError: http-recheck: the read waited 1.338 s during the slow gh call
CAUGHT G2e (round three) channel.save_destination does not declare its blocking I/O: rc=1 1 failed in 4.94s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.404 s during the slow gh call
CAUGHT S1 (round three) the settings write without its lock: rc=1 1 failed in 2.95s
    first assertion: E       AssertionError: ['accepted', 'accepted']
CAUGHT S2 (round three) the settings file written in place (not atomic): rc=1 1 failed in 0.57s
    first assertion: E               FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-2737/te
CAUGHT W2 (round three) the nudge card not keyed by the Room's live state: rc=1    Duration  4.86s (transform 1.30s, setup 564ms, import 2.26s, tests 186ms, environment 1.63s)
    first assertion: × UNKNOWN survives a close and reopen while Send is still in flight 50ms
Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-philo-10-02/pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt", line 151, in <module>
    assert mutated.count(before) == 1, (name, "the original text is not unique", before[:60])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ("W1 (round two) the nudge card starts open whatever its step's persisted state", 'the original text is not unique', 'useReducer(nudgeCardReducer, initialNudgeCard(persistedState')
```

### Captured run — 2026-09-29T03:24:46Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2947 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T03:26:33Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cc0fa5b3a1e794426d2161fb9730e605e674ec84

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 12.07s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 9.24 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 4.05s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 4.60s
    first assertion: E           AssertionError: the read waited 1.400 s during the send (baseline 0.005 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 4.93s
    first assertion: E           AssertionError: the read waited 1.408 s during the send (baseline 0.003 s)
CAUGHT G2c (round three) MCP tool calls on the event loop again (setup's identity read): rc=1 1 failed in 5.69s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.482 s during the slow gh call
CAUGHT G2d (round two) the HTTP recheck on the event loop: rc=1 1 failed in 4.81s
    first assertion: E           AssertionError: http-recheck: the read waited 1.299 s during the slow gh call
CAUGHT G2e (round three) channel.save_destination does not declare its blocking I/O: rc=1 1 failed in 6.23s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.688 s during the slow gh call
CAUGHT S1 (round three) the settings write without its lock: rc=1 1 failed in 4.26s
    first assertion: E       AssertionError: ['accepted', 'accepted']
CAUGHT S2 (round three) the settings file written in place (not atomic), as before this round: rc=1 1 failed in 0.73s
    first assertion: E       assert ('{\n  "config...oss_meeting_r' == '{\n  "config...": []\n  }\n}'
CAUGHT W2 (round three) the nudge card not keyed by the Room's live state: rc=1    Duration  4.13s (transform 1.13s, setup 497ms, import 1.86s, tests 118ms, environment 1.43s)
    first assertion: × UNKNOWN survives a close and reopen while Send is still in flight 33ms
CAUGHT W1 (round two) the nudge card starts open whatever its step's persisted state: rc=1    Duration  2.91s (transform 1.01s, setup 91ms, import 1.34s, tests 1.13s, environment 243ms)
    first assertion: × UNKNOWN survives closing and reopening the card 1073ms
CAUGHT M1 the CLI children unparented: rc=1 1 failed in 4.24s
    first assertion: E           AssertionError: {'name': 'subprocess.exec', 'operation_id': 'op_250dd6aca0844d229fd5d80fb9640834', 'outcome': 'succeeded', 'parent_operation_id': ''
CAUGHT M2 the CLI children under the default local-owner (the seam's principal not threaded): rc=1 1 failed in 7.02s
    first assertion: E       AssertionError: {"send":{"id":"chs_c5039d83ecf66b703ddf4e69","document_ref":"project_update:pupd_2e8002e272e74a6faf4911e7b7e43bd1","destination_id":"chd
CAUGHT M3 a nudge's UNKNOWN treated as a known failure (F4, main's mapping): rc=1 1 failed in 2.54s
    first assertion: E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_18cdc560d87f4f15beaab604449f3d98"
CAUGHT M4 an unpinned nonzero exit is FAILED: rc=1 1 failed in 1.89s
    first assertion: E           AssertionError: {'operation_id': 'op_2237e21fac854cafb0ac443bd2686bca', 'outcome': 'failed', 'receipt': {'actor_identity': 'owner-sess...b.com', 'lo
CAUGHT M5 exit 0 without a proof is SENT: rc=1 1 failed in 1.55s
    first assertion: E           AssertionError: {'operation_id': 'op_6c2ad3d3a6a64953ab521210c4c2e932', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...', 'site': 
CAUGHT M6 the GitHub login not compared before the boundary: rc=1 1 failed in 1.37s
    first assertion: E       AssertionError: {"send":{"id":"chs_cd71f9405fc54e23b1676f3c","document_ref":"project_update:pupd_fbdf22989107471b8710b341735b4b4a","destination_id":"chd
CAUGHT M7 the Atlassian create outside the acli lock: rc=1 1 failed in 31.47s
    first assertion: E       AssertionError: condition never held
CAUGHT M8 a plan may carry --jql, --filter or --edit-last: rc=1 1 failed in 1.55s
    first assertion: E           Failed: DID NOT RAISE <class 'ValueError'>
CAUGHT M9 a second Jira key accepted: rc=1 1 failed in 1.43s
    first assertion: E           holdspeak.services.errors.ValidationError: A Jira destination needs one work item key, like ABC-123
CAUGHT M10 the body in argv, not in the private file: rc=1 1 failed in 1.49s
    first assertion: E       AssertionError: assert 'failed' == 'sent'
CAUGHT M11 the Confluence title in argv: rc=1 1 failed in 1.43s
    first assertion: E           assert (False)
CAUGHT M12 the steward's child send admitted (no owner-press rule): rc=1 1 failed in 1.49s
    first assertion: E       AssertionError: assert ('sent', 'op_...c52a5295e78d') == ('prepared', ...c52a5295e78d')
CAUGHT M13 the scheduler may not submit the steward's prepare: rc=1 1 failed in 1.48s
    first assertion: E       ValueError: too many values to unpack (expected 1)
CAUGHT M14 the nudge without its durable boundary (it stays proposed while gh runs): rc=1 1 failed in 1.41s
    first assertion: E       AssertionError: assert 'proposed' == 'sending'
CAUGHT M15 the reaper leaves a sending nudge as it is: rc=1 1 failed in 1.49s
    first assertion: E       KeyError: 'outcome'
CAUGHT M16 a CLI take-over dispatches from a dispatching row as from a prepared one: rc=1 1 failed in 1.44s
    first assertion: E       AssertionError: assert ('sent', None) == ('unknown', 'interrupted')
CAUGHT M17 the per-channel size limit dropped: rc=1 1 failed in 1.54s
    first assertion: E       AssertionError: {"send":{"id":"chs_40303661327b3ec94cb2eb9b","document_ref":"project_update:pupd_33b3386e547e4c3e94badb246ada6631","destination_id":"chd
CAUGHT M18 the file mode not private: rc=1 1 failed in 1.46s
    first assertion: E       assert 420 == 384
29/29 mutations caught
```


## Round four (Codex Astra r3 DO-NOT-RATIFY on one P2, `checks/story-02-built-astra-r3.md`)

Codex found the settings work, the UNKNOWN work and the responsiveness work paid (in-process, the normal one-hub topology, the proxy forwards).

| Finding | Paid by | Fence (red first) |
|---|---|---|
| P2: re-keying the card discarded the owner's edited comment (Edit, Send, known failure, Send again submitted the DEFAULT text) | `NudgeLocal.text`: the Room's per-Send state keeps the text as submitted; `initialNudgeCard` restores it on every remount (pending, failed, open) | `nudgeUnknown10.test.tsx` "a known failed Send keeps the edited comment for retry" and "retry sends the edited comment after the real API reports a known failure" (Codex's probes; the second reads the retry's REQUEST BODY through the real `apiFetch`); red without the text (mutation W3); the three UNKNOWN fences stay green |
| The settings scope, stated honestly | the lock is PROCESS-LOCAL: it covers one hub, the stdio proxy forwarding to it, and a second hub on one database (refused by the database-owner lock). Two processes writing ONE config file with DIFFERENT databases can still lose an update (Codex's two-process probe). No reader sees a torn file. | BACKLOG row "Two processes writing one settings file can lose an update"; no cross-process lock now (Tenet 1) |
| #694's single tool-authority table | owed at the merge of main: fold `blocking_io` and `OWNER_PRESS` into it and check that `channel.send` and `nudge.send` are EGRESS there | — |

### Round four captures

The four glass shots were re-shot by this run.

### Captured run — 2026-09-29T03:44:22Z

- **Command:** `zsh -c cd web && npx vitest run src/features/project-room/__tests__/nudgeUnknown10.test.tsx src/features/project-room/health.test.ts && npx tsc --noEmit -p . && echo TSC-OK`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54c1e69b995c94bc50cb4595e27ac43409a67808

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-02/web


 Test Files  2 passed (2)
      Tests  30 passed (30)
   Start at  21:44:23
   Duration  2.00s (transform 1.67s, setup 215ms, import 2.44s, tests 255ms, environment 659ms)

TSC-OK
```

### Captured run — 2026-09-29T03:44:44Z

- **Command:** `env PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm HOLDSPEAK_EVIDENCE_WRITE=1 .tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/e2e/test_philo10_02_nudge_unknown_glass.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo10_settings_atomic.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54c1e69b995c94bc50cb4595e27ac43409a67808

```text
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 63.18s (0:01:03)
```

### Captured run — 2026-09-29T03:45:59Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54c1e69b995c94bc50cb4595e27ac43409a67808

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

### Captured run — 2026-09-29T03:46:44Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54c1e69b995c94bc50cb4595e27ac43409a67808

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 11.39s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 10.11 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 2.54s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 5.33s
    first assertion: E           AssertionError: the read waited 1.399 s during the send (baseline 0.003 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 5.00s
    first assertion: E           AssertionError: the read waited 1.402 s during the send (baseline 0.004 s)
CAUGHT G2c (round three) MCP tool calls on the event loop again (setup's identity read): rc=1 1 failed in 7.73s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.495 s during the slow gh call
CAUGHT G2d (round two) the HTTP recheck on the event loop: rc=1 1 failed in 4.82s
    first assertion: E           AssertionError: http-recheck: the read waited 1.301 s during the slow gh call
CAUGHT G2e (round three) channel.save_destination does not declare its blocking I/O: rc=1 1 failed in 5.10s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.355 s during the slow gh call
CAUGHT S1 (round three) the settings write without its lock: rc=1 1 failed in 3.42s
    first assertion: E       AssertionError: ['accepted', 'accepted']
CAUGHT S2 (round three) the settings file written in place (not atomic), as before this round: rc=1 1 failed in 0.57s
    first assertion: E       assert ('{\n  "config...oss_meeting_r' == '{\n  "config...": []\n  }\n}'
CAUGHT W2 (round three) the nudge card not keyed by the Room's live state: rc=1    Duration  5.26s (transform 1.33s, setup 808ms, import 2.37s, tests 242ms, environment 1.63s)
    first assertion: × UNKNOWN survives a close and reopen while Send is still in flight 38ms
CAUGHT W3 (round four) the Room's per-Send state forgets the submitted text (a remount restores the default): rc=1    Duration  4.51s (transform 1.35s, setup 433ms, import 2.15s, tests 296ms, environment 1.43s)
    first assertion: × a known failed Send keeps the edited comment for retry 50ms
CAUGHT W1 (round two) the nudge card starts open whatever its step's persisted state: rc=1    Duration  6.46s (transform 1.13s, setup 439ms, import 1.88s, tests 3.23s, environment 756ms)
    first assertion: × UNKNOWN survives closing and reopening the card 1085ms
CAUGHT M1 the CLI children unparented: rc=1 1 failed in 3.89s
    first assertion: E           AssertionError: {'name': 'subprocess.exec', 'operation_id': 'op_5176a2c424754bda8794b30f5414a7b0', 'outcome': 'succeeded', 'parent_operation_id': ''
CAUGHT M2 the CLI children under the default local-owner (the seam's principal not threaded): rc=1 1 failed in 2.73s
    first assertion: E       AssertionError: {"send":{"id":"chs_98c76971e9428fec447d6053","document_ref":"project_update:pupd_6a4b5428ce5e41d69e4f6e39afa91671","destination_id":"chd
CAUGHT M3 a nudge's UNKNOWN treated as a known failure (F4, main's mapping): rc=1 1 failed in 2.73s
    first assertion: E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_2b0cd31c276e4cfc9733d9004ed7642d"
CAUGHT M4 an unpinned nonzero exit is FAILED: rc=1 1 failed in 2.42s
    first assertion: E           AssertionError: {'operation_id': 'op_582f131977ca4b648b446c56018ac5b4', 'outcome': 'failed', 'receipt': {'actor_identity': 'owner-sess...b.com', 'lo
CAUGHT M5 exit 0 without a proof is SENT: rc=1 1 failed in 4.29s
    first assertion: E           AssertionError: {'operation_id': 'op_49433c48c01d4fb594297f2797829bea', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...', 'site': 
CAUGHT M6 the GitHub login not compared before the boundary: rc=1 1 failed in 6.30s
    first assertion: E       AssertionError: {"send":{"id":"chs_07dae641e92076bb4b39e4c1","document_ref":"project_update:pupd_df226fe6a7b84f36bee08efb62dc2f41","destination_id":"chd
CAUGHT M7 the Atlassian create outside the acli lock: rc=1 1 failed in 3.07s
    first assertion: E       AssertionError: [['acli', 'jira', 'auth', 'switch'], ['acli', 'jira', 'auth', 'status'], ['acli', 'jira', 'workitem', 'comment'], ['acli', 'confluence',
CAUGHT M8 a plan may carry --jql, --filter or --edit-last: rc=1 1 failed in 2.61s
    first assertion: E           Failed: DID NOT RAISE <class 'ValueError'>
CAUGHT M9 a second Jira key accepted: rc=1 1 failed in 2.61s
    first assertion: E           holdspeak.services.errors.ValidationError: A Jira destination needs one work item key, like ABC-123
CAUGHT M10 the body in argv, not in the private file: rc=1 1 failed in 2.73s
    first assertion: E       AssertionError: assert 'failed' == 'sent'
CAUGHT M11 the Confluence title in argv: rc=1 1 failed in 2.93s
    first assertion: E           assert (False)
CAUGHT M12 the steward's child send admitted (no owner-press rule): rc=1 1 failed in 3.57s
    first assertion: E       AssertionError: assert ('sent', 'op_...b97bdc21cf96') == ('prepared', ...b97bdc21cf96')
CAUGHT M13 the scheduler may not submit the steward's prepare: rc=1 1 failed in 3.58s
    first assertion: E       ValueError: too many values to unpack (expected 1)
CAUGHT M14 the nudge without its durable boundary (it stays proposed while gh runs): rc=1 1 failed in 2.87s
    first assertion: E       AssertionError: assert 'proposed' == 'sending'
CAUGHT M15 the reaper leaves a sending nudge as it is: rc=1 1 failed in 2.96s
    first assertion: E       KeyError: 'outcome'
CAUGHT M16 a CLI take-over dispatches from a dispatching row as from a prepared one: rc=1 1 failed in 2.79s
    first assertion: E       AssertionError: assert ('sent', None) == ('unknown', 'interrupted')
CAUGHT M17 the per-channel size limit dropped: rc=1 1 failed in 2.97s
    first assertion: E       AssertionError: {"send":{"id":"chs_678b2fe6408a38661e87c7a4","document_ref":"project_update:pupd_4084f76b198845adbb0c1d5d4ab92f70","destination_id":"chd
CAUGHT M18 the file mode not private: rc=1 1 failed in 2.36s
    first assertion: E       assert 420 == 384
30/30 mutations caught
```

### Captured run — 2026-09-29T03:49:30Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54c1e69b995c94bc50cb4595e27ac43409a67808

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2949 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```


## #694 merged in (main 84657927)

- **One owner-press source.** The branch's `OWNER_PRESS` set is gone. The kernel's steward-child refusal (`kernel/project_codec.py`) reads `kernel/channel_send.owner_press_operations()`, which is derived from the descriptors' `owner_press` flag (#694), the same flag the MCP authority table and the thread gate read. A steward run's child that is any owner press (`channel.send`, `channel.discard`, `channel.save_destination`, `channel.remove_destination`, `project.mark_update_delivered`, `nudge.send`) is refused with a receipt (mutations M12, M12b). The code depends on the run's actor. An owner-started or agent run's child press is refused `owner_principal_required`. A SCHEDULED steward's `nudge.send` is refused earlier, `declared_capability_required`, because the scheduler may submit only the steward's own children (`kernel/project.py` `scheduler_may_submit`); its `channel.send` / `channel.discard` reach the codec and are refused `owner_principal_required` (Codex Astra r4 finding 2).
- **`blocking_io` stays on the descriptor, one source; a census ties it to the authority table.** The two axes differ: `connection.recheck` is `work` yet runs gh; `channel.discard` is `egress` yet writes only the database. So neither can be derived from the other. The fence `test_the_sends_are_egress_owner_presses_and_blocking_io_in_the_one_table` asserts:
  - the blocking set is exactly `channel.send`, `channel.save_destination`, `nudge.send`, `connection.recheck`;
  - every blocking operation has an authority row;
  - `channel.send` and `nudge.send` are EGRESS, owner presses and blocking;
  - the kernel's press set equals the descriptors' flag.
- **Story-02 operations in the table.** Story 02 adds no new operation name; its rows (`channel.save_destination` AUTHORITY, `channel.send` / `channel.discard` / `nudge.send` EGRESS, `channel.prepare` WORK) are #694's. `test_thread_tool_gate.py` is green.
- **The kernel line budget is green now.** `project.py` is 256 lines on main (#694 carved the grant module); this branch adds zero lines there.
- **Re-anchored after the merge:** the pinned census sites that moved (`test_phase143_inference_capability_census.py` `operations.py` 2156/2157 -> 2162/2163; `test_phase143_routing_authority_census.py` `settings_service.py`, `config/core.py`, `project_service.py`) and three `atlas-phase7.json` anchors. The UNKNOWN row's lead icon is now `●` on a warning chip, not `⚠`: the UX canon ratchet counts `⚠` as an emoji, and it held the ceiling at 26.
- The first mutation capture below exits 1 on row M12. That row still named the removed `OWNER_PRESS` text; the row is corrected, and M12b is added. The second capture is the verdict: 31/31.

### Captured run — 2026-09-29T05:06:14Z

- **Command:** `bash .tmp/r5-scoped.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8aacec7c5fe9784f89c377f5ed99abce3bfee6ce

```text
bringing up nodes...
bringing up nodes...

...................s.................................................... [  5%]
........................................................................ [ 10%]
........................................................................ [ 15%]
........................................................................ [ 20%]
........................................................................ [ 25%]
........................................................................ [ 30%]
........................................................................ [ 35%]
........................................................................ [ 40%]
........................................................................ [ 45%]
........................................................................ [ 50%]
........................................................................ [ 55%]
........................................................................ [ 61%]
........................................................................ [ 66%]
........................................................................ [ 71%]
........................................................................ [ 76%]
........................................................................ [ 81%]
........................................................................ [ 86%]
........................................................................ [ 91%]
........................................................................ [ 96%]
................................................                         [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:804: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1415 passed, 1 skipped, 3 warnings in 105.38s (0:01:45)
```

### Captured run — 2026-09-29T05:07:59Z

- **Command:** `zsh -c cd web && npx vitest run src/features/project-room/__tests__/nudgeUnknown10.test.tsx src/features/project-room/health.test.ts && npx tsc --noEmit -p . && echo TSC-OK`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8aacec7c5fe9784f89c377f5ed99abce3bfee6ce

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-02/web


 Test Files  2 passed (2)
      Tests  30 passed (30)
   Start at  23:08:00
   Duration  1.17s (transform 694ms, setup 177ms, import 1.08s, tests 144ms, environment 630ms)

TSC-OK
```

### Captured run — 2026-09-29T05:08:11Z

- **Command:** `env PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm HOLDSPEAK_EVIDENCE_WRITE=1 .tmp/iso.sh .venv/bin/python -m pytest -q -p no:cacheprovider tests/e2e/test_philo10_02_nudge_unknown_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8aacec7c5fe9784f89c377f5ed99abce3bfee6ce

```text
..                                                                       [100%]
2 passed in 27.81s
```

### Captured run — 2026-09-29T05:08:41Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8aacec7c5fe9784f89c377f5ed99abce3bfee6ce

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

### Captured run — 2026-09-29T05:09:01Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 8aacec7c5fe9784f89c377f5ed99abce3bfee6ce

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 7.92s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 7.16 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 1.43s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 3.26s
    first assertion: E           AssertionError: the read waited 1.402 s during the send (baseline 0.001 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 3.28s
    first assertion: E           AssertionError: the read waited 1.380 s during the send (baseline 0.001 s)
CAUGHT G2c (round three) MCP tool calls on the event loop again (setup's identity read): rc=1 1 failed in 3.57s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.419 s during the slow gh call
CAUGHT G2d (round two) the HTTP recheck on the event loop: rc=1 1 failed in 3.44s
    first assertion: E           AssertionError: http-recheck: the read waited 1.265 s during the slow gh call
CAUGHT G2e (round three) channel.save_destination does not declare its blocking I/O: rc=1 1 failed in 3.56s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.272 s during the slow gh call
CAUGHT S1 (round three) the settings write without its lock: rc=1 1 failed in 1.68s
    first assertion: E       AssertionError: ['accepted', 'accepted']
CAUGHT S2 (round three) the settings file written in place (not atomic), as before this round: rc=1 1 failed in 0.35s
    first assertion: E       assert ('{\n  "config...oss_meeting_r' == '{\n  "config...": []\n  }\n}'
CAUGHT W2 (round three) the nudge card not keyed by the Room's live state: rc=1    Duration  1.04s (transform 425ms, setup 55ms, import 598ms, tests 138ms, environment 171ms)
    first assertion: × UNKNOWN survives a close and reopen while Send is still in flight 20ms
CAUGHT W3 (round four) the Room's per-Send state forgets the submitted text (a remount restores the default): rc=1    Duration  1.06s (transform 438ms, setup 59ms, import 612ms, tests 137ms, environment 176ms)
    first assertion: × a known failed Send keeps the edited comment for retry 23ms
CAUGHT W1 (round two) the nudge card starts open whatever its step's persisted state: rc=1    Duration  4.07s (transform 453ms, setup 58ms, import 633ms, tests 3.12s, environment 178ms)
    first assertion: × UNKNOWN survives closing and reopening the card 1053ms
CAUGHT M1 the CLI children unparented: rc=1 1 failed in 1.42s
    first assertion: E           AssertionError: {'name': 'subprocess.exec', 'operation_id': 'op_07cf27647fea47b78da42e2f9d9a2ffa', 'outcome': 'succeeded', 'parent_operation_id': ''
CAUGHT M2 the CLI children under the default local-owner (the seam's principal not threaded): rc=1 1 failed in 1.40s
    first assertion: E       AssertionError: {"send":{"id":"chs_a4066294641a6fb5b1f14b92","document_ref":"project_update:pupd_cc65fb5d7e3b430184c27a393dbcc418","destination_id":"chd
CAUGHT M3 a nudge's UNKNOWN treated as a known failure (F4, main's mapping): rc=1 1 failed in 1.40s
    first assertion: E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_bf4e12de4e6f4a679431d2c9541a2b58"
CAUGHT M4 an unpinned nonzero exit is FAILED: rc=1 1 failed in 1.46s
    first assertion: E           AssertionError: {'operation_id': 'op_1865a66906f94374812f0440ca4e0cda', 'outcome': 'failed', 'receipt': {'actor_identity': 'owner-sess...b.com', 'lo
CAUGHT M5 exit 0 without a proof is SENT: rc=1 1 failed in 1.39s
    first assertion: E           AssertionError: {'operation_id': 'op_d29c2189d46548968acdf3969a7efc43', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...', 'site': 
CAUGHT M6 the GitHub login not compared before the boundary: rc=1 1 failed in 1.37s
    first assertion: E       AssertionError: {"send":{"id":"chs_ceb49e9fd52dae4b2fdc63c9","document_ref":"project_update:pupd_6b40be86ca28480b9c7c6a74b1066489","destination_id":"chd
CAUGHT M7 the Atlassian create outside the acli lock: rc=1 1 failed in 31.44s
    first assertion: E       AssertionError: condition never held
CAUGHT M8 a plan may carry --jql, --filter or --edit-last: rc=1 1 failed in 1.39s
    first assertion: E           Failed: DID NOT RAISE <class 'ValueError'>
CAUGHT M9 a second Jira key accepted: rc=1 1 failed in 1.37s
    first assertion: E           holdspeak.services.errors.ValidationError: A Jira destination needs one work item key, like ABC-123
CAUGHT M10 the body in argv, not in the private file: rc=1 1 failed in 1.41s
    first assertion: E       AssertionError: assert 'failed' == 'sent'
CAUGHT M11 the Confluence title in argv: rc=1 1 failed in 1.36s
    first assertion: E           assert (False)
Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-philo-10-02/pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt", line 156, in <module>
    assert mutated.count(before) == 1, (name, "the original text is not unique", before[:60])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ("M12 the steward's child send admitted (no owner-press rule)", 'the original text is not unique', '        if self.name in rooms.OWNER_PRESS and context')
```

### Captured run — 2026-09-29T05:10:35Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8aacec7c5fe9784f89c377f5ed99abce3bfee6ce

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2949 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T05:11:29Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d9d439f3cd075bf8ce533f327134fd7dab6e6de2

```text
CAUGHT G1a the redactor scans the uncut error and any payload (story 01's cost): rc=1 1 failed in 7.92s
    first assertion: E           AssertionError: 2000-char error x 10 MiB: 7.19 s
CAUGHT G1b the named code passes through the redactor: rc=1 1 failed in 1.42s
    first assertion: E       AssertionError: assert ('failed', 'g...cted]_denied') == ('failed', 'g...ssion_denied')
CAUGHT G2a the HTTP routes run the service on the event loop: rc=1 1 failed in 3.45s
    first assertion: E           AssertionError: the read waited 1.404 s during the send (baseline 0.001 s)
CAUGHT G2b the MCP transport runs channel.send on the event loop: rc=1 1 failed in 3.35s
    first assertion: E           AssertionError: the read waited 1.377 s during the send (baseline 0.001 s)
CAUGHT G2c (round three) MCP tool calls on the event loop again (setup's identity read): rc=1 1 failed in 3.71s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.372 s during the slow gh call
CAUGHT G2d (round two) the HTTP recheck on the event loop: rc=1 1 failed in 3.47s
    first assertion: E           AssertionError: http-recheck: the read waited 1.262 s during the slow gh call
CAUGHT G2e (round three) channel.save_destination does not declare its blocking I/O: rc=1 1 failed in 3.52s
    first assertion: E           AssertionError: mcp-save-destination: the read waited 1.294 s during the slow gh call
CAUGHT S1 (round three) the settings write without its lock: rc=1 1 failed in 1.74s
    first assertion: E       AssertionError: ['accepted', 'accepted']
CAUGHT S2 (round three) the settings file written in place (not atomic), as before this round: rc=1 1 failed in 0.34s
    first assertion: E       assert ('{\n  "config...oss_meeting_r' == '{\n  "config...": []\n  }\n}'
CAUGHT W2 (round three) the nudge card not keyed by the Room's live state: rc=1    Duration  1.13s (transform 487ms, setup 59ms, import 682ms, tests 141ms, environment 174ms)
    first assertion: × UNKNOWN survives a close and reopen while Send is still in flight 21ms
CAUGHT W3 (round four) the Room's per-Send state forgets the submitted text (a remount restores the default): rc=1    Duration  1.20s (transform 515ms, setup 64ms, import 715ms, tests 149ms, environment 188ms)
    first assertion: × a known failed Send keeps the edited comment for retry 24ms
CAUGHT W1 (round two) the nudge card starts open whatever its step's persisted state: rc=1    Duration  4.15s (transform 503ms, setup 65ms, import 695ms, tests 3.13s, environment 184ms)
    first assertion: × UNKNOWN survives closing and reopening the card 1055ms
CAUGHT M1 the CLI children unparented: rc=1 1 failed in 1.49s
    first assertion: E           AssertionError: {'name': 'subprocess.exec', 'operation_id': 'op_524b3fe49926466e966f97a9140782de', 'outcome': 'succeeded', 'parent_operation_id': ''
CAUGHT M2 the CLI children under the default local-owner (the seam's principal not threaded): rc=1 1 failed in 1.44s
    first assertion: E       AssertionError: {"send":{"id":"chs_83beb02403af7e857fc31a0d","document_ref":"project_update:pupd_b3766d80ecb6437bb331208d8eebe8bf","destination_id":"chd
CAUGHT M3 a nudge's UNKNOWN treated as a known failure (F4, main's mapping): rc=1 1 failed in 1.36s
    first assertion: E       AssertionError: {"success":false,"error":"send_failed","code":"send_failed","message":"send failed","operation_id":"op_8ac5eae11d7b49a4b970442c27032114"
CAUGHT M4 an unpinned nonzero exit is FAILED: rc=1 1 failed in 1.43s
    first assertion: E           AssertionError: {'operation_id': 'op_23fc3daa06f242f1abb7273a36bd7018', 'outcome': 'failed', 'receipt': {'actor_identity': 'owner-sess...b.com', 'lo
CAUGHT M5 exit 0 without a proof is SENT: rc=1 1 failed in 1.41s
    first assertion: E           AssertionError: {'operation_id': 'op_9e8e6bddaa884b109c7a29f30f01fb69', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...', 'site': 
CAUGHT M6 the GitHub login not compared before the boundary: rc=1 1 failed in 1.47s
    first assertion: E       AssertionError: {"send":{"id":"chs_37ea3f5c3eedc409626e5c26","document_ref":"project_update:pupd_6b9415edcb404f26b0a5278896896057","destination_id":"chd
CAUGHT M7 the Atlassian create outside the acli lock: rc=1 1 failed in 31.44s
    first assertion: E       AssertionError: condition never held
CAUGHT M8 a plan may carry --jql, --filter or --edit-last: rc=1 1 failed in 1.40s
    first assertion: E           Failed: DID NOT RAISE <class 'ValueError'>
CAUGHT M9 a second Jira key accepted: rc=1 1 failed in 1.42s
    first assertion: E           holdspeak.services.errors.ValidationError: A Jira destination needs one work item key, like ABC-123
CAUGHT M10 the body in argv, not in the private file: rc=1 1 failed in 1.34s
    first assertion: E       AssertionError: assert 'failed' == 'sent'
CAUGHT M11 the Confluence title in argv: rc=1 1 failed in 1.39s
    first assertion: E           assert (False)
CAUGHT M12 the steward's child press admitted (no owner-press rule): rc=1 1 failed in 1.47s
    first assertion: E       AssertionError: assert ('sent', 'op_...9e7f63fef404') == ('prepared', ...9e7f63fef404')
CAUGHT M12b (#694 merged) the steward-child rule reads a hand list without channel.send, not the owner_press flag: rc=1 1 failed in 1.48s
    first assertion: E       AssertionError: assert ('sent', 'op_...62c4f419f597') == ('prepared', ...62c4f419f597')
CAUGHT M13 the scheduler may not submit the steward's prepare: rc=1 1 failed in 1.34s
    first assertion: E       ValueError: too many values to unpack (expected 1)
CAUGHT M14 the nudge without its durable boundary (it stays proposed while gh runs): rc=1 1 failed in 1.33s
    first assertion: E       AssertionError: assert 'proposed' == 'sending'
CAUGHT M15 the reaper leaves a sending nudge as it is: rc=1 1 failed in 1.41s
    first assertion: E       KeyError: 'outcome'
CAUGHT M16 a CLI take-over dispatches from a dispatching row as from a prepared one: rc=1 1 failed in 1.37s
    first assertion: E       AssertionError: assert ('sent', None) == ('unknown', 'interrupted')
CAUGHT M17 the per-channel size limit dropped: rc=1 1 failed in 1.35s
    first assertion: E       AssertionError: {"send":{"id":"chs_4c5f75f02e836a24512d23b7","document_ref":"project_update:pupd_f6153d19fa6e49659439e6a7735c2497","destination_id":"chd
CAUGHT M18 the file mode not private: rc=1 1 failed in 1.37s
    first assertion: E       assert 420 == 384
31/31 mutations caught
```


## Codex Astra r4 (`checks/story-02-built-astra-r4.md`): RATIFY-WITH-CONDITIONS

No product change requested. The one condition is Muad'Dib's full-suite result on the merge candidate `4716c010`, owed before merge. The refusal-code wording above is qualified per finding 2. The PR description is refreshed to the current build.
