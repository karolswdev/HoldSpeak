# Round-two usefulness — every planted fact, including omissions

**Partial; not an owner acceptance.** The two new successful LAN summaries are assessed together, without selecting a better run. Their technical delivery passes. The owner has not sat with this chain, and full recovery of the planted decisions, owners and actions fails.

Source: [`philo3_architect_meeting.txt`](../../../../../../tests/fixtures/philo3_architect_meeting.txt), with the same 34.67525-second WAV and unchanged SHA-256 `165ea9755d028ff3dc2b9fa85dd4c48f4db3220855906e0ffeed4a35919d47b2`. Actual engine: `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, llama.cpp at `192.168.1.43:8080`.

The complete source-to-output records are:

- [1440 observation](../../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/round-2/20260923T214120Z-case.j6.run_summary.summary_text-astra-1440/observation.json): 114 transcript words, meeting `e2f212d4`.
- [393 observation](../../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/round-2/20260923T214213Z-case.j6.run_summary.summary_text-astra-393/observation.json): 78 transcript words, meeting `a0d33ae9`.

Each observation retains import-completion transcript and `after.api_reads` meeting detail with the summary and all structured action items. These are two ASR results from identical audio, not width-dependent model settings.

| Planted fact | 1440 output | 393 output | Assessment |
| --- | --- | --- | --- |
| Decision 1: use SQLite for the local meeting ledger | ASR: “SQ like”; summary refers to local ledger but does not name SQLite | ASR: “SQ like”; summary omits ledger decision | SQLite decision not recovered |
| Owner 1: Maya Chen | ASR, summary and action owner: “Mayyachan” | Same corruption | Identity not recovered |
| Action 1: Maya writes migration plan **by Friday** | Summary and action retain migration plan and Friday; corrupted owner | Same | Action/deadline recovered; owner wrong |
| Decision 2: keep summary retrieval **on the local desk after a hub restart** | ASR retains the full decision; summary says “summary retrieval after hub restarts” but omits local desk | ASR retains decision; summary retains restart-testing action, not the local retrieval decision | Partial at 1440; decision omitted at 393 |
| Owner 2: Leo Martinez | Summary and action owner correct | Summary and action owner correct | Recovered |
| Action 2: Leo tests restart retrieval **on Tuesday** | Summary and action: test restart retrieval, Tuesday | Same | Recovered |
| Decision 3: use a recorded provider reply for isolated rig tests | ASR retains it; summary only mentions isolated rig tests, not the recorded-reply decision | Summary retains recorded provider reply for isolated rig tests | Partial at 1440; recovered at 393 |
| Owner 3: Priya Shah | ASR retains her name; summary and structured actions omit her | Summary identifies her as decision owner; no structured action | Omitted at 1440; recovered in summary at 393 |
| Action 3: Priya adds the named failure fence **before ship** | ASR repeats “Pshoglradha…” then “named failure offense before ship”; summary/action list omit the action and deadline | ASR says “Coalition. Coalition. named failure offense before ship”; summary/action list omit the action and deadline | Not recovered at either width |

Both structured outputs contain exactly two action items: “Write the Migration Plan” / Mayyachan / Friday; “Test restart retrieval” / Leo Martinez / Tuesday. Neither contains Priya's action. The 393 summary calls the three clauses “decisions” although its first two are action assignments; that wording is retained, not corrected in the evidence.

The [earlier usefulness mapping](../usefulness.md) remains valid historical evidence. [ASR instability and aftercare obstruction](deferred-ledger.md) remain inherited follow-ups. A successful queue, visible receipt, folded transcript and retained summary do not establish that the owner's meeting facts survived.

## Integrated output after main merge

The two additional ready runs on the final A2+A3 build remain **partial usefulness**, despite technical completion. The [1440 observation](../../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/round-2-integrated/20260923T221716Z-case.j6.run_summary.summary_text-astra-1440/observation.json) has 77 words, meeting `d5d4e62c`; the [393 observation](../../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/round-2-integrated/20260923T221734Z-case.j6.run_summary.summary_text-astra-393/observation.json) has 299 words, meeting `ea883298`. Same audio hash and real engine as above. Both complete outputs are retained; neither replaces the earlier results.

| Planted fact | Integrated 1440 output | Integrated 393 output |
| --- | --- | --- |
| D1: SQLite for local meeting ledger | ASR “SQ like”; summary “using SQ for the local ledger” — SQLite not recovered | Same substitution — SQLite not recovered |
| O1: Maya Chen | ASR, summary and action owner “Mayyachan” — wrong identity | Same wrong identity |
| A1: migration plan by Friday | Structured action and Friday recovered; summary only says action items assigned | Summary and structured action/deadline recovered, with corrupted owner |
| D2: local-desk summary retrieval after hub restart | Full decision recovered in summary | Full decision recovered in summary |
| O2: Leo Martinez | Name in summary, correct structured action owner | Correct summary/action owner |
| A2: test restart retrieval on Tuesday | Structured action and Tuesday recovered; summary omits task detail | Summary and structured action/Tuesday recovered |
| D3: recorded provider reply for isolated rig tests | Decision recovered in summary | Decision recovered in summary |
| O3: Priya Shah | Name appears in the list of assignees; no explicit named action or decision-to-owner pairing | Named beside the recorded-reply decision; no structured action |
| A3: named failure fence before ship | ASR “Our named failure offense before ship”; summary and structured actions omit action/deadline | ASR repeats “flashing” before “named failure offense before ship”; summary and structured actions omit action/deadline |

Both structured outputs still contain exactly two items: migration plan / Mayyachan / Friday, and restart retrieval / Leo Martinez / Tuesday. The summary's statement that Priya is assigned is not a recovered failure-fence action. The larger 393 transcript is ASR repetition, not a larger source meeting.

The 393 raw ready shot also records inherited aftercare overlap (`after.hit_test.all_owned: false`); its separately framed shot shows the summary but the panel reaches the transcript fold. This is retained in the [owner-cost ledger](deferred-ledger.md), not hidden by selecting another shorter result. The owner's sitting and full planted-fact recovery remain open.
