# Desk memory and missed attention

<a id="missed-attention-and-receipts"></a>

The **Memory** app is the current Desk entry for retained work. It opens the
pages **What I owe** and **What changed this week**, a **Find or ask your desk**
field, links to Projects and People, and recall rows.

The old **Missed** title remains as an inbound anchor for the attention and
receipt projection API. It is not the name of the current Memory app. The
projection is a read model over source records. It does not replace those
records or act as an audit log.

## Open it

1. Open **Go > Memory** or select **Memory** in the Dock.
2. Read **What I owe** and **What changed this week**.
3. Enter words or a question in **Find or ask your desk**, then select **Ask**.
4. Open a Project or person link when you need its narrower context.
5. Use the recall rows when you need recall states and source references.

The unscoped Memory app reads Desk memory. A Project scope opens that Project's
Room. A query scope opens recall for that query. **Find or ask your desk** sends
a question to Ask without an About chip, so it starts with whole-Desk retrieval
rules.

Standing pages are read operations. They do not make a model call or write a
record at read time. A page sentence is served only while its cited sources
remain live in the scope. A missing page or sentence can mean that no current
source supports it.

Memory search reads retained Notes, Meetings, decisions, Artifacts, Threads,
and other supported records. Meaning search is a separate setting. Turn it on
in Settings before its local index can run. A search result is evidence to
inspect. It is not a claim that the result is complete.

## Privacy

Memory reads require the Desk read permission. Project pages use the Project
scope. People data does not enter standing pages or normal memory search. A
People link stays in its protected store and follows [People security](PEOPLE_SECURITY.md).

The Memory app can show source references and belief states such as current,
superseded, and disputed. Read the source before you rely on a belief. A model
can prepare or update a page through a configured job, but a page read does
not prove that job ran.

Attention and receipt projections contain presentation state and source
references. Acknowledge, dismiss, or restore changes only presentation. It
does not approve an effect, resolve a conflict, change a Meeting or Note, or
delete the source receipt.

## API

Memory routes use `/api/memory`.

| Route | Meaning |
| --- | --- |
| `GET /api/memory/search` | Search retained records with query, kind, Project, time, and paging filters. |
| `GET /api/memory/pages` | Read standing pages for the Desk or one Project. |
| `GET /api/memory/recall` | Read current, superseded, disputed, and owed recall results. |
| `GET /api/memory/meaning-search` | Read meaning-search state. |
| `POST /api/memory/meaning-search/turn-on` | Owner action that starts meaning-search setup. |
| `POST /api/memory/meaning-search/turn-off` | Turn meaning search off. |

The retained projection routes use `/api/desk/projections`.

| Route | Meaning |
| --- | --- |
| `GET /api/desk/projections` | List attention and receipt rows. |
| `PUT /api/desk/projections/{projection_id}/presentation` | Acknowledge, dismiss, or restore one row. |

Projection filters include `q`, `kind`, `attention_state`, `subject_ref`,
`include_dismissed`, `offset`, and `limit`. The API limits a page to 200 rows.
The response identifies counts and whether more rows exist.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Memory says **Not written yet.** | Check the named `memory.page` engine and source records. A read does not build a page. |
| A page has no sentence | Check whether its cited sources are still live in the Desk or Project scope. |
| Find or ask your desk has no answer | Check Ask's engine, sources, tools, and permission result. |
| Meaning search is unavailable | Open its Settings control and check the local index state. |
| People is missing from Memory | Open People separately. Protected People content is not copied into Memory. |
| An old Missed link is empty | Open **Memory** for current pages, or query the projection API for attention and receipts. |

## See also

- [The Desk](WEB_DESK.md): navigation, windows, and Ask.
- [Project Rooms](PROJECT_ROOMS.md): Project-scoped pages and sources.
- [People integration](PEOPLE_INTEGRATION.md): protected relationship context.
- [Glossary](GLOSSARY.md): Memory, grounding, and receipt terms.
