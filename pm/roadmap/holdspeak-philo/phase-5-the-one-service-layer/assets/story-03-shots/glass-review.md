# PHILO-5-03 — Astra's glass readings

These are readings of the retained screenshots, separate from operation
equivalence. The source is `c4d46498`; the lane is in progress.

| Run | Shots inspected | Reading |
|---|---|---|
| `20260924T210414Z-case.closure.chain.s1_import_complete-astra-1440` | `none/browser/<run>/before.png`, `after.png` | The empty meeting area gains Architecture boundary review, a transcript disclosure and the LAN host beside Run summary. This case's predicate is a protocol read; the screenshots do not turn it into a face predicate. |
| `20260924T210623Z-case.closure.chain.s1_import_complete-astra-393` | `none/browser/<run>/before.png`, `after.png` | The imported meeting appears at phone width. The title, transcript disclosure, LAN badge and Run summary remain visible. This case also has a protocol predicate. |
| `20260924T210729Z-case.closure.chain.s2_summary_with_host-astra-1440` | `real/browser/<run>/before.png`, `after.png`, `framed.png` | The summary replaces the pre-run state and the host is visible in its retained run record. The summary text is readable. The raw after-shot and framing shot both retain the result. |
| `20260924T211731Z-case.j11.thought_keep.receipt_time-astra-1440` | `none/browser/<run>/before.png`, `after.png` | The blank Thought gains the typed body. Its foot shows KEPT and the local time, followed by IN INBOX. The receipt predicate first passes at 0.926 seconds, after the 0.45-second autosave delay; the retained PATCH response has working revision 2 and the saved body/time. The inventory's source-only concern that this receipt was unreachable is disproved by this run. |
| `20260924T212912Z-case.closure.chain.s2_summary_with_host-astra-393` | `real/browser/<run>/before.png`, `after.png`, `framed.png` | The LAN summary and host receipt remain visible at phone width. The frame shows the readable summary, topics and transcript disclosure. Predicate first satisfied at 8.712 seconds; terminal observation at 8.841 seconds. The Meeting ready notice repeats the inherited zero-count debt (`3 open · 0 decided`). |
| `20260924T213120Z-case.closure.chain.s3_same_summary_after_restart-astra-1440` | `real/browser/<run>/before.png`, `after.png`, `framed.png` | The same summary and LAN receipt remain visible after a real process restart. The retained record has a new PID and the same database, meeting identity, summary and receipt. Terminal observation: 3.445 seconds. |
| `20260924T213245Z-case.closure.chain.s3_same_summary_after_restart-astra-393` | `real/browser/<run>/before.png`, `after.png`, `framed.png` | The raw after-shot starts at the Arrival work list; the independent framing scroll shows the retained summary and LAN receipt below it. The same database, meeting identity, summary and receipt survive restart. Terminal observation: 3.416 seconds. |
| `20260924T213441Z-case.closure.chain.s4_decision_recorded-astra-1440` | `real/browser/<run>/before.png`, `after.png` | Done changes the editable decision to its saved reading view, with the meeting source and body visible. The real detail read retains its ID, proposed status and created_at; terminal observation: 1.086 seconds. This case predicates on the protocol read. |
| `20260924T213555Z-case.closure.chain.s4_decision_recorded-astra-393` | `real/browser/<run>/before.png`, `after.png` | The protocol title assertion passes and the real detail read contains the saved body/source. The raw after-shot has a New decision reading view with blank content. This shot does not prove rendered saved content; its timing or rendering cause remains unverified. Terminal observation: 1.086 seconds. |
| `20260924T213830Z-case.a1.decision_face_create.opens_and_reopens-astra-1440` | `none/browser/<run>/before.png`, `after.png` | The reopened decision shows the saved title, source and body. The invalid-status trigger returns HTTP 400 and the visible decision remains unchanged. Detail/list readbacks retain one saved row. Terminal observation: 1.038 seconds. |
| `20260924T214148Z-case.a1.decision_face_create.opens_and_reopens-astra-393` | `none/browser/<run>/before.png`, `after.png` | The reopened decision remains readable at phone width: title, source and body. The invalid-status request returns HTTP 400 while the same decision stays on screen. Terminal observation: 1.041 seconds. |
| `20260924T215606Z-case.a3.brief_next_day.decision_on_the_face-astra-1440` | `none/browser/<run>/blocked.png` | Setup displays the retained empty brief. The rig correctly blocks the trigger because the added decision read names an uncaptured decision_id. The atlas now captures that ID from its actual create response; this attempt remains blocked. |
| `20260924T215956Z-case.a3.brief_next_day.decision_on_the_face-astra-1440` | `none/browser/<run>/before.png`, `after.png` | The retained empty brief becomes the next-day brief with the decision row and Ack/Defer controls. The new brief ID differs from day one and its source_ref names the created decision. Terminal observation: 1.078 seconds. Reinspection at original resolution confirms Generate remains visible. |

| `20260924T220156Z-case.a3.brief_next_day.decision_on_the_face-astra-393` | `none/browser/<run>/before.png`, `after.png` | The next-day decision row, Ack/Defer controls, Generate control and receipt are readable at phone width. The producer read confirms a new brief ID and the same decision source. Terminal observation: 1.072 seconds. |

## Ledger

- Inherited face debt: the S2 after-shot contains a transient Meeting ready
  card with `2 open · 0 decided`. The zero count fails UX-CANON A.8 and
  Tenet 3's requirement that the interface help the owner. No face source
  changed in this lane; this is observed on the base frontend. The story's
  protocol/operation work does not fix or certify this toast.

- S4 at 393: the raw after-shot has blank decision content despite the saved
  detail read. This is a protocol case; its PASS certifies persistence only.
  The 1440 shot renders the saved content. Cause and eventual phone rendering
  remain unverified; no operation verdict can close that face gap (Tenet 3).

## Producer probe

Astra called the real rig `Hub` in a temporary HOME with a nonempty
header-only VTT (`WEBVTT` followed by two newlines). HTTP import returned
202 and meeting `7b6c7b7d`; the real background parser left its previously
created row with `intel_status.state = import_failed`, no segments, no
intelligence job and no run receipt. The summary route returned 409,
`code = empty`, `error = Meeting has no transcript`. This diagnoses the
existing atlas refusal setup, which incorrectly imported speech and waited
for a completed transcript. The atlas must capture this producer through
the normal rig before the pair is closed. This probe is not a closed walk.

| 20260924T220621Z-case.a3.brief_next_day.new_id_with_the_decision-astra-1440 | before.png, after.png | Both show the prior empty brief. API trigger saves the new day brief and its decision relationship, but does not refresh this face. Protocol PASS only; the separate face case proves the rendered transition. |

| 20260924T221218Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440 | before.png, after.png | Before has two waiting action rows. After adds the exact saved decision title with Ack/Defer, new-day receipt and Generate; retained LAN summary remains visible below. Face PASS. |

| 20260924T221324Z-case.closure.chain.s5_next_day_brief_has_it-astra-393 | before.png, after.png | After shows the exact saved decision title with Ack/Defer and Generate above it; the row is readable. Face PASS for the declared row. Receipt and summary are below the captured scroll position, so this shot adds no claim for them. |

| 20260924T221450Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440 | before.png, after.png | Decision row appears with Ack/Defer and the receipt; face predicate PASS. Before protocol has two missing-decision failures, but after has none because16:15 falls before the next lookback start17:00. Does not prove scoped breakage; retained attempt, unselected. |

| 20260924T221628Z-case.j11.thought_keep.receipt_time-astra-1440 | before.png, after.png | Blank note becomes the exact J11 body. KEPT with time remains visible in the footer; before and after render the same minute, while real save/read revision1→2 and last_modified change confirm this save. |

| 20260924T221724Z-case.j11.thought_keep.receipt_time-astra-393 | before.png, after.png | Exact J11 body appears and KEPT/time stays readable in the mobile footer. Real detail/workbench reads retain ID, note ID and cursor, revision1→2, and saved body/time. |

| 20260924T222024Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440 | before.png, after.png | Last Defer row becomes ALL 2 HANDLED with receipt retained; saved headline remains 2 decisions waiting while visible handled state updates. Protocol shelf maps Ack and Defer to their titled rows. |

| 20260924T222106Z-case.philo404.arrival_triaged_headline.all_handled-astra-393 | before.png, after.png | Last Defer row becomes readable ALL 2 HANDLED with the original brief receipt still visible. Both shelf states are retained against the correct row titles. |

| 20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440 | before.png, after.png | Empty-transcript meeting remains on Arrival; protocol409 empty refusal and no jobs retained. Protocol-only verdict. Face labels this failed VTT import SAVED; no failure receipt is shown here. Inherited presentation debt for PHILO-5-04, not a face PASS. |

| 20260924T222425Z-case.j6.route_intelligence_run.no_assignment-astra-1440 | before.png, after.png | Both show NO SUMMARY ROUTE · NO ASSIGNMENT. HTTP409 is retained and the actual refused job/receipt are read back against the same meeting; no new face claim from the API trigger. |

| 20260924T222649Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440 | before.png, after.png | Decision row appears with Ack/Defer and new-day receipt. Both same failures have new brief-scoped IDs in durable reads; old brief/items/Ack unchanged and final shelf empty. Failure rows are not rendered on this Arrival face; the face predicate is the decision row only. |

| 20260924T222745Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393 | before.png, after.png | Decision row with Ack/Defer and Generate is readable after next-day generation. Receipt is below the captured viewport. Both same failure sources get new brief-scoped IDs; old rows/Ack unchanged and final shelf empty, read from the isolated hub. |

- `20260924T223147Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440`: Astra viewed both raw shots. Generate leaves the same No changes headline and original GENERATED SEP 24 16:31 receipt on the face; both latest reads keep the exact brief id and generated_at. The rig observed the full 180-second late-result window; total 187.738 seconds.

- `20260924T223711Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393`: both raw shots viewed. No changes and GENERATED SEP 24 16:37 stay visible after Generate; Brief ready receipt is visible, no overflow. Exact brief ID/generated_at retained across reads. Total 188.635 seconds, including the 180-second late-result window.

- `20260924T224233Z-case.j10.route_generate_again.same_day_same_id-astra-1440`: both raw shots viewed. No changes and original receipt remain after the direct API trigger; returned/read-back brief id and generated_at match the pre-trigger read. Protocol verdict only.

- `20260924T224324Z-case.j10.brief_item_shelf.acknowledged-astra-1440`: both raw shots viewed. Direct HTTP Ack persists the intended item state, but the already-open Arrival still shows its row and Ack/Defer. Protocol PASS only; no live refresh claim (phase scope permits reopened reads). The separate ALL 2 HANDLED UI-click case proves the rendered transition.

- `20260924T224425Z-case.j10.brief_item_shelf.deferred-astra-1440`: both raw shots viewed. Direct HTTP Defer persists the correct row as deferred; already-open Arrival remains unchanged, with row and receipt visible. Protocol PASS only.

- `20260924T224519Z-case.j10.brief_item_shelf.refused-astra-1440`: both raw shots viewed. HTTP 422 Unknown shelf state: shelved leaves the exact brief and empty shelf unchanged. Arrival row and receipt remain visible. Protocol refusal only.

- `20260924T224620Z-case.closure.chain.s2_summary_with_host.replayed-astra-1440`: raw before/after and framed shot viewed. Run summary becomes RAN/Open; the summary and 192.168.1.43 LAN receipt are visible. Provider result is REPLAYED from the retained parsed real result (fixture hash in observation), not a new LAN inference. Existing toast shows 0 decided; already recorded debt.

- `20260924T224720Z-case.closure.chain.s2_summary_with_host.replayed-astra-393`: all three shots viewed. RAN/Open and LAN receipt are visible after the click; the separate framed shot shows the full retained summary. Raw after has the existing meeting toast over lower content. REPLAYED parsed provider result, never a real inference claim.

- `20260924T224832Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-1440`: raw before/after and framed shot viewed. Exact replayed summary survives real hub restart and is visible with the LAN-labelled receipt. All three restart retention flags are true. Replayed provider result; receipt host is configured routing metadata.

- `20260924T224917Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-393`: all three shots viewed. Raw after is at the top of Arrival; the separate framed shot shows the exact retained summary and LAN-labelled receipt after restart. All three restart retention flags true. REPLAYED result, browser-only face assertion.
