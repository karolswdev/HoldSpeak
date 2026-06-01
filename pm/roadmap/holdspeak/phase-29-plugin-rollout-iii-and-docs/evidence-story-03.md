# HS-29-03 Evidence — Comms plugins (real run) → zero stubs

**Date:** 2026-06-01.
**Story:** [story-03-comms-plugins.md](./story-03-comms-plugins.md).

## Implementation Evidence

The last two stubs flipped to real LLM-backed plugins (deferred, `["llm"]`),
Phase-16 pattern, registered in `_REAL_PLUGINS`. **Fourteen real plugins now —
zero `DeterministicPlugin` stubs remain.** No routing ripple — both already on the
comms chain.

- **`stakeholder_update_drafter`** (`stakeholder_update_drafter.py`) → a single
  object `{"update": {headline, highlights[], risks[], next_steps[]}}`; success
  when the headline or any section is non-empty. Artifact `stakeholder_update`.
- **`decision_announcement_drafter`** (`decision_announcement_drafter.py`) →
  `{"announcements": [{title, audience|null, message}]}`; each needs title +
  message. Artifact `decision_announcement`.

**Synthesis** (registry): `_stakeholder_update_body` (headline + Highlights/Risks/
Next-steps sections) + `_decision_announcement_body` (title + audience + message),
renderers registered under `stakeholder_update` / `decision_announcement`.

**Web render** (`history.astro` + `history-app.js`): `stakeholderUpdateFor` /
`stakeholderSections` (headline + bulleted sections), `announcementsFor`
(title + audience pill + message); folded into `hasStructuredRender`.
`(cd web && npm run build)` clean.

## Tests

- `tests/unit/test_stakeholder_update_drafter_plugin.py` (10),
  `tests/unit/test_decision_announcement_drafter_plugin.py` (11): attributes,
  success, headline-only success, empty → failure, item-without-required-field
  dropped, unparseable → failure, no-transcript, provider-exception, `_extract_*`,
  registrar, capability-blocked.
- **`test_no_deterministic_stub_remains`** — asserts every `_BUILTIN_PLUGIN_DEFS`
  ID resolves to a non-`DeterministicPlugin` (the rollout-complete invariant).
- `tests/unit/test_artifact_synthesis_diagram.py` (+2): `stakeholder_update`,
  `decision_announcement` body cases; byte-for-byte default-body guard still passes.
- **Two stub-stand-in tests reworked** (no stub left to point at):
  `test_plugin_host.py::test_builtin_plugins_register_and_execute` now asserts a
  real plugin is *blocked* without the `llm` capability;
  `test_mermaid_architecture_plugin.py::test_register_builtin_plugins_uses_real_class`
  asserts the sibling is *not* a `DeterministicPlugin`.

```bash
uv run pytest -q tests/unit/test_stakeholder_update_drafter_plugin.py tests/unit/test_decision_announcement_drafter_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_plugin_host.py tests/unit/test_mermaid_architecture_plugin.py   # 59 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                                                                                                                                          # 2062 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

```
UPDATE headline: ... MVP Scope Finalized with Postgres Adoption and Q3 Beta Target
  highlights: ['MVP scope defined', 'Postgres selected', 'Ingestion design progress', 'Beta Q3, sub-second dashboard']
  risks: ['Classifier model ownership unassigned', 'Open privacy concerns on raw feedback']
  next_steps: ['Sketch ingestion this week', 'Confirm legal angle', 'Assign classifier owner']
ANNOUNCEMENTS: 2 decision announcement(s) drafted.
  - Adoption of Postgres for Customer Feedback MVP | aud: Engineering Team
  - Private Beta Launch Timeline and Performance Target | aud: Product & Engineering Teams
```

(Not added to the shared spoken e2e — its conversation is a product kickoff;
verified by direct live checks + unit tests, per story scope.)

## Result

**The plugin rollout is complete: fourteen real plugins, zero stubs.** Every
registered MIR plugin has a real `run()`, a structured artifact, and a `/history`
render. **Next: HS-29-04** (document the plugin system on the public README), then
HS-29-05 (close).
