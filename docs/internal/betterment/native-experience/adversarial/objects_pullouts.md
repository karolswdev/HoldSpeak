# objects_pullouts

job: Open an object, inspect it and run an available object verb  
baseline: `55572802181d6a8045f6d27e3c722aaf5694dbbd` (anchors may drift)  
reviewer task: `review_objects_pullouts`  
evidence class: source, representative assertions, and named captures inspected; no tests executed, live walk, provider/native action, or owner observation.

VERDICT: DO-NOT-RATIFY

## Totality

The real job starts at a Desk icon, drawer row, citation, or deep link. The
owner selects one object, opens or raises its canonical window, inspects the
right material, runs an offered verb, sees a truthful outcome, and returns to
the same work. It includes stale/refused reads, retry, close/reopen, reload,
and draft preservation. The active route is spread across `web/src/desk/screen/Screen.tsx:104-136,207-291`,
`web/src/desk/store/compositorSlice.ts:265-339`, `web/src/desk/components/Pullout.tsx:74-145,153-169`,
and `web/src/desk/DeskApp.tsx:254-263`; the assigned source map does not follow
that end-to-end path. Multi-object commands are a separate collection job:
this family should explicitly remain a single-object inspection contract.

FINDINGS:

1. **P0 — registered is not active.** `web/src/desk/pullouts/registry.ts:21-47`
is compile-time coverage, not an opening contract. `PRIMITIVES` assigns
`pullout`, `window`, `surface`, or `none` (`web/src/lib/primitives.ts:471-699`),
and `openPullout` redirects before the registry (`web/src/desk/store/compositorSlice.ts:305-339`).
Several registry rows render `FallbackPullout`, whose only result is “No detail
view” (`web/src/desk/pullouts/FallbackPullout.tsx:6-17`); the cited
`docs/CAPABILITIES.md:44-47` is not an object capability. Cost: an empty card
or wrong application.
This fails Tenets 3 and 6. Correction: inventory every kind as specialized,
redirected, empty/unsupported, or absent, with its actual destination and
available verbs; never use registry exhaustiveness as behavior evidence.

2. **P0 — object identity does not fully converge.** Bare refs resolve by the
first matching kind (`web/src/desk/store/compositorSlice.ts:590-613`;
`web/src/desk/world.ts:100-108`), while qualified refs deduplicate by kind/id
(`web/src/desk/store/compositorSlice.ts:310-315`). The identity test covers
one pair and qualified collisions, not an ambiguous bare id or reload
(`web/src/desk/store/__tests__/pulloutIdentity.test.ts:25-70`). The cost is the
wrong workflow after collision or reordered data, failing Tenets 5, 6, and 7.
Correction: persist/open on `kind:id`, separate app/window/resource identity,
and assert collision, deep-link, and rehydration paths.

3. **P1 — verbs have no family-level outcome/return matrix.** The menu
constructs entries and calls `v.run` (`web/src/desk/objectMenu.ts:132-153,175-185`),
while registry verbs mix opens, editors, filing, and delete requests
(`web/src/desk/verbRegistry.ts:467-489,545-605,661-682`). A few bodies provide
retry/refusal (`web/src/desk/components/Pullout.tsx:153-169`;
`web/src/desk/pullouts/DecisionPullout.tsx:129-160,205-211`),
but tests prove dispatch, not outcomes, stale recovery, or return focus. This
fails Tenets 3, 6, and 7. Correction: map each verb to receipt, refusal,
retry, close, and return-to-work state.

4. **P1 — selected-set and legacy boundaries are underspecified.** Active
`objectMenu` replaced parked `floorMenu` (`web/src/desk/objectMenu.ts:1-3`),
`VerbContext` carries only one `selectedRef` (`web/src/desk/verbRegistry.ts:58-63`),
and the menu bar withholds itself unless selection is singular
(`web/src/desk/components/DeskMenuBar.tsx:84-99`). `ObjectList` can display a
set but exposes singular selection/open callbacks (`web/src/desk/surface/objects/ObjectList.tsx:87-95,118-125`).
Owner cost: a shared command can act on the wrong target or offer a dead set action (Tenets 3 and 5). Correction: state single-object pullouts plainly; hand set selection to
`explorer_repo`/`drawers` and test the explicit withholding/target rule rather
than inventing a universal multi-object pullout.

## Convergence

Converge with `windows` on compositor identity, front-window authority,
persistence, and raise/restore; first consumer: pullout reopen. Converge with
`explorer_repo` and `drawers` on scoped selection, resource identity, and
target-aware commands; they own multi-item views. Converge with `feedback`
and `notes_editor` on receipts, refusal, draft, and retry. Keep domain hosts
separate: one fallback would erase meeting, note, People, and editor semantics.

## User experience

Prior captures under `/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/` show a plausible fast path: `note-1440.png` has a quiet
object window with title, body, footer verbs, and local egress; `note-393.png`
keeps Back, Done, Feedback, and verbs reachable. This is capture inference,
not owner delight or accessibility proof. It says nothing about redirects,
fallback emptiness, stale reads, or safe return.

CONDITIONS: Add the 20-kind route table, canonical identity contract, verb
outcome/recovery/return matrix, and single-versus-set boundary assertions.
Do not add a second registry or window manager.

MISSED:

1. Redirected and fallback kinds, including an honest unsupported operation.
2. Bare-ID collision and reload/rehydration behavior.
3. Provider refusal, stale detail, retry, receipt, and focus return.
4. Multi-selection withholding and front-window versus selected-object target.

TUESDAY: A supported note appears quick in the named captures; arbitrary
objects are not yet dependable because routing, identity, and recovery are
unproved.

## Acceptance challenges

1. From a Desk icon at 1440 and 393, open one note, inspect it, run one offered
   verb, close/minimize it, and reopen the same `kind:id` window without losing
   its draft or front-window return.
2. Open a project, repository, workbench, and story ref; each lands in its
   declared active destination, while an unsupported detail view withholds its
   dead verb and names the limit.
3. Seed a note and decision with the same bare id; qualified opens produce two
   correct windows, and reload restores both identities and geometry.
4. Make a supported detail read stale or unavailable, retry it, then invoke a
   supported refusing verb; the object remains unchanged, the receipt names
   the outcome, and focus returns to the prior work.

UNKNOWN: No tests, builds, live Desk walks, provider/native actions, focus or
accessibility checks, performance measurements, or owner acceptance were
observed. Captures are prior named-state shots only; omission is not an
observed product bug, and parked code is not active proof.
