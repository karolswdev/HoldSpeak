# HS-16-04 Evidence — Web Mermaid rendering

**Date:** 2026-06-01.
**Story:** [story-04-web-mermaid-rendering.md](./story-04-web-mermaid-rendering.md).

## Implementation Evidence

**Dependency.** `web/package.json` now pins `mermaid: 11.15.0` (exact, no
caret — `npm install --save-exact mermaid@11`). v11's default `securityLevel`
is `strict` (HTML in labels disabled); we set it explicitly anyway.

**Render path.** The `/history` meeting-detail artifact list (`history.astro`)
gained a branch: for `artifact.artifact_type === 'diagram'` with a
`structured_json.mermaid` value, it renders a `<div class="mermaid-artifact"
x-init="renderMermaid($el, artifact.structured_json.mermaid)">` instead of the
raw `body_markdown` `<p>`. Every other artifact keeps the existing text body.

`history-app.js` `renderMermaid(el, code)`:
- Lazily loads mermaid via `window.__loadMermaid()`.
- `mermaid.initialize({ startOnLoad: false, securityLevel: 'strict',
  suppressErrorRendering: true, theme: 'dark' })` once.
- `await mermaid.render(id, code)` → injects the SVG.
- On any throw: replaces the container with an inline
  `.mermaid-render-error` warning + a `<pre>` of the raw source
  (`textContent`, so untrusted content can't inject markup).

**Lazy loader.** Because `history-app.js` is injected as a `?raw` string and
run via `new Function(...)`, a bare `import('mermaid')` inside it wouldn't be
bundler-resolvable. So the dynamic import lives in `history.astro`'s real module
script: `window.__loadMermaid = () => import('mermaid').then(m => m.default ?? m)`.
The bundler code-splits that into a standalone chunk fetched on demand.

**Styling.** `.mermaid-artifact :global(svg) { max-width: 100%; height: auto; }`
(`:global` because the SVG is injected at runtime and carries no Astro scope
attribute), plus `overflow-x: auto` on the container and muted styling for the
fallback warning/source.

## Bug caught during verification

The first screenshot pass showed mermaid injecting its own "Syntax error" bomb
SVG into `document.body` on the malformed input — even though our `try/catch`
already handled the failure. Fixed by adding `suppressErrorRendering: true` to
`mermaid.initialize`. Re-shot: the bomb is gone; only our inline fallback shows.

## Lazy-load verification (build)

```bash
cd web && npm run build
ls holdspeak/static/_built/_astro/ | grep -i mermaid
#   mermaid.core.CTTn9Q0W.js   (594K — standalone chunk)

grep -oE '/_built/_astro/[a-z0-9._-]+\.js' holdspeak/static/_built/index.html
#   only index.astro_astro_type_script_...js   (no mermaid)
grep -oE '/_built/_astro/[a-z0-9._-]+\.js' holdspeak/static/_built/dictation/index.html
#   only dictation.astro_astro_type_script_...js   (no mermaid)
grep -li mermaid holdspeak/static/_built/index.html holdspeak/static/_built/dictation/index.html
#   (no match — mermaid absent from home/dictation HTML)

# History page: no eager <script>/modulepreload for mermaid; the history entry
# chunk contains exactly one dynamic import() resolving to mermaid.core.*.js.
```

So mermaid loads only when a diagram artifact is actually rendered.

## Manual render verification (real Chrome)

Chrome-for-Testing 149 (via puppeteer, used only to drive the browser; **not**
added to `package.json`). A harness page loaded the real `mermaid@11.15.0` UMD
build and ran the exact `renderMermaid` logic (strict + `suppressErrorRendering`
+ the same fallback) against the actual generated architecture diagram and a
malformed input, at desktop (1280 px) and mobile (390 px) viewports.

```text
[desktop 1280px] ok->svg=true bad->fallback=true svg.maxWidth=376.688px
[mobile  390px]  ok->svg=true bad->fallback=true svg.maxWidth=376.688px
```

Screenshots:
- `evidence/mermaid_rendered_desktop.png` — valid diagram as SVG (Client → API
  Gateway → Auth/Billing → PostgreSQL), malformed → "Diagram could not be
  rendered — showing source." + raw source, no bomb graphic.
- `evidence/mermaid_rendered_mobile.png` — same, SVG constrained to card width.

**Verification boundary (honest scope):** the harness exercises the real
library/version + the exact render & fallback logic + scaling. The Alpine
`x-init` → `renderMermaid` plumbing on the live `/history` page (behind
`openMeeting` → `/api/meetings/{id}/artifacts`) was not click-driven in-browser;
it is locked instead by the `test_history_page_contains_control_plane_tabs_and_handlers`
bundle-marker assertions (`mermaid-artifact`, `renderMermaid` present in served
HTML + bundled JS). A full server+DB+click-through screenshot is left to the
HS-16-05 closeout dogfood if desired.

## Tests

Extended `tests/integration/test_web_server.py::...test_history_page_*` to assert
the `mermaid-artifact` container + `renderMermaid` hook appear in the served HTML
and the bundled JS (regression lock on the wiring). No new Python module — per
the story, frontend render is carried by manual/visual verification.

```bash
uv run pytest -q tests/integration/test_web_server.py -k history_page   # 1 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                       # 1902 passed, 13 skipped
```

## Security note

mermaid 11.15.0 runs with `securityLevel: 'strict'` (HTML in labels disabled by
default since v9). The diagram source comes from the LLM, not direct user input.
`suppressErrorRendering` keeps mermaid from inserting its own DOM on failure.
`npm audit` reports one high-severity advisory in `devalue` (a build/SSR-tooling
transitive dep, not on the client render path); the site is a static build, so
it is not exploitable here. Not auto-fixed to avoid churning Astro's transitive
versions; revisit at a deliberate dep bump.

## Result

The full pipeline is live end-to-end: transcript → LLM (self-hosted Qwen3.5-9B-Q6)
→ parsed Mermaid → persisted `diagram` artifact body → **rendered SVG in the web
UI**. Phase 16 is 4/5. **Next: HS-16-05** — RFC reality-check + `final-summary.md`
+ phase exit.
