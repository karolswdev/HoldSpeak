# PHILO-5-04 — His words, rehearsed

**REHEARSED; OWNER REVIEW PENDING (2026-09-24).** Target closing mode:
**REHEARSED, OWNER-REVIEWED SHOTS — PENDING OWNER REVIEW**.
This is a technical rehearsal. Muad'Dib publishes the shots for the owner's
review after counsel on built. No live sitting is claimed.

The final real-engine run completed in **326.090 seconds**, from
2026-09-25T00:14:07.695632Z to 00:19:33.786633Z (September 24 in Denver).
Astra inspected the summary before/after, decision, Thought, and brief PNGs
at 1440 × 900 and 393 × 852. The brief receipt and row crops are identical
to their corresponding full shot (same SHA256), so all 14 retained PNGs
are covered by those ten visual readings.

## The four prompts (written by the lane in the owner's words)

The lane expressed the assigned job as these four ordinary-word prompts.
These are the actual strings sent to one fresh Codex session and its
resumed turns. No prompt contains an operation name, field name, date or clock override. The owner typed nothing; the lane wrote these prompts and Astra's Codex session executed them. The rig alone advanced the brief producer's day
between the third and fourth turn. The machine clock did not change.

> I have an architecture review recording at /Users/karol/dev/tools/wt-philo-5-04/tests/fixtures/philo3_architect_meeting.wav. Import it into HoldSpeak, wait until the transcript is ready, and tell me when the meeting is ready for the next request.

> Please summarize the meeting we just imported. Keep the summary on its meeting record, and tell me when it is visible.

> Put this decision on my list to review tomorrow: Keep summary retrieval on the local desk. Link it to the meeting. Create a Thought titled Phase 5 rehearsal with this body: The meeting loop stays on the local desk. Then edit that Thought so the body ends with: Saved after the meeting review. Save that edit and tell me what you recorded.

> Now it is tomorrow. Make my brief and tell me what is on it.

## What Codex did

Codex started through `scripts/astra ask` with `codex exec` and resumed
that session for the later prompts. The effective holdspeak MCP command
was the lane's `.venv/bin/holdspeak-mcp`, cwd was the lane worktree, and
`mcp_servers.holdspeak.env.HOME` was the hub's isolated HOME. The real lock
published port 61059 and the token was persisted by the hub. The driver's
DB-path check ran before engine setup or the first Codex write.

| Turn | Public MCP calls chosen, in order | Client duration |
| --- | --- | --- |
| Import | `meeting.import` → `meeting.get` | 34.427 s |
| Summary | `meeting.get` → `meeting.run_intelligence` → `meeting.get` → `meeting.get` | 38.466 s |
| Decision and Thought | `thought.create` → `thought.update_working` → `desk.get` → `meeting.proposals` → `desk.create` → `desk.get` → `desk.get` | 201.398 s |
| Tomorrow | `monday_brief.generate` → `monday_brief.get` | 23.333 s |

All 15 completed tool calls and results are retained; this final run has
no tool refusal. The audit also accounts for refusals when present.
The decision write used `desk.create` with `kind=decisions`; the two Thought
writes were `thought.create` and `thought.update_working`. Codex also read repository documentation and source while finding the decision review fields — and two things that are neither product docs nor source: the Phase 4 roadmap story `pm/roadmap/holdspeak-philo/phase-4-the-morning/story-02-decision-in-the-visible-rows.md` and `~/.codex/config.toml` (read-only); in turn 1 the `scripts/astra ask` preamble ("You are Astra … TWO-BRAINS.md") led it to read the canon documents (TWO-BRAINS, CONSTITUTION, UX-CANON, ORCHESTRATION, AGENTS.md, CLAUDE.md). It did not read the atlas, `graph.json`, the phase-5 records or the run folders. This proves ordinary prompts with client discovery in this repo;
it does not prove discovery without repository access. The review date is
text in the decision context, not a scheduled reminder. No shelf call was
needed or chosen. The final run created no separate decision record.

The complete server record contains every tools/list request and response,
MCP call and result, and HTTP method/path/status. The complete Codex event
and rollout files are retained per turn. The audit pairs each client call
with a distinct server POST `/api/mcp` row by name, arguments and result.
Only explicit empty envelope defaults are normalized; nonempty content and
errors must agree. No non-MCP HTTP writes occur in a Codex turn window. These are recorded
index intervals `[5,10)`, `[182,311)`, `[312,624)` and `[857,880)`,
not timestamp filters: non-MCP rows do not carry timestamps. The root
read all 28 completed shell commands and found only repository/config
reads. Started/completed event duplicates are not separate commands.
The rig's engine setup and producer-day advance are separately recorded;
they are not attributed to Codex.

The first browser opening also wrote to the isolated hub: zero-based
transcript row **43**, `POST /api/desk/seed`, and row **62**,
`PUT /api/setup/onboarding`, both HTTP 200. These are FirstWords' first-open
handoff (`FirstWords.tsx:213-216`), outside every Codex window. `apply_seed`
(`db/seed.py:106-230`) writes the starter `directories`, `notes`, `recipes`
(including mode presets), `kbs`, `directory_memberships` and
`knowledge_memberships`. Note triggers also maintain `notes_memory_fts`
and its FTS backing tables. The onboarding service repeats the additive
seed and writes `onboarding_state` (`setup_service.py:40-43`). The final DB
has six starter directories, ten starter/guardrail notes, six mode recipes,
one KB and their memberships created at 00:14:47Z, plus disposition
`dismissed`. These were not Codex-created job objects. The source and final
rows identify the affected stores; no per-statement SQL trace or allocation
between the two requests is claimed. See the retained first-open readback.


## What the Desk showed

Shot IDs below are relative to the final run's `shots/` directory.

| Step | 1440 | 393 | Reading |
| --- | --- | --- | --- |
| Imported meeting | `summary/1440-before.png` | `summary/393-before.png` | Architecture review, 76 transcript words, assigned LAN engine; no summary yet. |
| Summary delivered | `summary/1440-after.png` | `summary/393-after.png` | Persisted summary text and actual `192.168.1.43 · LAN` receipt. Same open Arrival pages; zero navigation after open and no manual refresh. Scroll at 393 is recorded. |
| Decision on Chair | `decision/1440.png` | `decision/393.png` | Proposed review decision, exact local-desk wording and meeting link in its context. |
| Thought saved | `thought/1440.png` | `thought/393.png` | Edited body ends with “Saved after the meeting review.” and a KEPT receipt. |
| Next-day brief | `brief/1440.png` | `brief/393.png` | Sep 25 brief, review decision leads visible rows, `Brief ready · 6 items · 6:19 PM`. Fresh/reopened read. |
| Receipt predicate | `brief/1440-receipt.png` | `brief/393-receipt.png` | Same shot, taken after the receipt is visible. |
| Decision-row predicate | `brief/1440-row.png` | `brief/393-row.png` | Same shot, decision source matches the saved decision ID. |

The brief receipt counts all six raw section items; Arrival's human-item
heading counts five and shows its existing three-row cap. Six visible rows
are not claimed. The face also shows `GENERATED SEP 25 18:19` beside a `6:19 PM`
receipt: inconsistent formats for the same producer time. The count/time
conflict and the persisted raw `MeetingIntelService.run_intelligence` item
are now ledger rows 5/6. The raw item is counted by the receipt but filtered
from Arrival at `ChairHome.tsx:884-886`; expanding “2 more” was not walked.
The time is the brief producer's period end, not the wall
clock time of Codex's call. The transient summary toast still says
“3 open · 0 decided”; that inherited defect remains in the six-row ledger.

## What was read back

| Canonical operation | Durable result and comparison |
| --- | --- |
| `meeting.read` | `1a1f7ce7`, Architecture review, transcript complete; the real LAN summary and run receipt match both Arrival shots. |
| `decision.read` | `decision_96c04b1b7a13`, status proposed, title/body “Keep summary retrieval on the local desk.”, context references `meeting:1a1f7ce7`. |
| `thought.read` and `thought.workbench.read` | `thought_2b4148a5b1f8`, note `note_thought_c6f90ab0fab106d0`, working revision 1 → 2; final body “The meeting loop stays on the local desk. Saved after the meeting review.” |
| `brief.latest` | `brief-de8a52459de14125bc7ed351be8451b9`, period end `2026-09-25T18:19:14.790734`, decision item source `decision:decision_96c04b1b7a13`; same decision and receipt shown in the fresh Desk. |

The final SQLite backup uses SQLite's backup API from a read-only source.
It includes the committed WAL state. The database is
`/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo5-04-hub-fx3inucg/.local/share/holdspeak/holdspeak.db`.
The owner's desk database was never used.

The LAN endpoint `http://192.168.1.43:8080` answered HTTP 200 and served
`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`. All closing attempts used that real
engine. No replay is presented as real-engine closing proof. The fixture
is synthetic architect-meeting audio, with SHA256
`165ea9755d028ff3dc2b9fa85dd4c48f4db3220855906e0ffeed4a35919d47b2`.

## The receipt seam and stopped attempts

The fresh read originally showed saved brief rows without `Brief ready`.
The red probe re-opened run 4's existing Codex-produced brief at both
widths without generating another. The green probe read that same brief ID
after the surgical change; both widths then showed its five-item receipt.
The final run above independently created the six-item brief from a fresh
Codex session. [Settled design and Muad'Dib's check](receipt-seam.md).
The rendered fence starts with one complete real producer payload and
requires a later Generate to replace its count and time with another real
payload. The pre-fix runs `000904Z`, `001056Z` and `001255Z` each show
three failures: two missing-receipt assertions and one empty-Generate
timing failure. `001336Z` is a post-fix run with only the timing failure;
it is not a missing-receipt red. The previous citation was corrected at
Muad'Dib's closing check. A rendered StrictMode
mount-read fence also proves that a later failed read retains the first
receipt and a null response clears it. Deliberately clearing the receipt
on failure gives one failed test; the unmodified product passes all 20
scoped receipt/load/date tests. This is no already-open refresh claim.

Four stopped attempts remain complete and separately labelled. They exposed
an envelope-projection mismatch, an Arrival overlay/selector mistake, a
10 ms text timeout, and a decision wording ambiguity. The fourth run chose
an accepted decision, which the proposed-decision review collector omits;
it also created an extra decision record outside the pilot registry. The
final prompt explicitly asks for a decision on the review list tomorrow.
It supplies no status field. No collector behavior was changed. The exact
older prompts and results remain available. Early plain-copy SQLite files
are explicitly labelled incomplete; later read-only backups and the
original registry readbacks are the proof, not the incomplete files.

## What was not proven

- Owner review or a live sitting. Muad'Dib's publication and the owner's
  review are downstream; phase exit 5 stays unchecked.
- Already-open brief refresh. Only the existing summary delivery was
  observed without refresh; the brief was read on a fresh/reopened Desk.
- Usefulness or summary accuracy. Phase 3's measurement remains the measure.
  This run's text and unassigned action rows are retained without promotion.
- Missing-decision refusal parity: the actual HTTP/op pair is **FAIL, 2:1**.
  Shelf invalid-state refusal still happens before registry dispatch.
- The six ledgered product repairs or new decision kernel admission.
- A new restart proof in the final Codex run. This lane's S4 actual-atlas
  walk supplies the carried saved-content proof; earlier phase restart
  proofs keep their original scope.
- A full-suite result. The owner's lane law required scoped tests only.

## Retained evidence

- [Final observation](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/observations.json)
- [Full server MCP and HTTP transcript](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/rehearsal-transcript.jsonl)
- [Effective Codex config](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/effective-codex-config.json)
- [DB and lock proof](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/hub-proof.json)
- [Hub log](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/hub.log)
- [Final SQLite backup](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/db-proof.sqlite)
- [Run duration](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/run-status.json)
- [Stopped attempts](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/attempts/README.md)
- [Receipt red](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/receipt-red/brief-read.json) and [green](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/receipt-green/brief-read.json)
- [Structural audit](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/final-rehearsal-audit.txt)
- [Lane report and ledger](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/../../lane-report-story-04.md)

- Pre-fix rendered reds: [000904Z](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/receipt-tests/run-20260925T000904Z.out), [001056Z](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/receipt-tests/run-20260925T001056Z.out), [001255Z](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/receipt-tests/run-20260925T001255Z.out)
- [First-open seed readback](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/first-open-seed-readback.txt)
- [Closing check](../../../../../pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/../../checks/story-04-closing-muaddib.md)

## Notes from Muad'Dib's counsel (2026-09-24)

- `scripts/philo5_his_words.py:263` imports `holdspeak.mcp.tools`, which loads `holdspeak.operations` in-process for a READ-ONLY catalogue read under a throwaway HOME; that load sits OUTSIDE the story-03 AST fence (which covers `graph_walk.py` and `philo5_pairs.py`). It composes no service and writes nothing; recorded here so the fence's scope is honest.
- The shots show a Sep 25 brief under a menu-bar clock reading Sep 24: the rig advanced ONLY the producer's day (`PRODUCER_CLOCK_READ advance_days=1`, `hub.log:7`); the machine clock never moved.
- Carried box (b), S4 at 393: cause UNKNOWN. The DECISION body is empty ~0.4–1 s after Done at 393 (0.95 s empty, 1.363 s readable; 1440 readable at 0.955 s); suspected seam `DecisionPullout.tsx:69-71`; ledgered as a face flash in BACKLOG.
