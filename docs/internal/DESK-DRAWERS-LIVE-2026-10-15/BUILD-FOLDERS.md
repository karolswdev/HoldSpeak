# Folder build — 2026-10-15

HOLD FOR SHIP. Worker implementation complete; root owns browser verification,
the quick check and shipping. Base `bea522beb`, worktree
`wt-desk-drawers-live-20261015`, branch `feat/desk-drawers-live-20261015`.
The one finished review fix round is complete: 52/52 focused tests pass.

Tuesday: the owner can find a real root drawer, open its child drawers and
members, and use the same named Drawers section in phone Go. Tenets 3/5/6.

## Implementation

- `screen/compose.ts` adds the dedicated Directory path. A missing parent
  puts the child on Desk. Canonical and legacy directory member refs keep
  their objects filed; qualified refs do not hide a different kind with the
  same id. Real drawers make the Desk nonempty.
- `screen/GoHome.tsx` retains Go and adds root drawers through the existing
  Go group, row and Button components. The row carries its canonical
  `data-object-id`.
- `pullouts/DirectoryPullout.tsx` composes current Surface rows from actual
  child directories plus stored member refs. It deduplicates resolved refs,
  uses the existing canonical opener, keeps unavailable members visible,
  and reserves the empty state for no contents. Contents uses the existing
  SurfaceSection zero omission. The dead Drop action is removed; Dictate
  uses the library Button. The filing strip stays in place.
- The owned screen tests cover drawer selection and the existing object
  menu, qualified opens, filing and phone Go. The former still-only
  assertion now covers mounted live scenery, the still before readiness,
  its removal after readiness and no atmosphere on Quiet Desk.

The existing canonical identity is **`zone:<id>`**:
`api.qualifiedRef("directory", id)` emits it, and `world.objectByRef` resolves
it. Desk keys, selection, phone keys and open calls all use that identity.
`directory:<id>` is accepted as a member-ref alias by `normalizeRef`; no
global API or world lookup was changed. Using a cosmetic `directory:` Desk
key would have broken the existing object menu and selection contracts.

## Focused proof

The fixtures map recorded fields from root's actual isolated directory and
note route answers through `fromWireDirectory` and `fromWireNote`:
`.tmp/desk-drawers-live/produced-directory-wire.json` and
`produced-note-wire.json`. Edge cases derive missing parents, unavailable
members, legacy refs and cross-kind collisions from those records.

Every list/run used `.venv/bin/python .tmp/desk-drawers-live/locked.py`,
which holds the machine test lock and creates/removes an isolated HOME.
The initial worker runs used these files, with `--maxWorkers=2`:

```
src/desk/pullouts/DirectoryPullout.test.tsx
src/desk/screen/__tests__/Screen.test.tsx
src/desk/screen/__tests__/chairScreen.test.tsx
```

`world.test.ts` was absent under `web/src`; no substitute suite ran.
`folders-final-list.log` contains 30 collected cases, including:

```
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the screen of objects > renders real root drawers, recovers missing parents and opens the qualified directory
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the pure parts > reaches folders filed by canonical or directory alias member refs through their parent
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the pure parts > keeps canonical and legacy directory members filed without hiding a different qualified kind
src/desk/screen/__tests__/chairScreen.test.tsx > PHILO-14 A1 — the Chair is the screen > keeps phone Go and adds the same real root drawers as a named Drawers section
src/desk/pullouts/DirectoryPullout.test.tsx > Directory contents > renders actual child folders and stored members and opens their canonical refs
src/desk/pullouts/DirectoryPullout.test.tsx > Directory contents > deduplicates child membership, supports bare refs and retains kind-qualified collisions
src/desk/pullouts/DirectoryPullout.test.tsx > Directory contents > shows unresolved stored membership as unavailable, with no false Open or empty state
src/desk/pullouts/DirectoryPullout.test.tsx > Directory contents > reserves the empty state for an empty drawer and has no zero count or dead Drop action
```

Before product edits, `folders-red.log` ended:

```
Test Files  3 failed (3)
     Tests  8 failed | 21 passed (29)
```

That run had seven new folder cases and the changed atmosphere case. One
additional folder-membership alias case was added during implementation.
The original two-file baseline had passed 22/22.

At the initial build freeze, after removal of raw ref hover text,
`folders-final-frozen.log` ended:

```
Test Files  3 passed (3)
     Tests  30 passed (30)
  Start at  19:47:53
  Duration  4.58s
```

The inherited jsdom `HTMLCanvasElement.getContext` diagnostics from DeskIcon
text measurement remain in both baseline and final logs. These tests do not
prove real WebGL rendering or pointer geometry. This lane ran no browser,
build, install, staging or commit; root owns the 1440/393 observations.

No settled-design amendment and no new debt identified.

## Finished review fix round

The bounded source review found three real gaps. All three are fixed in this
one round, without changing folder storage, the filing writer, the shared
world lookup or any other kind's Open route.

- **Cyclic filing:** `rootDirectories` derives one effective parent per
  folder: a valid explicit parent first, then the first containing folder
  from resolved member refs. A parent-chain walk retains one reachable root
  per cycle. It prefers an original null-parent root, then sorts by id.
  Missing-parent recovery and self roots remain reachable.
- **Bare-id collisions:** directory member refs resolve through the existing
  `objectByRef` before canonicalization, as the directory reader does. A bare
  id that resolves to a Note cannot also hide a same-id drawer or Decision.
  An unresolved bare ref does not suppress a different object.
- **Object Open:** the directory branch of `verbRegistry.ts` uses the existing
  `openPullout(qualifiedRef(...), origin)` path. `objectMenu.ts` offers Open
  for drawers; File remains withheld. The rendered Screen test selects a
  drawer, presses Object → Open, then context-menu Open, and asserts both
  qualified dispatches. The other kind branches retain their prior route.

Root expanded ownership to those two small menu files and authorized their
existing focused tests. The exact original three files plus these two ran:

```
src/desk/__tests__/verbRegistry.test.ts
src/desk/__tests__/objectMenu.test.ts
```

The first cycle-only run reproduced both disappearing-root defects:
`folders-review-red.log`, 2 failed / 31 passed (33). After the review's two
additional seams were added, `folders-review-expanded-list.log` collected
52 cases, including:

```
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the pure parts > resolves bare members to one canonical kind without hiding colliding drawers or decisions
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the pure parts > keeps the original root reachable when filing it into its own child creates a parent cycle
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the pure parts > keeps one deterministic root for a membership-only cycle regardless of input order
src/desk/screen/__tests__/Screen.test.tsx > PHILO-14 A1 — the pure parts > keeps a self-filed or self-parented drawer as a reachable root
src/desk/__tests__/verbRegistry.test.ts > the verb registry (HS-105-05 / HS-111-07 v2) > opens a selected drawer by canonical ref and preserves its pointer origin
src/desk/__tests__/objectMenu.test.ts > objectMenuEntries (registry-derived, parallel list #4 dead) > offers a drawer's Open and dispatches its canonical ref while File stays withheld
```

Before the review fixes, `folders-review-expanded-red.log` ended:

```
Test Files  3 failed | 2 passed (5)
     Tests  6 failed | 46 passed (52)
```

After the review fixes, `folders-review-expanded-green.log` ended:

```
Test Files  5 passed (5)
     Tests  52 passed (52)
  Start at  19:57:33
  Duration  4.55s
```

The same inherited jsdom canvas diagnostics remain. Root owns the actual
filing-writer walk and live menu Open observation. The lane is frozen for
the reviewer's one re-check and root's shipping steps.
