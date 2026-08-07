---
name: meeting-preparation
description: "Assemble a prep pack: prior summary, open actions, likely topics, decisions needed."
version: 1.0.0
source: "Adapted from Hermes Agent teams-meeting-pipeline skill (MIT) + original"
tags: [meetings, preparation, agenda]
---

# Meeting Preparation

## Method

Given context about an upcoming meeting (prior transcripts, notes, agenda):

1. **Prior meeting summary.** What happened last time in 3-5 bullets.
2. **Open action items.** Unresolved items from prior meetings with owners and status.
3. **Likely topics.** Based on recent activity, what will probably come up.
4. **Decisions needed.** What needs to be decided in this meeting, with context.
5. **Prep questions.** 2-3 questions the attendee should be ready to answer.

## Output format

```
# Prep: [Meeting Name] — [Date]

## Last time
- bullet points

## Open actions
- [ ] Action — Owner — Status

## Likely topics
- topic with context

## Decisions needed
- decision with context and options

## Be ready for
- question you might be asked
```

## Rules

- Keep the total prep under 1 page. Density over length.
- Action items include status (done/in-progress/blocked/not started).
- Decisions include the options and tradeoffs, not just the question.
- If no prior meeting context is available, say so — don't fabricate history.

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
