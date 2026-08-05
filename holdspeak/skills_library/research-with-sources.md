---
name: research-with-sources
description: "Systematic research: define question, gather sources, synthesize, cite."
version: 1.0.0
source: "Adapted from Hermes Agent research-paper-writing + grounded-citations skills (MIT)"
tags: [research, synthesis, citations]
---

# Research with Sources

## Method

1. **Define the question.** State exactly what you're trying to answer.
2. **Gather sources.** Use all provided materials. Note what's missing.
3. **Extract findings.** For each source, pull the relevant facts with citations.
4. **Synthesize.** Combine findings into a coherent answer. Note where sources agree and disagree.
5. **Cite everything.** Every claim traces to a source or is marked as inference.

## Output structure

- **Question**: the research question restated
- **Sources consulted**: list with one-line descriptions
- **Findings**: synthesized answer with inline citations
- **Gaps**: what the sources didn't cover
- **Confidence**: high/medium/low with rationale

## Rules

- Never present inference as fact. "Based on [Source], it appears..." not "It is..."
- If sources conflict, present both views and note the conflict.
- Distinguish between primary sources (data, transcripts) and secondary (summaries, opinions).
- A finding without a citation is an unverified claim.

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
