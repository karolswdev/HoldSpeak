# PHILO-11-01 - The document sources

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** done
- **Depends on:** the owner's ratification
- **Unblocks:** PHILO-11-02 (the aftercare rewrite), PHILO-11-04, PHILO-11-06, PHILO-11-07
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** `docs/internal/philo/phase-11/grounding/backend.md` F2, F3, F4, F6; `faces.md` F1, F4; rulings R1, R2, R3, R8, R9
- **Design:** `design/document-sources.md` sections 1–4 (binding)
- **Canvas:** none (stories 03–05 own the faces)

## Problem

Only a published project update can be previewed, prepared or sent. Preview and prepare call `render_update` (`holdspeak/services/channel_service.py:153`, `:349`); the descriptors require `update_id` and refuse other properties (`holdspeak/channel_operations.py:174`, `:198`); file naming reads the update again at Send (`holdspeak/services/channel_contract.py:213`; `holdspeak/services/channel_service.py:473`); the public history filters by `update_id` (`holdspeak/channel_operations.py:294`). The brief, the decisions and the meeting summaries have no renderer. A thread cannot prepare a send: `channel.prepare` is not in the chat palette (`holdspeak/services/thread_tools.py:344`).

## Scope

- **In:** the `DocumentSource` Protocol and the `DOCUMENT_SOURCES` table (design section 1); the update as the first source; the seven new sources and their refusals (section 3): `monday_brief` (whole, with person sections, R1), `desk_decision`, `meeting_decision`, `decision_record` (R2), `meeting_summary`, `meeting_digest`, `meeting_followup` (R3, never the transcript); the digest and follow-up renderers kept from `holdspeak/slack_export.py` as Markdown, the 3,800-character truncation removed; the generic descriptors (section 4): `document_ref` on preview, prepare and the inline send, the `document_ref` filter on `channel.sends`; the two client callers changed in the same commit — the wire in `web/src/features/channels/channels.ts:499-506` and the inline Send body in `web/src/features/channels/SendWell.tsx:429` (`update_id: uid` → the generic reference) — with their fences, and the Phase 10 atlas `.op` arguments (Astra r1 finding 5: nothing breaks between the merges of 01 and 04); the frozen `document_json` column (title, slug, label; section 2) and file naming from it; the kernel target mapping (`holdspeak/services/project_kernel.py:184`); `channel.destinations`, preview, prepare and sends in the chat palette (stated default D2; Astra r1 finding 3); the brief source composes the stored brief (by id, `holdspeak/services/monday_brief_service.py:1492`) with the real person overlay (`holdspeak/services/person_overlay.py:3`), every item kept and the Ack/Defer marks omitted (Astra r1 finding 4).
- **Out:** the Slack channel (02); any face (03–05); Mark delivered on new kinds (R8); a snapshot digest, a renderer version, a stale state (R9); other briefs (charter Out).

## Acceptance criteria

- [x] Each of the eight kinds renders from its stored record by id through the real producer, and refuses by name (`document_kind_unknown`, `document_not_found`, `no_summary`, `not_published`). The brief carries its person sections. No model runs at preview or Send.
- [x] A transcript sentinel never appears in the payload of `meeting_summary`, `meeting_digest` or `meeting_followup`.
- [x] Preview, prepare, the inline send and sends take `document_ref` on HTTP, MCP and the rig's `op` step, over one descriptor and one service; `update_id` is gone. The Phase 10 update send still works unchanged on the face.
- [x] The Phase 10 lifecycle fences (R1–R6 over both forms, preview equals payload, one winner, `owner_principal_required`, `preview_changed`) are green, and each runs over at least one new kind as well as the update.
- [x] A prepared send of a new kind names its file and sends its frozen bytes with the source deleted (no live read at Send). An inline Send after the source changed refuses `preview_changed`; a new preview sends the new text.
- [x] The receipt and the admission of preview, prepare and the inline send name the `document_ref`.
- [x] A thread prepares "my brief for #leads" through the thread gate with no destination id given to the test (it finds the id through `channel.destinations`).
- [x] Two boundaries, two fences: a thread's `channel.send` is refused by the palette gate ("Tool outside the admitted palette", `holdspeak/services/thread_tools.py:591`; no operation); an external agent's `channel.send` over MCP is refused `owner_principal_required` with a receipt.
- [x] The update face's inline Send (the `SendWell.tsx:429` body) and prepared Send pass their Phase 10 glass at both widths on the story 01 head.
- [x] The brief's payload carries every item (an acknowledged one included) and the person overlay's sections; no Ack or Defer mark.
- [x] `project_update_deliveries` gets rows only for updates; the new kinds' history is their ended sends.

**Criterion 6 and Constitution XI.5:** preview is effect-free computation, as it was in Phase 10. It returns `document_ref` and creates no operation or receipt. Prepare and inline Send are admitted effects; their operation targets and receipts identify `document_ref`. The higher canon governs the wording above. The existing no-preview-operation fence remains binding. This interpretation is recorded in `lane-01-astra.md` for Muad'Dib's counsel-on-built; no new preview lifecycle is introduced.

## Effort (not a promise)

PROVISIONAL: 2.5–3.5 engineering days.

## Test plan

- **Integration:** fences through the real hub on an isolated HOME; each source minted through its real producer (the brief through `MondayBriefService.generate`, the decisions through their services, the meeting through the DB layer and its stored intelligence).
- **Rig:** `op` steps for preview, prepare and sends per kind.

## Notes

- 2026-09-29 — built and verified in `feat/philo-11-01`; [lane record](lane-01-astra.md) and [captured evidence](evidence-story-01.md). Muad'Dib's counsel-on-built is pending. Criterion 6 follows Constitution XI.5 as recorded above.

- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
