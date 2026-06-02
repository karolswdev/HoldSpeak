# HS-31-03 — `ActivityRepository` + `PluginArtifactRepository` + `ProjectRepository` + delete the god-class

- **Project:** holdspeak
- **Phase:** 31
- **Status:** done (2026-06-02). Evidence: [evidence-story-03.md](./evidence-story-03.md).

## Goal

Migrate the remaining three domains into repositories, then **delete
`MeetingDatabase` entirely** — by the end of this story nothing imports or
references it. Three repositories, SQL moved verbatim, call sites updated to the
`db.*` container. Can be one PR or three sub-commits — keep each domain isolated.

## Scope

- `ActivityRepository` — `activity_records`, `activity_annotations`,
  `activity_domain_rules`, `activity_enrichment_connectors`,
  `activity_import_checkpoints`, `activity_meeting_candidates`,
  `activity_privacy_settings`, `activity_project_rules`.
- `PluginArtifactRepository` — `plugin_runs`, `plugin_run_jobs`, `artifacts`,
  `artifact_sources`, `intent_windows`, `intent_window_scores`.
- `ProjectRepository` — `projects`, `project_detection_log`, `connector_runs`.
- Update all remaining call sites to `db.activity.*` / `db.plugins.*` / `db.projects.*`.
- **Delete the `MeetingDatabase` class.** The connection ownership + schema build
  live on the `Database` container; the god-class is gone. `grep -r MeetingDatabase`
  returns nothing.

## Test plan

- Rewrite the remaining `test_db.py` sections + activity / plugin-job / project
  route + service tests to the repo API.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- `grep -r MeetingDatabase holdspeak tests` — zero hits.

## Done when

- [x] All three repos extracted; call sites use the `db.*` container.
- [x] `MeetingDatabase` is deleted (renamed to `Database`); no remaining references in code.
- [x] Full suite green (2062); ruff clean.
