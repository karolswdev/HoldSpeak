# Mars and Saturn orbital places

**Size correction:** the owner rejected the enlarged moon bodies after #1229.
[Physical sizes and current verification](SCALE-CORRECTION.md) supersede the
original body-size direction and the historical images described below.

Built for the owner's 2026-10-16 request. Formal review: UNCHECKED — awaiting Muad'Dib. Owner visual acceptance remains open.

## Use

Open **Change places**, then choose **In Mars' orbit** or **In Saturn's orbit**. The existing Motion control and system reduced-motion preference apply. The choices retain the current default and existing saved scenes.

Mars uses local NASA terrain, a thin atmospheric limb, irregular Phobos and Deimos, independent moon paths, depth occlusion and transit shadows. Saturn uses warm flowing bands, an oblate globe, layered translucent rings with divisions and planet/ring shadows, Titan and Enceladus. Both use the local star map and a seeded rich starfield. Actual framebuffer stills serve the picker and unavailable-WebGL fallback.

[Design](DESIGN.md), [assets and credits](ASSETS.md), [Mars build](BUILD-MARS.md), [Saturn build](BUILD-SATURN.md), [catalog integration](BUILD-INTEGRATION.md), and [independent scene source counsel](REVIEW-SCENES.md).

## Verification boundaries

Worktree `wt-orbital-places-20261016`, branch `feat/orbital-places-20261016`. Started at `5c26bd0fa`; incorporated main through `58a0d4552` before final build. Product build `37302e41750eb272`.

Focused checks: Mars/model/sky 11 tests; Saturn/model 7; registry/picker/host 21. Collection and run tails are recorded in the build reports and `.tmp/orbital-places/`. Scene tests mock the renderer and image loading. They prove construction and lifecycle, not real GL rendering.

Actual scene renders at 1440×1000 and 393×852 sample authored elapsed 0/60/180 seconds. All four observations report no page or GL console errors. Root read all twelve images. Both moons are findable in each scene's sampled timeline; planet/ring front-back depth and portrait framing were inspected. These are sampled renders, not natural elapsed waiting, an astronomical ephemeris, or measured hardware performance.

Direction sketches in `canvas/index.html` use actual library drawers with a declared 2D composition sketch. They are not scene proof. `canvas/live.html` mounts the actual scene and shared runtime; `canvas/scene.html` is the direct authored-time capture harness. The preview server is local and separate from the owner hub.

The local atlas declares `edge.face.wallpaper_choose` at the existing `settingsWallpaper.tsx` selection handler; it is a new face declaration for these cases, not an old sealed-pass observation. It extends the canonical atlas and passes its JSON schema. The draft initially copied Jupiter's obsolete `edge.ui` identifier; schema validation caught it before any graph run. Sealed passes and schema are unchanged.

All walkthroughs use fresh isolated HOME/DB, native state off, engine none, and the one-machine-run lock. Phone selection uses native touch. Face readiness is distinct from moving frames, persistence, drawer input and pause/fallback checks. The canvas intentionally owns no pointer hits; controls above it retain those hits. The phone Desk's existing Apps/Drawers panel covers most of the background; portrait composition is separately visible in the direct actual scene captures.

## Remaining unknowns

Owner aesthetic judgment; hardware-wide FPS/thermals; long-running memory use. Independent worker source counsel is explicitly not Muad'Dib's check. No full-tape green, native capture/provider verification, or whole-product aesthetic acceptance is claimed.

## Final product checks and delivery

PR [#1229](https://github.com/karolswdev/HoldSpeak/pull/1229). Final quick check GREEN: 419 web files / 4,105 tests, 705 affected Python checks, 109 Desk sweeps, 17 canon checks. Logs: `.tmp/orbital-places/quick-final.log` and `quick-final/{build,vitest,py,sweep,canon}.log`. Final TypeScript check exits 0 in `typecheck-final.log`. Current source digest independently recomputed as `37302e41750eb272`, matching the frozen build and loaded HTML.

| Actual Desk journey | Widths | Observation directory under `.tmp/orbital-places/` |
| --- | --- | --- |
| Mars choose, reload, moving frames, drawer, Motion off/on, reduced motion, Quiet cleanup | 1440 / 393 | `final-mars-1440`, `final-mars-393` |
| Saturn same full journey | 1440 / 393 | `final-saturn-1440`, `final-saturn-393` |
| Real collection choice and first-render graph predicate | Both scenes at 1440 / 393 | `graph-{mars,saturn}-{1440,393}/<run-id>` |
| WebGL disabled, correct local still fallback | Mars 1440; Saturn 393 | `fallback-mars-1440`, `fallback-saturn-393` |

All four graph cases pass within 30 seconds, with initial feedback and settled terminal outcomes read separately. Root inspected each before/after pair and the product picker, desktop backgrounds and drawer shots. Supplemental walks verify nonzero changing GL pixel hashes, saved choice after close/reload, actual owned drawer pointer/touch hits, equal visible pixels during Motion off and system reduced motion, and scene removal on Quiet. Both preview images load at natural width 1440. Supplemental runs have no page errors or external requests. Fallback runs explicitly substitute browser WebGL disabled; reverse scene/viewport fallback combinations were not separately walked.

Graph/supplemental provenance records `9be90168917df5c165fa78925aef7082542c1c01`, dirty=true (untracked dependency symlink and later documentation); the final product source was frozen. The earlier Mars desktop walkthrough used preliminary build `df1268d885fe94ab`; it was repeated on the final combined build and is not the final proof.

Normal local delivery uses the idle owner hub after merge, separately from all isolated verification. The local preview server and serving worktree remain available. The scene choice is left to the owner. Formal postmerge review and owner live judgment remain open.
