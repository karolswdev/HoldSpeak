# Shared surfaces — root audit

Base main eb9a3266e. Source review plus dedicated desktop Settings captures.
These are isolated-hub observations, never the owner's desk.

## Observed slices

Settings Voice, Accounts → actual Add destination, and People settings were
opened at1440. Root read Voice and Accounts captures. Voice has its controls
and Settings return; Accounts keeps the existing wings and a real destination
form. The missing Accounts footer Back is not a trapped-screen finding:
the Settings wing already returns to the hub. No new defect is claimed from
those slices. Shots: `.tmp/deep-usability/root-shots/`.

Two capture setup attempts were spent. The first used a nonexistent frame
attribute and was interrupted, rather than spending repeated timeouts. The
second used the real front-frame class, obtained the three desktop poses,
then failed because Ask is a special host and refuses the ordinary hub window
open endpoint (HTTP400). Ask and these Settings phone poses remain unobserved
in this supplementary audit. Neither failure is a product defect. No API
failure or observation was edited into a pass.

## Source findings to verify, not delivered behavior

`web/src/desk/components/GroundingSection.tsx` renders raw buttons around
CheckGadget controls in meeting and resource rows (:208 and :351), despite
its own comment saying the checkbox is the one focusable control. This
violates the library control grammar and creates two keyboard targets per
choice (Tenets3/5, UXA.1). Async `toggleMeeting` (:87) and `toggleResource`
(:104) both merge from the selection captured before their fetch resolves;
quick concurrent choices can overwrite a newer selection. This is a source
trace, not an executed owner interaction. Resolve with a focused component
reproduction before any behavioral claim or build brief. Do not introduce
another selection store or change grounding authority.

Ask's Add notes Disclosure contains a second Ground this ask fold in the
shared GroundingSection. The extra reveal and resource-failure feedback
require a real special-host walk before deciding a composition change.
No new Ask task, account operation, inference or external delivery ran.

## Integration checks

Root independently inspected the agents' actual before images for Person
Context, Room refusal, Workbench draft return, and Knowledge text before and
after reload. These show meaningful work loss/obscured content, not only a
style mismatch. Canonical Knowledge is a collection; its unsupported body
textarea is the wrong editor, not a reason to create another document backend.
The repair preserves existing draft and membership authority.

## Shared selection reproduction and bounded fix

Focused component reproduction now confirms both source findings. After two
resource reads complete in reverse order, the rendered selection contains
only Alpha; Beta was silently overwritten. The same component renders its
checkboxes inside raw buttons. The initial test harness needed the native
details toggle to settle; that setup failure was not counted as a defect.
Actual red log: `.tmp/deep-usability/grounding-repro-r2.log`.

Root repaired this diagnosed seam locally: resolve into the current selection,
publish that selection before another completion can merge, avoid duplicate
refs, and keep each existing CheckGadget as its single keyboard control.
The visual row grammar and grounding wire/authority stay the same; outer
noninteractive row containers no longer nest inputs inside buttons. No new
selection store or navigation. Two focused files now pass19 tests
(`.tmp/deep-usability/grounding-fixed.log`). This is controlled component
evidence, not a real inference result. A real Ask selection walk follows.

## Close and failed-read integration seams

The Create lane found the frame starts departure animation before invoking
its old onClose callback. A writer that refuses that later callback can leave
a window visually departed. Its optional local beforeClose guard now runs
before departure, deduplicates pending closes and permits retry after refusal.
Normal-motion focused coverage supplements reduced-motion browser checks.
Root wired the existing Thought writer to that same guard; it flushes and
returns acceptance before the frame closes, preserving its failure/release
behavior. No second writer or navigation policy was added.

The Operate refusal walk also found an accepted Workbench item disappears
when a following aggregate collection read fails. The local window now keeps
its authoritative loaded detail. Root traced the shared failed-read bucket
replacement and delegated a bounded loader/store correction: keep existing
objects on classified transient read failure, retain the named failure, and
still honor authoritative empty reads and 401/403 refusals. The existing
first-ranked error alone cannot classify mixed failures, so the loader adds
only the needed optional per-kind transient classification. No backend or
new store is introduced. Focused proof is recorded in shared-read.md.

## Actual Ask selection — final isolated walks

`case.deep.ask.sources` in `atlas-deep-usability.json` passed at 1440 and
393: actual Search → Ask → Add notes, two real Note producers, both choices
checked after production `/api/grounding/resolve`200. Root read observations
and after shots; both terminal predicates settled, no console errors. The
reverse-order race is established separately by the controlled regression;
these live walks do not control response order or run a model.

- 1440: `.tmp/graph-walk/deep-usability/ask-1440/20261014T225028Z-case.deep.ask.sources-astra-1440/`.
- 393: `.tmp/graph-walk/deep-usability/ask-393/20261014T225543Z-case.deep.ask.sources-astra-393/`.

The phone shot also exposes a pre-existing summary tail: the long Grounded
on heading truncates before the object count and includes a zero Meeting
count. Selected objects remain readable and checked. The heading needs a
compact/no-zero pass; these action checks do not establish that every shared
Grounding pose is finished.

## Integrated audit metadata repair

The first combined check passed3717 web tests,107 sweep cases (2 existing
xfails) and15 canon guards, but its550 Python checks had3 failures. Root
corrected the new case's route-edge category, declared wall clock and explicit
Button selector, plus two old source snippets moved by the editor repair.
No test/schema fence was weakened. The exact focused rerun passed550/550
(`.tmp/deep-usability/graph-metadata-fixed.log`). Final Ask cases and the whole
combined quick check are rerun against the corrected definition.

Final corrected-definition Ask runs both passed and settled with real
`/api/grounding/resolve`200, both selected Notes, no enclosing input/button
and no console errors. Root read both observations and both after shots.
Final paths:

- `.tmp/graph-walk/deep-usability/final-ask-1440/20261014T230353Z-case.deep.ask.sources-astra-1440/`.
- `.tmp/graph-walk/deep-usability/final-ask-393/20261014T230403Z-case.deep.ask.sources-astra-393/`.

Frozen-source TypeScript also passed after the last Schedule/chrome changes
(`.tmp/deep-usability/final-types-frozen.log`).

## Final integrated release check

`quick-release-console.log` ends QUICK CHECK GREEN. Root read the actual
retained logs: build passed;407 web files/3717 tests;550 affected Python
checks;107 sweep cases and2 existing xfails;15 canon checks. All source was
frozen before this run. The separate frozen-source TypeScript and metadata
generator also passed. Logs live in `.tmp/deep-usability/quick-release/`.
The original red metadata result is retained above; no failure was waived.
