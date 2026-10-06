# Security and privacy

This document states what data HoldSpeak holds, where it lives, what can leave
the machine, and which boundaries HoldSpeak enforces. If the code and this
document disagree, that is a bug in one of them. File it.

HoldSpeak is **local-first**. Nothing leaves your machine unless you choose a
feature that sends it. HoldSpeak has no telemetry, no crash reporting, and no
background beacons.

Related documents:

- [Authority](AUTHORITY.md): Control mode, grants, and receipts.
- [People security boundary](PEOPLE_SECURITY.md): the encrypted People store.
- [Gate](GATE.md): held Coder tool calls.
- [Security model](SECURITY_MODEL.md): the runtime controls behind this contract.
- [`trust-destinations.json`](trust-destinations.json): the machine-readable
  list of destinations. Setup, doctor, and the Web Desk render it.

## Control mode

The `control_mode` config key sets how actions that cause an effect are handled.
The modes are **Secure**, **Normal**, and **YOLO**. YOLO is the default.

Under YOLO, an action for a registered, configured destination runs when you
propose it. Every execution writes an immutable receipt. Under Normal and
Secure, an action needs a decision or an exact, bounded grant.

These limits hold in every mode:

- Encryption at rest and key custody for People.
- The People refusal rules (scoring, surveillance, employment inference).
- Egress badges and disclosure surfaces.
- The receipt and refusal ledger.
- Refusal to sync, export, or connect People content.

See [Authority](AUTHORITY.md) for the full mode table.

## Interview context and model work

Interview facts and suggestions belong to a saved Thread on the hub. A stated
fact includes a source quote. An inference carries an explicit inferred
classification.

A model turn can send permitted context to its assigned model endpoint. Check
the **Runs on** destination and the Receipt when the host matters.

Removing a fact also removes its dependent suggestions. It does not erase earlier
Thread messages, kept outputs, or backups. Use the retention controls for those
copies.

The People section of Interview opens the protected People surface. Enter
confidential relationship material there. See the [Interview guide](INTERVIEW.md).

## Kernel boundary: cooperating code, not a sandbox

HoldSpeak runs its effects through a kernel. The kernel admits one operation,
signs a warrant, lets one executor claim it, and records one immutable receipt.
Terminal text and keys enter through `process.input@1`. Connector subprocesses and
egress enter through their registered operations. Classified CLI reads need an
authenticated owner principal.

Desktop typing crosses a real process boundary. `TextTyper` is a proxy that sends
a warrant over an anonymous pipe. A spawned child checks the broker signature,
policy version, request shape, payload hash, expiry, one-use warrant ID, and
focused-window generation. Only then does the child load the keyboard and
clipboard driver. A focus refusal spends the warrant. A lost child is
`indeterminate`. HoldSpeak never retries it blindly.

**This is not a sandbox against arbitrary same-user Python.** The OS account can
launch processes and open sockets, and the native drivers are installed on disk.
Run untrusted plugins or agent-written Python only with OS-level isolation. See
the [kernel plan](internal/PLAN_KERNEL_OPERATION_BROKER.md#5b-effect-capability-confinement-the-enforcement-boundary).

A test fence counts every effect statement in the five census families. The
effect debt register, [`effect_ledger.json`](../holdspeak/kernel/effect_ledger.json),
now reads 0 total / 0 covered / 0 exempt / 0 debt. A new unclassified effect
statement fails the fence by name.

Approved work has a liveness bound. Work that is not claimed before its signed
claim deadline ends as `execution_claim_expired`. Claimed work with no receipt
before the execution deadline ends as `execution_liveness_expired` and
`indeterminate`. The web runtime reaps expired work at startup and every second.
Terminal receipts are immutable, so a late executor cannot change uncertainty
into success.

At the HTTP and WebSocket edge, credentials derive one of three principal kinds:
owner, agent, or node. Routing is deny by default.

- The owner approves or rejects.
- An agent proposes allowed work and reads only its own scope. An agent never has
  `decide`, posture, delegation, or owner rights.
- A node claims executor work.

Scheduled work uses an internal `scheduler` principal. No credential or code path
upgrades it to owner.

## Inference authority and schedules

Every physical model attempt takes one path. `InferenceRunner` admits and claims
one `inference.invoke@1` child, binds one deployment revision, and lets one
reviewed adapter dispatch. A retry or fallback is a new child with a new receipt.
Cancellation rejects a late publication. Work that cannot be proved complete is
`indeterminate`. See [Architecture](ARCHITECTURE.md#inference-admission-one-path-one-receipt-per-attempt).

One finite parent run covers each live meeting, dictation, or wake session
(`meeting.session@1`, `dictation.session@1`, `wake.session@1`). Each model or
Whisper call is still a child that rechecks liveness, revocation, deadline, budget,
and revision.

Generic inference receipts hold references and hashes, not model bodies. This is
not a content-free promise for all kernel storage. A parent run keeps its input
snapshot, which can contain request content. The generic filter rejects named
audio, PCM, and token keys. It does not classify every string. See
[Security model](SECURITY_MODEL.md#data-handling-and-egress).

### Scheduled Workbench runs

A scheduled Workbench run has narrower authority than a manual run. When you
enable the schedule, HoldSpeak writes one live row in `kernel_schedule_delegations`.
The row binds:

- the owner delegator
- the Workbench ID and revision, and the schedule revision
- the Agent (`recipe`) ID and revision
- the exact cadence
- the deployment revision and terms digest
- an optional expiry

The due tick acts as `scheduler`. Admission re-checks these terms in the same
write transaction that claims the due minute. A missing, revoked, expired,
disabled, changed, or duplicate attempt is refused before dispatch with one of
`delegation_missing`, `delegation_revoked`, `delegation_expired`,
`schedule_disabled`, `delegation_stale_work`, `delegation_target_changed`, or
`duplicate_tick`. Each refusal leaves a receipt.
An edit, a disable, or drift also advances the publication fence, so a running
child cannot publish under old terms.

### Scheduled recording

Enabling a recording schedule approves its exact terms: time, cadence, and
duration. Editing the cron expression, duration, or timezone writes a new
delegation receipt. The due tick fires as `scheduler` and writes a receipt for
each fire.

A visible countdown on the capture hero names the schedule and the seconds left.
You can cancel during the countdown. Every failure leaves a receipt:

- `mic_floor_held`: another holder has the microphone. The receipt names it.
- `missed`: the hub was down. HoldSpeak writes one receipt per missed window.
- `missed_interrupted_arming`: the countdown was interrupted.

Capture uses the normal meeting start path. Audio stays local.

## 1. Data classes

| Data | Where it lives | Sensitivity | Notes |
|---|---|---|---|
| Meeting transcripts | `~/.local/share/holdspeak/holdspeak.db` (`segments`, `segments_fts`) | High | Speech text, speaker labels, timestamps. |
| Speaker voice embeddings | same database, `speakers.embedding` | High | A voiceprint, not raw audio. Used to recognize speakers across meetings. |
| Meeting intelligence | same database (`intel_snapshots`, `topics`, `action_items`, `artifacts`) | Medium-high | Model-derived topics, actions, summaries, and plugin artifacts. |
| Activity ledger | same database (`activity_records`, `activity_annotations`, `activity_meeting_candidates`) | Medium | URLs, titles, and entity IDs from browser history. |
| Raw meeting audio (iPad app) | Apple Documents, `meeting-audio/<meeting-id>.wav` | High | The app checkpoints the take on the device and finalizes a WAV. Recovery files are removed after finalization. |
| Config | `~/.config/holdspeak/config.json` | Medium | Holds the device PSK and web auth token. Destination secrets are kept apart in owner-only local custody. |
| Web recovery drafts | Browser `localStorage`, `hs.draft.v1.*` | High | Editable drafts. Cleared after the action that keeps them. |
| Web pending voice capture | Browser IndexedDB, `holdspeak-voice-recovery` | High | One bounded WAV per scope, kept only while transcription has not confirmed text. A successful transcription deletes it. |
| Native dictation recovery | Apple `UserDefaults` and Application Support | High | The draft, destination, and delivery ID, or bounded PCM. Cleared after delivery or transcription succeeds. |
| First-value mechanics | same database (`first_value_attempts`, `first_value_events`) | Low | Event names, IDs, timing, counts, and failure category. No phrase, transcript, or audio column. |
| Paired-delivery receipts | same database (`remote_dictation_deliveries`) | High | Delivery ID, request hash, lifecycle, and the terminal Receipt. A success Receipt can hold the final text so a reconnect returns it without typing twice. |

All state sits under your home directory with normal file permissions.

## 2. Storage and at-rest posture

- The database (`~/.local/share/holdspeak/holdspeak.db`) and the config
  (`~/.config/holdspeak/config.json`) are **plaintext on disk**. File permissions
  protect them.
- The database runs in WAL mode. Recent writes live in `holdspeak.db-wal` and
  `holdspeak.db-shm` while a hub is open. Do not put the data directory in a
  synced folder. Back up with `holdspeak backup`. Do not copy the file.
- Browser-history reads use temporary copies of the browser files. HoldSpeak
  deletes the copies after import and never modifies the originals.
- Activity retention applies at import time (default 30 days). Per-domain
  exclusion rules apply.

### Encryption at rest

The normal data plane stays plaintext. People records use a separate encrypted
store.

Full-disk encryption (FileVault on macOS, LUKS on Linux) is the practical
protection for a single-user local machine. It covers every file. HoldSpeak does
not manage a key for the whole database. **Turn on full-disk encryption.** Without
it, file-level access to a compromised machine exposes transcripts, voice
embeddings, and the activity ledger.

People content is different. HoldSpeak encrypts it with AES-256-GCM before it
reaches SQLite. The key sits in macOS Keychain or Linux Secret Service. There is
no file, config, or environment fallback. If the credential store is missing,
locked, or does not match, People fails closed. People content stays out of the
normal database, backups, search, Ask, Memory, sync, exports, connectors, Cadence,
generic MCP surfaces, and logs. See [People security boundary](PEOPLE_SECURITY.md).

A new class of third-party confidential data must use an equally reviewed
encrypted boundary or stay unsupported. It must not reuse the plaintext plane.

### The People resolver

Meeting intelligence can match owner names and speaker labels to People
relationships. The resolver (`people_service.resolve_relationship_by_watch_identity`)
runs inside the encrypted store, in memory, at read time. Only an opaque
relationship ID reaches the Watch projection.

A match is never a guess. Two relationships with the same display name, or an owner
string that fits two first names, resolve to nobody. HoldSpeak reports them as
ambiguous with their candidates. Only your own alias link settles the match
(`people_service.resolve_owner_candidates`).

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
by the deployment revision. The footer egress chip shows that host. The
deterministic fallback has no egress.

### The remote boundary

The Streamable HTTP listener (`POST /api/mcp`) is off by default for remote
callers. The `bind_host` setting is only stored. No listener or peer-address check uses it,
so it is not a network fence. A request from a non-loopback address never gets the
`OWNER` principal: the owner web token from a remote address returns 403.
HoldSpeak never reads `X-Forwarded-For` to derive a principal.

A loopback request with the owner token is local transport, not remote access. It
works whether or not the remote flag is on. The stdio MCP sidecar uses this path.

The sidecar never opens the database. It finds the running hub through the owner
lock beside the database file. It forwards each JSON-RPC message to the hub at
loopback `POST /api/mcp` with the owner token. The hub is the only writer. With no
hub running, the sidecar refuses by name. It ignores `HOLDSPEAK_MCP_STANDALONE`.
See [MCP sidecar](MCP_SIDECAR.md).

Scoped credentials carry a palette (the tool families the caller may use) and a
TTL capped at 30 days. The hub keeps `sha256(token)` and compares in constant
time. The plaintext shows once, at issue. A hub restart clears all credentials.
Each remote tool call writes a kernel-journal receipt with `origin: remote`, the
caller label, and the caller's tailnet IP. There is no relay. Machines talk
directly on the tailnet.

### Connector boundaries

- **Confluence.** The connector runs the `acli` CLI with a read-only allowlist
  (`auth status`, `auth switch`, `space list`, `space view`, `page view`,
  `blog list`, `blog view`). HoldSpeak makes no Confluence REST call. The CLI holds
  the credentials.
- **Calendar.** The only egress is the ICS fetch for HTTPS sources
  (`calendar_ingest_conductor.py`). The Settings row egress chip names the host.
  HoldSpeak stores no calendar credential and runs no OAuth flow. File sources
  cause no network egress. Arming a recording is your standing consent for a Room
  or for all calendar meetings. Armed never means started. The meeting watch reads
  the local database only and calls no model.

## 3. Trust boundaries

1. **The local process.** Fully trusted. It runs as you.
2. **The web runtime** (`web_server.py`). It binds `127.0.0.1` by default. On a
   non-loopback host, an auth token is required to bind and on every request. The
   exceptions are `/health`, the device audio WebSocket, and `/_built` assets.
3. **The device link** (`/api/devices/audio`). Devices such as AIPI-Lite
   authenticate with a pre-shared key (PSK), compared in constant time
   (`device_audio.verify_psk`). Reach is same-LAN.
4. **The audio floor** (`/api/dictation/floor`, `/claim`, `/release`). The browser
   open mic claims the same one-at-a-time arbiter as the hotkey, the meeting
   recorder, and the wake listener. The claim is leased for 20 seconds
   (`DEFAULT_LEASE_SECONDS`) and renewed at half that time. A closed tab stops
   renewing, and the floor frees itself. A refused claim answers 409 and names the
   active owner. The routes are local-only and carry no audio.
5. **Connector packs.** Code in `~/.holdspeak/connector_packs/` runs in-process
   with your permissions. The manifest permission check
   (`connector_runtime.py`) is an honesty mechanism, **not a sandbox**. A
   malicious pack can call `subprocess.run`. Install only packs you trust.
6. **Session steering** (`coder_steering.py`). Typing into a live Coder tmux pane
   is a this-device act. Nothing leaves the machine. Consent controls it, not an
   egress row. Watching is free: the peek is read-only and never sends a key.
7. **Rails as material** (`grounding_rails.py`, `rails_observer.py`). Grounding a
   run on an open phase or story reads the exact file your own `dw` command names,
   as opaque text. Nothing leaves the machine. The ambient observer is off by
   default and read-only. It writes one local journal note per batch. It never
   writes to the rails. A remote node sends rail events only, with no repo file
   bodies, each stamped with its origin node.
8. **The tool-call gate.** See below and [Gate](GATE.md).

### Session steering rules

- **Secure and Normal** need an arming grant. You issue it per session from the
  Desk. The TTL is 5 minutes in Secure and 15 minutes in Normal. The hard cap is
  60 minutes. The grant is pinned to the pane's tmux `%N` identity and held only
  in memory. A hub restart disarms everything.
- **YOLO** needs no arm grant for text and allowed-key delivery to a registered
  session or an exact `pane:%N`.
- The pane ID from the peek travels with the delivery request. One hub-side
  chokepoint re-resolves the registry target before every send. It refuses a
  missing, recycled, or retargeted pane and sends only to the verified `%N`.
- A mode change invalidates old grants. Every delivery and refusal is audited with
  its policy snapshot and shows as a source-linked Desk Receipt.
- **Any key.** Control and named keys (`C-c`, `Escape`, arrows) go through
  `coder_steering.deliver_keys`. A key must be on the allow-list or HoldSpeak
  refuses it by name before it reaches `tmux`.
- **Any pane.** A `pane:%N` key steers a raw tmux pane you started by hand, with
  the same pin and re-check.
- **Any configured machine.** `coder_steering_relay` forwards a command to a node
  named in `HOLDSPEAK_STEER_NODES`. The machine that types resolves the policy or
  grant and writes the audit. The hub only relays. Only the command, the expected
  pane identity, and the node's own bearer token cross the wire. A node that does
  not answer refuses with `node_offline`.
- **The session factory** (`coder_factory.py`) holds `spawn`, `rename`, and
  `kill`. A session name must pass a strict allow-list: it starts with a letter,
  digit, or underscore, so it is never read as a flag. HoldSpeak passes it as its
  own argument, never as a shell string. `kill` keeps a separate arm grant. It
  re-checks the pinned pane, drops the grant, and audits.

### Tool-call gate rules

A Claude Code session that you opted in can hold a matched tool call for a Desk
decision.

- **One chokepoint.** Every state change passes through one transition method in
  `db/gate.py`. The first write wins. A losing race gets a typed 409 that names
  the standing decision. A census test (`tests/unit/test_gate_chokepoint.py`)
  fails on a second path.
- **The record is not authority.** Only the live hook that waits for the decision
  can let the call proceed.
- **Fail closed.** When armed, any error is a deny with a named reason. There is
  no allow-on-error and no timeout auto-allow. When not armed, the hook is inert.
- **Restart invalidation.** Hub startup flips every held proposal to
  `invalidated`.
- **Bounded preview.** The hook sends a SHA-256 and the first 120 characters of the
  arguments. This truncates. It does not remove secrets.
- **No config edits.** `holdspeak gate install` prints the hook block. You add it
  to `~/.claude/settings.json`.
- **Token totals.** The Stop-hook leg reports token counts and the model name to
  the loopback hub. No message text leaves the hook process.

## 4. Egress points: everywhere data can leave the machine

[`trust-destinations.json`](trust-destinations.json) is the machine-readable
source for destination names, boundaries, data classes, authority, and revoke
actions. This table adds implementation detail. It is not a second inventory.

| Egress | Trigger | What leaves | Control |
|---|---|---|---|
| **Remote model endpoint** (`kernel/inference_runner.py`) | An admitted attempt whose frozen **Runs on** revision names an off-machine OpenAI-compatible endpoint | The model input for that attempt and request metadata. Never raw audio or embeddings. | You author and assign the destination. Each attempt has its own child and receipt. Local destinations never cross. A fallback is a separate frozen attempt. |
| **Calendar ICS sources** (`calendar_ingest_conductor.py`) | You add an ICS source (file path or HTTPS URL) in **Settings**. Each source refreshes at boot and every 15 minutes. | One bounded fetch per HTTPS source per refresh. No credentials, headers, cookies, or redirect follow-up. 10 s timeout, 5 MiB cap. | HTTPS only. Redirects are refused. The egress chip names the host. File sources cause no egress. |
| **Calendar snapshot** (`services/calendar_snapshot_service.py`) | You import a calendar screenshot with **Snapshot** or a Desk drop | The image goes to the vision model assigned to `calendar.snapshot_extract`. A local model means nothing leaves. | No vision assignment gives a named refusal. The generated `.ics` is a local source with the same parser limits. |
| **Failure webhook** (`intel_queue.py`) | You set `intel_retry_failure_webhook_url` | Queue statistics only. No transcript. | Opt-in. |
| **Wake-model download** (`wake_word.py`) | `wake_word.enabled` turns on with the models absent | Nothing leaves. HoldSpeak fetches the detection models (about 7 MB) once and caches them. | Opt-in. Detection runs locally. |
| **Send to Slack** (`services/channel_slack.py`) | You press `channel.send` for a saved Slack destination | The frozen document as Slack text. Meeting forms omit the transcript and audio. | The kernel admits an `external.egress` child to `hooks.slack.com:443`. Redirects are refused. Text over 39,000 characters is refused. No automatic repost follows an uncertain result. The webhook URL stays in the native keyring. |
| **Desk Slack relay** (`web/routes/desk_actuators.py`) | None | Nothing | Refuses with `slack_moved_to_channel`. Old proposals and receipts stay readable. |
| **Desk webhook** (`web/routes/desk_actuators.py`) | `meeting.companion_webhook_url` is set | The proposed text, as previewed, to that one endpoint | The URL is the consent for its host. YOLO runs it on propose. Normal and Secure need an authorization or grant. Every run writes a receipt. The URL is a credential and never appears in proposals, broadcasts, or API responses. |
| **Desk GitHub issue** (`web/routes/desk_actuators.py`) | The GitHub connector is on | The issue title and body, as previewed, through your own `gh` | HoldSpeak uses your `gh` login and stores no token. An unregistered repo is refused even in YOLO. |
| **Connector CLI enrichment** (`gh`, `jira`) | You enable the connector pack | Entity IDs (PR, issue, ticket numbers) to your own CLI tools | Opt-in. Manifest permissions `shell:exec` and `network:outbound`. |
| **Mission-control receipts** (`missioncontrol_bridge.py`) | A rails repo is in your project map (`~/.holdspeak/delivery_workbench.json`) and the conveyor is open | Nothing composed. A read of that repo's open pull requests through your `gh`. | You author the map. The routes are GET-only. A `gh` failure shows as a typed absence. |
| **PR receipts** (`delivery/pr_receipts.py`) | You click **Refresh**, or you set `pr_refresh_seconds` on a source | Nothing composed. One batched read of that repo's pull requests through your `gh`. | Manual by default. The cadence is per source and set by hand. A failure shows as a stale row. |
| **Mesh relay** (`intel/mesh_relay.py`) | An admitted run against a **Runs on** destination of kind `meshNode` | The prompt and result between the hub and the machine you named. No provider key crosses. | You pair the node. A per-node bearer authenticates it. The pinned hub Ed25519 key verifies each bound offer. The hub private key never leaves the hub. `holdspeak mesh serve` is the live consent. |
| **Web runtime responses** | A client asks for data | What the API returns | Loopback by default. Token-gated off loopback. |
| **Device audio link** | A paired device streams audio | Audio in. Status text out. | PSK. Same LAN. |
| **Browser mic capture** (`POST /api/dictation/transcribe`) | You hold the mic or TALK in the browser, or open-mic detects an utterance | Nothing leaves. The WAV goes to your own hub, local Whisper transcribes it, and HoldSpeak does not keep the audio (16 MB cap). | Off loopback, the hub is token-gated. Open-mic posts one WAV per utterance. The browser detects speech with energy and no model. |
| **Paired dictation delivery** (`POST /api/dictation/remote`) | You release the native dictation control or TALK, or send a draft | Final text and an opaque delivery ID to the named desktop. Raw audio never crosses. | Direct LAN or Tailscale peer, token-gated off loopback. The hub claims the ID first and caches the Receipt. A repeat returns the Receipt. A different payload under the same ID is refused. |

Notifications (`desktop_notify.py`) stay on this machine. macOS uses `osascript`.
Linux uses libnotify. By default the body holds only the needs-you count. Room
names appear only if you turn on the content setting. Quiet hours (default 22:00
to 08:00) suppress notifications. There is no remote push.

Browser-history reads make no network call. The activity ledger leaves the machine
only through the connector CLIs above, as entity IDs.

## 5. Secrets

- **Model API key.** Write it through the owner secret subresource of the Model
  Library for that model. It never appears in general model resources, sync, the
  database, read responses, logs, or receipts. The hub keeps it in owner-only
  (`0600`) local custody. Reads report presence only. `HOLDSPEAK_PROFILE_<ID>_KEY`
  is a headless fallback. Deleting the key in the UI writes a tombstone that
  suppresses the fallback. One model never uses another model's key. See
  [Models](MODELS.md).
- **Device PSK.** Created on first use and stored in `config.json`
  (`device_audio.ensure_device_psk`). Constant-time comparison. An empty PSK fails
  closed.
- **Web auth token.** Created on first use and stored in `config.json`
  (`web_auth.ensure_web_token`). Constant-time comparison. Never logged.
- **Slack webhook URL.** The `channel.save_slack_webhook` operation keeps the
  secret out of its recorded arguments. It saves the URL in the native keyring
  under `slack:<key_ref>`. A destination stores only the key reference and the
  channel label.
- **Firmware secrets** (AIPI-Lite). They live in gitignored `bridge.env` and
  `secrets.yaml`. The repo holds `.example` templates.

## 6. Threat model

In scope:

- Accidental transcript egress to a cloud model. Control: local default, fail
  closed.
- Open exposure when bound off loopback. Control: bind guard and token gate.
- Forged device audio. Control: PSK and LAN source-IP allowlist.

Out of scope:

- A compromised local account, or file access without full-disk encryption (see
  section 2).
- A malicious connector pack that you install (section 3).
- Network confidentiality for cross-network device or web reach. TLS, tunnels, and
  per-device PSKs are future work.

## 7. Reporting

HoldSpeak is a personal, local-first project. To report a finding, open an issue
that names the data class, the trust boundary, and the egress point.

## See also

- [Models](MODELS.md): pointing at a cloud endpoint is the one deliberate egress
  choice.
- [Getting Started](GETTING_STARTED.md): the local-by-default setup.
