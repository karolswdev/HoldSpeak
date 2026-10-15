# Finished source review — 2026-10-15

Independent Sol xhigh worker `review_account_workbench` reviewed the frozen
Accounts and Workbench source against DESIGN.md and base `3d46ffdc3`.
One finished review; no requested product corrections. This is not Muad'Dib's
check or Astra's postmerge review. The reviewer ran no tests or browser and
made no owner-state observation. Root owns those checks.

VERDICT: RATIFY

FINDINGS: None confirmed in the changed source.

CONDITIONS: None for this source review.

MISSED: No additional confirmed regression. Custom cron values remain visible
through CycleGadget; account drafts survive well changes; Workbench submission
and save fences remain intact.

TUESDAY: Source supports adding/checking accounts and preparing/running/reading
work; root's glass review determines fit and usability.

UNKNOWN: Tests, browser keyboard/IME behavior, resize geometry and owner-desk
results were not independently executed, per brief. HOLD FOR SHIP.

The reviewer checked account draft ownership and per-subref busy state,
provider-wide Recheck routing, textarea ref/caret/@/paste/Enter handling,
custom cron preservation, late write fences, missing-engine repair and Home
counts. Root then removed one unsupported `exact: true` test query option
found by TypeScript; the string role name remains exact by default. Product
source did not change after the review.

## One bounded fix re-check

The wider quick check then found the Accounts form remount regression, the
new Pad mic opt-out requiring a named capture-authority exception, and an
unchanged guard scanning parked CSS. Source was reopened only for those
repairs and focused proof. The same reviewer inspected the finished fixes:

VERDICT: RATIFY

FINDINGS: None confirmed in the bounded re-check.

CONDITIONS: None for source review.

MISSED: The first review missed the Add refusal-state loss through Sign in.
The fix preserves the mounted form behind native hidden
(`ConnectionsPane.tsx:258`, `:349`); focused coverage checks DOM identity,
hidden controls and restored Retry (`connections.app.test.tsx:304`). The mic
exemption matches its own tag (`ux_canon_scan.py:391`), with neighboring-field
and different-face guards (`test_ux_canon_scan.py:594`). The container guard
excludes parked CSS while requiring active global CSS
(`containerQueryLaw.test.ts:9`, `:39`). No ceiling change.

TUESDAY: The account detour now preserves the draft and refusal needed to
resume Add.

UNKNOWN: Reported test totals were not independently rerun. Browser focus
traversal, geometry, IME and owner-desk behavior remain outside this
source-only review. HOLD FOR SHIP.
