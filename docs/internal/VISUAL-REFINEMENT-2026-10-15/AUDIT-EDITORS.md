# Editor and configuration source audit — 2026-10-15

DRAFT — source candidates for root's live inspection. HOLD FOR SHIP.

Read against `94551006a` in `wt-visual-refinement-20261015`. No browser,
tests, builds, installs, or product edits. No item below is a live observation.
The ranking is owner cost, with the Tool Inspector and Thread question form
the strongest bounded repair targets. Tenets 3/5/6/7 and Constitution VII/VIII
govern the visual findings; honest failure states also engage Article VI.

## Ranked candidates

1. **Tool Inspector: the work action is buried in a separate configuration face.**
   Job: inspect an integration and post selected material. Open the command
   deck, search for `Custom webhook` or `GitHub`, and choose the integration
   under SETTINGS (`web/src/desk/components/DeskToolShelf.tsx:691`). With one
   nonempty Note or Artifact selected, its post/create verb under VERBS opens
   the same inspector (`DeskToolShelf.tsx:588`; `web/src/desk/contextual.ts:120`).
   The current mounted face is confirmed by `web/src/desk/DeskApp.tsx:243`.
   It puts operation prose and seven configuration facts before the selected
   source (`web/src/desk/components/DeskToolInspector.tsx:352`, `:353`, `:381`).
   Post, Approve, Reject, Retry, Return, and Configure are raw buttons
   (`DeskToolInspector.tsx:388`, `:460`, `:469`, `:480`, `:504`, `:516`). The
   source, proposal, and receipt each get another bordered, filled plate
   (`web/src/desk/components/chrome-menus.css:686`), while the inspector class
   also imposes its own fixed geometry, outline, and shadow on the existing
   frame (`chrome-menus.css:594`). This is a different control/material grammar
   at the exact point the owner acts. Reuse the existing `DeskWindowFrame`,
   `SurfaceSection`, `SurfaceWell`, `FoldGadget`, library `Button`, and
   `SurfaceFooter`. Keep source identity, preview, policy decision, and return
   action; fold technical facts rather than make another configuration system.
   Fails Tenets 3/5/6; UX-CANON A1 and the one-material rule. Actual scroll
   depth, clipped controls, and desktop/phone geometry need root's shots.

2. **Tool Inspector: failed and refused operations wear the success receipt material.**
   Job: understand a refused/failed post and recover. Opening path is item 1;
   the state requires an isolated response replay, not a real post. The
   receipt block is explicitly rendered for `failed`, `rejected`, and policy
   `refused` as well as `executed` (`DeskToolInspector.tsx:489`), but every
   receipt gets the same green success wash (`chrome-menus.css:707`). A
   separate bottom error paragraph appends generic instructions, including
   when the failed read was the authority fetch (`DeskToolInspector.tsx:154`,
   `:532`). There is no `EgressChip` beside the post/approval action; the
   destination appears as a distant generic fact (`DeskToolInspector.tsx:358`,
   `:426`). Reuse `StateChip`, `SurfaceState`, and `SurfaceFooter` receipt,
   egress, and verbs slots, with the actual stored outcome and existing retry
   handlers. Fails Tenets 3/5 and UX-CANON A9/A10. Source proves the shared
   style and branches; live contrast and outcome comprehension are unverified.

3. **Thread question: one answer sheet switches between library and custom controls.**
   Job: answer a tool's question and continue the held call. Open New Thread
   (`web/src/desk/verbRegistry.ts:257`) or an existing Thread; a
   `thread_tool_pending` frame with `elicitation` opens a QUESTION row and
   scrolls it into view (`web/src/desk/pullouts/ThreadPullout.tsx:1276`, `:681`).
   Enum is `CycleGadget`, but boolean, number, and free text are hand-built
   inputs (`ThreadPullout.tsx:189`, `:199`, `:209`, `:219`). The number has
   neither `aria-label` nor an associated label; the visible label has no
   `htmlFor` (`ThreadPullout.tsx:185`, `:211`). Their private rounded, monospace
   well styles (`web/src/desk/pullouts/thread-pullout.css:751`) differ from the
   paper/sans/Steel library text well (`web/src/desk/surface/gadgets.css:327`,
   `:361`). Reuse `GadgetGroup`, `GadgetRow`, `CheckGadget`, `StringGadget`,
   `CycleGadget`, and the existing Submit/Decline `Button`s. A numeric
   `StringGadget type="number"` can keep the current empty-string behavior;
   `StepperGadget` already exists if its number-only state is appropriate.
   Preserve answer types, the call ID, and the question's visibility when
   routine work is folded. Fails Tenets 3/5/6. Source candidate only: a
   concrete production tool that emits this question was not established.

4. **Agent/Recipe editor: populated fields lose their visible names.**
   Job: adjust an agent's instructions, tools, and Knowledge. Open an Agent
   object, then Edit (`web/src/desk/pullouts/RecipePullout.tsx:99`); the editor
   replaces the body (`RecipePullout.tsx:44`). New Agent also opens this
   species (`web/src/desk/verbRegistry.ts:224`). The editor renders Name, Role,
   Instructions, Avatar, User template, Tools, and Knowledge without
   `GadgetRow` or visible captions (`web/src/desk/pullouts/editors/RecipeEditor.tsx:54`,
   `:62`, `:68`, `:77`). `StringGadget`'s `label` is accessible only unless
   `caption` is passed (`web/src/desk/surface/gadgets.tsx:278`, `:346`); the
   textarea also exposes only its accessible label (`gadgets.tsx:409`). Once
   placeholders disappear, the owner sees a stack of unlabeled values.
   `More` is a one-way local toggle (`RecipeEditor.tsx:75`, `:110`), and Tools
   exposes a comma string (`:90`) while saving split values (`:36`). Reuse
   `GadgetGroup material="inset"`, labeled `GadgetRow controlWidth="full"`,
   the current String/Pad/Cycle gadgets, and `FoldGadget` for the advanced
   fields. The label/disclosure repair is small and shared-kit work; tool
   catalog redesign is a separate question. Keep the existing save writer
   and footer. Fails Tenets 3/5/7. Source establishes missing captions;
   filled values, long prompts, and expanded height need live inspection.

5. **Schedule recording: the old sheet mixes raw date controls and instructional copy.**
   Job: set a future recording. Chair footer → Schedule
   (`web/src/desk/chair/ChairHome.tsx:3159`) opens `ScheduleCreateWindow`.
   `web/src/desk/components/ScheduleCreateWindow.tsx:165` uses a full sentence
   as the group legend; When hand-wraps a raw `datetime-local` input (`:186`),
   recurring Cron explicitly removes the mic (`:203`), and the save error is
   a paragraph (`:146`, `:218`). Its action row is a local inline flex layout
   (`:227`). Reuse the native preference sheet variants in
   `web/src/desk/surface/contract.md:39`, `StringGadget`'s existing `type`
   prop, the current Cycle gadgets, and a library action/footer slot. Keep
   draft retention and one-shot/recurring semantics. Fails Tenets 3/5/6 and
   UX-CANON A3/voice law. Phone date control width and the actual popup remain
   unknown; this ranks below Inspector/Thread.

6. **Email destination editing cannot show a recipient list in full.**
   Job: verify and correct a saved report destination. Settings → Accounts
   (`web/src/pages/cores/SettingsCore.tsx:253`) → Destinations → Details → Edit
   (`web/src/pages/cores/connections/Destinations.tsx:477`, `:510`); Add
   destination → Email reaches the same form. `To` and `Cc` use single-line
   `StringGadget`s even though their values are comma-separated lists
   (`Destinations.tsx:261`), so a long recipient set must scroll inside the
   field and cannot be read as a whole. The surrounding edit sheet retains
   the old default rows (`:203`, `:295`) rather than the current inset
   preference rhythm. Reuse full labeled rows and `PadGadget` for values
   that must wrap, with the existing string-to-addresses conversion retained.
   Preserve `SecretRow`, account setup, EgressChip, and save/refusal behavior.
   Fails Tenets 3/5/7 and UX-CANON D's wrapping-value rule. This is a
   long-value source candidate, not evidence that ordinary destinations clip.

## Existing good patterns to keep

- `RecipePullout.tsx:44` replaces the body during edit and its
  `SurfaceFooter` at `:89` already owns save status and Done/Retry. The writer
  retains failed changes and waits for flush on close
  (`web/src/desk/pullouts/editors/useDebouncedSave.ts:50`, `:110`).
- Destinations distinguishes read failure from empty, keeps a failed Remove
  in place with Retry, and places EgressChip next to Check and Save
  (`Destinations.tsx:431`, `:514`, `:507`, `:299`). Details use wrapping
  ledger rows (`:471`). These behaviors should survive any visual pass.
- Current native preference variants already provide bounded value columns,
  full editors, engraved groups, action slots, and narrow reflow; their
  contract explicitly adds no schema or form-state machinery
  (`web/src/desk/surface/contract.md:39`).

## Exact inspection and regression hooks — read, not run

**Inspector:** data comes from `setup.trust.destinations`
(`DeskToolInspector.tsx:104`), produced from configured webhook/GitHub values
and receipt inventory (`holdspeak/trust_destinations.py:66`, `:122`). The
post path calls `/api/desk/actuators/{target}/propose` with exact selected
source text/ref/label (`DeskToolInspector.tsx:183`); decision uses the returned
proposal target/ID (`:218`). `web/src/desk/components/DeskToolInspector.test.tsx:59`
protects the source binding through proposal, receipt, selection changes,
and Return; `:175` covers immediate execution without an approval prompt;
`:257` covers the project branch. No failure/refusal visual assertion was
found in this file. The old Slack free-text action is parked explicitly
(`web/src/desk/contextual.ts:40`); use Custom webhook for isolated action states.

**Thread:** the executor recognizes a dispatch result's `elicit` value
(`holdspeak/services/thread_tools.py:773`); service rebroadcasts it as
`thread_tool_pending` (`holdspeak/services/thread_service.py:1635`); the
frontend reducer sets `elicitation` state (`web/src/desk/threads.ts:954`).
`web/src/desk/__tests__/ThreadToolRows.test.tsx:578` is the exact question
fixture; `:416` checks question/failure visibility alongside collapsed routine
work; `:136` checks the reducer. That form fixture covers only string and
presence, not answer submission or number/boolean/enum control behavior.
`tests/unit/test_thread_decide_always.py:136` protects the answer redispatch
protocol with a fake dispatcher. No concrete production tool producing the
question was established in this bounded audit; root may replay the fixture
on its isolated hub. `web/src/desk/__tests__/ThreadPullout.test.tsx:139`
covers neighboring message/error/sibling/footer behavior if the whole face
is touched.

**Destination:** `web/src/desk/__tests__/destinations.app.test.tsx:174` covers
account failure/setup and real field saves; `:236` covers email keys and
sender checks. Root owns live 1440/393 validation and any focused run choice.

## Unknowns and Tuesday judgment

No live reachability, shots, focus/hit ownership, scroll depth, popups,
computed type/contrast, service result, or DB row was verified here. Current
imports and opening actions establish active source paths, not successful
runtime actions. Inspector failure/refusal and mixed-type Thread questions
need isolated producer responses; no external action is required to inspect
them. The source supports a bounded kit composition pass, starting with the
Inspector and question form. Tuesday: the owner should see the selected
source, destination, next verb, and actual outcome before technical facts.
