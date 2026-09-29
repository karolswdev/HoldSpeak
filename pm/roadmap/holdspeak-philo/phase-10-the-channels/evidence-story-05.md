# Evidence - PHILO-10-05

- **Story:** PHILO-10-05 - The atlas cases for Send
- **Status:** done
- **Date:** 2026-09-29
- **Branch:** `feat/philo-10-05` from main `dce3afa9` (stories 01–04 merged). Round one changed no product file: it added the atlas file, the rig's recording runner and four small rig extensions, the fences, the proof scripts and the retained runs. Round two changed ONE product file, `web/src/features/channels/channels.ts` (the face's word tables, Muad'Dib's ruling); no service changed.
- **Red on main:** the pre-Phase-10 main is `98ea2cfa` (the parent of `3be017db`, story 01's merge): an export with its own web build and product package, this branch's rig and atlas copied in.

## What was built

- **`docs/internal/philo/graph/atlas-phase10.json`** (written by `assets/story-05-proof/add_atlas.py`): 27 cases — 15 face cases at 1440 and 393 and 12 `.op` twins (headless, MCP) — one state (`state.desk_presentation.p10_send_face`, its source anchors checked by the general fence) and 4 exclusions with reasons.
  - Face cases: `no_destination`, `destinations_listed`, `destination_picked`, `sending`, `sent` (the file channel: a REAL file written into the run's isolated HOME), `github_posted`, `refused`, `failed`, `unknown`, `unknown_after_restart`, `destination_changed`, `prepared`, `several`, `discard_after_send`, `receipt_after_return` (all `case.p10.send.*`).
  - Twins: `destinations_listed.op`, `sent.op`, `github_posted.op`, `refused.op`, `failed.op`, `unknown.op`, `destination_changed.op`, `prepared.op`, `several.op`, `discard_after_send.op`, `send_after_discard.op`, `replay_same_key.op`.
  - Every face case is `all_of` a readable face half AND a hub half read in the SAME observation (the press's own answer with its receipt, the hub's stored sends and history rows, the recording runner's count). No face-only proof (`test_every_face_case_reads_its_hub_outcome_in_the_same_observation`).
  - Every twin reads the kernel receipt (`kernel.receipt.read`: operation name, id, state, actor `owner`).
  - The named transitions: a restart during `dispatching` (`unknown_after_restart`: the GitHub create held after the boundary, `restart_hub`, UNKNOWN `interrupted`, ONE `gh issue comment` across both processes); a replay of the same key (`replay_same_key.op`: the first answer, one row, one history row, one create); a destination changed after prepare (`destination_changed` + `.op`: Edit parks the old destination, Send REFUSED `destination_parked`, the row stays prepared); Send and Discard together (`discard_after_send` + `.op`: Send won, Discard refused `send_already_settled` with a receipt; `send_after_discard.op`: the other order); receipts across away and back (`receipt_after_return`: SAVED after Back and reopening).
- **The rig (`scripts/graph_walk.py`)**, each addition performed, never labelled:
  - boundary `cli_runner`: a RECORDING runner at `holdspeak.services.channel_cli.CLI_RUNNER` installed INSIDE the hub process from a retained script (`tests/fixtures/philo10_atlas/gh-{posted,held,not-found,unpinned}.json`); it records each call (argv, the body file's sha256, pid) in the run HOME's `graph-walk-cli-calls.jsonl` before it answers; `hold: true` never answers. The channel's real `plan`, the kernel's `subprocess.exec` child and the owner principal run; no real `gh` or `acli`; no account. The hub boots with it again after `restart_hub`, and the log survives the restart.
  - `{hub_home}` bound to the run's isolated HOME (the file destination's folder).
  - predicate `cli_calls {argv_prefix, count}` (decidable headless); `protocol_reads` row `count` (0 included); `all_of` allowed headless (each part meets the headless guard itself).
  - ui action `scroll_into_view {selector, block}` (schema updated): the owner seats Send in the middle of the window before the press. Without it, at 393 the answer lands under the Room's sticky footer (the first run: 9 face cases at 393 read "a covering element owns hit points"). Not a claimed product defect: the long HOME path in the preview pushes Send to the footer's edge.
- **Fences** `tests/unit/test_philo10_atlas.py` (54 tests); `tests/unit/test_philo_graph_atlas.py` sibling count 45 → 57 and the channel operations in its mutating/readable sets (an `.op` predicate may be `all_of` of `op_facts` and `cli_calls`); `tests/unit/test_philo9_atlas.py` counts gain the Phase 10 file.
- **Proof scripts** (`assets/story-05-proof/`): `rig_run.py` (one hub, one HOME, one run directory `<case>--<width>/<run id>` per run, reuse refused), `retain.py` (the copier: keyed by case × width × run; refuses a label that exists, two rows sharing a directory, a directory that is not `<case>--<width>/<run id>` of its row, an observation of another case, width or verdict — all BEFORE it writes anything), `rig_phase.sh`, `batch.sh` (+ its log `batch1.log`), `equivalence.py`, `base_diff.py`, `mutations.py` (14), `fences.sh`, `exit_combos.sh`, `docs_nav.sh`.
- **Retained runs** `assets/story-05-shots/<label>/`: `p10-merged` (42, with shots), `red-98ea2cfa` (42), `p789-merged` (97, with shots), `p789-dce3afa9` (97, observations only), `base-merged` and `base-dce3afa9` (194 each, observations only), `serial-merged` (6), `s5-{merged,dce3afa9}-a{1,2,3}` (1 each).

## Round four — Muad'Dib's full suite on #698 @ `813e6684`: two branch-new reds, paid

- `tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires`: the closed UI vocabulary now names `scroll_into_view`, and a malformed seat (no selector, or a block other than start / center / end) blocks by name before any page is reached ("nothing was fired"; two cases added to the fence). `cli_calls` and the `protocol_reads` row `count` are not pinned by any closed-vocabulary fence (the predicate-kind fence reads `check_predicate` itself).
- `tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence`: `tests/unit/test_philo10_atlas.py` only READS pm/roadmap (the atlas, the retained runs, `retain.py`); every write of its copier and runner fences goes under `tmp_path`. Added to the guard's allow-list with that reason.
- Every unit file that imports the rig, plus the guard: 500 passed (capture below).

## Round three — Codex Astra r1 on #698 @ `813e6684` (RATIFY-WITH-CONDITIONS), paid

`checks/story-05-built-astra-r1.md` (verbatim). Codex reproduced 9 atlas runs and found the census honest and the recording runner answering where production reads. Its conditions:

| # | Finding | Payment | Proof |
|---|---|---|---|
| 1 (P2) | The code census silently skipped non-literal codes: an f-string, a `.format()` and a formatted code through the `reason` flow all escaped (9/9 green) | Every code expression goes through ONE reader (`_philo10_codes.py` `read`): a literal; an f-string ONLY if it is one of the eleven `ALLOWED_TEMPLATES` (the known variable-code forms); a variable only where FLOWS follows it; anything else is recorded UNSUPPORTED — in a producer, a pinned table, a `pinned()` answer, the `reason` arms, `_classify`, the transport's `code`, the kernel's row reason. New fence `test_no_code_expression_is_unsupported`; the steward module is read only for the restart's row reason (its other `code` variables are not channel codes) | `face_words_mutations.sh`: m4 (f-string), m5 (`.format()`), m6 (formatted code through the `reason` flow) RED; 6/6 red in all |
| 2 (P2) | `rig_phase.sh` ignored the build's status: npm exit 7 → the rig still walked (`--no-build`) and the wrapper exited 0 | Both branches (the tree and an export) stop on a failed build: exit 3, "BUILD FAILED: no walk, no retention" | `exit_combos.sh`: the build × rig × copier combinations on both branches (16) — a failed build exits 3 and NEITHER the rig nor the copier runs (markers); the 813e6684 script shown walking and retaining after a failed build (exit 0) |
| 3 (P3) | Stale summaries | The story's red count is 23 blocked / 17 not run (the retained runs); the Branch line says round two changed `channels.ts` | this file, the story file |

## Round two — Muad'Dib's ruling on #698: the face words, closed as a class

The census found seven codes the services emit that the face showed as raw capitals (for example `github_target_not_found` as "GITHUB TARGET NOT FOUND"). Ruled: fix it in this PR, close the class.

- **The derivation** (`tests/unit/_philo10_codes.py`), never a hand list: by AST over the channel modules (`channel_contract`, `channel_cli`, `channel_email`, `channel_service`, `kernel/channel_send`, the restart's row reason in `steward_contract`) — `ChannelRefused(code)`, `ValidationError(code=)`, `Outcome("failed"|"unknown", code)`, the `PINNED` / `FAILED_ON_CREATE` tables, a `pinned()` override's answers, `reason = a if .. else b`, the email transport's `_classify` and `EmailKeyError` / `EmailTransportError` codes, the kernel's row reasons; f-string codes as prefixes (`create_`, `github_exit_`, `unpinned_`, `payload_too_large:`); plus every `channel.*` operation's declared `refusals`. A code passed through a variable is followed by a declared FLOWS table; a NEW variable site fails the fence until it is followed. 98 codes; the census's seven were among 50 with no word.
- **The words** (`web/src/features/channels/channels.ts`): REFUSED / FAILED / UNKNOWN tables complete, and prefix tables for the variable codes; `refusedWord`, `failedWord`, `unknownWord` read them. The three dead keys (`github_issue_not_found`, `github_no_permission`, `jira_cannot_edit`: no service emits them) are gone. Plain ASD-STE100 words in capitals, e.g. **FAILED · ISSUE NOT FOUND · NOTHING SENT**, **RESULT UNKNOWN · NO CLEAR ANSWER**, **REFUSED · TOO LARGE**.
- **The fence** `tests/unit/test_philo10_face_words.py` (9): every emitted code has a word; every variable site is followed; the derivation sees a code from each source; the word functions read these tables; every word is plain capitals; the census's codes have their words. `assets/story-05-proof/face_words_mutations.sh`: 3 mutations (a word dropped, a new refusal code, a new variable site), 3 red.
- **Through the real producer at 1440 and 393:** `case.p10.send.failed` now also reads **ISSUE NOT FOUND** (gh's pinned "could not resolve to an issue" at the recording runner → `github_target_not_found` → the face). `words-merged`: 3/3 pass (both widths and the twin). Red on main `dce3afa9` (its own bundle): `words-red-dce3afa9` 0/2, "'ISSUE NOT FOUND' NOT in observe_at text". The whole Phase 10 file again on the new bundle: `p10-final` **42/42**.
- **Vitest** `src/features/channels`: 16/16. The needs-him destination row keeps its BACKLOG row (no fence built: it needs the connection check's runner answering "needs him" in a hub).

## The counts

| Label | Product | Runs | Verdicts |
|---|---|---|---|
| `p10-merged` | this branch (main `dce3afa9` + the rig) | 42 (15 face × 2 widths + 12 op) | **42 pass** |
| `red-98ea2cfa` | pre-Phase-10 main | 42 | **0 pass**: 2 fail (`no_destination`: no SEND well), 23 blocked (`POST /api/channels/destinations` 404; the MCP save names no destination), 17 not run (the hub cannot install the recording runner: `No module named 'holdspeak.services.channel_cli'`) |
| `p789-merged` | this branch | 97 (atlas-phase7, -8, -9, -9-steward) | 95 pass, 2 blocked |
| `p789-dce3afa9` | main, its own rig | 97 | 95 pass, the SAME 2 blocked |
| `serial-merged` | this branch, one at a time | 6 | the 2 p8 cases pass at both widths (4/4); s5 1440 blocked |
| `base-merged` | this branch | 194 (atlas.json, atlas-phase3.json) | 109 pass, 78 blocked, 6 fail, 1 not applicable |
| `base-dce3afa9` | main, its own rig | 194 | 110 pass, 77 blocked, 6 fail, 1 not applicable |
| `s5-*-a1..a3` | s5 at 1440, serial | 3 + 3 | after 1 of 3 pass; before 0 of 3 |

Per file at both widths (`p10-merged`): every face case passes at 1440 AND at 393 (15/15 each); the 12 twins pass. The Phase 7, 8 and 9 files: 95/97 in the batch; the two blocked (`case.p8.zone_rename.list` 1440: the palette click timed out; `case.p8.delete_twice.both_gone` 1440: the undo window's guard did not hold at delivery — the Phase 8 law blocking correctly) ran under load 17–29, blocked identically before, and pass serially.

**Base atlas before/after:** `base_diff.py base-dce3afa9 base-merged` exits 1 on ONE row: `case.closure.chain.s5_next_day_brief_more_opened` 1440, pass → blocked. It is the inherited input-precondition defect already ledgered (BACKLOG "PHILO-9-05 follow-ups": the "N more" verb renders only for more than three brief items, which the case never makes). Six serial attempts: this branch 1 of 3, main 0 of 3 (`s5-*`). No rig addition touches that case (no runner, no count, no scroll). **p789 before/after: 0 pass → not-pass.**

## Equivalence (face vs `.op`)

`equivalence.py` reads the retained `p10-merged` observations: for each of the 10 pairs, both widths and the twin pass, and the durable outcome the face's own press answered equals the twin's (outcome or refusal code, send state and reason, channel, receipt state and actor, gh creates), and the stored rows the face read equal the twin's durable read. 10 pairs, 0 not equal (capture below). Examples: `failed` — `failed`, `github_target_not_found`, receipt `failed`, actor owner, one create, at 1440, 393 and over MCP; `destinations_listed` — the same two active rows (file, github); `several` — two sent rows.

## The census (every criterion of stories 01–04, the charter's exits and the matrix)

Key: **ATLAS** = an atlas case (this story's `atlas-phase10.json` unless named); **GLASS** = `tests/e2e/...::test`; **BACKEND** = `tests/unit/...::test`; **EXCLUDED** = not an atlas case, with the reason. A glass or backend fence is not atlas coverage. File keys: SC `tests/unit/test_philo10_send_contract.py`, SR `test_philo10_send_recovery.py`, RS `test_philo10_send_restart.py`, CLI `test_philo10_cli_channels.py`, EM `test_philo10_email_channel.py`, RIG `test_philo10_rig_op.py`, P9M `test_philo9_mark_delivered.py` (all `tests/unit/`); GF `tests/e2e/test_philo10_04_send_face_glass.py`, G01 `tests/e2e/test_philo10_01_unknown_send_face.py`, G02 `tests/e2e/test_philo10_02_nudge_unknown_glass.py`, G9 `tests/e2e/test_philo9_03_room_face_glass.py`. Every name was checked by a grep for its `def` line.

### Story 01: the Send contract, saved destinations and the file channel

| # | Criterion | Disposition |
|---|---|---|
| 1 | Operations declared once; HTTP, MCP, the rig's `op` | BACKEND SC::test_the_operations_are_declared_once_and_reach_one_service_over_http_and_mcp, SC::test_http_and_mcp_reach_the_same_rows, RIG::test_the_rig_reaches_the_send_and_reads_each_receipt. ATLAS every `.op` twin (the rig's op step) |
| 2 | One operation, one terminal receipt per admitted row | BACKEND SC::test_each_admitted_row_is_one_operation_with_one_terminal_receipt. ATLAS `sent.op`, `prepared.op`, `destinations_listed.op` |
| 2a | Each refusal class leaves its receipt | BACKEND SC::test_each_refusal_class_leaves_its_receipt_and_sends_nothing. ATLAS `refused(.op)`, `destination_changed(.op)`, `discard_after_send(.op)`, `send_after_discard.op` |
| 2b | Reads and previews leave no receipt | BACKEND SC::test_reads_and_previews_leave_no_operation. ATLAS `destination_picked` (the preview writes no send) |
| 2c | A mutation turns each red | EXCLUDED: story 01's `assets/story-01-proof/` mutation record, not a case |
| 3 | Two sends, two files, with proof; suffix and exclusive create | BACKEND SC::test_two_sends_of_one_update_to_one_folder_make_two_files_with_their_proof, SC::test_the_suffix_and_exclusive_create_never_write_over_an_old_file. ATLAS `several(.op)` |
| 3a | sha256 read back equals the preview's digest | BACKEND SC::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes. ATLAS `sent.op` (`sends.0.proof.sha256` = the preview digest) |
| 3b | A name that leaves the folder is refused | BACKEND SC::test_a_name_that_leaves_the_folder_is_refused. EXCLUDED: the name comes from the title the renderer owns; no atlas route makes it |
| 4 | Crash rule: one dispatch, UNKNOWN | BACKEND SR::test_r1_a_failed_settle_is_taken_over_without_a_second_dispatch_and_the_replay_answers_it, SR::test_r2_r5_the_reaper_settles_a_silent_send_and_the_replay_answers_it, RS::test_r3_a_restart_during_dispatching_ends_unknown_once_and_the_replay_answers_it. ATLAS `unknown_after_restart` |
| 4a | An OS error off the pinned list, a failed read-back: UNKNOWN | BACKEND SC::test_an_error_off_the_pinned_list_and_bytes_that_do_not_read_back_are_unknown |
| 4b | The same key again: no second effect | BACKEND SR::test_the_same_key_again_makes_no_second_effect. ATLAS `replay_same_key.op` |
| 5 | R1–R6, both forms | BACKEND SR::test_r1_…, SR::test_r2_r5_…, RS::test_r3_…, SR::test_r4_the_reaper_and_a_take_over_race_and_one_wins, SR::test_r4_a_take_over_that_wins_leaves_the_reaper_nothing, SR::test_r6_a_send_reaped_before_its_boundary_dispatches_nothing_and_writes_no_history. EXCLUDED from the atlas: a reaper and a failed settle need an in-process seam the rig's hub does not carry |
| 5a | Mutations turn them red | EXCLUDED: story 01's mutation record |
| 6 | No body in a row, receipt, journal, log or error | BACKEND SC::test_the_body_never_reaches_a_kernel_row_a_receipt_the_journal_a_log_or_an_error |
| 6a | The redactor | BACKEND SC::test_an_excerpt_of_the_payload_and_a_secret_are_redacted, SC::test_an_error_is_redacted_and_cut |
| 6b | Payload file 0600 in 0700, digest checked | BACKEND SC::test_the_private_payload_file_is_0600_in_0700_and_its_digest_is_checked, SC::test_a_changed_payload_is_refused_before_any_effect |
| 6c | Oversize refused by name | BACKEND SC::test_an_oversize_payload_is_refused_by_name |
| 7 | Destination changed or parked after prepare: refused before dispatch | BACKEND SC::test_a_destination_whose_target_changed_after_prepare_is_refused, SC::test_edit_parks_the_old_row_and_a_send_prepared_to_it_is_refused_with_the_historical_target. ATLAS `destination_changed(.op)`, `refused(.op)` |
| 7a | Remove before the boundary wins; after, the send stands | BACKEND SC::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched, SC::test_a_remove_after_the_boundary_parks_and_the_send_stands |
| 7b | The historical target kept; Remove parks | BACKEND SC::test_remove_parks_and_keeps_history, SC::test_edit_parks_… |
| 8 | UNKNOWN never counted delivered, at 1440 and 393 | GLASS G01::TestUnknownSendFace::test_an_unknown_send_is_never_shown_as_delivered. ATLAS `unknown`, `unknown_after_restart` (RESULT UNKNOWN in the history) |
| 9 | An agent's send refused `owner_principal_required` | BACKEND SC::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required. EXCLUDED (`excluded.p10.agent_side`): the rig speaks with the owner's token only |
| 9a | An agent's prepare under its own identity; survives a restart | BACKEND SC::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner, RS::test_r3_…. EXCLUDED (`excluded.p10.agent_side`) |
| 9b | Send and Discard together: one wins | BACKEND SC::test_send_and_discard_pressed_together_settle_once, SC::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands. ATLAS `discard_after_send(.op)`, `send_after_discard.op` (sequential; true concurrency is the backend fence) |
| 10 | Manual rows read `channel: manual` | BACKEND SC::test_manual_rows_read_channel_manual, SC::test_an_existing_database_gains_the_columns_and_its_rows_read_manual. ATLAS `atlas-phase9.json` `case.p9.update.delivered_row(.op)` (pass in `p789-merged`) |
| 10a | Mark delivered unchanged | BACKEND P9M (all). ATLAS `case.p9.update.delivered_row.op` |

### Story 02: the GitHub and Atlassian channels

| # | Criterion | Disposition |
|---|---|---|
| G1 | The redactor's cost bounded; the named code survives | BACKEND CLI::test_gate1_the_redactors_worst_case_is_bounded, CLI::test_gate1_a_document_with_the_clis_error_phrase_keeps_the_named_code |
| G2 | The hub answers during a slow dispatch | BACKEND CLI::test_gate2_the_hub_answers_a_read_during_a_slow_send, CLI::test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub. ATLAS `sending` (the well reads SENDING and the hub's row while the create is held) |
| 1 | One `channel.send`; CLI children parented (F5) | BACKEND CLI::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner, CLI::test_f5_the_nudges_gh_child_is_parented_under_the_owner. ATLAS `github_posted(.op)` (the real plan through the kernel's child; the child's receipt is not read by the atlas) |
| 2 | The nudge: UNKNOWN never offered again (F4) | BACKEND CLI::test_f4_a_nudge_whose_gh_times_out_is_unknown_and_never_offered_again, CLI::test_a_nudge_whose_settle_fails_after_the_comment_never_posts_twice_and_the_reaper_says_unknown. GLASS G02::test_the_unknown_nudge_is_never_offered_again_1440, `_393`. EXCLUDED: the nudge is not the Send well |
| 3 | argv: the manifest prefix, no body; the file is the previewed bytes | BACKEND CLI::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes. The atlas's runner log keeps the body file's sha256 (retained) |
| 3a | A forbidden flag or a second key cannot be built | BACKEND CLI::test_a_plan_with_a_forbidden_flag_or_a_second_key_cannot_be_built |
| 4 | Atlassian inside the acli lock | BACKEND CLI::test_an_atlassian_send_runs_inside_the_acli_lock_and_a_second_waits. GLASS GF::TestSendChannelsGlass::test_a_held_acli_lock_is_refused_on_the_first_answer |
| 5 | GitHub saved as A, gh now B: refused | BACKEND CLI::test_a_github_destination_saved_as_a_is_refused_when_gh_is_b, CLI::test_a_status_that_names_another_account_never_creates. GLASS GF::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send. EXCLUDED: the runner's answers are fixed per script; the change of login mid-case is the glass's |
| 6 | The Confluence title in the digest, never in argv | BACKEND CLI::test_the_confluence_title_is_in_the_frozen_digest_and_never_in_argv_or_a_receipt |
| 7 | Pinned: FAILED; everything else: UNKNOWN | BACKEND CLI::test_only_a_pinned_error_is_failed_everything_else_unknown. ATLAS `failed(.op)` (the pinned "could not resolve to an issue" → `github_target_not_found`; the FIRST fence of that phrase, the census found none), `unknown(.op)` (an unpinned `HTTP 502` → `github_exit_1`) |
| 8 | No body in a subprocess receipt; the owner principal and the broker | BACKEND CLI::test_the_argv_has_…, CLI::test_each_send_is_one_channel_send_… |
| 9 | The steward prepares as its run's child; its send refused | BACKEND CLI::test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused, CLI::test_the_scheduled_steward_prepares_under_its_own_identity. EXCLUDED (`excluded.p10.agent_side`) |
| 10 | One real send per channel | EXCLUDED: story 06's leg B |

### Story 03: the email channel

| # | Criterion | Disposition |
|---|---|---|
| 1, 1a, 1b | One egress child; the wire bytes are the frozen ones; another host refused | BACKEND EM::test_c1_one_send_is_one_egress_child_whose_wire_bytes_and_digest_are_the_frozen_ones, EM::test_c1_two_different_bodies_are_two_different_admitted_digests, EM::test_c1_a_request_to_any_other_host_is_refused_by_the_kernel |
| 2, 2a | 202 + id SENT; the pinned 4xx FAILED; else UNKNOWN; R1–R6 | BACKEND EM::test_c2_each_answer_settles_by_the_pinned_list, EM::test_c2_the_two_403_discriminators_map_apart, EM::test_r2_a_failure_is_failed_only_when_no_byte_was_written, EM::test_c2_r1_…, EM::test_c2_r2_…, EM::test_c2_r3_…, EM::test_c2_r4_…, EM::test_c2_r6_… |
| 2b | ACCEPTED BY SENDGRID on the face | GLASS GF::TestSendEmailGlass::test_the_email_boards. EXCLUDED from the atlas (`excluded.p10.other_channels`): the email edge and a memory keyring inside the hub are seams the rig's hub does not carry; SENT has its atlas case on file and GitHub |
| 3, 4 | No key or body in an exception, the journal, a receipt, a log, a file | BACKEND EM::test_c3_every_egress_caller_records_a_sanitized_exception, EM::test_c3_an_email_transport_exception_carrying_the_key_and_body_leaves_neither, EM::test_c4_no_key_and_no_body_in_the_journal_a_receipt_a_log_an_error_or_a_file, EM::test_c4_the_key_is_never_planning_material, EM::test_r2_global_http_debug_on_prints_no_key_and_no_body |
| 5 | Key custody: native only | BACKEND EM::test_c5_a_native_backend_stores_and_reads_the_key, EM::test_c5_every_other_backend_is_refused_not_native, EM::test_c5_a_store_that_is_not_native_refuses_the_save_and_the_send_before_anything_leaves. GLASS GF::TestSendEmailGlass::test_the_email_destination_setup |
| 6 | A second provider: one class, one row | BACKEND EM::test_c6_a_materially_different_provider_plugs_in_with_one_class_and_one_row (story 03's `captures.md:30` cites it as `test_c6_a_second_provider_…`, a wrong name; noted, not edited here) |
| 7 | A real SendGrid send | EXCLUDED: story 06's leg B |

### Story 04: the Send face and the destinations

| # | Criterion | Disposition |
|---|---|---|
| 1 | Canvases ratified before build | EXCLUDED: the owner's word, recorded 2026-09-29 |
| 2 | Every matrix state shot and fenced at 1440 and 393 | GLASS GF (all classes). ATLAS every face case (the matrix below) |
| 2a | The face equals the hub's record and receipt | GLASS GF reads the sends and the history beside the face (not the kernel receipt). ATLAS every face case reads the press's own receipt in the same observation; every twin reads `kernel.receipt.read` |
| 3 | Every verb the library Button | GLASS GF (`assert_clean`: no raw button). EXCLUDED: the rig has no DOM-species predicate |
| 3a | The host chip on each row that leaves the machine | GLASS GF::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state, GF::TestSendFaceGlass::test_the_destinations_group, GF::TestSendChannelsGlass::test_the_remote_destination_forms_save. ATLAS `destinations_listed` (THIS DEVICE, GITHUB.COM), `destination_picked` |
| 3b | No modal | GLASS GF (`assert_clean`). EXCLUDED: no modal predicate in the rig |
| 3c | Nothing covers Send at 393 | GLASS GF (the nine-point pointer pass). ATLAS every face case's `readable_text` owns nine hit points at 393 |
| 4 | Web baseline zero branch-new | EXCLUDED: `scripts/check_web_baseline.py --run`, story 04's evidence |

### The charter's exits

| # | Exit | Disposition |
|---|---|---|
| 1 | Discoverable and executable over MCP alone | BACKEND SC::test_the_words_map_his_asks_and_never_say_an_agent_sends, SC::test_the_operations_are_declared_once_…, RIG::test_the_rig_reaches_the_send_and_reads_each_receipt. ATLAS every `.op` twin |
| 2 | Admission by effect | BACKEND SC::test_each_admitted_row_…, SC::test_each_refusal_class_…, CLI::test_each_send_is_one_channel_send_…, CLI::test_f5_…, CLI::test_a_plan_with_a_forbidden_flag_or_a_second_key_cannot_be_built, SC::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required, SC::test_send_and_discard_pressed_together_settle_once. ATLAS `refused.op`, `destination_changed.op`, `discard_after_send.op`, `send_after_discard.op` |
| 3 | What is sent is what was previewed | BACKEND SC::test_the_preview_is_the_frozen_bytes_…, CLI::test_the_argv_has_…, EM::test_c1_one_send_…, SC::test_a_changed_payload_is_refused_before_any_effect, SC::test_the_body_never_reaches_…, SC::test_an_oversize_payload_is_refused_by_name, CLI::test_an_oversize_body_is_refused_by_name_before_any_dispatch, EM::test_a_request_over_the_size_limit_is_refused_by_name. ATLAS `sent.op` (the file's sha256 = the preview's digest) |
| 4 | Honest outcomes and the crash rule | BACKEND SR, RS::test_r3_…, CLI::test_only_a_pinned_error_…, CLI::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create, CLI::test_a_real_kill_during_a_gh_create_ends_unknown_once_and_the_replay_never_runs_gh_again, CLI::test_f4_…, EM::test_c2_*. ATLAS `sent`, `github_posted`, `failed`, `unknown` (+ twins), `unknown_after_restart`, `replay_same_key.op` |
| 5 | One real send per channel or a named limit | File: ATLAS `sent` (a real write on the isolated HOME). GitHub, Jira, Confluence, email: EXCLUDED, story 06's leg B |
| 6 | The face as ratified | GLASS GF. ATLAS the face cases |
| 7 | The atlas: each Send state at both widths, twins, the transitions; Phase 7, 8, 9 still pass | ATLAS this story (the counts and the transitions above); `p789-merged` + `serial-merged` |
| 8 | The closing use | EXCLUDED: story 06 |

### The state/width matrix

| State | Disposition |
|---|---|
| No destination saved | ATLAS `no_destination`. GLASS GF::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state |
| Destinations listed | ATLAS `destinations_listed(.op)` (two rows; a third, synced row does not fit 393 with the run's long HOME path — the SYNCED FOLDER chip and the account states CONNECTED / NEEDS HIM are GLASS GF::TestSendFaceGlass::test_the_destinations_group, GF::TestSendChannelsGlass::test_the_remote_destination_forms_save; the census found no board asserting a needs-him row: NO FENCE, reported) |
| Destination picked | ATLAS `destination_picked` |
| Sending | ATLAS `sending` |
| SENT | ATLAS `sent(.op)` (SAVED), `github_posted(.op)` (POSTED), `receipt_after_return`. Email's ACCEPTED BY SENDGRID, Jira COMMENTED, Confluence BLOG POSTED: GLASS (`excluded.p10.other_channels`) |
| REFUSED | ATLAS `refused(.op)` (DESTINATION PARKED, NOTHING SENT) |
| FAILED | ATLAS `failed(.op)`: FAILED · ISSUE NOT FOUND · NOTHING SENT (round two; the class fenced by `tests/unit/test_philo10_face_words.py`) |
| UNKNOWN | ATLAS `unknown(.op)` (Check acme/payments #42; the verb renders only for an UNKNOWN latest send) |
| UNKNOWN after a restart | ATLAS `unknown_after_restart` |
| DESTINATION CHANGED | ATLAS `destination_changed(.op)` |
| PREPARED | ATLAS `prepared(.op)` (BY YOU). By an agent: `excluded.p10.agent_side` |
| Manual | ATLAS `atlas-phase9.json` `case.p9.update.delivered_row(.op)` |
| Several sends | ATLAS `several(.op)` |

### Gaps and notes from the census

- **No fence found:** a destination row in the needs-him state (`owner_action_required`). Reported, BACKLOG row.
- **Face words:** the FAILED table missed seven service codes (the code showed in capitals). PAID in round two (above).
- **Seen in a run:** after another hand's send, the DELIVERY history of an open update stays without its row until the update opens again (the hub holds it). BACKLOG row (low).

## Laws kept (the Phase 8 and 9 lessons)

- A timed window is one gesture: Discard's ConfirmVerb is armed and confirmed in ONE trigger (`then`), fenced by `test_a_timed_window_is_one_gesture` (mutation m8).
- A guard sits at the event: the restart case checks `dispatching` on the hub (a `check` step) immediately before `restart_hub`.
- An optional step is never the outcome: the only optional step is the gate's Continue later (`test_no_trigger_is_optional_…`, m9).
- Wrapper statuses: `fences.sh` and `rig_phase.sh` read each command's own status (`${pipestatus[1]}`); `exit_combos.sh` proves all four combinations for each (capture below). `docs_nav.sh` counts every check.
- The copier keys by case × width × run and refuses reuse (4 fences + one per retained label; capture below).

## Proof

### Captured run — 2026-09-29T15:43:54Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 144929b66768e6ac93f9e2e0d8f4ed748f2776f5

```text
HEAD = dce3afa91ff636a3cb6c571343bc637fcac97034
........................................................................ [ 81%]
................................................................         [100%]
352 passed in 11.93s
baseline (unmutated): 54 passed in 0.62s
m1   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_case_reference_inside_the_atl', 'test_the_counts_over_every_atlas_file']
m2   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_face_cases_carry_both_ruled_viewpor', 'test_every_matrix_state_and_transition_has_its_case']
m3   RED    ['test_every_face_case_reads_its_hub_outcome_in_the_same_observation']
m4   RED    ['test_every_admitted_write_twin_reads_its_kernel_receipt_with_its_actor']
m5   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m6   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m7   RED    ['test_the_pairs_read_the_same_values']
m8   RED    ['test_a_timed_window_is_one_gesture']
m9   RED    ['test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m10  RED    ['test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m11  RED    ['test_the_counts_over_every_atlas_file', 'test_every_matrix_state_and_transition_has_its_case']
m12  RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_desk_face_case_crosses_the_ga']
m13  RED    ['test_every_api_step_exists_in_the_generated_openapi']
m14  RED    ['test_the_pairs_read_the_same_values']
14 mutations: 14 red, 0 missed
fences exit 0; mutations exit 0
```

### Captured run — 2026-09-29T15:44:28Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/exit_combos.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 144929b66768e6ac93f9e2e0d8f4ed748f2776f5

```text
fences.sh A=0 B=0 -> exit 0 (wanted 0): ok
fences.sh A=0 B=1 -> exit 1 (wanted nonzero): ok
fences.sh A=1 B=0 -> exit 1 (wanted nonzero): ok
fences.sh A=1 B=1 -> exit 1 (wanted nonzero): ok
rig_phase.sh A=0 B=0 -> exit 0 (wanted 0): ok
rig_phase.sh A=0 B=1 -> exit 1 (wanted nonzero): ok
rig_phase.sh A=1 B=0 -> exit 1 (wanted nonzero): ok
rig_phase.sh A=1 B=1 -> exit 1 (wanted nonzero): ok
0 wrong
```

### Captured run — 2026-09-29T15:44:28Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/equivalence.py p10-merged`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 144929b66768e6ac93f9e2e0d8f4ed748f2776f5

```text
EQUAL case.p10.send.destination_changed: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
EQUAL case.p10.send.destinations_listed: verdicts ['pass', 'pass', 'pass']
      1440: shared {'gh_creates': 0}
      393: shared {'gh_creates': 0}
      1440 rows: shared {'rows': [('destinations', 'file', 'active', None), ('destinations', 'github', 'active', None)]}
      393 rows: shared {'rows': [('destinations', 'file', 'active', None), ('destinations', 'github', 'active', None)]}
EQUAL case.p10.send.discard_after_send: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'send_already_settled', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'send_already_settled', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
EQUAL case.p10.send.failed: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'failed', 'send.state': 'failed', 'send.reason': 'github_target_not_found', 'channel': 'github', 'receipt.state': 'failed', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      393: shared {'outcome': 'failed', 'send.state': 'failed', 'send.reason': 'github_target_not_found', 'channel': 'github', 'receipt.state': 'failed', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      1440 rows: shared {'rows': [('sends', 'github', 'failed', 'owner')]}
      393 rows: shared {'rows': [('sends', 'github', 'failed', 'owner')]}
EQUAL case.p10.send.github_posted: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'github', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      393: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'github', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
EQUAL case.p10.send.prepared: verdicts ['pass', 'pass', 'pass']
      1440: shared {}
      393: shared {}
      1440 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
EQUAL case.p10.send.refused: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
EQUAL case.p10.send.sent: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
EQUAL case.p10.send.several: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'sent', 'owner'), ('sends', 'file', 'sent', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'sent', 'owner'), ('sends', 'file', 'sent', 'owner')]}
EQUAL case.p10.send.unknown: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'unknown', 'send.state': 'unknown', 'send.reason': 'github_exit_1', 'channel': 'github', 'receipt.state': 'indeterminate', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      393: shared {'outcome': 'unknown', 'send.state': 'unknown', 'send.reason': 'github_exit_1', 'channel': 'github', 'receipt.state': 'indeterminate', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
10 pairs; 0 not equal
```

### Captured run — 2026-09-29T15:44:29Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/base_diff.py p789-dce3afa9 p789-merged`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 144929b66768e6ac93f9e2e0d8f4ed748f2776f5

```text
   2  before blocked         after blocked
  95  before pass            after pass
97 runs; 0 pass before and not after
```

### Captured run — 2026-09-29T15:44:29Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/base_diff.py base-dce3afa9 base-merged`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 144929b66768e6ac93f9e2e0d8f4ed748f2776f5

```text
  77  before blocked         after blocked
   6  before fail            after fail
   1  before not_applicable  after not_applicable
   1  before pass            after blocked
 109  before pass            after pass
DIFF atlas-phase3.json case.closure.chain.s5_next_day_brief_more_opened 1440: pass -> blocked
     before: predicate: 'Keep summary retrieval on the local desk' in observe_at text
     after:  BLOCKED: ui step wait_for on '[data-testid=arrival-brief-more]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
194 runs; 1 pass before and not after
```

### Captured run — 2026-09-29T15:44:29Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 144929b66768e6ac93f9e2e0d8f4ed748f2776f5

```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
rc=0  python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
rc=0  python3 scripts/check_docs.py
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
rc=0  python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Repository census: 5 outputs verified.
rc=0  python3 scripts/philo_repository_census.py --check
API reference checked
rc=0  python3 scripts/philo_api_reference.py --check
Boundary candidate census checked
rc=0  python3 scripts/philo_boundary_census.py --check
Doctor reference: 41 check functions
rc=0  python3 scripts/philo_doctor_reference.py --check
Configuration declaration reference is current
rc=0  python3 scripts/philo_config_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
rc=0  python3 scripts/philo_graph_reference.py --check
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
rc=0  python3 scripts/validate_architecture.py
Architecture documentation checked (10 outputs).
rc=0  python3 scripts/generate_capability_docs.py --check
Documentation coverage checked.
rc=0  python3 scripts/check_doc_coverage.py --check
OpenAPI: 580 paths
rc=0  .venv/bin/python scripts/philo_openapi_reference.py --check
checks failed: 0
```

### Captured run — 2026-09-29T15:54:32Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 713493fdb0d0e4e731a5ef8eb3a6aec67021ce8a

```text
HEAD = 08276df1116ccfdbcb213c97496a3159c3e2483c
........................................................................ [ 98%]
....                                                                     [100%]
364 passed in 11.92s
baseline (unmutated): 57 passed in 0.64s
m1   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_case_reference_inside_the_atl', 'test_the_counts_over_every_atlas_file']
m2   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_face_cases_carry_both_ruled_viewpor', 'test_every_matrix_state_and_transition_has_its_case']
m3   RED    ['test_every_face_case_reads_its_hub_outcome_in_the_same_observation']
m4   RED    ['test_every_admitted_write_twin_reads_its_kernel_receipt_with_its_actor']
m5   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m6   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m7   RED    ['test_the_pairs_read_the_same_values']
m8   RED    ['test_a_timed_window_is_one_gesture']
m9   RED    ['test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m10  RED    ['test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m11  RED    ['test_the_counts_over_every_atlas_file', 'test_every_matrix_state_and_transition_has_its_case']
m12  RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_desk_face_case_crosses_the_ga']
m13  RED    ['test_every_api_step_exists_in_the_generated_openapi']
m14  RED    ['test_the_pairs_read_the_same_values']
14 mutations: 14 red, 0 missed
fences exit 0; mutations exit 0
```

### Captured run — 2026-09-29T15:55:00Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/face_words_mutations.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 713493fdb0d0e4e731a5ef8eb3a6aec67021ce8a

```text
9 passed in 0.45s
baseline exit 0
2 failed, 7 passed in 0.49s
m1 RED (a FAILED word dropped)
1 failed, 8 passed in 0.50s
m2 RED (a new refusal code with no word)
1 failed, 8 passed in 0.48s
m3 RED (a code through a new variable site)
3 mutations: 3 red, 0 missed
```

### Captured run — 2026-09-29T15:55:03Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/exit_combos.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 713493fdb0d0e4e731a5ef8eb3a6aec67021ce8a

```text
fences.sh A=0 B=0 -> exit 0 (wanted 0): ok
fences.sh A=0 B=1 -> exit 1 (wanted nonzero): ok
fences.sh A=1 B=0 -> exit 1 (wanted nonzero): ok
fences.sh A=1 B=1 -> exit 1 (wanted nonzero): ok
rig_phase.sh A=0 B=0 -> exit 0 (wanted 0): ok
rig_phase.sh A=0 B=1 -> exit 1 (wanted nonzero): ok
rig_phase.sh A=1 B=0 -> exit 1 (wanted nonzero): ok
rig_phase.sh A=1 B=1 -> exit 1 (wanted nonzero): ok
0 wrong
```

### Captured run — 2026-09-29T15:55:04Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 713493fdb0d0e4e731a5ef8eb3a6aec67021ce8a

```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
rc=0  python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
rc=0  python3 scripts/check_docs.py
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
rc=0  python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Repository census: 5 outputs verified.
rc=0  python3 scripts/philo_repository_census.py --check
API reference checked
rc=0  python3 scripts/philo_api_reference.py --check
Boundary candidate census checked
rc=0  python3 scripts/philo_boundary_census.py --check
Doctor reference: 41 check functions
rc=0  python3 scripts/philo_doctor_reference.py --check
Configuration declaration reference is current
rc=0  python3 scripts/philo_config_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
rc=0  python3 scripts/philo_graph_reference.py --check
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
rc=0  python3 scripts/validate_architecture.py
Architecture documentation checked (10 outputs).
rc=0  python3 scripts/generate_capability_docs.py --check
Documentation coverage checked.
rc=0  python3 scripts/check_doc_coverage.py --check
OpenAPI: 580 paths
rc=0  .venv/bin/python scripts/philo_openapi_reference.py --check
checks failed: 0
```

### Captured run — 2026-09-29T15:55:22Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/equivalence.py p10-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 713493fdb0d0e4e731a5ef8eb3a6aec67021ce8a

```text
EQUAL case.p10.send.destination_changed: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
EQUAL case.p10.send.destinations_listed: verdicts ['pass', 'pass', 'pass']
      1440: shared {'gh_creates': 0}
      393: shared {'gh_creates': 0}
      1440 rows: shared {'rows': [('destinations', 'file', 'active', None), ('destinations', 'github', 'active', None)]}
      393 rows: shared {'rows': [('destinations', 'file', 'active', None), ('destinations', 'github', 'active', None)]}
EQUAL case.p10.send.discard_after_send: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'send_already_settled', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'send_already_settled', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
EQUAL case.p10.send.failed: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'failed', 'send.state': 'failed', 'send.reason': 'github_target_not_found', 'channel': 'github', 'receipt.state': 'failed', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      393: shared {'outcome': 'failed', 'send.state': 'failed', 'send.reason': 'github_target_not_found', 'channel': 'github', 'receipt.state': 'failed', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      1440 rows: shared {'rows': [('sends', 'github', 'failed', 'owner')]}
      393 rows: shared {'rows': [('sends', 'github', 'failed', 'owner')]}
EQUAL case.p10.send.github_posted: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'github', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      393: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'github', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
EQUAL case.p10.send.prepared: verdicts ['pass', 'pass', 'pass']
      1440: shared {}
      393: shared {}
      1440 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'prepared', 'owner')]}
EQUAL case.p10.send.refused: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'destination_parked', 'receipt.state': 'refused', 'receipt.actor_kind': 'owner'}
EQUAL case.p10.send.sent: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'sent', 'owner')]}
EQUAL case.p10.send.several: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      393: shared {'outcome': 'sent', 'send.state': 'sent', 'channel': 'file', 'receipt.state': 'succeeded', 'receipt.actor_kind': 'owner'}
      1440 rows: shared {'rows': [('sends', 'file', 'sent', 'owner'), ('sends', 'file', 'sent', 'owner')]}
      393 rows: shared {'rows': [('sends', 'file', 'sent', 'owner'), ('sends', 'file', 'sent', 'owner')]}
EQUAL case.p10.send.unknown: verdicts ['pass', 'pass', 'pass']
      1440: shared {'outcome': 'unknown', 'send.state': 'unknown', 'send.reason': 'github_exit_1', 'channel': 'github', 'receipt.state': 'indeterminate', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
      393: shared {'outcome': 'unknown', 'send.state': 'unknown', 'send.reason': 'github_exit_1', 'channel': 'github', 'receipt.state': 'indeterminate', 'receipt.actor_kind': 'owner', 'gh_creates': 1}
10 pairs; 0 not equal
```

### Captured run — 2026-09-29T15:55:23Z

- **Command:** `.venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 713493fdb0d0e4e731a5ef8eb3a6aec67021ce8a

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2966 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T16:13:25Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ccc225deab6918e4d9c8b8a9626c8e6092e1d8d

```text
HEAD = 813e668433af24d6b5ac934afff59a640b82670a
........................................................................ [ 98%]
.....                                                                    [100%]
365 passed in 13.57s
baseline (unmutated): 57 passed in 0.72s
m1   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_case_reference_inside_the_atl', 'test_the_counts_over_every_atlas_file']
m2   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_face_cases_carry_both_ruled_viewpor', 'test_every_matrix_state_and_transition_has_its_case']
m3   RED    ['test_every_face_case_reads_its_hub_outcome_in_the_same_observation']
m4   RED    ['test_every_admitted_write_twin_reads_its_kernel_receipt_with_its_actor']
m5   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m6   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m7   RED    ['test_the_pairs_read_the_same_values']
m8   RED    ['test_a_timed_window_is_one_gesture']
m9   RED    ['test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m10  RED    ['test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m11  RED    ['test_the_counts_over_every_atlas_file', 'test_every_matrix_state_and_transition_has_its_case']
m12  RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_desk_face_case_crosses_the_ga']
m13  RED    ['test_every_api_step_exists_in_the_generated_openapi']
m14  RED    ['test_the_pairs_read_the_same_values']
14 mutations: 14 red, 0 missed
fences exit 0; mutations exit 0
```

### Captured run — 2026-09-29T16:13:57Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/face_words_mutations.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ccc225deab6918e4d9c8b8a9626c8e6092e1d8d

```text
10 passed in 0.56s
baseline exit 0
2 failed, 8 passed in 0.56s
m1 RED (a FAILED word dropped)
1 failed, 9 passed in 0.57s
m2 RED (a new refusal code with no word)
1 failed, 9 passed in 0.57s
m3 RED (a code through a new variable site)
1 failed, 9 passed in 0.55s
m4 RED (an f-string code outside the allow-list)
1 failed, 9 passed in 0.61s
m5 RED (a .format() code)
1 failed, 9 passed in 0.59s
m6 RED (a formatted code through the reason flow)
6 mutations: 6 red, 0 missed
```

### Captured run — 2026-09-29T16:14:04Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/exit_combos.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ccc225deab6918e4d9c8b8a9626c8e6092e1d8d

```text
fences.sh A=0 B=0 -> exit 0 (wanted 0): ok
fences.sh A=0 B=1 -> exit 1 (wanted nonzero): ok
fences.sh A=1 B=0 -> exit 1 (wanted nonzero): ok
fences.sh A=1 B=1 -> exit 1 (wanted nonzero): ok
rig_phase.sh [tree] BUILD=0 RIG=0 RETAIN=0 -> exit 0, ran: rig retain (wanted 0): ok
rig_phase.sh [tree] BUILD=0 RIG=0 RETAIN=1 -> exit 1, ran: rig retain (wanted nonzero): ok
rig_phase.sh [tree] BUILD=0 RIG=1 RETAIN=0 -> exit 1, ran: rig retain (wanted nonzero): ok
rig_phase.sh [tree] BUILD=0 RIG=1 RETAIN=1 -> exit 1, ran: rig retain (wanted nonzero): ok
rig_phase.sh [tree] BUILD=7 RIG=0 RETAIN=0 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [tree] BUILD=7 RIG=0 RETAIN=1 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [tree] BUILD=7 RIG=1 RETAIN=0 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [tree] BUILD=7 RIG=1 RETAIN=1 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [export] BUILD=0 RIG=0 RETAIN=0 -> exit 0, ran: rig retain (wanted 0): ok
rig_phase.sh [export] BUILD=0 RIG=0 RETAIN=1 -> exit 1, ran: rig retain (wanted nonzero): ok
rig_phase.sh [export] BUILD=0 RIG=1 RETAIN=0 -> exit 1, ran: rig retain (wanted nonzero): ok
rig_phase.sh [export] BUILD=0 RIG=1 RETAIN=1 -> exit 1, ran: rig retain (wanted nonzero): ok
rig_phase.sh [export] BUILD=7 RIG=0 RETAIN=0 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [export] BUILD=7 RIG=0 RETAIN=1 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [export] BUILD=7 RIG=1 RETAIN=0 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
rig_phase.sh [export] BUILD=7 RIG=1 RETAIN=1 -> exit 3, ran: nothing (wanted nonzero, nothing ran): ok
before (813e6684) [tree] BUILD=7 -> exit 0, ran: rig retain (the defect: shown, not counted)
0 wrong
```

### Captured run — 2026-09-29T17:01:26Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright .venv/bin/python -m pytest -q -p no:cacheprovider -n 4 --basetemp=$H/pt tests/unit/test_evidence_scratch_guard.py tests/unit/test_philo8_atlas.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo9_atlas.py tests/unit/test_philo5_rehearsal_capture.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo9_04_atlas.py tests/unit/test_philo10_atlas.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo7_rig_faithful.py tests/unit/test_philo5_codex_seams.py tests/unit/test_philo3_summary_rig.py tests/unit/test_philo7_atlas.py tests/unit/test_philo9_02_rig_op.py tests/unit/test_philo10_rig_op.py tests/unit/test_philo5_pairs.py tests/unit/test_philo9_rig_op.py tests/unit/test_graph_walk_calibration.py  2>&1 | tail -2; rc=${pipestatus[1]}; rm -rf $H; exit $rc`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0d7f64cc7277ffa7599e6382fdd8a5327640ceb

```text
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
500 passed, 3 warnings in 104.42s (0:01:44)
```

### Captured run — 2026-09-29T17:03:11Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0d7f64cc7277ffa7599e6382fdd8a5327640ceb

```text
HEAD = 67cbd84b3cd62dd0901e7c8348bf75971d9925a7
........................................................................ [ 98%]
.....                                                                    [100%]
365 passed in 11.90s
baseline (unmutated): 57 passed in 0.65s
m1   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_case_reference_inside_the_atl', 'test_the_counts_over_every_atlas_file']
m2   RED    ['test_the_general_fences_hold_for_the_phase10_file[test_face_cases_carry_both_ruled_viewpor', 'test_every_matrix_state_and_transition_has_its_case']
m3   RED    ['test_every_face_case_reads_its_hub_outcome_in_the_same_observation']
m4   RED    ['test_every_admitted_write_twin_reads_its_kernel_receipt_with_its_actor']
m5   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m6   RED    ['test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send']
m7   RED    ['test_the_pairs_read_the_same_values']
m8   RED    ['test_a_timed_window_is_one_gesture']
m9   RED    ['test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m10  RED    ['test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m11  RED    ['test_the_counts_over_every_atlas_file', 'test_every_matrix_state_and_transition_has_its_case']
m12  RED    ['test_the_general_fences_hold_for_the_phase10_file[test_every_desk_face_case_crosses_the_ga']
m13  RED    ['test_every_api_step_exists_in_the_generated_openapi']
m14  RED    ['test_the_pairs_read_the_same_values']
14 mutations: 14 red, 0 missed
fences exit 0; mutations exit 0
```
