# HS-116-16 — Agent memory

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-06, HS-116-07
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

Agents learn. Every workbench run that completes — success or
failure — writes back what it learned. Every run that starts reads
what previous runs learned. Skills are the owner-approved layer
(explicit, ratified). Memory is the automatic layer (observed,
advisory). Together they compound: an agent that reviews PRs
twenty times gets better at it, not because someone manually wrote
twenty skills, but because each run leaves a trace the next one
recalls.

This is the Hermes learning loop + DW Phase 35 memory glass,
brought into the HoldSpeak workbench.

**Articles served:** V (consent — memory informs, never authorizes;
skill promotion requires owner approval), VI (honest — the memory
pane shows what the agent knew, never hides it), IX (proof — memory
receipts are audit evidence).

**UI/UX direction:** Study DW Phase 35's memory pane: every
recalled item says why it matched, every excluded item says why it
was dropped. The memory section in the workbench window should
feel like a glass pane — transparent, inspectable, never a black
box.

## The memory model

Three tiers of agent knowledge, from most to least persistent:

```
┌─────────────────────────────────────────┐
│ SOUL (constitutional context)           │ ← owner-authored, global
│ "Who I am, my preferences, my rules"   │    never changes per-run
├─────────────────────────────────────────┤
│ SKILLS (owner-approved procedures)      │ ← agent-proposed, owner-ratified
│ "How to review PRs in this codebase"   │    explicit, versioned
├─────────────────────────────────────────┤
│ MEMORY (automatic earned records)       │ ← written by every run
│ "Last time I reviewed auth, the owner  │    advisory, bounded, inspectable
│  preferred inline comments over summary│
│  blocks. The test suite takes 4 min."  │
└─────────────────────────────────────────┘
```

**Memory is NOT constitutional context and NOT skills.** It's a
third layer: automatic, advisory, bounded, and transparent. Memory
cannot authorize, satisfy a gate, or substitute for skills. Memory
can inform the agent's next run.

## Deliverables

1. **Memory store.** Per-workbench append-only JSONL at
   `~/.holdspeak/workbenches/<id>/memory.jsonl`. Each entry:
   ```json
   {
     "run_id": "wbrun-...",
     "timestamp": "2026-08-03T02:00:00Z",
     "kind": "observation" | "lesson" | "preference",
     "content": "The owner prefers inline comments...",
     "item_title": "Review PR #430",
     "provenance": { "egress": "local", "model": "llama-3.3" }
   }
   ```
   Entries are bounded: max 100 per workbench, oldest evicted.

2. **Terminal writeback.** At the end of each item processing, the
   conductor asks the agent: "Based on this task and your output,
   what ONE thing should future runs on this workbench remember?
   Reply with a single sentence or 'nothing'." The response (if
   not "nothing") is appended to the memory store. This is a
   cheap follow-up call with a tight system prompt, bounded to
   50 tokens max.

3. **Recall before dispatch.** Before each run, the conductor
   loads the memory store (most recent 20 entries, bounded to
   2KB) and injects it as a `[MEMORY]` block between the recipe
   standing context and the item grounding in the prompt stack:

   ```
   constitutional context
   → recipe prompt + skills
   → recipe standing context
   → [MEMORY] (recalled entries)    ← NEW
   → item grounding
   → item body
   ```

4. **Skill promotion.** When the agent's writeback content is
   substantial and repeated (similar observations across 3+ runs),
   the conductor automatically proposes a draft skill from the
   pattern. The owner sees the proposal in the skills section and
   approves or dismisses. Memory that becomes a skill is marked
   `promoted` in the memory store.

5. **Memory pane in the workbench window.** A section (or wing)
   showing the last 20 memory entries with:
   - Kind badge (observation / lesson / preference)
   - Content (one line, expandable)
   - Source (which run, which item, which model)
   - Age ("3 runs ago", "yesterday")
   - A "Promote to skill" chip on any entry

6. **Memory clear verb.** The owner can clear the memory store
   for a workbench. Confirmation required (Article V). This does
   NOT clear skills — skills are a separate, explicit layer.

## Test plan

- Backend: run a workbench, verify writeback creates a memory
  entry. Run again, verify the memory entry appears in the
  recalled [MEMORY] block.
- Visual: open the memory pane after 3 runs. See entries with
  kind badges and sources. Promote one to a skill. Verify the
  skill appears in the skills section.
