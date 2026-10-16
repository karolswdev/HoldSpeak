# Mars and Saturn scene review

DRAFT — UNCHECKED — awaiting Muad'Dib. Independent source counsel by the
catalog integration worker, 2026-10-16; this is not Muad'Dib's check.
The reviewer did not author the scene, model or shared sky files. The review
excludes the registry and integration tests authored by this reviewer.

VERDICT: RATIFY

FINDINGS:

1. No blocking scene defect found in this bounded review. The scenes reuse
   the host's motion and visibility lifecycle, without another timer or input
   listener: `web/src/desk/gl/marsOrbitScene.ts:232`,
   `web/src/desk/gl/saturnOrbitScene.ts:253`, and existing
   `web/src/desk/gl/atmosphereRuntime.ts:96`. Reduced motion stops geometry,
   cloud time and parallax; local maps can still refine a still. This follows
   Tenets 1 and 5. Image handlers reject callbacks after teardown, and cleanup
   is idempotent: `marsOrbitScene.ts:197`, `marsOrbitScene.ts:249`,
   `saturnOrbitScene.ts:274`, `orbitalSky.ts:125`, `orbitalSky.ts:147`.
2. Actual 3D paths have distinct phases and periods, rather than projected
   decorative dots: `marsOrbitModel.ts:3`, `marsOrbitModel.ts:13`,
   `saturnOrbitModel.ts:9`, `saturnOrbitModel.ts:21`. Mars' irregular meshes
   and lit foreground Phobos are visible at both widths; the elapsed-180
   shots show the smaller Deimos and partial globe occlusion of Phobos:
   `.tmp/orbital-places/mars-1440/time-0.png`, `mars-1440/time-180.png`,
   `mars-393/time-0.png`, `mars-393/time-180.png`. A transit shadow is visible.
   Titan is initially evident in both Saturn sizes; Enceladus is visible in
   `saturn-1440/time-60.png` and `saturn-393/time-180.png`. Authored scales and
   periods are explicitly cinematic in both models, consistent with DESIGN.
3. Saturn's rear ring arc is hidden by the globe while the front arc crosses
   it in the desktop and phone shots. Rings retain depth testing, transparency
   and a shared density profile for visible layers and their shadow:
   `saturnOrbitScene.ts:31`, `saturnOrbitScene.ts:86`,
   `saturnOrbitScene.ts:121`, `saturnOrbitScene.ts:204`.
   `.tmp/orbital-places/saturn-1440/time-0.png` and
   `saturn-393/time-0.png` show a complete ring span and Cassini gap. The
   narrower ice layers are filtered by pixel footprint at
   `saturnOrbitScene.ts:45`. No depth inversion or shown owner-job cost from
   the visual treatment was found.
4. Both widths preserve planet recognition and an initial moon, with no HUD,
   text or new controls. Warm Mars terrain, restrained limb, warm oblate
   Saturn and the local rich sky match the settled direction. Framing and
   rendering remain bounded: `marsOrbitScene.ts:216`,
   `marsOrbitModel.ts:20`, `saturnOrbitModel.ts:28`,
   `saturnOrbitModel.ts:36`. The shared sky has one seeded 18,000-point
   object, one backdrop and local image loading: `orbitalSky.ts:4`,
   `orbitalSky.ts:80`, `orbitalSky.ts:104`, `orbitalSky.ts:142`.
   This supports Tenets 3, 5 and 6 without changing the product workflow.

CONDITIONS: None from this scene review. Root retains the product quick check,
actual selection/persistence walkthrough and deployment decision.

MISSED: No additional defect with demonstrated owner cost found. The build
records correctly limit mocked-renderer tests to construction and lifecycle;
they do not present them as pixel or shader proof.

TUESDAY: The owner can use either calm, recognizable world behind the Desk;
the full Desk's text and control legibility remain root's product check.

UNKNOWN: I read DESIGN, BUILD-MARS, BUILD-SATURN, the five new scene/model/sky
files, the existing host lifecycle and all four observation JSON files, then
viewed the eight PNGs named above. The four observations report no GL or
console errors at authored elapsed 0/60/180 seconds. These are direct sampled
scene renders, not a claim of natural elapsed waiting. I did not run tests,
builds or a browser, and did not access owner state. I did not independently
review my own catalog integration. Continuous-motion smoothness, measured
frame cost, device thermals, long-running memory use, and Desk chrome/text
contrast cannot be established from these stills and source alone. Root owns
those live-product observations and the final close.
