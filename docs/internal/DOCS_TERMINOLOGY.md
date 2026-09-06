# Documentation terminology register

This register records HoldSpeak's technical terms for documentation authors.
It supplements the [public glossary](../GLOSSARY.md) and [canonical product names](POSITIONING.md#canonical-feature-names).
It does not reproduce the ASD-STE100 dictionary or approve ordinary English words outside their permitted meanings.

## Technical nouns

The following groups use the subject-specific categories in ASD-STE100 Issue 9, Rule 1.5.
The category numbers refer to the standard, not to HoldSpeak feature groups.

| Terms | Category | Permitted meaning and source |
| --- | --- | --- |
| Desk, Chair, Floor, arrival, Speak, Places, Settle in, Concierge, Interview, Thought Workbench | 19: computer science and information technology | Named product surfaces and controls. Use the meanings in the public glossary. |
| Thread, Note, Artifact, Project, Zone, decision record, Receipt, grant, Watch, assignment | 19 | Product records or contracts. Use the schema meaning, not a metaphor. |
| agent, Coder session, Steward, Heartbeat, Cadence, Rhythm, Resourceful | 19 | Specific product components or execution concepts. Keep an agent distinct from a Coder session. |
| Model Library, model, engine, runtime, endpoint, inference, capability, context, grounding | 19 | Model availability, input, routing, or execution concepts. Define ambiguous terms on first use. |
| MCP, API, HTTP, JSON, SQLite, WebSocket, CLI, GGUF, MLX | 19 | Protocol, interface, format, database, or runtime identifiers. Expand an abbreviation when the reader needs its meaning. |
| macOS, Linux, GitHub, Jira, Confluence, Whisper, HoldSpeak | 11: names of people, organizations, and products | Product or organization names. Preserve their spelling. |
| ASD-STE100, SRS, acceptance test, specification | 15: documents and standards | Identified documents and their parts. Do not imply certification from a document title. |
| Repository paths, command names, schema fields, environment variables | 19 | Literal software identifiers. Format them as code and preserve their exact bytes. |

An ordinary noun does not become an allowed technical term merely because an author puts it in this table.
New entries need a defined software meaning, a category, and a source in the product contract or interface.
Use the glossary for the reader's definition and this register for the editorial decision.

## Technical verbs

These terms describe computer processes under Rule 1.12, category 2.
Use them only for the listed actions and with the verb forms permitted by the standard.

| Verb | Intended action |
| --- | --- |
| click, tap, type | Supply pointer, touch, or keyboard input. Prefer **select** when the input method does not matter. |
| copy, paste | Use the clipboard controls. |
| save, store | Persist the specified record or data. Do not use these verbs for an unsaved draft. |
| open, close | Change the state of a window, record view, or file. |
| drag, scroll, resize, minimize, maximize | Operate the corresponding interface control. |
| install, download, upload | Perform the specified software or data transfer operation. |
| configure, enable, disable, reset | Change a named setting or configuration. State the scope and result. |
| encrypt, decrypt | Perform the named cryptographic operation. |
| validate, invalidate | Apply a specified contract check or change the validity of a record. |
| synchronize | Copy supported state between defined peers. Do not imply that every preference synchronizes. |

## Literal labels

Keep the exact control label when an instruction must identify a button or field.
For example, **Try draft**, **Keep idea**, and **Use these** have different effects.
Treat a label as a technical name. Write the surrounding instruction in controlled English.
An unusual label does not authorize the same wording throughout ordinary prose.

## Add a term

1. Check the public glossary and canonical-name table for an existing term.
2. Check the official dictionary for the intended word, part of speech, and meaning.
3. If a technical term is necessary, record its category and software meaning here.
4. Add or update the public definition when users need it.
5. Update the referring guides in the same change.

## See also

- [Writing standard](DOCS_STYLE.md): language review and page structure.
- [Public glossary](../GLOSSARY.md): reader-facing meanings.
- [ASD-STE100](https://www.asd-ste100.org/): authoritative standard and downloads.
