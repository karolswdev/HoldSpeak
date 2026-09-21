# HS-202-01 — Verification ledger

Astra, 2026-09-21 UTC. This is the follow-up home for the failures read in
the full isolated suite. It is not a claim that the full suite passed.
[Actual captures](evidence-story-01.md) retain every failure and rerun.

The full run used strict fence verification: **8 failed, 11,299 passed,
116 skipped, 4 xfailed** in 35:28. Both new fence parameters passed.
The untouched base was `50ca0dd6`, checked in the separate
`wt-202-01-baseline` worktree. Each comparison used a fresh HOME.

| Finding | Class and evidence | Disposition / follow-up |
|---|---|---|
| `test_no_live_doc_has_a_dangling_relative_link` | (b), inherited inventory metadata; the carried check contained 32 machine-local citation targets | Fixed the targets to repository-relative paths; verdict text unchanged. Focused check passes. |
| `test_committed_ledger_is_up_to_date` | (b), inherited generated phase index; Phase 202 was absent from `uat/features.yaml` | Regenerated the existing ledger: phase count 133 → 134 and the Phase 202 map entry only. Focused check passes. |
| `TestCalendarSourcesRoute::test_matched_this_week` | (a), inherited fixture posture; count 0 reproduced on base and lane at `test_hs175_calendar_sources.py:169` | Open. The fixture seeds Monday by UTC; production counts the owner's local week. At this early-Monday UTC run the seed falls outside the Denver week. Astra owns the fixture correction before phase close; preserve the local-week law from HS-175 counsel C8. |
| `TestMeetingsGlass::test_meetings_face` | (a), inherited old posture; absent `meetings-facets` reproduced on base and lane at `test_hs170_meetings_glass.py:318` | Open. HS-201-11 intentionally hides the facet when no open action exists. Astra owns correction of this older unconditional assertion, preserving both empty and populated coverage. HS-202-02 owns changes to the face; this lane changes neither. |
| `test_promotion_cancellation_after_provider_return_never_publishes_artifact` | (c), full-run-only; child outcome cancelled instead of succeeded at `test_decision_record_service.py:456` | Serial GREEN on base, then twice on lane, including immediately after both fence cases. If it recurs, Astra captures cancellation ordering under parallel load before changing the assertion. |
| `test_thought_workbench_real_glass[1440]` | (c), full-run-only; Thought region absent at `test_hs141_thought_workbench_glass.py:251` | Same three serial GREEN observations. If it recurs, Astra captures the selected window and browser trace under parallel load. |
| `test_real_http_executor_receipt_and_sigkill_cursor_replay` | (c), full-run-only; child hub health timed out at `test_kernel_real_hub.py:122` | Same three serial GREEN observations. If it recurs, Astra retains child process output and port/health timing under parallel load. |
| `test_speak_loop_393` | (c), full-run-only; raw text instead of the applied correction at `test_hs176_loop_glass.py:278` | Same three serial GREEN observations. If it recurs, Astra captures correction receipt and rendered text ordering under parallel load. |

Comparison capture `2026-09-21T01:34:03Z`: base **2 failed / 4 passed**;
lane, with both fence cases first, **2 failed / 6 passed**. The comparator's
exit 0 means both runs completed, not that either pytest run passed; each
pytest exit was 1. Second lane serial confirmation
`2026-09-21T01:39:50Z`: **4 passed in 26.75s**. This meets the method's two
serial GREEN runs for class (c). It does not identify the parallel cause
or prove the absence of all possible state leakage.

Luna's read-only review found the existing homes; Astra checked the cited
source and records before repeating them:

- Decision promotion: [Phase 136 evidence](../phase-136-scheduled-recording/evidence-story-01.md),
  lines 23–30, already records this exact cancellation test as an xdist
  flake, serial GREEN three times; service caller home HS-131-07.
- Thought glass: [Phase 145 final summary](../phase-145-the-door-polish/final-summary.md),
  lines 61–70, records HS-141 glass under load, serial GREEN twice.
- Kernel hub: [Phase 151 evidence](../phase-151-the-desk-chat/evidence-story-08.md),
  lines 1316–1332, records this exact health-timeout test as contention
  during concurrent hub boots, with an isolated GREEN capture.
- Speak loop: [Phase 176 status](../phase-176-the-speak-loop/current-phase-status.md),
  lines 321–342, records the same 393 loop as xdist-only / serial GREEN.
  Its landing helper waits for any existing result; a stale first result
  is a plausible mechanism, not a proved cause of this run.
- Calendar: `test_hs175_calendar_sources.py:128–138` seeds by UTC;
  `holdspeak/web/routes/calendar_sources.py:55–63,101–116` counts the local
  week. This is fixture debt against the existing HS-175 C8 ruling.
- Meetings: [HS-201-11](../phase-201-one-meeting-result/story-11-a-quiet-desk-for-the-sitting.md)
  requires the quiet facet; `HistoryCore.tsx:117–125,460–474` implements it.

The reviewed test and product sources are unchanged from the pinned base.
No leak from the new smoke was observed; that is bounded by the comparison,
not a universal lifecycle guarantee.

The base needed its own dependency build. Existing Node 22 was selected in
that process's PATH because installed Node 25 could not load its llhttp
library. No machine installation was changed. Both comparison legs used
the same Node 22 PATH; the second serial confirmation used the lane's
ordinary environment and its existing build.

## First-use defects and limits

- **(b), HS-202-02:** the normal RED fence names five defects at 1440 and
  nine at 393. The added `import-refresh` finding and Notes query ranking
  are visible amendments in the story and phase status. Desk memory
  content, partial-title recall, toast overlap and the host on MeetingPullout
  remain counsel findings for that lane, not coverage claims here.
- **(b), HS-202-06 / the sitting:** the owner's voice, real microphone,
  background queue drain with the owner lock, physical model egress,
  process-level restart, and the printed startup URL remain unproved.
- **(b), inherited roadmap records:** the six initial `dw check` errors
  are retained in the evidence: Phase 101 story 04 pairing, and missing
  final summaries for phases 152, 153, 154, 156 and 200. Their existing
  phase records are their homes; this lane flips none of them.
- **(a):** the two inherited expectation failures above are ledgered;
  no old-posture test was rewritten or weakened in this harness lane.

No product code, source-button ratchet, or CI command changed. The default
CI E2E job will be RED until the repair lane removes the named defects.
The PR is to remain unmerged as the owner ordered.


## Follow-up — ruled-design alignment, 2026-09-21 UTC

No new full-suite run. The same candidate is default RED on inventory 50ca
with the original five/nine keys, strict GREEN plus ratchet (6 passed in 92.95s),
and default RED on 3595fcb6 (2 failed, 4 passed in 72.14s). Both story 02 widths
complete all jobs. [Final evidence and shots](evidence-story-01.md#follow-up-result--partial-2026-09-21-utc).

| Finding | Class / proof | Home and action |
|---|---|---|
| Premature whole-page receipt guard; separate phone menu assumption | (a), corrected in this follow-up; editor receipt passes at both widths, Go → New Note passes393 | HS-202-01. Receipt freshness spans the edit, before Save closes the status region; no after-click receipt claim. |
| Resting pointer can change the highlighted palette row when results reorder | (b); before isolation Notes highlighted Custom webhook on story 02; parking the pointer makes keyboard Notes select the note | HS-202-02. Decide how keyboard selection and incidental hover should interact. The harness now parks the pointer before Meta+K, explicitly narrowing this leg to keyboard selection. |
| Folded Object/Open and Window/Close outside phone viewport | (b); Go 1404px high, overflow visible; rows y=877.5/y=1221.5 after attempted scroll | HS-202-02. Make the folded groups reachable; keep the existing named fence failures. |
| Import completion leaves stale selected meeting row | (b); transcript loads, no Run summary until reopen; no completion publication in the real import worker | HS-202-02, existing import-refresh. Add truthful refresh; the fence will pass when the loaded record changes within its existing bound. |
| FirstWords handoff intermittently never opens kept note | (c), unresolved; early hard content timeouts, later both widths complete on both product trees with unchanged speech leg | HS-202-01/02. Capture browser state/request ordering if it recurs; no root cause or flake repair claim, no KNOWN exception. |
| Editor's text is clipped horizontally at 393 | (b); editor-kept-before-save-393.png; receipt itself is visible | HS-202-02. Correct editor layout. This follow-up does not claim whole-editor layout coverage. |
| Save inside 450ms can close before any receipt; Cancel also keeps | (b), source counsel; not exercised by this walk | HS-202-02. The fence waits for successful autosave and its receipt before Save. |
| Opt-in HS202_EXPORT_SHOTS writes to the prior delivery folder | (b), existing source line 37; default runs use temporary shots | HS-202-01. Add run-specific export destination in a separate harness follow-up. Here export ran only in scratch; new proof copied to story-01-followup, original 26 untouched. |

`dw doctor` remains healthy. `dw check holdspeak` still names the same six
inherited errors: phase 101 evidence 04 not paired to done; missing phase
summaries 152, 153, 154, 156, 200. No unrelated roadmap cleanup is included.
