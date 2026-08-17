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

## Deliberately unavailable

The first People delivery has no sync, sharing, export, backup/recovery, connector,
MCP, global search, Ask/Memory grounding, recording, inference, scheduled brief,
nudge, scoring, ranking, or employment recommendation path. `shared_intent` records
a future access intention; it does not mean another participant can view the item.

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
