# Pinned baseline failure check

Baseline commit: `675401a857b85336d4acaa8c65383dfc9636e4c8`  
Baseline worktree: `.tmp/philo/baseline` (detached worktree)  
Full-suite input: `.tmp/philo/full-suite.xml` (`19` failures, `115` skips,
`11271` collected tests).

The full-suite failures split into five documentation/Mermaid failures owned by
the documentation or integration lanes and fourteen runtime failures. This
report covers only those fourteen runtime tests. No metal test or full suite was
run here. The clone's `/Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python`
was used with a fresh `HOME` for each command. The baseline imports check was:

```text
holdspeak.__file__ = .tmp/philo/baseline/holdspeak/__init__.py
HEAD = 675401a857b85336d4acaa8c65383dfc9636e4c8
```

## Results

Focused runtime result: **10 passed, 4 failed**.

### Passed

1. The eight Phase 200 attention tests passed together (`8 passed in 1.97s`):

   ```text
   RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_changed_item_with_the_same_count_notifies \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_restart_renotifies_nothing \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_escalation_fires_through_the_sweep_and_says_so \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_counsel_probe_2b_archived_project_ids_leave_the_settings \
     tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_the_policy_row_is_written_only_when_the_set_or_outcome_changed
   ```

   Evidence: `.tmp/philo/baseline-attention.log`. The full suite had reported
   these same eight as `held_quiet_hours` instead of `sent`; the isolated
   bounded rerun did not reproduce that result.

2. The real kernel hub cursor/restart test passed (`1 passed in 4.78s`):

   ```text
   RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay
   ```

   Evidence: `.tmp/philo/baseline-kernel-realhub.log`.

3. The remote Settings 393px test passed after building the pinned baseline
   Web bundle (`1 passed in 8.12s`):

   ```text
   source ../env.sh; RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q 'tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[393]'
   ```

   Evidence: `.tmp/philo/baseline-remote-settings-393-rerun.log`. The first
   attempt was an environment setup error (`vite: command not found`) because
   the detached worktree had no `web/node_modules`. I linked the clone's
   existing `web/node_modules` under the `.tmp` worktree and ran
   `npm --prefix web run build`; the built static bundle stayed inside the
   detached worktree. The first error is preserved in
   `.tmp/philo/baseline-remote-settings-393.log`.

### Failed

1. **Scheduled recipe loop:**

   ```text
   RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q tests/integration/test_phase200_recipe_catalog.py::TestTheScheduledOwnerReallyFires::test_the_sweep_is_driven_by_a_wall_clock_loop
   ```

   Result: `1 failed in 0.52s`. At
   `tests/integration/test_phase200_recipe_catalog.py:652`, the bytecode
   constant scan found no integer tick `>= 10` in
   `HeartbeatMixin._heartbeat_loop.__code__.co_consts`. The failure is
   preserved in `.tmp/philo/baseline-scheduled-recipe.log`.

2. **Practice guardrail glass:**

   ```text
   source ../env.sh; RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused
   ```

   Result: `1 failed in 13.49s`. At 1440px,
   `data-default-decision` was `allow`; the test requires `deny` at
   `tests/e2e/test_hs153_practice_glass.py:578`. Evidence:
   `.tmp/philo/baseline-hs153-guardrail.log`.

3. **Command Deck PROJECTS glass, 1440px:**

   ```text
   source ../env.sh; RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_projects_1440
   ```

   Result: `1 failed in 4.89s`. The Gamma room has zero needs-you items but
   still renders one `.desk-deck-badge`; the test requires zero at
   `tests/e2e/test_hs171_command_deck_glass.py:281`. Evidence:
   `.tmp/philo/baseline-hs171-1440.log`.

4. **Command Deck PROJECTS glass, 393px:**

   ```text
   source ../env.sh; RUN_HOME=$(mktemp -d); HOME="$RUN_HOME" /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python -m pytest -q tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_projects_393
   ```

   Result: `1 failed in 4.89s`, with the same Gamma zero-item badge failure
   at `tests/e2e/test_hs171_command_deck_glass.py:281`. Evidence:
   `.tmp/philo/baseline-hs171-393.log`.

## Unresolved baseline status

The fourteen runtime rows do not form a clean baseline: four remain red in
isolated execution. The eight attention failures from the full-suite XML
passed when run alone under fresh homes, so their full-suite `held_quiet_hours`
result is an unresolved ordering or shared-state discrepancy rather than a
confirmed pinned-source defect. The scheduled recipe bytecode assertion,
guardrail default, and zero-item PROJECTS badge failures reproduce directly.

No source or product file was edited. The detached worktree contains only
test-generated static assets/screenshots and the temporary dependency link
needed to run the glass tests; all evidence logs are under `.tmp/philo/`.
