# Physical moon size correction

Owner feedback 2026-10-16 supersedes the original cinematic-size direction.
The original bodies were deliberately enlarged for visibility; this was the
wrong choice. All eight natural moons now use measured body radius ratios.
Orbital distances, periods and phases remain authored; this is not an ephemeris.

Sources read 2026-10-16:
[planet physical parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html) and
[satellite physical parameters](https://ssd.jpl.nasa.gov/sats/phys_par/), NASA/JPL.

| Scene | Host radius convention, km | Moon mean radii, km |
| --- | --- | --- |
| Mars | Spherical mean, 3389.50 | Phobos 11.08; Deimos 6.2 |
| Jupiter | Spherical mean, 69911 | Io 1821.49; Europa 1560.80; Ganymede 2631.20; Callisto 2410.30 |
| Saturn | Oblate equatorial, 60268 | Titan 2574.76; Enceladus 252.10 |

Scene moon radius = scene host radius × physical moon radius / physical host
radius. No minimum pixel size, visibility boost, enlarged point or sprite is
introduced. Orthographic cameras preserve these ratios independent of depth.
Mars retains irregular shape with exact equivalent-volume normalization.
Existing shadow penumbrae and Titan's thin haze shrink with the corrected
radius; no photometrically exact shadow or atmosphere claim is made.

Independent integration-worker source counsel found no blocker; it is not
Muad'Dib's check. Counsel checked model-to-mesh radii, unit transforms, actual
Mars volume normalization, tests and shadow inputs. Root owns real GL renders,
regenerated previews, quick checks and deployment. Formal review remains open.

## Jupiter and Saturn

Jupiter's four sphere radii now derive from its mean radius and the four moon
mean radii above. The rare visitors, weather, camera, star map and motion host
are unchanged. Saturn's two sphere radii derive from its equatorial radius;
its existing oblate planet, rings and haze construction are unchanged.
Saturn focused collection/run: 2 files, 8 tests passed; logs under
`.tmp/orbital-places/scale-saturn-{collect,run}.log`.

## Mars correction — worker record

DRAFT — UNCHECKED. HOLD FOR SHIP. 2026-10-16.

Body sizes now use physical relative mean radii. Mars is 3389.50 km;
Phobos has equivalent-volume mean radius 11.08 km and Deimos 6.2 km.
Root supplied and verified the NASA/JPL values from
[planet physical parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html)
and [satellite physical parameters](https://ssd.jpl.nasa.gov/sats/phys_par/).

`marsOrbitModel.ts` exports `MARS_MEAN_RADIUS_KM` and retains each moon's
`physicalRadiusKm`. Each scene radius is exactly
`MARS_RADIUS * physicalRadiusKm / MARS_MEAN_RADIUS_KM`: approximately
0.01618 scene units for Phobos and 0.009054 for Deimos, with Mars at 4.95.
Orbit distances, periods and phases remain authored cinematic values.

`marsOrbitScene.ts` retains the irregular relief. It welds the duplicated
longitude seam and pole positions, sums signed tetrahedron volumes over the
closed indexed surface, and uniformly scales the completed geometry to the
volume of a sphere with its mapped physical radius. Thus ellipsoid shaping
and craters no longer alter equivalent volume. Moon meshes and their parent
keep unit scale; the orthographic camera gives no distance enlargement.
The existing transit shadow takes the corrected radius directly. No point,
sprite, glow, minimum pixel size or visibility enlargement was added.

The two existing focused test files now assert the physical radius ratios,
actual rendered triangle volumes, exact seam and pole closure, unit object
scales, the orthographic camera, and corrected shadow radii. Collected and ran only these two named files through the supplied
`.tmp/orbital-places/locked.py`, with isolated HOME, native state disabled and
the machine lock. Collection: `.tmp/orbital-places/scale-mars-collect.log`,
exit 0, 10 named tests. Run: `.tmp/orbital-places/scale-mars-run.log`, exit 0:

```text
Test Files  2 passed (2)
     Tests  10 passed (10)
  Duration  572ms
```

Actual volume assertions compare independently summed rendered triangle
volumes to physical sphere volumes with relative tolerance 1e-6. No build,
browser, stage or commit.

## Release verification — #1230

PR [#1230](https://github.com/karolswdev/HoldSpeak/pull/1230), base `58effbd4e`,
worktree `wt-orbital-scale-20261016`, branch `fix/orbital-scale-20261016`.
Frozen build `99ecedf6825c8597`; independently recomputed source digest matches.
TypeScript exits 0. Final quick GREEN: 4,119 tests in 420 web files, 705 affected
Python checks, 109 Desk sweep cases, 17 canon checks. No full-tape green claim.
Logs: `.tmp/orbital-places/quick-scale.log`, `quick-scale/`, `typecheck-scale.log`.
Jupiter focused tests: 14 passed in two files; `scale-jupiter-{collect,run}.log`.

Actual product factories rendered at 1440×1000 and 393×852, authored elapsed
0/60/180: all six observations pass with no page or GL console errors.
Root inspected the six initial images. Outputs:
`.tmp/orbital-places/scale-{mars,saturn,jupiter}-{1440,393}/`.
All three actual framebuffer exports replace the picker/fallback WebP files;
these are corrected scene exports, not sketches. The original build's
large-moon previews are superseded.

Real picker and first-frame readiness pass on isolated production hubs at
1440 and 393 through `scripts/graph_walk.py`, with native pointer/touch,
engine none, fresh HOME/DB and real clocks. Root read initial feedback,
settled outcomes, isolation/provenance, and before/after shots.
Observations: `.tmp/orbital-places/graph-scale-mars-{1440,393}/<run-id>/`.
Product revision is `8c86323af558b34e65e6da7651d3138c83a1cc8f`, dirty=true
(untracked dependency symlink; later records only). The local atlas retains
Saturn and declares Jupiter readiness, but those selector cases were not
rerun for this constant correction. Their actual GL scenes and model ratios
were verified at both widths. Motion/fallback behavior carries the prior
#1229 host proof; no runtime/control logic changed.

Normal owner-hub delivery follows merge and an idle runtime check, separately
from isolated verification. Earlier port61862 scene links redirect to the new
corrected live preview on57047. Preview/live serving trees are retained.
Formal postmerge review and owner aesthetic judgment remain open.
