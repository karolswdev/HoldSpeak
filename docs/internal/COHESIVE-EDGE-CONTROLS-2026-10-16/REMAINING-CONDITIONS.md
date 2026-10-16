# Remaining conditional controls — bounded source audit

DRAFT — source counsel for the release owner, 2026-10-16. Read the current
worktree, TWO-BRAINS, CLAUDE, Constitution, UX-CANON and the earlier
CANON-FOLLOWUP/VISUAL-CENSUS. No product changes, tests, browser, provider,
owner state or repository-history audit. Existing test names below were read
from source; they were not collected or run. The six action controls, Ask's
zero state and Resourcefulness belong to the other workers.

## Findings, ranked by owner cost

1. **Capability material is multiline data in a single-line editor.**
   `web/src/desk/contextual.ts:80` constructs selected material as
   `## title\nbody`, joining selections with two newlines. This is an actual
   caller contract, not hypothetical input. CapabilitySection seeds its durable
   draft from that material at
   `web/src/desk/pullouts/shared/CapabilitySection.tsx:43`, renders a native
   single-line input at line 130, then replaces the draft with the input's DOM
   value at line 135. Counterexample: select a Note with two Markdown paragraphs,
   open a ready workflow, and edit one word in Material. A text input strips
   line breaks; that edit writes the flattened document back to the draft and
   the next Run sends it at line 103. The owner also cannot inspect the
   paragraphs together before Run.

   **Settled minimum:** use the existing PadGadget with the same accessible
   label, durable value/scope, append-on-voice behavior and Run contract. Compose
   one mic. `web/src/desk/surface/gadgets.tsx:363` already supplies the multiline
   species and draft scope. Do not route through DeskComposer as-is: it mounts
   a gadget mic and another MicButton (`DeskComposer.tsx:35,53`).
   **Tenets 3, 5, 7; UX B and D's wrapping-value rule.**
   Focused existing checks: `web/src/desk/__tests__/contextual.test.ts` →
   `requires selected material and ready capabilities`;
   `web/src/desk/components/__tests__/commonControls.test.tsx` →
   `runs the same capability once while busy and keeps the artifact and assignment actions`.
   Neither currently proves multiline edit preservation; that exact interaction
   is the missing regression case.

2. **A successful PR review draft reports an operation identifier as its result.**
   This section is active in Companion (`web/src/pages/cores/CompanionCore.tsx:263`;
   registered at `web/src/desk/applications.ts:171`). The successful draft route
   returns nonempty output, artifact ID and operation ID, with no reason/error
   (`holdspeak/web/routes/delivery_prs.py:397–415`).
   `web/src/desk/components/PrReceiptsSection.tsx:188` therefore renders
   `RECEIPT` followed by the operation ID at line 189, while the review text is
   inside a closed `RAW · OUTPUT` fold at line 191. Counterexample: complete
   More → Draft review successfully. The resting result explains neither that
   the review is ready nor what the opaque identifier means.

   **Settled minimum:** retain the action identity with its result and show the
   proven draft outcome as `Review ready`; retain output and receipt identifiers
   in their disclosure. Other actions must use their actual returned state;
   a 202 launch response alone cannot justify `Agent started`.
   **Tenets 3–4, 7; UX A.10.**
   Focused existing check: `web/src/desk/components/PrReceiptsSection.test.tsx` →
   `shows the complete proposed comment before approval and offers deny`.
   That preserves the adjacent consent flow; this file has no existing
   successful-draft-result check. A recorded success reply rendered through
   Draft review is the missing case.

## Remaining classifications

| Site | Decision and evidence |
| --- | --- |
| Needs coverage label fallback | **No action established for current valid wire data.** The producer labels project rows from project names (`holdspeak/services/needs_you_aggregate.py:452,462,730,735`); creation rejects blank names (`holdspeak/db/projects.py:49`, `holdspeak/services/project_service.py:2957`) and normal renames reject them (`project_service.py:3453`). Watch labels come from provider/scope, falling back to the project name (`needs_you_aggregate.py:760`); frontend read failure supplies `Desk` (`web/src/desk/coverage.ts:100`). Thus `NeedsDrawer.tsx:661` does not itself establish a reachable raw-ID defect. Legacy/corrupt rows and alternate writers remain unverified. If observed, reuse `sourceLabel` at `coverage.ts:164`, rather than invent another fallback. |
| Coder reply | **No concrete job defect established.** `web/src/desk/pullouts/CoderPullout.tsx:110–135` already mounts multiline text, one mic, durable scope and guarded send. The actual composer styles allow the textarea to shrink (`web/src/desk/components/pullout.css:139`); the Coder-specific style provides a minimum height (`speak-to-fill.css:130`). A raw-element hit alone does not establish clipping, missing voice or failed delivery. Future species consolidation should use PadGadget and preserve the send/snapshot behavior tested in `CoderPullout.test.tsx`. |
| Review edit | **Composition debt; additional usability defect unproved.** Fields have MicButton (`web/src/features/project-room/review/ReviewPosture.tsx:108–117`) and both wrapper/input have `min-width: 0` (`review-posture.css:143,151`). The Text field accepts arbitrary strings (`review/model.ts:281,349`), so multiline text warrants the same PadGadget treatment if present; this pass did not pin a current producer/row requiring it. No blanket input migration is justified by geometry evidence here. |
| Review defer | **Runtime fit remains unknown; inspect this conditional state next.** At 393, open a proposal, press Edit, then Defer. The toolbar retains Save & accept, Cancel edit and Dismiss around the date/Confirm/Cancel group (`ReviewPosture.tsx:237–317`). The outer row is explicitly nowrap; the inner group is also an unwrapped flex row with a 120 px native date input (`review-posture.css:93–115`). No other selector for these groups was found. This is a concrete crowded counterexample candidate, but actual clipping/pointer ownership was not observed. If it fails, wrap the existing verb row and defer group under the `surface` container; retain native date selection, autofocus, Enter and Escape. The existing exact check is `ReviewPosture.test.tsx` → `clicking Defer button arms the defer (shows date + confirm)`; it does not test fit. Native date-picker behavior and a spoken-date adapter were not assessed. |

TUESDAY: Fix the material editor's loss of paragraph structure and the PR
draft's opaque success result; check armed Review on glass before calling its
phone composition usable. This audit gives no whole-app or release verdict.
