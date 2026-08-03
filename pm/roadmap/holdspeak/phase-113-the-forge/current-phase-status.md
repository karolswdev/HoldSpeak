# Phase 113 - The Forge

**Status:** DRAFT. Fifteen stories that turn the Desk into an
Architect's operating system — Workbench 2.0+ on steroids. Three
tracks: **build** (shared kit, real editor, AI, voice, git
drawers, DW primitives, decisions), **polish** (kill the animated
diorama, fix the compositor, refit every existing surface onto the
kit), and **operate** (formatting toolbar, creation flow, delete/
undo, discoverability). When this phase ships, the Desk IS the OS
— not a web app that approximates one, not a developer scratchpad
that requires knowing markdown syntax, not a maze where features
are built but unfindable.

**Last updated:** 2026-08-02 (expanded from 4 to 8 stories after
ideation session).

## Why this phase exists

The Desk is the front door (Article I) and every capability must
appear as a primitive on it (Article II). Five gaps break that
promise today:

1. **No shared component kit.** Four independent table
   implementations (SurfaceLedger, ZoneWindow table, PR receipts
   table, AttentionDrawer list). Four independent mic+text composers.
   SurfaceWings exists but ZoneWindow hand-rolls its own tabs.
   EgressChip exists but Pullout hand-rolls its own badge. Every new
   primitive window starts from scratch instead of composing from a
   shared kit. This is the Workbench anti-pattern: inconsistency
   masquerading as flexibility.

2. **The editor is a `<textarea rows={7}>`.** `InlineEditor.tsx` has
   no formatting, no syntax awareness, no keyboard shortcuts. For a
   product whose Constitution requires "native-grade craft"
   (Article VIII), this is the weakest link.

3. **Code and files live outside the Desk.** The Delivery system has
   git integration (`registry.py`, worktree management, PR receipts)
   but it projects into its own delivery surface. A developer's
   files cannot be seen, browsed, edited, staged, or committed from
   the Desk world.

4. **Delivery Workbench data is invisible.** DW projects, phases,
   stories, evidence, health — none of this exists as objects on the
   Desk. An architect who manages roadmaps through DW has no Desk
   surface for it. The richest structured data in the project lives
   in Markdown files that the Desk cannot see.

5. **Voice is dumb transcription.** MicButton appends raw text.
   There is no intelligence between speech and action. Speaking into
   a git drawer should understand "commit with message: fixed the
   routing bug", not append those words to a text field.

## Method

- **The shared kit ships first (story 01).** Every subsequent story
  composes from it. No one-off tables, no hand-rolled composers.
  The kit IS the Workbench 2.0+ consistency promise.
- **The editor is the second foundation (story 02).** Everything
  that opens files, composes text, or runs AI operations needs it.
- **Everything else layers on these two.** List convergence,
  AI editor, voice router, git drawers, DW primitives, and
  decisions each build on the kit and the editor.
- **Every story must pass a live screenshot walk** (1440px desktop,
  393px mobile) against the real hub before flip. No textarea-era
  regressions allowed.
- **Constitution articles cited per story.** No story ships without
  grounding in the canon it serves.
- **Workbench 2.0+ is the north star.** Every design decision is
  measured against: does this feel like an operating system where
  objects are real, manipulation is direct, and the grammar is
  consistent? If it feels like a web app with window chrome, it
  fails.

## Stories

### Build — new capabilities

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | [The shared kit](./story-01-the-shared-kit.md) | "We keep building the same components over and over" | backlog |
| 02 | [The real editor](./story-02-the-real-editor.md) | "I need to actually compose in this thing" | backlog |
| 03 | [List convergence](./story-03-list-convergence.md) | "The desktop list looks like ass" | backlog |
| 04 | [AI in the editor](./story-04-ai-in-the-editor.md) | "Built-in AI editing is a must" | backlog |
| 05 | [Voice Intent Router](./story-05-voice-intent-router.md) | "Voice should understand what window I'm talking to" | backlog |
| 06 | [Git-backed drawers](./story-06-git-backed-drawers.md) | "Drawers backed by a git repo would be so powerful" | backlog |
| 07 | [DW on the Desk](./story-07-dw-on-the-desk.md) | "Delivery Workbench should be a Desk primitive" | backlog |
| 08 | [Decision primitive](./story-08-decision-primitive.md) | "Architecture decisions need a real home" | backlog |

### Polish — make the existing desk truly Workbench 2.0+

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 09 | [The static desk](./story-09-the-static-desk.md) | "Icons hover and pulsate — that's not Workbench" | backlog |
| 10 | [The compositor](./story-10-the-compositor.md) | "Windows should behave like a real OS compositor" | backlog |
| 11 | [The refit](./story-11-the-refit.md) | "Every surface must be built from the same kit" | backlog |

### Operate — make the OS actually productive

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 12 | [The composing desk](./story-12-the-composing-desk.md) | "Where's bold? Where's heading? These are .md files" | backlog |
| 13 | [The creation flow](./story-13-the-creation-flow.md) | "How do I even create a note? Where's Cmd+N?" | backlog |
| 14 | [Object lifecycle](./story-14-object-lifecycle.md) | "I can't delete anything. There's no undo." | backlog |
| 15 | [Discoverability](./story-15-discoverability.md) | "Features exist but I can't find them" | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-113-01 | The shared kit | backlog | [story-01-the-shared-kit](./story-01-the-shared-kit.md) | — |
| HS-113-02 | The real editor | backlog | [story-02-the-real-editor](./story-02-the-real-editor.md) | — |
| HS-113-03 | List convergence | backlog | [story-03-list-convergence](./story-03-list-convergence.md) | — |
| HS-113-04 | AI in the editor | backlog | [story-04-ai-in-the-editor](./story-04-ai-in-the-editor.md) | — |
| HS-113-05 | Voice Intent Router | backlog | [story-05-voice-intent-router](./story-05-voice-intent-router.md) | — |
| HS-113-06 | Git-backed drawers | backlog | [story-06-git-backed-drawers](./story-06-git-backed-drawers.md) | — |
| HS-113-07 | DW on the Desk | backlog | [story-07-dw-on-the-desk](./story-07-dw-on-the-desk.md) | — |
| HS-113-08 | Decision primitive | backlog | [story-08-decision-primitive](./story-08-decision-primitive.md) | — |
| HS-113-09 | The static desk | backlog | [story-09-the-static-desk](./story-09-the-static-desk.md) | — |
| HS-113-10 | The compositor | backlog | [story-10-the-compositor](./story-10-the-compositor.md) | — |
| HS-113-11 | The refit | backlog | [story-11-the-refit](./story-11-the-refit.md) | — |
| HS-113-12 | The composing desk | backlog | [story-12-the-composing-desk](./story-12-the-composing-desk.md) | — |
| HS-113-13 | The creation flow | backlog | [story-13-the-creation-flow](./story-13-the-creation-flow.md) | — |
| HS-113-14 | Object lifecycle | backlog | [story-14-object-lifecycle](./story-14-object-lifecycle.md) | — |
| HS-113-15 | Discoverability | backlog | [story-15-discoverability](./story-15-discoverability.md) | — |

## Where we are

Draft. Awaiting owner charter decision. Vision brief published at
the artifact URL for review.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Shared kit extraction breaks existing surfaces | Medium | Extract one component at a time; full test suite between each; screenshot walk after all extractions | Existing tests break after kit adoption |
| CodeMirror bundle size bloats the web build | Low | Tree-shake; only import markdown mode + minimal extensions | Bundle exceeds 200KB gzipped |
| Editor theming fights the Desk glass aesthetic | Medium | Build a dedicated CM6 theme from design-tokens.json; test in dark-glass context early | Owner rejects the editor look |
| Git-backed drawers blur the "organizational drawer" mental model | Medium | Make repo drawers visually distinct (different sprite, different badge vocabulary) | Owner says the primitive model is wrong |
| Voice Intent Router scope creeps into a chatbot | Medium | Stateless classifier only. No conversation history. Multi-turn scoped to pending proposal. | Intent router starts maintaining session state |
| DW primitive is read-only but users expect writes | Low | Status transitions go through the kernel. Roadmap files stay Markdown-authored. The Desk is a lens, not an editor. | Users try to edit phase files through the Desk |
| Eight stories is too many for one phase | Medium | Foundation stories (01, 02) can ship independently. The phase can be split if the owner prefers. | Velocity drops below 1 story/day |

## Decisions made (this phase)

- 2026-08-02 — CodeMirror 6 over ProseMirror/Monaco/Slate — CM6
  respects the markdown-source contract, is lightweight, and its
  extension API lets us add AI features without forking.
- 2026-08-02 — Shared kit before features — every new window must
  compose from the kit. No one-off implementations allowed.
- 2026-08-02 — `roadmap` and `story` as new primitive kinds, not
  extensions of `project` — DW data has its own lifecycle, status
  vocabulary, and evidence model that don't fit the existing
  Project primitive.
- 2026-08-02 — Voice Intent Router is a stateless classifier, not
  a conversation agent — it maps (transcript + surface context) to
  a VoiceProposal. Multi-turn is scoped to the pending proposal.
- 2026-08-02 — Signal, Pulse, and Board deferred to a future
  phase — they compose well with the kit but are not needed for
  the core Architect's OS to ship.

## Decisions deferred

- Whether the AI editor uses streaming or batch responses — depends
  on the egress/receipt model the owner wants to see.
- Whether story cards are pullable from the Roadmap window onto the
  desk floor — density question at scale.
- Whether the DW commit contract certification UI lives on the Desk
  or stays in the terminal — accessibility vs. forcing-function
  tradeoff.
