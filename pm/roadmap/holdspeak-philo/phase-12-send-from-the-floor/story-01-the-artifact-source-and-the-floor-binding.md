# PHILO-12-01 - The artifact source and the Floor binding

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** done
- **Depends on:** the owner's ratification; Phase 11's merges (story 06 part 2, story 07)
- **Unblocks:** PHILO-12-03, PHILO-12-04, PHILO-12-05
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/backend.md` findings 1, 2, 3; `faces.md` F5, F8, F11
- **Design:** `design/floor-send.md` sections 2 (the resolved inputs), 4, 5 (the projection as data; the by-id read) (binding)
- **Canvas:** none (stories 02–04 own the faces)

## Problem

An artifact is stored text (`holdspeak/db/schema.py:342`), but `render_document(db, "artifact:<id>")` refuses `document_kind_unknown` (backend §1; `holdspeak/services/document_sources.py:435-444` lists eight kinds). Meeting synthesis appends raw window and run ids to the body (`holdspeak/plugins/synthesis.py:680-683`). A Floor icon id does not name a document: project versus update, three meeting forms, the brief's stored id (backend finding 1). The Floor's world types accept primitives only (`web/src/desk/world.ts:11`).

## Scope

- **In:** `_ArtifactSource` and its `DOCUMENT_SOURCES` row (design §4): the stored `body_markdown` by id; only the synthesis-owned source footer left out, matched against the artifact's stored lineage (`artifact_sources` `intent_window` and `plugin_run` rows), authored text and code kept; the label from `artifact_type` with no id; `artifact_body_missing` and `artifact_not_text` (the raw stored value, before the DTO coerces it), added to the descriptor refusal list and the shared face words; `payload_too_large:<channel>` reused; the descriptor kind list (`holdspeak/channel_operations.py:24`) and the registry fence (`tests/unit/test_philo11_document_sources.py:34`) at nine. `GET /api/brief/{brief_id}`, a plain authenticated read for the brief's exact-id handoff (design §5). The Floor binding (design §2): one new, pure web module over explicit **resolved inputs** (`Fact<T>`: unread, loading, failed, known) that answers a `document_ref`, a named refusal (only on a known absence: no summary, no published update, a parked destination) or `pending`; it performs no read. The projection variant for non-primitive items (destinations, the brief) as data. Web-unit fences. The `send` capability in `primitiveCan` for `decision`, `meeting`, `project`, `artifact`.
- **Out:** the reads that supply the facts (story 03); any face, and the wiring into `world.ts`, `sceneModel.ts`, `engine.ts`, `dropMatrix.ts`, `floorMenu.ts` (stories 03, 04); binary support, attachments, truncation; a revision store or a review gate for artifacts.

## Acceptance criteria

- [x] `artifact:<id>` renders the stored body by id through each real producer the Floor shows (meeting synthesis, run output, Ask Keep), with no model run; red on main (`document_kind_unknown`).
- [x] `document_not_found`, `artifact_body_missing`, `artifact_not_text` (a raw non-text stored value) and `payload_too_large:<channel>` refuse by name; each fence red before the fix.
- [x] No synthesis source footer (removed only when it matches stored lineage; an authored line that looks alike stays) and no internal id in an artifact payload, title, label or file name; the Phase 11 no-internal-id fence runs over nine kinds.
- [x] The Phase 10 lifecycle fences (preview equals payload, one winner, owner press, `preview_changed`) run over one artifact. A thread prepares an artifact send; an external agent's `channel.send` is refused `owner_principal_required` with a receipt.
- [x] A `tools/list` fence maps "send this artifact to <destination>" and "prepare it" to a tool and an argument path.
- [x] `GET /api/brief/{brief_id}` returns that stored brief, also when a later brief exists; an unknown id is a 404.
- [x] The binding module answers every row of design §2 and each named refusal, one web-unit case each; `unread`, `loading` and `failed` answer `pending`, never a refusal; the projection variant carries destinations and the brief without a new `PrimitiveKind`.

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days.

## Test plan

- **Integration:** fences through the real hub on an isolated HOME; each artifact minted through its real producer.
- **Web unit:** the binding module and the projection variant.
- **Rig:** `op` steps for preview and prepare on `artifact:<id>`.

## Notes

- 2026-09-30 — built and verified on `feat/philo-12-01`; [evidence](evidence-story-01.md), [lane record and full-suite ledger](lane-01-astra.md). Built counsel was outstanding at this point; it is recorded below.

- 2026-09-30 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-30 — built counsel r1 (`checks/story-01-built-muaddib-r1.md`) is RATIFY-WITH-CONDITIONS; C1 and C2 are paid in the Round Two lane report.
- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
