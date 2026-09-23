# PHILO-3-02 — round-two response and proof

Astra implemented the owner's round-two instruction against Muad'Dib's recorded **RATIFY-WITH-CONDITIONS** at branch `dfbaccd541e46e5a793786f3a6a6373e81b6e1a4`. C1 and the five accompanying corrections are paid below; Muad'Dib's re-read and merge remain pending. PHILO-3-02 stays done. This appends evidence and does not flip the story again.

## Built result

- **Plain cause:** the real bound queue failure supplies `PROVIDER FAILED`. The durable meeting and latest-job fields retain that cause, while the attempt audit retains its technical history. Both failed and retrying Arrival wells display exactly `LAST ERROR · PROVIDER FAILED`. This is the ratified classification, not a claim that the provider's verbatim error is displayed.
- **Settled queue header:** the count producer already excluded terminal jobs correctly. The missing seam was publication: the settlement path announced `desk_changed`, but the header consumes `runtime_queue`. The same durable transition now publishes the freshly produced runtime frame. Terminal failure shows zero queued and one failed; a scheduled retry correctly shows one queued.
- **Refresh continuity:** same-identity detail records remain rendered while their replacement reads are pending. Removed identities are pruned; active/generation and returned-identity guards still reject stale or wrong responses. An opened transcript stays open across a desk refresh.
- **Owner's fold ruling:** summary stays open. Transcript defaults closed, shows its durable word count on the existing library fold, and opens with one click. Other TranscriptWell consumers retain their existing defaults.
- **Read facts:** `SUMMARY READ FAILED` replaces missing/wrong-identity diagnostics; `MEETING SAVED` replaces `MEETING KEPT`. No raw meeting IDs reach those lines. No new Arrival verb or attempt limit was added.

The three implementation workers were `gpt-5.6-luna`, reasoning `xhigh`, held for SHIP. Astra reviewed the changes, rejected an unnecessary provider-boundary parser in favour of the explicitly ratified plain label, independently ran the decisive fences, inspected every new shot, and owns the gate.

## Fences: actual old producer and rendered old face

The baseline was an isolated `git archive` of `dfbaccd5`; no checkout was moved. The new tests were overlaid on it, with its **old real-producer wire fixture**, not a rewritten fake error. Actual stdout is retained:

| Seam | Before | After |
| --- | --- | --- |
| Plain retry/terminal cause and runtime-frame publication | [Backend raw red](cause/astra-final-pre-fix.raw.log): **5 failed, 7 passed**; real service admission and real queue drain, provider only substituted | Covered by independent **153 passed** [focused run](focused.raw.log) and [153 collected](focused.collect.raw.log) |
| Exact displayed cause, fold, read facts, refresh continuity | [Rendered raw red](arrival/astra-final-pre-fix.raw.log): **9 failed, 3 passed** on old Chair/TranscriptWell/wire | **12 Arrival tests pass**, included in full web check |
| Refresh seam in isolation | [Refresh-only red](arrival/astra-refresh-seam-pre-fix.raw.log): **1 failed, 11 skipped**; current face with only old `setMeetingDetails({})` restored in the archive; visible summary disappears during unresolved refresh | Rendered test holds the replacement read unresolved, asserts both summary and opened transcript remain, then resolves the replacement |
| Actual J6 recipe assertions | [Atlas raw red](rig/astra-final-pre-fix.raw.log): **2 failed** against old recipes | Both pass in the focused 153; all four affected actual walks pass below |

The displayed-cause test asserts `LAST ERROR · PROVIDER FAILED` directly, before checking the real wire's cause. It cannot pass merely because a fake and the face agree on a queue wrapper. The worker `.txt` reports are notes; the `astra-*.raw.log` files above are the independent red execution evidence.

## Actual rig and glass

[Observation index](observations-index.json), [audit source](verify_observations.py), and [audit output](observations-audit.raw.log). Every invocation is separately captured in the [paired DW evidence](../../../../../../pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/evidence-story-02.md). All six use the same synthetic WAV, completed-import wait, closed engine setup window, one Run, one isolated hub/HOME, and the final built asset `index-lDHBzCUa.js` (index SHA `812d35c43631f655e5441c9087786e3d03ef477cd0557561b65850fe8171ce05`). No manual refresh after Run.

Run directories live under `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/round-2/`; each retains `observation.json`, `before.png`, and `after.png`. Ready runs also retain `framed.png`. Astra inspected all fourteen shots.

| Actual atlas case | 1440 run / first result | 393 run / first result | Observation |
| --- | --- | --- | --- |
| `case.j6.run_summary.intel_failed` | `20260923T213753Z` / 0.928 s | `20260923T213842Z` / 0.926 s | Plain cause; header **1 FAILED**; API queued 0, failed 1; folded 77 words |
| `case.j6.run_summary.retrying` | `20260923T213924Z` / 0.926 s | `20260923T214019Z` / 0.929 s | Plain cause; header **1 QUEUED**; API scheduled retries 1, failed 0; folded 299 words |
| `case.j6.run_summary.summary_text` | `20260923T214120Z` / 7.082 s | `20260923T214213Z` / 6.676 s | Real summary and actual host; summary open, transcript folded; 114 / 78 words |

The four failed/retrying runs use the retained **provider-boundary reply**. They do not simulate a real LAN outage or prove future recovery. The two ready runs use `http://192.168.1.43:8080`; `/v1/models` returns **Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf**, `owned_by: llamacpp`. All six observed target regions own all nine pointer samples and report no console errors. This does not claim the whole desk is free of the inherited aftercare obstruction.

The original [60-observation evidence](../observations-index.md) remains immutable, including the J4/J5/J7 closure and both restart identity records. These six observations supplement it; no new restart run is claimed in round two.

## Full verification and limits

Main advanced to `5de5d0c3` with A3 and PR #616 became conflicting. The partial serial run was stopped deliberately, with its output retained, so main can be integrated before final full verification. This checkpoint is not ready for push/merge. No full Python result is inferred from it.

- `npm --prefix web run check`: **306 files / 2,807 tests**, typecheck, build, token/architecture checks and bundle gate pass. DW capture `2026-09-23T21:35:45Z` has exit 0. [Retained output](full-web.raw.log) contains DW's output-truncation marker after the test result/build warnings; [separate bundle-gate output](bundle-gate.raw.log) retains the final budget result: desk JS 1,320,728 B, CSS 319,048 B, zero maps.
- Focused Python: **153 passed**, DW `2026-09-23T21:35:25Z`, exit 0. Graph, API and capability generation checks pass; inherited graph census stays five miscited anchors and fourteen subtype conflicts.
- Full serial Python, isolated HOME, no metal: **interrupted to integrate main: 106 passed, 69 skipped, exit 2 after 1247.51 s**. [Complete stdout](full-python.pre-main-interrupted.raw.log), [capture receipt](full-python.pre-main-interrupted.capture.txt), and [classification](full-suite-classification.md).

**Technical completion is verified for the round-two corrections. Owner usefulness is partial.** [Every planted decision, owner and action is mapped](usefulness.md), including omissions. [Aftercare obstruction and unstable ASR are ledgered](deferred-ledger.md), not fixed. No owner sitting, native microphone capture, real LAN outage recovery, or eventual retry success is claimed. The render-only read-failure and delayed-refresh fences are not described as live native-failure walks.
