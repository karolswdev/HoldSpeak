---
name: ocr-and-documents
description: "Extract and structure text from PDFs, scans, and images."
version: 1.0.0
source: "Adapted from Hermes Agent ocr-and-documents skill (MIT)"
tags: [ocr, documents, extraction]
---

# OCR and Document Reading

## Method

When given a document, scan, or image with text:

1. **Extract** all visible text, preserving structure (headings, lists, tables).
2. **Structure** the output: section headings become markdown headings, tables become markdown tables.
3. **Flag uncertainty.** If text is unclear or partially occluded, mark it: `[unclear: possible text]`.
4. **Preserve order.** Maintain the reading order of the original document.

## Rules

- Never guess at illegible text — flag it.
- Preserve the document's hierarchy: title > section > subsection > body.
- Tables should maintain column alignment. Use markdown table syntax.
- If the document has multiple pages, note page boundaries.
- Handwritten text gets lower confidence — note this explicitly.

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
