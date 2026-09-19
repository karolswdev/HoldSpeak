# Charter audit — runtime and database (Astra, read-only, 2026-09-19)

Session `01a0bbab-4549-7e93-8c1c-7335e58c8119`. Brief: TWO-BRAINS role ask. Tree at 16d78b0b. Live DB read with `sqlite3 -readonly mode=ro`.

**FACTS**

1. **RUN IT.** Main is `16d78b0b9c3b57f592cd1280e4aa19e72e6aaaa4`. From the owner’s normal shell:

   ```sh
   cd /Users/karol/dev/tools/HoldSpeak &&
   test "$HOME" = /Users/karol &&
   env -u HOLDSPEAK_ALLOW_UNOWNED_DB \
     HOLDSPEAK_WEB_HOST=127.0.0.1 \
     HOLDSPEAK_WEB_PORT=8765 \
     HOLDSPEAK_BACKEND_REVISION="$(git rev-parse HEAD)" \
     uv run holdspeak web --no-open
   ```

   `HOLDSPEAK_WEB_PORT` **is honoured** ([web_runtime.py:66](/Users/karol/dev/tools/HoldSpeak/holdspeak/web_runtime.py:66)). The DB is `/Users/karol/.local/share/holdspeak/holdspeak.db`, derived from HOME ([core.py:47](/Users/karol/dev/tools/HoldSpeak/holdspeak/db/core.py:47)). Startup logs the URL, **not commit plus DB**. Authenticated `GET /api/system/identity` returns captured `backend_revision`, `frontend_build`, `database_path`, PID and ownership ([health.py:58](/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/system/health.py:58), [runtime_identity.py:249](/Users/karol/dev/tools/HoldSpeak/holdspeak/runtime_identity.py:249)). No new identity mechanism is needed.

2. **Current process differs from the inventory.** At **16:02 MDT**, `ps`/`lsof` showed PID **39433**, parent **39431**, running from **main checkout**, listening on **127.0.0.1:53901**, with DB handles under a temporary `scratchpad/u1home`. The live lock’s **31478 / 53674** record is stale: that PID is absent. No owner-DB hub was found.

   For replacement, verify the lock PID’s process, working directory and DB handles; send `SIGTERM` only to the verified intended hub, await exit, then start the command above. Do not remove the lock or enable the unowned escape hatch: the authority is `flock`, and stale JSON does not retain it ([runtime_lock.py:11](/Users/karol/dev/tools/HoldSpeak/holdspeak/runtime_lock.py:11)). PID 39433 is a separate temporary-DB process.

3. **SUMMARY RUN—live SQL.** Queried using `sqlite3 -readonly 'file:/Users/karol/.local/share/holdspeak/holdspeak.db?mode=ro'`. The queue resolves to SERVICE **`meeting-intel-queue`**, authority basis **`meeting-intel-queue:deferred`** ([binder:126](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_deferred_queue_binding.py:126), [deferred_bound.py:118](/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_session/deferred_bound.py:118)). Base summary capability: **`meeting.deferred_analysis`** ([binder:64](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_deferred_queue_binding.py:64)).

   Live rows: exactly one head/assignment, `capability:speech.transcribe` → `speech-migrated-dfd3d641b539d8acc136fd7a`, revision 1. **No exact summary assignment; no text-model profile; zero meetings/snapshots.** Live `legacy-legacy-*` heads: **0**. Retired DB: `global → legacy-legacy-intel` remains. Repairing that retired head would not repair this live path.

4. **Lawful assignment repair already has a service.** Register one compatible model/deployment through `ModelLibraryService`—cloud via `POST /api/inference/model-library/connect-hosted-model`, LAN via `/define-endpoint` ([routes:101](/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/model_library.py:101)). Then OWNER calls `InferenceAssignmentService.set_assignment`, HTTP **`POST /api/inference/assignments/set`**, or MCP **`inference_assignment.set`**, with:

   ```json
   {
     "command_id": "<unique>",
     "expected_revision": 0,
     "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
     "entries": [{"profile_id": "<compatible-profile>", "profile_revision": 1}]
   }
   ```

   Use the actual returned profile revision. The existing Concierge **Use these** writes **group** assignments only ([concierge_service.py:1148](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/concierge_service.py:1148)); it needs a narrow exact-capability write if used here. SERVICE cannot inherit group/global assignments ([policy:93](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/inference_service_route_policy.py:93)). The owner’s assignment gesture supplies approval; no second confirmation is owed ([Constitution XI.4:184](/Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:184)).

5. **HOST.** `run_intelligence` enqueues first, then independently resolves mutable meeting config; exceptions become `"local"` ([meeting_intel_service.py:63](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_intel_service.py:63), [:81](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_intel_service.py:81)). Chair receives that host **after POST** and displays its chip only while the receipt exists ([ChairHome.tsx:614](/Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:614), [:1716](/Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:1716)).

   Execution instead uses the binder’s frozen SERVICE route. The drainer already attempts to overwrite `model_host` from that route before dispatch, but catches failure; its helper selects the **first route leg**, not necessarily a later fallback actually used ([intel_queue.py:425](/Users/karol/dev/tools/HoldSpeak/holdspeak/intel_queue.py:425), [deferred_bound.py:201](/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_session/deferred_bound.py:201)). Thus neither pre-run disclosure nor complete after-run truth is established.

6. **Two additional capture-path dependencies.** Admission unconditionally requests live-analysis, bookmark-label and auto-title routes—even with intelligence disabled. Missing assignments therefore disable transcription as `record_only` ([intel_admission.py:149](/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_session/intel_admission.py:149), [:292](/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_session/intel_admission.py:292)). Separately, Stop unconditionally requests deferred analysis for transcript segments and auto-title for untitled meetings ([session.py:686](/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_session/session.py:686), [intel_admission.py:467](/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_session/intel_admission.py:467)). That can run before “ask for summary”; the later `intelligence_auto` check does not govern this earlier handoff.

7. **RESTART.** Successful publication inserts `intel_snapshots(meeting_id,timestamp,summary)`; reopening loads the latest snapshot by meeting ID ([meeting_plugin_projection.py:262](/Users/karol/dev/tools/HoldSpeak/holdspeak/kernel/meeting_plugin_projection.py:262), [meetings.py:558](/Users/karol/dev/tools/HoldSpeak/holdspeak/db/meetings.py:558)). **Committed summaries survive same-DB restart by construction.** No storage redesign is indicated. However, Chair’s Open passes a bare ID; History requires `meeting:<id>` ([ChairHome.tsx:1743](/Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:1743), [HistoryCore.tsx:40](/Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/HistoryCore.tsx:40)).

8. **LOOPS.** Ungated starts: plugin-job queue, Workbench conductor, scheduled-recording conductor ([web_runtime.py:529](/Users/karol/dev/tools/HoldSpeak/holdspeak/web_runtime.py:529), [web_server.py:1264](/Users/karol/dev/tools/HoldSpeak/holdspeak/web_server.py:1264)). They can write plugin results, automation state, and schedules/recordings. Live workbenches, schedules, plugin jobs, reactions and watches currently all count **0**; capability to write is not evidence that these loops presently have work. Minimal gate: reuse the existing owner-lock predicate at start/tick ([intel_queue_conductor.py:72](/Users/karol/dev/tools/HoldSpeak/holdspeak/intel_queue_conductor.py:72)); no roster UI.

9. **MODEL.** Live config says `intel_provider="cloud"`, `intel_cloud_model="gpt-5-mini"`, `intel_cloud_base_url=null`, `intel_profile_id="legacy-intel"` ([config.json:28](/Users/karol/.config/holdspeak/config.json:28), [:42](/Users/karol/.config/holdspeak/config.json:42)). Its local Gemma file is not the selected cloud engine. The retired `legacy-intel` profile names **`https://api.openai.com/v1` / `gpt-5-mini`**; `.43:8080` belongs to the retired LAN Qwen profile. Therefore: **currently unresolved; expected host after restoring the configured cloud choice is `api.openai.com`, not `192.168.1.43`.**

**REPAIRS THE PATH NEEDS**

- **S:** Provision one compatible engine and the exact summary assignment through existing owner verbs.
- **M:** Preserve speech-only recording; condition live-intel routes and Stop handoff on requested intelligence. Keep speech-parent fencing.
- **M:** Before Run, project the same SERVICE route resolver ([route_plan_service.py:242](/Users/karol/dev/tools/HoldSpeak/holdspeak/services/inference_route_plan_service.py:242)); bind execution to the disclosed selection, reject drift, persist actual execution host(s). Unresolved means unavailable, never local.
- **S:** Correct Chair’s meeting scope.
- **S, conditional:** Gate any unrelated boot writer that cannot remain inactive during the sitting. Starting with valid ownership and no unrelated work needs no new orchestration system.

**OFF-PATH**

None of the six listed reds directly tests meeting-summary persistence. Four concern Ask custody/restart or chat guardrails; CI isolation concerns the verification harness. The legacy-dictation warm-reuse test touches shared transcription code and must be resolved as the stated **dictation regression obligation**, without assuming its CI failure proves this meeting path broken ([test:105](/Users/karol/dev/tools/HoldSpeak/tests/unit/test_transcriber_init_race.py:105)).

Park Room linking, connectors, watches, model-screen consolidation, retired-data repair, worktree cleanup and storage redesign.

**UNKNOWN**

No tests, capture, inference, HTTP calls or restart were performed. Audio/transcription success, model readiness, summary usefulness, actual fallback egress and observed retrieval remain unverified. Nothing was changed.