# Jupiter orbit — delegated source counsel

2026-10-15. Initial round; finished worker source reviewed against
[DESIGN.md](DESIGN.md), the Seven Tenets and the existing Atmosphere contracts.
This is delegated source counsel for root, not Muad'Dib's check, the done call,
or the formal review after merge required by `CLAUDE.md`'s fast cycle.
Product and test files were read only. This counsel ran no test, build,
browser, install, provider or native action.

The initial report below covers the original sparse-sky and rigid-cloud
implementation only. Its line anchors describe that original source snapshot;
its verdict does not cover the owner's later sky/weather amendment. The final
bounded source recheck is recorded after it.

VERDICT: RATIFY — within the finished-source scope.

FINDINGS:

1. No actionable source defect found. The change adds one choice to the
   existing collection and uses its library controls; it adds no new operating
   surface (Tenets 2, 3 and 5). Evidence:
   `web/src/desk/gl/atmosphereRegistry.ts:42`,
   `web/src/desk/gl/atmosphereRegistry.ts:138`,
   `web/src/pages/cores/settingsWallpaper.tsx:43`.

   The four moons are separate spheres with different surface shaders. Their
   authored paths cover both signs of depth and pass across Jupiter's projected
   face; ordinary opaque depth testing hides the rear passes. The narrow
   composition still admits every moon: each continuous foreground half-orbit
   includes local x = -4, which projects inside the 393-wide camera after the
   system's x = 4.35 placement. At that point every moon is in front of the
   planet's surface. This is source reasoning, not a new render observation.
   Evidence: `web/src/desk/gl/jupiterOrbitModel.ts:5`,
   `web/src/desk/gl/jupiterOrbitModel.ts:38`,
   `web/src/desk/gl/jupiterOrbitScene.ts:208`,
   `web/src/desk/gl/jupiterOrbitScene.ts:247`,
   `web/src/desk/gl/jupiterOrbitScene.ts:374`.

   Encounter probabilities are disjoint 2%, 1% and 0.2% bands from a pure
   integer hash. Window zero is empty; duration and offset fit inside the same
   ten-minute window. Construction reads one session salt, layout retains its
   stable seed, and the scene caches one selection per window. Frames sample
   that selection rather than draw another chance. Visitors are hidden outside
   their pass. Evidence: `web/src/desk/gl/jupiterOrbitModel.ts:22`,
   `web/src/desk/gl/jupiterOrbitModel.ts:49`,
   `web/src/desk/gl/jupiterOrbitScene.ts:147`,
   `web/src/desk/gl/jupiterOrbitScene.ts:155`,
   `web/src/desk/gl/jupiterOrbitScene.ts:396`.

   Motion uses the host's active elapsed seconds. Hidden or reduced-motion
   time does not advance that clock; the scene also rejects updates while
   reduced motion is active. A local map completion explicitly renders the
   frozen frame. Error and disposal clear the image callbacks/source; disposal
   is guarded and releases every registered geometry, material, texture and
   renderer once. A captured late load returns before touching released state.
   Evidence: `web/src/desk/gl/atmosphereRuntime.ts:97`,
   `web/src/desk/gl/atmosphereRuntime.ts:123`,
   `web/src/desk/gl/jupiterOrbitScene.ts:342`,
   `web/src/desk/gl/jupiterOrbitScene.ts:383`,
   `web/src/desk/gl/jupiterOrbitScene.ts:417`.

   Render dimensions and DPR are bounded; the scene has no shadow-map or
   postprocessing stack, own animation loop, storage, timer or remote URL.
   Its map is a bundled import and glint is local pixel data (Tenet 1;
   Constitution Article III). Registry loading remains lazy. Quiet Desk still
   has no factory; it remains the default. Existing saved IDs, motion and sound
   storage are unchanged. Evidence: `web/src/desk/gl/jupiterOrbitModel.ts:93`,
   `web/src/desk/gl/jupiterOrbitScene.ts:1`,
   `web/src/desk/gl/jupiterOrbitScene.ts:293`,
   `web/src/desk/gl/atmosphereRegistry.ts:49`,
   `web/src/desk/gl/atmosphereRegistry.ts:55`,
   `web/src/desk/gl/atmosphereRegistry.ts:149`,
   `web/src/desk/gl/atmospherePreference.ts:22`,
   `web/src/desk/gl/atmosphereControls.ts:3`.

CONDITIONS: None for this source counsel. Root retains the quick check,
production verification, release and done call.

MISSED: No additional defect with a concrete cost to the owner was found.
The local preview now exists at
`web/public/desk/atmospheres/jupiter-orbit.webp`; [ASSETS.md](ASSETS.md) records
the NASA/JPL/Space Science Institute credit, source/hash, actual scene preview
and artistic timing/scale limits (`ASSETS.md:5`, `ASSETS.md:24`).

TUESDAY: Source supports choosing Jupiter in the existing Wallpaper collection,
then working with quiet scenery and the same Motion control; root owns the
visual judgment on the running desk (Tenets 3, 6 and 7).

UNKNOWN: I read the real collection and run logs: 11 scene/model tests passed
in `.tmp/jupiter-orbit/scene-run.log`, and 17 integration tests passed in
`.tmp/jupiter-orbit/integration-run.log`. I did not rerun them. Renderer tests
mock WebGL and cannot prove shader appearance. Root reports independently
reading actual 1440/393 scene, moon-phase and all three visitor renders. Their
observation records explicitly fix session salt and sample elapsed time, so
they prove rendered samples, not natural waiting or an observed rare-event
rate. I did not inspect those images, run production/build/quick checks, measure
GPU performance or verify the owner desk here. The inherited host clamps frame
delta to 0.05 seconds: eligibility is measured in its active runtime, as the
design specifies, rather than guaranteed wall-clock minutes at low frame rates
(`web/src/desk/gl/atmosphereRuntime.ts:98`).

## Final source recheck — owner's sky and weather amendment

2026-10-15. One final bounded recheck of the frozen scene/model and their two
focused test files, [DESIGN.md](DESIGN.md)'s amendment and [ASSETS.md](ASSETS.md).
This remains delegated source counsel for root, not Muad'Dib's check or a
formal review after merge. No product/test edit or execution was performed.

VERDICT: RATIFY — amended finished-source scope.

FINDINGS:

1. No actionable source defect found in the amendment. Cloud motion is
   independent of the sphere's rotation: `uCloudTime` drives opposing zonal
   displacement, local paired eddies and a localized storm rotation. Jet
   displacement is bounded by 0.026 UV units; the eddy terms are differences
   of bounded trigonometric values, and storm rotation is multiplied by a
   decaying spatial mask. None integrates displacement or lets shear grow with
   session length. Longitude wraps and latitude clamps; the poles suppress
   jets and eddies. This meets the requested small shader change without a
   simulation framework (Tenets 1 and 6). Evidence:
   `web/src/desk/gl/jupiterOrbitModel.ts:5`,
   `web/src/desk/gl/jupiterOrbitScene.ts:55`,
   `web/src/desk/gl/jupiterOrbitScene.ts:80`,
   `web/src/desk/gl/jupiterOrbitScene.ts:457`.

   The richer sky is a bundled NASA map plus a fixed 18,000-point layer and
   bounded dust shader. Layout RNG is seeded and consumed during construction;
   there is no frame-time global RNG, new animation loop, timer or external
   request. Encounter selection still occurs once per active elapsed window,
   and the small allocation changes preserve the existing moon and visitor
   math. Evidence: `web/src/desk/gl/jupiterOrbitScene.ts:1`,
   `web/src/desk/gl/jupiterOrbitScene.ts:174`,
   `web/src/desk/gl/jupiterOrbitScene.ts:188`,
   `web/src/desk/gl/jupiterOrbitScene.ts:231`,
   `web/src/desk/gl/jupiterOrbitScene.ts:405`,
   `web/src/desk/gl/jupiterOrbitScene.ts:473`.

   Reduced motion returns before changing cloud time, geometry or encounters.
   Both local image completions render even while frozen. Both error paths
   clear callbacks/source and retain procedural scenery. Disposal clears both
   images, then disposes the three registered textures and other owned GPU
   resources once; captured late load callbacks return on `destroyed`.
   Evidence: `web/src/desk/gl/jupiterOrbitScene.ts:409`,
   `web/src/desk/gl/jupiterOrbitScene.ts:458`,
   `web/src/desk/gl/jupiterOrbitScene.ts:494`,
   `web/src/desk/gl/__tests__/jupiterOrbitScene.test.ts:68`,
   `web/src/desk/gl/__tests__/jupiterOrbitScene.test.ts:135`.

CONDITIONS: None within the amended source scope. Root retains the revised
1440/393 and production observations, regenerated fallback, quick check,
release and done call described at `DESIGN.md:98`.

MISSED: No additional concrete owner-cost defect found. The richer-sky source,
credit, hash and artistic framing limits are recorded at `ASSETS.md:45`.

TUESDAY: The amended source adds calm sky detail and weather through the same
wallpaper and Motion control; root must judge legibility and feel on the
running desk (Tenets 3, 6 and 7).

UNKNOWN: I read `.tmp/jupiter-orbit/scene-rich-collect.log` (13 named tests in
the two focused files), the first amended run (12 passed; one signed-zero
matcher failure), and `.tmp/jupiter-orbit/scene-rich-run-final.log` (2 files,
13 tests passed). The test now uses `toBeCloseTo(0)` for zero displacement
(`web/src/desk/gl/__tests__/jupiterOrbitModel.test.ts:41`); no product change was
needed for that matcher failure. I did not rerun any test. The prior 17 green
integration tests cover the unchanged integration only. Root reports revised
1440 shader/timeline samples without errors and has read initial/120-second
renders; revised phone observation and fallback regeneration were still root
work when this recheck began. I have not inspected the revised images,
verified production/quick results, measured GPU performance, or observed a
natural long session. Source bounds prove finite displacement; they do not
prove every long-session storm shape or the owner's visual preference.
