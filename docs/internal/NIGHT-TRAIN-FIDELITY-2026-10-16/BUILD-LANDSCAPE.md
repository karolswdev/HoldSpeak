# Landscape fidelity correction

DRAFT — UNCHECKED. HOLD FOR SHIP. 2026-10-16.

The worker read the shipped actual 1440/393 captures and the owner's rejection
of the rounded, repetitive mountains before implementing the amended direction.
Worktree `wt-night-train-fidelity-20261016`, branch
`feat/night-train-fidelity-20261016`, base `6a3b8201f`.

`nightTrainJourney.ts` now authors different asymmetric summits, unequal
shoulders, descending rock buttresses, glacial cuts and saddles. Periodic domain
warping and ridged detail add stable relief to those larger landforms. Other
massifs along the long travel interval preserve journey coverage. Low foothills
and shore terrain use smooth seeded shapes. This replaces the former repeated
sinusoidal ridge field.

`nightTrainLandscape.ts` retains four 769 × 41 heightfields: no added terrain
triangles. The local rock shader uses raking directional light, cliff exposure,
restrained strata and grain, high-altitude slope-dependent snow, and aerial
haze. Actual visual quality remains subject to root's rendered review.

The lake replaces uniform bright dash patterns with dark directional sky and
mountain reflection hints and quiet ripples. A synchronous 769 × 1 RGBA data
texture stores skyline heights derived from the two actual mountain fields;
travel offsets keep the sampled reflection aligned. This is a bounded local
approximation, not another rendering pass or renderer.

The old station block is removed. Landscape imports `createTrainStation` from
`./nightTrainStation`, constructs it with `(room, world)`, calls its
`update(time)`, and calls its `dispose()` once. The station lane owns that helper
and its tests. Ground-locked tree travel and construction-time fixed tree
height/scale remain intact. Population stays at 208 tree instances.

The landscape directly owns seven geometries, nine materials, three instance
buffers and one data texture. Its marked moving groups preserve animation
through Room batching. Station resources are delegated to the station helper.

## Actual first-render rejection and correction

Root rejected the first fidelity render after reading
`.tmp/night-train-fidelity/edge-v1/full-1440-0.png` and `full-393-0.png`:
large dark pyramidal masses, visible high terrain cut edges and repetitive lake
bands. The implementation was refined; the first focused green result was not
visual acceptance.

Mountain depth support is now 38/34 m. Mountain height tapers below the lake at
those model boundaries. Existing boundary rows and columns become vertical
skirts down to y=-5, without adding vertices or triangles. The middle mountain
layer is 40% lower and farther back at z=-82; the far hero layer is 12% lower.
Gaussian ridge cross sections and smooth joins replace thin hard arête wedges.
Rock grain, strata, raking light and broken high snow patches were refined.
Lake ripple phase, width and amplitude now vary with bounded local noise.

An independent review then found the terrain triangle winding pointed normals
downward, disabling the slope-based snow and darkening the rock. Winding is
corrected before `computeVertexNormals()`. The focused geometry test now checks
positive normal Y at nine nonboundary interior points on each layer, in addition
to checking below-water skirts and normal variation. The literal-type comparison
in the model test was corrected with numeric coercion.

## Final blue-hour material tuning

Root read the second actual desktop/phone captures: terrain boundaries were
closed and the landforms separated, but corrected normals exposed excessive
brightness. The final bounded pass reduces the directional rock key from 1.02
to 0.56, cools the ambient/key color and increases distant aerial mixing. Snow
uses linear albedo (0.20, 0.24, 0.28), a narrower 18–23 m altitude transition,
broken ledge patches and lower lighting, leaving exposed rock. The far hero
height is reduced a further 15% from the preceding render. The shore tint is
darker and cooler, with a restrained low-rock-to-forest material blend. No
algorithm, topology, resource count or renderer was added in this pass.

## Focused proof

Only the two authorized files were collected, then run through
`.tmp/night-train-fidelity/locked.py`, using isolated HOME, native state disabled
and the machine lock:

- `nightTrainJourney.test.ts`: six tests covering bounded population and
  ground travel, smooth distant recycling, asymmetric summit/saddle height
  differences, full x/z relief, below-water boundaries, periodic joins, and station timing.
- `nightTrainLandscape.test.ts`: three tests covering actual terrain geometry,
  upward normals, below-water skirts and batching protection, local skyline data, station API delegation,
  deterministic explicit updates with stable tree shape, and resource ownership
  with idempotent cleanup.

Collection: `.tmp/night-train-fidelity/landscape-material-collect.log`, exit 0, nine named
tests. Run: `.tmp/night-train-fidelity/landscape-material-run.log`, exit 0:

```text
Test Files  2 passed (2)
     Tests  9 passed (9)
  Duration  1.00s
```

The separately requested `tsc --noEmit` also passed, exit 0, through the same
isolated locked runner: `.tmp/night-train-fidelity/landscape-material-tsc.log`.

## Limits

Tests construct real Three geometry through a lightweight Room substitute and
mock the separately owned station API. They do not compile shaders, render the
scene or accept appearance/performance. Root owns actual captures, moving review,
frame measurements, previews and build. This worker ran no browser, build,
owner-state, staging or commit actions. Product code is held for SHIP.
