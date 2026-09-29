# Evidence - PHILO-10-04

- **Story:** PHILO-10-04 - The Send face and the destinations setup (canvas first)
- **Status:** done
- **Date:** 2026-09-29

## Proof

### Captured run — 2026-09-29T07:41:41Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -rA 2>&1 | grep -E "^(PASSED|FAILED|ERROR) |passed|failed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c18fd6053023f545f65aa0cabb87d763a064bb48

```text
__ TestSendFaceGlass.test_a_known_failure_outlives_a_failed_sends_read[1440] ___
___ TestSendFaceGlass.test_a_known_failure_outlives_a_failed_sends_read[393] ___
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_known_failure_outlives_a_failed_sends_read[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_known_failure_outlives_a_failed_sends_read[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_the_remote_destination_forms_save[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_the_remote_destination_forms_save[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_boards[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::test_board_25_unknown_after_a_real_restart[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_boards[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::test_board_25_unknown_after_a_real_restart[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_destination_setup[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_destination_setup[1440]
22 passed in 129.56s (0:02:09)
```

### Captured run — 2026-09-29T07:43:51Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_01_unknown_send_face.py tests/e2e/test_philo9_03_room_face_glass.py tests/e2e/test_philo10_02_nudge_unknown_glass.py tests/e2e/test_hs173_policy_glass.py tests/e2e/test_hs173_health_glass.py tests/e2e/test_philo9_b1_connections_glass.py tests/e2e/test_hs170_settings_hub_glass.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_rig_op.py tests/unit/test_philo10_cli_channels.py tests/unit/test_philo10_email_channel.py tests/unit/test_philo10_04_atlassian_sign_in.py tests/unit/test_philo10_settings_atomic.py tests/unit/test_694_thread_never_sends.py tests/unit/test_api_surface.py tests/unit/test_philo5_one_decision.py "tests/unit/test_db.py::TestDatabaseShape" 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c18fd6053023f545f65aa0cabb87d763a064bb48

```text
...........................................................              [100%]
275 passed in 150.51s (0:02:30)
```

### Captured run — 2026-09-29T07:46:28Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H npm_config_cache=/Users/karol/.npm .venv/bin/python scripts/check_web_baseline.py --run 2>&1 | grep -A3 "BRANCH-NEW\|Suite totals"; cd web && npm run tokens:check 2>&1 | tail -1 && npm run tokens:gate 2>&1 | tail -1 && npm run guard:architecture 2>&1 | tail -1 && npx tsc --noEmit -p . && echo typecheck-clean`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c18fd6053023f545f65aa0cabb87d763a064bb48

```text
Suite totals: 2966 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (865 source files; zero framework residue).
typecheck-clean
```

### Captured run — 2026-09-29T07:47:17Z

- **Command:** `bash -c set -e; P=.venv/bin/python; python3 -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -1; $P scripts/check_docs.py; $P scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md; $P scripts/philo_repository_census.py --check; $P scripts/philo_api_reference.py --check; $P scripts/philo_boundary_census.py --check; $P scripts/philo_doctor_reference.py --check; $P scripts/philo_config_reference.py --check; $P scripts/philo_graph_reference.py --check 2>&1 | tail -1; $P scripts/validate_architecture.py; $P scripts/generate_capability_docs.py --check; $P scripts/check_doc_coverage.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** c18fd6053023f545f65aa0cabb87d763a064bb48

```text
OK
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference drift: docs/generated/api-reference.json
```

### Captured run — 2026-09-29T07:47:38Z

- **Command:** `bash -c set -e; P=.venv/bin/python; python3 -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -1; $P scripts/check_docs.py; $P scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md; $P scripts/philo_repository_census.py --check; $P scripts/philo_api_reference.py --check; $P scripts/philo_boundary_census.py --check; $P scripts/philo_doctor_reference.py --check; $P scripts/philo_config_reference.py --check; $P scripts/philo_graph_reference.py --check 2>&1 | tail -1; $P scripts/validate_architecture.py; $P scripts/generate_capability_docs.py --check; $P scripts/check_doc_coverage.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c18fd6053023f545f65aa0cabb87d763a064bb48

```text
OK
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference checked
Boundary candidate census checked
Doctor reference: 41 check functions
Configuration declaration reference is current
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
Architecture documentation checked (10 outputs).
Documentation coverage checked.
```

### Captured run — 2026-09-29T08:16:44Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -k "held_acli_lock or email_destination_setup" -rf 2>&1 | grep -E "^(FAILED|E   )|passed|failed" | cut -c1-260 | head -20`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d590ee4d75646aa0f983d12259e07378e21cd969

```text
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-open][data-destination='Jira PAY-121'] [data-testid=send-refused]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-open][data-destination='Jira PAY-121'] [data-testid=send-refused]") to be visible
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 20000ms exceeded.
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 20000ms exceeded.
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_a_held_acli_lock_is_refused_on_the_first_answer[393]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_a_held_acli_lock_is_refused_on_the_first_answer[1440]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_destination_setup[1440]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass::test_the_email_destination_setup[393]
4 failed in 36.99s
```

### Captured run — 2026-09-29T08:17:44Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_cli_channels.py tests/unit/test_philo10_email_channel.py tests/unit/test_philo10_04_atlassian_sign_in.py tests/unit/test_api_surface.py tests/unit/test_philo5_one_decision.py "tests/unit/test_db.py::TestDatabaseShape" 2>&1 | tail -2 && cd web && npx vitest run src/features/channels src/features/project-room 2>&1 | grep -E "Test Files|Tests |Errors"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d590ee4d75646aa0f983d12259e07378e21cd969

```text
.............                                                            [100%]
229 passed in 401.99s (0:06:41)
 Test Files  25 passed (25)
      Tests  465 passed (465)
```

### Captured run — 2026-09-29T08:24:40Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H npm_config_cache=/Users/karol/.npm .venv/bin/python scripts/check_web_baseline.py --run 2>&1 | grep -A3 "BRANCH-NEW\|Suite totals"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d590ee4d75646aa0f983d12259e07378e21cd969

```text
Suite totals: 2966 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T08:25:21Z

- **Command:** `bash -c set -e; P=.venv/bin/python; python3 -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -1; $P scripts/check_docs.py; $P scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md; $P scripts/philo_repository_census.py --check; $P scripts/philo_api_reference.py --check; $P scripts/philo_boundary_census.py --check; $P scripts/philo_doctor_reference.py --check; $P scripts/philo_config_reference.py --check; $P scripts/philo_graph_reference.py --check 2>&1 | tail -1; $P scripts/validate_architecture.py; $P scripts/generate_capability_docs.py --check; $P scripts/check_doc_coverage.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d590ee4d75646aa0f983d12259e07378e21cd969

```text
OK
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference checked
Boundary candidate census checked
Doctor reference: 41 check functions
Configuration declaration reference is current
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
Architecture documentation checked (10 outputs).
Documentation coverage checked.
```
