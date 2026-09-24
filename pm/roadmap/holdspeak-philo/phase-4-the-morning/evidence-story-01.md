# Evidence - PHILO-4-01

- **Story:** PHILO-4-01 - Generate is always reachable
- **Status:** done
- **Date:** 2026-09-23

## Proof

### Captured run — 2026-09-24T05:29:52Z

- **Command:** `bash -c cd web && npx vitest run src/desk/chair src/desk/surface`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50efadaa83bd11187ff87d316005705e2bd02d0c

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-4-01/web


 Test Files  39 passed (39)
      Tests  398 passed (398)
   Start at  23:29:52
   Duration  4.04s (transform 2.91s, setup 3.61s, import 11.42s, tests 8.72s, environment 14.33s)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
```

### Captured run — 2026-09-24T05:30:05Z

- **Command:** `uv run --extra dev pytest -q -p no:cacheprovider tests/unit/test_philo_4_01_generate.py tests/unit/test_monday_brief_service.py tests/unit/test_hs171_aggregate_notify.py tests/unit/test_walk_monday_brief_126.py tests/unit/test_philo_graph_atlas.py tests/integration/test_phase200_attention_coverage.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50efadaa83bd11187ff87d316005705e2bd02d0c

```text
........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 6.22s
```

### Captured run — 2026-09-24T05:30:19Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain muaddib --viewport 1440 --engine real --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 50efadaa83bd11187ff87d316005705e2bd02d0c

```text
[glass_infra] web bundle rebuilt in 4.7s
PASS: live
BRAIN: muaddib
SOURCE: 1c39294c9de932ae0352750b78e7a0a70b99a591 dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-CMAuckoZ.js'] hub=http://127.0.0.1:62528 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-dl5j400i/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: fail terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053019Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053019Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' NOT in observe_at text
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'document_text_len', 'document_text_sha256']).
```

### Captured run — 2026-09-24T05:33:50Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain muaddib --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 50efadaa83bd11187ff87d316005705e2bd02d0c

```text
PASS: live
BRAIN: muaddib
SOURCE: 1c39294c9de932ae0352750b78e7a0a70b99a591 dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-CMAuckoZ.js'] hub=http://127.0.0.1:63629 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hwaxiifm/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: fail terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053350Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053350Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' NOT in observe_at text
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'document_text_len', 'document_text_sha256', 'focus_label', 'rect', 'text']).
```
