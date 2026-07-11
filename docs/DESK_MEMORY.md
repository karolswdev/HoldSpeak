# Desk memory: attention and receipts

Desk memory answers two returning-user questions in one place: what still needs
me, and what happened while I was away? It is an additive read model over the
records HoldSpeak already owns. It is not a new queue or audit log.

Open **Desk memory** from the Desk to see visible counts, search and filter the
semantic list, and load older results without a fixed-item cutoff. Each card
names its subject, reason, decision kind, actual destination, authority basis,
attempt and outcome, time, and authoritative source. Meeting, artifact,
persona/workflow run, coder steering, integration proposal, dictation, sync,
capture recovery, background job, and Cadence records share this vocabulary.

The same projections feed contextual Desk badges, Qlippy, Mission Control, and
the native Queue HUD. Those surfaces do not reinterpret a failure or approval
independently. They link back to the feature journal for its full detail and
recovery or approval action.

## Privacy and ownership

Projection rows are rebuilt from their source records on every read. They do
not copy transcripts, dictated output, proposal payloads, steering text,
artifact bodies, conflict values, model inputs, or raw errors. The only durable
Desk-memory state is whether the owner acknowledged or dismissed a particular
projection.

Acknowledging or dismissing a card changes presentation only. It cannot approve
an effect, resolve a conflict, alter a meeting, change an artifact, or delete
the source receipt. If the source advances to a new lifecycle state, that state
gets its own stable projection and can surface again.

## API

`GET /api/desk/projections` supports `q`, `kind`, `attention_state`,
`subject_ref`, `include_dismissed`, `offset`, and `limit` (capped at 200 per
page). The response includes filtered counts, stable contextual subject counts,
and an explicit page envelope with `total` and `has_more`.

`PUT /api/desk/projections/{projection_id}/presentation` accepts
`acknowledge`, `dismiss`, or `restore`. Its response explicitly confirms that
the subject was unchanged.
