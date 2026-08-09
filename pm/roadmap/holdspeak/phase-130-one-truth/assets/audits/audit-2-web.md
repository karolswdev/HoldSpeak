# Audit 2 — Web duplicate-writer / misleading-control claims (issue #450), verified 2026-08-08

**1. Profile + InferenceTarget = two client contracts — DRIFTED-BUT-REAL (half fixed)**
Duplicate-WRITER part STALE: `holdspeak/web/routes/primitives/profiles.py:65-92` makes POST/PUT/DELETE `/api/profiles` return 405 (`_profiles_read_only`, HS-112-01); `/api/inference-targets` is the one write path. Duplicate-READ-contract part CONFIRMED: `web/src/pages/cores/settingsModels.tsx:104-135` fetches `/api/inference-targets` (106-108) AND `/api/profiles` (114-116), merging by id to fill `base_url`/`node`/`kind` — its own comment admits "The endpoint/node columns live on the profile shape." The `InferenceTarget` DTO (holdspeak/inference_targets.py:82-116) omits `base_url`/`node` yet carries a `profile_alias` block pointing back at `ProfileRecord` (db/models/__init__.py:689-721); the client holds both shapes to render one editable row.

**2. Two editors both write recipe `profile_id` — CONFIRMED (duplicate surfaces, one path)**
`web/src/desk/pullouts/editors/RecipeEditor.tsx:104-113` ("Runs on" CycleGadget → debounced recipe PUT) and `web/src/desk/infoContract.ts:71-94` (`recipe.runs_on` set → `updatePrimitive`) rendered by `InfoWindow.tsx:200-219`. Same PUT, but two writable controls with DIVERGENT empty-value semantics: RecipeEditor labels `""` "Default Runs on"; InfoWindow labels the same `""` "This device" and writes `null` where RecipeEditor writes `""`. Neither reflects the other's live edit (local state seeded once).

**3. Workbench execution ignores the Agent default — CONFIRMED**
`workbench_conductor.py:453`: `resolve_inference_target(db, wb.profile_id or "this_machine")`. The recipe is loaded at :448 and `recipes.profile_id` exists (schema.py:958) but is never consulted; fallback jumps past the Agent's "Runs on" to `this_machine`. Same pattern in `holdspeak/services/workbench_service.py:132`. An Agent configured for a private endpoint silently runs locally whenever the Workbench profile_id is null.

**4. Workbench skills UI mutates the Agent globally — CONFIRMED**
`WorkbenchWindow.tsx:385-470` renders a SKILLS section in the Workbench config wing with Attach/Remove/Approve/Dismiss. Writers at :1054-1093 call `updateSkill(skillId, {recipe_ids})` (api.ts:760-769, PUT /api/skills/{id}) — the RECIPE's global binding list, not workbench-scoped. Source list is global (`fetchSkills()` unfiltered, api.ts:701-704). Approve/Dismiss flip global skill status. Every edit changes the Agent everywhere while presented as this Workbench's configuration.

**5. Workbench creation can create two records — CONFIRMED**
`dataSlice.ts:150,163-188`: `createPrimitive("workbench")` POSTs `/api/workbenches` `{name:"New Workbench"}` then `openWorkbenchWindow(createdId)`. The blank workbench triggers the template picker (WorkbenchWindow.tsx:1387-1388); BOTH picker exits create another record — `instantiate()` POSTs `/api/workbench-templates/{id}/instantiate` (WorkbenchTemplatePicker.tsx:46-55), `createBlank()` POSTs `/api/workbenches` again (:69-76). First blank workbench is orphaned. Entry points: verbRegistry.ts:225, WorkbenchesHomeCore.tsx:65.

**6. Voice `set agent` with no handler — CONFIRMED, worse than claimed**
`web/src/desk/voice/grammars/workbench.ts:44-53` declares `set-agent`; the proposal switch at WorkbenchWindow.tsx:1170-1221 handles only add-item/run/clear-done/set-schedule; execution falls through to `setVoiceProposal(null)` — proposal appears accepted, nothing happens. ADDITIONALLY the `dismiss` intent (workbench.ts:34-43) is likewise unhandled — same silent no-op, not in the issue.

**7. Voice Commands enablement writable in two places — CONFIRMED**
SettingsCore.tsx:495-499 (`check(["dictation","macros","enabled"], "Voice commands")`) and CommandsCore.tsx:113-118 (`CheckGadget "Commands enabled"` → `persist(items,next)` :60-70 PUTting `/api/settings`). Two writers, one setting, three names. The Commands writer always resends the full `items` array from its own snapshot — clobbers macro edits made elsewhere since load.

**8. Dictation pipeline enablement writable in two places — CONFIRMED**
SettingsCore.tsx:459 and `web/src/pages/cores/dictation/Readiness.tsx:42-53,87-92` (`togglePipeline` PUT `{dictation:{pipeline:{enabled}}}`). Same key, two surfaces, no shared state — a Settings tab left open shows the stale value.

**9. "Run elsewhere" recovery persists the global dictation target — CONFIRMED**
`useSpeakDeck.ts:263-276`: `runElsewhere(id)` PUTs `/api/settings` `{dictation:{runtime:{profile_id: ...}}}` then `run()`. Triggering control is the plain RunsOnPicker in the failure banner (UtteranceWell.tsx:101-107) with no hint of permanence. A one-off retry silently rewrites the standing dictation destination — same key settingsModels.tsx:413 edits as a durable preference; providers.py:380-400 treats it as the explicit "run it there".

**10. Meeting Provider vs "Meetings Runs on" — MISREAD (real coupling gap remains)**
The duplicate-control framing is wrong; already remediated: SettingsCore.tsx:626-633 has no Runs-on control — it renders "RUNS ON LIVES IN MODELS" + Open Models button (HS-112-01). One writer: settingsModels.tsx:414. The fields are different decisions per providers.py:359-377 (`intel_provider` picks local/auto/cloud; `intel_profile_id` shapes only the cloud leg). Residual REAL problem: with `intel_provider` defaulting to "local" (config/meeting.py:33), picking a "Meetings" destination under Models has NO effect, and neither surface says so — misleading control, not duplicate writer.

## Auditor-found (not in issue #450)

- A. Unhandled `dismiss` voice intent — workbench.ts:34-43 vs switch at WorkbenchWindow.tsx:1170-1221.
- B. Divergent empty-value semantics for recipe "Runs on" — RecipeEditor.tsx:107 (`""` = "Default Runs on") vs infoContract.ts:80,90 (`""` labeled "This device", writes `null`); backend picks a third reading (`this_machine`, ignoring the recipe — see claim 3).
- C. Workbench "Runs on" default cosmetic-only — WorkbenchWindow.tsx:322 displays `detail.profile_id || "this_machine"` while WorkbenchTemplatePicker.tsx:52,74 maps the sentinel back to `null` on create; stored and displayed value never the same token.
- D. `CommandsCore.persist` full-array write — CommandsCore.tsx:60-70 sends `items` on every toggle; the enablement checkbox silently writes possibly-stale macro content.
- E. Settings writes are unmerged last-writer-wins — Readiness.tsx:45-48, useSpeakDeck.ts:265-273, CommandsCore.tsx:63-67, and the Prefs debounced update() all PUT `/api/settings` independently with partial trees and no version/etag; any two open surfaces race on the same document.
