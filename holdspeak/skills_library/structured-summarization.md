---
name: structured-summarization
description: "Summarize content with key points, decisions, actions, and open questions."
version: 1.0.0
source: "Original HoldSpeak skill"
tags: [summarization, meetings, documents]
---

# Structured Summarization

## Method

Produce a summary with exactly these sections:

1. **Key points** — The 3-5 most important facts or updates, each in one sentence.
2. **Decisions made** — What was decided, by whom, and the rationale (one line each).
3. **Action items** — Use the Action Item Extraction format if available.
4. **Open questions** — Unresolved issues, disagreements, or items deferred for later.

## Rules

- Lead with the single most important takeaway as the first sentence.
- Each section uses bullet points, not paragraphs.
- If a section has no items, write "None" — don't omit the heading.
- Never editorialize. Report what was said, not what you think about it.
- Keep the total summary under 500 words unless the input is exceptionally long.
