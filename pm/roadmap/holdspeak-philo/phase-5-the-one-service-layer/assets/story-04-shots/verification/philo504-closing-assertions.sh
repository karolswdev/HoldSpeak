#!/bin/zsh
set -eu
set -o pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
verification=../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification
cd web
scoped=(src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx)
env HOME=$(mktemp -d) npx vitest list $scoped > "$verification/closing-assertions-collect.txt"
env HOME=$(mktemp -d) npx vitest run --maxWorkers=2 $scoped | tee "$verification/closing-assertions-tests.txt"
