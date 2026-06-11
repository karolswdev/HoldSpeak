# Web frontend architecture (the decomposition pattern)

**Status:** canonical for the dictation cockpit; the pattern other pages
should follow when they are carved.
**Established:** Phase 54 (the dictation frontend decomposition).
**Read this if:** you are adding a section to `/dictation`, growing any page's
markup or behavior, or planning to carve another monolith page
(`history.astro` and `index.astro` are the standing follow-up candidates).

---

## The shape

A carved page has three layers:

```
web/src/pages/dictation.astro            the page: a thin composition (spine
                                         markup + spine styles only)
web/src/components/dictation/*.astro     section partials (markup + their own
                                         styles) and markup-less shared-style
                                         components
web/src/scripts/dictation-app.js         the script entry (imports init.js,
                                         documents the module map — nothing else)
web/src/scripts/dictation/*.js           single-concern behavior modules
```

Budgets are locked by `tests/unit/test_frontend_density_guard.py`:
page ≤ 300 lines, entry ≤ 50, every component and module ≤ 600. **When the
guard fires, carve — don't bump.** A file over budget wants a new partial or
module along the seams below; raising a budget is a deliberate, reviewed
decision.

## How a page loads its behavior (the module seam)

Pages historically loaded their app script with
`import src from "../scripts/<page>-app.js?raw"` + `new Function(src)()` — a
Phase-10 migration shim to reuse pre-design-system scripts verbatim. The
dictation page replaced it with a real bundled module:

```astro
<script>
  import "../scripts/dictation-app.js";
</script>
```

Astro emits this as a deferred `type="module"` script — identical timing to
the shim (DOM parsed before execution), but real imports/exports, strict
mode, and build-time rejection of duplicate declarations (the seam caught a
latent duplicate `escapeAttr` the eval had been masking via hoisting).

Two things ride along with the seam:

- **Client chunks ship un-minified.** Astro 6 hardcodes `minify: true` for
  the client environment (ignoring `vite.build.minify`), so
  `web/astro.config.mjs` overrides it with a `configEnvironment` plugin hook.
  Rationale: the bundle is served from a loopback FastAPI mount (size is
  irrelevant), the shim always shipped the full un-minified source anyway
  (as a raw string), readable JS suits a local-first tool, and the
  integration tests assert real source markers in the served chunks.
- **Other pages still use the `?raw` shim.** They keep it until they are
  carved; do not flip a page's loader without also checking its tests (some
  assert source markers that minification or bundling would change).

## Behavior modules

One module per concern under `web/src/scripts/<page>/`. For the dictation
cockpit: `core.js` (shared state, `api`, escape/format utils, the section
switcher), one module per tab (`blocks`, `readiness`, `knowledge`, `runtime`,
`memory`, `journal`, `dryrun`, `agent`), the two nudge systems, and `init.js`
(event wiring + the page-load sequence, executed at module evaluation).

**The one structural idiom — the section-loader registry.** Cross-module
"switch to / reload that section" calls go through `core.js`:

```js
registerSection("kb", loadKB);   // at module evaluation, in the owning module
loadSection("readiness");        // from any module, no direct import
```

This keeps the module graph **acyclic**: every module imports `core.js`;
`core.js` imports no feature module. Direct imports between feature modules
are fine when they don't create a cycle (e.g. `journal.js` imports the
correction ritual from `dryrun.js`). Helpers used by more than one module
live in `core.js`.

Shared mutable state lives in **one** module (`core.js`'s `state`); don't
duplicate it.

## Styles: the attribute-scoping trap and the cascade order

Two rules dominate everything else:

1. **Astro scoped styles never match JS-rendered DOM.** Astro emits scoped
   rules with an `[data-astro-cid-…]` **attribute** selector, and elements
   created at runtime via `innerHTML`/`createElement` don't carry the
   attribute. Phase 54 found shipped UI (block cards, template cards,
   readiness cards, the JS-rendered editor's controls) that had been
   *silently unstyled* for this exact reason. Therefore: **any rule whose
   target is JS-rendered goes in `<style is:global>`** — and the check is
   *who creates the node*, not where the class is written. Verify with a
   screenshot or a computed-style probe; a class existing in the bundle is
   not the same as it applying.
2. **`is:global` is page-contained, but cascade order matters.** Astro only
   ships a component's styles on pages that import it, so global selectors
   don't leak across pages. But rules at equal specificity are resolved by
   emission order, which follows import order. The pattern: markup-less
   shared-style components (`SharedStyles`, `KnowledgeStyles`,
   `DepthControlStyles`) are imported **before** the section partials so
   base primitives emit first and per-section overrides (e.g. `.fixit-yes`
   over `.btn`) keep winning. If you add a shared-style component, import it
   with the others, before any partial.

Static markup that lives in a partial's own template can use normal scoped
`<style>` (the partial's cid attribute is on its template elements).

## Adding a section to the dictation cockpit, step by step

1. **Markup:** create `web/src/components/dictation/<Name>Section.astro`
   with a `<section id="view-<key>" class="view" hidden>` root. Styles for
   its static markup go in a scoped `<style>`; styles for anything its
   module renders at runtime go in `<style is:global>` in the same file.
2. **Page:** import and render it in `dictation.astro` (after the existing
   sections), and add the tab button to the `.cockpit-tabs` row with
   `data-section="<key>"`.
3. **Switcher:** add `"<key>": "view-<key>"` to the `views` map in
   `core.js`'s `activateSection`.
4. **Behavior:** create `web/src/scripts/dictation/<key>.js`; export what
   `init.js` wires; call `registerSection("<key>", load<Name>)` at module
   evaluation if the tab loads data.
5. **Init:** import the module in `init.js` and add its event wiring in the
   wiring block (order is behavior — append, don't interleave).
6. **Verify:** `cd web && npm run build` (some tests read the built bundle),
   run the dictation slice, and screenshot the new tab. The density guard
   and the page-content tests (`test_web_dictation_cockpit.py`'s `_page()` /
   `_app_js()` helpers already read the carved tree) pick the new files up
   automatically.

## Testing notes

- Page-content tests read the **combined source** (page + partials, entry +
  modules) via the `_page()` / `_app_js()` helpers — assertions don't care
  which file a marker lives in.
- Artifact tests read the **served bundle**
  (`_built/_astro/dictation.astro_astro_type_script*.js`, `dictation*.css`);
  they work because the client ships un-minified.
- `holdspeak/static/_built/` is gitignored: edit `web/src`, build, commit
  source only.

## Follow-ups

`history.astro` and `index.astro` (plus their app scripts) still use the
monolith pattern and the `?raw` loader; they are the next candidates for this
treatment when a phase picks them up. Their JS-rendered DOM may have the same
latent attribute-scoping bug — check with a computed-style probe before
assuming their scoped styles apply.
