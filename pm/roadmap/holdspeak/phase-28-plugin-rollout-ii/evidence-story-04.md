# HS-28-04 Evidence — `risk_heatmap` (real run)

**Date:** 2026-06-01.
**Story:** [story-04-risk-heatmap.md](./story-04-risk-heatmap.md).

## Implementation Evidence

**Plugin** (`holdspeak/plugins/builtin/risk_heatmap.py`) — real `RiskHeatmapPlugin`
(`kind="synthesizer"`, deferred, `required_capabilities=["llm"]`). Phase-16
pattern: strict prompt → fenced ```json → `_extract_risks` parses
`{"risks": [{risk, impact, likelihood, mitigation, owner}]}`. `impact` /
`likelihood` are coerced via `_normalize_level` to `low | medium | high`
(synonyms: `critical`/`major`/`severe`/`likely` → high, `moderate` → medium,
`minor`/`unlikely` → low; unknown → medium). `mitigation` / `owner` null-coerced.
A risk needs text. Success when ≥1 risk; else the clean failure shape. The
ID/artifact mismatch is intentional: plugin id `risk_heatmap` → artifact type
`risk_register` (existing `_ARTIFACT_TYPE_BY_PLUGIN`). Uses
`build_configured_meeting_intel` (honours `.43`).

**Registration:** `_REAL_PLUGINS` maps `risk_heatmap` → the real class (**7 real
plugins now, 7 stubs**). **No routing ripple** — already on the `incident` chains.

**Synthesis** (registry): `_risk_body` (a markdown table: Risk / Impact /
Likelihood / Mitigation / Owner) + `_render_risks` registered under
`"risk_register"`. v1 is a structured table, not a literal 2D heatmap (status-doc
deferred decision). Other bodies unchanged.

**Web render** (`history.astro` + `history-app.js`): `risksFor(artifact)` + a
`.risk-table` with colour-coded `level-pill` chips (high=danger, medium=warning,
low=success) for impact/likelihood, from `structured_json`. Fallback `x-show`
excludes risks. `(cd web && npm run build)` clean.

## Tests

- `tests/unit/test_risk_heatmap_plugin.py` (12 cases): attributes, success +
  high-impact summary, `critical` → high coercion, unknown-level → medium,
  risk-without-text dropped, empty → failure, unparseable → failure,
  no-transcript, provider-exception, `_extract_risks` edge cases,
  `_normalize_level`, registrar, capability-blocked.
- `tests/unit/test_artifact_synthesis_diagram.py` (+1): `risk_register` table body
  + structured key; byte-for-byte default-body guard still passes.

```bash
uv run pytest -q tests/unit/test_risk_heatmap_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_intent_dispatch.py   # 27 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                           # 1978 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

```
summary: 3 risk(s); 3 high-impact.
 - [high/medium] Vendor slips API delivery, preventing on-time launch | mit: None | owner: None
 - [high/medium] Data migration loses customer records due to errors | mit: Maria will own the migration testing | owner: Maria
 - [high/medium] Compliance violation regarding storage of raw feedback text | mit: None | owner: None
```

## Live evidence (spoken e2e, extended)

`tests/e2e/test_spoken_meeting_e2e.py` now runs **seven** real plugins and asserts
the `risk_register` artifact + `.risk-table tbody tr` render. Refreshed
`evidence/spoken_meeting_artifacts.png` shows all seven artifacts inferred from
the natural conversation.

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s   # 1 passed (artifacts: action_items, adr, decisions, diagram, milestone_plan, requirements, risk_register)
```

## Result

**Seven real plugins now** — the architecture/delivery/risk meeting types are
covered. The renderer registry (HS-28-01) made all three new bodies drop-ins.
**Next: HS-28-05** to close the phase (RFC reality-status refresh + final-summary).
