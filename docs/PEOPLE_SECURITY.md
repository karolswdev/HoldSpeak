# People security boundary

The People capability holds third-party relationship material. It has a stricter
custody contract than the normal plaintext HoldSpeak database.

## What People does

- **Manual and notes-only.** You enter relationships, 1:1 agenda and private prep,
  requests, and your own manager commitments. HoldSpeak has no People audio,
  transcript import, speaker identity binding, or automatic extraction.
- **Aliases and calendar links.** The calendar series link and the owner alias are
  your own deliberate acts. They are encrypted inside the relationship record.
  Matching happens at read time. The plaintext database never stores a person
  reference.
- **Computed in memory.** The 1:1 brief is built in memory and never saved. The
  Monday Brief person sections (`person_sections`) are built at the HTTP route and
  the MCP adapter after the brief service returns. The `MondayBrief` dataclass and
  its `monday_briefs` and `monday_brief_items` tables never hold person content.
  The `holdspeak://briefs/latest` MCP resource serves the person-free dataclass.
- **Follow-through.** HoldSpeak decrypts accepted manager commitments only for the
  authenticated board response. It does not copy them to `action_items`, Cadence,
  the main database, or any other lifecycle store.

## How the data is protected

- **Encrypted before it is saved.** HoldSpeak writes sensitive values as canonical
  UTF-8 JSON and encrypts them with AES-256-GCM before SQLite sees them. The AAD
  binds the ciphertext to the store format, a random record ID, the record kind,
  and the key ID. Every write uses a fresh random 96-bit nonce.
- **Native key custody.** The random 256-bit key lives only in macOS Keychain or
  Linux Secret Service. HoldSpeak accepts a provider only if its backend is on an
  allow-list (`holdspeak/people/keys.py`). A missing, locked, mismatched, or
  unavailable credential gives a named locked or unavailable state. There is no
  weaker fallback.
- **Private store.** The People directory is owner-only. SQLite sees only random
  IDs, fixed enums, timestamps, the nonce, the key ID, and ciphertext. Names,
  relationship structure, note text, dates, visibility, and source meaning stay
  inside the ciphertext.

## MCP access

People does not enter generic MCP primitives, Follow-through resources, or
search. People tools and resources default to `write` for the local owner
process. Set `HOLDSPEAK_MCP_PEOPLE_ACCESS` in the hub's environment before the hub starts:

- `read` reduces access.
- `off` disables People over MCP. The adapter then leaves out `person_sections`.

MCP is a disclosure boundary. Returned content leaves HoldSpeak memory over stdio,
and the MCP client can keep or forward it.

The adapter returns relationship metadata and the records whose encrypted
visibility is `shared_intent`. It filters out leader-private 1:1s, private prep,
agenda, grounding notes, requests, and commitments before it serializes. A guessed
private record ID is refused by name. `people.one_on_one.brief` checks access,
filters encrypted items, and returns a `policy` block that names the disclosure
boundary.

The default `write` mode can create shared-intent records and move shared
commitments between states. It cannot initialize or recover the store, archive or
delete relationships, or run capture, inference, scoring, search, sync, export, or
connectors. The repository `.mcp.json` sets no override, so it uses the default.

`people.grounding.get` assembles the shared-intent notes, open requests,
commitments, and 1:1 evidence for an MCP client that you trust. It runs no
inference, scoring, save, or model call. It returns its disclosure policy with the
temporary bundle. If a client then starts an agent, that decision is the client's.
HoldSpeak never grounds a model on its own.

`shared_intent` records an access intention. It does not mean that another person
can see the item.

## What People does not do

People has no sync, sharing, export, backup or recovery, connector, global search,
Ask or Memory grounding, recording, People-owned inference, scheduled brief,
nudge, scoring, ranking, or employment recommendation path.

The policy refuses these requests:

- scoring or ranking an individual
- advice on performance, pay, promotion, discipline, or termination
- productivity, activity, or presence proxies
- inference of sentiment, emotion, personality, health, burnout, loyalty, or flight
  risk
- automatic opportunity allocation
- comparison between people.

A refusal gives a stable reason code and does not repeat the content.

## Where People content must not appear

- `holdspeak.db`, its WAL and SHM files, and automatic migration backups.
- Global search, Memory, Ask, the sync inbox and outbox, and primitive
  serialization.
- Cadence loops, evidence, next actions, nudges, audits, and Daily Brief storage.
- Kernel operation and receipt text, logs, exception details, and broadcasts.
- Meeting exports, files, Slack, webhook, and GitHub connectors, and automatic
  model grounding.

There are two deliberate exceptions.

- **`shared_intent` MCP responses.** They exist only in the sidecar response memory
  and stdout. They must never reach the plaintext database, logs, receipts,
  resources outside People, or background stores. Leader-private content is always
  excluded.
- **Send to Workbench.** When you press **Send to Workbench**, the chosen
  commitment wording and linked Project grounding become an ordinary Workbench item
  in the main database. An existing agent workflow can then run it. The UI names
  the destination. There is no background projection. Workbench results stay
  Workbench data. People keeps only stable execution references and satisfaction
  evidence. This is the only path from People content into the main workflow.

Readiness and audit data hold no content: a fixed state and reason code, a storage
class, the native provider type, a non-secret key ID, a fixed operation class, the
outcome, and a random opaque record ID where needed. No name, note, relationship
label, due date, source text, or ciphertext detail belongs in a log or receipt.

## Lose the key

HoldSpeak has no automatic backup or recovery for People. A copied People database
stays encrypted. It cannot be read without its OS credential. If you lose that
credential, the People data can be unreadable for good. HoldSpeak does not make a
replacement key, a plaintext recovery file, or a silent reset.

## Release checks

A release that includes People must prove these points:

- the correct key works after a restart
- a wrong, missing, or locked key fails
- a changed nonce or AAD is rejected
- file permissions are owner-only
- sentinel names and text do not appear in the raw People or main database bytes,
  WAL and SHM files, logs, search, sync, Cadence, receipts, backups, exports,
  errors, or broadcasts.

Production use also needs a walk through a real supported native credential store.

See also [Security and privacy](SECURITY.md#2-storage-and-at-rest-posture).
