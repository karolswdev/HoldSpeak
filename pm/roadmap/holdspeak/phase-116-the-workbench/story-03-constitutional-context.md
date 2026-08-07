# HS-116-03 — Constitutional context

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-01
- **Unblocks:** HS-116-07, HS-116-08
- **Owner:** unassigned

## The thesis (the bar)

The owner writes context that every agent run receives — always,
without grounding it per-conversation. This is the Hermes SOUL.md
concept and the DW project-context concept, surfaced on the Desk as
an editable document. The prompt stack becomes:

```
Constitutional context (immutable per run)
→ Recipe system prompt (the agent's role)
→ Skills (reusable procedures, HS-116-06)
→ Item grounding (meetings, artifacts, resources)
→ Item body (the task itself)
```

When this ships, the user can write "I'm a senior architect at
$COMPANY, I use TypeScript and Python, my LLM provider is
OpenRouter, never use React class components" and every agent on
every workbench knows it.

**Articles served:** II (a primitive — the context document is a
desk object), III (honest egress — the context itself never leaves
the machine unless a run carries it to an inference target, and
egress is badged), VII (no prose — the editor is the surface, not a
settings form with explanatory paragraphs).

## Deliverables

1. **ConstitutionalContext DB model.** Single-row table (or config
   key): `content` (markdown), `revision` (int, auto-incremented on
   save), `content_hash` (sha256), `updated_at`. Only one active
   document — this is the owner's voice, not per-project.

2. **API routes.** Under `/api/constitutional-context`:
   - `GET /` — current content, revision, hash.
   - `PUT /` — update content, auto-increment revision, recompute
     hash.

3. **Prompt injection.** Every agent run path (recipe chat, recipe
   run, ask, workbench run) injects the constitutional context as
   the first system message tier. The injection records the revision
   and hash in the run receipt, so every run declares exactly which
   context it received. Matches the Hermes pattern: immutable for
   the duration of the run, even if the owner edits it mid-session.

4. **Desk surface.** The constitutional context opens as a desk
   window — a DeskEditor with the markdown document. No settings
   form. Just the editor. Accessible from Settings or from a new
   "Context" entry in the dock.

5. **Budget gauge.** The context document shows its token count
   (estimated via the existing budget gauge infrastructure). The
   owner sees how much of the context window they're consuming with
   their constitution.

6. **DW project-context bridge.** If DW Phase 36 is available (the
   `pm/context/` directory exists and DW is wired), the
   constitutional context is also written as a DW project context
   revision. This means DW-backed workbenches (delivery workbench)
   and standalone workbenches share the same constitutional layer.

## Test plan

- `uv run pytest -q` — CRUD round-trip, revision auto-increment,
  hash stability, injection into recipe chat/run/ask/workbench-run
  paths, receipt records revision+hash.
- Visual: open the constitutional context editor, write a paragraph,
  save, open a chat with any agent, verify the agent references the
  context.
