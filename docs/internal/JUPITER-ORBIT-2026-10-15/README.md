# In Jupiter's orbit

Owner request2026-10-15; base54f028bd6, isolated worktree
wt-jupiter-orbit-20261015, branch feat/jupiter-orbit-20261015.
[Direction and live-preview amendment](DESIGN.md), [asset credits](ASSETS.md),
[scene worker](BUILD-SCENE.md), [integration worker](BUILD-INTEGRATION.md),
[bounded source counsel](REVIEW.md).

## Intent and scope

One new Wallpaper choice on the current Desk. A dimensional Jupiter, separate
Galilean moon spheres, subtle pointer depth and rare geometric visitors. The
owner reviewed the first render and asked for a real sense of the universe
and cloud convection. That amended direction adds a richer local NASA sky map,
galactic dust/star depth and independently flowing cloud belts/turbulence.
Existing default/saved choice, Settings controls, Motion, reduced motion,
visibility suspension and quiet sound behavior remain the existing contracts.
No backend/API/storage model or animation framework is added. NASA assets are
bundled locally; their source/credit/hash and artistic-scale limits are in
ASSETS.md. Timing and geometry are authored, not present ephemerides.

## Initial implementation and observations

Root rendered/read the component-library direction at1440/393 before build.
Two workers implemented the scene and its catalog integration in disjoint
files. Exact focused collection/run proof was read: initial scene/model11 in
two files, integration17 in three files, all passed. TypeScript and build
passed. The first exported preview was a cleared-framebuffer image; root
noticed and discarded it before product build, then exported and read a real
freshly rendered frame. No preview was synthesized from a product claim.

`scene-first-1440/` and `scene-first-393/` contain actual production-factory
renders at eight timeline points and all three rare visitor types, with no
page or shader errors. Root read initial/phase/spacecraft shots at both widths.
These are direct elapsed-time samples with session salt fixed0 at the crypto
boundary: they establish visual geometry, not natural waiting or live rarity.
Rarity is separately asserted through the pure per-window model. No production
debug control was added. The standalone live preview uses the unchanged real
Atmosphere runtime and actual scene factory without those substitutions.

The initial `production-1440/` walk captured six states with no page errors:
real Settings radio selection and restore, changing nonblank framebuffer,
actual drawer opening/hit ownership over the scene, persisted Motion off,
reduced motion and Quiet releasing the host. It belongs to the first version
before the owner's sky/weather amendment and does not verify that amendment.
The first source counsel likewise covers the original finished source only.

After the owner requested richer space/weather, root read the revised NASA
star-map library direction at both widths before the worker's amendment GO.
Final shader/product/graph/quick results are recorded below once complete.

## Verification boundaries

Tests/walks use fresh isolated HOME/DB under the machine lock, engine none,
and no owner DB, microphone, Keychain, clipboard, provider or owner tmux.
Normal local hub deployment is a separate final step after merge. Browser
rendering here uses software WebGL; it does not establish hardware performance
or owner acceptance. No remote CI green, full main tape or formal postmerge
review is inferred. Timelines for rare visitors are accelerated observations;
no one claims to have waited naturally for the rare event.

## Amended finished-source and production proof

The revised exact scene/model scope collected13 and passed13 in two files.
Its first run passed12 and failed a signed-zero matcher (`-0` versus `0`) in
one new bound assertion; using `toBeCloseTo(0)` corrected that test, with no
product fix for it. Root read the names and actual final tail in
`scene-rich-collect.log` and `scene-rich-run-final.log`. Integration's17 tests
remain green in the unchanged three-file scope. Release TypeScript and build
passed after the amendment. Final bounded source counsel RATIFY is separately
labelled in REVIEW.md; it does not stand in for formal postmerge review.

`scene-rich-1440/` and `scene-rich-393/` captured eight authored-time samples
and all three visitor renders with no page/shader errors. Root read the new
starfield, cloud-phase and Pioneer shots. This uses the same explicit fixed
salt/time boundary as the first direct-scene run. Root regenerated and read
the final1440×1000 preview from the amended production factory at elapsed0;
it is200766bytes. The canvas directions and source render/live preview are
outside quick-check coverage; they were rendered separately. Weather is
bounded shader advection and storm circulation, not a fluid simulation.

`production-rich-1440/` and `production-rich-393/` each captured six actual
product states, build `4e9308a2ae4cc5ff`, with no page errors or external
requests. The real Wallpaper radio selects and persists Jupiter. Reload keeps
one ready canvas, with nonblank changing framebuffer fingerprints. Real
mouse/touch opens an actual stored drawer over it, whose center hit point
belongs to the control. Root read the Desk/drawer shots and observations.
Motion off persists and the visible Desk pixels stay equal; OS reduced motion
also freezes the visible sample. Quiet removes the host. Phone Go covers much
of the sky with its existing rows; framebuffer motion, visible gaps, isolated
full-scene renders and focused lifecycle assertions are distinct evidence.

Actual WebGL-disabled browsers at both widths show the selected still and
failed host rather than a blank Desk. No page errors or external requests.
Outputs `fallback-rich-1440/`, `fallback-rich-393/`; root read the desktop
fallback shot. This deliberately degraded browser environment is declared.

## Official choice case

`case.desk.wallpaper.jupiter.ready` passed once per width, with fresh isolated
HOME/DB, engine none, no substitutions, source54f028bd6 plus dirty lane edits.
Root read each observation's provenance, initial and terminal result, then
both before/after shots before proceeding. Actual pointer at1440 and native
touch at393 choose the real library radio. The existing host loads local
Jupiter/Three modules and both local image assets, then reports its first
successful render: desktop first1.008s/settled1.671s, phone
first1.350s/settled1.552s, inside30s. This readiness predicate proves first
render, not rare waiting, hardware performance or pointer ownership by the
decorative canvas. Background hit tests correctly belong to work above it.
Outputs are `graph-jupiter-1440/` and `graph-jupiter-393/`.

Affected architecture/atlas/document claims collected/passed651. Generated
capability docs check passes; graph join check passes with14 existing subtype
notes. Current Places guide documents the choice, real Motion path and authored
scale/timing, and corrects its inherited incorrect Rainy City default.

## Wider catalog regression alignment

The first complete quick check correctly returned RED: six older Places/design
preview assertions fixed the collection at eight scenes, last Laundromat and
08 counters. Actual rendered output included the new Jupiter choice. Its
other results were3809 web passes,651 affected Python passes,107 Desk sweeps
(two existing xfails),17 canon passes. No result was waived. Root read the
actual failure log and extended the integration worker's scope to exactly
ChangePlacesCore.test.tsx and AtmospherePreview.test.tsx, with no product edit.
The exact old scope reproduced6failed/9passed; revised collection/run passed21
in two files. Expectations now compare the real catalog's rendered membership,
order/wrap and positions, explicitly include Jupiter, and test every scenic
direct link, retaining current-workspace, favorites and fallback assertions.
Root read both test diffs, collection and real tail. This test-only alignment
follows the completed source counsel and is not attributed to its verdict.

The standalone user-facing preview was also observed independently at
`live-preview-check/`: actual shared runtime, no entropy/time substitutions,
nonblank changing framebuffer samples and no page errors. The preview server
on 4488 is retained because the owner asked to see and use it while the release
check runs. This does not mutate the owner hub or store.

## Release — #1213

[PR #1213](https://github.com/karolswdev/HoldSpeak/pull/1213) carries the
original scene and the owner's richer-universe/flowing-weather amendment.
The final complete quick check is GREEN: 3821 web tests in 406 files,
651 affected Python assertions, 107 Desk sweeps (two existing xfails), and
17 canon guards. Root read the actual log and exit 0. Release TypeScript also
exited0. Logs: `.tmp/jupiter-orbit/quick-release.log` and
`.tmp/jupiter-orbit/typecheck-release.log`. The final build is
`05aaf13be67d3ff5`. Actual amended product walks used `4e9308a2ae4cc5ff`;
the later rebuild followed test-only catalog alignment, with no product-source
change. This distinction does not claim a new live walk against the final tag.

The normal owner hub redeploy follows merge. Its exact source, merge/tree,
served build, PID and warm runtime observations belong in the untracked
`LOCAL-HUB.md` in this retained serving worktree. No authenticated token is
recorded there. The standalone preview on 4488 is retained for the owner.
Delegated source counsel is separate from formal postmerge review, full main
tape, remote CI, owner acceptance, hardware performance and natural rare-event
waiting; none of those is inferred from these checks.
