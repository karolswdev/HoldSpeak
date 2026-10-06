# Memory

HoldSpeak memory is a read layer over your durable work.
It is an index. It is not a second notebook, and it does not hold facts that its sources do not hold.
HoldSpeak rebuilds each memory row from a source record, so a deleted source leaves no memory.

## What HoldSpeak remembers

You do not save to memory. The normal work is the write path.
When you keep a Note, record a Meeting, accept a Decision, keep an Artifact, or send a Thread message, that record becomes searchable.

Memory covers these kinds:

| Group | Kinds |
| --- | --- |
| Decisions | `decision`, `decision_record`, `desk_decision` |
| Records | `artifact`, `meeting`, `note`, `thread` |
| Work | `action`, `project_item`, `workbench_item`, `cadence` |
| What you sent or prepared | `send`, `project_update`, `prep_brief`, `calendar_event` |
| Other | `brief_item`, `dictation`, `steward_run`, `ask_answer` |

A match on a Meeting segment or a Thread message returns the whole Meeting or Thread.

Memory never reads raw People records, credentials, settings, kernel receipts, or unfiltered activity.
It skips parked Meetings, drafts, and sensitive Thread parts.
The correction memory of Dictation is a separate store.
HoldSpeak redacts secrets such as tokens, keys, and card numbers before it indexes a text.

The memory index lives in the HoldSpeak database.
A sweep keeps it current. A missed sweep loses nothing, because the next sweep reads the source.

## How a search works

Several retrievers run for one query. Each hit carries one `retrieval_origin`: the first retriever that found it.

| Origin | Search token | How it finds a hit |
| --- | --- | --- |
| `lexical` | KEYWORD | Full-text match on the record text. |
| `vector` | MEANING | Match by meaning, with embeddings. It needs **Meaning search** on. |
| `time` | TIME | A time phrase in the question, such as "last week", sets a date range. |
| `entity` | NAME | A person, project, or other name that HoldSpeak read from your records. |
| `relationship` | LINK | One step over a saved link, such as Meeting to Decision. |
| `observation` | none | A belief that HoldSpeak built from facts. See below. |

HoldSpeak merges the result lists by rank.
Each kind of record ranks on its own, so a long transcript cannot bury a short Decision.
Ties go to the newer record.

The link step starts from at most 32 keyword matches.
It adds at most 2 neighbors for each match and at most 64 in total.
It follows only links that HoldSpeak already saved. It never infers a link from similar words.

A Project search checks every hit against the Project before it returns the hit.

### Meaning search

Meaning search is off until the owner turns it on.
Open the **Models** window and use the **Meaning search** row.
The row shows OFF, DOWNLOADING, INDEXING, or ON.
**Turn on** downloads a small embedding model. This is the only path that starts the download.
The hub checks the file against a pinned hash.
With Meaning search off, search uses keywords, time, names, and links.
New items can take a short time to become searchable by meaning.

### Facts, beliefs, and pages

Background jobs can turn your records into more memory:

- **Facts and names.** The `memory.extract` capability reads admitted text and writes facts and the names in them.
- **Observations.** The `memory.consolidate` capability folds facts into beliefs. A belief keeps its evidence and its history. A later fact can refine, supersede, or contradict a belief.
- **Pages.** The `memory.page` capability writes standing answers. A Project has four: what we decided, what is open and who owes it, risks and disputes, and what changed this week. The desk has two: what I owe, and what changed this week.

Every page sentence cites its sources.
HoldSpeak cuts a sentence that has no source or an unsupported word.
HoldSpeak checks the sources again on each read.
When you edit or delete a source, the sentence that cites it disappears at once.
A page read makes no model call.

These jobs run only when a model is assigned to the capability, or when a local default exists.
With no model, nothing runs and nothing is written.
Set the models in the **Models** window.

## Where you see memory

| Place | What it shows |
| --- | --- |
| **Search** (`⌘K`) | Two-line hits: the matching passage, a token that names the retriever, and the day. |
| **Desk memory** window (**Go** menu) | A recall over the whole Desk or one Project. See below. |
| Project Room | Standing pages for that Project. |
| Brief | Standing pages for the desk. |
| Model prompts | Source blocks that HoldSpeak adds to a request. See below. |
| MCP and HTTP | The same data for other clients. |

## The Desk memory recall

A recall returns sections, not one flat list.
A superseded or disputed Decision never looks current.

`filter` is `all`, `decisions`, `commitments`, `briefs`, or `meetings`.
The response has these parts:

- `current`, `superseded`, and `disputed`: Decision records with rationale, source moment, and Project. The newest current Decision comes first.
- `owed`: open commitments with owner and due date, or a typed unknown such as `OWNER · UNKNOWN`.
- `meetings`, `briefs`, and `also`: other matches.
- `beliefs`: observations, under the `all` filter only.
- `remembered`: one count.

With no query, the window shows the newest memory of the desk.
The window keeps your query and filter on this device.

These verbs write through the normal services:

- **Carry into brief** calls `POST /api/decision-records/{id}/carry`. It records the current Decision, by reference, for the Project's next preparation. A repeat press has no further effect.
- **Name an owner**, **Set a date**, and **Mark done** call `POST /api/follow-through/complete` with the verb `delegate`, `due`, or `done`.
- `POST /api/decision-records/{id}/supersede` and `/dispute` seal a record.

Only **Mark done** and `dismiss` close a commitment. Each leaves a receipt.
A closed commitment refuses `delegate` and `due` until you reopen it.

## Grounding model requests

Before HoldSpeak sends a request to a model, it can add memory.
The current input is the query.
HoldSpeak loads at most 16 source blocks. Each block has a title and a `[REF: kind:id]` tag.
The request records the receipt:

```json
{
  "source_refs": ["note:n1", "meeting:m1"],
  "selection": "ecosystem_relevance",
  "matched_count": 2,
  "overflow_count": 0
}
```

Explicit attachments win. A request with attached records uses those records and adds no automatic recall.
A Thread leaves out its own messages and freezes the recalled sources on the user message.
Ask, Thread, Agent, Sequence, Workflow, Workbench, and Coder steering all use this contract.
A provider never searches memory itself.

## Search contracts

HTTP:

```text
GET /api/memory/search?query=rollback&project_id=orion&limit=20
```

MCP:

```json
{
  "name": "memory.search",
  "arguments": { "query": "rollback", "kind": "decision,meeting", "project_id": "orion", "limit": 20 }
}
```

Both take `query`, a comma-separated `kind`, `project_id`, ISO-8601 `time_from` and `time_to`, `limit` (1 to 500), and `offset`.
Other routes:

| Route or tool | Use |
| --- | --- |
| `GET /api/memory/recall` | The Desk memory recall. Takes `query`, `filter`, `limit`, and `recent`. |
| `GET /api/memory/pages` | Standing pages. Takes `scope` (`desk` or `project`) and `project_id`. |
| `memory.observations` | Beliefs with evidence and history. |
| `memory.page` | One standing page. |
| `GET /api/memory/meaning-search` | Meaning search state. |

See [API surface](API_SURFACE.md) and [MCP sidecar](MCP_SIDECAR.md) for exact fields.

## What memory does not do

- It does not call a model to rank results.
- It does not write a summary back after every Ask or Thread.
- It does not search People records, secrets, settings, or kernel receipts.
- It does not notify you about a possibly relevant memory.
- It does not bypass Project membership, permissions, egress, or receipt rules.

## Design sources

The link step adapts the parent and child recall of RAGFlow (Apache-2.0).
The facts, beliefs, and pages adapt ideas from Hindsight (MIT).
HoldSpeak copies no source code from either project.
The design is in `docs/internal/MEMORY-DESIGN.md`.
