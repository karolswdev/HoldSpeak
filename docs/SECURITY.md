# HoldSpeak Security & Privacy Posture

**Status:** living document.
**Last updated:** 2026-08-15 (one inference admission path, per-attempt
receipts, bounded schedule delegation, and per-session speech/meeting authority).

This document is the threat model for HoldSpeak: what data it holds, where that
data lives, what can leave the machine, and the decisions behind its at-rest
posture. If code and this document disagree, that is a bug in one of them;
file it.

## Kernel boundary: cooperating code, not a sandbox

Every known HoldSpeak route in the five ratified effect-census families now
has an enforcement or exemption proof. Terminal text and keys enter through
`process.input@1`; consequential connector subprocesses and egress enter
through their registered operations; classified CLI reads require an
authenticated owner principal; and the raw desktop driver is no longer
imported by the ordinary typing runtime.

Desktop typing now has a real process boundary, not only a routing
convention. The ordinary `TextTyper` is a warrant-only proxy over an
anonymous pipe. A small spawned child independently validates the broker
signature, current policy version, exact request shape, operation and target,
payload hash, placement, claim and execution expiry, one-use warrant ID, and
focused-window generation. Only after those checks does it import the
keyboard/clipboard driver. A focus refusal spends the warrant; a lost or
timed-out child is indeterminate and is never blindly retried.

**This is still not a general-purpose sandbox against arbitrary same-user
Python.** The OS account can launch processes and open sockets, and the Python
source containing native drivers is installed on disk. Untrusted plugins or
agent-authored Python therefore still require the process/OS isolation
threshold in
[RFC §5b](internal/PLAN_KERNEL_OPERATION_BROKER.md#5b-effect-capability-confinement-the-enforcement-boundary)
before they may execute. The stronger, precise claim today is that the
production desktop effect path crosses an independently validating process
boundary, while the kernel and census enforce HoldSpeak's own cooperating
routes.

The checked-in [effect debt register](../holdspeak/kernel/effect_ledger.json)
contains only transitional debt and is now **0 total / 0 covered / 0 exempt /
0 debt**. The fence separately pins all 21 formerly active migrated,
read-classified, exempt-computation, proxy, and confined statements, and a new
unclassified effect statement fails by name. From the corrected initial
baseline, the audited migration delta is **38 debt → 0 debt**. Article XI's
transitional clause 6 and the register expired together under their
owner-ratified sunset; the zero-row file remains as a machine-readable tombstone
and regression tripwire.

Approved work also has a generic liveness bound. Work not claimed before its
signed claim deadline terminalizes as `execution_claim_expired`; claimed work
whose executor never receipts before the signed execution deadline terminalizes
as `execution_liveness_expired` and `indeterminate`. The web runtime reaps on
startup and once per second. Terminal receipts are immutable, so a late executor
cannot rewrite uncertainty into success.

At the HTTP and WebSocket edge, credentials derive one of three authenticated
principal kinds: owner, agent, or node. Routing is deny by default. The owner
may approve or reject; an agent may propose allowed work and read only its
scope; a node may claim executor work. Agent rights never include `decide`,
posture changes, delegation, or ownership. Scheduled execution uses a fourth,
internal-only `scheduler` principal; no credential or code path upgrades it to
owner.

## Inference authority and bounded schedules

Every physical model attempt follows the canonical
[one-path inference contract](ARCHITECTURE.md#inference-admission-one-path-one-receipt-per-attempt):
`InferenceRunner` admits and claims one `inference.invoke@1` child, binds one
immutable deployment revision and authority basis, then permits one reviewed
adapter to dispatch. The terminal receipt is immutable. A parent run/session
cannot hide child calls in its own receipt, retry/fallback gets a distinct child
per physical attempt, cancellation rejects late publication, and execution that
cannot be proved complete is `indeterminate`, never guessed successful.

Scheduled Workbench work has narrower authority than a manual owner run.
Deliberately enabling the schedule mints one live row in
`kernel_schedule_delegations` that binds:

- owner delegator kind and identity;
- Workbench id/revision and schedule revision;
- Agent (`recipe`) id/revision;
- exact cadence;
- exact deployment revision and terms digest; and
- optional expiry.

The due tick acts as the `scheduler` principal. Admission re-derives those terms
inside the same write transaction that claims the due minute and persists the
parent. Missing, revoked, expired, disabled, cadence-changed, stale-work,
target-changed, or duplicate attempts refuse as `delegation_missing`,
`delegation_revoked`, `delegation_expired`, `schedule_disabled`,
`delegation_cadence_changed`, `delegation_stale_work`,
`delegation_target_changed`, or `duplicate_tick` before provider dispatch. Each
leaves a terminal refusal receipt with delegation provenance when available.
Edits, disable, sync changes, Agent drift, and target drift also advance the
publication fence so an already-running child cannot publish under old terms.

Scheduled recording follows the same bounded-delegation model. Enabling a
schedule records approval for its exact terms: time, cadence, and duration. A
terms edit (cron expression, duration, or timezone) writes a new delegation
receipt, re-approving the changed terms. The due tick fires as the `scheduler`
principal (the same internal-only principal as Workbench schedules), kernel-
admitted with a receipt per fire. The arming countdown (Article IV.3, mic owner
visible) is the fire's observable surface: a visible countdown on the capture
hero names the schedule and the seconds remaining. Cancellation during the
countdown is honored; a cancel after the countdown has elapsed is not.

Honest failure receipts cover every non-success path (Article VI.1): a held
microphone floor produces a `mic_floor_held` refusal naming the current holder;
a hub that was down at fire time produces a `missed` receipt on restart, bounded
to one receipt per missed window regardless of downtime length; an interrupted
arming resolves as `missed_interrupted_arming`. No fire path produces a silent
skip. Capture itself is the existing `_start_meeting` path with no new egress
point (Article III.1): audio stays local.

One finite parent represents meeting, dictation, or configured-wake authority
per live session (`meeting.session@1`, `dictation.session@1`, or
`wake.session@1`), but every actual LLM or local Whisper call remains an
invocation child that rechecks liveness,
revocation, deadline, budget, and exact revision. Pre-session Whisper preload
requires narrow authority for the exact model-config revision; it is not a silent
warmup exception. Prompts, transcripts, dictated text, audio, completions,
credentials, and token streams stay out of kernel operation, journal, and receipt
fields.

HoldSpeak is **local-first**. The design goal is that nothing leaves your
machine unless you explicitly choose a feature that sends it. The sections below
make that promise auditable rather than aspirational.

---

## 1. Data classes

| Data | Where it lives | Sensitivity | Notes |
|---|---|---|---|
| **Meeting transcripts / segments** | `~/.local/share/holdspeak/holdspeak.db` (SQLite; `segments`, `segments_fts`) | High | Verbatim speech text + speaker labels + timestamps. |
| **Speaker voice embeddings** | same DB, `speakers.embedding` (256-dim float32 BLOB) | High (biometric-adjacent) | Used for cross-meeting diarization. A voiceprint, not raw audio. |
| **Meeting intelligence** | same DB (`intel_snapshots`, `topics`, `action_items`, `artifacts`) | Medium-High | LLM-derived topics/actions/summaries + plugin artifacts. |
| **Activity ledger** | same DB (`activity_records`, `activity_annotations`, `activity_meeting_candidates`) | Medium | Browser-history-derived URLs/titles/entity IDs (GitHub/Jira/etc.). |
| **Raw meeting audio** | Apple Documents, `meeting-audio/<meeting-id>.wav`, plus a PCM journal while capture is recoverable | High | The flagship app checkpoints the take on device and finalizes it to a replayable WAV. Recovery manifests and partial PCM are removed after successful finalization; the WAV remains until its app data is removed. |
| **Config** | `~/.config/holdspeak/config.json` | Medium | Includes the **device PSK** and **web auth token** (secrets); the cloud API key is referenced by *env-var name*, not stored. |
| **Web recovery drafts** | Browser `localStorage`, under versioned `hs.draft.v1.*` keys | High | Editable First Words, Dictation, Ask, Agent, capability, Coder session reply, and steering drafts. Written synchronously in this browser's storage; cleared after a confirmed retaining action where the surface has one. |
| **Web pending voice capture** | Browser IndexedDB, `holdspeak-voice-recovery` | High | One bounded WAV per voice-to-fill scope, retained only when transcription has not confirmed text. A retry reuses this local audio; successful transcription deletes it. No capture enters first-value measurement. Open-mic segments do not use this store: they are held in memory, posted, and dropped. |
| **Native paired-dictation recovery draft** | Apple `UserDefaults`, `hs.dictate.recovery.v1` | High | The editable words, named destination, raw/processed flag, and opaque delivery id. Cleared only after the desktop confirms delivery. |
| **Native pending voice capture** | Apple Application Support, `HoldSpeak/dictation-recovery.pcm16` | High | Bounded 16 kHz mono PCM retained when on-device transcription fails or the app relaunches before text exists; deleted after transcription succeeds. |
| **First-value mechanics** | same DB (`first_value_attempts`, `first_value_events`) | Low | Bounded event names, ids, destination class, timing, counts, and failure category. The schema has no phrase, transcript, content, or audio column. |
| **Paired-delivery receipts** | same DB (`remote_dictation_deliveries`) | High | Opaque delivery id, request hash, lifecycle, and terminal HTTP Receipt. A successful Receipt may contain the processed final text so reconnect can return the exact prior result without typing again. |

All persistent state is under the user's home directory and protected by normal
filesystem permissions. There is **no telemetry, crash reporting, or background
beaconing** anywhere in the codebase.

---

## 2. Storage & at-rest posture

- The database (`holdspeak/db/`; `DEFAULT_DB_PATH = ~/.local/share/holdspeak/holdspeak.db` in `db/core.py`)
  and the config (`~/.config/holdspeak/config.json`) are **plaintext on disk**,
  protected by filesystem permissions only.
- Browser-history reads operate on **temporary snapshot copies** of the
  browser's SQLite files (`activity_history.py`) and are cleaned up after import;
  the original browser databases are never modified.
- Activity retention is enforced at import time (default 30 days) and per-domain
  exclusion rules are honored.

### Encryption-at-rest decision

**Decision: the normal HoldSpeak data plane remains plaintext; confidential People
records use a separate encrypted data plane.**

Rationale:
- HoldSpeak is single-user and local. The realistic protection for at-rest data
  on a personal machine is **full-disk encryption** (FileVault on macOS, LUKS on
  Linux), which covers every file uniformly (including the DB, config, and any
  temp snapshots) without HoldSpeak holding a key it cannot safely manage.
- Whole-application encryption would require a larger key-management and migration
  story (including headless installs) that, done poorly, adds risk without adding
  protection. HoldSpeak therefore does not imply that local-only normal data is
  encrypted.

The People capability is the narrow exception triggered by third-party relationship
material. Its records are written to a dedicated sidecar only after sensitive JSON
payloads are encrypted with AES-256-GCM. The random data-encryption key is retrieved
from an allow-listed native OS credential store (macOS Keychain or Linux Secret
Service); there is no production plaintext, file, config, or environment fallback.
If that credential store is absent, locked, or mismatched, People fails closed.
People content is excluded from the normal database, its safety backups, global
FTS/Search/Ask/Memory, sync, exports/connectors, Cadence, generic MCP surfaces, and
content-bearing logs. A default-off People MCP adapter can disclose relationship
metadata and `shared_intent` records over stdio only after the owner explicitly
starts the sidecar with read or write capability; leader-private content is always
excluded. See [People security boundary](PEOPLE_SECURITY.md).

**Residual risk:** if the machine is compromised at the file level and full-disk
encryption is off, transcripts, voice embeddings, and the activity ledger are
readable. We accept this for the local-first, single-user model and **recommend
users enable full-disk encryption**.

**Revisit trigger:** whole-application encryption remains warranted if HoldSpeak
gains multi-user installs or a shared/server deployment. New classes of third-party
confidential data must either enter an equivalently reviewed encrypted boundary or
remain unsupported; they must not silently reuse the plaintext plane.

---

## 3. Trust boundaries

1. **The local process**: fully trusted; runs as the user.
2. **The web runtime** (`web_server.py`): binds `127.0.0.1` by default (open,
   the long-standing "localhost is trusted" model). When bound to a non-loopback
   host it is gated by an auth token: required to bind and on every
   request, except `/health`, the device-audio WS, and `/_built` static assets.
3. **The device link** (`/api/devices/audio`): AIPI-Lite and compatible clients
   authenticate with a pre-shared key (PSK) compared in constant time
   (`device_audio.verify_psk`). Same-LAN scope today; cross-network reach is planned.
4. **The audio floor** (`/api/dictation/floor{,/claim,/release}` →
   `VoiceTypingSession`): the browser's open mic captures on the same physical
   machine as the hotkey, the meeting recorder, and the wake listener, so it
   claims the same one-at-a-time arbiter rather than listening behind it. The
   claim is **leased** (20 s, heartbeated at half): a tab that dies stops
   renewing and the floor frees itself, so a closed browser can never wedge the
   owner's hotkey. A refused claim answers 409 with the active owner named. The
   routes are local-only and carry no audio.
5. **Connector packs**: user-supplied code under `~/.holdspeak/connector_packs/`
   runs **in-process with the user's permissions**. The manifest permission gate
   (`connector_runtime.py`) is an *honesty* mechanism, **not a security sandbox**:
   a malicious pack can call `subprocess.run` directly. Only install packs you
   trust.
6. **Session steering** (`coder_steering.py` → a this-device tmux pane): typing into
   a live Coder session is a this-device consequential act (nothing leaves the
   machine), gated by a consent model rather than an egress row. Watching is
   free: the pull-out's peek is read-only, hash-gated, never a keystroke.
   Secure and Normal steering require an **arming grant**: issued per session
   by an explicit Desk act, TTL'd by Control mode (5 min Secure, 15 min Normal;
   60 min hard cap), pinned to the pane's unique tmux `%N` identity, and held
   **in memory only**, so a hub restart disarms everything. YOLO does not ask
   for that arm grant for text and allowed-key delivery to a registered session
   or exact `pane:%N`. The pane id captured by peek rides the delivery request;
   the chokepoint re-resolves the registry target immediately before every send
   and refuses a missing, recycled, or retargeted pane. It sends only to the
   verified canonical `%N`. Mode changes invalidate old grants. Enforcement
   lives in one hub-side chokepoint, not in either client. Every delivery and
   refusal is audited with its operation-policy snapshot and projects as a
   source-linked Desk Receipt.

   **Full manipulation** widens the reach without loosening the invariants.
   (a) *Any key*, not just text: control and named keys (`C-c`, `Escape`,
   arrows) go through a second chokepoint, `coder_steering.deliver_keys`, with
   the same authority and identity check plus audit; a named key must be on an
   allow-list or it is refused by name and never handed to `tmux`, so an
   arbitrary string can never become a keystroke. (b) *Any pane*, not just
   registered sessions: a
   `pane:%N` key steers a raw tmux pane (one you started by hand), pinned and
   re-verified exactly like a tracked session; watching any pane is free, and
   Secure/Normal manipulation is armed while eligible YOLO steering uses the
   exact pane as posture authority. (c) *Any configured machine*:
   `coder_steering_relay` forwards a command to a node named in
   `HOLDSPEAK_STEER_NODES`, which executes it against its own tmux.
   **The machine that types resolves the policy or grant and writes the audit**;
   the hub is a relay, never the authority over another machine's terminal, and
   only the command (text/keys), expected pane identity, and the node's own
   bearer token cross the wire. A node that does not answer refuses by name
   (`node_offline`), never a hang. Both chokepoints are pinned by a census test;
   YOLO still exposes only the registered text/allowed-key capability, not an
   arbitrary remote executable operation.

   **The session factory** (`coder_factory.py`) adds the lifecycle on the same
   terms. `spawn` and `rename` take a session name, which is user input, so the
   name is held to a strict allow-list (first character alphanumeric or underscore,
   so it can never be read as a flag) and passed as its own argument, never a
   shell string; a bad name refuses by name before tmux runs. `kill` is the most
   consequential act, so it retains a separate arm grant: it re-verifies the
   pinned pane, drops the grant afterward, and audits.
   The destructive tmux verbs live in that one module, pinned by a census, and
   every lifecycle act is audited with a plain heading.
6. **Rails as material** (`grounding_rails.py`, `rails_observer.py`):
   grounding a run on an open phase or story reads the exact file your own
   `dw` command line names, as opaque text; it never re-derives rail state
   from a markdown body, and nothing leaves the machine. The ambient
   observer is off by default and read-only: it watches your `dw` event
   stream and writes one local journal note per batch, summarized by a
   RuntimeProfile model you chose. It never writes to the rails; a suggested
   action is the existing story-flip proposal, human-approved, the commit
   gate keeping the final say. A remote node's rail events reach the journal
   only as events (no repo file bodies cross the wire), each stamped with
   its origin node, and a node gone quiet reads stale rather than fabricated.
7. **The tool-call gate** (`coder_gate.py`, `db/gate.py`,
   `web/routes/system/gate_routes.py`): a Claude Code session you opted in
   can hold a matched tool call for a desk decision. The boundary rules
   mirror the steering chokepoint's:
   - **One chokepoint.** Every proposal state flip passes through the one
     private transition method in `db/gate.py` (first write wins; a losing
     race gets a typed 409 naming the standing decision). A second flipping
     code path is a census failure (`tests/unit/test_gate_chokepoint.py`).
   - **The record is never authority.** A stored proposal cannot cause
     execution; only the live hook waiting on the decision can let the call
     proceed. Approve rides back to that hook or nowhere.
   - **Fail-closed when armed.** Armed plus any error (hub down, HTTP error,
     poll timeout, expiry) is a deny with its reason named; the hook has no
     allow-on-error path, and there is no timeout-auto-allow. Unarmed, the
     hook is inert: no rows, no hub contact, bounded latency.
   - **Restart invalidation.** Hub startup flips every held proposal to
     `invalidated`; nothing held pre-restart is decidable post-restart. The
     agent proposes again by retrying, never resumes.
   - **Redaction.** The hook sends a sha256 and the first 120 characters of
     the canonical arguments; the full payload never crosses the wire, never
     lands in a row, and the hub-side gate modules are grep-censused against
     touching it. Deny reasons are bounded one-liners.
   - **The install never edits another app's config.** `holdspeak gate
     install` prints the hook block; adding it to `~/.claude/settings.json`
     is the user's own act. Arming is a second, separate opt-in
     (master switch AND a per-repo matcher), read back by `doctor`.
   - The gate's Stop-hook leg reports the session's token totals (numbers
     and the model name only, summed from the agent's own transcript
     locally) to the loopback hub for the session receipt line. No message
     text leaves the hook process.

---

## 4. Egress points: everywhere data can leave the machine

The machine-readable source for destination names, boundaries, data classes,
authority, background ability, and revoke actions is
[`trust-destinations.json`](trust-destinations.json). Setup, doctor, Web, and
Swift render that registry with current enabled state; this narrative table
adds implementation detail but is not a second product inventory.

| Egress | Trigger | What leaves | Gate |
|---|---|---|---|
| **Configured remote model endpoint** (`kernel/inference_runner.py` → reviewed endpoint adapter) | An admitted attempt whose frozen **Runs on** revision names an off-machine OpenAI-compatible endpoint | The model input selected for that attempt (prompt, context, or transcript/dictated text as applicable) and endpoint/model request metadata; never raw audio or embeddings | You deliberately author and assign the destination. Each physical attempt gets its own admitted child and receipt; local destinations never take this crossing, and fallback is a separately frozen attempt. |
| **Deferred-intel failure webhook** (`intel_queue.py`, the `urlopen` send) | User configures `intel_retry_failure_webhook_url` | Queue statistics only (counts, rates), **no transcript** | Opt-in (URL must be set). |
| **Wake-model download** (`wake_word.py`, first enable) | `wake_word.enabled` flipped on with models absent | Nothing leaves: an inbound fetch of the detection models (~7 MB) from the openWakeWord GitHub releases, once, cached locally | Opt-in (the feature is off by default); stated in the settings copy. Detection itself runs locally and no audio ever egresses. |
| **Send to Slack** (`slack_export.py` → the gated webhook connector) | User configures `meeting.slack_webhook_url` AND approves one specific send | The meeting digest or follow-up draft, exactly as previewed on the proposal (plain text; no transcript, no audio) | Double opt-in: the URL must be set (consent for exactly its host; the connector refuses any other host before egress) and every send is a separate per-action approval. The webhook URL is treated as a credential: never in proposals, broadcasts, or API responses. |
| **Desk Slack relay** (`web/routes/desk_actuators.py` → the same gated webhook connector) | A desk or companion card proposes a Slack send AND you approve it | The proposed text, exactly as previewed (plain text) | The same double opt-in as Send to Slack: `meeting.slack_webhook_url` must be set and every send is a separate approval; the URL never rides a payload. |
| **Desk webhook connector** (`web/routes/desk_actuators.py` → `actuator_shared.execute_webhook_proposal`) | `meeting.companion_webhook_url` is configured AND you approve one specific send | The proposed text, exactly as previewed, to that one configured endpoint (Discord, Zapier, n8n, or any URL you set) | Double opt-in: the URL must be set (consent for exactly its host) and every send is a separate per-action approval. The URL is a credential: never in proposals, broadcasts, or API responses. |
| **Desk GitHub issue** (`web/routes/desk_actuators.py` → `gh issue create`) | The GitHub connector is enabled AND you approve one specific proposal | The issue title and body, exactly as previewed, through your own `gh` CLI | Opt-in + per-action approval; runs your authenticated `gh`, never a stored token of ours. Distinct from the read-only enrichment row below. |
| **Connector CLI enrichment** (`gh`, `jira` via subprocess) | User enables the connector pack | Entity IDs (PR/issue/ticket numbers) to the user's own CLI tools, which call their services | Opt-in + manifest permissions (`shell:exec`, `network:outbound`). |
| **Mission-control receipts** (`missioncontrol_bridge.py` → `gh pr list`) | A rails repo is named in your project map (`~/.holdspeak/delivery_workbench.json`) and the desk conveyor is open | Nothing composed: a read of that repo's open pull requests through your own authenticated `gh` CLI (GitHub learns which repo asked) | The map is yours to author; the belt's routes are GET-only end to end (fitness-tested); `gh` missing or failing renders as a typed absence, never a retry loop. |
| **PR receipts** (`delivery/pr_receipts.py` → `gh pr list`) | You click **Refresh** on the Pull requests section, or you set `pr_refresh_seconds` on a source's registry entry yourself | Nothing composed: one batched read of that registered repo's pull requests through your own authenticated `gh` (GitHub learns which repo asked). The optional **fetch** offered when a diff's commits are absent locally is a separate, explicit `git fetch` | Manual verb by default, never ambient; the cadence is per-source and hand-set. `gh` is grep-censused to this one module; a failing refresh degrades to a named stale row, keeping last-known-good. |
| **Mesh relay** (`intel/mesh_relay.py` → the hub relay queue) | An admitted run against a **Runs on** destination whose compatibility kind is `meshNode` | The prompt and result, between the hub and the machine you named; no provider key transits | You pair that node deliberately. Its per-node bearer authenticates worker HTTP, the pinned hub public Ed25519 key verifies the node/revision/operation/attempt/deadline-bound offer, and the hub private key never leaves hub custody. The worker reserves the offer before its local `InferenceRunner` can construct a provider; `holdspeak mesh serve` is the live consent. |
| **Web runtime responses** | A client requests data | Whatever the API returns (transcripts, action items, etc.) | Loopback by default; token-gated off-loopback. |
| **Device audio link** | A paired device streams audio | Audio in; status/LCD text out | PSK; same-LAN today. |
| **Browser mic capture** (`lib/speakToFill` → `POST /api/dictation/transcribe`) | The owner holds a mic or the Speak room's TALK key in the browser, **or** an open-mic session segments an utterance (`lib/openMic` posts through the same encoder and route) | Nothing leaves the machine: the WAV is posted to the hub on the same origin the page was served from, the hub's own local Whisper transcribes it, and the audio is never persisted (16 MB cap) | No egress point, held or continuous. Off-loopback the origin is the hub itself, token-gated like every other route; the audio never reaches a third party. Segmentation is decided in the browser (`lib/vad`, energy plus hangover, no model and no network), so continuous listening posts one WAV per detected utterance rather than a stream. |
| **Paired dictation delivery** (`POST /api/dictation/remote`) | The owner releases the native dictation control, releases TALK in the Speak room, or explicitly sends a preview/recovery draft | Finalized text plus an opaque delivery id to the named desktop; raw audio never crosses | Direct LAN/Tailscale peer, bearer-token gated off-loopback. The hub claims the id before delivery and caches the terminal Receipt; reconnecting with the same request returns that Receipt without typing twice. A different payload under the same id is refused. |

Browser history reads (`activity_*`) make **no network calls**; they are
read-only against local SQLite snapshots. The activity ledger never leaves the
machine except via the connector CLIs above (entity IDs only).

---

## 5. Secrets handling

- **Cloud API key**: read from an environment variable; **never written to
  config or the DB**. Since HS-112-01 the variable is per destination
  (`HOLDSPEAK_PROFILE_<ID>_KEY`); `OPENAI_API_KEY` remains only the hub's
  fallback when a feature has no destination assigned. A destination never
  borrows another one's key.
- **Device PSK**: generated lazily, stored in `config.json`
  (`device_audio.ensure_device_psk`); constant-time comparison; empty PSK fails
  closed.
- **Web auth token**: generated lazily, stored in `config.json`
  (`web_auth.ensure_web_token`); constant-time comparison; never logged.
- **Slack webhook URL** (`meeting.slack_webhook_url`): stored in
  `config.json` because it *is* the feature's configuration, but treated as
  a credential everywhere else: shown only in the Settings window, never on a
  proposal record, a broadcast, or any other API response (the connector
  joins it to the POST in memory at execution time).
- **Runs on destination keys**: a Runs on destination stores only its
  definition: name, kind, endpoint, model, and context window. The API retains
  the `profile` compatibility name. The API key is **never** part of the
  destination and **never syncs**. Each surface holds its own key for a shared destination: the device Keychain on
  iPad and iPhone, the hub's environment secret on the desktop
  (`HOLDSPEAK_PROFILE_<id>_KEY`). The key is joined to the request only at run
  time, never written to the synced shape, a ChangeSet, or any API response. A
  regression test asserts a key supplied to any ingress (a sync push or a REST
  body) never reappears on a read surface (the sync pull or `/api/profiles`).
- Bridge/firmware secrets (AIPI-Lite) live in gitignored `bridge.env` /
  `secrets.yaml`; `.example` templates are checked in.

---

## 6. Threat model summary

**In scope / mitigated:**
- Accidental transcript egress to the cloud → fail-closed default + regression test.
- Unauthenticated exposure when bound off-loopback → bind guard + token gate.
- Unauthorized device audio injection → PSK + (LAN) source-IP allowlist.

**Out of scope / accepted:**
- A compromised local account or file-level disk access without full-disk
  encryption (see §2).
- Malicious connector packs the user chooses to install (§3.4).
- Network-level confidentiality for cross-network device/web reach: owned by
  planned as future work (TLS, tunnels, per-device PSKs).

---

## 7. Reporting

This is a personal/local-first project. Security-relevant findings: open an
issue describing the data class, trust boundary, and egress point involved.

## See also

- [Models (bring your own)](MODELS.md): pointing at a cloud endpoint is the one
  deliberate egress choice.
- [Getting Started](GETTING_STARTED.md): the local-by-default setup this posture
  describes.
