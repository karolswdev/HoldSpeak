# Night Train — root review and checks

Implementation complete, 2026-10-16. Owner judges the live result; formal
postmerge review remains open. This is root's verification of worker output.

## Visual review

Root inspected the old scene and direction canvas at 1440/393 before build.
Root rejected the first implementation's oversized foreground seat, flat
terrain, bright long rain strokes and narrow lake. The second pass gave the
landscape actual shaded relief and a visible lake, with closer framing, fine
glass rain, richer walnut and stronger local lamp light. Final refinement fixed
sky clipping, restored a small seat edge, kept the cup visible on the phone,
rooted station lights in a platform and locked trees to their moving ground.

Final direct actual GL samples at elapsed0/30/90/180 exist under
`.tmp/night-train/after-final/`. Root read initial and180-second compositions at
both widths. These are authored elapsed samples, not natural three-minute waits.
No page or shader console errors were observed. The actual first frame supplies
the new picker/fallback still. Product source hashes match those captures; only
a test mock type cast changed later.

## Focused proof

Root read collection and complete run tails:

- Journey/landscape: 2 files, 7 tests passed,816ms;
  `.tmp/night-train/landscape-final-v3-{collect,run}.log`.
- Compartment/lifecycle: 1 file, 4 tests passed,482ms;
  `.tmp/night-train/compartment-final-v3-{collect,run}.log`.
- Final test-only overloaded canvas mock cast: same file4passed,631ms;
  `.tmp/night-train/compartment-typefix-run.log`.
- Final `tsc --noEmit`: passed with no diagnostics;
  `.tmp/night-train/compartment-typefix-tsc.log`.

The first type check caught that mock overload; it was fixed before delivery.
The renderer/composer are mocked in focused tests. Actual GL checks below cover
shader compilation and rendered behavior.

## Production checks

Full change quick check GREEN against main: production build, 4,133 related web
tests in419files,109Desk sweep checks,17canon guards. The final test-only delta
quick check also GREEN: fresh production build,4related tests,109sweep checks,
17canon guards. Logs: `.tmp/night-train/quick/` and `quick-typefix/`.
Final build `e3f7871900a082c1`; root independently recomputed the exact source
fingerprint and matched it. The outside-source direction/live harnesses were
checked by actual browser captures, not covered by the product quick check.

The local atlas validates against the production schema. Two final actual picker
walks ran one case per `scripts/graph_walk.py` invocation, engine none, with
fresh isolated HOME/DB and native state disabled. Both passed within30s:

-1440: `.tmp/night-train/graph-final-1440/20261017T024500Z-case.desk.wallpaper.train.ready-astra-1440/`.
-393: `.tmp/night-train/graph-final-393/20261017T024543Z-case.desk.wallpaper.train.ready-astra-393/`.

Root read initial feedback separately from settled terminal results, checked
isolated DB provenance, and inspected before/after shots. The real radio choice
persists through close/reload and renders the actual lazy scene; a created
Journey notes drawer remains visible. The phone after-shot includes the
existing Apps/Drawers navigation panel, so direct393captures judge full scene
composition. Walk revision is `e6164f1a3`, dirty=true from the final mock cast
and story records; final bundle/source fingerprint agrees with the delivered
candidate. No scene runtime source changed after direct final captures.

## Actual motion, resize and disposal

`.tmp/night-train/lifecycle-gl/observation.json`: actual shared host visibly
animates, freezes to identical pixels with reduced motion, resumes, and resizes
between1440/393 without page errors. Direct real-scene `setReducedMotion` also
freezes pixels despite explicit later updates and resumes correctly. Double
dispose plus later work is harmless. Renderer counters after disposal report
zero geometries and one texture; the old scene on unchanged Room reports the
same residual texture counter (`baseline-disposal.json`). Room forces context
loss. Owned reflection geometry/material/target and landscape resources are
individually verified once by focused tests; no zero-texture-counter claim.

## Local frame cost and limits

Bounded final measurement used ANGLE Metal on this Apple M2 Max, at1440/1000
and393/852 with requested DPR1/2/3. Existing Room caps actual buffers to about
one million pixels. Across30 measured direct frames per case, CPU-to-GL-finish
median was~0.8ms and p90≤1.3ms;99desktop/97phone submitted calls and~754k
triangles include the reflection pass. Across120 natural RAF intervals per
case, median8.3ms and p90≤9.6ms. Records:
`.tmp/night-train/performance-final/observation.json`.

These are local browser measurements, not a phone-hardware guarantee or a long
battery/thermal run. The scene keeps bounded geometry, a512×320reflection
target, no timers/network assets, and the existing shared scheduler. Motion and
sound controls keep their existing identity; sound was not changed. Rare event
waiting and other atmosphere scenes were not part of this rebuild.
