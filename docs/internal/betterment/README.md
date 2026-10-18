# Betterment: design documents that become recipes

Owner, 2026-10-17: the orchestrator's work is "an orchestrator of detailed
design documents for 'betterment' of current features, which then will
become recipes for execution / implementation."

One folder per feature: `docs/internal/betterment/<feature>/`.
Each folder holds two files and a `shots/` folder:

- `DESIGN.md`: what the feature is for and what it will be.
- `RECIPE.md`: the ordered build slices that make the design real.

## Why this format

The earlier Workbench passes (`WORKBENCH-PICKERS-2026-10-14`,
`ACCOUNT-WORKBENCH-2026-10-15`) moved badges and rows and proved them with
test counts. They never asked what the feature is for. The result was
polished, and it still made no sense. A betterment document starts from the
job and ends with a picture of the result.

## DESIGN.md: the sections, in this order

1. **The job.** Who opens this, when, and what they want to have when they
   close it. Use the owner's words when we have them. One paragraph.
2. **What it is today.** Screenshots at 1440 and 393 of every state a user
   meets (empty, first use, populated, running, failed, done). A friction
   log: each step of the job, what the user sees, what they expect, where
   they stop. Times and press counts.
3. **Why it fails.** Root causes, ranked. A root cause is a wrong model or a
   wrong concept, not a wrong padding. Each cause cites shots.
4. **The design.**
   - The concept model in one sentence ("A workbench is …").
   - The words: the names the user sees, and the names we stop using.
   - The layout of each state, drawn (a mockup in our own material, or an
     annotated wireframe). Desktop and phone.
   - What one press does, for every verb. A verb that cannot work is not
     shown.
   - What is removed or parked, and where it goes.
5. **Decisions for the owner.** At most three. Each one has a recommended
   answer, so the build can start on the default.
6. **How we know it worked.** The job from section 1, done by a person, with
   a target press count and time. Not a test count.

## RECIPE.md: the slices

Each slice is one PR in the fast cycle (`CLAUDE.md`). For each slice:

- **Goal**: one sentence a user would notice.
- **Files**: the files it touches (a few).
- **Changes**: what to build, specific enough for a worker who has not read
  the conversation.
- **Done when**: observable behavior ("press Run, see the first line of
  output in under 2 s"), at 1440 and 393.
- **Tests**: the cheapest tier that proves it (the test diet, `CLAUDE.md`).
- **Not in this slice**: so the worker does not wander.

Slices are ordered so that each merge leaves the feature better than before
and never half-broken on the owner's desk.

## Voice

Plain English, short sentences (ASD-STE100 for product text). No proof
notation ("GREEN:304", "PID", "custody", build hashes) in these documents.
Evidence paths go in a footnote, not in the prose.

## Index

The master plan is `PLAN.md`; every open owner decision is in `DECISIONS.md`; the feature inventory is `INVENTORY.md`;
cluster workers follow `CLUSTER-BRIEF.md`.

| Feature | Folder | State |
|---|---|---|
| Automations (today "Workbench") | `workbench/` | draft, owner decisions open |
| Engines | `engines/` | draft, owner decisions open |
| The desk's tools for every engine (MCP) | `mcp/` | draft, owner decisions open |
| Agents vs herdr (study) | `herdr/` | studied |
| Asking, thinking and memory (Ask, Threads, Notes, Memory, Search) | `asking/` | draft, owner decisions open |
| Projects, updates and decisions | `projects/` | draft, owner decisions open; P0 in build |
| Agents (Conductor, herdr ideas) | `agents/` | draft, owner decisions open |
| The daily surface, People and commitments | `daily/` | draft, owner decisions open |
| Settings and setup | `setup/` | draft, owner decisions open |
| The desk shell | `shell/` | draft, owner decisions open |
| Delivery and send | `send/` | draft, owner decisions open |
| Capture | `capture/` | draft, owner decisions open |
