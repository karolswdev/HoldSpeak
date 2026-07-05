# Evidence — HS-82-03 — The conveyor renders

**Status:** done (2026-07-04).

## The move

`web/src/desk/missioncontrol.ts` (the typed data layer: camelCase
view shapes, wire normalizers, and a self-contained zustand store
with the design's 15-second single-flight poll — deliberately its
own store, zero surgery on the desk's `DeskState`, minimal merge
surface with the in-flight phase-81 branch) +
`web/src/desk/components/MissionControlConveyor.tsx` (the fixture
at the foot of the desk: one belt per rails project, phases as
segments with the current phase marked, the current phase's
stories riding the belt with status and evidence marks, the next
actionable story wearing the desk's one `--accent` use, warnings
quiet but visible, collapsible to a tab) + `desk-mc-*` classes in
`desk.css` on Signal tokens + the mount as a `.desk-next` sibling
in `DeskApp.tsx`.

Honesty in the render path: a `compatibility` or `unavailable`
repo renders its typed state and detail; a desk with no rails
configured renders nothing at all; an empty belt is never
fabricated. The data layer normalizes all three bridge documents
(sessions and events ride in HS-82-04's rendering); malformed
entries normalize to `unreachable`, never to `live`.

## Proof

- `npm run test:desk` — **25 passed** (3 files: the existing desk
  suites plus `missioncontrol.test.ts` covering live-feed
  normalization, compatibility honesty, malformed-entry handling,
  the declared session field list, tmux-absent defaults, and
  event flattening that never fabricates from a dead repo).
- `npx astro build` — clean (17 pages; the island type-checks and
  bundles; output stays untracked per `.gitignore`
  `holdspeak/static/_built/`).
