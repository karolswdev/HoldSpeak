---
name: grounded-citations
description: "Every claim from a source gets an inline citation with verifiable provenance."
version: 1.0.0
source: "Adapted from Hermes Agent grounded-citations skill (MIT)"
tags: [citations, provenance, grounding]
---

# Grounded Citations

## Method

When referencing information from provided sources:

1. **Cite inline** immediately after the claim: `[Source: Meeting 2026-08-01, "exact quote or paraphrase"]`.
2. **Never synthesize without attribution.** If you combine multiple sources, cite each.
3. **Distinguish** between direct quotes and paraphrases. Quotes use quotation marks.
4. **Flag gaps.** If the sources don't cover a claim, say so: "Not addressed in provided materials."

## Rules

- Every factual claim must trace to a source or be explicitly marked as your inference.
- Prefer quoting over paraphrasing when the exact wording matters.
- When sources conflict, present both with citations and note the conflict.
- Never fabricate a citation. If you're unsure of the source, say "unattributed."

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
