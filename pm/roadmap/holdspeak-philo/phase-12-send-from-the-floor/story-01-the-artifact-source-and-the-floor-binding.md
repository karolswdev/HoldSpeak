# PHILO-12-01 - The artifact source and the Floor binding

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** backlog
- **Depends on:** the owner's ratification; Phase 11's merges (story 06 part 2, story 07)
- **Unblocks:** PHILO-12-03, PHILO-12-04, PHILO-12-05
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/backend.md` findings 1, 2, 3; `faces.md` F5, F8, F11
- **Design:** `design/floor-send.md` sections 2, 4, 5 (the projection as data) (binding)
- **Canvas:** none (stories 02–04 own the faces)

## Problem

An artifact is stored text (`holdspeak/db/schema.py:342`), but `render_document(db, "artifact:<id>")` refuses `document_kind_unknown` (backend §1; `holdspeak/services/document_sources.py:435-444` lists eight kinds). Meeting synthesis appends raw window and run ids to the body (`holdspeak/plugins/synthesis.py:680-683`). A Floor icon id does not name a document: project versus update, three meeting forms, the brief's stored id (backend finding 1). The Floor's world types accept primitives only (`web/src/desk/world.ts:11`).

## Scope

- **In:** `_ArtifactSource` and its `DOCUMENT_SOURCES` row (design §4): the stored `body_markdown` by id; the synthesis source footer left out (that known footer only); the label from `artifact_type` with no id; `artifact_body_missing` and `artifact_not_text` (the raw stored value, before the DTO coerces it), added to the descriptor refusal list and the shared face words; `payload_too_large:<channel>` reused; the descriptor kind list (`holdspeak/channel_operations.py:24`) and the registry fence (`tests/unit/test_philo11_document_sources.py:34`) at nine. The Floor binding (design §2): one new, pure web module that maps a Floor object or projection to its `document_ref` or a named refusal (no summary, no published update, a parked destination), and the projection variant for non-primitive icons (destinations, the brief) as data, with web-unit fences. The `send` capability in `primitiveCan` for `decision`, `meeting`, `project`, `artifact`.
- **Out:** any face, and the wiring into `world.ts`, `sceneModel.ts`, `engine.ts`, `dropMatrix.ts`, `floorMenu.ts` (stories 03, 04); binary support, attachments, truncation; a revision store or a review gate for artifacts.

## Acceptance criteria

- [ ] `artifact:<id>` renders the stored body by id through each real producer the Floor shows (meeting synthesis, run output, Ask Keep), with no model run; red on main (`document_kind_unknown`).
- [ ] `document_not_found`, `artifact_body_missing`, `artifact_not_text` (a raw non-text stored value) and `payload_too_large:<channel>` refuse by name; each fence red before the fix.
- [ ] No synthesis source footer and no internal id in an artifact payload, title, label or file name; the Phase 11 no-internal-id fence runs over nine kinds.
- [ ] The Phase 10 lifecycle fences (preview equals payload, one winner, owner press, `preview_changed`) run over one artifact. A thread prepares an artifact send; an external agent's `channel.send` is refused `owner_principal_required` with a receipt.
- [ ] A `tools/list` fence maps "send this artifact to <destination>" and "prepare it" to a tool and an argument path.
- [ ] The binding module answers every row of design §2 and each named refusal, one web-unit case each; the projection variant carries destinations and the brief without a new `PrimitiveKind`.

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days.

## Test plan

- **Integration:** fences through the real hub on an isolated HOME; each artifact minted through its real producer.
- **Web unit:** the binding module and the projection variant.
- **Rig:** `op` steps for preview and prepare on `artifact:<id>`.

## Notes

- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
