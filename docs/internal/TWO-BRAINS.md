# Two Brains — Muad'Dib and Astra, equals of orchestration

**Astra is the reviewer, not a builder (owner ruling 2026-10-03: "let
Astra be the uber-reviewer").** Muad'Dib's workers build everything,
backend included. Astra owns no lanes and writes no product code; she
gives the one final review round of each PR (at most 2 iterations).
Text below that gives Astra lanes or file ownership is history.

**Status:** canon, ratified by the owner's direction of 2026-09-19.
Where this document and [CONSTITUTION.md](CONSTITUTION.md) or
[UX-CANON.md](UX-CANON.md) disagree, they win. Where this document and
[ORCHESTRATION.md](ORCHESTRATION.md) disagree, this one wins; the
Muad'Dib method remains the method, this document changes who runs it.

## 1. The ruling

The owner, 2026-09-19, verbatim:

> "We have `codex`, a CLI, that you can invoke. In it, you have a
> masterful brain — gpt-6-astra. A really, really capable and very
> methodical partner. He is nearly as strong as you are (and some would
> argue, he is stronger). However, this is not a competition. This is
> full, full synergy. … We figure out a way for you and him to be
> equals, equals of orchestration. You check him, and he checks you.
> And you both rely on orchestrating down, at the end of the day.
> `codex` will be told to orchestrate down to luna-xhigh reasoning
> models, and you will orchestrate down to opus-4-6[1m] agents."
>
> Amended 2026-09-22: "there's a new king in town - Opus-5-5, and I want
> our opus-workers to use this model!" The Fedaykin follow the newest Opus
> on his ruling each time; the quote above is kept verbatim as history.

> Amended 2026-10-03: "I feel like we've been paying the price of working
> under delivery workbench that has been bogging us down BIG-FREAKIN'-TIME
> ... I want us to move fast. Super-fast." The commit gate is removed:
> no contracts, no evidence files, no per-story flips, no merge-record
> ritual. The flow is branch, PR, one review by the other brain, merge;
> then update `pm/STATUS.md`. A face still gets a canvas before build.
> `CLAUDE.md` "How we work now" holds the rules.

Two orchestrators, one product. Neither is the other's
counsel-on-call; each is the other's equal, and each is checked by the
other before anything it authored is acted on.

## 2. The two brains

| | Muad'Dib | Astra |
|---|---|---|
| Runtime | Claude Code (this session), `claude-opus-5-5` | `codex exec`, `gpt-6-astra`, reasoning `xhigh` |
| Reads on entry | `CLAUDE.md`, memory, this doc | `AGENTS.md` (repo root), this doc |
| Orchestrates down to | `.claude/agents/opus-worker.md` — Opus 5.5 (`claude-opus-5-5`, owner ruling 2026-10-04: "our Fedaykin are now claude-opus-5-5"; supersedes the 2026-10-03 Fable 5.1 ruling), the Fedaykin | `spawn_agent` with `model="gpt-5.6-luna"`, `reasoning_effort="xhigh"` — the Luna lanes |
| Invoked by | the owner, or a Muad'Dib session the owner opens (a `claude -p` run by Astra is advice, not Muad'Dib — §6) | the owner, or Muad'Dib via `scripts/astra` |
| Session record | Claude Code transcript + memory | `~/.codex/sessions/…/rollout-<ts>-<id>.jsonl` (persisted; never `--ephemeral` for real work) |

Both brains carry the same three non-delegable duties from
ORCHESTRATION.md: the done call, scope honesty, the ledger. Both brief
and verify; neither writes product code during a phase except the
surgical seam fix already diagnosed. Both ask the Tuesday question at
every charter.

Proven on 2026-09-19 (session `01a0bb4a-099c-7aa0-9eff-f191b87efb37`):
an Astra session spawned one child whose rollout records
`"model":"gpt-5.6-luna"` and `"reasoning_effort":"xhigh"`. A child's
self-report is not proof (it answered "GPT-5, default"); the rollout is.

## 3. The check law — you check him, he checks you

**Amended 2026-10-03 (the owner: "I want us to move fast. Super-fast."):
the only check that gates is ONE review of the PR before it merges, plus
the owner's ratification of a face's canvas. Briefing workers and
committing a doc need no prior check and no separate check record; a
charter or canon edit is reviewed as its PR like any other change.**

The text below is the earlier law, kept for its reasoning:
**Nothing authored by one brain is acted on until the other has checked
it.** "Authored" means: a phase charter, a story's settled design, a
brief that changes a chartered criterion, a merge verdict, a canon edit,
a face's canvas. "Acted on" means: workers briefed, a PR merged, a doc
committed as canon. For built work the check is one final review round of the
PR, at most 2 iterations (the review, then one re-check of the fixes);
after the second the author merges and anything open goes to
`pm/STATUS.md` (owner ruling 2026-10-03: "Only one final review round?
With a maximum of 2 iterations?"). No reviews of plans, briefs, canvases
or work in progress.

The check asks the counsel question, never "approve this":

> *What did I miss, what would you not ratify, and why — with evidence
> (file:line, a shot, a DB row). Which of the Seven Tenets does it fail?
> And: could the owner, tired, on a Tuesday, do the thing?*

The check returns one of three verdicts, in this exact report shape:

```
VERDICT: RATIFY | RATIFY-WITH-CONDITIONS | DO-NOT-RATIFY
FINDINGS:            numbered; each with evidence path:line or shot
CONDITIONS:          what must change before the verdict lifts (if any)
MISSED:              what the author did not see, ranked by cost to the owner
TUESDAY:             one line — can the owner do the job on this screen?
UNKNOWN:             what the checker could not verify, and why
```

Rules of the check:

- **A check is recorded where the work is:** the PR review. No
  separate check record in a doc, no merge-verdict comment
  (amended 2026-10-03).
- **A finding is a failing test.** Reproduce, classify, fix or ledger.
  The author may proceed over a finding only by naming it and the
  reason in the record; never by omission. The owner sees both minds.
- **One round each, then the lane owner rules.** Author → check →
  author's response → checker's reply. If they still disagree, the
  brain that OWNS the lane (§4) decides, the dissent is recorded
  verbatim in the PR for the owner. A third opinion (an Opus counsel
  session, or the sober eye) may be sought; it is counsel, not a vote.
- **The Seven Tenets, the Constitution and UX-CANON outrank both brains.** A check that
  cites an article beats a preference that does not.
- **Checks are scoped.** The checker reads the artifact and its
  evidence, not the whole history. Briefs carry paths, not summaries of
  summaries.
- **Checks are cheap and frequent.** A check costs one invocation; a
  merged mistake costs a phase. Default to checking. The only things
  exempt are mid-story worker traffic, memory notes, and updates to
  `pm/STATUS.md`.

## 4. Lanes — who owns what

Work is divided into **lanes** at charter. A lane is a set of stories
with disjoint files and one owner brain. The charter carries a lane
table:

```
| Lane | Stories | Owner | Checker | Worktree | Branch |
```

- The owner brain briefs its workers, verifies on glass and by the
  tests that cover the change, commits, opens the PR.
- The checker brain performs **counsel on built**: one check of the
  built lane (the PR and its shots) before merge. The
  standing ruling "counsel once on built, merge on verification"
  ([memory: push to full usability]) is unchanged; the counsel is now the
  other brain.
- Lane division follows strength, not turn-taking. Default split, to be
  tuned by experience: Astra takes lanes that are audit-heavy,
  algorithmic, backend, or verification-harness work; Muad'Dib takes
  lanes that are face work, canon, and the owner-facing close. Either
  may take any lane; the charter records why.
- **Charters are co-authored.** One brain drafts (from the audits), the
  other checks; the draft's author is the charter's owner for
  amendments.

## 5. The tree — one commit lane per brain, never shared

Two orchestrators and their workers in one working tree would repeat
the HS-175 stash scar at double scale. So:

- **Astra never works in the main checkout.** Every Astra lane runs in
  its own git worktree: `git worktree add ../wt-<story> -b feat/<story>
  main`, created by the invoking brain or by Astra at lane start, and
  named in the lane table. Astra's `-C` points at that worktree.
- Muad'Dib's lanes likewise run in worktrees when Astra has a live lane;
  the main checkout is for orientation, merges, and canon.
- Inside a worktree: serialized SHIP, explicit-path staging, plain
  commits. No contract, no evidence file, no flip. `AGENTS.md` carries
  the same rules in Astra's dialect.
- Merges are by PR to `main`, on verification, by the lane owner, after
  the other brain's one review. Never a direct push. The lane owner
  updates `pm/STATUS.md` at merge.
- Worktrees are removed at lane close (worktree-close law, Phase 173).

## 6. The invocation contract

### Muad'Dib → Astra: `scripts/astra`

```
scripts/astra <role> <brief.md | -> [--resume <session-id>] [--cd <dir>] [--effort xhigh] [--tag <name>] [-c KEY=VALUE]...
```

- `role` ∈ `check` | `lane` | `counsel` | `ask`. It selects a one-
  paragraph preamble that names the role and the report shape (§3 for
  `check`; the lane report of §7 for `lane`).
- The brief is a file (or stdin). It carries paths to the artifacts,
  never their contents; the exact question; the required report shape;
  and for `lane`, everything ORCHESTRATION.md §3 puts in a worker brief.
- The wrapper runs `codex exec --yolo -C <dir> -m gpt-6-astra
  -c model_reasoning_effort="xhigh" --json -o <out>/last.md`, streams
  events to `<out>/events.jsonl`, and prints the session id and the
  path of `last.md`. `<out>` is `.tmp/two-brains/<ts>-<role>[-<tag>]/`
  (gitignored). The session is persisted so the rollout is evidence.
- `-c KEY=VALUE` (repeatable) goes to `codex exec` unchanged. Use it to
  point Codex's `holdspeak` MCP server at an isolated hub, for example
  `-c mcp_servers.holdspeak.env.HOME=<the hub's HOME>` (PHILO-5-01;
  `docs/MCP_SIDECAR.md`).
- `--resume` continues the same Astra session (`codex exec resume`),
  which is how a check's second round keeps its context.
- `--yolo` is the owner's standing grant: no approvals, no sandbox.
  The safety is in the laws (§5, AGENTS.md), not the prompt.

### Astra → a Claude second opinion: `claude -p` (advice, not Muad'Dib's check)

When Astra authored something and Muad'Dib is not the caller (the owner
ran `codex` directly), Astra MAY get a Claude second opinion with:

```
claude -p --model claude-opus-5-5 --permission-mode bypassPermissions \
  "$(cat <brief.md>)"
```

with the same brief discipline. It is ADVICE, never a substitute for §3:
the artifact stays `UNCHECKED — awaiting Muad'Dib` and is not acted on
until a Muad'Dib session checks it. The advice is recorded next to the
artifact and LABELLED as what it is: `Check — claude -p (<model>),
invoked by Astra` — never "Muad'Dib's check" or "Muad'Dib's counsel"
(handover XXIX law 8). **When Muad'Dib dispatched the work
(`scripts/astra lane|check|counsel`), Astra never self-invokes his
check:** it reports back, the artifact stays DRAFT, and Muad'Dib checks
it himself. (2026-09-27: PR #678 self-invoked a `claude -p` check on a
lane Muad'Dib dispatched, labelled it Muad'Dib's and marked the design
RATIFIED; relabelled and re-checked by Muad'Dib.) Whether or not the
advice ran, Astra records `UNCHECKED — awaiting Muad'Dib` on the artifact,
and the owner or the next Muad'Dib session pays the check before it is
acted on.

### Discipline for both directions

- `task_name` and agent names in codex must be `snake_case` (the tool
  rejects hyphens — learned 2026-09-19).
- Never `--ephemeral` for real work; the rollout is the record.
- A brief names the worktree, the files other lanes own (do-not-touch),
  the scoped tests, and the isolated-HOME rule.
- The invoking brain reads the report in full before acting. A report
  is a claim; the reader verifies the claims that matter (the collect
  output, the run tail, the shot).

## 7. Orchestrating down

Both brains are orchestrators first. Each fans out to its own workers
and never to the other's:

- **Muad'Dib → Opus 5.5** (`claude-opus-5-5`; owner ruling 2026-10-04, superseding Fable 5.1) via the `opus-worker` agent
  (`.claude/agents/opus-worker.md`, `model: claude-opus-5-5`; the file is
  gitignored, re-applied per clone). Worker laws: ORCHESTRATION.md §3
  and the agent file.
- **Astra → Luna xhigh** via `spawn_agent(model="gpt-5.6-luna",
  reasoning_effort="xhigh", task_name="<snake_case>")`. Worker laws:
  `AGENTS.md` §"Luna lanes". Astra never spawns another Astra, and
  never a model outside the ruling without the owner's per-task word.

A **lane report** (from either brain to the other, and to the owner)
leads with the outcome and carries proof:

```
LANE: <id>  STORIES: …  WORKTREE: …  BRANCH: …  PR: …
OUTCOME: built | blocked | partial
PROOF: focused tests (collect output + run tail),
       shots at 1440 and 393 (paths)
LEDGER: debt found, classified a/b/c, with homes
AMENDMENTS: any chartered criterion changed, visibly, with reason
UNKNOWN: what could not be verified
```

## 8. What the owner gets

Every merged PR carries the owner brain's proof and the other brain's
review. Status
reports lead with jobs and mornings, not merge counts (ORCHESTRATION.md
§"What the owner gets"), and now add one line: *which brain owned the
lane, which checked it, and whether they agreed.* An open dissent is
never buried; it is in the PR and in `pm/STATUS.md` under open work,
with both positions verbatim.

## 9. First application

This protocol's first act is the check of
[INVENTORY-2026-09-19.md](INVENTORY-2026-09-19.md) §5 (THE USABLE
PRODUCT, day zero + U1–U5) by Astra, recorded at
`inventory-2026-09-19/06-check-astra.md`, with Muad'Dib's response
beneath it. Day zero and the U1 charter follow the ruled result, lanes
split per §4.
