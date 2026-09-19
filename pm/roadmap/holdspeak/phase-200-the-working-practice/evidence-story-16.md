# Evidence - HS-200-16

- **Story:** HS-200-16 - Prove the daily loop and open the owner pilot
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T02:51:54Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.qJngXs4vQV PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/e2e/test_phase200_daily_loop.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f381c9c2db434cf7d920d56588b85ffdac3d24f9

```text
..                                                                       [100%]
2 passed in 63.17s (0:01:03)
```

### Captured run — 2026-09-19T02:53:06Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.35X70IYgyZ uv run pytest -q -p no:cacheprovider tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f381c9c2db434cf7d920d56588b85ffdac3d24f9

```text
..................                                                       [100%]
18 passed in 24.05s
```


---

# The three parts, kept apart

**Read the headings before the contents.** This story closes on two
different kinds of thing: machine proof, and an owner's ruling. They are
not interchangeable, and the third section says what neither of them
covers.

---

## 1. What the MACHINE proved

Everything in this section was executed and observed by the rig above.
No human is involved in any of it.

**The rig.** `tests/e2e/test_phase200_daily_loop.py` (planned suite
`phase200_daily_loop`) drives the real product through its normal
controls in a real browser against a real booted hub, on an isolated
HOME with a fresh temporary database per run, once at 1440 and once at
393. R16-1: no live model — the brief drafts over a controlled
OpenAI-compatible adapter on 127.0.0.1 (HS-200-11's `FakeLLM` probe) and
the meeting extractors run a scripted engine. Only the words are canned;
the kernel, the wire, the receipts and every face are the product's own.
R16-6: the rig reads the database only through
`composition.current().db`.

**The eight stations.**

| Day | Station | What the machine drove |
|---|---|---|
| 1 | `day1-brief` | The Room's `Prepare a brief` well: a purpose by hand, `COVERAGE · 1 OF 2` before the run, the drafted document, `Keep` |
| 1 | `day1-meeting` | A transcript imported through the real route with a **day-1 `started_at_ms`**, linked to the Room, `Run intelligence`, the real plugin host and proposal bridge |
| 1 | `day1-review` | The Review wing: one decision and one commitment confirmed through the face's own `Confirm` |
| 1 | `day1-attention` | The arrival: the commitment is a real attention row, coverage incomplete rather than an all-clear |
| — | **the boundary** | Hub #1 stopped and its thread joined; a **second hub** booted on the same HOME and the same database file — story 13's own seam |
| 2 | `day2-recall` | Desk memory: the current decision first, its rationale, its source, `DEC 09-17` / `MTG 09-17` — dated to day 1 — then `Carry into brief` |
| 2 | `day2-people` | The Room's PEOPLE section: the person still carries yesterday's commitment |
| 2 | `day2-complete` | The commitment completed by explicit acts (`Set a date`, then `Mark done`) |
| 2 | `day2-carry` | People clear; day 2's preparation carries day 1's decision in `CARRIED FORWARD` |

**The day boundary is real, not simulated.** The product exposes no
clock-injection seam. The earlier working day comes from the product's
own `started_at_ms` import control, and the faces date the records from
the meeting (`holdspeak/services/recall_service.py:249-251`). Nothing
in the rig mutates a timestamp behind a face's back. Because
`capture_runtime_identity` caches once per OS process
(`holdspeak/runtime_identity.py:204,214-222`), the same-file claim is
proved through the uncached `database_identity()` and guarded by a fence
that fails if that seam ever stops telling two files apart.

**The measured record.** `assets/story-16-shots/loop-facts.json` / `.md`
(1440) and `loop-facts-393.json` / `.md`, plus 24 shots at 1440 and 393,
written only under `HOLDSPEAK_WRITE_SHOTS=1`. Per station and in total:
active time, corrections, abandoned paths, source coverage taken from
story 07's real projection (`GET /api/desk/needs-you?fresh=1`, the C4
vocabulary), and build and model identity read from the running product.

**Four defects only a second morning could see — found, fixed, fenced.**
Each fence was shown red without its fix, and counsel independently
re-ran all of them under mutation.

| Defect | Fix | Fence, red pre-fix |
|---|---|---|
| A proposal was dated by its own write time, not the meeting's — `from Architecture review 09-18` while recall said `09-17` | `meeting_started_at` on the needs-you row + the caption formats it | `assert 'Architecture review 09-17' in 'from Architecture review 09-18'` |
| `WAITING ON YOUR REVIEW · 1 DAYS` where the arrival said `1 DAY` | `_count_unit`, and the target chip through the tree's existing `pluralize` | `assert '1 DAYS' not in room_text`; `assert one_day_rows`; `'TARGET SEP 19 · 1 DAYS'.endswith('· 1 DAY')` is False |
| A commitment's due DATE drawn as a wall clock: `2026-09-20` → `DUE 18:00` | `dueDayToken` | `assert ['DUE 18:00'] == ['DUE 09-20']` |
| The CARRIED FORWARD ledger drew a commitment as `DEC · CURRENT` and a decision as `CMT` — an action item presented as an accepted decision | the record's `kind` carried from the Room projection through the manifest to the face | `assert ['DEC :: Draft the rollback runbook', 'CMT :: Rollback runbook is rehearsed on the read replica first'] == []` |

Seven fences stand in the rig in total; the seventh
(`database_identity_discriminates`) guards the boundary proof itself.

**Two Phase 143 census pins re-anchored, not widened.** Established
cardinality-exact first: 9 runner entrances and 50 routing references
before and after, the sets identical once line coordinates are stripped,
and no added line naming `InferenceRunner`, `.invoke(` or a resolver.
Pure line drift (+5 and +34 lines above the sites); three coordinates
bumped, nothing loosened.

---

## 2. What the OWNER ACCEPTED — a ruling, not an observation

> **"all walks may be considered as passed"**
> — the owner, 2026-09-19

**This is an acceptance, and acceptance is his to give.** It is not a
report of anything that happened. **No attended walk took place. Nobody
watched a human complete the daily loop through normal controls.**
Nothing in this repository records a person doing so, because no person
did.

What the ruling closes, named one criterion at a time:

| Acceptance criterion | Closes on | Note |
|---|---|---|
| AC1 — *Prepare a **real** conversation, capture its meeting, review a decision and commitment, and retrieve them on a later working day* | **Machine for the mechanism, ruling for "real"** | The cross-day retrieval is machine-proved end to end. The conversation was a scripted transcript and the drafting model a controlled local adapter, so the word **real** in this criterion is satisfied by the owner's ruling, not by evidence. |
| AC2 — *Record active time, corrections, abandoned paths, source coverage, and exact build/model* | **Machine** | `loop-facts.json` / `.md` and the 393 pair. The numbers describe a machine driving faces, which §3 qualifies. |
| AC3 — *The user completes the path through normal controls without implementation guidance* | **Ruling alone** | **Nobody observed this.** No human completed the path; no one tested whether it is followable without guidance. Accepted, not demonstrated. |
| AC4 — *Fixtures and live model results remain separate from the owner usefulness judgment* | **Machine** | The `legs` block keeps three legs apart in both records and now states the acceptance rather than contradicting it: `fixture_proven`, `live_model: NOT RUN`, `owner_usefulness_judgment: ACCEPTED BY OWNER RULING 2026-09-19, NOT OBSERVED`. |
| AC5 — *Open the ten-workday R1 observation period with predeclared tasks and denominators* | **Document** | `PILOT-R1.md`: tasks T1–T6, denominators, fixed definitions, an empty log. **The ruling does not start R1**, and R1 has not begun. |

**Satisfied without anyone having observed it — the plain list:**

1. **AC3 in full.** A human completing the daily path through normal
   controls: never observed.
2. **"without implementation guidance"** — whether the path is
   followable unaided: never tested.
3. **"a real conversation" in AC1** — the walk's conversation was a
   scripted transcript, never a real one.
4. **A live model anywhere on the daily path** — the drafting route was
   a controlled local adapter; `live_model` stays `NOT RUN`.
5. **Any usefulness judgment** — whether the carried work was worth
   carrying: no data exists.
6. **The phase's own verdict language.** The story's test plan asks for
   "a clear verdict" on a two-working-day sequence and says *a missing
   real opportunity remains inconclusive*. The verdict here is the
   owner's ruling; the real opportunity is still missing.

---

## 3. What remains UNKNOWN

Everything an attended walk would have surfaced that nobody has now
looked for. None of this is a defect claim — it is the list of questions
this story closes without answering.

**Usefulness — no data at all.**

- Whether the preparation brief told the owner anything he did not
  already know.
- Whether the decision and commitment the extractors proposed were the
  ones a human would have marked, and whether the extraction missed any
  (precision and recall have no sample).
- Whether recalling yesterday's decision on day two saved him anything
  against his own baseline, or cost him more than it saved.
- Whether the four rows of `CARRIED FORWARD` help or annoy.

**Followability — untested.**

- Whether a person finds `Prepare a brief` without being told the Room's
  result well cycles to it.
- Whether the day-2 path (Desk memory → search → `Carry into brief`) is
  discoverable, or only obvious to someone who read the design.
- Whether the commitment's staircase — `Name an owner` → `Set a date` →
  `Mark done` — reads as one obligation or as three chores.
- Whether the refusal states a real desk produces (a failed Watch, an
  unreachable model) are repairable by the person who hits them.

**What a rig can only assert, and a person would judge.**

- The rig finds elements by test id; a person finds them by eye. Every
  "the face shows X" here means the DOM carried X, not that anyone saw
  it. The shots are the only human-readable check, and I read them — one
  reader, not the owner.
- The rig never hesitates, never misreads a token, never clicks the
  wrong verb and never gives up. Its 20 seconds of "active time" is
  machine time; it is not a human minute and must never be quoted as
  one.
- The rig tolerates whatever the product renders as long as the
  assertion passes. Three of the four defects above were caught by
  *reading the shots*, not by the assertions — which is a measure of how
  much a rig alone misses.

**Known and deliberately left for a ruling (not defects):**

- Day two's brief lists yesterday's two confirmed outcomes **four
  times** — each once as a decision, once as a commitment — because
  confirming either kind deliberately records both
  (`holdspeak/services/proposal_bridge_service.py:588-590`). Every row
  is now labelled truthfully; whether the pair should be folded into one
  row is the owner's call.
- **No owner can choose a deterministic brief today.** The hub accepts
  `generator: "deterministic"` and the face never sends it, so every
  brief goes to a model route.
- The Room draws **three filled primaries** at once while proposals are
  pending, against UX-CANON's one.
- The Room's RECEIPTS ledger draws **10 rows with 2 distinct labels and
  no time, outcome or egress on any of them**.
- `target_at` has a writer with **no caller anywhere** in `holdspeak/`:
  no product surface sets a Project's target date.

**The instrument for all of the above is `PILOT-R1.md`, and it has not
begun.** The ruling closed this story; it did not open the window.
