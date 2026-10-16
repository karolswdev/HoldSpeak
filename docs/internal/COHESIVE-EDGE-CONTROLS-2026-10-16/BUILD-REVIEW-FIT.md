# Review Edit and Defer fit

Status: built; frozen, HOLD for SHIP. Root accepted both canvas widths before
the product edit. No staging or commit by this worker.

Tuesday: edit a proposal, choose a defer date, cancel defer, and keep the
latest edit draft. Tenet 3 requires every action to remain reachable.

Root's observed 393 failure is in
`.tmp/edges/review-fit-before-stable/observation.json`: Cancel defer extends
to x429.6 and Dismiss to x481.6. The outer toolbar and armed defer group do
not wrap; Save and accept and Cancel edit shrink to 44 px and break words.

Settled direction: keep the library Buttons at their natural width, wrap
the toolbar under the narrow `surface` container, give armed Defer a full
row that can wrap, and give the native date input the square kit material
and 44 px height. Preserve native picker, autofocus and keyboard behavior.

Canvas uses the real ReviewPosture and library window with a local specimen
controller. No hub calls or decisions. Reviewed shots are local at
`.tmp/edges/canvas-review-fit-shots/review-edit-defer-1440.png` and
`review-edit-defer-393.png`; their geometry is in `observation.json` beside
them. All six armed toolbar controls fit at both widths. At 393, all Buttons
are 44 px tall and keep their natural widths and unbroken labels; the native
date is 168 by 44. Desktop Buttons retain their 28 px height. These are
direction captures, not actual product task proof. No PNGs enter the commit.

Product changes are limited to review-posture.css's verb/defer/date rules.
The native input, picker, autofocus, event handlers and controller stay in
place. The focused regression suite uses the existing test harness and its
boundary doubles. Three added cases prove: Cancel defer retains Edit and
submits the latest draft; Escape closes Defer before Edit and Review with no
decision; Enter on the native date submits the exact date once.

Proof read by the worker:
- `.tmp/edges/review-fit-collect.log`: 19 named tests collected before run.
- `.tmp/edges/review-fit-run.log`: 1 file, 19 tests passed, 3.08 s.
- `.tmp/edges/review-fit-canvas.log`: 1440/393 direction captures, all six
  controls visible and no page errors.
- Scoped `git diff --check`: clean.

Root owns actual task, pointer and keyboard observations and the complete
quick check. Actual 393 by 852 fit and pointer ownership remain pending at
this handover; the body can scroll as needed. No claim of real decisions or
owner-desk use comes from this worker's tests or canvas.
