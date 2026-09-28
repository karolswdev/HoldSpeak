#!/bin/zsh
# PHILO-9-07 glass: the face fences at 1440x900 and 393x852 on the real hub
# (isolated HOME, the branch's own built bundle), the shots written to
# assets/story-07-shots (HOLDSPEAK_EVIDENCE_WRITE=1). Serial: a hub per test.
cd ${0:A:h}/../../../../../..
HOME=$(mktemp -d) HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -p no:cacheprovider -rf \
  tests/e2e/test_philo9_07_project_grant_glass.py 2>&1 | tail -3
ls pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-shots
