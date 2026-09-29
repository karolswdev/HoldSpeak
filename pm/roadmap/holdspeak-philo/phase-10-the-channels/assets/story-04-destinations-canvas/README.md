# PHILO-10-04 canvas B: the Destinations group in Settings → Connections

**Status: DRAFT, round four, for the owner's ratification** (rounds three and four change canvas A only; this canvas is recaptured with it) (UX-CANON §A.2: the canvas before the build). Round two pays Codex Astra r1 on #693 (`../../checks/canvases-astra-r1.md`). Round three pays Codex Astra r2 (`../../checks/canvases-astra-r2.md`) on canvas A; this canvas is recaptured with it, and the pointer probe now re-measures a control that changes size under it. Nothing here is built in product code. The review page is `index.html` in this folder: every board at 1440 × 900 and 393 × 852. Canvas A, the SEND well, is `../story-04-send-canvas/`; its README states the shared harness, the hub and the stated wire in full.

Sources: story 04 (`../../story-04-the-send-face-and-the-destinations.md`), the design (`../../design/send-lifecycle.md` sections 1, 5 and 8), story 01 as built (#692: the destination record, Remove = park, `DELETE /api/channels/destinations/{id}`), and the Connections pane it joins (`web/src/pages/cores/connections/ConnectionsPane.tsx`).

## Three questions for the owner

1. **The place:** destinations live in Settings → Connections, in a Destinations group under Tools? **Recommended: yes.** The accounts each destination uses are directly above.
2. **The Room's verb:** `Add destination` in the Room opens Settings AT the group (board 1: in view, the add form open), and the Room shows the new destination when he comes back, with no reload (canvas A board 2)? **Recommended: yes.**
3. **The name:** a new destination's name fills from its target (`Folder Payments`, `Jira PAY-118`, `Email lena@acme.io`) and stays editable? **Recommended: yes.**

## Round two

- **The arrival (F2):** the Room's verb sets an intent (`requestDestinationsFocus`, `harness/p10.ts`); the group reads it when it mounts, or from its event when Settings is already open, then scrolls itself into view and opens the add form. Board 1 is shot with NO harness scroll; its named elements (the group head, the Channel control) are asserted on screen at both widths.
- **The return (F2):** Save and Remove send the change signal; every open SEND well reads its destinations again (canvas A board 2).
- **Named failures (F5):** a destinations read that gets no answer shows `CANNOT READ DESTINATIONS` + Retry (board 16), never the empty add form. A refused key save shows `KEY NOT SAVED` + the reason (board 7).
- **The email Check (F6):** Check reports the sender's verification in SendGrid, never the key alone: `SENDER NOT VERIFIED` while the from address is not a verified sender (board 11).
- **The Confluence form (F5):** board 6.
- **Literal case (F6):** targets keep their exact spelling.

## What the boards are, exactly

- **The frame:** the product Settings window. `harness/ProposedConnections.tsx` is the real Connections module with the Destinations group added (`harness/Destinations.tsx`). Credentials and RAW stay below, as today.
- **Species only:** `GadgetGroup`, `GadgetRow`, `CycleGadget`, `StringGadget`, `CheckGadget` (token), `SecretRow`, `FoldGadget`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `EgressChip`, `Button`, `ConfirmVerb`.
- **The records:** a destination row never changes. Edit saves a new row with `replaces` and parks the old one; Remove parks. Parked rows stay in the `PARKED` fold with their history.
- **Validation at save** (design section 5): one Jira key, `owner/repo`, a number ≥ 1, an absolute folder, at most 20 addresses, a name.
- **The key:** typed once, into the OS keychain; the face shows `SET` / `KEY SET` and never the key (`key_text_on_face` = false on boards 7 and 8).

## Boards

| Board | What it shows |
|---|---|
| 1 | Arrive from the Room: the group in view, the add form open (no harness scroll) |
| 2 | Add a folder: Folder, Name (filled from the target), Save |
| 3 | Add a synced folder: SYNCED FOLDER, not THIS DEVICE |
| 4 | Add a GitHub comment |
| 5 | REFUSED `ONE KEY ONLY` |
| 6 | Add a Confluence blog post: account (SIGN IN), Space id |
| 7 | `KEY NOT SAVED · NO SAFE KEY STORE` (fixture: no safe OS key store) |
| 8 | Add an email: SendGrid, From, From name, the key (SET), To, Cc |
| 9 | The list |
| 10 | GitHub row open and checked: `CHECKED` |
| 11 | Email Check: `SENDER NOT VERIFIED` |
| 12 | Edit |
| 13 | The old row parked |
| 14 | Remove armed |
| 15 | Removed = parked |
| 16 | `CANNOT READ DESTINATIONS` + Retry |

## Measurements

32 renders (16 boards × 1440 × 900 and 393 × 852), `shots/facts.json`; the default run (both widths, each on its own hub) exits 0 with the fences on:

- Named elements on screen: **70 of 70**, board 1 with NO harness scroll. Identical shots within a width, with the menu-bar clock masked: **none**.
- Text under 12 px: **0** in the proposal, **0** inherited (with the 12 px repairs in `../story-04-send-canvas/harness/canvas.css`).
- Raw `<button>`: **0** in the proposal; **1** inherited on every render (`C COPY`, the library TransportKey; see Limits).
- Horizontal overflow: **0**.
- Contrast, unrounded: lowest **4.50444771:1**, the `SET` token of the SendGrid key (board 8; Codex's "B6 SET token"); none under 4.5:1.
- Pointer: **348** proposal controls × 9 points = **3132**, **all owned** at both widths. The probe re-measures a control that changes size under it (board 14's armed `Remove?` disarms to `Remove` after 3 s) and records it as `retried`; in this run none needed it. Of the untouched chrome, **128** controls miss points (the SETTINGS tab's right edge; at 393 the traffic lights, the Settings footer and the Dock).
- Modals **0**; the SendGrid key on the face **never** (`key_text_on_face` = false on boards 7 and 8); browser errors **0**.

## Limits (what the boards are not)

- The destination routes for channels other than the file channel are the shim's statement of the design (`../story-04-send-canvas/harness/shim.ts`); Check answers from stored account and sender states.
- The GitHub account and one Confluence account are overlaid on the Connections read. The Jira account is real (NEVER CHECKED).
- The COPY key on the Jira account row (Tools, above the group) is the library `TransportKey`, a raw `<button>` (`web/src/desk/surface/gadgets.tsx:720`, used at `ConnectionsPane.tsx:148`). The canvas does not touch it; the facts count it apart (`raw_buttons.inherited`). BACKLOG row filed.
- Inherited window chrome (the SETTINGS tab's right edge; at 393 the traffic lights, the Settings footer and the Dock) misses pointer points, as on the unchanged product. BACKLOG row filed.
