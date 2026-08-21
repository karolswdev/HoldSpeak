# HS-141-04 deterministic glass walk

These screenshots are produced by `tests/e2e/test_hs14104_refinement_glass.py`
with a fresh temporary `HOME` and SQLite database at each viewport (1440x900,
393x900). The owner journey is browser-only: typed First Value, Keep as Note,
Continue later, Develop this thought, then the ordinary refinement controls.

The provider is a **deterministic in-process provider simulation** attached only
to the real kernel runner's engine-factory seam. A temporary local model path
makes that exact `this_machine` destination truthfully ready. No browser fetch
interception, direct review API call, seeded note, or prewritten result row is
used. The real API, coordinator, kernel operation/receipt, projection and
polling/reconcile path produce the question; Answer writes the same Note; Stop
is exercised before and after a physical attempt, with delayed output released
only after Stop to prove suppression.

Run after `cd web && npm run build`:

```sh
uv run pytest -q tests/e2e/test_hs14104_refinement_glass.py --timeout=120
```

The test asserts zero page errors and both document/body width at each viewport.

## Model-unavailable recovery

`tests/e2e/test_hs141_models_setup_glass.py` opens the real Settings model page
from a fresh isolated home at 1440×900 and 393×900. It proves the guided
**Choose your AI** hierarchy, local-first setup, progressively disclosed AI
connections, touch geometry, and no-prompt readiness check.

- [Choose your AI — 1440](./hs-141-models-setup-1440.png)
- [Choose your AI — 393](./hs-141-models-setup-393.png)
