# Remaining canon hits — bounded source audit

Status: DRAFT — source counsel for the current release owner; no product change
or release verdict. 2026-10-16. Current source and
`.tmp/navigation/canon-fixed.json` were read. No test, browser, provider, owner
state or scanner run was performed. No ceiling or waiver was changed.

The scanner reports 120 hits across 57 file buckets. Those buckets are not 57
screens. **A1 means raw buttons**, not modals; this snapshot has no modal group.
The findings below are bounded follow-up work, ranked by the owner job. Runtime
geometry and urgency must be judged alongside the release owner's actual walks.

## Active follow-up

1. **Replay a Thread message with the shared action control.**
   `web/src/desk/pullouts/ThreadPullout.tsx:1044` mounts `SpeakerGlyph` on an
   assistant message. `web/src/desk/components/SpeakerGlyph.tsx:57` renders a raw
   button with only `thread-speaker-glyph`, not the library Button. The class
   gets an active colour at `web/src/desk/pullouts/thread-pullout.css:641` and
   nowrap at line 848; it does not get the shared plated action or phone target
   rule, which is scoped to `.btn` at `web/src/styles/global.css:184`.
   Compose this existing replay/stop action with Button. This is an active
   component consistency defect; the actual pointer area was not measured here.
   Tenets 5–6; UX A.1 and C.

2. **Use Rails and open a phase's Story with the same action grammar.**
   The normal Desk mounts Rails and the dossier at
   `web/src/desk/DeskApp.tsx:244` and line 246. Rails remains conditional on
   configured repositories (`MissionControlConveyor.tsx:609`). Its session pin,
   Story pick, evidence opener and waiting-session action are raw buttons at
   `web/src/desk/components/MissionControlConveyor.tsx:82`, line 160, line 182
   and line 472. The evidence opener has a fixed 32 × 32 box at
   `web/src/desk/components/mission-control.css:716`; Story and session controls
   use 32 px minimum heights at lines 145 and 187. The dossier's phase Story
   opener is raw at `web/src/desk/components/DeliveryDossierWindow.tsx:240`,
   with 3 px vertical padding and no reserved phone target in
   `web/src/desk/components/delivery.css:87`. Delivery opens a phase through
   `web/src/desk/components/DeliveryBoard.tsx:452`.
   Compose these five existing verbs with the shared control and judge the
   populated Rails/dossier at 393. This is one cross-face action consistency
   job, not five new screens. Source dimensions indicate a target concern;
   pointer ownership and any wider overrides were not proved in this audit.
   Tenets 5–6; UX A.1 and C.

3. **Read an Ask result's grounding state without a zero counter.**
   Desk mounts Ask at `web/src/desk/DeskApp.tsx:221`.
   `web/src/desk/components/AskPanel.tsx:460` checks only for a receipt, then
   line 463 renders `GROUNDED ON {groundedMatchCount(receipt)} OF ...`.
   The source therefore permits a zero numerator. The corresponding Project
   result requires `groundedCount > 0` at
   `web/src/features/project-room/ProjectRoomCore.tsx:2280`.
   Use an explicit honest grounding state for no grounded matches; preserve the
   receipt, claims and source evidence. This is a conditional copy/consistency
   residue, not proof that the current owner's data produced a zero receipt.
   Tenets 3–4; UX A.8 and A.10.

4. **Set a Workbench idle policy without repeated safety narration.**
   The Workbench Start form mounts Resourcefulness at
   `web/src/desk/components/WorkbenchWindow.tsx:493`.
   `web/src/desk/components/WorkbenchResourceful.tsx:87` introduces it with a
   sentence, line 189 repeats a four-clause safety paragraph, and line 223 adds
   another status sentence. The real choices and limits already appear in the
   contract tokens (lines 90–98), policy gadgets (line 100), routine choices
   (line 175), and armed Enable (line 214).
   Refine product-authored copy into concise facts attached to those choices;
   retain the actual execution boundary and consent. The repeated prose is a
   source-confirmed active canon residue. Its screen cost was not measured here,
   so this is lower priority than the action controls.
   Tenets 3–4; UX A.3.

## Classification of the other scanner groups

| Group | Source classification and limits |
| --- | --- |
| A1: 8 | Six active conditional controls are covered above. The two `ZoneWindow.tsx:134,170` sites have only a parked `desk/_parked/floor/gl/WorldStage.tsx:285` consumer in the source search. They are not two current Desk defects. |
| A8: 26 | Apart from Ask's receipt above, inspected hits resolve to surrounding positive guards, numeric `SurfaceSection` counts suppressed by `desk/surface/Surface.tsx:127`, input values, an enum, a cache key, ARIA plural selection, or a comment. Examples: People guards at `pages/cores/PeopleCore.tsx:735,743,855`; Review guards at `features/project-room/review/ReviewPosture.tsx:598,603,642`; Confirm all guard at `pages/cores/history/MeetingDetail.tsx:550`; selection guard at `desk/components/AskPanel.tsx:589`; History's explicit `Nothing today` at `features/project-room/ProjectRoomCore.tsx:2451`. No 26-screen zero-counter debt is established. |
| raw-ids: 15 | Thirteen inspected hits are keys, predicates, mapped agent names, named project options, or API payload fields. For example `ConnectionsPane.tsx:233,262` compares a wire state but displays `Sign in`; `PeopleCore.tsx:1299` displays `Leader private`; `FollowThroughView.tsx:340` sends `due_at`. Two genuine conditional display fallbacks remain: `desk/needs/NeedsDrawer.tsx:661` (`source.label || source.source_id`) and `desk/components/PrReceiptsSection.tsx:189` (operation/artifact identifier when no reason/error). Their live input guarantees and actual rows are unassessed. They are not promoted to pressing findings on the fallback expression alone. |
| A3 prose/sentence: 33 | Includes retrieved/transcribed/user/model content, token receipts in paragraph tags, ScrollHint class names, compatibility components and gallery examples. `CadenceCore.tsx:665`, `history/TranscriptWell.tsx:74`, Project outcome/summary and `WorkbenchWindow.tsx:769` carry source content, not product helper prose to rewrite. FirstWords has only a parked Welcome consumer in the source search. Resourcefulness is covered above. The active ApplicationBoundary recovery paragraph (`desk/components/ApplicationBoundary.tsx:42`) and Steward tooltip (`features/project-room/steward/StewardPosture.tsx:650`) are known product copy; they were not shown to obstruct an owner job. The rest of this group is not exhaustively closed. |
| B: 14 | Two are the library EditInPlace implementation (`desk/surface/Surface.tsx:1254,1263`); ZoneRenameRow has only parked consumers. Native file, password and radio controls account for seven more. The remaining Capability material, Coder reply, Review edit and Review defer inputs are active raw control composition debt; Capability/Coder/Review edit already carry MicButton. No visual defect or missing voice affordance is inferred from B alone. Their geometry, focus and native-picker behaviour remain unassessed. |
| C: 2 | NoteEditor and XtermPane are editor/viewer interiors, not independent faces. NoteEditor composes StringGadget and DeskEditor (`desk/pullouts/editors/NoteEditor.tsx:141,148`); Xterm uses the terminal's 12 px font (`desk/surface/XtermPane.tsx:113`). A single local literal font size does not prove a collapsed parent face. |
| emoji: 22 | The matcher includes plain check/cross/warning glyphs, library implementation, and even comments (`desk/surface/Surface.tsx:496,594`; `desk/surface/gadgets.tsx:110`). Ask/Dock/gallery glyphs also appear. This audit did not establish a pressing owner job failure from these codepoints and did not perform a complete rendered glyph review. |

## Unknown

No on-glass or source-data execution was added by this audit. Actual 393 target
ownership for the raw controls, populated Rails/dossier availability, zero-match
Ask receipts, missing-label Needs rows and identifier-only PR receipts are not
observed here. The release owner's manifest sweep and selected flow evidence
remain separate. These findings do not establish a security/data-loss issue or
a release blocker. No claim is made that all residual canon debt is closed.
