# Documentation writing standard

Use this policy for new and revised HoldSpeak documentation.
It combines controlled English with source checks, task-oriented structure, and maintained navigation.

## Language standard

The language reference is **ASD-STE100 Simplified Technical English, Issue 9, 2025-01-15**.
Use the [official ASD standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) for exact rules and dictionary meanings.
The request named ASD-DTE100. This refresh provisionally interprets that name as ASD-STE100.
The [September review](DOC_AUDIT_2026-09.md) records this assumption and the verification limits.

Apply these language controls:

| Rule group | Editorial check |
| --- | --- |
| 1 | Check vocabulary, word function, and meaning. Register necessary domain terms separately. Use American spelling. |
| 2 | Limit noun clusters. Identify longer technical names clearly. |
| 3 | Prefer direct verbs and active constructions. Check tense and verb form. |
| 4 | Keep sentences explicit. Expand contractions. |
| 5 | Limit procedural sentences to 20 words. Give one instruction per sentence. Put prerequisites before actions. |
| 6 | Limit descriptive sentences to 25 words and paragraphs to six sentences. Keep one topic per paragraph. |
| 7 | State a relevant hazard, required action, and consequence when a safety instruction is necessary. |
| 8 | Check punctuation and the standard's word-count rules. Avoid semicolons. |
| 9 | Rewrite unsuitable constructions. Check meaning and terminology in context. |

A word-count tool cannot establish dictionary compliance, permitted meaning, or technical accuracy.
The [official download guidance](https://www.asd-ste100.org/STE_downloads.html) also distinguishes AI assistance from verified compliance.
Do not label a document certified or fully compliant without the required substantive review.
Do not copy the standard or its full dictionary into this repository.

## Product terms and labels

Use the [terminology register](DOCS_TERMINOLOGY.md) for domain nouns and verbs.
Use the [public glossary](../GLOSSARY.md) for reader-facing definitions.
The [canonical-name table](POSITIONING.md#canonical-feature-names) owns product names.

Preserve exact UI labels in bold and exact code identifiers in backticks.
For example, **Keep idea** records a suggestion choice. Keep on a reply saves a separate output.
Explain that difference instead of using one vague verb for both.

Do not replace an API field or command to make it sound simpler.
Explain the identifier in ordinary prose instead.
Use **Interview mode** for the repeatable Thread capability and **Interview pane** for Thought refinement when the distinction matters.

## Describe the available product

A public guide describes implemented behavior.
A target requirement belongs in a specification with a status and an acceptance method.
Implementation, successful execution, model quality, and owner acceptance are different claims.
State a limitation next to the capability it qualifies.

For each procedural change, inspect the control or command in the current source.
For a permission claim, inspect the operation policy and applicable tests.
For a saved-state claim, identify which store owns the state and which events preserve it.
For an automation claim, identify its actual trigger, executor, authority, and result record.

Use specific data boundaries.
Configured models, connectors, remote clients, and outbound actions can each transfer data.
Do not use a blanket assurance that only a model endpoint can receive data.
Link [Security & Privacy](../SECURITY.md) for the full contract.

## Organize a user guide

This structure is a HoldSpeak documentation convention.
ASD-STE100 supplies the language rules, not the product's information architecture.

1. State the task and result below one level-one title.
2. State the prerequisites that affect the task.
3. Give the shortest complete procedure.
4. Describe the expected result and how to inspect it.
5. Explain persistence, permissions, or limits when they affect use.
6. Add a problem/action table for common failures.
7. End with **See also** and a small set of useful links.

Use numbered steps for actions and tables for parallel comparisons.
Keep examples clearly distinguishable from actual user records.
Use explicit placeholders for unprovided IDs, names, dates, and requirements.
A screenshot must represent the described interface and have useful alternative text.
Remove a misleading screenshot from the current guide instead of treating it as evidence of current behavior.

## Organize a specification or technical reference

A specification identifies its status, scope, requirement IDs, acceptance criteria, and verification evidence.
Keep target behavior distinct from implemented behavior.
The [Interview package](architect-assistant/README.md) is an example of that separation.

Technical references can use schema tables, examples, and architecture diagrams.
Generated API and MCP inventories retain their machine-generated regions.
Change their source or generator and regenerate the output when a contract changes.
Do not hand-edit a generated roster to make a test pass.

Historical evidence retains its original observations and dates.
Move it with a provenance note when it obstructs a public task guide.
Do not rewrite an old result to imply that a new test ran.

## Links and formatting

Use relative repository links and existing heading anchors.
Use direct external links for authoritative standards and external documentation.
Use **See also** as the footer heading.
Separate a link from its description with a colon.

Use periods, commas, colons, or parentheses in public prose.
The repository also disallows em and en dashes in that prose.
A literal UI string can retain its exact punctuation under the existing narrow guard exception.

Keep headings in order, code fences closed, and tables aligned by column count.
Keep Markdown examples separate from executable commands.
Never include real credentials or private data in an example.

## Review and maintain

Every behavior change must update its user procedure and relevant reference in the same PR.
Add new public guides to the documentation index.
Update glossary entries when product terminology changes.
Repair links to a changed heading in the same change.

The [contributor guide](../../CONTRIBUTING.md) gives the check commands.
The navigation checker checks public guides, their local links, and Markdown heading targets.
The existing drift guards check product terms, counts, generated contracts, and other repository rules.
Neither check replaces the language review above.

Before submitting a documentation PR, record:

- The current implementation sources used to verify procedures.
- The language and terminology review performed.
- The exact checks and their results.
- Any unverified behavior or remaining language review.

The [September review](DOC_AUDIT_2026-09.md) separates fully rewritten entry guides from retained detailed references.
It does not claim that every historical document has passed a complete STE review.

## See also

- [Terminology register](DOCS_TERMINOLOGY.md): domain terms and editorial decisions.
- [Public glossary](../GLOSSARY.md): definitions for users.
- [Contributing](../../CONTRIBUTING.md): validation and commit workflow.
- [September documentation review](DOC_AUDIT_2026-09.md): scope and verification record.
