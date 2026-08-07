# HS-116-05 — The templates

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-02, HS-116-04
- **Unblocks:** HS-116-08
- **Owner:** unassigned

## The thesis (the bar)

A user who has never seen HoldSpeak before can set up a working
agent workbench in thirty seconds. Pre-built templates ship with the
product: a recipe (the agent persona), a workbench config (name,
schedule suggestion), and starter items. The user picks a template,
picks a target, and they're running. When this ships, the product
has strong opinions about what agents are good at — delivered as
working examples, not documentation.

**Articles served:** VI (honest by construction — templates show
real capabilities, not demo state), VII (no prose — the template
is the explanation), VIII (native-grade craft — templates look as
good as hand-built workbenches).

## Deliverables

1. **Template registry.** A JSON registry at
   `holdspeak/workbench_templates.py` (or `web/src/desk/
   workbenchTemplates.ts` for the frontend). Each template is:
   ```
   { id, name, description, icon,
     recipe: { name, role, system_prompt, user_template },
     workbench: { schedule },
     starter_items: [{ title, body, priority }] }
   ```

2. **Template picker surface.** When creating a new workbench (or
   from the empty state), the user sees a grid of template cards.
   Each card shows: icon, name, one-line description, the schedule
   suggestion, and "Use this" verb. Picking a template creates the
   recipe + workbench + starter items in one gesture.

3. **Shipped templates.** At least three, each with a real,
   production-quality system prompt:

   **TODO Agent.** An overnight backlog worker. System prompt:
   work through items one by one, produce a short receipt per item,
   propose (never execute) anything that requires owner consent.
   Schedule suggestion: `0 2 * * *` (2 AM daily). Starter items:
   "Review open PRs", "Summarize yesterday's meeting notes",
   "Draft the weekly status update."

   **Triage Agent.** Classifies and prioritizes incoming items.
   System prompt: read each item's grounding, classify by urgency
   (act now / this week / backlog / dismiss), write a one-line
   rationale. Schedule suggestion: manual (run on demand). Starter
   items: none — the user feeds it.

   **Meeting Prep Agent.** Prepares context packs for upcoming
   meetings. System prompt: for each item (a meeting title +
   grounding), assemble relevant artifacts, summarize prior
   meetings with the same participants, list open action items.
   Schedule suggestion: `0 7 * * 1-5` (7 AM weekdays). Starter
   items: "Monday standup", "1:1 with manager."

4. **Delivery Workbench template.** A special template that, when
   selected, wires the workbench to the DW integration. The recipe
   is pre-configured with DW MCP tools and the system prompt
   includes the DW operating loop. The schedule follows the DW
   cadence. This template is available only when DW rails are
   detected (`dw doctor` passes).

5. **Custom from scratch.** The template picker always includes a
   "Blank workbench" card that opens the empty state (recipe picker
   + target picker + no starter items).

## Test plan

- `uv run pytest -q` — template registry loads, template
  instantiation creates recipe + workbench + items in one
  transaction.
- Visual: open the template picker, select TODO Agent, pick a
  target, verify the workbench opens with the starter items and
  the agent avatar.
