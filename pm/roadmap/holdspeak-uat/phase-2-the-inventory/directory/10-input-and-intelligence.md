# Directory — Input & Intelligence

> **Auto-derived** by the 8-agent inventory sweep (Opus 4.8, 2026-07-08) from the
> phase record, then to be **verified on real glass** by the sweep story. This is the
> *starting map*, not the final ledger: the ✅/❓/— marks are the record's claim, and
> every ❓ (and every contested ✅) is exactly what the human checks on the device.

the daily-driver half — dictation, its pipeline and learning loop, wake word, languages, macros, activity, on-device models, onboarding, presence. Feeds sweep story **HSU-2-02**.

**76 capabilities** — 28 must-test, 33 should-test, 15 spot-check.

Surfaces: ✅ record says present · ❓ unknown, verify on device · — record says not on this surface.

| P | web | iPad | iPhone | Capability | Key | Phases | State recipe(s) |
|---|---|---|---|---|---|---|---|
| 🔴 | ✅ | ❓ | ❓ | 'Dictate with this' — feed a selected activity record into the next dictation | `activity.prebriefing.dictate_with_this` | HS-53 | `seeded-desk`, `intel-endpoint-dead` |
| 🔴 | ✅ | ❓ | ❓ | One tap on a wrong result teaches the correction memory | `dictation.correction.one-tap-teaches` | HS-45,HS-48 | `seeded-desk` |
| 🔴 | ✅ | ❓ | ❓ | Copilot learns from your corrections and nudges future routing | `dictation.correction.session_memory` | HS-39,HS-40 | `seeded-desk` |
| 🔴 | ✅ | ❓ | ❓ | Review every dictation in a durable Journal (said→typed timeline) | `dictation.journal.review` | HS-45 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | The learning digest reports a real learned-from-N-similar count, honest at zero | `dictation.learning-digest.honest-count` | HS-48 | `seeded-desk`, `fresh-desk` |
| 🔴 | ✅ | ❓ | ❓ | Correct a dictation in the moment ('Was that right? → Fix it → Taught') | `dictation.moment_of_truth.correct_inline` | HS-45,HS-48 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Dry-run / preview a dictation transformation | `dictation.pipeline.dry_run` | HS-3,HS-4 | `dictation-pipeline-enabled` |
| 🔴 | ✅ | ✅ | ❓ | Enable the dictation pipeline | `dictation.pipeline.enable` | HS-1,HS-3,HS-18 | `fresh-desk`, `dictation-pipeline-enabled` |
| 🔴 | ✅ | ✅ | ❓ | The dictation pipeline routes rough speech by intent and rewrites for its target | `dictation.pipeline.intent-routing` | HS-52,DIR-01 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Preview mode shows the rewrite first; Type commits, Discard drops it | `dictation.pipeline.preview-before-type` | HS-75,HS-60 | `seeded-desk` |
| 🔴 | ✅ | ❓ | ❓ | Route dictation through an OpenAI-compatible endpoint | `dictation.runtime.openai_compatible` | HS-3,HS-18,HS-19 | `dictation-pipeline-enabled`, `intel-endpoint-dead` |
| 🔴 | ✅ | ✅ | ❓ | Hold the hotkey, speak, release: text lands in the active app | `dictation.voice-typing.hold-to-talk` | HS-42,HS-65 | `fresh-desk` |
| 🔴 | ✅ | ✅ | ❓ | Hold-to-talk voice typing | `dictation.voice_typing.hold_to_talk` | HS-0,HS-1 | `fresh-desk` |
| 🔴 | ✅ | ✅ | ✅ | Map a spoken keyword to a system action on the Voice Commands board | `macros.voice_commands.board` | HS-52 | `seeded-desk` |
| 🔴 | ✅ | ❓ | ❓ | Fire a mapped action by speaking its keyword during dictation | `macros.voice_commands.fire_while_dictating` | HS-52 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Voice-command macros fire over the remote relay from iPad | `mobile.dictation.macros.fire` | HSM-18-02 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ❓ | Activity pre-briefing nudge cards feed the iPad dictation model | `mobile.dictation.prebriefing.nudge` | HSM-18-05 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ✅ | iPad voice teleprompter with opt-in preview receipt | `mobile.dictation.teleprompter.preview` | HSM-18-01 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | — | ✅ | ❓ | Import and manage on-device models (Files sideload + AirDrop + HF download) | `mobile.models.import_and_manage` | HSM-5-03,HSM-14-10 | `first-run-no-model`, `model-file-in-files-app` |
| 🔴 | ❓ | ✅ | ❓ | Choose where inference runs (local / homelab / any endpoint) | `mobile.models.inference_mode_setting` | HSM-5-06,HSM-14 | `endpoint-reachable`, `intel-endpoint-dead` |
| 🔴 | — | ✅ | ❓ | Run meeting intelligence fully on-device (Mode A, local GGUF) | `mobile.models.on_device_inference` | HSM-5-02,HSM-5-01,HSM-8-04 | `model-installed-on-device`, `meeting-just-ended-open-actions`, `airplane-mode-on` |
| 🔴 | ✅ | ✅ | ✅ | Bring your own LLM: GGUF in-process, MLX on Apple Silicon, or any OpenAI-compatible endpoint | `models.byo.three-backends` | HSM-05,HS-65 | `first-run-no-model` |
| 🔴 | ✅ | ✅ | ✅ | A profile can name another of your machines to execute runs on it | `models.mesh.serve-another-machine` | HS-85,HSM-25 | `mesh-node-alive`, `mesh-node-just-died` |
| 🔴 | ✅ | ✅ | ✅ | Runtime profiles: a named target you point work at, per agent | `models.profiles.runs-on-per-agent` | HS-84,HSM-17 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ❓ | ❓ | Full-screen /welcome first-run wizard to first dictation | `onboarding.welcome.wizard` | HS-42,HS-43 | `first-run-no-model` |
| 🔴 | ✅ | ❓ | ❓ | Ambient desktop presence HUD showing dictation state | `presence.desktop.hud` | HS-41,HS-43 | `fresh-desk` |
| 🔴 | ✅ | ❓ | ❓ | Wake word arms HoldSpeak hands-free | `wakeword.hands_free_arm` | HS-60 | `fresh-desk`, `wake-word-enabled`, `first-run-no-model` |
| 🔴 | ✅ | ❓ | ❓ | Wake result previews before it types (consent gate) | `wakeword.preview_before_type` | HS-60 | `wake-word-enabled`, `wake-result-pending-preview` |
| 🟡 | ✅ | — | — | Opt-in activity enrichment connectors (GitHub/Jira) | `activity.enrichment.connectors` | HS-9,HS-11,HS-13 | `seeded-activity-ledger` |
| 🟡 | ✅ | — | — | Private local activity ledger from browser history | `activity.ledger.browser_history` | HS-8 | `seeded-activity-ledger` |
| 🟡 | ✅ | ✅ | ❓ | Source-cited activity pre-briefing nudges | `activity.prebriefing.nudges` | HS-8,HS-9,HS-53 | `seeded-activity-ledger`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ❓ | ❓ | Source-cited pre-briefing nudges on the dictation surface | `activity.prebriefing.nudges` | HS-53 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Configure every dictation/pipeline knob from the web cockpit (no file editing) | `config.cockpit.copilot_setup` | HS-40 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | View, add, delete, and clear persistent corrections | `config.memory.curate_corrections` | HS-40 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Activity pre-briefing offers what you touched recently as source-cited dictation context | `dictation.activity-prebriefing.cited-nudges` | HS-53 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Agent hooks report cwd/session/awaiting state | `dictation.agent_hooks.claude_codex` | HS-18,HS-19 | `agent-pane-awaiting-input` |
| 🟡 | ✅ | — | — | Author dictation blocks (intent classes) | `dictation.blocks.author` | HS-1,HS-4,HS-18 | `dictation-pipeline-enabled` |
| 🟡 | ✅ | ✅ | ❓ | Every dictation lands in the journal: said, typed, route, latency | `dictation.journal.said-to-typed` | HS-45,HS-48 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Project KB placeholder enrichment | `dictation.kb.project_facts` | HS-1,HS-3,HS-47 | `seeded-project-kb` |
| 🟡 | ✅ | ✅ | ❓ | The spoken language setting pins any of Whisper's 99 languages | `dictation.language.99-whisper-languages` | HS-59 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | 'What HoldSpeak learned' digest over your corrections | `dictation.learning.digest` | HS-48 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Preview a dictation before it types | `dictation.preview_before_type` | HS-75-01,HS-75-05 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Teach a repo via .hs/ project context files | `dictation.project_context.hs_files` | HS-3,HS-18,HS-19 | `seeded-hs-context-repo` |
| 🟡 | ✅ | ❓ | ❓ | Replay a past dictation through the current pipeline (before→after) | `dictation.replay.through_current_pipeline` | HS-45 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Replay an old utterance through the updated pipeline and watch the routing change | `dictation.replay.watch-routing-change` | HS-45 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Multi-pass rewrite refinement of dictated text | `dictation.rewrite.multi_pass` | HS-39,HS-40 | `seeded-desk`, `intel-endpoint-dead` |
| 🟡 | ✅ | ❓ | ❓ | Pick the dictation LLM runtime backend | `dictation.runtime.backend_picker` | HS-1,HS-3,HS-18 | `fresh-desk` |
| 🟡 | ✅ | ❓ | ❓ | Model-assisted fallback for where dictation gets typed | `dictation.target.model_assisted_detection` | HS-39 | `seeded-desk`, `intel-endpoint-dead` |
| 🟡 | ✅ | ❓ | ❓ | Target-profile detection & override | `dictation.target.profile_detection` | HS-1,HS-18,HS-19 | `dictation-pipeline-enabled` |
| 🟡 | ✅ | ✅ | ❓ | Voice commands map a spoken keyword to a real action | `dictation.voice-commands.keyword-to-action` | HS-52 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Say the wake phrase and it listens hands-free, previewed never typed until confirmed | `dictation.wake-word.hands-free-preview` | HS-60 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Teach the copilot about a project: Project Facts + Project Context | `kb.project.facts_and_context` | HS-47 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Pin the spoken transcription language | `languages.spoken_language` | HS-59 | `fresh-desk`, `non-english-speaker` |
| 🟡 | ✅ | ❓ | ❓ | Teach spoken words to type as symbols | `languages.spoken_symbol_dictionary` | HS-59 | `fresh-desk`, `seeded-symbol-dictionary` |
| 🟡 | ✅ | ✅ | ❓ | Author voice-command macros on the iPad CommandsBoard | `mobile.dictation.commandsboard.author` | HSM-18-02 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ✅ | Spoken (non-English) language at every iPad transcription site | `mobile.dictation.language.spoken` | HSM-18-03 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ✅ | Spoken-symbol dictionary applies user symbols on iPad | `mobile.dictation.symbols.dictionary` | HSM-18-04 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Guided first-dictation with a live success reward | `onboarding.first_dictation.reward` | HS-42,HS-43 | `first-run-no-model` |
| 🟡 | ✅ | ❓ | ❓ | Guided runtime model setup with a one-click 'Test my runtime' | `onboarding.model.setup_assistant` | HS-42,HS-43 | `first-run-no-model` |
| 🟡 | ✅ | ❓ | ❓ | Ambient Trust & Privacy chip + 'what can leave this machine' panel | `onboarding.trust.privacy_chip` | HS-42 | `fresh-desk`, `intel-endpoint-dead` |
| 🟡 | ✅ | ❓ | ❓ | Turn desktop presence on/off from a settings toggle (live start/stop) | `presence.toggle.config_backed` | HS-43 | `fresh-desk` |
| ⚪ | ✅ | — | — | Activity-derived meeting candidates | `activity.candidates.meeting` | HS-9,HS-13 | `seeded-activity-ledger` |
| ⚪ | ✅ | ❓ | ❓ | Sectioned, searchable settings with progressive disclosure | `config.settings.searchable` | HS-42,HS-43 | `seeded-desk` |
| ⚪ | ✅ | — | — | Remote device audio ingest (AIPI-Lite) | `devices.audio.remote_ingest` | HS-14,HS-17,HS-21 | `mesh-node-alive`, `fresh-desk` |
| ⚪ | — | — | — | AIPI companion signals a waiting agent | `devices.companion.agent_waiting` | HS-20,HS-22,HS-23 | `agent-pane-awaiting-input`, `mesh-node-alive` |
| ⚪ | ✅ | — | — | Device health reporting | `devices.health.status` | HS-17,HS-22,HS-23,HS-24 | `mesh-node-alive` |
| ⚪ | ✅ | ❓ | ❓ | Clipboard token injection | `dictation.clipboard.token` | HS-1,HS-3 | `fresh-desk` |
| ⚪ | ✅ | ❓ | ❓ | 'Learned from N similar' chips inline where you work | `dictation.learning.trust_signals` | HS-48 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | Spoken punctuation words | `dictation.punctuation.spoken` | HS-1 | `fresh-desk` |
| ⚪ | ✅ | ❓ | ❓ | Project-doc suggestions stop repeating what's already written | `dictation.suggestions.quality_gate` | HS-39 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | The spoken-symbol dictionary types your own vocabulary | `dictation.symbol-dictionary.spoken-vocabulary` | HS-59 | `seeded-desk` |
| ⚪ | ✅ | ❓ | ❓ | See per-stage dictation latency (p50/p95) and copilot state | `dictation.telemetry.depth_readiness` | HS-39,HS-40 | `seeded-desk` |
| ⚪ | ✅ | ❓ | ❓ | Ambient nudge when a detected project has no knowledge | `kb.project.discovery_nudge` | HS-47 | `seeded-desk` |
| ⚪ | ✅ | ❓ | ❓ | Guided .hs/ setup + copyable 'draft with your coding agent' prompt | `kb.project.guided_setup` | HS-47 | `fresh-desk` |
| ⚪ | — | ✅ | ❓ | Get the right model tier for your device automatically | `mobile.models.per_device_defaults` | HSM-5-04,HSM-5-03 | `first-run-no-model` |
| ⚪ | ✅ | ❓ | ❓ | Signal dark-first UI across every web surface | `ui.signal.design_system` | HS-30,HS-44 | `fresh-desk` |

Priority: 🔴 must-test · 🟡 should-test · ⚪ spot-check · ⬛ skip.
