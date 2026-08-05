# Phase 116 — The Workbench

**Status:** done (18/19, 1 superseded). All stories shipped. The
plumbing works. The product — a first-class DeskOS app with
mission-control dashboard, live run feedback, agent memory that
compounds, voice-driven operation, drag-and-drop work intake,
in-world configuration, and native-grade item cards — doesn't
exist yet. That's what stories 10-18 build. The architecture RFC
(`PLAN_WORKBENCH_ARCHITECTURE.md`) is ratified.

**Last updated:** 2026-08-04 (all product stories shipped; grounded in
Hermes Agent architecture research, Delivery Workbench Phase 36
capabilities, and the existing HoldSpeak inference target system).

## The orchestrator

This phase is commanded by **Opus 4.6** (Claude, 1M context). The
orchestrator holds the Constitution, the Hermes research, the DW
Phase 36 surface (programs, memory glass, project context,
suggestions, conductor), the existing HoldSpeak inference target
system, the desk grammar, and the material language — simultaneously.

**GPT-5.6 Terra** agents execute research spikes, component builds,
and verification walks. Opus designs the architecture, writes the
contracts, verifies the integration, and walks the result on the
real hub before claiming done.

## What we're building

HoldSpeak becomes an **agentic operating system**. Not "a chat app
with agents" — an OS where agents are first-class citizens that
*work for you*. You set up a workbench in thirty seconds: pick a
pre-built template or roll your own, point it at an inference target
(local, LAN, Tailscale, OpenRouter, cloud — whatever you have), give
it a schedule, and let it go.

The centerpiece is the **Workbench** primitive — a new desk object
where:

- An agent (a recipe) sits and works.
- Items arrive, get worked, produce receipts, get resolved.
- One inference target runs it all.
- A schedule or trigger wakes it up.
- Everything is governed by Article XI (kernel admission, bounded
  delegation) and Article V (consent spine — the agent proposes, the
  owner approves).

The Delivery Workbench integration becomes one *instance* of this
primitive — the workbench backed by PMO rails. Your TODO workbench,
your morning brief workbench, your bug triage workbench, and your
delivery workbench all sit on the same desk, same grammar, same
surface, same material.

## Why this phase exists

Phase 115 proved the Desk is a cohesive, native-grade OS. But it's
an OS that *waits for you*. Agents respond to your keystrokes. They
don't wake up overnight, work through a backlog, triage incoming
signals, or prepare your morning. The infrastructure for autonomous
agent work exists across two systems that haven't met:

1. **Delivery Workbench (Phase 36)** already has governed programs,
   restart-safe conductors, memory-before-dispatch, project context
   (constitutional context), agent suggestions, knowledge packets,
   and a Linear-grade workbench UI. But it lives in a CLI and a
   localhost browser — not on the Desk.

2. **HoldSpeak** already has PersonaChat, AskPanel, recipes with
   full CRUD, inference targets with CRUD/probe/egress, the kernel
   with bounded delegation, and the grounding system. But agents are
   reactive — ask and answer, never autonomous.

3. **Hermes Agent** (NousResearch, 225K stars) proved the patterns:
   layered constitutional context (SOUL.md → project → memory →
   session), native cron with fresh isolated sessions, skills as
   reusable procedural knowledge, parent-child subagent delegation,
   and morning briefs via collector→synthesize→deliver. These are
   the right interaction patterns for a personal agent OS.

Phase 116 fuses these three into one surface on the Desk.

## Method

- Ground every story in Constitution articles. Cite them.
- The Workbench is a DeskPrimitive (Article II). It gets derived UI
  from the OS, not its own screen.
- Every workbench run goes through the kernel (Article XI). Bounded
  delegation. Receipts.
- Every workbench run discloses egress (Article III). The badge sits
  on the workbench surface.
- Every workbench action obeys the consent spine (Article V). The
  agent proposes, the owner approves. Overnight runs produce
  proposals, not fait accompli.
- Skills are knowledge base items (Article II — everything is a
  primitive). Not a separate system.
- Pre-built workbenches ship as recipe + workbench templates.
  Templates are just JSON — recipe + workbench config + starter
  items.
- The DW integration upgrades to consume DW Phase 36 (project
  context, suggestions, memory glass) through the same workbench
  surface.
- Inference target binding is the existing system. No new targeting
  infrastructure. Just new consumers of InferenceTarget + profile_id.

## Dependency graph

```
HS-116-01  Workbench primitive (the contract)          ✓
    │
    ├── HS-116-02  Workbench surface (desk window)     ✓
    │       │
    │       ├── HS-116-04  Item composer + grounding   ✓
    │       │       │
    │       │       └── HS-116-11  Item depth (cards, results, keep, egress)
    │       │
    │       ├── HS-116-05  Pre-built templates         ✓
    │       │
    │       └── HS-116-10  Configuration panel (in-world settings, schedule presets)
    │               │
    │               ├── HS-116-14  Voice-driven workbench
    │               │
    │               └── HS-116-17  First-class app (dock, home dashboard, needs-you)
    │
    ├── HS-116-03  Constitutional context              ✓
    │       │
    │       └── HS-116-13  Hardening (DB, limits, errors, cron fix)
    │
    ├── HS-116-06  Skills primitive                    ✓
    │       │
    │       └── HS-116-16  Agent memory (writeback, recall, promotion)
    │
    ├── HS-116-07  Conductor (scheduler)               ✓
    │       │
    │       ├── HS-116-08  Morning brief template      ✓
    │       │
    │       ├── HS-116-12  Run feedback (SSE, history, notifications)
    │       │
    │       └── HS-116-16  Agent memory (writeback, recall)
    │
    └── HS-116-15  The walk (proof on glass — LAST)
```

## Stories

### The primitive

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 01 | The contract | What is a Workbench? The schema, the API, the DB model, the kernel admission. | backlog |
| 02 | The surface | What does a Workbench look like on the Desk? The window, the item list, the agent badge, the target lamp, the schedule indicator. | backlog |

### The context

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 03 | Constitutional context | How does the owner set always-on context that every agent run receives? | backlog |
| 04 | The composer | How do items arrive on the workbench? Voice, text, grounding, drag-and-drop. | backlog |

### The ecosystem

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 05 | The templates | What pre-built workbenches ship out of the box? TODO, Triage, Meeting Prep. | backlog |
| 06 | Skills | How do agents develop and share reusable procedural knowledge? | backlog |

### The autonomy

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 07 | The conductor | How do workbenches wake up, run, and report back? Scheduling, fresh sessions, receipts. | backlog |
| 08 | The morning brief | The first shipped autonomous workbench: collectors → synthesis → delivery. | backlog |

### The craft (the product surface)

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 10 | The configuration panel | How does the owner configure a workbench in-world? Name, agent, target, schedule presets, skills — all editable from the window. | backlog |
| 11 | Item depth | What does a real work item look like? Cards with state borders, editable body, rendered result with egress badge, Keep verb. | backlog |
| 12 | Run feedback | What happens when a workbench runs? Live item state via SSE, head scanning indicator, run history wing, desk notifications. | backlog |
| 13 | Hardening | Is the system trustworthy? Constitutional context in DB, size limits, skill budget visibility, conductor error receipts, cron fix. | backlog |
| 14 | Voice-driven workbench | Can the whole thing be driven by voice? Voice commands for add/run/dismiss/configure. Proposal strip for confirmation. | backlog |

### The intelligence

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 16 | Agent memory | How do agents learn? Terminal writeback, recall-before-dispatch, skill promotion from repeated observations. | backlog |
| 19 | Skill library | What does an agent know out of the box? 10 production skills adapted from Hermes, pre-bound to templates. | backlog |

### The interaction

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 18 | Drop to work | How does work arrive? Drag a note/meeting/artifact onto a workbench → item created with grounding. Drop, speak what to do, run. | backlog |

### The application

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 17 | First-class app | Is Workbenches a real DeskOS application? Dock entry, home dashboard, workbench summary cards, needs-you indicator, recent runs. | backlog |

### The proof

| # | Story | The ask it answers | Status |
|---|-------|-------------------|--------|
| 15 | The walk | Screenshot-verified proof that every surface works at 1440 and 393. End-to-end flow on glass. | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-116-01 | The contract | done | [story-01](./story-01-the-contract.md) | — |
| HS-116-02 | The surface | done | [story-02](./story-02-the-surface.md) | — |
| HS-116-03 | Constitutional context | done | [story-03](./story-03-constitutional-context.md) | — |
| HS-116-04 | The composer | done | [story-04](./story-04-the-composer.md) | — |
| HS-116-05 | The templates | done | [story-05](./story-05-the-templates.md) | — |
| HS-116-06 | Skills | done | [story-06](./story-06-skills.md) | — |
| HS-116-07 | The conductor | done | [story-07](./story-07-the-conductor.md) | — |
| HS-116-08 | The morning brief | done | [story-08](./story-08-the-morning-brief.md) | — |
| HS-116-09 | The walk (original) | superseded | [story-09](./story-09-the-walk.md) | superseded by HS-116-15 |
| HS-116-10 | The configuration panel | done | [story-10](./story-10-the-configuration-panel.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-116-11 | Item depth | done | [story-11](./story-11-item-depth.md) | [evidence-story-11](./evidence-story-11.md) |
| HS-116-12 | Run feedback | done | [story-12](./story-12-run-feedback.md) | [evidence-story-12](./evidence-story-12.md) |
| HS-116-13 | Hardening | done | [story-13](./story-13-hardening.md) | [evidence-story-13](./evidence-story-13.md) |
| HS-116-14 | Voice-driven workbench | done | [story-14](./story-14-voice-driven.md) | [evidence-story-14](./evidence-story-14.md) |
| HS-116-15 | The walk | done | [story-15](./story-15-the-walk.md) | [evidence-story-15](./evidence-story-15.md) |
| HS-116-16 | Agent memory | done | [story-16](./story-16-agent-memory.md) | [evidence-story-16](./evidence-story-16.md) |
| HS-116-17 | First-class app | done | [story-17](./story-17-first-class-app.md) | [evidence-story-17](./evidence-story-17.md) |
| HS-116-18 | Drop to work | done | [story-18](./story-18-drop-to-work.md) | [evidence-story-18](./evidence-story-18.md) |
| HS-116-19 | Skill library | done | [story-19](./story-19-skill-library.md) | [evidence-story-19](./evidence-story-19.md) |

## Where we are

18/19 (superseded: 09). All product stories shipped. The workbench
is a first-class DeskOS application: config panel with schedule
presets and skills, item cards with state borders and egress badges,
live run feedback via WebSocket, agent memory with recall and
writeback, voice commands, drop-to-work, workbenches home dashboard,
10 built-in skills, constitutional context in DB with size limits
and version history. Screenshot-verified at 1440 and 393.
configuration, item depth with rendered results and egress badges,
live run feedback via SSE, hardening (DB migration, size limits,
error receipts), voice commands, and the proof walk. The plumbing
works but the product doesn't exist yet.
