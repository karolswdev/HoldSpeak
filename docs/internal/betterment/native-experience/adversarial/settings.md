# settings

Job: Edit preferences and keep unsaved work visible  
Baseline: `555728021` (worktree `/Users/karol/dev/tools/wt-workflow-adversarial-20261023`)  
Reviewer task: review_settings  
Evidence class: worker source/assertion/capture review, then root isolated jsdom reproduction; no live Desk or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts from Go, menu, palette, a legacy route, or Accounts. Those doors converge on `configure-settings` / `surface-settings` (`web/src/desk/applications.ts:187-213`). Settings loads settings, hub, authority, and calendar facts; the owner chooses a section, edits a gadget, sees a receipt, and continues work. The job also includes refusals, optimistic concurrency, hidden-tab flush, return to the tab, and proving the value remains.

The family audit names only the form and says that focus, command context, and conflicts need shared rules. It does not bound work handed to Engines, Setup, or Accounts, and does not cover resumed tabs or stale revisions with a visible draft. “One manifest window” is not an end-to-end contract.

FINDINGS:

1. **P1 — dirty state is not visible during the debounce.** `updateMany` installs the local value and waits 700 ms before enqueueing (`web/src/pages/cores/SettingsCore.tsx:1628-1636`), but it never marks a dirty state. The footer then renders the previous `Saved HH:MM` receipt whenever `saving` is false (`web/src/pages/cores/settingsPrefs.tsx:724-736`). Cost: a tired architect cannot tell whether a change is only local; a reload or handoff can erase confidence. This fails Tenets 3 and 7. Correction: expose a pending/unsaved state immediately, suppress the old Saved receipt until every pending path is confirmed, and keep the state through section changes and leave flush.

2. **P1 — return after a hidden-tab flush can silently lose a later conflict.** The leave path sets `leaveSentRef` permanently and sends a revisionless keepalive (`web/src/pages/cores/SettingsCore.tsx:1645-1659`). Any later 409 is treated as the expected leave race and does not enter `failedChangesRef` (`web/src/pages/cores/SettingsCore.tsx:1592-1609`). The only assertion covers one-way pagehide, not hide/show followed by another edit (`web/src/pages/cores/__tests__/settingsLeave.philo17.test.tsx:50-70`). Cost: the owner returns to the desk, edits, and can lose that value without a refusal or Retry. This fails Tenets 3 and 7. Correction: scope the suppression to the exact leave request, reset it on visible/pageshow, and preserve every later 409 as a visible draft plus Retry.

3. **P1 — the audit does not establish the application boundary or durable identity.** Settings links Engines and Setup rather than owning them (`web/src/pages/cores/SettingsCore.tsx:2679-2686`), while the inventory declares only `settings` with partial evidence (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2968-2998`). Cost: duplicate writers or a Settings-owned framework, failing Tenets 1, 3, 5, and 7. Correction: specify `settings` as use-case id, `configure-settings` as app door, and the settings-update contract (`settings.update` in MCP, `/api/settings` writer; `docs/MCP_SIDECAR.md:287-291`); keep Accounts, Engines, and Setup separate, sharing only lifecycle, command, focus, persistence, and feedback contracts.

## Convergence

Converge with `accounts` for provider identity, egress, refusal, and source receipts; first consumers are `ConnectionsPane`, `Destinations`, and calendar rows. Converge with `engines_assignment` for readiness/handoff and `setup` for discovery. Converge with `navigation_commands`, `windows`, `native_input`, and `feedback` for app scope, focus, IME/voice editing, and outcomes. Keep Settings one inspector; the other families retain separate authority and recovery lifecycles.

## User experience

The 393 capture (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-settings-393.png`) shows a quick section index and direct fields; the 1440 Rhythm capture shows a coherent rail and grouped controls. This is a promising Workbench shape without modal ceremony. Both leave a quiet small-face area and a `Saved 01:09` footer, so craft depends on making pending work unmistakable. Source does not prove conflict/return or all cold sections.

CONDITIONS: Add the bounded state contract, fix the two persistence findings, and add assertions for dirty debounce, hide/show plus later 409, and alias-to-section convergence. Do not expand Settings into the application framework.

MISSED:

1. Hidden-tab return followed by an external revision and a new edit.
2. The 700 ms interval where the value is changed but not yet sent.
3. Cold Accounts/Engines/Setup handoffs, provider refusal, and return to the prior task.

TUESDAY: The owner can reach a preference quickly, but today cannot always tell whether the latest change is durable after switching sections or returning from a hidden tab.

## Acceptance challenges

1. Open Settings from Go, change “Auto export,” switch sections before 700 ms, and verify an explicit Unsaved/Saving state followed by Saved only after confirmation.
2. Start a save, hide and show the tab, edit a second field while another surface advances `_revision`, and verify the second draft remains visible with a refusal and Retry.
3. Enter Accounts through the configured alias, add a supported ICS feed, observe its egress/source receipt, refuse the read, retry, and return to the same section without losing an unrelated preference draft.
4. Open Engines and Setup from their Settings links and from their manifest doors; verify one Settings window plus the appropriate distinct Engines/Setup window, the correct destination, and no duplicate Settings writer.

UNKNOWN: The worker ran no tests. Root ran only the isolated two-case fixture described below; no build, live Desk walk, provider call, or owner-state action was run for this review. The captures are prior desk-sweep evidence, not this baseline’s acceptance. Remote permission outcomes, all cold sections, browser visibility timing, accessibility, and performance remain unproved.


## Root verification of the return conflict

Root reproduced finding 2 against product baseline `555728021` with the real
`SettingsCore`, Testing Library, jsdom and a stateful mocked settings resource,
derived from `web/src/pages/cores/__tests__/settingsLeave.philo17.test.tsx`.
Under the repository test lock, Node 22 and an isolated HOME, a keepalive save
was accepted after `pagehide`; `pageshow` followed; the user changed Auto-run
the summary to `every`; a later ordinary save received 409 and an authoritative
reread returned `manual`. The assertion that the visible control still held
`every` failed: it displayed `manual`. The control case, with the same later
409 but no leave/return, retained `every` and exposed Retry. Final fixture run:
one expected failing regression and one passing control. This is an isolated
component reproduction, not a live-browser or owner-settings observation.

The temporary reproduction is parked outside the normal test discovery; it
is not a shipped fix or a new expected-red baseline. The future repair must
add the permanent regression alongside the existing leave test and prove both
cases green. The 700 ms dirty-receipt finding remains source-based.

## Repair — leave/return write identity, 2026-10-23

The repair replaces the lifetime leave flag with the identities of the writes
covered by each keepalive request. A conflict can be treated as superseded
only for a covered job after the leave request succeeds. A later edit retains
its draft and the existing refusal/Retry path. Failed leave-only edits remain
retryable, and late leave responses preserve newer local values. Settled
leave records are pruned instead of accumulating for the window lifetime.

The permanent stateful Settings component regression covers the reproduced
hide/show plus later conflict, actual retry, covered old conflicts on both
sides of leave completion, keepalive failure, repeat hide, and late failures
after a newer write. It preserves immediate partial-patch leave delivery and
the existing serialized writer. There is no new face, modal or framework.

Focused proof: 66 cases in five files passed; the Accounts calendar refusal
fixture now includes the actual ApiError export and all 26 cases pass. The
required quick passed the build, 4,155 related web tests, seven affected
Python/browser cases, 110 desk sweep, 27 canon and 1,126 repository guards.
Root inspected Settings captures at 1440 and 393; these are layout evidence,
not live conflict or aesthetic acceptance. [PR1434](https://github.com/karolswdev/HoldSpeak/pull/1434) records delivery. The
dirty-debounce receipt, remaining section/alias jobs and owner UX acceptance
remain open; this does not close the Settings audit.
