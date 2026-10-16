# Cohesive workflows — finished-source counsel

2026-10-15. Source review against `7f3345745` in
`wt-cohesive-workflows-20261015`. One review and one fix recheck.
Owner-authorized source counsel; **not Muad'Dib's formal check**.
**UNCHECKED — awaiting Muad'Dib.** The verdict below concerns the reviewed
source only; it does not close the root's execution or live-face work.

VERDICT: RATIFY

FINDINGS:

1. **Closed — P1, ended capture cancelled a later recording.** Round 1
   found that Runs on kept its capture ownership while transcription was
   pending. Closing that host could call the shared cancellation and discard
   a newer field's recording. Ownership now ends before Stop hands off to
   transcription (`web/src/features/runson/useRunsOn.ts:605`), and its late
   failure path no longer cancels (`web/src/features/runson/useRunsOn.ts:617`).
   The granted helper seam ends the hold synchronously and releases the server
   floor in `finally` only when no newer hold owns it
   (`web/src/lib/speakToFill.ts:182`, `web/src/lib/speakToFill.ts:194`). A release
   failure preserves the actual transcription outcome. Focused regressions
   cover an old host closing before late success/failure and exercise real
   `micSession` state with fake WebAudio
   (`web/src/features/runson/__tests__/runsOn.test.tsx:736`,
   `web/src/lib/__tests__/micOwner.test.ts:107`). Tenets 2/3; Article IV.3.
2. **Closed — P2, Resourceful Retry bypassed pending ownership.** Round 1
   found that the guard surrounded `write`, while the receipt replays only its
   callback (`web/src/desk/hooks/useWriteReceipt.ts:164`). An older Enable Retry
   could overlap a later Pause and leave the policy enabled. Guard and loading
   now belong to that replayed callback
   (`web/src/desk/components/WorkbenchResourceful.tsx:71`). The regression uses
   the real receipt hook, blocks Pause until Retry settles, then asserts write
   flags `[true, true, false]`
   (`web/src/desk/components/__tests__/commonControls.test.tsx:109`). This was an
   incomplete scoped repair of the existing overlap, not a new backend race.
   Tenet 3.
3. **Cleared — granted qualified-lineage seam.** Root found that real Ask Keep
   sources use qualified Note references. The resolver now restricts a
   qualified reference to its canonical identity before using the existing
   object resolver, and supplies the chosen canonical action reference
   (`web/src/desk/lineage.ts:16`). Get Info opens that reference
   (`web/src/desk/components/InfoWindow.tsx:210`). Tests cover aliases, missing
   targets, collisions and legacy unique bare IDs; the rendered Note action
   drives the real store with a same-ID Meeting present
   (`web/src/desk/__tests__/lineage.test.ts:16`,
   `web/src/desk/components/__tests__/commonControls.test.tsx:52`). Tenets 3/5.

CONDITIONS: None remain for the reviewed source. Root's final quick check,
TypeScript/build and live 1440/393 work remain separate obligations.

MISSED: Ranked by cost to the owner: (1) losing the newer recording after an
older hold ended; (2) an old policy Retry reversing a later Pause; (3) an
existing qualified Note source appearing unavailable or opening another kind.
All three are addressed above. The other reviewed paths retain their scoped
authorities: Workbench body writes are ordered across close/reopen
(`web/src/desk/components/WorkbenchWindow.tsx:663`); only the actual
`already_decided` 409 is a gate race (`web/src/desk/gate.ts:66`); merged source
mutations settle every attempt and retain only rejected IDs for Retry
(`web/src/features/project-room/ProjectRoomCore.tsx:1387`); active Thought
request IDs and cleared markers override stale storage
(`web/src/desk/thought-workspace/ThoughtReadsWell.tsx:20`). Accepted writes and
failed rereads remain distinct. Shared controls use existing library species,
and People no longer invents model egress for creating a Workbench item.

TUESDAY: The reviewed source preserves the next draft and provides a usable
recovery path; the owner's actual fit, focus and live workflow verdict remain
with root's walk.

UNKNOWN: This reviewer ran no tests, build, browser, model, mic, provider,
owner-data, CI or deployment work. Worker collection files, test source and
run tails were read, including `.tmp/cohesive/preferences-counsel-final.log`
(132 passed, five files) and `.tmp/cohesive/lane-c-seam-final-focused.log`
(22 passed, two files). These are controlled local results, not native mic or
provider proof. Actual 1440/393 appearance, hit ownership and menu focus were
not observed here. The existing shared capture API still has no caller token;
the correction above closes the ended-hold cleanup regression and does not
establish general ownership across replacement of live or still-starting
captures or all server floor handoffs. Storage-denied fallback lasts only for
the current browser runtime. This bounded pass makes no claim that every
interface is complete.
