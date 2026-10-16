# In Jupiter's orbit

Owner request, 2026-10-15. Base54f028bd6, worktree wt-jupiter-orbit-20261015,
branch feat/jupiter-orbit-20261015. One new choice in the existing Wallpaper
collection. No default or current saved choice changes. Tuesday: can the owner
work calmly while noticing something extraordinary over a long session? Yes:
quiet space, readable objects, slow orbital movement, rare passing discoveries.

## Settled direction

A rich black starfield, restrained cool dust and a huge, dimensional Jupiter
across the right two thirds. NASA Cassini map PIA07782 provides actual cloud
structure and Great Red Spot. A warm sun illuminates the upper left, the
terminator falls into velvet shadow, a thin blue/ivory atmospheric rim traces
the limb. Jupiter turns very slowly. Tiny pointer parallax moves the viewpoint,
never the work or its hit targets. No text, clocks, orbit lines, HUD or labels
inside the scenery. Compose for both1440 and393: on phone the planet may crop
at the right, keeping a strong recognizable limb and foreground moon.

Io, Europa, Ganymede and Callisto are real separate sphere meshes, distinct
sulfur/ice/mottled/crater surfaces, with staggered gentle passes and depth
occlusion. Orbit planes remain near the equator; authored periods approximately
160/240/360/480s and sizes are cinematic, not ephemerides or physical scale.
One moon is initially visible; other passes reward longer presence. A moon
can cross the lit face, disappear behind the planet and emerge. A restrained
transit shadow is desirable if simple. Avoid all four beads arranged in a row.

Rare events: Pioneer with high-gain dish, tripod struts, gold foil body,
outboard RTGs/booms; Voyager-like visitor; an exceptionally rare dark monolith.
Quiet, slow silhouettes with a brief reflected sun glint, no notification or
sound, never giant foreground distractions. Ten-minute eligibility windows,
2% Pioneer /1% Voyager /0.2% monolith, otherwise none; never before ten minutes.
At most one event per window, about45–75s of travel, rest fully offscreen.
Probability is selected once per window by pure seeded math, never per frame.
A fresh session salt avoids the same surprise for every owner on every reload;
layout remains seeded. Use runtime elapsed time: hidden/reduced-motion time does
not advance surprises. No storage, timer service, analytics or public debug UI.

Reuse Atmosphere lifecycle, saved Motion and system reduced motion. No motion
while paused, no scene in Quiet. Bound DPR and render size, no enormous shadow
map or new postprocessing stack. All textures local; no runtime remote requests.
Texture load may refine an immediately drawn procedural planet, must render
when paused and release on error/dispose, including late loads. Dispose all
geometries/materials/textures/renderer once. Do not import interior Room kit or
rainy-city just for RNG. No new shared framework or dependencies.

## Lanes and ownership

Scene worker: new web/src/desk/gl/jupiterOrbitScene.ts, a small companion
jupiterOrbitModel.ts if useful, focused new __tests__/jupiterOrbit*.test.ts,
BUILD-SCENE.md. Root owns NASA texture, canvas, verification rigs and records.
Integration worker: gl/atmosphereRegistry.ts, existing registry test,
pages/cores/__tests__/settingsWallpaper.test.tsx, gl/__tests__/Atmosphere.test.tsx
only if needed for real selection coverage, and BUILD-INTEGRATION.md. Existing
Settings components, Screen, runtime, motion/sound persistence are not owned.
Root creates still preview from the actual scene, writes source credits/docs,
runs build/typecheck/quick, production observations and PR/deployment.

All anchors can drift: inspect current files. Workers implement this direction
and hold for root's canvas-read GO before product code. They run only named
focused test files via .tmp/jupiter-orbit/locked.py, collect before run and
record actual output. No build/install/browser, no owner HOME/DB, Keychain,
clipboard, microphone, native tmux/provider/model. No stage/commit. HOLD FOR SHIP.
Root runs the complete quick check, reads1440/393 shots, production choice and
motion/fallback, accelerated isolated timelines for all moon and rare-event
geometry (explicit time/RNG substitutions, not observed natural waiting).
Fast-cycle merge follows green quick; formal postmerge review is separate.

## Asset sources

NASA/JPL/Space Science Institute, Cassini PIA07782:
https://science.nasa.gov/photojournal/cassinis-best-maps-of-jupiter-cylindrical-map/
Local texture web/src/desk/gl/textures/jupiter-cassini.jpg, original441285bytes,
SHA2566b835ddd8036ea9efd25def04f75aa60b69b096025a37eeae5e9b6978e0a2281.
NASA moon reference: https://science.nasa.gov/jupiter/jupiter-moons/
Pioneer reference: https://science.nasa.gov/3d-resources/pioneer/
These establish visual references. Timing, scale and encounters are authored.

## Owner's live-preview amendment — stars and living weather

After seeing the actual first render, the owner asked for the actual universe
and visibly moving convection/cloud streams. Original source counsel covers
that first implementation only. Revised direction: a rich, deep starfield
with NASA's local galactic-coordinate Deep Star Map as grounding, a visible
irregular Milky Way and dark dust lanes, varied warm/cool star sizes and a few
restrained bright points. The sky stays calm and behind readable Desk icons;
no hard twinkling/strobes or bright lens flare. Decorative point layers may
add depth, without claiming exact present astrometry.

The cloud map must evolve independently of rigid planetary rotation: opposing
latitude-dependent jets, bounded gentle turbulent UV advection, and local
storm circulation. Preserve recognizable Great Red Spot/cloud detail. No
unbounded shear over a long workday, no reset seams or whole-map conveyor-belt
look. Use existing elapsed time; Motion off/reduced motion freeze all weather.
No new renderer/timer, simulation framework, ping-pong render targets or CFD.
A shader time uniform plus bounded analytic flow earns this visible behavior.
The same worker owns this amendment and extends only its exact focused tests.
Root must reread actual revised1440/393, regenerate fallback, rerun production
motion/controls/graph and quick. The old production1440 observation belongs to
the original version, not to this revision.
