# components_reference — adversarial review

WORKFLOW ID: components_reference  
JOB: Demonstrate the same application behavior with isolated fixture data  
BASELINE: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (source anchors may drift)  
REVIEWER TASK: `review_components_reference`  
EVIDENCE CLASS: source, representative assertions and existing captures; no execution or owner walk

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job should open Components, select a pattern, exercise the same identity,
selection, command, edit and outcome semantics as production, then return with
fixture state intact. Data and effects may be isolated, not the contract. The
application model asks for the same app/view models with fixture adapters
(`docs/internal/betterment/native-experience/APPLICATION-MODEL.md:153-176`).

The current surface is a useful catalogue, not that end-to-end brief.
`ComponentsCore` only mounts `DesignReference`
(`web/src/pages/cores/ComponentsCore.tsx:5-10`); the reference keeps pattern
and state in local React state (`web/src/pages/cores/design-reference/DesignReference.tsx:439-455`),
while rows and identities are hard-coded in `ObjectSpeciesGallery`
(`web/src/pages/cores/ObjectSpeciesGallery.tsx:35-126`). The audit needs a
sharper boundary between catalogue and shared behavior.

FINDINGS:

1. **P0 — No fixture-adapter seam is defined or evidenced.** The source has
   local specimen state and no app/view model or typed adapter boundary
   (`DesignReference.tsx:31-37,439-455`; `ObjectSpeciesGallery.tsx:35-126`).
   Owner cost: a polished reference can drift from Settings, RepoWindow or
   Ask while passing its own tests. This fails Tenets 2, 3, 5 and 6.
   Correction: define the smallest adapter contract from a real consumer
   (identity, selection, commands, edit state and outcome), feed Components
   through it, and name the first production consumer. Keep provider authority
   and effects out of the fixture.

2. **P0 — The acceptance evidence proves local controls, not application
   convergence.** The glass test itself limits its claims to icon/row
   activation, accessibility columns, arrow geometry, lamps, material and
   44px rows (`tests/e2e/test_components_glass.py:13-32,160-208`); page tests
   exercise local save/retry/reset only
   (`web/src/pages/ComponentsPage.test.tsx:34-142`). None falsifies per-window
   identity, history, command target, stale response, supported edit or
   return-to-work behavior. Owner cost: the reference can look
   trustworthy while Tuesday still fails (Tenet 7). Correction: map assertions
   to `explorer_repo`, `settings`, `windows`, `navigation_commands` and
   `feedback`, then prove one supported fixture path through the same model and
   one named production consumer. Do not fake filesystem operations.

3. **P1 — The happy path is expensive to discover at narrow width.** The
   Controls renders one very long sequential catalogue
   (`web/src/pages/cores/design-reference/ControlsGallery.tsx:128-472`). The
   existing 393 capture shows Object species only partly visible above the
   footer
   ([patterns-393.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/design-reference/patterns-393.png));
   ([surface-components-1440.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-components-1440.png)).
   This mid-scroll capture does not prove the content is unreachable. Owner cost:
   an architect looking for one species must hunt and cannot tell
   what is shared versus decorative. This fails Tenets 3 and 6. Correction:
   retain one window, add stable in-window target navigation and a visible
   scroll affordance, and prove a selected target at 393 without a new route.

## Convergence

Converge with `explorer_repo` first for typed resource identity, per-window
selection/history, commands and outcomes; its provider remains authoritative.
Converge with `settings` for dirty/pending/rejected/retried/saved edit state,
and with `ask_whole_desk`/`threads` for composer retry and draft preservation.
`people_prep` and `meeting_archive` later consume the same list/detail and
restoration contract. Reuse `ObjectList` row ids/selection props
(`web/src/desk/surface/objects/ObjectList.tsx:80-115`) and the one verb registry
(`web/src/desk/verbRegistry.ts:1-12,58-105`). Do not merge these into a fake
“reference app”: domain adapters, provenance, permissions and specialized
editor/terminal behavior stay separate.

## User experience

Forms is legible at 1440 and 393, and its receipt/action relation scans well.
The illustrated species are credible, but Controls turns lookup into scrolling.
This is a capture judgment, not owner delight or accessibility proof. Tuesday
is “choose, inspect, try, return”; today it is “choose, hunt, trust local.”

CONDITIONS: Define the fixture adapter with one real consumer; map acceptance
for identity, selection, commands, edits,
outcomes and return; add narrow target navigation and a 393 target capture.

MISSED:

1. Shared-versus-local identity and per-window state (highest cost).
2. Production parity for `settings` and `explorer_repo`, including stale and
   refused outcomes.
3. Keyboard/voice edit semantics and focus return after retry.
4. A fast, discoverable narrow-width lookup path through the catalogue.

TUESDAY: Not yet—the owner can inspect attractive local specimens, but cannot
rely on Components to demonstrate the behavior he will use in a production
window.

## Acceptance challenges

1. With the adapter and the same form pattern mounted in `settings`,
   edit a field, trigger a delayed save, make a newer edit, and verify the
   captured write does not replace the newer draft.
2. Open two supported fixture windows from `explorer_repo`; navigate
   one, switch focus, and verify independent location, selection and scroll.
3. Select a supported fixture row, sort it, and invoke its available command
   by pointer and keyboard; the command must target the same stable identity,
   or be visibly unavailable with its reason.
4. Force a supported local save/reply refusal, retry the captured request, and
   verify the newer draft remains and the receipt names the outcome.
5. At 393, choose Controls, jump to Object species, exercise one supported
   control, and verify target/result remain visible above the footer; return
   without resetting unrelated state.

UNKNOWN: No tests were executed. No live Desk, provider, native, assistive
technology or performance run, or owner acceptance, was observed. Captures are
named-state/viewport evidence, not proof of adoption, accessibility,
performance or delight.
