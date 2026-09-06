# The G0 critical journey suite

Four journeys a HoldSpeak installation must complete before any release
evidence means anything. They run the **real** services — the real FastAPI
app, the real database, the real repositories and routes — and substitute
only what sits outside the machine: the inference engine, the speech engine
and the typing target.

They must pass on a bare Linux runner: **no local model file, no PortAudio, no
macOS, no network, a fresh data root.** If a journey needs any of those, it is
not a G0 journey.

Run them:

    HOME=$(mktemp -d) uv run pytest -q -m critical tests/critical -p no:cacheprovider

CI reports them as their own job (`Critical Journeys (G0)` in
`.github/workflows/test.yml`), separately from the historical jobs, so a green
line here is readable on its own.

| Journey | Scenario | File |
|---|---|---|
| Identity | P200-A01 — name the loaded backend, bundle and database; see a stale bundle and a second runtime | `test_journey_identity.py` |
| Recovery | P200-A02 — back up, restore a copy, reopen the same records | `test_journey_backup_restore.py` |
| First sentence | P200-A03 — capture, keep, correct and reopen a sentence with no model present | `test_journey_first_sentence_cold.py` |
| Project first result | the Project's first useful result, cold | `test_journey_project_first_result.py` |
