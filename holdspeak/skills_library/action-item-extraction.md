---
name: action-item-extraction
description: "Extract concrete action items with owners, deadlines, and context."
version: 1.0.0
source: "Original HoldSpeak skill"
tags: [meetings, actions, tracking]
---

# Action Item Extraction

## Method

Scan the input for commitments, assignments, and next steps. For each:

1. **Action**: What needs to happen, in imperative form ("Ship the fix", not "The fix should be shipped").
2. **Owner**: Who committed to doing it. Use the speaker's name, not "someone."
3. **Deadline**: When it's due. If no explicit deadline, note "no deadline stated."
4. **Context**: One sentence on why this matters or what it blocks.

## Output format

```
- [ ] **Action** — Owner — Deadline
  Context: one sentence
```

## Rules

- Only extract items where someone committed or was assigned. "We should think about X" is not an action item.
- Preserve the owner's exact words for the commitment when possible.
- If the same action appears multiple times, consolidate — don't duplicate.
- Sort by deadline (soonest first), then by mentioned order.
