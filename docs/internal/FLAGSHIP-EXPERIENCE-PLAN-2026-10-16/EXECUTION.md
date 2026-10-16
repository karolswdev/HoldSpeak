# Delegation and first delivery

Active under the owner-invoked KICKOFF.md, 2026-10-16. The earlier planning
pause is superseded by that instruction. This operating model governs the
implementation; formal review and owner visual acceptance remain separate.

## Models and capacity

- One **Astra master orchestrator** owns design decisions, shared contracts,
  scope, independent review, integration, release and honest completion claims.
- Builders and bounded auditors use **Sol at HIGH reasoning**. The available
  worker identifier is `gpt-6.1-sol`, `reasoning_effort=high`. This follows the
  owner's current task-specific instruction rather than the older Luna default.
- This environment allows four concurrent agents including the root: **one
  orchestrator plus three workers**. Rotate finished worker slots into an
  independent integrated review. Do not imply more simultaneous capacity.
- If the owner launches an Astra root, that is the actual orchestrating model.
  A role label in a plan does not change a running session's model. No nested
  Astra layer or chain of sub-orchestrators is needed.

## Work in parallel where the dependencies permit it

Astra settles the reading hierarchy, source-open/status contract and component
examples before face implementation. During that short direction stage, three
Sol workers can independently inspect populated flagship composition, trace
source/lifecycle handoffs, and audit shared material/rendering. Their output is
concrete direction and build scope, not three incompatible visual systems.

The first substantive implementation batch is **Brief and connected source
reading**, with meaningful supporting changes in Day/Follow-through/Memory and
the shared Markdown material. Its three lanes are:

1. **Flagship composition.** Own Brief/Day composition and local intelligence
   layout. Implement the settled type hierarchy, readable grouping, source
   placement and narrow-window sequence. Preserve stored facts and source IDs.
2. **Source journeys.** Own exact source reads, lifecycle-aware focus, task
   inspection and visible failures. Integrate the retained candidate only after
   validating it. Own Follow-through behavior and affected API/opener files.
3. **Shared reading material.** Own the existing Markdown material component,
   document styles and bounded Codex asks adapter/normalization repair. Support
   tables and the document structures used by actual agent replies. Supply
   agreed classes/API early so the composition lane can integrate them.

The concrete brief names exact files and do-not-touch paths. A shared file has
one owner. Resolve API/props early; independent internals can then proceed in
parallel. Root decides cross-lane amendments quickly and records them. Lanes
finish a complete unit and hold for SHIP; they never commit or merge.

A future batch rotates the same three slots into daily work, conversation/
execution and supporting surfaces, as the parent plan sequences them. Maintain
one product direction across those batches.

## What each worker receives

- The owner's job and specific current evidence.
- The accepted actual-library composition and exact expected behavior.
- Named worktree/branch, source anchors with drift warning, exclusive files
  and other lanes' boundaries.
- A bounded implementation scope and the smallest relevant check budget.
- Actual outcomes to demonstrate, known limitations and HOLD FOR SHIP.

Workers implement the design. They report a missing seam or new abstraction
requirement instead of independently expanding the system. Keep reports short:
changed behavior, proof, limitations, ready/pending. Retire a worker if repeated
rounds grow into open-ended investigation; pass settled facts to a fresh worker.

## Integration and release

Independent source/design work runs in parallel. **Machine-heavy checks run
serially under the repository lock.** Workers can continue unrelated code or
document work while one focused check runs. Do not run three browser/build
jobs against the same machine to create the appearance of speed.

When the three lanes freeze, an independent Sol reviews the integrated journey
and visual result. Astra reads the actual before/after shots and named outcomes
and makes the done call. The ordinary quick check precedes merge; formal Astra/
Muad'Dib review and the main tape follow the current postmerge cycle.

Deliver one substantial, reviewable PR for the connected experience. Show the
owner paired current before/after faces plus the exact click→source→action→
result→return walkthrough. Deploy the exact verified build. Report any remaining
source, hardware or provider unknown separately. The release unit is the useful
experience; worker lanes are implementation boundaries.

## Markdown defect acceptance

The owner's Codex asks screenshot shows headings and a pipe table inline inside
a long paragraph. Strong text renders; block structure does not. Source-confirmed:
AskWell uses AgentWords (`surface/objects/AskWell.tsx:91`); its block model has
no table. Codex Stop capture (`holdspeak/agent_context/sessions.py:261`) and
transcript capture (`:1017`) join split whitespace before storing the question,
destroying block boundaries. Material is a separate subset renderer and also
lacks tables. Repair both capture and rendering; a CSS-only change or swapping
AskWell to Material would not restore the original structure. [Bounded renderer audit](MARKDOWN-AUDIT.md) records that trace.

The fix is complete when the actual affected Codex asks host displays:

- Distinct headings, paragraphs and lists from the original reply.
- Real table headers/cells and readable alignment; long cells wrap.
- Code fences/inline code as code rather than prose.
- Meaningful link labels. Supported object/repository targets use existing
  openers; unsupported or deliberately inert agent targets remain explicit
  without masquerading as working links. Do not implicitly execute agent text.
- A table-local scroll well when the table cannot fit a narrow window.
- Reachable question/response controls, unchanged original payload and no
  modification to the approval/decision meaning of the host.

Use the existing shared document material; choose an existing capable parser
if the dependency inventory offers one. A second Markdown skin or a growing
collection of ad-hoc pipe regexes would make consistency harder to maintain.
CodeMirror Markdown syntax support is already installed and is one candidate;
its presence alone does not settle its suitability as a document renderer.
Choose the smallest maintainable solution after checking the actual rendering
requirements. Preserve compact agent summaries as a separate presentation of
the same original text. Previously captured flattened questions cannot recover
original structure unless their original retained source is available; label
that recovery limit rather than guessing missing newlines.
