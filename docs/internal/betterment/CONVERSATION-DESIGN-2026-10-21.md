# Conversation design — shared reference, 2026-10-21

Owner feedback after #1421: Ask is a little better but far from a flagship; develop the improvements in common components and common designs. Tuesday: read an answer comfortably and write the next question without hunting for controls. Tenets 3, 5 and 6 govern the change. This is a shared conversation design implementation; aesthetic acceptance remains the owner's live judgment.

Owner-started session used Setup-installed MCP before editing. project.list contains no HoldSpeak reference; memory.search returned no newer applicable brief. No unrelated project was queried. Read TWO-BRAINS, current CLAUDE fast cycle, Constitution and UX/DESIGN_SYSTEM canon. Existing saved Thread windows already redirect to Ask (ThreadToAsk.tsx); do not revive the parked Thread window or pretend it is a second live face.

## Settled canvas before build

[Canvas](canvases/conversation-design-2026-10-21.html). Use current Workbench steel, warm paper, ink rules, selection blue, real 32/64 sprites and library Buttons. No gradients, shadows or new palette beyond existing material tokens, no rounded chat bubbles. The window remains the only chrome. No new provider, data model or interaction authority.

Ask becomes a continuous reading/writing page. A compact steel About band sits at the top; reading occupies the page with generous but useful margins and a bounded 68-character measure. One etched horizontal rule leads to the composer; there are no two disconnected, fully framed white rectangles and no empty gray footer bar. The editor and the microphone/Ask actions are one coherent well. The primary action has enough width and height to read as the action; mic is immediately beside it, never stranded at the editor's lower corner. Engine and egress stay at the left of that same action row. Tools unfolds in flow. Keep selected-passage and About pickers in flow and scrollable when needed.

Empty reading state: an asymmetric composition, with the actual conversation sprite and 26px heading Ask about your work on the left, two full-width prompt rows on the right (existing exact texts). Each prompt is one library Button, a 32px relevant sprite, 15px label, and a trailing arrow. No helper paragraphs or fake desk facts. At 560px and below, use a compact horizontal identity, then stack the prompt rows. Strong spacing hierarchy 24/16/8 and real readable targets. Prompt Buttons still prefill and focus only.

Conversation: a readable document, not chat bubbles or repeated cards. Captions You and Answer clearly lead their material; question uses 15px/600 and selection-blue ink, answer uses 15px with 1.65 line height. First answer heading uses the display/primary hierarchy without resizing all nested headings. Keep real Material Markdown, code blocks, sources, receipts and actions intact. Use a shared 68ch reading measure and turn rhythm in conversation.css. No four-line model permissions paragraph dominates the face.

## Shared species and adoption

Add ONE library ComposerWell in desk/surface, exported from its barrel and documented in contract.md. It is presentation only: children/editor, context (engine/egress), capture, actions and optional details slots. It owns the paper/etched rule, focus-within treatment, compact action row, 560px reflow and accessible spacing. It does not own draft, submit, keyboard, engine, microphone or persistence state. No callbacks that duplicate host authority. Ask composes its existing single PadGadget inside ComposerWell, keeping its exact className conversation-composer desk-ask-composer literal and labels for the canon guard. Its current immutable sent snapshot/durable draft behavior stays in Ask.

Adopt the same ComposerWell in the existing DeskComposer, retained for the parked PR receipt reply screen. Preserve callback semantics and single/multiline support. Use one MicButton per editor; current DeskComposer accidentally supplies both gadget-default and standalone capture. Disable gadget-default mic when passing the standalone scoped capture. The actual host retains sending authority. Do not widen scope to terminal/agent steering or parked ThreadComposer. Shared conversation.css carries the reading typography/turn rhythm; Ask CSS carries only its context/intro and window geometry. Do not append an escalating collection of local style overrides.

## Lane and checks

Worker owns web/src/desk/surface/ComposerWell.tsx and its CSS, barrel export, conversation.css, AskPanel.tsx/ask-panel.css, DeskComposer.tsx, and focused existing web Ask/speakableDesk tests or a meaningful new ComposerWell test if required. Root owns this record/canvas, contract.md, tests/e2e/test_ask_glass.py, status/tracker/delivery. Worktree /Users/karol/dev/tools/wt-conversation-design-20261021, branch feat/conversation-design-20261021, base d1691b773f54e91a7b3cff4094b28b2b5a89ad66. Anchors drift; locate symbols. Other paths are do-not-touch.

HOLD FOR SHIP; no staging/commit, tests, build, typecheck or probes until root freezes tracked source. All checks via scripts/test_lock.py with isolated HOME; pytest -n8 --dist worksteal, never metal or owner writes. Test current Ask submit/stop/retry/durable/IME invariants, scoped PR composer single/multiline/capture, and real Firefox 1440/393 first-open/pending/answered states. Add a long real-Markdown answer and narrow engine/capture/action hit-ownership check. Required quick green -> PR merge -> exact main deployment -> postmerge independent review -> full tape. Preserve original report files. Do not claim flagship acceptance from green checks.

## Built verification

Focused Ask, PR receipt and speakable-desk checks pass 50 cases; typecheck and
collection pass. Both real private-Hub Firefox sizes pass long Markdown/code,
actual thread persistence, retained next-draft and narrow action/capture
ownership. Initial screenshots exposed default Button halo margins offsetting
the mic and action; the common species now resets those margins for its
already-44px controls. The engine/tools row wraps its text inside a bounded
column, and the opened disclosure spans that row. Prompt labels use the 15px
primary step and the real action/meeting sprites. Question ink uses the
Workbench selection token. All edits remain in the settled composition.

Setup MCP review helper returned launch_only (403) for this owner-started
session. The independent local Luna review is an AGENTS fallback, not
Muad'Dib's check. No launch credential is bypassed. Owner aesthetic judgment
remains open; green tests establish behavior and layout bounds only.

The first required product check passed build, 4,125 web cases, three real
Firefox/drag cases, 110 sweep and 1,116 repository guards. Its sole red was
the microphone ratchet: it did not yet name DeskComposer's explicit capture
transfer, so it counted both disabled gadget-default mics as missing voice.
The existing exact-field MIC_HOST_AUTHORITIES mapping now includes this host
field, still requiring an actual MicButton in the same function. Both editor
variants join the existing positive/negative cases: no mic, another component's
mic, another field and another path must all remain violations. No ceiling or
scanner coverage is relaxed. Final required quick checks this guard correction
against the already-verified, byte-unchanged web implementation.

## Post-merge fix-forward design

Review of #1422 found that Tools could shrink a scrolled reading viewport and hide the answer actions. The common reading-end anchor preserves the end across content/viewport resize only while the reader is at the end. A reader above the end keeps their position. This hook owns scroll presentation only.

The shared composer owns inner editor paper, typography, border, padding and resize; legacy PR textarea skin must not compete. Source review corrected adoption provenance: routes.tsx maps /companion to Agents; CompanionCore and its PR replies are parked. There is no live PR reply route to photograph, and this change does not revive it. Earlier claims of live PR adoption were inaccurate.

Before build, extend the existing /design/components gallery with a Conversation composer specimen: the same DeskComposer, multiline local controlled draft, one scoped microphone and a Preview action that changes local specimen output only. Keep the common canvas geometry and tokens, no new panel/chrome. Host it under the legacy desk-pr-compose class to exercise the competing cascade. Render and inspect this actual gallery route at 1440/393, label evidence as a specimen, and retain callback coverage for parked PR consumers. This is the reusable reference; it is not proof of live PR delivery or owner aesthetic acceptance.

Fix-forward focused verification: 55 web cases and typecheck passed. Seven
real private-Hub browser cases passed, including Firefox 1440/393. Long-answer
verbs remain completely in the reading viewport with Tools open; a reader at
scrollTop 80 remains there when Tools changes height. The actual component
gallery renders the shared editor as transparent, borderless 14px sans under
the legacy PR host class, with one mic and fully owned 44px capture/action hit
areas. Root inspected all four new Tools/specimen shots. These are gallery
specimens, not PR route screenshots. Required quick follows on frozen source.

The required repeat caught a delayed scroll event race after Tools closed.
The hook now samples the actual scrollTop before scheduling and before using
an anchor; unchanged-position resize events retain the old end state. A new
deterministic regression covers queued resize → direct position80 → resize.
56 focused cases/typecheck and all seven real browser cases pass with this
correction. The 4,130-case related web run passed its assertions but reported
an unrelated Send test's delayed scrollIntoView call, missing from jsdom.
That case now supplies only its own element's browser-method boundary and
awaits the saved-row reveal. No product Send code or check ceiling changes.
Final required quick covers this fixture correction against product commit
957737c8e; all other web source remains byte-unchanged from the product run.
