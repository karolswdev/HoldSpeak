# Inventory, 2026-10-03

The owner's assignment, 2026-10-03: "we need everything inventorized AND cleaned up,
properly ... We polish the current features, we make sure, that..., e.g., our memory
system is hooked up into all processes." Then he uses HoldSpeak for one real week.

Four read-only passes on `origin/main` @ `6ccfa4e0d`. The open work they produced is
tracked in `pm/STATUS.md`. Screenshots of pass A are not committed.

| Pass | File | Headline |
|---|---|---|
| A. Every app, walked on a real hub (1440 and 393) | [A-apps.md](inventory-2026-10-03/A-apps.md) | 44 surfaces: 22 work, 7 partly, 3 broken, 11 empty without an engine, mic or calendar |
| B. Backend: services, loops, routes, MCP | [B-backend.md](inventory-2026-10-03/B-backend.md) | 13 of 16 loops alive; 11 MCP tools broken on every call; 219 of 717 routes have no web caller |
| C. Memory and the other shared systems | [C-wiring.md](inventory-2026-10-03/C-wiring.md) | Memory is a search over 11 tables; of 15 processes, 1 reads it fully and 10 do not read it |
| D. Failing tests and repo clutter | [D-hygiene.md](inventory-2026-10-03/D-hygiene.md) | 30 red in the default run, 35 in browser tests; `pm/` is 19,723 files and 2.3 GB |

## What it says, in short

- The Desk holds together; the gaps are at the joins: memory is read by almost
  nothing that writes for him, seven kinds of write do not tell other windows, and
  the "needs you" numbers disagree between faces.
- Several verbs are dead or broken on a fresh desk: Context save, Desk → New at the
  Chair, "Name an owner", Workbench Run without a model. Times are off by the UTC offset.
- With nothing configured, only dictation and recording work. Every AI job needs an
  engine assigned first.
- Most failing tests are stale tests, not product bugs.
- The repository carries about 2.3 GB of evidence and history in the checked-out tree.

## Not covered by any pass

Anything that needs a real engine, microphone, calendar, GitHub or Jira; a real
phone; the Swift app, firmware and UAT trees; the owner's own configuration and data.
His week of use is the test for these.
