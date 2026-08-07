# HS-116-06 — Skills

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-01
- **Unblocks:** HS-116-07
- **Owner:** unassigned

## The thesis (the bar)

Agents develop reusable procedural knowledge that compounds over
time. A skill is a knowledge base item — a markdown document that
describes how to do something. Agents can read skills, propose new
ones (the owner approves), and improve existing ones. Skills are
attached to recipes (an agent's skill set) and transferable between
workbenches. This is the Hermes `~/.hermes/skills/` concept,
grounded in HoldSpeak's existing knowledge base primitive.

When this ships, an agent that reviews PRs three times learns *how*
you like PRs reviewed and applies that knowledge on the fourth run
without being told again.

**Articles served:** II (skills are primitives — knowledge base
items with a `skill` kind), V (consent — agent proposes a skill,
owner approves before it's active), X (amendment — skills are agent
proposals, the owner ratifies).

## Deliverables

1. **Skill as KB item kind.** The existing knowledge base system
   gains a `skill` item kind. A skill item has: `title` (the
   skill name), `body` (markdown — the procedure), `source`
   (agent-proposed | owner-authored), `status` (draft | active |
   archived), `recipe_ids` (which recipes use this skill),
   `created_by` (recipe_id or "owner"), `version` (int).

2. **Skill injection.** Active skills attached to a recipe are
   injected into the prompt stack between the recipe's system
   prompt and the item grounding. The injection is bounded by a
   configurable byte budget (default 8192 bytes, matching DW's
   knowledge packet budget pattern). If skills exceed the budget,
   the most recently used are prioritized.

3. **Skill proposal.** During a workbench run, the agent can
   propose a new skill or an improvement to an existing one. The
   proposal is stored as a draft skill item. The owner sees draft
   skills in the workbench's result receipt and can approve
   (activate) or dismiss (archive) them. No skill becomes active
   without the owner's gesture. This follows Article V and
   Article X.

4. **Skill surface.** Skills are browsable as desk objects (they're
   KB items). They also appear in the recipe editor — the recipe's
   "Skills" section shows attached active skills and pending drafts.
   Inline editing in the DeskEditor.

5. **Skill transfer.** A skill can be attached to multiple recipes.
   The recipe editor's skill section has an "Attach existing skill"
   picker that searches the KB by title.

## Test plan

- `uv run pytest -q` — skill CRUD, skill injection into prompt
  stack, byte budget enforcement, proposal lifecycle (draft →
  active, draft → archived), multi-recipe attachment.
- Visual: run a workbench, verify the agent proposes a skill in its
  receipt, approve it, run again, verify the agent references the
  skill.
