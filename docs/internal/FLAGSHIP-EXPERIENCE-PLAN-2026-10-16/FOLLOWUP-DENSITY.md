# Density and artifact footer follow-up

Settled direction from the owner's current request; root visually read the
actual-library canvas on 2026-10-16 and authorized the bounded product change.
Direction shots: `.tmp/feedback/canvas/1440-short.png`, `1440-icons.png`,
`393-short.png`. These are direction only, not product validation or owner
acceptance. Tenets 3/5/6/7: fit the
architect's working desk with existing library species and readable words.

Tuesday: open the migration artifact, read it in a short window, then use Copy
or Dictate without first stretching the window. Keep more desktop objects in
view and recover vertical work area from the Dock.

The owner requests most desktop pictures about 25 percent smaller and a
shorter Today/Speak Dock. That current direction supersedes the older source
comment rejecting 24 px Dock rendering. Preview in [canvas-density](canvas-density/README.md)
before implementation; the source sprite assets and text sizes remain.

| Concern | Settled change | Exclusive product files |
| --- | --- | --- |
| Desktop Dock | Shelf 76→60 px; launcher 66→52 px; picture row 36→28 px; picture 32→24 px. Keep 12 px labels. Preserve phone shelf 56 px and tiles 54 px. | `web/src/desk/components/dock.css` |
| Desktop Screen objects | Picture 64→48 px; badge 32→24 px; minimum tile height 96→80 px. Only actual desktop Screen objects, retaining drawer art at 40 px and phone geometry. | `web/src/desk/surface/objects/objects.css` |
| Placement | Drawer/agent row 112→96 px; loose-object row 116→100 px. Preserve 120 px columns, 112 px tile width, and error/caption allowances. | `web/src/desk/screen/layout.ts` |
| Artifact foot | Explicit 4 px block padding, grid height auto/minimum 28 px. Standalone fallback gains `desk-surface-foot`; retain one existing hosted footer, 24 px inline grip reserve and 6 px desktop frame reserve. Body keeps scrolling. | `web/src/desk/surface/SurfaceFooter.tsx`, `web/src/desk/surface/surface-footer.css` |

The geometry lane owns tokens/windowGeometry and updates the work-band reserve
consistently with the 60 px Dock. The reading lane owns document rendering.
Neither file set belongs to this worker. Source anchors can drift during
parallel work; locate declarations by name before editing.

The density lane also sets the existing phone breakpoint's root
`--desk-snap-bottom: 56px` when the geometry lane raises the canonical fallback
to 60 px. This preserves the measured 56 px phone work area. The explicit
footer root padding replaces the narrow grid's old vertical padding; do not
stack both insets.

Source diagnosis: fixed sizes live in `dock.css:81,215,222,243` and
`objects.css:15,27,33,44`; placement in `screen/layout.ts:14–28`.
`surface-footer.css:15–25` already prevents flex shrink but has zero block
padding; its grid at `:50` uses a percentage height on an automatically sized
host. Artifact's unhosted footer comes from `SurfaceFooter.tsx:145`, missing
the frame-foot container/reserve at `window-chrome.css:684–694`.

No test/build/browser jobs or owner HOME/DB/provider/hardware access in the
canvas pass. Root serializes later checks under the machine lock with isolated
HOME. Required later observations: paired populated desktop/393 shots; short
and stretched artifact footer clearance; real pointer hits clear of resize
edges; unchanged phone targets and drawer artwork; correct 60 px work band.
No passing outcome is claimed in this direction record.

Implementation prepared after root's canvas read. Desktop pictures are scoped
to the actual Screen's `data-layout="free"` mode; this follows the Screen's
existing phone/desktop selection without adding a new viewport layout rule.
Existing Screen tests now assert the extra drawer fits in the first column,
the following drawer wraps above TALK, and caption rows keep their extra room.
The shared footer owns its single vertical inset, including write receipts.
`git diff --check` passed. No test/build/browser jobs ran in this worker lane;
root performs the focused suites, ordinary quick check and actual screenshots.

## Root verification

The frozen delivered baseline `a7145045f5dbab3c`, copied into this isolated
worktree, reproduces the owner's footer: the initial 400 px artifact has
0 px above its buttons and 8 px below; after a resize it has 4/4 px. The
upper window clamp is 54 px while the real screen begins at 28 px. Desktop
Dock pictures measure 32 px, Screen pictures 64 px, Dock height 76 px.
See `.tmp/feedback/before1440/observation.json` and the five shots. The
393 px baseline is recorded separately in `.tmp/feedback/before393/`.

These are real isolated graph-walk hubs. Recorded assistant Markdown enters
through Thread import and the production Keep API; no model output or PR
review is claimed. Copy reads the exact saved source. No owner database,
keys, microphone, provider turn or machine preferences enter the walks.

Root read the actual-library short artifact, full object field and phone
canvas before the density worker changed product CSS. The source review by
`density_final_review` is independent Sol counsel, not Muad'Dib's check.
It found no actionable source issue; runtime proof remains separate.

Final frozen candidate `ca987454c0b44162` matches the independently recomputed
source digest. Ordinary quick GREEN (`.tmp/feedback/quick-density-final.log`):
4,168 web tests in 422 files, 109 desktop/phone sweep checks, 17 canon checks.
TypeScript and generated-token consistency pass. The first quick found old
96-px-row test expectations; the final run includes the corrected expectations.
The final canvas also loads at 1440/393 without browser errors
(`.tmp/feedback/canvas-final/`).

Actual product walks: `.tmp/feedback/after1440/` and `after393/` each retain
observations and screenshots. Desktop opens at 400 px, moves down and back to
y=28, resizes to 600 and 320 px, stretches, copies exact source and reloads with
its saved 320×450 rectangle. All button sample points hit the button, with
clearance from the frame. The 56 px phone Dock and 44 px top bar remain; Copy and
More are reachable, and More exposes Dictate. Markdown task emphasis/code
renders; static checklist markers retain their state. Stored artifact reads
match before and after. Neither walk records browser errors.

Independent final Sol counsel RATIFY includes both production image sets and
the final quick output. Root read the actual initial/minimum desktop and phone
shots. Dictate execution is outside this isolated reading/layout walk.

The earlier full main tape 38950387547 finished red (103 failed / 16,327 passed),
with 96 failure names shared with the previous run. Its two known follow-through
wire-fixture field mismatches are prepared for a separate forward fix.
Six other newly observed failures remain unattributed; no full-tape green or
whole-product acceptance is claimed. CDE tape 38957119404 remains in progress.
Normal merge and idle-hub delivery follow this verified candidate.
