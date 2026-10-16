# Mars scene build

DRAFT — UNCHECKED. HOLD FOR SHIP. Worker implementation after root canvas GO,
2026-10-16. No staging or commits.

New Mars scene uses the local NASA Viking/USGS terrain map, warm ochre
lighting, a soft terminator and a thin atmospheric limb. Phobos and Deimos
have separate deformed, cratered meshes and distinct size, period and phase.
Their paths cross in front of and behind the globe using normal depth. A small
analytic ray shadow permits surface transits. Authored scales and periods are
cinematic, not an ephemeris. No text, HUD, orbit lines or rare-event system.

The small shared `orbitalSky.ts` helper extracts Jupiter's existing local map
and seeded 18,000-star pattern without changing Jupiter. It owns only its two
objects, geometries, materials, texture and image lifecycle. Saturn consumes:

```ts
createOrbitalSky(scene: THREE.Scene, seed: number, onReady: () => void): {
  setDpr(dpr: number): void;
  dispose(): void;
}
```

Both Mars maps refine the still when Motion is off. Planet rotation, moon
paths and rotation, and pointer parallax stop together. Resize preserves a
recognizable whole globe and initial Phobos at 1440 and 393; resolution is
bounded at 1600×1000 and DPR 1.5. Dispose is idempotent and captured image
callbacks become inert.

## Focused proof

Only these three named files were collected, then run, through
`.tmp/orbital-places/locked.py`, with isolated HOME and native state disabled:

- `web/src/desk/gl/__tests__/marsOrbitModel.test.ts` — 3 tests: initial
  foreground Phobos/distinct sizes and speeds; front/back periodic paths;
  framebuffer and DPR bounds.
- `web/src/desk/gl/__tests__/marsOrbitScene.test.ts` — 5 tests: irregular
  meshes/depth/thin limb; portrait and desktop framing; frozen motion and still
  map refinement; local failure fallback; exact resource cleanup/late callbacks.
- `web/src/desk/gl/__tests__/orbitalSky.test.ts` — 3 tests: seeded rich stars
  and bounded DPR; still refinement on image success/failure; owned-resource
  cleanup and late callbacks.

Collection: `.tmp/orbital-places/mars-collect.log`, exit 0, 11 named tests.
Run: `.tmp/orbital-places/mars-run.log`, exit 0:

```text
Test Files  3 passed (3)
     Tests  11 passed (11)
  Duration  802ms
```

An earlier collection could not start because the supplied dependency symlink
lacked Vitest; root repaired the environment before the successful runs.

## Limits

Tests mock WebGLRenderer and controlled image loading; they verify scene
construction and lifecycle, not shader compilation or visual quality. Actual
WebGL shots, live review, preview assets, build and wider integration checks
belong to root. No browser, owner state, stage or commit actions ran here.
