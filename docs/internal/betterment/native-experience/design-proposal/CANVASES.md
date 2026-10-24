# Native-experience design proposal canvases

**DRAFT — UNCHECKED, awaiting Muad’Dib.** 2026-10-23. These are static
design canvases, not product implementation, a route, a component preview or
evidence of production parity. The HTML has no handlers. Painted fields and
verbs are proposal labels only.

Open [CANVASES.html](CANVASES.html) locally. The artifact contains nine
paired board groups: one fixed desktop artboard (1440 × 900) and one fixed
narrow artboard (393 × 852) for each group. Each pair is a horizontal,
scrollable stage so the desktop board is not silently scaled to the viewport;
small state insets sit beside the primary composition. The page's legend is
outside the app frames and repeats the static-proposal boundary.

## What this packet settles

The strategy's first design checkpoint asks for a coherent resource and
preferences composition, the Thought editing counterexample, the sourced-Ask
handoff, retained-work outcomes and a Components reference that does not
pretend to be adopted. The boards make those decisions visible in one material
language:

- fine cool frames, restrained 8px rounding, quiet slate floor, pale paper,
  soft depth and blue selection from the current Workbench × Pop!_OS tokens;
- one window grammar: title and identity in the head, task regions in the body,
  receipt/egress and local verbs in the foot;
- 26px display once, 15px primary, 14px body and 12px mono metadata; readable
  text stays at or above the current 12px floor;
- desktop controls are painted at the current 32px `--size-btn` floor;
  narrow controls and field rows reserve 44px ownership;
- each narrow board preserves the job in one window. It stacks or sequences
  regions; it does not cram two desktop panes into 393px;
- illustrated glyphs are small inline construction cues only. No bitmap icon,
  CDN, new icon family or product asset was introduced.

The HTML uses class names that map to current surface species (`btn`,
`state-chip`, `egress`, `provenance`, `surface-well`, `window-head`,
`SurfaceSection`-style labels and `ComposerWell`-style composer material).
They are static CSS representations of the current values, not a replacement
for the library.

## Board map

| Board | Journey | Desktop state | Narrow state | Target consumer / owner job |
| --- | --- | --- | --- | --- |
| A · Resource workspace | J5 resources | Two independent windows of the same registered `HoldSpeak` repository: `/src` in front and `/docs` retained. Each has its own breadcrumb, selection, command target and Git-status context. | `/src` owns the full narrow frame; `/docs` is retained in the window list. | `RepoWindow` / repository provider. Inspect a file, navigate, switch windows and keep context after a refusal. |
| B · Thought + Ask | J1 Thought; J3 review Ask | A selected passage in a document window hands a scoped chip to Ask. The answer can become `Save as Note`; the source remains the return door. | One Ask frame contains the captured source quote, thread, stable composer and Back to Thought; source-return context stays outside the frame. | Thought document/editor and Ask source handoff. Preserve selection, editor ownership, draft and return location. |
| C · Settings | J6 settings | Compact category rail and two `You` fields (`Name`, `Also called`). `Name` is `NOT SAVED`, `Also called` is `SAVED`, and autosave shows `NOT READY` during the conflict. | One `You` category picker and stacked fields. No grid of giant cards and no generic Save verb. | Settings You section. A changed field stays visible while the revision is checked and `Retry` rechecks it. |
| D · Meeting retained work | J2 meeting | A meeting record keeps its stable meeting id, a partial-record view, timeline and actual Stop outcome. The recovery door is `Open partial record`; no invented automatic Send. | Same record identity, events and review action remain readable in one narrow window; outcome reads `Saved in part`. | Meeting record/live work. Distinguish stopped capture, retained partial record and review/recovery. |
| E · Components reference | J7 reference / desktop | Pattern navigation, fixture-state picker, same-production-pattern proposal, target consumer and optional contract notes. Clearly marked `PROPOSED` / `LOCAL SPECIMEN`. | Pattern and state lookup remain reachable above the footer in one window. | Components reference. Exercise a fixture adapter after a real consumer contract exists; do not claim adoption from a local specimen. |
| F · Project → Hand / Launch → Lane Result | J4 delegate | Project source and selected item remain visible beside the focused ResultBlock. `Hand`, `Launch` and `Start when one is free` keep their existing meanings; result identity includes launch, session, turn, worktree, used resources, last words and New/seen. | One Lane result shows its launch/session/turn, current Answer wait, supported Stop and Back to Project; source and alternative queue/Gate states remain separate context. | Project Room, Agents/Lane and ResultBlock. Keep session Stop/Resume distinct from wait Answer and Gate Approve/Deny; no universal monitor. |
| G · Meeting action → Today / Needs → Nudge / Send | J2 meeting; J4 follow-through | Meeting source, one canonical action row and frozen Send preview show action id/source/owner/due, exact bytes, destination, owner egress and unknown readback/replay key. | One prepared Send frame shows frozen content, destination, owner/due, egress and Back to Meeting; the canonical action/source and alternative unknown outcome are external context. | Meeting aftercare, Today/Needs and Send. Preserve the same action and prepared bytes; unknown is not `Sent` and retry does not duplicate. |
| H · Ask readiness | J6 settings / Ask | Blocked Ask, adopted profile reference, per-job engine assignment, account selection and ready composer are separate windows and authorities. | One Engines frame shows the adopted Local text profile, Ask assignment and Back to Ask; Setup/source-account transitions remain compact external context. | Settings You, Setup, Engines, Accounts and Ask. Readiness is scoped to the current Ask job and returns to the selected source. |
| I · Terminal operation + window feedback | J7 terminal / feedback | ProcessCore shows target/egress/receipt with unknown and session-scoped Stop; UiFeedbackHost shows source/window/generation, screenshot/audio, saved bundle and ASR-only retry. | One saved report frame keeps screenshot/audio/window generation and bundle identity, transcription-only Retry and Back to Settings; the operation receipt is separate context. | ProcessCore operation outcome and UiFeedbackHost report capture. Keep these two authorities distinct; a failed report cannot change or resend the domain operation. |

The group headings also state the intended relationship: A stresses per-window
application identity, B challenges selection and editor ownership, C stresses
dirty/revision/retry ownership, D stresses retained operation outcomes, E
tests whether a reference can demonstrate the same pattern without becoming a
second domain application, F keeps Hand/result authority and Project return
visible, G preserves action lineage through frozen egress, H separates
readiness authorities for one Ask job, and I draws ProcessCore and
UiFeedbackHost as two different jobs with two different returns.

The proposed convergence read order remains Repo → Settings You → Thought →
Ask → Project → People, followed by Meeting action aftercare. Ask source
handoff is drawn from supported Thought/Project/People material; repository
attachment remains conditional on a provider `ask` capability. For feedback,
ProcessCore is the first operation-outcome consumer (SendWell follows as the
second), while UiFeedbackHost reports Settings first and Ask second. The board
order is kept readable by job family rather than rearranged into a product
wizard; F–I add the missing return scenes and do not claim that their
producers or providers are already implemented.

## Region hierarchy and shared pattern

Every app frame in all nine scenes follows this order:

1. **Window head** — application/window identity, one title, state chip when
   it is a fact, and quiet frame actions. The head never repeats a long body
   title just to fill space.
2. **Body lead** — one leading fact or task name, one quiet scope line, then
   the region that owns the work.
3. **Task regions** — an optional navigation rail or breadcrumb, a readable
   work area, a bounded source/editor well only where that task needs it, and
   an inspector or context rail only when it preserves the job.
4. **In-flow state** — refusal, conflict, busy or retained outcome beside the
   affected resource. It never floats as a toast and never becomes a modal.
5. **Window foot** — egress where it happens, provenance, receipt or retained
   state, then local verbs. A static proposal may paint a verb, but no canvas
   control performs an action.

Shared visual pattern names are deliberately small:

| Pattern | Shared visual contract | First target consumer | Deliberate exception |
| --- | --- | --- | --- |
| Window head + foot | Identity, state, egress/provenance, frame focus and local context | All nine scenes | Specialized editor, lane, ledger and feedback windows still own their inner rendering. |
| Breadcrumb + command strip | Location first; commands carry explicit target context | RepoWindow | Git status is shown only as a supported repository fact; no transfer verbs. |
| Selected source passage + scope chip | Selection is a resource identity with a visible source, not a copied paragraph | Thought → Ask | Ask retains its composer and thread ownership. |
| Field row + autosave receipt | Field draft, captured write, conflict and retry stay distinct | Settings | No generic Save button; domain writer remains authoritative. |
| Timeline + retained outcome | Stable meeting id, event facts and recovery door distinguish stopped from saved | Meeting | Stop/partial/recovery semantics remain meeting-specific. |
| Pattern nav + fixture state | Shared production pattern proposal, fixture adapter and named target consumer | Components | `LOCAL SPECIMEN` is not adoption or owner acceptance. |
| Source return + receipt | Exact source/action/operation identity remains available beside a terminal or unknown outcome | Project, Meeting, ProcessCore | Return is a local opener, not a global task monitor or new workflow id. |
| Frozen preview + owner egress | Prepared bytes and destination remain inspectable until explicit owner `Send` | Today/Needs → Send | Unknown readback reuses the same key; no fake `Sent` state. |
| Job readiness surfaces | Profile, engine and account remain separate facts with a per-job ready state | Ask | These are separate authorities, not a setup wizard or universal readiness flag. |
| Operation ledger + issue bundle | Domain receipt and user-report bundle have separate ids, states and returns | ProcessCore + UiFeedbackHost | ASR retry is transcription-only; it never re-runs the operation or capture. |

No board introduces a universal workflow wizard, global task monitor, fake OS
file manager, hidden file transfer, Keep/Bin action, automatic Send, or a
second window manager. Repo A intentionally shows only the current source
facts from the application model: registered-root tree, file read/inspection,
navigation/history direction and Git status/branch context. It does not claim
copy, move, drop, stage or commit support.

## State stories

### A · Resource workspace

- **Default:** `/src` and `/docs` are separate windows of the same registered
  repository. Their breadcrumb, tree, selected identity and command target are
  different. The front window is `/src`; `/docs` is retained, not duplicated.
- **Error:** `READ REFUSED` names the path and leaves location and selection in
  place. `Retry` is local to the read request; the supported v1 command strip
  stays read/navigation/status only.
- **Resumed:** the retained second window can be raised without resetting the
  first window's history, selected row or scroll position. This is proposed
  behavior, not observed behavior.

### B · Thought + Ask source handoff

- **Default:** the selected passage has a clear source. Ask carries a scoped
  source chip, a stable reading/composer relationship and one answer at both
  widths; the narrow pair shows the source frame followed by the Ask frame.
- **Error:** `REPLY REFUSED` leaves composer text and the source chip intact;
  `Retry` names the captured request, not a new global task.
- **Resumed:** `Save as Note` is the retained action. Returning to Thought shows
  the original two-line selection. The boards do not use `Keep` or `Bin`.

**B input recovery implementation (2026-10-23):** the active Thought field
binds its editor/range/generation before transcription. A later draft, IME or
read-only target keeps words in the same Note's NOT INSERTED well; Insert at
caret is an explicit new local insertion with one undo. Copy retains the
words. Canvas B includes desktop recovery and a narrow source-state inset;
this static drawing is distinct from the actual browser captures.

### C · Settings

- **Default:** `Name` and `Also called` are readable fields. The conflict state
  keeps `Name` as `NOT SAVED`, `Also called` as `SAVED`, and autosave as `NOT
  READY`; `Autosave on change` is visible policy, not a generic Save affordance.
- **Error:** `CONFLICT` names the newer revision and keeps the draft visible.
  `Retry` rechecks the current revision; it does not throw the field away.
- **Resumed:** the saved chip remains tied to the field, and changing category
  does not imply a different application or large card page.

**Implementation observation (2026-10-23):** the first Settings You slice
uses the existing `GadgetGroup`/`GadgetRow` fields and owner writer, with per-field
Edited → Saving → Saved or Not saved. The compact policy row says Autosave on
change and one group Retry retains the current draft. A newer edit cannot be
called Saved by an earlier ACK. Forms in Components now exercises this same
composition/controller through isolated adapter IO; its presets are saved,
edited, saving, refused, retried and newer-edit. The earlier generic form mock
is parked. This is a bounded implementation refinement of C/E, not owner visual
acceptance or completion of all readiness work.

### D · Meeting retained work

- **Default:** the record view names one stable meeting id, event timestamps,
  local provenance and a partial transcript boundary.
- **Error/outcome:** `STOPPED` is explicit, and `SAVED IN PART` is a record
  outcome rather than a success badge. No automatic Send is drawn.
- **Resumed:** `Open partial record` is the recovery door. It returns to the
  retained record; it does not pretend to resume capture or retry a transport
  that the current contract has not established.

### E · Components reference

- **Default:** `Forms` is selected, with a conflict fixture. The pattern is
  labelled `PROPOSED`; the target consumer is `Settings · You`; the
  provider is a local adapter.
- **Error:** the fixture shows a retained draft and `Retry` as a specimen state.
  It is not a production request and makes no network write.
- **Resumed:** narrow lookup keeps the pattern strip and fixture-state picker
  in the same window, above the footer. `Local fixture` and `PROPOSED` stay visible.

### F · Project → Hand / Launch → Lane Result

- **Default:** Project Room owns `project:atlas-review`, the selected item and
  its source refs. `Hand` and `Launch` are visible owner verbs. A queued path
  says `Start when one is free`, not a generic `Start`.
- **Result:** the focused ResultBlock keeps `launchId`, `sessionKey`, `turnId`,
  worktree/branch, used resources, last words and durable `NEW`/seen state.
  `Answer` is shown for the current wait, with supported `Stop`. Gate
  `Approve`/`Deny` and stopped-session `Resume` are alternative domain states,
  not simultaneous controls on this primary result.
- **Resumed:** close/reopen returns to the originating Project row with the
  same launch identity. The board does not add a universal monitor.

### G · Meeting action → Today / Needs → Nudge / Send

- **Default:** the Meeting source and one canonical action row share
  `action:act_arch_review`, `meeting:mtg_…_arch`, owner `Karol` and a due date.
  `Nudge` opens the existing Send species with exact prepared bytes and a
  destination identity.
- **Error/outcome:** the Send face shows the owner egress at `Send`, a frozen
  preview digest. The separate `UNKNOWN` state inset keeps the same readback/
  replay identity; it is not painted simultaneously with a fresh prepared Send.
  The proposed recovery must not create a duplicate or mark a lost answer Sent.
- **Resumed:** return opens the original Meeting source/action lineage. The
  prepared row is not a new meeting or a replacement action.

### H · Ask readiness

- **Default:** an Ask with no adopted profile is visibly `BLOCKED` while its
  source and composer remain. Setup exposes real profile facts and an adopted
  `profile:local-text-01`; `Use` adopts the found Local text engine profile.
  Per-job assignment remains an Engines action; this is not a speech/owner
  identity profile.
- **Ready:** Engines assigns one engine to `Ask · source question`; Accounts
  selects Acme GitHub/Jira only for sources or destinations requiring that
  account. Local Ask does not require an OAuth account. Ask returns with its
  source chip/composer; speech readiness and other jobs remain separate.
- **Resumed:** the source selection and composer return to the same Thought
  passage. Setup, Engines and Accounts remain separate authorities, not a
  wizard or a second settings application.

### I · Terminal operation + window feedback

- **Default:** ProcessCore keeps operation target, egress, receipt and
  `UNKNOWN` readback visible, while a separate running terminal row exposes
  session-scoped `Stop`. UiFeedbackHost names the exact source/window/
  generation, screenshot, audio, installed-ASR route and saved bundle.
- **Error/outcome:** a saved bundle with `ASR FAILED` offers `Retry
  transcription` only. It does not re-record, resend or change the ProcessCore
  operation result. The operation ledger and report bundle retain separate
  identities.
- **Resumed:** `Cancel` returns to the originating window and preserves focus;
  a late capture or transcription result cannot replace the next report.

## Material sources and source-of-truth boundaries

The canvases were drawn against the current tracked sources, with anchors
kept as source facts rather than implementation promises:

- [STRATEGY.md](../STRATEGY.md) — proposed identity/lifetime, command scope,
  separate read/edit/operation state, falsification order and whole-job proof.
- [APPLICATION-MODEL.md](../APPLICATION-MODEL.md) — resource app identity,
  per-window navigation/history/selection, command context, supported
  repository boundaries and the explorer acceptance workload.
- [DELIVERY-PLAN.md](../DELIVERY-PLAN.md) — the design-refinement checkpoint,
  resource pilot, Settings/Thought counterexample and Components parity
  sequence.
- [adversarial/components_reference.md](../adversarial/components_reference.md)
  — the reference's current gap: local specimen state is not a fixture
  adapter or production convergence; narrow target navigation must be clear.
- [adversarial/agent_hand.md](../adversarial/agent_hand.md) and
  [adversarial/agent_result.md](../adversarial/agent_result.md) — exact Hand,
  Launch, queue, ResultBlock identity, session/turn facts, New/seen and
  separate Answer/Gate/Stop/Resume boundaries.
- [adversarial/today_followthrough.md](../adversarial/today_followthrough.md),
  [adversarial/send_prepare.md](../adversarial/send_prepare.md) and
  [adversarial/send_commit.md](../adversarial/send_commit.md) — canonical
  action lineage, Nudge as Send preparation, frozen bytes, owner egress,
  unknown readback and same-key recovery.
- [adversarial/feedback.md](../adversarial/feedback.md) — ProcessCore
  operation ledger versus UiFeedbackHost report bundle, saved capture,
  screenshot/audio/ASR facts, cancel return and ASR-only retry.
- [DESIGN_SYSTEM.md](../../../DESIGN_SYSTEM.md),
  [UX-CANON.md](../../../UX-CANON.md) and `web/src/styles/tokens.css` —
  Workbench × Pop!_OS material, 12px text floor, 32px desktop controls,
  44px narrow ownership, quiet borders, soft depth and library species.
- [MODERNIZATION-IMPLEMENTATION-2026-10-22.md](../../MODERNIZATION-IMPLEMENTATION-2026-10-22.md)
  and [modern-shell-2026-10-22.html](../../canvases/modern-shell-2026-10-22.html)
  — current shell direction and old canvas reference. The older canvas was
  used only for shell provenance; its generic Save semantics are not copied.
- Existing source consumers named by the audit: `RepoWindow`/repository
  provider, Thought editor, Ask composer, Settings profile, Meeting record and
  Components `DesignReference`. The live executable component catalogue
  remains the actual reference for a later implementation; this HTML is not
  that catalogue.

## What this static packet cannot verify

It cannot verify any of the following:

- that the current provider can read every path drawn, or that Git status is
  available for every registered repository;
- stable window ids, per-window history, selection anchors, scroll restoration,
  stale-response rejection or command routing;
- editor caret/IME/voice/undo behavior, source handoff identity, durable Note
  creation, or Ask transport/refusal semantics;
- Settings autosave ordering, revision conflict detection, newer-draft
  preservation or retry receipts;
- actual Meeting stop identity, partial-record persistence, recovery or
  transcript completeness;
- live Hand versus Launch admission, queue availability, ResultBlock
  authority, session/turn freshness, Gate races, late results, or exact
  worktree/used-resource receipts;
- canonical action/meeting lineage, destination/account readiness, exact
  prepared bytes, external Send arrival, unknown readback, replay-key
  idempotence or duplicate prevention;
- Ask provider capability, adopted profile/engine/account state, per-job
  readiness, native speech binding or a real source-to-composer return;
- ProcessCore journal/receipt reconciliation, parent/child operation state,
  terminal generation or UiFeedbackHost capture timing, bundle persistence,
  installed-ASR transcription, cancel focus return or ASR-only retry;
- a fixture adapter that uses the same production pattern/controller boundary,
  Components adoption, keyboard/assistive technology behavior, pointer hit
  ownership, performance or reduced-motion behavior;
- browser/device rendering at the real Desk, the live 1440/393 shots, or the
  owner's Tuesday use and aesthetic acceptance.

The next implementation brief should therefore cite the relevant board and
state, then prove the real job with isolated data and the current quick-check
and screenshot procedure. A green static review is not a build or walk result.

## Bounded implementation verification notes

These notes do not reopen the settled composition or ask for owner choices.
They identify source checks a later implementation brief must perform:

1. Verify the chosen narrow resource window-list direction and the retained
   `/docs` identity against the compositor's current window records.
2. Verify repository refusal copy and branch context placement against the
   provider response; keep the board's read/navigation/status boundary.
3. Verify Thought/Ask source identity and Note receipt wording against the
   authoritative producer; preserve the painted scope chip and return
   selection.
4. Verify `Autosave on change`, conflict, and draft-retained copy against the
   Settings writer and revision receipt.
5. Verify the retained Meeting record/recovery operation before exposing a
   build verb; this canvas still makes no capture-resume claim.
6. Verify the smallest Components fixture adapter from one real consumer,
   including identity, selection, commands, edit state and outcome; E remains
   a golden-record proposal until that seam exists.
7. Verify the active Hand/Launch ingress and queue wording against the current
   producer; the board uses the existing labels and does not imply provider
   support.
8. Verify the named Today/Needs → Nudge destination fixture, exact prepared
   bytes, ownerSend egress and same-key unknown receipt against the channel
   contract; no local-folder provider behavior is claimed here.
9. Verify the adopted Ask profile, per-job engine and account facts against
   Settings/Ask authorities; `profile:local-text-01` remains a fixture ref and
   readiness is intentionally not global.
10. Verify ProcessCore operation metadata and UiFeedbackHost bundle/ASR route
    against their current sources; I keeps the two contracts separate and does
    not claim either state was observed.

This artifact is ready for visual inspection by the root agent. It remains
**DRAFT — UNCHECKED, awaiting Muad’Dib** until his review; no product code,
route, manifest or deployment change is implied.


## B implementation observation — selected Thought source, 2026-10-23

The first P04 pilot uses the painted source/return relationship in the active
Thought and Ask windows. Its exact controlled source frame is also the
Components Conversation specimen. Back stays outside the quote fold during
pending work. An unchanged body restores range/scroll, including a closed
source window; SOURCE CHANGED keeps the current editor work and caret visible.
Save as note carries editable qualified source/thread links. These are bounded
implementation observations, not approval of all static boards or owner
visual acceptance. The frontend body capture validates return only; server
source-version pinning, Project/People jobs and whole J3 remain separate.
