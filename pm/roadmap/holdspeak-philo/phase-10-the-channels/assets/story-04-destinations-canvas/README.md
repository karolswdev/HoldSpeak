# PHILO-10-04 canvas B: the Destinations group in Settings → Connections

**Status: DRAFT, for the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. The review page is `index.html` in this folder: every board at 1440 × 900 and 393 × 852. Canvas A, the SEND well, is `../story-04-send-canvas/`. Both canvases share its harness (`../story-04-send-canvas/harness/`), and that README states the app, the hub and the stated wire in full.

Sources: story 04 (`../../story-04-the-send-face-and-the-destinations.md`: "add, check, remove (park; history kept), per-channel fields"), the design (`../../design/send-lifecycle.md` sections 1, 5 and 8), and the Connections pane it joins (`web/src/pages/cores/connections/ConnectionsPane.tsx`).

## Three questions for the owner

1. **The place:** destinations live in Settings → Connections, in a Destinations group under Tools? **Recommended: yes.** The accounts that each destination uses (GitHub, Jira, Confluence) are in Tools, directly above, so their sign-in states are in view.
2. **The Room's verb:** `Add destination` in the Room opens Settings there, and does not add a destination in the Room? **Recommended: yes.** One place to add, check and remove; the Room only sends.
3. **The name:** a new destination's name fills from its target (`Folder Payments`, `Jira PAY-118`, `Email lena@acme.io`) and stays editable? **Recommended: yes.** One less field to type; the name is what the SEND well shows.

## What the boards are, exactly

- **The frame:** the product Settings window. `harness/ProposedConnections.tsx` is the real Connections module with the Destinations group added (`harness/Destinations.tsx`). Credentials and RAW stay below, as today.
- **Species only:** `GadgetGroup`, `GadgetRow`, `CycleGadget`, `StringGadget`, `CheckGadget` (token), `SecretRow`, `FoldGadget`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `EgressChip`, `Button`, `ConfirmVerb`.
- **The records:** a destination row never changes. Edit saves a new row with `replaces` and parks the old one; Remove parks. Parked rows stay in the `PARKED` fold, and their send history is kept (design section 1).
- **Validation at save** (design section 5; the refusal words are canvas A's): one Jira key, `owner/repo`, a number ≥ 1, an absolute folder, at most 20 addresses, a name.
- **The key:** the SendGrid key is typed once and goes to the OS keychain (the shim drops the value and stores only `key_ref → true`). The face shows `SET` / `KEY SET` and never the key (`6-add-email-key-set-*`: `key_text_on_face` = false).
- **Board 1** is reached through the Room: canvas A board 1's `Add destination` opens this window at the group.

## Boards

| Board | What it shows |
|---|---|
| 1 | Empty, reached from the Room: the add form, open |
| 2 | Add a folder: Folder, Name (filled from the target), the SYNCED mark |
| 3 | Add a synced folder: the row will carry SYNCED FOLDER, not THIS DEVICE |
| 4 | Add a GitHub comment: Repository, Issue or Pull request, Number |
| 5 | REFUSED `ONE KEY ONLY`: two Jira keys, nothing saved |
| 6 | Add an email: Provider SENDGRID, From, From name, the key (SET), To, Cc |
| 7 | The list: seven destinations, each with channel, target, account state and the egress chip |
| 8 | A row open and checked: Check (`CHECKED` + time), Edit, Remove |
| 9 | Edit: the same form, filled |
| 10 | The old row parked: `PARKED` holds Jira PAY-118; the list shows Jira PAY-121 |
| 11 | Remove armed: `Remove?` |
| 12 | Removed = parked: the row goes into `PARKED`, history kept |

## Measurements

24 renders (12 boards × 1440 × 900 and 393 × 852), `shots/facts.json`; the scans cover the whole Settings window and any portal:

- Text under 12 px: **0** in the proposal, **0** inherited (with the 12 px repairs in `../story-04-send-canvas/harness/canvas.css`; before them the SYNCED token read 11 px and five inherited Connections texts 9–10 px).
- Raw `<button>` without the library `.btn`: **0** in the proposal; **1** inherited on every render (`C COPY`, the library TransportKey; see Limits).
- Horizontal overflow: **0**.
- Contrast, every text-bearing element inside the proposal: lowest **4.5:1** (board 6, the email form); none under 4.5:1. The probe records the lowest ratio per board, not the element.
- Pointer: **260** proposal controls, **2340** points, **all owned** at both widths (after the 44 px narrow-target repair; before it, the form's fields, selects, mics and SYNCED token failed at 393). Of the untouched chrome, **96** controls miss points (the SETTINGS tab's right edge; at 393 the traffic lights, the Settings footer and the Dock).
- Modals **0**; the SendGrid key on the face **never** (`key_text_on_face` = false); browser errors **0**.

## Limits (what the boards are not)

- The destination routes are the shim's statement of the design (`../story-04-send-canvas/harness/shim.ts`, items 2 and 6), not a server response. Check answers from stored account states.
- The GitHub account (`kwork`, CONNECTED) and one Confluence account (SIGN IN) are overlaid on the Connections read. The Jira account is real (NEVER CHECKED).
- The COPY key on the Jira account row (Tools, above the group) is the library `TransportKey`, a raw `<button>` (`web/src/desk/surface/gadgets.tsx:720`, used at `ConnectionsPane.tsx:148`). The canvas does not touch it, and the facts count it apart from the proposal (`raw_buttons.inherited`). BACKLOG row filed.
- Inherited window chrome (the SETTINGS tab's right edge; the 393 traffic lights, Settings footer and Dock) fails some pointer points. The same failures appear on the unchanged product; the proposal's own controls are all owned. BACKLOG row filed.
