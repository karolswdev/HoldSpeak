# PHILO Phase 12 grounding — backend half

**Status: DRAFT — UNCHECKED — awaiting Muad'Dib.** Grounding only. This is not a ratified design or permission to build.

**Date:** 2026-09-30 (America/Denver; run records use 2026-10-01 UTC). **Base:** `22c0acc40c7d49c2428f177301fdd9d195f80374`. **Owner:** Astra. **Checker:** Muad'Dib, pending. **Worktree:** `/Users/karol/dev/tools/wt-philo-12-ground-astra`. **Branch:** `docs/philo-12-ground-astra`.

The owner's question: “How do we now take advantage of all of this not only on the 'wall' (or whatever that black interface is), but also through the native desk os thing, right? the icons and so on?” His selected surface is **the web Desk's Floor**. Scope is **what is sendable today**, plus **Artifacts** and a **Brief icon**. Notes were not picked. His standing rules are **“You, every time”**, saved destinations, **“I'm the only user”**, **“Stop being so paranoid”**, and **“if it changes, we re-send.”** No migration is proposed.

**Tuesday:** the useful job is to drop an existing document on a saved destination, see that document's exact preview in place, then press Send. The backend already supports this pair. The missing work is a small Floor projection and drop/open path, plus one artifact renderer. A new send operation, a new publishing workflow, or a full Brief primitive would add cost before the owner's first use (Tenets 1, 2, 3, 5, 6 and 7).

This lane changes only this report and `probes/`. The companion face grounding belongs to Muad'Dib. Probes used isolated homes and databases. No external send was made. Existing tests may write through the file channel inside their temporary fixtures; the new destination probe only previews, prepares, parks, and observes an agent's refused Send.

## 1. Artifacts are already stored text documents

The primitive kind is **`artifact`**, not the subtype in `artifact_type`. Its descriptor is non-authorable, content-synced, and opens a pullout (`web/src/lib/primitives.ts:460`). The wire adapter reads title, `artifact_type`, and `body_markdown` into the existing artifact object (`web/src/desk/api.ts:540`). Its descriptor's meeting-only blurb is narrower than storage: artifacts can come from meetings or runs.

| Fact | Source at the base | Implication |
|---|---|---|
| `artifacts` holds `id`, nullable `meeting_id`, `origin`, `artifact_type`, title, `body_markdown TEXT`, `structured_json`, status, producer/run IDs and dates | `holdspeak/db/schema.py:342` | There is a durable body. This is not an arbitrary filesystem attachment or model-weight artifact. |
| `artifact_sources` holds typed lineage | `holdspeak/db/schema.py:371` | Lineage need not be sent as raw internal IDs. |
| Canonical repository insert/upsert stores the body and updates it on an ID conflict | `holdspeak/db/plugins.py:681`, `:708`, `:744` | Stable means stored and repeatably readable, not immutable forever. |
| Meeting plugin synthesis renders and persists drafts through that repository | `holdspeak/plugins/synthesis.py:745`, `:779` | Requirements, decisions, diagrams and other synthesized outputs already have a Markdown representation. |
| Recipe/chain/workflow output helper stores `run_output` with no meeting anchor | `holdspeak/services/support.py:80` | Run artifacts use the same body, not a second document store. |
| Ask Keep and Thread Keep store the retained text | `holdspeak/services/ask_service.py:485`; `holdspeak/services/thread_service.py:1775` | Kept answers are also artifact documents. Thread Keep refuses absent text. |
| Receipt-gated projections also write this table | `holdspeak/kernel/meeting_plugin_projection.py:96`; `holdspeak/kernel/recipe_projection.py:16`; `holdspeak/kernel/rails_journal_projection.py:14`, `:34`, `:60`; `holdspeak/kernel/sequence_workflow_projection.py:52`; `holdspeak/kernel/workbench_projection.py:34` | These paths bypass `record_artifact`. A renderer must read the stored row, not re-run its producer. |
| Decision promotion and sync also persist artifacts | `holdspeak/db/decisions.py:520`; `holdspeak/services/sync_service.py:483` | The producer set is wider than meeting synthesis; a narrow fixture is not an exhaustive producer proof. |
| The repository reads the saved artifact and sources by ID | `holdspeak/db/plugins.py:828`, `:913` | The source can use `db.plugins.get_artifact(source_id)`. |

The real synthesis and run-output probes stored and re-read bodies; repeated reads of the synthesis body were equal. **Current `render_document(db, "artifact:<id>")` refuses `document_kind_unknown`.** Both facts are in [artifacts.out.txt](probes/artifacts.out.txt), produced by [artifacts.py.txt](probes/artifacts.py.txt). The synthesis probe starts from a stored plugin result; it proves synthesis and persistence, not model inference.

**Smallest proposed addition:** implement `_ArtifactSource.render(db, source_id)` in `holdspeak/services/document_sources.py`, then add the `artifact` row to `DOCUMENT_SOURCES` (`:437`). Read one stored artifact, return the existing `Document(ref, title, body_md, slug, label)` interface (`holdspeak/services/channel_contract.py:80`, `:93`), and use a source-owned safe filename/label. `channel_contract.render_document` already delegates to the registry (`:247`). Preview, Prepare, inline Send and frozen prepared sends already use that contract (`holdspeak/services/channel_service.py:159`, `:400`, `:488`). No channel-specific artifact transport, table, version store, or migration is needed.

The current test pins the eight-entry registry (`tests/unit/test_philo11_document_sources.py:34`), and the wire description lists those kinds (`holdspeak/channel_operations.py:24`). Change that description and fence with the ninth source, not in a later cleanup. Exercise the real artifact producers through Preview/Prepare, then the existing isolated file-channel test path; pin missing body, non-text and oversize refusals before claiming them fixed. The existing `artifact:<id>` refusal in this probe is the current unsupported behavior, not a completed implementation fence.

Use the existing `body_markdown` as the content; do not regenerate the report from `structured_json`, invoke a model, attach an arbitrary file, or copy the pullout's rendered HTML. A Mermaid/code block in a stored Markdown body is text. **One content defect is already visible:** synthesis appends internal window and plugin-run IDs (`holdspeak/plugins/synthesis.py:680`), including in the real probe output. Phase 11 explicitly renders recognizable provenance instead of internal IDs (`holdspeak/services/document_sources.py:105`). Recommended artifact rendering omits only the known producer-owned provenance footer, identified against stored lineage, and leaves the authored report intact. This is a deterministic presentation rule to settle with Muad'Dib, not a general text scrubber or a migration. It needs a real synthesis-output fence; the artifact body is not automatically recipient-ready merely because it is stored Markdown.

Keep the existing changed-preview behavior and prepared-byte snapshot. Do not add a source revision system: if the body changes, preview it again and the owner sends again. An artifact's draft/review status is not the project update's publish lifecycle; a new artifact publish gate is not justified by this request. Preserve the current Floor population: run listings already hide `pending-review` and `rejected` (`holdspeak/db/plugins.py:931`), while a direct ID lookup does not (`:828`). Do not expose those hidden items just to make icons. The owner's explicit preview and Send remain the approval; this grounding does not propose a second artifact review ceremony.

**Non-text is a named refusal, not a conversion feature.** Proposed source refusals are `document_not_found` for an absent ID, `artifact_body_missing` for an empty/whitespace body, and `artifact_not_text` for binary or non-text material. Name the artifact in the short detail. These last two codes are proposals, not current behavior; add them to the descriptor refusal list and the shared face vocabulary together. No attachment upload, OCR, binary decoding, or silent truncation.

The existing store has no MIME/attachment discriminator. It coerces input with `str(body_markdown or "")` (`holdspeak/db/plugins.py:708`), and the read DTO coerces it again (`:862`). The probe demonstrates that a Python `bytes` argument becomes the text `b'\\x00\\xff\\x80'`; a lone surrogate fails at storage with `UnicodeEncodeError`. The probe's hand-built `Document` serialization is **not** proof of registered artifact support. A renderer cannot recover lost type information from a historical string. Keep the change small: accept actual stored text bodies and refuse known non-text/missing bodies at the source. Check the raw stored value before DTO coercion when enforcing a binary refusal; an `isinstance` check after `get_artifact` cannot prove that boundary. Reject non-string values at any producer seam touched by this work, before coercion. Do not promise binary classification that the current record cannot support or add a migration to infer it.

Existing size limits apply to the **serialized channel payload**, not just the artifact body. They already refuse `payload_too_large:<channel>` before dispatch (`holdspeak/services/channel_service.py:393`).

| Channel | Checked-in limit | Evidence |
|---|---|---|
| File | 10 MiB, UTF-8 payload bytes | `holdspeak/services/channel_contract.py:40` |
| GitHub | 65,536 serialized characters | `holdspeak/services/channel_contract.py:42`, `:53` |
| Jira | 32,767 serialized characters | `holdspeak/services/channel_contract.py:43`, `:53` |
| Confluence | 1,000,000 serialized bytes | `holdspeak/services/channel_contract.py:44` |
| Slack | 39,000 characters in the serialized JSON `text` field | `holdspeak/services/channel_contract.py:47`, `:56` |
| Email | 1,000,000 request bytes; SendGrid 20 recipients, Resend 50 | `holdspeak/services/channel_email.py:175`, `:263`, `:689`, `:698` |

These are local code limits, not a fresh audit of provider policies. GitHub/Jira and the email comments carry provisional limits. The artifact table/repository has no explicit body-size cap; reuse channel limits rather than invent a new arbitrary artifact cap.

## 2. A Brief icon without a new primitive

`PrimitiveKind` has 20 entries and no Brief (`web/src/lib/primitives.ts:28`). Brief rows already exist in `monday_briefs`/`monday_brief_items` (`holdspeak/db/schema.py:2464`). `GET /api/brief/latest` returns the current stored brief or null (`holdspeak/web/routes/monday_brief.py:112`). `BriefView` consumes that read and already composes the common Send wells (`web/src/desk/pullouts/views/BriefView.tsx:158`, `:461`). The existing document identity is **`monday_brief:<stored brief id>`** (`web/src/desk/documentSends.tsx:27`); its renderer reads the stored row (`holdspeak/services/document_sources.py:247`).

The smallest honest proposal is **one Floor affordance for the existing Intelligence → Brief capability**. Give its layout a stable key such as `intelligence:brief`, display the existing Brief view on open, and bind drag/preview to the actual stored brief ID. The icon's position identity and the document's send identity have different jobs. If no brief exists, opening can show the existing Generate flow; dropping must not generate or send a fictitious brief. A refresh must not silently switch the document in an already open preview.

This is not supported merely by filling a new bucket. `WorldObject.kind` and `.ref` currently require a primitive (`web/src/desk/world.ts:11`); world iteration is exhaustive over those kinds (`:30`), and Intelligence is visually excluded (`:19`). Add an explicit Floor projection/action variant that delegates to existing capability surfaces, rather than casting Brief to `Primitive` or silently adding a 21st kind. The same narrow presentation seam can cover destination and published-update icons. This is an affordance on existing capabilities under Constitution II.3, not an independent capability/lifecycle; Muad'Dib must check that interpretation with the faces.

| Choice | Actual work | Recommendation |
|---|---|---|
| Floor-only Brief projection | Read current Brief, stable local position key, explicit open/drag binding, shared icon/rendering and SendWell composition | Preferred for this job. No new primitive kind or DB schema. |
| Full Brief primitive | Extend `PrimitiveKind`, `Primitive`, descriptor table, `Items`, loaders/normalizers, world order, pullout registry and cross-surface contracts; decide its verbs and sync meaning | Existing Brief tables could still back it; a schema change is not inherently required. The extra API/type/lifecycle work earns its cost only if the owner needs Briefs as general Desk content beyond this Floor affordance. |

The exhaustive contracts are at `web/src/lib/primitives.ts:421`, `:448`; `web/src/desk/api.ts:51`; `web/src/desk/world.ts:49`; `web/src/desk/pullouts/registry.ts:21`. The existing local Intelligence descriptor already names the Brief (`web/src/lib/primitives.ts:628`). No migration or primitive promotion is needed to display a readable icon.

## 3. Saved destinations on the Floor

Use the existing **`channel.destinations`** read (`holdspeak/channel_operations.py:35`), exposed as `GET /api/channels/destinations` and MCP. Its service returns the saved identity, name, channel, account/target, state and badge (`holdspeak/services/channel_service.py:74`, `:143`). Connection information is a stored read, not a remote probe (`:86`). Drawing these icons adds no send authority and needs no new operation.

The default read selects only `state='active'` (`holdspeak/db/channels.py:100`). Keep `include_parked` off for the Floor. Remove parks a row; editing parks the old target and creates a new saved identity (`holdspeak/db/channels.py:3`; `holdspeak/services/channel_service.py:343`). A parked destination must disappear on refresh, while its send history remains. A stale drop gets `destination_parked` from preview, or `destination_not_saved` for an unknown ID (`holdspeak/services/channel_service.py:134`, `:159`). Do not infer active destinations from retained layout keys.

**Position storage already exists:** `hs.diorama.pos` in browser local storage is a string-keyed `{x,y}` map (`web/src/desk/store/dataSlice.ts:32`). `setPosition` updates it in memory; `persistPositions` saves it (`:825`). `objUnit` reads `positions[o.id]` (`web/src/desk/world.ts:159`). It is per browser/origin, not hub DB or cross-device placement, and unavailable local storage means arrangement does not persist (`dataSlice.ts:43`).

Use namespaced keys for the new projection, such as `destination:<saved id>`. Do not rewrite existing positions or add a table. Keep the parked icon's old position harmlessly dormant; a replacement destination has a new ID. Position storage does not itself create an icon: `Items`, `worldObjects`, the scene model and `WorldStage` currently have no destination input (`web/src/desk/api.ts:51`; `web/src/desk/world.ts:63`; `web/src/desk/gl/sceneModel.ts:123`; `web/src/desk/gl/WorldStage.tsx:34`). The new projection must read active rows and use the shared Floor rendering/drag path. Refresh on the existing destination-change/focus hooks (`web/src/desk/surface/send/SendWell.tsx:130`).

The isolated HTTP/MCP probe recorded an empty default destination list after parking, the parked row when explicitly requested, and no output file: [destinations_wire_probe.out.txt](probes/destinations_wire_probe.out.txt). It uses the real app/registry via in-process `TestClient`, not a live external endpoint.

## 4. The drag-to-preview wire

**No new backend operation is needed.** Resolve the dragged document identity, retain the saved destination ID, then call:

```text
channel.preview({document_ref, destination_id})
  -> show its preview + destination + egress badge in the existing Send well
  -> only on the owner's Send press:
channel.send({document_ref, destination_id, preview_digest, command_id})
```

The web adapter already takes that pair (`web/src/features/channels/channels.ts:561`). The Send well already reads a preview for its selected document/destination (`web/src/desk/surface/send/SendWell.tsx:453`) and its press submits the preview digest (`:537`). What is missing is a Floor drop/open action and an explicit way to select the dropped destination in this component; its current destination selection is private module state. Reuse this component rather than render another preview/receipt system.

The current WebGL drag-to-DOM seam dispatches `{id, kind}` to a marked grounding target (`web/src/desk/gl/engine.ts:1084`; `web/src/desk/components/GroundingSection.tsx:115`). A destination **icon in the scene** is not that DOM target. There is already an icon-to-icon rule table: `DROP_MATRIX` names `ground-into` and `file-knowledge` (`web/src/desk/dropMatrix.ts:9`, `:22`), and the engine dispatches those actions on release (`web/src/desk/gl/engine.ts:1106`). Extend that shared rule/action seam for preview and the new Floor projection; do not build another drag engine. Returning the source icon to its starting place after an accepted drop is an existing precedent (`engine.ts:1123`); dropping must not file/move the document into a destination or imply delivery. Muad'Dib owns its visible design.

| Icon/source | Exact `document_ref` | Availability / identity rule |
|---|---|---|
| Existing Desk decision primitive | `desk_decision:<decision id>` | Use the decision object's own ID; existing constructor at `web/src/desk/documentSends.tsx:32`. |
| Decision record projected onto the Floor | `decision_record:<record id>` | Intelligence/Room decision rows use this kind, including rows labelled `source="meeting"`; do not turn that label into `meeting_decision` (`documentSends.tsx:10`, `:36`). |
| Legacy meeting decision, if explicitly represented | `meeting_decision:<meeting_decision id>` | Supported by the backend source at `holdspeak/services/document_sources.py:310`; no generic Floor mapping follows from a meeting ID. |
| Meeting | `meeting_summary:<meeting id>`, `meeting_digest:<meeting id>`, or `meeting_followup:<meeting id>` | Explicit selected form; never the transcript. The three renderers are at `document_sources.py:387`, `:412`. |
| Published project update document | `project_update:<update id>` | A project ID is not an update ID. Bind an exact stored published update; renderer refuses `not_published` otherwise (`channel_contract.py:221`). Current constructor: `web/src/features/channels/SendWell.tsx:21`. |
| Brief Floor affordance | `monday_brief:<brief id>` | Resolve the displayed stored Brief, not the stable layout key or the string `latest`. |
| Artifact | `artifact:<artifact id>` | Proposed new source in §1; currently `document_kind_unknown`. |

The ordinary project icon should open its existing update choice, or a distinct published-update document projection should carry the exact ID. It must not silently send “the project.” Other Floor primitives are not made sendable by guessing a document prefix. Notes remain out of this phase.

**Meeting choice:** the existing `MeetingSendWell` starts at Summary and offers Summary / Digest / Follow-up in its inline CycleGadget. Its last selection is a private module map keyed by meeting ID, not persisted or carried by drag (`web/src/meetings/MeetingSendWell.tsx:18`, `:25`, `:34`). Recommended drop behavior is to open that picker with **Summary selected**, destination retained, and its Summary preview already loaded. Changing the form refreshes the preview for the same destination. This avoids guessing a hidden remembered form. Do not fall back from a refused form to a different document without an explicit choice; missing summary gets `no_summary` (`document_sources.py:44`, `:395`). Owner fork 2 below remains open.

### Kernel and receipt boundary

| Action | Admission and authority | Receipt consequence |
|---|---|---|
| Destination read / icon drawing | Existing authenticated read; `channel.destinations` is exempt (`channel_operations.py:35`, `:55`) | No new admission or terminal receipt. |
| `channel.preview` | Authenticated read/computation; explicitly XI.5-exempt (`channel_operations.py:180`, `:200`) | No kernel operation/receipt. Show the preview or a named refusal; never label it Sent. |
| `channel.prepare`, if used | Admitted local write (`channel_operations.py:203`, `:222`) | Freezes document, destination and transport bytes in `channel_sends`; terminal receipt and row are written together (`channel_service.py:400`, `:419`, `:429`). It is not covered by the preview exemption. |
| `channel.send` | Admitted, `owner_press=True` (`channel_operations.py:250`, `:292`); MCP authority is EGRESS (`holdspeak/mcp/tool_authority.py:272`) | Existing terminal success/failure/unknown/refusal receipt and send record. An agent may prepare but cannot acquire the owner's Send right. |

**Prepare is optional for an owner drop.** Recommend preview only: it adds no waiting send row each time the owner explores a destination. If a later design deliberately needs a durable prepared send, use the existing Prepare operation and display the frozen preview returned by that prepared row; do not show an earlier preview while sending newly prepared bytes. Preview/Prepare are WORK in the MCP authority table; Send is EGRESS (`holdspeak/mcp/tool_authority.py:265`). XI.5 still requires authenticated read authority (`docs/internal/CONSTITUTION.md:189`).

The probe observed zero new kernel operations for Preview; Prepare created a `succeeded` operation and receipt plus a `prepared` row with the same payload digest; an external agent's Send was refused as `owner_principal_required`, with a refusal receipt and the send row still `prepared`. No file was written. See [source](probes/destinations_wire_probe.py.txt) and [output](probes/destinations_wire_probe.out.txt). The agent attempt was made after parking, so it proves the observed owner-principal refusal, not every possible refusal ordering.

Keep the shared receipt visible across the destination's open/closed and document-form transitions. The existing Send well owns that history/receipt behavior; a new Floor wrapper must not unmount the only receipt when Send changes the branch. This needs a rendered transition fence in the eventual build, not a helper-only assertion.

## 5. Findings, ranked by cost to the owner

1. **A generic icon ID does not identify the document to send.** Project versus update, three meeting forms, and two decision representations require explicit refs (§4). Guessing could show/send the wrong report. **Tenets 3 and 7.** Proposed home: Phase 12 Floor document binding and rendered drop-to-preview fences.
2. **The current Floor cannot render Brief or destination records as-is.** Its world and scene types assume primitives (§§2–3). Claiming this is only “add an icon” hides real integration work; promoting everything to a primitive over-expands it. **Tenets 1, 2, 5 and 6.** Proposed home: one Floor projection/action seam with stable local keys.
3. **Artifact storage is usable; the channel source is absent.** The missing work is one renderer/registry entry plus readable provenance and truthful missing/non-text/size refusals (§1). Binary provenance lost by string coercion cannot be recovered by a renderer. **Tenets 1, 3, 4 and 7.** Proposed home: Phase 12 artifact document source; test real producer output and named refusal boundaries.
4. **Auto-Prepare would leave durable rows for exploratory drops.** Preview already does the requested job (§4). A second send path or a “confirm the preview” gate adds ceremony. **Tenets 1 and 3.** Proposed home: reuse the shared Send well, preview on drop, owner Send every time.

### Open forks for the owner

1. **Should one Brief icon follow the latest saved Brief, or should each generated Brief have an icon?** Recommended: one Brief icon with a stable position; bind the displayed stored ID when preview opens. No automatic generation on drop.
2. **Which meeting form should a drop show first?** Recommended: Summary, with the existing Summary / Digest / Follow-up picker visible in the same preview and the dropped destination retained.

Artifact text-only support, active saved destinations, and the owner pressing Send are already scope/rulings, not questions to ask again. The suggested default is to show active saved destinations without a second pin-management screen. Canvas, layout, opening surfaces, and the narrow-screen alternative to drag remain in Muad'Dib's face lane.

## Verification and ledger

The worker source census is in [brief_floor_audit.txt](probes/brief_floor_audit.txt). All source anchors describe the base above; recheck them before implementation. No product source, schema, story status, or canon was changed, so there is no branch-new product behavior and no story flip.

- Focused backend: [collection](probes/verify_scoped.collect.out.txt) lists 83 tests; [run](probes/verify_scoped.out.txt) reports **83 passed**. The five files cover Phase 11 sources/contract, Phase 10 send lifecycle, artifact synthesis persistence, and run artifacts. [Reproduction](probes/verify_scoped.sh.txt).
- Focused Floor: [collection](probes/brief_floor_vitest_list.txt) and [run](probes/brief_floor_vitest_run.txt) report **37 passed in 3 files**. These exercise existing world math, scene geometry/hit tests and Floor menus; they do not prove the proposed projection exists.
- Quiet full suite: **13,574 passed, 2 failed, 117 skipped, 4 xfailed**, exit 1, in 3,629.77 seconds. [Full output](probes/verify_full.out.txt), [reproduction](probes/verify_full.sh.txt). `tests/e2e/test_metal.py` was excluded. No worker edited during the run; product/test sources remained at the base. This is a red full-suite result, not a green claim.
- Real atlas case `case.j10.arrival_generate_brief.generated_empty` passed at 1440 and 393, one invocation/home per case, engine `none`, on the actual atlas. [Reproduction](probes/verify_walk.sh.txt), [1440 log](probes/walk-1440.out.txt), [393 log](probes/walk-393.out.txt). I read the observations and all four images: “No brief yet” becomes “No changes”; the returned stored Brief ID and visible “Brief ready” agree with a generated empty Brief. Initial feedback and terminal outcome were both observed; terminal settled in about 1.1 seconds. This does not establish a sub-500ms feedback bar.
- [1440 observation](probes/walk-1440/20261001T003822Z-case.j10.arrival_generate_brief.generated_empty-astra-1440/observation.json), [before](probes/walk-1440/20261001T003822Z-case.j10.arrival_generate_brief.generated_empty-astra-1440/before.png), [after](probes/walk-1440/20261001T003822Z-case.j10.arrival_generate_brief.generated_empty-astra-1440/after.png).
- [393 observation](probes/walk-393/20261001T003907Z-case.j10.arrival_generate_brief.generated_empty-astra-393/observation.json), [before](probes/walk-393/20261001T003907Z-case.j10.arrival_generate_brief.generated_empty-astra-393/before.png), [after](probes/walk-393/20261001T003907Z-case.j10.arrival_generate_brief.generated_empty-astra-393/after.png).

Both observations name temporary HOME database paths, base revision `22c0acc40`, and `dirty=true` because this grounding/probe output was untracked. These are current Chair evidence only. No new Floor send interaction exists to walk yet; no owner-desk observation, external delivery, binary attachment support, or cross-device placement is claimed. The narrow-screen Floor design remains unverified here.

**Ledger:** findings 1–4 above are proposed Phase 12 work, not regressions caused by this docs lane. Verification failures are named below with their a/b/c classification and follow-up home. No chartered criterion was amended. This report remains **UNCHECKED — awaiting Muad'Dib**; no self-invoked check was obtained.

`dw doctor` is healthy. Repository-wide `dw check` reports six inherited structural errors: orphaned evidence in phase 101 story 04, and missing final summaries in phases 152, 153, 154, 156 and 200. [Raw output](probes/dw_check.out.txt). Classification **b: real inherited structural debt**, not a regression from this report; all roadmap files are unchanged from `22c0acc40`. Home: those existing phases and PMO maintenance. This docs lane does not repair unrelated roadmap records or flip a story to hide the errors.

| Full-suite failure | Reproduction and classification | Follow-up home |
|---|---|---|
| `tests/e2e/test_hs171_shade_glass.py::test_shade_brief_row_1440` | **a: inherited fixture/assertion mismatch.** The fixture uses the requested September date for period fields, but `datetime('now')` for `generated_at` (`tests/e2e/test_hs171_shade_glass.py:845`). The face correctly formats `generated_at` (`web/src/desk/components/SystemShade.tsx:138`). The assertion at `tests/e2e/test_hs171_shade_glass.py:912` accepts only `SEP` or `2026`, so the real `OCT 01` token fails. The [isolated serial rerun](probes/verify_shade_serial.out.txt) reproduces the same failure. | Phase 171 Shade glass test: seed the field the face reads, and assert that field's date. No product change or September-only workaround. |
| `tests/unit/test_thread_tool_loop.py::TestHeldApprove::test_held_then_approved` | **c: isolated full-suite flake, serial-green twice.** `_wait_done` exceeded its two-second bound (`tests/unit/test_thread_tool_loop.py:250`). [Serial run 1](probes/verify_thread_serial1.out.txt) and [serial run 2](probes/verify_thread_serial2.out.txt) both passed under fresh homes. Parallel load is a possible cause, not established. | Thread tool-loop test/runtime timing triage; retain the full-run timeout evidence. No timeout inflation or product patch in this lane. |

Both failed nodes were [collected explicitly](probes/verify_failures.collect.out.txt); [triage commands](probes/verify_failures.sh.txt) run only these nodes. `git diff --quiet 22c0acc40 -- holdspeak web tests scripts .githooks pm/roadmap` returned 0 after verification: the tested implementation, tests and roadmap are unchanged from the requested base. The failures and follow-up homes remain visible in this DRAFT instead of being fixed outside its allowed paths.
