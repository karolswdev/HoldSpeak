# HS-27-03 Evidence — `decision_capture` (decisions + open questions)

**Date:** 2026-06-01.
**Story:** [story-03-decision-capture.md](./story-03-decision-capture.md).

## Implementation Evidence

**Plugin** (`holdspeak/plugins/builtin/decision_capture.py`) — net-new
`DecisionCapturePlugin` (`kind="synthesizer"`, deferred, `["llm"]`), Phase-16
pattern: strict prompt → single fenced ```json → `_extract_decisions` parses a
`{"decisions": [{decision, rationale}], "open_questions": [...]}` object
(fenced or bare; tolerates string-or-object decisions). Success when ≥1 decision
or open question; else the clean failure shape. Uses
`build_configured_meeting_intel` (so it honours the `.43` config).

**Registration & routing:**
- `_BUILTIN_PLUGIN_DEFS` gains `("decision_capture", "synthesizer")`;
  `_REAL_PLUGINS` maps it to the real class (3 real plugins now, 11 stubs).
- `router.py`: added to the **balanced** (default) profile base chain, so it
  fires on every balanced meeting regardless of detected intent — the "ubiquity"
  wiring. (Other profiles can opt in later.)
- `synthesis.py`: `_ARTIFACT_TYPE_BY_PLUGIN["decision_capture"] = "decisions"`;
  a `decisions` body branch (`**Decisions**` / `**Open questions**` sections) +
  `structured_json["decisions"]` / `["open_questions"]`. Other bodies
  byte-for-byte unchanged.

**Web render** (the HS-27-02 lesson applied up front): `history.astro` +
`history-app.js` render a `decisions` artifact as two structured lists
(Decisions with optional rationale; Open questions) from `structured_json` —
never the raw `body_markdown`.

## Tests

- `tests/unit/test_decision_capture_plugin.py` (10 cases): attributes, success
  (decisions + questions), decisions-only, empty → failure, unparseable →
  failure, no-transcript, provider-exception, `_extract_decisions` edge cases,
  registrar returns the real class, host-blocked-without-capability.
- `tests/unit/test_artifact_synthesis_diagram.py` (+1): `decisions` body +
  structured keys; the byte-for-byte non-custom-body guard still passes.
- **Routing ripple, fixed (not silenced):** adding `decision_capture` to the
  balanced base chain changed the dispatched chain, so `test_intent_dispatch.py`
  (chain constant + window-order count 3→4) and the two full-pipeline tests
  (`test_intent_pipeline`, `test_multi_intent_routing` — they register the union
  of plugin ids as stubs) were updated to include it. These were *correct* test
  updates (the product behaviour changed), verified green.

```bash
uv run pytest -q tests/unit/test_decision_capture_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_intent_dispatch.py tests/unit/test_intent_router.py   # 28 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                                                            # 1926 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (spoken e2e, extended)

`tests/e2e/test_spoken_meeting_e2e.py` now runs **all three** real plugins
(`mermaid_architecture`, `action_owner_enforcer`, `decision_capture`) against the
real `.43` Q6 endpoint and asserts each renders. Updated screenshot
`evidence/spoken_meeting_artifacts.png` shows, from the spoken meeting:

- Transcript (per-speaker, real Whisper output);
- Mermaid Architecture (rendered SVG);
- **Decision Capture (decisions)** — Decisions + Open-questions lists;
- Action Owner Enforcer (action_items) — the ownership checklist.

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s   # 1 passed
```

## Result

Three real ubiquitous plugins now flow end-to-end (transcript → LLM → artifact →
structured web render), all demonstrated by one spoken-meeting e2e. Phase 27 is
3/5. **Next: HS-27-04** (`requirements_extractor`, with its own structured
render), then **HS-27-05** to close (incl. the RFC reality-status refresh for the
plugins shipped this phase).
