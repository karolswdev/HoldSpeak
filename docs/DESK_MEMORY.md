# Desk memory: attention and receipts

Desk memory shows what still needs you and what happened while you were away.
It is a read model over records that HoldSpeak already keeps.
It is not a new queue and not an audit log.

This page covers the **Desk memory** dock entry.
To search what HoldSpeak remembers, see [Memory](RELATIONSHIP_AWARE_MEMORY.md).

## Open it

1. Select **Desk memory** in the dock.
2. Read the counts at the top. They show how many items need attention.
3. Enter text in **Search receipts**, or change **Show**.
4. Select **Filter**.

**Show** has three choices: **Everything**, **Needs / running**, and **Receipts**.
Select a row to read its detail.
A detail view names the subject, the reason, the decision kind, the actual destination, the authority basis, the attempt, the outcome, and the time.

The same read model feeds the badges on Desk objects, the dock badge, and Mission Control.
These surfaces do not interpret a failure or an approval on their own.
Each links back to the feature that owns the full detail and the recovery or approval action.

## Privacy

HoldSpeak rebuilds each row from its source record on every read.
A row does not copy transcripts, dictated text, proposal payloads, steering text, Artifact bodies, conflict values, model inputs, or raw errors.
The only stored state is whether you acknowledged or dismissed a row.

Acknowledge and dismiss change only how a row looks.
They do not approve an effect, resolve a conflict, change a Meeting or an Artifact, or delete the source receipt.
When the source moves to a new state, that state gets its own row and can appear again.

## API

`GET /api/desk/projections` lists rows.

| Parameter | Meaning |
| --- | --- |
| `q` | Search text. |
| `kind` | `attention` or `receipt`. |
| `attention_state` | `unseen`, `needs_attention`, `acknowledged`, or `resolved`. |
| `subject_ref` | Only rows for one subject. |
| `include_dismissed` | Include dismissed rows. |
| `offset`, `limit` | Paging. `limit` has a maximum of 200. |

The response includes counts and a page envelope with `total` and `has_more`.

`PUT /api/desk/projections/{projection_id}/presentation` takes an `action` of `acknowledge`, `dismiss`, or `restore`.
The response has `subject_unchanged: true`.
