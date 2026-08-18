# Settings Surface Census

Audited: 2026-08-17, HEAD `245ad700` (main).
Auditor: read-only census worker.
Method: exhaustive code read of the Settings core, its modules, and
the backend service, cross-referenced with consumer grep and 33 live
screenshots at 1440x900 and 393x900 (zero console errors).


## 1. Where the surface lives

| Layer | File(s) | Notes |
|---|---|---|
| **Web drawer face** | `web/src/pages/cores/settingsPrefs.tsx:289-401` | 14-tile grid + POSTURE + FILTER + precedence chain |
| **Web modules** | `web/src/pages/cores/SettingsCore.tsx:429-891` | `renderModule()` switch; authored, never wire-derived |
| **Models module** | `web/src/pages/cores/settingsModels.tsx:93-568` | Destinations table + RUNS ON + hub engine + rails observer |
| **Bespoke widgets** | `web/src/pages/cores/settingsBespoke.tsx:42-97` | HotkeyCapture only |
| **Prefs face / status** | `web/src/pages/cores/settingsPrefs.tsx` | PrefsFace, PrefStatusBar, enum options, DeskModule |
| **Settings write lib** | `web/src/lib/settingsWrite.ts` | withRevision() optimistic concurrency helper |
| **Backend route** | `holdspeak/web/routes/system/settings.py:30-71` | GET/PUT `/api/settings` |
| **Secrets route** | `holdspeak/web/routes/system/settings_secrets.py:28-67` | PUT/POST/DELETE per secret |
| **Settings service** | `holdspeak/services/settings_service.py:178-895` | Validation, merge, persist via Config.save() |
| **Config dataclasses** | `holdspeak/config/core.py`, `config/model.py`, `config/meeting.py`, `config/device.py`, `config/ui.py`, `config/integrations.py` | The persisted schema |
| **MCP tools** | `holdspeak/mcp/families/settings.py:11-49` | `settings.get` / `settings.update` |
| **Persistence** | `~/.holdspeak/config.json` via `Config.save()`/`Config.load()` | JSON file, no DB table |


## 2. Structure audit

**Organization:** The drawer face is a 4x4 grid (14 tiles, 2 empty slots) with a FILTER input, a POSTURE cycle (safe/neutral/yolo), and a precedence chain readout. Clicking a tile replaces the entire body with the module. A footer status bar shows egress badge + receipt (USING / WRITTEN hh:mm:ss / REFUSED ...). A "PREFS" back button appears inside modules.

**Module roster** (code constant at `settingsPrefs.tsx:27-42`):
Appearance, Hotkey, Transcription, Voice Typing, Wake Word, Presence,
Meetings, Cadence, Devices, Delivery, Models, Desk, Integrations, System.
= **14 modules**.

**First impression:** The user sees 14 tiles, a FILTER, and a POSTURE knob.
None of the tiles are labeled by what the user DOES; all are labeled by
internal system names. "Cadence", "Presence", "Rails observer" mean nothing
to someone who just installed the product. The tile count alone is
operator-grade: no consumer product ships 14 settings categories.

**What is needed after first run:** After the seed (which provides profiles,
a workbench, a zone), the user needs the Hotkey (one key, once), possibly
the Transcription model size. Everything else has a sane default or should
be law. That is 1-2 controls out of the entire surface.


## 3. Census table

### 3.1 Appearance (4 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 1 | Desk sounds | Master SFX toggle | `SettingsCore.tsx:435-443` | `config.ui.desk_sounds` | `sfx.ts` reads from `useDesk` store; the setting only passes through `toggleSfx()` at write time | KEEP | Genuinely needed; the only sound control |
| 2 | Show audio meter | Show/hide mic VU meter | `SettingsCore.tsx:445` | `config.ui.show_audio_meter` | **DEAD** -- no consumer found outside config definition (`config/ui.py:22`) and the Settings UI itself | KILL | Setting exists, is saved, nothing reads it |
| 3 | History lines | Dictation history line count | `SettingsCore.tsx:446-448` | `config.ui.history_lines` | **DEAD** -- no consumer found outside config definition (`config/ui.py:23`) and the Settings UI itself | KILL | Setting exists, is saved, nothing reads it |
| 4 | Theme | Color theme (dark/light/dracula/monokai) | `SettingsCore.tsx:450` | `config.ui.theme` | **DEAD** -- no backend or web consumer reads the persisted value; the desk has hardcoded dark styling | KILL | The desk is dark. The theme setting does nothing visible |

### 3.2 Hotkey (1 control)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 5 | Push-to-talk key | The hold-to-speak key | `settingsBespoke.tsx:42-97` | `config.hotkey.key` + `.display` | `holdspeak/hotkey.py` global listener, `web_runtime.py:309` | KEEP | Essential; the only place to set it; edit-in-world is the right pattern |

### 3.3 Transcription (5 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 6 | Model size | Whisper model (tiny/base/small/medium/large) | `SettingsCore.tsx:466` | `config.model.name` | `holdspeak/plugins/dictation/runtime.py:146+` | DEFAULT | The seed should pick sensible default; power users have it in Models |
| 7 | Backend | Transcription backend (auto/mlx/faster-whisper) | `SettingsCore.tsx:467` | `config.model.backend` | `holdspeak/plugins/dictation/runtime.py` | FOLD-TO-RAW | Wiring: which engine runs. Duplicates the Hub Default Engine in Models module |
| 8 | Language | Whisper language | `SettingsCore.tsx:468` | `config.model.language` | `holdspeak/plugins/dictation/assembly.py` | KEEP | Genuinely needed; no other place to set it |
| 9 | Warm on start | Pre-load transcription model | `SettingsCore.tsx:469` | `config.model.warm_on_start` | `holdspeak/plugins/dictation/assembly.py:234` | DEFAULT | Should default to true; hiding this trades a 2s boot penalty for simplicity |
| 10 | Transcribe timeout | Timeout for transcription | `SettingsCore.tsx:470-473` | `config.model.transcribe_timeout_seconds` | `config/model.py:28` (dataclass default only) | FOLD-TO-RAW | Operator tuning; nobody needs to change the 120s default |

### 3.4 Voice Typing (12 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 11 | Pipeline enabled | Master dictation pipeline toggle | `SettingsCore.tsx:496` | `config.dictation.pipeline.enabled` | `holdspeak/speech_session/plan.py` | DEFAULT | Should be on by default; toggling it off breaks core functionality |
| 12 | Stages | Pipeline stage list | `SettingsCore.tsx:497` | `config.dictation.pipeline.stages` | pipeline assembly | FOLD-TO-RAW | Comma-separated stage names is operator-grade wiring |
| 13 | Latency budget | Max pipeline latency | `SettingsCore.tsx:498-502` | `config.dictation.pipeline.max_total_latency_ms` | pipeline dispatch | FOLD-TO-RAW | Operator tuning knob |
| 14 | Target profile override | Force a target detection profile | `SettingsCore.tsx:503-506` | `config.dictation.pipeline.target_profile_override` | pipeline routing | FOLD-TO-RAW | Debug/development only |
| 15 | Rewrite passes | LLM rewrite iteration count | `SettingsCore.tsx:507-510` | `config.dictation.pipeline.rewrite_passes` | pipeline rewriter | FOLD-TO-RAW | Operator tuning |
| 16 | Corrections | Enable correction memory | `SettingsCore.tsx:511-514` | `config.dictation.pipeline.corrections_enabled` | correction matcher | DEFAULT | Should be on; the correction memory is a pillar feature |
| 17 | LLM target detect | Use LLM for target detection | `SettingsCore.tsx:515-518` | `config.dictation.pipeline.target_detect_llm_enabled` | target detector | FOLD-TO-RAW | Operator knob |
| 18 | Detect below | Confidence threshold for LLM detection | `SettingsCore.tsx:519-523` | `config.dictation.pipeline.target_detect_llm_below` | target detector | FOLD-TO-RAW | Operator tuning slider |
| 19 | Journal | Enable dictation journal | `SettingsCore.tsx:524` | `config.dictation.pipeline.journal_enabled` | journal writer | DEFAULT | Should be on; the journal is a pillar feature |
| 20 | Journal retention | Journal max entries | `SettingsCore.tsx:525-529` | `config.dictation.pipeline.journal_retention` | journal pruner | DEFAULT | Hardcode 500; nobody adjusts this |
| 21 | Preview before type | Show preview before typing | `SettingsCore.tsx:532` | `config.dictation.preview_before_type` | `operation_policy.py:392` | KEEP | Genuinely user-facing preference |
| 22 | Voice commands | Enable voice macros | `SettingsCore.tsx:533-537` | `config.dictation.macros.enabled` | `dictation_runner.py:73` | KEEP | User-facing; "0 configured" is honest |
| 23 | Spoken symbols table | Custom symbol dictionary | `SettingsCore.tsx:539-593` | `config.dictation.spoken_symbols[]` | `text_processor.py:60` | KEEP | Genuinely user-facing; edit-in-world pattern |

### 3.5 Wake Word (5 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 24 | Enabled | Wake word master toggle | `SettingsCore.tsx:601` | `config.wake_word.enabled` | `web_runtime.py:369`, `wake_word.py` | KEEP | Needed |
| 25 | Model | Wake word model name | `SettingsCore.tsx:602-604` | `config.wake_word.model` | `wake_word.py` | FOLD-TO-RAW | Wiring; users should not need to type "hey_jarvis" by hand |
| 26 | Threshold | Detection sensitivity | `SettingsCore.tsx:605-609` | `config.wake_word.threshold` | `wake_word.py` | FOLD-TO-RAW | Operator tuning slider |
| 27 | Armed window | Seconds to listen after wake | `SettingsCore.tsx:610-614` | `config.wake_word.armed_window_seconds` | `wake_word.py` | FOLD-TO-RAW | Operator tuning |
| 28 | Action | Wake action (preview/type) | `SettingsCore.tsx:615-621` | `config.wake_word.action` | `runtime/wake_glue.py` | KEEP | User-facing choice with real consequences |

### 3.6 Presence (2 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 29 | Presence | Desktop presence (HUD) toggle | `SettingsCore.tsx:626` | `config.presence.enabled` | `desktop_presence.py:260`, `web_runtime.py:373` | KEEP | Needed |
| 30 | Mascot | Show Qlippy mascot | `SettingsCore.tsx:627` | `config.presence.mascot` | `config/device.py:38` (config definition only; the presence renderer reads it) | KEEP | User-facing; a person should choose whether the mascot is visible |

### 3.7 Meetings (30 controls across 5 sections)

**Capture** (8 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 31 | Mic device | Microphone device name | `SettingsCore.tsx:634-636` | `config.meeting.mic_device` | `meeting_recorder.py:141`, `web_runtime.py:366` | FOLD-TO-OBJECT | Belongs on the Meetings window, not global settings |
| 32 | System audio device | Loopback audio device name | `SettingsCore.tsx:637-639` | `config.meeting.system_audio_device` | `main.py:696` | FOLD-TO-OBJECT | Belongs on the Meetings window |
| 33 | Mic label | Speaker label for mic channel | `SettingsCore.tsx:640` | `config.meeting.mic_label` | `main.py:701`, `meeting_session/models.py:133` | DEFAULT | Hardcode "Me"; nobody changes this |
| 34 | Remote label | Speaker label for remote channel | `SettingsCore.tsx:641` | `config.meeting.remote_label` | `main.py:702`, `meeting_session/models.py:134` | DEFAULT | Hardcode "Remote"; nobody changes this |
| 35 | Diarization | Enable speaker diarization | `SettingsCore.tsx:642` | `config.meeting.diarization_enabled` | `config/meeting.py:132`, meeting session | FOLD-TO-RAW | Advanced feature; default off is correct |
| 36 | Diarize mic | Diarize the mic channel too | `SettingsCore.tsx:643` | `config.meeting.diarize_mic` | `config/meeting.py:133` | FOLD-TO-RAW | Only meaningful when diarization is on; nesting |
| 37 | Cross-meeting recognition | Recognize speakers across meetings | `SettingsCore.tsx:644-647` | `config.meeting.cross_meeting_recognition` | `config/meeting.py:134` | DEFAULT | Default on is correct; nobody disables this |
| 38 | Similarity | Cosine similarity threshold | `SettingsCore.tsx:648-652` | `config.meeting.similarity_threshold` | `speaker_intel.py:155-167` | FOLD-TO-RAW | Operator tuning slider |

**Export** (3 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 39 | Auto export | Auto-export transcript on stop | `SettingsCore.tsx:655` | `config.meeting.auto_export` | `main.py:796` | FOLD-TO-OBJECT | Belongs on the Meetings window; a per-meeting choice |
| 40 | Format | Export format (txt/markdown/json/srt) | `SettingsCore.tsx:656` | `config.meeting.export_format` | `main.py:797`, `meeting_exports.py:226` | FOLD-TO-OBJECT | Belongs with the export action |
| 41 | Open on web | Auto-open browser after capture | `SettingsCore.tsx:657` | `config.meeting.web_auto_open` | `web_runtime.py:581` | DEFAULT | Default true; nobody toggles this |

**Intelligence** (4 controls + placement provenance readout)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 42 | Intel enabled | Master intelligence toggle | `SettingsCore.tsx:660` | `config.meeting.intel_enabled` | `setup_status.py:123`, `intel/providers.py:187` | DEFAULT | Should be on; turning it off defeats the product |
| 43 | Realtime model | Path to local realtime model | `SettingsCore.tsx:661` | `config.meeting.intel_realtime_model` | `intel/providers.py:202,294` | FOLD-TO-OBJECT | Belongs on the Models module or the meeting itself |
| 44 | Summary model | Path to summary model | `SettingsCore.tsx:662` | `config.meeting.intel_summary_model` | service validation only | FOLD-TO-RAW | Rarely changed, operator-level |
| 45 | Cloud store | Allow cloud model storage | `SettingsCore.tsx:663` | `config.meeting.intel_cloud_store` | `intel/providers.py:244`, `runtime/meeting_glue.py:271` | FOLD-TO-RAW | Egress control; should be a trust surface, not a setting |

**Deferred queue** (7 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 46 | Deferred enabled | Enable deferred intel queue | `SettingsCore.tsx:689` | `config.meeting.intel_deferred_enabled` | `meeting_import.py:364`, `meeting_session` multiple | DEFAULT | Default on; the alternative is lost intel on model unavailability |
| 47 | Poll interval | Queue poll interval (seconds) | `SettingsCore.tsx:690-694` | `config.meeting.intel_queue_poll_seconds` | **DEAD** -- stored in config but never threaded to `IntelQueue` constructor; queue uses hardcoded 120.0 default (`intel_queue.py:774`) | KILL | Dial disconnected from runtime |
| 48 | Retry base | Initial retry delay (seconds) | `SettingsCore.tsx:695-699` | `config.meeting.intel_retry_base_seconds` | `commands/intel.py:92` (CLI only) | FOLD-TO-RAW | Operator tuning; CLI-only consumer |
| 49 | Retry max | Max retry delay (seconds) | `SettingsCore.tsx:700-704` | `config.meeting.intel_retry_max_seconds` | `commands/intel.py:93` (CLI only) | FOLD-TO-RAW | Operator tuning |
| 50 | Retry attempts | Max retry attempts | `SettingsCore.tsx:705-707` | `config.meeting.intel_retry_max_attempts` | `commands/intel.py:94`, `services/meeting_intel_service.py:24` | FOLD-TO-RAW | Operator tuning |
| 51 | Failure alert % | Alert threshold for queue failure rate | `SettingsCore.tsx:708-712` | `config.meeting.intel_retry_failure_alert_percent` | **DEAD** -- stored in config but never threaded to `IntelQueue` constructor; queue uses hardcoded `RETRY_FAILURE_ALERT_PERCENT` constant | KILL | Dial disconnected from runtime |
| 52 | Alert hysteresis | Minutes above threshold before alerting | `SettingsCore.tsx:713-717` | `config.meeting.intel_retry_failure_hysteresis_minutes` | **DEAD** -- same as above; not threaded through | KILL | Dial disconnected from runtime |

**Routing** (8 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 53 | Multi-intent routing | MIR master toggle | `SettingsCore.tsx:724` | `config.meeting.mir_enabled` | `web_runtime.py:182` | DEFAULT | Default on; MIR is a core feature |
| 54 | Routing profile | Which profile governs intent routing | `SettingsCore.tsx:728-732` | `config.meeting.routing_profile` | `web_runtime.py:183`, `intel_queue.py:308` | FOLD-TO-RAW | Operator choice; 5 profiles is complexity |
| 55 | Intent router | Enable the intent router engine | `SettingsCore.tsx:733` | `config.meeting.intent_router_enabled` | `intel_queue.py:200` | FOLD-TO-RAW | Another toggle for the same subsystem as #53 |
| 56 | Intent window | Rolling window length (seconds) | `SettingsCore.tsx:734-738` | `config.meeting.intent_window_seconds` | `config/meeting.py:79` | FOLD-TO-RAW | Operator tuning |
| 57 | Intent step | Rolling window step (seconds) | `SettingsCore.tsx:739-743` | `config.meeting.intent_step_seconds` | `config/meeting.py:80` | FOLD-TO-RAW | Operator tuning |
| 58 | Score threshold | Intent activation threshold | `SettingsCore.tsx:744-748` | `config.meeting.intent_score_threshold` | `config/meeting.py:81` | FOLD-TO-RAW | Operator tuning slider |
| 59 | Hysteresis windows | Damping windows for intent detection | `SettingsCore.tsx:749-753` | `config.meeting.intent_hysteresis_windows` | `config/meeting.py:82` | FOLD-TO-RAW | Operator tuning |
| 60 | Segment probe | Enable segment probe | `SettingsCore.tsx:754-757` | `config.meeting.intent_segment_probe_enabled` | `config/meeting.py:95` | FOLD-TO-RAW | Debug feature |

**Actuators** (4 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 61 | Allow actuators | Master actuator toggle | `SettingsCore.tsx:761` | `config.meeting.allow_actuators` | `plugins/host.py:146`, `setup_status.py:182` | KEEP | Genuine consent gate (Article V) |
| 62 | Allowed actuators | Allowlist of actuator IDs | `SettingsCore.tsx:762` | `config.meeting.allowed_actuators` | `config/meeting.py:104` | FOLD-TO-RAW | Comma-separated IDs; operator wiring |
| 63 | Webhook hosts | Allowed webhook hosts | `SettingsCore.tsx:763` | `config.meeting.webhook_allowed_hosts` | `setup_status.py:183` | FOLD-TO-RAW | Operator wiring |
| 64 | GitHub repo | Default companion GitHub repo | `SettingsCore.tsx:764-766` | `config.meeting.companion_github_repo` | `trust_destinations.py:63,83` | FOLD-TO-OBJECT | Belongs on the integration it configures |

### 3.8 Cadence (9 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 65 | Cadence enabled | Master cadence toggle | `SettingsCore.tsx:774` | `config.cadence.enabled` | `runtime/cadence.py:20` | KEEP | Needed |
| 66 | Pressure | Cadence aggressiveness | `SettingsCore.tsx:775` | `config.cadence.pressure` | `config/integrations.py:16` (policy timings) | KEEP | Genuinely user-facing preference |
| 67 | Use LLM | Enable LLM in cadence | `SettingsCore.tsx:776` | `config.cadence.use_llm` | cadence service | FOLD-TO-RAW | Operator knob |
| 68 | Tick interval | Cadence poll interval (seconds) | `SettingsCore.tsx:777-780` | `config.cadence.tick_interval_seconds` | `runtime/cadence.py:109` | FOLD-TO-RAW | Operator tuning |
| 69 | Quiet from | Quiet hours start (hour) | `SettingsCore.tsx:782-786` | `config.cadence.quiet_hours_start` | `runtime/cadence.py:79` | KEEP | Genuinely user-facing |
| 70 | Quiet until | Quiet hours end (hour) | `SettingsCore.tsx:787-791` | `config.cadence.quiet_hours_end` | `runtime/cadence.py:79` | KEEP | Genuinely user-facing |
| 71 | Max nudges/day | Daily nudge cap | `SettingsCore.tsx:792-796` | `config.cadence.max_nudges_per_day` | cadence service | KEEP | Genuinely user-facing |
| 72 | Telegram enabled | Enable Telegram surface | `SettingsCore.tsx:798` | `config.cadence_telegram.enabled` | `trust_destinations.py:65`, `runtime/cadence.py:65` | KEEP | Needed for the integration |
| 73 | Telegram allowed chats | Chat IDs Telegram may message | `SettingsCore.tsx:799` | `config.cadence_telegram.allowed_chat_ids` | `runtime/cadence.py:95+` | FOLD-TO-RAW | Comma-separated IDs is operator wiring |

### 3.9 Devices (1 control + dynamic walker)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 74 | Device name | Mesh advertised name | `SettingsCore.tsx:808` | `config.mesh.device_name` | `web_server.py:426`, `mesh.py:51` | KEEP | Needed |
| 75+ | Device keys | Dynamic walker over `config.device.*` | `SettingsCore.tsx:810-815` | `config.device.*` | `device_audio.py`, mesh | FOLD-TO-RAW | Generic walker; debug wiring |

### 3.10 Delivery (0 controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| -- | (redirect) | States "CONFIG LIVES IN DELIVERY" + Open button | `SettingsCore.tsx:820-828` | n/a | n/a | KEEP | Correct pattern: config lives on the object |

### 3.11 Models (18+ controls)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 76 | Destinations table | CRUD for inference targets | `settingsModels.tsx:365-469` | `/api/inference-targets` (DB profiles table) | inference routing, deployment | KEEP | THE one-dial law; correct home |
| 77 | Dictation runs-on | Which target runs dictation LLM | `settingsModels.tsx:472` | `config.dictation.runtime.profile_id` | `plugins/dictation/assembly.py` | KEEP | One-dial law |
| 78 | Meetings runs-on | Which target runs meetings intel | `settingsModels.tsx:295-300` | `config.meeting.intel_profile_id` | `intel/providers.py` | KEEP | One-dial law |
| 79 | Meetings provider | Provider intent (local/cloud) | `settingsModels.tsx:311-322` | `config.meeting.intel_provider` | `intel/providers.py`, `setup_status.py:135` | KEEP | Egress-critical; correctly subordinated to destination |
| 80 | Rails runs-on | Which target runs rails observer | `settingsModels.tsx:474` | `config.rails_observer.profile_id` | `web_server.py:1104` | KEEP | One-dial law |
| 81 | Backend (hub default) | Local LLM backend (auto/mlx/llama_cpp) | `settingsModels.tsx:477-487` | `config.dictation.runtime.backend` | `plugins/dictation/runtime.py` | KEEP | Needed; but DUPLICATES Transcription > Backend (#7) |
| 82 | MLX model | Path to MLX model | `settingsModels.tsx:489-497` | `config.dictation.runtime.mlx_model` | `plugins/dictation/runtime_mlx.py` | KEEP | Needed |
| 83 | llama.cpp model | Path to GGUF model | `settingsModels.tsx:499-507` | `config.dictation.runtime.llama_cpp_model_path` | `plugins/dictation/runtime_llama_cpp.py` | KEEP | Needed |
| 84 | Context window | n_ctx for local model | `settingsModels.tsx:509-517` | `config.dictation.runtime.n_ctx` | runtime construction | FOLD-TO-RAW | Operator tuning |
| 85 | Warm on start (hub) | Pre-load local model | `settingsModels.tsx:518-526` | `config.dictation.runtime.warm_on_start` | same as #9 | KILL (dup) | DUPLICATE of Transcription > Warm on start (#9); same config path |
| 86 | Idle eviction | Seconds before evicting idle model | `settingsModels.tsx:527-536` | `config.dictation.runtime.eviction_idle_seconds` | runtime eviction | FOLD-TO-RAW | Operator tuning |
| 87 | Rails enabled | Enable rails observer | `settingsModels.tsx:541-546` | `config.rails_observer.enabled` | `web_server.py:1074` | KEEP | Needed |
| 88 | Rails poll | Observer poll interval (seconds) | `settingsModels.tsx:547-554` | `config.rails_observer.poll_seconds` | `web_server.py:1074` | FOLD-TO-RAW | Operator tuning |
| 89 | Rails tail | Events to show | `settingsModels.tsx:555-562` | `config.rails_observer.tail` | `web_server.py:1074` | FOLD-TO-RAW | Operator tuning |

### 3.12 Desk (1 destructive action)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 90 | Reset to seed | Tombstone + reseed desk primitives | `settingsPrefs.tsx:236-283` | desk DB tables | desk store `resetDesk()` | KEEP | Correct: armed, honest, states what resets/keeps |

### 3.13 Integrations (8 secret slots)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 91 | Web pairing token | Hub auth token | `SettingsCore.tsx:847-859` | credential store | web auth middleware | KEEP | Security credential |
| 92 | Device audio key | Device PSK | same | credential store | `device_audio.py:562` | KEEP | Security credential |
| 93 | Telegram bot token | Telegram bot API token | same | credential store | cadence telegram | KEEP | Integration credential |
| 94 | Telegram pairing code | Telegram pairing code | same | credential store | cadence telegram | KEEP | Integration credential |
| 95 | Failure alert webhook | Webhook for queue failures | same | credential store | `trust_destinations.py:68` | FOLD-TO-RAW | Operator wiring |
| 96 | Failure alert credential | Auth header for failure webhook | same | credential store | `services/credential_service.py:133` | FOLD-TO-RAW | Operator wiring |
| 97 | Slack webhook | Slack incoming webhook URL | same | credential store | `slack_export.py` | KEEP | Integration credential |
| 98 | Custom webhook | Companion webhook URL | same | credential store | `trust_destinations.py` | KEEP | Integration credential |

### 3.14 System (generic walker; 0-N controls)

Shows "NO UNMAPPED KEYS" when all keys are claimed by modules (the
current state on a fresh HOME, as seen in the screenshot). If a new config
key appears in `config.json` without a module claiming it, the generic
walker renders it here as raw checkboxes/inputs.

### 3.15 Drawer face (1 control)

| # | Name | What it controls | Renders | Persists | Consumed by | Disposition | Why |
|---|---|---|---|---|---|---|---|
| 99 | Posture (control mode) | Authority policy: safe/neutral/yolo | `settingsPrefs.tsx:377-390` | `/api/authority/control-mode` | `coder_steering.py`, principals, authority system | KEEP | Genuinely global; correct placement |


## 4. Live shots

33 screenshots captured at both 1440x900 and 393x900, zero console
errors. All shots saved to:
`/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/8cb4eee1-518d-4508-859c-1c60b6eb0e3b/scratchpad/settings-audit/`

Key observations from the glass:

- The Meetings module requires scrolling past the fold in BOTH viewports.
  At 1440x900 it needs one scroll; at 393x900 the Models module also
  requires scrolling. No other module needs scrolling.
- The Models module's Destinations table at 393px is severely truncated:
  column labels are clipped ("ENDPOIN", "NEEDS_KEY"), field values are
  invisible beyond 3-4 characters. Practically unusable at mobile width.
- The System module shows "NO UNMAPPED KEYS" -- all config paths are
  claimed by authored modules, which is correct.
- The Delivery module shows "CONFIG LIVES IN DELIVERY" with an
  Open button -- the correct edit-in-world pattern.


## 5. The headline

### Counts

| Category | Count |
|---|---|
| **Total controls on glass** | **99** (including 8 secret slots, 1 destructive action, 14 module tiles, 1 posture knob) |
| **Unique editable settings** | **89** (excluding tiles, posture, reset, secrets = pure config dials) |
| **DEAD (setting saved, nothing reads it)** | **5** (show_audio_meter, history_lines, theme, intel_queue_poll_seconds, intel_retry_failure_alert_percent + hysteresis = 5 dials) |
| **DUPLICATE** | **2** (Backend appears in both Transcription and Models; Warm on start appears in both Transcription and Models) |
| **FOLD-TO-RAW (debug/operator wiring)** | **31** |
| **FOLD-TO-OBJECT (belongs on the thing it configures)** | **7** |
| **DEFAULT (hardcode the sane value)** | **12** |
| **KEEP (genuinely global, genuinely needed)** | **33** |

### The "after" sketch

If every recommendation landed, the Settings window would contain:
**33 controls** across roughly 7 modules (Hotkey, Language, Voice
Typing essentials, Wake Word on/off + action, Presence, Cadence
user-facing, Integrations credentials, Posture, and Models/Destinations).
The user opens Settings and sees 7 tiles, not 14. Voice Typing shows
3 controls (preview, voice commands, spoken symbols), not 12 pipeline
knobs. Meetings shows nothing in Settings at all: mic device, export
format, and auto-export live on the Meetings window itself. The 31
operator tuning knobs fold behind one RAW well inside the module they
belong to (the debug-hides-behind-RAW rule). The 5 dead settings and
2 duplicates are simply deleted. The 12 defaults are hardcoded and
their dials removed.

### The three ugliest things on glass

1. **The Meetings module is a scroll canyon.** 30 controls across 5
   sections (Capture, Export, Intelligence, Deferred queue, Routing,
   Actuators), many of which are operator tuning knobs (retry base/max,
   hysteresis windows, score thresholds, segment probes) that no user
   will ever touch. Five of these controls are provably dead (disconnected
   from the runtime). This single module violates every standing direction:
   it is not joyful, it is not edit-in-world (mic device belongs on the
   meeting), and it does not hide debug behind RAW.

2. **The Destinations table at mobile width is broken.** At 393px, the
   6-column table truncates every column to 3-4 visible characters. The
   NAME, ENDPOINT, and MODEL columns are unreadable. The TEST and delete
   verbs per row create a dense, unusable control surface. This is the
   single most important settings surface in the product (the one-dial
   law) and it is not usable on any viewport narrower than ~1200px.

3. **Five dead settings sit on glass pretending to work.** `show_audio_meter`,
   `history_lines`, and `theme` are saved to disk and render in the
   Appearance module, but nothing in the product reads them. The user
   changes Theme from Dark to Monokai and nothing happens. The deferred
   queue's Poll, Failure alert %, and Alert hysteresis are saved to config
   but never threaded to the `IntelQueue` constructor -- the queue runs
   on hardcoded defaults regardless. These are silent no-ops that violate
   Article VI (honest by construction: "no fallback that hides a failure").
