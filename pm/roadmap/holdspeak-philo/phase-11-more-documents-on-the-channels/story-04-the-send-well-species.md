# PHILO-11-04 - The SEND well as one library species

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** done
- **Depends on:** PHILO-11-03 ratified (canvas E); PHILO-11-01 merged
- **Unblocks:** PHILO-11-05
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-11/grounding/faces.md` §2 (B1–B8), F3, F4
- **Design:** `design/document-sources.md` section 4 (the wire)
- **Canvas:** E (the shared well), ratified in story 03

## Problem

`web/src/features/channels/SendWell.tsx` is a feature module bound to the update at eight points (faces.md B1–B8): the `update` prop, the `update_id` wire, the `project_update:` filter, the press-store key name, `REV ${update.draftRevision}`, `DeliveryHistory` on the update controller, `ListChips` on `update.deliveries`, and the reload. On four or more faces it is a recurring element; UX-CANON §B says it goes into the library first.

## Scope

- **In:** the well takes a document reference (`{ref, title, label}`) in place of the update; B1–B8 replaced; `PreviewWell`, `ProofCell` and `useDestinations` exported or moved (faces.md §2); the history for a new kind from `channel.sends` by `document_ref` (the ended sends; F4); the update keeps its manual row and Mark delivered as a slot only it fills (R8); the Slack case in `ProofCell` (POSTED, no link); the species in the library and documented in `web/src/desk/surface/contract.md`; the update face recomposed on it with no visible change.
- **Out:** the well on the new faces (05).

## Acceptance criteria

- [x] One well component in the library, documented in `contract.md`; no face hand-rolls its rows.
- [x] The update's Phase 10 glass fences and atlas cases pass unchanged at both widths (no visible change).
- [x] A web-unit case per state for a non-update document: no destination, picked, SENT, POSTED (no link), REFUSED, FAILED, UNKNOWN, PREPARED; no manual row on a non-update.
- [x] The web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Web unit:** the species' states for the update and one new kind.
- **Glass:** the Phase 10 update fences at 1440 and 393.

## Notes

- 2026-09-30 — round four, on Astra's built-check r3 RATIFY-WITH-CONDITIONS (`checks/story-04-built-astra-r3.md`, verbatim): condition 1 paid — UNKNOWN and no-answer closed-row fences on both hosts (the update and a brief), red on `f4127c441` in a scratch export, green on the head. Condition 2 (resolve the stack after #707 and run the integration suite and gate) is owed when #707 merges.

- 2026-09-30 — round three, on Astra's built-check r2 DO-NOT-RATIFY (`checks/story-04-built-astra-r2.md`, verbatim): the receipt survives the click that leaves its row. Phase 10 at base `332d9158` kept only a summary chip on a closed row (`LastChip`: LAST SEND FAILED / LAST SEND UNKNOWN) and nothing for a refusal; the species now keeps the whole receipt at that seat on a CLOSED row (`ClosedReceipt`): FAILED → LAST SEND FAILED + its word + NOTHING SENT; REFUSED (newer than the latest send) → REFUSED + its word + NOTHING SENT; UNKNOWN → LAST SEND UNKNOWN + its word; no answer → NO ANSWER · RESULT UNKNOWN; the egress chip beside it. The seat is the ratified one: the canvas draws a destination's last result on the closed row's line 2, beside the egress chip (A3, B2, A4c; T1 draws the refusal in the open row, where it still is). An open row keeps the Phase 10 chip. SENDS stays sent and unknown rows only, as drawn. The update gets the same (it is the species); the Phase 10 glass passes at both widths. Four rendered-transition cases, red on `f4127c441`, green now. **Claims:** G2 is consumer behaviour only — the producer and the HTTP route are story 02's proof; G4 and the chip head are implemented — their Chair and picker proof is story 05's. Neither is proven here.

- 2026-09-30 — round two, on Astra's built-check r1 DO-NOT-RATIFY (`checks/story-04-built-astra-r1.md`, verbatim) and Muad'Dib's rulings: (1) reads and actions isolated by document identity — `useSends` keys its state by `doc.ref` and drops obsolete answers, `mergeKnown` admits only rows of `ref`, the preview is keyed by `ref`; Astra's two probes are web-unit cases, red on `13ec2a7b3`, green now. (2) G2 (consumer behaviour; the producer and route proof is story 02's): the red-before is pinned to the base `3552be416`; the refusal contract for story 02 is recorded there (top-level integer `size`, `limit` beside `code` / `error_code`; `size` the final Slack text's characters, `limit` 39000); the face reads the top level only (the nested `context` fallback removed); the word stays CHARACTERS (BACKLOG: carry the unit for a byte-limited channel). (3) G4 and the chip-head rule: the own-container approach RATIFIED; **implemented**, their proof on the Chair and the picker is owed by story 05 (not "paid"). (4) The update's DELIVERY rows reverted to their Phase 10 / E1a look (build what was ratified); the manual row and Mark delivered unchanged; BACKLOG: "unify DELIVERY rows into the one row grammar". (5) `tests/unit/test_native_surfaces_guard.py` scans `desk/surface/` at any depth; a nested viewport query is rejected (fixture + mutation). (6) Evidence counts corrected; T2 presses Send again and checks the new digest.

- 2026-09-30 — BUILT by Muad'Dib's Fedaykin lane (Opus 5.5), stacked on story 01 (#707). The species is `web/src/desk/surface/send/` (`SendWell`, `SendWells`, `SendHistory`, `PreparedChip`, and the pieces faces.md §2 asked exported), imported through its own sub-barrel `desk/surface/send` (it carries the channel wire; the main barrel stays wire-free, so no import cycle through the desk store); documented in `web/src/desk/surface/contract.md` ("SendWell"). The update's `PublishedWells` composes it and fills the `history` slot with its DELIVERY N + Mark delivered (R8). Canvas E conditions (round one wording; see round two above: G4 and the heads are implemented, not proven on the Chair): G2 (a named preview refusal shows its word and `41,099 / 39,000 CHARACTERS` when the answer carries `size` and `limit`; red before on HEAD); G3 (`send/send-well.css`: the species' own type and the one row grammar); G4 (the well is itself a `surface` container, so the kit's 44 px narrow rules answer to the well's width in any host — the kit law forbids viewport media, `tests/unit/test_native_surfaces_guard.py:86`); the heads (SEND / SENDS / DELIVERY at 12 px in every host; a head with `data-head-chip` wraps its chips under its label, intrinsically). Slack's face words (POSTED with no link, HOOKS.SLACK.COM, WEBHOOK SET, TOO LARGE FOR SLACK) are in `channels.ts`; the wire is story 02's. Proof: `evidence-story-04.md`.

- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
