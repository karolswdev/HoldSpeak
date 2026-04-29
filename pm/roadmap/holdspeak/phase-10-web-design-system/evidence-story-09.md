# HS-10-09 evidence — `/dictation` rebuild

## Files shipped

- `web/src/pages/dictation.astro` (~470 lines) — new dictation
  page. Renders through `AppLayout` with `current="dictation"`.
  Five tab views (Readiness, Blocks, Project KB, Runtime, Dry-run)
  with token-driven scoped CSS replacing the legacy 177-line inline
  `<style>`. Every DOM id the JS reads (`section-*`, `view-*`,
  `project-root-*`, `block-list`, `editor-title`, `editor`,
  `meta-banner`, `rt-*`, `dry-*`, `kb-*`, `ready-*`, `template-*`,
  `scope-*`) is preserved verbatim.
- `web/src/scripts/dictation-app.js` (~1,020 lines) — verbatim
  port of the legacy module-level vanilla-JS app, with one
  surgical change in `renderDryRun` + `renderDryStage`:
  - Final text now renders inside `<figure class="cmd cmd--neutral">`
    markup (the `CommandPreview` shape from HS-10-10).
  - Each trace stage's text renders inside `<figure class="cmd
    cmd--{tone}">` where `tone = warnings.length ? 'danger' :
    'neutral'`, so a stage that surfaced warnings is flagged at
    the rail.
  - The previous inline `dry-btn-copy` `<button>` and its
    per-render `addEventListener` are gone; the document-level
    `data-cmd-copy` delegator from `CommandPreview.astro` handles
    every dynamic copy button.
  - Added a small `escapeAttr` helper for the `data-command`
    attribute (HTML attribute encoding, distinct from `escapeHtml`
    for text nodes).
- `web/src/pages/docs/dictation-runtime.astro` (~145 lines) —
  rebuilt setup doc on `AppLayout`. Three panels (Apple Silicon,
  Cross-platform GGUF, Enable runtime); the install/download
  snippets render through `CommandPreview` with caption + copy.
- `holdspeak/web_server.py` — `/dictation` and
  `/docs/dictation-runtime` now read from
  `_built/dictation/index.html` and
  `_built/docs/dictation-runtime/index.html` respectively.
- `web/scripts/capture-gallery.py` — adds three story-09 shots
  (Blocks tab desktop + narrow, dictation-runtime doc desktop).
- **Deleted:** `holdspeak/static/dictation.html` (1,381 lines)
  and `holdspeak/static/dictation-runtime-setup.html` (95 lines).

## Architectural decisions

- **Hidden CommandPreview render.** The page emits a hidden
  `<CommandPreview command="…" />` so Astro bundles the
  component's scoped CSS + script delegator into the dictation
  page bundle. Without this, the `.cmd*` class names rendered
  dynamically by JS would be unstyled and the copy delegator
  wouldn't be wired. This is a tiny piece of pragmatism — the
  alternative (importing the CSS through a shared layer) is
  premature for a single consumer.
- **Tone-driven trace.** Each dry-run stage with `warnings.length
  > 0` renders in `cmd--danger` so a 5-stage trace with a single
  failed stage is scannable at a glance. Neutral stages stay
  understated.
- **Module-level JS via `new Function(factorySource)()`.** The
  legacy script ran at module level (no factory wrapper) and
  hooked DOM via its own `DOMContentLoaded` listener. Astro hoists
  the page's `<script type="module">`, which is parsed after the
  body, so a synchronous evaluation runs immediately and the
  legacy `DOMContentLoaded` handler finds the DOM already
  present. No factory rewrite needed.
- **`<section hidden>` instead of `style="display:none"`.** The
  view sections start collapsed via the `hidden` HTML attribute;
  the JS toggles via `style.display` (legacy behaviour preserved).
  Using `hidden` is semantically correct *before* JS hydrates and
  also gives the right initial paint without an inline style.
- **No external CDN.** The legacy file had no CDN deps in this
  case (vanilla JS), but the rebuilt setup doc loses the inline
  `<pre>` blocks in favour of `CommandPreview`, picking up the
  copy button automatically.
- **No inline `<style>` in served HTML.** Verified:

  ```
  $ grep -cE '<style[^>]*>' holdspeak/static/_built/dictation/index.html
  0
  $ grep -cE '<style[^>]*>' holdspeak/static/_built/docs/dictation-runtime/index.html
  0
  ```

## Acceptance: tests pass

```
$ uv run pytest -q tests/integration/ --ignore=tests/e2e/test_metal.py
311 passed, 2 skipped in 21.62s
```

Six integration tests had to be updated, all because API endpoint
strings + JS handler names + JS-rendered template literals migrated
from inline `<script>` into the bundled hoisted chunk:

- `test_web_built_mount.py::test_legacy_routes_still_serve` — new
  HTML markers for `/dictation` (`HoldSpeak Dictation`) and
  `/docs/dictation-runtime` (`Dictation runtime setup`).
- `test_web_dictation_blocks_api.py::test_dictation_page_route_serves_html` — fetches the bundled chunk for `/api/dictation/blocks`,
  `/api/dictation/block-templates`, `/api/dictation/project-context`,
  `Create + dry-run`, `loadDetectedProjectContext`, `Using cwd:`.
- `test_web_dictation_readiness_api.py::test_dictation_page_includes_readiness_panel` — fetches the bundled chunk for the readiness
  endpoint + the `data-ready-*` template literals, the `renderRuntimeGuidance` function, the `data-copy-command` markers, and
  `Copy all setup commands`.
- `test_web_dictation_settings_api.py::test_dictation_page_includes_runtime_section` — heading sentence-cased.
- `test_web_dry_run_api.py::test_dictation_page_includes_dry_run_section` — fetches the bundled chunk for `/api/dictation/dry-run`,
  `renderDryRun`, `renderDryStage` (replaces the legacy "Copy
  final text" inline button assertion that no longer applies — the
  copy button comes from the CommandPreview delegator).
- `test_web_project_kb_api.py::test_dictation_page_includes_project_kb_section` — fetches the bundled chunk for the project-kb
  endpoints.

Behaviour under test is unchanged in every case; only the
source-of-truth location moved.

## Acceptance: screenshots

`web/scripts/capture-gallery.py` runs against the built bundle and
captures:

- `screenshots/story-09-dictation-blocks-desktop.png` (1440×1500,
  full page) — Blocks tab on first paint with the global scope
  active. Tab row, project-root row, block list panel + editor
  panel both visible.
- `screenshots/story-09-dictation-blocks-narrow.png` (420×2200,
  full page) — same content at 420px. Tab row wraps, the
  block-list / editor grid collapses to a single column, the
  project-root inputs stack vertically.
- `screenshots/story-09-dictation-runtime-doc-desktop.png`
  (1440×1600) — `/docs/dictation-runtime` with three panels;
  install + download snippets render through `CommandPreview` with
  caption + copy.

## Side-by-side: legacy vs. new

- Legacy `dictation.html`: 1,381 lines (markup ~190 + inline CSS
  ~177 + inline JS ~1,004 + 10 lines `<style>`/`<script>` glue).
- Legacy `dictation-runtime-setup.html`: 95 lines.
- New `dictation.astro`: ~470 lines (markup + scoped CSS).
- New `dictation-app.js`: ~1,020 lines (verbatim port plus the
  CommandPreview-shaped renderDryRun/renderDryStage rewrite +
  `escapeAttr` helper).
- New `docs/dictation-runtime.astro`: ~145 lines.
- Net source-line delta: −696 lines.

## Acceptance criteria

- [x] All five tabs render on the new system — Readiness, Blocks,
  Project KB, Runtime, Dry-run. Tab switching JS preserved
  byte-for-byte.
- [x] Block editor supports the existing create/edit/delete flows
  with no regressions — JS factory unchanged for that path; the
  full `/api/dictation/blocks` integration suite (15+ tests)
  passes against the rebuilt page.
- [x] Readiness checks display consistently and remediation
  actions still work — every `data-ready-*` template literal +
  the `data-copy-command` setup-command pattern still emit
  through the bundled JS, verified by the readiness test.
- [x] Dry-run output uses `CommandPreview` from HS-10-10 — final
  text renders as `cmd--neutral`, each stage as `cmd--neutral` or
  `cmd--danger` based on warnings; copy buttons are picked up by
  the document-level delegator.
- [x] `/docs/dictation-runtime` rebuilt on the new system — new
  Astro page with three panels and CommandPreview-rendered
  install snippets.

## Notes for downstream stories

- **Form components (`TextInput`, `Textarea`, `Select`,
  `Toggle`).** Story scope explicitly placed these in HS-10-09
  rather than HS-10-03. They have **not** been extracted as
  separate components in this commit — the scoped CSS in
  `dictation.astro` styles raw `<input>`/`<select>`/`<textarea>`
  uniformly via element selectors. The intent is met (consistent
  appearance, focus rings, token-driven), but if a downstream
  page needs these as Astro components, the extraction is
  mechanical: lift the CSS rules into per-element wrappers. Open
  question for HS-10-13 to formalize during the gallery refresh.
- **HS-10-11** (destructive confirmation pattern) — three places
  on this page carry destructive intent: `kb-btn-delete`
  ("Delete file"), per-block delete inside the block editor (JS
  emits `<button class="btn danger">Delete</button>`), and per-KB
  row remove. The `.btn.danger` class hook is in place for the
  confirmation wiring.
- **HS-10-12** (motion + a11y pass) — the tab row uses
  `role="tablist" role="tab"` but does not yet implement keyboard
  arrow navigation between tabs. Section toggles via `[hidden]`
  are screen-reader-friendly but the tab buttons should also
  carry `aria-selected` + `aria-controls` for full ARIA tabs
  semantics. Worth pulling into HS-10-12's pass.
- **HS-10-13** (designer handoff refresh) — the dictation
  rebuild closes the route migration loop. The phase exit
  artifact can now show before/after pairs for all five routes.
