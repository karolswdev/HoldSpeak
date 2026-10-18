# Brief for a cluster betterment design (shared by every cluster worker)

You produce the betterment design for one **cluster** of HoldSpeak features.
The orchestrator reviews it and rewrites where needed. Your prompt names the
cluster, its features (the row numbers in `INVENTORY.md`), your hub port
range and your folder.

## Read first

- `docs/internal/betterment/README.md`: the format. Follow it exactly.
- `docs/internal/betterment/workbench/DESIGN.md`: the bar for a design.
- `docs/internal/betterment/PLAN.md`: the master plan and **the product
  model rulings** (the one name and one home for each concept). Your design
  must use those names. If you think a ruling is wrong for your cluster, say
  so in your §5 decisions; do not ignore it.
- `docs/internal/betterment/INVENTORY.md`: your cluster's rows, the
  duplicates and the promises.
- `engines/DESIGN.md` and `mcp/DESIGN.md`: every AI feature runs on Engines,
  and every tool-capable engine gets the desk's tools.
- `docs/internal/UX-CANON.md`, the Seven Tenets (`docs/internal/CONSTITUTION.md`),
  `docs/internal/philo/phase-17/RECON-2026-10-13.md`.

The owner: a Senior Software Architect who manages three people. He calls
HoldSpeak "the most advanced Agentic OS in the world" and says that today he
keeps hitting walls. Design for his week, not for the code.

## What to do

1. **Walk it live** (the "What it is today" section). Run an isolated hub on
   YOUR port range only (never 8765, his desk). Use an isolated HOME, the rig
   switches from CLAUDE.md, never his real HOME, DB or Keychain, and send
   nothing off the machine. Copy how `docs/internal/betterment/workbench/RECON.md`
   did it (its footnote names the rig: `scripts/graph_walk.py serve`). Seed
   realistic content: two or three meetings with transcripts, notes, three
   people (Mira, Theo, Jun), a project. Use the LAN engine at
   192.168.1.43:8080 if it is reachable; never fake replies. Walk each
   feature's job as a first-time user at 1440x900 and 393x852, and screenshot
   every state into `<folder>/shots/`. Keep a friction log (presses, seconds,
   exact words, where you got stuck). Stop the hub and remove the HOME when
   you finish.
2. **Map the code**: what each feature is in data, which verbs are dead or
   duplicated, overlaps, and constraints (as `workbench/MODEL.md` did, but
   shorter).
3. **Write** `<folder>/RECON.md` (walk + friction log), `<folder>/MODEL.md`
   (code map), `<folder>/DESIGN.md` (sections 1 to 6 of the format, with
   ASCII layouts for desktop and phone, the words table, what each press
   does, what is parked, and at most three owner decisions with defaults)
   and `<folder>/RECIPE.md` (PR-sized slices: goal, files, changes, done
   when, tests by the test diet, not in this slice; ordered so that each
   merge leaves things better and never half-broken).
4. **Be ambitious.** This is an agentic OS. Ask where an engine with the
   desk's tools, an automation, or an agent would do the job better than a
   form. Ask what "delight" means here: speed, one press, words he would use
   himself. But never add a verb that cannot work, and never add a second
   home for a concept that already has one.

## Rules

- Change no product code. Do not commit, stage or branch. Create files only
  in your folder.
- pytest or vitest runs go through `uv run python scripts/test_lock.py --`.
  You probably need none.
- Plain English, short sentences. No proof notation.
- In your final message: the folder, the shot count, the three biggest root
  causes, the design in five lines, and the slice list.
