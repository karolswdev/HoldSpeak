# Agent and New Automation: owner feedback remains delivery work

Owner reminder 2026-10-20: do not let the Firefox freeze repair displace the actual design complaints. These are the next two beauty-and-delight faces. A completed feedback infrastructure fix does not close them.

1. Agent session (`228957f43ef25018d024ceebd7f60370`): the agent window is too somber, basic and weak. This is a product differentiator. Provide a powerful, understandable working experience, with the owner's Herder reference investigated rather than a guessed functional substitute. The Workbench visual style must support its power. Preserve actual agent controls, operation and results.
2. New Automation (`94c073bc4822b068c29da8598590398b`, `workbench:__new__`): replace the wall of text and disproportionately large controls with clear visual hierarchy, useful pictograms and an easy task sequence. Use common components that improve the family of faces, within the Workbench material and style.

Both original reports retain audio, screenshot, values and configured-engine transcript. Read the real images and transcript before briefing. Build direction on the existing beauty-and-delight canvas, then verify live states and saved feedback PNGs at 1440/393. Functional green does not equal the owner's aesthetic judgment. No modals, speculative framework or fabricated live capabilities.

Root is shipping the capture freeze repair first so the owner can continue reporting. A read-only audit identified the following implementation seams; complete the direction on the existing canvas before the next isolated implementation lane.

## Agent session

`web/src/desk/components/SessionPullout.tsx` composes identity, status, AskWell, agent output and Details, but the useful body largely disappears without a report. The captured idle window showed “Terminal unavailable” and only “Latest activity · Bash.” Reuse `AgentAvatar`, `AgentWords`, `agentFlights.ts` and the direct owner-action vocabulary already in `agents/AgentRow.tsx`. Elevate useful output, state and the next actual owner action; keep technical facts in Details. Define an honest useful idle state without inventing agent output. Preserve transport, answer, terminal and operation receipts.

Focused behavior coverage lives in `components/__tests__/sessionWork.surface.test.tsx`, `sessionFooter.f2.test.tsx`, `sessionAnswer.f2.test.tsx`, `sessionSpeakAnswer.f2.test.tsx` and `sessionArmVerb.r6.test.tsx`. The repository already holds the reference study at `docs/internal/betterment/herdr/STUDY.md`; it was read for this implementation.

## New Automation

`web/src/desk/components/NewWorkbenchChooser.tsx` hosts `WorkbenchTemplatePicker.tsx`; `components/automation/automation-home.css` forces six prose cards into two columns with 112px minimum height. The captured 720×460 window has both scrollbars, with Start from scratch below the cards. Present compact pictogram-led choices: name, one useful fact line, and a clear scratch entry. Preserve one-press/one-record creation and unresolved blanks. Reuse library Button and existing `ChoiceCardShell`, `SurfaceLedgerRow`, `DeskIcon`/`IconGrid` material. Settle stable existing artwork per starter on the canvas; the current data has no icon field. Check the chooser's 480px minimum against the 393px sheet.

`web/src/desk/__tests__/automation.app.test.tsx` covers starter names, one-record creation, retries and unresolved blanks. Add only meaningful coverage for changed behavior; inspect actual hierarchy, pictograms, density and hit ownership at both widths. Do not treat the existing count assertion as aesthetic proof.

## Implementation delivery

The owner explicitly directed implementation after the recording-only response. The settled canvas and held build brief are `reported-faces.html` and `REPORTED-FACES.md`. The Agent composition now uses the real provider sprite, latest report and tool activity, screen-read report fallback, existing answer/direct/terminal operations and real Refresh. New Automation now uses shared ChoiceCardShell plus library Button, mapped pictograms, compact facts and a scratch-first layout. Source is entering focused verification; delivery proof is recorded in pm/STATUS.md. Original audio and report files remain authoritative and unchanged. A merged change is not the owner's aesthetic acceptance.
