# Security and privacy

HoldSpeak is local-first, single-user software. Local-first describes the hub
and its default storage. It does not mean that every configured model,
connector, agent CLI, browser client, or destination is local. Check the
assigned engine, egress chip where
provided, and execution Receipt for the route that was used. A route label alone
does not prove where every byte went.

HoldSpeak has no product telemetry, crash reporting, or background beacon.

This page describes implemented controls and their limits. It is not a promise
that cooperating same-user code is a sandbox.

## Control mode

The modes are **Secure**, **Normal**, and **YOLO**. The wire values are
`safe`, `neutral`, and `yolo`. **YOLO** is the default.

YOLO permits an eligible operation inside its configured scope without another
HoldSpeak prompt. It does not waive authentication, destination binding, the
allow-list, payload binding, pane identity, or the terminal Receipt. Secure and
Normal can require a preview, owner authorization, or an exact scoped grant.

The decision applies to a concrete operation descriptor. It is not a general
permission for a model or a process.

## Interview context and model work

An Ask or Thread turn starts with its selected records and frozen references.
Tool-capable Ask can retrieve additional permitted Desk context through its
tools. The **About** objects are a starting point, not a limit. The model route
receives the prompt and any context that the turn admits. A local model keeps
that request on the hub. A configured endpoint, mesh node, or CLI provider can
receive the prompt and selected records or tool results.

The **People** section of Interview opens the protected People surface. A normal
Thread does not turn private People material into generic memory. The agent
brief composer includes People data under Conductor R7 when its grounded source
supplies it. The brief redacts secrets, records source references, and reports
the People cut value.

## Kernel boundary: cooperating code, not a sandbox

The kernel admits operations, tracks principals, binds payloads and
destinations, and writes receipts. It is a cooperating application boundary.
It is not an OS sandbox against code that already runs as the same user. Such
code can read files, open sockets, start processes, or bypass HoldSpeak.

Use OS isolation for untrusted plugins, agent-written programs, or a model that
must not access the user account. A process that bypasses the hub is outside
these controls.

Desktop typing crosses a process boundary through the configured typing relay.
If the relay outcome is uncertain, HoldSpeak reports `indeterminate` and does
not retry blindly.

### Kernel effect census

The Article XI transitional effect ledger reports `0 total / 0 covered / 0
exempt / 0 debt` for the five named census families under `holdspeak/`. This is
the ledger's classified statement count, backed by its machine-pinned proof
map. It is not a universal sandbox claim: installed libraries, the operating
system, and same-user code remain outside the kernel's control.

## Inference authority and schedules

Every physical model call is a child inference attempt. It freezes the engine
assignment, route boundary, and input reference, then records a terminal
receipt. A fallback is another attempt with its own route and receipt.

### Scheduled Workbench runs

An enabled automation stores its trigger, source scope, engine, output, and
authority. Its delegation binds the Workbench and Agent revisions, exact
cadence, deployment revision, terms digest, and optional expiry. The scheduler
rechecks these terms at the due tick. A missing, revoked, expired, disabled,
stale, changed, or duplicate schedule is refused before dispatch. A schedule is
not proof that a run happened. Read the run record and terminal receipt.

### Scheduled recording

An armed recording stores its exact calendar rule. When it fires, it uses the
ordinary meeting start contract. It can capture only when the local audio
devices and permissions are ready. The schedule does not grant a model route or
an outbound destination. A held audio floor, a missed hub window, or an
interrupted countdown leaves a named receipt. Editing time, cadence, duration,
or timezone creates a new delegation state.

## 1. Data classes

| Class | Examples | Main boundary |
| --- | --- | --- |
| Capture | Microphone and system audio chunks | Local recorder, journal, and database |
| Speech text | Transcript and dictation text | Local transcriber, then any assigned model route |
| Desk records | Notes, meetings, decisions, projects, Threads | Main SQLite store and selected tools |
| People | Relationships, shared intent, private preparation | Separate encrypted People store |
| Credentials | Web token, model keys, connector keys | Owner-only config or native key custody |
| Effects | Typing, issue creation, Slack, webhook | Destination-specific operation and receipt |
| Agent work | Brief, repository, process, worktree | Agent launch scope and process receipt |

The main database also contains speaker embeddings, activity records, operation
metadata, and paired-delivery receipts. Browser recovery storage can contain
editable drafts or one bounded pending WAV. Native dictation recovery can hold a
bounded draft, destination, delivery id, or PCM until transcription or delivery
succeeds. These stores have separate retention and deletion paths.

## 2. Storage and at-rest posture

The normal data plane is SQLite under the configured data directory. It is not
encrypted by the meeting or Desk layer. Use operating-system disk protection
and file permissions for the main database.

The database uses WAL files while the hub is open. Do not place the data
directory in a synced folder. Browser-history reads use temporary copies and do
not modify the browser database. Activity retention and per-domain exclusion
apply when those records enter the activity ledger.

### Encryption at rest

People records use AES-256-GCM before SQLite sees their payload. The key is held
by the native key store. A missing, locked, mismatched, or unsafe key makes the
People store unavailable. It does not silently open an empty replacement.

### The People resolver

Meeting, Project, and follow-through services can resolve a People identity at
read time. The resolver refuses ambiguous matches. It does not put private
People notes into the plain transcript or generic search index.

### The reviewer nudge

The reviewer nudge runs one subprocess: `gh pr comment`
(`GITHUB_PR_COMMENT_MANIFEST` in `github_pr_actuator.py` allows that one argv
prefix). Two gates must both open:

1. The project policy lists the `github_comment` effect kind in
   `eligible_effect_kinds_json`. The default is empty.
2. You press Send on the nudge card after you read the exact comment text and the
   `GITHUB.COM` host badge.

The comment posts from your own authenticated `gh` identity. The nudge text names
no person by default. HoldSpeak cannot retract a posted comment. The receipt in
the service event ledger holds the comment URL, PR number, reviewer name, time,
host, and approving principal. A refusal or failure also leaves a receipt with a
named reason.

A project update drafted by a model sends the prompt and output to the host named
by the deployment revision. The Send preview and Engines name that host. The
deterministic fallback has no egress.

### The remote boundary

The hub listens on its configured host, but the persisted `bind_host` value is
not a network control. **No listener or peer-address check uses it,** so it is
not a network fence. On `POST /api/mcp`, a non-loopback request with the owner
token is refused. The owner web token is not a substitute for peer isolation.
The stdio MCP sidecar forwards JSON-RPC to the running loopback hub; it does not
open the database itself. Do not expose the hub to an untrusted network.

### Connector boundaries

GitHub, Jira, Confluence, calendar, email, Slack, webhooks, model endpoints,
mesh nodes, remote clients, and installed agent CLIs are separate boundaries. A
connector can send data to its provider. The connector's credential and
destination rules do not make model inference local.

Confluence uses the configured read-only CLI allow-list. Calendar HTTPS sources
use bounded fetches and refuse redirects. File calendar sources cause no network
egress. Connector packs run in the hub process with the owner's permissions;
their manifest is an honesty check, not a sandbox.

- **Confluence.** The connector runs the `acli` CLI with a read-only allowlist
  (`auth status`, `auth switch`, `space list`, `space view`, `page view`,
  `blog list`, `blog view`). HoldSpeak makes no Confluence REST call. The CLI holds
  the credentials.
- **Calendar.** The only egress is the ICS fetch for HTTPS sources
  (`calendar_ingest_conductor.py`). The feed URL is in the feed's Edit view in Settings > Accounts.
  HoldSpeak stores no calendar credential and runs no OAuth flow. File sources
  cause no network egress. Arming a recording is your standing consent for a Room
  or for all calendar meetings. Armed never means started. The meeting watch reads
  the local database only and calls no model.

## 3. Trust boundaries

1. The local hub process runs as the owner and is trusted with the main data.
2. The browser is an authenticated client. Its drafts and pending audio have
   their own browser storage limits.
3. The web runtime normally binds loopback. A non-loopback bind requires the
   web token for HTTP requests. The device audio WebSocket has its own PSK
   boundary, and WebSocket bus auth has its own route behavior.
4. A model endpoint receives the frozen request selected for its assignment.
5. An agent process receives its brief and scoped launch credentials.
6. A desktop relay can type into the focused application. It is not a content
   sandbox.
7. A connector or destination provider receives the payload named by its
   operation.

The audio floor is a leased one-at-a-time arbiter shared by browser open mic,
hotkey dictation, meeting capture, and wake listening. It does not carry audio
itself. A paired device audio stream authenticates with a PSK and sends audio to
the hub over its device route.

### Session steering rules

Coder steering binds the answer to the current agent wait, pane identity,
destination, and launch. An owner answer press can authorize that one current
wait. A stale wait or pane is refused. YOLO does not remove those checks.

Secure and Normal use a bounded in-memory pane grant. YOLO can deliver text and
allowed keys to a registered session or exact pane inside the configured scope.
The relay re-resolves the current pane before each send. A missing, recycled,
or retargeted pane is refused. Mode changes invalidate affected grants, and a
hub restart clears in-memory grants.

Named keys and control keys use an allow-list. A configured steering node
receives only the command, expected pane identity, and its own bearer token. The
node performs the policy check and writes the audit on the machine that types.

### Tool-call gate rules

Agent tool calls are checked against the launch scope and tool family. Agents
cannot change control posture, impersonate the owner, or use a missing launch
rule. The tool receipt records the operation and result. The Coder gate is one
chokepoint. A held call has a bounded preview, a first-write-wins decision, and
restart invalidation. The preview truncates canonical JSON after redaction; it
does not make unknown secrets safe.

## 4. Egress points: everywhere data can leave the machine

| Path | Data that can leave | Control |
| --- | --- | --- |
| Remote model endpoint | Prompt and selected context for an admitted inference attempt. Raw audio and embeddings are not sent by this path. | Frozen deployment revision, assigned host, child attempt, and Receipt. A fallback is a new attempt. |
| Supported CLI inference engine | Prompt and selected context through the installed CLI and its provider. | The CLI settings and provider account are the boundary. It is not a coding-agent launch. |
| Coding-agent handoff | Brief, selected Desk context, repository facts, and any People data carried by the brief. | Owner handoff, launch scope, worktree, process receipt, secret redaction, and 32 KB brief cap. |
| Calendar ICS source | One bounded HTTPS fetch per source refresh. No credentials, cookies, or redirect follow-up. | HTTPS-only source, timeout and size cap, redirect refusal, and host disclosure. File sources cause no network egress. |
| Calendar snapshot | Calendar screenshot to the vision route assigned to `calendar.snapshot_extract`. | Egress is resolved before upload. No assignment gives a named refusal. Confirmed events become a local source. |
| Failure-alert webhook | Queue statistics and failure-alert metadata, not transcript text. | Optional `intel_retry_failure_webhook_url`, bounded request, and external-egress receipt. |
| Wake-model download | Detection model bytes when wake word is enabled and models are absent. | Opt-in download. Detection runs locally after the model is cached. |
| Email channel | Frozen email body, sender, recipients, and provider request. | `channel.send`, provider host allow-list, native key custody, size and recipient limits, and terminal Receipt. |
| Slack channel | Frozen document text. Meeting forms omit transcript and audio. | Saved Slack destination, native key custody, host and size checks, channel operation, and Receipt. |
| Desk webhook | Proposed text as previewed to the configured endpoint. | Fixed destination, allowed-host policy, control mode, and Receipt. The URL is not returned in the proposal. |
| Desk GitHub issue or comment | Previewed issue or comment through the user's `gh` identity. | Registered repository or project effect policy, owner action, and Receipt. HoldSpeak cannot retract a posted comment. |
| Phone message | Message text and reply metadata to a paired Phone or configured Calls transport. | `phone.reach`, owner or agent principal, secret filter, length limit, pairing/line authentication, and a message event Receipt. A Program step has its own hourly limit. |
| Calls line / Phone call | The call reason, bounded context, and live call audio/text through the paired Phone or configured Calls Line. | Owner press, or a Program/step with `may_call` under non-Secure control; no transport, busy, quiet-hours, repeat, and secret checks refuse by name. Call events keep the terminal state and transcript reference. |
| Programs reaching the owner | A Program step can request a Phone message or call; the Program records remain local. | The Program and step control plus `phone.reach` decide the channel. Silence is never consent; an unallowed agent call waits in **Needs you**. |
| Connector CLI enrichment | Entity ids and provider query data to configured `gh`, `jira`, or `acli` tools. | Opt-in connector pack, read-only allow-list where defined, and provider credentials. |
| Mesh relay | Prompt and result between the hub and the named node. Provider keys do not cross. | Paired node bearer, pinned hub key, bound offer, and `holdspeak mesh serve`. |
| Web runtime response | Data requested by a browser or remote client. | Loopback default, web-token middleware for non-loopback HTTP, route rights, and the route's own WebSocket rules. |
| Device audio link | Audio frames in and device status out. | Paired-device PSK, same-LAN deployment expectation, and device route checks. |
| Browser mic capture | WAV to the hub's transcribe route. The local transcriber does not retain raw audio after the request. | Authenticated route, bounded body, and browser recovery copy deleted after confirmed transcription. |
| Paired dictation delivery | Final text and opaque delivery id to the named desktop. Raw audio does not cross. | Token gate, delivery claim, same-id replay, destination binding, and terminal Receipt. |
| Host notification and optional operations alerts | Notification body for this host, or configured failure-alert statistics to the webhook above. | Host notification is opt-in. The alert webhook is separately configured and does not carry transcript text. |

Meeting speech transcription and ordinary browser dictation use the local
Whisper backend. Model assignments route later summary, rewrite, intent,
plugin, or calendar-snapshot inference; they do not turn speech capture into a
remote transcription path. Check the assigned engine, egress chip, and Receipt.

## 5. Secrets

Do not put credentials in a Note, prompt, project context file, or test
fixture. Write model and connector keys through their owner-only settings.
Receipts store secret-safe destination identities and redacted previews.

Web authentication uses the configured owner token. Model keys stay in the
engine key store or owner-only local custody. People keys stay in native key
custody. A process that can already read the account can still read local
credentials; use OS isolation for that threat.

- Model keys are written through the owner-only Model Library secret route. A
  model resource reports presence, not the key. A deleted key writes a tombstone
  that suppresses a headless environment fallback for that engine.
- The device audio PSK is created for pairing and compared in constant time.
  An empty PSK refuses the device route.
- Slack, email, and other channel keys stay in native or owner-only key storage.
  A destination stores a key reference, not the secret.
- Web and model credentials are not copied into normal Desk records, general
  MCP resources, logs, or receipts.

## 6. Threat model

Controls cover accidental wrong-target effects, stale agent waits, duplicate
remote typing, missing model receipts, and disclosure of People private
records. They do not protect against:

- malware or a same-user process;
- a compromised model or connector provider;
- a user who exposes the hub token or database;
- a provider that retains data after HoldSpeak sends it;
- audio or text that the operating system never delivered;
- a remote bind that is exposed without a trusted network boundary.

## 7. Reporting

Report a security issue without including credentials, private transcripts, or
People content. Include the route, operation id, refusal or receipt state, and a
minimal reproduction that uses synthetic data.

## See also

- [People security boundary](PEOPLE_SECURITY.md)
- [Security model](SECURITY_MODEL.md)
- [Authority](AUTHORITY.md)
- [Models](MODELS.md)
- [Storage and migrations](STORAGE_AND_MIGRATIONS.md)
