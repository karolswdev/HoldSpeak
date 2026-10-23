# Richer desktop icons — 2026-10-22

The owner rejected the first illustrated pass: “they look like toilet bowls”
and “a tiny little bit too basic.” This is a shape and craft correction.
Tenets 5 and 6: one shared family of desktop objects with character, depth
and clear silhouettes. On Tuesday the architect must recognise the object
without reading its label. Owner aesthetic acceptance remains open.

## Settled direction before build

Canvas: `canvases/richer-icons-2026-10-22.html`.

Draw small, rich desktop illustrations in a consistent shallow three-quarter
view. Show an object's front and a narrow right or lower facet. Light comes
from the upper left. Use layered paper, coloured enamel, brushed metal,
small bright edge highlights and compact contact shadows. The silhouette
and two or three structural details carry the meaning at 32px. At 64px add
crafted details, not fake text or random dots. Corners follow the object.

Folders have upright tabs, visible sheets, an angled opening and a strongly
coloured front. No white basin under a rounded blue lid. Agent icons become
distinct head-and-shoulder portraits with visible face panels; no stacked
rounded head over a white drawer. Microphones have a metal grille, coloured
barrel and a proper articulated stand. Settings is a machined gear. Notes,
calendars and books have paper edges and bindings. Chat has overlapping
shaped speech sheets with clear tails. No generic square background tiles.

Palette: navy #263b53 for narrow seams and shade, richer blue #477fe0,
teal #259c96, violet #8870cb and warm amber #ecaa45, with lighter material
stops and cool paper #f8fbff. Avoid uniform thick cartoon casing; outlines
are generally 1.2–1.6 units, structural seams up to 2.2. Use filled facets
for depth. Keep the art within x/y5..58, including shadows and strokes,
so selected rims remain clear. Self-contained 64x64 SVGs; no external refs,
embedded images, fonts, text, filters or animations. `.detail` marks only
fine trim that can disappear at 32px; never hide eyes, content, or an object's
essential construction in the small export. The existing optical exporter
strengthens strokes by 1.15 and hides `.detail` at 32.

All 47 names, 66 base PNG dimensions/URLs, 142 active state files, sampling,
layout and behaviours remain. Old illustrated SVGs and PNGs are preserved
under `web/design/icons/_parked-illustrated-v1-2026-10-22/`. Do not overwrite
the earlier pixel-art archive or rewrite unrelated shell rules.

Delivery seam found during this pass: Vite's frontend build fingerprint
excluded PNGs. Include PNG bytes in the existing source census so a visible
icon-only change gets a new build identity. A focused regression loads the
real Vite config in a private fixture, verifies a stable identity for the
same input, then changes only the PNG and requires a different identity.
This does not change asset URLs or introduce a runtime renderer.

## Work and verification

Worktree `/Users/karol/dev/tools/wt-richer-icons-20261022`, branch
`feat/richer-icons-20261022`, base main9b43917e7. Root owns the direction,
canvas, ledger, proof and delivery. Three Luna workers own world documents
and folders, world people/agents and system/settings respectively; their
briefs name the disjoint files. Anchors drift: locate names. Workers hold
for SHIP and never stage/commit. Workers do not build or export. The system
worker may run only the named build-stamp regression for the delivery seam;
root runs the remaining checks. Root exports
only after all art source is frozen, checks deterministic output, source/URI/
dimensions/alpha/state guards, views contact sheets and actual Ask/Settings
at 1440/393, then runs the required quick before merge/deploy. Full tape and
post-merge review follow CLAUDE.md's fast cycle. Tests/builds use the one
machine lock, isolated HOME and the cached browser/toolchain; no metal test.

Owner-started desk brief: Setup MCP project.list has only PourDecisions,
so no HoldSpeak project.get target applies. memory.search returned no newer
icon direction. The owner's current rejection is the design instruction.
Original owner feedback files remain read-only. Earlier functional failures
and this aesthetic rejection are not closed by an asset-existence test.

Worker correction: an initial path typo created a new untracked
`web/design/icons/world/repository.svg` in the old main checkout. The initial
status had no such path; it had no tracked entry. Only that newly created
file was removed. Root verified the owner's five pre-existing dirty paths
remain present. All intended artwork is in the named worktree and the
earlier family is parked.

## Observed craft checks

The frozen family exports 66 deterministic base PNGs and derives the existing
selected/stale states. All 142 active PNGs changed and have transparent edge
clearance. The parked 47 SVGs and 142 PNGs match preceding main byte-for-byte.
Contact-sheet review corrected a clipped calendar binding and a loop arrow;
the canonical calendar is shared across world/Dock/Settings, Speak across
Dock/Settings, and the violet agent portrait across its object/Dock role.
Fifteen source/asset/registry/container checks pass. Actual Ask and Settings
shots were inspected at 1440/393. The build-stamp regression fails before the
PNG census fix and passes after it; it invokes the real Vite stamp plugin.
Required quick and delivery results are recorded in pm/STATUS.md.
