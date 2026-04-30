# HS-10-13 evidence — Designer handoff refresh + phase exit

## Files shipped

- `designer-handoff/screenshots/{dashboard,activity,activity-mobile,history,dictation}-desktop.png`
  — fresh captures of the rebuilt frontend taken via
  `designer-handoff/capture-screenshots.py --base-url
  http://127.0.0.1:4321/_built` against the running Astro dev
  server.
- `designer-handoff/style-handoff.md` — rewritten "Current Visual
  Language" against the actual phase-10 token set; documents the
  full component library now in `web/src/components/`; closes every
  open style question (unified dark theme stays; nav is unified;
  local-only grammar is `LocalPill`; command previews use
  `CommandPreview`; candidate state uses the `Pill` tone palette);
  explicitly defers light theme, per-route hero illustrations,
  and route-level transitions.
- `designer-handoff/ux-inventory.md` — replaces the legacy
  per-surface gap list with a short "what's left" punch list
  (connector packs in phase 11; dictation editor density), and a
  "what was closed in phase 10" section that names each shared
  component now backing the surfaces.
- `designer-handoff/screenshot-index.md` — capture date bumped to
  2026-04-29 and notes the dual `--base-url` mode (Astro dev OR
  holdspeak runtime).
- `designer-handoff/functional-handoff.md` — minimal touch:
  `/settings` collapsed into the `/history` Settings tab to match
  reality; added a one-paragraph note that phase 10 unified the
  navigation layout under `AppLayout` + `TopNav`. Workflow text
  intentionally untouched (this rebuild is presentation-only).

## Phase DoD checklist

- [x] **All HS-10-01..12 stories `done` with evidence files.** Story
  table in `current-phase-status.md` is fully populated; every row
  links to an `evidence-story-{n}.md` file in the same folder.
- [x] **`current-phase-status.md` story table updated.** Status flips
  + "Last updated" line both bumped in this commit.
- [x] **`pm/roadmap/holdspeak/README.md` "Last updated" bumped.**
  Done in this commit.
- [x] **No `<style>` block remains inline in any served page.** The
  legacy hand-authored `holdspeak/static/{dashboard,activity,
  history,dictation,dictation-runtime-setup}.html` files were
  removed in HS-10-06..09. The only `<style>` tags in the served
  output now come from Astro's component-scoped style emission
  (e.g. `<style>.hold-mark[data-astro-cid-3bbjgryf]{...}</style>`),
  which is the framework's intended mechanism — these styles are
  emitted *from* `<style>` blocks inside `.astro` components and
  scoped via attribute selectors. The story called this out
  explicitly: "the evidence file documents what the grep should
  look like in the new pipeline."

  ```
  $ find holdspeak/static -maxdepth 2 -type f
  holdspeak/static/_built/index.html
  holdspeak/static/_built/apple-touch-icon.png
  holdspeak/static/_built/favicon.svg
  ```

  All five legacy hand-rolled HTML files (combined ~7,743 lines)
  are gone; the only sources under `holdspeak/static/` are now the
  Astro build output (`_built/`).

- [x] **No legacy hand-authored HTML in `holdspeak/static/` source
  ownership.** Verified above.
- [x] **Roadmap README updated with phase-10 completion.** Phase 10
  flipped to `done` in the project README's phase index.

## Open style questions — resolved or deferred

| Question | Resolution |
|---|---|
| Unified dark theme, or light + dark tokens now? | Stays dark-only for v0.2.0; light theme deferred. |
| Should activity, history, dictation share one global nav? | Yes — `TopNav` mounted by `AppLayout` is the only nav. |
| Visual grammar for "local-only" status? | `LocalPill.astro` with the `local` Pill tone. |
| How to display connector command previews? | `CommandPreview.astro` — `<figure>` + tone-edge accent + copy. |
| How to visualize meeting candidate state? | Reuses the `Pill` tone palette (info / success / warn / neutral). |
| Page-level transitions / route animations? | Out of scope — explicitly deferred per HS-10-12 ("conflicts with calm and precise"). |

## Tests

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1184 passed, 13 skipped in 26.98s
```

## Build

```
$ npm run build
…
[build] 7 page(s) built in 707ms
[build] Complete!
```

(Build was last clean as of HS-10-12; no source code changed in
this story.)

## Phase exit

Phase 10 is **done**. The product graduates to phase 11 (Local
Connector Ecosystem), which can build on top of the component
library, the `ConfirmDialog` pattern, the `CommandPreview`
component, and the `Pill` tone palette without needing to invent
new visual language for `gh` / `jira` / future connector packs.
