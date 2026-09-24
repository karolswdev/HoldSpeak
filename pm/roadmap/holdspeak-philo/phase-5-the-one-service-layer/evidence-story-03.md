# Evidence - PHILO-5-03

- **Story:** PHILO-5-03 - The atlas proves the three paths
- **Status:** done
- **Date:** 2026-09-24

## Proof

The [lane report](story-03-lane-report.md) maps all seven boxes to the [20 paired comparisons](assets/story-03-shots/pairs.json), [33 browser observations](assets/story-03-shots/faces.json), [all 62 runs](assets/story-03-shots/runs.json), and scoped validation. Tests: 219 passed in 113.35 seconds, capture 2026-09-24T22:51:43Z. Rig fences: 21:51:35Z. Actual pair mutations: 22:55:40Z. Pair index and graph check: 22:55:42Z.

### Captured run — 2026-09-24T21:06:23Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s1_import_complete --brain astra --viewport 393 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:62672 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ehquttkg/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T210623Z-case.closure.chain.s1_import_complete-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T210623Z-case.closure.chain.s1_import_complete-astra-393/after.png']
NOTE: placeholder(s) ['meeting_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /meetings/0/id equals the declared value
```

### Captured run — 2026-09-24T21:07:29Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s2_summary_with_host --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:62754 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kxlvbhgu/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T210729Z-case.closure.chain.s2_summary_with_host-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T210729Z-case.closure.chain.s2_summary_with_host-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T210729Z-case.closure.chain.s2_summary_with_host-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: '192.168.1.43' in observe_at text
```

### Captured run — 2026-09-24T21:17:31Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.j11.thought_keep.receipt_time --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:63824 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1sd91n5y/.local/share/holdspeak/holdspeak.db engine=none
JOB: j11
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T211731Z-case.j11.thought_keep.receipt_time-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T211731Z-case.j11.thought_keep.receipt_time-astra-1440/after.png']
NOTE: predicate: 'KEPT ·' in observe_at text
```

### Captured run — 2026-09-24T21:29:12Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s2_summary_with_host --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:65105 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-fj8_kzo0/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T212912Z-case.closure.chain.s2_summary_with_host-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T212912Z-case.closure.chain.s2_summary_with_host-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T212912Z-case.closure.chain.s2_summary_with_host-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: '192.168.1.43' in observe_at text
```

### Captured run — 2026-09-24T21:31:20Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s3_same_summary_after_restart --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:65525 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rhjf1cea/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213120Z-case.closure.chain.s3_same_summary_after_restart-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213120Z-case.closure.chain.s3_same_summary_after_restart-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213120Z-case.closure.chain.s3_same_summary_after_restart-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The team decided to use SQ for the local meeting ledger, keep summary retrieval on the local desk after hub restarts, and use recorded provider replies for isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, and Leo Martinez will test restart retrieval on Tuesday.', wanted 'The team decided to use SQ for the local meeting ledger, keep summary retrieval on the local desk after hub restarts, and use recorded provider replies for isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, and Leo Martinez will test restart retrieval on Tuesday.'
```

### Captured run — 2026-09-24T21:32:45Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s3_same_summary_after_restart --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:49278 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-cdowqp0n/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213245Z-case.closure.chain.s3_same_summary_after_restart-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213245Z-case.closure.chain.s3_same_summary_after_restart-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213245Z-case.closure.chain.s3_same_summary_after_restart-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval procedures, and isolated rig tests. Action items were assigned to Mayyachan for the migration plan by Friday and Leo Martinez for testing restart retrieval by Tuesday.', wanted 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval procedures, and isolated rig tests. Action items were assigned to Mayyachan for the migration plan by Friday and Leo Martinez for testing restart retrieval by Tuesday.'
```

### Captured run — 2026-09-24T21:34:41Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s4_decision_recorded --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:49558 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-8rno7bz6/.local/share/holdspeak/holdspeak.db engine=real
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213441Z-case.closure.chain.s4_decision_recorded-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213441Z-case.closure.chain.s4_decision_recorded-astra-1440/after.png']
NOTE: predicate: /decisions/0/title equals the declared value
```

### Captured run — 2026-09-24T21:35:55Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s4_decision_recorded --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:49701 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5il7pi4k/.local/share/holdspeak/holdspeak.db engine=real
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213555Z-case.closure.chain.s4_decision_recorded-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T213555Z-case.closure.chain.s4_decision_recorded-astra-393/after.png']
NOTE: predicate: /decisions/0/title equals the declared value
```

### Captured run — 2026-09-24T21:38:30Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a1.decision_face_create.opens_and_reopens --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:49996 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-r8mnlhbr/.local/share/holdspeak/holdspeak.db engine=none
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T213830Z-case.a1.decision_face_create.opens_and_reopens-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T213830Z-case.a1.decision_face_create.opens_and_reopens-astra-1440/after.png']
NOTE: predicate: POST /api/decisions answered 400, wanted 400 (body sha256 75a37ad65fa2); response body contains the declared admission facts
```

### Captured run — 2026-09-24T21:41:48Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a1.decision_face_create.opens_and_reopens --brain astra --viewport 393 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:50193 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-wlkgmm_5/.local/share/holdspeak/holdspeak.db engine=none
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T214148Z-case.a1.decision_face_create.opens_and_reopens-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T214148Z-case.a1.decision_face_create.opens_and_reopens-astra-393/after.png']
NOTE: predicate: POST /api/decisions answered 400, wanted 400 (body sha256 75a37ad65fa2); response body contains the declared admission facts
```

### Captured run — 2026-09-24T21:43:28Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s1_import_complete.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:50301 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5binfdtx/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['meeting_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: transcription_status equals the declared value
```

### Captured run — 2026-09-24T21:44:40Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s2_summary_with_host.op --brain astra --viewport 1440 --engine real --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:50371 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-tfenvoum/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: intel.summary is non-empty
```

### Captured run — 2026-09-24T21:45:29Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s3_same_summary_after_restart.op --brain astra --viewport 1440 --engine real --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:50451 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-z7bl7t1m/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: intel.summary is non-empty
```

### Captured run — 2026-09-24T21:48:18Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s4_decision_recorded.op --brain astra --viewport 1440 --engine real --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:50646 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5rsu7jqr/.local/share/holdspeak/holdspeak.db engine=real
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: title equals the declared value
```

### Captured run — 2026-09-24T21:51:35Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/fences/verify_fences.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
RED op removed: calibration CAL-op-success BLOCKED; trigger not dispatched
GREEN calibration CAL-op-success ('pass', 'settled')
GREEN calibration CAL-op-unresolved ('blocked', '-')
GREEN calibration CAL-op-refusal ('pass', 'settled')
GREEN calibration CAL-op-never-completes ('fail', 'incomplete')
GREEN calibration CAL-op-headless-face-block ('blocked', 'settled')
GREEN calibration CAL-op-restart-retains-read ('pass', 'settled')
RED base snapshot: AttributeError 'NoneType' object has no attribute 'evaluate'
GREEN headless snapshot: real producer decision ID read back without a page
RED canonical projection rename: ('decision.create', 'desk.renamed', ['desk.create[kind=decisions]', 'desk.verb[verb_id=desk.create,kind=decisions]'])
GREEN canonical projections match live descriptors
RED real Thought resource decoder: capture_as 'aggregate_revision': no value at 'thought.aggregate_revision' in the decoded response of operation 'thought.read'
GREEN real Thought resource: typed revisions, cursor, save and readback
RED actual atlas restart flag omitted: summary_retained restart retention flags missing or false: ['summary_retained']
RED actual atlas restart flag omitted: receipt_retained restart retention flags missing or false: ['receipt_retained']
RED actual atlas restart flag omitted: meeting_identity_retained restart retention flags missing or false: ['meeting_identity_retained']
GREEN actual atlas restart retains all three relationships: 20260924T214529Z-case.closure.chain.s3_same_summary_after_restart.op-astra-1440
ALL REQUIRED RIG FENCE RESULTS VERIFIED
```

### Captured run — 2026-09-24T21:52:23Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s4_decision_recorded.op --brain astra --viewport 1440 --engine real --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:50978 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-j5y13mo2/.local/share/holdspeak/holdspeak.db engine=real
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: title equals the declared value
```

### Captured run — 2026-09-24T21:53:49Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a1.decision_face_create.opens_and_reopens.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51075 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1rr4w8yw/.local/share/holdspeak/holdspeak.db engine=none
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: operation refused by name 'mcp_refused': invalid decision status: bogus
```

### Captured run — 2026-09-24T21:56:06Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a3.brief_next_day.decision_on_the_face --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51159 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-gakw1izv/.local/share/holdspeak/holdspeak.db engine=none
JOB: a3
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T215606Z-case.a3.brief_next_day.decision_on_the_face-astra-1440/blocked.png']
NOTE: BLOCKED: unresolved placeholder(s) ['decision_id'] in the case's `expected`: no setup step and not the trigger captures them (`capture_as`), so the trigger was NOT fired
```

### Captured run — 2026-09-24T21:59:56Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a3.brief_next_day.decision_on_the_face --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51292 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-69vmsqxx/.local/share/holdspeak/holdspeak.db engine=none
JOB: a3
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T215956Z-case.a3.brief_next_day.decision_on_the_face-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T215956Z-case.a3.brief_next_day.decision_on_the_face-astra-1440/after.png']
NOTE: predicate: 'Review decision: Graph walk next-day decision A3' in observe_at text
```

### Captured run — 2026-09-24T22:01:56Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a3.brief_next_day.decision_on_the_face --brain astra --viewport 393 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51366 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-wl7pzd2p/.local/share/holdspeak/holdspeak.db engine=none
JOB: a3
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T220156Z-case.a3.brief_next_day.decision_on_the_face-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T220156Z-case.a3.brief_next_day.decision_on_the_face-astra-393/after.png']
NOTE: predicate: 'Review decision: Graph walk next-day decision A3' in observe_at text
```

### Captured run — 2026-09-24T22:04:05Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a3.brief_next_day.decision_on_the_face.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51445 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-yzlajqxi/.local/share/holdspeak/holdspeak.db engine=none
JOB: a3
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: sections.decisions is non-empty
```

### Captured run — 2026-09-24T22:06:21Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a3.brief_next_day.new_id_with_the_decision --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51516 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5ig4hr8e/.local/share/holdspeak/holdspeak.db engine=none
JOB: a3
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T220621Z-case.a3.brief_next_day.new_id_with_the_decision-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T220621Z-case.a3.brief_next_day.new_id_with_the_decision-astra-1440/after.png']
NOTE: predicate: POST /api/brief/generate answered 200, wanted 200 (body sha256 02ffc999f4ff); 'brief-dedc480a17264ffea10a22268fcee26e' not in the response body; response body contains the declared admission facts
```

### Captured run — 2026-09-24T22:11:30Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.a3.brief_next_day.new_id_with_the_decision.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51673 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-w6be8xmx/.local/share/holdspeak/holdspeak.db engine=none
JOB: a3
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: sections.decisions is non-empty
```

### Captured run — 2026-09-24T22:12:18Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51726 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-nrfd0qm_/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T221218Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T221218Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T22:13:24Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51833 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-b_0yt2pt/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T221324Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T221324Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 356, 'w': 369, 'h': 114}
```

### Captured run — 2026-09-24T22:14:18Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it.op --brain astra --viewport 1440 --engine real --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:51936 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-60ph2pc5/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: sections.decisions is non-empty
```

### Captured run — 2026-09-24T22:14:50Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_with_breakage --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52049 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-_12lew7_/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T221450Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T221450Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

**Scope correction — unselected run:** The 22:14:50Z run passes only its decision-row face predicate. It does not prove repeated breakage: `advance_days=0 now=2026-09-24T16:15:12` and `advance_days=1 now=2026-09-25T16:15:14` put the failure before the new window start17:00. The required existing wrapper precondition was missed. Retained unchanged; the equivalence index must block this attempt. See `checks/story-03-breakage-window-muaddib.md`.

### Captured run — 2026-09-24T22:16:28Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.j11.thought_keep.receipt_time --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52205 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-s8y4i7kp/.local/share/holdspeak/holdspeak.db engine=none
JOB: j11
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T221628Z-case.j11.thought_keep.receipt_time-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T221628Z-case.j11.thought_keep.receipt_time-astra-1440/after.png']
NOTE: predicate: 'KEPT ·' in observe_at text
```

### Captured run — 2026-09-24T22:17:24Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.j11.thought_keep.receipt_time --brain astra --viewport 393 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52260 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-8sh5p49p/.local/share/holdspeak/holdspeak.db engine=none
JOB: j11
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T221724Z-case.j11.thought_keep.receipt_time-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T221724Z-case.j11.thought_keep.receipt_time-astra-393/after.png']
NOTE: predicate: 'KEPT ·' in observe_at text
```

### Captured run — 2026-09-24T22:18:14Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.j11.thought_keep.receipt_time.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52316 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sqqe7hxr/.local/share/holdspeak/holdspeak.db engine=none
JOB: j11
VERDICT: blocked terminal=None
EVIDENCE: []
NOTE: BLOCKED: capture_as 'thought_id': no value at 'thought.id' in the decoded response of operation 'thought.create'
```

### Captured run — 2026-09-24T22:19:03Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.j11.thought_keep.receipt_time.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52358 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-m1ci1rhq/.local/share/holdspeak/holdspeak.db engine=none
JOB: j11
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: thought.working_note.last_modified is non-empty
```

### Captured run — 2026-09-24T22:19:50Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.j11.thought_keep.receipt_time.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52428 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1b9civvy/.local/share/holdspeak/holdspeak.db engine=none
JOB: j11
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: thought.working_note.body_markdown equals the declared value
```

### Captured run — 2026-09-24T22:20:24Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52464 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-fv9o3xmp/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222024Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222024Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/after.png']
NOTE: predicate: 'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}
```

### Captured run — 2026-09-24T22:21:06Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled --brain astra --viewport 393 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52508 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-nmmhhvsx/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222106Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222106Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/after.png']
NOTE: predicate: 'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}
```

### Captured run — 2026-09-24T22:22:28Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52577 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-fz7929d3/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: /brief-item-cc295e6c2e844b17befb9267c5cfe970 equals the declared value
```

### Captured run — 2026-09-24T22:22:58Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.route_intelligence_run.refusal --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52620 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-vn7uj5m_/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440/after.png']
NOTE: predicate: POST /api/meetings/750e137f/intelligence/run answered 409, wanted 409 (body sha256 fa2ae8cac82e); response body contains the declared admission facts
```

### Captured run — 2026-09-24T22:23:52Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.route_intelligence_run.refusal.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52708 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-b5dqj0rp/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: operation refused by name 'empty': Meeting has no transcript
```

### Captured run — 2026-09-24T22:24:25Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.route_intelligence_run.no_assignment --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52764 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-akw_u645/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222425Z-case.j6.route_intelligence_run.no_assignment-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222425Z-case.j6.route_intelligence_run.no_assignment-astra-1440/after.png']
NOTE: predicate: POST /api/meetings/be0918fd/intelligence/run answered 409, wanted 409 (body sha256 1aaad71a4fba); response body contains the declared admission facts
```

### Captured run — 2026-09-24T22:25:07Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.route_intelligence_run.no_assignment.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:52849 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1k2loo1y/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: fail terminal=settled
EVIDENCE: []
NOTE: predicate: refusal error 'The summary route is not available.' does not contain ['route_unavailable']
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['op_digest', 'op_reads']).
```

### Captured run — 2026-09-24T22:26:21Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.route_intelligence_run.no_assignment.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:53089 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-7tg6iwab/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: operation refused by name 'route_unavailable': The summary route is not available.
```

### Captured run — 2026-09-24T22:26:49Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/philo5_breakage_walk.py --case case.closure.chain.s5_next_day_brief_with_breakage --viewport 1440 --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
BREAKAGE_WINDOW TZ=Etc/GMT+2 local=2026-09-24T20:26:49.444329 after_close=True
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:53128 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-0qnvx1bc/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T222649Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T222649Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T22:27:45Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/philo5_breakage_walk.py --case case.closure.chain.s5_next_day_brief_with_breakage --viewport 393 --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
BREAKAGE_WINDOW TZ=Etc/GMT+2 local=2026-09-24T20:27:45.385340 after_close=True
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:53237 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kt881qh6/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T222745Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/browser/20260924T222745Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 356, 'w': 369, 'h': 114}
```

### Captured run — 2026-09-24T22:28:57Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/philo5_breakage_walk.py --case case.closure.chain.s5_next_day_brief_with_breakage.op --viewport 1440 --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
BREAKAGE_WINDOW TZ=Etc/GMT+2 local=2026-09-24T20:28:57.761096 after_close=True
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:53339 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-9imjkpwv/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: blocked terminal=None
EVIDENCE: []
NOTE: BLOCKED: precondition not met: {'kind': 'op_field', 'path': 'sections.broke.0.text', 'value': 'DecisionLifecycleService.get_decision failed'} at {'kind': 'op', 'name': 'brief.latest', 'args': {}} — sections.broke.0.text = 'PrimitiveService.get_decision failed', wanted 'DecisionLifecycleService.get_decision failed'
```

### Captured run — 2026-09-24T22:30:16Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/philo5_breakage_walk.py --case case.closure.chain.s5_next_day_brief_with_breakage.op --viewport 1440 --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
BREAKAGE_WINDOW TZ=Etc/GMT+2 local=2026-09-24T20:30:16.150132 after_close=True
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:53478 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-nw4eg15q/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: blocked terminal=None
EVIDENCE: []
NOTE: BLOCKED: capture_as 'old_breakage_id': capture_match at 'sections.broke' matched 0 rows; exactly one is required
```

### Captured run — 2026-09-24T22:31:47Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.arrival_generate_again.same_day_idempotent --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:53605 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-z9xd3y0j/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T223147Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T223147Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440/after.png']
NOTE: predicate: unchanged result; the returned identity 'No changes' (headline='No changes') IS the one displayed at '[data-testid=arrival-brief-headline]' (response chosen by the declared trigger_route POST /api/brief/generate)
```

## Breakage setup scope — checked amendment

Counsel: checks/story-03-breakage-source-muaddib.md. The headless sibling replaces its missing decision op setup with the same real HTTP 404 seed as the browser. HTTP GET on a missing id invokes the registry and falls through to the legacy lifecycle service at holdspeak/web/routes/decisions.py:58-61; MCP decision.read has only the primitive failure. Both paths now receive the same two-event input for the brief retention comparison. This pair does not establish missing-decision refusal parity. The mismatch is inherited compatibility projection debt assigned to PHILO-5-04; no product change is included. Runs 222857Z and 223016Z remain unselected and unchanged.

### Captured run — 2026-09-24T22:37:11Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.arrival_generate_again.same_day_idempotent --brain astra --viewport 393 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:54252 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-co2tj4o3/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T223711Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T223711Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393/after.png']
NOTE: predicate: unchanged result; the returned identity 'No changes' (headline='No changes') IS the one displayed at '[data-testid=arrival-brief-headline]' (response chosen by the declared trigger_route POST /api/brief/generate)
```

### Captured run — 2026-09-24T22:40:42Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.arrival_generate_again.same_day_idempotent.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:54972 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-psr2jq7g/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: id equals the declared value
```

### Captured run — 2026-09-24T22:41:25Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/philo5_breakage_walk.py --case case.closure.chain.s5_next_day_brief_with_breakage.op --viewport 1440 --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/real/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
BREAKAGE_WINDOW TZ=Etc/GMT+2 local=2026-09-24T20:41:25.368697 after_close=True
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55028 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-o1vrbeyv/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: sections.decisions is non-empty
```

### Captured run — 2026-09-24T22:42:33Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.route_generate_again.same_day_same_id --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55146 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-l4rfogi4/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224233Z-case.j10.route_generate_again.same_day_same_id-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224233Z-case.j10.route_generate_again.same_day_same_id-astra-1440/after.png']
NOTE: predicate: POST /api/brief/generate answered 200, wanted 200 (body sha256 5975842a88cd); response body contains the declared admission facts
```

### Captured run — 2026-09-24T22:43:08Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.route_generate_again.same_day_same_id.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55197 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-4m9_eeyw/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: id equals the declared value
```

### Captured run — 2026-09-24T22:43:24Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.brief_item_shelf.acknowledged --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55220 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sel2m6vk/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224324Z-case.j10.brief_item_shelf.acknowledged-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224324Z-case.j10.brief_item_shelf.acknowledged-astra-1440/after.png']
NOTE: predicate: /brief-item-a6a3383d245e409b9ca9373171c5a860 equals the declared value
```

### Captured run — 2026-09-24T22:44:02Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.brief_item_shelf.acknowledged.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55264 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-cikwsng3/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: /brief-item-1b239ebd766a44dd8547735aa6b4aff3 equals the declared value
```

### Captured run — 2026-09-24T22:44:25Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.brief_item_shelf.deferred --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55288 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-b1_i7po2/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224425Z-case.j10.brief_item_shelf.deferred-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224425Z-case.j10.brief_item_shelf.deferred-astra-1440/after.png']
NOTE: predicate: /brief-item-613cd0e96f3b4ed49d80c1708558fa03 equals the declared value
```

### Captured run — 2026-09-24T22:45:00Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.brief_item_shelf.deferred.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55360 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-j6n1he46/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: /brief-item-efe69b89c72c4e54a4eafd094008f335 equals the declared value
```

### Captured run — 2026-09-24T22:45:19Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.brief_item_shelf.refused --brain astra --viewport 1440 --engine none --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55393 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ca4t05ad/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224519Z-case.j10.brief_item_shelf.refused-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224519Z-case.j10.brief_item_shelf.refused-astra-1440/after.png']
NOTE: predicate: POST /api/brief/items/brief-item-80b07d918bce40f4b93d783fd455f514/shelf answered 422, wanted 422 (body sha256 963e3b1fb869); response body contains the declared admission facts
```

### Captured run — 2026-09-24T22:46:04Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j10.brief_item_shelf.refused.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55445 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-q4vff2bi/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: operation refused by name 'mcp_refused': Invalid arguments for monday_brief.shelf: state: 'shelved' is not one of ['acknowledged', 'deferred', None]
```

### Captured run — 2026-09-24T22:46:20Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s2_summary_with_host.replayed --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55472 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-j89y4p96/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224620Z-case.closure.chain.s2_summary_with_host.replayed-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224620Z-case.closure.chain.s2_summary_with_host.replayed-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224620Z-case.closure.chain.s2_summary_with_host.replayed-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: '192.168.1.43' in observe_at text
```

### Captured run — 2026-09-24T22:47:20Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s2_summary_with_host.replayed --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55556 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zuj_yd3h/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224720Z-case.closure.chain.s2_summary_with_host.replayed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224720Z-case.closure.chain.s2_summary_with_host.replayed-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224720Z-case.closure.chain.s2_summary_with_host.replayed-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: '192.168.1.43' in observe_at text
```

### Captured run — 2026-09-24T22:48:12Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s2_summary_with_host.op.replayed --brain astra --viewport 1440 --engine replayed --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55633 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-p0nhert0/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: intel.summary is non-empty
```

### Captured run — 2026-09-24T22:48:32Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s3_same_summary_after_restart.replayed --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55681 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zcb2im90/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224832Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224832Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224832Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval after hub restarts, and isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, while Leo Martinez will test restart retrieval on Tuesday.', wanted 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval after hub restarts, and isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, while Leo Martinez will test restart retrieval on Tuesday.'
```

### Captured run — 2026-09-24T22:49:17Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s3_same_summary_after_restart.replayed --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55767 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-2pp2623y/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224917Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224917Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/browser/20260924T224917Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval after hub restarts, and isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, while Leo Martinez will test restart retrieval on Tuesday.', wanted 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval after hub restarts, and isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, while Leo Martinez will test restart retrieval on Tuesday.'
```

### Captured run — 2026-09-24T22:50:09Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s3_same_summary_after_restart.op.replayed --brain astra --viewport 1440 --engine replayed --headless --no-build --out pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/replayed/op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
PASS: live
BRAIN: astra
SOURCE: c4d464985c25b296906608f0b256960d229c786c dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:55875 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-xu6fyjtw/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: intel.summary is non-empty
```

### Captured run — 2026-09-24T22:51:43Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HF_HOME=/Users/karol/dev/tools/wt-philo-5-03/.tmp/philo5-03-env/huggingface HF_HUB_OFFLINE=1 HOLDSPEAK_EVIDENCE_WRITE=1 uv run --extra dev --extra test pytest -q tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_pairs.py tests/unit/test_graph_walk_calibration.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_philo5_codex_seams.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_reference.py | tee pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/verification/scoped-tests.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
........................................................................ [ 32%]
........................................................................ [ 65%]
........................................................................ [ 98%]
...                                                                      [100%]
219 passed in 113.35s (0:01:53)
```

### Captured run — 2026-09-24T22:55:40Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) uv run --extra dev --extra test python pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/fences/verify_pair_fences.py | tee pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/verification/pair-fences.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
RED actual decision.read one-field title skew: FAIL [["decision.title", "fail", "decision.title differs"]]
GREEN actual decision pair: PASS []
RED actual S4 old false restart flags: BLOCKED [["restart.op.summary_retained", "fail", "restart summary_retained is absent or false"], ["restart.op.receipt_retained", "fail", "restart receipt_retained is absent or false"], ["restart.op.meeting_identity_retained", "fail", "restart meeting_identity_retained is absent or false"], ["restart.op.meeting_id", "blocked", "required projection restart.op.meeting_id is absent"]]
RED actual breakage before-close clock: BLOCKED producer clock first reading is outside the 17:00–23:00 breakage window
GREEN actual wrapped breakage clock: PASS producer clock first reading overlaps the 17:00–23:00 breakage window
RED actual old incomplete breakage pair: BLOCKED [["op.brief_identity", "fail", "first and final brief ids are equal"], ["op.decision_identity", "blocked", "op.decision_identity needs 2 producer/read stages"], ["created_at_present", "blocked", "created_at is required in producer and read stages"], ["op.decision_durable", "blocked", "named decision create/read slots are required"], ["op.old_brief_shelf_unchanged", "blocked", "breakage case lacks before/after brief DB snapshots"], ["op.final_brief_shelf_empty", "blocked", "final generated brief shelf is absent or nonempty"], ["op.old_shelf_ack_scope", "blocked", "old brief shelf is absent, empty, unscoped, or has no acknowledged item"], ["op.breakage_scoped_ids", "blocked", "breakage ids lack source mapping, collide, escape the final brief, or reuse the old id"], ["next_day.decision_projection", "blocked", "both transports need the user-authored decision projection"], ["next_day.breakage_causes", "blocked", "both transports need complete final broke text/detail rows"]]
RED next_day.breakage_causes (retained day-one op setup vs browser final; diagnostic only): FAIL {"name": "next_day.breakage_causes", "status": "fail", "detail": "next_day.breakage_causes differs", "op": [{"text": "PrimitiveService.get_decision failed", "detail": "not_found: NotFound('Unknown decision: philo402-deliberately-absent')"}], "browser": [{"text": "DecisionLifecycleService.get_decision failed", "detail": "not_found: NotFound('Unknown decision: philo402-deliberately-absent')"}, {"text": "PrimitiveService.get_decision failed", "detail": "not_found: NotFound('Unknown decision: philo402-deliberately-absent')"}]}
GREEN actual normalized breakage pair: PASS []
RED actual shelf refusal changed brief: FAIL [["refusal.brief_unchanged", "fail", "refusal.brief_unchanged differs"]]
GREEN actual refused empty shelf with unchanged brief: PASS []
RED missing named durable refusal reads: BLOCKED [["durable_unchanged", "blocked", "shelf refusal has no before and after shelf reads"], ["refusal.durable_projection", "blocked", "required projection refusal.durable_projection is absent"]]
RED actual summary receipt route identity: FAIL [["op.receipt_selection_identity", "fail", "op.receipt_selection_identity differs"]]
GREEN actual summary receipt route identity: PASS []
RED actual first Thought run did not change body: FAIL [["op.body_changed_on_save", "fail", "saved body was unchanged from the before read"]]
GREEN actual Thought saved-body transition: PASS []
GREEN all 18 named pairs plus 2 replay pairs: 20 PASS; original observations unchanged
```

### Captured run — 2026-09-24T22:55:42Z

- **Command:** `zsh -c set -e; set -o pipefail; HOME=$(mktemp -d) uv run --extra dev --extra test python pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/verification/verify_pairs.py | tee pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/verification/pairs-run.txt
HOME=$(mktemp -d) uv run python scripts/philo_graph_reference.py --check | tee pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/verification/graph-check.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7de3c3cfad239cf4da1c077b01d91424dc5a0d6

```text
case.closure.chain.s1_import_complete 20260924T210414Z-case.closure.chain.s1_import_complete-astra-1440 20260924T214328Z-case.closure.chain.s1_import_complete.op-astra-1440 PASS 3.481s
case.closure.chain.s2_summary_with_host 20260924T210729Z-case.closure.chain.s2_summary_with_host-astra-1440 20260924T214440Z-case.closure.chain.s2_summary_with_host.op-astra-1440 PASS 10.453s
case.closure.chain.s2_summary_with_host.replayed 20260924T224620Z-case.closure.chain.s2_summary_with_host.replayed-astra-1440 20260924T224812Z-case.closure.chain.s2_summary_with_host.op.replayed-astra-1440 PASS 4.909s
case.closure.chain.s3_same_summary_after_restart 20260924T213120Z-case.closure.chain.s3_same_summary_after_restart-astra-1440 20260924T214529Z-case.closure.chain.s3_same_summary_after_restart.op-astra-1440 PASS 12.745s
case.closure.chain.s3_same_summary_after_restart.replayed 20260924T224832Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-1440 20260924T225009Z-case.closure.chain.s3_same_summary_after_restart.op.replayed-astra-1440 PASS 7.062s
case.closure.chain.s4_decision_recorded 20260924T213441Z-case.closure.chain.s4_decision_recorded-astra-1440 20260924T215223Z-case.closure.chain.s4_decision_recorded.op-astra-1440 PASS 13.628s
case.a1.decision_face_create.opens_and_reopens 20260924T213830Z-case.a1.decision_face_create.opens_and_reopens-astra-1440 20260924T215349Z-case.a1.decision_face_create.opens_and_reopens.op-astra-1440 PASS 2.635s
case.a3.brief_next_day.decision_on_the_face 20260924T215956Z-case.a3.brief_next_day.decision_on_the_face-astra-1440 20260924T220405Z-case.a3.brief_next_day.decision_on_the_face.op-astra-1440 PASS 2.737s
case.a3.brief_next_day.new_id_with_the_decision 20260924T220621Z-case.a3.brief_next_day.new_id_with_the_decision-astra-1440 20260924T221130Z-case.a3.brief_next_day.new_id_with_the_decision.op-astra-1440 PASS 2.732s
case.closure.chain.s5_next_day_brief_has_it 20260924T221218Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440 20260924T221418Z-case.closure.chain.s5_next_day_brief_has_it.op-astra-1440 PASS 12.211s
case.closure.chain.s5_next_day_brief_with_breakage 20260924T222649Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440 20260924T224125Z-case.closure.chain.s5_next_day_brief_with_breakage.op-astra-1440 PASS 12.179s
case.philo404.arrival_triaged_headline.all_handled 20260924T222024Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440 20260924T222228Z-case.philo404.arrival_triaged_headline.all_handled.op-astra-1440 PASS 2.709s
case.j11.thought_keep.receipt_time 20260924T221628Z-case.j11.thought_keep.receipt_time-astra-1440 20260924T221950Z-case.j11.thought_keep.receipt_time.op-astra-1440 PASS 2.647s
case.j6.route_intelligence_run.refusal 20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440 20260924T222352Z-case.j6.route_intelligence_run.refusal.op-astra-1440 PASS 2.984s
case.j6.route_intelligence_run.no_assignment 20260924T222425Z-case.j6.route_intelligence_run.no_assignment-astra-1440 20260924T222621Z-case.j6.route_intelligence_run.no_assignment.op-astra-1440 PASS 4.859s
case.j10.arrival_generate_again.same_day_idempotent 20260924T223147Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440 20260924T224043Z-case.j10.arrival_generate_again.same_day_idempotent.op-astra-1440 PASS 2.714s
case.j10.route_generate_again.same_day_same_id 20260924T224233Z-case.j10.route_generate_again.same_day_same_id-astra-1440 20260924T224308Z-case.j10.route_generate_again.same_day_same_id.op-astra-1440 PASS 2.667s
case.j10.brief_item_shelf.acknowledged 20260924T224324Z-case.j10.brief_item_shelf.acknowledged-astra-1440 20260924T224402Z-case.j10.brief_item_shelf.acknowledged.op-astra-1440 PASS 2.693s
case.j10.brief_item_shelf.deferred 20260924T224425Z-case.j10.brief_item_shelf.deferred-astra-1440 20260924T224500Z-case.j10.brief_item_shelf.deferred.op-astra-1440 PASS 2.675s
case.j10.brief_item_shelf.refused 20260924T224519Z-case.j10.brief_item_shelf.refused-astra-1440 20260924T224604Z-case.j10.brief_item_shelf.refused.op-astra-1440 PASS 2.668s
PAIRS {'total': 20, 'pass': 20, 'fail': 0, 'blocked': 0}
BROWSER OBSERVATIONS 33 FACE CLAIMS REMAIN BROWSER-ONLY
ATLAS docs/internal/philo/graph/atlas.json cases 81 op siblings 7 replays 0
ATLAS docs/internal/philo/graph/atlas-phase3.json cases 31 op siblings 11 replays 4
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
```
