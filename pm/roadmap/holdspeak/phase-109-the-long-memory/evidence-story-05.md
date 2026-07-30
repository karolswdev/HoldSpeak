# Evidence - HS-109-05

- **Story:** HS-109-05 - The Project Memory window
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-30T00:23:20Z

- **Command:** `bash -c cd web && npm run test:web 2>&1 | tail -4 && npm run build 2>&1 | tail -2 && npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 18b4c8be25645574cc642a2430b8d862b7d17fa9

```text
      Tests  373 passed (373)
   Start at  18:23:20
   Duration  13.78s (transform 906ms, setup 1.84s, import 4.65s, tests 3.78s, environment 12.39s)

- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 3.32s

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```

### Captured run — 2026-07-30T00:23:41Z

- **Command:** `uv run pytest -q tests/ -k aftercare or project or decision --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 18b4c8be25645574cc642a2430b8d862b7d17fa9

```text
...................s.................................................... [ 27%]
........................................................................ [ 54%]
........................................................................ [ 82%]
...............................................                          [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_live_bus.py:24: needs Playwright + a browser
SKIPPED [1] tests/e2e/test_route_preflight.py:26: pre-flight needs Playwright + a browser
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
262 passed, 6 skipped, 4117 deselected in 40.43s
```

### Captured run — 2026-07-30T00:24:32Z

- **Command:** `bash -c HS_WALK_BASE=http://127.0.0.1:8797 HS_WALK_TOKEN=hs109-walk-token uv run --with playwright python scripts/hs109_05_walk.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 18b4c8be25645574cc642a2430b8d862b7d17fa9

```text
PASS  [1440] project opened from Desk search
PASS  [1440] memory window face present
PASS  [1440] accept gesture → promote verbs appear
PASS  [1440] deterministic promote → artifact chip
PASS  [1440] project search hits the real decision
shot: uat/_runs/hs-109-05-walk/memory-window-1440.png
PASS  [1440] ask-this-project answers from the archive (.43)
PASS  [1440] grounded-on count visible
shot: uat/_runs/hs-109-05-walk/memory-window-ask-1440.png
PASS  [393] project opens
PASS  [393] no horizontal body overflow
shot: uat/_runs/hs-109-05-walk/memory-window-393.png

9/9 beats passed
```

## The walk, narrated (screenshots read before the flip)

The hub was spawned from THIS tree serving a COPY of the owner's REAL
archive (real project `delivery-workbench`, real meetings, the real
decision records with verified moments), with the `a9e12058` meeting
associated to the project through the real route and the projection
re-derived so project keys inherit. The rig
(`scripts/hs109_05_walk.py`) passed **9/9**:

- **1440** — the project opened from the Desk search as a real desk
  object; the memory window in the one grammar with
  Timeline / Decisions / Search / Ask faces
  ([assets/memory-window-1440.png](./assets/memory-window-1440.png)):
  the timeline interleaves real decisions (lifecycle chips) with the
  real meeting row; Accept in-row (owner gesture, no modal) made the
  promote verbs appear; deterministic Promote produced the
  `artifact:promoted-…` chip; project-scoped search found the real
  BLUE LANTERN decision.
- **The ask face**
  ([assets/memory-window-ask-1440.png](./assets/memory-window-ask-1440.png))
  — mic on the input, the egress badge `→ 192.168.1.43` at the point
  of decision with the disclosure line (Private endpoint · sends
  Instruction, Selected context, Grounding), the grounding chip
  pre-pinned to the project, and the REAL `.43` answer: "The launch
  codename for the mesh milestone is **BLUE LANTERN**", **Grounded on
  2 of 2 matches**, two openable citation chips (the promoted
  artifact and the milestone artifact).
- **393**
  ([assets/memory-window-393.png](./assets/memory-window-393.png)) —
  list-first, rows truncate honestly, the Accepted chip persisting
  from the walk's real gesture, no horizontal body overflow
  (asserted).

The HS-109-03 promote verbs were wired into the agent's
`DecisionPromotionSlot` seam during this shipping pass (kind select +
Promote + Draft with model + the artifact chip), calling the real 03
routes.

## Suites

Web 373/373 + build + typecheck (first capture); backend
aftercare/project/decision family 262 green (second capture); full
suite tail below.
