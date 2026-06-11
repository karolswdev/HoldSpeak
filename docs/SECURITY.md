# HoldSpeak Security & Privacy Posture

**Status:** living document.
**Last updated:** 2026-05-31.

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
| **Raw audio** | In-memory buffers during a meeting only | High | Not persisted; discarded after transcription. |
| **Config** | `~/.config/holdspeak/config.json` | Medium | Includes the **device PSK** and **web auth token** (secrets); the cloud API key is referenced by *env-var name*, not stored. |

All persistent state is under the user's home directory and protected by normal
filesystem permissions. There is **no telemetry, crash reporting, or background
beaconing** anywhere in the codebase.

---

## 2. Storage & at-rest posture

- The database (`holdspeak/db.py`, `DEFAULT_DB_PATH = ~/.local/share/holdspeak/holdspeak.db`)
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

---

## 4. Egress points: everywhere data can leave the machine

| Egress | Trigger | What leaves | Gate |
|---|---|---|---|
| **Cloud meeting intel** (`intel.py` → OpenAI client) | `intel_provider` = `cloud`, or `auto` falling back | Transcript text (no audio, no embeddings, no activity) | Explicit provider choice. `provider="local"` (default) **never** egresses, locked by `tests/unit/test_intel_egress_invariant.py`; surfaced by `doctor` + `intel_egress` in the runtime status. |
| **Deferred-intel failure webhook** (`intel_queue.py:345`) | User configures `intel_retry_failure_webhook_url` | Queue statistics only (counts, rates), **no transcript** | Opt-in (URL must be set). |
| **Connector CLI enrichment** (`gh`, `jira` via subprocess) | User enables the connector pack | Entity IDs (PR/issue/ticket numbers) to the user's own CLI tools, which call their services | Opt-in + manifest permissions (`shell:exec`, `network:outbound`). |
| **Web runtime responses** | A client requests data | Whatever the API returns (transcripts, action items, etc.) | Loopback by default; token-gated off-loopback. |
| **Device audio link** | A paired device streams audio | Audio in; status/LCD text out | PSK; same-LAN today. |

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
