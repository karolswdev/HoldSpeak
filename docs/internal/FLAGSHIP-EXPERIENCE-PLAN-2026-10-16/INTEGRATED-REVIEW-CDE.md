Independent Sol counsel — 2026-10-16. Final integrated review and bounded
recheck; this is not Muad'Dib's check or the owner's visual acceptance.
Reviewed source, focused assertions and recorded run outputs, actual observation
records and representative state PNGs. No product implementation, test, build,
browser, staging, commit or owner-state operation was performed by this reviewer.

VERDICT: RATIFY

FINDINGS:

1. **Resolved — restored task commands could invoke Keep. Tenet 3.** The first
   actual return shot showed an unrelated slash palette over a retained `/todo`
   (`.tmp/flagship/creation-after-desktop-4/todo-refused-return.png`). The new
   completion refresh had evaluated a remounted field at cursor zero.
   `web/src/desk/components/ThreadComposer.tsx:163` now requires the cursor to
   follow the slash. Rendered regression coverage at
   `web/src/desk/__tests__/ThreadComposer.test.tsx:508` checks exact task dispatch,
   no Keep call and duplicate blocking only while pending. Final
   `.tmp/flagship/creation-release-{desktop,phone}/observation.json` and
   `.tmp/flagship/creation-release-narrow-2/observation.json` record cursor zero,
   exact Enter dispatch and no Keep. Read the final refused-return/keyboard PNGs:
   the stray palette is gone.

2. **Resolved — replacing all People input closed the editor. Tenet 3.**
   `web/src/pages/cores/PeopleCore.tsx:764` now opens retained drafts without
   closing an empty field. Closing after acceptance is explicit and belongs to
   the unchanged submitted snapshot. The three-field regression at
   `web/src/pages/cores/__tests__/peopleCore.test.tsx:97`, the 40-pass
   `.tmp/flagship/daily-people-clear.log`, and final daily observations prove
   empty editing stays open and focused. Newer agenda words survive the delayed
   genuine accepted Add, tab return and the Project round trip.

3. **Resolved — narrow fields and a Remote grant control lost useful space.
   Tenets 3/5/6.** People now composes a full-row gadget under the named surface
   container (`web/src/pages/cores/people.css:545`); Remote uses the existing
   wide/full GadgetRow (`web/src/pages/cores/SettingsCore.tsx:1108`). Read final
   `.tmp/flagship/daily-release-phone-2/agenda-pending.png` and
   `they-owe-detail.png`: editable words, mic and separate actions fit. The
   observation measures a 311-pixel gadget, 265-pixel input and 44-pixel controls.
   `.tmp/flagship/remote-release-phone/expanded-grant-control.png` shows the full
   grant action; its observation records all nine hit samples owned. The actual
   Remote 600-pixel capture also fits.

4. **Resolved — recovery tokens and subjects ran together. Tenets 3/4.**
   Explicit separators now distinguish task state, exact command and reason
   (`web/src/desk/components/ThreadComposer.tsx:915`), with the same correction
   for choice failures and Ask. Read final creation `todo-unknown.png`,
   `todo-refused-keyboard.png` and `ask-projects-failed.png` at desktop, phone and
   actual 600-pixel width. The text wraps clearly. Geometric reader flags around
   inline notice containers are not visible collisions in those inspected PNGs.

No open product finding remains in this bounded review. Final quick output
`.tmp/flagship/quick-cde-release.log` is GREEN: 4104 web tests across 417 files,
109 desk-sweep checks and 17 canon checks. Focused Thread/Ask correction output
`.tmp/flagship/d-run-keyboard.log` records 93 passed. Remote's focused 16 and
three conditional preservation tests were also read. These totals support
behavior; the actual images support the layout judgment.

CONDITIONS: None for the bounded C/D/E ship candidate.

MISSED:

1. Highest owner cost was the remount Enter action changing from the retained
   task to Keep. It is fixed and verified above.
2. Input continuity and phone control space were next: empty replacement lost
   focus, People fields squeezed, and the expanded grant action clipped. Each
   is fixed in the existing component composition.
3. Joined recovery text obscured which command or reason belonged to a state.
   The final actual notices resolve it.

The accepted scope preserves the previously healed #1215–1219 journeys.
Dormant Ambient Approve/Decline remains excluded; no fabricated local proposal
card establishes a new active path.

TUESDAY: Yes for the inspected job: prepare for the report, inspect either exact
obligation, finish the waiting Project Review, retain the next words, create a
Thread task and recover named reads without claiming a write was retried.

UNKNOWN:

- Final daily records are `.tmp/flagship/daily-release-phone-2/`,
  `daily-release-desktop/` and `daily-release-narrow/`; final creation records
  are `creation-release-desktop/`, `creation-release-phone/` and
  `creation-release-narrow-2/`. All record start/end build
  `a7145045f5dbab3c`, built `2026-10-16T19:30:18.728Z`, and no page errors.
  Narrow People is actually 600 pixels; Project remains at its supported
  800-pixel minimum. A 600-pixel desktop Project is not claimed.
- Final Remote phone repeats on that build. Desktop and actual 600-pixel Remote
  proof remains the product-identical `remote-after-1440-complete/` and
  `remote-after-narrow-complete/` records on `527eba20a62b65ff`. Named injected
  HTTP 503 console entries are the declared fault boundaries, not page errors.
- The local tool produces real task rows and receipts. A declared refusal stops
  before dispatch; a real dispatch followed by disconnect leaves the UI
  unknown, retains the command and causes no automatic replay. Only pending
  blocks Send. A later explicit Send can create another task because the
  endpoint is non-idempotent. This review promises no replay guarantee.
- Recorded imported assistant Markdown proves reading, actual Keep, exact
  artifact lineage/source opening and reopen. It proves no new provider turn.
  Native microphone/keys/clipboard, external delivery, real remote devices,
  provider execution, physical performance and the owner's judgment remain
  outside this isolated proof.
- Merge, live deployment, the full main tape and formal Astra postmerge review
  are separate release work; this counsel does not report their outcome.
