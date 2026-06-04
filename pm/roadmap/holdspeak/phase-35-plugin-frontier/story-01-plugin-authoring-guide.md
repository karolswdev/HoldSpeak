# HS-35-01 — Public plugin-authoring guide (`docs/PLUGIN_AUTHORING.md`)

- **Status:** done (2026-06-03). Evidence: [evidence-story-01.md](./evidence-story-01.md).

## Goal

The meeting-intel plugin contract is fully trodden internally (the RFC + 14
reference impls) but lives only in the *internal* `docs/internal/
PLAN_ARCHITECT_PLUGIN_SYSTEM.md`. Externalize it as a public how-to so others can
write a plugin — the doc Phase 29 explicitly deferred.

## Scope

- **`docs/PLUGIN_AUTHORING.md`** covering (mirror the shape of
  `docs/CONNECTOR_DEVELOPMENT.md`):
  1. The `HostPlugin` protocol — `id`, `version`, `kind`, `required_capabilities`,
     `execution_mode` (`inline` vs `deferred`), and the `run(context) -> dict`
     signature + the `ContextEnvelope` it receives.
  2. The reference pattern — build a JSON-only prompt → call the configured intel
     (`build_configured_meeting_intel()` / `MeetingIntel._chat_completion_text`) →
     parse + validate → return structured output (with a `confidence_hint`).
  3. The `llm` capability gate — declaring `required_capabilities = ["llm"]` and
     what "blocked" means when no endpoint is configured.
  4. Rendering — registering a synthesis renderer in `plugins/synthesis.py`
     (`_ARTIFACT_RENDERERS` / `_ARTIFACT_TYPE_BY_PLUGIN`) so the artifact shows in
     the web `/history` view.
  5. Joining a chain — the profile/intent model (`router.PROFILE_PLUGIN_BASE_CHAINS`
     / `_INTENT_PLUGIN_CHAIN`) and the test-update ripple (HANDOVER §5).
  6. Testing — stubbing the intel call, fixtures, the "shipped" bar (real `run`,
     real downstream, a renderer, unit + integration coverage) from RFC Appendix A.
- **Wire-in** — link from `docs/README.md` (index) and the README "Meeting
  intelligence plugins" section (which currently points only at the internal RFC).

## Test plan

- Doc link-check (`tests/unit/test_doc_drift_guard.py`) green — the new doc + its
  inbound links resolve.
- Manual: a reader can follow it against one real built-in (e.g. `decision_capture`).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` green (docs-only).

## Done when

- [x] `docs/PLUGIN_AUTHORING.md` documents the full contract + workflow (the 6
      points above), accurate against the current code.
- [x] Linked from `docs/README.md` + the README plugin section; link-check green.
- [x] Full suite green.
