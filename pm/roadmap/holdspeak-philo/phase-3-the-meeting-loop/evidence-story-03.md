# Evidence - PHILO-3-03

- **Story:** PHILO-3-03 - Read the dated brief with that decision (A3)
- **Status:** done
- **Date:** 2026-09-23

## Proof

### Captured run — 2026-09-23T19:03:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.r9p2ZWqMzh PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm sh -c set -o pipefail; (cd web && npx vitest run src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx src/desk/chair/__tests__/briefReceiptRendered202.test.tsx) && uv run --extra dev --extra test pytest -q -p no:cacheprovider tests/unit/test_philo3_03_brief_clock.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_hs175_week_brief.py tests/unit/test_brief_shelf.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/e2e/test_hs170_arrival_glass.py && uv run --extra dev python scripts/philo_graph_reference.py --check && uv run python scripts/philo_api_reference.py --check && uv run python scripts/philo_openapi_reference.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f01c54c74a4a916607e968191e2952a76743eb7

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-3-03/web


 Test Files  2 passed (2)
      Tests  10 passed (10)
   Start at  13:03:23
   Duration  921ms (transform 656ms, setup 131ms, import 905ms, tests 199ms, environment 377ms)

........................................................................ [ 60%]
...............................................                          [100%]
119 passed in 29.46s
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
API reference checked
OpenAPI: 569 paths
```
