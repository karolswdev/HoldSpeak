# Evidence — HS-46-02: The README, reimagined (the 10-second hook)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-46-documentation-lift`.

## What shipped

The README went from a spec sheet to a product pitch: a 10-second hook, a
"Why it's different" cool-facts strip, every graphic kept, the repetition cut,
depth linked out — **205 → 152 lines** (a 26% cut) with **more** headline value.

## Before → after

| | Before (205 lines) | After (152 lines) |
|---|---|---|
| Opening | A competent one-liner, then a feature list | **Hook** ("Hold a key. Speak. It types — anywhere. 100% local. And it learns you.") + a **"Why it's different"** 7-bullet cool-facts strip |
| "It learns you" | Buried / unstated | Above the fold — strip bullet #2 **and** a dedicated **"See it learn"** section (the operator GIF) |
| Plugin showcase | A **52-line** section with the full 14-row table | A ~13-line **teaser + link** to the authoring/meeting guides (count + actuator note kept) |
| AIPI-Lite | **22 lines**, two long paragraphs | A ~13-line teaser + the device art + links |
| Repetition | "What it does" / "Intelligence Pipeline" / "Meeting plugins" overlap; **pre-release stated twice** | Folded; **pre-release stated once** |
| Config | A raw JSON block inline | A 3-line pointer ("Settings, not files") to the guides |
| Graphics | logo · workflow map · operator GIF · AIPI art | **all four kept** (6 image assets total), repositioned |

**Section structure** — before: What it does · Workflow Map · Intelligence
Pipeline · AIPI-Lite Companion · Platform support · Quickstart · Where to go next
· Meeting intelligence plugins · Configuration · Contributing · License. After:
*(hook + strip)* Why it's different · What it does at a glance · See it learn ·
Quickstart · Platform support · Meeting intelligence · AIPI-Lite companion · Where
to go next · Configuration · Contributing · License.

## The hook + strip (excerpt)

> **Hold a key. Speak. It types — anywhere. 100% local. And it learns you.**
>
> ## Why it's different
> - 🔒 **100% local by default** …
> - 🧠 **It learns you** — journaled (said → typed → routed → latency); correct in the moment; replay to watch it improve …
> - 🎙️ **Voice *and* meetings both get an afterlife** …
> - 🧩 **14 real LLM-backed meeting plugins** …
> - 🔌 **Bring your own model** … 🪟 **Ambient desktop presence** … 📟 **AIPI-Lite companion** …

## Honesty (per the HS-46-01 audit)

- **Pre-release banner kept** (stated once now).
- **"100% local"** framed honestly: "by default … private unless you deliberately
  point at a cloud endpoint" — the local-first invariant, not an absolute claim.
- **"14 built-in plugins"** matches the registry (pinned by the HS-46-01 guard).
- **Presence** linked correctly (the config-toggle anchor); **every install extra
  named** (`meeting`, `dictation-mlx/-llama/-openai`) verified against
  `pyproject.toml [project.optional-dependencies]`.
- All deep-link anchors are the HS-46-01-verified ones (kept, not regenerated).

## Tests run

- Story test plan: `uv run pytest -q -k "doc_drift or link"` → **7 passed, 1
  skipped** (incl. the HS-46-01 plugin-count guard, which reads the new README's
  "14 built-in plugins" — green).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2364 passed,
  17 skipped** (exit 0).

## Acceptance criteria

- [x] Opens with a 10-second hook + a cool-facts strip; the journal/replay
      "it learns you" story is above the fold.
- [x] Every existing pixellab graphic still present (logo, workflow map, operator
      GIF, AIPI art — 6 image assets).
- [x] Repetition removed (no overlapping what-it-does/pipeline/plugins
      re-description; pre-release once; AIPI + plugin depth linked out).
- [x] Materially shorter (205 → 152) while keeping a quickstart, the capability
      view, and the "where to go next" map.
- [x] Honest: pre-release kept; no claim contradicts local-first; cool facts
      cross-checked against HS-46-01.
- [x] Doc-drift + dangling-link guards green; before/after captured above.
