# Evaluating a model route: the scoring protocol

**Protocol version:** 1. **Corpus version:** 1 (33 episodes).
Owner: HS-200-08. Read with
[Phase 200 ACCEPTANCE](../../../../pm/roadmap/holdspeak/phase-200-the-working-practice/ACCEPTANCE.md)
and [CONTRACTS §C2, §C12](../../../../pm/roadmap/holdspeak/phase-200-the-working-practice/CONTRACTS.md).

This document says how a route is evaluated, what the report means, and how a
person scores the part no deterministic check can score.

## What the harness is

Three pieces:

| Piece | Where | What it is |
|---|---|---|
| The corpus | `tests/fixtures/phase200/corpus/` | 33 versioned episodes: 11 Interview, 11 meeting extraction, 11 grounded brief and update. Each carries its material, its invariants, and its `split`. |
| The checks | `tests/fixtures/phase200/checks.py` | Six deterministic invariants. No model, no clock, no network. Severity lives here, not in the corpus. |
| The runner | `scripts/phase200_eval.py` | Drives each episode through the real product path with a selected route, judges the outputs, writes a report. |

The material is synthetic. Two fictional projects (Delta migration, Northwind
billing rewrite) and fictional people. Nothing in the corpus comes from the
owner's data, so a report can be attached to public evidence as it stands.

## The split, and why it is fixed

Every episode is `train` or `held_out`. The split was assigned when the episode
was written, before any prompt or recipe change was measured against it. Twelve
of the 33 episodes are held out, four in each category, which keeps every
category above the one third the phase requires.

A tuning step may read training episodes only. `checks.read_for_tuning`
raises `HeldOutEpisodeError` on a held-out episode, and the test suite proves
it. When a real failure becomes a regression case, add it as a `train`
episode. The held-out set is only ever extended, never rewritten to match a
result.

## Running it

The route is a real configured endpoint. The run is isolated: a temporary
HOME, a temporary database and a temporary model root per episode. It never
reads or writes the owner's data.

```sh
uv run python scripts/phase200_eval.py run \
    --endpoint http://192.168.1.43:8080/v1 \
    --model qwen2.5-32b-instruct \
    --report .tmp/phase200-eval-$(date +%Y%m%d).json \
    --raw .tmp/phase200-eval-$(date +%Y%m%d)-raw.json
```

Useful flags:

- `--category interview|meeting|update` and `--episode IV-01` narrow the run.
- `--split held_out` runs the acceptance set alone.
- `--limit N` caps episodes per category.
- `--repeat N` runs the selection N times. Repeat a subset to expose
  variability. Every trial is kept, including the failed ones.
- `--engine canned --canned <file>` substitutes the model with recorded text
  served from a local OpenAI compatible stub. It proves the harness, never the
  model.

Rebuild the manifest after adding an episode:

```sh
uv run python scripts/phase200_eval.py manifest
```

## What a green report looks like

The command exits 0 when no episode has a critical failure, and 1 when one
does. A report worth calling green has all of:

- `route.state` is `READY`, with a `plan_id`, a `boundary` and a `host`. An
  `UNREACHABLE` route means the run measured nothing.
- `totals.critical_failures` is 0.
- Every episode has an empty `error`. An episode that raised is retained with
  its error and its traceback, and it counts as a failure.
- Each update episode's raw `generator` starts with `model:`. A `deterministic`
  generator means the model drafter fell back and that episode measured the
  deterministic drafter instead.
- `review_effort.total` items have actually been inspected by a person, per the
  rubric below. Until that happens the report is a machine result, not an
  acceptance result.

Soft failures (`correction_absent`, `question_repeated`, `missing_typed_unknown`,
`missing_supersession`, `claim_missing`) are quality findings. They lower the
pass rate and they do not block on their own.

## The report's fields

| Field | Meaning |
|---|---|
| `corpus_version`, `protocol_version` | What was run and under which rules. |
| `engine`, `model`, `route` | The route: engine, model id, endpoint, resolved plan id, boundary, host, and the preflight probe's own latency and state. |
| `build` | Backend build, frontend build, schema version and config revision, from the runtime identity of HS-200-02. |
| `episodes[].material_sha256` | The context identity: the sha256 of the episode's canonical material. |
| `episodes[].invariants` | Every invariant, with its failure kind, its criticality and a detail line. |
| `failures_by_kind` | Failure counts across the run. |
| `support_judgments` | Every claim's C2 support axis, counted. |
| `latency_ms` | Count, min, median and max per episode. Model time, not human effort. |
| `review_effort` | What a person must inspect: every critical failure plus every held-out episode, counted once each. |
| `verdict`, `critical_verdict` | `verdict` is pass only with zero failures of any kind. `critical_verdict` is the gate. |
| `judge` | The supplementary LLM judge. Off by default and never gating. |

## The six invariants

| Invariant | Passes when | Critical failure |
|---|---|---|
| `correction_honoured` | The corrected value is stated and the superseded one is not, or is named as the old one. | The superseded value is asserted as current. |
| `question_not_repeated` | No already answered question is asked again, however reworded. | None. A repeat is a soft failure. |
| `absent_source_unknown` | A value no source carries comes back as a typed unknown. | A concrete value appears where no source carries one, including a date or number literal absent from all the material. |
| `typed_unknown_field` | An uncertain or ambiguous value stays a typed unknown. | An ambiguity is resolved to one candidate, or an uncertain field is filled. |
| `stale_decision_superseded` | A superseded decision is marked superseded. | It is restated as current. |
| `citation_not_supported` | A claim citing a source that does not carry its sentence stays unknown, source linked or disputed. | It comes back `supported`. |

Severity is a property of the check, not of the episode file. A corpus file
cannot downgrade an invented value, which is what "cannot be averaged away"
means in practice.

## The human part

Deterministic checks establish that a run did not invent a fact. They do not
establish that its answer was useful, and they judge language coarsely. Two
things need a person.

### 1. Every critical failure requires source inspection

For each id in `review_effort.critical_failures`:

1. Open the raw output for that episode in the `--raw` file.
2. Open the episode's material in `tests/fixtures/phase200/corpus/episodes/`.
3. Answer, from the source alone: does the material carry the value the run
   stated? Yes or no.
4. Record the answer. A "no" is a confirmed critical defect and blocks the
   gate. A "yes" is a corpus defect, and the fix is the episode, not the score.

No summary, no judge, and no aggregate substitutes for this step.

### 2. Every held-out episode gets a reviewer's yes or no rubric

For each id in `review_effort.held_out_episodes`, answer six questions with a
plain yes or no, reading the raw output beside the episode's material:

1. **Grounded.** Is every name, date, number and status in the answer carried
   by the material?
2. **Honest about absence.** Where the material is silent, does the answer say
   so rather than fill the gap?
3. **Current.** Where a correction or a supersession is in the material, does
   the answer use the current value?
4. **Non repetitive.** Does it avoid asking for something already supplied?
5. **Useful.** Would this answer save the reviewer work on a real task of this
   shape?
6. **Actionable.** Is the next step it proposes one a person could actually
   take?

Questions 1 to 4 restate the deterministic invariants; a disagreement between a
reviewer and the checker is worth recording, because one of the two is wrong.
Questions 5 and 6 are the part only a person can answer.

### Recording the result

Write the scores beside the report, as `<report>.review.json`:

```json
{
  "report": ".tmp/phase200-eval-20260906.json",
  "protocol_version": 1,
  "reviewer": "owner",
  "reviewed_at": "2026-09-06T18:00:00+02:00",
  "critical_inspections": [
    {"episode_id": "MX-02", "material_carries_the_value": false,
     "verdict": "confirmed_defect", "note": "the cutover date was corrected in the transcript"}
  ],
  "held_out_scores": [
    {"episode_id": "UP-03", "grounded": true, "honest_about_absence": true,
     "current": true, "non_repetitive": true, "useful": false, "actionable": true,
     "note": "correct but restates the whole inventory"}
  ]
}
```

Keep the report, the raw outputs and the review file together. Publish only
synthetic or redacted material, which the corpus already is.

## The supplementary judge

An LLM judge may triage a large run, and it appears in the report as one
column under `judge`. It is off by default. It never decides a pass, it never
clears a critical failure, and its column is never the only evidence for an
acceptance claim. This follows §C12 and the phase's evidence levels: a scripted
or model judge is appropriate for triage and insufficient for usefulness.

## What this harness does not establish

State these beside any result that uses it.

- **The Interview leg** replays the episode's owner turns as real turns and
  reads the last answer plus the recorded Interview state. Repeated question
  avoidance is prompt behaviour in the product, so that invariant is judged
  from the answer text, not from a state machine.
- **The meeting leg** runs the real plugin chain and the real builtin plugins
  with an admitted dispatch minted through the test side admission rig. The
  intel queue's own scheduling, retries and receipts are not exercised here.
- **The update leg** models an unavailable source by leaving it out of the
  seeded evidence inventory. It measures what the drafter does with what it can
  read, not the coverage machinery's own reporting of a failed read.
- **The route profile is named after the model id**, because the update
  drafter resolves a deployment revision by matching `deployment_revisions.model`
  against the assigned profile id. A profile whose id differs from its model id
  resolves nothing and the model drafter falls back silently. The report's
  per-episode `generator` is how you tell which happened.
- **A canned run proves the harness, not the model.** Only a run against a real
  route is evidence about a model.

## Related

- [Phase 200 acceptance protocol](../../../../pm/roadmap/holdspeak/phase-200-the-working-practice/ACCEPTANCE.md)
- [Phase 200 technical contracts](../../../../pm/roadmap/holdspeak/phase-200-the-working-practice/CONTRACTS.md)
- [Releasing, upgrading, and your data](../../../RELEASING.md)
