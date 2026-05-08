# HS-16-04 — Web: render `mermaid` artifacts as inline SVG via mermaid.js

- **Project:** holdspeak
- **Phase:** 16
- **Status:** backlog
- **Depends on:** HS-16-01, HS-16-03
- **Unblocks:** HS-16-05
- **Owner:** unassigned

## Problem

After HS-16-03, an artifact with `artifact_type="diagram"` has a
`body_markdown` containing a fenced ```mermaid block. The web
artifact-detail surface currently renders markdown via the existing
markdown pipeline (`web/src/...`), which leaves fenced blocks as
`<pre><code>` text. The user sees raw Mermaid syntax instead of a
diagram.

This story integrates `mermaid.js` into the web bundle and renders
`mermaid` fenced blocks as live SVG when an artifact-detail view
mounts. Mermaid is loaded only on routes that actually have a
diagram artifact (lazy-load) so the home / dictation pages don't
pay the bundle-size cost.

## Scope

- **In:**
  - Add `mermaid` as a dependency in `web/package.json`. Pin the
    version; document why in the story evidence.
  - Find the artifact-detail rendering component in `web/src/`
    (likely under `web/src/components/` or `web/src/pages/`).
    Add a hook (Astro / Alpine — match the existing pattern) that
    after the markdown body is rendered:
    1. Selects `pre code.language-mermaid` (or whatever class the
       current markdown pipeline emits for fenced ```mermaid).
    2. For each match, dynamically `import('mermaid')` (lazy),
       call `mermaid.run({ nodes: [match] })`, and on success
       replace the `<pre><code>` block with the rendered SVG.
    3. On render error (invalid Mermaid), leave the original
       `<pre><code>` in place AND prepend a small inline warning
       (`<div class="mermaid-render-error">Diagram could not be
       rendered — showing source.</div>`).
  - Style the rendered diagram so it scales to the artifact card
    width — `svg { max-width: 100%; height: auto; }` scoped to
    the artifact body container.
  - Lazy-load: mermaid.js is `import()`'d only inside the
    artifact-detail path; verify by building the site
    (`npm run build` in `web/`) and grepping the home / dictation
    bundles for `mermaid` — should not appear.
  - Manual evidence: open a meeting that has a `diagram`
    artifact (use the integration-test fixture from HS-16-01 or
    a hand-crafted SQLite row), screenshot the rendered diagram,
    save under
    `pm/roadmap/holdspeak/phase-16-first-real-plugin/evidence/mermaid_rendered.png`.

- **Out:**
  - Editing the diagram in the web UI. Read-only render only.
  - Per-theme styling of the diagram (dark-mode polish, custom
    colors). Default Mermaid theme is fine for this phase.
  - Server-side rendering of the SVG (would let us cache the
    rendered output and skip the client bundle, but adds a
    headless-browser dependency). Out of scope.
  - A non-mermaid renderer fallback (e.g., raw Graphviz). Mermaid
    is the only diagram dialect this phase supports.
  - Catching `mermaid` blocks in artifact previews on the
    meeting list / history pages. Detail view only.

## Acceptance criteria

- [ ] `web/package.json` has `mermaid` as a dependency with a
  pinned version.
- [ ] Opening the meeting-detail page for a meeting with a
  `diagram` artifact shows a rendered SVG diagram in place of
  the fenced text — verified manually with a screenshot in the
  evidence file.
- [ ] If the Mermaid syntax is invalid (intentional negative
  test — hand-craft a broken `mermaid` value in the DB), the
  page shows the raw fenced block with the inline warning, not
  a JS error or a blank page.
- [ ] The rendered SVG scales to fit the artifact card width on
  both desktop (≥ 1024 px) and mobile-emulated (≤ 480 px)
  widths — verified with two screenshots.
- [ ] Building `web/` (`npm run build`) does not include
  `mermaid` in the home or dictation bundle entry chunks. Grep
  the build output to verify (record the grep command + result
  in the evidence file).
- [ ] No regression: other markdown rendering (non-mermaid
  fenced code blocks, headings, lists) renders identically to
  before — verified by visiting the same artifact-detail page
  for a non-diagram artifact and visually comparing.

## Test plan

- Unit / component: if `web/` has a component-test rig, add one
  case verifying the post-render hook locates and replaces a
  `mermaid` block. If no rig exists, skip — manual verification
  carries this story (frontend, per project pattern).
- Build:
  `cd web && npm run build`. Inspect `web/dist/` (or wherever
  the build output lands) for the lazy-load split and the
  bundle-size grep.
- Manual:
  1. Create a meeting fixture with a `diagram` artifact (DB
     insert or use the HS-16-01 integration test artifacts).
  2. `holdspeak` then open the meeting-detail page in the
     browser.
  3. Screenshot the rendered diagram (desktop + mobile widths).
  4. Edit the fixture's `body_markdown` to contain malformed
     Mermaid; reload; screenshot the fallback warning.
  5. Open a non-diagram artifact (e.g., a `plugin_output` from
     a stub plugin) and verify the page still renders cleanly.

## Notes / open questions

- Astro vs client-side hydration: depending on which web
  framework wraps the artifact-detail page, the lazy `import('mermaid')`
  call might need to live in a client-only `<script>` island
  (Astro pattern). Match the existing pattern used by the
  `briefing-markdown.*.js` chunk in
  `holdspeak/static/_built/_astro/`; that's the closest
  precedent.
- Mermaid.js bundle size at the time of writing is ~1 MB
  uncompressed, ~250 KB gzipped. The lazy-load constraint is
  the main mitigation. If the gzipped size on the artifact-
  detail bundle grows by > 80 KB, switch to a CDN script tag
  with SRI per the active-risks table in
  `current-phase-status.md`.
- Security: mermaid.js renders untrusted input client-side and
  has had link-injection issues in the past. The `mermaid` value
  arrives from an LLM, not directly from user input, but we
  should:
  - Run mermaid with `securityLevel: 'strict'` (the default
    since v9 disables HTML in labels).
  - Note in the evidence file which mermaid.js version was
    pinned + verify the version's security defaults.
- If `mermaid.run()` is async and the user navigates away
  mid-render, leftover work should not throw uncaught
  rejections. Wrap the call site to swallow errors after
  unmount.
