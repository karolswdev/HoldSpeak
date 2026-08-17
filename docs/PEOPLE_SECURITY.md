# People security boundary

The People capability holds third-party relationship material. It therefore has a
different custody contract from HoldSpeak's normal, plaintext local database.

## Shipped boundary

- **Manual and notes-only.** Relationships, 1:1 agenda/private prep, requests, and
  explicit manager commitments are entered by the local owner. There is no People
  audio, transcript import, speaker/calendar binding, or automatic extraction.
- **Encrypted before persistence.** Sensitive values are serialized as canonical
  UTF-8 JSON and encrypted with AES-256-GCM before SQLite receives them. AAD binds
  ciphertext to the store format, random record ID, record kind, and key ID; every
  write uses a fresh random 96-bit nonce.
- **Native key custody.** The random 256-bit key is stored only in macOS Keychain or
  Linux Secret Service. A production provider is accepted only when its backend is
  explicitly allow-listed. Missing, locked, mismatched, or unavailable credentials
  produce a named locked/unavailable state—never a weaker fallback.
- **Private sidecar.** The People directory is owner-only. Random IDs, fixed enums,
  timestamps, nonce, key ID, and ciphertext are the only SQLite-visible record
  fields. Names, relationship topology, note text, dates, visibility, and source
  meaning remain inside ciphertext.
- **In-memory Follow-through projection.** Accepted manager commitments are
  decrypted only for the authenticated board response. They are not copied to
  `action_items`, Cadence, the main database, or another lifecycle authority.

## MCP disclosure capability

People does not enter generic MCP primitives, Follow-through resources, search, or
the default sidecar catalogue flow. Direct People tools and resources are disabled
unless the owner starts the stdio sidecar with
`HOLDSPEAK_MCP_PEOPLE_ACCESS=read|write`. This is a process-start disclosure
decision: returned content leaves HoldSpeak process memory over stdio and the parent
MCP client may retain or forward it.

Even when enabled, the adapter exposes relationship metadata plus only records whose
encrypted visibility is `shared_intent`. Leader-private 1:1s, private prep, agenda,
grounding notes, requests, and commitments are filtered before serialization; guessed private record
IDs named-refuse. Write mode can create shared-intent records and transition shared
commitments, but cannot initialize/recover the store, archive/delete relationships,
or invoke capture, inference, scoring, search, sync, export, or connectors. The
repository's default `.mcp.json` leaves People access off.

## Deliberately unavailable

The first People delivery has no sync, sharing, export, backup/recovery, connector,
generic primitive MCP access, global search, Ask/Memory grounding, recording, inference, scheduled brief,
nudge, scoring, ranking, or employment recommendation path. `shared_intent` records
an access intention; it does not mean another participant can view the item. The
opt-in MCP adapter is the only shipped disclosure of that class in this delivery.

The policy boundary refuses individual scoring/ranking; performance, pay,
promotion, discipline, or termination recommendations; productivity/activity or
presence proxies; sentiment, emotion, personality, health, burnout, loyalty, or
flight-risk inference; automatic opportunity allocation; and cross-person
comparison. Refusals expose stable reason codes without echoing content.

## Key loss and recovery

There is no recovery or automatic backup in this delivery. A copied People database
remains encrypted and is unusable without its matching OS credential. Losing that
credential can make People data permanently unreadable. HoldSpeak does not create a
replacement key, plaintext recovery file, or silent reset. Rotation, encrypted
backup, recovery preview, and destructive discard require a later independently
reviewed design.

## Observable surfaces

People content must not enter:

- `holdspeak.db`, its WAL/SHM files, or automatic migration backups;
- generic FTS, Memory/Ask, sync inbox/outbox, or primitive serialization;
- Cadence loops, evidence, next actions, nudges, audits, or Daily Brief storage;
- kernel operation/receipt text, logs, exception details, or broadcasts;
- meeting exports, files, Slack/webhook/GitHub connectors, or remote/local models.

Authorized `shared_intent` MCP responses are the explicit exception: they exist only
in the sidecar's response memory/stdout and must never be observed into the plaintext
main database, logs, receipts, resources outside the People family, or background
stores. Leader-private content remains categorically excluded.

Manual grounding notes are encrypted People records, not model-created profiles.
`people.grounding.get` can assemble the shared-intent notes, open requests,
commitments, and 1:1 evidence for an explicitly trusted MCP client. It performs no
inference, scoring, persistence, or model call, and returns its disclosure policy
with the transient bundle. A client that later invokes an agent owns that separate
decision boundary; HoldSpeak does not silently ground a model.

Readiness and audit metadata are content-free: a fixed state/reason code, storage
class, native provider type, non-secret key identifier, fixed operation class,
outcome, and random opaque record ID where required. No name, note, relationship
label, due date, source text, or ciphertext diagnostic belongs in a log or receipt.

## Release proof

A release containing People must prove correct-key restart; wrong/missing/locked-key
failure; nonce/AAD tamper rejection; owner-only permissions; and absence of sentinel
names/text across raw People/main database bytes, WAL/SHM, logs, FTS, sync, Cadence,
receipts, backups, exports, errors, and broadcasts. Production enablement also
requires a real supported native credential-store walk.
