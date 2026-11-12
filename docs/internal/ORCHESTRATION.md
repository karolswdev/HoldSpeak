# Orchestration: one brain, Codex builders, one wave at a time

This document tells you how the orchestrator runs the Codex builders in this
repository. It records the method in use on 2026-11-10, the principles behind
it, and the failures that made each rule. The owner asked for it on 2026-11-10:
"Could you please document your approach to orchestrating all these codex
sessions? And your principles?"

The method before 2026-11-07 is parked in
[ORCHESTRATION-through-2026-11-07.md](ORCHESTRATION-through-2026-11-07.md).
The rules that outrank this document are in
[CLAUDE.md](../../CLAUDE.md#how-we-work-now-one-brain-one-loop-three-checks-owner-ruling-2026-11-07)
and in [AGENTS.md](../../AGENTS.md#roles-and-delegation). Where this document
disagrees with one of them, that file wins.

## 1. The roles

| Role | Who | What it does | What it never does |
|---|---|---|---|
| Owner | Karol | Gives direction in a sentence. Judges a face live on his desk. | Reads a builder report. |
| Orchestrator | Muad'Dib (Claude) | Decides the work, writes the briefs, judges the results, merges, runs the checks on main, writes the records. | Writes product code. Asks the owner for permission between waves. |
| Builder | Codex Sol, one `codex exec` session for each lane | Builds one brief in one worktree. Runs its own tests. Opens one pull request. | Merges. Edits the main checkout, the served hub, `pm/STATUS.md` or the handover. |
| Reviewer | A fresh Codex session | Reads one merged diff on a security surface and gives a verdict. | Sees the builder's context. Changes a file. |

The orchestrator and the builders are different models from different
vendors. This is an owner ruling (2026-11-09), not a technical need.

## 2. The principles

Each principle has the owner's words or the failure that made it.

1. **One wave at a time, at most six builders.** Owner, 2026-11-09: "There's
   too much shit going on. Your context gets filled up too." A wave starts
   when the wave before it is merged, checked and recorded.
2. **The orchestrator's context is the scarce resource.** A builder writes
   its events, its errors and its report to files. The orchestrator reads the
   final message, the pull request body, the diff size and the shots. It does
   not read a builder's event stream.
3. **The brief is the step text.** There is no plan document, no contract and
   no completion report. A brief carries the owner's words, verbatim and
   dated, so that the builder serves the sentence and not a paraphrase.
4. **A drawing comes before a face.** A new face is drawn on a canvas first
   and the link goes in the brief. A drawing only picks a direction. Only the
   owner's word on his live desk judges a face.
5. **The kit comes first.** One lane builds a shared piece and that lane
   merges before an app lane uses the piece. An app lane never adds a
   stylesheet or a second implementation to get a face done.
6. **Lanes of one wave share no files.** One wave has at most one hub lane.
   The other lanes are app lanes, each on its own directories.
7. **A builder decides and ships.** A builder cannot ask a question while it
   runs. The brief says: decide, ship the first whole part, list the rest
   under "Left". The orchestrator then holds the "Left" list against the brief.
8. **The same session fixes its own work.** A follow-up goes to the session
   that built the change, because that session holds the context. A red on
   main goes to the session whose merge caused it.
9. **A fresh session reviews.** A reviewer that saw the builder's reasoning
   confirms it. The review brief has the diff range and the questions, never
   the builder's conclusions.
10. **The orchestrator judges every face itself.** It looks at each pane at
    the owner's window size (900 × 600) and at phone width (393), at full
    size, before a merge. A builder's sentence about a face is not evidence.
11. **No quality words about a face.** A report to the owner says what
    changed and what is off. The owner decides if a face is good.
12. **Checks run once, on main, by the orchestrator.** A builder runs the
    tests that its brief names. A red after a merge is fixed forward at once.
13. **A change subtracts.** Each pull request states its net live lines. A
    rebuilt face parks the old face in the same pull request.
14. **Nothing is lost by accident.** A face lane's pull request has a table:
    each old behaviour and where it lives now.
15. **Every merge is revertible, and nothing is deleted.** Retired code is
    parked. `main` receives pull requests only.
16. **The loop does not stop for permission.** Owner, 2026-11-10: "Yes, I do
    want you to continue orchestrating this further." The recommended
    direction is approved in advance. The owner stops the loop with a sentence.

## 3. One wave, step by step

### 3.1 Read before you pick

1. Read the feedback bundles in `~/.local/share/holdspeak/feedback/`. The
   owner writes them from "Show me" on his desk.
2. Read the newest owner sentences in memory and the "Still off" list in
   [HANDOVER.md](HANDOVER.md).
3. Run `uv run python scripts/operation_parity.py` for the hub numbers.
4. Pick work by core workflow. Each wave pairs one hub lane with app lanes.

### 3.2 Draw, when a face is new

Draw the face on a canvas with the kit's own pieces at 900 × 600 and at 393.
Publish the canvas and put the link in the brief. If the owner answers, his
sentence goes into the brief verbatim. If he does not answer, build the
recommended direction and say in each report that he has not judged it.

### 3.3 Write the briefs

A wave has one common brief and one short brief for each lane. The common
brief is the same text for every builder of the wave:

| Section | What it holds |
|---|---|
| Who you are | The owner's sentences for this wave, verbatim and dated. |
| Read first | Three to six files, by path. Never pasted text. |
| Where you work | The lane's worktree and branch. Never the main checkout or the served hub. |
| Rules that decide a merge | The direction, park never delete, one test that fails on main, the text rules, the security surfaces. |
| Tests | The lock, the isolated HOME, `-n 4`, and the exact runs for a hub lane and for a face lane. |
| What the last waves taught | One line for each failure in section 6 that a builder can prevent. |
| Ship | Explicit-path commits, push, `gh pr create`, do not merge. The shape of the pull request body and of the final message. |
| Shots | The window sizes and the folder for the screenshots. |
| Known on main | The reds that are not this lane's, so that it does not chase them. |

The lane brief holds only what differs: the job, the owned paths, the paths
of the other lanes (do not touch), the settled design, each state that must
have a shot, and the capabilities that must survive.

Two things make a brief work. Name files and tests by path, and state each
acceptance as something a test or a shot can show. Tell the builder what to
do when it cannot finish: ship the first whole part and list the rest.

### 3.4 Start the builders

```bash
export HS_ORCH=<a directory for this session's briefs and reports>
HOLDSPEAK_SKIP_WEB_BUILD=1 scripts/lane.sh new face/send-kit-20261110
scripts/orchestrate/run_lane.sh wave9 send face/send-kit-20261110
```

Run `run_lane.sh` as one background command for each lane. It joins
`$HS_ORCH/wave9/_common.md` and `$HS_ORCH/wave9/send.md`, fills in the
worktree and the branch, and runs one `codex exec` session to its end. The
report is `$HS_ORCH/wave9/out/send/last.md`. The harness tells the
orchestrator when the command ends. Do not poll.

### 3.5 Read a report

Read these four things, in this order, and nothing else:

1. `last.md`: the pull request, what changed, what passed, what is left.
2. The pull request body: the STATUS line, the behaviour table, the net lines.
3. `gh pr view <n> --json additions,deletions,mergeable`.
4. The shots. Crop each 900 × 600 window out of its desk shot, put two on a
   sheet and look at the sheet at full size. Put six phone shots on a sheet.

Then decide one of three things:

- **Merge.** The brief is met, or what is left is small and named.
- **Another round.** Write what is off as a numbered list and send it to the
  same session with `scripts/orchestrate/resume_lane.sh`.
- **Hold.** The builder cut the scope on its own. Send a round that names
  each missing capability and where it must sit. Do not merge a part of a
  flagship face with capabilities parked and no seat.

Write what is off as the owner would see it: "the verbs are hidden under
Actions at 900", not "improve the toolbar".

### 3.6 Merge and check

```bash
gh pr merge <n> --merge
gh pr view <n> --json state,mergeCommit -q '.state+" "+.mergeCommit.oid[0:9]'
git -C <main checkout> pull -q --ff-only origin main
scripts/orchestrate/checks_main.sh <the last green head>
```

`checks_main.sh` runs the quick check, the main check and the whole
non-browser suite, once, after the batch. Its last line is
`RESULT quick=<rc> main=<rc> suite=<rc>`. Do not pull or branch in the main
checkout while it runs.

When a check is red, find the merge that caused each red and send the list
to that builder's session. The builder works on a new branch from
`origin/main`. After its fix merges, run `scripts/quick_check.sh --retry` and
`scripts/main_check.sh --retry`. Do not debate a red and do not revert first:
a fix forward took 19 minutes on 2026-11-10.

### 3.7 Review a security surface

A merge that touches the gate boundary, a token page, egress, Telegram or
credentials gets one review round after the merge.

1. Write `$HS_ORCH/<wave>/out/<name>/brief.md`: the diff range, the surfaces,
   the questions, "read only, run nothing, change nothing", and the verdict
   shape (`VERDICT`, `FINDINGS` with file and line, `NOT VERIFIED`).
2. Run `scripts/orchestrate/review.sh <wave> <name>`.
3. Send each finding to the builder's session at once. The fix merges
   without a second review round.

On 2026-11-10 all five review rounds returned "NOT RATIFIED", with two to
nine findings each. The round costs one session and about ten minutes. Keep it.

### 3.8 Put it on the owner's desk

When main is green, move the served checkout to the new head. The served
checkout is named in [HANDOVER.md](HANDOVER.md), Part III.

```bash
cd <served checkout> && git fetch -q origin
git diff --name-only HEAD <sha> -- uv.lock pyproject.toml web/package-lock.json
git checkout -q --detach <sha>
(cd web && npm run build)
kill "$(pgrep -f 'holdspeak.cli_entry web --no-open')"
HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_UI_FEEDBACK=1 nohup .venv/bin/python -m holdspeak.cli_entry web --no-open >> <hub log> 2>&1 &
```

Run `uv sync --extra dev` or `npm ci` only when the second command prints a
file. Wait for the hub to answer on `127.0.0.1` and on the Tailscale address.
Then read the feedback folder again.

### 3.9 Record, then report

| Record | Where | When |
|---|---|---|
| The ledger | `$HS_ORCH/ledger.md`, one line for each event | At once: a launch, a report, a merge, a check, a round. |
| Status | `pm/STATUS.md`, one line for each merge, review and check | One records pull request at the wave boundary. |
| Handover | [HANDOVER.md](HANDOVER.md): what the wave did, what is still off, the lane rules it taught | The same pull request. |
| Memory | The owner's sentences, verbatim, with the reason and how to apply them | When he says them. |

The ledger is what lets a session with a new context continue. Write a line
before you start the next thing.

The report to the owner comes at the wave boundary, not at each merge. It
says what changed, what is still off, and what runs next. It gives both hub
addresses, the Tailscale address first, each in its own code block. It never
says that he approved a thing that he has not judged.

After the report, run `scripts/lane.sh purge` and start the next wave.

## 4. The tests a lane runs

Every run goes through `scripts/test_lock.py` with an isolated HOME. A
focused run uses `-n 4`.

| Lane | Before it pushes |
|---|---|
| Any lane | Its focused test files, and one test that fails on main. |
| Hub lane | The whole non-browser suite, once, on the branch merged with `origin/main`. |
| Face or kit lane | Whole vitest, the desk sweep, the `tests/e2e/*_glass.py` files of the apps it touches, and `tests/unit/test_ux_canon_ratchet.py`. |
| A lane that parks or renames a face | The non-browser tests that read the web tree also. |
| A lane that changes the shape of a hub answer or the words of a refusal | The whole non-browser suite, and a new recording of each stored answer that holds the shape. |

A builder never runs `scripts/quick_check.sh` or `scripts/main_check.sh`.
Those are the orchestrator's, once, on main.

## 5. When the owner speaks

1. Save his sentence to memory, verbatim, before you act on it.
2. If it changes the direction, stop launching. Let the running builders
   finish their pull requests.
3. Answer in a few lines: what you understood and what you do next.
4. Put his sentence in the next common brief.

One sentence from him is a ruling. A notification from a background task is
not his word, and neither is your own earlier message.

## 6. What went wrong, and the rule it made

| What happened | The rule now |
|---|---|
| Five builders each ran the whole check. They waited on the lock for 40 minutes. | A builder runs its named tests. The orchestrator runs the checks once on main. |
| Parallel lanes changed one shared hub and each missed the reds of the others. | One hub lane for each wave. It ends with the whole non-browser suite on the merged branch. |
| The sweep and vitest missed seven browser reds and one canon red. | A face lane runs the glass files of its apps and the canon ratchet. |
| A rebuilt face lost a behaviour: #2181 lost "Stop shows what was said", #2183 lost the Revoke question. | The behaviour table in the pull request body. Each destructive verb and its question is a row. |
| A lane parked a face and left three reds in tests that it never ran (#2194). | A lane that parks or renames a face runs the non-browser tests that read the web tree. |
| The orchestrator repeated a builder's word for a face. The owner opened the pane at 900 × 600: the buttons had no space between them. | The orchestrator looks at each pane itself at his size. No quality words. |
| A new field in a hub answer, or new refusal words, left stored answers and word fences red. This happened twice on 2026-11-10 (the reds fixed in #2221 and in #2224). | The last row of section 4, in every common brief. |
| A builder shipped a "first slice" of the flagship face. About twelve capabilities had no seat (#2223). | Hold. Send a round that names each one. |
| A lane held its pull request while it waited for the reds of another lane. | A lane pushes and names the reds that are not its own. |
| A diet took a control off a face. The control was the permission for a model call (#2194). | A change that removes a permission control is a security step and gets the review round. |
| The owner stopped the running sessions by accident. | `resume_lane.sh` continues a session from its thread id. The id is in the first line of `events.jsonl`. |
| The orchestrator's context filled with builder output and it lost its place. | Reports go to files. The ledger holds the place. One wave at a time. |
| A check ran in the main checkout while a pull changed the tree under it. | Do not pull or branch in the main checkout while a check runs. |
| An app lane made the kit's tab strip scroll sideways. The change showed half a word in every app that has tabs. | A kit change is judged in every app that uses the piece, at 900 × 600 and 393. The builder attaches those shots. |
| The whole suite was green and the quick check was red. Three tests failed only after other test files ran in the same process. The retry ran no test and said green. | A red that passes alone is not a flake until a leak is ruled out: run its file after its neighbours in one process. A retry that ran no test is a red. |
| A flagship PR needed a fit round and its review had four findings. Two rounds would have held the wave for a night. | Merge the PR, hold the redeploy, and send ONE round with the fit items and the findings to the builder's own session. Redeploy after that round is merged. |
| The builders' credits ran out in the middle of wave 10. The wave stopped half merged: one review not fixed, four pull requests not judged. | Probe the builders' credits before a wave starts. At a stop, write the handover with the order to continue. |
| Merges and the redeploy waited for GitHub CI and for a green on main. The owner: "Run this locally instead." | Nothing waits on GitHub CI. The local checks run once for each batch. Judged pull requests merge, and the hub is redeployed, while the checks run. A red goes forward to the builder that caused it. |
| The orchestrator's context filled two times in one session. Pictures were about half of it and shell output was most of the remainder. | A fork of the orchestrator judges a large shot set and returns only the off list. Cut each shell output. |
| `checks_main.sh` found no suite worktree: `lane.sh purge` had removed `wt-suite-main` as merged and clean. The suite did not run. | Before the checks, make sure that `wt-suite-main` exists. Make it again with `lane.sh new suite-main`. |

## 7. Numbers from 2026-11-10

| Measure | Value |
|---|---|
| Merge commits on main | 86 |
| Lanes in wave 9, in parallel | 7 |
| A lane, from start to pull request | 46 to 105 minutes |
| A reds round in the builder's own session | 19 minutes |
| The checks on main (quick check, main check, whole suite) | about 14 minutes |
| Review rounds, and how many ratified | 5, and 0 |
| Batches of checks with a red the first time | 5 of 8 |

Five batches of eight with a red is the weak point of the method. Each red was fixed
forward in less than an hour, but each one also delayed the redeploy to the
owner's desk. The rules in section 4 are the answer so far.

## 8. The files

| File | Purpose |
|---|---|
| `scripts/lane.sh` | Makes and removes a lane's worktree. |
| `scripts/orchestrate/run_lane.sh` | Starts one builder on one brief. |
| `scripts/orchestrate/resume_lane.sh` | Sends a follow-up round to the same session. |
| `scripts/orchestrate/review.sh` | Runs the one review round in a fresh session. |
| `scripts/orchestrate/checks_main.sh` | The checks on main after a merge batch. |
| `scripts/orchestrate/suite_main.sh` | The whole non-browser suite on `origin/main`, in its own worktree. |
| `scripts/orchestrate/_env.sh` | The paths and the builder model. |
| `scripts/test_lock.py` | The one CPU budget for all test runs. |

The scripts read these variables: `HS_ORCH` (the directory for briefs,
reports and the ledger; default `.tmp/orchestrate`), `HS_CODEX` (the `codex`
binary), `HS_BUILDER_MODEL` (default `gpt-6.1-sol`), `HS_BUILDER_EFFORT`
(default `high`), `HS_REVIEW_WT` and `HS_SUITE_WT` (the two worktrees).
