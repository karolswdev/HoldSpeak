# HoldSpeak Web

Astro source for the HoldSpeak web frontend. Builds static HTML/CSS/JS
into `../holdspeak/static/_built/`. The FastAPI runtime serves that
directory under the `/_built` URL mount.

## Why this exists

See `pm/roadmap/holdspeak/phase-10-web-design-system/` — phase 10 is
rebuilding every web route on a real design system (tokens, components,
identity) instead of the five hand-authored HTML files currently in
`holdspeak/static/`.

## Requirements

- Node.js ≥ 20 (only at build time; the deployed runtime stays
  Python/FastAPI).
- npm (bundled with Node).

## Commands

From this directory (`web/`):

```bash
npm install           # one-time
npm run dev           # local Astro dev server with hot reload
npm run build         # produces ../holdspeak/static/_built/
npm run preview       # serve the built output for inspection
```

After `npm run build`, the HoldSpeak runtime serves the built design-check
page at:

```
http://127.0.0.1:<runtime-port>/_built/design/check/
```

## Output contract

- Output goes into `../holdspeak/static/_built/` only. The five legacy
  HTML files at `../holdspeak/static/*.html` are off-limits to this
  pipeline until each route's rebuild story (HS-10-06 through HS-10-09)
  intentionally migrates it.
- Asset URLs are prefixed with `/_built` (Astro `base`) so they resolve
  through the FastAPI mount.
- This pipeline must not introduce any new runtime Python dependency.
  Node is build-time only.

## Source layout

```
web/
├── astro.config.mjs       # outDir = ../holdspeak/static/_built, base = /_built
├── package.json
├── src/
│   ├── pages/             # one .astro per route (Astro file-based routing)
│   │   └── design/check.astro    # HS-10-01 smoke page
│   ├── components/        # populated by HS-10-03
│   ├── layouts/           # populated by HS-10-04
│   └── styles/
│       └── global.css     # placeholder; real tokens land in HS-10-02
└── README.md
```
