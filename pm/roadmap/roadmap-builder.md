# Roadmap Builder

**Owner:** PMO.
**Status:** canonical methodology, distributed via `pmo-roadmap`
(`~/dev/reusable-processes/pmo-roadmap`).
**Read this if:** you are an agent (or a human) tasked with translating a
PMO plan + product vision into a phase-based, evidence-rich roadmap project
under `pm/roadmap/{project}/`.

This document is **both** the methodology and the primer prompt. §6 is the
copy-paste prompt block. The rest is the reference material that prompt
points at. §8 is a worked example from one real project (Pantrybot) — keep
or replace as fits your project.

---

## 0. What this exists to solve

Plans rot. They rot when:

- the plan lives in one giant doc with no per-step audit trail;
- "done" is asserted rather than evidenced;
- the next agent reading it doesn't know which paragraph is still true;
- chunks of work ship without updating tracking docs in the same commit.

The roadmap-builder fixes that by enforcing a **directory contract** where
every phase, story, and piece of evidence has a known home, and a **lifecycle
contract** where files appear and update at the right moment in the work.

The output is not a document. The output is a **filesystem-shaped project
plan** that survives session resets, agent handoffs, and the user picking it
up six weeks later.

---

## 1. Directory contract

```
pm/roadmap/
  roadmap-builder.md           ← this file (methodology)
  {project-slug}/
    README.md                  ← project-level: vision, phase index, current pointer
    phase-{n}-{kebab-slug}/
      current-phase-status.md  ← live doc: goal, scope, exit criteria, story table
      story-{n}-{kebab-slug}.md
      story-{n+1}-{kebab-slug}.md
      ...
      evidence-story-{n}.md    ← created when story-{n} ships
      evidence-story-{n+1}.md
      ...
      final-summary.md         ← created at phase exit
```

Rules:

1. One project per top-level folder. Slug is kebab-case, derived from the
   project's user-facing name (`pantrybot`, `mealplanner-v2`, etc.).
2. Phase folders are `phase-{n}-{kebab-slug}` where `{n}` is zero-indexed
   if there is a "convergence / setup" phase (Phase 0), otherwise one-indexed.
3. Story files are `story-{n}-{kebab-slug}.md` where `{n}` is the story's
   sequence within the phase. Story IDs in headers use
   `{PROJECT}-{phase}-{seq}` (e.g. `PB-0-01`, `PB-3-04`) — flat, sortable.
4. `evidence-story-{n}.md` pairs 1:1 with `story-{n}-*.md`. Created only
   when the story actually ships, never before.
5. `final-summary.md` is created **on phase exit** and is immutable
   afterwards. If a phase needs to be re-opened, open a new phase, do not
   edit a closed final-summary.
6. `current-phase-status.md` is the only file in a phase folder that is
   mutable across the phase's life. Everything else either appears once
   and stops changing, or appears at a known lifecycle moment.

---

## 2. File specs

Each spec gives required sections. Keep prose tight; this is a project plan,
not a manifesto. Code, file paths, and story IDs are the load-bearing
content.

### 2.1 `pm/roadmap/{project}/README.md`

Project-level orientation. A new agent reading just this file should
understand what the project is, where it is, and where to look next.

Required sections:

```markdown
# {Project Name} — Roadmap

**Last updated:** YYYY-MM-DD.
**Current phase:** [phase-{n}-{slug}](./phase-{n}-{slug}/current-phase-status.md)
**Status:** {planning | in-progress | shipped | paused}.

## Vision
{1–3 paragraphs: what we're building and why. Quote canon, don't invent.}

## Source canon
Bulleted list of authoritative docs this roadmap serves (e.g.
`/APP-SOUL.md`, `/DESIGN-BRIEF-X.md`, `pm/{project}/PLAN.md`). If a phase
disagrees with canon, canon wins.

## Phase index
| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | … | done | [phase-0-…](./phase-0-…/) |
| 1 | … | in-progress | [phase-1-…](./phase-1-…/) |
| 2 | … | not-started | [phase-2-…](./phase-2-…/) |

## Operating cadence
Per-chunk update list: which files are touched in the same commit when work
ships (story header, BACKLOG, CHANGELOG, current-phase-status, etc).
Mirrors §7 of this builder.

## Glossary
Project-specific terms. Skip if not needed.
```

### 2.2 `phase-{n}-{slug}/current-phase-status.md`

The single live document for a phase. Updated every chunk. At phase exit
its content seeds `final-summary.md` and then this file stops changing.

Required sections:

```markdown
# Phase {n} — {Title}

**Last updated:** YYYY-MM-DD (after chunk {x.y}).

## Goal
{One short paragraph. Immutable for the life of the phase.}

## Scope
- In: {bulleted concrete deliverables}
- Out: {bulleted things that look related but are NOT in this phase}

## Exit criteria (evidence required)
Checklist. Every item names a real artifact or test:
- [ ] {e.g. `frontend/scripts/validate-raster-assets.ts` exists and exits 0}
- [ ] {e.g. `npm run test:unit -- components/brand/__tests__/*.test.tsx` passes ≥6 cases}
- [ ] {e.g. iPhone device review screenshots in `graphic-design-handoff/...`}

## Story status
| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PB-1-01 | … | done | [story-01](./story-01-…md) | [evidence-01](./evidence-story-01.md) |
| PB-1-02 | … | in-progress | [story-02](./story-02-…md) | — |
| PB-1-03 | … | backlog | [story-03](./story-03-…md) | — |

## Where we are
{2–6 sentences: most recent chunk, what's next, blockers. Updated each
chunk. Treat this as the "pickup snapshot" — a fresh agent reading this
should know what to do next.}

## Active risks
| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| … | … | … | … |

## Decisions made (this phase)
- {date} — {decision} — {reason} — {authority}.

## Decisions deferred
- {decision} — {trigger to revisit} — {default if no decision}.
```

### 2.3 `phase-{n}-{slug}/story-{n}-{slug}.md`

One file per atomic unit of work. One story = one PR. Ported from the
existing `pm/pantry-life/` story shape (it works; don't redesign it).

Required header + sections:

```markdown
# {ID} — {Title}

- **Project:** {project-slug}
- **Phase:** {n}
- **Status:** backlog | ready | in-progress | blocked | done
- **Depends on:** {comma-separated IDs, or "none"}
- **Unblocks:** {comma-separated IDs} (optional)
- **Owner:** {initials or "unassigned"}

## Problem
{2–4 sentences: what and why.}

## Scope
- In: {concrete deliverables — file paths if known}
- Out: {related-looking things this story does NOT cover}

## Acceptance criteria
Checklist. Merge gate. Each item must be something a reader can verify by
reading code or running a command:
- [ ] …
- [ ] …

## Test plan
- Unit: {commands + which files}
- Integration / Cypress: {commands + spec files, or "n/a — covered in PB-X-Y"}
- Manual / device: {steps, or "n/a"}

## Notes / open questions
{Don't resolve ambiguity silently. Park it here. If the brief disagrees
with the story, the brief wins; record the disagreement here and move on.}
```

### 2.4 `phase-{n}-{slug}/evidence-story-{n}.md`

Created **after the story ships**. This is the auditable artifact trail.
The point is: "show me the story actually shipped, not just that someone
checked a box."

Required sections:

```markdown
# Evidence — {ID} — {Title}

- **Shipped:** YYYY-MM-DD
- **Commit:** {SHA or PR link}
- **Owner:** {initials}

## Files touched
- `path/to/file.ts:L12-L48` — {one-line "what changed"}
- `path/to/test.tsx` — {…}

## Verification artifacts
Paste the actual output, not a summary:
- `npm run type-check` → passed.
- `npm run test:unit -- foo.test.ts` → 1 file, 7 tests passed.
- `npm run lint -- path/to/file.ts` → 0 errors, 2 existing warnings.
- Cypress / device review: {results, screenshot paths if relevant}

## Acceptance criteria — re-checked
Re-run through the story's checklist with one-line evidence per item.
- [x] {item} — proven by {…}
- [x] {item} — proven by {…}

## Deviations from plan
{If scope shifted or an "Out" item ended up in scope, name it here. If
nothing deviated, write "none".}

## Follow-ups
{Anything spotted but not fixed. File as a new story if material; mention
the new story ID here.}
```

### 2.5 `phase-{n}-{slug}/final-summary.md`

Created **on phase exit**. Immutable afterwards.

Required sections:

```markdown
# Phase {n} — Final Summary

- **Phase opened:** YYYY-MM-DD
- **Phase closed:** YYYY-MM-DD
- **Chunks shipped:** {count}

## Goal — was it met?
Re-list the original goal verbatim, then a yes/no/partial with evidence
links to the relevant `evidence-story-*.md` files.

## Exit criteria — final state
Re-run the original exit-criteria checklist. Every item: status + evidence
link.
- [x] … — see [evidence-story-04](./evidence-story-04.md)
- [ ] … — **deferred to phase {m}**, reason: …

## Stories shipped
| ID | Title | Commit/PR | Date |
|---|---|---|---|
| PB-{n}-01 | … | abc1234 | 2026-04-26 |

## Stories cut or deferred
| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| PB-{n}-07 | … | scope cut at chunk {x.y} | phase {m}, or "won't ship" |

## Surprises and lessons
{What did we learn that the next phase needs to know? Calibration data
(e.g. "Pixellab batch 3 needed 2 regen passes — budget that into phase
{m}"). Not a feel-good retro; a practical handoff.}

## Handoff to phase {n+1}
- What is now available that wasn't before: {…}
- What changed in the contract / canon: {…}
- What the next phase should read first: {paths}

## Final asset / test posture
- {test counts}
- {asset counts}
- {anything material to baseline going forward}
```

---

## 3. Lifecycle

The lifecycle is the only thing that prevents the directory from rotting.

```
PHASE OPEN
  ├─ Create phase-{n}-{slug}/
  ├─ Write current-phase-status.md (goal, scope, exit, empty story table)
  └─ Write story-{n}-*.md stubs for every chunk identified in PMO plan

WORK IN PROGRESS (per chunk, repeat)
  ├─ Pick a story; flip its status: backlog → ready → in-progress
  ├─ Update current-phase-status.md story-status row in the same edit
  ├─ Ship one PR (per memory feedback_actually_run_tests: tests must
  │   actually run, not just be authored)
  ├─ On merge:
  │   ├─ Story status → done
  │   ├─ Create evidence-story-{n}.md with real verification output
  │   ├─ Update current-phase-status.md "Where we are" + story row
  │   ├─ Update project README.md last-updated
  │   └─ Update any project-canon docs (e.g. BACKLOG.md, CHANGELOG.md,
  │       IMPLEMENTATION-LOG.md) per the operating cadence
  └─ Repeat

PHASE CLOSE (every exit-criteria item checked or explicitly deferred)
  ├─ Write final-summary.md
  ├─ Freeze current-phase-status.md (no more edits)
  ├─ Update project README.md: phase status → done, current pointer →
  │   next phase
  └─ Open phase-{n+1}-{slug}/ if applicable
```

Anti-patterns that break the lifecycle (reject if seen):

- Writing `evidence-story-*.md` before the story shipped.
- Writing `final-summary.md` before all exit criteria are settled.
- Editing `current-phase-status.md` without also updating the relevant
  story row + the project README's "Last updated".
- Story files without acceptance criteria.
- Phase folders without exit criteria.
- Multiple stories in one PR (split, or document why with a `Notes`
  entry on each story file).

---

## 4. Naming and ID rules

- **Project slug:** kebab-case, derived from user-facing name. Stable
  forever. `pantrybot`, not `pantrybot-v2`.
- **Project prefix:** uppercase abbreviation, used in story IDs.
  `pantrybot` → `PB`. Pre-existing prefixes (`PL` for pantry-life) stay
  as-is on legacy stories; new projects pick a new prefix.
- **Phase folder:** `phase-{n}-{kebab-slug}`. Slug derives from the phase
  goal (`phase-0-convergence-pm-lock`, `phase-3-pl-raster-catalog`). Keep
  under ~40 chars total.
- **Story file:** `story-{n}-{kebab-slug}.md` where `{n}` is the
  zero-padded sequence within the phase (`story-01-…`, `story-02-…`).
- **Story ID:** `{PROJECT}-{phase}-{seq}` (`PB-3-04`). Flat, sortable,
  greppable.
- **Evidence file:** `evidence-story-{n}.md` (no slug — the story file's
  slug is the source of truth).

IDs are stable forever. If a story is cut, its ID is not reused.

---

## 5. What the builder agent actually does

When invoked to build (or re-build / extend) a roadmap project, the agent
runs this procedure. It must be **idempotent** — running it twice on the
same project should not duplicate or corrupt anything.

```
1. INPUTS — confirm with the user or read from invocation:
   - project name + slug
   - source canon paths (PMO plan, vision/brief docs, current-state docs)
   - whether this is a new project or an extension

2. READ — load all source canon. Do not invent phases. Phases come from
   the PMO plan; if the plan does not specify them, ask the user or
   surface candidate phases for approval before writing anything.

3. PROJECT SCAFFOLD — if pm/roadmap/{slug}/ does not exist:
   - create it
   - write README.md from §2.1 template, populated from canon
   - leave the phase index empty until phases are scaffolded

4. PHASE SCAFFOLD — for each phase in the PMO plan:
   - create phase-{n}-{slug}/ (skip if exists)
   - write current-phase-status.md from §2.2 template
   - for each chunk identified in the plan, write a story stub from §2.3
     template — acceptance criteria can be sparse but MUST exist
   - DO NOT write evidence-story-*.md (those land at ship time)
   - DO NOT write final-summary.md (those land at phase close)

5. CROSS-LINK — update the project README phase index. Update the
   "current phase" pointer to the lowest non-done phase.

6. VERIFY — self-check:
   - every phase listed in README.md has a folder ✓
   - every story listed in any current-phase-status.md table has a
     story-*.md file ✓
   - no evidence-*.md exists for a story not in `done` status ✓
   - no final-summary.md exists for a phase with unchecked exit
     criteria ✓
   - every file follows the templates in §2 ✓

7. REPORT — print a summary: what was created, what was skipped, what
   needs user input. Do NOT mark any work as complete in stories the
   user hasn't actually shipped.
```

---

## 6. Builder prompt (copy-paste)

Hand this prompt to a fresh agent along with the project's source canon
paths. The agent has no context from prior sessions; the prompt + this
file + the canon must be enough.

```
You are building (or extending) a phase-based roadmap project under
pm/roadmap/{project-slug}/. Read pm/roadmap/roadmap-builder.md first —
it is the methodology, the directory contract, the file templates, and
the lifecycle rules. Follow it exactly.

Inputs:
- project name: {fill in}
- project slug: {fill in, kebab-case}
- project prefix: {fill in, uppercase, 2–3 chars}
- source canon (read these before writing anything):
  - {path 1, e.g. /APP-SOUL.md}
  - {path 2, e.g. pm/ROADMAP.md}
  - {path 3, e.g. pm/{project}/PLAN.md}
  - {path 4, e.g. docs/go-live-readiness.md}
- mode: {NEW PROJECT | EXTEND EXISTING}

Procedure:
1. Read every canon doc in full. Do not skim. Quote, don't paraphrase,
   when filling in vision and goals.
2. Identify phases. They come from the PMO plan. If the plan is
   ambiguous, list your candidate phases and ASK before writing.
3. Identify chunks per phase. Each chunk = one shippable PR.
4. Run the §5 procedure in roadmap-builder.md. Be idempotent.
5. After scaffolding, run the §5.6 self-check and print the report.

Hard rules:
- Do NOT write evidence-story-*.md for stories that haven't shipped.
- Do NOT write final-summary.md for phases that haven't closed.
- Do NOT mark any story as `done` unless the canon plan explicitly
  records it as shipped (with a commit SHA or equivalent).
- Do NOT invent phases, stories, or acceptance criteria not grounded
  in canon. If canon is silent, surface the gap and ask.
- Follow the file templates in roadmap-builder.md §2 exactly.
- Honor every memory rule in ~/.claude/projects/.../memory/MEMORY.md
  that applies (greenfield, run-tests-don't-author, update-master-docs,
  etc.).

Output: a filesystem diff (what was created, what was skipped, what
needs user input) plus a one-paragraph summary. Do not write code
beyond the roadmap files themselves.
```

---

## 7. Operating principles (carry-overs)

These are the principles every roadmap project inherits. They are not
restated in each project's README; this section is the canonical source.

- **Evidence, not vibes.** Every "done" needs an `evidence-story-*.md`
  with actual command output. Type-check is not validation
  (memory: `feedback_actually_run_tests`).
- **Update master docs in the same chunk.** Every shipping commit
  touches the relevant tracking docs together (memory:
  `feedback_update_master_docs`,
  `feedback_pantry_life_pickup_snapshot`).
- **Run the tests; don't just author them.** Use the documented npm
  scripts (memory: `feedback_ios_test_npm_scripts`,
  `feedback_actually_run_tests`).
- **Greenfield discipline.** Pre-TestFlight, no users → no migration
  ceremony, no compat shims (memory:
  `feedback_greenfield_no_migrations`). Project-specific; honor when
  the project is in that state.
- **One PR per story.** If a chunk needs to bundle, document why on
  every story file involved.
- **Stop signals matter.** Risk tables in `current-phase-status.md`
  must include a stop signal — the concrete observation that triggers
  "halt this approach and regroup." Without one, the risk is
  decorative.
- **Canon wins.** If a story contradicts `APP-SOUL.md`, the design
  brief, or the PMO plan, the canon wins. Record the disagreement in
  the story's "Notes / open questions" and move on.

---

## 8. Worked example — Pantrybot (illustrative)

> The section below is the first real project to use this contract. Treat
> it as a concrete reference for *how* to map a PMO plan onto the
> directory contract. Replace or delete when you have your own example.


The first project to use this contract is `pm/roadmap/pantrybot/`,
seeded from `pm/ROADMAP.md`. The mapping:

| `pm/ROADMAP.md` section | `pm/roadmap/pantrybot/` artifact |
|---|---|
| §0–§3 vision + convergence | `README.md` |
| §4 phase 0 | `phase-0-convergence-pm-lock/current-phase-status.md` + 2 stories |
| §4 phase 1 | `phase-1-raster-runtime-shell/current-phase-status.md` + 3 stories |
| §4 phase 2 | `phase-2-testflight-brand-pack/current-phase-status.md` + 6 stories |
| §4 phase 3 | `phase-3-pl-raster-catalog/current-phase-status.md` + 8 stories |
| §4 phase 4 | `phase-4-pre-testflight-polish/current-phase-status.md` + 4 stories |
| §4 phase 5 | not scaffolded yet (post-TestFlight, deferred) |
| §6 risks / §7 decisions | distributed across each phase's `current-phase-status.md` |
| §10 cadence log | per-phase `final-summary.md` files at close |

Story prefix: `PB`. Example IDs: `PB-0-01`, `PB-3-04`.

When the user approves Phase 0 of `pm/ROADMAP.md`, run this builder on
the Pantrybot project to produce the scaffold. The first story shipped
under the new contract should have its evidence file land in the same
PR as the story-status flip.

---

## 9. Maintenance

This file changes when the methodology changes, not when individual
projects do. Bump the "Status" line date and add a note here:

- 2026-04-25 — initial methodology, v1.
