# The Workbench Architecture

> **Status:** DRAFT — awaiting owner ratification.
> **Proposed by:** Phase 116 (The Workbench).
> **Articles served:** I, II, III, IV, V, VI, VII, VIII, IX, XI.

## What this document is

This is the architectural RFC for the Workbench primitive — the
surface that makes HoldSpeak an agentic platform. It covers storage,
execution, context, scheduling, output, integration, and the
interaction model. Every decision is grounded in the Constitution.

This document does NOT charter stories. It establishes the contracts
stories must satisfy.

---

## 1. What a Workbench is

A Workbench is **a place where an agent works.** Not a chat thread.
Not a run-once prompt. A persistent workspace with:

- An identity (name, icon, position on the desk)
- An agent (a recipe — the persona that works here)
- An inference target (where the agent runs — local, LAN, cloud)
- A schedule (when the agent wakes up — or manual only)
- Items (the work — each one a task with context)
- A workspace (a directory on disk — where outputs land, where
  tools execute, where state persists between runs)
- Skills (learned procedures that compound over time)
- Run history (receipts for every execution)

A Workbench is a DeskPrimitive (Article II). It appears as an
object on the desk. It opens as a window. It is created, configured,
and operated entirely in-world (Article VII — no modals, no separate
settings screens).

The Delivery Workbench integration is one instance of this primitive.
A user's TODO workbench, morning brief workbench, and bug triage
workbench are other instances. Same grammar, same surface, same
material.

---

## 2. Storage architecture

### 2.1 The split

HoldSpeak uses three storage tiers:

| Tier | Path | What lives there |
|------|------|-----------------|
| Config | `~/.config/holdspeak/` | Settings, agent sessions, per-user config |
| Data | `~/.local/share/holdspeak/` | SQLite database, backups |
| Runtime | `~/.holdspeak/` | Credentials, gate config, plugin packs, delivery sources |

The Workbench adds a fourth concern: **workspace content** — agent
outputs, working directories, tool artifacts, run snapshots. This
content is neither config nor relational data. It's the filesystem
footprint of an agent's work.

### 2.2 The workspace directory

Every Workbench gets a home:

```
~/.holdspeak/workbenches/<workbench-id>/
├── workspace/                     ← the agent's working directory
│   ├── .git/                      ← if this workbench works in a repo
│   └── (any files the agent creates or needs)
├── runs/
│   └── <run-id>/
│       ├── receipt.json           ← the full run receipt
│       ├── prompt-stack.json      ← what the agent received (constitutional
│       │                             revision, skills, grounding — for audit)
│       └── items/
│           └── <item-id>.md       ← the agent's output for each item
├── skills/
│   └── <skill-id>.md              ← skill body, human-readable
└── manifest.json                  ← identity, pointers to DB records
```

**Why a filesystem tree and not just DB rows?**

- Agent outputs are **content**, not metadata. A two-page PR review
  belongs in a file you can read, grep, diff, and back up — not in
  a TEXT column you can only see through the API.
- A workbench that works with code needs a **working directory** —
  a place to clone repos, run tests, produce artifacts.
- Run snapshots (what the agent received, what it produced) are
  **audit evidence** — they should survive database migrations
  and be readable without the application.
- Skills are documents. They should be readable as files.

**The DB remains the index.** WorkbenchRecord, WorkbenchItemRecord,
and WorkbenchRunRecord in SQLite are the metadata layer — identity,
status, timestamps, pointers. The filesystem is the content layer.
The `manifest.json` links the two: it carries the workbench ID and
enough identity to reconnect if the DB is restored from backup.

### 2.3 Constitutional context storage

The constitutional context is a single-owner document. It belongs
in the database (not a JSON file in `~/.config/`) because:

- It needs transactional consistency with workbench runs.
- It needs to survive config directory cleanup.
- It needs version history (the last N revisions, for rollback).
- It needs a size limit enforced at the storage layer.

Schema: a `constitutional_context` table with `revision` (int,
auto-increment), `content` (text), `content_hash` (sha256),
`created_at` (timestamp). The latest revision is the active one.
Previous revisions are kept for audit and rollback (capped at 20).

### 2.4 Cleanup and lifecycle

- Deleting a workbench (tombstone in DB) does NOT delete the
  workspace directory. The owner explicitly removes it. Agent
  data is the owner's property.
- A `purge` verb hard-deletes the DB record AND removes the
  workspace directory. Confirmation required (Article V — the
  action is irreversible).
- Run directories are append-only. Old runs are never modified
  after completion.

---

## 3. The execution model

### 3.1 The prompt stack

Every workbench run assembles the prompt in this order:

```
┌─────────────────────────────────────┐
│ 1. Constitutional context           │  ← owner's always-on briefing
│    (revision + hash stamped)        │     injected by engine.run_prompt
├─────────────────────────────────────┤
│ 2. Recipe system prompt             │  ← the agent's identity and rules
│    + injected skills (8KB budget)   │     who you are, how you work
├─────────────────────────────────────┤
│ 3. Recipe standing context          │  ← manual_context + KB hydration
│    (manual_context + _kb_block)     │     what you always know
├─────────────────────────────────────┤
│ 4. Item grounding                   │  ← hydrated meetings, artifacts
│    (hydrate_grounding_blocks)       │     what this task is grounded in
├─────────────────────────────────────┤
│ 5. Item body                        │  ← the task itself
│    (title + body + instructions)    │     what you need to do
└─────────────────────────────────────┘
```

Layers 1-3 are the same for every item in a run. Layer 4-5 change
per item. The conductor must assemble ALL five layers — the current
implementation is missing layers 3 and 4.

The prompt stack snapshot (which revision, which skills, which
grounding refs) is written to `runs/<run-id>/prompt-stack.json`
for audit. This is how we prove what the agent received (Article IX).

### 3.2 Fresh session isolation

Each scheduled run starts a fresh session. No chat history. No
memory of previous runs. The only context is the prompt stack above.
This is deliberate (the Hermes pattern): a cron run starts clean so
its behavior is reproducible and auditable.

Skills are the mechanism for persistence between runs — not memory,
not history. An agent that learns something useful proposes a skill.
The owner approves it. Future runs include it in the prompt.

### 3.3 The wake gate

Before any model invocation, the conductor checks:

1. Does the workbench have pending items? (No → skip, no-op receipt)
2. Does the workbench have a recipe? (No → error receipt)
3. Is the inference target ready? (No → error receipt with refusal
   reason from Article VI)
4. If all pass → proceed with the run.

The wake gate ensures zero tokens are consumed for an empty or
misconfigured workbench.

### 3.4 Target readiness

The conductor MUST check `target.ready` before running. If the
target is unavailable (model file missing, endpoint unreachable,
mesh node offline), the conductor:

- Writes a run receipt with `status: "refused"`, the target name,
  and the readiness reason.
- Does NOT retry automatically. The next scheduled tick will
  re-check.
- The workbench window shows the refusal honestly (Article VI).

### 3.5 Item processing

For each pending item, in priority order:

1. **Claim** — status → `claimed`, `claimed_at` stamped.
2. **Assemble** — build the per-item user prompt (layers 4-5).
3. **Execute** — call `intel.run_prompt()` with the full stack.
4. **Persist** — write the output to the item record AND to
   `runs/<run-id>/items/<item-id>.md` on disk.
5. **Receipt** — status → `done` or `failed`, `completed_at`
   stamped, `result_egress` records the actual placement boundary
   and model.

If an item fails, the run continues to the next item. The run
receipt records attempted / completed / failed honestly.

---

## 4. The context model

### 4.1 Constitutional context

The owner's always-on briefing. Injected into EVERY agent run
across the entire system — not just workbenches. Persona chat,
ask, chains, workflows — all of them receive it.

Properties:
- **One document.** Not per-project, not per-agent. The owner's
  voice, once.
- **Revisioned.** Every save increments the revision and recomputes
  the sha256 hash. The last 20 revisions are kept.
- **Immutable per run.** If the owner edits the document while a
  run is in progress, the running agent's prompt doesn't change.
  The edit takes effect on the next run.
- **Bounded.** Maximum 32,768 characters (~8K tokens). The editor
  shows live character count and warns at 80%.
- **Stamped.** Every run receipt records which revision and hash
  the run received. Audit can prove what the agent knew.

### 4.2 Skills

Reusable procedural knowledge. The Hermes `~/.hermes/skills/`
concept, stored as DB records with filesystem mirrors.

Properties:
- **Agent-proposed, owner-approved.** An agent working a workbench
  can propose a new skill (status: `draft`, source:
  `agent-proposed`). The owner sees the proposal and approves
  (status: `active`) or dismisses (status: `archived`). Article V
  and Article X — agents propose, the owner ratifies.
- **Attached to recipes.** A skill has a `recipe_ids` list. It
  applies to those recipes only. Transfer is explicit (attach an
  existing skill to another recipe).
- **Budget-bounded.** Skills are injected between the recipe prompt
  and the standing context. Total injection is capped at 8,192
  bytes. Skills that don't fit are reported, not silently dropped.
- **Versioned.** Each edit increments the version. The run receipt
  records which skill versions were injected.
- **Readable as files.** Each skill is mirrored to
  `workbenches/<id>/skills/<skill-id>.md` for human readability.

### 4.3 Grounding

Items carry grounding — references to meetings, artifacts, and
other desk objects that provide context for the task. At execution
time, grounding refs are **hydrated** into actual text blocks using
the same pipeline as the recipe chat endpoint
(`hydrate_grounding_blocks` from `grounding.py`).

Grounding is NOT stored as text. It's stored as refs (IDs). The
text is resolved at execution time from the canonical store. This
means:
- Grounding is always fresh (if a meeting transcript is corrected,
  the next run sees the correction).
- Grounding is bounded (the hydration pipeline caps content).
- Unknown refs refuse honestly (Article VI).

---

## 5. The scheduling model

### 5.1 Cron expressions

Workbenches support standard 5-field cron expressions:
`minute hour dom month dow` (Sunday = 0).

The conductor checks every 60 seconds. A workbench that matches
the current minute is dispatched. Duplicate dispatch in the same
minute is prevented by a per-workbench last-check timestamp.

### 5.2 Schedule presets

The UI offers human-readable presets instead of raw cron input:

| Preset | Cron | When |
|--------|------|------|
| Every morning | `0 7 * * *` | 7:00 AM daily |
| Weekday mornings | `0 7 * * 1-5` | 7:00 AM Mon-Fri |
| Every night | `0 2 * * *` | 2:00 AM daily |
| Every hour | `0 * * * *` | Top of every hour |
| Custom | (user enters cron) | Advanced |
| Manual only | (no cron) | Run button only |

The cron expression is the stored truth. The presets are a UI
convenience.

### 5.3 Triggers (future)

Beyond cron, workbenches should eventually support event triggers:
- "When a meeting ends" → Meeting Prep workbench activates
- "When a PR is opened" → Code Review workbench activates
- "When items are added" → Triage workbench activates

This is a Phase 117+ concern. The conductor's architecture should
not prevent it, but Phase 116 ships cron + manual only.

---

## 6. The output model

### 6.1 Item results

An agent's output for an item is stored in TWO places:

1. **DB**: `WorkbenchItemRecord.result` — the text, for API access
   and UI rendering.
2. **Filesystem**: `runs/<run-id>/items/<item-id>.md` — the same
   text, as a readable file with a YAML front-matter header
   (item title, priority, egress boundary, model, timestamp).

### 6.2 Result egress

Every item result carries a placement receipt:
`{ boundary, model, engine }`. The UI renders this as an egress
lamp on the result (LOCAL green, LAN amber, CLOUD red). Article III.

### 6.3 The Keep verb

A result can be "kept" — minted as a desk artifact. The Keep verb
uses the same `/api/ask/keep` or `/api/recipes/{id}/keep` endpoint
that PersonaChat uses. The artifact appears on the desk as a
first-class object. The result's provenance (which workbench, which
item, which run, which model, which egress) travels with it.

### 6.4 Notifications

When a scheduled run completes, the conductor emits:

1. **SSE event** (`scope: "workbench"`) — the workbench window
   updates live if it's open.
2. **Desk notification** — visible in the Attention drawer. Shows:
   workbench name, items completed/failed, egress boundary.
3. **Morning brief delivery** — for the Morning Brief template
   specifically, the synthesis result is auto-kept as a desk
   artifact and pinned to the notification.

---

## 7. The integration model

### 7.1 Delivery Workbench integration

A DW-backed workbench is a regular workbench whose recipe has the
DW MCP tools wired and whose workspace contains a `pm/roadmap/`
tree. It's NOT a separate surface — it's a workbench that happens
to talk to DW.

The template for this workbench:
- Creates a recipe with DW MCP tool access
- Sets up the workspace with a `pm/roadmap/` reference
- The system prompt includes the DW operating loop (the same agent
  docs block that `.githooks/dw` installs)

### 7.2 Git integration

A workbench workspace can contain a git repository. The workbench
does NOT own the repo — it's a reference (a clone or a symlink).
The agent can read the repo (for code review, PR analysis) but
CANNOT commit or push without the kernel's consent gate (Article
XI — every consequential operation is admitted).

### 7.3 Future integrations

The workspace directory is the integration surface. Anything that
needs filesystem access — a code linter, a documentation generator,
a data pipeline — drops its output in the workspace. The workbench
window can render workspace contents as a file tree (the RepoWindow
pattern).

---

## 8. The interaction model

### 8.1 Window anatomy

```
┌──────────────────────────────────────────────┐
│ HEAD: [avatar] Name        [wings] [actions] │
│       ↑ click-to-edit                        │
├──────────────────────────────────────────────┤
│ CONFIG (collapsible, expanded when unconfigured):
│   Agent: [picker with avatars + names]       │
│   Runs on: [RunsOnPicker] [egress lamp]      │
│   Schedule: [preset chips] [enable toggle]   │
│   Skills: [list with approve/dismiss/attach] │
├──────────────────────────────────────────────┤
│ WINGS: [Items] [Runs] [Workspace]            │
├──────────────────────────────────────────────┤
│ ITEMS wing (default):                        │
│   ┌────────────────────────────────────────┐ │
│   │ [P1] Fix auth timeout          [DONE]  │ │
│   │      ↳ result preview (2 lines)  [▸]  │ │
│   ├────────────────────────────────────────┤ │
│   │ [P2] Review PR #430          [PENDING] │ │
│   ├────────────────────────────────────────┤ │
│   │ [P3] Draft weekly update    [RUNNING ◉]│ │
│   │      ↳ [LedMeter scanning]            │ │
│   └────────────────────────────────────────┘ │
│                                              │
│ COMPOSER:                                    │
│   [grounding section]                        │
│   [🎤] [title input        ] [body ▾] [P3] [＋]│
├──────────────────────────────────────────────┤
│ RUNS wing:                                   │
│   [SurfaceLedger of past runs with receipts] │
├──────────────────────────────────────────────┤
│ WORKSPACE wing (when filesystem exists):     │
│   [file tree of workspace/ directory]        │
├──────────────────────────────────────────────┤
│ FOOT: 5 items · last run 2h ago · LOCAL      │
│       [▸ Run]                                │
└──────────────────────────────────────────────┘
```

### 8.2 Item states

| State | Visual | Meaning |
|-------|--------|---------|
| pending | Neutral chip, full opacity | Waiting for the next run |
| claimed | Amber chip + LedMeter | The agent is working on this now |
| done | Green chip + result preview | The agent produced output |
| failed | Red chip + error preview | The agent could not complete this |
| dismissed | Muted chip, reduced opacity | The owner dismissed this item |

### 8.3 Voice commands

When a workbench window is focused, the desk voice grammar
registers workbench-scoped intents:

- "Add [title]" → create item with spoken title (proposal strip)
- "Add [title] priority [1-5]" → create with priority
- "Run" / "Go" → trigger manual run
- "Dismiss [item]" → dismiss the focused item
- "Set schedule [preset name]" → apply a schedule preset

Voice arms; it does not fire (Article IV). Voice-created items
appear in a proposal strip for confirmation.

### 8.4 Template picker

When creating a new workbench (or opening one with no recipe), the
template picker fills the window body:

- A grid of template cards, each showing: icon, name, one-line
  description, schedule preset, starter item count.
- A target picker above the grid (RunsOnPicker or select).
- A "Blank" card for custom setup.
- Picking a template creates recipe + workbench + starter items +
  workspace directory in one gesture.

### 8.5 What "batteries included" means

A user who picks "Morning Brief" from the template picker and
points it at their LAN endpoint should have, within 30 seconds:

- A named workbench on their desk with the Morning Brief avatar
- Three starter items (yesterday's meetings, overnight receipts,
  delivery status)
- A schedule set to 7 AM weekdays
- A workspace directory at `~/.holdspeak/workbenches/<id>/`
- The ability to hit "▸ Run" and see the agent process items

No configuration files. No cron syntax. No git commands. No setup
scripts. You pick a template, pick a target, and the agent goes to
work.

---

## 9. Open questions for the owner

1. **Should workbench workspace directories be under `~/.holdspeak/`
   or `~/.local/share/holdspeak/workbenches/`?** The former is the
   runtime home (credentials, packs); the latter is the data home
   (DB). Workspaces are content, which argues for the data tier,
   but they're also runtime artifacts (working directories), which
   argues for the runtime tier.

2. **Should the Morning Brief auto-keep its synthesis as a desk
   artifact, or just notification + receipt?** Auto-keep means the
   desk accumulates daily brief artifacts. Notification-only means
   you see it and it's gone (unless you keep it manually).

3. **Should workbenches be syncable between devices?** The DB
   record syncs. But the workspace directory doesn't. A workbench
   on the desktop and the same workbench on the laptop would share
   identity but not content.

4. **Should constitutional context be per-workbench or global?**
   The current design is global (one document, all agents). Some
   users might want different context for different workbenches
   (e.g., work context vs personal context). This could be solved
   with recipe-level `manual_context` rather than per-workbench
   constitutional context.

5. **Should the conductor support concurrent workbench runs?**
   Currently sequential (one at a time in the conductor thread).
   Two workbenches due at the same minute run one after the other.
   For overnight runs this is fine; for manual triggers it could
   feel slow.

---

## 10. What exists vs. what's needed

### Shipped (stories 01-08)

- WorkbenchRecord, WorkbenchItemRecord, WorkbenchRunRecord in SQLite
- CRUD API for workbenches, items, and runs
- WorkbenchWindow component (basic — inline styles, no wings, no
  configuration editing)
- Constitutional context (file-based, injected into run_prompt)
- Skills model + CRUD API + injection into recipe routes
- Conductor with cron scheduler + manual trigger
- 4 templates (TODO, Triage, Meeting Prep, Morning Brief)
- Verb registry entry ("New Workbench" in Create menu)

### Missing (stories 10-15 + this RFC's requirements)

- Workspace directories on disk
- Run output as files (not just DB columns)
- Grounding hydration in the conductor (FIXED in rewrite, not yet
  tested on real metal)
- Recipe standing context in the conductor (FIXED in rewrite)
- Constitutional context migration to DB
- Skills UI (invisible in the workbench window)
- Item depth (body editing, result rendering, egress badges, Keep)
- Configuration panel (in-world editing of all settings)
- Schedule presets (human-readable, not cron)
- Run feedback (SSE, live progress, run history wing)
- Voice commands
- The proof walk (screenshots on glass)

---

## 11. Relationship to the Constitution

| Article | How the Workbench serves it |
|---------|---------------------------|
| I — The Desk | The workbench IS a desk surface. No eject. |
| II — Everything is a primitive | WorkbenchRecord is a DeskPrimitive with derived UI. |
| III — Local first, honest egress | Every run receipts its placement. The egress badge is on every result. |
| IV — Voice is first-class | Every input can be spoken. Voice commands drive the workbench. |
| V — Consent is the spine | Agents propose (items, skills). The owner approves. The kernel gates consequential actions. |
| VI — Honest by construction | Empty workbenches say "no items." Dead targets say why. Failed runs say what failed. |
| VII — The interface serves | No prose. No modals. Edit in-world. Labels state what. |
| VIII — Native-grade craft | The workbench window uses the Signal Workbench material. Same bevels, keylines, tokens. |
| IX — Proof over claim | Run receipts. Prompt stack snapshots. Constitutional context stamps. The walk. |
| XI — The Kernel | Every workbench run is admissible. Agent tool effects are children of the run. |
