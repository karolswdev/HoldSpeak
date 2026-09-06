# Evidence - HS-168-05

- **Story:** HS-168-05 - The Tuesday walk, face-driven (the owner's real desk; the window shot at every step; the stopwatch — OWNER VERDICT)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-04T07:02:03Z

- **Command:** `bash -c HS168_WALK=1 HS168_WALK_DB=isolated uv run pytest -q -p no:cacheprovider tests/e2e/live168_walk.py --timeout=300 2>&1 | tail -2; python3 -c "import json; t=json.load(open('pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-05-walk/transcript-1440.json')); s=t['steps']; print('isolated 1440: steps', len(s), 'last', s[-1]['step_name'], s[-1]['clicks_cumulative'], 'clicks', s[-1]['seconds_cumulative'], 's'); r=json.load(open('pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-05-walk/real-transcript-1440.json')); rs=r['steps']; print('REAL 1440: mode', r['mode'], 'steps', len(rs), 'last', rs[-1]['step_name'], rs[-1]['clicks_cumulative'], 'clicks', rs[-1]['seconds_cumulative'], 's', rs[-1]['notes'])"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c670c0c08d04a2853b59a7a0aa137939f75ffc35

```text
..                                                                       [100%]
2 passed in 114.03s (0:01:54)
isolated 1440: steps 22 last activated 18 clicks 36.14 s
REAL 1440: mode real steps 17 last activated 18 clicks 38.33 s project_id=proj-4ed6be467d96; lifecycle=active
```

### Captured run — 2026-09-04T15:23:53Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.8yivZ8u83r uv run pytest -q tests/e2e/test_hs168_window_wings_glass.py tests/e2e/test_hs168_sources_glass.py -p no:randomly`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 75939ce7192f59b9fa0e295f1e2fc5b1bb77d2be

```text
......                                                                   [100%]
6 passed in 113.44s (0:01:53)
```
