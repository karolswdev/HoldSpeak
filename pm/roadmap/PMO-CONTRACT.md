# PMO Contract

**Owner:** PMO.
**Status:** canonical rules for any project that installed `pmo-roadmap`.
**Read this if:** you are about to commit, or you got blocked by the
pre-commit hook.

---

## What this is

Every commit in this repo passes through a `pre-commit` gate (`dw
gate`) that requires you (agent or human) to hold a fresh
`.tmp/CONTRACT.md` with all checkboxes set to `[x]`. Generate it with
`dw contract new` after staging: it stamps machine-verified facts —
branch, HEAD, `git write-tree` index tree, the staged file sample, and
the story ID(s) it covers — and the gate re-derives each fact at
commit time. The index tree is the freshness proof: a contract written
for a different staging state is stale by definition
(`contract-index-tree-mismatch`), and touching the file cannot refresh
it. Checked boxes are verified against the rule titles in this
document's contract template — canonical plus project extensions —
not merely counted (`contract-unknown-box` / `contract-missing-box`).

On success the trail is durable: the `commit-msg` hook stamps
`PMO-Story:` and `PMO-Contract-Digest:` (sha256) trailers onto the
commit message, and `post-commit` archives the exact contract — plus
any `BUNDLE-OK.md` rationale — under `.git/pmo-contract-archive/<sha>`
before clearing the working files. An aborted commit leaves the
contract in place for the retry.

The certification has two purposes:

1. Force a re-read of the rules at commit time, when context is
   sharpest and stakes are highest.
2. Make every commit auditable — if an agent ever ships shoddy work,
   they did so having explicitly certified otherwise, and the archived
   contract plus digest trailer prove exactly what was certified.

The hook will not lecture you about the rules. They live here.

---

## The rules

These apply to every commit, regardless of project.

### 1. Evidence, not vibes

If this commit claims work shipped (a story marked `done`, a phase
exit-criterion checked, a "fixed bug X" message), the corresponding
evidence is on disk.

For roadmap-tracked work that means an `evidence-story-{n}.md` file
with **actual command output**, not a summary. For non-roadmap work
that means commit message references to test runs / outputs you
actually saw.

Type-check passing is not validation.

### 2. Master docs updated in this same commit

If this commit ships a story, the relevant tracking docs are updated
in the same commit:

- the story-file header status (moving through the canonical
  story-status vocabulary declared in `roadmap-builder.md` §2.3)
- `pm/roadmap/{slug}/phase-{n}-*/current-phase-status.md` story table
- `pm/roadmap/{slug}/README.md` "Last updated"
- any project-canon doc the story explicitly mentions
  (BACKLOG, CHANGELOG, IMPLEMENTATION-LOG, PLAN.md §0, etc.)

Splitting tracking-doc updates into a follow-up commit is forbidden.

### 3. Tests actually ran

You ran the relevant tests via the documented project commands (npm
scripts, bash scripts, etc.). You read the output. You did not just
author the test file. Failed tests are either fixed or named in the
commit message as a known regression with a follow-up plan.

Prefer discharging this rule mechanically: run the tests through
`dw evidence capture <project> <phase> <story> -- <command>` and
generate the contract with `dw contract new --tests-capture
<evidence-path>`. The gate then verifies the captured run exists in
the staged evidence with exit code 0
(`contract-tests-capture-mismatch` otherwise), instead of trusting
the checkbox.

### 4. Greenfield discipline (where applicable)

If the project is in a pre-launch / greenfield state (the project
README will say so), you have not added migration ceremony, behavior-
preservation SQL, backwards-compat shims, or unused-export
preservation. Schema and APIs can change freely.

If the project is post-launch, this rule does not apply — the project
README will tell you which.

### 5. No bypasses, no scope creep

You did not pass `--no-verify` or `--no-gpg-sign`. You did not add a
`Co-Authored-By` line the user did not ask for. You did not include
files outside the scope of what the user asked for in this commit. If
unrelated cleanups happened to be in your working tree, they are in a
separate commit or explicitly mentioned in the message.

### 6. Story → evidence pairing (mechanically enforced)

If a story file's status flipped to `done` in this commit, the
corresponding `evidence-story-{n}.md` exists in this same commit.
Otherwise the story is `in-progress`, not `done`.

The gate compares each staged story file's `**Status:**` header in
`HEAD` against the staged index: a story "ships" when the header
flips from a non-done value to `done` or a done-synonym
(`complete | closed | shipped`) — renames and reformatting of
already-done stories are not flips. A shipped story without its
`evidence-story-{n}.md` staged in the same commit is blocked
(`evidence-missing`); evidence numbers pair as integers, so
`evidence-story-1.md` matches `story-01-*`. The gate also rejects
orphan evidence (`orphan-evidence`: an added evidence file whose
story does not flip in the same commit) and evidence deletions that
would orphan a still-done story
(`evidence-deletion-orphans-story`).

### 7. One PR per story (mechanically enforced)

This commit is part of work that maps to one story (or one logically
atomic chunk if outside the roadmap framework). If the diff bundles
multiple stories, the commit message says so and each story file's
"Notes" section records the bundling.

The pre-commit hook counts how many `pm/roadmap/.../story-*.md`
files flipped to `done` in this commit. More than one is a hard
block (`atomicity`). To bundle intentionally — and only
intentionally — write `.tmp/BUNDLE-OK.md` with a one-line rationale.
The gate accepts that as a per-commit override; on success it is
archived with the contract under `.git/pmo-contract-archive/<sha>`
and the working copy cleared (same pattern as the contract file).
Bundling is rare; if you find yourself reaching for `BUNDLE-OK`
regularly, you are mis-sizing your stories.

---

## Contract template

Generate the contract — do not hand-type it. After staging, run:

```bash
.githooks/dw gate                 # optional non-consuming preflight
.githooks/dw contract new         # stamps the facts, writes .tmp/CONTRACT.md
```

then flip every `[ ]` to `[x]` only after honestly verifying each
rule. The generated file looks like this (the facts block is stamped,
re-derived, and enforced by the gate; the box lines below are the
rule set the gate verifies by title):

```markdown
# Commit Contract

**Generated:** {UTC timestamp}
**Branch:** {branch}
**HEAD:** {commit sha, or "none" on the first commit}
**Index-tree:** {git write-tree of the staged index — the freshness proof}
**Story:** {story ID(s) detected in the staged diff, or "none"}
**Tier:** {full | short — decided mechanically; see "Contract tiers"}
**Staged files (sample):**
- {staged paths — must be a truthful subset of the real staged index}

I certify, for this commit:

- [ ] **Evidence, not vibes.** Claimed work has on-disk evidence (or a commit-message pointer to the actual output I read).
- [ ] **Master docs updated.** Story header status, current-phase-status table, and any project-canon docs touched by this story are updated in this same commit.
- [ ] **Tests ran.** I ran the relevant tests via the project's documented scripts and read the output. Type-check is not validation.
- [ ] **Greenfield discipline (if applicable).** I did not add migration ceremony, compat shims, or backwards-compat hacks where the project is greenfield.
- [ ] **No bypasses.** No `--no-verify`, no unauthorized `Co-Authored-By`, no scope creep beyond what the user asked.
- [ ] **Story → evidence pairing.** If any story flipped to `done`, its `evidence-story-{n}.md` ships in this commit.
- [ ] **One PR per story.** This commit maps to one story (or atomic chunk), or the bundling is documented.

Methodology: pm/roadmap/roadmap-builder.md
Rules canon: pm/roadmap/PMO-CONTRACT.md

## Work-log consent

**Work-log consent:** no

**Work-log reasons:**
- n/a

**Work-log exclusions:**
- none
```

The gate verifies boxes **by rule title**, against this fenced
template: every checked box must match a known rule title, and every
known rule must be checked. Projects that add rules simply add their
`- [ ] **Rule title.** …` lines to this template fence; `dw contract
new` and the gate pick them up automatically. The legacy
`EXPECTED_BOXES` count check applies only when no `PMO-CONTRACT.md`
is present. Restaging after generation invalidates the contract
(index-tree mismatch); re-run `dw contract new --force`.

The work-log consent block is not an eighth PMO checkbox and is not
counted by `EXPECTED_BOXES`. Projects that enable work logging through
`.githooks/pre-commit.config` only get a daily log entry when this line
is explicit:

```markdown
**Work-log consent:** yes
```

Use `yes` only when the staged work is valid long-term technical work
evidence. Keep `no` for commits that should not create an architect-log
entry. When consent is `yes`, write concrete reasons and any exclusions:

```markdown
**Work-log reasons:**
- Implements WLA-1-02 by capturing the staged diff after PMO checks pass.

**Work-log exclusions:**
- Do not include secret-looking fixture values from `testdata/`.
```

When work logging is enabled, `pre-commit` captures the consented staged
payload under `.git/pmo-work-log/`. `post-commit` appends a deterministic
entry to `~/.work/log/YYYY-MM-DD/{log-identity}-work-summary.log` only
after Git creates the commit. LLM summarization is intentionally outside
the MVP commit path.

For mechanical path omission, set `PMO_WORK_LOG_EXCLUDE_REGEX` in
`.githooks/pre-commit.config`. Contract exclusions explain intent; the
regex is what keeps matching staged paths out of captured work-log
payloads.

---

## Extending: project-specific rules

The canonical contract owns rules #1–#7. They are universal: every
project that adopts the framework inherits them. Some projects need
*additional* rules — for example, "every UI-facing change updates
the design handoff". The framework supports this without forking
the canonical hook.

### How to add a project-specific rule

1. **Add the rule to this `PMO-CONTRACT.md`**, below the canonical
   rules. Number it #8, #9, ... and label the section clearly as
   a project extension. The canonical content above this section
   stays as-is so `update.sh` can refresh it cleanly.
2. **Add a corresponding checkbox** to the contract template. Place
   it after the canonical 7. The canonical hook accepts ≥ 7 boxes,
   so adding more is safe.
3. **Add a structural enforcement check** (if applicable) to
   `.githooks/pre-commit.local`. The canonical hook sources this
   file after its own structural checks. The local hook can:
   - read `$STAGED`, `$STAGED_STORIES`, `$STAGED_EVIDENCE`,
     `$SHIPPED_STORIES`, `$SHIPPED_COUNT`, `$REPO_ROOT`
   - call `fail "reason"` (defined in the canonical hook) to block
   - append paths to `$EXTRA_CLEANUP_FILES` — they get `rm -f`'d
     on success
   - append text to `$EXTRA_BANNER_LINES` to extend the success
     banner
4. **Optionally provide a sentinel-file override** (e.g.
   `.tmp/<RULE>-OK.md`) that lets a project temporarily bypass the
   structural check with a one-line rationale. Add the sentinel
   path to `$EXTRA_CLEANUP_FILES` so it auto-deletes on success
   (same pattern as `BUNDLE-OK.md`).
5. **(Legacy) `EXPECTED_BOXES`** in `.githooks/pre-commit.config` is
   no longer required: the gate derives the required box set from this
   document's contract-template fence, so adding the checkbox in step 2
   is authoritative. The count-based override only matters for repos
   without a `PMO-CONTRACT.md`.

`update.sh` never touches `.githooks/pre-commit.local` or
`.githooks/pre-commit.config`. Both survive framework updates.

### Worked example

A complete project-extension example (rule text, template checkbox, and
the `pre-commit.local` structural check) lives at
[`templates/examples/project-extension-example.md`](./examples/project-extension-example.md)
in the framework repository. The pattern: the canonical framework stays
unchanged; the project's rule is mechanically enforced; `update.sh`
refreshes canonical files without clobbering the local extension.

---

## Contract tiers

The gate decides the required tier mechanically:

- **Full contract** — required whenever staged changes touch the
  roadmap tree (`pm/roadmap/**`), which includes every story flip. The
  full rule set above applies.
- **Short form** — commits that do not touch the roadmap tree may use
  `dw contract new --tier short` (or rely on `auto`, which picks it):
  the same stamped facts plus only the **No bypasses.** rule. A
  short-form contract on a roadmap-touching commit is rejected
  (`contract-tier-mismatch`).

Projects that want full ceremony everywhere set `PMO_CONTRACT_TIER=full`
in `.githooks/pre-commit.config`; the generator and the gate both honor
it. The conservative default: `auto` — full for anything roadmap-shaped,
short available for docs-and-code-only commits.

---

## Discharge

Some commits genuinely do not need every rule. A documentation typo
fix does not have "tests that ran." In those cases:

- You still write the contract.
- You still certify each box honestly.
- For a box that does not apply, you mark it `[x]` and add an inline
  parenthetical: `- [x] **Tests ran.** (n/a — docs-only)`.

The point is the re-read, not the literal applicability.

---

## Bypass

The user (only) may run `git commit --no-verify` in genuine emergencies.
Agents may not. The project's `CLAUDE.md` already restricts
`--no-verify` for agents; this contract layer assumes that restriction.

If an agent ever encounters a situation where the contract genuinely
cannot be honored (e.g. the rules themselves are wrong for the work),
the correct move is: stop, raise the conflict to the user, and let the
user adjust either the contract or the work scope.
