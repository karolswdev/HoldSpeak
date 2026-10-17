# In Mars' orbit; In Saturn's orbit

**Owner amendment 2026-10-16:** [physical moon body sizes](SCALE-CORRECTION.md)
supersede the cinematic-size clauses below.

DRAFT — UNCHECKED. Owner requested2026-10-16. Tuesday: quiet, beautiful
space behind productive work; the owner can notice passing moons without
losing legibility or control. Existing Atmosphere host and choice persistence.
Base5c26bd0fa, wt-orbital-places-20261016, feat/orbital-places-20261016.

## Direction

Mars: rusty terrain from the local NASA Viking/USGS map, recognizable dark
regions/canyons and polar frost, warm sunlight and a very thin cool atmospheric
limb against an actual rich universe. Slow planet rotation. Phobos and Deimos
are distinct irregular cratered grey bodies with different size/speed;
Phobos moves faster, with staggered cinematic passes and real depth occlusion.
A tiny surface transit shadow is desirable if cheap. Both must be findable
over the composed timeline; at least one is initially evident. No HUD/labels
orbits/notifications, no new easter-egg system.

Saturn: a stately warm ivory/gold banded oblate globe; immense finely layered
rings with a real Cassini Division, light through thinner regions, and
planet/ring shadows. Both front and back ring arcs have correct depth. Clouds
move subtly independent of slow rotation. Titan amber/hazy and Enceladus small
ice-white pass at staggered intervals. A rich starfield and irregular galactic
dust continue into the distance. Calm cinematic composition; no giant neon
rim, particle storm, labels or orbital UI.

Both use current Motion/system reduced-motion/hidden-page lifecycle. A frozen
scene still renders and refines local texture loads. Pointer parallax is tiny.
Resize/phone framing preserves planet/rings recognition and visible moon; bound
DPR/render size as Jupiter does. Original planet and star maps remain local,
no runtime network. Authored sizes/periods are cinematic, not an ephemeris.
Jupiter's existing scene/default/saved preferences remain valid.

## Ownership and contracts

Mars lane owns new marsOrbitScene.ts, marsOrbitModel.ts, orbitalSky.ts and its
focused scene/model tests. orbitalSky exports
createOrbitalSky(scene: THREE.Scene, seed: number, onReady: () => void) with
setDpr(number)/dispose(); it owns only sky geometries/materials/local map/late
image load teardown. Reuse the existing local jupiter-starfield.jpg with
credits. Keep this helper small; do not modify Jupiter to absorb it.
Saturn lane owns new saturnOrbitScene.ts/model and focused tests, consuming
that exact sky contract. Integrator owns atmosphereRegistry.ts and focused
existing registry/settingsWallpaper/Atmosphere tests. Root owns design canvas,
NASA map/assets/preview exports, walkthrough, records, commit/PR/deploy.
Workers inspect anchors, use disjoint ownership, hold for SHIP. Root sends
canvas GO before product face code. No stages/commits/build/browser/ownerstate
by workers. Check budget is exact named files under machine lock and isolated
HOME; no broad suite/metal/waiver.

Names and stable IDs: In Mars' orbit /mars-orbit, In Saturn's orbit /saturn-orbit.
Factory exports createMarsOrbitScene /createSaturnOrbitScene. Lazy scene
factories appear after Jupiter in the scenic catalog. Previews are actual
rendered framebuffer stills, not unrelated images; root supplies them.
