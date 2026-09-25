#!/bin/zsh
set -eu
set -o pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
verification=../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification
cd web
scoped=(src/desk/chair/__tests__/briefReceiptRendered202.test.tsx src/desk/chair/__tests__/briefFreshRead.philo504.test.tsx src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx)
env HOME=$(mktemp -d) npx vitest list $scoped > "$verification/receipt-final-collect.txt"
env HOME=$(mktemp -d) npx vitest run --maxWorkers=2 $scoped | tee "$verification/receipt-final-tests.txt"
