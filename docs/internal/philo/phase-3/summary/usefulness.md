# PHILO-3-02 usefulness evidence draft

**Status:** evidence draft for Muad'Dib counsel. The retained runs provide technical evidence for a live summary and restart retention. They do not close usefulness: there has been no owner sitting, and the source-to-summary mapping has omissions, ASR corruption, and one owner misattribution.

## Evidence set

The planted source is [`tests/fixtures/philo3_architect_meeting.txt`](../../../../../tests/fixtures/philo3_architect_meeting.txt), lines 3-7. Its manifest confirms three decisions, the owners `Maya Chen`, `Leo Martinez`, and `Priya Shah`, and the three actions at [`tests/fixtures/philo3_architect_meeting.json`](../../../../../tests/fixtures/philo3_architect_meeting.json), lines 25-33.

The primary fixed canonical run is the 1440px restart-retention observation:

`pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json`

The companion live summary observations are the 393px run:

`pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json`

and the 1440px run:

`pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json`.

The J7 observation retains the summary and three structured items after restart ([J7 observation:237-334](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L237)), with the same database path recorded for the restart ([J7 observation:1405-1414](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L1405)). The J6 runs show a live summary at both widths ([393 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L695), [1440 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L695)). These are technical facts; the mapping below is the usefulness assessment.

## Source → ASR → summary → structured output

### 1. SQLite local meeting ledger / Maya Chen / migration plan by Friday

- **Source:** “use SQLite for the local meeting ledger”; owner `Maya Chen`; “Maya Chen will write the migration plan by Friday” ([source text:3](../../../../../tests/fixtures/philo3_architect_meeting.txt#L3), [manifest:25-30](../../../../../tests/fixtures/philo3_architect_meeting.json#L25)).
- **ASR:** The canonical J7 transcript says “Use SQ like” and `Mayyachan`, then preserves the migration-plan action ([J7 observation:101-112](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L101)). Both J6 observations show the same `SQ like` and `Mayyachan` corruption ([393 observation:201-212](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L201), [1440 observation:201-212](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L201)).
- **Summary text:** J7 says `Mayyachan` is tasked with the migration plan but omits the SQLite decision ([J7 observation:237-239](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L237)). The 393 summary retains a corrupted “SQ” decision and only says that action items were assigned; the 1440 summary gives the action and omits the ledger decision ([393 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L695), [1440 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L695)).
- **Structured action:** J7 emits `Write the Migration Plan`, owner `Mayyachan`, due `Friday` ([J7 observation:130-142](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L130)); both J6 runs emit the same owner spelling ([393 observation:831-843](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L831), [1440 observation:831-843](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L831)).
- **Usefulness finding:** **PARTIAL.** The action and date survive, but `Maya Chen` is misattributed as `Mayyachan`; “SQLite” is corrupted as `SQ like`; and the decision is omitted or corrupted in the summary.

### 2. Local summary retrieval after restart / Leo Martinez / test on Tuesday

- **Source:** “keep summary retrieval on the local desk after a hub restart”; owner `Leo Martinez`; “Leo Martinez will test restart retrieval on Tuesday” ([source text:5](../../../../../tests/fixtures/philo3_architect_meeting.txt#L5), [manifest:30](../../../../../tests/fixtures/philo3_architect_meeting.json#L30)).
- **ASR:** All three observations preserve this sentence and the owner/action wording ([J7 observation:101-110](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L101), [393 observation:201-210](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L201), [1440 observation:201-210](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L201)).
- **Summary text:** The 393 summary includes a paraphrase of the restart-retrieval decision and says action items were assigned ([393 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L695)). J7 and 1440 retain the test action but omit the decision’s “local desk after a hub restart” statement ([J7 observation:237-239](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L237), [1440 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L695)).
- **Structured action:** All three runs emit `Test restart retrieval`, owner `Leo Martinez`, due `Tuesday` ([J7 observation:144-155](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L144), [393 observation:845-857](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L845), [1440 observation:845-857](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L845)).
- **Usefulness finding:** **PARTIAL.** Owner, action, and date are correct. The decision itself is explicit only in the 393 summary and is absent from the canonical J7 and 1440 summary text.

### 3. Recorded provider reply / Priya Shah / named failure fence before ship

- **Source:** “use a recorded provider reply for isolated rig tests”; owner `Priya Shah`; “Priya Shah will add the named failure fence before ship” ([source text:7](../../../../../tests/fixtures/philo3_architect_meeting.txt#L7), [manifest:31](../../../../../tests/fixtures/philo3_architect_meeting.json#L31)).
- **ASR:** J7 keeps the decision and owner but corrupts the action as `fixcice...`; its second segment says “named failure offense before ship” ([J7 observation:101-118](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L101)). The 393 run ends with `Action.ructure will add a newructure`; the 1440 run ends with repeated Korean filler after `Action` ([393 observation:201-218](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L201), [1440 observation:201-218](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L201)).
- **Summary text:** J7 and 1440 say Priya is responsible for using a recorded provider reply, turning the source decision into the apparent action and dropping the failure-fence action and “before ship” timing ([J7 observation:237-239](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L237), [1440 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L695)). The 393 summary says action items were assigned to Priya but does not name the failure fence ([393 observation:695-698](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L695)).
- **Structured action:** J7 emits a third item, but it is the wrong task — `Use a recorded provider reply for isolated rig tests`, owner `Priya Shah`, with `due: null` ([J7 observation:157-168](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/observation.json#L157)). The J6 393 and 1440 outputs contain only two structured action items, so Priya has no structured action at all ([393 observation:831-859](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L831), [1440 observation:831-859](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L831)).
- **Usefulness finding:** **FAIL for this item.** The owner survives, but the actual action is omitted or replaced by the decision; `before ship` is lost; and the structured output is absent in both J6 runs or misclassified in J7.

## Width and owner-use limitation

The 1440 summary shot is technically contained and hit-test owned ([1440 observation:695-778](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/observation.json#L695)). At 393, the summary rectangle ends at `y=576`, while samples at `y=574` are owned by `div#root > aside.ambient-preview.ambient-aftercare`; `all_owned` is false ([393 observation:703-778](../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/observation.json#L703)). This is the observed overlap with the last summary line in the retained 393 after shot:

`pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/after.png`

No owner sitting was performed. Therefore this draft records technical pass evidence and usefulness defects; it does not claim that the owner can use the summary on a Tuesday.

## Integrated build — additional fixed observations

All earlier observations above remain in the tree. The integrated summary runs are `20260923T170832Z` at 1440 (meeting `1cae49e2`) and `20260923T170913Z` at 393 (meeting `29f33f35`), under the same `assets/story-02-shots/rig/final/` directory. They do not repair the usefulness defects:

| Planted item | 1440 integrated output | 393 integrated output | Assessment |
| --- | --- | --- | --- |
| SQLite ledger; Maya Chen; migration plan Friday | Summary omits SQLite; owner is Mayyachan; action and Friday retained | Summary says SQ; owner is Mayyachan; action and Friday retained | Partial; incorrect name and technology |
| Keep local retrieval after restart; Leo Martinez; test Tuesday | Summary retains test/owner/Tuesday but omits the decision | Decision, owner, action and Tuesday retained | Exact useful item on phone; partial on desktop |
| Recorded reply; Priya Shah; named failure fence before ship | Summary and structured action invent installing replies; failure fence and deadline absent | Decision retained; Priya and her action absent from summary and structured actions | Failure for the planted action |

At 393 the raw arrival capture again has its last summary line covered by the existing aftercare panel. The separately retained `framed.png` records one ordinary scroll, after the raw completion observation: the full summary then owns all nine sample points (`y=382..472`), and Open remains clear. The original after shot and `all_owned: false` are retained; the scroll does not change the raw verdict or time. On the integrated build, summary first appeared without reload at 8.319 seconds (1440) and 7.074 seconds (393).

Other retained runs are not hidden: the earlier phone restart `20260923T163844Z` attributes the third action to Shagar Radha; the integrated ready run `20260923T170219Z` invents Jeanne Shah and a submission task. The generated observation index includes every completed real-engine summary and its structured actions for comparison. No run is selected because its content is better.

## Final integrated restart observations

The final J7 runs are `20260923T171417Z` at 1440 (meeting `3511adbe`) and `20260923T171510Z` at 393 (meeting `6d66aa30`). Both preserve the exact nonempty summary, receipt and meeting ID across different hub PIDs on the same isolated DB. [The complete index](observations-index.md) retains both full output payloads and all earlier outputs.

| Planted fact | Final 1440 output | Final 393 output |
| --- | --- | --- |
| Use SQLite for the local meeting ledger | ASR says “SQ like”; summary omits the decision | ASR says “SQ like”; summary omits the decision |
| Maya Chen owns the migration plan, due Friday | Summary and structured action retain task/Friday but name Mayyachan | Same task/date recovery and name corruption |
| Keep summary retrieval on the local desk after hub restart | Transcript retains the decision; summary omits the local-desk decision | Same omission from summary |
| Leo Martinez tests restart retrieval on Tuesday | Summary and structured action recover owner, task and Tuesday | Summary and structured action recover owner, task and Tuesday |
| Use a recorded provider reply for isolated rig tests | Summary retains the decision as a task attributed to Priya | Summary retains the decision as a task attributed to Priya |
| Priya Shah adds the named failure fence before ship | Transcript action is corrupted; output substitutes the recorded-reply decision and loses before-ship timing | Transcript action is corrupted; summary substitutes the decision; structured actions omit Priya entirely |

Usefulness remains **PARTIAL**, including a **failed third action**. Persistence preserves these errors too. No owner-use verdict or phase-exit acceptance follows from the technical restart pass.

## Final built Arrival observations

Final build `3d79edd5` produces the live summaries in `20260923T191042Z` (1440, meeting `2ebf16d2`) and `20260923T191150Z` (393, meeting `0f31e46e`). Both retain 34.67525 seconds and real ASR segments; both have only two structured actions.

| Planted item | 1440 final output | 393 final output | Result |
| --- | --- | --- | --- |
| SQLite ledger / Maya Chen / migration plan Friday | Ledger decision says SQ; name Mayyachan; migration plan/Friday retained | Ledger decision omitted from summary; name Mayyachan; migration plan/Friday retained | Partial |
| Local desk retrieval after restart / Leo Martinez / test Tuesday | Test, owner and Tuesday retained; local-desk decision omitted | Same task/owner/date recovery; local-desk decision omitted | Partial |
| Recorded provider reply / Priya Shah / named failure fence before ship | Summary says Priya handles isolated rig tests; recorded-reply decision is imprecise; failure fence and deadline absent; no structured Priya action | Summary substitutes the recorded-reply decision for her action; failure fence and deadline absent; no structured Priya action | Planted action fails |

The final 393 summary is four lines (72 px) and all nine raw hit samples are owned. This does not erase the earlier longer-summary overlap with aftercare. The comparison still supports technical completion and partial usefulness, not an owner-use verdict.
