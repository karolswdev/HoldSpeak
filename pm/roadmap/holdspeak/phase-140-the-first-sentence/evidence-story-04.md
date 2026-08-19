# HS-140-04 evidence — A desk worth opening

**Date:** 2026-08-18
**Result:** done; Terra seed/retry verdict RATIFY

## Shipped behavior

- The packaged fresh Desk contains Inbox, Personal, Work, Meetings, Decisions,
  and Reference; Start here; five question-led editable context notes; and one
  Everyday context Knowledge collection containing those five notes.
- The regular-user pack creates no Agent, model profile, provider endpoint, or
  Workbench, and asserts no personal fact about the owner.
- Ordinary seeding creates only never-seen deterministic ids. Existing edits,
  filing, Knowledge membership, Agent attachment, and tombstones remain the
  owner's. Interrupted applications safely complete missing new relationships
  on retry without moving or resurrecting an existing object.
- Explicit Reset tombstones the current Desk and force-restores the furnished
  defaults behind a confirmation that names both effects.
- Ask and Agent now call the existing concept `Context`. The Chair's existing
  Ask AI verb mounts the same Ask panel already used on Floor/List, fixing a
  dead prominent affordance found during the browser walk.

## Local verification

```text
.venv/bin/pytest -q tests/unit/test_desk_seed.py tests/unit/test_grounding_shared.py tests/unit/test_conductor_ref_hydration.py
35 passed in 2.85s

npx vitest run src/desk/DeskApp.test.tsx src/desk/__tests__/glassDrop.test.tsx src/pages/cores/__tests__/deskModule.test.tsx --maxWorkers=2
Test Files  3 passed (3)
Tests       13 passed (13)

uv run pytest -q tests/unit/test_doc_drift_guard.py tests/uat/test_build_ledger.py
21 passed in 1.18s
```

`npm run build` passed after 1,479 modules transformed, with only the existing
dynamic/static-import and large-chunk warnings. `git diff --check` passed.

## Isolated-HOME browser acceptance

The walk ran the real loopback server against a temporary HOME and database.
The packaged seed reported six directories, six notes, and one Knowledge
collection. The existing Continue later seam opened the normal Desk.

At both widths the Floor/List shows all six drawers and Everyday context; the
Ask grounding rack explicitly selects the collection and prices its hydrated
contents; a real newly created Agent offers `Everyday context` in its Context
selector. No attachment is automatic. All captures had zero console/page
errors and no horizontal document overflow.

- Furnished Floor: [1440×900](./assets/story-04/furnished-floor-1440x900.png), [393×900](./assets/story-04/furnished-floor-393x900.png)
- Explicit Ask attachment: [1440×900](./assets/story-04/everyday-context-ask-1440x900.png), [393×900](./assets/story-04/everyday-context-ask-393x900.png)
- Agent Context selection: [1440×900](./assets/story-04/everyday-context-agent-1440x900.png), [393×900](./assets/story-04/everyday-context-agent-393x900.png)

## Counsel trail

The first hostile pass found that a process interruption could leave default
filing and Knowledge membership permanently incomplete. The repair separates
new-object completion from owner-modified relationships and adds a partial-run
regression. Final read-only verdict: **RATIFY**.
