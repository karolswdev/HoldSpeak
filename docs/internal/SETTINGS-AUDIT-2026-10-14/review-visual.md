VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **P2 — Opening an existing account's sign-in discards a new account draft.** `web/src/pages/cores/connections/ConnectionsPane.tsx:327` uses one `well` value for the Add form and every existing account. Selecting an existing account changes that value at line 336; line 337 then unmounts `AddAccountFields`, whose Site and Email live only in local state at lines 280–281. Reproduction: with one Jira account that needs sign-in, open Add Jira account, enter another Site and Email, open the existing account's Sign in, then reopen Add Jira account. Both typed fields are empty. The same applies to Confluence and a refused Add draft. The previous independent Add fold remained mounted during this detour. This fails Tenet 3: repairing an account should not make the owner repeat typed work. This is a source transition finding; I did not execute the sequence.

2. **P2 — Accounts with the same email on different sites lose their collapsed identity when sign-in is needed.** `web/src/pages/cores/connections/ConnectionsPane.tsx:257` renders only provider and email as identity. In `owner_action_required` and `unavailable`, the trailing slot at line 259 is only Sign in/Details; the site appears in `check` at line 254, rendered inside the closed well at line 260. The producer's connection identity is explicitly `(site, email)` (`holdspeak/services/jira_provider.py:18`). Reproduction: expose two Jira accounts for the same email on different sites, both needing sign-in, and open Accounts. The collapsed rows have the same provider, email, state and verb; the owner must open each to find the intended site. Confluence shares this renderer. Preserve the provider distinction and the missing site identity. This fails Tenets 3 and 7: the architect cannot select the intended account directly. This is a rendered-source conclusion, without browser observation.

3. **P2 — Parked destinations use the new grid with the old cell structure.** `web/src/pages/cores/connections/Destinations.tsx:544` changes the parked ledger to `account-destinations`, while lines 549–552 still supply three bare token cells. The new template at `web/src/pages/cores/connections/connections.css:152` has a 24px lead track, flexible identity track and max-content action track; line 155 places only a `.surface-ledger-cells` wrapper, which parked rows lack. Thus the bare channel, target and parked-time tokens are auto-placed into those tracks rather than the intended facts slot. Reproduction: park a destination with a long folder or email target, then open PARKED at 393. The channel consumes the lead track and the target sizes the max-content trailing track. The slot mismatch follows from source; exact pixel overflow remains for the root's capture. This fails Tenet 6 and the requested consistent row grammar.

CONDITIONS:

- Keep an Add account draft across a detour to an existing account's sign-in/details. Explicit Cancel and a confirmed Add can clear it.
- Show the site in collapsed Atlassian account identity when the host's check action is inside a closed well.
- Give parked destination cells the wrapper/placement required by their chosen template, or preserve their compatible template. Inspect the long-target parked state at 393.

MISSED:

1. The shared `well` state adds a new unmount transition. The retained failed-Add test covers refusal in place (`web/src/pages/cores/__tests__/connections-pane.test.tsx:747`), not a sign-in detour.
2. Provider identity is improved, but the site half of a multi-site account identity is now hidden in two recovery states.
3. The active destination composition was updated; the parked composition was only given the new template name.

The changed tests retain the read/write refusal assertions. Their removed headline, plate, automatic command and redundant remote-badge expectations follow the requested composition change; I found no separate weakened behavior assertion to report. The root's `tests/e2e/settings_rig.py:32` arrival change also follows the parked headline.

TUESDAY: Direct module access and existing operation handlers remain present; the account-repair detour still makes the owner repeat a draft, so the conditions above should be fixed.

UNKNOWN: Independent source review of the uncommitted visual revision against `1b1b617d6`, not Muad'Dib's check. I ran no tests, builds or browsers and made no product edits. I inspected the shared ledger/gadget DOM contracts, producer account states, Settings navigation, destination setup's mounted-form path, FirstRun's default Card path and the shared door's default AddAccountFields path. Production appearance, hit ownership, actual browser transitions, owner acceptance and the combined quick check remain with root. I read the satellite corrective and FirstRun run tails (44 passed; 3 passed/28 skipped); those focused results do not establish that the new transitions above are covered or that the combined revision is green.

---

VERDICT: RATIFY

FINDINGS:

1. **Closed — account draft custody.** `web/src/pages/cores/connections/ConnectionsPane.tsx:337` keeps the populated-provider Add form mounted and hides its wrapper when another well opens. Site, Email and refusal state therefore survive the reported sign-in detour. The new parameterized test at `web/src/pages/cores/__tests__/connections-pane.test.tsx:623` checks both Jira and Confluence, both before and after an Add refusal; it asserts the same form node, both values and the retained Retry outcome. The earlier command-absence assertion now checks invisibility at line 673, which correctly reflects the retained hidden form rather than weakening the closed-command requirement.

2. **Closed — collapsed multi-site identity.** `web/src/pages/cores/connections/ConnectionsPane.tsx:257` adds the site to the collapsed identity for the two detail states. When expanded, the existing check host supplies the site. The four cases at `web/src/pages/cores/__tests__/connections-pane.test.tsx:649` cover Jira and Confluence in `owner_action_required` and `unavailable`, using the same email on two sites and requiring each site's visible identity.

3. **Closed — parked destination cell placement.** `web/src/pages/cores/connections/Destinations.tsx:549` now wraps all three parked facts in `.surface-ledger-cells.connections-tool-chips`, matching the placement rule at `web/src/pages/cores/connections/connections.css:155`. The new test at `web/src/desk/__tests__/destinations.app.test.tsx:72` requires that immediate facts wrapper to contain the channel, long target and parked time. It also retains the parked row's lack of destructive actions. This resolves the source slot mismatch; production width and overflow observation remain with root.

CONDITIONS: None remain on the three source findings. Root retains production observation, the combined quick check and the owner-facing visual acceptance.

MISSED: No additional finding within this bounded recheck. The seven added cases directly cover the reported transitions and DOM contract; they do not prove browser geometry.

TUESDAY: At source level, the account repair detour preserves typed work, sites remain selectable by identity, and parked facts have the correct row slot.

UNKNOWN: One final fix recheck on 2026-10-14, limited to the three findings and their focused tests. This is an independent Sol source review, not Muad'Dib's check. No tests, builds, browsers, product edits, staging or commits were performed. I read the seven collected regression names and the red tail (7 failed), then the latest corrective tail (59 passed, 1 failed). That remaining failure expected FOLDER while the rendered channel was FILE; the current test at `web/src/desk/__tests__/destinations.app.test.tsx:84` now expects FILE. I have not read a later run proving all 60 green. Root owns the combined quick run and the long parked target captures at 1440 and 393. Held for SHIP; the original review above remains the first-round record.
