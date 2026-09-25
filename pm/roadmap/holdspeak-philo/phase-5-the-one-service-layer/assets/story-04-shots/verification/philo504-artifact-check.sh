#!/bin/zsh
set -eu
set -o pipefail
verification=pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification
python3 "$verification/verify-final-rehearsal.py"
cat "$verification/final-rehearsal-audit.txt"
