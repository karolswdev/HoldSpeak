# Evidence — HS-21-01 Import AIPI-Lite Tree

- **Date:** 2026-05-24
- **Status:** done
- **Story:** [HS-21-01](./story-01-import-aipi-lite-tree.md)

## What changed

- Imported the AIPI-Lite firmware and bridge tree into `aipi-lite/`.
- Added root ignore rules for AIPI local runtime/config state:
  - `aipi-lite/secrets.yaml`
  - `aipi-lite/bridge.env`
  - `aipi-lite/.esphome/`
  - `aipi-lite/.venv/`
  - cache and coverage paths
- Added `aipi-lite/IMPORT.md` with source provenance and dirty-file notes.
- Updated HoldSpeak README and roadmap to mark AIPI-Lite as first-class.

## Import source

- **Source path:** `/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge`
- **Source branch:** `mine`
- **Source HEAD:** `f3d289f`

## Validation

```bash
git check-ignore -v aipi-lite/secrets.yaml aipi-lite/bridge.env aipi-lite/.esphome/foo aipi-lite/.venv/foo aipi-lite/.coverage aipi-lite/__pycache__/x.pyc
```

Result:

```text
aipi-lite/.gitignore:1:secrets.yaml  aipi-lite/secrets.yaml
aipi-lite/.gitignore:2:bridge.env    aipi-lite/bridge.env
aipi-lite/.gitignore:3:.esphome/     aipi-lite/.esphome/foo
aipi-lite/.gitignore:4:.venv/        aipi-lite/.venv/foo
aipi-lite/.gitignore:12:.coverage    aipi-lite/.coverage
aipi-lite/.gitignore:5:__pycache__/  aipi-lite/__pycache__/x.pyc
```

```bash
test -f aipi-lite/secrets.yaml && echo secrets-present
test -f aipi-lite/bridge.env && echo bridge-env-present
```

Result:

```text
secrets-present
bridge-env-present
```

```bash
PYTHONPATH=aipi-lite /home/karol/dev/esp32/AIPI-Lite-Voice-Bridge/.venv/bin/pytest -q aipi-lite/tests
```

Result:

```text
163 passed in 7.63s
```

```bash
git diff --check
```

Result: passed.

## Notes

- `aipi-lite/secrets.yaml` and `aipi-lite/bridge.env` remain on disk for local
  use but are ignored and must not be staged.
- The import excludes the source checkout's `.git`, `.venv`, `.esphome`,
  Python caches, pytest/ruff caches, and coverage output.
- Running the imported AIPI tests with HoldSpeak's existing `.venv` failed at
  collection because `structlog` is not installed there. The successful run
  above uses the prior AIPI virtualenv; HS-21-02 should define the unified
  dependency workflow.
