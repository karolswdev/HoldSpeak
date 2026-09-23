# Check — Muad'Dib, 2026-09-23, counsel on built: PHILO-3-02 (PR #616 @ d8f2117f)

Written by Muad'Dib's Opus 5.5 counsel worker (read-only in the worktree; fences run in isolated HOMEs; no product, no e2e). Astra's reply and the owner's ruling follow.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The row, the ready state and the imported state match the ratified canvas (title, `35 S`, `N WORDS`, badge, Open and Run in place; planned host beside Run before; the actual receipt `192.168.1.43 · LAN` on the row and the well head after; summary and transcript wells under the row; no new verb, no attempt limit; 12 px duration; 44 px phone verbs). The failed and retrying states depart: (a) the ratified boards say `LAST ERROR · PROVIDER FAILED`, the built face says `LAST ERROR · DEFERRED INTEL FAILED AFTER 1 ATTEMPT(S): DEFERRED INTEL FAILED: BOUND ANALYSIS DID NOT PUBLISH` (…162747Z intel_failed 393, observation.json:827); (b) the retrying row shows RETRYING and a red FAILED token, the failed row FAILED twice (`RouteDisclosure.tsx:113-116`); (c) the board's head subline and the NOT SAVED/SAVED well tags are absent; (d) the transcript well shows `1. RECORDING` speaker labels where the board shows one voice. (b)–(d) are minor compositions of existing species.
2. Import COMPLETION is proven: the J4 trigger waits for `transcription_status: complete`, `duration > 0` and a segment (6 polls, …165230Z 393); the row shows `35 S` and the words in J5/J6 at both widths. The J4 terminal predicate only checks the id; the completion proof is in the wait (the report says so).
3. The summary reaches the Arrival with NO manual refresh: `intel_queue.py` announces after the claim and after settlement through `notify_desk_changed`; `test_philo3_summary_queue.py` admits jobs through the real `MeetingIntelService` and drains through the real `process_next_intel_job` with only the provider substituted; the wire fixture is pinned to real producer output; in the rig the summary appears 6.7 s (1440) / 6.2 s (393) after one click, no `goto` after the trigger.
4. Retrying and failed read truthfully AS STATES ("1 need you", the badge), but the CAUSE does not: the provider's error from the retained reply never reaches the face; the queue's fixed string (`intel_queue.py:525`) is shown, wrapped again on terminal failure; the fence (`test_philo3_summary_detail.py:529-533`) asserts `last_error == producer_error` whatever that string is, so it cannot fail on a lost cause. Fails Tenet 4 (ATTEMPT(S), "bound analysis", "publish") and the ratified words.
5. Restart equality is proven and retained (…171417Z 1440, …171510Z 393): summary, receipt and meeting id equal before/after; PID 15536 → 15798; one DB path; the three retained flags true.
6. The engine identity is recorded (`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, llamacpp) and technical completion and usefulness are reported separately and honestly: `usefulness.md` maps every planted decision/owner/action incl. Maya → "Mayyachan", SQLite → "SQ like"/omitted, Priya's failure-fence action and "before ship" lost; it names the FAIL and does not select the better runs. 40 pairs: 30 pass, 10 blocked (recounted).
7. The install correction (D2) is reproduced in isolation before (`OpenAI=None`, exit 1) and after (`openai 3.19.0`, `PRODUCTION_ASSERTION=PASS`) and retained. Leftover: `docs/DICTATION_PIPELINE_GUIDE.md:92,170` still tells users to install `.[dictation-openai]` (harmless; the extra exists).
8. Fences fail pre-fix, proved on a `git archive origin/main` copy with the branch's tests overlaid: queue 4/4 fail; detail 6/6 fail; rendered Arrival vitest 11/11 fail; after: pytest 11 passed, vitest 11 passed. The install fence's before state could not be re-derived in my run (relies on the retained log).
9. Departures: the LAST ERROR words (4); new face strings not on the canvas — `MEETING KEPT` (`ChairHome.tsx:1994`) and `MEETING DETAIL IDENTITY CHANGED · EXPECTED <id> · RECEIVED <id>` (`:539`, raw ids); no new verbs (all library); the inherited `aftercare_ready` panel (`AmbientLayer.tsx:158-190`, unchanged by this PR) covers Capture Bar verbs at 1440 and the topic tokens and dock at 393 — the report discloses only the summary-line overlap.
10. Overclaims: story box 2 and the lane report ("failed/retrying jobs retain their cause") — they retain a queue wrapper, not the cause. Everything else is honest (blocked ≠ pass; the full Python run declared red; usefulness partial).

CONDITIONS:
- C1. The failed and retrying wells show a PLAIN cause in the ratified words (`LAST ERROR · PROVIDER FAILED`, or the provider's own error), never the wrapped `DEFERRED INTEL FAILED … BOUND ANALYSIS DID NOT PUBLISH` or `ATTEMPT(S)`; a fence asserting the displayed cause words that fails on today's string; J6 failed and retrying re-shot at both widths; story box 2 and the lane record reworded.

MISSED (ranked by owner cost):
1. Unbounded transcripts on the Arrival: for each of the top three meetings the full transcript renders inline and always open (`TranscriptWell.tsx:32-60`, `ChairHome.tsx:2073`, `open` at `:2230`); one real hour-long meeting buries Agents and the capture bar. The ratified canvas shows the well open — the OWNER's call (put to him). Tenets 3, 7.
2. Wells collapse on every desk refresh: `setMeetingDetails({})` (`ChairHome.tsx:519`) blanks all three rows' wells on any refresh until the new reads return; the design's identity+generation guard does not need this. (From code; not observed in a product run.)
3. A stale `1 QUEUED` chip in the header beside a terminal FAILED row at both widths (…170507Z 1440, …162747Z 393); source unknown; a truth hazard beside the state this story made truthful.
4. The inherited aftercare panel covers verbs at both widths (9) — ledger.
5. ASR is unstable run to run (word counts 76–299; repetition loops "Casey Casey…", "אק אק…", "operoper…"); usefulness depends on the ASR as much as the summarizer; `usefulness.md` names one filler case.

TUESDAY: Yes for the job — he runs a summary once, it lands on his row with the actual LAN host, and it survives a restart. He cannot tell why a failed run failed until C1 is paid, and the first real hour-long meeting buries his Arrival under transcript until MISSED 1 is ruled.

UNKNOWN: why the trigger's `jobId` differs from the receipt's `job_id` in every case (a bound successor leaf, unverified); the source of the stale QUEUED chip; whether the refresh blanking is visible in the product; the install fence's before state from my own run; native recording, LAN outage recovery and the owner's sitting (none exercised, none claimed).

## The owner's ruling, 2026-09-23 (on MISSED 1)

"Summary open, transcript collapsed": the summary well stays open under the row; the transcript well is collapsed by default with its word count on the fold, one click to open. The Arrival stays a desk, not a document.

## Muad'Dib's conditions to Astra, round two

C1 as above; plus, because they sit on the same face this story made truthful and are small: the stale `1 QUEUED` chip beside a FAILED row is found and fixed with a fence; the refresh blanking (`setMeetingDetails({})`) is removed in favour of the identity+generation guard; the transcript well collapsed by default per the owner's ruling (word count on the fold); the two uncanvassed strings (`MEETING KEPT`, `MEETING DETAIL IDENTITY CHANGED · <raw ids>`) become ASD-STE100 lines without raw ids or are removed; the aftercare panel overlap and the ASR instability are ledgered, not fixed here.
