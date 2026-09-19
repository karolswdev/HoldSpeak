# 05 — Desk census, 2026-09-19 (read-only)

Taken 2026-09-19 12:50–12:55 MDT (18:50 UTC) against the owner's real machine.
Repo at `/Users/karol/dev/tools/HoldSpeak`, `main` @ `16d78b0b`. Nothing was
written: the live DB was opened `mode=ro` with `PRAGMA query_only=1`; the retired
DB was **copied** to scratchpad and queried there so the original inode was never
opened by this census.

---

## 0. The finding that reframes every number below

**The owner's real desk DB was retired 38 minutes before this census, and the
live DB is empty.**

| | |
|---|---|
| `~/.local/share/holdspeak/holdspeak.db` | **born 2026-09-19 12:12:56**, 3.3 MB, schema v79, 249 tables, **essentially zero rows** |
| `~/.local/share/holdspeak/retired-2026-09-19/holdspeak.db` | **138 MB**, schema v79 (migrated 11:22:46 today), 250 tables — this is the real desk, Aug 2026 → 12:11 today |

The retired directory was created at 12:12. Nothing in the package writes a
`retired-*` path (`grep -rn "retired-" holdspeak/ scripts/` → no hits), so the
move was made by hand — by the owner or by an agent — immediately before the hub
was restarted at 12:12:56. The hub then reconciled a fresh schema onto a new
file (`holdspeak.log`, `2026-09-19 12:12:57 | holdspeak.db.reconcile | Reconcile:
created tables [...]` — all 249).

**So a census of the live DB measures a 38-minute-old empty file, not a product
in use.** Everything in §2–§3 below is therefore taken from the **retired** DB,
which is the owner's actual history. Both are reported where it matters.

---

## 1. Runtime

| Thing | State |
|---|---|
| Hub | **Running.** PID 31478, listening `127.0.0.1:53674`. `GET /health` → `{"status":"ok"}` |
| Hub code | **A worktree, not main**: `/private/tmp/muaddib-xxiii/wt16`, branch `feat/hs-200-16` @ `09159edc` (a merge of `origin/main` into that branch — it carries 200-42/43/45) |
| Started | 12:12 MDT today, 4 minutes before the fresh DB was reconciled |
| Version route | None exposed unauthenticated. `GET /api/health` → `{"success":false,"error":"principal_right_required"}` — there is no unauthenticated version/commit route |
| Owner lock | `holdspeak.db.owner.lock` → `{"pid":31478,"port":53674,"label":"holdspeak web"}` — correctly held |
| DB journal mode | **WAL**, on both the live and the retired file (`PRAGMA journal_mode` → `wal`). WAL is on; that part of 200-45 landed. Live WAL is 4.1 MB against a 3.3 MB DB |
| MCP sidecar | **Two of them.** PID 36653 (`uv run holdspeak-mcp`, started 12:26 today, no DB handle open yet) and **PID 55661, running since 2026-08-26**, which still holds **three read-write handles (`8u`, `9u`, `10u`) on the RETIRED inode** — a month-old sidecar writing to a file the product has abandoned. Both run from `/Users/karol/dev/tools/HoldSpeak/.venv`, i.e. a different tree from the hub |
| Log | `~/.local/share/holdspeak/holdspeak.log`, **41 MB** |

The P0 from memory (`reference_mcp_sidecar_second_writer`) is still live and has
now produced a concrete split: the sidecar and the hub are on **different
database files**.

---

## 2. Table census

249/250 tables. Reporting only non-empty ones; the other ~140 are zero in both
files. `_fts_*` shadow tables excluded.

### 2a. The live (empty) DB — everything written since 12:12:56

| Table | Rows | Newest | Meaning |
|---|---|---|---|
| `skills` | 10 | 12:12:57 | boot-seeded skill catalogue |
| `kernel_operations` / `kernel_receipts` | 7 / 7 | 12:43:08 | every admitted operation since boot: heartbeat sweeps only |
| `kernel_journal` | 5 | 12:13 | kernel append log |
| `pipeline_events` | 93 | 12:49 | runtime event stream |
| `inference_*` (routes, plans, executions) | 1–6 each | 12:13:00 | one boot-time inference route (model preload) |
| `inference_assignments` / `_heads` | 1 / 1 | 12:12:57 | **one** assignment — a fresh default, not the owner's six |
| `refinement_*`, `model_profile_*`, `deployment_revisions`, `cadence_policies`, `activity_privacy_settings` | 1 each | 12:12–12:43 | boot defaults |

Everything a user makes — meetings, projects, notes, threads, dictations,
watches, decisions — is **0**.

### 2b. The retired (real) DB — the owner's actual desk

| Table | Rows | Newest | Meaning |
|---|---|---|---|
| `pipeline_events` | **140,357** | 2026-09-19 11:31 | runtime event stream (dominates the 138 MB) |
| `kernel_operations` / `kernel_receipts` | **3,023 / 3,023** | 2026-09-19 11:58 | the kernel ledger — one row per admitted operation |
| `kernel_journal` | 2,397 | 09-19 11:34 | append-only kernel log |
| `monday_brief_items` | 1,839 | — | candidate items for the one brief ever generated |
| `inference_route_execution_commands` | 276 | 09-19 11:22 | per-step inference route commands |
| `activity_records` | 164 | 2026-08-24 | browser/app activity import (stopped 3.5 weeks ago) |
| `watch_setup_proposals` | 114 | 2026-09-04 | connector suggestions offered during Room setup |
| `inference_route_plans` | 101 | 09-19 11:22 | planned inference routes |
| `kernel_inference_receipt_attestations` | 104 | 09-19 11:34 | receipts binding an inference to a model |
| `refinement_aggregate_commands` | 77 | — | Thought-refinement command log |
| `refinement_hosts` | 70 | — | refinement host registrations |
| `service_events` | 57 | 2026-09-05 | service-level event log |
| `inference_runtime_leases` | 50 | 09-19 11:22 | model runtime leases |
| `inference_route_executions` / `_attempts` / adoption tables | 46 each | 09-19 11:22 | 46 routed inferences ever |
| `project_setup_answers` | 42 | 2026-09-04 | Room interview answers |
| `project_commands` | 41 | 2026-09-04 | Room mutation log |
| `kernel_parent_runs` | 38 | 09-19 11:34 | parent-run bookkeeping |
| `dictation_journal` | **19** | **2026-09-19 03:26** | dictation sessions with text |
| `desktop_type_receipts` | **31** | **2026-09-19 09:26** | text actually typed into apps |
| `connector_watches` / `watch_rules` / `project_sources` | **32 / 32 / 32** | 2026-09-04 | watches and their rules |
| `refinement_lifecycle_revisions` | 28 | 2026-08-31 | Thought lifecycle |
| `steward_steps` | 28 | 2026-09-04 | steward run steps |
| `thread_message_parts` / `thread_messages` | 28 / 26 | **2026-08-30** | desk chat |
| `desk_projection_state` | 22 | 09-19 11:37 | desk projection cursors |
| `project_changes` | 22 | 2026-09-04 | Room delta rows |
| `notes` | 17 | 2026-09-03 | desk notes |
| `remote_dictation_deliveries` | 14 | 2026-09-10 | remote dictation handoffs |
| `project_setup_sessions` | 14 | 2026-09-04 | Room setup runs |
| `project_observations` | 14 | — | evidence gathered for Rooms |
| `ask_results` | 13 | 2026-08-30 | Ask runs |
| `project_proposals` | 13 | 2026-09-04 | Room proposals |
| `deployment_revisions` | 13 | — | model deployment history |
| `directory_memberships` | 12 | 2026-08-31 | desk directory membership |
| `intel_jobs` | **10** | **2026-09-19 11:38** | queued meeting-intelligence work |
| `projects` | **10** | 2026-09-04 | Rooms |
| `threads` | 10 | 2026-08-30 | desk chat threads |
| `refinement_invocations` / `_review_results` | 10 / 10 | 2026-08-31 | Thought refinement |
| `inference_assignments` | 10 | — | model→capability assignments |
| `meetings` | **9** | **2026-09-19 11:37** | recorded meetings |
| `steward_policies` | 9 | 2026-09-05 | per-Room steward config |
| `refinement_thoughts` | 8 | 2026-08-31 | Thoughts |
| `segments` | 7 | 2026-08-23 | transcript segments (across all 9 meetings) |
| `directories`, `recipes` | 6, 6 | 2026-09-03 | desk folders; practice recipes |
| `intel_job_attempts` | **5** | **2026-09-19 11:38** | drainer attempts — **all refused/skipped** |
| `watch_evaluations` | **5** | **2026-09-19 11:27** | watch runs |
| `project_updates` | 5 | 2026-09-04 | published Room updates |
| `profiles`, `first_value_events`, `inference_model_acquisitions`, `knowledge_memberships` | 5 each | — | model profiles; first-value funnel; downloads; KB members |
| `gate_audit`, `refinement_attachment_revisions`, `refinement_context_actions` | 4 each | 2026-08-31 | coder gate; Thought context |
| `steward_runs` | **3** | 2026-09-04 | steward runs (all `completed`) |
| `workbench_items` | 3 | 2026-08-31 | workbench contents |
| `scheduled_recordings` | **2** | **2026-09-19 11:37** | scheduled captures |
| `cadence_loops` | 2 | 2026-09-03 | cadence loops — **both `killed`** |
| `watch_provider_connections` | 2 | 2026-09-03 | GitHub + Jira, both `connected` |
| `artifacts`, `artifact_sources`, `project_reviews`, `monday_brief_item_shelf`, `gate_proposals`, `activity_import_checkpoints` | 2 each | ≤ 2026-09-04 | — |
| `monday_briefs` | **1** | 2026-08-19 | Monday briefs ever generated |
| `action_items`, `project_items`, `workbenches`, `recipe_results`, `kbs`, `milestones`, `steering_audit`, `onboarding_state`, `needs_you_last_known` | 1 each | ≤ 2026-09-19 | — |

**Still exactly zero on the real desk:** `intel_snapshots`, `watch_effects`,
`decisions`, `decision_records`, `decision_commitments`,
`follow_through_proposals`, `cadence_nudges`, `calendar_events`, `speakers`,
`interview_sessions`, `meeting_projects`, `connector_reactions`, `plugin_runs`,
`plugin_run_jobs`, `workbench_runs`, `tool_turns`, `work_attempts`,
`kernel_schedule_ticks`, `activity_annotations`, `actuator_proposals`,
`context_promotions`, `bookmarks`, `topics`, `mesh_*`, `authority_grants`.

**People ledger** (`~/.local/share/holdspeak/people.v1.sqlite3`, 20 KB): the file
contains **one table, `meta`, with 2 rows**. No `people`, no relationships, no
1:1s, no commitments — the store was initialised (`people.store-setup`,
2026-08-30) and never used. **0 people.**

### 2c. What the owner actually has, in his terms

- **Meetings: 9.** 4 from 2026-08-12 stuck in `capture_status=recording` (never
  finalised), 1 test row (`"Already titled"`, 0.006 s), 2 real short captures
  (30 s and 22 s), and **2 created today at 11:37**. Total recorded audio across
  the whole history is **~83 seconds**. 7 transcript segments exist, all from
  2026-08-23. **Intelligence runs that produced a snapshot: 0. Proposals from a
  meeting: 0. Decisions: 0.**
- **Dictation: 19 sessions**, 31 typed deliveries, last one **today at 03:26 and
  09:26**. This is the one surface with genuine, recent, repeated daily use.
- **Rooms/projects: 10**, of which **9 are archived walk seeds** ("Ship the Q4
  platform on schedule with zero incidents" ×7) and **1 is active**:
  `proj-10b35905777c` — *"Complete delivery of governance framework for
  EverDriven Software Architecture."* 32 sources attached (19 GitHub, 12 Jira,
  1 native). 5 updates published, 14 observations, 3 steward runs (all
  2026-09-03/04, all completed).
- **Watches: 32.** 26 enabled-but-unarmed, **4 enabled-and-armed**, 2
  armed-but-disabled. 5 evaluations ever, **2 of them today at 11:27
  (scheduled)**. **Effects minted: 0.**
- **Decisions / follow-through / commitments: 0 / 0 / 0.**
- **Cadence: 2 loops, both `killed`; 0 nudges.** `cadence.enabled = False`.
- **Scheduled recordings: 2** (`"Scheduled recording"` and `"LOL"`, both
  one-shot, both `idle` after firing). Both fired today — they are what produced
  today's two meetings.
- **Monday briefs: 1**, from 2026-08-19.
- **Plugin jobs: 0** in every status.
- **Intel queue depth: 10 jobs — 7 `superseded`, 2 `skipped`, 1 `failed`. Zero
  succeeded, ever.**
- **Asks 13 · Thoughts 8 · Notes 17 · Threads 10** (last message 2026-08-30).
- **Workbenches 1** with 3 items, **0 runs**. **Recipes 6, 1 result.**
- **Heartbeat: 1,270 sweeps / 1,264 notify operations**, last 11:58 today.

---

## 3. Diff against the 2026-09-13 audit

Audit numbers from `docs/internal/OPERATIONAL-SURFACE-AUDIT.md:212-231`.

### What moved

| Metric | 09-13 | Today | Read |
|---|---|---|---|
| `heartbeat.sweep` / `.notify` | 724 / 718 | **1,270 / 1,264** | +546 sweeps in 6 days — the loop runs |
| `inference.invoke` | 147 | 153 | +6 |
| `dictation.session` / `desktop.type_text` | 35 / 30 | **36 / 31** | +1 each. One dictation in six days |
| `meeting.session` | 1 | 1 | unchanged |
| meetings | 7 | **9** | +2, both today, both from scheduled recordings |
| `intel_jobs` | (1 queued since 09-10) | **10** | the queue is being written |
| **`intel_job_attempts`** | 0 drains | **5, three of them today** | **the drainer exists and runs** |
| `watch_evaluations` | 3 | **5** | +2 today, both `scheduled` |
| watches armed | **2** | **4** (+2 armed-but-disabled) | arming happened |
| `scheduled_recording` kernel ops | not measured | 4, **2 today** | the schedule fires |
| schema | v77 | **v79** | the newest surface has now touched his machine |

The two callers the audit named as missing are **both present and executing**:

```
2026-09-19 12:12:57 | INFO | holdspeak.intel_queue_conductor | Intel queue drainer started (poll 15s)
2026-09-19 11:28:06 | INFO | holdspeak.runtime.heartbeat | heartbeat sweep: watches=4 rooms=1 ...
```

HS-200-42 (drainer), HS-200-43 (arming) and HS-200-45 (WAL) are on his machine
and working as wired.

### What is still zero, and why

| Still 0 | Audit's stated cause | Did the merged fix change it? |
|---|---|---|
| **`intel_snapshots`** | §3.1 "nothing drains the intel queue" | **Fix merged and running — and the count is still 0.** The drain no longer fails silently; it now fails loudly. Every claim is refused (below). |
| **`watch_effects`** | §3.3 effects only minted inside `evaluate_due` | Fix merged. Two scheduled evaluations ran today and **completed with zero matches**, so no effect was owed. Not proven either way — the fix has never had a matching evaluation to mint from. |
| **`decisions` / `decision_records` / `decision_commitments`** | downstream of intel | Unchanged, and cannot change: they are fed by intel snapshots, which is 0. |
| **`cadence_nudges`** | `cadence.enabled = False` | Config, not code. Still `False` (`~/.config/holdspeak/config.json`). Both loops `killed`. |
| **`calendar_events`** | `calendar.sources = []` | Still `[]`. No calendar connected. |
| **`meeting_projects`** | no meeting ever linked to a Room | Still 0 — and `meeting.intelligence_auto = 'room_linked'`, so auto-intel is gated on a link that has never been made once. |
| **`interview_sessions`** | the Interview face is parked | Unchanged. |
| **`plugin_runs` / `workbench_runs` / `tool_turns` / `work_attempts`** | never driven | Unchanged. |
| **`speakers`** | `diarization_enabled = False` | Config. Still off. |
| **People ledger** | not measured in the audit | 0 people. The store has never held a row. |

### The one blocker that now explains the biggest zero

`intel_snapshots` is 0 **not** because nothing drains the queue — it drains every
15 s — but because every claim is refused by model-assignment resolution:

```
2026-09-19 11:37:22 | ERROR | holdspeak.meeting_session | meeting session admission refused:
                              no_compatible_assignment (Model profile is no longer compatible.)
2026-09-19 11:38:02 | INFO  | holdspeak.db.intel | Plugin project_detector excluded from bound claim:
                              no model assignment can be frozen (HS-151-03 skip-with-receipt)
   ... same for requirements_extractor, action_owner_enforcer, decision_capture ...
2026-09-19 11:38:02 | WARNING | holdspeak.intel_queue | Bound deferred intel claim refused: ValidationError
2026-09-19 11:43:02 | WARNING | holdspeak.intel_queue | Deferred intel queue failure rate 100.00%
                              exceeded threshold 50.00% for 300s
```

Root cause, measured in the retired DB:

| `inference_assignment_heads.assignment_key` | resolved `profile_id` | exists in `profiles`? |
|---|---|---|
| `capability:speech.transcribe` | `speech-migrated-dfd3d641b539d8acc136fd7a` | yes (revisions) |
| `capability:chat.turn` / `.guardrail` / `.compact` | `lan-qwen36-35b-a3b` | yes |
| `group:agents_tools` | `lan-qwythos-9b-vision` | yes |
| **`global`** | **`legacy-legacy-intel`** | **NO** |

`profiles` holds `legacy-intel`; `model_profile_revisions` holds neither. There
is no `capability:meeting.*` head, so meeting intelligence falls through to
`global` → `legacy-legacy-intel` → unresolvable → refusal. A second row carries
the same defect: `legacy-target_a46b5f675a5f` against a profile whose real id is
`target_a46b5f675a5f`.

This is the known double-prefix scar (memory: *143 migration double-prefixed
legacy profile ids on his desk*). **It is the single dangling string standing
between a merged, running drainer and the first intel snapshot this product has
ever produced.** It also refuses live meeting sessions outright.

*(Whether the freshly-created DB reproduces the defect cannot be told yet — it
has one default assignment and no legacy migration to mis-prefix.)*

---

## 4. Models and connectors

From `~/.config/holdspeak/config.json` (secret **values** never read or printed;
presence only).

| Capability | Assigned to |
|---|---|
| Transcription (`capability:speech.transcribe`) | `speech-migrated-…` profile; runtime model Whisper `base` via MLX (`mlx-community/whisper-base-mlx`, loaded OK at boot) |
| Chat turn / guardrail / compact | `lan-qwen36-35b-a3b` — **LAN llama.cpp, 192.168.1.43:8080** |
| Agent tools group | `lan-qwythos-9b-vision` — LAN :8081 |
| **Meeting intelligence** | **no capability head; falls to `global` → `legacy-legacy-intel` → broken.** Config separately names `meeting.intel_provider='cloud'`, `intel_cloud_model='gpt-5-mini'`, `intel_profile_id='legacy-intel'` — the config and the assignment ledger disagree, and the ledger wins |
| Dictation pipeline | `dictation.runtime.backend='auto'`, MLX `Qwen3-8B-MLX-4bit`, OpenAI-compatible fallback at `http://127.0.0.1:8000/v1`, `profile_id='legacy-intel'`. The llama.cpp path is broken: 16 × `Failed to load model from file: …gemma-4-E4B…gguf` |

**LAN reachability:** `GET http://192.168.1.43:8080/health` → `{"status":"ok"}`.
**Reachable from this sandbox** — the LAN block noted in memory did not apply
here.

**Connectors** (presence only):

| Connector | State |
|---|---|
| GitHub | `watch_provider_connections.wpc_github` = `connected`; `~/.config/gh/hosts.yml` present. 19 watches |
| Jira | `wpc_jira_karolsaneapple.atlassian.net` = `connected` (Apple-account identity). 12 watches. **`~/.acli` does not exist** — the acli config the Jira parity ruling depends on is absent from this HOME |
| Confluence | no connection row, no watches |
| Calendar | **none.** `calendar.sources = []`, `calendar_events` = 0 |
| Cloud intel key | `meeting.intel_cloud_api_key_env` set (an env-var *name*, 14 chars) |
| Telegram cadence | bot token present, `cadence_telegram.enabled = False` |
| Outbound webhooks | `https://ops.example.com/…`, `https://hooks.example.com/keep`, `companion_github_repo='owner/repo'` — **placeholder seed values, not real endpoints** |
| macOS keychain | no `holdspeak` generic-password item |

---

## 5. Logs

`~/.local/share/holdspeak/holdspeak.log`, 41 MB. Histogram over the last 200k
lines:

| Count | Line |
|---|---|
| **101,882** | `WARNING holdspeak.config.core | config: ignoring unknown key(s) in [meeting]: intel_temperature` |
| **42,417** | `WARNING holdspeak.web.routes.system | Rejected WebSocket: principal=none missing_right=owner` |
| 22,586 | `config: ignoring unknown key(s) in [ui]: history_lines, show_audio_meter, theme` |
| 22,586 | `config: ignoring unknown key(s) in [meeting]: intel_queue_poll_seconds, intel_retry_failure_alert_percent, …, web_auto_open` |
| 217 | `config: ignoring unknown key(s) in [meeting]: mir_profile, plugin_profile` |
| 77 | `Wake model 'hey_jarvis' unavailable: No module named 'openwakeword.utils'` |
| 19 | `Failed to read Vite React shell: … /scratchpad/wt*/holdspeak/static/_built/index.html` |
| 17 | `intent-router classify attempt N failed` |
| 16 | `Failed to load llama_cpp model: …gemma-4-E4B…gguf` |
| 11 | `Remote dictation delivery refused mid-effect: desktop_executor_warrant_invalid` |
| 11 | `Schema shape changed; backed up to holdspeak.db.<id>.bak before applying backfills` |
| 7 | `Failed to start turn: FOREIGN KEY constraint failed` (threads) |
| 3 | `meeting session admission refused: no_compatible_assignment` |
| 2 | `Deferred intel queue failure rate 100% exceeded threshold 50% for 300s` |
| 24 | tracebacks |

Three of these are chronic and worth naming:

1. **~148,000 config-key warnings.** Five config keys the product itself wrote
   are now unknown to the loader, and it re-warns on **every config read**. This
   alone is most of the 41 MB log. It is not cosmetic — it means the shipped
   config schema has drifted from what is on disk and nothing reconciles it.
2. **42,417 rejected WebSocket handshakes**, currently recurring **every 12
   seconds** — a browser tab still open on the desk, retrying `/ws` forever with
   no owner token, since the hub restarted onto the new DB. Visible in the last
   200 lines as an unbroken 12-second cadence from 12:13 to 12:25.
3. **The intel failure-rate alarm fired at 100%** at 11:43 today and was still
   standing when the DB was retired.

Background loops that report themselves running: `intel_queue_conductor`
("drainer started (poll 15 s)"), `runtime.heartbeat` (15-minute sweeps; on the
empty DB every sweep now reports `watches=0 rooms=0` in 2 ms, against 5.5–8.4 s
on the real desk). Wake word is configured but **unavailable** — the
`openwakeword` dependency is broken, so `wake_word.enabled=True` is a lie on this
machine, despite one `wake.session` kernel op today.

---

## 6. Verdict

**This is a product with a very large surface and near-zero traffic — with one
genuine exception.**

The honest shape of it:

- **Dictation is real and daily.** 19 journal entries, 31 typed deliveries, the
  most recent at 03:26 and 09:26 **this morning**. He uses this.
- **Nothing else has a pulse.** Nine meetings totalling ~83 seconds of audio in
  five weeks. One active Room, last touched 2026-09-04. Last desk chat message
  2026-08-30. One Monday brief, 2026-08-19. Zero decisions, zero commitments,
  zero follow-through, zero calendar, zero people. Both cadence loops killed.
- **The machinery is now genuinely running.** The drainer polls, watches arm and
  evaluate on schedule, scheduled recordings fire, WAL is on. The audit's two
  missing callers are no longer missing. That is real progress since 09-13, and
  it is measurable in the ledger.
- **And the first thing that machinery did when it finally ran was refuse.**
  Every intel claim today was rejected by a dangling profile id
  (`legacy-legacy-intel`). The queue's failure rate hit 100%. Meeting sessions
  were refused admission. The product spent six days getting to the point where
  it could try, and then could not resolve a model.
- **The desk was then wiped.** At 12:12 today the 138 MB history was moved aside
  and the hub restarted on an empty file. Whatever the reason, the effect is that
  the running product now knows nothing about him, and a month-old MCP sidecar is
  still holding write handles on the file it abandoned.

**The three counts that would have to move for "I use this on a Tuesday":**

1. **`intel_snapshots` > 0.** It has never been anything but zero. Fix the
   `global` assignment head (`legacy-legacy-intel` → `legacy-intel`, or give
   meeting intelligence its own capability head) and the already-running drainer
   produces the product's first snapshot the same day. This is the highest-value,
   lowest-cost move on the board.
2. **`meetings` with real duration, weekly.** Nine meetings, 83 seconds total,
   four of them stuck mid-`recording` since August. Until a real meeting is
   captured end to end, every downstream count is structurally zero regardless of
   how much code ships.
3. **`decisions` + `decision_commitments` > 0.** This is the payoff the whole
   arc was built for and it has never fired once. It is gated entirely on (1) and
   (2) — and additionally on `meeting_projects`, which is 0, while
   `meeting.intelligence_auto = 'room_linked'` requires it.

A fourth, nearly free: `calendar.sources` is `[]`. The calendar work of Phase 175
has never had a source to read. One connected calendar would give the scheduled
recordings, the Monday brief and the cadence loops something to be about.
