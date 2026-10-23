# Illustrated icons — 2026-10-22

Owner: the modern shell is better, but its icons need a substantial improvement.
The owner chose “Crisp illustrated icons (recommended)” after the explicit
choice between illustrated, line and refined pixel art. This supersedes the
older D1 hard-pixel material prescription for this family. Workbench object
semantics, state images, labels and the common component framework remain.
Tenets 3, 5, 6 and 7: can the architect find an app by silhouette on Tuesday?

## Direction settled before build

Canvas: canvases/illustrated-icons-2026-10-22.html.
Vector-authored illustrations, transparent background, one clear object per
meaning. Slate outline #263b53, cool paper #f8fbff, blue #5b8fe8, teal #42ad9e,
small amber #f2b35b and violet #9580d7 accents. Restrained two-tone depth,
rounded joins, consistent light from top left. No black casing, pixel noise,
faux text, tiny hatching, emoji, copied brand marks or generic square tiles.
Large silhouette fills approximately 48–52 of a 64-unit artboard, leaving
room for selection/state rims. Each icon should read at 24/32 before detail.
Use an optical 32-unit export: increase outline and suppress fine detail,
rather than shrinking the full detailed picture. Small menu/mic glyphs use
bolder simpler silhouettes. Rest, selected and stale retain the same object.

The existing PNG URI/dimension contract remains for DOM, states and GPU:
64 world, 32 row/system/Settings assets (wallpaper keeps its existing 64). SVG originals are the shared
source, with deterministic browser raster exports; existing state derivation
remains. Smooth DOM and GPU sampling replaces pixel-nearest sampling for
this illustrated family. No new icon package or runtime renderer. Dock app
pictures become 32px on desktop, inside its existing 60px working band.

## Scope and lanes

Worktree /Users/karol/dev/tools/wt-illustrated-icons-20261022, branch
feat/illustrated-icons-20261022 from main937d7ea5c. Root owns this direction,
canvas, verification, docs, tracker/status and delivery. World artist owns
19 SVG originals under web/design/icons/world/. System artist owns the
20 system and 8 Settings originals under web/design/icons/{system,settings}/.
Integration worker owns deterministic export script, shared icon rendering
CSS and the GPU sampler. Workers do not edit one another's files, run tests,
build, stage or commit; root freezes source before generation/checks. Anchors
drift: locate symbols. Hold for SHIP. Read-only desk brief through installed
MCP found no HoldSpeak project (project.get inapplicable), and memory.search
returned no newer icon direction. Owner-started session.

Retain old originals under an explicitly parked source directory before
replacing them; never remove historical art. Asset/state existence, alpha,
size and identity guards remain. Required quick, screenshots at1440/393,
merge/deploy exact main, post-merge review, then pinned full tape. Owner
visual acceptance stays open; existing functional feedback stays tracked.

## Verification and fix-forward scope

The preceding main937d7ea5c tape completed red (12 Python, 25 browser, one
web). This pass also repairs its new shared-shell corner hit ownership,
disabled contrast, menu-label clipping and media-rule placement defects. The
visual readers adopt the already settled 32px desktop/44px phone Button,
pale selection and CSS4 colour serialization. Nine-point real pointer checks,
clipping/gray-only negative controls, semantic state and 4.5:1 floors remain.
The strict feedback check also exposed the generic pressed Button's excessive
selector specificity overriding Send's own selected state. That common rule
now leaves room for owner selection while retaining its priority over hover.
Arrange-all waits for the asynchronously loaded project title before reading
the name-based order; its size and order assertions remain exact.

The 142 previous active PNGs are parked byte-for-byte against main937d7ea5c.
The new 142 active PNGs have transparent edge clearance, including selected
rims. Fifteen focused source/asset/registry/container-law checks and typecheck
pass. Two frozen-source export/check cycles agree on all 66 base images;
state derivation remains the existing shared algorithm. Contact-sheet review
corrected two top-edge antenna details and dark-background microphone yokes.
Required quick and rendered-window results are recorded in pm/STATUS.md at
delivery; no whole-suite green or owner aesthetic acceptance is inferred.
