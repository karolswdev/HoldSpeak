# accounts

Job: Connect an account, check it and keep its boundary clear  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_accounts`  
Evidence class: source and representative assertions inspected; no tests, captures, live calls, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The whole job starts in Settings Accounts, New Project, or a found provider profile. The owner must identify or add the account, sign in or adopt the provider CLI profile, check the identity, see egress and permission, bind the account to a project source or destination, recover a refusal, and return to the draft with the choice present after reload. The brief describes Accounts as a Settings alias. That is too narrow: the New Project Door imports the same connection API (`web/src/features/project-room/door/useDoorController.ts:9-13`) and opens its own connect well (`web/src/features/project-room/door/DoorCore.tsx:89-127`); Destinations reads the connection list while also owning email and Slack key identities (`web/src/pages/cores/connections/Destinations.tsx:188-217`). The account boundary is provider identity and read/check state, not every outbound credential.

FINDINGS:

1. **High — the audit omits active consumers and their return paths.** Settings has inline rows, egress chips, native sign-in, add/remove and refresh (`web/src/pages/cores/connections/ConnectionsPane.tsx:650-760`), but New Project only exposes the command-style `SignInWell` and then rechecks (`web/src/features/project-room/door/DoorCore.tsx:121-127`; `web/src/features/project-room/door/useDoorController.ts:568-598`). An implementation brief that covers only Settings can make two visibly different connection jobs. Owner cost: a Tuesday project setup can be blocked even when Settings works. This fails Tenets 3 and 5. Correction: add New Project and Destinations to the totality, name one shared account read/check contract, and retain the destination keychain contract as a separate boundary.

2. **High — multiple connected accounts have no stated selection rule.** New Project resolves a Jira or Confluence ref only when exactly one account is connected (`web/src/features/project-room/door/useDoorController.ts:295-308`); discovery then returns without a request when the ref is empty (`web/src/features/project-room/door/useDoorController.ts:442-474`). Two valid accounts can therefore produce a silent empty picker, while Settings can display both. Owner cost: the architect cannot choose the account that owns the project. This fails Tenets 3 and 7. Correction: require an in-world account choice and carry its stable `connection_ref` through discovery, counts and project creation, or state a bounded one-account rule with a named refusal.

3. **Medium — sign-in interruption and return are absent from the brief.** The Settings poll swallows status-read errors (`web/src/pages/cores/connections/ConnectionsPane.tsx:174-190`), while sign-in runs live only in an in-memory map (`holdspeak/services/connection_signin_service.py:64-65,195-203`). A reload, restart, expired terminal, or failed CLI has no specified reattach, expiry, or draft-return result. This fails Tenet 6. Correction: define running, failed, succeeded, unknown-run and retry outcomes; preserve the draft and focus, and show a named refusal rather than implying success.

## Convergence

`new_project` and `projects_room` should consume shared `fetchConnections`/`recheckProvider` state, with project scope retaining the chosen `connection_ref` (`useDoorController.ts:243-267,370-383`). `send_prepare` and `send_commit` should consume the same provider facts, but keep `Destinations` email/Slack `key_ref` and send receipts separate (`Destinations.tsx:120-132`). `setup` is the first found-profile adopter; adoption must converge into the same account row, not a second registry. Do not merge calendar sources or destination secrets into one generic account object: their authority and persistence differ.

## User experience

The assertions show useful craft: per-row host placement, named states, retry, and preserved Add drafts (`web/src/pages/cores/__tests__/connections-pane.test.tsx:625-716`; `web/src/desk/__tests__/connections.app.test.tsx:168-249`). That is likely pleasant for one account. It will not please a senior architect with two Atlassian accounts until selection is explicit, and the command-only Door path does not match the Settings sign-in path. These are source-based judgments, not appearance or performance claims.

CONDITIONS: extend the audit to `new_project`, `projects_room`, `send_prepare`, `send_commit`, and `setup`; specify stable identity/ref, permission and egress facts; specify multi-account selection; specify sign-in restart/failure and return-to-draft behavior; keep destination credentials distinct.

MISSED:

1. Two connected Jira/Confluence accounts and exact project selection.
2. Sign-in CLI failure, terminal loss, reload, and retry without losing a draft.
3. An account removed or rechecked while a Project or Destination draft is open.
4. A found CLI profile adopted in Setup, then used by New Project and Send.

TUESDAY: One-account Settings checking is clear; the whole job is not yet a reliable Tuesday path when account choice or interruption matters.

## Acceptance challenges

1. With one GitHub profile found, New Project adopts it, shows `GITHUB.COM`, checks it, selects a repository, and creates the source with the same identity.
2. With two connected Jira accounts, New Project requires a visible account choice; discovery, count, and created scope all use that ref.
3. Start Jira sign-in, lose the terminal or reload, and verify a named failure/retry returns to the unchanged Project draft; no false `Works` appears.
4. Recheck the account used by a saved Jira destination, then prepare Send; the destination keeps its account/ref and the send row keeps its egress and uncertain-result recovery.

UNKNOWN: No tests or live provider/terminal runs were executed; no screenshot or owner acceptance was inspected in this review; provider permissions, external side effects, and performance remain unproved.
