# HoldSpeak Security & Privacy Posture

**Status:** living document.
**Last updated:** 2026-07-11.

This document is the threat model for HoldSpeak: what data it holds, where that
data lives, what can leave the machine, and the decisions behind its at-rest
posture. If code and this document disagree, that is a bug in one of them;
file it.

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
| **Web recovery drafts** | Browser `localStorage`, under versioned `hs.draft.v1.*` keys | High | Editable First Words, Dictation, Ask, Persona, capability, Coder session reply, and steering drafts. Written synchronously in this browser's storage; cleared after a confirmed retaining action where the surface has one. |
| **Web pending voice capture** | Browser IndexedDB, `holdspeak-voice-recovery` | High | One bounded WAV per voice-to-fill scope, retained only when transcription has not confirmed text. A retry reuses this local audio; successful transcription deletes it. No capture enters first-value measurement. |
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

**Decision: document the stance; do not implement app-level encryption now.**

Rationale:
- HoldSpeak is single-user and local. The realistic protection for at-rest data
  on a personal machine is **full-disk encryption** (FileVault on macOS, LUKS on
  Linux), which covers every file uniformly (including the DB, config, and any
  temp snapshots) without HoldSpeak holding a key it cannot safely manage.
- App-level encryption would require a key-management story (where does the key
  live on a headless homelab box?) that, done poorly, adds risk without adding
  protection.

**Residual risk:** if the machine is compromised at the file level and full-disk
encryption is off, transcripts, voice embeddings, and the activity ledger are
readable. We accept this for the local-first, single-user model and **recommend
users enable full-disk encryption**.

**Revisit trigger:** flip this decision if HoldSpeak gains multi-user installs,
a shared/server deployment, or stores third-party data under a contractual
confidentiality obligation. At that point, app-level encryption of the DB (e.g.
SQLCipher) becomes warranted and should be its own story.

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
4. **Connector packs**: user-supplied code under `~/.holdspeak/connector_packs/`
   runs **in-process with the user's permissions**. The manifest permission gate
   (`connector_runtime.py`) is an *honesty* mechanism, **not a security sandbox**:
   a malicious pack can call `subprocess.run` directly. Only install packs you
   trust.
5. **Session steering** (`coder_steering.py` → a this-device tmux pane): typing into
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

---

## 4. Egress points: everywhere data can leave the machine

The machine-readable source for destination names, boundaries, data classes,
authority, background ability, and revoke actions is
[`trust-destinations.json`](trust-destinations.json). Setup, doctor, Web, and
Swift render that registry with current enabled state; this narrative table
adds implementation detail but is not a second product inventory.

| Egress | Trigger | What leaves | Gate |
|---|---|---|---|
| **Cloud meeting intel** (`intel/providers.py` → OpenAI-compatible client) | `intel_provider` = `cloud`, or `auto` falling back | Transcript text (no audio, no embeddings, no activity) | Explicit provider choice. `provider="local"` (default) **never** egresses, locked by `tests/unit/test_intel_egress_invariant.py`; surfaced by `doctor` + `intel_egress` in the runtime status. |
| **Deferred-intel failure webhook** (`intel_queue.py`, the `urlopen` send) | User configures `intel_retry_failure_webhook_url` | Queue statistics only (counts, rates), **no transcript** | Opt-in (URL must be set). |
| **Wake-model download** (`wake_word.py`, first enable) | `wake_word.enabled` flipped on with models absent | Nothing leaves: an inbound fetch of the detection models (~7 MB) from the openWakeWord GitHub releases, once, cached locally | Opt-in (the feature is off by default); stated in the settings copy. Detection itself runs locally and no audio ever egresses. |
| **Send to Slack** (`slack_export.py` → the gated webhook connector) | User configures `meeting.slack_webhook_url` AND approves one specific send | The meeting digest or follow-up draft, exactly as previewed on the proposal (plain text; no transcript, no audio) | Double opt-in: the URL must be set (consent for exactly its host; the connector refuses any other host before egress) and every send is a separate per-action approval. The webhook URL is treated as a credential: never in proposals, broadcasts, or API responses. |
| **Desk Slack relay** (`web/routes/desk_actuators.py` → the same gated webhook connector) | A desk or companion card proposes a Slack send AND you approve it | The proposed text, exactly as previewed (plain text) | The same double opt-in as Send to Slack: `meeting.slack_webhook_url` must be set and every send is a separate approval; the URL never rides a payload. |
| **Desk webhook connector** (`web/routes/desk_actuators.py` → `actuator_shared.execute_webhook_proposal`) | `meeting.companion_webhook_url` is configured AND you approve one specific send | The proposed text, exactly as previewed, to that one configured endpoint (Discord, Zapier, n8n, or any URL you set) | Double opt-in: the URL must be set (consent for exactly its host) and every send is a separate per-action approval. The URL is a credential: never in proposals, broadcasts, or API responses. |
| **Desk GitHub issue** (`web/routes/desk_actuators.py` → `gh issue create`) | The GitHub connector is enabled AND you approve one specific proposal | The issue title and body, exactly as previewed, through your own `gh` CLI | Opt-in + per-action approval; runs your authenticated `gh`, never a stored token of ours. Distinct from the read-only enrichment row below. |
| **Connector CLI enrichment** (`gh`, `jira` via subprocess) | User enables the connector pack | Entity IDs (PR/issue/ticket numbers) to the user's own CLI tools, which call their services | Opt-in + manifest permissions (`shell:exec`, `network:outbound`). |
| **Mission-control receipts** (`missioncontrol_bridge.py` → `gh pr list`) | A rails repo is named in your project map (`~/.holdspeak/delivery_workbench.json`) and the desk conveyor is open | Nothing composed: a read of that repo's open pull requests through your own authenticated `gh` CLI (GitHub learns which repo asked) | The map is yours to author; the belt's routes are GET-only end to end (fitness-tested); `gh` missing or failing renders as a typed absence, never a retry loop. |
| **Mesh relay** (`intel/mesh_relay.py` → the hub relay queue) | A run against a Runs on destination whose compatibility kind is `meshNode` | The prompt and the result, between the hub and the machine you named (both yours; the worker authenticates with the hub token) | You author the destination, and the node serves only while `holdspeak mesh serve` runs on it (stopping it reads offline within seconds). No key ever transits: the node resolves the run through its own config and env. |
| **Web runtime responses** | A client requests data | Whatever the API returns (transcripts, action items, etc.) | Loopback by default; token-gated off-loopback. |
| **Device audio link** | A paired device streams audio | Audio in; status/LCD text out | PSK; same-LAN today. |
| **Paired dictation delivery** (`POST /api/dictation/remote`) | The owner releases the native dictation control or explicitly sends a preview/recovery draft | Finalized text plus an opaque delivery id to the named desktop; raw audio never crosses | Direct LAN/Tailscale peer, bearer-token gated off-loopback. The hub claims the id before delivery and caches the terminal Receipt; reconnecting with the same request returns that Receipt without typing twice. A different payload under the same id is refused. |

Browser history reads (`activity_*`) make **no network calls**; they are
read-only against local SQLite snapshots. The activity ledger never leaves the
machine except via the connector CLIs above (entity IDs only).

---

## 5. Secrets handling

- **Cloud API key**: read from an environment variable (default `OPENAI_API_KEY`,
  or a configured name); **never written to config or the DB**.
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
