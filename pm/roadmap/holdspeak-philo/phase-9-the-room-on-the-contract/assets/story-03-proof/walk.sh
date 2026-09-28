#!/bin/zsh
# The walk of the Chair's two proposal Open verbs (isolated hub, both widths).
cd ${0:A:h}/../../../../../..
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -s -p no:cacheprovider \
  pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/walk_chair_proposals.py 2>&1 \
  | grep -o -E "WALK .*|[0-9]+ (passed|failed).*" | cut -c1-600
