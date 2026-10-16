# Thread, Ask and notifications — source audit

2026-10-15 · DRAFT · source audit, no runtime verdict

Source base: `d07a88ca78d145ed0014e448a7c0154f9bbd6437`, worktree
`/Users/karol/dev/tools/wt-attention-dismiss-20261015`. The urgent dismissal
fix is changing AmbientLayer and projections in this tree. **Line anchors can
drift; find the named declaration before editing.** This audit changed only
this file. No product edits, builds, tests, browser runs or commits.

Read: TWO-BRAINS, CLAUDE fast cycle, Constitution, UX-CANON and DESIGN_SYSTEM;
current surface library contract and active components. Seven Tenets 2/3
(usable first work, acceleration), 4 (simple product language), 5 (shared
components), 6 (Workbench material) govern the proposal.

## The five priorities, in implementation order

1. **Make an Ask keep and retry the question that was sent.** Keep an immutable
   request snapshot beside the result. A retry sends that snapshot; a fresh
   Ask uses the current draft. Keep records the snapshot's instruction and
   context. Closing a running Ask must actually close its view and retain its
   durable draft. These are owner-visible correctness defects, not polish.
2. **Make Thread editing and recovery dependable.** Keep focus transfers within
   the inline editor alive; expose a real Retry for failed assistant turns;
   show loading as loading; replace the dead missing-thread Close action with
   real Close/Retry. Withhold the dead sibling navigation arrows while showing
   their true position/count. Do not build a branch navigation backend here.
3. **Give Thread and Ask one readable Workbench composition.** Existing window
   chrome; one paper conversation well; compact mono speaker/state metadata;
   readable UI type for authored text; one rail for the composer and context;
   one frame footer for receipt/egress. Replace raw editors with PadGadget or
   StringGadget. Ask's Keep/Bin appear once, in the footer. Thread's keep/fork
   verbs remain on the answer they act on. No new page, wizard or framework.
4. **Fit modes and context without a rack of controls.** Replace Thread's
   bespoke mode tab skin with FilterTokens, preserving the current active-mode
   toggle-to-unbind semantics. At narrow width its measured menu handles the
   choices. Remove Ask's redundant outer Add notes disclosure: its existing
   GroundingSection and RailsPicker already own their folds. Repair the raw
   RailsPicker button without nesting a button around a checkbox.
5. **Bring live notices onto the same material.** Qlippy, dictation preview and
   queue use square paper/slate material, ink, a compact source/state line and
   library Buttons. Remove the decorative gradient mascot plate and generic
   helper sentences. Preserve current projection, cutoff, preview and decision
   writers. Keep this a separate lane after the urgent dismissal fix.

Tuesday: the owner should type or speak, see which question ran, read an
answer, keep it, correct a failure and close the view without losing new work.

## Active entrypoints and behavior to preserve

| Surface | Active source and existing contract |
|---|---|
| Thread | `web/src/desk/pullouts/registry.ts:37` registers ThreadPullout. `newThread.ts:18` adopts the created thread before opening its pullout. `ThreadPullout.tsx:1151` mounts the active inner component. |
| Thread submission | `ThreadPullout.tsx:1302` calls `submitTurn` through useWriteReceipt with automatic send retry withheld. `threads.ts:686` provides pending echo, acknowledgement reconciliation and failure reload. `ThreadComposer.tsx:783` keeps draft/chips until acceptance. |
| Thread durability | `threadComposerDrafts.ts:15` uses sessionStorage, keyed by thread; pending sending state is never restored. Preserve this writer and storage scope. |
| Thread live turn | `ThreadPullout.tsx:1210` subscribes to turn/tool/status/guardrail/call frames; `:1376` reconciles active turns when frames are lost. Follow-tail stops when the owner scrolls away (`:1601`). Preserve these seams. |
| Thread content/actions | StreamingMaterial finalizes through Material (`:91`); keep note/artifact, edit/resend and fork use existing handlers (`:1327`). Routine tools remain folded while held questions/approvals stay exposed (`:1079`). |
| Thread specialist flows | InterviewPanel is active at `:1735`; People section suppresses the ordinary composer at `:1753`. Keep InterviewPanel's section/suggestion commands, CallChip, speaker replay, compaction, annotations and guardrails. |
| Ask | `DeskApp.tsx:221` mounts AskPanel when askOpen. It is a separate one-answer scratch surface, not the Thread window. Durable draft scope is `desk-ask` (`AskPanel.tsx:95`). |
| Ask request | `AskPanel.tsx:217` captures selected passage, selected desk context and grounding/rails, then calls runAsk. `ask.ts:222` serializes the HTTP request synchronously. Editing later does **not** mutate the original request body. |
| Ask result | SurfaceTraffic/SurfaceTrafficTurn, Material, RunLine, citations, grounding claims and route provenance already exist. Keep returns a real artifact through `keepAsk` (`ask.ts:337`); dragging the result onto the desk calls the same Keep. |
| Notifications | `AppShell.tsx:24` mounts AmbientLayer **outside** the `.desk-next` subtree. PreviewCard, QueueHud and Qlippy are live. AftercareNote returns null (`AmbientLayer.tsx:218`); do not revive its parked card styling. There is no separate active generic Toast host found in the inspected source. |

## Concrete defects and the settled repair

### Ask identity, newer draft and close

- **Retry changes the ask.** `AskPanel.tsx:393` calls `ask()` again. That reads
  current prompt, selection, context and grounding at `:217–244`. `sent` only
  retains prompt/lens/context count/selection (`:102`), not the full request.
  The composer and context controls remain editable during routing (`:491`,
  `:513`, `:558`). A failed question A followed by draft B makes Retry send B.
  Fails Tenet 3 and Article VI's honest action rule.
- **Keep can record the wrong instruction.** It submits live `prompt.trim()`
  (`:263`) beside the output of the earlier request. The printed YOU turn uses
  `sent.prompt` (`:370`). Editing during routing therefore makes the displayed
  instruction disagree with the kept artifact's instruction. Selected-text
  enrichment also lives in `requestPrompt` (`:222`), not that live raw prompt.
- **Running Close is not a close.** Escape refuses to close while routing
  (`:208`); the footer Cancel is disabled (`:588`); the shell onClose silently
  does nothing (`:347`). DeskWindow starts departure before invoking onClose
  (`DeskWindow.tsx:972–1026`), so normal-motion Close can leave a mounted,
  visually departed Ask. Exact visible outcome requires a live check.

Settled change in AskPanel only: retain an immutable submission object with
`prompt`, `lens`, copied context, built grounding wire object, selected passage
and keep-context. A common runner accepts that object; fresh Ask builds it,
Retry passes the last one. Retry must neither read nor overwrite a newer
durable draft. Keep uses the sent instruction and pinned keep-context. Keep
the newer draft when the result hides the composer. Do not clear it as a side
effect of retry/keep/close.

Use the existing `runAsk({ signal })` hook (`ask.ts:195`, `:225`) for local
abandonment. Close aborts that local request, invalidates its response handler,
and closes the view. Guard both success/failure updates against stale requests
and unmount. **AbortSignal does not prove the server/kernel run stopped.** The
control says Close/Cancel, never a false Stopped receipt. No new cancellation
API or durable Ask task mechanism is required for this surface pass.

### Thread editing, states and honest verbs

- `ThreadComposer.tsx:1077` cancels InlineEditor on textarea blur. Its Send is
  at `:1099`; a normal pointer focus transfer can remove the editor before the
  click. Only the mic has a mousedown guard (`:1086`). Use a group-level blur
  handler that ignores relatedTarget within the editor. Keep Enter, Escape,
  pointer Send/Cancel and mic working. Source identifies the event seam;
  pointer behavior still needs a live check.
- `ThreadPullout.tsx:1001` makes user text a click-only editable div. Add the
  existing library Button as the edit trigger or an explicit row Edit Button
  that opens the current InlineEditor. Do not use EditInPlace to auto-commit
  and resend on blur; that changes message semantics.
- Loading is rendered as `SurfaceState empty` (`:1579`). All first-load errors
  become “Thread not found” because `threads.ts:764` discards the cause.
  The visible Close callback at `ThreadPullout.tsx:1592` is a no-op. Render
  `SurfaceState loading`; use the already supplied Pullout `onClose` prop;
  for absent detail use an honest “Thread not loaded” plus retry of loadThread.
  Distinguishing 404 from an unavailable hub later requires a named load-error
  field in threads.ts; do not claim that distinction without one.
- Failed assistant turns print raw `errorJson.error` (`:1047`) and have no
  Retry; only crashed rows have Retry (`:1034`). Use SurfaceState for named
  failure plus the existing handleRetry. Keep exact server diagnostic text in
  a FoldGadget Details/Raw region, not as the leading status. Thread errors
  currently lack the bounded Ask `reason` token (`threads.ts:872`), so do not
  infer model/refusal reasons through text matching just to use RunLine.
- Both sibling arrows only call `loadThread(threadId)` (`:892`, `:893`).
  `getThread(id)` has no path argument (`threads.ts:333`), and the service reads
  newest leaf (`thread_service.py:254`; `db/threads.py:494`). Keep n/m as a
  passive true fact and withhold arrows. UX-CANON A.11; Tenet 3.

### Reading, composing and context material

- Thread's raw textarea (`ThreadComposer.tsx:977`) and InlineEditor textarea
  (`:1071`) duplicate the kit. Thread title (`ThreadPullout.tsx:1617`) and
  annotation comment (`:715`) also remain raw fields. Ask's textarea at
  `AskPanel.tsx:513` has no explicit accessible label and a separate mic.
  Replace with PadGadget/StringGadget using their existing hooks below.
- Thread labels, text, state instruments and chips remain close in scale:
  `thread-pullout.css:106`, `:126`, `:133`, `:350`. Its Send is a ghost Button
  re-skinned as desk-chip (`ThreadComposer.tsx:1005`); Call/modes/speaker have
  `all: unset` skins (`thread-pullout.css:845`, `:932`, `:967`). Ask's traffic
  is globally 12px mono (`surface.css:597`) while Send's payload already reads
  at UI 14px (`send-well.css:133`) and Thought at UI 15px
  (`thought-workspace.css:147`). Keep speaker/state tokens 12px mono; show
  user text 13px UI and answer text 14px UI; use the existing Material heading
  treatment. Editor surfaces need body/mono roles, not a fabricated headline.
- Thread paints forbidden left state rails (`thread-pullout.css:178`, `:185`,
  `:211`). Remove them; StateChip/SurfaceState carry state through icon/word.
- Ask repeats Keep and Bin in the answer (`AskPanel.tsx:409–419`) and footer
  (`:588`). Keep Copy by the material; retain one footer Keep primary and Bin
  ghost. Existing grounding receipt/citations stay under the answer.
- Ask adds outer Disclosure at `:558` around already folded GroundingSection
  (`GroundingSection.tsx:167`) and RailsPicker (`RailsPicker.tsx:107`). Remove
  the outer fold. Preserve fetch/pricing/selection logic. Rails rows contain
  a raw button with nested CheckGadget (`RailsPicker.tsx:146`): use the same
  div bandPress pattern as GroundingSection (`:74`) with the CheckGadget as
  the single native control.
- ModeTabs reimplements tabs (`ModeTabs.tsx:119`) and wraps at narrow width
  through its own CSS. FilterTokens provides library selection material and
  the measured strip menu. Adapt callback as
  `next => onSelect(next === activeMode?.id ? "" : next)`, preserve recipe
  fetch/order/cache, and name the group “Thread mode”. No new mode or None
  option is needed. Check folded-menu behavior when there is no bound mode.

Compose Thread's existing rows **inside one SurfaceTraffic**; MessageRow keeps
its outer `data-message-id` and wraps its content in SurfaceTrafficTurn. Keep
the annotation `.thread-row-assistant .thread-row-body` anchors or update the
selection lookup in the same file (`ThreadPullout.tsx:1405`). Keep one scroll
owner: attach useScrollHint to the body that already owns follow-tail, and make
the nested well body overflow visible. The composer remains a direct flex
child below it. Ask uses the same paper traffic treatment with a bounded
composer rail; scope its overrides to ask-panel.css, not the global traffic
species. Long input may scroll in its pad; it must not consume the whole phone
sheet. Confirm the final limit and text size on the canvas.

## Existing primitives to use, with exact supported APIs

| Primitive | Supported composition |
|---|---|
| PadGadget | `gadgets.tsx:363`: label, value, onChange(string), rows, autoGrow, disabled, autoFocus, onKeyDown, inputRef, inputProps, micLabel, micDraftScope. `inputProps` carries onSelect, onBlur, combobox links, data-testid. Thread onChange calls setDraft + updateAutocomplete using inputRef.selectionStart. Preserve @ and slash handlers. AutoGrow has no maximum prop; retain the composer cap in local CSS. |
| StringGadget | `gadgets.tsx:260`: same ref/inputProps/key hooks for title/comment. Use one built-in mic. It replaces its value on speech; Thread comment's current mic appends, so retain its existing external MicButton with `mic={false}` if preserving that append path. Do not silently change capture behavior. |
| SurfaceTraffic/Turn | `Surface.tsx:558`, `:585`: head/showEmpty and prefix/error/meta/verbs/children. Use YOU/ASSISTANT or current Ask YOU>/HUB> labels; no chat bubbles. Material remains the renderer. |
| SurfaceState | `Surface.tsx:214`: loading, error, empty, emptyLabel, onRetry, actionLabel/onAction. No invented empty-as-loading treatment. |
| RunLine/EngineLine | `RunLine.tsx:7`, `EngineLine.tsx:4`: keep Ask's current model/place/reason/retry data. Thread can show running from createdAt/modelId; do not invent completion duration or bounded failure reason. |
| FilterTokens | `FilterTokens.tsx:45`: options `{value,label,ariaLabel?}`, value, onChange, label, disabled, className. It carries measured narrow menu and library Buttons. |
| FoldGadget | `gadgets.tsx:467`: title, token, open/onToggle, className, children. Use for existing Raw, tool activity, earlier messages, context; preserve open state across updates. |
| SurfaceFooter | Existing egress/receipt/verbs/className slots. Preserve route-from-receipt logic at `ThreadPullout.tsx:23` and `AskPanel.tsx:295`, not intended destination painted as observed egress. |
| ScrollHint/useScrollHint | `Surface.tsx:1414` and barrel exports. Attach to the real scroll element, preserve followTail; avoid an extra nested scrolling viewport. |
| GadgetGroup | `gadgets.tsx`, contract “Native preference sheets”: material="inset", optional label, actions, children. Reuse current elicitation form at `ThreadPullout.tsx:177`; do not redesign its schema/commands. |
| Button | Use primary for Send/Ask/Keep where that is the face's action, ghost for secondary verbs. Remove desk-chip/all:unset overrides that erase disabled/focus/hit material. |

## Notifications: separate, bounded material lane

Confirmed source mismatch: `react-app.css:249–259` puts Preview/Qlippy/queue/
theater on hard-coded dark rgba, large round corner and elevated shadow.
`AmbientLayer.tsx:398` adds a gradient mascot square (`react-app.css:381`), an
eyebrow, strong title, summary paragraph and generic fallback sentence
(`AmbientLayer.tsx:424`). Preview adds “Preview before type” and generic prose
(`:71–72`). Queue prints zero-valued counts (`:135`) and a plain Open queue
link (`:148`). Qlippy uses fixed bottom 20/right 20 while preview sits bottom
24; their simultaneous geometry has not been seen. The old rule can shift
Qlippy right 452 whenever a working sheet is open (`pullout.css:409`), with no
narrow correction in that rule; phone clipping is a runtime risk.

Settled composition: preserve each current aside and writer; source/state
tokens at 12px mono, actual title 15px UI, only meaningful preview/content at
13–14px UI, one trailing verb row. Qlippy shows source, title, Review source
when it has a door, Dismiss and its current pending/failure treatment. Preview
shows the owner's words on SurfaceWell with Type it/Discard. Queue uses
SurfaceRows/SurfaceRow, omits each zero token, and a library Open queue Button.
Generic fallback summaries do not earn a paragraph. Do not truncate real
proposals or preview payloads into misleading text.

Material must be explicit because **AmbientLayer is outside both `.desk-next`
and window shell token remapping** (`AppShell.tsx:24`; `window-interior.css:20`).
Simply dropping StateChip/ActionNotice there does not produce their styled
face; their selectors require `.desk-next`. For this lane use unscoped
SurfaceWell/SurfaceRows/SurfaceState plus Button/LampGadget, and remap the
notice host's existing semantic tokens to the same `--wb-*` material in its
own CSS. Do not add `.desk-next` to an ambient wrapper (it also carries desk
layout), or copy a new notice component/store. Use the existing popup layer
and working-band offsets; verify it clears the dock at both widths.

Suggested notification files: `web/src/components/AmbientLayer.tsx`,
`web/src/styles/react-app.css`, and only the Qlippy displacement rule in
`web/src/desk/components/pullout.css`. Start after the urgent dismissal branch
lands; preserve that branch's cutoff and writer behavior exactly. No changes
to projections/intelligenceAttention/ambientAttentionCutoff are needed for
this material pass.

## Minimal coherent file groups

| Group | Exact files | Purpose |
|---|---|---|
| Ask | `web/src/desk/components/AskPanel.tsx`, `web/src/desk/components/ask-panel.css`, `web/src/desk/components/RailsPicker.tsx` | Immutable request/retry/keep/close, PadGadget, single action homes, paper conversation/composer, remove extra fold, raw rails control. Keep ask.ts and durableDraft contracts. |
| Thread | `web/src/desk/pullouts/ThreadPullout.tsx`, `web/src/desk/pullouts/thread-pullout.css`, `web/src/desk/components/ThreadComposer.tsx`, `web/src/desk/components/ModeTabs.tsx` | Conversation composition, state/retry/close honesty, editors/focus, passive branch position, modes and library material. Keep threads.ts/session draft writer/call/interview contracts. |
| Notifications | The three files above, after urgent merge | Material, copy, layout and action composition only. |

Optional narrowly justified extra: `threads.ts` only if the settled face needs
404 versus load-failure distinction; add the load error fact without changing
submission/reconciliation. `GroundingSection.tsx` only if the canvas needs a
shorter fold label; it is shared with SessionPullout, so preserve defaults or
make the label a caller option. No global token, surface, model or backend
redesign is needed.

## Unknown until root's runtime captures

- Actual owner desk model/recipe assignment; empty versus populated thread;
  actual Ask success, no-engine, refusal, transport failure and retry payloads.
- Inline edit pointer blur, keyboard entry, Escape, mic focus and speech
  append/replacement; autocomplete and slash selection with PadGadget.
- Close while routing with normal motion/reduced motion, re-opened durable
  draft and late result suppression; no claim about server cancellation.
- Thread follow-tail versus deliberate scroll, compaction fold, held tools,
  annotation selection geometry and long code/URLs.
- At 1440 and 393: native material, three text roles, actual contrast, 44px
  hit ownership, composer remaining in frame, footer wrap and scrolling.
- Real notifications together with dock/open sheet/virtual keyboard;
  placement, long title/summary/preview, Review route, dismiss retry and cutoff.

No claim here that any runtime axis passed. Root owns the current 1440/393
faces and canvas before implementation, then the scoped checks in CLAUDE's
fast cycle. This audit is held for root direction; it authorizes no product
implementation by this worker.
