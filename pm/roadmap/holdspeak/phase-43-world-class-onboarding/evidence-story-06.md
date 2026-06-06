# Evidence — HS-43-06 — Closeout (wire the wizard + docs + PR)

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-43-world-class-onboarding`

See [`final-summary.md`](./final-summary.md) for the full wrap-up.

## What shipped

- **The wizard is now the first-run path.** `web/src/pages/index.astro`: the `/`
  guard sends a **first-run** user to `/welcome` (the wizard) and a returning
  **hard-blocked** runtime to `/setup`. `web_runtime._print_setup_nudge`: the CLI
  prints "Welcome! Get set up in a minute: open …/welcome" on a fresh launch.
- **Docs lead with the wizard** — `docs/GETTING_STARTED.md` §4 is now "The welcome
  wizard" (the six steps), with `/welcome` + `/setup` in the routes table.
- **Dogfood** — `scripts/dogfood_wizard.py` → `WIZARD DOGFOOD OK`:
  ```
  1. fresh `/` -> /welcome   2. permissions   3. model GGUF -> backend llama_cpp
  4. first dictation: It worked.   5. presence on -> config.presence.enabled True (no env var)
  6. you're set   7. Open HoldSpeak -> dashboard
  ```
  (`evidence/wizard_dogfood.txt`.)
- **Before/after** — Phase-42 `setup_page.png` (boring checklist) vs the Phase-43
  `wizard_*.png` set.
- `final-summary.md`; README → done; HANDOVER refreshed; doc-guards green.

## Verification
```
uv run pytest -q tests/integration/test_web_setup_route.py tests/unit/test_doc_drift_guard.py → 9 passed
uv run python scripts/dogfood_wizard.py → WIZARD DOGFOOD OK
uv run pytest -q --ignore=tests/e2e/test_metal.py → green
```

## Acceptance criteria
- [x] Wizard dogfooded; before/after captured; full suite green; 0 `_built/`;
      final-summary.md; README → done; PR opened/merged.
