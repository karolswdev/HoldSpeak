#!/bin/zsh
# The one preservation red: test_hs171_rhythm_glass::test_mute_toggle, on the
# BASE's product files (swap.sh base) -- it fails the same way there (its seed
# posts `title` to /api/projects, refused by project.create's schema), so it is
# inherited, not this story's.
cd ${0:A:h}/../../../../../..
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/swap.sh base
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider tests/e2e/test_hs171_rhythm_glass.py -k mute_toggle 2>&1 \
  | grep -E "^E .*HTTP|passed|failed" | cut -c1-240
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/swap.sh branch
