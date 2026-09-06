# Environment verification record

Historical implementation and verification material moved from the public Places guide.
The original observations below are retained as recorded. They are not current test results.
See [Places](../ENVIRONMENTS.md) for user controls.

## Review and verification

From `web/`, with a supported Node version:

```sh
npm run dev -- --host 127.0.0.1 --port 4322
```

Open <http://127.0.0.1:4322/_built/atmospheres.html#rainy-city> to browse all
eight scenes without a hub. Choosing a preview does not save it until **Use on my
Floor** is pressed. This dev-only entry uses the actual production scene modules.

In another terminal, from `web/`:

```sh
node scripts/shoot-atmospheres.mjs
node scripts/check-atmospheres.mjs
npm run test:web -- src/desk/gl/__tests__ src/pages/cores/__tests__/settingsWallpaper.test.tsx src/design/AtmospherePreview.test.tsx
npm run test:web -- src/desk/__tests__/settle.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx
npm run tokens:check
npm run tokens:gate
npm run guard:architecture
npm run build
npm run bundle:gate
```

The screenshot script writes full-size PNG review images and compressed WebP
picker assets. Both the gallery and screenshot script use the registry's complete
scenic collection. Browser checks exercise all eight animated and paused scenes,
wraparound, local selection persistence, and both original worlds under reduced
motion in a 393px-wide gallery.
The observed frame rate is local headless-browser evidence, not a hardware-wide
performance guarantee.

For the production-bundle interaction walk, run the preview server and then the
check in separate terminals from `web/`:

```sh
npm exec vite preview -- --host 127.0.0.1 --port 4323
node scripts/check-environments-floor.mjs
node scripts/check-environments-floor.mjs --settle
```

This walk intercepts HTTP APIs with explicit test fixtures in an isolated browser.
It verifies real Pixi object selection through the atmosphere layer and live
Settings selection at desktop and phone widths. It does not test a live hub,
authentication, or WebSocket delivery, and never writes owner Desk data.
The `--settle` walk also verifies favorites across reload, native shortcuts,
Escape preserving the same window and recorder nodes, and hit-tested access to
Back to Desk and Stop above the phone sheet. Its recording state is an explicit
external-recording fixture, not a real session. It asserts zero microphone
requests and zero capture-action API writes.

Evidence lives in [assets/screenshots/environments](../assets/screenshots/environments/),
including the contact sheet, desktop/phone images, and JSON browser reports.

Full TypeScript checking currently encounters pre-existing errors in
`ProjectRoomCore.tsx` and `features/project-room/setup/__tests__/model.test.ts`;
the environment changes add no errors to that output.

## Main integration verification — 2026-09-05

Refreshed PR #528 onto main `855b34cb` while preserving its original history and the newer Concierge/Settings behavior. The Settings hub now exposes Wallpaper and its live selected-place fact. Production controls use the shared Button; favorites use a decorative SVG. The browser harness includes the current Thoughts, needs-you, and Settings hub responses and opens Wallpaper through the current row UI.

Actual output from the complete `npm run check`:

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (703 source files; zero framework residue).
 Test Files  233 passed (233)
      Tests  2220 passed (2220)
bundle gate passed (Desk JS 1255406 B; Desk CSS 297160 B; source maps 0)
```

After the final shared-control and Settings-row corrections: 16 focused control tests passed; TypeScript and a fresh production build passed. The production-browser checks were rerun at 1440 and 393 against that build:

```json
{
  "bundle": "production",
  "backend": "isolated HTTP fixtures",
  "pixiSelection": true,
  "settingsLiveSelection": true,
  "selectedPreviewsLoaded": true,
  "originalWorldsIncluded": true,
  "phoneOverflow": false,
  "errors": []
}
{
  "bundle": "production",
  "backend": "isolated HTTP fixtures",
  "preservedWindow": true,
  "preservedCaptureControl": true,
  "captureReachableOverPhoneSheet": true,
  "favoritesPersist": true,
  "nativeShortcuts": true,
  "escapeRestores": true,
  "phoneOverflow": false
}
```

Screenshots in this directory's linked assets were refreshed and inspected. Logs are in the desktop-delivery worktree's `.tmp/desktop-*` files. The browser checks use isolated HTTP fixtures and do not establish microphone hardware readiness or live-model quality. GitHub's broader Python/macOS jobs run separately; this local evidence does not claim they passed.
