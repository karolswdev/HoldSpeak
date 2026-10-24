# Bounded repair closeout — 2026-10-23

The owner clarified: finish work already underway, then refine strategy before
further code. These reviews cover the bounded repairs, not the 47 whole jobs
or near-native/appearance acceptance. Framework recommendations remain draft
#1435, UNCHECKED and awaiting Muad'Dib. No new product lane follows from them.

Ask saved-thread authority shipped in [PR1433](https://github.com/karolswdev/HoldSpeak/pull/1433),
main `3a44e5e71`. Its Astra post-merge RATIFY and limits are retained in the
[Ask record](../adversarial/ask_whole_desk.md).

The larger project-update Stop candidate is parked, not shipped, on
`fix/update-stop-repair-20261023`, commit `54a7436b7`. The last metadata/editor
changes and new regressions are unverified. Its [candidate record](https://github.com/karolswdev/HoldSpeak/blob/54a7436b72950797c9e96a69758ba44230bd2fdf/docs/internal/betterment/native-experience/checks/project-stop-candidate-2026-10-23.md)
names the remaining identity, transaction, draft and proof conditions.

## Settings — Astra post-merge review, PR1434

VERDICT: RATIFY

FINDINGS:

1. No blocking finding in the tested repair. `SettingsCore.tsx` now scopes
   supersession to covered job identities and successful leave writes, rather
   than a lifetime flag. Accepted-path cleanup preserves newer same-value
   refusal drafts; late responses retain newer local values and revisions.
   Evidence: `web/src/pages/cores/SettingsCore.tsx:1504`, `:1652`, `:1753`;
   the same-value regression is
   `web/src/pages/cores/__tests__/settingsLeave.philo17.test.tsx:240`.
2. Root read the 66-case focused run and final required quick: build, 4,155
   related web tests, seven affected Python/browser cases, 110 desk sweep,
   27 canon and 1,126 repository guards passed. Root inspected the Settings
   captures at 1440 and 393. The deployed backend is merged main `21399043e`,
   frontend `0286ed07855a8393`; identity owns the DB with no diagnoses and
   health/HTML routes answered 200. CLI/MCP invocation wrappers match it.

CONDITIONS: None for this bounded repair.

MISSED: The dirty-debounce receipt, broader configuration/alias handoffs,
reload durability and the whole Settings audit remain open.

TUESDAY: The tested leave/return conflict retains the newer value and Retry,
including the same-value race, without another save interface.

UNKNOWN: No live owner-settings write or owner aesthetic/assistive-technology
acceptance was observed. The pinned main tape runs after merge; quick green
is not a claim that the entire suite or product is green. This is Astra's
scoped post-merge review, not Muad'Dib's check of the strategy.

## Capture — Astra post-merge review, PR1436

VERDICT: RATIFY

FINDINGS:

1. No blocking finding in the tested repair. An attempt-local snapshot
   survives interception timeout and editable-field handoff; failure Retry
   and successful delayed creation consume the captured text without
   rearming input capture. Evidence: `web/src/desk/newThought.ts:77`, `:126`,
   `:133`; `web/src/desk/thoughtKeys.ts:79`, `:88`, `:115`; refused-create
   regression `web/src/desk/__tests__/thoughtDoorAndReceipt.test.tsx:170`.
2. Root read the 34-case focused proof and required quick: build, 4,169
   related web tests, five real-browser key/window cases, 110 sweep, 27 canon
   and 1,126 repository guards passed. Every-key captures at 1440 and 393
   were inspected. Main `5ab1c116e` is deployed with frontend
   `2eb9f97c4f0ee975`, owns the DB, reports no identity diagnosis and serves
   the health/HTML routes; invocation wrappers match the same source.

CONDITIONS: None for this bounded repair.

MISSED: This does not establish durable failed-create text across reload or
another global receipt replacing the Retry, nor the broader Capture/voice
targeting and document lifecycle contracts. Those remain design/audit work.

TUESDAY: First words survive the tested refused/late create and handoff,
while another field retains its own input authority.

UNKNOWN: No owner-state, physical input/audio, provider action, accessibility
or aesthetic acceptance was observed. The pinned main tape is running after
merge; its completion and attribution are separate from quick green.

## Meeting outcomes — Astra post-merge review, PR1437

VERDICT: RATIFY

FINDINGS:

1. No blocking finding in the tested repair. The HTTP response retains
   capture/save/cleanup facts; the shared parser and both Stop consumers
   keep those meanings separate. Non-clean window Stop outcomes use the
   existing receipt channel before the live view disappears; a clean saved
   Stop clears only its own matching verb/subject. Evidence:
   `holdspeak/web/routes/meetings/live.py:80`,
   `web/src/desk/store/recordingSlice.ts:152`,
   `web/src/pages/cores/LiveCore.tsx:348`. The real MeetingWindow transition
   is exercised in `web/src/pages/cores/LiveCore.test.tsx:250`.
2. Root read the final quick: build, 4,187 related web cases, 40 affected
   Python/browser cases, 110 sweep, 27 canon and 1,126 repository guards
   passed. The latter includes the regenerated API consumer manifest.
   Narrow Live and desktop stopped-record captures were inspected. Main
   `631d17880` is deployed with frontend `134b6294ef153b55`, owns the DB,
   reports no identity diagnoses and answers health/HTML routes. Invocation
   wrappers match the same source and preserve caller working directories.

CONDITIONS: None for this bounded repair.

MISSED: Complete persistence/recovery, physical audio cleanup, metadata target
identity and summary/aftercare handoff remain open audit/design conditions.
The backend's reported save flags are not a new proof that every segment or
ancillary write is durable. Recovery does not claim to retry JSON/aftercare.

TUESDAY: Window and orb Stop preserve the tested capture/save distinction,
and a save warning survives the switch to the Meeting record.

UNKNOWN: No owner-state recording, physical audio/native host, full portable
client, assistive-technology or owner aesthetic acceptance was observed. The
pinned main tape is running after merge. This is Astra's bounded repair
review, not Muad'Dib's check of the strategy.

## Full-tape follow-up and remaining work

The Ask main tape completed with 11 Python and nine browser failures; its
failing test ids match the pre-repair main tape. The strict Firefox timing
cases and web baseline passed. This comparison names existing failing ids;
it is not a claim that every underlying failure has been attributed or fixed.
The Settings, Capture and Meeting main tapes run in the background against
their pinned revisions. No whole-suite-green claim is made.

Presence remains disabled and feedback opt-in is preserved. The main checkout's
unrelated existing edits were left intact. There is no active product-edit
worker after closeout. The next planned work is the strategy decision table
and resource/preferences/Thought canvases, not automatic implementation of
the original audit delivery list.
