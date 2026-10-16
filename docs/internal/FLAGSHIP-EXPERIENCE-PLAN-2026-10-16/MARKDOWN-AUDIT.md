# Markdown audit — 2026-10-16

**DRAFT / UNCHECKED — awaiting Muad'Dib.** Read-only source audit during
the owner's planning pause. Base: `ebfce9feb`. No product changes, tests,
builds, browser sessions, or owner-state reads. Existing candidate edits
and this plan's README were not changed. Anchors describe the inspected
worktree; check them for drift before briefing implementation.

## Finding

The screenshot's `CODEX ASKS` text has three distinct causes: capture
destroys Markdown line boundaries; the agent renderer has no table
support; its link policy explicitly prints destinations as inert text.
Changing font or substituting Material will not resolve these causes.
This fails Tenets 3 and 7: the owner cannot scan an agent's plan or follow
its source. The duplicate document grammars fail Tenet 5.

## Source-to-render trace

| Stage | Source evidence | Observed source behavior |
|---|---|---|
| Codex Stop capture | `holdspeak/agent_context/sessions.py:259–262` | `" ".join(last_assistant_message.split())` removes every newline, indentation and repeated space, then keeps the capture limit's trailing characters. |
| Transcript capture, both supported agents | `holdspeak/agent_context/sessions.py:987`, `:1017–1019` | The extracted latest assistant message is also joined with spaces before truncation. Fixing only Codex Stop leaves this second loss path. |
| Pending question | `holdspeak/agent_context/sessions.py:342–348`, `:158–168`, `:380` | Codex's last message becomes the secret-filtered `question`; filtering trims edges. Preserve the filter and capture bounds when preserving structure. |
| Frontend session mapping | `web/src/desk/steering.ts:54–61` | `question` passes through unchanged. |
| Coder mapping | `web/src/desk/api.ts:582–602` | Question selects identity question, session question, last question, assistant text, then an awaiting prompt. No Markdown parsing here. |
| Session surface | `web/src/desk/components/SessionPullout.tsx:772`, `:675–695`, `:841` | Question passes to SessionAnswerWell and then AskWell. Latest report also uses AgentWords at `:843`. |
| Lane surface | `holdspeak/services/launch_lane.py:286–287`; `web/src/desk/lane/LaneWindow.tsx:397–418`, `:441–449` | Lane wait carries the same question; answer waits use AskWell, other wait text uses AgentWords. |
| Screenshot caption and body | `web/src/desk/surface/objects/AskWell.tsx:79`, `:88–91` | `${agent.toUpperCase()} ${word}` produces `CODEX ASKS`; full AgentWords renders the question. |
| Coder object | `web/src/desk/pullouts/CoderPullout.tsx:78–79` | Full AgentWords renders `ir.question`. |
| Conductor overview | `web/src/desk/conductor/ConductorWindow.tsx:582`, `:472–473` | Session question uses compact AgentWords, three lines. This overview deliberately differs from the full reading surface. |
| Current attention rows | `web/src/desk/needs/needsFace.ts:305`; `web/src/desk/surface/objects/NeedsRow.tsx:56`; `web/src/desk/chair/ChairHome.tsx:2850` | Rows use the question as their fact and compact AgentWords. `web/src/desk/components/AttentionDrawer.tsx:1–2` is only a re-export of the parked drawer; do not mistake it for the active entry point. |

The screenshot's precise owning window cannot be proved from its caption
alone: Session and Lane both compose AskWell. The capture loss and renderer
behavior are source-confirmed. Their correspondence to the screenshot is
an inference; no live payload or DOM was inspected.

`humanizeWireValue` (`web/src/lib/productLanguage.ts:258–264`) normalizes
labels. In SessionPullout it formats the state at `:779`, not the question.
`plainReceipt` (`web/src/desk/conductor/ConductorWindow.tsx:289–291`)
changes receipt casing only. Neither is on the inspected full-question
render path. Do not “repair” headings by guessing where a flattened string
once had newlines: structure must survive capture.

## Shared document gaps

**AgentWords.** `web/src/desk/components/AgentWords.tsx:38–47` defines only
paragraph, heading, list and code blocks. The heading regex is anchored to
a complete line; after capture collapse, a midparagraph `###` stays text.
No table production exists in `parseAgentWords` (`:50–112`). Links become
label + space + destination (`:182–193`), and destinations render as spans
(`:346–350`), so the absolute local path is intentional current behavior.
Full headings render as `strong`, losing heading semantics and depth
(`:364–370`). Lists retain only one nested level (`:33–36`, `:89–92`).
Fenced code already exists (`:60–67`, `:373–378`), but capture loss prevents
its recognition. Code currently wraps anywhere (`agent-words.css:47–57`).
Compact mode has deliberate ask selection and truncation (`:282–308`,
`:637–640`); preserve that product behavior while sharing parsing.

**Material.** `web/src/desk/surface/Material.tsx:70–107` has only headings,
flat lists and paragraphs. It joins paragraph lines with spaces (`:79`),
does not recognize fences or tables, trims indentation, and renders all
heading levels as `strong` (`:124–128`). Link behavior differs: known
`door:` destinations use the library Button, HTTP(S) destinations use an
anchor, other destinations become bold labels (`:46–61`). Preserve real
note doors (`:14–20`) when consolidating.

Material reaches notes, artifacts, decisions, Ask answers, published
updates, preparation briefs, tool previews and completed thread turns
(for example `NotePullout.tsx:471`, `ArtifactPullout.tsx:30`,
`DecisionPullout.tsx:188–194`, `AskPanel.tsx:454`,
`UpdatePosture.tsx:266`, `PreparePosture.tsx:490`). Completed threads switch
to Material (`ThreadPullout.tsx:95–101`); the nearby comment promises code
and Mermaid finalization that this renderer does not implement. Treat
Mermaid support as a separately settled requirement, not a promise of this
Markdown fix. Plain streaming text is intentional current behavior.

## Smallest coherent implementation plan

1. **Capture owner:** preserve line breaks and code indentation in both
   capture paths in `holdspeak/agent_context/sessions.py`. Keep filtering,
   capture bounds and lifecycle behavior. Previously flattened stored text
   cannot be reconstructed reliably; the next captured turn can carry the
   correct source.
2. **Shared reading component owner:** give Material and full AgentWords
   one document parser/render implementation in the component library.
   Keep their existing public entry points as adapters during migration;
   keep compact AgentWords' ask selection and width behavior. Do not build
   a third regex grammar. `web/package.json:43` already depends on
   `@codemirror/lang-markdown`; DeskEditor uses `markdown()` at
   `web/src/desk/components/DeskEditor.tsx:251`. The installed package's
   `dist/index.d.ts:12–15` exposes `markdownLanguage` with GFM, and installed
   `@lezer/markdown/dist/index.d.ts:559–587` describes Table/GFM. This is an
   available parser candidate, not a settled implementation choice: evaluate
   whether a small React adapter can meet the document contract without
   custom AST machinery. A syntax parser is not an existing complete
   document renderer. Settle that choice in the worker brief against
   Tenet 1; do not add a parser or framework merely because neither current
   renderer handles tables. No react-markdown, remark-gfm or marked
   dependency appears in the inspected package manifest.
3. **Reference opening owner:** supply the shared renderer's link policy.
   Preserve labels, route supported local references through the existing
   repository reference opener, preserve known note doors as library
   Buttons, and apply the app's settled external-link behavior. The
   current AgentWords policy deliberately prohibits press targets; replace
   it explicitly in the ratified design. This audit did not verify a local
   reference opener and cannot claim one already works.
4. **Face owners:** consume the shared renderer; do not implement per-app
   tables, code or links. Extend component contract and canvas examples
   with the reading species. Order: capture and document contract, reference
   policy integration, full reading adapters, then consumer proof. Keep
   unrelated paused product edits out of these lanes.

The reader needs semantic headings, lists and tables; preserved code
whitespace; wrapping long labels; and contained table/code overflow.
At 393 a wide table must scroll within its own announced well rather than
widen the window or erase column relationships. Keep code readable and
copyable without inserting changes into its source text. Compose existing
library affordances, including ScrollHint and Button, where needed.

## Acceptance for the later build

- A fresh multiline Codex Stop payload and a captured Claude/Codex
  transcript retain paragraphs, headings, list indentation, table rows and
  fenced-code whitespace through their actual question/report routes.
- The owner's representative plan renders headings, bold, nested lists,
  a pipe table, fenced code and labelled local/HTTP references in AskWell,
  full Coder/Session/Lane text, and Material consumers. No literal block
  markers remain for supported valid syntax.
- Compact Conductor/attention/receipt rows retain deliberate ask selection,
  bounded height and an honest truncation indicator; opening the row shows
  the full structured source.
- Local link text stays the human label and opens the intended repository
  reference. Unsupported destinations have a settled visible treatment;
  known note door Buttons continue to open their existing doors. Arbitrary
  HTML remains text and images do not silently trigger remote fetches.
- At 1440 and 393, long paths, tables and code stay inside the reading
  region; list hierarchy and table headers remain understandable, and
  scrolling content announces itself. Capture later shots from an isolated
  rig under the repository's live-walk procedure.
- Later focused proof covers capture preservation, shared parsing/rendering,
  link activation and compact consumers. No validation was executed in this
  bounded audit. Product work remains paused.

**Tuesday:** the owner must be able to read the plan as a document and open
its named source without decoding Markdown syntax or copying an absolute
path.
