#!/bin/zsh
# PRESERVATION: the existing Room, update, steward, arrival and shade glass the
# story's faces touch, on the branch (isolated HOME, parallel).
# PHILO-9 close (Codex Astra r1 on #689 finding 3): the exit status is pytest's
# (pipestatus), not cut's; proof: preserve_exit_combos.sh.
cd ${0:A:h}/../../../../../..
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 \
  tests/e2e/test_hs158_room_glass.py tests/e2e/test_hs160_delta_glass.py tests/e2e/test_hs161_github_glass.py \
  tests/e2e/test_hs162_update_glass.py tests/e2e/test_hs163_steward_glass.py tests/e2e/test_hs164_unattended_glass.py \
  tests/e2e/test_hs168_window_wings_glass.py tests/e2e/test_hs169_room_glass.py tests/e2e/test_hs170_arrival_glass.py \
  tests/e2e/test_hs171_shade_glass.py tests/e2e/test_hs171_rhythm_glass.py \
  tests/e2e/test_hs173_update_glass.py tests/e2e/test_hs173_health_glass.py tests/e2e/test_hs173_policy_glass.py \
  tests/e2e/test_hs174_receipts_glass.py tests/e2e/test_hs200_claim_support_glass.py tests/e2e/test_hs200_task_resume_glass.py \
  tests/e2e/test_hs200_coverage_glass.py tests/e2e/test_hs200_attention_glass.py tests/e2e/test_hs200_meeting_outcomes_glass.py \
  tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs200_continuity_glass.py 2>&1 \
  | grep -E "^(FAILED|ERROR)|passed|failed" | cut -c1-300
rc=${pipestatus[1]}
exit $rc
