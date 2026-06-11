# Evidence — HS-58-04: The developer + ops docs

**Date:** 2026-06-11
**Branch:** `phase-58-front-door`

## 1. What shipped

The eight extend-it/ops docs revised against the canon:

- **The contributor-pitch ledes.** PLUGIN_AUTHORING now says the quiet
  part ("the highest-leverage way to make HoldSpeak yours: the routing,
  persistence, rendering, and approval machinery already exist, so a new
  artifact type is mostly the prompt you wish your meetings produced");
  CONNECTOR_DEVELOPMENT opens with why a connector exists ("if HoldSpeak
  does not yet see the part of your world you care about… without forking
  the runtime"). The reference docs (DEVICE_PROTOCOL, MODELS, SECURITY,
  RELEASING, AGENT_HOOK_INSTALL, AIPI_LITE_DEV_WORKFLOW) keep their
  reference register; their ledes were already direct.
- **The dash cleanup**, prose only (fenced example code exempt per the
  canon), before → after: PLUGIN_AUTHORING 39 prose sites → 0 (43 stay
  inside example-code blocks), CONNECTOR_DEVELOPMENT 16 → 0,
  DEVICE_PROTOCOL 14 → 0, SECURITY 17 → 0, MODELS 11 → 0,
  AIPI_LITE_DEV_WORKFLOW 4 → 0 (RELEASING and AGENT_HOOK_INSTALL were
  already clean). Every replacement hand-chosen; bold-header list items
  became colon-led; mid-sentence appositives became parentheses, commas,
  or semicolons by sense; the numbered "1 — Build…" steps became
  "Step 1: build…"; numeric ranges normalized (4-9B, Medium-High).
- **No contract, schema, or protocol fact altered**: every edit in these
  files is punctuation, a lede, or a heading reword (e.g. "Egress points:
  everywhere data can leave the machine"); close codes, capability names,
  manifest fields, frame formats, and egress tables carry the exact same
  content. The two table cells whose value was a bare "—" (meaning
  "none") now say "none" explicitly, which is more honest than a glyph.

## 2. Tests

```
$ uv run pytest -q tests/ -k "doc"
77 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
```

(Docs-only; suite unchanged; all locks green.)
